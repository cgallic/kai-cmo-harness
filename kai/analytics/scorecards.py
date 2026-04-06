"""Scorecards and dashboard summary objects for the Kai Marketing OS.

Operators need a single-glance view of marketing health.  Instead of
dumping 15 KPIs at them, the scorecard system groups metrics into five
strategic categories:

1. **Visibility** -- "Are we being found?"
2. **Lead Flow** -- "Are leads coming in?"
3. **Conversions** -- "Are leads turning into customers?"
4. **Repeat Business** -- "Are customers coming back?"
5. **Spend Efficiency** -- "Are we getting good return on ad spend?"

Each scorecard scores its metrics 0-100, and the ``DashboardSummary``
rolls everything up into an overall health score.

This module is purely data models and scoring functions.  It makes no
API calls and has no external dependencies beyond stdlib and project
modules.

Downstream consumers:

- ``kai.gateway.routers`` -- renders dashboards via the API
- ``kai.analytics.watchers`` -- uses scorecard health for alert logic
- Weekly digest notifications (task 072)

Usage::

    from kai.analytics.scorecards import (
        build_dashboard_summary,
        build_visibility_scorecard,
        DashboardSummary,
        Scorecard,
        ScorecardHealth,
    )

    summary = build_dashboard_summary(
        business_id="biz-001",
        business_name="Acme Plumbing",
        archetype="local_service",
        kpi_values=kpis,
        targets=targets,
        benchmarks=benchmarks,
        channel_data=channels,
        period_start="2026-03-01",
        period_end="2026-03-31",
    )
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from kai.runtime.models import SerializableModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ScorecardHealth(str, Enum):
    """Health tier derived from a scorecard's 0-100 score."""

    EXCELLENT = "excellent"        # 80-100
    GOOD = "good"                  # 60-79
    NEEDS_ATTENTION = "needs_attention"  # 40-59
    POOR = "poor"                  # 20-39
    CRITICAL = "critical"          # 0-19


def _score_to_health(score: float) -> str:
    """Map a 0-100 numeric score to a ``ScorecardHealth`` value."""
    if score >= 80:
        return ScorecardHealth.EXCELLENT.value
    elif score >= 60:
        return ScorecardHealth.GOOD.value
    elif score >= 40:
        return ScorecardHealth.NEEDS_ATTENTION.value
    elif score >= 20:
        return ScorecardHealth.POOR.value
    else:
        return ScorecardHealth.CRITICAL.value


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


@dataclass
class ScorecardMetric(SerializableModel):
    """A single metric within a scorecard category.

    Attributes:
        metric_name: Machine-readable identifier.
        display_name: Human-readable label for dashboards.
        value: Current observed value, or ``None`` if unavailable.
        target: Target value to score against, or ``None``.
        benchmark: Industry benchmark, or ``None``.
        weight: How much this metric contributes to the scorecard score
            (0.0-1.0).  Weights within a scorecard should sum to 1.0.
        score_contribution: This metric's weighted contribution to the
            category score after scoring.
        trend: Direction of recent change: ``"up"``, ``"down"``,
            ``"flat"``, or ``"new"``.
        trend_value: Percent change driving the trend.
    """

    metric_name: str = ""
    display_name: str = ""
    value: Optional[float] = None
    target: Optional[float] = None
    benchmark: Optional[float] = None
    weight: float = 0.0
    score_contribution: Optional[float] = None
    trend: Optional[str] = None
    trend_value: Optional[float] = None


@dataclass
class Scorecard(SerializableModel):
    """A scored category of marketing metrics.

    Attributes:
        category: One of ``"visibility"``, ``"lead_flow"``,
            ``"conversions"``, ``"repeat_business"``,
            ``"spend_efficiency"``.
        display_name: Human-readable category name.
        description: The strategic question this scorecard answers.
        score: Composite 0-100 score for this category.
        health: ``ScorecardHealth`` enum value.
        metrics: The individual metrics that compose this scorecard.
        top_insight: Single-sentence summary of the most important
            finding within this category.
        recommended_actions: 1-3 specific actions to improve this score.
    """

    category: str = ""
    display_name: str = ""
    description: str = ""
    score: float = 0.0
    health: str = ScorecardHealth.CRITICAL.value
    metrics: List[ScorecardMetric] = field(default_factory=list)
    top_insight: str = ""
    recommended_actions: List[str] = field(default_factory=list)


