from datetime import datetime, timedelta, timezone

from kai.runtime.agents import default_agent_profiles
from kai.runtime.commercial import (
    COMMERCIAL_AGENT_IDS,
    CommercialHandoff,
    WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
)
from kai.runtime.workflows import get_workflow
from kai.runtime.store import RuntimeStore
from kai.runtime.website_builder_tools import (
    WebsiteBuilderToolResult,
    execute_codegen,
    result_to_handoff,
)
from kai.runtime.cloudflare_tools import _tree_sha256, deploy_pages
from kai.runtime.stripe_tools import create_test_payment_link
from kai.runtime.commercial_workflow import AGENT_EDGES, CommercialWorkflow, website_to_checkout
from kai.runtime.commercial_packet import build_commercial_packet
from kai.runtime.commercial_preflight import preflight
from kai.runtime.commercial_release import authorize_release, reconcile_release


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


def test_runtime_store_persists_commercial_handoffs_and_append_only_events(tmp_path):
    store = RuntimeStore(base_dir=tmp_path / "runtime")
    run = store.start_commercial_run(
        {
            "intent": "Build a demo site and checkout",
            "workflow": WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
            "brand_id": "demo-brand",
            "surface": "local",
            "inputs": {"source": "kaicalls:call:demo-001"},
        }
    )
    expires_at = (datetime.now(timezone.utc) + timedelta(hours=1)).isoformat()
    handoff = CommercialHandoff(
        run_id=run["run_id"],
        work_id="offer-001",
        source_ref="kaicalls:call:demo-001",
        producer_agent_id="agent.offer.strategist",
        consumer_agent_id="agent.proposal",
        artifact_uri="artifact://demo/offer-001.json",
        artifact_sha256="b" * 64,
        status="ready",
        approval_state="not_required",
        expires_at=expires_at,
    )

    assert store.append_commercial_handoff(handoff)["status"] == "ready"
    assert store.claim_commercial_handoff("offer-001", "agent.proposal")["status"] == "claimed"
    completed = store.complete_commercial_handoff(
        "offer-001", "agent.proposal", result={"proposal_id": "proposal-001"}
    )
    assert completed["status"] == "completed"

    reloaded = RuntimeStore(base_dir=tmp_path / "runtime")
    bundle = reloaded.get_commercial_bundle(run["run_id"])
    assert bundle["handoffs"][0]["metadata"]["consumer_result"]["proposal_id"] == "proposal-001"
    assert [event["event_type"] for event in bundle["events"]] == [
        "run.started",
        "handoff.ready",
        "handoff.claimed",
        "handoff.completed",
    ]


def test_runtime_store_binds_ola_approval_before_claim(tmp_path):
    store = RuntimeStore(base_dir=tmp_path / "runtime")
    run = store.start_commercial_run(
        {
            "intent": "Prepare approved checkout",
            "workflow": WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
            "brand_id": "demo-brand",
        }
    )
    handoff = CommercialHandoff(
        run_id=run["run_id"],
        work_id="checkout-001",
        source_ref="offer://demo/offer-001",
        producer_agent_id="agent.checkout",
        consumer_agent_id="agent.effect.executor",
        artifact_uri="stripe://checkout/checkout-001",
        artifact_sha256="c" * 64,
        status="ready",
        approval_state="pending",
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    )
    store.append_commercial_handoff(handoff)

    try:
        store.claim_commercial_handoff("checkout-001", "agent.effect.executor")
    except PermissionError:
        pass
    else:
        raise AssertionError("pending OLA handoff was claimable")

    approved = store.set_commercial_approval(
        "checkout-001",
        "approved",
        approval_ref="ola://approval/demo-001",
        approved_by="connor",
    )
    assert approved["approval_state"] == "approved"
    assert store.claim_commercial_handoff("checkout-001", "agent.effect.executor")["status"] == "claimed"


