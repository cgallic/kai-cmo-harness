"""Website conversion audit engine for the Kai Marketing OS.

Examines whether a business's website is effectively turning visitors
into leads, customers, or desired actions.  Checks CTA clarity, trust
signal placement, mobile readiness, page speed indicators, form
optimization, and archetype-specific conversion elements.

For local-service businesses the engine emphasizes phone CTAs and
service area clarity.  For ecommerce it emphasizes product CTAs and
checkout flow.

Usage::

    from kai.audits.website_conversion import (
        audit_website_conversion,
        score_website_conversion,
    )
    from kai.models.business_profile import BusinessProfile

    findings = audit_website_conversion(profile, website_data=None)
    score = score_website_conversion(findings)
"""

from __future__ import annotations

import re
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

# ============================================================================
# Constants
# ============================================================================

CATEGORY = "website_conversion"

# CTA verbs considered action-oriented
_ACTION_VERBS = {
    "book", "call", "get", "schedule", "buy", "order", "start",
    "request", "reserve", "claim", "download", "sign", "join",
    "register", "subscribe", "try", "contact", "apply", "hire",
    "shop", "send", "submit", "learn", "explore", "discover",
}

# Archetypes that depend heavily on phone-based conversion
_PHONE_CRITICAL_ARCHETYPES = {"local-service", "multi-location"}

# Form-field benchmarks by purpose
_FORM_BENCHMARKS = {
    "lead_gen": {"ideal_min": 3, "ideal_max": 5},
    "email_capture": {"ideal_min": 1, "ideal_max": 2},
}

# Page speed thresholds in seconds
_SPEED_GOOD = 3.0
_SPEED_WARNING = 5.0


# ============================================================================
# Archetype weight configuration
# ============================================================================


def get_archetype_weights(archetype: Optional[str]) -> Dict[str, float]:
    """Return check-weighting multipliers for a given archetype.

    Weights amplify the penalty for checks that are especially important
    for a specific business type.  The default weight is 1.0 -- any
    value above 1.0 increases the importance of that check relative to
    the baseline.

    Parameters
    ----------
    archetype:
        Business archetype string (e.g., ``"local-service"``).  If
        ``None`` or unrecognized, a uniform-weight dict is returned.

    Returns
    -------
    Dict[str, float]
        Mapping of check name to weight multiplier.
    """
    base: Dict[str, float] = {
        "cta_clarity": 1.0,
        "cta_above_fold": 1.0,
        "phone_visibility": 1.0,
        "trust_signals": 1.0,
        "form_optimization": 1.0,
        "offer_clarity": 1.0,
        "headline_effectiveness": 1.0,
        "social_proof": 1.0,
        "mobile_responsiveness": 1.0,
        "page_speed": 1.0,
        "service_area": 1.0,
        "emergency_handling": 1.0,
    }

    overrides: Dict[str, Dict[str, float]] = {
        "local-service": {
            "phone_visibility": 2.0,
            "service_area": 1.5,
            "emergency_handling": 1.5,
        },
        "ecommerce": {
            "offer_clarity": 2.0,
            "cta_clarity": 1.5,  # product CTA
            "form_optimization": 1.5,  # checkout flow
        },
        "professional-services": {
            "trust_signals": 2.0,
            "social_proof": 1.5,  # case studies / credentials
            "headline_effectiveness": 1.5,  # credential display
        },
        "multi-location": {
            "service_area": 2.0,  # per-location pages
            "phone_visibility": 1.5,  # location selector
        },
    }

    if archetype and archetype in overrides:
        base.update(overrides[archetype])
    return base


# ============================================================================
# Individual check functions
# ============================================================================


