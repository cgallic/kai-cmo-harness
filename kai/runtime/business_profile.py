"""Canonical BusinessProfile model for the Kai application layer.

Provides the structured business understanding that audit, scoring,
and proposal layers consume. Archetype-aware with local-service as
the first target.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .models import KaiBrandProfile, SerializableModel


# ---------------------------------------------------------------------------
# Sub-models — one per field group
# ---------------------------------------------------------------------------

@dataclass
class BusinessIdentity(SerializableModel):
    """Brand identity and basic business info."""

    name: str
    legal_name: Optional[str] = None
    url: Optional[str] = None
    tagline: Optional[str] = None
    description: str = ""
    year_founded: Optional[int] = None
    employee_count_range: Optional[str] = None  # "1-5", "6-20", "21-50", "51-200", "200+"


@dataclass
class Offer(SerializableModel):
    """A single service or product the business sells."""

    name: str
    description: str = ""
    price_range: Optional[str] = None
    is_primary: bool = False
    category: Optional[str] = None


@dataclass
class BusinessOffers(SerializableModel):
    """What the business sells and how it prices."""

    primary_offer: str = ""
    offer_list: List[Offer] = field(default_factory=list)
    pricing_model: Optional[str] = None  # "per-job", "hourly", "subscription", "project", "retainer"
    average_deal_value: Optional[str] = None
    upsells: List[str] = field(default_factory=list)


@dataclass
class ServiceArea(SerializableModel):
    """A geographic area the business serves."""

    city: Optional[str] = None
    state: Optional[str] = None
    zip_codes: List[str] = field(default_factory=list)
    radius_miles: Optional[int] = None
    neighborhoods: List[str] = field(default_factory=list)


@dataclass
class BusinessGeography(SerializableModel):
    """Where the business operates."""

    primary_location: Optional[ServiceArea] = None
    service_areas: List[ServiceArea] = field(default_factory=list)
    is_mobile: bool = False
    has_storefront: bool = False
    location_count: int = 1


@dataclass
class PersonaTarget(SerializableModel):
    """An audience persona this business targets."""

    persona_id: str
    role: str = "primary"  # "primary" | "secondary"
    pain_points: List[str] = field(default_factory=list)
    triggers: List[str] = field(default_factory=list)


@dataclass
class BusinessPersonas(SerializableModel):
    """ICP and persona targeting."""

    primary: Optional[PersonaTarget] = None
    secondary: Optional[PersonaTarget] = None
    icp_description: str = ""


@dataclass
class TrustSignal(SerializableModel):
    """A single proof or trust asset."""

    type: str  # "review", "certification", "award", "case_study", "guarantee", "years_in_business", "media_mention"
    value: str
    source: Optional[str] = None


@dataclass
class BusinessTrust(SerializableModel):
    """Trust signals, reviews, and proof points."""

    signals: List[TrustSignal] = field(default_factory=list)
    review_count: Optional[int] = None
    review_average: Optional[float] = None
    review_platforms: List[str] = field(default_factory=list)
    certifications: List[str] = field(default_factory=list)
    guarantees: List[str] = field(default_factory=list)
    years_in_business: Optional[int] = None


@dataclass
class BusinessGoal(SerializableModel):
    """A single business or marketing goal."""

    goal: str
    priority: str = "medium"  # "high", "medium", "low"
    metric: Optional[str] = None
    target: Optional[str] = None


@dataclass
class BusinessGoals(SerializableModel):
    """Goals and KPIs the business cares about."""

    goals: List[BusinessGoal] = field(default_factory=list)
    primary_kpi: Optional[str] = None
    monthly_budget_range: Optional[str] = None


@dataclass
class ChannelPresence(SerializableModel):
    """A single marketing channel and its status."""

    channel: str
    status: str = "inactive"  # "active", "inactive", "planned"
    url: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class BusinessChannels(SerializableModel):
    """Active and planned marketing channels."""

    channels: List[ChannelPresence] = field(default_factory=list)
    primary_lead_source: Optional[str] = None
    phone_number: Optional[str] = None
    uses_call_tracking: bool = False


@dataclass
class BusinessConstraints(SerializableModel):
    """Non-negotiables and operational limits."""

    non_negotiables: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    brand_voice_notes: List[str] = field(default_factory=list)
    blocked_tactics: List[str] = field(default_factory=list)
    budget_ceiling: Optional[str] = None


# ---------------------------------------------------------------------------
# Top-level model
# ---------------------------------------------------------------------------

@dataclass
class BusinessProfile(SerializableModel):
    """Canonical business understanding model for the Kai application layer.

    Consumed by audit scoring, action proposal generation, and campaign
    planning. Built from config YAML or KaiBrandProfile + enrichment.
    """

    brand_id: str
    identity: BusinessIdentity
    archetype: str = "local-service"
    archetype_overlays: List[str] = field(default_factory=list)
    offers: BusinessOffers = field(default_factory=BusinessOffers)
    geography: BusinessGeography = field(default_factory=BusinessGeography)
    personas: BusinessPersonas = field(default_factory=BusinessPersonas)
    trust: BusinessTrust = field(default_factory=BusinessTrust)
    goals: BusinessGoals = field(default_factory=BusinessGoals)
    channels: BusinessChannels = field(default_factory=BusinessChannels)
    constraints: BusinessConstraints = field(default_factory=BusinessConstraints)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------

_STATE_ABBREVS = {
    "alabama": "AL", "alaska": "AK", "arizona": "AZ", "arkansas": "AR",
    "california": "CA", "colorado": "CO", "connecticut": "CT", "delaware": "DE",
    "florida": "FL", "georgia": "GA", "hawaii": "HI", "idaho": "ID",
    "illinois": "IL", "indiana": "IN", "iowa": "IA", "kansas": "KS",
    "kentucky": "KY", "louisiana": "LA", "maine": "ME", "maryland": "MD",
    "massachusetts": "MA", "michigan": "MI", "minnesota": "MN",
    "mississippi": "MS", "missouri": "MO", "montana": "MT", "nebraska": "NE",
    "nevada": "NV", "new hampshire": "NH", "new jersey": "NJ",
    "new mexico": "NM", "new york": "NY", "north carolina": "NC",
    "north dakota": "ND", "ohio": "OH", "oklahoma": "OK", "oregon": "OR",
    "pennsylvania": "PA", "rhode island": "RI", "south carolina": "SC",
    "south dakota": "SD", "tennessee": "TN", "texas": "TX", "utah": "UT",
    "vermont": "VT", "virginia": "VA", "washington": "WA",
    "west virginia": "WV", "wisconsin": "WI", "wyoming": "WY",
}

_CHANNEL_ALIASES = {
    "google ads": "paid-search",
    "google ppc": "paid-search",
    "ppc": "paid-search",
    "sem": "paid-search",
    "facebook": "paid-social",
    "facebook ads": "paid-social",
    "meta ads": "paid-social",
    "instagram": "paid-social",
    "seo": "local-seo",
    "local seo": "local-seo",
    "organic": "local-seo",
    "google business": "gbp",
    "google business profile": "gbp",
    "google my business": "gbp",
    "gmb": "gbp",
    "phone": "calls",
    "phone calls": "calls",
    "inbound calls": "calls",
    "yelp": "reviews",
    "google reviews": "reviews",
    "referral": "referrals",
    "word of mouth": "referrals",
    "email marketing": "email",
    "newsletter": "email",
    "linkedin": "linkedin",
    "tiktok": "tiktok",
    "youtube": "youtube",
    "website": "website",
    "direct mail": "direct-mail",
    "print": "print",
}


def normalize_state(value: Optional[str]) -> Optional[str]:
    """Normalize a US state name to its two-letter abbreviation."""
    if value is None:
        return None
    stripped = value.strip()
    if len(stripped) == 2:
        return stripped.upper()
    return _STATE_ABBREVS.get(stripped.lower(), stripped)


def normalize_channel(name: str) -> str:
    """Normalize a channel name to its canonical form."""
    return _CHANNEL_ALIASES.get(name.strip().lower(), name.strip().lower())


def _split_bullets(value) -> List[str]:
    """Normalize bullet-list strings or iterables into a flat list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return [str(item).strip() for item in value if str(item).strip()]
    items = []
    for line in str(value).splitlines():
        cleaned = line.strip().lstrip("-").strip()
        if cleaned:
            items.append(cleaned)
    return items