def test_website_builder_tool_boundary_persists_hashed_receipt(tmp_path, monkeypatch):
    project = tmp_path / "website-builder"
    output = project / "apps" / "web" / "generated"
    output.mkdir(parents=True)
    (project / "orchestrate.js").write_text("// existing Website Builder entrypoint\n", encoding="utf-8")
    (output / "before.tsx").write_text("old", encoding="utf-8")

    class Completed:
        returncode = 0
        stdout = "real orchestrator receipt"
        stderr = ""

    def fake_run(command, **kwargs):
        (output / "page.tsx").write_text("generated by tool boundary", encoding="utf-8")
        return Completed()

    monkeypatch.setattr("kai.runtime.website_builder_tools.subprocess.run", fake_run)
    store = RuntimeStore(base_dir=tmp_path / "runtime")
    run = store.start_commercial_run(
        {
            "intent": "Generate the approved website surface",
            "workflow": WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
            "brand_id": "demo-brand",
        }
    )
    result = execute_codegen(
        store=store,
        run_id=run["run_id"],
        work_id="website-001",
        agent_id="agent.website.page",
        project_dir=project,
        specs=[{"type": "PageSpec", "id": "page.home", "route": "/"}],
        output_roots=["apps/web/generated"],
        build=False,
    )

    assert result.ok is True
    assert "apps\\web\\generated\\page.tsx" in result.changed_files or "apps/web/generated/page.tsx" in result.changed_files
    handoff = result_to_handoff(
        result,
        source_ref="handoff://website-spec-001",
        consumer_agent_id="agent.website.qa",
        expires_at=(datetime.now(timezone.utc) + timedelta(hours=1)).isoformat(),
    )
    persisted = store.append_commercial_handoff(handoff)
    assert persisted["artifact_uri"].startswith("artifact://commercial/tool-receipts/")
    assert len(persisted["artifact_sha256"]) == 64


def test_cloudflare_pages_tool_requires_approved_tree_and_reads_back_provider_state(
    tmp_path, monkeypatch
):
    output = tmp_path / "dist"
    output.mkdir()
    (output / "index.html").write_text("approved site", encoding="utf-8")
    approved_digest = _tree_sha256(output)

    class Completed:
        returncode = 0
        stdout = "https://demo.pages.dev"
        stderr = ""

    def fake_run(command, **kwargs):
        if "deployment" in command:
            result = Completed()
            result.stdout = '[{"id":"dep-001","url":"https://demo.pages.dev"}]'
            return result
        return Completed()

    monkeypatch.setattr("kai.runtime.cloudflare_tools.subprocess.run", fake_run)
    store = RuntimeStore(base_dir=tmp_path / "runtime")
    run = store.start_commercial_run(
        {
            "intent": "Deploy the approved site",
            "workflow": WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
            "brand_id": "demo-brand",
        }
    )
    receipt = deploy_pages(
        store=store,
        run_id=run["run_id"],
        work_id="deploy-001",
        project_name="demo-site",
        output_dir=output,
        approved_artifact_tree_sha256=approved_digest,
        account_id="account-001",
    )

    assert receipt.ok is True
    assert receipt.readback[0]["id"] == "dep-001"
    assert receipt.deployment_url == "https://demo.pages.dev"
    assert receipt.receipt_uri.endswith("deploy-001.cloudflare.json")


def test_stripe_tool_is_test_only_and_reads_back_hosted_payment_link(tmp_path, monkeypatch):
    calls = []

    def fake_request(method, path, **kwargs):
        calls.append((method, path, kwargs))
        if method == "POST":
            return {"id": "plink_test_001", "url": "https://buy.stripe.test/demo"}
        return {
            "id": "plink_test_001",
            "url": "https://buy.stripe.test/demo",
            "active": True,
            "metadata": {"run_id": "run-001", "work_id": "checkout-001"},
        }

    monkeypatch.setattr("kai.runtime.stripe_tools._stripe_request", fake_request)
    store = RuntimeStore(base_dir=tmp_path / "runtime")
    receipt = create_test_payment_link(
        store=store,
        run_id="run-001",
        work_id="checkout-001",
        offer_name="Website launch package",
        amount_cents=2500,
        api_key="sk_test_demo",
    )

    assert receipt.payment_link_id == "plink_test_001"
    assert receipt.readback["active"] is True
    assert calls[0][0:2] == ("POST", "/payment_links")
    assert calls[1][0:2] == ("GET", "/payment_links/plink_test_001")

    try:
        create_test_payment_link(
            store=store,
            run_id="run-001",
            work_id="checkout-live",
            offer_name="Unsafe live test",
            amount_cents=100,
            api_key="sk_live_do_not_use",
        )
    except RuntimeError as error:
        assert "sk_test_" in str(error)
    else:
        raise AssertionError("live Stripe key was accepted")


