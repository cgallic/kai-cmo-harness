# Task 059: Build anomaly detection and confidence scoring

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 10. Analytics, Attribution, and Monitoring
**Priority:** P2
**Depends on:** 056
**Estimated complexity:** Medium

## Context

Marketing metrics are noisy — traffic fluctuates, campaigns come and go, and seasonal patterns create natural variation. The anomaly detection layer must distinguish genuine problems (a tracking script broke, an ad got disapproved, a negative review tanked conversions) from normal noise. This layer feeds directly into the watcher system (workstream 12) which uses anomaly alerts to propose corrective actions, and into the attribution system (058) where confidence scoring determines how much credit an action gets for observed changes.

## Scope

Create `kai/analytics/anomaly_detection.py` containing the AnomalyDetector class with multiple detection strategies, the AnomalyAlert model, and confidence scoring utilities for metric changes.

## Detailed Requirements

### File: `kai/analytics/anomaly_detection.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: AnomalySeverity**
- `info` — unusual but not necessarily problematic
- `warning` — notable deviation, investigate when convenient
- `critical` — significant deviation requiring immediate attention

**Enum: AnomalyType**
- `statistical_outlier` — value outside expected range
- `trend_break` — established trend reversed
- `flatline` — normally active metric went to zero or near-zero
- `spike` — sudden increase well above average
- `drop` — sudden decrease well below average

**Model: AnomalyAlert**
- `id: str` — format `alert_{uuid_hex[:12]}`
- `metric_name: str` — which metric triggered the alert
- `anomaly_type: str` — AnomalyType enum value
- `severity: str` — AnomalySeverity enum value
- `detected_at: str` — ISO timestamp
- `value: float` — the observed value that triggered the alert
- `expected_range_low: float` — lower bound of expected range
- `expected_range_high: float` — upper bound of expected range
- `deviation_magnitude: float` — how far outside expected range (as multiple of std dev, or percent deviation)
- `possible_causes: List[str]` — suggested reasons for the anomaly
- `recommended_investigation: List[str]` — specific things to check
- `related_metrics: List[str]` — other metrics that may be affected
- `suppressed: bool` — True if this alert was suppressed by throttling
- `metadata: Dict[str, Any]`

**Model: MetricTimeSeries**
- `metric_name: str`
- `values: List[float]` — ordered time series values (oldest first)
- `dates: List[str]` — corresponding ISO date strings
- `source: str` — which connector produced this data

**Model: SeasonalPattern**
- `metric_name: str`
- `day_of_week_factors: Dict[int, float]` — 0=Monday through 6=Sunday, multiplier (1.0 = average)
- `month_factors: Dict[int, float]` — 1=January through 12=December, multiplier
- `known_events: List[Dict[str, Any]]` — list of {date, event_name, expected_impact_pct} for known events (holidays, industry events)

**Class: AnomalyDetector**
- `__init__(self, sensitivity: float = 2.0, min_data_points: int = 14)` — sensitivity is the number of standard deviations for statistical outlier detection; min_data_points is minimum history needed
- `detect_anomalies(self, time_series: MetricTimeSeries, seasonal_pattern: Optional[SeasonalPattern] = None) -> List[AnomalyAlert]` — run all detection methods and return combined alerts, deduplicated
- `_detect_statistical_outlier(self, time_series: MetricTimeSeries, window: int = 30) -> List[AnomalyAlert]`:
  - Calculate rolling mean and standard deviation over `window` days
  - Flag values outside mean +/- (sensitivity * std_dev)
  - Return AnomalyAlert with anomaly_type = "statistical_outlier"
  - If seasonal_pattern provided, adjust expected range by seasonal factor
- `_detect_trend_break(self, time_series: MetricTimeSeries, short_window: int = 7, long_window: int = 30) -> List[AnomalyAlert]`:
  - Calculate slope of short window (last 7 days) and long window (last 30 days)
  - If slopes have opposite signs and short slope magnitude > 0.5 * long slope magnitude, flag as trend break
  - Return AnomalyAlert with anomaly_type = "trend_break"
