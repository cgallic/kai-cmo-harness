"""Agentic commerce readiness audit.

Fixture-friendly audit for AI shopping readiness that can run fully local.
The engine reports structured findings (including explicit missing-data gaps)
so operators can prioritize fixes without live commerce credentials.
"""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional, Sequence

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

CATEGORY = "agentic_commerce"


def _as_map(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _as_list(value: Any) -> List[Any]:
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    if value is None:
        return []
    return [value]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_text(value: Any) -> bool:
    return bool(_text(value))


def _product_schema_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    schema = _as_map(data.get("schema"))
    product_schema = _as_list(schema.get("product"))
    if not product_schema:
        return create_finding(
            category=CATEGORY,
            subcategory="product_schema",
            severity=FindingSeverity.HIGH.value,
            title="Product schema is missing for commerce pages",
            description=(
                "AI shopping surfaces need structured product entities to parse "
                "price, availability, and compatibility details."
            ),
            recommendation=(
                "Add Product JSON-LD with name, sku, price, currency, availability, "
                "image, and offer metadata on key product pages."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.USER_PROVIDED.value,
            evidence=[
                Evidence(
                    evidence_type="checklist_item",
                    value="schema.product entries: 0",
                    source_label="commerce_fixture.schema",
                )
            ],
            tags=["product_schema", "catalog", "ai_shopping"],
        )
    return None


def _catalog_fields_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    catalog = _as_map(data.get("catalog"))
    products = [item for item in _as_list(catalog.get("products")) if isinstance(item, Mapping)]
    if not products:
        return create_missing_data_finding(
            category=CATEGORY,
            field_path="catalog.products",
            impact_description=(
                "Catalog products are missing, so readiness cannot score title, "
                "SKU, pricing, inventory, or product URL completeness."
            ),
            how_to_provide=(
                "Provide fixture products under catalog.products or connect a "
                "catalog feed export before rerunning the audit."
            ),
            critical_gap=True,
        )

    required_fields = ("id", "title", "sku", "price", "currency", "availability", "url")
    incomplete = 0
    for product in products:
        if any(not _has_text(product.get(field)) for field in required_fields):
            incomplete += 1

    if incomplete:
        return create_finding(
            category=CATEGORY,
            subcategory="catalog_fields",
            severity=FindingSeverity.HIGH.value if incomplete == len(products) else FindingSeverity.MEDIUM.value,
            title="Catalog fields are incomplete for agent discovery",
            description=(
                f"{incomplete} of {len(products)} products are missing required "
                "commerce fields (id/title/sku/price/currency/availability/url)."
            ),
            recommendation=(
                "Normalize product feed fields so every SKU includes canonical "
                "identity, pricing, inventory status, and a crawlable product URL."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.USER_PROVIDED.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=f"{incomplete}/{len(products)} products incomplete",
                    source_label="commerce_fixture.catalog.products",
                )
            ],
            tags=["catalog", "feed_quality"],
        )
    return None


def _pricing_inventory_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    catalog = _as_map(data.get("catalog"))
    products = [item for item in _as_list(catalog.get("products")) if isinstance(item, Mapping)]
    if not products:
        return None

    price_conflicts = 0
    inventory_unknown = 0
    for product in products:
        price = product.get("price")
        sale_price = product.get("sale_price")
        if _has_text(price) and _has_text(sale_price):
            try:
                if float(sale_price) > float(price):
                    price_conflicts += 1
            except (TypeError, ValueError):
                pass
        if _text(product.get("availability")).lower() in {"", "unknown", "n/a"}:
            inventory_unknown += 1

    if price_conflicts or inventory_unknown:
        return create_finding(
            category=CATEGORY,
            subcategory="pricing_inventory_clarity",
            severity=FindingSeverity.HIGH.value if price_conflicts else FindingSeverity.MEDIUM.value,
            title="Pricing or inventory clarity gaps detected",
            description=(
                f"Detected {price_conflicts} pricing conflicts and {inventory_unknown} "
                "products with unknown availability."
            ),
            recommendation=(
                "Align list/sale pricing logic and set explicit inventory state per SKU "
                "(in_stock, out_of_stock, preorder) before enabling agentic offers."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.USER_PROVIDED.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=f"price_conflicts={price_conflicts}, inventory_unknown={inventory_unknown}",
                    source_label="commerce_fixture.catalog.products",
                )
            ],
            tags=["pricing", "inventory"],
        )
    return None


def _policy_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    policies = _as_map(data.get("policies"))
    shipping = _text(policies.get("shipping"))
    returns = _text(policies.get("returns"))
    if shipping and returns:
        return None
    return create_finding(
        category=CATEGORY,
        subcategory="shipping_return_policy",
        severity=FindingSeverity.HIGH.value,
        title="Shipping or returns policy is missing",
        description=(
            "AI commerce checkouts need explicit shipping and return terms to "
            "avoid unsupported offers and post-purchase disputes."
        ),
        recommendation=(
            "Publish shipping and return policy pages with clear timelines, fees, "
            "regions, and eligibility exclusions."
        ),
        estimated_impact=ImpactLevel.HIGH.value,
        effort=EffortLevel.QUICK_WIN.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="checklist_item",
                value=f"shipping_present={bool(shipping)}; returns_present={bool(returns)}",
                source_label="commerce_fixture.policies",
            )
        ],
        tags=["policy", "checkout"],
    )


