# Task 058: Build attribution snapshots and action-to-outcome linkage

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 10. Analytics, Attribution, and Monitoring
**Priority:** P1
**Depends on:** 056, 022
**Estimated complexity:** Large

## Context

The Kai marketing OS proposes and executes marketing actions, but without attribution the system cannot learn from its own work. This module creates the machinery to capture "before" snapshots of all metrics, link them to specific actions, capture "after" snapshots once enough time has passed, and calculate the observed impact with a confidence score. This closes the loop: finding → proposal → execution → measurement → learning. Without this, the entire memory and learning subsystem (workstream 13) has no data to learn from, and the operator has no evidence that actions are working.

## Scope

Create `kai/analytics/attribution.py` containing attribution snapshot models, action-outcome linkage, multiple attribution model implementations, confidence scoring, and a complete ActionLineage model that traces an action from discovery through measured result.

## Detailed Requirements

### File: `kai/analytics/attribution.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: AttributionModel**
- `last_touch` — 100% credit to the last touchpoint before conversion
- `first_touch` — 100% credit to the first touchpoint
- `linear` — equal credit across all touchpoints
- `time_decay` — more credit to recent touchpoints (configurable half-life)

**Enum: ConfidenceLevel**
- `high` — clear before/after, no concurrent changes, adequate time elapsed
- `medium` — some concurrent changes but metric direction matches prediction
- `low` — many concurrent changes, insufficient time, external factors present
- `insufficient` — not enough data to assess

**Model: MetricSnapshot**
- `timestamp: str` — ISO timestamp when snapshot was captured
- `business_id: str`
- `kpi_values: Dict[str, float]` — kpi_name -> value at time of snapshot
- `channel_breakdowns: Dict[str, Dict[str, float]]` — channel_name -> {metric_name: value}
- `top_pages: List[Dict[str, Any]]` — top 10 pages by traffic, each with url, sessions, conversions
- `top_sources: List[Dict[str, Any]]` — top 10 traffic sources, each with source, medium, sessions
- `top_keywords: List[Dict[str, Any]]` — top 20 keywords from GSC, each with query, clicks, impressions, position
- `metadata: Dict[str, Any]` — additional context

**Model: AttributionSnapshot**
- `id: str` — unique identifier, format `snap_{uuid_hex[:12]}`
- `business_id: str`
- `snapshot_type: str` — "baseline", "pre_action", "post_action", "periodic"
- `captured_at: str` — ISO timestamp
- `metric_snapshot: MetricSnapshot`
- `trigger_action_id: Optional[str]` — action that triggered this snapshot (None for baseline/periodic)
- `notes: Optional[str]` — human-readable note about context

**Model: ObservedChange**
- `metric_name: str` — which KPI changed
- `before_value: float` — value in pre-action snapshot
- `after_value: float` — value in post-action snapshot
- `absolute_change: float` — after_value - before_value
- `percent_change: float` — (after - before) / before * 100 (handle zero division)
- `direction: str` — "improved", "declined", "unchanged" (based on KPI target_direction)
- `is_significant: bool` — True if change exceeds noise threshold

**Model: ActionOutcomeLinkage**
- `id: str` — unique identifier, format `aol_{uuid_hex[:12]}`
- `action_id: str` — links to ProposedAction.id
- `action_type: str` — copied from ProposedAction for quick reference
- `execution_date: str` — when the action was executed
- `measurement_window_days: int` — how many days between before and after snapshots
- `before_snapshot_id: str` — references AttributionSnapshot.id
- `after_snapshot_id: str` — references AttributionSnapshot.id
- `observed_changes: List[ObservedChange]` — all metric changes observed
- `confidence_level: str` — ConfidenceLevel enum value
- `confidence_score: float` — 0.0-1.0 numeric confidence
- `confidence_factors: Dict[str, Any]` — explanation of confidence scoring: concurrent_changes_count, time_elapsed_adequate (bool), external_factors (list), sample_size_adequate (bool)
- `contributing_factors: List[str]` — other things that may have influenced the metric
- `attribution_model: str` — which AttributionModel was used
- `attributed_impact: Dict[str, float]` — per-metric attributed impact after model applied
- `created_at: str`