- `_detect_flatline(self, time_series: MetricTimeSeries, zero_threshold: float = 0.01) -> List[AnomalyAlert]`:
  - Check if the last 3+ consecutive values are at or near zero when the 30-day average is > zero_threshold
  - Return AnomalyAlert with anomaly_type = "flatline", severity = "critical"
- `_detect_spike(self, time_series: MetricTimeSeries, spike_threshold: float = 2.0) -> List[AnomalyAlert]`:
  - Flag when latest value > spike_threshold * daily_average (over last 30 days)
  - Return AnomalyAlert with anomaly_type = "spike"
- `_detect_drop(self, time_series: MetricTimeSeries, drop_threshold: float = 0.5) -> List[AnomalyAlert]`:
  - Flag when latest value < drop_threshold * daily_average (over last 30 days)
  - Return AnomalyAlert with anomaly_type = "drop"
- `_adjust_for_seasonality(self, value: float, date: str, pattern: SeasonalPattern) -> float`:
  - Divide value by the seasonal factor for its day-of-week and month to get the seasonally-adjusted value
  - Check known_events list for date match, adjust accordingly
- `_suggest_possible_causes(self, anomaly_type: str, metric_name: str) -> List[str]`:
  - Return a list of common causes based on anomaly type and metric category
  - E.g., for flatline + sessions → ["Tracking script may have been removed", "DNS issue", "Server downtime"]
  - E.g., for spike + ad_spend → ["Budget cap removed or increased", "New campaign launched", "Bidding strategy change"]
  - E.g., for drop + conversions → ["Form broken", "Landing page changed", "Offer expired", "Pricing changed"]
  - Cover at least 5 metric categories: traffic, conversions, ad_spend, reviews, phone_calls

**Class: ConfidenceScorer**
- `score_metric_change(self, metric_name: str, before_value: float, after_value: float, concurrent_changes: int, days_elapsed: int, external_factors: List[str], seasonal_adjusted: bool = False) -> Dict[str, Any]`:
  - Returns dict with: confidence_level (str), confidence_score (float 0-1), reasoning (list of str)
  - Base score: 0.8
  - Penalties:
    - -0.1 per concurrent change (cap at -0.4)
    - -0.15 per external factor (cap at -0.3)
    - -0.2 if days_elapsed < 7
    - -0.1 if days_elapsed < 14
    - -0.05 if not seasonal_adjusted
  - Bonuses:
    - +0.1 if days_elapsed >= 30
    - +0.05 if zero concurrent changes
    - +0.05 if seasonal_adjusted
  - Floor at 0.0, cap at 1.0
  - Map to level: >= 0.7 → "high", >= 0.45 → "medium", >= 0.2 → "low", < 0.2 → "insufficient"
  - Reasoning: list of strings explaining each adjustment

## Output Files

- `kai/analytics/anomaly_detection.py`

## Acceptance Criteria

- File parses as valid Python
- `AnomalyDetector` implements all five detection methods with clear logic
- Statistical outlier detection uses proper rolling mean/std calculation (handle edge case of insufficient data gracefully)
- Trend break detection correctly compares short-window and long-window slopes
- Flatline detection checks consecutive near-zero values, not just the latest value
- Spike and drop detection use threshold multipliers against the rolling average
- Seasonality adjustment divides by the combined day-of-week and month factor
- `_suggest_possible_causes` covers at least 5 metric categories with 3+ causes each
- `ConfidenceScorer` implements the exact penalty/bonus rules described above
- All models use the `SerializableModel` mixin
- No external dependencies (all math is stdlib — no numpy/pandas)
- Helper functions handle edge cases: empty series, series shorter than window, zero standard deviation

## Reference Materials

- `kai/connectors/analytics/base.py` (Task 056) — MetricPoint, source connectors
- `kai/analytics/kpi_models.py` (Task 057) — KPIDefinition, which metrics exist
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/runtime/audit.py` — enum conventions
