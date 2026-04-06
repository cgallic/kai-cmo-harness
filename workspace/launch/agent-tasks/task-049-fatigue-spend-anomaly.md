# Task 049: Build fatigue detection and spend anomaly monitoring

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 8. Paid Media Operations
**Priority:** P2
**Depends on:** 046
**Estimated complexity:** Medium

## Context

Paid campaigns degrade over time. Audiences see the same ad too many times (fatigue), CPCs spike unexpectedly, budgets get consumed too quickly, and underperforming campaigns silently waste money. This module provides continuous monitoring that catches these problems early and generates structured alerts with specific recommended actions. It sits alongside the budget controls (Task 047) and creative variant system (Task 048), completing the paid media safety net. Without this monitoring, a local business could burn through its entire monthly budget on a fatigued campaign before anyone notices.

## Scope

Create `kai/paid_media/monitoring.py` containing FatigueDetector, SpendAnomalyDetector, UnderperformanceDetector, and a unified monitoring alert system.

## Detailed Requirements

### File: `kai/paid_media/monitoring.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: AlertSeverity (str, Enum)**
- `info` — informational, no action needed yet
- `warning` — attention recommended, performance is degrading
- `alert` — action needed soon, clear problem detected
- `critical` — immediate action required, significant waste or failure

**Enum: AlertCategory (str, Enum)**
- `creative_fatigue` — ad creative is tired, audience has seen it too many times
- `spend_anomaly` — spending pattern is abnormal
- `underperformance` — campaign not meeting targets
- `budget_pace` — budget consumption is off-pace
- `zero_activity` — no spend or impressions for extended period
- `quality_degradation` — quality/relevance scores dropping
- `cpc_spike` — sudden cost-per-click increase

**Model: MonitoringAlert**
- `id: str` — format `alert_{uuid_hex[:12]}`
- `category: str` — AlertCategory value
- `severity: str` — AlertSeverity value
- `entity_id: str` — campaign, ad group, or ad ID that triggered the alert
- `entity_type: str` — "campaign", "ad_group", "ad"
- `platform: str`
- `title: str` — short alert title (e.g., "Ad fatigue detected on campaign 'Spring HVAC'")
- `message: str` — detailed alert message with data
- `data: Dict[str, Any]` — supporting data points, default empty dict
- `recommended_action: str` — specific action to take
- `recommended_action_type: Optional[str]` — PaidMediaActionType value if applicable
- `auto_action_eligible: bool = False` — whether the system can take action automatically
- `created_at: str` — ISO timestamp
- `acknowledged: bool = False`
- `acknowledged_at: Optional[str]`
- `resolved: bool = False`
- `resolved_at: Optional[str]`
- `metadata: Dict[str, Any]` — default empty dict

**Model: FatigueIndicators**
- `entity_id: str`
- `platform: str`
- `current_frequency: float` — how many times average user has seen the ad
- `frequency_trend: str` — "increasing", "stable", "decreasing"
- `ctr_current: float` — current CTR
- `ctr_7d_ago: float` — CTR 7 days ago
- `ctr_change_pct: float` — percentage change in CTR
- `cpa_current: float` — current CPA
- `cpa_7d_ago: float` — CPA 7 days ago
- `cpa_change_pct: float` — percentage change in CPA
- `days_running: int` — how many days the creative has been active
- `is_fatigued: bool = False`
- `fatigue_reasons: List[str]` — why fatigue was detected, default empty list

**Model: SpendAnomaly**
- `entity_id: str`
- `platform: str`
- `anomaly_type: str` — "overspend", "underspend", "zero_spend", "cpc_spike", "pace_fast", "pace_slow"
- `expected_value: float` — what was expected
- `actual_value: float` — what actually happened
- `deviation_pct: float` — percentage deviation from expected
- `period: str` — time period of the anomaly (e.g., "2026-04-01", "last_24h", "last_7d")
- `is_anomaly: bool = True`

**Model: PerformanceBenchmark**
- `metric: str` — "ctr", "cpa", "roas", "conversion_rate", "quality_score"
- `platform: str`
- `campaign_type: str` — "search", "display", "social", "video"
- `industry: Optional[str]`
- `benchmark_value: float` — industry/platform benchmark
- `benchmark_source: str` — where the benchmark comes from
- `current_value: float`
- `comparison: str` — "above", "at", "below", "far_below"

**Model: MonitoringSnapshot**
- `timestamp: str` — ISO timestamp
- `campaigns_monitored: int`
- `alerts_generated: int`
- `alerts_by_severity: Dict[str, int]` — severity -> count, default empty dict
- `alerts_by_category: Dict[str, int]` — category -> count, default empty dict
- `top_alerts: List[MonitoringAlert]` — most severe alerts, default empty list
- `overall_health: str` — "healthy", "attention_needed", "action_required", "critical"

