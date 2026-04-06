# Task 025: Build proposal ranking, dedup, and dependency tracking

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 4. Proposal and Planning
**Priority:** P2
**Depends on:** 022
**Estimated complexity:** Medium

## Context

When the action mapper generates ProposedActions from multiple audit findings, the raw list often contains duplicates (e.g., both the conversion audit and the trust audit recommend "add phone number to hero") and lacks dependency ordering (e.g., "set up tracking" must happen before "launch campaign"). The ranking system applies a multi-factor score to prioritize actions, the dedup system detects and merges redundant actions, and the dependency tracker ensures actions execute in a valid order. Together, these produce a clean, ordered, actionable list from raw mapper output.

## Scope

Build `kai/proposals/ranking.py` containing functions for multi-factor ranking, deduplication, and dependency graph resolution. This module takes a raw list of ProposedActions and returns a clean, ranked, dependency-ordered list.

## Detailed Requirements

### File: `kai/proposals/ranking.py`

**Constants:**

```python
# Ranking weight factors (must sum to 1.0)
WEIGHT_SEVERITY = 0.30
WEIGHT_IMPACT = 0.25
WEIGHT_EFFORT_INVERSE = 0.20
WEIGHT_STAGE_FIT = 0.15
WEIGHT_BUDGET_FIT = 0.10

# Severity scores (0-100)
SEVERITY_SCORES = {
    "critical": 100,
    "high": 75,
    "medium": 50,
    "low": 25,
}

# Business stage fit multipliers
STAGE_FIT = {
    "pre-launch": {"website_update": 1.0, "content_creation": 0.8, "seo_fix": 0.5, "ad_campaign": 0.3, "email_sequence": 0.6, "review_request": 0.2, "social_post": 0.7, "analytics_fix": 0.9, "gbp_update": 0.4, "kaicalls_setup": 0.7},
    "early-pmf": {"website_update": 0.9, "content_creation": 0.8, "seo_fix": 0.7, "ad_campaign": 0.5, "email_sequence": 0.7, "review_request": 0.8, "social_post": 0.6, "analytics_fix": 0.8, "gbp_update": 0.9, "kaicalls_setup": 0.9},
    "growth": {"website_update": 0.7, "content_creation": 0.8, "seo_fix": 0.8, "ad_campaign": 0.9, "email_sequence": 0.9, "review_request": 0.7, "social_post": 0.7, "analytics_fix": 0.6, "gbp_update": 0.7, "kaicalls_setup": 0.8},
    "scale": {"website_update": 0.5, "content_creation": 0.7, "seo_fix": 0.6, "ad_campaign": 1.0, "email_sequence": 0.9, "review_request": 0.5, "social_post": 0.8, "analytics_fix": 0.5, "gbp_update": 0.5, "kaicalls_setup": 0.6},
    "mature": {"website_update": 0.4, "content_creation": 0.6, "seo_fix": 0.5, "ad_campaign": 0.8, "email_sequence": 0.8, "review_request": 0.4, "social_post": 0.7, "analytics_fix": 0.4, "gbp_update": 0.4, "kaicalls_setup": 0.5},
}
```

**Function: `rank_actions(actions: List[Dict[str, Any]], business_stage: str = "early-pmf", monthly_budget: Optional[float] = None) -> List[Dict[str, Any]]`**
- For each action, compute a composite score using these factors:
  1. **Severity factor** (0-100): Look up the source finding's severity in SEVERITY_SCORES. If severity is not available, use the action's priority_score as proxy.
  2. **Impact factor** (0-100): Derive from action_type importance. ad_campaign and email_sequence score higher (more direct revenue impact) than analytics_fix (indirect). Define an IMPACT_SCORES dict mapping action_type to base impact scores.
  3. **Effort inverse factor** (0-100): `100 - min(estimated_effort_hours * 10, 100)`. Smaller effort = higher score. Quick wins rank higher.
  4. **Stage fit factor** (0-100): `STAGE_FIT[business_stage].get(action_type, 0.5) * 100`. How appropriate is this action for the business's current stage.
  5. **Budget fit factor** (0-100): If monthly_budget is None, score 50 (neutral). If action cost <= 10% of monthly_budget, score 90. If cost <= 25%, score 70. If cost <= 50%, score 40. If cost > 50%, score 10.
