# Task 054: Build follow-up timing rules and deliverability controls

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 9. Lifecycle / CRM / Follow-Up Operations
**Priority:** P2
**Depends on:** 051
**Estimated complexity:** Medium

## Context

Email sequences fail silently when sent at the wrong time, too frequently, or to a list with deliverability problems. This module is the timing and deliverability control layer — it ensures emails go out during business hours in the recipient's timezone, enforces frequency caps to prevent over-contacting, manages domain warm-up schedules, handles bounces, monitors spam complaints, and maintains opt-out compliance. Without this layer, the lifecycle system would blast emails at 3 AM, send to hard-bounced addresses, and eventually get the sending domain blacklisted.

## Scope

Create `kai/lifecycle/timing.py` containing TimingRules, DeliverabilityControls, OptOutManager, and all supporting models and logic.

## Detailed Requirements

### File: `kai/lifecycle/timing.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: SendWindow (str, Enum)**
- `business_hours` — standard business hours (9 AM - 5 PM local time)
- `extended_hours` — extended hours (8 AM - 8 PM local time)
- `daytime` — daytime only (7 AM - 9 PM local time)
- `anytime` — no time restriction (for transactional emails)
- `custom` — custom hours defined in config

**Enum: BounceType (str, Enum)**
- `soft` — temporary delivery failure (mailbox full, server down, message too large)
- `hard` — permanent delivery failure (address doesn't exist, domain invalid)
- `block` — blocked by recipient server (blacklisted, policy rejection)
- `unknown` — bounce reason unclear

**Model: TimingRules**
- `send_window: str` — SendWindow value, default "business_hours"
- `custom_start_hour: int = 9` — start hour (0-23) for custom window
- `custom_end_hour: int = 17` — end hour (0-23) for custom window
- `timezone: str` — IANA timezone string, default "America/New_York"
- `respect_recipient_timezone: bool = True` — if True, send at optimal time in recipient's timezone
- `default_recipient_timezone: str = "America/New_York"` — fallback timezone if recipient's is unknown
- `send_on_weekends: bool = False` — whether to send on Saturday/Sunday
- `weekend_send_window: Optional[str]` — override window for weekends (e.g., "extended_hours")
- `min_gap_hours: int = 48` — minimum hours between emails to the same contact
- `max_emails_per_week: int = 3` — maximum emails per contact per week
- `max_emails_per_month: int = 10` — maximum emails per contact per month
- `suppress_holidays: bool = True` — skip sending on holidays
- `holiday_dates: List[str]` — ISO dates for holidays, default empty list
- `optimal_send_days: List[str]` — preferred days of week, default ["tuesday", "wednesday", "thursday"]
- `optimal_send_hours: List[int]` — preferred hours, default [9, 10, 14, 15] (9-10 AM and 2-3 PM)
- `archetype_overrides: Dict[str, Any]` — archetype-specific timing overrides, default empty dict

**Pre-built TIMING_PRESETS dict:**

```python
TIMING_PRESETS: Dict[str, TimingRules] = {
    "local_service": TimingRules(
        send_window="business_hours",
        send_on_weekends=False,
        min_gap_hours=48,
        max_emails_per_week=2,
        optimal_send_days=["tuesday", "wednesday", "thursday"],
        optimal_send_hours=[9, 10, 14],
    ),
    "ecommerce": TimingRules(
        send_window="extended_hours",
        send_on_weekends=True,
        weekend_send_window="daytime",
        min_gap_hours=24,
        max_emails_per_week=4,
        optimal_send_days=["tuesday", "thursday", "saturday"],
        optimal_send_hours=[10, 14, 19],
    ),
    "professional_services": TimingRules(
        send_window="business_hours",
        send_on_weekends=False,
        min_gap_hours=72,
        max_emails_per_week=2,
        optimal_send_days=["tuesday", "wednesday"],
        optimal_send_hours=[8, 9, 10],
    ),
    "transactional": TimingRules(
        send_window="anytime",
        send_on_weekends=True,
        min_gap_hours=0,
        max_emails_per_week=20,
        suppress_holidays=False,
    ),
}
```

**Model: SendTimeDecision**
- `original_send_time: str` — ISO timestamp originally requested
- `adjusted_send_time: str` — ISO timestamp after timing rules applied
- `was_adjusted: bool` — whether the time was changed
- `adjustment_reason: Optional[str]` — why it was adjusted (e.g., "Moved to next business day", "Shifted to optimal hour")
- `timezone_used: str` — which timezone was applied
- `is_within_window: bool` — whether the adjusted time is within the send window
- `warnings: List[str]` — any timing warnings, default empty list

**Model: WarmUpSchedule**
- `domain: str` — sending domain being warmed up
- `start_date: str` — ISO date warm-up started
- `current_day: int` — which day of the warm-up schedule
- `daily_limit: int` — maximum sends allowed today
- `total_sent_today: int = 0`
- `is_warm_up_complete: bool = False`
- `schedule: List[Dict[str, int]]` — list of {day: int, max_sends: int} defining the ramp-up. Default empty list.
- `notes: Optional[str]`

**Default warm-up schedule:**
```python
DEFAULT_WARMUP_SCHEDULE = [
    {"day": 1, "max_sends": 50},
    {"day": 2, "max_sends": 100},
    {"day": 3, "max_sends": 200},
    {"day": 4, "max_sends": 300},
    {"day": 5, "max_sends": 500},
    {"day": 6, "max_sends": 750},
    {"day": 7, "max_sends": 1000},
    {"day": 8, "max_sends": 1500},
    {"day": 9, "max_sends": 2000},
    {"day": 10, "max_sends": 3000},
    {"day": 11, "max_sends": 5000},
    {"day": 12, "max_sends": 7500},
    {"day": 13, "max_sends": 10000},
    {"day": 14, "max_sends": 15000},
    # Day 15+: warm-up complete, no limit
]
```

**Model: BounceRecord**
- `email: str`
- `bounce_type: str` — BounceType value
- `bounce_code: Optional[str]` — SMTP error code (e.g., "550", "452")
- `bounce_message: Optional[str]` — server response message
- `bounced_at: str` — ISO timestamp
- `retry_count: int = 0`
- `max_retries: int = 3` — for soft bounces
- `auto_unsubscribed: bool = False` — whether contact was auto-removed

**Model: SpamComplaintRecord**
- `email: str`
- `complaint_type: str` — "spam_button", "abuse_report", "feedback_loop"
- `reported_at: str` — ISO timestamp
- `message_id: Optional[str]` — which email triggered the complaint
- `auto_unsubscribed: bool = True` — complaints always auto-unsubscribe

**Model: DeliverabilityReport**
- `domain: str`
- `period: str` — time period (e.g., "last_7d", "last_30d")
- `total_sent: int = 0`
- `delivery_rate: float = 0.0`
- `open_rate: float = 0.0`
- `click_rate: float = 0.0`
- `bounce_rate: float = 0.0`
- `soft_bounce_rate: float = 0.0`
- `hard_bounce_rate: float = 0.0`
- `spam_complaint_rate: float = 0.0`
- `unsubscribe_rate: float = 0.0`
- `is_healthy: bool = True` — overall health assessment
- `issues: List[str]` — specific issues found, default empty list
- `recommendations: List[str]` — what to improve, default empty list
- `spf_configured: bool = False`
- `dkim_configured: bool = False`
- `dmarc_configured: bool = False`
- `generated_at: Optional[str]`

**Model: OptOutRecord**
- `email: str`
- `opt_out_type: str` — "global" (all emails), "list" (specific list), "type" (specific email type)
- `opt_out_scope: Optional[str]` — list ID or email type if type is "list" or "type"
- `opted_out_at: str` — ISO timestamp
- `source: str` — "unsubscribe_link", "reply_request", "manual", "spam_complaint", "api"
- `honored_at: Optional[str]` — when the opt-out was processed (should be within 24h)

**Class: TimingEngine**

Determines optimal send times and enforces timing rules.

Methods:
- `__init__(self, rules: Optional[TimingRules] = None, archetype: Optional[str] = None)` — initialize with rules. If archetype provided and no rules, load from TIMING_PRESETS.

- `calculate_send_time(self, requested_time: str, recipient_timezone: Optional[str] = None) -> SendTimeDecision`:
  1. Parse requested_time
  2. Determine timezone: use recipient_timezone if provided and respect_recipient_timezone is True, else use rules.timezone
  3. Convert to local time
  4. Check if within send_window. If not, find next valid window:
     - If before window start: move to window start
     - If after window end: move to next day's window start
     - If weekend and send_on_weekends is False: move to next Monday
     - If holiday and suppress_holidays is True: move to next non-holiday
  5. Prefer optimal_send_hours if moving anyway
  6. Return SendTimeDecision with adjustment details

- `check_frequency(self, email: str, send_history: List[Dict[str, Any]]) -> Dict[str, Any]`:
  - Check if sending to this email would violate frequency caps
  - Count emails in last 7 days and last 30 days from send_history
  - Return: `{"can_send": bool, "emails_this_week": int, "emails_this_month": int, "next_eligible": Optional[str], "reason": Optional[str]}`
  - If can't send: next_eligible is the ISO timestamp when they become eligible

- `suggest_optimal_time(self, date: str, recipient_timezone: Optional[str] = None) -> str`:
  - Given a date, suggest the best send time based on optimal_send_hours and send_window
  - Return ISO timestamp

- `is_within_send_window(self, timestamp: str) -> bool`:
  - Check if a timestamp falls within the configured send window
  - Account for timezone

- `get_next_window_start(self, from_time: str) -> str`:
  - Given a time, find the next valid send window start
  - Skip weekends if send_on_weekends is False
  - Skip holidays if suppress_holidays is True
  - Return ISO timestamp

**US_HOLIDAYS list (for 2026-2027):**
```python
US_HOLIDAYS = [
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Day
    "2026-02-16",  # Presidents Day
    "2026-05-25",  # Memorial Day
    "2026-07-04",  # Independence Day (observed July 3)
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-11-27",  # Black Friday
    "2026-12-24",  # Christmas Eve
    "2026-12-25",  # Christmas Day
    "2026-12-31",  # New Year's Eve
    "2027-01-01",  # New Year's Day
    # ... extend as needed
]
```

**Class: DeliverabilityController**

Monitors and manages email deliverability.

Methods:
- `__init__(self, alert_bounce_rate: float = 0.05, alert_spam_rate: float = 0.001, pause_spam_rate: float = 0.003)` — set thresholds

- `process_bounce(self, bounce: BounceRecord) -> Dict[str, Any]`:
  - Handle bounce based on type:
    - Soft bounce: increment retry_count, schedule retry if under max_retries
    - Hard bounce: auto-unsubscribe, add to suppression
    - Block: investigate, add to suppression after 2 occurrences
  - Return: `{"action": str, "auto_unsubscribed": bool, "retry_scheduled": bool, "message": str}`

- `process_spam_complaint(self, complaint: SpamComplaintRecord) -> Dict[str, Any]`:
  - Always auto-unsubscribe on spam complaint
  - Log the complaint
  - Return: `{"action": "auto_unsubscribed", "complaint_rate": float, "alert": bool, "message": str}`

- `check_list_hygiene(self, contacts: List[Dict[str, Any]]) -> Dict[str, Any]`:
  - Analyze a contact list for hygiene issues:
    - Contacts with no opens in 90 days: flag for re-engagement or removal
    - Contacts with hard bounces: flag for removal
    - Contacts with spam complaints: flag as suppressed
    - Duplicate emails: flag for dedup
    - Invalid email formats: flag for review
  - Return: `{"total": int, "clean": int, "inactive_90d": int, "bounced": int, "complained": int, "duplicates": int, "invalid": int, "recommendations": list}`

- `generate_deliverability_report(self, stats: Dict[str, Any]) -> DeliverabilityReport`:
  - Compile deliverability metrics into a report
  - Assess health:
    - Bounce rate > 5%: unhealthy, recommend list cleaning
    - Spam complaint rate > 0.1%: warning, review content and targeting
    - Spam complaint rate > 0.3%: critical, auto-pause sending
    - Open rate < 10%: warning, review subject lines and send timing
  - Check SPF/DKIM/DMARC status
  - Generate specific recommendations

- `get_warmup_limit(self, warmup_schedule: WarmUpSchedule) -> int`:
  - Given current day in warm-up, return max sends allowed
  - Look up in schedule, return the limit for the current day
  - If beyond schedule: warm-up complete, return -1 (no limit)

- `check_authentication(self) -> Dict[str, Any]`:
  - Return authentication setup status (to be populated by checking DNS records in production):
    - `{"spf": {"configured": bool, "record": Optional[str]}, "dkim": {"configured": bool, "record": Optional[str]}, "dmarc": {"configured": bool, "record": Optional[str]}, "recommendations": list}`
  - In stub mode: return all as unchecked with recommendation to verify

**Class: OptOutManager**

Manages opt-out/unsubscribe compliance.

Methods:
- `__init__(self, honor_within_hours: int = 24)` — better than the legal 10-day requirement

- `process_opt_out(self, email: str, opt_out_type: str = "global", source: str = "unsubscribe_link", scope: Optional[str] = None) -> OptOutRecord`:
  - Record the opt-out
  - Set honored_at to now (immediate processing)
  - Add to suppression list
  - Return OptOutRecord

- `check_can_send(self, email: str, email_type: str = "marketing") -> Dict[str, Any]`:
  - Check if an email can be sent to this address:
    - If globally opted out: cannot send any marketing, CAN send transactional
    - If list-opted-out: cannot send to that list, can send to others
    - If consent_status is "transactional_only": can send transactional, not marketing
    - If consent_status is "unknown": treat as opted out for marketing
  - Return: `{"can_send": bool, "reason": Optional[str], "email_types_allowed": list}`
  - email_types_allowed possibilities: ["marketing", "transactional"], ["transactional"], []

- `get_suppression_list(self) -> List[OptOutRecord]`:
  - Return all active opt-out records

- `is_suppressed(self, email: str) -> bool`:
  - Quick check if email is on suppression list

- `process_re_opt_in(self, email: str, source: str = "explicit_consent") -> Dict[str, Any]`:
  - Handle re-subscription
  - Only allow re-opt-in with explicit consent
  - Record the re-opt-in with source
  - Return: `{"success": bool, "message": str, "previous_opt_out": Optional[OptOutRecord]}`

- `export_suppression_list(self) -> List[Dict[str, str]]`:
  - Export suppression list in a standard format: [{"email": str, "reason": str, "date": str}]
  - For compliance record-keeping

Internal state:
- `_suppression_list: Dict[str, OptOutRecord]` — email -> OptOutRecord
- `_honor_within_hours: int`

**Helper functions (module-level):**

- `is_business_hours(timestamp: str, timezone: str = "America/New_York") -> bool` — check if timestamp is 9 AM - 5 PM in the given timezone
- `get_timezone_offset(timezone: str) -> int` — return UTC offset in hours for the timezone (simplified mapping for common US timezones)
- `is_holiday(date_str: str, holiday_list: Optional[List[str]] = None) -> bool` — check if date is a holiday
- `is_weekend(date_str: str) -> bool` — check if date is Saturday or Sunday
- `next_business_day(date_str: str) -> str` — return the next business day (skip weekends and holidays)
- `validate_email_format(email: str) -> bool` — basic email format validation (contains @, has domain, etc.)
- `calculate_engagement_score(open_rate: float, click_rate: float, bounce_rate: float, spam_rate: float) -> float` — composite deliverability health score (0-100)

## Output Files

- `kai/lifecycle/timing.py`
- `kai/lifecycle/__init__.py` (update to include timing exports)

## Acceptance Criteria

- [ ] `SendWindow` enum has all 5 values
- [ ] `BounceType` enum has all 4 values
- [ ] `TimingRules` model has all 16 fields with correct defaults
- [ ] `TIMING_PRESETS` has entries for local_service, ecommerce, professional_services, and transactional
- [ ] `SendTimeDecision` model has all 7 fields
- [ ] `WarmUpSchedule` model has all 8 fields
- [ ] `DEFAULT_WARMUP_SCHEDULE` has a 14-day ramp from 50 to 15000 sends/day
- [ ] `BounceRecord` and `SpamComplaintRecord` models exist with correct fields
- [ ] `DeliverabilityReport` model has all 17 fields including SPF/DKIM/DMARC status
- [ ] `OptOutRecord` model has all 6 fields
- [ ] `TimingEngine.calculate_send_time()` correctly adjusts for send windows, weekends, holidays, and timezones
- [ ] `TimingEngine.check_frequency()` enforces weekly and monthly caps
- [ ] `DeliverabilityController.process_bounce()` handles soft, hard, and block bounces differently
- [ ] `DeliverabilityController.process_spam_complaint()` always auto-unsubscribes
- [ ] `DeliverabilityController.check_list_hygiene()` identifies inactive, bounced, complained, duplicate, and invalid contacts
- [ ] `DeliverabilityController` pauses sending at 0.3% spam complaint rate
- [ ] `OptOutManager.process_opt_out()` honors within 24 hours (better than legal 10-day requirement)
- [ ] `OptOutManager.check_can_send()` distinguishes between marketing and transactional eligibility
- [ ] `OptOutManager.process_re_opt_in()` requires explicit consent
- [ ] `US_HOLIDAYS` list has at least 11 entries for 2026
- [ ] All 7 helper functions exist with correct signatures
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/actions/lifecycle.py` (created by Task 051) — LifecycleAction types that rely on timing
- `kai/connectors/lifecycle/base.py` (created by Task 050) — LifecycleConnector compliance methods
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `harness/references/cold-email-rules.md` — CAN-SPAM, deliverability rules
- `harness/references/advertising-compliance.md` — CAN-SPAM opt-out requirements (10-day rule we beat with 24-hour)
- `knowledge/channels/email-lifecycle.md` — email lifecycle guidance
- `knowledge/playbooks/marketing-automation.md` — automation timing best practices
- `CLAUDE.md` — full project context
