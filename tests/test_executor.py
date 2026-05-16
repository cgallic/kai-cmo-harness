"""Tests for ActionExecutor — the bridge between approved actions and connectors."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import scripts.harness_config as harness_config
from kai.runtime.loader import load_workspace_profile
from kai.runtime.actions import ActionStore
from kai.runtime.integrations import IntegrationRegistry
from kai.runtime.mandates import MandateLedger
from kai.runtime.policy import PolicyEngine
from kai.execution.credentials import CredentialStore
from kai.execution.connector_factory import ConnectorFactory
from kai.execution.executor import ActionExecutor
from kai.execution.result import ExecutionResult


# ---------------------------------------------------------------------------
# Config isolation
# ---------------------------------------------------------------------------


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


YAML_CONTENT = """
workspace:
  id: "kai-test"
  name: "Kai Test Executor"
products: []
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_executor(tmp_path, *, dry_run=True, auto_approve=False):
    """Create a fully wired ActionExecutor backed by temp dirs."""
    action_store = ActionStore(base_dir=tmp_path / "runtime", auto_approve_low_risk=auto_approve)
    registry = IntegrationRegistry(base_dir=tmp_path / "runtime")
    mandates = MandateLedger(base_dir=tmp_path / "runtime")
    cred_store = CredentialStore(vault_path=tmp_path / "creds.json")
    factory = ConnectorFactory(cred_store)
    policy = PolicyEngine()
    executor = ActionExecutor(
        action_store=action_store,
        integration_registry=registry,
        connector_factory=factory,
        policy_engine=policy,
        mandate_ledger=mandates,
        dry_run=dry_run,
    )
    return executor, action_store, registry, mandates, cred_store


def _register_wordpress_integration(registry, cred_store, brand_id="testbrand"):
    """Register a connected WordPress integration."""
    cred_store.set_override("wp_test", {
        "site_url": "https://test.example.com",
        "username": "admin",
        "password": "secret",
    })
    return registry.register({
        "brand_id": brand_id,
        "channel": "website",
        "provider": "wordpress",
        "status": "connected",
        "credentials_ref": "wp_test",
        "config": {"site_url": "https://test.example.com"},
        "capabilities": ["read", "write"],
        "last_verified_at": datetime.now(timezone.utc).isoformat(),
    })


# ---------------------------------------------------------------------------
# Tests: Action not found
# ---------------------------------------------------------------------------


class TestExecutorNotFound:
    def test_missing_action_returns_error(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, *_ = _make_executor(tmp_path)
            result = executor.execute("act_nonexistent")
            assert result.success is False
            assert "not found" in result.error


# ---------------------------------------------------------------------------
# Tests: Approval guard
# ---------------------------------------------------------------------------


class TestExecutorApprovalGuard:
    def test_pending_action_rejected(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, _, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Test",
                "proposed_changes": {"page_id": "1", "section_id": "hero", "new_content": "Hello"},
                "risk_tier": "medium",
            })

            result = executor.execute(action["action_id"])
            assert result.success is False
            assert "not approved" in result.error.lower()

    def test_rejected_action_blocked(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, _, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Test",
                "risk_tier": "medium",
            })
            store.reject_action(action["action_id"])

            result = executor.execute(action["action_id"])
            assert result.success is False
            assert "not approved" in result.error.lower()


# ---------------------------------------------------------------------------
# Tests: Integration guard
# ---------------------------------------------------------------------------


class TestExecutorIntegrationGuard:
    def test_no_integration_returns_error(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, *_ = _make_executor(tmp_path)

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_metadata",
                "intent": "Test",
                "proposed_changes": {"page_id": "1", "meta": {"title": "Test"}},
                "risk_tier": "low",
            })
            store.approve_action(action["action_id"])

            result = executor.execute(action["action_id"])
            assert result.success is False
            assert "connector health gate blocked execution" in result.error.lower()

    def test_kill_switch_blocks_execution(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, _, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)
            registry.activate_kill_switch("testbrand", "website")

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_metadata",
                "intent": "Test",
                "proposed_changes": {"page_id": "1", "meta": {"title": "Test"}},
                "risk_tier": "low",
            })
            store.approve_action(action["action_id"])

            result = executor.execute(action["action_id"])
            assert result.success is False
            assert (
                "connector health gate blocked execution" in result.error.lower()
                or "kill switch" in result.error.lower()
            )


