"""Trust and proof audit engine for the Kai Marketing OS.

Examines the breadth, depth, and specificity of a business's trust
signals -- testimonials, case studies, certifications, awards, team
visibility, guarantees, and social proof.  Identifies gaps in the trust
portfolio and recommends specific improvements.

For businesses that receive phone calls, evaluates whether AI
receptionist technology (KaiCalls) should be recommended to ensure no
lead goes unanswered.

Usage::

    from kai.audits.trust_proof import audit_trust_proof, score_trust_proof
    findings = audit_trust_proof(profile, connected_data=live_data)
    score = score_trust_proof(findings)
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

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CATEGORY = "trust_proof"

# Archetypes where certain checks are especially critical
_LOCAL_SERVICE_ARCHETYPES = {"local-service", "multi-location"}
_PROFESSIONAL_ARCHETYPES = {"professional-services"}

# Patterns that indicate vague praise (case-insensitive)
_VAGUE_PATTERNS: List[re.Pattern] = [
    re.compile(r"\bgreat (service|company|work|job|team|experience)\b", re.IGNORECASE),
    re.compile(r"\bhighly recommend\b", re.IGNORECASE),
    re.compile(r"\bvery (good|nice|professional|happy)\b", re.IGNORECASE),
    re.compile(r"\bamazing (service|company|work|job|team|experience)\b", re.IGNORECASE),
    re.compile(r"\bwonderful (service|company|work|job|team|experience)\b", re.IGNORECASE),
    re.compile(r"\bexcellent (service|company|work|job|team|experience)\b", re.IGNORECASE),
    re.compile(r"\b(love|loved) (them|it|this|working)\b", re.IGNORECASE),
    re.compile(r"\bwould (definitely )?use again\b", re.IGNORECASE),
    re.compile(r"\bbest (in town|around|ever)\b", re.IGNORECASE),
    re.compile(r"\b5 stars?\b", re.IGNORECASE),
]

# Patterns that indicate specific, high-quality testimony
_SPECIFIC_PATTERNS: List[re.Pattern] = [
    re.compile(r"\$[\d,]+", re.IGNORECASE),  # dollar amounts
    re.compile(r"\b\d+\s*(hours?|days?|weeks?|months?|years?|minutes?)\b", re.IGNORECASE),
    re.compile(r"\b\d+\s*%\b"),  # percentages
    re.compile(r"\bsaved?\b", re.IGNORECASE),
    re.compile(r"\bincreased?\b.*\b\d+", re.IGNORECASE),
    re.compile(r"\breduced?\b.*\b\d+", re.IGNORECASE),
    re.compile(r"\bbefore\b.*\bafter\b", re.IGNORECASE),
    re.compile(r"\bROI\b", re.IGNORECASE),
    re.compile(r"\brevenue\b", re.IGNORECASE),
]

# Guarantee-related keywords
_GUARANTEE_KEYWORDS = [
    "guarantee", "guaranteed", "warranty", "money-back", "money back",
    "satisfaction", "risk-free", "risk free", "refund", "no-risk",
]

# BBB/industry affiliation keywords
_AFFILIATION_KEYWORDS = [
    "bbb", "better business bureau", "chamber of commerce",
    "association", "affiliated", "member of", "accredited",
    "nari", "nahb", "nar", "aia", "asid",  # common trade associations
]

# AI receptionist / call handling keywords
_CALL_HANDLING_KEYWORDS = [
    "ai receptionist", "virtual receptionist", "call answering",
    "answering service", "call center", "auto-attendant",
    "kaicalls", "kai calls", "ivr", "call routing",
]


# ============================================================================
# Helper: archetype accessor
# ============================================================================

def _get_archetype(profile: BusinessProfile) -> Optional[str]:
    """Return the profile archetype, normalized to lowercase."""
    arch = getattr(profile.classification, "archetype", None)
    return arch.lower().strip() if arch else None


# ============================================================================
# Helper: parse GBP review data
# ============================================================================

def _parse_gbp_reviews(profile: BusinessProfile, connected_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Extract Google review count and rating from profile channels or connected data.

    Returns a dict with keys: ``found``, ``review_count``, ``rating``, ``source``.
    """
    result: Dict[str, Any] = {"found": False, "review_count": None, "rating": None, "source": None}

    # Check connected_data first (more authoritative)
    if connected_data:
        gbp_data = connected_data.get("gbp") or connected_data.get("google_business_profile") or {}
        if gbp_data:
            review_count = gbp_data.get("review_count") or gbp_data.get("reviews_count")
            rating = gbp_data.get("rating") or gbp_data.get("average_rating")
            if review_count is not None or rating is not None:
                result["found"] = True
                result["review_count"] = int(review_count) if review_count is not None else None
                result["rating"] = float(rating) if rating is not None else None
                result["source"] = "connected_data"
                return result

    # Fall back to channel notes parsing
    for channel in profile.channels:
        platform = (channel.platform or "").lower()
        if platform in ("gbp", "google_business_profile", "google business profile", "google"):
            notes = channel.notes or ""
            # Try to parse review count
            count_match = re.search(r"(\d+)\s*reviews?", notes, re.IGNORECASE)
            if count_match:
                result["review_count"] = int(count_match.group(1))
                result["found"] = True

            # Try to parse rating
            rating_match = re.search(r"(\d+\.?\d*)\s*(?:star|rating|/\s*5)", notes, re.IGNORECASE)
            if rating_match:
                result["rating"] = float(rating_match.group(1))
                result["found"] = True

            if result["found"]:
                result["source"] = "channel_notes"
                return result

    return result


