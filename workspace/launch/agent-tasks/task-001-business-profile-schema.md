# Task 001: Define canonical BusinessProfile schema

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 1. Workspace and Business Understanding
**Priority:** P1 (foundational — nearly everything depends on this)
**Depends on:** None
**Estimated complexity:** Large

## Context

The Kai Marketing OS needs a single canonical data model that represents ANY business the system might operate on. This BusinessProfile is the foundational schema consumed by every downstream system — audits, proposals, action plans, archetype activation, and workspace state. A partial prototype already exists at `kai/runtime/business_profile.py` using dataclasses, but the canonical version needs to be comprehensive, well-typed, and live at `kai/models/business_profile.py` as the authoritative source.

The existing prototype in `kai/runtime/business_profile.py` covers identity, offers, geography, personas, trust signals, digital presence, and goals. The new canonical version must preserve compatibility with those structures while expanding coverage significantly and moving to a cleaner module path.

## Scope

Create the canonical BusinessProfile Pydantic model at `kai/models/business_profile.py` and a package init at `kai/models/__init__.py` that exports all models. This is the single source of truth for business representation across the entire Kai system.

## Detailed Requirements

### File: `kai/models/business_profile.py`

Use Pydantic `BaseModel` with the same fallback pattern found in `gateway/models.py` (try importing pydantic, fall back to a minimal BaseModel if unavailable). Every sub-model should be its own class.

**Sub-model: BusinessIdentity**
- `business_name: str` — primary display name
- `dba: Optional[str]` — "doing business as" name if different
- `legal_entity: Optional[str]` — legal entity name (LLC, Inc, etc.)
- `website_url: Optional[str]` — primary website URL
- `phone: Optional[str]` — primary business phone
- `email: Optional[str]` — primary business email
- `logo_url: Optional[str]` — URL or path to logo asset
- `tagline: Optional[str]` — short brand tagline
- `elevator_pitch: Optional[str]` — 1-2 sentence pitch describing what the business does and for whom

**Sub-model: BusinessClassification**
- `industry: Optional[str]` — e.g., "home services", "legal", "ecommerce"
- `vertical: Optional[str]` — more specific than industry, e.g., "personal injury law", "residential plumbing"
- `business_model: Optional[str]` — one of: "service", "product", "hybrid", "marketplace", "saas", "agency"
- `archetype: Optional[str]` — one of: "local-service", "ecommerce", "professional-services", "multi-location", "creator", "saas"
- `stage: Optional[str]` — one of: "pre-launch", "early-pmf", "growth", "scale", "mature"

**Sub-model: Offer**
- `name: str` — offer/service/product name
- `description: Optional[str]` — what this offer includes
- `price_range: Optional[str]` — human-readable, e.g., "$200-500", "$49/mo"
- `margin_tier: Optional[str]` — one of: "low", "medium", "high", "premium"
- `is_seasonal: bool = False` — whether demand is seasonal
- `is_primary: bool = False` — whether this is the flagship offer
- `primary_cta: Optional[str]` — the main call to action for this offer, e.g., "Book Now", "Get Quote"
- `category: Optional[str]` — grouping category

**Sub-model: Location**
- `name: Optional[str]` — location name/label
- `address: Optional[str]` — full street address
- `city: Optional[str]`
- `state: Optional[str]`
- `zip_code: Optional[str]`
- `country: str = "US"`
- `phone: Optional[str]` — location-specific phone
- `hours: Optional[Dict[str, str]]` — day of week -> hours string
- `gbp_url: Optional[str]` — Google Business Profile URL
- `is_primary: bool = False`

**Sub-model: BusinessGeography**
- `service_areas: List[str]` — list of service area descriptions (cities, regions, zip codes)
- `locations: List[Location]` — physical locations
- `geo_scope: Optional[str]` — one of: "local", "regional", "national", "global"
- `is_mobile: bool = False` — whether the business travels to customers
- `has_storefront: bool = False`

**Sub-model: PersonaProfile**
- `name: str` — persona name or label
- `demographics: Optional[str]` — age, income, etc. as description
- `pain_points: List[str]` — what keeps this persona up at night
- `buying_triggers: List[str]` — what makes them act now
- `objections: List[str]` — why they hesitate
- `channels_used: List[str]` — where they spend time (google, facebook, nextdoor, etc.)
- `decision_timeline: Optional[str]` — how long from awareness to purchase
- `is_primary: bool = False`

**Sub-model: TrustSignal**
- `signal_type: str` — one of: "testimonial", "case_study", "certification", "award", "media_mention", "notable_client", "statistic"
- `title: Optional[str]`
- `content: str` — the actual testimonial text, case study summary, cert name, etc.
- `source: Optional[str]` — attribution
- `url: Optional[str]` — link to proof
- `date: Optional[str]`

**Sub-model: TrustProfile**
- `testimonials: List[TrustSignal]`
- `case_studies: List[TrustSignal]`
- `certifications: List[str]`
- `awards: List[str]`
- `years_in_business: Optional[int]`
- `team_size: Optional[str]` — e.g., "1-5", "6-20", "21-50"
- `notable_clients: List[str]`
- `insurance_details: Optional[str]`
- `licenses: List[str]`

**Sub-model: GoalsAndKPIs**
- `primary_goals: List[str]` — e.g., ["increase leads by 30%", "launch in new market"]
- `target_kpis: Dict[str, Any]` — mapping KPI name to target value, e.g., {"leads_per_month": 50, "cost_per_lead": 75}
- `timeframe: Optional[str]` — e.g., "Q2 2026", "next 90 days"
- `north_star_metric: Optional[str]` — the single most important metric

