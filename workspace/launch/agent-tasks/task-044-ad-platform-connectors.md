# Task 044: Build ad platform connectors

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 8. Paid Media Operations
**Priority:** P1
**Depends on:** None
**Estimated complexity:** Large

## Context

The Kai Marketing OS manages paid advertising across Google Ads, Meta (Facebook/Instagram) Ads, and Google Local Services Ads. Before any campaign management, bid optimization, or spend control can happen, there must be a connector layer that abstracts each ad platform's API into a common interface. This is the foundation of Workstream 8 — every downstream paid media feature (Tasks 045-049) depends on these connectors existing and exposing a consistent contract. Ad platform connectors are inherently higher-risk than social connectors because they involve real money — so every connector enforces dry-run defaults and spend safety checks.

## Scope

Create the `kai/connectors/ads/` package with a base abstract connector and three platform-specific implementations (Google Ads, Meta Ads, Google Local Services Ads). Each connector handles authentication, rate limiting, spend safety, and platform-specific campaign management while presenting a uniform interface.

## Detailed Requirements

### File: `kai/connectors/ads/__init__.py`

- Module docstring: "Ad platform connectors — uniform interface for campaign management, bidding, targeting, and analytics across paid advertising platforms."
- Import and re-export all connector classes
- Export `AD_PLATFORM_REGISTRY: Dict[str, Type[AdPlatformConnector]]` mapping platform name strings to connector classes
- Export `get_ad_connector(platform: str, config: dict) -> AdPlatformConnector` factory function
- `__all__` listing

### File: `kai/connectors/ads/base.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`. Use `abc.ABC` and `abc.abstractmethod`.

**Model: AdConnectorConfig**
- `platform: str` — platform name (google_ads, meta_ads, local_services_ads)
- `api_key: Optional[str]` — API key
- `api_secret: Optional[str]` — API secret / app secret
- `access_token: Optional[str]` — OAuth access token
- `refresh_token: Optional[str]` — OAuth refresh token
- `token_expiry: Optional[str]` — ISO timestamp
- `account_id: str` — ad account ID (Google customer ID, Meta ad account ID, etc.)
- `manager_account_id: Optional[str]` — MCC/manager account ID if applicable
- `sandbox_mode: bool = True` — when True, no real API calls. **DEFAULT IS TRUE — never default to live.**
- `dry_run: bool = True` — when True, mutating operations return preview without executing. **DEFAULT IS TRUE.**
- `rate_limit_rpm: int = 60`
- `max_daily_spend_usd: Optional[float]` — hard cap on daily spend this connector can set
- `max_monthly_spend_usd: Optional[float]` — hard cap on monthly spend
- `spend_alert_threshold_pct: float = 80.0` — alert when this % of budget is consumed
- `currency: str = "USD"`
- `timezone: str = "America/New_York"`
- `metadata: Dict[str, Any]` — default empty dict

**Model: CampaignSummary**
- `id: str` — platform campaign ID
- `name: str`
- `platform: str`
- `status: str` — "enabled", "paused", "removed", "ended", "draft"
- `objective: Optional[str]` — campaign objective (awareness, traffic, leads, sales, app_installs)
- `budget_daily: Optional[float]` — daily budget in account currency
- `budget_lifetime: Optional[float]` — lifetime budget
- `budget_remaining: Optional[float]` — remaining budget (if lifetime)
- `spend_today: float = 0.0`
- `spend_total: float = 0.0`
- `start_date: Optional[str]`
- `end_date: Optional[str]`
- `bid_strategy: Optional[str]` — "manual_cpc", "maximize_conversions", "target_cpa", "target_roas", "maximize_clicks", "lowest_cost"
- `ad_group_count: int = 0`
- `ad_count: int = 0`

**Model: AdGroupSummary**
- `id: str`
- `campaign_id: str`
- `name: str`
- `status: str` — "enabled", "paused", "removed"
- `bid_amount: Optional[float]`
- `ad_count: int = 0`
- `targeting_summary: Optional[str]` — human-readable targeting description

**Model: AdCreativeSummary**
- `id: str`
- `ad_group_id: str`
- `campaign_id: str`
- `format: str` — "search_responsive", "display_responsive", "video", "carousel", "collection", "single_image", "single_video", "local_services"
- `headlines: List[str]` — default empty list
- `descriptions: List[str]` — default empty list
- `media_urls: List[str]` — default empty list
- `landing_url: Optional[str]`
- `cta: Optional[str]`
- `status: str` — "active", "paused", "disapproved", "under_review", "removed"
- `disapproval_reasons: List[str]` — default empty list
- `quality_score: Optional[float]`
- `relevance_score: Optional[float]`

