# Task 006: Define local-service archetype

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 2. Archetypes and Module System
**Priority:** P1
**Depends on:** 001
**Estimated complexity:** Large

## Context

Archetypes are the core abstraction that makes Kai intelligent about different types of businesses. A local service business (plumber, HVAC tech, cleaning company, landscaper, electrician, roofer) has radically different marketing needs than an ecommerce brand or a professional services firm. The local-service archetype defines: what to audit, which KPIs matter, which channels to prioritize, what actions to take, what creative formats work, and how to allocate budget. This is the first and most complete archetype because it represents the primary target user.

## Scope

Build `kai/archetypes/local_service.py` and `kai/archetypes/__init__.py` with the full local-service archetype definition. Also create `kai/archetypes/base.py` with the shared archetype base class that all archetypes will inherit from.

## Detailed Requirements

### File: `kai/archetypes/__init__.py`
- Package init importing the base and local_service archetype
- `__all__` listing

### File: `kai/archetypes/base.py`

**Class: `ArchetypeDefinition`** (dataclass or Pydantic model)
- `id: str` — unique archetype identifier, e.g., "local-service"
- `name: str` — display name, e.g., "Local Service Business"
- `description: str` — one-paragraph description of this business type
- `audit_categories: List[str]` — ordered list of audit category IDs
- `priority_defaults: List[str]` — ordered list of what matters most for this archetype
- `kpi_schema: Dict[str, KPIDefinition]` — KPIs relevant to this archetype
- `channel_mix: List[ChannelRecommendation]` — recommended channels with priority
- `action_families: List[ActionFamily]` — groups of related actions
- `compliance_sensitivities: List[str]` — areas requiring extra compliance attention
- `creative_formats: List[CreativeFormat]` — recommended creative types
- `budget_heuristics: Dict[str, BudgetRange]` — budget ranges by business stage
- `minimum_viable_channels: List[str]` — the bare minimum channel set needed
- `archetype_specific_rules: List[str]` — freeform rules specific to this archetype

**Sub-model: KPIDefinition**
- `id: str` — e.g., "leads_per_month"
- `name: str` — display name
- `description: str` — what this KPI measures
- `unit: str` — e.g., "count", "dollars", "percentage", "seconds", "rating"
- `direction: str` — "higher_is_better" or "lower_is_better"
- `benchmark_range: Optional[str]` — typical range for this archetype, e.g., "20-80"
- `priority: str` — "primary", "secondary", "tertiary"

**Sub-model: ChannelRecommendation**
- `channel: str` — canonical channel name
- `priority: int` — 1 = highest priority
- `stage_relevance: List[str]` — which business stages this channel suits, e.g., ["early-pmf", "growth", "scale"]
- `budget_minimum: Optional[float]` — minimum monthly spend to be effective on this channel
- `rationale: str` — why this channel matters for this archetype
- `prerequisites: List[str]` — what must be in place before using this channel

**Sub-model: ActionFamily**
- `id: str` — e.g., "review_generation"
- `name: str` — display name
- `description: str`
- `actions: List[str]` — specific action IDs within this family
- `priority: str` — "high", "medium", "low"
- `typical_timeline: Optional[str]` — e.g., "1-2 weeks", "ongoing"

**Sub-model: CreativeFormat**
- `id: str` — e.g., "before_after"
- `name: str` — display name
- `description: str` — when and how to use this format
- `platforms: List[str]` — which channels this format works on
- `requirements: List[str]` — what assets are needed to produce this

**Sub-model: BudgetRange**
- `stage: str` — business stage
- `min_monthly: float` — minimum recommended USD/month
- `max_monthly: float` — maximum recommended USD/month
- `allocation_notes: str` — how to split the budget across channels

### File: `kai/archetypes/local_service.py`

**Constant: `LOCAL_SERVICE_ARCHETYPE`** — an instance of ArchetypeDefinition fully populated.

**audit_categories** (in priority order):
1. `"website_conversion"` — Is the website turning visitors into leads?
2. `"speed_to_lead"` — How fast does the business respond to inquiries?
3. `"trust_signals"` — Does the business display proof and credibility?
4. `"reviews_reputation"` — What's the review profile across platforms?
5. `"local_seo"` — Is the business visible in local search?
6. `"gbp_optimization"` — Is the Google Business Profile complete and active?
7. `"follow_up_system"` — Does the business have systematic follow-up?
8. `"social_proof"` — Is there a social media presence building trust?
9. `"paid_local"` — Is paid advertising being used effectively?