def _check_cta_clarity(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 1: CTA Clarity.

    Verifies that the primary offer has a clear, action-oriented CTA
    defined.  If offers exist but none have a ``primary_cta``, a HIGH
    finding is raised.  If a CTA exists, it is checked for an
    action-verb prefix.
    """
    findings: List[AuditFinding] = []

    if not profile.offers:
        # Offer emptiness is handled by _check_offer_clarity; skip here
        # to avoid duplicate CRITICAL findings.
        return findings

    primary_offers = [o for o in profile.offers if o.is_primary]
    offers_with_cta = [o for o in profile.offers if o.primary_cta]

    if not offers_with_cta:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="cta_clarity",
            severity=FindingSeverity.HIGH.value,
            title="No clear primary call-to-action defined",
            description=(
                "The business has offers defined but none include a primary "
                "call-to-action.  Visitors landing on the website will not "
                "see a clear next step, which directly reduces conversion "
                "rates."
            ),
            recommendation=_cta_recommendation_for_archetype(archetype),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="No primary_cta found on any offer",
                source_label="BusinessProfile.offers",
            )],
            tags=["cta", "conversion"],
        ))
        return findings

    # Validate that primary CTA text starts with an action verb
    for offer in offers_with_cta:
        cta_text = offer.primary_cta or ""
        first_word = cta_text.strip().split()[0].lower() if cta_text.strip() else ""
        if first_word and first_word not in _ACTION_VERBS:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="cta_clarity",
                severity=FindingSeverity.MEDIUM.value,
                title=f"CTA \"{cta_text}\" does not start with an action verb",
                description=(
                    f"The CTA for offer \"{offer.name}\" is \"{cta_text}\".  "
                    "High-converting CTAs start with a verb that tells the "
                    "visitor exactly what to do (e.g., \"Book\", \"Call\", "
                    "\"Get\", \"Schedule\", \"Buy\")."
                ),
                recommendation=(
                    f"Rewrite the CTA to start with an action verb.  "
                    f"Example: \"Book {offer.name}\" or \"Get a Free Quote\"."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                evidence=[Evidence(
                    evidence_type="text",
                    value=f"Current CTA: \"{cta_text}\"",
                    source_label=f"Offer: {offer.name}",
                )],
                tags=["cta", "conversion", "copywriting"],
            ))

    return findings


def _check_cta_above_fold(
    website_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Check 2: CTA Above the Fold.

    If live website data is available and contains above-fold indicators,
    the check evaluates them.  Otherwise a MISSING_DATA finding is
    generated.
    """
    findings: List[AuditFinding] = []

    if website_data and "above_fold_cta" in website_data:
        if not website_data["above_fold_cta"]:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="cta_above_fold",
                severity=FindingSeverity.HIGH.value,
                title="Primary CTA is not visible above the fold",
                description=(
                    "Live website analysis shows no call-to-action visible "
                    "in the initial viewport.  Visitors who do not scroll "
                    "will never see a conversion opportunity."
                ),
                recommendation=(
                    "Ensure primary CTA is visible without scrolling on both "
                    "desktop and mobile.  Place a button or link in the hero "
                    "section that matches the primary offer."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="text",
                    value="No CTA element detected in above-fold viewport",
                    source_label="Live website analysis",
                )],
                tags=["cta", "conversion", "above_fold"],
            ))
        # If above_fold_cta is True, this check passes -- no finding needed.
    else:
        findings.append(create_missing_data_finding(
            category=CATEGORY,
            field_path="website_data.above_fold_cta",
            impact_description=(
                "Cannot determine whether the primary CTA is visible above "
                "the fold.  This requires live website analysis."
            ),
            how_to_provide=(
                "Connect a website analysis integration or provide manual "
                "above-fold screenshot data in website_data."
            ),
        ))

    return findings


