"""Paid media budget controls, risk assessment, readiness checks, and campaign
management utilities.

This module is the safety-net layer between campaign actions and ad-platform
connectors.  It enforces spending limits, runs pre-launch readiness checks,
scores campaign risk, manages test-phase budgets, and provides geo-targeting
helpers for local businesses.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
import re
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


class ReadinessStatus(str, Enum):
    """Overall readiness status for a campaign launch."""

    ready = "ready"
    ready_with_warnings = "ready_with_warnings"
    not_ready = "not_ready"
    blocked = "blocked"


class RiskLevel(str, Enum):
    """Campaign risk classification."""

    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


# ============================================================================
# Models
# ============================================================================


class ReadinessCheckItem(BaseModel):
    """Result of a single readiness check."""

    check_name: str
    category: str  # "tracking", "landing_page", "budget", "creative", "compliance", "targeting", "technical"
    passed: bool
    severity: str  # "critical", "warning", "info"
    message: str
    remediation: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class ReadinessReport(BaseModel):
    """Aggregated readiness report for a campaign."""

    campaign_id: Optional[str] = None
    platform: str
    overall_status: str  # ReadinessStatus value
    checks: List[ReadinessCheckItem] = Field(default_factory=list)
    critical_failures: int = 0
    warnings: int = 0
    passed: int = 0
    summary: str
    checked_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BudgetCheckResult(BaseModel):
    """Result of a budget limit check."""

    is_within_limits: bool
    daily_budget_requested: float
    daily_budget_total_after: float
    monthly_projected_after: float
    daily_cap: Optional[float] = None
    monthly_cap: Optional[float] = None
    daily_utilization_pct: float = 0.0
    monthly_utilization_pct: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    blocks: List[str] = Field(default_factory=list)
    recommended_budget: Optional[float] = None


class RiskAssessmentResult(BaseModel):
    """Result of a campaign risk assessment."""

    risk_level: str  # RiskLevel value
    risk_score: float  # 0-100
    risk_factors: List[Dict[str, Any]] = Field(default_factory=list)
    mitigations: List[str] = Field(default_factory=list)
    approval_required: bool = False
    summary: str


class TestBudgetConfig(BaseModel):
    """Configuration for bounded test-phase budget management."""

    test_phase_days: int = 7
    test_daily_budget: float
    scale_daily_budget: float
    success_criteria: Dict[str, float] = Field(default_factory=dict)
    auto_scale_on_success: bool = False
    auto_pause_on_failure: bool = True
    current_phase: str = "test"  # "test", "evaluation", "scaling", "scaled"
    test_start_date: Optional[str] = None
    test_end_date: Optional[str] = None
    evaluation_result: Optional[str] = None  # "passed", "failed", "inconclusive"


class GeoTargetingSuggestion(BaseModel):
    """A geo-targeting suggestion for campaign location targeting."""

    location: str
    location_type: str  # "radius", "city", "zip", "county", "state"
    radius_miles: Optional[float] = None
    center_point: Optional[str] = None
    estimated_population: Optional[int] = None
    reason: str
    priority: str  # "primary", "secondary", "expansion"


# ============================================================================
# ReadinessChecker
# ============================================================================


class ReadinessChecker:
    """Runs comprehensive readiness checks before launching any campaign.

    Call :meth:`check_campaign_readiness` with the full campaign configuration
    dict and an optional business profile.  The method delegates to eight
    individual check methods, aggregates results, and returns a
    :class:`ReadinessReport`.
    """

    def __init__(self) -> None:
        pass

    # -- Public API ----------------------------------------------------------

    def check_campaign_readiness(
        self,
        campaign_config: Dict[str, Any],
        business_profile: Optional[Dict[str, Any]] = None,
    ) -> ReadinessReport:
        """Run all readiness checks and return a comprehensive report."""

        budget_guard = campaign_config.get("budget_guard")

        checks: List[ReadinessCheckItem] = [
            self._check_conversion_tracking(campaign_config),
            self._check_landing_page(campaign_config),
            self._check_landing_page_message_match(campaign_config),
            self._check_budget_within_limits(campaign_config, budget_guard),
            self._check_creative_assets(campaign_config),
            self._check_compliance(campaign_config, business_profile),
            self._check_audience_definition(campaign_config),
            self._check_platform_requirements(campaign_config),
        ]

        critical_failures = sum(
            1 for c in checks if not c.passed and c.severity == "critical"
        )
        warnings_count = sum(
            1 for c in checks if not c.passed and c.severity == "warning"
        )
        passed_count = sum(1 for c in checks if c.passed)

        # Determine overall status
        if critical_failures > 0:
            overall_status = ReadinessStatus.not_ready.value
        elif warnings_count > 0:
            overall_status = ReadinessStatus.ready_with_warnings.value
        else:
            overall_status = ReadinessStatus.ready.value

        # Check for hard blocks (compliance or budget blocks override status)
        has_blocks = any(
            not c.passed
            and c.severity == "critical"
            and c.category in ("compliance", "budget")
            for c in checks
        )
        if has_blocks:
            overall_status = ReadinessStatus.blocked.value

        total = len(checks)
        failed = total - passed_count
        summary_parts: List[str] = []
        if failed > 0:
            summary_parts.append(
                f"{failed} of {total} checks failed."
            )
        else:
            summary_parts.append(f"All {total} checks passed.")
        if critical_failures > 0:
            summary_parts.append(
                f"{critical_failures} critical issue(s) must be resolved before launch."
            )
        if warnings_count > 0:
            summary_parts.append(
                f"{warnings_count} warning(s) should be reviewed."
            )

        platform = campaign_config.get("platform", "unknown")

        return ReadinessReport(
            campaign_id=campaign_config.get("campaign_id") or campaign_config.get("id"),
            platform=platform,
            overall_status=overall_status,
            checks=checks,
            critical_failures=critical_failures,
            warnings=warnings_count,
            passed=passed_count,
            summary=" ".join(summary_parts),
            checked_at=datetime.now(timezone.utc).isoformat(),
        )

    # -- Individual Check Methods -------------------------------------------

    def _check_conversion_tracking(
        self, config: Dict[str, Any]
    ) -> ReadinessCheckItem:
        """Critical: verify conversion tracking is configured."""

        tracking_id = config.get("conversion_tracking_id") or config.get("pixel_id")

        if not tracking_id:
            return ReadinessCheckItem(
                check_name="conversion_tracking",
                category="tracking",
                passed=False,
                severity="critical",
                message=(
                    "No conversion tracking configured. Campaign will run "
                    "blind \u2014 unable to optimize for conversions or measure ROI."
                ),
                remediation="Set up Google conversion tag or Meta pixel before launching.",
                details={"tracking_id": None},
            )

        return ReadinessCheckItem(
            check_name="conversion_tracking",
            category="tracking",
            passed=True,
            severity="info",
            message="Conversion tracking is configured.",
            details={"tracking_id": tracking_id},
        )

    def _check_landing_page(self, config: Dict[str, Any]) -> ReadinessCheckItem:
        """Critical: verify landing page is specified and valid."""

        landing_urls: List[str] = config.get("landing_urls", [])

        if not landing_urls:
            return ReadinessCheckItem(
                check_name="landing_page",
                category="landing_page",
                passed=False,
                severity="critical",
                message="No landing page specified.",
                remediation="Create a dedicated landing page that matches your ad message.",
                details={"landing_urls": []},
            )

        issues: List[str] = []
        for url in landing_urls:
            if not url.startswith("https://"):
                issues.append(f"URL '{url}' does not use HTTPS.")

            # Check if URL is just the homepage (no meaningful path)
            cleaned = re.sub(r"^https?://[^/]+", "", url).strip("/")
            if not cleaned:
                issues.append(
                    f"URL '{url}' points to the homepage. A dedicated landing "
                    "page usually converts better."
                )

        if issues:
            return ReadinessCheckItem(
                check_name="landing_page",
                category="landing_page",
                passed=True,
                severity="warning",
                message=(
                    "Landing page(s) specified but with potential issues: "
                    + "; ".join(issues)
                ),
                remediation="Create a dedicated landing page that matches your ad message.",
                details={"landing_urls": landing_urls, "issues": issues},
            )

        return ReadinessCheckItem(
            check_name="landing_page",
            category="landing_page",
            passed=True,
            severity="info",
            message=f"Landing page configured: {', '.join(landing_urls)}.",
            details={"landing_urls": landing_urls},
        )

    def _check_landing_page_message_match(
        self, config: Dict[str, Any]
    ) -> ReadinessCheckItem:
        """Warning: heuristic check that ad message matches landing page."""

        headlines: List[str] = config.get("headlines", [])
        offer = config.get("offer", "")
        landing_urls: List[str] = config.get("landing_urls", [])

        # Build a set of signal words from the ad copy
        ad_text = " ".join(headlines).lower() + " " + str(offer).lower()
        signal_words = set()
        for word in re.split(r"\W+", ad_text):
            if len(word) > 3:
                signal_words.add(word)

        if not landing_urls or not signal_words:
            return ReadinessCheckItem(
                check_name="landing_page_message_match",
                category="landing_page",
                passed=True,
                severity="info",
                message="Unable to evaluate message match (insufficient data).",
                details={"signal_words": list(signal_words)},
            )

        # Check URL slugs for any signal word overlap
        url_text = " ".join(landing_urls).lower()
        matched = signal_words & set(re.split(r"\W+", url_text))

        if not matched and signal_words:
            return ReadinessCheckItem(
                check_name="landing_page_message_match",
                category="landing_page",
                passed=True,
                severity="warning",
                message=(
                    "Ad message may not match landing page. Ensure the landing "
                    "page prominently features the same offer/message as the ad."
                ),
                remediation=(
                    "Review landing page copy and ensure the headline and offer "
                    "match what the ad promises."
                ),
                details={
                    "ad_signal_words": sorted(signal_words),
                    "matched_in_url": [],
                },
            )

        return ReadinessCheckItem(
            check_name="landing_page_message_match",
            category="landing_page",
            passed=True,
            severity="info",
            message="Ad message appears consistent with landing page URL.",
            details={
                "ad_signal_words": sorted(signal_words),
                "matched_in_url": sorted(matched),
            },
        )

    def _check_budget_within_limits(
        self,
        config: Dict[str, Any],
        budget_guard: Optional[Dict[str, Any]] = None,
    ) -> ReadinessCheckItem:
        """Critical: validate campaign budget against spending caps."""

        daily_budget = config.get("budget_daily", 0.0) or 0.0

        if budget_guard is None:
            return ReadinessCheckItem(
                check_name="budget_within_limits",
                category="budget",
                passed=True,
                severity="warning",
                message="No budget guard configured. Set spending limits to prevent overspend.",
                remediation=(
                    "Create a BudgetGuard with daily and monthly caps for this business."
                ),
                details={"daily_budget": daily_budget},
            )

        daily_cap = budget_guard.get("max_daily_spend", 0.0)
        monthly_cap = budget_guard.get("max_monthly_spend", 0.0)
        current_daily = budget_guard.get("current_daily_spend", 0.0)
        current_monthly = budget_guard.get("current_monthly_spend", 0.0)

        total_daily_after = current_daily + daily_budget
        projected_monthly = total_daily_after * 30.4

        # Check daily cap
        if daily_cap > 0 and total_daily_after > daily_cap:
            return ReadinessCheckItem(
                check_name="budget_within_limits",
                category="budget",
                passed=False,
                severity="critical",
                message=(
                    f"Campaign budget (${daily_budget:.2f}/day) exceeds daily "
                    f"spend cap (${daily_cap:.2f}/day)."
                ),
                remediation=(
                    f"Reduce daily budget to ${max(0, daily_cap - current_daily):.2f}/day "
                    "or increase your daily spend cap."
                ),
                details={
                    "daily_budget": daily_budget,
                    "total_daily_after": total_daily_after,
                    "daily_cap": daily_cap,
                },
            )

        # Check monthly cap
        if monthly_cap > 0 and projected_monthly > monthly_cap:
            return ReadinessCheckItem(
                check_name="budget_within_limits",
                category="budget",
                passed=False,
                severity="critical",
                message=(
                    f"Projected monthly spend (${projected_monthly:.2f}/mo) exceeds "
                    f"monthly cap (${monthly_cap:.2f}/mo)."
                ),
                remediation="Reduce daily budget or increase your monthly spend cap.",
                details={
                    "daily_budget": daily_budget,
                    "projected_monthly": projected_monthly,
                    "monthly_cap": monthly_cap,
                },
            )

        # Warn at 80%+ utilization of remaining budget
        if monthly_cap > 0:
            remaining = monthly_cap - current_monthly
            if remaining > 0:
                pct_of_remaining = (daily_budget * 30.4) / remaining * 100
                if pct_of_remaining > 80:
                    return ReadinessCheckItem(
                        check_name="budget_within_limits",
                        category="budget",
                        passed=True,
                        severity="warning",
                        message=(
                            f"Campaign will consume {pct_of_remaining:.0f}% of "
                            "remaining monthly budget."
                        ),
                        details={
                            "daily_budget": daily_budget,
                            "remaining_monthly": remaining,
                            "pct_of_remaining": pct_of_remaining,
                        },
                    )

        return ReadinessCheckItem(
            check_name="budget_within_limits",
            category="budget",
            passed=True,
            severity="info",
            message="Budget is within configured limits.",
            details={
                "daily_budget": daily_budget,
                "total_daily_after": total_daily_after,
                "projected_monthly": projected_monthly,
                "daily_cap": daily_cap,
                "monthly_cap": monthly_cap,
            },
        )

    def _check_creative_assets(self, config: Dict[str, Any]) -> ReadinessCheckItem:
        """Critical: verify creative assets meet minimum platform requirements."""

        platform = config.get("platform", "").lower()
        headlines: List[str] = config.get("headlines", [])
        descriptions: List[str] = config.get("descriptions", [])
        primary_text = config.get("primary_text", "")
        media_refs: List[str] = config.get("media_refs", [])
        missing: List[str] = []

        if platform in ("google", "google_ads", "google ads"):
            # Google Search: 3+ headlines, 2+ descriptions
            if len(headlines) < 3:
                missing.append(
                    f"Google Search requires 3+ headlines (found {len(headlines)})"
                )
            if len(descriptions) < 2:
                missing.append(
                    f"Google Search requires 2+ descriptions (found {len(descriptions)})"
                )
        elif platform in ("meta", "facebook", "instagram", "meta_ads"):
            # Meta: primary text, headline, media asset
            if not primary_text:
                missing.append("Meta requires primary text")
            if not headlines:
                missing.append("Meta requires at least 1 headline")
            if not media_refs:
                missing.append("Meta requires at least 1 media asset (image or video)")
        else:
            # General: at least 1 headline and 1 description
            if not headlines:
                missing.append("At least 1 headline is required")
            if not descriptions and not primary_text:
                missing.append("At least 1 description or primary text is required")

        if missing:
            return ReadinessCheckItem(
                check_name="creative_assets",
                category="creative",
                passed=False,
                severity="critical",
                message=f"Insufficient creative assets. Missing: {'; '.join(missing)}.",
                remediation=f"Add the missing creative elements: {'; '.join(missing)}.",
                details={"missing": missing, "platform": platform},
            )

        return ReadinessCheckItem(
            check_name="creative_assets",
            category="creative",
            passed=True,
            severity="info",
            message="Creative assets meet minimum platform requirements.",
            details={
                "headlines_count": len(headlines),
                "descriptions_count": len(descriptions),
                "media_count": len(media_refs),
                "platform": platform,
            },
        )

    def _check_compliance(
        self,
        config: Dict[str, Any],
        business_profile: Optional[Dict[str, Any]] = None,
    ) -> ReadinessCheckItem:
        """Critical: compliance checks for regulated industries."""

        platform = config.get("platform", "").lower()
        industry = ""
        if business_profile:
            industry = (
                business_profile.get("industry", "")
                or business_profile.get("vertical", "")
                or ""
            ).lower()

        regulated_industries = {
            "healthcare",
            "health",
            "medical",
            "finance",
            "financial",
            "banking",
            "insurance",
            "legal",
            "law",
            "gambling",
            "casino",
            "alcohol",
            "cannabis",
            "marijuana",
            "pharmaceutical",
            "pharma",
        }

        # Meta Special Ad Categories
        meta_special_categories = {"housing", "employment", "credit"}
        special_ad_category = config.get("special_ad_category")

        if platform in ("meta", "facebook", "instagram", "meta_ads"):
            ad_category = (config.get("ad_category", "") or "").lower()
            if ad_category in meta_special_categories and not special_ad_category:
                return ReadinessCheckItem(
                    check_name="compliance",
                    category="compliance",
                    passed=False,
                    severity="critical",
                    message=(
                        f"Meta requires Special Ad Category declaration for "
                        f"{ad_category} advertising."
                    ),
                    remediation=(
                        f"Set special_ad_category to '{ad_category}' in the campaign "
                        "configuration before launching."
                    ),
                    details={
                        "platform": platform,
                        "ad_category": ad_category,
                        "special_ad_category_set": False,
                    },
                )

        if industry and any(ind in industry for ind in regulated_industries):
            missing_items: List[str] = []
            disclaimers = config.get("disclaimers", [])
            certifications = config.get("certifications", [])
            age_gate = config.get("age_gate", False)

            if not disclaimers:
                missing_items.append("required disclaimers")
            if not certifications:
                missing_items.append("industry certifications")
            if industry in ("alcohol", "cannabis", "marijuana", "gambling", "casino"):
                if not age_gate:
                    missing_items.append("age gate verification")

            if missing_items:
                return ReadinessCheckItem(
                    check_name="compliance",
                    category="compliance",
                    passed=False,
                    severity="critical",
                    message=(
                        f"Regulated industry ({industry}) requires additional "
                        f"compliance. Missing: {', '.join(missing_items)}."
                    ),
                    remediation=(
                        f"Add {', '.join(missing_items)} to the campaign configuration "
                        f"for {industry} advertising compliance."
                    ),
                    details={
                        "industry": industry,
                        "missing": missing_items,
                        "regulated": True,
                    },
                )

        return ReadinessCheckItem(
            check_name="compliance",
            category="compliance",
            passed=True,
            severity="info",
            message=(
                "General compliance check passed. Ensure ad copy follows "
                "FTC disclosure rules and platform policies."
            ),
            details={"industry": industry or "unregulated", "regulated": bool(industry)},
        )

    def _check_audience_definition(
        self, config: Dict[str, Any]
    ) -> ReadinessCheckItem:
        """Warning: evaluate targeting breadth."""

        locations: List[str] = config.get("locations", [])
        interests: List[str] = config.get("interests", [])
        audiences = config.get("custom_audiences", []) or config.get("audiences", [])
        keywords: List[str] = config.get("keywords", [])
        age_min = config.get("age_min")
        age_max = config.get("age_max")
        is_local = config.get("is_local_business", False)

        has_location = bool(locations)
        has_interest = bool(interests)
        has_audience = bool(audiences)
        has_keywords = bool(keywords)

        targeting_signals = sum([has_location, has_interest, has_audience, has_keywords])

        # Local business must have location targeting
        if is_local and not has_location:
            return ReadinessCheckItem(
                check_name="audience_definition",
                category="targeting",
                passed=False,
                severity="critical",
                message="Local business campaigns must have location targeting.",
                remediation=(
                    "Add location targeting (city, zip code, or radius) for your "
                    "service area."
                ),
                details={
                    "is_local": True,
                    "has_location": False,
                    "targeting_signals": targeting_signals,
                },
            )

        # Very broad targeting
        if targeting_signals == 0:
            return ReadinessCheckItem(
                check_name="audience_definition",
                category="targeting",
                passed=True,
                severity="warning",
                message=(
                    "Targeting is very broad. Consider adding location and "
                    "interest targeting to improve relevance."
                ),
                remediation=(
                    "Define at least one targeting signal: location, interests, "
                    "keywords, or custom audience."
                ),
                details={"targeting_signals": 0},
            )

        # Extremely narrow targeting heuristic
        narrow_signals = 0
        if has_location and len(locations) == 1:
            # Check if location looks like a zip code
            loc = locations[0].strip()
            if re.match(r"^\d{5}$", loc):
                narrow_signals += 1
        if age_min and age_max and (age_max - age_min) <= 5:
            narrow_signals += 1
        if has_interest and len(interests) == 1:
            narrow_signals += 1

        if narrow_signals >= 2:
            return ReadinessCheckItem(
                check_name="audience_definition",
                category="targeting",
                passed=True,
                severity="warning",
                message=(
                    "Targeting may be too narrow. Estimated reach could be "
                    "very limited."
                ),
                remediation=(
                    "Broaden targeting by adding more locations, expanding age "
                    "range, or adding additional interests."
                ),
                details={
                    "narrow_signals": narrow_signals,
                    "targeting_signals": targeting_signals,
                },
            )

        return ReadinessCheckItem(
            check_name="audience_definition",
            category="targeting",
            passed=True,
            severity="info",
            message="Audience targeting is defined.",
            details={"targeting_signals": targeting_signals},
        )

    def _check_platform_requirements(
        self, config: Dict[str, Any]
    ) -> ReadinessCheckItem:
        """Warning: platform-specific requirement checks."""

        platform = config.get("platform", "").lower()
        issues: List[str] = []

        if platform in ("google", "google_ads", "google ads"):
            campaign_type = config.get("campaign_type", "").lower()
            keywords = config.get("keywords", [])
            if campaign_type in ("search", "") and not keywords:
                issues.append(
                    "Google Search campaigns require a keyword list. "
                    "No keywords found in configuration."
                )

        if platform in ("meta", "facebook", "instagram", "meta_ads"):
            objective = config.get("objective", "").lower()
            pixel_events = config.get("pixel_events", [])
            if objective in ("conversions", "sales", "leads") and not pixel_events:
                issues.append(
                    "Meta conversion-objective campaigns should have pixel "
                    "events configured for optimization."
                )

        # General: bid strategy vs objective alignment
        bid_strategy = config.get("bid_strategy", "")
        objective = config.get("objective", "")
        if bid_strategy and objective:
            conversion_strategies = {
                "maximize_conversions",
                "target_cpa",
                "target_roas",
                "maximize_conversion_value",
            }
            traffic_strategies = {"maximize_clicks", "manual_cpc"}
            if (
                objective in ("conversions", "sales", "leads")
                and bid_strategy in traffic_strategies
            ):
                issues.append(
                    f"Bid strategy '{bid_strategy}' may not align with "
                    f"'{objective}' objective. Consider a conversion-focused "
                    "bid strategy."
                )
            if (
                objective in ("traffic", "awareness")
                and bid_strategy in conversion_strategies
            ):
                issues.append(
                    f"Bid strategy '{bid_strategy}' is conversion-focused but "
                    f"objective is '{objective}'. Consider a traffic or "
                    "awareness-focused bid strategy."
                )

        if issues:
            return ReadinessCheckItem(
                check_name="platform_requirements",
                category="technical",
                passed=True,
                severity="warning",
                message=" | ".join(issues),
                remediation="Review platform-specific setup requirements.",
                details={"platform": platform, "issues": issues},
            )

        return ReadinessCheckItem(
            check_name="platform_requirements",
            category="technical",
            passed=True,
            severity="info",
            message="Platform-specific requirements appear satisfied.",
            details={"platform": platform},
        )


# ============================================================================
# BudgetController
# ============================================================================


class BudgetController:
    """Enforces spending limits and budget safety.

    Initialised with a budget guard configuration dict (matching the
    :class:`~kai.models.paid_media.BudgetGuard` shape).
    """

    def __init__(self, budget_guard: Dict[str, Any]) -> None:
        self._guard = budget_guard

    # -- helpers -------------------------------------------------------------

    @property
    def daily_cap(self) -> float:
        return float(self._guard.get("max_daily_spend", 0.0))

    @property
    def monthly_cap(self) -> float:
        return float(self._guard.get("max_monthly_spend", 0.0))

    @property
    def alert_threshold_pct(self) -> float:
        return float(self._guard.get("alert_threshold_pct", 80.0))

    @property
    def auto_pause_threshold_pct(self) -> float:
        return float(self._guard.get("auto_pause_threshold_pct", 100.0))

    def _build_result(
        self,
        daily_requested: float,
        total_daily_after: float,
        is_new: bool = False,
        current_campaigns: Optional[List[Dict[str, Any]]] = None,
    ) -> BudgetCheckResult:
        """Core budget-check logic shared by change and launch methods."""

        monthly_projected = total_daily_after * 30.4

        daily_util = (
            (total_daily_after / self.daily_cap * 100) if self.daily_cap > 0 else 0.0
        )
        monthly_util = (
            (monthly_projected / self.monthly_cap * 100) if self.monthly_cap > 0 else 0.0
        )

        warnings: List[str] = []
        blocks: List[str] = []
        recommended: Optional[float] = None

        # Daily cap check
        if self.daily_cap > 0:
            if total_daily_after > self.daily_cap:
                blocks.append(
                    f"Total daily spend (${total_daily_after:.2f}) exceeds "
                    f"daily cap (${self.daily_cap:.2f})."
                )
                recommended = max(0.0, self.daily_cap - (total_daily_after - daily_requested))
            elif daily_util >= 90:
                warnings.append(
                    f"Daily spend at {daily_util:.0f}% of cap "
                    f"(${total_daily_after:.2f}/${self.daily_cap:.2f})."
                )
            elif daily_util >= 80:
                warnings.append(
                    f"Daily spend at {daily_util:.0f}% of cap "
                    f"(${total_daily_after:.2f}/${self.daily_cap:.2f})."
                )
            elif daily_util >= 70:
                warnings.append(
                    f"Daily spend at {daily_util:.0f}% of cap "
                    f"(${total_daily_after:.2f}/${self.daily_cap:.2f})."
                )

        # Monthly cap check
        if self.monthly_cap > 0:
            if monthly_projected > self.monthly_cap:
                blocks.append(
                    f"Projected monthly spend (${monthly_projected:.2f}) exceeds "
                    f"monthly cap (${self.monthly_cap:.2f})."
                )
                if recommended is None:
                    recommended = max(
                        0.0,
                        calculate_daily_from_monthly(self.monthly_cap)
                        - (total_daily_after - daily_requested),
                    )
            elif monthly_util >= 90:
                warnings.append(
                    f"Monthly projection at {monthly_util:.0f}% of cap "
                    f"(${monthly_projected:.2f}/${self.monthly_cap:.2f})."
                )
            elif monthly_util >= 80:
                warnings.append(
                    f"Monthly projection at {monthly_util:.0f}% of cap "
                    f"(${monthly_projected:.2f}/${self.monthly_cap:.2f})."
                )
            elif monthly_util >= 70:
                warnings.append(
                    f"Monthly projection at {monthly_util:.0f}% of cap "
                    f"(${monthly_projected:.2f}/${self.monthly_cap:.2f})."
                )

        # Extra warning for new campaign being the most expensive
        if is_new and current_campaigns:
            max_existing = max(
                (float(c.get("budget_daily", 0) or 0) for c in current_campaigns),
                default=0.0,
            )
            if daily_requested > max_existing > 0:
                warnings.append(
                    f"This would be the most expensive campaign "
                    f"(${daily_requested:.2f}/day vs current max ${max_existing:.2f}/day)."
                )

        is_within = len(blocks) == 0

        return BudgetCheckResult(
            is_within_limits=is_within,
            daily_budget_requested=daily_requested,
            daily_budget_total_after=total_daily_after,
            monthly_projected_after=monthly_projected,
            daily_cap=self.daily_cap if self.daily_cap > 0 else None,
            monthly_cap=self.monthly_cap if self.monthly_cap > 0 else None,
            daily_utilization_pct=round(daily_util, 2),
            monthly_utilization_pct=round(monthly_util, 2),
            warnings=warnings,
            blocks=blocks,
            recommended_budget=round(recommended, 2) if recommended is not None else None,
        )

    # -- Public API ----------------------------------------------------------

    def check_budget_change(
        self,
        campaign_id: str,
        new_daily_budget: float,
        current_campaigns: List[Dict[str, Any]],
    ) -> BudgetCheckResult:
        """Check if a budget change for an existing campaign is within limits.

        Sums daily budgets of all campaigns *excluding* ``campaign_id``, adds
        ``new_daily_budget``, then validates against caps.
        """

        other_total = sum(
            float(c.get("budget_daily", 0) or 0)
            for c in current_campaigns
            if (c.get("id") or c.get("campaign_id")) != campaign_id
        )
        total_after = other_total + new_daily_budget
        return self._build_result(new_daily_budget, total_after, is_new=False)

    def check_launch_budget(
        self,
        new_campaign_budget: float,
        current_campaigns: List[Dict[str, Any]],
    ) -> BudgetCheckResult:
        """Check if a new campaign budget fits within limits.

        Same as :meth:`check_budget_change` but treats the campaign as brand-new
        (no existing campaign to subtract).
        """

        existing_total = sum(
            float(c.get("budget_daily", 0) or 0) for c in current_campaigns
        )
        total_after = existing_total + new_campaign_budget
        return self._build_result(
            new_campaign_budget,
            total_after,
            is_new=True,
            current_campaigns=current_campaigns,
        )

    def monitor_spend(
        self,
        current_daily_spend: float,
        current_monthly_spend: float,
        day_of_month: int,
    ) -> Dict[str, Any]:
        """Evaluate current spend pace and project end-of-month totals.

        Returns a dict with pace assessment, projections, and alert signals.
        """

        days_left = days_remaining_in_month(day_of_month)
        days_elapsed = max(day_of_month, 1)

        # Project monthly spend from current daily pace
        avg_daily = current_monthly_spend / days_elapsed
        projected_monthly = current_monthly_spend + (avg_daily * days_left)

        utilization = (
            (projected_monthly / self.monthly_cap * 100)
            if self.monthly_cap > 0
            else 0.0
        )

        # Determine pace
        expected_spend = (
            (self.monthly_cap * (days_elapsed / 30.0)) if self.monthly_cap > 0 else 0.0
        )
        if expected_spend > 0:
            pace_ratio = current_monthly_spend / expected_spend
            if pace_ratio > 1.15:
                pace = "overspending"
            elif pace_ratio < 0.85:
                pace = "underspending"
            else:
                pace = "on_track"
        else:
            pace = "on_track"

        alert = utilization >= self.alert_threshold_pct
        auto_pause = utilization >= self.auto_pause_threshold_pct

        # Build message
        if auto_pause:
            message = (
                f"CRITICAL: Projected monthly spend ${projected_monthly:.2f} "
                f"exceeds auto-pause threshold ({self.auto_pause_threshold_pct:.0f}% "
                f"of ${self.monthly_cap:.2f}). Campaigns should be paused."
            )
        elif alert:
            message = (
                f"WARNING: Projected monthly spend ${projected_monthly:.2f} "
                f"exceeds alert threshold ({self.alert_threshold_pct:.0f}% "
                f"of ${self.monthly_cap:.2f}). Review campaign budgets."
            )
        elif pace == "overspending":
            message = (
                f"Spend pace is ahead of target. Current: ${current_monthly_spend:.2f}, "
                f"projected: ${projected_monthly:.2f}."
            )
        elif pace == "underspending":
            message = (
                f"Spend pace is below target. Current: ${current_monthly_spend:.2f}, "
                f"projected: ${projected_monthly:.2f}. Consider increasing budgets "
                "or reviewing ad delivery."
            )
        else:
            message = (
                f"Spend pace is on track. Current: ${current_monthly_spend:.2f}, "
                f"projected: ${projected_monthly:.2f}."
            )

        return {
            "pace": pace,
            "daily_spend": current_daily_spend,
            "monthly_spend": current_monthly_spend,
            "projected_monthly": round(projected_monthly, 2),
            "utilization_pct": round(utilization, 2),
            "alert": alert,
            "auto_pause": auto_pause,
            "message": message,
        }

    def recommend_budget_allocation(
        self,
        monthly_budget: float,
        campaign_count: int,
        campaign_priorities: Optional[Dict[str, int]] = None,
    ) -> Dict[str, float]:
        """Suggest daily budget allocation across campaigns.

        Reserves 10% of the monthly budget as an overage buffer.  If
        ``campaign_priorities`` is provided (campaign_id -> priority 1-5,
        where 5 is highest), budget is allocated proportionally.
        """

        if campaign_count <= 0:
            return {}

        # Reserve 10% buffer
        usable_monthly = monthly_budget * 0.90
        usable_daily = calculate_daily_from_monthly(usable_monthly)

        if campaign_priorities:
            # Allocate proportionally by priority weight
            total_weight = sum(campaign_priorities.values())
            if total_weight == 0:
                total_weight = len(campaign_priorities)
                campaign_priorities = {
                    k: 1 for k in campaign_priorities
                }

            allocation: Dict[str, float] = {}
            for cid, priority in campaign_priorities.items():
                share = priority / total_weight
                allocation[cid] = round(usable_daily * share, 2)
            return allocation

        # Even allocation
        per_campaign = round(usable_daily / campaign_count, 2)
        return {
            f"campaign_{i + 1}": per_campaign for i in range(campaign_count)
        }


# ============================================================================
# RiskAssessor
# ============================================================================


class RiskAssessor:
    """Scores campaign risk across six weighted factors.

    Total risk score ranges from 0 (safe) to 100 (maximum risk).
    """

    def __init__(self) -> None:
        self._weights = {
            "spend_level": 20,
            "audience_breadth": 20,
            "creative_compliance": 20,
            "landing_page_quality": 15,
            "industry_regulations": 15,
            "platform_track_record": 10,
        }

    def assess_campaign_risk(
        self,
        campaign_config: Dict[str, Any],
        business_profile: Optional[Dict[str, Any]] = None,
    ) -> RiskAssessmentResult:
        """Score campaign risk and return a :class:`RiskAssessmentResult`."""

        factors: List[Dict[str, Any]] = []
        mitigations: List[str] = []

        # 1. Spend level (weight: 20)
        daily_budget = float(campaign_config.get("budget_daily", 0) or 0)
        if daily_budget < 10:
            spend_score = 0
        elif daily_budget <= 50:
            spend_score = 5
        elif daily_budget <= 100:
            spend_score = 10
        elif daily_budget <= 500:
            spend_score = 15
        else:
            spend_score = 20
        factors.append({
            "factor": "spend_level",
            "impact": "financial",
            "score": spend_score,
            "explanation": (
                f"Daily budget ${daily_budget:.2f}. "
                f"{'High spend increases financial exposure.' if spend_score >= 15 else 'Moderate spend level.' if spend_score >= 10 else 'Conservative spend level.'}"
            ),
        })
        if spend_score >= 15:
            mitigations.append(
                "Start with a lower test budget and scale up after validating performance."
            )

        # 2. Audience breadth (weight: 20)
        locations = campaign_config.get("locations", [])
        interests = campaign_config.get("interests", [])
        audiences = campaign_config.get("custom_audiences", [])
        keywords = campaign_config.get("keywords", [])
        targeting_signals = sum([
            bool(locations),
            bool(interests),
            bool(audiences),
            bool(keywords),
        ])
        if targeting_signals == 0:
            audience_score = 20
        elif targeting_signals == 1:
            audience_score = 15
        elif targeting_signals == 2:
            audience_score = 10
        else:
            audience_score = 0
        if audience_score == 20:
            audience_detail = "No targeting defined \u2014 ads will reach a very broad audience."
        elif audience_score >= 10:
            audience_detail = "Consider tightening targeting."
        else:
            audience_detail = "Well-defined audience targeting."
        factors.append({
            "factor": "audience_breadth",
            "impact": "efficiency",
            "score": audience_score,
            "explanation": (
                f"{targeting_signals} targeting signal(s) configured. "
                f"{audience_detail}"
            ),
        })
        if audience_score >= 15:
            mitigations.append(
                "Add location, interest, or keyword targeting to narrow the audience."
            )

        # 3. Creative compliance (weight: 20)
        compliance_status = (
            campaign_config.get("compliance_status", "unchecked") or "unchecked"
        ).lower()
        if compliance_status == "passed":
            compliance_score = 0
        elif compliance_status in ("unchecked", "pending"):
            compliance_score = 10
        else:
            compliance_score = 20
        factors.append({
            "factor": "creative_compliance",
            "impact": "legal",
            "score": compliance_score,
            "explanation": (
                f"Compliance status: {compliance_status}. "
                f"{'Known compliance issues exist.' if compliance_score == 20 else 'Compliance not yet verified.' if compliance_score == 10 else 'Compliance checks passed.'}"
            ),
        })
        if compliance_score >= 10:
            mitigations.append(
                "Run ad creative through compliance review before launching."
            )

        # 4. Landing page quality (weight: 15)
        landing_urls = campaign_config.get("landing_urls", [])
        if not landing_urls:
            lp_score = 15
        else:
            # Check if any URL is a homepage
            is_homepage = False
            for url in landing_urls:
                cleaned = re.sub(r"^https?://[^/]+", "", url).strip("/")
                if not cleaned:
                    is_homepage = True
                    break
            lp_score = 10 if is_homepage else 0
        if lp_score == 15:
            lp_detail = "No landing page configured."
        elif lp_score == 10:
            lp_detail = "Landing page is the homepage \u2014 a dedicated page converts better."
        else:
            lp_detail = "Dedicated landing page configured."
        factors.append({
            "factor": "landing_page_quality",
            "impact": "conversion",
            "score": lp_score,
            "explanation": lp_detail,
        })
        if lp_score >= 10:
            mitigations.append(
                "Create a dedicated landing page with a clear CTA that matches the ad message."
            )

        # 5. Industry regulations (weight: 15)
        industry = ""
        if business_profile:
            industry = (
                business_profile.get("industry", "")
                or business_profile.get("vertical", "")
                or ""
            ).lower()

        heavily_regulated = {
            "healthcare", "health", "medical", "finance", "financial",
            "banking", "insurance", "pharmaceutical", "pharma", "gambling",
            "casino",
        }
        lightly_regulated = {
            "legal", "law", "alcohol", "cannabis", "marijuana",
            "real_estate", "education",
        }

        if any(ind in industry for ind in heavily_regulated):
            regulation_score = 15
        elif any(ind in industry for ind in lightly_regulated):
            regulation_score = 5
        else:
            regulation_score = 0
        if regulation_score == 15:
            reg_detail = "Heavily regulated \u2014 requires disclaimers, certifications, and careful ad copy."
        elif regulation_score == 5:
            reg_detail = "Some regulatory requirements apply."
        else:
            reg_detail = "No special regulatory requirements."
        factors.append({
            "factor": "industry_regulations",
            "impact": "compliance",
            "score": regulation_score,
            "explanation": (
                f"Industry: {industry or 'unspecified'}. {reg_detail}"
            ),
        })
        if regulation_score >= 5:
            mitigations.append(
                "Review platform advertising policies for your industry and add required disclaimers."
            )

        # 6. Platform track record (weight: 10)
        previous_campaigns = campaign_config.get("previous_campaigns_on_platform", 0)
        has_disapprovals = campaign_config.get("has_previous_disapprovals", False)
        if has_disapprovals:
            track_score = 10
        elif previous_campaigns == 0:
            track_score = 5
        else:
            track_score = 0
        factors.append({
            "factor": "platform_track_record",
            "impact": "operational",
            "score": track_score,
            "explanation": (
                f"{'Previous ad disapprovals on this platform.' if track_score == 10 else 'No campaign history on this platform.' if track_score == 5 else 'Established track record on this platform.'}"
            ),
        })
        if track_score >= 5:
            mitigations.append(
                "Review previous disapproval reasons and ensure new creative addresses those issues."
                if has_disapprovals
                else "Start with a conservative budget until you establish a platform track record."
            )

        # Calculate total
        total_score = sum(f["score"] for f in factors)

        if total_score <= 25:
            risk_level = RiskLevel.low.value
        elif total_score <= 50:
            risk_level = RiskLevel.medium.value
        elif total_score <= 75:
            risk_level = RiskLevel.high.value
        else:
            risk_level = RiskLevel.critical.value

        approval_required = risk_level in (RiskLevel.high.value, RiskLevel.critical.value)

        summary = (
            f"Risk score: {total_score}/100 ({risk_level}). "
            f"{len(mitigations)} mitigation(s) recommended."
        )
        if approval_required:
            summary += " Human approval required before launch."

        return RiskAssessmentResult(
            risk_level=risk_level,
            risk_score=float(total_score),
            risk_factors=factors,
            mitigations=mitigations,
            approval_required=approval_required,
            summary=summary,
        )


# ============================================================================
# BoundedTestBudget
# ============================================================================


class BoundedTestBudget:
    """Manages test-phase budgets for new campaigns.

    Wraps a :class:`TestBudgetConfig` and provides methods to query the
    current budget, evaluate test-phase results, and determine whether to
    scale or pause.
    """

    def __init__(self, config: TestBudgetConfig) -> None:
        self.config = config

    def get_current_budget(self) -> float:
        """Return the daily budget for the current phase."""

        phase = self.config.current_phase
        if phase in ("scaling", "scaled"):
            return self.config.scale_daily_budget
        # "test" and "evaluation" both use test budget
        return self.config.test_daily_budget

    def evaluate_test_results(
        self, performance: Dict[str, float]
    ) -> Dict[str, Any]:
        """Compare performance against success criteria.

        Returns a dict with ``result`` ("passed", "failed", "inconclusive"),
        ``criteria_results`` (per-criterion detail), and ``recommendation``.
        """

        criteria_results: List[Dict[str, Any]] = []
        all_passed = True
        has_insufficient_data = False

        # Check for minimum data threshold
        clicks = performance.get("clicks", 0)
        impressions = performance.get("impressions", 0)
        if clicks < 100 and impressions < 1000:
            has_insufficient_data = True

        for metric, target in self.config.success_criteria.items():
            actual = performance.get(metric, 0.0)

            # Metrics where lower is better
            lower_is_better = metric in (
                "cpa_max", "cpc_max", "cost_max", "bounce_rate_max",
            )

            if lower_is_better:
                passed = actual <= target
            else:
                passed = actual >= target

            if not passed:
                all_passed = False

            criteria_results.append({
                "metric": metric,
                "target": target,
                "actual": actual,
                "passed": passed,
            })

        # Determine overall result
        if has_insufficient_data:
            result = "inconclusive"
            remaining_days = self.config.test_phase_days
            recommendation = (
                f"Insufficient data for evaluation. Recommend extending test "
                f"phase by {remaining_days} days."
            )
        elif all_passed:
            result = "passed"
            recommendation = (
                f"Test phase successful. Campaign is ready to scale to "
                f"${self.config.scale_daily_budget:.2f}/day."
            )
        else:
            result = "failed"
            failed_metrics = [
                cr["metric"] for cr in criteria_results if not cr["passed"]
            ]
            recommendation = (
                "Test phase did not meet success criteria. Recommend pausing "
                f"and revising creative/targeting. Failed metrics: "
                f"{', '.join(failed_metrics)}."
            )

        # Store evaluation result on the config
        self.config.evaluation_result = result

        return {
            "result": result,
            "criteria_results": criteria_results,
            "recommendation": recommendation,
        }

    def should_scale(self) -> bool:
        """Return True if test passed and auto-scaling is enabled."""
        return (
            self.config.evaluation_result == "passed"
            and self.config.auto_scale_on_success
        )

    def should_pause(self) -> bool:
        """Return True if test failed and auto-pause is enabled."""
        return (
            self.config.evaluation_result == "failed"
            and self.config.auto_pause_on_failure
        )


# ============================================================================
# GeoTargetingHelper
# ============================================================================


class GeoTargetingHelper:
    """Helpers for location targeting, especially for local service businesses.

    Provides radius suggestions by business type, service-area expansion
    recommendations, and targeting structure for geo campaigns.
    """

    # Radius recommendations by business type (miles)
    _RADIUS_MAP: Dict[str, float] = {
        "restaurant": 5.0,
        "cafe": 5.0,
        "salon": 7.0,
        "barbershop": 7.0,
        "spa": 7.0,
        "dental": 10.0,
        "dentist": 10.0,
        "medical": 10.0,
        "doctor": 10.0,
        "chiropractor": 10.0,
        "veterinary": 10.0,
        "vet": 10.0,
        "legal": 15.0,
        "lawyer": 15.0,
        "attorney": 15.0,
        "accounting": 15.0,
        "plumbing": 25.0,
        "plumber": 25.0,
        "hvac": 25.0,
        "electrician": 25.0,
        "electrical": 25.0,
        "roofing": 25.0,
        "roofer": 25.0,
        "landscaping": 20.0,
        "lawn_care": 20.0,
        "tree_service": 20.0,
        "pest_control": 20.0,
        "cleaning": 15.0,
        "real_estate": 30.0,
        "realtor": 30.0,
        "moving": 30.0,
        "auto_repair": 10.0,
        "mechanic": 10.0,
    }

    # Business types considered "mobile" (go to the customer)
    _MOBILE_TYPES = {
        "plumbing", "plumber", "hvac", "electrician", "electrical",
        "roofing", "roofer", "landscaping", "lawn_care", "tree_service",
        "pest_control", "cleaning", "moving",
    }

    # Business types considered "storefront" (customer comes to you)
    _STOREFRONT_TYPES = {
        "restaurant", "cafe", "salon", "barbershop", "spa",
        "dental", "dentist", "medical", "doctor", "chiropractor",
        "veterinary", "vet", "auto_repair", "mechanic",
    }

    def __init__(self) -> None:
        pass

    def suggest_radius(self, business_type: str) -> float:
        """Return recommended targeting radius in miles for a business type."""

        normalized = business_type.lower().strip().replace(" ", "_").replace("-", "_")
        return self._RADIUS_MAP.get(normalized, 15.0)

    def suggest_targeting_from_service_areas(
        self,
        service_areas: List[str],
        business_type: Optional[str] = None,
    ) -> List[GeoTargetingSuggestion]:
        """Generate geo-targeting suggestions from a list of service areas.

        Each area is classified as a city, zip code, county/region, or state,
        and an appropriate targeting suggestion is generated.  Results are
        sorted with primary areas first.
        """

        suggestions: List[GeoTargetingSuggestion] = []
        normalized_type = (
            business_type.lower().strip().replace(" ", "_").replace("-", "_")
            if business_type
            else ""
        )

        # Determine radius based on business type category
        if normalized_type in self._MOBILE_TYPES:
            default_radius = 25.0
            radius_reason = "mobile service business"
        elif normalized_type in self._STOREFRONT_TYPES:
            default_radius = self.suggest_radius(normalized_type)
            radius_reason = "storefront business"
        else:
            default_radius = self.suggest_radius(normalized_type) if normalized_type else 15.0
            radius_reason = "standard service area"

        for i, area in enumerate(service_areas):
            area = area.strip()
            priority = "primary" if i < max(1, len(service_areas) // 2) else "secondary"

            # Classify the area
            if re.match(r"^\d{5}(-\d{4})?$", area):
                # ZIP code
                suggestions.append(GeoTargetingSuggestion(
                    location=area,
                    location_type="zip",
                    radius_miles=None,
                    center_point=None,
                    estimated_population=None,
                    reason=f"ZIP code from service area list ({radius_reason}).",
                    priority=priority,
                ))
            elif re.match(r"^[A-Z]{2}$", area.upper()) and len(area) == 2:
                # State abbreviation
                suggestions.append(GeoTargetingSuggestion(
                    location=area.upper(),
                    location_type="state",
                    radius_miles=None,
                    center_point=None,
                    estimated_population=None,
                    reason="State-level targeting from service area list.",
                    priority=priority,
                ))
            elif any(
                kw in area.lower()
                for kw in ("county", "parish", "borough", "region")
            ):
                # County or region
                suggestions.append(GeoTargetingSuggestion(
                    location=area,
                    location_type="county",
                    radius_miles=None,
                    center_point=None,
                    estimated_population=None,
                    reason=f"County/region targeting from service area list.",
                    priority=priority,
                ))
            else:
                # Assume city -- add city targeting plus radius
                suggestions.append(GeoTargetingSuggestion(
                    location=area,
                    location_type="city",
                    radius_miles=None,
                    center_point=area,
                    estimated_population=None,
                    reason=f"City from service area list ({radius_reason}).",
                    priority=priority,
                ))
                # Also add a radius suggestion for the city
                suggestions.append(GeoTargetingSuggestion(
                    location=f"{area} ({default_radius}-mile radius)",
                    location_type="radius",
                    radius_miles=default_radius,
                    center_point=area,
                    estimated_population=None,
                    reason=(
                        f"{default_radius}-mile radius around {area} to capture "
                        f"surrounding areas ({radius_reason})."
                    ),
                    priority=priority,
                ))

        # Sort: primary first, then secondary, then expansion
        priority_order = {"primary": 0, "secondary": 1, "expansion": 2}
        suggestions.sort(key=lambda s: priority_order.get(s.priority, 99))

        return suggestions

    def expand_service_areas(
        self,
        current_areas: List[str],
        performance_data: Optional[Dict[str, Any]] = None,
    ) -> List[GeoTargetingSuggestion]:
        """Suggest expansion areas based on current targeting and performance.

        If ``performance_data`` is provided as a dict mapping area names to
        performance dicts (with keys like ``conversions``, ``ctr``, ``cpa``),
        expansion suggestions are prioritised adjacent to best-performing areas.
        """

        suggestions: List[GeoTargetingSuggestion] = []

        if not current_areas:
            return suggestions

        # Rank current areas by performance if data is available
        ranked_areas: List[str]
        if performance_data:
            # Sort by conversions descending, then by ctr descending
            def perf_key(area: str) -> tuple:
                data = performance_data.get(area, {})
                return (
                    -float(data.get("conversions", 0)),
                    -float(data.get("ctr", 0)),
                    float(data.get("cpa", float("inf"))),
                )

            ranked_areas = sorted(current_areas, key=perf_key)
        else:
            ranked_areas = list(current_areas)

        for area in ranked_areas:
            area = area.strip()
            perf_info = ""
            if performance_data and area in performance_data:
                data = performance_data[area]
                conversions = data.get("conversions", 0)
                ctr = data.get("ctr", 0)
                perf_info = f" (current performance: {conversions} conversions, {ctr:.1%} CTR)"

            # Suggest adjacent area expansion
            suggestions.append(GeoTargetingSuggestion(
                location=f"Areas adjacent to {area}",
                location_type="radius",
                radius_miles=15.0,
                center_point=area,
                estimated_population=None,
                reason=(
                    f"Expansion into areas surrounding {area}{perf_info}. "
                    "Adjacent areas often share similar demographics and demand patterns."
                ),
                priority="expansion",
            ))

            # Suggest wider radius expansion for top performers
            if performance_data and area in performance_data:
                data = performance_data[area]
                if float(data.get("conversions", 0)) > 0:
                    suggestions.append(GeoTargetingSuggestion(
                        location=f"Extended radius around {area}",
                        location_type="radius",
                        radius_miles=30.0,
                        center_point=area,
                        estimated_population=None,
                        reason=(
                            f"Extended reach around top-performing area {area}"
                            f"{perf_info}. Strong results suggest demand exists "
                            "in a wider geography."
                        ),
                        priority="expansion",
                    ))

        return suggestions


# ============================================================================
# Module-level helper functions
# ============================================================================


def calculate_monthly_projection(daily_budget: float) -> float:
    """Project monthly spend from a daily budget (daily * 30.4)."""
    return daily_budget * 30.4


def calculate_daily_from_monthly(monthly_budget: float) -> float:
    """Calculate daily budget from a monthly budget (monthly / 30.4)."""
    return monthly_budget / 30.4


def days_remaining_in_month(current_day: int) -> int:
    """Return approximate days remaining in the month (assumes 30-day month)."""
    return max(0, 30 - current_day)


def calculate_remaining_budget(monthly_cap: float, current_spend: float) -> float:
    """Return remaining budget for the month."""
    return max(0.0, monthly_cap - current_spend)


def format_budget_summary(
    daily: float,
    monthly_projected: float,
    cap: Optional[float] = None,
) -> str:
    """Return a formatted budget summary string.

    Example::

        $50.00/day ($1,520.00/month projected, $2,000.00/month cap, 76% utilized)
    """
    if cap is not None and cap > 0:
        utilization = monthly_projected / cap * 100
        return (
            f"${daily:,.2f}/day "
            f"(${monthly_projected:,.2f}/month projected, "
            f"${cap:,.2f}/month cap, "
            f"{utilization:.0f}% utilized)"
        )
    return f"${daily:,.2f}/day (${monthly_projected:,.2f}/month projected)"
