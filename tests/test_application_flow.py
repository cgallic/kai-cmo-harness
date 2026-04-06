"""Tests for the first application-level local-service flow."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.runtime.actions import ActionStore
from kai.runtime.application_flow import (
    ProposedAction,
    ReviewBundle,
    build_local_service_audit_input,
    build_proposed_actions,
    build_review_bundle,
    persist_proposed_actions,
    run_local_service_audit,
    run_local_service_review_flow,
)
from kai.runtime.audit import AuditCategory, AuditResult
from kai.runtime.business_profile import load_local_service_fixture
from kai.runtime import load_andon_window_cleaning_fixture


def test_build_local_service_audit_input_covers_all_categories():
    """The adapter should emit the eight canonical local-service audit sections."""
    profile = load_local_service_fixture()

    audit_input = build_local_service_audit_input(profile)

    assert set(audit_input.keys()) == {category.value for category in AuditCategory}
    assert all(isinstance(checks, list) for checks in audit_input.values())
    assert all(len(checks) >= 4 for checks in audit_input.values())


def test_run_local_service_audit_from_business_profile():
    """The application flow should audit directly from a BusinessProfile."""
    profile = load_local_service_fixture()

    result = run_local_service_audit(profile)

    assert isinstance(result, AuditResult)
    assert result.brand_id == "truenorth-hvac"
    assert result.archetype == "local-service"
    assert len(result.categories) == 8
    assert result.total_findings >= 3
    assert result.overall_score >= 80


def test_build_proposed_actions_from_audit_findings():
    """Prioritized findings should become typed action proposals."""
    profile = load_local_service_fixture()
    audit_result = run_local_service_audit(profile)

    proposals = build_proposed_actions(profile, audit_result, source_run_id="run_local_123")

    assert proposals
    assert all(isinstance(proposal, ProposedAction) for proposal in proposals)
    assert all(proposal.brand_id == "truenorth-hvac" for proposal in proposals)
    assert all(proposal.source_audit_id == audit_result.audit_id for proposal in proposals)
    assert all(proposal.source_run_id == "run_local_123" for proposal in proposals)
    assert all(proposal.source_finding_ids for proposal in proposals)
    assert all(proposal.risk_tier in {"low", "medium", "high"} for proposal in proposals)
    assert all("policy_result" in proposal.metadata for proposal in proposals)
    assert {proposal.channel for proposal in proposals}.issubset({"website", "social", "paid_media", "email"})


def test_persist_proposed_actions_hands_off_to_action_store():
    """Application proposals should persist cleanly into the runtime action store."""
    profile = load_local_service_fixture()
    audit_result = run_local_service_audit(profile)
    proposals = build_proposed_actions(profile, audit_result)

    with tempfile.TemporaryDirectory() as tmpdir:
        store = ActionStore(base_dir=Path(tmpdir) / "runtime")
        records = persist_proposed_actions(proposals, action_store=store)

        assert len(records) == len(proposals)
        assert all(record["action_id"].startswith("act_") for record in records)
        assert all(record["brand_id"] == "truenorth-hvac" for record in records)
        assert all(store.get_action(record["action_id"]) is not None for record in records)


def test_build_review_bundle_combines_profile_audit_and_proposals():
    """The operator review bundle should package the full application output."""
    profile = load_local_service_fixture()
    audit_result = run_local_service_audit(profile)
    proposals = build_proposed_actions(profile, audit_result)

    bundle = build_review_bundle(profile, audit_result, proposals, source_run_id="run_bundle_1")

    assert isinstance(bundle, ReviewBundle)
    assert bundle.brand_id == "truenorth-hvac"
    assert bundle.business_profile_summary["name"] == "TrueNorth HVAC"
    assert bundle.audit_summary["audit_id"] == audit_result.audit_id
    assert bundle.audit_summary["total_findings"] == audit_result.total_findings
    assert len(bundle.proposed_actions) == len(proposals)
    assert bundle.metadata["source_run_id"] == "run_bundle_1"


def test_run_local_service_review_flow_end_to_end_with_persistence():
    """The full first application slice should run end to end."""
    profile = load_local_service_fixture()

    with tempfile.TemporaryDirectory() as tmpdir:
        store = ActionStore(base_dir=Path(tmpdir) / "runtime")
        bundle = run_local_service_review_flow(
            profile,
            source_run_id="run_end_to_end",
            persist_actions=True,
            action_store=store,
        )

        assert bundle.brand_id == "truenorth-hvac"
        assert bundle.metadata["proposal_count"] == len(bundle.proposed_actions)
        assert len(bundle.persisted_action_ids) == len(bundle.proposed_actions)
        assert all(store.get_action(action_id) is not None for action_id in bundle.persisted_action_ids)


def test_andon_flow_generates_cross_channel_plan():
    """The Andon fixture should yield a realistic cross-channel action mix."""
    profile = load_andon_window_cleaning_fixture()

    bundle = run_local_service_review_flow(profile, source_run_id="run_andon", persist_actions=False)

    channels = {proposal["channel"] for proposal in bundle.proposed_actions}
    assert "website" in channels
    assert "social" in channels
    assert "email" in channels
    assert bundle.audit_summary["critical_findings"] >= 1


if __name__ == "__main__":
    import inspect

    tests = [
        obj for name, obj in sorted(globals().items())
        if name.startswith("test_") and inspect.isfunction(obj)
    ]
    for test_fn in tests:
        test_fn()
        print(f"  PASS  {test_fn.__name__}")
    print(f"\nAll {len(tests)} application-flow tests passed!")
