"""Structured memory layer schemas for the Kai Marketing OS.

Seven memory layers organize raw learnings from the writeback system
(Task 073) into queryable, domain-specific stores:

1. **BusinessFactMemory** -- confirmed facts about the business
   (hours, pricing, staff, certifications).
2. **BrandConstraintMemory** -- brand preferences and anti-patterns
   learned from approvals, rejections, and explicit instructions.
3. **ProofAssetMemory** -- testimonials, case studies, stats, and
   other social proof assets with performance and consent tracking.
4. **ChannelLearningMemory** -- per-channel insights (best times,
   formats, audiences, budget levels) backed by data points.
5. **OfferLearningMemory** -- offer/discount/promotion performance
   with seasonal relevance and audience segment data.
6. **AudienceLearningMemory** -- audience segment insights including
   response patterns, preferred channels, and lifetime value.
7. **CreatorPerformanceMemory** -- creator campaign performance, disclosure
   compliance, usage-rights expiry, and ROAS slices.

Each entry carries :class:`MemoryMetadata` with creation/update
timestamps, contributing learning IDs, confirmation count, staleness
rules, and status.

Storage
-------
All layers are persisted as YAML files under
``workspace/{business_id}/memory/``.  Load and save functions handle
missing files and malformed data gracefully, returning empty instances
rather than raising.

Design
------
- Uses the dataclass + ``SerializableModel`` pattern from
  ``kai/runtime/models.py``.
- Atomic writes via a temporary file and rename.
- No external dependencies beyond the Python standard library (YAML is
  attempted first; JSON is the fallback).
"""

from __future__ import annotations

import json
import logging
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Optional YAML support -- falls back to JSON
# ---------------------------------------------------------------------------

try:
    import yaml  # type: ignore[import-untyped]

    _HAS_YAML = True
except ImportError:
    _HAS_YAML = False


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    """Create *path* and all parents if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _new_id(prefix: str) -> str:
    """Generate a unique ID with the given *prefix*."""
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


def _write_atomic(path: Path, text: str) -> None:
    """Write *text* to *path* atomically via a temp file and rename."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _serialize(payload: Dict[str, Any]) -> str:
    """Serialize *payload* to YAML (preferred) or JSON."""
    if _HAS_YAML:
        return yaml.dump(payload, default_flow_style=False, sort_keys=False, allow_unicode=True)
    return json.dumps(payload, indent=2, sort_keys=False, default=str)


def _deserialize(text: str) -> Dict[str, Any]:
    """Deserialize *text* from YAML or JSON."""
    if _HAS_YAML:
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _days_ago(iso_ts: str, days: int) -> bool:
    """Return True if *iso_ts* is more than *days* in the past."""
    try:
        ts = datetime.fromisoformat(iso_ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        threshold = datetime.now(timezone.utc) - timedelta(days=days)
        return ts < threshold
    except (ValueError, TypeError):
        return True  # treat unparseable timestamps as stale


# ---------------------------------------------------------------------------
# Serializable base (matches kai/runtime/models.py)
# ---------------------------------------------------------------------------


class _SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class MemoryStatus(str, Enum):
    """Lifecycle status of a memory entry."""

    ACTIVE = "active"
    STALE = "stale"
    ARCHIVED = "archived"
    PENDING = "pending"


# ---------------------------------------------------------------------------
# Shared metadata model
# ---------------------------------------------------------------------------


@dataclass
class MemoryMetadata(_SerializableModel):
    """Common metadata attached to every memory entry."""

    created_at: str = ""
    updated_at: str = ""
    source_learning_ids: List[str] = field(default_factory=list)
    confidence: str = "observed"
    confirmation_count: int = 0
    last_confirmed_at: Optional[str] = None
    status: str = MemoryStatus.ACTIVE.value
    staleness_days: int = 90
    notes: Optional[str] = None


# =========================================================================
# Layer 1 -- Business Facts
# =========================================================================


_FACT_CATEGORIES = frozenset({
    "hours", "services", "pricing", "staff", "locations",
    "contact", "equipment", "certifications", "insurance", "other",
})

_FACT_STALENESS: Dict[str, int] = {
    "hours": 30,
    "pricing": 30,
    "certifications": 180,
    "insurance": 180,
}
_FACT_STALENESS_DEFAULT = 90


@dataclass
class BusinessFactEntry(_SerializableModel):
    """A single confirmed fact about the business."""

    fact_id: str = ""
    category: str = "other"
    key: str = ""
    value: Any = None
    previous_value: Optional[Any] = None
    change_date: Optional[str] = None
    source: str = "operator_update"
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)

    def __post_init__(self) -> None:
        if not self.fact_id:
            self.fact_id = _new_id("fact")
        if not self.metadata.created_at:
            self.metadata.created_at = _utc_now()
            self.metadata.updated_at = self.metadata.created_at
        # Apply category-specific staleness
        self.metadata.staleness_days = _FACT_STALENESS.get(
            self.category, _FACT_STALENESS_DEFAULT
        )


