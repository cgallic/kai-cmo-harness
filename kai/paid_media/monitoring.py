"""Fatigue detection and spend anomaly monitoring for the Kai Marketing OS.

Provides continuous monitoring that catches paid campaign degradation early
and generates structured alerts with specific recommended actions.  Covers
creative fatigue, spending anomalies, under-performance vs. targets and
industry benchmarks, and quality score drops.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.

This module does **not** import anything from ``kai/runtime/``.
"""

from __future__ import annotations

import copy
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
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


class AlertSeverity(str, Enum):
    """Severity levels for monitoring alerts."""

    info = "info"
    warning = "warning"
    alert = "alert"
    critical = "critical"


class AlertCategory(str, Enum):
    """Categories of monitoring alerts."""

    creative_fatigue = "creative_fatigue"
    spend_anomaly = "spend_anomaly"
    underperformance = "underperformance"
    budget_pace = "budget_pace"
    zero_activity = "zero_activity"
    quality_degradation = "quality_degradation"
    cpc_spike = "cpc_spike"


# ============================================================================
# Models
# ============================================================================


class MonitoringAlert(BaseModel):
    """A single monitoring alert with recommended action."""

    id: str = Field(default_factory=lambda: generate_alert_id())
    category: str = ""
    severity: str = "info"
    entity_id: str = ""
    entity_type: str = ""
    platform: str = ""
    title: str = ""
    message: str = ""
    data: Dict[str, Any] = Field(default_factory=dict)
    recommended_action: str = ""
    recommended_action_type: Optional[str] = None
    auto_action_eligible: bool = False
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    acknowledged: bool = False
    acknowledged_at: Optional[str] = None
    resolved: bool = False
    resolved_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class FatigueIndicators(BaseModel):
    """Fatigue metrics for a single ad entity."""

    entity_id: str = ""
    platform: str = ""
    current_frequency: float = 0.0
    frequency_trend: str = "stable"
    ctr_current: float = 0.0
    ctr_7d_ago: float = 0.0
    ctr_change_pct: float = 0.0
    cpa_current: float = 0.0
    cpa_7d_ago: float = 0.0
    cpa_change_pct: float = 0.0
    days_running: int = 0
    is_fatigued: bool = False
    fatigue_reasons: List[str] = Field(default_factory=list)


class SpendAnomaly(BaseModel):
    """A detected spending anomaly."""

    entity_id: str = ""
    platform: str = ""
    anomaly_type: str = ""
    expected_value: float = 0.0
    actual_value: float = 0.0
    deviation_pct: float = 0.0
    period: str = ""
    is_anomaly: bool = True


class PerformanceBenchmark(BaseModel):
    """Comparison of a campaign metric against an industry benchmark."""

    metric: str = ""
    platform: str = ""
    campaign_type: str = ""
    industry: Optional[str] = None
    benchmark_value: float = 0.0
    benchmark_source: str = ""
    current_value: float = 0.0
    comparison: str = "at"


class MonitoringSnapshot(BaseModel):
    """Point-in-time summary of a full monitoring cycle."""

    timestamp: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    campaigns_monitored: int = 0
    alerts_generated: int = 0
    alerts_by_severity: Dict[str, int] = Field(default_factory=dict)
    alerts_by_category: Dict[str, int] = Field(default_factory=dict)
    top_alerts: List[MonitoringAlert] = Field(default_factory=list)
    overall_health: str = "healthy"


# ============================================================================
# Industry benchmarks
# ============================================================================

INDUSTRY_BENCHMARKS: Dict[str, Dict[str, Dict[str, float]]] = {
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
        "default": {
            "ctr": 0.01,
            "cpa": 35.0,
            "conversion_rate": 0.02,
            "frequency_cap": 3.0,
        },
        "ecommerce": {"ctr": 0.015, "cpa": 25.0, "conversion_rate": 0.025},
        "lead_gen": {"ctr": 0.008, "cpa": 40.0, "conversion_rate": 0.015},
    },
    "local_services_ads": {
        "default": {"cost_per_lead": 30.0, "lead_valid_rate": 0.6},
        "home_services": {"cost_per_lead": 25.0, "lead_valid_rate": 0.65},
        "legal": {"cost_per_lead": 80.0, "lead_valid_rate": 0.5},
    },
}


# ============================================================================
# Helper functions
# ============================================================================


def generate_alert_id() -> str:
    """Return a unique alert ID with ``alert_`` prefix."""
    return f"alert_{uuid.uuid4().hex[:12]}"


def calculate_pct_change(old_value: float, new_value: float) -> float:
    """Return the percentage change from *old_value* to *new_value*.

    Returns 0.0 when *old_value* is zero to avoid division errors.
    """
    if old_value == 0.0:
        return 0.0
    return ((new_value - old_value) / old_value) * 100


def determine_severity(
    deviation_pct: float, thresholds: Dict[str, float]
) -> str:
    """Map a deviation percentage to a severity level.

    *thresholds* should map severity names to minimum deviation values,
    e.g. ``{"warning": 20, "alert": 50, "critical": 100}``.
    Checks from highest to lowest.
    """
    severity_order = ["critical", "alert", "warning", "info"]
    for sev in severity_order:
        if sev in thresholds and abs(deviation_pct) >= thresholds[sev]:
            return sev
    return "info"


def get_benchmark(
    platform: str, metric: str, industry: Optional[str] = None
) -> Optional[float]:
    """Look up a benchmark value from ``INDUSTRY_BENCHMARKS``.

    Falls back to ``"default"`` if the given *industry* is not found.
    Returns ``None`` if the platform or metric is not in the table.
    """
    platform_data = INDUSTRY_BENCHMARKS.get(platform)
    if platform_data is None:
        return None

    industry_data = platform_data.get(industry or "default")
    if industry_data is None:
        industry_data = platform_data.get("default")
    if industry_data is None:
        return None

    return industry_data.get(metric)


