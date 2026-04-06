"""Memory writeback system -- captures structured learnings from marketing events.

Every time an action is approved, rejected, executed, measured, or receives
operator feedback, this module extracts structured learnings and persists
them to JSONL files organized by category.  This is the write path of Kai's
learning loop; the retrieval system (Task 075) is the read path.

Design
------
- Uses the dataclass + ``SerializableModel`` pattern from
  ``kai/runtime/models.py``.
- File I/O follows the atomic-write conventions from
  ``kai/runtime/actions.py`` (write to ``.tmp``, then rename).
- One JSONL file per ``LearningCategory`` under the configured
  ``memory_dir``.
- No external dependencies beyond the Python standard library.

Storage layout::

    {memory_dir}/
        brand_preference.jsonl
        creative_performance.jsonl
        channel_insight.jsonl
        audience_insight.jsonl
        offer_performance.jsonl
        compliance_constraint.jsonl
        operator_preference.jsonl
        business_fact.jsonl
        execution_record.jsonl
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers (mirrors kai/runtime/actions.py conventions)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    """Create *path* and all parents if they do not exist."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def _new_learning_id() -> str:
    """Generate a unique learning ID.  Format: ``learn_{12-hex-chars}``."""
    return f"learn_{uuid.uuid4().hex[:12]}"


def _json_dump_line(payload: Dict[str, Any]) -> str:
    """Serialize *payload* to a single compact JSON line."""
    return json.dumps(payload, separators=(",", ":"), sort_keys=True, default=str)


def _append_jsonl_atomic(path: Path, payload: Dict[str, Any]) -> None:
    """Append one JSON line to *path* using an atomic-write strategy.

    If the file does not exist it is created.  We write to a temporary
    file and then append its contents so that a crash mid-write never
    corrupts the main file.
    """
    line = _json_dump_line(payload) + "\n"
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    try:
        tmp_path.write_text(line, encoding="utf-8")
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


def _read_jsonl(path: Path) -> List[Dict[str, Any]]:
    """Read all JSON lines from *path*.  Returns ``[]`` if file is missing."""
    if not path.exists():
        return []
    records: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as fh:
        for raw_line in fh:
            raw_line = raw_line.strip()
            if raw_line:
                records.append(json.loads(raw_line))
    return records


def _rewrite_jsonl_atomic(path: Path, records: List[Dict[str, Any]]) -> None:
    """Rewrite the entire JSONL file atomically (for superseding updates)."""
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    lines = "".join(_json_dump_line(r) + "\n" for r in records)
    tmp_path.write_text(lines, encoding="utf-8")
    tmp_path.replace(path)


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


class LearningCategory(str, Enum):
    """What kind of knowledge this learning represents."""

    BRAND_PREFERENCE = "brand_preference"
    CREATIVE_PERFORMANCE = "creative_performance"
    CHANNEL_INSIGHT = "channel_insight"
    AUDIENCE_INSIGHT = "audience_insight"
    OFFER_PERFORMANCE = "offer_performance"
    COMPLIANCE_CONSTRAINT = "compliance_constraint"
    OPERATOR_PREFERENCE = "operator_preference"
    BUSINESS_FACT = "business_fact"
    EXECUTION_RECORD = "execution_record"


class LearningConfidence(str, Enum):
    """How confident we are in this learning."""

    CONFIRMED = "confirmed"
    OBSERVED = "observed"
    INFERRED = "inferred"
    SPECULATIVE = "speculative"


class WritebackTrigger(str, Enum):
    """What event triggered this learning capture."""

    ACTION_APPROVED = "action_approved"
    ACTION_REJECTED = "action_rejected"
    ACTION_EXECUTED = "action_executed"
    RESULTS_AVAILABLE = "results_available"
    OPERATOR_FEEDBACK = "operator_feedback"
    COMPLIANCE_VIOLATION = "compliance_violation"
    CREATIVE_SCORED = "creative_scored"
    WATCHER_FINDING = "watcher_finding"


# ---------------------------------------------------------------------------
# Data models
# ---------------------------------------------------------------------------


@dataclass
class Learning(_SerializableModel):
    """A single structured learning captured from a marketing event.

    Learnings are the core currency of the memory system.  Each one
    records a specific thing the system has learned about a business --
    what the operator prefers, what content performs well, which channels
    deliver, what compliance rules have been violated, etc.
    """

    id: str = ""
    business_id: str = ""
    category: str = ""           # LearningCategory value
    trigger: str = ""            # WritebackTrigger value
    title: str = ""              # Short human-readable description
    finding: str = ""            # Detailed description of what was learned
    confidence: str = ""         # LearningConfidence value
    evidence: Dict[str, Any] = field(default_factory=dict)
    source_action_id: Optional[str] = None
    source_type: str = ""        # "approval", "rejection", "performance_data", etc.
    tags: List[str] = field(default_factory=list)
    channel: Optional[str] = None
    content_type: Optional[str] = None
    created_at: str = ""
    expires_at: Optional[str] = None
    superseded_by: Optional[str] = None
    requires_confirmation: bool = False


@dataclass
class WritebackEvent(_SerializableModel):
    """An event that triggers the memory writeback pipeline.

    Upstream systems (approval flow, execution engine, analytics,
    compliance checker, quality gates, watchers) emit these events.
    The :class:`MemoryWriteback` engine dispatches each event to the
    appropriate handler based on its ``trigger`` field.
    """

    trigger: str = ""            # WritebackTrigger value
    action_id: Optional[str] = None
    business_id: str = ""
    event_data: Dict[str, Any] = field(default_factory=dict)
    timestamp: str = ""


# ---------------------------------------------------------------------------
# Tag extraction helpers
# ---------------------------------------------------------------------------


