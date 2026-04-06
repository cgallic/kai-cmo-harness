"""Creative and asset readiness audit engine for the Kai Marketing OS.

Evaluates a business's available marketing assets -- photography, video,
testimonial content, case study materials, brand assets -- against the
requirements of its active and planned marketing channels.  Identifies
asset gaps that would block or degrade specific channel executions.

If a business wants to run Meta Ads but has no product photos, that's a
blocker.  If they want social media presence but have no team photos or
behind-the-scenes content, that's a gap.  This engine maps what exists
against what each channel and campaign type needs.

Usage::

    from kai.audits.creative_readiness import (
        audit_creative_readiness,
        score_creative_readiness,
        map_assets_to_channels,
    )
    findings = audit_creative_readiness(profile, connected_data=live_data)
    score = score_creative_readiness(findings)
    asset_map = map_assets_to_channels("local-service")
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

CATEGORY = "creative_readiness"

_LOCAL_SERVICE_ARCHETYPES = {"local-service", "multi-location"}
_ECOMMERCE_ARCHETYPES = {"ecommerce", "d2c", "marketplace"}
_PROFESSIONAL_ARCHETYPES = {"professional-services", "saas", "agency"}

# Social-media channel platform names (normalized lowercase)
_SOCIAL_PLATFORMS = {
    "facebook", "instagram", "tiktok", "linkedin", "twitter",
    "x", "youtube", "pinterest", "snapchat",
}

# Photo-related keywords in trust signal content or raw notes
_PHOTO_KEYWORDS = [
    "photo", "photograph", "image", "headshot", "portfolio",
    "gallery", "before/after", "before and after", "picture",
    "shot", "visual", "imagery",
]

# Video-related keywords
_VIDEO_KEYWORDS = [
    "video", "youtube", "tiktok", "reel", "reels", "clip",
    "footage", "walkthrough", "testimonial video", "demo video",
    "explainer", "vlog", "webinar recording",
]

# Brand-color keywords in brand voice or metadata
_COLOR_KEYWORDS = [
    "color", "colour", "hex", "rgb", "palette", "brand color",
    "brand colour", "primary color", "accent color", "#",
]


# ============================================================================
# Helper: archetype accessor
# ============================================================================

def _get_archetype(profile: BusinessProfile) -> Optional[str]:
    """Return the profile archetype, normalized to lowercase."""
    arch = getattr(profile.classification, "archetype", None)
    return arch.lower().strip() if arch else None


# ============================================================================
# Helper: search text fields for keywords
# ============================================================================

def _profile_text_contains(profile: BusinessProfile, keywords: List[str]) -> bool:
    """Search trust signals, brand voice, channels, raw notes for keywords."""
    searchable: List[str] = []

    # Trust signals
    for t in profile.trust.testimonials:
        searchable.append(t.content or "")
        searchable.append(t.title or "")
    for cs in profile.trust.case_studies:
        searchable.append(cs.content or "")
        searchable.append(cs.title or "")

    # Certifications, awards
    searchable.extend(profile.trust.certifications)
    searchable.extend(profile.trust.awards)

    # Brand voice
    searchable.extend(profile.brand_voice.writing_samples)
    searchable.extend(profile.brand_voice.approved_messaging_blocks)
    if profile.brand_voice.competitor_differentiation:
        searchable.append(profile.brand_voice.competitor_differentiation)

    # Channel notes
    for ch in profile.channels:
        if ch.notes:
            searchable.append(ch.notes)
        if ch.url:
            searchable.append(ch.url)

    # Raw notes
    if profile.raw_notes:
        searchable.append(profile.raw_notes)

    # Metadata (string values only)
    for v in profile.metadata.values():
        if isinstance(v, str):
            searchable.append(v)

    combined = " ".join(searchable).lower()
    return any(kw.lower() in combined for kw in keywords)


def _connected_has_asset_type(
    connected_data: Optional[Dict[str, Any]],
    asset_key: str,
) -> bool:
    """Check connected_data for a specific asset type indicator."""
    if not connected_data:
        return False
    assets = connected_data.get("assets") or connected_data.get("creative_assets") or {}
    if isinstance(assets, dict):
        val = assets.get(asset_key)
        if isinstance(val, bool):
            return val
        if isinstance(val, (list, dict)):
            return len(val) > 0
        if isinstance(val, (int, float)):
            return val > 0
    return False


def _get_social_channels(profile: BusinessProfile) -> List[str]:
    """Return list of active social platform names from the profile."""
    result: List[str] = []
    for ch in profile.channels:
        platform = (ch.platform or "").lower().strip()
        if platform in _SOCIAL_PLATFORMS:
            if ch.is_active or ch.url:
                result.append(platform)
    return result


def _parse_team_size(team_size: Optional[str]) -> Optional[int]:
    """Parse team_size string into a minimum number.

    Handles formats like "1-5", "6-20", "21-50", "50+", "3".
    Returns the lower bound or None if unparseable.
    """
    if not team_size:
        return None
    cleaned = team_size.strip().replace("+", "")
    if "-" in cleaned:
        parts = cleaned.split("-")
        try:
            return int(parts[0].strip())
        except (ValueError, IndexError):
            return None
    try:
        return int(cleaned)
    except ValueError:
        return None


# ============================================================================
# Asset-to-channel mapping
# ============================================================================

def map_assets_to_channels(archetype: str) -> Dict[str, List[str]]:
    """Return a mapping of asset types to channels that require them.

    The mapping is archetype-dependent: local-service businesses need
    different assets than ecommerce or professional-services firms.

    Parameters
    ----------
    archetype:
        Business archetype (e.g., "local-service", "ecommerce",
        "professional-services").

    Returns
    -------
    Dict[str, List[str]]
        Keys are asset types, values are lists of channels requiring
        that asset.
    """
    arch = (archetype or "").lower().strip()

    # Base mapping common to all archetypes
    mapping: Dict[str, List[str]] = {
        "logo": [
            "website", "meta_ads", "google_ads", "linkedin", "email",
            "social_media", "print",
        ],
        "brand_colors": [
            "website", "meta_ads", "social_media", "email",
            "landing_pages", "print",
        ],
        "testimonial_content": [
            "website", "meta_ads", "landing_pages", "email",
            "google_ads", "social_media",
        ],
        "video": [
            "tiktok", "youtube", "meta_ads_video", "instagram_reels",
            "website", "linkedin",
        ],
        "team_headshots": [
            "website", "linkedin", "email_signatures",
            "google_business_profile",
        ],
    }

    if arch in _LOCAL_SERVICE_ARCHETYPES:
        mapping["project_photography"] = [
            "meta_ads", "instagram", "google_business_profile",
            "website", "social_media", "nextdoor",
        ]
        mapping["before_after_photos"] = [
            "meta_ads", "instagram", "google_business_profile",
            "website", "social_media", "landing_pages",
        ]
        mapping["vehicle_branding_photos"] = [
            "social_media", "google_business_profile", "website",
        ]
        mapping["action_shots"] = [
            "social_media", "meta_ads", "website",
            "google_business_profile",
        ]
        mapping["case_study_content"] = [
            "website", "landing_pages", "email", "social_media",
        ]

    elif arch in _ECOMMERCE_ARCHETYPES:
        mapping["product_photography"] = [
            "meta_ads", "google_shopping", "instagram", "website",
            "amazon", "tiktok_shop", "pinterest",
        ]
        mapping["lifestyle_photography"] = [
            "meta_ads", "instagram", "pinterest", "website",
            "social_media",
        ]
        mapping["unboxing_photos"] = [
            "social_media", "instagram", "tiktok", "youtube",
        ]
        mapping["product_video"] = [
            "tiktok", "youtube", "meta_ads_video", "instagram_reels",
            "website", "amazon",
        ]
        mapping["customer_success_stories"] = [
            "website", "email", "landing_pages", "social_media",
        ]

    elif arch in _PROFESSIONAL_ARCHETYPES:
        mapping["professional_headshots"] = [
            "website", "linkedin", "email_signatures",
            "google_business_profile", "speaking_engagements",
        ]
        mapping["office_workspace_photos"] = [
            "website", "google_business_profile", "social_media",
        ]
        mapping["event_speaking_photos"] = [
            "linkedin", "website", "social_media",
        ]
        mapping["case_study_content"] = [
            "website", "landing_pages", "email", "linkedin",
            "sales_collateral",
        ]
        mapping["thought_leadership_video"] = [
            "youtube", "linkedin", "website", "webinars",
        ]

    else:
        # Generic fallback
        mapping["product_service_photography"] = [
            "meta_ads", "instagram", "website", "social_media",
            "google_ads",
        ]
        mapping["case_study_content"] = [
            "website", "landing_pages", "email", "social_media",
        ]

    return mapping


# ============================================================================
# Check 1: Professional Photography
# ============================================================================

def _check_professional_photography(
    profile: BusinessProfile,
    archetype: Optional[str],
    connected_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Assess professional photography availability."""
    findings: List[AuditFinding] = []

    has_logo = profile.identity.logo_url is not None
    has_photo_signals = _profile_text_contains(profile, _PHOTO_KEYWORDS)
    has_connected_photos = _connected_has_asset_type(connected_data, "photography")

    if has_connected_photos or (has_logo and has_photo_signals):
        # Photography indicators exist -- no high-severity finding needed
        return findings

    if not has_logo and not has_photo_signals and not has_connected_photos:
        # No photography indicators at all
        base_description = (
            "No professional photography indicators -- professional images "
            "are essential for ads, social media, and website credibility."
        )

        if archetype and archetype in _LOCAL_SERVICE_ARCHETYPES:
            description = (
                f"{base_description} Before/after project photos, team photos, "
                "and equipment/truck photos are the minimum."
            )
            recommendation = (
                "Invest in: (1) Professional headshots for key team, "
                "(2) High-quality before/after project photos, "
                "(3) Branded truck/vehicle photos, "
                "(4) Action shots of team at work"
            )
        elif archetype and archetype in _ECOMMERCE_ARCHETYPES:
            description = (
                f"{base_description} Product photography is non-negotiable "
                "-- lifestyle and white-background shots needed."
            )
            recommendation = (
                "Invest in: (1) White-background product shots, "
                "(2) Lifestyle/in-use photography, "
                "(3) Package/unboxing photos, "
                "(4) Detail/texture close-ups"
            )
        elif archetype and archetype in _PROFESSIONAL_ARCHETYPES:
            description = (
                f"{base_description} Professional headshots and office/team "
                "photos establish authority."
            )
            recommendation = (
                "Invest in: (1) Professional headshots for all public-facing team, "
                "(2) Office/workspace photos, "
                "(3) Team collaboration photos, "
                "(4) Event/speaking photos"
            )
        else:
            description = base_description
            recommendation = (
                "Invest in professional photography: headshots, "
                "product/service photos, and team photos at minimum"
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="professional_photography",
            severity=FindingSeverity.HIGH.value,
            title="No professional photography indicators",
            description=description,
            recommendation=recommendation,
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.SIGNIFICANT.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="missing_data",
                    value="No logo_url and no photo-related trust signals found",
                    context="Professional photography is a prerequisite for most marketing channels",
                    source_label="Profile data analysis",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "photography", "blocker"],
        ))

    return findings


