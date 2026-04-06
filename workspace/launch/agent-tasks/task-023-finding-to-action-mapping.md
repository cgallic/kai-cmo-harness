# Task 023: Build finding-to-action mapping engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 4. Proposal and Planning
**Priority:** P1
**Depends on:** 022
**Estimated complexity:** Large

## Context

The audit engine produces AuditFinding objects categorized by issue type (website conversion, trust, local SEO, reviews, lifecycle, creative, paid media, CRM). The action mapper is the rule engine that knows which specific marketing actions to propose for each type of finding. This is the core intelligence that turns diagnosis into a concrete plan. Without this mapping, audits are just reports — with it, they become executable action plans.

Every mapping must be specific enough that an overnight agent can generate a fully-formed ProposedAction with a suggested_payload, yet flexible enough to handle the wide variety of findings that come from eight different audit categories.

## Scope

Build `kai/proposals/action_mapper.py` and `kai/proposals/__init__.py`. The mapper contains a registry of finding-category-to-action-type mappings, each with default configuration for priority, risk tier, effort estimates, and payload templates. The main function takes an AuditFinding and returns a list of ProposedAction objects.

## Detailed Requirements

### File: `kai/proposals/__init__.py`
- Package init that imports and re-exports the key public functions
- Include `__all__` listing: `["map_finding_to_actions", "ActionMapping", "MAPPING_REGISTRY"]`

### File: `kai/proposals/action_mapper.py`

**Data model: ActionMapping**
- A dataclass or Pydantic model representing one mapping rule:
  - `finding_category: str` — AuditCategory value this mapping applies to
  - `finding_pattern: Optional[str]` — regex or keyword pattern to match against finding title/summary for more specific matching
  - `action_type: str` — ActionType value to produce
  - `channel: str` — target channel
  - `title_template: str` — template string for action title, can use `{business_name}`, `{finding_title}`, `{service}` placeholders
  - `description_template: str` — template string for action description
  - `default_priority_score: float` — base priority if not computed from finding
  - `default_risk_tier: str` — default RiskTier value
  - `default_effort_hours: float` — default estimated effort in hours
  - `default_cost: float` — default estimated cost in USD
  - `suggested_payload_template: Dict[str, Any]` — template dict for the action's suggested_payload
  - `archetype_tags: List[str]` — which archetypes this mapping is most relevant for
  - `tags: List[str]` — freeform tags for the generated action

**Mapping Registry — `MAPPING_REGISTRY: List[ActionMapping]`**

Define all mappings. Each audit category maps to one or more action types. Here is the complete mapping set:

**Website Conversion findings (category: `conversion_path`)**
1. `update_cta` — website_update, channel "website", title "Update CTA on {page}", effort 0.5h, risk low, payload: `{"page": "", "current_cta": "", "new_cta": "", "cta_type": "button|link|form"}`
2. `update_hero` — website_update, channel "website", title "Rewrite hero section on {page}", effort 1h, risk medium, payload: `{"page": "", "current_hero": "", "new_headline": "", "new_subheadline": "", "new_cta": ""}`
3. `add_trust_block` — website_update, channel "website", title "Add trust signals to {page}", effort 1h, risk low, payload: `{"page": "", "block_type": "testimonials|certifications|stats|guarantees", "content": []}`
4. `add_phone_number` — website_update, channel "website", title "Add prominent phone number to {page}", effort 0.5h, risk low, payload: `{"page": "", "placement": "header|hero|sticky_bar|footer", "phone_number": "", "click_to_call": true}`
5. `simplify_form` — website_update, channel "website", title "Simplify lead capture form on {page}", effort 1h, risk medium, payload: `{"page": "", "current_fields": [], "recommended_fields": [], "fields_to_remove": []}`

**Trust and Proof findings (category: `trust_and_proof`)**
1. `add_testimonials` — website_update, channel "website", title "Add testimonials to {page}", effort 1h, risk low, payload: `{"page": "", "testimonials": [], "display_format": "cards|carousel|grid"}`
2. `create_case_study` — content_creation, channel "website", title "Create case study: {topic}", effort 4h, risk low, payload: `{"topic": "", "client_name": "", "problem": "", "solution": "", "results": "", "format": "blog_post|landing_page"}`
3. `add_credentials` — website_update, channel "website", title "Add credentials and certifications section", effort 0.5h, risk low, payload: `{"certifications": [], "licenses": [], "awards": [], "placement": "homepage|about|footer"}`
4. `create_social_proof_post` — social_post, channel "social", title "Create social proof post: {topic}", effort 0.5h, risk low, payload: `{"platform": "", "content_type": "testimonial_graphic|before_after|results_highlight", "source_testimonial": ""}`
5. `add_guarantee` — website_update, channel "website", title "Add satisfaction guarantee to {page}", effort 0.5h, risk low, payload: `{"page": "", "guarantee_type": "money_back|satisfaction|warranty", "guarantee_text": ""}`