**Sub-model: ChannelPresence**
- `platform: str` — normalized platform name
- `url: Optional[str]` — profile/page URL
- `is_connected: bool = False` — whether Kai has API access
- `is_active: bool = False` — whether the business is actively using it
- `last_activity: Optional[str]` — ISO date or description
- `follower_count: Optional[int]`
- `notes: Optional[str]`

**Sub-model: BusinessConstraints**
- `compliance_notes: List[str]` — regulatory or compliance notes
- `regulated_industry: bool = False`
- `claims_restrictions: List[str]` — things the business cannot claim in marketing
- `brand_voice_notes: Optional[str]` — freeform brand voice guidance
- `topics_to_avoid: List[str]` — topics that must never appear in content

**Sub-model: BudgetAndRisk**
- `monthly_marketing_budget: Optional[float]` — in USD
- `risk_tolerance: Optional[str]` — one of: "conservative", "moderate", "aggressive"
- `auto_execution_enabled: bool = False` — whether the system can take action without human approval
- `max_auto_spend_per_action: Optional[float]` — maximum USD the system can spend on a single action without approval

**Sub-model: BuyerSalesCycle**
- `buyer_type: Optional[str]` — one of: "b2b", "b2c", "b2b2c", "d2c"
- `sales_cycle_length: Optional[str]` — e.g., "same-day", "1-2 weeks", "3-6 months"
- `average_deal_size: Optional[float]` — in USD
- `decision_makers: List[str]` — roles involved in buying decision
- `sales_process: Optional[str]` — description of how deals close

**Sub-model: BrandVoice**
- `tone_descriptors: List[str]` — e.g., ["professional", "warm", "direct"]
- `writing_samples: List[str]` — URLs or inline samples of approved writing
- `approved_messaging_blocks: List[str]` — pre-approved copy blocks
- `competitor_differentiation: Optional[str]` — how this brand is different from competitors
- `personality_traits: List[str]` — e.g., ["authoritative", "approachable"]

**Sub-model: OperatorCapacity**
- `operator_hours_per_week: Optional[float]` — how many hours the human operator can dedicate
- `operator_skill_level: Optional[str]` — one of: "beginner", "intermediate", "advanced", "expert"
- `preferred_channels: List[str]` — channels the operator prefers to manage
- `delegation_preferences: Optional[str]` — what the operator wants the system to handle vs. do themselves

**Top-level: BusinessProfile**
- `id: str` — unique identifier for this business profile
- `identity: BusinessIdentity`
- `classification: BusinessClassification`
- `offers: List[Offer]`
- `geography: BusinessGeography`
- `personas: List[PersonaProfile]`
- `trust: TrustProfile`
- `goals: GoalsAndKPIs`
- `channels: List[ChannelPresence]`
- `constraints: BusinessConstraints`
- `budget: BudgetAndRisk`
- `sales_cycle: BuyerSalesCycle`
- `brand_voice: BrandVoice`
- `operator: OperatorCapacity`
- `raw_notes: Optional[str]` — freeform operator notes that don't fit elsewhere
- `created_at: Optional[str]` — ISO timestamp
- `updated_at: Optional[str]` — ISO timestamp
- `profile_version: str = "1.0.0"` — schema version for forward compatibility
- `metadata: Dict[str, Any]` — catch-all for anything not yet modeled

Every field that is a list should default to an empty list. Every field that is Optional should default to None. Every sub-model should have sensible defaults so a partially-filled BusinessProfile is always valid Python.

### File: `kai/models/__init__.py`

- Import and re-export every model class from `business_profile.py`
- Use `__all__` to make exports explicit
- Include a module docstring explaining this is the canonical model package

### Compatibility

- The existing `kai/runtime/business_profile.py` and `kai/runtime/models.py` use `dataclass` + `SerializableModel`. The new canonical models use Pydantic (with fallback). The two can coexist during migration. Do NOT modify the `kai/runtime/` files.
- Follow the import fallback pattern from `gateway/models.py` exactly: try importing from pydantic, fall back to a minimal BaseModel/Field shim.

## Output Files

- `kai/models/__init__.py`
- `kai/models/business_profile.py`

## Acceptance Criteria

- [ ] `kai/models/business_profile.py` exists and contains all 15 sub-models plus the top-level BusinessProfile
- [ ] Every field listed above is present with the correct type annotation and default value
- [ ] The pydantic import fallback pattern matches `gateway/models.py`
- [ ] `kai/models/__init__.py` exports all model classes via `__all__`
- [ ] No imports from `kai/runtime/` — this is a standalone canonical module
- [ ] All list fields default to `[]` via `Field(default_factory=list)` (not mutable default)
- [ ] All dict fields default to `{}` via `Field(default_factory=dict)`
- [ ] The file contains a module docstring and inline comments grouping the sub-models
- [ ] A `BusinessProfile` can be instantiated with only `id` and `identity` (everything else has defaults) — verify mentally, do not run code
- [ ] `profile_version` field exists for future schema migration support

## Reference Materials

- `kai/runtime/business_profile.py` — existing prototype to preserve compatibility with
- `kai/runtime/models.py` — existing SerializableModel and KaiBrandProfile patterns
- `gateway/models.py` — Pydantic import fallback pattern to replicate
- `config.example.yaml` — existing config structure showing workspace/product fields
- `CLAUDE.md` — full project context
