"""Franchise overlay for the Kai Marketing OS.

Layers brand compliance requirements, corporate alignment checks,
co-op fund tracking, and territory restrictions onto compatible base
archetypes.  Designed for franchise locations that must balance local
marketing autonomy with corporate brand standards.

Compatible with: ``local-service``, ``multi-location``, ``ecommerce``.

Usage::

    from kai.archetypes.overlays import apply_overlay, FRANCHISE_OVERLAY
    from kai.archetypes import LOCAL_SERVICE_ARCHETYPE

    franchise_local = apply_overlay(
        LOCAL_SERVICE_ARCHETYPE, FRANCHISE_OVERLAY
    )
"""

from __future__ import annotations

from kai.archetypes.base import KPIDefinition
from kai.archetypes.overlays.overlay_registry import OverlayDefinition

# ============================================================================
# Franchise-specific KPIs
# ============================================================================

_FRANCHISE_KPIS = {
    "brand_compliance_score": KPIDefinition(
        id="brand_compliance_score",
        name="Brand Compliance Score",
        description=(
            "Score (0-100) measuring adherence to franchisor brand "
            "guidelines across all marketing materials"
        ),
        unit="score",
        direction="higher_is_better",
        priority="primary",
        benchmark_range="85-100",
    ),
    "co_op_fund_utilization": KPIDefinition(
        id="co_op_fund_utilization",
        name="Co-op Fund Utilization",
        description=(
            "Percentage of available co-op advertising funds that "
            "have been used within the period"
        ),
        unit="percentage",
        direction="higher_is_better",
        priority="secondary",
        benchmark_range="70-100%",
    ),
}

# ============================================================================
# Overlay definition
# ============================================================================

FRANCHISE_OVERLAY = OverlayDefinition(
    id="franchise",
    name="Franchise",
    description=(
        "Adds brand compliance requirements, corporate alignment "
        "checks, co-op fund utilisation tracking, and territory "
        "restrictions.  Applies to franchise locations that must "
        "balance local marketing autonomy with corporate brand "
        "standards."
    ),
    compatible_archetypes=["local-service", "multi-location", "ecommerce"],
    additional_audit_categories=[
        "brand_compliance",
        "corporate_alignment",
        "co_op_utilization",
    ],
    additional_kpis=_FRANCHISE_KPIS,
    additional_compliance=[
        (
            "All marketing materials must comply with franchisor "
            "brand guidelines"
        ),
        (
            "Co-op advertising funds have specific usage rules and "
            "approval requirements"
        ),
        (
            "Franchisee cannot make brand-level claims without "
            "corporate approval"
        ),
        (
            "Territory advertising must respect agreed-upon "
            "geographic boundaries"
        ),
        (
            "Pricing and promotion changes may require franchisor "
            "approval"
        ),
        (
            "Use of franchisor trademarks is governed by franchise "
            "agreement"
        ),
    ],
    restricted_actions=[
        "brand_messaging_changes",
        "pricing_changes",
        "new_offer_creation",
    ],
    restricted_claims=[
        "franchise-wide claims without corporate approval",
    ],
    required_disclaimers=[
        "Independently owned and operated (if required by franchise agreement)",
    ],
    modified_priorities={
        "gbp_optimization": "high",
    },
    additional_creative_rules=[
        (
            "All creative must use approved brand assets (logos, "
            "colors, fonts)"
        ),
        "Local customization is limited to approved template fields",
        (
            "Corporate must approve any creative that deviates from "
            "templates"
        ),
    ],
    metadata={
        "approval_workflow": "corporate_review_required",
        "territory_enforcement": True,
    },
)

__all__ = ["FRANCHISE_OVERLAY"]
