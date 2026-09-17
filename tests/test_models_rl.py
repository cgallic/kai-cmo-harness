"""Offline transport contracts and outcome-policy regression cases."""
import asyncio
import json
import random
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace as NS

import pytest

from agent.llm.router import LLMRouter
from kai.analytics.rl import OutcomePolicy


def test_reasoning_responses_transport(monkeypatch):
    router = LLMRouter()
    router._provider = router._client_provider = "openai"
    calls = []
    router._client = NS(responses=NS(create=lambda **kw: (
        calls.append(kw) or NS(status="completed", output_text="result",
                              usage=NS(input_tokens=2, output_tokens=3, total_tokens=5))
    )))
    result, usage, _ = router._call_provider(
        model="gpt-6-astra", messages=[{"role": "user", "content": "test"}],
        max_tokens=4096, temperature=0.2)
    assert result == "result" and usage["total_tokens"] == 5
    assert "temperature" not in calls[0]
    assert calls[0]["max_output_tokens"] == 4096


def test_incomplete_reasoning_response_rejected():
    router = LLMRouter()
    router._provider = router._client_provider = "openai"
    router._client = NS(responses=NS(create=lambda **kw: NS(status="incomplete")))
    with pytest.raises(RuntimeError, match="did not complete"):
        router._call_provider(model="gpt-5.6-luna", messages=[], max_tokens=1, temperature=0.7)


def test_openrouter_sonnet_omits_sampling():
    router = LLMRouter()
    router._provider = router._client_provider = "openrouter"
    calls = []
    router._client = NS(chat=NS(completions=NS(create=lambda **kw: (
        calls.append(kw) or NS(choices=[NS(message=NS(content="ok"))], usage=None)
    ))))
    router._call_provider(model="anthropic/claude-sonnet-5", messages=[],
                          max_tokens=4096, temperature=0.2)
    assert "temperature" not in calls[0]


def test_native_anthropic_omits_sampling(monkeypatch):
    import agent.llm.router as mod
    calls = []
    monkeypatch.setattr(mod.requests, "post", lambda *a, **kw: (
        calls.append(kw) or NS(raise_for_status=lambda: None,
                              json=lambda: {"content": [{"type": "text", "text": "ok"}]})
    ))
    router = LLMRouter()
    router._complete_anthropic(model="claude-sonnet-5", messages=[],
                               max_tokens=4096, temperature=0.2)
    assert "temperature" not in calls[0]["json"]


def test_gemini_preserves_roles_and_output_budget(monkeypatch):
    import agent.llm.router as mod
    calls = []
    monkeypatch.setattr(mod, "_google_genai", NS(Client=lambda **kw: NS(
        models=NS(generate_content=lambda **kw: (
            calls.append(kw) or NS(text="ok", usage_metadata=None)
        )))))
    LLMRouter()._complete_gemini(
        model="gemini-3.8-flash", max_tokens=123, temperature=1,
        messages=[{"role": "system", "content": "rules"},
                  {"role": "user", "content": "hi"}, {"role": "assistant", "content": "hello"}])
    assert calls[0]["config"]["max_output_tokens"] == 123
    assert calls[0]["config"]["system_instruction"] == "rules"
    assert [c["role"] for c in calls[0]["contents"]] == ["user", "model"]


@pytest.fixture
def policy(tmp_path, monkeypatch):
    import kai.analytics.rl as rl
    clock = [datetime(2026, 1, 1, tzinfo=timezone.utc)]
    monkeypatch.setattr(rl, "utcnow", lambda: clock[0].isoformat())
    return OutcomePolicy(tmp_path / "rl.db"), clock


def choose(p, **kw):
    args = dict(brand_id="kai", metric="paid_signups", actions=["a", "b"],
                baseline=10, scale=10, direction="increase", actor="writer",
                baseline_at="2025-12-31T00:00:00+00:00", evidence_ref="baseline:1",
                window_days=1, rng=random.Random(1), min_samples=1)
    args.update(kw)
    return p.choose(**args)


def observation(record, **kw):
    args = dict(decision_id=record["decision_id"], value=20,
                executed_at=record["created_at"],
                observed_at=(datetime.fromisoformat(record["created_at"]) + timedelta(days=1)).isoformat(),
                verifier="collector", evidence_ref="measurement:1", executed_action=record["action"])
    args.update(kw)
    return args


