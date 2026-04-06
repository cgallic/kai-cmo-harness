"""Creative variant workflow and inventory tracking for the Kai Marketing OS.

Manages the lifecycle of ad creative variants: generating them from a base
creative, tracking which variant is winning, determining statistical
significance, promoting winners, and flagging stale creatives that need
refreshing.  Sits between the creative generation system and the ad platform
connectors so the paid media system always has fresh, tested creative options.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.

This module does **not** import anything from ``kai/runtime/``.
"""

from __future__ import annotations

import copy
import math
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


class VariantStatus(str, Enum):
    """Lifecycle status of a creative variant."""

    draft = "draft"
    testing = "testing"
    winning = "winning"
    losing = "losing"
    inconclusive = "inconclusive"
    retired = "retired"
    promoted = "promoted"


class VariantTestElement(str, Enum):
    """Which element of the ad creative is being tested."""

    headline = "headline"
    description = "description"
    image = "image"
    video = "video"
    cta = "cta"
    landing_page = "landing_page"
    audience = "audience"
    format = "format"


# ============================================================================
# Models
# ============================================================================


class CreativeVariant(BaseModel):
    """A single variant of an ad creative used in A/B testing."""

    id: str = Field(default_factory=lambda: generate_variant_id())
    base_creative_id: str = ""
    campaign_id: str = ""
    ad_group_id: str = ""
    platform: str = ""
    variant_type: str = ""
    variant_label: str = ""
    variant_content: Dict[str, Any] = Field(default_factory=dict)
    status: str = "draft"
    platform_ad_id: Optional[str] = None
    test_start_date: Optional[str] = None
    test_end_date: Optional[str] = None
    performance: Dict[str, float] = Field(default_factory=dict)
    sample_size: int = 0
    confidence_level: float = 0.0
    lift_vs_control: Optional[float] = None
    is_control: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class VariantTest(BaseModel):
    """A structured test comparing multiple creative variants."""

    id: str = Field(default_factory=lambda: generate_test_id())
    base_creative_id: str = ""
    campaign_id: str = ""
    platform: str = ""
    test_element: str = ""
    hypothesis: str = ""
    variants: List[str] = Field(default_factory=list)
    control_variant_id: str = ""
    primary_metric: str = "ctr"
    minimum_sample_size: int = 1000
    significance_threshold: float = 0.95
    status: str = "running"
    winner_id: Optional[str] = None
    result_summary: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CreativeInventoryItem(BaseModel):
    """A tracked ad creative in the inventory with freshness scoring."""

    id: str = Field(default_factory=lambda: generate_inventory_id())
    platform: str = ""
    campaign_id: Optional[str] = None
    ad_group_id: Optional[str] = None
    format: str = ""
    headlines: List[str] = Field(default_factory=list)
    descriptions: List[str] = Field(default_factory=list)
    media_refs: List[str] = Field(default_factory=list)
    landing_url: Optional[str] = None
    cta: Optional[str] = None
    status: str = "active"
    created_at: Optional[str] = None
    first_served_at: Optional[str] = None
    days_active: int = 0
    freshness_score: float = 1.0
    performance_trend: str = "no_data"
    last_performance_check: Optional[str] = None
    needs_refresh: bool = False
    variant_count: int = 0
    last_variant_test: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Variant generation strategies
# ============================================================================

VARIANT_GENERATION_STRATEGIES: Dict[str, Any] = {
    "headline": {
        "angles": [
            "question",
            "number_stat",
            "fear_pain",
            "benefit_led",
            "social_proof",
        ],
        "templates": {
            "question": "What if {benefit}?",
            "number_stat": "{number} {audience} trust {brand} for {service}",
            "fear_pain": "Stop {pain_point} -- {solution}",
            "benefit_led": "Get {benefit} in {timeframe}",
            "social_proof": "Join {number}+ {audience} who {outcome}",
        },
    },
    "cta": {
        "options_by_objective": {
            "leads": [
                "Get Free Quote",
                "Book Now",
                "Call Today",
                "Schedule Service",
                "Get Estimate",
            ],
            "sales": [
                "Buy Now",
                "Shop Now",
                "Order Today",
                "Get Started",
                "Claim Offer",
            ],
            "traffic": [
                "See Details",
                "Explore",
                "Read More",
                "Discover How",
                "View Options",
            ],
            "awareness": [
                "Watch Now",
                "See How",
                "Discover",
                "Explore",
                "View Story",
            ],
        },
    },
    "description": {
        "frameworks": [
            "benefit_first",
            "problem_first",
            "social_proof_first",
            "urgency_first",
        ],
        "templates": {
            "benefit_first": "{benefit}. {how_it_works}. {cta}.",
            "problem_first": "Tired of {problem}? {solution}. {cta}.",
            "social_proof_first": "{number}+ {audience} chose us. {benefit}. {cta}.",
            "urgency_first": "Limited time: {offer}. {benefit}. {cta}.",
        },
    },
}


