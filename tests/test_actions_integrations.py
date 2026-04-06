"""Tests for ActionStore and IntegrationRegistry."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.runtime.loader import load_workspace_profile
from kai.runtime.actions import ActionStore, ActionProposal
from kai.runtime.integrations import IntegrationRegistry, IntegrationEntry


def _with_config(yaml_content: str):
    """Context manager that points the runtime at a temp config.yaml."""

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
  - id: glowcraft
    name: "GlowCraft"
    description: "DTC skincare ecommerce brand."
    proof_points: |
      - 4.8 star average
"""


# -----------------------------------------------------------------------
# ActionStore tests
# -----------------------------------------------------------------------


def test_action_proposal_lifecycle_full():
    """Propose -> approve -> execute -> complete lifecycle."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            action = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Update hero headline on homepage",
                "proposed_changes": {"page": "/", "field": "hero_headline", "new_value": "Glow from within"},
                "risk_tier": "medium",
            })

            assert action["action_id"].startswith("act_")
            assert action["approval_state"] == "pending"
            assert action["execution_state"] == "pending"

            # Approve
            approved = store.approve_action(action["action_id"], note="Looks good")
            assert approved["approval_state"] == "approved"
            assert approved["metadata"]["approval_note"] == "Looks good"

            # Mark executing
            executing = store.mark_executing(action["action_id"])
            assert executing["execution_state"] == "executing"

            # Mark completed
            completed = store.mark_completed(
                action["action_id"],
                result_summary={"status": "success", "page_updated": True},
            )
            assert completed["execution_state"] == "completed"
            assert completed["result_summary"]["status"] == "success"
            assert completed["executed_at"] is not None


def test_action_rejection_and_hold():
    """Reject and hold state transitions."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            # Test hold
            action1 = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "paid_media",
                "action_type": "adjust_budget",
                "intent": "Increase Meta ad budget by 50%",
                "risk_tier": "high",
            })
            held = store.hold_action(action1["action_id"], note="Need CFO sign-off")
            assert held["approval_state"] == "held"
            assert held["metadata"]["hold_note"] == "Need CFO sign-off"

            # Held action can be approved
            approved = store.approve_action(action1["action_id"])
            assert approved["approval_state"] == "approved"

            # Test reject
            action2 = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "email",
                "action_type": "send_broadcast",
                "intent": "Send flash sale email to entire list",
                "risk_tier": "high",
            })
            rejected = store.reject_action(action2["action_id"], note="Too aggressive")
            assert rejected["approval_state"] == "rejected"
            assert rejected["metadata"]["rejection_note"] == "Too aggressive"

            # Rejected action cannot be approved
            try:
                store.approve_action(action2["action_id"])
                assert False, "Should have raised ValueError"
            except ValueError:
                pass


def test_auto_approval_low_risk():
    """Low-risk actions are auto-approved when the flag is enabled."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(
                base_dir=Path(tmpdir) / "runtime",
                auto_approve_low_risk=True,
            )

            low_risk = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "analytics",
                "action_type": "update_tracking",
                "intent": "Add UTM parameter to landing page link",
                "risk_tier": "low",
            })
            assert low_risk["approval_state"] == "auto_approved"

            # Auto-approved action can be executed directly
            executing = store.mark_executing(low_risk["action_id"])
            assert executing["execution_state"] == "executing"

            # Medium-risk action should still be pending
            medium_risk = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Rewrite pricing page",
                "risk_tier": "medium",
            })
            assert medium_risk["approval_state"] == "pending"


def test_auto_approval_disabled_by_default():
    """Without the flag, low-risk actions are pending."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            action = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "analytics",
                "action_type": "update_tracking",
                "intent": "Add UTM parameter",
                "risk_tier": "low",
            })
            assert action["approval_state"] == "pending"


def test_action_log_immutability():
    """Every state transition should be recorded in the append-only log."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            action = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "social",
                "action_type": "publish_social_post",
                "intent": "Post product launch announcement",
                "risk_tier": "medium",
            })
            action_id = action["action_id"]

            # Transition: pending -> held -> approved -> executing -> completed
            store.hold_action(action_id)
            store.approve_action(action_id)
            store.mark_executing(action_id)
            store.mark_completed(action_id, result_summary={"posted": True})

            log = store.get_action_log()

            # Should have 5 entries: creation + 4 transitions
            assert len(log) == 5

            # Verify all entries reference this action
            for entry in log:
                assert entry["action_id"] == action_id
                assert entry["log_id"].startswith("log_")
                assert entry["timestamp"] is not None

            # Verify the state transitions are in reverse chronological order (newest first)
            states = [(e["field"], e["new_state"]) for e in log]
            assert ("execution_state", "completed") in states
            assert ("execution_state", "executing") in states
            assert ("approval_state", "approved") in states
            assert ("approval_state", "held") in states
            assert ("approval_state", "pending") in states

            # Log files on disk should be individual JSON files (immutable)
            log_files = list(store.log_dir.glob("*.json"))
            assert len(log_files) == 5


def test_action_failure_and_rollback():
    """Failed actions can be rolled back."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            action = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Update pricing page",
                "risk_tier": "medium",
            })
            store.approve_action(action["action_id"])
            store.mark_executing(action["action_id"])

            failed = store.mark_failed(action["action_id"], error="API timeout")
            assert failed["execution_state"] == "failed"
            assert failed["result_summary"]["error"] == "API timeout"

            rolled_back = store.mark_rolled_back(
                action["action_id"],
                rollback_result={"restored": True, "previous_version": "v2.1"},
            )
            assert rolled_back["execution_state"] == "rolled_back"
            assert rolled_back["result_summary"]["restored"] is True


