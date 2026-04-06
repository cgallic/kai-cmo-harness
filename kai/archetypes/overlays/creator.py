"""Creator / Personal Brand overlay for the Kai Marketing OS.

Layers audience-first metrics, FTC sponsorship disclosure requirements,
content consistency scoring, and monetisation diversification tracking
onto any base archetype.  Designed for YouTubers, podcasters, newsletter
operators, course creators, influencers, and personal-brand-driven
businesses.

Compatible with: all archetypes (no restriction).

Usage::

    from kai.archetypes.overlays import apply_overlay, CREATOR_OVERLAY
    from kai.archetypes import ECOMMERCE_ARCHETYPE

    creator_ecom = apply_overlay(ECOMMERCE_ARCHETYPE, CREATOR_OVERLAY)
"""

from __future__ import annotations

from kai.archetypes.base import KPIDefinition
from kai.archetypes.overlays.overlay_registry import OverlayDefinition

# ============================================================================
# Creator-specific KPIs
# ============================================================================

_CREATOR_KPIS = {
    "audience_growth_rate": KPIDefinition(
        id="audience_growth_rate",
        name="Audience Growth Rate",
        description=(
            "Month-over-month percentage growth of total followers/"
            "subscribers across primary platforms"
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="2-10%/mo",
    ),
    "engagement_rate": KPIDefinition(
        id="engagement_rate",
        name="Engagement Rate",
        description=(
            "Average engagement (likes + comments + shares + saves) "
            "as a percentage of reach or followers"
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="1-8%",
    ),
    "content_consistency_score": KPIDefinition(
        id="content_consistency_score",
        name="Content Consistency Score",
        description=(
            "Internal score (0-100) measuring adherence to the "
            "planned publishing cadence"
        ),
        unit="score",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="70-100",
    ),
    "revenue_per_follower": KPIDefinition(
        id="revenue_per_follower",
        name="Revenue Per Follower",
        description=(
            "Total revenue divided by total follower count -- measures "
            "audience monetisation efficiency"
        ),
        unit="dollars",
        direction="higher_is_better",
        priority="tertiary",
        benchmark_range="$0.01-0.50",
    ),
    "sponsorship_rate": KPIDefinition(
        id="sponsorship_rate",
        name="Sponsorship Rate",
        description=(
            "Average rate charged per sponsored post or video"
        ),
        unit="dollars",
        direction="higher_is_better",
        priority="tertiary",
    ),
}

# ============================================================================
# Overlay definition
# ============================================================================

CREATOR_OVERLAY = OverlayDefinition(
    id="creator",
    name="Creator / Personal Brand",
    description=(
        "Adds audience-first metrics, FTC sponsorship disclosure "
        "requirements, content consistency scoring, and monetisation "
        "diversification tracking.  Applies to YouTubers, podcasters, "
        "newsletter operators, course creators, and personal-brand-"
        "driven businesses."
    ),
    compatible_archetypes=[],  # compatible with all archetypes
    additional_audit_categories=[
        "audience_engagement",
        "content_consistency",
        "monetization_diversification",
    ],
    additional_kpis=_CREATOR_KPIS,
    additional_compliance=[
        (
            "FTC requires clear disclosure of sponsored content and "
            "affiliate relationships"
        ),
        (
            "Platform-specific sponsorship disclosure rules (Instagram "
            "#ad, YouTube paid promotion checkbox)"
        ),
        (
            "Earnings claims in monetization courses must be "
            "substantiated"
        ),
    ],
    restricted_actions=[],
    restricted_claims=[
        "guaranteed income",
        "easy money",
        "passive income without effort",
    ],
    required_disclaimers=[
        "Paid partnership (for sponsored content)",
        "Affiliate link (for affiliate content)",
    ],
    modified_priorities={
        "social_proof_content": "high",
    },
    additional_creative_rules=[
        (
            "Personal brand content should be authentic -- scripted "
            "content should still feel genuine"
        ),
        (
            "Algorithm optimization is important but not at the cost "
            "of brand authenticity"
        ),
        (
            "Cross-platform repurposing should adapt format, not just "
            "repost identically"
        ),
    ],
    metadata={
        "monetisation_channels": [
            "sponsorships",
            "affiliate",
            "courses",
            "merchandise",
            "memberships",
            "ad_revenue",
        ],
    },
)

__all__ = ["CREATOR_OVERLAY"]
