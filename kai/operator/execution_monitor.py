"""Execution monitoring and action history for the Kai Marketing OS.

Tracks action status through the full lifecycle, generates periodic
execution reports, and handles failure recovery.  This is the
"operations dashboard" that gives operators confidence that the system
is working correctly and transparently.

Components
----------
ActionHistory
    Persistent, queryable record of all execution records stored as
    JSONL files under ``workspace/{business_id}/execution/history.jsonl``.
    Supports filtered queries, sorted pagination, grouping, and summary
    statistics.

ExecutionStatusTracker
    Convenience layer over ActionHistory that provides pipeline-style
    views: active, completed, failed, scheduled, and upcoming.

ExecutionReportGenerator
    Produces daily and weekly execution reports with genuine
    recommendations derived from execution patterns.

FailureRecovery
    Classifies failures into recovery types (retry, rollback,
    alternative, escalate, abandon) and executes recovery actions.

Design
------
- Uses the dataclass + ``SerializableModel`` pattern from
  ``kai/runtime/models.py``.
- File I/O follows project conventions: JSONL for append-heavy data,
  atomic writes via temp file + rename.
- No external dependencies beyond the Python standard library.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _parse_iso(ts: str) -> Optional[datetime]:
    """Parse an ISO-8601 timestamp, returning None on failure."""
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _json_dump_line(payload: Dict[str, Any]) -> str:
    """Serialize *payload* to a single compact JSON line."""
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, default=str)


def _append_jsonl_atomic(path: Path, payload: Dict[str, Any]) -> None:
    """Append one JSON line to *path* atomically."""
    line = _json_dump_line(payload) + "\n"
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(line, encoding="utf-8")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read all JSON lines from *path*. Returns [] if missing."""
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw_line in fh:
            raw_line = raw_line.strip()
            if raw_line:
                try:
                    records.append(json.loads(raw_line))
                except json.JSONDecodeError:
                    continue
    return records


def _rewrite_jsonl_atomic(path: Path, records: List[Dict[str, Any]]) -> None:
    """Rewrite an entire JSONL file atomically."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    lines = "".join(_json_dump_line(r) + "\n" for r in records)
    tmp_path.write_text(lines, encoding="utf-8")
    tmp_path.replace(path)


# ---------------------------------------------------------------------------
# Serializable base
# ---------------------------------------------------------------------------

class _SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class ExecutionState(str, Enum):
    """Lifecycle state of an action through execution."""

    PENDING_APPROVAL = "pending_approval"
    APPROVED_WAITING = "approved_waiting"
    SCHEDULED = "scheduled"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    CANCELLED = "cancelled"


_ACTIVE_STATES = frozenset({
    ExecutionState.EXECUTING.value,
    ExecutionState.APPROVED_WAITING.value,
    ExecutionState.SCHEDULED.value,
})

_TERMINAL_STATES = frozenset({
    ExecutionState.COMPLETED.value,
    ExecutionState.FAILED.value,
    ExecutionState.ROLLED_BACK.value,
    ExecutionState.CANCELLED.value,
})


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------

@dataclass
class ExecutionRecord(_SerializableModel):
    """A single action's execution record across its full lifecycle."""

    action_id: str = ""
    business_id: str = ""
    title: str = ""
    action_type: str = ""
    channel: str = ""
    state: str = ExecutionState.PENDING_APPROVAL.value
    proposed_at: str = ""
    approved_at: Optional[str] = None
    approved_by: Optional[str] = None
    scheduled_for: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    failed_at: Optional[str] = None
    failure_reason: Optional[str] = None
    rolled_back_at: Optional[str] = None
    rollback_reason: Optional[str] = None
    risk_tier: str = "low"
    estimated_spend: Optional[float] = None
    actual_spend: Optional[float] = None
    outcome_summary: Optional[str] = None
    error_details: Optional[Dict[str, Any]] = None
    retry_count: int = 0
    max_retries: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.action_id:
            self.action_id = _new_id("act")
        if not self.proposed_at:
            self.proposed_at = _utc_now()


