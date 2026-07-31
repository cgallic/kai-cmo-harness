"""Action store — lifecycle management for proposed marketing mutations."""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from scripts.harness_config import get_config

from .models import SerializableModel


EXECUTION_STATES = ("pending", "executing", "completed", "failed", "rolled_back")
OPERATING_STATES = ("drafted", "gated", "approved", "executed", "verified", "learned")


# ---------------------------------------------------------------------------
# Helpers (mirrors store.py conventions)
# ---------------------------------------------------------------------------


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


def derive_operating_state(record: dict) -> str:
    """Return the marketing-OS lifecycle state for a stored action."""

    metadata = record.get("metadata") or {}
    explicit = metadata.get("operating_state")
    if explicit in OPERATING_STATES:
        return explicit
    if record.get("memory_writeback_ids"):
        return "learned"
    if record.get("verification_result"):
        return "verified"
    if record.get("execution_state") == "completed":
        return "executed"
    if record.get("approval_state") in ("approved", "auto_approved"):
        return "approved"
    if record.get("policy_result"):
        return "gated"
    return "drafted"


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


@dataclass
class ActionProposal(SerializableModel):
    """A proposed real-world marketing mutation against a live channel."""

    action_id: str = ""
    brand_id: str = ""
    channel: str = ""  # website, social, paid_media, email, analytics
    action_type: str = ""  # update_page_copy, publish_social_post, etc.
    intent: str = ""
    proposed_changes: Dict[str, Any] = field(default_factory=dict)
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    source_run_id: Optional[str] = None
    mandate_id: Optional[str] = None
    risk_tier: Literal["low", "medium", "high"] = "low"
    policy_result: Dict[str, Any] = field(default_factory=lambda: {"passed": True, "checks": [], "violations": []})
    preview_artifact: Optional[Dict[str, Any]] = None
    approval_state: Literal["pending", "approved", "rejected", "auto_approved", "held"] = "pending"
    execution_state: Literal["pending", "executing", "completed", "failed", "rolled_back"] = "pending"
    verification_criteria: List[Dict[str, Any]] = field(default_factory=list)
    verification_result: Optional[Dict[str, Any]] = None
    rollback_reference: Optional[Dict[str, Any]] = None
    result_summary: Optional[Dict[str, Any]] = None
    memory_writeback_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    executed_at: Optional[str] = None


# ---------------------------------------------------------------------------
# ActionStore
# ---------------------------------------------------------------------------


