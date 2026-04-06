"""Immutable audit trail for the Kai Marketing OS.

Every other system in Kai writes to this trail: approvals, executions,
content publishing, budget spending, profile changes, kill switch
activations, and operator overrides.  The trail is append-only -- entries
can never be modified or deleted after creation.  This ensures the
integrity of the record even if something goes wrong.

Each entry includes a SHA-256 checksum of its content for integrity
verification.  Files are organized as JSONL by business_id and
year-month for efficient querying and archival.

Usage::

    from kai.compliance.audit_trail import (
        AuditTrail,
        create_audit_entry,
        log_approval,
        log_execution,
        log_compliance_violation,
    )

    trail = AuditTrail(base_dir="workspace")
    entry = create_audit_entry(
        actor="operator",
        action_type="action_approved",
        business_id="biz_abc123",
        description="Approved email campaign for Q2 launch",
    )
    entry_id = trail.append(entry)

    # Query recent entries
    entries = trail.query("biz_abc123", limit=50)

    # Verify integrity
    report = trail.verify_integrity("biz_abc123", "2026-04")

Design notes
------------
- Uses dataclass + SerializableModel pattern from ``kai/runtime/models.py``.
- File I/O follows patterns from ``kai/runtime/actions.py`` (atomic helpers,
  thread safety, JSON conventions).
- JSONL format: one JSON object per line for efficient append and streaming.
- No external dependencies beyond stdlib (hashlib, json, threading, pathlib).
"""

from __future__ import annotations

import hashlib
import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Serialization helper (matches kai.runtime.models.SerializableModel)
# ---------------------------------------------------------------------------


class SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _new_id(prefix: str) -> str:
    """Generate a prefixed unique ID using 12 hex characters."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    """Create a directory and all parents if they don't exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _json_compact(obj: Any) -> str:
    """Serialize to compact JSON with sorted keys for deterministic output."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def _parse_date(date_str: str) -> datetime:
    """Parse an ISO 8601 date/datetime string to a datetime.

    Handles date-only strings (``2026-04-02``), full ISO timestamps,
    and the ``Z`` suffix.
    """
    if not date_str:
        return datetime.min.replace(tzinfo=timezone.utc)

    # Date-only: "2026-04-02"
    if len(date_str) == 10 and date_str.count("-") == 2:
        return datetime.fromisoformat(date_str + "T00:00:00+00:00")

    cleaned = date_str.replace("Z", "+00:00")
    try:
        dt = datetime.fromisoformat(cleaned)
    except ValueError:
        # Strip microseconds and retry
        if "." in cleaned:
            cleaned = cleaned.split(".")[0] + cleaned[cleaned.rfind("+"):]
            dt = datetime.fromisoformat(cleaned)
        else:
            raise

    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _year_month(date_str: str) -> str:
    """Extract YYYY-MM from an ISO date string."""
    dt = _parse_date(date_str)
    return f"{dt.year:04d}-{dt.month:02d}"


# ============================================================================
# Enums
# ============================================================================


class AuditActor(str, Enum):
    """Who or what performed the audited action."""

    system = "system"
    """Automated system action."""

    operator = "operator"
    """Human operator action."""

    agent = "agent"
    """AI agent decision."""

    scheduler = "scheduler"
    """Scheduled or cron action."""

    compliance_engine = "compliance_engine"
    """Compliance check result."""

    watcher = "watcher"
    """Background watcher finding."""


class AuditActionType(str, Enum):
    """What type of action is being recorded."""

    finding_generated = "finding_generated"
    """Audit finding created."""

    action_proposed = "action_proposed"
    """Marketing action proposed."""

    action_approved = "action_approved"
    """Action approved by operator or auto-approved."""

    action_rejected = "action_rejected"
    """Action rejected by operator."""

    action_revised = "action_revised"
    """Action revised after rejection."""

    action_executed = "action_executed"
    """Action executed/deployed."""

    action_failed = "action_failed"
    """Action execution failed."""

    action_rolled_back = "action_rolled_back"
    """Action was rolled back."""

    content_created = "content_created"
    """Content asset created."""

    content_published = "content_published"
    """Content published to a channel."""

    content_unpublished = "content_unpublished"
    """Content removed from a channel."""

    budget_spent = "budget_spent"
    """Ad spend or budget allocation."""

    profile_updated = "profile_updated"
    """Business profile changed."""

    workspace_updated = "workspace_updated"
    """Workspace state changed."""

    compliance_check = "compliance_check"
    """Compliance check performed."""

    compliance_violation = "compliance_violation"
    """Compliance violation detected."""

    kill_switch_activated = "kill_switch_activated"
    """Kill switch triggered."""

    kill_switch_deactivated = "kill_switch_deactivated"
    """Kill switch lifted."""

    operator_override = "operator_override"
    """Operator overrode a system decision."""

    watcher_finding = "watcher_finding"
    """Background watcher produced a finding."""

    memory_updated = "memory_updated"
    """Learning/memory entry written."""

    escalation = "escalation"
    """Action or decision escalated to higher authority."""


# ============================================================================
# Model
# ============================================================================


@dataclass
class AuditEntry(SerializableModel):
    """A single immutable audit trail entry.

    Once appended, an entry's content must never change.  The checksum
    field is computed at append time and can be used to verify integrity.
    """

    id: str
    """Format ``audit_{uuid_hex[:12]}``."""

    timestamp: str
    """ISO timestamp (UTC) when the event occurred."""

    actor: str
    """AuditActor enum value."""

    actor_id: Optional[str] = None
    """Specific identifier (operator name, agent id, watcher name)."""

    action_type: str = ""
    """AuditActionType enum value."""

    action_id: Optional[str] = None
    """Reference to the ProposedAction, finding, or other object."""

    business_id: str = ""
    """Which business this relates to."""

    description: str = ""
    """Human-readable description of what happened."""

    before_state: Optional[Dict[str, Any]] = None
    """State before the action (for profile/workspace updates)."""

    after_state: Optional[Dict[str, Any]] = None
    """State after the action."""

    approval_status: Optional[str] = None
    """One of: auto_approved, operator_approved, operator_rejected, or None."""

    spend_amount: Optional[float] = None
    """If this involved budget spend."""

    channel: Optional[str] = None
    """Which marketing channel."""

    risk_tier: Optional[str] = None
    """Risk tier of the action."""

    compliance_status: Optional[str] = None
    """One of: pass, fail, warning (if compliance was checked)."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional context."""

    parent_entry_id: Optional[str] = None
    """For linking related audit entries."""

    checksum: Optional[str] = None
    """SHA-256 hash of the entry content for integrity verification."""