@dataclass
class ChannelRollup(SerializableModel):
    """Aggregated performance data for a single marketing channel.

    Attributes:
        channel: Channel identifier (e.g., ``"organic_search"``,
            ``"paid_search"``).
        sessions: Total sessions from this channel.
        leads: Total leads attributed to this channel.
        conversions: Total conversions attributed to this channel.
        spend: Total spend in this channel (USD).
        revenue: Total revenue attributed to this channel (USD).
        roas: Return on ad spend (revenue / spend).
        conversion_rate: Conversions / sessions as a ratio.
        cost_per_lead: Spend / leads.
        health: ``ScorecardHealth`` value derived from channel
            performance vs targets.
    """

    channel: str = ""
    sessions: Optional[float] = None
    leads: Optional[float] = None
    conversions: Optional[float] = None
    spend: Optional[float] = None
    revenue: Optional[float] = None
    roas: Optional[float] = None
    conversion_rate: Optional[float] = None
    cost_per_lead: Optional[float] = None
    health: str = ScorecardHealth.NEEDS_ATTENTION.value


@dataclass
class DashboardSummary(SerializableModel):
    """Top-level executive summary of marketing health.

    Aggregates the five category scorecards, channel rollups, and
    period-over-period comparison into a single object that drives the
    operator dashboard.

    Attributes:
        business_id: Unique identifier for the business.
        business_name: Display name.
        archetype: Business archetype slug.
        generated_at: ISO timestamp when this summary was generated.
        period_start: ISO date for the start of the reporting period.
        period_end: ISO date for the end of the reporting period.
        overall_health_score: 0-100 weighted average of all scorecard
            scores.
        overall_health: ``ScorecardHealth`` enum value.
        scorecards: The five category scorecards.
        channel_rollups: Per-channel performance rollups.
        top_3_wins: Best-performing areas.
        top_3_concerns: Areas needing attention.
        recommended_next_actions: Prioritized list of what to do next.
        period_comparison: Comparison with the previous period, or
            ``None`` if no previous data.
    """

    business_id: str = ""
    business_name: str = ""
    archetype: str = ""
    generated_at: str = ""
    period_start: str = ""
    period_end: str = ""
    overall_health_score: float = 0.0
    overall_health: str = ScorecardHealth.CRITICAL.value
    scorecards: List[Scorecard] = field(default_factory=list)
    channel_rollups: List[ChannelRollup] = field(default_factory=list)
    top_3_wins: List[str] = field(default_factory=list)
    top_3_concerns: List[str] = field(default_factory=list)
    recommended_next_actions: List[str] = field(default_factory=list)
    period_comparison: Optional[Dict[str, Any]] = None


# ============================================================================
# Scoring helpers
# ============================================================================


def _score_metric_higher_is_better(
    value: Optional[float],
    target: Optional[float],
) -> Optional[float]:
    """Score a higher-is-better metric as a 0-100 value.

    Returns ``min(100, (value / target) * 100)`` or ``None`` when either
    ``value`` or ``target`` is unavailable or target is zero.
    """
    if value is None or target is None or target <= 0:
        return None
    return min(100.0, (value / target) * 100.0)


def _score_metric_lower_is_better(
    value: Optional[float],
    target: Optional[float],
) -> Optional[float]:
    """Score a lower-is-better metric as a 0-100 value.

    Returns ``min(100, (target / value) * 100)`` or ``None`` when either
    ``value`` or ``target`` is unavailable or value is zero.
    """
    if value is None or target is None or value <= 0:
        return None
    return min(100.0, (target / value) * 100.0)


def _build_scorecard_metrics(
    metric_specs: List[Dict[str, Any]],
    kpi_values: Dict[str, float],
    targets: Dict[str, float],
    benchmarks: Dict[str, float],
) -> List[ScorecardMetric]:
    """Build a list of ``ScorecardMetric`` from a spec list.

    Each spec dict must contain ``name``, ``display_name``, ``weight``,
    and ``inverted`` (bool, True for lower-is-better metrics).
    """
    metrics: List[ScorecardMetric] = []
    for spec in metric_specs:
        name = spec["name"]
        value = kpi_values.get(name)
        target = targets.get(name)
        benchmark = benchmarks.get(name)
        inverted = spec.get("inverted", False)

        if inverted:
            raw_score = _score_metric_lower_is_better(value, target)
        else:
            raw_score = _score_metric_higher_is_better(value, target)

        # Determine trend from kpi_values hints if present
        trend_key = f"{name}_trend"
        trend_value = kpi_values.get(trend_key)
        if trend_value is not None:
            if trend_value > 1.0:
                trend = "up"
            elif trend_value < -1.0:
                trend = "down"
            else:
                trend = "flat"
        else:
            trend = None

        weight = spec["weight"]
        score_contribution = (raw_score * weight) if raw_score is not None else None

        metrics.append(
            ScorecardMetric(
                metric_name=name,
                display_name=spec["display_name"],
                value=value,
                target=target,
                benchmark=benchmark,
                weight=weight,
                score_contribution=round(score_contribution, 2) if score_contribution is not None else None,
                trend=trend,
                trend_value=round(trend_value, 2) if trend_value is not None else None,
            )
        )
    return metrics


