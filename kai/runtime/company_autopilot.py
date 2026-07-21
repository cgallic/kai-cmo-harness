"""Proof-bound Company Autopilot command-center aggregation.

This module is deliberately read-only.  It derives an operator view from the
canonical workspace, runtime, action, connector-health, and goal stores without
creating a second state model or treating onboarding checklists as evidence.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, Iterable, List, Optional

from .actions import derive_operating_state
from .goals import compute_goal_pace


PROOF_PASS_VALUES = {
    "accepted", "matched", "pass", "passed", "reconciled", "success", "succeeded", "verified",
}
UNHEALTHY_CONNECTOR_STATES = {
    "degraded", "error", "failed", "disconnected", "expired", "revoked", "unhealthy",
}
EVIDENCE_DECISION_KEYS = {
    "accepted", "matched", "passed", "reconciled", "success", "verified",
}


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _as_utc(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _positive_evidence(value: Any) -> bool:
    """Require positive evidence when a value carries its own verdict."""
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return bool(value.strip())
    if isinstance(value, list):
        return any(_positive_evidence(item) for item in value)
    if not isinstance(value, dict) or not value:
        return False

    normalized = {str(key).lower(): item for key, item in value.items()}
    if "status" in normalized:
        return str(normalized["status"]).lower() in PROOF_PASS_VALUES
    decisions = [normalized[key] for key in EVIDENCE_DECISION_KEYS if key in normalized]
    if decisions:
        return any(item is True or str(item).lower() in PROOF_PASS_VALUES for item in decisions)
    return any(_positive_evidence(item) for item in normalized.values())


def _truthy_evidence(payload: Any, keys: Iterable[str]) -> bool:
    """Find explicit, non-empty evidence under one of *keys* recursively."""
    wanted = {key.lower() for key in keys}
    if isinstance(payload, dict):
        for key, value in payload.items():
            if str(key).lower() in wanted:
                if _positive_evidence(value):
                    return True
            if _truthy_evidence(value, wanted):
                return True
    elif isinstance(payload, list):
        return any(_truthy_evidence(item, wanted) for item in payload)
    return False


def has_strict_proof(action: Dict[str, Any]) -> bool:
    """Return whether an executed action has the full acceptance evidence.

    A successful connector response is not enough.  Strict proof requires an
    accepted verification decision plus a provider receipt, an independent
    read-back, and reconciliation evidence.
    """
    verification = action.get("verification_result")
    if not isinstance(verification, dict):
        return False
    decision = str(
        verification.get("status")
        or verification.get("verdict")
        or verification.get("decision")
        or ""
    ).lower()
    accepted = (
        decision in PROOF_PASS_VALUES
        or verification.get("passed") is True
        or verification.get("accepted") is True
    )
    if not accepted:
        return False
    proof_payload = {
        "verification": verification,
        "result": action.get("result_summary") or {},
        "metadata": action.get("metadata") or {},
    }
    provider_receipt = _truthy_evidence(
        proof_payload,
        {"provider_receipt", "provider_receipt_id", "provider_response_receipt"},
    )
    independent_readback = _truthy_evidence(
        proof_payload,
        {"independent_readback", "independent_read_back", "readback", "read_back"},
    )
    reconciliation = _truthy_evidence(
        proof_payload,
        {"reconciliation", "reconciliation_evidence", "reconciled_at", "reconciled"},
    )
    return provider_receipt and independent_readback and reconciliation


class CompanyAutopilotService:
    """Build a deterministic command center from injected canonical stores."""

    def __init__(
        self,
        *,
        workspace_loader: Optional[Callable[[], Any]] = None,
        runtime_store: Any = None,
        action_store: Any = None,
        connector_health: Any = None,
        goal_registry: Any = None,
        now: Optional[Callable[[], datetime]] = None,
        stale_after_days: int = 7,
    ) -> None:
        if workspace_loader is None:
            from .loader import load_workspace_profile
            workspace_loader = load_workspace_profile
        if runtime_store is None:
            from .store import get_default_runtime_store
            runtime_store = get_default_runtime_store()
        if action_store is None:
            from .actions import get_default_action_store
            action_store = get_default_action_store()
        if connector_health is None:
            from .connector_health import ConnectorHealthDashboard
            connector_health = ConnectorHealthDashboard()
        if goal_registry is None:
            from .goals import get_default_goal_registry
            goal_registry = get_default_goal_registry()

        self._workspace_loader = workspace_loader
        self._runtime_store = runtime_store
        self._action_store = action_store
        self._connector_health = connector_health
        self._goal_registry = goal_registry
        self._now = now or _utc_now
        self._stale_after = timedelta(days=stale_after_days)

    def command_center(self, brand_id: Optional[str] = None) -> Dict[str, Any]:
        """Return exactly one primary proof-bound bottleneck and its coach."""
        rows = self._build_rows(brand_id=brand_id)
        blocked = [row for row in rows if row["primary_bottleneck"] is not None]
        primary = min(blocked, key=lambda row: (row["priority_rank"], row["brand_id"])) if blocked else None
        bottleneck = primary["primary_bottleneck"] if primary else None
        coach = self._coach(bottleneck)
        return {
            "generated_at": self._now().isoformat(),
            "brand_scope": brand_id or "portfolio",
            "primary_bottleneck": bottleneck,
            "coach": coach,
            "portfolio_count": len(rows),
        }

    def portfolio(self, brand_id: Optional[str] = None) -> Dict[str, Any]:
        """Return one evidence-derived lifecycle row per configured brand."""
        rows = self._build_rows(brand_id=brand_id)
        for row in rows:
            row.pop("priority_rank", None)
        return {
            "generated_at": self._now().isoformat(),
            "rows": rows,
            "count": len(rows),
        }

    def _build_rows(self, brand_id: Optional[str]) -> List[Dict[str, Any]]:
        workspace = self._workspace_loader()
        brands = list(getattr(workspace, "brands", []) or [])
        if brand_id:
            brands = [brand for brand in brands if getattr(brand, "id", None) == brand_id]
        rows = [self._brand_row(brand) for brand in sorted(brands, key=lambda item: item.id)]
        return rows

    def _brand_row(self, brand: Any) -> Dict[str, Any]:
        brand_id = brand.id
        actions = self._action_store.list_actions(brand_id=brand_id, limit=10_000)
        runs = self._runtime_store.list_runs(brand_id=brand_id, limit=10_000)
        goals = [goal for goal in self._goal_registry.list_goals(brand_id=brand_id) if goal.status == "active"]
        health = self._connector_health.brand_health(brand_id)
        bottleneck, rank = self._select_bottleneck(brand, actions, runs, goals, health)

        latest_action = self._latest(actions)
        latest_run = self._latest(runs)
        lifecycle = derive_operating_state(latest_action) if latest_action else (
            latest_run.get("status", "not_started") if latest_run else "not_started"
        )
        row_health = "blocked" if bottleneck else "healthy"
        if bottleneck and bottleneck["type"] in {"pending_approval", "behind_pace_goal", "stale_runtime"}:
            row_health = "needs_attention"

        return {
            "brand_id": brand_id,
            "brand_name": getattr(brand, "name", brand_id),
            "lifecycle": lifecycle,
            "health": row_health,
            "blocked_gate": bottleneck["blocked_gate"] if bottleneck else None,
            "owner": bottleneck["owner"] if bottleneck else self._owner(brand),
            "next_action": bottleneck["next_action"] if bottleneck else "Monitor verified outcomes and goal pace.",
            "close_condition": bottleneck["close_condition"] if bottleneck else "No proof-bound blocker is open.",
            "evidence_refs": bottleneck["evidence_refs"] if bottleneck else self._baseline_refs(latest_run, latest_action),
            "primary_bottleneck": bottleneck,
            "priority_rank": rank,
        }

    def _select_bottleneck(
        self,
        brand: Any,
        actions: List[Dict[str, Any]],
        runs: List[Dict[str, Any]],
        goals: List[Any],
        health: Dict[str, Any],
    ) -> tuple[Optional[Dict[str, Any]], int]:
        failed = [a for a in actions if a.get("execution_state") in {"failed", "rolled_back"}]
        if failed:
            action = self._latest(failed)
            return self._action_bottleneck(
                brand, action, 1, "failed_action", "execution_failed",
                "Diagnose the failed action and submit a corrected proposal.",
                "A replacement action is approved, executed, and carries strict verification proof.",
            ), 1

        unverified = [
            action for action in actions
            if action.get("execution_state") == "completed" and not has_strict_proof(action)
        ]
        if unverified:
            action = self._latest(unverified)
            return self._action_bottleneck(
                brand, action, 2, "unverified_execution", "strict_proof_missing",
                "Collect provider receipt, independent read-back, and reconciliation evidence.",
                "Verification is accepted and all three strict-proof evidence classes are attached.",
            ), 2

        unhealthy = self._unhealthy_integrations(health)
        if unhealthy:
            integration = sorted(unhealthy, key=lambda item: str(item.get("integration_id", "")))[0]
            refs = [f"integration:{integration.get('integration_id') or integration.get('provider') or 'unknown'}"]
            return self._bottleneck(
                brand, 3, "connector_unhealthy", "connector_health",
                "Restore the connector and verify scopes, freshness, and a successful read.",
                "Connector is healthy, current, and independently readable with required scopes.", refs,
                subject=integration.get("provider") or integration.get("channel"),
            ), 3

        approvals = [a for a in actions if a.get("approval_state") in {"held", "pending"}]
        if approvals:
            action = self._latest(approvals)
            return self._action_bottleneck(
                brand, action, 4, "pending_approval", "human_approval",
                "Review the proposal evidence and approve, reject, or request revision.",
                "A human records a decision and any approved execution remains proof-gated.",
            ), 4

        behind = []
        for goal in goals:
            pace = compute_goal_pace(goal, now=self._now())
            if pace.get("behind_pace"):
                behind.append((goal, pace))
        if behind:
            goal, pace = sorted(behind, key=lambda item: item[0].goal_id)[0]
            refs = [f"goal:{goal.goal_id}"]
            return self._bottleneck(
                brand, 5, "behind_pace_goal", "goal_pace",
                f"Replan work for {goal.name} from current measured KPI state.",
                "Measured KPI pace is on target or the goal is achieved, with source-backed current value.", refs,
                subject=goal.name,
                extra={"pace": pace},
            ), 5

        latest_run = self._latest(runs)
        latest_at = _as_utc((latest_run or {}).get("updated_at"))
        if latest_run is None or latest_at is None or self._now() - latest_at > self._stale_after:
            refs = [f"run:{latest_run['run_id']}"] if latest_run else []
            return self._bottleneck(
                brand, 6, "stale_runtime", "current_runtime_state",
                "Run a current evidence-backed review for this brand.",
                "A current run snapshot exists within the freshness window and records its sources.", refs,
                subject=(latest_run or {}).get("run_id"),
            ), 6
        return None, 999

    def _action_bottleneck(
        self, brand: Any, action: Dict[str, Any], rank: int, kind: str, gate: str,
        next_action: str, close_condition: str,
    ) -> Dict[str, Any]:
        refs = [f"action:{action.get('action_id', 'unknown')}"]
        if action.get("source_run_id"):
            refs.append(f"run:{action['source_run_id']}")
        for evidence in action.get("evidence") or []:
            if isinstance(evidence, str):
                refs.append(evidence)
            elif isinstance(evidence, dict):
                ref = evidence.get("id") or evidence.get("source") or evidence.get("url")
                if ref:
                    refs.append(str(ref))
        return self._bottleneck(
            brand, rank, kind, gate, next_action, close_condition, refs,
            subject=action.get("action_id"), owner=self._owner(brand, action),
        )

    def _bottleneck(
        self, brand: Any, rank: int, kind: str, gate: str, next_action: str,
        close_condition: str, evidence_refs: List[str], *, subject: Any = None,
        owner: Optional[str] = None, extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        result = {
            "priority_rank": rank,
            "type": kind,
            "brand_id": brand.id,
            "subject": subject,
            "blocked_gate": gate,
            "owner": owner or self._owner(brand),
            "next_action": next_action,
            "close_condition": close_condition,
            "evidence_refs": list(dict.fromkeys(evidence_refs)),
        }
        if extra:
            result.update(extra)
        return result

    @staticmethod
    def _unhealthy_integrations(health: Dict[str, Any]) -> List[Dict[str, Any]]:
        unhealthy = []
        for integration in health.get("integrations") or []:
            state = str(integration.get("status") or "").lower()
            if (
                state in UNHEALTHY_CONNECTOR_STATES
                or integration.get("stale_sync") is True
                or integration.get("kill_switch") is True
                or bool(integration.get("last_error"))
            ):
                unhealthy.append(integration)
        return unhealthy

    @staticmethod
    def _latest(records: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if not records:
            return None
        return max(records, key=lambda item: item.get("updated_at") or item.get("created_at") or "")

    @staticmethod
    def _owner(brand: Any, action: Optional[Dict[str, Any]] = None) -> str:
        metadata = (action or {}).get("metadata") or {}
        brand_metadata = getattr(brand, "metadata", {}) or {}
        return str(
            metadata.get("owner")
            or metadata.get("assigned_to")
            or brand_metadata.get("owner")
            or "unassigned"
        )

    @staticmethod
    def _baseline_refs(
        latest_run: Optional[Dict[str, Any]], latest_action: Optional[Dict[str, Any]],
    ) -> List[str]:
        refs = []
        if latest_run:
            refs.append(f"run:{latest_run.get('run_id')}")
        if latest_action:
            refs.append(f"action:{latest_action.get('action_id')}")
        return refs

    @staticmethod
    def _coach(bottleneck: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        if bottleneck is None:
            return {
                "status": "monitor",
                "message": "No proof-bound blocker is open. Monitor verified outcomes and goal pace.",
                "next_action": "Monitor verified outcomes and goal pace.",
                "close_condition": "No proof-bound blocker is open.",
                "evidence_refs": [],
            }
        return {
            "status": "action_required",
            "message": bottleneck["next_action"],
            "next_action": bottleneck["next_action"],
            "close_condition": bottleneck["close_condition"],
            "evidence_refs": bottleneck["evidence_refs"],
        }
