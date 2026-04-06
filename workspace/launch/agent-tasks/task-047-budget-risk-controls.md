# Task 047: Build budget and risk controls with readiness checks

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 8. Paid Media Operations
**Priority:** P1
**Depends on:** 046
**Estimated complexity:** Medium

## Context

Paid media operations involve real money. Before any campaign launches or budget changes, the system must enforce rigorous controls that prevent overspend, catch misconfigured campaigns, and ensure everything is ready for live traffic. This is the "safety net" layer for paid media — it sits between the action system (Task 045) and the actual connectors (Task 044), ensuring no campaign goes live without passing readiness checks, and no budget exceeds configured limits. For local businesses especially, a single budget mistake could burn an entire month's marketing budget in a day.

## Scope

Create `kai/paid_media/controls.py` containing ReadinessCheck, BudgetControl, RiskAssessment, BoundedTestBudget, and geo/service-area targeting helpers.

## Detailed Requirements

### File: `kai/paid_media/__init__.py`

- Module docstring: "Paid media operations — budget controls, risk assessment, readiness checks, and campaign management utilities."
- Import and re-export key classes from controls.py
- `__all__` listing

### File: `kai/paid_media/controls.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: ReadinessStatus (str, Enum)**
- `ready` — all checks passed, safe to launch
- `ready_with_warnings` — checks passed but warnings exist
- `not_ready` — one or more critical checks failed
- `blocked` — a hard block prevents launch (compliance, budget, etc.)

**Enum: RiskLevel (str, Enum)**
- `low` — minimal risk (e.g., small budget test, proven creative, tight targeting)
- `medium` — moderate risk (e.g., new creative, moderate budget, new targeting)
- `high` — significant risk (e.g., large budget, broad targeting, new platform)
- `critical` — very high risk (e.g., very large budget, regulated industry, no conversion tracking)

