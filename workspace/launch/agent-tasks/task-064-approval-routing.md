# Task 064: Build approval routing by risk tier

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 11. Approval, Compliance, and Policy Control
**Priority:** P1
**Depends on:** 022
**Estimated complexity:** Medium

## Context

Not every marketing action needs the same level of human oversight. Fixing a broken tracking script is auto-approvable; launching a $5,000 ad campaign requires explicit operator sign-off. The approval routing system examines each ProposedAction's risk tier, spend amount, content type, and business configuration to determine the correct approval path. This is the trust and safety layer that ensures the operator stays in control while allowing low-risk optimizations to proceed efficiently. Every action in the system passes through this router before execution.

## Scope

Create `kai/compliance/approval_routing.py` containing the ApprovalRouter class, approval route models, escalation logic, configurable routing rules, and an audit log for routing decisions.

## Detailed Requirements

### File: `kai/compliance/approval_routing.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: ApprovalRoute**
- `auto_approve` — execute immediately, no human review needed
- `low_touch` — notify operator, execute after configurable delay (default 1 hour) unless vetoed
- `operator_review` — queue for operator, require explicit approval (can batch-approve)
- `operator_approval` — queue with full preview, require individual sign-off
- `executive_approval` — require two approvals or escalate to designated executive contact

**Enum: EscalationReason**
- `timeout` — action not reviewed within time window
- `spend_threshold` — spend exceeds a threshold for the current route
- `compliance_flag` — compliance engine flagged a concern
- `override_request` — operator requested escalation
- `multiple_rejections` — action has been rejected and revised multiple times

**Model: RoutingDecision**
- `id: str` — format `route_{uuid_hex[:12]}`
- `action_id: str` — which ProposedAction this routes
- `risk_tier: str` — RiskTier from ProposedAction (auto, low, medium, high, critical)
- `route: str` — ApprovalRoute enum value (the determined route)
- `reason: str` — human-readable explanation of why this route was chosen
- `contributing_factors: List[str]` — list of factors that influenced the routing decision
- `estimated_spend: Optional[float]` — if the action involves spend
- `content_is_public: bool` — whether this action produces public-facing content
- `compliance_flags: List[str]` — any compliance concerns from the compliance engine
- `auto_execute_at: Optional[str]` — for low_touch: ISO timestamp when auto-execution will occur
- `escalate_at: Optional[str]` — ISO timestamp when this will escalate if not reviewed
- `decided_at: str` — ISO timestamp
- `decided_by: str` — "system" for automatic routing, operator name for overrides

**Model: RoutingConfig**
- `business_id: str`
- `auto_approve_enabled: bool` — whether any actions can be auto-approved (default True)
- `auto_approve_max_spend: float` — max spend for auto-approval (default 0.0 — no spend auto-approved)
- `low_touch_delay_minutes: int` — delay before low-touch auto-execution (default 60)
- `low_touch_max_spend: float` — max spend for low-touch routing (default 50.0)
- `operator_review_max_spend: float` — max spend for operator review (default 500.0)
- `operator_approval_max_spend: float` — max spend for operator approval (default 5000.0)
- `executive_threshold_spend: float` — spend above this triggers executive approval (default 5000.0)
- `escalation_timeout_hours: int` — hours before escalation if not reviewed (default 24)
- `require_approval_for_public_content: bool` — force operator_review minimum for any public-facing content (default True)
- `custom_overrides: Dict[str, str]` — action_type -> forced route overrides (e.g., {"kaicalls_setup": "operator_approval"})

**Model: RoutingAuditEntry**
- `timestamp: str` — ISO timestamp
- `action_id: str`
- `business_id: str`
- `route_chosen: str` — ApprovalRoute value
- `risk_tier: str`
- `reason: str`
- `approver: Optional[str]` — who approved (None if auto)
- `approved_at: Optional[str]`
- `rejected_at: Optional[str]`
- `rejection_reason: Optional[str]`
- `escalated: bool`
- `escalation_reason: Optional[str]`