# ============================================================================
# Check 2: Logo Quality
# ============================================================================

def _check_logo_quality(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Assess logo availability and format readiness."""
    findings: List[AuditFinding] = []

    if profile.identity.logo_url is None:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="logo",
            severity=FindingSeverity.MEDIUM.value,
            title="No logo URL on file",
            description=(
                "No logo URL on file -- the logo is the core brand asset "
                "needed across all channels."
            ),
            recommendation=(
                "Provide logo in multiple formats: SVG/vector, "
                "transparent PNG (1000x1000+), and favicon (32x32, 180x180)"
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="missing_data",
                    value="identity.logo_url is None",
                    context="Logo is required for website, ads, social profiles, and email",
                    source_label="BusinessProfile.identity",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "logo", "brand_asset"],
        ))
    else:
        # Logo exists -- provide advisory on format availability
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="logo",
            severity=FindingSeverity.INFO.value,
            title="Ensure logo is available in all required formats",
            description=(
                "Ensure logo is available in: high-res PNG (transparent "
                "background), square format (for social profiles), horizontal "
                "format (for website header), and favicon size."
            ),
            recommendation=(
                "Provide logo in multiple formats: SVG/vector, "
                "transparent PNG (1000x1000+), and favicon (32x32, 180x180)"
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"Logo URL on file: {profile.identity.logo_url}",
                    context="Verify that all format variants exist",
                    source_label="BusinessProfile.identity",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "logo", "advisory"],
        ))

    return findings


# ============================================================================
# Check 3: Brand Colors Defined
# ============================================================================

def _check_brand_colors(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Check whether brand colors are defined."""
    findings: List[AuditFinding] = []

    # Search brand voice notes, personality traits, metadata, raw notes
    searchable: List[str] = []
    searchable.extend(profile.brand_voice.tone_descriptors)
    searchable.extend(profile.brand_voice.personality_traits)
    searchable.extend(profile.brand_voice.approved_messaging_blocks)
    if profile.brand_voice.competitor_differentiation:
        searchable.append(profile.brand_voice.competitor_differentiation)
    if profile.constraints.brand_voice_notes:
        searchable.append(profile.constraints.brand_voice_notes)
    if profile.raw_notes:
        searchable.append(profile.raw_notes)
    for v in profile.metadata.values():
        if isinstance(v, str):
            searchable.append(v)

    combined = " ".join(searchable).lower()
    has_colors = any(kw.lower() in combined for kw in _COLOR_KEYWORDS)

    if not has_colors:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="brand_colors",
            severity=FindingSeverity.MEDIUM.value,
            title="Brand colors not defined",
            description=(
                "Brand colors not defined -- consistent color usage across "
                "all marketing materials builds recognition."
            ),
            recommendation=(
                "Define: primary brand color, secondary color, accent color, "
                "and background color. Provide hex codes."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="missing_data",
                    value="No brand color information found in profile",
                    context="Brand colors are needed for website, ads, social media, and email templates",
                    source_label="Brand voice and metadata analysis",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "brand_colors", "brand_asset"],
        ))

    return findings


