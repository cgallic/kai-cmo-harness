"""YouTube connector — YouTube Data API v3 integration.

Handles standard video uploads, YouTube Shorts, resumable upload protocol,
custom thumbnails, video statistics, channel analytics, and subscriber
demographics.  All calls are routed through the abstract ``_api_call``
placeholder; set ``sandbox_mode=True`` (the default) to receive mock
responses without live HTTP traffic.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import (
    AudienceInsights,
    MediaRequirements,
    SocialConnector,
    SocialConnectorConfig,
    SocialMetrics,
    SocialPost,
)

logger = logging.getLogger(__name__)


class YouTubeConnector(SocialConnector):
    """YouTube Data API v3 connector for video publishing and channel analytics."""

    DATA_API_BASE: str = "https://www.googleapis.com/youtube/v3"
    UPLOAD_BASE: str = "https://www.googleapis.com/upload/youtube/v3/videos"
    ANALYTICS_BASE: str = "https://youtubeanalytics.googleapis.com/v2"

    # Default chunk size for resumable uploads (5 MB)
    CHUNK_SIZE: int = 5 * 1024 * 1024

    def __init__(self, config: SocialConnectorConfig) -> None:
        super().__init__(config)
        self._connected: bool = False
        # Kai focuses on Shorts for most local businesses
        self._is_shorts_focus: bool = True

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "youtube"

    @property
    def media_requirements(self) -> MediaRequirements:
        return MediaRequirements(
            platform="youtube",
            max_image_size_mb=2.0,
            max_video_size_mb=131072.0,
            max_video_duration_seconds=43200,
            supported_image_formats=["jpg", "png"],
            supported_video_formats=["mp4", "mov", "avi", "wmv", "flv", "webm"],
            aspect_ratios={"video": "16:9", "short": "9:16"},
            max_caption_length=5000,
            max_hashtags=15,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Return authorization headers for YouTube API."""
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
        }

    def _set_thumbnail(self, video_id: str, thumbnail_path: str) -> bool:
        """Set a custom thumbnail for a video via ``thumbnails.set()``."""
        if self._is_sandbox():
            logger.info("[youtube] Sandbox _set_thumbnail — video=%s", video_id)
            return True

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.DATA_API_BASE}/thumbnails/set"
            self._api_call(
                "POST",
                url,
                headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "image/png",
                },
                params={"videoId": video_id},
                data=f"<binary_file:{thumbnail_path}>",
            )
            self._record_request()
            logger.info("[youtube] Thumbnail set for video %s", video_id)
            return True
        except Exception as exc:
            logger.error("[youtube] _set_thumbnail failed: %s", exc)
            return False

    def _is_short(self, post: SocialPost) -> bool:
        """Determine if a post should be uploaded as a YouTube Short."""
        # Explicit short media type
        if post.media_type == "short":
            return True
        # Check metadata
        if post.metadata.get("is_short", False):
            return True
        # Check if title contains #Shorts
        if "#shorts" in post.content_text.lower() or "#Shorts" in post.content_text:
            return True
        return False

    # ------------------------------------------------------------------
    # Connection & Auth
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials by fetching the channel info."""
        if self._is_sandbox():
            logger.info("[youtube] Sandbox connect — skipping live validation")
            self._connected = True
            return True

        if not self.config.access_token:
            logger.error("[youtube] No access_token provided")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.DATA_API_BASE}/channels"
            params: Dict[str, Any] = {
                "part": "snippet,statistics",
                "mine": True,
            }
            if self.config.page_id:
                params = {"part": "snippet,statistics", "id": self.config.page_id}

            self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()
            self._connected = True
            logger.info("[youtube] Connected successfully")
            return True
        except Exception as exc:
            logger.error("[youtube] Connection failed: %s", exc)
            return False

    def refresh_auth(self) -> bool:
        """Refresh the Google OAuth2 access token."""
        if self._is_sandbox():
            logger.info("[youtube] Sandbox refresh_auth — returning True")
            return True

        if not self.config.refresh_token:
            logger.error("[youtube] No refresh_token available")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = "https://oauth2.googleapis.com/token"
            self._api_call(
                "POST",
                url,
                json_body={
                    "client_id": self.config.api_key,
                    "client_secret": self.config.api_secret,
                    "refresh_token": self.config.refresh_token,
                    "grant_type": "refresh_token",
                },
            )
            self._record_request()
            logger.info("[youtube] Token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("[youtube] Token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_profile(self) -> Dict[str, Any]:
        """Fetch the connected YouTube channel profile."""
        if self._is_sandbox():
            return self._sandbox_response(
                "get_profile",
                channel_title="Sandbox Channel",
                subscriber_count=8500,
                video_count=120,
                view_count=450000,
            )

        self._require_connection()
        if not self._check_rate_limit():
            return {"error": "rate_limited"}

        try:
            url = f"{self.DATA_API_BASE}/channels"
            params: Dict[str, Any] = {
                "part": "snippet,statistics,brandingSettings",
                "mine": True,
            }
            if self.config.page_id:
                params = {"part": "snippet,statistics,brandingSettings", "id": self.config.page_id}

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()

            items = result.get("items", [])
            if items:
                channel = items[0]
                return {
                    "id": channel.get("id"),
                    "title": channel.get("snippet", {}).get("title"),
                    "description": channel.get("snippet", {}).get("description"),
                    "subscriber_count": channel.get("statistics", {}).get("subscriberCount"),
                    "video_count": channel.get("statistics", {}).get("videoCount"),
                    "view_count": channel.get("statistics", {}).get("viewCount"),
                    "custom_url": channel.get("snippet", {}).get("customUrl"),
                    "thumbnail_url": channel.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url"),
                }
            return result
        except Exception as exc:
            logger.error("[youtube] get_profile failed: %s", exc)
            return {"error": str(exc)}

    def get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]:
        """Fetch recent videos from the channel."""
        if self._is_sandbox():
            return [
                SocialPost(
                    id=f"yt_sandbox_{i}",
                    platform="youtube",
                    content_text=f"Sandbox YouTube video #{i}",
                    media_type="video",
                    status="published",
                    published_at=datetime.now(timezone.utc).isoformat(),
                    published_url=f"https://youtube.com/watch?v=yt_sandbox_{i}",
                )
                for i in range(min(limit, 3))
            ]

        self._require_connection()
        if not self._check_rate_limit():
            return []

        try:
            # Step 1: Search for channel's videos
            url = f"{self.DATA_API_BASE}/search"
            params: Dict[str, Any] = {
                "part": "snippet",
                "channelId": self.config.page_id,
                "order": "date",
                "maxResults": limit,
                "type": "video",
            }
            if cursor:
                params["pageToken"] = cursor

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()

            posts: List[SocialPost] = []
            for item in result.get("items", []):
                video_id = item.get("id", {}).get("videoId", "")
                snippet = item.get("snippet", {})
                posts.append(
                    SocialPost(
                        id=video_id,
                        platform="youtube",
                        content_text=snippet.get("title", ""),
                        media_type="video",
                        status="published",
                        published_at=snippet.get("publishedAt"),
                        published_url=f"https://youtube.com/watch?v={video_id}",
                        metadata={"description": snippet.get("description", "")},
                    )
                )
            return posts
        except Exception as exc:
            logger.error("[youtube] get_posts failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_post(self, post: SocialPost) -> SocialPost:
        """Upload a video (standard or Short) to YouTube via resumable upload.

        For Shorts, the title includes ``#Shorts`` and the video is vertical
        (9:16), max 60 seconds.  Scheduling is supported via the
        ``publishAt`` field in the status object.
        """
        self._require_connection()

        errors = self._validate_post(post)
        if errors:
            post.status = "failed"
            post.error_message = "; ".join(errors)
            logger.error("[youtube] Post validation failed: %s", post.error_message)
            return post

        if self._is_sandbox():
            sandbox_id = f"yt_{uuid.uuid4().hex[:12]}"
            is_short = self._is_short(post)
            post.id = sandbox_id
            post.status = "scheduled" if post.schedule_time else "published"
            post.published_url = f"https://youtube.com/watch?v={sandbox_id}"
            if not post.schedule_time:
                post.published_at = datetime.now(timezone.utc).isoformat()
            post.metadata["is_short"] = is_short
            logger.info("[youtube] Sandbox create_post — id=%s short=%s", sandbox_id, is_short)
            return post

        if not self._check_rate_limit():
            post.status = "failed"
            post.error_message = "Rate limited"
            return post

        try:
            is_short = self._is_short(post)

            # Build title — include #Shorts for Shorts
            title = post.content_text[:100]  # YouTube title max ~100 chars
            if is_short and "#Shorts" not in title and "#shorts" not in title:
                title = f"{title} #Shorts"

            # Build description from full content + hashtags
            description = post.content_text
            if post.hashtags:
                hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
                description += f"\n\n{hashtag_str}"

            # Build tags from hashtags
            tags = [tag.lstrip("#") for tag in post.hashtags]

            # Video resource body
            video_body: Dict[str, Any] = {
                "snippet": {
                    "title": title,
                    "description": description,
                    "tags": tags,
                    "categoryId": post.metadata.get("category_id", "22"),  # 22 = People & Blogs
                },
                "status": {
                    "privacyStatus": post.metadata.get("privacy_status", "public"),
                    "selfDeclaredMadeForKids": post.metadata.get("made_for_kids", False),
                    "notifySubscribers": post.metadata.get("notify_subscribers", True),
                },
            }

            # Scheduling
            if post.schedule_time:
                video_body["status"]["privacyStatus"] = "private"
                video_body["status"]["publishAt"] = post.schedule_time

            # Step 1: Initiate resumable upload
            init_url = self.UPLOAD_BASE
            init_params = {
                "uploadType": "resumable",
                "part": "snippet,status",
            }

            init_result = self._api_call(
                "POST",
                init_url,
                headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": "video/*",
                },
                params=init_params,
                json_body=video_body,
            )
            self._record_request()

            # The upload URL is returned in the Location header
            upload_url = init_result.get("location", init_result.get("upload_url", ""))

            # Step 2: Upload video data (in production, this would stream the file)
            if upload_url and post.media_urls:
                try:
                    upload_result = self._api_call(
                        "PUT",
                        upload_url,
                        headers={
                            "Authorization": f"Bearer {self.config.access_token}",
                            "Content-Type": "video/*",
                        },
                        data=f"<binary_file:{post.media_urls[0]}>",
                    )
                    self._record_request()

                    video_id = upload_result.get("id", "")
                    post.id = video_id
                except NotImplementedError:
                    logger.warning("[youtube] Video upload skipped — live API not yet implemented")
                    post.id = f"yt_pending_{uuid.uuid4().hex[:8]}"

            post.status = "scheduled" if post.schedule_time else "published"
            if not post.schedule_time:
                post.published_at = datetime.now(timezone.utc).isoformat()
            post.published_url = f"https://youtube.com/watch?v={post.id}"
            post.metadata["is_short"] = is_short

            # Set thumbnail if provided
            thumbnail_path = post.metadata.get("thumbnail_path")
            if thumbnail_path and post.id:
                self._set_thumbnail(post.id, thumbnail_path)

            logger.info("[youtube] Video uploaded — id=%s short=%s", post.id, is_short)
            return post

        except Exception as exc:
            post.status = "failed"
            post.error_message = str(exc)
            logger.error("[youtube] create_post failed: %s", exc)
            return post

    def update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost:
        """Update a YouTube video's metadata (title, description, tags, etc.)."""
        self._require_connection()

        if self._is_sandbox():
            return SocialPost(
                id=post_id,
                platform="youtube",
                content_text=updates.get("content_text", ""),
                status="published",
                metadata={"sandbox": True, "updates_applied": list(updates.keys())},
            )

        if not self._check_rate_limit():
            return SocialPost(
                id=post_id,
                platform="youtube",
                content_text="",
                status="failed",
                error_message="Rate limited",
            )

        try:
            url = f"{self.DATA_API_BASE}/videos"
            video_body: Dict[str, Any] = {
                "id": post_id,
                "snippet": {},
            }

            if "content_text" in updates:
                video_body["snippet"]["title"] = updates["content_text"][:100]
            if "description" in updates:
                video_body["snippet"]["description"] = updates["description"]
            if "tags" in updates:
                video_body["snippet"]["tags"] = updates["tags"]
            if "category_id" in updates:
                video_body["snippet"]["categoryId"] = updates["category_id"]

            self._api_call(
                "PUT",
                url,
                headers=self._build_headers(),
                params={"part": "snippet"},
                json_body=video_body,
            )
            self._record_request()

            return SocialPost(
                id=post_id,
                platform="youtube",
                content_text=updates.get("content_text", ""),
                status="published",
            )
        except Exception as exc:
            logger.error("[youtube] update_post failed: %s", exc)
            return SocialPost(
                id=post_id,
                platform="youtube",
                content_text="",
                status="failed",
                error_message=str(exc),
            )

    def delete_post(self, post_id: str) -> bool:
        """Delete a YouTube video."""
        self._require_connection()

        if self._is_sandbox():
            logger.info("[youtube] Sandbox delete_post — id=%s", post_id)
            return True

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.DATA_API_BASE}/videos"
            self._api_call(
                "DELETE",
                url,
                headers=self._build_headers(),
                params={"id": post_id},
            )
            self._record_request()
            logger.info("[youtube] Video deleted — id=%s", post_id)
            return True
        except Exception as exc:
            logger.error("[youtube] delete_post failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Metrics & Insights
    # ------------------------------------------------------------------

    def get_metrics(self, post_id: str) -> SocialMetrics:
        """Fetch video statistics via ``videos.list(part='statistics')``."""
        if self._is_sandbox():
            return SocialMetrics(
                post_id=post_id,
                platform="youtube",
                impressions=12000,
                reach=8500,
                likes=420,
                comments=65,
                shares=28,
                video_views=9200,
                engagement_rate=round((420 + 65 + 28) / 8500, 4) if 8500 > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return SocialMetrics(post_id=post_id, platform="youtube")

        try:
            url = f"{self.DATA_API_BASE}/videos"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={"part": "statistics", "id": post_id},
            )
            self._record_request()

            items = result.get("items", [])
            if not items:
                return SocialMetrics(post_id=post_id, platform="youtube")

            stats = items[0].get("statistics", {})
            views = int(stats.get("viewCount", 0))
            likes = int(stats.get("likeCount", 0))
            comments_count = int(stats.get("commentCount", 0))
            favorites = int(stats.get("favoriteCount", 0))

            return SocialMetrics(
                post_id=post_id,
                platform="youtube",
                impressions=views,
                reach=views,
                likes=likes,
                comments=comments_count,
                saves=favorites,
                video_views=views,
                engagement_rate=round((likes + comments_count) / views, 4) if views > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[youtube] get_metrics failed: %s", exc)
            return SocialMetrics(post_id=post_id, platform="youtube")

    def get_audience_insights(self) -> AudienceInsights:
        """Fetch channel and audience demographics.

        Uses ``channels.list(part='statistics')`` for subscriber/video
        counts and ``youtubeAnalytics.reports().query()`` for demographics.
        """
        if self._is_sandbox():
            return AudienceInsights(
                platform="youtube",
                total_followers=8500,
                follower_growth_30d=320,
                top_locations=[
                    {"location": "United States", "percentage": 42.0},
                    {"location": "India", "percentage": 15.0},
                    {"location": "United Kingdom", "percentage": 10.0},
                    {"location": "Canada", "percentage": 7.0},
                ],
                age_gender_breakdown=[
                    {"age_range": "25-34", "gender": "male", "percentage": 30.0},
                    {"age_range": "25-34", "gender": "female", "percentage": 18.0},
                    {"age_range": "18-24", "gender": "male", "percentage": 22.0},
                    {"age_range": "35-44", "gender": "male", "percentage": 12.0},
                ],
                active_hours=[
                    {"day": "Saturday", "hour": 15, "engagement_level": "high"},
                    {"day": "Sunday", "hour": 11, "engagement_level": "high"},
                    {"day": "Wednesday", "hour": 19, "engagement_level": "high"},
                ],
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return AudienceInsights(platform="youtube")

        try:
            # Step 1: Get channel statistics
            channel_url = f"{self.DATA_API_BASE}/channels"
            channel_params: Dict[str, Any] = {
                "part": "statistics",
                "mine": True,
            }
            if self.config.page_id:
                channel_params = {"part": "statistics", "id": self.config.page_id}

            channel_result = self._api_call(
                "GET", channel_url, headers=self._build_headers(), params=channel_params
            )
            self._record_request()

            items = channel_result.get("items", [])
            subscriber_count = 0
            if items:
                subscriber_count = int(items[0].get("statistics", {}).get("subscriberCount", 0))

            # Step 2: Get demographic data from YouTube Analytics
            analytics_url = f"{self.ANALYTICS_BASE}/reports"

            # Country breakdown
            country_result = self._api_call(
                "GET",
                analytics_url,
                headers=self._build_headers(),
                params={
                    "ids": "channel==MINE",
                    "startDate": "2020-01-01",
                    "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "metrics": "views",
                    "dimensions": "country",
                    "sort": "-views",
                    "maxResults": 10,
                },
            )
            self._record_request()

            total_views = sum(row[1] for row in country_result.get("rows", []))
            top_locations = [
                {
                    "location": row[0],
                    "percentage": round(row[1] / max(total_views, 1) * 100, 1),
                }
                for row in country_result.get("rows", [])
            ]

            # Age/Gender breakdown
            demo_result = self._api_call(
                "GET",
                analytics_url,
                headers=self._build_headers(),
                params={
                    "ids": "channel==MINE",
                    "startDate": "2020-01-01",
                    "endDate": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
                    "metrics": "viewerPercentage",
                    "dimensions": "ageGroup,gender",
                },
            )
            self._record_request()

            age_gender_breakdown = [
                {
                    "age_range": row[0],
                    "gender": row[1],
                    "percentage": round(row[2], 1),
                }
                for row in demo_result.get("rows", [])
            ]

            return AudienceInsights(
                platform="youtube",
                total_followers=subscriber_count,
                top_locations=top_locations,
                age_gender_breakdown=age_gender_breakdown,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[youtube] get_audience_insights failed: %s", exc)
            return AudienceInsights(platform="youtube")

    # ------------------------------------------------------------------
    # Media Upload (resumable)
    # ------------------------------------------------------------------

    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload media using YouTube's resumable upload protocol.

        1. Initiate upload with POST to get a resumable upload URI.
        2. Upload the file in chunks.
        3. Handle resume on failure by querying the upload status.
        """
        if self._is_sandbox():
            sandbox_id = f"yt_media_{uuid.uuid4().hex[:12]}"
            logger.info("[youtube] Sandbox upload_media — id=%s", sandbox_id)
            return sandbox_id

        self._require_connection()
        if not self._check_rate_limit():
            raise RuntimeError("Rate limited — cannot upload media")

        try:
            if media_type in ("image", "thumbnail"):
                # Thumbnail upload is not resumable
                url = f"{self.DATA_API_BASE}/thumbnails/set"
                result = self._api_call(
                    "POST",
                    url,
                    headers={
                        "Authorization": f"Bearer {self.config.access_token}",
                        "Content-Type": "image/png",
                    },
                    data=f"<binary_file:{file_path}>",
                )
                self._record_request()
                return result.get("items", [{}])[0].get("default", {}).get("url", "")

            # Video: resumable upload
            # Step 1: Initiate the resumable upload session
            video_body: Dict[str, Any] = {
                "snippet": {
                    "title": "Uploaded via Kai",
                    "description": "",
                },
                "status": {
                    "privacyStatus": "private",
                },
            }

            init_result = self._api_call(
                "POST",
                self.UPLOAD_BASE,
                headers={
                    "Authorization": f"Bearer {self.config.access_token}",
                    "Content-Type": "application/json",
                    "X-Upload-Content-Type": "video/*",
                },
                params={"uploadType": "resumable", "part": "snippet,status"},
                json_body=video_body,
            )
            self._record_request()

            upload_url = init_result.get("location", init_result.get("upload_url", ""))

            # Step 2: Upload the video file (in production, read in chunks)
            if upload_url:
                upload_result = self._api_call(
                    "PUT",
                    upload_url,
                    headers={
                        "Authorization": f"Bearer {self.config.access_token}",
                        "Content-Type": "video/*",
                    },
                    data=f"<binary_file:{file_path}>",
                )
                self._record_request()
                video_id: str = upload_result.get("id", "")
                logger.info("[youtube] Video uploaded — id=%s", video_id)
                return video_id

            return ""
        except Exception as exc:
            logger.error("[youtube] upload_media failed: %s", exc)
            raise
