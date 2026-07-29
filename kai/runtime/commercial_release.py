"""Approval-bound release and post-release reconciliation contracts."""
from __future__ import annotations

from typing import Any, Mapping


def authorize_release(*, packet: Mapping[str, Any], approval: Mapping[str, Any]) -> dict[str, Any]:
    if approval.get("decision") != "APPROVE":
        raise PermissionError("release requires an APPROVE decision")
    if approval.get("packet_sha256") != packet.get("packet_sha256"):
        raise PermissionError("approval is bound to a different packet")
    return {"state": "authorized", "packet_sha256": packet["packet_sha256"], "effects": packet["effects"]}


def reconcile_release(*, authorization: Mapping[str, Any], receipts: list[Mapping[str, Any]], readbacks: list[Mapping[str, Any]]) -> dict[str, Any]:
    if authorization.get("state") != "authorized":
        raise ValueError("release is not authorized")
    effect_ids = {str(effect.get("effect_id")) for effect in authorization.get("effects", [])}
    receipt_ids = {str(item.get("effect_id")) for item in receipts}
    readback_ids = {str(item.get("effect_id")) for item in readbacks}
    missing_receipts = sorted(effect_ids - receipt_ids)
    missing_readbacks = sorted(effect_ids - readback_ids)
    state = "shipped" if not missing_receipts and not missing_readbacks else "blocked"
    return {"state": state, "packet_sha256": authorization["packet_sha256"], "missing_receipts": missing_receipts, "missing_readbacks": missing_readbacks}


__all__ = ["authorize_release", "reconcile_release"]