# ============================================================================
# Helper: check testimonial quality
# ============================================================================

def _assess_testimonial_specificity(content: str) -> str:
    """Classify a testimonial as 'specific', 'moderate', or 'vague'."""
    specific_hits = sum(1 for p in _SPECIFIC_PATTERNS if p.search(content))
    vague_hits = sum(1 for p in _VAGUE_PATTERNS if p.search(content))

    if specific_hits >= 2:
        return "specific"
    if specific_hits >= 1 and vague_hits <= 1:
        return "moderate"
    if vague_hits >= 1 and specific_hits == 0:
        return "vague"
    # Short testimonials without any signal are assumed vague
    if len(content.split()) < 15:
        return "vague"
    return "moderate"


# ============================================================================
# Helper: search text fields for keywords
# ============================================================================

def _profile_contains_keywords(profile: BusinessProfile, keywords: List[str]) -> bool:
    """Search trust signals, constraints, and raw notes for any keyword."""
    searchable_texts: List[str] = []

    # Trust signals content
    for t in profile.trust.testimonials:
        searchable_texts.append(t.content or "")
        searchable_texts.append(t.title or "")
    for cs in profile.trust.case_studies:
        searchable_texts.append(cs.content or "")
        searchable_texts.append(cs.title or "")

    # Certifications and awards
    searchable_texts.extend(profile.trust.certifications)
    searchable_texts.extend(profile.trust.awards)

    # Constraints
    searchable_texts.extend(profile.constraints.compliance_notes)
    searchable_texts.extend(profile.constraints.claims_restrictions)
    if profile.constraints.brand_voice_notes:
        searchable_texts.append(profile.constraints.brand_voice_notes)

    # Raw notes
    if profile.raw_notes:
        searchable_texts.append(profile.raw_notes)

    combined = " ".join(searchable_texts).lower()
    return any(kw.lower() in combined for kw in keywords)


# ============================================================================
# Individual Checks
# ============================================================================

def _check_testimonial_count(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 1: Testimonial Count and Quality."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)
    testimonials = profile.trust.testimonials

    if not testimonials:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="testimonials",
            severity=FindingSeverity.HIGH.value,
            title="No testimonials on file",
            description=(
                "Social proof from real customers is essential for conversion. "
                "Visitors need third-party validation before trusting a business "
                "with their money or time. Without testimonials, the website "
                "relies entirely on self-reported claims."
            ),
            recommendation=(
                "Collect testimonials that include specific results, timeframes, "
                "and the customer's situation before working with you. "
                "Start by emailing your 5 happiest customers and asking for "
                "a short quote about their experience."
            ),
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="0 testimonials found in business profile",
                context="Industry benchmark: 5-10 diverse testimonials for credible social proof",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "testimonials", "social_proof"],
        ))
        return findings

    n = len(testimonials)
    if n < 3:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="testimonials",
            severity=FindingSeverity.MEDIUM.value,
            title=f"Only {n} testimonial{'s' if n != 1 else ''} on file",
            description=(
                f"Only {n} testimonial{'s' if n != 1 else ''} found. "
                "Aim for at least 5-10 diverse testimonials covering different "
                "services, customer types, and outcomes. More testimonials build "
                "a stronger trust portfolio."
            ),
            recommendation=(
                "Expand testimonial collection to cover different service types "
                "and customer demographics. Ask customers to describe their "
                "specific problem, the experience, and the measurable result."
            ),
            evidence=[Evidence(
                evidence_type="metric",
                value=str(n),
                context=f"{n} testimonial{'s' if n != 1 else ''} found; target is 5-10 minimum",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "testimonials", "social_proof"],
        ))

    # Assess quality of existing testimonials
    quality_counts = {"specific": 0, "moderate": 0, "vague": 0}
    for t in testimonials:
        quality = _assess_testimonial_specificity(t.content or "")
        quality_counts[quality] += 1

    vague_ratio = quality_counts["vague"] / max(len(testimonials), 1)
    if vague_ratio > 0.5 and len(testimonials) >= 2:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="testimonial_quality",
            severity=FindingSeverity.MEDIUM.value,
            title="Testimonials lack specificity",
            description=(
                f"{quality_counts['vague']} of {len(testimonials)} testimonials use "
                "general praise without specific results, numbers, or outcomes. "
                "Specific testimonials convert 3-5x better than generic praise "
                "like 'Great service!' or 'Highly recommend!'"
            ),
            recommendation=(
                "When collecting testimonials, ask customers to describe: "
                "(1) the problem they had before, (2) the experience of working "
                "with you, and (3) the specific result -- including numbers, "
                "timeframes, and dollar amounts where possible."
            ),
            evidence=[Evidence(
                evidence_type="comparison",
                value=f"Vague: {quality_counts['vague']}, Moderate: {quality_counts['moderate']}, Specific: {quality_counts['specific']}",
                context="Specific > 'Great service!' -- numbers and outcomes convert better",
                source_label="Testimonial content analysis",
            )],
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "testimonials", "quality", "social_proof"],
        ))

    return findings