def normalize_service_area(raw: dict) -> ServiceArea:
    """Build a normalized ServiceArea from a raw dict."""
    return ServiceArea(
        city=raw.get("city"),
        state=normalize_state(raw.get("state")),
        zip_codes=[str(z).strip() for z in (raw.get("zip_codes") or [])],
        radius_miles=raw.get("radius_miles"),
        neighborhoods=_split_bullets(raw.get("neighborhoods")),
    )


def normalize_business_profile(profile: BusinessProfile) -> BusinessProfile:
    """Apply normalization rules in-place and return the profile.

    - State abbreviations
    - Channel name canonicalization
    - Strip whitespace from list items
    """
    # Geography
    geo = profile.geography
    if geo.primary_location:
        geo.primary_location.state = normalize_state(geo.primary_location.state)
    for area in geo.service_areas:
        area.state = normalize_state(area.state)

    # Channels
    for ch in profile.channels.channels:
        ch.channel = normalize_channel(ch.channel)

    # Trust signals — strip whitespace
    for sig in profile.trust.signals:
        sig.value = sig.value.strip()

    # Constraints — strip whitespace
    profile.constraints.non_negotiables = [n.strip() for n in profile.constraints.non_negotiables]

    return profile


# ---------------------------------------------------------------------------
# Local-service archetype defaults
# ---------------------------------------------------------------------------