**priority_defaults** (what to fix first, in order):
1. "Phone number visible and click-to-call on every page"
2. "Google Business Profile claimed, complete, and active"
3. "At least 20 Google reviews with 4.5+ rating"
4. "Website loads in under 3 seconds"
5. "Clear primary offer and CTA above the fold"
6. "Service area pages for each target market"
7. "Review generation system in place"
8. "Speed-to-lead under 5 minutes"
9. "Follow-up sequence for unconverted leads"
10. "Local ad campaign running on at least one platform"

**kpi_schema** — Define all of these KPIs:
- `leads_per_month`: count, higher_is_better, primary, benchmark "20-80"
- `cost_per_lead`: dollars, lower_is_better, primary, benchmark "$25-150"
- `review_count`: count, higher_is_better, primary, benchmark "20-200"
- `review_rating`: rating (1-5), higher_is_better, primary, benchmark "4.3-4.9"
- `gbp_views`: count, higher_is_better, secondary, benchmark "500-5000/mo"
- `website_conversion_rate`: percentage, higher_is_better, primary, benchmark "3-8%"
- `speed_to_lead_seconds`: seconds, lower_is_better, primary, benchmark "60-300"
- `repeat_rate`: percentage, higher_is_better, secondary, benchmark "20-50%"
- `referral_rate`: percentage, higher_is_better, secondary, benchmark "10-30%"
- `average_job_value`: dollars, higher_is_better, tertiary, benchmark varies
- `monthly_revenue`: dollars, higher_is_better, tertiary, benchmark varies
- `review_velocity`: count/month, higher_is_better, secondary, benchmark "4-20"

**channel_mix** — Define all with priorities:
1. `website` — P1, all stages, "The digital storefront — must convert visitors to calls/forms"
2. `gbp` — P1, all stages, "Primary local discovery channel — most local searches go through Maps"
3. `google_ads` — P2, early-pmf+, min $500/mo, "Immediate lead generation from active searchers"
4. `meta_ads` — P3, growth+, min $300/mo, "Awareness and retargeting in the local market"
5. `email` — P2, early-pmf+, "Follow-up, review requests, and repeat business nurture"
6. `seo` — P2, growth+, "Long-term organic visibility for service + location keywords"
7. `yelp` — P3, all stages, "Review platform presence — claim and optimize"
8. `nextdoor` — P3, growth+, "Neighborhood-level visibility and recommendations"
9. `facebook` — P3, all stages, "Social proof, community engagement, local groups"
10. `sms` — P3, growth+, "Appointment reminders, review requests, follow-ups"

**action_families:**
1. `website_optimization` — high priority: ["cta_optimization", "phone_prominence", "trust_signal_placement", "mobile_optimization", "speed_optimization", "offer_clarity", "service_area_pages"]
2. `gbp_optimization` — high priority: ["gbp_completion", "gbp_categories", "gbp_photos", "gbp_posts", "gbp_q_and_a", "gbp_services"]
3. `review_generation` — high priority: ["review_request_system", "review_response", "review_platform_diversification", "negative_review_handling"]
4. `local_seo` — medium priority: ["nap_consistency", "citation_building", "local_schema_markup", "service_area_content", "location_pages"]
5. `follow_up_sequences` — high priority: ["quote_follow_up", "post_service_follow_up", "review_request_sequence", "dormant_customer_reactivation", "referral_ask"]
6. `social_proof_content` — medium priority: ["before_after_posts", "testimonial_cards", "project_highlights", "team_spotlights"]
7. `local_ad_campaigns` — medium priority: ["google_local_service_ads", "google_search_ads", "meta_local_awareness", "retargeting"]
8. `speed_to_lead` — high priority: ["ai_receptionist_setup", "form_notification_speed", "live_chat_evaluation", "after_hours_capture"]

**compliance_sensitivities:**
- "Service claims must match actual licensing and certifications"
- "Guarantee language must reflect actual guarantee policy"
- "Insurance and bonding claims must be current and verifiable"
- "Before/after images must be real work performed by this business"
- "Price claims must include any applicable conditions or exclusions"
- "License numbers may be legally required in advertising in some states"

