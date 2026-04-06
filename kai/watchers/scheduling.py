"""Watcher scheduling, throttling, notification routing, and archetype packs.

Task 072 — The "notification UX" layer that makes watchers useful instead
of noisy.  Handles schedule cadence, per-watcher throttling, notification
routing (immediate vs. daily digest vs. weekly rollup), digest compilation,
and pre-configured watcher packs per business archetype.

Components
----------
- **NotificationChannel** / **DigestFrequency** — enums for routing.
- **WatcherSchedule** / **ThrottleConfig** — per-watcher schedule and throttle models.
- **NotificationPreference** — per-business notification routing preferences.
- **DigestEntry** / **Digest** — structured digest output models.
- **NotificationSystem** — routes findings, builds digests, formats for channels.
- **ArchetypeWatcherPack** — pre-configured watcher sets per archetype.
- **get_*_watcher_pack()** — factory functions for each archetype.
"""

from __future__ import annotations

import copy
import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (matches framework.py pattern)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
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

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ============================================================================
# Enums
# ============================================================================


class NotificationChannel(str, Enum):
    """Delivery channel for watcher notifications."""

    IN_APP = "in_app"
    EMAIL = "email"
    SLACK = "slack"
    SMS = "sms"
    WEBHOOK = "webhook"


class DigestFrequency(str, Enum):
    """When a finding should be delivered to the operator."""

    IMMEDIATE = "immediate"
    DAILY = "daily"
    WEEKLY = "weekly"


# ============================================================================
# Data Models
# ============================================================================


class WatcherSchedule(BaseModel):
    """Per-watcher scheduling state."""

    watcher_name: str
    schedule_type: str = "daily"  # "daily", "weekly", "hourly", "event_driven"
    run_time: Optional[str] = None  # "06:00" or "monday_06:00"
    timezone: str = "UTC"
    last_run: Optional[str] = None  # ISO timestamp
    next_run: Optional[str] = None  # ISO timestamp
    consecutive_failures: int = 0
    max_retries: int = 3
    backoff_minutes: int = 30


class ThrottleConfig(BaseModel):
    """Per-watcher throttling rules to prevent alert fatigue."""

    watcher_name: str
    max_findings_per_day: int = 5
    suppression_window_days: int = 7
    cooldown_after_action_days: int = 14
    max_findings_per_run: int = 10
    priority_order: List[str] = Field(
        default_factory=lambda: ["critical", "high", "medium", "low"]
    )
    severity_minimum: str = "low"  # Show everything by default


class NotificationPreference(BaseModel):
    """Per-business notification routing preferences."""

    business_id: str
    operator_email: Optional[str] = None
    operator_phone: Optional[str] = None
    slack_channel: Optional[str] = None
    webhook_url: Optional[str] = None
    channels: List[str] = Field(
        default_factory=lambda: [NotificationChannel.IN_APP.value]
    )
    critical_channels: List[str] = Field(
        default_factory=lambda: [
            NotificationChannel.IN_APP.value,
            NotificationChannel.EMAIL.value,
        ]
    )
    digest_frequency: str = DigestFrequency.DAILY.value
    quiet_hours_start: Optional[str] = None  # "22:00"
    quiet_hours_end: Optional[str] = None    # "07:00"
    weekly_digest_day: str = "monday"
    weekly_digest_time: str = "09:00"


class DigestEntry(BaseModel):
    """A single entry within a digest."""

    watcher_name: str
    finding_id: str
    title: str
    severity: str
    urgency: str
    category: str
    description: str = ""  # Max 200 chars
    has_proposed_action: bool = False
    auto_eligible: bool = False


class Digest(BaseModel):
    """Compiled digest of watcher findings for a business."""

    business_id: str
    business_name: str
    digest_type: str = "daily"  # "daily" or "weekly"
    period_start: str = ""      # ISO date
    period_end: str = ""        # ISO date
    generated_at: str = ""      # ISO timestamp
    total_findings: int = 0
    critical_findings: int = 0
    high_findings: int = 0
    medium_findings: int = 0
    low_findings: int = 0
    entries: List[DigestEntry] = Field(default_factory=list)
    suppressed_count: int = 0
    top_priorities: List[str] = Field(default_factory=list)
    overall_health_trend: str = "stable"  # "improving", "stable", "declining"
    action_items: List[str] = Field(default_factory=list)


