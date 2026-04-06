# Task 038: Build on-page SEO, schema markup, and trust-block generation

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 6. Website Operations
**Priority:** P2
**Depends on:** 034
**Estimated complexity:** Medium

## Context

Every page on a business website needs proper on-page SEO elements (title tags, meta descriptions, heading structure), schema.org structured data (so Google can display rich results), trust blocks (visual credibility signals), and internal linking strategy. These elements are often missing or poorly implemented on small business websites — and they are some of the highest-ROI fixes because they improve both search visibility and conversion.

This module generates these elements programmatically from BusinessProfile data, so the system can fix SEO issues without requiring the operator to understand technical SEO. It produces ready-to-inject HTML and JSON-LD that the website action system can apply via CMS connectors.

## Scope

Build `kai/website/seo_elements.py` containing generators for title/meta tags, schema.org markup (7 types), trust blocks, and internal linking recommendations. All generators take BusinessProfile data as input and produce structured output ready for page injection.

## Detailed Requirements

### File: `kai/website/seo_elements.py`

**Constants:**

```python
# Title tag constraints
TITLE_MAX_CHARS = 60
TITLE_MIN_CHARS = 30

# Meta description constraints
META_DESC_MAX_CHARS = 160
META_DESC_MIN_CHARS = 120

# Schema.org context
SCHEMA_CONTEXT = "https://schema.org"

# Common page types
PAGE_TYPES = [
    "homepage", "service_page", "service_area_page", "contact_page",
    "about_page", "blog_post", "product_page", "faq_page",
    "testimonials_page", "gallery_page", "team_page",
]
```

---

**Title/Meta Generator:**

`generate_title_tag(page_type: str, profile: Dict[str, Any], target_keyword: Optional[str] = None, service: Optional[Dict[str, Any]] = None, area: Optional[str] = None) -> Dict[str, Any]`
- Generate an SEO-optimized title tag
- Rules (from algorithmic authorship and SEO best practices):
  - Target keyword should appear near the beginning of the title
  - Business name should appear (typically at the end, separated by "|" or "—")
  - Include a trust signal or differentiator if space permits
  - Under 60 characters (truncate intelligently, not mid-word)
  - No keyword stuffing (max 1 repetition of primary keyword)
- Page-type-specific patterns:
  - `homepage`: "{Primary Service} in {City} | {Business Name}"
  - `service_page`: "{Service Name} — {City} | {Business Name}"
  - `service_area_page`: "{Service Name} in {Area} — {Business Name}"
  - `contact_page`: "Contact {Business Name} | Free {Service} Quote"
  - `about_page`: "About {Business Name} — {City} {Service} Since {Year}"
  - `blog_post`: "{Target Keyword} — {Business Name}"
  - `product_page`: "{Product Name} | {Category} | {Business Name}"
  - `faq_page`: "{Service} FAQs — Answers from {Business Name}"
- If `target_keyword` is provided, prioritize it over the default pattern
- Return: `{"title": str, "char_count": int, "keyword_position": Optional[int], "truncated": bool}`

`generate_meta_description(page_type: str, profile: Dict[str, Any], target_keyword: Optional[str] = None, service: Optional[Dict[str, Any]] = None, area: Optional[str] = None) -> Dict[str, Any]`
- Generate an SEO-optimized meta description
- Rules:
  - Include target keyword naturally (not forced)
  - Include a call to action (call, visit, learn more)
  - Include a trust signal or proof point if space permits
  - 120-160 characters (too short gets expanded by Google, too long gets truncated)
  - Action-oriented language (start with verb when possible)
  - Include phone number for local service businesses