def _compute_scorecard_score(metrics: List[ScorecardMetric]) -> float:
    """Compute the weighted score from a list of scorecard metrics.

    Metrics with ``None`` values are excluded.  The remaining metrics
    have their weights re-normalised so they sum to 1.0, preventing
    missing data from deflating the score.

    Returns 0.0 if no metrics have data.
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for m in metrics:
        if m.score_contribution is not None and m.value is not None:
            weighted_sum += m.score_contribution
            total_weight += m.weight

    if total_weight == 0.0:
        return 0.0

    # Re-normalise: the metric weights may not sum to 1.0 if some
    # metrics were excluded.  Scale up to compensate.
    raw = weighted_sum / total_weight
    return round(min(100.0, max(0.0, raw)), 1)


def _generate_top_insight(metrics: List[ScorecardMetric]) -> str:
    """Generate a single-sentence insight from the scorecard metrics.

    Identifies the metric with the largest gap between value and target
    and produces a human-readable sentence.
    """
    largest_gap_metric: Optional[ScorecardMetric] = None
    largest_gap = 0.0

    for m in metrics:
        if m.value is not None and m.target is not None and m.target > 0:
            gap = abs(m.value - m.target) / m.target
            if gap > largest_gap:
                largest_gap = gap
                largest_gap_metric = m

    if largest_gap_metric is None:
        return "Insufficient data to generate insights."

    m = largest_gap_metric
    if m.value is not None and m.target is not None:
        if m.value >= m.target:
            pct_over = ((m.value - m.target) / m.target) * 100.0
            return (
                f"{m.display_name} is {pct_over:.0f}% above target "
                f"({m.value:.0f} vs {m.target:.0f} target)."
            )
        else:
            pct_below = ((m.target - m.value) / m.target) * 100.0
            return (
                f"{m.display_name} is {pct_below:.0f}% below target "
                f"({m.value:.0f} vs {m.target:.0f} target) -- "
                f"this is the biggest gap to close."
            )

    return "Insufficient data to generate insights."


def _generate_recommended_actions(
    metrics: List[ScorecardMetric],
    category: str,
) -> List[str]:
    """Generate 1-3 recommended actions based on lowest-scoring metrics.

    Each recommendation is a concrete, actionable sentence.
    """
    # Collect scored metrics and sort by contribution (lowest first)
    scored = [
        m for m in metrics
        if m.score_contribution is not None and m.value is not None
    ]
    scored.sort(key=lambda m: m.score_contribution or 0.0)

    # Action templates per metric category
    action_templates: Dict[str, str] = {
        # Visibility
        "search_impressions": "Publish 2-3 SEO-optimized blog posts targeting high-volume keywords to increase search impressions.",
        "gbp_views": "Update Google Business Profile with fresh photos, posts, and Q&A responses to boost local visibility.",
        "social_reach": "Increase social posting frequency to 5x/week and test short-form video content for broader reach.",
        "direct_traffic": "Run a branded awareness campaign or PR push to increase direct traffic from brand recognition.",
        "brand_search_volume": "Invest in brand-building content (podcasts, guest posts, PR) to grow branded search demand.",
        # Lead flow
        "total_leads": "Add a secondary lead capture mechanism (chat widget or phone-based CTA) to increase total lead volume.",
        "cost_per_lead": "Pause underperforming ad campaigns and reallocate budget to the top 2 lowest-CPL channels.",
        "lead_sources_diversity": "Activate at least one new lead generation channel (email, referral program, or social ads).",
        "phone_calls": "Add click-to-call CTAs above the fold on all service pages and set up KaiCalls AI receptionist for after-hours coverage.",
        "lead_quality_indicator": "Tighten lead qualification criteria in forms and ad targeting to improve lead quality ratio.",
        # Conversions
        "website_conversion_rate": "A/B test the primary CTA on the homepage and top 3 landing pages to improve conversion rate.",
        "landing_page_conversion_rate": "Simplify landing page forms to 3-4 fields and add social proof (reviews, logos) above the fold.",
        "form_completion_rate": "Reduce form fields, add progress indicators, and implement autofill to improve form completion.",
        "phone_call_rate": "Make phone numbers prominent on mobile, add sticky call bars, and implement KaiCalls for instant response.",
        "speed_to_lead": "Set up automated instant-response emails and consider KaiCalls AI receptionist for immediate phone follow-up.",
        # Repeat business
        "repeat_customer_rate": "Launch a post-service follow-up email sequence with maintenance reminders and seasonal offers.",
        "customer_retention_rate": "Implement a loyalty program or VIP tier system to incentivize repeat purchases.",
        "ltv_trend": "Create upsell and cross-sell campaigns targeting existing customers with complementary services.",
        "referral_rate": "Launch a referral program offering incentives for both the referrer and the new customer.",
        "review_rating": "Automate review request emails sent 24-48 hours after service completion to boost ratings volume.",
        # Spend efficiency
        "overall_roas": "Shift 20% of budget from lowest-ROAS channel to highest-ROAS channel and monitor for 14 days.",
        "cpa_trend": "Review audience targeting on highest-CPA campaigns and test lookalike audiences from best customers.",
        "budget_utilization": "Review and adjust campaign budgets and bidding strategies to ensure full budget utilization.",
        "per_channel_roas_best": "Double down on the highest-performing channel by increasing its budget allocation by 25%.",
        "wasted_spend_pct": "Add negative keywords, tighten geo-targeting, and pause zero-conversion ad groups to reduce waste.",
    }

    actions: List[str] = []
    for m in scored[:3]:
        template = action_templates.get(m.metric_name)
        if template:
            actions.append(template)
        else:
            actions.append(
                f"Investigate and improve {m.display_name} -- "
                f"currently at {m.value:.0f} against a target of {m.target:.0f}."
                if m.value is not None and m.target is not None
                else f"Collect data for {m.display_name} to enable scoring."
            )

    if not actions:
        actions.append(
            f"Collect baseline data for all {category} metrics to enable scoring."
        )

    return actions


# ============================================================================
# Scorecard builders
# ============================================================================


_VISIBILITY_METRICS = [
    {"name": "search_impressions", "display_name": "Search Impressions", "weight": 0.25, "inverted": False},
    {"name": "gbp_views", "display_name": "GBP Views", "weight": 0.25, "inverted": False},
    {"name": "social_reach", "display_name": "Social Reach", "weight": 0.15, "inverted": False},
    {"name": "direct_traffic", "display_name": "Direct Traffic", "weight": 0.15, "inverted": False},
    {"name": "brand_search_volume", "display_name": "Brand Search Volume", "weight": 0.20, "inverted": False},
]

_LEAD_FLOW_METRICS = [
    {"name": "total_leads", "display_name": "Total Leads", "weight": 0.30, "inverted": False},
    {"name": "cost_per_lead", "display_name": "Cost Per Lead", "weight": 0.25, "inverted": True},
    {"name": "lead_sources_diversity", "display_name": "Lead Source Diversity", "weight": 0.15, "inverted": False},
    {"name": "phone_calls", "display_name": "Phone Calls", "weight": 0.15, "inverted": False},
    {"name": "lead_quality_indicator", "display_name": "Lead Quality", "weight": 0.15, "inverted": False},
]

_CONVERSION_METRICS = [
    {"name": "website_conversion_rate", "display_name": "Website Conversion Rate", "weight": 0.30, "inverted": False},
    {"name": "landing_page_conversion_rate", "display_name": "Landing Page Conversion Rate", "weight": 0.25, "inverted": False},
    {"name": "form_completion_rate", "display_name": "Form Completion Rate", "weight": 0.15, "inverted": False},
    {"name": "phone_call_rate", "display_name": "Phone Call Rate", "weight": 0.15, "inverted": False},
    {"name": "speed_to_lead", "display_name": "Speed to Lead", "weight": 0.15, "inverted": True},
]

_REPEAT_BUSINESS_METRICS = [
    {"name": "repeat_customer_rate", "display_name": "Repeat Customer Rate", "weight": 0.25, "inverted": False},
    {"name": "customer_retention_rate", "display_name": "Customer Retention Rate", "weight": 0.25, "inverted": False},
    {"name": "ltv_trend", "display_name": "LTV Trend", "weight": 0.20, "inverted": False},
    {"name": "referral_rate", "display_name": "Referral Rate", "weight": 0.15, "inverted": False},
    {"name": "review_rating", "display_name": "Review Rating", "weight": 0.15, "inverted": False},
]

_SPEND_EFFICIENCY_METRICS = [
    {"name": "overall_roas", "display_name": "Overall ROAS", "weight": 0.30, "inverted": False},
    {"name": "cpa_trend", "display_name": "CPA Trend", "weight": 0.25, "inverted": True},
    {"name": "budget_utilization", "display_name": "Budget Utilization", "weight": 0.20, "inverted": False},
    {"name": "per_channel_roas_best", "display_name": "Best Channel ROAS", "weight": 0.15, "inverted": False},
    {"name": "wasted_spend_pct", "display_name": "Wasted Spend %", "weight": 0.10, "inverted": True},
]


def build_visibility_scorecard(
    kpi_values: Dict[str, float],
    targets: Dict[str, float],
    benchmarks: Dict[str, float],
) -> Scorecard:
    """Build the Visibility scorecard.

    Answers: *"Are we being found by potential customers?"*

    Metrics (weights summing to 1.0):
        - ``search_impressions`` (0.25)
        - ``gbp_views`` (0.25)
        - ``social_reach`` (0.15)
        - ``direct_traffic`` (0.15)
        - ``brand_search_volume`` (0.20)
    """
    metrics = _build_scorecard_metrics(
        _VISIBILITY_METRICS, kpi_values, targets, benchmarks,
    )
    score = _compute_scorecard_score(metrics)

    return Scorecard(
        category="visibility",
        display_name="Visibility",
        description="Are we being found by potential customers?",
        score=score,
        health=_score_to_health(score),
        metrics=metrics,
        top_insight=_generate_top_insight(metrics),
        recommended_actions=_generate_recommended_actions(metrics, "visibility"),
    )


def build_lead_flow_scorecard(
    kpi_values: Dict[str, float],
    targets: Dict[str, float],
    benchmarks: Dict[str, float],
) -> Scorecard:
    """Build the Lead Flow scorecard.

    Answers: *"Are leads coming in at the right volume and cost?"*

    Metrics (weights summing to 1.0):
        - ``total_leads`` (0.30)
        - ``cost_per_lead`` (0.25) -- inverted scoring (lower is better)
        - ``lead_sources_diversity`` (0.15)
        - ``phone_calls`` (0.15)
        - ``lead_quality_indicator`` (0.15)
    """
    metrics = _build_scorecard_metrics(
        _LEAD_FLOW_METRICS, kpi_values, targets, benchmarks,
    )
    score = _compute_scorecard_score(metrics)

    return Scorecard(
        category="lead_flow",
        display_name="Lead Flow",
        description="Are leads coming in at the right volume and cost?",
        score=score,
        health=_score_to_health(score),
        metrics=metrics,
        top_insight=_generate_top_insight(metrics),
        recommended_actions=_generate_recommended_actions(metrics, "lead_flow"),
    )


def build_conversion_scorecard(
    kpi_values: Dict[str, float],
    targets: Dict[str, float],
    benchmarks: Dict[str, float],
) -> Scorecard:
    """Build the Conversions scorecard.

    Answers: *"Are leads turning into customers?"*

    Metrics (weights summing to 1.0):
        - ``website_conversion_rate`` (0.30)
        - ``landing_page_conversion_rate`` (0.25)
        - ``form_completion_rate`` (0.15)
        - ``phone_call_rate`` (0.15)
        - ``speed_to_lead`` (0.15) -- inverted scoring (lower is better)
    """
    metrics = _build_scorecard_metrics(
        _CONVERSION_METRICS, kpi_values, targets, benchmarks,
    )
    score = _compute_scorecard_score(metrics)

    return Scorecard(
        category="conversions",
        display_name="Conversions",
        description="Are leads turning into customers?",
        score=score,
        health=_score_to_health(score),
        metrics=metrics,
        top_insight=_generate_top_insight(metrics),
        recommended_actions=_generate_recommended_actions(metrics, "conversions"),
    )


def build_repeat_business_scorecard(
    kpi_values: Dict[str, float],
    targets: Dict[str, float],
    benchmarks: Dict[str, float],
) -> Scorecard:
    """Build the Repeat Business scorecard.

    Answers: *"Are customers coming back and referring others?"*

    Metrics (weights summing to 1.0):
        - ``repeat_customer_rate`` (0.25)
        - ``customer_retention_rate`` (0.25)
        - ``ltv_trend`` (0.20)
        - ``referral_rate`` (0.15)
        - ``review_rating`` (0.15)
    """
    metrics = _build_scorecard_metrics(
        _REPEAT_BUSINESS_METRICS, kpi_values, targets, benchmarks,
    )
    score = _compute_scorecard_score(metrics)

    return Scorecard(
        category="repeat_business",
        display_name="Repeat Business",
        description="Are customers coming back and referring others?",
        score=score,
        health=_score_to_health(score),
        metrics=metrics,
        top_insight=_generate_top_insight(metrics),
        recommended_actions=_generate_recommended_actions(metrics, "repeat_business"),
    )


def build_spend_efficiency_scorecard(
    kpi_values: Dict[str, float],
    targets: Dict[str, float],
    benchmarks: Dict[str, float],
) -> Scorecard:
    """Build the Spend Efficiency scorecard.

    Answers: *"Are we getting good return on ad spend?"*

    Metrics (weights summing to 1.0):
        - ``overall_roas`` (0.30)
        - ``cpa_trend`` (0.25) -- inverted scoring (lower is better)
        - ``budget_utilization`` (0.20)
        - ``per_channel_roas_best`` (0.15)
        - ``wasted_spend_pct`` (0.10) -- inverted scoring (lower is better)
    """
    metrics = _build_scorecard_metrics(
        _SPEND_EFFICIENCY_METRICS, kpi_values, targets, benchmarks,
    )
    score = _compute_scorecard_score(metrics)

    return Scorecard(
        category="spend_efficiency",
        display_name="Spend Efficiency",
        description="Are we getting good return on ad spend?",
        score=score,
        health=_score_to_health(score),
        metrics=metrics,
        top_insight=_generate_top_insight(metrics),
        recommended_actions=_generate_recommended_actions(metrics, "spend_efficiency"),
    )


# ============================================================================
# Channel rollups
# ============================================================================


_VALID_CHANNELS = [
    "organic_search",
    "paid_search",
    "social_organic",
    "social_paid",
    "email",
    "direct",
    "referral",
    "phone",
]


def _build_channel_rollup(
    channel: str,
    data: Dict[str, float],
    targets: Optional[Dict[str, float]] = None,
) -> ChannelRollup:
    """Build a ``ChannelRollup`` from raw channel data.

    The ``data`` dict may contain any of: ``sessions``, ``leads``,
    ``conversions``, ``spend``, ``revenue``.  Derived metrics (``roas``,
    ``conversion_rate``, ``cost_per_lead``) are computed automatically.
    """
    sessions = data.get("sessions")
    leads = data.get("leads")
    conversions = data.get("conversions")
    spend = data.get("spend")
    revenue = data.get("revenue")

    # Derived metrics
    roas: Optional[float] = None
    if revenue is not None and spend is not None and spend > 0:
        roas = round(revenue / spend, 2)

    conversion_rate: Optional[float] = None
    if conversions is not None and sessions is not None and sessions > 0:
        conversion_rate = round(conversions / sessions, 4)

    cost_per_lead: Optional[float] = None
    if spend is not None and leads is not None and leads > 0:
        cost_per_lead = round(spend / leads, 2)

    # Determine channel health from available metrics
    health = _assess_channel_health(roas, conversion_rate, cost_per_lead, targets)

    return ChannelRollup(
        channel=channel,
        sessions=sessions,
        leads=leads,
        conversions=conversions,
        spend=spend,
        revenue=revenue,
        roas=roas,
        conversion_rate=conversion_rate,
        cost_per_lead=cost_per_lead,
        health=health,
    )


def _assess_channel_health(
    roas: Optional[float],
    conversion_rate: Optional[float],
    cost_per_lead: Optional[float],
    targets: Optional[Dict[str, float]] = None,
) -> str:
    """Heuristic channel health assessment.

    Uses ROAS and conversion rate to assign a health tier.  Falls back
    to ``needs_attention`` when there is insufficient data.
    """
    if targets is None:
        targets = {}

    # Use ROAS as the primary signal for paid channels
    if roas is not None:
        roas_target = targets.get("roas", 3.0)
        if roas >= roas_target * 1.2:
            return ScorecardHealth.EXCELLENT.value
        elif roas >= roas_target * 0.8:
            return ScorecardHealth.GOOD.value
        elif roas >= roas_target * 0.5:
            return ScorecardHealth.NEEDS_ATTENTION.value
        elif roas >= roas_target * 0.25:
            return ScorecardHealth.POOR.value
        else:
            return ScorecardHealth.CRITICAL.value

    # Use conversion rate as a secondary signal
    if conversion_rate is not None:
        cr_target = targets.get("conversion_rate", 0.03)
        if conversion_rate >= cr_target * 1.2:
            return ScorecardHealth.EXCELLENT.value
        elif conversion_rate >= cr_target * 0.8:
            return ScorecardHealth.GOOD.value
        elif conversion_rate >= cr_target * 0.5:
            return ScorecardHealth.NEEDS_ATTENTION.value
        else:
            return ScorecardHealth.POOR.value

    return ScorecardHealth.NEEDS_ATTENTION.value


# ============================================================================
# Dashboard summary builder
# ============================================================================


# Category weights for the overall health score
_CATEGORY_WEIGHTS: Dict[str, float] = {
    "visibility": 0.20,
    "lead_flow": 0.25,
    "conversions": 0.25,
    "repeat_business": 0.15,
    "spend_efficiency": 0.15,
}


def build_dashboard_summary(
    business_id: str,
    business_name: str,
    archetype: str,
    kpi_values: Dict[str, float],
    targets: Dict[str, float],
    benchmarks: Dict[str, float],
    channel_data: Dict[str, Dict[str, float]],
    period_start: str,
    period_end: str,
    previous_summary: Optional[DashboardSummary] = None,
) -> DashboardSummary:
    """Build a complete executive dashboard summary.

    Constructs all five scorecards, computes the overall health score,
    builds channel rollups, identifies wins and concerns, and generates
    recommended next actions.

    Args:
        business_id: Unique identifier for the business.
        business_name: Display name.
        archetype: Business archetype slug.
        kpi_values: Mapping of ``metric_name`` to current value.
        targets: Mapping of ``metric_name`` to target value.
        benchmarks: Mapping of ``metric_name`` to industry benchmark.
        channel_data: Mapping of ``channel_name`` to a dict of raw
            performance metrics (``sessions``, ``leads``, ``conversions``,
            ``spend``, ``revenue``).
        period_start: ISO date string for the start of the period.
        period_end: ISO date string for the end of the period.
        previous_summary: Optional previous ``DashboardSummary`` for
            period-over-period comparison.

    Returns:
        A fully populated ``DashboardSummary``.
    """
    # 1. Build all five scorecards
    scorecards = [
        build_visibility_scorecard(kpi_values, targets, benchmarks),
        build_lead_flow_scorecard(kpi_values, targets, benchmarks),
        build_conversion_scorecard(kpi_values, targets, benchmarks),
        build_repeat_business_scorecard(kpi_values, targets, benchmarks),
        build_spend_efficiency_scorecard(kpi_values, targets, benchmarks),
    ]

    # 2. Calculate overall health score (weighted average)
    overall_health_score = _compute_overall_health(scorecards)
    overall_health = _score_to_health(overall_health_score)

    # 3. Build channel rollups
    channel_rollups = [
        _build_channel_rollup(channel, data)
        for channel, data in channel_data.items()
    ]

    # 4. Extract top 3 wins and concerns
    top_3_wins = _extract_wins(scorecards)
    top_3_concerns = _extract_concerns(scorecards)

    # 5. Build recommended next actions from critical and poor scorecards
    recommended_next_actions = _build_next_actions(scorecards)

    # 6. Period comparison
    period_comparison = _compute_period_comparison(
        overall_health_score, scorecards, previous_summary,
    )

    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    return DashboardSummary(
        business_id=business_id,
        business_name=business_name,
        archetype=archetype,
        generated_at=generated_at,
        period_start=period_start,
        period_end=period_end,
        overall_health_score=overall_health_score,
        overall_health=overall_health,
        scorecards=scorecards,
        channel_rollups=channel_rollups,
        top_3_wins=top_3_wins,
        top_3_concerns=top_3_concerns,
        recommended_next_actions=recommended_next_actions,
        period_comparison=period_comparison,
    )


def _compute_overall_health(scorecards: List[Scorecard]) -> float:
    """Compute the weighted overall health score from all scorecards.

    Category weights:
        - visibility: 0.20
        - lead_flow: 0.25
        - conversions: 0.25
        - repeat_business: 0.15
        - spend_efficiency: 0.15
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for sc in scorecards:
        weight = _CATEGORY_WEIGHTS.get(sc.category, 0.0)
        weighted_sum += sc.score * weight
        total_weight += weight

    if total_weight == 0.0:
        return 0.0

    return round(weighted_sum / total_weight, 1)


