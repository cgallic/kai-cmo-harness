# Task 072: Build watcher scheduling, throttling, and notification system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 12. Background Automation and Watcher Loops
**Priority:** P2
**Depends on:** 067
**Estimated complexity:** Medium

## Context

Individual watchers (Tasks 068-071) produce findings, but the operator experience depends on how those findings are packaged and delivered. Too many alerts cause fatigue and get ignored; too few mean problems go unnoticed. This module handles the scheduling cadence, per-watcher throttling rules, notification routing (which findings go to immediate alerts vs. daily digest vs. weekly rollup), digest compilation, and pre-configured watcher packs per business archetype. This is the "notification UX" layer that makes watchers useful instead of noisy.

## Scope

Create `kai/watchers/scheduling.py` containing WatcherSchedule configuration, ThrottleConfig per watcher, NotificationSystem for routing and digest building, and ArchetypeWatcherPacks for pre-configured watcher sets per archetype.

## Detailed Requirements

### File: `kai/watchers/scheduling.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: NotificationChannel**
- `in_app` — displayed in the operator dashboard
- `email` — sent via email to the operator
- `slack` — sent to a Slack channel (stub)
- `sms` — sent via SMS (stub)
- `webhook` — sent to a webhook URL (stub)

**Enum: DigestFrequency**
- `immediate` — send right away (for critical findings)
- `daily` — include in daily digest
- `weekly` — include in weekly rollup

**Model: WatcherSchedule**
- `watcher_name: str`
- `schedule_type: str` — "daily", "weekly", "hourly", "event_driven"
- `run_time: Optional[str]` — for daily: "06:00" (24h local time); for weekly: "monday_06:00"
- `timezone: str` — default "UTC"
- `last_run: Optional[str]` — ISO timestamp of last successful run
- `next_run: Optional[str]` — ISO timestamp of next scheduled run
- `consecutive_failures: int` — count of consecutive run failures (for backoff)
- `max_retries: int` — max retry attempts on failure (default 3)
- `backoff_minutes: int` — delay between retries (default 30)

**Model: ThrottleConfig**
- `watcher_name: str`
- `max_findings_per_day: int` — maximum findings surfaced per day to prevent alert fatigue (default 5)
- `suppression_window_days: int` — don't re-alert for same suppression_key within this window (default 7)
- `cooldown_after_action_days: int` — after action taken on a finding, suppress related findings (default 14)
- `max_findings_per_run: int` — cap per individual run (default 10)
- `priority_order: List[str]` — when throttled, which finding categories to keep: order of severity ("critical", "high", "medium", "low")
- `severity_minimum: str` — minimum severity to surface (default "low" — show everything)

**Model: NotificationPreference**
- `business_id: str`
- `operator_email: Optional[str]`
- `operator_phone: Optional[str]`
- `slack_channel: Optional[str]`
- `webhook_url: Optional[str]`
- `channels: List[str]` — enabled NotificationChannel values (default ["in_app"])
- `critical_channels: List[str]` — channels for critical/immediate alerts (default ["in_app", "email"])
- `digest_frequency: str` — DigestFrequency for non-critical findings (default "daily")
- `quiet_hours_start: Optional[str]` — "22:00" — don't send non-critical notifications during quiet hours
- `quiet_hours_end: Optional[str]` — "07:00"
- `weekly_digest_day: str` — day of week for weekly rollup (default "monday")
- `weekly_digest_time: str` — time for weekly rollup (default "09:00")

**Model: DigestEntry**
- `watcher_name: str`
- `finding_id: str`
- `title: str`
- `severity: str`
- `urgency: str`
- `category: str`
- `description: str` — shortened description (max 200 chars)
- `has_proposed_action: bool`
- `auto_eligible: bool`

**Model: Digest**
- `business_id: str`
- `business_name: str`
- `digest_type: str` — "daily" or "weekly"
- `period_start: str` — ISO date
- `period_end: str` — ISO date
- `generated_at: str` — ISO timestamp
- `total_findings: int`
- `critical_findings: int`
- `high_findings: int`
- `medium_findings: int`
- `low_findings: int`
- `entries: List[DigestEntry]`
- `suppressed_count: int` — how many findings were suppressed by throttling
- `top_priorities: List[str]` — top 3 things to address (human-readable)
- `overall_health_trend: str` — "improving", "stable", "declining" based on finding count trend
- `action_items: List[str]` — specific things the operator should do today/this week

**Class: NotificationSystem**
- `__init__(self)`
- `_pending_notifications: Dict[str, List[DigestEntry]]` — {business_id: [entries pending for digest]}
- `route_finding(self, finding: Any, preference: NotificationPreference) -> str`:
  - Determine where this finding should go based on urgency and preference:
    - urgency="immediate" → send via critical_channels immediately
    - urgency="soon" and severity in ("critical", "high") → send via critical_channels
    - urgency="soon" and severity in ("medium", "low") → add to daily digest
    - urgency="scheduled" → add to daily/weekly digest based on preference
    - urgency="informational" → add to weekly digest only
  - Return the routing decision: "immediate", "daily_digest", "weekly_digest"
  - Respect quiet hours: if in quiet hours, queue "immediate" non-critical for delivery at quiet_hours_end
