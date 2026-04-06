"""Proof-of-life automation, filler suppression, and staleness detection.

Ensures a minimum viable social media presence even when the operator is
too busy to create content manually.  The ``ProofOfLifeEngine`` generates
posting plans that draw from existing content inventory first.  The
``FillerSuppressor`` blocks low-quality filler (generic quotes, empty
holiday posts, AI slop) so that autopilot posts maintain brand quality.
The ``StalenessDetector`` monitors for platform inactivity and triggers
escalating alerts.
"""

from __future__ import annotations

import copy
import re
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with fallback (mirrors gateway/models.py)
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


class ProofOfLifeStatus(str, Enum):
    """Health status of a platform's posting cadence."""

    healthy = "healthy"
    at_risk = "at_risk"
    stale = "stale"
    critical = "critical"
    disabled = "disabled"


class FillerRejectionReason(str, Enum):
    """Reasons a piece of content is classified as filler."""

    generic_motivational = "generic_motivational"
    stock_photo_no_context = "stock_photo_no_context"
    empty_holiday = "empty_holiday"
    low_quality_score = "low_quality_score"
    duplicate_recent = "duplicate_recent"
    no_brand_relevance = "no_brand_relevance"
    ai_slop_detected = "ai_slop_detected"


# ============================================================================
# Models
# ============================================================================


class PlatformHealth(BaseModel):
    """Health snapshot for a single platform."""

    platform: str = Field(..., description="Platform name")
    is_active: bool = Field(True, description="Whether the business uses this platform")
    last_post_date: Optional[str] = Field(None, description="ISO date of last detected post")
    days_since_last_post: int = Field(0)
    posts_this_week: int = Field(0)
    posts_this_month: int = Field(0)
    status: str = Field(
        ProofOfLifeStatus.healthy.value,
        description="ProofOfLifeStatus value",
    )
    staleness_threshold_days: int = Field(14, description="Days without a post before stale flag")
    minimum_posts_per_week: int = Field(1, description="Minimum posting frequency target")
    content_types_used_30d: List[str] = Field(
        default_factory=list,
        description="Content types used in last 30 days",
    )
    content_type_gaps: List[str] = Field(
        default_factory=list,
        description="Content types that should be used but have not been",
    )


class ProofOfLifePlan(BaseModel):
    """Posting plan for a single platform over a planning period."""

    platform: str = Field(...)
    planned_posts: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of planned post dicts with content_type, suggested_date, etc.",
    )
    frequency_target: str = Field("1 post per week")
    content_mix: Dict[str, int] = Field(
        default_factory=dict,
        description="content_type -> count per cycle",
    )
    covers_period: str = Field("", description="e.g. 2026-04-01 to 2026-04-07")
    uses_existing_content: int = Field(0)
    requires_new_content: int = Field(0)


class FillerCheckResult(BaseModel):
    """Result of running filler detection checks on content."""

    is_filler: bool = Field(False, description="True if content is detected as filler")
    rejection_reasons: List[str] = Field(default_factory=list)
    quality_score: Optional[float] = Field(
        None, description="Estimated Four U's score, 0-16 scale"
    )
    improvement_suggestions: List[str] = Field(default_factory=list)
    brand_relevance_score: float = Field(0.0, description="0.0 to 1.0")
    checked_at: Optional[str] = Field(None, description="ISO timestamp")


class StalenessAlert(BaseModel):
    """Alert generated when a platform goes too long without posting."""

    id: str = Field(..., description="Format: stale_{uuid_hex[:12]}")
    platform: str = Field(...)
    days_since_last_post: int = Field(0)
    severity: str = Field(
        ..., description="warning (7-13 days), alert (14-21 days), critical (21+ days)"
    )
    suggested_action: str = Field(...)
    created_at: str = Field(..., description="ISO timestamp")
    acknowledged: bool = Field(False)


class ContentInventoryItem(BaseModel):
    """A single piece of reusable content in the inventory."""

    id: str = Field(..., description="Unique ID")
    content_type: str = Field(..., description="SocialContentType value")
    source: str = Field(
        ...,
        description=(
            "Where this came from: completed_job, customer_review, team_event, "
            "seasonal_calendar, operator_upload, generated"
        ),
    )
    raw_content: str = Field(..., description="Source material text")
    media_refs: List[str] = Field(default_factory=list)
    usable_platforms: List[str] = Field(default_factory=list)
    used_count: int = Field(0)
    last_used_date: Optional[str] = Field(None)
    freshness_score: float = Field(1.0, description="1.0 = fresh, 0.0 = stale")
    created_at: str = Field(...)


