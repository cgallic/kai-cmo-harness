"""Ad platform connectors — uniform interface for campaign management,
bidding, targeting, and analytics across paid advertising platforms.

Provides three connectors:

- ``GoogleAdsConnector`` — Google Ads (Search, Display, Video,
  Performance Max, Shopping)
- ``MetaAdsConnector`` — Meta/Facebook/Instagram Ads
- ``LocalServicesAdsConnector`` — Google Local Services Ads

All connectors share the ``AdPlatformConnector`` abstract base class and
default to **sandbox + dry-run** mode so that no real money is spent
until explicitly opted in.
"""

from __future__ import annotations

from typing import Any, Dict, Type

from .base import (
    AdConnectorConfig,
    AdCreativeSummary,
    AdGroupSummary,
    AdMetrics,
    AdPlatformConnector,
    BudgetStatus,
    CampaignSummary,
    RateLimitState,
    SpendSafetyCheck,
)
from .google_ads import GoogleAdsConnector
from .local_services_ads import LocalServicesAdsConnector
from .meta_ads import MetaAdsConnector

# ---------------------------------------------------------------------------
# Platform registry
# ---------------------------------------------------------------------------

AD_PLATFORM_REGISTRY: Dict[str, Type[AdPlatformConnector]] = {
    "google_ads": GoogleAdsConnector,
    "meta_ads": MetaAdsConnector,
    "local_services_ads": LocalServicesAdsConnector,
}


def get_ad_connector(platform: str, config: dict) -> AdPlatformConnector:
    """Factory function — instantiate an ad connector by platform name.

    Parameters
    ----------
    platform:
        One of ``"google_ads"``, ``"meta_ads"``, ``"local_services_ads"``.
    config:
        Dict of keyword arguments forwarded to ``AdConnectorConfig``.

    Returns
    -------
    AdPlatformConnector
        A concrete connector instance ready for ``connect()``.

    Raises
    ------
    ValueError
        If ``platform`` is not in the registry.
    """
    connector_cls = AD_PLATFORM_REGISTRY.get(platform)
    if connector_cls is None:
        available = ", ".join(sorted(AD_PLATFORM_REGISTRY.keys()))
        raise ValueError(
            f"Unknown ad platform '{platform}'. "
            f"Available platforms: {available}"
        )

    connector_config = AdConnectorConfig(platform=platform, **config)
    return connector_cls(connector_config)


__all__ = [
    # Base class & models
    "AdPlatformConnector",
    "AdConnectorConfig",
    "CampaignSummary",
    "AdGroupSummary",
    "AdCreativeSummary",
    "AdMetrics",
    "BudgetStatus",
    "SpendSafetyCheck",
    "RateLimitState",
    # Concrete connectors
    "GoogleAdsConnector",
    "MetaAdsConnector",
    "LocalServicesAdsConnector",
    # Registry & factory
    "AD_PLATFORM_REGISTRY",
    "get_ad_connector",
]
