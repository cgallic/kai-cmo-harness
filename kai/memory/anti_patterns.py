"""Anti-pattern memory and archetype default improvement system.

Tracks what does NOT work for a business -- rejected content, failed
campaigns, compliance violations, ignored proposals -- and prevents the
system from repeatedly proposing actions that fail.  Beyond individual
business learning, the :class:`ArchetypeDefaultImprovement` system
aggregates anonymized learnings across businesses to improve baseline
recommendations for each archetype.

Design
------
- Uses the dataclass + ``_SerializableModel`` pattern consistent with
  ``kai/runtime/models.py`` and ``kai/memory/schemas.py``.
- YAML-preferred persistence with JSON fallback.
- Atomic writes via temp file and rename.
- No external dependencies beyond the Python standard library (YAML is
  attempted first; JSON is the fallback).

Storage
-------
- Per-business anti-patterns:
  ``workspace/{business_id}/memory/anti_patterns.yaml``
- Aggregate archetype data:
  ``{aggregate_dir}/{archetype}.yaml``
- Improvement suggestions:
  ``{aggregate_dir}/{archetype}_suggestions.yaml``
"""

from __future__ import annotations

import json
import logging
import uuid
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

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
# Helpers (mirrors schemas.py / writeback.py conventions)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    """Create *path* and all parents if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _new_id(prefix: str, length: int = 12) -> str:
    """Generate a unique ID with the given *prefix*."""
    return f"{prefix}_{uuid.uuid4().hex[:length]}"