def _extract_wins(scorecards: List[Scorecard]) -> List[str]:
    """Extract the top 3 wins across all scorecards.

    A "win" is a metric with a high score contribution and a positive
    trend (or simply above target).
    """
    candidates: List[Dict[str, Any]] = []

    for sc in scorecards:
        for m in sc.metrics:
            if m.value is None or m.target is None:
                continue
            if m.score_contribution is not None and m.score_contribution > 0:
                # Higher score contribution relative to weight = better performance
                relative_score = m.score_contribution / m.weight if m.weight > 0 else 0.0
                is_above_target = m.value >= m.target if not _is_inverted(m.metric_name) else m.value <= m.target
                has_positive_trend = m.trend == "up"

                if is_above_target or has_positive_trend:
                    candidates.append({
                        "text": f"{m.display_name}: {m.value:.0f} vs {m.target:.0f} target ({sc.display_name})",
                        "score": relative_score,
                        "has_trend": has_positive_trend,
                    })

    # Sort by score (best first), breaking ties with trend
    candidates.sort(key=lambda c: (c["score"], c["has_trend"]), reverse=True)

    return [c["text"] for c in candidates[:3]]


def _extract_concerns(scorecards: List[Scorecard]) -> List[str]:
    """Extract the top 3 concerns across all scorecards.

    A "concern" is a metric significantly below target or with a
    negative trend.
    """
    candidates: List[Dict[str, Any]] = []

    for sc in scorecards:
        for m in sc.metrics:
            if m.value is None or m.target is None:
                continue
            if m.score_contribution is not None:
                relative_score = m.score_contribution / m.weight if m.weight > 0 else 0.0
                is_below_target = m.value < m.target if not _is_inverted(m.metric_name) else m.value > m.target
                has_negative_trend = m.trend == "down"

                if is_below_target or has_negative_trend:
                    gap_pct = abs(m.value - m.target) / m.target * 100 if m.target > 0 else 0
                    candidates.append({
                        "text": f"{m.display_name}: {m.value:.0f} vs {m.target:.0f} target ({sc.display_name})",
                        "gap_pct": gap_pct,
                        "has_negative_trend": has_negative_trend,
                    })

    # Sort by gap percentage (largest gap first)
    candidates.sort(key=lambda c: (c["gap_pct"], c["has_negative_trend"]), reverse=True)

    return [c["text"] for c in candidates[:3]]