# ============================================================================
# Check 4: Testimonial Content Available for Marketing Use
# ============================================================================

def _check_testimonial_content(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Assess testimonial content availability and quality for marketing use."""
    findings: List[AuditFinding] = []

    testimonials = profile.trust.testimonials

    if not testimonials:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="testimonial_content",
            severity=FindingSeverity.HIGH.value,
            title="No testimonial content available",
            description=(
                "No testimonial content available -- this blocks social proof "
                "in ads, landing pages, and email."
            ),
            recommendation=(
                "Collect written testimonials with: customer name, location, "
                "specific result, and permission to use in marketing"
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="missing_data",
                    value="profile.trust.testimonials is empty",
                    context="Testimonials are needed for ads, landing pages, email, and social proof",
                    source_label="BusinessProfile.trust",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "testimonials", "social_proof", "blocker"],
        ))
        return findings

    # Testimonials exist -- check for attribution quality
    lacking_attribution = 0
    for t in testimonials:
        source = t.source or ""
        title = t.title or ""
        content = t.content or ""
        # A well-attributed testimonial has a name or source identifier
        combined_meta = f"{source} {title}".strip()
        if not combined_meta or combined_meta.lower() in ("anonymous", "customer", "client"):
            lacking_attribution += 1

    if lacking_attribution > 0 and lacking_attribution == len(testimonials):
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="testimonial_content",
            severity=FindingSeverity.MEDIUM.value,
            title="Testimonials lack attribution",
            description=(
                "Testimonials exist but lack attribution -- named testimonials "
                "are 3x more credible than anonymous ones."
            ),
            recommendation=(
                "Collect written testimonials with: customer name, location, "
                "specific result, and permission to use in marketing"
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"{lacking_attribution} of {len(testimonials)} testimonials lack named attribution",
                    context="Named testimonials convert significantly better than anonymous quotes",
                    source_label="Testimonial quality analysis",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "testimonials", "social_proof", "quality"],
        ))
    elif lacking_attribution > 0:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="testimonial_content",
            severity=FindingSeverity.LOW.value,
            title="Some testimonials lack attribution",
            description=(
                f"{lacking_attribution} of {len(testimonials)} testimonials "
                "lack named attribution -- named testimonials are 3x more "
                "credible than anonymous ones."
            ),
            recommendation=(
                "Follow up with customers who left anonymous testimonials "
                "to get permission for named attribution"
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"{lacking_attribution} of {len(testimonials)} testimonials lack named attribution",
                    context="Improving attribution on existing testimonials is a quick win",
                    source_label="Testimonial quality analysis",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "testimonials", "social_proof"],
        ))

    return findings


# ============================================================================
# Check 5: Case Study Content Available
# ============================================================================

def _check_case_study_content(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Assess case study availability and coverage."""
    findings: List[AuditFinding] = []

    case_studies = profile.trust.case_studies
    count = len(case_studies)

    if count == 0:
        if archetype and archetype in _PROFESSIONAL_ARCHETYPES:
            severity = FindingSeverity.HIGH.value
            title = "No case study content"
            description = (
                "No case study content -- case studies are the primary "
                "conversion asset for professional services."
            )
            impact = ImpactLevel.HIGH.value
        elif archetype and archetype in _LOCAL_SERVICE_ARCHETYPES:
            severity = FindingSeverity.MEDIUM.value
            title = "No before/after or project showcase content"
            description = (
                "No before/after or project showcase content documented."
            )
            impact = ImpactLevel.MEDIUM.value
        elif archetype and archetype in _ECOMMERCE_ARCHETYPES:
            severity = FindingSeverity.MEDIUM.value
            title = "No customer success stories documented"
            description = (
                "No customer success stories documented."
            )
            impact = ImpactLevel.MEDIUM.value
        else:
            severity = FindingSeverity.MEDIUM.value
            title = "No case study content"
            description = (
                "No case study or success story content documented."
            )
            impact = ImpactLevel.MEDIUM.value

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="case_studies",
            severity=severity,
            title=title,
            description=description,
            recommendation=(
                "Document at least 3 case studies covering different service "
                "types or customer profiles. Include: problem, solution, "
                "specific measurable results, and customer quote."
            ),
            estimated_impact=impact,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="missing_data",
                    value="profile.trust.case_studies is empty",
                    context="Case studies are high-conversion content assets",
                    source_label="BusinessProfile.trust",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "case_studies", "social_proof"],
        ))

    elif count < 3:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="case_studies",
            severity=FindingSeverity.LOW.value,
            title=f"Only {count} case stud{'y' if count == 1 else 'ies'}",
            description=(
                f"Only {count} case stud{'y' if count == 1 else 'ies'} -- "
                "expand coverage to different service types and customer profiles."
            ),
            recommendation=(
                "Expand to at least 3 case studies covering different service "
                "categories, customer sizes, or use cases"
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"{count} case stud{'y' if count == 1 else 'ies'} on file",
                    context="Three or more case studies provide better category coverage",
                    source_label="BusinessProfile.trust",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "case_studies"],
        ))

    return findings


