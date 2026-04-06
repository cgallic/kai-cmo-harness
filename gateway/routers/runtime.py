"""Runtime metadata and approval lifecycle endpoints for the Kai remote runner."""

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException

from kai.runtime import (
    get_default_runtime_store,
    load_module_manifests,
    load_workspace_profile,
)


router = APIRouter()


@router.get("/workspace")
async def get_workspace():
    """Return the canonical Kai workspace profile."""
    workspace = load_workspace_profile()
    return workspace.model_dump()


@router.get("/brands")
async def list_brands():
    """List brands configured in the Kai workspace."""
    workspace = load_workspace_profile()
    return {
        "brands": [brand.model_dump() for brand in workspace.brands],
        "count": len(workspace.brands),
    }


@router.get("/modules")
async def list_modules():
    """List available module manifests."""
    manifests = load_module_manifests()
    return {
        "modules": [manifest.model_dump() for manifest in manifests.values()],
        "count": len(manifests),
    }


@router.get("/state")
async def get_runtime_state():
    """Return the derived runtime state snapshot."""
    store = get_default_runtime_store()
    state = store.get_state() or store.snapshot_state()
    return state


@router.get("/runs")
async def list_runs(
    brand_id: Optional[str] = None,
    workflow: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """List persisted runtime runs."""
    store = get_default_runtime_store()
    runs = store.list_runs(
        brand_id=brand_id,
        workflow=workflow,
        status=status,
        limit=limit,
    )
    return {
        "runs": runs,
        "count": len(runs),
    }


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get a specific runtime run record."""
    store = get_default_runtime_store()
    run = store.get_run(run_id)
    if not run:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return run


@router.get("/runs/{run_id}/lineage")
async def get_run_lineage(run_id: str):
    """Return the full run lineage with attached artifacts."""
    store = get_default_runtime_store()
    bundle = store.get_run_bundle(run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return {
        "run_id": run_id,
        "lineage": bundle["lineage"],
        "artifact_count": len(bundle["artifacts"]),
        "artifacts": bundle["artifacts"],
        "approval": bundle["approval"],
        "observability": bundle["observability"],
    }


@router.get("/runs/{run_id}/bundle")
async def get_run_bundle(run_id: str):
    """Return the canonical run bundle for observability and replay."""
    store = get_default_runtime_store()
    bundle = store.get_run_bundle(run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return bundle


@router.get("/approvals")
async def list_approvals(
    brand_id: Optional[str] = None,
    workflow: Optional[str] = None,
    status: Optional[str] = None,
    limit: int = 50,
):
    """List runs that reached an approval or hold decision."""
    store = get_default_runtime_store()
    approvals = store.list_approvals(
        brand_id=brand_id,
        workflow=workflow,
        status=status,
        limit=limit,
    )
    return {
        "approvals": approvals,
        "count": len(approvals),
        "observability": (store.get_state() or store.snapshot_state()).get("observability", {}),
    }


@router.get("/approvals/{run_id}")
async def get_approval(run_id: str):
    """Return approval context for a specific run."""
    store = get_default_runtime_store()
    bundle = store.get_run_bundle(run_id)
    if not bundle:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    return {
        "run_id": run_id,
        "approval": bundle["approval"],
        "run": bundle["run"],
        "lineage": bundle["lineage"],
    }


@router.get("/artifacts")
async def list_artifacts(
    brand_id: Optional[str] = None,
    workflow: Optional[str] = None,
    artifact_type: Optional[str] = None,
    run_id: Optional[str] = None,
    limit: int = 50,
):
    """List persisted runtime artifacts."""
    store = get_default_runtime_store()
    artifacts = store.list_artifacts(
        brand_id=brand_id,
        workflow=workflow,
        artifact_type=artifact_type,
        run_id=run_id,
        limit=limit,
    )
    return {
        "artifacts": artifacts,
        "count": len(artifacts),
    }


@router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str):
    """Get a specific runtime artifact record."""
    store = get_default_runtime_store()
    artifact = store.get_artifact(artifact_id)
    if not artifact:
        return {"error": f"Artifact '{artifact_id}' not found"}
    return artifact


# ------------------------------------------------------------------
# Approval lifecycle mutations
# ------------------------------------------------------------------


@router.post("/runs/{run_id}/approve")
async def approve_run(run_id: str, note: Optional[str] = None):
    """Approve a run, triggering memory writeback."""
    store = get_default_runtime_store()
    try:
        record = store.approve_run(run_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    bundle = store.get_run_bundle(run_id)
    return {
        "run_id": run_id,
        "status": record["status"],
        "approval": (bundle or {}).get("approval"),
        "memory_updates": (bundle or {}).get("memory_updates", []),
    }


@router.post("/runs/{run_id}/hold")
async def hold_run(run_id: str, note: Optional[str] = None):
    """Place a run on hold pending human review."""
    store = get_default_runtime_store()
    try:
        record = store.hold_run(run_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"run_id": run_id, "status": record["status"]}


@router.post("/runs/{run_id}/revise")
async def request_revision(run_id: str, note: str = ""):
    """Request a revision, moving the run back to draft."""
    store = get_default_runtime_store()
    if not note:
        raise HTTPException(status_code=400, detail="A revision note is required")
    try:
        record = store.request_revision(run_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"run_id": run_id, "status": record["status"]}


@router.post("/runs/{run_id}/reject")
async def reject_run(run_id: str, note: Optional[str] = None):
    """Reject a run permanently."""
    store = get_default_runtime_store()
    try:
        record = store.reject_run(run_id, note=note)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {"run_id": run_id, "status": record["status"]}


@router.post("/runs/{run_id}/resume")
async def resume_run(
    run_id: str,
    inputs_override: Optional[Dict[str, Any]] = None,
):
    """Create a child run from a prior run for revision continuation."""
    store = get_default_runtime_store()
    try:
        child = store.resume_run(run_id, inputs_override=inputs_override)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    return {
        "parent_run_id": run_id,
        "child_run_id": child["run_id"],
        "status": child["status"],
    }
