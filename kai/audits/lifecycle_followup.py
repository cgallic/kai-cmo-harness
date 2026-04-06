"""Lifecycle and follow-up audit engine for the Kai Marketing OS.

Examines whether the business has systematic processes to capture, nurture,
and retain leads and customers at every stage of the relationship -- from
first inquiry to repeat purchase.  Most businesses lose leads and customers
not because of poor marketing but because of poor follow-up.

Usage::

    from kai.audits.lifecycle_followup import audit_lifecycle_followup, score_lifecycle_followup

    findings = audit_lifecycle_followup(profile)
    score    = score_lifecycle_followup(findings)

All findings carry ``category = "follow_up_gaps"`` or
``category = "speed_to_lead"`` and use the structured ``AuditFinding``
model from ``kai.models.audit``.
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

CATEGORY_FOLLOWUP = "follow_up_gaps"
CATEGORY_SPEED = "speed_to_lead"

_LOCAL_SERVICE_ARCHETYPES = {"local-service"}
_PROFESSIONAL_SERVICES_ARCHETYPES = {"professional-services"}
_MULTI_LOCATION_ARCHETYPES = {"multi-location"}
_ECOMMERCE_ARCHETYPES = {"ecommerce"}
_SERVICE_ARCHETYPES = _LOCAL_SERVICE_ARCHETYPES | _PROFESSIONAL_SERVICES_ARCHETYPES

# Archetypes where phone-based lead capture is critical.
_PHONE_BUSINESS_ARCHETYPES = (
    _LOCAL_SERVICE_ARCHETYPES | _MULTI_LOCATION_ARCHETYPES | _PROFESSIONAL_SERVICES_ARCHETYPES
)


# ============================================================================
# Public API
# ============================================================================


def audit_lifecycle_followup(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run all lifecycle and follow-up checks against *profile*.

    Parameters
    ----------
    profile:
        The canonical ``BusinessProfile`` to audit.
    connected_data:
        Optional dictionary of live data from integrations.
        Recognised keys:

        - ``has_welcome_sequence`` (bool)
        - ``welcome_sequence_length`` (int) -- number of emails in series
        - ``has_post_service_sequence`` (bool)
        - ``has_post_purchase_sequence`` (bool)
        - ``has_review_automation`` (bool)
        - ``has_referral_program`` (bool)
        - ``has_reactivation_campaign`` (bool)
        - ``has_quote_followup`` (bool)
        - ``avg_response_time_minutes`` (float) -- average first-response time
        - ``has_after_hours_system`` (bool)
        - ``has_ai_receptionist`` (bool)
        - ``email_subscriber_count`` (int)
        - ``email_list_growth_rate`` (float) -- monthly growth %

    Returns
    -------
    List[AuditFinding]
        Ordered list of findings across ``follow_up_gaps`` and
        ``speed_to_lead`` categories.
    """
    if connected_data is None:
        connected_data = {}

    archetype = _resolve_archetype(profile)

    findings: List[AuditFinding] = []

    # Run all 10 checks in order.
    findings.extend(_check_email_capture(profile, archetype, connected_data))
    findings.extend(_check_welcome_sequence(profile, archetype, connected_data))
    findings.extend(_check_post_service_sequence(profile, archetype, connected_data))
    findings.extend(_check_review_request_automation(profile, archetype, connected_data))
    findings.extend(_check_referral_system(profile, archetype, connected_data))
    findings.extend(_check_dormant_reactivation(profile, archetype, connected_data))
    findings.extend(_check_quote_followup(profile, archetype, connected_data))
    findings.extend(_check_speed_to_lead(profile, archetype, connected_data))
    findings.extend(_check_after_hours_capture(profile, archetype, connected_data))
    findings.extend(_check_followup_compliance(profile, archetype))

    return findings


def score_lifecycle_followup(findings: List[AuditFinding]) -> float:
    """Score the lifecycle/follow-up dimension on a 0-100 scale.

    Speed-to-lead and post-service follow-up checks are weighted 2x
    relative to other checks.  The scoring formula is::

        penalty = sum(severity_penalty * weight) for each finding
        score   = max(0, min(100, 100 - penalty))

    The *weight* for a finding is 2 if its ``subcategory`` is
    ``"speed_to_lead"`` or ``"post_service_sequence"``; otherwise 1.

    Severity penalties mirror ``compute_category_scorecard``::

        CRITICAL -> 25, HIGH -> 15, MEDIUM -> 8, LOW -> 3, INFO -> 0

    Parameters
    ----------
    findings:
        The list produced by ``audit_lifecycle_followup``.

    Returns
    -------
    float
        A score clamped to [0, 100], rounded to one decimal place.
    """
    severity_penalty = {
        FindingSeverity.CRITICAL.value: 25,
        FindingSeverity.HIGH.value: 15,
        FindingSeverity.MEDIUM.value: 8,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 0,
    }

    # Subcategories that receive 2x weight.
    double_weight_subs = {"speed_to_lead", "post_service_sequence"}

    total_penalty = 0.0
    for f in findings:
        base = severity_penalty.get(f.severity, 0)
        weight = 2 if getattr(f, "subcategory", None) in double_weight_subs else 1
        total_penalty += base * weight

    return round(max(0.0, min(100.0, 100.0 - total_penalty)), 1)


# ============================================================================
# Internal helpers
# ============================================================================


def _resolve_archetype(profile: BusinessProfile) -> str:
    """Return the normalised archetype string or ``"unknown"``."""
    archetype = None
    if hasattr(profile, "classification") and profile.classification:
        archetype = getattr(profile.classification, "archetype", None)
    return (archetype or "unknown").lower().strip()


def _has_email_channel(profile: BusinessProfile) -> Optional[Any]:
    """Return the email ``ChannelPresence`` if one exists, else ``None``."""
    for ch in profile.channels:
        platform = (ch.platform or "").lower().strip()
        if platform in ("email", "email_marketing", "newsletter", "mailchimp", "klaviyo", "loops", "convertkit", "activecampaign"):
            return ch
    return None


