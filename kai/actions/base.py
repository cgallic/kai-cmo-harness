"""Abstract Action base class, lifecycle state machine, and result model.

Every concrete action (website update, SEO fix, tracking change) inherits
from :class:`Action` and implements the four-phase lifecycle:
validate -> preview -> (approve) -> execute -> verify.

The lifecycle is enforced via :class:`ActionLifecycleState` transitions.
No mutation can occur without explicit approval, and every mutation
records before/after snapshots for rollback.
"""

from __future__ import annotations

import enum
from abc import ABC, abstractmethod
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Lifecycle State
# ---------------------------------------------------------------------------


class ActionLifecycleState(str, enum.Enum):
    """Lifecycle states for an executable action.

    Transitions:
        created -> validated -> previewed -> approved -> executing -> completed
                                                                   -> failed
        completed -> rolled_back
        (any state before executing) -> cancelled
    """

    created = "created"
    validated = "validated"
    previewed = "previewed"
    approved = "approved"
    executing = "executing"
    completed = "completed"
    failed = "failed"
    rolled_back = "rolled_back"
    cancelled = "cancelled"


# ---------------------------------------------------------------------------
# ActionResult
# ---------------------------------------------------------------------------


@dataclass
class ActionResult:
    """Standard result envelope returned by every lifecycle method.

    Parameters
    ----------
    success : bool
        Whether the operation succeeded.
    action_id : str
        The action this result refers to.
    state : str
        Current ``ActionLifecycleState`` value after the operation.
    message : str
        Human-readable summary of the outcome.
    before_state : dict or None
        Snapshot of the target before execution (used for rollback).
    after_state : dict or None
        Snapshot of the target after execution.
    errors : list of str
        Error messages when ``success`` is False.
    warnings : list of str
        Non-fatal warning messages.
    timestamp : str or None
        ISO-8601 timestamp of when the result was produced.
    metadata : dict
        Catch-all bag for preview diffs, tracking info, etc.
    """

    success: bool
    action_id: str
    state: str
    message: str
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.timestamp is None:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Abstract Action
# ---------------------------------------------------------------------------


