"""Tests for runtime agent profile registry and scope checks."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.runtime.agents import AgentRegistry, default_agent_profiles
from kai.runtime.loader import load_workspace_profile
from kai.runtime.models import KaiAgentProfile


def _with_config(yaml_content: str):
    """Context manager that points the runtime at a temp config.yaml."""

    @contextlib.contextmanager
    def ctx():
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False, encoding="utf-8") as handle:
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
  name: "Kai Test Runtime"

products:
  - id: alpha-hvac
    name: "Alpha HVAC"
    description: "Local service business."
"""


def test_agent_registry_create_get_list_update():
    """Agent profiles should be persisted and queryable from local storage."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = AgentRegistry(base_dir=Path(tmpdir) / "runtime")
            created = registry.create(
                KaiAgentProfile(
                    name="Kai SEO Worker",
                    owner="ops@kai.test",
                    purpose="Runs SEO-focused workflows.",
                    workspace_id="kai-test",
                    brand_scope=["alpha-hvac"],
                    workflow_scope=["kai-seo-audit"],
                    tool_scope=["quality_gates"],
                    model="gpt-5.4",
                )
            )

            assert created["agent_id"].startswith("agent_")
            assert created["status"] == "active"

            fetched = registry.get(created["agent_id"])
            assert fetched is not None
            assert fetched["name"] == "Kai SEO Worker"

            listed = registry.list(workspace_id="kai-test")
            assert len(listed) == 1
            assert listed[0]["agent_id"] == created["agent_id"]

            updated = registry.update(created["agent_id"], assurance_level="high")
            assert updated["assurance_level"] == "high"


def test_agent_scope_allows_one_brand_denies_another():
    """Scoped agent should allow its brand and deny others."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = AgentRegistry(base_dir=Path(tmpdir) / "runtime")
            created = registry.create(
                {
                    "name": "Kai Brand Agent",
                    "owner": "ops@kai.test",
                    "purpose": "Brand-specific execution.",
                    "workspace_id": "kai-test",
                    "brand_scope": ["alpha-hvac"],
                    "workflow_scope": ["kai-launch"],
                    "tool_scope": ["content_writer"],
                }
            )

            allowed = registry.check_scope(
                created["agent_id"],
                workspace_id="kai-test",
                brand_id="alpha-hvac",
                workflow_id="kai-launch",
                tool_id="content_writer",
            )
            denied = registry.check_scope(
                created["agent_id"],
                workspace_id="kai-test",
                brand_id="beta-hvac",
                workflow_id="kai-launch",
                tool_id="content_writer",
            )

            assert allowed["allowed"] is True
            assert denied["allowed"] is False
            assert "Brand scope denied" in denied["reason"]


def test_revoked_agent_fails_scope_checks():
    """Revoked agents should fail all scope checks."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = AgentRegistry(base_dir=Path(tmpdir) / "runtime")
            created = registry.create(
                {
                    "name": "Kai Revocable Agent",
                    "owner": "ops@kai.test",
                    "purpose": "Temporary worker.",
                    "workspace_id": "kai-test",
                    "brand_scope": ["*"],
                    "workflow_scope": ["*"],
                    "tool_scope": ["*"],
                }
            )

            revoked = registry.revoke(created["agent_id"], reason="Contract ended")
            result = registry.check_scope(
                created["agent_id"],
                workspace_id="kai-test",
                brand_id="alpha-hvac",
                workflow_id="kai-launch",
                tool_id="content_writer",
            )

            assert revoked["status"] == "revoked"
            assert revoked["revoked_at"] is not None
            assert result["allowed"] is False
            assert "revoked" in result["reason"].lower()


def test_default_agent_profiles_examples_are_available():
    """Default profiles should provide starter examples for docs and fixtures."""
    examples = default_agent_profiles(workspace_id="kai-test")
    assert len(examples) >= 3
    ids = {profile.agent_id for profile in examples}
    assert "agent_kai_operator" in ids
    assert "agent_content_worker" in ids
    assert "agent_connector_watcher" in ids


if __name__ == "__main__":
    test_agent_registry_create_get_list_update()
    test_agent_scope_allows_one_brand_denies_another()
    test_revoked_agent_fails_scope_checks()
    test_default_agent_profiles_examples_are_available()
    print("All agent registry tests passed!")
