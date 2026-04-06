# Task 065: Build revision workflows and kill switches

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 11. Approval, Compliance, and Policy Control
**Priority:** P2
**Depends on:** 064
**Estimated complexity:** Medium

## Context

When an operator rejects a proposed action, the system needs a structured way to revise and resubmit. The revision workflow captures rejection context, routes it back to the creative engine, and tracks revision cycles to prevent infinite loops. The kill switch system provides emergency controls — an operator must be able to pause everything instantly when something goes wrong (a compliance issue surfaces, a budget overrun is detected, or a brand crisis occurs). These are critical safety mechanisms that give operators confidence in an autonomous marketing system.

## Scope

Create `kai/compliance/revision.py` containing the RevisionWorkflow class, KillSwitch class, OperatorOverride model, and all supporting types for managing rejection → revision cycles and emergency stop mechanisms.

## Detailed Requirements

### File: `kai/compliance/revision.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: RejectionCategory**
- `brand_voice` — tone, style, or voice doesn't match brand
- `compliance` — legal or platform compliance concern
- `strategy` — doesn't align with current business strategy
- `timing` — wrong time for this action (seasonal, business cycle)
- `budget` — budget concern or prioritization issue
- `quality` — content quality insufficient
- `accuracy` — factual inaccuracy or outdated information
- `other` — doesn't fit other categories

**Enum: KillSwitchScope**
- `all` — freeze all actions for all businesses
- `business` — freeze all actions for a specific business
- `channel` — freeze all actions for a specific channel
- `campaign` — freeze a specific campaign
- `action_type` — freeze all actions of a specific type

**Enum: SystemStatus**
- `active` — system operating normally
- `paused` — system paused, no new actions executing
- `emergency_stop` — everything frozen, operator alerted
- `maintenance` — system in maintenance mode

**Model: Rejection**
- `id: str` — format `rej_{uuid_hex[:12]}`
- `action_id: str` — the rejected ProposedAction
- `rejected_by: str` — operator name/id
- `rejected_at: str` — ISO timestamp
- `category: str` — RejectionCategory enum value
- `reason: str` — free-text explanation from operator
- `specific_issues: List[str]` — list of specific things wrong (e.g., ["headline too aggressive", "CTA doesn't match brand"])
- `revision_guidance: Optional[str]` — operator's guidance for revision
- `do_not_retry: bool` — if True, do not attempt revision (kill this action)

**Model: RevisionAttempt**
- `id: str` — format `rev_{uuid_hex[:12]}`
- `action_id: str` — original action
- `revision_number: int` — 1, 2, 3...
- `rejection_id: str` — which rejection triggered this revision
- `changes_made: List[str]` — list of specific changes in this revision
- `revised_content: Dict[str, Any]` — the new content/configuration
- `created_at: str`
- `status: str` — "pending_review", "approved", "rejected", "escalated"

**Model: RevisionHistory**
- `action_id: str`
- `original_version: Dict[str, Any]` — the original proposed action content
- `rejections: List[Rejection]` — ordered list of rejections
- `revisions: List[RevisionAttempt]` — ordered list of revision attempts
- `current_status: str` — "pending", "approved", "exhausted", "killed"
- `total_revision_cycles: int`
- `max_revision_cycles: int` — default 3

**Class: RevisionWorkflow**
- `__init__(self, max_cycles: int = 3)`
- `handle_rejection(self, action_id: str, rejection: Rejection, action_data: Dict[str, Any]) -> RevisionAttempt or None`:
  - If rejection.do_not_retry is True, return None and mark action as killed
  - Check if max revision cycles exceeded → return None and mark as exhausted/escalated
  - Create a RevisionAttempt with revision_number incremented
  - Include rejection context in the revision attempt for the creative engine to use
  - Return the RevisionAttempt
