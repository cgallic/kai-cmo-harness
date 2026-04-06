"""Anomaly detection and confidence scoring for marketing metrics.

Detects genuine metric anomalies (tracking breakage, ad disapprovals,
conversion drops) versus normal noise.  Feeds into the watcher system
(workstream 12) for corrective-action proposals and into the attribution
system (task 058) where confidence scoring determines how much credit a
marketing action receives for observed changes.

Detection strategies:
    - Statistical outlier (rolling mean +/- N std-dev)
    - Trend break (short-window vs long-window slope divergence)
    - Flatline (consecutive near-zero when historically active)
    - Spike (sudden increase above threshold multiple)
    - Drop (sudden decrease below threshold fraction)

All math is stdlib-only -- no numpy, pandas, or scipy required.

Usage::

    from kai.analytics.anomaly_detection import (
        AnomalyDetector,
        ConfidenceScorer,
        MetricTimeSeries,
        SeasonalPattern,
        AnomalyAlert,
    )

    series = MetricTimeSeries(
        metric_name="sessions",
        values=[100, 110, 95, 105, 0, 0, 0],
        dates=["2026-03-25", "2026-03-26", "2026-03-27",
               "2026-03-28", "2026-03-29", "2026-03-30", "2026-03-31"],
        source="ga4",
    )
    detector = AnomalyDetector(sensitivity=2.0, min_data_points=14)
    alerts = detector.detect_anomalies(series)

    scorer = ConfidenceScorer()
    result = scorer.score_metric_change(
        metric_name="conversions",
        before_value=50.0,
        after_value=75.0,
        concurrent_changes=2,
        days_elapsed=21,
        external_factors=["holiday_weekend"],
    )
"""

from __future__ import annotations

import math
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from kai.runtime.models import SerializableModel


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class AnomalySeverity(str, Enum):
    """Alert severity level."""

    INFO = "info"          # Unusual but not necessarily problematic
    WARNING = "warning"    # Notable deviation, investigate when convenient
    CRITICAL = "critical"  # Significant deviation requiring immediate attention


class AnomalyType(str, Enum):
    """Classification of the detected anomaly."""

    STATISTICAL_OUTLIER = "statistical_outlier"  # Value outside expected range
    TREND_BREAK = "trend_break"                  # Established trend reversed
    FLATLINE = "flatline"                        # Active metric went to zero
    SPIKE = "spike"                              # Sudden increase well above avg
    DROP = "drop"                                # Sudden decrease well below avg


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


def _new_alert_id() -> str:
    """Generate a unique alert identifier."""
    return f"alert_{uuid.uuid4().hex[:12]}"


@dataclass
class AnomalyAlert(SerializableModel):
    """A single anomaly alert raised against a marketing metric.

    Attributes:
        id: Unique alert identifier, format ``alert_{uuid_hex[:12]}``.
        metric_name: Which metric triggered the alert.
        anomaly_type: AnomalyType enum value string.
        severity: AnomalySeverity enum value string.
        detected_at: ISO timestamp when the anomaly was detected.
        value: The observed value that triggered the alert.
        expected_range_low: Lower bound of the expected range.
        expected_range_high: Upper bound of the expected range.
        deviation_magnitude: How far outside expected range (as multiple
            of standard deviation, or percent deviation).
        possible_causes: Suggested reasons for the anomaly.
        recommended_investigation: Specific things to check.
        related_metrics: Other metrics that may be affected.
        suppressed: True if this alert was suppressed by throttling.
        metadata: Arbitrary additional context.
    """

    id: str = ""
    metric_name: str = ""
    anomaly_type: str = ""
    severity: str = ""
    detected_at: str = ""
    value: float = 0.0
    expected_range_low: float = 0.0
    expected_range_high: float = 0.0
    deviation_magnitude: float = 0.0
    possible_causes: List[str] = field(default_factory=list)
    recommended_investigation: List[str] = field(default_factory=list)
    related_metrics: List[str] = field(default_factory=list)
    suppressed: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _new_alert_id()
        if not self.detected_at:
            self.detected_at = datetime.utcnow().isoformat()


@dataclass
class MetricTimeSeries(SerializableModel):
    """An ordered time series for a single marketing metric.

    ``values`` and ``dates`` must be the same length, ordered oldest-first.

    Attributes:
        metric_name: Canonical metric name (e.g., "sessions", "conversions").
        values: Numeric values ordered oldest-first.
        dates: Corresponding ISO date strings (YYYY-MM-DD).
        source: Which connector produced this data (e.g., "ga4", "gsc").
    """

    metric_name: str = ""
    values: List[float] = field(default_factory=list)
    dates: List[str] = field(default_factory=list)
    source: str = ""


