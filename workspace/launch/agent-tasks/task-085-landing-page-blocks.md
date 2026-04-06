# Task 085: Build landing page block generation and visual request workflow

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** Cross-Cutting Creative
**Priority:** P2
**Depends on:** 028, 034
**Estimated complexity:** Large

## Context

Landing pages are the conversion engine of marketing — every ad, email, and social post drives traffic to a landing page where the conversion happens. Rather than generating landing pages as monolithic blocks of copy, Kai generates them as composable blocks: hero, value props, social proof, process, objections, offer, CTA, and comparison. Each block is a self-contained unit with its own copy, structure, and data requirements. The visual request workflow handles the reality that some blocks need real images, photography, or video — assets the AI cannot generate but can specify with enough detail for a designer or AI image tool to produce. The page assembler combines blocks into an optimal landing page structure.

## Scope

Create `kai/creative/landing_page_blocks.py` containing the block generator for 8 landing page block types, the VisualRequest workflow for managing image/video asset needs, and the PageAssembler for combining blocks into complete pages.

## Detailed Requirements

### File: `kai/creative/landing_page_blocks.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: BlockType**
- `hero`
- `value_prop`
- `social_proof`
- `process`
- `objection_handler`
- `offer`
- `cta`
- `comparison`
- `faq`
- `trust_bar`

**Enum: VisualRequestStatus**
- `requested` — visual has been requested
- `in_progress` — designer/tool is working on it
- `delivered` — visual has been delivered
- `approved` — visual approved for use
- `deployed` — visual is live on the page

**Model: LandingPageBlock**
- `id: str` — format `block_{uuid_hex[:8]}`
- `block_type: str` — BlockType enum value
- `position: int` — suggested position on the page (1 = top)
- `headline: Optional[str]`
- `subheadline: Optional[str]`
- `body_copy: Optional[str]`
- `cta_text: Optional[str]`
- `cta_url: Optional[str]`
- `supporting_elements: List[Dict[str, Any]]` — list items, bullets, steps, etc.
- `visual_requirements: List[str]` — what images/videos this block needs
- `html_structure_suggestion: str` — semantic HTML concept (simplified, not full production)
- `schema_markup: Optional[str]` — JSON-LD if applicable
- `data_requirements: List[str]` — what business data this block needs to render
- `archetype_notes: Optional[str]` — archetype-specific guidance for this block
- `metadata: Dict[str, Any]`

**Class: LandingPageBlockGenerator**
- `__init__(self, business_profile: Any = None)`

- `generate_hero_block(self, headline: str, subheadline: str, primary_cta: str, cta_url: str, trust_badges: List[str] = None, background_image_concept: Optional[str] = None) -> LandingPageBlock`:
  - Position: 1 (always first)
  - HTML: full-width hero section with headline, subheadline, CTA button, optional background image
  - Trust badges: rendered as small icons/text below the CTA (e.g., "4.9 Stars", "Licensed", "Free Estimate")
  - Visual requirements: background image matching the image concept
  - Supporting elements: trust badges list
  - Schema: WebPage with mainEntity

- `generate_value_prop_block(self, value_props: List[Dict[str, str]], section_headline: Optional[str] = None) -> LandingPageBlock`:
  - Value props: list of {icon_concept, title, description} — typically 3-4 items
  - Position: 2 (below hero)
  - HTML: grid of cards or columns, each with icon concept, short title, description
  - Section headline: e.g., "Why Choose Us" or "What Makes Us Different"
  - No visual requirement for this block (icons are conceptual)

- `generate_social_proof_block(self, testimonials: List[Dict[str, Any]], review_aggregate: Optional[Dict[str, Any]] = None) -> LandingPageBlock`:
  - Position: 3 (after value props — proof supports claims)
  - Testimonials: list of {quote, customer_name, rating, service_type}
  - Review aggregate: {count, avg_rating, platform}
  - HTML: testimonial carousel or grid, optional aggregate badge
  - Schema: Review + AggregateRating