def _check_case_studies(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 2: Case Study Presence."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)
    case_studies = profile.trust.case_studies

    if not case_studies:
        # Severity depends on archetype
        if archetype in _PROFESSIONAL_ARCHETYPES:
            severity = FindingSeverity.HIGH.value
            title = "No case studies -- professional services firms need documented proof"
            desc = (
                "Professional services firms sell expertise and outcomes. "
                "Without case studies, prospects have no evidence of past "
                "results. Case studies are the single strongest trust asset "
                "for professional services businesses."
            )
        elif archetype == "ecommerce":
            severity = FindingSeverity.MEDIUM.value
            title = "No case studies or customer stories"
            desc = (
                "Consider creating 'customer story' content that showcases "
                "how real customers use your products. Product-focused case "
                "studies reduce purchase anxiety and increase average order value."
            )
        elif archetype in _LOCAL_SERVICE_ARCHETYPES:
            severity = FindingSeverity.MEDIUM.value
            title = "No case studies or project showcases"
            desc = (
                "Before/after documentation builds trust for service businesses. "
                "Prospects want to see what you've done for others before "
                "committing their home or business to your care."
            )
        else:
            severity = FindingSeverity.MEDIUM.value
            title = "No case studies on file"
            desc = (
                "Case studies are a powerful trust tool. They provide third-party "
                "evidence of results and help prospects envision working with you."
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="case_studies",
            severity=severity,
            title=title,
            description=desc,
            recommendation=(
                "Create case studies in Problem > Solution > Results format "
                "with specific metrics. Start with your 3 best client outcomes "
                "and include real numbers, timeframes, and named results."
            ),
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="0 case studies found in business profile",
                context="Target: 3+ case studies covering different service types",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.SIGNIFICANT.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "case_studies", "social_proof"],
        ))

    elif len(case_studies) < 3:
        n = len(case_studies)
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="case_studies",
            severity=FindingSeverity.LOW.value,
            title=f"Only {n} case stud{'ies' if n != 1 else 'y'}",
            description=(
                f"Only {n} case stud{'ies' if n != 1 else 'y'} on file. "
                "Expand to cover different service types and customer profiles "
                "so prospects can find a scenario that matches their situation."
            ),
            recommendation=(
                "Create case studies in Problem > Solution > Results format "
                "with specific metrics. Cover different service categories "
                "and customer segments."
            ),
            evidence=[Evidence(
                evidence_type="metric",
                value=str(n),
                context=f"{n} case stud{'ies' if n != 1 else 'y'} found; target is 3+",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.SIGNIFICANT.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "case_studies", "social_proof"],
        ))

    return findings


def _check_credentials(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 3: Credentials and Certifications Displayed."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)
    has_certs = bool(profile.trust.certifications)
    has_licenses = bool(profile.trust.licenses)

    if not has_certs and not has_licenses:
        if archetype in _LOCAL_SERVICE_ARCHETYPES:
            severity = FindingSeverity.HIGH.value
            title = "No licenses or certifications on file"
            desc = (
                "Credentials are a primary trust signal for service businesses. "
                "Customers need to know you are licensed and certified before "
                "letting you into their home or business."
            )
        elif archetype in _PROFESSIONAL_ARCHETYPES:
            severity = FindingSeverity.HIGH.value
            title = "No professional certifications listed"
            desc = (
                "Professional services buyers evaluate credentials before "
                "engaging. Listing certifications, degrees, and professional "
                "affiliations is essential for credibility in this space."
            )
        else:
            severity = FindingSeverity.MEDIUM.value
            title = "No certifications or credentials on file"
            desc = (
                "Certifications and credentials serve as third-party trust "
                "signals. Even non-regulated businesses benefit from displaying "
                "relevant professional certifications."
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="credentials",
            severity=severity,
            title=title,
            description=desc,
            recommendation=(
                "Display license numbers, certification badges, and "
                "professional affiliations prominently on the website header "
                "or footer. Add certification logos to key landing pages."
            ),
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="0 certifications and 0 licenses found",
                context="Credentials are a primary trust factor for service and professional businesses",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "credentials", "certifications"],
        ))

    else:
        cert_count = len(profile.trust.certifications)
        license_count = len(profile.trust.licenses)
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="credentials",
            severity=FindingSeverity.INFO.value,
            title="Certifications and licenses found",
            description=(
                f"{cert_count} certification{'s' if cert_count != 1 else ''} and "
                f"{license_count} license{'s' if license_count != 1 else ''} on file. "
                "Ensure they are prominently displayed on the website header "
                "or footer, not buried on an interior page."
            ),
            recommendation=(
                "Display license numbers, certification badges, and "
                "professional affiliations prominently on the website header "
                "or footer and on key conversion pages."
            ),
            evidence=[Evidence(
                evidence_type="metric",
                value=f"Certifications: {cert_count}, Licenses: {license_count}",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "credentials", "certifications"],
        ))

    return findings