class ActionStore:
    """File-backed persistence for marketing action proposals and their lifecycle.

    Actions are stored as individual JSON files under ``{base_dir}/actions/``.
    An append-only audit log lives under ``{base_dir}/action_log/``.
    """

    def __init__(self, base_dir: Optional[Path] = None, *, auto_approve_low_risk: bool = False):
        cfg = get_config()
        if base_dir is None:
            base_dir = Path(os.environ.get("KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")))

        self.base_dir = base_dir
        self.actions_dir = _ensure_dir(self.base_dir / "actions")
        self.log_dir = _ensure_dir(self.base_dir / "action_log")
        self.auto_approve_low_risk = auto_approve_low_risk
        self._lock = threading.RLock()

    @classmethod
    def default(cls) -> "ActionStore":
        return cls()

    # ------------------------------------------------------------------
    # Proposal creation
    # ------------------------------------------------------------------

    def propose_action(self, proposal: ActionProposal | dict) -> dict:
        """Create a new action proposal.

        If *auto_approve_low_risk* is enabled and the risk tier is ``"low"``,
        the action is auto-approved immediately.
        """
        record = self._coerce_proposal(proposal)
        action_id = record.get("action_id") or _new_id("act")
        now = _utc_now()

        record["action_id"] = action_id
        record.setdefault("created_at", now)
        record["updated_at"] = now
        record["execution_state"] = "pending"
        record["metadata"].setdefault(
            "operating_state",
            "gated" if record.get("policy_result") else "drafted",
        )

        # Determine initial approval state
        if self.auto_approve_low_risk and record.get("risk_tier") == "low":
            record["approval_state"] = "auto_approved"
            record["metadata"]["operating_state"] = "approved"
        else:
            record.setdefault("approval_state", "pending")

        with self._lock:
            _write_json_atomic(self.actions_dir / f"{action_id}.json", record)
            self._append_log(
                action_id=action_id,
                previous_state=None,
                new_state=record["approval_state"],
                field="approval_state",
                actor="system",
            )

        return record

    # ------------------------------------------------------------------
    # Approval state mutations
    # ------------------------------------------------------------------

    def approve_action(self, action_id: str, note: Optional[str] = None) -> dict:
        """Approve a pending or held action."""
        with self._lock:
            record = self._require_action(action_id)
            prev = record["approval_state"]
            if prev not in ("pending", "held"):
                raise ValueError(f"Cannot approve action in approval_state '{prev}'")
            record["approval_state"] = "approved"
            record["updated_at"] = _utc_now()
            if note:
                record["metadata"]["approval_note"] = note
            record["metadata"]["operating_state"] = "approved"
            self._write_action(record)
            self._append_log(action_id, prev, "approved", "approval_state", actor="human", note=note)
            return record

    def reject_action(self, action_id: str, note: Optional[str] = None) -> dict:
        """Reject a pending or held action."""
        with self._lock:
            record = self._require_action(action_id)
            prev = record["approval_state"]
            if prev not in ("pending", "held"):
                raise ValueError(f"Cannot reject action in approval_state '{prev}'")
            record["approval_state"] = "rejected"
            record["updated_at"] = _utc_now()
            if note:
                record["metadata"]["rejection_note"] = note
            self._write_action(record)
            self._append_log(action_id, prev, "rejected", "approval_state", actor="human", note=note)
            return record

    def hold_action(self, action_id: str, note: Optional[str] = None) -> dict:
        """Place a pending action on hold for review."""
        with self._lock:
            record = self._require_action(action_id)
            prev = record["approval_state"]
            if prev != "pending":
                raise ValueError(f"Cannot hold action in approval_state '{prev}'")
            record["approval_state"] = "held"
            record["updated_at"] = _utc_now()
            if note:
                record["metadata"]["hold_note"] = note
            self._write_action(record)
            self._append_log(action_id, prev, "held", "approval_state", actor="human", note=note)
            return record

    # ------------------------------------------------------------------
    # Execution state mutations
    # ------------------------------------------------------------------

    def mark_executing(self, action_id: str) -> dict:
        """Mark an approved/auto_approved action as executing."""
        with self._lock:
            record = self._require_action(action_id)
            if record["approval_state"] not in ("approved", "auto_approved"):
                raise ValueError(
                    f"Cannot execute action with approval_state '{record['approval_state']}' — "
                    "must be approved or auto_approved"
                )
            prev = record["execution_state"]
            if prev == "executing":
                return record
            record["execution_state"] = "executing"
            record["updated_at"] = _utc_now()
            record["metadata"]["operating_state"] = "approved"
            self._write_action(record)
            self._append_log(action_id, prev, "executing", "execution_state", actor="system")
            return record

    def claim_ready_actions(
        self,
        *,
        brand_id: Optional[str] = None,
        limit: int = 50,
        worker_id: Optional[str] = None,
    ) -> List[dict]:
        """Atomically claim approved actions for one worker.

        The claim happens under the store lock and persists the executing
        state before returning. This prevents two in-process workers from
        selecting the same approved action between list and execute.
        """
        worker_id = worker_id or f"worker_{os.getpid()}"
        claimed: List[dict] = []
        with self._lock:
            ready = self.list_actions(
                brand_id=brand_id,
                execution_state="pending",
                limit=max(limit, 1),
            )
            ready = [
                record for record in ready
                if record.get("approval_state") in ("approved", "auto_approved")
            ]
            for record in ready[:limit]:
                action_id = record["action_id"]
                current = self._require_action(action_id)
                if current.get("execution_state") != "pending":
                    continue
                previous = current.get("execution_state")
                current["execution_state"] = "executing"
                current["updated_at"] = _utc_now()
                current["metadata"]["operating_state"] = "approved"
                current["metadata"]["claimed_by"] = worker_id
                current["metadata"]["claimed_at"] = current["updated_at"]
                self._write_action(current)
                self._append_log(action_id, previous, "executing", "execution_state", actor=worker_id)
                claimed.append(current)
        return claimed

    def mark_completed(self, action_id: str, result_summary: dict) -> dict:
        """Mark an executing action as completed."""
        with self._lock:
            record = self._require_action(action_id)
            prev = record["execution_state"]
            if prev != "executing":
                raise ValueError(f"Cannot complete action in execution_state '{prev}'")
            record["execution_state"] = "completed"
            record["result_summary"] = result_summary
            now = _utc_now()
            record["updated_at"] = now
            record["executed_at"] = now
            record["metadata"]["operating_state"] = "executed"
            self._write_action(record)
            self._append_log(action_id, prev, "completed", "execution_state", actor="system")
            return record

    def mark_failed(self, action_id: str, error: str) -> dict:
        """Mark an executing action as failed."""
        with self._lock:
            record = self._require_action(action_id)
            prev = record["execution_state"]
            if prev != "executing":
                raise ValueError(f"Cannot fail action in execution_state '{prev}'")
            record["execution_state"] = "failed"
            record["result_summary"] = {"error": error}
            now = _utc_now()
            record["updated_at"] = now
            record["executed_at"] = now
            record["metadata"]["operating_state"] = "gated"
            self._write_action(record)
            self._append_log(action_id, prev, "failed", "execution_state", actor="system", note=error)
            return record

    def mark_rolled_back(self, action_id: str, rollback_result: dict) -> dict:
        """Mark a completed or failed action as rolled back."""
        with self._lock:
            record = self._require_action(action_id)
            prev = record["execution_state"]
            if prev not in ("completed", "failed"):
                raise ValueError(f"Cannot roll back action in execution_state '{prev}'")
            record["execution_state"] = "rolled_back"
            record["result_summary"] = rollback_result
            record["updated_at"] = _utc_now()
            record["metadata"]["operating_state"] = "executed"
            self._write_action(record)
            self._append_log(action_id, prev, "rolled_back", "execution_state", actor="system")
            return record

    def mark_verified(self, action_id: str, verification_result: dict) -> dict:
        """Attach a verification result to an executed action."""
        with self._lock:
            record = self._require_action(action_id)
            if record["execution_state"] != "completed":
                raise ValueError(f"Cannot verify action in execution_state '{record['execution_state']}'")
            prev = derive_operating_state(record)
            record["verification_result"] = verification_result
            record["metadata"]["operating_state"] = "verified"
            record["updated_at"] = _utc_now()
            self._write_action(record)
            self._append_log(action_id, prev, "verified", "operating_state", actor="system")
            return record

    def mark_learned(self, action_id: str, memory_writeback_ids: List[str]) -> dict:
        """Attach memory writeback references after verification."""
        with self._lock:
            record = self._require_action(action_id)
            if derive_operating_state(record) != "verified":
                raise ValueError("Cannot learn from an action before verification")
            prev = derive_operating_state(record)
            record["memory_writeback_ids"] = list(memory_writeback_ids)
            record["metadata"]["operating_state"] = "learned"
            record["updated_at"] = _utc_now()
            self._write_action(record)
            self._append_log(action_id, prev, "learned", "operating_state", actor="system")
            return record

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_action(self, action_id: str) -> Optional[dict]:
        """Load a single action by ID."""
        path = self.actions_dir / f"{action_id}.json"
        if not path.exists():
            return None
        return _json_load(path)

    def list_actions(
        self,
        *,
        brand_id: Optional[str] = None,
        channel: Optional[str] = None,
        approval_state: Optional[str] = None,
        execution_state: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """List actions with optional filters."""
        records: List[dict] = []
        for path in self.actions_dir.glob("*.json"):
            record = _json_load(path)
            if brand_id and record.get("brand_id") != brand_id:
                continue
            if channel and record.get("channel") != channel:
                continue
            if approval_state and record.get("approval_state") != approval_state:
                continue
            if execution_state and record.get("execution_state") != execution_state:
                continue
            records.append(record)
        records.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        return records[:limit]

    def list_pending_approvals(
        self,
        *,
        brand_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """Return actions in pending or held approval state."""
        records: List[dict] = []
        for path in self.actions_dir.glob("*.json"):
            record = _json_load(path)
            if record.get("approval_state") not in ("pending", "held"):
                continue
            if brand_id and record.get("brand_id") != brand_id:
                continue
            records.append(record)
        records.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        return records[:limit]

    def get_action_log(
        self,
        *,
        brand_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """Return immutable action-log entries, newest first.

        Each entry records a single state transition.
        """
        entries: List[dict] = []
        for path in self.log_dir.glob("*.json"):
            entry = _json_load(path)
            if brand_id:
                # Resolve action's brand_id for filtering
                action = self.get_action(entry.get("action_id", ""))
                if not action or action.get("brand_id") != brand_id:
                    continue
            entries.append(entry)
        entries.sort(key=lambda e: e.get("timestamp", ""), reverse=True)
        return entries[:limit]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_action(self, action_id: str) -> dict:
        record = self.get_action(action_id)
        if not record:
            raise KeyError(f"Action not found: {action_id}")
        return record

    def _write_action(self, record: dict) -> None:
        _write_json_atomic(self.actions_dir / f"{record['action_id']}.json", record)

    def _coerce_proposal(self, proposal: ActionProposal | dict) -> dict:
        if isinstance(proposal, ActionProposal):
            return asdict(proposal)
        if isinstance(proposal, dict):
            result = dict(proposal)
            result.setdefault("mandate_id", None)
            result.setdefault("proposed_changes", {})
            result.setdefault("evidence", [])
            result.setdefault("policy_result", {"passed": True, "checks": [], "violations": []})
            result.setdefault("preview_artifact", None)
            result.setdefault("verification_criteria", [])
            result.setdefault("verification_result", None)
            result.setdefault("memory_writeback_ids", [])
            result.setdefault("metadata", {})
            result.setdefault("risk_tier", "low")
            result.setdefault("rollback_reference", None)
            result.setdefault("result_summary", None)
            result.setdefault("executed_at", None)
            return result
        raise TypeError(f"Unsupported proposal type: {type(proposal)!r}")

    def _append_log(
        self,
        action_id: str,
        previous_state: Optional[str],
        new_state: str,
        field: str,
        actor: str,
        note: Optional[str] = None,
    ) -> dict:
        """Write an immutable log entry for a state transition."""
        entry = {
            "log_id": _new_id("log"),
            "action_id": action_id,
            "field": field,
            "previous_state": previous_state,
            "new_state": new_state,
            "actor": actor,
            "note": note,
            "timestamp": _utc_now(),
        }
        _write_json_atomic(self.log_dir / f"{entry['log_id']}.json", entry)
        return entry


# ---------------------------------------------------------------------------
# Process-wide singleton
# ---------------------------------------------------------------------------

_DEFAULT_ACTION_STORE: Optional[ActionStore] = None


def get_default_action_store() -> ActionStore:
    """Lazily construct the process-wide default action store."""
    global _DEFAULT_ACTION_STORE
    if _DEFAULT_ACTION_STORE is None:
        _DEFAULT_ACTION_STORE = ActionStore.default()
    return _DEFAULT_ACTION_STORE
