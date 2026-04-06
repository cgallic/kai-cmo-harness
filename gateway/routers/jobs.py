"""Jobs router."""

from typing import Optional

from fastapi import APIRouter, HTTPException

from kai.runtime import get_default_runtime_store
from gateway.jobs import job_queue
from gateway.models import JobStatus, WebhookResponse

router = APIRouter()


@router.get("", response_model=WebhookResponse)
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50,
):
    """List all jobs, optionally filtered by status."""
    job_status = None
    if status:
        try:
            job_status = JobStatus(status)
        except ValueError as exc:
            raise HTTPException(
                status_code=400,
                detail="Invalid status. Must be one of: pending, running, completed, failed",
            ) from exc

    jobs = job_queue.list_jobs(status=job_status, limit=limit)

    return WebhookResponse(
        success=True,
        data={
            "jobs": [
                {
                    "job_id": j.job_id,
                    "run_id": j.run_id,
                    "status": j.status.value,
                    "run_status": j.run_status,
                    "approval_state": j.approval_state,
                    "command": j.command,
                    "client": j.client,
                    "workflow": j.workflow,
                    "brand_id": j.brand_id,
                    "surface": j.surface.value if j.surface else None,
                    "module_set": j.module_set,
                    "inputs": j.inputs,
                    "metadata": j.metadata,
                    "runtime_metadata": j.runtime_metadata,
                    "created_at": j.created_at.isoformat(),
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "lineage_run_ids": j.lineage_run_ids,
                    "artifact_ids": j.artifact_ids,
                    "artifact_count": len(j.artifact_ids),
                    "has_result": j.result is not None,
                    "has_error": j.error is not None,
                }
                for j in jobs
            ],
            "total": len(jobs),
        },
    )


@router.get("/{job_id}", response_model=WebhookResponse)
async def get_job(job_id: str):
    """Get details for a specific job including result/error."""
    job = job_queue.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return WebhookResponse(
        success=True,
        data={
            "job_id": job.job_id,
            "run_id": job.run_id,
            "status": job.status.value,
            "run_status": job.run_status,
            "approval_state": job.approval_state,
            "command": job.command,
            "client": job.client,
            "workflow": job.workflow,
            "brand_id": job.brand_id,
            "surface": job.surface.value if job.surface else None,
            "module_set": job.module_set,
            "inputs": job.inputs,
            "metadata": job.metadata,
            "runtime_metadata": job.runtime_metadata,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "run_outputs": job.run_outputs,
            "error": job.error,
            "lineage_run_ids": job.lineage_run_ids,
            "artifact_ids": job.artifact_ids,
            "artifact_count": len(job.artifact_ids),
        },
    )


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """Quick status check for a job (minimal response)."""
    job = job_queue.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    return {
        "job_id": job.job_id,
        "run_id": job.run_id,
        "status": job.status.value,
        "run_status": job.run_status,
        "approval_state": job.approval_state,
        "completed": job.status in [JobStatus.COMPLETED, JobStatus.FAILED],
        "success": job.status == JobStatus.COMPLETED,
        "artifact_count": len(job.artifact_ids),
    }


@router.get("/{job_id}/artifacts", response_model=WebhookResponse)
async def list_job_artifacts(job_id: str):
    """List artifacts attached to a job/run."""
    job = job_queue.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    runtime_store = get_default_runtime_store()
    artifacts = runtime_store.list_artifacts(run_id=job.run_id) if job.run_id else []
    if not artifacts:
        artifacts = job_queue.list_artifacts(run_id=job.run_id, job_id=job.job_id)

    return WebhookResponse(
        success=True,
        data={
            "job_id": job.job_id,
            "run_id": job.run_id,
            "artifacts": artifacts,
            "total": len(artifacts),
        },
    )


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """Delete a job record (cleanup)."""
    job = job_queue.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(status_code=400, detail="Cannot delete pending or running jobs")

    import sqlite3

    with sqlite3.connect(job_queue.db_path) as conn:
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        conn.execute("DELETE FROM runs WHERE job_id = ? OR run_id = ?", (job_id, job_id))
        conn.execute(
            "DELETE FROM artifacts WHERE job_id = ? OR run_id = ?",
            (job_id, job_id),
        )
        conn.commit()

    return {"message": f"Job '{job_id}' deleted"}