**Model: AdMetrics**
- `entity_id: str` — campaign, ad group, or ad ID
- `entity_type: str` — "campaign", "ad_group", "ad"
- `date_range: str` — e.g., "2026-03-01:2026-03-31"
- `impressions: int = 0`
- `clicks: int = 0`
- `ctr: float = 0.0`
- `conversions: float = 0.0`
- `conversion_rate: float = 0.0`
- `cost: float = 0.0`
- `cpc: float = 0.0`
- `cpa: float = 0.0`
- `roas: float = 0.0`
- `frequency: float = 0.0`
- `quality_score: Optional[float]`
- `relevance_score: Optional[float]`
- `impression_share: Optional[float]`

**Model: BudgetStatus**
- `account_id: str`
- `platform: str`
- `daily_budget_total: float = 0.0` — sum of all campaign daily budgets
- `daily_spend_today: float = 0.0`
- `monthly_spend: float = 0.0`
- `monthly_budget_cap: Optional[float]` — from config
- `budget_utilization_pct: float = 0.0` — monthly_spend / monthly_budget_cap * 100
- `projected_monthly_spend: float = 0.0` — extrapolated from daily spend
- `is_over_pace: bool = False` — True if projected > cap
- `alert_triggered: bool = False` — True if utilization > threshold
- `campaigns_active: int = 0`
- `campaigns_paused: int = 0`

**Model: SpendSafetyCheck**
- `operation: str` — what operation is being attempted
- `requested_amount: Optional[float]` — budget being set or changed
- `current_daily_total: float = 0.0`
- `new_daily_total_if_approved: float = 0.0`
- `monthly_cap: Optional[float]`
- `projected_monthly_if_approved: float = 0.0`
- `is_safe: bool = True`
- `warnings: List[str]` — default empty list
- `blocks: List[str]` — hard blocks that prevent the operation, default empty list

**Model: RateLimitState** (reuse pattern from social base)
- `requests_made: int = 0`
- `requests_remaining: int = 60`
- `window_reset_at: Optional[str]`
- `is_throttled: bool = False`

**Abstract class: AdPlatformConnector(ABC)**

- `__init__(self, config: AdConnectorConfig)` — store config, initialize `_rate_limit`, `_connected: bool = False`
- `platform_name: str` — abstract property

Abstract methods:
- `connect(self) -> bool` — validate credentials and establish connection
- `refresh_auth(self) -> bool` — refresh OAuth tokens
- `get_campaigns(self, status_filter: Optional[str] = None) -> List[CampaignSummary]` — list all campaigns, optionally filtered by status
- `get_campaign(self, campaign_id: str) -> CampaignSummary` — get a single campaign
- `create_campaign(self, config: Dict[str, Any]) -> CampaignSummary` — create a new campaign (requires dry_run=False)
- `update_campaign(self, campaign_id: str, changes: Dict[str, Any]) -> CampaignSummary` — update campaign settings
- `pause_campaign(self, campaign_id: str) -> CampaignSummary` — pause a campaign
- `enable_campaign(self, campaign_id: str) -> CampaignSummary` — re-enable a paused campaign
- `get_ad_groups(self, campaign_id: str) -> List[AdGroupSummary]` — list ad groups in a campaign
- `create_ad_group(self, campaign_id: str, config: Dict[str, Any]) -> AdGroupSummary` — create an ad group
- `create_ad(self, ad_group_id: str, creative: Dict[str, Any]) -> AdCreativeSummary` — create an ad creative
- `get_metrics(self, entity_id: str, entity_type: str, date_range: str) -> AdMetrics` — fetch performance metrics
- `get_budget_status(self) -> BudgetStatus` — get current budget/spend status across the account

