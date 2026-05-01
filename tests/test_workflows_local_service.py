"""Tests for the marketing-OS workflow and local-service contracts."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.runtime.actions import ActionStore, derive_operating_state
from kai.runtime.integrations import IntegrationRegistry, is_operational
from kai.runtime.loader import load_workspace_profile
from kai.runtime.local_service import action_from_finding, normalize_snapshot
from kai.runtime.workflows import get_content_format, get_generation_workflow, list_generation_formats
from scripts.content.engine import VALID_FORMATS, _find_bracket_placeholders


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
  name: "Kai Test Runtime"

products:
  - id: truenorth
    name: "TrueNorth HVAC"
    description: "Residential HVAC and emergency repair."
"""


def test_workflow_registry_normalizes_dashboard_and_skill_formats():
    """Dashboard formats and kai-* aliases resolve before the engine runs."""

    assert get_content_format("landing-page") == "landing-page"
    assert get_content_format("kai-landing-page") == "landing-page"
    assert get_content_format("email") == "email-lifecycle"
    assert get_content_format("kai-seo-audit") is None

    workflow = get_generation_workflow("review-response")
    assert workflow is not None
    assert workflow.local_service_asset == "review_response"
    assert "landing-page" in list_generation_formats()
    assert "landing-page" in VALID_FORMATS


def test_bracket_placeholders_are_detected_before_approval():
    """Execution assets cannot ship with leftover template tokens."""

    bad = "Headline: [Company Name] fixes AC fast\nCTA: [Book now]"
    good = "Read [our HVAC guide](https://example.com) before booking."

    assert _find_bracket_placeholders(bad) == ["[Company Name]"]
    assert _find_bracket_placeholders(good) == []


def test_action_operating_state_reaches_verified_and_learned():
    """Actions expose the supervised-autonomy lifecycle without breaking legacy states."""

    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")
            action = store.propose_action(
                {
                    "brand_id": "truenorth",
                    "channel": "calls",
                    "action_type": "setup_kaicalls",
                    "intent": "Capture missed emergency repair calls",
                    "risk_tier": "medium",
                }
            )
            assert action["execution_state"] == "pending"
            assert derive_operating_state(action) == "gated"

            store.approve_action(action["action_id"])
            store.mark_executing(action["action_id"])
            executed = store.mark_completed(
                action["action_id"],
                result_summary={"captured_calls": 3},
            )
            assert derive_operating_state(executed) == "executed"

            verified = store.mark_verified(
                action["action_id"],
                {"metric": "captured_calls", "value": 3, "passed": True},
            )
            assert derive_operating_state(verified) == "verified"

            learned = store.mark_learned(action["action_id"], ["mem_call_cta_1"])
            assert derive_operating_state(learned) == "learned"
            assert learned["memory_writeback_ids"] == ["mem_call_cta_1"]


def test_integration_operational_requires_successful_sync_or_verify():
    """A green badge needs proven health, not just connected auth."""

    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")
            entry = registry.register(
                {
                    "brand_id": "truenorth",
                    "channel": "gbp",
                    "provider": "pipedream_google_business_profile",
                    "status": "connected",
                    "connected_account_id": "ca_123",
                    "capabilities": ["read", "write"],
                }
            )
            assert is_operational(entry) is False

            synced = registry.mark_synced(entry["integration_id"])
            assert is_operational(synced) is True
            health = registry.get_health_summary("truenorth")["gbp"][0]
            assert health["operational"] is True
            assert health["capability_state"]["read_sync_ok"] is True


def test_local_service_finding_becomes_kaicalls_action_and_snapshot():
    """Missed-call findings become typed KaiCalls proposals with verification."""

    finding = {
        "type": "missed_call_risk",
        "title": "Missed calls after hours",
        "description": "43% of inbound calls were missed outside office hours.",
        "recommendation": "Set up KaiCalls to answer and qualify after-hours callers.",
        "evidence": [{"metric": "missed_call_rate", "value": 0.43}],
    }
    action = action_from_finding(finding, brand_id="truenorth", source_run_id="run_1")

    assert action["action_type"] == "setup_kaicalls"
    assert action["channel"] == "calls"
    assert action["proposed_changes"]["workflow_id"] == "call-script"
    assert action["verification_criteria"][0]["metric"] == "missed_call_rate"

    snapshot = normalize_snapshot(
        brand_id="truenorth",
        calls={"missed_call_rate": 0.43},
        integrations=[
            {
                "provider": "pipedream_kaicalls",
                "channel": "calls",
                "connected": True,
                "configured": True,
            }
        ],
    )
    assert snapshot["calls"]["missed_call_rate"] == 0.43
    assert snapshot["integrations"][0]["provider"] == "pipedream_kaicalls"
