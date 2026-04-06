"""Paid media readiness audit engine for the Kai Marketing OS.

Evaluates whether a business has the prerequisites in place to run
paid advertising effectively across major platforms.  Checks conversion
tracking, landing pages, ad account status, pixel/tag installation,
audience definitions, budget allocation, creative assets, offer/CTA
clarity, competitor landscape, compliance requirements, and produces
per-platform readiness assessments.

Before spending a single dollar on advertising, a business needs
prerequisites in place: conversion tracking, landing pages, creative
assets, audience definitions, and compliance readiness.  Launching paid
campaigns without these prerequisites wastes budget and produces
misleading data.

Usage::

    from kai.audits.paid_media_readiness import (
        audit_paid_media_readiness,
        score_paid_media_readiness,
        get_platform_prerequisites,
    )
    from kai.models.business_profile import BusinessProfile

    findings = audit_paid_media_readiness(profile, connected_data=None)
    score = score_paid_media_readiness(findings)
    prereqs = get_platform_prerequisites("google_ads", "local-service")
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

# ============================================================================
# Constants
# ============================================================================

CATEGORY = "paid_media_readiness"

# Platform display names for human-readable output
_PLATFORM_DISPLAY: Dict[str, str] = {
    "google_ads": "Google Ads",
    "meta_ads": "Meta Ads (Facebook/Instagram)",
    "linkedin_ads": "LinkedIn Ads",
    "tiktok_ads": "TikTok Ads",
    "microsoft_ads": "Microsoft/Bing Ads",
    "pinterest_ads": "Pinterest Ads",
    "snapchat_ads": "Snapchat Ads",
    "amazon_ads": "Amazon Ads",
    "x_ads": "X/Twitter Ads",
}

# All ad platform channel names recognized by the audit
_AD_PLATFORMS = set(_PLATFORM_DISPLAY.keys())

# Analytics channel names that indicate conversion tracking
_ANALYTICS_CHANNELS = {"ga4", "google_analytics", "google_ads", "analytics"}

# Minimum monthly budgets (USD) by platform to generate meaningful data
_PLATFORM_MIN_BUDGETS: Dict[str, float] = {
    "google_ads": 500.0,
    "meta_ads": 500.0,
    "linkedin_ads": 1000.0,
    "tiktok_ads": 500.0,
    "microsoft_ads": 300.0,
    "pinterest_ads": 300.0,
    "snapchat_ads": 300.0,
    "amazon_ads": 500.0,
    "x_ads": 300.0,
}

# Recommended ad platforms per archetype (ordered by priority)
_ARCHETYPE_PLATFORM_RECOMMENDATIONS: Dict[str, List[str]] = {
    "local-service": ["google_ads", "meta_ads"],
    "ecommerce": ["google_ads", "meta_ads", "tiktok_ads", "pinterest_ads"],
    "professional-services": ["google_ads", "linkedin_ads", "meta_ads"],
    "multi-location": ["google_ads", "meta_ads"],
    "creator": ["meta_ads", "tiktok_ads", "x_ads"],
    "saas": ["google_ads", "linkedin_ads", "meta_ads"],
}

# Industries considered regulated for ad compliance purposes
_REGULATED_INDUSTRIES = {
    "healthcare", "health", "medical", "dental", "pharmacy",
    "legal", "law", "attorney",
    "financial", "finance", "banking", "insurance", "lending", "mortgage",
    "real_estate", "real estate", "property", "housing",
    "alcohol", "cannabis", "gambling",
}

# Pixel/tag advisory messages per platform
_PIXEL_TAG_ADVISORY: Dict[str, str] = {
    "google_ads": (
        "Verify Google Ads conversion tag and Google Tag Manager are "
        "installed"
    ),
    "meta_ads": (
        "Verify Meta Pixel is installed and firing on all key pages"
    ),
    "linkedin_ads": "Verify LinkedIn Insight Tag is installed",
    "tiktok_ads": "Verify TikTok Pixel is installed",
    "microsoft_ads": "Verify Microsoft UET tag is installed",
    "pinterest_ads": "Verify Pinterest Tag is installed",
    "snapchat_ads": "Verify Snap Pixel is installed",
    "amazon_ads": "Verify Amazon Attribution tracking is configured",
    "x_ads": "Verify X/Twitter Pixel is installed",
}


# ============================================================================
# Platform prerequisites
# ============================================================================


def get_platform_prerequisites(platform: str, archetype: str) -> List[str]:
    """Return the list of prerequisites for a specific platform + archetype.

    Each prerequisite is a short human-readable string describing what
    must be in place before launching ads on the given platform.

    Parameters
    ----------
    platform:
        Canonical platform name (e.g., ``"google_ads"``).
    archetype:
        Business archetype (e.g., ``"local-service"``).

    Returns
    -------
    List[str]
        Ordered list of prerequisite descriptions.
    """
    base: Dict[str, List[str]] = {
        "google_ads": [
            "Ad account created and billing set up",
            "Conversion tracking via Google Tag or GA4",
            "Landing pages with relevant content",
            "Keyword research completed",
            "Ad copy drafted (headlines and descriptions)",
            "Daily budget set",
        ],
        "meta_ads": [
            "Business Manager set up",
            "Ad account created and billing set up",
            "Meta Pixel installed and verified",
            "Custom audiences defined (website visitors, email list)",
            "Ad creative ready (images, video, copy)",
            "Campaign structure defined (campaign > ad set > ad)",
        ],
        "linkedin_ads": [
            "Campaign Manager account created",
            "Ad account billing configured",
            "LinkedIn Insight Tag installed",
            "Target audience defined (job titles, industries, company size)",
            "Ad creative and copy ready",
            "Budget set (minimum $10/day recommended)",
        ],
        "tiktok_ads": [
            "TikTok Ads Manager account created",
            "Ad account billing configured",
            "TikTok Pixel installed",
            "Video creative ready (vertical 9:16 format)",
            "Target audience defined",
            "Budget set",
        ],
        "microsoft_ads": [
            "Microsoft Advertising account created",
            "UET tag installed",
            "Conversion goals configured",
            "Ad copy drafted",
            "Budget set",
        ],
        "pinterest_ads": [
            "Pinterest Business account created",
            "Pinterest Tag installed",
            "Pin creative ready (2:3 aspect ratio)",
            "Audience targeting defined",
            "Budget set",
        ],
        "snapchat_ads": [
            "Snapchat Ads Manager account created",
            "Snap Pixel installed",
            "Creative ready (vertical video or image)",
            "Audience targeting defined",
            "Budget set",
        ],
        "amazon_ads": [
            "Amazon Seller/Vendor Central account active",
            "Amazon Attribution configured",
            "Product listings optimized",
            "Ad copy and keywords ready",
            "Budget set",
        ],
        "x_ads": [
            "X Ads account created and verified",
            "X Pixel installed",
            "Ad creative ready",
            "Target audience defined",
            "Budget set",
        ],
    }

    prereqs = list(base.get(platform, [
        "Ad account created and billing set up",
        "Conversion tracking installed",
        "Landing pages ready",
        "Ad creative prepared",
        "Budget set",
    ]))

    # Archetype-specific additions
    if platform == "google_ads" and archetype == "local-service":
        prereqs.extend([
            "Google Guaranteed or Google Screened badge applied for (LSA)",
            "Background check submitted (LSA)",
            "License and insurance documentation uploaded (LSA)",
            "Service areas defined (LSA)",
            "Business hours set (LSA)",
            "LSA budget set separately from Search budget",
        ])

    if platform == "meta_ads":
        prereqs.append(
            "Special Ad Category designation if applicable "
            "(housing, employment, credit, social issues)"
        )

    if platform == "google_ads" and archetype == "ecommerce":
        prereqs.extend([
            "Google Merchant Center set up and product feed active",
            "Shopping campaign structure defined",
        ])

    if platform == "google_ads" and archetype == "professional-services":
        prereqs.append(
            "Lawyer/professional advertising certification if required "
            "by jurisdiction"
        )

    if platform == "linkedin_ads" and archetype in (
        "professional-services", "saas"
    ):
        prereqs.append("Thought leadership content ready for Sponsored Content")

    return prereqs


# ============================================================================
# Individual check functions
# ============================================================================


def _check_conversion_tracking(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Check 1: Conversion Tracking Installed.

    Verifies that analytics and conversion tracking are in place.
    Running paid ads without tracking is the most fundamental
    mistake -- every dollar spent produces no attributable data.
    """
    findings: List[AuditFinding] = []

    analytics_channels = [
        ch for ch in profile.channels
        if ch.platform.lower() in _ANALYTICS_CHANNELS
    ]

    if not analytics_channels:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="conversion_tracking",
            severity=FindingSeverity.CRITICAL.value,
            title="No conversion tracking detected",
            description=(
                "No analytics or conversion tracking channel was found in "
                "the business profile. Running paid ads without tracking is "
                "burning money blind -- there is no way to measure which "
                "campaigns produce results, which audiences convert, or "
                "what the cost per acquisition actually is."
            ),
            recommendation=(
                "Before spending $1 on ads: (1) Install Google Analytics 4, "
                "(2) Set up conversion events (form submit, phone click, "
                "purchase), (3) Verify events fire correctly, (4) Import "
                "conversions into ad platforms"
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="No analytics channel in profile.channels",
                source_label="BusinessProfile.channels",
            )],
            tags=["conversion_tracking", "analytics", "blocking"],
        ))
        return findings

    # Analytics exists -- check connection status
    connected_analytics = [ch for ch in analytics_channels if ch.is_connected]
    disconnected_analytics = [
        ch for ch in analytics_channels if not ch.is_connected
    ]

    if not connected_analytics and disconnected_analytics:
        platforms = ", ".join(ch.platform for ch in disconnected_analytics)
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="conversion_tracking",
            severity=FindingSeverity.HIGH.value,
            title="Analytics exists but is not connected",
            description=(
                f"Analytics channel(s) ({platforms}) exist in the profile but "
                "none are connected. Conversion tracking cannot be verified "
                "without a live connection. Ad platforms need verified "
                "conversion signals to optimize campaigns."
            ),
            recommendation=(
                "Connect analytics to verify conversion tracking: "
                "(1) Confirm the analytics property is receiving data, "
                "(2) Verify conversion events are configured, "
                "(3) Import conversions into ad platforms"
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Disconnected analytics: {platforms}",
                source_label="BusinessProfile.channels",
            )],
            tags=["conversion_tracking", "analytics"],
        ))

    # If connected, check for conversion event indicators in connected_data
    if connected_analytics:
        if connected_data and connected_data.get("conversion_events_configured"):
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="conversion_tracking",
                severity=FindingSeverity.INFO.value,
                title="Conversion tracking verified and active",
                description=(
                    "Analytics is connected and conversion events are "
                    "configured. Paid ad platforms can receive conversion "
                    "signals for optimization."
                ),
                recommendation=(
                    "Maintain conversion tracking hygiene: review tracked "
                    "events quarterly, ensure new funnels are tracked, and "
                    "verify data accuracy in ad platforms."
                ),
                estimated_impact=ImpactLevel.LOW.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="checklist_item",
                    value="Conversion events confirmed via connected data",
                    source_label="Connected analytics data",
                )],
                tags=["conversion_tracking", "analytics"],
            ))
        elif connected_data and not connected_data.get("conversion_events_configured"):
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="conversion_tracking",
                severity=FindingSeverity.HIGH.value,
                title="Analytics connected but no conversion events configured",
                description=(
                    "Analytics is connected and receiving traffic data, but "
                    "no conversion events have been configured. Without "
                    "conversion events, ad platforms cannot optimize for "
                    "actual business outcomes."
                ),
                recommendation=(
                    "Set up conversion events in GA4: (1) Form submissions, "
                    "(2) Phone number clicks, (3) Purchases/bookings, "
                    "(4) Key page visits. Then import these as conversions "
                    "in each ad platform."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.CONNECTED.value,
                evidence=[Evidence(
                    evidence_type="checklist_item",
                    value="Analytics connected but conversion_events_configured=False",
                    source_label="Connected analytics data",
                )],
                tags=["conversion_tracking", "analytics"],
            ))
        else:
            # Connected but no connected_data to verify events
            platforms = ", ".join(ch.platform for ch in connected_analytics)
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="conversion_tracking",
                severity=FindingSeverity.INFO.value,
                title=f"Analytics connected ({platforms})",
                description=(
                    f"Analytics channel(s) ({platforms}) are connected. "
                    "Conversion event configuration could not be verified "
                    "from the available data -- manual verification is "
                    "recommended before launching paid campaigns."
                ),
                recommendation=(
                    "Manually verify that conversion events are set up and "
                    "firing: check GA4 > Admin > Events for configured "
                    "conversions, and verify each ad platform is receiving "
                    "conversion data."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.STATIC.value,
                evidence=[Evidence(
                    evidence_type="checklist_item",
                    value=f"Connected analytics: {platforms}",
                    source_label="BusinessProfile.channels",
                )],
                tags=["conversion_tracking", "analytics"],
            ))

    return findings


