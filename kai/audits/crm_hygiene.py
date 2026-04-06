"""CRM and data hygiene audit engine for the Kai Marketing OS.

Examines the health of a business's customer data -- list quality,
segmentation, deliverability indicators, consent compliance, data
completeness, duplicate rate, engagement recency, and source tracking.
Poor data hygiene leads to email deliverability problems, wasted ad spend
on bad audiences, and compliance risks (CAN-SPAM, GDPR, CCPA).

Since CRM data is rarely available in the BusinessProfile alone, this
audit generates many MISSING_DATA findings when ``connected_data`` is
not provided.  That is by design -- it tells the operator what data to
connect for a complete assessment.

Usage::

    from kai.audits.crm_hygiene import audit_crm_hygiene, score_crm_hygiene

    findings = audit_crm_hygiene(profile)
    score    = score_crm_hygiene(findings)

All findings carry ``category = "crm_hygiene"`` or ``"data_quality"``
and use the structured ``AuditFinding`` model from ``kai.models.audit``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORY_CRM = "crm_hygiene"
CATEGORY_DQ = "data_quality"

_LOCAL_SERVICE_ARCHETYPES = {"local-service"}
_ECOMMERCE_ARCHETYPES = {"ecommerce"}
_PROFESSIONAL_SERVICES_ARCHETYPES = {"professional-services"}

# Recommended segments per archetype.
_SEGMENT_RECOMMENDATIONS: Dict[str, str] = {
    "local-service": (
        "Active customers, past customers (90+ days), leads (never purchased), "
        "service type interest, location"
    ),
    "ecommerce": (
        "First-time buyers, repeat buyers, VIPs (top 10%), cart abandoners, "
        "browse abandoners, win-back (90+ days)"
    ),
    "professional-services": (
        "Prospects, active clients, past clients, referral partners, "
        "newsletter subscribers, event attendees"
    ),
}

_DEFAULT_SEGMENT_RECOMMENDATION = (
    "Active customers, past customers (90+ days), leads (never purchased), "
    "engagement level, acquisition source"
)

# Sources that should be tracked for every contact.
_RECOMMENDED_SOURCES = [
    "website form",
    "phone call",
    "referral",
    "event",
    "social media",
    "paid ad",
    "organic search",
    "manual entry",
]


# ============================================================================
# Public API
# ============================================================================


def audit_crm_hygiene(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run all CRM and data hygiene checks against *profile*.

    Parameters
    ----------
    profile:
        The canonical ``BusinessProfile`` to audit.
    connected_data:
        Optional dictionary of CRM/email-platform data from integrations.
        Recognised keys:

        - ``list_size`` (int) -- total contacts in the list
        - ``segment_count`` (int) -- number of distinct segments
        - ``segment_names`` (List[str]) -- names of segments
        - ``bounce_rate`` (float) -- 0.0 to 1.0 (e.g. 0.03 = 3%)
        - ``spam_complaint_rate`` (float) -- 0.0 to 1.0
        - ``inbox_placement_rate`` (float) -- 0.0 to 1.0
        - ``unsubscribe_rate`` (float) -- 0.0 to 1.0 (per campaign)
        - ``field_completeness`` (Dict[str, float]) -- field name to
          percentage (0.0-1.0) of contacts that have a value.
          Expected fields: ``email``, ``phone``, ``source``, ``name``.
        - ``duplicate_rate`` (float) -- 0.0 to 1.0
        - ``recency_distribution`` (Dict[str, float]) -- keys are
          ``"30d"``, ``"90d"``, ``"180d"``, ``"365d"``, ``"365d_plus"``
          with float values summing to 1.0.
        - ``consent_records_present`` (bool) -- whether opt-in
          documentation exists
        - ``contacts_without_consent_pct`` (float) -- 0.0 to 1.0
        - ``source_attribution_pct`` (float) -- fraction of contacts
          with a known acquisition source (0.0 to 1.0)
        - ``source_distribution`` (Dict[str, int]) -- source name to
          count of contacts

    Returns
    -------
    List[AuditFinding]
        All findings from the CRM hygiene audit.  Findings use
        ``category = "crm_hygiene"`` or ``"data_quality"``.
    """
    if connected_data is None:
        connected_data = {}

    archetype = _resolve_archetype(profile)

    findings: List[AuditFinding] = []
    findings.extend(_check_contact_list_size(connected_data, archetype))
    findings.extend(_check_list_segmentation(connected_data, archetype))
    findings.extend(_check_email_deliverability(connected_data))
    findings.extend(_check_unsubscribe_rate(connected_data))
    findings.extend(_check_data_completeness(connected_data, archetype))
    findings.extend(_check_duplicate_detection(connected_data))
    findings.extend(_check_last_contact_recency(connected_data))
    findings.extend(_check_consent_opt_in(connected_data))
    findings.extend(_check_data_source_tracking(connected_data))
    findings.extend(_check_overall_data_health(findings, connected_data))

    return findings


