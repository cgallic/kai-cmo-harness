"""Capacity-aware pruning and action mode selection.

This module filters a ranked, deduped list of ProposedAction dicts
against real-world operator constraints: available hours, monthly budget,
risk tolerance, and channel preferences.  It also selects between two
operating modes:

- **Compounding** (default): many small, safe, incremental actions
  distributed across weeks for steady improvement.
- **Burst**: concentrated effort compressed into a 2-week push for
  launches, seasonal events, or urgent remediation.

The main entry point is ``prune_and_shape``, which orchestrates the
full pipeline: mode selection, channel boosting, capacity pruning, and
mode-specific scheduling.

Design principles
-----------------
1. **Transparency.**  Every pruned action carries a ``pruned_reason``
   explaining why it was removed.
2. **Capacity-realistic.**  The output is achievable within the
   operator's stated hours and budget.
3. **Mode-appropriate.**  Compounding mode builds confidence with quick
   wins first; burst mode frontloads foundation work.
4. **Pure functions.**  No file I/O, no network, no state mutation.
"""

from __future__ import annotations

import copy
from collections import defaultdict
from enum import Enum
from typing import Any, Dict, List, Optional


# ============================================================================
# Enums and Data Models
# ============================================================================


class ActionMode(str, Enum):
    """Operating mode for action scheduling.

    COMPOUNDING
        Many small, safe, incremental actions over time.  Default for
        most businesses.  Builds confidence, shows quick results, and
        compounds gains week over week.

    BURST
        Concentrate effort into one coordinated push over 2 weeks.
        Used for product launches, seasonal pushes, grand openings,
        or when the majority of findings are critical/high severity.
    """

    COMPOUNDING = "compounding"
    BURST = "burst"


class CapacityConstraints:
    """Operator capacity and preference constraints.

    Attributes
    ----------
    hours_per_week:
        Available operator hours per week.
    monthly_budget:
        Total monthly marketing budget in USD.  0 means only free
        actions are viable.
    risk_tolerance:
        One of ``"conservative"``, ``"moderate"``, ``"aggressive"``.
    auto_execution_enabled:
        Whether the system can auto-execute approved actions.
    max_actions_per_week:
        Hard cap on actions per week.
    blocked_channels:
        Channels the operator does not want actions on.
    preferred_channels:
        Channels the operator prefers (these get a priority boost).
    """

    __slots__ = (
        "hours_per_week",
        "monthly_budget",
        "risk_tolerance",
        "auto_execution_enabled",
        "max_actions_per_week",
        "blocked_channels",
        "preferred_channels",
    )

    def __init__(
        self,
        hours_per_week: float = 10.0,
        monthly_budget: float = 0.0,
        risk_tolerance: str = "moderate",
        auto_execution_enabled: bool = False,
        max_actions_per_week: int = 10,
        blocked_channels: Optional[List[str]] = None,
        preferred_channels: Optional[List[str]] = None,
    ) -> None:
        self.hours_per_week = hours_per_week
        self.monthly_budget = monthly_budget
        self.risk_tolerance = risk_tolerance
        self.auto_execution_enabled = auto_execution_enabled
        self.max_actions_per_week = max_actions_per_week
        self.blocked_channels = blocked_channels or []
        self.preferred_channels = preferred_channels or []

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CapacityConstraints":
        """Construct from a dict, using defaults for missing keys."""
        return cls(
            hours_per_week=data.get("hours_per_week", 10.0),
            monthly_budget=data.get("monthly_budget", 0.0),
            risk_tolerance=data.get("risk_tolerance", "moderate"),
            auto_execution_enabled=data.get("auto_execution_enabled", False),
            max_actions_per_week=data.get("max_actions_per_week", 10),
            blocked_channels=data.get("blocked_channels", []),
            preferred_channels=data.get("preferred_channels", []),
        )


# Risk tiers ordered from least risky to most risky
_RISK_ORDER = ("auto", "low", "medium", "high", "critical")

# Burst mode keywords in operator requests
_BURST_KEYWORDS = frozenset({
    "launch", "push", "campaign", "blast", "seasonal",
    "holiday", "black friday", "grand opening",
})

