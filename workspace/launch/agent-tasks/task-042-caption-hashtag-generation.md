# Task 042: Build caption, hashtag, and geo-tag generation

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 7. Social Operations
**Priority:** P2
**Depends on:** 040
**Estimated complexity:** Small

## Context

Once the social content type system (Task 040) defines what kinds of posts exist and what each platform requires, the system needs an engine that generates platform-optimized captions, curates hashtag sets, and recommends geo-tags. This is the "writing layer" for social content — it takes a content type, platform, and business profile and produces ready-to-post captions with appropriate hashtags and location tags. The proof-of-life automation (Task 043) and the broader content pipeline rely on this engine to produce captions that follow platform best practices without manual writing.

## Scope

Create `kai/social/caption_engine.py` containing the caption generator, hashtag generator, geo-tag recommender, and all supporting models and data structures.

## Detailed Requirements

### File: `kai/social/caption_engine.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Model: CaptionRequest**
- `content_type: str` — SocialContentType value (proof_post, testimonial_post, etc.)
- `platform: str` — SocialPlatform value (instagram, facebook, linkedin, tiktok, x_twitter, youtube)
- `business_name: str` — name of the business
- `service_or_product: Optional[str]` — what was done or what's being promoted
- `result_or_outcome: Optional[str]` — measurable result or transformation
- `customer_name: Optional[str]` — customer name (for testimonials)
- `customer_quote: Optional[str]` — customer testimonial text
- `location: Optional[str]` — city/area for local businesses
- `offer_details: Optional[str]` — promotional offer details
- `offer_deadline: Optional[str]` — offer expiration
- `seasonal_context: Optional[str]` — seasonal hook (e.g., "spring", "back to school")
- `topic: Optional[str]` — educational/tip topic
- `event_name: Optional[str]` — community event name
- `tone_override: Optional[str]` — override default platform tone (e.g., "extra casual", "formal")
- `include_emoji: bool = True` — whether to suggest emoji usage
- `include_cta: bool = True` — whether to include a call-to-action
- `custom_cta: Optional[str]` — specific CTA to use instead of generated one
- `additional_context: Optional[str]` — freeform additional context for caption generation
- `metadata: Dict[str, Any]` — default empty dict

