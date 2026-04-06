"""Review and reputation audit engine for the Kai Marketing OS.

Examines the health of a business's online review profile across platforms.
Goes beyond simple count and rating to evaluate velocity (how often new
reviews arrive), recency, response behaviour, platform distribution,
negative-review patterns, and whether a systematic review-generation process
is in place.

Usage::

    from kai.audits.review_reputation import audit_review_reputation, score_review_reputation

    findings = audit_review_reputation(profile)
    score    = score_review_reputation(findings)

All findings carry ``category = "reviews_reputation"`` and use the
structured ``AuditFinding`` model from ``kai.models.audit``.
"""

from __future__ import annotations

import re
import statistics
from datetime import datetime, timezone
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
from kai.models.business_profile import BusinessProfile, ChannelPresence

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORY = "reviews_reputation"

# Archetypes for which Google review benchmarks differ.
_LOCAL_SERVICE_ARCHETYPES = {"local-service"}
_PROFESSIONAL_SERVICES_ARCHETYPES = {"professional-services"}
_MULTI_LOCATION_ARCHETYPES = {"multi-location"}
_ECOMMERCE_ARCHETYPES = {"ecommerce"}

# Industry-specific review platforms keyed by vertical keyword.
_INDUSTRY_PLATFORMS: Dict[str, List[str]] = {
    "legal": ["avvo", "martindale", "justia"],
    "law": ["avvo", "martindale", "justia"],
    "attorney": ["avvo", "martindale", "justia"],
    "lawyer": ["avvo", "martindale", "justia"],
    "medical": ["healthgrades", "vitals", "zocdoc", "webmd"],
    "doctor": ["healthgrades", "vitals", "zocdoc", "webmd"],
    "healthcare": ["healthgrades", "vitals", "zocdoc", "webmd"],
    "dental": ["healthgrades", "zocdoc"],
    "dentist": ["healthgrades", "zocdoc"],
    "restaurant": ["tripadvisor", "opentable"],
    "food": ["tripadvisor", "opentable", "doordash"],
    "hotel": ["tripadvisor", "booking.com"],
    "hospitality": ["tripadvisor", "booking.com"],
    "real_estate": ["zillow", "realtor.com"],
    "realtor": ["zillow", "realtor.com"],
    "home_services": ["angi", "homeadvisor", "thumbtack"],
    "automotive": ["carfax", "dealerrater"],
    "auto": ["carfax", "dealerrater"],
}

# Platform name normalisations used when matching channel entries.
_PLATFORM_ALIASES: Dict[str, str] = {
    "google": "gbp",
    "google_business": "gbp",
    "google_business_profile": "gbp",
    "gmb": "gbp",
    "google_maps": "gbp",
    "facebook": "facebook",
    "fb": "facebook",
    "yelp": "yelp",
}


# ============================================================================
# Public API
# ============================================================================