**INDUSTRY_BENCHMARKS dict:**

Define benchmark values by platform and industry:
```python
INDUSTRY_BENCHMARKS = {
    "google_search": {
        "default": {"ctr": 0.035, "cpa": 50.0, "conversion_rate": 0.04},
        "legal": {"ctr": 0.025, "cpa": 85.0, "conversion_rate": 0.03},
        "home_services": {"ctr": 0.04, "cpa": 40.0, "conversion_rate": 0.05},
        "dental": {"ctr": 0.03, "cpa": 60.0, "conversion_rate": 0.04},
        "real_estate": {"ctr": 0.035, "cpa": 55.0, "conversion_rate": 0.035},
        "automotive": {"ctr": 0.04, "cpa": 35.0, "conversion_rate": 0.06},
        "ecommerce": {"ctr": 0.025, "cpa": 45.0, "conversion_rate": 0.03},
    },
    "google_display": {
        "default": {"ctr": 0.005, "cpa": 75.0, "conversion_rate": 0.01},
    },
    "meta_ads": {
        "default": {"ctr": 0.01, "cpa": 35.0, "conversion_rate": 0.02, "frequency_cap": 3.0},
        "ecommerce": {"ctr": 0.015, "cpa": 25.0, "conversion_rate": 0.025},
        "lead_gen": {"ctr": 0.008, "cpa": 40.0, "conversion_rate": 0.015},
    },
    "local_services_ads": {
        "default": {"cost_per_lead": 30.0, "lead_valid_rate": 0.6},
        "home_services": {"cost_per_lead": 25.0, "lead_valid_rate": 0.65},
        "legal": {"cost_per_lead": 80.0, "lead_valid_rate": 0.5},
    },
}
```

**Class: FatigueDetector**

Monitors for creative fatigue across campaigns.

Methods:
- `__init__(self, frequency_threshold_display: float = 3.0, frequency_threshold_social: float = 2.0, ctr_decline_threshold_pct: float = 20.0, cpa_increase_threshold_pct: float = 30.0, max_days_unchanged: int = 30)` — set fatigue thresholds

- `check_fatigue(self, entity_id: str, platform: str, performance_history: List[Dict[str, Any]]) -> FatigueIndicators`:
  - `performance_history` is a list of daily performance snapshots: [{"date": str, "impressions": int, "clicks": int, "ctr": float, "conversions": float, "cpa": float, "frequency": float}]
  - Calculate current and 7-day-ago metrics
  - Calculate CTR change: `(ctr_current - ctr_7d_ago) / ctr_7d_ago * 100`
  - Calculate CPA change: `(cpa_current - cpa_7d_ago) / cpa_7d_ago * 100`
  - Detect fatigue when ANY of these conditions are true:
    1. Frequency > frequency_threshold (display: 3/week, social: 2/week)
    2. CTR declining >20% over 7 days
    3. CPA increasing >30% over 7 days
    4. Creative running >30 days unchanged
  - Populate fatigue_reasons with which conditions triggered
  - Return FatigueIndicators

- `generate_fatigue_alerts(self, indicators: FatigueIndicators) -> List[MonitoringAlert]`:
  - For each fatigue reason, generate an appropriate alert
  - Frequency fatigue: severity "warning" to "alert" based on how far over threshold
  - CTR decline: severity "warning" if 20-30%, "alert" if >30%
  - CPA increase: severity "warning" if 30-50%, "alert" if >50%
  - Days running: severity "info" at 25 days, "warning" at 30 days, "alert" at 45 days
  - Recommended actions:
    - Frequency: "Refresh creative or narrow audience. Consider new ad variants."
    - CTR decline: "Test new headlines and images. The current creative is losing effectiveness."
    - CPA increase: "Review targeting and bidding. Creative may need refresh. Consider pausing underperformers."
    - Days running: "Creative has been running for {days} days. Generate new variants to test."

- `get_fatigue_summary(self, all_indicators: List[FatigueIndicators]) -> Dict[str, Any]`:
  - Return: `{"total_monitored": int, "fatigued": int, "at_risk": int, "healthy": int, "most_fatigued": list}`

**Class: SpendAnomalyDetector**

Monitors for unusual spending patterns.

Methods:
- `__init__(self, overspend_threshold_pct: float = 50.0, zero_spend_hours: int = 48, cpc_spike_threshold_pct: float = 50.0, pace_alert_threshold_pct: float = 20.0)` — set anomaly thresholds

- `check_daily_spend(self, entity_id: str, platform: str, daily_budget: float, actual_spend: float) -> Optional[SpendAnomaly]`:
  - If actual_spend > daily_budget * (1 + overspend_threshold_pct/100): return overspend anomaly
  - If actual_spend == 0 and campaign is enabled: return zero_spend anomaly
  - If actual_spend < daily_budget * 0.2 and campaign enabled for >3 days: return underspend anomaly
  - Return None if normal

