"""Connector factory — creates connector instances from IntegrationEntry records.

Maps ``(channel, provider)`` pairs to connector classes and constructs them
with resolved credentials from the CredentialStore.
"""

from __future__ import annotations

import importlib
import logging
from typing import Any, Dict, Tuple, Type

from .credentials import CredentialStore

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Registry: (channel, provider) -> (module_path, class_name)
# ---------------------------------------------------------------------------

_CONNECTOR_REGISTRY: Dict[Tuple[str, str], Tuple[str, str]] = {
    # Analytics
    ("analytics", "ga4"): ("kai.connectors.analytics.ga4", "GA4Connector"),
    ("analytics", "gsc"): ("kai.connectors.analytics.gsc", "GSCConnector"),
    ("analytics", "gbp"): ("kai.connectors.analytics.gbp", "GBPConnector"),
    ("analytics", "call_tracking"): ("kai.connectors.analytics.call_tracking", "CallTrackingConnector"),
    # CMS
    ("website", "wordpress"): ("kai.connectors.cms.wordpress", "WordPressConnector"),
    ("website", "shopify"): ("kai.connectors.cms.shopify", "ShopifyConnector"),
    ("website", "webflow"): ("kai.connectors.cms.webflow", "WebflowConnector"),
    ("website", "static"): ("kai.connectors.cms.static_site", "StaticSiteConnector"),
    # Ads
    ("paid_media", "google_ads"): ("kai.connectors.ads.google_ads", "GoogleAdsConnector"),
    ("paid_media", "meta_ads"): ("kai.connectors.ads.meta_ads", "MetaAdsConnector"),
    ("paid_media", "local_services_ads"): ("kai.connectors.ads.local_services_ads", "LocalServicesAdsConnector"),
    # Lifecycle
    ("email", "mailchimp"): ("kai.connectors.lifecycle.mailchimp", "MailchimpConnector"),
    ("email", "loops"): ("kai.connectors.lifecycle.loops", "LoopsConnector"),
    ("email", "sendgrid"): ("kai.connectors.lifecycle.sendgrid", "SendGridConnector"),
    # Social
    ("social", "facebook"): ("kai.connectors.social.facebook", "FacebookConnector"),
    ("social", "instagram"): ("kai.connectors.social.instagram", "InstagramConnector"),
    ("social", "tiktok"): ("kai.connectors.social.tiktok", "TikTokConnector"),
    ("social", "linkedin"): ("kai.connectors.social.linkedin", "LinkedInConnector"),
    ("social", "youtube"): ("kai.connectors.social.youtube", "YouTubeConnector"),
}


def _import_class(module_path: str, class_name: str) -> Type:
    """Dynamically import a connector class."""
    module = importlib.import_module(module_path)
    return getattr(module, class_name)


# ---------------------------------------------------------------------------
# Config builders per connector family
# ---------------------------------------------------------------------------


def _build_analytics_config(credentials: Dict[str, Any], integration: Dict[str, Any]) -> Any:
    """Build a ConnectorConfig for analytics connectors."""
    from kai.connectors.analytics.base import ConnectorConfig

    return ConnectorConfig(
        connector_type=integration.get("provider", ""),
        credentials=credentials,
        property_id=integration.get("config", {}).get("property_id", ""),
        enabled=True,
        metadata=integration.get("config", {}),
    )


def _build_cms_config(
    credentials: Dict[str, Any], integration: Dict[str, Any], *, read_only: bool = False
) -> Dict[str, Any]:
    """Build a config dict for CMS connectors (they accept a plain dict)."""
    int_config = integration.get("config", {})
    return {
        "site_url": credentials.get("site_url", int_config.get("site_url", "")),
        "username": credentials.get("username", ""),
        "password": credentials.get("password", ""),
        "api_base": credentials.get("api_base", int_config.get("api_base", "/wp-json/wp/v2")),
        "auth_type": credentials.get("auth_type", "application_password"),
        "verify_ssl": credentials.get("verify_ssl", True),
        "read_only": read_only,
        **{k: v for k, v in int_config.items() if k not in ("site_url", "api_base")},
    }


def _build_ads_config(credentials: Dict[str, Any], integration: Dict[str, Any]) -> Any:
    """Build an AdConnectorConfig for ad platform connectors."""
    from kai.connectors.ads.base import AdConnectorConfig

    int_config = integration.get("config", {})
    return AdConnectorConfig(
        platform=integration.get("provider", ""),
        api_key=credentials.get("api_key"),
        api_secret=credentials.get("api_secret"),
        access_token=credentials.get("access_token"),
        refresh_token=credentials.get("refresh_token"),
        account_id=credentials.get("account_id", int_config.get("account_id", "")),
        manager_account_id=credentials.get("manager_account_id"),
        sandbox_mode=int_config.get("sandbox_mode", True),
        dry_run=int_config.get("dry_run", True),
        max_daily_spend_usd=int_config.get("max_daily_spend_usd"),
        max_monthly_spend_usd=int_config.get("max_monthly_spend_usd"),
        metadata=int_config,
    )