- `create_revision_context(self, rejection: Rejection, original_content: Dict[str, Any]) -> Dict[str, Any]`:
  - Build a context dict that the creative engine can consume:
    - original_content: the rejected content
    - rejection_category: the category
    - rejection_reason: the reason
    - specific_issues: list of issues
    - revision_guidance: operator's guidance
    - do_not_change: list of elements that were NOT flagged (preserve what's working)
  - Return the context dict
- `get_revision_history(self, action_id: str) -> RevisionHistory`:
  - Retrieve or construct the revision history for an action
  - Return RevisionHistory object
- `should_escalate(self, action_id: str) -> bool`:
  - Return True if revision cycles exhausted (>= max_cycles)
  - Return True if multiple rejections with different categories (unclear what operator wants)
- `build_escalation_summary(self, history: RevisionHistory) -> str`:
  - Generate a human-readable summary of the revision history for escalation
  - Include: original action, each rejection with reason, each revision with changes, recommendation

**Model: KillSwitchActivation**
- `id: str` — format `kill_{uuid_hex[:12]}`
- `scope: str` — KillSwitchScope enum value
- `scope_target: Optional[str]` — the specific business_id, channel, campaign_id, or action_type being killed
- `activated_by: str` — "operator", "system", "compliance_engine", "spend_monitor", "anomaly_detector"
- `activated_at: str` — ISO timestamp
- `reason: str` — why the kill switch was activated
- `trigger_event: Optional[str]` — what triggered this (e.g., "spend_threshold_exceeded", "compliance_violation_detected")
- `deactivated_at: Optional[str]` — when it was lifted (None if still active)
- `deactivated_by: Optional[str]`
- `deactivation_reason: Optional[str]`
- `affected_action_ids: List[str]` — list of actions that were paused by this kill switch

**Class: KillSwitch**
- `__init__(self)`
- `_active_switches: List[KillSwitchActivation]` — list of currently active kill switches
- `_system_status: str` — SystemStatus enum value, default "active"
- `pause_all_actions(self, activated_by: str, reason: str) -> KillSwitchActivation`:
  - Create a KillSwitchActivation with scope="all"
  - Set system_status to "paused"
  - Return the activation record
- `pause_channel(self, channel: str, activated_by: str, reason: str) -> KillSwitchActivation`:
  - Create a KillSwitchActivation with scope="channel", scope_target=channel
  - Return the activation record
- `pause_campaign(self, campaign_id: str, activated_by: str, reason: str) -> KillSwitchActivation`:
  - Create a KillSwitchActivation with scope="campaign", scope_target=campaign_id
  - Return the activation record
- `pause_action_type(self, action_type: str, activated_by: str, reason: str) -> KillSwitchActivation`:
  - Create a KillSwitchActivation with scope="action_type", scope_target=action_type
- `emergency_stop(self, activated_by: str, reason: str) -> KillSwitchActivation`:
  - Create a KillSwitchActivation with scope="all"
  - Set system_status to "emergency_stop"
  - Should also generate a notification flag for immediate operator alert
  - Return the activation record
- `deactivate(self, activation_id: str, deactivated_by: str, reason: str) -> bool`:
  - Find the activation, set deactivated_at and deactivated_by
  - If no other active switches remain, set system_status back to "active"
  - Return True if found and deactivated, False if not found
- `is_action_blocked(self, action: Any) -> Tuple[bool, Optional[str]]`:
  - Check all active kill switches to see if this action is blocked
  - Check scopes: "all" blocks everything, "channel" blocks matching channel, "campaign" blocks matching campaign, "action_type" blocks matching type
  - Return (is_blocked, reason_if_blocked)
- `get_active_switches(self) -> List[KillSwitchActivation]`:
  - Return all currently active kill switches (deactivated_at is None)
- `get_system_status(self) -> str`:
  - Return current SystemStatus

**Model: OperatorOverride**
- `id: str` — format `ovr_{uuid_hex[:12]}`
- `action_id: str` — the action being overridden
- `override_type: str` — "force_approve", "force_reject", "change_route", "change_priority", "bypass_compliance"
- `original_decision: str` — what the system decided
- `override_decision: str` — what the operator decided instead
- `reason: str` — documented reason for the override
- `overridden_by: str` — operator name/id
- `overridden_at: str` — ISO timestamp
- `acknowledged_risk: bool` — operator acknowledged any compliance or risk implications

**Function: create_operator_override(action_id: str, override_type: str, original_decision: str, override_decision: str, reason: str, overridden_by: str, risk_acknowledgment: bool = False) -> OperatorOverride**
- Validate override_type is one of the allowed values
- If override_type is "bypass_compliance", require risk_acknowledgment=True
- Return the OperatorOverride object

## Output Files

- `kai/compliance/revision.py`

## Acceptance Criteria

- File parses as valid Python
- `RevisionWorkflow.handle_rejection()` correctly enforces max revision cycles
- `create_revision_context()` produces a dict the creative engine can consume (preserves what's working)
- `should_escalate()` catches both cycle exhaustion and conflicting rejection categories
- `KillSwitch` correctly manages multiple concurrent active switches
- `is_action_blocked()` checks all scopes correctly (all > business > channel > campaign > action_type)
- `emergency_stop()` sets system status to "emergency_stop"
- `deactivate()` correctly resets system status when no active switches remain
- `OperatorOverride` requires risk acknowledgment for compliance bypass
- All models use SerializableModel mixin
- No external dependencies beyond stdlib

## Reference Materials

- `kai/compliance/approval_routing.py` (Task 064) — RoutingDecision, ApprovalRoute
- `kai/runtime/actions.py` — ProposedAction structure
- `kai/runtime/models.py` — SerializableModel pattern
