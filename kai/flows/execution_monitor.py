"""Execution monitoring flow -- visibility into active, completed, and failed actions.

Provides a lightweight flow for operators to check what is currently
executing, what completed recently, what failed, and what is scheduled
next.  Includes retry capability for failed actions.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _load_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _parse_iso(ts: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp, returning None on failure."""
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# ExecutionMonitoringFlow
# ---------------------------------------------------------------------------

_ACTIVE_STATES = {"executing", "approved_waiting", "scheduled"}
_TERMINAL_STATES = {"completed", "failed", "rolled_back", "cancelled"}


class ExecutionMonitoringFlow:
    """Operator flow for monitoring action execution.

    Usage::

        flow = ExecutionMonitoringFlow(workspace_dir="workspace")
        status = flow.start("biz_abc123")
        active = flow.get_active_executions("biz_abc123")
        completions = flow.get_recent_completions("biz_abc123", days=7)
        failures = flow.get_failures("biz_abc123")
        result = flow.retry_action("act_abc123")
        upcoming = flow.get_upcoming("biz_abc123")
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir

    # -- lifecycle -------------------------------------------------------

    def start(self, business_id: str) -> Dict[str, Any]:
        """Return current execution status overview.

        Returns
        -------
        dict with keys: active_executions, recent_completions, failures
        """
        return {
            "active_executions": self.get_active_executions(business_id),
            "recent_completions": self.get_recent_completions(business_id, days=7),
            "failures": self.get_failures(business_id),
        }

    # -- active executions -----------------------------------------------

    def get_active_executions(self, business_id: str) -> List[Dict[str, Any]]:
        """Return actions currently executing, waiting, or scheduled."""
        records = self._load_execution_records(business_id)
        active: List[Dict[str, Any]] = []

        for rec in records:
            state = rec.get("execution_state", rec.get("state", ""))
            if state in _ACTIVE_STATES:
                active.append({
                    "action_id": rec.get("action_id", rec.get("id", "")),
                    "title": rec.get("title", ""),
                    "action_type": rec.get("action_type", ""),
                    "channel": rec.get("channel", ""),
                    "state": state,
                    "started_at": rec.get("started_at", ""),
                    "scheduled_for": rec.get("scheduled_for", ""),
                    "risk_tier": rec.get("risk_tier", "low"),
                    "progress": rec.get("progress", "unknown"),
                })

        return active

    # -- recent completions ----------------------------------------------

    def get_recent_completions(
        self, business_id: str, days: int = 7,
    ) -> List[Dict[str, Any]]:
        """Return actions completed within the last *days* days."""
        records = self._load_execution_records(business_id)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        completions: List[Dict[str, Any]] = []
        for rec in records:
            state = rec.get("execution_state", rec.get("state", ""))
            if state != "completed":
                continue

            completed_at = rec.get("completed_at", "")
            dt = _parse_iso(completed_at)
            if dt is None or dt < cutoff:
                continue

            completions.append({
                "action_id": rec.get("action_id", rec.get("id", "")),
                "title": rec.get("title", ""),
                "action_type": rec.get("action_type", ""),
                "channel": rec.get("channel", ""),
                "completed_at": completed_at,
                "outcome_summary": rec.get("outcome_summary", rec.get("result_summary", "")),
            })

        # Sort by completion date descending
        completions.sort(key=lambda c: c.get("completed_at", ""), reverse=True)
        return completions

    # -- failures --------------------------------------------------------

    def get_failures(self, business_id: str) -> List[Dict[str, Any]]:
        """Return failed actions with error details and suggested recovery."""
        records = self._load_execution_records(business_id)
        failures: List[Dict[str, Any]] = []

        for rec in records:
            state = rec.get("execution_state", rec.get("state", ""))
            if state != "failed":
                continue

            failure_reason = rec.get("failure_reason", "Unknown error")
            recovery = self._suggest_recovery(failure_reason, rec)

            failures.append({
                "action_id": rec.get("action_id", rec.get("id", "")),
                "title": rec.get("title", ""),
                "action_type": rec.get("action_type", ""),
                "channel": rec.get("channel", ""),
                "failed_at": rec.get("failed_at", ""),
                "failure_reason": failure_reason,
                "error_details": rec.get("error_details", {}),
                "retry_count": rec.get("retry_count", 0),
                "max_retries": rec.get("max_retries", 3),
                "suggested_recovery": recovery,
            })

        return failures

    # -- retry -----------------------------------------------------------

    def retry_action(self, action_id: str) -> Dict[str, Any]:
        """Retry a failed action.

        Increments retry_count, resets the execution state to
        ``approved_waiting``, and persists the update.  If the action
        has exceeded its max_retries, returns a failure result.
        """
        record = self._find_record(action_id)
        if record is None:
            return {"success": False, "reason": f"Action {action_id} not found."}

        state = record.get("execution_state", record.get("state", ""))
        if state != "failed":
            return {"success": False, "reason": f"Action is not in failed state (current: {state})."}

        retry_count = record.get("retry_count", 0)
        max_retries = record.get("max_retries", 3)

        if retry_count >= max_retries:
            return {
                "success": False,
                "reason": f"Max retries ({max_retries}) exceeded. Consider an alternative approach or escalate.",
                "retry_count": retry_count,
                "max_retries": max_retries,
            }

        record["retry_count"] = retry_count + 1
        record["execution_state"] = "approved_waiting"
        record["state"] = "approved_waiting"
        record["failed_at"] = None
        record["failure_reason"] = None
        record["error_details"] = None

        self._persist_record(record)

        return {
            "success": True,
            "retry_number": retry_count + 1,
            "next_attempt_at": _utc_now(),
            "action_id": action_id,
        }

    # -- upcoming --------------------------------------------------------

    def get_upcoming(self, business_id: str) -> List[Dict[str, Any]]:
        """Return scheduled actions sorted by execution date ascending."""
        records = self._load_execution_records(business_id)
        upcoming: List[Dict[str, Any]] = []

        for rec in records:
            state = rec.get("execution_state", rec.get("state", ""))
            if state != "scheduled":
                continue

            upcoming.append({
                "action_id": rec.get("action_id", rec.get("id", "")),
                "title": rec.get("title", ""),
                "action_type": rec.get("action_type", ""),
                "channel": rec.get("channel", ""),
                "scheduled_for": rec.get("scheduled_for", ""),
                "risk_tier": rec.get("risk_tier", "low"),
            })

        upcoming.sort(key=lambda u: u.get("scheduled_for", ""))
        return upcoming

    # -- private helpers -------------------------------------------------

    def _load_execution_records(self, business_id: str) -> List[Dict[str, Any]]:
        """Load all execution records for a business from disk.

        Checks multiple directories: proposals, history, and execution.
        """
        records: List[Dict[str, Any]] = []
        search_dirs = [
            os.path.join(self.workspace_dir, "proposals", business_id),
            os.path.join(self.workspace_dir, "history", business_id),
            os.path.join(self.workspace_dir, business_id, "execution"),
        ]

        seen_ids: set = set()
        for dirpath in search_dirs:
            if not os.path.isdir(dirpath):
                continue
            for fname in os.listdir(dirpath):
                if not fname.endswith(".json") and not fname.endswith(".jsonl"):
                    continue
                filepath = os.path.join(dirpath, fname)
                if fname.endswith(".jsonl"):
                    records.extend(self._read_jsonl(filepath, seen_ids))
                else:
                    data = _load_json_file(filepath)
                    if data is not None:
                        aid = data.get("action_id", data.get("id", ""))
                        if aid and aid not in seen_ids:
                            seen_ids.add(aid)
                            records.append(data)

        return records

    @staticmethod
    def _read_jsonl(path: str, seen_ids: set) -> List[Dict[str, Any]]:
        """Read JSONL records, deduplicating by action_id."""
        records: List[Dict[str, Any]] = []
        try:
            with open(path, "r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    data = json.loads(line)
                    aid = data.get("action_id", data.get("id", ""))
                    if aid and aid not in seen_ids:
                        seen_ids.add(aid)
                        records.append(data)
        except Exception:
            pass
        return records

    def _find_record(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Find a single execution record by action_id across all businesses."""
        # Scan workspace for any business directory containing this action
        for subdir in ("proposals", "history"):
            root = os.path.join(self.workspace_dir, subdir)
            if not os.path.isdir(root):
                continue
            for biz_dir in os.listdir(root):
                biz_path = os.path.join(root, biz_dir)
                if not os.path.isdir(biz_path):
                    continue
                for fname in os.listdir(biz_path):
                    if not fname.endswith(".json"):
                        continue
                    data = _load_json_file(os.path.join(biz_path, fname))
                    if data is not None:
                        aid = data.get("action_id", data.get("id", ""))
                        if aid == action_id:
                            data["_file_path"] = os.path.join(biz_path, fname)
                            return data
        return None

    def _persist_record(self, record: Dict[str, Any]) -> None:
        """Persist a modified record back to disk."""
        file_path = record.pop("_file_path", None)
        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as fh:
                    json.dump(record, fh, indent=2, default=str)
            except Exception:
                pass

    @staticmethod
    def _suggest_recovery(failure_reason: str, record: Dict[str, Any]) -> str:
        """Suggest a recovery action based on the failure reason."""
        reason_lower = failure_reason.lower()

        if any(kw in reason_lower for kw in ("timeout", "timed out", "rate limit", "429", "503")):
            return "Transient error -- retry is likely to succeed."

        if any(kw in reason_lower for kw in ("disapproved", "rejected", "policy", "violation")):
            return "Content was rejected by the platform. Review and revise the creative, then retry."

        if any(kw in reason_lower for kw in ("auth", "unauthorized", "403", "401", "credential")):
            return "Authentication failure. Verify API credentials and permissions, then retry."

        if any(kw in reason_lower for kw in ("invalid", "config", "missing field", "schema")):
            return "Configuration error. Review the action parameters and fix the issue before retrying."

        if any(kw in reason_lower for kw in ("budget", "spend", "billing")):
            return "Budget or billing issue. Check account balance and spending limits."

        retry_count = record.get("retry_count", 0)
        max_retries = record.get("max_retries", 3)
        if retry_count >= max_retries:
            return "Max retries exceeded. Escalate to operator for manual intervention or try an alternative approach."

        return "Unknown error. Review error details and consider retrying or escalating."