# ============================================================================
# Helper functions
# ============================================================================


def generate_variant_id() -> str:
    """Return a unique creative variant ID with ``cv_`` prefix."""
    return f"cv_{uuid.uuid4().hex[:12]}"


def generate_test_id() -> str:
    """Return a unique variant test ID with ``vt_`` prefix."""
    return f"vt_{uuid.uuid4().hex[:12]}"


def generate_inventory_id() -> str:
    """Return a unique creative inventory ID with ``ci_`` prefix."""
    return f"ci_{uuid.uuid4().hex[:12]}"


def calculate_z_score(p1: float, n1: int, p2: float, n2: int) -> float:
    """Calculate the z-score for a two-proportion z-test.

    Compares proportions *p1* (from sample of size *n1*) and *p2* (from
    sample of size *n2*).  Returns 0.0 when inputs make computation
    impossible (zero sample sizes, identical proportions, or a zero pooled
    proportion).
    """
    if n1 <= 0 or n2 <= 0:
        return 0.0
    if p1 == p2:
        return 0.0
    p_combined = (p1 * n1 + p2 * n2) / (n1 + n2)
    if p_combined <= 0.0 or p_combined >= 1.0:
        return 0.0
    se = math.sqrt(p_combined * (1 - p_combined) * (1 / n1 + 1 / n2))
    if se == 0.0:
        return 0.0
    return (p1 - p2) / se


def is_significant(z_score: float, threshold: float = 0.95) -> bool:
    """Return ``True`` if the absolute z-score exceeds the critical value
    for the given confidence *threshold*.

    Supported thresholds:
        * 0.90 -> z > 1.645
        * 0.95 -> z > 1.96
        * 0.99 -> z > 2.576
    """
    critical_values: Dict[float, float] = {
        0.90: 1.645,
        0.95: 1.96,
        0.99: 2.576,
    }
    critical = critical_values.get(threshold, 1.96)
    return abs(z_score) > critical


def calculate_lift(control_rate: float, variant_rate: float) -> float:
    """Return the percentage lift of *variant_rate* over *control_rate*.

    Returns 0.0 when *control_rate* is zero to avoid division errors.
    A return value of 0.15 means the variant is 15% better than control.
    """
    if control_rate <= 0.0:
        return 0.0
    return (variant_rate - control_rate) / control_rate


def days_since(date_str: str) -> int:
    """Return the number of whole days between *date_str* and now (UTC).

    Accepts ISO-8601 date strings (``YYYY-MM-DD`` or full datetime).
    Returns 0 if the string cannot be parsed.
    """
    try:
        if "T" in date_str:
            dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        else:
            dt = datetime.fromisoformat(date_str).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        delta = now - dt
        return max(0, delta.days)
    except (ValueError, TypeError):
        return 0


# ============================================================================
# VariantWorkflow
# ============================================================================


