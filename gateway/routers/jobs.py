"""
Jobs router.

Provides access to async job status and results.
"""

from typing import Optional

from fastapi import APIRouter, HTTPException

from gateway.jobs import job_queue
from gateway.models import JobStatus, JobInfo, WebhookResponse

router = APIRouter()


@router.get("", response_model=WebhookResponse)
async def list_jobs(
    status: Optional[str] = None,
    limit: int = 50
):
    """
    List all jobs, optionally filtered by status.

    Query params:
    - status: pending, running, completed, failed
    - limit: max number of jobs to return (default 50)
    """
    job_status = None
    if status:
        try:
            job_status = JobStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: pending, running, completed, failed"
            )

    jobs = job_queue.list_jobs(status=job_status, limit=limit)

    return WebhookResponse(
        success=True,
        data={
            "jobs": [
                {
                    "job_id": j.job_id,
                    "command": j.command,
                    "client": j.client,
                    "status": j.status.value,
                    "created_at": j.created_at.isoformat(),
                    "started_at": j.started_at.isoformat() if j.started_at else None,
                    "completed_at": j.completed_at.isoformat() if j.completed_at else None,
                    "has_result": j.result is not None,
                    "has_error": j.error is not None,
                }
                for j in jobs
            ],
            "total": len(jobs)
        }
    )


@router.get("/{job_id}", response_model=WebhookResponse)
async def get_job(job_id: str):
    """
    Get details for a specific job including result/error.
    """
    job = job_queue.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )

    return WebhookResponse(
        success=True,
        data={
            "job_id": job.job_id,
            "command": job.command,
            "client": job.client,
            "status": job.status.value,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "result": job.result,
            "error": job.error,
        }
    )


@router.get("/{job_id}/status")
async def get_job_status(job_id: str):
    """
    Quick status check for a job (minimal response).
    """
    job = job_queue.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )

    return {
        "job_id": job.job_id,
        "status": job.status.value,
        "completed": job.status in [JobStatus.COMPLETED, JobStatus.FAILED],
        "success": job.status == JobStatus.COMPLETED,
    }


@router.delete("/{job_id}")
async def delete_job(job_id: str):
    """
    Delete a job record (cleanup).
    """
    job = job_queue.get_job(job_id)

    if not job:
        raise HTTPException(
            status_code=404,
            detail=f"Job '{job_id}' not found"
        )

    # Only allow deletion of completed or failed jobs
    if job.status in [JobStatus.PENDING, JobStatus.RUNNING]:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete pending or running jobs"
        )

    # Delete from database
    import sqlite3
    with sqlite3.connect(job_queue.db_path) as conn:
        conn.execute("DELETE FROM jobs WHERE job_id = ?", (job_id,))
        conn.commit()

    return {"message": f"Job '{job_id}' deleted"}