def _build_lifecycle_config(credentials: Dict[str, Any], integration: Dict[str, Any]) -> Any:
    """Build a LifecycleConnectorConfig for email/lifecycle connectors."""
    from kai.connectors.lifecycle.base import LifecycleConnectorConfig

    int_config = integration.get("config", {})
    return LifecycleConnectorConfig(
        provider=integration.get("provider", ""),
        api_key=credentials.get("api_key"),
        api_secret=credentials.get("api_secret"),
        access_token=credentials.get("access_token"),
        from_email=credentials.get("from_email", int_config.get("from_email", "")),
        from_name=credentials.get("from_name", int_config.get("from_name", "")),
        reply_to=credentials.get("reply_to", int_config.get("reply_to")),
        physical_address=credentials.get("physical_address", int_config.get("physical_address", "")),
        sandbox_mode=int_config.get("sandbox_mode", True),
        metadata=int_config,
    )


def _build_social_config(credentials: Dict[str, Any], integration: Dict[str, Any]) -> Any:
    """Build a SocialConnectorConfig for social platform connectors."""
    from kai.connectors.social.base import SocialConnectorConfig

    int_config = integration.get("config", {})
    return SocialConnectorConfig(
        platform=integration.get("provider", ""),
        api_key=credentials.get("api_key"),
        api_secret=credentials.get("api_secret"),
        access_token=credentials.get("access_token"),
        refresh_token=credentials.get("refresh_token"),
        page_id=credentials.get("page_id", int_config.get("page_id")),
        sandbox_mode=int_config.get("sandbox_mode", True),
        metadata=int_config,
    )


# Map channel -> config builder
_CONFIG_BUILDERS = {
    "analytics": _build_analytics_config,
    "website": _build_cms_config,
    "paid_media": _build_ads_config,
    "email": _build_lifecycle_config,
    "social": _build_social_config,
}


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


class ConnectorFactory:
    """Creates connector instances from IntegrationEntry dicts.

    Parameters
    ----------
    credential_store : CredentialStore
        Resolves ``credentials_ref`` to usable credential dicts.
    """

    def __init__(self, credential_store: CredentialStore) -> None:
        self._credential_store = credential_store

    def create(self, integration: Dict[str, Any], *, read_only: bool = False) -> Any:
        """Create a connector from an IntegrationEntry dict.

        Steps:
            1. Look up the connector class from registry using (channel, provider).
            2. Resolve credentials from credential store using credentials_ref.
            3. Build the connector-specific config.
            4. Instantiate and return.

        Parameters
        ----------
        integration : dict
            A dict with at least: channel, provider, credentials_ref, config.
        read_only : bool
            Force the connector into read-only mode (CMS only).

        Returns
        -------
        connector
            An instantiated connector.

        Raises
        ------
        KeyError
            If (channel, provider) is not in the registry or credentials_ref
            cannot be resolved.
        """
        channel = integration.get("channel", "")
        provider = integration.get("provider", "")
        key = (channel, provider)

        if key not in _CONNECTOR_REGISTRY:
            raise KeyError(
                f"No connector registered for ({channel!r}, {provider!r}). "
                f"Available: {sorted(_CONNECTOR_REGISTRY.keys())}"
            )

        module_path, class_name = _CONNECTOR_REGISTRY[key]
        connector_cls = _import_class(module_path, class_name)

        # Resolve credentials
        cred_ref = integration.get("credentials_ref")
        credentials = self._credential_store.resolve(cred_ref) if cred_ref else {}

        # Build config using the appropriate builder
        builder = _CONFIG_BUILDERS.get(channel)
        if builder is None:
            raise KeyError(f"No config builder for channel {channel!r}")

        if channel == "website":
            config = builder(credentials, integration, read_only=read_only)
            return connector_cls(config, read_only=read_only)

        config = builder(credentials, integration)
        return connector_cls(config)

    def create_read_only(self, integration: Dict[str, Any]) -> Any:
        """Create a connector in read-only mode (for observation)."""
        return self.create(integration, read_only=True)

    @staticmethod
    def list_supported() -> list:
        """Return all supported (channel, provider) pairs."""
        return sorted(_CONNECTOR_REGISTRY.keys())
