"""Instagram connector — Instagram Graph API integration via Facebook Graph API.

Handles feed posts (single image, carousel, reels), hashtag research,
two-step container+publish flow, post insights, and audience demographics.
All calls are routed through the abstract ``_api_call`` placeholder; set
``sandbox_mode=True`` (the default) to receive mock responses.
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


class InstagramConnector(SocialConnector):
    """Instagram Graph API connector (routed through Facebook Graph API)."""

    API_VERSION: str = "v19.0"
    BASE_URL: str = f"https://graph.facebook.com/{API_VERSION}"

    def __init__(self, config: SocialConnectorConfig) -> None:
        super().__init__(config)
        self._connected: bool = False
        # The Instagram Business Account ID (obtained through the FB page)
        self._ig_user_id: Optional[str] = config.page_id

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "instagram"

    @property
    def media_requirements(self) -> MediaRequirements:
        return MediaRequirements(
            platform="instagram",
            max_image_size_mb=8.0,
            max_video_size_mb=4096.0,
            max_video_duration_seconds=5400,
            supported_image_formats=["jpg", "png"],
            supported_video_formats=["mp4", "mov"],
            aspect_ratios={
                "feed_square": "1:1",
                "feed_portrait": "4:5",
                "feed_landscape": "1.91:1",
                "story": "9:16",
                "reel": "9:16",
            },
            max_caption_length=2200,
            max_hashtags=30,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Return authorization headers for Graph API requests."""
        return {"Authorization": f"Bearer {self.config.access_token}"}

    def _get_hashtag_id(self, hashtag: str) -> Optional[str]:
        """Search for a hashtag ID via ``ig_hashtag_search``."""
        if self._is_sandbox():
            return f"hashtag_sandbox_{hashtag.lstrip('#')}"

        if not self._check_rate_limit():
            return None

        try:
            url = f"{self.BASE_URL}/ig_hashtag_search"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={"user_id": self._ig_user_id, "q": hashtag.lstrip("#")},
            )
            self._record_request()

            data = result.get("data", [])
            return data[0].get("id") if data else None
        except Exception as exc:
            logger.error("[instagram] _get_hashtag_id failed for '%s': %s", hashtag, exc)
            return None

    def _get_recent_hashtag_media(self, hashtag_id: str, limit: int = 25) -> List[Dict[str, Any]]:
        """Fetch recent media for a given hashtag ID."""
        if self._is_sandbox():
            return [
                {
                    "id": f"ig_ht_media_{i}",
                    "caption": f"Sandbox hashtag media #{i}",
                    "media_type": "IMAGE",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
                for i in range(min(limit, 5))
            ]

        if not self._check_rate_limit():
            return []

        try:
            url = f"{self.BASE_URL}/{hashtag_id}/recent_media"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={
                    "user_id": self._ig_user_id,
                    "fields": "id,caption,media_type,media_url,timestamp,like_count,comments_count",
                    "limit": limit,
                },
            )
            self._record_request()
            return result.get("data", [])
        except Exception as exc:
            logger.error("[instagram] _get_recent_hashtag_media failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Connection & Auth
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials by fetching the IG business account info."""
        if self._is_sandbox():
            logger.info("[instagram] Sandbox connect — skipping live validation")
            self._connected = True
            return True

        if not self.config.access_token:
            logger.error("[instagram] No access_token provided")
            return False
        if not self._ig_user_id:
            logger.error("[instagram] No page_id / IG user ID provided")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/{self._ig_user_id}"
            self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={"fields": "id,username,name,biography,followers_count,media_count"},
            )
            self._record_request()
            self._connected = True
            logger.info("[instagram] Connected successfully to IG account %s", self._ig_user_id)
            return True
        except Exception as exc:
            logger.error("[instagram] Connection failed: %s", exc)
            return False

    def refresh_auth(self) -> bool:
        """Refresh the long-lived Instagram token via Facebook token exchange."""
        if self._is_sandbox():
            logger.info("[instagram] Sandbox refresh_auth — returning True")
            return True

        if not self.config.access_token:
            logger.error("[instagram] No token available to refresh")
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
            logger.info("[instagram] Token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("[instagram] Token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_profile(self) -> Dict[str, Any]:
        """Fetch the connected IG business account profile."""
        if self._is_sandbox():
            return self._sandbox_response(
                "get_profile",
                ig_user_id=self._ig_user_id,
                username="sandbox_account",
                followers_count=5000,
                media_count=120,
            )

        self._require_connection()
        if not self._check_rate_limit():
            return {"error": "rate_limited"}

        try:
            url = f"{self.BASE_URL}/{self._ig_user_id}"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={"fields": "id,username,name,biography,followers_count,follows_count,media_count,profile_picture_url,website"},
            )
            self._record_request()
            return result
        except Exception as exc:
            logger.error("[instagram] get_profile failed: %s", exc)
            return {"error": str(exc)}

    def get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]:
        """Fetch recent media from the IG account."""
        if self._is_sandbox():
            return [
                SocialPost(
                    id=f"ig_sandbox_{i}",
                    platform="instagram",
                    content_text=f"Sandbox IG post #{i}",
                    status="published",
                    published_at=datetime.now(timezone.utc).isoformat(),
                )
                for i in range(min(limit, 3))
            ]

        self._require_connection()
        if not self._check_rate_limit():
            return []

        try:
            url = f"{self.BASE_URL}/{self._ig_user_id}/media"
            params: Dict[str, Any] = {
                "fields": "id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count",
                "limit": limit,
            }
            if cursor:
                params["after"] = cursor

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()

            posts: List[SocialPost] = []
            for item in result.get("data", []):
                media_type_map = {
                    "IMAGE": "image",
                    "VIDEO": "video",
                    "CAROUSEL_ALBUM": "carousel",
                }
                posts.append(
                    SocialPost(
                        id=item.get("id"),
                        platform="instagram",
                        content_text=item.get("caption", ""),
                        media_type=media_type_map.get(item.get("media_type"), None),
                        status="published",
                        published_at=item.get("timestamp"),
                        published_url=item.get("permalink"),
                    )
                )
            return posts
        except Exception as exc:
            logger.error("[instagram] get_posts failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Write operations (two-step container + publish flow)
    # ------------------------------------------------------------------

    def create_post(self, post: SocialPost) -> SocialPost:
        """Create an Instagram post using the two-step container-then-publish flow.

        Supports three flows:
        1. **Single image feed post**: create container with ``image_url``,
           then publish with ``creation_id``.
        2. **Carousel**: create individual item containers, then create a
           carousel container referencing the children, then publish.
        3. **Reel**: create container with ``video_url`` and
           ``media_type=REELS``, then publish.
        """
        self._require_connection()

        errors = self._validate_post(post)
        if errors:
            post.status = "failed"
            post.error_message = "; ".join(errors)
            logger.error("[instagram] Post validation failed: %s", post.error_message)
            return post

        if self._is_sandbox():
            sandbox_id = f"ig_{uuid.uuid4().hex[:12]}"
            post.id = sandbox_id
            post.status = "published"
            post.published_at = datetime.now(timezone.utc).isoformat()
            post.published_url = f"https://instagram.com/p/{sandbox_id}"
            logger.info("[instagram] Sandbox create_post — id=%s", sandbox_id)
            return post

        if not self._check_rate_limit():
            post.status = "failed"
            post.error_message = "Rate limited"
            return post

        try:
            # Build caption with hashtags
            caption = post.content_text
            if post.hashtags:
                hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
                caption += f"\n\n{hashtag_str}"

            if post.media_type == "carousel" and len(post.media_urls) > 1:
                # -- Carousel flow --
                child_ids: List[str] = []
                for media_url in post.media_urls:
                    is_video = self._is_video_url(media_url)
                    child_payload: Dict[str, Any] = {
                        "is_carousel_item": True,
                    }
                    if is_video:
                        child_payload["video_url"] = media_url
                        child_payload["media_type"] = "VIDEO"
                    else:
                        child_payload["image_url"] = media_url

                    child_result = self._api_call(
                        "POST",
                        f"{self.BASE_URL}/{self._ig_user_id}/media",
                        headers=self._build_headers(),
                        json_body=child_payload,
                    )
                    self._record_request()
                    child_ids.append(child_result.get("id", ""))

                # Create the carousel container
                carousel_payload: Dict[str, Any] = {
                    "media_type": "CAROUSEL",
                    "children": ",".join(child_ids),
                    "caption": caption,
                }
                if post.location_tag:
                    carousel_payload["location_id"] = post.location_tag

                container_result = self._api_call(
                    "POST",
                    f"{self.BASE_URL}/{self._ig_user_id}/media",
                    headers=self._build_headers(),
                    json_body=carousel_payload,
                )
                self._record_request()
                creation_id = container_result.get("id", "")

            elif post.media_type == "reel" or post.media_type == "video":
                # -- Reel / Video flow --
                reel_payload: Dict[str, Any] = {
                    "media_type": "REELS",
                    "video_url": post.media_urls[0] if post.media_urls else "",
                    "caption": caption,
                }
                if post.location_tag:
                    reel_payload["location_id"] = post.location_tag

                container_result = self._api_call(
                    "POST",
                    f"{self.BASE_URL}/{self._ig_user_id}/media",
                    headers=self._build_headers(),
                    json_body=reel_payload,
                )
                self._record_request()
                creation_id = container_result.get("id", "")

            else:
                # -- Single image feed post flow --
                image_payload: Dict[str, Any] = {
                    "image_url": post.media_urls[0] if post.media_urls else "",
                    "caption": caption,
                }
                if post.location_tag:
                    image_payload["location_id"] = post.location_tag

                container_result = self._api_call(
                    "POST",
                    f"{self.BASE_URL}/{self._ig_user_id}/media",
                    headers=self._build_headers(),
                    json_body=image_payload,
                )
                self._record_request()
                creation_id = container_result.get("id", "")

            # Step 2: Publish the container
            publish_result = self._api_call(
                "POST",
                f"{self.BASE_URL}/{self._ig_user_id}/media_publish",
                headers=self._build_headers(),
                json_body={"creation_id": creation_id},
            )
            self._record_request()

            post.id = publish_result.get("id", creation_id)
            post.status = "published"
            post.published_at = datetime.now(timezone.utc).isoformat()
            post.published_url = f"https://instagram.com/p/{post.id}"
            logger.info("[instagram] Post created — id=%s", post.id)
            return post

        except Exception as exc:
            post.status = "failed"
            post.error_message = str(exc)
            logger.error("[instagram] create_post failed: %s", exc)
            return post

    def update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost:
        """Update an existing IG post (limited — Instagram only allows caption edits on some media)."""
        self._require_connection()

        if self._is_sandbox():
            return SocialPost(
                id=post_id,
                platform="instagram",
                content_text=updates.get("content_text", ""),
                status="published",
                metadata={"sandbox": True, "updates_applied": list(updates.keys())},
            )

        if not self._check_rate_limit():
            return SocialPost(
                id=post_id,
                platform="instagram",
                content_text="",
                status="failed",
                error_message="Rate limited",
            )

        try:
            url = f"{self.BASE_URL}/{post_id}"
            payload: Dict[str, Any] = {}
            if "content_text" in updates:
                payload["caption"] = updates["content_text"]

            self._api_call("POST", url, headers=self._build_headers(), json_body=payload)
            self._record_request()

            return SocialPost(
                id=post_id,
                platform="instagram",
                content_text=updates.get("content_text", ""),
                status="published",
            )
        except Exception as exc:
            logger.error("[instagram] update_post failed: %s", exc)
            return SocialPost(
                id=post_id,
                platform="instagram",
                content_text="",
                status="failed",
                error_message=str(exc),
            )

    def delete_post(self, post_id: str) -> bool:
        """Delete a post.  Note: IG Graph API does not support deletion for all media types."""
        self._require_connection()

        if self._is_sandbox():
            logger.info("[instagram] Sandbox delete_post — id=%s", post_id)
            return True

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/{post_id}"
            self._api_call("DELETE", url, headers=self._build_headers())
            self._record_request()
            logger.info("[instagram] Post deleted — id=%s", post_id)
            return True
        except Exception as exc:
            logger.error("[instagram] delete_post failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Metrics & Insights
    # ------------------------------------------------------------------

    def get_metrics(self, post_id: str) -> SocialMetrics:
        """Fetch engagement metrics via ``/{media_id}/insights``."""
        if self._is_sandbox():
            return SocialMetrics(
                post_id=post_id,
                platform="instagram",
                impressions=2500,
                reach=1800,
                likes=210,
                comments=28,
                shares=15,
                saves=42,
                video_views=900,
                engagement_rate=round((210 + 28 + 15 + 42) / 1800, 4) if 1800 > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return SocialMetrics(post_id=post_id, platform="instagram")

        try:
            url = f"{self.BASE_URL}/{post_id}/insights"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={
                    "metric": "impressions,reach,engagement,saved,video_views",
                },
            )
            self._record_request()

            data_map: Dict[str, int] = {}
            for entry in result.get("data", []):
                name = entry.get("name", "")
                values = entry.get("values", [{}])
                data_map[name] = values[0].get("value", 0) if values else 0

            impressions = data_map.get("impressions", 0)
            reach = data_map.get("reach", 0)
            engagement = data_map.get("engagement", 0)
            saved = data_map.get("saved", 0)
            video_views = data_map.get("video_views", 0)

            return SocialMetrics(
                post_id=post_id,
                platform="instagram",
                impressions=impressions,
                reach=reach,
                likes=engagement,
                saves=saved,
                video_views=video_views,
                engagement_rate=round(engagement / reach, 4) if reach > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[instagram] get_metrics failed: %s", exc)
            return SocialMetrics(post_id=post_id, platform="instagram")

    def get_audience_insights(self) -> AudienceInsights:
        """Fetch IG audience demographics via the IG Insights API."""
        if self._is_sandbox():
            return AudienceInsights(
                platform="instagram",
                total_followers=5000,
                follower_growth_30d=180,
                top_locations=[
                    {"location": "New York, NY", "percentage": 22.0},
                    {"location": "Los Angeles, CA", "percentage": 14.5},
                ],
                age_gender_breakdown=[
                    {"age_range": "25-34", "gender": "female", "percentage": 32.0},
                    {"age_range": "25-34", "gender": "male", "percentage": 22.0},
                    {"age_range": "18-24", "gender": "female", "percentage": 18.0},
                ],
                active_hours=[
                    {"day": "Tuesday", "hour": 12, "engagement_level": "high"},
                    {"day": "Thursday", "hour": 18, "engagement_level": "high"},
                ],
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return AudienceInsights(platform="instagram")

        try:
            # Fetch follower count
            profile_url = f"{self.BASE_URL}/{self._ig_user_id}"
            profile = self._api_call(
                "GET",
                profile_url,
                headers=self._build_headers(),
                params={"fields": "followers_count"},
            )
            self._record_request()

            # Fetch demographics insights
            insights_url = f"{self.BASE_URL}/{self._ig_user_id}/insights"
            insights_result = self._api_call(
                "GET",
                insights_url,
                headers=self._build_headers(),
                params={
                    "metric": "audience_city,audience_gender_age,audience_locale",
                    "period": "lifetime",
                },
            )
            self._record_request()

            data_map: Dict[str, Any] = {}
            for entry in insights_result.get("data", []):
                data_map[entry.get("name", "")] = entry.get("values", [{}])

            # Parse city data
            city_data = data_map.get("audience_city", [{}])
            city_values = city_data[0].get("value", {}) if city_data else {}
            total_city = sum(city_values.values()) if city_values else 1
            top_locations = [
                {"location": city, "percentage": round(count / total_city * 100, 1)}
                for city, count in sorted(city_values.items(), key=lambda x: x[1], reverse=True)[:10]
            ]

            # Parse gender/age data
            ga_data = data_map.get("audience_gender_age", [{}])
            ga_values = ga_data[0].get("value", {}) if ga_data else {}
            total_ga = sum(ga_values.values()) if ga_values else 1
            age_gender_breakdown = [
                {
                    "age_range": key.split(".")[-1] if "." in key else key,
                    "gender": key.split(".")[0] if "." in key else "unknown",
                    "percentage": round(count / total_ga * 100, 1),
                }
                for key, count in ga_values.items()
            ]

            return AudienceInsights(
                platform="instagram",
                total_followers=profile.get("followers_count", 0),
                top_locations=top_locations,
                age_gender_breakdown=age_gender_breakdown,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[instagram] get_audience_insights failed: %s", exc)
            return AudienceInsights(platform="instagram")

    # ------------------------------------------------------------------
    # Media Upload
    # ------------------------------------------------------------------

    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload media by creating a container (IG does not support raw binary uploads)."""
        if self._is_sandbox():
            sandbox_id = f"ig_media_{uuid.uuid4().hex[:12]}"
            logger.info("[instagram] Sandbox upload_media — id=%s", sandbox_id)
            return sandbox_id

        self._require_connection()
        if not self._check_rate_limit():
            raise RuntimeError("Rate limited — cannot upload media")

        try:
            url = f"{self.BASE_URL}/{self._ig_user_id}/media"
            payload: Dict[str, Any] = {}
            if media_type == "video":
                payload["video_url"] = file_path
                payload["media_type"] = "VIDEO"
            else:
                payload["image_url"] = file_path

            result = self._api_call("POST", url, headers=self._build_headers(), json_body=payload)
            self._record_request()
            media_id: str = result.get("id", "")
            logger.info("[instagram] Media uploaded — id=%s", media_id)
            return media_id
        except Exception as exc:
            logger.error("[instagram] upload_media failed: %s", exc)
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
