# Task 076: Build anti-pattern memory and archetype default improvement

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 13. Memory and Learning Loop
**Priority:** P3
**Depends on:** 074
**Estimated complexity:** Medium

## Context

Learning what works is valuable; learning what does NOT work is equally valuable. The anti-pattern memory prevents the system from repeatedly proposing actions that fail, content that gets rejected, or campaigns that underperform. Beyond individual business learning, the archetype default improvement system aggregates anonymized learnings across businesses to improve the baseline recommendations for each archetype. If 80% of local-service businesses eventually set up review request sequences, that should become a default recommendation rather than a finding to discover each time.

## Scope

Create `kai/memory/anti_patterns.py` containing the AntiPatternMemory for tracking what doesn't work, the anti-pattern matching logic that checks new proposals against past failures, and the ArchetypeDefaultImprovement system that suggests updates to archetype defaults based on aggregate patterns.

## Detailed Requirements

### File: `kai/memory/anti_patterns.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: AntiPatternType**
- `rejected_content` — content rejected by operator
- `failed_campaign` — campaign that underperformed metrics
- `low_quality_creative` — content that scored poorly on quality gates
- `compliance_violation` — content that violated compliance rules
- `ignored_proposal` — proposal that was consistently skipped/deferred
- `negative_outcome` — action that produced worse metrics than before

**Model: AntiPatternEntry**
- `id: str` — format `ap_{uuid_hex[:12]}`
- `business_id: str`
- `anti_pattern_type: str` — AntiPatternType enum value
- `description: str` — what went wrong (e.g., "Aggressive discount CTA rejected — operator prefers value framing")
- `action_type: str` — what type of action this was
- `channel: Optional[str]` — which channel
- `content_type: Optional[str]` — which content type
- `pattern_signature: str` — a generalizable description of the pattern (e.g., "discount_heavy_cta", "casual_email_tone", "stock_photo_hero")
- `failure_reason: str` — why it failed: "operator_rejected", "low_performance", "compliance_violation", "quality_gate_failure", "consistently_ignored"
- `specific_feedback: Optional[str]` — operator's rejection reason or specific issue
- `occurrence_count: int` — how many times this pattern has failed
- `first_seen: str` — ISO timestamp
- `last_seen: str` — ISO timestamp
- `risk_if_repeated: str` — "low", "medium", "high" — what happens if we do this again
- `alternative_approach: Optional[str]` — what to do instead
- `metadata: Dict[str, Any]`

**Model: AntiPatternMemory**
- `business_id: str`
- `patterns: List[AntiPatternEntry]`
- `get_patterns_for_action_type(self, action_type: str) -> List[AntiPatternEntry]`
- `get_patterns_for_channel(self, channel: str) -> List[AntiPatternEntry]`
- `get_high_risk_patterns(self) -> List[AntiPatternEntry]` — risk_if_repeated == "high"
- `get_frequent_patterns(self, min_occurrences: int = 3) -> List[AntiPatternEntry]` — patterns that failed multiple times
- Storage format: `workspace/{business_id}/memory/anti_patterns.yaml`

**Class: AntiPatternMatcher**
- `__init__(self, memory: AntiPatternMemory)`
- `check_proposal(self, action_type: str, channel: Optional[str], content_type: Optional[str], content_features: Dict[str, Any]) -> List[Dict[str, Any]]`:
  - Check a proposed action against known anti-patterns
  - `content_features` is a dict describing the proposed content: {tone, cta_type, offer_type, headline_style, visual_style, etc.}
  - Return list of matches: [{anti_pattern_id, match_score (0-1), description, risk_level, alternative}]
  - Match logic:
    - Exact match on action_type + channel + pattern_signature = 1.0 match
    - Partial match (same action_type, similar pattern_signature) = 0.5-0.8
    - Weak match (same channel, different action_type but similar features) = 0.2-0.4
- `record_anti_pattern(self, action_id: str, business_id: str, anti_pattern_type: str, action_type: str, channel: Optional[str], content_type: Optional[str], failure_reason: str, specific_feedback: Optional[str] = None) -> AntiPatternEntry`:
  - Check if a similar pattern already exists (same pattern_signature)
  - If exists: increment occurrence_count, update last_seen
  - If new: create new AntiPatternEntry
  - Auto-generate pattern_signature from action attributes
  - Auto-determine risk_if_repeated based on anti_pattern_type and occurrence_count
  - Return the entry