# ============================================================================
# Check 6: Video Content Available
# ============================================================================

def _check_video_content(
    profile: BusinessProfile,
    archetype: Optional[str],
    connected_data: Optional[Dict[str, Any]],
) -> List[AuditFinding]:
    """Assess video content availability."""
    findings: List[AuditFinding] = []

    has_video_signals = _profile_text_contains(profile, _VIDEO_KEYWORDS)
    has_connected_video = _connected_has_asset_type(connected_data, "video")

    # Check channel presence for video platforms
    has_video_channel = False
    for ch in profile.channels:
        platform = (ch.platform or "").lower()
        if platform in ("youtube", "tiktok", "vimeo"):
            if ch.is_active:
                has_video_channel = True
                break

    if has_video_signals or has_connected_video or has_video_channel:
        return findings

    # No video content indicators
    recommendation = (
        "Start with: (1) 60-second brand overview video, "
        "(2) Customer testimonial videos, "
        "(3) Service/product demo videos"
    )

    if archetype and archetype in _ECOMMERCE_ARCHETYPES:
        severity = FindingSeverity.HIGH.value
        description = (
            "No video content -- video drives 80% higher conversion rates "
            "for product pages."
        )
        impact = ImpactLevel.HIGH.value
    elif archetype and archetype in _LOCAL_SERVICE_ARCHETYPES:
        severity = FindingSeverity.MEDIUM.value
        description = (
            "No video content -- short project walkthrough and testimonial "
            "videos are high-impact."
        )
        impact = ImpactLevel.MEDIUM.value
    elif archetype and archetype in _PROFESSIONAL_ARCHETYPES:
        severity = FindingSeverity.MEDIUM.value
        description = (
            "No video content -- thought leadership and explainer videos "
            "build authority."
        )
        impact = ImpactLevel.MEDIUM.value
    else:
        severity = FindingSeverity.MEDIUM.value
        description = (
            "No video content indicators found -- video content "
            "significantly improves engagement across all channels."
        )
        impact = ImpactLevel.MEDIUM.value

    findings.append(create_finding(
        category=CATEGORY,
        subcategory="video_content",
        severity=severity,
        title="No video content available",
        description=description,
        recommendation=recommendation,
        estimated_impact=impact,
        effort=EffortLevel.SIGNIFICANT.value,
        source=FindingSource.STATIC.value,
        evidence=[
            Evidence(
                evidence_type="missing_data",
                value="No video content indicators in profile, channels, or connected data",
                context="Video is required for TikTok, YouTube, video ads, and product pages",
                source_label="Profile and channel analysis",
            ),
        ],
        archetype_relevance=[archetype] if archetype else [],
        tags=["creative", "video", "content"],
    ))

    return findings


