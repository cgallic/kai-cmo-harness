# Task 080: Build execution monitoring and action history

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 14. Operator Surfaces, Packaging, and Delivery
**Priority:** P2
**Depends on:** 078
**Estimated complexity:** Medium

## Context

Once actions are approved and executing, the operator needs visibility into what is happening, what has completed, what has failed, and what is coming next. The execution monitoring system provides this visibility layer — it tracks action status through the full lifecycle, generates periodic execution reports, and handles failure recovery gracefully. This is the "operations dashboard" that gives operators confidence that the system is working correctly and transparently.

## Scope

Create `kai/operator/execution_monitor.py` containing the ActionHistory queryable record, ExecutionStatus tracker, periodic ExecutionReport generator, and FailureRecovery handler.

## Detailed Requirements

### File: `kai/operator/execution_monitor.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: ExecutionState**
- `pending_approval` — action proposed, awaiting approval
- `approved_waiting` — approved, waiting for execution slot
- `scheduled` — scheduled for future execution
- `executing` — currently being executed
- `completed` — successfully completed
- `failed` — execution failed
- `rolled_back` — completed but then rolled back
- `cancelled` — cancelled before execution

**Model: ExecutionRecord**
- `action_id: str`
- `business_id: str`
- `title: str`
- `action_type: str`
- `channel: str`
- `state: str` — ExecutionState enum value
- `proposed_at: str` — ISO timestamp
- `approved_at: Optional[str]`
- `approved_by: Optional[str]`
- `scheduled_for: Optional[str]` — planned execution time
- `started_at: Optional[str]`
- `completed_at: Optional[str]`
- `failed_at: Optional[str]`
- `failure_reason: Optional[str]`
- `rolled_back_at: Optional[str]`
- `rollback_reason: Optional[str]`
- `risk_tier: str`
- `estimated_spend: Optional[float]`
- `actual_spend: Optional[float]`
- `outcome_summary: Optional[str]` — brief summary of results if completed
- `error_details: Optional[Dict[str, Any]]` — detailed error info if failed
- `retry_count: int` — number of retry attempts
- `max_retries: int` — max allowed retries (default 3)
- `metadata: Dict[str, Any]`

**Class: ActionHistory**
- `__init__(self, workspace_dir: str)`
- `_records: Dict[str, ExecutionRecord]` — in-memory cache of records
- `add_record(self, record: ExecutionRecord)`:
  - Add or update an execution record
  - Persist to disk: `workspace/{business_id}/execution/history.jsonl`
- `update_state(self, action_id: str, new_state: str, **kwargs) -> bool`:
  - Update the state of an action and any additional fields
  - Append state change to history file
  - Return True if found and updated
- `query(self, business_id: str, filters: Dict[str, Any] = None) -> List[ExecutionRecord]`:
  - Query records with filters:
    - `date_start`: ISO date string
    - `date_end`: ISO date string
    - `channel`: filter by channel
    - `action_type`: filter by action type
    - `state`: filter by execution state
    - `risk_tier`: filter by risk tier
  - Return matching records
- `query_sorted(self, business_id: str, sort_by: str = "date", sort_order: str = "desc", limit: int = 50, offset: int = 0, **filters) -> List[ExecutionRecord]`:
  - Query with sorting:
    - sort_by: "date", "impact", "spend"
    - sort_order: "asc", "desc"
  - Apply pagination (limit, offset)
- `group_by(self, business_id: str, group_field: str) -> Dict[str, List[ExecutionRecord]]`:
  - Group records by: "channel", "action_type", "state", "risk_tier"
  - Return dict of {group_value: [records]}
- `get_summary_stats(self, business_id: str, days: int = 30) -> Dict[str, Any]`:
  - Return summary for the last N days:
    - total_actions: int
    - by_state: {state: count}
    - by_channel: {channel: count}
    - success_rate: completed / (completed + failed)
    - average_completion_time_hours: float
    - total_spend: float
    - top_action_types: list of (action_type, count) sorted by frequency

**Class: ExecutionStatusTracker**
- `__init__(self, history: ActionHistory)`
- `get_active_executions(self, business_id: str) -> List[ExecutionRecord]`:
  - Return records in state: "executing", "approved_waiting", "scheduled"
- `get_recent_completions(self, business_id: str, days: int = 7) -> List[ExecutionRecord]`:
  - Return completed records from the last N days
- `get_failures(self, business_id: str, unresolved_only: bool = True) -> List[ExecutionRecord]`:
  - Return failed records
  - If unresolved_only: exclude those that have been retried or rolled back
- `get_upcoming_scheduled(self, business_id: str) -> List[ExecutionRecord]`:
  - Return records in "scheduled" state, sorted by scheduled_for ascending
- `get_pipeline_view(self, business_id: str) -> Dict[str, List[ExecutionRecord]]`:
  - Return records grouped by state for a pipeline/kanban view:
    - pending_approval, approved_waiting, scheduled, executing, completed (last 5), failed

