"""Generate Router - HTTP surface for the Outcome Engine."""

import asyncio
from typing import Optional

from fastapi import APIRouter, HTTPException

from kai.runtime import get_default_runtime_store
from kai.runtime.workflows import get_generation_workflow, list_generation_formats
from gateway.config import config
from gateway.jobs import job_queue
from gateway.models import (
    AsyncJobResponse,
    ArtifactType,
    BaseModel,
    Field,
    RunRequest,
    RunResult,
    RunSurface,
)

router = APIRouter()


class GenerateRequest(BaseModel):
    """Request body for content generation."""

    format: str = Field(..., description="Content format (blog, meta-ads, etc.)")
    site: str = Field(..., description="Site key (kaicalls, buildwithkai, etc.)")
    keyword: str = Field(..., description="Target keyword")
    persona: Optional[str] = Field(None, description="Override persona")
    dry_run: bool = Field(False, description="Generate brief only")
    skip_gates: bool = Field(False, description="Skip quality gates")
    brand_id: Optional[str] = Field(None, description="Canonical brand id; defaults to site")
    workflow: str = Field("content-generate", description="Canonical workflow name")
    surface: RunSurface = Field(default=RunSurface.REMOTE, description="Execution surface")
    module_set: list[str] = Field(default_factory=list, description="Explicit module set override")


def _run_generate(
    format: str,
    site: str,
    keyword: str,
    persona: Optional[str],
    dry_run: bool,
    skip_gates: bool,
    run_context: dict,
    job_id: str,
) -> dict:
    """Run engine.generate() in a thread (called by job_queue)."""
    from scripts.content.engine import generate

    result = asyncio.run(
        generate(
            format=format,
            site=site,
            keyword=keyword,
            persona=persona,
            dry_run=dry_run,
            skip_gates=skip_gates,
            workflow=run_context.get("workflow") or "content-generate",
            surface=run_context.get("surface") or RunSurface.REMOTE.value,
            run_id=run_context.get("run_id") or job_id,
        )
    )

    brand = result.metadata.get("brand", {}) if isinstance(result.metadata, dict) else {}
    modules = result.metadata.get("modules", []) if isinstance(result.metadata, dict) else []
    module_ids = [m.get("id") for m in modules if isinstance(m, dict) and m.get("id")]
    brand_id = brand.get("id") or run_context.get("brand_id") or site
    run_id = result.metadata.get("run_id") or run_context.get("run_id") or job_id
    workflow = run_context.get("workflow") or "content-generate"
    surface = run_context.get("surface") or RunSurface.REMOTE.value
    runtime_artifact_refs = result.metadata.get("artifact_refs", {}) if isinstance(result.metadata, dict) else {}
    artifact_ids = list(runtime_artifact_refs.values())

    if artifact_ids:
        runtime_store = get_default_runtime_store()
        for artifact_id in artifact_ids:
            artifact = runtime_store.get_artifact(artifact_id)
            if not artifact:
                continue
            job_queue.record_artifact(
                run_id=run_id,
                artifact_type=artifact.get("artifact_type", ArtifactType.DRAFT),
                brand_id=brand_id,
                workflow=workflow,
                payload=artifact.get("data", {}),
                job_id=job_id,
                module_set=artifact.get("module_set", module_ids),
            )
    else:
        brief_artifact_id = job_queue.record_artifact(
            run_id=run_id,
            artifact_type=ArtifactType.BRIEF,
            brand_id=brand_id,
            workflow=workflow,
            payload={"brief": result.brief, "metadata": result.metadata},
            job_id=job_id,
            module_set=module_ids,
        )
        artifact_ids.append(brief_artifact_id)

        if result.content:
            content_artifact_type = (
                ArtifactType.APPROVED_ASSET if result.status == "approved" else ArtifactType.DRAFT
            )
            content_artifact_id = job_queue.record_artifact(
                run_id=run_id,
                artifact_type=content_artifact_type,
                brand_id=brand_id,
                workflow=workflow,
                payload={
                    "content_preview": result.content[:2000],
                    "content_length": len(result.content),
                    "status": result.status,
                    "proposal_id": result.proposal_id,
                    "gate_report": result.gate_report,
                },
                job_id=job_id,
                module_set=module_ids,
            )
            artifact_ids.append(content_artifact_id)

    run_result = RunResult(
        run_id=run_id,
        job_id=job_id,
        status=result.status,
        workflow=workflow,
        brand_id=brand_id,
        surface=RunSurface(surface),
        proposal_id=result.proposal_id,
        brief=result.brief,
        gate_report=result.gate_report,
        content_preview=result.content[:500] if result.content else "",
        content_length=len(result.content) if result.content else 0,
        artifact_ids=artifact_ids,
        metadata=result.metadata,
    )

    return {
        "run_id": run_result.run_id,
        "job_id": run_result.job_id,
        "status": run_result.status,
        "workflow": run_result.workflow,
        "brand_id": run_result.brand_id,
        "surface": run_result.surface.value,
        "proposal_id": run_result.proposal_id,
        "brief": run_result.brief,
        "gate_report": run_result.gate_report,
        "content_preview": run_result.content_preview,
        "content_length": run_result.content_length,
        "artifact_ids": run_result.artifact_ids,
        "metadata": run_result.metadata,
        "module_set": module_ids,
    }


