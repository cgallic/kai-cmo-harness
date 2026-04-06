"""Social platform connector base — abstract interface and shared data models.

Defines the SocialConnector ABC and Pydantic models that every platform
connector must implement.  All concrete connectors inherit from
SocialConnector and fill in platform-specific API details while the base
handles rate-limit bookkeeping, post validation, and sandbox helpers.
"""

from __future__ import annotations

import copy
import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Type

# ---------------------------------------------------------------------------
# Pydantic import with fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
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

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================


class SocialConnectorConfig(BaseModel):
    """Configuration for a social platform connector."""

    platform: str = Field(..., description="Platform name (facebook, instagram, linkedin, tiktok, youtube)")
    api_key: Optional[str] = Field(None, description="API key if applicable")
    api_secret: Optional[str] = Field(None, description="API secret if applicable")
    access_token: Optional[str] = Field(None, description="OAuth access token")
    refresh_token: Optional[str] = Field(None, description="OAuth refresh token")
    token_expiry: Optional[str] = Field(None, description="ISO timestamp when access token expires")
    page_id: Optional[str] = Field(None, description="Platform-specific page/account identifier")
    sandbox_mode: bool = Field(True, description="When True, no real API calls are made")
    rate_limit_rpm: int = Field(60, description="Requests per minute cap")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Catch-all for platform-specific config")


class SocialPost(BaseModel):
    """A social media post destined for — or retrieved from — a platform."""

    id: Optional[str] = Field(None, description="Platform-assigned post ID (None before publishing)")
    platform: str = Field(..., description="Which platform this post targets")
    content_text: str = Field(..., description="The caption / text body")
    media_urls: List[str] = Field(default_factory=list, description="URLs or local paths to media files")
    media_type: Optional[str] = Field(
        None,
        description="One of: image, video, carousel, reel, story, short, or None",
    )
    link_url: Optional[str] = Field(None, description="URL to include in the post (if supported)")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags to include")
    location_tag: Optional[str] = Field(None, description="Location / geo tag identifier")
    schedule_time: Optional[str] = Field(
        None,
        description="ISO timestamp for scheduled publishing (None = publish immediately)",
    )
    status: str = Field("draft", description="One of: draft, pending_approval, approved, scheduled, published, failed")
    published_at: Optional[str] = Field(None, description="ISO timestamp when actually published")
    published_url: Optional[str] = Field(None, description="URL to the live post")
    error_message: Optional[str] = Field(None, description="Error details if status is 'failed'")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SocialMetrics(BaseModel):
    """Engagement metrics for a single social post."""

    post_id: str = Field(..., description="The post this metrics object refers to")
    platform: str = Field(..., description="Platform name")
    impressions: int = Field(0)
    reach: int = Field(0)
    likes: int = Field(0)
    comments: int = Field(0)
    shares: int = Field(0)
    saves: int = Field(0)
    clicks: int = Field(0)
    video_views: int = Field(0)
    engagement_rate: float = Field(
        0.0,
        description="Calculated as (likes+comments+shares+saves) / reach",
    )
    fetched_at: Optional[str] = Field(None, description="ISO timestamp when metrics were last pulled")


class AudienceInsights(BaseModel):
    """Audience demographics and behaviour data for an account."""

    platform: str = Field(..., description="Platform name")
    total_followers: int = Field(0)
    follower_growth_30d: int = Field(0)
    top_locations: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {location, percentage}",
    )
    age_gender_breakdown: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {age_range, gender, percentage}",
    )
    active_hours: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of {day, hour, engagement_level}",
    )
    fetched_at: Optional[str] = Field(None, description="ISO timestamp")


class MediaRequirements(BaseModel):
    """Platform-specific media constraints."""

    platform: str = Field(..., description="Platform name")
    max_image_size_mb: float = Field(...)
    max_video_size_mb: float = Field(...)
    max_video_duration_seconds: int = Field(...)
    supported_image_formats: List[str] = Field(default_factory=list, description='e.g., ["jpg", "png", "webp"]')
    supported_video_formats: List[str] = Field(default_factory=list, description='e.g., ["mp4", "mov"]')
    aspect_ratios: Dict[str, str] = Field(
        default_factory=dict,
        description='Mapping content type to recommended ratio, e.g., {"feed": "1:1", "story": "9:16"}',
    )
    max_caption_length: int = Field(...)
    max_hashtags: int = Field(...)


class RateLimitState(BaseModel):
    """Tracks rate-limit status for a connector."""

    requests_made: int = Field(0)
    requests_remaining: int = Field(60)
    window_reset_at: Optional[str] = Field(None, description="ISO timestamp when the rate limit window resets")
    is_throttled: bool = Field(False)


# ============================================================================
# Abstract Base Connector
# ============================================================================