class TestExecutorConnectorHealthGate:
    def test_degraded_blocks_high_risk_actions(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, mandates, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            integration = registry.list_for_brand("testbrand", channel="website")[0]
            registry.update(
                integration["integration_id"],
                status="degraded",
                last_error="OAuth token expired",
            )

            mandate = mandates.create({
                "agent_id": "agent_kai_operator",
                "brand_id": "testbrand",
                "channel": "website",
                "action_types": ["update_page_copy"],
                "created_by": "ops@kai.test",
            })
            mandates.approve(mandate["mandate_id"], approved_by="ops@kai.test")

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Update hero headline",
                "proposed_changes": {"page_id": "1", "section_id": "hero", "new_content": "New"},
                "risk_tier": "high",
                "mandate_id": mandate["mandate_id"],
            })
            store.approve_action(action["action_id"])

            executor._factory = MagicMock()
            result = executor.execute(action["action_id"])

            assert result.success is False
            assert "connector health gate blocked execution" in (result.error or "").lower()
            assert "degraded" in (result.error or "").lower()
            executor._factory.create.assert_not_called()

    def test_degraded_allows_low_risk_with_warning(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, _, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)
            integration = registry.list_for_brand("testbrand", channel="website")[0]
            registry.update(
                integration["integration_id"],
                status="degraded",
                last_error="Rate limit encountered",
            )

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_metadata",
                "intent": "Refresh metadata",
                "proposed_changes": {"page_id": "2", "meta": {"title": "Updated"}},
                "risk_tier": "low",
            })
            store.approve_action(action["action_id"])

            mock_connector = MagicMock()
            mock_connector.update_metadata.return_value = {"success": True}
            executor._factory = MagicMock()
            executor._factory.create.return_value = mock_connector

            result = executor.execute(action["action_id"])
            assert result.success is True
            executor._factory.create.assert_called_once()


# ---------------------------------------------------------------------------
# Tests: Successful execution with mock connector
# ---------------------------------------------------------------------------


class TestExecutorSuccess:
    def test_approved_action_executes(self, tmp_path):
        """Full lifecycle: propose -> approve -> execute with mocked connector."""
        with _with_config(YAML_CONTENT):
            executor, store, registry, mandates, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            mandate = mandates.create({
                "agent_id": "agent_kai_operator",
                "brand_id": "testbrand",
                "channel": "website",
                "action_types": ["update_page_copy"],
                "created_by": "ops@kai.test",
            })
            mandates.approve(mandate["mandate_id"], approved_by="ops@kai.test")
            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Update hero headline",
                "proposed_changes": {
                    "page_id": "42",
                    "section_id": "hero",
                    "new_content": "<h1>New Headline</h1>",
                },
                "risk_tier": "medium",
                "mandate_id": mandate["mandate_id"],
            })
            store.approve_action(action["action_id"])

            # Mock the connector factory to return a mock connector
            mock_connector = MagicMock()
            mock_connector.snapshot_page.return_value = {"page_id": "42", "content": "old"}
            mock_connector.update_page_section.return_value = {
                "success": True,
                "page_id": "42",
                "section_id": "hero",
            }
            executor._factory = MagicMock()
            executor._factory.create.return_value = mock_connector

            result = executor.execute(action["action_id"])

            assert result.success is True
            assert result.before_state == {"page_id": "42", "content": "old"}
            assert result.duration_ms >= 0

            # Verify action store was updated
            final = store.get_action(action["action_id"])
            assert final["execution_state"] == "completed"
            assert final["executed_at"] is not None

            # Verify connector was called correctly
            mock_connector.update_page_section.assert_called_once_with(
                page_id="42",
                section_id="hero",
                content="<h1>New Headline</h1>",
                content_type="html",
            )

    def test_auto_approved_executes(self, tmp_path):
        """Auto-approved low-risk actions should execute."""
        with _with_config(YAML_CONTENT):
            executor, store, registry, mandates, cred_store = _make_executor(
                tmp_path, auto_approve=True
            )
            _register_wordpress_integration(registry, cred_store)

            mandate = mandates.create({
                "agent_id": "agent_kai_operator",
                "brand_id": "testbrand",
                "channel": "website",
                "action_types": ["fix_broken_link"],
                "created_by": "ops@kai.test",
            })
            mandates.approve(mandate["mandate_id"], approved_by="ops@kai.test")
            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "fix_broken_link",
                "intent": "Fix broken link on homepage",
                "proposed_changes": {
                    "page_id": "1",
                    "section_id": "footer",
                    "new_content": '<a href="/contact">Contact</a>',
                },
                "risk_tier": "low",
                "mandate_id": mandate["mandate_id"],
            })
            assert action["approval_state"] == "auto_approved"

            mock_connector = MagicMock()
            mock_connector.snapshot_page.return_value = {}
            mock_connector.update_page_section.return_value = {"success": True}
            executor._factory = MagicMock()
            executor._factory.create.return_value = mock_connector

            result = executor.execute(action["action_id"])
            assert result.success is True