**Model: ExecutionReport**
- `business_id: str`
- `report_type: str` — "daily" or "weekly"
- `period_start: str`
- `period_end: str`
- `generated_at: str`
- `actions_executed: int`
- `actions_completed: int`
- `actions_failed: int`
- `actions_pending: int`
- `success_rate: float` — 0-100 percentage
- `total_spend: float`
- `spend_by_channel: Dict[str, float]`
- `outcomes_observed: List[Dict[str, Any]]` — list of {action_id, title, outcome_summary}
- `top_wins: List[str]` — best outcomes from this period
- `issues_encountered: List[Dict[str, Any]]` — failures and issues
- `upcoming_actions: List[Dict[str, Any]]` — scheduled actions for next period
- `recommendations: List[str]` — system recommendations based on execution patterns

**Class: ExecutionReportGenerator**
- `__init__(self, history: ActionHistory)`
- `generate_daily_report(self, business_id: str, date: str) -> ExecutionReport`:
  - Compile daily report from action history
  - Include: what executed today, outcomes, failures, tomorrow's schedule
  - Generate recommendations based on patterns (e.g., "3 consecutive failures on email channel — investigate deliverability")
- `generate_weekly_report(self, business_id: str, week_start: str) -> ExecutionReport`:
  - Compile weekly rollup
  - Include: weekly totals, success rate trend, spend summary, top wins, issues
  - Compare to previous week if available
- `_identify_top_wins(self, records: List[ExecutionRecord]) -> List[str]`:
  - Identify completed actions with positive outcomes
  - Return top 3 as human-readable strings
- `_identify_issues(self, records: List[ExecutionRecord]) -> List[Dict[str, Any]]`:
  - Identify failures, repeated failures, slow completions
  - Return structured issue descriptions

**Model: FailureRecoveryAction**
- `action_id: str`
- `failure_reason: str`
- `recovery_type: str` — "retry", "rollback", "alternative", "escalate", "abandon"
- `recovery_description: str`
- `auto_recoverable: bool`
- `requires_operator: bool`

**Class: FailureRecovery**
- `__init__(self, history: ActionHistory)`
- `analyze_failure(self, action_id: str) -> FailureRecoveryAction`:
  - Examine the failed action and determine recovery path:
    - If transient error (API timeout, rate limit): suggest retry
    - If content issue (ad disapproved, content rejected by platform): suggest fix + retry
    - If permanent error (invalid config, auth failure): suggest escalate to operator
    - If action has been retried max_retries times: suggest alternative approach or abandon
  - Return FailureRecoveryAction with recommendation
- `attempt_retry(self, action_id: str) -> Dict[str, Any]`:
  - Increment retry_count on the record
  - If retry_count >= max_retries: return {success: False, reason: "max_retries_exceeded"}
  - Reset state to "approved_waiting" for re-execution
  - Return {success: True, retry_number, next_attempt_at}
- `attempt_rollback(self, action_id: str, reason: str) -> Dict[str, Any]`:
  - Set state to "rolled_back" with reason
  - Return {success: True, rolled_back_at}
  - Note: actual rollback logic (undoing the action) is delegated to the channel connector
- `suggest_alternative(self, action_id: str) -> Optional[Dict[str, Any]]`:
  - Based on the failure reason, suggest an alternative action
  - E.g., if ad disapproved → suggest copy revision; if email bounce → suggest list cleanup
  - Return suggested alternative action data or None
- `escalate_to_operator(self, action_id: str, summary: str) -> Dict[str, Any]`:
  - Create an escalation with full failure context
  - Return escalation details for operator notification

## Output Files

- `kai/operator/execution_monitor.py`

## Acceptance Criteria

- File parses as valid Python
- ActionHistory correctly persists records to JSONL and supports all query filters
- query_sorted handles all three sort options with pagination
- group_by produces correct groupings for all four group fields
- ExecutionStatusTracker provides clear views of active, completed, failed, and upcoming actions
- get_pipeline_view returns the correct pipeline stages
- ExecutionReportGenerator produces daily and weekly reports with genuine recommendations (not placeholder text)
- FailureRecovery correctly classifies failures into recovery types
- attempt_retry enforces max_retries limit
- Failure analysis distinguishes transient vs. permanent errors
- get_summary_stats calculates success_rate and average_completion_time correctly
- All models use SerializableModel mixin
- File I/O follows project patterns (JSONL, atomic writes)

## Reference Materials

- `kai/runtime/actions.py` — action lifecycle, file I/O patterns
- `kai/runtime/store.py` — workspace storage conventions
- `kai/operator/remote_surface.py` (Task 078) — StatusResponse, DashboardResponse
- `kai/compliance/audit_trail.py` (Task 066) — audit logging patterns
- `kai/runtime/models.py` — SerializableModel pattern
