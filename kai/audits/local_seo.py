"""Local SEO and visibility audit engine for the Kai Marketing OS.

Examines a BusinessProfile's geography, channels, offers, and identity
data to produce structured AuditFindings covering:

1.  GBP existence and completeness
2.  GBP category alignment
3.  NAP (Name, Address, Phone) consistency
4.  Local schema markup readiness
5.  Service area page strategy
6.  Location page strategy
7.  Local keyword targeting readiness
8.  Citation consistency
9.  Local link profile indicators
10. Per-location scoring (multi-location only)

For multi-location businesses every location is scored independently
and the weakest/strongest locations are flagged.

Usage::

    from kai.models.business_profile import BusinessProfile
    from kai.audits.local_seo import audit_local_seo, score_local_seo

    findings = audit_local_seo(profile)
    score = score_local_seo(findings)
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
    compute_category_scorecard,
    create_finding,
    create_missing_data_finding,
)
from kai.models.business_profile import BusinessProfile

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_CATEGORY = "local_seo"

_LOCAL_ARCHETYPES = {"local-service", "multi-location"}

_MAJOR_DIRECTORIES = [
    "Google",
    "Yelp",
    "Bing Places",
    "Apple Maps",
    "Facebook",
    "Yellow Pages",
    "BBB",
    "Nextdoor",
]


# ============================================================================
# Public API
# ============================================================================


def audit_local_seo(
    profile: "BusinessProfile",
    connected_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run all local SEO checks against a BusinessProfile.

    Parameters
    ----------
    profile:
        The business profile to audit.
    connected_data:
        Optional dictionary of live integration data.  Recognized keys:

        - ``"gbp_categories"`` -- dict with ``"primary"`` (str) and
          optional ``"secondary"`` (list[str]) GBP category info.
        - ``"citation_audit"`` -- dict with citation health data.
        - ``"backlinks"`` -- dict with local backlink/link-profile data.

    Returns
    -------
    List[AuditFinding]
        Ordered list of findings.  All findings have
        ``category="local_seo"``.
    """
    if connected_data is None:
        connected_data = {}

    findings: List[AuditFinding] = []

    archetype = _get_archetype(profile)
    is_local = archetype in _LOCAL_ARCHETYPES
    is_multi = archetype == "multi-location"
    has_physical = _has_physical_presence(profile)

    # Check 1 -- GBP existence and completeness
    findings.extend(_check_gbp_existence(profile, archetype, is_local, has_physical))

    # Check 2 -- GBP categories
    findings.extend(_check_gbp_categories(profile, connected_data))

    # Check 3 -- NAP consistency
    findings.extend(_check_nap_consistency(profile, is_multi))

    # Check 4 -- Local schema markup readiness
    findings.extend(_check_local_schema_markup(is_multi))

    # Check 5 -- Service area pages
    findings.extend(_check_service_area_pages(profile, archetype, is_local, is_multi))

    # Check 6 -- Location pages
    findings.extend(_check_location_pages(profile, archetype, is_multi))

    # Check 7 -- Local keyword targeting readiness
    findings.extend(_check_local_keyword_targeting(profile))

    # Check 8 -- Citation consistency
    findings.extend(_check_citation_consistency(connected_data))

    # Check 9 -- Local link profile indicators
    findings.extend(_check_local_link_profile(connected_data))

    # Check 10 -- Per-location scoring (multi-location only)
    findings.extend(_check_per_location_scoring(profile, is_multi))

    return findings


def score_local_seo(findings: List[AuditFinding]) -> float:
    """Compute a 0-100 local SEO health score from findings.

    Uses the standard Kai scoring formula via
    ``compute_category_scorecard``.  For multi-location businesses the
    per-location findings are weighted proportionally alongside the
    fleet-level findings.

    Parameters
    ----------
    findings:
        AuditFinding list produced by ``audit_local_seo``.

    Returns
    -------
    float
        Score in the range [0, 100].
    """
    if not findings:
        return 100.0

    scorecard = compute_category_scorecard(
        category=_CATEGORY,
        findings=findings,
        display_name="Local SEO",
        weight=1.0,
    )
    return scorecard.score


def assess_location_completeness(location: Dict[str, Any]) -> Dict[str, bool]:
    """Score a single location dict for completeness.

    Parameters
    ----------
    location:
        A dictionary (or ``Location.model_dump()`` output) with
        potential keys: ``name``, ``address``, ``phone``, ``gbp_url``,
        ``hours``.

    Returns
    -------
    Dict[str, bool]
        Keys: ``has_name``, ``has_address``, ``has_phone``,
        ``has_gbp``, ``has_hours``.
    """
    return {
        "has_name": bool(location.get("name")),
        "has_address": bool(location.get("address")),
        "has_phone": bool(location.get("phone")),
        "has_gbp": bool(location.get("gbp_url")),
        "has_hours": bool(location.get("hours")),
    }


# ============================================================================
# Check implementations
# ============================================================================


