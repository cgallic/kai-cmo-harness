"""Outstand social publishing connector.

The API paths are configurable because Outstand workspaces can expose a
different API prefix.  The connector keeps the harness' provider-neutral
``SocialPost`` contract while preserving provider receipts in metadata.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import AudienceInsights, MediaRequirements, SocialConnector, SocialConnectorConfig, SocialMetrics, SocialPost

logger = logging.getLogger(__name__)


class OutstandConnector(SocialConnector):
    """Adapter for Outstand accounts and post scheduling/read-back."""

    BASE_URL = "https://api.outstand.so/v1"

    @property
    def platform_name(self) -> str:
        return "outstand"

    @property
    def media_requirements(self) -> MediaRequirements:
        return MediaRequirements(
            platform="outstand", max_image_size_mb=25, max_video_size_mb=1024,
            max_video_duration_seconds=3600, supported_image_formats=["jpg", "jpeg", "png", "webp"],
            supported_video_formats=["mp4", "mov"], aspect_ratios={"feed": "flexible"},
            max_caption_length=10000, max_hashtags=30,
        )

    def _headers(self) -> Dict[str, str]:
        return {"Authorization": f"Bearer {self.config.access_token or self.config.api_key}", "Content-Type": "application/json"}

    def _path(self, name: str) -> str:
        return str(self.config.metadata.get(f"{name}_path", {
            "accounts": "/social-accounts", "posts": "/posts/"
        }[name]))

    def _idempotency_key(self, post: SocialPost) -> str:
        explicit = post.metadata.get("idempotency_key") or self.config.metadata.get("idempotency_key")
        if explicit:
            return str(explicit)
        raw = "|".join([self.platform_name, self.config.page_id or "", post.content_text,
                         post.schedule_time or "", *post.media_urls])
        return "outstand-" + hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]

    def connect(self) -> bool:
        if self._is_sandbox():
            self._connected = True
            return True
        if not (self.config.access_token or self.config.api_key):
            return False
        try:
            self.list_accounts()
            self._connected = True
            return True
        except Exception as exc:
            logger.error("[outstand] connection failed: %s", exc)
            return False

    def refresh_auth(self) -> bool:
        return bool(self.config.access_token or self.config.api_key) if not self._is_sandbox() else True

    def list_accounts(self) -> List[Dict[str, Any]]:
        """Return provider accounts, retaining the raw provider objects."""
        if self._is_sandbox():
            return [{"id": self.config.page_id or "outstand_sandbox_account", "name": "Sandbox Outstand Account"}]
        if not self._check_rate_limit():
            raise RuntimeError("Outstand rate limit exceeded")
        result = self._api_call("GET", f"{self.BASE_URL}{self._path('accounts')}", headers=self._headers())
        self._record_request()
        return result.get("data", result.get("accounts", []))

    def get_profile(self) -> Dict[str, Any]:
        accounts = self.list_accounts()
        return next((a for a in accounts if str(a.get("id")) == str(self.config.page_id)), accounts[0] if accounts else {})

    def get_posts(self, limit: int = 20, cursor: Optional[str] = None) -> List[SocialPost]:
        if self._is_sandbox():
            return []
        self._require_connection()
        result = self._api_call("GET", f"{self.BASE_URL}{self._path('posts')}", headers=self._headers(), params={"account_id": self.config.page_id, "limit": limit, **({"cursor": cursor} if cursor else {})})
        self._record_request()
        return [self._post_from_provider(item) for item in result.get("data", result.get("posts", []))]

    def get_post(self, post_id: str) -> SocialPost:
        """Read one provider post; used as the independent publish read-back."""
        self._require_connection()
        if self._is_sandbox():
            return SocialPost(id=post_id, platform="outstand", content_text="", status="published", metadata={"sandbox": True})
        result = self._api_call("GET", f"{self.BASE_URL}{self._path('posts')}/{post_id}", headers=self._headers())
        self._record_request()
        return self._post_from_provider(result.get("data", result.get("post", result)))

    def _post_from_provider(self, item: Dict[str, Any]) -> SocialPost:
        return SocialPost(id=str(item.get("id")) if item.get("id") is not None else None, platform="outstand",
                          content_text=item.get("content", item.get("text", "")), media_urls=item.get("media_urls", []),
                          schedule_time=item.get("scheduled_at", item.get("schedule_time")), status=item.get("status", "published"),
                          published_at=item.get("published_at"), published_url=item.get("url", item.get("permalink")), metadata={"provider": item})

    def create_post(self, post: SocialPost) -> SocialPost:
        self._require_connection()
        errors = self._validate_post(post)
        if errors:
            post.status, post.error_message = "failed", "; ".join(errors)
            return post
        key = self._idempotency_key(post)
        if self._is_sandbox():
            post.id = post.id or f"outstand_sandbox_{key[-12:]}"
            post.status = "scheduled" if post.schedule_time else "published"
            post.metadata["idempotency_key"] = key
            return post
        if not self._check_rate_limit():
            post.status, post.error_message = "failed", "Rate limited"
            return post
        container: Dict[str, Any] = {"content": post.content_text}
        if post.media_urls:
            container["media"] = [
                {"url": url, "filename": url.rsplit("/", 1)[-1] or "media"}
                for url in post.media_urls
            ]
        payload: Dict[str, Any] = {
            "containers": [container],
            "accounts": [self.config.page_id] if self.config.page_id else [],
        }
        if post.schedule_time:
            payload["scheduledAt"] = post.schedule_time
        try:
            result = self._api_call("POST", f"{self.BASE_URL}{self._path('posts')}", headers={**self._headers(), "Idempotency-Key": key}, json_body=payload)
            self._record_request()
            provider = result.get("data", result.get("post", result))
            returned = self._post_from_provider(provider)
            post.id, post.status, post.published_at, post.published_url = returned.id, returned.status, returned.published_at, returned.published_url
            post.metadata.update({"idempotency_key": key, "provider_receipt": provider})
            return post
        except Exception as exc:
            post.status, post.error_message = "failed", str(exc)
            return post

    def update_post(self, post_id: str, updates: Dict[str, Any]) -> SocialPost:
        raise NotImplementedError("Outstand adapter intentionally supports create/read, not update")

    def delete_post(self, post_id: str) -> bool:
        raise NotImplementedError("Outstand adapter intentionally supports create/read, not delete")

    def get_metrics(self, post_id: str) -> SocialMetrics:
        return SocialMetrics(post_id=post_id, platform="outstand")

    def get_audience_insights(self) -> AudienceInsights:
        return AudienceInsights(platform="outstand")

    def upload_media(self, file_path: str, media_type: str) -> str:
        raise NotImplementedError("Outstand media upload is supplied by the caller as a URL")