- `_generate_pattern_signature(self, action_type: str, channel: Optional[str], content_type: Optional[str], failure_reason: str) -> str`:
  - Create a generalizable signature like "social_post_instagram_aggressive_cta" or "email_marketing_casual_tone"
  - Used for matching future proposals against past failures
- `_calculate_match_score(self, pattern: AntiPatternEntry, action_type: str, channel: Optional[str], content_features: Dict[str, Any]) -> float`:
  - Scoring based on: exact field matches, similarity of pattern_signature, related failure types
  - Return 0.0-1.0

**Model: ArchetypeAggregate**
- `archetype: str`
- `total_businesses_observed: int`
- `action_success_rates: Dict[str, Dict[str, float]]` — {action_type: {channel: success_rate}}
- `common_first_actions: List[Dict[str, Any]]` — actions that most businesses end up doing first: [{action_type, channel, pct_of_businesses}]
- `common_anti_patterns: List[Dict[str, Any]]` — anti-patterns seen across multiple businesses: [{pattern_signature, pct_of_businesses, description}]
- `default_improvement_suggestions: List[str]` — suggested changes to archetype defaults
- `last_updated: str`

**Model: DefaultImprovementSuggestion**
- `id: str` — format `imp_{uuid_hex[:8]}`
- `archetype: str`
- `suggestion_type: str` — "add_default_action", "remove_default_action", "change_priority", "add_watcher", "adjust_threshold"
- `description: str` — what to change and why
- `evidence: str` — data supporting the suggestion (e.g., "85% of local-service businesses manually add review request sequences within first month")
- `impact_estimate: str` — "high", "medium", "low"
- `confidence: str` — based on sample size and consistency of signal
- `approved: bool` — whether this suggestion has been reviewed and approved
- `applied: bool` — whether this suggestion has been applied to archetype defaults

**Class: ArchetypeDefaultImprovement**
- `__init__(self, aggregate_dir: str)` — directory for aggregate data
- `analyze_patterns(self, archetype: str, business_learnings: List[Dict[str, Any]]) -> ArchetypeAggregate`:
  - Aggregate learnings across multiple businesses for an archetype
  - Calculate action success rates by type and channel
  - Identify common first actions (what most businesses end up doing)
  - Identify common anti-patterns across businesses
  - Return the aggregate
- `generate_improvement_suggestions(self, aggregate: ArchetypeAggregate) -> List[DefaultImprovementSuggestion]`:
  - Rules for generating suggestions:
    - If > 80% of businesses eventually do an action → suggest making it a default
    - If a finding is always ignored (< 10% action rate across businesses) → suggest lowering its priority
    - If a channel consistently underperforms for this archetype (< 30% success rate) → suggest adjusting channel mix
    - If a watcher finding consistently leads to action (> 70% action rate) → suggest making it auto-eligible
    - If an anti-pattern appears in > 50% of businesses → suggest adding it to archetype default constraints
  - Return list of suggestions with evidence and confidence
- `apply_suggestion(self, suggestion_id: str) -> bool`:
  - Mark a suggestion as applied
  - The actual application to archetype config is handled by the archetype system (Tasks 006-009)
  - Return True if found and marked
- `_calculate_action_adoption_rate(self, action_type: str, business_count: int, businesses_using: int) -> float`:
  - Simple adoption rate calculation
- `_identify_common_sequences(self, business_learnings: List[Dict]) -> List[Dict]`:
  - Identify common action sequences (e.g., audit → GBP optimization → review requests → ad campaign)
  - Return ordered sequences with frequency count

## Output Files

- `kai/memory/anti_patterns.py`

## Acceptance Criteria

- File parses as valid Python
- AntiPatternMatcher.check_proposal() returns meaningful match scores with clear scoring logic
- Pattern signature generation creates useful, matchable signatures (not just random strings)
- record_anti_pattern correctly increments occurrence count for existing patterns
- ArchetypeDefaultImprovement implements all five suggestion rules with the specified thresholds
- Improvement suggestions include evidence and confidence levels
- Common anti-patterns are identified across businesses (not just within one business)
- Action adoption rate calculation is correct
- High-risk patterns (occurrence_count >= 3 or compliance violations) correctly escalate risk_if_repeated
- All models use SerializableModel mixin
- Storage uses YAML in the workspace directory pattern

## Reference Materials

- `kai/memory/schemas.py` (Task 074) — memory layer schemas for cross-referencing
- `kai/memory/writeback.py` (Task 073) — Learning model, how anti-patterns are captured
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/runtime/audit.py` — AuditFinding patterns (anti-patterns are the inverse)
