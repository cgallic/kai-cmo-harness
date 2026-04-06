"""Connected-account management through Pipedream Connect.

Handles the lifecycle of connecting external service accounts for Kai brands:
create connect tokens, list/verify/delete accounts, and map them back to
IntegrationRegistry entries.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from .base import (
    PipedreamClient,
    PipedreamError,
    PipedreamErrorKind,
    resolve_app_slug,
)

logger = logging.getLogger(__name__)


class PipedreamAccountManager:
    """Manages Pipedream connected accounts for Kai brands.

    Each Kai brand maps to a Pipedream ``external_user_id`` so accounts
    are scoped per business.
    """

    def __init__(self, client: Optional[PipedreamClient] = None):
        self._client = client or PipedreamClient()

    @property
    def pd(self):
        return self._client.sdk

    # ------------------------------------------------------------------
    # Connect tokens (for OAuth flows)
    # ------------------------------------------------------------------

    def create_connect_token(
        self,
        brand_id: str,
        *,
        allowed_origins: Optional[List[str]] = None,
        success_redirect_uri: Optional[str] = None,
        error_redirect_uri: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a short-lived connect token for a brand's OAuth flow.

        Returns dict with ``token``, ``expires_at``, and ``connect_link_url``.
        The frontend (or a Connect Link URL) uses this token to let the
        business owner authorise their accounts.
        """
        kwargs: Dict[str, Any] = {"external_user_id": brand_id}
        if allowed_origins:
            kwargs["allowed_origins"] = allowed_origins
        if success_redirect_uri:
            kwargs["success_redirect_uri"] = success_redirect_uri
        if error_redirect_uri:
            kwargs["error_redirect_uri"] = error_redirect_uri

        webhook_url = self._client.config.webhook_base_url
        if webhook_url:
            kwargs["webhook_uri"] = f"{webhook_url}/pipedream/webhooks/connect"

        result = self._client.safe_call(self.pd.tokens.create, **kwargs)
        return _token_to_dict(result)

    # ------------------------------------------------------------------
    # Account CRUD
    # ------------------------------------------------------------------

    def list_accounts(
        self,
        brand_id: str,
        *,
        app_slug: Optional[str] = None,
        include_credentials: bool = False,
    ) -> List[Dict[str, Any]]:
        """List all Pipedream connected accounts for a brand."""
        kwargs: Dict[str, Any] = {"external_user_id": brand_id}
        if app_slug:
            kwargs["app"] = app_slug
        if include_credentials:
            kwargs["include_credentials"] = True

        result = self._client.safe_call(self.pd.accounts.list, **kwargs)
        return [_account_to_dict(a) for a in result]

    def get_account(
        self,
        account_id: str,
        *,
        include_credentials: bool = False,
    ) -> Dict[str, Any]:
        """Retrieve a single connected account by Pipedream account ID."""
        kwargs: Dict[str, Any] = {}
        if include_credentials:
            kwargs["include_credentials"] = True
        result = self._client.safe_call(
            self.pd.accounts.retrieve, account_id, **kwargs
        )
        return _account_to_dict(result)

    def delete_account(self, account_id: str) -> None:
        """Delete a connected account from Pipedream."""
        self._client.safe_call(self.pd.accounts.delete, account_id)

    def delete_all_for_brand(self, brand_id: str) -> None:
        """Delete ALL connected accounts for a brand (external user).

        Use with extreme caution — this is irreversible.
        """
        self._client.safe_call(
            self.pd.users.delete_external_user, external_user_id=brand_id
        )

    # ------------------------------------------------------------------
    # Account lookup by Kai channel + provider
    # ------------------------------------------------------------------

    def find_account_for_integration(
        self,
        brand_id: str,
        channel: str,
        provider: str,
    ) -> Optional[Dict[str, Any]]:
        """Find the Pipedream connected account matching a Kai integration.

        Returns the first matching account or None.
        """
        app_slug = resolve_app_slug(channel, provider)
        if not app_slug:
            logger.warning(
                "No Pipedream app slug for channel=%s provider=%s", channel, provider
            )
            return None
        accounts = self.list_accounts(brand_id, app_slug=app_slug)
        return accounts[0] if accounts else None

    # ------------------------------------------------------------------
    # Verification
    # ------------------------------------------------------------------

    def verify_account(self, account_id: str) -> Dict[str, Any]:
        """Verify a connected account is still healthy.

        Retrieves the account and checks that it has valid credentials.
        Returns a dict with ``healthy``, ``account_id``, and ``detail``.
        """
        try:
            account = self.get_account(account_id, include_credentials=True)
        except PipedreamError as exc:
            return {
                "healthy": False,
                "account_id": account_id,
                "detail": str(exc),
                "error_kind": exc.kind.value,
            }

        has_creds = bool(account.get("credentials"))
        return {
            "healthy": has_creds,
            "account_id": account_id,
            "app": account.get("app"),
            "detail": "credentials present" if has_creds else "no credentials found",
        }

    def verify_brand_accounts(self, brand_id: str) -> List[Dict[str, Any]]:
        """Verify all connected accounts for a brand."""
        accounts = self.list_accounts(brand_id)
        results = []
        for acct in accounts:
            acct_id = acct.get("id", "")
            if acct_id:
                results.append(self.verify_account(acct_id))
        return results

    # ------------------------------------------------------------------
    # Capability extraction
    # ------------------------------------------------------------------

    def get_capabilities(
        self,
        channel: str,
        provider: str,
    ) -> Dict[str, Any]:
        """Discover what a Pipedream app can do (actions + triggers).

        Returns lists of available action and trigger component IDs.
        """
        app_slug = resolve_app_slug(channel, provider)
        if not app_slug:
            return {"actions": [], "triggers": [], "app_slug": None}

        actions = self._client.safe_call(
            self.pd.actions.list, app=app_slug, limit=100
        )
        triggers = self._client.safe_call(
            self.pd.triggers.list, app=app_slug, limit=100
        )
        return {
            "app_slug": app_slug,
            "actions": [_component_summary(a) for a in actions],
            "triggers": [_component_summary(t) for t in triggers],
        }


