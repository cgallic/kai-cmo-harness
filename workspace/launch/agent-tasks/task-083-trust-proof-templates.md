# Task 083: Build trust/proof block templates and review rendering

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** Cross-Cutting Creative
**Priority:** P2
**Depends on:** 001
**Estimated complexity:** Medium

## Context

Trust and social proof are the most critical conversion elements on any marketing page — yet they are the hardest to generate programmatically because they require real business data (reviews, certifications, case studies, team info). The trust/proof block template system provides reusable, structured templates for the most common trust-building page sections. Each template defines the HTML structure concept, required data fields, and how to populate them from the business profile and proof asset memory. The review renderer takes raw review data and transforms it into multiple usable formats — website testimonials, shareable social proof, aggregate displays, and response templates.

## Scope

Create `kai/creative/trust_blocks.py` containing trust block templates, a template selection engine, the ReviewRenderer class, and review response template generation.

## Detailed Requirements

### File: `kai/creative/trust_blocks.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: TrustBlockType**
- `credentials_bar`
- `review_aggregate`
- `testimonial_card`
- `case_study_snippet`
- `team_showcase`
- `guarantee_badge`
- `media_mentions`
- `numbers_bar`
- `trust_seal_row`
- `client_logos`

**Model: TrustBlockTemplate**
- `block_type: str` — TrustBlockType enum value
- `name: str` — human-readable name
- `description: str` — when to use this block
- `required_data: List[str]` — data fields needed to render (e.g., ["review_count", "avg_rating", "platform"])
- `optional_data: List[str]` — data fields that enhance but aren't required
- `html_structure: str` — HTML skeleton/concept with {placeholder} tokens (simplified, not full production HTML)
- `copy_template: str` — copy pattern with {placeholders}
- `schema_markup: Optional[str]` — JSON-LD schema markup template if applicable
- `placement_guidance: str` — where on the page this works best: "hero_adjacent", "mid_page", "above_fold", "bottom", "sidebar"
- `archetype_relevance: List[str]` — which archetypes this is most effective for (empty = all)

**Function: build_credentials_bar() -> TrustBlockTemplate**
- Horizontal row of certification badges, license numbers, insurance logos
- Required: business_name, at least one credential
- HTML: row of badge icons with text labels
- Copy: "{credential_name} | License #{license_number} | Since {year}"
- Schema: LocalBusiness with hasCredential
- Placement: hero_adjacent or header area
- Archetype: ["local_service", "professional_services"]

**Function: build_review_aggregate() -> TrustBlockTemplate**
- Large display of aggregate review data: "4.9 stars from 127 Google Reviews"
- Required: review_count, avg_rating, review_platform
- HTML: star rating visual (text-based stars), count, platform name, link to reviews
- Copy: "{avg_rating} stars from {review_count} {platform} reviews"
- Schema: AggregateRating
- Placement: hero_adjacent, above_fold
- Archetype: all

**Function: build_testimonial_card() -> TrustBlockTemplate**
- Individual customer testimonial with attribution
- Required: quote_text, customer_name
- Optional: customer_photo_url, star_rating, service_type, date
- HTML: quote block with attribution, optional star rating, optional photo
- Copy: '"{quote_text}" — {customer_name}, {city}'
- Schema: Review with author and reviewBody
- Placement: mid_page, anywhere
- Archetype: all

**Function: build_case_study_snippet() -> TrustBlockTemplate**
- Problem → Solution → Result in 3 sentences
- Required: problem, solution, result
- Optional: client_name, industry, metric_improvement
- HTML: three-column or three-row layout with icon per section
- Copy: "Challenge: {problem}. Solution: {solution}. Result: {result}."
- Placement: mid_page
- Archetype: ["professional_services", "local_service"]

**Function: build_team_showcase() -> TrustBlockTemplate**
- Team photo/bio section with experience highlights
- Required: team_members (list of {name, role, years_experience})
- Optional: team_photo_url, certifications, fun_fact
- HTML: grid of team member cards
- Copy: "{name}, {role} — {years_experience} years of experience"
- Placement: mid_page to bottom
- Archetype: ["local_service", "professional_services"]

**Function: build_guarantee_badge() -> TrustBlockTemplate**
- Guarantee statement with badge/seal visual concept
- Required: guarantee_text, guarantee_type
- Optional: guarantee_duration, terms_url
- HTML: badge/seal design concept with guarantee text
- Copy: "{guarantee_type}: {guarantee_text}"
- Placement: near CTA, hero_adjacent
- Archetype: ["local_service", "ecommerce"]

**Function: build_media_mentions() -> TrustBlockTemplate**
- "As Seen In" row with publication logos
- Required: publications (list of {name, logo_url or placeholder})
- HTML: horizontal row of publication logos/names
- Copy: "As featured in {publication_1}, {publication_2}, and {publication_3}"
- Placement: above_fold, hero_adjacent
- Archetype: ["professional_services", "ecommerce"]

