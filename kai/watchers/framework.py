"""Core watcher framework for the Kai Marketing OS.

This module defines the abstract ``Watcher`` base class, structured output
models (``WatcherFinding``, ``WatcherOutput``), configuration (``WatcherConfig``),
and the scheduling/suppression infrastructure that manages registration,
deduplication, and execution for all individual watchers.

Design principles:

1. **No external dependencies** -- stdlib only (with optional Pydantic upgrade).
2. **Isolation** -- one watcher crashing never takes down others.
3. **Suppression** -- same issue is not re-surfaced within a configurable window.
4. **Archetype-aware** -- watchers declare which business archetypes they apply to.
5. **Schedule-aware** -- daily, weekly, hourly, or event-driven cadences.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import abc
import copy
import logging
import time
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors kai/models/audit.py)
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
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ============================================================================
# Enums
# ============================================================================


class WatcherScheduleType(str, Enum):
    """Cadence at which a watcher runs."""

    DAILY = "daily"
    WEEKLY = "weekly"
    EVENT_DRIVEN = "event_driven"
    HOURLY = "hourly"


class FindingUrgency(str, Enum):
    """How quickly a finding demands attention."""

    IMMEDIATE = "immediate"     # Needs attention now (site down, tracking broken)
    SOON = "soon"               # Should be addressed within 24-48 hours
    SCHEDULED = "scheduled"     # Can be addressed in next planning cycle
    INFORMATIONAL = "informational"  # FYI, no action required


# ============================================================================
# Data Models
# ============================================================================


class WatcherConfig(BaseModel):
    """Per-watcher configuration, overridable per business."""

    watcher_name: str
    enabled: bool = True
    schedule_type: str = WatcherScheduleType.DAILY.value
    schedule_time: Optional[str] = None
    archetype_relevance: List[str] = Field(default_factory=list)
    max_findings_per_run: int = 10
    suppression_window_days: int = 7
    cooldown_after_action_days: int = 14
    custom_config: Dict[str, Any] = Field(default_factory=dict)


class WatcherFinding(BaseModel):
    """A single finding produced by a watcher run.

    Mirrors the structure of ``AuditFinding`` in ``kai.models.audit`` but
    is tailored for continuous monitoring: it carries a suppression key for
    deduplication, an urgency level, and an optional proposed action.
    """

    id: str
    watcher_name: str
    business_id: str
    check_timestamp: str
    title: str
    description: str
    urgency: str = FindingUrgency.SCHEDULED.value
    severity: str = "medium"  # Reuses FindingSeverity values: critical, high, medium, low
    category: str = "website_health"
    auto_eligible: bool = False
    proposed_action: Optional[Dict[str, Any]] = None
    evidence: Dict[str, Any] = Field(default_factory=dict)
    suppression_key: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)


class WatcherOutput(BaseModel):
    """Structured output from a single watcher run."""

    watcher_name: str
    business_id: str
    run_timestamp: str
    findings: List[WatcherFinding] = Field(default_factory=list)
    suppressed_count: int = 0
    errors: List[str] = Field(default_factory=list)
    runtime_seconds: float = 0.0


# ============================================================================
# Abstract Watcher Base Class
# ============================================================================


class Watcher(abc.ABC):
    """Abstract base class for all Kai watchers.

    Subclasses must implement :meth:`check` to perform the actual monitoring
    logic against a business profile and workspace state.  They may also
    override :meth:`should_run` for fine-grained relevance filtering and
    :meth:`get_default_config` to customize default scheduling and
    suppression settings.

    Attributes
    ----------
    name : str
        Unique identifier for this watcher.
    description : str
        Human-readable explanation of what this watcher monitors.
    schedule_type : str
        Default schedule cadence (a ``WatcherScheduleType`` value).
    archetype_relevance : List[str]
        Business archetypes this watcher applies to.  Empty means all.
    enabled : bool
        Whether this watcher is active by default.
    """

    name: str = ""
    description: str = ""
    schedule_type: str = WatcherScheduleType.DAILY.value
    archetype_relevance: List[str] = []
    enabled: bool = True

    @abc.abstractmethod
    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Run the monitoring check and return findings.

        Parameters
        ----------
        business_profile:
            The ``BusinessProfile`` (or compatible dict) for the business
            being monitored.
        workspace_state:
            The current workspace/runtime state providing context such as
            connected integrations and recent activity.

        Returns
        -------
        List[WatcherFinding]
            Zero or more findings discovered during this check.
        """
        ...

    def should_run(self, business_profile: Any) -> bool:
        """Determine whether this watcher is relevant for the given business.

        Default implementation checks if the business archetype is listed in
        ``archetype_relevance``.  An empty ``archetype_relevance`` list means
        the watcher applies to all archetypes.

        Parameters
        ----------
        business_profile:
            The ``BusinessProfile`` (or compatible dict/object) for the
            business being evaluated.

        Returns
        -------
        bool
            ``True`` if this watcher should run for the given business.
        """
        if not self.archetype_relevance:
            return True

        # Support both object attribute and dict access for archetype
        archetype = None
        if hasattr(business_profile, "classification"):
            classification = business_profile.classification
            if hasattr(classification, "archetype"):
                archetype = classification.archetype
            elif isinstance(classification, dict):
                archetype = classification.get("archetype")
        elif isinstance(business_profile, dict):
            classification = business_profile.get("classification", {})
            if isinstance(classification, dict):
                archetype = classification.get("archetype")

        if archetype is None:
            # Cannot determine archetype -- run the watcher to be safe
            return True

        return archetype in self.archetype_relevance

    def get_default_config(self) -> WatcherConfig:
        """Return the default ``WatcherConfig`` for this watcher.

        Subclasses should override to set watcher-specific defaults such as
        custom schedule times, suppression windows, or max findings per run.

        Returns
        -------
        WatcherConfig
            Default configuration for this watcher.
        """
        return WatcherConfig(
            watcher_name=self.name,
            enabled=self.enabled,
            schedule_type=self.schedule_type,
            archetype_relevance=list(self.archetype_relevance),
        )