def test_list_actions_filters():
    """list_actions should filter by brand, channel, and states."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            store.propose_action({
                "brand_id": "glowcraft",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Update homepage",
                "risk_tier": "low",
            })
            store.propose_action({
                "brand_id": "glowcraft",
                "channel": "email",
                "action_type": "send_broadcast",
                "intent": "Send newsletter",
                "risk_tier": "medium",
            })
            store.propose_action({
                "brand_id": "other_brand",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Update other homepage",
                "risk_tier": "low",
            })

            all_actions = store.list_actions()
            assert len(all_actions) == 3

            glowcraft_only = store.list_actions(brand_id="glowcraft")
            assert len(glowcraft_only) == 2

            website_only = store.list_actions(channel="website")
            assert len(website_only) == 2

            glowcraft_website = store.list_actions(brand_id="glowcraft", channel="website")
            assert len(glowcraft_website) == 1


def test_pending_approvals_listing():
    """list_pending_approvals should return only pending and held actions."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            a1 = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Action 1 - stays pending",
                "risk_tier": "medium",
            })
            a2 = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "email",
                "action_type": "send_broadcast",
                "intent": "Action 2 - will be held",
                "risk_tier": "high",
            })
            a3 = store.propose_action({
                "brand_id": "glowcraft",
                "channel": "social",
                "action_type": "publish_social_post",
                "intent": "Action 3 - will be approved",
                "risk_tier": "medium",
            })

            store.hold_action(a2["action_id"])
            store.approve_action(a3["action_id"])

            pending = store.list_pending_approvals()
            assert len(pending) == 2
            pending_ids = {a["action_id"] for a in pending}
            assert a1["action_id"] in pending_ids
            assert a2["action_id"] in pending_ids
            assert a3["action_id"] not in pending_ids

            # Filter by brand
            pending_glowcraft = store.list_pending_approvals(brand_id="glowcraft")
            assert len(pending_glowcraft) == 2


def test_action_proposal_with_dataclass():
    """ActionProposal dataclass should work as input to propose_action."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ActionStore(base_dir=Path(tmpdir) / "runtime")

            proposal = ActionProposal(
                brand_id="glowcraft",
                channel="paid_media",
                action_type="create_ad_creative",
                intent="Create new Meta ad creative for spring campaign",
                proposed_changes={"ad_set": "spring_2026", "headline": "Spring Glow Sale"},
                risk_tier="medium",
                policy_result={"passed": True, "checks": ["meta_tos"], "violations": []},
            )

            action = store.propose_action(proposal)
            assert action["action_id"].startswith("act_")
            assert action["brand_id"] == "glowcraft"
            assert action["channel"] == "paid_media"
            assert action["proposed_changes"]["headline"] == "Spring Glow Sale"
            assert action["policy_result"]["passed"] is True


def test_action_persistence_across_store_instances():
    """Actions should survive store re-instantiation (file-backed)."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "runtime"

            store1 = ActionStore(base_dir=base)
            action = store1.propose_action({
                "brand_id": "glowcraft",
                "channel": "website",
                "action_type": "update_page_copy",
                "intent": "Test persistence",
                "risk_tier": "low",
            })

            store2 = ActionStore(base_dir=base)
            reloaded = store2.get_action(action["action_id"])
            assert reloaded is not None
            assert reloaded["intent"] == "Test persistence"


# -----------------------------------------------------------------------
# IntegrationRegistry tests
# -----------------------------------------------------------------------


def test_integration_register_and_get():
    """Register an integration and retrieve it by ID."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")

            entry = registry.register({
                "brand_id": "glowcraft",
                "channel": "website",
                "provider": "wordpress",
                "status": "connected",
                "credentials_ref": "vault://glowcraft/wordpress",
                "config": {"site_url": "https://glowcraft.com"},
                "capabilities": ["read", "write"],
            })

            assert entry["integration_id"].startswith("int_")
            assert entry["status"] == "connected"
            assert entry["connected_at"] is not None

            fetched = registry.get(entry["integration_id"])
            assert fetched is not None
            assert fetched["provider"] == "wordpress"


def test_integration_list_for_brand():
    """list_for_brand should filter by brand and optionally by channel."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")

            registry.register({
                "brand_id": "glowcraft",
                "channel": "website",
                "provider": "wordpress",
                "status": "connected",
            })
            registry.register({
                "brand_id": "glowcraft",
                "channel": "email",
                "provider": "mailchimp",
                "status": "connected",
            })
            registry.register({
                "brand_id": "other_brand",
                "channel": "website",
                "provider": "shopify",
                "status": "connected",
            })

            all_glowcraft = registry.list_for_brand("glowcraft")
            assert len(all_glowcraft) == 2

            website_only = registry.list_for_brand("glowcraft", channel="website")
            assert len(website_only) == 1
            assert website_only[0]["provider"] == "wordpress"