@router.post("", response_model=AsyncJobResponse)
async def create_generate_job(req: GenerateRequest):
    """Queue a content generation job."""
    workspace = config.workspace_profile
    workflow_definition = get_generation_workflow(req.format)
    if not workflow_definition or not workflow_definition.content_format:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Unsupported workflow or format: {req.format}",
                "valid_formats": sorted(list_generation_formats()),
            },
        )
    canonical_format = workflow_definition.content_format
    brand = workspace.get_brand(req.brand_id or req.site)
    module_set = req.module_set or (brand.module_ids if brand else [])
    canonical_workflow = (
        workflow_definition.workflow_id
        if req.workflow == "content-generate"
        else req.workflow
    )
    run_context = RunRequest(
        intent=f"Generate {canonical_format} for {req.site}: {req.keyword}",
        workflow=canonical_workflow,
        brand_id=req.brand_id or req.site,
        surface=req.surface,
        module_set=module_set,
        inputs={
            "format": canonical_format,
            "requested_format": req.format,
            "workflow_id": workflow_definition.workflow_id,
            "site": req.site,
            "keyword": req.keyword,
            "persona": req.persona,
            "dry_run": req.dry_run,
            "skip_gates": req.skip_gates,
        },
        metadata={
            "source": "gateway.generate",
            "workspace_id": workspace.workspace_id,
            "workflow_definition": workflow_definition.model_dump(),
        },
    )
    run_context_payload = run_context.model_dump() | {
        "surface": run_context.surface.value,
        "run_id": None,
    }

    job_id = job_queue.create_job(
        command="generate",
        client=req.site,
        options=run_context.inputs | {"brand_id": run_context.brand_id, "workflow": run_context.workflow},
        run_request=run_context_payload,
    )
    run_context_payload["run_id"] = job_id

    job_queue.submit_job(
        job_id,
        _run_generate,
        canonical_format,
        req.site,
        req.keyword,
        req.persona,
        req.dry_run,
        req.skip_gates,
        run_context_payload,
        job_id,
    )

    return AsyncJobResponse(
        job_id=job_id,
        run_id=job_id,
        status="queued",
        message=f"Generating {canonical_format} for {req.site}: {req.keyword}",
    )


@router.get("/{job_id}")
async def get_generate_job(job_id: str):
    """Check status of a generation job."""
    job = job_queue.get_job(job_id)
    if not job:
        return {"error": f"Job {job_id} not found"}
    return job
