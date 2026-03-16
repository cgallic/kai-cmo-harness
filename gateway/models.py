"""
Pydantic models for request/response schemas.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ============================================================================
# Common Models
# ============================================================================

class WebhookRequest(BaseModel):
    """Base request model for all webhook endpoints."""
    client: Optional[str] = Field(
        None,
        description="Client ID from clients_config.json (e.g., 'clawdbot', 'mdi', 'snapped_ai_collective')"
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional options for the command"
    )


class WebhookResponse(BaseModel):
    """Standard response for sync webhook endpoints."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AsyncJobResponse(BaseModel):
    """Response for async job endpoints."""
    job_id: str
    status: str = "pending"
    message: str = "Job queued"


# ============================================================================
# Job Models
# ============================================================================

class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class JobInfo(BaseModel):
    """Information about a job."""
    job_id: str
    status: JobStatus
    command: str
    client: Optional[str] = None
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ============================================================================
# Analytics Models
# ============================================================================

class AnalyticsRequest(WebhookRequest):
    """Request for analytics endpoints."""
    start_date: str = Field("30daysAgo", description="Start date (YYYY-MM-DD or NdaysAgo)")
    end_date: str = Field("today", description="End date (YYYY-MM-DD or today)")
    limit: int = Field(30, ge=1, le=100, description="Result limit")


class AnalyticsSummary(BaseModel):
    """Executive summary response."""
    website: Optional[Dict[str, Any]] = None
    search: Optional[Dict[str, Any]] = None
    business: Optional[Dict[str, Any]] = None
    funnel: Optional[Dict[str, Any]] = None


# ============================================================================
# TikTok Models
# ============================================================================

class TikTokRequest(WebhookRequest):
    """Request for TikTok endpoints."""
    pass


class TikTokScrapeRequest(TikTokRequest):
    """Request for TikTok scrape endpoint."""
    max_videos: int = Field(200, ge=1, le=500)
    full_history: bool = False
    min_duration: int = Field(0, ge=0)


class TikTokGenerateRequest(TikTokRequest):
    """Request for TikTok generate endpoint."""
    num_batches: int = Field(2, ge=1, le=5)
    posts_per_batch: int = Field(4, ge=1, le=10)


class TikTokSearchRequest(TikTokRequest):
    """Request for TikTok search endpoint."""
    query: str = Field(..., description="Search query")
    count: int = Field(20, ge=1, le=50)


class TikTokCommentsRequest(TikTokRequest):
    """Request for TikTok comments endpoint."""
    video_id: str = Field(..., description="TikTok video ID")
    count: int = Field(50, ge=1, le=100)


class TikTokTranscriptRequest(TikTokRequest):
    """Request for TikTok transcript endpoint."""
    video_id: str = Field(..., description="TikTok video ID")


# ============================================================================
# Cold Email Models
# ============================================================================

class ColdEmailRequest(WebhookRequest):
    """Request for cold email endpoints."""
    pass


class WarmupStatusResponse(BaseModel):
    """Response for warmup status endpoint."""
    accounts: List[Dict[str, Any]]
    total_warming: int
    ready_to_send: int


# ============================================================================
# Task Models
# ============================================================================

class TaskExtractRequest(WebhookRequest):
    """Request for task extraction endpoint."""
    text: str = Field(..., description="Text to extract tasks from")


# ============================================================================
# Client Models
# ============================================================================

class ClientInfo(BaseModel):
    """Information about a client."""
    id: str
    name: str
    category: str
    description: Optional[str] = None
    url: Optional[str] = None
    status: Optional[str] = None
    ga_property: Optional[str] = None
    gsc_site: Optional[str] = None
