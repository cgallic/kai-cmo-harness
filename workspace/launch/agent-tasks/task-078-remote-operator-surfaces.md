# Task 078: Build remote operator surfaces

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 14. Operator Surfaces, Packaging, and Delivery
**Priority:** P1
**Depends on:** 022
**Estimated complexity:** Large

## Context

While the local operator surface (Task 077) serves Claude Code-style interaction, the remote operator surface exposes the same capabilities via HTTP API for dashboards, mobile apps, and third-party integrations. This module extends the existing FastAPI gateway with routes for audit, proposals, approvals, status, history, dashboard, watchers, and profile management. It also defines the structured JSON response formats that front-end applications would consume. The gateway already has patterns established in `gateway/routers/` — this task extends that structure with Kai-specific operator routes.

## Scope

Create `kai/operator/remote_surface.py` containing the API route definitions and response models, plus a corresponding gateway router file `gateway/routers/kai_operator.py` that integrates with the existing FastAPI gateway.

## Detailed Requirements

### File: `kai/operator/remote_surface.py`

This file defines the response models and business logic layer that the gateway router calls.

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Model: AuditResponse**
- `business_id: str`
- `audit_type: str` — "full" or scoped type
- `run_at: str` — ISO timestamp
- `overall_score: float` — 0-100
- `category_scores: Dict[str, float]` — {category: score}
- `finding_counts: Dict[str, int]` — {severity: count}
- `top_findings: List[Dict[str, Any]]` — top 10 findings with full detail
- `recommendations: List[str]` — top 5 prioritized recommendations

**Model: ProposalListResponse**
- `business_id: str`
- `total_count: int`
- `pending_count: int`
- `approved_count: int`
- `rejected_count: int`
- `proposals: List[Dict[str, Any]]` — list of proposals with: id, title, channel, risk_tier, priority, status, created_at, estimated_spend
- `page: int`
- `page_size: int`
- `has_more: bool`

**Model: ProposalDetailResponse**
- `proposal: Dict[str, Any]` — full proposal details
- `finding: Optional[Dict[str, Any]]` — the finding that generated this proposal
- `compliance_result: Optional[Dict[str, Any]]` — compliance check results if run
- `preview: Optional[Dict[str, Any]]` — content preview if applicable
- `routing_decision: Optional[Dict[str, Any]]` — how this was routed
- `revision_history: Optional[Dict[str, Any]]` — if this has been revised
- `similar_past_actions: List[Dict[str, Any]]` — similar actions that were taken before, with outcomes

**Model: ApprovalRequest**
- `action_id: str`
- `approved_by: str`
- `notes: Optional[str]`

**Model: RejectionRequest**
- `action_id: str`
- `rejected_by: str`
- `reason: str`
- `category: Optional[str]` — RejectionCategory
- `specific_issues: List[str]`
- `revision_guidance: Optional[str]`
- `do_not_retry: bool`

**Model: ApprovalResponse**
- `action_id: str`
- `status: str` — "approved" or "rejected"
- `route: str` — the approval route used
- `next_action: str` — what happens next ("queued_for_execution", "revision_in_progress", "killed")
- `timestamp: str`

**Model: StatusResponse**
- `business_id: str`
- `system_status: str` — "active", "paused", "emergency_stop"
- `pending_actions: Dict[str, int]` — {risk_tier: count}
- `active_campaigns: List[Dict[str, Any]]` — list with name, channel, status, key_metric
- `recent_actions: List[Dict[str, Any]]` — last 10 actions with timestamp, title, status
- `active_watchers: int`
- `watcher_findings_today: int`
- `critical_alerts: List[Dict[str, Any]]` — any critical/immediate findings
- `kill_switches_active: List[Dict[str, Any]]`

**Model: DashboardResponse**
- `business_id: str`
- `business_name: str`
- `generated_at: str`
- `overall_health_score: float` — 0-100
- `overall_health: str` — "excellent", "good", "needs_attention", "poor", "critical"
- `scorecards: List[Dict[str, Any]]` — the five category scorecards
- `top_wins: List[str]`
- `top_concerns: List[str]`
- `recommended_actions: List[str]`
- `pending_approvals: int`
- `channel_overview: List[Dict[str, Any]]` — per-channel summary
- `trend_data: Optional[Dict[str, Any]]` — vs last period

**Model: WatcherResponse**
- `business_id: str`
- `total_watchers: int`
- `enabled_watchers: int`
- `recent_findings: List[Dict[str, Any]]` — findings with: id, watcher, title, severity, urgency, timestamp, auto_eligible
- `findings_by_severity: Dict[str, int]`
- `last_run_times: Dict[str, str]` — {watcher_name: last_run_timestamp}

**Model: ProfileResponse**
- `business_id: str`
- `profile: Dict[str, Any]` — full business profile
- `archetype: str`
- `active_channels: List[str]`
- `last_updated: str`