# ============================================================================
# Check 7: Before/After Documentation
# ============================================================================

def _check_before_after_documentation(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Assess before/after project documentation for applicable archetypes."""
    findings: List[AuditFinding] = []

    if not archetype:
        return findings

    before_after_keywords = [
        "before/after", "before and after", "before & after",
        "transformation", "project photo", "project gallery",
        "project portfolio", "completed project",
    ]

    has_ba_evidence = _profile_text_contains(profile, before_after_keywords)

    if archetype in _LOCAL_SERVICE_ARCHETYPES:
        if not has_ba_evidence:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="before_after",
                severity=FindingSeverity.MEDIUM.value,
                title="No before/after project documentation",
                description=(
                    "No before/after project documentation -- this is the most "
                    "powerful social proof format for service businesses."
                ),
                recommendation=(
                    "Photograph every project: (1) Before photo, "
                    "(2) During work photo, (3) After completion photo. "
                    "Store in a shared album for marketing use."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.ONGOING.value,
                source=FindingSource.STATIC.value,
                evidence=[
                    Evidence(
                        evidence_type="missing_data",
                        value="No before/after evidence in trust signals or profile data",
                        context="Before/after photos drive the highest engagement for service businesses",
                        source_label="Profile trust signal analysis",
                    ),
                ],
                archetype_relevance=[archetype],
                tags=["creative", "before_after", "photography", "social_proof"],
            ))

    elif archetype in _ECOMMERCE_ARCHETYPES:
        # Advisory for ecommerce -- before/after depends on product type,
        # and some platforms restrict before/after imagery (e.g., Meta Ads
        # for weight loss products, Pinterest bans all weight loss ads).
        if not has_ba_evidence:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="before_after",
                severity=FindingSeverity.INFO.value,
                title="Consider before/after content if product allows",
                description=(
                    "Before/after transformation content is high-impact for "
                    "applicable product categories. Check platform ad policies "
                    "before using -- Meta and Pinterest restrict before/after "
                    "imagery for health and wellness products."
                ),
                recommendation=(
                    "If your product produces visible transformations, document "
                    "customer results with their permission. Verify platform ad "
                    "policies before using in paid campaigns."
                ),
                estimated_impact=ImpactLevel.LOW.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.STATIC.value,
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="No before/after content found; applicability depends on product type",
                        context="Some ad platforms restrict before/after imagery",
                        source_label="Profile analysis",
                    ),
                ],
                archetype_relevance=[archetype],
                tags=["creative", "before_after", "advisory"],
            ))

    return findings


# ============================================================================
# Check 8: Team Headshots
# ============================================================================

def _check_team_headshots(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Assess team headshot availability for multi-person teams."""
    findings: List[AuditFinding] = []

    team_size_min = _parse_team_size(profile.trust.team_size)

    # Only flag if team has 2+ people
    if team_size_min is None or team_size_min < 2:
        return findings

    headshot_keywords = [
        "headshot", "team photo", "team picture", "staff photo",
        "portrait", "professional photo",
    ]
    has_headshot_evidence = _profile_text_contains(profile, headshot_keywords)

    if not has_headshot_evidence:
        base_description = (
            "Team headshots not available -- people buy from people, "
            "not faceless companies."
        )

        if archetype and archetype in _LOCAL_SERVICE_ARCHETYPES:
            description = (
                f"{base_description} Customers want to know who's coming "
                "to their home."
            )
        elif archetype and archetype in _PROFESSIONAL_ARCHETYPES:
            description = (
                f"{base_description} Headshots on the website and LinkedIn "
                "are essential for credibility."
            )
        else:
            description = base_description

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="team_headshots",
            severity=FindingSeverity.MEDIUM.value,
            title="Team headshots not available",
            description=description,
            recommendation=(
                "Schedule professional headshots for all customer-facing "
                "team members"
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"Team size indicates {team_size_min}+ employees but no headshot evidence found",
                    context="Team photos build trust and personalize the brand",
                    source_label="Profile trust and team data",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "headshots", "team", "trust"],
        ))

    return findings