class Action(ABC):
    """Abstract base class for all executable actions.

    Concrete subclasses must implement the four lifecycle methods:
    ``validate``, ``preview``, ``execute``, and ``verify``.

    Parameters
    ----------
    action_id : str
        Unique identifier for this action instance.
    source_proposal_id : str
        Links back to the ``ProposedAction`` that spawned this action.
    reason : str
        Human-readable reason (from ``ProposedAction.reason``).
    connector : object or None
        CMS connector instance. Can be set later before execution.
    """

    def __init__(
        self,
        action_id: str,
        source_proposal_id: str,
        reason: str,
        connector: Optional[Any] = None,
    ) -> None:
        self.action_id = action_id
        self.source_proposal_id = source_proposal_id
        self.reason = reason
        self.connector = connector
        self.state = ActionLifecycleState.created
        self.created_at: str = _utc_now()
        self._before_snapshot: Optional[Dict[str, Any]] = None
        self._preview_result: Optional[ActionResult] = None

    # ------------------------------------------------------------------
    # Abstract lifecycle methods
    # ------------------------------------------------------------------

    @abstractmethod
    def validate(self) -> ActionResult:
        """Phase 1: Check parameters, verify target exists, assess safety.

        Must transition state to ``validated`` on success.
        """

    @abstractmethod
    def preview(self) -> ActionResult:
        """Phase 2: Generate a diff / description of the planned change.

        Must transition state to ``previewed`` on success.
        Should capture a before-snapshot when connector is available.
        """

    @abstractmethod
    def execute(self) -> ActionResult:
        """Phase 3: Apply the change via the CMS connector.

        Must be in ``approved`` state to proceed.
        Must transition state to ``completed`` or ``failed``.
        Must store before_state for rollback.
        """

    @abstractmethod
    def verify(self) -> ActionResult:
        """Phase 4: Read back the target and confirm the change took effect.

        Returns an ActionResult indicating verification success/failure.
        """

    # ------------------------------------------------------------------
    # Concrete lifecycle methods
    # ------------------------------------------------------------------

    def approve(self) -> None:
        """Approve the action for execution.

        Can only be called when state is ``previewed``.

        Raises
        ------
        RuntimeError
            If the current state is not ``previewed``.
        """
        if self.state != ActionLifecycleState.previewed:
            raise RuntimeError(
                f"Cannot approve action in state '{self.state.value}'. "
                f"Action must be in 'previewed' state."
            )
        self.state = ActionLifecycleState.approved

    def cancel(self) -> None:
        """Cancel the action before execution begins.

        Can be called in any state before ``executing``.

        Raises
        ------
        RuntimeError
            If the action is already executing or beyond.
        """
        non_cancellable = {
            ActionLifecycleState.executing,
            ActionLifecycleState.completed,
            ActionLifecycleState.failed,
            ActionLifecycleState.rolled_back,
        }
        if self.state in non_cancellable:
            raise RuntimeError(
                f"Cannot cancel action in state '{self.state.value}'. "
                f"Action is already executing or beyond."
            )
        self.state = ActionLifecycleState.cancelled

    def rollback(self) -> ActionResult:
        """Restore the target to its state before execution.

        Can only be called when state is ``completed``.

        Returns
        -------
        ActionResult
            Result of the rollback operation.

        Raises
        ------
        RuntimeError
            If the action is not in ``completed`` state or if no
            before-snapshot was captured.
        """
        if self.state != ActionLifecycleState.completed:
            raise RuntimeError(
                f"Cannot rollback action in state '{self.state.value}'. "
                f"Action must be in 'completed' state."
            )

        if self._before_snapshot is None:
            return ActionResult(
                success=False,
                action_id=self.action_id,
                state=self.state.value,
                message="Rollback failed: no before-state snapshot was captured.",
                errors=["No before-state snapshot available for rollback."],
            )

        if self.connector is None:
            return ActionResult(
                success=False,
                action_id=self.action_id,
                state=self.state.value,
                message="Rollback failed: no CMS connector available.",
                errors=["CMS connector is not set."],
            )

        try:
            self._apply_rollback(self._before_snapshot)
            self.state = ActionLifecycleState.rolled_back
            return ActionResult(
                success=True,
                action_id=self.action_id,
                state=self.state.value,
                message="Action rolled back successfully.",
                before_state=self._before_snapshot,
            )
        except Exception as exc:
            return ActionResult(
                success=False,
                action_id=self.action_id,
                state=self.state.value,
                message=f"Rollback failed: {exc}",
                errors=[str(exc)],
            )

    def _apply_rollback(self, before_snapshot: Dict[str, Any]) -> None:
        """Restore state from a before-snapshot via the connector.

        Subclasses can override for custom rollback logic.
        The default implementation restores page section content and metadata
        based on the snapshot structure.
        """
        # If the snapshot contains section-level data, restore the section
        if "page_id" in before_snapshot and "section_id" in before_snapshot:
            self.connector.update_page_section(
                before_snapshot["page_id"],
                before_snapshot["section_id"],
                before_snapshot.get("content", ""),
                content_type=before_snapshot.get("content_type", "html"),
            )
        # If the snapshot contains metadata, restore it
        elif "page_id" in before_snapshot and "metadata" in before_snapshot:
            self.connector.update_metadata(
                before_snapshot["page_id"],
                before_snapshot["metadata"],
            )

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the action to a dict for storage and logging.

        Returns
        -------
        dict
            Complete action state including lifecycle info.
        """
        return {
            "action_id": self.action_id,
            "action_type": self.__class__.__name__,
            "source_proposal_id": self.source_proposal_id,
            "reason": self.reason,
            "state": self.state.value,
            "created_at": self.created_at,
            "has_connector": self.connector is not None,
            "before_snapshot": self._before_snapshot,
            "preview_result": (
                self._preview_result.to_dict() if self._preview_result else None
            ),
        }

    # ------------------------------------------------------------------
    # State-transition guards used by subclasses
    # ------------------------------------------------------------------

    def _require_state(self, required: ActionLifecycleState, operation: str) -> None:
        """Raise RuntimeError if the current state does not match *required*."""
        if self.state != required:
            raise RuntimeError(
                f"Cannot {operation} in state '{self.state.value}'. "
                f"Required state: '{required.value}'."
            )

    def _require_connector(self, operation: str) -> None:
        """Raise RuntimeError if no connector is set."""
        if self.connector is None:
            raise RuntimeError(
                f"Cannot {operation}: no CMS connector is set on this action."
            )

    def _fail_result(self, message: str, errors: Optional[List[str]] = None) -> ActionResult:
        """Build a failure ActionResult preserving the current state."""
        return ActionResult(
            success=False,
            action_id=self.action_id,
            state=self.state.value,
            message=message,
            errors=errors or [message],
        )

    def _success_result(
        self,
        message: str,
        *,
        before_state: Optional[Dict[str, Any]] = None,
        after_state: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        warnings: Optional[List[str]] = None,
    ) -> ActionResult:
        """Build a success ActionResult with the current state."""
        return ActionResult(
            success=True,
            action_id=self.action_id,
            state=self.state.value,
            message=message,
            before_state=before_state,
            after_state=after_state,
            metadata=metadata or {},
            warnings=warnings or [],
        )
