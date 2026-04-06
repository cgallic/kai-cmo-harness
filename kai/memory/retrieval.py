"""Context-aware memory retrieval for the Kai Marketing OS.

The read path of Kai's persistent learning system.  When the proposal
engine generates actions, the copy engine writes headlines, the approval
router estimates risk, or the watcher system evaluates findings, this
module surfaces the most relevant accumulated learnings.

Five context-specific retrieval methods pull from all six memory layers
(business facts, brand constraints, proof assets, channel learnings,
offer learnings, audience learnings), rank by relevance, filter by
staleness and confidence, and compile the results into a
:class:`MemoryBrief` that any downstream consumer can use without
understanding the underlying storage layout.

Design
------
- Uses the dataclass + ``SerializableModel`` pattern from
  ``kai/runtime/models.py``.
- Relies on ``kai/memory/schemas.py`` for layer loading and models.
- No external dependencies beyond the Python standard library.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from kai.memory.schemas import (
    AudienceLearningEntry,
    AudienceLearningMemory,
    BrandConstraintEntry,
    BrandConstraintMemory,
    BusinessFactEntry,
    BusinessFactMemory,
    ChannelLearningEntry,
    ChannelLearningMemory,
    MemoryMetadata,
    MemoryStatus,
    OfferLearningEntry,
    OfferLearningMemory,
    ProofAssetEntry,
    ProofAssetMemory,
    load_memory_layer,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _age_in_days(iso_ts: str) -> int:
    """Return the number of whole days between *iso_ts* and now.

    Returns ``9999`` if the timestamp is unparseable so that unparseable
    entries are treated as very old rather than crashing.
    """
    try:
        ts = datetime.fromisoformat(iso_ts)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        delta = datetime.now(timezone.utc) - ts
        return max(0, delta.days)
    except (ValueError, TypeError):
        return 9999


def _is_stale(meta: MemoryMetadata) -> bool:
    """Return True if an entry's metadata indicates staleness."""
    if meta.status == MemoryStatus.ARCHIVED.value:
        return True
    ref_ts = meta.last_confirmed_at or meta.updated_at or meta.created_at
    if not ref_ts:
        return True
    return _age_in_days(ref_ts) > meta.staleness_days


# ---------------------------------------------------------------------------
# Confidence hierarchy
# ---------------------------------------------------------------------------

_CONFIDENCE_RANK: Dict[str, int] = {
    "confirmed": 4,
    "observed": 3,
    "inferred": 2,
    "speculative": 1,
}

_CONFIDENCE_RELEVANCE: Dict[str, float] = {
    "confirmed": 1.0,
    "observed": 0.7,
    "inferred": 0.4,
    "speculative": 0.2,
}


# ---------------------------------------------------------------------------
# Serializable base (matches kai/runtime/models.py)
# ---------------------------------------------------------------------------


class _SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Models
# ---------------------------------------------------------------------------


@dataclass
class RetrievalContext(_SerializableModel):
    """Describes what the system is currently doing so retrieval can be
    targeted to the right learnings."""

    context_type: str = "proposal"
    business_id: str = ""
    channel: Optional[str] = None
    content_type: Optional[str] = None
    action_type: Optional[str] = None
    audience_segment: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    max_results: int = 10
    min_confidence: str = "inferred"
    include_stale: bool = False


@dataclass
class RetrievedMemory(_SerializableModel):
    """A single memory entry that has been scored and annotated for the
    current retrieval context."""

    source_layer: str = ""
    entry_id: str = ""
    relevance_score: float = 0.0
    content: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    confidence: str = ""
    age_days: int = 0
    is_stale: bool = False
    usage_hint: str = ""


@dataclass
class MemoryBrief(_SerializableModel):
    """The complete retrieval result: a context-specific digest of all
    relevant memories for a downstream consumer."""

    business_id: str = ""
    context: RetrievalContext = field(default_factory=RetrievalContext)
    retrieved_at: str = ""
    total_entries_searched: int = 0
    entries_returned: int = 0
    memories: List[RetrievedMemory] = field(default_factory=list)
    key_constraints: List[str] = field(default_factory=list)
    winning_patterns: List[str] = field(default_factory=list)
    things_to_avoid: List[str] = field(default_factory=list)
    available_proof_assets: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Layer-to-RetrievedMemory adapters
# ---------------------------------------------------------------------------


def _adapt_business_fact(entry: BusinessFactEntry) -> RetrievedMemory:
    """Convert a BusinessFactEntry into a RetrievedMemory."""
    return RetrievedMemory(
        source_layer="business_facts",
        entry_id=entry.fact_id,
        content={
            "category": entry.category,
            "key": entry.key,
            "value": entry.value,
            "previous_value": entry.previous_value,
            "source": entry.source,
        },
        summary=f"{entry.category}/{entry.key}: {entry.value}",
        confidence=entry.metadata.confidence,
        age_days=_age_in_days(entry.metadata.updated_at or entry.metadata.created_at),
        is_stale=_is_stale(entry.metadata),
    )


