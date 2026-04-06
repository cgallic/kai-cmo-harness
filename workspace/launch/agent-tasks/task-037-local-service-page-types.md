# Task 037: Build local-service page type builders

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 6. Website Operations
**Priority:** P1
**Depends on:** 034, 006
**Estimated complexity:** Large

## Context

Local service businesses (plumbers, electricians, roofers, cleaners, HVAC, landscapers, etc.) need specific page types that follow proven structures for converting local searchers into leads. A homepage for a plumber is fundamentally different from a homepage for a SaaS product — it needs a hero with a phone number, service area information, before/after photos, trust signals specific to home services (licensed, bonded, insured), and local schema markup.

The local-service page type builders generate complete, structured page blueprints for the four core page types every local service business needs: homepage, service pages, service area pages, and contact/quote pages. Each builder outputs a PageStructure with ordered sections, each section containing its content, position, and schema.org markup. These builders use the BusinessProfile for all dynamic content — services, areas, reviews, credentials — so the output is specific to the business, not generic templates.

## Scope

Build `kai/website/local_service_pages.py` and `kai/website/__init__.py` containing page type builder functions for the four core local service page types, the PageStructure model, and schema.org markup generators for local business use cases.

## Detailed Requirements

### File: `kai/website/__init__.py`
- Package init that imports and re-exports page builder functions
- Include `__all__` listing

### File: `kai/website/local_service_pages.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Model: PageSection**
- `section_id: str` — unique identifier within the page
- `section_type: str` — one of: "hero", "trust_bar", "services_overview", "service_detail", "process_steps", "testimonials", "before_after", "faq", "cta_block", "about_snippet", "service_area_map", "contact_info", "pricing_indicators", "credentials", "recent_work", "related_services", "area_content", "driving_directions", "area_offers", "form_section", "hours_map", "what_to_expect", "schema_markup"
- `position: int` — order position on the page (1-based)
- `heading: Optional[str]` — section heading text
- `content: Dict[str, Any]` — section content (structure varies by section_type)
- `schema_markup: Optional[Dict[str, Any]]` — JSON-LD schema for this section
- `css_class_suggestion: Optional[str]` — suggested CSS class name for styling
- `notes: Optional[str]` — implementation notes for the developer/designer
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: PageStructure**
- `page_type: str` — "homepage", "service_page", "service_area_page", "contact_page"
- `title: str` — page title (for `<title>` tag)
- `meta_description: str` — meta description
- `slug: str` — URL slug
- `sections: List[PageSection]` — ordered list of page sections
- `page_schema: List[Dict[str, Any]]` — page-level JSON-LD schema markup (can have multiple schema objects)
- `internal_links: List[Dict[str, str]]` — suggested internal links: [{"text": "", "url": "", "context": ""}]
- `canonical_url: Optional[str]`
- `og_tags: Dict[str, str]` — Open Graph tags
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Builder: `build_homepage(profile: Dict[str, Any]) -> Dict[str, Any]`**

Generates a complete homepage structure for a local service business. Extracts data from the BusinessProfile dict.

Sections in order:

1. **Hero section** (position 1)
   - `content`:
     - `headline: str` — primary headline, e.g., "{City}'s Trusted {Service} — Call for a Free Quote"
     - `subheadline: str` — supporting text, e.g., "Licensed, bonded & insured. Serving {service_area} for {years}+ years."
     - `primary_cta: Dict` — `{"text": "Call Now: {phone}", "url": "tel:{phone}", "type": "phone"}`
     - `secondary_cta: Dict` — `{"text": "Get a Free Quote", "url": "/contact", "type": "form"}`
     - `trust_indicator: str` — e.g., "{review_count}+ Five-Star Reviews on Google"
     - `background_image_suggestion: str` — description of ideal hero image
   - Notes: Phone number must be prominent and click-to-call on mobile

2. **Trust bar** (position 2)
   - `content`:
     - `items: List[Dict]` — 4-5 trust indicators: years in business, review count, certification, license, guarantee
   - Notes: Single horizontal row, no heading, badges/icons preferred