# ============================================================================
# Constants — filler detection patterns
# ============================================================================

GENERIC_MOTIVATIONAL_PATTERNS: List[str] = [
    "rise and grind",
    "your only limit is you",
    "be the change",
    "good vibes only",
    "monday motivation",
    "hustle harder",
    "dream big",
    "stay positive",
    "believe in yourself",
    "make it happen",
    "never give up",
    "work hard play hard",
    "blessed and grateful",
    "living my best life",
    "new week new goals",
    "mindset is everything",
    "the grind never stops",
    "success is a journey",
    "positive vibes",
    "thankful thursday",
    "transformation tuesday",
    "wellness wednesday",
    "flashback friday",
    "self care sunday",
    "you got this",
    "keep going",
    "sky is the limit",
    "chase your dreams",
    "be unstoppable",
    "progress not perfection",
]

EMPTY_HOLIDAY_PATTERNS: List[str] = [
    r"^(happy|merry|blessed)\s+(monday|tuesday|wednesday|thursday|friday|saturday|sunday)!?\s*$",
    r"^(happy|merry|blessed)\s+\w+\s*(day|eve|weekend)!?\s*$",
    r"^(happy|merry|blessed)\s+(new year|valentine|easter|memorial|independence|labor|thanksgiving|christmas|hanukkah|diwali|holiday)s?!?\s*[^\w]*\s*$",
]

# AI slop phrases from CLAUDE.md quality gate rules.
_AI_SLOP_PHRASES: List[str] = [
    "in conclusion",
    "it's important to note",
    "in today's rapidly evolving",
    "this comprehensive guide",
    "without further ado",
    "it's worth noting that",
]

# Default content type rotation for proof-of-life scheduling.
_DEFAULT_CONTENT_ROTATION: List[str] = [
    "proof_post",
    "local_tip_post",
    "behind_the_scenes_post",
    "educational_post",
]

# All valid content types that should appear in a healthy mix.
_ALL_CONTENT_TYPES: List[str] = [
    "proof_post",
    "testimonial_post",
    "local_tip_post",
    "offer_post",
    "behind_the_scenes_post",
    "educational_post",
    "community_post",
    "seasonal_post",
]

# Minimum viable weekly content mix.
_MINIMUM_WEEKLY_MIX: Dict[str, int] = {
    "proof_post": 1,
    "local_tip_post": 1,
    "behind_the_scenes_post": 1,
}

# Season mapping by month number.
_MONTH_TO_SEASON: Dict[int, str] = {
    1: "winter", 2: "winter", 3: "spring",
    4: "spring", 5: "spring", 6: "summer",
    7: "summer", 8: "summer", 9: "fall",
    10: "fall", 11: "fall", 12: "winter",
}


# ============================================================================
# Helper functions (module-level)
# ============================================================================


def generate_stale_alert_id() -> str:
    """Return a staleness alert ID in format ``stale_{uuid_hex[:12]}``."""
    return f"stale_{uuid.uuid4().hex[:12]}"


def days_between(date_a: str, date_b: str) -> int:
    """Calculate days between two ISO date strings.

    Returns an absolute value so argument order does not matter.
    """
    fmt_options = ["%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%Y-%m-%dT%H:%M:%S%z"]
    da: Optional[datetime] = None
    db: Optional[datetime] = None

    for fmt in fmt_options:
        if da is None:
            try:
                da = datetime.strptime(date_a[:19], fmt[:19] if "T" in date_a else fmt)
            except ValueError:
                pass
        if db is None:
            try:
                db = datetime.strptime(date_b[:19], fmt[:19] if "T" in date_b else fmt)
            except ValueError:
                pass

    if da is None or db is None:
        # Last-resort: try the basic date format.
        da = da or datetime.strptime(date_a[:10], "%Y-%m-%d")
        db = db or datetime.strptime(date_b[:10], "%Y-%m-%d")

    return abs((da - db).days)


def get_current_season() -> str:
    """Return the current season based on the current month."""
    month = datetime.now(timezone.utc).month
    return _MONTH_TO_SEASON.get(month, "spring")