def _adapt_brand_constraint(entry: BrandConstraintEntry) -> RetrievedMemory:
    """Convert a BrandConstraintEntry into a RetrievedMemory."""
    polarity = "Prefer" if entry.positive else "Avoid"
    return RetrievedMemory(
        source_layer="brand_constraints",
        entry_id=entry.constraint_id,
        content={
            "constraint_type": entry.constraint_type,
            "description": entry.description,
            "rule": entry.rule,
            "positive": entry.positive,
            "strength": entry.strength,
            "examples": entry.examples,
        },
        summary=f"{polarity}: {entry.description}" if entry.description else f"{polarity}: {entry.rule}",
        confidence=entry.metadata.confidence,
        age_days=_age_in_days(entry.metadata.updated_at or entry.metadata.created_at),
        is_stale=_is_stale(entry.metadata),
    )


def _adapt_proof_asset(entry: ProofAssetEntry) -> RetrievedMemory:
    """Convert a ProofAssetEntry into a RetrievedMemory."""
    perf = entry.performance_data
    times_used = perf.get("times_used", 0)
    engagement = perf.get("engagement_rate", 0.0)
    summary_parts = [f"{entry.asset_type}"]
    if entry.source:
        summary_parts.append(f"from {entry.source}")
    if times_used:
        summary_parts.append(f"used {times_used}x")
    if engagement:
        summary_parts.append(f"{engagement:.1%} engagement")

    return RetrievedMemory(
        source_layer="proof_assets",
        entry_id=entry.asset_id,
        content={
            "asset_type": entry.asset_type,
            "content": entry.content,
            "source": entry.source,
            "approved_for": entry.approved_for,
            "consent_status": entry.consent_status,
            "performance_data": entry.performance_data,
        },
        summary=" — ".join(summary_parts),
        confidence=entry.metadata.confidence,
        age_days=_age_in_days(entry.metadata.updated_at or entry.metadata.created_at),
        is_stale=_is_stale(entry.metadata),
    )


def _adapt_channel_learning(entry: ChannelLearningEntry) -> RetrievedMemory:
    """Convert a ChannelLearningEntry into a RetrievedMemory."""
    effect_str = f" ({entry.effect_size:+.1f}x)" if entry.effect_size is not None else ""
    return RetrievedMemory(
        source_layer="channel_learnings",
        entry_id=entry.learning_id,
        content={
            "channel": entry.channel,
            "insight_type": entry.insight_type,
            "insight": entry.insight,
            "data_points": entry.data_points,
            "effect_size": entry.effect_size,
            "time_period": entry.time_period,
        },
        summary=f"[{entry.channel}] {entry.insight}{effect_str}",
        confidence=entry.metadata.confidence,
        age_days=_age_in_days(entry.metadata.updated_at or entry.metadata.created_at),
        is_stale=_is_stale(entry.metadata),
    )


def _adapt_offer_learning(entry: OfferLearningEntry) -> RetrievedMemory:
    """Convert an OfferLearningEntry into a RetrievedMemory."""
    summary_parts = [f"{entry.offer_type}: {entry.offer_description}"]
    if entry.conversion_rate is not None:
        summary_parts.append(f"{entry.conversion_rate:.1%} CVR")
    if entry.net_impact is not None:
        sign = "+" if entry.net_impact >= 0 else ""
        summary_parts.append(f"{sign}${entry.net_impact:.0f} net")

    return RetrievedMemory(
        source_layer="offer_learnings",
        entry_id=entry.learning_id,
        content={
            "offer_type": entry.offer_type,
            "offer_description": entry.offer_description,
            "channel": entry.channel,
            "conversion_rate": entry.conversion_rate,
            "revenue_impact": entry.revenue_impact,
            "cost": entry.cost,
            "net_impact": entry.net_impact,
            "seasonal_relevance": entry.seasonal_relevance,
            "audience_segment": entry.audience_segment,
        },
        summary=" — ".join(summary_parts),
        confidence=entry.metadata.confidence,
        age_days=_age_in_days(entry.metadata.updated_at or entry.metadata.created_at),
        is_stale=_is_stale(entry.metadata),
    )


def _adapt_audience_learning(entry: AudienceLearningEntry) -> RetrievedMemory:
    """Convert an AudienceLearningEntry into a RetrievedMemory."""
    summary_parts = [entry.segment_description or entry.audience_type]
    if entry.insight:
        summary_parts.append(entry.insight)

    return RetrievedMemory(
        source_layer="audience_learnings",
        entry_id=entry.learning_id,
        content={
            "audience_type": entry.audience_type,
            "segment_description": entry.segment_description,
            "insight": entry.insight,
            "response_to_message_type": entry.response_to_message_type,
            "preferred_channel": entry.preferred_channel,
            "conversion_rate": entry.conversion_rate,
            "ltv_estimate": entry.ltv_estimate,
            "data_points": entry.data_points,
        },
        summary=" — ".join(summary_parts),
        confidence=entry.metadata.confidence,
        age_days=_age_in_days(entry.metadata.updated_at or entry.metadata.created_at),
        is_stale=_is_stale(entry.metadata),
    )


# ---------------------------------------------------------------------------
# MemoryRetriever
# ---------------------------------------------------------------------------