# ============================================================================
# Watcher Registry
# ============================================================================


class WatcherRegistry:
    """Central catalog of registered watchers with per-business overrides.

    Manages watcher lifecycle (register, unregister, enable, disable) and
    stores per-business configuration overrides so different businesses can
    customize schedule, suppression, and enabled state independently.
    """

    def __init__(self) -> None:
        self._watchers: Dict[str, Watcher] = {}
        self._configs: Dict[str, Dict[str, WatcherConfig]] = {}

    # -- Registration -------------------------------------------------------

    def register(self, watcher: Watcher) -> None:
        """Register a watcher.

        Raises
        ------
        ValueError
            If a watcher with the same ``name`` is already registered.
        """
        if watcher.name in self._watchers:
            raise ValueError(
                f"Watcher '{watcher.name}' is already registered. "
                "Unregister the existing watcher first."
            )
        self._watchers[watcher.name] = watcher
        logger.debug("Registered watcher: %s", watcher.name)

    def unregister(self, watcher_name: str) -> None:
        """Remove a watcher from the registry.

        Silently ignores unknown watcher names.
        """
        removed = self._watchers.pop(watcher_name, None)
        if removed is not None:
            logger.debug("Unregistered watcher: %s", watcher_name)

    # -- Lookup -------------------------------------------------------------

    def get_watcher(self, name: str) -> Optional[Watcher]:
        """Return a watcher by name, or ``None`` if not found."""
        return self._watchers.get(name)

    def list_watchers(self) -> List[Watcher]:
        """Return all registered watchers."""
        return list(self._watchers.values())

    def get_watchers_for_archetype(self, archetype: str) -> List[Watcher]:
        """Return watchers relevant to the given archetype.

        A watcher with an empty ``archetype_relevance`` list is considered
        relevant to every archetype.
        """
        result: List[Watcher] = []
        for watcher in self._watchers.values():
            if not watcher.archetype_relevance or archetype in watcher.archetype_relevance:
                result.append(watcher)
        return result

    # -- Per-business configuration -----------------------------------------

    def set_config(
        self,
        business_id: str,
        watcher_name: str,
        config: WatcherConfig,
    ) -> None:
        """Set a per-business configuration override for a watcher."""
        if business_id not in self._configs:
            self._configs[business_id] = {}
        self._configs[business_id][watcher_name] = config
        logger.debug(
            "Set config override for watcher '%s' on business '%s'",
            watcher_name,
            business_id,
        )

    def get_config(self, business_id: str, watcher_name: str) -> WatcherConfig:
        """Return per-business config if set, otherwise the watcher's default.

        Falls back to a generic ``WatcherConfig`` if the watcher is not
        registered (defensive -- should not happen in normal operation).
        """
        # Check for per-business override first
        biz_configs = self._configs.get(business_id, {})
        if watcher_name in biz_configs:
            return biz_configs[watcher_name]

        # Fall back to the watcher's built-in default
        watcher = self._watchers.get(watcher_name)
        if watcher is not None:
            return watcher.get_default_config()

        # Defensive fallback -- watcher not registered
        return WatcherConfig(watcher_name=watcher_name)

    def enable_watcher(self, business_id: str, watcher_name: str) -> None:
        """Enable a watcher for a specific business.

        Creates or mutates the per-business config override so the watcher
        is marked as enabled regardless of its default.
        """
        config = self.get_config(business_id, watcher_name)
        # Build a new config with enabled=True, preserving all other fields
        updated = WatcherConfig(
            watcher_name=config.watcher_name,
            enabled=True,
            schedule_type=config.schedule_type,
            schedule_time=config.schedule_time,
            archetype_relevance=config.archetype_relevance,
            max_findings_per_run=config.max_findings_per_run,
            suppression_window_days=config.suppression_window_days,
            cooldown_after_action_days=config.cooldown_after_action_days,
            custom_config=config.custom_config,
        )
        self.set_config(business_id, watcher_name, updated)

    def disable_watcher(self, business_id: str, watcher_name: str) -> None:
        """Disable a watcher for a specific business.

        Creates or mutates the per-business config override so the watcher
        is marked as disabled regardless of its default.
        """
        config = self.get_config(business_id, watcher_name)
        updated = WatcherConfig(
            watcher_name=config.watcher_name,
            enabled=False,
            schedule_type=config.schedule_type,
            schedule_time=config.schedule_time,
            archetype_relevance=config.archetype_relevance,
            max_findings_per_run=config.max_findings_per_run,
            suppression_window_days=config.suppression_window_days,
            cooldown_after_action_days=config.cooldown_after_action_days,
            custom_config=config.custom_config,
        )
        self.set_config(business_id, watcher_name, updated)