def score_crm_hygiene(findings: List[AuditFinding]) -> float:
    """Score the CRM/data-hygiene dimension on a 0-100 scale.

    Consent and compliance findings (subcategory ``"consent_opt_in"``) are
    weighted 2x because compliance is non-negotiable.

    If more than 70% of findings have ``source = MISSING_DATA``, the score
    is set to 50 (neutral/unknown) rather than penalising for gaps.

    Severity penalties mirror ``compute_category_scorecard``::

        CRITICAL -> 25, HIGH -> 15, MEDIUM -> 8, LOW -> 3, INFO -> 0

    Parameters
    ----------
    findings:
        The list produced by ``audit_crm_hygiene``.

    Returns
    -------
    float
        A score clamped to [0, 100], rounded to one decimal place.
    """
    if not findings:
        return 50.0

    # Check if mostly MISSING_DATA -- return neutral score.
    missing_count = sum(
        1 for f in findings
        if getattr(f, "source", None) == FindingSource.MISSING_DATA.value
    )
    if len(findings) > 0 and (missing_count / len(findings)) > 0.70:
        return 50.0

    severity_penalty = {
        FindingSeverity.CRITICAL.value: 25,
        FindingSeverity.HIGH.value: 15,
        FindingSeverity.MEDIUM.value: 8,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 0,
    }

    # Subcategories that receive 2x weight (compliance).
    compliance_subs = {"consent_opt_in"}

    total_penalty = 0.0
    for f in findings:
        # Skip the overall summary finding from penalty calculation to
        # avoid double-counting.
        if getattr(f, "subcategory", None) == "overall_health_summary":
            continue
        base = severity_penalty.get(f.severity, 0)
        weight = 2 if getattr(f, "subcategory", None) in compliance_subs else 1
        total_penalty += base * weight

    return round(max(0.0, min(100.0, 100.0 - total_penalty)), 1)


def assess_list_health_tier(
    bounce_rate: Optional[float] = None,
    spam_rate: Optional[float] = None,
    unsub_rate: Optional[float] = None,
) -> str:
    """Classify overall list health from available deliverability metrics.

    Parameters
    ----------
    bounce_rate:
        Bounce rate as a fraction (e.g. 0.02 = 2%).
    spam_rate:
        Spam complaint rate as a fraction (e.g. 0.001 = 0.1%).
    unsub_rate:
        Unsubscribe rate per campaign as a fraction (e.g. 0.005 = 0.5%).

    Returns
    -------
    str
        One of ``"healthy"``, ``"at_risk"``, ``"critical"``, or
        ``"unknown"`` if all inputs are None.
    """
    if bounce_rate is None and spam_rate is None and unsub_rate is None:
        return "unknown"

    # Check for critical thresholds first.
    if bounce_rate is not None and bounce_rate > 0.05:
        return "critical"
    if spam_rate is not None and spam_rate > 0.003:
        return "critical"
    if unsub_rate is not None and unsub_rate > 0.01:
        return "critical"

    # Check for at-risk thresholds.
    if bounce_rate is not None and bounce_rate > 0.02:
        return "at_risk"
    if spam_rate is not None and spam_rate > 0.001:
        return "at_risk"
    if unsub_rate is not None and unsub_rate > 0.005:
        return "at_risk"

    return "healthy"


# ============================================================================
# Internal: individual checks
# ============================================================================


def _resolve_archetype(profile: BusinessProfile) -> str:
    """Return the normalised archetype string from the profile."""
    classification = getattr(profile, "classification", None)
    if classification is not None:
        archetype = getattr(classification, "archetype", None)
        if archetype:
            return archetype
    return "local-service"  # sensible default


def _pct_display(value: float) -> str:
    """Format a 0-1 fraction as a human-readable percentage string."""
    return f"{value * 100:.1f}%"


# ── Check 1: Contact List Size ──────────────────────────────────────────────


def _check_contact_list_size(
    connected_data: Dict[str, Any],
    archetype: str,
) -> List[AuditFinding]:
    """Evaluate contact list size relative to business archetype."""
    findings: List[AuditFinding] = []
    list_size = connected_data.get("list_size")

    if list_size is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY_CRM,
            field_path="connected_data.list_size",
            impact_description=(
                "Contact list size unknown -- connect your email platform "
                "or CRM to assess data health"
            ),
            how_to_provide=(
                "Connect your email platform (Mailchimp, Klaviyo, ActiveCampaign, "
                "HubSpot, etc.) or export your contact list size."
            ),
        ))
        return findings

    # Evaluate by archetype.
    if archetype in _ECOMMERCE_ARCHETYPES:
        if list_size < 1000:
            severity = FindingSeverity.LOW.value
            desc = (
                f"Email list has {list_size:,} contacts -- small for an ecommerce "
                f"business. Most ecommerce brands need 10K+ contacts for effective "
                f"email-driven revenue."
            )
        elif list_size < 10000:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Email list has {list_size:,} contacts -- medium-sized list. "
                f"Continue growing toward 10K+ for strong email revenue potential."
            )
        elif list_size < 50000:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Email list has {list_size:,} contacts -- good foundation for "
                f"email marketing revenue."
            )
        else:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Email list has {list_size:,} contacts -- strong list size for "
                f"ecommerce. Focus on segmentation and engagement quality."
            )
    elif archetype in _PROFESSIONAL_SERVICES_ARCHETYPES:
        if list_size < 50:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Contact list has {list_size:,} contacts -- just starting. "
                f"For professional services, even a small well-targeted list "
                f"can drive results."
            )
        elif list_size < 200:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Contact list has {list_size:,} contacts -- good start for "
                f"a B2B/professional services business."
            )
        else:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Contact list has {list_size:,} contacts -- strong foundation "
                f"for a professional services business."
            )
    else:
        # Default: local-service and other archetypes.
        if list_size < 100:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Contact list has {list_size:,} contacts -- just getting started. "
                f"Prioritise building your list through website capture, social, "
                f"and in-person collection."
            )
        elif list_size < 500:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Contact list has {list_size:,} contacts -- good start for a "
                f"local service business."
            )
        else:
            severity = FindingSeverity.INFO.value
            desc = (
                f"Contact list has {list_size:,} contacts -- strong foundation "
                f"for a local service business."
            )

    findings.append(create_finding(
        category=CATEGORY_CRM,
        severity=severity,
        title=f"Contact list size: {list_size:,}",
        description=desc,
        recommendation=(
            "Track your contact list size monthly. Set growth targets: aim for "
            "3-5% monthly list growth through website capture, social, and "
            "event collection."
        ),
        subcategory="contact_list_size",
        source=FindingSource.CONNECTED.value,
        effort=EffortLevel.ONGOING.value,
        estimated_impact=ImpactLevel.MEDIUM.value,
        evidence=[
            Evidence(
                evidence_type="metric",
                value=str(list_size),
                context=f"Total contacts in CRM/email platform",
                source_label="Connected CRM data",
            ),
        ],
        tags=["crm", "list_growth"],
        archetype_relevance=[archetype],
        metadata={"list_size": list_size, "archetype": archetype},
    ))

    return findings