- `check_spend_velocity(self, entity_id: str, platform: str, monthly_budget: float, current_month_spend: float, day_of_month: int) -> Optional[SpendAnomaly]`:
  - Calculate expected spend so far: `monthly_budget * (day_of_month / 30.4)`
  - Calculate actual vs expected deviation
  - If spending >20% faster than expected (pace_fast): return anomaly
  - If spending >20% slower than expected (pace_slow): return anomaly (might indicate ad issues)
  - If projecting to exhaust budget before month end: return critical anomaly

- `check_cpc_spike(self, entity_id: str, platform: str, current_cpc: float, avg_cpc_30d: float) -> Optional[SpendAnomaly]`:
  - If current_cpc > avg_cpc_30d * (1 + cpc_spike_threshold_pct/100): return cpc_spike anomaly
  - Include deviation percentage

- `check_zero_activity(self, entity_id: str, platform: str, hours_since_last_impression: float) -> Optional[SpendAnomaly]`:
  - If hours_since_last_impression > zero_spend_hours: return zero_activity anomaly
  - Possible causes: "disapproved ads", "budget exhausted", "billing issue", "targeting too narrow"

- `generate_spend_alerts(self, anomalies: List[SpendAnomaly]) -> List[MonitoringAlert]`:
  - Map each anomaly to an alert:
    - overspend: severity "alert", "Daily spend exceeded budget by {pct}%. Possible causes: bid strategy overshoot, competitive auction."
    - zero_spend: severity "alert" (48h) or "critical" (72h+), "No spend detected for {hours} hours. Check ad approval status and billing."
    - cpc_spike: severity "warning" (50-100%) or "alert" (>100%), "CPC spiked {pct}% above 30-day average. Possible increased competition."
    - pace_fast: severity "warning", "Spend is {pct}% ahead of pace. Monthly budget may be exhausted by day {day}."
    - pace_slow: severity "info", "Spend is {pct}% behind pace. Ads may have delivery issues."

**Class: UnderperformanceDetector**

Monitors for campaigns not meeting targets.

Methods:
- `__init__(self, underperformance_days: int = 14)` — how many consecutive days before flagging

- `check_against_target(self, entity_id: str, platform: str, metric: str, target_value: float, current_value: float, days_below_target: int) -> Optional[MonitoringAlert]`:
  - If current_value is below target for >underperformance_days consecutive days, generate alert
  - For ROAS: below is worse (want higher)
  - For CPA: above is worse (want lower)
  - For CTR: below is worse
  - Severity: "warning" if 14-21 days, "alert" if 21-30 days, "critical" if >30 days
  - Recommended action varies by metric:
    - ROAS low: "Campaign ROAS ({current}) is below target ({target}). Review audience targeting, landing page, and offer strength."
    - CPA high: "Campaign CPA (${current}) exceeds target (${target}). Consider tightening targeting, improving ad relevance, or revising bid strategy."
    - CTR low: "Campaign CTR ({current}%) is below target ({target}%). Test new headlines and creative. Current ads may not be resonating."

- `check_against_benchmark(self, entity_id: str, platform: str, campaign_type: str, industry: Optional[str], performance: Dict[str, float]) -> List[PerformanceBenchmark]`:
  - Compare current performance against INDUSTRY_BENCHMARKS
  - Look up benchmarks for the platform + industry (fall back to "default" if industry not found)
  - For each metric with a benchmark: create a PerformanceBenchmark
  - Comparison: "above" if >10% above benchmark, "at" if within 10%, "below" if 10-30% below, "far_below" if >30% below
  - Return list of all comparisons

- `check_quality_scores(self, entity_id: str, platform: str, current_quality_score: Optional[float], previous_quality_score: Optional[float]) -> Optional[MonitoringAlert]`:
  - Google: quality score 1-10
  - If quality_score < 5: generate "alert", "Quality score is low ({score}/10). Improve ad relevance, landing page experience, or expected CTR."
  - If quality_score dropped by 2+ points: generate "warning", "Quality score dropped from {prev} to {current}. Investigate recent changes."

- `generate_underperformance_report(self, campaign_id: str, alerts: List[MonitoringAlert], benchmarks: List[PerformanceBenchmark]) -> Dict[str, Any]`:
  - Compile a structured report: `{"campaign_id": str, "health_score": float (0-100), "alerts": list, "benchmark_comparison": list, "priority_actions": list, "summary": str}`
  - health_score: 100 minus penalties (each alert -10 to -25 based on severity, each "far_below" benchmark -10)
  - priority_actions: ordered list of what to fix first

