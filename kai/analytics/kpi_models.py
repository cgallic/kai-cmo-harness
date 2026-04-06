"""KPI model definitions per business archetype.

This module defines the canonical KPI (Key Performance Indicator) data
structures and provides pre-built KPI sets for every supported business
archetype.  Each ``KPIDefinition`` encodes:

- **What** to measure (metric name, display name, units)
- **Where** to get the data (which analytics connector and metric names)
- **How** to compute it (calculation method and formula)
- **What good looks like** (benchmarks by industry, target direction)
- **When to worry** (alert thresholds and refresh frequency)

Downstream consumers:

- ``kai.analytics.scorecards`` renders KPI dashboards per business
- ``kai.analytics.watchers`` fires alerts when thresholds are breached
- ``kai.analytics.attribution`` connects marketing actions to KPI movement
- ``kai.proposals`` suggests actions when KPIs decline

Usage::

    from kai.analytics.kpi_models import (
        get_kpis_for_archetype,
        calculate_health_score,
        KPIDefinition,
        KPIDashboard,
        KPIValue,
    )

    kpis = get_kpis_for_archetype("local_service")
    dashboard = KPIDashboard(
        business_id="biz-001",
        archetype="local_service",
        generated_at="2026-04-02T10:00:00Z",
        period_start="2026-03-01",
        period_end="2026-03-31",
        kpi_values=kpi_values,
    )
    dashboard.overall_health_score = calculate_health_score(kpi_values)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from kai.runtime.models import SerializableModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class TargetDirection(str, Enum):
    """Whether a higher or lower value is desirable for a KPI."""

    HIGHER_IS_BETTER = "higher_is_better"
    LOWER_IS_BETTER = "lower_is_better"


class AlertLevel(str, Enum):
    """Severity of a KPI threshold breach."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Core models
# ---------------------------------------------------------------------------


@dataclass
class KPIDefinition(SerializableModel):
    """Complete definition of a single Key Performance Indicator.

    A ``KPIDefinition`` tells the system everything it needs to know about
    a metric: where the data lives, how to calculate it, what benchmarks
    to compare against, and when to raise an alert.

    Attributes:
        name: Machine-readable identifier (e.g., ``"leads_per_month"``).
        display_name: Human-readable label for dashboards and reports.
        description: What this KPI measures and why it matters.
        source_connector: Which analytics connector provides the raw data.
            One of ``"ga4"``, ``"gsc"``, ``"call_tracking"``, ``"gbp"``,
            ``"ad_metrics"``, ``"crm"``, or a ``"+"``-joined combination
            for multi-source KPIs (e.g., ``"ga4+call_tracking+crm"``).
        source_metrics: The ``MetricPoint.metric_name`` values to pull
            from the connector(s).
        calculation_method: How to combine source metrics into a KPI
            value.  One of ``"direct"``, ``"sum"``, ``"ratio"``,
            ``"average"``, ``"weighted_average"``, ``"custom"``.
        calculation_formula: Human-readable formula for non-direct
            calculations.  ``None`` for ``"direct"`` metrics.
        unit: Display unit for the value.  One of ``"count"``,
            ``"currency"``, ``"percentage"``, ``"rating"``, ``"seconds"``,
            ``"minutes"``, ``"ratio"``, ``"score"``.
        target_direction: Whether higher or lower values are better.
        default_benchmark: Industry-average benchmark value, or ``None``
            when the benchmark varies too much across industries.
        benchmark_by_industry: Industry-specific benchmark values keyed
            by lowercase industry slug (e.g., ``"plumbing"``).
        alert_thresholds: Multipliers applied to the target to determine
            alert severity.  ``{"warning": 0.7, "critical": 0.4}`` means
            warn at 70 percent of target, critical at 40 percent.
        refresh_frequency: How often this KPI should be recalculated.
            One of ``"daily"``, ``"weekly"``, ``"monthly"``.
        archetype_relevance: Which business archetypes this KPI applies
            to (e.g., ``["local_service", "multi_location"]``).
    """

    name: str = ""
    display_name: str = ""
    description: str = ""
    source_connector: str = ""
    source_metrics: List[str] = field(default_factory=list)
    calculation_method: str = "direct"
    calculation_formula: Optional[str] = None
    unit: str = "count"
    target_direction: str = TargetDirection.HIGHER_IS_BETTER.value
    default_benchmark: Optional[float] = None
    benchmark_by_industry: Dict[str, float] = field(default_factory=dict)
    alert_thresholds: Dict[str, float] = field(
        default_factory=lambda: {"warning": 0.7, "critical": 0.4},
    )
    refresh_frequency: str = "daily"
    archetype_relevance: List[str] = field(default_factory=list)