3. **Services overview** (position 3)
   - `content`:
     - `heading: str` — "Our Services" or "{Type} Services in {City}"
     - `services: List[Dict]` — each with `name`, `description` (1-2 sentences), `icon_suggestion`, `link` (to service page)
   - Notes: Grid layout (3 or 4 columns), each service links to its dedicated page

4. **About snippet** (position 4)
   - `content`:
     - `heading: str` — "Why Choose {business_name}"
     - `body: str` — 2-3 paragraphs about the business, pulled from profile identity.elevator_pitch and trust signals
     - `differentiators: List[str]` — 3-4 key differentiators
     - `team_photo_suggestion: str` — description of ideal team/owner photo
   - Notes: Include photo of owner/team if available

5. **Testimonials** (position 5)
   - `content`:
     - `heading: str` — "What Our Customers Say"
     - `testimonials: List[Dict]` — 3-5 testimonials from profile.trust.testimonials, each with quote, name, rating, service
     - `google_review_link: Optional[str]` — link to Google reviews
   - Notes: Star ratings displayed, Google icon for verified reviews

6. **Recent work / Before-After** (position 6)
   - `content`:
     - `heading: str` — "Our Recent Work" or "See the Difference"
     - `projects: List[Dict]` — each with title, description, before_image_suggestion, after_image_suggestion
     - `view_all_link: Optional[str]` — link to gallery page if exists
   - Notes: Carousel or grid layout, before/after slider if possible

7. **Service area** (position 7)
   - `content`:
     - `heading: str` — "Serving {primary_area} and Surrounding Areas"
     - `areas: List[str]` — from profile.geography.service_areas
     - `map_embed_suggestion: str` — "Embed Google Map centered on {primary_location}"
     - `area_page_links: List[Dict]` — links to service area pages
   - Notes: Include map if possible, list all service areas with links

8. **CTA block** (position 8)
   - `content`:
     - `heading: str` — "Ready to Get Started?"
     - `body: str` — 1-2 sentences with urgency element
     - `cta: Dict` — `{"text": "Call {phone}", "url": "tel:{phone}", "type": "phone"}`
     - `secondary_cta: Dict` — `{"text": "Request a Quote Online", "url": "/contact", "type": "form"}`
     - `trust_element: str` — e.g., "Free estimates. No obligation."
   - Notes: Full-width section with contrasting background

Schema markup for homepage:
- LocalBusiness schema with: name, address, phone, url, geo coordinates, openingHours, aggregateRating, areaServed
- Service schema for each service offered
- Review schema for testimonials

**Builder: `build_service_page(profile: Dict[str, Any], service: Dict[str, Any]) -> Dict[str, Any]`**

Generates a dedicated service page. `service` is an Offer dict from BusinessProfile.offers.

Sections in order:

1. **Hero/intro** (position 1)
   - Headline: "{Service Name} in {City}" or "Professional {Service Name} Services"
   - Subheadline with primary benefit
   - CTA: call or quote
   - Trust indicator relevant to this service

2. **Service description** (position 2)
   - Detailed description of the service (from offer.description expanded)
   - What's included, what to expect

3. **Process steps** (position 3)
   - Numbered steps: "How Our {Service} Works"
   - Typically 3-5 steps: Contact → Assessment → Service → Follow-Up
   - Each step: number, title, description

4. **Pricing indicators** (position 4)
   - Not exact pricing, but range or "starting at" indicators
   - From offer.price_range if available
   - "Factors that affect pricing" list
   - "Get an exact quote" CTA

5. **FAQ** (position 5)
   - 5-8 service-specific FAQs
   - Derived from common questions for this service type
   - FAQ schema.org markup

6. **Testimonials** (position 6)
   - Service-specific testimonials if available
   - Filter profile.trust.testimonials by service category

7. **Related services** (position 7)
   - Links to other service pages
   - "You might also need" framing

8. **CTA block** (position 8)
   - Service-specific CTA with phone and form

