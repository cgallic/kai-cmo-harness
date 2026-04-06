"""Attribution snapshots and action-to-outcome linkage for the Kai Marketing OS.

This module closes the marketing feedback loop by capturing metric snapshots
before and after actions are executed, linking those snapshots to specific
actions, and calculating the observed impact with a confidence score.

The flow this enables:

    finding -> proposal -> execution -> measurement -> learning

Without this module the system cannot learn from its own work and the
operator has no evidence that actions are working.

Downstream consumers:

- ``kai.analytics.scorecards`` -- renders outcome data on dashboards
- ``kai.runtime.memory`` -- feeds learnings into persistent memory
- ``kai.proposals`` -- uses outcome data to refine future proposals

Usage::

    from kai.analytics.attribution import (
        AttributionModel,
        ConfidenceLevel,
        MetricSnapshot,
        AttributionSnapshot,
        ObservedChange,
        ActionOutcomeLinkage,
        ActionLineage,
        calculate_confidence,
        apply_attribution_model,
        build_action_lineage,
    )

    conf_level, conf_score, conf_factors = calculate_confidence(
        before_snap, after_snap,
        concurrent_actions=["act_abc123"],
        external_events=["holiday_memorial_day"],
        measurement_days=21,
    )
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from kai.runtime.models import SerializableModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AttributionModel(str, Enum):
    """Which attribution model to use when distributing credit."""

    LAST_TOUCH = "last_touch"
    FIRST_TOUCH = "first_touch"
    LINEAR = "linear"
    TIME_DECAY = "time_decay"


class ConfidenceLevel(str, Enum):
    """How confident we are in the attribution of an observed change."""

    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INSUFFICIENT = "insufficient"


# ---------------------------------------------------------------------------
# ID generators
# ---------------------------------------------------------------------------


def _generate_snapshot_id() -> str:
    """Generate a unique snapshot ID.  Format: ``snap_{12-hex-chars}``."""
    return f"snap_{uuid.uuid4().hex[:12]}"


def _generate_linkage_id() -> str:
    """Generate a unique linkage ID.  Format: ``aol_{12-hex-chars}``."""
    return f"aol_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


@dataclass
class MetricSnapshot(SerializableModel):
    """A point-in-time capture of all marketing metrics for a business.

    Stores the raw KPI values, channel-level breakdowns, and top
    performers at the moment the snapshot was taken.

    Attributes:
        timestamp: ISO timestamp when the snapshot was captured.
        business_id: Unique identifier for the business.
        kpi_values: Mapping of ``kpi_name`` to numeric value at the time
            of the snapshot.
        channel_breakdowns: Mapping of ``channel_name`` to a dict of
            ``{metric_name: value}`` pairs for that channel.
        top_pages: Top 10 pages by traffic.  Each entry contains ``url``,
            ``sessions``, and ``conversions``.
        top_sources: Top 10 traffic sources.  Each entry contains
            ``source``, ``medium``, and ``sessions``.
        top_keywords: Top 20 keywords from Google Search Console.  Each
            entry contains ``query``, ``clicks``, ``impressions``, and
            ``position``.
        metadata: Additional context captured at snapshot time.
    """

    timestamp: str = ""
    business_id: str = ""
    kpi_values: Dict[str, float] = field(default_factory=dict)
    channel_breakdowns: Dict[str, Dict[str, float]] = field(default_factory=dict)
    top_pages: List[Dict[str, Any]] = field(default_factory=list)
    top_sources: List[Dict[str, Any]] = field(default_factory=list)
    top_keywords: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AttributionSnapshot(SerializableModel):
    """A labelled metric snapshot tied to a specific trigger or schedule.

    Wraps a ``MetricSnapshot`` with context about *why* it was captured
    (baseline, pre-action, post-action, or periodic) and which action
    triggered it.

    Attributes:
        id: Unique identifier (``snap_{12-hex-chars}``).
        business_id: Unique identifier for the business.
        snapshot_type: One of ``"baseline"``, ``"pre_action"``,
            ``"post_action"``, or ``"periodic"``.
        captured_at: ISO timestamp when the snapshot was taken.
        metric_snapshot: The underlying ``MetricSnapshot``.
        trigger_action_id: The action that triggered this snapshot, or
            ``None`` for baseline and periodic snapshots.
        notes: Optional human-readable note about context.
    """

    id: str = field(default_factory=_generate_snapshot_id)
    business_id: str = ""
    snapshot_type: str = "baseline"
    captured_at: str = ""
    metric_snapshot: MetricSnapshot = field(default_factory=MetricSnapshot)
    trigger_action_id: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class ObservedChange(SerializableModel):
    """The measured difference in a single KPI between two snapshots.

    Captures both the absolute and percentage change, the direction
    relative to the KPI's target direction, and whether the change
    exceeds the noise threshold.

    Attributes:
        metric_name: Which KPI changed.
        before_value: Value in the pre-action snapshot.
        after_value: Value in the post-action snapshot.
        absolute_change: ``after_value - before_value``.
        percent_change: Percentage change, handling zero-division safely.
        direction: ``"improved"``, ``"declined"``, or ``"unchanged"``
            based on KPI target direction.
        is_significant: ``True`` if the change exceeds a noise threshold.
    """

    metric_name: str = ""
    before_value: float = 0.0
    after_value: float = 0.0
    absolute_change: float = 0.0
    percent_change: float = 0.0
    direction: str = "unchanged"
    is_significant: bool = False


@dataclass
class ActionOutcomeLinkage(SerializableModel):
    """Links a marketing action to its measured outcome.

    Connects a ``ProposedAction`` to before/after ``AttributionSnapshot``
    pairs and records the observed changes, confidence assessment, and
    attributed impact under the chosen attribution model.

    Attributes:
        id: Unique identifier (``aol_{12-hex-chars}``).
        action_id: References ``ProposedAction.id``.
        action_type: Copied from ``ProposedAction.action_type`` for quick
            reference.
        execution_date: ISO date when the action was executed.
        measurement_window_days: Number of days between the before and
            after snapshots.
        before_snapshot_id: References the pre-action
            ``AttributionSnapshot.id``.
        after_snapshot_id: References the post-action
            ``AttributionSnapshot.id``.
        observed_changes: All metric changes observed in the window.
        confidence_level: ``ConfidenceLevel`` enum value.
        confidence_score: Numeric confidence between 0.0 and 1.0.
        confidence_factors: Breakdown of how the confidence score was
            computed.
        contributing_factors: Other things that may have influenced the
            metric (e.g., other concurrent actions, seasonality).
        attribution_model: Which ``AttributionModel`` was used.
        attributed_impact: Per-metric attributed impact after the model
            has been applied.
        created_at: ISO timestamp.
    """

    id: str = field(default_factory=_generate_linkage_id)
    action_id: str = ""
    action_type: str = ""
    execution_date: str = ""
    measurement_window_days: int = 0
    before_snapshot_id: str = ""
    after_snapshot_id: str = ""
    observed_changes: List[ObservedChange] = field(default_factory=list)
    confidence_level: str = ConfidenceLevel.INSUFFICIENT.value
    confidence_score: float = 0.0
    confidence_factors: Dict[str, Any] = field(default_factory=dict)
    contributing_factors: List[str] = field(default_factory=list)
    attribution_model: str = AttributionModel.LAST_TOUCH.value
    attributed_impact: Dict[str, float] = field(default_factory=dict)
    created_at: str = ""


@dataclass
class ActionLineage(SerializableModel):
    """Complete trace of an action from discovery through measured result.

    Assembles every stage of the action lifecycle into a single record
    that can be displayed in dashboards, fed into the learning system,
    or used for retrospective analysis.

    Attributes:
        action_id: The action being traced.
        business_id: Which business this action belongs to.
        finding_id: The original ``AuditFinding`` that triggered the
            chain.
        finding_summary: Short description of the finding.
        proposal_date: ISO date when the action was proposed.
        approval_date: When approved, or ``None`` if pending.
        approval_decision: ``"approved"``, ``"rejected"``, or
            ``"revised"``, or ``None`` if pending.
        execution_date: When executed, or ``None`` if not yet.
        execution_status: Current status of the action.
        measurement_date: When post-action metrics were captured, or
            ``None``.
        outcome_linkage_id: References ``ActionOutcomeLinkage.id``, or
            ``None``.
        outcome_summary: Human-readable outcome string.
        learnings: Extracted learnings from this action's lifecycle.
        full_timeline: Ordered list of events, each with ``event_type``,
            ``timestamp``, ``description``, and ``actor``.
    """

    action_id: str = ""
    business_id: str = ""
    finding_id: str = ""
    finding_summary: str = ""
    proposal_date: str = ""
    approval_date: Optional[str] = None
    approval_decision: Optional[str] = None
    execution_date: Optional[str] = None
    execution_status: str = "pending"
    measurement_date: Optional[str] = None
    outcome_linkage_id: Optional[str] = None
    outcome_summary: Optional[str] = None
    learnings: List[str] = field(default_factory=list)
    full_timeline: List[Dict[str, Any]] = field(default_factory=list)


# ============================================================================
# Confidence scoring
# ============================================================================


def calculate_confidence(
    before_snapshot: AttributionSnapshot,
    after_snapshot: AttributionSnapshot,
    concurrent_actions: List[str],
    external_events: List[str],
    measurement_days: int,
) -> Tuple[str, float, Dict[str, Any]]:
    """Score how confident we can be in the attribution of observed changes.

    Starts at a score of 1.0 and applies penalties for concurrent actions,
    external events, and insufficient measurement time.  A bonus is added
    for longer measurement windows that produce more data.

    Scoring rules:
        - Start at 1.0
        - Subtract 0.1 per concurrent action executed in the same window
        - Subtract 0.15 per known external event (holiday, algorithm
          update, seasonality)
        - Subtract 0.2 if ``measurement_days`` < 7
        - Subtract 0.1 if ``measurement_days`` < 14 (but >= 7)
        - Add 0.1 if ``measurement_days`` >= 30 (more data)
        - Floor at 0.0, cap at 1.0

    Confidence level mapping:
        - >= 0.75 -> high
        - >= 0.50 -> medium
        - >= 0.25 -> low
        - < 0.25  -> insufficient

    Args:
        before_snapshot: The pre-action ``AttributionSnapshot``.
        after_snapshot: The post-action ``AttributionSnapshot``.
        concurrent_actions: IDs of other actions executed in the same
            measurement window.
        external_events: Known external events that may have influenced
            metrics (e.g., ``"holiday_memorial_day"``,
            ``"google_core_update"``).
        measurement_days: Number of days between the before and after
            snapshots.

    Returns:
        A 3-tuple of ``(confidence_level, confidence_score,
        confidence_factors)`` where ``confidence_factors`` is a dict
        explaining the scoring breakdown.
    """
    score = 1.0

    # Penalty: concurrent actions reduce confidence because the observed
    # change may be partly caused by those other actions.
    concurrent_penalty = len(concurrent_actions) * 0.1
    score -= concurrent_penalty

    # Penalty: external events (holidays, algorithm updates, seasonality
    # shifts) inject noise that makes attribution unreliable.
    external_penalty = len(external_events) * 0.15
    score -= external_penalty

    # Penalty: very short measurement windows produce noisy data.
    time_penalty = 0.0
    time_bonus = 0.0
    if measurement_days < 7:
        time_penalty = 0.2
        score -= time_penalty
    elif measurement_days < 14:
        time_penalty = 0.1
        score -= time_penalty

    # Bonus: longer windows give us more data points and reduce noise.
    if measurement_days >= 30:
        time_bonus = 0.1
        score += time_bonus

    # Clamp to [0.0, 1.0]
    score = max(0.0, min(1.0, score))

    # Map numeric score to confidence level
    if score >= 0.75:
        level = ConfidenceLevel.HIGH.value
    elif score >= 0.5:
        level = ConfidenceLevel.MEDIUM.value
    elif score >= 0.25:
        level = ConfidenceLevel.LOW.value
    else:
        level = ConfidenceLevel.INSUFFICIENT.value

    # Build explanation factors
    time_elapsed_adequate = measurement_days >= 14
    sample_size_adequate = measurement_days >= 7

    factors: Dict[str, Any] = {
        "concurrent_changes_count": len(concurrent_actions),
        "concurrent_penalty": round(concurrent_penalty, 2),
        "time_elapsed_adequate": time_elapsed_adequate,
        "time_penalty": round(time_penalty, 2),
        "time_bonus": round(time_bonus, 2),
        "external_factors": list(external_events),
        "external_penalty": round(external_penalty, 2),
        "sample_size_adequate": sample_size_adequate,
        "measurement_days": measurement_days,
        "raw_score": round(score, 4),
    }

    return level, round(score, 4), factors


# ============================================================================
# Attribution models
# ============================================================================


def apply_attribution_model(
    model: str,
    touchpoints: List[Dict[str, Any]],
    total_value: float,
) -> Dict[str, float]:
    """Distribute a total conversion value across touchpoints.

    Each touchpoint is a dict with at least ``action_id`` and
    ``timestamp`` (ISO string).  The ``channel`` key is optional and
    used for reporting.

    Implementations:
        - ``last_touch``: 100 % credit to the last touchpoint before
          conversion.
        - ``first_touch``: 100 % credit to the first touchpoint.
        - ``linear``: Equal credit across all touchpoints.
        - ``time_decay``: Half-life of 7 days.  More recent touchpoints
          receive more credit.  Weight formula:
          ``2 ** (-days_before_conversion / 7)``.

    Args:
        model: ``AttributionModel`` enum value string.
        touchpoints: List of dicts, each with ``action_id``,
            ``timestamp``, and optionally ``channel``.
        total_value: The total conversion value to distribute.

    Returns:
        A dict mapping ``action_id`` to its attributed value.  If no
        touchpoints are provided, returns an empty dict.  If an unknown
        model is given, falls back to ``last_touch``.
    """
    if not touchpoints:
        return {}

    # Sort touchpoints by timestamp (chronological order)
    sorted_touchpoints = sorted(touchpoints, key=lambda tp: tp.get("timestamp", ""))

    if model == AttributionModel.FIRST_TOUCH.value:
        return _first_touch(sorted_touchpoints, total_value)
    elif model == AttributionModel.LINEAR.value:
        return _linear(sorted_touchpoints, total_value)
    elif model == AttributionModel.TIME_DECAY.value:
        return _time_decay(sorted_touchpoints, total_value)
    else:
        # Default and explicit last_touch
        return _last_touch(sorted_touchpoints, total_value)


def _last_touch(
    sorted_touchpoints: List[Dict[str, Any]],
    total_value: float,
) -> Dict[str, float]:
    """Assign 100 % credit to the last touchpoint."""
    result: Dict[str, float] = {}
    for tp in sorted_touchpoints:
        result[tp["action_id"]] = 0.0
    last = sorted_touchpoints[-1]
    result[last["action_id"]] = total_value
    return result


def _first_touch(
    sorted_touchpoints: List[Dict[str, Any]],
    total_value: float,
) -> Dict[str, float]:
    """Assign 100 % credit to the first touchpoint."""
    result: Dict[str, float] = {}
    for tp in sorted_touchpoints:
        result[tp["action_id"]] = 0.0
    first = sorted_touchpoints[0]
    result[first["action_id"]] = total_value
    return result


def _linear(
    sorted_touchpoints: List[Dict[str, Any]],
    total_value: float,
) -> Dict[str, float]:
    """Split credit equally across all touchpoints.

    If an ``action_id`` appears in multiple touchpoints, its shares are
    summed so the total still equals ``total_value``.
    """
    n = len(sorted_touchpoints)
    share = total_value / n if n > 0 else 0.0

    result: Dict[str, float] = {}
    for tp in sorted_touchpoints:
        aid = tp["action_id"]
        result[aid] = result.get(aid, 0.0) + share

    # Round to avoid floating-point drift
    return {aid: round(val, 4) for aid, val in result.items()}


def _time_decay(
    sorted_touchpoints: List[Dict[str, Any]],
    total_value: float,
) -> Dict[str, float]:
    """Distribute credit using exponential time decay.

    The most recent touchpoint gets the most credit.  The weight for
    each touchpoint is ``2 ** (-days_before_conversion / 7)`` where
    ``days_before_conversion`` is the number of days between the
    touchpoint and the last (most recent) touchpoint.

    The weights are normalised so they sum to 1.0 before being
    multiplied by ``total_value``.
    """
    if not sorted_touchpoints:
        return {}

    # Parse the conversion timestamp (the last touchpoint)
    last_ts = sorted_touchpoints[-1].get("timestamp", "")
    conversion_dt = _parse_iso_timestamp(last_ts)

    # Calculate raw weights
    raw_weights: List[Tuple[str, float]] = []
    for tp in sorted_touchpoints:
        tp_dt = _parse_iso_timestamp(tp.get("timestamp", ""))
        days_before = (conversion_dt - tp_dt).total_seconds() / 86400.0
        # Clamp negative days (can happen if timestamps are equal)
        days_before = max(0.0, days_before)
        weight = 2.0 ** (-days_before / 7.0)
        raw_weights.append((tp["action_id"], weight))

    # Normalise weights
    total_weight = sum(w for _, w in raw_weights)
    if total_weight == 0.0:
        # All weights are zero -- fall back to equal split
        share = total_value / len(raw_weights) if raw_weights else 0.0
        return {aid: round(share, 4) for aid, _ in raw_weights}

    result: Dict[str, float] = {}
    for aid, w in raw_weights:
        attributed = (w / total_weight) * total_value
        result[aid] = result.get(aid, 0.0) + attributed

    return {aid: round(val, 4) for aid, val in result.items()}


def _parse_iso_timestamp(ts: str) -> datetime:
    """Best-effort parse of an ISO-format timestamp string.

    Handles both ``YYYY-MM-DDTHH:MM:SSZ`` and ``YYYY-MM-DD`` formats.
    Falls back to the Unix epoch if the string cannot be parsed.
    """
    if not ts:
        return datetime(2000, 1, 1, tzinfo=timezone.utc)

    # Try full ISO format first
    for fmt in (
        "%Y-%m-%dT%H:%M:%S%z",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d",
    ):
        try:
            dt = datetime.strptime(ts, fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue

    return datetime(2000, 1, 1, tzinfo=timezone.utc)


# ============================================================================
# Observed change computation
# ============================================================================


def compute_observed_changes(
    before_snapshot: AttributionSnapshot,
    after_snapshot: AttributionSnapshot,
    kpi_directions: Optional[Dict[str, str]] = None,
    noise_threshold_pct: float = 5.0,
) -> List[ObservedChange]:
    """Compare two snapshots and compute per-metric changes.

    Iterates over all KPIs present in both the before and after
    snapshots and calculates the absolute and percentage change.

    Args:
        before_snapshot: The pre-action ``AttributionSnapshot``.
        after_snapshot: The post-action ``AttributionSnapshot``.
        kpi_directions: Optional mapping of ``kpi_name`` to
            ``TargetDirection`` value (``"higher_is_better"`` or
            ``"lower_is_better"``).  Used to determine whether a change
            is an improvement or decline.  Defaults to
            ``"higher_is_better"`` for all metrics if not provided.
        noise_threshold_pct: Minimum absolute percent change to be
            considered significant.  Defaults to 5.0 %.

    Returns:
        A list of ``ObservedChange`` objects, one per metric that
        appears in both snapshots.
    """
    if kpi_directions is None:
        kpi_directions = {}

    before_vals = before_snapshot.metric_snapshot.kpi_values
    after_vals = after_snapshot.metric_snapshot.kpi_values

    # Only process metrics present in both snapshots
    common_metrics = set(before_vals.keys()) & set(after_vals.keys())

    changes: List[ObservedChange] = []
    for metric_name in sorted(common_metrics):
        before_value = before_vals[metric_name]
        after_value = after_vals[metric_name]

        absolute_change = after_value - before_value

        # Handle zero-division for percent change
        if before_value != 0.0:
            percent_change = (absolute_change / before_value) * 100.0
        elif after_value != 0.0:
            # Before was zero, after is non-zero -- infinite growth,
            # represent as 100 % gain for practical purposes.
            percent_change = 100.0
        else:
            percent_change = 0.0

        # Determine direction based on KPI's target direction
        direction_pref = kpi_directions.get(metric_name, "higher_is_better")

        if abs(percent_change) < noise_threshold_pct:
            direction = "unchanged"
        elif direction_pref == "lower_is_better":
            direction = "improved" if absolute_change < 0 else "declined"
        else:
            # higher_is_better (default)
            direction = "improved" if absolute_change > 0 else "declined"

        is_significant = abs(percent_change) >= noise_threshold_pct

        changes.append(
            ObservedChange(
                metric_name=metric_name,
                before_value=round(before_value, 4),
                after_value=round(after_value, 4),
                absolute_change=round(absolute_change, 4),
                percent_change=round(percent_change, 2),
                direction=direction,
                is_significant=is_significant,
            )
        )

    return changes


# ============================================================================
# Action lineage builder
# ============================================================================


def build_action_lineage(
    action_id: str,
    business_id: str,
    finding: Any,
    proposal: Any,
    approval: Optional[Any] = None,
    execution: Optional[Any] = None,
    outcome: Optional[ActionOutcomeLinkage] = None,
) -> ActionLineage:
    """Assemble a complete lineage record from component objects.

    Takes the various objects that represent stages of the action
    lifecycle and composes them into a single ``ActionLineage`` with a
    full timeline and extracted learnings.

    The ``finding``, ``proposal``, ``approval``, and ``execution``
    parameters are duck-typed -- they only need the attributes that the
    function reads.  This avoids hard-coupling to specific model classes.

    Expected attributes on each parameter:

    - ``finding``: ``id``, ``summary`` (or ``title`` or ``description``)
    - ``proposal``: ``created_at`` (or ``proposal_date``)
    - ``approval``: ``decision`` (or ``status``), ``created_at``
      (or ``approval_date``)
    - ``execution``: ``status``, ``executed_at`` (or ``created_at``,
      ``execution_date``), ``error`` (optional)

    Args:
        action_id: The action being traced.
        business_id: Which business this action belongs to.
        finding: The audit finding that started the chain.
        proposal: The proposal / proposed action.
        approval: The approval record, or ``None`` if not yet approved.
        execution: The execution record, or ``None`` if not yet executed.
        outcome: The ``ActionOutcomeLinkage``, or ``None`` if not yet
            measured.

    Returns:
        A fully populated ``ActionLineage`` instance.
    """
    timeline: List[Dict[str, Any]] = []

    # -- Finding --
    finding_id = _safe_attr(finding, "id", "")
    finding_summary = (
        _safe_attr(finding, "summary", "")
        or _safe_attr(finding, "title", "")
        or _safe_attr(finding, "description", "")
    )

    timeline.append({
        "event_type": "finding_created",
        "timestamp": _safe_attr(finding, "created_at", ""),
        "description": f"Finding identified: {finding_summary}",
        "actor": "system",
    })

    # -- Proposal --
    proposal_date = (
        _safe_attr(proposal, "created_at", "")
        or _safe_attr(proposal, "proposal_date", "")
    )

    timeline.append({
        "event_type": "action_proposed",
        "timestamp": proposal_date,
        "description": f"Action proposed: {_safe_attr(proposal, 'title', action_id)}",
        "actor": "system",
    })

    # -- Approval --
    approval_date: Optional[str] = None
    approval_decision: Optional[str] = None

    if approval is not None:
        approval_decision = (
            _safe_attr(approval, "decision", None)
            or _safe_attr(approval, "status", None)
        )
        approval_date = (
            _safe_attr(approval, "created_at", None)
            or _safe_attr(approval, "approval_date", None)
        )
        timeline.append({
            "event_type": "action_reviewed",
            "timestamp": approval_date or "",
            "description": f"Action {approval_decision or 'reviewed'}",
            "actor": _safe_attr(approval, "reviewer", "operator"),
        })

    # -- Execution --
    execution_date: Optional[str] = None
    execution_status = "pending"

    if approval is not None and approval_decision in ("approved", "revised"):
        execution_status = "approved"

    if execution is not None:
        execution_status = _safe_attr(execution, "status", "completed")
        execution_date = (
            _safe_attr(execution, "executed_at", None)
            or _safe_attr(execution, "created_at", None)
            or _safe_attr(execution, "execution_date", None)
        )
        timeline.append({
            "event_type": "action_executed",
            "timestamp": execution_date or "",
            "description": f"Action executed (status: {execution_status})",
            "actor": "system",
        })

        exec_error = _safe_attr(execution, "error", None)
        if exec_error:
            execution_status = "failed"
            timeline.append({
                "event_type": "execution_failed",
                "timestamp": execution_date or "",
                "description": f"Execution failed: {exec_error}",
                "actor": "system",
            })

    # -- Measurement / Outcome --
    measurement_date: Optional[str] = None
    outcome_linkage_id: Optional[str] = None
    outcome_summary: Optional[str] = None
    learnings: List[str] = []

    if outcome is not None:
        outcome_linkage_id = outcome.id
        measurement_date = outcome.created_at or ""

        timeline.append({
            "event_type": "outcome_measured",
            "timestamp": measurement_date,
            "description": (
                f"Outcome measured: {outcome.confidence_level} confidence, "
                f"{len(outcome.observed_changes)} metrics tracked"
            ),
            "actor": "system",
        })

        # Extract learnings from observed changes
        learnings = _extract_learnings(outcome)

        # Build human-readable outcome summary
        outcome_summary = _build_outcome_summary(outcome)

    # Sort timeline by timestamp
    timeline.sort(key=lambda e: e.get("timestamp", ""))

    return ActionLineage(
        action_id=action_id,
        business_id=business_id,
        finding_id=finding_id,
        finding_summary=finding_summary,
        proposal_date=proposal_date,
        approval_date=approval_date,
        approval_decision=approval_decision,
        execution_date=execution_date,
        execution_status=execution_status,
        measurement_date=measurement_date,
        outcome_linkage_id=outcome_linkage_id,
        outcome_summary=outcome_summary,
        learnings=learnings,
        full_timeline=timeline,
    )


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _safe_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Read an attribute from an object, returning *default* on failure.

    Supports both regular objects (``getattr``) and dicts (``get``).
    """
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return getattr(obj, attr, default)


