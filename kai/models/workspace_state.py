"""Connected workspace state model for the Kai Marketing OS.

A BusinessProfile describes what a business IS.  WorkspaceState describes
what the system CAN DO right now for that business -- which integrations
are connected, what permissions the system has, what budgets are set, and
what the operator has approved for automatic execution.

This is the live operational layer that changes as integrations are
connected/disconnected and operator preferences evolve.  The workspace
state persists to disk so it survives between sessions.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
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

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ---------------------------------------------------------------------------
# YAML import with JSON fallback
# ---------------------------------------------------------------------------

try:
    import yaml as _yaml
except ImportError:  # pragma: no cover
    _yaml = None


def _serialize_to_string(data: dict) -> str:
    """Serialize a dict to YAML string, falling back to JSON if PyYAML
    is not installed."""
    if _yaml is not None:
        return _yaml.safe_dump(data, default_flow_style=False, sort_keys=False)
    import json
    return json.dumps(data, indent=2, sort_keys=False, default=str)


def _deserialize_from_string(text: str, file_path: str) -> dict:
    """Deserialize a YAML or JSON string back to a dict."""
    if _yaml is not None:
        return _yaml.safe_load(text) or {}
    import json
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        raise ValueError(
            f"Cannot parse {file_path}. Install PyYAML (`pip install pyyaml`) "
            "for YAML support, or ensure the file contains valid JSON."
        )


def _get_file_extension() -> str:
    """Return the preferred file extension based on available serializer."""
    return ".yaml" if _yaml is not None else ".json"


# ============================================================================
# Sub-models
# ============================================================================


class Integration(BaseModel):
    """A single platform integration and its current connection state."""

    platform_name: str
    connection_type: Optional[str] = None  # "oauth", "api_key", "webhook", "manual", "mcp"
    status: str = "disconnected"  # "connected", "expired", "pending", "disconnected", "error"
    capabilities: List[str] = Field(default_factory=list)
    scopes: List[str] = Field(default_factory=list)
    connected_at: Optional[str] = None  # ISO timestamp
    last_sync: Optional[str] = None  # ISO timestamp
    expires_at: Optional[str] = None  # ISO timestamp
    account_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BudgetConstraint(BaseModel):
    """Spending limits and tracking for the workspace."""

    daily_cap: Optional[float] = None
    weekly_cap: Optional[float] = None
    monthly_cap: Optional[float] = None
    per_action_cap: Optional[float] = None
    total_spent_this_month: float = 0.0
    last_reset_date: Optional[str] = None  # ISO date


class ApprovalDefaults(BaseModel):
    """Default approval workflow rules for the workspace."""

    auto_approve_below: Optional[float] = None  # USD threshold
    require_human_for: List[str] = Field(default_factory=list)
    auto_approve_types: List[str] = Field(default_factory=list)
    escalation_channel: Optional[str] = None  # "discord", "email", "slack"
    escalation_contact: Optional[str] = None
    max_auto_actions_per_day: Optional[int] = None


class ChannelEnablement(BaseModel):
    """Activation status and readiness for a single marketing channel."""

    channel: str
    is_enabled: bool = False
    is_configured: bool = False
    missing_prerequisites: List[str] = Field(default_factory=list)
    priority: Optional[int] = None  # 1 = highest
    notes: Optional[str] = None


class OperatorPreferences(BaseModel):
    """Human operator preferences and availability settings."""

    notification_channel: Optional[str] = None
    active_hours: Optional[str] = None  # e.g. "9am-5pm EST"
    response_time_expectation: Optional[str] = None  # "same-day", "within-1-hour", etc.
    preferred_report_frequency: Optional[str] = None  # "daily", "weekly", "monthly"
    language: str = "en"
    timezone: str = "America/New_York"
    custom_preferences: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Top-level WorkspaceState
# ============================================================================


class WorkspaceState(BaseModel):
    """Live operational state for a Kai workspace.

    Links to a ``BusinessProfile`` via ``business_profile_id`` and tracks
    which integrations are connected, what budgets and approval rules are
    set, which channels are active, and operator preferences.

    A ``WorkspaceState`` can be instantiated with only ``workspace_id``
    and ``business_profile_id``; every other field carries a sensible
    default.
    """

    workspace_id: str
    business_profile_id: str
    integrations: List[Integration] = Field(default_factory=list)
    budget: BudgetConstraint = Field(default_factory=BudgetConstraint)
    approval: ApprovalDefaults = Field(default_factory=ApprovalDefaults)
    enabled_channels: List[ChannelEnablement] = Field(default_factory=list)
    operator: OperatorPreferences = Field(default_factory=OperatorPreferences)
    active_modules: List[str] = Field(default_factory=list)
    disabled_modules: List[str] = Field(default_factory=list)
    last_audit_date: Optional[str] = None
    last_action_date: Optional[str] = None
    state_version: str = "1.0.0"
    created_at: Optional[str] = None  # ISO timestamp
    updated_at: Optional[str] = None  # ISO timestamp
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Persistence & Utility Functions
# ============================================================================


def _model_to_dict(obj: Any) -> Any:
    """Recursively convert a model instance to a plain dict.

    Handles both Pydantic v2 ``model_dump()`` and the stdlib fallback,
    plus nested models and lists of models.
    """
    if hasattr(obj, "model_dump") and callable(obj.model_dump):
        raw = obj.model_dump()
    elif isinstance(obj, dict):
        raw = obj
    elif isinstance(obj, list):
        return [_model_to_dict(item) for item in obj]
    else:
        return obj

    result = {}
    for key, value in raw.items():
        if hasattr(value, "model_dump") and callable(value.model_dump):
            result[key] = _model_to_dict(value)
        elif isinstance(value, list):
            result[key] = [_model_to_dict(item) for item in value]
        elif isinstance(value, dict):
            result[key] = {k: _model_to_dict(v) for k, v in value.items()}
        else:
            result[key] = value
    return result


def save_workspace_state(
    state: WorkspaceState,
    workspace_dir: str = "workspace",
) -> str:
    """Serialize and persist a WorkspaceState to disk.

    Saves to ``{workspace_dir}/state/{workspace_id}.yaml`` (or ``.json``
    if PyYAML is not available).  Creates intermediate directories when
    they do not exist.

    Parameters
    ----------
    state:
        The workspace state to persist.
    workspace_dir:
        Root workspace directory.  Defaults to ``"workspace"``.

    Returns
    -------
    str
        The absolute file path that was written.
    """
    state_dir = Path(workspace_dir) / "state"
    state_dir.mkdir(parents=True, exist_ok=True)

    data = _model_to_dict(state)
    ext = _get_file_extension()
    file_path = state_dir / f"{state.workspace_id}{ext}"

    serialized = _serialize_to_string(data)
    file_path.write_text(serialized, encoding="utf-8")

    return str(file_path.resolve())


def load_workspace_state(
    workspace_id: str,
    workspace_dir: str = "workspace",
) -> Optional[WorkspaceState]:
    """Load a WorkspaceState from disk.

    Tries YAML first, then JSON.  Returns ``None`` if no state file
    exists for the given workspace (this is not an error -- it indicates
    a brand-new workspace).

    Parameters
    ----------
    workspace_id:
        The workspace identifier (used as the file stem).
    workspace_dir:
        Root workspace directory.  Defaults to ``"workspace"``.

    Returns
    -------
    Optional[WorkspaceState]
        The loaded state, or ``None`` if the file does not exist.
    """
    state_dir = Path(workspace_dir) / "state"

    # Try both extensions so we can load files regardless of which
    # serializer was used to write them.
    candidates = [
        state_dir / f"{workspace_id}.yaml",
        state_dir / f"{workspace_id}.json",
    ]

    file_path: Optional[Path] = None
    for candidate in candidates:
        if candidate.is_file():
            file_path = candidate
            break

    if file_path is None:
        return None

    text = file_path.read_text(encoding="utf-8")
    data = _deserialize_from_string(text, str(file_path))

    # Reconstruct nested sub-models from raw dicts.
    # Handle missing fields gracefully for forward compatibility.
    integrations_raw = data.pop("integrations", [])
    integrations = [Integration(**entry) for entry in integrations_raw] if integrations_raw else []

    budget_raw = data.pop("budget", {})
    budget = BudgetConstraint(**budget_raw) if budget_raw else BudgetConstraint()

    approval_raw = data.pop("approval", {})
    approval = ApprovalDefaults(**approval_raw) if approval_raw else ApprovalDefaults()

    channels_raw = data.pop("enabled_channels", [])
    enabled_channels = [ChannelEnablement(**entry) for entry in channels_raw] if channels_raw else []

    operator_raw = data.pop("operator", {})
    operator = OperatorPreferences(**operator_raw) if operator_raw else OperatorPreferences()

    return WorkspaceState(
        integrations=integrations,
        budget=budget,
        approval=approval,
        enabled_channels=enabled_channels,
        operator=operator,
        **data,
    )


def update_integration_status(
    state: WorkspaceState,
    platform: str,
    status: str,
    last_sync: Optional[str] = None,
) -> WorkspaceState:
    """Return a new WorkspaceState with the given integration updated.

    If no integration with ``platform_name == platform`` exists, a new
    ``Integration`` entry is created with the given status.

    Parameters
    ----------
    state:
        The current workspace state.  Not mutated.
    platform:
        Canonical platform name to match against ``Integration.platform_name``.
    status:
        New status value (e.g. ``"connected"``, ``"expired"``).
    last_sync:
        Optional ISO timestamp to record as the last successful sync.

    Returns
    -------
    WorkspaceState
        A new state instance with the integration updated.
    """
    existing_data = _model_to_dict(state)

    integrations = list(existing_data.get("integrations", []))
    found = False
    for i, entry in enumerate(integrations):
        if entry.get("platform_name") == platform:
            integrations[i] = {**entry, "status": status}
            if last_sync is not None:
                integrations[i]["last_sync"] = last_sync
            found = True
            break

    if not found:
        new_integration = {"platform_name": platform, "status": status}
        if last_sync is not None:
            new_integration["last_sync"] = last_sync
        integrations.append(new_integration)

    existing_data["integrations"] = integrations

    # Update the top-level updated_at timestamp.
    existing_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Reconstruct via load path for consistency.
    integrations_models = [Integration(**entry) for entry in integrations]
    budget = BudgetConstraint(**existing_data.pop("budget", {}))
    approval = ApprovalDefaults(**existing_data.pop("approval", {}))
    channels_raw = existing_data.pop("enabled_channels", [])
    enabled_channels = [ChannelEnablement(**entry) for entry in channels_raw]
    operator = OperatorPreferences(**existing_data.pop("operator", {}))
    existing_data.pop("integrations", None)

    return WorkspaceState(
        integrations=integrations_models,
        budget=budget,
        approval=approval,
        enabled_channels=enabled_channels,
        operator=operator,
        **existing_data,
    )


def check_budget_available(state: WorkspaceState, amount: float) -> bool:
    """Check whether spending ``amount`` USD is within all budget limits.

    Evaluates (in order):

    1. ``per_action_cap`` -- single-action ceiling.
    2. ``daily_cap`` -- daily ceiling (uses ``metadata["daily_spent"]``
       for tracking; defaults to ``0.0`` if missing).
    3. ``monthly_cap`` -- monthly ceiling (uses ``total_spent_this_month``).

    Returns ``True`` when the spend is within all applicable limits,
    ``False`` otherwise.  If no caps are configured the function returns
    ``True``.
    """
    budget = state.budget

    # 1. Per-action cap
    if budget.per_action_cap is not None and amount > budget.per_action_cap:
        return False

    # 2. Daily cap -- daily tracking lives in state.metadata
    if budget.daily_cap is not None:
        state_meta = state.metadata if isinstance(state.metadata, dict) else {}
        daily_spent = float(state_meta.get("daily_spent", 0.0))
        if daily_spent + amount > budget.daily_cap:
            return False

    # 3. Weekly cap
    if budget.weekly_cap is not None:
        state_meta = state.metadata if isinstance(state.metadata, dict) else {}
        weekly_spent = float(state_meta.get("weekly_spent", 0.0))
        if weekly_spent + amount > budget.weekly_cap:
            return False

    # 4. Monthly cap
    if budget.monthly_cap is not None:
        if budget.total_spent_this_month + amount > budget.monthly_cap:
            return False

    return True


def requires_approval(
    state: WorkspaceState,
    action_type: str,
    cost: Optional[float] = None,
) -> bool:
    """Determine whether an action needs human approval.

    Decision logic (evaluated in order):

    1. If ``action_type`` is in ``require_human_for`` -> ``True``.
    2. If ``action_type`` is in ``auto_approve_types`` -> ``False``.
    3. If ``cost`` is provided and ``auto_approve_below`` is set and
       ``cost < auto_approve_below`` -> ``False``.
    4. Default: ``True`` (conservative -- require approval when unsure).

    Parameters
    ----------
    state:
        The workspace state containing approval rules.
    action_type:
        The type of action being evaluated (e.g. ``"ad_spend"``).
    cost:
        Optional estimated cost in USD for the action.

    Returns
    -------
    bool
        ``True`` if human approval is required.
    """
    approval = state.approval

    # 1. Explicitly requires human approval
    if action_type in approval.require_human_for:
        return True

    # 2. Explicitly auto-approved
    if action_type in approval.auto_approve_types:
        return False

    # 3. Cost below auto-approve threshold
    if (
        cost is not None
        and approval.auto_approve_below is not None
        and cost < approval.auto_approve_below
    ):
        return False

    # 4. Conservative default
    return True


def get_connected_platforms(state: WorkspaceState) -> List[str]:
    """Return a list of platform names where the integration status is
    ``"connected"``.

    Parameters
    ----------
    state:
        The workspace state to inspect.

    Returns
    -------
    List[str]
        Platform names with active connections.
    """
    return [
        integration.platform_name
        for integration in state.integrations
        if integration.status == "connected"
    ]


def get_available_capabilities(state: WorkspaceState) -> Dict[str, List[str]]:
    """Return a mapping of connected platform names to their capabilities.

    Only integrations with ``status == "connected"`` are included.

    Parameters
    ----------
    state:
        The workspace state to inspect.

    Returns
    -------
    Dict[str, List[str]]
        ``{platform_name: [capability, ...]}`` for all connected integrations.
    """
    result: Dict[str, List[str]] = {}
    for integration in state.integrations:
        if integration.status == "connected":
            result[integration.platform_name] = list(integration.capabilities)
    return result