Schema markup:
- Service schema with: name, description, provider (LocalBusiness), areaServed, offers
- FAQ schema for the FAQ section
- Review schema for service-specific testimonials

**Builder: `build_service_area_page(profile: Dict[str, Any], area: str, services: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]`**

Generates a service area page for a specific geographic area.

Sections in order:

1. **Area hero** (position 1)
   - Headline: "{Service Type} Services in {Area}"
   - Subheadline: "Serving {Area} with trusted {service} since {year}"
   - CTA with phone

2. **Area content** (position 2)
   - 2-3 paragraphs of area-specific content
   - Mention local landmarks, neighborhoods, or characteristics
   - Explain why this business serves this area
   - NOTE: Content must be genuinely area-specific, not generic copy with city name swapped

3. **Services available** (position 3)
   - List of services available in this area (from `services` param or profile.offers)
   - Each links to the service page with area context

4. **Local testimonials** (position 4)
   - Testimonials from customers in this area if available
   - Filter by customer_location matching area

5. **Driving directions** (position 5)
   - If business has a physical location, include directions from the area
   - "How to reach us from {Area}"
   - Estimated drive time

6. **Area-specific offers** (position 6)
   - If there are offers specific to this area, include them
   - "Special offer for {Area} residents" framing

7. **CTA block** (position 7)
   - Area-specific CTA: "Call your {Area} {service} experts"

Schema markup:
- LocalBusiness schema with areaServed = this specific area
- Service schema for services available in this area

**Builder: `build_contact_page(profile: Dict[str, Any]) -> Dict[str, Any]`**

Generates a contact/quote request page.

Sections in order:

1. **Contact hero** (position 1)
   - Headline: "Contact {business_name}" or "Get Your Free Quote"
   - Phone number prominent

2. **Form section** (position 2)
   - Form fields: name, phone, email, service needed (dropdown from offers), message, preferred contact method
   - Minimal required fields (name, phone or email, service)
   - Form CTA: "Request a Free Quote" or "Send Message"

3. **Contact info** (position 3)
   - Phone, email, address
   - Hours of operation
   - "Response time: We respond within {X} hours"

4. **Hours and map** (position 4)
   - Business hours from profile.geography.locations[0].hours
   - Google Maps embed suggestion
   - Driving directions from major landmarks

5. **Trust signals** (position 5)
   - Credentials, certifications, guarantees
   - "Why customers choose us" bullet list

6. **What to expect** (position 6)
   - After form submission: "Here's what happens next"
   - Step 1: We'll call you within X hours
   - Step 2: Free on-site assessment
   - Step 3: Detailed quote with no obligation

Schema markup:
- LocalBusiness with contactPoint
- ContactPoint schema with phone, email, contactType

**Helper: `_extract_phone(profile: Dict[str, Any]) -> str`**
- Extract primary phone number from profile.identity.phone or profile.geography.locations[0].phone
- Return phone string or empty string if not available

**Helper: `_extract_primary_location(profile: Dict[str, Any]) -> Dict[str, Any]`**
- Extract primary location from profile.geography.locations (is_primary=True or first)
- Return location dict or empty dict

**Helper: `_extract_trust_indicators(profile: Dict[str, Any]) -> List[Dict[str, str]]`**
- Extract 4-5 trust indicators from profile.trust:
  - years_in_business → "{years}+ Years of Experience"
  - testimonials count → "{count}+ Five-Star Reviews"
  - certifications → "{cert} Certified"
  - licenses → "Licensed & Insured"
  - team_size → "{size}-Person Team"
- Return list of dicts: [{"icon": "", "text": ""}]

**Helper: `_generate_local_business_schema(profile: Dict[str, Any]) -> Dict[str, Any]`**
- Generate a complete LocalBusiness JSON-LD schema from BusinessProfile data
- Include: @context, @type, name, url, telephone, address (PostalAddress), geo (GeoCoordinates if available), openingHoursSpecification, aggregateRating (from review count/rating), areaServed, image, sameAs (social profiles)
- Return JSON-LD dict