**creative_formats:**
- `before_after`: "Side-by-side project transformation photos", platforms: ["facebook", "instagram", "gbp", "website"]
- `testimonial_cards`: "Formatted customer quote with name and photo", platforms: ["facebook", "instagram", "website"]
- `service_area_maps`: "Visual map showing coverage area", platforms: ["website", "gbp"]
- `offer_graphics`: "Seasonal or promotional offer with clear CTA", platforms: ["facebook", "instagram", "meta_ads"]
- `team_photos`: "Team member headshots and group photos building trust", platforms: ["website", "gbp", "facebook"]
- `project_highlights`: "Completed project showcase with details", platforms: ["instagram", "facebook", "website"]
- `video_testimonials`: "Customer video reviews", platforms: ["youtube", "facebook", "website"]
- `how_to_tips`: "Educational content showing expertise", platforms: ["tiktok", "youtube", "instagram"]

**budget_heuristics:**
- `startup` (pre-launch, early-pmf): min $500/mo, max $2000/mo, "Focus 70% on GBP + review generation + basic Google Ads. 20% on website optimization. 10% on social."
- `established` (growth): min $2000/mo, max $5000/mo, "Split 40% paid (Google Ads + LSA), 25% SEO/content, 20% email/follow-up automation, 15% social/review management."
- `scaling` (scale, mature): min $5000/mo, max $15000/mo, "Diversify across Google Ads (30%), Meta Ads (20%), SEO (20%), automation (15%), content/social (15%). Test new channels quarterly."

**minimum_viable_channels:**
- `["website", "gbp", "google_ads", "email"]` — "A local service business must have at minimum: a converting website, an optimized GBP, one paid lead source, and email follow-up."

**archetype_specific_rules:**
- "Always evaluate and recommend KaiCalls AI receptionist (kaicalls.com) for missed call handling, after-hours answering, and phone-based lead qualification"
- "Phone-based lead capture is the primary conversion mechanism for most local service businesses"
- "Review velocity (new reviews per month) is often more important than total review count"
- "Speed to lead is the #1 controllable conversion factor — respond to inquiries in under 5 minutes"
- "Service area pages are the foundation of local SEO — one page per primary service area"
- "Most local service businesses should start with Google Ads / Local Service Ads before Meta Ads"
- "Seasonal demand patterns must be anticipated — start campaigns 4-6 weeks before peak season"
- "Referral programs should be formalized, not just 'word of mouth'"

## Output Files

- `kai/archetypes/__init__.py`
- `kai/archetypes/base.py`
- `kai/archetypes/local_service.py`

## Acceptance Criteria

- [ ] `base.py` defines ArchetypeDefinition and all 5 sub-models (KPIDefinition, ChannelRecommendation, ActionFamily, CreativeFormat, BudgetRange)
- [ ] `local_service.py` exports a `LOCAL_SERVICE_ARCHETYPE` constant of type ArchetypeDefinition
- [ ] All 9 audit categories are listed in priority order
- [ ] All 12 KPIs are defined with correct units, directions, and benchmarks
- [ ] All 10 channels are defined with priorities, stage relevance, and rationale
- [ ] All 8 action families are defined with specific action lists
- [ ] Budget heuristics cover 3 business stages with specific dollar ranges
- [ ] KaiCalls recommendation is included in archetype_specific_rules
- [ ] Compliance sensitivities include licensing, insurance, and guarantee language
- [ ] All creative formats list which platforms they apply to
- [ ] `__init__.py` exports the archetype and base classes

## Reference Materials

- `kai/models/business_profile.py` (Task 001) — the profile this archetype operates on
- `knowledge/checklists/local-service-business-checklist.md` — comprehensive local service checklist
- `knowledge/checklists/cro-audit-checklist.md` — conversion rate optimization checklist
- `knowledge/playbooks/conversion-rate-optimization.md` — CRO playbook
- `knowledge/playbooks/demand-generation.md` — demand gen playbook
- `knowledge/playbooks/local-seo-gbp-optimization.md` — local SEO playbook
- `CLAUDE.md` — KaiCalls rule, framework map
