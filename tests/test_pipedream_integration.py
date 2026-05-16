"""Tests for Pipedream adapter, connection lifecycle, and execution routing.

Uses mocked Pipedream SDK calls — real API calls require credentials
and are tested via the /connections endpoints in staging.
"""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.runtime.loader import load_workspace_profile


def _with_config(yaml_content: str):
    @contextlib.contextmanager
    def ctx():
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".yaml", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(textwrap.dedent(yaml_content))
            handle.flush()
            previous = os.environ.get("CMO_CONFIG_PATH")
            os.environ["CMO_CONFIG_PATH"] = handle.name
            harness_config._config = None
            load_workspace_profile.cache_clear()
            try:
                yield Path(handle.name)
            finally:
                if previous is None:
                    os.environ.pop("CMO_CONFIG_PATH", None)
                else:
                    os.environ["CMO_CONFIG_PATH"] = previous
                harness_config._config = None
                load_workspace_profile.cache_clear()
                try:
                    os.unlink(handle.name)
                except OSError:
                    pass

    return ctx()


_MINIMAL_YAML = """\
    brand: test-brand
    data_dir: {tmp}
    content_log_path: {tmp}/content_log.csv
"""


# ---------------------------------------------------------------------------
# IntegrationRegistry — new Pipedream fields
# ---------------------------------------------------------------------------


