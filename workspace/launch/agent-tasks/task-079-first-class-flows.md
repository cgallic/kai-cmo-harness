# Task 079: Build first-class flows

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 14. Operator Surfaces, Packaging, and Delivery
**Priority:** P1
**Depends on:** 077, 078
**Estimated complexity:** Large

## Context

Individual commands (audit, approve, reject) are useful but operators need guided workflows — multi-step sequences that walk them through the complete cycle from diagnosis to action to monitoring. First-class flows are the "happy paths" that most operators will follow: onboarding a new business, reviewing an audit, approving/rejecting/revising proposals, monitoring execution, and reviewing learnings. Each flow orchestrates multiple subsystems into a coherent, step-by-step experience. These flows are what make Kai feel like a marketing operating system rather than a bag of disconnected commands.

## Scope

Create `kai/flows/` module with five flow implementations: OnboardingFlow, AuditReviewFlow, ApproveRejectReviseFlow, ExecutionMonitoringFlow, and LearningReviewFlow.

## Detailed Requirements

### File: `kai/flows/__init__.py`
- Module docstring explaining the flows system
- Export all flow classes

### File: `kai/flows/onboarding.py`

**Model: OnboardingStep**
- `step_number: int`
- `title: str`
- `description: str`
- `status: str` — "pending", "in_progress", "completed", "skipped"
- `required: bool`
- `input_schema: Dict[str, Any]` — what data this step needs
- `output: Optional[Dict[str, Any]]` — what this step produced

**Model: OnboardingState**
- `business_id: str`
- `started_at: str`
- `current_step: int`
- `steps: List[OnboardingStep]`
- `business_profile: Optional[Dict[str, Any]]`
- `archetype: Optional[str]`
- `initial_audit: Optional[Dict[str, Any]]`
- `initial_proposals: Optional[Dict[str, Any]]`
- `completed_at: Optional[str]`

**Class: OnboardingFlow**
- `__init__(self, workspace_dir: str)`
- `start(self, business_name: str) -> OnboardingState`:
  - Initialize the onboarding flow with 8 steps
  - Return the initial state
- `get_steps(self) -> List[OnboardingStep]`:
  - Step 1: "Collect Business Information" — gather name, URL, services, service area, phone, hours
  - Step 2: "Build Business Profile" — create BusinessProfile from collected data
  - Step 3: "Determine Archetype" — auto-detect or manually select archetype
  - Step 4: "Activate Modules" — activate archetype-specific modules and watchers
  - Step 5: "Run Initial Audit" — execute full audit against the business
  - Step 6: "Generate First Proposals" — generate initial proposal bundle from audit findings
  - Step 7: "Present Review Bundle" — show audit results and proposals to operator for review
  - Step 8: "Operator Approves Initial Actions" — operator approves first batch of actions
- `advance_step(self, state: OnboardingState, step_input: Dict[str, Any]) -> OnboardingState`:
  - Process the input for the current step
  - Validate input against the step's input_schema
  - Advance to the next step
  - Return updated state
