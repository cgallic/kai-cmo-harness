# Task 043: Build proof-of-life automation and filler suppression

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 7. Social Operations
**Priority:** P2
**Depends on:** 040, 041
**Estimated complexity:** Medium

## Context

Many local and small businesses struggle to maintain a consistent social media presence — they go weeks or months without posting, which signals to potential customers that the business might be inactive or untrustworthy. The proof-of-life system ensures a minimum viable social presence even when the operator is too busy to create content manually. At the same time, it must prevent low-quality filler content (generic motivational quotes, stock photos, empty holiday posts) that actually hurts the brand more than silence would. This is the "autopilot" layer that keeps the lights on while maintaining quality standards.

## Scope

Create `kai/social/proof_of_life.py` containing the proof-of-life automation engine, filler suppression logic, staleness detection, and content inventory awareness. This module coordinates with the content type system (Task 040) and scheduling queue (Task 041) to generate and schedule minimum-viable social content.

## Detailed Requirements

### File: `kai/social/proof_of_life.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: ProofOfLifeStatus (str, Enum)**
- `healthy` — posting at or above minimum frequency across all active platforms
- `at_risk` — one or more platforms approaching staleness threshold
- `stale` — one or more platforms have exceeded staleness threshold (14+ days no posts)
- `critical` — all active platforms are stale (business appears inactive)
- `disabled` — proof-of-life automation is turned off

**Enum: FillerRejectionReason (str, Enum)**
- `generic_motivational` — generic motivational quote with no brand connection
- `stock_photo_no_context` — stock photo with no meaningful caption or context
- `empty_holiday` — "Happy [holiday]" with no offer, value, or brand connection
- `low_quality_score` — content scores below minimum quality threshold
- `duplicate_recent` — content too similar to a recently posted piece
- `no_brand_relevance` — content has no connection to the business or its services
- `ai_slop_detected` — content contains AI slop phrases from CLAUDE.md banned list

**Model: PlatformHealth**
- `platform: str` — platform name
- `is_active: bool` — whether the business uses this platform
- `last_post_date: Optional[str]` — ISO date of last detected post
- `days_since_last_post: int = 0`
- `posts_this_week: int = 0`
- `posts_this_month: int = 0`
- `status: str` — ProofOfLifeStatus value
- `staleness_threshold_days: int = 14` — days without a post before flagging as stale
- `minimum_posts_per_week: int = 1` — minimum posting frequency target
- `content_types_used_30d: List[str]` — which content types have been used in last 30 days
- `content_type_gaps: List[str]` — which content types SHOULD be used but haven't been

**Model: ProofOfLifePlan**
- `platform: str`
- `planned_posts: List[Dict[str, Any]]` — list of {content_type, suggested_date, suggested_time, content_brief, priority}
- `frequency_target: str` — e.g., "1 post per week"
- `content_mix: Dict[str, int]` — content_type -> count per cycle, e.g., {"proof_post": 1, "local_tip_post": 1, "behind_the_scenes_post": 1}
- `covers_period: str` — e.g., "2026-04-01 to 2026-04-07"
- `uses_existing_content: int` — how many posts reuse existing content inventory
- `requires_new_content: int` — how many posts need new content creation

**Model: FillerCheckResult**
- `is_filler: bool` — True if the content is detected as filler
- `rejection_reasons: List[str]` — FillerRejectionReason values, default empty list
- `quality_score: Optional[float]` — estimated Four U's score (simplified), 0-16 scale
- `improvement_suggestions: List[str]` — how to make the content not-filler, default empty list
- `brand_relevance_score: float = 0.0` — 0.0 to 1.0, how connected to the business
- `checked_at: Optional[str]` — ISO timestamp

**Model: StalenessAlert**
- `id: str` — format `stale_{uuid_hex[:12]}`
- `platform: str`
- `days_since_last_post: int`
- `severity: str` — "warning" (7-13 days), "alert" (14-21 days), "critical" (21+ days)
- `suggested_action: str` — what to do about it
- `created_at: str` — ISO timestamp
- `acknowledged: bool = False`

**Model: ContentInventoryItem**
- `id: str` — unique ID
- `content_type: str` — SocialContentType value
- `source: str` — where this content came from: "completed_job", "customer_review", "team_event", "seasonal_calendar", "operator_upload", "generated"
- `raw_content: str` — the source material (review text, job description, photo description, etc.)
- `media_refs: List[str]` — associated media, default empty list
- `usable_platforms: List[str]` — which platforms this can be adapted for
- `used_count: int = 0` — how many times this has been used
- `last_used_date: Optional[str]`
- `freshness_score: float = 1.0` — 1.0 = fresh, degrades over time, 0.0 = stale
- `created_at: str`

**Class: ProofOfLifeEngine**

Core engine that maintains minimum social presence.