@dataclass
class KPIValue(SerializableModel):
    """A single KPI observation at a point in time.

    Captures the current value, trend data across multiple windows,
    performance relative to target and benchmark, and data quality.

    Attributes:
        kpi_name: References ``KPIDefinition.name``.
        value: Current metric value.  ``None`` when no data is available.
        date: ISO date string (``YYYY-MM-DD``) for this observation.
        trend_7d: Percent change over the last 7 days.
        trend_30d: Percent change over the last 30 days.
        trend_90d: Percent change over the last 90 days.
        vs_target: Fraction of target achieved (e.g., ``0.85`` means
            85 percent of target).
        vs_benchmark: Fraction of industry benchmark (e.g., ``1.2``
            means 120 percent of benchmark).
        alert_level: ``AlertLevel`` value if a threshold is breached,
            otherwise ``None``.
        data_quality: Data completeness indicator.  One of
            ``"complete"``, ``"partial"``, ``"estimated"``,
            ``"unavailable"``.
    """

    kpi_name: str = ""
    value: Optional[float] = None
    date: str = ""
    trend_7d: Optional[float] = None
    trend_30d: Optional[float] = None
    trend_90d: Optional[float] = None
    vs_target: Optional[float] = None
    vs_benchmark: Optional[float] = None
    alert_level: Optional[str] = None
    data_quality: str = "complete"


@dataclass
class KPIDashboard(SerializableModel):
    """Aggregated KPI dashboard for a single business over a time period.

    Attributes:
        business_id: Unique identifier for the business.
        archetype: Business archetype slug (e.g., ``"local_service"``).
        generated_at: ISO timestamp when this dashboard was generated.
        period_start: ISO date for the start of the reporting period.
        period_end: ISO date for the end of the reporting period.
        kpi_values: List of ``KPIValue`` observations for this period.
        overall_health_score: Composite 0--100 score derived from
            ``calculate_health_score``.
        top_wins: Up to 3 KPI names trending positively.
        top_concerns: Up to 3 KPI names trending negatively.
        period_comparison: Optional summary comparing this period to the
            previous period (keys vary by archetype).
    """

    business_id: str = ""
    archetype: str = ""
    generated_at: str = ""
    period_start: str = ""
    period_end: str = ""
    kpi_values: List[KPIValue] = field(default_factory=list)
    overall_health_score: Optional[float] = None
    top_wins: List[str] = field(default_factory=list)
    top_concerns: List[str] = field(default_factory=list)
    period_comparison: Optional[Dict[str, Any]] = None


# ============================================================================
# Local-service KPI definitions
# ============================================================================


