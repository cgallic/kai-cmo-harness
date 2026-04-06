"""Channel state sync through Pipedream.

Reads the current state of connected external systems and normalises it
into Kai-readable snapshots.  These snapshots feed audits, proposals,
and watchers so Kai can reason about what is actually happening in each
channel before proposing changes.
"""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import (
    PipedreamClient,
    PipedreamError,
    PipedreamErrorKind,
    resolve_app_slug,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Sync specs — what to read per channel
# ---------------------------------------------------------------------------

# Each spec defines what Pipedream component or proxy call to use for
# reading state from a channel.  The ``normalise`` key names a function
# that converts the raw response into a Kai-standard snapshot dict.

_SYNC_SPECS: Dict[str, Dict[str, Any]] = {
    "analytics_ga4": {
        "label": "Google Analytics overview",
        "component_id": None,
        "proxy": {
            "method": "POST",
            "url": "https://analyticsdata.googleapis.com/v1beta/{property_id}:runReport",
        },
        "default_body": {
            "dateRanges": [{"startDate": "28daysAgo", "endDate": "today"}],
            "metrics": [
                {"name": "sessions"},
                {"name": "totalUsers"},
                {"name": "bounceRate"},
                {"name": "averageSessionDuration"},
                {"name": "screenPageViews"},
            ],
        },
    },
    "analytics_gsc": {
        "label": "Search Console performance",
        "component_id": None,
        "proxy": {
            "method": "POST",
            "url": "https://searchconsole.googleapis.com/webmasters/v3/sites/{site_url}/searchAnalytics/query",
        },
        "default_body": {
            "startDate": None,  # filled at runtime
            "endDate": None,
            "dimensions": ["query", "page"],
            "rowLimit": 100,
        },
    },
    "website_wordpress": {
        "label": "WordPress pages and posts",
        "component_id": "wordpress_org-get-all-posts",
        "prop_mapping": {"status": "status", "per_page": "per_page"},
    },
    "social_facebook": {
        "label": "Facebook Page insights",
        "component_id": None,
        "proxy": {
            "method": "GET",
            "url": "https://graph.facebook.com/v21.0/{page_id}/insights?metric=page_impressions,page_engaged_users,page_fans&period=day&date_preset=last_28d",
        },
    },
    "social_instagram": {
        "label": "Instagram business insights",
        "component_id": None,
        "proxy": {
            "method": "GET",
            "url": "https://graph.facebook.com/v21.0/{ig_user_id}/insights?metric=impressions,reach,profile_views&period=day&timeframe=last_28_days",
        },
    },
    "email_mailchimp": {
        "label": "Mailchimp audience and campaign stats",
        "component_id": "mailchimp-get-lists",
        "prop_mapping": {},
    },
    "email_loops": {
        "label": "Loops contacts and events",
        "component_id": None,
        "proxy": {
            "method": "GET",
            "url": "https://app.loops.so/api/v1/contacts?limit=100",
        },
    },
    "paid_media_google_ads": {
        "label": "Google Ads campaign summary",
        "component_id": None,
        "proxy": {
            "method": "POST",
            "url": "https://googleads.googleapis.com/v18/customers/{customer_id}/googleAds:searchStream",
        },
        "default_body": {
            "query": (
                "SELECT campaign.name, campaign.status, "
                "metrics.impressions, metrics.clicks, metrics.cost_micros "
                "FROM campaign WHERE segments.date DURING LAST_30_DAYS"
            ),
        },
    },
}


class PipedreamStateSync:
    """Reads channel state from external systems via Pipedream.

    Produces normalised state snapshots that can be persisted into
    IntegrationRegistry metadata or fed directly into audits and watchers.
    """

    def __init__(self, client: Optional[PipedreamClient] = None):
        self._client = client or PipedreamClient()

    @property
    def pd(self):
        return self._client.sdk

    # ------------------------------------------------------------------
    # Sync a single channel
    # ------------------------------------------------------------------

    def sync_channel(
        self,
        *,
        brand_id: str,
        channel: str,
        provider: str,
        connected_account_id: str,
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Sync state for one channel+provider and return a normalised snapshot.

        Parameters
        ----------
        brand_id : str
            Kai brand (maps to Pipedream external_user_id).
        channel : str
            Kai channel name.
        provider : str
            Kai provider name.
        connected_account_id : str
            Pipedream connected account ID.
        config : dict, optional
            Provider-specific config overrides (property_id, site_url, etc.).

        Returns
        -------
        dict with ``channel``, ``provider``, ``synced_at``, ``stale`` (bool),
        ``data`` (the normalised snapshot), and ``error`` (if any).
        """
        spec_key = f"{channel}_{provider}"
        spec = _SYNC_SPECS.get(spec_key)
        config = config or {}
        start = time.monotonic()

        if not spec:
            return self._sync_result(
                channel, provider,
                error=f"No sync spec for {spec_key}",
                duration_ms=0.0,
            )

        try:
            if spec.get("component_id"):
                data = self._sync_via_component(
                    brand_id=brand_id,
                    provider=provider,
                    connected_account_id=connected_account_id,
                    spec=spec,
                    config=config,
                )
            elif spec.get("proxy"):
                data = self._sync_via_proxy(
                    brand_id=brand_id,
                    connected_account_id=connected_account_id,
                    spec=spec,
                    config=config,
                )
            else:
                data = {}
        except PipedreamError as exc:
            elapsed = (time.monotonic() - start) * 1000
            return self._sync_result(
                channel, provider,
                error=str(exc),
                error_kind=exc.kind.value,
                duration_ms=elapsed,
            )

        elapsed = (time.monotonic() - start) * 1000
        return self._sync_result(channel, provider, data=data, duration_ms=elapsed)

    # ------------------------------------------------------------------
    # Sync all channels for a brand
    # ------------------------------------------------------------------

    def sync_all(
        self,
        brand_id: str,
        integrations: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """Sync all connected integrations for a brand.

        Parameters
        ----------
        brand_id : str
        integrations : list of dict
            Integration records from IntegrationRegistry.list_for_brand().

        Returns list of sync results.
        """
        results = []
        for integ in integrations:
            if integ.get("status") not in ("connected", "degraded"):
                continue
            acct_id = integ.get("connected_account_id")
            if not acct_id:
                continue
            result = self.sync_channel(
                brand_id=brand_id,
                channel=integ.get("channel", ""),
                provider=integ.get("provider", ""),
                connected_account_id=acct_id,
                config=integ.get("config", {}),
            )
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Staleness detection
    # ------------------------------------------------------------------

    @staticmethod
    def is_stale(last_sync_at: Optional[str], max_age_hours: int = 24) -> bool:
        """Return True if the last sync is older than max_age_hours."""
        if not last_sync_at:
            return True
        try:
            last = datetime.fromisoformat(last_sync_at)
            if last.tzinfo is None:
                last = last.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - last
            return age.total_seconds() > max_age_hours * 3600
        except (ValueError, TypeError):
            return True

    # ------------------------------------------------------------------
    # Internal — component sync
    # ------------------------------------------------------------------

    def _sync_via_component(
        self,
        *,
        brand_id: str,
        provider: str,
        connected_account_id: str,
        spec: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        app_slug = resolve_app_slug(spec.get("channel", ""), provider) or provider
        component_id = spec["component_id"]
        prop_mapping = spec.get("prop_mapping", {})

        configured_props: Dict[str, Any] = {
            app_slug: {"authProvisionId": connected_account_id},
        }
        for pd_prop, cfg_key in prop_mapping.items():
            if cfg_key in config:
                configured_props[pd_prop] = config[cfg_key]

        response = self._client.safe_call(
            self.pd.actions.run,
            id=component_id,
            external_user_id=brand_id,
            configured_props=configured_props,
        )
        return _to_dict(response)

    # ------------------------------------------------------------------
    # Internal — proxy sync
    # ------------------------------------------------------------------

    def _sync_via_proxy(
        self,
        *,
        brand_id: str,
        connected_account_id: str,
        spec: Dict[str, Any],
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        proxy_spec = spec["proxy"]
        method = proxy_spec.get("method", "GET").upper()
        url = proxy_spec["url"].format(**config)

        proxy_kwargs: Dict[str, Any] = {
            "url": url,
            "external_user_id": brand_id,
            "account_id": connected_account_id,
        }

        if method in ("POST", "PUT", "PATCH"):
            body = dict(spec.get("default_body", {}))
            body.update({k: v for k, v in config.items() if k not in url})
            proxy_kwargs["body"] = body

        proxy_fn = {
            "GET": self.pd.proxy.get,
            "POST": self.pd.proxy.post,
            "PUT": self.pd.proxy.put,
            "PATCH": self.pd.proxy.patch,
            "DELETE": self.pd.proxy.delete,
        }.get(method)

        if not proxy_fn:
            raise PipedreamError(
                f"Unsupported sync method: {method}",
                kind=PipedreamErrorKind.UNSUPPORTED_ACTION,
            )

        response = self._client.safe_call(proxy_fn, **proxy_kwargs)
        return _to_dict(response)

    # ------------------------------------------------------------------
    # Result builder
    # ------------------------------------------------------------------

    @staticmethod
    def _sync_result(
        channel: str,
        provider: str,
        *,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        error_kind: Optional[str] = None,
        duration_ms: float = 0.0,
    ) -> Dict[str, Any]:
        return {
            "channel": channel,
            "provider": provider,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "stale": False,
            "data": data or {},
            "error": error,
            "error_kind": error_kind,
            "duration_ms": round(duration_ms, 2),
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_dict(obj) -> Dict[str, Any]:
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return {"raw": str(obj)}
