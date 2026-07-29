"""Hash-bound commercial packet assembled before human approval.

This module is deliberately provider-neutral.  It validates that every held
artifact belongs to the same run and creates the exact payload that Ola must
show before any external effect can be released.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Mapping


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha256(value: Any) -> str:
    return hashlib.sha256(value if isinstance(value, bytes) else _canonical(value)).hexdigest()


def _require_hash(value: Any, field: str) -> str:
    result = str(value or "")
    if len(result) != 64 or any(char not in "0123456789abcdef" for char in result):
        raise ValueError(f"{field} must be a lowercase SHA-256")
    return result


def build_commercial_packet(
    *,
    run_id: str,
    offer: Mapping[str, Any],
    website: Mapping[str, Any],
    proposal: Mapping[str, Any],
    checkout: Mapping[str, Any],
    booking: Mapping[str, Any],
    recipient: Mapping[str, Any],
    effects: list[Mapping[str, Any]],
    expires_at: str,
) -> dict[str, Any]:
    """Create an exact, approval-pending packet without releasing effects."""
    if not run_id or not expires_at:
        raise ValueError("run_id and expires_at are required")
    offer_hash = _require_hash(offer.get("artifact_sha256"), "offer artifact_sha256")
    website_hash = _require_hash(website.get("artifact_sha256"), "website artifact_sha256")
    proposal_hash = _require_hash(proposal.get("artifact_sha256"), "proposal artifact_sha256")
    checkout_id = str(checkout.get("id") or "")
    if not checkout_id or checkout.get("livemode") is not False or checkout.get("state") != "held":
        raise ValueError("checkout must be a held Stripe test-mode object")
    booking_id = str(booking.get("id") or "")
    if not booking_id or booking.get("state") != "held":
        raise ValueError("booking must be held")
    if not recipient.get("address") or not recipient.get("channel"):
        raise ValueError("recipient address and channel are required")
    if not effects or any(not item.get("effect_id") for item in effects):
        raise ValueError("effects must contain effect_id values")

    payload = {
        "schema": "kai.commercial.packet.v1",
        "run_id": run_id,
        "offer_sha256": offer_hash,
        "website_build_sha256": website_hash,
        "proposal_sha256": proposal_hash,
        "checkout": {"id": checkout_id, "livemode": False, "state": "held"},
        "booking": {"id": booking_id, "state": "held"},
        "recipient": dict(recipient),
        "effects": [dict(item) for item in effects],
        "expires_at": expires_at,
        "approval_state": "pending",
    }
    return {
        **payload,
        "packet_sha256": _sha256(payload),
        "approval": {"required": True, "state": "pending", "packet_sha256": _sha256(payload)},
    }


__all__ = ["build_commercial_packet"]