def _extract_tags_from_event(event: WritebackEvent) -> List[str]:
    """Build a list of searchable tags from event data.

    Tags are lowercase, deduplicated strings that the retrieval system
    (Task 075) uses for fast lookup.
    """
    tags: List[str] = []
    data = event.event_data

    if data.get("channel"):
        tags.append(str(data["channel"]).lower())
    if data.get("content_type"):
        tags.append(str(data["content_type"]).lower())
    if data.get("action_type"):
        tags.append(str(data["action_type"]).lower())
    if data.get("persona"):
        tags.append(str(data["persona"]).lower())

    # Pull keywords from title or subject line if present
    for key in ("title", "subject_line", "headline"):
        value = data.get(key)
        if value and isinstance(value, str):
            # Extract significant words (skip very short common words)
            for word in value.lower().split():
                cleaned = word.strip(".,!?:;\"'()[]")
                if len(cleaned) > 3 and cleaned not in tags:
                    tags.append(cleaned)
            break  # Only use the first found

    # Pull explicit tags from event data
    extra_tags = data.get("tags")
    if isinstance(extra_tags, list):
        for t in extra_tags:
            tag = str(t).lower()
            if tag not in tags:
                tags.append(tag)

    return tags


# ---------------------------------------------------------------------------
# MemoryWriteback engine
# ---------------------------------------------------------------------------