def audit_review_reputation(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run all review-and-reputation checks against *profile*.

    Parameters
    ----------
    profile:
        The canonical ``BusinessProfile`` to audit.
    connected_data:
        Optional dictionary of live review data from integrations.
        Recognised keys:

        - ``google_review_count`` (int)
        - ``google_review_rating`` (float)
        - ``yelp_review_count`` (int)
        - ``yelp_rating`` (float)
        - ``review_dates`` (List[str]) -- ISO-format date strings
        - ``reviews_per_month`` (float)
        - ``latest_review_date`` (str) -- ISO date
        - ``response_rate`` (float) -- 0.0 to 1.0
        - ``review_texts`` (List[str]) -- raw review bodies
        - ``sentiment_themes`` (List[str]) -- pre-computed negative themes
        - ``has_review_automation`` (bool)
        - ``locations`` (List[Dict]) -- per-location review data for
          multi-location businesses.  Each dict may contain
          ``name``, ``review_count``, ``rating``.

    Returns
    -------
    List[AuditFinding]
        Ordered list of findings with ``category = "reviews_reputation"``.
    """
    if connected_data is None:
        connected_data = {}

    archetype = _resolve_archetype(profile)
    metrics = parse_review_metrics(profile, connected_data)

    findings: List[AuditFinding] = []

    # Run all 10 checks in order.
    findings.extend(_check_google_review_count(archetype, metrics, profile))
    findings.extend(_check_google_review_rating(metrics))
    findings.extend(_check_review_velocity(metrics, connected_data))
    findings.extend(_check_review_recency(metrics, connected_data))
    findings.extend(_check_response_rate(connected_data))
    findings.extend(_check_response_quality())
    findings.extend(_check_platform_distribution(archetype, metrics, profile))
    findings.extend(_check_negative_review_patterns(connected_data))
    findings.extend(_check_review_generation_system(profile, connected_data))
    findings.extend(
        _check_multi_location_distribution(archetype, connected_data)
    )

    return findings


def score_review_reputation(findings: List[AuditFinding]) -> float:
    """Score the review/reputation dimension on a 0-100 scale.

    Review count and rating checks are weighted 2x relative to other checks.
    The scoring formula is::

        penalty = sum(severity_penalty * weight) for each finding
        score   = max(0, min(100, 100 - penalty))

    The *weight* for a finding is 2 if its ``subcategory`` is
    ``"google_review_count"`` or ``"google_review_rating"``; otherwise 1.

    Severity penalties mirror ``compute_category_scorecard``::

        CRITICAL -> 25, HIGH -> 15, MEDIUM -> 8, LOW -> 3, INFO -> 0

    Parameters
    ----------
    findings:
        The list produced by ``audit_review_reputation``.

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
    double_weight_subs = {"google_review_count", "google_review_rating"}

    total_penalty = 0.0
    for f in findings:
        base = severity_penalty.get(f.severity, 0)
        weight = 2 if getattr(f, "subcategory", None) in double_weight_subs else 1
        total_penalty += base * weight

    return round(max(0.0, min(100.0, 100.0 - total_penalty)), 1)


def parse_review_metrics(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Extract review-related data from *profile* channels and *connected_data*.

    Parses human-readable channel ``notes`` fields (e.g. ``"87 reviews,
    4.7 rating"``) and merges with any data supplied via *connected_data*.

    Returns
    -------
    dict
        Keys: ``google_review_count``, ``google_review_rating``,
        ``yelp_review_count``, ``yelp_rating``, ``facebook_review_count``,
        ``facebook_rating``, ``total_reviews``, ``platforms_with_reviews``,
        ``reviews_per_month``, ``latest_review_date``.
        Any value may be ``None`` when data is unavailable.
    """
    if connected_data is None:
        connected_data = {}

    out: Dict[str, Any] = {
        "google_review_count": None,
        "google_review_rating": None,
        "yelp_review_count": None,
        "yelp_rating": None,
        "facebook_review_count": None,
        "facebook_rating": None,
        "total_reviews": None,
        "platforms_with_reviews": [],
        "reviews_per_month": None,
        "latest_review_date": None,
    }

    # ----- Parse channel notes from the profile -----
    for ch in profile.channels:
        norm = _normalise_platform(ch.platform)
        notes = ch.notes or ""

        count = _extract_review_count(notes)
        rating = _extract_rating(notes)

        if norm == "gbp":
            if count is not None:
                out["google_review_count"] = count
            if rating is not None:
                out["google_review_rating"] = rating
        elif norm == "yelp":
            if count is not None:
                out["yelp_review_count"] = count
            if rating is not None:
                out["yelp_rating"] = rating
        elif norm == "facebook":
            if count is not None:
                out["facebook_review_count"] = count
            if rating is not None:
                out["facebook_rating"] = rating

    # ----- Override / supplement from connected_data -----
    for key in (
        "google_review_count",
        "google_review_rating",
        "yelp_review_count",
        "yelp_rating",
        "reviews_per_month",
        "latest_review_date",
    ):
        if key in connected_data and connected_data[key] is not None:
            out[key] = connected_data[key]

    # ----- Derive aggregates -----
    platforms: List[str] = []
    total = 0
    for platform_key, count_key in [
        ("gbp", "google_review_count"),
        ("yelp", "yelp_review_count"),
        ("facebook", "facebook_review_count"),
    ]:
        c = out.get(count_key)
        if c is not None and c > 0:
            platforms.append(platform_key)
            total += c

    out["platforms_with_reviews"] = platforms
    out["total_reviews"] = total if platforms else None

    # Derive velocity from review_dates if provided and not already set.
    if out["reviews_per_month"] is None and "review_dates" in connected_data:
        out["reviews_per_month"] = _compute_velocity(connected_data["review_dates"])

    # Derive latest_review_date from review_dates if not already set.
    if out["latest_review_date"] is None and "review_dates" in connected_data:
        dates = connected_data["review_dates"]
        if dates:
            out["latest_review_date"] = max(dates)

    return out


# ============================================================================
# Check implementations
# ============================================================================


def _check_google_review_count(
    archetype: str,
    metrics: Dict[str, Any],
    profile: BusinessProfile,
) -> List[AuditFinding]:
    """Check 1: Google review count with archetype-specific benchmarks."""
    findings: List[AuditFinding] = []
    count = metrics.get("google_review_count")

    # Ecommerce: Google reviews are N/A (product reviews checked separately).
    if archetype in _ECOMMERCE_ARCHETYPES:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="google_review_count",
                severity=FindingSeverity.INFO.value,
                title="Google review count N/A for ecommerce",
                description=(
                    "Google Business Profile reviews are not the primary review "
                    "surface for ecommerce businesses. Product reviews on the "
                    "store and marketplace platforms are assessed separately."
                ),
                recommendation=(
                    "Focus review efforts on product-level reviews on your store "
                    "and marketplace listings (Amazon, Shopify, etc.)."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                archetype_relevance=["ecommerce"],
                tags=["reviews", "ecommerce"],
            )
        )
        return findings

    if count is None:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="channels.gbp.review_count",
                impact_description=(
                    "Google review count not available -- cannot assess review "
                    "volume health. Connect Google Business Profile to evaluate."
                ),
                how_to_provide=(
                    "Connect your Google Business Profile via the GBP integration, "
                    "or add review count in the GBP channel notes "
                    '(e.g. "87 reviews, 4.7 rating").'
                ),
                critical_gap=True,
            )
        )
        return findings

    # Multi-location: per-location assessment happens in Check 10.
    # Here we assess the aggregate or primary-location count.
    if archetype in _MULTI_LOCATION_ARCHETYPES:
        # Use local-service thresholds for the aggregate / primary location.
        severity, title, description = _assess_local_service_review_count(count)
    elif archetype in _PROFESSIONAL_SERVICES_ARCHETYPES:
        severity, title, description = _assess_professional_services_review_count(count)
    else:
        # Default to local-service thresholds.
        severity, title, description = _assess_local_service_review_count(count)

    recommendation = (
        "Target a minimum of 50 Google reviews with a 4.5+ average rating. "
        "Implement an automated review request system that sends a text or "
        "email within 24 hours of service completion with a direct Google "
        "review link."
    )

    source = FindingSource.STATIC.value
    if count == metrics.get("google_review_count"):
        # Came from profile notes or connected data -- determine which.
        source = (
            FindingSource.CONNECTED.value
            if "google_review_count" in (
                {k for k, v in ({} if not metrics else metrics).items() if v is not None}
            )
            else FindingSource.STATIC.value
        )

    findings.append(
        create_finding(
            category=CATEGORY,
            subcategory="google_review_count",
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            source=source,
            effort=EffortLevel.ONGOING.value,
            estimated_impact=ImpactLevel.HIGH.value,
            archetype_relevance=[archetype],
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=str(count),
                    context=f"Google review count: {count}",
                    source_label="Google Business Profile",
                ),
            ],
            tags=["reviews", "google", "review_count"],
            metadata={"google_review_count": count, "archetype": archetype},
        )
    )
    return findings


def _check_google_review_rating(
    metrics: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 2: Google review rating across all severity ranges."""
    findings: List[AuditFinding] = []
    rating = metrics.get("google_review_rating")

    if rating is None:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="channels.gbp.review_rating",
                impact_description=(
                    "Google review rating not available -- cannot assess "
                    "review quality. Connect Google Business Profile to evaluate."
                ),
                how_to_provide=(
                    "Connect your Google Business Profile via the GBP integration, "
                    "or add the rating in the GBP channel notes "
                    '(e.g. "87 reviews, 4.7 rating").'
                ),
                critical_gap=True,
            )
        )
        return findings

    if rating < 3.5:
        severity = FindingSeverity.CRITICAL.value
        title = f"Google rating {rating} is below 3.5 -- actively repelling customers"
        description = (
            f"Google rating is {rating}, which is below 3.5. This actively "
            "repels customers and suppresses local ranking. Prospective "
            "customers will skip your listing entirely at this rating level."
        )
        recommendation = (
            "Prioritize service quality improvements and address the root "
            "causes of negative reviews before requesting new ones. Respond "
            "to every negative review professionally. Consider a service "
            "recovery programme for dissatisfied customers."
        )
    elif rating < 4.0:
        severity = FindingSeverity.HIGH.value
        title = f"Google rating {rating} is below 4.0 -- significant trust barrier"
        description = (
            f"Google rating is {rating}, which is below 4.0. Customers "
            "comparison-shopping will choose competitors with higher ratings. "
            "Address negative reviews and improve service delivery to "
            "raise this above 4.0."
        )
        recommendation = (
            "Review the last 20 negative reviews for recurring themes. "
            "Address operational issues first, then implement a review "
            "request system targeting your most satisfied customers."
        )
    elif rating < 4.5:
        severity = FindingSeverity.MEDIUM.value
        title = f"Google rating is {rating} -- target 4.5+ for competitive advantage"
        description = (
            f"Google rating is {rating}. This is acceptable but not "
            "competitive. Target 4.5+ through consistent review generation "
            "from your most satisfied customers."
        )
        recommendation = (
            "Implement a systematic review request process that targets "
            "customers who have expressed satisfaction. Send the request "
            "within 24 hours of service completion when the positive "
            "experience is fresh."
        )
    elif rating < 4.9:
        severity = FindingSeverity.LOW.value
        title = f"Strong Google rating of {rating} -- maintain momentum"
        description = (
            f"Google rating of {rating} is strong and builds trust with "
            "prospective customers. Maintain this through continued "
            "review requests and quality service delivery."
        )
        recommendation = (
            "Continue your current review generation approach. Respond "
            "to every review to show engagement. Watch for any emerging "
            "negative themes."
        )
    else:
        severity = FindingSeverity.INFO.value
        title = f"Excellent Google rating of {rating} -- verify authenticity perception"
        description = (
            f"Google rating of {rating} is excellent. Consider whether a "
            "near-perfect rating looks authentic to prospective customers. "
            "Ratings of 4.9-5.0 with few reviews can appear artificially "
            "inflated."
        )
        recommendation = (
            "A near-perfect rating is a strong asset. Ensure review volume "
            "is high enough that the rating looks natural. If you have fewer "
            "than 30 reviews, focus on increasing volume."
        )

    findings.append(
        create_finding(
            category=CATEGORY,
            subcategory="google_review_rating",
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            source=FindingSource.STATIC.value,
            effort=EffortLevel.ONGOING.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=str(rating),
                    context=f"Google review rating: {rating}",
                    source_label="Google Business Profile",
                ),
            ],
            tags=["reviews", "google", "review_rating"],
            metadata={"google_review_rating": rating},
        )
    )
    return findings