def _check_landing_pages(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 2: Landing Pages Exist for Key Offers.

    Sending paid traffic to a homepage wastes 30-50% of ad spend.
    Each primary offer needs a dedicated landing page with specific
    CTA, social proof, and service details.
    """
    findings: List[AuditFinding] = []

    if not profile.offers:
        # No offers means we cannot assess landing pages -- this is
        # caught more severely by _check_offer_cta (Check 8).
        return findings

    primary_offers = [o for o in profile.offers if o.is_primary]
    if not primary_offers:
        primary_offers = profile.offers[:3]  # Assess top offers if none marked

    offers_missing_lp = []
    offers_with_lp = []

    for offer in primary_offers:
        # Landing page evidence: a URL-like string in the offer metadata,
        # the offer description mentioning a page, or connected_data with
        # landing page URLs.  We check for url-like patterns in the offer.
        has_lp_evidence = False
        if hasattr(offer, "metadata") and isinstance(
            getattr(offer, "metadata", None), dict
        ):
            meta = offer.metadata  # type: ignore[union-attr]
            if meta.get("landing_page_url") or meta.get("landing_page"):
                has_lp_evidence = True
        if not has_lp_evidence:
            offers_missing_lp.append(offer.name)
        else:
            offers_with_lp.append(offer.name)

    if offers_missing_lp:
        missing_list = ", ".join(offers_missing_lp)

        if archetype == "ecommerce":
            desc = (
                f"No dedicated landing pages detected for: {missing_list}. "
                "Product pages and collection pages serve as landing pages "
                "for ecommerce -- ensure they are conversion-optimized with "
                "clear CTAs, trust badges, reviews, and urgency elements."
            )
        elif archetype == "local-service":
            desc = (
                f"No dedicated landing pages detected for: {missing_list}. "
                "Each core service needs its own landing page with a specific "
                "CTA, social proof, service details, and service area "
                "information. Sending ad traffic to the homepage wastes "
                "30-50% of ad spend."
            )
        else:
            desc = (
                f"No dedicated landing pages detected for: {missing_list}. "
                "Sending ad traffic to the homepage instead of a dedicated "
                "landing page wastes 30-50% of ad spend. Each primary offer "
                "needs a focused page with a single CTA."
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="landing_pages",
            severity=FindingSeverity.HIGH.value,
            title="No dedicated landing pages for primary offers",
            description=desc,
            recommendation=(
                "Create a dedicated landing page for each primary offer. "
                "Include: headline matching the ad, specific CTA, trust "
                "signals, and no navigation distractions."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.SIGNIFICANT.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Offers missing landing pages: {missing_list}",
                source_label="BusinessProfile.offers",
            )],
            tags=["landing_pages", "conversion"],
        ))

    if offers_with_lp:
        lp_list = ", ".join(offers_with_lp)
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="landing_pages",
            severity=FindingSeverity.INFO.value,
            title="Landing pages detected for offers",
            description=(
                f"Landing page evidence found for: {lp_list}. Verify that "
                "these pages have ad-specific headlines, strong CTAs, trust "
                "signals, and no distracting navigation."
            ),
            recommendation=(
                "Review each landing page for ad readiness: does the "
                "headline match the ad? Is there a single clear CTA? Are "
                "trust signals above the fold?"
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Offers with landing pages: {lp_list}",
                source_label="BusinessProfile.offers",
            )],
            tags=["landing_pages"],
        ))

    return findings


def _check_ad_account_status(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 3: Ad Account Status.

    Verifies which ad platform accounts exist and their connection
    status.  Also flags recommended platforms that are missing.
    """
    findings: List[AuditFinding] = []

    ad_channels = {
        ch.platform.lower(): ch
        for ch in profile.channels
        if ch.platform.lower() in _AD_PLATFORMS
    }

    # Report on present platforms
    for platform_key, channel in ad_channels.items():
        display = _PLATFORM_DISPLAY.get(platform_key, platform_key)
        if channel.is_connected:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="ad_account_status",
                severity=FindingSeverity.INFO.value,
                title=f"{display} ad account connected",
                description=(
                    f"{display} ad account is connected and accessible. "
                    "Billing, targeting, and creative can be configured."
                ),
                recommendation=(
                    f"Verify {display} billing is active and account is "
                    "in good standing before launching campaigns."
                ),
                estimated_impact=ImpactLevel.LOW.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.STATIC.value,
                evidence=[Evidence(
                    evidence_type="checklist_item",
                    value=f"{display} is_connected=True",
                    source_label="BusinessProfile.channels",
                )],
                tags=["ad_account", platform_key],
            ))
        else:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="ad_account_status",
                severity=FindingSeverity.MEDIUM.value,
                title=f"{display} ad account not connected",
                description=(
                    f"{display} ad account exists in the profile but is not "
                    "connected. Connection is required before running ads "
                    "on this platform."
                ),
                recommendation=(
                    f"Connect the {display} ad account: verify credentials, "
                    "confirm billing information, and grant API access."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.STATIC.value,
                evidence=[Evidence(
                    evidence_type="checklist_item",
                    value=f"{display} is_connected=False",
                    source_label="BusinessProfile.channels",
                )],
                tags=["ad_account", platform_key],
            ))

    # Flag recommended platforms that are missing entirely
    recommended = _ARCHETYPE_PLATFORM_RECOMMENDATIONS.get(archetype or "", [])
    for platform_key in recommended:
        if platform_key not in ad_channels:
            display = _PLATFORM_DISPLAY.get(platform_key, platform_key)
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="ad_account_status",
                severity=FindingSeverity.MEDIUM.value,
                title=f"No {display} account",
                description=(
                    f"No {display} account found in the business profile. "
                    f"This is a recommended advertising channel for the "
                    f"{archetype or 'your'} archetype."
                ),
                recommendation=(
                    f"Create a {display} ad account and connect it to "
                    "begin advertising on this recommended platform."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.STATIC.value,
                evidence=[Evidence(
                    evidence_type="checklist_item",
                    value=(
                        f"{display} is a recommended channel for "
                        f"{archetype or 'this'} archetype but not present"
                    ),
                    source_label="Archetype channel recommendations",
                )],
                tags=["ad_account", platform_key],
            ))

    return findings


