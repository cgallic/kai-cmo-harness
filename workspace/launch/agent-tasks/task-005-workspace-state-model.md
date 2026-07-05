# Task 005: Build connected workspace state model

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 1. Workspace and Business Understanding
**Priority:** P2
**Depends on:** 001
**Estimated complexity:** Medium

## Context

A BusinessProfile describes what a business IS. WorkspaceState describes what the system CAN DO right now for that business — which integrations are connected, what permissions the system has, what budgets are set, and what the operator has approved for automatic execution. This is the live operational layer that changes as integrations are connected/disconnected and operator preferences evolve. The workspace state persists to disk so it survives between sessions.

## Scope

Build `kai/models/workspace_state.py` with the WorkspaceState model and related sub-models, plus persistence functions to save/load state to YAML/JSON in the `workspace/` directory.

## Detailed Requirements

### File: `kai/models/workspace_state.py`

Use the same Pydantic/fallback import pattern as `gateway/models.py`.

**Sub-model: Integration**
- `platform_name: str` — canonical platform name (should match channel normalization output)
- `connection_type: Optional[str]` — one of: "oauth", "api_key", "webhook", "manual", "mcp"
- `status: str` — one of: "connected", "expired", "pending", "disconnected", "error"
- `capabilities: List[str]` — list of action strings this integration enables, e.g., ["read_analytics", "post_content", "manage_ads", "read_reviews"]
- `scopes: List[str]` — OAuth scopes or permission scopes granted
- `connected_at: Optional[str]` — ISO timestamp
- `last_sync: Optional[str]` — ISO timestamp of last successful data sync
- `expires_at: Optional[str]` — ISO timestamp of when auth expires (for OAuth tokens)
- `account_id: Optional[str]` — platform-specific account ID
- `metadata: Dict[str, Any]` — platform-specific extra data

**Sub-model: BudgetConstraint**
- `daily_cap: Optional[float]` — maximum USD spend per day
- `weekly_cap: Optional[float]` — maximum USD spend per week
- `monthly_cap: Optional[float]` — maximum USD spend per month
- `per_action_cap: Optional[float]` — maximum USD for a single action without approval
- `total_spent_this_month: float = 0.0` — running total for the current month
- `last_reset_date: Optional[str]` — when the monthly counter was last reset

**Sub-model: ApprovalDefaults**
- `auto_approve_below: Optional[float]` — auto-approve actions costing less than this USD amount
- `require_human_for: List[str]` — action types that always require human approval, e.g., ["ad_spend", "email_blast", "public_post", "account_change"]
- `auto_approve_types: List[str]` — action types that are always auto-approved, e.g., ["audit", "report", "draft", "internal_note"]
- `escalation_channel: Optional[str]` — where to send approval requests (e.g., "discord", "email", "slack")
- `escalation_contact: Optional[str]` — who to notify for approvals
- `max_auto_actions_per_day: Optional[int]` — rate limit on automatic actions

**Sub-model: ChannelEnablement**
- `channel: str` — canonical channel name
- `is_enabled: bool = False` — whether this channel is active for this workspace
- `is_configured: bool = False` — whether all prerequisites are met
- `missing_prerequisites: List[str]` — what's still needed to activate, e.g., ["connect Google Ads account", "set daily budget"]
- `priority: Optional[int]` — operator-assigned priority ranking (1 = highest)
- `notes: Optional[str]`

**Sub-model: OperatorPreferences**
- `notification_channel: Optional[str]` — preferred notification method
- `active_hours: Optional[str]` — when the operator is available, e.g., "9am-5pm EST"
- `response_time_expectation: Optional[str]` — e.g., "same-day", "within-1-hour", "next-business-day"
- `preferred_report_frequency: Optional[str]` — e.g., "daily", "weekly", "monthly"
- `language: str = "en"` — content language
- `timezone: str = "America/New_York"` — operator's timezone
- `custom_preferences: Dict[str, Any]` — catch-all for operator-specific settings

