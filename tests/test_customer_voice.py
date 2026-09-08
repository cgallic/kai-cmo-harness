import asyncio
import json
from types import SimpleNamespace as NS

import pytest

from kai.voice import VoiceStore
from kai.voice.evaluation import calibrate, review_draft, compare_replay
from scripts.quality.engine import QualityEngine, clear_cache
from scripts.quality.gate import evaluate_proposal


@pytest.fixture
def store(tmp_path):
    return VoiceStore(tmp_path / "voice.sqlite")


def profile(store, **kwargs):
    args = dict(brand="acme", writer="founder", rules=["Use plain sentences."],
                banned_phrases=["enterprise-grade"], source_ref="guide:1", approved_by="customer")
    args.update(kwargs)
    return store.profile(**args)


def example(store, **kwargs):
    args = dict(brand="acme", writer="founder", channel="linkedin", original="Old copy",
                final="Customer copy", source_ref="post:1", reviewer="customer",
                reason="Too corporate", topic="hiring")
    args.update(kwargs)
    return store.example(**args)


def test_versions_require_compare_and_swap(store):
    v1 = profile(store)
    assert profile(store) == v1
    with pytest.raises(ValueError, match="expected_version"):
        profile(store, rules=["Keep paragraphs short."])
    v2 = profile(store, rules=["Keep paragraphs short."], expected_version=v1)
    assert v2 != v1
    assert store.packet(brand="acme", writer="founder", channel="linkedin")["profiles"][0]["version"] == v2


def test_scope_and_holdout_never_leak(store):
    profile(store)
    example(store)
    example(store, brand="other", original="Other draft", final="Other customer")
    example(store, writer="employee", original="Employee draft", final="Employee final")
    example(store, channel="email", original="Email draft", final="Email final")
    example(store, split="holdout", original="Test draft", final="Test final")
    example(store, audience="enterprise", original="Enterprise draft", final="Enterprise final")
    example(store, origin="ai_approved", original="AI draft", final="AI final")
    packet = store.packet(brand="acme", writer="founder", channel="linkedin", topic="hiring")
    assert [e["final"] for e in packet["examples"]] == ["Customer copy"]
    assert not store.packet(brand="unknown", writer="founder", channel="linkedin")["configured"]


def test_train_holdout_duplicates_rejected(store):
    example(store)
    with pytest.raises(ValueError, match="overlaps"):
        example(store, split="holdout", original="Some new opening")


def test_feedback_retains_edits_without_promoting_rules(store):
    profile(store)
    packet = store.packet(brand="acme", writer="founder", channel="linkedin")
    store.record(run_id="run1", brand="acme", kind="context", data=packet)
    store.record(run_id="run1", brand="acme", kind="draft", data={"content": "Our innovative solution"})
    args = dict(brand="acme", run_id="run1", final="We answer your calls.",
                reviewer="customer", reason="Write plainly")
    first = store.feedback(**args)
    assert store.feedback(**args) == first
    assert store.metrics(brand="acme")["reviewed_assets"] == 1
    assert store.packet(brand="acme", writer="founder", channel="linkedin")["rules"] == ["Use plain sentences."]
    with pytest.raises(ValueError):
        store.feedback(**dict(args, brand="other"))


def test_cache_isolation_and_copy_safety(store):
    clear_cache()
    profile(store)
    a = store.packet(brand="acme", writer="founder", channel="linkedin")
    b = dict(a, brand="other", banned_phrases=[], version="other")
    async def run():
        first = await QualityEngine(use_llm=False, brand_id="acme", voice_profile=a).score_content("An enterprise-grade system.", "a.md")
        second = await QualityEngine(use_llm=False, brand_id="other", voice_profile=b).score_content("An enterprise-grade system.", "b.md")
        def voice(r):
            return next(rule for c in r.categories for rule in c.rules if rule.rule_id == "VC-01")
        assert not voice(first).passed and voice(second).passed
        assert first.file_path == "a.md" and second.file_path == "b.md"
        first.metadata["poison"] = True
        again = await QualityEngine(use_llm=False, brand_id="acme", voice_profile=a).score_content("An enterprise-grade system.", "a.md")
        assert "poison" not in again.metadata
        assert evaluate_proposal(first, {"auto_approve_above": 0})["status"] == "rejected"
    asyncio.run(run())
    with pytest.raises(ValueError, match="belong"):
        QualityEngine(brand_id="other", voice_profile=a)


def test_no_ambient_home_profile(monkeypatch, tmp_path):
    from scripts.quality.rules.voice_consistency import VoiceConsistencyRule
    from scripts.quality.parser import parse_markdown
    monkeypatch.setattr("pathlib.Path.home", lambda: tmp_path)
    (tmp_path / ".kai-marketing").mkdir()
    (tmp_path / ".kai-marketing/voice.md").write_text("# Banned\n- ordinary\n")
    assert VoiceConsistencyRule().evaluate(parse_markdown("An ordinary sentence.")).passed