Methods:
- `__init__(self, minimum_posts_per_week: int = 1, platforms: Optional[List[str]] = None)` — set minimum posting frequency and active platforms. Default platforms: ["instagram", "facebook"]
- `assess_health(self, post_history: List[Dict[str, Any]]) -> Dict[str, PlatformHealth]` — given a list of past posts (with platform, date, content_type), assess the health status of each active platform. Return platform -> PlatformHealth mapping.
  - Post history items should have at minimum: `{"platform": str, "published_at": str, "content_type": Optional[str]}`
  - Calculate days_since_last_post, posts_this_week, posts_this_month
  - Determine status: healthy (meeting minimum), at_risk (below minimum this week but posted within 7 days), stale (14+ days), critical (21+ days or all platforms stale)
  - Identify content_type_gaps: if only one type is used, flag others as gaps
- `generate_plan(self, health: Dict[str, PlatformHealth], content_inventory: List[ContentInventoryItem], days_ahead: int = 7) -> Dict[str, ProofOfLifePlan]` — for each platform that is at_risk/stale/critical, generate a posting plan.
  - Minimum viable mix per week: 1 proof/testimonial + 1 tip/educational + 1 behind-scenes/community
  - Prioritize using existing content_inventory first (prefer items with used_count=0 or low freshness degrade)
  - Only generate_new_content flag for slots that can't be filled from inventory
  - Schedule posts at optimal times from DEFAULT_SCHEDULING_RULES (Task 041)
  - For critical platforms, plan an immediate post (next available slot) plus normal cadence
- `select_next_content_type(self, health: PlatformHealth) -> str` — given a platform's health, determine which content type to post next.
  - If content_type_gaps exist, fill the most important gap first
  - Default rotation: proof_post -> local_tip_post -> behind_the_scenes_post -> educational_post -> repeat
  - If seasonal_context applies (based on current date), prioritize seasonal_post
  - Never schedule two of the same content type in a row on the same platform
- `mark_post_published(self, platform: str, content_type: str, published_at: str)` — update internal tracking when a post is published. Affects health assessment.

**Class: FillerSuppressor**

Detects and blocks low-quality filler content.

Methods:
- `__init__(self)` — initialize banned phrases, quality thresholds
- `check_content(self, content_text: str, content_type: str, business_name: str, business_industry: Optional[str] = None, media_refs: Optional[List[str]] = None) -> FillerCheckResult` — analyze content and determine if it's filler. Apply all checks:
  1. **Generic motivational check**: detect generic quotes with no brand connection. Match against `GENERIC_MOTIVATIONAL_PATTERNS` list.
  2. **Stock photo check**: if media_refs is provided and content_text is very short (<50 chars) and generic, flag as stock_photo_no_context.
  3. **Empty holiday check**: detect "{Happy/Merry/Blessed} {Holiday}" patterns with no offer, CTA, or value-add. Match against `EMPTY_HOLIDAY_PATTERNS`.
  4. **Quality score check**: simplified Four U's estimation:
     - Unique: does it mention the business name or specific details? (0-4)
     - Useful: does it contain actionable info or an offer? (0-4)
     - Ultra-specific: does it have numbers, names, or specific details? (0-4)
     - Urgent: does it have a reason to engage today? (0-4)
     - If total < 8/16, flag as low_quality_score
  5. **AI slop check**: scan for banned phrases from CLAUDE.md: "In conclusion", "It's important to note", "In today's rapidly evolving", "This comprehensive guide", "Without further ado", "It's worth noting that"
  6. **Brand relevance check**: does the content mention the business name, industry, service, or location? Score 0-1. Below 0.3 = low relevance.
  7. Build improvement_suggestions for each failing check
- `_is_generic_motivational(self, text: str) -> bool` — check against patterns like "Rise and grind", "Your only limit is you", "Be the change", "Good vibes only", "Monday motivation", etc.
- `_is_empty_holiday(self, text: str) -> bool` — check against patterns like "Happy [Day]!" with no substance following
- `_estimate_quality_score(self, text: str, business_name: str, business_industry: Optional[str]) -> float` — simplified Four U's score (0-16)
- `_check_ai_slop(self, text: str) -> List[str]` — return list of AI slop phrases found
- `_calculate_brand_relevance(self, text: str, business_name: str, business_industry: Optional[str]) -> float` — simple keyword matching score

**GENERIC_MOTIVATIONAL_PATTERNS list:**
Define at least 30 patterns that indicate generic motivational filler:
- "rise and grind"
- "your only limit is you"
- "be the change"
- "good vibes only"
- "monday motivation"
- "hustle harder"
- "dream big"
- "stay positive"
- "believe in yourself"
- "make it happen"
- "never give up"
- "work hard play hard"
- "blessed and grateful"
- "living my best life"
- "new week new goals"
- "mindset is everything"
- "the grind never stops"
- "success is a journey"
- "positive vibes"
- "thankful thursday"
- "transformation tuesday"
- "wellness wednesday"
- "flashback friday"
- "self care sunday"
- "you got this"
- "keep going"
- "sky is the limit"
- "chase your dreams"
- "be unstoppable"
- "progress not perfection"

