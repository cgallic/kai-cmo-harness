# Task 056: Build analytics connector layer

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 10. Analytics, Attribution, and Monitoring
**Priority:** P1
**Depends on:** None
**Estimated complexity:** Large

## Context

The Kai marketing OS needs to pull metrics from multiple analytics platforms to measure marketing performance, detect anomalies, attribute outcomes to actions, and build dashboards. This connector layer is the data foundation for all monitoring, scoring, and learning subsystems. Without standardized analytics access, the system cannot prove that its marketing actions produced results or detect when things go wrong.

Every downstream analytics feature — KPI models (057), attribution (058), anomaly detection (059), scorecards (060), and watchers (067-072) — depends on this connector layer producing a unified MetricPoint format.

## Scope

Create `kai/connectors/analytics/` module with an abstract base connector and five concrete connectors (GA4, GSC, call tracking, GBP, ad metrics), plus a unified metric format that all connectors output. These are schema and interface definitions — actual API calls should be stubbed with clear docstrings explaining what API endpoints they would hit.

## Detailed Requirements

### File: `kai/connectors/__init__.py`
- Empty or with a module docstring

### File: `kai/connectors/analytics/__init__.py`
- Export all connector classes and the MetricPoint model
- Module docstring explaining the unified analytics layer

### File: `kai/connectors/analytics/base.py`

Use the same dataclass + `SerializableModel` pattern from `kai/runtime/models.py`. Import `SerializableModel` from `kai.runtime.models`.

**Model: MetricPoint**
- `metric_name: str` — canonical metric name (e.g., "sessions", "clicks", "phone_calls")
- `value: float` — the metric value
- `date: str` — ISO date string (YYYY-MM-DD)
- `dimension: Optional[str]` — optional dimension value (e.g., "organic", "mobile", "homepage")
- `dimension_name: Optional[str]` — dimension key (e.g., "traffic_source", "device", "page")
- `source: str` — which connector produced this (e.g., "ga4", "gsc", "call_tracking", "gbp")
- `metadata: Dict[str, Any]` — additional context (e.g., confidence interval, sample size)

**Model: DateRange**
- `start_date: str` — ISO date string
- `end_date: str` — ISO date string

**Model: ConnectorConfig**
- `connector_type: str` — e.g., "ga4", "gsc", "call_tracking"
- `credentials: Dict[str, Any]` — API keys, OAuth tokens, service account paths (never logged)
- `property_id: Optional[str]` — GA4 property, GSC site URL, GBP location ID, etc.
- `enabled: bool` — whether this connector is active
- `metadata: Dict[str, Any]` — connector-specific config

**Abstract class: AnalyticsConnector**
- `__init__(self, config: ConnectorConfig)` — store config
- `connect(self) -> bool` — validate credentials and connectivity (stub: return True)
- `get_metrics(self, date_range: DateRange, dimensions: List[str], metrics: List[str]) -> List[MetricPoint]` — abstract, returns metric data
- `get_events(self, event_name: str, date_range: DateRange) -> List[MetricPoint]` — abstract, returns event-level data
- `get_real_time(self) -> List[MetricPoint]` — abstract, returns real-time snapshot
- `get_conversion_data(self, date_range: DateRange) -> List[MetricPoint]` — abstract, returns conversion metrics
- `available_metrics(self) -> List[str]` — abstract, returns list of metrics this connector can provide
- `available_dimensions(self) -> List[str]` — abstract, returns list of dimensions this connector supports

### File: `kai/connectors/analytics/ga4.py`

**Class: GA4Connector(AnalyticsConnector)**
- `connector_type = "ga4"`
- Available metrics: `sessions`, `active_users`, `new_users`, `page_views`, `screen_page_views`, `engagement_rate`, `engaged_sessions`, `average_session_duration`, `bounce_rate`, `conversions`, `event_count`, `user_engagement`, `session_conversion_rate`
- Available dimensions: `date`, `page_path`, `page_title`, `traffic_source`, `session_source`, `session_medium`, `session_campaign`, `device_category`, `country`, `city`, `landing_page`, `event_name`
- `get_metrics()` — stub that returns empty list with docstring explaining it would call GA4 Data API v1 `runReport` endpoint
- `get_events()` — stub for GA4 Data API event-level reporting
- `get_real_time()` — stub for GA4 Data API `runRealtimeReport` endpoint
- `get_conversion_data()` — stub for conversion-focused report (filter on conversion events)
- `get_landing_page_performance(self, date_range: DateRange) -> List[MetricPoint]` — helper that fetches sessions, conversions, bounce rate per landing page
- `get_traffic_sources(self, date_range: DateRange) -> List[MetricPoint]` — helper that fetches sessions, users, conversions per source/medium
- `get_user_demographics(self, date_range: DateRange) -> List[MetricPoint]` — helper for country, city, device breakdowns

### File: `kai/connectors/analytics/gsc.py`

**Class: GSCConnector(AnalyticsConnector)**
- `connector_type = "gsc"`
- Available metrics: `clicks`, `impressions`, `ctr`, `position`
- Available dimensions: `query`, `page`, `device`, `country`, `date`, `search_appearance`
- `get_metrics()` — stub for Search Console API `searchanalytics.query` method
- `get_events()` — returns empty list (GSC does not support event-level data)
- `get_real_time()` — returns empty list (GSC does not support real-time)
- `get_conversion_data()` — returns empty list (GSC has no conversion data)
- `get_top_queries(self, date_range: DateRange, limit: int = 50) -> List[MetricPoint]` — helper for top queries by clicks
- `get_top_pages(self, date_range: DateRange, limit: int = 50) -> List[MetricPoint]` — helper for top pages by clicks
- `get_position_changes(self, date_range: DateRange, comparison_range: DateRange) -> List[Dict]` — compare position for overlapping queries across two date ranges, return list of dicts with query, old_position, new_position, change

