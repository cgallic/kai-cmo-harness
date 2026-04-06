"""Social platform connectors — uniform interface for publishing, scheduling, and analytics across social media platforms."""

from __future__ import annotations

from typing import Dict, Type

from .base import (
    AudienceInsights,
    MediaRequirements,
    RateLimitState,
    SocialConnector,
    SocialConnectorConfig,
    SocialMetrics,
    SocialPost,
)
from .facebook import FacebookConnector
from .instagram import InstagramConnector
from .linkedin import LinkedInConnector
from .tiktok import TikTokConnector
from .youtube import YouTubeConnector

# ---------------------------------------------------------------------------
# Platform Registry
# ---------------------------------------------------------------------------

PLATFORM_REGISTRY: Dict[str, Type[SocialConnector]] = {
    "facebook": FacebookConnector,
    "instagram": InstagramConnector,
    "linkedin": LinkedInConnector,
    "tiktok": TikTokConnector,
    "youtube": YouTubeConnector,
}


def get_connector(platform: str, config: dict) -> SocialConnector:
    """Instantiate a social connector by platform name.

    Parameters
    ----------
    platform:
        One of the keys in ``PLATFORM_REGISTRY`` (e.g. ``"facebook"``).
    config:
        A dict of keyword arguments forwarded to
        ``SocialConnectorConfig``.  The ``platform`` field is set
        automatically if not already present.

    Returns
    -------
    SocialConnector
        A ready-to-use (but not yet connected) connector instance.

    Raises
    ------
    ValueError
        If *platform* is not in the registry.
    """
    platform_lower = platform.lower()
    connector_cls = PLATFORM_REGISTRY.get(platform_lower)
    if connector_cls is None:
        available = ", ".join(sorted(PLATFORM_REGISTRY.keys()))
        raise ValueError(
            f"Unknown platform '{platform}'. Available platforms: {available}"
        )

    config.setdefault("platform", platform_lower)
    connector_config = SocialConnectorConfig(**config)
    return connector_cls(connector_config)


__all__ = [
    # Models
    "AudienceInsights",
    "MediaRequirements",
    "RateLimitState",
    "SocialConnector",
    "SocialConnectorConfig",
    "SocialMetrics",
    "SocialPost",
    # Connectors
    "FacebookConnector",
    "InstagramConnector",
    "LinkedInConnector",
    "TikTokConnector",
    "YouTubeConnector",
    # Registry & factory
    "PLATFORM_REGISTRY",
    "get_connector",
]
