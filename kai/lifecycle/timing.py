"""Follow-up timing rules and deliverability controls.

Ensures emails go out during business hours in the recipient's timezone,
enforces frequency caps, manages domain warm-up schedules, handles bounces,
monitors spam complaints, and maintains opt-out compliance.
"""

from __future__ import annotations

import copy
import re
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Enums
# ============================================================================


class SendWindow(str, Enum):
    """Allowed send-window values."""

    business_hours = "business_hours"
    extended_hours = "extended_hours"
    daytime = "daytime"
    anytime = "anytime"
    custom = "custom"


class BounceType(str, Enum):
    """Bounce classification."""

    soft = "soft"
    hard = "hard"
    block = "block"
    unknown = "unknown"


# ============================================================================
# Constants
# ============================================================================

# Mapping of SendWindow -> (start_hour, end_hour)
SEND_WINDOW_HOURS: Dict[str, tuple] = {
    "business_hours": (9, 17),
    "extended_hours": (8, 20),
    "daytime": (7, 21),
    "anytime": (0, 24),
}

# Simplified UTC offset mapping for common US timezones
TIMEZONE_UTC_OFFSETS: Dict[str, int] = {
    "America/New_York": -5,
    "America/Chicago": -6,
    "America/Denver": -7,
    "America/Los_Angeles": -8,
    "America/Phoenix": -7,
    "America/Anchorage": -9,
    "Pacific/Honolulu": -10,
    "America/Detroit": -5,
    "America/Indiana/Indianapolis": -5,
    "America/Boise": -7,
    "US/Eastern": -5,
    "US/Central": -6,
    "US/Mountain": -7,
    "US/Pacific": -8,
    "UTC": 0,
    "Europe/London": 0,
    "Europe/Berlin": 1,
    "Europe/Paris": 1,
    "Asia/Tokyo": 9,
    "Asia/Shanghai": 8,
    "Australia/Sydney": 11,
}

US_HOLIDAYS: List[str] = [
    "2026-01-01",  # New Year's Day
    "2026-01-19",  # MLK Day
    "2026-02-16",  # Presidents Day
    "2026-05-25",  # Memorial Day
    "2026-07-04",  # Independence Day
    "2026-09-07",  # Labor Day
    "2026-11-26",  # Thanksgiving
    "2026-11-27",  # Black Friday
    "2026-12-24",  # Christmas Eve
    "2026-12-25",  # Christmas Day
    "2026-12-31",  # New Year's Eve
    "2027-01-01",  # New Year's Day
    "2027-01-18",  # MLK Day
    "2027-02-15",  # Presidents Day
    "2027-05-31",  # Memorial Day
    "2027-07-04",  # Independence Day (observed July 5)
    "2027-07-05",  # Independence Day observed
    "2027-09-06",  # Labor Day
    "2027-11-25",  # Thanksgiving
    "2027-11-26",  # Black Friday
    "2027-12-24",  # Christmas Eve
    "2027-12-25",  # Christmas Day
    "2027-12-31",  # New Year's Eve
]