# ============================================================================
# Suppression Manager
# ============================================================================


class SuppressionManager:
    """Deduplication and cooldown logic for watcher findings.

    Prevents alert fatigue by tracking when findings and actions were last
    recorded, and suppressing repeat findings within configurable time
    windows.

    Internal state
    ---------------
    ``_suppressed``
        ``{business_id: {suppression_key: last_finding_iso_timestamp}}``
    ``_action_cooldowns``
        ``{business_id: {suppression_key: action_iso_timestamp}}``
    """

    def __init__(self) -> None:
        self._suppressed: Dict[str, Dict[str, str]] = {}
        self._action_cooldowns: Dict[str, Dict[str, str]] = {}

    # -- Public API ---------------------------------------------------------

    def should_suppress(
        self,
        finding: WatcherFinding,
        config: WatcherConfig,
    ) -> bool:
        """Decide whether *finding* should be suppressed.

        A finding is suppressed if:

        1. The same ``suppression_key`` for the same ``business_id`` was
           already recorded within ``config.suppression_window_days``, **or**
        2. An action was taken on the same key within
           ``config.cooldown_after_action_days``.

        Returns ``True`` to suppress, ``False`` to surface the finding.
        """
        business_id = finding.business_id
        key = finding.suppression_key

        if not key:
            # No suppression key -- never suppress
            return False

        # Check suppression window
        biz_suppressed = self._suppressed.get(business_id, {})
        last_finding_ts = biz_suppressed.get(key)
        if last_finding_ts is not None:
            if self._is_within_window(last_finding_ts, config.suppression_window_days):
                return True

        # Check action cooldown
        biz_cooldowns = self._action_cooldowns.get(business_id, {})
        action_ts = biz_cooldowns.get(key)
        if action_ts is not None:
            if self._is_within_window(action_ts, config.cooldown_after_action_days):
                return True

        return False

    def record_finding(self, finding: WatcherFinding) -> None:
        """Record that a finding was produced (for future suppression checks).

        Uses ``finding.check_timestamp`` as the recorded timestamp.
        """
        business_id = finding.business_id
        key = finding.suppression_key

        if not key:
            return

        if business_id not in self._suppressed:
            self._suppressed[business_id] = {}

        self._suppressed[business_id][key] = finding.check_timestamp

    def record_action_taken(
        self,
        business_id: str,
        suppression_key: str,
    ) -> None:
        """Record that an action was taken, triggering cooldown suppression.

        The current UTC time is used as the action timestamp.
        """
        if not suppression_key:
            return

        if business_id not in self._action_cooldowns:
            self._action_cooldowns[business_id] = {}

        self._action_cooldowns[business_id][suppression_key] = (
            datetime.now(timezone.utc).isoformat()
        )

    def clear_expired(self) -> None:
        """Remove suppression and cooldown entries older than the maximum window.

        Uses a generous 90-day maximum to ensure stale entries are cleaned up
        even if individual watchers have shorter windows.  The per-finding
        window check in :meth:`should_suppress` handles the precise cutoff.
        """
        max_window_days = 90
        self._purge_expired_entries(self._suppressed, max_window_days)
        self._purge_expired_entries(self._action_cooldowns, max_window_days)

    # -- Internals ----------------------------------------------------------

    @staticmethod
    def _is_within_window(timestamp_iso: str, window_days: int) -> bool:
        """Check whether an ISO timestamp is within *window_days* of now."""
        try:
            ts = datetime.fromisoformat(timestamp_iso)
            # Ensure timezone-aware comparison
            if ts.tzinfo is None:
                ts = ts.replace(tzinfo=timezone.utc)
            cutoff = datetime.now(timezone.utc) - timedelta(days=window_days)
            return ts > cutoff
        except (ValueError, TypeError):
            # Unparseable timestamp -- treat as expired
            return False

    @staticmethod
    def _purge_expired_entries(
        store: Dict[str, Dict[str, str]],
        max_window_days: int,
    ) -> None:
        """Remove entries older than *max_window_days* from a nested dict."""
        cutoff = datetime.now(timezone.utc) - timedelta(days=max_window_days)
        business_ids_to_remove: List[str] = []

        for business_id, entries in store.items():
            keys_to_remove: List[str] = []
            for key, ts_iso in entries.items():
                try:
                    ts = datetime.fromisoformat(ts_iso)
                    if ts.tzinfo is None:
                        ts = ts.replace(tzinfo=timezone.utc)
                    if ts <= cutoff:
                        keys_to_remove.append(key)
                except (ValueError, TypeError):
                    keys_to_remove.append(key)

            for key in keys_to_remove:
                del entries[key]

            if not entries:
                business_ids_to_remove.append(business_id)

        for business_id in business_ids_to_remove:
            del store[business_id]


