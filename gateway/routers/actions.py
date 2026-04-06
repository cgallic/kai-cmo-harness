"""Operator Command Center Router.

Surfaces action proposals, approval workflows, integration management,
and an operator dashboard for the Kai marketing runtime.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException

router = APIRouter()


# ============================================================================
# Lazy import helpers — backing stores are built in parallel
# ============================================================================

def _get_action_store():
    try:
        from kai.runtime.actions import get_default_action_store
        return get_default_action_store()
    except (ImportError, Exception):
        return None


def _get_policy_engine():
    try:
        from kai.runtime.policy import PolicyEngine
        return PolicyEngine()
    except (ImportError, Exception):
        return None


def _get_integration_registry():
    try:
        from kai.runtime.integrations import get_default_integration_registry
        return get_default_integration_registry()
    except (ImportError, Exception):
        return None


def _require_store(name: str, store):
    if store is None:
        raise HTTPException(
            status_code=503,
            detail=f"{name} not yet available",
        )
    return store


# ============================================================================
# Action Proposals
# ============================================================================


@router.post("/propose")
async def propose_action(
    brand_id: str,
    channel: str,
    action_type: str,
    intent: str,
    proposed_changes: Optional[Dict[str, Any]] = None,
    source_run_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Create a new action proposal, evaluated through PolicyEngine."""
    store = _require_store("Action store", _get_action_store())

    action_dict = {
        "brand_id": brand_id,
        "channel": channel,
        "action_type": action_type,
        "intent": intent,
        "proposed_changes": proposed_changes or {},
        "source_run_id": source_run_id,
        "metadata": metadata or {},
    }

    engine = _get_policy_engine()
    if engine is not None:
        policy_result = engine.evaluate(action_dict)
    else:
        policy_result = {
            "passed": True,
            "risk_tier": "medium",
            "checks": [],
            "violations": [],
            "auto_eligible": False,
            "requires_approval": True,
        }

    action_dict["risk_tier"] = policy_result["risk_tier"]
    action_dict["policy_result"] = policy_result

    record = store.propose_action(action_dict)
    return {
        "action_id": record["action_id"],
        "risk_tier": policy_result["risk_tier"],
        "policy_result": policy_result,
        "approval_state": record["approval_state"],
        "auto_eligible": policy_result.get("auto_eligible", False),
    }


@router.get("/proposals")
async def list_proposals(
    brand_id: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 50,
):
    """List pending and held action proposals."""
    store = _require_store("Action store", _get_action_store())
    proposals = store.list_pending_approvals(brand_id=brand_id, limit=limit)
    if channel:
        proposals = [p for p in proposals if p.get("channel") == channel]
    return {"proposals": proposals, "count": len(proposals)}


@router.get("/proposals/{action_id}")
async def get_proposal(action_id: str):
    """Return full detail for a single proposal."""
    store = _require_store("Action store", _get_action_store())
    action = store.get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Proposal '{action_id}' not found")
    return action


@router.post("/proposals/{action_id}/approve")
async def approve_proposal(action_id: str, note: Optional[str] = None):
    """Approve a pending proposal for execution."""
    store = _require_store("Action store", _get_action_store())
    try:
        record = store.approve_action(action_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Proposal '{action_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "action_id": action_id,
        "approval_state": record["approval_state"],
        "execution_state": record["execution_state"],
    }


