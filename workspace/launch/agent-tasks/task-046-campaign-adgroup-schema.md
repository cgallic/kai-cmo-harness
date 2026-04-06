# Task 046: Build campaign and ad group schema

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 8. Paid Media Operations
**Priority:** P1
**Depends on:** 044
**Estimated complexity:** Medium

## Context

The ad platform connectors (Task 044) provide a uniform interface for talking to Google Ads, Meta Ads, and LSA. But the system also needs rich internal models for campaigns, ad groups, ads, targeting, performance, and budget controls that live independent of any specific platform API. These models are the canonical internal representation — they store the "truth" of what the business is running across all platforms, enable cross-platform analysis, and provide the data structures that budget controls (Task 047), variant workflows (Task 048), and monitoring (Task 049) all consume.

## Scope

Create `kai/models/paid_media.py` containing all paid media data models: Campaign, AdGroup, Ad, Targeting, AdPerformance, BudgetGuard, and supporting types. Also create negative keyword and exclusion list models.

## Detailed Requirements

### File: `kai/models/paid_media.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`. Follow the same structural conventions as `kai/models/proposal.py` (Task 022) — enums as `str, Enum` subclasses, Pydantic models with sensible defaults.

**Enum: CampaignObjective (str, Enum)**
- `awareness` — brand awareness / reach
- `traffic` — website traffic / link clicks
- `leads` — lead generation (form fills, calls)
- `sales` — conversions / purchases
- `app_installs` — app installs
- `local` — local store visits / local awareness

**Enum: CampaignStatus (str, Enum)**
- `draft` — campaign exists in Kai but not yet on platform
- `enabled` — active and running
- `paused` — paused by operator or system
- `ended` — reached end date
- `removed` — deleted
- `limited` — running but limited (budget, targeting, or policy)
- `learning` — in platform learning phase (usually first 50 conversions on Meta)

**Enum: BidStrategy (str, Enum)**
- `manual_cpc` — manual cost-per-click bidding
- `maximize_conversions` — automated bidding for conversions
- `target_cpa` — target cost-per-acquisition
- `target_roas` — target return on ad spend
- `maximize_clicks` — automated bidding for clicks
- `lowest_cost` — Meta's default — lowest cost per result
- `cost_cap` — Meta's cost cap bidding
- `bid_cap` — Meta's bid cap
- `maximize_conversion_value` — Google's maximize conversion value

**Enum: AdFormat (str, Enum)**
- `search_responsive` — Google responsive search ad
- `display_responsive` — Google responsive display ad
- `performance_max` — Google Performance Max
- `single_image` — single image ad (Meta, LinkedIn)
- `single_video` — single video ad
- `carousel` — multi-image/video carousel
- `collection` — Meta collection ad
- `stories` — stories placement ad
- `reels` — reels placement ad
- `local_services` — Google Local Services ad
- `shopping` — Google Shopping ad
- `discovery` — Google Discovery ad

**Enum: AdStatus (str, Enum)**
- `active` — serving impressions
- `paused` — paused
- `under_review` — platform is reviewing
- `disapproved` — rejected by platform
- `approved_limited` — approved but with limited delivery
- `removed` — deleted
- `draft` — not yet submitted

**Model: Targeting**
- `locations: List[str]` — location targets (cities, states, zip codes, countries), default empty list
- `location_radius_miles: Optional[float]` — radius targeting in miles (for local businesses)
- `location_exclusions: List[str]` — locations to exclude, default empty list
- `age_min: Optional[int]` — minimum age (18-65+)
- `age_max: Optional[int]` — maximum age
- `genders: List[str]` — gender targeting: "all", "male", "female", "unknown", default ["all"]
- `interests: List[str]` — interest targeting categories, default empty list
- `behaviors: List[str]` — behavioral targeting, default empty list
- `custom_audiences: List[str]` — custom audience IDs, default empty list
- `lookalike_audiences: List[str]` — lookalike audience IDs, default empty list
- `keywords: List[str]` — keyword targeting (Google Search), default empty list
- `keyword_match_types: Dict[str, str]` — keyword -> match_type mapping (broad, phrase, exact), default empty dict
- `negative_keywords: List[str]` — negative keywords, default empty list
- `placements: List[str]` — placement targeting (feed, stories, search, display, audience_network), default empty list
- `devices: List[str]` — device targeting: "mobile", "desktop", "tablet", default empty list (= all)
- `schedule: Optional[Dict[str, Any]]` — day/hour scheduling, e.g., {"monday": [9, 17], "tuesday": [9, 17]}, default None (= all times)
- `languages: List[str]` — language codes, default ["en"]
- `estimated_reach: Optional[int]` — estimated audience size
- `targeting_summary: Optional[str]` — human-readable summary of all targeting

