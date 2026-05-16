"""Mandate ledger — local authority records for high-risk Kai actions."""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.harness_config import get_config

from .models import ActionMandate
from .policy import PAID_MEDIA_MUTATION_ACTIONS


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def _json_load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload: Any) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(_json_dump(payload), encoding="utf-8")
    tmp_path.replace(path)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _parse_iso8601(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _to_float(value: Any) -> Optional[float]:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


HIGH_RISK_ACTION_TYPES: set[tuple[str, str]] = {
    ("website", "update_page_copy"),
    ("website", "update_page_section"),
    ("website", "update_cta"),
    ("website", "restructure_page"),
    ("website", "change_pricing"),
    ("website", "update_regulated_claims"),
    ("social", "publish_social_post"),
    ("social", "schedule_social_post"),
    ("email", "launch_email_sequence"),
    ("email", "send_approved_template"),
}


class MandateLedger:
    """File-backed local ledger for action mandates."""

    def __init__(self, base_dir: Optional[Path] = None):
        cfg = get_config()
        if base_dir is None:
            base_dir = Path(os.environ.get("KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")))

        self.base_dir = base_dir
        self.mandates_dir = _ensure_dir(self.base_dir / "mandates")
        self._lock = threading.RLock()

    @classmethod
    def default(cls) -> "MandateLedger":
        return cls()

    def create(self, mandate: ActionMandate | dict) -> dict:
        """Create and persist a mandate."""
        record = self._coerce_mandate(mandate)
        mandate_id = record.get("mandate_id") or _new_id("mandate")
        now = _utc_now()

        record["mandate_id"] = mandate_id
        record["approval_state"] = record.get("approval_state") or "pending"
        record["created_at"] = record.get("created_at") or now
        record["updated_at"] = now
        record.setdefault("metadata", {})

        with self._lock:
            _write_json_atomic(self.mandates_dir / f"{mandate_id}.json", record)
        return record

    def get(self, mandate_id: str) -> Optional[dict]:
        path = self.mandates_dir / f"{mandate_id}.json"
        if not path.exists():
            return None
        return _json_load(path)

    def update(self, mandate_id: str, **changes: Any) -> dict:
        with self._lock:
            record = self._require(mandate_id)
            record.update(changes)
            record["updated_at"] = _utc_now()
            _write_json_atomic(self.mandates_dir / f"{mandate_id}.json", record)
            return record

    def approve(self, mandate_id: str, *, approved_by: str, note: Optional[str] = None) -> dict:
        with self._lock:
            record = self._require(mandate_id)
            if record.get("approval_state") not in {"pending"}:
                raise ValueError(f"Cannot approve mandate in state '{record.get('approval_state')}'")
            record["approval_state"] = "approved"
            record["approved_by"] = approved_by
            record["updated_at"] = _utc_now()
            if note:
                record.setdefault("metadata", {})["approval_note"] = note
            _write_json_atomic(self.mandates_dir / f"{mandate_id}.json", record)
            return record

    def reject(self, mandate_id: str, *, approved_by: str, note: Optional[str] = None) -> dict:
        with self._lock:
            record = self._require(mandate_id)
            if record.get("approval_state") not in {"pending"}:
                raise ValueError(f"Cannot reject mandate in state '{record.get('approval_state')}'")
            record["approval_state"] = "rejected"
            record["approved_by"] = approved_by
            record["updated_at"] = _utc_now()
            if note:
                record.setdefault("metadata", {})["rejection_note"] = note
            _write_json_atomic(self.mandates_dir / f"{mandate_id}.json", record)
            return record

    def revoke(self, mandate_id: str, *, approved_by: str, note: Optional[str] = None) -> dict:
        with self._lock:
            record = self._require(mandate_id)
            record["approval_state"] = "revoked"
            record["approved_by"] = approved_by
            record["revoked_at"] = _utc_now()
            record["updated_at"] = record["revoked_at"]
            if note:
                record.setdefault("metadata", {})["revocation_note"] = note
            _write_json_atomic(self.mandates_dir / f"{mandate_id}.json", record)
            return record

    def list(
        self,
        *,
        brand_id: Optional[str] = None,
        agent_id: Optional[str] = None,
        approval_state: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        records: List[dict] = []
        for path in self.mandates_dir.glob("*.json"):
            record = _json_load(path)
            if brand_id and record.get("brand_id") != brand_id:
                continue
            if agent_id and record.get("agent_id") != agent_id:
                continue
            if approval_state and record.get("approval_state") != approval_state:
                continue
            records.append(record)
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return records[:limit]

    def validate_for_action(self, action: dict, *, at_time: Optional[str] = None) -> dict:
        """Validate whether an action has a usable mandate."""
        if not self.requires_mandate(action):
            return {"allowed": True, "reason": "Mandate not required for this action", "mandate_id": None}

        mandate_id = (
            action.get("mandate_id")
            or (action.get("metadata") or {}).get("mandate_id")
        )
        if not mandate_id:
            return {
                "allowed": False,
                "reason": "High-risk action requires an approved mandate",
                "mandate_id": None,
            }

        mandate = self.get(mandate_id)
        if not mandate:
            return {"allowed": False, "reason": f"Mandate not found: {mandate_id}", "mandate_id": mandate_id}

        now = _parse_iso8601(at_time) if at_time else datetime.now(timezone.utc)
        if now is None:
            now = datetime.now(timezone.utc)

        approval_state = mandate.get("approval_state")
        if approval_state != "approved":
            return {
                "allowed": False,
                "reason": f"Mandate is not approved (state: {approval_state})",
                "mandate_id": mandate_id,
            }

        expires_at = _parse_iso8601(mandate.get("expires_at"))
        if expires_at and expires_at <= now:
            return {"allowed": False, "reason": "Mandate is expired", "mandate_id": mandate_id}

        if mandate.get("revoked_at"):
            return {"allowed": False, "reason": "Mandate is revoked", "mandate_id": mandate_id}

        action_brand = action.get("brand_id")
        if mandate.get("brand_id") != action_brand:
            return {
                "allowed": False,
                "reason": f"Mandate brand scope denied: {action_brand}",
                "mandate_id": mandate_id,
            }

        mandate_channel = mandate.get("channel")
        action_channel = action.get("channel")
        if mandate_channel not in {"*", action_channel}:
            return {
                "allowed": False,
                "reason": f"Mandate channel scope denied: {action_channel}",
                "mandate_id": mandate_id,
            }

        action_type = action.get("action_type")
        allowed_actions = set(mandate.get("action_types") or [])
        if "*" not in allowed_actions and action_type not in allowed_actions:
            return {
                "allowed": False,
                "reason": f"Mandate action scope denied: {action_type}",
                "mandate_id": mandate_id,
            }

        limit_failure = self._validate_limits(mandate, action)
        if limit_failure is not None:
            return {
                "allowed": False,
                "reason": limit_failure,
                "mandate_id": mandate_id,
            }

        return {"allowed": True, "reason": "ok", "mandate_id": mandate_id}

    def requires_mandate(self, action: dict) -> bool:
        """Return True when the action can mutate spend/publish/outreach/site state."""
        channel = action.get("channel", "")
        action_type = action.get("action_type", "")
        key = (channel, action_type)
        if key in HIGH_RISK_ACTION_TYPES:
            return True
        if channel == "paid_media" and action_type in PAID_MEDIA_MUTATION_ACTIONS:
            return True
        if action.get("risk_tier") == "high":
            return True
        return False

    def _validate_limits(self, mandate: dict, action: dict) -> Optional[str]:
        limits = mandate.get("limits") or {}
        proposed = action.get("proposed_changes") or {}

        max_daily_budget = _to_float(
            limits.get("max_daily_budget_usd")
            or limits.get("max_daily_budget")
        )
        if max_daily_budget is not None:
            new_daily_budget = _to_float(proposed.get("new_daily_budget"))
            if new_daily_budget is not None and new_daily_budget > max_daily_budget:
                return (
                    f"Action daily budget ${new_daily_budget:g} exceeds mandate limit "
                    f"${max_daily_budget:g}"
                )

        max_budget_increase_pct = _to_float(limits.get("max_budget_increase_pct"))
        if max_budget_increase_pct is not None:
            increase_pct = _to_float(proposed.get("budget_increase_pct"))
            if increase_pct is not None and increase_pct > max_budget_increase_pct:
                return (
                    f"Action budget increase {increase_pct:g}% exceeds mandate limit "
                    f"{max_budget_increase_pct:g}%"
                )

        return None

    def _require(self, mandate_id: str) -> dict:
        record = self.get(mandate_id)
        if not record:
            raise KeyError(f"Mandate not found: {mandate_id}")
        return record

    def _coerce_mandate(self, mandate: ActionMandate | dict) -> dict:
        if isinstance(mandate, ActionMandate):
            return asdict(mandate)
        if isinstance(mandate, dict):
            result = dict(mandate)
            result.setdefault("mandate_id", "")
            result.setdefault("agent_id", "")
            result.setdefault("brand_id", "")
            result.setdefault("channel", "")
            result.setdefault("action_types", [])
            result.setdefault("limits", {})
            result.setdefault("expires_at", None)
            result.setdefault("created_by", "")
            result.setdefault("approved_by", "")
            result.setdefault("approval_state", "pending")
            result.setdefault("source_run_id", None)
            result.setdefault("evidence", [])
            result.setdefault("metadata", {})
            result.setdefault("created_at", "")
            result.setdefault("updated_at", "")
            result.setdefault("revoked_at", None)
            return result
        raise TypeError(f"Unsupported mandate type: {type(mandate)!r}")


_DEFAULT_MANDATE_LEDGER: Optional[MandateLedger] = None


def get_default_mandate_ledger() -> MandateLedger:
    """Lazily construct the process-wide default mandate ledger."""
    global _DEFAULT_MANDATE_LEDGER
    if _DEFAULT_MANDATE_LEDGER is None:
        _DEFAULT_MANDATE_LEDGER = MandateLedger.default()
    return _DEFAULT_MANDATE_LEDGER