def _check_phone_visibility(
    profile: BusinessProfile,
    archetype: Optional[str],
    website_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Check 3: Phone Number Visibility.

    For local-service and multi-location archetypes, phone visibility is
    critical.  For other archetypes, it is a lower-severity recommendation.
    All phone-related findings set ``kaicalls_relevant = True``.
    """
    findings: List[AuditFinding] = []
    is_phone_critical = archetype in _PHONE_CRITICAL_ARCHETYPES

    phone = profile.identity.phone

    if phone is None:
        severity = (
            FindingSeverity.CRITICAL.value if is_phone_critical
            else FindingSeverity.LOW.value
        )
        title = (
            "No phone number on file -- local service businesses must "
            "have a prominently displayed phone number"
            if is_phone_critical
            else "No phone number on file"
        )
        description = (
            "Phone-based leads are the highest-intent conversion channel "
            "for local service businesses.  Without a phone number, the "
            "business is invisible to callers and cannot capture phone leads."
            if is_phone_critical
            else (
                "A phone number provides an additional conversion path for "
                "visitors who prefer direct contact."
            )
        )
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="phone_visibility",
            severity=severity,
            title=title,
            description=description,
            recommendation=(
                "Add a business phone number to the profile and ensure it is "
                "displayed in the website header on every page.  Consider "
                "KaiCalls AI receptionist (kaicalls.com) to ensure every call "
                "is answered, even after hours."
            ),
            estimated_impact=(
                ImpactLevel.HIGH.value if is_phone_critical
                else ImpactLevel.LOW.value
            ),
            effort=EffortLevel.QUICK_WIN.value,
            kaicalls_relevant=True,
            evidence=[Evidence(
                evidence_type="missing_data",
                value="identity.phone is None",
                source_label="BusinessProfile.identity",
            )],
            tags=["phone", "conversion", "kaicalls"],
        ))
        return findings

    # Phone exists -- check for click-to-call evidence
    has_click_to_call = (
        website_data is not None
        and website_data.get("click_to_call", False)
    )

    if not has_click_to_call:
        severity = (
            FindingSeverity.HIGH.value if is_phone_critical
            else FindingSeverity.LOW.value
        )
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="phone_visibility",
            severity=severity,
            title=(
                "Phone number should be click-to-call and visible in header "
                "on every page"
            ),
            description=(
                "The business has a phone number on file but there is no "
                "evidence of click-to-call functionality on the website.  "
                "Mobile users should be able to tap the number to call "
                "instantly."
            ),
            recommendation=(
                "Implement click-to-call (tel: link) on the phone number in "
                "the site header.  Make it sticky on mobile.  Consider "
                "KaiCalls AI receptionist (kaicalls.com) to handle overflow "
                "and after-hours calls."
            ),
            estimated_impact=(
                ImpactLevel.HIGH.value if is_phone_critical
                else ImpactLevel.LOW.value
            ),
            effort=EffortLevel.QUICK_WIN.value,
            kaicalls_relevant=True,
            evidence=[Evidence(
                evidence_type="text",
                value=f"Phone on file: {phone}",
                context="No click-to-call evidence in website data",
                source_label="BusinessProfile.identity + website_data",
            )],
            tags=["phone", "conversion", "kaicalls", "mobile"],
        ))

    return findings


def _check_trust_signals(
    profile: BusinessProfile,
) -> List[AuditFinding]:
    """Check 4: Trust Signals Near CTAs.

    Verifies that the profile has testimonials, certifications, or
    awards to display near conversion points.  Also checks for case
    study availability.
    """
    findings: List[AuditFinding] = []
    trust = profile.trust

    has_testimonials = bool(trust.testimonials)
    has_certifications = bool(trust.certifications)
    has_awards = bool(trust.awards)
    has_case_studies = bool(trust.case_studies)

    if not has_testimonials and not has_certifications and not has_awards:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="trust_signals",
            severity=FindingSeverity.HIGH.value,
            title="No trust signals available to display near conversion points",
            description=(
                "The profile contains no testimonials, certifications, or "
                "awards.  Trust signals placed near CTAs can increase "
                "conversion rates by 15-30% by reducing purchase anxiety."
            ),
            recommendation=(
                "Collect at least 3 customer testimonials and display them "
                "adjacent to the primary CTA.  Add any certifications, "
                "licenses, or awards.  A trust badge row (BBB, industry "
                "certifications, review stars) near the CTA is a proven "
                "conversion booster."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="testimonials=0, certifications=0, awards=0",
                source_label="BusinessProfile.trust",
            )],
            tags=["trust", "conversion", "social_proof"],
        ))
    elif not has_case_studies:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="trust_signals",
            severity=FindingSeverity.MEDIUM.value,
            title=(
                "Case studies/proof of results should support the "
                "conversion path"
            ),
            description=(
                "Trust signals (testimonials, certifications, or awards) "
                "exist, but there are no case studies.  Case studies "
                "provide the strongest form of social proof because they "
                "show real outcomes, not just endorsements."
            ),
            recommendation=(
                "Create at least one detailed case study showing the "
                "problem, solution, and quantified results.  Display it "
                "within the conversion path so visitors see proof of "
                "outcomes before taking action."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="case_studies=0",
                context=(
                    f"Other trust signals present: "
                    f"testimonials={len(trust.testimonials)}, "
                    f"certifications={len(trust.certifications)}, "
                    f"awards={len(trust.awards)}"
                ),
                source_label="BusinessProfile.trust",
            )],
            tags=["trust", "conversion", "case_study"],
        ))

    return findings


def _check_form_optimization(
    website_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Check 5: Form Optimization.

    If website data includes form field counts, compares against
    benchmarks.  Otherwise generates an advisory finding about best
    practices.
    """
    findings: List[AuditFinding] = []

    if website_data and "form_field_count" in website_data:
        field_count = website_data["form_field_count"]
        form_type = website_data.get("form_type", "lead_gen")
        benchmarks = _FORM_BENCHMARKS.get(form_type, _FORM_BENCHMARKS["lead_gen"])

        if field_count > benchmarks["ideal_max"]:
            excess = field_count - benchmarks["ideal_max"]
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="form_optimization",
                severity=FindingSeverity.HIGH.value,
                title=(
                    f"Form has {field_count} fields -- "
                    f"{excess} more than the ideal maximum of "
                    f"{benchmarks['ideal_max']}"
                ),
                description=(
                    f"The primary form has {field_count} fields.  Each "
                    f"additional field beyond {benchmarks['ideal_max']} "
                    f"reduces form completion rates by approximately 10%.  "
                    f"For {form_type.replace('_', ' ')} forms, the ideal "
                    f"range is {benchmarks['ideal_min']}-"
                    f"{benchmarks['ideal_max']} fields."
                ),
                recommendation=(
                    "Minimize form fields to name, phone/email, and one "
                    "qualifying question.  Move non-essential fields to a "
                    "follow-up step after the initial conversion."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="metric",
                    value=f"{field_count} fields",
                    context=f"Benchmark: {benchmarks['ideal_min']}-{benchmarks['ideal_max']} fields",
                    source_label="Live website analysis",
                )],
                tags=["form", "conversion", "ux"],
            ))
        elif field_count < benchmarks["ideal_min"]:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="form_optimization",
                severity=FindingSeverity.LOW.value,
                title=(
                    f"Form has only {field_count} field(s) -- may not "
                    f"capture enough qualifying information"
                ),
                description=(
                    f"The form has {field_count} field(s), which is below "
                    f"the ideal minimum of {benchmarks['ideal_min']}.  "
                    f"While fewer fields increase completion rates, too "
                    f"few may result in low-quality leads that cannot be "
                    f"effectively followed up."
                ),
                recommendation=(
                    "Consider adding a qualifying question (e.g., service "
                    "needed, budget range, timeline) to improve lead quality "
                    "without significantly impacting conversion rates."
                ),
                estimated_impact=ImpactLevel.LOW.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="metric",
                    value=f"{field_count} fields",
                    context=f"Benchmark: {benchmarks['ideal_min']}-{benchmarks['ideal_max']} fields",
                    source_label="Live website analysis",
                )],
                tags=["form", "conversion", "lead_quality"],
            ))
        # If within range, this check passes -- no finding needed.
    else:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="form_optimization",
            severity=FindingSeverity.INFO.value,
            title="Form field count not available -- review form length manually",
            description=(
                "Live form data is not available.  Form length is one of "
                "the biggest controllable factors in conversion rate.  "
                "Best practice is 3-5 fields for lead generation forms "
                "and 1-2 fields for email capture."
            ),
            recommendation=(
                "Minimize form fields to name, phone/email, and one "
                "qualifying question.  Each additional field beyond 5 "
                "reduces completion rates by roughly 10%."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.INFERRED.value,
            evidence=[Evidence(
                evidence_type="text",
                value="Form field count not in website_data",
                source_label="Advisory",
            )],
            tags=["form", "conversion", "advisory"],
        ))

    return findings


