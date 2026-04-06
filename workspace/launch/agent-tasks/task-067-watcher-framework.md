# Task 067: Build watcher framework core

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 12. Background Automation and Watcher Loops
**Priority:** P1
**Depends on:** 013, 022
**Estimated complexity:** Large

## Context

Watchers are background monitoring loops that continuously check for marketing issues, opportunities, and anomalies. They run on schedules (daily, weekly) or are triggered by events, and produce findings that can optionally include proposed actions for automatic or operator-approved resolution. The watcher framework is the infrastructure that manages registration, scheduling, deduplication, and output formatting for all individual watchers (Tasks 068-071). Without this framework, each watcher would need its own scheduling, throttling, and output logic. Watchers are the "always on" layer that transforms Kai from a tool you invoke into a system that proactively monitors and recommends.

## Scope

Create `kai/watchers/framework.py` containing the abstract Watcher base class, WatcherFinding model, WatcherScheduler, WatcherRegistry, and deduplication/suppression logic.

## Detailed Requirements

### File: `kai/watchers/__init__.py`
- Module docstring explaining the watcher system
- Export key classes

### File: `kai/watchers/framework.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: WatcherScheduleType**
- `daily` — runs once per day
- `weekly` — runs once per week
- `event_driven` — triggered by specific events
- `hourly` — runs every hour (for critical monitoring only)

**Enum: FindingUrgency**
- `immediate` — needs attention now (e.g., site down, tracking broken)
- `soon` — should be addressed within 24-48 hours
- `scheduled` — can be addressed in next planning cycle
- `informational` — FYI, no action required

**Model: WatcherConfig**
- `watcher_name: str`
- `enabled: bool` — whether this watcher is active
- `schedule_type: str` — WatcherScheduleType enum value
- `schedule_time: Optional[str]` — for daily: "06:00" (24h format); for weekly: "monday_06:00"
- `archetype_relevance: List[str]` — which archetypes this watcher is relevant for (empty = all)
- `max_findings_per_run: int` — prevent alert fatigue (default 10)
- `suppression_window_days: int` — don't re-alert same issue within this many days (default 7)
- `cooldown_after_action_days: int` — after an action is taken, suppress related findings for this many days (default 14)
- `custom_config: Dict[str, Any]` — watcher-specific configuration overrides

**Model: WatcherFinding**
- `id: str` — format `wf_{uuid_hex[:12]}`
- `watcher_name: str` — which watcher produced this finding
- `business_id: str`
- `check_timestamp: str` — ISO timestamp when this check ran
- `title: str` — short human-readable title (e.g., "Website SSL certificate expiring in 7 days")
- `description: str` — detailed description of what was found
- `urgency: str` — FindingUrgency enum value
- `severity: str` — reuse FindingSeverity from audit.py: "critical", "high", "medium", "low"
- `category: str` — reuse AuditCategory or extend: "website_health", "local_visibility", "social_freshness", "ad_performance", "lead_followup", "content_freshness"
- `auto_eligible: bool` — can the system act on this without human approval?
- `proposed_action: Optional[Dict[str, Any]]` — optional ProposedAction data (as dict to avoid circular imports)
- `evidence: Dict[str, Any]` — data supporting the finding (e.g., {"current_value": 0, "expected_value": 150, "metric": "daily_sessions"})
- `suppression_key: str` — key for dedup/suppression (e.g., "ssl_expiring_{domain}" — same key = same issue)
- `metadata: Dict[str, Any]`

**Model: WatcherOutput**
- `watcher_name: str`
- `business_id: str`
- `run_timestamp: str`
- `findings: List[WatcherFinding]`
- `suppressed_count: int` — how many findings were suppressed by dedup
- `errors: List[str]` — any errors encountered during the run
- `runtime_seconds: float` — how long the watcher took to run

**Abstract Class: Watcher**
- `name: str` — unique watcher name
- `description: str` — what this watcher monitors
- `schedule_type: str` — default schedule for this watcher
- `archetype_relevance: List[str]` — which archetypes this is relevant for
- `enabled: bool` — default True
- `check(self, business_profile: Any, workspace_state: Any) -> List[WatcherFinding]`:
  - Abstract method — subclasses implement the actual checking logic
  - Receives the business profile and workspace state for context
  - Returns a list of WatcherFinding objects
- `should_run(self, business_profile: Any) -> bool`:
  - Check if this watcher is relevant for the given business
  - Default implementation: check if business archetype is in archetype_relevance (or archetype_relevance is empty = run for all)
  - Subclasses can override for more specific logic
- `get_default_config(self) -> WatcherConfig`:
  - Return a default WatcherConfig for this watcher
  - Subclasses should override to set appropriate defaults

