"""Tests for the Jev-typed decision log and its learning loop."""

from __future__ import annotations

import json
from dataclasses import replace
from datetime import datetime, timedelta, timezone

import pytest

from scripts.autonomy import decision_log as dl

CHANNEL = dl.Question(
    question_id="next_channel",
    type="choice",
    instructions="Which channel does the brief name as the lead source?",
    criteria=(("email", "email is named"), ("seo", "search is named")),
)
HAS_PRICE = dl.Question(question_id="has_price", type="noul", instructions="The page shows a dollar price.")
PRED = dl.Prediction(metric="revenue", baseline=100.0, target=150.0, window_days=30)
LATER = (datetime.now(timezone.utc) + timedelta(seconds=5)).isoformat(timespec="seconds")


@pytest.fixture
def log(tmp_path, monkeypatch):
    monkeypatch.setenv("KAI_AUTONOMY_DIR", str(tmp_path))
    return tmp_path / "decisions.jsonl"


def make(i: int, choice: str, **kw) -> dl.Decision:
    base = dict(
        decision_id=f"d{i}", kind="channel", subject=f"brand-{i}", options=("email", "seo"), choice=choice,
        rationale="test", prediction=PRED, actor="planner",
    )
    base.update(kw)
    return dl.Decision(**base)


def record(i: int, choice: str, observed: float, label: str = "", **kw) -> None:
    dl.decide(make(i, choice, **kw))
    dl.observe(dl.Outcome(decision_id=f"d{i}", observed=observed, source="stripe", verifier="reviewer", label=label, observed_at=LATER))


# -- types ---------------------------------------------------------------

def test_prediction_must_be_an_outcome_metric():
    with pytest.raises(dl.DecisionLogError, match="not an outcome metric"):
        dl.Prediction(metric="sessions", baseline=1, target=2, window_days=7)


def test_prediction_target_must_move_in_direction():
    with pytest.raises(dl.DecisionLogError, match="does not increase"):
        dl.Prediction(metric="leads", baseline=10, target=5, window_days=7)


def test_choice_must_be_an_option():
    with pytest.raises(dl.DecisionLogError, match="not one of the options"):
        make(1, "tiktok")


def test_model_decision_pins_question_and_confidence():
    with pytest.raises(dl.DecisionLogError, match="pin question_id"):
        make(1, "email", model="typesafe/jev-1.13")


def test_question_version_changes_with_wording():
    reworded = replace(CHANNEL, instructions="Which channel is named first?")
    assert reworded.version != CHANNEL.version


def test_jev_answer_rejects_bad_distribution():
    with pytest.raises(dl.DecisionLogError, match="sum to"):
        dl.JevAnswer.parse(CHANNEL, {"probabilities": {"email": 0.9, "seo": 0.9}})
    with pytest.raises(dl.DecisionLogError, match="unknown options"):
        dl.JevAnswer.parse(CHANNEL, {"probabilities": {"email": 0.5, "tiktok": 0.5}})


def test_gate_choice_needs_confidence_and_margin():
    sure = dl.JevAnswer.parse(CHANNEL, {"probabilities": {"email": 0.8, "seo": 0.2}})
    close = dl.JevAnswer.parse(CHANNEL, {"probabilities": {"email": 0.55, "seo": 0.45}})
    assert sure.passes(0.60)
    assert not close.passes(0.60)
    assert not sure.passes(0.85)


def test_gate_noul_uses_distance_from_half():
    assert dl.JevAnswer.parse(HAS_PRICE, {"noul": 0.75}).passes(0.60)  # p >= 0.70
    assert dl.JevAnswer.parse(HAS_PRICE, {"noul": 0.25}).passes(0.60)  # p <= 0.30
    assert not dl.JevAnswer.parse(HAS_PRICE, {"noul": 0.65}).passes(0.60)


# -- log -----------------------------------------------------------------

def test_decider_cannot_verify_own_outcome(log):
    dl.decide(make(1, "email"))
    with pytest.raises(dl.DecisionLogError, match="may not verify"):
        dl.observe(dl.Outcome(decision_id="d1", observed=120, source="stripe", verifier="planner", observed_at=LATER))


def test_outcome_cannot_predate_decision(log):
    dl.decide(make(1, "email"))
    with pytest.raises(dl.DecisionLogError, match="before the decision"):
        dl.observe(dl.Outcome(decision_id="d1", observed=120, source="stripe", verifier="r", observed_at="2020-01-01T00:00:00+00:00"))


def test_corrupt_line_names_file_and_line(log):
    dl.decide(make(1, "email"))
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"schema": dl.SCHEMA, "event": "decided", "decision": {"decision_id": "x"}}) + "\n")
    with pytest.raises(dl.DecisionLogError, match=r"decisions.jsonl:2"):
        dl.load()


def test_grade_and_lift():
    assert dl.grade(PRED, 160) == "hit"
    assert dl.grade(PRED, 120) == "partial"
    assert dl.grade(PRED, 90) == "miss"
    assert dl.lift(PRED, 150) == 0.5


# -- Jev decisions -------------------------------------------------------