def _check_review_velocity(
    metrics: Dict[str, Any],
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 3: Review velocity (reviews per month)."""
    findings: List[AuditFinding] = []
    velocity = metrics.get("reviews_per_month")

    if velocity is None:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="connected_data.reviews_per_month",
                impact_description=(
                    "Review velocity data not available -- cannot assess "
                    "how frequently new reviews arrive. Connect review "
                    "integration to measure velocity."
                ),
                how_to_provide=(
                    "Connect your Google Business Profile API or provide "
                    "review dates via the connected_data parameter so "
                    "velocity can be calculated."
                ),
                critical_gap=False,
            )
        )
        return findings

    if velocity < 1:
        severity = FindingSeverity.HIGH.value
        title = "Review velocity is stagnant -- fewer than 1 review per month"
        description = (
            f"Review velocity is approximately {velocity:.1f} reviews/month. "
            "A business without regular new reviews signals stagnation "
            "to both customers and search algorithms. You need a systematic "
            "review request process."
        )
    elif velocity < 4:
        severity = FindingSeverity.MEDIUM.value
        title = f"Review velocity is {velocity:.1f}/month -- adequate but could be stronger"
        description = (
            f"Review velocity of {velocity:.1f} reviews per month is adequate "
            "but leaves room for improvement. Competitors with higher velocity "
            "will outpace your review profile over time."
        )
    elif velocity <= 10:
        severity = FindingSeverity.LOW.value
        title = f"Good review velocity of {velocity:.1f} reviews per month"
        description = (
            f"Review velocity of {velocity:.1f} reviews per month is solid. "
            "Maintain your current approach to review generation."
        )
    else:
        severity = FindingSeverity.INFO.value
        title = f"Excellent review velocity of {velocity:.1f} reviews per month"
        description = (
            f"Review velocity of {velocity:.1f} reviews per month is excellent. "
            "This rate will quickly build a dominant review profile."
        )

    recommendation = (
        "Implement an automated review request system -- send a text or "
        "email within 24 hours of service completion with a direct Google "
        "review link. Make it one-click easy for the customer."
    )

    findings.append(
        create_finding(
            category=CATEGORY,
            subcategory="review_velocity",
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.HIGH.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=f"{velocity:.1f}",
                    context=f"Reviews per month: {velocity:.1f}",
                    source_label="Review integration",
                ),
            ],
            tags=["reviews", "velocity"],
            metadata={"reviews_per_month": velocity},
        )
    )
    return findings


def _check_review_recency(
    metrics: Dict[str, Any],
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 4: How recent is the latest review?"""
    findings: List[AuditFinding] = []
    latest_str = metrics.get("latest_review_date")

    if latest_str is None:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="connected_data.latest_review_date",
                impact_description=(
                    "Latest review date not available -- cannot assess review "
                    "recency. Connect review integration to evaluate."
                ),
                how_to_provide=(
                    "Connect your Google Business Profile API or provide "
                    "the latest_review_date in connected_data (ISO format)."
                ),
                critical_gap=False,
            )
        )
        return findings

    days_since = _days_since_date(latest_str)
    if days_since is None:
        # Could not parse the date -- treat as missing.
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="connected_data.latest_review_date",
                impact_description=(
                    f"Could not parse latest review date '{latest_str}'. "
                    "Review recency could not be assessed."
                ),
                how_to_provide="Provide the date in ISO-8601 format (YYYY-MM-DD).",
                critical_gap=False,
            )
        )
        return findings

    if days_since > 90:
        severity = FindingSeverity.HIGH.value
        title = "Most recent review is over 3 months old -- stale profile"
        description = (
            f"The most recent review is {days_since} days old. Stale reviews "
            "signal a dormant business to both customers and Google's local "
            "ranking algorithm. Recent reviews are a key freshness signal."
        )
    elif days_since > 30:
        severity = FindingSeverity.MEDIUM.value
        title = f"No reviews in the last {days_since} days"
        description = (
            f"The last review was {days_since} days ago. Maintain consistent "
            "review generation to keep your profile fresh and active."
        )
    else:
        severity = FindingSeverity.INFO.value
        title = "Recent review activity detected"
        description = (
            f"Most recent review was {days_since} day{'s' if days_since != 1 else ''} ago. "
            "Review profile appears active and current."
        )

    recommendation = (
        "Maintain a steady cadence of review requests. Aim for at least "
        "one new review per week to keep your profile looking active."
    )

    findings.append(
        create_finding(
            category=CATEGORY,
            subcategory="review_recency",
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.MEDIUM.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=f"{days_since} days",
                    context=f"Days since last review: {days_since}",
                    source_label="Review integration",
                ),
            ],
            tags=["reviews", "recency"],
            metadata={
                "latest_review_date": latest_str,
                "days_since_last_review": days_since,
            },
        )
    )
    return findings