def _check_pixel_tag_status(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]],
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 4: Pixel/Tag Status.

    Verifies pixel and tracking tag installation for each ad platform.
    Uses connected_data if available; otherwise generates per-platform
    advisory findings.
    """
    findings: List[AuditFinding] = []

    ad_channels = {
        ch.platform.lower(): ch
        for ch in profile.channels
        if ch.platform.lower() in _AD_PLATFORMS
    }

    # Determine which platforms have active or planned ad spend
    recommended = set(
        _ARCHETYPE_PLATFORM_RECOMMENDATIONS.get(archetype or "", [])
    )
    active_platforms = {
        p for p, ch in ad_channels.items()
        if ch.is_active or ch.is_connected
    }

    # Check connected_data for pixel verification
    pixel_data = (
        connected_data.get("pixel_verification", {})
        if connected_data
        else {}
    )

    platforms_to_check = set(ad_channels.keys()) | recommended

    for platform_key in sorted(platforms_to_check):
        display = _PLATFORM_DISPLAY.get(platform_key, platform_key)
        advisory = _PIXEL_TAG_ADVISORY.get(platform_key, f"Verify {display} tracking pixel is installed")

        if platform_key in pixel_data:
            status = pixel_data[platform_key]
            is_verified = status.get("verified", False) if isinstance(status, dict) else bool(status)
            if is_verified:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="pixel_tag_status",
                    severity=FindingSeverity.INFO.value,
                    title=f"{display} pixel/tag verified",
                    description=(
                        f"{display} tracking pixel or tag has been verified "
                        "as installed and firing correctly."
                    ),
                    recommendation=(
                        f"Monitor {display} pixel health regularly. Check "
                        "for errors in the platform's event diagnostics tool."
                    ),
                    estimated_impact=ImpactLevel.LOW.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    source=FindingSource.CONNECTED.value,
                    evidence=[Evidence(
                        evidence_type="checklist_item",
                        value=f"{display} pixel verified=True",
                        source_label="Connected pixel verification data",
                    )],
                    tags=["pixel", "tracking", platform_key],
                ))
            else:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="pixel_tag_status",
                    severity=FindingSeverity.HIGH.value,
                    title=f"{display} pixel/tag not verified",
                    description=(
                        f"{display} tracking pixel or tag was checked but "
                        "could not be verified. Ads cannot track conversions "
                        "without a working pixel."
                    ),
                    recommendation=advisory,
                    estimated_impact=ImpactLevel.HIGH.value,
                    effort=EffortLevel.MODERATE.value,
                    source=FindingSource.CONNECTED.value,
                    evidence=[Evidence(
                        evidence_type="checklist_item",
                        value=f"{display} pixel verified=False",
                        source_label="Connected pixel verification data",
                    )],
                    tags=["pixel", "tracking", platform_key],
                ))
        else:
            # No connected data -- generate advisory
            is_active_or_planned = (
                platform_key in active_platforms
                or platform_key in recommended
            )
            severity = (
                FindingSeverity.HIGH.value
                if platform_key in active_platforms
                else FindingSeverity.MEDIUM.value
            )

            if is_active_or_planned:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="pixel_tag_status",
                    severity=severity,
                    title=f"{display} pixel/tag status unknown",
                    description=(
                        f"{display} pixel or tracking tag installation could "
                        "not be verified from available data. "
                        + (
                            "This platform has active or connected status, "
                            "making pixel verification a high priority."
                            if platform_key in active_platforms
                            else "This is a recommended platform for your "
                            "archetype."
                        )
                    ),
                    recommendation=advisory,
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    effort=EffortLevel.MODERATE.value,
                    source=FindingSource.MISSING_DATA.value,
                    evidence=[Evidence(
                        evidence_type="missing_data",
                        value=f"pixel_verification.{platform_key}",
                        context=f"Cannot verify {display} pixel installation",
                        source_label="Pixel verification data",
                    )],
                    tags=["pixel", "tracking", platform_key],
                    metadata={
                        "field_path": f"pixel_verification.{platform_key}",
                        "how_to_provide": (
                            f"Connect {display} account or manually verify "
                            "pixel installation using the platform's tag "
                            "diagnostics tool."
                        ),
                    },
                ))

    return findings


def _check_audience_definitions(
    profile: BusinessProfile,
) -> List[AuditFinding]:
    """Check 5: Audience Definitions.

    Ad targeting requires clear audience definitions.  Personas with
    demographics, pain points, and channel preferences produce more
    effective ad targeting.
    """
    findings: List[AuditFinding] = []

    if not profile.personas:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="audience_definitions",
            severity=FindingSeverity.HIGH.value,
            title="No target personas defined",
            description=(
                "No target personas are defined in the business profile. "
                "Ad targeting requires clear audience definitions -- without "
                "them, campaigns target too broadly and waste budget on "
                "unqualified traffic."
            ),
            recommendation=(
                "Define for each persona: demographics (age, location, "
                "income), interests/behaviors (for platform targeting), "
                "pain points (for ad copy), and buying triggers (for "
                "campaign timing)"
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="profile.personas is empty",
                source_label="BusinessProfile.personas",
            )],
            tags=["audience", "targeting", "personas"],
        ))
        return findings

    # Check persona quality
    well_defined = []
    missing_channels = []

    for persona in profile.personas:
        has_demographics = bool(persona.demographics)
        has_pain_points = bool(persona.pain_points)
        has_channels = bool(persona.channels_used)

        if has_demographics and has_pain_points and has_channels:
            well_defined.append(persona.name)
        elif not has_channels:
            missing_channels.append(persona.name)

    if missing_channels:
        names = ", ".join(missing_channels)
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="audience_definitions",
            severity=FindingSeverity.MEDIUM.value,
            title="Personas missing channel preferences",
            description=(
                f"Personas defined but missing channel preferences: "
                f"{names}. Channel preferences affect platform-specific "
                "targeting -- knowing where your audience spends time "
                "determines which ad platforms to prioritize."
            ),
            recommendation=(
                "Add channels_used to each persona: which social platforms "
                "do they use? Where do they search? What content do they "
                "consume? This drives platform selection and targeting."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Personas missing channels_used: {names}",
                source_label="BusinessProfile.personas",
            )],
            tags=["audience", "targeting", "personas"],
        ))

    if well_defined:
        names = ", ".join(well_defined)
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="audience_definitions",
            severity=FindingSeverity.INFO.value,
            title="Personas are well-defined for ad targeting",
            description=(
                f"The following personas have demographics, pain points, "
                f"and channel preferences defined: {names}. These can be "
                "directly translated into ad platform audience targeting."
            ),
            recommendation=(
                "Translate persona definitions into platform-specific "
                "targeting: create custom audiences, lookalike audiences, "
                "and interest-based targeting from the persona data."
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Well-defined personas: {names}",
                source_label="BusinessProfile.personas",
            )],
            tags=["audience", "targeting", "personas"],
        ))

    return findings


def _check_budget_allocated(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 6: Budget Allocated.

    Paid media requires a defined budget with daily/monthly caps.
    Insufficient budget means platforms cannot complete their learning
    phase and optimization suffers.
    """
    findings: List[AuditFinding] = []
    budget = profile.budget.monthly_marketing_budget

    if budget is None:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="budget_allocated",
            severity=FindingSeverity.HIGH.value,
            title="No marketing budget set",
            description=(
                "No monthly marketing budget is set in the business profile. "
                "Paid media requires a defined budget with daily and monthly "
                "caps. Without a budget, it is impossible to determine which "
                "platforms are feasible or to allocate spend effectively."
            ),
            recommendation=(
                "Set a monthly marketing budget. Platform minimums: "
                "Google Ads $500/mo, Meta Ads $500/mo, LinkedIn Ads "
                "$1,000/mo, TikTok Ads $500/mo. Start with 1-2 platforms "
                "and scale as results justify."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="profile.budget.monthly_marketing_budget is None",
                source_label="BusinessProfile.budget",
            )],
            tags=["budget", "blocking"],
        ))
        return findings

    if budget < 300:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="budget_allocated",
            severity=FindingSeverity.MEDIUM.value,
            title=f"Marketing budget of ${budget:.0f}/mo is below recommended minimums",
            description=(
                f"A monthly marketing budget of ${budget:.0f} is below "
                "the recommended minimum for most paid channels. Most ad "
                "platforms need at least $300-500/mo to generate enough "
                "data for optimization and meaningful results."
            ),
            recommendation=(
                f"At ${budget:.0f}/mo, focus on one platform only. "
                "Google Ads Search is the best single-channel choice for "
                "most businesses at low budgets because it captures active "
                "intent. Consider increasing budget to $500+/mo to enable "
                "platform learning phase completion."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="metric",
                value=f"${budget:.0f}/mo",
                context="Below $300/mo minimum threshold",
                source_label="BusinessProfile.budget",
            )],
            tags=["budget"],
        ))
        return findings

    # Budget is set and at least $300 -- determine feasible platforms
    feasible_platforms = []
    for platform_key, min_budget in _PLATFORM_MIN_BUDGETS.items():
        if budget >= min_budget:
            display = _PLATFORM_DISPLAY.get(platform_key, platform_key)
            feasible_platforms.append(display)

    # Filter to recommended platforms for the archetype
    recommended = _ARCHETYPE_PLATFORM_RECOMMENDATIONS.get(archetype or "", [])
    recommended_feasible = []
    for platform_key in recommended:
        min_req = _PLATFORM_MIN_BUDGETS.get(platform_key, 300.0)
        if budget >= min_req:
            recommended_feasible.append(
                _PLATFORM_DISPLAY.get(platform_key, platform_key)
            )

    channel_list = (
        ", ".join(recommended_feasible)
        if recommended_feasible
        else ", ".join(feasible_platforms[:3])
    )

    findings.append(create_finding(
        category=CATEGORY,
        subcategory="budget_allocated",
        severity=FindingSeverity.INFO.value,
        title=f"Budget of ${budget:.0f}/mo allocated",
        description=(
            f"Monthly marketing budget of ${budget:.0f} is allocated. "
            f"This is sufficient for: {channel_list}. Distribute budget "
            "based on expected ROI per channel, starting with the "
            "highest-intent platform."
        ),
        recommendation=(
            f"At ${budget:.0f}/mo, prioritize spend on: {channel_list}. "
            "Allocate 60-70% of budget to the primary platform and "
            "30-40% to the secondary. Review allocation monthly based on "
            "ROAS (return on ad spend)."
        ),
        estimated_impact=ImpactLevel.LOW.value,
        effort=EffortLevel.QUICK_WIN.value,
        evidence=[Evidence(
            evidence_type="metric",
            value=f"${budget:.0f}/mo",
            context=f"Sufficient for {len(feasible_platforms)} platform(s)",
            source_label="BusinessProfile.budget",
        )],
        tags=["budget"],
    ))

    # Warn about platforms that are under-budget
    for platform_key in recommended:
        min_req = _PLATFORM_MIN_BUDGETS.get(platform_key, 300.0)
        if budget < min_req:
            display = _PLATFORM_DISPLAY.get(platform_key, platform_key)
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="budget_allocated",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Budget below minimum for {display}",
                description=(
                    f"{display} is a recommended channel for {archetype or 'your'} "
                    f"archetype but requires a minimum of ${min_req:.0f}/mo. "
                    f"Current budget of ${budget:.0f}/mo is insufficient for "
                    "this platform."
                ),
                recommendation=(
                    f"Either increase budget to ${min_req:.0f}/mo to include "
                    f"{display}, or reallocate to platforms with lower "
                    "minimums."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.QUICK_WIN.value,
                evidence=[Evidence(
                    evidence_type="metric",
                    value=f"${budget:.0f}/mo < ${min_req:.0f}/mo minimum",
                    context=f"{display} requires higher budget",
                    source_label="Platform budget requirements",
                )],
                tags=["budget", platform_key],
            ))

    return findings


