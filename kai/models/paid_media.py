"""Paid media data models for the Kai Marketing OS.

Canonical internal representations for campaigns, ad groups, ads, targeting,
performance metrics, budget guards, negative keyword lists, and exclusion
lists.  These models are platform-agnostic -- they store the "truth" of what
the business is running across all ad platforms and enable cross-platform
analysis, budget controls, variant workflows, and monitoring.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.

This module does **not** import anything from ``kai/runtime/``.
"""

from __future__ import annotations

import copy
import uuid
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


class CampaignObjective(str, Enum):
    """Campaign objective types across ad platforms."""

    awareness = "awareness"
    traffic = "traffic"
    leads = "leads"
    sales = "sales"
    app_installs = "app_installs"
    local = "local"


class CampaignStatus(str, Enum):
    """Lifecycle status of a campaign."""

    draft = "draft"
    enabled = "enabled"
    paused = "paused"
    ended = "ended"
    removed = "removed"
    limited = "limited"
    learning = "learning"


class BidStrategy(str, Enum):
    """Bid strategy options across platforms."""

    manual_cpc = "manual_cpc"
    maximize_conversions = "maximize_conversions"
    target_cpa = "target_cpa"
    target_roas = "target_roas"
    maximize_clicks = "maximize_clicks"
    lowest_cost = "lowest_cost"
    cost_cap = "cost_cap"
    bid_cap = "bid_cap"
    maximize_conversion_value = "maximize_conversion_value"


class AdFormat(str, Enum):
    """Ad creative format types."""

    search_responsive = "search_responsive"
    display_responsive = "display_responsive"
    performance_max = "performance_max"
    single_image = "single_image"
    single_video = "single_video"
    carousel = "carousel"
    collection = "collection"
    stories = "stories"
    reels = "reels"
    local_services = "local_services"
    shopping = "shopping"
    discovery = "discovery"


class AdStatus(str, Enum):
    """Status of an individual ad creative."""

    active = "active"
    paused = "paused"
    under_review = "under_review"
    disapproved = "disapproved"
    approved_limited = "approved_limited"
    removed = "removed"
    draft = "draft"


# ============================================================================
# Targeting
# ============================================================================


class Targeting(BaseModel):
    """Audience and placement targeting configuration.

    Used at both the campaign and ad-group level.  Ad-group targeting
    overrides campaign targeting when present.
    """

    locations: List[str] = Field(default_factory=list)
    location_radius_miles: Optional[float] = None
    location_exclusions: List[str] = Field(default_factory=list)
    age_min: Optional[int] = None
    age_max: Optional[int] = None
    genders: List[str] = Field(default_factory=lambda: ["all"])
    interests: List[str] = Field(default_factory=list)
    behaviors: List[str] = Field(default_factory=list)
    custom_audiences: List[str] = Field(default_factory=list)
    lookalike_audiences: List[str] = Field(default_factory=list)
    keywords: List[str] = Field(default_factory=list)
    keyword_match_types: Dict[str, str] = Field(default_factory=dict)
    negative_keywords: List[str] = Field(default_factory=list)
    placements: List[str] = Field(default_factory=list)
    devices: List[str] = Field(default_factory=list)
    schedule: Optional[Dict[str, Any]] = None
    languages: List[str] = Field(default_factory=lambda: ["en"])
    estimated_reach: Optional[int] = None
    targeting_summary: Optional[str] = None


# ============================================================================
# Negative Keywords & Exclusion Lists
# ============================================================================


class NegativeKeywordList(BaseModel):
    """A reusable list of negative keywords that can be shared across campaigns."""

    id: str
    name: str
    keywords: List[str] = Field(default_factory=list)
    match_type: str = "broad"
    applied_to_campaigns: List[str] = Field(default_factory=list)
    is_shared: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


STANDARD_NEGATIVE_KEYWORDS: Dict[str, List[str]] = {
    "universal": [
        "free",
        "cheap",
        "diy",
        "how to",
        "tutorial",
        "salary",
        "jobs",
        "hiring",
        "reddit",
        "youtube",
        "wikipedia",
        "what is",
        "definition",
    ],
    "local_service": [
        "near me complaints",
        "lawsuit",
        "scam",
        "worst",
        "avoid",
        "cheap",
        "free estimate",
        "jobs hiring",
        "careers",
    ],
    "ecommerce": [
        "free",
        "torrent",
        "download",
        "diy",
        "homemade",
        "used",
        "refurbished",
        "complaint",
        "recall",
    ],
    "professional_services": [
        "free",
        "cheap",
        "pro bono",
        "template",
        "diy",
        "example",
        "sample",
        "class",
        "course",
        "salary",
        "jobs",
    ],
}


class ExclusionList(BaseModel):
    """A reusable exclusion list for placements, topics, or audiences."""

    id: str
    name: str
    exclusion_type: str  # "placement", "topic", "audience"
    items: List[str] = Field(default_factory=list)
    applied_to_campaigns: List[str] = Field(default_factory=list)


# ============================================================================
# Ad
# ============================================================================