def _write_atomic(path: Path, text: str) -> None:
    """Write *text* to *path* atomically via a temp file and rename."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _serialize(payload: Dict[str, Any]) -> str:
    """Serialize *payload* to YAML (preferred) or JSON."""
    if _HAS_YAML:
        return yaml.dump(
            payload, default_flow_style=False, sort_keys=False, allow_unicode=True
        )
    return json.dumps(payload, indent=2, sort_keys=False, default=str)


def _deserialize(text: str) -> Dict[str, Any]:
    """Deserialize *text* from YAML or JSON."""
    if _HAS_YAML:
        return yaml.safe_load(text) or {}
    return json.loads(text)


def _storage_ext() -> str:
    """Return the preferred file extension."""
    return "yaml" if _HAS_YAML else "json"


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


class AntiPatternType(str, Enum):
    """What class of failure this anti-pattern represents."""

    REJECTED_CONTENT = "rejected_content"
    FAILED_CAMPAIGN = "failed_campaign"
    LOW_QUALITY_CREATIVE = "low_quality_creative"
    COMPLIANCE_VIOLATION = "compliance_violation"
    IGNORED_PROPOSAL = "ignored_proposal"
    NEGATIVE_OUTCOME = "negative_outcome"


# Mapping from anti-pattern type to base risk at first occurrence.
_BASE_RISK: Dict[str, str] = {
    AntiPatternType.COMPLIANCE_VIOLATION.value: "high",
    AntiPatternType.NEGATIVE_OUTCOME.value: "medium",
    AntiPatternType.REJECTED_CONTENT.value: "medium",
    AntiPatternType.FAILED_CAMPAIGN.value: "medium",
    AntiPatternType.LOW_QUALITY_CREATIVE.value: "low",
    AntiPatternType.IGNORED_PROPOSAL.value: "low",
}

# Occurrence thresholds for risk escalation.
_RISK_ESCALATION_THRESHOLD = 3  # >= this count escalates risk


# ---------------------------------------------------------------------------
# Anti-pattern entry
# ---------------------------------------------------------------------------


@dataclass
class AntiPatternEntry(_SerializableModel):
    """A single recorded anti-pattern for a business.

    Each entry captures a generalizable pattern that failed, why it
    failed, how many times it has recurred, and what to do instead.
    """

    id: str = ""
    business_id: str = ""
    anti_pattern_type: str = ""  # AntiPatternType value
    description: str = ""
    action_type: str = ""
    channel: Optional[str] = None
    content_type: Optional[str] = None
    pattern_signature: str = ""
    failure_reason: str = ""
    specific_feedback: Optional[str] = None
    occurrence_count: int = 1
    first_seen: str = ""
    last_seen: str = ""
    risk_if_repeated: str = "low"
    alternative_approach: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _new_id("ap")
        now = _utc_now()
        if not self.first_seen:
            self.first_seen = now
        if not self.last_seen:
            self.last_seen = now


# ---------------------------------------------------------------------------
# Anti-pattern memory (per-business store)
# ---------------------------------------------------------------------------


@dataclass
class AntiPatternMemory(_SerializableModel):
    """The full anti-pattern memory for a single business.

    Provides query helpers that downstream systems (proposal generation,
    quality gates) use to check new work against past failures.
    """

    business_id: str = ""
    patterns: List[AntiPatternEntry] = field(default_factory=list)

    # -- query methods ---------------------------------------------------

    def get_patterns_for_action_type(self, action_type: str) -> List[AntiPatternEntry]:
        """Return all patterns matching the given *action_type*."""
        return [p for p in self.patterns if p.action_type == action_type]

    def get_patterns_for_channel(self, channel: str) -> List[AntiPatternEntry]:
        """Return all patterns matching the given *channel*."""
        return [p for p in self.patterns if p.channel == channel]

    def get_high_risk_patterns(self) -> List[AntiPatternEntry]:
        """Return patterns where ``risk_if_repeated`` is ``"high"``."""
        return [p for p in self.patterns if p.risk_if_repeated == "high"]

    def get_frequent_patterns(self, min_occurrences: int = 3) -> List[AntiPatternEntry]:
        """Return patterns that have failed *min_occurrences* or more times."""
        return [p for p in self.patterns if p.occurrence_count >= min_occurrences]


# ---------------------------------------------------------------------------
# Anti-pattern matcher
# ---------------------------------------------------------------------------


class AntiPatternMatcher:
    """Checks new proposals against known anti-patterns and records new ones.

    Parameters
    ----------
    memory:
        The :class:`AntiPatternMemory` instance for the business.
    """

    def __init__(self, memory: AntiPatternMemory) -> None:
        self.memory = memory

    # -- public API ------------------------------------------------------

    def check_proposal(
        self,
        action_type: str,
        channel: Optional[str],
        content_type: Optional[str],
        content_features: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Check a proposed action against known anti-patterns.

        Parameters
        ----------
        action_type:
            The type of action being proposed (e.g. ``"social_post"``).
        channel:
            Target channel (e.g. ``"instagram"``).
        content_type:
            Content format (e.g. ``"carousel"``).
        content_features:
            Dict describing the proposed content.  Expected keys include
            ``tone``, ``cta_type``, ``offer_type``, ``headline_style``,
            ``visual_style``, etc.

        Returns
        -------
        list[dict]
            Each match contains: ``anti_pattern_id``, ``match_score``
            (0.0-1.0), ``description``, ``risk_level``, ``alternative``.
            Sorted by match_score descending.  Only scores >= 0.2 are
            returned.
        """
        matches: List[Dict[str, Any]] = []
        for pattern in self.memory.patterns:
            score = self._calculate_match_score(
                pattern, action_type, channel, content_type, content_features
            )
            if score >= 0.2:
                matches.append(
                    {
                        "anti_pattern_id": pattern.id,
                        "match_score": round(score, 2),
                        "description": pattern.description,
                        "risk_level": pattern.risk_if_repeated,
                        "alternative": pattern.alternative_approach,
                    }
                )
        matches.sort(key=lambda m: m["match_score"], reverse=True)
        return matches

    def record_anti_pattern(
        self,
        action_id: str,
        business_id: str,
        anti_pattern_type: str,
        action_type: str,
        channel: Optional[str],
        content_type: Optional[str],
        failure_reason: str,
        specific_feedback: Optional[str] = None,
    ) -> AntiPatternEntry:
        """Record a new anti-pattern or increment an existing one.

        If a pattern with the same ``pattern_signature`` already exists
        in memory, the existing entry's ``occurrence_count`` and
        ``last_seen`` are updated and its risk is re-evaluated.  Otherwise
        a new entry is created.

        Returns the created or updated :class:`AntiPatternEntry`.
        """
        signature = self._generate_pattern_signature(
            action_type, channel, content_type, failure_reason
        )

        # Check for existing pattern with same signature
        existing = self._find_by_signature(signature)
        if existing is not None:
            existing.occurrence_count += 1
            existing.last_seen = _utc_now()
            # Merge feedback if new info is provided
            if specific_feedback and specific_feedback != existing.specific_feedback:
                if existing.specific_feedback:
                    existing.specific_feedback = (
                        f"{existing.specific_feedback}; {specific_feedback}"
                    )
                else:
                    existing.specific_feedback = specific_feedback
            # Store source action in metadata
            source_actions: List[str] = existing.metadata.get("source_action_ids", [])
            if action_id not in source_actions:
                source_actions.append(action_id)
                existing.metadata["source_action_ids"] = source_actions
            # Re-evaluate risk
            existing.risk_if_repeated = _determine_risk(
                anti_pattern_type, existing.occurrence_count
            )
            return existing

        # Create new entry
        now = _utc_now()
        description = self._build_description(
            action_type, channel, content_type, failure_reason, specific_feedback
        )
        entry = AntiPatternEntry(
            business_id=business_id,
            anti_pattern_type=anti_pattern_type,
            description=description,
            action_type=action_type,
            channel=channel,
            content_type=content_type,
            pattern_signature=signature,
            failure_reason=failure_reason,
            specific_feedback=specific_feedback,
            occurrence_count=1,
            first_seen=now,
            last_seen=now,
            risk_if_repeated=_determine_risk(anti_pattern_type, 1),
            metadata={"source_action_ids": [action_id]},
        )
        self.memory.patterns.append(entry)
        return entry

    # -- private helpers -------------------------------------------------

    def _find_by_signature(self, signature: str) -> Optional[AntiPatternEntry]:
        """Return the first pattern whose signature matches *signature*."""
        for pattern in self.memory.patterns:
            if pattern.pattern_signature == signature:
                return pattern
        return None

    def _generate_pattern_signature(
        self,
        action_type: str,
        channel: Optional[str],
        content_type: Optional[str],
        failure_reason: str,
    ) -> str:
        """Create a generalizable, matchable signature.

        Format: ``{action_type}_{channel}_{content_type}_{failure_reason}``
        with missing parts omitted and all values lower-cased and
        normalized (spaces to underscores, stripped of special chars).
        """
        parts: List[str] = []
        for value in (action_type, channel, content_type, failure_reason):
            if value:
                normalized = (
                    value.lower()
                    .replace(" ", "_")
                    .replace("-", "_")
                    .replace(".", "")
                    .replace(",", "")
                    .replace("'", "")
                    .replace('"', "")
                    .strip("_")
                )
                if normalized:
                    parts.append(normalized)
        return "_".join(parts) if parts else "unknown_pattern"

    def _calculate_match_score(
        self,
        pattern: AntiPatternEntry,
        action_type: str,
        channel: Optional[str],
        content_type: Optional[str],
        content_features: Dict[str, Any],
    ) -> float:
        """Score how closely a proposal matches a known anti-pattern.

        Scoring tiers:
        - Exact match on action_type + channel + pattern_signature: 1.0
        - Partial match (same action_type, similar pattern_signature): 0.5-0.8
        - Weak match (same channel, different action_type but similar features): 0.2-0.4

        The score is the *maximum* of the three tier evaluations (a
        proposal might match weakly on one axis but strongly on another).
        """
        # -- Tier 1: exact signature match --------------------------------
        proposal_sig = self._generate_pattern_signature(
            action_type, channel, content_type, ""
        )
        # Full signature (with failure_reason) match
        if (
            pattern.action_type == action_type
            and pattern.channel == channel
            and pattern.pattern_signature.startswith(proposal_sig)
        ):
            return 1.0

        # -- Tier 2: partial match ----------------------------------------
        tier2_score = 0.0
        if pattern.action_type == action_type:
            tier2_score = 0.5
            # Bonus for matching channel
            if channel and pattern.channel == channel:
                tier2_score += 0.15
            # Bonus for matching content_type
            if content_type and pattern.content_type == content_type:
                tier2_score += 0.15
            # Cap at 0.8 for partial match tier
            tier2_score = min(tier2_score, 0.8)

        # -- Tier 3: weak feature match -----------------------------------
        tier3_score = 0.0
        if channel and pattern.channel == channel and pattern.action_type != action_type:
            tier3_score = 0.2
            # Check content_features overlap with pattern signature
            feature_overlap = self._feature_overlap_score(
                pattern, content_features
            )
            tier3_score += feature_overlap * 0.2  # up to +0.2 from features
            tier3_score = min(tier3_score, 0.4)

        return max(tier2_score, tier3_score)

    @staticmethod
    def _feature_overlap_score(
        pattern: AntiPatternEntry,
        content_features: Dict[str, Any],
    ) -> float:
        """Compute 0.0-1.0 overlap between content features and pattern.

        Checks how many feature values appear in the pattern's
        signature, description, or specific_feedback.
        """
        if not content_features:
            return 0.0

        searchable = " ".join(
            filter(
                None,
                [
                    pattern.pattern_signature,
                    pattern.description,
                    pattern.specific_feedback or "",
                    pattern.failure_reason,
                ],
            )
        ).lower()

        if not searchable:
            return 0.0

        match_count = 0
        total = 0
        for _key, value in content_features.items():
            if value is None:
                continue
            total += 1
            val_str = str(value).lower().replace(" ", "_")
            if val_str in searchable or val_str.replace("_", " ") in searchable:
                match_count += 1

        if total == 0:
            return 0.0
        return match_count / total

    @staticmethod
    def _build_description(
        action_type: str,
        channel: Optional[str],
        content_type: Optional[str],
        failure_reason: str,
        specific_feedback: Optional[str],
    ) -> str:
        """Build a human-readable description of the anti-pattern."""
        parts: List[str] = []
        label = action_type.replace("_", " ").title()
        if channel:
            label += f" on {channel}"
        if content_type:
            label += f" ({content_type})"
        parts.append(label)

        reason_label = failure_reason.replace("_", " ")
        parts.append(f"failed due to {reason_label}")

        if specific_feedback:
            parts.append(f"-- {specific_feedback}")

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Risk determination helper
# ---------------------------------------------------------------------------