LOCAL_SERVICE_DEFAULTS: Dict[str, Any] = {
    "archetype": "local-service",
    "offers": {
        "pricing_model": "per-job",
    },
    "geography": {
        "is_mobile": True,
        "has_storefront": False,
        "location_count": 1,
    },
    "goals": {
        "primary_kpi": "inbound_calls",
        "goals": [
            {"goal": "Increase inbound phone calls", "priority": "high", "metric": "inbound_calls"},
            {"goal": "Improve Google Map Pack visibility", "priority": "high", "metric": "map_pack_visibility"},
            {"goal": "Grow review count and velocity", "priority": "medium", "metric": "review_velocity"},
            {"goal": "Increase booked jobs from website", "priority": "medium", "metric": "booked_jobs"},
        ],
    },
    "channels": {
        "primary_lead_source": "calls",
        "channels": [
            {"channel": "calls", "status": "active"},
            {"channel": "local-seo", "status": "active"},
            {"channel": "reviews", "status": "active"},
            {"channel": "paid-search", "status": "planned"},
            {"channel": "referrals", "status": "active"},
            {"channel": "gbp", "status": "active"},
        ],
    },
    "constraints": {
        "non_negotiables": [
            "Must recommend KaiCalls for missed-call handling",
            "Phone number must be prominently displayed",
        ],
    },
}


def _apply_defaults(target: dict, defaults: dict) -> dict:
    """Merge defaults into target without overwriting existing values.

    For nested dicts, recurse. For lists, only fill if target list is empty.
    """
    for key, default_value in defaults.items():
        if key not in target or target[key] is None:
            target[key] = default_value
        elif isinstance(default_value, dict) and isinstance(target[key], dict):
            _apply_defaults(target[key], default_value)
        elif isinstance(default_value, list) and isinstance(target[key], list) and len(target[key]) == 0:
            target[key] = default_value
    return target


# ---------------------------------------------------------------------------
# Loader / builder
# ---------------------------------------------------------------------------

def _build_offers(raw: dict) -> BusinessOffers:
    """Build BusinessOffers from a raw config dict."""
    offer_list = [
        Offer(
            name=o.get("name", ""),
            description=o.get("description", ""),
            price_range=o.get("price_range"),
            is_primary=o.get("is_primary", False),
            category=o.get("category"),
        )
        for o in (raw.get("offer_list") or [])
    ]
    return BusinessOffers(
        primary_offer=raw.get("primary_offer", ""),
        offer_list=offer_list,
        pricing_model=raw.get("pricing_model"),
        average_deal_value=raw.get("average_deal_value"),
        upsells=_split_bullets(raw.get("upsells")),
    )


