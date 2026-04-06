"""Revision workflows and kill switches for the Kai Marketing OS.

When an operator rejects a proposed action, the revision workflow captures
the rejection context, tracks revision cycles, and enforces a maximum retry
limit to prevent infinite loops.  The kill switch system provides emergency
controls -- an operator can pause everything instantly when something goes
wrong (compliance issue, budget overrun, brand crisis).

Together these are the safety mechanisms that give operators confidence in
an autonomous marketing system.

Usage::

    from kai.compliance.revision import (
        RevisionWorkflow,
        KillSwitch,
        Rejection,
        RejectionCategory,
        create_operator_override,
    )

    # Reject an action with context
    rejection = Rejection(
        id="rej_abc123def456",
        action_id="act_abc123",
        rejected_by="connor",
        rejected_at="2026-04-02T12:00:00+00:00",
        category=RejectionCategory.brand_voice.value,
        reason="Headline too aggressive for our brand",
        specific_issues=["headline too aggressive", "CTA doesn't match brand"],
    )

    workflow = RevisionWorkflow(max_cycles=3)
    attempt = workflow.handle_rejection("act_abc123", rejection, original_data)

    # Emergency stop
    ks = KillSwitch()
    activation = ks.emergency_stop("operator", "Brand crisis detected")

Design notes
------------
- Uses dataclass + SerializableModel pattern from ``kai/runtime/models.py``.
- ProposedAction is typed as ``Any`` to avoid circular imports.
- No external dependencies beyond stdlib.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Serialization helper (matches kai.runtime.models.SerializableModel)
# ---------------------------------------------------------------------------


class SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# ID and timestamp helpers
# ---------------------------------------------------------------------------


def _new_id(prefix: str) -> str:
    """Generate a prefixed unique ID using 12 hex characters."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


# ============================================================================
# Enums
# ============================================================================


class RejectionCategory(str, Enum):
    """Why the operator rejected the proposed action."""

    brand_voice = "brand_voice"
    """Tone, style, or voice doesn't match brand."""

    compliance = "compliance"
    """Legal or platform compliance concern."""

    strategy = "strategy"
    """Doesn't align with current business strategy."""

    timing = "timing"
    """Wrong time for this action (seasonal, business cycle)."""

    budget = "budget"
    """Budget concern or prioritization issue."""

    quality = "quality"
    """Content quality insufficient."""

    accuracy = "accuracy"
    """Factual inaccuracy or outdated information."""

    other = "other"
    """Doesn't fit other categories."""


class KillSwitchScope(str, Enum):
    """What gets frozen when a kill switch is activated."""

    all = "all"
    """Freeze all actions for all businesses."""

    business = "business"
    """Freeze all actions for a specific business."""

    channel = "channel"
    """Freeze all actions for a specific channel."""

    campaign = "campaign"
    """Freeze a specific campaign."""

    action_type = "action_type"
    """Freeze all actions of a specific type."""


class SystemStatus(str, Enum):
    """Overall system operating mode."""

    active = "active"
    """System operating normally."""

    paused = "paused"
    """System paused, no new actions executing."""

    emergency_stop = "emergency_stop"
    """Everything frozen, operator alerted."""

    maintenance = "maintenance"
    """System in maintenance mode."""


# ============================================================================
# Models
# ============================================================================


@dataclass
class Rejection(SerializableModel):
    """Structured record of an operator rejecting a proposed action.

    Captures the rejection category, free-text reason, specific issues,
    and optional guidance for the revision engine.  If ``do_not_retry``
    is True, the system will not attempt a revision.
    """

    id: str
    """Format ``rej_{uuid_hex[:12]}``."""

    action_id: str
    """The rejected ProposedAction."""

    rejected_by: str
    """Operator name or identifier."""

    rejected_at: str
    """ISO timestamp of rejection."""

    category: str
    """RejectionCategory enum value."""

    reason: str
    """Free-text explanation from the operator."""

    specific_issues: List[str] = field(default_factory=list)
    """Specific things wrong (e.g., 'headline too aggressive')."""

    revision_guidance: Optional[str] = None
    """Operator's guidance for the revision engine."""

    do_not_retry: bool = False
    """If True, do not attempt revision -- kill this action."""


