"""Canonical result from executing an action through a connector."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from kai.runtime.models import SerializableModel


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class ExecutionResult(SerializableModel):
    """Result returned by the ActionExecutor after dispatching to a connector.

    Attributes:
        action_id: The action that was executed.
        success: Whether the connector call succeeded.
        connector_type: Which connector ran (e.g., "wordpress", "ga4").
        method_called: The connector method that was invoked.
        response_data: Structured data returned by the connector.
        error: Error message if success is False.
        duration_ms: Wall-clock time for the connector call.
        dry_run: True if the connector was in dry-run/sandbox mode.
        before_state: Snapshot captured before mutation (for rollback).
        after_state: State after mutation (for verification).
        timestamp: ISO timestamp of execution.
    """

    action_id: str = ""
    success: bool = False
    connector_type: str = ""
    method_called: str = ""
    response_data: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    duration_ms: float = 0.0
    dry_run: bool = False
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    timestamp: str = field(default_factory=_utc_now)