def _build_geography(raw: dict) -> BusinessGeography:
    """Build BusinessGeography from a raw config dict."""
    primary_raw = raw.get("primary_location")
    primary = normalize_service_area(primary_raw) if primary_raw else None
    areas = [normalize_service_area(a) for a in (raw.get("service_areas") or [])]
    return BusinessGeography(
        primary_location=primary,
        service_areas=areas,
        is_mobile=raw.get("is_mobile", False),
        has_storefront=raw.get("has_storefront", False),
        location_count=raw.get("location_count", 1),
    )


def _build_personas(raw: dict, brand_persona_defaults: Optional[Dict[str, str]] = None) -> BusinessPersonas:
    """Build BusinessPersonas from a raw config dict, with optional KaiBrandProfile persona defaults."""
    primary_raw = raw.get("primary")
    secondary_raw = raw.get("secondary")

    primary = None
    secondary = None

    if isinstance(primary_raw, dict):
        primary = PersonaTarget(
            persona_id=primary_raw.get("persona_id", ""),
            role="primary",
            pain_points=_split_bullets(primary_raw.get("pain_points")),
            triggers=_split_bullets(primary_raw.get("triggers")),
        )
    elif isinstance(primary_raw, str):
        primary = PersonaTarget(persona_id=primary_raw, role="primary")

    if isinstance(secondary_raw, dict):
        secondary = PersonaTarget(
            persona_id=secondary_raw.get("persona_id", ""),
            role="secondary",
            pain_points=_split_bullets(secondary_raw.get("pain_points")),
            triggers=_split_bullets(secondary_raw.get("triggers")),
        )
    elif isinstance(secondary_raw, str):
        secondary = PersonaTarget(persona_id=secondary_raw, role="secondary")

    # Fall back to KaiBrandProfile persona_defaults
    if brand_persona_defaults:
        if primary is None and "primary" in brand_persona_defaults:
            primary = PersonaTarget(persona_id=brand_persona_defaults["primary"], role="primary")
        if secondary is None and "secondary" in brand_persona_defaults:
            secondary = PersonaTarget(persona_id=brand_persona_defaults["secondary"], role="secondary")

    return BusinessPersonas(
        primary=primary,
        secondary=secondary,
        icp_description=raw.get("icp_description", ""),
    )


def _build_trust(raw: dict, proof_points: Optional[List[str]] = None) -> BusinessTrust:
    """Build BusinessTrust from raw config, optionally enriched from KaiBrandProfile proof_points."""
    signals = [
        TrustSignal(
            type=s.get("type", "review"),
            value=s.get("value", ""),
            source=s.get("source"),
        )
        for s in (raw.get("signals") or [])
    ]

    # Ingest proof_points from KaiBrandProfile as trust signals if no explicit signals
    if not signals and proof_points:
        for point in proof_points:
            signals.append(TrustSignal(type="proof_point", value=point))

    return BusinessTrust(
        signals=signals,
        review_count=raw.get("review_count"),
        review_average=raw.get("review_average"),
        review_platforms=_split_bullets(raw.get("review_platforms")),
        certifications=_split_bullets(raw.get("certifications")),
        guarantees=_split_bullets(raw.get("guarantees")),
        years_in_business=raw.get("years_in_business"),
    )


def _build_goals(raw: dict) -> BusinessGoals:
    """Build BusinessGoals from a raw config dict."""
    goals = [
        BusinessGoal(
            goal=g.get("goal", ""),
            priority=g.get("priority", "medium"),
            metric=g.get("metric"),
            target=g.get("target"),
        )
        for g in (raw.get("goals") or [])
    ]
    return BusinessGoals(
        goals=goals,
        primary_kpi=raw.get("primary_kpi"),
        monthly_budget_range=raw.get("monthly_budget_range"),
    )