- `generate_process_block(self, steps: List[Dict[str, str]], section_headline: Optional[str] = None) -> LandingPageBlock`:
  - Steps: list of {step_number, title, description} — typically 3-5 steps
  - Section headline: e.g., "How It Works" or "Our Simple Process"
  - Position: 4
  - HTML: numbered steps with icons, horizontal or vertical layout
  - Each step has an icon concept description

- `generate_objection_handler_block(self, objections: List[Dict[str, str]], format_type: str = "faq") -> LandingPageBlock`:
  - Objections: list of {question, answer} (FAQ format) or {myth, truth} (myth-busting format)
  - format_type: "faq" (question/answer accordion) or "myths" (myth-busting cards)
  - Position: 5
  - HTML: accordion (FAQ) or two-column cards (myths)
  - Schema: FAQPage with Question/Answer pairs

- `generate_offer_block(self, offer_headline: str, offer_details: str, price_display: Optional[str] = None, urgency_element: Optional[str] = None, guarantee: Optional[str] = None) -> LandingPageBlock`:
  - Position: 6
  - HTML: centered offer section with prominent offer, optional price, urgency countdown/text, guarantee badge
  - Supporting elements: offer details, pricing, urgency, guarantee
  - Visual: offer graphic concept if applicable

- `generate_cta_block(self, headline: str, cta_text: str, cta_url: str, reassurance_text: Optional[str] = None, secondary_cta: Optional[Dict[str, str]] = None) -> LandingPageBlock`:
  - Position: 7 (near bottom — final push)
  - HTML: centered section with headline, large CTA button, reassurance text below
  - Reassurance: e.g., "No obligation. Free estimate. Takes 30 seconds."
  - Secondary CTA: e.g., {text: "Call Us Instead", url: "tel:+1234567890"}
  - For local service: always include phone number as secondary CTA

- `generate_comparison_block(self, comparison_items: List[Dict[str, Any]], us_label: str = "Us", them_label: str = "Others") -> LandingPageBlock`:
  - Items: list of {feature, us_value, them_value}
  - Position: 5 (alternative to or after objection handler)
  - HTML: comparison table with checkmarks/x marks
  - Note: follow competitor_mention_policy from brand constraints (never name competitors directly unless allowed)

**Model: VisualRequest**
- `id: str` — format `vr_{uuid_hex[:8]}`
- `block_id: str` — which landing page block needs this visual
- `description: str` — detailed description of what the visual should show
- `dimensions: str` — e.g., "1920x1080", "1200x628", "1080x1080"
- `format: str` — "photo", "illustration", "icon", "video", "graphic"
- `style_reference: Optional[str]` — description of desired style
- `brand_guidelines: Optional[Dict[str, Any]]` — colors, fonts, logo placement
- `priority: str` — "high", "medium", "low"
- `deadline: Optional[str]` — ISO date
- `status: str` — VisualRequestStatus enum value
- `delivered_asset_url: Optional[str]` — URL/path to delivered asset
- `approved_by: Optional[str]`
- `notes: Optional[str]`

**Class: VisualRequestWorkflow**
- `__init__(self, workspace_dir: str)`
- `create_request(self, block_id: str, description: str, dimensions: str, format: str, priority: str = "medium", style_reference: Optional[str] = None, brand_guidelines: Optional[Dict] = None, deadline: Optional[str] = None) -> VisualRequest`:
  - Create and persist a visual request
  - Return the request
- `update_status(self, request_id: str, new_status: str, **kwargs) -> bool`:
  - Update request status
  - If "delivered": require delivered_asset_url in kwargs
  - If "approved": require approved_by in kwargs
  - Return True if found and updated
- `get_pending_requests(self, business_id: Optional[str] = None) -> List[VisualRequest]`:
  - Return all requests not yet delivered