class MemoryRetriever:
    """Context-aware memory retrieval engine.

    Loads all six memory layers for a business, filters and ranks entries
    by relevance to the current retrieval context, and compiles a
    :class:`MemoryBrief` that downstream consumers (proposal engine,
    creative engine, approval router, watcher system) can use directly.

    Parameters
    ----------
    base_dir:
        Root workspace directory.  Memory layers live under
        ``{base_dir}/{business_id}/memory/``.
    """

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        # Session cache: avoids re-reading the same layers within one
        # retrieval session (multiple retrieve calls on the same instance).
        self._layer_cache: Dict[str, Dict[str, Any]] = {}

    # ------------------------------------------------------------------
    # Public entry points
    # ------------------------------------------------------------------

    def retrieve(self, context: RetrievalContext) -> MemoryBrief:
        """Main entry point: dispatch to the context-specific method.

        Always includes brand constraints regardless of context type.
        """
        dispatch = {
            "proposal": self._retrieve_proposal,
            "creative": self._retrieve_creative,
            "channel_selection": self._retrieve_channel_selection,
            "approval": self._retrieve_approval,
            "watcher": self._retrieve_watcher,
            "audit": self._retrieve_audit,
        }

        handler = dispatch.get(context.context_type, self._retrieve_generic)
        return handler(context)

    def retrieve_for_proposal(
        self,
        business_id: str,
        action_type: str,
        channel: str,
    ) -> MemoryBrief:
        """Retrieve memories relevant to generating a proposal.

        Surfaces past actions that performed well (do this again), past
        actions that performed poorly (avoid this), operator approval
        patterns, channel learnings, and relevant business facts.
        """
        context = RetrievalContext(
            context_type="proposal",
            business_id=business_id,
            channel=channel,
            action_type=action_type,
            tags=["proposal", action_type, channel],
        )
        return self.retrieve(context)

    def retrieve_for_creative(
        self,
        business_id: str,
        content_type: str,
        channel: str,
        audience: Optional[str] = None,
    ) -> MemoryBrief:
        """Retrieve memories relevant to generating creative content.

        Surfaces brand voice/tone preferences, best-performing creative
        for this content_type + channel, approved proof assets, audience
        insights, and offer learnings.
        """
        tags = ["creative", content_type, channel]
        if audience:
            tags.append(audience)
        context = RetrievalContext(
            context_type="creative",
            business_id=business_id,
            channel=channel,
            content_type=content_type,
            audience_segment=audience,
            tags=tags,
        )
        return self.retrieve(context)

    def retrieve_for_channel_selection(
        self,
        business_id: str,
    ) -> MemoryBrief:
        """Retrieve memories for deciding which channels to use.

        Surfaces channel performance data, audience channel preferences,
        and budget efficiency by channel.
        """
        context = RetrievalContext(
            context_type="channel_selection",
            business_id=business_id,
            tags=["channel_selection"],
        )
        return self.retrieve(context)

    def retrieve_for_approval(
        self,
        business_id: str,
        action_type: str,
        risk_tier: str,
    ) -> MemoryBrief:
        """Retrieve memories for predicting operator approval behavior.

        Surfaces past approval/rejection patterns, operator preferences
        that affect approval, and compliance constraints violated before.
        """
        context = RetrievalContext(
            context_type="approval",
            business_id=business_id,
            action_type=action_type,
            tags=["approval", action_type, risk_tier],
        )
        return self.retrieve(context)

    def retrieve_for_watcher(
        self,
        business_id: str,
        watcher_name: str,
    ) -> MemoryBrief:
        """Retrieve memories for reducing watcher false positives.

        Surfaces past watcher findings that were dismissed (suppress
        similar), past findings that led to action (prioritize similar),
        and business facts that affect thresholds.
        """
        context = RetrievalContext(
            context_type="watcher",
            business_id=business_id,
            tags=["watcher", watcher_name],
        )
        return self.retrieve(context)

    # ------------------------------------------------------------------
    # Layer loading with session cache
    # ------------------------------------------------------------------

    def _load_memory_layers(self, business_id: str) -> Dict[str, Any]:
        """Load all six memory layers for a business, caching per session.

        Returns a dict of ``{layer_name: memory_layer_object}``.
        """
        if business_id in self._layer_cache:
            return self._layer_cache[business_id]

        layer_names = [
            "business_facts",
            "brand_constraints",
            "proof_assets",
            "channel_learnings",
            "offer_learnings",
            "audience_learnings",
        ]

        layers: Dict[str, Any] = {}
        for name in layer_names:
            try:
                layers[name] = load_memory_layer(business_id, name, self.base_dir)
            except Exception as exc:
                logger.warning(
                    "Failed to load memory layer %s for %s: %s",
                    name, business_id, exc,
                )
                layers[name] = None

        self._layer_cache[business_id] = layers
        return layers

    def clear_cache(self) -> None:
        """Clear the session layer cache, forcing re-reads on next retrieve."""
        self._layer_cache.clear()

    # ------------------------------------------------------------------
    # Ranking, filtering, and hints
    # ------------------------------------------------------------------

    def _rank_by_relevance(
        self,
        entries: List[RetrievedMemory],
        context: RetrievalContext,
    ) -> List[RetrievedMemory]:
        """Rank entries by relevance to the current context.

        Ranking factors (combined via weighted average):

        - **Confidence** (40%): confirmed=1.0, observed=0.7,
          inferred=0.4, speculative=0.2
        - **Recency** (30%): ``max(0.1, 1.0 - (age_days / 365))``
        - **Context match** (30%): +0.3 per matching dimension
          (channel, content_type, tags), capped at 1.0; brand
          constraint strength adds up to +0.5
        """
        context_tags_lower = {t.lower() for t in context.tags} if context.tags else set()

        for entry in entries:
            # Factor 1: confidence
            confidence_score = _CONFIDENCE_RELEVANCE.get(entry.confidence, 0.2)

            # Factor 2: recency
            recency_score = max(0.1, 1.0 - (entry.age_days / 365.0))

            # Factor 3: context match
            match_score = 0.0

            # Channel match
            if context.channel and entry.content:
                entry_channel = entry.content.get("channel", "")
                if entry_channel and isinstance(entry_channel, str):
                    if entry_channel.lower() == context.channel.lower():
                        match_score += 0.3

            # Content type match
            if context.content_type and entry.content:
                # Check multiple possible content-type fields
                for ct_key in ("content_type", "asset_type", "insight_type", "offer_type"):
                    entry_ct = entry.content.get(ct_key, "")
                    if entry_ct and isinstance(entry_ct, str):
                        if entry_ct.lower() == context.content_type.lower():
                            match_score += 0.3
                            break

            # Tag match: each overlapping tag adds 0.3 / max(1, len(tags))
            if context_tags_lower and entry.content:
                # Build a set of searchable text from entry content values
                entry_text_parts: List[str] = []
                for v in entry.content.values():
                    if isinstance(v, str):
                        entry_text_parts.append(v.lower())
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, str):
                                entry_text_parts.append(item.lower())
                entry_text = " ".join(entry_text_parts)

                matching_tags = sum(
                    1 for tag in context_tags_lower
                    if tag in entry_text
                )
                if matching_tags > 0:
                    tag_bonus = 0.3 * min(matching_tags, 3) / 3.0
                    match_score += tag_bonus

            # Brand constraint strength bonus
            if entry.source_layer == "brand_constraints":
                strength = entry.content.get("strength", 1)
                if isinstance(strength, (int, float)):
                    match_score += min(float(strength), 5.0) * 0.1

            match_score = min(match_score, 1.0)

            # Weighted average
            entry.relevance_score = round(
                (confidence_score * 0.4)
                + (recency_score * 0.3)
                + (match_score * 0.3),
                4,
            )

        entries.sort(key=lambda e: e.relevance_score, reverse=True)
        return entries

    def _filter_by_staleness(
        self,
        entries: List[RetrievedMemory],
        include_stale: bool,
    ) -> List[RetrievedMemory]:
        """Exclude stale entries unless *include_stale* is True."""
        if include_stale:
            return entries
        return [e for e in entries if not e.is_stale]

    def _filter_by_confidence(
        self,
        entries: List[RetrievedMemory],
        min_confidence: str,
    ) -> List[RetrievedMemory]:
        """Exclude entries below *min_confidence*.

        Hierarchy: confirmed > observed > inferred > speculative.
        """
        min_rank = _CONFIDENCE_RANK.get(min_confidence, 0)
        return [
            e for e in entries
            if _CONFIDENCE_RANK.get(e.confidence, 0) >= min_rank
        ]

    def _generate_usage_hint(
        self,
        entry: RetrievedMemory,
        context: RetrievalContext,
    ) -> str:
        """Generate a context-aware usage hint for a retrieved memory.

        The hint tells the downstream consumer *how* to use this memory,
        not just *what* it contains.
        """
        layer = entry.source_layer
        ctx = context.context_type
        content = entry.content

        # -- Brand constraints -------------------------------------------------
        if layer == "brand_constraints":
            positive = content.get("positive", True)
            rule = content.get("rule", "") or content.get("description", "")
            strength = content.get("strength", 1)

            if ctx == "creative":
                if positive:
                    return f"Apply this style preference (strength {strength}/5): {rule}"
                return f"Avoid this pattern (strength {strength}/5): {rule}"
            elif ctx == "proposal":
                if positive:
                    return f"Operator prefers: {rule} — align proposal accordingly"
                return f"Operator dislikes: {rule} — avoid in proposal"
            elif ctx == "approval":
                if positive:
                    return f"Aligns with operator preference: {rule}"
                return f"Conflicts with operator preference: {rule} — may trigger rejection"
            else:
                verb = "Follow" if positive else "Avoid"
                return f"{verb} brand constraint: {rule}"

        # -- Business facts ----------------------------------------------------
        if layer == "business_facts":
            key = content.get("key", "")
            value = content.get("value", "")
            category = content.get("category", "")

            if ctx == "creative":
                return f"Use current business data — {key}: {value}"
            elif ctx == "proposal":
                return f"Factor into proposal — {category}/{key}: {value}"
            elif ctx == "watcher":
                return f"Business context for threshold calibration — {key}: {value}"
            return f"Known business fact — {key}: {value}"

        # -- Channel learnings -------------------------------------------------
        if layer == "channel_learnings":
            channel = content.get("channel", "")
            insight = content.get("insight", "")
            effect_size = content.get("effect_size")
            data_points = content.get("data_points", 0)

            effect_str = f" ({effect_size:+.1f}x)" if effect_size is not None else ""
            dp_str = f" ({data_points} data points)" if data_points else ""

            if ctx == "proposal":
                return f"Consider for {channel}: {insight}{effect_str}{dp_str}"
            elif ctx == "creative":
                return f"Optimize for {channel}: {insight}{effect_str}"
            elif ctx == "channel_selection":
                return f"Channel data — {channel}: {insight}{effect_str}{dp_str}"
            return f"Channel insight — {channel}: {insight}"

        # -- Proof assets ------------------------------------------------------
        if layer == "proof_assets":
            asset_type = content.get("asset_type", "")
            approved_for = content.get("approved_for", [])
            consent = content.get("consent_status", "pending")

            if consent != "approved":
                return f"Proof asset ({asset_type}) available but consent is '{consent}' — verify before use"
            if ctx == "creative":
                approved_str = ", ".join(approved_for) if approved_for else "general use"
                return f"Use this {asset_type} for social proof — approved for: {approved_str}"
            return f"Available {asset_type} proof asset — consent: {consent}"

        # -- Offer learnings ---------------------------------------------------
        if layer == "offer_learnings":
            offer_desc = content.get("offer_description", "")
            cvr = content.get("conversion_rate")
            net = content.get("net_impact")
            seasonal = content.get("seasonal_relevance")

            parts = [f"Offer: {offer_desc}"]
            if cvr is not None:
                parts.append(f"{cvr:.1%} CVR")
            if net is not None:
                sign = "+" if net >= 0 else ""
                parts.append(f"{sign}${net:.0f} net impact")
            if seasonal:
                parts.append(f"seasonal: {seasonal}")

            if ctx == "creative":
                return "Consider this offer in copy — " + ", ".join(parts)
            elif ctx == "proposal":
                return "Data-backed offer option — " + ", ".join(parts)
            return "Offer learning — " + ", ".join(parts)

        # -- Audience learnings ------------------------------------------------
        if layer == "audience_learnings":
            segment = content.get("segment_description", "")
            insight = content.get("insight", "")
            preferred_ch = content.get("preferred_channel")
            msg_type = content.get("response_to_message_type")

            if ctx == "creative":
                hint = f"Audience segment '{segment}': {insight}"
                if msg_type:
                    hint += f" — responds to '{msg_type}' messaging"
                return hint
            elif ctx == "channel_selection":
                hint = f"Segment '{segment}'"
                if preferred_ch:
                    hint += f" prefers {preferred_ch}"
                return hint
            elif ctx == "proposal":
                hint = f"Target audience data — {segment}: {insight}"
                if preferred_ch:
                    hint += f" (engages on {preferred_ch})"
                return hint
            return f"Audience insight — {segment}: {insight}"

        # -- Fallback ----------------------------------------------------------
        return f"Memory from {layer}: {entry.summary}"

    # ------------------------------------------------------------------
    # Brief assembly helpers
    # ------------------------------------------------------------------

    def _compile_key_constraints(
        self,
        memories: List[RetrievedMemory],
    ) -> List[str]:
        """Extract the top brand constraints as one-line strings."""
        constraints: List[str] = []
        for m in memories:
            if m.source_layer == "brand_constraints":
                positive = m.content.get("positive", True)
                rule = m.content.get("rule", "") or m.content.get("description", "")
                strength = m.content.get("strength", 1)
                if rule:
                    prefix = "MUST" if positive else "MUST NOT"
                    constraints.append(f"[strength {strength}/5] {prefix}: {rule}")
        # Sort by strength descending
        constraints.sort(key=lambda c: -int(c.split("/")[0].split()[-1]))
        return constraints[:10]

    def _compile_winning_patterns(
        self,
        memories: List[RetrievedMemory],
    ) -> List[str]:
        """Extract patterns that have performed well."""
        patterns: List[str] = []
        for m in memories:
            if m.source_layer == "channel_learnings":
                effect = m.content.get("effect_size")
                if effect is not None and effect > 0:
                    patterns.append(
                        f"[{m.content.get('channel', '?')}] "
                        f"{m.content.get('insight', m.summary)} "
                        f"(+{effect:.1f}x, {m.content.get('data_points', 0)} pts)"
                    )
            elif m.source_layer == "brand_constraints" and m.content.get("positive"):
                patterns.append(m.summary)
            elif m.source_layer == "offer_learnings":
                net = m.content.get("net_impact")
                if net is not None and net > 0:
                    patterns.append(
                        f"{m.content.get('offer_description', m.summary)} "
                        f"(+${net:.0f} net)"
                    )
            elif m.source_layer == "audience_learnings":
                cvr = m.content.get("conversion_rate")
                if cvr is not None and cvr > 0:
                    patterns.append(
                        f"Segment '{m.content.get('segment_description', '?')}' "
                        f"converts at {cvr:.1%}"
                    )
        return patterns[:10]

    def _compile_things_to_avoid(
        self,
        memories: List[RetrievedMemory],
    ) -> List[str]:
        """Extract patterns that have performed poorly or been rejected."""
        avoid: List[str] = []
        for m in memories:
            if m.source_layer == "brand_constraints" and not m.content.get("positive", True):
                rule = m.content.get("rule", "") or m.content.get("description", "")
                if rule:
                    avoid.append(f"Avoid: {rule}")
            elif m.source_layer == "channel_learnings":
                effect = m.content.get("effect_size")
                if effect is not None and effect < 0:
                    avoid.append(
                        f"[{m.content.get('channel', '?')}] "
                        f"{m.content.get('insight', m.summary)} "
                        f"({effect:.1f}x)"
                    )
            elif m.source_layer == "offer_learnings":
                net = m.content.get("net_impact")
                if net is not None and net < 0:
                    avoid.append(
                        f"Underperforming offer: {m.content.get('offer_description', m.summary)} "
                        f"(${net:.0f} net)"
                    )
        return avoid[:10]

    def _compile_proof_assets(
        self,
        memories: List[RetrievedMemory],
    ) -> List[str]:
        """Extract available proof assets as one-line descriptions."""
        assets: List[str] = []
        for m in memories:
            if m.source_layer == "proof_assets":
                asset_type = m.content.get("asset_type", "")
                content_text = m.content.get("content", "")
                consent = m.content.get("consent_status", "pending")
                approved_for = m.content.get("approved_for", [])

                preview = content_text[:80] + "..." if len(content_text) > 80 else content_text
                approved_str = ", ".join(approved_for) if approved_for else "general"
                consent_flag = "" if consent == "approved" else f" [consent: {consent}]"

                assets.append(
                    f"[{asset_type}] {preview} — approved for: {approved_str}{consent_flag}"
                )
        return assets[:10]

    def _assemble_brief(
        self,
        context: RetrievalContext,
        all_adapted: List[RetrievedMemory],
    ) -> MemoryBrief:
        """Apply filters, rank, attach hints, and compile into a MemoryBrief."""
        total_searched = len(all_adapted)

        # Filter
        filtered = self._filter_by_staleness(all_adapted, context.include_stale)
        filtered = self._filter_by_confidence(filtered, context.min_confidence)

        # Rank
        ranked = self._rank_by_relevance(filtered, context)

        # Attach usage hints
        for entry in ranked:
            entry.usage_hint = self._generate_usage_hint(entry, context)

        # Truncate to max_results
        top = ranked[: context.max_results]

        return MemoryBrief(
            business_id=context.business_id,
            context=context,
            retrieved_at=_utc_now(),
            total_entries_searched=total_searched,
            entries_returned=len(top),
            memories=top,
            key_constraints=self._compile_key_constraints(ranked),
            winning_patterns=self._compile_winning_patterns(ranked),
            things_to_avoid=self._compile_things_to_avoid(ranked),
            available_proof_assets=self._compile_proof_assets(ranked),
        )

    # ------------------------------------------------------------------
    # Adapter helpers for batch conversion
    # ------------------------------------------------------------------

    def _adapt_all_entries(
        self,
        layers: Dict[str, Any],
    ) -> List[RetrievedMemory]:
        """Convert all entries across all loaded layers into RetrievedMemory."""
        adapted: List[RetrievedMemory] = []

        # Business facts
        bf: Optional[BusinessFactMemory] = layers.get("business_facts")
        if bf is not None:
            for entry in bf.facts:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_business_fact(entry))

        # Brand constraints
        bc: Optional[BrandConstraintMemory] = layers.get("brand_constraints")
        if bc is not None:
            for entry in bc.constraints:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_brand_constraint(entry))

        # Proof assets
        pa: Optional[ProofAssetMemory] = layers.get("proof_assets")
        if pa is not None:
            for entry in pa.assets:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_proof_asset(entry))

        # Channel learnings
        cl: Optional[ChannelLearningMemory] = layers.get("channel_learnings")
        if cl is not None:
            for entry in cl.learnings:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_channel_learning(entry))

        # Offer learnings
        ol: Optional[OfferLearningMemory] = layers.get("offer_learnings")
        if ol is not None:
            for entry in ol.learnings:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_offer_learning(entry))

        # Audience learnings
        al: Optional[AudienceLearningMemory] = layers.get("audience_learnings")
        if al is not None:
            for entry in al.learnings:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_audience_learning(entry))

        return adapted

    # ------------------------------------------------------------------
    # Context-specific retrieval implementations
    # ------------------------------------------------------------------

    def _retrieve_proposal(self, context: RetrievalContext) -> MemoryBrief:
        """Retrieve for proposal generation.

        Pulls:
        - Past actions of this type that performed well (winning patterns)
        - Past actions of this type that performed poorly (things to avoid)
        - Operator approval patterns for this action type
        - Channel learnings for target channel
        - Relevant business facts
        - Brand constraints (always)
        """
        layers = self._load_memory_layers(context.business_id)
        adapted: List[RetrievedMemory] = []

        # Brand constraints — always included
        bc: Optional[BrandConstraintMemory] = layers.get("brand_constraints")
        if bc is not None:
            for entry in bc.constraints:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_brand_constraint(entry))

        # Business facts — relevant to ensuring proposal uses current data
        bf: Optional[BusinessFactMemory] = layers.get("business_facts")
        if bf is not None:
            for entry in bf.facts:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_business_fact(entry))

        # Channel learnings — filtered to target channel if provided,
        # otherwise include all for cross-channel proposal context
        cl: Optional[ChannelLearningMemory] = layers.get("channel_learnings")
        if cl is not None:
            if context.channel:
                channel_entries = cl.get_learnings_for_channel(context.channel)
            else:
                channel_entries = [
                    e for e in cl.learnings
                    if e.metadata.status != MemoryStatus.ARCHIVED.value
                ]
            for entry in channel_entries:
                adapted.append(_adapt_channel_learning(entry))

        # Offer learnings — for this channel if specified
        ol: Optional[OfferLearningMemory] = layers.get("offer_learnings")
        if ol is not None:
            if context.channel:
                offer_entries = ol.get_offers_for_channel(context.channel)
            else:
                offer_entries = ol.get_best_offers(limit=10)
            for entry in offer_entries:
                adapted.append(_adapt_offer_learning(entry))

        # Audience learnings — include high-value segments
        al: Optional[AudienceLearningMemory] = layers.get("audience_learnings")
        if al is not None:
            for entry in al.get_highest_value_segments(limit=5):
                adapted.append(_adapt_audience_learning(entry))

        return self._assemble_brief(context, adapted)

    def _retrieve_creative(self, context: RetrievalContext) -> MemoryBrief:
        """Retrieve for creative content generation.

        Pulls:
        - Brand voice/tone preferences (brand constraints)
        - Best-performing creative for this content_type + channel
        - Approved proof assets for this content type
        - Audience insights for target audience
        - Offer learnings (what offers to consider in copy)
        """
        layers = self._load_memory_layers(context.business_id)
        adapted: List[RetrievedMemory] = []

        # Brand constraints — voice, tone, style
        bc: Optional[BrandConstraintMemory] = layers.get("brand_constraints")
        if bc is not None:
            # Include all active constraints; content-type-specific ones
            # will rank higher via the relevance scorer
            for entry in bc.constraints:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_brand_constraint(entry))

            # Also pull content-type-specific constraints to front
            if context.content_type:
                for entry in bc.get_constraints_for_content_type(context.content_type):
                    # Already in the list from the loop above; they will
                    # rank higher naturally due to context matching.
                    pass

        # Proof assets — approved for this content type
        pa: Optional[ProofAssetMemory] = layers.get("proof_assets")
        if pa is not None:
            if context.content_type:
                approved = pa.get_approved_for_content_type(context.content_type)
                if approved:
                    for entry in approved:
                        adapted.append(_adapt_proof_asset(entry))
                else:
                    # Fall back to best-performing assets
                    for entry in pa.get_best_performing(limit=5):
                        adapted.append(_adapt_proof_asset(entry))
            else:
                for entry in pa.get_best_performing(limit=5):
                    adapted.append(_adapt_proof_asset(entry))

        # Channel learnings — best creative patterns for target channel
        cl: Optional[ChannelLearningMemory] = layers.get("channel_learnings")
        if cl is not None:
            if context.channel:
                for entry in cl.get_learnings_for_channel(context.channel):
                    adapted.append(_adapt_channel_learning(entry))
            else:
                # Include strongest insights across channels
                for entry in cl.get_strongest_insights(min_data_points=3):
                    adapted.append(_adapt_channel_learning(entry))

        # Audience learnings — target audience if specified
        al: Optional[AudienceLearningMemory] = layers.get("audience_learnings")
        if al is not None:
            if context.audience_segment:
                # Look for matching segment
                for entry in al.learnings:
                    if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                        continue
                    seg_lower = entry.segment_description.lower()
                    aud_lower = context.audience_segment.lower()
                    if aud_lower in seg_lower or seg_lower in aud_lower:
                        adapted.append(_adapt_audience_learning(entry))
                # If no direct match, include highest-value segments
                if not any(m.source_layer == "audience_learnings" for m in adapted):
                    for entry in al.get_highest_value_segments(limit=3):
                        adapted.append(_adapt_audience_learning(entry))
            else:
                for entry in al.get_highest_value_segments(limit=3):
                    adapted.append(_adapt_audience_learning(entry))

        # Offer learnings — what offers to weave into copy
        ol: Optional[OfferLearningMemory] = layers.get("offer_learnings")
        if ol is not None:
            for entry in ol.get_best_offers(limit=5):
                adapted.append(_adapt_offer_learning(entry))

        return self._assemble_brief(context, adapted)

    def _retrieve_channel_selection(self, context: RetrievalContext) -> MemoryBrief:
        """Retrieve for deciding which channels to use.

        Pulls:
        - Channel performance data (all channels)
        - Audience channel preferences
        - Budget efficiency by channel (offer cost/impact data)
        """
        layers = self._load_memory_layers(context.business_id)
        adapted: List[RetrievedMemory] = []

        # Brand constraints (always)
        bc: Optional[BrandConstraintMemory] = layers.get("brand_constraints")
        if bc is not None:
            # Only channel-related constraints
            for entry in bc.constraints:
                if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                    continue
                if entry.constraint_type == "channel_preference":
                    adapted.append(_adapt_brand_constraint(entry))

        # All channel learnings — the core data
        cl: Optional[ChannelLearningMemory] = layers.get("channel_learnings")
        if cl is not None:
            for entry in cl.learnings:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_channel_learning(entry))

        # Audience learnings — preferred channels
        al: Optional[AudienceLearningMemory] = layers.get("audience_learnings")
        if al is not None:
            for entry in al.learnings:
                if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                    continue
                if entry.preferred_channel:
                    adapted.append(_adapt_audience_learning(entry))

        # Offer learnings — channel-specific ROI
        ol: Optional[OfferLearningMemory] = layers.get("offer_learnings")
        if ol is not None:
            for entry in ol.learnings:
                if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                    continue
                if entry.channel:
                    adapted.append(_adapt_offer_learning(entry))

        return self._assemble_brief(context, adapted)

    def _retrieve_approval(self, context: RetrievalContext) -> MemoryBrief:
        """Retrieve for predicting operator approval behavior.

        Pulls:
        - Brand constraints (especially negative ones -- rejection signals)
        - Channel learnings for operator preference patterns
        - Business facts that may affect approval (compliance, hours, etc.)
        """
        layers = self._load_memory_layers(context.business_id)
        adapted: List[RetrievedMemory] = []

        # Brand constraints — all of them, since any can trigger rejection
        bc: Optional[BrandConstraintMemory] = layers.get("brand_constraints")
        if bc is not None:
            for entry in bc.constraints:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_brand_constraint(entry))

        # Business facts — compliance, certifications, restrictions
        bf: Optional[BusinessFactMemory] = layers.get("business_facts")
        if bf is not None:
            compliance_categories = {"certifications", "insurance", "hours", "contact"}
            for entry in bf.facts:
                if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                    continue
                if entry.category in compliance_categories:
                    adapted.append(_adapt_business_fact(entry))

        # Channel learnings — operator has shown preferences here
        cl: Optional[ChannelLearningMemory] = layers.get("channel_learnings")
        if cl is not None:
            if context.channel:
                for entry in cl.get_learnings_for_channel(context.channel):
                    adapted.append(_adapt_channel_learning(entry))

        return self._assemble_brief(context, adapted)

    def _retrieve_watcher(self, context: RetrievalContext) -> MemoryBrief:
        """Retrieve for reducing watcher false positives.

        Pulls:
        - Brand constraints (for threshold calibration)
        - Business facts (affect what constitutes a real finding)
        - Channel learnings with negative effect sizes (known problems)
        - Audience learnings (segment-specific thresholds)

        Downstream consumers use ``things_to_avoid`` as a suppress list
        (findings that were previously dismissed) and
        ``winning_patterns`` as a prioritize list (findings that led to
        real action).
        """
        layers = self._load_memory_layers(context.business_id)
        adapted: List[RetrievedMemory] = []

        # Business facts — affect thresholds and what is normal
        bf: Optional[BusinessFactMemory] = layers.get("business_facts")
        if bf is not None:
            for entry in bf.facts:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_business_fact(entry))

        # Brand constraints — what the operator cares about
        bc: Optional[BrandConstraintMemory] = layers.get("brand_constraints")
        if bc is not None:
            for entry in bc.constraints:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_brand_constraint(entry))

        # Channel learnings — known problem areas (negative effects)
        # and confirmed good patterns (positive effects)
        cl: Optional[ChannelLearningMemory] = layers.get("channel_learnings")
        if cl is not None:
            for entry in cl.learnings:
                if entry.metadata.status == MemoryStatus.ARCHIVED.value:
                    continue
                if entry.effect_size is not None:
                    adapted.append(_adapt_channel_learning(entry))

        # Audience learnings — segment-specific data for calibration
        al: Optional[AudienceLearningMemory] = layers.get("audience_learnings")
        if al is not None:
            for entry in al.learnings:
                if entry.metadata.status != MemoryStatus.ARCHIVED.value:
                    adapted.append(_adapt_audience_learning(entry))

        return self._assemble_brief(context, adapted)

    def _retrieve_audit(self, context: RetrievalContext) -> MemoryBrief:
        """Retrieve for audit context — pull everything relevant.

        Audits need a wide view of the business: all facts, constraints,
        channel performance, audience data, and proof assets.
        """
        layers = self._load_memory_layers(context.business_id)
        adapted = self._adapt_all_entries(layers)
        return self._assemble_brief(context, adapted)

    def _retrieve_generic(self, context: RetrievalContext) -> MemoryBrief:
        """Fallback retrieval for unknown context types.

        Loads all entries and lets the ranker sort by relevance.
        """
        layers = self._load_memory_layers(context.business_id)
        adapted = self._adapt_all_entries(layers)
        return self._assemble_brief(context, adapted)