# ============================================================================
# Check 9: Social Media Content Library
# ============================================================================

def _check_social_content_library(
    profile: BusinessProfile,
    archetype: Optional[str],
) -> List[AuditFinding]:
    """Assess social media content library readiness."""
    findings: List[AuditFinding] = []

    social_channels = _get_social_channels(profile)

    content_library_keywords = [
        "content library", "content calendar", "content bank",
        "asset library", "media library", "photo library",
        "content schedule", "batch content", "content batch",
    ]
    has_library_evidence = _profile_text_contains(profile, content_library_keywords)

    if social_channels and not has_library_evidence:
        channel_list = ", ".join(sorted(social_channels))
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="social_content_library",
            severity=FindingSeverity.MEDIUM.value,
            title="Active social channels but no content library",
            description=(
                f"Active social channels ({channel_list}) but no content "
                "library -- batch-create and organize content for consistent posting."
            ),
            recommendation=(
                "Build a content library: 30+ photos organized by category, "
                "10+ testimonial graphics, 5+ video clips, seasonal content templates"
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.SIGNIFICANT.value,
            source=FindingSource.STATIC.value,
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"Active social channels: {channel_list}",
                    context="Consistent posting requires a pre-built content library",
                    source_label="Channel analysis",
                ),
            ],
            archetype_relevance=[archetype] if archetype else [],
            tags=["creative", "social_media", "content_library"],
        ))

    elif not social_channels:
        # No social channels -- severity depends on archetype
        if archetype and archetype in _ECOMMERCE_ARCHETYPES:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="social_content_library",
                severity=FindingSeverity.INFO.value,
                title="No active social media channels detected",
                description=(
                    "No active social media channels detected. For ecommerce, "
                    "Instagram and TikTok are high-value channels that require "
                    "a content library to operate effectively."
                ),
                recommendation=(
                    "Establish social presence on Instagram and TikTok as a minimum. "
                    "Build a content library before launching to ensure consistent posting."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.SIGNIFICANT.value,
                source=FindingSource.MISSING_DATA.value,
                evidence=[
                    Evidence(
                        evidence_type="missing_data",
                        value="No active social channels in profile",
                        context="Social presence is critical for ecommerce brands",
                        source_label="Channel analysis",
                    ),
                ],
                archetype_relevance=[archetype] if archetype else [],
                tags=["creative", "social_media", "missing_data"],
            ))
        else:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="social_content_library",
                severity=FindingSeverity.INFO.value,
                title="No active social media channels detected",
                description=(
                    "No active social media channels detected -- unable to "
                    "assess social content library needs."
                ),
                recommendation=(
                    "If social media is planned, build a content library "
                    "before launching: 30+ photos, 10+ testimonial graphics, "
                    "5+ video clips"
                ),
                estimated_impact=ImpactLevel.LOW.value,
                effort=EffortLevel.SIGNIFICANT.value,
                source=FindingSource.MISSING_DATA.value,
                evidence=[
                    Evidence(
                        evidence_type="missing_data",
                        value="No active social channels in profile",
                        context="Cannot assess content library without knowing which social channels are used",
                        source_label="Channel analysis",
                    ),
                ],
                archetype_relevance=[archetype] if archetype else [],
                tags=["creative", "social_media", "missing_data"],
            ))

    return findings