def _get_business_hours_limited(profile: BusinessProfile) -> bool:
    """Return ``True`` if the business appears to have limited operating hours.

    Heuristic: checks location hours for patterns indicating the business
    is not open 24/7 (e.g. ``"7am-6pm"``, ``"9:00-17:00"``).
    """
    if not hasattr(profile, "geography") or not profile.geography:
        return True  # Assume limited hours when unknown.

    for loc in profile.geography.locations:
        hours = getattr(loc, "hours", None)
        if not hours:
            continue
        # If any day shows "24" or "always" assume 24/7.
        for _day, time_str in hours.items():
            normalised = (time_str or "").lower().replace(" ", "")
            if "24" in normalised or "always" in normalised:
                return False
    # No evidence of 24/7 coverage.
    return True


def _profile_mentions(profile: BusinessProfile, *keywords: str) -> bool:
    """Return ``True`` if raw_notes or sales_process mentions any keyword."""
    search_fields = []
    if hasattr(profile, "raw_notes") and profile.raw_notes:
        search_fields.append(profile.raw_notes.lower())
    if hasattr(profile, "sales_cycle") and profile.sales_cycle:
        sp = getattr(profile.sales_cycle, "sales_process", None)
        if sp:
            search_fields.append(sp.lower())
    haystack = " ".join(search_fields)
    return any(kw.lower() in haystack for kw in keywords)


def _operator_hours(profile: BusinessProfile) -> Optional[float]:
    """Return operator hours per week or ``None``."""
    if hasattr(profile, "operator") and profile.operator:
        return getattr(profile.operator, "operator_hours_per_week", None)
    return None


def _years_in_business(profile: BusinessProfile) -> Optional[int]:
    """Return years in business or ``None``."""
    if hasattr(profile, "trust") and profile.trust:
        return getattr(profile.trust, "years_in_business", None)
    return None


def _has_emergency_services(profile: BusinessProfile) -> bool:
    """Check if the business offers emergency or after-hours services."""
    keywords = ("emergency", "24/7", "after-hours", "after hours", "urgent")
    # Check offers.
    for offer in profile.offers:
        name = (offer.name or "").lower()
        desc = (offer.description or "").lower()
        if any(kw in name or kw in desc for kw in keywords):
            return True
    # Check raw notes.
    if profile.raw_notes and any(kw in profile.raw_notes.lower() for kw in keywords):
        return True
    return False


# ============================================================================
# Check implementations
# ============================================================================