def _is_inverted(metric_name: str) -> bool:
    """Check if a metric uses inverted scoring (lower is better)."""
    inverted_metrics = {
        "cost_per_lead",
        "speed_to_lead",
        "cpa_trend",
        "wasted_spend_pct",
    }
    return metric_name in inverted_metrics


def _build_next_actions(scorecards: List[Scorecard]) -> List[str]:
    """Build a prioritized list of next actions from the weakest scorecards.

    Pulls recommended actions from scorecards with ``critical`` or
    ``poor`` health first, then ``needs_attention``.  Caps at 5 actions.
    """
    actions: List[str] = []

    # Priority order: critical, poor, needs_attention
    priority_order = [
        ScorecardHealth.CRITICAL.value,
        ScorecardHealth.POOR.value,
        ScorecardHealth.NEEDS_ATTENTION.value,
    ]

    for health_level in priority_order:
        for sc in scorecards:
            if sc.health == health_level:
                for action in sc.recommended_actions:
                    if action not in actions:
                        actions.append(action)
                    if len(actions) >= 5:
                        return actions

    # If we have fewer than 5, pad with the first available actions
    if not actions:
        for sc in scorecards:
            for action in sc.recommended_actions:
                if action not in actions:
                    actions.append(action)
                if len(actions) >= 3:
                    return actions

    return actions