**Helper: `_generate_service_schema(service: Dict[str, Any], profile: Dict[str, Any]) -> Dict[str, Any]`**
- Generate a Service JSON-LD schema
- Include: @context, @type, name, description, provider (LocalBusiness reference), areaServed, offers (if price_range available)
- Return JSON-LD dict

**Helper: `_generate_faq_schema(faqs: List[Dict[str, str]]) -> Dict[str, Any]`**
- Generate FAQPage JSON-LD schema from a list of {"question": "", "answer": ""} dicts
- Return JSON-LD dict

**Helper: `_generate_review_schema(testimonials: List[Dict[str, Any]]) -> List[Dict[str, Any]]`**
- Generate Review JSON-LD schema for each testimonial
- Include: @type, author, reviewRating, reviewBody, datePublished
- Return list of Review schema dicts

**Helper: `_build_meta_title(page_type: str, profile: Dict[str, Any], service: Optional[Dict[str, Any]] = None, area: Optional[str] = None) -> str`**
- Generate SEO-optimized title tag:
  - Homepage: "{Business Name} — {Primary Service} in {City} | {Trust Signal}"
  - Service page: "{Service Name} in {City} | {Business Name}"
  - Area page: "{Service Type} in {Area} | {Business Name}"
  - Contact: "Contact {Business Name} | Free Quote | {Phone}"
- Keep under 60 characters (truncate business name if needed)

**Helper: `_build_meta_description(page_type: str, profile: Dict[str, Any], service: Optional[Dict[str, Any]] = None, area: Optional[str] = None) -> str`**
- Generate meta description:
  - Homepage: "{Business Name} offers professional {services} in {City}. {Trust Signal}. Call {phone} for a free estimate."
  - Service page: "Professional {service} services in {City}. {Key benefit}. Free estimates. Call {phone}."
  - Area page: "Need {service} in {area}? {Business Name} serves {area} with {trust signal}. Call {phone}."
  - Contact: "Contact {Business Name} for a free {service} quote. Call {phone} or fill out our form. We respond within {X} hours."
- Keep under 160 characters

## Output Files

- `kai/website/__init__.py`
- `kai/website/local_service_pages.py`

## Acceptance Criteria

- [ ] `local_service_pages.py` contains PageSection and PageStructure models
- [ ] build_homepage generates 8 sections in the correct order with all specified content fields
- [ ] build_service_page generates 8 sections with service-specific content
- [ ] build_service_area_page generates 7 sections with genuinely area-specific content guidance
- [ ] build_contact_page generates 6 sections with form, contact info, and trust signals
- [ ] All builders extract data from BusinessProfile dict (not hardcoded content)
- [ ] Phone numbers are extracted and included in heroes and CTA blocks
- [ ] Trust indicators are extracted from profile.trust and formatted for display
- [ ] LocalBusiness schema is generated with all available fields
- [ ] Service schema is generated for each service
- [ ] FAQ schema follows FAQPage specification
- [ ] Review schema is generated from testimonials
- [ ] Meta titles are under 60 characters
- [ ] Meta descriptions are under 160 characters
- [ ] OG tags are included in PageStructure
- [ ] Internal links are suggested between related pages (service → area, area → service, all → contact)
- [ ] All helpers handle missing/None data gracefully (return defaults, not errors)
- [ ] KaiCalls: contact page mentions AI receptionist availability for after-hours calls if applicable

## Reference Materials

- `kai/models/business_profile.py` (created by Task 001) — full BusinessProfile schema for data extraction
- `kai/actions/website.py` (created by Task 034) — website actions that will implement these page structures
- Task 006 spec — local-service archetype definition for archetype-specific patterns
- `knowledge/checklists/local-service-business-checklist.md` — local service business requirements
- `knowledge/checklists/seo-checklist.md` — SEO requirements for page elements
- `knowledge/checklists/technical-seo-audit-sop.md` — technical SEO requirements
- Schema.org references: LocalBusiness, Service, FAQPage, Review
- `CLAUDE.md` — KaiCalls rule for phone lead capture recommendations