**Class: WatcherRegistry**
- `_watchers: Dict[str, Watcher]` — registered watchers by name
- `_configs: Dict[str, Dict[str, WatcherConfig]]` — per-business config overrides: {business_id: {watcher_name: config}}
- `register(self, watcher: Watcher)`:
  - Add a watcher to the registry
  - Raise ValueError if a watcher with the same name is already registered
- `unregister(self, watcher_name: str)`:
  - Remove a watcher from the registry
- `get_watcher(self, name: str) -> Optional[Watcher]`:
  - Return a watcher by name, or None
- `list_watchers(self) -> List[Watcher]`:
  - Return all registered watchers
- `get_watchers_for_archetype(self, archetype: str) -> List[Watcher]`:
  - Return watchers relevant to the given archetype
- `set_config(self, business_id: str, watcher_name: str, config: WatcherConfig)`:
  - Set per-business configuration override for a watcher
- `get_config(self, business_id: str, watcher_name: str) -> WatcherConfig`:
  - Return per-business config if set, otherwise return watcher's default config
- `enable_watcher(self, business_id: str, watcher_name: str)`:
  - Enable a watcher for a specific business
- `disable_watcher(self, business_id: str, watcher_name: str)`:
  - Disable a watcher for a specific business

**Class: SuppressionManager**
- `_suppressed: Dict[str, Dict[str, str]]` — {business_id: {suppression_key: last_finding_timestamp}}
- `_action_cooldowns: Dict[str, Dict[str, str]]` — {business_id: {suppression_key: action_timestamp}}
- `should_suppress(self, finding: WatcherFinding, config: WatcherConfig) -> bool`:
  - Check if this finding's suppression_key was already seen within the suppression_window_days
  - Check if a related action was taken within the cooldown_after_action_days
  - Return True if should suppress, False otherwise
- `record_finding(self, finding: WatcherFinding)`:
  - Record that this finding was produced (for future suppression checks)
- `record_action_taken(self, business_id: str, suppression_key: str)`:
  - Record that an action was taken for this issue (triggers cooldown)
- `clear_expired(self)`:
  - Remove suppression entries older than the maximum suppression window (cleanup)
- `_is_within_window(self, timestamp: str, window_days: int) -> bool`:
  - Helper to check if a timestamp is within N days of now

**Class: WatcherScheduler**
- `__init__(self, registry: WatcherRegistry, suppression_manager: SuppressionManager)`
- `get_watchers_due(self, business_id: str, archetype: str, current_time: str) -> List[Watcher]`:
  - Given a point in time, return which watchers should run now
  - Check schedule_type, schedule_time, and last run time
  - Filter by archetype relevance
  - Only return enabled watchers
- `run_watcher(self, watcher: Watcher, business_profile: Any, workspace_state: Any) -> WatcherOutput`:
  - Run a single watcher's check method
  - Apply suppression to findings
  - Track runtime
  - Catch and log any exceptions (do not let one watcher crash others)
  - Return WatcherOutput with findings (after suppression) and suppressed count
- `run_all_due(self, business_id: str, archetype: str, business_profile: Any, workspace_state: Any, current_time: str) -> List[WatcherOutput]`:
  - Get all due watchers, run each, return all outputs
  - Run sequentially (not parallel — watchers may share state)
- `_record_last_run(self, watcher_name: str, business_id: str, timestamp: str)`:
  - Track when each watcher last ran for scheduling purposes
- `_last_runs: Dict[str, Dict[str, str]]` — {business_id: {watcher_name: last_run_timestamp}}

## Output Files

- `kai/watchers/__init__.py`
- `kai/watchers/framework.py`

## Acceptance Criteria

- All files parse as valid Python
- `Watcher` is a proper abstract class with abstract `check()` method
- `WatcherRegistry` correctly manages watcher lifecycle (register, unregister, enable, disable)
- Per-business config overrides work correctly (return override if set, default otherwise)
- `SuppressionManager` correctly prevents duplicate findings within the suppression window
- Cooldown after action correctly suppresses findings for the configured duration
- `WatcherScheduler.run_watcher()` catches exceptions and returns them in WatcherOutput.errors (does not propagate)
- `get_watchers_due()` correctly filters by schedule, archetype, and enabled status
- WatcherFinding has a `suppression_key` for dedup and an `auto_eligible` flag for automatic action
- All models use SerializableModel mixin
- No external dependencies beyond stdlib

## Reference Materials

- `kai/runtime/audit.py` — AuditFinding (similar structure to WatcherFinding), FindingSeverity, AuditCategory
- `kai/runtime/actions.py` — ProposedAction (used in WatcherFinding.proposed_action)
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/runtime/business_profile.py` — BusinessProfile (passed to watchers)
- `kai/runtime/store.py` — workspace state patterns