def _check_offer_clarity(
    profile: BusinessProfile,
) -> List[AuditFinding]:
    """Check 6: Offer Clarity.

    Verifies that offers are defined and that the primary offer has a
    description and price range.
    """
    findings: List[AuditFinding] = []

    if not profile.offers:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="offer_clarity",
            severity=FindingSeverity.CRITICAL.value,
            title=(
                "No offers defined -- the website must clearly communicate "
                "what the business offers"
            ),
            description=(
                "The business profile has zero offers.  A website without "
                "clearly communicated offers cannot convert visitors because "
                "they do not know what the business does or what they can "
                "buy."
            ),
            recommendation=(
                "Define at least one primary offer with a name, description, "
                "price range (or 'free consultation'), and a primary CTA.  "
                "The offer should be visible on the homepage within the "
                "first viewport."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="offers=[] (empty)",
                source_label="BusinessProfile.offers",
            )],
            tags=["offer", "conversion", "critical"],
        ))
        return findings

    # Check primary offer for description and price range
    primary_offers = [o for o in profile.offers if o.is_primary]
    target_offers = primary_offers if primary_offers else profile.offers[:1]

    for offer in target_offers:
        if not offer.description:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="offer_clarity",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Offer \"{offer.name}\" has no description",
                description=(
                    f"The offer \"{offer.name}\" lacks a description.  "
                    "Visitors need to understand what the offer includes, "
                    "who it is for, and what outcome it delivers before "
                    "they will convert."
                ),
                recommendation=(
                    f"Write a 1-2 sentence description for \"{offer.name}\" "
                    "that explains the deliverable, target audience, and "
                    "primary benefit."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                evidence=[Evidence(
                    evidence_type="text",
                    value=f"Offer \"{offer.name}\" description is None",
                    source_label="BusinessProfile.offers",
                )],
                tags=["offer", "conversion", "copywriting"],
            ))

        if not offer.price_range:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="offer_clarity",
                severity=FindingSeverity.MEDIUM.value,
                title=(
                    "Primary offer should include pricing guidance (exact "
                    "or range) to qualify leads"
                ),
                description=(
                    f"The offer \"{offer.name}\" has no price range defined.  "
                    "Displaying pricing guidance (even a range like "
                    "\"Starting at $X\") filters unqualified traffic and "
                    "sets expectations, reducing wasted sales time."
                ),
                recommendation=(
                    f"Add a price_range to \"{offer.name}\" -- even a "
                    "general range like \"$200-500\" or \"Starting at "
                    "$99/mo\".  If pricing is custom, use \"Free "
                    "consultation\" as the CTA and mention that pricing "
                    "is discussed during the call."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                evidence=[Evidence(
                    evidence_type="text",
                    value=f"Offer \"{offer.name}\" price_range is None",
                    source_label="BusinessProfile.offers",
                )],
                tags=["offer", "conversion", "pricing"],
            ))

    return findings


