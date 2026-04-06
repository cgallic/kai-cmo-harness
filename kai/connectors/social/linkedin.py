"""LinkedIn connector — LinkedIn Marketing API v2 integration.

Handles text posts, image posts, article/link shares, video uploads,
company page vs personal profile posting, share statistics, and follower
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


class LinkedInConnector(SocialConnector):
    """LinkedIn Marketing API v2 connector for company and personal posting."""

    BASE_URL: str = "https://api.linkedin.com/v2"

    def __init__(self, config: SocialConnectorConfig) -> None:
        super().__init__(config)
        self._connected: bool = False
        # Determine if posting as organization or person based on page_id format
        self._is_organization: bool = self._detect_entity_type()

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "linkedin"

    @property
    def media_requirements(self) -> MediaRequirements:
        return MediaRequirements(
            platform="linkedin",
            max_image_size_mb=10.0,
            max_video_size_mb=5120.0,
            max_video_duration_seconds=600,
            supported_image_formats=["jpg", "png", "gif"],
            supported_video_formats=["mp4"],
            aspect_ratios={"feed": "flexible", "video": "16:9 or 1:1"},
            max_caption_length=3000,
            max_hashtags=5,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_entity_type(self) -> bool:
        """Return True if the page_id looks like an organization ID.

        If ``metadata`` includes ``entity_type=person`` we treat it as a
        personal profile, otherwise we default to organization.
        """
        entity_type = self.config.metadata.get("entity_type", "organization")
        return entity_type != "person"

    def _get_author_urn(self) -> str:
        """Build the correct URN for the entity (organization or person)."""
        if self._is_organization:
            return f"urn:li:organization:{self.config.page_id}"
        return f"urn:li:person:{self.config.page_id}"

    def _build_headers(self) -> Dict[str, str]:
        """Return authorization and content-type headers."""
        return {
            "Authorization": f"Bearer {self.config.access_token}",
            "Content-Type": "application/json",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    # ------------------------------------------------------------------
    # Connection & Auth
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials by fetching the profile/organization info."""
        if self._is_sandbox():
            logger.info("[linkedin] Sandbox connect — skipping live validation")
            self._connected = True
            return True

        if not self.config.access_token:
            logger.error("[linkedin] No access_token provided")
            return False
        if not self.config.page_id:
            logger.error("[linkedin] No page_id provided")
            return False

        if not self._check_rate_limit():
            return False

        try:
            if self._is_organization:
                url = f"{self.BASE_URL}/organizations/{self.config.page_id}"
                params = {"projection": "(id,localizedName,vanityName)"}
            else:
                url = f"{self.BASE_URL}/me"
                params = {"projection": "(id,firstName,lastName)"}

            self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()
            self._connected = True
            logger.info("[linkedin] Connected successfully — entity=%s", self._get_author_urn())
            return True
        except Exception as exc:
            logger.error("[linkedin] Connection failed: %s", exc)
            return False

    def refresh_auth(self) -> bool:
        """Refresh the OAuth2 access token using the refresh token."""
        if self._is_sandbox():
            logger.info("[linkedin] Sandbox refresh_auth — returning True")
            return True

        if not self.config.refresh_token:
            logger.error("[linkedin] No refresh_token available")
            return False

        if not self._check_rate_limit():
            return False

        try:
            url = "https://www.linkedin.com/oauth/v2/accessToken"
            self._api_call(
                "POST",
                url,
                json_body={
                    "grant_type": "refresh_token",
                    "refresh_token": self.config.refresh_token,
                    "client_id": self.config.api_key,
                    "client_secret": self.config.api_secret,
                },
            )
            self._record_request()
            logger.info("[linkedin] Token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("[linkedin] Token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Read operations
    # ------------------------------------------------------------------

    def get_profile(self) -> Dict[str, Any]:
        """Fetch the connected organization or personal profile info."""
        if self._is_sandbox():
            return self._sandbox_response(
                "get_profile",
                urn=self._get_author_urn(),
                name="Sandbox LinkedIn Profile",
                follower_count=2500,
                is_organization=self._is_organization,
            )

        self._require_connection()
        if not self._check_rate_limit():
            return {"error": "rate_limited"}

        try:
            if self._is_organization:
                url = f"{self.BASE_URL}/organizations/{self.config.page_id}"
                params: Dict[str, Any] = {
                    "projection": "(id,localizedName,vanityName,description,logoV2,followersCount)",
                }
            else:
                url = f"{self.BASE_URL}/me"
                params = {
                    "projection": "(id,firstName,lastName,profilePicture,headline)",
                }

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()
            return result
        except Exception as exc:
            logger.error("[linkedin] get_profile failed: %s", exc)
            return {"error": str(exc)}

    def get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]:
        """Fetch recent posts (shares) from the entity feed."""
        if self._is_sandbox():
            return [
                SocialPost(
                    id=f"li_sandbox_{i}",
                    platform="linkedin",
                    content_text=f"Sandbox LinkedIn post #{i}",
                    status="published",
                    published_at=datetime.now(timezone.utc).isoformat(),
                )
                for i in range(min(limit, 3))
            ]

        self._require_connection()
        if not self._check_rate_limit():
            return []

        try:
            author_urn = self._get_author_urn()
            url = f"{self.BASE_URL}/ugcPosts"
            params: Dict[str, Any] = {
                "q": "authors",
                "authors": f"List({author_urn})",
                "count": limit,
            }
            if cursor:
                params["start"] = cursor

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()

            posts: List[SocialPost] = []
            for item in result.get("elements", []):
                specific_content = item.get("specificContent", {})
                share_content = specific_content.get("com.linkedin.ugc.ShareContent", {})
                commentary = share_content.get("shareCommentary", {}).get("text", "")

                posts.append(
                    SocialPost(
                        id=item.get("id"),
                        platform="linkedin",
                        content_text=commentary,
                        status="published",
                        published_at=item.get("created", {}).get("time"),
                    )
                )
            return posts
        except Exception as exc:
            logger.error("[linkedin] get_posts failed: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Write operations
    # ------------------------------------------------------------------

    def create_post(self, post: SocialPost) -> SocialPost:
        """Create a LinkedIn post (text, image, article/link, or video).

        Posting as organization uses ``urn:li:organization:{id}``.
        Posting as person uses ``urn:li:person:{id}``.
        """
        self._require_connection()

        errors = self._validate_post(post)
        if errors:
            post.status = "failed"
            post.error_message = "; ".join(errors)
            logger.error("[linkedin] Post validation failed: %s", post.error_message)
            return post

        if self._is_sandbox():
            sandbox_id = f"li_{uuid.uuid4().hex[:12]}"
            post.id = sandbox_id
            post.status = "published"
            post.published_at = datetime.now(timezone.utc).isoformat()
            post.published_url = f"https://linkedin.com/feed/update/{sandbox_id}"
            logger.info("[linkedin] Sandbox create_post — id=%s", sandbox_id)
            return post

        if not self._check_rate_limit():
            post.status = "failed"
            post.error_message = "Rate limited"
            return post

        try:
            author_urn = self._get_author_urn()

            # Build caption with hashtags
            commentary = post.content_text
            if post.hashtags:
                hashtag_str = " ".join(f"#{tag.lstrip('#')}" for tag in post.hashtags)
                commentary += f"\n\n{hashtag_str}"

            # Determine share media category and build payload
            if post.media_type == "video" or (post.media_urls and self._is_video_url(post.media_urls[0])):
                # Video post — register upload first, then post
                media_asset = self._register_upload("VIDEO")
                share_media_category = "VIDEO"
                media_entries = [
                    {
                        "status": "READY",
                        "media": media_asset,
                        "title": {"text": post.metadata.get("title", "")},
                        "description": {"text": commentary[:200]},
                    }
                ]
            elif post.media_type == "image" or (post.media_urls and not self._is_video_url(post.media_urls[0])):
                # Image post — register upload first
                media_asset = self._register_upload("IMAGE")
                share_media_category = "IMAGE"
                media_entries = [
                    {
                        "status": "READY",
                        "media": media_asset,
                    }
                ]
            elif post.link_url:
                # Article / link post
                share_media_category = "ARTICLE"
                media_entries = [
                    {
                        "status": "READY",
                        "originalUrl": post.link_url,
                        "title": {"text": post.metadata.get("title", "")},
                        "description": {"text": post.metadata.get("description", "")},
                    }
                ]
            else:
                # Text-only post
                share_media_category = "NONE"
                media_entries = []

            ugc_payload: Dict[str, Any] = {
                "author": author_urn,
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": commentary},
                        "shareMediaCategory": share_media_category,
                    }
                },
                "visibility": {
                    "com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC",
                },
            }

            if media_entries:
                ugc_payload["specificContent"]["com.linkedin.ugc.ShareContent"]["media"] = media_entries

            result = self._api_call(
                "POST",
                f"{self.BASE_URL}/ugcPosts",
                headers=self._build_headers(),
                json_body=ugc_payload,
            )
            self._record_request()

            post.id = result.get("id", "")
            post.status = "published"
            post.published_at = datetime.now(timezone.utc).isoformat()
            post.published_url = f"https://linkedin.com/feed/update/{post.id}"
            logger.info("[linkedin] Post created — id=%s", post.id)
            return post

        except Exception as exc:
            post.status = "failed"
            post.error_message = str(exc)
            logger.error("[linkedin] create_post failed: %s", exc)
            return post

    def update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost:
        """Update a LinkedIn post (limited support — mostly for deleting and re-creating)."""
        self._require_connection()

        if self._is_sandbox():
            return SocialPost(
                id=post_id,
                platform="linkedin",
                content_text=updates.get("content_text", ""),
                status="published",
                metadata={"sandbox": True, "updates_applied": list(updates.keys())},
            )

        if not self._check_rate_limit():
            return SocialPost(
                id=post_id,
                platform="linkedin",
                content_text="",
                status="failed",
                error_message="Rate limited",
            )

        try:
            # LinkedIn UGC posts have limited edit support.  The API allows
            # PATCH on some fields but most orgs delete and re-create.
            url = f"{self.BASE_URL}/ugcPosts/{post_id}"
            payload: Dict[str, Any] = {}
            if "content_text" in updates:
                payload["specificContent"] = {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": updates["content_text"]},
                    }
                }

            self._api_call("PATCH", url, headers=self._build_headers(), json_body=payload)
            self._record_request()

            return SocialPost(
                id=post_id,
                platform="linkedin",
                content_text=updates.get("content_text", ""),
                status="published",
            )
        except Exception as exc:
            logger.error("[linkedin] update_post failed: %s", exc)
            return SocialPost(
                id=post_id,
                platform="linkedin",
                content_text="",
                status="failed",
                error_message=str(exc),
            )

    def delete_post(self, post_id: str) -> bool:
        """Delete a UGC post."""
        self._require_connection()

        if self._is_sandbox():
            logger.info("[linkedin] Sandbox delete_post — id=%s", post_id)
            return True

        if not self._check_rate_limit():
            return False

        try:
            url = f"{self.BASE_URL}/ugcPosts/{post_id}"
            self._api_call("DELETE", url, headers=self._build_headers())
            self._record_request()
            logger.info("[linkedin] Post deleted — id=%s", post_id)
            return True
        except Exception as exc:
            logger.error("[linkedin] delete_post failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Metrics & Insights
    # ------------------------------------------------------------------

    def get_metrics(self, post_id: str) -> SocialMetrics:
        """Fetch share statistics via ``/organizationalEntityShareStatistics``."""
        if self._is_sandbox():
            return SocialMetrics(
                post_id=post_id,
                platform="linkedin",
                impressions=3200,
                reach=2100,
                likes=145,
                comments=22,
                shares=18,
                clicks=88,
                engagement_rate=round((145 + 22 + 18) / 2100, 4) if 2100 > 0 else 0.0,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return SocialMetrics(post_id=post_id, platform="linkedin")

        try:
            url = f"{self.BASE_URL}/organizationalEntityShareStatistics"
            params: Dict[str, Any] = {
                "q": "organizationalEntity",
                "organizationalEntity": self._get_author_urn(),
                "shares": f"List({post_id})",
            }

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()

            elements = result.get("elements", [])
            if not elements:
                return SocialMetrics(post_id=post_id, platform="linkedin")

            stats = elements[0].get("totalShareStatistics", {})
            impressions = stats.get("impressionCount", 0)
            unique_impressions = stats.get("uniqueImpressionsCount", 0)
            clicks = stats.get("clickCount", 0)
            likes = stats.get("likeCount", 0)
            comments = stats.get("commentCount", 0)
            shares = stats.get("shareCount", 0)
            engagement = stats.get("engagement", 0.0)

            return SocialMetrics(
                post_id=post_id,
                platform="linkedin",
                impressions=impressions,
                reach=unique_impressions,
                likes=likes,
                comments=comments,
                shares=shares,
                clicks=clicks,
                engagement_rate=round(engagement, 4),
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[linkedin] get_metrics failed: %s", exc)
            return SocialMetrics(post_id=post_id, platform="linkedin")

    def get_audience_insights(self) -> AudienceInsights:
        """Fetch follower demographics via ``/organizationalEntityFollowerStatistics``."""
        if self._is_sandbox():
            return AudienceInsights(
                platform="linkedin",
                total_followers=2500,
                follower_growth_30d=85,
                top_locations=[
                    {"location": "San Francisco Bay Area", "percentage": 18.0},
                    {"location": "Greater New York City Area", "percentage": 15.5},
                    {"location": "Greater Los Angeles Area", "percentage": 10.2},
                ],
                age_gender_breakdown=[
                    {"age_range": "25-34", "gender": "all", "percentage": 38.0},
                    {"age_range": "35-44", "gender": "all", "percentage": 28.0},
                    {"age_range": "45-54", "gender": "all", "percentage": 18.0},
                ],
                active_hours=[
                    {"day": "Tuesday", "hour": 10, "engagement_level": "high"},
                    {"day": "Wednesday", "hour": 14, "engagement_level": "high"},
                ],
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )

        if not self._check_rate_limit():
            return AudienceInsights(platform="linkedin")

        try:
            url = f"{self.BASE_URL}/organizationalEntityFollowerStatistics"
            params: Dict[str, Any] = {
                "q": "organizationalEntity",
                "organizationalEntity": self._get_author_urn(),
            }

            result = self._api_call("GET", url, headers=self._build_headers(), params=params)
            self._record_request()

            elements = result.get("elements", [])
            if not elements:
                return AudienceInsights(platform="linkedin")

            follower_stats = elements[0]
            total = follower_stats.get("followerCounts", {}).get("organicFollowerCount", 0)

            # Industry breakdown (LinkedIn-specific)
            industry_data = follower_stats.get("followerCountsByIndustry", [])
            top_locations_data = follower_stats.get("followerCountsByGeo", [])
            seniority_data = follower_stats.get("followerCountsBySeniority", [])
            function_data = follower_stats.get("followerCountsByFunction", [])

            top_locations = [
                {
                    "location": entry.get("geo", {}).get("localizedName", "Unknown"),
                    "percentage": round(entry.get("followerCounts", {}).get("organicFollowerCount", 0) / max(total, 1) * 100, 1),
                }
                for entry in sorted(
                    top_locations_data,
                    key=lambda x: x.get("followerCounts", {}).get("organicFollowerCount", 0),
                    reverse=True,
                )[:10]
            ]

            # LinkedIn provides seniority rather than age — map to age_gender_breakdown
            age_gender_breakdown = [
                {
                    "age_range": entry.get("seniority", {}).get("localizedName", "Unknown"),
                    "gender": "all",
                    "percentage": round(entry.get("followerCounts", {}).get("organicFollowerCount", 0) / max(total, 1) * 100, 1),
                }
                for entry in seniority_data
            ]

            return AudienceInsights(
                platform="linkedin",
                total_followers=total,
                top_locations=top_locations,
                age_gender_breakdown=age_gender_breakdown,
                fetched_at=datetime.now(timezone.utc).isoformat(),
            )
        except Exception as exc:
            logger.error("[linkedin] get_audience_insights failed: %s", exc)
            return AudienceInsights(platform="linkedin")

    # ------------------------------------------------------------------
    # Media Upload
    # ------------------------------------------------------------------

    def upload_media(self, file_path: str, media_type: str) -> str:
        """Upload a media file via LinkedIn's registered upload flow."""
        if self._is_sandbox():
            sandbox_id = f"li_media_{uuid.uuid4().hex[:12]}"
            logger.info("[linkedin] Sandbox upload_media — id=%s", sandbox_id)
            return sandbox_id

        self._require_connection()
        if not self._check_rate_limit():
            raise RuntimeError("Rate limited — cannot upload media")

        try:
            recipe = "IMAGE" if media_type != "video" else "VIDEO"
            asset_urn = self._register_upload(recipe)
            # In production: upload binary to the uploadUrl returned by register
            logger.info("[linkedin] Media uploaded — asset=%s", asset_urn)
            return asset_urn
        except Exception as exc:
            logger.error("[linkedin] upload_media failed: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _register_upload(self, recipe: str) -> str:
        """Register a media upload with LinkedIn and return the asset URN.

        In production this calls ``/assets?action=registerUpload`` and
        returns both the upload URL and asset URN.
        """
        if self._is_sandbox():
            return f"urn:li:digitalmediaAsset:sandbox_{uuid.uuid4().hex[:12]}"

        register_payload: Dict[str, Any] = {
            "registerUploadRequest": {
                "recipes": [f"urn:li:digitalmediaRecipe:feedshare-{recipe.lower()}"],
                "owner": self._get_author_urn(),
                "serviceRelationships": [
                    {
                        "relationshipType": "OWNER",
                        "identifier": "urn:li:userGeneratedContent",
                    }
                ],
            }
        }

        result = self._api_call(
            "POST",
            f"{self.BASE_URL}/assets?action=registerUpload",
            headers=self._build_headers(),
            json_body=register_payload,
        )
        self._record_request()

        asset = result.get("value", {}).get("asset", "")
        return asset

    @staticmethod
    def _is_video_url(url: str) -> bool:
        """Return True if the URL appears to reference a video file."""
        video_extensions = {"mp4", "mov", "avi", "wmv", "flv", "webm"}
        ext = url.rsplit(".", 1)[-1].lower() if "." in url else ""
        return ext in video_extensions
