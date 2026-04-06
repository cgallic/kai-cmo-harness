"""TikTok connector — TikTok Business API v2 integration.

Handles video publishing (init + upload + status), photo mode posts,
privacy settings, engagement metrics, audience demographics, and
trending sound discovery.  All calls are routed through the abstract
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
    SocialConnector,
    SocialConnectorConfig,
    SocialMetrics,
    SocialPost,
)

logger = logging.getLogger(__name__)


class TikTokConnector(SocialConnector):
    """TikTok Business API v2 connector for video/photo publishing and analytics."""

    BASE_URL: str = "https://open.tiktokapis.com/v2"

    # Privacy levels supported by the TikTok API
    PRIVACY_LEVELS = (
        "PUBLIC_TO_EVERYONE",
        "MUTUAL_FOLLOW_FRIENDS",
        "FOLLOWER_OF_CREATOR",
        "SELF_ONLY",
    )

    def __init__(self, config: SocialConnectorConfig) -> None:
        super().__init__(config)
        self._connected: bool = False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "tiktok"

    @property
    def media_requirements(self) -> MediaRequirements:
        return MediaRequirements(
            platform="tiktok",
            max_image_size_mb=10.0,
            max_video_size_mb=4096.0,
            max_video_duration_seconds=600,
            supported_image_formats=["jpg", "png", "webp"],
            supported_video_formats=["mp4", "mov", "webm"],
            aspect_ratios={"video": "9:16"},
            max_caption_length=2200,
            max_hashtags=100,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Return authorization headers for TikTok Business API."""
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json; charset=UTF-8",
        }

    def _get_privacy_level(self) -> str:
        """Read privacy level from config metadata or default to PUBLIC."""
        level = self.config.metadata.get("privacy_level", "PUBLIC_TO_EVERYONE")
        if level in self.PRIVACY_LEVELS:
            return level
        return "PUBLIC_TO_EVERYONE"

    def _get_trending_sounds(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Fetch trending audio/sounds from TikTok (stub).

        In production this would call the TikTok Research API or
        scrape trending sounds.  Returns sandbox data for now.
        """
        if self._is_sandbox():
            return [
                {
                    "id": f"sound_{uuid.uuid4().hex[:8]}",
                    "title": f"Trending Sound #{i + 1}",
                    "author": f"Artist {i + 1}",
                    "duration_seconds": 30 + i * 5,
                    "usage_count": (10000 - i * 800),
                    "is_original": i % 3 == 0,
                }
                for i in range(min(limit, 20))
            ]

        if not self._check_rate_limit():
            return []

        try:
            # The trending sounds endpoint is part of the Research API
            url = f"{self.BASE_URL}/research/music/trending/"
            result = self._api_call(
                "POST",
                url,
                headers=self._build_headers(),
                json_body={"count": limit},
            )
            self._record_request()
            return result.get("data", {}).get("sounds", [])
        except Exception as exc:
            logger.error("[tiktok] _get_trending_sounds failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Connection & Auth
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials by fetching the business user info."""
        if self._is_sandbox():
            logger.info("[tiktok] Sandbox connect — skipping live validation")
            self._connected = True
            return True

        if not self.config.access_token:
            logger.error("[tiktok] No access_token provided")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/user/info/"
            self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={"fields": "open_id,union_id,avatar_url,display_name,follower_count"},
            )
            self._record_request()
            self._connected = True
            logger.info("[tiktok] Connected successfully")
            return True
        except Exception as exc:
            logger.error("[tiktok] Connection failed: %s", exc)
            return False

    def refresh_auth(self) -> bool:
        """Refresh the TikTok OAuth token."""
        if self._is_sandbox():
            logger.info("[tiktok] Sandbox refresh_auth — returning True")
            return True

        if not self.config.refresh_token:
            logger.error("[tiktok] No refresh_token available")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = "https://open.tiktokapis.com/v2/oauth/token/"
            self._api_call(
                "POST",
                url,
                json_body={
                    "client_key": self.config.api_key,
                    "client_secret": self.config.api_secret,
                    "grant_type": "refresh_token",
                    "refresh_token": self.config.refresh_token,
                },
            )
            self._record_request()
            logger.info("[tiktok] Token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("[tiktok] Token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_profile(self) -> Dict[str, Any]:
        """Fetch the connected TikTok user profile."""
        if self._is_sandbox():
            return self._sandbox_response(
                "get_profile",
                display_name="Sandbox Creator",
                follower_count=15000,
                following_count=250,
                likes_count=120000,
                video_count=85,
            )

        self._require_connection()
        if not self._check_rate_limit():
            return {"error": "rate_limited"}

        try:
            url = f"{self.BASE_URL}/user/info/"
            result = self._api_call(
                "GET",
                url,
                headers=self._build_headers(),
                params={
                    "fields": "open_id,union_id,avatar_url,display_name,bio_description,"
                    "follower_count,following_count,likes_count,video_count",
                },
            )
            self._record_request()
            return result.get("data", {}).get("user", result)
        except Exception as exc:
            logger.error("[tiktok] get_profile failed: %s", exc)
            return {"error": str(exc)}

    def get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]:
        """Fetch recent videos from the TikTok account."""
        if self._is_sandbox():
            return [
                SocialPost(
                    id=f"tt_sandbox_{i}",
                    platform="tiktok",
                    content_text=f"Sandbox TikTok video #{i}",
                    media_type="video",
                    status="published",
                    published_at=datetime.now(timezone.utc).isoformat(),
                )
                for i in range(min(limit, 3))
            ]

        self._require_connection()
        if not self._check_rate_limit():
            return []

        try:
            url = f"{self.BASE_URL}/video/list/"
            payload: Dict[str, Any] = {
                "max_count": limit,
                "fields": "id,title,video_description,create_time,share_url,duration,cover_image_url",
            }
            if cursor:
                payload["cursor"] = cursor

            result = self._api_call("POST", url, headers=self._build_headers(), json_body=payload)
            self._record_request()

            posts: List[SocialPost] = []
            for video in result.get("data", {}).get("videos", []):
                posts.append(
                    SocialPost(
                        id=video.get("id"),
                        platform="tiktok",
                        content_text=video.get("video_description", video.get("title", "")),
                        media_type="video",
                        status="published",
                        published_at=video.get("create_time"),
                        published_url=video.get("share_url"),
                    )
                )
            return posts
        except Exception as exc:
            logger.error("[tiktok] get_posts failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_post(self, post: SocialPost) -> SocialPost:
        """Publish a TikTok video or photo-mode post.

        **Video flow**: init publish -> upload video -> check status.
        **Photo mode**: init with ``post_mode=DIRECT_POST`` and
        ``media_type=PHOTO``.

        Supports ``disable_comment``, ``disable_duet``, ``disable_stitch``
        flags via ``post.metadata``.
        """
        self._require_connection()

        errors = self._validate_post(post)
        if errors:
            post.status = "failed"
            post.error_message = "; ".join(errors)
            logger.error("[tiktok] Post validation failed: %s", post.error_message)
            return post

        if self._is_sandbox():
            sandbox_id = f"tt_{uuid.uuid4().hex[:12]}"
            post.id = sandbox_id
            post.status = "published"
            post.published_at = datetime.now(timezone.utc).isoformat()
            post.published_url = f"https://tiktok.com/@sandbox/video/{sandbox_id}"
            logger.info("[tiktok] Sandbox create_post — id=%s", sandbox_id)
            return post

        if not self._check_rate_limit():
            post.status = "failed"
            post.error_message = "Rate limited"
            return post

        try:
            # Build caption with hashtags
            title = post.content_text
            if post.hashtags:
                hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
                title += f" {hashtag_str}"

            privacy_level = self._get_privacy_level()

            # Extract interaction flags from metadata
            disable_comment = post.metadata.get("disable_comment", False)
            disable_duet = post.metadata.get("disable_duet", False)
            disable_stitch = post.metadata.get("disable_stitch", False)

            if post.media_type == "image":
                # -- Photo mode flow --
                url = f"{self.BASE_URL}/post/publish/content/init/"
                init_payload: Dict[str, Any] = {
                    "post_info": {
                        "title": title,
                        "privacy_level": privacy_level,
                        "disable_comment": disable_comment,
                        "post_mode": "DIRECT_POST",
                        "media_type": "PHOTO",
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "photo_images": post.media_urls,
                    },
                }

                result = self._api_call("POST", url, headers=self._build_headers(), json_body=init_payload)
                self._record_request()

                publish_id = result.get("data", {}).get("publish_id", "")
                post.id = publish_id
                post.status = "published"
                post.published_at = datetime.now(timezone.utc).isoformat()
                logger.info("[tiktok] Photo post created — publish_id=%s", publish_id)

            else:
                # -- Video flow: init -> upload -> status check --
                # Step 1: Initialize publish
                init_url = f"{self.BASE_URL}/post/publish/video/init/"
                init_payload = {
                    "post_info": {
                        "title": title,
                        "privacy_level": privacy_level,
                        "disable_comment": disable_comment,
                        "disable_duet": disable_duet,
                        "disable_stitch": disable_stitch,
                    },
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "video_url": post.media_urls[0] if post.media_urls else "",
                    },
                }

                if post.schedule_time:
                    init_payload["post_info"]["schedule_time"] = post.schedule_time

                init_result = self._api_call(
                    "POST", init_url, headers=self._build_headers(), json_body=init_payload
                )
                self._record_request()

                publish_id = init_result.get("data", {}).get("publish_id", "")
                upload_url = init_result.get("data", {}).get("upload_url", "")

                # Step 2: Upload video to the provided URL (in production)
                if upload_url and post.media_urls:
                    try:
                        self._api_call(
                            "PUT",
                            upload_url,
                            headers={"Content-Type": "video/mp4"},
                            data=f"<binary_file:{post.media_urls[0]}>",
                        )
                        self._record_request()
                    except NotImplementedError:
                        # Expected in non-sandbox mode before HTTP client is wired
                        logger.warning("[tiktok] Video upload skipped — live API not yet implemented")

                # Step 3: Check publish status
                status_url = f"{self.BASE_URL}/post/publish/status/fetch/"
                status_result = self._api_call(
                    "POST",
                    status_url,
                    headers=self._build_headers(),
                    json_body={"publish_id": publish_id},
                )
                self._record_request()

                publish_status = status_result.get("data", {}).get("status", "PROCESSING")
                post.id = publish_id

                if publish_status == "PUBLISH_COMPLETE":
                    post.status = "published"
                    post.published_at = datetime.now(timezone.utc).isoformat()
                elif post.schedule_time:
                    post.status = "scheduled"
                else:
                    # Still processing
                    post.status = "pending_approval"
                    post.metadata["publish_status"] = publish_status

                logger.info(
                    "[tiktok] Video post initiated — publish_id=%s status=%s",
                    publish_id,
                    post.status,
                )

            return post

        except Exception as exc:
            post.status = "failed"
            post.error_message = str(exc)
            logger.error("[tiktok] create_post failed: %s", exc)
            return post

    def update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost:
        """Update a TikTok post (very limited — TikTok does not support editing published videos)."""
        self._require_connection()

        if self._is_sandbox():
            return SocialPost(
                id=post_id,
                platform="tiktok",
                content_text=updates.get("content_text", ""),
                status="published",
                metadata={"sandbox": True, "updates_applied": list(updates.keys())},
            )

        # TikTok does not support editing published posts
        logger.warning("[tiktok] TikTok does not support editing published videos")
        return SocialPost(
            id=post_id,
            platform="tiktok",
            content_text=updates.get("content_text", ""),
            status="failed",
            error_message="TikTok does not support editing published videos — delete and re-post instead",
        )

    def delete_post(self, post_id: str) -> bool:
        """Delete a TikTok video."""
        self._require_connection()

        if self._is_sandbox():
            logger.info("[tiktok] Sandbox delete_post — id=%s", post_id)
            return True

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/video/delete/"
            self._api_call(
                "POST",
                url,
                headers=self._build_headers(),
                json_body={"video_id": post_id},
            )
            self._record_request()
            logger.info("[tiktok] Post deleted — id=%s", post_id)
            return True
        except Exception as exc:
            logger.error("[tiktok] delete_post failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Metrics & Insights
    # ------------------------------------------------------------------

    def get_metrics(self, post_id: str) -> SocialMetrics:
        """Fetch video metrics via ``/video/query/``."""
        if self._is_sandbox():
            return SocialMetrics(
                post_id=post_id,
                platform="tiktok",
                impressions=45000,
                reach=32000,
                likes=3200,
                comments=280,
                shares=450,
                saves=180,
                video_views=38000,
                engagement_rate=round((3200 + 280 + 450 + 180) / 32000, 4) if 32000 > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return SocialMetrics(post_id=post_id, platform="tiktok")

        try:
            url = f"{self.BASE_URL}/video/query/"
            result = self._api_call(
                "POST",
                url,
                headers=self._build_headers(),
                json_body={
                    "filters": {"video_ids": [post_id]},
                    "fields": "id,like_count,comment_count,share_count,view_count,forward_count,average_watch_time,video_duration",
                },
            )
            self._record_request()

            videos = result.get("data", {}).get("videos", [])
            if not videos:
                return SocialMetrics(post_id=post_id, platform="tiktok")

            video = videos[0]
            views = video.get("view_count", 0)
            likes = video.get("like_count", 0)
            comments_count = video.get("comment_count", 0)
            shares = video.get("share_count", 0)
            forwards = video.get("forward_count", 0)

            return SocialMetrics(
                post_id=post_id,
                platform="tiktok",
                impressions=views,
                reach=views,
                likes=likes,
                comments=comments_count,
                shares=shares + forwards,
                video_views=views,
                engagement_rate=round((likes + comments_count + shares) / views, 4) if views > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[tiktok] get_metrics failed: %s", exc)
            return SocialMetrics(post_id=post_id, platform="tiktok")

    def get_audience_insights(self) -> AudienceInsights:
        """Fetch follower demographics via ``/business/get/``."""
        if self._is_sandbox():
            return AudienceInsights(
                platform="tiktok",
                total_followers=15000,
                follower_growth_30d=1200,
                top_locations=[
                    {"location": "United States", "percentage": 45.0},
                    {"location": "United Kingdom", "percentage": 12.0},
                    {"location": "Canada", "percentage": 8.0},
                ],
                age_gender_breakdown=[
                    {"age_range": "18-24", "gender": "female", "percentage": 28.0},
                    {"age_range": "18-24", "gender": "male", "percentage": 22.0},
                    {"age_range": "25-34", "gender": "female", "percentage": 20.0},
                    {"age_range": "25-34", "gender": "male", "percentage": 15.0},
                ],
                active_hours=[
                    {"day": "Monday", "hour": 20, "engagement_level": "high"},
                    {"day": "Friday", "hour": 18, "engagement_level": "high"},
                    {"day": "Saturday", "hour": 14, "engagement_level": "high"},
                ],
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return AudienceInsights(platform="tiktok")

        try:
            url = f"{self.BASE_URL}/business/get/"
            result = self._api_call(
                "POST",
                url,
                headers=self._build_headers(),
                json_body={
                    "fields": "followers_count,audience_countries,audience_genders,audience_ages",
                },
            )
            self._record_request()

            data = result.get("data", {})
            followers = data.get("followers_count", 0)

            # Country breakdown
            countries = data.get("audience_countries", [])
            top_locations = [
                {"location": entry.get("country", "Unknown"), "percentage": entry.get("percentage", 0)}
                for entry in countries[:10]
            ]

            # Gender x Age breakdown
            genders = data.get("audience_genders", [])
            ages = data.get("audience_ages", [])
            age_gender_breakdown = []
            for age_entry in ages:
                for gender_entry in genders:
                    age_gender_breakdown.append(
                        {
                            "age_range": age_entry.get("age_range", "Unknown"),
                            "gender": gender_entry.get("gender", "unknown"),
                            "percentage": round(
                                age_entry.get("percentage", 0) * gender_entry.get("percentage", 0) / 100, 1
                            ),
                        }
                    )

            return AudienceInsights(
                platform="tiktok",
                total_followers=followers,
                top_locations=top_locations,
                age_gender_breakdown=age_gender_breakdown,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[tiktok] get_audience_insights failed: %s", exc)
            return AudienceInsights(platform="tiktok")

    # ------------------------------------------------------------------
    # Media Upload
    # ------------------------------------------------------------------

    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload media to TikTok via the publish init flow."""
        if self._is_sandbox():
            sandbox_id = f"tt_media_{uuid.uuid4().hex[:12]}"
            logger.info("[tiktok] Sandbox upload_media — id=%s", sandbox_id)
            return sandbox_id

        self._require_connection()
        if not self._check_rate_limit():
            raise RuntimeError("Rate limited — cannot upload media")

        try:
            if media_type == "video":
                url = f"{self.BASE_URL}/post/publish/video/init/"
                payload: Dict[str, Any] = {
                    "source_info": {
                        "source": "FILE_UPLOAD",
                        "video_size": 0,  # Would be set from actual file
                        "chunk_size": 10 * 1024 * 1024,  # 10MB chunks
                        "total_chunk_count": 1,
                    },
                }
            else:
                url = f"{self.BASE_URL}/post/publish/content/init/"
                payload = {
                    "source_info": {
                        "source": "PULL_FROM_URL",
                        "photo_images": [file_path],
                    },
                    "post_info": {
                        "media_type": "PHOTO",
                        "post_mode": "DIRECT_POST",
                    },
                }

            result = self._api_call("POST", url, headers=self._build_headers(), json_body=payload)
            self._record_request()

            media_id: str = result.get("data", {}).get("publish_id", "")
            logger.info("[tiktok] Media upload initiated — id=%s", media_id)
            return media_id
        except Exception as exc:
            logger.error("[tiktok] upload_media failed: %s", exc)
            raise