def _check_headline_effectiveness() -> List[AuditFinding]:
    """Check 7: Headline Effectiveness (advisory).

    Cannot assess from profile alone.  Generates an advisory INFO
    finding with best practices.
    """
    return [create_finding(
        category=CATEGORY,
        subcategory="headline_effectiveness",
        severity=FindingSeverity.INFO.value,
        title="Review homepage headline effectiveness",
        description=(
            "Headline effectiveness cannot be assessed from the business "
            "profile alone -- it requires reviewing the actual website copy.  "
            "The homepage headline is the single most-read element on the "
            "page and has outsized impact on bounce rate and engagement."
        ),
        recommendation=(
            "Homepage headline should state what you do, who you do it "
            "for, and the primary benefit -- in under 10 words.  Avoid "
            "generic phrases like \"Welcome to [Business Name]\" or "
            "\"We are the leading provider of...\""
        ),
        estimated_impact=ImpactLevel.MEDIUM.value,
        effort=EffortLevel.QUICK_WIN.value,
        source=FindingSource.INFERRED.value,
        evidence=[Evidence(
            evidence_type="text",
            value="Headline assessment requires live website review",
            source_label="Advisory",
        )],
        tags=["headline", "conversion", "copywriting", "advisory"],
    )]


def _check_social_proof(
    profile: BusinessProfile,
) -> List[AuditFinding]:
    """Check 8: Social Proof Placement.

    Looks at channel presence for review data (GBP, Yelp, etc.) and
    recommends prominent display of review counts and ratings.
    """
    findings: List[AuditFinding] = []

    # Look for review platforms in channels
    review_platforms = {"gbp", "google_business_profile", "yelp", "google", "trustpilot"}
    review_channels = [
        ch for ch in profile.channels
        if ch.platform.lower().replace(" ", "_") in review_platforms
    ]

    has_review_data = False
    for ch in review_channels:
        if ch.follower_count is not None or ch.notes:
            has_review_data = True
            # Suggest displaying this data
            display_value = (
                f"{ch.follower_count} reviews"
                if ch.follower_count is not None
                else ch.notes or "Review data available"
            )
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="social_proof",
                severity=FindingSeverity.INFO.value,
                title=f"Display {ch.platform} review data prominently on website",
                description=(
                    f"{ch.platform} shows {display_value}.  Displaying "
                    "review counts and star ratings on the website "
                    "increases trust and conversion rates."
                ),
                recommendation=(
                    f"Add a review badge or widget showing the {ch.platform} "
                    "rating and review count near the primary CTA and in the "
                    "site footer.  Use schema markup (AggregateRating) to "
                    "enable rich snippets in search results."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                evidence=[Evidence(
                    evidence_type="metric",
                    value=display_value,
                    source_label=ch.platform,
                )],
                tags=["social_proof", "conversion", "reviews"],
            ))

    if not review_channels or not has_review_data:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="social_proof",
            severity=FindingSeverity.MEDIUM.value,
            title="No review data available to display as social proof",
            description=(
                "No review platform data (Google Business Profile, Yelp, "
                "Trustpilot, etc.) is available in the business profile.  "
                "Review data is one of the strongest conversion drivers "
                "and should be displayed prominently."
            ),
            recommendation=(
                "Connect Google Business Profile and/or Yelp to the "
                "business profile.  Aim for 20+ reviews with a 4.5+ star "
                "average.  Display review count and rating on the website "
                "homepage and landing pages."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="No review platform data in profile.channels",
                source_label="BusinessProfile.channels",
            )],
            tags=["social_proof", "conversion", "reviews"],
        ))

    return findings