class VariantWorkflow:
    """Manages the lifecycle of creative variant testing.

    Responsible for generating variant specs, creating tests, evaluating
    statistical significance, promoting winners, and suggesting what to
    test next.
    """

    def __init__(
        self,
        significance_threshold: float = 0.95,
        min_sample_size: int = 1000,
    ) -> None:
        self.significance_threshold = significance_threshold
        self.min_sample_size = min_sample_size

    # ------------------------------------------------------------------
    # generate_variants
    # ------------------------------------------------------------------

    def generate_variants(
        self,
        base_creative: Dict[str, Any],
        test_element: str,
        count: int = 3,
    ) -> List[CreativeVariant]:
        """Generate variant specs from a base creative.

        One variant is always the control (the original creative).  The
        remaining *count* variants explore different angles based on the
        *test_element* and the strategies defined in
        ``VARIANT_GENERATION_STRATEGIES``.
        """
        now = datetime.now(timezone.utc).isoformat()
        campaign_id = base_creative.get("campaign_id", "")
        ad_group_id = base_creative.get("ad_group_id", "")
        platform = base_creative.get("platform", "")
        base_id = base_creative.get("id", "")

        variants: List[CreativeVariant] = []

        # -- Control variant (the original) --
        control_content = self._extract_control_content(base_creative, test_element)
        control = CreativeVariant(
            id=generate_variant_id(),
            base_creative_id=base_id,
            campaign_id=campaign_id,
            ad_group_id=ad_group_id,
            platform=platform,
            variant_type=test_element,
            variant_label=f"Control ({test_element})",
            variant_content=control_content,
            status="draft",
            is_control=True,
            created_at=now,
            updated_at=now,
        )
        variants.append(control)

        # -- Generate test variants by element --
        if test_element == VariantTestElement.headline.value:
            variants.extend(
                self._generate_headline_variants(base_creative, count, now)
            )
        elif test_element == VariantTestElement.description.value:
            variants.extend(
                self._generate_description_variants(base_creative, count, now)
            )
        elif test_element == VariantTestElement.cta.value:
            variants.extend(
                self._generate_cta_variants(base_creative, count, now)
            )
        elif test_element == VariantTestElement.image.value:
            variants.extend(
                self._generate_image_variants(base_creative, count, now)
            )
        elif test_element == VariantTestElement.landing_page.value:
            variants.extend(
                self._generate_landing_page_variants(base_creative, count, now)
            )
        elif test_element == VariantTestElement.video.value:
            variants.extend(
                self._generate_video_variants(base_creative, count, now)
            )
        elif test_element == VariantTestElement.audience.value:
            variants.extend(
                self._generate_audience_variants(base_creative, count, now)
            )
        elif test_element == VariantTestElement.format.value:
            variants.extend(
                self._generate_format_variants(base_creative, count, now)
            )

        return variants

    # ------------------------------------------------------------------
    # create_test
    # ------------------------------------------------------------------

    def create_test(
        self,
        base_creative_id: str,
        variants: List[CreativeVariant],
        primary_metric: str = "ctr",
        hypothesis: Optional[str] = None,
    ) -> VariantTest:
        """Create a ``VariantTest`` from the base creative and variants.

        Auto-generates a hypothesis when none is provided.
        """
        now = datetime.now(timezone.utc).isoformat()
        variant_ids = [v.id for v in variants]

        control_variant_id = ""
        test_element = ""
        platform = ""
        campaign_id = ""
        for v in variants:
            if v.is_control:
                control_variant_id = v.id
            test_element = v.variant_type
            platform = v.platform
            campaign_id = v.campaign_id

        if not hypothesis:
            hypothesis = self._auto_hypothesis(test_element, primary_metric, variants)

        return VariantTest(
            id=generate_test_id(),
            base_creative_id=base_creative_id,
            campaign_id=campaign_id,
            platform=platform,
            test_element=test_element,
            hypothesis=hypothesis,
            variants=variant_ids,
            control_variant_id=control_variant_id,
            primary_metric=primary_metric,
            minimum_sample_size=self.min_sample_size,
            significance_threshold=self.significance_threshold,
            status="running",
            started_at=now,
        )

    # ------------------------------------------------------------------
    # evaluate_test
    # ------------------------------------------------------------------

    def evaluate_test(
        self,
        test: VariantTest,
        variant_performance: Dict[str, Dict[str, float]],
    ) -> VariantTest:
        """Evaluate a running test using the supplied performance data.

        *variant_performance* maps each variant ID to a dict of metrics::

            {"impressions": x, "clicks": x, "conversions": x,
             "ctr": x, "cpa": x, "roas": x}

        If any variant has not reached the minimum sample size the test
        remains ``"running"``.  When sufficient data exists a simplified
        statistical significance check is used (z-test for proportions on
        CTR; threshold-based comparison for CPA/ROAS).
        """
        metric = test.primary_metric

        # Check minimum sample sizes are met
        for vid in test.variants:
            perf = variant_performance.get(vid, {})
            impressions = int(perf.get("impressions", 0))
            if impressions < test.minimum_sample_size:
                test.status = "running"
                return test

        # Retrieve control performance
        control_perf = variant_performance.get(test.control_variant_id, {})
        control_metric_value = self._get_metric_value(control_perf, metric)
        control_impressions = int(control_perf.get("impressions", 0))
        control_clicks = int(control_perf.get("clicks", 0))

        best_variant_id: Optional[str] = None
        best_z: float = 0.0
        best_lift: float = 0.0
        all_results: Dict[str, Dict[str, Any]] = {}

        for vid in test.variants:
            perf = variant_performance.get(vid, {})
            variant_metric_value = self._get_metric_value(perf, metric)
            variant_impressions = int(perf.get("impressions", 0))
            variant_clicks = int(perf.get("clicks", 0))

            if vid == test.control_variant_id:
                all_results[vid] = {
                    "metric_value": variant_metric_value,
                    "z_score": 0.0,
                    "lift": 0.0,
                    "confidence": 0.0,
                    "is_control": True,
                }
                continue

            # Compute significance depending on metric type
            if metric == "ctr":
                z = calculate_z_score(
                    variant_metric_value,
                    variant_impressions,
                    control_metric_value,
                    control_impressions,
                )
                sig = is_significant(z, test.significance_threshold)
                confidence = min(1.0, abs(z) / 3.0)  # rough mapping
                lift = calculate_lift(control_metric_value, variant_metric_value)
            elif metric == "conversion_rate":
                z = calculate_z_score(
                    variant_metric_value,
                    variant_clicks,
                    control_metric_value,
                    control_clicks,
                )
                sig = is_significant(z, test.significance_threshold)
                confidence = min(1.0, abs(z) / 3.0)
                lift = calculate_lift(control_metric_value, variant_metric_value)
            elif metric in ("cpa", "roas"):
                # Threshold-based comparison for cost/revenue metrics
                lift = calculate_lift(control_metric_value, variant_metric_value)
                # For CPA, negative lift (lower CPA) is better
                effective_diff = abs(lift)
                sig = effective_diff >= 0.20 and variant_impressions >= test.minimum_sample_size
                z = effective_diff * 5.0  # synthetic z for ranking
                confidence = min(1.0, effective_diff / 0.30)
            else:
                z = 0.0
                sig = False
                confidence = 0.0
                lift = calculate_lift(control_metric_value, variant_metric_value)

            all_results[vid] = {
                "metric_value": variant_metric_value,
                "z_score": z,
                "lift": lift,
                "confidence": confidence,
                "is_control": False,
                "significant": sig,
            }

            # Determine best variant: for CPA lower is better, everything
            # else higher is better.
            is_better = False
            if metric == "cpa":
                is_better = variant_metric_value < control_metric_value and sig
            else:
                is_better = variant_metric_value > control_metric_value and sig

            if is_better and abs(z) > abs(best_z):
                best_z = z
                best_lift = lift
                best_variant_id = vid

        # Determine test outcome
        now = datetime.now(timezone.utc).isoformat()

        if best_variant_id:
            test.winner_id = best_variant_id
            test.status = "completed"
            test.completed_at = now
            winner_result = all_results[best_variant_id]
            lift_pct = round(winner_result["lift"] * 100, 1)
            test.result_summary = (
                f"Variant {best_variant_id} won with {lift_pct}% lift "
                f"on {metric} over control at "
                f"{round(winner_result['confidence'] * 100, 1)}% confidence."
            )
        else:
            # Check whether any variant even had enough data to be evaluated
            any_significant = any(
                r.get("significant", False)
                for r in all_results.values()
                if not r.get("is_control")
            )
            if not any_significant:
                # All variants evaluated but no winner -- inconclusive
                test.status = "completed"
                test.completed_at = now
                test.result_summary = (
                    f"Test completed. No variant achieved statistical significance "
                    f"on {metric} at {test.significance_threshold * 100:.0f}% confidence."
                )

        # Update individual variant results (returned via metadata)
        test.metadata = {**test.metadata, "variant_results": all_results}

        return test

    # ------------------------------------------------------------------
    # promote_winner
    # ------------------------------------------------------------------

    def promote_winner(self, test: VariantTest) -> Dict[str, Any]:
        """Generate instructions for promoting the winning variant.

        Does NOT execute the promotion -- returns a dict describing what
        the action system should do.
        """
        if not test.winner_id or test.status != "completed":
            return {
                "action": "none",
                "reason": "Test has no declared winner or is not completed.",
            }

        variant_results = test.metadata.get("variant_results", {})
        winner_result = variant_results.get(test.winner_id, {})

        pause_ids = [
            vid
            for vid in test.variants
            if vid != test.winner_id
        ]

        lift_pct = round(winner_result.get("lift", 0.0) * 100, 1)

        return {
            "action": "promote",
            "winner_id": test.winner_id,
            "updates": {
                "test_element": test.test_element,
                "base_creative_id": test.base_creative_id,
                "campaign_id": test.campaign_id,
                "platform": test.platform,
                "winning_metric": test.primary_metric,
                "winning_value": winner_result.get("metric_value", 0.0),
                "lift_vs_control_pct": lift_pct,
            },
            "pause_ids": pause_ids,
            "summary": (
                f"Promote variant {test.winner_id} as the new primary creative. "
                f"It achieved {lift_pct}% lift on {test.primary_metric}. "
                f"Pause {len(pause_ids)} other variant(s)."
            ),
        }

    # ------------------------------------------------------------------
    # suggest_next_test
    # ------------------------------------------------------------------

    def suggest_next_test(
        self,
        inventory_item: CreativeInventoryItem,
        past_tests: List[VariantTest],
    ) -> Optional[Dict[str, Any]]:
        """Suggest the next test element based on history and priority.

        Priority order: headline > cta > description > image > landing_page.
        Skips elements tested within the last 30 days.
        """
        priority_order = [
            VariantTestElement.headline.value,
            VariantTestElement.cta.value,
            VariantTestElement.description.value,
            VariantTestElement.image.value,
            VariantTestElement.landing_page.value,
        ]

        # Build a map of element -> most recent test date
        recent_tests: Dict[str, str] = {}
        for t in past_tests:
            elem = t.test_element
            completed = t.completed_at or t.started_at or ""
            if elem not in recent_tests or completed > recent_tests[elem]:
                recent_tests[elem] = completed

        now = datetime.now(timezone.utc)

        for element in priority_order:
            last_tested = recent_tests.get(element)
            if last_tested:
                days_ago = days_since(last_tested)
                if days_ago < 30:
                    continue

            reason_parts: List[str] = []
            if element not in recent_tests:
                reason_parts.append(f"{element} has never been tested on this creative")
            else:
                reason_parts.append(
                    f"{element} was last tested {days_since(recent_tests[element])} days ago"
                )

            if inventory_item.performance_trend == "declining":
                reason_parts.append("performance is declining")
            if inventory_item.needs_refresh:
                reason_parts.append("creative is flagged for refresh")

            priority = "high"
            if element in (
                VariantTestElement.image.value,
                VariantTestElement.landing_page.value,
            ):
                priority = "medium"

            return {
                "test_element": element,
                "reason": "; ".join(reason_parts),
                "priority": priority,
            }

        # All elements tested within last 30 days
        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_control_content(
        base_creative: Dict[str, Any], test_element: str
    ) -> Dict[str, Any]:
        """Pull the current content for the tested element from the base creative."""
        if test_element == VariantTestElement.headline.value:
            return {"headlines": list(base_creative.get("headlines", []))}
        if test_element == VariantTestElement.description.value:
            return {"descriptions": list(base_creative.get("descriptions", []))}
        if test_element == VariantTestElement.cta.value:
            return {"cta": base_creative.get("cta", "")}
        if test_element == VariantTestElement.image.value:
            return {"media_urls": list(base_creative.get("media_refs", []))}
        if test_element == VariantTestElement.landing_page.value:
            return {"landing_url": base_creative.get("landing_url", "")}
        if test_element == VariantTestElement.video.value:
            return {"media_urls": list(base_creative.get("media_refs", []))}
        if test_element == VariantTestElement.audience.value:
            return {"audience": base_creative.get("audience", "")}
        if test_element == VariantTestElement.format.value:
            return {"format": base_creative.get("format", "")}
        return {}

    @staticmethod
    def _get_metric_value(perf: Dict[str, float], metric: str) -> float:
        """Retrieve the value of a named metric from a performance dict."""
        return float(perf.get(metric, 0.0))

    def _base_variant(
        self,
        base_creative: Dict[str, Any],
        test_element: str,
        now: str,
    ) -> Dict[str, Any]:
        """Return common kwargs for constructing a ``CreativeVariant``."""
        return {
            "base_creative_id": base_creative.get("id", ""),
            "campaign_id": base_creative.get("campaign_id", ""),
            "ad_group_id": base_creative.get("ad_group_id", ""),
            "platform": base_creative.get("platform", ""),
            "variant_type": test_element,
            "status": "draft",
            "is_control": False,
            "created_at": now,
            "updated_at": now,
        }

    def _generate_headline_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        strategies = VARIANT_GENERATION_STRATEGIES["headline"]
        angles = strategies["angles"]
        templates = strategies["templates"]
        base_kwargs = self._base_variant(base_creative, VariantTestElement.headline.value, now)

        brand = base_creative.get("brand", "us")
        service = base_creative.get("service", "our service")
        benefit = base_creative.get("benefit", "better results")
        pain_point = base_creative.get("pain_point", "wasted budget")
        solution = base_creative.get("solution", "a proven approach")
        audience = base_creative.get("audience_label", "customers")
        outcome = base_creative.get("outcome", "saw results")
        timeframe = base_creative.get("timeframe", "days")
        number = base_creative.get("proof_number", "1,000")

        fill = {
            "brand": brand,
            "service": service,
            "benefit": benefit,
            "pain_point": pain_point,
            "solution": solution,
            "audience": audience,
            "outcome": outcome,
            "timeframe": timeframe,
            "number": number,
        }

        results: List[CreativeVariant] = []
        for i in range(min(count, len(angles))):
            angle = angles[i]
            template = templates.get(angle, "{benefit}")
            headline_text = template.format_map({**fill})
            label_map = {
                "question": "Headline: Question Hook",
                "number_stat": "Headline: Number/Stat Lead",
                "fear_pain": "Headline: Pain Point Hook",
                "benefit_led": "Headline: Benefit Lead",
                "social_proof": "Headline: Social Proof Lead",
            }
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=label_map.get(angle, f"Headline: {angle}"),
                    variant_content={"headlines": [headline_text]},
                    **base_kwargs,
                )
            )
        return results

    def _generate_description_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        strategies = VARIANT_GENERATION_STRATEGIES["description"]
        frameworks = strategies["frameworks"]
        templates = strategies["templates"]
        base_kwargs = self._base_variant(
            base_creative, VariantTestElement.description.value, now
        )

        benefit = base_creative.get("benefit", "better results")
        how_it_works = base_creative.get("how_it_works", "simple setup")
        cta_text = base_creative.get("cta", "Get started")
        problem = base_creative.get("pain_point", "wasted spend")
        solution = base_creative.get("solution", "a smarter approach")
        audience = base_creative.get("audience_label", "businesses")
        offer = base_creative.get("offer", "a free consultation")
        number = base_creative.get("proof_number", "500")

        fill = {
            "benefit": benefit,
            "how_it_works": how_it_works,
            "cta": cta_text,
            "problem": problem,
            "solution": solution,
            "audience": audience,
            "offer": offer,
            "number": number,
        }

        results: List[CreativeVariant] = []
        for i in range(min(count, len(frameworks))):
            fw = frameworks[i]
            template = templates.get(fw, "{benefit}. {cta}.")
            desc_text = template.format_map({**fill})
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=f"Description: {fw.replace('_', ' ').title()}",
                    variant_content={"descriptions": [desc_text]},
                    **base_kwargs,
                )
            )
        return results

    def _generate_cta_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        strategies = VARIANT_GENERATION_STRATEGIES["cta"]
        objective = base_creative.get("objective", "leads")
        options = strategies["options_by_objective"].get(
            objective,
            strategies["options_by_objective"]["leads"],
        )
        base_kwargs = self._base_variant(
            base_creative, VariantTestElement.cta.value, now
        )

        current_cta = base_creative.get("cta", "")
        available = [o for o in options if o.lower() != current_cta.lower()]
        if not available:
            available = options

        results: List[CreativeVariant] = []
        for i in range(min(count, len(available))):
            cta_text = available[i]
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=f"CTA: {cta_text}",
                    variant_content={"cta": cta_text},
                    **base_kwargs,
                )
            )
        return results

    def _generate_image_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        base_kwargs = self._base_variant(
            base_creative, VariantTestElement.image.value, now
        )
        image_angles = [
            ("Product/service close-up with clear branding", "Image: Product Close-Up"),
            ("Customer using the product in a real setting", "Image: Customer In Action"),
            ("Before-and-after comparison split frame", "Image: Before/After"),
            ("Team or staff photo conveying trust", "Image: Team Photo"),
            ("Bold text overlay with benefit statement", "Image: Text Overlay"),
        ]

        results: List[CreativeVariant] = []
        for i in range(min(count, len(image_angles))):
            description, label = image_angles[i]
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=label,
                    variant_content={
                        "image_brief": description,
                        "media_urls": [],
                    },
                    **base_kwargs,
                )
            )
        return results

    def _generate_landing_page_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        base_kwargs = self._base_variant(
            base_creative, VariantTestElement.landing_page.value, now
        )
        landing_url = base_creative.get("landing_url", "")

        lp_angles = [
            (f"{landing_url}?v=short_form", "LP: Short-Form (Above Fold CTA)"),
            (f"{landing_url}?v=long_form", "LP: Long-Form (Full Story)"),
            (f"{landing_url}?v=social_proof", "LP: Social Proof Heavy"),
            (f"{landing_url}?v=video_hero", "LP: Video Hero"),
        ]

        results: List[CreativeVariant] = []
        for i in range(min(count, len(lp_angles))):
            url, label = lp_angles[i]
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=label,
                    variant_content={"landing_url": url},
                    **base_kwargs,
                )
            )
        return results

    def _generate_video_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        base_kwargs = self._base_variant(
            base_creative, VariantTestElement.video.value, now
        )
        video_angles = [
            ("Testimonial-led video with customer speaking to camera", "Video: Testimonial"),
            ("Product demo with quick-cut editing", "Video: Product Demo"),
            ("Problem-agitation-solution narrative arc", "Video: PAS Narrative"),
            ("UGC-style casual phone recording", "Video: UGC Style"),
        ]

        results: List[CreativeVariant] = []
        for i in range(min(count, len(video_angles))):
            brief, label = video_angles[i]
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=label,
                    variant_content={"video_brief": brief, "media_urls": []},
                    **base_kwargs,
                )
            )
        return results

    def _generate_audience_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        base_kwargs = self._base_variant(
            base_creative, VariantTestElement.audience.value, now
        )
        audience_angles = [
            ("Broad targeting -- let the algorithm optimize", "Audience: Broad"),
            ("Interest-based targeting -- niche interests", "Audience: Interest Stack"),
            ("Lookalike audience from top customers", "Audience: Lookalike"),
            ("Retargeting audience -- past visitors", "Audience: Retargeting"),
        ]

        results: List[CreativeVariant] = []
        for i in range(min(count, len(audience_angles))):
            desc, label = audience_angles[i]
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=label,
                    variant_content={"audience_description": desc},
                    **base_kwargs,
                )
            )
        return results

    def _generate_format_variants(
        self, base_creative: Dict[str, Any], count: int, now: str
    ) -> List[CreativeVariant]:
        base_kwargs = self._base_variant(
            base_creative, VariantTestElement.format.value, now
        )
        format_angles = [
            ("single_image", "Format: Single Image"),
            ("single_video", "Format: Single Video"),
            ("carousel", "Format: Carousel"),
            ("stories", "Format: Stories"),
        ]
        current_format = base_creative.get("format", "")
        available = [(f, l) for f, l in format_angles if f != current_format]
        if not available:
            available = format_angles

        results: List[CreativeVariant] = []
        for i in range(min(count, len(available))):
            fmt, label = available[i]
            results.append(
                CreativeVariant(
                    id=generate_variant_id(),
                    variant_label=label,
                    variant_content={"format": fmt},
                    **base_kwargs,
                )
            )
        return results

    @staticmethod
    def _auto_hypothesis(
        test_element: str,
        primary_metric: str,
        variants: List[CreativeVariant],
    ) -> str:
        """Auto-generate a hypothesis string from test context."""
        non_control = [v for v in variants if not v.is_control]
        labels = ", ".join(v.variant_label for v in non_control[:3])
        metric_label = primary_metric.upper().replace("_", " ")
        return (
            f"Testing {test_element} variants ({labels}) will produce a "
            f"statistically significant difference in {metric_label} "
            f"compared to the control."
        )