def _check_creative_assets(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 7: Creative Assets Ready.

    Ads need images, video, and copy variants before launching.
    Platform-specific requirements vary.
    """
    findings: List[AuditFinding] = []

    # Check trust profile for photo/media indicators
    has_photos = bool(profile.trust.case_studies) or bool(
        profile.trust.testimonials
    )
    has_media_evidence = False

    # Check metadata or offers for creative readiness indicators
    for offer in profile.offers:
        meta = getattr(offer, "metadata", None)
        if isinstance(meta, dict) and (
            meta.get("creative_ready") or meta.get("images") or meta.get("video")
        ):
            has_media_evidence = True
            break

    if not has_photos and not has_media_evidence:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="creative_assets",
            severity=FindingSeverity.HIGH.value,
            title="Creative assets not ready for ads",
            description=(
                "No evidence of professional creative assets (photos, "
                "videos, or ad-ready media) found in the profile. Ads need "
                "visual assets before launching -- text-only campaigns have "
                "severely limited reach on most platforms."
            ),
            recommendation=(
                "Before launching ads, prepare: 3-5 image variants per "
                "campaign, 2-3 headline variants, 2 description variants, "
                "and at least 1 video creative for video platforms"
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.SIGNIFICANT.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="No creative asset evidence in profile",
                source_label="BusinessProfile (trust, offers)",
            )],
            tags=["creative", "assets"],
        ))
    else:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="creative_assets",
            severity=FindingSeverity.INFO.value,
            title="Some creative assets detected",
            description=(
                "Evidence of existing media assets found (case studies, "
                "testimonials, or offer media). These may need adaptation "
                "for ad formats and platform-specific requirements."
            ),
            recommendation=(
                "Verify creative assets meet platform requirements: "
                "Meta Ads needs 3-5 image/video variants per ad set; "
                "Google Search Ads need compelling copy (visual assets less "
                "critical); TikTok/YouTube need vertical video content."
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="Creative asset evidence found in profile",
                source_label="BusinessProfile (trust, offers)",
            )],
            tags=["creative", "assets"],
        ))

    # Platform-specific creative advisories for recommended platforms
    recommended = _ARCHETYPE_PLATFORM_RECOMMENDATIONS.get(archetype or "", [])
    video_platforms = {"tiktok_ads", "snapchat_ads"}
    recommended_video = [p for p in recommended if p in video_platforms]

    if recommended_video:
        platform_names = ", ".join(
            _PLATFORM_DISPLAY.get(p, p) for p in recommended_video
        )
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="creative_assets",
            severity=FindingSeverity.MEDIUM.value,
            title=f"Video content needed for {platform_names}",
            description=(
                f"{platform_names} require video content for effective "
                "advertising. These platforms are algorithmically optimized "
                "for video and image-only ads underperform significantly."
            ),
            recommendation=(
                "Produce video creative for video platforms: shoot "
                "short-form vertical (9:16) video, 15-60 seconds. "
                "Authentic, lo-fi video often outperforms polished "
                "production on TikTok and Snapchat."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.SIGNIFICANT.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Video platforms recommended: {platform_names}",
                source_label="Archetype channel recommendations",
            )],
            tags=["creative", "video"],
        ))

    return findings


def _check_offer_cta(
    profile: BusinessProfile,
) -> List[AuditFinding]:
    """Check 8: Offer/CTA Defined.

    Cannot create ads without knowing what to sell or what action
    to request.  Every ad campaign needs a specific offer and CTA.
    """
    findings: List[AuditFinding] = []

    if not profile.offers:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="offer_cta",
            severity=FindingSeverity.CRITICAL.value,
            title="No offers defined",
            description=(
                "No offers are defined in the business profile. Cannot "
                "create ads without knowing what to sell. Every ad "
                "campaign needs a specific offer and CTA -- what the "
                "customer gets and what they should do next."
            ),
            recommendation=(
                "Define at least one primary offer: name, description, "
                "price range, and a clear CTA (e.g., 'Book Now', 'Get "
                "Quote', 'Buy Now', 'Start Free Trial')"
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="profile.offers is empty",
                source_label="BusinessProfile.offers",
            )],
            tags=["offer", "cta", "blocking"],
        ))
        return findings

    offers_with_cta = [o for o in profile.offers if o.primary_cta]
    offers_without_cta = [o for o in profile.offers if not o.primary_cta]

    if offers_with_cta:
        cta_list = ", ".join(
            f"{o.name} ({o.primary_cta})" for o in offers_with_cta
        )
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="offer_cta",
            severity=FindingSeverity.INFO.value,
            title="Offers and CTAs defined",
            description=(
                f"Offers with CTAs: {cta_list}. These are ready for ad "
                "campaign alignment."
            ),
            recommendation=(
                "Map each offer+CTA to a specific ad campaign. Ensure "
                "the ad copy reinforces the offer and the landing page "
                "CTA matches the ad CTA."
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Offers with CTAs: {len(offers_with_cta)}",
                source_label="BusinessProfile.offers",
            )],
            tags=["offer", "cta"],
        ))

    if offers_without_cta:
        names = ", ".join(o.name for o in offers_without_cta)
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="offer_cta",
            severity=FindingSeverity.MEDIUM.value,
            title="Offers defined but missing specific CTAs",
            description=(
                f"The following offers have no specific CTA: {names}. "
                "Ads need a clear call to action -- visitors must know "
                "exactly what to do after clicking."
            ),
            recommendation=(
                "Add a primary_cta to each offer. Use action verbs: "
                "'Book Now', 'Get Quote', 'Buy Now', 'Start Free Trial', "
                "'Schedule Consultation', 'Call Now'"
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=f"Offers without CTAs: {names}",
                source_label="BusinessProfile.offers",
            )],
            tags=["offer", "cta"],
        ))

    return findings


def _check_competitor_landscape() -> List[AuditFinding]:
    """Check 9: Competitor Ad Landscape (advisory).

    Cannot be assessed from profile data alone.  Generates an
    advisory finding recommending manual competitor research.
    """
    return [create_finding(
        category=CATEGORY,
        subcategory="competitor_landscape",
        severity=FindingSeverity.INFO.value,
        title="Research competitor ad presence before launching",
        description=(
            "Competitor ad landscape cannot be assessed from profile "
            "data alone. Before launching paid campaigns, research what "
            "competitors are advertising, their messaging, and their "
            "offers. This informs positioning and bid strategy."
        ),
        recommendation=(
            "Use Google Ads Transparency Center and Meta Ad Library to "
            "research competitor ad strategies, messaging, and offers "
            "before launching. Check: (1) Google Ads Transparency Center, "
            "(2) Meta Ad Library, (3) Search your target keywords and "
            "note who is advertising"
        ),
        estimated_impact=ImpactLevel.MEDIUM.value,
        effort=EffortLevel.MODERATE.value,
        source=FindingSource.INFERRED.value,
        evidence=[Evidence(
            evidence_type="text",
            value="Competitor ad data not available from profile",
            source_label="Advisory",
        )],
        tags=["competitor", "research", "advisory"],
    )]


def _check_compliance_precheck(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check 10: Compliance Pre-Check for Regulated Industries.

    Regulated industries face additional ad platform requirements.
    Compliance violations can get accounts suspended or banned.
    """
    findings: List[AuditFinding] = []

    industry = (profile.classification.industry or "").lower()
    vertical = (profile.classification.vertical or "").lower()
    is_regulated = profile.constraints.regulated_industry

    # Detect regulated industry from classification even if the flag
    # is not explicitly set
    detected_regulated = False
    detected_category = ""
    for keyword in _REGULATED_INDUSTRIES:
        if keyword in industry or keyword in vertical:
            detected_regulated = True
            # Map to regulatory category
            if keyword in ("healthcare", "health", "medical", "dental", "pharmacy"):
                detected_category = "healthcare"
            elif keyword in ("legal", "law", "attorney"):
                detected_category = "legal"
            elif keyword in (
                "financial", "finance", "banking", "insurance",
                "lending", "mortgage",
            ):
                detected_category = "financial"
            elif keyword in ("real_estate", "real estate", "property", "housing"):
                detected_category = "real_estate"
            else:
                detected_category = keyword
            break

    if is_regulated or detected_regulated:
        # Generate platform-specific compliance findings
        compliance_reqs: Dict[str, str] = {}

        if detected_category == "healthcare":
            compliance_reqs = {
                "meta_ads": (
                    "Meta Ads require Special Ad Category designation for "
                    "health-related advertising. Health claims are heavily "
                    "restricted -- no before/after images, no personal "
                    "health assertions."
                ),
                "google_ads": (
                    "Google Ads requires healthcare and medicines "
                    "certification for certain health-related advertising. "
                    "Clinical claims must be substantiated."
                ),
                "tiktok_ads": (
                    "TikTok restricts weight management and health "
                    "supplement advertising. AI content disclosure "
                    "required."
                ),
            }
        elif detected_category == "legal":
            compliance_reqs = {
                "google_ads": (
                    "Google Ads requires lawyer advertising certification "
                    "in some jurisdictions. State bar rules may apply to "
                    "ad content."
                ),
                "meta_ads": (
                    "Legal service ads on Meta may be subject to Special "
                    "Ad Category requirements depending on the practice "
                    "area."
                ),
            }
        elif detected_category == "financial":
            compliance_reqs = {
                "google_ads": (
                    "Financial service ads on Google require disclosures "
                    "and may need platform certification. APR and fee "
                    "disclosures are mandatory."
                ),
                "meta_ads": (
                    "Meta Ads require Special Ad Category for credit "
                    "products. Financial claims must include required "
                    "regulatory disclosures."
                ),
                "linkedin_ads": (
                    "LinkedIn requires substantiation for financial "
                    "performance claims in B2B financial advertising."
                ),
            }
        elif detected_category == "real_estate":
            compliance_reqs = {
                "meta_ads": (
                    "Meta Ads require Special Ad Category for "
                    "housing-related advertising. Targeting restrictions "
                    "apply -- cannot target by age, gender, or zip code "
                    "for housing ads."
                ),
                "google_ads": (
                    "Real estate ads on Google must comply with Fair "
                    "Housing Act requirements. Equal Opportunity Housing "
                    "logo may be required."
                ),
            }
        else:
            compliance_reqs = {
                "all": (
                    f"Industry '{detected_category}' may have platform-"
                    "specific advertising restrictions. Review each "
                    "platform's ad policies before launching."
                ),
            }

        for platform_key, requirement in compliance_reqs.items():
            display = _PLATFORM_DISPLAY.get(platform_key, platform_key)
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="compliance_precheck",
                severity=FindingSeverity.HIGH.value,
                title=f"Compliance requirement: {display} ({detected_category})",
                description=requirement,
                recommendation=(
                    "Before launching, review platform-specific ad policies "
                    "for your industry. See harness/references/ for full "
                    "policy references. Non-compliance can result in ad "
                    "rejection, account suspension, or permanent ban."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                evidence=[Evidence(
                    evidence_type="checklist_item",
                    value=(
                        f"Regulated industry: {detected_category}, "
                        f"Platform: {display}"
                    ),
                    source_label="BusinessProfile.constraints / classification",
                )],
                tags=["compliance", "regulated", detected_category, platform_key],
            ))
    else:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="compliance_precheck",
            severity=FindingSeverity.INFO.value,
            title="No special regulatory requirements detected",
            description=(
                "No regulated industry designation was detected for this "
                "business. Standard ad platform policies still apply -- "
                "all ads must comply with platform terms of service and "
                "applicable laws (FTC, GDPR, CAN-SPAM, COPPA)."
            ),
            recommendation=(
                "Even without industry-specific regulations, review "
                "platform ad policies before launching. FTC disclosure "
                "requirements, GDPR consent rules, and platform-specific "
                "content policies apply to all advertisers."
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="regulated_industry=False, no regulated keywords in classification",
                source_label="BusinessProfile.constraints / classification",
            )],
            tags=["compliance"],
        ))

    return findings


