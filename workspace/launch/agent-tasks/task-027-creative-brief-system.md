# Task 027: Build creative brief system from proposals

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 5. Creative and Asset Generation
**Priority:** P1
**Depends on:** 022
**Estimated complexity:** Medium

## Context

ProposedActions describe what needs to happen ("create a case study", "write ad copy for Google Search", "build a welcome email sequence"). But before any creative work begins, there must be a structured brief that specifies the persona, tone, format constraints, quality thresholds, and platform requirements. The CreativeBrief is the contract between the proposal layer and the creative execution layer. It ensures every piece of content is intentional, on-brand, and measurable. The brief system also serves as the integration point with the existing harness brief schema (`harness/brief-schema.md`) and skill contracts (`harness/skill-contracts/`).

## Scope

Build `kai/creative/brief.py` and `kai/creative/__init__.py` containing the CreativeBrief model and functions to generate briefs from ProposedActions using business profile context.

## Detailed Requirements

### File: `kai/creative/__init__.py`
- Package init that imports and re-exports key classes and functions
- Include `__all__` listing

### File: `kai/creative/brief.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: BriefType**
- `copy` — text-based content (articles, emails, ad copy, scripts)
- `visual` — image or graphic design assets
- `video` — video content (scripts, reels, ads)
- `audio` — podcast scripts, voicemail scripts, hold music scripts

**Enum: ContentFormat**
- `blog_post`
- `linkedin_article`
- `social_post`
- `ad_copy`
- `email_welcome`
- `email_nurture`
- `email_cold_outreach`
- `email_review_request`
- `email_reactivation`
- `landing_page`
- `service_page`
- `service_area_page`
- `case_study`
- `press_release`
- `video_script`
- `call_script`
- `voicemail_script`
- `testimonial_graphic`
- `offer_graphic`
- `before_after_graphic`
- `social_reel`
- `faq_section`
- `homepage_section`
- `web_section`

**Model: CreativeBrief**
- `id: str` — unique identifier, format `brf_{uuid_hex[:12]}`
- `source_action_id: str` — links back to the ProposedAction that generated this brief
- `brief_type: str` — BriefType enum value
- `channel: str` — target channel (matches ProposedAction channel)
- `format: str` — ContentFormat enum value
- `persona_target: Optional[str]` — name of the target persona from BusinessProfile.personas
- `persona_pain_point: Optional[str]` — specific pain point being addressed
- `key_message: str` — the single most important message this content must convey
- `supporting_messages: List[str]` — secondary messages, default empty list
- `tone_notes: str` — tone guidance, e.g., "professional but approachable, avoid corporate jargon"
- `brand_voice_reference: Optional[str]` — reference to BrandVoice from BusinessProfile
- `offer: Optional[str]` — if this content promotes a specific offer, name it here
- `offer_details: Optional[str]` — offer specifics (price, discount, terms)
- `cta: str` — primary call to action, e.g., "Call Now for a Free Quote"
- `cta_url: Optional[str]` — URL for the CTA if applicable
- `word_count_target: Optional[int]` — target word count for copy-based briefs
- `word_count_range: Optional[str]` — acceptable range, e.g., "1200-1800"
- `dimensions: Optional[str]` — for visual briefs, e.g., "1080x1080", "1200x630"
- `duration_target: Optional[str]` — for video/audio, e.g., "30 seconds", "2 minutes"
- `platform_constraints: Dict[str, Any]` — platform-specific rules (character limits, policy restrictions), default empty dict
- `compliance_notes: List[str]` — regulatory or policy notes for this content, default empty list
- `reference_assets: List[str]` — URLs or paths to reference materials, default empty list
- `target_keyword: Optional[str]` — primary SEO keyword (for search content)
- `secondary_keywords: List[str]` — supporting keywords, default empty list
- `internal_links: List[str]` — URLs to link to in this content, default empty list
- `quality_gate_thresholds: Dict[str, Any]` — specific quality gate targets, default:
  ```python
  {
      "four_us_min": 12,
      "banned_words_check": True,
      "seo_lint": False,  # only True for SEO content
  }
  ```
