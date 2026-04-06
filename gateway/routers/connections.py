"""Connection management router.

Handles the full lifecycle of connecting brand accounts through Pipedream:
initiate, confirm, verify, reconnect, disconnect, sync, and health.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()


# ============================================================================
# Lazy import helpers
# ============================================================================


def _get_connection_manager():
    try:
        from kai.runtime.connections import ConnectionManager
        return ConnectionManager()
    except (ImportError, Exception):
        return None


def _get_health_dashboard():
    try:
        from kai.runtime.connector_health import ConnectorHealthDashboard
        return ConnectorHealthDashboard()
    except (ImportError, Exception):
        return None


def _get_state_sync():
    try:
        from gateway.adapters.pipedream.state_sync import PipedreamStateSync
        return PipedreamStateSync()
    except (ImportError, Exception):
        return None


def _get_registry():
    try:
        from kai.runtime.integrations import get_default_integration_registry
        return get_default_integration_registry()
    except (ImportError, Exception):
        return None


def _get_onboarding():
    try:
        from kai.runtime.onboarding import OnboardingFlow
        return OnboardingFlow()
    except (ImportError, Exception):
        return None


def _require(name: str, obj):
    if obj is None:
        raise HTTPException(status_code=503, detail=f"{name} not available")


# ============================================================================
# Request models
# ============================================================================


class InitiateConnectionRequest(BaseModel):
    brand_id: str
    channel: str
    provider: str
    config: Optional[Dict[str, Any]] = None
    allowed_origins: Optional[List[str]] = None
    success_redirect_uri: Optional[str] = None
    error_redirect_uri: Optional[str] = None


class ConfirmConnectionRequest(BaseModel):
    integration_id: str
    connected_account_id: str
    external_user_id: Optional[str] = None
    scopes: Optional[List[str]] = None


class DisconnectRequest(BaseModel):
    delete_pipedream_account: bool = False


class OnboardingChecklistRequest(BaseModel):
    brand_id: str
    archetype: str = "local_service"
    known_client: Optional[str] = None


# ============================================================================
# Connection lifecycle
# ============================================================================


@router.post("/connect")
async def initiate_connection(req: InitiateConnectionRequest):
    """Start the OAuth connection flow for a brand+channel+provider."""
    mgr = _get_connection_manager()
    _require("ConnectionManager", mgr)
    try:
        result = mgr.initiate_connection(
            brand_id=req.brand_id,
            channel=req.channel,
            provider=req.provider,
            config=req.config,
            allowed_origins=req.allowed_origins,
            success_redirect_uri=req.success_redirect_uri,
            error_redirect_uri=req.error_redirect_uri,
        )
        return result
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/confirm")
async def confirm_connection(req: ConfirmConnectionRequest):
    """Confirm an OAuth flow completed — maps Pipedream account to integration."""
    mgr = _get_connection_manager()
    _require("ConnectionManager", mgr)
    try:
        result = mgr.confirm_connection(
            integration_id=req.integration_id,
            connected_account_id=req.connected_account_id,
            external_user_id=req.external_user_id,
            scopes=req.scopes,
        )
        return result
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{integration_id}/verify")
async def verify_connection(integration_id: str):
    """Verify that a connected integration is still healthy."""
    mgr = _get_connection_manager()
    _require("ConnectionManager", mgr)
    try:
        return mgr.verify_connection(integration_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{integration_id}/reconnect")
async def reconnect(integration_id: str):
    """Re-initiate OAuth for an expired or degraded integration."""
    mgr = _get_connection_manager()
    _require("ConnectionManager", mgr)
    try:
        return mgr.reconnect(integration_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/{integration_id}/disconnect")
async def disconnect(integration_id: str, req: DisconnectRequest):
    """Disconnect an integration, preserving history."""
    mgr = _get_connection_manager()
    _require("ConnectionManager", mgr)
    try:
        return mgr.disconnect(
            integration_id,
            delete_pipedream_account=req.delete_pipedream_account,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc))


# ============================================================================
# Brand connection status
# ============================================================================


@router.get("/status/{brand_id}")
async def connection_status(brand_id: str):
    """Get connection status summary for a brand."""
    mgr = _get_connection_manager()
    _require("ConnectionManager", mgr)
    return mgr.get_connection_status(brand_id)


@router.post("/verify-all/{brand_id}")
async def verify_all(brand_id: str):
    """Verify all integrations for a brand."""
    mgr = _get_connection_manager()
    _require("ConnectionManager", mgr)
    return mgr.verify_all(brand_id)


# ============================================================================
# Health dashboard
# ============================================================================


@router.get("/health/{brand_id}")
async def brand_health(brand_id: str):
    """Full health report for a brand's integrations."""
    dashboard = _get_health_dashboard()
    _require("ConnectorHealthDashboard", dashboard)
    return dashboard.brand_health(brand_id)