Concrete helper methods (not abstract):
- `_check_rate_limit(self) -> bool` — rate limit check (same pattern as social)
- `_record_request(self)` — increment request counter
- `_is_sandbox(self) -> bool` — return `self.config.sandbox_mode`
- `_is_dry_run(self) -> bool` — return `self.config.dry_run`
- `_sandbox_response(self, method_name: str, **kwargs) -> Dict[str, Any]` — mock response for sandbox mode
- `_spend_safety_check(self, operation: str, requested_amount: Optional[float] = None) -> SpendSafetyCheck` — check if an operation is safe from a spend perspective:
  1. If requested_amount is set, calculate what total daily spend would be
  2. Check against max_daily_spend_usd
  3. Check projected monthly against max_monthly_spend_usd
  4. If over daily cap: add block "Daily spend cap would be exceeded"
  5. If over monthly cap: add block "Monthly spend cap would be exceeded"
  6. If over alert threshold but under cap: add warning "Spend is at {pct}% of monthly cap"
  7. Return SpendSafetyCheck with is_safe = (len(blocks) == 0)
- `_require_confirmation(self, operation: str, details: Dict[str, Any]) -> Dict[str, Any]` — for mutating operations when dry_run=False, return a confirmation dict: `{"requires_confirmation": True, "operation": operation, "details": details, "message": "This operation will make live changes. Set confirm=True to proceed."}`. Actual implementations should check for a `confirm=True` flag in the call.
- `_check_connected(self)` — raise `ConnectionError` if not connected
- `_check_mutating_allowed(self, operation: str) -> SpendSafetyCheck` — combines sandbox check, dry_run check, connected check, and spend safety check. Returns SpendSafetyCheck. If sandbox or dry_run, the check returns a mock result but doesn't block.

### File: `kai/connectors/ads/google_ads.py`

**Class: GoogleAdsConnector(AdPlatformConnector)**

- `platform_name` returns `"google_ads"`
- API version constant: `API_VERSION = "v17"`
- Uses Google Ads API

`connect()`:
- Validate config has `access_token` and `account_id` (Google customer ID format: XXX-XXX-XXXX)
- If `manager_account_id` is set, use it as login-customer-id header
- Test connection by fetching account info via `GoogleAdsService.SearchStream` with query `SELECT customer.id, customer.descriptive_name FROM customer LIMIT 1`

`get_campaigns()`:
- GAQL query: `SELECT campaign.id, campaign.name, campaign.status, campaign.advertising_channel_type, campaign_budget.amount_micros, campaign.bidding_strategy_type FROM campaign WHERE campaign.status != 'REMOVED'`
- Map status: ENABLED -> "enabled", PAUSED -> "paused", REMOVED -> "removed"
- Map bidding strategy types to human-readable strings

`create_campaign()`:
- Required config keys: `name`, `budget_daily`, `bidding_strategy`, `campaign_type` (SEARCH, DISPLAY, VIDEO, PERFORMANCE_MAX, SHOPPING)
- Create budget resource first via CampaignBudgetService
- Create campaign resource via CampaignService
- Support keyword targeting, location targeting, language targeting in config
- MUST run `_check_mutating_allowed()` and return preview if dry_run

`update_campaign()`:
- Support updating: name, status, budget (via CampaignBudgetService), bidding strategy, targeting
- MUST run spend safety check if budget is being changed

`get_ad_groups()`:
- GAQL query: `SELECT ad_group.id, ad_group.name, ad_group.status, ad_group.cpc_bid_micros FROM ad_group WHERE ad_group.campaign.id = {campaign_id}`

`create_ad()`:
- Support Responsive Search Ads: up to 15 headlines (30 chars each), up to 4 descriptions (90 chars each), final URLs, path fields
- Support Responsive Display Ads: headlines, descriptions, marketing images, logos, business name
- Validate headline/description lengths before submission

`get_metrics()`:
- GAQL query construction based on entity_type (campaign, ad_group, ad)
- Metrics: impressions, clicks, cost_micros, conversions, conversions_value, average_cpc, ctr, search_impression_share
- Convert cost_micros to USD (divide by 1_000_000)
- Support date range parameter: `WHERE segments.date BETWEEN '{start}' AND '{end}'`

Additional methods:
- `get_keywords(self, ad_group_id: str) -> List[Dict[str, Any]]` — fetch keywords with match type, status, quality score
- `add_keywords(self, ad_group_id: str, keywords: List[Dict[str, str]]) -> List[Dict[str, Any]]` — add keywords (keyword_text, match_type)
- `add_negative_keywords(self, campaign_id: str, keywords: List[str]) -> List[Dict[str, Any]]` — add campaign-level negative keywords
- `get_search_terms_report(self, campaign_id: str, date_range: str) -> List[Dict[str, Any]]` — fetch search terms report
- `_convert_micros(self, micros: int) -> float` — convert micros to dollars
- `_to_micros(self, dollars: float) -> int` — convert dollars to micros
- `_build_gaql(self, select: List[str], from_resource: str, where: Optional[str] = None, order_by: Optional[str] = None, limit: Optional[int] = None) -> str` — helper to build GAQL query strings