# ============================================================================
# Check 10: Asset Gap Analysis Summary
# ============================================================================

def _check_asset_gap_analysis(
    profile: BusinessProfile,
    archetype: Optional[str],
    all_findings: List[AuditFinding],
) -> List[AuditFinding]:
    """Generate a composite summary mapping asset gaps to channel blockages."""
    findings: List[AuditFinding] = []

    arch = archetype or "general"
    asset_channel_map = map_assets_to_channels(arch)

    # Identify which asset categories have gaps based on prior findings
    gap_subcategories = set()
    highest_severity = FindingSeverity.INFO.value
    severity_rank = {
        FindingSeverity.CRITICAL.value: 4,
        FindingSeverity.HIGH.value: 3,
        FindingSeverity.MEDIUM.value: 2,
        FindingSeverity.LOW.value: 1,
        FindingSeverity.INFO.value: 0,
    }
    max_sev_rank = 0

    for f in all_findings:
        if f.severity in (FindingSeverity.HIGH.value, FindingSeverity.MEDIUM.value,
                          FindingSeverity.CRITICAL.value):
            if f.subcategory:
                gap_subcategories.add(f.subcategory)
            rank = severity_rank.get(f.severity, 0)
            if rank > max_sev_rank:
                max_sev_rank = rank
                highest_severity = f.severity

    if not gap_subcategories:
        # No significant asset gaps found -- no summary needed
        return findings

    # Map subcategories to readable asset names and their blocked channels
    subcategory_to_asset_map = {
        "professional_photography": ["product_photography", "project_photography",
                                     "lifestyle_photography", "product_service_photography"],
        "logo": ["logo"],
        "brand_colors": ["brand_colors"],
        "testimonial_content": ["testimonial_content"],
        "case_studies": ["case_study_content", "customer_success_stories"],
        "video_content": ["video", "product_video", "thought_leadership_video"],
        "before_after": ["before_after_photos"],
        "team_headshots": ["team_headshots", "professional_headshots"],
        "social_content_library": [],
    }

    asset_to_readable = {
        "professional_photography": "professional photography",
        "product_photography": "product photography",
        "project_photography": "project photography",
        "lifestyle_photography": "lifestyle photography",
        "product_service_photography": "product/service photography",
        "logo": "logo files",
        "brand_colors": "brand color definitions",
        "testimonial_content": "testimonial content",
        "case_study_content": "case study content",
        "customer_success_stories": "customer success stories",
        "video": "video content",
        "product_video": "product video",
        "thought_leadership_video": "thought leadership video",
        "before_after_photos": "before/after photos",
        "team_headshots": "team headshots",
        "professional_headshots": "professional headshots",
    }

    blockage_lines: List[str] = []
    blocked_channels_all: set = set()

    for subcat in gap_subcategories:
        asset_keys = subcategory_to_asset_map.get(subcat, [])
        for asset_key in asset_keys:
            channels = asset_channel_map.get(asset_key, [])
            if channels:
                readable = asset_to_readable.get(asset_key, asset_key.replace("_", " "))
                channel_str = ", ".join(ch.replace("_", " ").title() for ch in channels[:5])
                if len(channels) > 5:
                    channel_str += f" (+{len(channels) - 5} more)"
                blockage_lines.append(f"No {readable} blocks: {channel_str}")
                blocked_channels_all.update(channels)

    if not blockage_lines:
        return findings

    description_parts = ["Asset gaps block execution on key channels:"]
    description_parts.extend(f"  - {line}" for line in blockage_lines[:6])
    if len(blockage_lines) > 6:
        description_parts.append(f"  - ...and {len(blockage_lines) - 6} additional blockages")

    findings.append(create_finding(
        category=CATEGORY,
        subcategory="asset_gap_summary",
        severity=highest_severity,
        title=f"Asset gaps block {len(blocked_channels_all)} channel(s)",
        description="\n".join(description_parts),
        recommendation=(
            "Prioritize asset creation in order of channel impact. "
            "Start with the asset types that unblock the most channels "
            "simultaneously."
        ),
        estimated_impact=ImpactLevel.HIGH.value,
        effort=EffortLevel.SIGNIFICANT.value,
        source=FindingSource.STATIC.value,
        evidence=[
            Evidence(
                evidence_type="text",
                value=f"{len(gap_subcategories)} asset category gaps blocking {len(blocked_channels_all)} channels",
                context="Composite summary of all creative asset gaps",
                source_label="Creative readiness audit summary",
            ),
        ],
        related_findings=[f.id for f in all_findings if f.severity != FindingSeverity.INFO.value],
        archetype_relevance=[archetype] if archetype else [],
        tags=["creative", "summary", "asset_gaps", "blocker"],
        metadata={
            "blockage_lines": blockage_lines,
            "blocked_channel_count": len(blocked_channels_all),
            "gap_categories": sorted(gap_subcategories),
        },
    ))

    return findings


