# Task 060: Build scorecards and dashboard summary objects

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 10. Analytics, Attribution, and Monitoring
**Priority:** P2
**Depends on:** 057
**Estimated complexity:** Medium

## Context

Operators need a single-glance view of marketing health. Instead of dumping 15 KPIs at them, the scorecard system groups metrics into five strategic categories (visibility, lead flow, conversions, repeat business, spend efficiency), scores each 0-100, and rolls everything up into an overall health score. This is the "executive summary" of marketing performance that drives the operator dashboard (Task 078) and weekly digest notifications (Task 072). Each scorecard answers one strategic question: "Are we being found?" / "Are leads coming in?" / "Are leads converting?" / "Are customers coming back?" / "Are we spending wisely?"

## Scope

Create `kai/analytics/scorecards.py` containing five scorecard models, a dashboard summary aggregator, and per-channel rollup logic. Pure data models and scoring functions — no API calls.

## Detailed Requirements

### File: `kai/analytics/scorecards.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: ScorecardHealth**
- `excellent` — score 80-100
- `good` — score 60-79
- `needs_attention` — score 40-59
- `poor` — score 20-39
- `critical` — score 0-19

**Model: ScorecardMetric**
- `metric_name: str`
- `display_name: str`
- `value: Optional[float]`
- `target: Optional[float]`
- `benchmark: Optional[float]`
- `weight: float` — how much this metric contributes to the scorecard score (0.0-1.0, weights within a scorecard should sum to 1.0)
- `score_contribution: Optional[float]` — this metric's weighted contribution to the category score
- `trend: Optional[str]` — "up", "down", "flat", "new"
- `trend_value: Optional[float]` — percent change

**Model: Scorecard**
- `category: str` — "visibility", "lead_flow", "conversions", "repeat_business", "spend_efficiency"
- `display_name: str`
- `description: str` — what strategic question this scorecard answers
- `score: float` — 0-100
- `health: str` — ScorecardHealth enum value
- `metrics: List[ScorecardMetric]`
- `top_insight: str` — single-sentence summary of the most important finding
- `recommended_actions: List[str]` — 1-3 specific actions to improve this score

**Function: build_visibility_scorecard(kpi_values: Dict[str, float], targets: Dict[str, float], benchmarks: Dict[str, float]) -> Scorecard**
- Description: "Are we being found by potential customers?"
- Metrics (with weights):
  - `search_impressions` (0.25) — GSC impressions
  - `gbp_views` (0.25) — GBP search + maps views
  - `social_reach` (0.15) — total social media reach
  - `direct_traffic` (0.15) — GA4 direct sessions
  - `brand_search_volume` (0.20) — branded search queries
- Scoring: for each metric, score = min(100, (value / target) * 100) if target > 0. Weighted sum across all metrics.
- Generate top_insight from the metric with the largest gap between value and target
- Generate recommended_actions based on lowest-scoring metrics

**Function: build_lead_flow_scorecard(kpi_values, targets, benchmarks) -> Scorecard**
- Description: "Are leads coming in at the right volume and cost?"
- Metrics:
  - `total_leads` (0.30) — sum of form + phone + chat leads
  - `cost_per_lead` (0.25) — inverted scoring (lower is better)
  - `lead_sources_diversity` (0.15) — number of channels generating leads / total channels (more diverse = better)
  - `phone_calls` (0.15) — call volume
  - `lead_quality_indicator` (0.15) — ratio of qualified leads to total leads
- For "lower is better" metrics: score = min(100, (target / value) * 100)

**Function: build_conversion_scorecard(kpi_values, targets, benchmarks) -> Scorecard**
- Description: "Are leads turning into customers?"
- Metrics:
  - `website_conversion_rate` (0.30)
  - `landing_page_conversion_rate` (0.25)
  - `form_completion_rate` (0.15)
  - `phone_call_rate` (0.15) — calls as percentage of sessions
  - `speed_to_lead` (0.15) — inverted scoring (lower is better)

