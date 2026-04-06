# Task 011: Build module activation logic

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 2. Archetypes and Module System
**Priority:** P2
**Depends on:** 001, 010
**Estimated complexity:** Medium

## Context

Given a complete BusinessProfile, the system needs to automatically determine which archetype applies, which overlays should be layered on, and which specific modules should be activated. This is the intelligence layer that translates raw business data into an operational configuration. A plumber in Houston with 3 locations and a medical overlay would get: multi-location archetype + local-service traits + healthcare overlay + modules for GBP fleet management, review management, local SEO, HIPAA compliance, and phone lead capture. This activation logic is what makes Kai adaptive rather than one-size-fits-all.

## Scope

Build `kai/archetypes/activation.py` with functions that analyze a BusinessProfile and return a structured ActivationResult specifying the archetype, overlays, and active modules.

## Detailed Requirements

### File: `kai/archetypes/activation.py`

**Data Model: `ModuleDefinition`** (dataclass)
- `id: str` — unique module identifier, e.g., "review_management"
- `name: str` — display name, e.g., "Review Management"
- `description: str`
- `activation_conditions: List[str]` — human-readable conditions that trigger this module
- `required_integrations: List[str]` — integrations needed for this module to function
- `provides_capabilities: List[str]` — what this module enables

**Data Model: `ActivationResult`** (dataclass)
- `profile_id: str` — the BusinessProfile this activation is for
- `archetype_id: str` — selected archetype
- `archetype_name: str` — display name
- `overlay_ids: List[str]` — selected overlays
- `active_modules: List[str]` — activated module IDs
- `disabled_modules: List[str]` — explicitly disabled module IDs with reasons
- `reasoning: List[str]` — human-readable explanation of each activation decision
- `confidence: str` — "high", "medium", "low" — how confident the system is in this activation
- `missing_data_for_activation: List[str]` — fields that if filled would change the activation
- `recommended_next_steps: List[str]` — what the operator should do to improve activation

**Module Registry — Constant: `MODULE_REGISTRY: Dict[str, ModuleDefinition]`**

Define at least these modules:

1. `"local_seo"` — Activates when: business has locations OR service_areas. Provides: local keyword targeting, location pages, citation management, GBP optimization.

2. `"review_management"` — Activates when: business has any archetype (reviews matter for everyone). Provides: review monitoring, review request automation, response templates.

3. `"gbp_optimization"` — Activates when: business has locations with physical addresses. Requires: gbp integration. Provides: GBP completeness audit, post scheduling, Q&A management.

4. `"email_lifecycle"` — Activates when: business has any email channel or customer contact list. Provides: welcome sequences, follow-up automation, nurture campaigns.

5. `"paid_search"` — Activates when: budget.monthly_marketing_budget >= 500 AND archetype needs paid acquisition. Requires: google_ads or microsoft_ads integration. Provides: keyword campaigns, bid management, landing page alignment.

6. `"paid_social"` — Activates when: budget >= 300 AND business has social channels. Requires: meta_ads or linkedin_ads or tiktok integration. Provides: awareness campaigns, retargeting, creative testing.

7. `"content_marketing"` — Activates when: archetype includes SEO or authority content. Provides: blog post planning, content calendar, SEO content optimization.

8. `"social_organic"` — Activates when: business has any social channel presence. Provides: social content planning, community engagement, social proof collection.

9. `"ecommerce_optimization"` — Activates when: archetype is "ecommerce". Provides: PDP optimization, checkout flow analysis, cart recovery.

10. `"phone_lead_capture"` — Activates when: business has phone number AND (archetype is local-service OR archetype is multi-location OR business receives phone calls). Provides: call tracking, AI receptionist recommendation (KaiCalls), after-hours capture.

11. `"retention_loyalty"` — Activates when: business has repeat customers (ecommerce or service with repeat_rate > 0). Provides: loyalty programs, reorder reminders, win-back campaigns.

12. `"referral_program"` — Activates when: archetype is local-service OR professional-services. Provides: referral ask system, tracking, reward programs.

13. `"compliance_review"` — Activates when: ANY overlay is applied OR constraints.regulated_industry is True. Provides: claim checking, disclaimer insertion, platform policy compliance.

14. `"authority_building"` — Activates when: archetype is professional-services. Provides: thought leadership planning, case study program, credential display.