@router.get("/health/{brand_id}/{channel}")
async def channel_health(brand_id: str, channel: str):
    """Health for a single channel."""
    dashboard = _get_health_dashboard()
    _require("ConnectorHealthDashboard", dashboard)
    return dashboard.channel_health(brand_id, channel)


# ============================================================================
# State sync
# ============================================================================


@router.post("/sync/{brand_id}")
async def sync_all_channels(brand_id: str):
    """Sync state for all connected integrations."""
    sync = _get_state_sync()
    _require("PipedreamStateSync", sync)
    registry = _get_registry()
    _require("IntegrationRegistry", registry)

    integrations = registry.list_for_brand(brand_id)
    results = sync.sync_all(brand_id, integrations)

    # Update last_sync_at on each integration
    for result in results:
        if not result.get("error"):
            for integ in integrations:
                if (
                    integ.get("channel") == result.get("channel")
                    and integ.get("provider") == result.get("provider")
                ):
                    registry.mark_synced(integ["integration_id"])

    return {"brand_id": brand_id, "results": results}


@router.post("/sync/{brand_id}/{channel}/{provider}")
async def sync_single_channel(brand_id: str, channel: str, provider: str):
    """Sync state for a single integration."""
    sync = _get_state_sync()
    _require("PipedreamStateSync", sync)
    registry = _get_registry()
    _require("IntegrationRegistry", registry)

    integrations = registry.list_for_brand(brand_id, channel=channel)
    target = next(
        (i for i in integrations if i.get("provider") == provider),
        None,
    )
    if not target:
        raise HTTPException(
            status_code=404,
            detail=f"No integration for brand={brand_id} channel={channel} provider={provider}",
        )

    acct_id = target.get("connected_account_id")
    if not acct_id:
        raise HTTPException(status_code=400, detail="No connected account — connect first")

    result = sync.sync_channel(
        brand_id=brand_id,
        channel=channel,
        provider=provider,
        connected_account_id=acct_id,
        config=target.get("config", {}),
    )

    if not result.get("error"):
        registry.mark_synced(target["integration_id"])

    return result


# ============================================================================
# Onboarding
# ============================================================================


@router.post("/onboarding/checklist")
async def get_onboarding_checklist(req: OnboardingChecklistRequest):
    """Generate a connection checklist for a new client."""
    flow = _get_onboarding()
    _require("OnboardingFlow", flow)
    return flow.get_connection_checklist(
        req.brand_id,
        archetype=req.archetype,
        known_client=req.known_client,
    )


@router.get("/onboarding/status/{brand_id}")
async def get_onboarding_status(brand_id: str):
    """Get onboarding progress for a brand."""
    flow = _get_onboarding()
    _require("OnboardingFlow", flow)
    return flow.get_onboarding_status(brand_id)


# ============================================================================
# Pipedream webhook receiver
# ============================================================================


@router.post("/webhooks/pipedream/connect")
async def pipedream_connect_webhook(payload: Dict[str, Any]):
    """Receive Pipedream CONNECTION_SUCCESS / CONNECTION_ERROR webhooks.

    Auto-confirms connections when Pipedream notifies us that an OAuth
    flow completed.
    """
    event_type = payload.get("type")

    if event_type == "CONNECTION_SUCCESS":
        account = payload.get("account", {})
        account_id = account.get("id")
        external_user_id = payload.get("external_user_id")

        if not account_id:
            raise HTTPException(status_code=400, detail="Missing account.id")

        # Find the pending integration for this brand
        registry = _get_registry()
        _require("IntegrationRegistry", registry)

        if external_user_id:
            pending = [
                i for i in registry.list_for_brand(external_user_id)
                if i.get("status") == "pending_auth"
            ]
            if pending:
                mgr = _get_connection_manager()
                _require("ConnectionManager", mgr)
                result = mgr.confirm_connection(
                    integration_id=pending[0]["integration_id"],
                    connected_account_id=account_id,
                    external_user_id=external_user_id,
                )
                return {"status": "confirmed", "integration": result}

        return {"status": "received", "event_type": event_type}

    elif event_type == "CONNECTION_ERROR":
        return {"status": "received", "event_type": event_type, "error": payload.get("error")}

    return {"status": "ignored", "event_type": event_type}
