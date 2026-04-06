# Task 040: Build social content type system and format rules

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 7. Social Operations
**Priority:** P1
**Depends on:** 039
**Estimated complexity:** Medium

## Context

Once the social connector layer (Task 039) provides a uniform interface to each platform, the system needs a structured taxonomy of social content types and per-platform format rules. This is the "what can we post and how must it look on each platform" layer. Every social feature downstream — caption generation (042), scheduling (041), proof-of-life (043) — uses these content types and format rules to produce platform-compliant posts. Without this, the system would generate content that violates character limits, uses wrong aspect ratios, or ignores platform best practices.

## Scope

Create `kai/social/content_types.py` containing all social content type definitions, per-platform format rules, and cross-product templates that map each content type to each platform's specific constraints. Also create the package init.

## Detailed Requirements

### File: `kai/social/__init__.py`

- Module docstring: "Social content management — content types, format rules, scheduling, and platform optimization."
- Import and re-export key classes from content_types.py
- `__all__` listing

### File: `kai/social/content_types.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: SocialContentType (str, Enum)**
- `proof_post` — before/after, project completion, results showcase. Best for showing work quality and building trust.
- `testimonial_post` — customer quote with photo/graphic. Social proof that converts.
- `local_tip_post` — helpful advice related to service area (e.g., "3 signs your AC needs service"). Positions business as expert.
- `offer_post` — promotional with urgency, clear CTA. Direct response.
- `behind_the_scenes_post` — team, process, workspace authenticity. Humanizes the brand.
- `educational_post` — how-to, myth-busting, FAQ answer. Value-first content.
- `community_post` — local events, partnerships, sponsorships. Community connection.
- `seasonal_post` — holiday, weather, seasonal service reminders. Timely relevance.

Each enum member should have a `description` attribute or use a docstring comment. Add a class method `get_description(cls, content_type: str) -> str` that returns a one-sentence description.

**Enum: SocialPlatform (str, Enum)**
- `instagram`
- `facebook`
- `linkedin`
- `tiktok`
- `x_twitter`
- `youtube`

**Model: PlatformFormatRules**
- `platform: str` — SocialPlatform value
- `max_caption_length: int`
- `recommended_caption_length: int` — sweet spot for engagement
- `max_hashtags: int`
- `recommended_hashtags: int` — optimal for reach
- `max_media_items: int` — max images/videos per post (carousel limit)
- `preferred_aspect_ratios: List[str]` — e.g., ["1:1", "4:5"] for Instagram feed
- `supports_scheduling: bool`
- `supports_link_in_post: bool` — whether the platform allows clickable links in post body
- `supports_carousel: bool`
- `supports_video: bool`
- `supports_stories: bool`
- `supports_reels_shorts: bool`
- `tone_guidance: str` — brief tone direction, e.g., "Professional but personable. No hard sells."
- `best_practices: List[str]` — 3-5 key best practices as strings
- `posting_frequency_max_per_day: int`
- `posting_frequency_recommended_per_day: float` — e.g., 0.5 means every other day

**Pre-built PLATFORM_RULES dict: `PLATFORM_RULES: Dict[str, PlatformFormatRules]`**

Define one PlatformFormatRules instance per platform with these values:

1. **Instagram**:
   - max_caption_length: 2200, recommended: 150 (for feed) to 2200 (for carousel education)
   - max_hashtags: 30, recommended: 5-10
   - max_media_items: 10 (carousel)
   - preferred_aspect_ratios: ["1:1", "4:5", "9:16"]
   - supports_scheduling: True, link_in_post: False, carousel: True, video: True, stories: True, reels_shorts: True
   - tone: "Visual-first, authentic, slightly casual. Lead with the image, support with caption."
   - best_practices: ["First line is the hook — must stop the scroll", "Use line breaks for readability", "Put hashtags in first comment or at end", "Carousel posts get 3x engagement vs single image", "Reels reach 2x more non-followers than feed posts"]
   - max_per_day: 3, recommended: 1.0

2. **Facebook**:
   - max_caption_length: 63206, recommended: 80 (for link posts) to 250 (for engagement posts)
   - max_hashtags: 30, recommended: 2-3
   - max_media_items: 10 (carousel)
   - preferred_aspect_ratios: ["1:1", "4:5", "16:9"]
   - supports_scheduling: True, link_in_post: True, carousel: True, video: True, stories: True, reels_shorts: True
   - tone: "Conversational, community-oriented. Questions and stories perform best."
   - best_practices: ["Native video outperforms YouTube links by 10x", "Posts with questions get 2x comments", "Share to relevant local groups for organic reach", "Link posts get less reach than photo/video posts", "Facebook prioritizes content that sparks conversation"]
   - max_per_day: 2, recommended: 1.0