**Top-level: WorkspaceState**
- `workspace_id: str` — unique workspace identifier (matches BusinessProfile.id)
- `business_profile_id: str` — linked BusinessProfile ID
- `integrations: List[Integration]` — all platform integrations
- `budget: BudgetConstraint` — budget constraints
- `approval: ApprovalDefaults` — approval workflow settings
- `enabled_channels: List[ChannelEnablement]` — which channels are active
- `operator: OperatorPreferences` — operator preferences
- `active_modules: List[str]` — currently activated module IDs
- `disabled_modules: List[str]` — explicitly disabled modules
- `last_audit_date: Optional[str]` — when the last audit was run
- `last_action_date: Optional[str]` — when the last action was taken
- `state_version: str = "1.0.0"` — schema version
- `created_at: Optional[str]` — ISO timestamp
- `updated_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all

**Persistence Functions:**

1. **`save_workspace_state(state: WorkspaceState, workspace_dir: str = "workspace") -> str`**
   - Serialize the WorkspaceState to YAML
   - Save to `{workspace_dir}/state/{workspace_id}.yaml`
   - Create directories if they don't exist
   - Return the file path written
   - Use yaml.safe_dump for serialization
   - Handle model_dump() for both Pydantic and fallback BaseModel

2. **`load_workspace_state(workspace_id: str, workspace_dir: str = "workspace") -> Optional[WorkspaceState]`**
   - Load from `{workspace_dir}/state/{workspace_id}.yaml`
   - Return None if file doesn't exist (not an error — new workspace)
   - Parse YAML and construct WorkspaceState
   - Handle missing/extra fields gracefully (forward compatibility)

3. **`update_integration_status(state: WorkspaceState, platform: str, status: str, last_sync: Optional[str] = None) -> WorkspaceState`**
   - Find the integration by platform_name, update its status and optionally last_sync
   - If integration doesn't exist, create a new one with the given status
   - Return the updated state (do not mutate in place — return a new copy)

4. **`check_budget_available(state: WorkspaceState, amount: float) -> bool`**
   - Check if spending `amount` would exceed any budget constraint
   - Check per_action_cap, daily_cap (requires tracking — use metadata for daily tracking), monthly_cap
   - Return True if the spend is within limits

5. **`requires_approval(state: WorkspaceState, action_type: str, cost: Optional[float] = None) -> bool`**
   - Determine if an action needs human approval
   - If action_type is in require_human_for -> True
   - If action_type is in auto_approve_types -> False
   - If cost is not None and auto_approve_below is set and cost < auto_approve_below -> False
   - Default: True (conservative — require approval by default)

6. **`get_connected_platforms(state: WorkspaceState) -> List[str]`**
   - Return list of platform names where status == "connected"

7. **`get_available_capabilities(state: WorkspaceState) -> Dict[str, List[str]]`**
   - Return dict mapping platform_name -> capabilities for all connected integrations

### YAML import handling
- Import yaml with try/except
- If yaml is not available, fall back to JSON (import json, use json.dumps/loads)
- Include clear error messages about installing PyYAML

### Update `kai/models/__init__.py`
- Add imports for WorkspaceState and all sub-models from workspace_state.py
- Extend `__all__` list (do not overwrite existing exports from Task 001)

## Output Files

- `kai/models/workspace_state.py`
- `kai/models/__init__.py` (modify — add new exports)

## Acceptance Criteria

- [ ] `workspace_state.py` contains all 5 sub-models and the top-level WorkspaceState
- [ ] All 7 persistence/utility functions are implemented
- [ ] `save_workspace_state` serializes to YAML in `workspace/state/` directory
- [ ] `load_workspace_state` returns None for missing files, not an error
- [ ] `check_budget_available` checks all relevant caps (per-action, daily, monthly)
- [ ] `requires_approval` defaults to True (conservative) when no rules match
- [ ] All sub-models have sensible defaults so a minimal WorkspaceState can be created
- [ ] YAML import has fallback to JSON
- [ ] `kai/models/__init__.py` is updated to export workspace_state models (without removing existing exports)
- [ ] Pydantic/fallback import pattern matches `gateway/models.py`

## Reference Materials

- `kai/models/business_profile.py` (Task 001) — the profile this state links to
- `gateway/models.py` — Pydantic import fallback pattern
- `kai/runtime/models.py` — KaiWorkspaceProfile for inspiration
- `kai/runtime/store.py` — existing persistence patterns
- `config.yaml.example` — workspace config section