- Page-type-specific patterns:
  - `homepage`: "Looking for {service} in {city}? {Business Name} offers {key_benefit}. {trust_signal}. Call {phone} for a free estimate."
  - `service_page`: "Professional {service} in {city}. {Differentiator}. Free estimates — call {phone} or request a quote online."
  - `service_area_page`: "Need {service} in {area}? {Business Name} serves {area} and surrounding communities. {Trust signal}. Call {phone}."
  - `contact_page`: "Get a free {service} quote from {Business Name}. Call {phone}, email, or fill out our form. We respond within {X} hours."
  - `about_page`: "Learn about {Business Name} — {years}+ years of {service} in {city}. {Team/owner info}. {Certification}."
  - `blog_post`: varies by topic
- Return: `{"description": str, "char_count": int, "includes_keyword": bool, "includes_cta": bool, "includes_phone": bool}`

`generate_og_tags(page_type: str, profile: Dict[str, Any], title: str, description: str, page_url: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, str]`
- Generate Open Graph tags for social sharing
- Return dict with keys: "og:title", "og:description", "og:type", "og:url", "og:image", "og:site_name", "og:locale"
- og:type: "website" for homepage, "article" for blog posts, "product" for product pages
- og:image: use provided image_url, or suggest a default (business logo or hero image)

---

**Schema Markup Generator:**

`generate_local_business_schema(profile: Dict[str, Any]) -> Dict[str, Any]`
- Generate a complete LocalBusiness JSON-LD schema
- Fields:
  - `@context`: "https://schema.org"
  - `@type`: "LocalBusiness" (or more specific subtype if identifiable: "Plumber", "Electrician", "HVAC", "Dentist", "Attorney", "Restaurant", "RealEstateAgent")
  - `name`: from profile.identity.business_name
  - `url`: from profile.identity.website_url
  - `telephone`: from profile.identity.phone
  - `email`: from profile.identity.email
  - `logo`: from profile.identity.logo_url
  - `image`: from profile.identity.logo_url (or hero image if available)
  - `description`: from profile.identity.elevator_pitch
  - `address`: PostalAddress from primary location
  - `geo`: GeoCoordinates if lat/lng available in location metadata
  - `openingHoursSpecification`: from primary location hours
  - `areaServed`: from profile.geography.service_areas
  - `aggregateRating`: computed from testimonials (count and average rating)
  - `review`: from profile.trust.testimonials (first 3-5)
  - `sameAs`: list of social media profile URLs from profile.channels
  - `priceRange`: from primary offer price_range
  - `paymentAccepted`: if available in metadata
  - `hasMap`: Google Maps URL if available
- Return valid JSON-LD dict
- Include a `_validate_schema(schema: Dict) -> Dict` helper that checks for required fields

`generate_service_schema(service: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]`
- Generate Service schema JSON-LD
- Fields:
  - `@type`: "Service"
  - `name`: service name
  - `description`: service description
  - `provider`: nested LocalBusiness reference (can be compact with just @id)
  - `areaServed`: from profile.geography
  - `offers`: if price_range available, include Offer with priceRange
  - `serviceType`: service category or name
- Return JSON-LD dict

`generate_product_schema(product: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]`
- Generate Product schema JSON-LD for ecommerce products
- Fields:
  - `@type`: "Product"
  - `name`, `description`, `image`, `sku`
  - `offers`: Offer with price, priceCurrency, availability, url
  - `aggregateRating` if reviews available
  - `brand`: Organization with business name
- Return JSON-LD dict

`generate_faq_schema(faqs: List[Dict[str, str]]) -> Dict[str, Any]`
- Generate FAQPage JSON-LD schema
- Input: list of `{"question": str, "answer": str}` dicts
- Output: complete FAQPage schema with mainEntity containing Question/Answer pairs
- Answers should be plain text (strip HTML if present)
- Return JSON-LD dict

`generate_howto_schema(title: str, steps: List[Dict[str, str]], total_time: Optional[str] = None) -> Dict[str, Any]`
- Generate HowTo JSON-LD schema
- Input: title and list of `{"name": str, "text": str, "image": Optional[str]}` step dicts
- Include estimatedCost and totalTime if provided
- Return JSON-LD dict