# ── Check 2: List Segmentation Quality ──────────────────────────────────────


def _check_list_segmentation(
    connected_data: Dict[str, Any],
    archetype: str,
) -> List[AuditFinding]:
    """Evaluate the quality and depth of list segmentation."""
    findings: List[AuditFinding] = []
    segment_count = connected_data.get("segment_count")
    segment_names = connected_data.get("segment_names", [])

    if segment_count is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY_CRM,
            field_path="connected_data.segment_count",
            impact_description="List segmentation data not available",
            how_to_provide=(
                "Connect your email platform and provide the number of "
                "segments/lists and their names."
            ),
        ))
        return findings

    seg_rec = _SEGMENT_RECOMMENDATIONS.get(archetype, _DEFAULT_SEGMENT_RECOMMENDATION)

    if segment_count <= 1:
        severity = FindingSeverity.HIGH.value
        title = "No list segmentation"
        desc = (
            "No list segmentation -- sending the same message to everyone "
            "reduces engagement and increases unsubscribes"
        )
        impact = ImpactLevel.HIGH.value
    elif segment_count <= 5:
        severity = FindingSeverity.MEDIUM.value
        title = f"Basic segmentation ({segment_count} segments)"
        desc = (
            f"Basic segmentation in place with {segment_count} segments -- "
            f"expand with behavioral and purchase-based segments"
        )
        impact = ImpactLevel.MEDIUM.value
    else:
        severity = FindingSeverity.INFO.value
        title = f"Strong segmentation ({segment_count} segments)"
        desc = f"Strong segmentation structure with {segment_count} segments"
        impact = ImpactLevel.LOW.value

    evidence_items = [
        Evidence(
            evidence_type="metric",
            value=str(segment_count),
            context="Number of distinct audience segments",
            source_label="Connected CRM data",
        ),
    ]
    if segment_names:
        evidence_items.append(
            Evidence(
                evidence_type="text",
                value=", ".join(segment_names),
                context="Current segment names",
                source_label="Connected CRM data",
            )
        )

    findings.append(create_finding(
        category=CATEGORY_CRM,
        severity=severity,
        title=title,
        description=desc,
        recommendation=f"Recommended segments for {archetype}: {seg_rec}",
        subcategory="list_segmentation",
        source=FindingSource.CONNECTED.value,
        effort=EffortLevel.MODERATE.value,
        estimated_impact=impact,
        evidence=evidence_items,
        tags=["crm", "segmentation"],
        archetype_relevance=[archetype],
        metadata={
            "segment_count": segment_count,
            "segment_names": segment_names,
            "archetype": archetype,
        },
    ))

    return findings


# ── Check 3: Email Deliverability Indicators ────────────────────────────────