def _check_mobile_responsiveness(
    archetype: Optional[str],
    website_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Check 9: Mobile Responsiveness.

    If website data includes mobile indicators, evaluates them.
    Otherwise generates an advisory finding.  For local-service
    archetype, emphasizes the criticality of mobile-first design.
    """
    findings: List[AuditFinding] = []
    is_local = archetype in _PHONE_CRITICAL_ARCHETYPES

    if website_data and "mobile_friendly" in website_data:
        if not website_data["mobile_friendly"]:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="mobile_responsiveness",
                severity=FindingSeverity.CRITICAL.value if is_local else FindingSeverity.HIGH.value,
                title="Website is not mobile-friendly",
                description=(
                    "Live analysis indicates the website is not mobile-"
                    "responsive.  Over 60% of web traffic is on mobile "
                    "devices.  For local service businesses, 70%+ of "
                    "searches happen on mobile."
                ),
                recommendation=(
                    "Implement responsive design immediately.  Ensure "
                    "click-to-call buttons, forms, and CTAs are thumb-"
                    "friendly on mobile.  Test with Google's Mobile-"
                    "Friendly Test tool."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.SIGNIFICANT.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="text",
                    value="Website flagged as not mobile-friendly",
                    source_label="Live website analysis",
                )],
                tags=["mobile", "conversion", "ux"],
            ))
        # Mobile-friendly = True: passes, no finding.
    else:
        # No data -- advisory finding
        severity = (
            FindingSeverity.MEDIUM.value if is_local
            else FindingSeverity.INFO.value
        )
        description = (
            "Mobile responsiveness cannot be assessed without live "
            "website data.  "
        )
        if is_local:
            description += (
                "70%+ of local service searches are on mobile -- "
                "click-to-call and mobile-first design are non-negotiable."
            )
        else:
            description += (
                "Over 60% of web traffic is on mobile devices.  A "
                "mobile-first design is essential for conversion."
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="mobile_responsiveness",
            severity=severity,
            title="Mobile responsiveness data not available -- review manually",
            description=description,
            recommendation=(
                "Test the website with Google's Mobile-Friendly Test "
                "(search.google.com/test/mobile-friendly).  Ensure CTAs, "
                "phone numbers, and forms are fully usable on mobile "
                "without pinch-zooming."
            ),
            estimated_impact=ImpactLevel.HIGH.value if is_local else ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.INFERRED.value,
            evidence=[Evidence(
                evidence_type="text",
                value="No mobile responsiveness data in website_data",
                source_label="Advisory",
            )],
            tags=["mobile", "conversion", "advisory"],
        ))

    return findings


def _check_page_speed(
    website_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Check 10: Page Speed Indicators.

    If website data includes speed metrics, scores against benchmarks.
    Otherwise generates a MISSING_DATA finding.
    """
    findings: List[AuditFinding] = []

    if website_data and "page_load_seconds" in website_data:
        load_time = float(website_data["page_load_seconds"])

        if load_time > _SPEED_WARNING:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="page_speed",
                severity=FindingSeverity.CRITICAL.value,
                title=f"Page load time is {load_time:.1f}s -- critically slow",
                description=(
                    f"The website takes {load_time:.1f} seconds to load.  "
                    "Pages that take over 5 seconds lose approximately 90% "
                    "of potential visitors.  Every additional second of load "
                    "time reduces conversions by roughly 7%."
                ),
                recommendation=(
                    "Target page load time under 3 seconds.  Compress "
                    "images, enable browser caching, minimize JavaScript, "
                    "and consider a CDN.  Use Google PageSpeed Insights "
                    "to identify specific bottlenecks."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="metric",
                    value=f"{load_time:.1f}s",
                    context="Benchmark: under 3s = good, 3-5s = warning, 5s+ = critical",
                    source_label="Live website analysis",
                )],
                tags=["speed", "conversion", "technical"],
            ))
        elif load_time > _SPEED_GOOD:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="page_speed",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Page load time is {load_time:.1f}s -- room for improvement",
                description=(
                    f"The website takes {load_time:.1f} seconds to load.  "
                    "While not critically slow, every second above 3 seconds "
                    "reduces conversions.  Pages loading in under 3 seconds "
                    "have significantly higher engagement."
                ),
                recommendation=(
                    "Target page load time under 3 seconds.  Use Google "
                    "PageSpeed Insights to measure and identify "
                    "optimization opportunities."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="metric",
                    value=f"{load_time:.1f}s",
                    context="Benchmark: under 3s = good, 3-5s = warning, 5s+ = critical",
                    source_label="Live website analysis",
                )],
                tags=["speed", "conversion", "technical"],
            ))
        # Under 3s: passes, no finding.
    else:
        findings.append(create_missing_data_finding(
            category=CATEGORY,
            field_path="website_data.page_load_seconds",
            impact_description=(
                "Cannot assess page speed without live website performance "
                "metrics.  Page speed directly impacts both conversion rate "
                "and search rankings."
            ),
            how_to_provide=(
                "Run a Google PageSpeed Insights test or connect a "
                "performance monitoring integration.  Provide the result "
                "as website_data['page_load_seconds']."
            ),
        ))

    return findings


