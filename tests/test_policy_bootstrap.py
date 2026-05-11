from __future__ import annotations

from kai.runtime.models import KaiBrandProfile
from kai.runtime.policy import PolicyEngine
from kai.runtime.policy_bootstrap import (
    activate_paid_media_accounts,
    ensure_brand_policy,
    load_brand_policy,
)


def test_first_run_policy_discovers_accounts_but_fails_closed(tmp_path):
    policy = ensure_brand_policy(
        "glowcraft",
        brand=KaiBrandProfile(
            id="glowcraft",
            name="GlowCraft",
            active_channels=["paid_media", "analytics"],
        ),
        integrations=[
            {
                "integration_id": "int_meta",
                "brand_id": "glowcraft",
                "channel": "paid_media",
                "provider": "meta_ads",
                "status": "connected",
                "capabilities": ["read", "write", "budget"],
                "config": {"ad_account_id": "act_123"},
            }
        ],
        base_dir=tmp_path / "runtime",
    )

    guardrails = policy["paid_media_guardrails"]
    assert policy["policy_status"] == "draft"
    assert guardrails["allowed_accounts"] == []
    assert guardrails["discovered_accounts"][0]["account_id"] == "act_123"

    result = PolicyEngine(brand_policies=policy).evaluate({
        "channel": "paid_media",
        "action_type": "create_paused_ad",
        "execution_requested": True,
        "metadata": {"approval_id": "approval_1"},
        "proposed_changes": {
            "account_id": "act_123",
            "status": "PAUSED",
            "change_diff": {"ad": {"before": None, "after": {"name": "Variant A"}}},
        },
        "evidence": [{"source": "approval:approval_1"}],
    })

    assert result["passed"] is False
    assert "Missing paid_media_guardrails.allowed_accounts" in result["violations"][0]


def test_existing_policy_is_preserved_on_subsequent_first_run(tmp_path):
    base_dir = tmp_path / "runtime"
    first = ensure_brand_policy(
        "glowcraft",
        brand={"id": "glowcraft", "active_channels": ["paid_media"]},
        base_dir=base_dir,
    )
    activated = activate_paid_media_accounts(
        first,
        allowed_accounts=["act_123"],
        max_daily_budget=250,
    )
    from kai.runtime.policy_bootstrap import write_brand_policy

    write_brand_policy("glowcraft", activated, base_dir=base_dir)

    second = ensure_brand_policy(
        "glowcraft",
        brand={"id": "glowcraft", "active_channels": ["paid_media"]},
        integrations=[],
        base_dir=base_dir,
    )

    assert second["policy_status"] == "active"
    assert second["paid_media_guardrails"]["allowed_accounts"] == ["act_123"]
    assert load_brand_policy("glowcraft", base_dir)["policy_status"] == "active"


def test_activated_policy_allows_approved_paused_ad_create(tmp_path):
    draft = ensure_brand_policy(
        "glowcraft",
        brand={"id": "glowcraft", "active_channels": ["paid_media"]},
        base_dir=tmp_path / "runtime",
    )
    policy = activate_paid_media_accounts(
        draft,
        allowed_accounts=["act_123"],
        max_daily_budget=250,
    )

    result = PolicyEngine(brand_policies=policy).evaluate({
        "channel": "paid_media",
        "action_type": "create_paused_ad",
        "execution_requested": True,
        "metadata": {"approval_id": "approval_1"},
        "proposed_changes": {
            "account_id": "act_123",
            "status": "PAUSED",
            "change_diff": {"ad": {"before": None, "after": {"name": "Variant A"}}},
        },
        "evidence": [{"source": "approval:approval_1"}],
    })

    assert result["passed"] is True
    assert result["requires_approval"] is True
