# Task 029: Build creative asset support

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 5. Creative and Asset Generation
**Priority:** P2
**Depends on:** 027
**Estimated complexity:** Large

## Context

Not all marketing actions produce text copy. Many require visual assets — testimonial graphics, before/after layouts, offer graphics, video reels with branded overlays. Kai cannot directly produce images or video, but it can produce precise specifications that a designer, Canva user, or automated design tool can execute. The creative asset support module defines structured models for non-copy assets, a workflow for requesting and tracking asset production, and enough detail in each specification that the output is unambiguous.

This module bridges the gap between "we need a testimonial graphic" and a designer having everything they need to produce one without asking follow-up questions.

## Scope

Build `kai/creative/asset_support.py` containing models for visual and video asset specifications, an asset request workflow, and status tracking. These models describe what to produce — they do not produce the assets themselves.

## Detailed Requirements

### File: `kai/creative/asset_support.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: AssetType**
- `image` — static image (graphic, photo edit, infographic)
- `before_after` — before/after comparison layout
- `testimonial_graphic` — branded testimonial card
- `offer_graphic` — promotional offer graphic
- `video_reel` — short-form video (TikTok, Reels, Shorts)
- `video_long` — long-form video (YouTube, webinar)
- `carousel` — multi-slide carousel (Instagram, LinkedIn)
- `infographic` — data visualization or process infographic
- `logo_variant` — logo adaptation for specific use
- `social_cover` — social media cover/banner image

**Enum: AssetStatus**
- `requested` — asset has been specified but not started
- `in_progress` — designer/tool is working on it
- `delivered` — asset has been produced and is available
- `approved` — operator has approved the asset for use
- `rejected` — operator rejected, needs revision
- `revision_requested` — revision notes provided, awaiting update

**Model: ImageConcept**
- `id: str` — unique identifier, format `img_{uuid_hex[:12]}`
- `description: str` — detailed description of what the image should show
- `dimensions: str` — pixel dimensions, e.g., "1080x1080"
- `aspect_ratio: str` — e.g., "1:1", "16:9", "4:5", "9:16"
- `style_notes: str` — visual style guidance: "clean and modern", "warm and inviting", "bold and energetic"
- `color_palette: List[str]` — hex color codes to use, default empty list (use brand colors)
- `text_overlay: Optional[str]` — text to overlay on the image
- `text_overlay_position: Optional[str]` — where to place text: "top", "center", "bottom", "top-left", etc.
- `font_guidance: Optional[str]` — font style guidance: "sans-serif, bold", "serif, elegant"
- `brand_elements: List[str]` — brand elements to include: "logo", "tagline", "brand_colors", "watermark"
- `reference_images: List[str]` — URLs or paths to reference/inspiration images, default empty list
- `platform: str` — target platform for dimensions/format optimization
- `file_format: str` — "png", "jpg", "webp", "svg", default "png"
- `background: Optional[str]` — "white", "transparent", "brand_primary", "photo", "gradient"
- `mood: Optional[str]` — emotional mood: "professional", "friendly", "urgent", "luxurious", "casual"
- `subjects: List[str]` — what/who should be depicted, default empty list
- `avoid: List[str]` — elements to avoid: "stock photo look", "clip art", "text-heavy", default empty list
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: BeforeAfterLayout**
- `id: str` — unique identifier, format `ba_{uuid_hex[:12]}`
- `before_description: str` — description of the "before" state
- `before_image_source: Optional[str]` — path/URL to before image if available
- `after_description: str` — description of the "after" state
- `after_image_source: Optional[str]` — path/URL to after image if available
- `caption: str` — caption text for the comparison
- `format: str` — one of: "side_by_side", "slider", "carousel", "stacked"
- `dimensions: str` — overall dimensions
- `platform: str` — target platform
- `brand_overlay: bool` — whether to include brand elements, default True
- `logo_position: Optional[str]` — where to place logo: "bottom-right", "top-left", etc.
- `call_to_action: Optional[str]` — CTA text to include on the graphic
- `project_details: Optional[str]` — description of the project (location, service type, etc.)
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: TestimonialGraphic**
- `id: str` — unique identifier, format `tst_{uuid_hex[:12]}`
- `quote: str` — the testimonial text
- `quote_max_words: int` — max words to display (truncate if needed), default 40
- `attribution: str` — customer name or "Customer Name, City"
- `star_rating: Optional[int]` — 1-5 stars, None if not applicable
- `review_platform: Optional[str]` — "google", "yelp", "facebook" — include platform icon
- `customer_photo: Optional[str]` — path/URL to customer photo
- `brand_overlay: bool` — include brand logo/colors, default True
- `dimensions: str` — default "1080x1080"
- `platform: str` — target platform
- `background_style: str` — "solid_brand", "gradient", "photo_blur", "clean_white", default "solid_brand"
- `accent_color: Optional[str]` — hex color for accent elements (quote marks, stars)
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: OfferGraphic**
- `id: str` — unique identifier, format `ofr_{uuid_hex[:12]}`
- `headline: str` — main offer headline, e.g., "20% Off First Service"
- `offer_details: str` — details of the offer, terms, expiration
- `cta: str` — call to action text
- `urgency_element: Optional[str]` — urgency text: "Ends Sunday", "First 10 Customers Only"
- `brand_elements: List[str]` — brand elements to include, default ["logo", "brand_colors"]
- `dimensions: str` — default "1080x1080"
- `platform: str` — target platform
- `background_style: str` — "bold_color", "photo_overlay", "gradient", "pattern", default "bold_color"
- `disclaimer: Optional[str]` — legal disclaimer or terms text (small print)
- `promo_code: Optional[str]` — promo code to display if applicable
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: VideoReelBrief**
- `id: str` — unique identifier, format `vid_{uuid_hex[:12]}`
- `hook: str` — first 3 seconds hook description (what happens visually + audio)
- `hook_text_overlay: str` — text shown in first 3 seconds
- `main_content: List[Dict[str, Any]]` — ordered list of content segments, each with:
  - `timestamp_start: str` — e.g., "0:03"
  - `timestamp_end: str` — e.g., "0:08"
  - `visual_description: str` — what is shown
  - `narration: Optional[str]` — voiceover text
  - `text_overlay: Optional[str]` — text shown on screen
  - `transition: Optional[str]` — transition to next segment: "cut", "swipe", "zoom", "fade"
