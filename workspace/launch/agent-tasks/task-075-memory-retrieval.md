# Task 075: Build memory retrieval for proposals and creative generation

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 13. Memory and Learning Loop
**Priority:** P2
**Depends on:** 074
**Estimated complexity:** Medium

## Context

Memory is only valuable if it is surfaced at the right time. The memory retrieval system is the read path that makes accumulated learnings available to every decision-making subsystem in Kai. When the proposal engine generates actions, it should know what worked before. When the copy engine writes a headline, it should know which headline styles this operator prefers. When the approval router estimates risk, it should know the operator's past approval patterns. This module provides context-aware retrieval that pulls the most relevant learnings based on what the system is currently doing.

## Scope

Create `kai/memory/retrieval.py` containing the MemoryRetriever class with context-specific retrieval methods, relevance ranking, staleness handling, and integration points for the four main consumers: proposal engine, creative engine, approval router, and watcher system.

## Detailed Requirements

### File: `kai/memory/retrieval.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Model: RetrievalContext**
- `context_type: str` — "proposal", "creative", "channel_selection", "approval", "watcher", "audit"
- `business_id: str`
- `channel: Optional[str]` — target channel for channel-specific retrieval
- `content_type: Optional[str]` — target content type
- `action_type: Optional[str]` — type of action being planned
- `audience_segment: Optional[str]` — target audience
- `tags: List[str]` — additional search tags
- `max_results: int` — maximum learnings to return (default 10)
- `min_confidence: str` — minimum confidence level to include (default "inferred")
- `include_stale: bool` — whether to include stale entries (default False)

**Model: RetrievedMemory**
- `source_layer: str` — which memory layer this came from
- `entry_id: str` — id of the memory entry
- `relevance_score: float` — 0.0-1.0, how relevant this is to the current context
- `content: Dict[str, Any]` — the actual memory content (varies by layer)
- `summary: str` — one-sentence summary for quick consumption
- `confidence: str` — confidence level
- `age_days: int` — how many days old this memory is
- `is_stale: bool` — whether this entry is past its staleness date
- `usage_hint: str` — how to use this memory in the current context (e.g., "Prefer this headline style", "Avoid this CTA format")

**Model: MemoryBrief**
- `business_id: str`
- `context: RetrievalContext`
- `retrieved_at: str` — ISO timestamp
- `total_entries_searched: int`
- `entries_returned: int`
- `memories: List[RetrievedMemory]`
- `key_constraints: List[str]` — top constraints to respect (from brand_constraints layer)
- `winning_patterns: List[str]` — patterns that have performed well (from channel/creative learnings)
- `things_to_avoid: List[str]` — patterns that have performed poorly or been rejected
- `available_proof_assets: List[str]` — proof assets available for this content type

**Class: MemoryRetriever**
- `__init__(self, base_dir: str)` — base directory for memory files
- `retrieve(self, context: RetrievalContext) -> MemoryBrief`:
  - Main entry point: load relevant memory layers, filter by context, rank by relevance, assemble MemoryBrief
  - Dispatch to context-specific retrieval method
  - Always include brand constraints regardless of context type
- `retrieve_for_proposal(self, business_id: str, action_type: str, channel: str) -> MemoryBrief`:
  - Context: generating a proposal for a specific action type and channel
  - Retrieve:
    - Past actions of this type that performed well → "do this again"
    - Past actions of this type that performed poorly → "avoid this"
    - Operator approval patterns for this action type → predict approval likelihood
    - Channel learnings for target channel → best practices
    - Relevant business facts → ensure proposal uses current information
  - Key output: winning_patterns, things_to_avoid, key_constraints
- `retrieve_for_creative(self, business_id: str, content_type: str, channel: str, audience: Optional[str] = None) -> MemoryBrief`:
  - Context: generating creative content
  - Retrieve:
    - Brand voice/tone preferences → style guidance
    - Best-performing creative for this content_type + channel → winning patterns
    - Approved proof assets for this content type → available social proof
    - Audience insights for target audience → messaging guidance
    - Offer learnings → what offers to consider
  - Key output: brand constraints, winning creative patterns, available proof assets