**Model: ReadinessCheckItem**
- `check_name: str` — short name (e.g., "conversion_tracking", "landing_page_loads", "budget_within_limits")
- `category: str` — grouping: "tracking", "landing_page", "budget", "creative", "compliance", "targeting", "technical"
- `passed: bool`
- `severity: str` — "critical" (blocks launch), "warning" (doesn't block but should be addressed), "info"
- `message: str` — human-readable result description
- `remediation: Optional[str]` — how to fix if failed
- `details: Dict[str, Any]` — additional detail data, default empty dict

**Model: ReadinessReport**
- `campaign_id: Optional[str]` — campaign being checked
- `platform: str`
- `overall_status: str` — ReadinessStatus value
- `checks: List[ReadinessCheckItem]` — all check results, default empty list
- `critical_failures: int = 0` — count of critical failures
- `warnings: int = 0` — count of warnings
- `passed: int = 0` — count of passed checks
- `summary: str` — human-readable summary (e.g., "3 of 10 checks failed. 2 critical issues must be resolved before launch.")
- `checked_at: str` — ISO timestamp
- `metadata: Dict[str, Any]` — default empty dict

**Model: BudgetCheckResult**
- `is_within_limits: bool`
- `daily_budget_requested: float`
- `daily_budget_total_after: float` — total daily spend across all campaigns after this change
- `monthly_projected_after: float` — projected monthly spend after this change
- `daily_cap: Optional[float]` — configured daily cap
- `monthly_cap: Optional[float]` — configured monthly cap
- `daily_utilization_pct: float = 0.0`
- `monthly_utilization_pct: float = 0.0`
- `warnings: List[str]` — default empty list
- `blocks: List[str]` — hard blocks, default empty list
- `recommended_budget: Optional[float]` — suggested budget if requested is too high

**Model: RiskAssessmentResult**
- `risk_level: str` — RiskLevel value
- `risk_score: float` — 0-100, higher = riskier
- `risk_factors: List[Dict[str, Any]]` — list of {factor, impact, score, explanation}, default empty list
- `mitigations: List[str]` — recommended risk mitigation steps, default empty list
- `approval_required: bool = False` — whether human approval is required at this risk level
- `summary: str`

**Model: TestBudgetConfig**
- `test_phase_days: int = 7` — how long the test phase lasts
- `test_daily_budget: float` — daily budget during test phase
- `scale_daily_budget: float` — daily budget to scale to after test (if successful)
- `success_criteria: Dict[str, float]` — KPIs that must be met to graduate from test, e.g., {"cpa_max": 50.0, "ctr_min": 0.02, "conversions_min": 5}
- `auto_scale_on_success: bool = False` — automatically increase budget if test passes
- `auto_pause_on_failure: bool = True` — automatically pause if test fails
- `current_phase: str` — "test", "evaluation", "scaling", "scaled", default "test"
- `test_start_date: Optional[str]`
- `test_end_date: Optional[str]`
- `evaluation_result: Optional[str]` — "passed", "failed", "inconclusive"

**Model: GeoTargetingSuggestion**
- `location: str` — location name or description
- `location_type: str` — "radius", "city", "zip", "county", "state"
- `radius_miles: Optional[float]` — radius if type is "radius"
- `center_point: Optional[str]` — center address/location for radius targeting
- `estimated_population: Optional[int]`
- `reason: str` — why this targeting is suggested
- `priority: str` — "primary", "secondary", "expansion"

**Class: ReadinessChecker**

Runs comprehensive readiness checks before launching any campaign.

Methods:
- `__init__(self)` — initialize
- `check_campaign_readiness(self, campaign_config: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> ReadinessReport` — run all readiness checks and return a comprehensive report. Calls each individual check method and aggregates results.

Individual check methods (each returns a ReadinessCheckItem):

- `_check_conversion_tracking(self, config: Dict[str, Any]) -> ReadinessCheckItem`:
  - Critical check. Look for `conversion_tracking_id` or `pixel_id` in config.
  - If missing: FAIL, critical, "No conversion tracking configured. Campaign will run blind — unable to optimize for conversions or measure ROI."
  - Remediation: "Set up Google conversion tag or Meta pixel before launching."
  - If present: PASS, "Conversion tracking is configured."

- `_check_landing_page(self, config: Dict[str, Any]) -> ReadinessCheckItem`:
  - Critical check. Look for `landing_urls` in config.
  - If missing or empty: FAIL, critical, "No landing page specified."
  - If present: check URL format (has https://, has a path, not a homepage unless intentional).
  - Warn if landing page is the homepage (usually means better landing page needed).
  - Remediation: "Create a dedicated landing page that matches your ad message."

- `_check_landing_page_message_match(self, config: Dict[str, Any]) -> ReadinessCheckItem`:
  - Warning check. Compare ad headlines/offer with landing page URL slug or any provided page metadata.
  - If ad mentions an offer but landing URL doesn't reference it: WARN, "Ad message may not match landing page. Ensure the landing page prominently features the same offer/message as the ad."
  - This is a heuristic — warn broadly, let operator verify.

- `_check_budget_within_limits(self, config: Dict[str, Any], budget_guard: Optional[Dict[str, Any]] = None) -> ReadinessCheckItem`:
  - Critical check. If budget_guard is provided, validate the campaign budget against caps.
  - If daily budget > daily cap: FAIL, critical, "Campaign budget (${budget}/day) exceeds daily spend cap (${cap}/day)."
  - If projected monthly > monthly cap: FAIL, critical, "Projected monthly spend (${projected}/mo) exceeds monthly cap (${cap}/mo)."
  - If within limits but >80% of remaining budget: WARN, "Campaign will consume {pct}% of remaining monthly budget."
  - If no budget_guard provided: WARN, "No budget guard configured. Set spending limits to prevent overspend."

- `_check_creative_assets(self, config: Dict[str, Any]) -> ReadinessCheckItem`:
  - Critical check. Verify creative assets are present and meet minimum requirements.
  - Google Search: need 3+ headlines, 2+ descriptions
  - Meta: need primary text, headline, media asset
  - If insufficient: FAIL, critical, "Insufficient creative assets."
  - Remediation: list what's missing.

- `_check_compliance(self, config: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> ReadinessCheckItem`:
  - Critical check for regulated industries.
  - If business_profile indicates regulated industry (healthcare, finance, legal, gambling, alcohol, cannabis):
    - Check for required disclaimers, certifications, age gates
    - If missing: FAIL, critical, "Regulated industry ({industry}) requires additional compliance. Missing: {items}."
  - If Meta and industry is housing/employment/credit:
    - Check special_ad_category is set
    - If missing: FAIL, critical, "Meta requires Special Ad Category declaration for {category} advertising."
  - If not regulated: PASS with info note about general compliance.

- `_check_audience_definition(self, config: Dict[str, Any]) -> ReadinessCheckItem`:
  - Warning check. Evaluate targeting breadth.
  - If no location, no interest, no audience targeting: WARN, "Targeting is very broad. Consider adding location and interest targeting to improve relevance."
  - If targeting is extremely narrow (e.g., single zip code + narrow age + single interest): WARN, "Targeting may be too narrow. Estimated reach could be very limited."
  - If local business has no location targeting: FAIL, critical, "Local business campaigns must have location targeting."

- `_check_platform_requirements(self, config: Dict[str, Any]) -> ReadinessCheckItem`:
  - Warning check. Platform-specific requirements.
  - Google: verify keyword list for search campaigns
  - Meta: verify pixel events are set up for conversion objective
  - General: verify bid strategy matches objective

**Class: BudgetController**

Enforces spending limits and budget safety.

Methods:
- `__init__(self, budget_guard: Dict[str, Any])` — initialize with BudgetGuard configuration
- `check_budget_change(self, campaign_id: str, new_daily_budget: float, current_campaigns: List[Dict[str, Any]]) -> BudgetCheckResult`:
  1. Sum current daily budgets of all campaigns (excluding the one being changed)
  2. Add new_daily_budget to get total
  3. Calculate monthly projection: total * 30.4
  4. Check against daily cap and monthly cap
  5. Generate warnings at 70%, 80%, 90% utilization
  6. Generate blocks at 100%+ utilization
  7. If blocked, calculate recommended_budget (what budget WOULD fit within limits)
  8. Return BudgetCheckResult

- `check_launch_budget(self, new_campaign_budget: float, current_campaigns: List[Dict[str, Any]]) -> BudgetCheckResult`:
  - Same as check_budget_change but for a brand-new campaign (no existing campaign to subtract)
  - Additional check: if this would be the most expensive campaign, warn

- `monitor_spend(self, current_daily_spend: float, current_monthly_spend: float, day_of_month: int) -> Dict[str, Any]`:
  - Calculate pace: on track, underspending, overspending
  - Project end-of-month spend based on current pace
  - Return: `{"pace": str, "daily_spend": float, "monthly_spend": float, "projected_monthly": float, "utilization_pct": float, "alert": bool, "auto_pause": bool, "message": str}`
  - Alert if utilization > alert_threshold_pct
  - Auto-pause signal if utilization > auto_pause_threshold_pct

- `recommend_budget_allocation(self, monthly_budget: float, campaign_count: int, campaign_priorities: Optional[Dict[str, int]] = None) -> Dict[str, float]`:
  - Given a total monthly budget and number of campaigns, suggest daily budget per campaign
  - If priorities provided (campaign_id -> priority 1-5), allocate proportionally
  - Reserve 10% as buffer for overages
  - Return campaign_id -> daily_budget mapping

**Class: RiskAssessor**

Scores campaign risk.

Methods:
- `__init__(self)` — initialize risk factor weights
- `assess_campaign_risk(self, campaign_config: Dict[str, Any], business_profile: Optional[Dict[str, Any]] = None) -> RiskAssessmentResult`:
  - Score each risk factor (0-20 each, higher = riskier):
    1. **Spend level** (weight: 20):
       - <$10/day: 0, $10-50/day: 5, $50-100/day: 10, $100-500/day: 15, >$500/day: 20
    2. **Audience breadth** (weight: 20):
       - Very targeted: 0, Moderate: 10, Very broad: 15, No targeting: 20
    3. **Creative compliance** (weight: 20):
       - Compliance checked and passed: 0, Not checked: 10, Known issues: 20
    4. **Landing page quality** (weight: 15):
       - Dedicated LP with message match: 0, Homepage: 10, No LP: 15
    5. **Industry regulations** (weight: 15):
       - Unregulated: 0, Lightly regulated: 5, Heavily regulated (healthcare, finance): 15
    6. **Platform track record** (weight: 10):
       - Existing successful campaigns: 0, No history on platform: 5, Previous disapprovals: 10
  - Total risk score = sum of all factors (0-100)
  - risk_level: low (0-25), medium (26-50), high (51-75), critical (76-100)
  - approval_required: True if risk_level is "high" or "critical"
  - Generate mitigations for each high-scoring factor

**Class: BoundedTestBudget**

Manages test-phase budgets for new campaigns.

Methods:
- `__init__(self, config: TestBudgetConfig)` — store config
- `get_current_budget(self) -> float`:
  - If current_phase is "test": return test_daily_budget
  - If current_phase is "scaling" or "scaled": return scale_daily_budget
  - If current_phase is "evaluation": return test_daily_budget (don't change during evaluation)

- `evaluate_test_results(self, performance: Dict[str, float]) -> Dict[str, Any]`:
  - Compare performance against success_criteria
  - For each criterion: {"metric": str, "target": float, "actual": float, "passed": bool}
  - Overall result: "passed" (all criteria met), "failed" (any critical criterion missed), "inconclusive" (not enough data — e.g., fewer than 100 clicks)
  - Return: `{"result": str, "criteria_results": list, "recommendation": str}`
  - Recommendations:
    - Passed: "Test phase successful. Campaign is ready to scale to ${scale_budget}/day."
    - Failed: "Test phase did not meet success criteria. Recommend pausing and revising creative/targeting."
    - Inconclusive: "Insufficient data for evaluation. Recommend extending test phase by {days} days."

- `should_scale(self) -> bool` — return True if evaluation passed and auto_scale_on_success is True
- `should_pause(self) -> bool` — return True if evaluation failed and auto_pause_on_failure is True

**Class: GeoTargetingHelper**

Helpers for location targeting, especially for local service businesses.

Methods:
- `__init__(self)` — initialize
- `suggest_targeting_from_service_areas(self, service_areas: List[str], business_type: Optional[str] = None) -> List[GeoTargetingSuggestion]`:
  - For each service area, generate targeting suggestions:
    - If area is a city: suggest city targeting + 15-mile radius
    - If area is a zip code: suggest zip + adjacent zips
    - If area is a county/region: suggest the entire area
  - For mobile businesses (plumber, electrician, etc.): wider radius (25 miles)
  - For storefront businesses (restaurant, salon): tighter radius (5-10 miles)
  - Return sorted by priority: primary service areas first, then expansion areas

- `suggest_radius(self, business_type: str) -> float`:
  - Return recommended radius in miles based on business type:
    - "restaurant": 5.0
    - "salon" / "barbershop": 7.0
    - "dental" / "medical": 10.0
    - "legal": 15.0
    - "plumbing" / "hvac" / "electrician" / "roofing": 25.0
    - "landscaping": 20.0
    - "real_estate": 30.0
    - default: 15.0

- `expand_service_areas(self, current_areas: List[str], performance_data: Optional[Dict[str, Any]] = None) -> List[GeoTargetingSuggestion]`:
  - Suggest expansion areas based on current targeting
  - If performance data shows strong results in adjacent areas: suggest those
  - Prioritize expansion into areas adjacent to best-performing current areas
  - Return as "expansion" priority suggestions

**Helper functions (module-level):**

- `calculate_monthly_projection(daily_budget: float) -> float` — return `daily_budget * 30.4`
- `calculate_daily_from_monthly(monthly_budget: float) -> float` — return `monthly_budget / 30.4`
- `days_remaining_in_month(current_day: int) -> int` — return days left based on day of month (approximate: assume 30 days)
- `calculate_remaining_budget(monthly_cap: float, current_spend: float) -> float` — return `max(0, monthly_cap - current_spend)`
- `format_budget_summary(daily: float, monthly_projected: float, cap: Optional[float]) -> str` — return formatted string like "$50.00/day ($1,520/month projected, $2,000/month cap, 76% utilized)"

## Output Files

- `kai/paid_media/__init__.py`
- `kai/paid_media/controls.py`

## Acceptance Criteria

- [ ] `ReadinessStatus` enum has 4 values, `RiskLevel` enum has 4 values
- [ ] `ReadinessCheckItem` model has all 7 fields
- [ ] `ReadinessReport` model has all 9 fields including count rollups
- [ ] `BudgetCheckResult` model has all 11 fields
- [ ] `RiskAssessmentResult` model has all 6 fields
- [ ] `TestBudgetConfig` model has all 10 fields including test/scale phases
- [ ] `GeoTargetingSuggestion` model has all 7 fields
- [ ] `ReadinessChecker` has `check_campaign_readiness()` plus all 8 individual check methods
- [ ] `_check_conversion_tracking()` fails as critical when no tracking is configured
- [ ] `_check_compliance()` catches Meta Special Ad Category requirements
- [ ] `_check_audience_definition()` warns on both too-broad and too-narrow targeting
- [ ] `BudgetController` has all 4 methods with correct budget math
- [ ] `BudgetController.check_budget_change()` calculates utilization percentages correctly
- [ ] `BudgetController.recommend_budget_allocation()` reserves 10% buffer
- [ ] `RiskAssessor.assess_campaign_risk()` scores 6 risk factors and produces correct risk_level
- [ ] `BoundedTestBudget` manages test/evaluation/scaling phases
- [ ] `BoundedTestBudget.evaluate_test_results()` handles passed/failed/inconclusive outcomes
- [ ] `GeoTargetingHelper.suggest_radius()` returns appropriate radius for at least 8 business types
- [ ] All 5 module-level helper functions exist with correct math
- [ ] Pydantic import fallback pattern matches `gateway/models.py`

## Reference Materials

- `kai/models/paid_media.py` (created by Task 046) — Campaign, BudgetGuard, Targeting models
- `kai/connectors/ads/base.py` (created by Task 044) — AdConnectorConfig, SpendSafetyCheck
- `kai/actions/paid_media.py` (created by Task 045) — LaunchCampaign readiness check integration
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile.geography.service_areas for geo targeting
- `harness/references/meta-ads-rules.md` — Special Ad Category requirements
- `knowledge/playbooks/ad-campaign-management.md` — campaign management guidance
- `knowledge/playbooks/conversion-rate-optimization.md` — landing page quality factors
- `CLAUDE.md` — full project context