`generate_organization_schema(profile: Dict[str, Any]) -> Dict[str, Any]`
- Generate Organization JSON-LD schema (for about pages)
- Fields: name, url, logo, description, foundingDate (from years_in_business), founders, numberOfEmployees, address, contactPoint, sameAs
- Return JSON-LD dict

`generate_review_schema(testimonials: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]`
- Generate AggregateRating + Review JSON-LD
- Compute: ratingValue (average), reviewCount, bestRating (5), worstRating (1)
- Include individual Review objects for up to 5 testimonials
- Each Review: author (Person), reviewRating (Rating), reviewBody, datePublished
- Return JSON-LD dict

**Helper: `_determine_business_subtype(profile: Dict[str, Any]) -> str`**
- Map business vertical/industry to schema.org LocalBusiness subtypes:
  - "plumbing" → "Plumber"
  - "electrical" → "Electrician"
  - "hvac" → "HVACBusiness"
  - "dental", "dentist" → "Dentist"
  - "legal", "lawyer", "attorney" → "Attorney"
  - "restaurant", "food" → "Restaurant"
  - "real estate" → "RealEstateAgent"
  - "roofing" → "RoofingContractor"
  - "locksmith" → "Locksmith"
  - "auto", "mechanic" → "AutoRepair"
  - etc.
- Default to "LocalBusiness" if no specific match
- Return schema.org type string

**Helper: `_format_opening_hours(hours: Dict[str, str]) -> List[Dict[str, Any]]`**
- Convert hours dict `{"Monday": "8am-5pm", "Tuesday": "8am-5pm", ...}` to schema.org openingHoursSpecification format
- Handle: "Closed", "24 hours", ranges like "8:00 AM - 5:00 PM"
- Return list of OpeningHoursSpecification dicts

---

**Trust Block Generator:**

`generate_trust_block(profile: Dict[str, Any], block_style: str = "horizontal") -> Dict[str, Any]`
- Generate an HTML-ready trust block from BusinessProfile trust signals
- `block_style`: "horizontal" (single row), "grid" (2x2 or 2x3), "vertical" (stacked)
- Trust items to include (in priority order, take up to 5):
  1. Years in business (if >= 5): "{years}+ Years of Experience"
  2. Review count + rating: "{count} Five-Star Reviews"
  3. Jobs/projects completed (if in metadata): "{count}+ Projects Completed"
  4. Certifications (first 1-2): "{cert} Certified"
  5. Licenses: "Licensed & Insured"
  6. Guarantee: "Satisfaction Guaranteed"
  7. Response time (if known): "We Respond Within {X} Hours"
  8. Team size: "{count}-Person Team"
- Output:
  ```python
  {
      "items": [
          {"icon_suggestion": "clock|star|shield|users|check|award",
           "text": str,
           "value": Optional[str],  # the number or rating
           "source": str},          # which profile field this came from
      ],
      "block_style": str,
      "html_suggestion": str,  # sample HTML structure
      "css_class": str,         # suggested class name
  }
  ```
- Generate `html_suggestion` as a clean HTML snippet:
  ```html
  <div class="trust-bar">
    <div class="trust-item"><span class="trust-icon">icon</span><span class="trust-text">text</span></div>
    ...
  </div>
  ```

`generate_credentials_section(profile: Dict[str, Any]) -> Dict[str, Any]`
- Generate a credentials/certifications section
- Include: certifications, licenses, awards, insurance details, professional memberships
- Output: `{"heading": "Our Credentials", "items": [...], "html_suggestion": str}`

`generate_social_proof_bar(profile: Dict[str, Any]) -> Dict[str, Any]`
- Generate a compact social proof bar (different from full trust block)
- Focus on review platforms: Google rating, Yelp rating, Facebook rating, BBB rating
- Output: `{"items": [{"platform": str, "rating": float, "count": int, "icon": str}], "html_suggestion": str}`