**Function: build_numbers_bar() -> TrustBlockTemplate**
- Row of impressive numbers: "500+ Projects | 15 Years | 4.9 Stars | Licensed & Insured"
- Required: at least 3 number/fact items
- HTML: horizontal bar with large numbers and descriptions
- Copy: "{number_1}+ {label_1} | {number_2} {label_2} | {number_3} {label_3}"
- Placement: hero_adjacent, above_fold
- Archetype: all

**Function: get_all_templates() -> List[TrustBlockTemplate]**
- Return all trust block templates

**Model: ReviewData**
- `reviewer_name: str`
- `rating: int` — 1-5
- `review_text: str`
- `platform: str` — "google", "yelp", "facebook", "bbb"
- `date: str` — ISO date
- `response: Optional[str]` — business response if any
- `service_type: Optional[str]`
- `verified: bool`

**Model: ReviewAggregate**
- `total_reviews: int`
- `average_rating: float`
- `platform: str`
- `rating_distribution: Dict[int, int]` — {5: 85, 4: 20, 3: 8, 2: 3, 1: 2}
- `recent_reviews: List[ReviewData]`
- `multi_platform_totals: Optional[Dict[str, Dict[str, Any]]]` — {platform: {count, avg_rating}}

**Class: ReviewRenderer**
- `__init__(self, reviews: List[ReviewData])`
- `render_website_testimonials(self, limit: int = 5, min_rating: int = 4) -> List[Dict[str, Any]]`:
  - Select best reviews for website display
  - Criteria: min_rating, length (not too short, not too long), diverse service types
  - Return list of {quote, customer_name, rating, service_type, date}
- `render_social_proof_graphic(self, review: ReviewData) -> Dict[str, Any]`:
  - Generate specifications for a social media graphic featuring one review
  - Return: {text_content, layout_type ("card", "quote"), dimensions ("1080x1080"), background_suggestion, font_suggestion}
- `render_aggregate_proof(self) -> Dict[str, Any]`:
  - Compile aggregate data across all reviews
  - Return: {total_reviews, avg_rating, platform_breakdown, star_distribution, headline (e.g., "4.9 Stars from 127 Reviews")}
- `render_review_response_templates(self) -> Dict[str, str]`:
  - Generate response templates for different review types:
    - `positive_5star`: thankful, personal, invitation to return
    - `positive_4star`: thankful, address any subtle concerns, invitation to return
    - `neutral_3star`: empathetic, address concerns, offer resolution
    - `negative_2star`: empathetic, take responsibility, offer resolution, take offline
    - `negative_1star`: empathetic, apologize, take offline, offer to make right
  - Each template: 3-5 sentences with {placeholder} for specific details
  - Return dict of {template_type: template_text}
- `curate_by_service(self, service_type: str, limit: int = 3) -> List[ReviewData]`:
  - Return reviews filtered by service_type, sorted by rating then recency
- `get_best_quotes(self, max_words: int = 30, limit: int = 10) -> List[str]`:
  - Extract the best short quotes from reviews (< max_words)
  - Prefer quotes with specific details, emotion, or results

**Function: select_trust_blocks(page_type: str, archetype: str, available_data: Dict[str, bool]) -> List[TrustBlockTemplate]**
- Given a page type (e.g., "homepage", "service_page", "landing_page", "about_page"), archetype, and what data is available:
  - Return an ordered list of recommended trust blocks
  - Order: most impactful first
  - Only include blocks where required_data is available
  - **Homepage**: review_aggregate → numbers_bar → testimonial_card → credentials_bar
  - **Service page**: testimonial_card → case_study_snippet → guarantee_badge → review_aggregate
  - **Landing page**: review_aggregate → testimonial_card → guarantee_badge → numbers_bar
  - **About page**: team_showcase → media_mentions → credentials_bar → numbers_bar

## Output Files

- `kai/creative/trust_blocks.py`

## Acceptance Criteria

- File parses as valid Python
- All 8 trust block templates are implemented with complete fields
- HTML structure concepts use {placeholder} format (not full production HTML)
- Schema markup templates are valid JSON-LD structure for applicable blocks
- ReviewRenderer curates reviews intelligently (not just first N)
- Review response templates cover all 5 rating levels with appropriate tone
- Response templates are empathetic for negative reviews (not defensive)
- select_trust_blocks returns blocks in optimal order for each page type
- select_trust_blocks only returns blocks where required data is available
- Best quote extraction prefers specific, detailed quotes over generic praise
- All models use SerializableModel mixin

## Reference Materials

- `kai/runtime/business_profile.py` — BusinessProfile fields for data availability
- `kai/memory/schemas.py` (Task 074) — ProofAssetMemory for proof asset data
- `knowledge/checklists/website-launch-checklist.md` — trust elements checklist
- `knowledge/checklists/perception-engineering-checklist.md` — persuasion elements
- `knowledge/frameworks/content-copywriting/perception-engineering.md` — trust/proof layers
- `kai/runtime/models.py` — SerializableModel pattern