DEFAULT_WARMUP_SCHEDULE: List[Dict[str, int]] = [
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


# ============================================================================
# Models
# ============================================================================


class TimingRules(BaseModel):
    """Configurable timing rules for email sending."""

    send_window: str = "business_hours"
    custom_start_hour: int = 9
    custom_end_hour: int = 17
    timezone: str = "America/New_York"
    respect_recipient_timezone: bool = True
    default_recipient_timezone: str = "America/New_York"
    send_on_weekends: bool = False
    weekend_send_window: Optional[str] = None
    min_gap_hours: int = 48
    max_emails_per_week: int = 3
    max_emails_per_month: int = 10
    suppress_holidays: bool = True
    holiday_dates: List[str] = Field(default_factory=list)
    optimal_send_days: List[str] = Field(
        default_factory=lambda: ["tuesday", "wednesday", "thursday"]
    )
    optimal_send_hours: List[int] = Field(
        default_factory=lambda: [9, 10, 14, 15]
    )
    archetype_overrides: Dict[str, Any] = Field(default_factory=dict)


class SendTimeDecision(BaseModel):
    """Result of calculating the optimal send time."""

    original_send_time: str
    adjusted_send_time: str
    was_adjusted: bool
    adjustment_reason: Optional[str] = None
    timezone_used: str = "America/New_York"
    is_within_window: bool = True
    warnings: List[str] = Field(default_factory=list)


class WarmUpSchedule(BaseModel):
    """Domain warm-up tracking."""

    domain: str
    start_date: str
    current_day: int
    daily_limit: int
    total_sent_today: int = 0
    is_warm_up_complete: bool = False
    schedule: List[Dict[str, int]] = Field(default_factory=list)
    notes: Optional[str] = None


class BounceRecord(BaseModel):
    """Record of an email bounce event."""

    email: str
    bounce_type: str
    bounce_code: Optional[str] = None
    bounce_message: Optional[str] = None
    bounced_at: str
    retry_count: int = 0
    max_retries: int = 3
    auto_unsubscribed: bool = False


class SpamComplaintRecord(BaseModel):
    """Record of a spam complaint."""

    email: str
    complaint_type: str
    reported_at: str
    message_id: Optional[str] = None
    auto_unsubscribed: bool = True


class DeliverabilityReport(BaseModel):
    """Comprehensive deliverability health report for a sending domain."""

    domain: str
    period: str
    total_sent: int = 0
    delivery_rate: float = 0.0
    open_rate: float = 0.0
    click_rate: float = 0.0
    bounce_rate: float = 0.0
    soft_bounce_rate: float = 0.0
    hard_bounce_rate: float = 0.0
    spam_complaint_rate: float = 0.0
    unsubscribe_rate: float = 0.0
    is_healthy: bool = True
    issues: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    spf_configured: bool = False
    dkim_configured: bool = False
    dmarc_configured: bool = False
    generated_at: Optional[str] = None


class OptOutRecord(BaseModel):
    """Record of a contact's opt-out / unsubscribe event."""

    email: str
    opt_out_type: str
    opt_out_scope: Optional[str] = None
    opted_out_at: str
    source: str
    honored_at: Optional[str] = None


# ============================================================================
# Timing Presets
# ============================================================================

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
        max_emails_per_month=100,
        suppress_holidays=False,
    ),
}


# ============================================================================
# Module-Level Helper Functions
# ============================================================================


def _parse_iso(timestamp: str) -> datetime:
    """Parse an ISO-format timestamp string into a datetime object.

    Handles both ``YYYY-MM-DDTHH:MM:SS`` and ``YYYY-MM-DD`` formats.
    """
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(timestamp, fmt)
        except ValueError:
            continue
    # Strip timezone suffix (e.g. +00:00 / Z) and retry
    clean = re.sub(r"[+-]\d{2}:\d{2}$", "", timestamp).replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%d"):
        try:
            return datetime.strptime(clean, fmt)
        except ValueError:
            continue
    raise ValueError(f"Unable to parse timestamp: {timestamp}")


def is_business_hours(timestamp: str, timezone: str = "America/New_York") -> bool:
    """Return True if *timestamp* falls within 9 AM - 5 PM in *timezone*."""
    dt = _parse_iso(timestamp)
    offset = get_timezone_offset(timezone)
    local_hour = (dt.hour + offset) % 24
    return 9 <= local_hour < 17


def get_timezone_offset(timezone: str) -> int:
    """Return the UTC offset in hours for a timezone (simplified mapping)."""
    return TIMEZONE_UTC_OFFSETS.get(timezone, 0)


def is_holiday(date_str: str, holiday_list: Optional[List[str]] = None) -> bool:
    """Return True if *date_str* (YYYY-MM-DD or ISO timestamp) is a holiday."""
    day_part = date_str[:10]
    holidays = holiday_list if holiday_list is not None else US_HOLIDAYS
    return day_part in holidays


def is_weekend(date_str: str) -> bool:
    """Return True if *date_str* falls on a Saturday or Sunday."""
    dt = _parse_iso(date_str)
    return dt.weekday() >= 5  # 5 = Saturday, 6 = Sunday


def next_business_day(date_str: str) -> str:
    """Return the next business day (skipping weekends and US holidays) as YYYY-MM-DD."""
    dt = _parse_iso(date_str)
    candidate = dt + timedelta(days=1)
    while True:
        candidate_str = candidate.strftime("%Y-%m-%d")
        if candidate.weekday() < 5 and not is_holiday(candidate_str):
            return candidate_str
        candidate += timedelta(days=1)


def validate_email_format(email: str) -> bool:
    """Basic email format validation (contains @, has domain with dot)."""
    if not email or not isinstance(email, str):
        return False
    pattern = r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$"
    return bool(re.match(pattern, email))


