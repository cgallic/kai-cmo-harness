"""Proposal bundling system for the Kai Marketing OS.

This module groups related ProposedAction dicts into coherent, time-boxed
plans that operators can review and approve as a unit.  Four bundle types
are supported:

- **7-day quick wins** -- small, low-risk actions for immediate impact.
- **30-day plan** -- a month of improvement with weekly milestones.
- **Campaign pack** -- actions grouped around a single marketing theme.
- **Monthly operating plan** -- recurring maintenance + one-time improvements.

The main entry point is ``auto_bundle``, which generates all applicable
bundles from a list of actions in one call.

Design principles
-----------------
1. **Operator-readable.**  Every bundle has an auto-generated executive
   summary in plain English.
2. **Constraint-aware.**  Budget caps and effort limits are respected.
3. **Composable.**  Each bundling function works independently and can
   be called directly when only one bundle type is needed.
4. **Pure functions.**  No file I/O, no network, no state mutation.
"""

from __future__ import annotations

import copy
import uuid
from collections import defaultdict
from typing import Any, Dict, List, Optional


# ============================================================================
# Constants
# ============================================================================

MAX_7DAY_ACTIONS = 7
MAX_7DAY_EFFORT_HOURS = 10.0
MAX_30DAY_ACTIONS = 25
CAMPAIGN_MIN_ACTIONS = 3
CAMPAIGN_MAX_ACTIONS = 12

# Campaign theme definitions: theme name -> matching action_types and tag patterns
_CAMPAIGN_THEMES: Dict[str, Dict[str, Any]] = {
    "review_generation": {
        "action_types": {"review_request", "reputation_action", "social_post", "email_sequence"},
        "tag_patterns": {"reviews", "reputation", "social_proof", "testimonial"},
    },
    "local_visibility": {
        "action_types": {"seo_fix", "gbp_update", "content_creation", "ad_campaign"},
        "tag_patterns": {"local", "seo", "gbp", "service_area", "nap", "schema", "google_lsa"},
    },
    "trust_building": {
        "action_types": {"content_creation", "website_update", "social_post"},
        "tag_patterns": {"trust", "case_study", "testimonials", "credentials", "before_after", "guarantee", "social_proof"},
    },
    "lead_capture": {
        "action_types": {"website_update", "kaicalls_setup", "analytics_fix"},
        "tag_patterns": {"conversion", "cta", "form", "phone", "click_to_call", "call_tracking", "speed_to_lead", "kaicalls"},
    },
    "content_launch": {
        "action_types": {"content_creation", "social_post", "email_sequence"},
        "tag_patterns": {"content", "service_page", "landing_page", "blog", "social"},
    },
    "paid_launch": {
        "action_types": {"ad_campaign", "content_creation", "analytics_fix"},
        "tag_patterns": {"paid_media", "campaign", "retargeting", "tracking", "google_ads", "google_lsa"},
    },
}

# Week assignment rules for 30-day plan
_WEEK_CATEGORY_RULES: Dict[int, Dict[str, Any]] = {
    1: {
        "label": "Foundation & Quick Wins",
        "max_effort": None,  # overridden by hours_per_week
        "risk_cap": {"auto", "low"},
        "action_types": {"analytics_fix", "seo_fix", "website_update", "gbp_update"},
        "priority": "quick_wins_first",
    },
    2: {
        "label": "Content & SEO",
        "max_effort": None,
        "risk_cap": {"auto", "low", "medium"},
        "action_types": {"content_creation", "seo_fix", "review_request", "reputation_action"},
        "priority": "content_first",
    },
    3: {
        "label": "Campaigns & Creative",
        "max_effort": None,
        "risk_cap": {"auto", "low", "medium"},
        "action_types": {"content_creation", "email_sequence", "follow_up_sequence", "social_post", "kaicalls_setup"},
        "priority": "campaign_prep",
    },
    4: {
        "label": "Launch & Measure",
        "max_effort": None,
        "risk_cap": {"auto", "low", "medium", "high"},
        "action_types": {"ad_campaign", "analytics_fix", "email_sequence"},
        "priority": "launch",
    },
}


# ============================================================================
# 7-Day Quick Wins Bundle
# ============================================================================


