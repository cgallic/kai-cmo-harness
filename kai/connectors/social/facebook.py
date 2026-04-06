"""Facebook connector — Graph API v19.0 integration for page publishing and analytics.

Handles text posts, photo uploads, video uploads, link sharing, scheduled
publishing, post insights, and page audience demographics through the
Facebook Graph API.  All calls are routed through the abstract
``_api_call`` placeholder; set ``sandbox_mode=True`` (the default) to
receive mock responses without live HTTP traffic.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import (
    AudienceInsights,
    MediaRequirements,
    RateLimitState,
    SocialConnector,
    SocialConnectorConfig,
    SocialMetrics,
    SocialPost,
)

logger = logging.getLogger(__name__)


class FacebookConnector(SocialConnector):
    """Facebook Graph API connector for page-level publishing and insights."""

    API_VERSION: str = "v19.0"
    BASE_URL: str = f"https://graph.facebook.com/{API_VERSION}"

    def __init__(self, config: SocialConnectorConfig) -> None:
        super().__init__(config)
        self._connected: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "facebook"

    @property
    def media_requirements(self) -> MediaRequirements:
        return MediaRequirements(
            platform="facebook",
            max_image_size_mb=10.0,
            max_video_size_mb=4096.0,
            max_video_duration_seconds=14400,
            supported_image_formats=["jpg", "png", "bmp", "gif", "tiff"],
            supported_video_formats=["mp4", "mov", "avi"],
            aspect_ratios={"feed": "flexible", "story": "9:16", "reel": "9:16"},
            max_caption_length=63206,
            max_hashtags=30,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Return authorization headers for Graph API requests."""
        return {"Authorization": f"Bearer {self.config.access_token}"}

    # ------------------------------------------------------------------
    # Connection & Auth
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials by fetching page info via ``/{page_id}``."""
        if self._is_sandbox():
            logger.info("[facebook] Sandbox connect — skipping live validation")
            self._connected = True
            return True

        if not self.config.access_token:
            logger.error("[facebook] No access_token provided")
            return False
        if not self.config.page_id:
            logger.error("[facebook] No page_id provided")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/{self.config.page_id}"
            self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={"fields": "name,id,fan_count"},
            )
            self._record_request()
            self._connected = True
            logger.info("[facebook] Connected successfully to page %s", self.config.page_id)
            return True
        except Exception as exc:
            logger.error("[facebook] Connection failed: %s", exc)
            return False

    def refresh_auth(self) -> bool:
        """Exchange a long-lived token or refresh token for a new access token."""
        if self._is_sandbox():
            logger.info("[facebook] Sandbox refresh_auth — returning True")
            return True

        if not self.config.refresh_token and not self.config.access_token:
            logger.error("[facebook] No token available to refresh")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/oauth/access_token"
            self._api_call(
                "GET",
                url,
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": self.config.api_key,
                    "client_secret": self.config.api_secret,
                    "fb_exchange_token": self.config.access_token,
                },
            )
            self._record_request()
            logger.info("[facebook] Token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("[facebook] Token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_profile(self) -> Dict[str, Any]:
        """Fetch the connected page's profile information."""
        if self._is_sandbox():
            return self._sandbox_response(
                "get_profile",
                page_id=self.config.page_id,
                name="Sandbox Page",
                fan_count=10000,
                category="Local Business",
            )

        self._require_connection()
        if not self._check_rate_limit():
            return {"error": "rate_limited"}

        try:
            url = f"{self.BASE_URL}/{self.config.page_id}"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={"fields": "name,id,fan_count,category,about,website,picture"},
            )
            self._record_request()
            return result
        except Exception as exc:
            logger.error("[facebook] get_profile failed: %s", exc)
            return {"error": str(exc)}

    def get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]:
        """Fetch recent posts from the page feed."""
        if self._is_sandbox():
            sandbox = self._sandbox_response("get_posts", limit=limit, cursor=cursor)
            return [
                SocialPost(
                    id=f"fb_sandbox_{i}",
                    platform="facebook",
                    content_text=f"Sandbox post #{i}",
                    status="published",
                    published_at=datetime.now(timezone.utc).isoformat(),
                )
                for i in range(min(limit, 3))
            ]

        self._require_connection()
        if not self._check_rate_limit():
            return []

        try:
            url = f"{self.BASE_URL}/{self.config.page_id}/feed"
            params: Dict[str, Any] = {
                "fields": "id,message,created_time,permalink_url,type,status_type,shares,attachments",
                "limit": limit,
            }
            if cursor:
                params["after"] = cursor

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()

            posts: List[SocialPost] = []
            for item in result.get("data", []):
                posts.append(
                    SocialPost(
                        id=item.get("id"),
                        platform="facebook",
                        content_text=item.get("message", ""),
                        status="published",
                        published_at=item.get("created_time"),
                        published_url=item.get("permalink_url"),
                    )
                )
            return posts
        except Exception as exc:
            logger.error("[facebook] get_posts failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_post(self, post: SocialPost) -> SocialPost:
        """Publish or schedule a post on the Facebook page.

        Supports text-only, single image, video, and link posts.  If
        ``post.schedule_time`` is set the post is created as unpublished
        with a ``scheduled_publish_time``.
        """
        self._require_connection()

        # Validate post against media requirements
        errors = self._validate_post(post)
        if errors:
            post.status = "failed"
            post.error_message = "; ".join(errors)
            logger.error("[facebook] Post validation failed: %s", post.error_message)
            return post

        if self._is_sandbox():
            sandbox_id = f"fb_{uuid.uuid4().hex[:12]}"
            post.id = sandbox_id
            post.status = "scheduled" if post.schedule_time else "published"
            post.published_url = f"https://facebook.com/{self.config.page_id}/posts/{sandbox_id}"
            if not post.schedule_time:
                post.published_at = datetime.now(timezone.utc).isoformat()
            logger.info("[facebook] Sandbox create_post — id=%s", sandbox_id)
            return post

        if not self._check_rate_limit():
            post.status = "failed"
            post.error_message = "Rate limited"
            return post

        try:
            # Determine the correct endpoint and payload based on content type
            if post.media_type == "video" or (post.media_urls and self._is_video_url(post.media_urls[0])):
                # Video post
                url = f"{self.BASE_URL}/{self.config.page_id}/videos"
                payload: Dict[str, Any] = {
                    "description": post.content_text,
                }
                if post.media_urls:
                    payload["file_url"] = post.media_urls[0]

            elif post.media_type == "image" or (post.media_urls and not self._is_video_url(post.media_urls[0])):
                # Photo post
                url = f"{self.BASE_URL}/{self.config.page_id}/photos"
                payload = {
                    "message": post.content_text,
                }
                if post.media_urls:
                    payload["url"] = post.media_urls[0]

            elif post.link_url:
                # Link post
                url = f"{self.BASE_URL}/{self.config.page_id}/feed"
                payload = {
                    "message": post.content_text,
                    "link": post.link_url,
                }

            else:
                # Text-only post
                url = f"{self.BASE_URL}/{self.config.page_id}/feed"
                payload = {
                    "message": post.content_text,
                }

            # Add hashtags to message body
            if post.hashtags:
                hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
                if "message" in payload:
                    payload["message"] += f"\n\n{hashtag_str}"
                elif "description" in payload:
                    payload["description"] += f"\n\n{hashtag_str}"

            # Scheduling: create as unpublished with scheduled_publish_time
            if post.schedule_time:
                payload["published"] = False
                payload["scheduled_publish_time"] = post.schedule_time

            result = self._api_call("POST", url, headers=self._build_headers(), json_body=payload)
            self._record_request()

            post.id = result.get("id", result.get("post_id"))
            post.status = "scheduled" if post.schedule_time else "published"
            if not post.schedule_time:
                post.published_at = datetime.now(timezone.utc).isoformat()
                post.published_url = f"https://facebook.com/{self.config.page_id}/posts/{post.id}"
            logger.info("[facebook] Post created — id=%s status=%s", post.id, post.status)
            return post

        except Exception as exc:
            post.status = "failed"
            post.error_message = str(exc)
            logger.error("[facebook] create_post failed: %s", exc)
            return post

    def update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost:
        """Update an existing post's message text."""
        self._require_connection()

        if self._is_sandbox():
            return SocialPost(
                id=post_id,
                platform="facebook",
                content_text=updates.get("content_text", ""),
                status="published",
                metadata={"sandbox": True, "updates_applied": list(updates.keys())},
            )

        if not self._check_rate_limit():
            return SocialPost(
                id=post_id,
                platform="facebook",
                content_text="",
                status="failed",
                error_message="Rate limited",
            )

        try:
            url = f"{self.BASE_URL}/{post_id}"
            payload: Dict[str, Any] = {}
            if "content_text" in updates:
                payload["message"] = updates["content_text"]

            self._api_call("POST", url, headers=self._build_headers(), json_body=payload)
            self._record_request()

            return SocialPost(
                id=post_id,
                platform="facebook",
                content_text=updates.get("content_text", ""),
                status="published",
            )
        except Exception as exc:
            logger.error("[facebook] update_post failed: %s", exc)
            return SocialPost(
                id=post_id,
                platform="facebook",
                content_text="",
                status="failed",
                error_message=str(exc),
            )

    def delete_post(self, post_id: str) -> bool:
        """Delete a post by its ID."""
        self._require_connection()

        if self._is_sandbox():
            logger.info("[facebook] Sandbox delete_post — id=%s", post_id)
            return True

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/{post_id}"
            self._api_call("DELETE", url, headers=self._build_headers())
            self._record_request()
            logger.info("[facebook] Post deleted — id=%s", post_id)
            return True
        except Exception as exc:
            logger.error("[facebook] delete_post failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Metrics & Insights
    # ------------------------------------------------------------------

    def get_metrics(self, post_id: str) -> SocialMetrics:
        """Fetch engagement metrics for a specific post via ``/{post_id}/insights``."""
        if self._is_sandbox():
            return SocialMetrics(
                post_id=post_id,
                platform="facebook",
                impressions=1200,
                reach=800,
                likes=95,
                comments=12,
                shares=8,
                saves=3,
                clicks=45,
                engagement_rate=round((95 + 12 + 8 + 3) / 800, 4) if 800 > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return SocialMetrics(post_id=post_id, platform="facebook")

        try:
            url = f"{self.BASE_URL}/{post_id}/insights"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={
                    "metric": "post_impressions,post_impressions_unique,post_engaged_users,post_clicks",
                },
            )
            self._record_request()

            # Parse insights response — each metric is a dict with name/values
            data_map: Dict[str, int] = {}
            for entry in result.get("data", []):
                name = entry.get("name", "")
                values = entry.get("values", [{}])
                data_map[name] = values[0].get("value", 0) if values else 0

            impressions = data_map.get("post_impressions", 0)
            reach = data_map.get("post_impressions_unique", 0)
            engaged = data_map.get("post_engaged_users", 0)
            clicks = data_map.get("post_clicks", 0)

            return SocialMetrics(
                post_id=post_id,
                platform="facebook",
                impressions=impressions,
                reach=reach,
                likes=engaged,
                clicks=clicks,
                engagement_rate=round(engaged / reach, 4) if reach > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[facebook] get_metrics failed: %s", exc)
            return SocialMetrics(post_id=post_id, platform="facebook")

    def get_audience_insights(self) -> AudienceInsights:
        """Fetch page audience demographics via ``/{page_id}/insights``."""
        if self._is_sandbox():
            return AudienceInsights(
                platform="facebook",
                total_followers=10000,
                follower_growth_30d=250,
                top_locations=[
                    {"location": "New York, NY", "percentage": 18.5},
                    {"location": "Los Angeles, CA", "percentage": 12.3},
                    {"location": "Chicago, IL", "percentage": 8.7},
                ],
                age_gender_breakdown=[
                    {"age_range": "25-34", "gender": "male", "percentage": 28.0},
                    {"age_range": "25-34", "gender": "female", "percentage": 24.0},
                    {"age_range": "35-44", "gender": "male", "percentage": 16.0},
                ],
                active_hours=[
                    {"day": "Wednesday", "hour": 14, "engagement_level": "high"},
                    {"day": "Thursday", "hour": 19, "engagement_level": "high"},
                ],
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return AudienceInsights(platform="facebook")

        try:
            url = f"{self.BASE_URL}/{self.config.page_id}/insights"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={
                    "metric": "page_fans_city,page_fans_gender_age,page_fans_online",
                    "period": "day",
                },
            )
            self._record_request()

            data_map: Dict[str, Any] = {}
            for entry in result.get("data", []):
                data_map[entry.get("name", "")] = entry.get("values", [{}])

            # Parse city data
            city_data = data_map.get("page_fans_city", [{}])
            city_values = city_data[0].get("value", {}) if city_data else {}
            total_city = sum(city_values.values()) if city_values else 1
            top_locations = [
                {"location": city, "percentage": round(count / total_city * 100, 1)}
                for city, count in sorted(city_values.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # Parse gender/age data
            gender_age_data = data_map.get("page_fans_gender_age", [{}])
            gender_age_values = gender_age_data[0].get("value", {}) if gender_age_data else {}
            total_fans = sum(gender_age_values.values()) if gender_age_values else 1
            age_gender_breakdown = [
                {
                    "age_range": key.split(".")[-1] if "." in key else key,
                    "gender": key.split(".")[0] if "." in key else "unknown",
                    "percentage": round(count / total_fans * 100, 1),
                }
                for key, count in gender_age_values.items()
            ]

            return AudienceInsights(
                platform="facebook",
                total_followers=total_fans,
                top_locations=top_locations,
                age_gender_breakdown=age_gender_breakdown,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[facebook] get_audience_insights failed: %s", exc)
            return AudienceInsights(platform="facebook")

    # ------------------------------------------------------------------
    # Media Upload
    # ------------------------------------------------------------------

    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload a media file and return the platform media reference ID."""
        if self._is_sandbox():
            sandbox_id = f"fb_media_{uuid.uuid4().hex[:12]}"
            logger.info("[facebook] Sandbox upload_media — id=%s", sandbox_id)
            return sandbox_id

        self._require_connection()
        if not self._check_rate_limit():
            raise RuntimeError("Rate limited — cannot upload media")

        try:
            if media_type == "video":
                url = f"{self.BASE_URL}/{self.config.page_id}/videos"
            else:
                url = f"{self.BASE_URL}/{self.config.page_id}/photos"

            result = self._api_call(
                "POST",
                url,
                headers=self._build_headers(),
                data={"source": file_path, "published": False},
            )
            self._record_request()
            return result.get("id", "")
        except Exception as exc:
            logger.error("[facebook] upload_media failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _is_video_url(url: str) -> bool:
        """Return True if the URL appears to reference a video file."""
        video_extensions = {"mp4", "mov", "avi", "wmv", "flv", "webm"}
        ext = url.rsplit(".", 1)[-1].lower() if "." in url else ""
        return ext in video_extensions
