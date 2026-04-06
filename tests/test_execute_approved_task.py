"""Tests for ExecuteApprovedActionsTask — mock executor, verify queue processing."""

from __future__ import annotations

import asyncio
import contextlib
import os
import sys
import tempfile
import textwrap
from pathlib import Path
from unittest.mock import MagicMock, patch, AsyncMock

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest
import scripts.harness_config as harness_config
from kai.runtime.loader import load_workspace_profile
from kai.runtime.actions import ActionStore
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
  name: "Kai Test Task"
products: []
"""


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestExecuteApprovedTask:
    def test_task_type(self):
        from agent.tasks.execute_approved import ExecuteApprovedActionsTask
        task = ExecuteApprovedActionsTask()
        assert task.task_type == "execute_approved_actions"

    def test_no_pending_actions_succeeds(self, tmp_path):
        """When no actions are pending, the task reports success with 0 processed."""
        with _with_config(YAML_CONTENT):
            from agent.tasks.execute_approved import ExecuteApprovedActionsTask

            task_handler = ExecuteApprovedActionsTask()
            mock_scheduled = MagicMock()

            # Mock all the imports inside execute()
            mock_store = MagicMock(spec=ActionStore)
            mock_store.list_actions.return_value = []

            with patch("kai.runtime.actions.ActionStore", return_value=mock_store), \
                 patch("kai.runtime.integrations.IntegrationRegistry"), \
                 patch("kai.execution.credentials.CredentialStore"), \
                 patch("kai.execution.connector_factory.ConnectorFactory"), \
                 patch("kai.runtime.policy.PolicyEngine"), \
                 patch("kai.execution.executor.ActionExecutor"):

                result = asyncio.run(task_handler.execute(mock_scheduled))

            assert result["success"] is True
            assert result["processed"] == 0

    def test_processes_approved_actions(self, tmp_path):
        """When actions are approved, the task executes them."""
        with _with_config(YAML_CONTENT):
            from agent.tasks.execute_approved import ExecuteApprovedActionsTask

            task_handler = ExecuteApprovedActionsTask()
            mock_scheduled = MagicMock()

            mock_store = MagicMock()
            mock_store.list_actions.side_effect = [
                [{"action_id": "act_1"}, {"action_id": "act_2"}],  # approved
                [],  # auto_approved
            ]

            mock_executor = MagicMock()
            mock_executor.execute.return_value = ExecutionResult(
                action_id="act_1", success=True, connector_type="wordpress"
            )

            with patch("kai.runtime.actions.ActionStore", return_value=mock_store), \
                 patch("kai.runtime.integrations.IntegrationRegistry"), \
                 patch("kai.execution.credentials.CredentialStore"), \
                 patch("kai.execution.connector_factory.ConnectorFactory"), \
                 patch("kai.runtime.policy.PolicyEngine"), \
                 patch("kai.execution.executor.ActionExecutor", return_value=mock_executor):

                result = asyncio.run(task_handler.execute(mock_scheduled, notify=False))

            assert result["processed"] == 2
            assert result["succeeded"] == 2
            assert result["failed"] == 0

    def test_reports_failures(self, tmp_path):
        """When an action fails, it's counted and reported."""
        with _with_config(YAML_CONTENT):
            from agent.tasks.execute_approved import ExecuteApprovedActionsTask

            task_handler = ExecuteApprovedActionsTask()
            mock_scheduled = MagicMock()

            mock_store = MagicMock()
            mock_store.list_actions.side_effect = [
                [{"action_id": "act_fail"}],  # approved
                [],  # auto_approved
            ]

            mock_executor = MagicMock()
            mock_executor.execute.return_value = ExecutionResult(
                action_id="act_fail", success=False, error="API timeout"
            )

            with patch("kai.runtime.actions.ActionStore", return_value=mock_store), \
                 patch("kai.runtime.integrations.IntegrationRegistry"), \
                 patch("kai.execution.credentials.CredentialStore"), \
                 patch("kai.execution.connector_factory.ConnectorFactory"), \
                 patch("kai.runtime.policy.PolicyEngine"), \
                 patch("kai.execution.executor.ActionExecutor", return_value=mock_executor):

                result = asyncio.run(task_handler.execute(mock_scheduled, notify=False))

            assert result["processed"] == 1
            assert result["succeeded"] == 0
            assert result["failed"] == 1
            assert "act_fail" in result["errors"][0]


class TestConnectorHealthTask:
    def test_task_type(self):
        from agent.tasks.connector_health import ConnectorHealthCheckTask
        task = ConnectorHealthCheckTask()
        assert task.task_type == "connector_health_check"