def _determine_risk(anti_pattern_type: str, occurrence_count: int) -> str:
    """Determine risk_if_repeated based on type and recurrence.

    Rules:
    - Compliance violations are always ``"high"``.
    - Any pattern with >= 3 occurrences escalates to ``"high"``.
    - Otherwise use the base risk from ``_BASE_RISK``.
    """
    if anti_pattern_type == AntiPatternType.COMPLIANCE_VIOLATION.value:
        return "high"
    if occurrence_count >= _RISK_ESCALATION_THRESHOLD:
        return "high"
    return _BASE_RISK.get(anti_pattern_type, "medium")


# =========================================================================
# Archetype aggregate and default improvement
# =========================================================================


@dataclass
class ArchetypeAggregate(_SerializableModel):
    """Aggregated learnings across multiple businesses for one archetype.

    Used by :class:`ArchetypeDefaultImprovement` to identify patterns
    that warrant changes to archetype defaults.
    """

    archetype: str = ""
    total_businesses_observed: int = 0
    action_success_rates: Dict[str, Dict[str, float]] = field(default_factory=dict)
    common_first_actions: List[Dict[str, Any]] = field(default_factory=list)
    common_anti_patterns: List[Dict[str, Any]] = field(default_factory=list)
    default_improvement_suggestions: List[str] = field(default_factory=list)
    last_updated: str = ""

    def __post_init__(self) -> None:
        if not self.last_updated:
            self.last_updated = _utc_now()