# Burst phase action-type assignments
_BURST_PHASES: Dict[str, Dict[str, Any]] = {
    "foundation": {
        "days": "1-2",
        "action_types": {"analytics_fix", "seo_fix"},
        "description": "Set up tracking, fix technical foundation",
    },
    "creation": {
        "days": "3-7",
        "action_types": {"content_creation", "website_update", "gbp_update"},
        "description": "Create content, update website, prepare assets",
    },
    "launch": {
        "days": "8-12",
        "action_types": {"ad_campaign", "social_post", "email_sequence"},
        "description": "Launch campaigns, publish content, start sequences",
    },
    "activate": {
        "days": "13-14",
        "action_types": {"follow_up_sequence", "review_request", "reputation_action", "kaicalls_setup"},
        "description": "Activate follow-up systems, start review requests",
    },
}


# ============================================================================
# Mode Selection
# ============================================================================


def select_action_mode(
    business_stage: str,
    operator_request: Optional[str] = None,
    finding_severity_distribution: Optional[Dict[str, int]] = None,
) -> str:
    """Select between compounding and burst operating modes.

    Decision logic (checked in order):
    1. If the operator's request contains launch/push/campaign/seasonal
       keywords, return burst.
    2. If the business is pre-launch, return burst.
    3. If more than 50% of findings are critical or high severity,
       return burst.
    4. Otherwise, return compounding.

    Parameters
    ----------
    business_stage:
        Current business stage (e.g., ``"pre-launch"``, ``"growth"``).
    operator_request:
        Free-text operator request or context.
    finding_severity_distribution:
        Dict mapping severity level to finding count
        (e.g., ``{"critical": 3, "high": 5, "medium": 10}``).

    Returns
    -------
    str
        ``"compounding"`` or ``"burst"``.
    """
    # Check operator request for burst keywords
    if operator_request:
        request_lower = operator_request.lower()
        for keyword in _BURST_KEYWORDS:
            if keyword in request_lower:
                return ActionMode.BURST.value

    # Pre-launch businesses need everything set up
    if business_stage == "pre-launch":
        return ActionMode.BURST.value

    # Check severity distribution
    if finding_severity_distribution:
        total = sum(finding_severity_distribution.values())
        if total > 0:
            urgent = (
                finding_severity_distribution.get("critical", 0)
                + finding_severity_distribution.get("high", 0)
            )
            if urgent / total > 0.50:
                return ActionMode.BURST.value

    return ActionMode.COMPOUNDING.value


# ============================================================================
# Capacity Pruning
# ============================================================================