def _check_team_visibility(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 4: Team Photos and Visibility."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)
    team_size = profile.trust.team_size

    if team_size is None:
        findings.append(create_missing_data_finding(
            category=CATEGORY,
            field_path="trust.team_size",
            impact_description=(
                "Team size is unknown. Cannot assess whether the business "
                "is presenting its team to build personal trust with prospects."
            ),
            how_to_provide=(
                "Set trust.team_size to the approximate size range "
                "(e.g., '1-5', '6-20', '21-50')."
            ),
        ))
        return findings

    # Team size is set -- check for team-related trust signals
    has_team_signal = False
    for t in profile.trust.testimonials + profile.trust.case_studies:
        content_lower = (t.content or "").lower() + " " + (t.title or "").lower()
        if any(word in content_lower for word in ["team", "staff", "crew", "employees", "technician"]):
            has_team_signal = True
            break

    # Also check raw notes for team page indicators
    if profile.raw_notes:
        raw_lower = profile.raw_notes.lower()
        if any(word in raw_lower for word in ["team page", "about us", "headshot", "bio", "meet the team"]):
            has_team_signal = True

    if not has_team_signal:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="team_visibility",
            severity=FindingSeverity.MEDIUM.value,
            title=f"Team size is {team_size} but no team visibility signals",
            description=(
                f"Team size is listed as {team_size} but there are no "
                "signals that the team is visible to prospects. "
                "Visitors want to know who they're hiring or buying from. "
                "Faceless businesses convert lower than businesses with "
                "visible, named team members."
            ),
            recommendation=(
                "Add professional headshots and brief bios for key team "
                "members to the website. At minimum, include the owner/founder "
                "and any client-facing team members on an 'About Us' page."
            ),
            evidence=[Evidence(
                evidence_type="text",
                value=f"Team size: {team_size}; no team-related trust signals detected",
                context="Personal visibility builds trust -- faceless businesses convert lower",
                source_label="Trust profile + signal scan",
            )],
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.INFERRED.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "team", "visibility"],
        ))

    return findings


def _check_years_in_business(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 5: Years in Business."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)
    years = profile.trust.years_in_business

    if years is None:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="longevity",
            severity=FindingSeverity.LOW.value,
            title="Years in business not stated",
            description=(
                "Longevity is a powerful trust signal. Customers prefer "
                "businesses that have been operating for years over unknown "
                "newcomers. If the business has been around for a while, "
                "it should be prominently stated."
            ),
            recommendation=(
                "State years in business in the website header, about page, "
                "and ad copy. Even '2+ years' is better than silence."
            ),
            evidence=[Evidence(
                evidence_type="missing_data",
                value="trust.years_in_business",
                context="Longevity is a trust multiplier -- state it if available",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "longevity"],
        ))
        return findings

    if years >= 10:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="longevity",
            severity=FindingSeverity.INFO.value,
            title=f"{years} years in business -- strong differentiator",
            description=(
                f"{years} years in business is a powerful trust signal. "
                "This longevity should be featured in headlines, ad copy, "
                "and key landing pages. Few competitors can match this."
            ),
            recommendation=(
                f"Feature '{years} years of experience' in website header, "
                "Google Ads headlines, Meta ad copy, and the about page. "
                "Use it as a competitive differentiator."
            ),
            evidence=[Evidence(
                evidence_type="metric",
                value=str(years),
                context=f"{years} years -- feature this prominently as a competitive advantage",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "longevity", "differentiator"],
        ))
    elif years >= 5:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="longevity",
            severity=FindingSeverity.INFO.value,
            title=f"{years} years in business -- display as social proof",
            description=(
                f"{years} years in business is a solid trust signal. "
                "Prominently display this across marketing channels to "
                "build credibility with prospects."
            ),
            recommendation=(
                "State years in business in the website header, about page, "
                "and ad copy. Pair with review count for compounding trust."
            ),
            evidence=[Evidence(
                evidence_type="metric",
                value=str(years),
                context=f"{years} years -- display prominently as social proof",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "longevity"],
        ))
    else:
        # Less than 5 years -- no finding needed, but no action either
        pass

    return findings


def _check_guarantee(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 6: Guarantee/Warranty Visibility."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)

    has_guarantee = _profile_contains_keywords(profile, _GUARANTEE_KEYWORDS)

    if not has_guarantee:
        # Build recommendation noting claims restrictions if applicable
        rec = (
            "Define and prominently display a satisfaction guarantee, "
            "warranty, or money-back promise. Even a simple 'We'll make "
            "it right' statement reduces purchase friction."
        )
        if profile.constraints.claims_restrictions:
            restrictions_summary = "; ".join(profile.constraints.claims_restrictions[:3])
            rec += (
                f" Note: comply with claims restrictions ({restrictions_summary}). "
                "Frame the guarantee in compliant language."
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="guarantee",
            severity=FindingSeverity.MEDIUM.value,
            title="No guarantee or warranty language found",
            description=(
                "A clear guarantee reduces purchase risk and increases "
                "conversion. Visitors who are on the fence will convert when "
                "they know the downside is protected. No guarantee language "
                "was found in the business profile."
            ),
            recommendation=rec,
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="No guarantee, warranty, or risk-reversal language detected",
                context="Risk reversal is one of the highest-impact conversion levers",
                source_label="Profile keyword scan",
            )],
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.INFERRED.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "guarantee", "risk_reversal", "conversion"],
        ))

    return findings