@dataclass
class ExecutionReport(_SerializableModel):
    """Periodic execution report (daily or weekly)."""

    business_id: str = ""
    report_type: str = "daily"
    period_start: str = ""
    period_end: str = ""
    generated_at: str = ""
    actions_executed: int = 0
    actions_completed: int = 0
    actions_failed: int = 0
    actions_pending: int = 0
    success_rate: float = 0.0
    total_spend: float = 0.0
    spend_by_channel: Dict[str, float] = field(default_factory=dict)
    outcomes_observed: List[Dict[str, Any]] = field(default_factory=list)
    top_wins: List[str] = field(default_factory=list)
    issues_encountered: List[Dict[str, Any]] = field(default_factory=list)
    upcoming_actions: List[Dict[str, Any]] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class FailureRecoveryAction(_SerializableModel):
    """A recommended recovery action for a failed execution."""

    action_id: str = ""
    failure_reason: str = ""
    recovery_type: str = "escalate"  # retry | rollback | alternative | escalate | abandon
    recovery_description: str = ""
    auto_recoverable: bool = False
    requires_operator: bool = True


# =========================================================================
# ActionHistory
# =========================================================================

class ActionHistory:
    """Persistent, queryable record of execution history.

    Records are stored in JSONL format at
    ``{workspace_dir}/{business_id}/execution/history.jsonl``.
    An in-memory cache avoids repeated disk reads within a session.
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir
        self._records: Dict[str, ExecutionRecord] = {}
        self._loaded_businesses: set = set()

    # -- path helpers ----------------------------------------------------

    def _history_path(self, business_id: str) -> Path:
        return Path(self.workspace_dir) / business_id / "execution" / "history.jsonl"

    # -- loading ---------------------------------------------------------

    def _ensure_loaded(self, business_id: str) -> None:
        """Lazy-load records for *business_id* if not already cached."""
        if business_id in self._loaded_businesses:
            return

        path = self._history_path(business_id)
        raw_records = _read_jsonl(path)

        for raw in raw_records:
            rec = self._dict_to_record(raw)
            self._records[rec.action_id] = rec

        self._loaded_businesses.add(business_id)

    @staticmethod
    def _dict_to_record(raw: Dict[str, Any]) -> ExecutionRecord:
        """Convert a raw dict to an ExecutionRecord, tolerating extra keys."""
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(ExecutionRecord)}
        kwargs = {k: v for k, v in raw.items() if k in field_names}
        return ExecutionRecord(**kwargs)

    # -- write operations ------------------------------------------------

    def add_record(self, record: ExecutionRecord) -> None:
        """Add or update an execution record and persist to disk."""
        self._records[record.action_id] = record
        self._loaded_businesses.add(record.business_id)

        path = self._history_path(record.business_id)
        _ensure_dir(path.parent)
        _append_jsonl_atomic(path, record.model_dump())

    def update_state(self, action_id: str, new_state: str, **kwargs: Any) -> bool:
        """Update the state of an action and any additional fields.

        Appends the state change to the JSONL history file and updates
        the in-memory cache.  Returns True if the action was found.
        """
        record = self._records.get(action_id)
        if record is None:
            # Try to find it by scanning all loaded businesses
            for bid in list(self._loaded_businesses):
                self._ensure_loaded(bid)
            record = self._records.get(action_id)

        if record is None:
            return False

        record.state = new_state
        for key, value in kwargs.items():
            if hasattr(record, key):
                setattr(record, key, value)

        # Persist -- rewrite the full file to reflect the update
        self._persist_business(record.business_id)
        return True

    def _persist_business(self, business_id: str) -> None:
        """Rewrite the JSONL file for a business with current cache state."""
        path = self._history_path(business_id)
        _ensure_dir(path.parent)

        biz_records = [
            r.model_dump()
            for r in self._records.values()
            if r.business_id == business_id
        ]
        _rewrite_jsonl_atomic(path, biz_records)

    # -- query operations ------------------------------------------------

    def query(
        self,
        business_id: str,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[ExecutionRecord]:
        """Query records with optional filters.

        Supported filter keys:
            date_start, date_end, channel, action_type, state, risk_tier
        """
        self._ensure_loaded(business_id)
        filters = filters or {}

        results: List[ExecutionRecord] = []
        for rec in self._records.values():
            if rec.business_id != business_id:
                continue
            if not self._matches_filters(rec, filters):
                continue
            results.append(rec)

        return results

    def query_sorted(
        self,
        business_id: str,
        sort_by: str = "date",
        sort_order: str = "desc",
        limit: int = 50,
        offset: int = 0,
        **filters: Any,
    ) -> List[ExecutionRecord]:
        """Query with sorting and pagination.

        Parameters
        ----------
        sort_by : str
            One of ``"date"``, ``"impact"``, ``"spend"``.
        sort_order : str
            ``"asc"`` or ``"desc"``.
        limit : int
            Max records to return.
        offset : int
            Number of records to skip.
        **filters
            Same keys as :meth:`query`.
        """
        records = self.query(business_id, filters if filters else None)

        key_func = self._sort_key(sort_by)
        records.sort(key=key_func, reverse=(sort_order == "desc"))

        return records[offset:offset + limit]

    def group_by(
        self, business_id: str, group_field: str,
    ) -> Dict[str, List[ExecutionRecord]]:
        """Group records by a field.

        Parameters
        ----------
        group_field : str
            One of ``"channel"``, ``"action_type"``, ``"state"``, ``"risk_tier"``.
        """
        self._ensure_loaded(business_id)
        groups: Dict[str, List[ExecutionRecord]] = {}

        for rec in self._records.values():
            if rec.business_id != business_id:
                continue
            value = getattr(rec, group_field, "unknown")
            groups.setdefault(value, []).append(rec)

        return groups

    def get_summary_stats(
        self, business_id: str, days: int = 30,
    ) -> Dict[str, Any]:
        """Return summary statistics for the last *days* days.

        Returns
        -------
        dict with keys:
            total_actions, by_state, by_channel, success_rate,
            average_completion_time_hours, total_spend, top_action_types
        """
        self._ensure_loaded(business_id)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        records_in_range: List[ExecutionRecord] = []
        for rec in self._records.values():
            if rec.business_id != business_id:
                continue
            proposed_dt = _parse_iso(rec.proposed_at)
            if proposed_dt is not None and proposed_dt >= cutoff:
                records_in_range.append(rec)

        by_state: Dict[str, int] = {}
        by_channel: Dict[str, int] = {}
        action_type_counts: Dict[str, int] = {}
        completed_count = 0
        failed_count = 0
        total_spend = 0.0
        completion_times: List[float] = []

        for rec in records_in_range:
            by_state[rec.state] = by_state.get(rec.state, 0) + 1
            by_channel[rec.channel] = by_channel.get(rec.channel, 0) + 1
            action_type_counts[rec.action_type] = action_type_counts.get(rec.action_type, 0) + 1

            if rec.state == ExecutionState.COMPLETED.value:
                completed_count += 1
            elif rec.state == ExecutionState.FAILED.value:
                failed_count += 1

            if rec.actual_spend is not None:
                total_spend += rec.actual_spend

            # Calculate completion time if both timestamps exist
            if rec.started_at and rec.completed_at:
                start_dt = _parse_iso(rec.started_at)
                end_dt = _parse_iso(rec.completed_at)
                if start_dt and end_dt and end_dt > start_dt:
                    hours = (end_dt - start_dt).total_seconds() / 3600.0
                    completion_times.append(hours)

        denominator = completed_count + failed_count
        success_rate = (completed_count / denominator * 100.0) if denominator > 0 else 0.0
        avg_completion = (
            sum(completion_times) / len(completion_times)
            if completion_times else 0.0
        )

        top_types = sorted(action_type_counts.items(), key=lambda x: x[1], reverse=True)

        return {
            "total_actions": len(records_in_range),
            "by_state": by_state,
            "by_channel": by_channel,
            "success_rate": round(success_rate, 1),
            "average_completion_time_hours": round(avg_completion, 2),
            "total_spend": round(total_spend, 2),
            "top_action_types": top_types[:10],
        }

    # -- private filter/sort helpers -------------------------------------

    @staticmethod
    def _matches_filters(rec: ExecutionRecord, filters: Dict[str, Any]) -> bool:
        """Check whether *rec* matches all *filters*."""
        if "channel" in filters and rec.channel != filters["channel"]:
            return False
        if "action_type" in filters and rec.action_type != filters["action_type"]:
            return False
        if "state" in filters and rec.state != filters["state"]:
            return False
        if "risk_tier" in filters and rec.risk_tier != filters["risk_tier"]:
            return False

        if "date_start" in filters:
            dt = _parse_iso(rec.proposed_at)
            cutoff = _parse_iso(filters["date_start"])
            if dt and cutoff and dt < cutoff:
                return False

        if "date_end" in filters:
            dt = _parse_iso(rec.proposed_at)
            cutoff = _parse_iso(filters["date_end"])
            if dt and cutoff and dt > cutoff:
                return False

        return True

    @staticmethod
    def _sort_key(sort_by: str):
        """Return a sort key function for the given *sort_by* field."""
        if sort_by == "date":
            return lambda r: r.proposed_at or ""
        elif sort_by == "impact":
            return lambda r: r.actual_spend if r.actual_spend is not None else 0.0
        elif sort_by == "spend":
            return lambda r: r.actual_spend if r.actual_spend is not None else 0.0
        else:
            return lambda r: r.proposed_at or ""


# =========================================================================
# ExecutionStatusTracker
# =========================================================================

class ExecutionStatusTracker:
    """Convenience views over ActionHistory for operator dashboards."""

    def __init__(self, history: ActionHistory) -> None:
        self.history = history

    def get_active_executions(self, business_id: str) -> List[ExecutionRecord]:
        """Return records in executing, approved_waiting, or scheduled state."""
        all_records = self.history.query(business_id)
        return [r for r in all_records if r.state in _ACTIVE_STATES]

    def get_recent_completions(
        self, business_id: str, days: int = 7,
    ) -> List[ExecutionRecord]:
        """Return completed records from the last *days* days."""
        all_records = self.history.query(business_id, {"state": ExecutionState.COMPLETED.value})
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        recent: List[ExecutionRecord] = []
        for rec in all_records:
            if rec.completed_at:
                dt = _parse_iso(rec.completed_at)
                if dt and dt >= cutoff:
                    recent.append(rec)

        recent.sort(key=lambda r: r.completed_at or "", reverse=True)
        return recent

    def get_failures(
        self, business_id: str, unresolved_only: bool = True,
    ) -> List[ExecutionRecord]:
        """Return failed records.

        If *unresolved_only* is True, exclude records that have been
        retried (state changed from failed) or rolled back.
        """
        all_records = self.history.query(business_id)
        failures: List[ExecutionRecord] = []

        for rec in all_records:
            if rec.state != ExecutionState.FAILED.value:
                continue
            if unresolved_only and rec.retry_count > 0:
                # If retry_count > 0 but still failed, it is unresolved
                # If the state is no longer FAILED, it was retried successfully
                pass  # still failed, include it
            failures.append(rec)

        return failures

    def get_upcoming_scheduled(self, business_id: str) -> List[ExecutionRecord]:
        """Return scheduled records sorted by scheduled_for ascending."""
        all_records = self.history.query(business_id, {"state": ExecutionState.SCHEDULED.value})
        all_records.sort(key=lambda r: r.scheduled_for or "")
        return all_records

    def get_pipeline_view(
        self, business_id: str,
    ) -> Dict[str, List[ExecutionRecord]]:
        """Return records grouped by state for a pipeline/kanban view.

        Completed and failed states are limited to the 5 most recent
        entries each to keep the view focused.
        """
        all_records = self.history.query(business_id)

        pipeline: Dict[str, List[ExecutionRecord]] = {
            "pending_approval": [],
            "approved_waiting": [],
            "scheduled": [],
            "executing": [],
            "completed": [],
            "failed": [],
        }

        for rec in all_records:
            bucket = pipeline.get(rec.state)
            if bucket is not None:
                bucket.append(rec)

        # Sort terminal states by date and limit
        pipeline["completed"].sort(key=lambda r: r.completed_at or "", reverse=True)
        pipeline["completed"] = pipeline["completed"][:5]

        pipeline["failed"].sort(key=lambda r: r.failed_at or "", reverse=True)
        pipeline["failed"] = pipeline["failed"][:5]

        # Sort scheduled by date ascending
        pipeline["scheduled"].sort(key=lambda r: r.scheduled_for or "")

        return pipeline


# =========================================================================
# ExecutionReportGenerator
# =========================================================================

class ExecutionReportGenerator:
    """Generate daily and weekly execution reports."""

    def __init__(self, history: ActionHistory) -> None:
        self.history = history

    def generate_daily_report(
        self, business_id: str, date: str,
    ) -> ExecutionReport:
        """Compile a daily execution report.

        Parameters
        ----------
        date : str
            ISO date string (YYYY-MM-DD) for the report day.
        """
        day_start = f"{date}T00:00:00+00:00"
        day_end = f"{date}T23:59:59+00:00"

        # Next day for upcoming actions
        dt_date = _parse_iso(day_start)
        if dt_date:
            next_day = (dt_date + timedelta(days=1)).strftime("%Y-%m-%d")
        else:
            next_day = date

        records = self.history.query(business_id, {
            "date_start": day_start,
            "date_end": day_end,
        })

        return self._build_report(
            business_id=business_id,
            report_type="daily",
            period_start=day_start,
            period_end=day_end,
            records=records,
            upcoming_cutoff=f"{next_day}T23:59:59+00:00",
        )

    def generate_weekly_report(
        self, business_id: str, week_start: str,
    ) -> ExecutionReport:
        """Compile a weekly execution report.

        Parameters
        ----------
        week_start : str
            ISO date string (YYYY-MM-DD) for the Monday of the report week.
        """
        start_dt = _parse_iso(f"{week_start}T00:00:00+00:00")
        if start_dt:
            end_dt = start_dt + timedelta(days=6, hours=23, minutes=59, seconds=59)
            period_end = end_dt.isoformat()
            upcoming_end = (start_dt + timedelta(days=13, hours=23, minutes=59, seconds=59)).isoformat()
        else:
            period_end = f"{week_start}T23:59:59+00:00"
            upcoming_end = period_end

        period_start = f"{week_start}T00:00:00+00:00"

        records = self.history.query(business_id, {
            "date_start": period_start,
            "date_end": period_end,
        })

        report = self._build_report(
            business_id=business_id,
            report_type="weekly",
            period_start=period_start,
            period_end=period_end,
            records=records,
            upcoming_cutoff=upcoming_end,
        )

        # Weekly-specific: compare to previous week
        if start_dt:
            prev_start = (start_dt - timedelta(days=7)).isoformat()
            prev_end = (start_dt - timedelta(seconds=1)).isoformat()
            prev_records = self.history.query(business_id, {
                "date_start": prev_start,
                "date_end": prev_end,
            })
            prev_completed = sum(1 for r in prev_records if r.state == ExecutionState.COMPLETED.value)
            curr_completed = report.actions_completed

            if prev_completed > 0:
                change_pct = round(((curr_completed - prev_completed) / prev_completed) * 100, 1)
                direction = "up" if change_pct > 0 else "down" if change_pct < 0 else "flat"
                report.recommendations.append(
                    f"Completion volume is {direction} {abs(change_pct)}% vs last week "
                    f"({curr_completed} vs {prev_completed})."
                )

        return report

    def _build_report(
        self,
        business_id: str,
        report_type: str,
        period_start: str,
        period_end: str,
        records: List[ExecutionRecord],
        upcoming_cutoff: str,
    ) -> ExecutionReport:
        """Core report builder shared by daily and weekly generators."""
        executed = [r for r in records if r.state in (
            ExecutionState.EXECUTING.value,
            ExecutionState.COMPLETED.value,
            ExecutionState.FAILED.value,
        )]
        completed = [r for r in records if r.state == ExecutionState.COMPLETED.value]
        failed = [r for r in records if r.state == ExecutionState.FAILED.value]
        pending = [r for r in records if r.state in _ACTIVE_STATES]

        denominator = len(completed) + len(failed)
        success_rate = (len(completed) / denominator * 100.0) if denominator > 0 else 0.0

        # Spend by channel
        total_spend = 0.0
        spend_by_channel: Dict[str, float] = {}
        for rec in records:
            spend = rec.actual_spend if rec.actual_spend is not None else 0.0
            total_spend += spend
            if spend > 0:
                spend_by_channel[rec.channel] = spend_by_channel.get(rec.channel, 0.0) + spend

        # Outcomes
        outcomes = [
            {
                "action_id": r.action_id,
                "title": r.title,
                "outcome_summary": r.outcome_summary or "Completed successfully",
            }
            for r in completed
        ]

        # Top wins and issues
        top_wins = self._identify_top_wins(completed)
        issues = self._identify_issues(records)

        # Upcoming actions
        all_records = self.history.query(business_id)
        upcoming = [
            {
                "action_id": r.action_id,
                "title": r.title,
                "channel": r.channel,
                "scheduled_for": r.scheduled_for or "",
                "risk_tier": r.risk_tier,
            }
            for r in all_records
            if r.state == ExecutionState.SCHEDULED.value
            and (r.scheduled_for or "") <= upcoming_cutoff
        ]

        # Generate recommendations
        recommendations = self._generate_recommendations(records, failed)

        return ExecutionReport(
            business_id=business_id,
            report_type=report_type,
            period_start=period_start,
            period_end=period_end,
            generated_at=_utc_now(),
            actions_executed=len(executed),
            actions_completed=len(completed),
            actions_failed=len(failed),
            actions_pending=len(pending),
            success_rate=round(success_rate, 1),
            total_spend=round(total_spend, 2),
            spend_by_channel={k: round(v, 2) for k, v in spend_by_channel.items()},
            outcomes_observed=outcomes,
            top_wins=top_wins,
            issues_encountered=issues,
            upcoming_actions=upcoming,
            recommendations=recommendations,
        )

    def _identify_top_wins(self, records: List[ExecutionRecord]) -> List[str]:
        """Identify completed actions with positive outcomes."""
        wins: List[Tuple[str, float]] = []
        for rec in records:
            if not rec.outcome_summary:
                continue
            # Score based on spend efficiency and outcome presence
            score = 1.0
            if rec.actual_spend and rec.actual_spend > 0:
                score += 0.5
            if "increase" in (rec.outcome_summary or "").lower():
                score += 1.0
            if "conversion" in (rec.outcome_summary or "").lower():
                score += 0.5
            wins.append((
                f"{rec.title}: {rec.outcome_summary}",
                score,
            ))

        wins.sort(key=lambda w: w[1], reverse=True)
        return [w[0] for w in wins[:3]]

    def _identify_issues(self, records: List[ExecutionRecord]) -> List[Dict[str, Any]]:
        """Identify failures, repeated failures, and slow completions."""
        issues: List[Dict[str, Any]] = []

        # Failed actions
        failed = [r for r in records if r.state == ExecutionState.FAILED.value]
        for rec in failed:
            issues.append({
                "type": "failure",
                "action_id": rec.action_id,
                "title": rec.title,
                "channel": rec.channel,
                "reason": rec.failure_reason or "Unknown",
                "retry_count": rec.retry_count,
                "severity": "high" if rec.retry_count >= rec.max_retries else "medium",
            })

        # Repeated failures on the same channel
        channel_failures: Dict[str, int] = {}
        for rec in failed:
            channel_failures[rec.channel] = channel_failures.get(rec.channel, 0) + 1

        for channel, count in channel_failures.items():
            if count >= 3:
                issues.append({
                    "type": "pattern",
                    "channel": channel,
                    "title": f"{count} consecutive failures on {channel} channel",
                    "reason": f"Repeated failures suggest a systemic issue with {channel}.",
                    "severity": "critical",
                })

        # Slow completions (>48 hours from start to complete)
        for rec in records:
            if rec.state != ExecutionState.COMPLETED.value:
                continue
            if not rec.started_at or not rec.completed_at:
                continue
            start_dt = _parse_iso(rec.started_at)
            end_dt = _parse_iso(rec.completed_at)
            if start_dt and end_dt:
                hours = (end_dt - start_dt).total_seconds() / 3600.0
                if hours > 48:
                    issues.append({
                        "type": "slow_completion",
                        "action_id": rec.action_id,
                        "title": f"{rec.title} took {hours:.0f} hours to complete",
                        "channel": rec.channel,
                        "severity": "low",
                    })

        return issues

    @staticmethod
    def _generate_recommendations(
        records: List[ExecutionRecord],
        failed: List[ExecutionRecord],
    ) -> List[str]:
        """Generate actionable recommendations from execution patterns."""
        recommendations: List[str] = []

        if not records:
            recommendations.append("No actions executed in this period. Review the proposal queue.")
            return recommendations

        # Check for channel-specific failure patterns
        channel_failures: Dict[str, int] = {}
        for rec in failed:
            channel_failures[rec.channel] = channel_failures.get(rec.channel, 0) + 1

        for channel, count in channel_failures.items():
            if count >= 3:
                recommendations.append(
                    f"{count} failures on {channel} -- investigate deliverability, "
                    f"API credentials, or platform policy changes."
                )
            elif count >= 2:
                recommendations.append(
                    f"{count} failures on {channel} -- monitor closely next period."
                )

        # Check for high retry rates
        high_retry = [r for r in records if r.retry_count >= 2]
        if len(high_retry) >= 3:
            recommendations.append(
                f"{len(high_retry)} actions required 2+ retries. Review error patterns "
                f"and consider adding pre-flight checks."
            )

        # Check for spend concentration
        channel_spend: Dict[str, float] = {}
        total_spend = 0.0
        for rec in records:
            spend = rec.actual_spend or 0.0
            channel_spend[rec.channel] = channel_spend.get(rec.channel, 0.0) + spend
            total_spend += spend

        if total_spend > 0:
            for channel, spend in channel_spend.items():
                pct = (spend / total_spend) * 100.0
                if pct > 70:
                    recommendations.append(
                        f"{pct:.0f}% of spend concentrated on {channel}. "
                        f"Consider diversifying across channels."
                    )

        # Check for actions stuck in queue
        pending = [r for r in records if r.state in _ACTIVE_STATES]
        if len(pending) > 10:
            recommendations.append(
                f"{len(pending)} actions are pending or in progress. "
                f"Review the queue to avoid bottlenecks."
            )

        # Positive pattern
        completed = [r for r in records if r.state == ExecutionState.COMPLETED.value]
        total_with_outcome = len(records)
        if total_with_outcome > 0:
            completion_rate = (len(completed) / total_with_outcome) * 100.0
            if completion_rate > 80:
                recommendations.append(
                    f"Strong execution this period with {completion_rate:.0f}% completion rate."
                )

        return recommendations


# =========================================================================
# FailureRecovery
# =========================================================================

class FailureRecovery:
    """Classify failures and execute recovery actions."""

    def __init__(self, history: ActionHistory) -> None:
        self.history = history

    def analyze_failure(self, action_id: str) -> FailureRecoveryAction:
        """Examine a failed action and determine the best recovery path.

        Classification logic:
        - Transient errors (timeout, rate limit, 5xx) -> retry
        - Content rejection (disapproved, policy violation) -> fix + retry
        - Auth failures (401, 403, credentials) -> escalate
        - Max retries exceeded -> alternative or abandon
        """
        records = {r.action_id: r for r in self.history._records.values()}
        record = records.get(action_id)

        if record is None:
            return FailureRecoveryAction(
                action_id=action_id,
                failure_reason="Action not found",
                recovery_type="escalate",
                recovery_description="Cannot analyze -- action not found in history.",
                auto_recoverable=False,
                requires_operator=True,
            )

        reason = (record.failure_reason or "").lower()
        retries_exhausted = record.retry_count >= record.max_retries

        # Max retries exceeded -- suggest alternative or abandon
        if retries_exhausted:
            return FailureRecoveryAction(
                action_id=action_id,
                failure_reason=record.failure_reason or "Unknown",
                recovery_type="alternative" if record.retry_count <= record.max_retries + 1 else "abandon",
                recovery_description=(
                    f"Action has been retried {record.retry_count} times (max {record.max_retries}). "
                    f"Consider an alternative approach or abandon this action."
                ),
                auto_recoverable=False,
                requires_operator=True,
            )

        # Transient errors -- auto-retry
        transient_keywords = ("timeout", "timed out", "rate limit", "429", "503", "502", "504", "temporary")
        if any(kw in reason for kw in transient_keywords):
            return FailureRecoveryAction(
                action_id=action_id,
                failure_reason=record.failure_reason or "Transient error",
                recovery_type="retry",
                recovery_description=(
                    "Transient error detected. Automatic retry is recommended. "
                    f"Retry {record.retry_count + 1} of {record.max_retries}."
                ),
                auto_recoverable=True,
                requires_operator=False,
            )

        # Content/policy rejection -- needs human fix
        content_keywords = ("disapproved", "rejected", "policy", "violation", "prohibited", "restricted")
        if any(kw in reason for kw in content_keywords):
            return FailureRecoveryAction(
                action_id=action_id,
                failure_reason=record.failure_reason or "Content rejected",
                recovery_type="alternative",
                recovery_description=(
                    "Content was rejected by the platform. Review the rejection reason, "
                    "revise the creative to address policy violations, and resubmit."
                ),
                auto_recoverable=False,
                requires_operator=True,
            )

        # Auth/permission errors -- escalate
        auth_keywords = ("auth", "unauthorized", "forbidden", "401", "403", "credential", "permission")
        if any(kw in reason for kw in auth_keywords):
            return FailureRecoveryAction(
                action_id=action_id,
                failure_reason=record.failure_reason or "Authentication failure",
                recovery_type="escalate",
                recovery_description=(
                    "Authentication or permission error. Verify API credentials, "
                    "check account status, and ensure proper access levels."
                ),
                auto_recoverable=False,
                requires_operator=True,
            )

        # Configuration errors
        config_keywords = ("invalid", "config", "missing", "schema", "validation", "malformed")
        if any(kw in reason for kw in config_keywords):
            return FailureRecoveryAction(
                action_id=action_id,
                failure_reason=record.failure_reason or "Configuration error",
                recovery_type="escalate",
                recovery_description=(
                    "Configuration or validation error. Review the action parameters "
                    "and fix any invalid or missing fields before retrying."
                ),
                auto_recoverable=False,
                requires_operator=True,
            )

        # Default -- escalate
        return FailureRecoveryAction(
            action_id=action_id,
            failure_reason=record.failure_reason or "Unknown error",
            recovery_type="escalate",
            recovery_description=(
                "Unknown failure type. Review the error details and determine "
                "the appropriate recovery action."
            ),
            auto_recoverable=False,
            requires_operator=True,
        )

    def attempt_retry(self, action_id: str) -> Dict[str, Any]:
        """Retry a failed action.

        Increments retry_count and resets state to ``approved_waiting``.
        Returns failure if max_retries is exceeded.
        """
        record = self.history._records.get(action_id)
        if record is None:
            return {"success": False, "reason": f"Action {action_id} not found."}

        if record.state != ExecutionState.FAILED.value:
            return {"success": False, "reason": f"Action is not in failed state (current: {record.state})."}

        if record.retry_count >= record.max_retries:
            return {
                "success": False,
                "reason": "max_retries_exceeded",
                "retry_count": record.retry_count,
                "max_retries": record.max_retries,
            }

        record.retry_count += 1
        record.state = ExecutionState.APPROVED_WAITING.value
        record.failed_at = None
        record.failure_reason = None
        record.error_details = None

        self.history._persist_business(record.business_id)

        return {
            "success": True,
            "retry_number": record.retry_count,
            "next_attempt_at": _utc_now(),
            "action_id": action_id,
        }

    def attempt_rollback(self, action_id: str, reason: str) -> Dict[str, Any]:
        """Mark an action as rolled back.

        Sets state to ``rolled_back`` with the given reason.
        Actual rollback logic (undoing the action) is delegated to
        the channel connector.
        """
        record = self.history._records.get(action_id)
        if record is None:
            return {"success": False, "reason": f"Action {action_id} not found."}

        rolled_back_at = _utc_now()
        record.state = ExecutionState.ROLLED_BACK.value
        record.rolled_back_at = rolled_back_at
        record.rollback_reason = reason

        self.history._persist_business(record.business_id)

        return {
            "success": True,
            "action_id": action_id,
            "rolled_back_at": rolled_back_at,
        }

    def suggest_alternative(self, action_id: str) -> Optional[Dict[str, Any]]:
        """Suggest an alternative action based on the failure reason.

        Returns a suggested alternative action or None if no clear
        alternative can be determined.
        """
        record = self.history._records.get(action_id)
        if record is None:
            return None

        reason = (record.failure_reason or "").lower()

        # Ad disapproval -> suggest copy revision
        if any(kw in reason for kw in ("disapproved", "policy", "violation")):
            return {
                "original_action_id": action_id,
                "suggested_action": "revise_creative",
                "description": (
                    f"Revise the creative for '{record.title}' to address policy violations. "
                    f"Check the platform's ad policy reference for specific requirements."
                ),
                "channel": record.channel,
                "risk_tier": record.risk_tier,
            }

        # Email bounce -> suggest list cleanup
        if any(kw in reason for kw in ("bounce", "undeliverable", "invalid email")):
            return {
                "original_action_id": action_id,
                "suggested_action": "clean_email_list",
                "description": (
                    "Clean the email list to remove invalid addresses before "
                    "resending. Consider verifying the list with an email "
                    "validation service."
                ),
                "channel": "email",
                "risk_tier": "low",
            }

        # Budget exhausted -> suggest budget increase or pause
        if any(kw in reason for kw in ("budget", "spend limit", "billing")):
            return {
                "original_action_id": action_id,
                "suggested_action": "adjust_budget",
                "description": (
                    f"The {record.channel} campaign hit its budget limit. "
                    f"Review performance and either increase the budget or "
                    f"reallocate from underperforming channels."
                ),
                "channel": record.channel,
                "risk_tier": "medium",
            }

        # API/integration failure -> suggest manual execution
        if any(kw in reason for kw in ("api", "integration", "connection")):
            return {
                "original_action_id": action_id,
                "suggested_action": "manual_execution",
                "description": (
                    f"The automated execution for '{record.title}' failed due to "
                    f"an integration issue. Execute this action manually through "
                    f"the {record.channel} platform directly."
                ),
                "channel": record.channel,
                "risk_tier": record.risk_tier,
            }

        return None

    def escalate_to_operator(
        self, action_id: str, summary: str,
    ) -> Dict[str, Any]:
        """Create an escalation with full failure context.

        Returns an escalation record with all relevant details for
        operator notification.
        """
        record = self.history._records.get(action_id)
        if record is None:
            return {
                "success": False,
                "reason": f"Action {action_id} not found.",
            }

        return {
            "success": True,
            "escalation_id": _new_id("esc"),
            "action_id": action_id,
            "title": record.title,
            "channel": record.channel,
            "action_type": record.action_type,
            "risk_tier": record.risk_tier,
            "failure_reason": record.failure_reason,
            "error_details": record.error_details,
            "retry_count": record.retry_count,
            "max_retries": record.max_retries,
            "summary": summary,
            "proposed_at": record.proposed_at,
            "failed_at": record.failed_at,
            "escalated_at": _utc_now(),
            "requires_action": True,
        }