# ============================================================================
# Main entry point
# ============================================================================

def audit_creative_readiness(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run a creative and asset readiness audit on a business profile.

    Evaluates available marketing assets -- photography, video, brand
    assets, testimonials, case studies -- against the requirements of the
    business's active and planned channels.  Identifies asset gaps that
    would block or degrade specific channel executions.

    Parameters
    ----------
    profile:
        The ``BusinessProfile`` to audit.
    connected_data:
        Optional dictionary of data from connected platforms.  May
        include asset inventory data under keys like ``"assets"`` or
        ``"creative_assets"``.

    Returns
    -------
    List[AuditFinding]
        All findings from the creative readiness audit.  Each finding
        has ``category="creative_readiness"`` and a descriptive
        ``subcategory``.
    """
    archetype = _get_archetype(profile)
    findings: List[AuditFinding] = []

    # Check 1: Professional Photography
    findings.extend(_check_professional_photography(profile, archetype, connected_data))

    # Check 2: Logo Quality
    findings.extend(_check_logo_quality(profile, archetype))

    # Check 3: Brand Colors Defined
    findings.extend(_check_brand_colors(profile, archetype))

    # Check 4: Testimonial Content
    findings.extend(_check_testimonial_content(profile, archetype))

    # Check 5: Case Study Content
    findings.extend(_check_case_study_content(profile, archetype))

    # Check 6: Video Content
    findings.extend(_check_video_content(profile, archetype, connected_data))

    # Check 7: Before/After Documentation
    findings.extend(_check_before_after_documentation(profile, archetype))

    # Check 8: Team Headshots
    findings.extend(_check_team_headshots(profile, archetype))

    # Check 9: Social Media Content Library
    findings.extend(_check_social_content_library(profile, archetype))

    # Check 10: Asset Gap Analysis Summary (depends on all prior findings)
    findings.extend(_check_asset_gap_analysis(profile, archetype, findings))

    return findings


# ============================================================================
# Scoring
# ============================================================================

def score_creative_readiness(findings: List[AuditFinding]) -> float:
    """Compute a 0-100 creative readiness score from audit findings.

    Scoring formula::

        score = 100 - (critical * 25 + high * 15 + medium * 8 + low * 3)

    The score is clamped to [0, 100].  INFO-level and MISSING_DATA
    source findings do not reduce the score.

    Parameters
    ----------
    findings:
        List of ``AuditFinding`` from ``audit_creative_readiness()``.

    Returns
    -------
    float
        Creative readiness score in the range [0, 100].
    """
    critical = 0
    high = 0
    medium = 0
    low = 0

    for f in findings:
        sev = f.severity
        if sev == FindingSeverity.CRITICAL.value:
            critical += 1
        elif sev == FindingSeverity.HIGH.value:
            high += 1
        elif sev == FindingSeverity.MEDIUM.value:
            medium += 1
        elif sev == FindingSeverity.LOW.value:
            low += 1

    penalty = (critical * 25) + (high * 15) + (medium * 8) + (low * 3)
    return max(0.0, min(100.0, round(100.0 - penalty, 1)))
