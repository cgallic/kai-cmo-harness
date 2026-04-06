# Task 070: Build ad fatigue and spend anomaly watchers

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 12. Background Automation and Watcher Loops
**Priority:** P2
**Depends on:** 067
**Estimated complexity:** Medium

## Context

Paid advertising budgets are the most financially sensitive part of marketing operations. Ad fatigue (same creative shown too many times), runaway spend (budget caps accidentally removed), and underperforming campaigns can waste thousands of dollars in days. These watchers monitor ad performance continuously and flag issues before they become expensive problems. For local service businesses, where marketing budgets are tight, catching a $50/day overspend or a campaign with zero conversions early can mean the difference between profitable and unprofitable marketing.

## Scope

Create `kai/watchers/ad_spend.py` containing three concrete watcher implementations: AdFatigueWatcher (daily), SpendAnomalyWatcher (daily), and ROASWatcher (weekly).

## Detailed Requirements

### File: `kai/watchers/ad_spend.py`

Import and extend the `Watcher` abstract class from `kai/watchers/framework.py`.

**Class: AdFatigueWatcher(Watcher)**
- `name = "ad_fatigue"`
- `description = "Monitors ad creative fatigue indicators: frequency, CTR decline, and creative age"`
- `schedule_type = "daily"`
- `archetype_relevance = []` — relevant for any archetype running ads
- `FATIGUE_THRESHOLDS`:
  - `frequency_warning`: 3.0 (average times a user has seen the ad)
  - `frequency_critical`: 5.0
  - `ctr_decline_warning`: 0.20 (20% CTR decline from initial performance)
  - `ctr_decline_critical`: 0.40 (40% CTR decline)
  - `creative_age_warning`: 21 (days since creative launched)
  - `creative_age_critical`: 45 (days)
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - For each active ad campaign, check fatigue indicators
- `_check_frequency(self, campaign_id: str, campaign_name: str, frequency: float) -> Optional[WatcherFinding]`:
  - Compare frequency against thresholds
  - Title: f"Ad frequency too high on '{campaign_name}' ({frequency:.1f}x)"
  - Evidence: {campaign_id, campaign_name, current_frequency, threshold, platform}
  - Proposed action: audience expansion, creative refresh, or frequency cap adjustment
  - auto_eligible: False (requires creative decision)
- `_check_ctr_decline(self, campaign_id: str, campaign_name: str, current_ctr: float, initial_ctr: float) -> Optional[WatcherFinding]`:
  - Calculate CTR decline percentage
  - Title: f"CTR declining on '{campaign_name}' (down {decline_pct:.0f}% from launch)"
  - Evidence: {campaign_id, campaign_name, current_ctr, initial_ctr, decline_pct, days_running}
  - Proposed action: new creative variants, audience refresh, bid adjustment
- `_check_creative_age(self, campaign_id: str, campaign_name: str, creative_launch_date: str) -> Optional[WatcherFinding]`:
  - Calculate days since creative launched
  - Title: f"Same creative running for {days} days on '{campaign_name}'"
  - Evidence: {campaign_id, campaign_name, creative_launch_date, days_running}
  - Proposed action: generate new creative variants using variant engine (Task 084)
  - auto_eligible: True (system can generate creative variants for review)
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="daily", schedule_time="07:00"
  - suppression_window_days=3 (re-check frequently for active ads)
  - cooldown_after_action_days=7 (after creative refresh, wait before re-alerting)

**Class: SpendAnomalyWatcher(Watcher)**
- `name = "spend_anomaly"`
- `description = "Monitors daily ad spend against budgets and flags overspend, underspend, and cost spikes"`
- `schedule_type = "daily"`
- `archetype_relevance = []` — relevant for any archetype with ad spend
- `SPEND_THRESHOLDS`:
  - `overspend_warning`: 1.2 (120% of daily budget)
  - `overspend_critical`: 1.5 (150% of daily budget)
  - `projected_monthly_warning`: 1.1 (110% of monthly cap)
  - `zero_spend_check`: True (flag campaigns with 0 spend)
  - `cpc_spike_threshold`: 2.0 (200% of 7-day average CPC)
  - `cpa_spike_threshold`: 2.0 (200% of 7-day average CPA)
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Check daily spend vs budget, projected monthly spend, zero-spend campaigns, cost spikes
- `_check_daily_spend(self, campaign_id: str, campaign_name: str, daily_spend: float, daily_budget: float) -> Optional[WatcherFinding]`:
  - Compare spend to budget
  - If spend > overspend_critical * budget: severity="critical", urgency="immediate"
  - If spend > overspend_warning * budget: severity="warning", urgency="soon"
  - Title: f"Overspend alert: '{campaign_name}' spent ${daily_spend:.2f} vs ${daily_budget:.2f} budget"
  - Evidence: {campaign_id, campaign_name, daily_spend, daily_budget, overspend_pct, platform}
  - Proposed action: reduce daily budget, pause campaign if critical
  - auto_eligible: True for budget reduction (within safe limits)
- `_check_projected_monthly(self, total_monthly_spend: float, monthly_cap: float, days_remaining: int) -> Optional[WatcherFinding]`:
  - Calculate projected monthly spend based on daily run rate
  - If projected > monthly_cap * projected_monthly_warning: severity="warning"
  - Title: f"Projected monthly spend ${projected:.2f} exceeds cap ${monthly_cap:.2f}"
  - Evidence: {current_monthly_spend, daily_run_rate, projected_monthly, monthly_cap, days_remaining}
  - Proposed action: reduce daily budgets proportionally to stay within cap
