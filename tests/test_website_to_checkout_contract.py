from datetime import datetime, timezone

from kai.runtime.agents import default_agent_profiles
from kai.runtime.commercial import (
    COMMERCIAL_AGENT_IDS,
    CommercialHandoff,
    WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
)
from kai.runtime.workflows import get_workflow


def test_website_to_checkout_is_registered_as_high_risk_manual_workflow():
    workflow = get_workflow(WEBSITE_TO_CHECKOUT_WORKFLOW_ID)

    assert workflow is not None
    assert workflow.handler == "kai.runtime.commercial.website_to_checkout"
    assert workflow.risk_tier == "high"
    assert workflow.auto_run_allowed is False
    assert "provider_receipts" in workflow.output_artifacts


def test_commercial_agent_profiles_are_first_class_and_scoped():
    profiles = {profile.agent_id: profile for profile in default_agent_profiles()}

    assert set(COMMERCIAL_AGENT_IDS).issubset(profiles)
    assert profiles["agent.website.content"].workflow_scope == [WEBSITE_TO_CHECKOUT_WORKFLOW_ID]
    assert "website_builder.gen_content" in profiles["agent.website.content"].tool_scope
    assert "cloudflare.deploy" in profiles["agent.cloudflare.publisher"].tool_scope


def test_handoff_requires_distinct_known_agents_and_hash():
    handoff = CommercialHandoff(
        run_id="sale-001",
        work_id="work-001",
        source_ref="kaicalls:call:call-001",
        producer_agent_id="agent.offer.strategist",
        consumer_agent_id="agent.proposal",
        artifact_uri="artifact://sale-001/offer.json",
        artifact_sha256="a" * 64,
        status="ready",
        approval_state="not_required",
        expires_at=datetime.now(timezone.utc).isoformat(),
    )

    assert handoff.validate() == []
    assert handoff.model_dump()["schema"] == "kai.commercial.handoff.v1"


def test_handoff_rejects_unknown_agent_and_bad_hash():
    handoff = CommercialHandoff(
        run_id="sale-001",
        work_id="work-001",
        source_ref="kaicalls:call:call-001",
        producer_agent_id="agent.fake",
        consumer_agent_id="agent.fake",
        artifact_uri="artifact://sale-001/offer.json",
        artifact_sha256="not-a-hash",
        status="ready",
        approval_state="pending",
        expires_at="not-a-date",
    )

    errors = handoff.validate()
    assert "producer_agent_id and consumer_agent_id must differ" in errors
    assert any("unknown producer agent" in error for error in errors)
    assert "artifact_sha256 must be lowercase SHA-256" in errors
    assert "expires_at must be ISO-8601" in errors