def _compute_period_comparison(
    current_overall: float,
    current_scorecards: List[Scorecard],
    previous_summary: Optional[DashboardSummary],
) -> Optional[Dict[str, Any]]:
    """Compute period-over-period comparison.

    Returns ``None`` if no previous summary is available.  Otherwise
    returns a dict with:
        - ``overall_change_pct``: percent change in overall health score
        - ``improved_categories``: list of category names that improved
        - ``declined_categories``: list of category names that declined
    """
    if previous_summary is None:
        return None

    prev_overall = previous_summary.overall_health_score

    if prev_overall > 0:
        overall_change_pct = round(
            ((current_overall - prev_overall) / prev_overall) * 100, 1,
        )
    elif current_overall > 0:
        overall_change_pct = 100.0
    else:
        overall_change_pct = 0.0

    # Build a lookup of previous scorecard scores by category
    prev_scores: Dict[str, float] = {}
    for sc in previous_summary.scorecards:
        prev_scores[sc.category] = sc.score

    improved_categories: List[str] = []
    declined_categories: List[str] = []

    for sc in current_scorecards:
        prev_score = prev_scores.get(sc.category)
        if prev_score is not None:
            if sc.score > prev_score + 2.0:  # 2-point threshold to avoid noise
                improved_categories.append(sc.category)
            elif sc.score < prev_score - 2.0:
                declined_categories.append(sc.category)

    return {
        "overall_change_pct": overall_change_pct,
        "previous_overall_score": prev_overall,
        "current_overall_score": current_overall,
        "improved_categories": improved_categories,
        "declined_categories": declined_categories,
    }