@dataclass
class RevisionAttempt(SerializableModel):
    """A single attempt to revise a rejected action.

    Tracks the revision number within the cycle, the specific changes
    made, the revised content, and the current review status.
    """

    id: str
    """Format ``rev_{uuid_hex[:12]}``."""

    action_id: str
    """Original action being revised."""

    revision_number: int
    """Revision cycle number: 1, 2, 3 ..."""

    rejection_id: str
    """Which Rejection triggered this revision."""

    changes_made: List[str] = field(default_factory=list)
    """List of specific changes in this revision."""

    revised_content: Dict[str, Any] = field(default_factory=dict)
    """The new content or configuration."""

    created_at: str = ""
    """ISO timestamp."""

    status: str = "pending_review"
    """One of: pending_review, approved, rejected, escalated."""


@dataclass
class RevisionHistory(SerializableModel):
    """Complete revision history for a single action.

    Maintains the original version, all rejections, all revision attempts,
    and the current lifecycle status.
    """

    action_id: str
    """The action being tracked."""

    original_version: Dict[str, Any] = field(default_factory=dict)
    """The original proposed action content."""

    rejections: List[Rejection] = field(default_factory=list)
    """Ordered list of rejections."""

    revisions: List[RevisionAttempt] = field(default_factory=list)
    """Ordered list of revision attempts."""

    current_status: str = "pending"
    """One of: pending, approved, exhausted, killed."""

    total_revision_cycles: int = 0
    """How many revision cycles have been attempted."""

    max_revision_cycles: int = 3
    """Maximum allowed revision cycles before escalation."""


@dataclass
class KillSwitchActivation(SerializableModel):
    """Record of a kill switch being activated.

    Captures the scope, who activated it, why, what triggered it,
    and tracks deactivation when the switch is lifted.
    """

    id: str
    """Format ``kill_{uuid_hex[:12]}``."""

    scope: str
    """KillSwitchScope enum value."""

    scope_target: Optional[str] = None
    """The specific business_id, channel, campaign_id, or action_type."""

    activated_by: str = ""
    """One of: operator, system, compliance_engine, spend_monitor, anomaly_detector."""

    activated_at: str = ""
    """ISO timestamp of activation."""

    reason: str = ""
    """Why the kill switch was activated."""

    trigger_event: Optional[str] = None
    """What triggered this (e.g., spend_threshold_exceeded)."""

    deactivated_at: Optional[str] = None
    """When it was lifted (None if still active)."""

    deactivated_by: Optional[str] = None
    """Who lifted the switch."""

    deactivation_reason: Optional[str] = None
    """Why it was lifted."""

    affected_action_ids: List[str] = field(default_factory=list)
    """Actions that were paused by this kill switch."""


@dataclass
class OperatorOverride(SerializableModel):
    """Record of an operator overriding a system decision.

    Captures the override type, what the system decided versus what
    the operator decided, and requires explicit risk acknowledgment
    for compliance bypass overrides.
    """

    id: str
    """Format ``ovr_{uuid_hex[:12]}``."""

    action_id: str
    """The action being overridden."""

    override_type: str
    """One of: force_approve, force_reject, change_route, change_priority, bypass_compliance."""

    original_decision: str
    """What the system decided."""

    override_decision: str
    """What the operator decided instead."""

    reason: str
    """Documented reason for the override."""

    overridden_by: str
    """Operator name or identifier."""

    overridden_at: str = ""
    """ISO timestamp."""

    acknowledged_risk: bool = False
    """Operator acknowledged any compliance or risk implications."""


# ============================================================================
# RevisionWorkflow
# ============================================================================


_VALID_OVERRIDE_TYPES = frozenset({
    "force_approve",
    "force_reject",
    "change_route",
    "change_priority",
    "bypass_compliance",
})