def _extract_learnings(outcome: ActionOutcomeLinkage) -> List[str]:
    """Derive human-readable learnings from an outcome linkage.

    Examines each observed change and the confidence score to produce
    actionable insight strings.
    """
    learnings: List[str] = []

    improved = [c for c in outcome.observed_changes if c.direction == "improved" and c.is_significant]
    declined = [c for c in outcome.observed_changes if c.direction == "declined" and c.is_significant]

    if improved:
        names = ", ".join(c.metric_name for c in improved[:3])
        best = max(improved, key=lambda c: abs(c.percent_change))
        learnings.append(
            f"Action improved {len(improved)} metric(s): {names}. "
            f"Largest gain: {best.metric_name} ({best.percent_change:+.1f}%)."
        )

    if declined:
        names = ", ".join(c.metric_name for c in declined[:3])
        worst = max(declined, key=lambda c: abs(c.percent_change))
        learnings.append(
            f"Action may have negatively impacted {len(declined)} metric(s): {names}. "
            f"Largest decline: {worst.metric_name} ({worst.percent_change:+.1f}%)."
        )

    if outcome.confidence_level == ConfidenceLevel.INSUFFICIENT.value:
        learnings.append(
            "Confidence is insufficient -- consider extending the measurement "
            "window or reducing concurrent actions."
        )
    elif outcome.confidence_level == ConfidenceLevel.LOW.value:
        learnings.append(
            "Confidence is low due to concurrent actions or external events. "
            "Results are directional, not definitive."
        )

    if outcome.contributing_factors:
        learnings.append(
            f"Contributing factors to consider: "
            f"{', '.join(outcome.contributing_factors[:3])}."
        )

    if not improved and not declined:
        learnings.append(
            "No significant metric changes were observed in the measurement window."
        )

    return learnings


def _build_outcome_summary(outcome: ActionOutcomeLinkage) -> str:
    """Build a single-sentence human-readable outcome summary.

    Example output: ``"+15% conversion rate, -3% bounce rate, high confidence"``
    """
    parts: List[str] = []

    significant = [
        c for c in outcome.observed_changes
        if c.is_significant
    ]

    # Show up to 3 most significant changes
    significant.sort(key=lambda c: abs(c.percent_change), reverse=True)
    for change in significant[:3]:
        parts.append(f"{change.percent_change:+.1f}% {change.metric_name}")

    if not parts:
        parts.append("no significant changes")

    parts.append(f"{outcome.confidence_level} confidence")

    return ", ".join(parts)