@dataclass
class BusinessFactMemory(_SerializableModel):
    """Memory layer: confirmed facts about the business."""

    business_id: str = ""
    facts: List[BusinessFactEntry] = field(default_factory=list)
    last_full_sync: Optional[str] = None

    # -- query methods ---------------------------------------------------

    def get_fact(self, key: str) -> Optional[BusinessFactEntry]:
        """Lookup a fact by its machine-readable *key*."""
        for entry in self.facts:
            if entry.key == key and entry.metadata.status != MemoryStatus.ARCHIVED.value:
                return entry
        return None

    def get_facts_by_category(self, category: str) -> List[BusinessFactEntry]:
        """Return all active facts in the given *category*."""
        return [
            f for f in self.facts
            if f.category == category
            and f.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_stale_facts(self) -> List[BusinessFactEntry]:
        """Return facts that are past their staleness date."""
        stale: List[BusinessFactEntry] = []
        for entry in self.facts:
            if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                continue
            ref_ts = entry.metadata.last_confirmed_at or entry.metadata.updated_at or entry.metadata.created_at
            if _days_ago(ref_ts, entry.metadata.staleness_days):
                stale.append(entry)
        return stale


# =========================================================================
# Layer 2 -- Brand Constraints
# =========================================================================


_CONSTRAINT_TYPES = frozenset({
    "tone_preference", "style_preference", "cta_preference",
    "image_preference", "topic_preference", "formatting_preference",
    "channel_preference",
})


@dataclass
class BrandConstraintEntry(_SerializableModel):
    """A learned brand preference or anti-pattern."""

    constraint_id: str = ""
    constraint_type: str = "style_preference"
    description: str = ""
    rule: str = ""
    positive: bool = True
    strength: int = 1
    source_events: List[str] = field(default_factory=list)
    examples: List[Dict[str, str]] = field(default_factory=list)
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)

    def __post_init__(self) -> None:
        if not self.constraint_id:
            self.constraint_id = _new_id("bc")
        if not self.metadata.created_at:
            self.metadata.created_at = _utc_now()
            self.metadata.updated_at = self.metadata.created_at
        self.metadata.staleness_days = 180


