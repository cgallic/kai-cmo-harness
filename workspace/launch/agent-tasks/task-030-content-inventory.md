# Task 030: Build content inventory and asset awareness system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 5. Creative and Asset Generation
**Priority:** P2
**Depends on:** 001
**Estimated complexity:** Medium

## Context

Before creating new content or assets, Kai should know what a business already has. A restaurant might have professional photos from a recent shoot. A plumber might have 50 Google reviews but no testimonials on their website. An ecommerce brand might have case studies buried in their blog that could be repurposed. The content inventory catalogs everything a business has available — photos, testimonials, case studies, logos, brand assets, approved copy, and video clips — and makes it queryable so the creative engine can reuse existing assets instead of always creating from scratch.

The gap analysis function compares what the creative briefs require against what the inventory contains, identifying exactly what is missing and needs to be produced. This prevents wasted effort and ensures existing assets get used.

## Scope

Build `kai/creative/inventory.py` containing the ContentInventory model, inventory loader functions, gap analysis, and reuse recommendation logic.

## Detailed Requirements

### File: `kai/creative/inventory.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: AssetQuality**
- `professional` — professionally produced, high resolution, brand-consistent
- `good` — decent quality, usable as-is for most purposes
- `usable` — acceptable quality, may need minor editing
- `poor` — low quality, needs replacement or significant editing
- `placeholder` — temporary placeholder, must be replaced

**Enum: UsageRights**
- `owned` — business owns full rights
- `licensed` — licensed for specific uses (check terms)
- `stock` — stock image/video with license
- `user_generated` — customer/user submitted (need permission)
- `unknown` — usage rights not confirmed

