# Task 073: Build memory writeback system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 13. Memory and Learning Loop
**Priority:** P1
**Depends on:** 022
**Estimated complexity:** Large

## Context

A marketing system that cannot learn from its own actions is no better than a one-time consulting engagement. The memory writeback system is what transforms Kai from a "generate proposals" tool into a continuously-improving marketing partner. Every time an action is approved (or rejected), executed, measured, or receives operator feedback, the system captures structured learnings and writes them to persistent memory. Over time, these learnings accumulate into a rich understanding of what works for this specific business — which headlines convert, which offers resonate, which channels deliver ROI, which creative styles the operator prefers. This is the write path; the retrieval system (Task 075) is the read path.

## Scope

Create `kai/memory/writeback.py` containing the MemoryWriteback system, writeback trigger handlers, structured learning objects, and the logic for determining which learnings auto-write vs. require confirmation.

## Detailed Requirements

### File: `kai/memory/__init__.py`
- Module docstring explaining the memory/learning system
- Export key classes

### File: `kai/memory/writeback.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`. For file I/O, follow patterns from `kai/runtime/actions.py` (atomic writes, JSONL storage).

**Enum: LearningCategory**
- `brand_preference` — learned brand voice, tone, style preferences
- `creative_performance` — which creative elements perform well/poorly
- `channel_insight` — channel-specific learnings (best times, best formats)
- `audience_insight` — what resonates with which audience segments
- `offer_performance` — which offers/pricing/promotions convert
- `compliance_constraint` — compliance rules learned from violations
- `operator_preference` — operator approval/rejection patterns
- `business_fact` — confirmed facts about the business
- `execution_record` — record of what was executed (not a learning per se, but a memory)

**Enum: LearningConfidence**
- `confirmed` — directly confirmed by operator or multiple data points
- `observed` — observed from data but not explicitly confirmed
- `inferred` — inferred from patterns but needs more evidence
- `speculative` — weak signal, needs validation

**Enum: WritebackTrigger**
- `action_approved` — an action was approved by operator
- `action_rejected` — an action was rejected with feedback
- `action_executed` — an action was deployed/executed
- `results_available` — performance data is now available for a past action
- `operator_feedback` — explicit feedback from operator (not approval/rejection)
- `compliance_violation` — a compliance check failed
- `creative_scored` — quality gates scored content
- `watcher_finding` — a watcher found something noteworthy

**Model: Learning**
- `id: str` — format `learn_{uuid_hex[:12]}`
- `business_id: str`
- `category: str` — LearningCategory enum value
- `trigger: str` — WritebackTrigger enum value
- `title: str` — short description (e.g., "Operator prefers formal tone in email subject lines")
- `finding: str` — detailed description of what was learned
- `confidence: str` — LearningConfidence enum value
- `evidence: Dict[str, Any]` — supporting data: {source_action_id, metric_values, approval_context, etc.}
- `source_action_id: Optional[str]` — the action that generated this learning
- `source_type: str` — "approval", "rejection", "performance_data", "operator_feedback", "compliance", "quality_gate"
- `tags: List[str]` — searchable tags (e.g., ["email", "subject_line", "formal_tone"])
- `channel: Optional[str]` — which marketing channel this applies to
- `content_type: Optional[str]` — which content type this applies to
- `created_at: str` — ISO timestamp
- `expires_at: Optional[str]` — when this learning should be re-validated (None = no expiry)
- `superseded_by: Optional[str]` — if a newer learning replaces this one
- `requires_confirmation: bool` — whether operator must confirm before this is treated as established

**Model: WritebackEvent**
- `trigger: str` — WritebackTrigger enum value
- `action_id: Optional[str]`
- `business_id: str`
- `event_data: Dict[str, Any]` — trigger-specific data
- `timestamp: str`

**Class: MemoryWriteback**
- `__init__(self, memory_dir: str)` — base directory for memory storage (typically `workspace/{business_id}/memory/`)
- `_pending_confirmations: List[Learning]` — learnings awaiting operator confirmation
- `process_event(self, event: WritebackEvent) -> List[Learning]`:
  - Dispatch to the appropriate handler based on event.trigger
  - Return list of Learning objects generated
  - Persist auto-write learnings immediately
  - Queue confirmation-required learnings in _pending_confirmations
