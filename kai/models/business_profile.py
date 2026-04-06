"""Canonical BusinessProfile schema for the Kai Marketing OS.

This is the single source of truth for representing ANY business the Kai
system operates on.  Every downstream system -- audits, proposals, action
plans, archetype activation, workspace state -- consumes this model.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.

Migration note
--------------
The older prototype at ``kai/runtime/business_profile.py`` uses stdlib
dataclasses + ``SerializableModel``.  The two can coexist during the
migration period.  This module does **not** import anything from
``kai/runtime/``.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Identity & Classification
# ============================================================================


class BusinessIdentity(BaseModel):
    """Brand identity and basic contact information."""

    business_name: str
    dba: Optional[str] = None
    legal_entity: Optional[str] = None
    website_url: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    logo_url: Optional[str] = None
    tagline: Optional[str] = None
    elevator_pitch: Optional[str] = None


class BusinessClassification(BaseModel):
    """Industry vertical, business model, archetype, and growth stage."""

    industry: Optional[str] = None
    vertical: Optional[str] = None
    business_model: Optional[str] = None  # "service", "product", "hybrid", "marketplace", "saas", "agency"
    archetype: Optional[str] = None  # "local-service", "ecommerce", "professional-services", "multi-location", "creator", "saas"
    stage: Optional[str] = None  # "pre-launch", "early-pmf", "growth", "scale", "mature"


# ============================================================================
# Offers
# ============================================================================


class Offer(BaseModel):
    """A single service or product the business sells."""

    name: str
    description: Optional[str] = None
    price_range: Optional[str] = None  # Human-readable, e.g. "$200-500", "$49/mo"
    margin_tier: Optional[str] = None  # "low", "medium", "high", "premium"
    is_seasonal: bool = False
    is_primary: bool = False
    primary_cta: Optional[str] = None  # e.g. "Book Now", "Get Quote"
    category: Optional[str] = None


# ============================================================================
# Geography & Locations
# ============================================================================


class Location(BaseModel):
    """A single physical business location."""

    name: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    country: str = "US"
    phone: Optional[str] = None  # Location-specific phone
    hours: Optional[Dict[str, str]] = None  # Day of week -> hours string
    gbp_url: Optional[str] = None  # Google Business Profile URL
    is_primary: bool = False


class BusinessGeography(BaseModel):
    """Where the business operates -- service areas, locations, and scope."""

    service_areas: List[str] = Field(default_factory=list)
    locations: List[Location] = Field(default_factory=list)
    geo_scope: Optional[str] = None  # "local", "regional", "national", "global"
    is_mobile: bool = False
    has_storefront: bool = False


# ============================================================================
# Personas
# ============================================================================


class PersonaProfile(BaseModel):
    """An audience persona this business targets."""

    name: str
    demographics: Optional[str] = None
    pain_points: List[str] = Field(default_factory=list)
    buying_triggers: List[str] = Field(default_factory=list)
    objections: List[str] = Field(default_factory=list)
    channels_used: List[str] = Field(default_factory=list)
    decision_timeline: Optional[str] = None
    is_primary: bool = False


# ============================================================================
# Trust Signals & Profile
# ============================================================================


class TrustSignal(BaseModel):
    """A single proof or trust asset.

    ``signal_type`` should be one of: ``"testimonial"``, ``"case_study"``,
    ``"certification"``, ``"award"``, ``"media_mention"``,
    ``"notable_client"``, ``"statistic"``.
    """

    signal_type: str
    title: Optional[str] = None
    content: str
    source: Optional[str] = None
    url: Optional[str] = None
    date: Optional[str] = None


class TrustProfile(BaseModel):
    """Aggregated trust signals, certifications, awards, and social proof."""

    testimonials: List[TrustSignal] = Field(default_factory=list)
    case_studies: List[TrustSignal] = Field(default_factory=list)
    certifications: List[str] = Field(default_factory=list)
    awards: List[str] = Field(default_factory=list)
    years_in_business: Optional[int] = None
    team_size: Optional[str] = None  # e.g. "1-5", "6-20", "21-50"
    notable_clients: List[str] = Field(default_factory=list)
    insurance_details: Optional[str] = None
    licenses: List[str] = Field(default_factory=list)


# ============================================================================
# Goals & KPIs
# ============================================================================


class GoalsAndKPIs(BaseModel):
    """Business goals, target KPIs, and the north-star metric."""

    primary_goals: List[str] = Field(default_factory=list)
    target_kpis: Dict[str, Any] = Field(default_factory=dict)
    timeframe: Optional[str] = None  # e.g. "Q2 2026", "next 90 days"
    north_star_metric: Optional[str] = None


# ============================================================================
# Channel Presence
# ============================================================================


class ChannelPresence(BaseModel):
    """A single marketing channel and its current status."""

    platform: str  # Normalized platform name
    url: Optional[str] = None
    is_connected: bool = False  # Whether Kai has API access
    is_active: bool = False  # Whether the business actively uses it
    last_activity: Optional[str] = None  # ISO date or description
    follower_count: Optional[int] = None
    notes: Optional[str] = None


# ============================================================================
# Constraints
# ============================================================================


class BusinessConstraints(BaseModel):
    """Regulatory, compliance, and brand guardrails."""

    compliance_notes: List[str] = Field(default_factory=list)
    regulated_industry: bool = False
    claims_restrictions: List[str] = Field(default_factory=list)
    brand_voice_notes: Optional[str] = None
    topics_to_avoid: List[str] = Field(default_factory=list)


# ============================================================================
# Budget & Risk
# ============================================================================


class BudgetAndRisk(BaseModel):
    """Marketing budget, risk tolerance, and automation limits."""

    monthly_marketing_budget: Optional[float] = None  # USD
    risk_tolerance: Optional[str] = None  # "conservative", "moderate", "aggressive"
    auto_execution_enabled: bool = False
    max_auto_spend_per_action: Optional[float] = None  # Max USD per action without approval


# ============================================================================
# Buyer & Sales Cycle
# ============================================================================


class BuyerSalesCycle(BaseModel):
    """How the business sells -- buyer type, cycle length, and deal size."""

    buyer_type: Optional[str] = None  # "b2b", "b2c", "b2b2c", "d2c"
    sales_cycle_length: Optional[str] = None  # e.g. "same-day", "1-2 weeks", "3-6 months"
    average_deal_size: Optional[float] = None  # USD
    decision_makers: List[str] = Field(default_factory=list)
    sales_process: Optional[str] = None


# ============================================================================
# Brand Voice
# ============================================================================


class BrandVoice(BaseModel):
    """Brand voice, tone, and approved messaging assets."""

    tone_descriptors: List[str] = Field(default_factory=list)
    writing_samples: List[str] = Field(default_factory=list)
    approved_messaging_blocks: List[str] = Field(default_factory=list)
    competitor_differentiation: Optional[str] = None
    personality_traits: List[str] = Field(default_factory=list)


# ============================================================================
# Operator Capacity
# ============================================================================


class OperatorCapacity(BaseModel):
    """Human operator availability, skill level, and delegation preferences."""

    operator_hours_per_week: Optional[float] = None
    operator_skill_level: Optional[str] = None  # "beginner", "intermediate", "advanced", "expert"
    preferred_channels: List[str] = Field(default_factory=list)
    delegation_preferences: Optional[str] = None


# ============================================================================
# Top-level BusinessProfile
# ============================================================================


class BusinessProfile(BaseModel):
    """Canonical business representation for the entire Kai Marketing OS.

    Every downstream system -- audits, proposals, action plans, archetype
    activation, and workspace state -- consumes this model.

    A ``BusinessProfile`` can be instantiated with only ``id`` and
    ``identity``; every other field carries a sensible default.

    The ``profile_version`` field supports forward-compatible schema
    migrations.
    """

    id: str
    identity: BusinessIdentity
    classification: BusinessClassification = Field(default_factory=BusinessClassification)
    offers: List[Offer] = Field(default_factory=list)
    geography: BusinessGeography = Field(default_factory=BusinessGeography)
    personas: List[PersonaProfile] = Field(default_factory=list)
    trust: TrustProfile = Field(default_factory=TrustProfile)
    goals: GoalsAndKPIs = Field(default_factory=GoalsAndKPIs)
    channels: List[ChannelPresence] = Field(default_factory=list)
    constraints: BusinessConstraints = Field(default_factory=BusinessConstraints)
    budget: BudgetAndRisk = Field(default_factory=BudgetAndRisk)
    sales_cycle: BuyerSalesCycle = Field(default_factory=BuyerSalesCycle)
    brand_voice: BrandVoice = Field(default_factory=BrandVoice)
    operator: OperatorCapacity = Field(default_factory=OperatorCapacity)
    raw_notes: Optional[str] = None
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    profile_version: str = "1.0.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