**Model: InventoryPhoto**
- `id: str` — unique identifier
- `file_path: Optional[str]` — local file path if available
- `url: Optional[str]` — URL if hosted online
- `description: str` — what the photo shows
- `tags: List[str]` — descriptive tags: "team", "before_after", "exterior", "work_in_progress", "product", "headshot"
- `quality: str` — AssetQuality enum value, default "good"
- `usage_rights: str` — UsageRights enum value, default "owned"
- `dimensions: Optional[str]` — pixel dimensions if known
- `date_taken: Optional[str]` — ISO date
- `photographer: Optional[str]`
- `used_on: List[str]` — where this photo is currently used: "homepage", "google_maps", "instagram", etc.
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: InventoryTestimonial**
- `id: str` — unique identifier
- `quote: str` — the testimonial text
- `customer_name: str` — attribution name
- `customer_title: Optional[str]` — job title or descriptor
- `customer_location: Optional[str]` — city/state
- `source: str` — where this testimonial came from: "google", "yelp", "facebook", "direct", "email", "video"
- `date: Optional[str]` — ISO date
- `star_rating: Optional[int]` — 1-5
- `verified: bool` — whether this is from a verified review platform, default False
- `usage_rights: str` — UsageRights value, default "owned"
- `used_on: List[str]` — where this testimonial is currently displayed
- `has_photo: bool` — whether customer photo is available, default False
- `has_video: bool` — whether video testimonial exists, default False
- `service_category: Optional[str]` — which service this testimonial is about
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: InventoryCaseStudy**
- `id: str` — unique identifier
- `title: str` — case study title
- `client_name: Optional[str]` — client name (may be anonymized)
- `industry: Optional[str]` — client's industry
- `service_provided: Optional[str]` — which service was delivered
- `problem_summary: str` — brief summary of the problem
- `solution_summary: str` — brief summary of the solution
- `results_metrics: Dict[str, str]` — measurable results, e.g., {"revenue_increase": "40%", "lead_increase": "3x"}
- `url: Optional[str]` — URL if published
- `file_path: Optional[str]` — local file path if available
- `format: str` — "blog_post", "pdf", "landing_page", "video", default "blog_post"
- `date_published: Optional[str]` — ISO date
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: InventoryLogo**
- `id: str` — unique identifier
- `file_path: Optional[str]` — local file path
- `url: Optional[str]` — URL
- `format: str` — "svg", "png", "jpg", "eps", "ai"
- `color_variant: str` — "full_color", "white", "black", "monochrome", "reversed"
- `dimensions: Optional[str]`
- `is_primary: bool` — whether this is the main logo, default False
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: BrandAssets**
- `primary_colors: List[str]` — hex color codes
- `secondary_colors: List[str]` — hex color codes
- `fonts: List[Dict[str, str]]` — list of {"name": "", "usage": "headings|body|accent", "url": ""}
- `icon_set: Optional[str]` — icon library used: "fontawesome", "heroicons", "custom"
- `templates: List[Dict[str, str]]` — list of {"name": "", "type": "social|email|presentation", "url": ""}
- `style_guide_url: Optional[str]` — link to brand style guide
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: ApprovedMessageBlock**
- `id: str` — unique identifier
- `content: str` — the approved copy block
- `block_type: str` — "tagline", "boilerplate", "disclaimer", "guarantee", "value_prop", "about", "trust_statement"
- `approved_by: Optional[str]` — who approved this block
- `approved_date: Optional[str]` — ISO date
- `channels_approved_for: List[str]` — where this block can be used: "website", "email", "ads", "social", "all"
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: InventoryVideoClip**
- `id: str` — unique identifier
- `file_path: Optional[str]` — local file path
- `url: Optional[str]` — URL if hosted
- `description: str` — what the video shows
- `duration_seconds: int` — length in seconds
- `platform: Optional[str]` — which platform this was created for
- `topic: Optional[str]` — topic/subject of the video
- `quality: str` — AssetQuality value
- `usage_rights: str` — UsageRights value
- `has_audio: bool` — whether it has usable audio, default True
- `tags: List[str]` — descriptive tags
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: ContentInventory**
- `business_id: str` — links to BusinessProfile
- `photos: List[InventoryPhoto]` — default empty list
- `testimonials: List[InventoryTestimonial]` — default empty list
- `case_studies: List[InventoryCaseStudy]` — default empty list
- `logos: List[InventoryLogo]` — default empty list
- `brand_assets: Optional[BrandAssets]` — default None
- `approved_messaging: List[ApprovedMessageBlock]` — default empty list
- `video_clips: List[InventoryVideoClip]` — default empty list
- `last_updated: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Function: `load_inventory_from_workspace(workspace_path: str) -> Dict[str, Any]`**
- Scan a workspace directory for existing assets
- Look for common directory patterns:
  - `photos/`, `images/`, `assets/images/` — scan for image files (.jpg, .png, .webp, .svg)
  - `testimonials/`, `reviews/` — scan for text/markdown files with testimonial content
  - `case-studies/`, `case_studies/` — scan for case study files
  - `logos/`, `brand/` — scan for logo files
  - `videos/`, `clips/` — scan for video files (.mp4, .mov, .webm)
  - `brand/`, `style-guide/` — scan for brand asset files
- For each found file, create an inventory item with available metadata
- Mark quality as "unknown" and usage_rights as "unknown" for auto-discovered assets
- Return ContentInventory dict
- NOTE: Define the function signature and file discovery logic, but use `os.path.exists` and `os.listdir` for scanning — no heavy dependencies

**Function: `load_inventory_from_yaml(file_path: str) -> Dict[str, Any]`**
- Load a pre-defined inventory from a YAML file
- Expected YAML structure mirrors the ContentInventory model
- Return ContentInventory dict

**Function: `analyze_gaps(inventory: Dict[str, Any], briefs: List[Dict[str, Any]]) -> Dict[str, Any]`**
- Given a ContentInventory and a list of CreativeBriefs, identify what is missing
- For each brief, check:
  - Does the inventory have photos matching the brief's needs? (by tags, quality, platform)
  - Does the inventory have testimonials for the relevant service? (by service_category)
  - Does the inventory have case studies in the relevant industry? (by industry, service)
  - Are there approved messaging blocks that match the brief's key_message?
  - Are there logo variants needed for the brief's platform?
  - Are there video clips if the brief requires video?
- Output:
  ```python
  {
      "total_briefs": int,
      "briefs_with_gaps": int,
      "gaps": [
          {
              "brief_id": str,
              "brief_format": str,
              "missing_assets": [
                  {"asset_type": "photo", "description": "Need professional exterior photo", "urgency": "high|medium|low"},
                  ...
              ],
              "reuse_suggestions": [
                  {"asset_id": str, "asset_type": str, "match_reason": str, "adaptation_needed": str},
                  ...
              ],
          }
      ],
      "summary": {
          "photos_needed": int,
          "testimonials_needed": int,
          "case_studies_needed": int,
          "video_clips_needed": int,
          "logos_needed": int,
      }
  }
  ```

**Function: `recommend_reuse(inventory: Dict[str, Any], brief: Dict[str, Any]) -> List[Dict[str, Any]]`**
- Given a single CreativeBrief, search the inventory for reusable assets
- Match by:
  - Tags overlap (photo tags vs. brief content type/topic)
  - Service category (testimonial service_category vs. brief offer/topic)
  - Platform (asset platform vs. brief platform)
  - Quality threshold (only suggest "professional" or "good" quality assets)
- For each match, return:
  - `asset_id`, `asset_type` — which asset matches
  - `match_score` — 0.0 to 1.0 confidence score
  - `match_reason` — why this asset is relevant
  - `adaptation_needed` — what changes would be needed to use it (e.g., "resize from 1080x1080 to 1200x630", "add brand overlay", "crop for vertical")
- Sort by match_score descending
- Return list of reuse recommendations

**Function: `get_inventory_summary(inventory: Dict[str, Any]) -> Dict[str, Any]`**
- Return a quick summary of what is in the inventory:
  ```python
  {
      "total_photos": int,
      "professional_photos": int,
      "total_testimonials": int,
      "verified_testimonials": int,
      "total_case_studies": int,
      "total_logos": int,
      "logo_formats": List[str],
      "has_brand_assets": bool,
      "total_approved_messaging": int,
      "total_video_clips": int,
      "last_updated": Optional[str],
  }
  ```

## Output Files

- `kai/creative/inventory.py`

## Acceptance Criteria

- [ ] `inventory.py` contains AssetQuality and UsageRights enums
- [ ] All 7 inventory item models (Photo, Testimonial, CaseStudy, Logo, BrandAssets, MessageBlock, VideoClip) have all specified fields
- [ ] ContentInventory model aggregates all inventory types
- [ ] load_inventory_from_workspace scans common directory patterns for assets
- [ ] load_inventory_from_yaml loads structured inventory from YAML
- [ ] analyze_gaps correctly compares inventory against briefs and identifies missing assets
- [ ] recommend_reuse matches inventory assets to briefs by tags, category, platform, and quality
- [ ] Gap analysis output includes both missing assets and reuse suggestions per brief
- [ ] get_inventory_summary returns a quick count summary
- [ ] All functions handle empty/None inventories gracefully
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] No heavy external dependencies — uses only stdlib (os, pathlib) for file scanning

## Reference Materials

- `kai/models/business_profile.py` (created by Task 001) — TrustProfile (testimonials, case_studies), BrandVoice
- `kai/creative/brief.py` (created by Task 027) — CreativeBrief schema for gap analysis
- `gateway/models.py` — Pydantic import fallback pattern
- `workspace/` directory — example workspace structure to support