# ---------------------------------------------------------------------------
# Tests: Connector failure
# ---------------------------------------------------------------------------


class TestExecutorFailure:
    def test_connector_exception_marks_failed(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, mandates, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            mandate = mandates.create({
                "agent_id": "agent_kai_operator",
                "brand_id": "testbrand",
                "channel": "website",
                "action_types": ["update_page_copy"],
                "created_by": "ops@kai.test",
            })
            mandates.approve(mandate["mandate_id"], approved_by="ops@kai.test")
            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Test",
                "proposed_changes": {"page_id": "1", "section_id": "hero", "new_content": "x"},
                "risk_tier": "medium",
                "mandate_id": mandate["mandate_id"],
            })
            store.approve_action(action["action_id"])

            mock_connector = MagicMock()
            mock_connector.snapshot_page.return_value = {}
            mock_connector.update_page_section.side_effect = ConnectionError("API timeout")
            executor._factory = MagicMock()
            executor._factory.create.return_value = mock_connector

            result = executor.execute(action["action_id"])
            assert result.success is False
            assert "API timeout" in result.error

            final = store.get_action(action["action_id"])
            assert final["execution_state"] == "failed"

    def test_connector_creation_failure(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, mandates, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            mandate = mandates.create({
                "agent_id": "agent_kai_operator",
                "brand_id": "testbrand",
                "channel": "website",
                "action_types": ["update_page_copy"],
                "created_by": "ops@kai.test",
            })
            mandates.approve(mandate["mandate_id"], approved_by="ops@kai.test")
            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Test",
                "proposed_changes": {"page_id": "1", "section_id": "hero", "new_content": "x"},
                "risk_tier": "medium",
                "mandate_id": mandate["mandate_id"],
            })
            store.approve_action(action["action_id"])

            executor._factory = MagicMock()
            executor._factory.create.side_effect = KeyError("bad creds")

            result = executor.execute(action["action_id"])
            assert result.success is False
            assert "bad creds" in result.error

            final = store.get_action(action["action_id"])
            assert final["execution_state"] == "failed"


# ---------------------------------------------------------------------------
# Tests: Batch execution
# ---------------------------------------------------------------------------


class TestExecutorBatch:
    def test_batch_processes_all(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, _, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            ids = []
            for i in range(3):
                action = store.propose_action({
                    "brand_id": "testbrand",
                    "channel": "website",
                    "action_type": "update_metadata",
                    "intent": f"Update meta {i}",
                    "proposed_changes": {"page_id": str(i), "meta": {"title": f"Title {i}"}},
                    "risk_tier": "low",
                })
                store.approve_action(action["action_id"])
                ids.append(action["action_id"])

            mock_connector = MagicMock()
            mock_connector.update_metadata.return_value = {"success": True}
            executor._factory = MagicMock()
            executor._factory.create.return_value = mock_connector

            results = executor.execute_batch(ids)
            assert len(results) == 3
            assert all(r.success for r in results)


class TestExecutorMandates:
    def test_high_risk_action_requires_mandate(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, _, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Update homepage hero copy",
                "proposed_changes": {"page_id": "1", "section_id": "hero", "new_content": "Hello"},
                "risk_tier": "medium",
            })
            store.approve_action(action["action_id"])

            result = executor.execute(action["action_id"])
            assert result.success is False
            assert "mandate validation failed" in (result.error or "").lower()

    def test_low_risk_read_only_action_does_not_require_mandate(self, tmp_path):
        with _with_config(YAML_CONTENT):
            executor, store, registry, _, cred_store = _make_executor(tmp_path)
            _register_wordpress_integration(registry, cred_store)

            action = store.propose_action({
                "brand_id": "testbrand",
                "channel": "website",
                "action_type": "update_metadata",
                "intent": "Refresh metadata tags",
                "proposed_changes": {"page_id": "9", "meta": {"title": "New"}},
                "risk_tier": "low",
            })
            store.approve_action(action["action_id"])

            mock_connector = MagicMock()
            mock_connector.update_metadata.return_value = {"success": True}
            executor._factory = MagicMock()
            executor._factory.create.return_value = mock_connector

            result = executor.execute(action["action_id"])
            assert result.success is True


# ---------------------------------------------------------------------------
# Tests: ExecutionResult
# ---------------------------------------------------------------------------


class TestExecutionResult:
    def test_serializable(self):
        result = ExecutionResult(
            action_id="act_123",
            success=True,
            connector_type="wordpress",
            method_called="update_page_section",
        )
        d = result.model_dump()
        assert d["action_id"] == "act_123"
        assert d["success"] is True
        assert "timestamp" in d
