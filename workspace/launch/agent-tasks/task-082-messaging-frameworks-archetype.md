# Task 082: Build messaging frameworks by archetype

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** Cross-Cutting Creative
**Priority:** P1
**Depends on:** 006, 007, 008, 009
**Estimated complexity:** Large

## Context

Different business archetypes need fundamentally different messaging approaches. A plumber's marketing speaks to urgency, trust, and local reliability; an ecommerce brand speaks to product quality, social proof, and scarcity; a law firm speaks to expertise, credentials, and empathy. The messaging frameworks provide structured libraries of message angles, objection handlers, seasonal hooks, and CTA patterns specific to each archetype. The copy generation engine (Task 028), creative variant engine (Task 084), and landing page generator (Task 085) all pull from these frameworks to produce on-brand, archetype-appropriate content. This is the "voice" layer that makes Kai's output sound like a marketing expert for each specific business type.

## Scope

Create `kai/creative/messaging_frameworks/` module with four archetype-specific messaging framework files plus a base model and a router function.

## Detailed Requirements

### File: `kai/creative/__init__.py`
- Module docstring for the creative system
- Export key classes

### File: `kai/creative/messaging_frameworks/__init__.py`
- Export all messaging framework classes and the router function

### File: `kai/creative/messaging_frameworks/base.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Model: MessageAngle**
- `angle_name: str` — e.g., "reliability", "urgency", "social_proof"
- `description: str` — when to use this angle
- `headline_templates: List[str]` — 5+ headline templates using this angle (with {placeholders})
- `subheadline_templates: List[str]` — 3+ subheadline templates
- `value_props: List[str]` — value propositions that support this angle
- `tone: str` — "confident", "empathetic", "urgent", "authoritative", "conversational"
- `best_for: List[str]` — which content types this angle works best for (e.g., "landing_page", "ad", "email")

**Model: ObjectionHandler**
- `objection: str` — the customer objection (e.g., "It costs too much")
- `reframe: str` — how to reframe the objection (e.g., "The cost of NOT fixing it is higher")
- `response_templates: List[str]` — 3+ response copy templates
- `proof_type: str` — what type of proof works best: "testimonial", "statistic", "case_study", "guarantee", "comparison"

**Model: SeasonalHook**
- `season_or_event: str` — "spring", "summer", "fall", "winter", "new_year", "tax_season", "back_to_school", "black_friday", "end_of_year", etc.
- `relevance_months: List[int]` — which months this applies to (1-12)
- `hook_angle: str` — how to connect the season to the business
- `headline_templates: List[str]` — 3+ seasonal headline templates
- `offer_suggestions: List[str]` — seasonal offer ideas
- `urgency_element: str` — what creates natural urgency (e.g., "before winter hits", "while supplies last")

**Model: CTATemplate**
- `cta_text: str` — e.g., "Get Your Free Quote"
- `cta_type: str` — "primary", "secondary", "soft"
- `funnel_stage: str` — "awareness", "consideration", "decision"
- `best_for: List[str]` — content types this CTA works for
- `supporting_text: Optional[str]` — text that appears near the CTA (e.g., "No obligation. Takes 30 seconds.")

**Model: MessagingFramework**
- `archetype: str`
- `core_message: str` — the single most important message for this archetype
- `message_angles: List[MessageAngle]`
- `objection_handlers: List[ObjectionHandler]`
- `seasonal_hooks: List[SeasonalHook]`
- `cta_library: List[CTATemplate]`
- `tone_guidelines: Dict[str, str]` — {channel: recommended_tone}
- `forbidden_phrases: List[str]` — phrases that never work for this archetype
- `proof_priorities: List[str]` — ordered list of most effective proof types

### File: `kai/creative/messaging_frameworks/local_service.py`

**Function: build_local_service_messaging() -> MessagingFramework**

Core message: "We are the trusted, reliable choice in your neighborhood"

Message angles (minimum 6):
- **Reliability**: "We show up on time, every time" — templates for dependability, consistency, track record
- **Speed/Urgency**: "Emergency at 2am? We answer." — templates for 24/7 availability, same-day service
- **Local Trust**: "Your neighbors chose us 500+ times" — templates for community presence, local reputation
- **Quality Guarantee**: "Done right or we come back free" — templates for workmanship guarantees
- **Customer Results**: "See what we did for [Customer Name]" — templates for before/after, case studies
- **KaiCalls Integration**: "Never miss a call — our AI receptionist answers 24/7" — templates for always-available phone response, instant lead capture

Objection handlers (minimum 5):
- "It costs too much" → reframe to cost of inaction, value over time, financing options
- "I can do it myself" → reframe to risk, time cost, warranty/insurance, code compliance
- "I found someone cheaper" → reframe to experience, reviews, guarantee, hidden costs
- "I need to think about it" → reframe to urgency, limited availability, price increase risk
- "I'm not sure you do this type of work" → reframe to service breadth, specialization, examples

Seasonal hooks (minimum 4):
- Spring: maintenance/cleanup, "Get ahead of the season"
- Summer: peak demand, "Book now before the rush"
- Fall: winterization, "Protect your home before winter"
- Winter: emergency services, "Don't get caught in the cold"

CTA library (minimum 8):
- "Get Your Free Quote" (primary, decision)
- "Call Now" (primary, decision)
- "Schedule a Free Inspection" (primary, consideration)
- "See Our Work" (secondary, consideration)
- "Read Our Reviews" (soft, awareness)
- "Get a Same-Day Estimate" (primary, decision)
- "Talk to a Pro" (primary, consideration)
- "See Pricing" (secondary, consideration)

