"""Kai Operator API router for the FastAPI gateway.

Exposes the Kai operator surface over HTTP with structured JSON
responses.  Routes follow the existing gateway patterns established in
``gateway/routers/actions.py`` and ``gateway/routers/runtime.py``.

All routes require API key authentication via the ``x-api-key`` header
(reusing the ``verify_api_key`` dependency from ``gateway/auth.py``).
"""

from __future__ import annotations

import os
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query

router = APIRouter()


# ============================================================================
# Lazy surface construction
# ============================================================================


def _get_surface():
    """Lazily construct a RemoteOperatorSurface.

    The workspace directory is resolved from the ``KAI_WORKSPACE_DIR``
    environment variable, falling back to ``./workspace`` relative to
    the project root.
    """
    try:
        from kai.operator.remote_surface import RemoteOperatorSurface
    except ImportError:
        return None

    workspace_dir = os.environ.get(
        "KAI_WORKSPACE_DIR",
        os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "workspace"),
    )
    return RemoteOperatorSurface(workspace_dir=workspace_dir)


def _require_surface():
    surface = _get_surface()
    if surface is None:
        raise HTTPException(
            status_code=503,
            detail="Kai operator surface not available",
        )
    return surface


# ============================================================================
# Audit
# ============================================================================


@router.get("/audit/{business_id}")
async def get_audit(
    business_id: str,
    scope: str = Query("full", description="Audit scope: full, website, seo, social, ads, lifecycle"),
):
    """Run or retrieve the latest audit for a business."""
    surface = _require_surface()
    try:
        result = surface.get_audit(business_id, scope=scope)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Proposals
# ============================================================================


@router.get("/proposals/{business_id}")
async def list_proposals(
    business_id: str,
    status: str = Query("pending", description="Filter: pending, approved, rejected, all"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Results per page"),
):
    """List proposals for a business with pagination."""
    surface = _require_surface()
    try:
        result = surface.get_proposals(
            business_id,
            status_filter=status,
            channel=channel,
            page=page,
            page_size=page_size,
        )
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.get("/proposals/{business_id}/{action_id}")
async def get_proposal_detail(business_id: str, action_id: str):
    """Return full detail for a single proposal."""
    surface = _require_surface()
    try:
        result = surface.get_proposal_detail(business_id, action_id)
        if not result.proposal:
            raise HTTPException(status_code=404, detail=f"Proposal '{action_id}' not found")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Approve / Reject / Execute
# ============================================================================


@router.post("/proposals/{action_id}/approve")
async def approve_action(action_id: str, body: Dict[str, Any]):
    """Approve a pending proposal."""
    surface = _require_surface()
    try:
        from kai.operator.remote_surface import ApprovalRequest
        request = ApprovalRequest(
            action_id=action_id,
            approved_by=body.get("approved_by", "operator"),
            notes=body.get("notes"),
        )
        result = surface.approve_action(request)
        if result.status == "error":
            if result.next_action == "not_found":
                raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
            raise HTTPException(status_code=400, detail=f"Cannot approve: {result.next_action}")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/proposals/{action_id}/reject")
async def reject_action(action_id: str, body: Dict[str, Any]):
    """Reject a pending proposal with feedback."""
    surface = _require_surface()
    try:
        from kai.operator.remote_surface import RejectionRequest
        reason = body.get("reason", "")
        if not reason:
            raise HTTPException(status_code=400, detail="Rejection reason is required")
        request = RejectionRequest(
            action_id=action_id,
            rejected_by=body.get("rejected_by", "operator"),
            reason=reason,
            category=body.get("category"),
            specific_issues=body.get("specific_issues", []),
            revision_guidance=body.get("revision_guidance"),
            do_not_retry=body.get("do_not_retry", False),
        )
        result = surface.reject_action(request)
        if result.status == "error":
            if result.next_action == "not_found":
                raise HTTPException(status_code=404, detail=f"Action '{action_id}' not found")
            raise HTTPException(status_code=400, detail=f"Cannot reject: {result.next_action}")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.post("/proposals/{action_id}/execute")
async def execute_action(action_id: str, body: Optional[Dict[str, Any]] = None):
    """Execute an approved action."""
    surface = _require_surface()
    business_id = (body or {}).get("business_id", "")
    try:
        result = surface.execute_action(business_id, action_id)
        if result.get("status") == "error":
            error_msg = result.get("error", "Unknown error")
            if "not found" in error_msg.lower():
                raise HTTPException(status_code=404, detail=error_msg)
            raise HTTPException(status_code=400, detail=error_msg)
        return result
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Status
# ============================================================================


@router.get("/status/{business_id}")
async def get_status(business_id: str):
    """Return system status for a business."""
    surface = _require_surface()
    try:
        result = surface.get_status(business_id)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# History
# ============================================================================


@router.get("/history/{business_id}")
async def get_history(
    business_id: str,
    days: int = Query(30, ge=1, description="Number of days to look back"),
    channel: Optional[str] = Query(None, description="Filter by channel"),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
):
    """Return action history for a business."""
    surface = _require_surface()
    try:
        return surface.get_history(business_id, days=days, channel=channel, limit=limit)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Dashboard
# ============================================================================


@router.get("/dashboard/{business_id}")
async def get_dashboard(business_id: str):
    """Return a high-level dashboard summary."""
    surface = _require_surface()
    try:
        result = surface.get_dashboard(business_id)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Watchers
# ============================================================================


@router.get("/watchers/{business_id}")
async def get_watchers(business_id: str):
    """Return watcher state and recent findings."""
    surface = _require_surface()
    try:
        result = surface.get_watchers(business_id)
        return result.model_dump()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


# ============================================================================
# Profile
# ============================================================================


@router.get("/profile/{business_id}")
async def get_profile(business_id: str):
    """Return the business profile."""
    surface = _require_surface()
    try:
        result = surface.get_profile(business_id)
        if not result.profile:
            raise HTTPException(status_code=404, detail=f"Profile '{business_id}' not found")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@router.put("/profile/{business_id}")
async def update_profile(business_id: str, body: Dict[str, Any]):
    """Update safe fields on the business profile."""
    surface = _require_surface()
    try:
        from kai.operator.remote_surface import ProfileUpdateRequest
        fields = body.get("fields", body)
        # Strip out protected fields from the input
        _protected = {"business_id", "id", "archetype", "created_at"}
        safe_fields = {k: v for k, v in fields.items() if k not in _protected}
        if not safe_fields:
            raise HTTPException(status_code=400, detail="No updateable fields provided")
        request = ProfileUpdateRequest(fields=safe_fields)
        result = surface.update_profile(business_id, request)
        if not result.profile:
            raise HTTPException(status_code=404, detail=f"Profile '{business_id}' not found")
        return result.model_dump()
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