class RevisionWorkflow:
    """Manages the rejection-to-revision cycle for proposed marketing actions.

    Tracks revision history per action, enforces a maximum number of
    revision cycles, and provides escalation logic when revisions are
    exhausted or the operator's feedback is contradictory.

    Parameters
    ----------
    max_cycles : int
        Maximum number of revision cycles before escalation (default 3).
    """

    def __init__(self, max_cycles: int = 3) -> None:
        self._max_cycles = max_cycles
        self._histories: Dict[str, RevisionHistory] = {}

    # ------------------------------------------------------------------
    # Core workflow
    # ------------------------------------------------------------------

    def handle_rejection(
        self,
        action_id: str,
        rejection: Rejection,
        action_data: Dict[str, Any],
    ) -> Optional[RevisionAttempt]:
        """Handle an operator rejection and optionally create a revision attempt.

        If the rejection has ``do_not_retry=True``, the action is marked
        as killed and no revision is created.  If the maximum number of
        revision cycles has been reached, the action is marked as
        exhausted and escalated.

        Parameters
        ----------
        action_id : str
            The action being rejected.
        rejection : Rejection
            The structured rejection from the operator.
        action_data : dict
            The current action content (original or most recent revision).

        Returns
        -------
        RevisionAttempt or None
            A new revision attempt for the creative engine to fill, or
            None if the action was killed or revision cycles are exhausted.
        """
        history = self._get_or_create_history(action_id, action_data)
        history.rejections.append(rejection)

        # Operator explicitly said "do not retry"
        if rejection.do_not_retry:
            history.current_status = "killed"
            return None

        # Check if max revision cycles exceeded
        if history.total_revision_cycles >= history.max_revision_cycles:
            history.current_status = "exhausted"
            return None

        # Create a new revision attempt
        history.total_revision_cycles += 1
        attempt = RevisionAttempt(
            id=_new_id("rev"),
            action_id=action_id,
            revision_number=history.total_revision_cycles,
            rejection_id=rejection.id,
            changes_made=[],
            revised_content=self.create_revision_context(rejection, action_data),
            created_at=_now_iso(),
            status="pending_review",
        )
        history.revisions.append(attempt)
        history.current_status = "pending"
        return attempt

    def create_revision_context(
        self,
        rejection: Rejection,
        original_content: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Build a context dict that the creative engine can consume.

        Includes the original content, rejection details, and a list of
        content keys that were NOT flagged (so the engine preserves what
        is working).

        Parameters
        ----------
        rejection : Rejection
            The structured rejection.
        original_content : dict
            The rejected content.

        Returns
        -------
        dict
            Context dict with original_content, rejection details, and
            a do_not_change list.
        """
        # Determine which content keys were NOT flagged as issues.
        # We consider a key "flagged" if any specific issue substring
        # matches the key name (case-insensitive).
        all_keys = list(original_content.keys())
        flagged_keys: List[str] = []
        for key in all_keys:
            for issue in rejection.specific_issues:
                if key.lower() in issue.lower() or issue.lower() in key.lower():
                    flagged_keys.append(key)
                    break

        do_not_change = [k for k in all_keys if k not in flagged_keys]

        return {
            "original_content": original_content,
            "rejection_category": rejection.category,
            "rejection_reason": rejection.reason,
            "specific_issues": list(rejection.specific_issues),
            "revision_guidance": rejection.revision_guidance,
            "do_not_change": do_not_change,
        }

    def get_revision_history(self, action_id: str) -> RevisionHistory:
        """Retrieve or construct the revision history for an action.

        If no history exists yet, returns a new empty RevisionHistory.

        Parameters
        ----------
        action_id : str
            The action to look up.

        Returns
        -------
        RevisionHistory
            The revision history for the action.
        """
        if action_id in self._histories:
            return self._histories[action_id]
        # Return a new history object (not yet tracked)
        history = RevisionHistory(
            action_id=action_id,
            max_revision_cycles=self._max_cycles,
        )
        self._histories[action_id] = history
        return history

    def should_escalate(self, action_id: str) -> bool:
        """Determine whether an action should be escalated.

        Returns True if:
        - Revision cycles are exhausted (>= max_cycles).
        - Multiple rejections have different categories (unclear what
          the operator wants).

        Parameters
        ----------
        action_id : str
            The action to check.

        Returns
        -------
        bool
            True if the action should be escalated.
        """
        if action_id not in self._histories:
            return False

        history = self._histories[action_id]

        # Exhausted cycles
        if history.total_revision_cycles >= history.max_revision_cycles:
            return True

        # Conflicting rejection categories -- if 2+ rejections have
        # different categories, the operator's feedback is ambiguous
        if len(history.rejections) >= 2:
            categories = {r.category for r in history.rejections}
            if len(categories) >= 2:
                return True

        return False

    def build_escalation_summary(self, history: RevisionHistory) -> str:
        """Generate a human-readable summary for escalation.

        Includes the original action, each rejection with reason, each
        revision with changes, and a recommendation.

        Parameters
        ----------
        history : RevisionHistory
            The complete revision history for the action.

        Returns
        -------
        str
            A formatted escalation summary.
        """
        lines: List[str] = []
        lines.append(f"ESCALATION SUMMARY for action {history.action_id}")
        lines.append("=" * 60)
        lines.append("")

        # Original version
        lines.append("ORIGINAL VERSION:")
        if history.original_version:
            for key, value in history.original_version.items():
                val_str = str(value)
                if len(val_str) > 200:
                    val_str = val_str[:200] + "..."
                lines.append(f"  {key}: {val_str}")
        else:
            lines.append("  (no original version recorded)")
        lines.append("")

        # Rejections and revisions interleaved chronologically
        lines.append(f"REVISION HISTORY ({history.total_revision_cycles} cycle(s) of "
                      f"{history.max_revision_cycles} max):")
        lines.append("-" * 40)

        for i, rejection in enumerate(history.rejections, 1):
            lines.append(f"  Rejection #{i}:")
            lines.append(f"    Category: {rejection.category}")
            lines.append(f"    Reason: {rejection.reason}")
            lines.append(f"    Rejected by: {rejection.rejected_by} at {rejection.rejected_at}")
            if rejection.specific_issues:
                lines.append(f"    Issues: {', '.join(rejection.specific_issues)}")
            if rejection.revision_guidance:
                lines.append(f"    Guidance: {rejection.revision_guidance}")
            if rejection.do_not_retry:
                lines.append("    DO NOT RETRY flag set")
            lines.append("")

            # Find the revision attempt triggered by this rejection
            matching_revisions = [
                r for r in history.revisions if r.rejection_id == rejection.id
            ]
            for rev in matching_revisions:
                lines.append(f"  Revision #{rev.revision_number} (status: {rev.status}):")
                if rev.changes_made:
                    for change in rev.changes_made:
                        lines.append(f"    - {change}")
                else:
                    lines.append("    (no specific changes recorded)")
                lines.append("")

        # Recommendation
        lines.append("RECOMMENDATION:")
        if history.current_status == "killed":
            lines.append("  Action was explicitly killed by operator. Do not retry.")
        elif history.current_status == "exhausted":
            lines.append("  Maximum revision cycles exhausted. Requires human re-brief "
                         "or fundamentally different approach.")
        else:
            # Check for conflicting categories
            if len(history.rejections) >= 2:
                categories = {r.category for r in history.rejections}
                if len(categories) >= 2:
                    lines.append(
                        f"  Conflicting rejection categories ({', '.join(sorted(categories))}). "
                        "Operator feedback is ambiguous -- requires a direct conversation "
                        "to clarify expectations before further revision."
                    )
                else:
                    lines.append(
                        f"  Multiple rejections in same category ({next(iter(categories))}). "
                        "The revision engine is not adequately addressing the operator's "
                        "concern. Consider a different approach or manual creation."
                    )
            else:
                lines.append("  Escalated for human review.")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_or_create_history(
        self,
        action_id: str,
        action_data: Dict[str, Any],
    ) -> RevisionHistory:
        """Get existing history or create a new one with original content."""
        if action_id in self._histories:
            return self._histories[action_id]

        history = RevisionHistory(
            action_id=action_id,
            original_version=dict(action_data),
            max_revision_cycles=self._max_cycles,
        )
        self._histories[action_id] = history
        return history


# ============================================================================
# KillSwitch
# ============================================================================


class KillSwitch:
    """Emergency control system for pausing marketing operations.

    Manages concurrent kill switch activations at different scopes
    (all, business, channel, campaign, action_type).  Tracks system
    status and provides an ``is_action_blocked`` check that other
    systems call before executing any action.
    """

    def __init__(self) -> None:
        self._active_switches: List[KillSwitchActivation] = []
        self._system_status: str = SystemStatus.active.value
        self._notification_flags: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Activation methods
    # ------------------------------------------------------------------

    def pause_all_actions(
        self,
        activated_by: str,
        reason: str,
    ) -> KillSwitchActivation:
        """Pause all actions across all businesses.

        Sets system status to ``paused``.

        Parameters
        ----------
        activated_by : str
            Who activated the switch (operator, system, etc.).
        reason : str
            Why the switch was activated.

        Returns
        -------
        KillSwitchActivation
            The activation record.
        """
        activation = KillSwitchActivation(
            id=_new_id("kill"),
            scope=KillSwitchScope.all.value,
            scope_target=None,
            activated_by=activated_by,
            activated_at=_now_iso(),
            reason=reason,
        )
        self._active_switches.append(activation)
        self._system_status = SystemStatus.paused.value
        return activation

    def pause_business(
        self,
        business_id: str,
        activated_by: str,
        reason: str,
    ) -> KillSwitchActivation:
        """Pause all actions for a specific business.

        Parameters
        ----------
        business_id : str
            The business to freeze.
        activated_by : str
            Who activated the switch.
        reason : str
            Why the switch was activated.

        Returns
        -------
        KillSwitchActivation
            The activation record.
        """
        activation = KillSwitchActivation(
            id=_new_id("kill"),
            scope=KillSwitchScope.business.value,
            scope_target=business_id,
            activated_by=activated_by,
            activated_at=_now_iso(),
            reason=reason,
        )
        self._active_switches.append(activation)
        return activation

    def pause_channel(
        self,
        channel: str,
        activated_by: str,
        reason: str,
    ) -> KillSwitchActivation:
        """Pause all actions for a specific channel.

        Parameters
        ----------
        channel : str
            The marketing channel to freeze (e.g., "email", "social").
        activated_by : str
            Who activated the switch.
        reason : str
            Why the switch was activated.

        Returns
        -------
        KillSwitchActivation
            The activation record.
        """
        activation = KillSwitchActivation(
            id=_new_id("kill"),
            scope=KillSwitchScope.channel.value,
            scope_target=channel,
            activated_by=activated_by,
            activated_at=_now_iso(),
            reason=reason,
        )
        self._active_switches.append(activation)
        return activation

    def pause_campaign(
        self,
        campaign_id: str,
        activated_by: str,
        reason: str,
    ) -> KillSwitchActivation:
        """Pause a specific campaign.

        Parameters
        ----------
        campaign_id : str
            The campaign to freeze.
        activated_by : str
            Who activated the switch.
        reason : str
            Why the switch was activated.

        Returns
        -------
        KillSwitchActivation
            The activation record.
        """
        activation = KillSwitchActivation(
            id=_new_id("kill"),
            scope=KillSwitchScope.campaign.value,
            scope_target=campaign_id,
            activated_by=activated_by,
            activated_at=_now_iso(),
            reason=reason,
        )
        self._active_switches.append(activation)
        return activation

    def pause_action_type(
        self,
        action_type: str,
        activated_by: str,
        reason: str,
    ) -> KillSwitchActivation:
        """Pause all actions of a specific type.

        Parameters
        ----------
        action_type : str
            The action type to freeze (e.g., "ad_campaign").
        activated_by : str
            Who activated the switch.
        reason : str
            Why the switch was activated.

        Returns
        -------
        KillSwitchActivation
            The activation record.
        """
        activation = KillSwitchActivation(
            id=_new_id("kill"),
            scope=KillSwitchScope.action_type.value,
            scope_target=action_type,
            activated_by=activated_by,
            activated_at=_now_iso(),
            reason=reason,
        )
        self._active_switches.append(activation)
        return activation

    def emergency_stop(
        self,
        activated_by: str,
        reason: str,
    ) -> KillSwitchActivation:
        """Trigger an emergency stop -- freeze everything and alert operator.

        Sets system status to ``emergency_stop`` and generates a
        notification flag for immediate operator alert.

        Parameters
        ----------
        activated_by : str
            Who triggered the emergency stop.
        reason : str
            Why the emergency stop was triggered.

        Returns
        -------
        KillSwitchActivation
            The activation record.
        """
        activation = KillSwitchActivation(
            id=_new_id("kill"),
            scope=KillSwitchScope.all.value,
            scope_target=None,
            activated_by=activated_by,
            activated_at=_now_iso(),
            reason=reason,
            trigger_event="emergency_stop",
        )
        self._active_switches.append(activation)
        self._system_status = SystemStatus.emergency_stop.value

        # Generate notification flag for immediate operator alert
        self._notification_flags.append({
            "type": "emergency_stop",
            "activation_id": activation.id,
            "activated_by": activated_by,
            "reason": reason,
            "timestamp": activation.activated_at,
            "requires_immediate_attention": True,
        })

        return activation

    # ------------------------------------------------------------------
    # Deactivation
    # ------------------------------------------------------------------

    def deactivate(
        self,
        activation_id: str,
        deactivated_by: str,
        reason: str,
    ) -> bool:
        """Deactivate a kill switch.

        If no other active switches remain after deactivation, sets the
        system status back to ``active``.

        Parameters
        ----------
        activation_id : str
            The kill switch activation to deactivate.
        deactivated_by : str
            Who is lifting the switch.
        reason : str
            Why the switch is being lifted.

        Returns
        -------
        bool
            True if found and deactivated, False if not found.
        """
        target: Optional[KillSwitchActivation] = None
        for switch in self._active_switches:
            if switch.id == activation_id and switch.deactivated_at is None:
                target = switch
                break

        if target is None:
            return False

        now = _now_iso()
        target.deactivated_at = now
        target.deactivated_by = deactivated_by
        target.deactivation_reason = reason

        # Check if any active switches remain
        still_active = [
            s for s in self._active_switches if s.deactivated_at is None
        ]
        if not still_active:
            self._system_status = SystemStatus.active.value

        return True

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def is_action_blocked(self, action: Any) -> Tuple[bool, Optional[str]]:
        """Check whether an action is blocked by any active kill switch.

        Checks scopes in priority order: ``all`` blocks everything,
        ``business`` blocks matching business, ``channel`` blocks
        matching channel, ``campaign`` blocks matching campaign,
        ``action_type`` blocks matching type.

        Parameters
        ----------
        action : Any
            A ProposedAction or any object with ``channel``,
            ``action_type``, ``business_id``, and ``campaign_id``
            attributes.

        Returns
        -------
        tuple of (bool, str or None)
            ``(True, reason)`` if blocked, ``(False, None)`` if not.
        """
        action_channel = getattr(action, "channel", None)
        action_type = getattr(action, "action_type", None)
        action_business_id = getattr(action, "business_id", None)
        action_campaign_id = getattr(action, "campaign_id", None)

        # Also check metadata for campaign_id if not a top-level attribute
        if action_campaign_id is None:
            metadata = getattr(action, "metadata", {})
            if isinstance(metadata, dict):
                action_campaign_id = metadata.get("campaign_id")

        for switch in self._active_switches:
            # Skip deactivated switches
            if switch.deactivated_at is not None:
                continue

            scope = switch.scope

            # "all" blocks everything
            if scope == KillSwitchScope.all.value:
                return True, f"All actions paused: {switch.reason}"

            # "business" blocks matching business
            if (
                scope == KillSwitchScope.business.value
                and switch.scope_target is not None
                and action_business_id == switch.scope_target
            ):
                return True, f"Business '{switch.scope_target}' paused: {switch.reason}"

            # "channel" blocks matching channel
            if (
                scope == KillSwitchScope.channel.value
                and switch.scope_target is not None
                and action_channel == switch.scope_target
            ):
                return True, f"Channel '{switch.scope_target}' paused: {switch.reason}"

            # "campaign" blocks matching campaign
            if (
                scope == KillSwitchScope.campaign.value
                and switch.scope_target is not None
                and action_campaign_id == switch.scope_target
            ):
                return True, f"Campaign '{switch.scope_target}' paused: {switch.reason}"

            # "action_type" blocks matching type
            if (
                scope == KillSwitchScope.action_type.value
                and switch.scope_target is not None
                and action_type == switch.scope_target
            ):
                return True, f"Action type '{switch.scope_target}' paused: {switch.reason}"

        return False, None

    def get_active_switches(self) -> List[KillSwitchActivation]:
        """Return all currently active kill switches.

        Returns
        -------
        list of KillSwitchActivation
            Switches where ``deactivated_at`` is None.
        """
        return [s for s in self._active_switches if s.deactivated_at is None]

    def get_system_status(self) -> str:
        """Return the current system status.

        Returns
        -------
        str
            A SystemStatus enum value.
        """
        return self._system_status

    def get_notification_flags(self) -> List[Dict[str, Any]]:
        """Return and clear pending notification flags.

        Returns
        -------
        list of dict
            Notification flags generated by emergency_stop or other
            critical events.  Once read, the flags are cleared.
        """
        flags = list(self._notification_flags)
        self._notification_flags.clear()
        return flags


# ============================================================================
# Operator Override factory
# ============================================================================


def create_operator_override(
    action_id: str,
    override_type: str,
    original_decision: str,
    override_decision: str,
    reason: str,
    overridden_by: str,
    risk_acknowledgment: bool = False,
) -> OperatorOverride:
    """Create an OperatorOverride record.

    Validates that the override type is one of the allowed values.
    If the override type is ``bypass_compliance``, requires explicit
    ``risk_acknowledgment=True``.

    Parameters
    ----------
    action_id : str
        The action being overridden.
    override_type : str
        One of: force_approve, force_reject, change_route,
        change_priority, bypass_compliance.
    original_decision : str
        What the system decided.
    override_decision : str
        What the operator decided instead.
    reason : str
        Documented reason for the override.
    overridden_by : str
        Operator name or identifier.
    risk_acknowledgment : bool
        Must be True for bypass_compliance overrides.

    Returns
    -------
    OperatorOverride
        The override record.

    Raises
    ------
    ValueError
        If override_type is not valid, or if bypass_compliance is
        requested without risk acknowledgment.
    """
    if override_type not in _VALID_OVERRIDE_TYPES:
        raise ValueError(
            f"Invalid override_type '{override_type}'. "
            f"Must be one of: {', '.join(sorted(_VALID_OVERRIDE_TYPES))}"
        )

    if override_type == "bypass_compliance" and not risk_acknowledgment:
        raise ValueError(
            "bypass_compliance override requires risk_acknowledgment=True. "
            "The operator must explicitly acknowledge the compliance risk."
        )

    return OperatorOverride(
        id=_new_id("ovr"),
        action_id=action_id,
        override_type=override_type,
        original_decision=original_decision,
        override_decision=override_decision,
        reason=reason,
        overridden_by=overridden_by,
        overridden_at=_now_iso(),
        acknowledged_risk=risk_acknowledgment,
    )
