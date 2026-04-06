# Task 032: Build reusable libraries (CTAs, offers, approved message blocks)

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 5. Creative and Asset Generation
**Priority:** P3
**Depends on:** 001
**Estimated complexity:** Medium

## Context

The creative engine generates content by applying frameworks and rules, but it also needs access to proven, reusable building blocks — CTAs that convert for specific archetypes, offer structures that work for specific business types, and pre-approved copy blocks that have been validated. Rather than generating these from scratch every time, the library system provides curated defaults organized by archetype and channel, plus the ability for each business to add their own custom entries.

This is the "ingredient pantry" of the creative system. When the copy engine needs a CTA for a local plumber's homepage, it can pull from a tested library of service-business CTAs instead of generating one cold every time.

## Scope

Build `kai/creative/libraries.py` containing the CTA, Offer, and MessageBlock library models, default entries organized by archetype, and functions to load, extend, and query the libraries. Also create the YAML data files that hold the default library entries.

## Detailed Requirements

### File: `kai/creative/libraries.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Model: CTAEntry**
- `id: str` — unique identifier
- `text: str` — the CTA text, e.g., "Call Now for a Free Quote"
- `short_text: Optional[str]` — abbreviated version for space-constrained contexts, e.g., "Call Now"
- `archetype_tags: List[str]` — which archetypes this CTA works for: "local-service", "ecommerce", "professional-services", "multi-location", "creator", "saas"
- `channel_tags: List[str]` — which channels this CTA is appropriate for: "website", "email", "ads", "social", "all"
- `intent: str` — what this CTA aims to achieve: "call", "form_submit", "purchase", "schedule", "download", "subscribe", "learn_more"
- `urgency_level: str` — "none", "low", "medium", "high"
- `compliance_notes: Optional[str]` — any compliance considerations
- `quality_score: float` — 0.0 to 1.0 rating of CTA effectiveness, default 0.5
- `source: str` — "default" or "custom"
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: OfferEntry**
- `id: str` — unique identifier
- `name: str` — offer name, e.g., "Free Estimate"
- `description: str` — full offer description
- `offer_type: str` — "free_consultation", "free_estimate", "percentage_off", "dollar_off", "bundle_deal", "free_shipping", "bogo", "trial", "seasonal", "referral", "loyalty"
- `archetype_tags: List[str]` — which archetypes this offer suits
- `channel_tags: List[str]` — where this offer can be promoted
- `typical_value: Optional[str]` — typical value range, e.g., "10-20% off", "$50 value"
- `urgency_type: Optional[str]` — how to create urgency: "time_limited", "quantity_limited", "seasonal", "first_time_only", "none"
- `terms_template: Optional[str]` — template for offer terms/conditions
- `compliance_notes: Optional[str]`
- `quality_score: float` — default 0.5
- `source: str` — "default" or "custom"
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: MessageBlockEntry**
- `id: str` — unique identifier
- `content: str` — the copy block text
- `block_type: str` — "trust_statement", "guarantee", "urgency", "social_proof", "value_prop", "about_boilerplate", "disclaimer", "cta_section", "faq_answer"
- `archetype_tags: List[str]` — which archetypes this block suits
- `channel_tags: List[str]` — where this block can be used
- `compliance_notes: Optional[str]`
- `quality_score: float` — default 0.5
- `variables: List[str]` — placeholders in the content that need filling: ["{business_name}", "{years}", "{review_count}"], default empty list
- `source: str` — "default" or "custom"
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: CreativeLibrary**
- `ctas: List[CTAEntry]` — default empty list
- `offers: List[OfferEntry]` — default empty list
- `message_blocks: List[MessageBlockEntry]` — default empty list
- `business_id: Optional[str]` — if this is a business-specific library
- `last_updated: Optional[str]` — ISO timestamp

**Default CTA library entries (define at least 25 entries):**

Local-service CTAs:
1. "Call Now for a Free Quote" — intent: call, urgency: medium, channels: website/ads
2. "Schedule Your Free Estimate" — intent: schedule, urgency: low, channels: website/email
3. "Get a Free Quote in 60 Seconds" — intent: form_submit, urgency: medium, channels: website
4. "Book Your Appointment" — intent: schedule, urgency: low, channels: website/social
5. "Call {phone} — Available 24/7" — intent: call, urgency: high, channels: website
6. "See Our Work" — intent: learn_more, urgency: none, channels: website/social
7. "Request a Callback" — intent: form_submit, urgency: low, channels: website