def _check_service_area(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 11: Service Area Clarity (local-service and multi-location).

    Only applies to local-service and multi-location archetypes.  Checks
    whether service areas are defined in the profile.
    """
    findings: List[AuditFinding] = []

    if archetype not in _PHONE_CRITICAL_ARCHETYPES:
        return findings

    service_areas = profile.geography.service_areas

    if not service_areas:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="service_area",
            severity=FindingSeverity.HIGH.value,
            title=(
                "Service areas not defined -- visitors need to know if "
                "you serve their area"
            ),
            description=(
                "The business is classified as a local-service or "
                "multi-location business but has no service areas defined.  "
                "Visitors searching for local services need to immediately "
                "confirm that the business serves their area."
            ),
            recommendation=(
                "Create dedicated service area pages for each primary "
                "market.  Each page should include the area name in the "
                "title, a map, service descriptions, and a local CTA.  "
                "Also display service areas on the homepage."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="geography.service_areas is empty",
                source_label="BusinessProfile.geography",
            )],
            tags=["service_area", "conversion", "local_seo"],
        ))
    else:
        # Service areas exist -- advisory to ensure they appear on the site
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="service_area",
            severity=FindingSeverity.INFO.value,
            title=(
                f"{len(service_areas)} service area(s) defined -- ensure "
                f"they are visible on the website"
            ),
            description=(
                f"The profile defines {len(service_areas)} service area(s): "
                f"{', '.join(service_areas[:5])}"
                f"{'...' if len(service_areas) > 5 else ''}.  "
                "Ensure these areas are clearly displayed on the website "
                "and each major market has a dedicated landing page."
            ),
            recommendation=(
                "Create dedicated service area pages for each primary "
                "market.  Include the area name in the page title, embed "
                "a map, and use a local CTA (e.g., \"Call us in "
                f"{service_areas[0]}\" or \"Get a quote for "
                f"{service_areas[0]}\")."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="text",
                value=f"Service areas: {', '.join(service_areas[:10])}",
                source_label="BusinessProfile.geography",
            )],
            tags=["service_area", "conversion", "local_seo", "advisory"],
        ))

    return findings


def _check_emergency_handling(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 12: Emergency/Urgency Handling (local-service).

    Only applies to local-service archetype.  If any offers indicate
    emergency services, checks for after-hours availability evidence.
    """
    findings: List[AuditFinding] = []

    if archetype != "local-service":
        return findings

    # Detect emergency-related offers by name/description keywords
    emergency_keywords = {
        "emergency", "urgent", "24/7", "24-hour", "same-day",
        "after-hours", "after hours", "overnight",
    }

    emergency_offers = []
    for offer in profile.offers:
        offer_text = (
            (offer.name or "").lower() + " " +
            (offer.description or "").lower() + " " +
            (offer.category or "").lower()
        )
        if any(kw in offer_text for kw in emergency_keywords):
            emergency_offers.append(offer)

    if not emergency_offers:
        return findings

    # Emergency offers detected -- check for after-hours availability
    has_after_hours = False

    # Check locations for 24/7 or extended hours
    for loc in profile.geography.locations:
        if loc.hours:
            hours_text = " ".join(str(v) for v in loc.hours.values()).lower()
            if "24" in hours_text or "always" in hours_text:
                has_after_hours = True
                break

    # Check channel notes for after-hours indicators
    for ch in profile.channels:
        if ch.notes and any(
            kw in ch.notes.lower() for kw in {"24/7", "after-hours", "always open"}
        ):
            has_after_hours = True
            break

    if not has_after_hours:
        emergency_names = ", ".join(o.name for o in emergency_offers[:3])
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="emergency_handling",
            severity=FindingSeverity.HIGH.value,
            title=(
                "Emergency service offered but no clear after-hours "
                "availability"
            ),
            description=(
                f"The business offers emergency/urgent services "
                f"({emergency_names}) but there is no evidence of "
                "after-hours availability in the profile.  Customers "
                "needing emergency service will call outside business "
                "hours -- if no one answers, the lead is lost to a "
                "competitor."
            ),
            recommendation=(
                "KaiCalls AI receptionist (kaicalls.com) can handle "
                "after-hours emergency calls, qualify the urgency, "
                "capture caller details, and dispatch to the on-call "
                "technician.  Ensure the website clearly states 24/7 "
                "availability and displays the phone number prominently "
                "with a click-to-call link."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            kaicalls_relevant=True,
            evidence=[Evidence(
                evidence_type="text",
                value=f"Emergency offers: {emergency_names}",
                context="No after-hours availability evidence in profile",
                source_label="BusinessProfile.offers + locations",
            )],
            tags=["emergency", "conversion", "phone", "kaicalls", "after_hours"],
        ))

    return findings


# ============================================================================
# Helpers
# ============================================================================


def _cta_recommendation_for_archetype(archetype: Optional[str]) -> str:
    """Return an archetype-specific CTA recommendation string."""
    archetype_ctas: Dict[str, str] = {
        "local-service": (
            "For local service businesses, the ideal primary CTA is "
            "\"Call Now\" or \"Get a Free Quote\" with a click-to-call "
            "phone number.  Consider adding KaiCalls AI receptionist "
            "(kaicalls.com) to ensure every call is answered."
        ),
        "ecommerce": (
            "For ecommerce, the primary CTA should be product-specific: "
            "\"Shop Now\", \"Add to Cart\", or \"Buy [Product Name]\".  "
            "Place it above the fold on every product page."
        ),
        "professional-services": (
            "For professional services, the primary CTA should invite a "
            "conversation: \"Schedule a Consultation\", \"Book a Call\", "
            "or \"Get Started\".  Pair it with credentialing trust signals."
        ),
        "multi-location": (
            "For multi-location businesses, the primary CTA should route "
            "by location: \"Find Your Nearest Location\" or \"Call Your "
            "Local Office\".  Each location page needs its own CTA."
        ),
        "saas": (
            "For SaaS products, the primary CTA should be \"Start Free "
            "Trial\" or \"Get Started Free\".  Minimize friction between "
            "CTA click and product access."
        ),
        "creator": (
            "For creators, the primary CTA depends on the monetization "
            "model: \"Subscribe\", \"Join the Community\", or \"Download "
            "the Free [Resource]\".  Make it the single most prominent "
            "element on the page."
        ),
    }
    return archetype_ctas.get(archetype or "", (
        "Define a clear primary CTA for each offer.  The CTA should "
        "start with an action verb (Book, Call, Get, Schedule, Buy) and "
        "tell the visitor exactly what happens when they click."
    ))


