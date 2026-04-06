"""Approval routing by risk tier for the Kai Marketing OS.

Every marketing action passes through the ApprovalRouter before execution.
The router examines the ProposedAction's risk tier, estimated spend, content
type, compliance flags, and the operator's routing configuration to determine
the correct approval path -- from auto-approve (no human needed) up to
executive approval (two sign-offs required).

This is the trust and safety layer that keeps operators in control while
letting low-risk optimizations proceed without friction.

Usage::

    from kai.compliance.approval_routing import (
        ApprovalRouter,
        get_default_routing_config,
    )

    config = get_default_routing_config("biz_abc123")
    router = ApprovalRouter(config)

    decision = router.route_action(proposed_action, compliance_result)
    print(decision.route)        # "operator_review"
    print(decision.reason)       # "Medium risk tier → operator review required"
    print(decision.escalate_at)  # "2026-04-03T10:00:00+00:00"

Design notes
------------
- Uses dataclass + SerializableModel pattern from ``kai/runtime/models.py``.
- ProposedAction and ComplianceResult are typed as ``Any`` to avoid circular
  imports.  The router accesses them by attribute name.
- No external dependencies beyond stdlib.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Serialization helper (matches kai.runtime.models.SerializableModel)
# ---------------------------------------------------------------------------


class SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)  # type: ignore[arg-type]


# ============================================================================
# Enums
# ============================================================================


class ApprovalRoute(str, Enum):
    """The approval path an action must take before execution.

    Ordered from least oversight to most oversight.  The router selects
    the appropriate route based on risk tier, spend, content visibility,
    and compliance flags.
    """

    auto_approve = "auto_approve"
    """Execute immediately, no human review needed."""

    low_touch = "low_touch"
    """Notify operator, execute after configurable delay unless vetoed."""

    operator_review = "operator_review"
    """Queue for operator, require explicit approval (can batch-approve)."""

    operator_approval = "operator_approval"
    """Queue with full preview, require individual sign-off."""

    executive_approval = "executive_approval"
    """Require two approvals or escalate to designated executive contact."""


class EscalationReason(str, Enum):
    """Why an action was escalated to a higher approval tier."""

    timeout = "timeout"
    """Action was not reviewed within the configured time window."""

    spend_threshold = "spend_threshold"
    """Spend exceeds the threshold for the current route."""

    compliance_flag = "compliance_flag"
    """The compliance engine flagged a concern."""

    override_request = "override_request"
    """Operator explicitly requested escalation."""

    multiple_rejections = "multiple_rejections"
    """Action has been rejected and revised multiple times."""


# ---------------------------------------------------------------------------
# Route hierarchy for escalation
# ---------------------------------------------------------------------------

_ROUTE_HIERARCHY: List[str] = [
    ApprovalRoute.auto_approve.value,
    ApprovalRoute.low_touch.value,
    ApprovalRoute.operator_review.value,
    ApprovalRoute.operator_approval.value,
    ApprovalRoute.executive_approval.value,
]


def _next_route(current_route: str) -> str:
    """Return the next-higher route in the hierarchy.

    If already at the maximum (executive_approval), returns the same route.
    """
    try:
        idx = _ROUTE_HIERARCHY.index(current_route)
    except ValueError:
        # Unknown route -- default to operator_review as a safe middle ground
        return ApprovalRoute.operator_review.value
    next_idx = min(idx + 1, len(_ROUTE_HIERARCHY) - 1)
    return _ROUTE_HIERARCHY[next_idx]


def _route_rank(route: str) -> int:
    """Return the numeric rank of a route (higher = more oversight).

    Unknown routes get rank 2 (operator_review level) as a safe default.
    """
    try:
        return _ROUTE_HIERARCHY.index(route)
    except ValueError:
        return 2


# ============================================================================
# Models
# ============================================================================


@dataclass
class RoutingDecision(SerializableModel):
    """The result of routing a ProposedAction through the approval system.

    Contains the chosen route, full reasoning, timestamps for auto-execution
    and escalation, and any compliance flags that influenced the decision.
    """

    id: str
    """Format ``route_{uuid_hex[:12]}``."""

    action_id: str
    """Which ProposedAction this routes."""

    risk_tier: str
    """RiskTier from ProposedAction (auto, low, medium, high, critical)."""

    route: str
    """ApprovalRoute enum value -- the determined route."""

    reason: str
    """Human-readable explanation of why this route was chosen."""

    contributing_factors: List[str] = field(default_factory=list)
    """Factors that influenced the routing decision."""

    estimated_spend: Optional[float] = None
    """If the action involves spend."""

    content_is_public: bool = False
    """Whether this action produces public-facing content."""

    compliance_flags: List[str] = field(default_factory=list)
    """Any compliance concerns from the compliance engine."""

    auto_execute_at: Optional[str] = None
    """For low_touch: ISO timestamp when auto-execution will occur."""

    escalate_at: Optional[str] = None
    """ISO timestamp when this will escalate if not reviewed."""

    decided_at: str = ""
    """ISO timestamp."""

    decided_by: str = "system"
    """'system' for automatic routing, operator name for overrides."""


@dataclass
class RoutingConfig(SerializableModel):
    """Per-business configuration for the approval router.

    Controls which actions can be auto-approved, spend thresholds for
    each approval tier, escalation timeouts, and custom overrides.
    Defaults are conservative -- no spend is auto-approved and all
    public content requires operator review.
    """

    business_id: str

    auto_approve_enabled: bool = True
    """Whether any actions can be auto-approved."""

    auto_approve_max_spend: float = 0.0
    """Max spend for auto-approval (default 0.0 -- no spend auto-approved)."""

    low_touch_delay_minutes: int = 60
    """Delay before low-touch auto-execution (default 60 minutes)."""

    low_touch_max_spend: float = 50.0
    """Max spend for low-touch routing."""

    operator_review_max_spend: float = 500.0
    """Max spend for operator review."""

    operator_approval_max_spend: float = 5000.0
    """Max spend for operator approval."""

    executive_threshold_spend: float = 5000.0
    """Spend above this triggers executive approval."""

    escalation_timeout_hours: int = 24
    """Hours before escalation if not reviewed."""

    require_approval_for_public_content: bool = True
    """Force operator_review minimum for any public-facing content."""

    custom_overrides: Dict[str, str] = field(default_factory=dict)
    """action_type -> forced route overrides.

    Example: ``{"kaicalls_setup": "operator_approval"}``
    """


@dataclass
class RoutingAuditEntry(SerializableModel):
    """Immutable audit log entry for a routing decision.

    Captures the full lifecycle of a routing decision: the initial route
    chosen, who approved or rejected it, whether it was escalated, and why.
    Storage is handled by the audit trail system (Task 066).
    """

    timestamp: str
    """ISO timestamp when this entry was created."""

    action_id: str
    business_id: str

    route_chosen: str
    """ApprovalRoute value."""

    risk_tier: str
    reason: str

    approver: Optional[str] = None
    """Who approved (None if auto-approved or not yet approved)."""

    approved_at: Optional[str] = None
    rejected_at: Optional[str] = None
    rejection_reason: Optional[str] = None

    escalated: bool = False
    escalation_reason: Optional[str] = None


# ============================================================================
# ID Generation
# ============================================================================


def _generate_routing_id() -> str:
    """Generate a unique routing decision ID.

    Format: ``route_{12-hex-chars}``
    """
    return f"route_{uuid.uuid4().hex[:12]}"


def _now_iso() -> str:
    """Return the current UTC time as an ISO 8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(iso_str: str) -> datetime:
    """Parse an ISO 8601 timestamp string to a datetime.

    Handles both timezone-aware strings (with ``+00:00`` or ``Z``) and
    naive strings (assumed UTC).
    """
    # Handle the Z suffix that fromisoformat doesn't always accept
    cleaned = iso_str.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(cleaned)
    except ValueError:
        # Last resort: strip microseconds and retry
        if "." in cleaned:
            cleaned = cleaned.split(".")[0] + cleaned[cleaned.rfind("+"):]
            return datetime.fromisoformat(cleaned)
        raise