def test_policy_learns_and_isolates_brand(policy):
    p, clock = policy
    first = choose(p, actions=["a"])
    second = choose(p, actions=["b"])
    clock[0] += timedelta(days=2)
    assert p.observe(**observation(first)) == 1
    assert p.observe(**observation(second, value=0)) == -1
    decision = choose(p)
    assert decision["probabilities"] == pytest.approx({"a": 0.95, "b": 0.05})
    assert choose(p, brand_id="other")["probabilities"] == {"a": 0.5, "b": 0.5}
    assert choose(p, metric="clicks")["mode"] == "cold_start"


def test_feedback_idempotency_and_conflict(policy):
    p, clock = policy
    record = choose(p)
    clock[0] += timedelta(days=2)
    payload = observation(record)
    assert p.observe(**payload) == p.observe(**payload)
    with pytest.raises(ValueError, match="conflicting"):
        p.observe(**dict(payload, value=30))
    assert len(p.export()) == 1


@pytest.mark.parametrize("change,match", [
    ({"verifier": "writer"}, "producer"),
    ({"value": float("nan")}, "finite"),
    ({"executed_action": "wrong"}, "does not match"),
    ({"cost": -1}, "nonnegative"),
    ({"cost": 2}, "predeclared"),
    ({"evidence_ref": ""}, "required"),
    ({"observed_at": "2026-01-01T12:00:00+00:00"}, "matured"),
    ({"executed_at": "2025-12-31T00:00:00+00:00"}, "execution"),
])
def test_bad_feedback_cannot_train(policy, change, match):
    p, clock = policy
    record = choose(p)
    clock[0] += timedelta(days=2)
    with pytest.raises(ValueError, match=match):
        p.observe(**observation(record, **change))
    assert p.export()[0]["reward"] is None


def test_decrease_metric_cost_and_scale(policy):
    p, clock = policy
    record = choose(p, direction="decrease", cost_budget=100)
    clock[0] += timedelta(days=2)
    assert p.observe(**observation(record, value=5, cost=10)) == pytest.approx(0.4)
    assert choose(p, scale=20)["mode"] == "cold_start"


def test_pending_is_not_negative_and_restart_replays(policy):
    p, _ = policy
    choose(p)
    assert choose(p)["mode"] == "cold_start"
    assert len(OutcomePolicy(p.path).export()) == 2


def test_decomposer_connects_policy(policy, monkeypatch):
    from agent.decomposer import GoalDecomposer, llm_router
    from kai.runtime.models import KaiGoal
    p, _ = policy
    monkeypatch.setenv("KAI_RL_DB", str(p.path))
    async def complete(prompt, **kwargs):
        assert "Predeclared outcome-learning experiment" in prompt
        return json.dumps({"nodes": [{"node_id": "n", "task_type": "content_pipeline"}], "edges": []})
    monkeypatch.setattr(llm_router, "complete", complete)
    goal = KaiGoal(goal_id="g", name="signups", target_value=20, current_value=10, brand_id="kai", kpi_name="paid_signups", target_direction="increase",
                   metadata={"rl_experiment": dict(actions=["content_pipeline"],
                       baseline=10, scale=10, actor="writer",
                       baseline_at="2025-12-31T00:00:00+00:00", evidence_ref="baseline:1")})
    graph = asyncio.run(GoalDecomposer().decompose(goal))
    assert graph.nodes["n"].inputs["rl_decision_id"] == p.export()[0]["decision_id"]


def test_unknown_model_cost_is_not_free():
    assert LLMRouter().estimate_cost(1000, 1000, model="new-model") is None
    assert LLMRouter().estimate_cost(1_000_000, 1_000_000, model="gpt-6-astra") == 60


def test_legacy_chat_sampling_preserved():
    router = LLMRouter()
    router._provider = router._client_provider = "openai"
    calls = []
    router._client = NS(chat=NS(completions=NS(create=lambda **kw: (
        calls.append(kw) or NS(choices=[NS(message=NS(content="ok"))], usage=None)
    ))))
    router._call_provider(model="gpt-4.1", messages=[], max_tokens=512, temperature=0.2)
    assert calls[0]["temperature"] == 0.2
    assert calls[0]["max_tokens"] == 512


def test_concurrent_feedback_settles_once(policy):
    from concurrent.futures import ThreadPoolExecutor
    p, clock = policy
    record = choose(p)
    clock[0] += timedelta(days=2)
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _: p.observe(**observation(record)), range(8)))
    assert results == [1] * 8
    assert len(p.export()) == 1
