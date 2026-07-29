"""Stripe test-mode checkout tool boundary with provider read-back."""

from __future__ import annotations

import base64
import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from .store import RuntimeStore


STRIPE_TOOL_ID = "stripe.test_checkout"
STRIPE_API = "https://api.stripe.com/v1"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _stripe_request(
    method: str,
    path: str,
    *,
    api_key: str,
    form: Optional[dict[str, Any]] = None,
    idempotency_key: Optional[str] = None,
) -> dict:
    payload = None
    headers = {
        "Authorization": "Basic "
        + base64.b64encode(f"{api_key}:".encode()).decode(),
        "User-Agent": "kai-commercial-agent/1.0",
    }
    if form is not None:
        payload = urllib.parse.urlencode(form).encode()
        headers["Content-Type"] = "application/x-www-form-urlencoded"
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    request = urllib.request.Request(
        f"{STRIPE_API}{path}", data=payload, headers=headers, method=method
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode())
    except urllib.error.HTTPError as error:
        detail = error.read().decode(errors="replace")
        raise RuntimeError(f"Stripe API {error.code}: {detail[:1000]}") from error


@dataclass(frozen=True)
class StripePaymentLinkReceipt:
    run_id: str
    work_id: str
    payment_link_id: str
    payment_link_url: str
    amount_cents: int
    currency: str
    provider_object: dict
    readback: dict
    provider_response_sha256: str
    receipt_uri: str
    receipt_sha256: str

    def model_dump(self) -> Dict[str, Any]:
        return {"schema": "kai.stripe.test-payment-link-receipt.v1", **self.__dict__}


def create_test_payment_link(
    *,
    store: RuntimeStore,
    run_id: str,
    work_id: str,
    offer_name: str,
    amount_cents: int,
    currency: str = "usd",
    api_key: Optional[str] = None,
) -> StripePaymentLinkReceipt:
    """Create and retrieve one Stripe test Payment Link."""
    key = api_key or os.environ.get("STRIPE_SECRET_KEY") or ""
    if not key.startswith("sk_test_"):
        raise RuntimeError("Stripe commercial demo requires an sk_test_ secret")
    if not offer_name.strip() or amount_cents <= 0:
        raise ValueError("offer_name and a positive amount_cents are required")
    if currency.lower() != "usd":
        raise ValueError("the film slice currently permits USD only")

    idempotency_key = f"kai-commercial-{run_id}-{work_id}"
    created = _stripe_request(
        "POST",
        "/payment_links",
        api_key=key,
        idempotency_key=idempotency_key,
        form={
            "line_items[0][price_data][currency]": "usd",
            "line_items[0][price_data][unit_amount]": str(amount_cents),
            "line_items[0][price_data][product_data][name]": offer_name,
            "line_items[0][quantity]": "1",
            "metadata[run_id]": run_id,
            "metadata[work_id]": work_id,
        },
    )
    payment_link_id = str(created.get("id") or "")
    payment_link_url = str(created.get("url") or "")
    if not payment_link_id or not payment_link_url:
        raise RuntimeError("Stripe did not return a hosted payment link")
    readback = _stripe_request("GET", f"/payment_links/{payment_link_id}", api_key=key)
    response_bytes = json.dumps({"created": created, "readback": readback}, sort_keys=True).encode()
    receipt_payload = {
        "schema": "kai.stripe.test-payment-link-receipt.v1",
        "run_id": run_id,
        "work_id": work_id,
        "payment_link_id": payment_link_id,
        "payment_link_url": payment_link_url,
        "amount_cents": amount_cents,
        "currency": currency,
        "provider_object": created,
        "readback": readback,
        "provider_response_sha256": hashlib.sha256(response_bytes).hexdigest(),
        "recorded_at": _utc_now(),
    }
    receipt_dir = store.commercial_dir / "provider_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"{work_id}.stripe.json"
    receipt_bytes = json.dumps(receipt_payload, indent=2, sort_keys=True).encode()
    temp_path = receipt_path.with_suffix(".json.tmp")
    temp_path.write_bytes(receipt_bytes)
    temp_path.replace(receipt_path)
    receipt_sha256 = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    return StripePaymentLinkReceipt(
        run_id=run_id,
        work_id=work_id,
        payment_link_id=payment_link_id,
        payment_link_url=payment_link_url,
        amount_cents=amount_cents,
        currency=currency,
        provider_object=created,
        readback=readback,
        provider_response_sha256=receipt_payload["provider_response_sha256"],
        receipt_uri=f"artifact://commercial/provider-receipts/{work_id}.stripe.json",
        receipt_sha256=receipt_sha256,
    )


def release_test_payment_link(
    *, api_key: Optional[str], payment_link_id: str, run_id: str, work_id: str
) -> dict[str, Any]:
    """Activate one held Stripe test link and independently retrieve it."""
    key = api_key or os.environ.get("STRIPE_SECRET_KEY") or ""
    if not key.startswith("sk_test_"):
        raise RuntimeError("Stripe commercial release requires an sk_test_ secret")
    if not payment_link_id:
        raise ValueError("payment_link_id is required")
    activated = _stripe_request(
        "POST", f"/payment_links/{payment_link_id}", api_key=key,
        form={"active": "true"}, idempotency_key=f"kai-commercial-release-{run_id}-{work_id}",
    )
    readback = _stripe_request("GET", f"/payment_links/{payment_link_id}", api_key=key)
    if activated.get("livemode") is not False or readback.get("livemode") is not False:
        raise RuntimeError("Stripe release read-back was not test mode")
    if readback.get("active") is not True:
        raise RuntimeError("Stripe release read-back was not active")
    return {
        "schema": "kai.stripe.test-payment-link-release.v1",
        "run_id": run_id,
        "work_id": work_id,
        "payment_link_id": payment_link_id,
        "provider_object": activated,
        "readback": readback,
        "provider_response_sha256": hashlib.sha256(
            json.dumps({"activated": activated, "readback": readback}, sort_keys=True).encode()
        ).hexdigest(),
    }
