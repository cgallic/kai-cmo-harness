# Task 084: Build ad creative variant logic and cross-channel adaptation

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** Cross-Cutting Creative
**Priority:** P2
**Depends on:** 028, 029
**Estimated complexity:** Large

## Context

Marketing effectiveness requires testing multiple creative variants — different headlines, descriptions, CTAs, and visual concepts — across multiple channels. Creating each variant manually is tedious; automating variant generation from a single base creative is a force multiplier. The variant engine generates structured variations of every creative element, while the cross-channel adapter takes content created for one channel and reformats it for others (blog post to social posts to email to ads). These two capabilities together mean a single creative brief can produce dozens of ready-to-deploy assets across all channels.

## Scope

Create `kai/creative/variant_engine.py` containing the VariantGenerator for creating multiple creative variants from a base, the CrossChannelAdapter for adapting content across channels, and the variant naming/tracking system.

## Detailed Requirements

### File: `kai/creative/variant_engine.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: VariantType**
- `headline_benefit` — headline emphasizing the benefit
- `headline_feature` — headline emphasizing the feature
- `headline_social_proof` — headline using social proof
- `headline_urgency` — headline creating urgency
- `headline_question` — headline as a question
- `headline_statistic` — headline using a specific number/stat
- `description_short` — short description variant
- `description_medium` — medium-length description
- `description_long` — long description variant
- `cta_action` — CTA with action verb ("Get", "Start", "Book")
- `cta_value` — CTA emphasizing value ("See Pricing", "Save Now")
- `cta_urgency` — CTA creating urgency ("Claim Your Spot", "Limited Time")
- `visual_product` — product-focused visual concept
- `visual_lifestyle` — lifestyle-focused visual concept
- `visual_social_proof` — testimonial/review-based visual
- `audience_persona_a` — adapted for persona A
- `audience_persona_b` — adapted for persona B

**Model: BaseCreative**
- `id: str` — format `base_{uuid_hex[:8]}`
- `headline: str`
- `description: str`
- `cta: str`
- `image_concept: Optional[str]` — description of visual concept
- `target_audience: Optional[str]`
- `channel: str` — original channel this was created for
- `offer: Optional[str]` — the offer being promoted
- `proof_point: Optional[str]` — key proof/social proof element
- `metadata: Dict[str, Any]`

**Model: CreativeVariant**
- `id: str` — format using naming convention (see below)
- `base_id: str` — references the BaseCreative
- `variant_type: str` — VariantType enum value
- `variant_number: int` — sequential within type (1, 2, 3...)
- `headline: str`
- `description: str`
- `cta: str`
- `image_concept: Optional[str]`
- `target_audience: Optional[str]`
- `channel: str` — target channel for this variant
- `changes_from_base: List[str]` — what was changed (e.g., ["headline rewritten with urgency angle", "CTA changed to action verb"])
- `rationale: str` — why this variant might perform differently
- `character_counts: Dict[str, int]` — {headline: len, description: len, cta: len}

**Class: VariantGenerator**
- `__init__(self)`
- `generate_variants(self, base: BaseCreative, variant_types: Optional[List[str]] = None, variants_per_type: int = 2) -> List[CreativeVariant]`:
  - Generate variants for each requested type (or all types if None)
  - Return list of CreativeVariant objects
  - Apply the naming convention to each variant
- `generate_headline_variants(self, base: BaseCreative, count: int = 6) -> List[CreativeVariant]`:
  - Generate headline variants across all headline types:
    - Benefit: focus on the customer benefit (e.g., "Save 3 Hours Every Week")
    - Feature: focus on the product feature (e.g., "AI-Powered 24/7 Call Answering")
    - Social proof: use numbers/reviews (e.g., "Join 500+ Businesses Who Never Miss a Call")
    - Urgency: create time pressure (e.g., "Limited Spots Available This Month")
    - Question: engage with a question (e.g., "Still Missing Customer Calls After Hours?")
    - Statistic: lead with a number (e.g., "78% of Callers Won't Leave a Voicemail")
  - Each variant: different headline, same description/CTA from base
- `generate_description_variants(self, base: BaseCreative, count: int = 3) -> List[CreativeVariant]`:
  - Short (under 90 chars): punchy, single benefit
  - Medium (90-150 chars): benefit + proof point
  - Long (150-300 chars): benefit + proof + specific details
  - Each variant: same headline from base, different description
- `generate_cta_variants(self, base: BaseCreative, count: int = 4) -> List[CreativeVariant]`:
  - Action CTAs: "Get Your Free Quote", "Start Now", "Book Today"
  - Value CTAs: "See Pricing", "Compare Plans", "Calculate Your Savings"
  - Urgency CTAs: "Claim Your Spot", "Don't Miss Out", "Limited Time Offer"
  - Soft CTAs: "Learn More", "See How It Works", "Watch Demo"
- `generate_visual_variants(self, base: BaseCreative, count: int = 3) -> List[CreativeVariant]`:
  - Product-focused: the product/service in action
  - Lifestyle: customer using/benefiting from the product
  - Social proof: review quote overlaid, before/after concept, customer photo concept
  - Same copy, different image_concept
- `generate_audience_variants(self, base: BaseCreative, personas: List[str]) -> List[CreativeVariant]`:
  - Adapt the message for each persona
  - Adjust headline angle, description emphasis, CTA language
  - Each variant tagged with target_audience