@dataclass
class DefaultImprovementSuggestion(_SerializableModel):
    """A suggested change to an archetype's defaults backed by evidence.

    Suggestions are generated by
    :meth:`ArchetypeDefaultImprovement.generate_improvement_suggestions`
    and must be reviewed and approved before being applied.
    """

    id: str = ""
    archetype: str = ""
    suggestion_type: str = ""
    description: str = ""
    evidence: str = ""
    impact_estimate: str = "medium"
    confidence: str = "low"
    approved: bool = False
    applied: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            self.id = _new_id("imp", 8)


# -- Suggestion-type constants for clarity --------------------------------

SUGGESTION_ADD_DEFAULT_ACTION = "add_default_action"
SUGGESTION_REMOVE_DEFAULT_ACTION = "remove_default_action"
SUGGESTION_CHANGE_PRIORITY = "change_priority"
SUGGESTION_ADD_WATCHER = "add_watcher"
SUGGESTION_ADJUST_THRESHOLD = "adjust_threshold"

# -- Thresholds for suggestion generation ---------------------------------

_ADOPTION_THRESHOLD = 0.80       # > 80% adoption -> add_default_action
_IGNORE_THRESHOLD = 0.10         # < 10% action rate -> change_priority (lower)
_UNDERPERFORM_THRESHOLD = 0.30   # < 30% success rate -> adjust_threshold
_WATCHER_ACTION_THRESHOLD = 0.70 # > 70% action rate from watcher -> add_watcher
_ANTI_PATTERN_PREVALENCE = 0.50  # > 50% of businesses -> adjust_threshold


