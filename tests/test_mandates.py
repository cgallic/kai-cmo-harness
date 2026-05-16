"""Tests for local ActionMandate ledger and execution scope validation."""

from __future__ import annotations

import contextlib
import os
import sys
import tempfile
import textwrap
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import scripts.harness_config as harness_config
from kai.runtime.loader import load_workspace_profile
from kai.runtime.mandates import MandateLedger
from kai.runtime.models import ActionMandate


def _with_config(yaml_content: str):
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
products: []
"""


def _approved_mandate(ledger: MandateLedger, **overrides):
    payload = {
        "agent_id": "agent_kai_operator",
        "brand_id": "alpha-hvac",
        "channel": "website",
        "action_types": ["update_page_copy"],
        "limits": {},
        "created_by": "ops@kai.test",
        "approval_state": "pending",
    }
    payload.update(overrides)
    created = ledger.create(payload)
    return ledger.approve(created["mandate_id"], approved_by="ops@kai.test")


def test_mandate_ledger_create_get_list_and_state_changes():
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = MandateLedger(base_dir=Path(tmpdir) / "runtime")
            created = ledger.create(
                ActionMandate(
                    agent_id="agent_kai_operator",
                    brand_id="alpha-hvac",
                    channel="social",
                    action_types=["publish_social_post"],
                    created_by="ops@kai.test",
                    source_run_id="run_123",
                )
            )
            assert created["mandate_id"].startswith("mandate_")
            assert created["approval_state"] == "pending"

            approved = ledger.approve(created["mandate_id"], approved_by="ops@kai.test")
            assert approved["approval_state"] == "approved"

            listed = ledger.list(brand_id="alpha-hvac", approval_state="approved")
            assert len(listed) == 1
            assert listed[0]["mandate_id"] == created["mandate_id"]

            revoked = ledger.revoke(created["mandate_id"], approved_by="ops@kai.test", note="End of campaign")
            assert revoked["approval_state"] == "revoked"
            assert revoked["revoked_at"] is not None


def test_validate_for_action_requires_approved_mandate_for_high_risk_categories():
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = MandateLedger(base_dir=Path(tmpdir) / "runtime")

            site_mutation = {
                "brand_id": "alpha-hvac",
                "channel": "website",
                "action_type": "update_page_copy",
                "risk_tier": "medium",
            }
            publish = {
                "brand_id": "alpha-hvac",
                "channel": "social",
                "action_type": "publish_social_post",
                "risk_tier": "medium",
            }
            outreach = {
                "brand_id": "alpha-hvac",
                "channel": "email",
                "action_type": "send_approved_template",
                "risk_tier": "medium",
            }
            spend = {
                "brand_id": "alpha-hvac",
                "channel": "paid_media",
                "action_type": "increase_budget",
                "risk_tier": "high",
            }

            for action in (site_mutation, publish, outreach, spend):
                denied = ledger.validate_for_action(action)
                assert denied["allowed"] is False
                assert "requires an approved mandate" in denied["reason"]


def test_validate_for_action_enforces_expiry_revocation_and_spend_limits():
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = MandateLedger(base_dir=Path(tmpdir) / "runtime")

            # Expired mandate
            expired = _approved_mandate(
                ledger,
                channel="paid_media",
                action_types=["increase_budget"],
                expires_at=(datetime.now(timezone.utc) - timedelta(minutes=1)).isoformat(),
            )
            expired_action = {
                "brand_id": "alpha-hvac",
                "channel": "paid_media",
                "action_type": "increase_budget",
                "risk_tier": "high",
                "mandate_id": expired["mandate_id"],
            }
            expired_result = ledger.validate_for_action(expired_action)
            assert expired_result["allowed"] is False
            assert "expired" in expired_result["reason"].lower()

            # Revoked mandate
            revoked = _approved_mandate(
                ledger,
                channel="social",
                action_types=["publish_social_post"],
            )
            ledger.revoke(revoked["mandate_id"], approved_by="ops@kai.test")
            revoked_action = {
                "brand_id": "alpha-hvac",
                "channel": "social",
                "action_type": "publish_social_post",
                "risk_tier": "medium",
                "mandate_id": revoked["mandate_id"],
            }
            revoked_result = ledger.validate_for_action(revoked_action)
            assert revoked_result["allowed"] is False
            assert "not approved" in revoked_result["reason"].lower()

            # Spend-limited mandate
            spend = _approved_mandate(
                ledger,
                channel="paid_media",
                action_types=["increase_budget"],
                limits={"max_daily_budget_usd": 200, "max_budget_increase_pct": 20},
            )
            spend_action = {
                "brand_id": "alpha-hvac",
                "channel": "paid_media",
                "action_type": "increase_budget",
                "risk_tier": "high",
                "mandate_id": spend["mandate_id"],
                "proposed_changes": {"new_daily_budget": 260, "budget_increase_pct": 30},
            }
            spend_result = ledger.validate_for_action(spend_action)
            assert spend_result["allowed"] is False
            assert "exceeds mandate limit" in spend_result["reason"]


def test_low_risk_read_only_action_does_not_require_mandate():
    with _with_config(YAML_CONTENT):
        with tempfile.TemporaryDirectory() as tmpdir:
            ledger = MandateLedger(base_dir=Path(tmpdir) / "runtime")
            read_only_action = {
                "brand_id": "alpha-hvac",
                "channel": "analytics",
                "action_type": "read_performance",
                "risk_tier": "low",
            }
            result = ledger.validate_for_action(read_only_action)
            assert result["allowed"] is True
            assert "not required" in result["reason"].lower()