def test_decide_with_jev_records_or_escalates(log, monkeypatch):
    answers = iter([
        {"model": "typesafe/jev-1.13", "answers": {"next_channel": {"probabilities": {"email": 0.9, "seo": 0.1}}}},
        {"model": "typesafe/jev-1.13", "answers": {"next_channel": {"probabilities": {"email": 0.52, "seo": 0.48}}}},
    ])
    monkeypatch.setattr(dl, "ask_jev", lambda *a, **k: next(answers))
    kw = dict(kind="channel", subject="acme", state_text="brief", question=CHANNEL, prediction=PRED, actor="planner")
    decision = dl.decide_with_jev(**kw)
    assert decision and decision.choice == "email" and decision.gate_floor == dl.GATE_FLOOR
    assert decision.question_version == CHANNEL.version
    assert dl.decide_with_jev(**kw) is None
    state = dl.load()
    assert len(state.decisions) == 1 and state.escalations == 1


def test_mock_backend_is_deterministic_and_typed(log):
    a = dl.ask_jev("same state", [CHANNEL, HAS_PRICE], backend="mock")
    b = dl.ask_jev("same state", [CHANNEL, HAS_PRICE], backend="mock")
    assert a == b
    dl.JevAnswer.parse(CHANNEL, a["answers"]["next_channel"])
    dl.JevAnswer.parse(HAS_PRICE, a["answers"]["has_price"])


def test_retired_question_refused(log):
    with open(log, "a", encoding="utf-8") as handle:
        handle.write(json.dumps({"schema": dl.SCHEMA, "event": "question_retired", "question": f"next_channel@{CHANNEL.version}"}) + "\n")
    with pytest.raises(dl.DecisionLogError, match="retired"):
        dl.decide_with_jev(kind="channel", subject="a", state_text="s", question=CHANNEL, prediction=PRED, actor="p", backend="mock")


# -- learning ------------------------------------------------------------

def test_learn_accepts_lesson_only_with_evidence(log):
    for i in range(5):
        record(i, "email", 200 + i)
        record(100 + i, "seo", 100 + i)
    assert dl.learn(min_n=10)["accepted"] == []  # too few
    for i in range(5, 12):
        record(i, "email", 200 + i)
        record(100 + i, "seo", 100 + i)
    result = dl.learn(min_n=10)
    lessons = {dl.load().lessons[lid].choice: dl.load().lessons[lid].stance for lid in result["accepted"]}
    assert lessons == {"email": "prefer", "seo": "avoid"}


def test_learn_retires_lesson_that_stops_paying(log):
    lesson = dl.Lesson("lsn-1", "channel", "prefer", "email", "revenue", 1.0, 0.01, 10, 10, ("d0",))
    dl._append("lesson_accepted", {"lesson": dl.asdict(lesson)})
    for i in range(10):
        record(i, "email", 100, lesson_refs=("lsn-1",))
        record(100 + i, "seo", 200 + i)
    result = dl.learn(min_n=10, max_new=0)
    assert result["retired"] == ["lsn-1"]
    assert not dl.load().active_lessons()


def test_gate_tightens_then_question_retires(log):
    model = dict(model="typesafe/jev-1.13", question_id="next_channel", question_version=CHANNEL.version, confidence=0.99)
    key = f"next_channel@{CHANNEL.version}"
    n = 0
    floor = dl.GATE_FLOOR
    while True:
        for _ in range(10):  # 50% right at every floor
            record(n, "email", 100, label="email" if n % 2 else "seo", gate_floor=floor, **model)
            n += 1
        result = dl.learn(min_n=10, max_new=0)
        if result["questions_retired"]:
            break
        floor = result["gates"][key]
        assert dl.GATE_FLOOR < floor <= dl.GATE_CEILING
    assert result["questions_retired"] == [key]
    assert floor == dl.GATE_CEILING


def test_gate_loosens_when_accurate(log):
    model = dict(model="typesafe/jev-1.13", question_id="next_channel", question_version=CHANNEL.version, confidence=0.99)
    key = f"next_channel@{CHANNEL.version}"
    dl._append("gate_tuned", {"question": key, "floor": 0.7})
    for i in range(10):
        record(i, "email", 100, label="email", gate_floor=0.7, **model)
    assert dl.learn(min_n=10, max_new=0)["gates"] == {key: 0.65}


def test_learn_stalls_without_new_evidence(log):
    record(1, "email", 120)
    for _ in range(3):
        assert not dl.learn()["stalled"]
    assert dl.learn()["stalled"]
    record(2, "seo", 90)
    assert not dl.learn()["stalled"]


def test_outcome_from_kai_data(tmp_path):
    path = tmp_path / "kai-data.json"
    path.write_text(json.dumps({"metrics": [{"metric_id": "stripe_net_revenue", "value": {"usd": 795.0}, "source_id": "stripe"}]}))
    value, source = dl.outcome_from_kai_data(path, "stripe_net_revenue")
    assert value == 795.0 and "stripe_net_revenue" in source
    with pytest.raises(dl.DecisionLogError, match="data gap"):
        dl.outcome_from_kai_data(path, "crm_deals_won")
    with pytest.raises(dl.DecisionLogError, match="not an outcome metric id"):
        dl.outcome_from_kai_data(path, "ga4_sessions")


def test_cli_status_and_ask_mock(log, tmp_path, capsys):
    spec = tmp_path / "ask.json"
    spec.write_text(json.dumps({
        "kind": "channel", "subject": "acme", "state": "brief text", "actor": "planner",
        "question": {"id": "next_channel", "type": "choice", "instructions": CHANNEL.instructions, "criteria": dict(CHANNEL.criteria)},
        "prediction": {"metric": "leads", "baseline": 4, "target": 8, "window_days": 30},
    }))
    assert dl.main(["ask", str(spec), "--mock"]) == 0
    assert dl.main(["status"]) == 0
    out = capsys.readouterr().out
    assert '"decisions"' in out