@dataclass
class SeasonalPattern(SerializableModel):
    """Known seasonal adjustments for a metric.

    Factors are multipliers where 1.0 means average.  A day_of_week_factor
    of 0.7 for Sunday means the metric is typically 30 % below its daily
    average on Sundays.

    Attributes:
        metric_name: Which metric this pattern applies to.
        day_of_week_factors: 0=Monday .. 6=Sunday, multiplier (1.0 = avg).
        month_factors: 1=January .. 12=December, multiplier.
        known_events: List of ``{"date": str, "event_name": str,
            "expected_impact_pct": float}`` for holidays and events.
    """

    metric_name: str = ""
    day_of_week_factors: Dict[int, float] = field(default_factory=dict)
    month_factors: Dict[int, float] = field(default_factory=dict)
    known_events: List[Dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Internal math helpers (stdlib-only, no numpy/pandas)
# ---------------------------------------------------------------------------


def _mean(vals: List[float]) -> float:
    """Arithmetic mean. Returns 0.0 for empty input."""
    if not vals:
        return 0.0
    return sum(vals) / len(vals)


def _std_dev(vals: List[float], mean_val: Optional[float] = None) -> float:
    """Population standard deviation. Returns 0.0 for < 2 values."""
    if len(vals) < 2:
        return 0.0
    m = mean_val if mean_val is not None else _mean(vals)
    variance = sum((v - m) ** 2 for v in vals) / len(vals)
    return math.sqrt(variance)


def _linear_slope(vals: List[float]) -> float:
    """Ordinary least-squares slope for equally-spaced values.

    Returns 0.0 for empty or single-element input.  The x-axis is
    implicitly [0, 1, 2, ...].
    """
    n = len(vals)
    if n < 2:
        return 0.0
    x_mean = (n - 1) / 2.0
    y_mean = _mean(vals)
    numerator = 0.0
    denominator = 0.0
    for i, y in enumerate(vals):
        dx = i - x_mean
        numerator += dx * (y - y_mean)
        denominator += dx * dx
    if denominator == 0.0:
        return 0.0
    return numerator / denominator


def _parse_iso_date(date_str: str) -> Optional[datetime]:
    """Parse a YYYY-MM-DD date string, returning None on failure."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except (ValueError, TypeError):
        return None


# ---------------------------------------------------------------------------
# Metric category inference
# ---------------------------------------------------------------------------

_METRIC_CATEGORIES: Dict[str, List[str]] = {
    "traffic": [
        "sessions", "users", "pageviews", "page_views", "visits",
        "unique_visitors", "organic_sessions", "organic_traffic",
        "referral_traffic", "direct_traffic",
    ],
    "conversions": [
        "conversions", "conversion_rate", "leads", "form_submissions",
        "sign_ups", "signups", "purchases", "transactions", "goals",
        "goal_completions", "demo_requests", "consultation_requests",
    ],
    "ad_spend": [
        "ad_spend", "cost", "spend", "cpc", "cpm", "cpa", "roas",
        "impressions", "clicks", "ctr", "click_through_rate",
        "cost_per_click", "cost_per_acquisition",
    ],
    "reviews": [
        "reviews", "review_count", "review_score", "rating",
        "average_rating", "star_rating", "nps", "net_promoter_score",
        "review_velocity", "review_response_rate",
    ],
    "phone_calls": [
        "phone_calls", "calls", "call_volume", "missed_calls",
        "answered_calls", "call_duration", "call_conversion_rate",
        "voicemails", "callback_requests",
    ],
    "email": [
        "open_rate", "click_rate", "email_opens", "email_clicks",
        "unsubscribes", "bounce_rate", "delivery_rate", "list_growth",
    ],
    "social": [
        "followers", "engagement_rate", "likes", "shares", "comments",
        "reach", "impressions_social", "mentions",
    ],
}


def _infer_metric_category(metric_name: str) -> str:
    """Infer the marketing category from a metric name.

    Returns the best-matching category key, or ``"general"`` when no
    keyword matches.
    """
    lower = metric_name.lower()
    for category, keywords in _METRIC_CATEGORIES.items():
        for kw in keywords:
            if kw in lower:
                return category
    return "general"


# ---------------------------------------------------------------------------
# AnomalyDetector
# ---------------------------------------------------------------------------


class AnomalyDetector:
    """Multi-strategy anomaly detector for marketing metric time series.

    Runs five detection methods against a ``MetricTimeSeries`` and
    returns a deduplicated, severity-sorted list of ``AnomalyAlert``
    objects.

    Args:
        sensitivity: Number of standard deviations for statistical outlier
            detection.  Lower values are more sensitive.
        min_data_points: Minimum history length required before detection
            runs.  Series shorter than this return an empty list with no
            error.
    """

    def __init__(
        self,
        sensitivity: float = 2.0,
        min_data_points: int = 14,
    ) -> None:
        self.sensitivity = sensitivity
        self.min_data_points = min_data_points

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def detect_anomalies(
        self,
        time_series: MetricTimeSeries,
        seasonal_pattern: Optional[SeasonalPattern] = None,
    ) -> List[AnomalyAlert]:
        """Run all detection strategies and return combined, deduplicated alerts.

        Args:
            time_series: The metric time series to analyze.
            seasonal_pattern: Optional seasonal adjustment factors.  When
                provided, the statistical outlier detector adjusts expected
                ranges by the seasonal factor for each date.

        Returns:
            List of ``AnomalyAlert`` objects sorted by severity (critical
            first), then by deviation magnitude (largest first).  Alerts
            that would duplicate an already-emitted (metric_name,
            anomaly_type) pair on the same date are suppressed.
        """
        if not time_series.values or len(time_series.values) < self.min_data_points:
            return []

        all_alerts: List[AnomalyAlert] = []
        all_alerts.extend(self._detect_statistical_outlier(time_series, seasonal_pattern=seasonal_pattern))
        all_alerts.extend(self._detect_trend_break(time_series))
        all_alerts.extend(self._detect_flatline(time_series))
        all_alerts.extend(self._detect_spike(time_series))
        all_alerts.extend(self._detect_drop(time_series))

        deduped = self._deduplicate_alerts(all_alerts)
        deduped.sort(key=self._alert_sort_key)
        return deduped

    # ------------------------------------------------------------------
    # Detection: statistical outlier
    # ------------------------------------------------------------------

    def _detect_statistical_outlier(
        self,
        time_series: MetricTimeSeries,
        window: int = 30,
        seasonal_pattern: Optional[SeasonalPattern] = None,
    ) -> List[AnomalyAlert]:
        """Flag values outside the rolling mean +/- (sensitivity * std_dev).

        Uses a trailing window of ``window`` days.  When a
        ``SeasonalPattern`` is provided, the expected range is adjusted
        by the combined seasonal factor for the observation date.
        """
        values = time_series.values
        dates = time_series.dates
        alerts: List[AnomalyAlert] = []

        # Only evaluate the most recent value to avoid historical noise
        if len(values) < 2:
            return alerts

        # Determine the window slice (excluding the latest value itself)
        end_idx = len(values) - 1
        start_idx = max(0, end_idx - window)
        window_vals = values[start_idx:end_idx]

        if len(window_vals) < 2:
            return alerts

        rolling_mean = _mean(window_vals)
        rolling_std = _std_dev(window_vals, rolling_mean)

        # Guard against zero std-dev (perfectly flat history)
        if rolling_std == 0.0:
            return alerts

        current_value = values[end_idx]
        current_date = dates[end_idx] if end_idx < len(dates) else ""

        # Seasonally adjust if pattern provided
        if seasonal_pattern is not None:
            adjusted_value = self._adjust_for_seasonality(
                current_value, current_date, seasonal_pattern
            )
        else:
            adjusted_value = current_value

        expected_low = rolling_mean - (self.sensitivity * rolling_std)
        expected_high = rolling_mean + (self.sensitivity * rolling_std)

        if adjusted_value < expected_low or adjusted_value > expected_high:
            deviation = abs(adjusted_value - rolling_mean) / rolling_std
            severity = self._severity_from_deviation(deviation)

            alerts.append(AnomalyAlert(
                metric_name=time_series.metric_name,
                anomaly_type=AnomalyType.STATISTICAL_OUTLIER.value,
                severity=severity,
                value=current_value,
                expected_range_low=round(expected_low, 4),
                expected_range_high=round(expected_high, 4),
                deviation_magnitude=round(deviation, 4),
                possible_causes=self._suggest_possible_causes(
                    AnomalyType.STATISTICAL_OUTLIER.value,
                    time_series.metric_name,
                ),
                recommended_investigation=self._suggest_investigation(
                    AnomalyType.STATISTICAL_OUTLIER.value,
                    time_series.metric_name,
                ),
                related_metrics=self._suggest_related_metrics(
                    time_series.metric_name,
                ),
                metadata={
                    "detection_method": "statistical_outlier",
                    "window": window,
                    "rolling_mean": round(rolling_mean, 4),
                    "rolling_std": round(rolling_std, 4),
                    "seasonally_adjusted": seasonal_pattern is not None,
                    "adjusted_value": round(adjusted_value, 4),
                    "source": time_series.source,
                },
            ))

        return alerts

    # ------------------------------------------------------------------
    # Detection: trend break
    # ------------------------------------------------------------------

    def _detect_trend_break(
        self,
        time_series: MetricTimeSeries,
        short_window: int = 7,
        long_window: int = 30,
    ) -> List[AnomalyAlert]:
        """Detect when a short-window trend reverses the long-window trend.

        A trend break is flagged when the slopes of the short and long
        windows have opposite signs AND the short-window slope magnitude
        exceeds 50 % of the long-window slope magnitude.
        """
        values = time_series.values
        alerts: List[AnomalyAlert] = []

        if len(values) < long_window:
            # Use what we have if we meet min_data_points but are under long_window
            if len(values) < short_window + 1:
                return alerts
            effective_long = len(values)
        else:
            effective_long = long_window

        short_slice = values[-short_window:]
        long_slice = values[-effective_long:]

        short_slope = _linear_slope(short_slice)
        long_slope = _linear_slope(long_slice)

        # Opposite signs check (skip if either is exactly zero)
        if long_slope == 0.0 or short_slope == 0.0:
            return alerts

        slopes_oppose = (short_slope > 0 and long_slope < 0) or (
            short_slope < 0 and long_slope > 0
        )
        magnitude_significant = abs(short_slope) > 0.5 * abs(long_slope)

        if slopes_oppose and magnitude_significant:
            long_mean = _mean(long_slice)
            long_std = _std_dev(long_slice)
            current_value = values[-1]
            deviation = abs(short_slope / long_slope) if long_slope != 0 else 0.0

            # Compute a reasonable expected range from the long window
            expected_low = long_mean - (self.sensitivity * long_std) if long_std > 0 else long_mean * 0.8
            expected_high = long_mean + (self.sensitivity * long_std) if long_std > 0 else long_mean * 1.2

            severity = AnomalySeverity.WARNING.value
            if deviation > 2.0:
                severity = AnomalySeverity.CRITICAL.value

            alerts.append(AnomalyAlert(
                metric_name=time_series.metric_name,
                anomaly_type=AnomalyType.TREND_BREAK.value,
                severity=severity,
                value=current_value,
                expected_range_low=round(expected_low, 4),
                expected_range_high=round(expected_high, 4),
                deviation_magnitude=round(deviation, 4),
                possible_causes=self._suggest_possible_causes(
                    AnomalyType.TREND_BREAK.value,
                    time_series.metric_name,
                ),
                recommended_investigation=self._suggest_investigation(
                    AnomalyType.TREND_BREAK.value,
                    time_series.metric_name,
                ),
                related_metrics=self._suggest_related_metrics(
                    time_series.metric_name,
                ),
                metadata={
                    "detection_method": "trend_break",
                    "short_window": short_window,
                    "long_window": effective_long,
                    "short_slope": round(short_slope, 6),
                    "long_slope": round(long_slope, 6),
                    "slope_ratio": round(deviation, 4),
                    "source": time_series.source,
                },
            ))

        return alerts

    # ------------------------------------------------------------------
    # Detection: flatline
    # ------------------------------------------------------------------

    def _detect_flatline(
        self,
        time_series: MetricTimeSeries,
        zero_threshold: float = 0.01,
    ) -> List[AnomalyAlert]:
        """Detect when a normally active metric flatlines to near-zero.

        A flatline is flagged when the last 3 or more consecutive values
        are at or below ``zero_threshold`` AND the 30-day rolling average
        (excluding those trailing zeros) is meaningfully above zero.
        """
        values = time_series.values
        alerts: List[AnomalyAlert] = []

        if len(values) < 4:
            return alerts

        # Count consecutive near-zero values from the end
        consecutive_zero = 0
        for v in reversed(values):
            if abs(v) <= zero_threshold:
                consecutive_zero += 1
            else:
                break

        if consecutive_zero < 3:
            return alerts

        # Compute the average of the non-flatline portion
        non_flatline = values[: len(values) - consecutive_zero]
        if not non_flatline:
            return alerts

        historical_avg = _mean(non_flatline)
        if historical_avg <= zero_threshold:
            # The metric was always near-zero; not a real flatline
            return alerts

        deviation_pct = 100.0  # Dropped to ~0 from a positive average

        alerts.append(AnomalyAlert(
            metric_name=time_series.metric_name,
            anomaly_type=AnomalyType.FLATLINE.value,
            severity=AnomalySeverity.CRITICAL.value,
            value=values[-1],
            expected_range_low=round(historical_avg * 0.5, 4),
            expected_range_high=round(historical_avg * 1.5, 4),
            deviation_magnitude=round(deviation_pct, 4),
            possible_causes=self._suggest_possible_causes(
                AnomalyType.FLATLINE.value,
                time_series.metric_name,
            ),
            recommended_investigation=self._suggest_investigation(
                AnomalyType.FLATLINE.value,
                time_series.metric_name,
            ),
            related_metrics=self._suggest_related_metrics(
                time_series.metric_name,
            ),
            metadata={
                "detection_method": "flatline",
                "consecutive_zero_days": consecutive_zero,
                "historical_average": round(historical_avg, 4),
                "zero_threshold": zero_threshold,
                "source": time_series.source,
            },
        ))

        return alerts

    # ------------------------------------------------------------------
    # Detection: spike
    # ------------------------------------------------------------------

    def _detect_spike(
        self,
        time_series: MetricTimeSeries,
        spike_threshold: float = 2.0,
    ) -> List[AnomalyAlert]:
        """Flag when the latest value exceeds spike_threshold * rolling avg.

        The rolling average uses up to 30 days of history, excluding the
        latest value itself.
        """
        values = time_series.values
        alerts: List[AnomalyAlert] = []

        if len(values) < 2:
            return alerts

        end_idx = len(values) - 1
        start_idx = max(0, end_idx - 30)
        window_vals = values[start_idx:end_idx]

        if not window_vals:
            return alerts

        daily_avg = _mean(window_vals)
        daily_std = _std_dev(window_vals, daily_avg)
        current_value = values[end_idx]

        # Guard: if the average is zero or negative, spike detection is meaningless
        if daily_avg <= 0:
            return alerts

        if current_value > spike_threshold * daily_avg:
            deviation_multiple = current_value / daily_avg
            deviation_std = (
                (current_value - daily_avg) / daily_std if daily_std > 0 else deviation_multiple
            )

            severity = AnomalySeverity.WARNING.value
            if deviation_multiple > 3.0:
                severity = AnomalySeverity.CRITICAL.value
            elif deviation_multiple < 2.5:
                severity = AnomalySeverity.INFO.value

            expected_high = daily_avg + (self.sensitivity * daily_std) if daily_std > 0 else daily_avg * 1.5

            alerts.append(AnomalyAlert(
                metric_name=time_series.metric_name,
                anomaly_type=AnomalyType.SPIKE.value,
                severity=severity,
                value=current_value,
                expected_range_low=round(max(0.0, daily_avg - (self.sensitivity * daily_std)) if daily_std > 0 else daily_avg * 0.5, 4),
                expected_range_high=round(expected_high, 4),
                deviation_magnitude=round(deviation_std, 4),
                possible_causes=self._suggest_possible_causes(
                    AnomalyType.SPIKE.value,
                    time_series.metric_name,
                ),
                recommended_investigation=self._suggest_investigation(
                    AnomalyType.SPIKE.value,
                    time_series.metric_name,
                ),
                related_metrics=self._suggest_related_metrics(
                    time_series.metric_name,
                ),
                metadata={
                    "detection_method": "spike",
                    "spike_threshold": spike_threshold,
                    "daily_average": round(daily_avg, 4),
                    "multiple_of_average": round(deviation_multiple, 4),
                    "source": time_series.source,
                },
            ))

        return alerts

    # ------------------------------------------------------------------
    # Detection: drop
    # ------------------------------------------------------------------

    def _detect_drop(
        self,
        time_series: MetricTimeSeries,
        drop_threshold: float = 0.5,
    ) -> List[AnomalyAlert]:
        """Flag when the latest value falls below drop_threshold * rolling avg.

        The rolling average uses up to 30 days of history, excluding the
        latest value itself.
        """
        values = time_series.values
        alerts: List[AnomalyAlert] = []

        if len(values) < 2:
            return alerts

        end_idx = len(values) - 1
        start_idx = max(0, end_idx - 30)
        window_vals = values[start_idx:end_idx]

        if not window_vals:
            return alerts

        daily_avg = _mean(window_vals)
        daily_std = _std_dev(window_vals, daily_avg)
        current_value = values[end_idx]

        # Guard: if the average is zero or negative, drop detection is meaningless
        if daily_avg <= 0:
            return alerts

        if current_value < drop_threshold * daily_avg:
            drop_pct = ((daily_avg - current_value) / daily_avg) * 100.0
            deviation_std = (
                (daily_avg - current_value) / daily_std if daily_std > 0 else drop_pct
            )

            severity = AnomalySeverity.WARNING.value
            if drop_pct > 80.0:
                severity = AnomalySeverity.CRITICAL.value
            elif drop_pct > 60.0:
                severity = AnomalySeverity.WARNING.value
            else:
                severity = AnomalySeverity.INFO.value

            expected_low = max(0.0, daily_avg - (self.sensitivity * daily_std)) if daily_std > 0 else daily_avg * 0.5

            alerts.append(AnomalyAlert(
                metric_name=time_series.metric_name,
                anomaly_type=AnomalyType.DROP.value,
                severity=severity,
                value=current_value,
                expected_range_low=round(expected_low, 4),
                expected_range_high=round(daily_avg + (self.sensitivity * daily_std) if daily_std > 0 else daily_avg * 1.5, 4),
                deviation_magnitude=round(deviation_std, 4),
                possible_causes=self._suggest_possible_causes(
                    AnomalyType.DROP.value,
                    time_series.metric_name,
                ),
                recommended_investigation=self._suggest_investigation(
                    AnomalyType.DROP.value,
                    time_series.metric_name,
                ),
                related_metrics=self._suggest_related_metrics(
                    time_series.metric_name,
                ),
                metadata={
                    "detection_method": "drop",
                    "drop_threshold": drop_threshold,
                    "daily_average": round(daily_avg, 4),
                    "drop_percent": round(drop_pct, 2),
                    "source": time_series.source,
                },
            ))

        return alerts

    # ------------------------------------------------------------------
    # Seasonality adjustment
    # ------------------------------------------------------------------

    def _adjust_for_seasonality(
        self,
        value: float,
        date: str,
        pattern: SeasonalPattern,
    ) -> float:
        """Divide value by the combined seasonal factor for its date.

        The combined factor is ``day_of_week_factor * month_factor``.
        If an entry in ``known_events`` matches the date, the event's
        ``expected_impact_pct`` is applied as an additional adjustment
        (e.g., +20 % impact means we divide by 1.2 to normalize).

        Returns the original value unchanged when the combined factor
        is zero or negative (safety guard).
        """
        parsed = _parse_iso_date(date)
        if parsed is None:
            return value

        # Day-of-week: Monday=0 .. Sunday=6
        dow_factor = pattern.day_of_week_factors.get(parsed.weekday(), 1.0)
        month_factor = pattern.month_factors.get(parsed.month, 1.0)
        combined = dow_factor * month_factor

        # Check known events for this date
        for event in pattern.known_events:
            event_date = event.get("date", "")
            if event_date == date:
                impact_pct = float(event.get("expected_impact_pct", 0))
                combined *= 1.0 + (impact_pct / 100.0)

        if combined <= 0:
            return value

        return value / combined

    # ------------------------------------------------------------------
    # Cause / investigation suggestions
    # ------------------------------------------------------------------

    # Maps (anomaly_type, metric_category) → list of possible causes
    _CAUSE_MAP: Dict[str, Dict[str, List[str]]] = {
        AnomalyType.STATISTICAL_OUTLIER.value: {
            "traffic": [
                "Algorithm update changed organic ranking positions",
                "Referral traffic from viral social post",
                "Bot or crawler traffic spike inflating numbers",
            ],
            "conversions": [
                "Landing page A/B test variant activated",
                "Pricing or offer change affected conversion rate",
                "Form or checkout flow was modified",
            ],
            "ad_spend": [
                "Budget cap was changed",
                "Bidding strategy auto-adjusted spend",
                "New ad group or campaign went live",
            ],
            "reviews": [
                "Review solicitation campaign produced a batch",
                "Negative review cluster from a single incident",
                "Review platform policy change removed reviews",
            ],
            "phone_calls": [
                "New call tracking number activated",
                "Ad extension or landing page change drove more calls",
                "IVR or routing configuration changed",
            ],
            "email": [
                "Deliverability issue with email provider",
                "New email campaign or list segment activated",
                "Subject line or send time change affected open rate",
            ],
            "social": [
                "Post went viral or was boosted",
                "Algorithm change affected reach",
                "Influencer mention or share",
            ],
            "general": [
                "External event or industry trend shift",
                "Data collection or tracking change",
                "Seasonal or cyclical variation",
            ],
        },
        AnomalyType.TREND_BREAK.value: {
            "traffic": [
                "Google algorithm update shifted rankings",
                "Competitor launched aggressive content campaign",
                "Technical SEO issue (indexation, crawl errors)",
                "Paid campaign launched or paused, shifting total traffic",
            ],
            "conversions": [
                "Conversion tracking code was modified or removed",
                "Landing page redesign changed user flow",
                "Pricing or offer strategy changed",
                "Market conditions or competitor activity shifted",
            ],
            "ad_spend": [
                "Budget reallocation across campaigns",
                "Platform auction dynamics shifted",
                "New competitor entered the auction",
            ],
            "reviews": [
                "Review generation process changed or stopped",
                "Competitor reputation campaign affecting sentiment",
                "Platform algorithm change affecting review visibility",
            ],
            "phone_calls": [
                "Call routing or IVR system changed",
                "Business hours or staffing changed",
                "KaiCalls AI receptionist configuration updated",
            ],
            "email": [
                "Email frequency or cadence changed",
                "List hygiene or segmentation updated",
                "Domain reputation shift",
            ],
            "social": [
                "Posting frequency or content strategy changed",
                "Platform algorithm update",
                "Audience growth or decline trend",
            ],
            "general": [
                "Fundamental change in marketing strategy",
                "New competitor or market entrant",
                "Seasonal pattern shift",
            ],
        },
        AnomalyType.FLATLINE.value: {
            "traffic": [
                "Tracking script may have been removed or broken",
                "DNS issue or server downtime",
                "Google Analytics property misconfigured",
                "Site blocked by robots.txt change",
            ],
            "conversions": [
                "Form is broken or unreachable",
                "Conversion tracking tag was removed",
                "Thank-you page URL changed, breaking goal tracking",
                "Payment processor outage",
            ],
            "ad_spend": [
                "Ad account was paused or suspended",
                "Payment method expired or billing failed",
                "All campaigns set to zero budget",
            ],
            "reviews": [
                "Review solicitation process stopped entirely",
                "Review platform account disconnected",
                "Email automation sending review requests is broken",
            ],
            "phone_calls": [
                "Phone number disconnected or ported incorrectly",
                "Call tracking provider outage",
                "KaiCalls AI receptionist disconnected",
                "VoIP system failure",
            ],
            "email": [
                "Email sending paused or provider suspended",
                "Domain blacklisted by email providers",
                "Automation workflow disabled",
            ],
            "social": [
                "Social account suspended or restricted",
                "Posting automation stopped",
                "API connection to social platform broken",
            ],
            "general": [
                "Data pipeline or integration broken",
                "API credentials expired",
                "Reporting tool lost access",
            ],
        },
        AnomalyType.SPIKE.value: {
            "traffic": [
                "Content went viral on social media",
                "Major backlink from high-authority site",
                "Bot or scraper traffic inflation",
                "Paid campaign launched driving surge",
            ],
            "conversions": [
                "Flash sale or limited-time offer launched",
                "PR coverage drove high-intent traffic",
                "Conversion tracking double-firing",
            ],
            "ad_spend": [
                "Budget cap removed or increased",
                "New campaign launched with high initial bids",
                "Bidding strategy change (manual to automated)",
            ],
            "reviews": [
                "Review generation campaign blast sent",
                "Featured on review aggregator site",
                "Customer appreciation event generated review wave",
            ],
            "phone_calls": [
                "New ad campaign with click-to-call extension",
                "TV or radio ad aired driving call volume",
                "Emergency or crisis situation causing call surge",
            ],
            "email": [
                "Large broadcast email sent to full list",
                "Re-engagement campaign to dormant subscribers",
                "Email forwarded or shared widely",
            ],
            "social": [
                "Post went viral or was reshared by influencer",
                "Paid social campaign budget increased",
                "Trending topic or hashtag alignment",
            ],
            "general": [
                "Seasonal event or holiday driving activity",
                "PR or media coverage",
                "Competitor outage redirecting traffic",
            ],
        },
        AnomalyType.DROP.value: {
            "traffic": [
                "Google algorithm update penalized the site",
                "Major technical issue (500 errors, slow load)",
                "Paid campaign paused without organic pickup",
                "Seasonal dip or holiday weekend",
            ],
            "conversions": [
                "Form broken or contact page returning errors",
                "Landing page changed, breaking the conversion path",
                "Offer expired or pricing changed",
                "Competitor launched better offer",
            ],
            "ad_spend": [
                "Campaign paused due to budget exhaustion",
                "Ad disapproved by platform policy review",
                "Billing failure or payment method expired",
            ],
            "reviews": [
                "Negative review burst suppressing overall rating",
                "Review platform removed legitimate reviews",
                "Review solicitation emails going to spam",
            ],
            "phone_calls": [
                "Phone system outage or routing error",
                "Business hours changed without updating ads",
                "Call tracking number expired",
                "KaiCalls AI receptionist misconfigured",
            ],
            "email": [
                "Domain or IP blacklisted",
                "Email content triggering spam filters",
                "Subscriber fatigue from over-sending",
            ],
            "social": [
                "Algorithm suppressed content reach",
                "Account penalized for policy violation",
                "Audience fatigue or unfollows",
            ],
            "general": [
                "External market event reducing demand",
                "Competitor captured market share",
                "Seasonal downturn",
            ],
        },
    }

    def _suggest_possible_causes(
        self,
        anomaly_type: str,
        metric_name: str,
    ) -> List[str]:
        """Return common causes based on anomaly type and metric category.

        Covers traffic, conversions, ad_spend, reviews, phone_calls,
        email, social, and a general fallback.
        """
        category = _infer_metric_category(metric_name)
        type_map = self._CAUSE_MAP.get(anomaly_type, {})
        causes = type_map.get(category, type_map.get("general", []))
        if not causes:
            causes = [
                "Unexpected change in data source",
                "External factor or market shift",
                "Possible tracking or measurement issue",
            ]
        return list(causes)

    # Maps (anomaly_type, metric_category) → investigation steps
    _INVESTIGATION_MAP: Dict[str, Dict[str, List[str]]] = {
        AnomalyType.STATISTICAL_OUTLIER.value: {
            "traffic": [
                "Check Google Search Console for ranking position changes",
                "Review server access logs for bot traffic patterns",
                "Compare traffic sources (organic vs direct vs referral)",
            ],
            "conversions": [
                "Test all conversion forms and checkout flows manually",
                "Verify conversion tracking tags are firing correctly",
                "Review any recent landing page or pricing changes",
            ],
            "ad_spend": [
                "Review platform billing and budget settings",
                "Check for bid strategy changes or new campaign launches",
                "Audit audience targeting for unexpected expansion",
            ],
            "reviews": [
                "Check review platforms for policy enforcement actions",
                "Review recent customer interactions for patterns",
                "Verify review solicitation automation is working",
            ],
            "phone_calls": [
                "Test all published phone numbers end-to-end",
                "Check call tracking dashboard for routing issues",
                "Review KaiCalls AI receptionist logs for errors",
            ],
            "general": [
                "Check all data source connections and API health",
                "Review recent configuration or code changes",
                "Cross-reference with other metrics for corroboration",
            ],
        },
        AnomalyType.TREND_BREAK.value: {
            "general": [
                "Compare the metric with historical seasonal patterns",
                "Check for recent marketing strategy or budget changes",
                "Review competitor activity for correlated shifts",
                "Audit tracking implementation for recent modifications",
            ],
        },
        AnomalyType.FLATLINE.value: {
            "general": [
                "Verify the data collection pipeline is operational",
                "Check API credentials and connection status",
                "Test the tracking script or pixel on the live site",
                "Review server and application error logs",
                "Contact the data provider for platform-side outages",
            ],
        },
        AnomalyType.SPIKE.value: {
            "general": [
                "Check for bot or invalid traffic using server logs",
                "Review recently launched campaigns or content",
                "Look for external mentions, press coverage, or viral posts",
                "Verify tracking is not double-counting events",
            ],
        },
        AnomalyType.DROP.value: {
            "general": [
                "Test the conversion path end-to-end in an incognito browser",
                "Check server error rates and page load times",
                "Review any recent deployments or CMS changes",
                "Verify ad campaigns are active and approved",
                "Check for Google algorithm update announcements",
            ],
        },
    }

    def _suggest_investigation(
        self,
        anomaly_type: str,
        metric_name: str,
    ) -> List[str]:
        """Return specific investigation steps for the anomaly."""
        category = _infer_metric_category(metric_name)
        type_map = self._INVESTIGATION_MAP.get(anomaly_type, {})
        steps = type_map.get(category, type_map.get("general", []))
        if not steps:
            steps = [
                "Review the metric data source for errors",
                "Check for recent changes to tracking or configuration",
                "Cross-reference with related metrics",
            ]
        return list(steps)

    # Related metrics by category
    _RELATED_METRICS_MAP: Dict[str, List[str]] = {
        "traffic": ["bounce_rate", "pages_per_session", "session_duration", "conversions"],
        "conversions": ["sessions", "conversion_rate", "revenue", "leads"],
        "ad_spend": ["impressions", "clicks", "ctr", "conversions", "roas"],
        "reviews": ["review_score", "review_velocity", "conversions", "phone_calls"],
        "phone_calls": ["sessions", "conversions", "ad_spend", "missed_calls"],
        "email": ["delivery_rate", "open_rate", "click_rate", "unsubscribes"],
        "social": ["followers", "engagement_rate", "reach", "website_referrals"],
        "general": ["sessions", "conversions", "revenue"],
    }

    def _suggest_related_metrics(self, metric_name: str) -> List[str]:
        """Return metrics likely affected by the same root cause."""
        category = _infer_metric_category(metric_name)
        related = self._RELATED_METRICS_MAP.get(
            category, self._RELATED_METRICS_MAP["general"]
        )
        # Exclude the metric itself if it appears in the related list
        return [m for m in related if m != metric_name.lower()]

    # ------------------------------------------------------------------
    # Deduplication and sorting
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate_alerts(alerts: List[AnomalyAlert]) -> List[AnomalyAlert]:
        """Remove duplicate (metric_name, anomaly_type) alerts.

        When duplicates exist, the alert with the higher severity (or
        larger deviation magnitude as tiebreaker) is kept; the others
        are marked as suppressed and included at the end.
        """
        severity_rank = {
            AnomalySeverity.CRITICAL.value: 0,
            AnomalySeverity.WARNING.value: 1,
            AnomalySeverity.INFO.value: 2,
        }

        best: Dict[str, AnomalyAlert] = {}
        suppressed: List[AnomalyAlert] = []

        for alert in alerts:
            key = f"{alert.metric_name}::{alert.anomaly_type}"
            existing = best.get(key)
            if existing is None:
                best[key] = alert
            else:
                # Compare: lower severity_rank is more severe
                existing_rank = severity_rank.get(existing.severity, 99)
                new_rank = severity_rank.get(alert.severity, 99)

                if new_rank < existing_rank or (
                    new_rank == existing_rank
                    and alert.deviation_magnitude > existing.deviation_magnitude
                ):
                    existing.suppressed = True
                    suppressed.append(existing)
                    best[key] = alert
                else:
                    alert.suppressed = True
                    suppressed.append(alert)

        result = list(best.values())
        result.extend(suppressed)
        return result

    @staticmethod
    def _alert_sort_key(alert: AnomalyAlert) -> tuple:
        """Sort key: unsuppressed first, then severity, then deviation."""
        severity_rank = {
            AnomalySeverity.CRITICAL.value: 0,
            AnomalySeverity.WARNING.value: 1,
            AnomalySeverity.INFO.value: 2,
        }
        return (
            1 if alert.suppressed else 0,
            severity_rank.get(alert.severity, 99),
            -alert.deviation_magnitude,
        )

    # ------------------------------------------------------------------
    # Severity helpers
    # ------------------------------------------------------------------

    def _severity_from_deviation(self, deviation: float) -> str:
        """Map a standard-deviation distance to a severity level."""
        if deviation >= self.sensitivity * 2:
            return AnomalySeverity.CRITICAL.value
        if deviation >= self.sensitivity:
            return AnomalySeverity.WARNING.value
        return AnomalySeverity.INFO.value


# ---------------------------------------------------------------------------
# ConfidenceScorer
# ---------------------------------------------------------------------------


class ConfidenceScorer:
    """Score the confidence that an observed metric change is causally
    linked to a specific marketing action.

    Uses a penalty/bonus system starting from a base score of 0.8.
    Concurrent changes, external factors, short observation windows, and
    lack of seasonal adjustment all reduce confidence.  Long observation
    windows and isolation (zero concurrent changes) increase it.

    Usage::

        scorer = ConfidenceScorer()
        result = scorer.score_metric_change(
            metric_name="conversions",
            before_value=50.0,
            after_value=75.0,
            concurrent_changes=2,
            days_elapsed=21,
            external_factors=["holiday_weekend"],
        )
        # result == {
        #     "confidence_level": "medium",
        #     "confidence_score": 0.55,
        #     "reasoning": [...],
        # }
    """

    BASE_SCORE: float = 0.8

    def score_metric_change(
        self,
        metric_name: str,
        before_value: float,
        after_value: float,
        concurrent_changes: int,
        days_elapsed: int,
        external_factors: List[str],
        seasonal_adjusted: bool = False,
    ) -> Dict[str, Any]:
        """Score confidence in the causality of an observed metric change.

        Args:
            metric_name: Which metric changed.
            before_value: Metric value before the action.
            after_value: Metric value after the action.
            concurrent_changes: Number of other marketing changes that
                happened in the same observation window.
            days_elapsed: Days between the action and the measurement.
            external_factors: Known confounders (e.g., "holiday_weekend",
                "competitor_launch", "algorithm_update").
            seasonal_adjusted: Whether the before/after values have been
                adjusted for seasonal patterns.

        Returns:
            Dict with ``confidence_level`` (str), ``confidence_score``
            (float 0-1), and ``reasoning`` (list of str explaining each
            adjustment).
        """
        score = self.BASE_SCORE
        reasoning: List[str] = [f"Base confidence score: {self.BASE_SCORE}"]

        # --- Penalties ---

        # Concurrent changes: -0.1 per change, capped at -0.4
        if concurrent_changes > 0:
            penalty = min(concurrent_changes * 0.1, 0.4)
            score -= penalty
            reasoning.append(
                f"-{penalty:.2f}: {concurrent_changes} concurrent marketing "
                f"change(s) make it harder to isolate causality"
            )

        # External factors: -0.15 per factor, capped at -0.3
        if external_factors:
            penalty = min(len(external_factors) * 0.15, 0.3)
            score -= penalty
            factors_str = ", ".join(external_factors)
            reasoning.append(
                f"-{penalty:.2f}: {len(external_factors)} external factor(s) "
                f"({factors_str}) may confound the result"
            )

        # Short observation window
        if days_elapsed < 7:
            score -= 0.2
            reasoning.append(
                f"-0.20: only {days_elapsed} day(s) elapsed — too short "
                f"for reliable measurement (need at least 7)"
            )
        elif days_elapsed < 14:
            score -= 0.1
            reasoning.append(
                f"-0.10: only {days_elapsed} day(s) elapsed — moderate "
                f"observation window (14+ days preferred)"
            )

        # Seasonal adjustment missing
        if not seasonal_adjusted:
            score -= 0.05
            reasoning.append(
                "-0.05: values were not seasonally adjusted — seasonal "
                "patterns may be inflating or deflating the change"
            )

        # --- Bonuses ---

        # Long observation window
        if days_elapsed >= 30:
            score += 0.1
            reasoning.append(
                f"+0.10: {days_elapsed} day(s) elapsed — long observation "
                f"window increases confidence"
            )

        # Zero concurrent changes
        if concurrent_changes == 0:
            score += 0.05
            reasoning.append(
                "+0.05: no concurrent changes — the action was isolated, "
                "strengthening causal inference"
            )

        # Seasonal adjustment present
        if seasonal_adjusted:
            score += 0.05
            reasoning.append(
                "+0.05: values were seasonally adjusted — removes calendar "
                "noise from the comparison"
            )

        # --- Clamp and classify ---
        score = max(0.0, min(1.0, score))
        score = round(score, 2)

        if score >= 0.7:
            level = "high"
        elif score >= 0.45:
            level = "medium"
        elif score >= 0.2:
            level = "low"
        else:
            level = "insufficient"

        reasoning.append(f"Final score: {score} → confidence level: {level}")

        # Compute change metrics for context
        if before_value != 0:
            change_pct = round(((after_value - before_value) / abs(before_value)) * 100.0, 2)
        else:
            change_pct = None

        return {
            "confidence_level": level,
            "confidence_score": score,
            "reasoning": reasoning,
            "metric_name": metric_name,
            "before_value": before_value,
            "after_value": after_value,
            "change_percent": change_pct,
            "days_elapsed": days_elapsed,
            "concurrent_changes": concurrent_changes,
            "external_factors": external_factors,
            "seasonal_adjusted": seasonal_adjusted,
        }