@dataclass
class BrandConstraintMemory(_SerializableModel):
    """Memory layer: brand preferences and negative constraints."""

    business_id: str = ""
    constraints: List[BrandConstraintEntry] = field(default_factory=list)

    # -- query methods ---------------------------------------------------

    def get_constraints_for_content_type(self, content_type: str) -> List[BrandConstraintEntry]:
        """Return constraints whose rule references the given *content_type*."""
        results: List[BrandConstraintEntry] = []
        ct_lower = content_type.lower()
        for c in self.constraints:
            if c.metadata.status == MemoryStatus.ARCHIVED.value:
                continue
            if ct_lower in c.rule.lower() or ct_lower in c.description.lower():
                results.append(c)
        return results

    def get_positive_preferences(self) -> List[BrandConstraintEntry]:
        """Return constraints the business *does* want."""
        return [
            c for c in self.constraints
            if c.positive and c.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_negative_constraints(self) -> List[BrandConstraintEntry]:
        """Return things the business wants to *avoid*."""
        return [
            c for c in self.constraints
            if not c.positive and c.metadata.status != MemoryStatus.ARCHIVED.value
        ]


# =========================================================================
# Layer 3 -- Proof Assets
# =========================================================================


_ASSET_TYPES = frozenset({
    "testimonial", "case_study", "before_after", "certification",
    "award", "media_mention", "statistic", "review_highlight",
})

_PROOF_STALENESS: Dict[str, int] = {
    "testimonial": 365,
    "statistic": 180,
    "certification": 9999,  # never
    "award": 9999,
}
_PROOF_STALENESS_DEFAULT = 365


@dataclass
class ProofAssetEntry(_SerializableModel):
    """A social proof asset with consent and performance tracking."""

    asset_id: str = ""
    asset_type: str = "testimonial"
    content: str = ""
    source: str = ""
    date_collected: str = ""
    performance_data: Dict[str, Any] = field(default_factory=lambda: {
        "times_used": 0,
        "engagement_rate": 0.0,
        "conversion_lift": 0.0,
        "best_placement": "",
    })
    approved_for: List[str] = field(default_factory=list)
    consent_status: str = "pending"
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)

    def __post_init__(self) -> None:
        if not self.asset_id:
            self.asset_id = _new_id("proof")
        if not self.date_collected:
            self.date_collected = _utc_now()
        if not self.metadata.created_at:
            self.metadata.created_at = _utc_now()
            self.metadata.updated_at = self.metadata.created_at
        self.metadata.staleness_days = _PROOF_STALENESS.get(
            self.asset_type, _PROOF_STALENESS_DEFAULT
        )


@dataclass
class ProofAssetMemory(_SerializableModel):
    """Memory layer: social proof assets."""

    business_id: str = ""
    assets: List[ProofAssetEntry] = field(default_factory=list)

    # -- query methods ---------------------------------------------------

    def get_best_performing(self, limit: int = 5) -> List[ProofAssetEntry]:
        """Return the top *limit* assets sorted by engagement and conversion."""
        active = [
            a for a in self.assets
            if a.metadata.status != MemoryStatus.ARCHIVED.value
        ]

        def _score(asset: ProofAssetEntry) -> float:
            perf = asset.performance_data
            engagement = float(perf.get("engagement_rate", 0.0))
            conversion = float(perf.get("conversion_lift", 0.0))
            usage = int(perf.get("times_used", 0))
            return (conversion * 2.0) + engagement + (usage * 0.1)

        active.sort(key=_score, reverse=True)
        return active[:limit]

    def get_by_type(self, asset_type: str) -> List[ProofAssetEntry]:
        """Return all active assets of the given *asset_type*."""
        return [
            a for a in self.assets
            if a.asset_type == asset_type
            and a.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_approved_for_content_type(self, content_type: str) -> List[ProofAssetEntry]:
        """Return assets approved for the given *content_type*."""
        ct_lower = content_type.lower()
        return [
            a for a in self.assets
            if ct_lower in [x.lower() for x in a.approved_for]
            and a.metadata.status != MemoryStatus.ARCHIVED.value
        ]


# =========================================================================
# Layer 4 -- Channel Learnings
# =========================================================================


_CHANNEL_NAMES = frozenset({
    "google_ads", "meta_ads", "email", "social_facebook",
    "social_instagram", "social_linkedin", "social_tiktok",
    "organic_search", "gbp",
})

_INSIGHT_TYPES = frozenset({
    "best_posting_time", "best_ad_format", "best_audience_segment",
    "best_creative_type", "best_subject_line_pattern",
    "optimal_frequency", "optimal_budget", "platform_algorithm_note",
})


@dataclass
class ChannelLearningEntry(_SerializableModel):
    """A single per-channel insight backed by data points."""

    learning_id: str = ""
    channel: str = ""
    insight_type: str = ""
    insight: str = ""
    data_points: int = 0
    effect_size: Optional[float] = None
    time_period: str = ""
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)

    def __post_init__(self) -> None:
        if not self.learning_id:
            self.learning_id = _new_id("chl")
        if not self.metadata.created_at:
            self.metadata.created_at = _utc_now()
            self.metadata.updated_at = self.metadata.created_at
        self.metadata.staleness_days = 90