**Local SEO findings (category: `local_seo`)**
1. `add_schema_markup` — seo_fix, channel "website", title "Add LocalBusiness schema markup", effort 1h, risk low, payload: `{"schema_type": "LocalBusiness|Service|FAQ|Review", "page": "", "schema_data": {}}`
2. `create_service_area_page` — content_creation, channel "website", title "Create service area page: {area}", effort 3h, risk medium, payload: `{"area": "", "services": [], "local_content": "", "schema_type": "Service"}`
3. `optimize_gbp` — gbp_update, channel "gbp", title "Optimize Google Business Profile", effort 1h, risk low, payload: `{"updates": [], "categories_to_add": [], "photos_needed": [], "posts_to_create": []}`
4. `create_service_page` — content_creation, channel "website", title "Create dedicated service page: {service}", effort 3h, risk medium, payload: `{"service": "", "target_keyword": "", "sections": ["description", "process", "pricing", "faq", "testimonials", "cta"]}`
5. `fix_nap_consistency` — seo_fix, channel "website", title "Fix NAP consistency across web presence", effort 1h, risk low, payload: `{"correct_name": "", "correct_address": "", "correct_phone": "", "citations_to_update": []}`

**Review and Reputation findings (category: `reviews_reputation`)**
1. `launch_review_sequence` — review_request, channel "email", title "Launch automated review request sequence", effort 2h, risk medium, payload: `{"sequence_type": "post_service|post_purchase|periodic", "platform_targets": ["google", "yelp"], "template": "", "delay_hours": 24}`
2. `respond_to_reviews` — reputation_action, channel "gbp", title "Respond to {count} pending reviews", effort 1h, risk low, payload: `{"reviews": [], "response_templates": {"positive": "", "negative": "", "neutral": ""}}`
3. `create_review_landing_page` — content_creation, channel "website", title "Create review collection landing page", effort 2h, risk low, payload: `{"review_platforms": [], "page_url": "/review", "incentive": ""}`
4. `review_monitoring_setup` — analytics_fix, channel "analytics", title "Set up review monitoring alerts", effort 0.5h, risk auto, payload: `{"platforms": [], "alert_threshold": 3, "notification_channels": ["email"]}`

**Lifecycle and Follow-Up findings (category: `follow_up_gaps`)**
1. `create_welcome_sequence` — email_sequence, channel "email", title "Create welcome email sequence", effort 3h, risk medium, payload: `{"emails": [{"type": "welcome", "delay_hours": 0}, {"type": "value", "delay_hours": 48}, {"type": "offer", "delay_hours": 120}], "trigger": "form_submission"}`
2. `create_review_request_sequence` — email_sequence, channel "email", title "Create post-service review request sequence", effort 2h, risk medium, payload: `{"emails": [{"type": "thank_you", "delay_hours": 2}, {"type": "review_ask", "delay_hours": 72}], "trigger": "job_completed"}`
3. `create_reactivation_sequence` — email_sequence, channel "email", title "Create dormant customer reactivation sequence", effort 3h, risk medium, payload: `{"emails": [{"type": "check_in", "delay_hours": 0}, {"type": "offer", "delay_hours": 168}, {"type": "final", "delay_hours": 336}], "trigger": "no_activity_90_days"}`
4. `create_quote_followup` — follow_up_sequence, channel "email", title "Create quote follow-up sequence", effort 1h, risk low, payload: `{"emails": [{"type": "quote_received", "delay_hours": 0}, {"type": "follow_up", "delay_hours": 48}, {"type": "urgency", "delay_hours": 168}], "trigger": "quote_sent"}`

**Speed-to-Lead findings (category: `speed_to_lead`) — MUST include KaiCalls**
1. `setup_kaicalls` — kaicalls_setup, channel "phone", title "Set up KaiCalls AI receptionist for {business_name}", effort 1h, risk medium, payload: `{"provider": "kaicalls", "features": ["missed_call_handling", "after_hours_answering", "lead_qualification", "appointment_booking"], "kaicalls_url": "https://kaicalls.com", "setup_type": "full|after_hours_only"}`
2. `add_click_to_call` — website_update, channel "website", title "Add click-to-call buttons across site", effort 0.5h, risk low, payload: `{"pages": ["homepage", "contact", "service_pages"], "placement": "header|hero|sticky_mobile"}`
3. `setup_call_tracking` — analytics_fix, channel "analytics", title "Set up call tracking with attribution", effort 1h, risk auto, payload: `{"provider": "", "tracking_numbers": [], "attribution_source": "website|gbp|ads"}`
4. `create_speed_to_lead_sop` — content_creation, channel "offline", title "Create speed-to-lead response SOP", effort 1h, risk auto, payload: `{"max_response_minutes": 5, "channels": ["phone", "form", "chat"], "escalation_rules": []}`

