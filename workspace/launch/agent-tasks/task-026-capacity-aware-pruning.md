# Task 026: Build capacity-aware pruning and action mode selection

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 4. Proposal and Planning
**Priority:** P2
**Depends on:** 022, 005
**Estimated complexity:** Medium

## Context

A ranked, deduped list of ProposedActions still needs to be filtered against real-world constraints: how many hours per week does the operator have? What is the monthly budget? How risk-tolerant is this business? Beyond pruning, the system needs to select between two fundamentally different operating modes — the steady "small compounding actions" mode (default) where the system makes consistent incremental improvements, and the "campaign burst" mode where effort is concentrated into a coordinated push. The right mode depends on the business's stage, the operator's request, and the nature of the findings.

## Scope

Build `kai/proposals/pruning.py` with functions for capacity-aware action filtering, mode selection, and mode-specific action list shaping. This module takes a processed action list (from ranking.py) and workspace/operator constraints, and produces a realistic, achievable action list.

## Detailed Requirements

### File: `kai/proposals/pruning.py`

**Enum: ActionMode**
- `COMPOUNDING` — many small, safe, incremental actions over time. Default for most businesses.
- `BURST` — concentrate effort into one coordinated push. Used for launches, seasonal pushes, or operator request.

**Data model: CapacityConstraints**
- `hours_per_week: float` — operator's available hours per week, default 10.0
- `monthly_budget: float` — total monthly marketing budget in USD, default 0.0 (no budget means only free actions)
- `risk_tolerance: str` — one of "conservative", "moderate", "aggressive", default "moderate"
- `auto_execution_enabled: bool` — whether the system can auto-execute approved actions, default False
- `max_actions_per_week: int` — hard cap on actions per week to prevent overwhelm, default 10
- `blocked_channels: List[str]` — channels the operator does not want actions on, default empty list
- `preferred_channels: List[str]` — channels the operator prefers (boost priority), default empty list

**Function: `select_action_mode(business_stage: str, operator_request: Optional[str] = None, finding_severity_distribution: Optional[Dict[str, int]] = None) -> str`**
- Returns ActionMode value ("compounding" or "burst")
- Decision logic:
  - If `operator_request` contains keywords "launch", "push", "campaign", "blast", "seasonal", "holiday", "black friday", "grand opening" → return "burst"
  - If `business_stage` == "pre-launch" → return "burst" (need to get everything set up)
  - If `finding_severity_distribution` and more than 50% of findings are "critical" or "high" → return "burst" (too many urgent issues for incremental approach)
  - Otherwise → return "compounding"
- Include docstring explaining the two modes clearly

**Function: `prune_by_capacity(actions: List[Dict[str, Any]], constraints: Dict[str, Any]) -> List[Dict[str, Any]]`**
- Parse constraints dict into CapacityConstraints fields
- Filter actions:
  1. Remove actions on `blocked_channels`
  2. Remove actions where `estimated_cost > monthly_budget * 0.5` (no single action should take more than half the budget) — unless risk_tolerance is "aggressive"
  3. Remove actions where `risk_tier` exceeds tolerance:
     - conservative: remove "high" and "critical" risk actions
     - moderate: remove "critical" risk actions
     - aggressive: keep all
  4. If total estimated_effort_hours across all remaining actions exceeds `hours_per_week * 4` (monthly capacity), truncate the list by priority_score — keep highest priority first
  5. If total estimated_cost exceeds `monthly_budget`, truncate by priority_score
- For each removed action, add a `pruned_reason` field in its metadata explaining why it was removed
- Return the filtered list plus a separate `pruned_actions` list (for transparency)
- Return format: `{"included": [...], "pruned": [...], "capacity_utilization": {...}}`

**Function: `boost_preferred_channels(actions: List[Dict[str, Any]], preferred_channels: List[str], boost_factor: float = 1.15) -> List[Dict[str, Any]]`**
- For actions on preferred_channels, multiply priority_score by boost_factor
- Re-sort by priority_score
- Return boosted and sorted list

**Function: `shape_for_compounding(actions: List[Dict[str, Any]], hours_per_week: float = 10.0, weeks: int = 4) -> List[Dict[str, Any]]`**
- Distribute actions across weeks for steady execution:
  - Week 1: prioritize "auto" and "low" risk actions (build confidence, show quick results)
  - Week 2: mix of "low" and "medium" risk actions
  - Week 3-4: can include "medium" and "high" risk actions