- `_check_zero_spend(self, campaign_id: str, campaign_name: str, status: str) -> Optional[WatcherFinding]`:
  - Flag campaigns that are active but have zero spend (may indicate disapproved ads)
  - Severity: "warning", urgency="soon"
  - Title: f"Zero spend on active campaign '{campaign_name}' — possible ad disapproval"
  - Evidence: {campaign_id, campaign_name, status, days_zero_spend, possible_reason}
  - Proposed action: check ad disapproval status, review ad copy for policy violations
- `_check_cost_spikes(self, campaign_id: str, campaign_name: str, metric_name: str, current_value: float, average_value: float) -> Optional[WatcherFinding]`:
  - Check CPC and CPA against 7-day averages
  - If current > threshold * average: severity="warning"
  - Title: f"{metric_name} spike on '{campaign_name}': ${current_value:.2f} vs ${average_value:.2f} avg"
  - Evidence: {campaign_id, campaign_name, metric_name, current_value, average_value, spike_multiplier}
  - Proposed action: bid adjustment, audience review, competitive landscape check
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="daily", schedule_time="08:00"
  - suppression_window_days=1 (re-check daily for spend issues)
  - max_findings_per_run=20

**Class: ROASWatcher(Watcher)**
- `name = "roas_monitor"`
- `description = "Monitors return on ad spend and flags underperforming campaigns and diminishing returns"`
- `schedule_type = "weekly"`
- `archetype_relevance = []` — relevant for all archetypes with ad spend
- `ROAS_THRESHOLDS`:
  - `below_target_days`: 14 (flag if ROAS below target for 14+ days)
  - `negative_roi_days`: 7 (flag if ROI is negative for 7+ days)
  - `diminishing_returns_pct`: 0.20 (flag if ROAS declining 20%+ while spend increasing)
- `check(self, business_profile, workspace_state) -> List[WatcherFinding]`:
  - Check per-campaign ROAS, negative ROI campaigns, diminishing returns
- `_check_roas_below_target(self, campaign_id: str, campaign_name: str, current_roas: float, target_roas: float, days_below: int) -> Optional[WatcherFinding]`:
  - If below target for >= ROAS_THRESHOLDS["below_target_days"]: severity="high"
  - Title: f"ROAS below target on '{campaign_name}' for {days_below} days ({current_roas:.1f}x vs {target_roas:.1f}x target)"
  - Evidence: {campaign_id, campaign_name, current_roas, target_roas, days_below, total_spend_in_period}
  - Proposed action: pause campaign, reallocate budget to better performers, or refresh creative
- `_check_negative_roi(self, campaign_id: str, campaign_name: str, spend: float, revenue: float, days_negative: int) -> Optional[WatcherFinding]`:
  - ROI < 0 (spend > revenue) for >= negative_roi_days
  - Severity: "critical" if spend > $100/day, "high" otherwise
  - Title: f"Negative ROI on '{campaign_name}' for {days_negative} days (spent ${spend:.2f}, earned ${revenue:.2f})"
  - Evidence: {campaign_id, campaign_name, spend, revenue, roi, days_negative}
  - Proposed action: pause campaign immediately if critical, reduce budget if high
  - auto_eligible: True for pause recommendation on critical
- `_check_diminishing_returns(self, campaign_id: str, campaign_name: str, spend_trend: List[float], roas_trend: List[float]) -> Optional[WatcherFinding]`:
  - Detect pattern: spend increasing but ROAS decreasing
  - Title: f"Diminishing returns on '{campaign_name}': spend up but ROAS declining"
  - Evidence: {campaign_id, campaign_name, spend_trend_direction, roas_trend_direction, optimal_spend_estimate}
  - Proposed action: reduce spend to estimated optimal level, test new audiences
- `get_default_config(self) -> WatcherConfig`:
  - schedule_type="weekly", schedule_time="monday_09:00"
  - suppression_window_days=7
  - max_findings_per_run=10

## Output Files

- `kai/watchers/ad_spend.py`

## Acceptance Criteria

- File parses as valid Python
- All three watcher classes properly extend the abstract `Watcher` base class
- AdFatigueWatcher checks frequency, CTR decline, and creative age with realistic thresholds
- SpendAnomalyWatcher checks daily spend vs budget, projected monthly, zero-spend, and cost spikes
- ROASWatcher checks ROAS vs target, negative ROI, and diminishing returns
- Overspend finding correctly triggers severity="critical" at 150% threshold and "warning" at 120%
- Zero-spend detection correctly identifies potentially disapproved ads
- Diminishing returns detection compares spend trend to ROAS trend
- auto_eligible is True only for safe automated actions (budget reduction within limits, pause recommendation)
- All findings have specific evidence dicts with concrete metric values
- All suppression_key values are unique and meaningful per issue

## Reference Materials

- `kai/watchers/framework.py` (Task 067) — Watcher base class, WatcherFinding
- `kai/connectors/analytics/ad_metrics.py` (Task 056) — ad metric data sources
- `kai/analytics/anomaly_detection.py` (Task 059) — anomaly detection patterns
- `knowledge/checklists/paid-acquisition-checklist.md` — ad performance benchmarks
- `harness/references/google-ads-policy-reference.md` — Google Ads disapproval reasons
