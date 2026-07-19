# Task 003: Build normalization layer

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 1. Workspace and Business Understanding
**Priority:** P2
**Depends on:** 001
**Estimated complexity:** Medium

## Context

Business data enters Kai from many sources — YAML configs, onboarding interviews, API integrations, form inputs. Each source uses different naming conventions: "FB" vs "Facebook" vs "facebook" vs "Meta", "Google My Business" vs "GBP" vs "Google Business Profile", "NY" vs "New York" vs "new york". The normalization layer ensures that all downstream systems (audits, archetypes, channel matching) work with canonical, consistent identifiers regardless of how the data was originally entered.

## Scope

Build the `kai/normalization/` module with four sub-modules: channels, locations, metadata, and offers. Each module contains pure functions that take messy input and return normalized output. Include lookup tables and fuzzy matching where appropriate.

## Detailed Requirements

### File: `kai/normalization/__init__.py`
- Package init importing key normalize functions
- Export via `__all__`

### File: `kai/normalization/channels.py`

**Function: `normalize_channel(raw: str) -> str`**
- Convert any channel name variant to a canonical lowercase identifier
- Lookup table must include at minimum:

| Input variants | Canonical output |
|---|---|
| "FB", "Facebook", "facebook", "fb", "Meta" (when referring to social) | `"facebook"` |
| "IG", "Instagram", "instagram", "ig", "insta" | `"instagram"` |
| "Google My Business", "GMB", "GBP", "Google Business Profile", "google business" | `"gbp"` |
| "Google Ads", "Google AdWords", "AdWords", "google ads", "GAds" | `"google_ads"` |
| "Meta Ads", "Facebook Ads", "FB Ads", "Instagram Ads", "meta ads" | `"meta_ads"` |
| "LinkedIn", "linkedin", "LI" | `"linkedin"` |
| "LinkedIn Ads", "linkedin ads" | `"linkedin_ads"` |
| "TikTok", "tiktok", "tik tok", "TT" | `"tiktok"` |
| "TikTok Shop", "tiktok shop" | `"tiktok_shop"` |
| "X", "Twitter", "twitter", "x.com" | `"x_twitter"` |
| "YouTube", "youtube", "YT", "yt" | `"youtube"` |
| "Pinterest", "pinterest" | `"pinterest"` |
| "Snapchat", "snapchat", "snap" | `"snapchat"` |
| "Email", "email", "Email Marketing" | `"email"` |
| "SMS", "sms", "text", "Text Marketing" | `"sms"` |
| "SEO", "seo", "Organic Search" | `"seo"` |
| "Website", "website", "site", "web" | `"website"` |
| "Google Search Console", "GSC", "gsc" | `"gsc"` |
| "Google Analytics", "GA4", "ga4", "GA" | `"ga4"` |
| "Nextdoor", "nextdoor" | `"nextdoor"` |
| "Yelp", "yelp" | `"yelp"` |
| "Amazon", "amazon" | `"amazon"` |
| "Amazon Ads", "amazon ads" | `"amazon_ads"` |
| "Microsoft Ads", "Bing Ads", "bing ads" | `"microsoft_ads"` |
| "Podcast", "podcast", "podcasting" | `"podcast"` |
| "PR", "press", "Press Releases", "public relations" | `"pr"` |

- Matching should be case-insensitive
- Strip leading/trailing whitespace before matching
- If no match found, return the input lowercased with spaces replaced by underscores
- Include a `CHANNEL_ALIASES` dict constant that maps all variants to canonical names

**Function: `normalize_channel_list(raw_list: List[str]) -> List[str]`**
- Apply normalize_channel to each item, deduplicate, return sorted

**Function: `get_canonical_channels() -> List[str]`**
- Return the full list of canonical channel identifiers

### File: `kai/normalization/locations.py`

**Function: `normalize_state(raw: str) -> str`**
- Convert US state names and abbreviations to two-letter uppercase code
- "California" -> "CA", "ca" -> "CA", "calif" -> "CA", "Cal." -> "CA"
- Include full lookup table for all 50 states + DC + territories (PR, GU, VI, AS, MP)
- Return input unchanged if not recognized

**Function: `normalize_city(raw: str) -> str`**
- Title-case, strip extra whitespace
- Handle common abbreviations: "St." -> "Saint", "Ft." -> "Fort", "Mt." -> "Mount"
- "new york city" -> "New York City", "NYC" -> "New York City"
- "LA" -> "Los Angeles" (when context is city, not state)
- Include a small lookup of the top 20 US city abbreviations

**Function: `normalize_zip(raw: str) -> str`**
- Strip to digits only
- Pad to 5 digits with leading zeros
- Validate: 5 digits returns the zip, anything else returns empty string
- Handle "ZIP+4" format: "90210-1234" -> "90210"

**Function: `normalize_service_area(raw: str) -> str`**
- Clean up a freeform service area string
- Normalize embedded state names/abbreviations
- Standardize formatting: "los angeles, ca" -> "Los Angeles, CA"
- Trim excessive whitespace

