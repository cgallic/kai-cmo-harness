# Task 068: Build website health and local visibility watchers

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 12. Background Automation and Watcher Loops
**Priority:** P2
**Depends on:** 067
**Estimated complexity:** Medium

## Context

A local service business's website and online presence are its digital storefront. If the website goes down, forms break, SSL expires, or the Google Business Profile gets suspended, leads stop flowing immediately. These watchers continuously monitor the fundamental health of the business's web presence and local visibility, catching issues before they become revenue-losing problems. These are the "first responder" watchers — the ones that detect when something critical breaks. They produce WatcherFinding objects that the watcher framework (Task 067) routes to operators or auto-resolution.

## Scope

Create `kai/watchers/website_visibility.py` containing three concrete watcher implementations: WebsiteHealthWatcher (daily), LocalVisibilityWatcher (weekly), and PagePerformanceWatcher (weekly).

## Detailed Requirements

### File: `kai/watchers/website_visibility.py`

Import and extend the `Watcher` abstract class from `kai/watchers/framework.py`. Import `WatcherFinding`, `WatcherConfig`, `FindingUrgency` from the same module. Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Class: WebsiteHealthWatcher(Watcher)**
- `name = "website_health"`
- `description = "Monitors website uptime, SSL, forms, tracking, and key page availability"`
- `schedule_type = "daily"`
- `archetype_relevance = []` — relevant for all archetypes
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Run all checks below, collect findings
  - Each check is a private method that returns Optional[WatcherFinding]
- `_check_site_uptime(self, url: str) -> Optional[WatcherFinding]`:
  - Stub: would perform HTTP HEAD request to the main URL
  - If non-200 response: return finding with urgency="immediate", severity="critical"
  - Finding title: "Website is down or returning errors"
  - Evidence: {url, status_code, response_time_ms}
  - Proposed action: alert operator immediately
- `_check_key_pages(self, url: str, key_pages: List[str]) -> List[WatcherFinding]`:
  - Stub: would check each key page (/, /about, /contact, /services, /reviews)
  - Return a finding for each page returning non-200
  - Severity: "high" for homepage/contact, "medium" for other pages
- `_check_ssl_certificate(self, url: str) -> Optional[WatcherFinding]`:
  - Stub: would check SSL certificate expiration date
  - If expiring within 30 days: severity="warning", urgency="soon"
  - If expiring within 7 days: severity="critical", urgency="immediate"
  - If expired: severity="critical", urgency="immediate"
  - Evidence: {domain, expiry_date, days_remaining}
- `_check_forms_working(self, url: str) -> Optional[WatcherFinding]`:
  - Stub: would check that form submission endpoints respond with 200
  - Evidence: {form_url, endpoint, status_code}
  - Proposed action: auto-eligible if fix is known (e.g., form handler URL changed)
- `_check_phone_number(self, url: str, expected_phone: str) -> Optional[WatcherFinding]`:
  - Stub: would scrape key pages for phone number and compare to expected
  - If phone number missing from homepage: severity="high"
  - If phone number doesn't match expected: severity="critical"
  - Evidence: {expected_phone, found_phone, pages_checked}
- `_check_tracking_scripts(self, url: str) -> Optional[WatcherFinding]`:
  - Stub: would check for presence of GA4, GTM, or other tracking scripts
  - If GA4 tracking missing: severity="high", title="Google Analytics tracking not detected"
  - Evidence: {scripts_expected, scripts_found, scripts_missing}
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="daily", schedule_time="06:00"
  - suppression_window_days=1 (re-alert daily for critical issues)
  - max_findings_per_run=20

**Class: LocalVisibilityWatcher(Watcher)**
- `name = "local_visibility"`
- `description = "Monitors Google Business Profile health, NAP consistency, and local search visibility"`
- `schedule_type = "weekly"`
- `archetype_relevance = ["local_service", "multi_location"]`
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Run all checks below
- `_check_gbp_status(self, business_profile) -> Optional[WatcherFinding]`:
  - Stub: would check GBP listing is active, verified, and not suspended
  - If suspended: severity="critical", urgency="immediate"
  - If not verified: severity="high", urgency="soon"
  - Evidence: {gbp_status, listing_url, last_verified}
