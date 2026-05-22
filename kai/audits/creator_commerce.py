"""Creator commerce operations audit.

OSS-first, fixture-friendly checks for creator commerce operations:
creator fit inputs, audience quality, rate-card hygiene, rights/disclosure,
affiliate attribution, and GMV evidence coverage.
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


CATEGORY = "creator_commerce"


def _as_map(value: Any) -> Mapping[str, Any]:
    if isinstance(value, Mapping):
        return value
    return {}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, tuple):
        return list(value)
    return [value]


def _text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _has_text(value: Any) -> bool:
    return bool(_text(value))


def _creator_roster_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    creators = [item for item in _as_list(data.get("creators")) if isinstance(item, Mapping)]
    if creators:
        return None

    return create_missing_data_finding(
        category=CATEGORY,
        field_path="creators",
        impact_description=(
            "No creator roster was provided, so Kai cannot evaluate creator fit, "
            "rights posture, rate-card quality, or channel mix risk."
        ),
        how_to_provide=(
            "Provide creators[] fixtures with creator_id/name/platform and baseline "
            "audience metrics before running creator commerce scoring."
        ),
        critical_gap=True,
    )


def _audience_quality_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    creators = [item for item in _as_list(data.get("creators")) if isinstance(item, Mapping)]
    if not creators:
        return None

    missing_metrics = 0
    low_engagement = 0
    for creator in creators:
        followers = creator.get("follower_count")
        engagement_rate = creator.get("engagement_rate")
        if followers is None or engagement_rate is None:
            missing_metrics += 1
            continue
        try:
            if float(engagement_rate) < 0.01:
                low_engagement += 1
        except (TypeError, ValueError):
            missing_metrics += 1

    if not missing_metrics and not low_engagement:
        return None

    severity = FindingSeverity.HIGH.value if missing_metrics else FindingSeverity.MEDIUM.value
    return create_finding(
        category=CATEGORY,
        subcategory="audience_quality",
        severity=severity,
        title="Audience quality inputs are incomplete or weak",
        description=(
            f"{missing_metrics} creators are missing follower/engagement metrics and "
            f"{low_engagement} creators are below a 1% engagement threshold."
        ),
        recommendation=(
            "Capture follower_count and engagement_rate per creator and pause low-quality "
            "partners until audience health is verified."
        ),
        estimated_impact=ImpactLevel.HIGH.value,
        effort=EffortLevel.QUICK_WIN.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="metric",
                value=(
                    f"creators={len(creators)}, missing_metrics={missing_metrics}, "
                    f"low_engagement={low_engagement}"
                ),
                source_label="creator_fixture.creators",
            )
        ],
        tags=["audience_quality", "creator_fit"],
    )


def _rate_card_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    rate_cards = [item for item in _as_list(data.get("rate_cards")) if isinstance(item, Mapping)]
    if not rate_cards:
        return create_missing_data_finding(
            category=CATEGORY,
            field_path="rate_cards",
            impact_description=(
                "Missing rate cards block offer benchmarking and channel-level creator "
                "economics decisions."
            ),
            how_to_provide=(
                "Provide rate_cards[] with creator_id, deliverables, rate_usd, usage_rights_days, "
                "and whitelisting_allowed fields."
            ),
            critical_gap=False,
        )

    incomplete = 0
    for card in rate_cards:
        required = ("creator_id", "deliverables", "rate_usd", "usage_rights_days")
        if any(not _has_text(card.get(field)) for field in required):
            incomplete += 1

    if incomplete == 0:
        return None

    return create_finding(
        category=CATEGORY,
        subcategory="rate_card_hygiene",
        severity=FindingSeverity.MEDIUM.value,
        title="Rate-card coverage is incomplete",
        description=(
            f"{incomplete} of {len(rate_cards)} rate cards are missing critical economic "
            "or usage-rights fields."
        ),
        recommendation=(
            "Normalize rate cards so each creator has explicit deliverables, rate, and usage-rights windows."
        ),
        estimated_impact=ImpactLevel.MEDIUM.value,
        effort=EffortLevel.QUICK_WIN.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="metric",
                value=f"incomplete_rate_cards={incomplete}/{len(rate_cards)}",
                source_label="creator_fixture.rate_cards",
            )
        ],
        tags=["rates", "rights", "economics"],
    )


def _rights_disclosure_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    rights = _as_map(data.get("rights_policy"))
    usage_rights_required = bool(rights.get("usage_rights_required"))
    ftc_disclosure_template = _text(rights.get("ftc_disclosure_template"))
    platform_disclosure = bool(rights.get("platform_disclosure_required"))

    if usage_rights_required and ftc_disclosure_template and platform_disclosure:
        return None

    return create_finding(
        category=CATEGORY,
        subcategory="rights_disclosure",
        severity=FindingSeverity.HIGH.value,
        title="Rights and disclosure policy is incomplete",
        description=(
            "Creator ops needs explicit usage-rights requirements and FTC/platform "
            "disclosure standards before scaling partner output."
        ),
        recommendation=(
            "Define rights_policy with usage_rights_required=true, "
            "platform_disclosure_required=true, and an approved FTC disclosure template."
        ),
        estimated_impact=ImpactLevel.HIGH.value,
        effort=EffortLevel.QUICK_WIN.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="checklist_item",
                value=(
                    f"usage_rights_required={usage_rights_required}; "
                    f"platform_disclosure_required={platform_disclosure}; "
                    f"ftc_template_present={bool(ftc_disclosure_template)}"
                ),
                source_label="creator_fixture.rights_policy",
            )
        ],
        tags=["rights", "disclosure", "compliance"],
    )


def _affiliate_tracking_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    affiliate = _as_map(data.get("affiliate"))
    enabled = bool(affiliate.get("enabled"))
    tracking_template = _text(affiliate.get("tracking_template"))
    payout_terms = _text(affiliate.get("payout_terms"))

    if enabled and tracking_template and payout_terms:
        return None

    return create_finding(
        category=CATEGORY,
        subcategory="affiliate_tracking",
        severity=FindingSeverity.MEDIUM.value,
        title="Affiliate tracking baseline is not ready",
        description=(
            "Creator-linked revenue cannot be trusted without standardized tracking "
            "links and payout policy terms."
        ),
        recommendation=(
            "Enable affiliate tracking with a deterministic link template "
            "(e.g. ?utm_source=creator&utm_campaign=<id>) and document payout terms."
        ),
        estimated_impact=ImpactLevel.MEDIUM.value,
        effort=EffortLevel.MODERATE.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="checklist_item",
                value=(
                    f"enabled={enabled}; tracking_template={bool(tracking_template)}; "
                    f"payout_terms={bool(payout_terms)}"
                ),
                source_label="creator_fixture.affiliate",
            )
        ],
        tags=["affiliate", "attribution"],
    )


def _gmv_data_gap(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    performance = _as_map(data.get("performance"))
    attributed_gmv = performance.get("attributed_gmv")
    order_count = performance.get("order_count")
    attribution_window_days = performance.get("attribution_window_days")

    if attributed_gmv is not None and order_count is not None and attribution_window_days is not None:
        return None

    return create_missing_data_finding(
        category=CATEGORY,
        field_path="performance.attributed_gmv",
        impact_description=(
            "GMV attribution data is incomplete, so creator ROI and partner-level "
            "promotion quality cannot be scored reliably."
        ),
        how_to_provide=(
            "Provide performance.attributed_gmv, performance.order_count, and "
            "performance.attribution_window_days from analytics or fixture exports."
        ),
        critical_gap=False,
    )


def _material_connection_disclosure_finding(data: Mapping[str, Any]) -> Optional[AuditFinding]:
    creators = [item for item in _as_list(data.get("creators")) if isinstance(item, Mapping)]
    if not creators:
        return None

    flagged: List[str] = []
    for creator in creators:
        creator_id = _text(creator.get("creator_id")) or _text(creator.get("name")) or "<unknown>"
        has_connection = False

        connections = _as_list(creator.get("material_connections"))
        if connections:
            has_connection = True
        if bool(creator.get("gifted_product")):
            has_connection = True
        if bool(creator.get("affiliate_enabled")):
            has_connection = True
        relationship_type = _text(creator.get("relationship_type")).lower()
        if relationship_type in {"employee", "founder", "director", "brand_ambassador"}:
            has_connection = True

        if not has_connection:
            continue

        disclosed = creator.get("material_connection_disclosed")
        if disclosed is not True:
            flagged.append(creator_id)

    if not flagged:
        return None

    return create_finding(
        category=CATEGORY,
        subcategory="material_connection_disclosure",
        severity=FindingSeverity.HIGH.value,
        title="Material connection disclosures are missing in creator fixture",
        description=(
            f"{len(flagged)} creator records show gifting, affiliate, or insider relationships "
            "without an explicit material-connection disclosure flag."
        ),
        recommendation=(
            "Set material_connection_disclosed=true for every creator entry with gifting, "
            "affiliate links, or insider/employment relationships, and include the disclosure text template."
        ),
        estimated_impact=ImpactLevel.HIGH.value,
        effort=EffortLevel.QUICK_WIN.value,
        source=FindingSource.USER_PROVIDED.value,
        evidence=[
            Evidence(
                evidence_type="checklist_item",
                value=f"flagged_creators={','.join(flagged)}",
                source_label="creator_fixture.creators",
            )
        ],
        tags=["disclosure", "affiliate", "insider_endorsement"],
    )


def audit_creator_commerce_ops(
    data: Optional[Mapping[str, Any]] = None,
) -> List[AuditFinding]:
    """Run fixture-friendly creator commerce checks and return findings."""
    payload = data or {}
    findings: List[AuditFinding] = []

    for finding in (
        _creator_roster_finding(payload),
        _audience_quality_finding(payload),
        _rate_card_finding(payload),
        _rights_disclosure_finding(payload),
        _affiliate_tracking_finding(payload),
        _gmv_data_gap(payload),
        _material_connection_disclosure_finding(payload),
    ):
        if finding is not None:
            findings.append(finding)

    return findings


_SEVERITY_PENALTIES: Dict[str, int] = {
    FindingSeverity.CRITICAL.value: 30,
    FindingSeverity.HIGH.value: 20,
    FindingSeverity.MEDIUM.value: 10,
    FindingSeverity.LOW.value: 5,
    FindingSeverity.INFO.value: 0,
}


def score_creator_commerce_ops(findings: Sequence[AuditFinding]) -> float:
    """Return a 0-100 creator commerce readiness score."""
    score = 100
    for finding in findings:
        score -= _SEVERITY_PENALTIES.get(finding.severity, 10)
    return max(0.0, float(score))


def summarize_creator_commerce_findings(
    findings: Sequence[AuditFinding],
) -> Dict[str, Any]:
    """Summarize findings into count buckets and score."""
    counts = {
        "critical": 0,
        "high": 0,
        "medium": 0,
        "low": 0,
        "info": 0,
        "missing_data": 0,
    }
    for finding in findings:
        severity = finding.severity.lower()
        if severity in counts:
            counts[severity] += 1
        if finding.source == FindingSource.MISSING_DATA.value:
            counts["missing_data"] += 1

    return {
        "category": CATEGORY,
        "score": score_creator_commerce_ops(findings),
        "counts": counts,
        "total_findings": len(findings),
        "top_titles": [finding.title for finding in findings[:5]],
    }


__all__ = [
    "audit_creator_commerce_ops",
    "score_creator_commerce_ops",
    "summarize_creator_commerce_findings",
]