def calculate_health_score(alerts: List[MonitoringAlert]) -> float:
    """Compute a 0-100 health score by penalizing for each alert.

    Penalty per severity: info=-2, warning=-5, alert=-15, critical=-25.
    """
    penalties: Dict[str, float] = {
        "info": 2.0,
        "warning": 5.0,
        "alert": 15.0,
        "critical": 25.0,
    }
    total_penalty = sum(
        penalties.get(a.severity, 0.0) for a in alerts
    )
    return max(0.0, min(100.0, 100.0 - total_penalty))


# ============================================================================
# FatigueDetector
# ============================================================================


class FatigueDetector:
    """Monitors for creative fatigue across campaigns.

    Checks frequency, CTR decline, CPA increases, and creative age to
    detect when ads are losing effectiveness.
    """

    def __init__(
        self,
        frequency_threshold_display: float = 3.0,
        frequency_threshold_social: float = 2.0,
        ctr_decline_threshold_pct: float = 20.0,
        cpa_increase_threshold_pct: float = 30.0,
        max_days_unchanged: int = 30,
    ) -> None:
        self.frequency_threshold_display = frequency_threshold_display
        self.frequency_threshold_social = frequency_threshold_social
        self.ctr_decline_threshold_pct = ctr_decline_threshold_pct
        self.cpa_increase_threshold_pct = cpa_increase_threshold_pct
        self.max_days_unchanged = max_days_unchanged

    # ------------------------------------------------------------------
    # check_fatigue
    # ------------------------------------------------------------------

    def check_fatigue(
        self,
        entity_id: str,
        platform: str,
        performance_history: List[Dict[str, Any]],
    ) -> FatigueIndicators:
        """Analyze performance history and return fatigue indicators.

        *performance_history* is a list of daily snapshots ordered by date
        ascending::

            [{"date": str, "impressions": int, "clicks": int,
              "ctr": float, "conversions": float, "cpa": float,
              "frequency": float}, ...]
        """
        indicators = FatigueIndicators(
            entity_id=entity_id,
            platform=platform,
        )

        if not performance_history:
            return indicators

        days_running = len(performance_history)
        indicators.days_running = days_running

        # Most recent snapshot
        current = performance_history[-1]
        current_frequency = float(current.get("frequency", 0.0))
        ctr_current = float(current.get("ctr", 0.0))
        cpa_current = float(current.get("cpa", 0.0))
        indicators.current_frequency = current_frequency
        indicators.ctr_current = ctr_current
        indicators.cpa_current = cpa_current

        # Snapshot from ~7 days ago (or the earliest available)
        idx_7d = max(0, len(performance_history) - 8)
        snapshot_7d = performance_history[idx_7d]
        ctr_7d_ago = float(snapshot_7d.get("ctr", 0.0))
        cpa_7d_ago = float(snapshot_7d.get("cpa", 0.0))
        freq_7d_ago = float(snapshot_7d.get("frequency", 0.0))
        indicators.ctr_7d_ago = ctr_7d_ago
        indicators.cpa_7d_ago = cpa_7d_ago

        # Compute percentage changes
        indicators.ctr_change_pct = calculate_pct_change(ctr_7d_ago, ctr_current)
        indicators.cpa_change_pct = calculate_pct_change(cpa_7d_ago, cpa_current)

        # Frequency trend
        if freq_7d_ago > 0:
            freq_change = calculate_pct_change(freq_7d_ago, current_frequency)
            if freq_change > 10.0:
                indicators.frequency_trend = "increasing"
            elif freq_change < -10.0:
                indicators.frequency_trend = "decreasing"
            else:
                indicators.frequency_trend = "stable"

        # --- Fatigue condition 1: Frequency threshold ---
        is_social = platform.lower() in (
            "meta_ads", "meta", "facebook", "instagram",
            "tiktok", "snapchat", "pinterest",
        )
        freq_threshold = (
            self.frequency_threshold_social if is_social
            else self.frequency_threshold_display
        )
        if current_frequency > freq_threshold:
            indicators.fatigue_reasons.append(
                f"Frequency ({current_frequency:.1f}) exceeds "
                f"threshold ({freq_threshold:.1f})"
            )

        # --- Fatigue condition 2: CTR declining ---
        if ctr_7d_ago > 0 and indicators.ctr_change_pct < -self.ctr_decline_threshold_pct:
            indicators.fatigue_reasons.append(
                f"CTR declined {abs(indicators.ctr_change_pct):.1f}% "
                f"over 7 days ({ctr_7d_ago:.4f} -> {ctr_current:.4f})"
            )

        # --- Fatigue condition 3: CPA increasing ---
        if cpa_7d_ago > 0 and indicators.cpa_change_pct > self.cpa_increase_threshold_pct:
            indicators.fatigue_reasons.append(
                f"CPA increased {indicators.cpa_change_pct:.1f}% "
                f"over 7 days (${cpa_7d_ago:.2f} -> ${cpa_current:.2f})"
            )

        # --- Fatigue condition 4: Creative running too long ---
        if days_running > self.max_days_unchanged:
            indicators.fatigue_reasons.append(
                f"Creative has been running for {days_running} days "
                f"without changes (threshold: {self.max_days_unchanged})"
            )

        indicators.is_fatigued = len(indicators.fatigue_reasons) > 0

        return indicators

    # ------------------------------------------------------------------
    # generate_fatigue_alerts
    # ------------------------------------------------------------------

    def generate_fatigue_alerts(
        self, indicators: FatigueIndicators
    ) -> List[MonitoringAlert]:
        """Generate alerts for each fatigue reason detected."""
        alerts: List[MonitoringAlert] = []
        if not indicators.is_fatigued:
            return alerts

        now = datetime.now(timezone.utc).isoformat()

        for reason in indicators.fatigue_reasons:
            lower_reason = reason.lower()

            if "frequency" in lower_reason:
                # Severity based on how far over threshold
                freq = indicators.current_frequency
                if freq > 5.0:
                    severity = "alert"
                else:
                    severity = "warning"
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.creative_fatigue.value,
                    severity=severity,
                    entity_id=indicators.entity_id,
                    entity_type="ad",
                    platform=indicators.platform,
                    title=f"High ad frequency on {indicators.entity_id}",
                    message=reason,
                    data={
                        "current_frequency": indicators.current_frequency,
                        "frequency_trend": indicators.frequency_trend,
                    },
                    recommended_action=(
                        "Refresh creative or narrow audience. "
                        "Consider new ad variants."
                    ),
                    recommended_action_type="refresh_creative",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif "ctr" in lower_reason:
                decline = abs(indicators.ctr_change_pct)
                if decline > 30.0:
                    severity = "alert"
                else:
                    severity = "warning"
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.creative_fatigue.value,
                    severity=severity,
                    entity_id=indicators.entity_id,
                    entity_type="ad",
                    platform=indicators.platform,
                    title=f"CTR declining on {indicators.entity_id}",
                    message=reason,
                    data={
                        "ctr_current": indicators.ctr_current,
                        "ctr_7d_ago": indicators.ctr_7d_ago,
                        "ctr_change_pct": indicators.ctr_change_pct,
                    },
                    recommended_action=(
                        "Test new headlines and images. "
                        "The current creative is losing effectiveness."
                    ),
                    recommended_action_type="test_variants",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif "cpa" in lower_reason:
                increase = indicators.cpa_change_pct
                if increase > 50.0:
                    severity = "alert"
                else:
                    severity = "warning"
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.creative_fatigue.value,
                    severity=severity,
                    entity_id=indicators.entity_id,
                    entity_type="ad",
                    platform=indicators.platform,
                    title=f"CPA increasing on {indicators.entity_id}",
                    message=reason,
                    data={
                        "cpa_current": indicators.cpa_current,
                        "cpa_7d_ago": indicators.cpa_7d_ago,
                        "cpa_change_pct": indicators.cpa_change_pct,
                    },
                    recommended_action=(
                        "Review targeting and bidding. Creative may need "
                        "refresh. Consider pausing underperformers."
                    ),
                    recommended_action_type="review_campaign",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif "running for" in lower_reason:
                days = indicators.days_running
                if days >= 45:
                    severity = "alert"
                elif days >= 30:
                    severity = "warning"
                else:
                    severity = "info"
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.creative_fatigue.value,
                    severity=severity,
                    entity_id=indicators.entity_id,
                    entity_type="ad",
                    platform=indicators.platform,
                    title=f"Stale creative on {indicators.entity_id}",
                    message=reason,
                    data={"days_running": indicators.days_running},
                    recommended_action=(
                        f"Creative has been running for {days} days. "
                        f"Generate new variants to test."
                    ),
                    recommended_action_type="generate_variants",
                    auto_action_eligible=True,
                    created_at=now,
                ))

        return alerts

    # ------------------------------------------------------------------
    # get_fatigue_summary
    # ------------------------------------------------------------------

    def get_fatigue_summary(
        self, all_indicators: List[FatigueIndicators]
    ) -> Dict[str, Any]:
        """Return an aggregated fatigue summary."""
        total = len(all_indicators)
        fatigued = sum(1 for i in all_indicators if i.is_fatigued)

        # "At risk" means not yet fatigued but showing early warning signs
        at_risk = 0
        for i in all_indicators:
            if i.is_fatigued:
                continue
            at_risk_signals = 0
            if i.ctr_change_pct < -10.0:
                at_risk_signals += 1
            if i.cpa_change_pct > 15.0:
                at_risk_signals += 1
            if i.days_running > self.max_days_unchanged * 0.7:
                at_risk_signals += 1
            if i.frequency_trend == "increasing":
                at_risk_signals += 1
            if at_risk_signals >= 2:
                at_risk += 1

        healthy = total - fatigued - at_risk

        # Sort most fatigued (by number of reasons, then by CTR decline)
        most_fatigued = sorted(
            [i for i in all_indicators if i.is_fatigued],
            key=lambda x: (-len(x.fatigue_reasons), x.ctr_change_pct),
        )
        most_fatigued_summaries = [
            {
                "entity_id": i.entity_id,
                "platform": i.platform,
                "reasons": list(i.fatigue_reasons),
                "days_running": i.days_running,
                "ctr_change_pct": round(i.ctr_change_pct, 1),
            }
            for i in most_fatigued[:10]
        ]

        return {
            "total_monitored": total,
            "fatigued": fatigued,
            "at_risk": at_risk,
            "healthy": healthy,
            "most_fatigued": most_fatigued_summaries,
        }