def prune_by_capacity(
    actions: List[Dict[str, Any]],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    """Filter actions against capacity constraints.

    Removes actions that exceed risk tolerance, budget limits, effort
    caps, or are on blocked channels.  Returns both the included and
    pruned lists with reasons.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    constraints:
        Constraints dict (parsed into ``CapacityConstraints``).

    Returns
    -------
    dict
        ``{"included": [...], "pruned": [...], "capacity_utilization": {...}}``
    """
    caps = CapacityConstraints.from_dict(constraints)

    included: List[Dict[str, Any]] = []
    pruned: List[Dict[str, Any]] = []

    # Sort by priority for deterministic truncation
    sorted_actions = sorted(
        [copy.deepcopy(a) for a in actions],
        key=lambda a: a.get("priority_score", 0),
        reverse=True,
    )

    # Risk tier threshold based on tolerance
    if caps.risk_tolerance == "conservative":
        blocked_risks = {"high", "critical"}
    elif caps.risk_tolerance == "moderate":
        blocked_risks = {"critical"}
    else:  # aggressive
        blocked_risks = set()

    # Phase 1: filter by channel, risk, and individual cost
    phase1: List[Dict[str, Any]] = []
    for action in sorted_actions:
        channel = action.get("channel", "")
        risk = action.get("risk_tier", "low")
        cost = action.get("estimated_cost") or 0.0

        # Check blocked channels
        if channel in caps.blocked_channels:
            action.setdefault("metadata", {})
            action["metadata"]["pruned_reason"] = f"Channel '{channel}' is blocked by operator"
            pruned.append(action)
            continue

        # Check risk tolerance
        if risk in blocked_risks:
            action.setdefault("metadata", {})
            action["metadata"]["pruned_reason"] = (
                f"Risk tier '{risk}' exceeds '{caps.risk_tolerance}' tolerance"
            )
            pruned.append(action)
            continue

        # Check individual cost cap (no single action > 50% of budget)
        if (caps.monthly_budget > 0
                and cost > caps.monthly_budget * 0.5
                and caps.risk_tolerance != "aggressive"):
            action.setdefault("metadata", {})
            action["metadata"]["pruned_reason"] = (
                f"Cost ${cost:.2f} exceeds 50% of monthly budget "
                f"${caps.monthly_budget:.2f}"
            )
            pruned.append(action)
            continue

        phase1.append(action)

    # Phase 2: truncate by monthly effort capacity
    monthly_capacity = caps.hours_per_week * 4
    cumulative_effort = 0.0
    phase2: List[Dict[str, Any]] = []

    for action in phase1:
        effort = action.get("estimated_effort_hours") or 0.0
        if cumulative_effort + effort > monthly_capacity:
            action.setdefault("metadata", {})
            action["metadata"]["pruned_reason"] = (
                f"Monthly effort capacity exhausted "
                f"({round(monthly_capacity, 1)}h limit, "
                f"{round(cumulative_effort, 1)}h already allocated)"
            )
            pruned.append(action)
            continue
        cumulative_effort += effort
        phase2.append(action)

    # Phase 3: truncate by total budget
    if caps.monthly_budget > 0:
        cumulative_cost = 0.0
        for action in list(phase2):
            cost = action.get("estimated_cost") or 0.0
            if cost > 0 and cumulative_cost + cost > caps.monthly_budget:
                phase2.remove(action)
                action.setdefault("metadata", {})
                action["metadata"]["pruned_reason"] = (
                    f"Monthly budget exhausted "
                    f"(${caps.monthly_budget:.2f} limit, "
                    f"${cumulative_cost:.2f} already allocated)"
                )
                pruned.append(action)
                continue
            cumulative_cost += cost

    included = phase2
    utilization = _compute_capacity_utilization(included, constraints)

    return {
        "included": included,
        "pruned": pruned,
        "capacity_utilization": utilization,
    }


# ============================================================================
# Channel Boosting
# ============================================================================


def boost_preferred_channels(
    actions: List[Dict[str, Any]],
    preferred_channels: List[str],
    boost_factor: float = 1.15,
) -> List[Dict[str, Any]]:
    """Boost priority scores for actions on preferred channels.

    Multiplies each matching action's ``priority_score`` by
    *boost_factor*, then re-sorts by score descending.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    preferred_channels:
        Channel names to boost.
    boost_factor:
        Multiplier for preferred-channel actions.

    Returns
    -------
    list[dict]
        Boosted and re-sorted action list.
    """
    if not preferred_channels:
        return list(actions)

    preferred_set = set(preferred_channels)
    boosted = []

    for action in actions:
        action = copy.deepcopy(action)
        if action.get("channel", "") in preferred_set:
            current = action.get("priority_score", 50.0)
            action["priority_score"] = min(100.0, round(current * boost_factor, 2))
            action.setdefault("metadata", {})
            action["metadata"]["channel_boosted"] = True
        boosted.append(action)

    boosted.sort(key=lambda a: a.get("priority_score", 0), reverse=True)
    return boosted


# ============================================================================
# Mode Shaping: Compounding
# ============================================================================


def shape_for_compounding(
    actions: List[Dict[str, Any]],
    hours_per_week: float = 10.0,
    weeks: int = 4,
) -> List[Dict[str, Any]]:
    """Distribute actions across weeks for steady compounding execution.

    Week distribution:
    - Week 1: auto/low risk actions (build confidence, show quick results)
    - Week 2: mix of low and medium risk
    - Weeks 3-4: can include medium and high risk

    Within each week, effort does not exceed *hours_per_week*, and
    category diversity is maintained.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    hours_per_week:
        Maximum effort hours per week.
    weeks:
        Number of weeks to distribute across.

    Returns
    -------
    list[dict]
        Actions with ``scheduled_week`` in metadata.
    """
    # Define risk tolerance per week
    week_risk_caps = {
        1: {"auto", "low"},
        2: {"auto", "low", "medium"},
        3: {"auto", "low", "medium", "high"},
        4: {"auto", "low", "medium", "high"},
    }
    # Extend for weeks > 4
    for w in range(5, weeks + 1):
        week_risk_caps[w] = {"auto", "low", "medium", "high"}

    weekly_effort: Dict[int, float] = {w: 0.0 for w in range(1, weeks + 1)}
    weekly_categories: Dict[int, Dict[str, int]] = {w: defaultdict(int) for w in range(1, weeks + 1)}
    assigned: List[Dict[str, Any]] = []
    assigned_ids: set = set()

    # Sort by priority descending
    sorted_actions = sorted(
        actions, key=lambda a: a.get("priority_score", 0), reverse=True
    )

    # First pass: assign each action to the best-fit week
    for action in sorted_actions:
        action = copy.deepcopy(action)
        action_id = action.get("id", "")
        if action_id in assigned_ids:
            continue

        risk = action.get("risk_tier", "low")
        effort = action.get("estimated_effort_hours") or 0.0
        meta = action.get("metadata", {})
        category = meta.get("finding_category", action.get("channel", "general"))

        best_week = None
        best_diversity_score = -1

        for week_num in range(1, weeks + 1):
            # Check risk tolerance
            if risk not in week_risk_caps.get(week_num, set()):
                continue

            # Check effort capacity
            if weekly_effort[week_num] + effort > hours_per_week:
                continue

            # Compute diversity score -- prefer weeks that don't already
            # have many actions in this category
            cat_count = weekly_categories[week_num].get(category, 0)
            diversity_score = 10 - cat_count  # Lower category count = better

            if diversity_score > best_diversity_score:
                best_diversity_score = diversity_score
                best_week = week_num

        if best_week is not None:
            action.setdefault("metadata", {})
            action["metadata"]["scheduled_week"] = best_week
            weekly_effort[best_week] += effort
            weekly_categories[best_week][category] += 1
            assigned.append(action)
            assigned_ids.add(action_id)

    return assigned


# ============================================================================
# Mode Shaping: Burst
# ============================================================================


def shape_for_burst(
    actions: List[Dict[str, Any]],
    hours_per_week: float = 20.0,
    burst_weeks: int = 2,
) -> List[Dict[str, Any]]:
    """Concentrate actions into a compressed burst timeline.

    Four phases over *burst_weeks*:
    - Foundation (days 1-2): analytics, tracking, technical fixes
    - Creation (days 3-7): content, website updates, assets
    - Launch (days 8-12): campaigns, social, email sends
    - Activate (days 13-14): follow-up systems, review requests

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    hours_per_week:
        Effort per week (2x normal for burst mode).
    burst_weeks:
        Duration of the burst in weeks.

    Returns
    -------
    list[dict]
        Actions with ``burst_phase`` and ``burst_day`` in metadata.
    """
    total_capacity = hours_per_week * burst_weeks
    cumulative_effort = 0.0

    # Assign actions to phases by type
    phase_actions: Dict[str, List[Dict[str, Any]]] = {
        "foundation": [],
        "creation": [],
        "launch": [],
        "activate": [],
    }
    unassigned: List[Dict[str, Any]] = []

    sorted_actions = sorted(
        actions, key=lambda a: a.get("priority_score", 0), reverse=True
    )

    for action in sorted_actions:
        action = copy.deepcopy(action)
        action_type = action.get("action_type", "")
        placed = False

        for phase_name, phase_config in _BURST_PHASES.items():
            if action_type in phase_config["action_types"]:
                phase_actions[phase_name].append(action)
                placed = True
                break

        if not placed:
            unassigned.append(action)

    # Distribute unassigned actions to phases with capacity
    phase_order = ["foundation", "creation", "launch", "activate"]
    for action in unassigned:
        # Default: put in creation phase (most flexible)
        phase_actions["creation"].append(action)

    # Assign burst_phase, burst_day, and check capacity
    result: List[Dict[str, Any]] = []
    day_cursor = 1
    phase_day_ranges = {
        "foundation": (1, 2),
        "creation": (3, 7),
        "launch": (8, 12),
        "activate": (13, 14),
    }

    for phase_name in phase_order:
        phase_config = _BURST_PHASES[phase_name]
        day_start, day_end = phase_day_ranges[phase_name]
        phase_acts = phase_actions[phase_name]

        # Sort within phase by priority
        phase_acts.sort(key=lambda a: a.get("priority_score", 0), reverse=True)

        for i, action in enumerate(phase_acts):
            effort = action.get("estimated_effort_hours") or 0.0
            if cumulative_effort + effort > total_capacity:
                break

            # Distribute days across the phase's day range
            day_range = day_end - day_start + 1
            assigned_day = day_start + (i % day_range)

            action.setdefault("metadata", {})
            action["metadata"]["burst_phase"] = phase_name
            action["metadata"]["burst_day"] = assigned_day
            action["metadata"]["burst_phase_description"] = phase_config["description"]

            cumulative_effort += effort
            result.append(action)

    return result


# ============================================================================
# Pipeline Orchestrator
# ============================================================================


def prune_and_shape(
    actions: List[Dict[str, Any]],
    constraints: Dict[str, Any],
    business_stage: str = "early-pmf",
    operator_request: Optional[str] = None,
) -> Dict[str, Any]:
    """Full capacity-aware pruning and scheduling pipeline.

    Steps:
    1. Select action mode (compounding or burst).
    2. Boost preferred channels.
    3. Prune by capacity constraints.
    4. Shape for the selected mode.
    5. Compute utilization metrics and warnings.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts (from ranking.process_actions).
    constraints:
        Capacity constraints dict.
    business_stage:
        Current business stage.
    operator_request:
        Free-text operator request for mode detection.

    Returns
    -------
    dict
        Full result with ``mode``, ``actions``, ``pruned``,
        ``capacity_utilization``, and ``warnings``.
    """
    caps = CapacityConstraints.from_dict(constraints)

    # Step 1: Select mode
    severity_dist = _extract_severity_distribution(actions)
    mode = select_action_mode(
        business_stage=business_stage,
        operator_request=operator_request,
        finding_severity_distribution=severity_dist,
    )

    # Build mode reason
    mode_reason = _build_mode_reason(mode, business_stage, operator_request, severity_dist)

    # Step 2: Boost preferred channels
    boosted = boost_preferred_channels(
        actions,
        preferred_channels=caps.preferred_channels,
    )

    # Step 3: Prune by capacity
    prune_result = prune_by_capacity(boosted, constraints)
    included = prune_result["included"]
    pruned = prune_result["pruned"]

    # Step 4: Shape for selected mode
    if mode == ActionMode.BURST.value:
        shaped = shape_for_burst(
            included,
            hours_per_week=caps.hours_per_week * 2,  # 2x effort for burst
            burst_weeks=2,
        )
    else:
        shaped = shape_for_compounding(
            included,
            hours_per_week=caps.hours_per_week,
            weeks=4,
        )

    # Step 5: Compute metrics and warnings
    utilization = _compute_capacity_utilization(shaped, constraints)
    warnings = _generate_warnings(shaped, constraints, mode)

    return {
        "mode": mode,
        "mode_reason": mode_reason,
        "actions": shaped,
        "pruned": pruned,
        "capacity_utilization": utilization,
        "warnings": warnings,
    }


# ============================================================================
# Internal helpers
# ============================================================================


def _compute_capacity_utilization(
    actions: List[Dict[str, Any]],
    constraints: Dict[str, Any],
) -> Dict[str, Any]:
    """Calculate capacity utilization metrics.

    Returns total effort, weekly average, total cost, budget utilization
    percentage, and average actions per week.
    """
    total_effort = sum(a.get("estimated_effort_hours") or 0.0 for a in actions)
    total_cost = sum(a.get("estimated_cost") or 0.0 for a in actions)
    monthly_budget = constraints.get("monthly_budget", 0.0)

    budget_pct = 0.0
    if monthly_budget and monthly_budget > 0:
        budget_pct = round(total_cost / monthly_budget * 100, 1)

    return {
        "total_effort_hours": round(total_effort, 2),
        "weekly_effort_hours": round(total_effort / 4, 2),
        "total_cost": round(total_cost, 2),
        "budget_utilization_pct": budget_pct,
        "actions_per_week": round(len(actions) / 4, 1),
    }


def _generate_warnings(
    actions: List[Dict[str, Any]],
    constraints: Dict[str, Any],
    mode: str,
) -> List[str]:
    """Generate warnings about capacity and constraint edge cases."""
    caps = CapacityConstraints.from_dict(constraints)
    warnings: List[str] = []

    total_effort = sum(a.get("estimated_effort_hours") or 0.0 for a in actions)
    total_cost = sum(a.get("estimated_cost") or 0.0 for a in actions)
    weekly_effort = total_effort / 4

    # Warning: weekly effort exceeds capacity
    if weekly_effort > caps.hours_per_week:
        warnings.append(
            f"Weekly effort ({round(weekly_effort, 1)}h) exceeds available "
            f"hours ({caps.hours_per_week}h/week). Consider extending the "
            f"timeline or reducing scope."
        )

    # Warning: budget near limit
    if caps.monthly_budget > 0 and total_cost > caps.monthly_budget * 0.90:
        pct = round(total_cost / caps.monthly_budget * 100, 1)
        warnings.append(
            f"Total cost (${round(total_cost, 2)}) uses {pct}% of the "
            f"monthly budget (${caps.monthly_budget:.2f}). Very little "
            f"budget remains for unexpected needs."
        )

    # Warning: all high-priority actions pruned
    if not actions:
        warnings.append(
            "No actions remain after pruning. Consider increasing budget, "
            "available hours, or risk tolerance."
        )

    # Warning: burst mode with low hours
    if mode == ActionMode.BURST.value and caps.hours_per_week < 15:
        warnings.append(
            f"Burst mode selected but operator has only {caps.hours_per_week}h/week "
            f"available. Burst mode works best with 15+ hours/week. Consider "
            f"switching to compounding mode or freeing up more time."
        )

    # Warning: no budget for paid actions
    paid_actions = [a for a in actions if a.get("action_type") == "ad_campaign"]
    if paid_actions and caps.monthly_budget == 0:
        warnings.append(
            f"{len(paid_actions)} paid campaign(s) are included but monthly "
            f"budget is $0. These actions require ad spend to execute."
        )

    return warnings


def _extract_severity_distribution(
    actions: List[Dict[str, Any]],
) -> Dict[str, int]:
    """Extract finding severity distribution from action metadata."""
    dist: Dict[str, int] = defaultdict(int)
    for action in actions:
        meta = action.get("metadata", {})
        severity = meta.get("finding_severity", "medium")
        dist[severity] += 1
    return dict(dist)


def _build_mode_reason(
    mode: str,
    business_stage: str,
    operator_request: Optional[str],
    severity_dist: Dict[str, int],
) -> str:
    """Build a human-readable explanation for the selected mode."""
    if mode == ActionMode.BURST.value:
        if operator_request:
            request_lower = operator_request.lower()
            for keyword in _BURST_KEYWORDS:
                if keyword in request_lower:
                    return f"Burst mode selected because the request mentions '{keyword}'."

        if business_stage == "pre-launch":
            return "Burst mode selected because the business is pre-launch and needs rapid setup."

        total = sum(severity_dist.values())
        if total > 0:
            urgent = severity_dist.get("critical", 0) + severity_dist.get("high", 0)
            if urgent / total > 0.50:
                return (
                    f"Burst mode selected because {urgent} of {total} findings "
                    f"({round(urgent / total * 100)}%) are critical or high severity."
                )

        return "Burst mode selected based on overall assessment."

    return (
        "Compounding mode selected for steady, incremental improvement. "
        "Small wins build momentum and compound over time."
    )