def _check_response_rate(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 5: Owner response rate to reviews."""
    findings: List[AuditFinding] = []
    response_rate = connected_data.get("response_rate")

    if response_rate is None:
        # No connected data -- issue advisory at MEDIUM.
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="response_rate",
                severity=FindingSeverity.MEDIUM.value,
                title="Review response rate unknown -- ensure you respond to every review",
                description=(
                    "Review response rate data is not available. Responding "
                    "to reviews -- both positive and negative -- improves "
                    "local ranking signals and demonstrates that you value "
                    "customer feedback."
                ),
                recommendation=(
                    "Respond to every review within 48 hours. Thank positive "
                    "reviewers by name and reference the specific service. "
                    "Acknowledge concerns in negative reviews and take the "
                    "conversation offline."
                ),
                source=FindingSource.INFERRED.value,
                effort=EffortLevel.ONGOING.value,
                estimated_impact=ImpactLevel.MEDIUM.value,
                tags=["reviews", "response_rate"],
            )
        )
        return findings

    # Normalise to percentage.
    pct = response_rate * 100 if response_rate <= 1.0 else response_rate

    if pct == 0:
        severity = FindingSeverity.HIGH.value
        title = "No review responses detected -- 0% response rate"
        description = (
            "No review responses were detected. Responding to reviews "
            "improves local ranking, shows prospective customers you care, "
            "and gives you a chance to address concerns publicly."
        )
    elif pct < 50:
        severity = FindingSeverity.MEDIUM.value
        title = f"Only {pct:.0f}% of reviews have a response"
        description = (
            f"Response rate is {pct:.0f}%. Only responding to some reviews "
            "sends an inconsistent signal. Aim to respond to every review, "
            "positive and negative."
        )
    elif pct < 90:
        severity = FindingSeverity.LOW.value
        title = f"Good response habit at {pct:.0f}% -- close the gap"
        description = (
            f"Response rate of {pct:.0f}% is a good habit. Close the gap "
            "on remaining unresponded reviews to reach 100%."
        )
    else:
        severity = FindingSeverity.INFO.value
        title = f"Excellent review response rate of {pct:.0f}%"
        description = (
            f"Response rate of {pct:.0f}% demonstrates strong engagement "
            "with customer feedback. This is a positive local ranking signal "
            "and builds trust with prospective customers."
        )

    recommendation = (
        "Respond to every review within 48 hours. Positive review responses "
        "should thank the customer by name and reference the specific service. "
        "Negative review responses should acknowledge the concern and "
        "offer to resolve the issue offline."
    )

    findings.append(
        create_finding(
            category=CATEGORY,
            subcategory="response_rate",
            severity=severity,
            title=title,
            description=description,
            recommendation=recommendation,
            source=FindingSource.CONNECTED.value,
            effort=EffortLevel.ONGOING.value,
            estimated_impact=ImpactLevel.MEDIUM.value,
            evidence=[
                Evidence(
                    evidence_type="metric",
                    value=f"{pct:.0f}%",
                    context=f"Review response rate: {pct:.0f}%",
                    source_label="Review integration",
                ),
            ],
            tags=["reviews", "response_rate"],
            metadata={"response_rate": response_rate, "response_rate_pct": pct},
        )
    )
    return findings


def _check_response_quality() -> List[AuditFinding]:
    """Check 6: Advisory on review response quality best practices."""
    return [
        create_finding(
            category=CATEGORY,
            subcategory="response_quality",
            severity=FindingSeverity.INFO.value,
            title="Review response quality -- best practices advisory",
            description=(
                "Review response quality cannot be fully assessed from profile "
                "data alone. This advisory outlines best practices. "
                "Positive review responses should: thank the customer by name, "
                "reference the specific service, and be personalized (not "
                "template). Negative review responses should: acknowledge the "
                "concern, take the conversation offline, and offer a resolution."
            ),
            recommendation=(
                "Create review response templates for positive, neutral, and "
                "negative reviews -- but personalize each response. Never "
                "copy-paste the same reply to multiple reviews. Include the "
                "reviewer's name and a detail from their review."
            ),
            source=FindingSource.INFERRED.value,
            effort=EffortLevel.QUICK_WIN.value,
            estimated_impact=ImpactLevel.MEDIUM.value,
            tags=["reviews", "response_quality", "advisory"],
        )
    ]


def _check_platform_distribution(
    archetype: str,
    metrics: Dict[str, Any],
    profile: BusinessProfile,
) -> List[AuditFinding]:
    """Check 7: Review distribution across platforms."""
    findings: List[AuditFinding] = []
    platforms = metrics.get("platforms_with_reviews", [])

    # Check for Yelp presence for local-service archetypes.
    has_yelp_channel = any(
        _normalise_platform(ch.platform) == "yelp" for ch in profile.channels
    )

    if len(platforms) == 0:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="channels.*.review_count",
                impact_description=(
                    "No review data found on any platform. Cannot assess "
                    "review distribution."
                ),
                how_to_provide=(
                    "Add review counts to your channel notes or connect "
                    "review platform integrations."
                ),
                critical_gap=True,
            )
        )
        return findings

    if len(platforms) == 1:
        single_platform = platforms[0]
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="platform_distribution",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Reviews concentrated on {single_platform} only",
                description=(
                    f"Reviews only exist on {single_platform}. A diversified "
                    "review presence across Google, Yelp, and industry-specific "
                    "platforms protects against algorithm changes on any single "
                    "platform and reaches customers who prefer different "
                    "discovery channels."
                ),
                recommendation=(
                    "Diversify review generation across Google, Yelp, and "
                    "industry-relevant platforms. Rotate which platform you "
                    "link to in review request messages."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.MEDIUM.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"Reviews found on: {', '.join(platforms)}",
                        context="Single-platform review concentration",
                        source_label="Profile channel data",
                    ),
                ],
                tags=["reviews", "distribution"],
                metadata={"platforms_with_reviews": platforms},
            )
        )
    else:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="platform_distribution",
                severity=FindingSeverity.LOW.value,
                title=f"Reviews present on {len(platforms)} platforms -- good distribution",
                description=(
                    f"Reviews exist on {len(platforms)} platforms "
                    f"({', '.join(platforms)}). This provides diversified "
                    "social proof across customer discovery channels."
                ),
                recommendation=(
                    "Maintain review presence across platforms. Continue "
                    "rotating review request links across Google and Yelp."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"Reviews found on: {', '.join(platforms)}",
                        context="Multi-platform review distribution",
                        source_label="Profile channel data",
                    ),
                ],
                tags=["reviews", "distribution"],
                metadata={"platforms_with_reviews": platforms},
            )
        )

    # Yelp-specific check for local-service businesses.
    if (
        archetype in _LOCAL_SERVICE_ARCHETYPES
        and "yelp" not in platforms
        and not has_yelp_channel
    ):
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="platform_distribution",
                severity=FindingSeverity.MEDIUM.value,
                title="No Yelp presence for a local service business",
                description=(
                    "Yelp is a significant discovery platform for local services. "
                    "Not having a claimed Yelp profile means potential customers "
                    "searching on Yelp will not find you, or worse, find an "
                    "unclaimed listing with no information."
                ),
                recommendation=(
                    "Claim your Yelp business profile, complete all sections, "
                    "and begin directing a portion of review requests to Yelp."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.MEDIUM.value,
                archetype_relevance=["local-service"],
                tags=["reviews", "yelp", "distribution"],
            )
        )

    # Industry-specific platform check.
    _check_industry_platforms(findings, profile, platforms)

    return findings


def _check_negative_review_patterns(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 8: Patterns in negative reviews."""
    findings: List[AuditFinding] = []
    themes = connected_data.get("sentiment_themes")
    review_texts = connected_data.get("review_texts")

    if themes:
        # Pre-computed negative themes provided.
        for theme in themes:
            findings.append(
                create_finding(
                    category=CATEGORY,
                    subcategory="negative_patterns",
                    severity=FindingSeverity.HIGH.value,
                    title=f"Negative review pattern detected: {theme}",
                    description=(
                        f"Multiple negative reviews mention '{theme}'. This is "
                        "a systemic issue that marketing alone cannot fix. The "
                        "underlying operational problem must be addressed before "
                        "review scores will improve."
                    ),
                    recommendation=(
                        f"Investigate the '{theme}' complaints operationally. "
                        "If 3+ reviews mention the same issue, it is an operations "
                        "problem, not a marketing problem. Fix the root cause, "
                        "then follow up with affected customers."
                    ),
                    source=FindingSource.CONNECTED.value,
                    effort=EffortLevel.SIGNIFICANT.value,
                    estimated_impact=ImpactLevel.HIGH.value,
                    evidence=[
                        Evidence(
                            evidence_type="text",
                            value=f"Recurring negative theme: {theme}",
                            context="Pattern identified from review sentiment analysis",
                            source_label="Review sentiment analysis",
                        ),
                    ],
                    tags=["reviews", "negative_patterns", "operations"],
                    metadata={"negative_theme": theme},
                )
            )
        return findings

    if review_texts:
        # Attempt basic theme extraction from raw review texts.
        detected = _extract_negative_themes(review_texts)
        if detected:
            for theme in detected:
                findings.append(
                    create_finding(
                        category=CATEGORY,
                        subcategory="negative_patterns",
                        severity=FindingSeverity.HIGH.value,
                        title=f"Negative review pattern detected: {theme}",
                        description=(
                            f"Multiple negative reviews reference '{theme}'. "
                            "This is a systemic issue that marketing alone cannot "
                            "fix. Address the underlying operational problem."
                        ),
                        recommendation=(
                            f"Investigate the '{theme}' complaints operationally. "
                            "Categorize negative reviews by theme. If 3+ reviews "
                            "mention the same issue, it is an operations problem, "
                            "not a marketing problem."
                        ),
                        source=FindingSource.CONNECTED.value,
                        effort=EffortLevel.SIGNIFICANT.value,
                        estimated_impact=ImpactLevel.HIGH.value,
                        evidence=[
                            Evidence(
                                evidence_type="text",
                                value=f"Recurring negative theme: {theme}",
                                context="Pattern extracted from review text analysis",
                                source_label="Review text analysis",
                            ),
                        ],
                        tags=["reviews", "negative_patterns", "operations"],
                        metadata={"negative_theme": theme},
                    )
                )
            return findings

    # No review text or sentiment data available.
    findings.append(
        create_finding(
            category=CATEGORY,
            subcategory="negative_patterns",
            severity=FindingSeverity.INFO.value,
            title="Negative review patterns not assessed -- manual review recommended",
            description=(
                "Review text data is not available, so automated pattern "
                "detection could not run. Manually review the last 20 negative "
                "reviews to identify recurring complaint themes."
            ),
            recommendation=(
                "Categorize negative reviews by theme. If 3+ reviews mention "
                "the same issue, it is an operations problem, not a marketing "
                "problem. Common themes include response time, pricing, "
                "communication, and quality."
            ),
            source=FindingSource.MISSING_DATA.value,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.MEDIUM.value,
            tags=["reviews", "negative_patterns", "missing_data"],
            metadata={
                "field_path": "connected_data.review_texts",
                "how_to_provide": (
                    "Connect your review platform APIs to provide review text, "
                    "or manually review the last 20 reviews for recurring "
                    "complaint themes and provide them via "
                    "connected_data['sentiment_themes']."
                ),
            },
        )
    )
    return findings


def _check_review_generation_system(
    profile: BusinessProfile,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 9: Evidence of a systematic review request process."""
    findings: List[AuditFinding] = []
    has_automation = connected_data.get("has_review_automation")

    if has_automation is True:
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="review_generation_system",
                severity=FindingSeverity.INFO.value,
                title="Review generation system appears to be in place",
                description=(
                    "Connected data indicates a review request automation "
                    "system is active. This is the foundation of sustainable "
                    "review growth."
                ),
                recommendation=(
                    "Maintain and optimise your review request system. "
                    "A/B test timing (same-day vs. next-day), message copy, "
                    "and channel (text vs. email) to improve conversion rates."
                ),
                source=FindingSource.CONNECTED.value,
                effort=EffortLevel.QUICK_WIN.value,
                estimated_impact=ImpactLevel.LOW.value,
                tags=["reviews", "automation", "review_generation"],
            )
        )
        return findings

    if has_automation is False:
        # Explicitly reported as absent.
        severity = FindingSeverity.HIGH.value
        source = FindingSource.CONNECTED.value
    else:
        # Infer from profile signals.
        evidence_found = _detect_review_system_signals(profile)
        if evidence_found:
            findings.append(
                create_finding(
                    category=CATEGORY,
                    subcategory="review_generation_system",
                    severity=FindingSeverity.INFO.value,
                    title="Possible review generation system detected from profile signals",
                    description=(
                        "Profile channel notes or integrations suggest a review "
                        "request system may be in place. Confirm this is actively "
                        "running and optimised."
                    ),
                    recommendation=(
                        "Verify your review request system is actively sending "
                        "requests after every service completion. Track the "
                        "conversion rate from request to review."
                    ),
                    source=FindingSource.INFERRED.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    estimated_impact=ImpactLevel.LOW.value,
                    tags=["reviews", "automation", "review_generation"],
                )
            )
            return findings

        severity = FindingSeverity.HIGH.value
        source = FindingSource.INFERRED.value

    findings.append(
        create_finding(
            category=CATEGORY,
            subcategory="review_generation_system",
            severity=severity,
            title="No review generation system detected",
            description=(
                "No evidence of a systematic review request process was found. "
                "Reviews do not happen organically at scale -- businesses that "
                "rely on organic reviews will always be outpaced by competitors "
                "who ask systematically."
            ),
            recommendation=(
                "Implement automated review requests: send via text or email "
                "within 24 hours of service completion, include a direct link "
                "to your Google review page, and make it one-click easy. "
                "Tools like Birdeye, Podium, or a simple CRM automation can "
                "handle this."
            ),
            source=source,
            effort=EffortLevel.MODERATE.value,
            estimated_impact=ImpactLevel.HIGH.value,
            kaicalls_relevant=True,
            tags=["reviews", "automation", "review_generation"],
        )
    )
    return findings


def _check_multi_location_distribution(
    archetype: str,
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 10: Per-location review comparison (multi-location only)."""
    findings: List[AuditFinding] = []

    if archetype not in _MULTI_LOCATION_ARCHETYPES:
        return findings

    locations = connected_data.get("locations")
    if not locations or not isinstance(locations, list) or len(locations) < 2:
        findings.append(
            create_missing_data_finding(
                category=CATEGORY,
                field_path="connected_data.locations",
                impact_description=(
                    "Per-location review data not available for multi-location "
                    "business. Cannot compare review health across locations."
                ),
                how_to_provide=(
                    "Provide per-location review data in connected_data['locations'] "
                    "as a list of dicts, each containing 'name', 'review_count', "
                    "and 'rating'."
                ),
                critical_gap=True,
            )
        )
        return findings

    # Extract per-location counts and ratings.
    loc_counts: List[int] = []
    loc_ratings: List[float] = []
    loc_names: List[str] = []

    for loc in locations:
        name = loc.get("name", "Unknown")
        count = loc.get("review_count")
        rating = loc.get("rating")
        loc_names.append(name)
        if count is not None:
            loc_counts.append(count)
        if rating is not None:
            loc_ratings.append(rating)

    # Compare review counts across locations.
    if len(loc_counts) >= 2:
        avg_count = statistics.mean(loc_counts)
        for i, loc in enumerate(locations):
            name = loc.get("name", "Unknown")
            count = loc.get("review_count")
            if count is not None and avg_count > 0:
                # Flag if significantly below average (less than 50% of mean).
                if count < avg_count * 0.5:
                    findings.append(
                        create_finding(
                            category=CATEGORY,
                            subcategory="multi_location_reviews",
                            severity=FindingSeverity.HIGH.value,
                            title=f"Location '{name}' has only {count} reviews vs. fleet average of {avg_count:.0f}",
                            description=(
                                f"Location '{name}' has {count} reviews compared "
                                f"to the fleet average of {avg_count:.0f}. "
                                "Underperforming locations drag down the whole "
                                "brand's perception in their local market and "
                                "suppress GBP visibility for that location."
                            ),
                            recommendation=(
                                f"Prioritize review generation at the '{name}' "
                                "location. Implement location-specific review "
                                "request links and train staff at this location "
                                "to ask for reviews after every service."
                            ),
                            source=FindingSource.CONNECTED.value,
                            effort=EffortLevel.MODERATE.value,
                            estimated_impact=ImpactLevel.HIGH.value,
                            archetype_relevance=["multi-location"],
                            evidence=[
                                Evidence(
                                    evidence_type="comparison",
                                    value=f"{count} vs. {avg_count:.0f} avg",
                                    context=f"Location '{name}' review count vs. fleet average",
                                    source_label="Per-location review data",
                                ),
                            ],
                            tags=["reviews", "multi_location", "underperforming"],
                            metadata={
                                "location_name": name,
                                "location_review_count": count,
                                "fleet_avg_review_count": round(avg_count),
                            },
                        )
                    )

    # Compare ratings across locations.
    if len(loc_ratings) >= 2:
        avg_rating = statistics.mean(loc_ratings)
        for i, loc in enumerate(locations):
            name = loc.get("name", "Unknown")
            rating = loc.get("rating")
            if rating is not None:
                # Flag if rating is 0.5+ below fleet average.
                if rating < avg_rating - 0.5:
                    findings.append(
                        create_finding(
                            category=CATEGORY,
                            subcategory="multi_location_reviews",
                            severity=FindingSeverity.HIGH.value,
                            title=f"Location '{name}' rated {rating} vs. fleet average {avg_rating:.1f}",
                            description=(
                                f"Location '{name}' has a {rating} rating compared "
                                f"to the fleet average of {avg_rating:.1f}. This "
                                "location's low rating is a brand liability and "
                                "may indicate service quality issues that need "
                                "operational attention."
                            ),
                            recommendation=(
                                f"Investigate service quality at the '{name}' "
                                "location. Review the last 20 negative reviews "
                                "for this location to identify operational issues. "
                                "Address root causes before focusing on review "
                                "generation."
                            ),
                            source=FindingSource.CONNECTED.value,
                            effort=EffortLevel.SIGNIFICANT.value,
                            estimated_impact=ImpactLevel.HIGH.value,
                            archetype_relevance=["multi-location"],
                            evidence=[
                                Evidence(
                                    evidence_type="comparison",
                                    value=f"{rating} vs. {avg_rating:.1f} avg",
                                    context=f"Location '{name}' rating vs. fleet average",
                                    source_label="Per-location review data",
                                ),
                            ],
                            tags=["reviews", "multi_location", "underperforming"],
                            metadata={
                                "location_name": name,
                                "location_rating": rating,
                                "fleet_avg_rating": round(avg_rating, 1),
                            },
                        )
                    )

    # Summary finding: identify strongest and weakest locations.
    if loc_counts and loc_ratings and len(locations) >= 2:
        # Build a composite for identification.
        scored_locs: List[tuple] = []
        for loc in locations:
            name = loc.get("name", "Unknown")
            count = loc.get("review_count", 0) or 0
            rating = loc.get("rating", 0.0) or 0.0
            scored_locs.append((name, count, rating))

        if scored_locs:
            strongest = max(scored_locs, key=lambda x: (x[2], x[1]))
            weakest = min(scored_locs, key=lambda x: (x[2], x[1]))

            if strongest[0] != weakest[0]:
                findings.append(
                    create_finding(
                        category=CATEGORY,
                        subcategory="multi_location_reviews",
                        severity=FindingSeverity.INFO.value,
                        title="Multi-location review profile summary",
                        description=(
                            f"Strongest location: '{strongest[0]}' "
                            f"({strongest[1]} reviews, {strongest[2]} rating). "
                            f"Weakest location: '{weakest[0]}' "
                            f"({weakest[1]} reviews, {weakest[2]} rating). "
                            f"Fleet covers {len(locations)} locations."
                        ),
                        recommendation=(
                            f"Use '{strongest[0]}' as the benchmark for review "
                            "processes. Replicate its review generation practices "
                            f"at '{weakest[0]}' and other underperforming locations."
                        ),
                        source=FindingSource.CONNECTED.value,
                        effort=EffortLevel.MODERATE.value,
                        estimated_impact=ImpactLevel.MEDIUM.value,
                        archetype_relevance=["multi-location"],
                        evidence=[
                            Evidence(
                                evidence_type="comparison",
                                value=(
                                    f"Best: {strongest[0]} ({strongest[1]} reviews, "
                                    f"{strongest[2]} rating) / "
                                    f"Worst: {weakest[0]} ({weakest[1]} reviews, "
                                    f"{weakest[2]} rating)"
                                ),
                                context="Multi-location review profile comparison",
                                source_label="Per-location review data",
                            ),
                        ],
                        tags=["reviews", "multi_location", "summary"],
                        metadata={
                            "strongest_location": strongest[0],
                            "weakest_location": weakest[0],
                            "total_locations": len(locations),
                        },
                    )
                )

    return findings


# ============================================================================
# Internal helpers
# ============================================================================


def _resolve_archetype(profile: BusinessProfile) -> str:
    """Return the normalised archetype string from the profile."""
    arch = ""
    if hasattr(profile, "classification") and profile.classification:
        arch = getattr(profile.classification, "archetype", "") or ""
    return arch.lower().strip()


def _normalise_platform(name: str) -> str:
    """Normalise a platform name to a canonical key."""
    key = name.lower().strip().replace(" ", "_").replace("-", "_")
    return _PLATFORM_ALIASES.get(key, key)


def _extract_review_count(text: str) -> Optional[int]:
    """Parse a review count from freeform text.

    Matches patterns like ``"87 reviews"``, ``"reviews: 87"``,
    ``"87 google reviews"``, ``"review count: 87"``.
    """
    if not text:
        return None

    # Pattern 1: "{N} review(s)"
    m = re.search(r"(\d+)\s*(?:google\s*)?reviews?", text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    # Pattern 2: "review(s): {N}" or "review count: {N}"
    m = re.search(r"reviews?\s*(?:count)?\s*[:=]\s*(\d+)", text, re.IGNORECASE)
    if m:
        return int(m.group(1))

    return None


def _extract_rating(text: str) -> Optional[float]:
    """Parse a star rating from freeform text.

    Matches patterns like ``"4.7 rating"``, ``"rating: 4.7"``,
    ``"4.7 stars"``, ``"4.7/5"``.
    """
    if not text:
        return None

    # Pattern 1: "{N.N} rating/stars" or "{N.N}/5"
    m = re.search(r"(\d+\.?\d*)\s*(?:star|rating|/5)", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        if 1.0 <= val <= 5.0:
            return val

    # Pattern 2: "rating: {N.N}"
    m = re.search(r"rating\s*[:=]\s*(\d+\.?\d*)", text, re.IGNORECASE)
    if m:
        val = float(m.group(1))
        if 1.0 <= val <= 5.0:
            return val

    return None


def _assess_local_service_review_count(
    count: int,
) -> tuple:
    """Return (severity, title, description) for local-service review count."""
    if count < 10:
        return (
            FindingSeverity.CRITICAL.value,
            f"Only {count} Google reviews -- critically low for a local service",
            (
                f"Google review count is {count}, which is critically low for "
                "a local service business. Fewer than 10 reviews means you are "
                "invisible in local search results and lack the social proof "
                "needed to convert searchers into customers."
            ),
        )
    elif count < 20:
        return (
            FindingSeverity.HIGH.value,
            f"{count} Google reviews -- below minimum for local trust",
            (
                f"Google review count is {count}. This is below the minimum "
                "threshold where reviews begin to build meaningful local trust. "
                "Competitors with 50+ reviews will consistently outrank you "
                "in the local pack."
            ),
        )
    elif count < 50:
        return (
            FindingSeverity.MEDIUM.value,
            f"{count} Google reviews -- building but not yet competitive",
            (
                f"Google review count is {count}. You have a foundation but "
                "are not yet competitive with established local businesses "
                "that have 100+ reviews. Continue systematic review generation."
            ),
        )
    elif count < 100:
        return (
            FindingSeverity.LOW.value,
            f"{count} Google reviews -- solid but room to grow",
            (
                f"Google review count is {count}. This is a solid foundation "
                "that provides good social proof. Continue growing toward 100+ "
                "to dominate the local pack."
            ),
        )
    else:
        return (
            FindingSeverity.INFO.value,
            f"{count} Google reviews -- strong review profile",
            (
                f"Google review count of {count} is strong. This provides "
                "substantial social proof and supports local search ranking. "
                "Maintain your review generation velocity."
            ),
        )


def _assess_professional_services_review_count(
    count: int,
) -> tuple:
    """Return (severity, title, description) for professional-services review count."""
    if count < 5:
        return (
            FindingSeverity.HIGH.value,
            f"Only {count} Google reviews -- below minimum for professional credibility",
            (
                f"Google review count is {count}. Professional services "
                "businesses need at least 5 reviews to establish basic "
                "credibility. Prospects researching firms will be hesitant "
                "to engage with a firm that has almost no reviews."
            ),
        )
    elif count < 15:
        return (
            FindingSeverity.MEDIUM.value,
            f"{count} Google reviews -- adequate but not differentiating",
            (
                f"Google review count is {count}. This provides basic social "
                "proof but does not differentiate you from competitors. "
                "Target 15+ reviews to stand out in your market."
            ),
        )
    elif count < 30:
        return (
            FindingSeverity.LOW.value,
            f"{count} Google reviews -- solid for a professional services firm",
            (
                f"Google review count of {count} is solid for a professional "
                "services business. This builds meaningful credibility with "
                "prospects evaluating firms."
            ),
        )
    else:
        return (
            FindingSeverity.INFO.value,
            f"{count} Google reviews -- excellent for professional services",
            (
                f"Google review count of {count} is excellent for a professional "
                "services firm. This volume of social proof is a genuine "
                "competitive advantage in prospect evaluation."
            ),
        )


def _compute_velocity(review_dates: List[str]) -> Optional[float]:
    """Compute reviews-per-month from a list of ISO date strings.

    Returns ``None`` if fewer than 2 dates are parseable or the date
    range spans less than 1 day.
    """
    parsed: List[datetime] = []
    for ds in review_dates:
        dt = _parse_date(ds)
        if dt is not None:
            parsed.append(dt)

    if len(parsed) < 2:
        return None

    parsed.sort()
    span_days = (parsed[-1] - parsed[0]).days
    if span_days < 1:
        return None

    months = span_days / 30.44  # Average days per month.
    if months < 0.1:
        return None

    return round(len(parsed) / months, 1)


def _days_since_date(date_str: str) -> Optional[int]:
    """Return number of days between *date_str* and today (UTC).

    Returns ``None`` if parsing fails.
    """
    dt = _parse_date(date_str)
    if dt is None:
        return None
    now = datetime.now(timezone.utc)
    delta = now - dt
    return max(0, delta.days)


def _parse_date(date_str: str) -> Optional[datetime]:
    """Best-effort ISO date parse.  Returns a tz-aware datetime or None."""
    if not date_str:
        return None
    # Try full ISO first, then date-only.
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
        try:
            dt = datetime.strptime(date_str.strip(), fmt)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt
        except ValueError:
            continue
    return None


def _detect_review_system_signals(profile: BusinessProfile) -> bool:
    """Look for clues in the profile that a review request system exists."""
    # Check channel notes for automation keywords.
    automation_keywords = [
        "review request",
        "review automation",
        "automated review",
        "review follow-up",
        "review follow up",
        "birdeye",
        "podium",
        "grade.us",
        "nicejob",
        "reputation.com",
        "widewail",
        "reviewtrackers",
        "broadly",
    ]

    for ch in profile.channels:
        notes = (ch.notes or "").lower()
        for keyword in automation_keywords:
            if keyword in notes:
                return True

    # Check raw_notes on the profile.
    raw = (profile.raw_notes or "").lower()
    for keyword in automation_keywords:
        if keyword in raw:
            return True

    return False


def _check_industry_platforms(
    findings: List[AuditFinding],
    profile: BusinessProfile,
    existing_platforms: List[str],
) -> None:
    """Append findings for missing industry-specific review platforms."""
    industry = ""
    vertical = ""
    if hasattr(profile, "classification") and profile.classification:
        industry = (getattr(profile.classification, "industry", "") or "").lower()
        vertical = (getattr(profile.classification, "vertical", "") or "").lower()

    # Collect all relevant industry platforms.
    relevant: set = set()
    for keyword, platforms in _INDUSTRY_PLATFORMS.items():
        if keyword in industry or keyword in vertical:
            relevant.update(platforms)

    if not relevant:
        return

    # Check which are missing from existing review platforms and channels.
    all_channel_platforms = {
        _normalise_platform(ch.platform) for ch in profile.channels
    }
    existing_set = set(existing_platforms) | all_channel_platforms

    missing = relevant - existing_set
    if missing:
        platform_list = ", ".join(sorted(missing))
        findings.append(
            create_finding(
                category=CATEGORY,
                subcategory="platform_distribution",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Missing industry review platforms: {platform_list}",
                description=(
                    f"For a {industry or vertical} business, the following "
                    f"industry-specific review platforms are relevant but "
                    f"not found in your profile: {platform_list}. These "
                    "platforms are where prospective customers in your "
                    "industry specifically look for reviews."
                ),
                recommendation=(
                    f"Claim and optimize your presence on {platform_list}. "
                    "Ensure your business information is accurate and begin "
                    "directing a portion of review requests to these "
                    "industry-specific platforms."
                ),
                source=FindingSource.STATIC.value,
                effort=EffortLevel.MODERATE.value,
                estimated_impact=ImpactLevel.MEDIUM.value,
                tags=["reviews", "industry_platforms", "distribution"],
                metadata={
                    "missing_platforms": sorted(missing),
                    "industry": industry,
                    "vertical": vertical,
                },
            )
        )


def _extract_negative_themes(review_texts: List[str]) -> List[str]:
    """Basic keyword-frequency extraction from negative review texts.

    This is a heuristic fallback when pre-computed sentiment themes are
    not available.  It counts occurrences of common complaint categories
    and returns themes that appear in 3+ reviews.
    """
    theme_keywords: Dict[str, List[str]] = {
        "response time": ["slow response", "never called back", "didn't respond",
                          "no response", "took forever", "waited", "waiting",
                          "didn't return", "hours to respond", "days to respond",
                          "late", "no show", "no-show"],
        "pricing": ["overcharged", "too expensive", "price", "pricing",
                     "rip off", "rip-off", "hidden fee", "hidden charge",
                     "overpriced", "gouging", "bait and switch"],
        "communication": ["poor communication", "no communication",
                          "didn't explain", "confusing", "miscommunication",
                          "unclear", "never told", "didn't inform",
                          "lack of communication", "unresponsive"],
        "quality": ["poor quality", "bad work", "shoddy", "incomplete",
                     "had to redo", "came back", "broke again", "didn't fix",
                     "still broken", "terrible job", "awful work",
                     "not professional"],
        "customer service": ["rude", "unprofessional", "disrespectful",
                             "dismissive", "wouldn't listen", "argued",
                             "attitude", "unhelpful", "condescending"],
        "scheduling": ["missed appointment", "late arrival", "didn't show",
                       "rescheduled", "scheduling", "cancelled",
                       "wrong time", "wrong day"],
        "cleanliness": ["mess", "messy", "dirty", "didn't clean up",
                        "left a mess", "cleanup", "filthy"],
    }

    theme_counts: Dict[str, int] = {t: 0 for t in theme_keywords}

    for text in review_texts:
        lower = text.lower()
        for theme, keywords in theme_keywords.items():
            for kw in keywords:
                if kw in lower:
                    theme_counts[theme] += 1
                    break  # Count each review only once per theme.

    # Return themes appearing in 3+ reviews.
    return [theme for theme, count in theme_counts.items() if count >= 3]