**Function: `format_full_address(address: Optional[str], city: Optional[str], state: Optional[str], zip_code: Optional[str]) -> str`**
- Combine components into a standard US address format
- Skip None/empty components
- Apply normalization to each component

### File: `kai/normalization/metadata.py`

**Function: `normalize_industry(raw: str) -> str`**
- Map common industry names to canonical identifiers
- Lookup table:

| Input variants | Canonical |
|---|---|
| "home services", "home improvement", "residential services" | `"home_services"` |
| "legal", "law", "law firm", "attorney", "legal services" | `"legal"` |
| "healthcare", "medical", "health", "health care" | `"healthcare"` |
| "real estate", "realty", "property" | `"real_estate"` |
| "restaurant", "food service", "food & beverage", "F&B" | `"restaurant"` |
| "ecommerce", "e-commerce", "online retail", "DTC", "D2C" | `"ecommerce"` |
| "SaaS", "saas", "software", "tech" | `"saas"` |
| "fitness", "gym", "wellness", "health & fitness" | `"fitness"` |
| "beauty", "salon", "spa", "aesthetics" | `"beauty"` |
| "automotive", "auto", "car dealership", "auto repair" | `"automotive"` |
| "financial services", "finance", "fintech", "banking" | `"financial_services"` |
| "education", "edtech", "training" | `"education"` |
| "construction", "contracting", "general contractor" | `"construction"` |
| "professional services", "consulting", "consultancy" | `"professional_services"` |
| "agency", "marketing agency", "digital agency" | `"agency"` |
| "nonprofit", "non-profit", "NGO" | `"nonprofit"` |

- Case-insensitive matching
- Return lowercased, underscored input if no match

**Function: `normalize_business_model(raw: str) -> str`**
- Canonical values: "service", "product", "hybrid", "marketplace", "saas", "agency"
- Map variants: "services" -> "service", "products" -> "product", "SaaS" -> "saas", etc.

**Function: `normalize_archetype(raw: str) -> str`**
- Canonical values: "local-service", "ecommerce", "professional-services", "multi-location", "creator", "saas"
- Map common variants and strip whitespace

**Function: `normalize_stage(raw: str) -> str`**
- Canonical values: "pre-launch", "early-pmf", "growth", "scale", "mature"
- Map: "startup" -> "early-pmf", "scaling" -> "scale", "established" -> "mature", "new" -> "pre-launch"

### File: `kai/normalization/offers.py`

**Function: `normalize_offer_name(raw: str) -> str`**
- Title-case, strip extra whitespace
- Remove trailing punctuation
- Standardize common patterns: "AC Repair" stays "AC Repair", "a/c repair" -> "AC Repair"

**Function: `normalize_price_range(raw: str) -> str`**
- Standardize to "$X-Y" or "$X/period" format
- "200 to 500" -> "$200-500"
- "200-500 dollars" -> "$200-500"
- "$49 per month" -> "$49/mo"
- "49.99/mo" -> "$49.99/mo"
- "free" -> "Free"
- Return input stripped if no pattern matches

**Function: `normalize_cta(raw: str) -> str`**
- Title-case standard CTAs
- Map variants: "book now" -> "Book Now", "get a quote" -> "Get Quote", "call us" -> "Call Now", "free estimate" -> "Get Free Estimate", "schedule" -> "Schedule Now", "learn more" -> "Learn More", "buy now" -> "Buy Now", "start free trial" -> "Start Free Trial"
- Return title-cased input if no specific mapping

**Function: `normalize_margin_tier(raw: str) -> str`**
- Canonical values: "low", "medium", "high", "premium"
- Map: "thin" -> "low", "moderate" -> "medium", "fat" -> "high", "luxury" -> "premium"

### General Requirements for All Normalizers

- Every function is a pure function: input -> output, no side effects
- Every function handles None input gracefully (return None or empty string as appropriate)
- Every function has a docstring with examples
- Every function strips whitespace from string inputs
- All lookup dicts are module-level constants (ALL_CAPS names)
- Type hints on every function signature
- No external dependencies — stdlib only (re, string, typing)

## Output Files

- `kai/normalization/__init__.py`
- `kai/normalization/channels.py`
- `kai/normalization/locations.py`
- `kai/normalization/metadata.py`
- `kai/normalization/offers.py`

## Acceptance Criteria

- [ ] All 5 files exist under `kai/normalization/`
- [ ] `channels.py` has `CHANNEL_ALIASES` dict with 25+ channel mappings and `normalize_channel()` function
- [ ] `locations.py` has US state lookup table covering all 50 states + DC + territories
- [ ] `metadata.py` has industry lookup table with 15+ industries
- [ ] `offers.py` normalizes price ranges to consistent format
- [ ] Every function has type hints and a docstring with at least one example
- [ ] Every function handles None/empty input without crashing
- [ ] All lookup tables are module-level constants
- [ ] No external dependencies beyond stdlib
- [ ] `__init__.py` exports key functions via `__all__`

## Reference Materials

- `kai/models/business_profile.py` (Task 001) — the schema fields these normalizers feed into
- `config.yaml.example` — example of raw channel/site data that needs normalization
- `CLAUDE.md` — Framework Map showing channel names used across the system