class Ad(BaseModel):
    """A single ad creative within an ad group.

    Supports variant tracking for A/B testing workflows -- ``variant_of``
    links back to the parent ad, ``variant_type`` describes what is being
    tested, and ``is_control`` marks the baseline variant.
    """

    id: str
    platform_id: Optional[str] = None
    ad_group_id: str
    campaign_id: str
    platform: str
    format: str  # AdFormat value
    headlines: List[str] = Field(default_factory=list)
    descriptions: List[str] = Field(default_factory=list)
    media_refs: List[str] = Field(default_factory=list)
    landing_url: str
    display_url: Optional[str] = None
    cta: Optional[str] = None
    status: str = "draft"
    compliance_status: str = "unchecked"
    compliance_issues: List[str] = Field(default_factory=list)
    disapproval_reasons: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    first_served_at: Optional[str] = None
    performance: Optional[Dict[str, Any]] = None
    variant_of: Optional[str] = None
    variant_type: Optional[str] = None
    is_control: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Ad Group
# ============================================================================


class AdGroup(BaseModel):
    """A group of ads within a campaign, with optional targeting refinements."""

    id: str
    platform_id: Optional[str] = None
    campaign_id: str
    platform: str
    name: str
    status: str = "enabled"
    targeting_refinement: Optional[Targeting] = None
    bid_amount: Optional[float] = None
    bid_strategy_override: Optional[str] = None
    ads: List[str] = Field(default_factory=list)
    ad_count: int = 0
    audience: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Ad Performance
# ============================================================================


class AdPerformance(BaseModel):
    """Performance metrics snapshot for a campaign, ad group, or ad.

    All numeric fields default to zero.  Optional fields are platform-
    specific metrics that may not be available on all platforms.
    """

    entity_id: str
    entity_type: str  # "campaign", "ad_group", "ad"
    platform: str
    date_range_start: str
    date_range_end: str
    impressions: int = 0
    clicks: int = 0
    ctr: float = 0.0
    conversions: float = 0.0
    conversion_rate: float = 0.0
    cost: float = 0.0
    cpc: float = 0.0
    cpa: float = 0.0
    roas: float = 0.0
    revenue: float = 0.0
    frequency: float = 0.0
    reach: int = 0
    quality_score: Optional[float] = None
    relevance_score: Optional[float] = None
    impression_share: Optional[float] = None
    search_impression_share: Optional[float] = None
    average_position: Optional[float] = None
    video_views: int = 0
    video_view_rate: float = 0.0
    fetched_at: Optional[str] = None


# ============================================================================
# Campaign
# ============================================================================


class Campaign(BaseModel):
    """Top-level campaign model -- the canonical internal representation.

    Links to ad groups by ID and carries campaign-level targeting,
    budgets, bid strategy, performance snapshots, and learning-phase
    tracking.
    """

    id: str
    platform_id: Optional[str] = None
    platform: str
    name: str
    objective: str  # CampaignObjective value
    status: str = "draft"
    budget_daily: Optional[float] = None
    budget_lifetime: Optional[float] = None
    budget_remaining: Optional[float] = None
    bid_strategy: str = "maximize_conversions"
    bid_target_value: Optional[float] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    targeting: Targeting = Field(default_factory=Targeting)
    ad_groups: List[str] = Field(default_factory=list)
    ad_group_count: int = 0
    total_ad_count: int = 0
    negative_keyword_lists: List[str] = Field(default_factory=list)
    exclusion_lists: List[str] = Field(default_factory=list)
    performance: Optional[AdPerformance] = None
    special_ad_category: Optional[str] = None
    learning_phase: bool = False
    learning_phase_end_estimate: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    launched_at: Optional[str] = None
    last_optimized_at: Optional[str] = None
    business_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Budget Guard
# ============================================================================


class BudgetGuard(BaseModel):
    """Cross-campaign budget safety guard for a business.

    Tracks daily and monthly spend across all monitored campaigns and
    triggers alerts or auto-pause when thresholds are reached.
    """

    id: str
    business_id: str
    max_daily_spend: float
    max_monthly_spend: float
    max_single_campaign_daily: Optional[float] = None
    alert_threshold_pct: float = 80.0
    auto_pause_threshold_pct: float = 100.0
    current_daily_spend: float = 0.0
    current_monthly_spend: float = 0.0
    is_alert_triggered: bool = False
    is_auto_pause_triggered: bool = False
    campaigns_monitored: List[str] = Field(default_factory=list)
    last_checked_at: Optional[str] = None
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# ID Generators
# ============================================================================


def generate_campaign_id() -> str:
    """Generate a unique campaign ID with ``cmp_`` prefix."""
    return f"cmp_{uuid.uuid4().hex[:12]}"


def generate_ad_group_id() -> str:
    """Generate a unique ad group ID with ``ag_`` prefix."""
    return f"ag_{uuid.uuid4().hex[:12]}"


def generate_ad_id() -> str:
    """Generate a unique ad ID with ``ad_`` prefix."""
    return f"ad_{uuid.uuid4().hex[:12]}"