- Composite score = `WEIGHT_SEVERITY * severity + WEIGHT_IMPACT * impact + WEIGHT_EFFORT_INVERSE * effort_inv + WEIGHT_STAGE_FIT * stage_fit + WEIGHT_BUDGET_FIT * budget_fit`
- Update each action's `priority_score` with the composite score
- Sort actions by composite score descending
- Return the sorted list

**Function: `deduplicate_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]`**
- Detect duplicate or near-duplicate actions using these signals:
  1. **Exact match**: same action_type + same channel + same page/target in suggested_payload
  2. **Title similarity**: normalized titles (lowercase, stripped of specifics like page names) that match > 80%
  3. **Payload overlap**: same action_type and > 70% key overlap in suggested_payload
- When duplicates are detected:
  - Keep the action with the higher priority_score
  - Merge the `tags` lists (union)
  - Merge the `source_finding_id` into a `merged_finding_ids` list in metadata
  - Add a `deduplicated: true` flag in metadata
  - Preserve the richer description (longer of the two)
- Return deduplicated list

**Helper: `_normalize_title(title: str) -> str`**
- Lowercase, remove page-specific references (e.g., "{page}" becomes ""), strip extra whitespace
- Used for title similarity comparison

**Helper: `_title_similarity(title_a: str, title_b: str) -> float`**
- Compute similarity ratio between two normalized titles
- Use simple token overlap: `len(intersection) / len(union)` of word sets
- Return float 0.0 to 1.0

**Function: `resolve_dependencies(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]`**
- Build a dependency graph from each action's `depends_on` list
- Add implicit dependencies based on action type relationships:
  - `analytics_fix` (tracking setup) should come before `ad_campaign` (needs tracking to measure)
  - `content_creation` (landing page) should come before `ad_campaign` that references it
  - `website_update` (add form) should come before `email_sequence` (that triggers from form)
  - `seo_fix` (schema markup) can run independently
  - `review_request` should come after `reputation_action` (respond to existing reviews first)
  - `kaicalls_setup` should come before `add_click_to_call` if both present
- Perform topological sort on the dependency graph
- If cycles are detected, log a warning and break the cycle by removing the lowest-priority edge
- Return actions in dependency-valid order, preserving priority_score order within each dependency level

**Helper: `_build_dependency_graph(actions: List[Dict[str, Any]]) -> Dict[str, List[str]]`**
- Build adjacency list from explicit `depends_on` fields
- Add implicit edges based on action type rules above
- Return dict mapping action_id to list of dependency action_ids

**Helper: `_topological_sort(graph: Dict[str, List[str]], actions: List[Dict[str, Any]]) -> List[str]`**
- Kahn's algorithm for topological sort
- Within each level (actions with same number of unresolved dependencies), sort by priority_score descending
- Handle cycles by detecting them and removing the lowest-priority edge
- Return list of action_ids in valid execution order

**Function: `process_actions(actions: List[Dict[str, Any]], business_stage: str = "early-pmf", monthly_budget: Optional[float] = None) -> List[Dict[str, Any]]`**
- High-level pipeline: rank → deduplicate → resolve dependencies
- This is the main entry point for consumers
- Returns a clean, ranked, deduped, dependency-ordered list of actions

## Output Files

- `kai/proposals/ranking.py`

## Acceptance Criteria

- [ ] `ranking.py` contains rank_actions, deduplicate_actions, resolve_dependencies, and process_actions
- [ ] Multi-factor ranking uses all 5 weighted factors with correct math
- [ ] Weight factors sum to 1.0
- [ ] STAGE_FIT dict covers all 5 business stages and all action types
- [ ] Deduplication handles exact matches, title similarity, and payload overlap
- [ ] Duplicate merging preserves the higher-scored action and merges metadata
- [ ] Dependency resolution includes both explicit depends_on and implicit type-based rules
- [ ] Topological sort handles cycles gracefully (breaks them, does not crash)
- [ ] process_actions chains rank → dedup → dependency resolution in correct order
- [ ] All functions accept and return dicts (not requiring model instances)
- [ ] No side effects — all functions are pure
- [ ] Constants are defined at module level with clear names

## Reference Materials

- `kai/models/proposal.py` (created by Task 022) — ProposedAction schema with priority_score, risk_tier, depends_on, estimated_effort_hours, estimated_cost fields
- `kai/models/business_profile.py` (created by Task 001) — BusinessClassification.stage for business stage
- `kai/proposals/action_mapper.py` (created by Task 023) — produces the raw action list that this module processes
- `kai/runtime/audit.py` — FindingSeverity and FindingPriority enums for severity scoring