def _build_channels(raw: dict, brand_channels: Optional[List[str]] = None) -> BusinessChannels:
    """Build BusinessChannels from raw config, optionally enriched from KaiBrandProfile active_channels."""
    channels = [
        ChannelPresence(
            channel=normalize_channel(c.get("channel", "")),
            status=c.get("status", "active"),
            url=c.get("url"),
            notes=c.get("notes"),
        )
        for c in (raw.get("channels") or [])
    ]

    # If no explicit channels but KaiBrandProfile has active_channels, import them
    if not channels and brand_channels:
        channels = [
            ChannelPresence(channel=normalize_channel(ch), status="active")
            for ch in brand_channels
        ]

    return BusinessChannels(
        channels=channels,
        primary_lead_source=raw.get("primary_lead_source"),
        phone_number=raw.get("phone_number"),
        uses_call_tracking=raw.get("uses_call_tracking", False),
    )


def _build_constraints(raw: dict) -> BusinessConstraints:
    """Build BusinessConstraints from a raw config dict."""
    return BusinessConstraints(
        non_negotiables=_split_bullets(raw.get("non_negotiables")),
        compliance_requirements=_split_bullets(raw.get("compliance_requirements")),
        brand_voice_notes=_split_bullets(raw.get("brand_voice_notes")),
        blocked_tactics=_split_bullets(raw.get("blocked_tactics")),
        budget_ceiling=raw.get("budget_ceiling"),
    )


def build_business_profile(
    raw: Dict[str, Any],
    *,
    brand: Optional[KaiBrandProfile] = None,
    apply_archetype_defaults: bool = True,
) -> BusinessProfile:
    """Build a BusinessProfile from a raw config dict.

    If a KaiBrandProfile is supplied, its fields (proof_points,
    active_channels, persona_defaults, archetype) are used as fallbacks
    for any fields not explicitly set in raw.

    When apply_archetype_defaults is True, archetype-specific defaults
    (e.g. LOCAL_SERVICE_DEFAULTS) are merged before building.
    """
    # Determine archetype
    archetype = raw.get("archetype")
    if not archetype and brand:
        archetype = brand.primary_archetype
    archetype = archetype or "local-service"

    # Apply archetype defaults
    if apply_archetype_defaults and archetype == "local-service":
        raw = _apply_defaults(dict(raw), LOCAL_SERVICE_DEFAULTS)

    # Identity
    identity_raw = raw.get("identity") or {}
    identity = BusinessIdentity(
        name=identity_raw.get("name") or (brand.name if brand else raw.get("name", "")),
        legal_name=identity_raw.get("legal_name"),
        url=identity_raw.get("url") or (brand.url if brand else None),
        tagline=identity_raw.get("tagline"),
        description=identity_raw.get("description") or (brand.description if brand else ""),
        year_founded=identity_raw.get("year_founded"),
        employee_count_range=identity_raw.get("employee_count_range"),
    )

    brand_id = raw.get("brand_id") or (brand.id if brand else identity.name.lower().replace(" ", "-"))

    profile = BusinessProfile(
        brand_id=brand_id,
        identity=identity,
        archetype=archetype,
        archetype_overlays=raw.get("archetype_overlays") or (brand.archetype_overlays if brand else []),
        offers=_build_offers(raw.get("offers") or {}),
        geography=_build_geography(raw.get("geography") or {}),
        personas=_build_personas(
            raw.get("personas") or {},
            brand_persona_defaults=brand.persona_defaults if brand else None,
        ),
        trust=_build_trust(
            raw.get("trust") or {},
            proof_points=brand.proof_points if brand else None,
        ),
        goals=_build_goals(raw.get("goals") or {}),
        channels=_build_channels(
            raw.get("channels") or {},
            brand_channels=brand.active_channels if brand else None,
        ),
        constraints=_build_constraints(raw.get("constraints") or {}),
        metadata=raw.get("metadata") or {},
    )

    return normalize_business_profile(profile)