def test_integration_disconnect():
    """Disconnecting an integration should set its status."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")

            entry = registry.register({
                "brand_id": "glowcraft",
                "channel": "paid_media",
                "provider": "meta",
                "status": "connected",
                "capabilities": ["read", "write", "budget"],
            })

            disconnected = registry.disconnect(entry["integration_id"])
            assert disconnected["status"] == "disconnected"

            fetched = registry.get(entry["integration_id"])
            assert fetched["status"] == "disconnected"


def test_integration_kill_switch():
    """Kill switch should block and unblock channel integrations."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")

            registry.register({
                "brand_id": "glowcraft",
                "channel": "paid_media",
                "provider": "meta",
                "status": "connected",
                "capabilities": ["read", "write", "budget"],
            })
            registry.register({
                "brand_id": "glowcraft",
                "channel": "paid_media",
                "provider": "google_ads",
                "status": "connected",
                "capabilities": ["read", "write", "budget"],
            })

            # Channel should be active before kill switch
            assert registry.is_channel_active("glowcraft", "paid_media") is True

            # Activate kill switch
            killed = registry.activate_kill_switch("glowcraft", "paid_media")
            assert len(killed) == 2
            for entry in killed:
                assert entry["kill_switch"] is True

            # Channel should be inactive after kill switch
            assert registry.is_channel_active("glowcraft", "paid_media") is False

            # Deactivate kill switch
            restored = registry.deactivate_kill_switch("glowcraft", "paid_media")
            assert len(restored) == 2
            for entry in restored:
                assert entry["kill_switch"] is False

            # Channel should be active again
            assert registry.is_channel_active("glowcraft", "paid_media") is True


def test_integration_is_channel_active_requires_connected():
    """is_channel_active should return False for disconnected integrations."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")

            entry = registry.register({
                "brand_id": "glowcraft",
                "channel": "email",
                "provider": "mailchimp",
                "status": "disconnected",
            })

            assert registry.is_channel_active("glowcraft", "email") is False

            # Connect it
            registry.update(entry["integration_id"], status="connected")
            assert registry.is_channel_active("glowcraft", "email") is True


def test_integration_update():
    """update() should patch fields and preserve the rest."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")

            entry = registry.register({
                "brand_id": "glowcraft",
                "channel": "analytics",
                "provider": "ga4",
                "status": "pending_auth",
                "config": {"property_id": "G-12345"},
            })

            updated = registry.update(
                entry["integration_id"],
                status="connected",
                config={"property_id": "G-12345", "view_id": "main"},
            )
            assert updated["status"] == "connected"
            assert updated["config"]["view_id"] == "main"
            assert updated["connected_at"] is not None


def test_integration_dataclass_input():
    """IntegrationEntry dataclass should work as input to register."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")

            entry = IntegrationEntry(
                brand_id="glowcraft",
                channel="social",
                provider="meta",
                status="connected",
                capabilities=["read", "write", "schedule"],
                config={"page_id": "123456"},
            )

            registered = registry.register(entry)
            assert registered["integration_id"].startswith("int_")
            assert registered["provider"] == "meta"
            assert registered["capabilities"] == ["read", "write", "schedule"]


def test_integration_persistence():
    """Integrations should survive registry re-instantiation."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            base = Path(tmpdir) / "runtime"

            reg1 = IntegrationRegistry(base_dir=base)
            entry = reg1.register({
                "brand_id": "glowcraft",
                "channel": "website",
                "provider": "shopify",
                "status": "connected",
            })

            reg2 = IntegrationRegistry(base_dir=base)
            fetched = reg2.get(entry["integration_id"])
            assert fetched is not None
            assert fetched["provider"] == "shopify"


def test_no_channel_returns_inactive():
    """is_channel_active returns False when no integrations exist for a channel."""
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            registry = IntegrationRegistry(base_dir=Path(tmpdir) / "runtime")
            assert registry.is_channel_active("glowcraft", "nonexistent") is False


# -----------------------------------------------------------------------
# Runner
# -----------------------------------------------------------------------


if __name__ == "__main__":
    test_action_proposal_lifecycle_full()
    test_action_rejection_and_hold()
    test_auto_approval_low_risk()
    test_auto_approval_disabled_by_default()
    test_action_log_immutability()
    test_action_failure_and_rollback()
    test_list_actions_filters()
    test_pending_approvals_listing()
    test_action_proposal_with_dataclass()
    test_action_persistence_across_store_instances()
    test_integration_register_and_get()
    test_integration_list_for_brand()
    test_integration_disconnect()
    test_integration_kill_switch()
    test_integration_is_channel_active_requires_connected()
    test_integration_update()
    test_integration_dataclass_input()
    test_integration_persistence()
    test_no_channel_returns_inactive()
    print("All actions + integrations tests passed!")