### File: `kai/connectors/ads/meta_ads.py`

**Class: MetaAdsConnector(AdPlatformConnector)**

- `platform_name` returns `"meta_ads"`
- API version constant: `API_VERSION = "v19.0"`
- Base URL: `BASE_URL = "https://graph.facebook.com/{API_VERSION}"`
- Uses Meta Marketing API

`connect()`:
- Validate config has `access_token` and `account_id` (format: act_XXXXXXXXX)
- Test connection by fetching `/{account_id}?fields=name,account_id,account_status,currency,timezone_name`

`get_campaigns()`:
- Endpoint: `/{account_id}/campaigns?fields=id,name,status,objective,daily_budget,lifetime_budget,start_time,stop_time,bid_strategy`
- Map status: ACTIVE -> "enabled", PAUSED -> "paused", DELETED -> "removed", ARCHIVED -> "ended"
- Map objectives: OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_LEADS, OUTCOME_SALES, etc.

`create_campaign()`:
- Required config: `name`, `objective`, `status` (PAUSED recommended for new campaigns), `special_ad_categories` (HOUSING, EMPLOYMENT, CREDIT, or empty)
- Create campaign, then create ad set within it, then create ad
- **Special Ad Categories are CRITICAL**: if the business is in housing, employment, or credit, the campaign MUST declare this. The connector should check and warn.
- Budget can be set at campaign level (CBO) or ad set level

`get_ad_groups()` (ad sets in Meta terminology):
- Endpoint: `/{campaign_id}/adsets?fields=id,name,status,daily_budget,targeting,optimization_goal,billing_event`
- Map targeting to human-readable summary