### File: `kai/connectors/analytics/call_tracking.py`

**Class: CallTrackingConnector(AnalyticsConnector)**
- `connector_type = "call_tracking"`
- Available metrics: `total_calls`, `missed_calls`, `answered_calls`, `first_time_callers`, `repeat_callers`, `average_call_duration_seconds`, `calls_to_conversion`, `call_answer_rate`
- Available dimensions: `date`, `tracking_number`, `source`, `campaign`, `landing_page`, `call_status`, `caller_type`
- `get_metrics()` — stub for generic call tracking API
- `get_events()` — stub for individual call event retrieval
- `get_real_time()` — stub for active/recent calls
- `get_conversion_data()` — stub for calls that resulted in conversions
- `get_missed_call_analysis(self, date_range: DateRange) -> Dict` — return dict with: total_missed, missed_by_hour (dict of hour -> count), missed_by_day_of_week, average_response_time_minutes, kaicalls_recommendation (bool, True if missed_call_rate > 0.15)
- `get_speed_to_lead(self, date_range: DateRange) -> Dict` — return dict with: average_seconds, median_seconds, p90_seconds, calls_under_60s_pct, calls_under_300s_pct
- `kaicalls_integration_check(self) -> Dict` — return dict with: is_integrated (bool), integration_type (str), recommendation (str explaining KaiCalls setup if not integrated)

### File: `kai/connectors/analytics/gbp.py`

**Class: GBPConnector(AnalyticsConnector)**
- `connector_type = "gbp"`
- Available metrics: `search_views`, `maps_views`, `direction_requests`, `phone_calls`, `website_clicks`, `photo_views`, `photo_count`, `review_count`, `review_rating`
- Available dimensions: `date`, `search_type`, `action_type`
- `get_metrics()` — stub for Google Business Profile Performance API
- `get_events()` — returns empty list (GBP does not support custom events)
- `get_real_time()` — returns empty list (GBP does not support real-time)
- `get_conversion_data()` — stub for actions (direction requests, phone calls, website clicks)
- `get_review_metrics(self, date_range: DateRange) -> Dict` — return dict with: total_reviews, average_rating, new_reviews_in_period, rating_distribution (dict of 1-5 -> count), unresponded_count
- `get_listing_health(self) -> Dict` — return dict with: is_verified, is_suspended, has_photos, photo_count, has_hours, has_description, has_categories, category_list, completeness_score (0-100)

### File: `kai/connectors/analytics/ad_metrics.py`

**Class: AdMetricsAggregator**
- Not a subclass of AnalyticsConnector — this is a wrapper/aggregator
- `__init__(self, connectors: Dict[str, Any])` — accepts dict of platform_name -> connector instance
- `get_unified_ad_metrics(self, date_range: DateRange) -> List[MetricPoint]` — pull metrics from all configured ad platform connectors into MetricPoint format
- `get_spend_summary(self, date_range: DateRange) -> Dict` — return dict with: total_spend, spend_by_platform (dict), spend_by_campaign (dict), daily_spend_trend (list)
- `get_roas_by_platform(self, date_range: DateRange) -> Dict` — return dict with per-platform ROAS
- `get_roas_by_campaign(self, date_range: DateRange) -> Dict` — return dict with per-campaign ROAS
- Metric normalization: map platform-specific metric names to canonical names (e.g., Google's "cost" and Meta's "spend" both become "ad_spend")
- Include a `METRIC_MAPPING` dict constant that maps: `{"google_ads": {"cost": "ad_spend", "clicks": "ad_clicks", ...}, "meta_ads": {"spend": "ad_spend", "link_clicks": "ad_clicks", ...}}`

## Output Files

- `kai/connectors/__init__.py`
- `kai/connectors/analytics/__init__.py`
- `kai/connectors/analytics/base.py`
- `kai/connectors/analytics/ga4.py`
- `kai/connectors/analytics/gsc.py`
- `kai/connectors/analytics/call_tracking.py`
- `kai/connectors/analytics/gbp.py`
- `kai/connectors/analytics/ad_metrics.py`

## Acceptance Criteria

- All files parse as valid Python (no syntax errors)
- `AnalyticsConnector` is a proper abstract base class with abstract methods
- All five concrete connectors implement every abstract method (even if stubbed)
- `MetricPoint` is a dataclass with `SerializableModel` mixin, matching the project pattern from `kai/runtime/models.py`
- Every stub method has a docstring explaining what real API it would call
- `CallTrackingConnector` includes the KaiCalls integration check and recommendation logic
- `AdMetricsAggregator` includes the `METRIC_MAPPING` constant for Google Ads and Meta Ads
- No external dependencies imported beyond stdlib and project-internal modules
- `__init__.py` files properly export all public classes

## Reference Materials

- `kai/runtime/models.py` — SerializableModel base class and dataclass patterns
- `kai/runtime/audit.py` — enum and dataclass conventions used across the project
- `kai/runtime/actions.py` — file structure conventions (helpers, models, logic)
- `gateway/routers/analytics.py` — existing analytics router patterns
- `knowledge/checklists/cro-audit-checklist.md` — CRO metrics context
- `knowledge/playbooks/conversion-rate-optimization.md` — KPI context for local service businesses