def _check_email_deliverability(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Evaluate bounce rate, spam complaint rate, and inbox placement."""
    findings: List[AuditFinding] = []
    bounce_rate = connected_data.get("bounce_rate")
    spam_rate = connected_data.get("spam_complaint_rate")
    inbox_rate = connected_data.get("inbox_placement_rate")

    has_any = bounce_rate is not None or spam_rate is not None or inbox_rate is not None

    if not has_any:
        findings.append(create_missing_data_finding(
            category=CATEGORY_CRM,
            field_path="connected_data.deliverability_metrics",
            impact_description=(
                "Email deliverability metrics not available -- connect your "
                "email platform"
            ),
            how_to_provide=(
                "Connect your email platform to provide bounce rate, spam "
                "complaint rate, and inbox placement rate."
            ),
            critical_gap=True,
        ))
        return findings

    # --- Bounce rate ---
    if bounce_rate is not None:
        if bounce_rate > 0.05:
            severity = FindingSeverity.HIGH.value
            title = f"Bounce rate above 5% ({_pct_display(bounce_rate)})"
            desc = (
                f"Bounce rate is {_pct_display(bounce_rate)} -- list needs "
                f"cleaning to protect sender reputation"
            )
        elif bounce_rate > 0.02:
            severity = FindingSeverity.MEDIUM.value
            title = f"Bounce rate elevated ({_pct_display(bounce_rate)})"
            desc = (
                f"Bounce rate is {_pct_display(bounce_rate)} -- above the 2% "
                f"healthy threshold. Clean invalid addresses promptly."
            )
        else:
            severity = FindingSeverity.INFO.value
            title = f"Bounce rate healthy ({_pct_display(bounce_rate)})"
            desc = f"Bounce rate is {_pct_display(bounce_rate)} -- within healthy range"

        findings.append(create_finding(
            category=CATEGORY_CRM,
            severity=severity,
            title=title,
            description=desc,
            recommendation=(
                "Monitor bounce rate monthly. Clean bounced addresses immediately. "
                "Investigate spam complaints for opt-in gaps."
            ),
            subcategory="bounce_rate",
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=_pct_display(bounce_rate),
                    context="Email bounce rate",
                    source_label="Connected email platform",
                ),
            ],
            tags=["crm", "deliverability", "bounce"],
            metadata={"bounce_rate": bounce_rate},
        ))

    # --- Spam complaint rate ---
    if spam_rate is not None:
        if spam_rate > 0.003:
            severity = FindingSeverity.CRITICAL.value
            title = f"Spam complaint rate above 0.3% ({_pct_display(spam_rate)})"
            desc = (
                f"Spam complaint rate is {_pct_display(spam_rate)} -- risk of "
                f"email provider blacklisting"
            )
        elif spam_rate > 0.001:
            severity = FindingSeverity.MEDIUM.value
            title = f"Spam complaint rate elevated ({_pct_display(spam_rate)})"
            desc = (
                f"Spam complaint rate is {_pct_display(spam_rate)} -- above the "
                f"0.1% healthy threshold. Review opt-in process."
            )
        else:
            severity = FindingSeverity.INFO.value
            title = f"Spam complaint rate healthy ({_pct_display(spam_rate)})"
            desc = (
                f"Spam complaint rate is {_pct_display(spam_rate)} -- within "
                f"healthy range"
            )

        findings.append(create_finding(
            category=CATEGORY_CRM,
            severity=severity,
            title=title,
            description=desc,
            recommendation=(
                "Monitor spam complaint rate monthly. If elevated: review "
                "opt-in process, add unsubscribe links to all emails, and "
                "honour opt-outs within 10 business days (CAN-SPAM)."
            ),
            subcategory="spam_complaint_rate",
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=_pct_display(spam_rate),
                    context="Email spam complaint rate",
                    source_label="Connected email platform",
                ),
            ],
            tags=["crm", "deliverability", "spam", "compliance"],
            metadata={"spam_complaint_rate": spam_rate},
        ))

    # --- Inbox placement rate ---
    if inbox_rate is not None:
        if inbox_rate < 0.85:
            severity = FindingSeverity.HIGH.value
            title = f"Inbox placement below 85% ({_pct_display(inbox_rate)})"
            desc = (
                f"Inbox placement rate is {_pct_display(inbox_rate)} -- "
                f"a significant portion of emails are going to spam or "
                f"being blocked"
            )
        elif inbox_rate < 0.95:
            severity = FindingSeverity.MEDIUM.value
            title = f"Inbox placement below 95% ({_pct_display(inbox_rate)})"
            desc = (
                f"Inbox placement rate is {_pct_display(inbox_rate)} -- "
                f"some emails may be landing in spam folders"
            )
        else:
            severity = FindingSeverity.INFO.value
            title = f"Inbox placement healthy ({_pct_display(inbox_rate)})"
            desc = (
                f"Inbox placement rate is {_pct_display(inbox_rate)} -- "
                f"emails are reaching inboxes"
            )

        findings.append(create_finding(
            category=CATEGORY_CRM,
            severity=severity,
            title=title,
            description=desc,
            recommendation=(
                "Monitor inbox placement rate. If below 95%: check sender "
                "authentication (SPF, DKIM, DMARC), reduce bounce rate, "
                "and review content for spam triggers."
            ),
            subcategory="inbox_placement",
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=_pct_display(inbox_rate),
                    context="Email inbox placement rate",
                    source_label="Connected email platform",
                ),
            ],
            tags=["crm", "deliverability", "inbox"],
            metadata={"inbox_placement_rate": inbox_rate},
        ))

    return findings


# ── Check 4: Unsubscribe Rate ───────────────────────────────────────────────


def _check_unsubscribe_rate(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Evaluate per-campaign unsubscribe rate."""
    findings: List[AuditFinding] = []
    unsub_rate = connected_data.get("unsubscribe_rate")

    if unsub_rate is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY_CRM,
            field_path="connected_data.unsubscribe_rate",
            impact_description=(
                "Unsubscribe rate not available -- cannot assess list "
                "engagement health"
            ),
            how_to_provide=(
                "Connect your email platform to provide the average "
                "unsubscribe rate per campaign."
            ),
        ))
        return findings

    if unsub_rate > 0.01:
        severity = FindingSeverity.HIGH.value
        title = f"High unsubscribe rate ({_pct_display(unsub_rate)})"
        desc = (
            f"High unsubscribe rate of {_pct_display(unsub_rate)} per campaign "
            f"-- either sending too frequently, content is irrelevant, or list "
            f"was acquired without proper consent"
        )
    elif unsub_rate > 0.005:
        severity = FindingSeverity.MEDIUM.value
        title = f"Elevated unsubscribe rate ({_pct_display(unsub_rate)})"
        desc = (
            f"Unsubscribe rate is {_pct_display(unsub_rate)} per campaign "
            f"-- review email frequency and content relevance"
        )
    else:
        severity = FindingSeverity.INFO.value
        title = f"Healthy unsubscribe rate ({_pct_display(unsub_rate)})"
        desc = (
            f"Unsubscribe rate is {_pct_display(unsub_rate)} per campaign "
            f"-- within healthy range"
        )

    findings.append(create_finding(
        category=CATEGORY_CRM,
        severity=severity,
        title=title,
        description=desc,
        recommendation=(
            "If unsubscribe rate is high: (1) Reduce send frequency, "
            "(2) Improve segmentation, (3) Review content relevance, "
            "(4) Add preference center"
        ),
        subcategory="unsubscribe_rate",
        source=FindingSource.CONNECTED.value,
        effort=EffortLevel.MODERATE.value,
        estimated_impact=ImpactLevel.MEDIUM.value,
        evidence=[
            Evidence(
                evidence_type="metric",
                value=_pct_display(unsub_rate),
                context="Average unsubscribe rate per campaign",
                source_label="Connected email platform",
            ),
        ],
        tags=["crm", "engagement", "unsubscribe"],
        metadata={"unsubscribe_rate": unsub_rate},
    ))

    return findings


# ── Check 5: Data Completeness ──────────────────────────────────────────────