@router.post("/proposals/{action_id}/reject")
async def reject_proposal(action_id: str, note: Optional[str] = None):
    """Reject a pending proposal."""
    store = _require_store("Action store", _get_action_store())
    try:
        store.reject_action(action_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Proposal '{action_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"action_id": action_id, "approval_state": "rejected"}


@router.post("/proposals/{action_id}/hold")
async def hold_proposal(action_id: str, note: Optional[str] = None):
    """Place a pending proposal on hold for further review."""
    store = _require_store("Action store", _get_action_store())
    try:
        store.hold_action(action_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Proposal '{action_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"action_id": action_id, "approval_state": "held"}


# ============================================================================
# Action History & Listing
# ============================================================================


@router.get("/history")
async def get_action_history(
    brand_id: Optional[str] = None,
    channel: Optional[str] = None,
    limit: int = 100,
):
    """Return the immutable action audit log."""
    store = _require_store("Action store", _get_action_store())
    entries = store.get_action_log(brand_id=brand_id, limit=limit)
    return {"entries": entries, "count": len(entries)}


@router.get("/actions")
async def list_actions(
    brand_id: Optional[str] = None,
    channel: Optional[str] = None,
    approval_state: Optional[str] = None,
    execution_state: Optional[str] = None,
    limit: int = 50,
):
    """List all actions with optional filters."""
    store = _require_store("Action store", _get_action_store())
    actions = store.list_actions(
        brand_id=brand_id,
        channel=channel,
        approval_state=approval_state,
        execution_state=execution_state,
        limit=limit,
    )
    return {"actions": actions, "count": len(actions)}


@router.get("/actions/{action_id}")
async def get_action(action_id: str):
    """Return a full action record by ID."""
    store = _require_store("Action store", _get_action_store())
    action = store.get_action(action_id)
    if action is None:
        raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
    return action


# ============================================================================
# Integrations
# ============================================================================


@router.get("/integrations")
async def list_integrations(
    brand_id: Optional[str] = None,
    channel: Optional[str] = None,
):
    """List registered integrations."""
    registry = _require_store("Integration registry", _get_integration_registry())
    if brand_id:
        integrations = registry.list_for_brand(brand_id, channel=channel)
    else:
        integrations = []
    return {"integrations": integrations, "count": len(integrations)}


@router.post("/integrations")
async def register_integration(
    brand_id: str,
    channel: str,
    provider: str,
    config: Optional[Dict[str, Any]] = None,
    capabilities: Optional[List[str]] = None,
    metadata: Optional[Dict[str, Any]] = None,
):
    """Register a new marketing integration."""
    registry = _require_store("Integration registry", _get_integration_registry())
    record = registry.register({
        "brand_id": brand_id,
        "channel": channel,
        "provider": provider,
        "status": "connected",
        "config": config or {},
        "capabilities": capabilities or [],
        "metadata": metadata or {},
    })
    return record


@router.post("/integrations/{integration_id}/disconnect")
async def disconnect_integration(integration_id: str):
    """Disconnect an active integration."""
    registry = _require_store("Integration registry", _get_integration_registry())
    try:
        registry.disconnect(integration_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    return {"integration_id": integration_id, "status": "disconnected"}


@router.post("/integrations/{integration_id}/kill-switch")
async def toggle_kill_switch(integration_id: str, enabled: bool = True):
    """Engage or release the kill switch on an integration."""
    registry = _require_store("Integration registry", _get_integration_registry())
    record = registry.get(integration_id)
    if record is None:
        raise HTTPException(status_code=404, detail=f"Integration '{integration_id}' not found")
    brand_id = record["brand_id"]
    channel = record["channel"]
    if enabled:
        registry.activate_kill_switch(brand_id, channel)
    else:
        registry.deactivate_kill_switch(brand_id, channel)
    return {"integration_id": integration_id, "kill_switch": enabled}


# ============================================================================
# Operator Dashboard
# ============================================================================


@router.get("/dashboard")
async def operator_dashboard(brand_id: Optional[str] = None):
    """Operator overview: pending proposals, recent actions, integrations, health."""
    store = _get_action_store()
    registry = _get_integration_registry()

    pending_count = 0
    recent_actions: List[Dict[str, Any]] = []
    if store is not None:
        try:
            pending = store.list_pending_approvals(brand_id=brand_id)
            pending_count = len(pending)
            all_actions = store.list_actions(brand_id=brand_id, limit=10)
            recent_actions = all_actions
        except Exception:
            pass

    active_integrations: List[Dict[str, Any]] = []
    channel_summary: Dict[str, Any] = {}
    if registry is not None and brand_id:
        try:
            integrations = registry.list_for_brand(brand_id)
            active_integrations = integrations
            for integ in integrations:
                ch = integ.get("channel", "unknown")
                if ch not in channel_summary:
                    channel_summary[ch] = {"integrations": 0, "kill_switch_active": False}
                channel_summary[ch]["integrations"] += 1
                if integ.get("kill_switch"):
                    channel_summary[ch]["kill_switch_active"] = True
        except Exception:
            pass

    return {
        "pending_count": pending_count,
        "recent_actions": recent_actions,
        "active_integrations": active_integrations,
        "channel_summary": channel_summary,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "stores_available": {
            "action_store": store is not None,
            "integration_registry": registry is not None,
        },
    }