def calculate_engagement_score(
    open_rate: float,
    click_rate: float,
    bounce_rate: float,
    spam_rate: float,
) -> float:
    """Compute a composite deliverability health score from 0 to 100.

    Weights:
    - Open rate contributes positively  (30% weight, normalised to a 50% ceiling)
    - Click rate contributes positively (20% weight, normalised to a 10% ceiling)
    - Bounce rate penalises             (25% weight, normalised to a 10% ceiling)
    - Spam rate penalises heavily       (25% weight, normalised to a 1% ceiling)
    """
    open_score = min(open_rate / 0.50, 1.0) * 30.0
    click_score = min(click_rate / 0.10, 1.0) * 20.0
    bounce_penalty = min(bounce_rate / 0.10, 1.0) * 25.0
    spam_penalty = min(spam_rate / 0.01, 1.0) * 25.0

    raw = open_score + click_score - bounce_penalty - spam_penalty
    # Shift so that 50/50 positive input yields 50.  Clamp to 0-100.
    score = max(0.0, min(100.0, raw + 50.0))
    return round(score, 1)


# ============================================================================
# TimingEngine
# ============================================================================


class TimingEngine:
    """Determines optimal send times and enforces timing rules."""

    def __init__(
        self,
        rules: Optional[TimingRules] = None,
        archetype: Optional[str] = None,
    ) -> None:
        if rules is not None:
            self.rules = rules
        elif archetype and archetype in TIMING_PRESETS:
            self.rules = TIMING_PRESETS[archetype]
        else:
            self.rules = TimingRules()

    # ----- internal helpers ------------------------------------------------

    def _get_window_hours(self, window: Optional[str] = None) -> tuple:
        """Return (start_hour, end_hour) for the given or default window."""
        win = window or self.rules.send_window
        if win == "custom":
            return (self.rules.custom_start_hour, self.rules.custom_end_hour)
        return SEND_WINDOW_HOURS.get(win, (9, 17))

    def _apply_offset(self, dt: datetime, tz: str) -> datetime:
        """Shift *dt* by the UTC offset of *tz*."""
        offset = get_timezone_offset(tz)
        return dt + timedelta(hours=offset)

    def _resolve_timezone(self, recipient_timezone: Optional[str]) -> str:
        if (
            recipient_timezone
            and self.rules.respect_recipient_timezone
        ):
            return recipient_timezone
        return self.rules.timezone

    # ----- public API ------------------------------------------------------

    def calculate_send_time(
        self,
        requested_time: str,
        recipient_timezone: Optional[str] = None,
    ) -> SendTimeDecision:
        """Calculate the best send time given timing rules and timezone.

        Returns a :class:`SendTimeDecision` with adjustment details.
        """
        dt = _parse_iso(requested_time)
        tz = self._resolve_timezone(recipient_timezone)
        offset = get_timezone_offset(tz)
        local_dt = dt + timedelta(hours=offset)

        original_iso = dt.strftime("%Y-%m-%dT%H:%M:%S")
        adjusted_dt = local_dt
        was_adjusted = False
        reasons: List[str] = []
        warnings: List[str] = []

        # Determine applicable window
        is_wknd = adjusted_dt.weekday() >= 5
        if is_wknd and self.rules.weekend_send_window:
            start_h, end_h = self._get_window_hours(self.rules.weekend_send_window)
        else:
            start_h, end_h = self._get_window_hours()

        # Check weekends
        if is_wknd and not self.rules.send_on_weekends:
            # Move to next Monday
            days_ahead = 7 - adjusted_dt.weekday()  # Monday
            adjusted_dt = adjusted_dt.replace(hour=start_h, minute=0, second=0) + timedelta(days=days_ahead)
            was_adjusted = True
            reasons.append("Moved to next Monday (no weekend sends)")

        # Check holidays
        date_part = adjusted_dt.strftime("%Y-%m-%d")
        all_holidays = self.rules.holiday_dates or US_HOLIDAYS
        if self.rules.suppress_holidays and is_holiday(date_part, all_holidays):
            while is_holiday(adjusted_dt.strftime("%Y-%m-%d"), all_holidays) or adjusted_dt.weekday() >= 5:
                adjusted_dt += timedelta(days=1)
            adjusted_dt = adjusted_dt.replace(hour=start_h, minute=0, second=0)
            was_adjusted = True
            reasons.append("Moved past holiday")

        # Refresh window in case date changed
        is_wknd = adjusted_dt.weekday() >= 5
        if is_wknd and self.rules.weekend_send_window:
            start_h, end_h = self._get_window_hours(self.rules.weekend_send_window)
        else:
            start_h, end_h = self._get_window_hours()

        # Check send window
        current_hour = adjusted_dt.hour
        if end_h <= 24 and (current_hour < start_h or current_hour >= end_h):
            if current_hour < start_h:
                adjusted_dt = adjusted_dt.replace(hour=start_h, minute=0, second=0)
                reasons.append(f"Shifted to window start ({start_h}:00)")
            else:
                # After window end -- move to next day
                adjusted_dt = adjusted_dt + timedelta(days=1)
                adjusted_dt = adjusted_dt.replace(hour=start_h, minute=0, second=0)
                reasons.append("Moved to next day window start")
                # Re-check weekend/holiday for the new day
                if adjusted_dt.weekday() >= 5 and not self.rules.send_on_weekends:
                    days_ahead = 7 - adjusted_dt.weekday()
                    adjusted_dt += timedelta(days=days_ahead)
                    reasons.append("Skipped weekend after shift")
            was_adjusted = True

        # Prefer optimal hours when already adjusting
        if was_adjusted and self.rules.optimal_send_hours:
            # Pick the earliest optimal hour that is within the window
            for oh in sorted(self.rules.optimal_send_hours):
                if start_h <= oh < end_h:
                    adjusted_dt = adjusted_dt.replace(hour=oh, minute=0, second=0)
                    break

        # Convert back to UTC for output
        adjusted_utc = adjusted_dt - timedelta(hours=offset)
        adjusted_iso = adjusted_utc.strftime("%Y-%m-%dT%H:%M:%S")

        # Within-window check on final time
        final_local = adjusted_utc + timedelta(hours=offset)
        final_hour = final_local.hour
        in_window = start_h <= final_hour < end_h if end_h <= 24 else True

        if not in_window:
            warnings.append(f"Adjusted time {adjusted_iso} is still outside the send window")

        return SendTimeDecision(
            original_send_time=original_iso,
            adjusted_send_time=adjusted_iso,
            was_adjusted=was_adjusted,
            adjustment_reason="; ".join(reasons) if reasons else None,
            timezone_used=tz,
            is_within_window=in_window,
            warnings=warnings,
        )

    def check_frequency(
        self,
        email: str,
        send_history: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Check whether sending to *email* would violate frequency caps.

        *send_history* is a list of dicts with at least a ``"sent_at"`` key
        (ISO timestamp) representing previous sends to this contact.

        Returns a dict with ``can_send``, ``emails_this_week``,
        ``emails_this_month``, ``next_eligible``, and ``reason``.
        """
        now = datetime.utcnow()
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        emails_this_week = 0
        emails_this_month = 0
        most_recent: Optional[datetime] = None

        for entry in send_history:
            sent_at = _parse_iso(entry.get("sent_at", ""))
            if sent_at >= week_ago:
                emails_this_week += 1
            if sent_at >= month_ago:
                emails_this_month += 1
            if most_recent is None or sent_at > most_recent:
                most_recent = sent_at

        # Check min_gap_hours
        if most_recent is not None:
            hours_since_last = (now - most_recent).total_seconds() / 3600
            if hours_since_last < self.rules.min_gap_hours:
                next_eligible = most_recent + timedelta(hours=self.rules.min_gap_hours)
                return {
                    "can_send": False,
                    "emails_this_week": emails_this_week,
                    "emails_this_month": emails_this_month,
                    "next_eligible": next_eligible.strftime("%Y-%m-%dT%H:%M:%S"),
                    "reason": (
                        f"Minimum gap of {self.rules.min_gap_hours}h not met. "
                        f"Last email was {hours_since_last:.1f}h ago."
                    ),
                }

        # Check weekly cap
        if emails_this_week >= self.rules.max_emails_per_week:
            next_eligible = week_ago + timedelta(days=7)
            return {
                "can_send": False,
                "emails_this_week": emails_this_week,
                "emails_this_month": emails_this_month,
                "next_eligible": next_eligible.strftime("%Y-%m-%dT%H:%M:%S"),
                "reason": (
                    f"Weekly cap reached ({emails_this_week}/{self.rules.max_emails_per_week})."
                ),
            }

        # Check monthly cap
        if emails_this_month >= self.rules.max_emails_per_month:
            next_eligible = month_ago + timedelta(days=30)
            return {
                "can_send": False,
                "emails_this_week": emails_this_week,
                "emails_this_month": emails_this_month,
                "next_eligible": next_eligible.strftime("%Y-%m-%dT%H:%M:%S"),
                "reason": (
                    f"Monthly cap reached ({emails_this_month}/{self.rules.max_emails_per_month})."
                ),
            }

        return {
            "can_send": True,
            "emails_this_week": emails_this_week,
            "emails_this_month": emails_this_month,
            "next_eligible": None,
            "reason": None,
        }

    def suggest_optimal_time(
        self,
        date: str,
        recipient_timezone: Optional[str] = None,
    ) -> str:
        """Given a date, suggest the best send time (ISO timestamp in UTC).

        Picks the first optimal hour that falls within the send window.
        """
        dt = _parse_iso(date)
        tz = self._resolve_timezone(recipient_timezone)
        offset = get_timezone_offset(tz)

        start_h, end_h = self._get_window_hours()
        chosen_hour = start_h  # fallback

        for oh in sorted(self.rules.optimal_send_hours):
            if start_h <= oh < end_h:
                chosen_hour = oh
                break

        local_dt = dt.replace(hour=chosen_hour, minute=0, second=0)
        utc_dt = local_dt - timedelta(hours=offset)
        return utc_dt.strftime("%Y-%m-%dT%H:%M:%S")

    def is_within_send_window(self, timestamp: str) -> bool:
        """Check if *timestamp* falls within the configured send window."""
        dt = _parse_iso(timestamp)
        offset = get_timezone_offset(self.rules.timezone)
        local_dt = dt + timedelta(hours=offset)

        is_wknd = local_dt.weekday() >= 5
        if is_wknd and self.rules.weekend_send_window:
            start_h, end_h = self._get_window_hours(self.rules.weekend_send_window)
        else:
            start_h, end_h = self._get_window_hours()

        # anytime window -> always valid
        if start_h == 0 and end_h == 24:
            return True

        return start_h <= local_dt.hour < end_h

    def get_next_window_start(self, from_time: str) -> str:
        """Find the next valid send-window start from *from_time* (returns ISO UTC)."""
        dt = _parse_iso(from_time)
        offset = get_timezone_offset(self.rules.timezone)
        local_dt = dt + timedelta(hours=offset)

        start_h, end_h = self._get_window_hours()

        # Move to next day's window start
        candidate = (local_dt + timedelta(days=1)).replace(
            hour=start_h, minute=0, second=0, microsecond=0
        )

        # Skip weekends if needed
        while True:
            if candidate.weekday() >= 5 and not self.rules.send_on_weekends:
                candidate += timedelta(days=1)
                continue
            date_part = candidate.strftime("%Y-%m-%d")
            all_holidays = self.rules.holiday_dates or US_HOLIDAYS
            if self.rules.suppress_holidays and is_holiday(date_part, all_holidays):
                candidate += timedelta(days=1)
                continue
            break

        utc_candidate = candidate - timedelta(hours=offset)
        return utc_candidate.strftime("%Y-%m-%dT%H:%M:%S")


# ============================================================================
# DeliverabilityController
# ============================================================================


class DeliverabilityController:
    """Monitors and manages email deliverability health."""

    def __init__(
        self,
        alert_bounce_rate: float = 0.05,
        alert_spam_rate: float = 0.001,
        pause_spam_rate: float = 0.003,
    ) -> None:
        self.alert_bounce_rate = alert_bounce_rate
        self.alert_spam_rate = alert_spam_rate
        self.pause_spam_rate = pause_spam_rate
        self._bounce_history: List[BounceRecord] = []
        self._spam_complaints: List[SpamComplaintRecord] = []
        self._suppression: Dict[str, str] = {}  # email -> reason

    def process_bounce(self, bounce: BounceRecord) -> Dict[str, Any]:
        """Handle a bounce event.  Returns action taken and status."""
        self._bounce_history.append(bounce)

        if bounce.bounce_type == BounceType.hard.value or bounce.bounce_type == "hard":
            bounce.auto_unsubscribed = True
            self._suppression[bounce.email] = "hard_bounce"
            return {
                "action": "auto_unsubscribed",
                "auto_unsubscribed": True,
                "retry_scheduled": False,
                "message": (
                    f"Hard bounce for {bounce.email}. Address permanently invalid. "
                    "Auto-unsubscribed and added to suppression list."
                ),
            }

        if bounce.bounce_type == BounceType.soft.value or bounce.bounce_type == "soft":
            if bounce.retry_count < bounce.max_retries:
                bounce.retry_count += 1
                return {
                    "action": "retry_scheduled",
                    "auto_unsubscribed": False,
                    "retry_scheduled": True,
                    "message": (
                        f"Soft bounce for {bounce.email}. Retry {bounce.retry_count}/{bounce.max_retries} scheduled."
                    ),
                }
            else:
                bounce.auto_unsubscribed = True
                self._suppression[bounce.email] = "soft_bounce_max_retries"
                return {
                    "action": "auto_unsubscribed",
                    "auto_unsubscribed": True,
                    "retry_scheduled": False,
                    "message": (
                        f"Soft bounce for {bounce.email}. Max retries ({bounce.max_retries}) reached. "
                        "Auto-unsubscribed."
                    ),
                }

        if bounce.bounce_type == BounceType.block.value or bounce.bounce_type == "block":
            # Count prior blocks for this email
            prior_blocks = sum(
                1
                for b in self._bounce_history
                if b.email == bounce.email
                and (b.bounce_type == BounceType.block.value or b.bounce_type == "block")
            )
            if prior_blocks >= 2:
                bounce.auto_unsubscribed = True
                self._suppression[bounce.email] = "blocked"
                return {
                    "action": "auto_unsubscribed",
                    "auto_unsubscribed": True,
                    "retry_scheduled": False,
                    "message": (
                        f"Block bounce for {bounce.email}. "
                        f"{prior_blocks} occurrences. Added to suppression list."
                    ),
                }
            return {
                "action": "investigate",
                "auto_unsubscribed": False,
                "retry_scheduled": False,
                "message": (
                    f"Block bounce for {bounce.email}. Occurrence {prior_blocks}. "
                    "Monitoring -- will suppress after 2 occurrences."
                ),
            }

        # Unknown bounce type
        return {
            "action": "logged",
            "auto_unsubscribed": False,
            "retry_scheduled": False,
            "message": f"Unknown bounce type for {bounce.email}. Logged for review.",
        }

    def process_spam_complaint(
        self, complaint: SpamComplaintRecord
    ) -> Dict[str, Any]:
        """Handle a spam complaint.  Always auto-unsubscribes the contact."""
        self._spam_complaints.append(complaint)
        complaint.auto_unsubscribed = True
        self._suppression[complaint.email] = "spam_complaint"

        total_sent = max(len(self._bounce_history) + len(self._spam_complaints), 1)
        rate = len(self._spam_complaints) / total_sent

        alert = rate >= self.alert_spam_rate
        if rate >= self.pause_spam_rate:
            message = (
                f"CRITICAL: Spam complaint rate {rate:.4f} exceeds pause threshold "
                f"({self.pause_spam_rate}). Sending should be paused immediately."
            )
        elif alert:
            message = (
                f"WARNING: Spam complaint rate {rate:.4f} exceeds alert threshold "
                f"({self.alert_spam_rate}). Review content and targeting."
            )
        else:
            message = f"Spam complaint from {complaint.email}. Rate {rate:.4f} is within limits."

        return {
            "action": "auto_unsubscribed",
            "complaint_rate": round(rate, 6),
            "alert": alert,
            "message": message,
        }

    def check_list_hygiene(
        self, contacts: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyse a contact list for hygiene issues.

        Each contact dict should have at minimum ``email``.
        Optional keys: ``last_open_date``, ``bounced``, ``complained``, ``status``.
        """
        total = len(contacts)
        clean = 0
        inactive_90d = 0
        bounced = 0
        complained = 0
        duplicates = 0
        invalid = 0
        recommendations: List[str] = []

        seen_emails: set = set()
        now = datetime.utcnow()
        ninety_days_ago = now - timedelta(days=90)

        for c in contacts:
            email = c.get("email", "")

            # Invalid format
            if not validate_email_format(email):
                invalid += 1
                continue

            # Duplicate check
            email_lower = email.lower().strip()
            if email_lower in seen_emails:
                duplicates += 1
                continue
            seen_emails.add(email_lower)

            # Bounced
            if c.get("bounced", False):
                bounced += 1
                continue

            # Complained
            if c.get("complained", False):
                complained += 1
                continue

            # Inactive (no opens in 90 days)
            last_open = c.get("last_open_date")
            if last_open:
                try:
                    last_open_dt = _parse_iso(last_open)
                    if last_open_dt < ninety_days_ago:
                        inactive_90d += 1
                        continue
                except (ValueError, TypeError):
                    pass

            clean += 1

        # Recommendations
        if invalid > 0:
            recommendations.append(f"Remove {invalid} contacts with invalid email formats.")
        if bounced > 0:
            recommendations.append(f"Remove {bounced} hard-bounced contacts from your list.")
        if complained > 0:
            recommendations.append(f"Suppress {complained} contacts who filed spam complaints.")
        if duplicates > 0:
            recommendations.append(f"De-duplicate {duplicates} duplicate email addresses.")
        if inactive_90d > 0:
            pct = round((inactive_90d / max(total, 1)) * 100, 1)
            if pct > 30:
                recommendations.append(
                    f"{inactive_90d} contacts ({pct}%) have not opened in 90 days. "
                    "Run a re-engagement campaign or remove them to protect deliverability."
                )
            else:
                recommendations.append(
                    f"{inactive_90d} contacts ({pct}%) inactive for 90+ days. "
                    "Consider a re-engagement sequence before removing."
                )

        if not recommendations:
            recommendations.append("List looks healthy. No immediate action required.")

        return {
            "total": total,
            "clean": clean,
            "inactive_90d": inactive_90d,
            "bounced": bounced,
            "complained": complained,
            "duplicates": duplicates,
            "invalid": invalid,
            "recommendations": recommendations,
        }

    def generate_deliverability_report(
        self, stats: Dict[str, Any]
    ) -> DeliverabilityReport:
        """Compile deliverability metrics into a health report.

        *stats* dict keys: ``domain``, ``period``, ``total_sent``,
        ``delivered``, ``opens``, ``clicks``, ``bounces``, ``soft_bounces``,
        ``hard_bounces``, ``spam_complaints``, ``unsubscribes``,
        ``spf_configured``, ``dkim_configured``, ``dmarc_configured``.
        """
        total = stats.get("total_sent", 0)
        if total == 0:
            total = 1  # avoid division by zero

        delivery_rate = stats.get("delivered", 0) / total
        open_rate = stats.get("opens", 0) / total
        click_rate = stats.get("clicks", 0) / total
        bounce_rate = stats.get("bounces", 0) / total
        soft_bounce_rate = stats.get("soft_bounces", 0) / total
        hard_bounce_rate = stats.get("hard_bounces", 0) / total
        spam_rate = stats.get("spam_complaints", 0) / total
        unsub_rate = stats.get("unsubscribes", 0) / total

        issues: List[str] = []
        recommendations: List[str] = []
        is_healthy = True

        # Bounce analysis
        if bounce_rate > self.alert_bounce_rate:
            is_healthy = False
            issues.append(f"Bounce rate {bounce_rate:.2%} exceeds {self.alert_bounce_rate:.0%} threshold.")
            recommendations.append("Clean your email list. Remove hard-bounced addresses immediately.")

        # Spam analysis
        if spam_rate >= self.pause_spam_rate:
            is_healthy = False
            issues.append(
                f"CRITICAL: Spam complaint rate {spam_rate:.4%} exceeds pause threshold "
                f"({self.pause_spam_rate:.2%}). Auto-pause sending."
            )
            recommendations.append(
                "Pause all marketing sends immediately. Review content, "
                "targeting, and list acquisition methods before resuming."
            )
        elif spam_rate >= self.alert_spam_rate:
            is_healthy = False
            issues.append(f"Spam complaint rate {spam_rate:.4%} is elevated.")
            recommendations.append("Review email content and audience targeting.")

        # Open rate analysis
        if open_rate < 0.10:
            issues.append(f"Open rate {open_rate:.2%} is below 10%.")
            recommendations.append(
                "Test different subject lines, send times, and sender names. "
                "Check that emails are not landing in spam."
            )

        # Authentication
        spf = stats.get("spf_configured", False)
        dkim = stats.get("dkim_configured", False)
        dmarc = stats.get("dmarc_configured", False)

        if not spf:
            recommendations.append("Configure SPF record for your sending domain.")
        if not dkim:
            recommendations.append("Configure DKIM signing for your sending domain.")
        if not dmarc:
            recommendations.append("Configure DMARC policy for your sending domain.")
        if not (spf and dkim and dmarc):
            issues.append("Email authentication is incomplete (SPF/DKIM/DMARC).")

        return DeliverabilityReport(
            domain=stats.get("domain", "unknown"),
            period=stats.get("period", "unknown"),
            total_sent=stats.get("total_sent", 0),
            delivery_rate=round(delivery_rate, 4),
            open_rate=round(open_rate, 4),
            click_rate=round(click_rate, 4),
            bounce_rate=round(bounce_rate, 4),
            soft_bounce_rate=round(soft_bounce_rate, 4),
            hard_bounce_rate=round(hard_bounce_rate, 4),
            spam_complaint_rate=round(spam_rate, 6),
            unsubscribe_rate=round(unsub_rate, 4),
            is_healthy=is_healthy,
            issues=issues,
            recommendations=recommendations,
            spf_configured=spf,
            dkim_configured=dkim,
            dmarc_configured=dmarc,
            generated_at=datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S"),
        )

    def get_warmup_limit(self, warmup_schedule: WarmUpSchedule) -> int:
        """Return the maximum sends allowed for the current warm-up day.

        Returns ``-1`` if warm-up is complete (no limit).
        """
        schedule = warmup_schedule.schedule or DEFAULT_WARMUP_SCHEDULE
        for entry in schedule:
            if entry["day"] == warmup_schedule.current_day:
                return entry["max_sends"]
        # Beyond schedule: warm-up complete
        if warmup_schedule.current_day > len(schedule):
            return -1
        return -1

    def check_authentication(self) -> Dict[str, Any]:
        """Return email authentication setup status.

        In non-production mode this returns a placeholder result with a
        recommendation to verify DNS records.
        """
        return {
            "spf": {"configured": False, "record": None},
            "dkim": {"configured": False, "record": None},
            "dmarc": {"configured": False, "record": None},
            "recommendations": [
                "Verify SPF, DKIM, and DMARC records for your sending domain.",
                "Use a tool like MXToolbox or Google Postmaster Tools to validate configuration.",
            ],
        }


# ============================================================================
# OptOutManager
# ============================================================================


class OptOutManager:
    """Manages opt-out / unsubscribe compliance.

    Processes opt-outs within 24 hours (better than the legal 10-day CAN-SPAM
    requirement).  Maintains an in-memory suppression list.
    """

    def __init__(self, honor_within_hours: int = 24) -> None:
        self._honor_within_hours = honor_within_hours
        self._suppression_list: Dict[str, OptOutRecord] = {}

    def process_opt_out(
        self,
        email: str,
        opt_out_type: str = "global",
        source: str = "unsubscribe_link",
        scope: Optional[str] = None,
    ) -> OptOutRecord:
        """Record and immediately honour an opt-out request."""
        now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S")
        record = OptOutRecord(
            email=email,
            opt_out_type=opt_out_type,
            opt_out_scope=scope,
            opted_out_at=now_iso,
            source=source,
            honored_at=now_iso,  # immediate processing
        )
        self._suppression_list[email.lower().strip()] = record
        return record

    def check_can_send(
        self,
        email: str,
        email_type: str = "marketing",
    ) -> Dict[str, Any]:
        """Check whether an email can be sent to this address.

        Distinguishes between marketing and transactional eligibility.
        """
        key = email.lower().strip()
        record = self._suppression_list.get(key)

        if record is None:
            return {
                "can_send": True,
                "reason": None,
                "email_types_allowed": ["marketing", "transactional"],
            }

        # Global opt-out blocks marketing but still allows transactional
        if record.opt_out_type == "global":
            if email_type == "transactional":
                return {
                    "can_send": True,
                    "reason": "Contact opted out globally but transactional emails are allowed.",
                    "email_types_allowed": ["transactional"],
                }
            return {
                "can_send": False,
                "reason": f"Contact opted out globally on {record.opted_out_at} via {record.source}.",
                "email_types_allowed": ["transactional"],
            }

        # List-specific opt-out
        if record.opt_out_type == "list":
            if email_type == "transactional":
                return {
                    "can_send": True,
                    "reason": "Contact opted out of a specific list; transactional still allowed.",
                    "email_types_allowed": ["transactional"],
                }
            # Check scope match (the caller should pass the relevant list)
            return {
                "can_send": False,
                "reason": (
                    f"Contact opted out of list '{record.opt_out_scope}' "
                    f"on {record.opted_out_at}."
                ),
                "email_types_allowed": ["transactional"],
            }

        # Type-specific opt-out
        if record.opt_out_type == "type":
            if email_type == record.opt_out_scope:
                return {
                    "can_send": False,
                    "reason": f"Contact opted out of '{record.opt_out_scope}' emails.",
                    "email_types_allowed": ["transactional"],
                }
            return {
                "can_send": True,
                "reason": None,
                "email_types_allowed": ["marketing", "transactional"],
            }

        # Fallback: treat unknown opt-out types as global
        return {
            "can_send": False,
            "reason": "Contact is on suppression list.",
            "email_types_allowed": [],
        }

    def get_suppression_list(self) -> List[OptOutRecord]:
        """Return all active opt-out records."""
        return list(self._suppression_list.values())

    def is_suppressed(self, email: str) -> bool:
        """Quick check if email is on suppression list."""
        return email.lower().strip() in self._suppression_list

    def process_re_opt_in(
        self,
        email: str,
        source: str = "explicit_consent",
    ) -> Dict[str, Any]:
        """Handle a re-subscription request.

        Only allows re-opt-in with explicit consent.
        """
        key = email.lower().strip()

        if source != "explicit_consent":
            return {
                "success": False,
                "message": (
                    "Re-opt-in requires explicit consent. "
                    "The contact must actively confirm their subscription."
                ),
                "previous_opt_out": self._suppression_list.get(key),
            }

        previous = self._suppression_list.pop(key, None)
        return {
            "success": True,
            "message": (
                f"Contact {email} has been re-subscribed with explicit consent."
                if previous
                else f"Contact {email} was not on the suppression list."
            ),
            "previous_opt_out": previous,
        }

    def export_suppression_list(self) -> List[Dict[str, str]]:
        """Export suppression list in a standard format for compliance record-keeping."""
        return [
            {
                "email": record.email,
                "reason": record.source,
                "date": record.opted_out_at,
            }
            for record in self._suppression_list.values()
        ]