**Model: ProfileUpdateRequest**
- `fields: Dict[str, Any]` — fields to update

**Class: RemoteOperatorSurface**
- `__init__(self, workspace_dir: str)`
- Methods mirror LocalOperatorSurface but return response models instead of formatted strings:
  - `get_audit(self, business_id: str, scope: str = "full") -> AuditResponse`
  - `get_proposals(self, business_id: str, status_filter: str = "pending", channel: Optional[str] = None, page: int = 1, page_size: int = 20) -> ProposalListResponse`
  - `get_proposal_detail(self, business_id: str, action_id: str) -> ProposalDetailResponse`
  - `approve_action(self, request: ApprovalRequest) -> ApprovalResponse`
  - `reject_action(self, request: RejectionRequest) -> ApprovalResponse`
  - `execute_action(self, business_id: str, action_id: str) -> Dict[str, Any]`
  - `get_status(self, business_id: str) -> StatusResponse`
  - `get_history(self, business_id: str, days: int = 30, channel: Optional[str] = None, limit: int = 50) -> Dict[str, Any]`
  - `get_dashboard(self, business_id: str) -> DashboardResponse`
  - `get_watchers(self, business_id: str) -> WatcherResponse`
  - `get_profile(self, business_id: str) -> ProfileResponse`
  - `update_profile(self, business_id: str, request: ProfileUpdateRequest) -> ProfileResponse`

### File: `gateway/routers/kai_operator.py`

Follow the existing router patterns in `gateway/routers/` (e.g., `actions.py`, `runtime.py`).

**FastAPI router with prefix `/api/kai`**:
- `GET /api/kai/audit/{business_id}` — run or retrieve latest audit
  - Query params: scope (default "full")
  - Returns AuditResponse as JSON
- `GET /api/kai/proposals/{business_id}` — list proposals
  - Query params: status (default "pending"), channel, page (default 1), page_size (default 20)
  - Returns ProposalListResponse as JSON
- `GET /api/kai/proposals/{business_id}/{action_id}` — get proposal detail
  - Returns ProposalDetailResponse as JSON
- `POST /api/kai/proposals/{action_id}/approve` — approve action
  - Body: ApprovalRequest as JSON
  - Returns ApprovalResponse as JSON
- `POST /api/kai/proposals/{action_id}/reject` — reject action
  - Body: RejectionRequest as JSON
  - Returns ApprovalResponse as JSON
- `POST /api/kai/proposals/{action_id}/execute` — execute approved action
  - Returns execution status as JSON
- `GET /api/kai/status/{business_id}` — system status
  - Returns StatusResponse as JSON
- `GET /api/kai/history/{business_id}` — action history
  - Query params: days (default 30), channel, limit (default 50)
  - Returns paginated history as JSON
- `GET /api/kai/dashboard/{business_id}` — dashboard summary
  - Returns DashboardResponse as JSON
- `GET /api/kai/watchers/{business_id}` — watcher findings
  - Returns WatcherResponse as JSON
- `GET /api/kai/profile/{business_id}` — business profile
  - Returns ProfileResponse as JSON
- `PUT /api/kai/profile/{business_id}` — update business profile
  - Body: ProfileUpdateRequest as JSON
  - Returns updated ProfileResponse as JSON

**Authentication**: API key-based via `x-api-key` header (reuse existing `gateway/auth.py` pattern)

**Error handling**: all routes should catch exceptions and return structured error responses with status codes:
- 200: success
- 400: bad request (invalid input)
- 404: business/action not found
- 401: unauthorized (bad API key)
- 500: internal error

## Output Files

- `kai/operator/remote_surface.py`
- `gateway/routers/kai_operator.py`

## Acceptance Criteria

- All files parse as valid Python
- All 12 API routes are defined with proper HTTP methods, path params, and query params
- Response models include all specified fields
- ProposalDetailResponse includes finding context and compliance result (not just the bare proposal)
- DashboardResponse includes scorecards, wins/concerns, and recommendations
- Gateway router follows existing patterns in `gateway/routers/actions.py` and `gateway/routers/runtime.py`
- Authentication uses the existing `verify_api_key` dependency from `gateway/auth.py`
- Error handling returns structured JSON error responses
- Pagination is implemented for proposals and history endpoints
- ProfileUpdateRequest only allows updating safe fields (not business_id or archetype)
- All response models use SerializableModel mixin

## Reference Materials

- `gateway/routers/actions.py` — existing router patterns for FastAPI routes
- `gateway/routers/runtime.py` — existing runtime router patterns
- `gateway/main.py` — how routers are registered
- `gateway/auth.py` — API key authentication pattern
- `gateway/models.py` — existing response models
- `kai/operator/local_surface.py` (Task 077) — local surface methods to mirror
- `kai/analytics/scorecards.py` (Task 060) — DashboardSummary for dashboard response
- `kai/runtime/models.py` — SerializableModel pattern
