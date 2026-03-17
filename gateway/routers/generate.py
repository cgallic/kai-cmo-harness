"""
Generate Router — HTTP surface for the Outcome Engine.

POST /generate   → queue a content generation job
GET  /generate/{job_id} → check job status / retrieve result
"""

import asyncio
from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from gateway.jobs import job_queue
from gateway.models import AsyncJobResponse

router = APIRouter()


class GenerateRequest(BaseModel):
    """Request body for content generation."""
    format: str = Field(..., description="Content format (blog, meta-ads, etc.)")
    site: str = Field(..., description="Site key (kaicalls, buildwithkai, etc.)")
    keyword: str = Field(..., description="Target keyword")
    persona: Optional[str] = Field(None, description="Override persona")
    dry_run: bool = Field(False, description="Generate brief only")
    skip_gates: bool = Field(False, description="Skip quality gates")


def _run_generate(format: str, site: str, keyword: str,
                  persona: Optional[str], dry_run: bool, skip_gates: bool) -> dict:
    """Run engine.generate() in a thread (called by job_queue)."""
    from scripts.content.engine import generate

    result = asyncio.run(generate(
        format=format,
        site=site,
        keyword=keyword,
        persona=persona,
        dry_run=dry_run,
        skip_gates=skip_gates,
    ))

    return {
        "status": result.status,
        "proposal_id": result.proposal_id,
        "brief": result.brief,
        "gate_report": result.gate_report,
        "content_preview": result.content[:500] if result.content else "",
        "content_length": len(result.content) if result.content else 0,
        "metadata": result.metadata,
    }


@router.post("", response_model=AsyncJobResponse)
async def create_generate_job(req: GenerateRequest):
    """Queue a content generation job."""
    job_id = job_queue.create_job(
        command="generate",
        client=req.site,
        options={
            "format": req.format,
            "site": req.site,
            "keyword": req.keyword,
            "persona": req.persona,
            "dry_run": req.dry_run,
            "skip_gates": req.skip_gates,
        },
    )

    job_queue.submit_job(
        job_id,
        _run_generate,
        req.format, req.site, req.keyword,
        req.persona, req.dry_run, req.skip_gates,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="queued",
        message=f"Generating {req.format} for {req.site}: {req.keyword}",
    )


@router.get("/{job_id}")
async def get_generate_job(job_id: str):
    """Check status of a generation job."""
    job = job_queue.get_job(job_id)
    if not job:
        return {"error": f"Job {job_id} not found"}
    return job