# ============================================================================
# Public API: Approval Router
# ============================================================================


# Action types considered public-facing
_PUBLIC_ACTION_TYPES = frozenset({
    "website_update",
    "social_post",
    "ad_campaign",
    "email_sequence",
    "content_creation",
    "review_request",
    "gbp_update",
    "follow_up_sequence",
    "reputation_action",
})

# Action types considered internal (not public-facing)
_INTERNAL_ACTION_TYPES = frozenset({
    "analytics_fix",
    "kaicalls_setup",
    "seo_fix",
})


class ApprovalRouter:
    """Routes ProposedActions to the appropriate approval path.

    The router applies a priority-ordered set of rules:

    1. Compliance flags force ``operator_approval`` minimum.
    2. Custom overrides for specific action types.
    3. Risk tier determines the base route.
    4. Public content check raises the floor to ``operator_review``.
    5. Spend escalation bumps the route when spend exceeds the
       threshold for the current tier.

    Parameters
    ----------
    config : RoutingConfig
        Per-business routing configuration with spend thresholds,
        escalation timeouts, and custom overrides.
    """

    def __init__(self, config: RoutingConfig) -> None:
        self._config = config

    # ------------------------------------------------------------------
    # Primary routing
    # ------------------------------------------------------------------

    def route_action(
        self,
        action: Any,
        compliance_result: Optional[Any] = None,
    ) -> RoutingDecision:
        """Determine the approval route for a ProposedAction.

        Parameters
        ----------
        action : Any
            A ProposedAction (typed as Any to avoid circular imports).
            Expected attributes: ``id``, ``action_type``, ``risk_tier``,
            ``estimated_cost``, ``metadata``.
        compliance_result : Any, optional
            A ComplianceResult from the compliance engine.  If present
            and it contains violations, the route is forced to at least
            ``operator_approval``.

        Returns
        -------
        RoutingDecision
            The routing decision with full reasoning.
        """
        now = _now_iso()
        config = self._config
        factors: List[str] = []
        compliance_flags: List[str] = []

        # Extract action attributes safely
        action_id = getattr(action, "id", "unknown")
        action_type = getattr(action, "action_type", "unknown")
        risk_tier = getattr(action, "risk_tier", "medium")
        estimated_spend = self._estimate_spend(action)
        content_is_public = self._determine_content_is_public(action)

        # Start with the base route from risk tier
        route = self._route_from_risk_tier(risk_tier, estimated_spend)
        reason_parts: List[str] = []

        # ----- Priority 1: Compliance flags -----
        if compliance_result is not None:
            violations = getattr(compliance_result, "violations", [])
            warnings = getattr(compliance_result, "warnings", [])
            status = getattr(compliance_result, "status", "pass")

            if violations:
                compliance_flags = [
                    getattr(v, "description", str(v)) for v in violations
                ]
                factors.append(
                    f"compliance_violations: {len(violations)} violation(s) found"
                )
                # Force at least operator_approval
                if _route_rank(route) < _route_rank(ApprovalRoute.operator_approval.value):
                    route = ApprovalRoute.operator_approval.value
                    reason_parts.append(
                        f"Compliance violations ({len(violations)}) force "
                        f"operator approval minimum"
                    )

            if warnings:
                factors.append(
                    f"compliance_warnings: {len(warnings)} warning(s)"
                )

            if status == "fail":
                factors.append("compliance_status: fail")

        # ----- Priority 2: Custom overrides -----
        if action_type in config.custom_overrides:
            forced_route = config.custom_overrides[action_type]
            # Custom override only raises the route, never lowers it
            if _route_rank(forced_route) > _route_rank(route):
                route = forced_route
                reason_parts.append(
                    f"Custom override for '{action_type}' forces "
                    f"'{forced_route}'"
                )
            factors.append(f"custom_override: {action_type} -> {forced_route}")

        # ----- Priority 3: Risk tier (already applied as base) -----
        if not reason_parts:
            # Only add the base reason if nothing has overridden it yet
            reason_parts.append(
                f"Risk tier '{risk_tier}' maps to '{route}'"
            )
        factors.append(f"risk_tier: {risk_tier}")

        # ----- Priority 4: Public content check -----
        if (
            content_is_public
            and config.require_approval_for_public_content
            and _route_rank(route) < _route_rank(ApprovalRoute.operator_review.value)
        ):
            route = ApprovalRoute.operator_review.value
            reason_parts.append(
                "Public-facing content requires operator review minimum"
            )
            factors.append("public_content_override: True")

        if content_is_public:
            factors.append("content_is_public: True")
        else:
            factors.append("content_is_public: False")

        # ----- Priority 5: Spend escalation -----
        if estimated_spend > 0:
            route = self._apply_spend_escalation(
                route, estimated_spend, factors, reason_parts,
            )
            factors.append(f"estimated_spend: ${estimated_spend:.2f}")

        # ----- Calculate timestamps -----
        now_dt = datetime.now(timezone.utc)

        auto_execute_at: Optional[str] = None
        if route == ApprovalRoute.low_touch.value:
            execute_dt = now_dt + timedelta(minutes=config.low_touch_delay_minutes)
            auto_execute_at = execute_dt.isoformat()

        escalate_at: Optional[str] = None
        if route != ApprovalRoute.auto_approve.value:
            escalate_dt = now_dt + timedelta(hours=config.escalation_timeout_hours)
            escalate_at = escalate_dt.isoformat()

        # ----- Build the reason string -----
        reason = "; ".join(reason_parts) if reason_parts else f"Default routing for risk tier '{risk_tier}'"

        return RoutingDecision(
            id=_generate_routing_id(),
            action_id=action_id,
            risk_tier=risk_tier,
            route=route,
            reason=reason,
            contributing_factors=factors,
            estimated_spend=estimated_spend if estimated_spend > 0 else None,
            content_is_public=content_is_public,
            compliance_flags=compliance_flags,
            auto_execute_at=auto_execute_at,
            escalate_at=escalate_at,
            decided_at=now,
            decided_by="system",
        )

    # ------------------------------------------------------------------
    # Escalation
    # ------------------------------------------------------------------

    def escalate(
        self,
        decision: RoutingDecision,
        reason: str,
    ) -> RoutingDecision:
        """Escalate a routing decision to the next-higher approval tier.

        Creates a new RoutingDecision with the next route in the
        hierarchy.  If the decision is already at executive_approval,
        keeps it there and adds ``max_escalation_reached`` to
        contributing_factors.

        Parameters
        ----------
        decision : RoutingDecision
            The current routing decision to escalate.
        reason : str
            Human-readable reason for escalation.

        Returns
        -------
        RoutingDecision
            A new routing decision at the higher tier.
        """
        now = _now_iso()
        now_dt = datetime.now(timezone.utc)
        current_route = decision.route
        new_route = _next_route(current_route)

        new_factors = list(decision.contributing_factors)
        new_factors.append(f"escalated_from: {current_route}")
        new_factors.append(f"escalation_reason: {reason}")

        at_max = new_route == current_route
        if at_max:
            new_factors.append("max_escalation_reached")

        new_reason = (
            f"Escalated from '{current_route}' to '{new_route}': {reason}"
            if not at_max
            else f"Already at maximum approval tier (executive_approval): {reason}"
        )

        escalate_at: Optional[str] = None
        if new_route != ApprovalRoute.auto_approve.value:
            escalate_dt = now_dt + timedelta(
                hours=self._config.escalation_timeout_hours,
            )
            escalate_at = escalate_dt.isoformat()

        return RoutingDecision(
            id=_generate_routing_id(),
            action_id=decision.action_id,
            risk_tier=decision.risk_tier,
            route=new_route,
            reason=new_reason,
            contributing_factors=new_factors,
            estimated_spend=decision.estimated_spend,
            content_is_public=decision.content_is_public,
            compliance_flags=decision.compliance_flags,
            auto_execute_at=None,  # Escalated actions never auto-execute
            escalate_at=escalate_at,
            decided_at=now,
            decided_by="system",
        )

    # ------------------------------------------------------------------
    # Timeout escalation check
    # ------------------------------------------------------------------

    def check_for_timeout_escalation(
        self,
        decision: RoutingDecision,
        current_time: str,
    ) -> Optional[RoutingDecision]:
        """Check whether a routing decision should be escalated due to timeout.

        Compares ``current_time`` against ``decision.escalate_at``.  If
        the escalation window has passed and the action has not been
        approved or rejected, returns a new escalated RoutingDecision.

        Parameters
        ----------
        decision : RoutingDecision
            The routing decision to check.
        current_time : str
            Current time as an ISO 8601 timestamp.

        Returns
        -------
        RoutingDecision or None
            A new escalated decision if timeout has occurred, or None if
            no escalation is needed.
        """
        if decision.escalate_at is None:
            return None

        # Auto-approved actions don't escalate
        if decision.route == ApprovalRoute.auto_approve.value:
            return None

        current_dt = _parse_iso(current_time)
        escalate_dt = _parse_iso(decision.escalate_at)

        if current_dt > escalate_dt:
            return self.escalate(
                decision,
                reason=(
                    f"Action not reviewed within "
                    f"{self._config.escalation_timeout_hours}-hour window "
                    f"(escalate_at: {decision.escalate_at})"
                ),
            )

        return None

    # ------------------------------------------------------------------
    # Audit logging
    # ------------------------------------------------------------------

    def log_routing_decision(
        self,
        decision: RoutingDecision,
        business_id: str,
    ) -> RoutingAuditEntry:
        """Create an audit entry from a routing decision.

        The returned entry captures the routing decision's key facts for
        the audit trail.  Actual storage is handled by the audit trail
        system (Task 066).

        Parameters
        ----------
        decision : RoutingDecision
            The routing decision to log.
        business_id : str
            The business this decision belongs to.

        Returns
        -------
        RoutingAuditEntry
            A complete audit entry ready for persistence.
        """
        return RoutingAuditEntry(
            timestamp=_now_iso(),
            action_id=decision.action_id,
            business_id=business_id,
            route_chosen=decision.route,
            risk_tier=decision.risk_tier,
            reason=decision.reason,
            approver=None,
            approved_at=None,
            rejected_at=None,
            rejection_reason=None,
            escalated=False,
            escalation_reason=None,
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _determine_content_is_public(self, action: Any) -> bool:
        """Determine whether an action produces public-facing content.

        Checks the action's ``action_type`` attribute against known
        public and internal action types.  Defaults to True (safer
        assumption) for unknown types.

        Parameters
        ----------
        action : Any
            A ProposedAction.

        Returns
        -------
        bool
            True if the action produces externally visible content.
        """
        action_type = getattr(action, "action_type", "unknown")

        # Explicitly internal action types
        if action_type in _INTERNAL_ACTION_TYPES:
            return False

        # Explicitly public action types
        if action_type in _PUBLIC_ACTION_TYPES:
            return True

        # Default to True -- safer to require review than to skip it
        return True

    def _estimate_spend(self, action: Any) -> float:
        """Extract estimated spend from an action.

        Checks ``estimated_cost`` first (the canonical field on
        ProposedAction), then falls back to ``estimated_spend`` in
        metadata.

        Parameters
        ----------
        action : Any
            A ProposedAction.

        Returns
        -------
        float
            Estimated spend in USD, or 0.0 if not specified.
        """
        # Primary: ProposedAction.estimated_cost
        cost = getattr(action, "estimated_cost", None)
        if cost is not None:
            try:
                return float(cost)
            except (TypeError, ValueError):
                pass

        # Fallback: metadata.estimated_spend
        metadata = getattr(action, "metadata", {})
        if isinstance(metadata, dict):
            spend = metadata.get("estimated_spend")
            if spend is not None:
                try:
                    return float(spend)
                except (TypeError, ValueError):
                    pass

        return 0.0

    def _route_from_risk_tier(self, risk_tier: str, estimated_spend: float) -> str:
        """Map a risk tier to its base approval route.

        Parameters
        ----------
        risk_tier : str
            RiskTier enum value (auto, low, medium, high, critical).
        estimated_spend : float
            Estimated spend for spend-gating on auto and low tiers.

        Returns
        -------
        str
            ApprovalRoute enum value.
        """
        config = self._config

        if risk_tier == "auto":
            if config.auto_approve_enabled and estimated_spend <= config.auto_approve_max_spend:
                return ApprovalRoute.auto_approve.value
            # Auto tier but auto-approve disabled or spend too high --
            # fall through to low_touch
            return ApprovalRoute.low_touch.value

        if risk_tier == "low":
            if estimated_spend <= config.low_touch_max_spend:
                return ApprovalRoute.low_touch.value
            return ApprovalRoute.operator_review.value

        if risk_tier == "medium":
            return ApprovalRoute.operator_review.value

        if risk_tier == "high":
            return ApprovalRoute.operator_approval.value

        if risk_tier == "critical":
            return ApprovalRoute.executive_approval.value

        # Unknown risk tier -- default to operator_review
        return ApprovalRoute.operator_review.value

    def _apply_spend_escalation(
        self,
        current_route: str,
        estimated_spend: float,
        factors: List[str],
        reason_parts: List[str],
    ) -> str:
        """Escalate the route if spend exceeds the threshold for the current tier.

        Walks up the route hierarchy until the spend fits within the
        tier's threshold, or hits executive_approval.

        Parameters
        ----------
        current_route : str
            The currently determined route.
        estimated_spend : float
            The action's estimated spend.
        factors : list
            Mutable list of contributing factors (appended to in place).
        reason_parts : list
            Mutable list of reason strings (appended to in place).

        Returns
        -------
        str
            The (possibly escalated) route.
        """
        config = self._config
        route = current_route

        # Define spend ceilings per route tier
        spend_ceilings = {
            ApprovalRoute.auto_approve.value: config.auto_approve_max_spend,
            ApprovalRoute.low_touch.value: config.low_touch_max_spend,
            ApprovalRoute.operator_review.value: config.operator_review_max_spend,
            ApprovalRoute.operator_approval.value: config.operator_approval_max_spend,
        }

        # Executive approval has no ceiling -- it's the top
        escalated = False
        while route in spend_ceilings:
            ceiling = spend_ceilings[route]
            if estimated_spend > ceiling:
                old_route = route
                route = _next_route(route)
                if not escalated:
                    escalated = True
                factors.append(
                    f"spend_escalation: ${estimated_spend:.2f} exceeds "
                    f"${ceiling:.2f} ceiling for '{old_route}'"
                )
                reason_parts.append(
                    f"Spend ${estimated_spend:.2f} exceeds "
                    f"${ceiling:.2f} threshold for '{old_route}', "
                    f"escalated to '{route}'"
                )
                # Safety: if we didn't actually move up, break
                if route == old_route:
                    break
            else:
                break

        return route


# ============================================================================
# Factory
# ============================================================================


def get_default_routing_config(business_id: str) -> RoutingConfig:
    """Return a sensible default routing configuration.

    The defaults are deliberately conservative:

    - Auto-approve is enabled but with $0 max spend (no spending
      without human review).
    - Low-touch delay is 60 minutes (1 hour before auto-execution).
    - Public content always requires operator review.
    - 24-hour escalation timeout.

    Parameters
    ----------
    business_id : str
        The business this configuration applies to.

    Returns
    -------
    RoutingConfig
        A conservative default routing configuration.
    """
    return RoutingConfig(
        business_id=business_id,
        auto_approve_enabled=True,
        auto_approve_max_spend=0.0,
        low_touch_delay_minutes=60,
        low_touch_max_spend=50.0,
        operator_review_max_spend=500.0,
        operator_approval_max_spend=5000.0,
        executive_threshold_spend=5000.0,
        escalation_timeout_hours=24,
        require_approval_for_public_content=True,
        custom_overrides={},
    )