**Class: ApprovalRouter**
- `__init__(self, config: RoutingConfig)`
- `route_action(self, action: Any, compliance_result: Optional[Any] = None) -> RoutingDecision`:
  - Accept a ProposedAction (typed as Any to avoid circular imports) and optional ComplianceResult
  - Determine the route using the following priority logic:
    1. If compliance_result exists and has violations → force `operator_approval` minimum
    2. Check custom_overrides for action_type → use forced route if matched
    3. Evaluate risk_tier:
       - `auto` risk_tier → `auto_approve` (if auto_approve_enabled and spend <= auto_approve_max_spend)
       - `low` risk_tier → `low_touch` (if spend <= low_touch_max_spend)
       - `medium` risk_tier → `operator_review`
       - `high` risk_tier → `operator_approval`
       - `critical` risk_tier → `executive_approval`
    4. Override check: if content_is_public and require_approval_for_public_content → minimum `operator_review`
    5. Spend escalation: if estimated_spend exceeds the threshold for the current route, escalate to next tier
  - Calculate auto_execute_at for low_touch (current time + delay)
  - Calculate escalate_at (current time + escalation_timeout)
  - Return RoutingDecision with full reasoning

- `escalate(self, decision: RoutingDecision, reason: str) -> RoutingDecision`:
  - Create a new RoutingDecision with the next-higher route
  - Route hierarchy: auto_approve → low_touch → operator_review → operator_approval → executive_approval
  - Set escalation_reason on the new decision
  - If already at executive_approval, keep it there but add "max_escalation_reached" to contributing_factors

- `check_for_timeout_escalation(self, decision: RoutingDecision, current_time: str) -> Optional[RoutingDecision]`:
  - Compare current_time against decision.escalate_at
  - If current_time > escalate_at and action hasn't been approved/rejected, trigger escalation
  - Return new escalated RoutingDecision or None if no escalation needed

- `log_routing_decision(self, decision: RoutingDecision, business_id: str) -> RoutingAuditEntry`:
  - Create an audit entry from the routing decision
  - Return the entry (storage is handled by the audit trail system, Task 066)

- `_determine_content_is_public(self, action: Any) -> bool`:
  - Check action_type: website_update, social_post, ad_campaign, content_creation → True
  - analytics_fix, kaicalls_setup (internal configuration) → False
  - email_sequence → True (external-facing)
  - Default to True (safer)

- `_estimate_spend(self, action: Any) -> float`:
  - Extract estimated_spend from action metadata
  - Default to 0.0 if not specified

**Function: get_default_routing_config(business_id: str) -> RoutingConfig**
- Returns a sensible default configuration
- auto_approve_enabled = True
- Conservative spend thresholds
- 24-hour escalation timeout
- require_approval_for_public_content = True

## Output Files

- `kai/compliance/approval_routing.py`

## Acceptance Criteria

- File parses as valid Python
- `ApprovalRouter.route_action()` implements the exact priority logic described: compliance flags → custom overrides → risk tier → public content check → spend escalation
- Spend escalation correctly bumps the route to the next tier when spend exceeds the threshold
- `escalate()` correctly moves up the route hierarchy and handles the max-tier case
- `check_for_timeout_escalation()` correctly compares ISO timestamps
- `_determine_content_is_public()` covers all ActionType values from Task 022
- `RoutingConfig` defaults are conservative and safe (no auto-approved spend, require approval for public content)
- All models use SerializableModel mixin
- `log_routing_decision()` creates a complete audit entry
- No external dependencies beyond stdlib

## Reference Materials

- `kai/runtime/actions.py` — ProposedAction structure, RiskTier, ActionType
- `kai/compliance/engine.py` (Task 062) — ComplianceResult that feeds into routing
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/runtime/audit.py` — enum patterns