- `_process_step_1(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Validate: name (required), url (optional but recommended), services, phone
  - Store collected data
- `_process_step_2(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Build BusinessProfile from step 1 data
  - Fill in defaults for missing fields
- `_process_step_3(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Auto-detect archetype from business profile (using heuristics: service-based → local_service, product catalog → ecommerce, etc.)
  - Allow operator override
- `_process_step_4(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Activate modules based on archetype
  - Configure watchers based on archetype watcher pack
- `_process_step_5(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Stub: run initial audit (return placeholder result with structure)
  - Store audit results in state
- `_process_step_6(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Stub: generate proposals from audit findings (return placeholder bundle)
  - Store proposals in state
- `_process_step_7(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Compile review bundle: audit summary + top proposals + recommended first actions
  - This step outputs data for the operator to review
- `_process_step_8(self, state: OnboardingState, input_data: Dict) -> OnboardingState`:
  - Process operator's approvals/rejections of initial proposals
  - Mark onboarding as complete
  - Set completed_at timestamp
- `skip_step(self, state: OnboardingState) -> OnboardingState`:
  - Skip the current step if it's not required
  - Advance to next step
- `get_progress(self, state: OnboardingState) -> Dict[str, Any]`:
  - Return: {current_step, total_steps, completed_steps, pct_complete, estimated_remaining_minutes}

### File: `kai/flows/audit_review.py`

**Model: AuditReviewState**
- `business_id: str`
- `audit_result: Optional[Dict[str, Any]]`
- `review_bundle: Optional[Dict[str, Any]]`
- `operator_notes: List[str]`
- `drill_down_category: Optional[str]`

**Class: AuditReviewFlow**
- `__init__(self, workspace_dir: str)`
- `start(self, business_id: str, scope: str = "full") -> AuditReviewState`:
  - Run all relevant audits for the business
  - Compile into review bundle with executive summary
  - Return state with audit results and review bundle
- `get_executive_summary(self, state: AuditReviewState) -> Dict[str, Any]`:
  - Return: overall_score, category_scores, top_3_critical_findings, top_3_quick_wins, recommended_focus_area
- `drill_down(self, state: AuditReviewState, category: str) -> Dict[str, Any]`:
  - Show all findings for a specific category with details
  - Return: category_score, findings (sorted by severity), recommendation_count
- `generate_proposals_from_audit(self, state: AuditReviewState) -> Dict[str, Any]`:
  - Generate proposals from audit findings
  - Return: proposal_count, proposals_by_priority, estimated_total_effort

### File: `kai/flows/approval_flow.py`

**Model: ApprovalFlowState**
- `business_id: str`
- `queue: List[Dict[str, Any]]` — ordered list of actions to review
- `current_index: int`
- `decisions: List[Dict[str, Any]]` — list of {action_id, decision, reason, timestamp}
- `batch_mode: bool` — True if reviewing multiple actions at once

**Class: ApproveRejectReviseFlow**
- `__init__(self, workspace_dir: str)`
- `start(self, business_id: str, action_ids: Optional[List[str]] = None) -> ApprovalFlowState`:
  - Load pending actions (all or specified)
  - Sort by priority and risk tier
  - Return state with queue
- `show_current_action(self, state: ApprovalFlowState) -> Dict[str, Any]`:
  - Return full context for current action:
    - action details (title, description, channel, risk tier)
    - source finding (what prompted this)
    - impact estimate
    - compliance result (if checked)
    - content preview (if applicable)
    - similar past actions and their outcomes (from memory)
    - routing recommendation
- `approve(self, state: ApprovalFlowState, notes: Optional[str] = None) -> ApprovalFlowState`:
  - Record approval decision
  - Advance to next action in queue
- `reject(self, state: ApprovalFlowState, reason: str, category: str, revision_guidance: Optional[str] = None) -> ApprovalFlowState`:
  - Record rejection with full context
  - Trigger revision workflow if applicable
  - Advance to next action
- `defer(self, state: ApprovalFlowState) -> ApprovalFlowState`:
  - Skip this action for now (defer to later)
  - Advance to next action
- `batch_approve(self, state: ApprovalFlowState, action_ids: List[str]) -> ApprovalFlowState`:
  - Approve multiple actions at once
  - Only allowed for actions with risk_tier <= "low"
- `get_summary(self, state: ApprovalFlowState) -> Dict[str, Any]`:
  - Return: total_reviewed, approved_count, rejected_count, deferred_count, remaining

### File: `kai/flows/execution_monitor.py`

**Class: ExecutionMonitoringFlow**
- `__init__(self, workspace_dir: str)`
- `start(self, business_id: str) -> Dict[str, Any]`:
  - Return current execution status: active_executions, recent_completions, failures
- `get_active_executions(self, business_id: str) -> List[Dict[str, Any]]`:
  - Return list of currently executing actions with status and progress
- `get_recent_completions(self, business_id: str, days: int = 7) -> List[Dict[str, Any]]`:
  - Return completed actions with outcomes
- `get_failures(self, business_id: str) -> List[Dict[str, Any]]`:
  - Return failed actions with error details and suggested recovery
- `retry_action(self, action_id: str) -> Dict[str, Any]`:
  - Retry a failed action
- `get_upcoming(self, business_id: str) -> List[Dict[str, Any]]`:
  - Return scheduled/upcoming actions with execution dates

### File: `kai/flows/learning_review.py`

**Class: LearningReviewFlow**
- `__init__(self, workspace_dir: str)`
- `start(self, business_id: str) -> Dict[str, Any]`:
  - Load recent learnings from memory system
  - Separate into confirmed vs. pending confirmation
  - Return: recent_learnings, pending_confirmations, stale_memories
- `get_pending_confirmations(self, business_id: str) -> List[Dict[str, Any]]`:
  - Return learnings awaiting operator confirmation
- `confirm_learning(self, learning_id: str, confirmed: bool, notes: Optional[str] = None) -> Dict[str, Any]`:
  - Confirm or dismiss a learning
  - Return confirmation result
- `review_stale_memories(self, business_id: str) -> List[Dict[str, Any]]`:
  - Return memories past their staleness date for re-validation
- `get_learning_summary(self, business_id: str) -> Dict[str, Any]`:
  - Return: total_learnings by category, strongest insights, newest learnings, recommended review cadence

## Output Files

- `kai/flows/__init__.py`
- `kai/flows/onboarding.py`
- `kai/flows/audit_review.py`
- `kai/flows/approval_flow.py`
- `kai/flows/execution_monitor.py`
- `kai/flows/learning_review.py`

## Acceptance Criteria

- All files parse as valid Python
- OnboardingFlow has all 8 steps with clear input schemas and outputs
- Archetype auto-detection in step 3 uses reasonable heuristics
- AuditReviewFlow includes executive summary and drill-down capability
- ApproveRejectReviseFlow supports individual review, batch approval (low-risk only), and defer
- show_current_action includes memory-based context (similar past actions and outcomes)
- ExecutionMonitoringFlow covers active, completed, failed, and upcoming actions
- LearningReviewFlow surfaces both pending confirmations and stale memories
- All flows maintain state objects that can be persisted and resumed
- batch_approve correctly enforces risk tier restrictions
- No external dependencies

## Reference Materials

- `kai/operator/local_surface.py` (Task 077) — command methods that flows orchestrate
- `kai/operator/remote_surface.py` (Task 078) — API response models
- `kai/runtime/audit.py` — audit engine
- `kai/runtime/actions.py` — action lifecycle
- `kai/compliance/approval_routing.py` (Task 064) — approval routing
- `kai/compliance/revision.py` (Task 065) — revision workflow
- `kai/memory/retrieval.py` (Task 075) — memory retrieval for context
- `kai/runtime/business_profile.py` — BusinessProfile for onboarding
- `kai/runtime/models.py` — SerializableModel pattern