def _check_insurance_licensing(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 7: Insurance and Licensing (local-service, multi-location)."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)

    if archetype not in _LOCAL_SERVICE_ARCHETYPES:
        # Other archetypes: skip or produce INFO-level note
        if not profile.trust.insurance_details and not profile.trust.licenses:
            # Not relevant enough to flag for non-local archetypes
            pass
        return findings

    # Insurance check
    if not profile.trust.insurance_details:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="insurance",
            severity=FindingSeverity.HIGH.value,
            title="No insurance information on file",
            description=(
                "Customers need to know you're insured before letting you "
                "into their home or business. Lack of visible insurance "
                "information is a dealbreaker for many homeowners and "
                "property managers."
            ),
            recommendation=(
                "Add insurance details (general liability, workers' comp, "
                "bonding) to the website footer, about page, and Google "
                "Business Profile description. Include policy numbers "
                "or 'Fully Insured' badges."
            ),
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="No insurance details found in trust profile",
                context="Insurance is a top-3 trust factor for home service buyers",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype],
            tags=["trust", "insurance", "local_service"],
        ))
    else:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="insurance",
            severity=FindingSeverity.INFO.value,
            title="Insurance documented",
            description=(
                f"Insurance details on file: {profile.trust.insurance_details}. "
                "Ensure this information is displayed prominently on the "
                "website and Google Business Profile."
            ),
            recommendation=(
                "Display insurance details on the website header or footer "
                "and include in Google Business Profile description."
            ),
            evidence=[Evidence(
                evidence_type="text",
                value=profile.trust.insurance_details,
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype],
            tags=["trust", "insurance", "local_service"],
        ))

    # License check (local-service specific)
    if not profile.trust.licenses:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="licensing",
            severity=FindingSeverity.HIGH.value,
            title="No license information on file",
            description=(
                "License information is required by most states for regulated "
                "trades. Displaying license numbers is both a legal requirement "
                "and a powerful trust signal."
            ),
            recommendation=(
                "Add license numbers to the website footer, about page, and "
                "Google Business Profile. Include state license number "
                "for each applicable trade."
            ),
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="0 licenses found in trust profile",
                context="Required for regulated trades; trust signal for all service businesses",
                source_label="Trust profile",
            )],
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype],
            tags=["trust", "licensing", "local_service", "compliance"],
        ))

    return findings


def _check_affiliations(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 8: BBB/Industry Affiliations."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)

    has_affiliation = _profile_contains_keywords(profile, _AFFILIATION_KEYWORDS)

    if not has_affiliation:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="affiliations",
            severity=FindingSeverity.LOW.value,
            title="No industry affiliations or BBB membership noted",
            description=(
                "No BBB accreditation, chamber of commerce membership, or "
                "industry association affiliations were found. These serve "
                "as third-party credibility signals that reduce buyer "
                "uncertainty."
            ),
            recommendation=(
                "Consider BBB accreditation and industry association membership "
                "as trust multipliers. Display membership badges on the website "
                "and include in business descriptions."
            ),
            evidence=[Evidence(
                evidence_type="checklist_item",
                value="No BBB or industry affiliation keywords found in profile",
                context="Third-party affiliations serve as independent credibility signals",
                source_label="Profile keyword scan",
            )],
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.INFERRED.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "affiliations", "bbb", "credibility"],
        ))

    return findings