def _check_email_capture(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 1: Email capture mechanism."""
    findings: List[AuditFinding] = []
    email_ch = _has_email_channel(profile)

    if email_ch is None:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="email_capture",
                severity=FindingSeverity.HIGH.value,
                title="No email marketing channel active",
                description=(
                    "Email is the highest-ROI marketing channel (avg $42 per "
                    "$1 spent). No email marketing channel was detected in the "
                    "business profile. Without email capture, the business "
                    "has no owned audience and depends entirely on rented "
                    "platforms (social, paid) for every customer touchpoint."
                ),
                recommendation=(
                    "Implement email capture on every page: popup offer, "
                    "footer signup, exit intent, and resource download gates. "
                    "Choose an ESP (Mailchimp, Klaviyo, ConvertKit, or Loops) "
                    "and set up list growth tracking within the first week."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="No email marketing channel found in business profile channels.",
                        context="Email marketing averages $42 return per $1 spent (DMA).",
                        source_label="Business profile channel audit",
                    ),
                ],
                tags=["email", "lead_capture", "owned_audience"],
            )
        )
        return findings

    # Email channel exists but may be inactive.
    is_active = getattr(email_ch, "is_active", False)
    if not is_active:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="email_capture",
                severity=FindingSeverity.MEDIUM.value,
                title="Email channel exists but appears inactive",
                description=(
                    "An email marketing channel is configured but shows no "
                    "recent activity. An inactive email list decays at "
                    "approximately 25% per year -- subscribers who don't hear "
                    "from you will forget they signed up and mark future "
                    "emails as spam."
                ),
                recommendation=(
                    "Re-activate the email channel immediately. Send a "
                    "re-engagement campaign to the existing list, purge "
                    "unresponsive subscribers after 90 days of no opens, and "
                    "establish a consistent sending cadence (weekly minimum)."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.MEDIUM.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"Email channel '{email_ch.platform}' is_active=False.",
                        context="Inactive email lists decay ~25%/year.",
                        source_label="Business profile channel audit",
                    ),
                ],
                tags=["email", "reactivation"],
            )
        )
        return findings

    # Email channel active -- check for subscriber indicators.
    sub_count = connected_data.get("email_subscriber_count")
    if sub_count is not None:
        if sub_count < 100:
            findings.append(
                create_finding(
                    category=CATEGORY_FOLLOWUP,
                    subcategory="email_capture",
                    severity=FindingSeverity.MEDIUM.value,
                    title="Email list is very small",
                    description=(
                        f"Email subscriber count is {sub_count}. A list under "
                        "100 subscribers limits the effectiveness of email "
                        "marketing campaigns and provides insufficient data "
                        "for A/B testing or segmentation."
                    ),
                    recommendation=(
                        "Accelerate list growth: add email capture to every "
                        "page (popup, footer, exit intent), gate high-value "
                        "resources behind email signup, and run a lead magnet "
                        "campaign to build the list to 500+ within 90 days."
                    ),
                    source=FindingSource.CONNECTED.value,
                    effort=EffortLevel.MODERATE.value,
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    evidence=[
                        Evidence(
                            evidence_type="metric",
                            value=str(sub_count),
                            context="Subscriber count below 100 threshold.",
                            source_label="Email integration data",
                        ),
                    ],
                    tags=["email", "list_growth"],
                )
            )
        else:
            findings.append(
                create_finding(
                    category=CATEGORY_FOLLOWUP,
                    subcategory="email_capture",
                    severity=FindingSeverity.INFO.value,
                    title="Email channel active with subscriber base",
                    description=(
                        f"Email marketing channel is active with {sub_count} "
                        "subscribers. Verify capture mechanisms are present "
                        "on all high-traffic pages and that list growth rate "
                        "is positive month-over-month."
                    ),
                    recommendation=(
                        "Audit email capture points: ensure popup, footer, "
                        "and exit-intent forms are present on all key pages. "
                        "Target 3-5% month-over-month list growth."
                    ),
                    source=FindingSource.CONNECTED.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    estimated_impact=ImpactLevel.LOW.value,
                    evidence=[
                        Evidence(
                            evidence_type="metric",
                            value=str(sub_count),
                            context="Active email list detected.",
                            source_label="Email integration data",
                        ),
                    ],
                    tags=["email", "list_growth"],
                )
            )
    else:
        # Active channel but no subscriber data.
        findings.append(
            create_missing_data_finding(
                category=CATEGORY_FOLLOWUP,
                field_path="connected_data.email_subscriber_count",
                impact_description=(
                    "Email channel is active but subscriber count is unknown. "
                    "Cannot assess list health or growth trajectory."
                ),
                how_to_provide=(
                    "Connect the email marketing platform (Mailchimp, Klaviyo, "
                    "etc.) to provide subscriber count and growth rate data."
                ),
            )
        )

    return findings


def _check_welcome_sequence(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 2: Welcome email sequence."""
    findings: List[AuditFinding] = []

    has_welcome = connected_data.get("has_welcome_sequence")

    if has_welcome is True:
        seq_length = connected_data.get("welcome_sequence_length", 0)
        if seq_length and seq_length >= 3:
            findings.append(
                create_finding(
                    category=CATEGORY_FOLLOWUP,
                    subcategory="welcome_sequence",
                    severity=FindingSeverity.INFO.value,
                    title="Welcome sequence in place",
                    description=(
                        f"A {seq_length}-email welcome sequence is active. "
                        "New subscribers are being onboarded with an automated series."
                    ),
                    recommendation=(
                        "Review welcome sequence performance quarterly. "
                        "Benchmark: 50%+ open rate on email 1, 30%+ on "
                        "remaining emails. A/B test subject lines and CTAs."
                    ),
                    source=FindingSource.CONNECTED.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    estimated_impact=ImpactLevel.LOW.value,
                    tags=["email", "welcome_sequence", "automation"],
                )
            )
        elif seq_length and seq_length < 3:
            findings.append(
                create_finding(
                    category=CATEGORY_FOLLOWUP,
                    subcategory="welcome_sequence",
                    severity=FindingSeverity.LOW.value,
                    title="Welcome sequence is too short",
                    description=(
                        f"Welcome sequence has only {seq_length} email(s). "
                        "Best practice is 3-5 emails to properly onboard "
                        "new subscribers and build the relationship."
                    ),
                    recommendation=(
                        "Expand to a 3-5 email welcome sequence: "
                        "(1) Welcome + immediate value, "
                        "(2) Story + social proof, "
                        "(3) Core offer + CTA, "
                        "(4) FAQ/objection handling, "
                        "(5) Urgency/deadline."
                    ),
                    source=FindingSource.CONNECTED.value,
                    effort=EffortLevel.MODERATE.value,
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    tags=["email", "welcome_sequence", "automation"],
                )
            )
        else:
            findings.append(
                create_finding(
                    category=CATEGORY_FOLLOWUP,
                    subcategory="welcome_sequence",
                    severity=FindingSeverity.INFO.value,
                    title="Welcome sequence detected",
                    description=(
                        "A welcome sequence is active but the number of "
                        "emails in the series is unknown. Verify it "
                        "contains 3-5 emails covering value, proof, offer, "
                        "objections, and urgency."
                    ),
                    recommendation=(
                        "Audit the welcome sequence to ensure it has at "
                        "least 3 emails and follows the recommended "
                        "structure: value, story, offer, FAQ, urgency."
                    ),
                    source=FindingSource.CONNECTED.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    estimated_impact=ImpactLevel.LOW.value,
                    tags=["email", "welcome_sequence", "automation"],
                )
            )
        return findings

    if has_welcome is False:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="welcome_sequence",
                severity=FindingSeverity.MEDIUM.value,
                title="No welcome email sequence",
                description=(
                    "No welcome email sequence is in place. New subscribers "
                    "who receive a welcome series are 33% more likely to "
                    "engage long-term. Without one, first impressions are "
                    "left to chance and new leads go cold."
                ),
                recommendation=(
                    "Create a 3-5 email welcome sequence: "
                    "(1) Welcome + immediate value, "
                    "(2) Story + social proof, "
                    "(3) Core offer + CTA, "
                    "(4) FAQ/objection handling, "
                    "(5) Urgency/deadline."
                ),
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="No welcome sequence detected in email automation data.",
                        context="Subscribers with a welcome series are 33% more likely to engage long-term.",
                        source_label="Email automation audit",
                    ),
                ],
                tags=["email", "welcome_sequence", "automation"],
            )
        )
        return findings

    # No automation data available -- generate advisory.
    findings.append(
        create_finding(
            category=CATEGORY_FOLLOWUP,
            subcategory="welcome_sequence",
            severity=FindingSeverity.MEDIUM.value,
            title="Welcome sequence status unknown -- verify manually",
            description=(
                "No email automation data is available to confirm whether "
                "a welcome email sequence is in place. New subscribers who "
                "receive a welcome series are 33% more likely to engage "
                "long-term. This is a foundational automation that should "
                "be verified immediately."
            ),
            recommendation=(
                "Create a 3-5 email welcome sequence: "
                "(1) Welcome + immediate value, "
                "(2) Story + social proof, "
                "(3) Core offer + CTA, "
                "(4) FAQ/objection handling, "
                "(5) Urgency/deadline."
            ),
            source=FindingSource.INFERRED.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="missing_data",
                    value="connected_data.has_welcome_sequence",
                    context="Cannot verify welcome sequence without email automation data.",
                    source_label="Data completeness check",
                ),
            ],
            tags=["email", "welcome_sequence", "automation", "missing_data"],
        )
    )

    return findings