def is_seasonal_relevant(content_type: str, season: str) -> bool:
    """Certain content types are more relevant in certain seasons.

    Returns ``True`` if *content_type* is especially suited to *season*.
    """
    relevance: Dict[str, List[str]] = {
        "seasonal_post": ["spring", "summer", "fall", "winter"],
        "offer_post": ["spring", "fall"],
        "community_post": ["summer", "fall"],
        "behind_the_scenes_post": ["winter"],
    }
    seasons = relevance.get(content_type, [])
    return season.lower() in seasons


# ============================================================================
# ProofOfLifeEngine
# ============================================================================


class ProofOfLifeEngine:
    """Core engine that maintains minimum social presence."""

    def __init__(
        self,
        minimum_posts_per_week: int = 1,
        platforms: Optional[List[str]] = None,
    ) -> None:
        self.minimum_posts_per_week = minimum_posts_per_week
        self.platforms = platforms or ["instagram", "facebook"]
        # Internal post tracking for mark_post_published.
        self._published_log: List[Dict[str, str]] = []
        # Track the last scheduled content type per platform to avoid consecutive dupes.
        self._last_content_type: Dict[str, str] = {}

    def assess_health(
        self, post_history: List[Dict[str, Any]],
    ) -> Dict[str, PlatformHealth]:
        """Assess health status of each active platform.

        *post_history* items must have at minimum::

            {"platform": str, "published_at": str, "content_type": Optional[str]}

        Returns a mapping of platform name to ``PlatformHealth``.
        """
        now = datetime.now(timezone.utc)
        now_str = now.strftime("%Y-%m-%d")
        week_ago = now - timedelta(days=7)
        month_ago = now - timedelta(days=30)

        result: Dict[str, PlatformHealth] = {}

        for platform in self.platforms:
            platform_posts = [
                p for p in post_history if p.get("platform") == platform
            ]

            # Find last post date.
            last_post_date: Optional[str] = None
            days_since = 0
            if platform_posts:
                dates = []
                for p in platform_posts:
                    pub = p.get("published_at", "")
                    if pub:
                        dates.append(pub)
                if dates:
                    dates.sort(reverse=True)
                    last_post_date = dates[0]
                    days_since = days_between(last_post_date, now_str)

            # Count posts this week and this month.
            posts_this_week = 0
            posts_this_month = 0
            content_types_30d: List[str] = []

            for p in platform_posts:
                pub = p.get("published_at", "")
                if not pub:
                    continue
                try:
                    pub_dt = datetime.strptime(pub[:10], "%Y-%m-%d").replace(
                        tzinfo=timezone.utc
                    )
                except ValueError:
                    continue
                if pub_dt >= week_ago:
                    posts_this_week += 1
                if pub_dt >= month_ago:
                    posts_this_month += 1
                    ct = p.get("content_type")
                    if ct and ct not in content_types_30d:
                        content_types_30d.append(ct)

            # Determine status.
            if last_post_date is None:
                status = ProofOfLifeStatus.critical.value
                days_since = 999
            elif days_since >= 21:
                status = ProofOfLifeStatus.critical.value
            elif days_since >= 14:
                status = ProofOfLifeStatus.stale.value
            elif posts_this_week < self.minimum_posts_per_week and days_since >= 7:
                status = ProofOfLifeStatus.at_risk.value
            elif posts_this_week < self.minimum_posts_per_week:
                status = ProofOfLifeStatus.at_risk.value
            else:
                status = ProofOfLifeStatus.healthy.value

            # Identify content type gaps.
            recommended_types = [
                "proof_post", "local_tip_post", "behind_the_scenes_post",
                "educational_post",
            ]
            content_type_gaps = [
                ct for ct in recommended_types if ct not in content_types_30d
            ]

            result[platform] = PlatformHealth(
                platform=platform,
                is_active=True,
                last_post_date=last_post_date,
                days_since_last_post=days_since,
                posts_this_week=posts_this_week,
                posts_this_month=posts_this_month,
                status=status,
                staleness_threshold_days=14,
                minimum_posts_per_week=self.minimum_posts_per_week,
                content_types_used_30d=content_types_30d,
                content_type_gaps=content_type_gaps,
            )

        # If ALL platforms are critical, mark them all as critical.
        all_statuses = [h.status for h in result.values()]
        if all_statuses and all(s == ProofOfLifeStatus.critical.value for s in all_statuses):
            for h in result.values():
                h.status = ProofOfLifeStatus.critical.value

        return result

    def generate_plan(
        self,
        health: Dict[str, PlatformHealth],
        content_inventory: List[ContentInventoryItem],
        days_ahead: int = 7,
    ) -> Dict[str, ProofOfLifePlan]:
        """Generate a posting plan for each at-risk, stale, or critical platform.

        Prioritizes existing content inventory before flagging new content needs.
        """
        now = datetime.now(timezone.utc)
        end_date = now + timedelta(days=days_ahead)
        covers = f"{now.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"

        plans: Dict[str, ProofOfLifePlan] = {}

        for platform, ph in health.items():
            if ph.status == ProofOfLifeStatus.healthy.value:
                continue
            if ph.status == ProofOfLifeStatus.disabled.value:
                continue

            planned_posts: List[Dict[str, Any]] = []
            content_mix: Dict[str, int] = {}
            uses_existing = 0
            requires_new = 0

            # For critical: schedule an immediate post.
            is_critical = ph.status == ProofOfLifeStatus.critical.value
            is_stale = ph.status == ProofOfLifeStatus.stale.value

            # Determine how many posts to schedule.
            if is_critical:
                num_posts = max(3, self.minimum_posts_per_week)
            elif is_stale:
                num_posts = max(2, self.minimum_posts_per_week)
            else:
                num_posts = self.minimum_posts_per_week

            # Build the content type sequence.
            for i in range(num_posts):
                content_type = self.select_next_content_type(ph)

                # Try to find inventory item for this content type and platform.
                inventory_match = self._find_inventory_item(
                    content_inventory, content_type, platform,
                )

                if is_critical and i == 0:
                    # Immediate post — next available slot.
                    suggested_date = now.strftime("%Y-%m-%d")
                    suggested_time = "10:00"
                    priority = "immediate"
                else:
                    # Spread across the planning period.
                    day_offset = max(1, (days_ahead // num_posts) * (i + (0 if not is_critical else 1)))
                    post_date = now + timedelta(days=min(day_offset, days_ahead))
                    suggested_date = post_date.strftime("%Y-%m-%d")
                    suggested_time = "10:00"
                    priority = "normal"

                content_brief = ""
                if inventory_match:
                    content_brief = (
                        f"Reuse inventory item '{inventory_match.id}': "
                        f"{inventory_match.raw_content[:100]}..."
                        if len(inventory_match.raw_content) > 100
                        else f"Reuse inventory item '{inventory_match.id}': {inventory_match.raw_content}"
                    )
                    uses_existing += 1
                    # Mark as used so it is not reused in this plan.
                    inventory_match.used_count += 1
                else:
                    content_brief = (
                        f"Create new {content_type} content for {platform}."
                    )
                    requires_new += 1

                planned_posts.append({
                    "content_type": content_type,
                    "suggested_date": suggested_date,
                    "suggested_time": suggested_time,
                    "content_brief": content_brief,
                    "priority": priority,
                })

                content_mix[content_type] = content_mix.get(content_type, 0) + 1
                # Update last scheduled to avoid consecutive duplicates.
                self._last_content_type[platform] = content_type

            plans[platform] = ProofOfLifePlan(
                platform=platform,
                planned_posts=planned_posts,
                frequency_target=f"{self.minimum_posts_per_week} post{'s' if self.minimum_posts_per_week != 1 else ''} per week",
                content_mix=content_mix,
                covers_period=covers,
                uses_existing_content=uses_existing,
                requires_new_content=requires_new,
            )

        return plans

    def select_next_content_type(self, health: PlatformHealth) -> str:
        """Determine which content type to post next for a given platform.

        Rules:
        1. If content_type_gaps exist, fill the most important gap first.
        2. If seasonal context applies, prioritize seasonal_post.
        3. Follow the default rotation, skipping the last used type.
        4. Never return the same type as the previous post on this platform.
        """
        platform = health.platform
        last_used = self._last_content_type.get(platform)

        # 1. Check for seasonal relevance.
        season = get_current_season()
        if is_seasonal_relevant("seasonal_post", season):
            if last_used != "seasonal_post" and "seasonal_post" in health.content_type_gaps:
                self._last_content_type[platform] = "seasonal_post"
                return "seasonal_post"

        # 2. Fill content type gaps (prioritize proof_post > local_tip > bts > educational).
        gap_priority = [
            "proof_post", "local_tip_post", "behind_the_scenes_post",
            "educational_post", "testimonial_post", "community_post",
        ]
        for ct in gap_priority:
            if ct in health.content_type_gaps and ct != last_used:
                self._last_content_type[platform] = ct
                return ct

        # 3. Default rotation.
        for ct in _DEFAULT_CONTENT_ROTATION:
            if ct != last_used:
                self._last_content_type[platform] = ct
                return ct

        # 4. Fallback — just pick the first rotation item even if it matches.
        fallback = _DEFAULT_CONTENT_ROTATION[0]
        self._last_content_type[platform] = fallback
        return fallback

    def mark_post_published(
        self, platform: str, content_type: str, published_at: str,
    ) -> None:
        """Update internal tracking when a post is published."""
        self._published_log.append({
            "platform": platform,
            "content_type": content_type,
            "published_at": published_at,
        })
        self._last_content_type[platform] = content_type

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _find_inventory_item(
        self,
        inventory: List[ContentInventoryItem],
        content_type: str,
        platform: str,
    ) -> Optional[ContentInventoryItem]:
        """Find the best inventory item for a content type and platform.

        Prefers items with ``used_count == 0`` and high freshness.
        """
        candidates = [
            item for item in inventory
            if item.content_type == content_type
            and platform in item.usable_platforms
        ]

        if not candidates:
            return None

        # Sort: unused first, then by freshness descending.
        candidates.sort(key=lambda x: (x.used_count, -x.freshness_score))
        return candidates[0]


# ============================================================================
# FillerSuppressor
# ============================================================================


class FillerSuppressor:
    """Detects and blocks low-quality filler content."""

    def __init__(self) -> None:
        self.generic_patterns = GENERIC_MOTIVATIONAL_PATTERNS
        self.holiday_patterns = EMPTY_HOLIDAY_PATTERNS
        self.ai_slop_phrases = _AI_SLOP_PHRASES
        self.min_quality_score = 8.0  # Out of 16

    def check_content(
        self,
        content_text: str,
        content_type: str,
        business_name: str,
        business_industry: Optional[str] = None,
        media_refs: Optional[List[str]] = None,
    ) -> FillerCheckResult:
        """Analyze content and determine if it is filler.

        Runs all checks:
        1. Generic motivational pattern
        2. Stock photo with no context
        3. Empty holiday post
        4. Quality score estimation
        5. AI slop phrase detection
        6. Brand relevance check
        """
        rejection_reasons: List[str] = []
        improvement_suggestions: List[str] = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        # 1. Generic motivational check.
        if self._is_generic_motivational(content_text):
            rejection_reasons.append(FillerRejectionReason.generic_motivational.value)
            improvement_suggestions.append(
                "Replace generic motivation with a specific tip, result, or story "
                "from your actual business experience."
            )

        # 2. Stock photo check.
        if media_refs and len(media_refs) > 0 and len(content_text.strip()) < 50:
            # Short caption with media — likely stock photo filler.
            text_lower = content_text.lower().strip()
            generic_indicators = [
                "check this out", "photo", "image", "pic", "mood",
                "vibes", "love this", "so good", "amazing",
            ]
            if any(ind in text_lower for ind in generic_indicators) or len(text_lower) < 20:
                rejection_reasons.append(
                    FillerRejectionReason.stock_photo_no_context.value
                )
                improvement_suggestions.append(
                    "Add a meaningful caption that connects the image to your "
                    "business, a specific project, or a client story."
                )

        # 3. Empty holiday check.
        if self._is_empty_holiday(content_text):
            rejection_reasons.append(FillerRejectionReason.empty_holiday.value)
            improvement_suggestions.append(
                "Add value to holiday posts: include a seasonal tip, a special "
                "offer, or a story about what this day means to your business."
            )

        # 4. Quality score check.
        quality_score = self._estimate_quality_score(
            content_text, business_name, business_industry,
        )
        if quality_score < self.min_quality_score:
            rejection_reasons.append(FillerRejectionReason.low_quality_score.value)
            improvement_suggestions.append(
                f"Quality score is {quality_score:.1f}/16 (minimum {self.min_quality_score:.0f}). "
                "Add specific details, numbers, actionable advice, or urgency."
            )

        # 5. AI slop check.
        slop_found = self._check_ai_slop(content_text)
        if slop_found:
            rejection_reasons.append(FillerRejectionReason.ai_slop_detected.value)
            improvement_suggestions.append(
                f"Remove AI slop phrases: {', '.join(slop_found)}. "
                "Rewrite those sentences in plain, direct language."
            )

        # 6. Brand relevance check.
        brand_relevance = self._calculate_brand_relevance(
            content_text, business_name, business_industry,
        )
        if brand_relevance < 0.3:
            rejection_reasons.append(FillerRejectionReason.no_brand_relevance.value)
            improvement_suggestions.append(
                "Content has no connection to your business. Mention your "
                "business name, services, location, or a specific project."
            )

        is_filler = len(rejection_reasons) > 0

        return FillerCheckResult(
            is_filler=is_filler,
            rejection_reasons=rejection_reasons,
            quality_score=quality_score,
            improvement_suggestions=improvement_suggestions,
            brand_relevance_score=brand_relevance,
            checked_at=now_str,
        )

    def _is_generic_motivational(self, text: str) -> bool:
        """Check against known generic motivational patterns."""
        text_lower = text.lower().strip()
        # Remove punctuation and emoji for matching.
        stripped = re.sub(r"[^\w\s]", "", text_lower)
        stripped = re.sub(r"\s+", " ", stripped).strip()

        for pattern in self.generic_patterns:
            if pattern in stripped:
                return True
        return False

    def _is_empty_holiday(self, text: str) -> bool:
        """Check for empty holiday post patterns."""
        # Strip emoji for matching.
        text_clean = re.sub(
            r"[\U0001f300-\U0001f9ff\U00002600-\U000027bf\U0000fe00-\U0000feff]",
            "",
            text,
        ).strip()

        for pattern in self.holiday_patterns:
            if re.match(pattern, text_clean, re.IGNORECASE):
                return True
        return False

    def _estimate_quality_score(
        self,
        text: str,
        business_name: str,
        business_industry: Optional[str],
    ) -> float:
        """Simplified Four U's score estimation on a 0-16 scale.

        Each U is scored 0-4:
        - Unique: mentions business name or specific details (not generic).
        - Useful: contains actionable info, a tip, or an offer.
        - Ultra-specific: has numbers, names, or concrete details.
        - Urgent: has a reason to engage today (deadline, limited, now).
        """
        text_lower = text.lower()
        words = text_lower.split()
        word_count = len(words)

        # --- Unique (0-4) ---
        unique_score = 0.0
        if business_name.lower() in text_lower:
            unique_score += 2.0
        if business_industry and business_industry.lower() in text_lower:
            unique_score += 1.0
        # Specific details: sentences > 10 words, multiple sentences.
        sentences = [s.strip() for s in re.split(r"[.!?]", text) if s.strip()]
        if len(sentences) >= 3:
            unique_score += 1.0
        unique_score = min(unique_score, 4.0)

        # --- Useful (0-4) ---
        useful_score = 0.0
        action_words = [
            "how to", "step", "tip", "call", "book", "schedule", "visit",
            "click", "save", "try", "check", "learn", "discover", "get",
        ]
        for aw in action_words:
            if aw in text_lower:
                useful_score += 1.0
                break
        if any(w in text_lower for w in ["offer", "deal", "discount", "free", "special"]):
            useful_score += 1.5
        if word_count >= 30:
            useful_score += 1.0
        if word_count >= 60:
            useful_score += 0.5
        useful_score = min(useful_score, 4.0)

        # --- Ultra-specific (0-4) ---
        specific_score = 0.0
        # Check for numbers.
        if re.search(r"\d+", text):
            specific_score += 1.5
        # Check for proper nouns (capitalized words not at start of sentence).
        proper_nouns = re.findall(r"(?<!^)(?<!\. )[A-Z][a-z]+", text)
        if len(proper_nouns) >= 2:
            specific_score += 1.0
        # Named tools, products, or locations.
        if any(c in text for c in ["$", "%", "#", "@"]):
            specific_score += 0.5
        if word_count >= 20:
            specific_score += 1.0
        specific_score = min(specific_score, 4.0)

        # --- Urgent (0-4) ---
        urgent_score = 0.0
        urgency_words = [
            "now", "today", "limited", "deadline", "ends", "last chance",
            "hurry", "don't wait", "act fast", "this week", "expire",
            "only", "before", "running out", "spots left",
        ]
        for uw in urgency_words:
            if uw in text_lower:
                urgent_score += 1.5
        if re.search(r"\d{4}-\d{2}-\d{2}", text):
            urgent_score += 1.0
        urgent_score = min(urgent_score, 4.0)

        return unique_score + useful_score + specific_score + urgent_score

    def _check_ai_slop(self, text: str) -> List[str]:
        """Return list of AI slop phrases found in the text."""
        text_lower = text.lower()
        found: List[str] = []
        for phrase in self.ai_slop_phrases:
            if phrase in text_lower:
                found.append(phrase)
        return found

    def _calculate_brand_relevance(
        self,
        text: str,
        business_name: str,
        business_industry: Optional[str],
    ) -> float:
        """Simple keyword-matching brand relevance score (0.0 to 1.0)."""
        text_lower = text.lower()
        score = 0.0
        max_signals = 5.0

        # Business name mention.
        if business_name.lower() in text_lower:
            score += 2.0

        # Industry mention.
        if business_industry and business_industry.lower() in text_lower:
            score += 1.0

        # Service-related keywords.
        service_signals = [
            "service", "client", "customer", "project", "job",
            "team", "work", "results", "appointment", "booking",
            "estimate", "quote", "review",
        ]
        matches = sum(1 for s in service_signals if s in text_lower)
        score += min(matches * 0.5, 1.5)

        # Location mention (any capitalized multi-word that looks like a place).
        if re.search(r"[A-Z][a-z]+(?:\s[A-Z][a-z]+)*", text):
            score += 0.5

        return min(score / max_signals, 1.0)


# ============================================================================
# StalenessDetector
# ============================================================================


class StalenessDetector:
    """Monitors for platform inactivity and generates escalating alerts."""

    def __init__(
        self,
        warning_days: int = 7,
        alert_days: int = 14,
        critical_days: int = 21,
    ) -> None:
        self.warning_days = warning_days
        self.alert_days = alert_days
        self.critical_days = critical_days

    def check_staleness(
        self, platform_health: Dict[str, PlatformHealth],
    ) -> List[StalenessAlert]:
        """Check each platform and generate alerts for staleness."""
        alerts: List[StalenessAlert] = []
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")

        for platform, ph in platform_health.items():
            if not ph.is_active:
                continue

            days = ph.days_since_last_post

            if days >= self.critical_days:
                alerts.append(
                    StalenessAlert(
                        id=generate_stale_alert_id(),
                        platform=platform,
                        days_since_last_post=days,
                        severity="critical",
                        suggested_action=(
                            f"CRITICAL: Platform {platform} has had no activity in "
                            f"{days} days. This actively harms credibility. "
                            "Immediate action required."
                        ),
                        created_at=now_str,
                        acknowledged=False,
                    )
                )
            elif days >= self.alert_days:
                alerts.append(
                    StalenessAlert(
                        id=generate_stale_alert_id(),
                        platform=platform,
                        days_since_last_post=days,
                        severity="alert",
                        suggested_action=(
                            f"Platform {platform} is stale ({days} days since last "
                            "post). Potential customers may think the business is "
                            "inactive. Schedule a post immediately."
                        ),
                        created_at=now_str,
                        acknowledged=False,
                    )
                )
            elif days >= self.warning_days:
                alerts.append(
                    StalenessAlert(
                        id=generate_stale_alert_id(),
                        platform=platform,
                        days_since_last_post=days,
                        severity="warning",
                        suggested_action=(
                            f"Platform {platform} has not been posted to in {days} "
                            "days. Consider scheduling a post."
                        ),
                        created_at=now_str,
                        acknowledged=False,
                    )
                )

        return alerts

    def get_most_urgent(
        self, alerts: List[StalenessAlert],
    ) -> Optional[StalenessAlert]:
        """Return the most severe and oldest alert."""
        if not alerts:
            return None

        severity_order = {"critical": 0, "alert": 1, "warning": 2}
        sorted_alerts = sorted(
            alerts,
            key=lambda a: (
                severity_order.get(a.severity, 3),
                -a.days_since_last_post,
            ),
        )
        return sorted_alerts[0]

    def suggest_recovery_action(self, alert: StalenessAlert) -> str:
        """Suggest a recovery action based on alert severity."""
        if alert.severity == "warning":
            return (
                "Post a proof-of-work or tip post to show the business is "
                "active."
            )
        elif alert.severity == "alert":
            return (
                "Post a behind-the-scenes or proof post immediately, then "
                "schedule 3 posts over the next week to rebuild consistency."
            )
        elif alert.severity == "critical":
            return (
                "Post a 'we're still here' update with a value-add (tip or "
                "offer), then build a weekly posting schedule. Consider a "
                "re-introduction post."
            )
        return "Schedule a post to re-establish presence."