def _check_google_reviews(profile: BusinessProfile, connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]:
    """Check 9: Google Review Count and Rating."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)
    gbp_data = _parse_gbp_reviews(profile, connected_data)

    if not gbp_data["found"]:
        # Check if GBP channel exists at all
        has_gbp = any(
            (ch.platform or "").lower() in ("gbp", "google_business_profile", "google business profile", "google")
            for ch in profile.channels
        )
        if has_gbp:
            findings.append(create_missing_data_finding(
                category=CATEGORY,
                field_path="channels.gbp.review_data",
                impact_description=(
                    "GBP channel is listed but no review count or rating data "
                    "is available. Cannot benchmark review performance."
                ),
                how_to_provide=(
                    "Add review count and rating to the GBP channel notes "
                    "(e.g., '87 reviews, 4.7 rating') or connect the GBP "
                    "integration for automatic data."
                ),
                critical_gap=True,
            ))
        else:
            # No GBP channel at all
            if archetype in _LOCAL_SERVICE_ARCHETYPES:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.HIGH.value,
                    title="No Google Business Profile channel found",
                    description=(
                        "No GBP channel is listed for a local service business. "
                        "Google reviews are the primary trust signal for local "
                        "businesses and directly impact local search ranking."
                    ),
                    recommendation=(
                        "Claim and optimize a Google Business Profile immediately. "
                        "Start generating reviews through a systematic review "
                        "request process."
                    ),
                    evidence=[Evidence(
                        evidence_type="missing_data",
                        value="channels.gbp",
                        context="GBP is essential for local service businesses",
                        source_label="Channel list",
                    )],
                    estimated_impact=ImpactLevel.HIGH.value,
                    effort=EffortLevel.MODERATE.value,
                    source=FindingSource.STATIC.value,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "gbp", "local_seo"],
                ))
        return findings

    review_count = gbp_data["review_count"]
    rating = gbp_data["rating"]
    source = FindingSource.CONNECTED.value if gbp_data["source"] == "connected_data" else FindingSource.STATIC.value

    # Review count benchmarks by archetype
    if review_count is not None:
        if archetype in _LOCAL_SERVICE_ARCHETYPES:
            if review_count < 20:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.HIGH.value,
                    title=f"Only {review_count} Google reviews",
                    description=(
                        f"Only {review_count} Google reviews for a local service business. "
                        "Competitors likely have 50-100+. Low review count signals "
                        "inexperience or low volume to prospects researching options."
                    ),
                    recommendation=(
                        "Implement a systematic review generation process. Send "
                        "a review request via text/email within 24 hours of "
                        "service completion. Target 2-3 new reviews per week."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Local service benchmark: 50+ reviews for credibility, 100+ for dominance",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.HIGH.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))
            elif review_count < 50:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.MEDIUM.value,
                    title=f"{review_count} Google reviews -- good start",
                    description=(
                        f"{review_count} Google reviews is a solid foundation but "
                        "not yet dominant. Competitors in established markets often "
                        "have 100+. Continuing review velocity is critical."
                    ),
                    recommendation=(
                        "Maintain review generation momentum. Target 50+ reviews, "
                        "then expand to other platforms (Yelp, industry-specific "
                        "sites) for broader trust coverage."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Good start; target 50+ for strong local credibility",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))
            elif review_count < 100:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.LOW.value,
                    title=f"{review_count} Google reviews -- expand to other platforms",
                    description=(
                        f"{review_count} Google reviews provides strong local "
                        "credibility. Consider expanding review presence to "
                        "Yelp, Facebook, and industry-specific review platforms."
                    ),
                    recommendation=(
                        "Diversify review platforms. Add Yelp, Facebook, and "
                        "industry-specific sites to the review generation process."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Strong count; diversify across platforms for maximum trust",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.LOW.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))
            else:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.INFO.value,
                    title=f"{review_count} Google reviews -- dominant position",
                    description=(
                        f"{review_count} Google reviews is a dominant local position. "
                        "Maintain review velocity and respond to all reviews "
                        "to sustain this advantage."
                    ),
                    recommendation=(
                        "Maintain review velocity and respond to every review "
                        "within 24 hours. Leverage this review count in ad copy "
                        "and website headers."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Dominant review count -- maintain and leverage",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.LOW.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))

        elif archetype in _PROFESSIONAL_ARCHETYPES:
            if review_count < 10:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.HIGH.value,
                    title=f"Only {review_count} Google reviews",
                    description=(
                        f"Only {review_count} Google reviews for a professional "
                        "services business. Even 10-15 reviews builds meaningful "
                        "trust in the professional services space."
                    ),
                    recommendation=(
                        "Request reviews from satisfied clients at project "
                        "completion. Professional services reviews carry high "
                        "weight -- even 10 quality reviews makes a difference."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Professional services benchmark: 10+ for credibility, 30+ for strong",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.HIGH.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))
            elif review_count < 30:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.MEDIUM.value,
                    title=f"{review_count} Google reviews -- solid for professional services",
                    description=(
                        f"{review_count} Google reviews is a good foundation. "
                        "Continue generating reviews and diversify to "
                        "industry-specific platforms."
                    ),
                    recommendation=(
                        "Continue review generation. Add industry-specific "
                        "review platforms (Avvo, Clutch, G2, etc.) to build "
                        "multi-platform trust."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Solid count; expand to industry-specific platforms",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))
            else:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.INFO.value,
                    title=f"{review_count} Google reviews -- strong position",
                    description=(
                        f"{review_count} Google reviews is a strong position "
                        "for professional services. Maintain velocity and "
                        "leverage in marketing materials."
                    ),
                    recommendation=(
                        "Maintain review velocity. Highlight review count "
                        "and rating in proposals, website, and ad copy."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Strong review count for professional services",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.LOW.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))

        else:
            # Generic archetype: use local-service thresholds with softer severity
            if review_count < 20:
                findings.append(create_finding(
                    category=CATEGORY,
                    subcategory="google_reviews",
                    severity=FindingSeverity.MEDIUM.value,
                    title=f"Only {review_count} Google reviews",
                    description=(
                        f"Only {review_count} Google reviews. Building review "
                        "count improves trust across all channels."
                    ),
                    recommendation=(
                        "Implement a systematic review generation process. "
                        "Target 2+ new reviews per week."
                    ),
                    evidence=[Evidence(
                        evidence_type="metric",
                        value=str(review_count),
                        context="Low review count; systematic generation needed",
                        source_label="Google Business Profile",
                    )],
                    estimated_impact=ImpactLevel.MEDIUM.value,
                    effort=EffortLevel.ONGOING.value,
                    source=source,
                    archetype_relevance=[archetype] if archetype else [],
                    tags=["trust", "google_reviews", "review_count"],
                ))

    # Rating assessment (applies to all archetypes)
    if rating is not None:
        if rating < 4.0:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="google_rating",
                severity=FindingSeverity.HIGH.value,
                title=f"Google rating below 4.0 ({rating})",
                description=(
                    f"Google rating is {rating}/5.0, which is below the "
                    "critical 4.0 threshold. Ratings below 4.0 actively deter "
                    "prospects. Address negative reviews, identify service "
                    "quality issues, and implement a reputation recovery plan."
                ),
                recommendation=(
                    "Address negative reviews and improve service quality. "
                    "Respond professionally to all negative reviews. Identify "
                    "root causes of complaints and fix operational issues."
                ),
                evidence=[Evidence(
                    evidence_type="metric",
                    value=str(rating),
                    context="Below 4.0 is a trust red flag -- prospects actively avoid sub-4.0 businesses",
                    source_label="Google Business Profile",
                )],
                estimated_impact=ImpactLevel.HIGH.value,
                effort=EffortLevel.SIGNIFICANT.value,
                source=source,
                archetype_relevance=[archetype] if archetype else [],
                tags=["trust", "google_reviews", "rating", "reputation"],
            ))
        elif rating < 4.5:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="google_rating",
                severity=FindingSeverity.MEDIUM.value,
                title=f"Google rating is {rating} -- target 4.5+",
                description=(
                    f"Google rating is {rating}/5.0. This is adequate but "
                    "4.5+ is the trust sweet spot where conversion rates "
                    "measurably increase. Focus on review velocity and "
                    "responding to every review."
                ),
                recommendation=(
                    "Target 4.5+ through increased review velocity from "
                    "happy customers and prompt, professional responses to "
                    "all reviews (positive and negative)."
                ),
                evidence=[Evidence(
                    evidence_type="metric",
                    value=str(rating),
                    context="4.0-4.4 is adequate; 4.5+ is the trust conversion threshold",
                    source_label="Google Business Profile",
                )],
                estimated_impact=ImpactLevel.MEDIUM.value,
                effort=EffortLevel.ONGOING.value,
                source=source,
                archetype_relevance=[archetype] if archetype else [],
                tags=["trust", "google_reviews", "rating"],
            ))
        else:
            findings.append(create_finding(
                category=CATEGORY,
                subcategory="google_rating",
                severity=FindingSeverity.INFO.value,
                title=f"Google rating is {rating} -- excellent",
                description=(
                    f"Google rating is {rating}/5.0. This is an excellent "
                    "trust signal. Maintain this through continued review "
                    "generation and prompt responses to all reviews."
                ),
                recommendation=(
                    "Maintain current rating through continued review "
                    "generation. Feature the rating in ad copy, website "
                    "headers, and email signatures."
                ),
                evidence=[Evidence(
                    evidence_type="metric",
                    value=str(rating),
                    context="Excellent rating -- maintain and leverage in marketing",
                    source_label="Google Business Profile",
                )],
                estimated_impact=ImpactLevel.LOW.value,
                effort=EffortLevel.ONGOING.value,
                source=source,
                archetype_relevance=[archetype] if archetype else [],
                tags=["trust", "google_reviews", "rating"],
            ))

    return findings


def _check_social_proof_specificity(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 10: Social Proof Specificity (aggregated across all trust signals)."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)

    # Collect all textual trust signals
    all_signals: List[str] = []
    for t in profile.trust.testimonials:
        all_signals.append(t.content or "")
    for cs in profile.trust.case_studies:
        all_signals.append(cs.content or "")

    if not all_signals:
        # Already covered by testimonial and case study checks
        return findings

    quality_counts = {"specific": 0, "moderate": 0, "vague": 0}
    for text in all_signals:
        if not text.strip():
            quality_counts["vague"] += 1
            continue
        quality = _assess_testimonial_specificity(text)
        quality_counts[quality] += 1

    total = len(all_signals)
    vague_count = quality_counts["vague"]
    vague_ratio = vague_count / max(total, 1)

    # Only flag if we have enough signals AND most are vague
    if total >= 3 and vague_ratio > 0.6:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="proof_specificity",
            severity=FindingSeverity.MEDIUM.value,
            title="Social proof lacks specificity across the board",
            description=(
                f"{vague_count} of {total} social proof items are vague or "
                "lack specific results, numbers, and outcomes. Specific "
                "proof converts 3-5x better than general praise."
            ),
            recommendation=(
                "When collecting testimonials, ask customers to describe: "
                "the problem, the experience, and the specific result. "
                "Rewrite case studies to include measurable outcomes."
            ),
            evidence=[Evidence(
                evidence_type="comparison",
                value=f"Vague: {vague_count}/{total}, Specific: {quality_counts['specific']}/{total}",
                context="Specific results and numbers are the strongest form of social proof",
                source_label="Aggregated social proof analysis",
            )],
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.MODERATE.value,
            source=FindingSource.STATIC.value,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "social_proof", "specificity", "quality"],
        ))

    return findings


def _check_kaicalls_phone_capture(profile: BusinessProfile) -> List[AuditFinding]:
    """Check 11: KaiCalls Phone Lead Capture Assessment."""
    findings: List[AuditFinding] = []
    archetype = _get_archetype(profile)
    phone = getattr(profile.identity, "phone", None)

    if not phone:
        # No phone on file -- skip this check for non-phone businesses
        return findings

    has_call_handling = _profile_contains_keywords(profile, _CALL_HANDLING_KEYWORDS)

    if has_call_handling:
        # Already has some form of call handling -- no finding
        return findings

    operator_hours = getattr(profile.operator, "operator_hours_per_week", None)

    if archetype in _LOCAL_SERVICE_ARCHETYPES:
        # Determine severity: CRITICAL if operator capacity is low, else HIGH
        if operator_hours is not None and operator_hours < 10:
            severity = FindingSeverity.CRITICAL.value
            title = "No AI phone receptionist -- calls almost certainly being missed"
            desc = (
                "This local service business has a phone number but no AI "
                "receptionist or call handling system, and operator capacity "
                f"is only {operator_hours} hours/week. Local service businesses "
                "miss 30-60% of incoming calls. With limited operator "
                "availability, the miss rate is likely even higher. Missed "
                "calls are lost leads that go straight to competitors."
            )
        else:
            severity = FindingSeverity.HIGH.value
            title = "No AI phone receptionist -- calls are likely being missed"
            desc = (
                "This local service business has a phone number but no AI "
                "receptionist or call handling system. Local service "
                "businesses miss 30-60% of incoming calls. Missed calls "
                "are lost leads. An AI receptionist ensures every call is "
                "answered, qualified, and routed 24/7."
            )

        findings.append(create_finding(
            category=CATEGORY,
            subcategory="phone_lead_capture",
            severity=severity,
            title=title,
            description=desc,
            recommendation=(
                "Implement KaiCalls AI receptionist (kaicalls.com) for "
                "24/7 call handling, after-hours answering, and lead "
                "qualification. KaiCalls answers every call within 2 rings, "
                "qualifies the lead, books appointments, and sends "
                "instant notifications -- no missed calls, no lost leads."
            ),
            evidence=[Evidence(
                evidence_type="text",
                value=f"Phone: {phone}; No AI receptionist or call handling detected",
                context="Local service businesses miss 30-60% of calls without call handling technology",
                source_label="Profile phone + keyword scan",
            )],
            estimated_impact=ImpactLevel.HIGH.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.INFERRED.value,
            kaicalls_relevant=True,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "phone", "kaicalls", "lead_capture", "ai_receptionist"],
        ))

    elif archetype in _PROFESSIONAL_ARCHETYPES:
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="phone_lead_capture",
            severity=FindingSeverity.MEDIUM.value,
            title="Consider AI receptionist for after-hours inquiry handling",
            description=(
                "Professional services business with a phone number but no "
                "AI receptionist or call handling system. Prospective clients "
                "often call outside business hours, especially for urgent "
                "matters. An AI receptionist handles after-hours inquiries "
                "and initial lead qualification."
            ),
            recommendation=(
                "Implement KaiCalls AI receptionist (kaicalls.com) for "
                "after-hours answering and initial lead qualification. "
                "Ensure high-value inquiries are captured and routed "
                "even when the office is closed."
            ),
            evidence=[Evidence(
                evidence_type="text",
                value=f"Phone: {phone}; No AI receptionist detected",
                context="Professional services prospects call after hours for urgent needs",
                source_label="Profile phone + keyword scan",
            )],
            estimated_impact=ImpactLevel.MEDIUM.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.INFERRED.value,
            kaicalls_relevant=True,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "phone", "kaicalls", "lead_capture", "ai_receptionist"],
        ))

    else:
        # Other archetypes with phone: lower-priority recommendation
        findings.append(create_finding(
            category=CATEGORY,
            subcategory="phone_lead_capture",
            severity=FindingSeverity.LOW.value,
            title="Phone number present -- consider AI call handling",
            description=(
                "A phone number is listed but no AI receptionist or call "
                "handling system was detected. Missed calls are missed "
                "revenue, regardless of business type."
            ),
            recommendation=(
                "Evaluate whether inbound calls are a meaningful lead "
                "channel. If so, implement KaiCalls AI receptionist "
                "(kaicalls.com) for 24/7 call handling."
            ),
            evidence=[Evidence(
                evidence_type="text",
                value=f"Phone: {phone}; No AI receptionist detected",
                source_label="Profile phone + keyword scan",
            )],
            estimated_impact=ImpactLevel.LOW.value,
            effort=EffortLevel.QUICK_WIN.value,
            source=FindingSource.INFERRED.value,
            kaicalls_relevant=True,
            archetype_relevance=[archetype] if archetype else [],
            tags=["trust", "phone", "kaicalls", "lead_capture"],
        ))

    return findings


# ============================================================================
# Main entry point
# ============================================================================

def audit_trust_proof(
    profile: BusinessProfile,
    connected_data: Optional[Dict[str, Any]] = None,
) -> List[AuditFinding]:
    """Run a comprehensive trust and proof audit on a business profile.

    Examines 11 dimensions of trust: testimonials, case studies,
    credentials, team visibility, years in business, guarantees,
    insurance/licensing, affiliations, Google reviews, social proof
    specificity, and phone lead capture (KaiCalls).

    Parameters
    ----------
    profile:
        The ``BusinessProfile`` to audit.
    connected_data:
        Optional dictionary of live integration data (e.g., GBP review
        data, website scrape data).  Keys are integration names, values
        are dictionaries of integration-specific data.

    Returns
    -------
    List[AuditFinding]
        All trust and proof findings, sorted by severity (most severe first).
    """
    findings: List[AuditFinding] = []

    # Run all 11 checks
    findings.extend(_check_testimonial_count(profile))         # Check 1 (also covers part of Check 10)
    findings.extend(_check_case_studies(profile))              # Check 2
    findings.extend(_check_credentials(profile))               # Check 3
    findings.extend(_check_team_visibility(profile))           # Check 4
    findings.extend(_check_years_in_business(profile))         # Check 5
    findings.extend(_check_guarantee(profile))                 # Check 6
    findings.extend(_check_insurance_licensing(profile))       # Check 7
    findings.extend(_check_affiliations(profile))              # Check 8
    findings.extend(_check_google_reviews(profile, connected_data))  # Check 9
    findings.extend(_check_social_proof_specificity(profile))  # Check 10
    findings.extend(_check_kaicalls_phone_capture(profile))    # Check 11

    # Deduplicate findings by ID (defensive; each factory call should produce unique IDs)
    seen_ids: set = set()
    deduped: List[AuditFinding] = []
    for f in findings:
        if f.id not in seen_ids:
            seen_ids.add(f.id)
            deduped.append(f)
    findings = deduped

    # Sort by severity (most severe first)
    severity_order = {
        FindingSeverity.CRITICAL.value: 0,
        FindingSeverity.HIGH.value: 1,
        FindingSeverity.MEDIUM.value: 2,
        FindingSeverity.LOW.value: 3,
        FindingSeverity.INFO.value: 4,
    }
    findings.sort(key=lambda f: severity_order.get(f.severity, 99))

    return findings


# ============================================================================
# Scoring function
# ============================================================================

def score_trust_proof(findings: List[AuditFinding]) -> float:
    """Compute a 0-100 trust and proof score from audit findings.

    Scoring formula::

        score = 100 - (critical * 25 + high * 15 + medium * 8 + low * 3)

    The score is clamped to [0, 100].  INFO-level and MISSING_DATA
    findings do not reduce the score.

    Parameters
    ----------
    findings:
        List of ``AuditFinding`` from ``audit_trust_proof()``.

    Returns
    -------
    float
        Trust and proof score in the range [0, 100].
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