3. **LinkedIn**:
   - max_caption_length: 3000, recommended: 1300
   - max_hashtags: 30 (technically), recommended: 3-5
   - max_media_items: 9 (document carousel)
   - preferred_aspect_ratios: ["1:1", "1.91:1", "4:5"]
   - supports_scheduling: True, link_in_post: True, carousel: True (document format), video: True, stories: False, reels_shorts: False
   - tone: "Professional, thought-leadership oriented. Share expertise and industry insights."
   - best_practices: ["Open with a hook line, then line break for 'see more' click", "Document carousels get 3x engagement", "Comment on your own post to boost reach", "Tag relevant people and companies", "Post between 7-9 AM or 12-1 PM local time"]
   - max_per_day: 2, recommended: 1.0

4. **TikTok**:
   - max_caption_length: 2200, recommended: 150
   - max_hashtags: 100 (technically), recommended: 3-5
   - max_media_items: 1 (single video or photo carousel up to 35)
   - preferred_aspect_ratios: ["9:16"]
   - supports_scheduling: True, link_in_post: False (bio link only unless business account), carousel: True (photo mode), video: True, stories: False (removed), reels_shorts: True (it IS short form)
   - tone: "Authentic, unpolished, trend-aware. Educational content in entertainment wrapper."
   - best_practices: ["Hook in first 1-3 seconds or lose them", "Trending sounds boost discovery 2-3x", "Show don't tell — demonstrate expertise visually", "Reply to comments with video for engagement loop", "Post 1-3x daily for growth phase, 3-5x/week for maintenance"]
   - max_per_day: 3, recommended: 1.0

5. **X/Twitter**:
   - max_caption_length: 280 (free), recommended: 240-280
   - max_hashtags: 10, recommended: 2-3
   - max_media_items: 4 (images)
   - preferred_aspect_ratios: ["16:9", "1:1"]
   - supports_scheduling: True, link_in_post: True, carousel: False, video: True, stories: False, reels_shorts: False
   - tone: "Punchy, opinionated, concise. Hot takes and thread format for depth."
   - best_practices: ["Threads get 5x engagement of single tweets", "Tweet without links gets more reach than with links", "Reply to your own tweet to add links below", "Post contrarian or spicy takes for engagement", "Quote tweets > retweets for reach"]
   - max_per_day: 5, recommended: 2.0

6. **YouTube**:
   - max_caption_length: 5000, recommended: 200 (for Shorts description)
   - max_hashtags: 15, recommended: 3-5
   - max_media_items: 1
   - preferred_aspect_ratios: ["16:9", "9:16"]
   - supports_scheduling: True, link_in_post: True (description), carousel: False, video: True, stories: False (community posts instead), reels_shorts: True
   - tone: "Educational, helpful, personality-driven. First 30 seconds determine retention."
   - best_practices: ["Title and thumbnail are 80% of success", "First 30 seconds must hook — ask a question or show the payoff", "Include Shorts in every long-form video with #Shorts tag", "Chapters improve watch time and SEO", "End screen and cards drive subscriber growth"]
   - max_per_day: 2, recommended: 0.3 (long-form) or 1.0 (Shorts)

**Model: ContentTypeTemplate**
- `content_type: str` — SocialContentType value
- `platform: str` — SocialPlatform value
- `structure: List[str]` — ordered list of structural elements (e.g., ["hook", "before_photo", "after_photo", "result_description", "cta"])
- `required_elements: List[str]` — elements that MUST be present
- `optional_elements: List[str]` — elements that can be included
- `suggested_hooks: List[str]` — 3-5 example opening lines/hooks for this content type on this platform
- `cta_options: List[str]` — 3-5 appropriate CTA options
- `caption_template: str` — a fill-in-the-blank caption template string with `{placeholders}`
- `media_guidance: str` — what kind of media to use (e.g., "Before/after side-by-side image, or carousel with before + after + detail shots")
- `notes: str` — any special notes for this combination

**Function: `get_content_type_template(content_type: str, platform: str) -> Optional[ContentTypeTemplate]`**
- Look up the cross-product (content_type, platform) in a `CONTENT_TYPE_TEMPLATES` dict
- Return the template or None if the combination is not supported

**CONTENT_TYPE_TEMPLATES dict — define at minimum these cross-products (8 types x 6 platforms = 48, but not all combinations are valid):**

Define templates for each content type across the primary platforms. At minimum, define complete templates for:

1. **ProofPost** on Instagram, Facebook, LinkedIn, TikTok (4 templates)
   - Instagram: carousel with before/after, result stats in caption, strong hook first line
   - Facebook: single image or short video, detailed story in caption, community engagement question at end
   - LinkedIn: professional framing, business outcome focus, industry relevance
   - TikTok: timelapse or transformation video, trending sound, text overlay with results

