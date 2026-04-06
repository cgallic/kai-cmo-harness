# Task 057: Build KPI models per archetype

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 10. Analytics, Attribution, and Monitoring
**Priority:** P1
**Depends on:** 056, 006, 007, 008, 009
**Estimated complexity:** Medium

## Context

Different business archetypes care about fundamentally different marketing KPIs. A local plumber tracks leads per month and review count; an ecommerce store tracks ROAS and cart abandonment; a law firm tracks qualified leads and close rate. The KPI model layer defines which metrics matter for each archetype, where to source them (which analytics connector), how to calculate them, and what benchmarks to compare against. This layer feeds directly into scorecards (060), dashboards (060), watcher alerts (067-072), and the attribution system (058).

## Scope

Create `kai/analytics/kpi_models.py` containing Pydantic-style dataclass models for KPI definitions, per-archetype KPI sets, benchmark data, and dashboard aggregation models.

## Detailed Requirements

### File: `kai/analytics/__init__.py`
- Module docstring explaining the analytics layer
- Export key classes

### File: `kai/analytics/kpi_models.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: TargetDirection**
- `higher_is_better` — e.g., leads, revenue, conversion rate
- `lower_is_better` — e.g., cost per lead, bounce rate, churn rate

**Enum: AlertLevel**
- `info` — metric is slightly off-trend
- `warning` — metric is notably below target
- `critical` — metric is dangerously below target or flatlined

**Model: KPIDefinition**
- `name: str` — machine-readable name (e.g., "leads_per_month")
- `display_name: str` — human-readable name (e.g., "Leads Per Month")
- `description: str` — what this KPI measures and why it matters
- `source_connector: str` — which connector provides the raw data (e.g., "ga4", "gsc", "call_tracking", "gbp", "ad_metrics", "crm")
- `source_metrics: List[str]` — which MetricPoint metric_names to pull
- `calculation_method: str` — one of: "direct" (single metric), "sum" (sum multiple metrics), "ratio" (metric_a / metric_b), "average", "weighted_average", "custom"
- `calculation_formula: Optional[str]` — human-readable formula for non-direct calculations (e.g., "conversions / sessions * 100")
- `unit: str` — display unit: "count", "currency", "percentage", "rating", "seconds", "minutes"
- `target_direction: str` — TargetDirection enum value
- `default_benchmark: Optional[float]` — industry-average benchmark (None if varies too much)
- `benchmark_by_industry: Dict[str, float]` — industry-specific benchmarks (e.g., {"plumbing": 45, "dental": 65, "hvac": 50})
- `alert_thresholds: Dict[str, float]` — threshold multipliers for alerts: {"warning": 0.7, "critical": 0.4} meaning warn at 70% of target, critical at 40%
- `refresh_frequency: str` — "daily", "weekly", "monthly"
- `archetype_relevance: List[str]` — which archetypes this KPI applies to

**Model: KPIValue**
- `kpi_name: str` — references KPIDefinition.name
- `value: Optional[float]` — current value (None if no data yet)
- `date: str` — date of this value (ISO format)
- `trend_7d: Optional[float]` — percent change over last 7 days
- `trend_30d: Optional[float]` — percent change over last 30 days
- `trend_90d: Optional[float]` — percent change over last 90 days
- `vs_target: Optional[float]` — percent of target achieved (e.g., 0.85 = 85% of target)
- `vs_benchmark: Optional[float]` — percent of industry benchmark (e.g., 1.2 = 120% of benchmark)
- `alert_level: Optional[str]` — AlertLevel if thresholds are breached, else None
- `data_quality: str` — "complete", "partial", "estimated", "unavailable"

**Model: KPIDashboard**
- `business_id: str`
- `archetype: str`
- `generated_at: str` — ISO timestamp
- `period_start: str` — ISO date
- `period_end: str` — ISO date
- `kpi_values: List[KPIValue]`
- `overall_health_score: Optional[float]` — 0-100 composite score
- `top_wins: List[str]` — up to 3 KPIs trending positively
- `top_concerns: List[str]` — up to 3 KPIs trending negatively
- `period_comparison: Optional[Dict[str, Any]]` — vs previous period summary