# ============================================================================
# AuditTrail
# ============================================================================


class AuditTrail:
    """Append-only audit log manager.

    Stores entries as JSONL files organized by business and month:
    ``{base_dir}/{business_id}/audit/{YYYY-MM}.jsonl``.

    All append operations are thread-safe via a ``threading.Lock``.
    The trail never modifies or overwrites existing lines.

    Parameters
    ----------
    base_dir : str
        Base directory for audit files (typically ``workspace/``).
    """

    def __init__(self, base_dir: str) -> None:
        self._base_dir = Path(base_dir)
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def append(self, entry: AuditEntry) -> str:
        """Append an audit entry to the trail.

        Computes the SHA-256 checksum, determines the file path from
        the business_id and timestamp, and appends the entry as a
        single line to the JSONL file.

        CRITICAL: This method is append-only.  It opens the file in
        append mode (``"a"``), never write mode (``"w"``).

        Parameters
        ----------
        entry : AuditEntry
            The audit entry to persist.

        Returns
        -------
        str
            The entry id.
        """
        # Compute and set checksum
        entry.checksum = self._compute_checksum(entry)

        # Determine file path
        file_path = self._get_file_path(entry.business_id, entry.timestamp)

        # Serialize to a single compact JSON line
        entry_dict = entry.model_dump()
        line = json.dumps(entry_dict, sort_keys=True, default=str)

        with self._lock:
            _ensure_dir(file_path.parent)
            # APPEND ONLY -- never "w" mode
            with open(file_path, "a", encoding="utf-8") as f:
                f.write(line + "\n")

        return entry.id

    def _compute_checksum(self, entry: AuditEntry) -> str:
        """Compute SHA-256 checksum of an entry's content.

        Serializes the entry to JSON with sorted keys, excluding the
        checksum field itself, for deterministic output.

        Parameters
        ----------
        entry : AuditEntry
            The entry to checksum.

        Returns
        -------
        str
            SHA-256 hex digest.
        """
        entry_dict = entry.model_dump()
        # Exclude checksum field from the hash input
        entry_dict.pop("checksum", None)
        serialized = _json_compact(entry_dict)
        return hashlib.sha256(serialized.encode("utf-8")).hexdigest()

    def _get_file_path(self, business_id: str, date: str) -> Path:
        """Determine the JSONL file path for a business and date.

        Parameters
        ----------
        business_id : str
            The business identifier.
        date : str
            An ISO date or timestamp string.

        Returns
        -------
        Path
            Path to the JSONL file: ``{base_dir}/{business_id}/audit/{YYYY-MM}.jsonl``
        """
        ym = _year_month(date)
        return self._base_dir / business_id / "audit" / f"{ym}.jsonl"

    # ------------------------------------------------------------------
    # Query operations
    # ------------------------------------------------------------------

    def query(
        self,
        business_id: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        actor: Optional[str] = None,
        action_type: Optional[str] = None,
        action_id: Optional[str] = None,
        channel: Optional[str] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[AuditEntry]:
        """Query audit entries with filters and pagination.

        Reads the relevant JSONL files for the date range, applies
        filters, and returns matching entries sorted by timestamp
        descending (most recent first).

        Parameters
        ----------
        business_id : str
            The business to query.
        start_date : str, optional
            ISO date/datetime -- only entries at or after this time.
        end_date : str, optional
            ISO date/datetime -- only entries at or before this time.
        actor : str, optional
            Filter by actor type.
        action_type : str, optional
            Filter by action type.
        action_id : str, optional
            Filter by action id.
        channel : str, optional
            Filter by channel.
        limit : int
            Maximum entries to return (default 100).
        offset : int
            Number of entries to skip (default 0).

        Returns
        -------
        list of AuditEntry
            Matching entries, most recent first.
        """
        # Determine which JSONL files to read
        file_paths = self._resolve_files(business_id, start_date, end_date)

        # Parse filters
        start_dt = _parse_date(start_date) if start_date else None
        end_dt = _parse_date(end_date) if end_date else None

        entries: List[AuditEntry] = []

        for file_path in file_paths:
            if not file_path.exists():
                continue
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    # Apply filters
                    if start_dt or end_dt:
                        entry_dt = _parse_date(data.get("timestamp", ""))
                        if start_dt and entry_dt < start_dt:
                            continue
                        if end_dt and entry_dt > end_dt:
                            continue

                    if actor and data.get("actor") != actor:
                        continue
                    if action_type and data.get("action_type") != action_type:
                        continue
                    if action_id and data.get("action_id") != action_id:
                        continue
                    if channel and data.get("channel") != channel:
                        continue

                    entries.append(_dict_to_audit_entry(data))

        # Sort by timestamp descending (most recent first)
        entries.sort(key=lambda e: e.timestamp, reverse=True)

        # Apply pagination
        return entries[offset:offset + limit]

    def query_by_action(
        self,
        action_id: str,
        business_id: str,
    ) -> List[AuditEntry]:
        """Find all audit entries related to a specific action.

        Searches across all available JSONL files for the business.

        Parameters
        ----------
        action_id : str
            The action to search for.
        business_id : str
            The business the action belongs to.

        Returns
        -------
        list of AuditEntry
            Entries sorted by timestamp ascending (chronological).
        """
        audit_dir = self._base_dir / business_id / "audit"
        if not audit_dir.exists():
            return []

        entries: List[AuditEntry] = []

        for file_path in sorted(audit_dir.glob("*.jsonl")):
            with open(file_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)
                    except json.JSONDecodeError:
                        continue

                    if data.get("action_id") == action_id:
                        entries.append(_dict_to_audit_entry(data))

        # Sort chronologically (ascending)
        entries.sort(key=lambda e: e.timestamp)
        return entries

    def get_action_timeline(
        self,
        action_id: str,
        business_id: str,
    ) -> List[Dict[str, Any]]:
        """Return a clean timeline of an action's lifecycle.

        Parameters
        ----------
        action_id : str
            The action to trace.
        business_id : str
            The business the action belongs to.

        Returns
        -------
        list of dict
            Each entry: ``{timestamp, event_type, description, actor}``.
            Ordered chronologically.
        """
        entries = self.query_by_action(action_id, business_id)
        timeline: List[Dict[str, Any]] = []
        for entry in entries:
            timeline.append({
                "timestamp": entry.timestamp,
                "event_type": entry.action_type,
                "description": entry.description,
                "actor": entry.actor_id or entry.actor,
            })
        return timeline

    # ------------------------------------------------------------------
    # Integrity verification
    # ------------------------------------------------------------------

    def verify_integrity(
        self,
        business_id: str,
        month: str,
    ) -> Dict[str, Any]:
        """Verify the integrity of all entries in a JSONL file.

        Recomputes checksums for every entry and compares them against
        the stored checksums.

        Parameters
        ----------
        business_id : str
            The business to verify.
        month : str
            Year-month string (e.g., ``"2026-04"``).

        Returns
        -------
        dict
            ``{total_entries, verified_ok, verification_failures}``
            where ``verification_failures`` is a list of entry ids
            with mismatched checksums.
        """
        file_path = self._base_dir / business_id / "audit" / f"{month}.jsonl"
        result: Dict[str, Any] = {
            "total_entries": 0,
            "verified_ok": 0,
            "verification_failures": [],
        }

        if not file_path.exists():
            return result

        with open(file_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                except json.JSONDecodeError:
                    continue

                result["total_entries"] += 1
                entry = _dict_to_audit_entry(data)
                stored_checksum = entry.checksum

                # Recompute checksum
                recomputed = self._compute_checksum(entry)

                if stored_checksum == recomputed:
                    result["verified_ok"] += 1
                else:
                    result["verification_failures"].append(entry.id)

        return result

    # ------------------------------------------------------------------
    # Compliance report
    # ------------------------------------------------------------------

    def generate_compliance_report(
        self,
        business_id: str,
        start_date: str,
        end_date: str,
    ) -> Dict[str, Any]:
        """Generate a comprehensive compliance report for a date range.

        Queries all entries and compiles statistics covering actions,
        approvals, rejections, compliance events, spend, kill switch
        activations, and operator overrides.

        Parameters
        ----------
        business_id : str
            The business to report on.
        start_date : str
            ISO date/datetime -- report start.
        end_date : str
            ISO date/datetime -- report end.

        Returns
        -------
        dict
            Comprehensive compliance report.
        """
        # Fetch all entries in the range (use a high limit)
        entries = self.query(
            business_id=business_id,
            start_date=start_date,
            end_date=end_date,
            limit=100_000,
        )

        report: Dict[str, Any] = {
            "business_id": business_id,
            "report_period": {"start": start_date, "end": end_date},
            "generated_at": _now_iso(),
            "total_actions": 0,
            "approved_actions": 0,
            "rejected_actions": 0,
            "auto_approved_actions": 0,
            "compliance_checks": 0,
            "compliance_violations": [],
            "kill_switch_activations": [],
            "operator_overrides": [],
            "total_spend": 0.0,
            "spend_by_channel": {},
            "regulated_actions": [],
        }

        # Regulated categories for special tracking
        regulated_keywords = {"healthcare", "financial", "legal", "medical", "pharma", "insurance"}

        for entry in entries:
            action_type = entry.action_type

            # Count proposed actions
            if action_type == AuditActionType.action_proposed.value:
                report["total_actions"] += 1

            # Count approvals
            if action_type == AuditActionType.action_approved.value:
                report["approved_actions"] += 1
                if entry.approval_status == "auto_approved":
                    report["auto_approved_actions"] += 1

            # Count rejections
            if action_type == AuditActionType.action_rejected.value:
                report["rejected_actions"] += 1

            # Count compliance checks
            if action_type == AuditActionType.compliance_check.value:
                report["compliance_checks"] += 1

            # Track compliance violations
            if action_type == AuditActionType.compliance_violation.value:
                report["compliance_violations"].append({
                    "entry_id": entry.id,
                    "timestamp": entry.timestamp,
                    "action_id": entry.action_id,
                    "description": entry.description,
                    "compliance_status": entry.compliance_status,
                    "metadata": entry.metadata,
                })

            # Track kill switch events
            if action_type in (
                AuditActionType.kill_switch_activated.value,
                AuditActionType.kill_switch_deactivated.value,
            ):
                report["kill_switch_activations"].append({
                    "entry_id": entry.id,
                    "timestamp": entry.timestamp,
                    "event_type": action_type,
                    "description": entry.description,
                    "actor": entry.actor_id or entry.actor,
                    "metadata": entry.metadata,
                })

            # Track operator overrides
            if action_type == AuditActionType.operator_override.value:
                report["operator_overrides"].append({
                    "entry_id": entry.id,
                    "timestamp": entry.timestamp,
                    "action_id": entry.action_id,
                    "description": entry.description,
                    "actor": entry.actor_id or entry.actor,
                    "metadata": entry.metadata,
                })

            # Track spend
            if entry.spend_amount is not None and entry.spend_amount > 0:
                report["total_spend"] += entry.spend_amount
                ch = entry.channel or "unspecified"
                report["spend_by_channel"][ch] = (
                    report["spend_by_channel"].get(ch, 0.0) + entry.spend_amount
                )

            # Track regulated actions
            desc_lower = entry.description.lower()
            channel_lower = (entry.channel or "").lower()
            metadata_str = json.dumps(entry.metadata, default=str).lower()
            combined = f"{desc_lower} {channel_lower} {metadata_str}"
            if any(kw in combined for kw in regulated_keywords):
                if action_type in (
                    AuditActionType.action_proposed.value,
                    AuditActionType.action_approved.value,
                    AuditActionType.action_executed.value,
                ):
                    report["regulated_actions"].append({
                        "entry_id": entry.id,
                        "timestamp": entry.timestamp,
                        "action_id": entry.action_id,
                        "action_type": action_type,
                        "description": entry.description,
                        "approval_status": entry.approval_status,
                        "risk_tier": entry.risk_tier,
                        "channel": entry.channel,
                    })

        return report

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _resolve_files(
        self,
        business_id: str,
        start_date: Optional[str],
        end_date: Optional[str],
    ) -> List[Path]:
        """Determine which JSONL files to read for a query.

        If no date range is given, returns all JSONL files for the
        business.  Otherwise, returns only files whose year-month
        falls within the range.
        """
        audit_dir = self._base_dir / business_id / "audit"
        if not audit_dir.exists():
            return []

        all_files = sorted(audit_dir.glob("*.jsonl"))

        if not start_date and not end_date:
            return all_files

        # Extract year-month bounds
        start_ym = _year_month(start_date) if start_date else "0000-00"
        end_ym = _year_month(end_date) if end_date else "9999-99"

        matching: List[Path] = []
        for fp in all_files:
            # Filename is YYYY-MM.jsonl
            file_ym = fp.stem  # e.g., "2026-04"
            if start_ym <= file_ym <= end_ym:
                matching.append(fp)

        return matching


# ============================================================================
# Convenience functions
# ============================================================================


def _dict_to_audit_entry(data: Dict[str, Any]) -> AuditEntry:
    """Reconstruct an AuditEntry from a dict (loaded from JSONL).

    Handles missing fields gracefully by using defaults.
    """
    return AuditEntry(
        id=data.get("id", ""),
        timestamp=data.get("timestamp", ""),
        actor=data.get("actor", ""),
        actor_id=data.get("actor_id"),
        action_type=data.get("action_type", ""),
        action_id=data.get("action_id"),
        business_id=data.get("business_id", ""),
        description=data.get("description", ""),
        before_state=data.get("before_state"),
        after_state=data.get("after_state"),
        approval_status=data.get("approval_status"),
        spend_amount=data.get("spend_amount"),
        channel=data.get("channel"),
        risk_tier=data.get("risk_tier"),
        compliance_status=data.get("compliance_status"),
        metadata=data.get("metadata", {}),
        parent_entry_id=data.get("parent_entry_id"),
        checksum=data.get("checksum"),
    )


def create_audit_entry(
    actor: str,
    action_type: str,
    business_id: str,
    description: str,
    **kwargs: Any,
) -> AuditEntry:
    """Create an AuditEntry with automatic id and timestamp.

    The caller must still call ``trail.append(entry)`` to persist.

    Parameters
    ----------
    actor : str
        AuditActor enum value.
    action_type : str
        AuditActionType enum value.
    business_id : str
        Which business this relates to.
    description : str
        Human-readable description.
    **kwargs
        Optional fields: actor_id, action_id, before_state, after_state,
        approval_status, spend_amount, channel, risk_tier,
        compliance_status, metadata, parent_entry_id.

    Returns
    -------
    AuditEntry
        Ready for ``trail.append()``.
    """
    return AuditEntry(
        id=_new_id("audit"),
        timestamp=_now_iso(),
        actor=actor,
        action_type=action_type,
        business_id=business_id,
        description=description,
        actor_id=kwargs.get("actor_id"),
        action_id=kwargs.get("action_id"),
        before_state=kwargs.get("before_state"),
        after_state=kwargs.get("after_state"),
        approval_status=kwargs.get("approval_status"),
        spend_amount=kwargs.get("spend_amount"),
        channel=kwargs.get("channel"),
        risk_tier=kwargs.get("risk_tier"),
        compliance_status=kwargs.get("compliance_status"),
        metadata=kwargs.get("metadata", {}),
        parent_entry_id=kwargs.get("parent_entry_id"),
    )


def log_approval(
    trail: AuditTrail,
    action_id: str,
    business_id: str,
    approved_by: str,
    route: str,
    risk_tier: str,
    spend: Optional[float] = None,
) -> str:
    """Create and append an approval audit entry.

    Parameters
    ----------
    trail : AuditTrail
        The audit trail to write to.
    action_id : str
        The approved action.
    business_id : str
        The business this belongs to.
    approved_by : str
        Who approved (operator name or "system" for auto-approve).
    route : str
        The approval route that was used.
    risk_tier : str
        Risk tier of the action.
    spend : float, optional
        If the action involves spend.

    Returns
    -------
    str
        The audit entry id.
    """
    approval_status = "auto_approved" if approved_by == "system" else "operator_approved"
    entry = create_audit_entry(
        actor=AuditActor.operator.value if approved_by != "system" else AuditActor.system.value,
        action_type=AuditActionType.action_approved.value,
        business_id=business_id,
        description=f"Action {action_id} approved via {route} route by {approved_by}",
        actor_id=approved_by,
        action_id=action_id,
        approval_status=approval_status,
        spend_amount=spend,
        risk_tier=risk_tier,
        metadata={"route": route},
    )
    return trail.append(entry)


def log_execution(
    trail: AuditTrail,
    action_id: str,
    business_id: str,
    channel: str,
    description: str,
    success: bool,
) -> str:
    """Create and append an execution audit entry.

    Uses ``action_executed`` if success is True, ``action_failed`` if not.

    Parameters
    ----------
    trail : AuditTrail
        The audit trail to write to.
    action_id : str
        The executed action.
    business_id : str
        The business this belongs to.
    channel : str
        Which marketing channel.
    description : str
        What happened.
    success : bool
        Whether the execution succeeded.

    Returns
    -------
    str
        The audit entry id.
    """
    action_type = (
        AuditActionType.action_executed.value
        if success
        else AuditActionType.action_failed.value
    )
    entry = create_audit_entry(
        actor=AuditActor.system.value,
        action_type=action_type,
        business_id=business_id,
        description=description,
        action_id=action_id,
        channel=channel,
        metadata={"success": success},
    )
    return trail.append(entry)


def log_compliance_violation(
    trail: AuditTrail,
    action_id: str,
    business_id: str,
    violation_description: str,
    rule_id: str,
    severity: str,
) -> str:
    """Create and append a compliance violation audit entry.

    Parameters
    ----------
    trail : AuditTrail
        The audit trail to write to.
    action_id : str
        The action with the violation.
    business_id : str
        The business this belongs to.
    violation_description : str
        What the violation is.
    rule_id : str
        Which compliance rule was violated.
    severity : str
        Severity level (e.g., "critical", "high", "medium", "low").

    Returns
    -------
    str
        The audit entry id.
    """
    entry = create_audit_entry(
        actor=AuditActor.compliance_engine.value,
        action_type=AuditActionType.compliance_violation.value,
        business_id=business_id,
        description=violation_description,
        action_id=action_id,
        compliance_status="fail",
        metadata={"rule_id": rule_id, "severity": severity},
    )
    return trail.append(entry)