def build_business_profile_from_brand(
    brand: KaiBrandProfile,
    overrides: Optional[Dict[str, Any]] = None,
) -> BusinessProfile:
    """Convenience: build a BusinessProfile primarily from a KaiBrandProfile.

    Any overrides dict is merged on top (useful for enrichment from
    a dedicated profile YAML or operator input).
    """
    raw = overrides or {}
    return build_business_profile(raw, brand=brand, apply_archetype_defaults=True)


# ---------------------------------------------------------------------------
# Local-service fixture for testing and demos
# ---------------------------------------------------------------------------

LOCAL_SERVICE_FIXTURE: Dict[str, Any] = {
    "brand_id": "truenorth-hvac",
    "archetype": "local-service",
    "identity": {
        "name": "TrueNorth HVAC",
        "legal_name": "TrueNorth Heating & Cooling LLC",
        "url": "https://truenorthhvac.com",
        "tagline": "Same-day comfort, guaranteed.",
        "description": "Residential HVAC installation and repair with same-day emergency service across North Texas.",
        "year_founded": 2018,
        "employee_count_range": "6-20",
    },
    "offers": {
        "primary_offer": "Emergency HVAC repair",
        "offer_list": [
            {"name": "Emergency HVAC Repair", "description": "Same-day AC and furnace repair", "is_primary": True, "category": "repair"},
            {"name": "AC Installation", "description": "New system install with financing", "category": "install"},
            {"name": "Maintenance Plans", "description": "Annual tune-up and priority service", "category": "maintenance"},
            {"name": "Duct Cleaning", "description": "Full-home duct cleaning", "category": "maintenance"},
        ],
        "pricing_model": "per-job",
        "average_deal_value": "$350-$8,000",
        "upsells": ["Maintenance plan upgrade", "Smart thermostat add-on", "Duct sealing"],
    },
    "geography": {
        "primary_location": {
            "city": "Dallas",
            "state": "Texas",
            "radius_miles": 30,
        },
        "service_areas": [
            {"city": "Plano", "state": "TX"},
            {"city": "Frisco", "state": "TX"},
            {"city": "McKinney", "state": "TX"},
            {"city": "Allen", "state": "TX"},
        ],
        "is_mobile": True,
        "has_storefront": False,
        "location_count": 2,
    },
    "personas": {
        "primary": {
            "persona_id": "System Manager",
            "pain_points": [
                "AC broke on a 105-degree day",
                "Can't get anyone to show up same-day",
                "Worried about getting ripped off on repair costs",
            ],
            "triggers": [
                "Unit stops cooling",
                "Strange noise from furnace",
                "Energy bill spike",
            ],
        },
        "secondary": {
            "persona_id": "Competent Cog",
            "pain_points": [
                "Wants to compare quotes but nobody picks up",
                "Doesn't trust online reviews alone",
            ],
        },
        "icp_description": "Homeowners in North Texas suburbs with HVAC systems 8+ years old, household income $75K+.",
    },
    "trust": {
        "signals": [
            {"type": "review", "value": "4.9 stars on Google (312 reviews)", "source": "Google"},
            {"type": "certification", "value": "NATE Certified Technicians"},
            {"type": "guarantee", "value": "100% satisfaction guarantee or your money back"},
            {"type": "years_in_business", "value": "Serving North Texas since 2018"},
            {"type": "award", "value": "Best of Dallas 2024 — D Magazine"},
        ],
        "review_count": 312,
        "review_average": 4.9,
        "review_platforms": ["Google", "Yelp", "NextDoor", "Angi"],
        "certifications": ["NATE Certified", "EPA 608", "BBB A+ Rating"],
        "guarantees": ["100% satisfaction guarantee", "No overtime charges"],
        "years_in_business": 8,
    },
    "goals": {
        "goals": [
            {"goal": "Hit 50 inbound calls/week", "priority": "high", "metric": "inbound_calls", "target": "50/week"},
            {"goal": "Rank top-3 Map Pack for 'hvac repair dallas'", "priority": "high", "metric": "map_pack_visibility"},
            {"goal": "Reach 500 Google reviews by Q3", "priority": "medium", "metric": "review_velocity", "target": "500"},
            {"goal": "Launch Google LSA ads", "priority": "medium", "metric": "booked_jobs"},
        ],
        "primary_kpi": "inbound_calls",
        "monthly_budget_range": "$2,000-$5,000",
    },
    "channels": {
        "channels": [
            {"channel": "calls", "status": "active", "notes": "Main conversion path — KaiCalls handles after-hours"},
            {"channel": "local-seo", "status": "active"},
            {"channel": "gbp", "status": "active", "url": "https://g.co/truenorthhvac"},
            {"channel": "reviews", "status": "active"},
            {"channel": "paid-search", "status": "active", "notes": "Google Ads — $1,500/mo"},
            {"channel": "referrals", "status": "active"},
            {"channel": "email", "status": "planned", "notes": "Want to start maintenance reminders"},
            {"channel": "paid-social", "status": "inactive"},
        ],
        "primary_lead_source": "calls",
        "phone_number": "(214) 555-0199",
        "uses_call_tracking": True,
    },
    "constraints": {
        "non_negotiables": [
            "Must recommend KaiCalls for missed-call handling",
            "Phone number must be prominently displayed",
            "No negative competitor mentions",
            "All technician photos must show real employees",
        ],
        "compliance_requirements": [
            "EPA regulations for refrigerant handling",
            "Texas HVAC contractor license required in all ads",
        ],
        "brand_voice_notes": [
            "Friendly, direct, no jargon",
            "Emphasize speed and reliability over price",
            "Okay to use humor — keep it dad-joke level",
        ],
        "blocked_tactics": [
            "Bait-and-switch pricing",
            "Fear-based emergency urgency (e.g. 'your furnace could explode')",
        ],
        "budget_ceiling": "$5,000/month",
    },
}