Tone guidelines:
- website: "confident, professional, approachable"
- social: "friendly, community-focused, helpful"
- ads: "direct, benefit-focused, urgent"
- email: "personal, professional, concise"
- reviews: "grateful, responsive, professional"

### File: `kai/creative/messaging_frameworks/ecommerce.py`

**Function: build_ecommerce_messaging() -> MessagingFramework**

Core message: "Products you'll love, from a brand you can trust"

Message angles (minimum 6):
- **Product Quality**: materials, craftsmanship, sourcing
- **Value**: price/quality ratio, cost-per-use, investment framing
- **Uniqueness**: what makes this different from competitors
- **Social Proof**: customer photos, review highlights, bestseller status
- **Urgency/Scarcity**: limited stock, seasonal availability, flash sales
- **Lifestyle**: how this product fits into the customer's aspirational lifestyle

Objection handlers (minimum 5):
- "I can find it cheaper" → quality difference, warranty, customer service, total value
- "I'm not sure about the quality" → materials detail, manufacturing process, review highlights
- "I need to see it first" → return policy, customer photos, detailed specs, video demos
- "I don't need it right now" → limited availability, price going up, seasonal relevance
- "I've never heard of this brand" → brand story, press mentions, review count, social following

Seasonal hooks (minimum 4): appropriate ecommerce seasons
CTA library (minimum 8): ecommerce-appropriate CTAs
Tone guidelines: per-channel recommendations

### File: `kai/creative/messaging_frameworks/professional_services.py`

**Function: build_professional_services_messaging() -> MessagingFramework**

Core message: "Expert guidance that gets results, from people who understand your challenges"

Message angles (minimum 6):
- **Expertise/Credentials**: years of experience, certifications, specializations
- **Case Studies/Results**: specific outcomes for similar clients
- **Thought Leadership**: original insights, frameworks, published research
- **Process Clarity**: "Here's exactly how we work" — transparency in methodology
- **Empathy/Understanding**: "We've seen this challenge before" — client-centered language
- **Exclusivity/Selectivity**: limited capacity, selective client relationships

Objection handlers (minimum 5):
- "Your fees are too high" → ROI framing, cost of wrong hire/decision, value of expertise
- "We can handle this in-house" → specialized expertise, capacity augmentation, fresh perspective
- "We need to see a proposal first" → discovery process, preliminary assessment offer
- "We're comparing several firms" → differentiation, case study evidence, process advantage
- "The timing isn't right" → cost of delay, market conditions, competitive advantage

Seasonal hooks, CTA library, tone guidelines: professional services-appropriate

### File: `kai/creative/messaging_frameworks/multi_location.py`

**Function: build_multi_location_messaging() -> MessagingFramework**

Core message: "National brand quality with local team care — [Brand] is in your neighborhood"

Message angles (minimum 6):
- **Brand + Local**: national brand trust combined with local service
- **Consistency**: same quality standards at every location
- **Local Team**: meet your local team, local expertise
- **Convenience**: a location near you, wide service coverage
- **Local Reviews**: location-specific social proof
- **Local Promotions**: location-specific offers and community involvement

Per-location personalization rules:
- Replace {location_name} with specific location name
- Use location-specific review counts and ratings
- Reference local team members by name (when available)
- Adapt offers to local market conditions

CTA library: both brand-level and location-level CTAs
Tone guidelines: brand-consistent with local warmth

**Function: get_messaging_framework(archetype: str) -> MessagingFramework**
- Router function: given archetype string, return the right messaging framework
- Supported: "local_service", "ecommerce", "professional_services", "multi_location"
- Raise ValueError for unknown archetype

## Output Files

- `kai/creative/__init__.py`
- `kai/creative/messaging_frameworks/__init__.py`
- `kai/creative/messaging_frameworks/base.py`
- `kai/creative/messaging_frameworks/local_service.py`
- `kai/creative/messaging_frameworks/ecommerce.py`
- `kai/creative/messaging_frameworks/professional_services.py`
- `kai/creative/messaging_frameworks/multi_location.py`

## Acceptance Criteria

- All files parse as valid Python
- Base models (MessageAngle, ObjectionHandler, SeasonalHook, CTATemplate) are complete
- Local service framework has at least 6 message angles, 5 objection handlers, 4 seasonal hooks, 8 CTAs
- Local service framework includes KaiCalls-specific messaging angle
- Ecommerce framework has appropriate e-commerce-specific angles (product quality, scarcity, lifestyle)
- Professional services framework has authority-building and thought leadership angles
- Multi-location framework includes per-location personalization rules
- Headline templates use {placeholder} format for customization
- Objection handlers include specific reframes (not generic "we're better" responses)
- Seasonal hooks include specific months and urgency elements
- CTA library covers all funnel stages (awareness, consideration, decision)
- Tone guidelines cover all major channels
- `get_messaging_framework` correctly routes to each archetype

## Reference Materials

- `knowledge/personas/_persona-index.md` — persona hooks and pain points
- `knowledge/frameworks/content-copywriting/perception-engineering.md` — persuasion framework
- `knowledge/frameworks/content-copywriting/four-us-framework.md` — content quality framework
- `knowledge/channels/` — channel-specific messaging guidelines
- `kai/runtime/models.py` — SerializableModel pattern