def _check_platform_readiness(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]],
    archetype: Optional[str],
    prior_findings: List[AuditFinding],
) -> List[AuditFinding]:
    """Check 11: Platform-Specific Readiness Assessment.

    Generates a summary finding per relevant platform by checking
    prerequisites: account, tracking, budget, creative, landing page,
    and compliance status.
    """
    findings: List[AuditFinding] = []

    recommended = _ARCHETYPE_PLATFORM_RECOMMENDATIONS.get(archetype or "", [])
    if not recommended:
        # Fallback: assess platforms present in channels
        recommended = [
            ch.platform.lower()
            for ch in profile.channels
            if ch.platform.lower() in _AD_PLATFORMS
        ]
    if not recommended:
        recommended = ["google_ads", "meta_ads"]

    # Build a lookup of existing findings by subcategory and platform
    # to determine what has been checked and what status it has
    ad_channels = {
        ch.platform.lower(): ch
        for ch in profile.channels
        if ch.platform.lower() in _AD_PLATFORMS
    }

    budget = profile.budget.monthly_marketing_budget
    has_offers = bool(profile.offers)
    has_cta = any(o.primary_cta for o in profile.offers) if has_offers else False
    has_personas = bool(profile.personas)

    # Check for compliance findings in prior results
    compliance_findings = [
        f for f in prior_findings
        if f.subcategory == "compliance_precheck"
        and f.severity in (FindingSeverity.HIGH.value, FindingSeverity.CRITICAL.value)
    ]
    has_compliance_issues = bool(compliance_findings)

    # Check for creative asset findings
    creative_issues = [
        f for f in prior_findings
        if f.subcategory == "creative_assets"
        and f.severity in (FindingSeverity.HIGH.value, FindingSeverity.CRITICAL.value)
    ]
    has_creative_issues = bool(creative_issues)

    # Check for landing page findings
    lp_issues = [
        f for f in prior_findings
        if f.subcategory == "landing_pages"
        and f.severity in (FindingSeverity.HIGH.value, FindingSeverity.CRITICAL.value)
    ]
    has_lp_issues = bool(lp_issues)

    # Check for tracking findings
    tracking_issues = [
        f for f in prior_findings
        if f.subcategory == "conversion_tracking"
        and f.severity in (FindingSeverity.HIGH.value, FindingSeverity.CRITICAL.value)
    ]
    has_tracking_issues = bool(tracking_issues)

    for idx, platform_key in enumerate(recommended):
        display = _PLATFORM_DISPLAY.get(platform_key, platform_key)
        prereqs = get_platform_prerequisites(platform_key, archetype or "")

        # Assess each prerequisite dimension
        status_items: Dict[str, bool] = {}
        missing_items: List[str] = []

        # Account
        channel = ad_channels.get(platform_key)
        account_ready = channel is not None and channel.is_connected
        status_items["Account"] = account_ready
        if not account_ready:
            missing_items.append("Ad account")

        # Tracking
        tracking_ready = not has_tracking_issues
        # Also check connected_data for pixel status
        if connected_data:
            pixel_data = connected_data.get("pixel_verification", {})
            if platform_key in pixel_data:
                pv = pixel_data[platform_key]
                tracking_ready = (
                    pv.get("verified", False) if isinstance(pv, dict) else bool(pv)
                )
        status_items["Tracking"] = tracking_ready
        if not tracking_ready:
            missing_items.append("Conversion tracking")

        # Budget
        min_budget = _PLATFORM_MIN_BUDGETS.get(platform_key, 300.0)
        budget_ready = budget is not None and budget >= min_budget
        status_items["Budget"] = budget_ready
        if not budget_ready:
            missing_items.append(f"Budget (min ${min_budget:.0f}/mo)")

        # Creative
        creative_ready = not has_creative_issues
        status_items["Creative"] = creative_ready
        if not creative_ready:
            missing_items.append("Creative assets")

        # Landing page
        lp_ready = not has_lp_issues
        status_items["Landing page"] = lp_ready
        if not lp_ready:
            missing_items.append("Landing pages")

        # Compliance
        # Check for platform-specific compliance issues
        platform_compliance_issues = [
            f for f in compliance_findings
            if platform_key in getattr(f, "tags", [])
        ]
        compliance_ready = not bool(platform_compliance_issues)
        status_items["Compliance"] = compliance_ready
        if not compliance_ready:
            missing_items.append("Compliance requirements")

        # Determine overall readiness
        ready_count = sum(1 for v in status_items.values() if v)
        total_count = len(status_items)
        missing_count = total_count - ready_count

        if missing_count == 0:
            status_label = "READY"
            severity = FindingSeverity.INFO.value
        elif missing_count <= 2:
            status_label = "NEARLY READY"
            severity = FindingSeverity.MEDIUM.value
        else:
            status_label = "NOT READY"
            severity = FindingSeverity.HIGH.value

        # Severity also depends on platform priority for the archetype
        # Higher-priority platforms get higher severity when not ready
        if idx == 0 and severity == FindingSeverity.MEDIUM.value:
            severity = FindingSeverity.HIGH.value

        status_summary = ", ".join(
            f"{k}: {'Y' if v else 'N'}" for k, v in status_items.items()
        )

        if missing_items:
            missing_str = ", ".join(missing_items)
            desc = (
                f"{display} Readiness: {status_label} "
                f"({ready_count}/{total_count} prerequisites met). "
                f"Missing: {missing_str}."
            )
        else:
            desc = (
                f"{display} Readiness: {status_label} "
                f"({ready_count}/{total_count} prerequisites met). "
                "All core prerequisites are in place."
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="platform_readiness",
            severity=severity,
            title=f"{display} Readiness: {status_label}",
            description=desc,
            recommendation=(
                f"Address missing prerequisites for {display} before "
                f"launching: {', '.join(missing_items)}"
                if missing_items
                else (
                    f"{display} prerequisites are met. Proceed with "
                    "campaign planning: define campaign structure, create "
                    "ad copy, set targeting, and prepare a launch timeline."
                )
            ),
            estimated_impact=(
                ImpactLevel.HIGH.value
                if idx < 2
                else ImpactLevel.MEDIUM.value
            ),
            effort=(
                EffortLevel.QUICK_WIN.value
                if missing_count == 0
                else (
                    EffortLevel.MODERATE.value
                    if missing_count <= 2
                    else EffortLevel.SIGNIFICANT.value
                )
            ),
            evidence=[Evidence(
                evidence_type="checklist_item",
                value=status_summary,
                source_label=f"{display} readiness assessment",
            )],
            tags=["platform_readiness", platform_key],
            metadata={
                "platform": platform_key,
                "status": status_label,
                "ready_count": ready_count,
                "total_count": total_count,
                "missing_items": missing_items,
                "status_items": {k: v for k, v in status_items.items()},
            },
        ))

    return findings