- `cta: str` — final call to action
- `cta_visual: str` — what the CTA looks like (button graphic, text overlay, etc.)
- `duration_target: int` — target duration in seconds
- `platform: str` — target platform (affects aspect ratio and style)
- `aspect_ratio: str` — "9:16" for vertical (TikTok, Reels), "16:9" for horizontal (YouTube), "1:1" for square
- `music_notes: Optional[str]` — music style/mood guidance
- `text_overlays: List[Dict[str, str]]` — list of {"text": "", "timestamp": "", "style": ""}, default empty list
- `b_roll_suggestions: List[str]` — suggested B-roll footage descriptions, default empty list
- `filming_notes: Optional[str]` — notes for the person filming (lighting, angle, etc.)
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: CarouselBrief**
- `id: str` — unique identifier, format `car_{uuid_hex[:12]}`
- `title: str` — carousel title/theme
- `slides: List[Dict[str, Any]]` — ordered list of slides, each with:
  - `slide_number: int`
  - `headline: str`
  - `body_text: Optional[str]`
  - `visual_description: str`
  - `cta: Optional[str]` — CTA for this slide (typically last slide only)
- `total_slides: int` — 3-10 slides
- `dimensions: str` — default "1080x1350" for Instagram
- `platform: str` — target platform
- `brand_consistent: bool` — whether all slides use consistent brand styling, default True
- `swipe_cta: str` — text encouraging swipe: "Swipe for more", "Keep reading"
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: AssetRequest**
- `id: str` — unique identifier, format `asr_{uuid_hex[:12]}`
- `source_action_id: str` — links back to ProposedAction
- `source_brief_id: str` — links back to CreativeBrief
- `asset_type: str` — AssetType enum value
- `asset_spec: Dict[str, Any]` — the full asset specification (one of the models above, serialized)
- `status: str` — AssetStatus enum value, default "requested"
- `assigned_to: Optional[str]` — who is responsible for producing this asset
- `due_date: Optional[str]` — ISO date for when this asset is needed
- `delivered_url: Optional[str]` — URL/path to delivered asset
- `revision_notes: List[str]` — notes if revision was requested, default empty list
- `approval_notes: Optional[str]` — operator notes on approval/rejection
- `created_at: Optional[str]` — ISO timestamp
- `updated_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Function: `create_asset_request(action: Dict[str, Any], brief: Dict[str, Any]) -> Dict[str, Any]`**
- Given a ProposedAction and CreativeBrief, determine what asset is needed
- Map brief.format to asset_type:
  - testimonial_graphic → TestimonialGraphic spec
  - offer_graphic → OfferGraphic spec
  - before_after_graphic → BeforeAfterLayout spec
  - social_reel → VideoReelBrief spec
- Populate asset spec from brief and action data (dimensions from platform, brand from profile, etc.)
- Return AssetRequest dict

**Function: `generate_image_specs_for_action(action: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]`**
- Given an action that needs visual assets, generate all needed ImageConcept specs
- For social posts: generate image specs per platform (different dimensions)
- For website updates: generate image specs for the updated section
- For ad campaigns: generate ad creative specs per platform
- Return list of ImageConcept dicts with platform-appropriate dimensions

**Function: `get_dimensions_for_platform(platform: str, content_type: str) -> Dict[str, str]`**
- Return recommended dimensions for common platform/content type combos:
  ```python
  PLATFORM_DIMENSIONS = {
      ("instagram", "post"): {"dimensions": "1080x1080", "aspect_ratio": "1:1"},
      ("instagram", "story"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
      ("instagram", "reel"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
      ("instagram", "carousel"): {"dimensions": "1080x1350", "aspect_ratio": "4:5"},
      ("facebook", "post"): {"dimensions": "1200x630", "aspect_ratio": "1.91:1"},
      ("facebook", "story"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
      ("facebook", "ad"): {"dimensions": "1080x1080", "aspect_ratio": "1:1"},
      ("linkedin", "post"): {"dimensions": "1200x627", "aspect_ratio": "1.91:1"},
      ("linkedin", "carousel"): {"dimensions": "1080x1080", "aspect_ratio": "1:1"},
      ("tiktok", "video"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
      ("youtube", "thumbnail"): {"dimensions": "1280x720", "aspect_ratio": "16:9"},
      ("youtube", "short"): {"dimensions": "1080x1920", "aspect_ratio": "9:16"},
      ("twitter", "post"): {"dimensions": "1200x675", "aspect_ratio": "16:9"},
      ("pinterest", "pin"): {"dimensions": "1000x1500", "aspect_ratio": "2:3"},
      ("google_ads", "display"): {"dimensions": "1200x628", "aspect_ratio": "1.91:1"},
      ("website", "hero"): {"dimensions": "1920x1080", "aspect_ratio": "16:9"},
      ("website", "section"): {"dimensions": "1200x800", "aspect_ratio": "3:2"},
      ("email", "header"): {"dimensions": "600x200", "aspect_ratio": "3:1"},
  }
  ```

**Function: `update_asset_status(asset_request: Dict[str, Any], new_status: str, notes: Optional[str] = None) -> Dict[str, Any]`**
- Update the status field on an AssetRequest
- If status is "revision_requested", notes parameter is required and added to revision_notes list
- If status is "delivered", delivered_url should be provided via notes
- Update updated_at timestamp
- Return updated AssetRequest dict

## Output Files

- `kai/creative/asset_support.py`

## Acceptance Criteria

- [ ] `asset_support.py` contains AssetType and AssetStatus enums with all listed values
- [ ] ImageConcept model has all 18 fields with correct types and defaults
- [ ] BeforeAfterLayout model has all 14 fields with correct types and defaults
- [ ] TestimonialGraphic model has all 13 fields with correct types and defaults
- [ ] OfferGraphic model has all 11 fields with correct types and defaults
- [ ] VideoReelBrief model has all 16 fields with correct types and defaults
- [ ] CarouselBrief model has all 10 fields with correct types and defaults
- [ ] AssetRequest model tracks the full lifecycle (requested through approved/rejected)
- [ ] create_asset_request correctly maps brief format to asset type and populates specs
- [ ] PLATFORM_DIMENSIONS covers all major platform/content type combinations (18+ entries)
- [ ] get_dimensions_for_platform returns correct dimensions for any platform/content type combo
- [ ] update_asset_status handles all status transitions and enforces notes requirement for revisions
- [ ] generate_image_specs_for_action produces platform-appropriate specs
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] All list fields use `Field(default_factory=list)`, all dict fields use `Field(default_factory=dict)`

## Reference Materials

- `kai/creative/brief.py` (created by Task 027) — CreativeBrief schema, PLATFORM_CONSTRAINTS
- `kai/models/proposal.py` (created by Task 022) — ProposedAction schema
- `kai/models/business_profile.py` (created by Task 001) — BrandVoice, TrustProfile for brand elements
- `gateway/models.py` — Pydantic import fallback pattern
- `knowledge/channels/tiktok-algorithm.md` — TikTok content requirements
- `knowledge/channels/meta-advertising.md` — Meta ad creative requirements