**Function: get_local_service_kpis() -> List[KPIDefinition]**
Return definitions for:
- `leads_per_month` — source: ga4+call_tracking+crm, calculation: sum of form submissions + phone calls + chat leads
- `cost_per_lead` — source: ad_metrics, calculation: total ad spend / total leads
- `phone_calls` — source: call_tracking, calculation: direct
- `form_submissions` — source: ga4, calculation: direct (form_submit events)
- `gbp_views` — source: gbp, calculation: sum of search_views + maps_views
- `gbp_actions` — source: gbp, calculation: sum of direction_requests + phone_calls + website_clicks
- `review_count` — source: gbp, calculation: direct
- `review_rating` — source: gbp, calculation: direct
- `website_conversion_rate` — source: ga4, calculation: ratio (conversions / sessions)
- `speed_to_lead_minutes` — source: call_tracking+crm, calculation: average time to first response
- `repeat_customer_rate` — source: crm, calculation: ratio (repeat_customers / total_customers)
- `revenue_per_lead` — source: crm+ad_metrics, calculation: ratio (revenue / leads)

**Function: get_ecommerce_kpis() -> List[KPIDefinition]**
Return definitions for:
- `revenue`, `orders`, `aov` (average order value), `conversion_rate`, `cart_abandonment_rate`, `customer_ltv`, `repeat_purchase_rate`, `roas`, `email_revenue_pct`, `sessions`, `bounce_rate`, `new_vs_returning_ratio`

**Function: get_professional_services_kpis() -> List[KPIDefinition]**
Return definitions for:
- `qualified_leads`, `proposal_sent_rate`, `close_rate`, `average_engagement_value`, `client_retention_rate`, `referral_rate`, `content_views`, `linkedin_engagement`, `thought_leadership_reach`

**Function: get_multi_location_kpis() -> List[KPIDefinition]**
Return definitions for:
- All local-service KPIs (reuse via function call) plus:
- `location_consistency_score` — how consistent NAP/branding is across locations (0-100)
- `brand_search_volume` — branded search queries from GSC
- `multi_location_review_distribution` — standard deviation of review counts across locations

**Function: get_kpis_for_archetype(archetype: str) -> List[KPIDefinition]**
- Router function: given archetype string, return the right KPI set
- Supported archetypes: "local_service", "ecommerce", "professional_services", "multi_location"
- Raise ValueError for unknown archetype

**Function: calculate_health_score(kpi_values: List[KPIValue]) -> float**
- Weighted average of vs_target scores across all KPIs with data
- KPIs with alert_level "critical" get 2x weight penalty
- Return 0-100 float
- Return 0.0 if no KPIs have data

## Output Files

- `kai/analytics/__init__.py`
- `kai/analytics/kpi_models.py`

## Acceptance Criteria

- All files parse as valid Python
- Four archetype KPI functions return complete lists matching the spec above
- Every KPIDefinition has all fields populated with sensible values (no placeholder strings)
- `benchmark_by_industry` has at least 3 industry entries per KPI where benchmarks vary
- `get_kpis_for_archetype` correctly routes to each archetype function
- `calculate_health_score` has clear logic with the weighting penalty
- All dataclasses use the `SerializableModel` mixin pattern
- Multi-location KPIs include all local-service KPIs plus the additional three

## Reference Materials

- `kai/connectors/analytics/base.py` (from Task 056) — MetricPoint format and connector types
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/runtime/audit.py` — enum conventions
- `knowledge/checklists/cro-audit-checklist.md` — CRO KPIs
- `knowledge/playbooks/conversion-rate-optimization.md` — conversion metrics context
- `knowledge/playbooks/demand-generation.md` — demand gen KPIs