# ============================================================================
# SpendAnomalyDetector
# ============================================================================


class SpendAnomalyDetector:
    """Monitors for unusual spending patterns across campaigns."""

    def __init__(
        self,
        overspend_threshold_pct: float = 50.0,
        zero_spend_hours: int = 48,
        cpc_spike_threshold_pct: float = 50.0,
        pace_alert_threshold_pct: float = 20.0,
    ) -> None:
        self.overspend_threshold_pct = overspend_threshold_pct
        self.zero_spend_hours = zero_spend_hours
        self.cpc_spike_threshold_pct = cpc_spike_threshold_pct
        self.pace_alert_threshold_pct = pace_alert_threshold_pct

    # ------------------------------------------------------------------
    # check_daily_spend
    # ------------------------------------------------------------------

    def check_daily_spend(
        self,
        entity_id: str,
        platform: str,
        daily_budget: float,
        actual_spend: float,
    ) -> Optional[SpendAnomaly]:
        """Check whether daily spend is abnormal.

        Returns a ``SpendAnomaly`` for overspend, zero-spend, or
        significant under-spend.  Returns ``None`` if normal.
        """
        if daily_budget <= 0:
            return None

        overspend_limit = daily_budget * (1 + self.overspend_threshold_pct / 100)
        if actual_spend > overspend_limit:
            deviation = calculate_pct_change(daily_budget, actual_spend)
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="overspend",
                expected_value=daily_budget,
                actual_value=actual_spend,
                deviation_pct=deviation,
                period="last_24h",
            )

        if actual_spend == 0.0:
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="zero_spend",
                expected_value=daily_budget,
                actual_value=0.0,
                deviation_pct=-100.0,
                period="last_24h",
            )

        underspend_floor = daily_budget * 0.2
        if actual_spend < underspend_floor:
            deviation = calculate_pct_change(daily_budget, actual_spend)
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="underspend",
                expected_value=daily_budget,
                actual_value=actual_spend,
                deviation_pct=deviation,
                period="last_24h",
            )

        return None

    # ------------------------------------------------------------------
    # check_spend_velocity
    # ------------------------------------------------------------------

    def check_spend_velocity(
        self,
        entity_id: str,
        platform: str,
        monthly_budget: float,
        current_month_spend: float,
        day_of_month: int,
    ) -> Optional[SpendAnomaly]:
        """Check whether monthly spend pacing is abnormal.

        Detects pace-fast, pace-slow, and projected budget exhaustion.
        """
        if monthly_budget <= 0 or day_of_month <= 0:
            return None

        expected_spend = monthly_budget * (day_of_month / 30.4)
        if expected_spend <= 0:
            return None

        deviation = calculate_pct_change(expected_spend, current_month_spend)

        # Project when budget will exhaust
        daily_avg = current_month_spend / day_of_month if day_of_month > 0 else 0
        if daily_avg > 0:
            days_to_exhaust = (monthly_budget - current_month_spend) / daily_avg
            projected_exhaust_day = day_of_month + days_to_exhaust
        else:
            projected_exhaust_day = 999  # effectively never

        # Critical: projected to exhaust before month end
        if projected_exhaust_day < 28 and deviation > self.pace_alert_threshold_pct:
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="pace_fast",
                expected_value=expected_spend,
                actual_value=current_month_spend,
                deviation_pct=deviation,
                period=f"month_to_day_{day_of_month}",
            )

        # Fast pacing
        if deviation > self.pace_alert_threshold_pct:
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="pace_fast",
                expected_value=expected_spend,
                actual_value=current_month_spend,
                deviation_pct=deviation,
                period=f"month_to_day_{day_of_month}",
            )

        # Slow pacing
        if deviation < -self.pace_alert_threshold_pct:
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="pace_slow",
                expected_value=expected_spend,
                actual_value=current_month_spend,
                deviation_pct=deviation,
                period=f"month_to_day_{day_of_month}",
            )

        return None

    # ------------------------------------------------------------------
    # check_cpc_spike
    # ------------------------------------------------------------------

    def check_cpc_spike(
        self,
        entity_id: str,
        platform: str,
        current_cpc: float,
        avg_cpc_30d: float,
    ) -> Optional[SpendAnomaly]:
        """Check for a sudden CPC increase vs. 30-day average."""
        if avg_cpc_30d <= 0:
            return None

        spike_limit = avg_cpc_30d * (1 + self.cpc_spike_threshold_pct / 100)
        if current_cpc > spike_limit:
            deviation = calculate_pct_change(avg_cpc_30d, current_cpc)
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="cpc_spike",
                expected_value=avg_cpc_30d,
                actual_value=current_cpc,
                deviation_pct=deviation,
                period="last_24h",
            )

        return None

    # ------------------------------------------------------------------
    # check_zero_activity
    # ------------------------------------------------------------------

    def check_zero_activity(
        self,
        entity_id: str,
        platform: str,
        hours_since_last_impression: float,
    ) -> Optional[SpendAnomaly]:
        """Check for extended periods with no impressions."""
        if hours_since_last_impression > self.zero_spend_hours:
            return SpendAnomaly(
                entity_id=entity_id,
                platform=platform,
                anomaly_type="zero_spend",
                expected_value=0.0,
                actual_value=hours_since_last_impression,
                deviation_pct=100.0,
                period=f"last_{hours_since_last_impression:.0f}h",
            )
        return None

    # ------------------------------------------------------------------
    # generate_spend_alerts
    # ------------------------------------------------------------------

    def generate_spend_alerts(
        self, anomalies: List[SpendAnomaly]
    ) -> List[MonitoringAlert]:
        """Map each ``SpendAnomaly`` to a structured ``MonitoringAlert``."""
        alerts: List[MonitoringAlert] = []
        now = datetime.now(timezone.utc).isoformat()

        for anomaly in anomalies:
            atype = anomaly.anomaly_type
            dev = abs(anomaly.deviation_pct)

            if atype == "overspend":
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.spend_anomaly.value,
                    severity="alert",
                    entity_id=anomaly.entity_id,
                    entity_type="campaign",
                    platform=anomaly.platform,
                    title=f"Daily overspend on {anomaly.entity_id}",
                    message=(
                        f"Daily spend exceeded budget by {dev:.0f}%. "
                        f"Expected ${anomaly.expected_value:.2f}, "
                        f"actual ${anomaly.actual_value:.2f}. "
                        f"Possible causes: bid strategy overshoot, "
                        f"competitive auction."
                    ),
                    data={
                        "expected": anomaly.expected_value,
                        "actual": anomaly.actual_value,
                        "deviation_pct": anomaly.deviation_pct,
                    },
                    recommended_action=(
                        f"Daily spend exceeded budget by {dev:.0f}%. "
                        f"Possible causes: bid strategy overshoot, "
                        f"competitive auction."
                    ),
                    recommended_action_type="adjust_budget",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif atype == "zero_spend":
                hours = anomaly.actual_value
                severity = "critical" if hours >= 72 else "alert"
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.zero_activity.value,
                    severity=severity,
                    entity_id=anomaly.entity_id,
                    entity_type="campaign",
                    platform=anomaly.platform,
                    title=f"No activity on {anomaly.entity_id}",
                    message=(
                        f"No spend detected for {hours:.0f} hours. "
                        f"Check ad approval status and billing."
                    ),
                    data={
                        "hours_inactive": hours,
                        "possible_causes": [
                            "disapproved ads",
                            "budget exhausted",
                            "billing issue",
                            "targeting too narrow",
                        ],
                    },
                    recommended_action=(
                        f"No spend detected for {hours:.0f} hours. "
                        f"Check ad approval status and billing."
                    ),
                    recommended_action_type="investigate",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif atype == "cpc_spike":
                severity = "alert" if dev > 100 else "warning"
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.cpc_spike.value,
                    severity=severity,
                    entity_id=anomaly.entity_id,
                    entity_type="campaign",
                    platform=anomaly.platform,
                    title=f"CPC spike on {anomaly.entity_id}",
                    message=(
                        f"CPC spiked {dev:.0f}% above 30-day average. "
                        f"Average: ${anomaly.expected_value:.2f}, "
                        f"current: ${anomaly.actual_value:.2f}. "
                        f"Possible increased competition."
                    ),
                    data={
                        "avg_cpc_30d": anomaly.expected_value,
                        "current_cpc": anomaly.actual_value,
                        "spike_pct": anomaly.deviation_pct,
                    },
                    recommended_action=(
                        f"CPC spiked {dev:.0f}% above 30-day average. "
                        f"Possible increased competition."
                    ),
                    recommended_action_type="review_bids",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif atype == "pace_fast":
                # Estimate exhaustion day
                daily_avg_spend = anomaly.actual_value  # rough proxy
                severity = "warning"
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.budget_pace.value,
                    severity=severity,
                    entity_id=anomaly.entity_id,
                    entity_type="campaign",
                    platform=anomaly.platform,
                    title=f"Budget pacing fast on {anomaly.entity_id}",
                    message=(
                        f"Spend is {dev:.0f}% ahead of pace. "
                        f"Monthly budget may be exhausted early."
                    ),
                    data={
                        "expected_spend": anomaly.expected_value,
                        "actual_spend": anomaly.actual_value,
                        "deviation_pct": anomaly.deviation_pct,
                    },
                    recommended_action=(
                        f"Spend is {dev:.0f}% ahead of pace. "
                        f"Monthly budget may be exhausted early."
                    ),
                    recommended_action_type="adjust_pacing",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif atype == "pace_slow":
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.budget_pace.value,
                    severity="info",
                    entity_id=anomaly.entity_id,
                    entity_type="campaign",
                    platform=anomaly.platform,
                    title=f"Budget pacing slow on {anomaly.entity_id}",
                    message=(
                        f"Spend is {dev:.0f}% behind pace. "
                        f"Ads may have delivery issues."
                    ),
                    data={
                        "expected_spend": anomaly.expected_value,
                        "actual_spend": anomaly.actual_value,
                        "deviation_pct": anomaly.deviation_pct,
                    },
                    recommended_action=(
                        f"Spend is {dev:.0f}% behind pace. "
                        f"Ads may have delivery issues."
                    ),
                    recommended_action_type="investigate",
                    auto_action_eligible=False,
                    created_at=now,
                ))

            elif atype == "underspend":
                alerts.append(MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.spend_anomaly.value,
                    severity="warning",
                    entity_id=anomaly.entity_id,
                    entity_type="campaign",
                    platform=anomaly.platform,
                    title=f"Significant underspend on {anomaly.entity_id}",
                    message=(
                        f"Daily spend (${anomaly.actual_value:.2f}) is well "
                        f"below budget (${anomaly.expected_value:.2f}). "
                        f"Ads may have delivery or targeting issues."
                    ),
                    data={
                        "expected": anomaly.expected_value,
                        "actual": anomaly.actual_value,
                        "deviation_pct": anomaly.deviation_pct,
                    },
                    recommended_action=(
                        "Check ad approval status, targeting breadth, "
                        "and bid competitiveness."
                    ),
                    recommended_action_type="investigate",
                    auto_action_eligible=False,
                    created_at=now,
                ))

        return alerts