def test_workflow_handler_requires_a_real_agent_executor(tmp_path):
    request = {
        "brand_id": "demo-brand",
        "source_ref": "kaicalls:call:demo-002",
        "source_artifact_uri": "artifact://calls/demo-002.json",
        "source_artifact_sha256": "d" * 64,
    }

    try:
        import asyncio

        asyncio.run(website_to_checkout(request, store=RuntimeStore(base_dir=tmp_path / "runtime")))
    except RuntimeError as error:
        assert "configured agent executor" in str(error)
    else:
        raise AssertionError("workflow accepted a missing agent executor")


def test_workflow_advances_named_agents_and_holds_effect_edges_for_ola(tmp_path):
    calls = []

    def executor(*, agent_id, run, handoff):
        calls.append((agent_id, handoff["work_id"]))
        return {
            "artifact_uri": f"artifact://{run['run_id']}/{agent_id}.json",
            "artifact_sha256": "e" * 64,
            "metadata": {"agent_turn": agent_id},
        }

    store = RuntimeStore(base_dir=tmp_path / "runtime")
    workflow = CommercialWorkflow(store, executor)
    first = workflow.start_from_voice(
        {
            "brand_id": "demo-brand",
            "source_ref": "kaicalls:call:demo-003",
            "source_artifact_uri": "artifact://calls/demo-003.json",
            "source_artifact_sha256": "f" * 64,
        }
    )

    import asyncio

    advanced = asyncio.run(workflow.advance(first["work_id"]))
    assert calls == [("agent.commercial.orchestrator", first["work_id"])]
    assert advanced["status"] == "advanced"

    offer = next(
        item for item in advanced["next_handoffs"]
        if item["consumer_agent_id"] == "agent.offer.strategist"
    )
    advanced_offer = asyncio.run(workflow.advance(offer["work_id"]))
    website = next(
        item for item in advanced_offer["next_handoffs"]
        if item["consumer_agent_id"] == "agent.website.architect"
    )
    assert website["approval_state"] == "not_required"
    assert all(item["consumer_agent_id"] != "agent.checkout" for item in advanced_offer["next_handoffs"])
    assert [agent_id for agent_id, _ in calls] == [
        "agent.commercial.orchestrator",
        "agent.offer.strategist",
    ]


def test_build_and_release_order_keeps_outbound_effects_after_ola():
    assert AGENT_EDGES["agent.website.qa"] == ("agent.proposal",)
    assert AGENT_EDGES["agent.proposal"] == ("agent.checkout",)
    assert AGENT_EDGES["agent.checkout"] == ("agent.booking",)
    assert AGENT_EDGES["agent.booking"] == ("agent.ola.projector",)
    assert "agent.checkout.release" in AGENT_EDGES["agent.effect.executor"]
    assert "agent.cloudflare.publisher" in AGENT_EDGES["agent.effect.executor"]