# ============================================================================
# Scoring
# ============================================================================

# Severity penalty map for scoring
_SEVERITY_PENALTY: Dict[str, float] = {
    FindingSeverity.CRITICAL.value: 25.0,
    FindingSeverity.HIGH.value: 15.0,
    FindingSeverity.MEDIUM.value: 8.0,
    FindingSeverity.LOW.value: 3.0,
}


def score_website_conversion(findings: List[AuditFinding]) -> float:
    """Compute a 0-100 website conversion score from findings.

    Starts at 100 and deducts points based on finding severity:

    - CRITICAL: -25
    - HIGH: -15
    - MEDIUM: -8
    - LOW: -3

    INFO and MISSING_DATA source findings are excluded from scoring
    (they do not penalize the score, but they indicate an incomplete
    assessment).

    The score is clamped to the range [0, 100].

    Parameters
    ----------
    findings:
        List of ``AuditFinding`` objects produced by
        ``audit_website_conversion()``.

    Returns
    -------
    float
        Website conversion health score between 0 and 100.
    """
    score = 100.0

    for finding in findings:
        # Skip MISSING_DATA source findings and INFO severity findings
        if finding.source == FindingSource.MISSING_DATA.value:
            continue
        if finding.severity == FindingSeverity.INFO.value:
            continue

        penalty = _SEVERITY_PENALTY.get(finding.severity, 0.0)
        score -= penalty

    return max(0.0, min(100.0, round(score, 1)))


# ============================================================================
# Main audit entry point
# ============================================================================


def audit_website_conversion(
    profile: BusinessProfile,
    website_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run the full website conversion audit against a business profile.

    Executes all 12 conversion checks and returns structured findings.
    If data is not available to assess a particular check, a
    MISSING_DATA finding is generated instead of silently skipping.

    Parameters
    ----------
    profile:
        The ``BusinessProfile`` to audit.  At minimum, ``id`` and
        ``identity`` must be populated.
    website_data:
        Optional dictionary of live website analysis data.  Keys may
        include:

        - ``above_fold_cta`` (bool): Whether a CTA is visible above the fold.
        - ``click_to_call`` (bool): Whether the phone number is click-to-call.
        - ``form_field_count`` (int): Number of fields in the primary form.
        - ``form_type`` (str): ``"lead_gen"`` or ``"email_capture"``.
        - ``mobile_friendly`` (bool): Whether the site is mobile-responsive.
        - ``page_load_seconds`` (float): Page load time in seconds.

    Returns
    -------
    List[AuditFinding]
        A list of structured findings covering all 12 conversion checks.
        Every check produces at least one finding (real or MISSING_DATA).
    """
    archetype = (
        profile.classification.archetype
        if profile.classification
        else None
    )

    findings: List[AuditFinding] = []

    # Check 1: CTA Clarity
    findings.extend(_check_cta_clarity(profile, archetype))

    # Check 2: CTA Above the Fold
    findings.extend(_check_cta_above_fold(website_data))

    # Check 3: Phone Number Visibility
    findings.extend(_check_phone_visibility(profile, archetype, website_data))

    # Check 4: Trust Signals Near CTAs
    findings.extend(_check_trust_signals(profile))

    # Check 5: Form Optimization
    findings.extend(_check_form_optimization(website_data))

    # Check 6: Offer Clarity
    findings.extend(_check_offer_clarity(profile))

    # Check 7: Headline Effectiveness
    findings.extend(_check_headline_effectiveness())

    # Check 8: Social Proof Placement
    findings.extend(_check_social_proof(profile))

    # Check 9: Mobile Responsiveness
    findings.extend(_check_mobile_responsiveness(archetype, website_data))

    # Check 10: Page Speed Indicators
    findings.extend(_check_page_speed(website_data))

    # Check 11: Service Area Clarity
    findings.extend(_check_service_area(profile, archetype))

    # Check 12: Emergency/Urgency Handling
    findings.extend(_check_emergency_handling(profile, archetype))

    # Tag all findings with archetype relevance if known
    if archetype:
        for finding in findings:
            if archetype not in finding.archetype_relevance:
                finding.archetype_relevance.append(archetype)

    # Ensure every finding has the correct category
    for finding in findings:
        if finding.category != CATEGORY:
            finding.category = CATEGORY

    return findings