- `_check_nap_consistency(self, business_profile) -> Optional[WatcherFinding]`:
  - Stub: would check NAP (Name, Address, Phone) across known citation sources
  - If inconsistencies found: severity="medium", urgency="scheduled"
  - Evidence: {inconsistent_sources (list), correct_nap, found_variations}
  - Proposed action: submit NAP corrections to inconsistent sources
- `_check_competitor_activity(self, business_profile) -> Optional[WatcherFinding]`:
  - Stub: would check for new competitor GBP listings in the service area
  - If new competitor detected: severity="low", urgency="informational"
  - Evidence: {new_competitor_name, location, distance_miles, category}
- `_check_local_ranking(self, business_profile) -> Optional[WatcherFinding]`:
  - Stub: would check local search ranking positions from GSC data
  - If significant ranking drops detected: severity="medium", urgency="soon"
  - Evidence: {queries_dropped, average_position_change, affected_pages}
- `_check_service_area_coverage(self, business_profile) -> Optional[WatcherFinding]`:
  - Stub: would check if the business appears in search results for target service areas
  - If gaps in coverage: severity="medium", urgency="scheduled"
  - Evidence: {target_areas, areas_covered, areas_missing}
  - Proposed action: create service area pages for missing areas
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="weekly", schedule_time="monday_06:00"
  - suppression_window_days=14
  - max_findings_per_run=15

**Class: PagePerformanceWatcher(Watcher)**
- `name = "page_performance"`
- `description = "Monitors Core Web Vitals, mobile usability, and page errors"`
- `schedule_type = "weekly"`
- `archetype_relevance = []` — relevant for all archetypes
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Run all checks below
- `_check_core_web_vitals(self, url: str) -> List[WatcherFinding]`:
  - Stub: would check LCP, FID/INP, CLS via CrUX API or PageSpeed Insights
  - Finding per metric that fails threshold:
    - LCP > 2.5s: severity="medium", title="Largest Contentful Paint exceeds threshold"
    - INP > 200ms: severity="medium", title="Interaction to Next Paint exceeds threshold"
    - CLS > 0.1: severity="medium", title="Cumulative Layout Shift exceeds threshold"
  - Evidence: {metric_name, current_value, threshold, percentile, page_url}
- `_check_mobile_usability(self, url: str) -> Optional[WatcherFinding]`:
  - Stub: would check for mobile usability issues via Search Console API
  - Evidence: {issues_found (list), pages_affected, issue_types}
- `_check_404_errors(self, business_profile) -> Optional[WatcherFinding]`:
  - Stub: would check GSC for pages returning 404 errors
  - If new 404s detected: severity="medium" (or "high" if important pages)
  - Evidence: {new_404_urls (list), total_404_count, high_traffic_404s}
  - Proposed action: set up 301 redirects for important pages
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="weekly", schedule_time="tuesday_06:00"
  - suppression_window_days=30 (CWV changes slowly)
  - max_findings_per_run=10

## Output Files

- `kai/watchers/website_visibility.py`

## Acceptance Criteria

- File parses as valid Python
- All three watcher classes properly extend the abstract `Watcher` base class
- Every `check()` method returns `List[WatcherFinding]` (never None)
- Every private check method returns `Optional[WatcherFinding]` or `List[WatcherFinding]`
- All findings have appropriate suppression_key values for dedup (e.g., "ssl_expiring_{domain}", "gbp_suspended_{business_id}")
- Severity and urgency levels are appropriate for each issue type
- WebsiteHealthWatcher is relevant for all archetypes (empty archetype_relevance)
- LocalVisibilityWatcher is only relevant for local_service and multi_location
- Each watcher's `get_default_config()` returns sensible defaults
- Evidence dicts include specific, actionable data (not placeholders)
- Proposed actions are included where auto-resolution is feasible
- All stub methods have docstrings explaining what real API/check they would perform

## Reference Materials

- `kai/watchers/framework.py` (Task 067) — Watcher base class, WatcherFinding, WatcherConfig
- `kai/runtime/audit.py` — FindingSeverity, AuditCategory
- `kai/connectors/analytics/gsc.py` (Task 056) — GSC data for ranking/404 checks
- `kai/connectors/analytics/gbp.py` (Task 056) — GBP data for listing health
- `knowledge/checklists/website-launch-checklist.md` — what to check on a website
- `knowledge/checklists/technical-seo-audit-sop.md` — technical SEO checks