# ============================================================================
# NotificationSystem
# ============================================================================


class NotificationSystem:
    """Routes findings to the right notification channel and builds digests.

    Determines whether a finding should be sent immediately, added to a
    daily digest, or held for the weekly rollup.  Respects quiet hours,
    severity-based channel routing, and per-business preferences.
    """

    SEVERITY_RANK = {"critical": 0, "high": 1, "medium": 2, "low": 3, "warning": 2}

    def __init__(self) -> None:
        self._pending_notifications: Dict[str, List[DigestEntry]] = {}
        self._previous_digest_counts: Dict[str, int] = {}

    # -- Routing ------------------------------------------------------------

    def route_finding(
        self,
        finding: Any,
        preference: NotificationPreference,
    ) -> str:
        """Determine where a finding should go based on urgency and preference.

        Routing rules:
        - urgency="immediate" -> send via critical_channels immediately
        - urgency="soon" + severity critical/high -> critical_channels
        - urgency="soon" + severity medium/low -> daily digest
        - urgency="scheduled" -> daily or weekly digest per preference
        - urgency="informational" -> weekly digest only

        Quiet hours: non-critical immediate findings are queued for
        delivery at quiet_hours_end.

        Parameters
        ----------
        finding:
            A ``WatcherFinding`` or compatible object with ``urgency``,
            ``severity``, ``watcher_name``, ``id``, ``title``,
            ``category``, ``description``, ``proposed_action``,
            ``auto_eligible``, and ``business_id``.
        preference:
            The business's notification preferences.

        Returns
        -------
        str
            The routing decision: "immediate", "daily_digest", or
            "weekly_digest".
        """
        urgency = _get_attr(finding, "urgency", "scheduled")
        severity = _get_attr(finding, "severity", "medium")
        business_id = _get_attr(finding, "business_id", preference.business_id)

        # Build a digest entry for potential queuing
        entry = DigestEntry(
            watcher_name=_get_attr(finding, "watcher_name", ""),
            finding_id=_get_attr(finding, "id", ""),
            title=_get_attr(finding, "title", ""),
            severity=severity,
            urgency=urgency,
            category=_get_attr(finding, "category", ""),
            description=_get_attr(finding, "description", "")[:200],
            has_proposed_action=_get_attr(finding, "proposed_action", None) is not None,
            auto_eligible=_get_attr(finding, "auto_eligible", False),
        )

        current_time = datetime.now(timezone.utc).strftime("%H:%M")
        in_quiet = self._is_in_quiet_hours(current_time, preference)

        if urgency == "immediate":
            if severity in ("critical", "high") or not in_quiet:
                return "immediate"
            # Non-critical immediate during quiet hours -> queue for morning
            self.add_to_digest(business_id, entry)
            return "daily_digest"

        if urgency == "soon":
            if severity in ("critical", "high"):
                if in_quiet and severity != "critical":
                    self.add_to_digest(business_id, entry)
                    return "daily_digest"
                return "immediate"
            # Medium/low severity "soon" -> daily digest
            self.add_to_digest(business_id, entry)
            return "daily_digest"

        if urgency == "scheduled":
            if preference.digest_frequency == DigestFrequency.WEEKLY.value:
                self.add_to_digest(business_id, entry)
                return "weekly_digest"
            self.add_to_digest(business_id, entry)
            return "daily_digest"

        if urgency == "informational":
            self.add_to_digest(business_id, entry)
            return "weekly_digest"

        # Default fallback
        self.add_to_digest(business_id, entry)
        return "daily_digest"

    # -- Digest building ----------------------------------------------------

    def add_to_digest(self, business_id: str, entry: DigestEntry) -> None:
        """Add an entry to the pending notification queue for a business."""
        if business_id not in self._pending_notifications:
            self._pending_notifications[business_id] = []
        self._pending_notifications[business_id].append(entry)

    def build_daily_digest(
        self,
        business_id: str,
        business_name: str,
    ) -> Digest:
        """Compile all pending entries for today into a Digest.

        Sorts entries by severity (critical first), generates top priorities
        from critical + high severity entries, generates actionable items,
        and calculates the overall health trend by comparing finding count
        to the previous digest.
        """
        entries = self._pending_notifications.pop(business_id, [])

        # Sort by severity
        entries.sort(key=lambda e: self.SEVERITY_RANK.get(e.severity, 99))

        # Count by severity
        counts = _count_by_severity(entries)

        # Generate top priorities (from critical and high entries)
        top_priorities = _generate_top_priorities(entries)

        # Generate action items
        action_items = _generate_action_items(entries)

        # Health trend
        previous_count = self._previous_digest_counts.get(business_id, 0)
        total = len(entries)
        if previous_count == 0:
            trend = "stable"
        elif total < previous_count:
            trend = "improving"
        elif total > previous_count:
            trend = "declining"
        else:
            trend = "stable"

        self._previous_digest_counts[business_id] = total

        now = datetime.now(timezone.utc)

        return Digest(
            business_id=business_id,
            business_name=business_name,
            digest_type="daily",
            period_start=now.strftime("%Y-%m-%d"),
            period_end=now.strftime("%Y-%m-%d"),
            generated_at=now.isoformat(),
            total_findings=total,
            critical_findings=counts.get("critical", 0),
            high_findings=counts.get("high", 0),
            medium_findings=counts.get("medium", 0),
            low_findings=counts.get("low", 0),
            entries=entries,
            suppressed_count=0,
            top_priorities=top_priorities,
            overall_health_trend=trend,
            action_items=action_items,
        )

    def build_weekly_digest(
        self,
        business_id: str,
        business_name: str,
        daily_digests: List[Digest],
    ) -> Digest:
        """Compile weekly rollup from daily digests plus weekly-only entries.

        Deduplicates entries that appeared in multiple daily digests (by
        finding_id).  Includes any pending weekly-only entries.
        """
        # Collect all entries and deduplicate
        seen_ids: set[str] = set()
        all_entries: List[DigestEntry] = []

        for digest in daily_digests:
            for entry in digest.entries:
                if entry.finding_id not in seen_ids:
                    seen_ids.add(entry.finding_id)
                    all_entries.append(entry)

        # Add any pending weekly-only entries
        pending = self._pending_notifications.pop(business_id, [])
        for entry in pending:
            if entry.finding_id not in seen_ids:
                seen_ids.add(entry.finding_id)
                all_entries.append(entry)

        # Sort by severity
        all_entries.sort(key=lambda e: self.SEVERITY_RANK.get(e.severity, 99))

        counts = _count_by_severity(all_entries)
        top_priorities = _generate_top_priorities(all_entries)
        action_items = _generate_action_items(all_entries)

        # Calculate suppressed total from daily digests
        total_suppressed = sum(d.suppressed_count for d in daily_digests)

        # Trend from daily digest progression
        if len(daily_digests) >= 2:
            first_half = daily_digests[: len(daily_digests) // 2]
            second_half = daily_digests[len(daily_digests) // 2 :]
            first_avg = (
                sum(d.total_findings for d in first_half) / len(first_half)
                if first_half
                else 0
            )
            second_avg = (
                sum(d.total_findings for d in second_half) / len(second_half)
                if second_half
                else 0
            )
            if second_avg < first_avg * 0.8:
                trend = "improving"
            elif second_avg > first_avg * 1.2:
                trend = "declining"
            else:
                trend = "stable"
        else:
            trend = "stable"

        now = datetime.now(timezone.utc)
        period_start = (
            daily_digests[0].period_start if daily_digests else now.strftime("%Y-%m-%d")
        )
        period_end = now.strftime("%Y-%m-%d")

        return Digest(
            business_id=business_id,
            business_name=business_name,
            digest_type="weekly",
            period_start=period_start,
            period_end=period_end,
            generated_at=now.isoformat(),
            total_findings=len(all_entries),
            critical_findings=counts.get("critical", 0),
            high_findings=counts.get("high", 0),
            medium_findings=counts.get("medium", 0),
            low_findings=counts.get("low", 0),
            entries=all_entries,
            suppressed_count=total_suppressed,
            top_priorities=top_priorities,
            overall_health_trend=trend,
            action_items=action_items,
        )

    # -- Channel formatting -------------------------------------------------

    def _format_for_channel(self, digest: Digest, channel: str) -> str:
        """Format a digest for the target notification channel.

        Parameters
        ----------
        digest:
            The compiled digest to format.
        channel:
            One of the ``NotificationChannel`` values.

        Returns
        -------
        str
            Formatted string suitable for the channel.
        """
        if channel == NotificationChannel.IN_APP.value:
            return self._format_in_app(digest)
        elif channel == NotificationChannel.EMAIL.value:
            return self._format_email(digest)
        elif channel == NotificationChannel.SLACK.value:
            return self._format_slack(digest)
        else:
            # Webhook, SMS, and unknown channels get JSON
            return self._format_in_app(digest)

    def _format_in_app(self, digest: Digest) -> str:
        """Format digest as structured JSON for dashboard display."""
        data = {
            "business_id": digest.business_id,
            "business_name": digest.business_name,
            "digest_type": digest.digest_type,
            "generated_at": digest.generated_at,
            "summary": {
                "total": digest.total_findings,
                "critical": digest.critical_findings,
                "high": digest.high_findings,
                "medium": digest.medium_findings,
                "low": digest.low_findings,
            },
            "health_trend": digest.overall_health_trend,
            "top_priorities": digest.top_priorities,
            "action_items": digest.action_items,
            "entries": [
                {
                    "title": e.title,
                    "severity": e.severity,
                    "category": e.category,
                    "has_action": e.has_proposed_action,
                    "auto_eligible": e.auto_eligible,
                }
                for e in digest.entries
            ],
        }
        return json.dumps(data, indent=2, default=str)

    def _format_email(self, digest: Digest) -> str:
        """Format digest as email-friendly plain text."""
        lines = [
            f"{'Weekly' if digest.digest_type == 'weekly' else 'Daily'} "
            f"Marketing Health Report — {digest.business_name}",
            f"Period: {digest.period_start} to {digest.period_end}",
            f"Generated: {digest.generated_at}",
            "",
            "=" * 50,
            "SUMMARY",
            "=" * 50,
            f"Total findings: {digest.total_findings}",
            f"  Critical: {digest.critical_findings}",
            f"  High: {digest.high_findings}",
            f"  Medium: {digest.medium_findings}",
            f"  Low: {digest.low_findings}",
            f"Health trend: {digest.overall_health_trend}",
            "",
        ]

        if digest.top_priorities:
            lines.append("TOP PRIORITIES")
            lines.append("-" * 30)
            for i, priority in enumerate(digest.top_priorities, 1):
                lines.append(f"  {i}. {priority}")
            lines.append("")

        if digest.action_items:
            lines.append("ACTION ITEMS")
            lines.append("-" * 30)
            for item in digest.action_items:
                lines.append(f"  - {item}")
            lines.append("")

        if digest.entries:
            lines.append("ALL FINDINGS")
            lines.append("-" * 30)
            for entry in digest.entries:
                severity_badge = f"[{entry.severity.upper()}]"
                action_badge = " [ACTION AVAILABLE]" if entry.has_proposed_action else ""
                lines.append(f"  {severity_badge} {entry.title}{action_badge}")
                if entry.description:
                    lines.append(f"    {entry.description}")
            lines.append("")

        if digest.suppressed_count > 0:
            lines.append(
                f"({digest.suppressed_count} additional findings suppressed "
                "by throttling rules)"
            )

        return "\n".join(lines)

    def _format_slack(self, digest: Digest) -> str:
        """Format digest as a Slack-compatible message with sections."""
        blocks = [
            f"*{'Weekly' if digest.digest_type == 'weekly' else 'Daily'} "
            f"Marketing Health — {digest.business_name}*",
            f"_{digest.period_start} to {digest.period_end}_",
            "",
            f":bar_chart: *{digest.total_findings} findings* | "
            f"Trend: {digest.overall_health_trend}",
        ]

        if digest.critical_findings > 0:
            blocks.append(
                f":rotating_light: *{digest.critical_findings} critical* issues"
            )

        if digest.top_priorities:
            blocks.append("")
            blocks.append("*Top Priorities:*")
            for i, priority in enumerate(digest.top_priorities, 1):
                blocks.append(f"  {i}. {priority}")

        if digest.action_items:
            blocks.append("")
            blocks.append("*Action Items:*")
            for item in digest.action_items:
                blocks.append(f"  - {item}")

        return "\n".join(blocks)

    # -- Quiet hours --------------------------------------------------------

    def _is_in_quiet_hours(
        self,
        current_time: str,
        preference: NotificationPreference,
    ) -> bool:
        """Check if current time falls within quiet hours.

        Handles overnight ranges (e.g., 22:00 to 07:00) correctly.

        Parameters
        ----------
        current_time:
            Time in "HH:MM" 24-hour format.
        preference:
            Notification preference with quiet_hours_start/end.

        Returns
        -------
        bool
            True if the current time is within the quiet window.
        """
        start = preference.quiet_hours_start
        end = preference.quiet_hours_end

        if start is None or end is None:
            return False

        try:
            current_minutes = _time_to_minutes(current_time)
            start_minutes = _time_to_minutes(start)
            end_minutes = _time_to_minutes(end)
        except (ValueError, IndexError):
            return False

        if start_minutes <= end_minutes:
            # Same-day range (e.g., 09:00 to 17:00)
            return start_minutes <= current_minutes < end_minutes
        else:
            # Overnight range (e.g., 22:00 to 07:00)
            return current_minutes >= start_minutes or current_minutes < end_minutes


# ============================================================================
# ArchetypeWatcherPack
# ============================================================================


class ArchetypeWatcherPack(BaseModel):
    """Pre-configured watcher set for a business archetype."""

    archetype: str
    watchers: List[str] = Field(default_factory=list)
    description: str = ""
    overrides: Dict[str, Dict[str, Any]] = Field(default_factory=dict)


def get_local_service_watcher_pack() -> ArchetypeWatcherPack:
    """Comprehensive monitoring for local service businesses.

    Covers website health, local visibility, reviews, lead response speed,
    follow-up gaps, social freshness, content freshness, ad fatigue, and
    spend anomalies.
    """
    return ArchetypeWatcherPack(
        archetype="local_service",
        watchers=[
            "website_health",
            "local_visibility",
            "review_velocity",
            "speed_to_lead",
            "social_staleness",
            "followup_gaps",
            "content_freshness",
            "ad_fatigue",
            "spend_anomaly",
        ],
        description=(
            "Comprehensive monitoring for local service businesses — website "
            "health, local visibility, reviews, lead response speed, and "
            "follow-up gaps"
        ),
        overrides={
            "speed_to_lead": {"suppression_window_days": 3},
        },
    )


def get_ecommerce_watcher_pack() -> ArchetypeWatcherPack:
    """E-commerce monitoring focused on site performance, ad efficiency, and retention."""
    return ArchetypeWatcherPack(
        archetype="ecommerce",
        watchers=[
            "website_health",
            "page_performance",
            "ad_fatigue",
            "spend_anomaly",
            "roas_monitor",
            "content_freshness",
            "social_staleness",
            "engagement_decline",
            "dormant_customers",
        ],
        description=(
            "E-commerce monitoring — site performance, ad spend efficiency, "
            "customer retention, and content freshness"
        ),
        overrides={},
    )


def get_professional_services_watcher_pack() -> ArchetypeWatcherPack:
    """Professional services monitoring focused on content and lead response.

    Tightens the blog freshness threshold to 6 months instead of 12 because
    professional services firms rely on thought leadership and stale content
    erodes credibility faster.
    """
    return ArchetypeWatcherPack(
        archetype="professional_services",
        watchers=[
            "website_health",
            "content_freshness",
            "engagement_decline",
            "speed_to_lead",
            "followup_gaps",
            "social_staleness",
        ],
        description=(
            "Professional services monitoring — content freshness, engagement, "
            "lead response, and thought leadership"
        ),
        overrides={
            "content_freshness": {
                "custom_config": {"blog_posts_threshold_months": 6},
            },
        },
    )


def get_multi_location_watcher_pack() -> ArchetypeWatcherPack:
    """Multi-location monitoring: all local service watchers applied per-location.

    Each watcher runs once per location, enabling location-level health
    tracking.  Includes a placeholder for a future ``brand_consistency``
    watcher that ensures all locations maintain consistent branding.
    """
    return ArchetypeWatcherPack(
        archetype="multi_location",
        watchers=[
            "website_health",
            "local_visibility",
            "review_velocity",
            "speed_to_lead",
            "social_staleness",
            "followup_gaps",
            "content_freshness",
            "ad_fatigue",
            "spend_anomaly",
            "brand_consistency",  # placeholder for future implementation
        ],
        description=(
            "Multi-location monitoring — all local service watchers per "
            "location plus brand consistency"
        ),
        overrides={
            "speed_to_lead": {"suppression_window_days": 3},
        },
    )


def get_watcher_pack_for_archetype(archetype: str) -> ArchetypeWatcherPack:
    """Return the pre-configured watcher pack for a given archetype.

    Parameters
    ----------
    archetype:
        One of "local_service", "ecommerce", "professional_services",
        or "multi_location".

    Returns
    -------
    ArchetypeWatcherPack
        The matching watcher pack.

    Raises
    ------
    ValueError
        If the archetype is not recognized.
    """
    packs = {
        "local_service": get_local_service_watcher_pack,
        "ecommerce": get_ecommerce_watcher_pack,
        "professional_services": get_professional_services_watcher_pack,
        "multi_location": get_multi_location_watcher_pack,
    }

    factory = packs.get(archetype)
    if factory is None:
        raise ValueError(
            f"Unknown archetype '{archetype}'. Supported: "
            f"{', '.join(sorted(packs.keys()))}"
        )
    return factory()


# ============================================================================
# Helpers
# ============================================================================


def _time_to_minutes(time_str: str) -> int:
    """Convert "HH:MM" to total minutes since midnight."""
    parts = time_str.split(":")
    return int(parts[0]) * 60 + int(parts[1])


def _get_attr(obj: Any, attr: str, default: Any = None) -> Any:
    """Get attribute from an object or dict."""
    if hasattr(obj, attr):
        return getattr(obj, attr)
    if isinstance(obj, dict):
        return obj.get(attr, default)
    return default


def _count_by_severity(entries: List[DigestEntry]) -> Dict[str, int]:
    """Count entries by severity level."""
    counts: Dict[str, int] = {}
    for entry in entries:
        counts[entry.severity] = counts.get(entry.severity, 0) + 1
    return counts


def _generate_top_priorities(entries: List[DigestEntry], max_items: int = 3) -> List[str]:
    """Generate human-readable top priority items from critical/high entries."""
    priorities: List[str] = []
    for entry in entries:
        if entry.severity in ("critical", "high") and len(priorities) < max_items:
            priorities.append(entry.title)
    return priorities


def _generate_action_items(entries: List[DigestEntry]) -> List[str]:
    """Generate specific action items from entries with proposed actions."""
    items: List[str] = []
    for entry in entries:
        if entry.has_proposed_action and entry.severity in ("critical", "high"):
            action_text = (
                f"[{entry.severity.upper()}] {entry.title}"
                + (" (auto-eligible)" if entry.auto_eligible else "")
            )
            items.append(action_text)
    return items