`create_ad()`:
- Support formats: single image, single video, carousel, collection
- Create ad creative first: `/{account_id}/adcreatives` with `object_story_spec` (for feed ads) or `asset_feed_spec` (for dynamic creative)
- Then create ad: `/{ad_set_id}/ads` with creative reference
- Include `tracking_specs` for pixel/conversion tracking
- Validate image dimensions and text-in-image ratio (Meta's 20% text rule is relaxed but still affects delivery)

`get_metrics()`:
- Endpoint: `/{entity_id}/insights?fields=impressions,clicks,ctr,actions,cost_per_action_type,spend,frequency`
- Parse `actions` array to extract conversions by type
- Support breakdowns: age, gender, placement, device_platform

Additional methods:
- `get_custom_audiences(self) -> List[Dict[str, Any]]` — fetch custom audiences via `/{account_id}/customaudiences`
- `create_custom_audience(self, name: str, audience_type: str, config: Dict[str, Any]) -> Dict[str, Any]` — create custom audience (customer_list, website_traffic, lookalike)
- `create_lookalike_audience(self, source_audience_id: str, country: str, ratio: float = 0.01) -> Dict[str, Any]` — create lookalike from source
- `get_pixel_events(self) -> List[Dict[str, Any]]` — check pixel status and recent events
- `check_special_ad_category(self, business_industry: Optional[str]) -> Optional[str]` — given industry, determine if special ad category is required. Return the category or None.
- `_build_headers(self) -> Dict[str, str]` — auth headers

### File: `kai/connectors/ads/local_services_ads.py`

**Class: LocalServicesAdsConnector(AdPlatformConnector)**

- `platform_name` returns `"local_services_ads"`
- Uses Google Local Services Ads API

`connect()`:
- Validate config has access_token and account_id
- Test by fetching account details

`get_campaigns()`:
- LSA doesn't have traditional campaigns — return a single CampaignSummary representing the LSA profile
- Include budget mode (weekly budget), job types enabled, service areas

`get_leads(self, date_range: Optional[str] = None, lead_type: Optional[str] = None) -> List[Dict[str, Any]]`:
- Fetch leads (phone calls, messages) via Local Services API
- Each lead: `id`, `lead_type` (PHONE_CALL, MESSAGE, BOOKING), `customer_phone`, `customer_name`, `creation_time`, `service_category`, `charged`, `charge_amount`
- Support filtering by date range and lead type

`update_budget(self, weekly_budget: float) -> Dict[str, Any]`:
- Update the weekly budget cap
- MUST run spend safety check

`get_reviews(self) -> List[Dict[str, Any]]`:
- Fetch Google Guaranteed reviews
- Each review: `reviewer_name`, `rating`, `comment`, `response`, `created_at`

`respond_to_review(self, review_id: str, response_text: str) -> Dict[str, Any]`:
- Submit a review response

`get_profile(self) -> Dict[str, Any]`:
- Fetch business profile: categories, service areas, hours, license info, insurance info, background check status

`update_service_areas(self, areas: List[Dict[str, Any]]) -> Dict[str, Any]`:
- Update service area targeting (zip codes, cities, radius)

`get_metrics()`:
- LSA metrics: leads_total, leads_charged, leads_disputed, cost_total, cost_per_lead, impression_estimate
- Date range support

Note: LSA connector doesn't implement all base class methods (e.g., create_campaign, create_ad_group, create_ad are not applicable). These should raise `NotImplementedError("Local Services Ads does not support direct campaign/ad creation. Use get_leads() and update_budget() instead.")`.

### General requirements for ALL connector files:

1. Every file starts with a module docstring
2. Use `from __future__ import annotations`
3. Import `logging`, create `logger = logging.getLogger(__name__)`
4. Every API call: (a) sandbox check, (b) rate limit check, (c) spend safety check for mutating ops, (d) dry_run check for mutating ops, (e) record request, (f) try/except with logging
5. All connectors store `_connected: bool = False`
6. ALL mutating methods default to `dry_run=True` behavior — return a preview dict showing what WOULD happen
7. Type annotations on all methods
8. No actual HTTP library imports — use `self._api_call(method, url, **kwargs)` placeholder that raises `NotImplementedError("Live API calls not yet implemented — use sandbox mode")` when not in sandbox mode

## Output Files

- `kai/connectors/ads/__init__.py`
- `kai/connectors/ads/base.py`
- `kai/connectors/ads/google_ads.py`
- `kai/connectors/ads/meta_ads.py`
- `kai/connectors/ads/local_services_ads.py`

## Acceptance Criteria

- [ ] `AdConnectorConfig` has all 17 fields, with `sandbox_mode=True` and `dry_run=True` as defaults
- [ ] `CampaignSummary`, `AdGroupSummary`, `AdCreativeSummary`, `AdMetrics`, `BudgetStatus` all have correct fields
- [ ] `SpendSafetyCheck` model exists with is_safe, warnings, and blocks fields
- [ ] `AdPlatformConnector` abstract class has all 13 abstract methods and 8 concrete helper methods
- [ ] `_spend_safety_check()` validates against daily and monthly caps
- [ ] `_check_mutating_allowed()` combines sandbox, dry_run, connected, and spend checks
- [ ] `_require_confirmation()` returns a confirmation dict for live mutations
- [ ] `GoogleAdsConnector` implements all abstract methods with GAQL queries and correct API references
- [ ] `GoogleAdsConnector` converts between micros and dollars
- [ ] `MetaAdsConnector` implements all abstract methods with correct Marketing API endpoints
- [ ] `MetaAdsConnector.check_special_ad_category()` detects housing/employment/credit industries
- [ ] `LocalServicesAdsConnector` implements applicable methods and raises NotImplementedError for inapplicable ones
- [ ] `LocalServicesAdsConnector` has `get_leads()` and `get_reviews()` methods
- [ ] All mutating operations check `_is_dry_run()` and return preview if True
- [ ] All connectors check sandbox mode first and return mock responses
- [ ] No actual HTTP library imports
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] `kai/connectors/ads/__init__.py` exports `AD_PLATFORM_REGISTRY` and `get_ad_connector` factory

## Reference Materials

- `kai/connectors/social/base.py` (created by Task 039) — SocialConnector pattern to mirror
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `kai/runtime/actions.py` — existing action lifecycle patterns (lines 50-150)
- `harness/references/google-ads-policy-reference.md` — Google Ads policies
- `harness/references/meta-ads-rules.md` — Meta Ads policies (Special Ad Categories critical)
- `knowledge/playbooks/ad-campaign-management.md` — ad campaign management playbook
- `knowledge/channels/paid-acquisition.md` — paid acquisition channel guide
- `CLAUDE.md` — full project context