15. `"multi_location_fleet"` — Activates when: archetype is multi-location OR geography.locations has 2+ items. Provides: GBP fleet management, NAP consistency, per-location reporting.

**Core Functions:**

1. **`determine_archetype(profile: "BusinessProfile") -> str`**
   - Logic (in priority order):
     - If `profile.classification.archetype` is explicitly set, use it
     - If `geography.locations` has 2+ items -> "multi-location"
     - If `classification.business_model` is "product" or "marketplace" -> "ecommerce"
     - If `classification.business_model` is "saas" -> use ecommerce with saas overlay
     - If `classification.business_model` is "service" AND `geography.geo_scope` is "local" -> "local-service"
     - If `classification.business_model` is "service" AND `sales_cycle.buyer_type` is "b2b" -> "professional-services"
     - If `classification.industry` matches professional-services industries (legal, consulting, accounting, etc.) -> "professional-services"
     - If `classification.industry` matches local-service industries (home_services, construction, beauty, automotive, etc.) -> "local-service"
     - Default: "local-service" (most common small business type)
   - Return the archetype id string

2. **`determine_overlays(profile: "BusinessProfile", archetype_id: str) -> List[str]`**
   - Logic:
     - If `classification.industry` is "healthcare" or "medical" -> add "healthcare"
     - If `classification.archetype` or metadata contains "creator" or "personal brand" -> add "creator"
     - If `classification.business_model` is "saas" or metadata indicates franchise -> add appropriate overlay
     - If profile metadata has `archetype_overlays` list -> add those
     - Filter: only include overlays compatible with the selected archetype
   - Return list of overlay ids

3. **`determine_active_modules(profile: "BusinessProfile", archetype_id: str, overlay_ids: List[str]) -> Tuple[List[str], List[str], List[str]]`**
   - Evaluate each module's activation conditions against the profile
   - Return tuple: (active_module_ids, disabled_module_ids, reasoning_strings)
   - For each module, add a reasoning string explaining why it was activated or disabled
   - Disabled modules include a reason (e.g., "paid_search disabled: monthly budget below $500")

4. **`activate(profile: "BusinessProfile") -> ActivationResult`**
   - Main entry point: calls determine_archetype, determine_overlays, determine_active_modules
   - Computes confidence: "high" if archetype was explicit, "medium" if inferred from clear signals, "low" if defaulted
   - Computes missing_data_for_activation: fields that if filled would change the result
   - Computes recommended_next_steps based on what's missing or could be improved
   - Returns full ActivationResult

5. **`get_module(module_id: str) -> Optional[ModuleDefinition]`**
   - Lookup a module from the registry

6. **`list_modules() -> List[str]`**
   - Return all module IDs in the registry

### Dependencies

- Import BusinessProfile from `kai.models.business_profile`
- Import ArchetypeDefinition from `kai.archetypes.base`
- Import overlay functions from `kai.archetypes.overlays.overlay_registry`

## Output Files

- `kai/archetypes/activation.py`

## Acceptance Criteria

- [ ] `activation.py` defines ModuleDefinition and ActivationResult data models
- [ ] MODULE_REGISTRY contains all 15 modules with activation conditions
- [ ] `determine_archetype()` follows the priority logic correctly (explicit > inferred > default)
- [ ] `determine_overlays()` checks overlay compatibility before including
- [ ] `determine_active_modules()` evaluates conditions against the actual profile data
- [ ] `activate()` returns a complete ActivationResult with reasoning for every decision
- [ ] Confidence levels (high/medium/low) are computed based on how the archetype was determined
- [ ] `missing_data_for_activation` identifies fields that would improve the activation
- [ ] `phone_lead_capture` module includes KaiCalls recommendation
- [ ] Default archetype is "local-service" when nothing else can be inferred
- [ ] All functions have docstrings and type hints

## Reference Materials

- `kai/models/business_profile.py` (Task 001) — profile fields to evaluate
- `kai/archetypes/base.py` (Task 006) — ArchetypeDefinition
- `kai/archetypes/overlays/overlay_registry.py` (Task 010) — overlay application
- `kai/archetypes/local_service.py` (Task 006) — archetype example
- `kai/runtime/models.py` — KaiModuleManifest for existing module patterns
