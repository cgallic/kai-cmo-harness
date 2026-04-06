"""Shared Pipedream client configuration, error handling, and constants.

All Pipedream interaction in Kai flows through this module's client.
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Error taxonomy
# ---------------------------------------------------------------------------


class PipedreamErrorKind(str, Enum):
    """Normalized failure categories for operator-readable diagnostics."""

    AUTH_FAILURE = "auth_failure"
    SCOPE_FAILURE = "scope_failure"
    PROVIDER_VALIDATION = "provider_validation"
    RATE_LIMIT = "rate_limit"
    TRANSIENT = "transient"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    UNSUPPORTED_ACTION = "unsupported_action"
    UNKNOWN = "unknown"


class PipedreamError(Exception):
    """Structured error from a Pipedream API call."""

    def __init__(
        self,
        message: str,
        kind: PipedreamErrorKind = PipedreamErrorKind.UNKNOWN,
        status_code: Optional[int] = None,
        raw: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(message)
        self.kind = kind
        self.status_code = status_code
        self.raw = raw or {}


def classify_error(status_code: int, body: Any = None) -> PipedreamErrorKind:
    """Map an HTTP status code to a normalized error kind."""
    if status_code == 401:
        return PipedreamErrorKind.AUTH_FAILURE
    if status_code == 403:
        return PipedreamErrorKind.SCOPE_FAILURE
    if status_code == 404:
        return PipedreamErrorKind.NOT_FOUND
    if status_code == 429:
        return PipedreamErrorKind.RATE_LIMIT
    if status_code == 504:
        return PipedreamErrorKind.TIMEOUT
    if status_code >= 500:
        return PipedreamErrorKind.TRANSIENT
    if status_code == 422:
        return PipedreamErrorKind.PROVIDER_VALIDATION
    return PipedreamErrorKind.UNKNOWN


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------


@dataclass
class PipedreamConfig:
    """Resolved Pipedream Connect credentials and project settings."""

    client_id: str
    client_secret: str
    project_id: str
    environment: str = "development"  # "development" | "production"
    webhook_base_url: Optional[str] = None  # for connect token callbacks

    @classmethod
    def from_env(cls) -> "PipedreamConfig":
        """Build config from environment variables."""
        client_id = os.environ.get("PIPEDREAM_CLIENT_ID", "")
        client_secret = os.environ.get("PIPEDREAM_CLIENT_SECRET", "")
        project_id = os.environ.get("PIPEDREAM_PROJECT_ID", "")
        environment = os.environ.get("PIPEDREAM_ENVIRONMENT", "development")
        webhook_base_url = os.environ.get("PIPEDREAM_WEBHOOK_BASE_URL")

        if not all([client_id, client_secret, project_id]):
            logger.warning(
                "Pipedream credentials not fully configured — "
                "set PIPEDREAM_CLIENT_ID, PIPEDREAM_CLIENT_SECRET, PIPEDREAM_PROJECT_ID"
            )
        return cls(
            client_id=client_id,
            client_secret=client_secret,
            project_id=project_id,
            environment=environment,
            webhook_base_url=webhook_base_url,
        )


# ---------------------------------------------------------------------------
# Client wrapper
# ---------------------------------------------------------------------------


class PipedreamClient:
    """Thin wrapper around the ``pipedream`` Python SDK.

    Centralises client construction so the rest of Kai never imports the SDK
    directly.  Lazy-initialises on first use so missing credentials don't
    crash import time.
    """

    def __init__(self, config: Optional[PipedreamConfig] = None):
        self._config = config or PipedreamConfig.from_env()
        self._client = None  # lazy

    @property
    def config(self) -> PipedreamConfig:
        return self._config

    @property
    def sdk(self):
        """Return the initialised ``pipedream.Pipedream`` client.

        Raises ``PipedreamError`` if credentials are missing.
        """
        if self._client is None:
            self._client = self._build_client()
        return self._client

    def _build_client(self):
        cfg = self._config
        if not all([cfg.client_id, cfg.client_secret, cfg.project_id]):
            raise PipedreamError(
                "Pipedream credentials not configured",
                kind=PipedreamErrorKind.AUTH_FAILURE,
            )
        try:
            from pipedream import Pipedream

            return Pipedream(
                project_id=cfg.project_id,
                project_environment=cfg.environment,
                client_id=cfg.client_id,
                client_secret=cfg.client_secret,
            )
        except ImportError:
            raise PipedreamError(
                "pipedream SDK not installed — run: pip install pipedream",
                kind=PipedreamErrorKind.UNKNOWN,
            )
        except Exception as exc:
            raise PipedreamError(
                f"Failed to initialise Pipedream client: {exc}",
                kind=PipedreamErrorKind.AUTH_FAILURE,
                raw={"original_error": str(exc)},
            ) from exc

    def safe_call(self, fn, *args, **kwargs) -> Any:
        """Execute a Pipedream SDK call with normalised error handling.

        Catches SDK ``ApiError`` and converts to ``PipedreamError`` with
        the correct ``PipedreamErrorKind``.
        """
        try:
            return fn(*args, **kwargs)
        except Exception as exc:
            status_code = getattr(exc, "status_code", None)
            body = getattr(exc, "body", None)
            if status_code is not None:
                kind = classify_error(status_code, body)
                raise PipedreamError(
                    str(exc), kind=kind, status_code=status_code, raw={"body": body}
                ) from exc
            raise PipedreamError(
                f"Pipedream call failed: {exc}",
                kind=PipedreamErrorKind.UNKNOWN,
                raw={"original_error": str(exc)},
            ) from exc


# ---------------------------------------------------------------------------
# Channel → Pipedream app slug mapping
# ---------------------------------------------------------------------------

# Maps (channel, provider) to the Pipedream app slug used in their API.
PROVIDER_APP_SLUGS: Dict[tuple, str] = {
    # Analytics
    ("analytics", "ga4"): "google_analytics",
    ("analytics", "gsc"): "google_search_console",
    ("analytics", "gbp"): "google_my_business",
    # CMS / Website
    ("website", "wordpress"): "wordpress_org",
    ("website", "shopify"): "shopify",
    ("website", "webflow"): "webflow",
    ("website", "github"): "github",
    ("website", "vercel"): "vercel",
    # Social
    ("social", "facebook"): "facebook_pages",
    ("social", "instagram"): "instagram_business",
    ("social", "linkedin"): "linkedin",
    ("social", "tiktok"): "tiktok_marketing",
    ("social", "youtube"): "youtube_data_api",
    ("social", "x"): "twitter",
    # Email / Lifecycle
    ("email", "mailchimp"): "mailchimp",
    ("email", "loops"): "loops_so",
    ("email", "sendgrid"): "sendgrid",
    # Paid Media
    ("paid_media", "google_ads"): "google_ads",
    ("paid_media", "meta_ads"): "facebook_marketing_api",
    ("paid_media", "linkedin_ads"): "linkedin_ads",
    ("paid_media", "tiktok_ads"): "tiktok_marketing",
    # CRM
    ("email", "hubspot"): "hubspot",
}


def resolve_app_slug(channel: str, provider: str) -> Optional[str]:
    """Look up the Pipedream app slug for a Kai channel+provider pair."""
    return PROVIDER_APP_SLUGS.get((channel, provider))