class MemoryWriteback:
    """Captures structured learnings from marketing events and persists them.

    Parameters
    ----------
    memory_dir:
        Base directory for memory storage.  Typically
        ``workspace/{business_id}/memory/``.  One JSONL file per
        :class:`LearningCategory` is stored here.
    """

    def __init__(self, memory_dir: str) -> None:
        self.memory_dir = _ensure_dir(Path(memory_dir))
        self._pending_confirmations: List[Learning] = []

        # Dispatch table mapping trigger values to handler methods
        self._handlers: Dict[str, Any] = {
            WritebackTrigger.ACTION_APPROVED.value: self._handle_action_approved,
            WritebackTrigger.ACTION_REJECTED.value: self._handle_action_rejected,
            WritebackTrigger.ACTION_EXECUTED.value: self._handle_action_executed,
            WritebackTrigger.RESULTS_AVAILABLE.value: self._handle_results_available,
            WritebackTrigger.OPERATOR_FEEDBACK.value: self._handle_operator_feedback,
            WritebackTrigger.COMPLIANCE_VIOLATION.value: self._handle_compliance_violation,
            WritebackTrigger.CREATIVE_SCORED.value: self._handle_creative_scored,
            WritebackTrigger.WATCHER_FINDING.value: self._handle_watcher_finding,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_event(self, event: WritebackEvent) -> List[Learning]:
        """Dispatch *event* to the appropriate handler and persist learnings.

        Auto-write learnings are persisted immediately.  Learnings that
        require operator confirmation are queued in
        ``_pending_confirmations``.

        Returns
        -------
        list[Learning]
            All learnings generated from this event (both auto-written
            and pending-confirmation).
        """
        handler = self._handlers.get(event.trigger)
        if handler is None:
            return []

        learnings: List[Learning] = handler(event)

        for learning in learnings:
            if learning.requires_confirmation:
                self._pending_confirmations.append(learning)
            else:
                # Check for superseded learnings before persisting
                superseded_id = self._check_for_superseded(learning)
                if superseded_id:
                    learning.evidence["superseded_learning_id"] = superseded_id
                self._persist_learning(learning)

        return learnings

    def confirm_learning(
        self,
        learning_id: str,
        confirmed: bool,
        operator_notes: Optional[str] = None,
    ) -> bool:
        """Operator confirms or dismisses a pending learning.

        Parameters
        ----------
        learning_id:
            The ``id`` of the learning to confirm or dismiss.
        confirmed:
            ``True`` to confirm (persist with confidence="confirmed"),
            ``False`` to dismiss.
        operator_notes:
            Optional notes from the operator.

        Returns
        -------
        bool
            ``True`` if the learning was found and processed.
        """
        target: Optional[Learning] = None
        target_idx: Optional[int] = None

        for idx, pending in enumerate(self._pending_confirmations):
            if pending.id == learning_id:
                target = pending
                target_idx = idx
                break

        if target is None or target_idx is None:
            return False

        # Remove from pending list
        self._pending_confirmations.pop(target_idx)

        if confirmed:
            # Upgrade confidence and persist
            target.confidence = LearningConfidence.CONFIRMED.value
            target.requires_confirmation = False
            if operator_notes:
                target.evidence["operator_confirmation_notes"] = operator_notes
            superseded_id = self._check_for_superseded(target)
            if superseded_id:
                target.evidence["superseded_learning_id"] = superseded_id
            self._persist_learning(target)
        else:
            # Optionally record the dismissal as its own learning
            if operator_notes:
                dismissal = Learning(
                    id=_new_learning_id(),
                    business_id=target.business_id,
                    category=LearningCategory.OPERATOR_PREFERENCE.value,
                    trigger=target.trigger,
                    title=f"Dismissed learning: {target.title}",
                    finding=(
                        f"Operator dismissed a proposed learning. "
                        f"Original finding: {target.finding}. "
                        f"Operator notes: {operator_notes}"
                    ),
                    confidence=LearningConfidence.CONFIRMED.value,
                    evidence={
                        "dismissed_learning_id": target.id,
                        "dismissed_category": target.category,
                        "operator_notes": operator_notes,
                    },
                    source_action_id=target.source_action_id,
                    source_type="dismissal",
                    tags=["dismissed"] + target.tags,
                    channel=target.channel,
                    content_type=target.content_type,
                    created_at=_utc_now(),
                    requires_confirmation=False,
                )
                self._persist_learning(dismissal)

        return True

    def get_pending_confirmations(self, business_id: str) -> List[Learning]:
        """Return all learnings awaiting operator confirmation for a business.

        Parameters
        ----------
        business_id:
            Filter pending confirmations to this business.

        Returns
        -------
        list[Learning]
            Pending learnings for the given business.
        """
        return [
            p for p in self._pending_confirmations
            if p.business_id == business_id
        ]

    # ------------------------------------------------------------------
    # Trigger handlers
    # ------------------------------------------------------------------

    def _handle_action_approved(self, event: WritebackEvent) -> List[Learning]:
        """Extract learnings from an approved action.

        When an operator approves an action, the specific creative choices
        embedded in that action (headline style, tone, CTA format, channel
        targeting) become signals about brand and operator preferences.

        Confidence: "observed" -- a single approval is a signal, not yet
        a confirmed preference.
        Auto-write: True.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)
        learnings: List[Learning] = []

        # Record the approval as a brand preference signal
        action_type = data.get("action_type", "unknown")
        title = data.get("title", "Untitled action")
        channel = data.get("channel")
        content_type = data.get("content_type")

        # Primary learning: approval pattern
        learnings.append(Learning(
            id=_new_learning_id(),
            business_id=event.business_id,
            category=LearningCategory.BRAND_PREFERENCE.value,
            trigger=WritebackTrigger.ACTION_APPROVED.value,
            title=f"Operator approved: {title}",
            finding=(
                f"Operator approved a {action_type} action"
                f"{f' on {channel}' if channel else ''}. "
                f"Title: \"{title}\". "
                f"This signals alignment with the operator's brand expectations."
            ),
            confidence=LearningConfidence.OBSERVED.value,
            evidence={
                "source_action_id": event.action_id,
                "action_type": action_type,
                "channel": channel,
                "content_type": content_type,
                "approved_payload_keys": list(data.get("suggested_payload", {}).keys())
                if isinstance(data.get("suggested_payload"), dict) else [],
            },
            source_action_id=event.action_id,
            source_type="approval",
            tags=tags + ["approved"],
            channel=channel,
            content_type=content_type,
            created_at=now,
            requires_confirmation=False,
        ))

        # If the action includes specific creative elements, record them
        payload = data.get("suggested_payload", {})
        if isinstance(payload, dict):
            # Headline style signal
            headline = payload.get("headline") or payload.get("subject_line")
            if headline and isinstance(headline, str):
                # Determine style attributes from the headline
                style_notes = []
                if any(c in headline for c in "!?"):
                    style_notes.append("uses punctuation emphasis")
                if len(headline.split()) <= 6:
                    style_notes.append("short/punchy")
                elif len(headline.split()) > 12:
                    style_notes.append("long-form")
                if any(w in headline.lower() for w in ("you", "your", "you're")):
                    style_notes.append("second-person address")

                if style_notes:
                    learnings.append(Learning(
                        id=_new_learning_id(),
                        business_id=event.business_id,
                        category=LearningCategory.BRAND_PREFERENCE.value,
                        trigger=WritebackTrigger.ACTION_APPROVED.value,
                        title=f"Approved headline style: {', '.join(style_notes)}",
                        finding=(
                            f"Operator approved content with headline \"{headline}\" "
                            f"which exhibits: {', '.join(style_notes)}. "
                            f"This suggests the operator accepts this style."
                        ),
                        confidence=LearningConfidence.OBSERVED.value,
                        evidence={
                            "source_action_id": event.action_id,
                            "headline": headline,
                            "style_attributes": style_notes,
                        },
                        source_action_id=event.action_id,
                        source_type="approval",
                        tags=tags + ["headline_style"] + style_notes,
                        channel=channel,
                        content_type=content_type,
                        created_at=now,
                        requires_confirmation=False,
                    ))

            # Tone signal
            tone = payload.get("tone") or payload.get("voice")
            if tone and isinstance(tone, str):
                learnings.append(Learning(
                    id=_new_learning_id(),
                    business_id=event.business_id,
                    category=LearningCategory.BRAND_PREFERENCE.value,
                    trigger=WritebackTrigger.ACTION_APPROVED.value,
                    title=f"Approved tone: {tone}",
                    finding=(
                        f"Operator approved content with tone \"{tone}\" "
                        f"for {action_type}{f' on {channel}' if channel else ''}."
                    ),
                    confidence=LearningConfidence.OBSERVED.value,
                    evidence={
                        "source_action_id": event.action_id,
                        "tone": tone,
                        "action_type": action_type,
                    },
                    source_action_id=event.action_id,
                    source_type="approval",
                    tags=tags + ["tone", tone.lower()],
                    channel=channel,
                    content_type=content_type,
                    created_at=now,
                    requires_confirmation=False,
                ))

        return learnings

    def _handle_action_rejected(self, event: WritebackEvent) -> List[Learning]:
        """Extract constraint learnings from a rejected action.

        Rejections are the strongest learning signals -- the operator
        explicitly said "this is wrong."  The rejection category and
        specific issues tell us exactly what to avoid in the future.

        Confidence: "confirmed" -- explicit operator correction.
        requires_confirmation: False.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)
        learnings: List[Learning] = []

        rejection_category = data.get("rejection_category", "general")
        rejection_reason = data.get("rejection_reason", "No reason provided")
        specific_issues = data.get("specific_issues", [])
        title = data.get("title", "Untitled action")
        channel = data.get("channel")
        content_type = data.get("content_type")
        action_type = data.get("action_type", "unknown")

        # Map rejection_category to a learning category
        category_map = {
            "brand_voice": LearningCategory.BRAND_PREFERENCE.value,
            "tone": LearningCategory.BRAND_PREFERENCE.value,
            "style": LearningCategory.BRAND_PREFERENCE.value,
            "compliance": LearningCategory.COMPLIANCE_CONSTRAINT.value,
            "legal": LearningCategory.COMPLIANCE_CONSTRAINT.value,
            "strategy": LearningCategory.OPERATOR_PREFERENCE.value,
            "targeting": LearningCategory.AUDIENCE_INSIGHT.value,
            "audience": LearningCategory.AUDIENCE_INSIGHT.value,
            "offer": LearningCategory.OFFER_PERFORMANCE.value,
            "pricing": LearningCategory.OFFER_PERFORMANCE.value,
            "creative": LearningCategory.CREATIVE_PERFORMANCE.value,
            "design": LearningCategory.CREATIVE_PERFORMANCE.value,
            "channel": LearningCategory.CHANNEL_INSIGHT.value,
        }
        learning_category = category_map.get(
            rejection_category,
            LearningCategory.OPERATOR_PREFERENCE.value,
        )

        # Build specific issues string for the finding
        issues_detail = ""
        if specific_issues and isinstance(specific_issues, list):
            issues_detail = " Specific issues: " + "; ".join(
                str(issue) for issue in specific_issues
            ) + "."

        # Primary rejection learning
        learnings.append(Learning(
            id=_new_learning_id(),
            business_id=event.business_id,
            category=learning_category,
            trigger=WritebackTrigger.ACTION_REJECTED.value,
            title=f"Rejected ({rejection_category}): {title}",
            finding=(
                f"Operator rejected a {action_type} action"
                f"{f' on {channel}' if channel else ''}"
                f" for reason: {rejection_reason}.{issues_detail}"
                f" This is a confirmed constraint to respect in future content."
            ),
            confidence=LearningConfidence.CONFIRMED.value,
            evidence={
                "source_action_id": event.action_id,
                "rejection_category": rejection_category,
                "rejection_reason": rejection_reason,
                "specific_issues": specific_issues,
                "action_type": action_type,
                "channel": channel,
            },
            source_action_id=event.action_id,
            source_type="rejection",
            tags=tags + ["rejected", rejection_category],
            channel=channel,
            content_type=content_type,
            created_at=now,
            requires_confirmation=False,
        ))

        # If brand_voice rejection, also record an operator_preference learning
        if rejection_category in ("brand_voice", "tone", "style"):
            learnings.append(Learning(
                id=_new_learning_id(),
                business_id=event.business_id,
                category=LearningCategory.OPERATOR_PREFERENCE.value,
                trigger=WritebackTrigger.ACTION_REJECTED.value,
                title=f"Operator dislikes: {rejection_reason}",
                finding=(
                    f"Operator explicitly rejected {action_type} content because of "
                    f"{rejection_category} issues: {rejection_reason}.{issues_detail}"
                    f" Avoid this pattern in future {action_type} work"
                    f"{f' on {channel}' if channel else ''}."
                ),
                confidence=LearningConfidence.CONFIRMED.value,
                evidence={
                    "source_action_id": event.action_id,
                    "rejection_category": rejection_category,
                    "rejection_reason": rejection_reason,
                    "specific_issues": specific_issues,
                },
                source_action_id=event.action_id,
                source_type="rejection",
                tags=tags + ["dislike", rejection_category, "voice_constraint"],
                channel=channel,
                content_type=content_type,
                created_at=now,
                requires_confirmation=False,
            ))

        return learnings

    def _handle_action_executed(self, event: WritebackEvent) -> List[Learning]:
        """Record an execution as a factual memory.

        This is not a preference or performance learning -- it is a
        record of what was deployed, when, and on which channel.  Useful
        for deduplication and timeline reconstruction.

        Confidence: "confirmed" -- it happened.
        Auto-write: True.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)

        title = data.get("title", "Untitled action")
        channel = data.get("channel")
        content_type = data.get("content_type")
        action_type = data.get("action_type", "unknown")
        content_summary = data.get("content_summary", "")
        executed_at = data.get("executed_at", event.timestamp)

        learning = Learning(
            id=_new_learning_id(),
            business_id=event.business_id,
            category=LearningCategory.EXECUTION_RECORD.value,
            trigger=WritebackTrigger.ACTION_EXECUTED.value,
            title=f"Executed: {title}",
            finding=(
                f"Action \"{title}\" ({action_type}) was executed"
                f"{f' on {channel}' if channel else ''}"
                f" at {executed_at}."
                f"{f' Summary: {content_summary}' if content_summary else ''}"
            ),
            confidence=LearningConfidence.CONFIRMED.value,
            evidence={
                "source_action_id": event.action_id,
                "action_type": action_type,
                "channel": channel,
                "content_type": content_type,
                "executed_at": executed_at,
                "content_summary": content_summary,
            },
            source_action_id=event.action_id,
            source_type="execution",
            tags=tags + ["executed"],
            channel=channel,
            content_type=content_type,
            created_at=now,
            requires_confirmation=False,
        )

        return [learning]

    def _handle_results_available(self, event: WritebackEvent) -> List[Learning]:
        """Extract performance learnings from measured action outcomes.

        This is the most valuable trigger -- it connects actions to real
        outcomes.  The confidence level depends on the attribution
        confidence from the analytics layer (Task 058).

        High-impact learnings (e.g., "this channel doesn't work") require
        operator confirmation because a bad data point or attribution
        error could produce a misleading conclusion.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)
        learnings: List[Learning] = []

        title = data.get("title", "Untitled action")
        channel = data.get("channel")
        content_type = data.get("content_type")
        action_type = data.get("action_type", "unknown")

        # Performance metrics
        metrics = data.get("metrics", {})
        target_metrics = data.get("target_metrics", {})
        benchmark_metrics = data.get("benchmark_metrics", {})
        attribution_confidence = data.get("attribution_confidence", "observed")

        # Map attribution confidence to learning confidence
        confidence_map = {
            "high": LearningConfidence.CONFIRMED.value,
            "confirmed": LearningConfidence.CONFIRMED.value,
            "medium": LearningConfidence.OBSERVED.value,
            "observed": LearningConfidence.OBSERVED.value,
            "low": LearningConfidence.INFERRED.value,
            "inferred": LearningConfidence.INFERRED.value,
            "speculative": LearningConfidence.SPECULATIVE.value,
        }
        confidence = confidence_map.get(
            str(attribution_confidence).lower(),
            LearningConfidence.OBSERVED.value,
        )

        # Determine if the action performed well or poorly
        performed_well: Optional[bool] = None
        performance_details: List[str] = []

        if isinstance(metrics, dict) and isinstance(target_metrics, dict):
            wins = 0
            losses = 0
            for metric_name, actual_value in metrics.items():
                if not isinstance(actual_value, (int, float)):
                    continue
                target = target_metrics.get(metric_name)
                if target is not None and isinstance(target, (int, float)):
                    if actual_value >= target:
                        wins += 1
                        ratio = actual_value / target if target != 0 else 0
                        performance_details.append(
                            f"{metric_name}: {actual_value} vs target {target} "
                            f"({ratio:.1f}x)"
                        )
                    else:
                        losses += 1
                        ratio = actual_value / target if target != 0 else 0
                        performance_details.append(
                            f"{metric_name}: {actual_value} vs target {target} "
                            f"({ratio:.1f}x -- below target)"
                        )
            if wins + losses > 0:
                performed_well = wins >= losses

        # Also check against benchmarks when targets are missing
        if performed_well is None and isinstance(metrics, dict) and isinstance(benchmark_metrics, dict):
            wins = 0
            losses = 0
            for metric_name, actual_value in metrics.items():
                if not isinstance(actual_value, (int, float)):
                    continue
                bench = benchmark_metrics.get(metric_name)
                if bench is not None and isinstance(bench, (int, float)):
                    if actual_value >= bench:
                        wins += 1
                        performance_details.append(
                            f"{metric_name}: {actual_value} vs benchmark {bench} (above)"
                        )
                    else:
                        losses += 1
                        performance_details.append(
                            f"{metric_name}: {actual_value} vs benchmark {bench} (below)"
                        )
            if wins + losses > 0:
                performed_well = wins >= losses

        performance_summary = "; ".join(performance_details) if performance_details else "No target comparison available"

        if performed_well is True:
            # Winning pattern
            learnings.append(Learning(
                id=_new_learning_id(),
                business_id=event.business_id,
                category=LearningCategory.CREATIVE_PERFORMANCE.value,
                trigger=WritebackTrigger.RESULTS_AVAILABLE.value,
                title=f"Strong performer: {title}",
                finding=(
                    f"Action \"{title}\" ({action_type})"
                    f"{f' on {channel}' if channel else ''}"
                    f" performed above targets. {performance_summary}."
                    f" Consider replicating this pattern."
                ),
                confidence=confidence,
                evidence={
                    "source_action_id": event.action_id,
                    "metrics": metrics,
                    "target_metrics": target_metrics,
                    "benchmark_metrics": benchmark_metrics,
                    "attribution_confidence": attribution_confidence,
                    "performance_details": performance_details,
                },
                source_action_id=event.action_id,
                source_type="performance_data",
                tags=tags + ["winner", "above_target"],
                channel=channel,
                content_type=content_type,
                created_at=now,
                requires_confirmation=False,
            ))
        elif performed_well is False:
            # Losing pattern -- high-impact, requires confirmation
            learnings.append(Learning(
                id=_new_learning_id(),
                business_id=event.business_id,
                category=LearningCategory.CREATIVE_PERFORMANCE.value,
                trigger=WritebackTrigger.RESULTS_AVAILABLE.value,
                title=f"Underperformer: {title}",
                finding=(
                    f"Action \"{title}\" ({action_type})"
                    f"{f' on {channel}' if channel else ''}"
                    f" performed below targets. {performance_summary}."
                    f" Review whether this pattern should be avoided."
                ),
                confidence=confidence,
                evidence={
                    "source_action_id": event.action_id,
                    "metrics": metrics,
                    "target_metrics": target_metrics,
                    "benchmark_metrics": benchmark_metrics,
                    "attribution_confidence": attribution_confidence,
                    "performance_details": performance_details,
                },
                source_action_id=event.action_id,
                source_type="performance_data",
                tags=tags + ["underperformer", "below_target"],
                channel=channel,
                content_type=content_type,
                created_at=now,
                requires_confirmation=True,
            ))

        # Channel-specific insight (e.g., best posting times, best formats)
        best_time = data.get("best_performing_time")
        best_format = data.get("best_performing_format")
        best_segment = data.get("best_performing_segment")

        if best_time and channel:
            learnings.append(Learning(
                id=_new_learning_id(),
                business_id=event.business_id,
                category=LearningCategory.CHANNEL_INSIGHT.value,
                trigger=WritebackTrigger.RESULTS_AVAILABLE.value,
                title=f"Best time on {channel}: {best_time}",
                finding=(
                    f"Content on {channel} performed best when posted/sent at "
                    f"{best_time}. Based on results from \"{title}\"."
                ),
                confidence=confidence,
                evidence={
                    "source_action_id": event.action_id,
                    "best_time": best_time,
                    "metrics": metrics,
                },
                source_action_id=event.action_id,
                source_type="performance_data",
                tags=tags + ["timing", "best_time", channel],
                channel=channel,
                content_type=content_type,
                created_at=now,
                requires_confirmation=False,
            ))

        if best_format and channel:
            learnings.append(Learning(
                id=_new_learning_id(),
                business_id=event.business_id,
                category=LearningCategory.CHANNEL_INSIGHT.value,
                trigger=WritebackTrigger.RESULTS_AVAILABLE.value,
                title=f"Best format on {channel}: {best_format}",
                finding=(
                    f"The format \"{best_format}\" performed best on {channel}. "
                    f"Based on results from \"{title}\"."
                ),
                confidence=confidence,
                evidence={
                    "source_action_id": event.action_id,
                    "best_format": best_format,
                    "metrics": metrics,
                },
                source_action_id=event.action_id,
                source_type="performance_data",
                tags=tags + ["format", best_format.lower(), channel],
                channel=channel,
                content_type=content_type,
                created_at=now,
                requires_confirmation=False,
            ))

        if best_segment:
            learnings.append(Learning(
                id=_new_learning_id(),
                business_id=event.business_id,
                category=LearningCategory.AUDIENCE_INSIGHT.value,
                trigger=WritebackTrigger.RESULTS_AVAILABLE.value,
                title=f"Best performing segment: {best_segment}",
                finding=(
                    f"Audience segment \"{best_segment}\" responded best to "
                    f"\"{title}\" ({action_type})"
                    f"{f' on {channel}' if channel else ''}."
                ),
                confidence=confidence,
                evidence={
                    "source_action_id": event.action_id,
                    "best_segment": best_segment,
                    "metrics": metrics,
                },
                source_action_id=event.action_id,
                source_type="performance_data",
                tags=tags + ["segment", best_segment.lower()],
                channel=channel,
                content_type=content_type,
                created_at=now,
                requires_confirmation=False,
            ))

        # Offer performance insight
        offer_data = data.get("offer")
        conversion_rate = metrics.get("conversion_rate") if isinstance(metrics, dict) else None
        if offer_data and conversion_rate is not None:
            learnings.append(Learning(
                id=_new_learning_id(),
                business_id=event.business_id,
                category=LearningCategory.OFFER_PERFORMANCE.value,
                trigger=WritebackTrigger.RESULTS_AVAILABLE.value,
                title=f"Offer performance: {offer_data} ({conversion_rate}% conversion)",
                finding=(
                    f"The offer \"{offer_data}\" achieved a {conversion_rate}% "
                    f"conversion rate via {action_type}"
                    f"{f' on {channel}' if channel else ''}."
                ),
                confidence=confidence,
                evidence={
                    "source_action_id": event.action_id,
                    "offer": offer_data,
                    "conversion_rate": conversion_rate,
                    "metrics": metrics,
                },
                source_action_id=event.action_id,
                source_type="performance_data",
                tags=tags + ["offer", "conversion"],
                channel=channel,
                content_type=content_type,
                created_at=now,
                requires_confirmation=False,
            ))

        return learnings

    def _handle_operator_feedback(self, event: WritebackEvent) -> List[Learning]:
        """Capture direct operator input as confirmed learnings.

        Operator feedback is the most authoritative source because the
        operator is explicitly telling the system something.  These are
        always auto-written with "confirmed" confidence.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)

        feedback_text = data.get("feedback", "")
        feedback_category = data.get("feedback_category", "general")
        channel = data.get("channel")
        content_type = data.get("content_type")

        # Map feedback category to a learning category
        category_map = {
            "brand_voice": LearningCategory.BRAND_PREFERENCE.value,
            "tone": LearningCategory.BRAND_PREFERENCE.value,
            "style": LearningCategory.BRAND_PREFERENCE.value,
            "channel": LearningCategory.CHANNEL_INSIGHT.value,
            "audience": LearningCategory.AUDIENCE_INSIGHT.value,
            "offer": LearningCategory.OFFER_PERFORMANCE.value,
            "compliance": LearningCategory.COMPLIANCE_CONSTRAINT.value,
            "business": LearningCategory.BUSINESS_FACT.value,
            "fact": LearningCategory.BUSINESS_FACT.value,
        }
        learning_category = category_map.get(
            feedback_category,
            LearningCategory.OPERATOR_PREFERENCE.value,
        )

        # Build a concise title from the feedback
        title_text = feedback_text[:80] + "..." if len(feedback_text) > 80 else feedback_text

        learning = Learning(
            id=_new_learning_id(),
            business_id=event.business_id,
            category=learning_category,
            trigger=WritebackTrigger.OPERATOR_FEEDBACK.value,
            title=f"Operator says: {title_text}",
            finding=(
                f"Direct operator feedback"
                f"{f' ({feedback_category})' if feedback_category != 'general' else ''}: "
                f"{feedback_text}"
            ),
            confidence=LearningConfidence.CONFIRMED.value,
            evidence={
                "source_action_id": event.action_id,
                "feedback_text": feedback_text,
                "feedback_category": feedback_category,
            },
            source_action_id=event.action_id,
            source_type="operator_feedback",
            tags=tags + ["operator_feedback", feedback_category],
            channel=channel,
            content_type=content_type,
            created_at=now,
            requires_confirmation=False,
        )

        return [learning]

    def _handle_compliance_violation(self, event: WritebackEvent) -> List[Learning]:
        """Record a compliance violation as a hard constraint.

        Compliance violations are non-negotiable constraints -- the
        system must never repeat them.  These are always auto-written
        with "confirmed" confidence because compliance is binary.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)

        rule_id = data.get("rule_id", "unknown_rule")
        violation_description = data.get("violation_description", "")
        remediation = data.get("remediation", "")
        platform = data.get("platform", "")
        channel = data.get("channel")
        content_type = data.get("content_type")
        severity = data.get("severity", "high")

        learning = Learning(
            id=_new_learning_id(),
            business_id=event.business_id,
            category=LearningCategory.COMPLIANCE_CONSTRAINT.value,
            trigger=WritebackTrigger.COMPLIANCE_VIOLATION.value,
            title=f"Compliance violation: {rule_id}",
            finding=(
                f"Compliance violation detected ({rule_id})"
                f"{f' on {platform}' if platform else ''}: "
                f"{violation_description}."
                f"{f' Remediation: {remediation}.' if remediation else ''}"
                f" This is a hard constraint -- never repeat this pattern."
            ),
            confidence=LearningConfidence.CONFIRMED.value,
            evidence={
                "source_action_id": event.action_id,
                "rule_id": rule_id,
                "violation_description": violation_description,
                "remediation": remediation,
                "platform": platform,
                "severity": severity,
            },
            source_action_id=event.action_id,
            source_type="compliance",
            tags=tags + ["compliance", "violation", rule_id, severity],
            channel=channel,
            content_type=content_type,
            created_at=now,
            requires_confirmation=False,
        )

        return [learning]

    def _handle_creative_scored(self, event: WritebackEvent) -> List[Learning]:
        """Record quality gate results as creative performance learnings.

        Tracks which content patterns score highest on the Four U's and
        other quality gates so the system can learn which structures and
        approaches produce the best-scoring content.

        Confidence: "observed" -- gate scores are objective but a single
        data point does not establish a pattern.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)

        channel = data.get("channel")
        content_type = data.get("content_type")
        action_type = data.get("action_type", "unknown")
        title = data.get("title", "Untitled content")

        # Four U's scores
        four_us_score = data.get("four_us_score")
        four_us_breakdown = data.get("four_us_breakdown", {})
        banned_word_pass = data.get("banned_word_pass")
        seo_lint_pass = data.get("seo_lint_pass")
        overall_pass = data.get("overall_pass", True)

        score_details: List[str] = []
        if four_us_score is not None:
            score_details.append(f"Four U's: {four_us_score}/16")
        if isinstance(four_us_breakdown, dict):
            for dimension, score in four_us_breakdown.items():
                score_details.append(f"  {dimension}: {score}/4")
        if banned_word_pass is not None:
            score_details.append(
                f"Banned words: {'PASS' if banned_word_pass else 'FAIL'}"
            )
        if seo_lint_pass is not None:
            score_details.append(
                f"SEO lint: {'PASS' if seo_lint_pass else 'FAIL'}"
            )

        score_summary = "; ".join(score_details) if score_details else "No scores available"

        # Determine if this was high-scoring (worth learning from)
        high_scoring = (
            isinstance(four_us_score, (int, float)) and four_us_score >= 14
        )

        if high_scoring:
            title_prefix = "High-quality content pattern"
        elif overall_pass:
            title_prefix = "Passing content scored"
        else:
            title_prefix = "Below-gate content pattern"

        learning = Learning(
            id=_new_learning_id(),
            business_id=event.business_id,
            category=LearningCategory.CREATIVE_PERFORMANCE.value,
            trigger=WritebackTrigger.CREATIVE_SCORED.value,
            title=f"{title_prefix}: {title}",
            finding=(
                f"Quality gates scored \"{title}\" ({action_type}): "
                f"{score_summary}. "
                f"{'This pattern produced high-quality content -- replicate it.' if high_scoring else ''}"
                f"{'This content passed all gates.' if overall_pass and not high_scoring else ''}"
                f"{'This content failed quality gates -- avoid this pattern.' if not overall_pass else ''}"
            ),
            confidence=LearningConfidence.OBSERVED.value,
            evidence={
                "source_action_id": event.action_id,
                "four_us_score": four_us_score,
                "four_us_breakdown": four_us_breakdown,
                "banned_word_pass": banned_word_pass,
                "seo_lint_pass": seo_lint_pass,
                "overall_pass": overall_pass,
                "action_type": action_type,
            },
            source_action_id=event.action_id,
            source_type="quality_gate",
            tags=tags + [
                "quality_gate",
                "high_quality" if high_scoring else ("passing" if overall_pass else "failed"),
            ],
            channel=channel,
            content_type=content_type,
            created_at=now,
            requires_confirmation=False,
        )

        return [learning]

    def _handle_watcher_finding(self, event: WritebackEvent) -> List[Learning]:
        """Record a notable finding from a watcher (automated monitor).

        Watchers (Tasks 067-072) continuously scan metrics, competitors,
        content freshness, and other signals.  When they find something
        noteworthy, it becomes a learning.

        Confidence depends on the watcher's own confidence assessment.
        High-impact watcher findings require operator confirmation.
        """
        data = event.event_data
        now = _utc_now()
        tags = _extract_tags_from_event(event)

        watcher_type = data.get("watcher_type", "unknown")
        finding_title = data.get("finding_title", "Watcher finding")
        finding_detail = data.get("finding_detail", "")
        watcher_confidence = data.get("watcher_confidence", "observed")
        severity = data.get("severity", "medium")
        channel = data.get("channel")
        content_type = data.get("content_type")
        recommended_action = data.get("recommended_action", "")

        # Map watcher type to a learning category
        watcher_category_map = {
            "metric_watcher": LearningCategory.CHANNEL_INSIGHT.value,
            "competitor_watcher": LearningCategory.AUDIENCE_INSIGHT.value,
            "content_freshness": LearningCategory.CREATIVE_PERFORMANCE.value,
            "rank_tracker": LearningCategory.CHANNEL_INSIGHT.value,
            "review_monitor": LearningCategory.BUSINESS_FACT.value,
            "social_listener": LearningCategory.AUDIENCE_INSIGHT.value,
            "ad_performance": LearningCategory.CHANNEL_INSIGHT.value,
        }
        learning_category = watcher_category_map.get(
            watcher_type,
            LearningCategory.CHANNEL_INSIGHT.value,
        )

        # Map watcher confidence to learning confidence
        confidence_map = {
            "high": LearningConfidence.CONFIRMED.value,
            "confirmed": LearningConfidence.CONFIRMED.value,
            "medium": LearningConfidence.OBSERVED.value,
            "observed": LearningConfidence.OBSERVED.value,
            "low": LearningConfidence.INFERRED.value,
            "inferred": LearningConfidence.INFERRED.value,
            "speculative": LearningConfidence.SPECULATIVE.value,
        }
        confidence = confidence_map.get(
            str(watcher_confidence).lower(),
            LearningConfidence.OBSERVED.value,
        )

        # High-severity findings from watchers need human confirmation
        requires_confirmation = severity in ("high", "critical")

        learning = Learning(
            id=_new_learning_id(),
            business_id=event.business_id,
            category=learning_category,
            trigger=WritebackTrigger.WATCHER_FINDING.value,
            title=f"Watcher ({watcher_type}): {finding_title}",
            finding=(
                f"{finding_detail}"
                f"{f' Recommended action: {recommended_action}.' if recommended_action else ''}"
            ),
            confidence=confidence,
            evidence={
                "source_action_id": event.action_id,
                "watcher_type": watcher_type,
                "finding_title": finding_title,
                "finding_detail": finding_detail,
                "watcher_confidence": watcher_confidence,
                "severity": severity,
                "recommended_action": recommended_action,
            },
            source_action_id=event.action_id,
            source_type="watcher",
            tags=tags + ["watcher", watcher_type, severity],
            channel=channel,
            content_type=content_type,
            created_at=now,
            requires_confirmation=requires_confirmation,
        )

        return [learning]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def _persist_learning(self, learning: Learning) -> None:
        """Write a learning to the appropriate category JSONL file.

        File organization: one JSONL file per ``LearningCategory``.
        Uses an atomic-write strategy so a crash mid-write does not
        corrupt the file.
        """
        category = learning.category
        file_name = f"{category}.jsonl"
        file_path = self.memory_dir / file_name
        payload = learning.model_dump()
        _append_jsonl_atomic(file_path, payload)

    # ------------------------------------------------------------------
    # Supersedence detection
    # ------------------------------------------------------------------

    def _check_for_superseded(self, new_learning: Learning) -> Optional[str]:
        """Check whether *new_learning* contradicts or updates an existing one.

        Looks for existing learnings in the same category, for the same
        business, that address the same topic (matched by overlapping
        tags and channel).  If a contradiction is found, the old learning
        is marked as superseded.

        Returns
        -------
        str or None
            The ``id`` of the superseded learning, or ``None``.
        """
        category = new_learning.category
        file_path = self.memory_dir / f"{category}.jsonl"
        existing_records = _read_jsonl(file_path)

        if not existing_records:
            return None

        new_tags_set = set(new_learning.tags)
        superseded_id: Optional[str] = None

        for idx, record in enumerate(existing_records):
            # Must be same business
            if record.get("business_id") != new_learning.business_id:
                continue

            # Must not already be superseded
            if record.get("superseded_by"):
                continue

            # Check for topical overlap: same channel + overlapping tags
            same_channel = (
                record.get("channel") == new_learning.channel
                and new_learning.channel is not None
            )
            old_tags_set = set(record.get("tags", []))
            # Exclude generic tags from overlap calculation
            generic_tags = {
                "approved", "rejected", "executed", "dismissed",
                "compliance", "violation", "quality_gate", "watcher",
                "operator_feedback", "winner", "above_target",
                "underperformer", "below_target", "high_quality",
                "passing", "failed",
            }
            meaningful_new = new_tags_set - generic_tags
            meaningful_old = old_tags_set - generic_tags
            tag_overlap = meaningful_new & meaningful_old

            # Need same channel AND at least 2 meaningful overlapping tags
            if not (same_channel and len(tag_overlap) >= 2):
                continue

            # Check for contradiction patterns
            is_contradiction = False

            # Approval vs. rejection contradiction
            new_is_rejection = new_learning.trigger == WritebackTrigger.ACTION_REJECTED.value
            old_is_approval = record.get("trigger") == WritebackTrigger.ACTION_APPROVED.value
            if new_is_rejection and old_is_approval:
                is_contradiction = True

            # Opposite performance signals
            new_is_underperformer = "underperformer" in new_tags_set or "below_target" in new_tags_set
            old_is_winner = "winner" in old_tags_set or "above_target" in old_tags_set
            if new_is_underperformer and old_is_winner:
                is_contradiction = True

            new_is_winner = "winner" in new_tags_set or "above_target" in new_tags_set
            old_is_underperformer = "underperformer" in old_tags_set or "below_target" in old_tags_set
            if new_is_winner and old_is_underperformer:
                is_contradiction = True

            # Same source type updating an older learning in the same category
            if (
                record.get("source_type") == new_learning.source_type
                and record.get("category") == new_learning.category
                and new_learning.source_type in ("operator_feedback", "rejection")
            ):
                is_contradiction = True

            if is_contradiction:
                # Mark the old record as superseded
                existing_records[idx]["superseded_by"] = new_learning.id
                superseded_id = record.get("id")
                # Rewrite the file with the updated records
                _rewrite_jsonl_atomic(file_path, existing_records)
                break

        return superseded_id