def _check_data_completeness(
    connected_data: Dict[str, Any],
    archetype: str,
) -> List[AuditFinding]:
    """Evaluate what percentage of contacts have key fields populated."""
    findings: List[AuditFinding] = []
    field_completeness = connected_data.get("field_completeness")

    if field_completeness is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY_DQ,
            field_path="connected_data.field_completeness",
            impact_description=(
                "Contact data completeness metrics not available"
            ),
            how_to_provide=(
                "Export or connect your CRM to provide field completeness "
                "percentages for email, phone, name, and lead source."
            ),
        ))
        return findings

    evidence_items: List[Evidence] = []

    # --- Email completeness ---
    email_pct = field_completeness.get("email")
    if email_pct is not None:
        evidence_items.append(
            Evidence(
                evidence_type="metric",
                value=_pct_display(email_pct),
                context="Contacts with email address",
                source_label="Connected CRM data",
            )
        )
        if email_pct < 1.0:
            findings.append(create_finding(
                category=CATEGORY_DQ,
                severity=FindingSeverity.MEDIUM.value,
                title=f"Email completeness: {_pct_display(email_pct)}",
                description=(
                    f"Some contacts are missing email addresses "
                    f"({_pct_display(email_pct)} have email). Email should "
                    f"be present for 100% of marketing contacts."
                ),
                recommendation=(
                    "Audit contacts missing email addresses. Remove or "
                    "enrich records that lack email."
                ),
                subcategory="field_completeness_email",
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.MEDIUM.value,
                evidence=[
                    Evidence(
                        evidence_type="metric",
                        value=_pct_display(email_pct),
                        context="Contacts with email address",
                        source_label="Connected CRM data",
                    ),
                ],
                tags=["data_quality", "completeness"],
                metadata={"email_completeness": email_pct},
            ))

    # --- Phone completeness ---
    phone_pct = field_completeness.get("phone")
    if phone_pct is not None:
        evidence_items.append(
            Evidence(
                evidence_type="metric",
                value=_pct_display(phone_pct),
                context="Contacts with phone number",
                source_label="Connected CRM data",
            )
        )
        phone_threshold = 0.30 if archetype in _LOCAL_SERVICE_ARCHETYPES else 0.50
        if phone_pct < phone_threshold:
            phone_desc = (
                f"Only {_pct_display(phone_pct)} of contacts have phone numbers"
            )
            if archetype in _LOCAL_SERVICE_ARCHETYPES:
                phone_desc += (
                    " -- phone is a primary communication channel for "
                    "local service businesses"
                )
                severity = FindingSeverity.MEDIUM.value
                impact = ImpactLevel.HIGH.value
                kaicalls = True
            else:
                severity = FindingSeverity.LOW.value
                impact = ImpactLevel.MEDIUM.value
                kaicalls = False

            findings.append(create_finding(
                category=CATEGORY_DQ,
                severity=severity,
                title=f"Phone completeness: {_pct_display(phone_pct)}",
                description=phone_desc,
                recommendation=(
                    "Collect phone numbers at point of contact. For service "
                    "businesses, phone is often the primary engagement channel. "
                    "Consider KaiCalls AI receptionist (kaicalls.com) to capture "
                    "every inbound call as a contact record."
                ),
                subcategory="field_completeness_phone",
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=impact,
                evidence=[
                    Evidence(
                        evidence_type="metric",
                        value=_pct_display(phone_pct),
                        context="Contacts with phone number",
                        source_label="Connected CRM data",
                    ),
                ],
                tags=["data_quality", "completeness", "phone"],
                kaicalls_relevant=kaicalls,
                metadata={"phone_completeness": phone_pct, "archetype": archetype},
            ))

    # --- Source/origin completeness ---
    source_pct = field_completeness.get("source")
    if source_pct is not None:
        evidence_items.append(
            Evidence(
                evidence_type="metric",
                value=_pct_display(source_pct),
                context="Contacts with source attribution",
                source_label="Connected CRM data",
            )
        )
        if source_pct < 0.50:
            findings.append(create_finding(
                category=CATEGORY_DQ,
                severity=FindingSeverity.MEDIUM.value,
                title=f"Source attribution: {_pct_display(source_pct)}",
                description=(
                    f"Over half of contacts have no source attribution -- "
                    f"cannot measure which channels drive the best leads"
                ),
                recommendation=(
                    "Tag every new contact with their acquisition source at "
                    "the point of entry. This data is essential for "
                    "calculating channel ROI."
                ),
                subcategory="field_completeness_source",
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                evidence=[
                    Evidence(
                        evidence_type="metric",
                        value=_pct_display(source_pct),
                        context="Contacts with source attribution",
                        source_label="Connected CRM data",
                    ),
                ],
                tags=["data_quality", "completeness", "attribution"],
                metadata={"source_completeness": source_pct},
            ))

    # --- Name completeness ---
    name_pct = field_completeness.get("name")
    if name_pct is not None:
        evidence_items.append(
            Evidence(
                evidence_type="metric",
                value=_pct_display(name_pct),
                context="Contacts with name",
                source_label="Connected CRM data",
            )
        )
        if name_pct < 0.90:
            findings.append(create_finding(
                category=CATEGORY_DQ,
                severity=FindingSeverity.LOW.value,
                title=f"Name completeness: {_pct_display(name_pct)}",
                description=(
                    f"Only {_pct_display(name_pct)} of contacts have a name "
                    f"on file. Personalisation (subject lines, greetings) "
                    f"requires name data."
                ),
                recommendation=(
                    "Collect first name at minimum in all forms. "
                    "Enrich existing records through progressive profiling."
                ),
                subcategory="field_completeness_name",
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                evidence=[
                    Evidence(
                        evidence_type="metric",
                        value=_pct_display(name_pct),
                        context="Contacts with name",
                        source_label="Connected CRM data",
                    ),
                ],
                tags=["data_quality", "completeness"],
                metadata={"name_completeness": name_pct},
            ))

    # Generate a summary finding for data completeness if we have evidence.
    if evidence_items:
        all_good = True
        for ev in evidence_items:
            try:
                val = float(ev.value.rstrip("%")) / 100.0
                if val < 0.80:
                    all_good = False
                    break
            except (ValueError, AttributeError):
                pass

        if all_good:
            findings.append(create_finding(
                category=CATEGORY_DQ,
                severity=FindingSeverity.INFO.value,
                title="Data completeness: acceptable across key fields",
                description=(
                    "Core contact fields are reasonably well populated."
                ),
                recommendation=(
                    "Audit your contact records for completeness. Prioritise: "
                    "email (required), phone (important for service businesses), "
                    "lead source (essential for attribution), and last contact date."
                ),
                subcategory="field_completeness_summary",
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.ONGOING.value,
                estimated_impact=ImpactLevel.LOW.value,
                evidence=evidence_items,
                tags=["data_quality", "completeness"],
            ))

    return findings