# ============================================================================
# Main audit function
# ============================================================================


def audit_paid_media_readiness(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run the full paid media readiness audit.

    Evaluates whether a business has the prerequisites in place to run
    paid advertising effectively.  Returns a list of ``AuditFinding``
    objects covering 11 check areas.

    Parameters
    ----------
    profile:
        The ``BusinessProfile`` to audit.
    connected_data:
        Optional dictionary that may include:

        - ``conversion_events_configured`` (bool): whether conversion
          events are set up in analytics.
        - ``pixel_verification`` (dict): mapping of platform key to
          verification status (bool or dict with ``verified`` key).
        - ``campaign_performance`` (dict): historical campaign data.

    Returns
    -------
    List[AuditFinding]
        All findings from all 11 checks, ordered by check number.
    """
    archetype = (
        profile.classification.archetype
        if profile.classification
        else None
    )

    findings: List[AuditFinding] = []

    # Check 1: Conversion Tracking
    findings.extend(_check_conversion_tracking(profile, connected_data))

    # Check 2: Landing Pages
    findings.extend(_check_landing_pages(profile, archetype))

    # Check 3: Ad Account Status
    findings.extend(_check_ad_account_status(profile, archetype))

    # Check 4: Pixel/Tag Status
    findings.extend(_check_pixel_tag_status(profile, connected_data, archetype))

    # Check 5: Audience Definitions
    findings.extend(_check_audience_definitions(profile))

    # Check 6: Budget Allocated
    findings.extend(_check_budget_allocated(profile, archetype))

    # Check 7: Creative Assets
    findings.extend(_check_creative_assets(profile, archetype))

    # Check 8: Offer/CTA Defined
    findings.extend(_check_offer_cta(profile))

    # Check 9: Competitor Ad Landscape
    findings.extend(_check_competitor_landscape())

    # Check 10: Compliance Pre-Check
    findings.extend(_check_compliance_precheck(profile, archetype))

    # Check 11: Platform-Specific Readiness (uses results from above)
    findings.extend(_check_platform_readiness(
        profile, connected_data, archetype, findings,
    ))

    return findings


# ============================================================================
# Scoring
# ============================================================================


def score_paid_media_readiness(findings: List[AuditFinding]) -> float:
    """Compute a 0-100 paid media readiness score from findings.

    Scoring formula::

        penalty = sum(severity_penalty * weight) for each finding
        score   = max(0, min(100, 100 - penalty))

    Conversion tracking and landing page findings are weighted 2x
    because they are the foundational prerequisites -- everything else
    is built on top of them.

    Severity penalties mirror ``compute_category_scorecard``::

        CRITICAL -> 25, HIGH -> 15, MEDIUM -> 8, LOW -> 3, INFO -> 0

    Parameters
    ----------
    findings:
        The list produced by ``audit_paid_media_readiness``.

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

    # Subcategories that receive 2x weight
    double_weight_subs = {"conversion_tracking", "landing_pages"}

    total_penalty = 0.0
    for f in findings:
        base = severity_penalty.get(f.severity, 0)
        weight = 2 if getattr(f, "subcategory", None) in double_weight_subs else 1
        total_penalty += base * weight

    return round(max(0.0, min(100.0, 100.0 - total_penalty)), 1)
