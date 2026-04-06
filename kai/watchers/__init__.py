"""Watcher framework for the Kai Marketing OS.

Watchers are background monitoring loops that continuously check for marketing
issues, opportunities, and anomalies.  They run on schedules (hourly, daily,
weekly) or are triggered by events, and produce structured findings that can
optionally include proposed actions for automatic or operator-approved
resolution.

The framework provides:

- **Watcher** -- abstract base class that all concrete watchers extend.
  Subclasses implement ``check()`` to inspect a business profile and workspace
  state, returning a list of ``WatcherFinding`` objects.
- **WatcherRegistry** -- central catalog of available watchers with per-business
  configuration overrides and enable/disable control.
- **SuppressionManager** -- deduplication and cooldown logic that prevents alert
  fatigue by suppressing repeated findings within configurable time windows.
- **WatcherScheduler** -- orchestrates which watchers should run at a given point
  in time, executes them safely (isolating failures), applies suppression, and
  returns structured ``WatcherOutput`` results.

Concrete watchers:

- **website_visibility** -- WebsiteHealthWatcher, LocalVisibilityWatcher,
  PagePerformanceWatcher (Task 068).
- **social_freshness** -- SocialStalenessWatcher, ContentFreshnessWatcher,
  EngagementDeclineWatcher (Task 069).
- **ad_spend** -- AdFatigueWatcher, SpendAnomalyWatcher, ROASWatcher (Task 070).
- **lead_followup** -- SpeedToLeadWatcher, FollowUpGapWatcher,
  ReviewVelocityWatcher, DormantCustomerWatcher (Task 071).
- **scheduling** -- NotificationSystem, ArchetypeWatcherPack, digest models,
  and archetype-specific watcher pack factories (Task 072).

Usage::

    from kai.watchers import (
        # Framework
        Watcher,
        WatcherConfig,
        WatcherFinding,
        WatcherOutput,
        WatcherRegistry,
        WatcherScheduler,
        SuppressionManager,
        WatcherScheduleType,
        FindingUrgency,
        # Website & visibility (Task 068)
        WebsiteHealthWatcher,
        LocalVisibilityWatcher,
        PagePerformanceWatcher,
        # Social & content freshness (Task 069)
        SocialStalenessWatcher,
        ContentFreshnessWatcher,
        EngagementDeclineWatcher,
        # Ad spend & ROAS (Task 070)
        AdFatigueWatcher,
        SpendAnomalyWatcher,
        ROASWatcher,
        # Lead response & follow-up (Task 071)
        SpeedToLeadWatcher,
        FollowUpGapWatcher,
        ReviewVelocityWatcher,
        DormantCustomerWatcher,
        # Scheduling & notifications (Task 072)
        NotificationSystem,
        NotificationChannel,
        DigestFrequency,
        ArchetypeWatcherPack,
        get_watcher_pack_for_archetype,
    )
"""

from .framework import (
    # Enums
    FindingUrgency,
    WatcherScheduleType,
    # Models
    WatcherConfig,
    WatcherFinding,
    WatcherOutput,
    # Abstract base
    Watcher,
    # Infrastructure
    WatcherRegistry,
    SuppressionManager,
    WatcherScheduler,
)

# Task 068 — Website health & local visibility
from .website_visibility import (
    WebsiteHealthWatcher,
    LocalVisibilityWatcher,
    PagePerformanceWatcher,
)

# Task 069 — Social staleness & content freshness
from .social_freshness import (
    SocialStalenessWatcher,
    ContentFreshnessWatcher,
    EngagementDeclineWatcher,
)

# Task 070 — Ad fatigue & spend anomaly
from .ad_spend import (
    AdFatigueWatcher,
    SpendAnomalyWatcher,
    ROASWatcher,
)

# Task 071 — Lead response & follow-up gaps
from .lead_followup import (
    SpeedToLeadWatcher,
    FollowUpGapWatcher,
    ReviewVelocityWatcher,
    DormantCustomerWatcher,
)

# Task 072 — Scheduling, throttling, notifications
from .scheduling import (
    NotificationChannel,
    DigestFrequency,
    WatcherSchedule,
    ThrottleConfig,
    NotificationPreference,
    DigestEntry,
    Digest,
    NotificationSystem,
    ArchetypeWatcherPack,
    get_local_service_watcher_pack,
    get_ecommerce_watcher_pack,
    get_professional_services_watcher_pack,
    get_multi_location_watcher_pack,
    get_watcher_pack_for_archetype,
)

__all__ = [
    # Framework enums
    "WatcherScheduleType",
    "FindingUrgency",
    # Framework models
    "WatcherConfig",
    "WatcherFinding",
    "WatcherOutput",
    # Framework base class
    "Watcher",
    # Framework infrastructure
    "WatcherRegistry",
    "SuppressionManager",
    "WatcherScheduler",
    # Task 068 — Website health & local visibility
    "WebsiteHealthWatcher",
    "LocalVisibilityWatcher",
    "PagePerformanceWatcher",
    # Task 069 — Social staleness & content freshness
    "SocialStalenessWatcher",
    "ContentFreshnessWatcher",
    "EngagementDeclineWatcher",
    # Task 070 — Ad fatigue & spend anomaly
    "AdFatigueWatcher",
    "SpendAnomalyWatcher",
    "ROASWatcher",
    # Task 071 — Lead response & follow-up gaps
    "SpeedToLeadWatcher",
    "FollowUpGapWatcher",
    "ReviewVelocityWatcher",
    "DormantCustomerWatcher",
    # Task 072 — Scheduling, throttling, notifications
    "NotificationChannel",
    "DigestFrequency",
    "WatcherSchedule",
    "ThrottleConfig",
    "NotificationPreference",
    "DigestEntry",
    "Digest",
    "NotificationSystem",
    "ArchetypeWatcherPack",
    "get_local_service_watcher_pack",
    "get_ecommerce_watcher_pack",
    "get_professional_services_watcher_pack",
    "get_multi_location_watcher_pack",
    "get_watcher_pack_for_archetype",
]