# ── Check 6: Duplicate Detection ────────────────────────────────────────────


def _check_duplicate_detection(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check for duplicate contacts in the database."""
    findings: List[AuditFinding] = []
    duplicate_rate = connected_data.get("duplicate_rate")

    if duplicate_rate is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY_DQ,
            field_path="connected_data.duplicate_rate",
            impact_description=(
                "Duplicate contact rate not available -- cannot assess "
                "data cleanliness"
            ),
            how_to_provide=(
                "Run a deduplication analysis on your CRM: match on email "
                "address first, then phone number, then name + address."
            ),
        ))
        return findings

    if duplicate_rate > 0.05:
        severity = FindingSeverity.MEDIUM.value
        title = f"Duplicate contacts detected ({_pct_display(duplicate_rate)})"
        desc = (
            f"Duplicate contacts detected ({_pct_display(duplicate_rate)}) "
            f"-- duplicates waste email sends and skew reporting"
        )
    else:
        severity = FindingSeverity.INFO.value
        title = f"Low duplicate rate ({_pct_display(duplicate_rate)})"
        desc = f"Low duplicate rate of {_pct_display(duplicate_rate)}"

    findings.append(create_finding(
        category=CATEGORY_DQ,
        severity=severity,
        title=title,
        description=desc,
        recommendation=(
            "Run a deduplication process: match on email address first, then "
            "phone number, then name + address. Merge duplicates, keeping "
            "the most complete record."
        ),
        subcategory="duplicate_detection",
        source=FindingSource.CONNECTED.value,
        effort=EffortLevel.MODERATE.value,
        estimated_impact=ImpactLevel.MEDIUM.value,
        evidence=[
            Evidence(
                evidence_type="metric",
                value=_pct_display(duplicate_rate),
                context="Estimated duplicate contact rate",
                source_label="Connected CRM data",
            ),
        ],
        tags=["data_quality", "duplicates"],
        metadata={"duplicate_rate": duplicate_rate},
    ))

    return findings


# ── Check 7: Last-Contact Recency Distribution ──────────────────────────────


def _check_last_contact_recency(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Evaluate how recently contacts have been engaged."""
    findings: List[AuditFinding] = []
    recency = connected_data.get("recency_distribution")

    if recency is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY_CRM,
            field_path="connected_data.recency_distribution",
            impact_description=(
                "Contact engagement recency data not available -- cannot "
                "assess list freshness"
            ),
            how_to_provide=(
                "Export last-contact or last-activity dates from your CRM "
                "to enable recency analysis."
            ),
        ))
        return findings

    dormant_pct = recency.get("365d_plus", 0.0)

    # Build evidence from all recency buckets.
    evidence_items = []
    bucket_labels = {
        "30d": "Active (last 30 days)",
        "90d": "Recent (31-90 days)",
        "180d": "Cooling (91-180 days)",
        "365d": "Dormant (181-365 days)",
        "365d_plus": "Dead (365+ days)",
    }
    for bucket_key, label in bucket_labels.items():
        val = recency.get(bucket_key)
        if val is not None:
            evidence_items.append(
                Evidence(
                    evidence_type="metric",
                    value=_pct_display(val),
                    context=label,
                    source_label="Connected CRM data",
                )
            )

    if dormant_pct > 0.40:
        severity = FindingSeverity.HIGH.value
        title = f"Over 40% of list dormant ({_pct_display(dormant_pct)} 365+ days)"
        desc = (
            f"Over 40% of your list is dormant (no contact in 12+ months) "
            f"-- these contacts may be invalid and harm deliverability"
        )
    elif dormant_pct > 0.20:
        severity = FindingSeverity.MEDIUM.value
        title = f"Significant dormant portion ({_pct_display(dormant_pct)} 365+ days)"
        desc = (
            f"Significant portion of list is dormant "
            f"({_pct_display(dormant_pct)} with no contact in 12+ months)"
        )
    else:
        severity = FindingSeverity.INFO.value
        title = f"Healthy engagement distribution ({_pct_display(dormant_pct)} dormant)"
        desc = "Healthy engagement distribution across the contact list"

    findings.append(create_finding(
        category=CATEGORY_CRM,
        severity=severity,
        title=title,
        description=desc,
        recommendation=(
            "Segment contacts by last activity: Active (0-90 days), "
            "Cooling (90-180 days), Dormant (180-365 days), Dead (365+ days). "
            "Create win-back campaigns for Cooling/Dormant. Suppress or "
            "remove Dead."
        ),
        subcategory="recency_distribution",
        source=FindingSource.CONNECTED.value,
        effort=EffortLevel.MODERATE.value,
        estimated_impact=ImpactLevel.HIGH.value,
        evidence=evidence_items,
        tags=["crm", "engagement", "recency"],
        metadata={"recency_distribution": recency, "dormant_pct": dormant_pct},
    ))

    return findings


# ── Check 8: Consent and Opt-In Status ──────────────────────────────────────


