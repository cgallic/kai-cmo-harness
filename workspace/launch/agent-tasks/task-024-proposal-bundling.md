# Task 024: Build proposal bundling system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 4. Proposal and Planning
**Priority:** P2
**Depends on:** 022
**Estimated complexity:** Medium

## Context

An audit of a typical local service business produces 15-40 ProposedActions. Presenting all of them as a flat list overwhelms the operator. The bundling system groups related actions into coherent, time-boxed plans that an operator can understand and approve as a unit. A 7-day bundle says "here are the quick wins you can do this week." A 30-day plan lays out a month of improvement with weekly milestones. A campaign pack groups related actions around a single marketing initiative. A monthly operating plan combines recurring maintenance with strategic improvements.

This is the layer that turns a raw action list into something that feels like a marketing strategy rather than a task dump.

## Scope

Build `kai/proposals/bundler.py` with functions that take a list of ProposedAction objects (as dicts or model instances) and produce ProposalBundle objects organized by bundle type. Each bundle type has specific selection criteria, ordering rules, and structural requirements.

## Detailed Requirements

### File: `kai/proposals/bundler.py`

**Constants:**

```python
MAX_7DAY_ACTIONS = 7        # Maximum actions in a quick-wins bundle
MAX_7DAY_EFFORT_HOURS = 10  # Total effort cap for 7-day bundle
MAX_30DAY_ACTIONS = 25      # Maximum actions in a 30-day plan
CAMPAIGN_MIN_ACTIONS = 3    # Minimum actions to form a campaign pack
CAMPAIGN_MAX_ACTIONS = 12   # Maximum actions in a campaign pack
```

**Function: `bundle_7day_quick_wins(actions: List[Dict[str, Any]], budget_cap: Optional[float] = None) -> Dict[str, Any]`**
- Select actions where:
  - `estimated_effort_hours <= 2.0` (individual action is small)
  - `risk_tier` in ["auto", "low"]
  - `estimated_cost <= 50.0` (or within budget_cap if provided)
- Sort by `priority_score` descending
- Take top `MAX_7DAY_ACTIONS` actions, stopping if cumulative effort exceeds `MAX_7DAY_EFFORT_HOURS` or cumulative cost exceeds budget_cap
- Produce a ProposalBundle dict with:
  - `bundle_type`: "7_day"
  - `bundle_name`: "Week 1 Quick Wins"
  - `executive_summary`: auto-generated from the included actions (e.g., "This bundle contains {n} quick wins that can be completed in {total_hours} hours with ${total_cost} in spend. Focus areas: {top_3_categories}.")
  - `total_estimated_cost`: sum of selected action costs
  - `total_estimated_effort_hours`: sum of selected action effort hours
  - `expected_outcomes`: derived from each action's expected_outcome
- Return the bundle dict

**Function: `bundle_30day_plan(actions: List[Dict[str, Any]], budget_cap: Optional[float] = None, hours_per_week: float = 10.0) -> Dict[str, Any]`**
- Take all viable actions (not just quick wins) up to MAX_30DAY_ACTIONS
- Sort by: dependency order first (actions with no depends_on come first), then priority_score descending
- Assign actions to weekly milestones:
  - **Week 1**: quick wins (effort ≤ 2h, risk ≤ low) + foundation work (analytics fixes, tracking setup)
  - **Week 2**: content creation + SEO fixes + review system setup
  - **Week 3**: campaign preparation + creative production + email sequences
  - **Week 4**: campaign launch + paid media + measurement setup
- Each week's total effort should not exceed `hours_per_week`
- If budget_cap is provided, cumulative cost across all weeks must not exceed it
- Produce a ProposalBundle dict with:
  - `bundle_type`: "30_day"
  - `bundle_name`: "30-Day Marketing Improvement Plan"
  - `weekly_milestones`: dict with keys "week_1", "week_2", "week_3", "week_4", each containing a list of action IDs and milestone descriptions
  - `executive_summary`: overview of the month's plan
  - `expected_outcomes`: measurable outcomes expected by day 30

**Function: `bundle_campaign_pack(actions: List[Dict[str, Any]], campaign_theme: str) -> Optional[Dict[str, Any]]`**
- Group actions by thematic similarity. Campaign themes include:
  - "review_generation": review_request + reputation_action + social proof posts + email sequences about reviews
  - "local_visibility": seo_fix + gbp_update + service_area_pages + local ad campaign
  - "trust_building": case studies + testimonials + credentials + before/after content
  - "lead_capture": website_update (forms/CTAs) + kaicalls_setup + call tracking + speed-to-lead
  - "content_launch": content_creation (blog/pages) + social_post + email announcement
  - "paid_launch": ad_campaign + landing page + retargeting + tracking setup