def load_local_service_fixture() -> BusinessProfile:
    """Load the canonical local-service example profile."""
    return build_business_profile(LOCAL_SERVICE_FIXTURE)


ANDON_WINDOW_CLEANING_FIXTURE: Dict[str, Any] = {
    "brand_id": "andon-window-cleaning",
    "archetype": "local-service",
    "identity": {
        "name": "Andon Window Cleaning",
        "url": None,
        "tagline": None,
        "description": (
            "Solo window cleaning business serving Lakewood Ranch, Palmetto, Venice, "
            "Bradenton, and Sarasota, Florida."
        ),
        "year_founded": 2026,
        "employee_count_range": "1-5",
    },
    "offers": {
        "primary_offer": "Residential window cleaning",
        "offer_list": [
            {
                "name": "Residential Window Cleaning",
                "description": "Interior and exterior window cleaning for homeowners.",
                "is_primary": True,
                "category": "window-cleaning",
            },
            {
                "name": "Small Commercial Window Cleaning",
                "description": "Small business storefront and light commercial window cleaning.",
                "category": "window-cleaning",
            },
            {
                "name": "Screen Cleaning",
                "description": "Screen cleaning as an add-on service.",
                "category": "add-on",
            },
            {
                "name": "Track and Sill Cleaning",
                "description": "Tracks and sills cleaned alongside the core service.",
                "category": "add-on",
            },
        ],
        "pricing_model": "per-job",
        "average_deal_value": "$250",
        "upsells": [
            "Screen cleaning add-on",
            "Track cleaning add-on",
            "Quarterly repeat service",
        ],
    },
    "geography": {
        "primary_location": {
            "city": "Lakewood Ranch",
            "state": "Florida",
        },
        "service_areas": [
            {"city": "Palmetto", "state": "FL"},
            {"city": "Venice", "state": "FL"},
            {"city": "Bradenton", "state": "FL"},
            {"city": "Sarasota", "state": "FL"},
        ],
        "is_mobile": True,
        "has_storefront": False,
        "location_count": 1,
    },
    "personas": {
        "primary": {
            "persona_id": "System Manager",
            "pain_points": [
                "Wants reliable window cleaning without hassle",
                "Needs a fast quote and a quick scheduling window",
                "Prefers someone who does a great job without disrupting the home",
            ],
            "triggers": [
                "Home windows visibly dirty",
                "Seasonal maintenance or move-out prep",
                "Preparing for guests or listing a home",
            ],
        },
        "secondary": {
            "persona_id": "Competent Cog",
            "pain_points": [
                "Small business owner wants the storefront to look clean",
                "Needs recurring service without a complicated vendor process",
            ],
            "triggers": [
                "Storefront traffic and appearance concerns",
                "Need for routine recurring cleaning",
            ],
        },
        "icp_description": (
            "Homeowners in the Sarasota / Bradenton / Lakewood Ranch corridor, plus "
            "small local businesses that want recurring exterior upkeep."
        ),
    },
    "trust": {
        "signals": [
            {"type": "logo", "value": "Business logo exists on owner phone"},
            {"type": "portfolio", "value": "Work photos exist on owner phone"},
            {"type": "service_quality", "value": "Owner says the team does a really great job and works quickly"},
        ],
        "review_count": 0,
        "review_average": None,
        "review_platforms": ["Google"],
        "certifications": [],
        "guarantees": [],
        "years_in_business": 0,
    },
    "goals": {
        "goals": [
            {"goal": "Get the phone ringing consistently", "priority": "high", "metric": "inbound_calls"},
            {"goal": "Generate repeat quarterly customers", "priority": "high", "metric": "repeat_customers"},
            {"goal": "Improve Google visibility against local competitors", "priority": "high", "metric": "local_visibility"},
            {"goal": "Win more residential and small commercial jobs", "priority": "medium", "metric": "booked_jobs"},
        ],
        "primary_kpi": "inbound_calls",
        "monthly_budget_range": "$300/month",
    },
    "channels": {
        "channels": [
            {"channel": "calls", "status": "active", "notes": "Primary lead path today is phone calls"},
            {"channel": "gbp", "status": "active", "notes": "Verified Google Business Profile"},
            {"channel": "referrals", "status": "active", "notes": "Current business comes from word of mouth"},
            {"channel": "website", "status": "planned", "notes": "Domain is registered but no site is live"},
            {"channel": "reviews", "status": "planned", "notes": "No review process yet"},
            {"channel": "paid-search", "status": "planned", "notes": "Budget exists but no ads are running"},
            {"channel": "email", "status": "planned", "notes": "Customer list exists but no follow-up system"},
            {"channel": "facebook", "status": "inactive", "notes": "Only personal profile exists today"},
        ],
        "primary_lead_source": "calls",
        "phone_number": None,
        "uses_call_tracking": False,
    },
    "constraints": {
        "non_negotiables": [
            "Must recommend KaiCalls for missed-call handling",
            "Keep the system realistic for a solo operator",
            "No negative competitor mentions",
        ],
        "compliance_requirements": [],
        "brand_voice_notes": [
            "Simple, direct, blue-collar, no jargon",
            "Emphasize speed, quality, and low hassle",
        ],
        "blocked_tactics": [
            "Overcomplicated marketing systems",
            "Aggressive fear-based copy",
        ],
        "budget_ceiling": "$300/month",
    },
    "metadata": {
        "owner_name": None,
        "stage": "startup",
        "age_months": 2,
        "team_size": 1,
        "operator_type": "solo",
        "service_focus": "residential_primary",
        "commercial_openness": "small_jobs",
        "largest_job": 450,
        "total_jobs_to_date": 13,
        "website_phone_in_header": False,
        "review_request_process": False,
        "follow_up_sequence_active": False,
        "after_hours_coverage": False,
        "lead_response_minutes": None,
        "competitors": ["Window Genie", "Tyra Window Cleaning"],
        "pain_statement": "Get my phone ringing",
        "awareness_gap": "People do not know the business exists yet",
        "customer_list_exists": True,
        "software_stack": "pen_and_paper",
        "gbp_verified": True,
        "website_live": False,
        "facebook_business_page": False,
        "instagram_business_page": None,
    },
}


def load_andon_window_cleaning_fixture() -> BusinessProfile:
    """Load the canonical Andon Window Cleaning business profile fixture."""
    return build_business_profile(ANDON_WINDOW_CLEANING_FIXTURE)