**Model: NegativeKeywordList**
- `id: str` — unique ID, format `nkl_{uuid_hex[:12]}`
- `name: str` — descriptive name (e.g., "Standard Service Business Exclusions", "Competitor Names")
- `keywords: List[str]` — the negative keywords, default empty list
- `match_type: str` — default match type: "broad", "phrase", "exact", default "broad"
- `applied_to_campaigns: List[str]` — campaign IDs this list is applied to, default empty list
- `is_shared: bool = False` — whether this list is shared across campaigns
- `created_at: Optional[str]`
- `updated_at: Optional[str]`

**Pre-built STANDARD_NEGATIVE_KEYWORDS: Dict[str, List[str]]**

Define standard negative keyword lists by business type:
- `"universal"`: ["free", "cheap", "diy", "how to", "tutorial", "salary", "jobs", "hiring", "reddit", "youtube", "wikipedia", "what is", "definition"]
- `"local_service"`: ["near me complaints", "lawsuit", "scam", "worst", "avoid", "cheap", "free estimate", "jobs hiring", "careers"]
- `"ecommerce"`: ["free", "torrent", "download", "diy", "homemade", "used", "refurbished", "complaint", "recall"]
- `"professional_services"`: ["free", "cheap", "pro bono", "template", "diy", "example", "sample", "class", "course", "salary", "jobs"]

**Model: ExclusionList**
- `id: str` — format `excl_{uuid_hex[:12]}`
- `name: str`
- `exclusion_type: str` — "placement", "topic", "audience"
- `items: List[str]` — the excluded items, default empty list
- `applied_to_campaigns: List[str]` — default empty list

**Model: Ad**
- `id: str` — unique ad ID, format `ad_{uuid_hex[:12]}`
- `platform_id: Optional[str]` — platform-assigned ad ID
- `ad_group_id: str` — parent ad group
- `campaign_id: str` — parent campaign
- `platform: str` — platform name
- `format: str` — AdFormat value
- `headlines: List[str]` — ad headlines, default empty list
- `descriptions: List[str]` — ad descriptions, default empty list
- `media_refs: List[str]` — media asset IDs or URLs, default empty list
- `landing_url: str` — destination URL
- `display_url: Optional[str]` — display URL (Google Ads path fields)
- `cta: Optional[str]` — call-to-action text or button type
- `status: str` — AdStatus value, default "draft"
- `compliance_status: str` — "unchecked", "compliant", "non_compliant", "under_review", default "unchecked"
- `compliance_issues: List[str]` — specific compliance problems found, default empty list
- `disapproval_reasons: List[str]` — platform disapproval reasons (if disapproved), default empty list
- `quality_score: Optional[float]` — platform quality/relevance score (1-10 scale)
- `relevance_score: Optional[float]` — platform relevance score
- `created_at: Optional[str]`
- `updated_at: Optional[str]`
- `first_served_at: Optional[str]` — when the ad first started receiving impressions
- `performance: Optional[Dict[str, Any]]` — latest performance snapshot, default None
- `variant_of: Optional[str]` — parent ad ID if this is a variant (for A/B testing)
- `variant_type: Optional[str]` — what's being tested: "headline", "description", "image", "cta", "audience"
- `is_control: bool = False` — whether this is the control variant in a test
- `metadata: Dict[str, Any]` — default empty dict