---

**Internal Linking Recommender:**

`recommend_internal_links(current_page: Dict[str, Any], site_pages: List[Dict[str, Any]], max_links: int = 5) -> List[Dict[str, Any]]`
- Given current page info and a list of all site pages, recommend internal links
- Rules:
  - Service pages should link to related service pages, their service area pages, and the contact page
  - Service area pages should link to service pages for services offered in that area, and the contact page
  - Blog posts should link to relevant service pages and other related blog posts
  - Homepage should link to all top-level service pages
  - No page should link to itself
  - Contact page should be linked from every other page
  - Max 1 internal link per heading section (algorithmic authorship rule)
  - Context before link (no link in first word of sentence, no link in first sentence of paragraph)
- Match by: shared service topics, shared areas, related categories
- Output: list of `{"target_page_id": str, "target_url": str, "anchor_text": str, "context": str, "placement_suggestion": str}`
  - `context`: explanation of why this link is relevant
  - `placement_suggestion`: where in the current page to place this link (section name or "after paragraph about X")

`analyze_site_linking_opportunities(pages: List[Dict[str, Any]], profile: Dict[str, Any]) -> Dict[str, Any]`
- Analyze the full site structure and identify linking gaps
- Output:
  ```python
  {
      "total_pages": int,
      "orphan_pages": List[str],        # pages with no internal links pointing to them
      "over_linked_pages": List[str],    # pages with > 10 internal links
      "under_linked_pages": List[str],   # pages with < 2 internal links
      "missing_contact_links": List[str], # pages that don't link to contact
      "recommendations": List[Dict],     # specific linking recommendations
      "hub_pages": List[str],            # pages that should serve as content hubs
  }
  ```

## Output Files

- `kai/website/seo_elements.py`

## Acceptance Criteria

- [ ] `seo_elements.py` contains all title/meta generators for 8+ page types
- [ ] Title tags stay under 60 characters with intelligent truncation
- [ ] Meta descriptions stay in 120-160 character range with CTA and trust signal
- [ ] OG tags are generated for social sharing with correct og:type per page type
- [ ] LocalBusiness schema includes all available fields from BusinessProfile
- [ ] Business subtype detection maps 10+ verticals to specific schema.org types
- [ ] Service schema includes provider, areaServed, and offers
- [ ] FAQ schema follows FAQPage specification with Question/Answer pairs
- [ ] HowTo schema includes steps with optional images and time estimates
- [ ] Organization schema includes founding info, team size, and contact
- [ ] Review/AggregateRating schema computes averages from testimonials
- [ ] Opening hours are converted to schema.org openingHoursSpecification format
- [ ] Trust block generator produces HTML-ready output with 5 prioritized trust items
- [ ] Credentials section includes certifications, licenses, awards, and insurance
- [ ] Internal linking recommender follows algorithmic authorship link placement rules
- [ ] Site linking analysis identifies orphan, over-linked, and under-linked pages
- [ ] All schema output is valid JSON-LD (uses correct @context, @type, field names)
- [ ] All generators handle missing/partial data gracefully (skip fields, don't error)
- [ ] Phone number is included in meta descriptions for local service businesses

## Reference Materials

- `knowledge/checklists/seo-checklist.md` — SEO content checklist with link placement rules
- `knowledge/checklists/technical-seo-audit-sop.md` — technical SEO audit requirements
- `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` — link placement rules (no links in first sentence)
- `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md` — entity optimization for AI search
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile for data extraction
- `kai/actions/website.py` (created by Task 034) — website actions that will apply these SEO elements
- `kai/website/local_service_pages.py` (created by Task 037) — page builders that use schema generators
- Schema.org documentation: LocalBusiness, Service, Product, FAQPage, HowTo, Organization, Review
- `CLAUDE.md` — algorithmic authorship rules for internal linking