# ============================================================================
# UnderperformanceDetector
# ============================================================================


class UnderperformanceDetector:
    """Monitors campaigns that are not meeting targets or benchmarks."""

    def __init__(self, underperformance_days: int = 14) -> None:
        self.underperformance_days = underperformance_days

    # ------------------------------------------------------------------
    # check_against_target
    # ------------------------------------------------------------------

    def check_against_target(
        self,
        entity_id: str,
        platform: str,
        metric: str,
        target_value: float,
        current_value: float,
        days_below_target: int,
    ) -> Optional[MonitoringAlert]:
        """Generate an alert when a metric misses its target for too long.

        For ROAS/CTR, "below" target is bad.  For CPA, "above" target is bad.
        """
        # Determine whether the current value is underperforming
        is_underperforming = False
        if metric in ("roas", "ctr", "conversion_rate"):
            is_underperforming = current_value < target_value
        elif metric == "cpa":
            is_underperforming = current_value > target_value
        else:
            is_underperforming = current_value < target_value

        if not is_underperforming:
            return None
        if days_below_target < self.underperformance_days:
            return None

        # Severity based on duration
        if days_below_target > 30:
            severity = "critical"
        elif days_below_target > 21:
            severity = "alert"
        else:
            severity = "warning"

        now = datetime.now(timezone.utc).isoformat()

        # Build metric-specific recommended action
        if metric == "roas":
            recommended = (
                f"Campaign ROAS ({current_value:.2f}) is below target "
                f"({target_value:.2f}). Review audience targeting, "
                f"landing page, and offer strength."
            )
        elif metric == "cpa":
            recommended = (
                f"Campaign CPA (${current_value:.2f}) exceeds target "
                f"(${target_value:.2f}). Consider tightening targeting, "
                f"improving ad relevance, or revising bid strategy."
            )
        elif metric in ("ctr", "conversion_rate"):
            recommended = (
                f"Campaign {metric.upper()} ({current_value * 100:.2f}%) "
                f"is below target ({target_value * 100:.2f}%). "
                f"Test new headlines and creative. "
                f"Current ads may not be resonating."
            )
        else:
            recommended = (
                f"Campaign {metric} ({current_value}) is below target "
                f"({target_value}). Review campaign settings."
            )

        return MonitoringAlert(
            id=generate_alert_id(),
            category=AlertCategory.underperformance.value,
            severity=severity,
            entity_id=entity_id,
            entity_type="campaign",
            platform=platform,
            title=f"{metric.upper()} underperforming on {entity_id}",
            message=(
                f"{metric.upper()} has been below target for "
                f"{days_below_target} consecutive days."
            ),
            data={
                "metric": metric,
                "target": target_value,
                "current": current_value,
                "days_below_target": days_below_target,
            },
            recommended_action=recommended,
            recommended_action_type="optimize_campaign",
            auto_action_eligible=False,
            created_at=now,
        )

    # ------------------------------------------------------------------
    # check_against_benchmark
    # ------------------------------------------------------------------

    def check_against_benchmark(
        self,
        entity_id: str,
        platform: str,
        campaign_type: str,
        industry: Optional[str],
        performance: Dict[str, float],
    ) -> List[PerformanceBenchmark]:
        """Compare current performance against ``INDUSTRY_BENCHMARKS``.

        Returns a ``PerformanceBenchmark`` for every metric that has
        a benchmark entry.
        """
        platform_data = INDUSTRY_BENCHMARKS.get(platform, {})
        industry_data = platform_data.get(industry or "default")
        if industry_data is None:
            industry_data = platform_data.get("default", {})

        benchmarks: List[PerformanceBenchmark] = []
        source = f"INDUSTRY_BENCHMARKS[{platform}][{industry or 'default'}]"

        for metric_name, bench_value in industry_data.items():
            current = performance.get(metric_name)
            if current is None:
                continue

            # Determine comparison
            if bench_value == 0:
                comparison = "at"
            else:
                pct_diff = ((current - bench_value) / bench_value) * 100
                # For CPA / cost_per_lead: lower is better, so flip logic
                if metric_name in ("cpa", "cost_per_lead"):
                    if pct_diff < -10:
                        comparison = "above"  # below benchmark CPA = good
                    elif pct_diff > 30:
                        comparison = "far_below"
                    elif pct_diff > 10:
                        comparison = "below"
                    else:
                        comparison = "at"
                else:
                    if pct_diff > 10:
                        comparison = "above"
                    elif pct_diff < -30:
                        comparison = "far_below"
                    elif pct_diff < -10:
                        comparison = "below"
                    else:
                        comparison = "at"

            benchmarks.append(PerformanceBenchmark(
                metric=metric_name,
                platform=platform,
                campaign_type=campaign_type,
                industry=industry,
                benchmark_value=bench_value,
                benchmark_source=source,
                current_value=current,
                comparison=comparison,
            ))

        return benchmarks

    # ------------------------------------------------------------------
    # check_quality_scores
    # ------------------------------------------------------------------

    def check_quality_scores(
        self,
        entity_id: str,
        platform: str,
        current_quality_score: Optional[float],
        previous_quality_score: Optional[float],
    ) -> Optional[MonitoringAlert]:
        """Detect low quality scores or significant quality drops."""
        if current_quality_score is None:
            return None

        now = datetime.now(timezone.utc).isoformat()

        # Low quality score
        if current_quality_score < 5:
            return MonitoringAlert(
                id=generate_alert_id(),
                category=AlertCategory.quality_degradation.value,
                severity="alert",
                entity_id=entity_id,
                entity_type="ad",
                platform=platform,
                title=f"Low quality score on {entity_id}",
                message=(
                    f"Quality score is low ({current_quality_score:.0f}/10). "
                    f"Improve ad relevance, landing page experience, "
                    f"or expected CTR."
                ),
                data={
                    "current_quality_score": current_quality_score,
                    "previous_quality_score": previous_quality_score,
                },
                recommended_action=(
                    f"Quality score is low ({current_quality_score:.0f}/10). "
                    f"Improve ad relevance, landing page experience, "
                    f"or expected CTR."
                ),
                recommended_action_type="improve_quality",
                auto_action_eligible=False,
                created_at=now,
            )

        # Quality score drop
        if previous_quality_score is not None:
            drop = previous_quality_score - current_quality_score
            if drop >= 2:
                return MonitoringAlert(
                    id=generate_alert_id(),
                    category=AlertCategory.quality_degradation.value,
                    severity="warning",
                    entity_id=entity_id,
                    entity_type="ad",
                    platform=platform,
                    title=f"Quality score dropped on {entity_id}",
                    message=(
                        f"Quality score dropped from "
                        f"{previous_quality_score:.0f} to "
                        f"{current_quality_score:.0f}. "
                        f"Investigate recent changes."
                    ),
                    data={
                        "current_quality_score": current_quality_score,
                        "previous_quality_score": previous_quality_score,
                        "drop": drop,
                    },
                    recommended_action=(
                        f"Quality score dropped from "
                        f"{previous_quality_score:.0f} to "
                        f"{current_quality_score:.0f}. "
                        f"Investigate recent changes."
                    ),
                    recommended_action_type="investigate",
                    auto_action_eligible=False,
                    created_at=now,
                )

        return None

    # ------------------------------------------------------------------
    # generate_underperformance_report
    # ------------------------------------------------------------------

    def generate_underperformance_report(
        self,
        campaign_id: str,
        alerts: List[MonitoringAlert],
        benchmarks: List[PerformanceBenchmark],
    ) -> Dict[str, Any]:
        """Compile a structured underperformance report.

        ``health_score`` starts at 100 and is reduced by alert severity
        penalties and ``"far_below"`` benchmark comparisons.
        """
        # Calculate health score from alerts
        health = calculate_health_score(alerts)

        # Additional penalty for far-below benchmarks
        for b in benchmarks:
            if b.comparison == "far_below":
                health = max(0.0, health - 10.0)

        health = max(0.0, min(100.0, health))

        # Build priority actions
        severity_rank = {"critical": 0, "alert": 1, "warning": 2, "info": 3}
        sorted_alerts = sorted(
            alerts,
            key=lambda a: severity_rank.get(a.severity, 99),
        )
        priority_actions = [a.recommended_action for a in sorted_alerts if a.recommended_action]

        # Build benchmark comparison list
        benchmark_comparison = [
            {
                "metric": b.metric,
                "benchmark": b.benchmark_value,
                "current": b.current_value,
                "comparison": b.comparison,
                "source": b.benchmark_source,
            }
            for b in benchmarks
        ]

        # Summary
        critical_count = sum(1 for a in alerts if a.severity == "critical")
        alert_count = sum(1 for a in alerts if a.severity == "alert")
        far_below_count = sum(1 for b in benchmarks if b.comparison == "far_below")

        if critical_count > 0:
            summary = (
                f"Campaign {campaign_id} has {critical_count} critical issue(s) "
                f"requiring immediate attention."
            )
        elif alert_count > 0:
            summary = (
                f"Campaign {campaign_id} has {alert_count} alert(s) that "
                f"need action soon."
            )
        elif far_below_count > 0:
            summary = (
                f"Campaign {campaign_id} is performing well below benchmarks "
                f"on {far_below_count} metric(s)."
            )
        elif alerts:
            summary = (
                f"Campaign {campaign_id} has {len(alerts)} minor issue(s) "
                f"to monitor."
            )
        else:
            summary = f"Campaign {campaign_id} is performing within acceptable ranges."

        return {
            "campaign_id": campaign_id,
            "health_score": round(health, 1),
            "alerts": [a.model_dump() for a in sorted_alerts],
            "benchmark_comparison": benchmark_comparison,
            "priority_actions": priority_actions,
            "summary": summary,
        }