- `add_to_digest(self, business_id: str, entry: DigestEntry)`:
  - Add entry to pending notifications for the business
- `build_daily_digest(self, business_id: str, business_name: str) -> Digest`:
  - Compile all pending entries for today into a Digest
  - Sort entries by severity (critical first)
  - Generate top_priorities from critical + high severity entries
  - Generate action_items (specific, actionable items)
  - Calculate overall_health_trend by comparing finding count to previous digest
  - Clear pending entries after building
- `build_weekly_digest(self, business_id: str, business_name: str, daily_digests: List[Digest]) -> Digest`:
  - Compile weekly rollup from daily digests + any weekly-only entries
  - Deduplicate entries that appeared in multiple daily digests
  - Generate weekly trend analysis
  - Include suppressed_count total
- `_format_for_channel(self, digest: Digest, channel: str) -> str`:
  - Format digest for the target notification channel
  - `in_app`: structured dict/JSON (for dashboard display)
  - `email`: formatted text with sections, counts, and action items
  - `slack`: Slack-formatted message with sections and links
  - Return formatted string
- `_is_in_quiet_hours(self, current_time: str, preference: NotificationPreference) -> bool`:
  - Check if current time falls within quiet_hours_start to quiet_hours_end
  - Handle overnight quiet hours (e.g., 22:00-07:00)

**Model: ArchetypeWatcherPack**
- `archetype: str`
- `watchers: List[str]` — list of watcher names to activate
- `description: str`
- `overrides: Dict[str, Dict[str, Any]]` — per-watcher config overrides for this archetype

**Function: get_local_service_watcher_pack() -> ArchetypeWatcherPack**
- Watchers: ["website_health", "local_visibility", "review_velocity", "speed_to_lead", "social_staleness", "followup_gaps", "content_freshness", "ad_fatigue", "spend_anomaly"]
- Description: "Comprehensive monitoring for local service businesses — website health, local visibility, reviews, lead response speed, and follow-up gaps"
- Overrides: speed_to_lead gets suppression_window_days=3 (more frequent for local service)

**Function: get_ecommerce_watcher_pack() -> ArchetypeWatcherPack**
- Watchers: ["website_health", "page_performance", "ad_fatigue", "spend_anomaly", "roas_monitor", "content_freshness", "social_staleness", "engagement_decline", "dormant_customers"]
- Description: "E-commerce monitoring — site performance, ad spend efficiency, customer retention, and content freshness"

**Function: get_professional_services_watcher_pack() -> ArchetypeWatcherPack**
- Watchers: ["website_health", "content_freshness", "engagement_decline", "speed_to_lead", "followup_gaps", "social_staleness"]
- Description: "Professional services monitoring — content freshness, engagement, lead response, and thought leadership"
- Overrides: content_freshness gets blog threshold of 6 months instead of 12

**Function: get_multi_location_watcher_pack() -> ArchetypeWatcherPack**
- Watchers: all local_service watchers applied per-location + ["brand_consistency"] (placeholder)
- Description: "Multi-location monitoring — all local service watchers per location plus brand consistency"
- Note: per-location application means each watcher runs once per location

**Function: get_watcher_pack_for_archetype(archetype: str) -> ArchetypeWatcherPack**
- Router function: given archetype string, return the right watcher pack
- Supported: "local_service", "ecommerce", "professional_services", "multi_location"
- Raise ValueError for unknown archetype

## Output Files

- `kai/watchers/scheduling.py`

## Acceptance Criteria

- File parses as valid Python
- NotificationSystem correctly routes findings based on urgency + severity + preference
- Quiet hours handling is correct for overnight ranges (e.g., 22:00-07:00)
- Daily digest is sorted by severity, includes top priorities and action items
- Weekly digest deduplicates findings from daily digests
- All four archetype watcher packs include appropriate watchers
- Local service pack includes speed_to_lead and review_velocity (business-critical for local)
- E-commerce pack includes roas_monitor and dormant_customers
- Professional services pack includes content_freshness with tighter thresholds
- Multi-location pack notes per-location watcher application
- ThrottleConfig priority_order correctly preserves highest-severity findings when throttled
- All models use SerializableModel mixin

## Reference Materials

- `kai/watchers/framework.py` (Task 067) — WatcherScheduler, SuppressionManager, WatcherFinding
- `kai/watchers/website_visibility.py` (Task 068) — website watchers
- `kai/watchers/social_freshness.py` (Task 069) — social watchers
- `kai/watchers/ad_spend.py` (Task 070) — ad watchers
- `kai/watchers/lead_followup.py` (Task 071) — lead/follow-up watchers
- `kai/runtime/models.py` — SerializableModel pattern