**Model: CaptionResult**
- `caption_text: str` — the full generated caption text
- `hook_line: str` — the first line / scroll-stopping hook (extracted from caption_text)
- `body_text: str` — the main body after the hook
- `cta_text: str` — the call-to-action portion
- `hashtags: List[str]` — recommended hashtags (without # prefix)
- `hashtag_string: str` — formatted hashtag string ready to append (with # prefix, space-separated)
- `full_text_with_hashtags: str` — caption_text + hashtag_string combined, formatted per platform convention
- `character_count: int` — length of full_text_with_hashtags
- `platform: str`
- `warnings: List[str]` — any warnings (e.g., "Caption exceeds recommended length for Instagram")
- `metadata: Dict[str, Any]` — default empty dict

**Model: HashtagSet**
- `hashtag: str` — the hashtag text (without # prefix)
- `category: str` — one of: "branded", "industry", "local", "trending", "niche", "community"
- `reach_estimate: Optional[str]` — qualitative: "high" (>1M posts), "medium" (100K-1M), "low" (<100K)
- `competition_level: Optional[str]` — "high", "medium", "low"
- `recommended_for: List[str]` — list of platform names this hashtag works best on

**Model: HashtagStrategy**
- `branded_hashtags: List[HashtagSet]` — 1-2 brand-specific hashtags
- `industry_hashtags: List[HashtagSet]` — 3-5 industry/category hashtags
- `local_hashtags: List[HashtagSet]` — 2-3 location-based hashtags
- `trending_hashtags: List[HashtagSet]` — 1-2 currently trending hashtags
- `niche_hashtags: List[HashtagSet]` — 2-3 specific niche hashtags
- `total_count: int` — total number of hashtags across all categories
- `platform_optimized: bool` — whether count has been trimmed to platform recommendation

**Model: GeoTagRecommendation**
- `location_name: str` — display name of the location
- `location_id: Optional[str]` — platform-specific location ID
- `platform: str` — which platform this tag is for
- `relevance: str` — "high", "medium", "low" — how relevant to the post content
- `reason: str` — why this location was recommended

**HOOK_TEMPLATES dict — scroll-stopping hooks by content type:**

Define a `HOOK_TEMPLATES: Dict[str, List[str]]` mapping each SocialContentType to 10+ hook templates. Use `{placeholders}` for personalization.

1. **proof_post**:
   - "This {service} transformation took {timeframe}. Here's what happened."
   - "Before and after: {location} {service} that speaks for itself."
   - "{result_or_outcome} — and it started with one phone call."
   - "Our client couldn't believe the difference. Neither could we."
   - "RESULTS: {result_or_outcome} for our {location} client."
   - "What a difference. Swipe to see the before."
   - "This is what {service} should look like."
   - "The transformation our {location} client didn't think was possible."
   - "We love a good before and after. This one's special."
   - "Real results. Real client. {location}."

2. **testimonial_post**:
   - "'{customer_quote}' — {customer_name}"
   - "Here's what {customer_name} had to say about working with us."
   - "We don't write our own reviews. {customer_name} did."
   - "This review made our whole week."
   - "Our clients say it better than we ever could."
   - "5 stars from {customer_name} in {location}."
   - "Read what {customer_name} said about our {service}."
   - "When you get a review like this, you screenshot it immediately."
   - "THIS is why we do what we do."
   - "Real words from a real customer."

3. **local_tip_post**:
   - "{number} signs your {item} needs {service}. (Number {number} surprises most people.)"
   - "Most {location} homeowners don't know this about {topic}."
   - "Quick tip from our {service} team that could save you hundreds."
   - "Here's what we tell every customer about {topic}."
   - "The question we get asked most: {topic}"
   - "Stop making this {topic} mistake. Here's what to do instead."
   - "Pro tip: {topic} — from our team with {years}+ years experience."
   - "You asked, we answered: {topic}"
   - "Before you try to DIY your {service}, read this."
   - "The {number} {topic} myths we hear every week."

4. **offer_post**:
   - "LIMITED: {offer_details}. Ends {offer_deadline}."
   - "For {location} only: {offer_details}"
   - "We're running our biggest {seasonal_context} deal ever."
   - "{offer_details} — but only until {offer_deadline}."
   - "First {number} callers get {offer_details}."
   - "This deal won't last. {offer_details}"
   - "Our {seasonal_context} special is HERE."
   - "{offer_details}. DM us or call now."
   - "If you've been waiting for the right time, this is it."
   - "DEAL ALERT for {location}:"

5. **behind_the_scenes_post**:
   - "A day in the life of our {service} team."
   - "Here's what goes into a typical {service} job."
   - "Behind the scenes at {business_name}."
   - "Meet the team that makes it happen."
   - "What you don't see: the prep behind every {service}."
   - "This is what {time} AM looks like at {business_name}."
   - "The tools of the trade. Here's what we use."
   - "Teamwork in action on today's {service} job."
   - "A peek behind the curtain."
   - "The part of {service} nobody talks about."

6. **educational_post**:
   - "How to {topic} in {number} easy steps."
   - "{topic}: what most people get wrong."
   - "MYTH: {myth}. FACT: {fact}."
   - "The {number} things you need to know about {topic}."
   - "Save this for later: {topic} guide."
   - "Why does {topic}? Here's the answer."
   - "Everything you need to know about {topic}."
   - "You asked about {topic}. Here's our answer."
   - "If your {item} does this, here's what it means."
   - "Expert answer: {topic}"

7. **community_post**:
   - "Proud to support {event_name} in {location}!"
   - "We love being part of the {location} community."
   - "Great time at {event_name} today."
   - "Shoutout to our neighbors at {partner_name}."
   - "{business_name} + {location} = home."
   - "Giving back to {location}: {event_name}"
   - "See you at {event_name} this {day}!"
   - "Thank you {location} for {years}+ years of trust."
   - "Community is everything. Here's why."
   - "Our favorite part of working in {location}:"

8. **seasonal_post**:
   - "It's {season} in {location} — time to think about {service}."
   - "{season} is here. Is your {item} ready?"
   - "Don't wait until it's too late: {seasonal_context} {service} reminder."
   - "{holiday} special from {business_name}!"
   - "Every {season}, we see the same {service} issue. Here's how to avoid it."
   - "Your {season} {service} checklist:"
   - "{season} is peak {service} season. Book now before we're full."
   - "Happy {holiday} from the {business_name} family!"
   - "The {season} {service} question we get every year:"
   - "{season} prep: {number} things to do for your {item} this week."

**CTA_LIBRARY dict — calls-to-action by content type and platform:**

Define `CTA_LIBRARY: Dict[str, Dict[str, List[str]]]` mapping content_type -> platform -> list of CTAs.

Common CTAs across types:
- Instagram: "Link in bio", "DM us for details", "Save this for later", "Tag someone who needs this", "Double tap if you agree"
- Facebook: "Click the link below", "Comment below", "Share with a friend", "Call us at {phone}", "Message us"
- LinkedIn: "What's your experience with this?", "Follow for more insights", "Comment your thoughts", "Connect with us", "Read the full article (link in comments)"
- TikTok: "Follow for more tips", "Comment your question", "Save this", "Share with someone who needs this", "Link in bio"
- X/Twitter: "RT if you agree", "Reply with your take", "Follow for daily tips", "Link in thread", "Bookmark this"
- YouTube: "Subscribe for more", "Drop a comment", "Like if this helped", "Watch the full video (link in bio)", "Share with someone"

Per content_type variations (provide at least 3 CTAs per content_type per platform):
- proof_post: "Want results like this? {cta}", "Ready for your transformation? {cta}", "Your {item} could look like this too."
- testimonial_post: "See why our clients love us.", "Ready to be our next success story?", "Read more reviews at {url}"
- offer_post: "Claim this offer before {deadline}.", "Call {phone} to book.", "Limited spots — act now."
- educational_post: "Save this for when you need it.", "Share with someone who needs to see this.", "Follow for more {topic} tips."

**Class: CaptionGenerator**

Methods:
- `__init__(self)` — load HOOK_TEMPLATES and CTA_LIBRARY
- `generate_caption(self, request: CaptionRequest) -> CaptionResult` — main generation method:
  1. Look up content_type in HOOK_TEMPLATES, select a hook template, fill placeholders from request fields
  2. Build body text from request context (service, result, location, customer details)
  3. Generate CTA from CTA_LIBRARY based on content_type and platform, fill placeholders
  4. Combine hook + body + CTA
  5. Apply platform-specific formatting: line breaks after hook (Instagram/LinkedIn), brevity for X, etc.
  6. Validate against platform character limits
  7. Generate warnings if over limits
  8. Return CaptionResult with all fields populated
- `_select_hook(self, content_type: str, request: CaptionRequest) -> str` — pick the most appropriate hook template and fill placeholders. Use simple round-robin or random selection from available templates.
- `_build_body(self, content_type: str, request: CaptionRequest) -> str` — construct the body paragraph based on content type and available request fields. Different structure per content type.
- `_select_cta(self, content_type: str, platform: str, request: CaptionRequest) -> str` — select and personalize a CTA.
- `_format_for_platform(self, hook: str, body: str, cta: str, platform: str, include_emoji: bool) -> str` — apply platform-specific formatting:
  - Instagram: hook + double line break + body + double line break + cta
  - Facebook: hook + line break + body + line break + cta
  - LinkedIn: hook + line break (triggers "see more") + body + line break + cta
  - TikTok: hook + body + cta (all compact)
  - X/Twitter: hook + cta (body may be omitted if over limit; prioritize hook and CTA)
  - YouTube: hook + body + cta (description format)
- `_truncate_for_platform(self, text: str, platform: str) -> tuple[str, List[str]]` — if text exceeds platform max, truncate intelligently (preserve hook and CTA, trim body). Return (truncated_text, warnings).

**Class: HashtagGenerator**

Methods:
- `__init__(self)` — initialize any internal state
- `generate_hashtags(self, business_name: str, industry: Optional[str], location: Optional[str], content_type: Optional[str], platform: str, custom_hashtags: Optional[List[str]] = None) -> HashtagStrategy`
  1. Generate branded hashtags: business name as hashtag (e.g., "AcmePlumbing"), plus business name + location if local
  2. Generate industry hashtags from a `INDUSTRY_HASHTAG_MAP: Dict[str, List[str]]` that maps common industries to relevant hashtags
  3. Generate local hashtags: city name, "{city}{industry}", "{city}business", "{city}services"
  4. Trending hashtags: return empty list by default (would need live API data in production)
  5. Niche hashtags: combine industry + content_type specific hashtags
  6. Trim total to platform-recommended count (from PLATFORM_RULES)
  7. Add any custom_hashtags provided
  8. Return HashtagStrategy with all categories populated
- `_sanitize_hashtag(self, text: str) -> str` — remove spaces, special characters, ensure lowercase, limit to 100 characters
- `_deduplicate(self, hashtags: List[HashtagSet]) -> List[HashtagSet]` — remove duplicate hashtags
- `_trim_to_platform(self, hashtags: List[HashtagSet], platform: str) -> List[HashtagSet]` — reduce to recommended count for platform, keeping a mix of categories (prioritize: branded > local > industry > niche > trending)

**INDUSTRY_HASHTAG_MAP — industry to hashtag mapping:**

Define `INDUSTRY_HASHTAG_MAP: Dict[str, List[str]]` with at least 15 industries:
- "plumbing": ["plumber", "plumbing", "plumbinglife", "plumbersofinstagram", "plumbingrepair", "waterheater", "drainservice"]
- "hvac": ["hvac", "hvaclife", "hvactech", "heating", "cooling", "airconditioning", "hvacservice"]
- "roofing": ["roofing", "roofer", "roofrepair", "newroof", "roofingcontractor", "roofinglife"]
- "landscaping": ["landscaping", "landscape", "lawncare", "gardening", "outdoorliving", "landscapedesign"]
- "cleaning": ["cleaning", "cleaningservice", "housecleaning", "deepclean", "cleaningtips", "cleanhome"]
- "electrician": ["electrician", "electrical", "electricalwork", "sparklife", "wiringexperts"]
- "dental": ["dentist", "dental", "dentistry", "oralhealth", "smile", "dentalcare"]
- "legal": ["lawyer", "attorney", "legaladvice", "lawfirm", "justice", "legalhelp"]
- "real_estate": ["realestate", "realtor", "homesale", "househunting", "dreamhome", "realtorlife"]
- "restaurant": ["restaurant", "foodie", "localfood", "eatlocal", "chef", "foodlover"]
- "automotive": ["autorepair", "mechanic", "carrepair", "automotive", "autoservice"]
- "salon": ["salon", "hairstylist", "beauty", "haircare", "hairdresser", "beautysalon"]
- "fitness": ["fitness", "personaltrainer", "gym", "workout", "fitlife", "healthylifestyle"]
- "accounting": ["accountant", "accounting", "taxseason", "smallbusiness", "bookkeeping", "cpa"]
- "photography": ["photographer", "photography", "photoshoot", "portrait", "weddingphotography"]

**Class: GeoTagRecommender**

Methods:
- `__init__(self)` — initialize
- `recommend_geo_tags(self, business_name: str, service_areas: List[str], post_content_type: str, platform: str) -> List[GeoTagRecommendation]`
  1. For proof_post / behind_the_scenes: recommend the specific job location + business location
  2. For offer_post / seasonal_post: recommend the primary service area city
  3. For community_post: recommend the event/community location
  4. For educational / testimonial / local_tip: recommend the business's primary city
  5. General rule: always include business primary location; add service area locations for local businesses
  6. Return 1-3 recommendations, sorted by relevance
- `_format_location_name(self, area: str) -> str` — clean up location string for use as a geo-tag (title case, remove state abbreviations if needed)

## Output Files

- `kai/social/caption_engine.py`
- `kai/social/__init__.py` (update to include caption_engine exports)

## Acceptance Criteria

- [ ] `CaptionRequest` model has all 19 fields with correct types and defaults
- [ ] `CaptionResult` model has all 11 fields
- [ ] `HashtagSet` model has all 5 fields
- [ ] `HashtagStrategy` model has all 7 fields
- [ ] `GeoTagRecommendation` model has all 5 fields
- [ ] `HOOK_TEMPLATES` dict has 10+ hooks for all 8 content types (80+ total hooks)
- [ ] All hooks use `{placeholder}` format and are specific/actionable (not generic filler)
- [ ] `CTA_LIBRARY` has CTAs for each content_type x platform combination
- [ ] `CaptionGenerator` class has all 6 methods with correct signatures and logic
- [ ] `CaptionGenerator.generate_caption()` produces a complete CaptionResult with hook, body, CTA, and hashtags
- [ ] Platform-specific formatting is applied (line breaks for Instagram/LinkedIn, brevity for X)
- [ ] `HashtagGenerator` class has all 4 methods with correct signatures
- [ ] `INDUSTRY_HASHTAG_MAP` has at least 15 industries with 5+ hashtags each
- [ ] Hashtag trimming respects platform-recommended counts
- [ ] `GeoTagRecommender` class has 2 methods with correct signatures
- [ ] Geo-tag recommendations vary by content type as specified
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] No quality-gate-banned words appear in any hook or CTA templates (no "leverage", "utilize", "synergy", "innovative", "deep dive", etc.)

## Reference Materials

- `kai/social/content_types.py` (created by Task 040) — SocialContentType, SocialPlatform, PlatformFormatRules, PLATFORM_RULES
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `knowledge/channels/instagram.md` — Instagram content guidance
- `knowledge/channels/tiktok-algorithm.md` — TikTok content strategy
- `knowledge/channels/linkedin-articles.md` — LinkedIn content guidance
- `knowledge/channels/x-twitter.md` — X/Twitter content guidance
- `knowledge/playbooks/social-media-strategy.md` — overall social strategy
- `CLAUDE.md` — quality gate rules, banned word list, Four U's framework