- `_handle_action_approved(self, event: WritebackEvent) -> List[Learning]`:
  - Extract brand preference learnings from what was approved:
    - If the action included specific creative choices (headline style, tone, CTA format), record as brand_preference
    - If the action targeted a specific channel/format, record the approval as a signal
  - Confidence: "observed" (single approval is a signal, not confirmation)
  - Auto-write: True (execution records don't need confirmation)
  - Example learning: "Operator approved headline with urgency angle for Google Ads" → brand_preference
- `_handle_action_rejected(self, event: WritebackEvent) -> List[Learning]`:
  - Extract constraint learnings from rejection reason and category:
    - If rejection_category is "brand_voice" → record tone/style constraint
    - If rejection_category is "compliance" → record compliance constraint
    - If rejection_category is "strategy" → record strategic direction
  - Include the specific_issues from the Rejection object as evidence
  - Confidence: "confirmed" (operator explicitly said this is wrong)
  - requires_confirmation: False (rejections are clear signals)
  - Example: "Operator rejected casual emoji usage in LinkedIn posts" → brand_preference + operator_preference
- `_handle_action_executed(self, event: WritebackEvent) -> List[Learning]`:
  - Record the execution as an execution_record learning
  - Include: what was executed, when, on which channel, content summary
  - Auto-write: True
  - Confidence: "confirmed"
- `_handle_results_available(self, event: WritebackEvent) -> List[Learning]`:
  - This is the most valuable trigger — connecting actions to outcomes
  - Extract performance learnings:
    - If action performed well (above target/benchmark): record winning pattern
    - If action performed poorly (below target): record losing pattern
    - Channel-specific learnings: best posting times, best ad formats, best audience segments
    - Offer learnings: which offers converted, at what rate
  - Confidence: depends on ActionOutcomeLinkage confidence_level (from Task 058)
  - requires_confirmation: True for high-impact learnings (e.g., "this channel doesn't work for your business")
  - Example: "Blog posts published on Tuesdays get 2.3x more traffic than other days" → channel_insight
- `_handle_operator_feedback(self, event: WritebackEvent) -> List[Learning]`:
  - Direct operator input (e.g., "I prefer shorter email subject lines")
  - Confidence: "confirmed"
  - Auto-write: True (operator said it directly)
  - requires_confirmation: False
- `_handle_compliance_violation(self, event: WritebackEvent) -> List[Learning]`:
  - Record the violation as a compliance_constraint learning
  - Include: rule_id, violation description, how to avoid in future
  - Confidence: "confirmed"
  - Auto-write: True (compliance is non-negotiable)
- `_handle_creative_scored(self, event: WritebackEvent) -> List[Learning]`:
  - Record quality gate results as creative_performance learnings
  - Track which content patterns score highest on Four U's
  - Confidence: "observed"
- `confirm_learning(self, learning_id: str, confirmed: bool, operator_notes: Optional[str] = None) -> bool`:
  - Operator confirms or dismisses a pending learning
  - If confirmed: persist to memory with confidence="confirmed"
  - If dismissed: remove from pending, optionally record the dismissal as its own learning
  - Return True if found and processed
- `get_pending_confirmations(self, business_id: str) -> List[Learning]`:
  - Return all learnings awaiting operator confirmation
- `_persist_learning(self, learning: Learning)`:
  - Write learning to JSONL file: `{memory_dir}/{category}.jsonl`
  - Use atomic write pattern from actions.py
  - File organization: one JSONL file per learning category
- `_check_for_superseded(self, new_learning: Learning) -> Optional[str]`:
  - Check if this learning contradicts or updates an existing learning
  - If yes, set superseded_by on the old learning and return its id
  - E.g., if old learning says "operator prefers casual tone" and new rejection says "too casual", supersede the old one

## Output Files

- `kai/memory/__init__.py`
- `kai/memory/writeback.py`

## Acceptance Criteria

- All files parse as valid Python
- All eight trigger handlers are implemented with realistic learning extraction logic
- Each handler produces appropriately categorized learnings (not just generic "something happened")
- Confidence levels are correctly assigned: rejections → "confirmed", approvals → "observed", results → depends on attribution confidence
- `requires_confirmation` is True for high-impact learnings and False for clear signals (rejections, operator feedback)
- `_persist_learning` uses JSONL format with one file per learning category
- `_check_for_superseded` implements basic contradiction detection
- `confirm_learning` correctly handles both confirmation and dismissal
- Learning objects have searchable tags for retrieval (Task 075)
- File I/O follows the atomic write patterns from `kai/runtime/actions.py`
- No external dependencies beyond stdlib

## Reference Materials

- `kai/runtime/actions.py` — file I/O patterns, atomic writes, JSON helpers
- `kai/runtime/store.py` — workspace storage conventions
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/compliance/revision.py` (Task 065) — Rejection model (used in _handle_action_rejected)
- `kai/analytics/attribution.py` (Task 058) — ActionOutcomeLinkage (used in _handle_results_available)
- `kai/compliance/audit_trail.py` (Task 066) — audit entry patterns