# ============================================================================
# Watcher Scheduler
# ============================================================================


class WatcherScheduler:
    """Orchestrates watcher execution: scheduling, running, and suppression.

    The scheduler determines which watchers are due to run at a given point
    in time, executes them safely (catching exceptions), applies suppression
    to the resulting findings, and returns structured ``WatcherOutput``
    objects.

    Parameters
    ----------
    registry : WatcherRegistry
        The watcher catalog to pull watchers and configs from.
    suppression_manager : SuppressionManager
        Handles deduplication and cooldown enforcement.
    """

    def __init__(
        self,
        registry: WatcherRegistry,
        suppression_manager: SuppressionManager,
    ) -> None:
        self._registry = registry
        self._suppression = suppression_manager
        self._last_runs: Dict[str, Dict[str, str]] = {}

    # -- Scheduling ---------------------------------------------------------

    def get_watchers_due(
        self,
        business_id: str,
        archetype: str,
        current_time: str,
    ) -> List[Watcher]:
        """Return watchers that should run now for a given business.

        Filters by:

        1. Archetype relevance.
        2. Enabled status (per-business config override wins).
        3. Schedule cadence vs. last run time.

        Event-driven watchers are never returned here -- they must be
        triggered explicitly.

        Parameters
        ----------
        business_id:
            The business to check watchers for.
        archetype:
            The business archetype for relevance filtering.
        current_time:
            ISO-formatted timestamp representing "now".

        Returns
        -------
        List[Watcher]
            Watchers that are due to run.
        """
        try:
            now = datetime.fromisoformat(current_time)
            if now.tzinfo is None:
                now = now.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            now = datetime.now(timezone.utc)

        candidates = self._registry.get_watchers_for_archetype(archetype)
        due: List[Watcher] = []

        for watcher in candidates:
            config = self._registry.get_config(business_id, watcher.name)

            # Must be enabled
            if not config.enabled:
                continue

            schedule = config.schedule_type

            # Event-driven watchers are not scheduled -- skip
            if schedule == WatcherScheduleType.EVENT_DRIVEN.value:
                continue

            # Check if enough time has passed since last run
            last_run_ts = self._get_last_run(business_id, watcher.name)

            if last_run_ts is None:
                # Never run before -- due now
                due.append(watcher)
                continue

            try:
                last_run = datetime.fromisoformat(last_run_ts)
                if last_run.tzinfo is None:
                    last_run = last_run.replace(tzinfo=timezone.utc)
            except (ValueError, TypeError):
                # Unparseable last run -- treat as never run
                due.append(watcher)
                continue

            elapsed = now - last_run

            if schedule == WatcherScheduleType.HOURLY.value:
                if elapsed >= timedelta(hours=1):
                    due.append(watcher)
            elif schedule == WatcherScheduleType.DAILY.value:
                if elapsed >= timedelta(days=1):
                    # If a specific schedule_time is configured, check it
                    if config.schedule_time and not self._is_schedule_time_met(
                        now, config.schedule_time, "daily"
                    ):
                        continue
                    due.append(watcher)
            elif schedule == WatcherScheduleType.WEEKLY.value:
                if elapsed >= timedelta(weeks=1):
                    if config.schedule_time and not self._is_schedule_time_met(
                        now, config.schedule_time, "weekly"
                    ):
                        continue
                    due.append(watcher)

        return due

    # -- Execution ----------------------------------------------------------

    def run_watcher(
        self,
        watcher: Watcher,
        business_profile: Any,
        workspace_state: Any,
    ) -> WatcherOutput:
        """Run a single watcher safely and return structured output.

        - Captures runtime duration.
        - Applies suppression to findings.
        - Enforces ``max_findings_per_run``.
        - Catches and logs any exceptions (does not propagate).

        Parameters
        ----------
        watcher:
            The watcher instance to execute.
        business_profile:
            Business profile passed to the watcher's ``check()`` method.
        workspace_state:
            Workspace state passed to the watcher's ``check()`` method.

        Returns
        -------
        WatcherOutput
            Structured output with findings, suppressed count, errors, and
            runtime duration.
        """
        # Resolve business_id from profile
        business_id = self._extract_business_id(business_profile)
        run_ts = datetime.now(timezone.utc).isoformat()
        config = self._registry.get_config(business_id, watcher.name)

        start = time.monotonic()
        raw_findings: List[WatcherFinding] = []
        errors: List[str] = []

        # Execute the check -- isolate failures
        try:
            raw_findings = watcher.check(business_profile, workspace_state)
        except Exception as exc:
            error_msg = f"Watcher '{watcher.name}' raised {type(exc).__name__}: {exc}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)

        elapsed = time.monotonic() - start

        # Apply suppression
        surfaced: List[WatcherFinding] = []
        suppressed_count = 0

        for finding in raw_findings:
            if self._suppression.should_suppress(finding, config):
                suppressed_count += 1
            else:
                surfaced.append(finding)
                self._suppression.record_finding(finding)

        # Enforce max_findings_per_run to prevent alert fatigue
        if len(surfaced) > config.max_findings_per_run:
            overflow = len(surfaced) - config.max_findings_per_run
            surfaced = surfaced[: config.max_findings_per_run]
            suppressed_count += overflow

        # Record this run
        self._record_last_run(watcher.name, business_id, run_ts)

        return WatcherOutput(
            watcher_name=watcher.name,
            business_id=business_id,
            run_timestamp=run_ts,
            findings=surfaced,
            suppressed_count=suppressed_count,
            errors=errors,
            runtime_seconds=round(elapsed, 3),
        )

    def run_all_due(
        self,
        business_id: str,
        archetype: str,
        business_profile: Any,
        workspace_state: Any,
        current_time: str,
    ) -> List[WatcherOutput]:
        """Get all due watchers, run each sequentially, return all outputs.

        Watchers run sequentially because they may share state through the
        workspace.  Each watcher's failures are isolated -- one crash does
        not prevent others from running.

        Parameters
        ----------
        business_id:
            The business to run watchers for.
        archetype:
            The business archetype for relevance filtering.
        business_profile:
            Business profile passed to each watcher.
        workspace_state:
            Workspace state passed to each watcher.
        current_time:
            ISO timestamp representing "now" for schedule evaluation.

        Returns
        -------
        List[WatcherOutput]
            One output per watcher that was due and executed.
        """
        due_watchers = self.get_watchers_due(business_id, archetype, current_time)
        outputs: List[WatcherOutput] = []

        for watcher in due_watchers:
            # Double-check relevance with the full business profile
            try:
                if not watcher.should_run(business_profile):
                    continue
            except Exception as exc:
                logger.warning(
                    "Watcher '%s' should_run() raised %s: %s -- skipping",
                    watcher.name,
                    type(exc).__name__,
                    exc,
                )
                continue

            output = self.run_watcher(watcher, business_profile, workspace_state)
            outputs.append(output)

        return outputs

    # -- Internal helpers ---------------------------------------------------

    def _record_last_run(
        self,
        watcher_name: str,
        business_id: str,
        timestamp: str,
    ) -> None:
        """Track when a watcher last ran for scheduling purposes."""
        if business_id not in self._last_runs:
            self._last_runs[business_id] = {}
        self._last_runs[business_id][watcher_name] = timestamp

    def _get_last_run(
        self,
        business_id: str,
        watcher_name: str,
    ) -> Optional[str]:
        """Return the ISO timestamp of the last run, or None."""
        return self._last_runs.get(business_id, {}).get(watcher_name)

    @staticmethod
    def _extract_business_id(business_profile: Any) -> str:
        """Extract business_id from a profile object or dict."""
        if hasattr(business_profile, "id"):
            return str(business_profile.id)
        if isinstance(business_profile, dict):
            return str(business_profile.get("id", "unknown"))
        return "unknown"

    @staticmethod
    def _is_schedule_time_met(
        now: datetime,
        schedule_time: str,
        schedule_type: str,
    ) -> bool:
        """Check if the current time matches the configured schedule_time.

        For daily schedules, ``schedule_time`` is ``"HH:MM"`` (24h format).
        For weekly schedules, ``schedule_time`` is ``"dayname_HH:MM"``
        (e.g. ``"monday_06:00"``).

        The match is approximate: the current hour must equal the scheduled
        hour.  This avoids missed runs due to minute-level drift.
        """
        if schedule_type == "daily":
            # Parse "HH:MM"
            try:
                parts = schedule_time.split(":")
                target_hour = int(parts[0])
                return now.hour == target_hour
            except (ValueError, IndexError):
                return True  # Unparseable -- allow the run

        elif schedule_type == "weekly":
            # Parse "dayname_HH:MM" (e.g. "monday_06:00")
            try:
                day_part, time_part = schedule_time.lower().split("_", 1)
                day_names = [
                    "monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday",
                ]
                if day_part not in day_names:
                    return True  # Unrecognized day -- allow the run

                target_weekday = day_names.index(day_part)
                if now.weekday() != target_weekday:
                    return False

                hour_parts = time_part.split(":")
                target_hour = int(hour_parts[0])
                return now.hour == target_hour
            except (ValueError, IndexError):
                return True  # Unparseable -- allow the run

        return True