def _check_gbp_existence(
    profile: "BusinessProfile",
    archetype: str,
    is_local: bool,
    has_physical: bool,
) -> List[AuditFinding]:
    """Check 1: GBP existence and completeness."""
    findings: List[AuditFinding] = []
    gbp_channel = _find_channel(profile, "gbp")

    recommendation = (
        "Claim, verify, and fully complete your Google Business Profile. "
        "Include: business description, all services, photos, hours, and service area."
    )

    if gbp_channel is None:
        # No GBP channel at all
        if is_local:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="gbp_existence",
                severity=FindingSeverity.CRITICAL.value,
                title="No Google Business Profile detected",
                description=(
                    "GBP is the #1 local discovery channel for local-service and "
                    "multi-location businesses. Without a verified GBP, the business "
                    "is invisible in Google Maps and local pack results."
                ),
                recommendation=recommendation,
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.STATIC.value,
                archetype_relevance=["local-service", "multi-location"],
                tags=["gbp", "local_seo", "visibility"],
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="No GBP channel found in profile.channels",
                        context="Google Business Profile is required for local search visibility.",
                        source_label="Business profile channel audit",
                    ),
                ],
            ))
        elif has_physical:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="gbp_existence",
                severity=FindingSeverity.HIGH.value,
                title="Physical locations but no Google Business Profile",
                description=(
                    "The business has physical locations but no Google Business Profile. "
                    "A verified GBP drives foot traffic, phone calls, and direction "
                    "requests for any business with a physical presence."
                ),
                recommendation=recommendation,
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.STATIC.value,
                tags=["gbp", "local_seo", "visibility"],
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="Physical locations exist but no GBP channel found",
                        context="Any business with a physical location benefits from a GBP listing.",
                        source_label="Business profile channel audit",
                    ),
                ],
            ))
    else:
        # GBP exists -- check active status
        is_active = getattr(gbp_channel, "is_active", False)
        if not is_active:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="gbp_existence",
                severity=FindingSeverity.HIGH.value,
                title="Google Business Profile is inactive",
                description=(
                    "The Google Business Profile exists but is marked as inactive. "
                    "An inactive GBP loses ranking signals, stops appearing in local "
                    "search results, and cannot accumulate new reviews."
                ),
                recommendation=(
                    "Reactivate the Google Business Profile. Verify ownership, update "
                    "business hours, add recent photos, and respond to any pending reviews."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.STATIC.value,
                tags=["gbp", "local_seo", "inactive"],
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="GBP channel exists with is_active=False",
                        context="An inactive GBP loses ranking signals over time.",
                        source_label="Business profile channel audit",
                    ),
                ],
            ))
        else:
            # GBP is active -- check for completeness via notes/metadata
            notes = getattr(gbp_channel, "notes", None) or ""
            completeness_issues = []
            if "incomplete" in notes.lower():
                completeness_issues.append("GBP notes indicate incomplete profile")
            if "missing" in notes.lower():
                completeness_issues.append("GBP notes indicate missing information")

            if completeness_issues:
                findings.append(create_finding(
                    category=_CATEGORY,
                    subcategory="gbp_completeness",
                    severity=FindingSeverity.MEDIUM.value,
                    title="Google Business Profile may be incomplete",
                    description=(
                        "The GBP is active but channel notes suggest it may not be "
                        "fully completed. A fully completed GBP ranks higher and "
                        "converts more searchers to customers."
                    ),
                    recommendation=recommendation,
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    source=FindingSource.INFERRED.value,
                    tags=["gbp", "local_seo", "completeness"],
                    evidence=[
                        Evidence(
                            evidence_type="text",
                            value="; ".join(completeness_issues),
                            context="Inferred from GBP channel notes.",
                            source_label="Business profile channel notes",
                        ),
                    ],
                ))

    return findings