**Naming convention**:
- Format: `{base_id}_{variant_type}_{variant_number:02d}`
- Example: `base_a1b2c3d4_headline_urgency_01`

**Model: ChannelSpec**
- `channel: str`
- `headline_max_chars: int`
- `description_max_chars: int`
- `cta_max_chars: Optional[int]`
- `hashtags_allowed: bool`
- `hashtag_limit: Optional[int]`
- `mentions_allowed: bool`
- `emoji_allowed: bool`
- `link_allowed: bool`
- `image_required: bool`
- `video_allowed: bool`
- `tone_adjustment: Optional[str]` — how tone should shift for this channel
- `special_format: Optional[str]` — e.g., "carousel", "story", "reel"

**Function: get_channel_specs() -> Dict[str, ChannelSpec]**
Return specs for:
- `google_ads_search`: headline 30 chars, description 90 chars, no hashtags/emoji
- `google_ads_display`: headline 30 chars, description 90 chars
- `meta_ads_feed`: headline 40 chars, description 125 chars (primary text 125 for optimal), hashtags OK
- `meta_ads_stories`: headline 40 chars, description shorter
- `linkedin_ads`: headline 70 chars, description 150 chars, professional tone
- `tiktok_ads`: headline 100 chars, description 100 chars, casual tone, hashtags
- `instagram_organic`: caption 2200 chars max, 30 hashtags max, emoji encouraged
- `facebook_organic`: post 500 chars optimal, hashtags sparingly
- `linkedin_organic`: post 1300 chars, 3-5 hashtags, professional tone
- `twitter_organic`: 280 chars, 2-3 hashtags
- `email_subject`: 50 chars optimal, no hashtags, no emoji (unless tested)
- `email_body`: unlimited, professional tone

**Class: CrossChannelAdapter**
- `__init__(self)`
- `adapt(self, source_content: Dict[str, Any], source_channel: str, target_channel: str) -> Dict[str, Any]`:
  - Adapt content from one channel format to another
  - Apply character limits from channel specs
  - Adjust tone per channel spec
  - Add/remove hashtags as appropriate
  - Return adapted content dict
- `adapt_blog_to_social(self, blog_content: Dict[str, Any]) -> Dict[str, List[Dict]]`:
  - Take a blog post (title, body, key points) and generate:
    - 3 LinkedIn posts (thought leadership angle)
    - 3 Twitter/X posts (punchy takeaways)
    - 3 Instagram captions (visual + caption)
    - 2 Facebook posts (engagement-focused)
    - 2 TikTok script concepts (hook + teach)
  - Return: {platform: [post_dicts]}
- `adapt_landing_page_to_ads(self, landing_page: Dict[str, Any]) -> Dict[str, List[Dict]]`:
  - Take landing page copy (hero, value props, proof) and generate:
    - Google Search ads (3 headline + description sets)
    - Meta feed ads (2 primary_text + headline sets)
    - LinkedIn ads (2 ad copy sets)
  - Return: {platform: [ad_dicts]}
- `adapt_email_to_social(self, email_content: Dict[str, Any]) -> Dict[str, List[Dict]]`:
  - Take email content (subject, body, CTA) and generate social posts
  - Return: {platform: [post_dicts]}
- `adapt_video_to_shorts(self, video_script: Dict[str, Any]) -> List[Dict[str, Any]]`:
  - Take a long-form video script and identify:
    - 3-5 potential short-form clips (15-60 seconds)
    - For each: start_time concept, hook, key message, CTA
  - Return: list of short-form clip specifications
- `_truncate_to_limit(self, text: str, max_chars: int, preserve_words: bool = True) -> str`:
  - Truncate text to character limit
  - If preserve_words: don't cut mid-word, add "..." if truncated
- `_adjust_tone(self, text: str, target_tone: str) -> str`:
  - Stub: describe how tone would be adjusted
  - Return text with tone adjustment notes
- `_add_hashtags(self, text: str, topic: str, platform: str, limit: int) -> str`:
  - Stub: add relevant hashtags for the topic and platform
  - Return text with appended hashtags

## Output Files

- `kai/creative/variant_engine.py`

## Acceptance Criteria

- File parses as valid Python
- VariantGenerator produces all headline variant types (benefit, feature, social_proof, urgency, question, statistic)
- Description variants correctly produce short/medium/long versions
- CTA variants cover action, value, urgency, and soft types
- Naming convention follows the `{base_id}_{variant_type}_{number}` format consistently
- Channel specs are accurate for all major platforms (correct character limits)
- CrossChannelAdapter.adapt_blog_to_social produces platform-appropriate content counts
- Character limit enforcement works correctly (truncates without breaking words)
- Google Ads specs correctly enforce 30-char headline and 90-char description limits
- CreativeVariant includes changes_from_base and rationale (not empty)
- All models use SerializableModel mixin

## Reference Materials

- `kai/creative/messaging_frameworks/` (Task 082) — message angles for variant generation
- `knowledge/channels/` — channel-specific format requirements
- `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` — writing rules
- `knowledge/channels/meta-advertising.md` — Meta ad format specs
- `knowledge/channels/tiktok-algorithm.md` — TikTok format specs
- `harness/references/google-ads-policy-reference.md` — Google Ads character limits
- `kai/runtime/models.py` — SerializableModel pattern