**Model: ActionLineage**
- `action_id: str`
- `business_id: str`
- `finding_id: str` — the original AuditFinding that triggered this chain
- `finding_summary: str` — short description of the finding
- `proposal_date: str` — when the action was proposed
- `approval_date: Optional[str]` — when approved (None if pending)
- `approval_decision: Optional[str]` — "approved", "rejected", "revised"
- `execution_date: Optional[str]` — when executed (None if not yet)
- `execution_status: str` — "pending", "approved", "executing", "completed", "failed"
- `measurement_date: Optional[str]` — when post-action metrics were captured
- `outcome_linkage_id: Optional[str]` — references ActionOutcomeLinkage.id
- `outcome_summary: Optional[str]` — human-readable outcome (e.g., "+15% conversion rate, high confidence")
- `learnings: List[str]` — extracted learnings from this action's lifecycle
- `full_timeline: List[Dict[str, Any]]` — ordered list of events: [{event_type, timestamp, description, actor}]

**Function: calculate_confidence(before_snapshot: AttributionSnapshot, after_snapshot: AttributionSnapshot, concurrent_actions: List[str], external_events: List[str], measurement_days: int) -> Tuple[str, float, Dict]**
- Returns (confidence_level, confidence_score, confidence_factors)
- Scoring rules:
  - Start at 1.0
  - Subtract 0.1 per concurrent action executed in the same window
  - Subtract 0.15 per known external event (holiday, algorithm update, seasonality)
  - Subtract 0.2 if measurement_days < 7
  - Subtract 0.1 if measurement_days < 14
  - Add 0.1 if measurement_days >= 30 (more data)
  - Floor at 0.0, cap at 1.0
  - Map to ConfidenceLevel: >= 0.75 → high, >= 0.5 → medium, >= 0.25 → low, < 0.25 → insufficient

**Function: apply_attribution_model(model: str, touchpoints: List[Dict], total_value: float) -> Dict[str, float]**
- `touchpoints` is a list of dicts with: action_id, timestamp, channel
- Returns dict of action_id -> attributed value
- Implementations:
  - `last_touch`: 100% to last touchpoint
  - `first_touch`: 100% to first touchpoint
  - `linear`: equal split across all touchpoints
  - `time_decay`: half-life of 7 days, more weight to recent. Weight = 2^(-days_before_conversion / 7)

**Function: build_action_lineage(action_id: str, business_id: str, finding: Any, proposal: Any, approval: Optional[Any], execution: Optional[Any], outcome: Optional[ActionOutcomeLinkage]) -> ActionLineage**
- Assembles a complete lineage record from the component objects
- Generates timeline from available data
- Extracts learnings from outcome (if available)

## Output Files

- `kai/analytics/attribution.py`

## Acceptance Criteria

- File parses as valid Python
- All models are complete dataclasses with SerializableModel mixin
- `calculate_confidence` implements the exact scoring rules described above
- `apply_attribution_model` correctly implements all four attribution models
- Time-decay model uses the 2^(-days/7) formula correctly
- `build_action_lineage` handles optional None values for approval, execution, outcome
- ObservedChange correctly handles zero-division in percent_change calculation
- All id fields use the established `prefix_{uuid_hex[:12]}` pattern
- No external dependencies beyond stdlib + project modules

## Reference Materials

- `kai/connectors/analytics/base.py` (Task 056) — MetricPoint, DateRange
- `kai/analytics/kpi_models.py` (Task 057) — KPIDefinition, KPIValue, TargetDirection
- `kai/runtime/actions.py` — ProposedAction and action lifecycle patterns
- `kai/runtime/audit.py` — AuditFinding structure
- `kai/runtime/models.py` — SerializableModel pattern