def _check_gbp_categories(
    profile: "BusinessProfile",
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 2: GBP category alignment."""
    findings: List[AuditFinding] = []

    gbp_categories = connected_data.get("gbp_categories")

    if gbp_categories is None:
        findings.append(create_missing_data_finding(
            category=_CATEGORY,
            field_path="connected_data.gbp_categories",
            impact_description=(
                "Cannot verify GBP primary category alignment without connected "
                "GBP category data. The primary category is the strongest local "
                "ranking signal after proximity."
            ),
            how_to_provide=(
                "Connect GBP data or manually provide the primary and secondary "
                "categories set in Google Business Profile."
            ),
        ))
    else:
        primary_cat = gbp_categories.get("primary", "")
        secondary_cats = gbp_categories.get("secondary", [])

        # Check alignment with business offers
        primary_offer_names = [
            o.name.lower()
            for o in profile.offers
            if getattr(o, "is_primary", False)
        ]
        all_offer_names = [o.name.lower() for o in profile.offers]

        if primary_cat:
            primary_cat_lower = primary_cat.lower()
            # Rough alignment check: primary category should relate to
            # the primary service
            has_alignment = any(
                offer_name in primary_cat_lower or primary_cat_lower in offer_name
                for offer_name in (primary_offer_names or all_offer_names)
            )
            if not has_alignment and (primary_offer_names or all_offer_names):
                findings.append(create_finding(
                    category=_CATEGORY,
                    subcategory="gbp_categories",
                    severity=FindingSeverity.MEDIUM.value,
                    title="GBP primary category may not match main service",
                    description=(
                        f"The GBP primary category is '{primary_cat}' but it does "
                        f"not clearly align with the business's primary offers. "
                        f"The primary category is the strongest local ranking signal "
                        f"after searcher proximity."
                    ),
                    recommendation=(
                        "Set your primary GBP category to your most important "
                        "service. Add secondary categories for all other services offered."
                    ),
                    estimated_impact=ImpactLevel.HIGH.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    source=FindingSource.CONNECTED.value,
                    tags=["gbp", "categories", "local_seo"],
                    evidence=[
                        Evidence(
                            evidence_type="comparison",
                            value=f"GBP primary: '{primary_cat}' vs. offers: {all_offer_names[:5]}",
                            context="Primary category should match the core service.",
                            source_label="GBP category data",
                        ),
                    ],
                ))

            # Check secondary categories cover additional offers
            if len(all_offer_names) > 1 and not secondary_cats:
                findings.append(create_finding(
                    category=_CATEGORY,
                    subcategory="gbp_categories",
                    severity=FindingSeverity.LOW.value,
                    title="No secondary GBP categories set",
                    description=(
                        "The business offers multiple services but no secondary "
                        "GBP categories are set. Secondary categories help the "
                        "listing appear in searches for additional services."
                    ),
                    recommendation=(
                        "Add secondary categories for all other services offered "
                        "beyond the primary category."
                    ),
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    source=FindingSource.CONNECTED.value,
                    tags=["gbp", "categories", "local_seo"],
                    evidence=[
                        Evidence(
                            evidence_type="text",
                            value=f"Business has {len(all_offer_names)} offers but 0 secondary GBP categories.",
                            source_label="GBP category data",
                        ),
                    ],
                ))
        else:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="gbp_categories",
                severity=FindingSeverity.HIGH.value,
                title="GBP primary category not set",
                description=(
                    "The Google Business Profile has no primary category. The "
                    "primary category is the single strongest local ranking signal "
                    "after searcher proximity. Without it, the listing will rank "
                    "poorly for relevant searches."
                ),
                recommendation=(
                    "Set your primary GBP category to your most important "
                    "service. Add secondary categories for all other services offered."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.CONNECTED.value,
                tags=["gbp", "categories", "local_seo"],
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="GBP primary category is empty.",
                        source_label="GBP category data",
                    ),
                ],
            ))

    return findings


def _check_nap_consistency(
    profile: "BusinessProfile",
    is_multi: bool,
) -> List[AuditFinding]:
    """Check 3: NAP (Name, Address, Phone) consistency."""
    findings: List[AuditFinding] = []
    identity = profile.identity
    locations = profile.geography.locations

    business_name = getattr(identity, "business_name", None) or ""
    business_phone = getattr(identity, "phone", None) or ""
    dba = getattr(identity, "dba", None) or ""
    legal_entity = getattr(identity, "legal_entity", None) or ""

    # Check for multiple business names (DBA vs legal)
    names_in_use = [n for n in [business_name, dba, legal_entity] if n]
    unique_names = set(n.strip().lower() for n in names_in_use if n.strip())
    if len(unique_names) > 1:
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="nap_consistency",
            severity=FindingSeverity.MEDIUM.value,
            title="Business uses multiple names",
            description=(
                "The business has different names across identity fields "
                f"(business name, DBA, legal entity: {names_in_use}). "
                "NAP inconsistency across directories hurts local rankings and "
                "confuses search engines trying to reconcile entity references."
            ),
            recommendation=(
                "Choose one canonical business name and ensure it is used "
                "identically across all online directories, citations, and the "
                "Google Business Profile."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            tags=["nap", "consistency", "local_seo"],
            evidence=[
                Evidence(
                    evidence_type="comparison",
                    value=f"Names found: {names_in_use}",
                    context="Multiple names create NAP inconsistency across directories.",
                    source_label="Business identity fields",
                ),
            ],
        ))

    # Check phone consistency between identity and locations
    if locations and business_phone:
        for loc in locations:
            loc_phone = getattr(loc, "phone", None) or ""
            if loc_phone and _normalize_phone(loc_phone) != _normalize_phone(business_phone):
                loc_name = getattr(loc, "name", None) or "Unnamed location"
                findings.append(create_finding(
                    category=_CATEGORY,
                    subcategory="nap_consistency",
                    severity=FindingSeverity.MEDIUM.value,
                    title=f"Inconsistent phone: '{loc_name}' vs. business identity",
                    description=(
                        f"Location '{loc_name}' has phone '{loc_phone}' which differs "
                        f"from the business identity phone '{business_phone}'. "
                        f"NAP inconsistency hurts local rankings because search engines "
                        f"cannot confidently reconcile the listings as the same entity."
                    ),
                    recommendation=(
                        "If each location has a unique tracking or direct line, "
                        "that is acceptable. Ensure the business identity phone matches "
                        "the primary location or headquarters number used on the main "
                        "GBP listing."
                    ),
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    source=FindingSource.STATIC.value,
                    tags=["nap", "phone", "consistency", "local_seo"],
                    evidence=[
                        Evidence(
                            evidence_type="comparison",
                            value=f"Identity phone: '{business_phone}' vs. location phone: '{loc_phone}'",
                            context="Phone numbers should be consistent or intentionally different per-location.",
                            source_label="Business profile data",
                        ),
                    ],
                    kaicalls_relevant=True,
                ))

    # Per-location NAP completeness (especially for multi-location)
    if is_multi and locations:
        for loc in locations:
            loc_name = getattr(loc, "name", None) or "Unnamed location"
            loc_address = getattr(loc, "address", None) or ""
            loc_phone = getattr(loc, "phone", None) or ""

            missing_fields = []
            if not loc_address:
                missing_fields.append("address")
            if not loc_phone:
                missing_fields.append("phone")

            if missing_fields:
                findings.append(create_finding(
                    category=_CATEGORY,
                    subcategory="nap_consistency",
                    severity=FindingSeverity.HIGH.value,
                    title=f"Location '{loc_name}' missing {', '.join(missing_fields)}",
                    description=(
                        f"Location '{loc_name}' is missing {' and '.join(missing_fields)}. "
                        f"Incomplete location data breaks NAP consistency and prevents "
                        f"the location from being properly indexed in local search."
                    ),
                    recommendation=(
                        f"Add the missing {' and '.join(missing_fields)} for location "
                        f"'{loc_name}'. Every location must have a complete NAP "
                        f"(Name, Address, Phone) to rank in local results."
                    ),
                    estimated_impact=ImpactLevel.HIGH.value,
                    effort=EffortLevel.QUICK_WIN.value,
                    source=FindingSource.STATIC.value,
                    archetype_relevance=["multi-location"],
                    tags=["nap", "completeness", "local_seo", "multi-location"],
                    evidence=[
                        Evidence(
                            evidence_type="checklist_item",
                            value=f"Location '{loc_name}' missing: {', '.join(missing_fields)}",
                            context="Every location needs complete NAP for local search indexing.",
                            source_label="Location data audit",
                        ),
                    ],
                    kaicalls_relevant="phone" in missing_fields,
                ))
    elif not is_multi and locations:
        # Single-location: check the one location for basic completeness
        loc = locations[0]
        loc_address = getattr(loc, "address", None) or ""
        loc_phone = getattr(loc, "phone", None) or ""
        if not loc_address and not business_phone and not loc_phone:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="nap_consistency",
                severity=FindingSeverity.HIGH.value,
                title="Incomplete NAP data for primary location",
                description=(
                    "The primary location is missing both address and phone. "
                    "A complete NAP (Name, Address, Phone) is the foundation "
                    "of local SEO. Without it, the business cannot appear "
                    "correctly in local search results."
                ),
                recommendation=(
                    "Add a complete address and phone number for the primary "
                    "business location."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.QUICK_WIN.value,
                source=FindingSource.STATIC.value,
                tags=["nap", "completeness", "local_seo"],
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="Primary location missing address and phone.",
                        source_label="Location data audit",
                    ),
                ],
                kaicalls_relevant=True,
            ))

    return findings


def _check_local_schema_markup(is_multi: bool) -> List[AuditFinding]:
    """Check 4: Local schema markup readiness (advisory)."""
    findings: List[AuditFinding] = []

    if is_multi:
        recommendation = (
            "Implement LocalBusiness schema markup on every location page. "
            "Include: name, address, phone, hours, geo coordinates, service "
            "area, and aggregate rating. Each location page should have its "
            "own LocalBusiness schema with unique address and phone."
        )
    else:
        recommendation = (
            "Implement LocalBusiness schema markup on every location page. "
            "Include: name, address, phone, hours, geo coordinates, service "
            "area, and aggregate rating."
        )

    findings.append(create_missing_data_finding(
        category=_CATEGORY,
        field_path="website.schema_markup.local_business",
        impact_description=(
            "Cannot verify LocalBusiness schema markup from profile data alone. "
            "Structured data helps search engines display rich results (star "
            "ratings, hours, address) and improves local ranking signals."
        ),
        how_to_provide=(
            "Connect website crawl data or provide the current schema markup "
            "status for location pages."
        ),
    ))

    # Also generate the advisory recommendation
    findings.append(create_finding(
        category=_CATEGORY,
        subcategory="schema_markup",
        severity=FindingSeverity.MEDIUM.value,
        title="Implement LocalBusiness schema markup",
        description=(
            "LocalBusiness structured data enables rich snippets in search results "
            "(star ratings, hours, phone) and provides explicit entity signals to "
            "search engines. This cannot be verified from profile data alone but "
            "is a high-impact local SEO requirement."
        ),
        recommendation=recommendation,
        estimated_impact=ImpactLevel.MEDIUM.value,
        effort=EffortLevel.MODERATE.value,
        source=FindingSource.INFERRED.value,
        tags=["schema", "structured_data", "local_seo"],
        evidence=[
            Evidence(
                evidence_type="text",
                value="Schema markup status cannot be determined from business profile data.",
                context="Advisory: verify and implement LocalBusiness schema on all location pages.",
                source_label="Local SEO best practices",
            ),
        ],
    ))

    return findings


def _check_service_area_pages(
    profile: "BusinessProfile",
    archetype: str,
    is_local: bool,
    is_multi: bool,
) -> List[AuditFinding]:
    """Check 5: Service area page strategy."""
    findings: List[AuditFinding] = []
    service_areas = profile.geography.service_areas
    locations = profile.geography.locations
    n_areas = len(service_areas)

    if is_local:
        if n_areas == 0:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="service_area_pages",
                severity=FindingSeverity.HIGH.value,
                title="No service areas defined",
                description=(
                    "Service area pages are the foundation of local SEO for "
                    "service-area businesses. Without defined service areas, "
                    "the business cannot build location-targeted pages that "
                    "rank for '[service] in [city]' queries."
                ),
                recommendation=(
                    "Define all primary service areas (cities, neighborhoods, "
                    "counties) the business serves. Create a dedicated, "
                    "unique-content page for each service area."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.SIGNIFICANT.value,
                source=FindingSource.STATIC.value,
                archetype_relevance=["local-service"],
                tags=["service_areas", "local_seo", "content_strategy"],
                evidence=[
                    Evidence(
                        evidence_type="checklist_item",
                        value="profile.geography.service_areas is empty",
                        context="Service area pages are required for local-service businesses.",
                        source_label="Business geography audit",
                    ),
                ],
            ))
        elif n_areas <= 2:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="service_area_pages",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Only {n_areas} service area(s) defined",
                description=(
                    f"Only {n_areas} service area(s) are defined: {service_areas}. "
                    f"Expanding service area coverage with dedicated pages for each "
                    f"market creates more ranking opportunities for local queries."
                ),
                recommendation=(
                    "Expand to cover all primary markets with dedicated pages. "
                    "Each service area page should have unique content — not "
                    "templated address swaps."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.STATIC.value,
                archetype_relevance=["local-service"],
                tags=["service_areas", "local_seo", "content_strategy"],
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"Service areas: {service_areas}",
                        context="Most local businesses serve 5+ distinct areas.",
                        source_label="Business geography audit",
                    ),
                ],
            ))
        else:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="service_area_pages",
                severity=FindingSeverity.INFO.value,
                title=f"Service areas defined for {n_areas} markets",
                description=(
                    f"{n_areas} service areas are defined: {service_areas[:5]}"
                    f"{'...' if n_areas > 5 else ''}. "
                    f"Ensure each has a dedicated, unique content page — not "
                    f"templated address-swap pages that Google may flag as thin content."
                ),
                recommendation=(
                    "Audit each service area page for unique content. Each page "
                    "should reference local landmarks, neighborhoods, and specific "
                    "service details for that area."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.ONGOING.value,
                source=FindingSource.STATIC.value,
                archetype_relevance=["local-service"],
                tags=["service_areas", "local_seo", "content_strategy"],
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"{n_areas} service areas defined.",
                        source_label="Business geography audit",
                    ),
                ],
            ))

    # Multi-location: locations exist but no service area strategy
    if is_multi and locations and n_areas == 0:
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="service_area_pages",
            severity=FindingSeverity.HIGH.value,
            title="Locations exist but no service area strategy defined",
            description=(
                "The business has multiple locations but no service areas are "
                "defined. Each location should have a service area footprint "
                "with dedicated content targeting local searches."
            ),
            recommendation=(
                "Define the service area for each location. Build service area "
                "pages that target '[service] in [city/neighborhood]' queries "
                "for each location's market."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.SIGNIFICANT.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=["multi-location"],
            tags=["service_areas", "local_seo", "multi-location"],
            evidence=[
                Evidence(
                    evidence_type="checklist_item",
                    value=f"{len(locations)} locations but 0 service areas defined.",
                    context="Multi-location businesses need a service area strategy per location.",
                    source_label="Business geography audit",
                ),
            ],
        ))

    return findings


def _check_location_pages(
    profile: "BusinessProfile",
    archetype: str,
    is_multi: bool,
) -> List[AuditFinding]:
    """Check 6: Location page strategy."""
    findings: List[AuditFinding] = []
    locations = profile.geography.locations
    n_locations = len(locations)

    if is_multi:
        if n_locations > 1:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="location_pages",
                severity=FindingSeverity.HIGH.value,
                title=f"Ensure {n_locations} unique location pages exist",
                description=(
                    f"The business has {n_locations} locations. Each needs a "
                    f"dedicated website page with unique content — not just "
                    f"address swaps. Location pages are the landing targets "
                    f"for local search and Google Maps clicks."
                ),
                recommendation=(
                    f"Create {n_locations} unique location pages. Each page should "
                    f"include: location-specific content, team bios, photos of the "
                    f"actual location, local testimonials, and embedded Google Map. "
                    f"Avoid duplicate content across location pages."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.SIGNIFICANT.value,
                source=FindingSource.STATIC.value,
                archetype_relevance=["multi-location"],
                tags=["location_pages", "local_seo", "multi-location"],
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"{n_locations} locations require unique pages.",
                        context="Each location page must have unique content for local ranking.",
                        source_label="Business geography audit",
                    ),
                ],
            ))
        elif n_locations == 1:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="location_pages",
                severity=FindingSeverity.MEDIUM.value,
                title="Single location — create a dedicated location page",
                description=(
                    "Multi-location archetype with only one location currently. "
                    "A dedicated location page is still essential for local SEO."
                ),
                recommendation=(
                    "Create a dedicated location page with address, hours, "
                    "embedded map, and location-specific content."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.STATIC.value,
                archetype_relevance=["multi-location"],
                tags=["location_pages", "local_seo"],
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value="1 location defined for multi-location archetype.",
                        source_label="Business geography audit",
                    ),
                ],
            ))
    elif archetype == "local-service":
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="location_pages",
            severity=FindingSeverity.MEDIUM.value,
            title="Create a dedicated local office or service area page",
            description=(
                "Local-service businesses benefit from a dedicated page about "
                "their office, team, and service area. This page serves as "
                "the landing target for branded local searches and builds "
                "trust with local customers."
            ),
            recommendation=(
                "Create a dedicated 'About Our [City] Office' or "
                "'Service Areas' page. Include team photos, the office "
                "address, hours, and a description of the areas served."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=["local-service"],
            tags=["location_pages", "local_seo"],
            evidence=[
                Evidence(
                    evidence_type="text",
                    value="Local-service archetype benefits from a dedicated location page.",
                    source_label="Local SEO best practices",
                ),
            ],
        ))

    return findings


def _check_local_keyword_targeting(
    profile: "BusinessProfile",
) -> List[AuditFinding]:
    """Check 7: Local keyword targeting readiness."""
    findings: List[AuditFinding] = []
    offers = profile.offers
    service_areas = profile.geography.service_areas
    has_offers = len(offers) > 0
    has_service_areas = len(service_areas) > 0

    if not has_offers:
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="keyword_targeting",
            severity=FindingSeverity.CRITICAL.value,
            title="Offers not defined — cannot build keyword strategy",
            description=(
                "No offers (services or products) are defined in the business "
                "profile. A keyword strategy requires knowing what the business "
                "does so that '[service] + [location]' keyword combinations "
                "can be built."
            ),
            recommendation=(
                "Define the business's primary offers (services or products). "
                "Each offer becomes the seed for local keyword targeting: "
                "'[offer] in [city]', '[offer] near [neighborhood]', "
                "'best [offer] [city]'."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            tags=["keywords", "local_seo", "offers"],
            evidence=[
                Evidence(
                    evidence_type="checklist_item",
                    value="profile.offers is empty",
                    context="Cannot build any keyword strategy without knowing the business's services.",
                    source_label="Business profile audit",
                ),
            ],
        ))
    elif not has_service_areas:
        # Has offers but no service areas
        offer_names = [o.name for o in offers[:5]]
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="keyword_targeting",
            severity=FindingSeverity.HIGH.value,
            title="Service areas needed to build local keyword targeting",
            description=(
                f"The business has offers ({offer_names}) but no service areas "
                f"are defined. Local keyword targeting requires both the 'what' "
                f"(services) and the 'where' (service areas) to build effective "
                f"'[service] in [city]' combinations."
            ),
            recommendation=(
                "Define all service areas (cities, neighborhoods, counties) the "
                "business serves. This enables keyword combinations like: "
                f"'{offers[0].name} in [city]', "
                f"'{offers[0].name} near [neighborhood]', "
                f"'best {offers[0].name} [city]'."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            tags=["keywords", "local_seo", "service_areas"],
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"Offers present ({len(offers)}) but service_areas is empty.",
                    context="Both offers and service areas are needed for local keyword targeting.",
                    source_label="Business profile audit",
                ),
            ],
        ))
    else:
        # Both present — good
        offer_names = [o.name for o in offers[:3]]
        area_names = service_areas[:3]
        example_keywords = [
            f"{offer_names[0]} in {area_names[0]}",
        ]
        if len(area_names) > 1:
            example_keywords.append(f"{offer_names[0]} near {area_names[1]}")
        if len(offer_names) > 1:
            example_keywords.append(f"best {offer_names[1]} {area_names[0]}")

        total_combos = len(offers) * len(service_areas)
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="keyword_targeting",
            severity=FindingSeverity.INFO.value,
            title=f"Local keyword targets ready: {total_combos} service+location combos",
            description=(
                f"Local keyword targets can be built from {len(offers)} offers "
                f"and {len(service_areas)} service areas "
                f"({total_combos} combinations). "
                f"Example patterns: {', '.join(example_keywords)}."
            ),
            recommendation=(
                "Build a keyword map pairing each offer with each service area. "
                "Prioritize high-value combinations (primary offer + largest market) "
                "for dedicated landing pages."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            tags=["keywords", "local_seo", "ready"],
            evidence=[
                Evidence(
                    evidence_type="text",
                    value=f"{total_combos} keyword combinations available.",
                    context=f"Examples: {', '.join(example_keywords)}",
                    source_label="Business profile data",
                ),
            ],
        ))

    return findings


def _check_citation_consistency(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 8: Citation consistency."""
    findings: List[AuditFinding] = []
    citation_data = connected_data.get("citation_audit")

    if citation_data is None:
        findings.append(create_missing_data_finding(
            category=_CATEGORY,
            field_path="connected_data.citation_audit",
            impact_description=(
                "Cannot assess citation health without connected citation audit "
                "data. Inconsistent citations (different name, address, or phone "
                "across directories) directly hurt local rankings."
            ),
            how_to_provide=(
                "Run a citation audit using a tool like BrightLocal, Moz Local, "
                "or Whitespark. Provide the results as connected_data."
            ),
        ))

        # Also generate the advisory recommendation
        dir_list = ", ".join(_MAJOR_DIRECTORIES)
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="citations",
            severity=FindingSeverity.MEDIUM.value,
            title="Audit citations on major directories for NAP consistency",
            description=(
                "Citation consistency across major directories is a core local "
                "ranking factor. Inconsistent NAP (Name, Address, Phone) across "
                "directories confuses search engines and weakens local authority."
            ),
            recommendation=(
                f"Audit citations on major directories ({dir_list}) for NAP "
                f"consistency. Fix any inconsistencies in business name, address, "
                f"or phone number. Consider using a citation management service "
                f"for ongoing consistency."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.INFERRED.value,
            tags=["citations", "nap", "local_seo"],
            evidence=[
                Evidence(
                    evidence_type="text",
                    value="Citation audit data not available — advisory recommendation.",
                    context="Citation consistency is a core local ranking signal.",
                    source_label="Local SEO best practices",
                ),
            ],
        ))
    else:
        # Analyze connected citation data
        inconsistent = citation_data.get("inconsistent_listings", [])
        total_listings = citation_data.get("total_listings", 0)
        missing_listings = citation_data.get("missing_listings", [])

        if inconsistent:
            severity = (
                FindingSeverity.HIGH.value
                if len(inconsistent) > 3
                else FindingSeverity.MEDIUM.value
            )
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="citations",
                severity=severity,
                title=f"{len(inconsistent)} inconsistent citation(s) found",
                description=(
                    f"Found {len(inconsistent)} directories with inconsistent NAP "
                    f"data out of {total_listings} total listings. Inconsistent "
                    f"citations confuse search engines and weaken local authority."
                ),
                recommendation=(
                    "Fix NAP inconsistencies on the flagged directories. Prioritize "
                    "Google, Yelp, and Facebook first as they carry the most weight."
                ),
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.CONNECTED.value,
                tags=["citations", "nap", "local_seo", "inconsistent"],
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"Inconsistent: {inconsistent[:5]}",
                        context=f"{len(inconsistent)} of {total_listings} listings have NAP issues.",
                        source_label="Citation audit data",
                    ),
                ],
            ))

        if missing_listings:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="citations",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Missing from {len(missing_listings)} major directories",
                description=(
                    f"The business is not listed on {len(missing_listings)} major "
                    f"directories: {missing_listings[:5]}. Each missing directory "
                    f"is a lost citation signal and a missed discovery channel."
                ),
                recommendation=(
                    f"Create listings on: {', '.join(missing_listings[:5])}. "
                    f"Ensure consistent NAP data across all new listings."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.MODERATE.value,
                source=FindingSource.CONNECTED.value,
                tags=["citations", "local_seo", "missing"],
                evidence=[
                    Evidence(
                        evidence_type="text",
                        value=f"Missing from: {missing_listings}",
                        source_label="Citation audit data",
                    ),
                ],
            ))

    return findings