- `get_request_status(self, request_id: str) -> Optional[VisualRequest]`:
  - Return a specific request
- `link_asset_to_block(self, request_id: str, block_id: str, asset_url: str) -> bool`:
  - Connect a delivered visual to the page block that requested it
  - Return True if successful
- `get_requests_for_page(self, block_ids: List[str]) -> List[VisualRequest]`:
  - Return all visual requests associated with the given block IDs
- `_persist_request(self, request: VisualRequest)`:
  - Save request to `workspace/visual_requests/` as YAML

**Model: PageStructure**
- `page_id: str` — format `page_{uuid_hex[:8]}`
- `page_type: str` — "landing_page", "service_page", "location_page", "offer_page"
- `title: str`
- `meta_description: str`
- `blocks: List[LandingPageBlock]` — ordered list of blocks
- `visual_requests: List[VisualRequest]` — all visual requests for this page
- `schema_markup: str` — combined JSON-LD for the full page
- `estimated_word_count: int`
- `archetype: str`

**Class: PageAssembler**
- `__init__(self, block_generator: LandingPageBlockGenerator)`
- `assemble_landing_page(self, page_config: Dict[str, Any]) -> PageStructure`:
  - Accept a configuration dict with: page_type, headline, offer, value_props, testimonials, etc.
  - Generate all appropriate blocks in optimal order
  - Compile visual requests across all blocks
  - Generate page-level schema markup
  - Calculate estimated word count
  - Return PageStructure
- `get_optimal_block_order(self, page_type: str, archetype: str) -> List[str]`:
  - Return the optimal block type order for a given page type and archetype
  - **Landing page (local service)**: hero → value_prop → social_proof → process → objection_handler → offer → cta → trust_bar
  - **Landing page (ecommerce)**: hero → social_proof → value_prop → comparison → offer → objection_handler → cta
  - **Landing page (professional services)**: hero → value_prop → case_study_snippet → process → social_proof → offer → cta
  - **Service page**: hero → value_prop → process → social_proof → objection_handler → cta
  - **Location page**: hero → trust_bar → value_prop → social_proof → process → cta
- `_generate_page_schema(self, page: PageStructure) -> str`:
  - Combine schema from individual blocks into full-page JSON-LD
  - Add WebPage schema with breadcrumb support
  - Return JSON-LD string
- `_calculate_word_count(self, blocks: List[LandingPageBlock]) -> int`:
  - Sum word counts across all blocks
  - Count headline, subheadline, body_copy, supporting_elements text

## Output Files

- `kai/creative/landing_page_blocks.py`

## Acceptance Criteria

- File parses as valid Python
- All 8 block generator methods produce complete LandingPageBlock objects with all fields
- Hero block always has position 1 and includes trust badge support
- Social proof block includes schema markup for Review and AggregateRating
- Objection handler block supports both FAQ and myth-busting formats
- FAQ block includes FAQPage schema markup
- CTA block includes local-service phone number guidance
- Comparison block notes brand constraint compliance for competitor mentions
- VisualRequestWorkflow correctly manages the full lifecycle (requested → delivered → approved → deployed)
- PageAssembler produces optimal block ordering for all page type + archetype combinations
- Page-level schema markup correctly combines block-level schemas
- Visual requests are automatically created for blocks that need images
- All models use SerializableModel mixin

## Reference Materials

- `kai/creative/trust_blocks.py` (Task 083) — trust block templates for social proof
- `kai/creative/messaging_frameworks/` (Task 082) — messaging angles for copy generation
- `knowledge/frameworks/content-copywriting/perception-engineering.md` — persuasion structure
- `knowledge/checklists/perception-engineering-checklist.md` — landing page best practices
- `knowledge/checklists/website-launch-checklist.md` — page requirements
- `knowledge/frameworks/content-copywriting/qdp-qdh-qds-content-architecture.md` — content architecture
- `kai/runtime/models.py` — SerializableModel pattern