- Each week's total effort should not exceed `hours_per_week`
- Tag each action with `scheduled_week: int` in metadata
- Ensure diversity: don't put all actions from one category in the same week
- Return actions with scheduling metadata

**Function: `shape_for_burst(actions: List[Dict[str, Any]], hours_per_week: float = 20.0, burst_weeks: int = 2) -> List[Dict[str, Any]]`**
- Concentrate high-impact actions into a compressed timeline:
  - All foundation work (analytics, tracking) in first 2 days
  - All content creation in days 3-7
  - All campaign launches in week 2
  - All follow-up systems activated by end of week 2
- Higher effort tolerance per week (2x normal)
- Tag each action with `burst_day: int` or `burst_phase: str` in metadata
- Phases: "foundation" (days 1-2), "creation" (days 3-7), "launch" (days 8-12), "activate" (days 13-14)
- Return actions with burst scheduling metadata

**Function: `prune_and_shape(actions: List[Dict[str, Any]], constraints: Dict[str, Any], business_stage: str = "early-pmf", operator_request: Optional[str] = None) -> Dict[str, Any]`**
- High-level orchestrator:
  1. Select action mode
  2. Boost preferred channels
  3. Prune by capacity
  4. Shape for selected mode (compounding or burst)
  5. Compute capacity utilization metrics
- Return:
  ```python
  {
      "mode": "compounding" | "burst",
      "mode_reason": "why this mode was selected",
      "actions": [...],        # shaped and scheduled actions
      "pruned": [...],         # removed actions with reasons
      "capacity_utilization": {
          "total_effort_hours": float,
          "weekly_effort_hours": float,
          "total_cost": float,
          "budget_utilization_pct": float,
          "actions_per_week": float,
      },
      "warnings": [...]  # any warnings about capacity or constraints
  }
  ```

**Helper: `_compute_capacity_utilization(actions: List[Dict[str, Any]], constraints: Dict[str, Any]) -> Dict[str, Any]`**
- Calculate:
  - `total_effort_hours`: sum of all estimated_effort_hours
  - `weekly_effort_hours`: total / 4 (monthly average)
  - `total_cost`: sum of all estimated_cost
  - `budget_utilization_pct`: total_cost / monthly_budget * 100 (or 0 if no budget)
  - `actions_per_week`: len(actions) / 4
- Return metrics dict

**Helper: `_generate_warnings(actions: List[Dict[str, Any]], constraints: Dict[str, Any], mode: str) -> List[str]`**
- Generate warnings when:
  - Weekly effort exceeds hours_per_week (even after pruning)
  - Total cost exceeds 90% of monthly budget
  - All high-priority actions were pruned due to risk tolerance
  - No actions remain after pruning
  - Burst mode selected but operator has < 15 hours/week available

## Output Files

- `kai/proposals/pruning.py`

## Acceptance Criteria

- [ ] `pruning.py` contains ActionMode enum and CapacityConstraints model
- [ ] select_action_mode correctly handles operator requests, business stage, and severity distribution
- [ ] prune_by_capacity removes actions exceeding budget, risk tolerance, and effort caps
- [ ] Pruned actions include reasons for removal in metadata
- [ ] boost_preferred_channels correctly boosts and re-sorts actions
- [ ] shape_for_compounding distributes actions across 4 weeks with effort caps and diversity
- [ ] shape_for_burst concentrates actions into 4 phases over 2 weeks
- [ ] prune_and_shape orchestrates the full pipeline and returns structured output
- [ ] Capacity utilization metrics are computed and included in output
- [ ] Warnings are generated for edge cases (over-capacity, budget near limit, etc.)
- [ ] Conservative risk tolerance correctly filters out high/critical actions
- [ ] No side effects — all functions are pure

## Reference Materials

- `kai/models/proposal.py` (created by Task 022) — ProposedAction fields: priority_score, risk_tier, estimated_effort_hours, estimated_cost, channel
- `kai/models/business_profile.py` (created by Task 001) — BudgetAndRisk (monthly_marketing_budget, risk_tolerance, auto_execution_enabled), OperatorCapacity (operator_hours_per_week, preferred_channels)
- `kai/proposals/ranking.py` (created by Task 025) — produces the ranked list this module prunes
- Connected workspace state model (Task 005) — WorkspaceState with operator constraints
