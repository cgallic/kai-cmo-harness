"""
TikTok webhook router.

Exposes scripts/tiktok CLI commands via HTTP endpoints.
"""

from fastapi import APIRouter

from gateway.models import (
    WebhookRequest,
    WebhookResponse,
    AsyncJobResponse,
    TikTokScrapeRequest,
    TikTokGenerateRequest,
    TikTokSearchRequest,
    TikTokCommentsRequest,
    TikTokTranscriptRequest,
)
from gateway.jobs import job_queue
from gateway.adapters.tiktok_adapter import TikTokAdapter

router = APIRouter()
adapter = TikTokAdapter()


@router.post("/stats", response_model=WebhookResponse)
async def tiktok_stats(request: WebhookRequest):
    """
    Get TikTok account statistics.

    Equivalent to: python -m scripts.tiktok.cli stats
    """
    try:
        data = await adapter.get_stats(client=request.client)
        return WebhookResponse(success=True, data=data)
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/videos", response_model=WebhookResponse)
async def tiktok_videos(request: WebhookRequest):
    """
    Get recent TikTok videos.

    Equivalent to: python -m scripts.tiktok.cli videos
    """
    try:
        days = request.options.get("days", 7)
        limit = request.options.get("limit", 20)
        data = await adapter.get_videos(
            client=request.client,
            days=days,
            limit=limit
        )
        return WebhookResponse(success=True, data={"videos": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/winners", response_model=WebhookResponse)
async def tiktok_winners(request: WebhookRequest):
    """
    Get TikTok winner videos.

    Equivalent to: python -m scripts.tiktok.cli winners
    """
    try:
        limit = request.options.get("limit", 20)
        tier = request.options.get("tier")
        status = request.options.get("status")
        data = await adapter.get_winners(
            client=request.client,
            limit=limit,
            tier=tier,
            status=status
        )
        return WebhookResponse(success=True, data={"winners": data})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/scrape", response_model=AsyncJobResponse)
async def tiktok_scrape(request: TikTokScrapeRequest):
    """
    Start a TikTok scrape job (async).

    Equivalent to: python -m scripts.tiktok.cli scrape
    """
    job_id = job_queue.create_job(
        command="tiktok_scrape",
        client=request.client,
        options={
            "max_videos": request.max_videos,
            "full_history": request.full_history,
            "min_duration": request.min_duration,
        }
    )

    # Submit to thread pool
    job_queue.submit_job(
        job_id,
        adapter.run_scrape,
        client=request.client,
        max_videos=request.max_videos,
        full_history=request.full_history,
        min_duration=request.min_duration,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message="TikTok scrape job queued"
    )


@router.post("/detect-winners", response_model=AsyncJobResponse)
async def tiktok_detect_winners(request: WebhookRequest):
    """
    Start winner detection job (async).

    Equivalent to: python -m scripts.tiktok.cli detect-winners
    """
    lookback = request.options.get("lookback", 30)
    age = request.options.get("age", 72)

    job_id = job_queue.create_job(
        command="tiktok_detect_winners",
        client=request.client,
        options={"lookback": lookback, "age": age}
    )

    job_queue.submit_job(
        job_id,
        adapter.run_detect_winners,
        client=request.client,
        lookback_days=lookback,
        video_age_limit=age,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message="Winner detection job queued"
    )


@router.post("/generate", response_model=AsyncJobResponse)
async def tiktok_generate(request: TikTokGenerateRequest):
    """
    Generate TikTok posts using Claude AI (async).

    Equivalent to: python -m scripts.tiktok.cli generate
    """
    job_id = job_queue.create_job(
        command="tiktok_generate",
        client=request.client,
        options={
            "num_batches": request.num_batches,
            "posts_per_batch": request.posts_per_batch,
        }
    )

    job_queue.submit_job(
        job_id,
        adapter.run_generate,
        client=request.client,
        num_batches=request.num_batches,
        posts_per_batch=request.posts_per_batch,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message="TikTok content generation job queued"
    )


@router.post("/metrics", response_model=AsyncJobResponse)
async def tiktok_metrics(request: WebhookRequest):
    """
    Update video metrics (async).

    Equivalent to: python -m scripts.tiktok.cli metrics
    """
    limit = request.options.get("limit", 50)

    job_id = job_queue.create_job(
        command="tiktok_metrics",
        client=request.client,
        options={"limit": limit}
    )

    job_queue.submit_job(
        job_id,
        adapter.run_metrics_update,
        client=request.client,
        limit=limit,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message="Metrics update job queued"
    )


@router.post("/search", response_model=WebhookResponse)
async def tiktok_search(request: TikTokSearchRequest):
    """
    Search TikTok videos by keyword.

    Equivalent to: python -m scripts.tiktok.cli search "query"
    """
    try:
        videos = await adapter.search_videos(
            query=request.query,
            count=request.count,
        )
        return WebhookResponse(success=True, data={"videos": videos, "query": request.query})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/comments", response_model=WebhookResponse)
async def tiktok_comments(request: TikTokCommentsRequest):
    """
    Get comments for a TikTok video.

    Equivalent to: python -m scripts.tiktok.cli comments <video_id>
    """
    try:
        comments = await adapter.get_comments(
            video_id=request.video_id,
            count=request.count,
        )
        return WebhookResponse(success=True, data={"comments": comments, "video_id": request.video_id})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))


@router.post("/transcript", response_model=AsyncJobResponse)
async def tiktok_transcript(request: TikTokTranscriptRequest):
    """
    Transcribe a TikTok video (async - downloads video + Gemini AI).

    Equivalent to: python -m scripts.tiktok.cli transcribe <video_id>
    """
    job_id = job_queue.create_job(
        command="tiktok_transcript",
        client=request.client,
        options={"video_id": request.video_id}
    )

    job_queue.submit_job(
        job_id,
        adapter.transcribe_video,
        video_id=request.video_id,
    )

    return AsyncJobResponse(
        job_id=job_id,
        status="pending",
        message=f"Transcript job queued for video {request.video_id}"
    )


@router.get("/clients", response_model=WebhookResponse)
async def tiktok_clients():
    """
    List available TikTok clients for post generation.

    Equivalent to: python -m scripts.tiktok.cli clients
    """
    try:
        clients = adapter.list_clients()
        return WebhookResponse(success=True, data={"clients": clients})
    except Exception as e:
        return WebhookResponse(success=False, error=str(e))