@dataclass
class ChannelLearningMemory(_SerializableModel):
    """Memory layer: per-channel performance insights."""

    business_id: str = ""
    learnings: List[ChannelLearningEntry] = field(default_factory=list)

    # -- query methods ---------------------------------------------------

    def get_learnings_for_channel(self, channel: str) -> List[ChannelLearningEntry]:
        """Return all active learnings for the given *channel*."""
        return [
            l for l in self.learnings
            if l.channel == channel
            and l.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_learnings_by_type(self, insight_type: str) -> List[ChannelLearningEntry]:
        """Return all active learnings of the given *insight_type*."""
        return [
            l for l in self.learnings
            if l.insight_type == insight_type
            and l.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_strongest_insights(self, min_data_points: int = 5) -> List[ChannelLearningEntry]:
        """Return insights supported by at least *min_data_points* data points."""
        return [
            l for l in self.learnings
            if l.data_points >= min_data_points
            and l.metadata.status != MemoryStatus.ARCHIVED.value
        ]


# =========================================================================
# Layer 5 -- Offer Learnings
# =========================================================================


_OFFER_TYPES = frozenset({
    "discount", "bundle", "free_consultation", "guarantee",
    "urgency", "seasonal", "loyalty", "referral", "financing",
})


@dataclass
class OfferLearningEntry(_SerializableModel):
    """A single offer/promotion performance record."""

    learning_id: str = ""
    offer_type: str = ""
    offer_description: str = ""
    channel: str = ""
    conversion_rate: Optional[float] = None
    revenue_impact: Optional[float] = None
    cost: Optional[float] = None
    net_impact: Optional[float] = None
    time_period: str = ""
    seasonal_relevance: Optional[str] = None
    audience_segment: Optional[str] = None
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)

    def __post_init__(self) -> None:
        if not self.learning_id:
            self.learning_id = _new_id("ofl")
        if not self.metadata.created_at:
            self.metadata.created_at = _utc_now()
            self.metadata.updated_at = self.metadata.created_at
        self.metadata.staleness_days = 180
        # Auto-compute net_impact if both sides are present
        if self.net_impact is None and self.revenue_impact is not None and self.cost is not None:
            self.net_impact = self.revenue_impact - self.cost


@dataclass
class OfferLearningMemory(_SerializableModel):
    """Memory layer: offer and promotion performance insights."""

    business_id: str = ""
    learnings: List[OfferLearningEntry] = field(default_factory=list)

    # -- query methods ---------------------------------------------------

    def get_best_offers(self, limit: int = 5) -> List[OfferLearningEntry]:
        """Return the top *limit* offers sorted by net_impact descending."""
        active = [
            l for l in self.learnings
            if l.metadata.status != MemoryStatus.ARCHIVED.value
        ]
        active.sort(key=lambda o: o.net_impact if o.net_impact is not None else float("-inf"), reverse=True)
        return active[:limit]

    def get_seasonal_offers(self, season: str) -> List[OfferLearningEntry]:
        """Return offers relevant to the given *season*."""
        s_lower = season.lower()
        return [
            l for l in self.learnings
            if l.seasonal_relevance is not None
            and l.seasonal_relevance.lower() == s_lower
            and l.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_offers_for_channel(self, channel: str) -> List[OfferLearningEntry]:
        """Return offer learnings for the given *channel*."""
        return [
            l for l in self.learnings
            if l.channel == channel
            and l.metadata.status != MemoryStatus.ARCHIVED.value
        ]


# =========================================================================
# Layer 6 -- Audience Learnings
# =========================================================================


_AUDIENCE_TYPES = frozenset({
    "demographic", "behavioral", "psychographic", "persona_match",
})


@dataclass
class AudienceLearningEntry(_SerializableModel):
    """A single audience segment insight."""

    learning_id: str = ""
    audience_type: str = "behavioral"
    segment_description: str = ""
    insight: str = ""
    response_to_message_type: Optional[str] = None
    preferred_channel: Optional[str] = None
    conversion_rate: Optional[float] = None
    ltv_estimate: Optional[float] = None
    data_points: int = 0
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)

    def __post_init__(self) -> None:
        if not self.learning_id:
            self.learning_id = _new_id("aud")
        if not self.metadata.created_at:
            self.metadata.created_at = _utc_now()
            self.metadata.updated_at = self.metadata.created_at
        self.metadata.staleness_days = 120


@dataclass
class AudienceLearningMemory(_SerializableModel):
    """Memory layer: audience segment insights."""

    business_id: str = ""
    learnings: List[AudienceLearningEntry] = field(default_factory=list)

    # -- query methods ---------------------------------------------------

    def get_learnings_by_type(self, audience_type: str) -> List[AudienceLearningEntry]:
        """Return active learnings for the given *audience_type*."""
        return [
            l for l in self.learnings
            if l.audience_type == audience_type
            and l.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_highest_value_segments(self, limit: int = 5) -> List[AudienceLearningEntry]:
        """Return the highest-LTV audience segments."""
        active = [
            l for l in self.learnings
            if l.metadata.status != MemoryStatus.ARCHIVED.value
        ]
        active.sort(
            key=lambda a: a.ltv_estimate if a.ltv_estimate is not None else float("-inf"),
            reverse=True,
        )
        return active[:limit]


# =========================================================================
# Layer 7 -- Creator Performance Learnings
# =========================================================================


@dataclass
class CreatorPerformanceEntry(_SerializableModel):
    """A creator-commerce performance record for one creator/campaign slice."""

    entry_id: str = ""
    creator_id: str = ""
    creator_name: Optional[str] = None
    platform: str = ""
    campaign_id: Optional[str] = None
    content_asset_id: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    spend_usd: Optional[float] = None
    attributed_revenue_usd: Optional[float] = None
    attributed_orders: Optional[int] = None
    affiliate_clicks: Optional[int] = None
    affiliate_conversions: Optional[int] = None
    gmv_usd: Optional[float] = None
    disclosure_compliant: bool = False
    usage_rights_expires_at: Optional[str] = None
    whitelisting_enabled: bool = False
    metadata: MemoryMetadata = field(default_factory=MemoryMetadata)

    def __post_init__(self) -> None:
        if not self.entry_id:
            self.entry_id = _new_id("crp")
        if not self.metadata.created_at:
            self.metadata.created_at = _utc_now()
            self.metadata.updated_at = self.metadata.created_at
        self.metadata.staleness_days = 60

    @property
    def roas(self) -> Optional[float]:
        """Return return-on-ad-spend when spend and revenue are available."""
        if self.spend_usd is None or self.attributed_revenue_usd is None:
            return None
        if self.spend_usd <= 0:
            return None
        return float(self.attributed_revenue_usd) / float(self.spend_usd)


@dataclass
class CreatorPerformanceMemory(_SerializableModel):
    """Memory layer: creator-commerce campaign and compliance performance."""

    business_id: str = ""
    entries: List[CreatorPerformanceEntry] = field(default_factory=list)

    def get_non_compliant_disclosures(self) -> List[CreatorPerformanceEntry]:
        """Return active entries where disclosure compliance is false."""
        return [
            entry for entry in self.entries
            if not entry.disclosure_compliant
            and entry.metadata.status != MemoryStatus.ARCHIVED.value
        ]

    def get_rights_expiring_within(self, days: int = 14) -> List[CreatorPerformanceEntry]:
        """Return active entries with usage rights expiring within *days*."""
        expiring: List[CreatorPerformanceEntry] = []
        now = datetime.now(timezone.utc)
        for entry in self.entries:
            if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                continue
            if not entry.usage_rights_expires_at:
                continue
            try:
                expiry = datetime.fromisoformat(entry.usage_rights_expires_at)
                if expiry.tzinfo is None:
                    expiry = expiry.replace(tzinfo=timezone.utc)
            except (TypeError, ValueError):
                continue
            delta = expiry - now
            if timedelta(0) <= delta <= timedelta(days=days):
                expiring.append(entry)
        return expiring

    def get_top_creators_by_roas(self, limit: int = 5) -> List[CreatorPerformanceEntry]:
        """Return the highest-ROAS creator slices with available spend/revenue data."""
        scored = [
            entry for entry in self.entries
            if entry.metadata.status != MemoryStatus.ARCHIVED.value
            and entry.roas is not None
        ]
        scored.sort(key=lambda entry: entry.roas or 0.0, reverse=True)
        return scored[:limit]


# =========================================================================
# Layer name -> model class registry
# =========================================================================


_LAYER_REGISTRY: Dict[str, type] = {
    "business_facts": BusinessFactMemory,
    "brand_constraints": BrandConstraintMemory,
    "proof_assets": ProofAssetMemory,
    "channel_learnings": ChannelLearningMemory,
    "offer_learnings": OfferLearningMemory,
    "audience_learnings": AudienceLearningMemory,
    "creator_performance": CreatorPerformanceMemory,
}

_LAYER_LIST_FIELD: Dict[str, str] = {
    "business_facts": "facts",
    "brand_constraints": "constraints",
    "proof_assets": "assets",
    "channel_learnings": "learnings",
    "offer_learnings": "learnings",
    "audience_learnings": "learnings",
    "creator_performance": "entries",
}

_LAYER_ENTRY_CLASS: Dict[str, type] = {
    "business_facts": BusinessFactEntry,
    "brand_constraints": BrandConstraintEntry,
    "proof_assets": ProofAssetEntry,
    "channel_learnings": ChannelLearningEntry,
    "offer_learnings": OfferLearningEntry,
    "audience_learnings": AudienceLearningEntry,
    "creator_performance": CreatorPerformanceEntry,
}


def _storage_path(business_id: str, layer_name: str, base_dir: str) -> Path:
    """Return the on-disk path for a memory layer.

    Pattern: ``{base_dir}/{business_id}/memory/{layer_name}.yaml``
    """
    ext = "yaml" if _HAS_YAML else "json"
    return Path(base_dir) / business_id / "memory" / f"{layer_name}.{ext}"


# =========================================================================
# Reconstruction helpers
# =========================================================================


def _reconstruct_metadata(raw: Dict[str, Any]) -> MemoryMetadata:
    """Build a ``MemoryMetadata`` from a raw dict, tolerating missing keys."""
    return MemoryMetadata(
        created_at=raw.get("created_at", ""),
        updated_at=raw.get("updated_at", ""),
        source_learning_ids=raw.get("source_learning_ids", []),
        confidence=raw.get("confidence", "observed"),
        confirmation_count=int(raw.get("confirmation_count", 0)),
        last_confirmed_at=raw.get("last_confirmed_at"),
        status=raw.get("status", MemoryStatus.ACTIVE.value),
        staleness_days=int(raw.get("staleness_days", 90)),
        notes=raw.get("notes"),
    )


def _reconstruct_entry(entry_cls: type, raw: Dict[str, Any]) -> Any:
    """Reconstruct an entry dataclass from a raw dict.

    Handles the nested ``metadata`` field specially and silently
    ignores unknown keys so that older/newer schema versions do not
    crash on load.
    """
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(entry_cls)}
    kwargs: Dict[str, Any] = {}
    for k, v in raw.items():
        if k not in field_names:
            continue
        if k == "metadata" and isinstance(v, dict):
            kwargs[k] = _reconstruct_metadata(v)
        else:
            kwargs[k] = v
    return entry_cls(**kwargs)


def _reconstruct_memory(layer_cls: type, entry_cls: type, list_field: str, raw: Dict[str, Any], business_id: str) -> Any:
    """Reconstruct a memory layer model from a raw dict."""
    entries_raw = raw.get(list_field, [])
    entries = [_reconstruct_entry(entry_cls, e) for e in entries_raw if isinstance(e, dict)]

    kwargs: Dict[str, Any] = {"business_id": business_id, list_field: entries}

    # Layer-specific top-level fields
    if layer_cls is BusinessFactMemory:
        kwargs["last_full_sync"] = raw.get("last_full_sync")

    return layer_cls(**kwargs)


# =========================================================================
# Public API -- load / save / stale check
# =========================================================================


def load_memory_layer(business_id: str, layer_name: str, base_dir: str) -> Any:
    """Load a memory layer from disk.

    Parameters
    ----------
    business_id : str
        Business identifier.
    layer_name : str
        One of: ``business_facts``, ``brand_constraints``, ``proof_assets``,
        ``channel_learnings``, ``offer_learnings``, ``audience_learnings``,
        ``creator_performance``.
    base_dir : str
        Root workspace directory (layers live under
        ``{base_dir}/{business_id}/memory/``).

    Returns
    -------
    The appropriate memory model instance.  If the file does not exist
    or contains malformed data, an empty instance is returned and a
    warning is logged.
    """
    if layer_name not in _LAYER_REGISTRY:
        raise ValueError(
            f"Unknown memory layer {layer_name!r}. "
            f"Must be one of: {', '.join(sorted(_LAYER_REGISTRY))}"
        )

    layer_cls = _LAYER_REGISTRY[layer_name]
    entry_cls = _LAYER_ENTRY_CLASS[layer_name]
    list_field = _LAYER_LIST_FIELD[layer_name]

    # Try both .yaml and .json extensions
    yaml_path = Path(base_dir) / business_id / "memory" / f"{layer_name}.yaml"
    json_path = Path(base_dir) / business_id / "memory" / f"{layer_name}.json"

    file_path: Optional[Path] = None
    if yaml_path.exists():
        file_path = yaml_path
    elif json_path.exists():
        file_path = json_path

    if file_path is None:
        logger.debug("Memory layer %s not found for %s -- returning empty", layer_name, business_id)
        return layer_cls(business_id=business_id)

    try:
        raw_text = file_path.read_text(encoding="utf-8")
        raw = _deserialize(raw_text)
        if not isinstance(raw, dict):
            logger.warning("Memory layer %s for %s is not a dict -- returning empty", layer_name, business_id)
            return layer_cls(business_id=business_id)
        return _reconstruct_memory(layer_cls, entry_cls, list_field, raw, business_id)
    except Exception as exc:
        logger.warning("Failed to load memory layer %s for %s: %s -- returning empty", layer_name, business_id, exc)
        return layer_cls(business_id=business_id)


def save_memory_layer(memory_layer: Any, base_dir: str) -> None:
    """Save a memory layer to its YAML (or JSON) file on disk.

    Parameters
    ----------
    memory_layer
        An instance of one of the six memory layer models.
    base_dir : str
        Root workspace directory.

    Uses the atomic write pattern (write to temp, then rename) to avoid
    partial writes on crash.
    """
    business_id: str = getattr(memory_layer, "business_id", "")
    if not business_id:
        raise ValueError("memory_layer must have a non-empty business_id")

    # Determine layer name from type
    layer_name: Optional[str] = None
    for name, cls in _LAYER_REGISTRY.items():
        if isinstance(memory_layer, cls):
            layer_name = name
            break

    if layer_name is None:
        raise TypeError(
            f"Unknown memory layer type {type(memory_layer).__name__}. "
            f"Expected one of: {', '.join(c.__name__ for c in _LAYER_REGISTRY.values())}"
        )

    file_path = _storage_path(business_id, layer_name, base_dir)
    _ensure_dir(file_path.parent)

    payload = memory_layer.model_dump()
    text = _serialize(payload)
    _write_atomic(file_path, text)


def get_all_stale_entries(business_id: str, base_dir: str) -> Dict[str, List[Any]]:
    """Check all memory layers for stale entries.

    Parameters
    ----------
    business_id : str
        Business identifier.
    base_dir : str
        Root workspace directory.

    Returns
    -------
    dict
        Mapping of ``{layer_name: [stale_entries]}``.  Only layers with
        at least one stale entry are included.
    """
    stale_map: Dict[str, List[Any]] = {}

    for layer_name in _LAYER_REGISTRY:
        layer = load_memory_layer(business_id, layer_name, base_dir)
        list_field = _LAYER_LIST_FIELD[layer_name]
        entries: List[Any] = getattr(layer, list_field, [])

        stale_entries: List[Any] = []
        for entry in entries:
            meta: Optional[MemoryMetadata] = getattr(entry, "metadata", None)
            if meta is None:
                continue
            if meta.status == MemoryStatus.ARCHIVED.value:
                continue
            ref_ts = meta.last_confirmed_at or meta.updated_at or meta.created_at
            if _days_ago(ref_ts, meta.staleness_days):
                stale_entries.append(entry)

        if stale_entries:
            stale_map[layer_name] = stale_entries

    return stale_map