- `competitor_url: Optional[str]` — URL of competitor content being outperformed
- `competitor_weakness: Optional[str]` — specific gap in competitor content
- `angle: Optional[str]` — the specific frame/angle for this content
- `hook_options: List[str]` — potential hooks for the content opener, default empty list
- `proof_available: Optional[str]` — data, stories, or examples available for this content
- `created_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Function: `generate_brief(action: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`**
- Takes a ProposedAction dict and optional BusinessProfile dict
- Determines brief_type from action_type:
  - website_update, seo_fix → "copy" (brief_type), format determined by payload
  - social_post → "copy", format "social_post"
  - ad_campaign → "copy", format "ad_copy"
  - email_sequence → "copy", format determined by email type in payload
  - content_creation → "copy" or "visual" depending on payload content_type
  - review_request → "copy", format "email_review_request"
  - follow_up_sequence → "copy", format varies
  - reputation_action → "copy" (review responses)
- Extracts persona from business_profile.personas (pick primary, or first available)
- Extracts tone from business_profile.brand_voice.tone_descriptors
- Extracts CTA from action.suggested_payload or business_profile.offers (primary offer's primary_cta)
- Sets quality gate thresholds based on format:
  - Blog/article/landing page → four_us_min: 12, seo_lint: True
  - Email/ad/social → four_us_min: 10, seo_lint: False
  - Internal/analytics → no quality gate
- Sets word_count_target based on format (reference WORD_COUNT_TARGETS constant)
- Returns a CreativeBrief dict

**Constant: WORD_COUNT_TARGETS**
```python
WORD_COUNT_TARGETS = {
    "blog_post": {"target": 1400, "range": "1200-1800"},
    "linkedin_article": {"target": 800, "range": "700-1000"},
    "social_post": {"target": 150, "range": "50-280"},
    "ad_copy": {"target": 50, "range": "25-90"},
    "email_welcome": {"target": 200, "range": "150-300"},
    "email_nurture": {"target": 300, "range": "200-500"},
    "email_cold_outreach": {"target": 100, "range": "75-150"},
    "email_review_request": {"target": 100, "range": "75-150"},
    "email_reactivation": {"target": 150, "range": "100-250"},
    "landing_page": {"target": 1500, "range": "800-2500"},
    "service_page": {"target": 1200, "range": "800-1500"},
    "service_area_page": {"target": 800, "range": "600-1000"},
    "case_study": {"target": 1000, "range": "800-1500"},
    "press_release": {"target": 500, "range": "400-700"},
    "video_script": {"target": 200, "range": "100-500"},
    "call_script": {"target": 300, "range": "200-500"},
    "voicemail_script": {"target": 50, "range": "30-60"},
    "faq_section": {"target": 500, "range": "300-800"},
    "homepage_section": {"target": 200, "range": "100-400"},
    "web_section": {"target": 200, "range": "100-400"},
}
```

**Constant: PLATFORM_CONSTRAINTS**
```python
PLATFORM_CONSTRAINTS = {
    "google_ads": {"headline_max_chars": 30, "description_max_chars": 90, "headlines_needed": 15, "descriptions_needed": 4},
    "meta_ads": {"primary_text_max_chars": 125, "headline_max_chars": 40, "description_max_chars": 30},
    "linkedin_ads": {"intro_text_max_chars": 600, "headline_max_chars": 200},
    "tiktok_ads": {"caption_max_chars": 100, "video_max_seconds": 60},
    "instagram_post": {"caption_max_chars": 2200, "hashtag_max": 30},
    "linkedin_post": {"post_max_chars": 3000, "hashtag_max": 5},
    "facebook_post": {"post_max_chars": 63206},
    "twitter_post": {"post_max_chars": 280},
    "tiktok_post": {"caption_max_chars": 2200},
    "email": {"subject_max_chars": 60, "preview_max_chars": 90},
}
```

**Function: `generate_briefs_for_bundle(bundle: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`**
- Takes a ProposalBundle dict and generates briefs for each action that requires creative work
- Not all actions need briefs (analytics_fix, tracking setup do not)
- Actions that need briefs: content_creation, social_post, ad_campaign, email_sequence, website_update (if copy change), review_request (if template needed), follow_up_sequence
- Returns list of CreativeBrief dicts

**Function: `brief_to_harness_format(brief: Dict[str, Any]) -> Dict[str, Any]`**
- Convert a CreativeBrief to the format expected by `harness/brief-schema.md`
- Maps fields: format, persona → persona, target_keyword, secondary_keywords, angle, hook_options, cta, word_count_target, internal_links
- Returns a dict matching the harness brief JSON schema

**Helper: `generate_brief_id() -> str`**
- Return `brf_{uuid.uuid4().hex[:12]}`

## Output Files

- `kai/creative/__init__.py`
- `kai/creative/brief.py`

## Acceptance Criteria

- [ ] `kai/creative/brief.py` contains BriefType and ContentFormat enums with all listed values
- [ ] CreativeBrief model has all 30+ fields with correct types and defaults
- [ ] generate_brief correctly maps action_type to brief_type and format
- [ ] Persona, tone, and CTA extraction from BusinessProfile works for partial profiles
- [ ] Quality gate thresholds vary by content format (12 for SEO, 10 for ads/email)
- [ ] Word count targets are defined for all formats
- [ ] Platform constraints cover all major ad and social platforms
- [ ] generate_briefs_for_bundle correctly filters actions that need creative work
- [ ] brief_to_harness_format produces output compatible with `harness/brief-schema.md`
- [ ] PLATFORM_CONSTRAINTS includes character limits for all major platforms
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] `kai/creative/__init__.py` exports all public classes and functions

## Reference Materials

- `harness/brief-schema.md` — existing brief schema that brief_to_harness_format must match
- `harness/skill-contracts/blog-post.yaml` — example skill contract with word count, required sections
- `harness/skill-contracts/` — all 7 skill contract files for format requirements
- `kai/models/proposal.py` (created by Task 022) — ProposedAction schema
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile with personas, brand_voice, offers
- `gateway/models.py` — Pydantic import fallback pattern
- `CLAUDE.md` — quality gate thresholds (12/16 for publishing, 10/16 for ads/email)