def bundle_7day_quick_wins(
    actions: List[Dict[str, Any]],
    budget_cap: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate a 7-day quick wins bundle from eligible actions.

    Selects low-effort, low-risk, affordable actions sorted by priority,
    capped at ``MAX_7DAY_ACTIONS`` or ``MAX_7DAY_EFFORT_HOURS``.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    budget_cap:
        Maximum total cost for the bundle.

    Returns
    -------
    dict
        A ProposalBundle-compatible dict with ``bundle_type: "7_day"``.
    """
    # Filter eligible actions
    eligible = [
        a for a in actions
        if (
            (a.get("estimated_effort_hours") or 0) <= 2.0
            and a.get("risk_tier", "low") in ("auto", "low")
            and (a.get("estimated_cost") or 0) <= (budget_cap if budget_cap is not None else 50.0)
        )
    ]

    # Sort by priority descending
    eligible.sort(key=lambda a: a.get("priority_score", 0), reverse=True)

    # Select actions within constraints
    selected: List[Dict[str, Any]] = []
    cumulative_effort = 0.0
    cumulative_cost = 0.0

    for action in eligible:
        if len(selected) >= MAX_7DAY_ACTIONS:
            break

        effort = action.get("estimated_effort_hours") or 0.0
        cost = action.get("estimated_cost") or 0.0

        if cumulative_effort + effort > MAX_7DAY_EFFORT_HOURS:
            break
        if budget_cap is not None and cumulative_cost + cost > budget_cap:
            continue

        selected.append(copy.deepcopy(action))
        cumulative_effort += effort
        cumulative_cost += cost

    # Build expected outcomes
    expected_outcomes = [
        a.get("expected_outcome", a.get("title", ""))
        for a in selected
        if a.get("expected_outcome") or a.get("title")
    ]

    total_cost = sum(a.get("estimated_cost") or 0 for a in selected)
    total_effort = sum(a.get("estimated_effort_hours") or 0 for a in selected)

    summary = _generate_executive_summary(selected, "7_day")

    return {
        "id": f"bnd_{uuid.uuid4().hex[:12]}",
        "bundle_type": "7_day",
        "bundle_name": "Week 1 Quick Wins",
        "actions": selected,
        "total_estimated_cost": round(total_cost, 2),
        "total_estimated_effort_hours": round(total_effort, 2),
        "executive_summary": summary,
        "expected_outcomes": expected_outcomes,
        "weekly_milestones": {},
        "created_at": None,
        "metadata": {},
    }


# ============================================================================
# 30-Day Plan Bundle
# ============================================================================


def bundle_30day_plan(
    actions: List[Dict[str, Any]],
    budget_cap: Optional[float] = None,
    hours_per_week: float = 10.0,
) -> Dict[str, Any]:
    """Generate a 30-day improvement plan with weekly milestones.

    Actions are assigned to four weekly milestones based on risk profile,
    action type, and effort constraints.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    budget_cap:
        Maximum total cost for the entire plan.
    hours_per_week:
        Effort cap per week in hours.

    Returns
    -------
    dict
        A ProposalBundle-compatible dict with ``bundle_type: "30_day"``.
    """
    # Apply budget filter if needed
    if budget_cap is not None:
        viable = _respect_budget(actions, budget_cap)
    else:
        viable = [copy.deepcopy(a) for a in actions]

    # Sort by: actions with no depends_on first, then priority descending
    viable.sort(
        key=lambda a: (
            0 if not a.get("depends_on") else 1,
            -a.get("priority_score", 0),
        )
    )

    # Cap at MAX_30DAY_ACTIONS
    viable = viable[:MAX_30DAY_ACTIONS]

    # Assign actions to weeks
    weekly_actions: Dict[int, List[Dict[str, Any]]] = {1: [], 2: [], 3: [], 4: []}
    weekly_effort: Dict[int, float] = {1: 0.0, 2: 0.0, 3: 0.0, 4: 0.0}
    assigned_ids: set = set()

    for week_num in range(1, 5):
        rules = _WEEK_CATEGORY_RULES[week_num]
        risk_cap = rules["risk_cap"]
        preferred_types = rules["action_types"]

        # First pass: assign actions that fit this week's profile
        for action in viable:
            action_id = action.get("id", "")
            if action_id in assigned_ids:
                continue

            effort = action.get("estimated_effort_hours") or 0.0
            if weekly_effort[week_num] + effort > hours_per_week:
                continue

            risk = action.get("risk_tier", "low")
            action_type = action.get("action_type", "")

            # Check risk is within this week's tolerance
            if risk not in risk_cap:
                continue

            # Prefer actions that match this week's profile
            if action_type in preferred_types:
                weekly_actions[week_num].append(action)
                weekly_effort[week_num] += effort
                assigned_ids.add(action_id)

    # Second pass: fill remaining capacity with unassigned actions
    for action in viable:
        action_id = action.get("id", "")
        if action_id in assigned_ids:
            continue

        effort = action.get("estimated_effort_hours") or 0.0
        risk = action.get("risk_tier", "low")

        # Try to place in the earliest week with capacity and risk tolerance
        for week_num in range(1, 5):
            rules = _WEEK_CATEGORY_RULES[week_num]
            risk_cap = rules["risk_cap"]

            if risk not in risk_cap:
                continue
            if weekly_effort[week_num] + effort > hours_per_week:
                continue

            weekly_actions[week_num].append(action)
            weekly_effort[week_num] += effort
            assigned_ids.add(action_id)
            break

    # Build weekly milestones
    weekly_milestones: Dict[str, Dict[str, Any]] = {}
    all_selected: List[Dict[str, Any]] = []
    for week_num in range(1, 5):
        week_key = f"week_{week_num}"
        week_acts = weekly_actions[week_num]
        all_selected.extend(week_acts)

        weekly_milestones[week_key] = {
            "label": _WEEK_CATEGORY_RULES[week_num]["label"],
            "action_ids": [a.get("id", "") for a in week_acts],
            "action_titles": [a.get("title", "") for a in week_acts],
            "effort_hours": round(weekly_effort[week_num], 2),
            "milestone_description": (
                f"{_WEEK_CATEGORY_RULES[week_num]['label']}: "
                f"{len(week_acts)} actions, "
                f"{round(weekly_effort[week_num], 1)}h effort"
            ),
        }

    total_cost = sum(a.get("estimated_cost") or 0 for a in all_selected)
    total_effort = sum(a.get("estimated_effort_hours") or 0 for a in all_selected)

    summary = _generate_executive_summary(all_selected, "30_day")
    expected_outcomes = _derive_expected_outcomes(all_selected)

    return {
        "id": f"bnd_{uuid.uuid4().hex[:12]}",
        "bundle_type": "30_day",
        "bundle_name": "30-Day Marketing Improvement Plan",
        "actions": all_selected,
        "total_estimated_cost": round(total_cost, 2),
        "total_estimated_effort_hours": round(total_effort, 2),
        "executive_summary": summary,
        "expected_outcomes": expected_outcomes,
        "weekly_milestones": weekly_milestones,
        "created_at": None,
        "metadata": {"hours_per_week": hours_per_week},
    }


# ============================================================================
# Campaign Pack Bundle
# ============================================================================


def bundle_campaign_pack(
    actions: List[Dict[str, Any]],
    campaign_theme: str,
) -> Optional[Dict[str, Any]]:
    """Group actions into a thematic campaign bundle.

    Matches actions to the requested theme by checking ``action_type``
    and ``tags``.  Returns ``None`` if fewer than
    ``CAMPAIGN_MIN_ACTIONS`` match.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    campaign_theme:
        One of the supported campaign themes (e.g.,
        ``"review_generation"``, ``"lead_capture"``).

    Returns
    -------
    dict or None
        A ProposalBundle-compatible dict with ``bundle_type: "campaign"``,
        or ``None`` if not enough actions match.
    """
    theme_config = _CAMPAIGN_THEMES.get(campaign_theme)
    if theme_config is None:
        return None

    target_types = theme_config["action_types"]
    target_tags = theme_config["tag_patterns"]

    # Score each action for theme relevance
    scored: List[tuple] = []
    for action in actions:
        action_type = action.get("action_type", "")
        action_tags = set(action.get("tags", []))

        type_match = action_type in target_types
        tag_overlap = len(action_tags & target_tags)

        if type_match or tag_overlap > 0:
            relevance = (1 if type_match else 0) + tag_overlap
            scored.append((relevance, action.get("priority_score", 0), action))

    if len(scored) < CAMPAIGN_MIN_ACTIONS:
        return None

    # Sort by relevance descending, then priority descending
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

    # Cap at CAMPAIGN_MAX_ACTIONS
    selected = [copy.deepcopy(item[2]) for item in scored[:CAMPAIGN_MAX_ACTIONS]]

    # Sort selected by dependency then priority for execution order
    selected.sort(
        key=lambda a: (
            0 if not a.get("depends_on") else 1,
            -a.get("priority_score", 0),
        )
    )

    total_cost = sum(a.get("estimated_cost") or 0 for a in selected)
    total_effort = sum(a.get("estimated_effort_hours") or 0 for a in selected)
    display_name = campaign_theme.replace("_", " ").title()

    summary = _generate_executive_summary(selected, "campaign")
    expected_outcomes = _derive_expected_outcomes(selected)

    return {
        "id": f"bnd_{uuid.uuid4().hex[:12]}",
        "bundle_type": "campaign",
        "bundle_name": f"{display_name} Campaign",
        "actions": selected,
        "total_estimated_cost": round(total_cost, 2),
        "total_estimated_effort_hours": round(total_effort, 2),
        "executive_summary": summary,
        "expected_outcomes": expected_outcomes,
        "weekly_milestones": {},
        "created_at": None,
        "metadata": {"campaign_theme": campaign_theme},
    }


# ============================================================================
# Monthly Operating Plan Bundle
# ============================================================================


def bundle_monthly_operating_plan(
    actions: List[Dict[str, Any]],
    recurring_actions: Optional[List[Dict[str, Any]]] = None,
    budget_cap: Optional[float] = None,
) -> Dict[str, Any]:
    """Generate a monthly operating plan with recurring + one-time items.

    Combines recurring maintenance activities with one-time improvements
    and includes measurement checkpoints at weeks 2 and 4.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts (one-time improvements).
    recurring_actions:
        Optional list of recurring action dicts.  If not provided,
        stub recurring items are generated based on action types present.
    budget_cap:
        Maximum total cost for the month.

    Returns
    -------
    dict
        A ProposalBundle-compatible dict with
        ``bundle_type: "monthly_operating"``.
    """
    # Generate recurring stubs if not provided
    if recurring_actions is None:
        recurring_actions = _generate_recurring_stubs(actions)

    # Apply budget filter to one-time actions
    one_time = list(actions)
    if budget_cap is not None:
        one_time_cost = sum(a.get("estimated_cost") or 0 for a in one_time)
        recurring_cost = sum(a.get("estimated_cost") or 0 for a in recurring_actions)
        remaining = budget_cap - recurring_cost
        if remaining > 0:
            one_time = _respect_budget(one_time, remaining)
        else:
            one_time = [a for a in one_time if (a.get("estimated_cost") or 0) == 0]

    # Sort one-time actions by priority
    one_time.sort(key=lambda a: a.get("priority_score", 0), reverse=True)

    # Distribute across 4 weeks
    weekly_milestones: Dict[str, Dict[str, Any]] = {}
    all_actions: List[Dict[str, Any]] = []

    recurring_per_week = [copy.deepcopy(r) for r in recurring_actions]
    one_time_queue = [copy.deepcopy(a) for a in one_time]

    for week_num in range(1, 5):
        week_key = f"week_{week_num}"
        week_actions: List[Dict[str, Any]] = []

        # Add recurring actions to every week
        for r in recurring_per_week:
            tagged = copy.deepcopy(r)
            tagged.setdefault("metadata", {})
            tagged["metadata"]["recurring"] = True
            tagged["metadata"]["scheduled_week"] = week_num
            week_actions.append(tagged)

        # Add one-time improvements (distribute evenly)
        items_per_week = max(1, len(one_time_queue) // (5 - week_num)) if one_time_queue else 0
        for _ in range(items_per_week):
            if one_time_queue:
                item = one_time_queue.pop(0)
                item.setdefault("metadata", {})
                item["metadata"]["scheduled_week"] = week_num
                week_actions.append(item)

        all_actions.extend(week_actions)

        # Build milestone description
        recurring_count = len(recurring_per_week)
        one_time_count = len(week_actions) - recurring_count

        milestone_parts = [f"{recurring_count} recurring"]
        if one_time_count > 0:
            milestone_parts.append(f"{one_time_count} improvement{'s' if one_time_count != 1 else ''}")

        weekly_milestones[week_key] = {
            "label": f"Week {week_num}",
            "action_ids": [a.get("id", "") for a in week_actions],
            "action_titles": [a.get("title", "") for a in week_actions],
            "effort_hours": round(sum(a.get("estimated_effort_hours") or 0 for a in week_actions), 2),
            "milestone_description": f"Week {week_num}: {', '.join(milestone_parts)}",
        }

    # Measurement checkpoints
    measurement_checkpoints = [
        {
            "week": 2,
            "label": "Mid-Month Check",
            "metrics": [
                "Website traffic vs. previous period",
                "Lead form submission count",
                "Phone call volume",
                "Review count and average rating",
                "Email open and click rates",
            ],
        },
        {
            "week": 4,
            "label": "Month-End Review",
            "metrics": [
                "Total leads generated (all channels)",
                "Cost per lead by channel",
                "Website conversion rate change",
                "Google Business Profile views and actions",
                "Revenue attributed to marketing",
                "Tasks completed vs. planned",
            ],
        },
    ]

    total_cost = sum(a.get("estimated_cost") or 0 for a in all_actions)
    total_effort = sum(a.get("estimated_effort_hours") or 0 for a in all_actions)

    summary = _generate_executive_summary(all_actions, "monthly_operating")

    return {
        "id": f"bnd_{uuid.uuid4().hex[:12]}",
        "bundle_type": "monthly_operating",
        "bundle_name": "Monthly Marketing Operating Plan",
        "actions": all_actions,
        "total_estimated_cost": round(total_cost, 2),
        "total_estimated_effort_hours": round(total_effort, 2),
        "executive_summary": summary,
        "expected_outcomes": [
            "Consistent brand presence across active channels",
            "Steady lead flow from organic and direct channels",
            "Review velocity maintained or improved",
            "Performance data collected for next month's optimization",
        ],
        "weekly_milestones": weekly_milestones,
        "measurement_checkpoints": measurement_checkpoints,
        "created_at": None,
        "metadata": {},
    }


# ============================================================================
# Auto-Bundle Orchestrator
# ============================================================================


def auto_bundle(
    actions: List[Dict[str, Any]],
    business_profile: Optional[Dict[str, Any]] = None,
    budget_cap: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Generate all applicable bundles from an action list.

    Produces:
    1. A 7-day quick wins bundle (always).
    2. A 30-day plan (always).
    3. Campaign packs for each detected theme.
    4. A monthly operating plan (always).

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    business_profile:
        Optional business profile dict for extracting budget and
        hours constraints.
    budget_cap:
        Explicit budget cap.  Overrides profile-derived budget.

    Returns
    -------
    list[dict]
        List of ProposalBundle-compatible dicts.
    """
    if business_profile is None:
        business_profile = {}

    # Extract constraints from business profile
    if budget_cap is None:
        budget_info = business_profile.get("budget", business_profile.get("budget_and_risk", {}))
        if isinstance(budget_info, dict):
            budget_cap = budget_info.get("monthly_marketing_budget")

    operator_info = business_profile.get("operator", business_profile.get("operator_capacity", {}))
    hours_per_week = 10.0
    if isinstance(operator_info, dict):
        hours_per_week = operator_info.get("operator_hours_per_week", 10.0)

    bundles: List[Dict[str, Any]] = []

    # 1. 7-day quick wins
    quick_wins = bundle_7day_quick_wins(actions, budget_cap=budget_cap)
    if quick_wins.get("actions"):
        bundles.append(quick_wins)

    # 2. 30-day plan
    plan_30 = bundle_30day_plan(actions, budget_cap=budget_cap, hours_per_week=hours_per_week)
    if plan_30.get("actions"):
        bundles.append(plan_30)

    # 3. Campaign packs for detected themes
    detected_themes = _detect_campaign_themes(actions)
    for theme in detected_themes:
        pack = bundle_campaign_pack(actions, campaign_theme=theme)
        if pack is not None:
            bundles.append(pack)

    # 4. Monthly operating plan
    monthly = bundle_monthly_operating_plan(actions, budget_cap=budget_cap)
    if monthly.get("actions"):
        bundles.append(monthly)

    return bundles


# ============================================================================
# Internal helpers
# ============================================================================


def _generate_executive_summary(
    actions: List[Dict[str, Any]],
    bundle_type: str,
) -> str:
    """Generate a 3-5 sentence executive summary for a bundle.

    Mentions action count, total effort, total cost, top categories,
    and expected primary outcome.  Uses plain operator-friendly language.
    """
    if not actions:
        return "No actions are included in this bundle."

    count = len(actions)
    total_effort = sum(a.get("estimated_effort_hours") or 0 for a in actions)
    total_cost = sum(a.get("estimated_cost") or 0 for a in actions)

    # Identify top categories
    categories: Dict[str, int] = defaultdict(int)
    for action in actions:
        meta = action.get("metadata", {})
        cat = meta.get("finding_category", action.get("channel", "general"))
        categories[cat] += 1

    top_cats = sorted(categories.items(), key=lambda x: x[1], reverse=True)[:3]
    cat_names = [cat.replace("_", " ") for cat, _ in top_cats]

    # Bundle-type-specific framing
    if bundle_type == "7_day":
        intro = (
            f"This bundle contains {count} quick wins that can be completed "
            f"in {round(total_effort, 1)} hours"
        )
    elif bundle_type == "30_day":
        intro = (
            f"This 30-day plan includes {count} actions spread across 4 weekly "
            f"milestones, requiring approximately {round(total_effort, 1)} total hours"
        )
    elif bundle_type == "campaign":
        intro = (
            f"This campaign bundles {count} coordinated actions requiring "
            f"{round(total_effort, 1)} hours of effort"
        )
    elif bundle_type == "monthly_operating":
        intro = (
            f"This monthly operating plan includes {count} actions combining "
            f"recurring maintenance with targeted improvements, totaling "
            f"{round(total_effort, 1)} hours"
        )
    else:
        intro = f"This bundle contains {count} actions requiring {round(total_effort, 1)} hours"

    # Cost portion
    if total_cost > 0:
        intro += f" with ${round(total_cost, 2)} in estimated spend"
    else:
        intro += " with no additional spend required"

    # Categories
    if cat_names:
        focus = ", ".join(cat_names)
        intro += f". Focus areas: {focus}."
    else:
        intro += "."

    # Closing sentence
    risk_counts: Dict[str, int] = defaultdict(int)
    for action in actions:
        risk_counts[action.get("risk_tier", "low")] += 1

    low_risk_pct = (
        (risk_counts.get("auto", 0) + risk_counts.get("low", 0)) / count * 100
        if count > 0 else 0
    )

    if low_risk_pct >= 80:
        closing = "Most actions are low-risk and can be batch-approved."
    elif low_risk_pct >= 50:
        closing = "The plan mixes quick wins with some actions that need individual review."
    else:
        closing = "Several actions require individual operator approval before execution."

    return f"{intro} {closing}"


def _detect_campaign_themes(actions: List[Dict[str, Any]]) -> List[str]:
    """Detect which campaign themes have enough matching actions.

    Returns theme names where at least ``CAMPAIGN_MIN_ACTIONS`` actions
    match by action type or tags.
    """
    detected: List[str] = []

    for theme_name, theme_config in _CAMPAIGN_THEMES.items():
        target_types = theme_config["action_types"]
        target_tags = theme_config["tag_patterns"]

        match_count = 0
        for action in actions:
            action_type = action.get("action_type", "")
            action_tags = set(action.get("tags", []))

            if action_type in target_types or (action_tags & target_tags):
                match_count += 1

        if match_count >= CAMPAIGN_MIN_ACTIONS:
            detected.append(theme_name)

    return detected


def _respect_budget(
    actions: List[Dict[str, Any]],
    budget_cap: float,
) -> List[Dict[str, Any]]:
    """Filter actions to stay within budget, prioritizing highest-scored.

    Actions are sorted by ``priority_score`` descending.  The first
    actions whose cumulative cost fits within *budget_cap* are kept.
    Free actions (cost == 0) are always included.
    """
    sorted_actions = sorted(
        actions, key=lambda a: a.get("priority_score", 0), reverse=True
    )

    kept: List[Dict[str, Any]] = []
    cumulative_cost = 0.0

    for action in sorted_actions:
        cost = action.get("estimated_cost") or 0.0
        if cost == 0:
            kept.append(copy.deepcopy(action))
            continue
        if cumulative_cost + cost <= budget_cap:
            kept.append(copy.deepcopy(action))
            cumulative_cost += cost

    return kept


def _derive_expected_outcomes(actions: List[Dict[str, Any]]) -> List[str]:
    """Derive a list of expected outcomes from the actions.

    Uses action ``expected_outcome`` fields when available, falls back
    to generating generic outcomes from action types.
    """
    outcomes: List[str] = []
    seen: set = set()

    for action in actions:
        outcome = action.get("expected_outcome", "")
        if outcome and outcome not in seen:
            outcomes.append(outcome)
            seen.add(outcome)

    # Add generic outcomes if we have few specifics
    if len(outcomes) < 3:
        type_outcomes = {
            "website_update": "Improved website conversion rate",
            "seo_fix": "Better search engine visibility",
            "content_creation": "Expanded content library and topical authority",
            "email_sequence": "Automated lead nurture increasing conversion",
            "ad_campaign": "New paid acquisition channel generating leads",
            "review_request": "Increased review volume and average rating",
            "gbp_update": "Improved local search presence",
            "kaicalls_setup": "Automated phone lead capture reducing missed opportunities",
            "social_post": "Increased brand awareness and social engagement",
            "analytics_fix": "Accurate marketing attribution and measurement",
        }
        for action in actions:
            action_type = action.get("action_type", "")
            generic = type_outcomes.get(action_type)
            if generic and generic not in seen:
                outcomes.append(generic)
                seen.add(generic)

    return outcomes[:8]  # Cap at 8 outcomes


def _generate_recurring_stubs(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Generate stub recurring actions based on action types present.

    Examines the one-time action list to infer what recurring maintenance
    the business needs.
    """
    types_present = {a.get("action_type", "") for a in actions}
    channels_present = {a.get("channel", "") for a in actions}
    stubs: List[Dict[str, Any]] = []

    # Social posting if any social actions exist
    if "social_post" in types_present or "social" in channels_present:
        stubs.append({
            "id": f"rec_{uuid.uuid4().hex[:12]}",
            "action_type": "social_post",
            "channel": "social",
            "title": "Weekly social media posting",
            "description": "Maintain consistent social media presence with 3-5 posts per week across active platforms.",
            "estimated_effort_hours": 2.0,
            "estimated_cost": 0.0,
            "risk_tier": "low",
            "priority_score": 40.0,
            "tags": ["recurring", "social"],
            "metadata": {"recurring": True, "frequency": "weekly"},
        })

    # GBP posting if any GBP actions exist
    if "gbp_update" in types_present or "gbp" in channels_present:
        stubs.append({
            "id": f"rec_{uuid.uuid4().hex[:12]}",
            "action_type": "gbp_update",
            "channel": "gbp",
            "title": "Weekly Google Business Profile post",
            "description": "Publish a weekly GBP post with updates, offers, or tips to maintain profile freshness.",
            "estimated_effort_hours": 0.5,
            "estimated_cost": 0.0,
            "risk_tier": "low",
            "priority_score": 35.0,
            "tags": ["recurring", "gbp"],
            "metadata": {"recurring": True, "frequency": "weekly"},
        })

    # Review monitoring if any review actions exist
    if "review_request" in types_present or "reputation_action" in types_present:
        stubs.append({
            "id": f"rec_{uuid.uuid4().hex[:12]}",
            "action_type": "reputation_action",
            "channel": "gbp",
            "title": "Weekly review monitoring and response",
            "description": "Check for new reviews, respond promptly, and flag any negative reviews for follow-up.",
            "estimated_effort_hours": 0.5,
            "estimated_cost": 0.0,
            "risk_tier": "low",
            "priority_score": 45.0,
            "tags": ["recurring", "reviews"],
            "metadata": {"recurring": True, "frequency": "weekly"},
        })

    # Email engagement check if any email actions exist
    if "email_sequence" in types_present or "email" in channels_present:
        stubs.append({
            "id": f"rec_{uuid.uuid4().hex[:12]}",
            "action_type": "analytics_fix",
            "channel": "email",
            "title": "Weekly email performance check",
            "description": "Review email open rates, click rates, and unsubscribe rates.  Adjust sequences if metrics decline.",
            "estimated_effort_hours": 0.5,
            "estimated_cost": 0.0,
            "risk_tier": "auto",
            "priority_score": 30.0,
            "tags": ["recurring", "email", "analytics"],
            "metadata": {"recurring": True, "frequency": "weekly"},
        })

    # Analytics check-in (always include)
    stubs.append({
        "id": f"rec_{uuid.uuid4().hex[:12]}",
        "action_type": "analytics_fix",
        "channel": "analytics",
        "title": "Weekly analytics check-in",
        "description": "Review website traffic, conversion rates, and lead volume.  Note trends and anomalies.",
        "estimated_effort_hours": 0.5,
        "estimated_cost": 0.0,
        "risk_tier": "auto",
        "priority_score": 30.0,
        "tags": ["recurring", "analytics"],
        "metadata": {"recurring": True, "frequency": "weekly"},
    })

    return stubs