# ============================================================================
# PaidMediaMonitor
# ============================================================================


class PaidMediaMonitor:
    """Unified monitoring coordinator that runs all detectors.

    Orchestrates fatigue, spend anomaly, and underperformance checks
    across all campaigns in a single monitoring cycle.
    """

    def __init__(
        self,
        fatigue_detector: Optional[FatigueDetector] = None,
        spend_detector: Optional[SpendAnomalyDetector] = None,
        performance_detector: Optional[UnderperformanceDetector] = None,
    ) -> None:
        self.fatigue_detector = fatigue_detector or FatigueDetector()
        self.spend_detector = spend_detector or SpendAnomalyDetector()
        self.performance_detector = performance_detector or UnderperformanceDetector()
        self._alerts: Dict[str, MonitoringAlert] = {}

    # ------------------------------------------------------------------
    # run_monitoring_cycle
    # ------------------------------------------------------------------

    def run_monitoring_cycle(
        self,
        campaigns: List[Dict[str, Any]],
        performance_data: Dict[str, List[Dict[str, Any]]],
        budget_data: Dict[str, Dict[str, Any]],
        targets: Dict[str, Dict[str, float]],
    ) -> MonitoringSnapshot:
        """Run all detectors across all campaigns and return a snapshot.

        Parameters
        ----------
        campaigns:
            List of campaign dicts with keys ``id``, ``platform``,
            ``status``, ``budget``, ``industry``.
        performance_data:
            ``campaign_id -> [daily_snapshots]`` for fatigue checks.
        budget_data:
            ``campaign_id -> {daily_budget, monthly_budget,
            current_month_spend, day_of_month}``.
        targets:
            ``campaign_id -> {metric: target_value}``.
        """
        all_alerts: List[MonitoringAlert] = []

        for campaign in campaigns:
            cid = campaign.get("id", "")
            platform = campaign.get("platform", "")
            status = campaign.get("status", "enabled")
            industry = campaign.get("industry")

            if status in ("removed", "ended"):
                continue

            # --- Fatigue detection ---
            perf_history = performance_data.get(cid, [])
            if perf_history:
                indicators = self.fatigue_detector.check_fatigue(
                    entity_id=cid,
                    platform=platform,
                    performance_history=perf_history,
                )
                fatigue_alerts = self.fatigue_detector.generate_fatigue_alerts(indicators)
                all_alerts.extend(fatigue_alerts)

            # --- Spend anomaly detection ---
            budget = budget_data.get(cid, {})
            daily_budget = budget.get("daily_budget", 0.0)
            monthly_budget = budget.get("monthly_budget", 0.0)
            current_month_spend = budget.get("current_month_spend", 0.0)
            day_of_month = budget.get("day_of_month", 1)

            # Daily spend check (use the last day's cost from performance history)
            if perf_history and daily_budget > 0:
                last_day = perf_history[-1]
                actual_daily = float(last_day.get("cost", last_day.get("spend", 0.0)))
                daily_anomaly = self.spend_detector.check_daily_spend(
                    entity_id=cid,
                    platform=platform,
                    daily_budget=daily_budget,
                    actual_spend=actual_daily,
                )
                if daily_anomaly:
                    daily_alerts = self.spend_detector.generate_spend_alerts([daily_anomaly])
                    all_alerts.extend(daily_alerts)

            # Velocity check
            if monthly_budget > 0:
                velocity_anomaly = self.spend_detector.check_spend_velocity(
                    entity_id=cid,
                    platform=platform,
                    monthly_budget=monthly_budget,
                    current_month_spend=current_month_spend,
                    day_of_month=day_of_month,
                )
                if velocity_anomaly:
                    velocity_alerts = self.spend_detector.generate_spend_alerts(
                        [velocity_anomaly]
                    )
                    all_alerts.extend(velocity_alerts)

            # CPC spike check
            if perf_history and len(perf_history) >= 7:
                current_cpc = float(perf_history[-1].get("cpc", 0.0))
                avg_cpc_30d = sum(
                    float(d.get("cpc", 0.0)) for d in perf_history
                ) / len(perf_history)
                cpc_anomaly = self.spend_detector.check_cpc_spike(
                    entity_id=cid,
                    platform=platform,
                    current_cpc=current_cpc,
                    avg_cpc_30d=avg_cpc_30d,
                )
                if cpc_anomaly:
                    cpc_alerts = self.spend_detector.generate_spend_alerts([cpc_anomaly])
                    all_alerts.extend(cpc_alerts)

            # --- Underperformance detection ---
            campaign_targets = targets.get(cid, {})
            if perf_history and campaign_targets:
                latest_perf = perf_history[-1]
                for metric_name, target_val in campaign_targets.items():
                    current_val = float(latest_perf.get(metric_name, 0.0))
                    # Estimate days below target from the tail of performance history
                    days_below = 0
                    for day in reversed(perf_history):
                        day_val = float(day.get(metric_name, 0.0))
                        is_below = False
                        if metric_name == "cpa":
                            is_below = day_val > target_val
                        else:
                            is_below = day_val < target_val
                        if is_below:
                            days_below += 1
                        else:
                            break

                    target_alert = self.performance_detector.check_against_target(
                        entity_id=cid,
                        platform=platform,
                        metric=metric_name,
                        target_value=target_val,
                        current_value=current_val,
                        days_below_target=days_below,
                    )
                    if target_alert:
                        all_alerts.extend([target_alert])

        # Deduplicate by (entity_id, category, anomaly_type/title)
        seen: set = set()
        deduped: List[MonitoringAlert] = []
        for alert in all_alerts:
            key = (alert.entity_id, alert.category, alert.title)
            if key not in seen:
                seen.add(key)
                deduped.append(alert)
                self._alerts[alert.id] = alert

        # Sort by severity
        severity_rank = {"critical": 0, "alert": 1, "warning": 2, "info": 3}
        deduped.sort(key=lambda a: severity_rank.get(a.severity, 99))

        # Build snapshot
        alerts_by_severity: Dict[str, int] = {}
        alerts_by_category: Dict[str, int] = {}
        for alert in deduped:
            alerts_by_severity[alert.severity] = (
                alerts_by_severity.get(alert.severity, 0) + 1
            )
            alerts_by_category[alert.category] = (
                alerts_by_category.get(alert.category, 0) + 1
            )

        # Determine overall health
        critical_count = alerts_by_severity.get("critical", 0)
        alert_count = alerts_by_severity.get("alert", 0)
        warning_count = alerts_by_severity.get("warning", 0)

        if critical_count > 0:
            overall_health = "critical"
        elif alert_count > 0:
            overall_health = "action_required"
        elif warning_count > 0:
            overall_health = "attention_needed"
        else:
            overall_health = "healthy"

        return MonitoringSnapshot(
            timestamp=datetime.now(timezone.utc).isoformat(),
            campaigns_monitored=len(
                [c for c in campaigns if c.get("status") not in ("removed", "ended")]
            ),
            alerts_generated=len(deduped),
            alerts_by_severity=alerts_by_severity,
            alerts_by_category=alerts_by_category,
            top_alerts=deduped[:10],
            overall_health=overall_health,
        )

    # ------------------------------------------------------------------
    # get_actionable_alerts
    # ------------------------------------------------------------------

    def get_actionable_alerts(
        self, snapshot: MonitoringSnapshot
    ) -> List[MonitoringAlert]:
        """Filter to unacknowledged alerts at warning severity or higher."""
        severity_rank = {"critical": 0, "alert": 1, "warning": 2, "info": 3}
        actionable = [
            a
            for a in snapshot.top_alerts
            if severity_rank.get(a.severity, 99) <= 2 and not a.acknowledged
        ]
        actionable.sort(
            key=lambda a: (severity_rank.get(a.severity, 99), a.created_at)
        )
        return actionable

    # ------------------------------------------------------------------
    # acknowledge_alert
    # ------------------------------------------------------------------

    def acknowledge_alert(self, alert_id: str) -> MonitoringAlert:
        """Mark an alert as acknowledged."""
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise KeyError(f"Alert {alert_id} not found")
        alert.acknowledged = True
        alert.acknowledged_at = datetime.now(timezone.utc).isoformat()
        self._alerts[alert_id] = alert
        return alert

    # ------------------------------------------------------------------
    # resolve_alert
    # ------------------------------------------------------------------

    def resolve_alert(self, alert_id: str) -> MonitoringAlert:
        """Mark an alert as resolved."""
        alert = self._alerts.get(alert_id)
        if alert is None:
            raise KeyError(f"Alert {alert_id} not found")
        alert.resolved = True
        alert.resolved_at = datetime.now(timezone.utc).isoformat()
        self._alerts[alert_id] = alert
        return alert