# ============================================================================
# CreativeInventory
# ============================================================================


class CreativeInventory:
    """Tracks all ad creatives with freshness scoring.

    Flags stale creatives that need refreshing and provides inventory
    summaries by platform and format.
    """

    def __init__(
        self,
        freshness_threshold: float = 0.3,
        max_days_without_refresh: int = 30,
    ) -> None:
        self.freshness_threshold = freshness_threshold
        self.max_days_without_refresh = max_days_without_refresh
        self._items: Dict[str, CreativeInventoryItem] = {}

    # ------------------------------------------------------------------
    # add_creative
    # ------------------------------------------------------------------

    def add_creative(self, creative: Dict[str, Any]) -> CreativeInventoryItem:
        """Create and register a ``CreativeInventoryItem`` from a dict."""
        now = datetime.now(timezone.utc).isoformat()
        item = CreativeInventoryItem(
            id=generate_inventory_id(),
            platform=creative.get("platform", ""),
            campaign_id=creative.get("campaign_id"),
            ad_group_id=creative.get("ad_group_id"),
            format=creative.get("format", ""),
            headlines=list(creative.get("headlines", [])),
            descriptions=list(creative.get("descriptions", [])),
            media_refs=list(creative.get("media_refs", [])),
            landing_url=creative.get("landing_url"),
            cta=creative.get("cta"),
            status="active",
            created_at=now,
            freshness_score=1.0,
        )
        self._items[item.id] = item
        return item

    # ------------------------------------------------------------------
    # update_performance
    # ------------------------------------------------------------------

    def update_performance(
        self,
        item_id: str,
        performance: Dict[str, float],
    ) -> CreativeInventoryItem:
        """Update performance data and compute the performance trend.

        *performance* should contain ``ctr_last_7d`` and ``ctr_prev_7d``
        keys for trend computation.
        """
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"Inventory item {item_id} not found")

        now = datetime.now(timezone.utc).isoformat()
        item.last_performance_check = now

        ctr_last_7d = performance.get("ctr_last_7d", 0.0)
        ctr_prev_7d = performance.get("ctr_prev_7d", 0.0)

        if ctr_prev_7d > 0:
            change_pct = ((ctr_last_7d - ctr_prev_7d) / ctr_prev_7d) * 100
            if change_pct > 10.0:
                item.performance_trend = "improving"
            elif change_pct < -10.0:
                item.performance_trend = "declining"
            else:
                item.performance_trend = "stable"
        else:
            item.performance_trend = "no_data"

        # Recalculate freshness after updating trend
        item.freshness_score = self.calculate_freshness(item)
        item.metadata = {**item.metadata, "last_performance": performance}

        self._items[item_id] = item
        return item

    # ------------------------------------------------------------------
    # calculate_freshness
    # ------------------------------------------------------------------

    def calculate_freshness(self, item: CreativeInventoryItem) -> float:
        """Calculate freshness score for a creative.

        Formula::

            freshness = max(0.0, 1.0 - (days_active / max_days) * degradation)

        The *degradation_factor* depends on ``performance_trend``:

        * ``"declining"``  -> 1.0  (degrades at full speed)
        * ``"stable"``     -> 0.7
        * ``"improving"``  -> 0.4  (degrades much slower)
        * ``"no_data"``    -> 0.7  (assume stable)
        """
        degradation_map: Dict[str, float] = {
            "declining": 1.0,
            "stable": 0.7,
            "improving": 0.4,
            "no_data": 0.7,
        }
        degradation_factor = degradation_map.get(item.performance_trend, 0.7)

        if self.max_days_without_refresh <= 0:
            freshness = 1.0
        else:
            freshness = 1.0 - (
                item.days_active / self.max_days_without_refresh
            ) * degradation_factor

        freshness = max(0.0, min(1.0, freshness))

        item.needs_refresh = freshness < self.freshness_threshold
        item.freshness_score = freshness

        return freshness

    # ------------------------------------------------------------------
    # get_stale_creatives
    # ------------------------------------------------------------------

    def get_stale_creatives(self) -> List[CreativeInventoryItem]:
        """Return all items that need refreshing, sorted by staleness."""
        stale = [
            item
            for item in self._items.values()
            if item.needs_refresh or item.days_active > self.max_days_without_refresh
        ]
        stale.sort(key=lambda i: i.freshness_score)
        return stale

    # ------------------------------------------------------------------
    # get_inventory_summary
    # ------------------------------------------------------------------

    def get_inventory_summary(
        self, platform: Optional[str] = None
    ) -> Dict[str, Any]:
        """Return an aggregated inventory summary.

        Optionally filter to a single *platform*.
        """
        items = list(self._items.values())
        if platform:
            items = [i for i in items if i.platform == platform]

        total = len(items)
        active = sum(1 for i in items if i.status == "active")
        stale = sum(
            1 for i in items
            if i.needs_refresh or i.days_active > self.max_days_without_refresh
        )
        avg_freshness = (
            sum(i.freshness_score for i in items) / total if total > 0 else 0.0
        )

        by_platform: Dict[str, int] = {}
        by_format: Dict[str, int] = {}
        for i in items:
            by_platform[i.platform] = by_platform.get(i.platform, 0) + 1
            by_format[i.format] = by_format.get(i.format, 0) + 1

        needs_attention = [
            {
                "id": i.id,
                "platform": i.platform,
                "freshness_score": round(i.freshness_score, 3),
                "days_active": i.days_active,
                "performance_trend": i.performance_trend,
            }
            for i in sorted(items, key=lambda x: x.freshness_score)
            if i.needs_refresh or i.days_active > self.max_days_without_refresh
        ]

        return {
            "total": total,
            "active": active,
            "stale": stale,
            "average_freshness": round(avg_freshness, 3),
            "by_platform": by_platform,
            "by_format": by_format,
            "needs_attention": needs_attention,
        }

    # ------------------------------------------------------------------
    # retire_creative
    # ------------------------------------------------------------------

    def retire_creative(
        self, item_id: str, reason: str = "Stale"
    ) -> CreativeInventoryItem:
        """Set a creative's status to ``retired`` and record the reason."""
        item = self._items.get(item_id)
        if item is None:
            raise KeyError(f"Inventory item {item_id} not found")

        item.status = "retired"
        item.metadata = {**item.metadata, "retire_reason": reason}
        self._items[item_id] = item
        return item