**Class: PaidMediaMonitor**

Unified monitoring coordinator that runs all detectors.

Methods:
- `__init__(self, fatigue_detector: Optional[FatigueDetector] = None, spend_detector: Optional[SpendAnomalyDetector] = None, performance_detector: Optional[UnderperformanceDetector] = None)` — initialize with detectors (create defaults if None)

- `run_monitoring_cycle(self, campaigns: List[Dict[str, Any]], performance_data: Dict[str, List[Dict[str, Any]]], budget_data: Dict[str, Dict[str, Any]], targets: Dict[str, Dict[str, float]]) -> MonitoringSnapshot`:
  - Run all detectors across all campaigns
  - `campaigns`: list of campaign dicts with id, platform, status, budget, industry
  - `performance_data`: campaign_id -> list of daily performance snapshots
  - `budget_data`: campaign_id -> {daily_budget, monthly_budget, current_month_spend, day_of_month}
  - `targets`: campaign_id -> {metric: target_value} for target-based checks
  - Aggregate all alerts, deduplicate, sort by severity
  - Determine overall_health based on alert count and severity
  - Return MonitoringSnapshot

- `get_actionable_alerts(self, snapshot: MonitoringSnapshot) -> List[MonitoringAlert]`:
  - Filter to alerts that are "warning" severity or higher and not yet acknowledged
  - Sort by severity (critical first) then by created_at

- `acknowledge_alert(self, alert_id: str) -> MonitoringAlert`:
  - Mark an alert as acknowledged

- `resolve_alert(self, alert_id: str) -> MonitoringAlert`:
  - Mark an alert as resolved

**Helper functions (module-level):**

- `generate_alert_id() -> str` — return `alert_{uuid.uuid4().hex[:12]}`
- `calculate_pct_change(old_value: float, new_value: float) -> float` — return `((new_value - old_value) / old_value) * 100` if old_value != 0, else 0.0
- `determine_severity(deviation_pct: float, thresholds: Dict[str, float]) -> str` — given deviation and threshold dict {"warning": 20, "alert": 50, "critical": 100}, return severity level
- `get_benchmark(platform: str, metric: str, industry: Optional[str] = None) -> Optional[float]` — look up benchmark from INDUSTRY_BENCHMARKS
- `calculate_health_score(alerts: List[MonitoringAlert]) -> float` — 100 minus severity penalties: info=-2, warning=-5, alert=-15, critical=-25. Clamp to 0-100.

## Output Files

- `kai/paid_media/monitoring.py`
- `kai/paid_media/__init__.py` (update to include monitoring exports)

## Acceptance Criteria

- [ ] `AlertSeverity` enum has 4 values, `AlertCategory` enum has 7 values
- [ ] `MonitoringAlert` model has all 16 fields including severity, recommended_action, and resolution tracking
- [ ] `FatigueIndicators` model has all 12 fields
- [ ] `SpendAnomaly` model has all 8 fields
- [ ] `PerformanceBenchmark` model has all 8 fields
- [ ] `MonitoringSnapshot` model has all 7 fields
- [ ] `INDUSTRY_BENCHMARKS` dict has entries for google_search (7 industries), google_display, meta_ads (3 types), and local_services_ads (3 types)
- [ ] `FatigueDetector.check_fatigue()` checks all 4 fatigue conditions with correct thresholds
- [ ] `FatigueDetector.generate_fatigue_alerts()` produces alerts with specific recommended actions
- [ ] `SpendAnomalyDetector` has all 5 check methods covering overspend, zero spend, CPC spike, velocity, and zero activity
- [ ] `SpendAnomalyDetector.check_spend_velocity()` correctly projects budget exhaustion
- [ ] `UnderperformanceDetector.check_against_benchmark()` compares against INDUSTRY_BENCHMARKS
- [ ] `UnderperformanceDetector.check_quality_scores()` detects both low scores and score drops
- [ ] `PaidMediaMonitor.run_monitoring_cycle()` runs all detectors and aggregates alerts
- [ ] `PaidMediaMonitor.get_actionable_alerts()` filters and sorts correctly
- [ ] All 5 module-level helper functions exist
- [ ] `calculate_pct_change()` handles zero division
- [ ] `calculate_health_score()` correctly penalizes by severity
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/models/paid_media.py` (created by Task 046) — Campaign, AdPerformance, BudgetGuard models
- `kai/paid_media/controls.py` (created by Task 047) — BudgetController for budget monitoring integration
- `kai/paid_media/variants.py` (created by Task 048) — CreativeInventory freshness for fatigue cross-reference
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `knowledge/playbooks/ad-campaign-management.md` — campaign optimization guidance
- `knowledge/playbooks/ad-creative-best-practices.md` — creative fatigue guidance
- `CLAUDE.md` — full project context
