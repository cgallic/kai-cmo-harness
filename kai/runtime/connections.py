"""Connection lifecycle manager — connect, verify, reconnect, disconnect.

Orchestrates the full lifecycle of connecting a brand's external accounts
through Pipedream and persisting them in IntegrationRegistry.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .integrations import IntegrationEntry, IntegrationRegistry, _new_id, _utc_now

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages the lifecycle of brand integrations backed by Pipedream.

    Flow:
    1. ``initiate_connection`` — creates IntegrationEntry + Pipedream connect token
    2. ``confirm_connection`` — called after OAuth success webhook, maps account
    3. ``verify_connection`` — checks account health via Pipedream
    4. ``reconnect`` — re-initiates OAuth for an expired/degraded integration
    5. ``disconnect`` — marks integration disconnected, preserves history
    """

    def __init__(
        self,
        registry: Optional[IntegrationRegistry] = None,
        account_manager=None,
    ):
        if registry is None:
            from .integrations import get_default_integration_registry
            registry = get_default_integration_registry()
        self._registry = registry
        self._account_manager = account_manager  # PipedreamAccountManager, lazy-imported

    @property
    def accounts(self):
        """Lazy-load PipedreamAccountManager to avoid import-time SDK dependency."""
        if self._account_manager is None:
            from gateway.adapters.pipedream.accounts import PipedreamAccountManager
            self._account_manager = PipedreamAccountManager()
        return self._account_manager

    # ------------------------------------------------------------------
    # 1. Initiate connection
    # ------------------------------------------------------------------

    def initiate_connection(
        self,
        *,
        brand_id: str,
        channel: str,
        provider: str,
        config: Optional[Dict[str, Any]] = None,
        allowed_origins: Optional[List[str]] = None,
        success_redirect_uri: Optional[str] = None,
        error_redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Start the connection flow for a brand+channel+provider.

        Creates a pending IntegrationEntry and a Pipedream connect token
        for the OAuth flow.

        Returns dict with ``integration_id``, ``connect_token``, and
        ``connect_link_url`` for the frontend to use.
        """
        entry = IntegrationEntry(
            integration_id=_new_id("int"),
            brand_id=brand_id,
            channel=channel,
            provider=provider,
            status="pending_auth",
            config=config or {},
        )
        record = self._registry.register(entry)
        integration_id = record["integration_id"]

        token_result = self.accounts.create_connect_token(
            brand_id,
            allowed_origins=allowed_origins,
            success_redirect_uri=success_redirect_uri,
            error_redirect_uri=error_redirect_uri,
        )

        logger.info(
            "Initiated connection brand=%s channel=%s provider=%s → integration=%s",
            brand_id, channel, provider, integration_id,
        )

        return {
            "integration_id": integration_id,
            "brand_id": brand_id,
            "channel": channel,
            "provider": provider,
            "status": "pending_auth",
            "connect_token": token_result.get("token"),
            "connect_link_url": token_result.get("connect_link_url"),
            "expires_at": token_result.get("expires_at"),
        }

    # ------------------------------------------------------------------
    # 2. Confirm connection (after OAuth success)
    # ------------------------------------------------------------------

    def confirm_connection(
        self,
        *,
        integration_id: str,
        connected_account_id: str,
        external_user_id: Optional[str] = None,
        scopes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Confirm that an OAuth flow completed successfully.

        Called when Pipedream sends a CONNECTION_SUCCESS webhook or when
        the frontend confirms the OAuth callback.

        Maps the Pipedream connected account to the IntegrationEntry and
        discovers capabilities.
        """
        record = self._registry.get(integration_id)
        if not record:
            raise KeyError(f"Integration not found: {integration_id}")

        channel = record.get("channel", "")
        provider = record.get("provider", "")

        capabilities = self._discover_capabilities(channel, provider)

        updated = self._registry.update(
            integration_id,
            status="connected",
            connected_account_id=connected_account_id,
            external_user_id=external_user_id,
            scopes=scopes or [],
            capabilities=capabilities,
            last_verified_at=_utc_now(),
            last_error=None,
        )

        logger.info(
            "Confirmed connection integration=%s account=%s capabilities=%s",
            integration_id, connected_account_id, capabilities,
        )
        return updated

    # ------------------------------------------------------------------
    # 3. Verify connection
    # ------------------------------------------------------------------

    def verify_connection(self, integration_id: str) -> Dict[str, Any]:
        """Verify that a connected integration is still healthy.

        Checks the Pipedream connected account and updates the
        IntegrationEntry status accordingly.

        Returns dict with ``healthy``, ``status``, and ``detail``.
        """
        record = self._registry.get(integration_id)
        if not record:
            raise KeyError(f"Integration not found: {integration_id}")

        acct_id = record.get("connected_account_id")
        if not acct_id:
            self._registry.mark_error(integration_id, "No connected account ID")
            return {
                "integration_id": integration_id,
                "healthy": False,
                "status": "error",
                "detail": "No connected account ID — initiate connection first",
            }

        verification = self.accounts.verify_account(acct_id)
        healthy = verification.get("healthy", False)

        if healthy:
            self._registry.mark_verified(integration_id)
            return {
                "integration_id": integration_id,
                "healthy": True,
                "status": "connected",
                "detail": verification.get("detail", ""),
            }
        else:
            reason = verification.get("detail", "verification failed")
            self._registry.mark_degraded(integration_id, reason)
            return {
                "integration_id": integration_id,
                "healthy": False,
                "status": "degraded",
                "detail": reason,
                "error_kind": verification.get("error_kind"),
            }

    def verify_all(self, brand_id: str) -> List[Dict[str, Any]]:
        """Verify all integrations for a brand."""
        integrations = self._registry.list_for_brand(brand_id)
        results = []
        for integ in integrations:
            iid = integ.get("integration_id", "")
            if integ.get("status") == "disconnected":
                continue
            results.append(self.verify_connection(iid))
        return results

    # ------------------------------------------------------------------
    # 4. Reconnect
    # ------------------------------------------------------------------

    def reconnect(
        self,
        integration_id: str,
        *,
        allowed_origins: Optional[List[str]] = None,
        success_redirect_uri: Optional[str] = None,
        error_redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Re-initiate OAuth for an expired or degraded integration.

        Preserves the existing IntegrationEntry and its history, but
        generates a new connect token for re-authentication.
        """
        record = self._registry.get(integration_id)
        if not record:
            raise KeyError(f"Integration not found: {integration_id}")

        brand_id = record["brand_id"]

        self._registry.update(integration_id, status="pending_auth", last_error=None)

        token_result = self.accounts.create_connect_token(
            brand_id,
            allowed_origins=allowed_origins,
            success_redirect_uri=success_redirect_uri,
            error_redirect_uri=error_redirect_uri,
        )

        logger.info("Reconnect initiated for integration=%s", integration_id)

        return {
            "integration_id": integration_id,
            "brand_id": brand_id,
            "channel": record.get("channel"),
            "provider": record.get("provider"),
            "status": "pending_auth",
            "connect_token": token_result.get("token"),
            "connect_link_url": token_result.get("connect_link_url"),
            "expires_at": token_result.get("expires_at"),
        }

    # ------------------------------------------------------------------
    # 5. Disconnect
    # ------------------------------------------------------------------

    def disconnect(
        self,
        integration_id: str,
        *,
        delete_pipedream_account: bool = False,
    ) -> Dict[str, Any]:
        """Disconnect an integration, preserving history.

        Marks the IntegrationEntry as disconnected.  Optionally deletes
        the Pipedream connected account (irreversible).
        """
        record = self._registry.get(integration_id)
        if not record:
            raise KeyError(f"Integration not found: {integration_id}")

        if delete_pipedream_account:
            acct_id = record.get("connected_account_id")
            if acct_id:
                try:
                    self.accounts.delete_account(acct_id)
                    logger.info("Deleted Pipedream account %s", acct_id)
                except Exception as exc:
                    logger.warning("Failed to delete Pipedream account %s: %s", acct_id, exc)

        updated = self._registry.update(
            integration_id,
            status="disconnected",
            last_error=None,
        )

        logger.info("Disconnected integration=%s", integration_id)
        return updated

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get_connection_status(self, brand_id: str) -> Dict[str, Any]:
        """Return a summary of all connections for a brand.

        Includes health summary, scope summary, and per-integration status.
        """
        health = self._registry.get_health_summary(brand_id)
        scopes = self._registry.get_scope_summary(brand_id)
        integrations = self._registry.list_for_brand(brand_id)

        return {
            "brand_id": brand_id,
            "total_integrations": len(integrations),
            "health": health,
            "scopes": scopes,
            "integrations": integrations,
        }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _discover_capabilities(self, channel: str, provider: str) -> List[str]:
        """Discover what a connected account can do via Pipedream."""
        try:
            caps = self.accounts.get_capabilities(channel, provider)
            capabilities = []
            if caps.get("actions"):
                capabilities.append("write")
            if caps.get("triggers"):
                capabilities.append("read")
            # Add channel-specific defaults
            if channel == "analytics":
                capabilities = ["read"]
            elif channel == "website":
                capabilities = ["read", "write"]
            elif channel == "social":
                capabilities = ["read", "write", "schedule"]
            elif channel == "email":
                capabilities = ["read", "write", "send"]
            elif channel == "paid_media":
                capabilities = ["read", "write", "budget"]
            return capabilities
        except Exception as exc:
            logger.warning("Capability discovery failed for %s/%s: %s", channel, provider, exc)
            return []