Ecommerce CTAs:
8. "Add to Cart" — intent: purchase, urgency: none, channels: website
9. "Shop Now" — intent: purchase, urgency: low, channels: ads/social/email
10. "Claim Your Discount" — intent: purchase, urgency: high, channels: email/ads
11. "Buy Now — Free Shipping Over $50" — intent: purchase, urgency: medium, channels: website
12. "Get 20% Off Your First Order" — intent: purchase, urgency: high, channels: ads/email
13. "Shop the Collection" — intent: learn_more, urgency: none, channels: social
14. "Join the Waitlist" — intent: subscribe, urgency: medium, channels: website/social

Professional-services CTAs:
15. "Schedule a Consultation" — intent: schedule, urgency: low, channels: website
16. "Book Your Free Strategy Session" — intent: schedule, urgency: medium, channels: website/ads
17. "Get Started Today" — intent: form_submit, urgency: medium, channels: website/email
18. "Download the Guide" — intent: download, urgency: low, channels: website/email
19. "Request a Proposal" — intent: form_submit, urgency: low, channels: website

Multi-location CTAs:
20. "Find Your Nearest Location" — intent: learn_more, urgency: low, channels: website
21. "Check Availability in Your Area" — intent: form_submit, urgency: low, channels: website/ads
22. "Visit Us Today" — intent: learn_more, urgency: medium, channels: ads/social

Universal CTAs:
23. "Learn More" — intent: learn_more, urgency: none, channels: all
24. "Subscribe for Updates" — intent: subscribe, urgency: none, channels: website/email
25. "Contact Us" — intent: form_submit, urgency: none, channels: website

**Default Offer library entries (define at least 15 entries):**

Local-service offers:
1. "Free Estimate" — free_consultation, no urgency
2. "10% Off First Service" — percentage_off, first_time_only
3. "$50 Off Any Service Over $300" — dollar_off, none
4. "Free Safety Inspection" — free_consultation, none
5. "Seasonal Tune-Up Special" — seasonal, seasonal urgency

Ecommerce offers:
6. "Free Shipping on Orders Over $50" — free_shipping, none
7. "Buy 2 Get 1 Free" — bogo, time_limited
8. "20% Off First Purchase" — percentage_off, first_time_only
9. "Holiday Sale — Up to 40% Off" — seasonal, seasonal
10. "Free Returns Within 30 Days" — trial, none

Professional-services offers:
11. "Free 30-Minute Consultation" — free_consultation, none
12. "Free Audit Report" — free_consultation, none
13. "10% Off Annual Plans" — percentage_off, none
14. "Refer a Friend, Get $100 Credit" — referral, none

Universal:
15. "Money-Back Guarantee" — trial, none

**Default MessageBlock library entries (define at least 15 entries):**

Trust statements:
1. "Serving {city} for over {years} years with {review_count}+ five-star reviews." — trust_statement, local-service
2. "Trusted by {client_count}+ businesses to deliver measurable results." — trust_statement, professional-services
3. "Licensed, bonded, and insured for your protection." — trust_statement, local-service
4. "{review_count}+ happy customers and counting." — trust_statement, all

Guarantee blocks:
5. "100% Satisfaction Guarantee — If you're not happy, we'll make it right." — guarantee, local-service
6. "30-Day Money-Back Guarantee — No questions asked." — guarantee, ecommerce
7. "Free revisions until you're satisfied." — guarantee, professional-services

Urgency blocks:
8. "Limited availability — book your spot before we're fully scheduled." — urgency, local-service
9. "Offer ends {date}. Don't miss out." — urgency, all
10. "Only {count} spots remaining this month." — urgency, professional-services

Social proof blocks:
11. "Rated {rating}/5 on Google with {review_count} reviews." — social_proof, all
12. "Featured in {publication} as a top {industry} provider." — social_proof, professional-services
13. "Join {subscriber_count}+ professionals who trust our insights." — social_proof, saas

Value prop blocks:
14. "Same-day service available for emergencies." — value_prop, local-service
15. "No hidden fees. The price we quote is the price you pay." — value_prop, local-service