def _reviews_proof_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    proof = _as_map(data.get("proof"))
    review_count = proof.get("review_count")
    avg_rating = proof.get("average_rating")
    if review_count is None and avg_rating is None:
        return create_missing_data_finding(
            category=CATEGORY,
            field_path="proof.review_count",
            impact_description=(
                "Review and trust proof inputs are missing, so recommendation quality "
                "for social proof and conversion confidence is reduced."
            ),
            how_to_provide=(
                "Include review_count and average_rating from public review exports or "
                "connected review platforms."
            ),
            critical_gap=False,
        )
    return None


def _checkout_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    checkout = _as_map(data.get("checkout"))
    checkout_url = _text(checkout.get("checkout_url"))
    guest_checkout = bool(checkout.get("guest_checkout"))
    payment_methods = _as_list(checkout.get("payment_methods"))

    if checkout_url and guest_checkout and payment_methods:
        return None

    return create_finding(
        category=CATEGORY,
        subcategory="checkout_readiness",
        severity=FindingSeverity.HIGH.value,
        title="Checkout readiness is incomplete",
        description=(
            "Agentic checkout needs a valid checkout URL, guest flow support, and "
            "declared payment methods."
        ),
        recommendation=(
            "Provide checkout_url, enable guest_checkout, and declare supported "
            "payment methods for static and connected audits."
        ),
        estimated_impact=ImpactLevel.HIGH.value,
        effort=EffortLevel.MODERATE.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="checklist_item",
                value=(
                    f"checkout_url={bool(checkout_url)}; "
                    f"guest_checkout={guest_checkout}; "
                    f"payment_methods={len(payment_methods)}"
                ),
                source_label="commerce_fixture.checkout",
            )
        ],
        tags=["checkout", "conversion"],
    )


def _crawler_findings(data: Mapping[str, Any]) -> List[AuditFinding]:
    findings: List[AuditFinding] = []
    crawler = _as_map(data.get("crawler"))
    robots_txt = _text(crawler.get("robots_txt"))
    llms_txt = _text(crawler.get("llms_txt"))
    ai_policy = _text(crawler.get("ai_policy"))

    if not robots_txt or not llms_txt:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="robots_llms",
                severity=FindingSeverity.HIGH.value,
                title="robots.txt or llms.txt coverage is incomplete",
                description=(
                    "Agent discovery and safe crawling depend on explicit robots and "
                    "llms policy files."
                ),
                recommendation=(
                    "Publish both robots.txt and llms.txt with crawler rules and "
                    "commerce capability links."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.USER_PROVIDED.value,
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value=f"robots_txt={bool(robots_txt)}; llms_txt={bool(llms_txt)}",
                        source_label="commerce_fixture.crawler",
                    )
                ],
                tags=["robots", "llms", "agent_readiness"],
            )
        )

    if not ai_policy:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="ai_crawler_policy",
                severity=FindingSeverity.MEDIUM.value,
                title="AI crawler policy is missing",
                description=(
                    "No explicit allow/deny or licensing policy was supplied for AI "
                    "crawlers, model training, or answer-engine surfaces."
                ),
                recommendation=(
                    "Define an AI crawler policy with allowed bots, blocked bots, and "
                    "licensing notes for high-value content."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.USER_PROVIDED.value,
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="crawler.ai_policy is empty",
                        source_label="commerce_fixture.crawler",
                    )
                ],
                tags=["crawler_policy", "compliance"],
            )
        )

    return findings


def _offer_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    offers = [item for item in _as_list(data.get("offers")) if isinstance(item, Mapping)]
    if not offers:
        return create_missing_data_finding(
            category=CATEGORY,
            field_path="offers",
            impact_description=(
                "Offer readability could not be scored because no structured offers were "
                "provided in fixture data."
            ),
            how_to_provide=(
                "Add at least one offer with title, eligibility, and expiration fields."
            ),
            critical_gap=False,
        )

    missing_rules = 0
    for offer in offers:
        if not _has_text(offer.get("title")) or not _has_text(offer.get("eligibility")) or not _has_text(offer.get("expiration")):
            missing_rules += 1

    if missing_rules:
        return create_finding(
            category=CATEGORY,
            subcategory="offer_readability",
            severity=FindingSeverity.MEDIUM.value,
            title="Offer readability metadata is incomplete",
            description=(
                f"{missing_rules} of {len(offers)} offers are missing title, "
                "eligibility, or expiration details."
            ),
            recommendation=(
                "Standardize offers with explicit title, eligibility, expiration, "
                "stackability, and region constraints."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.USER_PROVIDED.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=f"{missing_rules}/{len(offers)} offers incomplete",
                    source_label="commerce_fixture.offers",
                )
            ],
            tags=["offers", "eligibility"],
        )

    return None