def get_local_service_kpis() -> List[KPIDefinition]:
    """Return the canonical KPI set for the local-service archetype.

    Covers inbound lead volume, cost efficiency, phone and form
    conversions, Google Business Profile visibility, reviews, website
    conversion rate, speed to lead, and customer retention metrics.
    """
    return [
        KPIDefinition(
            name="leads_per_month",
            display_name="Leads Per Month",
            description=(
                "Total inbound leads across all channels (form submissions, "
                "phone calls, chat leads) per month.  The primary demand "
                "signal for a local service business."
            ),
            source_connector="ga4+call_tracking+crm",
            source_metrics=[
                "form_submissions",
                "phone_calls",
                "chat_leads",
            ],
            calculation_method="sum",
            calculation_formula="form_submissions + phone_calls + chat_leads",
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=45.0,
            benchmark_by_industry={
                "plumbing": 45.0,
                "hvac": 50.0,
                "dental": 65.0,
                "cleaning": 40.0,
                "landscaping": 35.0,
                "roofing": 30.0,
                "pest_control": 55.0,
                "electrical": 40.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="cost_per_lead",
            display_name="Cost Per Lead",
            description=(
                "Average marketing spend required to generate one inbound "
                "lead.  Calculated across all paid channels.  Lower is "
                "better, but extremely low CPL can indicate unqualified lead "
                "volume."
            ),
            source_connector="ad_metrics",
            source_metrics=["total_ad_spend", "total_leads"],
            calculation_method="ratio",
            calculation_formula="total_ad_spend / total_leads",
            unit="currency",
            target_direction=TargetDirection.LOWER_IS_BETTER.value,
            default_benchmark=75.0,
            benchmark_by_industry={
                "plumbing": 65.0,
                "hvac": 80.0,
                "dental": 45.0,
                "cleaning": 35.0,
                "landscaping": 50.0,
                "roofing": 120.0,
                "pest_control": 40.0,
                "electrical": 70.0,
            },
            alert_thresholds={"warning": 1.3, "critical": 1.8},
            refresh_frequency="daily",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="phone_calls",
            display_name="Phone Calls",
            description=(
                "Total inbound phone calls tracked through call tracking "
                "numbers.  For most local service businesses, phone calls "
                "are the highest-intent conversion action."
            ),
            source_connector="call_tracking",
            source_metrics=["phone_calls"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=30.0,
            benchmark_by_industry={
                "plumbing": 35.0,
                "hvac": 40.0,
                "dental": 50.0,
                "cleaning": 20.0,
                "landscaping": 25.0,
                "roofing": 20.0,
                "pest_control": 35.0,
                "electrical": 30.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="form_submissions",
            display_name="Form Submissions",
            description=(
                "Total website form submissions (contact forms, quote "
                "requests, scheduling forms).  Tracked via GA4 form_submit "
                "events."
            ),
            source_connector="ga4",
            source_metrics=["form_submit"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=15.0,
            benchmark_by_industry={
                "plumbing": 12.0,
                "hvac": 15.0,
                "dental": 20.0,
                "cleaning": 18.0,
                "landscaping": 10.0,
                "roofing": 8.0,
                "pest_control": 15.0,
                "electrical": 12.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="gbp_views",
            display_name="GBP Views",
            description=(
                "Total monthly views on the Google Business Profile listing, "
                "combining Search views and Maps views.  Measures local "
                "discovery reach."
            ),
            source_connector="gbp",
            source_metrics=["search_views", "maps_views"],
            calculation_method="sum",
            calculation_formula="search_views + maps_views",
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=2000.0,
            benchmark_by_industry={
                "plumbing": 1800.0,
                "hvac": 2200.0,
                "dental": 3500.0,
                "cleaning": 1500.0,
                "landscaping": 1200.0,
                "roofing": 1000.0,
                "pest_control": 2000.0,
                "electrical": 1600.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="gbp_actions",
            display_name="GBP Actions",
            description=(
                "Total actions taken on the Google Business Profile listing: "
                "direction requests, phone calls, and website clicks.  "
                "Measures engagement beyond passive views."
            ),
            source_connector="gbp",
            source_metrics=[
                "direction_requests",
                "phone_calls",
                "website_clicks",
            ],
            calculation_method="sum",
            calculation_formula=(
                "direction_requests + phone_calls + website_clicks"
            ),
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=250.0,
            benchmark_by_industry={
                "plumbing": 220.0,
                "hvac": 280.0,
                "dental": 400.0,
                "cleaning": 180.0,
                "landscaping": 150.0,
                "roofing": 120.0,
                "pest_control": 250.0,
                "electrical": 200.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="review_count",
            display_name="Review Count",
            description=(
                "Total number of Google reviews on the business listing.  "
                "Review count is a local ranking factor and a trust signal "
                "for prospective customers."
            ),
            source_connector="gbp",
            source_metrics=["review_count"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=80.0,
            benchmark_by_industry={
                "plumbing": 60.0,
                "hvac": 75.0,
                "dental": 120.0,
                "cleaning": 50.0,
                "landscaping": 40.0,
                "roofing": 35.0,
                "pest_control": 70.0,
                "electrical": 55.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="review_rating",
            display_name="Review Rating",
            description=(
                "Average Google review star rating (1.0--5.0).  Ratings "
                "below 4.0 significantly reduce click-through from search "
                "results and Maps."
            ),
            source_connector="gbp",
            source_metrics=["review_rating"],
            calculation_method="direct",
            calculation_formula=None,
            unit="rating",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=4.5,
            benchmark_by_industry={
                "plumbing": 4.4,
                "hvac": 4.5,
                "dental": 4.7,
                "cleaning": 4.6,
                "landscaping": 4.5,
                "roofing": 4.3,
                "pest_control": 4.5,
                "electrical": 4.4,
            },
            alert_thresholds={"warning": 0.93, "critical": 0.85},
            refresh_frequency="weekly",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="website_conversion_rate",
            display_name="Website Conversion Rate",
            description=(
                "Percentage of website visitors who complete a conversion "
                "action (phone call, form submission, chat).  The primary "
                "efficiency metric for the website."
            ),
            source_connector="ga4",
            source_metrics=["conversions", "sessions"],
            calculation_method="ratio",
            calculation_formula="conversions / sessions * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=5.0,
            benchmark_by_industry={
                "plumbing": 5.0,
                "hvac": 4.5,
                "dental": 6.0,
                "cleaning": 5.5,
                "landscaping": 4.0,
                "roofing": 3.5,
                "pest_control": 5.5,
                "electrical": 4.5,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="speed_to_lead_minutes",
            display_name="Speed to Lead (Minutes)",
            description=(
                "Average time in minutes from when a lead comes in to the "
                "first response.  Speed to lead is the single most "
                "controllable conversion factor -- respond in under 5 "
                "minutes to maximize close rate."
            ),
            source_connector="call_tracking+crm",
            source_metrics=["lead_created_at", "first_response_at"],
            calculation_method="average",
            calculation_formula=(
                "average(first_response_at - lead_created_at) in minutes"
            ),
            unit="minutes",
            target_direction=TargetDirection.LOWER_IS_BETTER.value,
            default_benchmark=5.0,
            benchmark_by_industry={
                "plumbing": 8.0,
                "hvac": 10.0,
                "dental": 15.0,
                "cleaning": 12.0,
                "landscaping": 20.0,
                "roofing": 15.0,
                "pest_control": 10.0,
                "electrical": 12.0,
            },
            alert_thresholds={"warning": 1.5, "critical": 3.0},
            refresh_frequency="daily",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="repeat_customer_rate",
            display_name="Repeat Customer Rate",
            description=(
                "Percentage of customers who book a second job or service.  "
                "High repeat rates indicate strong service quality and "
                "effective follow-up."
            ),
            source_connector="crm",
            source_metrics=["repeat_customers", "total_customers"],
            calculation_method="ratio",
            calculation_formula="repeat_customers / total_customers * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=30.0,
            benchmark_by_industry={
                "plumbing": 25.0,
                "hvac": 35.0,
                "dental": 70.0,
                "cleaning": 60.0,
                "landscaping": 55.0,
                "roofing": 10.0,
                "pest_control": 50.0,
                "electrical": 20.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="monthly",
            archetype_relevance=["local_service", "multi_location"],
        ),
        KPIDefinition(
            name="revenue_per_lead",
            display_name="Revenue Per Lead",
            description=(
                "Average revenue generated per inbound lead.  Factors in "
                "both close rate and average job value.  Used to calculate "
                "acceptable cost-per-lead thresholds."
            ),
            source_connector="crm+ad_metrics",
            source_metrics=["total_revenue", "total_leads"],
            calculation_method="ratio",
            calculation_formula="total_revenue / total_leads",
            unit="currency",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=150.0,
            benchmark_by_industry={
                "plumbing": 120.0,
                "hvac": 180.0,
                "dental": 200.0,
                "cleaning": 80.0,
                "landscaping": 100.0,
                "roofing": 350.0,
                "pest_control": 90.0,
                "electrical": 140.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="monthly",
            archetype_relevance=["local_service", "multi_location"],
        ),
    ]


# ============================================================================
# Ecommerce KPI definitions
# ============================================================================


def get_ecommerce_kpis() -> List[KPIDefinition]:
    """Return the canonical KPI set for the ecommerce / DTC archetype.

    Covers revenue, orders, average order value, conversion rate, cart
    abandonment, customer lifetime value, repeat purchases, ROAS, email
    revenue contribution, sessions, bounce rate, and new-vs-returning
    visitor ratio.
    """
    return [
        KPIDefinition(
            name="revenue",
            display_name="Revenue",
            description=(
                "Total revenue from product sales across all channels "
                "(website, marketplace, social commerce).  The primary "
                "business health metric."
            ),
            source_connector="ga4+crm",
            source_metrics=["purchase_revenue"],
            calculation_method="direct",
            calculation_formula=None,
            unit="currency",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=None,
            benchmark_by_industry={
                "apparel": 50000.0,
                "beauty": 30000.0,
                "home_goods": 40000.0,
                "food_beverage": 25000.0,
                "supplements": 35000.0,
                "electronics": 75000.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="orders",
            display_name="Orders",
            description=(
                "Total number of completed orders per period.  Order "
                "count combined with AOV determines revenue trajectory."
            ),
            source_connector="ga4+crm",
            source_metrics=["purchase_count"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=None,
            benchmark_by_industry={
                "apparel": 800.0,
                "beauty": 600.0,
                "home_goods": 400.0,
                "food_beverage": 1000.0,
                "supplements": 500.0,
                "electronics": 300.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="aov",
            display_name="Average Order Value",
            description=(
                "Average dollar amount per order.  AOV is a primary "
                "revenue lever -- increasing AOV does not require more "
                "traffic or a higher conversion rate."
            ),
            source_connector="ga4+crm",
            source_metrics=["purchase_revenue", "purchase_count"],
            calculation_method="ratio",
            calculation_formula="purchase_revenue / purchase_count",
            unit="currency",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=65.0,
            benchmark_by_industry={
                "apparel": 75.0,
                "beauty": 55.0,
                "home_goods": 120.0,
                "food_beverage": 45.0,
                "supplements": 60.0,
                "electronics": 180.0,
            },
            alert_thresholds={"warning": 0.8, "critical": 0.6},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="conversion_rate",
            display_name="Conversion Rate",
            description=(
                "Percentage of site visitors who complete a purchase.  "
                "The multiplier for all traffic -- optimize conversion "
                "rate before increasing ad spend."
            ),
            source_connector="ga4",
            source_metrics=["purchases", "sessions"],
            calculation_method="ratio",
            calculation_formula="purchases / sessions * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=2.5,
            benchmark_by_industry={
                "apparel": 2.0,
                "beauty": 3.0,
                "home_goods": 1.8,
                "food_beverage": 3.5,
                "supplements": 2.5,
                "electronics": 1.5,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="cart_abandonment_rate",
            display_name="Cart Abandonment Rate",
            description=(
                "Percentage of shoppers who add items to cart but do not "
                "complete checkout.  Industry average hovers around 70 "
                "percent -- reducing abandonment by even a few points "
                "directly increases revenue."
            ),
            source_connector="ga4",
            source_metrics=["add_to_cart_sessions", "purchase_sessions"],
            calculation_method="ratio",
            calculation_formula=(
                "(add_to_cart_sessions - purchase_sessions) "
                "/ add_to_cart_sessions * 100"
            ),
            unit="percentage",
            target_direction=TargetDirection.LOWER_IS_BETTER.value,
            default_benchmark=70.0,
            benchmark_by_industry={
                "apparel": 72.0,
                "beauty": 65.0,
                "home_goods": 74.0,
                "food_beverage": 60.0,
                "supplements": 68.0,
                "electronics": 78.0,
            },
            alert_thresholds={"warning": 1.1, "critical": 1.25},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="customer_ltv",
            display_name="Customer Lifetime Value",
            description=(
                "Total revenue a customer generates over their entire "
                "relationship with the brand.  LTV sets the ceiling for "
                "acceptable customer acquisition cost."
            ),
            source_connector="crm",
            source_metrics=[
                "customer_total_revenue",
                "customer_count",
            ],
            calculation_method="average",
            calculation_formula=(
                "sum(customer_total_revenue) / count(unique_customers)"
            ),
            unit="currency",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=180.0,
            benchmark_by_industry={
                "apparel": 200.0,
                "beauty": 250.0,
                "home_goods": 300.0,
                "food_beverage": 120.0,
                "supplements": 350.0,
                "electronics": 400.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="monthly",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="repeat_purchase_rate",
            display_name="Repeat Purchase Rate",
            description=(
                "Percentage of customers who make more than one purchase.  "
                "A healthy repeat rate indicates product-market fit and "
                "effective retention marketing."
            ),
            source_connector="crm",
            source_metrics=["repeat_customers", "total_customers"],
            calculation_method="ratio",
            calculation_formula="repeat_customers / total_customers * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=27.0,
            benchmark_by_industry={
                "apparel": 25.0,
                "beauty": 35.0,
                "home_goods": 20.0,
                "food_beverage": 40.0,
                "supplements": 45.0,
                "electronics": 15.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="monthly",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="roas",
            display_name="Return on Ad Spend",
            description=(
                "Revenue generated per dollar of advertising spend.  A "
                "ROAS of 3.0 means three dollars of revenue for every "
                "dollar spent on ads.  Break-even is typically 2.0x."
            ),
            source_connector="ad_metrics",
            source_metrics=["ad_revenue", "ad_spend"],
            calculation_method="ratio",
            calculation_formula="ad_revenue / ad_spend",
            unit="ratio",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=3.0,
            benchmark_by_industry={
                "apparel": 3.0,
                "beauty": 3.5,
                "home_goods": 2.5,
                "food_beverage": 4.0,
                "supplements": 2.8,
                "electronics": 2.2,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.5},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="email_revenue_pct",
            display_name="Email Revenue %",
            description=(
                "Percentage of total revenue attributable to email "
                "marketing (lifecycle, campaign, automated flows).  A "
                "healthy ecommerce business generates 20--40 percent of "
                "revenue from email."
            ),
            source_connector="ga4+crm",
            source_metrics=["email_revenue", "total_revenue"],
            calculation_method="ratio",
            calculation_formula="email_revenue / total_revenue * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=25.0,
            benchmark_by_industry={
                "apparel": 28.0,
                "beauty": 30.0,
                "home_goods": 22.0,
                "food_beverage": 25.0,
                "supplements": 35.0,
                "electronics": 18.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="sessions",
            display_name="Sessions",
            description=(
                "Total website sessions per period.  Sessions are the "
                "top-of-funnel volume metric -- conversion rate multiplied "
                "by sessions determines order count."
            ),
            source_connector="ga4",
            source_metrics=["sessions"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=None,
            benchmark_by_industry={
                "apparel": 50000.0,
                "beauty": 35000.0,
                "home_goods": 25000.0,
                "food_beverage": 30000.0,
                "supplements": 20000.0,
                "electronics": 40000.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="bounce_rate",
            display_name="Bounce Rate",
            description=(
                "Percentage of sessions where the visitor leaves without "
                "interacting beyond the landing page.  High bounce rates "
                "on product pages indicate messaging, speed, or UX "
                "problems."
            ),
            source_connector="ga4",
            source_metrics=["bounce_rate"],
            calculation_method="direct",
            calculation_formula=None,
            unit="percentage",
            target_direction=TargetDirection.LOWER_IS_BETTER.value,
            default_benchmark=45.0,
            benchmark_by_industry={
                "apparel": 42.0,
                "beauty": 40.0,
                "home_goods": 48.0,
                "food_beverage": 38.0,
                "supplements": 44.0,
                "electronics": 50.0,
            },
            alert_thresholds={"warning": 1.15, "critical": 1.4},
            refresh_frequency="daily",
            archetype_relevance=["ecommerce"],
        ),
        KPIDefinition(
            name="new_vs_returning_ratio",
            display_name="New vs Returning Ratio",
            description=(
                "Ratio of new visitors to returning visitors.  A healthy "
                "balance is 60/40 to 40/60.  Skewing too heavily toward "
                "new visitors means retention is weak; too heavily toward "
                "returning means acquisition has stalled."
            ),
            source_connector="ga4",
            source_metrics=["new_users", "returning_users"],
            calculation_method="ratio",
            calculation_formula="new_users / returning_users",
            unit="ratio",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=1.5,
            benchmark_by_industry={
                "apparel": 1.5,
                "beauty": 1.2,
                "home_goods": 1.8,
                "food_beverage": 1.0,
                "supplements": 1.1,
                "electronics": 2.0,
            },
            alert_thresholds={"warning": 0.5, "critical": 0.3},
            refresh_frequency="weekly",
            archetype_relevance=["ecommerce"],
        ),
    ]


# ============================================================================
# Professional-services KPI definitions
# ============================================================================


def get_professional_services_kpis() -> List[KPIDefinition]:
    """Return the canonical KPI set for the professional-services archetype.

    Covers qualified leads, proposal pipeline, close rates, engagement
    value, client retention, referrals, content authority, LinkedIn
    engagement, and thought leadership reach.
    """
    return [
        KPIDefinition(
            name="qualified_leads",
            display_name="Qualified Leads",
            description=(
                "Number of qualified inbound leads per month from all "
                "channels.  Qualified means the lead matches the firm's "
                "ideal client profile and has budget authority."
            ),
            source_connector="crm",
            source_metrics=["qualified_lead_count"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=15.0,
            benchmark_by_industry={
                "law_firm": 12.0,
                "consulting": 18.0,
                "accounting": 15.0,
                "financial_advisory": 10.0,
                "architecture": 8.0,
                "marketing_agency": 20.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="proposal_sent_rate",
            display_name="Proposal Sent Rate",
            description=(
                "Percentage of qualified leads that advance to a formal "
                "proposal or statement of work.  A low rate may indicate "
                "qualification criteria are too loose or the sales process "
                "has friction."
            ),
            source_connector="crm",
            source_metrics=["proposals_sent", "qualified_leads"],
            calculation_method="ratio",
            calculation_formula="proposals_sent / qualified_leads * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=45.0,
            benchmark_by_industry={
                "law_firm": 50.0,
                "consulting": 40.0,
                "accounting": 55.0,
                "financial_advisory": 35.0,
                "architecture": 45.0,
                "marketing_agency": 50.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="close_rate",
            display_name="Close Rate",
            description=(
                "Percentage of proposals that convert to signed "
                "engagements or retainers.  The most direct measure of "
                "sales effectiveness."
            ),
            source_connector="crm",
            source_metrics=["closed_won", "proposals_sent"],
            calculation_method="ratio",
            calculation_formula="closed_won / proposals_sent * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=35.0,
            benchmark_by_industry={
                "law_firm": 40.0,
                "consulting": 30.0,
                "accounting": 45.0,
                "financial_advisory": 25.0,
                "architecture": 35.0,
                "marketing_agency": 30.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="monthly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="average_engagement_value",
            display_name="Average Engagement Value",
            description=(
                "Average dollar value of a new client engagement, "
                "retainer, or project.  Used to calculate acceptable "
                "acquisition costs and pipeline value."
            ),
            source_connector="crm",
            source_metrics=["engagement_revenue", "engagement_count"],
            calculation_method="ratio",
            calculation_formula="engagement_revenue / engagement_count",
            unit="currency",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=None,
            benchmark_by_industry={
                "law_firm": 8000.0,
                "consulting": 15000.0,
                "accounting": 5000.0,
                "financial_advisory": 3000.0,
                "architecture": 25000.0,
                "marketing_agency": 6000.0,
            },
            alert_thresholds={"warning": 0.8, "critical": 0.5},
            refresh_frequency="monthly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="client_retention_rate",
            display_name="Client Retention Rate",
            description=(
                "Percentage of clients retained year over year (for "
                "retainer or recurring engagements).  High retention "
                "reduces dependence on new business acquisition."
            ),
            source_connector="crm",
            source_metrics=["retained_clients", "total_clients_prev_year"],
            calculation_method="ratio",
            calculation_formula=(
                "retained_clients / total_clients_prev_year * 100"
            ),
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=85.0,
            benchmark_by_industry={
                "law_firm": 80.0,
                "consulting": 75.0,
                "accounting": 92.0,
                "financial_advisory": 90.0,
                "architecture": 70.0,
                "marketing_agency": 78.0,
            },
            alert_thresholds={"warning": 0.85, "critical": 0.7},
            refresh_frequency="monthly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="referral_rate",
            display_name="Referral Rate",
            description=(
                "Percentage of new clients acquired through referrals "
                "from existing clients, partners, or professional "
                "networks.  Typically the highest-converting and lowest-"
                "cost lead source for professional services."
            ),
            source_connector="crm",
            source_metrics=["referral_clients", "new_clients"],
            calculation_method="ratio",
            calculation_formula="referral_clients / new_clients * 100",
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=40.0,
            benchmark_by_industry={
                "law_firm": 45.0,
                "consulting": 35.0,
                "accounting": 50.0,
                "financial_advisory": 55.0,
                "architecture": 40.0,
                "marketing_agency": 30.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="monthly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="content_views",
            display_name="Content Views",
            description=(
                "Total views on thought leadership content (blog posts, "
                "articles, whitepapers, case studies).  Measures the "
                "reach of the firm's authority content engine."
            ),
            source_connector="ga4",
            source_metrics=["page_views"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=5000.0,
            benchmark_by_industry={
                "law_firm": 8000.0,
                "consulting": 6000.0,
                "accounting": 4000.0,
                "financial_advisory": 3000.0,
                "architecture": 2500.0,
                "marketing_agency": 10000.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="linkedin_engagement",
            display_name="LinkedIn Engagement",
            description=(
                "Average engagement rate on LinkedIn posts across firm "
                "and key personnel profiles.  LinkedIn is the primary "
                "organic social channel for professional services."
            ),
            source_connector="ga4",
            source_metrics=["linkedin_engagement_rate"],
            calculation_method="direct",
            calculation_formula=None,
            unit="percentage",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=3.0,
            benchmark_by_industry={
                "law_firm": 2.5,
                "consulting": 3.5,
                "accounting": 2.0,
                "financial_advisory": 2.8,
                "architecture": 4.0,
                "marketing_agency": 4.5,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["professional_services"],
        ),
        KPIDefinition(
            name="thought_leadership_reach",
            display_name="Thought Leadership Reach",
            description=(
                "Combined reach of thought leadership activities: "
                "speaking engagements attended, podcast appearances, "
                "media mentions, and content impressions.  A composite "
                "measure of the firm's industry visibility."
            ),
            source_connector="crm+ga4",
            source_metrics=[
                "speaking_events",
                "podcast_appearances",
                "media_mentions",
                "content_impressions",
            ],
            calculation_method="sum",
            calculation_formula=(
                "speaking_events + podcast_appearances + media_mentions "
                "+ content_impressions"
            ),
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=None,
            benchmark_by_industry={
                "law_firm": 15.0,
                "consulting": 20.0,
                "accounting": 10.0,
                "financial_advisory": 12.0,
                "architecture": 8.0,
                "marketing_agency": 25.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="monthly",
            archetype_relevance=["professional_services"],
        ),
    ]


# ============================================================================
# Multi-location KPI definitions
# ============================================================================


def get_multi_location_kpis() -> List[KPIDefinition]:
    """Return the canonical KPI set for the multi-location archetype.

    Includes all local-service KPIs (since each location operates as a
    local business) plus three additional KPIs specific to managing a
    fleet of locations: NAP/branding consistency, branded search volume,
    and review distribution across the fleet.
    """
    base_kpis = get_local_service_kpis()

    # Update archetype_relevance on each base KPI to include
    # multi_location (they already include it from the definition,
    # but this makes the intent explicit).
    for kpi in base_kpis:
        if "multi_location" not in kpi.archetype_relevance:
            kpi.archetype_relevance.append("multi_location")

    multi_location_specific = [
        KPIDefinition(
            name="location_consistency_score",
            display_name="Location Consistency Score",
            description=(
                "Composite 0--100 score measuring how consistent NAP "
                "(Name, Address, Phone), branding, GBP completeness, and "
                "content quality are across all locations.  Inconsistency "
                "confuses search engines and erodes brand trust."
            ),
            source_connector="gbp+crm",
            source_metrics=[
                "nap_match_rate",
                "brand_asset_compliance",
                "gbp_completeness_per_location",
            ],
            calculation_method="weighted_average",
            calculation_formula=(
                "0.4 * nap_match_rate + 0.3 * brand_asset_compliance "
                "+ 0.3 * avg(gbp_completeness_per_location)"
            ),
            unit="score",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=80.0,
            benchmark_by_industry={
                "dental": 85.0,
                "fitness": 75.0,
                "restaurant": 70.0,
                "retail_chain": 80.0,
                "home_services": 72.0,
                "healthcare": 88.0,
            },
            alert_thresholds={"warning": 0.8, "critical": 0.6},
            refresh_frequency="weekly",
            archetype_relevance=["multi_location"],
        ),
        KPIDefinition(
            name="brand_search_volume",
            display_name="Brand Search Volume",
            description=(
                "Total branded search queries (company name and "
                "variations) from Google Search Console.  Brand search "
                "volume is a leading indicator of brand awareness and "
                "grows with effective marketing across all locations."
            ),
            source_connector="gsc",
            source_metrics=["branded_impressions", "branded_clicks"],
            calculation_method="direct",
            calculation_formula=None,
            unit="count",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=None,
            benchmark_by_industry={
                "dental": 2000.0,
                "fitness": 5000.0,
                "restaurant": 8000.0,
                "retail_chain": 10000.0,
                "home_services": 1500.0,
                "healthcare": 3000.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["multi_location"],
        ),
        KPIDefinition(
            name="multi_location_review_distribution",
            display_name="Review Distribution Score",
            description=(
                "Standard deviation of review counts across locations, "
                "inverted so that a lower deviation yields a higher "
                "score.  High variance means some locations have strong "
                "review profiles while others are neglected -- the "
                "weakest location drags down the brand in its market."
            ),
            source_connector="gbp",
            source_metrics=["review_count_per_location"],
            calculation_method="custom",
            calculation_formula=(
                "100 - min(100, stddev(review_count_per_location))"
            ),
            unit="score",
            target_direction=TargetDirection.HIGHER_IS_BETTER.value,
            default_benchmark=70.0,
            benchmark_by_industry={
                "dental": 75.0,
                "fitness": 65.0,
                "restaurant": 60.0,
                "retail_chain": 70.0,
                "home_services": 68.0,
                "healthcare": 72.0,
            },
            alert_thresholds={"warning": 0.7, "critical": 0.4},
            refresh_frequency="weekly",
            archetype_relevance=["multi_location"],
        ),
    ]

    return base_kpis + multi_location_specific


# ============================================================================
# Router
# ============================================================================

_ARCHETYPE_KPI_DISPATCH = {
    "local_service": get_local_service_kpis,
    "ecommerce": get_ecommerce_kpis,
    "professional_services": get_professional_services_kpis,
    "multi_location": get_multi_location_kpis,
}


def get_kpis_for_archetype(archetype: str) -> List[KPIDefinition]:
    """Return the KPI definition set for the given archetype.

    Args:
        archetype: One of ``"local_service"``, ``"ecommerce"``,
            ``"professional_services"``, ``"multi_location"``.

    Returns:
        A list of fully-populated ``KPIDefinition`` objects.

    Raises:
        ValueError: If the archetype is not recognized.
    """
    factory = _ARCHETYPE_KPI_DISPATCH.get(archetype)
    if factory is None:
        supported = ", ".join(sorted(_ARCHETYPE_KPI_DISPATCH.keys()))
        raise ValueError(
            f"Unknown archetype {archetype!r}. "
            f"Supported archetypes: {supported}"
        )
    return factory()


# ============================================================================
# Health score calculation
# ============================================================================


def calculate_health_score(kpi_values: List[KPIValue]) -> float:
    """Compute a 0--100 composite health score from a list of KPI values.

    The score is a weighted average of ``vs_target`` values across all
    KPIs that have data.  KPIs with a ``"critical"`` alert level receive
    a 2x weight penalty (i.e., they pull the score down twice as hard as
    a normal KPI).  KPIs with a ``"warning"`` alert level receive a 1.5x
    weight penalty.

    The raw weighted average is clamped to the 0--100 range.

    Args:
        kpi_values: List of ``KPIValue`` observations.  Only entries
            with a non-``None`` ``vs_target`` value contribute to the
            score.

    Returns:
        A float between 0.0 and 100.0.  Returns 0.0 if no KPIs have
        data (i.e., all ``vs_target`` values are ``None``).
    """
    total_weight = 0.0
    weighted_sum = 0.0

    for kv in kpi_values:
        if kv.vs_target is None:
            continue

        # Base weight for every KPI with data
        weight = 1.0

        # Penalty weights for underperforming KPIs
        if kv.alert_level == AlertLevel.CRITICAL.value:
            weight = 2.0
        elif kv.alert_level == AlertLevel.WARNING.value:
            weight = 1.5

        # vs_target is a fraction (e.g. 0.85 = 85% of target)
        # Cap individual KPI contribution at 1.0 so outperformance
        # on one KPI cannot mask underperformance elsewhere.
        capped_target = min(kv.vs_target, 1.0)

        weighted_sum += capped_target * weight
        total_weight += weight

    if total_weight == 0.0:
        return 0.0

    # Convert from 0.0-1.0 fraction to 0-100 score
    raw_score = (weighted_sum / total_weight) * 100.0

    # Clamp to valid range
    return max(0.0, min(100.0, raw_score))