def test_preapproval_packet_binds_all_held_artifacts_and_effects():
    packet = build_commercial_packet(
        run_id="sale-demo-001",
        offer={"artifact_sha256": "a" * 64},
        website={"artifact_sha256": "b" * 64},
        proposal={"artifact_sha256": "c" * 64, "artifact_url": "https://artifacts.example.test/proposal.md", "mime_type": "text/markdown", "title": "Website proposal"},
        checkout={"id": "plink_test_001", "livemode": False, "state": "held"},
        booking={"id": "booking_test_001", "state": "held"},
        recipient={"address": "demo@example.test", "channel": "email"},
        effects=[
            {"effect_id": "cloudflare.publish", "state": "held"},
            {"effect_id": "proposal.send", "state": "held"},
            {"effect_id": "checkout.release", "state": "held"},
            {"effect_id": "booking.deliver", "state": "held"},
        ],
        expires_at="2026-07-30T00:00:00+00:00",
    )

    assert packet["schema"] == "kai.commercial.packet.v1"
    assert packet["approval_state"] == "pending"
    assert packet["checkout"] == {"id": "plink_test_001", "livemode": False, "state": "held"}
    assert packet["approval"]["packet_sha256"] == packet["packet_sha256"]


def test_preapproval_packet_rejects_live_or_unheld_checkout():
    try:
        build_commercial_packet(
            run_id="sale-demo-002",
            offer={"artifact_sha256": "a" * 64},
            website={"artifact_sha256": "b" * 64},
            proposal={"artifact_sha256": "c" * 64, "artifact_url": "https://artifacts.example.test/proposal.md", "mime_type": "text/markdown", "title": "Website proposal"},
            checkout={"id": "plink_live", "livemode": True, "state": "held"},
            booking={"id": "booking_test_002", "state": "held"},
            recipient={"address": "demo@example.test", "channel": "email"},
            effects=[{"effect_id": "proposal.send", "state": "held"}],
            expires_at="2026-07-30T00:00:00+00:00",
        )
    except ValueError as error:
        assert "test-mode" in str(error)
    else:
        raise AssertionError("live checkout was accepted into a preapproval packet")


def test_preflight_covers_every_pre_call_phase_and_agent():
    profiles = {profile.agent_id: profile.model_dump() for profile in default_agent_profiles()}
    packet = build_commercial_packet(
        run_id="sale-demo-003",
        offer={"artifact_sha256": "a" * 64},
        website={"artifact_sha256": "b" * 64},
        proposal={"artifact_sha256": "c" * 64, "artifact_url": "https://artifacts.example.test/proposal.md", "mime_type": "text/markdown", "title": "Website proposal"},
        checkout={"id": "plink_test_003", "livemode": False, "state": "held"},
        booking={"id": "booking_test_003", "state": "held"},
        recipient={"address": "demo@example.test", "channel": "email"},
        effects=[{"effect_id": "proposal.send", "state": "held"}],
        expires_at="2026-07-30T00:00:00+00:00",
    )
    result = preflight(profiles=profiles, packet=packet)
    assert result["ready"] is True
    assert result["errors"] == []
    assert "website_qa" in result["phases"]
    assert "ola_pending" in result["phases"]


def test_after_call_release_requires_exact_approval_and_reconciles_every_effect():
    packet = {"packet_sha256": "d" * 64, "effects": [{"effect_id": "site.publish"}, {"effect_id": "checkout.release"}]}
    authorization = authorize_release(packet=packet, approval={"decision": "APPROVE", "packet_sha256": "d" * 64})
    result = reconcile_release(
        authorization=authorization,
        receipts=[{"effect_id": "site.publish"}, {"effect_id": "checkout.release"}],
        readbacks=[{"effect_id": "site.publish"}, {"effect_id": "checkout.release"}],
    )
    assert result["state"] == "shipped"


def test_after_call_release_rejects_stale_approval_and_missing_readback():
    packet = {"packet_sha256": "e" * 64, "effects": [{"effect_id": "site.publish"}]}
    try:
        authorize_release(packet=packet, approval={"decision": "APPROVE", "packet_sha256": "f" * 64})
    except PermissionError:
        pass
    else:
        raise AssertionError("stale approval was accepted")
    authorization = authorize_release(packet=packet, approval={"decision": "APPROVE", "packet_sha256": "e" * 64})
    result = reconcile_release(authorization=authorization, receipts=[], readbacks=[])
    assert result["state"] == "blocked"