class TestIntegrationRegistryPipedreamFields:
    """Verify the new Pipedream-specific fields on IntegrationEntry."""

    def test_register_with_pipedream_fields(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry

                reg = IntegrationRegistry(base_dir=Path(tmp))
                record = reg.register({
                    "brand_id": "brand_test",
                    "channel": "website",
                    "provider": "wordpress",
                    "connected_account_id": "apn_abc123",
                    "external_user_id": "brand_test",
                    "scopes": ["read", "write"],
                })
                assert record["connected_account_id"] == "apn_abc123"
                assert record["external_user_id"] == "brand_test"
                assert record["scopes"] == ["read", "write"]
                assert record["last_verified_at"] is None
                assert record["last_sync_at"] is None
                assert record["last_error"] is None

    def test_degraded_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry

                reg = IntegrationRegistry(base_dir=Path(tmp))
                record = reg.register({
                    "brand_id": "b1",
                    "channel": "analytics",
                    "provider": "ga4",
                    "status": "connected",
                    "connected_account_id": "apn_x",
                })
                iid = record["integration_id"]
                updated = reg.mark_degraded(iid, "token expired")
                assert updated["status"] == "degraded"
                assert updated["last_error"] == "token expired"

    def test_health_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry

                reg = IntegrationRegistry(base_dir=Path(tmp))
                reg.register({
                    "brand_id": "b1",
                    "channel": "website",
                    "provider": "wordpress",
                    "status": "connected",
                })
                reg.register({
                    "brand_id": "b1",
                    "channel": "analytics",
                    "provider": "ga4",
                    "status": "error",
                    "last_error": "auth expired",
                })
                summary = reg.get_health_summary("b1")
                assert "website" in summary
                assert "analytics" in summary
                assert summary["website"][0]["status"] == "connected"
                assert summary["analytics"][0]["status"] == "error"

    def test_scope_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry

                reg = IntegrationRegistry(base_dir=Path(tmp))
                reg.register({
                    "brand_id": "b1",
                    "channel": "website",
                    "provider": "wordpress",
                    "status": "connected",
                    "capabilities": ["read", "write"],
                })
                scope = reg.get_scope_summary("b1")
                assert "website" in scope["connected"]
                assert "analytics" in scope["missing"]
                assert "social" in scope["missing"]


# ---------------------------------------------------------------------------
# PipedreamClient / base
# ---------------------------------------------------------------------------


class TestPipedreamBase:
    """Test error classification and config."""

    def test_classify_error(self):
        from gateway.adapters.pipedream.base import (
            classify_error,
            PipedreamErrorKind,
        )
        assert classify_error(401) == PipedreamErrorKind.AUTH_FAILURE
        assert classify_error(403) == PipedreamErrorKind.SCOPE_FAILURE
        assert classify_error(429) == PipedreamErrorKind.RATE_LIMIT
        assert classify_error(504) == PipedreamErrorKind.TIMEOUT
        assert classify_error(500) == PipedreamErrorKind.TRANSIENT
        assert classify_error(422) == PipedreamErrorKind.PROVIDER_VALIDATION
        assert classify_error(404) == PipedreamErrorKind.NOT_FOUND

    def test_resolve_app_slug(self):
        from gateway.adapters.pipedream.base import resolve_app_slug
        assert resolve_app_slug("website", "wordpress") == "wordpress_org"
        assert resolve_app_slug("analytics", "ga4") == "google_analytics"
        assert resolve_app_slug("social", "facebook") == "facebook_pages"
        assert resolve_app_slug("email", "loops") == "loops_so"
        assert resolve_app_slug("paid_media", "google_ads") == "google_ads"
        assert resolve_app_slug("unknown", "unknown") is None

    def test_config_from_env(self):
        with patch.dict(os.environ, {
            "PIPEDREAM_CLIENT_ID": "cid",
            "PIPEDREAM_CLIENT_SECRET": "csecret",
            "PIPEDREAM_PROJECT_ID": "proj_123",
            "PIPEDREAM_ENVIRONMENT": "production",
        }):
            from gateway.adapters.pipedream.base import PipedreamConfig
            cfg = PipedreamConfig.from_env()
            assert cfg.client_id == "cid"
            assert cfg.client_secret == "csecret"
            assert cfg.project_id == "proj_123"
            assert cfg.environment == "production"


# ---------------------------------------------------------------------------
# PipedreamExecutor — dry run
# ---------------------------------------------------------------------------


class TestPipedreamExecutorDryRun:
    """Test dry-run execution (no SDK calls)."""

    def test_dry_run_returns_preview(self):
        from gateway.adapters.pipedream.executor import PipedreamExecutor

        executor = PipedreamExecutor(client=MagicMock())
        result = executor.execute(
            brand_id="brand_test",
            channel="website",
            provider="wordpress",
            action_type="update_page_copy",
            connected_account_id="apn_123",
            proposed_changes={"page_id": "42", "new_content": "<p>Hello</p>"},
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True
        assert "wordpress_org-update-post" in result["method_called"]

    def test_dry_run_unsupported_action(self):
        from gateway.adapters.pipedream.executor import PipedreamExecutor

        executor = PipedreamExecutor(client=MagicMock())
        result = executor.execute(
            brand_id="brand_test",
            channel="website",
            provider="wordpress",
            action_type="nonexistent_action",
            connected_account_id="apn_123",
            proposed_changes={},
            dry_run=True,
        )
        assert result["success"] is True
        assert result["dry_run"] is True
        assert "none" in result["method_called"]

    def test_list_supported_actions(self):
        from gateway.adapters.pipedream.executor import PipedreamExecutor
        executor = PipedreamExecutor(client=MagicMock())
        actions = executor.list_supported_actions()
        assert "website.update_page_copy" in actions
        assert "email.launch_email_sequence" in actions
        assert "social.publish_social_post" in actions


# ---------------------------------------------------------------------------
# Channel write prop translation
# ---------------------------------------------------------------------------


class TestPipedreamWriteProps:
    """Verify prop translation for each write path is correct."""

    def _make_executor_with_mock(self):
        from gateway.adapters.pipedream.executor import PipedreamExecutor
        mock_client = MagicMock()
        mock_sdk = MagicMock()
        mock_client.sdk = mock_sdk
        mock_client.safe_call = lambda fn, **kw: fn(**kw)
        mock_client.config = MagicMock()
        mock_sdk.actions.run.return_value = {"status": "ok"}
        executor = PipedreamExecutor(client=mock_client)
        return executor, mock_sdk

    def test_wordpress_write_props(self):
        executor, sdk = self._make_executor_with_mock()
        result = executor.execute(
            brand_id="kaicalls",
            channel="website",
            provider="wordpress",
            action_type="update_page_copy",
            connected_account_id="apn_wp_001",
            proposed_changes={"page_id": "42", "new_content": "<p>New CTA</p>", "title": "About"},
            dry_run=False,
        )
        assert result["success"] is True
        call_kwargs = sdk.actions.run.call_args
        props = call_kwargs.kwargs.get("configured_props", call_kwargs[1].get("configured_props", {}))
        assert props["post_id"] == "42"
        assert props["content"] == "<p>New CTA</p>"
        assert props["title"] == "About"
        assert props["wordpress_org"]["authProvisionId"] == "apn_wp_001"

    def test_mailchimp_write_props(self):
        executor, sdk = self._make_executor_with_mock()
        result = executor.execute(
            brand_id="starrs",
            channel="email",
            provider="mailchimp",
            action_type="launch_email_sequence",
            connected_account_id="apn_mc_001",
            proposed_changes={"list_id": "lst_abc", "subject": "Summer Party!", "from_name": "Starrs"},
            dry_run=False,
        )
        assert result["success"] is True
        call_kwargs = sdk.actions.run.call_args
        props = call_kwargs.kwargs.get("configured_props", call_kwargs[1].get("configured_props", {}))
        assert props["list_id"] == "lst_abc"
        assert props["subject_line"] == "Summer Party!"
        assert props["from_name"] == "Starrs"

    def test_facebook_social_write_props(self):
        executor, sdk = self._make_executor_with_mock()
        result = executor.execute(
            brand_id="starrs",
            channel="social",
            provider="facebook",
            action_type="publish_social_post",
            connected_account_id="apn_fb_001",
            proposed_changes={"text": "Book your party today!", "link": "https://starrsparty.com"},
            dry_run=False,
        )
        assert result["success"] is True
        call_kwargs = sdk.actions.run.call_args
        props = call_kwargs.kwargs.get("configured_props", call_kwargs[1].get("configured_props", {}))
        assert props["message"] == "Book your party today!"
        assert props["link"] == "https://starrsparty.com"
        assert props["facebook_pages"]["authProvisionId"] == "apn_fb_001"

    def test_loops_transactional_write_props(self):
        executor, sdk = self._make_executor_with_mock()
        result = executor.execute(
            brand_id="kaicalls",
            channel="email",
            provider="loops",
            action_type="send_transactional",
            connected_account_id="apn_loops_001",
            proposed_changes={
                "template_id": "tmpl_welcome",
                "to_email": "owner@business.com",
                "variables": {"name": "John"},
            },
            dry_run=False,
        )
        assert result["success"] is True
        call_kwargs = sdk.actions.run.call_args
        props = call_kwargs.kwargs.get("configured_props", call_kwargs[1].get("configured_props", {}))
        assert props["transactional_id"] == "tmpl_welcome"
        assert props["email"] == "owner@business.com"
        assert props["data_variables"] == {"name": "John"}

    def test_linkedin_post_write_props(self):
        executor, sdk = self._make_executor_with_mock()
        result = executor.execute(
            brand_id="kaicalls",
            channel="social",
            provider="linkedin",
            action_type="publish_linkedin_post",
            connected_account_id="apn_li_001",
            proposed_changes={"text": "AI receptionist handles your calls 24/7"},
            dry_run=False,
        )
        assert result["success"] is True
        call_kwargs = sdk.actions.run.call_args
        props = call_kwargs.kwargs.get("configured_props", call_kwargs[1].get("configured_props", {}))
        assert props["text"] == "AI receptionist handles your calls 24/7"

    def test_google_ads_pause_write_props(self):
        executor, sdk = self._make_executor_with_mock()
        result = executor.execute(
            brand_id="kaicalls",
            channel="paid_media",
            provider="google_ads",
            action_type="pause_campaign",
            connected_account_id="apn_gads_001",
            proposed_changes={"campaign_id": "camp_123", "status": "PAUSED"},
            dry_run=False,
        )
        assert result["success"] is True
        call_kwargs = sdk.actions.run.call_args
        props = call_kwargs.kwargs.get("configured_props", call_kwargs[1].get("configured_props", {}))
        assert props["campaign_id"] == "camp_123"
        assert props["status"] == "PAUSED"


# ---------------------------------------------------------------------------
# State sync — staleness
# ---------------------------------------------------------------------------


class TestStateSyncStaleness:
    def test_stale_if_none(self):
        from gateway.adapters.pipedream.state_sync import PipedreamStateSync
        assert PipedreamStateSync.is_stale(None) is True

    def test_stale_if_old(self):
        from gateway.adapters.pipedream.state_sync import PipedreamStateSync
        assert PipedreamStateSync.is_stale("2020-01-01T00:00:00+00:00") is True

    def test_not_stale_if_recent(self):
        from datetime import datetime, timezone
        from gateway.adapters.pipedream.state_sync import PipedreamStateSync
        now = datetime.now(timezone.utc).isoformat()
        assert PipedreamStateSync.is_stale(now) is False


# ---------------------------------------------------------------------------
# Connector health
# ---------------------------------------------------------------------------


class TestConnectorHealth:
    def test_error_classification(self):
        from kai.runtime.connector_health import classify_integration_error
        result = classify_integration_error("auth_failure")
        assert result["category"] == "auth_failure"
        assert result["action_required"] == "reconnect"

    def test_execution_log_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.connector_health import ExecutionLog
                log = ExecutionLog(base_dir=Path(tmp))
                log.append("brand_1", {
                    "action_id": "act_001",
                    "channel": "website",
                    "success": True,
                })
                entries = log.tail("brand_1")
                assert len(entries) == 1
                assert entries[0]["action_id"] == "act_001"
                assert entries[0]["success"] is True
                assert "logged_at" in entries[0]

    def test_execution_log_search(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.connector_health import ExecutionLog
                log = ExecutionLog(base_dir=Path(tmp))
                log.append("b1", {"channel": "website", "success": True, "action_type": "update"})
                log.append("b1", {"channel": "email", "success": False, "action_type": "send"})
                log.append("b1", {"channel": "website", "success": False, "action_type": "update"})

                website_only = log.search("b1", channel="website")
                assert len(website_only) == 2
                failures = log.search("b1", success=False)
                assert len(failures) == 2

    def test_error_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.connector_health import IntegrationErrorHistory
                hist = IntegrationErrorHistory(base_dir=Path(tmp))
                hist.record_error("int_001", "auth_failure", "Token expired")
                hist.record_error("int_001", "rate_limit", "429 returned")
                entries = hist.get_history("int_001")
                assert len(entries) == 2
                assert entries[0]["error_kind"] == "auth_failure"
                assert entries[1]["error_kind"] == "rate_limit"


# ---------------------------------------------------------------------------
# Connection lifecycle (mocked Pipedream)
# ---------------------------------------------------------------------------


class TestConnectionManager:
    def test_initiate_and_confirm(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry
                from kai.runtime.connections import ConnectionManager

                reg = IntegrationRegistry(base_dir=Path(tmp))
                mock_accounts = MagicMock()
                mock_accounts.create_connect_token.return_value = {
                    "token": "ctok_test123",
                    "connect_link_url": "https://pipedream.com/connect?token=ctok_test123",
                    "expires_at": "2026-04-04T00:00:00Z",
                }
                mock_accounts.get_capabilities.return_value = {
                    "actions": [{"id": "wordpress_org-update-post"}],
                    "triggers": [],
                }

                mgr = ConnectionManager(registry=reg, account_manager=mock_accounts)

                # Initiate
                init_result = mgr.initiate_connection(
                    brand_id="kaicalls",
                    channel="website",
                    provider="wordpress",
                )
                assert init_result["status"] == "pending_auth"
                assert init_result["connect_token"] == "ctok_test123"
                iid = init_result["integration_id"]

                # Confirm
                confirmed = mgr.confirm_connection(
                    integration_id=iid,
                    connected_account_id="apn_wp_001",
                    scopes=["read", "write"],
                )
                assert confirmed["status"] == "connected"
                assert confirmed["connected_account_id"] == "apn_wp_001"
                assert confirmed["scopes"] == ["read", "write"]
                assert "write" in confirmed["capabilities"]

    def test_verify_healthy(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry
                from kai.runtime.connections import ConnectionManager

                reg = IntegrationRegistry(base_dir=Path(tmp))
                record = reg.register({
                    "brand_id": "kaicalls",
                    "channel": "website",
                    "provider": "wordpress",
                    "status": "connected",
                    "connected_account_id": "apn_wp_001",
                })
                iid = record["integration_id"]

                mock_accounts = MagicMock()
                mock_accounts.verify_account.return_value = {
                    "healthy": True,
                    "account_id": "apn_wp_001",
                    "detail": "credentials present",
                }
                mgr = ConnectionManager(registry=reg, account_manager=mock_accounts)

                result = mgr.verify_connection(iid)
                assert result["healthy"] is True
                assert result["status"] == "connected"

    def test_disconnect_preserves_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry
                from kai.runtime.connections import ConnectionManager

                reg = IntegrationRegistry(base_dir=Path(tmp))
                record = reg.register({
                    "brand_id": "starrs",
                    "channel": "social",
                    "provider": "facebook",
                    "status": "connected",
                    "connected_account_id": "apn_fb_001",
                })
                iid = record["integration_id"]

                mock_accounts = MagicMock()
                mgr = ConnectionManager(registry=reg, account_manager=mock_accounts)

                disconnected = mgr.disconnect(iid)
                assert disconnected["status"] == "disconnected"
                # History preserved
                reloaded = reg.get(iid)
                assert reloaded["connected_account_id"] == "apn_fb_001"

    def test_reconnect(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.integrations import IntegrationRegistry
                from kai.runtime.connections import ConnectionManager

                reg = IntegrationRegistry(base_dir=Path(tmp))
                record = reg.register({
                    "brand_id": "kaicalls",
                    "channel": "analytics",
                    "provider": "ga4",
                    "status": "degraded",
                    "connected_account_id": "apn_ga_001",
                    "last_error": "token expired",
                })
                iid = record["integration_id"]

                mock_accounts = MagicMock()
                mock_accounts.create_connect_token.return_value = {
                    "token": "ctok_reconnect",
                    "connect_link_url": "https://pipedream.com/connect?token=ctok_reconnect",
                    "expires_at": "2026-04-04T00:00:00Z",
                }
                mgr = ConnectionManager(registry=reg, account_manager=mock_accounts)

                result = mgr.reconnect(iid)
                assert result["status"] == "pending_auth"
                assert result["connect_token"] == "ctok_reconnect"


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------


class TestOnboarding:
    def test_kaicalls_checklist(self):
        from kai.runtime.onboarding import OnboardingFlow
        flow = OnboardingFlow()
        checklist = flow.get_connection_checklist(
            "kaicalls",
            known_client="kaicalls",
        )
        channels = {item["channel"] for item in checklist}
        assert "website" in channels
        assert "analytics" in channels
        required = [item for item in checklist if item["priority"] == "required"]
        assert len(required) >= 3

    def test_starrs_party_checklist(self):
        from kai.runtime.onboarding import OnboardingFlow
        flow = OnboardingFlow()
        checklist = flow.get_connection_checklist(
            "starrs_party",
            known_client="starrs_party",
        )
        channels = {item["channel"] for item in checklist}
        assert "website" in channels
        assert "social" in channels
        # Starrs Party needs both Facebook and Instagram
        providers = {item["provider"] for item in checklist}
        assert "facebook" in providers
        assert "instagram" in providers

    def test_default_local_service_checklist(self):
        from kai.runtime.onboarding import OnboardingFlow
        flow = OnboardingFlow()
        checklist = flow.get_connection_checklist("new_client", archetype="local_service")
        providers = {item["provider"] for item in checklist}
        assert "wordpress" in providers
        assert "ga4" in providers
        assert "gbp" in providers

    def test_default_saas_checklist(self):
        from kai.runtime.onboarding import OnboardingFlow
        flow = OnboardingFlow()
        checklist = flow.get_connection_checklist("new_saas", archetype="saas")
        providers = {item["provider"] for item in checklist}
        assert "wordpress" in providers
        assert "loops" in providers


# ---------------------------------------------------------------------------
# ActionExecutor — Pipedream path preference
# ---------------------------------------------------------------------------


class TestExecutorPipedreamRouting:
    """Verify ActionExecutor routes to Pipedream when connected_account_id exists."""

    def test_prefers_pipedream_when_connected_account_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.actions import ActionStore
                from kai.runtime.integrations import IntegrationRegistry
                from kai.runtime.mandates import MandateLedger
                from kai.runtime.policy import PolicyEngine
                from kai.execution.connector_factory import ConnectorFactory
                from kai.execution.executor import ActionExecutor

                store = ActionStore(base_dir=Path(tmp))
                reg = IntegrationRegistry(base_dir=Path(tmp))
                mandates = MandateLedger(base_dir=Path(tmp))
                factory = ConnectorFactory(credential_store=MagicMock())

                # Register integration WITH connected_account_id
                reg.register({
                    "brand_id": "b1",
                    "channel": "website",
                    "provider": "wordpress",
                    "status": "connected",
                    "connected_account_id": "apn_wp_001",
                })
                mandate = mandates.create({
                    "agent_id": "agent_kai_operator",
                    "brand_id": "b1",
                    "channel": "website",
                    "action_types": ["update_page_copy"],
                    "created_by": "ops@kai.test",
                })
                mandates.approve(mandate["mandate_id"], approved_by="ops@kai.test")

                # Create an approved action
                proposal = store.propose_action({
                    "brand_id": "b1",
                    "channel": "website",
                    "action_type": "update_page_copy",
                    "intent": "Fix CTA text",
                    "proposed_changes": {"page_id": "1", "new_content": "Call now"},
                    "risk_tier": "low",
                    "mandate_id": mandate["mandate_id"],
                })
                action_id = proposal["action_id"]
                store.approve_action(action_id)

                executor = ActionExecutor(
                    action_store=store,
                    integration_registry=reg,
                    connector_factory=factory,
                    mandate_ledger=mandates,
                    dry_run=True,
                )

                # Mock the Pipedream executor
                mock_pd = MagicMock()
                mock_pd.execute.return_value = {
                    "success": True,
                    "method_called": "dry_run:wordpress_org-update-post",
                    "response_data": {"dry_run": True},
                    "error": None,
                    "dry_run": True,
                }

                with patch(
                    "kai.execution.executor._get_pipedream_executor",
                    return_value=mock_pd,
                ):
                    result = executor.execute(action_id)

                assert result.success is True
                assert result.dry_run is True
                mock_pd.execute.assert_called_once()

    def test_falls_back_to_connector_without_account_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            with _with_config(_MINIMAL_YAML.format(tmp=tmp)):
                from kai.runtime.actions import ActionStore
                from kai.runtime.integrations import IntegrationRegistry
                from kai.runtime.mandates import MandateLedger
                from kai.execution.connector_factory import ConnectorFactory
                from kai.execution.executor import ActionExecutor

                store = ActionStore(base_dir=Path(tmp))
                reg = IntegrationRegistry(base_dir=Path(tmp))
                mandates = MandateLedger(base_dir=Path(tmp))
                factory = ConnectorFactory(credential_store=MagicMock())

                # Register WITHOUT connected_account_id
                reg.register({
                    "brand_id": "b1",
                    "channel": "website",
                    "provider": "wordpress",
                    "status": "connected",
                })
                mandate = mandates.create({
                    "agent_id": "agent_kai_operator",
                    "brand_id": "b1",
                    "channel": "website",
                    "action_types": ["update_page_copy"],
                    "created_by": "ops@kai.test",
                })
                mandates.approve(mandate["mandate_id"], approved_by="ops@kai.test")

                proposal = store.propose_action({
                    "brand_id": "b1",
                    "channel": "website",
                    "action_type": "update_page_copy",
                    "intent": "Fix copy",
                    "proposed_changes": {"page_id": "1", "new_content": "Hi"},
                    "risk_tier": "low",
                    "mandate_id": mandate["mandate_id"],
                })
                action_id = proposal["action_id"]
                store.approve_action(action_id)

                mock_connector = MagicMock()
                mock_connector.snapshot_page.return_value = {"html": "<p>old</p>"}
                mock_connector.update_page_section.return_value = {"ok": True}
                factory.create = MagicMock(return_value=mock_connector)

                executor = ActionExecutor(
                    action_store=store,
                    integration_registry=reg,
                    connector_factory=factory,
                    mandate_ledger=mandates,
                    dry_run=True,
                )

                with patch(
                    "kai.execution.executor._get_pipedream_executor",
                    return_value=None,
                ):
                    result = executor.execute(action_id)

                # Falls back to direct connector
                assert result.success is True
                factory.create.assert_called_once()