# ============================================================================
# Convenience factory
# ============================================================================


def create_watcher_finding(
    watcher_name: str,
    business_id: str,
    title: str,
    description: str,
    suppression_key: str,
    *,
    urgency: str = FindingUrgency.SCHEDULED.value,
    severity: str = "medium",
    category: str = "website_health",
    auto_eligible: bool = False,
    proposed_action: Optional[Dict[str, Any]] = None,
    evidence: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> WatcherFinding:
    """Factory function for creating watcher findings with auto-generated IDs.

    Generates a ``wf_`` prefixed UUID-based ID and sets the check timestamp
    to the current UTC time.

    Parameters
    ----------
    watcher_name:
        Name of the watcher that produced this finding.
    business_id:
        The business this finding relates to.
    title:
        Short human-readable summary.
    description:
        Detailed description of what was found.
    suppression_key:
        Key for deduplication (e.g. ``"ssl_expiring_example.com"``).
    urgency:
        ``FindingUrgency`` value.
    severity:
        ``FindingSeverity`` value from ``kai.models.audit``.
    category:
        Finding category.
    auto_eligible:
        Whether the system can act on this without human approval.
    proposed_action:
        Optional action data (as dict).
    evidence:
        Data supporting the finding.
    metadata:
        Additional metadata.

    Returns
    -------
    WatcherFinding
        A fully populated finding instance.
    """
    return WatcherFinding(
        id=f"wf_{uuid.uuid4().hex[:12]}",
        watcher_name=watcher_name,
        business_id=business_id,
        check_timestamp=datetime.now(timezone.utc).isoformat(),
        title=title,
        description=description,
        urgency=urgency,
        severity=severity,
        category=category,
        auto_eligible=auto_eligible,
        proposed_action=proposed_action,
        evidence=evidence if evidence is not None else {},
        suppression_key=suppression_key,
        metadata=metadata if metadata is not None else {},
    )
