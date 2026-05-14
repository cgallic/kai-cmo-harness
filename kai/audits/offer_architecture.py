"""Offer architecture audit helpers for ecommerce/CRO funnel teardowns.

This engine turns competitor funnel notes into structured audit output:
source evidence, an offer/pricing matrix, extracted conversion mechanics,
and concrete A/B test hypotheses. It is intentionally data-first so CRO
recommendations do not drift into generic competitor inspiration.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set

from kai.models.audit import (
    AuditFinding,
    EffortLevel,
    Evidence,
    FindingSeverity,
    FindingSource,
    ImpactLevel,
    create_finding,
    create_missing_data_finding,
)
from kai.models.business_profile import BusinessProfile


CATEGORY = "offer_architecture"

_ECOMMERCE_ARCHETYPES = {"ecommerce", "dtc", "d2c", "marketplace"}

REQUIRED_MECHANICS: Sequence[str] = (
    "default_purchase_path",
    "subscription_framing",
    "price_anchoring",
    "bonus_stacking",
    "forced_choice_architecture",
    "checkout_friction",
    "upsell_downsell",
    "retention_incentives",
    "risk_reversal",
)

MECHANIC_LABELS: Mapping[str, str] = {
    "default_purchase_path": "Default purchase path",
    "subscription_framing": "Subscription vs one-time framing",
    "price_anchoring": "Price anchoring",
    "bonus_stacking": "Bonus/free-gift stacking",
    "forced_choice_architecture": "Forced-choice architecture",
    "checkout_friction": "Checkout friction/removal",
    "upsell_downsell": "Upsell/downsell structure",
    "retention_incentives": "Retention incentives",
    "risk_reversal": "Risk reversal",
}

_MECHANIC_KEYWORDS: Mapping[str, Sequence[str]] = {
    "default_purchase_path": (
        "default",
        "preselected",
        "primary path",
        "recommended",
        "most popular",
    ),
    "subscription_framing": (
        "subscription",
        "subscribe",
        "one-time",
        "one time",
        "autoship",
        "auto-ship",
        "recurring",
    ),
    "price_anchoring": (
        "anchor",
        "compare at",
        "was $",
        "save",
        "savings",
        "priced high",
        "strike",
    ),
    "bonus_stacking": (
        "bonus",
        "free gift",
        "gift",
        "bundle",
        "stack",
        "90-day",
        "90 day",
    ),
    "forced_choice_architecture": (
        "choose",
        "forced choice",
        "select",
        "option",
        "plan",
        "tier",
    ),
    "checkout_friction": (
        "shop pay",
        "apple pay",
        "paypal",
        "guest checkout",
        "express checkout",
        "one-click",
        "one click",
        "friction",
    ),
    "upsell_downsell": (
        "upsell",
        "downsell",
        "post-purchase",
        "post purchase",
        "order bump",
        "add-on",
        "add on",
    ),
    "retention_incentives": (
        "retention",
        "loyalty",
        "replenishment",
        "continued subscription",
        "subscribe and save",
        "unlock",
        "reward",
    ),
    "risk_reversal": (
        "guarantee",
        "refund",
        "money back",
        "money-back",
        "free returns",
        "trial",
        "cancel anytime",
    ),
}

_TEST_TEMPLATES: Mapping[str, str] = {
    "default_purchase_path": (
        "Test the current purchase selector against a version where the best "
        "economics path is preselected and labeled as the recommended choice."
    ),
    "subscription_framing": (
        "Test one-time purchase as the default against subscription as the "
        "default, with savings and cancel-anytime copy next to the selector."
    ),
    "price_anchoring": (
        "Test the current price display against a three-point anchor: one-time "
        "price, subscription savings, and total value of included bonuses."
    ),
    "bonus_stacking": (
        "Test no bonus stack against a larger-kit option that adds gifts only "
        "when shoppers choose the higher-commitment path."
    ),
    "forced_choice_architecture": (
        "Test open-ended product selection against a forced choice between two "
        "or three named paths with a clear recommended option."
    ),
    "checkout_friction": (
        "Test the current checkout path against an express-payment path with "
        "guest checkout and fewer visible fields before payment."
    ),
    "upsell_downsell": (
        "Test no post-purchase offer against one relevant order bump or "
        "post-purchase upsell tied to the item already bought."
    ),
    "retention_incentives": (
        "Test a standard subscription against a continuity offer where future "
        "shipments unlock a gift, credit, or exclusive item."
    ),
    "risk_reversal": (
        "Test the current guarantee placement against risk-reversal copy near "
        "the first CTA, cart, and final checkout action."
    ),
}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _stringify(value: Any) -> str:
    if isinstance(value, Mapping):
        return " ".join(_stringify(item) for item in value.values())
    if isinstance(value, (list, tuple, set)):
        return " ".join(_stringify(item) for item in value)
    return "" if value is None else str(value)


def _competitor_funnels(funnel_data: Any) -> List[Mapping[str, Any]]:
    if not funnel_data:
        return []
    if isinstance(funnel_data, list):
        raw_items = funnel_data
    elif isinstance(funnel_data, Mapping):
        raw_items = (
            funnel_data.get("competitors")
            or funnel_data.get("competitor_funnels")
            or funnel_data.get("funnels")
            or []
        )
    else:
        return []

    return [item for item in raw_items if isinstance(item, Mapping)]


def _source_values(competitor: Mapping[str, Any]) -> List[str]:
    values: List[str] = []
    for key in (
        "source_url",
        "source_urls",
        "landing_page_url",
        "ad_library_url",
        "ad_library_urls",
        "google_ads_url",
        "archive_url",
        "archive_urls",
        "screenshot",
        "screenshots",
        "archived_notes",
    ):
        values.extend(str(item) for item in _as_list(competitor.get(key)) if item)
    return values


def _first_source(competitor: Mapping[str, Any]) -> Optional[str]:
    values = _source_values(competitor)
    return values[0] if values else None


def _has_source_evidence(competitor: Mapping[str, Any]) -> bool:
    return bool(_source_values(competitor))


def _pricing_entries(competitor: Mapping[str, Any]) -> List[Mapping[str, Any]]:
    raw = (
        competitor.get("pricing")
        or competitor.get("offers")
        or competitor.get("offer_stack")
        or competitor.get("purchase_paths")
        or []
    )
    if isinstance(raw, Mapping):
        raw_entries: Iterable[Any] = raw.values()
    else:
        raw_entries = _as_list(raw)

    entries = [item for item in raw_entries if isinstance(item, Mapping)]
    if entries:
        return entries

    if any(
        competitor.get(key)
        for key in ("price", "billing_model", "quantity", "bonuses", "risk_reversal")
    ):
        return [competitor]
    return []


def _entry_value(entry: Mapping[str, Any], *keys: str) -> Any:
    for key in keys:
        if key in entry and entry.get(key) not in (None, ""):
            return entry.get(key)
    return None


def _is_default_path(entry: Mapping[str, Any]) -> bool:
    explicit = _entry_value(entry, "is_default", "default", "preselected")
    if explicit is not None:
        return bool(explicit)
    label = _stringify(_entry_value(entry, "path", "name", "label")).lower()
    return any(term in label for term in ("default", "recommended", "most popular"))


def build_offer_pricing_matrix(
    competitor_funnels: Sequence[Mapping[str, Any]],
) -> List[Dict[str, Any]]:
    """Build a normalized offer/pricing matrix from competitor funnel notes."""

    matrix: List[Dict[str, Any]] = []
    for competitor in competitor_funnels:
        name = str(competitor.get("name") or competitor.get("brand") or "Unknown")
        source_url = _first_source(competitor)
        for entry in _pricing_entries(competitor):
            matrix.append(
                {
                    "competitor": name,
                    "path": _entry_value(entry, "path", "name", "label") or "Unlabeled path",
                    "price": _entry_value(entry, "price", "amount", "display_price"),
                    "billing_model": _entry_value(
                        entry,
                        "billing_model",
                        "billing",
                        "purchase_type",
                        "frequency",
                    ),
                    "quantity": _entry_value(entry, "quantity", "supply", "term"),
                    "default_path": _is_default_path(entry),
                    "bonuses": _as_list(_entry_value(entry, "bonuses", "gifts", "bonus_stack")),
                    "retention_incentive": _entry_value(
                        entry,
                        "retention_incentive",
                        "retention",
                        "continuity",
                    ),
                    "risk_reversal": _entry_value(
                        entry,
                        "risk_reversal",
                        "guarantee",
                        "refund_policy",
                    ),
                    "source_url": source_url,
                }
            )
    return matrix


def extract_conversion_mechanics(competitor: Mapping[str, Any]) -> List[str]:
    """Extract known conversion mechanics from one competitor funnel note."""

    searchable = _stringify(competitor).lower()
    found: Set[str] = set()
    for mechanic, keywords in _MECHANIC_KEYWORDS.items():
        if any(keyword in searchable for keyword in keywords):
            found.add(mechanic)
    return [mechanic for mechanic in REQUIRED_MECHANICS if mechanic in found]


def generate_ab_test_hypotheses(
    mechanics: Sequence[str],
    *,
    audience_segment: str = "ecommerce visitors",
) -> List[Dict[str, str]]:
    """Convert extracted mechanics into test-ready hypotheses."""

    hypotheses: List[Dict[str, str]] = []
    for mechanic in mechanics:
        template = _TEST_TEMPLATES.get(mechanic)
        if not template:
            continue
        label = MECHANIC_LABELS.get(mechanic, mechanic.replace("_", " ").title())
        hypotheses.append(
            {
                "mechanic": mechanic,
                "name": label,
                "hypothesis": (
                    f"{template} For {audience_segment}, this should improve "
                    "purchase conversion, average order value, or subscription "
                    "attach rate because the value tradeoff is clearer."
                ),
                "primary_metric": "purchase_conversion_rate",
                "guardrail_metric": "refund_rate",
            }
        )
    return hypotheses


def _profile_is_ecommerce(profile: BusinessProfile) -> bool:
    archetype = (profile.classification.archetype or "").strip().lower()
    business_model = (profile.classification.business_model or "").strip().lower()
    buyer_type = (profile.sales_cycle.buyer_type or "").strip().lower()
    return (
        archetype in _ECOMMERCE_ARCHETYPES
        or business_model in {"product", "marketplace"}
        or buyer_type in {"dtc", "d2c"}
    )


def audit_offer_architecture(
    profile: BusinessProfile,
    funnel_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Audit whether ecommerce/CRO work includes funnel-hack evidence."""

    findings: List[AuditFinding] = []
    competitors = _competitor_funnels(funnel_data)
    is_ecommerce = _profile_is_ecommerce(profile)

    if not competitors:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="funnel_data.competitors",
                impact_description=(
                    "No competitor funnel teardowns were provided. Ecommerce "
                    "and CRO audits need external winning funnels before "
                    "recommending offer or landing-page changes."
                ),
                how_to_provide=(
                    "Add at least 2 competitor or adjacent-brand funnel notes "
                    "with source URLs, screenshots or archived notes, pricing "
                    "paths, extracted mechanics, and checkout observations."
                ),
                critical_gap=is_ecommerce,
            )
        )
        return findings

    unsourced = [
        str(item.get("name") or item.get("brand") or "Unknown")
        for item in competitors
        if not _has_source_evidence(item)
    ]
    if unsourced:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="source_evidence",
                severity=FindingSeverity.HIGH.value if is_ecommerce else FindingSeverity.MEDIUM.value,
                title="Competitor funnel teardown is missing source evidence",
                description=(
                    "One or more competitor funnel notes lack source URLs, "
                    "screenshots, or archived notes. Recommendations based "
                    "on unsourced funnel memory are not audit-grade evidence."
                ),
                recommendation=(
                    "Attach the landing-page URL, Meta Ads Library URL, "
                    "Google ad evidence, screenshot path, or archived notes "
                    f"for: {', '.join(unsourced)}."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.QUICK_WIN.value,
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value=", ".join(unsourced),
                        source_label="Unsourced competitor funnels",
                    )
                ],
                tags=["competitor_funnel", "source_evidence", "cro"],
            )
        )

    matrix = build_offer_pricing_matrix(competitors)
    if not matrix:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="offer_pricing_matrix",
                severity=FindingSeverity.HIGH.value if is_ecommerce else FindingSeverity.MEDIUM.value,
                title="No offer/pricing matrix captured from competitor funnels",
                description=(
                    "The teardown does not capture purchase paths, prices, "
                    "default options, bonuses, retention incentives, or risk "
                    "reversal. Without that matrix, the audit cannot separate "
                    "conversion mechanics from visual taste."
                ),
                recommendation=(
                    "Build an offer/pricing matrix for every inspected funnel: "
                    "path, price, billing model, quantity, default status, "
                    "bonus stack, retention incentive, risk reversal, and source."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.PUBLIC_OBSERVED.value,
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="No pricing entries found in funnel_data",
                        source_label="Funnel teardown data",
                    )
                ],
                tags=["offer", "pricing", "matrix", "cro"],
            )
        )

    mechanics_by_competitor: Dict[str, List[str]] = {}
    covered: List[str] = []
    for competitor in competitors:
        name = str(competitor.get("name") or competitor.get("brand") or "Unknown")
        mechanics = extract_conversion_mechanics(competitor)
        mechanics_by_competitor[name] = mechanics
        for mechanic in mechanics:
            if mechanic not in covered:
                covered.append(mechanic)

    if not covered:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="conversion_mechanics",
                severity=FindingSeverity.MEDIUM.value,
                title="No conversion mechanics extracted from competitor funnels",
                description=(
                    "The teardown captures competitors but does not identify "
                    "the mechanics that may explain conversion: default path, "
                    "subscription framing, price anchors, bonuses, checkout "
                    "friction, upsells, retention, or risk reversal."
                ),
                recommendation=(
                    "Rewrite the teardown as mechanics, not inspiration. For "
                    "each funnel, list the default purchase path, subscription "
                    "or one-time framing, anchor price, gifts, checkout steps, "
                    "upsells, retention hooks, and guarantee."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="No known mechanics matched competitor notes",
                        source_label="Funnel teardown data",
                    )
                ],
                tags=["mechanics", "cro", "ecommerce"],
            )
        )

    hypotheses = generate_ab_test_hypotheses(covered)
    if covered:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="funnel_hack_summary",
                severity=FindingSeverity.INFO.value,
                title="Competitor funnel mechanics ready for A/B test planning",
                description=(
                    "The teardown includes extractable conversion mechanics. "
                    "Use the matrix and hypotheses as the CRO audit's offer "
                    "architecture section."
                ),
                recommendation=(
                    "Prioritize one high-traffic, low-build test first. Do "
                    "not copy the competitor aesthetic; test the commercial "
                    "mechanic behind it."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.PUBLIC_OBSERVED.value,
                evidence=[
                    Evidence(
                        evidence_type="comparison",
                        value=", ".join(MECHANIC_LABELS[m] for m in covered),
                        source_label="Extracted conversion mechanics",
                    )
                ],
                tags=["ab_testing", "offer_architecture", "cro"],
                metadata={
                    "offer_pricing_matrix": matrix,
                    "mechanics_by_competitor": mechanics_by_competitor,
                    "ab_test_hypotheses": hypotheses,
                },
            )
        )

    return findings


def score_offer_architecture(findings: Sequence[AuditFinding]) -> float:
    """Compute a 0-100 readiness score from offer architecture findings."""

    penalties = {
        FindingSeverity.CRITICAL.value: 25,
        FindingSeverity.HIGH.value: 15,
        FindingSeverity.MEDIUM.value: 8,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 0,
    }
    penalty = sum(penalties.get(finding.severity, 8) for finding in findings)
    return max(0.0, min(100.0, 100.0 - penalty))