def _check_consent_opt_in(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Evaluate consent records and opt-in compliance."""
    findings: List[AuditFinding] = []
    consent_present = connected_data.get("consent_records_present")
    no_consent_pct = connected_data.get("contacts_without_consent_pct")

    compliance_details = (
        "CAN-SPAM: Every commercial email must include physical address, "
        "unsubscribe link, and be sent only to contacts who have not opted out. "
        "GDPR: EU contacts require explicit opt-in consent with documented "
        "proof, right to be forgotten, and data portability. "
        "CCPA: California residents have the right to know what data is "
        "collected and request deletion."
    )

    if consent_present is None:
        # No data at all about consent -- this is a medium advisory by spec.
        findings.append(create_finding(
            category=CATEGORY_CRM,
            severity=FindingSeverity.MEDIUM.value,
            title="Consent and opt-in status not tracked",
            description=(
                "Consent and opt-in status should be tracked for every "
                "contact -- CAN-SPAM requires demonstrable consent for "
                "commercial email, GDPR requires explicit opt-in for EU "
                "contacts"
            ),
            recommendation=(
                f"Implement consent tracking for every contact. {compliance_details}"
            ),
            subcategory="consent_opt_in",
            source=FindingSource.INFERRED.value,
            effort=EffortLevel.SIGNIFICANT.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value="No consent tracking data provided",
                    context="Compliance risk assessment",
                    source_label="Audit data completeness check",
                ),
            ],
            tags=["crm", "compliance", "consent", "gdpr", "can-spam", "ccpa"],
            metadata={"compliance_details": compliance_details},
        ))
        return findings

    if consent_present is False or (no_consent_pct is not None and no_consent_pct > 0):
        # Some or all contacts lack consent records.
        pct_display = _pct_display(no_consent_pct) if no_consent_pct is not None else "unknown %"
        findings.append(create_finding(
            category=CATEGORY_CRM,
            severity=FindingSeverity.HIGH.value,
            title="Contacts without consent records",
            description=(
                f"Contacts without consent records ({pct_display}) pose "
                f"compliance risk under CAN-SPAM, GDPR, and CCPA"
            ),
            recommendation=(
                f"Audit all contacts for consent records. Re-confirm consent "
                f"for contacts without documented opt-in. {compliance_details}"
            ),
            subcategory="consent_opt_in",
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.SIGNIFICANT.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=pct_display,
                    context="Contacts without consent records",
                    source_label="Connected CRM data",
                ),
            ],
            tags=["crm", "compliance", "consent", "gdpr", "can-spam", "ccpa"],
            metadata={
                "contacts_without_consent_pct": no_consent_pct,
                "compliance_details": compliance_details,
            },
        ))
    else:
        findings.append(create_finding(
            category=CATEGORY_CRM,
            severity=FindingSeverity.INFO.value,
            title="Consent records present for all contacts",
            description="Consent records present for all contacts",
            recommendation=(
                f"Continue maintaining consent records. {compliance_details}"
            ),
            subcategory="consent_opt_in",
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.ONGOING.value,
            estimated_impact=ImpactLevel.LOW.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value="All contacts have consent records",
                    context="Compliance status",
                    source_label="Connected CRM data",
                ),
            ],
            tags=["crm", "compliance", "consent"],
        ))

    return findings


# ── Check 9: Data Source Tracking ────────────────────────────────────────────


def _check_data_source_tracking(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Evaluate whether contacts have known acquisition sources."""
    findings: List[AuditFinding] = []
    source_pct = connected_data.get("source_attribution_pct")
    source_dist = connected_data.get("source_distribution")

    if source_pct is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY_DQ,
            field_path="connected_data.source_attribution_pct",
            impact_description=(
                "Contact source attribution data not available -- cannot "
                "measure which channels drive the best leads"
            ),
            how_to_provide=(
                "Export or connect your CRM to provide the percentage of "
                "contacts with a known acquisition source."
            ),
        ))
        return findings

    if source_pct >= 0.80:
        severity = FindingSeverity.INFO.value
        title = f"Strong source tracking ({_pct_display(source_pct)})"
        desc = f"Strong source tracking -- {_pct_display(source_pct)} of contacts have a known source"
    elif source_pct >= 0.50:
        severity = FindingSeverity.MEDIUM.value
        gap_pct = _pct_display(1.0 - source_pct)
        title = f"Source tracking gaps ({_pct_display(source_pct)} tracked)"
        desc = (
            f"Source tracking gaps -- {gap_pct} of contacts have unknown origin"
        )
    else:
        severity = FindingSeverity.HIGH.value
        title = f"Most contacts lack source attribution ({_pct_display(source_pct)})"
        desc = (
            f"Most contacts have no source attribution -- impossible to "
            f"measure which channels drive the best leads"
        )

    evidence_items = [
        Evidence(
            evidence_type="metric",
            value=_pct_display(source_pct),
            context="Contacts with known acquisition source",
            source_label="Connected CRM data",
        ),
    ]

    if source_dist:
        dist_summary = ", ".join(
            f"{src}: {count}" for src, count in sorted(
                source_dist.items(), key=lambda x: x[1], reverse=True
            )[:5]
        )
        evidence_items.append(
            Evidence(
                evidence_type="text",
                value=dist_summary,
                context="Top acquisition sources",
                source_label="Connected CRM data",
            )
        )

    rec_sources = ", ".join(_RECOMMENDED_SOURCES)

    findings.append(create_finding(
        category=CATEGORY_DQ,
        severity=severity,
        title=title,
        description=desc,
        recommendation=(
            f"Tag every new contact with their acquisition source at the "
            f"point of entry. This data is essential for calculating channel "
            f"ROI. Recommended sources to track: {rec_sources}."
        ),
        subcategory="source_tracking",
        source=FindingSource.CONNECTED.value,
        effort=EffortLevel.MODERATE.value,
        estimated_impact=ImpactLevel.HIGH.value,
        evidence=evidence_items,
        tags=["data_quality", "attribution", "source_tracking"],
        metadata={
            "source_attribution_pct": source_pct,
            "source_distribution": source_dist,
        },
    ))

    return findings