class ArchetypeDefaultImprovement:
    """Aggregates cross-business learnings and suggests archetype defaults.

    Parameters
    ----------
    aggregate_dir:
        Directory where aggregate data and suggestions are stored.
        Typically ``workspace/_aggregates/`` or similar.
    """

    def __init__(self, aggregate_dir: str) -> None:
        self.aggregate_dir = Path(aggregate_dir)
        _ensure_dir(self.aggregate_dir)

    # -- public API ------------------------------------------------------

    def analyze_patterns(
        self,
        archetype: str,
        business_learnings: List[Dict[str, Any]],
    ) -> ArchetypeAggregate:
        """Aggregate learnings across multiple businesses for *archetype*.

        Parameters
        ----------
        archetype:
            The archetype identifier (e.g. ``"local_service"``).
        business_learnings:
            A list of per-business learning summaries.  Each dict
            should contain:

            - ``business_id`` (str)
            - ``actions_taken`` (list[dict]): each with ``action_type``,
              ``channel``, ``success`` (bool), ``order`` (int, 1-based
              sequence).
            - ``anti_patterns`` (list[dict]): each with
              ``pattern_signature``, ``description``.
            - ``watcher_findings_actioned`` (list[dict]): each with
              ``finding_type``, ``actioned`` (bool).
            - ``findings_ignored`` (list[dict]): each with
              ``finding_type``, ``action_rate`` (float 0-1).

        Returns
        -------
        ArchetypeAggregate
        """
        total = len(business_learnings)
        if total == 0:
            return ArchetypeAggregate(archetype=archetype)

        success_rates = self._compute_action_success_rates(business_learnings)
        first_actions = self._identify_common_first_actions(business_learnings, total)
        anti_patterns = self._identify_common_anti_patterns(business_learnings, total)

        aggregate = ArchetypeAggregate(
            archetype=archetype,
            total_businesses_observed=total,
            action_success_rates=success_rates,
            common_first_actions=first_actions,
            common_anti_patterns=anti_patterns,
            last_updated=_utc_now(),
        )

        # Persist
        self._save_aggregate(aggregate)
        return aggregate

    def generate_improvement_suggestions(
        self,
        aggregate: ArchetypeAggregate,
    ) -> List[DefaultImprovementSuggestion]:
        """Generate improvement suggestions based on aggregate data.

        Five rules are applied:

        1. If > 80% of businesses eventually do an action, suggest making
           it a default.
        2. If a finding is always ignored (< 10% action rate), suggest
           lowering its priority.
        3. If a channel consistently underperforms (< 30% success rate),
           suggest adjusting the channel mix.
        4. If a watcher finding consistently leads to action (> 70%
           action rate), suggest making it auto-eligible.
        5. If an anti-pattern appears in > 50% of businesses, suggest
           adding it to archetype default constraints.

        Returns
        -------
        list[DefaultImprovementSuggestion]
            Sorted by impact_estimate (high first).
        """
        archetype = aggregate.archetype
        total = aggregate.total_businesses_observed
        if total == 0:
            return []

        suggestions: List[DefaultImprovementSuggestion] = []

        # -- Rule 1: high adoption actions -> add_default_action ----------
        for action in aggregate.common_first_actions:
            pct = action.get("pct_of_businesses", 0.0)
            if pct > _ADOPTION_THRESHOLD:
                action_type = action.get("action_type", "unknown")
                channel = action.get("channel", "")
                label = action_type
                if channel:
                    label += f" on {channel}"
                confidence = self._confidence_from_sample(total)
                suggestions.append(
                    DefaultImprovementSuggestion(
                        archetype=archetype,
                        suggestion_type=SUGGESTION_ADD_DEFAULT_ACTION,
                        description=(
                            f"Make '{label}' a default action for "
                            f"{archetype} archetype"
                        ),
                        evidence=(
                            f"{pct * 100:.0f}% of {archetype} businesses "
                            f"({int(pct * total)}/{total}) manually add "
                            f"'{label}' within first month"
                        ),
                        impact_estimate="high",
                        confidence=confidence,
                    )
                )

        # -- Rule 2: ignored findings -> change_priority (lower) ----------
        # Scan common_first_actions for items with very low adoption that
        # represent findings rather than actions.  Also check aggregate
        # metadata if available.
        for action in aggregate.common_first_actions:
            pct = action.get("pct_of_businesses", 0.0)
            if pct < _IGNORE_THRESHOLD and pct > 0.0:
                action_type = action.get("action_type", "unknown")
                confidence = self._confidence_from_sample(total)
                suggestions.append(
                    DefaultImprovementSuggestion(
                        archetype=archetype,
                        suggestion_type=SUGGESTION_CHANGE_PRIORITY,
                        description=(
                            f"Lower priority of '{action_type}' finding "
                            f"for {archetype} archetype -- rarely acted upon"
                        ),
                        evidence=(
                            f"Only {pct * 100:.1f}% of {archetype} "
                            f"businesses take action on this finding "
                            f"({int(pct * total)}/{total})"
                        ),
                        impact_estimate="low",
                        confidence=confidence,
                    )
                )

        # -- Rule 3: underperforming channels -> adjust_threshold ---------
        for action_type, channels in aggregate.action_success_rates.items():
            for channel, rate in channels.items():
                if rate < _UNDERPERFORM_THRESHOLD:
                    confidence = self._confidence_from_sample(total)
                    suggestions.append(
                        DefaultImprovementSuggestion(
                            archetype=archetype,
                            suggestion_type=SUGGESTION_ADJUST_THRESHOLD,
                            description=(
                                f"Adjust channel mix: '{channel}' for "
                                f"'{action_type}' underperforms in "
                                f"{archetype} archetype"
                            ),
                            evidence=(
                                f"{channel} success rate for {action_type} "
                                f"is {rate * 100:.0f}% across {total} "
                                f"businesses (below {_UNDERPERFORM_THRESHOLD * 100:.0f}% threshold)"
                            ),
                            impact_estimate="medium",
                            confidence=confidence,
                        )
                    )

        # -- Rule 4: watcher findings with high action rate -> add_watcher
        # We look for this data in aggregate metadata if present, or
        # re-derive from the common_first_actions entries tagged as
        # watcher-originated.
        for action in aggregate.common_first_actions:
            watcher_action_rate = action.get("watcher_action_rate")
            if watcher_action_rate is not None and watcher_action_rate > _WATCHER_ACTION_THRESHOLD:
                action_type = action.get("action_type", "unknown")
                confidence = self._confidence_from_sample(total)
                suggestions.append(
                    DefaultImprovementSuggestion(
                        archetype=archetype,
                        suggestion_type=SUGGESTION_ADD_WATCHER,
                        description=(
                            f"Make '{action_type}' auto-eligible for "
                            f"{archetype} archetype -- watcher finding "
                            f"consistently leads to action"
                        ),
                        evidence=(
                            f"Watcher findings for '{action_type}' have a "
                            f"{watcher_action_rate * 100:.0f}% action rate "
                            f"across {total} businesses"
                        ),
                        impact_estimate="medium",
                        confidence=confidence,
                    )
                )

        # -- Rule 5: prevalent anti-patterns -> adjust_threshold ----------
        for ap in aggregate.common_anti_patterns:
            pct = ap.get("pct_of_businesses", 0.0)
            if pct > _ANTI_PATTERN_PREVALENCE:
                sig = ap.get("pattern_signature", "unknown")
                desc = ap.get("description", sig)
                confidence = self._confidence_from_sample(total)
                suggestions.append(
                    DefaultImprovementSuggestion(
                        archetype=archetype,
                        suggestion_type=SUGGESTION_ADJUST_THRESHOLD,
                        description=(
                            f"Add default constraint against '{sig}' "
                            f"for {archetype} archetype"
                        ),
                        evidence=(
                            f"Anti-pattern '{desc}' appears in "
                            f"{pct * 100:.0f}% of {archetype} businesses "
                            f"({int(pct * total)}/{total})"
                        ),
                        impact_estimate="high",
                        confidence=confidence,
                    )
                )

        # Sort by impact (high > medium > low)
        impact_order = {"high": 0, "medium": 1, "low": 2}
        suggestions.sort(key=lambda s: impact_order.get(s.impact_estimate, 9))

        # Persist suggestions
        self._save_suggestions(archetype, suggestions)
        return suggestions

    def apply_suggestion(self, suggestion_id: str) -> bool:
        """Mark a suggestion as applied.

        Searches all archetype suggestion files for *suggestion_id*.
        The actual application to archetype config is handled by the
        archetype system (Tasks 006-009) -- this method only updates the
        ``applied`` flag.

        Returns ``True`` if the suggestion was found and marked.
        """
        ext = _storage_ext()
        for path in self.aggregate_dir.glob(f"*_suggestions.{ext}"):
            try:
                raw = _deserialize(path.read_text(encoding="utf-8"))
            except Exception:
                continue
            suggestions_raw = raw.get("suggestions", [])
            found = False
            for entry in suggestions_raw:
                if entry.get("id") == suggestion_id:
                    entry["applied"] = True
                    found = True
                    break
            if found:
                raw["suggestions"] = suggestions_raw
                _write_atomic(path, _serialize(raw))
                return True
        return False

    # -- private helpers -------------------------------------------------

    @staticmethod
    def _calculate_action_adoption_rate(
        action_type: str,
        business_count: int,
        businesses_using: int,
    ) -> float:
        """Simple adoption rate: businesses_using / business_count."""
        if business_count <= 0:
            return 0.0
        return businesses_using / business_count

    @staticmethod
    def _identify_common_sequences(
        business_learnings: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Identify common action sequences across businesses.

        Extracts the ordered sequence of ``action_type`` values from each
        business and counts identical prefixes of length 2 and 3.

        Returns
        -------
        list[dict]
            Each item: ``{"sequence": [action_type, ...], "count": int,
            "pct_of_businesses": float}``.  Sorted by count descending.
        """
        total = len(business_learnings)
        if total == 0:
            return []

        # Collect ordered action sequences
        pair_counter: Counter[Tuple[str, ...]] = Counter()
        triple_counter: Counter[Tuple[str, ...]] = Counter()

        for bl in business_learnings:
            actions = bl.get("actions_taken", [])
            # Sort by order field to get the execution sequence
            sorted_actions = sorted(actions, key=lambda a: a.get("order", 0))
            action_types = [a.get("action_type", "") for a in sorted_actions if a.get("action_type")]

            # Extract unique pairs and triples
            seen_pairs: set[Tuple[str, ...]] = set()
            seen_triples: set[Tuple[str, ...]] = set()

            for i in range(len(action_types) - 1):
                pair = tuple(action_types[i : i + 2])
                if pair not in seen_pairs:
                    seen_pairs.add(pair)
                    pair_counter[pair] += 1
            for i in range(len(action_types) - 2):
                triple = tuple(action_types[i : i + 3])
                if triple not in seen_triples:
                    seen_triples.add(triple)
                    triple_counter[triple] += 1

        # Merge and sort by count
        results: List[Dict[str, Any]] = []
        for seq, count in triple_counter.most_common():
            if count >= 2:  # Need at least 2 businesses
                results.append(
                    {
                        "sequence": list(seq),
                        "count": count,
                        "pct_of_businesses": round(count / total, 2),
                    }
                )
        for seq, count in pair_counter.most_common():
            if count >= 2:
                results.append(
                    {
                        "sequence": list(seq),
                        "count": count,
                        "pct_of_businesses": round(count / total, 2),
                    }
                )

        # Deduplicate: if a triple and a pair share the same prefix, keep the triple
        # Sort longest first, then by count
        results.sort(key=lambda r: (-len(r["sequence"]), -r["count"]))
        return results

    @staticmethod
    def _compute_action_success_rates(
        business_learnings: List[Dict[str, Any]],
    ) -> Dict[str, Dict[str, float]]:
        """Compute success rate per action_type per channel.

        Returns ``{action_type: {channel: success_rate}}``.
        """
        # Accumulate counts: (action_type, channel) -> (successes, total)
        counts: Dict[Tuple[str, str], List[int]] = {}

        for bl in business_learnings:
            for action in bl.get("actions_taken", []):
                at = action.get("action_type", "")
                ch = action.get("channel", "_all")
                if not at:
                    continue
                key = (at, ch)
                if key not in counts:
                    counts[key] = [0, 0]
                counts[key][1] += 1
                if action.get("success", False):
                    counts[key][0] += 1

        result: Dict[str, Dict[str, float]] = {}
        for (at, ch), (succ, tot) in counts.items():
            rate = succ / tot if tot > 0 else 0.0
            result.setdefault(at, {})[ch] = round(rate, 3)
        return result

    @staticmethod
    def _identify_common_first_actions(
        business_learnings: List[Dict[str, Any]],
        total: int,
    ) -> List[Dict[str, Any]]:
        """Identify actions that most businesses end up doing.

        Counts how many businesses have each ``(action_type, channel)``
        combination and returns the most common ones with adoption rate.
        """
        action_counter: Counter[Tuple[str, str]] = Counter()

        for bl in business_learnings:
            seen: set[Tuple[str, str]] = set()
            for action in bl.get("actions_taken", []):
                at = action.get("action_type", "")
                ch = action.get("channel", "_all")
                if not at:
                    continue
                key = (at, ch)
                if key not in seen:
                    seen.add(key)
                    action_counter[key] += 1

        results: List[Dict[str, Any]] = []
        for (at, ch), count in action_counter.most_common():
            pct = count / total if total > 0 else 0.0
            entry: Dict[str, Any] = {
                "action_type": at,
                "channel": ch,
                "pct_of_businesses": round(pct, 3),
            }
            results.append(entry)
        return results

    @staticmethod
    def _identify_common_anti_patterns(
        business_learnings: List[Dict[str, Any]],
        total: int,
    ) -> List[Dict[str, Any]]:
        """Identify anti-patterns that appear across multiple businesses."""
        sig_counter: Counter[str] = Counter()
        sig_descriptions: Dict[str, str] = {}

        for bl in business_learnings:
            seen_sigs: set[str] = set()
            for ap in bl.get("anti_patterns", []):
                sig = ap.get("pattern_signature", "")
                if not sig or sig in seen_sigs:
                    continue
                seen_sigs.add(sig)
                sig_counter[sig] += 1
                # Keep the first description encountered
                if sig not in sig_descriptions:
                    sig_descriptions[sig] = ap.get("description", sig)

        results: List[Dict[str, Any]] = []
        for sig, count in sig_counter.most_common():
            pct = count / total if total > 0 else 0.0
            results.append(
                {
                    "pattern_signature": sig,
                    "pct_of_businesses": round(pct, 3),
                    "description": sig_descriptions.get(sig, sig),
                }
            )
        return results

    @staticmethod
    def _confidence_from_sample(total: int) -> str:
        """Map sample size to a confidence label.

        - < 5 businesses: ``"low"``
        - 5-19 businesses: ``"medium"``
        - >= 20 businesses: ``"high"``
        """
        if total >= 20:
            return "high"
        if total >= 5:
            return "medium"
        return "low"

    def _save_aggregate(self, aggregate: ArchetypeAggregate) -> None:
        """Persist an aggregate to disk."""
        ext = _storage_ext()
        path = self.aggregate_dir / f"{aggregate.archetype}.{ext}"
        _write_atomic(path, _serialize(aggregate.model_dump()))

    def _save_suggestions(
        self,
        archetype: str,
        suggestions: List[DefaultImprovementSuggestion],
    ) -> None:
        """Persist suggestions to disk."""
        ext = _storage_ext()
        path = self.aggregate_dir / f"{archetype}_suggestions.{ext}"
        payload = {
            "archetype": archetype,
            "generated_at": _utc_now(),
            "suggestions": [s.model_dump() for s in suggestions],
        }
        _write_atomic(path, _serialize(payload))


# =========================================================================
# Persistence helpers for AntiPatternMemory
# =========================================================================


def _anti_pattern_path(business_id: str, base_dir: str) -> Path:
    """Return the on-disk path for a business's anti-pattern memory.

    Pattern: ``{base_dir}/{business_id}/memory/anti_patterns.{ext}``
    """
    ext = _storage_ext()
    return Path(base_dir) / business_id / "memory" / f"anti_patterns.{ext}"


def load_anti_pattern_memory(business_id: str, base_dir: str) -> AntiPatternMemory:
    """Load anti-pattern memory from disk.

    Returns an empty :class:`AntiPatternMemory` if the file does not
    exist or contains malformed data.
    """
    yaml_path = Path(base_dir) / business_id / "memory" / "anti_patterns.yaml"
    json_path = Path(base_dir) / business_id / "memory" / "anti_patterns.json"

    file_path: Optional[Path] = None
    if yaml_path.exists():
        file_path = yaml_path
    elif json_path.exists():
        file_path = json_path

    if file_path is None:
        logger.debug(
            "Anti-pattern memory not found for %s -- returning empty",
            business_id,
        )
        return AntiPatternMemory(business_id=business_id)

    try:
        raw = _deserialize(file_path.read_text(encoding="utf-8"))
        if not isinstance(raw, dict):
            logger.warning(
                "Anti-pattern memory for %s is not a dict -- returning empty",
                business_id,
            )
            return AntiPatternMemory(business_id=business_id)
        return _reconstruct_anti_pattern_memory(raw, business_id)
    except Exception as exc:
        logger.warning(
            "Failed to load anti-pattern memory for %s: %s -- returning empty",
            business_id,
            exc,
        )
        return AntiPatternMemory(business_id=business_id)


def save_anti_pattern_memory(memory: AntiPatternMemory, base_dir: str) -> None:
    """Save anti-pattern memory to disk using atomic write."""
    if not memory.business_id:
        raise ValueError("AntiPatternMemory must have a non-empty business_id")
    path = _anti_pattern_path(memory.business_id, base_dir)
    _ensure_dir(path.parent)
    _write_atomic(path, _serialize(memory.model_dump()))


def _reconstruct_anti_pattern_memory(
    raw: Dict[str, Any],
    business_id: str,
) -> AntiPatternMemory:
    """Reconstruct an :class:`AntiPatternMemory` from a raw dict.

    Tolerates missing keys and unknown fields so that older/newer schema
    versions do not crash on load.
    """
    import dataclasses

    patterns_raw = raw.get("patterns", [])
    entry_fields = {f.name for f in dataclasses.fields(AntiPatternEntry)}

    patterns: List[AntiPatternEntry] = []
    for pr in patterns_raw:
        if not isinstance(pr, dict):
            continue
        kwargs = {k: v for k, v in pr.items() if k in entry_fields}
        patterns.append(AntiPatternEntry(**kwargs))

    return AntiPatternMemory(business_id=business_id, patterns=patterns)