- `retrieve_for_channel_selection(self, business_id: str) -> MemoryBrief`:
  - Context: deciding which channels to use for a campaign
  - Retrieve:
    - Channel performance data → which channels deliver ROI
    - Audience channel preferences → where the audience engages
    - Budget efficiency by channel → best spend allocation
  - Key output: ranked channel recommendations with supporting data
- `retrieve_for_approval(self, business_id: str, action_type: str, risk_tier: str) -> MemoryBrief`:
  - Context: predicting operator approval behavior
  - Retrieve:
    - Past approval/rejection patterns for this action_type + risk_tier
    - Operator preferences that affect approval (e.g., always rejects aggressive tone)
    - Compliance constraints that were violated before
  - Key output: predicted approval likelihood, likely objections
- `retrieve_for_watcher(self, business_id: str, watcher_name: str) -> MemoryBrief`:
  - Context: reducing watcher false positives
  - Retrieve:
    - Past watcher findings that were dismissed/ignored → suppress similar
    - Past watcher findings that led to action → prioritize similar
    - Business facts that affect watcher thresholds
  - Key output: findings to suppress, findings to prioritize
- `_load_memory_layers(self, business_id: str) -> Dict[str, Any]`:
  - Load all memory layers for a business
  - Cache loaded layers for the duration of the retrieval session (avoid re-reading files)
  - Return dict of {layer_name: memory_layer_object}
- `_rank_by_relevance(self, entries: List[RetrievedMemory], context: RetrievalContext) -> List[RetrievedMemory]`:
  - Rank retrieved entries by relevance to the current context
  - Ranking factors:
    - Confidence level (higher = more relevant): confirmed=1.0, observed=0.7, inferred=0.4, speculative=0.2
    - Recency (newer = more relevant): score = max(0.1, 1.0 - (age_days / 365))
    - Context match (matching channel/content_type/tags = more relevant): +0.3 per match
    - Strength (for brand constraints): strength 5 = +0.5, strength 1 = +0.1
  - Final relevance_score = weighted average of factors
  - Sort by relevance_score descending
- `_filter_by_staleness(self, entries: List[RetrievedMemory], include_stale: bool) -> List[RetrievedMemory]`:
  - If include_stale is False, exclude stale entries
  - If include_stale is True, include them but set is_stale flag
- `_filter_by_confidence(self, entries: List[RetrievedMemory], min_confidence: str) -> List[RetrievedMemory]`:
  - Filter entries below minimum confidence level
  - Confidence hierarchy: confirmed > observed > inferred > speculative
- `_generate_usage_hints(self, entry: RetrievedMemory, context: RetrievalContext) -> str`:
  - Generate a human-readable hint for how to use this memory
  - E.g., for brand_constraint in creative context: "Apply formal tone — operator rejected casual email copy on [date]"
  - E.g., for channel_learning in proposal context: "Consider Tuesday posting — 2.3x engagement observed"

## Output Files

- `kai/memory/retrieval.py`

## Acceptance Criteria

- File parses as valid Python
- All five context-specific retrieval methods are implemented with clear retrieval logic
- `_rank_by_relevance` implements the exact ranking formula with confidence, recency, and context-match factors
- Staleness filtering correctly excludes stale entries when include_stale=False
- Confidence filtering correctly applies the hierarchy
- MemoryBrief includes key_constraints, winning_patterns, things_to_avoid, and available_proof_assets as pre-compiled lists
- Usage hints are context-aware and specific (not generic)
- Memory layer loading is cached within a retrieval session
- `retrieve_for_creative` specifically includes proof assets for social proof
- `retrieve_for_watcher` supports false-positive reduction via dismissed finding history
- All models use SerializableModel mixin
- No external dependencies

## Reference Materials

- `kai/memory/schemas.py` (Task 074) — all six memory layer schemas and their query methods
- `kai/memory/writeback.py` (Task 073) — Learning model, LearningCategory, LearningConfidence
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/runtime/audit.py` — AuditCategory (for context matching)