def _check_post_service_sequence(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 3: Post-purchase / post-service follow-up sequence."""
    findings: List[AuditFinding] = []

    is_ecommerce = archetype in _ECOMMERCE_ARCHETYPES

    # Connected data keys differ by business type.
    if is_ecommerce:
        has_sequence = connected_data.get("has_post_purchase_sequence")
    else:
        has_sequence = connected_data.get("has_post_service_sequence")

    # Also check profile notes for evidence of follow-up.
    mentions_followup = _profile_mentions(
        profile,
        "post-service", "post-purchase", "follow-up sequence",
        "follow up sequence", "after service", "after purchase",
        "thank you email", "review request",
    )

    if has_sequence is True:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="post_service_sequence",
                severity=FindingSeverity.INFO.value,
                title="Post-service follow-up sequence in place",
                description=(
                    "An automated post-service (or post-purchase) follow-up "
                    "sequence is active. This captures the highest-engagement "
                    "window after service completion for reviews, referrals, "
                    "and repeat bookings."
                ),
                recommendation=(
                    "Review the sequence quarterly. Ensure it includes: "
                    "(1) Thank you + review request within 24 hours, "
                    "(2) Feedback check at 7 days, "
                    "(3) Referral ask at 30 days."
                ),
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                tags=["follow_up", "post_service", "automation"],
            )
        )
        return findings

    if has_sequence is False or (has_sequence is None and not mentions_followup):
        if is_ecommerce:
            title = "No post-purchase follow-up sequence"
            description = (
                "No post-purchase sequence detected. Ecommerce businesses "
                "that automate post-purchase follow-up see 20-40% higher "
                "repeat purchase rates. The window immediately after "
                "purchase is the highest-engagement moment for building "
                "loyalty and generating reviews."
            )
            recommendation = (
                "Implement a post-purchase sequence: "
                "(1) Order confirmation (immediate), "
                "(2) Shipping notification, "
                "(3) Delivery follow-up + usage tips (1 day after delivery), "
                "(4) Review request (3-5 days after delivery), "
                "(5) Cross-sell recommendation (14 days after delivery)."
            )
        else:
            title = "No post-service follow-up detected"
            description = (
                "No post-service follow-up sequence detected. The window "
                "after service completion is the highest-engagement moment "
                "for review requests, referrals, and repeat bookings. "
                "Without automated follow-up, this moment is lost and "
                "the business relies on the customer to initiate contact."
            )
            recommendation = (
                "Send automated follow-up within 24 hours of service "
                "completion: (1) Thank you + review request, "
                "(2) 7 days later: feedback check, "
                "(3) 30 days later: referral ask + repeat booking offer."
            )

        source = (
            FindingSource.CONNECTED.value
            if has_sequence is False
            else FindingSource.INFERRED.value
        )

        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="post_service_sequence",
                severity=FindingSeverity.HIGH.value,
                title=title,
                description=description,
                recommendation=recommendation,
                source=source,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="No post-service/post-purchase follow-up sequence detected.",
                        context="The post-service window is the highest-engagement moment for reviews and repeat bookings.",
                        source_label="Lifecycle automation audit",
                    ),
                ],
                tags=["follow_up", "post_service", "automation"],
            )
        )
        return findings

    # Profile mentions follow-up but no connected data to confirm.
    if mentions_followup and has_sequence is None:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY_FOLLOWUP,
                field_path="connected_data.has_post_service_sequence",
                impact_description=(
                    "Profile mentions post-service follow-up but no automation "
                    "data is connected to verify the sequence is active and "
                    "properly configured."
                ),
                how_to_provide=(
                    "Connect the email/SMS automation platform to verify the "
                    "post-service follow-up sequence is live and firing correctly."
                ),
            )
        )

    return findings


def _check_review_request_automation(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 4: Automated review request system."""
    findings: List[AuditFinding] = []

    has_automation = connected_data.get("has_review_automation")

    if has_automation is True:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="review_request_automation",
                severity=FindingSeverity.INFO.value,
                title="Automated review request system in place",
                description=(
                    "An automated review request system is active. "
                    "Businesses with automated review requests generate "
                    "3-5x more reviews than those relying on manual asks."
                ),
                recommendation=(
                    "Optimize the review request flow: ensure the link goes "
                    "directly to the Google review page (skip the profile "
                    "page), send within 24 hours of service, and A/B test "
                    "SMS vs email delivery for higher response rates."
                ),
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                tags=["reviews", "automation"],
            )
        )
        return findings

    if has_automation is False:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="review_request_automation",
                severity=FindingSeverity.HIGH.value,
                title="No automated review request system",
                description=(
                    "No automated review request system detected. Manual "
                    "review requests are inconsistent, don't scale, and "
                    "produce far fewer reviews. Businesses with automated "
                    "review requests generate 3-5x more reviews than those "
                    "relying on manual asks."
                ),
                recommendation=(
                    "Automate review requests via text/email within 24 hours "
                    "of service completion. Include a direct link to your "
                    "Google review page. Tools: Podium, Birdeye, NiceJob, "
                    "or a simple CRM automation."
                ),
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="No automated review request system detected.",
                        context="Manual review requests don't scale. Automation generates 3-5x more reviews.",
                        source_label="Review automation audit",
                    ),
                ],
                tags=["reviews", "automation"],
            )
        )
        return findings

    # No connected data -- check profile for hints.
    mentions_review_system = _profile_mentions(
        profile, "review request", "review automation", "review system",
        "podium", "birdeye", "nicejob",
    )

    if not mentions_review_system:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="review_request_automation",
                severity=FindingSeverity.HIGH.value,
                title="No automated review request system",
                description=(
                    "No evidence of an automated review request system. "
                    "Manual review requests are inconsistent and don't scale. "
                    "Without automation, the business is leaving its online "
                    "reputation to chance."
                ),
                recommendation=(
                    "Automate review requests via text/email within 24 hours "
                    "of service completion. Include a direct link to your "
                    "Google review page. Tools: Podium, Birdeye, NiceJob, "
                    "or a simple CRM automation."
                ),
                source=FindingSource.INFERRED.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                evidence=[
                    Evidence(
                        evidence_type="missing_data",
                        value="connected_data.has_review_automation",
                        context="No review automation data available and no evidence in profile.",
                        source_label="Data completeness check",
                    ),
                ],
                tags=["reviews", "automation", "missing_data"],
            )
        )
    else:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY_FOLLOWUP,
                field_path="connected_data.has_review_automation",
                impact_description=(
                    "Profile mentions review request tools but no automation "
                    "data is connected to verify the system is active."
                ),
                how_to_provide=(
                    "Connect the review management platform or confirm "
                    "review request automation is active in the CRM."
                ),
            )
        )

    return findings


