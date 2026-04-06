"""Module activation logic for the Kai Marketing OS.

Analyzes a ``BusinessProfile`` and determines which archetype applies,
which overlays should be layered on, and which modules should be activated.
This is the intelligence layer that translates raw business data into an
operational configuration.

Usage::

    from kai.archetypes.activation import activate

    result = activate(profile)
    print(result.archetype_id)      # "local-service"
    print(result.active_modules)    # ["local_seo", "review_management", ...]
    print(result.reasoning)         # human-readable decision log
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from kai.models.business_profile import BusinessProfile

# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ModuleDefinition:
    """A marketing module that can be activated for a business.

    Parameters
    ----------
    id:
        Unique module identifier, e.g. ``"review_management"``.
    name:
        Human-readable display name.
    description:
        What this module does when active.
    activation_conditions:
        Human-readable conditions that trigger this module.
    required_integrations:
        External integrations needed for this module to function.
    provides_capabilities:
        What this module enables when active.
    """

    id: str
    name: str
    description: str
    activation_conditions: List[str] = field(default_factory=list)
    required_integrations: List[str] = field(default_factory=list)
    provides_capabilities: List[str] = field(default_factory=list)


@dataclass
class ActivationResult:
    """Complete activation configuration for a business.

    Parameters
    ----------
    profile_id:
        The ``BusinessProfile.id`` this activation was computed for.
    archetype_id:
        Selected archetype identifier.
    archetype_name:
        Human-readable display name for the archetype.
    overlay_ids:
        Overlays applied on top of the archetype.
    active_modules:
        Module IDs activated for this profile.
    disabled_modules:
        Module IDs explicitly disabled (with reasons in ``reasoning``).
    reasoning:
        Human-readable explanation for every activation decision.
    confidence:
        ``"high"``, ``"medium"``, or ``"low"`` based on how the
        archetype was determined.
    missing_data_for_activation:
        Profile fields that, if populated, would refine the activation.
    recommended_next_steps:
        Operator actions that would improve the configuration.
    """

    profile_id: str
    archetype_id: str
    archetype_name: str
    overlay_ids: List[str] = field(default_factory=list)
    active_modules: List[str] = field(default_factory=list)
    disabled_modules: List[str] = field(default_factory=list)
    reasoning: List[str] = field(default_factory=list)
    confidence: str = "medium"
    missing_data_for_activation: List[str] = field(default_factory=list)
    recommended_next_steps: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants — industry lists used by determine_archetype
# ---------------------------------------------------------------------------

_PROFESSIONAL_SERVICES_INDUSTRIES = frozenset({
    "legal",
    "law",
    "consulting",
    "accounting",
    "finance",
    "financial_services",
    "architecture",
    "engineering",
    "marketing",
    "advertising",
    "recruiting",
    "staffing",
    "it_services",
    "management_consulting",
    "tax",
    "insurance",
    "wealth_management",
    "real_estate_brokerage",
})

_LOCAL_SERVICE_INDUSTRIES = frozenset({
    "home_services",
    "construction",
    "beauty",
    "automotive",
    "cleaning",
    "plumbing",
    "hvac",
    "electrical",
    "landscaping",
    "roofing",
    "painting",
    "pest_control",
    "locksmith",
    "moving",
    "handyman",
    "flooring",
    "remodeling",
    "garage_door",
    "tree_service",
    "pressure_washing",
    "window_cleaning",
    "pool_service",
    "appliance_repair",
    "fencing",
    "septic",
    "demolition",
    "concrete",
    "paving",
    "salon",
    "spa",
    "barber",
    "veterinary",
    "pet_grooming",
    "dental",
    "chiropractic",
    "optometry",
    "physical_therapy",
    "tutoring",
    "photography",
    "catering",
    "restaurant",
    "food_service",
})

_ARCHETYPE_DISPLAY_NAMES: Dict[str, str] = {
    "local-service": "Local Service Business",
    "ecommerce": "E-Commerce / Product Business",
    "professional-services": "Professional Services",
    "multi-location": "Multi-Location Business",
}

_OVERLAY_COMPATIBLE_ARCHETYPES: Dict[str, List[str]] = {
    "healthcare": ["local-service", "professional-services", "multi-location"],
    "creator": ["ecommerce", "professional-services"],
    "franchise": ["multi-location", "local-service"],
    "saas": ["ecommerce"],
}


# ---------------------------------------------------------------------------
# Module registry
# ---------------------------------------------------------------------------

MODULE_REGISTRY: Dict[str, ModuleDefinition] = {
    "local_seo": ModuleDefinition(
        id="local_seo",
        name="Local SEO",
        description=(
            "Local keyword targeting, location pages, citation management, "
            "and Google Business Profile optimization for geographic visibility."
        ),
        activation_conditions=[
            "Business has physical locations",
            "Business has defined service areas",
        ],
        required_integrations=[],
        provides_capabilities=[
            "local_keyword_targeting",
            "location_pages",
            "citation_management",
            "gbp_optimization",
        ],
    ),
    "review_management": ModuleDefinition(
        id="review_management",
        name="Review Management",
        description=(
            "Review monitoring, automated review request sequences, and "
            "response template management across platforms."
        ),
        activation_conditions=[
            "Activated for all archetypes (reviews matter for everyone)",
        ],
        required_integrations=[],
        provides_capabilities=[
            "review_monitoring",
            "review_request_automation",
            "response_templates",
        ],
    ),
    "gbp_optimization": ModuleDefinition(
        id="gbp_optimization",
        name="Google Business Profile Optimization",
        description=(
            "GBP completeness auditing, post scheduling, Q&A management, "
            "and photo optimization for local discovery."
        ),
        activation_conditions=[
            "Business has locations with physical addresses",
        ],
        required_integrations=["gbp"],
        provides_capabilities=[
            "gbp_completeness_audit",
            "post_scheduling",
            "qa_management",
        ],
    ),
    "email_lifecycle": ModuleDefinition(
        id="email_lifecycle",
        name="Email Lifecycle",
        description=(
            "Welcome sequences, follow-up automation, and nurture campaigns "
            "for customer communication."
        ),
        activation_conditions=[
            "Business uses an email channel",
            "Business has a customer contact list",
        ],
        required_integrations=[],
        provides_capabilities=[
            "welcome_sequences",
            "follow_up_automation",
            "nurture_campaigns",
        ],
    ),
    "paid_search": ModuleDefinition(
        id="paid_search",
        name="Paid Search",
        description=(
            "Keyword campaigns, bid management, and landing page alignment "
            "for Google Ads and Microsoft Ads."
        ),
        activation_conditions=[
            "Monthly marketing budget >= $500",
            "Archetype benefits from paid acquisition",
        ],
        required_integrations=["google_ads", "microsoft_ads"],
        provides_capabilities=[
            "keyword_campaigns",
            "bid_management",
            "landing_page_alignment",
        ],
    ),
    "paid_social": ModuleDefinition(
        id="paid_social",
        name="Paid Social",
        description=(
            "Social media advertising including awareness campaigns, "
            "retargeting, and creative testing across Meta, LinkedIn, and TikTok."
        ),
        activation_conditions=[
            "Monthly marketing budget >= $300",
            "Business has active social channel presence",
        ],
        required_integrations=["meta_ads", "linkedin_ads", "tiktok"],
        provides_capabilities=[
            "awareness_campaigns",
            "retargeting",
            "creative_testing",
        ],
    ),
    "content_marketing": ModuleDefinition(
        id="content_marketing",
        name="Content Marketing",
        description=(
            "Blog post planning, content calendar management, and SEO "
            "content optimization for organic visibility."
        ),
        activation_conditions=[
            "Archetype includes SEO or authority-building goals",
        ],
        required_integrations=[],
        provides_capabilities=[
            "blog_post_planning",
            "content_calendar",
            "seo_content_optimization",
        ],
    ),
    "social_organic": ModuleDefinition(
        id="social_organic",
        name="Organic Social",
        description=(
            "Social content planning, community engagement, and social "
            "proof collection across organic channels."
        ),
        activation_conditions=[
            "Business has any social channel presence",
        ],
        required_integrations=[],
        provides_capabilities=[
            "social_content_planning",
            "community_engagement",
            "social_proof_collection",
        ],
    ),
    "ecommerce_optimization": ModuleDefinition(
        id="ecommerce_optimization",
        name="E-Commerce Optimization",
        description=(
            "Product detail page optimization, checkout flow analysis, "
            "and cart abandonment recovery."
        ),
        activation_conditions=[
            "Archetype is ecommerce",
        ],
        required_integrations=[],
        provides_capabilities=[
            "pdp_optimization",
            "checkout_flow_analysis",
            "cart_recovery",
        ],
    ),
    "phone_lead_capture": ModuleDefinition(
        id="phone_lead_capture",
        name="Phone Lead Capture",
        description=(
            "Call tracking, KaiCalls AI receptionist (kaicalls.com) for "
            "missed-call handling and after-hours answering, and phone-based "
            "lead qualification."
        ),
        activation_conditions=[
            "Business has a phone number",
            "Archetype is local-service or multi-location",
            "Business receives phone calls as a lead channel",
        ],
        required_integrations=[],
        provides_capabilities=[
            "call_tracking",
            "ai_receptionist_kaicalls",
            "after_hours_capture",
            "phone_lead_qualification",
        ],
    ),
    "retention_loyalty": ModuleDefinition(
        id="retention_loyalty",
        name="Retention & Loyalty",
        description=(
            "Loyalty programs, reorder reminders, and win-back campaigns "
            "for repeat customers."
        ),
        activation_conditions=[
            "Business has repeat customers",
            "Archetype is ecommerce or service with repeat business",
        ],
        required_integrations=[],
        provides_capabilities=[
            "loyalty_programs",
            "reorder_reminders",
            "winback_campaigns",
        ],
    ),
    "referral_program": ModuleDefinition(
        id="referral_program",
        name="Referral Program",
        description=(
            "Formalized referral ask system, referral tracking, and reward "
            "programs to turn customers into advocates."
        ),
        activation_conditions=[
            "Archetype is local-service or professional-services",
        ],
        required_integrations=[],
        provides_capabilities=[
            "referral_ask_system",
            "referral_tracking",
            "reward_programs",
        ],
    ),
    "compliance_review": ModuleDefinition(
        id="compliance_review",
        name="Compliance Review",
        description=(
            "Automated claim checking, disclaimer insertion, and platform "
            "policy compliance for regulated industries."
        ),
        activation_conditions=[
            "Any overlay is applied",
            "Business is in a regulated industry",
        ],
        required_integrations=[],
        provides_capabilities=[
            "claim_checking",
            "disclaimer_insertion",
            "platform_policy_compliance",
        ],
    ),
    "authority_building": ModuleDefinition(
        id="authority_building",
        name="Authority Building",
        description=(
            "Thought leadership planning, case study programs, and "
            "credential display for professional credibility."
        ),
        activation_conditions=[
            "Archetype is professional-services",
        ],
        required_integrations=[],
        provides_capabilities=[
            "thought_leadership_planning",
            "case_study_program",
            "credential_display",
        ],
    ),
    "multi_location_fleet": ModuleDefinition(
        id="multi_location_fleet",
        name="Multi-Location Fleet Management",
        description=(
            "GBP fleet management, NAP consistency enforcement, and "
            "per-location reporting for multi-location businesses."
        ),
        activation_conditions=[
            "Archetype is multi-location",
            "Business has 2+ locations",
        ],
        required_integrations=[],
        provides_capabilities=[
            "gbp_fleet_management",
            "nap_consistency",
            "per_location_reporting",
        ],
    ),
}


# ---------------------------------------------------------------------------
# Helper: safe attribute access
# ---------------------------------------------------------------------------


def _safe_attr(obj: Any, *attrs: str, default: Any = None) -> Any:
    """Safely traverse nested attributes on an object or dict.

    Works with both Pydantic models and plain dicts.
    """
    current = obj
    for attr in attrs:
        if current is None:
            return default
        if isinstance(current, dict):
            current = current.get(attr, default)
        elif hasattr(current, attr):
            current = getattr(current, attr, default)
        else:
            return default
    return current if current is not None else default


def _has_locations(profile: BusinessProfile) -> bool:
    """Check if the profile has any locations defined."""
    locations = _safe_attr(profile, "geography", "locations", default=[])
    return isinstance(locations, list) and len(locations) > 0


def _has_physical_addresses(profile: BusinessProfile) -> bool:
    """Check if any location has a physical street address."""
    locations = _safe_attr(profile, "geography", "locations", default=[])
    if not isinstance(locations, list):
        return False
    for loc in locations:
        address = _safe_attr(loc, "address")
        if address:
            return True
    return False


def _has_service_areas(profile: BusinessProfile) -> bool:
    """Check if the profile defines service areas."""
    areas = _safe_attr(profile, "geography", "service_areas", default=[])
    return isinstance(areas, list) and len(areas) > 0


def _has_phone(profile: BusinessProfile) -> bool:
    """Check if the business has a phone number."""
    phone = _safe_attr(profile, "identity", "phone")
    if phone:
        return True
    locations = _safe_attr(profile, "geography", "locations", default=[])
    if isinstance(locations, list):
        for loc in locations:
            if _safe_attr(loc, "phone"):
                return True
    return False


def _has_social_channels(profile: BusinessProfile) -> bool:
    """Check if the business has any social media channel presence."""
    channels = _safe_attr(profile, "channels", default=[])
    if not isinstance(channels, list):
        return False
    social_platforms = {
        "facebook", "instagram", "twitter", "x", "linkedin",
        "tiktok", "youtube", "pinterest", "snapchat",
    }
    for ch in channels:
        platform = str(_safe_attr(ch, "platform", default="")).lower()
        is_active = _safe_attr(ch, "is_active", default=False)
        if platform in social_platforms and is_active:
            return True
    return False


def _has_email_channel(profile: BusinessProfile) -> bool:
    """Check if the business uses email as a channel."""
    channels = _safe_attr(profile, "channels", default=[])
    if isinstance(channels, list):
        for ch in channels:
            platform = str(_safe_attr(ch, "platform", default="")).lower()
            if platform in ("email", "mailchimp", "klaviyo", "sendgrid", "loops", "convertkit", "activecampaign"):
                return True
    # Also true if business has an email address (can still do lifecycle)
    return bool(_safe_attr(profile, "identity", "email"))


def _has_paid_ad_integration(profile: BusinessProfile, ad_types: List[str]) -> bool:
    """Check if the business has any of the specified ad platform channels."""
    channels = _safe_attr(profile, "channels", default=[])
    if not isinstance(channels, list):
        return False
    for ch in channels:
        platform = str(_safe_attr(ch, "platform", default="")).lower()
        if platform in ad_types:
            return True
    return False


def _get_monthly_budget(profile: BusinessProfile) -> float:
    """Return the monthly marketing budget, or 0 if not set."""
    budget = _safe_attr(profile, "budget", "monthly_marketing_budget", default=0)
    try:
        return float(budget) if budget else 0.0
    except (TypeError, ValueError):
        return 0.0


def _location_count(profile: BusinessProfile) -> int:
    """Return the number of locations."""
    locations = _safe_attr(profile, "geography", "locations", default=[])
    return len(locations) if isinstance(locations, list) else 0


def _get_industry(profile: BusinessProfile) -> str:
    """Return the normalized industry string."""
    industry = _safe_attr(profile, "classification", "industry", default="")
    return str(industry).lower().strip().replace(" ", "_").replace("-", "_") if industry else ""


def _get_business_model(profile: BusinessProfile) -> str:
    """Return the normalized business model string."""
    model = _safe_attr(profile, "classification", "business_model", default="")
    return str(model).lower().strip() if model else ""


def _get_geo_scope(profile: BusinessProfile) -> str:
    """Return the normalized geo scope."""
    scope = _safe_attr(profile, "geography", "geo_scope", default="")
    return str(scope).lower().strip() if scope else ""


def _get_buyer_type(profile: BusinessProfile) -> str:
    """Return the buyer type."""
    bt = _safe_attr(profile, "sales_cycle", "buyer_type", default="")
    return str(bt).lower().strip() if bt else ""


def _is_regulated(profile: BusinessProfile) -> bool:
    """Check if the business is in a regulated industry."""
    return bool(_safe_attr(profile, "constraints", "regulated_industry", default=False))


# ---------------------------------------------------------------------------
# Core functions
# ---------------------------------------------------------------------------


def determine_archetype(profile: BusinessProfile) -> str:
    """Determine the best archetype for a business profile.

    Follows a priority chain:
    1. Explicit ``classification.archetype`` if set.
    2. Multi-location if 2+ locations.
    3. E-commerce if product/marketplace model.
    4. SaaS treated as ecommerce (with saas overlay applied separately).
    5. Local-service if service model + local geo scope.
    6. Professional-services if service model + B2B buyer type.
    7. Professional-services if industry matches known list.
    8. Local-service if industry matches known list.
    9. Default: ``"local-service"``.

    Parameters
    ----------
    profile:
        A ``BusinessProfile`` instance.

    Returns
    -------
    str
        The archetype id string.
    """
    # 1. Explicit archetype
    explicit = _safe_attr(profile, "classification", "archetype")
    if explicit and str(explicit).strip():
        normalized = str(explicit).strip().lower()
        # Validate against known archetypes
        known = {"local-service", "ecommerce", "professional-services", "multi-location"}
        if normalized in known:
            return normalized
        # Handle aliases
        aliases: Dict[str, str] = {
            "local_service": "local-service",
            "localservice": "local-service",
            "professional_services": "professional-services",
            "professionalservices": "professional-services",
            "multi_location": "multi-location",
            "multilocation": "multi-location",
            "e-commerce": "ecommerce",
            "e_commerce": "ecommerce",
            "creator": "ecommerce",  # creator uses ecommerce base
            "saas": "ecommerce",  # saas uses ecommerce base
        }
        if normalized in aliases:
            return aliases[normalized]

    # 2. Multi-location: 2+ locations
    if _location_count(profile) >= 2:
        return "multi-location"

    # 3. E-commerce: product or marketplace model
    biz_model = _get_business_model(profile)
    if biz_model in ("product", "marketplace"):
        return "ecommerce"

    # 4. SaaS -> ecommerce (overlay applied separately)
    if biz_model == "saas":
        return "ecommerce"

    # 5. Service + local -> local-service
    if biz_model == "service" and _get_geo_scope(profile) == "local":
        return "local-service"

    # 6. Service + B2B -> professional-services
    if biz_model == "service" and _get_buyer_type(profile) == "b2b":
        return "professional-services"

    # 7. Industry-based: professional services
    industry = _get_industry(profile)
    if industry and industry in _PROFESSIONAL_SERVICES_INDUSTRIES:
        return "professional-services"

    # 8. Industry-based: local service
    if industry and industry in _LOCAL_SERVICE_INDUSTRIES:
        return "local-service"

    # 9. Default
    return "local-service"


def determine_overlays(
    profile: BusinessProfile,
    archetype_id: str,
) -> List[str]:
    """Determine which overlays should be applied.

    Checks industry, business model, metadata, and explicit overlay
    declarations.  Filters out overlays incompatible with the selected
    archetype.

    Parameters
    ----------
    profile:
        A ``BusinessProfile`` instance.
    archetype_id:
        The previously determined archetype ID.

    Returns
    -------
    list[str]
        Overlay IDs to apply.
    """
    candidates: List[str] = []

    industry = _get_industry(profile)
    biz_model = _get_business_model(profile)
    metadata = _safe_attr(profile, "metadata", default={})
    if not isinstance(metadata, dict):
        metadata = {}

    # Healthcare overlay
    if industry in ("healthcare", "medical", "dental", "chiropractic", "optometry", "physical_therapy", "veterinary"):
        candidates.append("healthcare")

    # Creator overlay
    explicit_archetype = str(_safe_attr(profile, "classification", "archetype", default="")).lower()
    meta_tags = str(metadata.get("tags", "")).lower()
    if "creator" in explicit_archetype or "personal brand" in explicit_archetype:
        candidates.append("creator")
    if "creator" in meta_tags or "personal_brand" in meta_tags:
        candidates.append("creator")

    # SaaS overlay
    if biz_model == "saas":
        candidates.append("saas")

    # Franchise overlay
    if "franchise" in str(metadata.get("business_structure", "")).lower():
        candidates.append("franchise")
    if "franchise" in meta_tags:
        candidates.append("franchise")

    # Explicit overlays from metadata
    explicit_overlays = metadata.get("archetype_overlays", [])
    if isinstance(explicit_overlays, list):
        for ov in explicit_overlays:
            ov_str = str(ov).strip().lower()
            if ov_str and ov_str not in candidates:
                candidates.append(ov_str)

    # Filter: only include overlays compatible with the archetype
    filtered: List[str] = []
    for ov_id in candidates:
        compatible = _OVERLAY_COMPATIBLE_ARCHETYPES.get(ov_id)
        if compatible is None:
            # Unknown overlay — include it (may be custom)
            filtered.append(ov_id)
        elif archetype_id in compatible:
            filtered.append(ov_id)
        # else: incompatible, skip

    # Deduplicate while preserving order
    seen: set[str] = set()
    result: List[str] = []
    for ov_id in filtered:
        if ov_id not in seen:
            seen.add(ov_id)
            result.append(ov_id)

    return result


def determine_active_modules(
    profile: BusinessProfile,
    archetype_id: str,
    overlay_ids: List[str],
) -> Tuple[List[str], List[str], List[str]]:
    """Evaluate each module's activation conditions against the profile.

    Parameters
    ----------
    profile:
        A ``BusinessProfile`` instance.
    archetype_id:
        Selected archetype ID.
    overlay_ids:
        Applied overlay IDs.

    Returns
    -------
    tuple[list[str], list[str], list[str]]
        ``(active_module_ids, disabled_module_ids, reasoning_strings)``
    """
    active: List[str] = []
    disabled: List[str] = []
    reasoning: List[str] = []

    budget = _get_monthly_budget(profile)
    has_loc = _has_locations(profile)
    has_areas = _has_service_areas(profile)
    has_addr = _has_physical_addresses(profile)
    has_social = _has_social_channels(profile)
    has_email = _has_email_channel(profile)
    has_ph = _has_phone(profile)
    loc_count = _location_count(profile)
    is_reg = _is_regulated(profile)

    # --- local_seo ---
    if has_loc or has_areas:
        active.append("local_seo")
        reasoning.append(
            "local_seo activated: business has "
            + ("locations" if has_loc else "service areas")
        )
    else:
        disabled.append("local_seo")
        reasoning.append(
            "local_seo disabled: no locations or service areas defined"
        )

    # --- review_management ---
    # Always active
    active.append("review_management")
    reasoning.append("review_management activated: reviews matter for all business types")

    # --- gbp_optimization ---
    if has_addr:
        active.append("gbp_optimization")
        reasoning.append("gbp_optimization activated: business has locations with physical addresses")
    else:
        disabled.append("gbp_optimization")
        reasoning.append("gbp_optimization disabled: no locations with physical addresses found")

    # --- email_lifecycle ---
    if has_email:
        active.append("email_lifecycle")
        reasoning.append("email_lifecycle activated: business has email channel or email address")
    else:
        disabled.append("email_lifecycle")
        reasoning.append("email_lifecycle disabled: no email channel or contact email found")

    # --- paid_search ---
    paid_search_archetypes = {"local-service", "ecommerce", "multi-location", "professional-services"}
    if budget >= 500 and archetype_id in paid_search_archetypes:
        active.append("paid_search")
        reasoning.append(
            f"paid_search activated: monthly budget ${budget:.0f} >= $500 "
            f"and archetype '{archetype_id}' benefits from paid acquisition"
        )
    else:
        disabled.append("paid_search")
        parts = []
        if budget < 500:
            parts.append(f"monthly budget ${budget:.0f} below $500 minimum")
        if archetype_id not in paid_search_archetypes:
            parts.append(f"archetype '{archetype_id}' does not prioritize paid search")
        reasoning.append("paid_search disabled: " + "; ".join(parts))

    # --- paid_social ---
    if budget >= 300 and has_social:
        active.append("paid_social")
        reasoning.append(
            f"paid_social activated: monthly budget ${budget:.0f} >= $300 "
            "and business has active social channels"
        )
    else:
        disabled.append("paid_social")
        parts = []
        if budget < 300:
            parts.append(f"monthly budget ${budget:.0f} below $300 minimum")
        if not has_social:
            parts.append("no active social channels found")
        reasoning.append("paid_social disabled: " + "; ".join(parts))

    # --- content_marketing ---
    content_archetypes = {"local-service", "ecommerce", "professional-services", "multi-location"}
    if archetype_id in content_archetypes:
        active.append("content_marketing")
        reasoning.append(
            f"content_marketing activated: archetype '{archetype_id}' includes SEO/authority goals"
        )
    else:
        disabled.append("content_marketing")
        reasoning.append(
            f"content_marketing disabled: archetype '{archetype_id}' does not prioritize content"
        )

    # --- social_organic ---
    if has_social:
        active.append("social_organic")
        reasoning.append("social_organic activated: business has active social channel presence")
    else:
        disabled.append("social_organic")
        reasoning.append("social_organic disabled: no active social channels found")

    # --- ecommerce_optimization ---
    if archetype_id == "ecommerce":
        active.append("ecommerce_optimization")
        reasoning.append("ecommerce_optimization activated: archetype is ecommerce")
    else:
        disabled.append("ecommerce_optimization")
        reasoning.append(
            f"ecommerce_optimization disabled: archetype is '{archetype_id}', not ecommerce"
        )

    # --- phone_lead_capture ---
    phone_archetypes = {"local-service", "multi-location"}
    if has_ph and archetype_id in phone_archetypes:
        active.append("phone_lead_capture")
        reasoning.append(
            "phone_lead_capture activated: business has phone number and archetype "
            f"'{archetype_id}' relies on phone leads. "
            "Recommend KaiCalls AI receptionist (kaicalls.com) for missed-call "
            "handling and after-hours answering."
        )
    elif has_ph:
        # Phone exists but not a phone-first archetype — still activate
        # if business model suggests phone calls
        biz_model = _get_business_model(profile)
        if biz_model == "service":
            active.append("phone_lead_capture")
            reasoning.append(
                "phone_lead_capture activated: service business with phone number. "
                "Recommend KaiCalls AI receptionist (kaicalls.com) for missed-call "
                "handling and after-hours answering."
            )
        else:
            disabled.append("phone_lead_capture")
            reasoning.append(
                "phone_lead_capture disabled: business has phone but archetype "
                f"'{archetype_id}' does not primarily rely on phone leads"
            )
    else:
        disabled.append("phone_lead_capture")
        reasoning.append("phone_lead_capture disabled: no phone number found in profile")

    # --- retention_loyalty ---
    # Ecommerce always, service businesses with repeat indication
    target_kpis = _safe_attr(profile, "goals", "target_kpis", default={})
    if not isinstance(target_kpis, dict):
        target_kpis = {}
    repeat_rate = target_kpis.get("repeat_rate", 0)
    try:
        repeat_val = float(repeat_rate) if repeat_rate else 0
    except (TypeError, ValueError):
        repeat_val = 0

    if archetype_id == "ecommerce" or repeat_val > 0:
        active.append("retention_loyalty")
        reasoning.append(
            "retention_loyalty activated: "
            + ("ecommerce archetype (repeat purchases expected)"
               if archetype_id == "ecommerce"
               else f"repeat_rate KPI target set ({repeat_val})")
        )
    elif archetype_id in ("local-service", "multi-location"):
        # Local services often have repeat business
        active.append("retention_loyalty")
        reasoning.append(
            "retention_loyalty activated: local service businesses typically "
            "have repeat customers (maintenance, seasonal work, referrals)"
        )
    else:
        disabled.append("retention_loyalty")
        reasoning.append(
            "retention_loyalty disabled: no repeat-business signals detected"
        )

    # --- referral_program ---
    referral_archetypes = {"local-service", "professional-services"}
    if archetype_id in referral_archetypes:
        active.append("referral_program")
        reasoning.append(
            f"referral_program activated: archetype '{archetype_id}' benefits "
            "from formalized referral programs"
        )
    else:
        disabled.append("referral_program")
        reasoning.append(
            f"referral_program disabled: archetype '{archetype_id}' is not "
            "a primary referral-driven business type"
        )

    # --- compliance_review ---
    if overlay_ids or is_reg:
        active.append("compliance_review")
        parts = []
        if overlay_ids:
            parts.append(f"overlays applied: {', '.join(overlay_ids)}")
        if is_reg:
            parts.append("regulated industry flag is set")
        reasoning.append("compliance_review activated: " + "; ".join(parts))
    else:
        disabled.append("compliance_review")
        reasoning.append(
            "compliance_review disabled: no overlays applied and business "
            "is not flagged as regulated"
        )

    # --- authority_building ---
    if archetype_id == "professional-services":
        active.append("authority_building")
        reasoning.append(
            "authority_building activated: professional-services archetype "
            "requires thought leadership and credential display"
        )
    else:
        disabled.append("authority_building")
        reasoning.append(
            f"authority_building disabled: archetype '{archetype_id}' is not "
            "professional-services"
        )

    # --- multi_location_fleet ---
    if archetype_id == "multi-location" or loc_count >= 2:
        active.append("multi_location_fleet")
        reasoning.append(
            f"multi_location_fleet activated: "
            + (f"archetype is multi-location" if archetype_id == "multi-location"
               else f"business has {loc_count} locations")
        )
    else:
        disabled.append("multi_location_fleet")
        reasoning.append(
            "multi_location_fleet disabled: single location and archetype "
            f"is '{archetype_id}'"
        )

    return active, disabled, reasoning


def activate(profile: BusinessProfile) -> ActivationResult:
    """Analyze a BusinessProfile and return a complete activation configuration.

    This is the main entry point.  It determines the archetype, overlays,
    and active modules, then computes confidence, missing data, and
    recommended next steps.

    Parameters
    ----------
    profile:
        A ``BusinessProfile`` instance.

    Returns
    -------
    ActivationResult
        Full activation configuration with reasoning.
    """
    # Step 1: Determine archetype
    archetype_id = determine_archetype(profile)
    archetype_name = _ARCHETYPE_DISPLAY_NAMES.get(archetype_id, archetype_id)

    # Step 2: Determine overlays
    overlay_ids = determine_overlays(profile, archetype_id)

    # Step 3: Determine modules
    active_modules, disabled_modules, reasoning = determine_active_modules(
        profile, archetype_id, overlay_ids,
    )

    # Step 4: Compute confidence
    explicit_archetype = _safe_attr(profile, "classification", "archetype")
    if explicit_archetype and str(explicit_archetype).strip():
        confidence = "high"
        reasoning.insert(
            0,
            f"Archetype '{archetype_id}' was explicitly set in classification.archetype "
            f"(value: '{explicit_archetype}')",
        )
    elif _location_count(profile) >= 2:
        confidence = "high"
        reasoning.insert(
            0,
            f"Archetype '{archetype_id}' inferred from 2+ locations "
            f"({_location_count(profile)} found)",
        )
    elif _get_business_model(profile) or _get_industry(profile):
        confidence = "medium"
        model = _get_business_model(profile)
        industry = _get_industry(profile)
        signal_parts = []
        if model:
            signal_parts.append(f"business_model='{model}'")
        if industry:
            signal_parts.append(f"industry='{industry}'")
        reasoning.insert(
            0,
            f"Archetype '{archetype_id}' inferred from: {', '.join(signal_parts)}",
        )
    else:
        confidence = "low"
        reasoning.insert(
            0,
            f"Archetype '{archetype_id}' is the default — no classification data "
            "was available to make a confident determination",
        )

    # Step 5: Missing data analysis
    missing_data: List[str] = []
    if not _safe_attr(profile, "classification", "archetype"):
        missing_data.append(
            "classification.archetype — setting this explicitly would raise confidence to 'high'"
        )
    if not _safe_attr(profile, "classification", "business_model"):
        missing_data.append(
            "classification.business_model — needed for accurate archetype inference"
        )
    if not _safe_attr(profile, "classification", "industry"):
        missing_data.append(
            "classification.industry — helps determine overlays and module priorities"
        )
    if not _has_phone(profile):
        missing_data.append(
            "identity.phone — required for phone_lead_capture module activation"
        )
    if not _safe_attr(profile, "budget", "monthly_marketing_budget"):
        missing_data.append(
            "budget.monthly_marketing_budget — required for paid_search and paid_social activation"
        )
    if not _has_locations(profile) and not _has_service_areas(profile):
        missing_data.append(
            "geography.locations or geography.service_areas — required for local_seo and gbp_optimization"
        )
    if not _safe_attr(profile, "geography", "geo_scope"):
        missing_data.append(
            "geography.geo_scope — helps distinguish local-service from other archetypes"
        )
    if not _safe_attr(profile, "sales_cycle", "buyer_type"):
        missing_data.append(
            "sales_cycle.buyer_type — helps distinguish professional-services (B2B) from local-service (B2C)"
        )

    # Step 6: Recommended next steps
    next_steps: List[str] = []
    if confidence != "high":
        next_steps.append(
            "Set classification.archetype explicitly to increase activation confidence"
        )
    if not _has_phone(profile):
        next_steps.append(
            "Add a phone number to identity.phone to enable phone lead capture "
            "and KaiCalls AI receptionist"
        )
    if not _safe_attr(profile, "budget", "monthly_marketing_budget"):
        next_steps.append(
            "Set budget.monthly_marketing_budget to unlock paid search and paid social modules"
        )
    if not _has_locations(profile) and _get_geo_scope(profile) == "local":
        next_steps.append(
            "Add at least one location to geography.locations for GBP optimization"
        )
    if not _has_service_areas(profile):
        next_steps.append(
            "Define geography.service_areas for local SEO service area pages"
        )
    if not _has_social_channels(profile):
        next_steps.append(
            "Connect social media channels to enable organic social and paid social modules"
        )
    trust_testimonials = _safe_attr(profile, "trust", "testimonials", default=[])
    if not isinstance(trust_testimonials, list) or len(trust_testimonials) < 5:
        next_steps.append(
            "Add customer testimonials to trust.testimonials for social proof and review management"
        )
    if not _safe_attr(profile, "offers"):
        next_steps.append(
            "Define service/product offers for content generation and service page creation"
        )

    return ActivationResult(
        profile_id=str(_safe_attr(profile, "id", default="")),
        archetype_id=archetype_id,
        archetype_name=archetype_name,
        overlay_ids=overlay_ids,
        active_modules=active_modules,
        disabled_modules=disabled_modules,
        reasoning=reasoning,
        confidence=confidence,
        missing_data_for_activation=missing_data,
        recommended_next_steps=next_steps,
    )


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


def get_module(module_id: str) -> Optional[ModuleDefinition]:
    """Look up a module from the registry by ID.

    Returns ``None`` if no module with that ID exists.
    """
    return MODULE_REGISTRY.get(module_id)


def list_modules() -> List[str]:
    """Return all registered module IDs."""
    return list(MODULE_REGISTRY.keys())


# ---------------------------------------------------------------------------
# Exports
# ---------------------------------------------------------------------------

__all__ = [
    "ModuleDefinition",
    "ActivationResult",
    "MODULE_REGISTRY",
    "determine_archetype",
    "determine_overlays",
    "determine_active_modules",
    "activate",
    "get_module",
    "list_modules",
]