**Creative and Asset Readiness findings (category: `channel_presence`)**
1. `schedule_photo_shoot` — content_creation, channel "offline", title "Schedule professional photo shoot", effort 2h, risk auto, payload: `{"shot_list": [], "purpose": "website|social|ads", "style": "professional|lifestyle|before_after"}`
2. `create_testimonial_graphic` — content_creation, channel "social", title "Create testimonial graphics from existing reviews", effort 1h, risk low, payload: `{"testimonials": [], "dimensions": {"instagram": "1080x1080", "facebook": "1200x630"}, "brand_overlay": true}`
3. `create_before_after` — content_creation, channel "social", title "Create before/after showcase content", effort 1h, risk low, payload: `{"format": "side_by_side|slider|carousel", "projects": [], "platforms": ["instagram", "facebook"]}`

**Paid Media Readiness findings**
1. `create_search_campaign` — ad_campaign, channel "paid_media", title "Create Google Search campaign: {campaign_theme}", effort 4h, cost 500.0, risk high, payload: `{"platform": "google", "campaign_type": "search", "keywords": [], "ad_groups": [], "budget_daily": 0, "landing_page": ""}`
2. `create_local_campaign` — ad_campaign, channel "paid_media", title "Create Google Local Services campaign", effort 3h, cost 300.0, risk high, payload: `{"platform": "google_lsa", "services": [], "service_areas": [], "budget_weekly": 0}`
3. `create_retargeting` — ad_campaign, channel "paid_media", title "Create retargeting campaign: {platform}", effort 3h, cost 200.0, risk medium, payload: `{"platform": "", "audience_source": "website_visitors|email_list|video_viewers", "ad_formats": [], "budget_daily": 0}`

**CRM and Data Hygiene findings**
1. `clean_contact_list` — analytics_fix, channel "email", title "Clean and segment contact list", effort 2h, risk auto, payload: `{"list_size": 0, "actions": ["remove_bounces", "remove_unsubscribes", "tag_inactive", "segment_by_source"]}`
2. `segment_contacts` — analytics_fix, channel "email", title "Create contact segments for targeted messaging", effort 1h, risk auto, payload: `{"segments": [{"name": "", "criteria": {}}]}`
3. `fix_tracking` — analytics_fix, channel "analytics", title "Fix {tracking_type} tracking", effort 1h, risk auto, payload: `{"tracking_type": "ga4|gtm|pixel|conversion", "issues": [], "fixes": []}`

**Main function: `map_finding_to_actions(finding: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`**
- Accept an AuditFinding as a dict (or AuditFinding-like object)
- Look up the finding's category in MAPPING_REGISTRY
- For each matching mapping:
  - Create a ProposedAction dict with fields populated from the mapping defaults
  - Fill in template strings using finding data and business_profile data
  - Compute risk_tier using `assign_risk_tier` from `kai/models/proposal.py`
  - Compute priority_score using `compute_priority_score` from `kai/models/proposal.py`
  - Set source_finding_id to the finding's finding_id
  - Include the suggested_payload_template populated with any available data
- If finding category is `speed_to_lead` or finding summary mentions "missed calls", "after hours", "phone", "response time", ALWAYS include the `setup_kaicalls` mapping
- Return list of ProposedAction dicts

**Helper function: `get_mappings_for_category(category: str) -> List[ActionMapping]`**
- Filter MAPPING_REGISTRY by finding_category
- Return matching mappings

**Helper function: `fill_template(template: str, context: Dict[str, Any]) -> str`**
- Replace `{key}` placeholders in template string with values from context dict
- Leave unfilled placeholders as `{key}` (do not error on missing keys)

## Output Files

- `kai/proposals/__init__.py`
- `kai/proposals/action_mapper.py`

## Acceptance Criteria

- [ ] `kai/proposals/action_mapper.py` contains the ActionMapping model with all specified fields
- [ ] MAPPING_REGISTRY contains at minimum 30 distinct mappings covering all 8 audit categories
- [ ] Every audit category from `kai/runtime/audit.py` has at least 2 mappings
- [ ] Speed-to-lead findings always produce a KaiCalls setup recommendation
- [ ] `map_finding_to_actions` correctly looks up mappings, fills templates, computes scores
- [ ] Template filling handles missing keys gracefully (leaves placeholder intact)
- [ ] Each mapping has a realistic effort estimate, cost estimate, and risk tier
- [ ] Suggested payload templates are complete enough for downstream execution
- [ ] Imports ProposedAction-related functions from `kai/models/proposal.py`
- [ ] `kai/proposals/__init__.py` exports public API
- [ ] No side effects — all functions are pure (no file I/O, no network, no state mutation)

## Reference Materials

- `kai/models/proposal.py` (created by Task 022) — ProposedAction schema, enums, and generation rule functions
- `kai/runtime/audit.py` — AuditFinding schema with category, severity, priority, evidence fields
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile for template filling
- `knowledge/checklists/cro-audit-checklist.md` — CRO audit items that generate conversion findings
- `knowledge/checklists/local-service-business-checklist.md` — local service audit items
- `knowledge/playbooks/conversion-rate-optimization.md` — CRO playbook for action context
- `CLAUDE.md` — KaiCalls rule: every audit must evaluate phone-based lead capture