def _check_referral_system(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 5: Referral ask system."""
    findings: List[AuditFinding] = []

    has_referral = connected_data.get("has_referral_program")

    # Check profile for mentions.
    mentions_referral = _profile_mentions(
        profile, "referral", "refer a friend", "referral program",
        "referral bonus", "referral incentive",
    )

    if has_referral is True or mentions_referral:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="referral_system",
                severity=FindingSeverity.INFO.value,
                title="Referral program detected",
                description=(
                    "Evidence of a referral program or referral ask system "
                    "was found. Referrals are the highest-quality leads with "
                    "the lowest acquisition cost."
                ),
                recommendation=(
                    "Optimize the referral program: (1) Ask at the natural "
                    "moment (right after a positive outcome), (2) Make it "
                    "easy (shareable link or card), (3) Track referral "
                    "sources to identify top advocates, (4) Follow up on "
                    "every referral within 24 hours."
                ),
                source=(
                    FindingSource.CONNECTED.value
                    if has_referral is True
                    else FindingSource.STATIC.value
                ),
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                tags=["referrals", "lead_generation"],
            )
        )
        return findings

    # No referral program evidence.
    is_professional = archetype in _PROFESSIONAL_SERVICES_ARCHETYPES

    if is_professional:
        severity = FindingSeverity.HIGH.value
        description = (
            "No formalized referral system detected. Professional services "
            "firms get 30-60% of new clients from referrals -- this must "
            "be systematized, not left to luck. Without a referral program, "
            "the firm is missing its highest-converting lead source."
        )
    else:
        severity = FindingSeverity.MEDIUM.value
        description = (
            "No formalized referral system detected. Referrals are the "
            "highest-quality leads but most businesses rely on luck instead "
            "of a system. A structured referral program turns satisfied "
            "customers into a predictable lead source."
        )

    findings.append(
        create_finding(
            category=CATEGORY_FOLLOWUP,
            subcategory="referral_system",
            severity=severity,
            title="No formalized referral system",
            description=description,
            recommendation=(
                "Create a referral program: "
                "(1) Ask satisfied customers for referrals at the natural "
                "moment (post-service, post-positive-outcome), "
                "(2) Make it easy (shareable link or card), "
                "(3) Offer incentive (discount, gift card, service credit), "
                "(4) Track and follow up on every referral within 24 hours."
            ),
            source=FindingSource.INFERRED.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.HIGH.value,
            archetype_relevance=["professional-services"] if is_professional else [],
            evidence=[
                Evidence(
                    evidence_type="text",
                    value="No referral program evidence found in profile or connected data.",
                    context=(
                        "Professional services firms get 30-60% of new clients from referrals."
                        if is_professional
                        else "Referrals are the highest-quality, lowest-cost lead source."
                    ),
                    source_label="Lifecycle automation audit",
                ),
            ],
            tags=["referrals", "lead_generation"],
        )
    )

    return findings


def _check_dormant_reactivation(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 6: Dormant customer reactivation."""
    findings: List[AuditFinding] = []

    years = _years_in_business(profile)

    # Only relevant if the business has been operating long enough.
    if years is not None and years < 1:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="dormant_reactivation",
                severity=FindingSeverity.INFO.value,
                title="Business too new for dormant customer reactivation",
                description=(
                    f"Business has been operating for {years} year(s). "
                    "Dormant customer reactivation becomes relevant after "
                    "12+ months of operation when a meaningful base of "
                    "past customers has accumulated."
                ),
                recommendation=(
                    "Revisit this check after 12 months of operation. "
                    "In the meantime, focus on building a customer database "
                    "that tracks last-purchase/service dates for future "
                    "segmentation."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                tags=["retention", "reactivation"],
            )
        )
        return findings

    has_reactivation = connected_data.get("has_reactivation_campaign")

    if has_reactivation is True:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="dormant_reactivation",
                severity=FindingSeverity.INFO.value,
                title="Dormant customer reactivation program in place",
                description=(
                    "A dormant customer reactivation campaign or win-back "
                    "sequence is active. Past customers are being re-engaged."
                ),
                recommendation=(
                    "Review win-back campaign performance. Segment by "
                    "dormancy period (6 months, 12 months, 18+ months) "
                    "and tailor messaging and offers for each cohort."
                ),
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                tags=["retention", "reactivation"],
            )
        )
        return findings

    # No reactivation evidence.
    is_ecommerce = archetype in _ECOMMERCE_ARCHETYPES

    if is_ecommerce:
        title = "No win-back email sequence for lapsed customers"
        description = (
            "No win-back email sequence detected. Ecommerce businesses "
            "should re-engage lapsed customers (no purchase in 60-90 days) "
            "with 'we miss you' campaigns and exclusive offers. Acquiring "
            "a new customer costs 5-7x more than retaining an existing one."
        )
        recommendation = (
            "Segment customers by last purchase date. Create a win-back "
            "sequence for 60-90 day lapsed customers: "
            "(1) 'We miss you' email with personalized product recs, "
            "(2) Exclusive discount or free shipping offer, "
            "(3) Final nudge with expiring incentive."
        )
    else:
        title = "No dormant customer reactivation program"
        description = (
            "No dormant customer reactivation program detected. Past "
            "customers who haven't returned in 6+ months need a win-back "
            "campaign. It costs 5-7x more to acquire a new customer than "
            "to re-engage an existing one."
        )
        recommendation = (
            "Segment customers by last purchase/service date. Send "
            "targeted reactivation campaigns to 6-12 month dormant "
            "customers with a compelling reason to return: seasonal "
            "check-up, loyalty discount, new service offering, or "
            "a simple 'how can we help?' touchpoint."
        )

    source = (
        FindingSource.CONNECTED.value
        if has_reactivation is False
        else FindingSource.INFERRED.value
    )

    findings.append(
        create_finding(
            category=CATEGORY_FOLLOWUP,
            subcategory="dormant_reactivation",
            severity=FindingSeverity.MEDIUM.value,
            title=title,
            description=description,
            recommendation=recommendation,
            source=source,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.MEDIUM.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value="No dormant customer reactivation campaign detected.",
                    context="Acquiring a new customer costs 5-7x more than retaining an existing one.",
                    source_label="Lifecycle automation audit",
                ),
            ],
            tags=["retention", "reactivation"],
        )
    )

    return findings