def _check_local_link_profile(
    connected_data: Dict[str, Any],
) -> List[AuditFinding]:
    """Check 9: Local link profile indicators."""
    findings: List[AuditFinding] = []
    backlink_data = connected_data.get("backlinks")

    if backlink_data is None:
        findings.append(create_missing_data_finding(
            category=_CATEGORY,
            field_path="connected_data.backlinks",
            impact_description=(
                "Cannot assess local link profile without connected backlink data. "
                "Local links from chambers of commerce, sponsorships, and community "
                "organizations are strong local ranking signals."
            ),
            how_to_provide=(
                "Connect Ahrefs, Moz, or Semrush backlink data. Alternatively, "
                "provide a manual list of known local link sources."
            ),
        ))

        # Advisory recommendation
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="local_links",
            severity=FindingSeverity.LOW.value,
            title="Build local links through community involvement",
            description=(
                "Local backlinks from authoritative community sources are a "
                "strong local ranking signal. Without backlink data, the current "
                "local link profile cannot be assessed."
            ),
            recommendation=(
                "Build local links through: chamber of commerce membership, "
                "local sponsorships, local news coverage, partner cross-links, "
                "and community involvement."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.ONGOING.value,
            source=FindingSource.INFERRED.value,
            tags=["links", "local_seo", "community"],
            evidence=[
                Evidence(
                    evidence_type="text",
                    value="Backlink data not available — advisory recommendation.",
                    context="Local links are a core local ranking factor.",
                    source_label="Local SEO best practices",
                ),
            ],
        ))
    else:
        # Analyze connected backlink data
        local_links = backlink_data.get("local_link_count", 0)
        total_links = backlink_data.get("total_link_count", 0)
        local_sources = backlink_data.get("local_sources", [])

        if total_links > 0 and local_links == 0:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="local_links",
                severity=FindingSeverity.MEDIUM.value,
                title="No local links detected in backlink profile",
                description=(
                    f"The site has {total_links} total backlinks but no locally "
                    f"relevant links. Local links from community organizations, "
                    f"local news, and business partners send strong local "
                    f"ranking signals."
                ),
                recommendation=(
                    "Build local links through: chamber of commerce membership, "
                    "local sponsorships, local news coverage, partner cross-links, "
                    "and community involvement."
                ),
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.ONGOING.value,
                source=FindingSource.CONNECTED.value,
                tags=["links", "local_seo"],
                evidence=[
                    Evidence(
                        evidence_type="metric",
                        value=f"0 local links out of {total_links} total.",
                        source_label="Backlink data",
                    ),
                ],
            ))
        elif local_links > 0:
            findings.append(create_finding(
                category=_CATEGORY,
                subcategory="local_links",
                severity=FindingSeverity.INFO.value,
                title=f"{local_links} local link(s) detected",
                description=(
                    f"Found {local_links} locally relevant links out of "
                    f"{total_links} total. "
                    f"{'Sources include: ' + ', '.join(local_sources[:5]) if local_sources else ''}"
                ),
                recommendation=(
                    "Continue building local links. Target: chamber of commerce, "
                    "local sponsorships, local news, and partner cross-links."
                ),
                estimated_impact=ImpactLevel.LOW.value,
                effort=EffortLevel.ONGOING.value,
                source=FindingSource.CONNECTED.value,
                tags=["links", "local_seo"],
                evidence=[
                    Evidence(
                        evidence_type="metric",
                        value=f"{local_links} local links out of {total_links} total.",
                        source_label="Backlink data",
                    ),
                ],
            ))

    return findings


