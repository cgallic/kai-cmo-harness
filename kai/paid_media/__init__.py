"""Paid media operations -- budget controls, risk assessment, readiness checks,
creative variant workflows, fatigue detection, and spend anomaly monitoring."""

from kai.paid_media.controls import (
    BoundedTestBudget,
    BudgetCheckResult,
    BudgetController,
    GeoTargetingHelper,
    GeoTargetingSuggestion,
    ReadinessCheckItem,
    ReadinessChecker,
    ReadinessReport,
    ReadinessStatus,
    RiskAssessmentResult,
    RiskAssessor,
    RiskLevel,
    TestBudgetConfig,
    calculate_daily_from_monthly,
    calculate_monthly_projection,
    calculate_remaining_budget,
    days_remaining_in_month,
    format_budget_summary,
)

from kai.paid_media.variants import (
    CreativeInventory,
    CreativeInventoryItem,
    CreativeVariant,
    VariantStatus,
    VariantTest,
    VariantTestElement,
    VariantWorkflow,
    VARIANT_GENERATION_STRATEGIES,
    calculate_lift,
    calculate_z_score,
    days_since,
    generate_inventory_id,
    generate_test_id,
    generate_variant_id,
    is_significant,
)

from kai.paid_media.monitoring import (
    AlertCategory,
    AlertSeverity,
    FatigueDetector,
    FatigueIndicators,
    INDUSTRY_BENCHMARKS,
    MonitoringAlert,
    MonitoringSnapshot,
    PaidMediaMonitor,
    PerformanceBenchmark,
    SpendAnomaly,
    SpendAnomalyDetector,
    UnderperformanceDetector,
    calculate_health_score,
    calculate_pct_change,
    determine_severity,
    generate_alert_id,
    get_benchmark,
)

__all__ = [
    # Enums — controls
    "ReadinessStatus",
    "RiskLevel",
    # Models — controls
    "ReadinessCheckItem",
    "ReadinessReport",
    "BudgetCheckResult",
    "RiskAssessmentResult",
    "TestBudgetConfig",
    "GeoTargetingSuggestion",
    # Classes — controls
    "ReadinessChecker",
    "BudgetController",
    "RiskAssessor",
    "BoundedTestBudget",
    "GeoTargetingHelper",
    # Helpers — controls
    "calculate_monthly_projection",
    "calculate_daily_from_monthly",
    "days_remaining_in_month",
    "calculate_remaining_budget",
    "format_budget_summary",
    # Enums — variants
    "VariantStatus",
    "VariantTestElement",
    # Models — variants
    "CreativeVariant",
    "VariantTest",
    "CreativeInventoryItem",
    # Classes — variants
    "VariantWorkflow",
    "CreativeInventory",
    # Constants — variants
    "VARIANT_GENERATION_STRATEGIES",
    # Helpers — variants
    "generate_variant_id",
    "generate_test_id",
    "generate_inventory_id",
    "calculate_z_score",
    "is_significant",
    "calculate_lift",
    "days_since",
    # Enums — monitoring
    "AlertSeverity",
    "AlertCategory",
    # Models — monitoring
    "MonitoringAlert",
    "FatigueIndicators",
    "SpendAnomaly",
    "PerformanceBenchmark",
    "MonitoringSnapshot",
    # Classes — monitoring
    "FatigueDetector",
    "SpendAnomalyDetector",
    "UnderperformanceDetector",
    "PaidMediaMonitor",
    # Constants — monitoring
    "INDUSTRY_BENCHMARKS",
    # Helpers — monitoring
    "generate_alert_id",
    "calculate_pct_change",
    "determine_severity",
    "get_benchmark",
    "calculate_health_score",
]