def _check_quote_followup(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 7: Quote/proposal follow-up system."""
    findings: List[AuditFinding] = []

    # Only relevant for service-based businesses.
    if archetype not in _SERVICE_ARCHETYPES:
        return findings

    has_quote_followup = connected_data.get("has_quote_followup")
    mentions_quotes = _profile_mentions(
        profile, "quote", "estimate", "proposal", "bid",
    )
    mentions_followup = _profile_mentions(
        profile, "quote follow-up", "proposal follow-up", "estimate follow-up",
        "quote followup", "proposal followup",
    )

    if has_quote_followup is True or mentions_followup:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="quote_followup",
                severity=FindingSeverity.INFO.value,
                title="Quote follow-up process in place",
                description=(
                    "Evidence of a quote/proposal follow-up system detected. "
                    "Systematic follow-up on sent quotes prevents leads from "
                    "slipping through the cracks."
                ),
                recommendation=(
                    "Verify the follow-up cadence: Day 1 (quote sent + "
                    "confirmation), Day 3 (check-in), Day 7 (second "
                    "follow-up with FAQ), Day 14 (final nudge with "
                    "time-limited incentive). Track conversion rate from "
                    "quote to close."
                ),
                source=(
                    FindingSource.CONNECTED.value
                    if has_quote_followup is True
                    else FindingSource.STATIC.value
                ),
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                tags=["sales", "quote_followup"],
            )
        )
        return findings

    # Quotes are mentioned but no follow-up system.
    if mentions_quotes and not mentions_followup:
        findings.append(
            create_finding(
                category=CATEGORY_FOLLOWUP,
                subcategory="quote_followup",
                severity=FindingSeverity.HIGH.value,
                title="Quote follow-up not systematized",
                description=(
                    "The sales process involves quotes/estimates but no "
                    "systematic follow-up process was detected. Most "
                    "unconverted quotes are lost to inaction, not "
                    "competition. Without follow-up, sent quotes are "
                    "forgotten and potential revenue walks away."
                ),
                recommendation=(
                    "Implement automated quote follow-up: "
                    "Day 1: quote sent + confirmation email/text. "
                    "Day 3: check-in ('Any questions about the estimate?'). "
                    "Day 7: second follow-up with FAQ/objection handler. "
                    "Day 14: final nudge with time-limited incentive."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="Sales process mentions quotes/estimates but no follow-up system detected.",
                        context="Most unconverted quotes are lost to inaction, not competition.",
                        source_label="Sales process audit",
                    ),
                ],
                archetype_relevance=["local-service", "professional-services"],
                tags=["sales", "quote_followup"],
            )
        )
        return findings

    # No quote mentions and no connected data -- advisory for service businesses.
    if has_quote_followup is None and not mentions_quotes:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY_FOLLOWUP,
                field_path="sales_cycle.sales_process (quote follow-up)",
                impact_description=(
                    "Cannot assess quote/proposal follow-up for this "
                    "service business. The sales process description does "
                    "not mention quotes, estimates, or proposals."
                ),
                how_to_provide=(
                    "Describe the sales process in the business profile, "
                    "including whether quotes/estimates are provided and "
                    "how follow-up is handled after sending a quote."
                ),
            )
        )

    return findings


def _check_speed_to_lead(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 8: Speed to lead (response time)."""
    findings: List[AuditFinding] = []

    avg_response = connected_data.get("avg_response_time_minutes")
    is_phone_business = archetype in _PHONE_BUSINESS_ARCHETYPES
    hours = _operator_hours(profile)

    if avg_response is not None:
        # Benchmark: <5 min = excellent, 5-30 = good, 30-60 = poor, >60 = critical.
        if avg_response < 5:
            severity = FindingSeverity.INFO.value
            title = "Excellent speed to lead"
            description = (
                f"Average first-response time is {avg_response:.0f} minutes. "
                "Leads contacted within 5 minutes are 21x more likely to "
                "convert than those contacted after 30 minutes. This is "
                "excellent performance."
            )
            recommendation = (
                "Maintain this response speed. Monitor for degradation "
                "during high-volume periods or staff changes."
            )
        elif avg_response <= 30:
            severity = FindingSeverity.LOW.value
            title = "Good speed to lead -- room for improvement"
            description = (
                f"Average first-response time is {avg_response:.0f} minutes. "
                "This is acceptable but not optimal. Leads contacted within "
                "5 minutes are 21x more likely to convert than those "
                "contacted after 30 minutes."
            )
            recommendation = (
                "Reduce response time to under 5 minutes. Consider: "
                "automated instant replies (text/email), AI receptionist "
                "for phone calls, and CRM alerts that notify staff "
                "immediately on new lead submission."
            )
        elif avg_response <= 60:
            severity = FindingSeverity.MEDIUM.value
            title = "Slow speed to lead"
            description = (
                f"Average first-response time is {avg_response:.0f} minutes. "
                "Leads contacted within 5 minutes are 21x more likely to "
                "convert than those contacted after 30 minutes. A 30-60 "
                "minute response window means the business is losing "
                "winnable leads to competitors who respond faster."
            )
            recommendation = (
                "Implement instant automated responses for all lead "
                "channels: auto-reply email, auto-text for form "
                "submissions, and an AI receptionist for phone calls. "
                "Target under 5 minutes for first human response."
            )
        else:
            severity = FindingSeverity.HIGH.value
            title = "Critical speed-to-lead gap"
            description = (
                f"Average first-response time is {avg_response:.0f} minutes "
                f"({avg_response / 60:.1f} hours). Leads contacted within 5 "
                "minutes are 21x more likely to convert than those contacted "
                "after 30 minutes. At this response speed, the majority of "
                "leads are going cold before first contact."
            )
            recommendation = (
                "This is a revenue emergency. Implement immediately: "
                "(1) Automated instant text/email reply on every form submission, "
                "(2) AI receptionist for phone calls (KaiCalls at kaicalls.com), "
                "(3) CRM real-time alerts to the operator's phone. "
                "Target under 5 minutes for first human response."
            )

        findings.append(
            create_finding(
                category=CATEGORY_SPEED,
                subcategory="speed_to_lead",
                severity=severity,
                title=title,
                description=description,
                recommendation=recommendation,
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.HIGH.value,
                kaicalls_relevant=is_phone_business,
                evidence=[
                    Evidence(
                        evidence_type="metric",
                        value=f"{avg_response:.0f} minutes",
                        context="Benchmark: <5 min excellent, 5-30 good, 30-60 poor, >60 critical.",
                        source_label="Response time data",
                    ),
                ],
                tags=["speed_to_lead", "response_time"],
            )
        )
        return findings

    # No connected response time data -- assess from profile indicators.
    if hours is not None and hours < 20:
        has_automation = (
            connected_data.get("has_ai_receptionist", False)
            or connected_data.get("has_after_hours_system", False)
        )
        auto_mention = _profile_mentions(
            profile, "auto-reply", "auto reply", "chatbot", "ai receptionist",
            "kaicalls", "instant response",
        )

        if not has_automation and not auto_mention:
            findings.append(
                create_finding(
                    category=CATEGORY_SPEED,
                    subcategory="speed_to_lead",
                    severity=FindingSeverity.HIGH.value,
                    title="Speed to lead at risk -- limited operator availability",
                    description=(
                        f"Operator dedicates approximately {hours:.0f} hours/week "
                        "to the business and no automated response system was "
                        "detected. Leads contacted within 5 minutes are 21x "
                        "more likely to convert than those contacted after 30 "
                        "minutes. With limited availability, leads are likely "
                        "waiting hours or days for a response."
                    ),
                    recommendation=(
                        "Implement automated lead response to cover gaps: "
                        "(1) Auto-reply text/email on every form submission "
                        "(instant), (2) AI receptionist for phone calls "
                        "(KaiCalls at kaicalls.com), (3) CRM mobile alerts "
                        "for real-time lead notifications."
                    ),
                    source=FindingSource.INFERRED.value,
                    effort=EffortLevel.MODERATE.value,
                    estimated_impact=ImpactLevel.HIGH.value,
                    kaicalls_relevant=is_phone_business,
                    evidence=[
                        Evidence(
                            evidence_type="metric",
                            value=f"{hours:.0f} hours/week",
                            context="Limited operator availability with no automated response detected.",
                            source_label="Operator capacity assessment",
                        ),
                    ],
                    tags=["speed_to_lead", "operator_capacity"],
                )
            )
            return findings

    if hours is not None and hours >= 40:
        findings.append(
            create_finding(
                category=CATEGORY_SPEED,
                subcategory="speed_to_lead",
                severity=FindingSeverity.INFO.value,
                title="Full-time attention available for lead response",
                description=(
                    f"Operator dedicates approximately {hours:.0f} hours/week "
                    "to the business. Full-time availability reduces the "
                    "risk of delayed lead response during business hours."
                ),
                recommendation=(
                    "Verify actual response times. Full-time availability "
                    "does not guarantee fast response if the operator is "
                    "on jobs or in meetings. Consider automated instant "
                    "replies as a safety net."
                ),
                source=FindingSource.INFERRED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                kaicalls_relevant=is_phone_business,
                tags=["speed_to_lead", "operator_capacity"],
            )
        )
        return findings

    # No response time data and no operator hours -- missing data.
    findings.append(
        create_missing_data_finding(
            category=CATEGORY_SPEED,
            field_path="connected_data.avg_response_time_minutes",
            impact_description=(
                "Cannot assess speed to lead. No response time metrics "
                "available and operator availability is unknown. For "
                "local-service businesses, speed to lead is the single "
                "most impactful conversion factor."
            ),
            how_to_provide=(
                "Connect CRM or call tracking to measure average response "
                "time, or provide operator hours per week in the business "
                "profile."
            ),
            critical_gap=archetype in _LOCAL_SERVICE_ARCHETYPES,
        )
    )

    return findings


def _check_after_hours_capture(
    profile: BusinessProfile,
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 9: After-hours lead capture (KaiCalls)."""
    findings: List[AuditFinding] = []

    # Only critical for local-service and multi-location businesses.
    if archetype not in (_LOCAL_SERVICE_ARCHETYPES | _MULTI_LOCATION_ARCHETYPES):
        return findings

    has_after_hours = connected_data.get("has_after_hours_system", False)
    has_ai_receptionist = connected_data.get("has_ai_receptionist", False)

    # Check profile for existing coverage.
    mentions_coverage = _profile_mentions(
        profile, "after-hours", "after hours", "24/7", "ai receptionist",
        "kaicalls", "answering service", "virtual receptionist",
    )

    if has_after_hours or has_ai_receptionist or mentions_coverage:
        findings.append(
            create_finding(
                category=CATEGORY_SPEED,
                subcategory="after_hours_capture",
                severity=FindingSeverity.INFO.value,
                title="After-hours lead capture system detected",
                description=(
                    "Evidence of an after-hours lead capture or AI "
                    "receptionist system was found. This ensures leads "
                    "that arrive outside business hours are captured and "
                    "responded to promptly."
                ),
                recommendation=(
                    "Verify the after-hours system is capturing all "
                    "channels (phone, web form, chat). Review captured "
                    "leads weekly to ensure quality and follow-up speed."
                ),
                source=(
                    FindingSource.CONNECTED.value
                    if (has_after_hours or has_ai_receptionist)
                    else FindingSource.STATIC.value
                ),
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                kaicalls_relevant=True,
                tags=["after_hours", "lead_capture", "kaicalls"],
            )
        )
        return findings

    # No after-hours system detected -- assess business hours.
    limited_hours = _get_business_hours_limited(profile)
    has_emergency = _has_emergency_services(profile)

    if limited_hours:
        severity = FindingSeverity.CRITICAL.value
        description = (
            "No after-hours lead capture system detected. 40%+ of customer "
            "inquiries happen outside business hours. Without an AI "
            "receptionist or after-hours system, these leads are going to "
            "competitors who answer. Every missed call is a lost opportunity "
            "that cost marketing dollars to generate."
        )

        if has_emergency:
            description += (
                " This is especially critical because the business offers "
                "emergency services -- customers calling after hours for "
                "urgent needs will immediately call the next provider."
            )

        findings.append(
            create_finding(
                category=CATEGORY_SPEED,
                subcategory="after_hours_capture",
                severity=severity,
                title="No after-hours lead capture -- losing leads when closed",
                description=description,
                recommendation=(
                    "Implement KaiCalls AI receptionist (kaicalls.com) for "
                    "24/7 call answering, lead qualification, and appointment "
                    "scheduling -- even when you're on a job or asleep. "
                    "KaiCalls answers every call in seconds, qualifies the "
                    "lead, and books appointments directly on your calendar."
                ),
                source=FindingSource.INFERRED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.HIGH.value,
                kaicalls_relevant=True,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="Business has limited hours and no after-hours lead capture system.",
                        context="40%+ of customer inquiries happen outside business hours.",
                        source_label="After-hours coverage assessment",
                    ),
                ],
                archetype_relevance=["local-service", "multi-location"],
                tags=["after_hours", "lead_capture", "kaicalls", "critical"],
            )
        )
    else:
        # Business appears to have 24/7 hours but no system detected.
        findings.append(
            create_finding(
                category=CATEGORY_SPEED,
                subcategory="after_hours_capture",
                severity=FindingSeverity.MEDIUM.value,
                title="Verify after-hours lead capture coverage",
                description=(
                    "Business hours suggest 24/7 availability, but no "
                    "automated after-hours system was detected. Verify "
                    "that all inbound channels (phone, web, chat) are "
                    "covered at all times and that missed calls are "
                    "captured automatically."
                ),
                recommendation=(
                    "Even with extended hours, implement KaiCalls AI "
                    "receptionist (kaicalls.com) as a safety net for "
                    "overflow calls, break times, and busy periods "
                    "when staff cannot answer."
                ),
                source=FindingSource.INFERRED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.MEDIUM.value,
                kaicalls_relevant=True,
                tags=["after_hours", "lead_capture", "kaicalls"],
            )
        )

    return findings


def _check_followup_compliance(
    profile: BusinessProfile,
    archetype: str,
) -> List[AuditFinding]:
    """Check 10: Follow-up frequency and opt-out compliance advisory."""
    findings: List[AuditFinding] = []

    # Determine sales cycle context for cadence advice.
    sales_cycle_length = None
    if hasattr(profile, "sales_cycle") and profile.sales_cycle:
        sales_cycle_length = getattr(profile.sales_cycle, "sales_cycle_length", None)

    if sales_cycle_length:
        normalised = (sales_cycle_length or "").lower().strip()
        if any(term in normalised for term in ("same-day", "same day", "immediate", "instant")):
            cadence_advice = (
                "This is a same-day/immediate service business. Follow-up "
                "cadence should be rapid: instant confirmation, same-day "
                "review request, 7-day check-in."
            )
        elif any(term in normalised for term in ("week", "1-2", "1 to 2", "short")):
            cadence_advice = (
                "Sales cycle is 1-2 weeks. Follow-up cadence: confirm "
                "within 24 hours, check in at day 3 and day 7, then "
                "move to monthly nurture."
            )
        elif any(term in normalised for term in ("month", "3-6", "quarter", "long")):
            cadence_advice = (
                "Sales cycle is multi-month. Follow-up cadence: weekly "
                "touchpoints for first month, bi-weekly for months 2-3, "
                "then monthly nurture with value-add content."
            )
        else:
            cadence_advice = (
                "Follow-up cadence should match the buying cycle. Map the "
                "average time from first contact to close and design a "
                "sequence that maintains engagement through the full cycle."
            )
    else:
        cadence_advice = (
            "Follow-up cadence should match the buying cycle: same-day "
            "services need rapid follow-up, considered purchases need "
            "slower nurture. Map the average time from first contact to "
            "close and design touchpoints accordingly."
        )

    compliance_description = (
        f"{cadence_advice} "
        "All email sequences must include one-click unsubscribe "
        "(CAN-SPAM compliance). SMS requires explicit opt-in and easy "
        "opt-out (TCPA compliance). Failure to comply with CAN-SPAM can "
        "result in penalties up to $51,744 per email. TCPA violations "
        "can result in $500-$1,500 per message in statutory damages."
    )

    findings.append(
        create_finding(
            category=CATEGORY_FOLLOWUP,
            subcategory="followup_compliance",
            severity=FindingSeverity.INFO.value,
            title="Follow-up compliance advisory",
            description=compliance_description,
            recommendation=(
                "Audit all automated sequences for compliance: "
                "(1) Every email must have a visible one-click unsubscribe "
                "link (CAN-SPAM), "
                "(2) Every SMS must have opt-in consent on file and include "
                "STOP instructions (TCPA), "
                "(3) Honor unsubscribe/STOP requests within 10 business "
                "days (CAN-SPAM) or immediately (TCPA best practice), "
                "(4) Maintain opt-in records for at least 4 years."
            ),
            source=FindingSource.STATIC.value,
            effort=EffortLevel.QUICK_WIN.value,
            estimated_impact=ImpactLevel.LOW.value,
            tags=["compliance", "can_spam", "tcpa", "advisory"],
        )
    )

    return findings