def _check_per_location_scoring(
    profile: "BusinessProfile",
    is_multi: bool,
) -> List[AuditFinding]:
    """Check 10: Per-location scoring (multi-location only)."""
    findings: List[AuditFinding] = []
    locations = profile.geography.locations

    if not is_multi or len(locations) < 2:
        return findings

    # Score each location
    location_scores: List[Dict[str, Any]] = []
    for loc in locations:
        loc_dict = loc.model_dump() if hasattr(loc, "model_dump") else loc.__dict__
        completeness = assess_location_completeness(loc_dict)
        score = sum(1 for v in completeness.values() if v)
        total = len(completeness)
        loc_name = getattr(loc, "name", None) or loc_dict.get("name") or "Unnamed"
        location_scores.append({
            "name": loc_name,
            "completeness": completeness,
            "score": score,
            "total": total,
            "location": loc,
        })

    # Generate a finding for each location
    for ls in location_scores:
        comp = ls["completeness"]
        present = [k.replace("has_", "") for k, v in comp.items() if v]
        missing = [k.replace("has_", "") for k, v in comp.items() if not v]

        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="per_location_score",
            severity=FindingSeverity.INFO.value,
            title=f"Location '{ls['name']}': {ls['score']}/{ls['total']} completeness",
            description=(
                f"Location '{ls['name']}' scores {ls['score']}/{ls['total']} "
                f"on local SEO readiness. "
                f"Present: {', '.join(present) if present else 'none'}. "
                f"Missing: {', '.join(missing) if missing else 'none'}."
            ),
            recommendation=(
                f"Complete the missing fields for '{ls['name']}': "
                f"{', '.join(missing)}."
                if missing
                else f"'{ls['name']}' is fully complete. Maintain and optimize."
            ),
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=["multi-location"],
            tags=["per_location", "local_seo", "multi-location"],
            evidence=[
                Evidence(
                    evidence_type="checklist_item",
                    value=f"Score: {ls['score']}/{ls['total']}",
                    context=f"Present: {present}, Missing: {missing}",
                    source_label=f"Location completeness: {ls['name']}",
                ),
            ],
            metadata={
                "location_name": ls["name"],
                "completeness": ls["completeness"],
                "score": ls["score"],
                "total": ls["total"],
            },
        ))

    # Identify weakest and strongest locations
    sorted_locations = sorted(location_scores, key=lambda x: x["score"])
    weakest = sorted_locations[0]
    strongest = sorted_locations[-1]

    if weakest["score"] < strongest["score"]:
        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="per_location_score",
            severity=FindingSeverity.HIGH.value,
            title=f"Location '{weakest['name']}' has the weakest local SEO profile",
            description=(
                f"'{weakest['name']}' scores {weakest['score']}/{weakest['total']} — "
                f"the lowest of all {len(locations)} locations. Prioritize filling "
                f"gaps here to raise the fleet-wide local SEO floor."
            ),
            recommendation=(
                f"Prioritize '{weakest['name']}'. Fill missing fields: "
                f"{', '.join(k.replace('has_', '') for k, v in weakest['completeness'].items() if not v)}."
            ),
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=["multi-location"],
            tags=["per_location", "local_seo", "multi-location", "weakest"],
            evidence=[
                Evidence(
                    evidence_type="comparison",
                    value=f"Weakest: '{weakest['name']}' ({weakest['score']}/{weakest['total']})",
                    context=f"Strongest: '{strongest['name']}' ({strongest['score']}/{strongest['total']})",
                    source_label="Per-location scoring comparison",
                ),
            ],
            metadata={"weakest_location": weakest["name"]},
        ))

        findings.append(create_finding(
            category=_CATEGORY,
            subcategory="per_location_score",
            severity=FindingSeverity.INFO.value,
            title=f"Location '{strongest['name']}' is the best-optimized",
            description=(
                f"'{strongest['name']}' scores {strongest['score']}/{strongest['total']} — "
                f"the highest of all {len(locations)} locations. Use this location "
                f"as a template for optimizing the others."
            ),
            recommendation=(
                f"Use '{strongest['name']}' as the model for optimizing other "
                f"locations. Replicate its completeness pattern across the fleet."
            ),
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=["multi-location"],
            tags=["per_location", "local_seo", "multi-location", "strongest"],
            evidence=[
                Evidence(
                    evidence_type="comparison",
                    value=f"Strongest: '{strongest['name']}' ({strongest['score']}/{strongest['total']})",
                    context="Use as template for other locations.",
                    source_label="Per-location scoring comparison",
                ),
            ],
            metadata={"strongest_location": strongest["name"]},
        ))

    return findings


# ============================================================================
# Internal helpers
# ============================================================================


def _get_archetype(profile: "BusinessProfile") -> str:
    """Extract the archetype string, defaulting to empty."""
    classification = getattr(profile, "classification", None)
    if classification is None:
        return ""
    return getattr(classification, "archetype", None) or ""


def _has_physical_presence(profile: "BusinessProfile") -> bool:
    """Determine if the business has any physical presence."""
    geo = profile.geography
    if geo.locations:
        return True
    if getattr(geo, "has_storefront", False):
        return True
    return False


def _find_channel(
    profile: "BusinessProfile",
    platform_name: str,
) -> Any:
    """Find a ChannelPresence by platform name (case-insensitive)."""
    target = platform_name.lower()
    for ch in profile.channels:
        if getattr(ch, "platform", "").lower() == target:
            return ch
    return None


def _normalize_phone(phone: str) -> str:
    """Strip a phone number to digits only for comparison."""
    return "".join(c for c in phone if c.isdigit())