# ---------------------------------------------------------------------------
# Helpers — normalise SDK objects to plain dicts
# ---------------------------------------------------------------------------


def _token_to_dict(token_obj) -> Dict[str, Any]:
    """Convert a Pipedream token response to a plain dict."""
    if isinstance(token_obj, dict):
        return token_obj
    return {
        "token": getattr(token_obj, "token", None),
        "expires_at": getattr(token_obj, "expires_at", None),
        "connect_link_url": getattr(token_obj, "connect_link_url", None),
    }


def _account_to_dict(account_obj) -> Dict[str, Any]:
    """Convert a Pipedream account object to a plain dict."""
    if isinstance(account_obj, dict):
        return account_obj
    return {
        "id": getattr(account_obj, "id", None),
        "name": getattr(account_obj, "name", None),
        "app": getattr(account_obj, "app", None),
        "external_user_id": getattr(account_obj, "external_user_id", None),
        "created_at": getattr(account_obj, "created_at", None),
        "updated_at": getattr(account_obj, "updated_at", None),
        "credentials": getattr(account_obj, "credentials", None),
        "healthy": getattr(account_obj, "healthy", None),
    }


def _component_summary(comp_obj) -> Dict[str, Any]:
    """Extract a summary from a Pipedream component (action or trigger)."""
    if isinstance(comp_obj, dict):
        return {
            "id": comp_obj.get("id"),
            "name": comp_obj.get("name"),
            "description": comp_obj.get("description"),
        }
    return {
        "id": getattr(comp_obj, "id", None),
        "name": getattr(comp_obj, "name", None),
        "description": getattr(comp_obj, "description", None),
    }