**EMPTY_HOLIDAY_PATTERNS list:**
Define patterns for empty holiday posts:
- r"^(happy|merry|blessed)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)!?\s*$"
- r"^(happy|merry|blessed)\s+\w+\s*(day|eve|weekend)!?\s*$"
- r"^(happy|merry|blessed)\s+(new year|valentine|easter|memorial|independence|labor|thanksgiving|christmas|hanukkah|diwali|holiday)!?\s*[🎉🎄🎆❤️🇺🇸]*\s*$"
- (case insensitive matching)

**Class: StalenessDetector**

Monitors for platform inactivity.

Methods:
- `__init__(self, warning_days: int = 7, alert_days: int = 14, critical_days: int = 21)` — set staleness thresholds
- `check_staleness(self, platform_health: Dict[str, PlatformHealth]) -> List[StalenessAlert]` — check each platform and generate alerts for any that are approaching or exceeding staleness thresholds.
  - Warning (7-13 days): "Platform {platform} has not been posted to in {days} days. Consider scheduling a post."
  - Alert (14-21 days): "Platform {platform} is stale ({days} days since last post). Potential customers may think the business is inactive. Schedule a post immediately."
  - Critical (21+ days): "CRITICAL: Platform {platform} has had no activity in {days} days. This actively harms credibility. Immediate action required."
- `get_most_urgent(self, alerts: List[StalenessAlert]) -> Optional[StalenessAlert]` — return the most severe/oldest alert
- `suggest_recovery_action(self, alert: StalenessAlert) -> str` — suggest what to post to recover:
  - For 7-13 days: "Post a proof-of-work or tip post to show the business is active"
  - For 14-21 days: "Post a behind-the-scenes or proof post immediately, then schedule 3 posts over the next week to rebuild consistency"
  - For 21+ days: "Post a 'we're still here' update with a value-add (tip or offer), then build a weekly posting schedule. Consider a re-introduction post."

**Helper functions (module-level):**

- `generate_stale_alert_id() -> str` — return `stale_{uuid.uuid4().hex[:12]}`
- `days_between(date_a: str, date_b: str) -> int` — calculate days between two ISO date strings
- `get_current_season() -> str` — return current season based on current month (spring/summer/fall/winter)
- `is_seasonal_relevant(content_type: str, season: str) -> bool` — certain content types are more relevant in certain seasons

## Output Files

- `kai/social/proof_of_life.py`
- `kai/social/__init__.py` (update to include proof_of_life exports)

## Acceptance Criteria

- [ ] `ProofOfLifeStatus` enum has all 5 statuses
- [ ] `FillerRejectionReason` enum has all 7 rejection reasons
- [ ] `PlatformHealth` model has all 11 fields with correct types and defaults
- [ ] `ProofOfLifePlan` model has all 7 fields
- [ ] `FillerCheckResult` model has all 6 fields
- [ ] `StalenessAlert` model has all 7 fields
- [ ] `ContentInventoryItem` model has all 11 fields
- [ ] `ProofOfLifeEngine` class has all 4 methods with correct signatures
- [ ] `ProofOfLifeEngine.generate_plan()` prioritizes existing content inventory before flagging new content needs
- [ ] `ProofOfLifeEngine.select_next_content_type()` avoids scheduling the same type consecutively
- [ ] `FillerSuppressor` class has all 6 methods including 5 internal check methods
- [ ] `FillerSuppressor.check_content()` runs all 7 checks and aggregates results
- [ ] `GENERIC_MOTIVATIONAL_PATTERNS` has at least 30 patterns
- [ ] `EMPTY_HOLIDAY_PATTERNS` has regex patterns for detecting empty holiday posts
- [ ] `FillerSuppressor` catches AI slop phrases from CLAUDE.md banned list
- [ ] Simplified Four U's estimation works on the 0-16 scale
- [ ] `StalenessDetector` class has all 3 methods
- [ ] Staleness thresholds: warning at 7 days, alert at 14 days, critical at 21 days
- [ ] All 4 helper functions exist with correct signatures
- [ ] No quality-gate-banned words appear in any string constants in this file
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/social/content_types.py` (created by Task 040) — SocialContentType enum, content type definitions
- `kai/social/scheduler.py` (created by Task 041) — PostQueue, SchedulingRules, DEFAULT_SCHEDULING_RULES
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `scripts/quality_gates/four_us_score.py` — Four U's scoring logic to reference for simplified version
- `scripts/quality_gates/banned_word_check.py` — banned word list to reference for AI slop check
- `CLAUDE.md` — quality gate rules, banned word list, AI slop phrases, Four U's framework
- `knowledge/playbooks/social-media-strategy.md` — social strategy guidance