2. **TestimonialPost** on Instagram, Facebook, LinkedIn (3 templates)
   - Instagram: quote graphic or short video clip, customer tag, story version
   - Facebook: customer photo with quote text, link to full review
   - LinkedIn: professional endorsement framing, case study teaser

3. **LocalTipPost** on Instagram, Facebook, TikTok, YouTube (4 templates)
   - Instagram: carousel with numbered tips, save-worthy formatting
   - Facebook: question-based hook, detailed tip, conversation starter
   - TikTok: quick tip video 15-30 seconds, text overlay, practical demo
   - YouTube: Short with tip demonstration

4. **OfferPost** on Instagram, Facebook, X (3 templates)
   - Instagram: eye-catching graphic, urgency in caption, story with link sticker
   - Facebook: offer details, link to landing page, urgency
   - X: punchy offer text, link, deadline

5. **BehindTheScenesPost** on Instagram, TikTok, YouTube (3 templates)
   - Instagram: casual photo/video, authentic caption, team tags
   - TikTok: day-in-the-life style, trending format
   - YouTube: Short showing process or workspace

6. **EducationalPost** on all 6 platforms (6 templates)
   - Each platform-appropriate format for how-to/educational content

7. **CommunityPost** on Facebook, Instagram, LinkedIn (3 templates)
   - Local event support, partnership announcements, community involvement

8. **SeasonalPost** on Instagram, Facebook, TikTok (3 templates)
   - Seasonal service reminders with offer tie-in

For each template, provide:
- 3-5 `suggested_hooks` that are specific and usable (not generic)
- 3-5 `cta_options` appropriate to the content type and platform
- A `caption_template` with `{business_name}`, `{service}`, `{result}`, `{location}`, `{offer}`, `{cta}` placeholders as appropriate
- Specific `media_guidance`

**Function: `get_platform_rules(platform: str) -> Optional[PlatformFormatRules]`**
- Look up and return rules from PLATFORM_RULES

**Function: `get_supported_content_types(platform: str) -> List[str]`**
- Return which content types are supported/recommended for a given platform

**Function: `validate_post_for_platform(content_text: str, platform: str, media_count: int = 0, hashtag_count: int = 0) -> List[str]`**
- Check content against platform rules
- Return list of validation warnings/errors:
  - "Caption exceeds {platform} limit of {max} characters (currently {actual})"
  - "Too many hashtags for {platform}: {count} used, {max} allowed"
  - "Hashtag count ({count}) exceeds recommended ({recommended}) for {platform}"
  - "Caption length ({length}) exceeds recommended ({recommended}) for {platform} — consider shortening for engagement"
  - "Media count ({count}) exceeds {platform} maximum of {max}"

## Output Files

- `kai/social/__init__.py`
- `kai/social/content_types.py`

## Acceptance Criteria

- [ ] `SocialContentType` enum has all 8 content types with descriptive values
- [ ] `SocialPlatform` enum has all 6 platforms
- [ ] `PlatformFormatRules` model has all 16 fields listed above
- [ ] `PLATFORM_RULES` dict contains fully populated rules for all 6 platforms with accurate, real-world values
- [ ] `ContentTypeTemplate` model has all 9 fields
- [ ] `CONTENT_TYPE_TEMPLATES` dict contains at least 29 cross-product templates (the specified combinations above)
- [ ] Each template has at least 3 `suggested_hooks`, 3 `cta_options`, and a usable `caption_template` with placeholders
- [ ] `get_content_type_template()`, `get_platform_rules()`, `get_supported_content_types()`, `validate_post_for_platform()` functions all exist with correct logic
- [ ] `validate_post_for_platform()` catches caption length, hashtag count, and media count violations
- [ ] All templates have specific, actionable hooks (not generic "Check this out!" filler)
- [ ] Platform rules match real 2025-2026 platform limits (e.g., Instagram 2200 chars, X 280 chars)
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] `kai/social/__init__.py` exports key classes

## Reference Materials

- `kai/connectors/social/base.py` (created by Task 039) — SocialPost, MediaRequirements models
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `knowledge/channels/instagram.md` — Instagram content guidance
- `knowledge/channels/tiktok-algorithm.md` — TikTok algorithm and content strategy
- `knowledge/channels/linkedin-articles.md` — LinkedIn content guidance
- `knowledge/channels/x-twitter.md` — X/Twitter content guidance
- `knowledge/channels/youtube.md` — YouTube content guidance
- `knowledge/playbooks/social-media-strategy.md` — overall social strategy
- `CLAUDE.md` — full project context, Four U's quality gate rules
