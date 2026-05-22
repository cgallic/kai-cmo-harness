"""Analytics layer for the Kai Marketing OS.

This module defines the KPI model system that maps marketing metrics to
business archetypes.  Each archetype (local service, ecommerce,
professional services, multi-location) has a curated set of KPI
definitions that specify:

- Which metrics matter and why
- Where to source the raw data (which analytics connector)
- How to calculate composite metrics from raw data points
- What industry benchmarks to compare against
- When to raise alerts for underperformance

Downstream consumers include:

- **Scorecards** (task 060) -- render KPI dashboards per business
- **Watchers** (tasks 067-072) -- fire alerts on threshold breaches
- **Attribution** (task 058) -- connect marketing actions to KPI movement
- **Proposals** -- suggest actions when KPIs decline

Usage::

    from kai.analytics.kpi_models import (
        get_kpis_for_archetype,
        calculate_health_score,
        KPIDefinition,
        KPIDashboard,
        KPIValue,
    )

    kpis = get_kpis_for_archetype("local_service")
    score = calculate_health_score(kpi_values)
"""

from kai.analytics.kpi_models import (
    AlertLevel,
    KPIDashboard,
    KPIDefinition,
    KPIValue,
    TargetDirection,
    calculate_health_score,
    get_ecommerce_kpis,
    get_kpis_for_archetype,
    get_local_service_kpis,
    get_multi_location_kpis,
    get_professional_services_kpis,
)

from kai.analytics.anomaly_detection import (
    AnomalyAlert,
    AnomalyDetector,
    AnomalySeverity,
    AnomalyType,
    ConfidenceScorer,
    MetricTimeSeries,
    SeasonalPattern,
)

from kai.analytics.attribution import (
    ActionLineage,
    ActionOutcomeLinkage,
    AttributionModel,
    AttributionSnapshot,
    ConfidenceLevel,
    MetricSnapshot,
    ObservedChange,
    apply_attribution_model,
    build_action_lineage,
    calculate_confidence,
    compute_observed_changes,
)

from kai.analytics.rewards import (
    ActionReward,
    compute_reward_score,
    get_average_rewards_by_action_type,
    load_rewards_log,
    log_action_rewards,
)

from kai.analytics.scorecards import (
    ChannelRollup,
    DashboardSummary,
    Scorecard,
    ScorecardHealth,
    ScorecardMetric,
    build_conversion_scorecard,
    build_dashboard_summary,
    build_lead_flow_scorecard,
    build_repeat_business_scorecard,
    build_spend_efficiency_scorecard,
    build_visibility_scorecard,
)

__all__ = [
    # KPI models (task 057)
    "AlertLevel",
    "KPIDashboard",
    "KPIDefinition",
    "KPIValue",
    "TargetDirection",
    "calculate_health_score",
    "get_ecommerce_kpis",
    "get_kpis_for_archetype",
    "get_local_service_kpis",
    "get_multi_location_kpis",
    "get_professional_services_kpis",
    # Attribution (task 058)
    "ActionLineage",
    "ActionOutcomeLinkage",
    "AttributionModel",
    "AttributionSnapshot",
    "ConfidenceLevel",
    "MetricSnapshot",
    "ObservedChange",
    "apply_attribution_model",
    "build_action_lineage",
    "calculate_confidence",
    "compute_observed_changes",
    # Rewards (Phase 3)
    "ActionReward",
    "compute_reward_score",
    "get_average_rewards_by_action_type",
    "load_rewards_log",
    "log_action_rewards",
    # Anomaly detection (task 059)
    "AnomalyAlert",
    "AnomalyDetector",
    "AnomalySeverity",
    "AnomalyType",
    "ConfidenceScorer",
    "MetricTimeSeries",
    "SeasonalPattern",
    # Scorecards (task 060)
    "ChannelRollup",
    "DashboardSummary",
    "Scorecard",
    "ScorecardHealth",
    "ScorecardMetric",
    "build_conversion_scorecard",
    "build_dashboard_summary",
    "build_lead_flow_scorecard",
    "build_repeat_business_scorecard",
    "build_spend_efficiency_scorecard",
    "build_visibility_scorecard",
]