**Model: AdGroup**
- `id: str` — format `ag_{uuid_hex[:12]}`
- `platform_id: Optional[str]`
- `campaign_id: str`
- `platform: str`
- `name: str`
- `status: str` — "enabled", "paused", "removed", default "enabled"
- `targeting_refinement: Optional[Targeting]` — ad-group-level targeting overrides (if different from campaign), default None
- `bid_amount: Optional[float]` — ad-group-level bid override
- `bid_strategy_override: Optional[str]` — override campaign bid strategy at ad group level
- `ads: List[str]` — list of Ad IDs in this group, default empty list
- `ad_count: int = 0`
- `audience: Optional[str]` — audience segment name/description
- `created_at: Optional[str]`
- `updated_at: Optional[str]`
- `metadata: Dict[str, Any]` — default empty dict

**Model: AdPerformance**
- `entity_id: str` — campaign, ad group, or ad ID
- `entity_type: str` — "campaign", "ad_group", "ad"
- `platform: str`
- `date_range_start: str` — ISO date
- `date_range_end: str` — ISO date
- `impressions: int = 0`
- `clicks: int = 0`
- `ctr: float = 0.0` — click-through rate (clicks / impressions)
- `conversions: float = 0.0` — can be fractional (attributed)
- `conversion_rate: float = 0.0` — conversions / clicks
- `cost: float = 0.0` — total spend in USD
- `cpc: float = 0.0` — cost per click
- `cpa: float = 0.0` — cost per acquisition/conversion
- `roas: float = 0.0` — return on ad spend (revenue / cost)
- `revenue: float = 0.0` — attributed revenue
- `frequency: float = 0.0` — average times each user saw the ad
- `reach: int = 0` — unique users reached
- `quality_score: Optional[float]` — Google quality score (1-10)
- `relevance_score: Optional[float]` — Meta relevance diagnostics
- `impression_share: Optional[float]` — Google impression share (0-1)
- `search_impression_share: Optional[float]` — Google search impression share
- `average_position: Optional[float]` — Google average position (deprecated but useful for LSA)
- `video_views: int = 0` — for video ads
- `video_view_rate: float = 0.0`
- `fetched_at: Optional[str]` — when this data was last pulled

**Model: Campaign**
- `id: str` — format `cmp_{uuid_hex[:12]}`
- `platform_id: Optional[str]` — platform-assigned campaign ID
- `platform: str` — platform name
- `name: str`
- `objective: str` — CampaignObjective value
- `status: str` — CampaignStatus value, default "draft"
- `budget_daily: Optional[float]` — daily budget in USD
- `budget_lifetime: Optional[float]` — lifetime budget in USD
- `budget_remaining: Optional[float]` — remaining budget (for lifetime campaigns)
- `bid_strategy: str` — BidStrategy value, default "maximize_conversions"
- `bid_target_value: Optional[float]` — target CPA/ROAS value if applicable
- `start_date: Optional[str]` — ISO date
- `end_date: Optional[str]` — ISO date
- `targeting: Targeting` — campaign-level targeting (use `Field(default_factory=Targeting)` or equivalent)
- `ad_groups: List[str]` — list of AdGroup IDs, default empty list
- `ad_group_count: int = 0`
- `total_ad_count: int = 0`
- `negative_keyword_lists: List[str]` — NegativeKeywordList IDs applied, default empty list
- `exclusion_lists: List[str]` — ExclusionList IDs applied, default empty list
- `performance: Optional[AdPerformance]` — latest performance snapshot
- `special_ad_category: Optional[str]` — Meta special ad category if applicable (HOUSING, EMPLOYMENT, CREDIT)
- `learning_phase: bool = False` — whether campaign is in platform learning phase
- `learning_phase_end_estimate: Optional[str]` — estimated date learning phase will end
- `created_at: Optional[str]`
- `updated_at: Optional[str]`
- `launched_at: Optional[str]` — when campaign was first enabled
- `last_optimized_at: Optional[str]` — when campaign was last optimized/adjusted
- `business_id: Optional[str]` — link to BusinessProfile
- `tags: List[str]` — freeform tags, default empty list
- `notes: Optional[str]` — operator notes
- `metadata: Dict[str, Any]` — default empty dict