- Match actions to the requested theme by checking action_type and tags
- If fewer than `CAMPAIGN_MIN_ACTIONS` match, return None
- Cap at `CAMPAIGN_MAX_ACTIONS`
- Produce a ProposalBundle dict with:
  - `bundle_type`: "campaign"
  - `bundle_name`: "{campaign_theme} Campaign" (title-cased)
  - `executive_summary`: describes the campaign's goal, actions, and expected results
  - Dependency-ordered action list

**Function: `bundle_monthly_operating_plan(actions: List[Dict[str, Any]], recurring_actions: Optional[List[Dict[str, Any]]] = None, budget_cap: Optional[float] = None) -> Dict[str, Any]`**
- Combine:
  - **Recurring actions**: social posting schedule, email sends, review monitoring, analytics check-ins, GBP posting. If `recurring_actions` not provided, generate stub recurring items based on action types present.
  - **One-time improvements**: selected from the action list, prioritized
  - **Measurement checkpoints**: at week 2 (mid-month check) and week 4 (month-end review)
- Structure the monthly plan with:
  - `weekly_milestones`: 4 weeks, each with recurring items + any one-time items scheduled for that week
  - `measurement_checkpoints`: list of metrics to check at each checkpoint
  - `executive_summary`: overview of the month's activity and goals
- Respect budget_cap across the entire month
- Return ProposalBundle dict with `bundle_type`: "monthly_operating"

**Function: `auto_bundle(actions: List[Dict[str, Any]], business_profile: Optional[Dict[str, Any]] = None, budget_cap: Optional[float] = None) -> List[Dict[str, Any]]`**
- High-level orchestrator that generates all applicable bundles from a list of actions:
  1. Always generate a 7-day quick wins bundle
  2. Always generate a 30-day plan
  3. Detect possible campaign themes and generate campaign packs for each
  4. Generate a monthly operating plan
- Extract budget_cap from business_profile's `budget.monthly_marketing_budget` if not provided directly
- Extract hours_per_week from business_profile's `operator.operator_hours_per_week` if available
- Return list of all generated ProposalBundle dicts

**Helper: `_generate_executive_summary(actions: List[Dict[str, Any]], bundle_type: str) -> str`**
- Generate a 3-5 sentence summary based on the actions included
- Mention: number of actions, total effort, total cost, top categories addressed, expected primary outcome
- Keep language operator-friendly (no jargon)

**Helper: `_detect_campaign_themes(actions: List[Dict[str, Any]]) -> List[str]`**
- Analyze the action types and tags in the list
- Return list of campaign theme strings that have enough matching actions (>= CAMPAIGN_MIN_ACTIONS)
- Check each theme's action_type patterns (defined above in bundle_campaign_pack)

**Helper: `_respect_budget(actions: List[Dict[str, Any]], budget_cap: float) -> List[Dict[str, Any]]`**
- Filter/truncate actions to stay within budget_cap
- Prioritize by priority_score — keep highest priority actions first
- Return filtered list

## Output Files

- `kai/proposals/bundler.py`

## Acceptance Criteria

- [ ] `bundler.py` contains all 4 main bundling functions and the auto_bundle orchestrator
- [ ] 7-day bundle correctly filters by effort, risk, and cost constraints
- [ ] 30-day plan assigns actions to weekly milestones with effort cap per week
- [ ] Campaign pack groups actions by theme and requires minimum action count
- [ ] Monthly operating plan includes both one-time and recurring items
- [ ] auto_bundle generates all applicable bundle types in one call
- [ ] Budget constraints from BusinessProfile are respected when provided
- [ ] Executive summaries are auto-generated and operator-readable
- [ ] All functions accept dicts (not requiring Pydantic model instances) for flexibility
- [ ] Helper functions for summary generation, theme detection, and budget filtering exist
- [ ] Constants for limits (max actions, max effort) are defined at module level
- [ ] No side effects — all functions are pure

## Reference Materials

- `kai/models/proposal.py` (created by Task 022) — ProposedAction and ProposalBundle schemas
- `kai/models/business_profile.py` (created by Task 001) — BudgetAndRisk.monthly_marketing_budget, OperatorCapacity.operator_hours_per_week
- `kai/proposals/action_mapper.py` (created by Task 023) — produces the actions that bundling consumes
- `CLAUDE.md` — quality gate rules and content pipeline