class SocialConnector(ABC):
    """Abstract base class for social platform connectors.

    Each concrete subclass implements platform-specific API logic while this
    base provides rate-limit bookkeeping, post validation, and sandbox helpers.
    """

    def __init__(self, config: SocialConnectorConfig) -> None:
        self.config = config
        self._rate_limit = RateLimitState(
            requests_remaining=config.rate_limit_rpm,
        )
        self._connected: bool = False

    # ------------------------------------------------------------------
    # Abstract properties
    # ------------------------------------------------------------------

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Return the canonical platform identifier string."""
        ...

    @property
    @abstractmethod
    def media_requirements(self) -> MediaRequirements:
        """Return platform-specific media constraints."""
        ...

    # ------------------------------------------------------------------
    # Abstract methods
    # ------------------------------------------------------------------

    @abstractmethod
    def connect(self) -> bool:
        """Test the connection / validate credentials.  Return True if connected."""
        ...

    @abstractmethod
    def refresh_auth(self) -> bool:
        """Refresh OAuth token if expired.  Return True if refreshed."""
        ...

    @abstractmethod
    def get_profile(self) -> Dict[str, Any]:
        """Return the connected page/account profile info."""
        ...

    @abstractmethod
    def get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]:
        """Fetch recent posts with pagination."""
        ...

    @abstractmethod
    def create_post(self, post: SocialPost) -> SocialPost:
        """Publish or schedule a post.  Return updated post with id and status."""
        ...

    @abstractmethod
    def update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost:
        """Update an existing post (if platform allows)."""
        ...

    @abstractmethod
    def delete_post(self, post_id: str) -> bool:
        """Delete a post.  Return True if successful."""
        ...

    @abstractmethod
    def get_metrics(self, post_id: str) -> SocialMetrics:
        """Fetch engagement metrics for a specific post."""
        ...

    @abstractmethod
    def get_audience_insights(self) -> AudienceInsights:
        """Fetch audience demographics and behavior data."""
        ...

    @abstractmethod
    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload a media file and return a platform media reference/ID."""
        ...

    # ------------------------------------------------------------------
    # Concrete helper methods
    # ------------------------------------------------------------------

    def _check_rate_limit(self) -> bool:
        """Return True if a request can be made without exceeding rate limits.

        If the window has elapsed, reset the counters.  If throttled, return
        False.
        """
        now = datetime.now(timezone.utc)

        # If we have a reset timestamp and it has passed, reset the window
        if self._rate_limit.window_reset_at:
            try:
                reset_time = datetime.fromisoformat(self._rate_limit.window_reset_at)
                if now >= reset_time:
                    self._rate_limit.requests_made = 0
                    self._rate_limit.requests_remaining = self.config.rate_limit_rpm
                    self._rate_limit.is_throttled = False
                    self._rate_limit.window_reset_at = None
            except (ValueError, TypeError):
                pass

        if self._rate_limit.is_throttled:
            logger.warning(
                "[%s] Rate-limited — throttled until %s",
                self.platform_name,
                self._rate_limit.window_reset_at,
            )
            return False

        if self._rate_limit.requests_remaining <= 0:
            self._rate_limit.is_throttled = True
            logger.warning("[%s] Rate limit exhausted", self.platform_name)
            return False

        return True

    def _record_request(self) -> None:
        """Increment requests_made and update remaining count.

        If this is the first request in a new window, set the window_reset_at
        to 60 seconds from now.
        """
        now = datetime.now(timezone.utc)

        if self._rate_limit.window_reset_at is None:
            from datetime import timedelta

            self._rate_limit.window_reset_at = (now + timedelta(seconds=60)).isoformat()

        self._rate_limit.requests_made += 1
        self._rate_limit.requests_remaining = max(
            0,
            self.config.rate_limit_rpm - self._rate_limit.requests_made,
        )

    def _validate_post(self, post: SocialPost) -> List[str]:
        """Validate *post* against this connector's media requirements.

        Returns a list of validation error strings.  An empty list means the
        post is valid.
        """
        errors: List[str] = []
        reqs = self.media_requirements

        # Caption length
        if len(post.content_text) > reqs.max_caption_length:
            errors.append(
                f"Caption length {len(post.content_text)} exceeds max {reqs.max_caption_length}"
            )

        # Hashtag count
        if len(post.hashtags) > reqs.max_hashtags:
            errors.append(
                f"Hashtag count {len(post.hashtags)} exceeds max {reqs.max_hashtags}"
            )

        # Media format validation
        if post.media_urls:
            for url in post.media_urls:
                ext = url.rsplit(".", 1)[-1].lower() if "." in url else ""
                if ext:
                    all_formats = reqs.supported_image_formats + reqs.supported_video_formats
                    if ext not in all_formats:
                        errors.append(f"Unsupported media format: .{ext}")

        # Media type validation
        valid_media_types = {"image", "video", "carousel", "reel", "story", "short", None}
        if post.media_type not in valid_media_types:
            errors.append(f"Invalid media_type: {post.media_type}")

        return errors

    def _is_sandbox(self) -> bool:
        """Return True when sandbox mode is active (no real API calls)."""
        return self.config.sandbox_mode

    def _sandbox_response(self, method_name: str, **kwargs: Any) -> Dict[str, Any]:
        """Return a mock response dict for sandbox mode."""
        return {"sandbox": True, "method": method_name, **kwargs}

    # ------------------------------------------------------------------
    # Internal API call placeholder
    # ------------------------------------------------------------------

    def _api_call(
        self,
        method: str,
        url: str,
        *,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
        data: Optional[Any] = None,
        timeout: int = 30,
    ) -> Dict[str, Any]:
        """Placeholder for live HTTP calls.

        In production this would delegate to an HTTP client (requests, httpx,
        etc.).  For now it raises ``NotImplementedError`` to ensure sandbox
        mode is used during development.
        """
        raise NotImplementedError(
            "Live API calls not yet implemented — use sandbox mode"
        )

    # ------------------------------------------------------------------
    # Connection guard
    # ------------------------------------------------------------------

    def _require_connection(self) -> None:
        """Raise ``ConnectionError`` if the connector is not connected."""
        if not self._connected:
            raise ConnectionError(
                f"[{self.platform_name}] Not connected. Call connect() first."
            )
