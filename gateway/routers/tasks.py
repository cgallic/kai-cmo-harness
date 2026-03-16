"""
Tasks webhook router.

Exposes task extraction and management via HTTP endpoints.
"""

from fastapi import APIRouter

from gateway.models import (
    TaskExtractRequest,
    WebhookRequest,
    WebhookResponse,
    AsyncJobResponse,
)
from gateway.jobs import job_queue
from gateway.adapters.tasks_adapter import TasksAdapter

router = APIRouter()
adapter = TasksAdapter()


@router.post("/extract", response_model=AsyncJobResponse)
async def extract_tasks(request: TaskExtractRequest):
    """
    Extract tasks from text using AI (async).

    Equivalent to: python scripts/task_extractor.py
    """
    job_id = job_queue.create_job(
        command="task_extract",
        client=request.client,
        options={"text": request.text[:500]}  # Truncate for storage
    )

    job_queue.submit_job(
        job_id,
        adapter.run_extract,
        text=request.text,
        client=request.client,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message="Task extraction job queued"
    )


@router.post("/deduplicate", response_model=WebhookResponse)
async def deduplicate_tasks(request: WebhookRequest):
    """
    Deduplicate tasks from a list.

    Equivalent to: python scripts/task_deduplicator.py
    """
    tasks = request.options.get("tasks", [])

    if not tasks:
        return WebhookResponse(
            success=False,
            error="Missing 'tasks' in options"
        )

    try:
        data = adapter.deduplicate(tasks=tasks)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))