**Function: build_repeat_business_scorecard(kpi_values, targets, benchmarks) -> Scorecard**
- Description: "Are customers coming back and referring others?"
- Metrics:
  - `repeat_customer_rate` (0.25)
  - `customer_retention_rate` (0.25)
  - `ltv_trend` (0.20) — direction of customer lifetime value
  - `referral_rate` (0.15)
  - `review_rating` (0.15)

**Function: build_spend_efficiency_scorecard(kpi_values, targets, benchmarks) -> Scorecard**
- Description: "Are we getting good return on ad spend?"
- Metrics:
  - `overall_roas` (0.30)
  - `cpa_trend` (0.25) — inverted, lower is better
  - `budget_utilization` (0.20) — percent of allocated budget actually spent
  - `per_channel_roas_best` (0.15) — best-performing channel ROAS
  - `wasted_spend_pct` (0.10) — inverted, lower is better

**Model: ChannelRollup**
- `channel: str` — "organic_search", "paid_search", "social_organic", "social_paid", "email", "direct", "referral", "phone"
- `sessions: Optional[float]`
- `leads: Optional[float]`
- `conversions: Optional[float]`
- `spend: Optional[float]`
- `revenue: Optional[float]`
- `roas: Optional[float]`
- `conversion_rate: Optional[float]`
- `cost_per_lead: Optional[float]`
- `health: str` — ScorecardHealth based on channel performance vs targets

**Model: DashboardSummary**
- `business_id: str`
- `business_name: str`
- `archetype: str`
- `generated_at: str` — ISO timestamp
- `period_start: str`
- `period_end: str`
- `overall_health_score: float` — 0-100, weighted average of all scorecard scores
- `overall_health: str` — ScorecardHealth enum value
- `scorecards: List[Scorecard]` — the five category scorecards
- `channel_rollups: List[ChannelRollup]`
- `top_3_wins: List[str]` — best-performing areas
- `top_3_concerns: List[str]` — areas needing attention
- `recommended_next_actions: List[str]` — prioritized list of what to do next
- `period_comparison: Optional[Dict[str, Any]]` — vs previous period: {overall_change_pct, improved_categories, declined_categories}

**Function: build_dashboard_summary(business_id: str, business_name: str, archetype: str, kpi_values: Dict[str, float], targets: Dict[str, float], benchmarks: Dict[str, float], channel_data: Dict[str, Dict[str, float]], period_start: str, period_end: str, previous_summary: Optional[DashboardSummary] = None) -> DashboardSummary**
- Build all five scorecards
- Calculate overall_health_score as weighted average: visibility (0.20), lead_flow (0.25), conversions (0.25), repeat_business (0.15), spend_efficiency (0.15)
- Build channel rollups from channel_data
- Extract top 3 wins (highest-scoring metrics with positive trends)
- Extract top 3 concerns (lowest-scoring metrics or negative trends)
- Build recommended_next_actions from the "critical" and "poor" scorecard recommended_actions
- If previous_summary provided, calculate period_comparison

## Output Files

- `kai/analytics/scorecards.py`

## Acceptance Criteria

- File parses as valid Python
- All five scorecard builder functions are implemented with correct metric weights that sum to 1.0
- "Lower is better" metrics (cost_per_lead, CPA, speed_to_lead) use inverted scoring logic
- Each scorecard generates a meaningful `top_insight` string (not placeholder text)
- `build_dashboard_summary` correctly weights the five scorecards in the overall score
- ScorecardHealth enum correctly maps score ranges
- All functions handle missing data gracefully (metrics with None values are excluded from scoring)
- Channel rollup model covers all major marketing channels
- Period comparison logic handles the case where previous_summary is None
- No external dependencies

## Reference Materials

- `kai/analytics/kpi_models.py` (Task 057) — KPIDefinition, KPIValue, KPIDashboard
- `kai/runtime/models.py` — SerializableModel pattern
- `knowledge/checklists/cro-audit-checklist.md` — what matters for conversion scoring
- `knowledge/playbooks/conversion-rate-optimization.md` — CRO metric priorities
