"""SaaS / Software overlay for the Kai Marketing OS.

Layers trial funnel optimisation, product-led growth metrics, churn
prevention KPIs, and software-specific compliance requirements onto
any base archetype.  Designed for SaaS products, developer tools,
B2B platforms, and subscription software businesses.

Compatible with: all archetypes (primarily ``professional-services``
and ``ecommerce``).

Usage::

    from kai.archetypes.overlays import apply_overlay, SAAS_OVERLAY
    from kai.archetypes import PROFESSIONAL_SERVICES_ARCHETYPE

    saas_pro = apply_overlay(
        PROFESSIONAL_SERVICES_ARCHETYPE, SAAS_OVERLAY
    )
"""

from __future__ import annotations

from kai.archetypes.base import KPIDefinition
from kai.archetypes.overlays.overlay_registry import OverlayDefinition

# ============================================================================
# SaaS-specific KPIs
# ============================================================================

_SAAS_KPIS = {
    "trial_to_paid_rate": KPIDefinition(
        id="trial_to_paid_rate",
        name="Trial-to-Paid Conversion Rate",
        description=(
            "Percentage of free-trial users who convert to a paid "
            "subscription"
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="2-15%",
    ),
    "monthly_churn_rate": KPIDefinition(
        id="monthly_churn_rate",
        name="Monthly Churn Rate",
        description=(
            "Percentage of paying customers lost per month"
        ),
        unit="percentage",
        direction="lower_is_better",
        priority="primary",
        benchmark_range="2-8%",
    ),
    "net_revenue_retention": KPIDefinition(
        id="net_revenue_retention",
        name="Net Revenue Retention",
        description=(
            "Percentage of recurring revenue retained from existing "
            "customers after accounting for churn, contraction, and "
            "expansion.  Over 100% means expansion exceeds losses."
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="90-130%",
    ),
    "activation_rate": KPIDefinition(
        id="activation_rate",
        name="Activation Rate",
        description=(
            "Percentage of new signups that reach the product's "
            "'aha moment' -- the action most correlated with retention"
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="20-60%",
    ),
    "feature_adoption_rate": KPIDefinition(
        id="feature_adoption_rate",
        name="Feature Adoption Rate",
        description=(
            "Percentage of active users who adopt a newly released "
            "or targeted feature within a given period"
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="10-40%",
    ),
    "support_ticket_volume": KPIDefinition(
        id="support_ticket_volume",
        name="Support Ticket Volume",
        description=(
            "Total support tickets opened per month -- high volume "
            "may indicate UX problems or missing documentation"
        ),
        unit="count",
        direction="lower_is_better",
        priority="tertiary",
    ),
}

# ============================================================================
# Overlay definition
# ============================================================================

SAAS_OVERLAY = OverlayDefinition(
    id="saas",
    name="SaaS / Software",
    description=(
        "Adds trial funnel optimisation, product-led growth metrics, "
        "churn prevention KPIs, and software-specific compliance "
        "requirements.  Applies to SaaS products, developer tools, "
        "B2B platforms, and subscription software businesses."
    ),
    compatible_archetypes=[],  # compatible with all archetypes
    additional_audit_categories=[
        "trial_funnel",
        "product_led_growth",
        "feature_announcements",
        "churn_prevention",
    ],
    additional_kpis=_SAAS_KPIS,
    additional_compliance=[
        (
            "Free trial terms must be clearly stated -- no surprise "
            "charges"
        ),
        (
            "Pricing page must accurately reflect current pricing "
            "(FTC click-to-cancel compliance)"
        ),
        (
            "Comparison claims against competitors must be factual "
            "and current"
        ),
        (
            "Data handling and privacy claims must comply with "
            "GDPR/CCPA"
        ),
        "Uptime and performance claims must be verifiable",
    ],
    restricted_actions=[],
    restricted_claims=[
        "#1 software",
        "guaranteed uptime (without SLA)",
        "competitor disparagement",
    ],
    required_disclaimers=[],
    modified_priorities={
        "follow_up_sequences": "high",
    },
    additional_creative_rules=[
        "Product screenshots must reflect the current UI",
        (
            "Feature announcements should be timed with actual "
            "releases"
        ),
        (
            "Comparison charts must be kept current -- outdated "
            "comparisons are worse than none"
        ),
        (
            "Demo videos should show real product workflows, not "
            "mockups"
        ),
    ],
    metadata={
        "growth_model": "product_led",
        "pricing_models": [
            "freemium",
            "free_trial",
            "usage_based",
            "seat_based",
        ],
    },
)

__all__ = ["SAAS_OVERLAY"]