def test_judge_does_not_see_preference_labels(store):
    profile(store)
    example(store, split="holdout")
    def judge(prompt):
        assert "Too corporate" not in prompt
        assert '"accepted"' not in prompt
        data = json.loads(prompt[prompt.index('{"profile"'):])
        return json.dumps({"choice": "A" if data["A"] == "Customer copy" else "B", "evidence": "Customer copy"})
    result = calibrate(store, brand="acme", writer="founder", channel="linkedin", judge=judge)
    assert result["agreement"] == 1
    assert result["automatic_promotion"] is False


def test_voice_judge_rejects_fabricated_quotes():
    packet = dict(version="v")
    with pytest.raises(ValueError, match="invented"):
        review_draft(packet, "Real sentence.", lambda _: json.dumps(
            {"verdict": "FAIL", "issues": [{"quote": "fake", "rule": "tone", "direction": "fix"}]}))


def test_uncalibrated_voice_review_cannot_autoapprove(store):
    profile(store)
    async def run():
        packet = store.packet(brand="acme", writer="founder", channel="linkedin")
        report = await QualityEngine(use_llm=False, brand_id="acme", voice_profile=packet).score_content("Plain words.")
        assert evaluate_proposal(report, {"auto_approve_above": 0})["status"] == "pending"
    asyncio.run(run())


def test_replay_never_publishes(store):
    store.record(brand="acme", run_id="r", kind="llm", data=dict(
        stage="content_pipeline", model="old", prompt="brief", prompt_hash="h", output="original"))
    result = compare_replay(store, brand="acme", run_id="r", candidate=lambda p: "new " + p)
    assert result["candidate"] == "new brief" and not result["published"]
    with pytest.raises(ValueError):
        compare_replay(store, brand="other", run_id="r", candidate=lambda p: "bad")


def test_content_routes_by_stage_and_retains_usage():
    from agent.llm.content import ContentClient
    calls = []
    router = NS(_detect_provider=lambda: "fake", get_model_for_task=lambda task: task,
                _call_provider=lambda **kw: (calls.append(kw) or ("draft", {"total_tokens": 3}, "stop")))
    client = ContentClient(router=router)
    assert client.for_task("content_revision")("fix one sentence") == "draft"
    assert client.events[0]["stage"] == "content_revision"
    assert calls[0]["model"] == "content_revision"


def test_bound_outcome_matches_asset_and_brand(tmp_path, monkeypatch):
    from datetime import datetime, timedelta, timezone
    import kai.analytics.rl as rl
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    monkeypatch.setattr(rl, "utcnow", lambda: clock[0].isoformat())
    p = rl.OutcomePolicy(tmp_path / "rl.sqlite")
    d = p.choose(brand_id="acme", metric="signups", actions=["content_pipeline"],
                 baseline=10, scale=10, direction="increase", actor="writer",
                 baseline_at="2025-12-31T00:00:00Z", evidence_ref="baseline", window_days=1)
    binding = p.bind_execution(decision_id=d["decision_id"], brand_id="acme", run_id="r",
                               content_hash="hash", receipt_ref="receipt", action="content_pipeline",
                               executed_at=clock[0].isoformat())
    with pytest.raises(ValueError, match="already"):
        p.bind_execution(decision_id=d["decision_id"], brand_id="acme", run_id="other",
                         content_hash="hash", receipt_ref="receipt", action="content_pipeline",
                         executed_at=clock[0].isoformat())
    s = VoiceStore(tmp_path / "voice.sqlite")
    s.record(brand="acme", run_id="r", kind="execution", data=dict(decision_id=d["decision_id"], **binding))
    clock[0] += timedelta(days=2)
    assert s.outcome(brand="acme", run_id="r", rl_db=p.path, decision_id=d["decision_id"],
                     value=15, observed_at=clock[0].isoformat(), verifier="collector",
                     evidence_ref="metrics") == 0.5
    assert s.metrics(brand="acme")["business_outcomes"][0]["reward"] == 0.5


def test_rule_references_must_be_in_customer_evidence():
    with pytest.raises(ValueError, match="customer rule"):
        review_draft(dict(version="v", rules=["Be specific."]), "Real words.", lambda _: json.dumps(
            {"verdict": "FAIL", "issues": [{"quote": "Real", "rule": "Use slang", "direction": "fix"}]}))


def test_experiment_reservation_prevents_double_execution(tmp_path):
    from kai.analytics.rl import OutcomePolicy, utcnow
    p = OutcomePolicy(tmp_path / "rl.sqlite")
    d = p.choose(brand_id="acme", metric="signups", actions=["content_pipeline"],
                 baseline=10, scale=10, direction="increase", actor="writer",
                 baseline_at=utcnow(), evidence_ref="baseline", window_days=1)
    p.reserve_run(decision_id=d["decision_id"], brand_id="acme", run_id="r", action="content_pipeline")
    with pytest.raises(ValueError, match="reserved"):
        p.reserve_run(decision_id=d["decision_id"], brand_id="acme", run_id="r2", action="content_pipeline")


def test_unknown_cost_not_reported_as_free(store):
    store.record(brand="acme", run_id="r", kind="feedback", data=dict(accepted=True, edit_fraction=0))
    store.record(brand="acme", run_id="r", kind="llm", data=dict(estimated_cost_usd=None))
    assert store.metrics(brand="acme")["estimated_cost_per_accepted_asset"] is None
    assert store.metrics(brand="acme")["calls_with_unknown_cost"] == 1