**Model: BudgetGuard**
- `id: str` — format `bg_{uuid_hex[:12]}`
- `business_id: str` — which business this guard applies to
- `max_daily_spend: float` — maximum total daily spend across all campaigns
- `max_monthly_spend: float` — maximum monthly spend
- `max_single_campaign_daily: Optional[float]` — no single campaign can exceed this daily
- `alert_threshold_pct: float = 80.0` — alert when this % of monthly budget consumed
- `auto_pause_threshold_pct: float = 100.0` — auto-pause campaigns when this % reached
- `current_daily_spend: float = 0.0` — tracked current daily total
- `current_monthly_spend: float = 0.0` — tracked current monthly total
- `is_alert_triggered: bool = False`
- `is_auto_pause_triggered: bool = False`
- `campaigns_monitored: List[str]` — campaign IDs being monitored, default empty list
- `last_checked_at: Optional[str]`
- `created_at: Optional[str]`
- `metadata: Dict[str, Any]` — default empty dict

**Helper functions (module-level):**

- `generate_campaign_id() -> str` — return `cmp_{uuid.uuid4().hex[:12]}`
- `generate_ad_group_id() -> str` — return `ag_{uuid.uuid4().hex[:12]}`
- `generate_ad_id() -> str` — return `ad_{uuid.uuid4().hex[:12]}`
- `generate_nkl_id() -> str` — return `nkl_{uuid.uuid4().hex[:12]}`
- `generate_exclusion_id() -> str` — return `excl_{uuid.uuid4().hex[:12]}`
- `generate_budget_guard_id() -> str` — return `bg_{uuid.uuid4().hex[:12]}`
- `calculate_ctr(clicks: int, impressions: int) -> float` — safe division (return 0.0 if impressions == 0)
- `calculate_cpa(cost: float, conversions: float) -> float` — safe division
- `calculate_roas(revenue: float, cost: float) -> float` — safe division
- `calculate_conversion_rate(conversions: float, clicks: int) -> float` — safe division
- `summarize_targeting(targeting: Targeting) -> str` — generate a human-readable summary of targeting settings (e.g., "Ages 25-55, Male+Female, Denver CO area, 15-mile radius, interests: home improvement")

### File: `kai/models/__init__.py` (update)

- Add imports for all new model classes and enums from `paid_media.py`
- Add them to `__all__`

## Output Files

- `kai/models/paid_media.py`
- `kai/models/__init__.py` (update)

## Acceptance Criteria

- [ ] All 5 enums exist: CampaignObjective (6 values), CampaignStatus (7 values), BidStrategy (9 values), AdFormat (12 values), AdStatus (7 values)
- [ ] `Targeting` model has all 19 fields with correct types and defaults
- [ ] `NegativeKeywordList` model has all 8 fields
- [ ] `STANDARD_NEGATIVE_KEYWORDS` dict has entries for "universal", "local_service", "ecommerce", "professional_services"
- [ ] `ExclusionList` model has all 5 fields
- [ ] `Ad` model has all 24 fields including variant tracking fields
- [ ] `AdGroup` model has all 14 fields
- [ ] `AdPerformance` model has all 25 fields with correct numeric types and defaults
- [ ] `Campaign` model has all 29 fields including learning_phase tracking
- [ ] `BudgetGuard` model has all 14 fields including auto_pause logic
- [ ] All 11 helper functions exist with correct signatures
- [ ] `calculate_ctr/cpa/roas/conversion_rate` all handle division by zero
- [ ] `summarize_targeting()` produces readable human output
- [ ] All ID generators use correct prefixes (cmp_, ag_, ad_, nkl_, excl_, bg_)
- [ ] All list fields use `Field(default_factory=list)`, all dict fields use `Field(default_factory=dict)`
- [ ] `kai/models/__init__.py` exports all new classes and enums
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] No imports from `kai/runtime/` — standalone in `kai/models/`

## Reference Materials

- `kai/connectors/ads/base.py` (created by Task 044) — CampaignSummary, AdGroupSummary, AdCreativeSummary, AdMetrics for compatibility alignment
- `kai/models/proposal.py` (created by Task 022) — ProposedAction for action_type compatibility
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile for business_id references
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `harness/references/google-ads-policy-reference.md` — Google Ads campaign structure reference
- `harness/references/meta-ads-rules.md` — Meta campaign structure and Special Ad Categories
- `knowledge/playbooks/ad-campaign-management.md` — campaign management concepts
- `CLAUDE.md` — full project context
