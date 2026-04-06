"""Request/response schemas for the Kai gateway."""

from __future__ import annotations

import copy
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Common Models
# ============================================================================


class WebhookRequest(BaseModel):
    """Base request model for all webhook endpoints."""

    client: Optional[str] = Field(
        None,
        description="Client ID from clients_config.json (e.g., 'clawdbot', 'mdi', 'snapped_ai_collective')",
    )
    options: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional options for the command",
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
    run_id: Optional[str] = None
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


class RunSurface(str, Enum):
    """Execution surface for a run."""

    LOCAL = "local"
    REMOTE = "remote"


class ArtifactType(str, Enum):
    """Canonical artifact types for Kai runs."""

    BRIEF = "brief"
    DRAFT = "draft"
    AUDIT_FINDINGS = "audit_findings"
    CAMPAIGN_PLAN = "campaign_plan"
    GATE_PROPOSAL = "gate_proposal"
    APPROVED_ASSET = "approved_asset"
    PUBLISHED_ASSET = "published_asset"
    PERFORMANCE_SNAPSHOT = "performance_snapshot"
    LEARNED_PATTERN = "learned_pattern"


class RunRequest(BaseModel):
    """Canonical run request for local and remote surfaces."""

    intent: str = Field(..., description="User intent driving the run")
    workflow: str = Field(..., description="Workflow name, e.g. generate, audit, plan")
    brand_id: str = Field(..., description="Canonical brand/workspace id")
    surface: RunSurface = Field(default=RunSurface.REMOTE)
    module_set: List[str] = Field(default_factory=list)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RunArtifact(BaseModel):
    """Canonical artifact record attached to a run."""

    artifact_id: str
    run_id: str
    job_id: Optional[str] = None
    artifact_type: ArtifactType
    brand_id: str
    workflow: str
    module_set: List[str] = Field(default_factory=list)
    payload: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class RunResult(BaseModel):
    """Canonical result payload returned by run execution."""

    run_id: str
    job_id: Optional[str] = None
    status: str
    workflow: str
    brand_id: str
    surface: RunSurface = Field(default=RunSurface.REMOTE)
    proposal_id: Optional[str] = None
    brief: Optional[Dict[str, Any]] = None
    gate_report: Optional[Dict[str, Any]] = None
    content_preview: str = ""
    content_length: int = 0
    artifact_ids: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class JobInfo(BaseModel):
    """Information about a job."""

    job_id: str
    run_id: Optional[str] = None
    status: JobStatus
    run_status: Optional[str] = None
    approval_state: Optional[str] = None
    command: str
    client: Optional[str] = None
    workflow: Optional[str] = None
    brand_id: Optional[str] = None
    surface: Optional[RunSurface] = None
    module_set: List[str] = Field(default_factory=list)
    inputs: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    run_outputs: Dict[str, Any] = Field(default_factory=dict)
    runtime_metadata: Dict[str, Any] = Field(default_factory=dict)
    error: Optional[str] = None
    lineage_run_ids: List[str] = Field(default_factory=list)
    artifact_ids: List[str] = Field(default_factory=list)


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
