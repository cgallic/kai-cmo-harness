"""Execute typed Kai actions through Pipedream Connect.

Translates ActionProposal fields into Pipedream ``actions.run()`` calls
or ``proxy.*`` calls, normalising results back into ``ExecutionResult``.
"""

from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

from .base import (
    PipedreamClient,
    PipedreamError,
    PipedreamErrorKind,
    resolve_app_slug,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Action → Pipedream component mapping
# ---------------------------------------------------------------------------

# Maps (channel, action_type) to a Pipedream component ID and the prop
# names that Kai should populate from ActionProposal.proposed_changes.
# When component_id is None, we fall back to the proxy API.

_ACTION_COMPONENT_MAP: Dict[tuple, Dict[str, Any]] = {
    # Website / CMS — WordPress
    ("website", "update_page_copy"): {
        "component_id": "wordpress_org-update-post",
        "prop_mapping": {
            "post_id": "page_id",
            "content": "new_content",
            "title": "title",
        },
    },
    ("website", "update_metadata"): {
        "component_id": "wordpress_org-update-post",
        "prop_mapping": {
            "post_id": "page_id",
            "meta_input": "metadata",
        },
    },
    # Email — Mailchimp
    ("email", "launch_email_sequence"): {
        "component_id": "mailchimp-create-campaign",
        "prop_mapping": {
            "list_id": "list_id",
            "subject_line": "subject",
            "from_name": "from_name",
        },
    },
    ("email", "send_approved_template"): {
        "component_id": "mailchimp-send-campaign",
        "prop_mapping": {"campaign_id": "campaign_id"},
    },
    # Email — Loops
    ("email", "send_transactional"): {
        "component_id": "loops_so-send-transactional-email",
        "prop_mapping": {
            "transactional_id": "template_id",
            "email": "to_email",
            "data_variables": "variables",
        },
    },
    # Social — Facebook Pages
    ("social", "publish_social_post"): {
        "component_id": "facebook_pages-create-post",
        "prop_mapping": {
            "message": "text",
            "link": "link",
        },
    },
    ("social", "schedule_social_post"): {
        "component_id": "facebook_pages-create-post",
        "prop_mapping": {
            "message": "text",
            "published": "published",
            "scheduled_publish_time": "scheduled_at",
        },
    },
    # Social — LinkedIn
    ("social", "publish_linkedin_post"): {
        "component_id": "linkedin-create-share-update",
        "prop_mapping": {
            "text": "text",
        },
    },
    # Website / Next.js — GitHub-backed (PRs, file updates)
    ("website", "create_pr"): {
        "component_id": "github-create-pull-request",
        "prop_mapping": {
            "repoFullname": "repo",
            "head": "branch",
            "base": "base_branch",
            "title": "title",
            "body": "description",
        },
    },
    ("website", "create_or_update_file"): {
        "component_id": "github-create-or-update-file-contents",
        "prop_mapping": {
            "repoFullname": "repo",
            "path": "file_path",
            "fileContent": "content",
            "commitMessage": "commit_message",
            "branch": "branch",
        },
    },
    # Website — fix CTA / broken link (WordPress component)
    ("website", "update_cta"): {
        "component_id": "wordpress_org-update-post",
        "prop_mapping": {
            "post_id": "page_id",
            "content": "new_content",
        },
    },
    ("website", "fix_broken_link"): {
        "component_id": "wordpress_org-update-post",
        "prop_mapping": {
            "post_id": "page_id",
            "content": "new_content",
        },
    },
    # Email — SendGrid
    ("email", "send_email"): {
        "component_id": "sendgrid-send-email",
        "prop_mapping": {
            "to_email": "to_email",
            "from_email": "from_email",
            "subject": "subject",
            "html_content": "body",
        },
    },
    # Paid media — Google Ads
    ("paid_media", "pause_campaign"): {
        "component_id": "google_ads-update-campaign",
        "prop_mapping": {
            "campaign_id": "campaign_id",
            "status": "status",
        },
    },
    ("paid_media", "adjust_budget"): {
        "component_id": "google_ads-update-campaign",
        "prop_mapping": {
            "campaign_id": "campaign_id",
            "budget_amount_micros": "budget_micros",
        },
    },
    # Paid media — Meta Ads
    ("paid_media", "create_ad_creative"): {
        "component_id": "facebook_marketing_api-create-ad",
        "prop_mapping": {
            "ad_account_id": "ad_account_id",
            "name": "creative_name",
            "creative": "creative_spec",
        },
    },
    # Analytics — GA4 (read-only via proxy)
    ("analytics", "fetch_report"): {
        "component_id": None,  # uses proxy
        "proxy": {
            "method": "POST",
            "url": "https://analyticsdata.googleapis.com/v1beta/{property_id}:runReport",
        },
    },
}


class PipedreamExecutor:
    """Dispatches typed Kai actions through Pipedream.

    Two execution paths:
    1. **Component actions** — ``client.actions.run()`` with pre-built
       Pipedream components (10,000+ available).
    2. **Proxy calls** — ``client.proxy.*`` for arbitrary API requests
       using the user's stored credentials.

    Both paths use the connected account's credentials without ever
    exposing them to Kai.
    """

    def __init__(self, client: Optional[PipedreamClient] = None):
        self._client = client or PipedreamClient()

    @property
    def pd(self):
        return self._client.sdk

    # ------------------------------------------------------------------
    # Main dispatch
    # ------------------------------------------------------------------

    def execute(
        self,
        *,
        brand_id: str,
        channel: str,
        provider: str,
        action_type: str,
        connected_account_id: str,
        proposed_changes: Dict[str, Any],
        dry_run: bool = True,
    ) -> Dict[str, Any]:
        """Execute an action through Pipedream and return a normalised result.

        Parameters
        ----------
        brand_id : str
            Kai brand ID (maps to Pipedream external_user_id).
        channel : str
            Kai channel (website, social, email, paid_media, analytics).
        provider : str
            Kai provider (wordpress, mailchimp, facebook, etc.).
        action_type : str
            The typed action (update_page_copy, publish_social_post, etc.).
        connected_account_id : str
            Pipedream account ID (apn_xxx) for the target service.
        proposed_changes : dict
            The action payload from ActionProposal.proposed_changes.
        dry_run : bool
            When True, log the call but don't execute (default True).

        Returns
        -------
        dict with keys: success, connector_type, method_called,
        response_data, error, duration_ms, dry_run.
        """
        start = time.monotonic()
        mapping = _ACTION_COMPONENT_MAP.get((channel, action_type))
        app_slug = resolve_app_slug(channel, provider) or provider

        if dry_run:
            return self._dry_run_result(
                channel, action_type, provider, proposed_changes, mapping
            )

        try:
            if mapping and mapping.get("component_id"):
                result = self._execute_component(
                    brand_id=brand_id,
                    app_slug=app_slug,
                    connected_account_id=connected_account_id,
                    mapping=mapping,
                    proposed_changes=proposed_changes,
                )
            elif mapping and mapping.get("proxy"):
                result = self._execute_proxy(
                    brand_id=brand_id,
                    connected_account_id=connected_account_id,
                    proxy_spec=mapping["proxy"],
                    proposed_changes=proposed_changes,
                )
            else:
                raise PipedreamError(
                    f"No Pipedream mapping for ({channel}, {action_type})",
                    kind=PipedreamErrorKind.UNSUPPORTED_ACTION,
                )
        except PipedreamError:
            raise
        except Exception as exc:
            raise PipedreamError(
                f"Execution failed: {exc}",
                kind=PipedreamErrorKind.UNKNOWN,
                raw={"original_error": str(exc)},
            ) from exc

        elapsed = (time.monotonic() - start) * 1000
        return {
            "success": True,
            "connector_type": provider,
            "method_called": f"pipedream:{mapping.get('component_id') if mapping else 'proxy'}",
            "response_data": result,
            "error": None,
            "duration_ms": round(elapsed, 2),
            "dry_run": False,
        }

    # ------------------------------------------------------------------
    # Component execution
    # ------------------------------------------------------------------

    def _execute_component(
        self,
        *,
        brand_id: str,
        app_slug: str,
        connected_account_id: str,
        mapping: Dict[str, Any],
        proposed_changes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run a Pipedream pre-built action component."""
        component_id = mapping["component_id"]
        prop_mapping = mapping.get("prop_mapping", {})

        configured_props: Dict[str, Any] = {
            app_slug: {"authProvisionId": connected_account_id},
        }
        for pd_prop, kai_key in prop_mapping.items():
            if kai_key in proposed_changes:
                configured_props[pd_prop] = proposed_changes[kai_key]

        logger.info(
            "Executing Pipedream component %s for brand=%s account=%s",
            component_id, brand_id, connected_account_id,
        )

        response = self._client.safe_call(
            self.pd.actions.run,
            id=component_id,
            external_user_id=brand_id,
            configured_props=configured_props,
        )
        return _response_to_dict(response)

    # ------------------------------------------------------------------
    # Proxy execution
    # ------------------------------------------------------------------

    def _execute_proxy(
        self,
        *,
        brand_id: str,
        connected_account_id: str,
        proxy_spec: Dict[str, Any],
        proposed_changes: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Make an arbitrary API call through Pipedream's proxy."""
        method = proxy_spec.get("method", "GET").upper()
        url_template = proxy_spec["url"]

        url = url_template.format(**proposed_changes)

        proxy_kwargs = {
            "url": url,
            "external_user_id": brand_id,
            "account_id": connected_account_id,
        }

        body = {k: v for k, v in proposed_changes.items() if k not in url_template}

        logger.info(
            "Executing Pipedream proxy %s %s for brand=%s",
            method, url, brand_id,
        )

        if method == "GET":
            response = self._client.safe_call(self.pd.proxy.get, **proxy_kwargs)
        elif method == "POST":
            proxy_kwargs["body"] = body
            response = self._client.safe_call(self.pd.proxy.post, **proxy_kwargs)
        elif method == "PUT":
            proxy_kwargs["body"] = body
            response = self._client.safe_call(self.pd.proxy.put, **proxy_kwargs)
        elif method == "PATCH":
            proxy_kwargs["body"] = body
            response = self._client.safe_call(self.pd.proxy.patch, **proxy_kwargs)
        elif method == "DELETE":
            response = self._client.safe_call(self.pd.proxy.delete, **proxy_kwargs)
        else:
            raise PipedreamError(
                f"Unsupported proxy method: {method}",
                kind=PipedreamErrorKind.UNSUPPORTED_ACTION,
            )

        return _response_to_dict(response)

    # ------------------------------------------------------------------
    # Dry run
    # ------------------------------------------------------------------

    def _dry_run_result(
        self,
        channel: str,
        action_type: str,
        provider: str,
        proposed_changes: Dict[str, Any],
        mapping: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        method = "none"
        if mapping:
            method = mapping.get("component_id") or "proxy"
        return {
            "success": True,
            "connector_type": provider,
            "method_called": f"dry_run:{method}",
            "response_data": {
                "channel": channel,
                "action_type": action_type,
                "proposed_changes": proposed_changes,
                "would_call": method,
            },
            "error": None,
            "duration_ms": 0.0,
            "dry_run": True,
        }

    # ------------------------------------------------------------------
    # Discovery
    # ------------------------------------------------------------------

    def list_supported_actions(self) -> Dict[str, str]:
        """Return a dict of (channel, action_type) → component_id for all mapped actions."""
        return {
            f"{ch}.{at}": m.get("component_id") or "proxy"
            for (ch, at), m in _ACTION_COMPONENT_MAP.items()
        }


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _response_to_dict(response) -> Dict[str, Any]:
    """Normalise a Pipedream SDK response to a plain dict."""
    if isinstance(response, dict):
        return response
    if hasattr(response, "model_dump"):
        return response.model_dump()
    if hasattr(response, "__dict__"):
        return {k: v for k, v in response.__dict__.items() if not k.startswith("_")}
    return {"raw": str(response)}