def _protocol_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    protocols = _as_map(data.get("protocols"))
    acp = bool(protocols.get("acp"))
    ucp = bool(protocols.get("ucp"))
    ap2 = bool(protocols.get("ap2"))
    x402 = bool(protocols.get("x402"))

    supported = sum([acp, ucp, ap2, x402])
    if supported >= 2:
        return None

    return create_finding(
        category=CATEGORY,
        subcategory="protocol_readiness",
        severity=FindingSeverity.MEDIUM.value,
        title="Agentic protocol readiness notes are limited",
        description=(
            "The audit lacks meaningful ACP/UCP/AP2/x402 readiness coverage. "
            "Protocol notes should define which rails are currently supported."
        ),
        recommendation=(
            "Document readiness notes for ACP/UCP/AP2/x402 with current support "
            "state, blockers, and nearest implementation path."
        ),
        estimated_impact=ImpactLevel.MEDIUM.value,
        effort=EffortLevel.MODERATE.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="metric",
                value=f"protocols_supported={supported}/4",
                source_label="commerce_fixture.protocols",
            )
        ],
        tags=["acp", "ucp", "ap2", "x402"],
    )


def _connector_data_gap(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    connected = _as_map(data.get("connected_sources"))
    if not connected:
        return create_missing_data_finding(
            category=CATEGORY,
            field_path="connected_sources",
            impact_description=(
                "Connected-source coverage is absent. Static fixture mode can still run, "
                "but live catalog and checkout verification is incomplete."
            ),
            how_to_provide=(
                "Provide connected_sources metadata (merchant_center/shopify/analytics) "
                "or explicitly mark fixture-only mode."
            ),
            critical_gap=False,
        )

    if not connected.get("credentials_available", True):
        return create_missing_data_finding(
            category=CATEGORY,
            field_path="connected_sources.credentials_available",
            impact_description=(
                "Live credentials are unavailable. Audit outputs are static-mode findings "
                "and should not claim connected verification."
            ),
            how_to_provide=(
                "Keep static mode and list this as a data gap, or supply credentials and "
                "rerun connected-mode checks."
            ),
            critical_gap=False,
        )
    return None


def audit_agentic_commerce_readiness(
    commerce_data: Optional[Mapping[str, Any]] = None,
) -> List[AuditFinding]:
    """Run a fixture-friendly agentic commerce readiness audit."""

    data = _as_map(commerce_data)
    findings: List[AuditFinding] = []

    for finding in (
        _product_schema_finding(data),
        _catalog_fields_finding(data),
        _pricing_inventory_finding(data),
        _policy_finding(data),
        _reviews_proof_finding(data),
        _checkout_finding(data),
        _offer_finding(data),
        _protocol_finding(data),
        _connector_data_gap(data),
    ):
        if finding is not None:
            findings.append(finding)

    findings.extend(_crawler_findings(data))

    return findings


_SEVERITY_PENALTY: Dict[str, float] = {
    FindingSeverity.CRITICAL.value: 25.0,
    FindingSeverity.HIGH.value: 15.0,
    FindingSeverity.MEDIUM.value: 8.0,
    FindingSeverity.LOW.value: 3.0,
}


def score_agentic_commerce_readiness(findings: Sequence[AuditFinding]) -> float:
    """Compute readiness score from findings on a 0-100 scale."""

    score = 100.0
    for finding in findings:
        if finding.source == FindingSource.MISSING_DATA.value:
            continue
        if finding.severity == FindingSeverity.INFO.value:
            continue
        score -= _SEVERITY_PENALTY.get(finding.severity, 0.0)
    return max(0.0, min(100.0, round(score, 1)))


def summarize_agentic_commerce_findings(
    findings: Sequence[AuditFinding],
    *,
    top_n: int = 5,
) -> Dict[str, Any]:
    """Return summary metrics and prioritized finding IDs."""

    severity_order = {
        FindingSeverity.CRITICAL.value: 0,
        FindingSeverity.HIGH.value: 1,
        FindingSeverity.MEDIUM.value: 2,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 4,
    }
    ranked = sorted(
        findings,
        key=lambda item: (
            severity_order.get(item.severity, 99),
            item.priority,
        ),
    )

    counts: Dict[str, int] = {
        FindingSeverity.CRITICAL.value: 0,
        FindingSeverity.HIGH.value: 0,
        FindingSeverity.MEDIUM.value: 0,
        FindingSeverity.LOW.value: 0,
        FindingSeverity.INFO.value: 0,
        "missing_data": 0,
    }
    for finding in findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
        if finding.source == FindingSource.MISSING_DATA.value:
            counts["missing_data"] += 1

    return {
        "score": score_agentic_commerce_readiness(findings),
        "counts": counts,
        "top_fix_ids": [finding.id for finding in ranked[:top_n]],
    }