def generate_nkl_id() -> str:
    """Generate a unique negative keyword list ID with ``nkl_`` prefix."""
    return f"nkl_{uuid.uuid4().hex[:12]}"


def generate_exclusion_id() -> str:
    """Generate a unique exclusion list ID with ``excl_`` prefix."""
    return f"excl_{uuid.uuid4().hex[:12]}"


def generate_budget_guard_id() -> str:
    """Generate a unique budget guard ID with ``bg_`` prefix."""
    return f"bg_{uuid.uuid4().hex[:12]}"


# ============================================================================
# Metric Calculators
# ============================================================================


def calculate_ctr(clicks: int, impressions: int) -> float:
    """Calculate click-through rate.  Returns 0.0 if impressions is zero."""
    if impressions == 0:
        return 0.0
    return clicks / impressions


def calculate_cpa(cost: float, conversions: float) -> float:
    """Calculate cost per acquisition.  Returns 0.0 if conversions is zero."""
    if conversions == 0:
        return 0.0
    return cost / conversions


def calculate_roas(revenue: float, cost: float) -> float:
    """Calculate return on ad spend.  Returns 0.0 if cost is zero."""
    if cost == 0:
        return 0.0
    return revenue / cost


def calculate_conversion_rate(conversions: float, clicks: int) -> float:
    """Calculate conversion rate.  Returns 0.0 if clicks is zero."""
    if clicks == 0:
        return 0.0
    return conversions / clicks


# ============================================================================
# Targeting Summary
# ============================================================================


def summarize_targeting(targeting: Targeting) -> str:
    """Generate a human-readable summary of targeting settings.

    Example output::

        Ages 25-55, Male+Female, Denver CO area, 15-mile radius,
        interests: home improvement, plumbing
    """
    parts: List[str] = []

    # Age range
    if targeting.age_min is not None or targeting.age_max is not None:
        age_min = targeting.age_min if targeting.age_min is not None else 18
        age_max_str = f"{targeting.age_max}" if targeting.age_max is not None else "65+"
        parts.append(f"Ages {age_min}-{age_max_str}")

    # Genders
    genders = targeting.genders
    if genders and genders != ["all"]:
        gender_label = "+".join(g.capitalize() for g in genders)
        parts.append(gender_label)

    # Locations
    if targeting.locations:
        loc_str = ", ".join(targeting.locations[:5])
        if len(targeting.locations) > 5:
            loc_str += f" +{len(targeting.locations) - 5} more"
        parts.append(loc_str)

    # Radius
    if targeting.location_radius_miles is not None:
        parts.append(f"{targeting.location_radius_miles}-mile radius")

    # Location exclusions
    if targeting.location_exclusions:
        excl_str = ", ".join(targeting.location_exclusions[:3])
        if len(targeting.location_exclusions) > 3:
            excl_str += f" +{len(targeting.location_exclusions) - 3} more"
        parts.append(f"excluding: {excl_str}")

    # Interests
    if targeting.interests:
        int_str = ", ".join(targeting.interests[:5])
        if len(targeting.interests) > 5:
            int_str += f" +{len(targeting.interests) - 5} more"
        parts.append(f"interests: {int_str}")

    # Behaviors
    if targeting.behaviors:
        beh_str = ", ".join(targeting.behaviors[:3])
        if len(targeting.behaviors) > 3:
            beh_str += f" +{len(targeting.behaviors) - 3} more"
        parts.append(f"behaviors: {beh_str}")

    # Keywords
    if targeting.keywords:
        kw_str = ", ".join(targeting.keywords[:5])
        if len(targeting.keywords) > 5:
            kw_str += f" +{len(targeting.keywords) - 5} more"
        parts.append(f"keywords: {kw_str}")

    # Negative keywords
    if targeting.negative_keywords:
        parts.append(f"{len(targeting.negative_keywords)} negative keywords")

    # Placements
    if targeting.placements:
        parts.append(f"placements: {', '.join(targeting.placements)}")

    # Devices
    if targeting.devices:
        parts.append(f"devices: {', '.join(targeting.devices)}")

    # Custom audiences
    if targeting.custom_audiences:
        parts.append(f"{len(targeting.custom_audiences)} custom audience(s)")

    # Lookalike audiences
    if targeting.lookalike_audiences:
        parts.append(f"{len(targeting.lookalike_audiences)} lookalike audience(s)")

    # Languages (only note if non-default)
    if targeting.languages and targeting.languages != ["en"]:
        parts.append(f"languages: {', '.join(targeting.languages)}")

    # Schedule
    if targeting.schedule is not None:
        days = list(targeting.schedule.keys())
        if days:
            parts.append(f"scheduled: {', '.join(d.capitalize() for d in days[:4])}")
            if len(days) > 4:
                parts[-1] += f" +{len(days) - 4} more days"

    # Estimated reach
    if targeting.estimated_reach is not None:
        parts.append(f"est. reach: {targeting.estimated_reach:,}")

    if not parts:
        return "No targeting restrictions (broad)"

    return ", ".join(parts)