**Function: `load_default_library() -> Dict[str, Any]`**
- Construct a CreativeLibrary dict from the hardcoded default entries above
- Return the library dict

**Function: `load_library_from_yaml(file_path: str) -> Dict[str, Any]`**
- Load a YAML file containing library entries
- Expected YAML structure:
  ```yaml
  ctas:
    - text: "Call Now"
      archetype_tags: ["local-service"]
      channel_tags: ["website", "ads"]
      intent: "call"
      ...
  offers:
    - name: "Free Estimate"
      ...
  message_blocks:
    - content: "Trusted by ..."
      ...
  ```
- Parse into CreativeLibrary dict
- Return the library dict

**Function: `merge_libraries(default_lib: Dict[str, Any], custom_lib: Dict[str, Any]) -> Dict[str, Any]`**
- Merge a custom (business-specific) library with the default library
- Custom entries take precedence when IDs match
- Custom entries extend (do not replace) the default lists
- Return merged library

**Function: `query_ctas(library: Dict[str, Any], archetype: Optional[str] = None, channel: Optional[str] = None, intent: Optional[str] = None, urgency_level: Optional[str] = None) -> List[Dict[str, Any]]`**
- Filter CTAs by any combination of criteria
- If a criterion is None, do not filter on that dimension
- Sort by quality_score descending
- Return matching CTA entries

**Function: `query_offers(library: Dict[str, Any], archetype: Optional[str] = None, channel: Optional[str] = None, offer_type: Optional[str] = None) -> List[Dict[str, Any]]`**
- Filter offers by any combination of criteria
- Sort by quality_score descending
- Return matching offer entries

**Function: `query_message_blocks(library: Dict[str, Any], archetype: Optional[str] = None, channel: Optional[str] = None, block_type: Optional[str] = None) -> List[Dict[str, Any]]`**
- Filter message blocks by any combination of criteria
- Sort by quality_score descending
- Return matching message block entries

**Function: `fill_variables(block: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]`**
- Replace `{variable_name}` placeholders in a message block's content with values from context dict
- If a variable is not in context, leave the placeholder intact
- Return the block with filled content

**Function: `get_library_for_business(business_profile: Dict[str, Any], custom_yaml_path: Optional[str] = None) -> Dict[str, Any]`**
- High-level function:
  1. Load default library
  2. If custom_yaml_path provided, load custom library from YAML and merge
  3. Return the merged library
- Extract archetype from business_profile.classification.archetype to suggest which defaults are most relevant

## Output Files

- `kai/creative/libraries.py`
- `kai/creative/library_data/` directory (create if needed)
- `kai/creative/library_data/default_ctas.yaml` — YAML file with the default CTA entries
- `kai/creative/library_data/default_offers.yaml` — YAML file with the default offer entries
- `kai/creative/library_data/default_message_blocks.yaml` — YAML file with the default message block entries

## Acceptance Criteria

- [ ] `libraries.py` contains CTAEntry, OfferEntry, MessageBlockEntry, and CreativeLibrary models
- [ ] Default CTA library has at least 25 entries covering 4+ archetypes
- [ ] Default Offer library has at least 15 entries covering 4+ archetypes
- [ ] Default MessageBlock library has at least 15 entries covering trust, guarantee, urgency, social proof, and value prop types
- [ ] load_default_library returns a populated library
- [ ] load_library_from_yaml parses YAML into library format
- [ ] merge_libraries correctly extends defaults with custom entries
- [ ] query_ctas, query_offers, query_message_blocks filter by archetype, channel, type
- [ ] fill_variables replaces placeholders and handles missing variables gracefully
- [ ] get_library_for_business orchestrates loading and merging
- [ ] YAML data files are created in `kai/creative/library_data/` with all default entries
- [ ] Every entry has archetype_tags and channel_tags for queryability
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/models/business_profile.py` (created by Task 001) — BusinessClassification.archetype, BrandVoice
- `kai/creative/brief.py` (created by Task 027) — CreativeBrief.cta, .offer fields that consume library entries
- `gateway/models.py` — Pydantic import fallback pattern
- `harness/skill-contracts/` — skill contracts with CTA and format requirements
- `CLAUDE.md` — quality gate rules, persona hooks