# ── Check 10: Overall Data Health Summary ────────────────────────────────────


def _check_overall_data_health(
    prior_findings: List[AuditFinding],
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Generate a composite finding summarising overall CRM health.

    Categories:
    - "clean": low bounce, good segmentation, complete data
    - "needs_attention": some issues
    - "poor": multiple critical issues
    """
    findings: List[AuditFinding] = []

    # Count severities from prior findings (excluding MISSING_DATA source).
    critical_count = 0
    high_count = 0
    medium_count = 0
    low_count = 0
    info_count = 0
    missing_count = 0
    total_count = len(prior_findings)

    for f in prior_findings:
        src = getattr(f, "source", FindingSource.STATIC.value)
        if src == FindingSource.MISSING_DATA.value:
            missing_count += 1
            continue

        sev = f.severity
        if sev == FindingSeverity.CRITICAL.value:
            critical_count += 1
        elif sev == FindingSeverity.HIGH.value:
            high_count += 1
        elif sev == FindingSeverity.MEDIUM.value:
            medium_count += 1
        elif sev == FindingSeverity.LOW.value:
            low_count += 1
        elif sev == FindingSeverity.INFO.value:
            info_count += 1

    # Determine health tier.
    if critical_count > 0 or high_count >= 3:
        health_tier = "poor"
    elif high_count > 0 or medium_count >= 3:
        health_tier = "needs_attention"
    else:
        health_tier = "clean"

    # Build the top 3 actions list.
    top_actions: List[str] = []

    # Collect non-info, non-missing-data findings sorted by severity.
    severity_order = {
        FindingSeverity.CRITICAL.value: 0,
        FindingSeverity.HIGH.value: 1,
        FindingSeverity.MEDIUM.value: 2,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 4,
    }
    actionable = sorted(
        [
            f for f in prior_findings
            if (
                getattr(f, "source", "") != FindingSource.MISSING_DATA.value
                and f.severity != FindingSeverity.INFO.value
            )
        ],
        key=lambda f: severity_order.get(f.severity, 99),
    )
    for f in actionable[:3]:
        top_actions.append(f.recommendation)

    # If we have fewer than 3 actions and lots of missing data, surface that.
    if len(top_actions) < 3 and missing_count > 0:
        top_actions.append(
            "Connect your CRM and email platform to enable a complete "
            "data hygiene assessment."
        )

    # Determine overall severity.
    if health_tier == "poor":
        severity = FindingSeverity.HIGH.value
        title = "CRM data health: poor"
        desc = (
            f"CRM data health is poor -- {critical_count} critical and "
            f"{high_count} high-severity issues found across {total_count} checks. "
            f"Multiple data hygiene issues are compounding to limit marketing "
            f"effectiveness and create compliance risk."
        )
    elif health_tier == "needs_attention":
        severity = FindingSeverity.MEDIUM.value
        title = "CRM data health: needs attention"
        desc = (
            f"CRM data needs attention -- {high_count} high and "
            f"{medium_count} medium-severity issues found. Data quality "
            f"gaps are limiting segmentation, personalisation, and attribution."
        )
    else:
        severity = FindingSeverity.INFO.value
        title = "CRM data health: clean"
        desc = (
            "CRM data health is clean -- list hygiene, segmentation, and "
            "compliance are in good shape."
        )

    # If mostly missing data, note that.
    if total_count > 0 and missing_count / total_count > 0.70:
        severity = FindingSeverity.MEDIUM.value
        title = "CRM data health: insufficient data"
        desc = (
            f"Unable to fully assess CRM health -- {missing_count} of "
            f"{total_count} checks returned missing data. Connect your "
            f"CRM and email platform for a complete assessment."
        )

    # Assess overall list health tier from deliverability metrics.
    list_tier = assess_list_health_tier(
        bounce_rate=connected_data.get("bounce_rate"),
        spam_rate=connected_data.get("spam_complaint_rate"),
        unsub_rate=connected_data.get("unsubscribe_rate"),
    )

    evidence_items = [
        Evidence(
            evidence_type="text",
            value=health_tier,
            context="Overall CRM data health classification",
            source_label="Composite audit assessment",
        ),
        Evidence(
            evidence_type="text",
            value=list_tier,
            context="Email list health tier",
            source_label="Deliverability metrics assessment",
        ),
        Evidence(
            evidence_type="metric",
            value=str(total_count),
            context="Total checks performed",
            source_label="CRM hygiene audit",
        ),
        Evidence(
            evidence_type="metric",
            value=str(missing_count),
            context="Checks with missing data",
            source_label="CRM hygiene audit",
        ),
    ]

    rec_text = "Top data hygiene actions: "
    if top_actions:
        for i, action in enumerate(top_actions, 1):
            rec_text += f"({i}) {action} "
    else:
        rec_text += (
            "(1) Connect your CRM/email platform, "
            "(2) Run a deduplication process, "
            "(3) Audit consent records for compliance."
        )

    findings.append(create_finding(
        category=CATEGORY_CRM,
        severity=severity,
        title=title,
        description=desc,
        recommendation=rec_text.strip(),
        subcategory="overall_health_summary",
        source=FindingSource.INFERRED.value,
        effort=EffortLevel.ONGOING.value,
        estimated_impact=ImpactLevel.HIGH.value,
        evidence=evidence_items,
        tags=["crm", "data_quality", "summary"],
        metadata={
            "health_tier": health_tier,
            "list_health_tier": list_tier,
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "missing_count": missing_count,
            "total_checks": total_count,
            "top_actions": top_actions,
        },
    ))

    return findings
