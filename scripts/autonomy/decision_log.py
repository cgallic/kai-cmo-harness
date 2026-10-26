#!/usr/bin/env python3
"""Decision log: Jev-typed decisions, graded on revenue, that tune themselves.

Kai routes findings (``decisions.py``), logs runs (``ledger.py``) and grades
content (``performance_check.py``), but nothing recorded *a choice, how sure the
model was, and what it was expected to earn*, so nothing could learn which
choices make money or when the decider can be trusted. This module does.

Decisions are made by **Jev**, TypeSafe's System One decision model: text state
in, typed answers out (``choice`` with a probability per option, ``noul`` yes/no
probability, ``score`` on a rubric). Jev never writes prose. Each answer passes a
confidence gate; a confident answer becomes a ``Decision``, an unsure one is an
``escalated`` event for a human or a stronger model. Humans and other models can
record decisions too (``model="human"``).

  decide    typed Decision: options, choice, Jev probabilities, and a
            prediction (outcome metric, baseline, target, window) fixed first
  observe   an Outcome read by someone other than the decider, optionally with
            the true answer to the Jev question (``label``)
  learn     one pass, three loops:
            1. choice lessons: a choice that beats the other choices for a kind
               (min_n per side, min_delta lift, Welch p < p_threshold)
            2. lesson retirement: decisions that followed a lesson must keep
               beating those that did not
            3. gate tuning: per question version, gated answers checked against
               true labels; below ``target_accuracy`` the gate tightens, and a
               question still wrong at the ceiling is retired so it must be
               reworded (a new version) before Jev may decide with it again

Models: answers come from a pinned System One model (``jev-1.14`` default,
``jev-1.13``, or a local Laya checkpoint). Gates are per question version and
model; ``shadow`` models answer the same question without deciding and are
graded on the same labels, and ``route_model`` moves a question to the model
that measurably answers it best.

Everything is an append-only event log (``data/autonomy/decisions.jsonl``,
``KAI_AUTONOMY_DIR`` override) folded on read like the approval queue. Writes
raise; every line is re-validated into frozen dataclasses on read.

Guardrails on the recursion:
  - predictions name an outcome metric (revenue, leads, bookings...), never
    activity: the Revenue Lens, enforced by type
  - the outcome verifier may not be the decider (ECO independence rule)
  - nothing is learned without min_n, min_delta and significance
  - lesson depth (lessons from decisions that followed lessons) is capped
  - gates only tighten on evidence and loosen back no lower than the default
  - after ``stall_limit`` passes with no change and no new outcome, ``learn``
    stops until new evidence arrives
  - lessons reach ``memory/lessons.md`` only with ``--apply``
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import random
import sys
import time
import urllib.error
import urllib.request
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal, get_args

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.autonomy.decisions import ACTION_CLASSES  # noqa: E402

SCHEMA = "kai.decision-event.v1"

OutcomeMetric = Literal[
    "revenue",
    "leads",
    "qualified_leads",
    "bookings",
    "paid_customers",
    "won_deals",
    "lead_to_won_rate",
    "step_conversion",
]
Direction = Literal["increase", "decrease"]
QuestionType = Literal["choice", "noul", "score"]
EventType = Literal[
    "decided", "escalated", "shadowed", "observed", "lesson_accepted", "lesson_retired",
    "gate_tuned", "question_retired", "learn_pass",
]
Grade = Literal["hit", "partial", "miss"]

OUTCOME_METRICS: tuple[str, ...] = get_args(OutcomeMetric)
EVENT_TYPES: tuple[str, ...] = get_args(EventType)

# Confidence gate, same defaults as cmo_agent scripts/jev_label and
# connorgallic.com/ask. Choice: confidence >= floor and the leader at least
# MARGIN ahead. Noul: confidence is |2p - 1| (TypeSafe's recommendation), so
# 0.4 means p >= 0.7 or p <= 0.3.
GATE_FLOOR = 0.60
GATE_CEILING = 0.95
GATE_STEP = 0.05
MARGIN_MIN = 0.20

JEV_URL = os.environ.get("JEV_URL", "https://openrouter.ai/api/v1/systemone")
LAYA_URL = os.environ.get("LAYA_BASE_URL", "")  # e.g. the agent box laya.service; unset = local `laya` package

# System One models. Ids are pinned versions, never ``jev-latest``: gates are
# tuned per model, and an alias that moves on release would silently reuse a
# floor learned on another model. Sources: docs.typesafe.ai/models.md,
# openrouter.ai/api/v1/models (checked 2026-10-26); Laya model card.
MODELS: dict[str, dict[str, Any]] = {
    "jev-1.14": {"openrouter": "typesafe/jev-1.14", "direct": "jev-1.14.0", "released": "2026-10-14",
                 "note": "current TypeSafe model; better multilingual; same price as 1.13"},
    "jev-1.13": {"openrouter": "typesafe/jev-1.13", "direct": "jev-1.13.0", "released": "2026-09-17",
                 "note": "first Jev; literal, weak on counts/dates, leans to the first choice option"},
    "laya/typed-decisions": {"laya": "typed-decisions", "note": "open-source, local, fine-tuned (0.766 vs 0.362 base on its own benchmark), 512 tokens"},
    "laya/english": {"laya": "english", "note": "open-source base checkpoint, near chance zero-shot"},
    "laya/multilingual": {"laya": "multilingual", "note": "open-source base checkpoint, 100+ languages, 1k tokens"},
}
DEFAULT_MODEL = os.environ.get("JEV_MODEL", "jev-1.14")

# Collector metric ids (scripts/audit/collect.py --revenue) that can settle a
# prediction straight from kai-data.json.
KAI_DATA_METRICS: dict[str, str] = {
    "stripe_net_revenue": "revenue",
    "stripe_paying_customers": "paid_customers",
    "crm_new_leads": "leads",
    "crm_deals_won": "won_deals",
    "crm_won_revenue": "revenue",
    "crm_lead_to_won_rate": "lead_to_won_rate",
    "bookings_held_or_upcoming": "bookings",
}


class DecisionLogError(ValueError):
    """A record or event that would make the log lie."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _parse_time(value: str, name: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value)
    except (TypeError, ValueError) as exc:
        raise DecisionLogError(f"{name} is not ISO-8601: {value!r}") from exc
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise DecisionLogError(message)


def _number(value: Any, name: str) -> float:
    _require(isinstance(value, (int, float)) and not isinstance(value, bool), f"{name} must be a number")
    return float(value)


def _unit(value: Any, name: str) -> float:
    number = _number(value, name)
    _require(0.0 <= number <= 1.0, f"{name} must be within 0..1")
    return number


# --------------------------------------------------------------------------
# Jev questions and answers
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Question:
    """One Jev question. ``version`` pins the exact wording that was asked.

    Write questions about visible features, not judgments ("the first line has
    a $ figure", not "is the hook good"): that wording moved a labeling test
    from 34-43% wrong to 97-99% right.
    """

    question_id: str
    type: QuestionType
    instructions: str
    criteria: tuple[tuple[str, str], ...] = ()  # choice: (key, meaning); score: ("0", level)...

    def __post_init__(self) -> None:
        _require(bool(self.question_id.strip()), "question_id is required")
        _require(self.type in get_args(QuestionType), f"type must be one of {get_args(QuestionType)}")
        _require(bool(self.instructions.strip()), "instructions are required")
        if self.type == "noul":
            _require(not self.criteria, "noul questions take no criteria")
        else:
            keys = [k for k, _ in self.criteria]
            _require(len(keys) >= 2 and len(set(keys)) == len(keys), f"{self.type} needs two or more distinct criteria")

    @property
    def version(self) -> str:
        blob = json.dumps([self.type, self.instructions, list(self.criteria)], sort_keys=True)
        return hashlib.sha256(blob.encode()).hexdigest()[:12]

    @property
    def options(self) -> tuple[str, ...]:
        return ("yes", "no") if self.type == "noul" else tuple(k for k, _ in self.criteria)

    def payload(self) -> dict[str, Any]:
        body: dict[str, Any] = {"type": self.type, "instructions": self.instructions}
        if self.type == "choice":
            body["criteria"] = dict(self.criteria)
        elif self.type == "score":
            body["criteria"] = [meaning for _, meaning in self.criteria]
        return body

    @classmethod
    def from_dict(cls, question_id: str, data: dict[str, Any]) -> "Question":
        criteria = data.get("criteria") or ()
        if isinstance(criteria, dict):
            pairs = tuple((str(k), str(v)) for k, v in criteria.items())
        else:
            pairs = tuple((str(i), str(v)) for i, v in enumerate(criteria))
        return cls(question_id=question_id, type=data.get("type", ""), instructions=data.get("instructions", ""), criteria=pairs)


@dataclass(frozen=True)
class JevAnswer:
    """A validated Jev answer: the answer, the distribution, and the confidence."""

    question_id: str
    answer: str
    probabilities: tuple[tuple[str, float], ...]
    confidence: float
    margin: float
    type: QuestionType = "choice"

    @classmethod
    def parse(cls, question: Question, raw: dict[str, Any]) -> "JevAnswer":
        _require(isinstance(raw, dict), f"{question.question_id}: answer must be an object")
        if question.type == "noul":
            p = _unit(raw.get("noul"), f"{question.question_id}.noul")
            answer = "yes" if p >= 0.5 else "no"
            confidence = abs(2 * p - 1)
            return cls(question.question_id, answer, (("yes", p), ("no", 1 - p)), round(confidence, 4), round(confidence, 4), "noul")
        probs = raw.get("probabilities") or {}
        if question.type == "score" and isinstance(probs, list):
            probs = {str(i): v for i, v in enumerate(probs)}
        _require(isinstance(probs, dict) and probs, f"{question.question_id}: probabilities missing")
        dist = {str(k): _unit(v, f"{question.question_id}.probabilities[{k}]") for k, v in probs.items()}
        _require(set(dist) <= set(question.options), f"{question.question_id}: unknown options {sorted(set(dist) - set(question.options))}")
        _require(abs(sum(dist.values()) - 1.0) <= 0.02, f"{question.question_id}: probabilities sum to {sum(dist.values()):.3f}")
        ranked = sorted(dist.items(), key=lambda kv: -kv[1])
        if question.type == "choice":
            answer = str(raw.get("choice") or ranked[0][0])
            _require(answer in question.options, f"{question.question_id}: choice {answer!r} not in criteria")
        else:
            answer = str(int(round(_number(raw.get("score", ranked[0][0]), f"{question.question_id}.score"))))
        confidence = _unit(raw.get("confidence", ranked[0][1]), f"{question.question_id}.confidence")
        margin = ranked[0][1] - (ranked[1][1] if len(ranked) > 1 else 0.0)
        return cls(question.question_id, answer, tuple(ranked), round(confidence, 4), round(margin, 4), question.type)

    def passes(self, floor: float) -> bool:
        if self.type == "noul":
            return self.confidence >= _noul_floor(floor)
        return self.confidence >= floor and self.margin >= MARGIN_MIN


def _noul_floor(floor: float) -> float:
    """Map the choice-scale floor (0.60 default) onto |2p-1| (0.40 = p 0.70)."""
    return round(2 * (floor + 0.10) - 1, 4)


def canonical_model(name: str) -> str:
    """Map any spelling (typesafe/jev-1.13-20260917, jev-1.14.0, laya) to a MODELS id."""
    raw = name.strip().lstrip("~")
    _require("latest" not in raw and "preview" not in raw, f"{name!r} is an alias; pin a version from {sorted(MODELS)}")
    if raw in MODELS:
        return raw
    if raw.startswith("laya"):
        tail = raw.split("/", 1)[1] if "/" in raw else "english"
        key = f"laya/{tail.removeprefix('laya-')}"
    else:
        tail = raw.removeprefix("typesafe/")
        parts = tail.split("-")
        if len(parts) > 2 and parts[-1].isdigit():  # dated OpenRouter slug
            tail = "-".join(parts[:-1])
        key = tail[:-2] if tail.count(".") == 2 and tail.endswith(".0") else tail
    _require(key in MODELS, f"unknown System One model {name!r}; known: {sorted(MODELS)}")
    return key


def ask_jev(state: str, questions: list[Question], *, model: str = "", backend: str = "jev", retries: int = 4) -> dict[str, Any]:
    """Ask every question in one System One call. ``backend="mock"`` is offline."""
    model = canonical_model(model or DEFAULT_MODEL)
    if backend == "mock":
        rng = random.Random(hashlib.sha256(f"{model}|{state}".encode()).hexdigest())
        answers: dict[str, Any] = {}
        for q in questions:
            if q.type == "noul":
                answers[q.question_id] = {"type": "noul", "noul": rng.random()}
            else:
                weights = [rng.random() ** 3 for _ in q.options]
                probs = {o: w / sum(weights) for o, w in zip(q.options, weights)}
                best = max(probs, key=probs.get)
                answers[q.question_id] = {"type": q.type, "choice": best, "score": float(best) if q.type == "score" else None,
                                          "probabilities": probs, "confidence": probs[best]}
        return {"model": model, "answers": answers}
    spec = MODELS[model]
    payload = {q.question_id: q.payload() for q in questions}
    if "laya" in spec:
        if not LAYA_URL:
            from laya import Router  # pip install laya; downloads weights once

            res = Router().predict(state, payload, model=spec["laya"])
            return {"model": model, "answers": res["answers"]}
        url, headers = LAYA_URL, {"Content-Type": "application/json"}
        body = json.dumps({"state": state, "model": spec["laya"], "questions": payload}).encode()
    else:
        direct = "typesafe.ai" in JEV_URL
        key = os.environ.get("TYPESAFE_API_KEY") if direct else os.environ.get("OPENROUTER_API_KEY")
        _require(bool(key), "set OPENROUTER_API_KEY (or TYPESAFE_API_KEY with JEV_URL=https://api.typesafe.ai/v1/systemone)")
        url, headers = JEV_URL, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
        body = json.dumps({"state": state[:12000], "model": spec["direct" if direct else "openrouter"], "questions": payload}).encode()
    request = urllib.request.Request(url, data=body, headers=headers)
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(request, timeout=30) as resp:
                return {**json.loads(resp.read().decode()), "model": model}
        except urllib.error.HTTPError as exc:
            if exc.code in (429, 502, 503, 529) and attempt < retries - 1:
                time.sleep(2 ** attempt + random.random())
                continue
            raise DecisionLogError(f"jev HTTP {exc.code}") from None
        except urllib.error.URLError:
            if attempt < retries - 1:
                time.sleep(2 ** attempt)
                continue
            raise
    raise DecisionLogError("jev: retries exhausted")


# --------------------------------------------------------------------------
# Typed records
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class Prediction:
    """What the choice is expected to move, declared before the result exists."""

    metric: OutcomeMetric
    baseline: float
    target: float
    window_days: int
    direction: Direction = "increase"

    def __post_init__(self) -> None:
        _require(self.metric in OUTCOME_METRICS, f"metric {self.metric!r} is not an outcome metric {OUTCOME_METRICS}")
        _require(self.direction in get_args(Direction), f"direction must be one of {get_args(Direction)}")
        _number(self.baseline, "baseline")
        _number(self.target, "target")
        _require(isinstance(self.window_days, int) and self.window_days > 0, "window_days must be a positive int")
        moves = self.target > self.baseline if self.direction == "increase" else self.target < self.baseline
        _require(moves, f"target {self.target} does not {self.direction} on baseline {self.baseline}")


@dataclass(frozen=True)
class Decision:
    decision_id: str
    kind: str
    subject: str
    options: tuple[str, ...]
    choice: str
    rationale: str
    prediction: Prediction
    actor: str
    model: str = "human"
    question_id: str = ""
    question_version: str = ""
    probabilities: tuple[tuple[str, float], ...] = ()
    confidence: float | None = None
    gate_floor: float | None = None  # the floor the answer cleared
    action_class: str = "auto_pr"
    lesson_refs: tuple[str, ...] = ()
    run_id: str = ""
    eco_record_id: str = ""
    made_at: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        for name in ("decision_id", "kind", "subject", "choice", "rationale", "actor", "model"):
            _require(isinstance(getattr(self, name), str) and getattr(self, name).strip(), f"{name} is required")
        _require(len(set(self.options)) >= 2, "a decision needs at least two distinct options")
        _require(self.choice in self.options, f"choice {self.choice!r} is not one of the options")
        _require(self.action_class in ACTION_CLASSES, f"action_class must be one of {ACTION_CLASSES}")
        _require(isinstance(self.prediction, Prediction), "prediction must be a Prediction")
        if self.model != "human":
            _require(canonical_model(self.model) == self.model, f"model {self.model!r} must be a pinned id from MODELS")
            _require(bool(self.question_id and self.question_version), "model decisions must pin question_id and question_version")
            _require(self.confidence is not None, "model decisions must carry confidence")
        if self.confidence is not None:
            _unit(self.confidence, "confidence")
        if self.gate_floor is not None:
            _unit(self.gate_floor, "gate_floor")
        _parse_time(self.made_at, "made_at")


@dataclass(frozen=True)
class Outcome:
    decision_id: str
    observed: float
    source: str
    verifier: str
    label: str = ""  # true answer to the Jev question, when it can be observed
    observed_at: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        _number(self.observed, "observed")
        _require(bool(self.source.strip()), "source is required (where the number was read)")
        _require(bool(self.verifier.strip()), "verifier is required")
        _parse_time(self.observed_at, "observed_at")


@dataclass(frozen=True)
class Lesson:
    lesson_id: str
    kind: str
    stance: Literal["prefer", "avoid"]
    choice: str
    metric: OutcomeMetric
    lift: float
    p_value: float
    n_choice: int
    n_other: int
    evidence: tuple[str, ...]
    depth: int = 0


def lift(prediction: Prediction, observed: float) -> float:
    """Signed move toward the target, scaled by the baseline (1.0 = doubled)."""
    move = (observed - prediction.baseline) / max(abs(prediction.baseline), 1.0)
    return round(move if prediction.direction == "increase" else -move, 4)


def grade(prediction: Prediction, observed: float) -> Grade:
    reached = observed >= prediction.target if prediction.direction == "increase" else observed <= prediction.target
    if reached:
        return "hit"
    return "partial" if lift(prediction, observed) > 0 else "miss"


# --------------------------------------------------------------------------
# Event log
# --------------------------------------------------------------------------

def log_path() -> Path:
    base = os.environ.get("KAI_AUTONOMY_DIR")
    return (Path(base) if base else REPO_ROOT / "data" / "autonomy") / "decisions.jsonl"


def _append(event_type: EventType, body: dict[str, Any], path: Path | None = None) -> dict[str, Any]:
    event = {"schema": SCHEMA, "event": event_type, "event_id": uuid.uuid4().hex[:12], "at": _utc_now(), **body}
    target = path or log_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def _pairs(value: Any) -> tuple[tuple[str, float], ...]:
    return tuple((str(k), float(v)) for k, v in (value or ()))


def _decision_from(data: dict[str, Any]) -> Decision:
    data = dict(data)
    data["prediction"] = Prediction(**data["prediction"])
    data["options"] = tuple(data["options"])
    data["lesson_refs"] = tuple(data.get("lesson_refs") or ())
    data["probabilities"] = _pairs(data.get("probabilities"))
    return Decision(**data)


@dataclass
class State:
    decisions: dict[str, Decision] = field(default_factory=dict)
    outcomes: dict[str, Outcome] = field(default_factory=dict)
    lessons: dict[str, Lesson] = field(default_factory=dict)
    retired: set[str] = field(default_factory=set)
    gates: dict[str, float] = field(default_factory=dict)  # "question_id@version@model" -> floor
    retired_questions: set[str] = field(default_factory=set)  # same key: retired for that model only
    shadows: dict[str, list[dict[str, Any]]] = field(default_factory=dict)  # decision_id -> other models' answers
    escalations: int = 0
    passes: list[dict[str, Any]] = field(default_factory=list)

    def active_lessons(self) -> list[Lesson]:
        return [lesson for lid, lesson in self.lessons.items() if lid not in self.retired]

    def graded(self) -> list[tuple[Decision, Outcome, float]]:
        return [(self.decisions[d], o, lift(self.decisions[d].prediction, o.observed)) for d, o in self.outcomes.items()]

    def floor(self, question: Question, model: str) -> float:
        return self.gates.get(gate_key(question.question_id, question.version, model), GATE_FLOOR)

    def accuracy(self) -> dict[str, list[bool]]:
        """Per gate key: was each answer right, counting only answers that
        cleared the key's current floor (the decider's own and shadow asks)."""
        table: dict[str, list[bool]] = {}
        for decision, outcome, _ in self.graded():
            if not (decision.question_id and outcome.label):
                continue
            rows = [(decision.model, decision.choice, decision.gate_floor, True)]
            rows += [(s["model"], s["answer"], s["floor"], s["passed"]) for s in self.shadows.get(decision.decision_id, [])]
            for model, answer, floor, passed in rows:
                key = gate_key(decision.question_id, decision.question_version, model)
                if passed and (floor if floor is not None else GATE_FLOOR) == self.gates.get(key, GATE_FLOOR):
                    table.setdefault(key, []).append(outcome.label == answer)
        return table


def gate_key(question_id: str, version: str, model: str) -> str:
    return f"{question_id}@{version}@{model}"


def load(path: Path | None = None) -> State:
    """Fold the log into state, re-validating every event."""
    target = path or log_path()
    state = State()
    if not target.exists():
        return state
    for number, line in enumerate(target.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            _require(event.get("schema") == SCHEMA, f"unknown schema {event.get('schema')!r}")
            kind = event.get("event")
            _require(kind in EVENT_TYPES, f"unknown event {kind!r}")
            if kind == "decided":
                decision = _decision_from(event["decision"])
                _require(decision.decision_id not in state.decisions, "duplicate decision_id")
                state.decisions[decision.decision_id] = decision
            elif kind == "escalated":
                state.escalations += 1
            elif kind == "shadowed":
                _require(event["decision_id"] in state.decisions, "shadow for an unknown decision")
                state.shadows.setdefault(event["decision_id"], []).append({
                    "model": canonical_model(event["model"]), "answer": str(event["answer"]),
                    "floor": _unit(event["floor"], "floor"), "passed": bool(event["passed"]),
                })
            elif kind == "observed":
                outcome = Outcome(**event["outcome"])
                _check_outcome(state, outcome)
                state.outcomes[outcome.decision_id] = outcome
            elif kind == "lesson_accepted":
                lesson = Lesson(**{**event["lesson"], "evidence": tuple(event["lesson"]["evidence"])})
                state.lessons[lesson.lesson_id] = lesson
            elif kind == "lesson_retired":
                state.retired.add(event["lesson_id"])
            elif kind == "gate_tuned":
                floor = _unit(event["floor"], "floor")
                _require(GATE_FLOOR <= floor <= GATE_CEILING, f"floor {floor} outside {GATE_FLOOR}..{GATE_CEILING}")
                state.gates[event["question"]] = floor
            elif kind == "question_retired":
                state.retired_questions.add(event["question"])
            else:
                state.passes.append(event)
        except (DecisionLogError, KeyError, TypeError, json.JSONDecodeError) as exc:
            raise DecisionLogError(f"{target}:{number}: {exc}") from exc
    return state


def _check_outcome(state: State, outcome: Outcome) -> None:
    decision = state.decisions.get(outcome.decision_id)
    _require(decision is not None, f"no decision {outcome.decision_id!r}")
    _require(outcome.decision_id not in state.outcomes, "outcome already recorded for this decision")
    _require(outcome.verifier.strip().lower() not in {decision.actor.strip().lower(), decision.model.strip().lower()},
             "the decider may not verify its own outcome")
    _require(_parse_time(outcome.observed_at, "observed_at") >= _parse_time(decision.made_at, "made_at"),
             "outcome observed before the decision was made")


def decide(decision: Decision, path: Path | None = None) -> dict[str, Any]:
    state = load(path)
    _require(decision.decision_id not in state.decisions, "duplicate decision_id")
    unknown = [ref for ref in decision.lesson_refs if ref not in state.lessons]
    _require(not unknown, f"lesson_refs not in the log: {unknown}")
    return _append("decided", {"decision": asdict(decision)}, path)


def route_model(
    state: State,
    question: Question,
    candidates: tuple[str, ...] = (),
    *,
    min_n: int = 10,
    target_accuracy: float = 0.85,
) -> str:
    """Pick the System One model for a question from measured accuracy.

    A model that has min_n labeled answers for this exact question version is
    ranked by accuracy at its current gate. The default model wins until
    another model proves itself (target_accuracy or better than the default's
    measured accuracy). Models retired for this question are skipped.
    """
    pool = list(dict.fromkeys(canonical_model(m) for m in (candidates or (DEFAULT_MODEL,))))
    prefix = f"{question.question_id}@{question.version}@"
    table = state.accuracy()
    pool += [k[len(prefix):] for k in table if k.startswith(prefix) and k[len(prefix):] not in pool]
    live = [m for m in pool if prefix + m not in state.retired_questions]
    _require(bool(live), f"every model is retired for {question.question_id}@{question.version}; reword it")
    measured = {m: sum(table[prefix + m]) / len(table[prefix + m]) for m in live if len(table.get(prefix + m, [])) >= min_n}
    default = live[0]
    if not measured:
        return default
    best = max(measured, key=lambda m: (measured[m], -live.index(m)))
    bar = measured.get(default, target_accuracy)
    return best if measured[best] >= bar else default


def decide_with_jev(
    *,
    kind: str,
    subject: str,
    state_text: str,
    question: Question,
    prediction: Prediction,
    actor: str,
    model: str = "",
    candidates: tuple[str, ...] = (),
    shadow: tuple[str, ...] = (),
    action_class: str = "auto_pr",
    run_id: str = "",
    backend: str = "jev",
    path: Path | None = None,
) -> Decision | None:
    """Ask Jev, gate the answer, and record a Decision (or an escalation).

    ``model`` pins a model; otherwise ``route_model`` picks one from
    ``candidates`` (default: DEFAULT_MODEL) by measured accuracy. ``shadow``
    models answer the same question for comparison only: their answers never
    decide, but once the outcome label arrives they are graded too, which is
    how a cheaper or newer model earns the route. Returns None when the
    deciding model is unsure; the escalation is logged and the caller routes to
    a human or a stronger model. Active lessons for this kind are cited so the
    next pass can test them.
    """
    state = load(path)
    model = canonical_model(model) if model else route_model(state, question, candidates)
    key = gate_key(question.question_id, question.version, model)
    _require(key not in state.retired_questions, f"question {key} was retired for low accuracy; reword it or use another model")
    response = ask_jev(state_text, [question], model=model, backend=backend)
    answer = JevAnswer.parse(question, (response.get("answers") or {}).get(question.question_id))
    floor = state.floor(question, model)
    if not answer.passes(floor):
        _append("escalated", {"kind": kind, "subject": subject, "question": key, "answer": asdict(answer), "floor": floor}, path)
        return None
    refs = tuple(l.lesson_id for l in state.active_lessons() if l.kind == kind)
    decision = Decision(
        decision_id=f"dec-{uuid.uuid4().hex[:10]}",
        kind=kind,
        subject=subject,
        options=question.options,
        choice=answer.answer,
        rationale=f"{model} {question.question_id}@{question.version}: {answer.answer} at confidence {answer.confidence}",
        prediction=prediction,
        actor=actor,
        model=model,
        question_id=question.question_id,
        question_version=question.version,
        probabilities=answer.probabilities,
        confidence=answer.confidence,
        gate_floor=floor,
        action_class=action_class,
        lesson_refs=refs,
        run_id=run_id,
    )
    decide(decision, path)
    for other in dict.fromkeys(canonical_model(m) for m in shadow):
        if other == model:
            continue
        try:
            raw = ask_jev(state_text, [question], model=other, backend=backend)
            seen = JevAnswer.parse(question, (raw.get("answers") or {}).get(question.question_id))
        except (OSError, ImportError, DecisionLogError) as exc:  # a shadow never blocks the decision
            print(f"shadow {other} skipped: {exc}", file=sys.stderr)
            continue
        other_floor = state.floor(question, other)
        _append("shadowed", {"decision_id": decision.decision_id, "model": other, "answer": seen.answer,
                             "confidence": seen.confidence, "floor": other_floor, "passed": seen.passes(other_floor)}, path)
    return decision


def observe(outcome: Outcome, path: Path | None = None) -> dict[str, Any]:
    state = load(path)
    _check_outcome(state, outcome)
    return _append("observed", {"outcome": asdict(outcome)}, path)


def outcome_from_kai_data(kai_data: Path, metric_id: str) -> tuple[float, str]:
    """Read one collector metric from kai-data.json as an outcome value."""
    _require(metric_id in KAI_DATA_METRICS, f"{metric_id!r} is not an outcome metric id {sorted(KAI_DATA_METRICS)}")
    data = json.loads(kai_data.read_text(encoding="utf-8"))
    for metric in data.get("metrics", []):
        if metric.get("metric_id") != metric_id:
            continue
        value = metric.get("value")
        if isinstance(value, dict):
            _require(len(value) == 1, f"{metric_id} has several currencies {sorted(value)}; record one by hand")
            value = next(iter(value.values()))
        return _number(value, metric_id), f"{kai_data}#{metric_id} ({metric.get('source_id', '')})"
    raise DecisionLogError(f"{metric_id} is not in {kai_data}; it is a data gap, not a zero")


# --------------------------------------------------------------------------
# Learning loop
# --------------------------------------------------------------------------

def _welch_p(a: list[float], b: list[float]) -> float:
    from scripts.self_improvement.stats_utils import welch_ttest

    return float(welch_ttest(a, b)["p_value"])


def _depth(state: State, decision_ids: list[str]) -> int:
    cited = [state.lessons[r].depth for d in decision_ids for r in state.decisions[d].lesson_refs if r in state.lessons]
    return 1 + max(cited) if cited else 0


def learn(
    path: Path | None = None,
    *,
    min_n: int = 10,
    min_delta: float = 0.15,
    p_threshold: float = 0.05,
    target_accuracy: float = 0.85,
    max_depth: int = 2,
    stall_limit: int = 3,
    max_new: int = 3,
) -> dict[str, Any]:
    """One learning pass. Returns what changed, or that it stalled."""
    state = load(path)
    graded = state.graded()
    recent = state.passes[-stall_limit:]
    if len(recent) == stall_limit and all(not p.get("changed") and p.get("graded") == len(graded) for p in recent):
        return {"stalled": True, "graded": len(graded), "accepted": [], "retired": [], "gates": {}, "questions_retired": []}

    by_kind: dict[str, list[tuple[Decision, Outcome, float]]] = {}
    for row in graded:
        by_kind.setdefault(row[0].kind, []).append(row)

    # 1. Choice lessons.
    taken = {(l.kind, l.choice) for l in state.active_lessons()}
    accepted: list[Lesson] = []
    for kind, rows in sorted(by_kind.items()):
        for choice in sorted({d.choice for d, _, _ in rows}):
            if len(accepted) >= max_new or (kind, choice) in taken:
                continue
            mine = [r for r in rows if r[0].choice == choice]
            other = [r for r in rows if r[0].choice != choice]
            if len(mine) < min_n or len(other) < min_n:
                continue
            a, b = [r[2] for r in mine], [r[2] for r in other]
            delta = sum(a) / len(a) - sum(b) / len(b)
            if abs(delta) < min_delta:
                continue
            p_value = _welch_p(a, b)
            if p_value >= p_threshold:
                continue
            evidence = [r[0].decision_id for r in mine + other]
            depth = _depth(state, evidence)
            if depth > max_depth:
                continue
            metrics = {r[0].prediction.metric for r in mine}
            lesson = Lesson(
                lesson_id=f"lsn-{uuid.uuid4().hex[:10]}", kind=kind, stance="prefer" if delta > 0 else "avoid",
                choice=choice, metric=metrics.pop() if len(metrics) == 1 else "revenue", lift=round(delta, 4),
                p_value=round(p_value, 4), n_choice=len(a), n_other=len(b), evidence=tuple(sorted(evidence)), depth=depth,
            )
            _append("lesson_accepted", {"lesson": asdict(lesson)}, path)
            accepted.append(lesson)

    # 2. Lesson retirement: followers must keep beating the rest.
    retired: list[str] = []
    for lesson in state.active_lessons():
        rows = by_kind.get(lesson.kind, [])
        followed = [r[2] for r in rows if lesson.lesson_id in r[0].lesson_refs and r[0].choice == lesson.choice]
        others = [r[2] for r in rows if lesson.lesson_id not in r[0].lesson_refs]
        if len(followed) >= min_n and len(others) >= min_n:
            better = sum(followed) / len(followed) > sum(others) / len(others)
            if better != (lesson.stance == "prefer"):
                _append("lesson_retired", {"lesson_id": lesson.lesson_id, "reason": "the gain did not hold for later decisions"}, path)
                retired.append(lesson.lesson_id)

    # 3. Gate tuning, per question version and model: was each model right
    # when it was confident enough to decide (or would have been, for shadows)?
    gates: dict[str, float] = {}
    questions_retired: list[str] = []
    labeled = state.accuracy()
    for key, hits in sorted(labeled.items()):
        if len(hits) < min_n or key in state.retired_questions:
            continue
        accuracy = sum(hits) / len(hits)
        current = state.gates.get(key, GATE_FLOOR)
        if accuracy < target_accuracy:
            if current >= GATE_CEILING:
                _append("question_retired", {"question": key, "accuracy": round(accuracy, 4), "n": len(hits)}, path)
                questions_retired.append(key)
                continue
            new = round(min(GATE_CEILING, current + GATE_STEP), 4)
        elif accuracy >= target_accuracy + 0.05 and current > GATE_FLOOR:
            new = round(max(GATE_FLOOR, current - GATE_STEP), 4)
        else:
            continue
        _append("gate_tuned", {"question": key, "floor": new, "accuracy": round(accuracy, 4), "n": len(hits)}, path)
        gates[key] = new

    changed = bool(accepted or retired or gates or questions_retired)
    _append("learn_pass", {"graded": len(graded), "changed": changed}, path)
    return {
        "stalled": False, "graded": len(graded), "accepted": [l.lesson_id for l in accepted], "retired": retired,
        "gates": gates, "questions_retired": questions_retired, "lessons": [asdict(l) for l in accepted],
    }


def write_lessons(result: dict[str, Any], path: Path | None = None) -> list[str]:
    """Write a pass's lessons, retirements and retired questions to memory/lessons.md."""
    from scripts.self_improvement.lesson_capture import append_lessons, format_lesson

    state = load(path)
    lines = []
    for lid in result.get("accepted", []):
        l = state.lessons[lid]
        advice = f"{l.stance} {l.choice!r} ({l.metric} lift {l.lift:+.0%} vs other choices, p={l.p_value}, n={l.n_choice}/{l.n_other})"
        lines.append(format_lesson(f"When deciding {l.kind}", advice, f"decision log {lid}"))
    for lid in result.get("retired", []):
        l = state.lessons[lid]
        lines.append(format_lesson(f"When deciding {l.kind}", f"drop the rule to {l.stance} {l.choice!r}; its gain did not hold", f"decision log {lid}", status="retired"))
    for key in result.get("questions_retired", []):
        lines.append(format_lesson(f"When Jev answers {key}", "reword the question as a visible feature or route it to another model; it stayed wrong at the strictest gate", "decision log gate tuning"))
    return append_lessons(lines)


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Jev-typed decision log and revenue-graded learning loop")
    sub = parser.add_subparsers(dest="cmd", required=True)
    p_decide = sub.add_parser("decide", help="record a decision from a JSON file (human or other model)")
    p_decide.add_argument("file", type=Path)
    p_ask = sub.add_parser("ask", help="let Jev decide: JSON file with kind, subject, state, question, prediction, actor")
    p_ask.add_argument("file", type=Path)
    p_ask.add_argument("--mock", action="store_true", help="offline mock answers, no API call")
    p_ask.add_argument("--model", default="", help=f"pin a model {sorted(MODELS)}; default: route by measured accuracy")
    p_ask.add_argument("--candidates", default="", help="comma list of models the router may pick from (first = default)")
    p_ask.add_argument("--shadow", default="", help="comma list of models that also answer, graded but never deciding")
    p_obs = sub.add_parser("observe", help="record the outcome of a decision")
    p_obs.add_argument("--decision-id", required=True)
    p_obs.add_argument("--verifier", required=True)
    p_obs.add_argument("--observed", type=float)
    p_obs.add_argument("--source", default="")
    p_obs.add_argument("--label", default="", help="the true answer to the Jev question, if observable")
    p_obs.add_argument("--kai-data", type=Path, help="read the value from a collector kai-data.json")
    p_obs.add_argument("--metric-id", default="")
    p_learn = sub.add_parser("learn", help="run one learning pass")
    p_learn.add_argument("--apply", action="store_true", help="write lessons to memory/lessons.md")
    p_learn.add_argument("--min-n", type=int, default=10)
    p_learn.add_argument("--min-delta", type=float, default=0.15)
    p_learn.add_argument("--p-threshold", type=float, default=0.05)
    p_learn.add_argument("--target-accuracy", type=float, default=0.85)
    sub.add_parser("status", help="decisions, outcomes, gates and active lessons")
    sub.add_parser("models", help="known System One models and measured accuracy per question")
    args = parser.parse_args(argv)

    try:
        if args.cmd == "decide":
            raw = json.loads(args.file.read_text(encoding="utf-8"))
            raw.setdefault("decision_id", f"dec-{uuid.uuid4().hex[:10]}")
            print(decide(_decision_from(raw))["decision"]["decision_id"])
        elif args.cmd == "ask":
            raw = json.loads(args.file.read_text(encoding="utf-8"))
            q = raw["question"]
            decision = decide_with_jev(
                kind=raw["kind"], subject=raw["subject"], state_text=raw["state"],
                question=Question.from_dict(q.pop("id"), q), prediction=Prediction(**raw["prediction"]),
                actor=raw["actor"], action_class=raw.get("action_class", "auto_pr"),
                model=args.model or raw.get("model", ""),
                candidates=tuple(m for m in (args.candidates or ",".join(raw.get("candidates", []))).split(",") if m),
                shadow=tuple(m for m in (args.shadow or ",".join(raw.get("shadow", []))).split(",") if m),
                backend="mock" if args.mock else "jev",
            )
            print(json.dumps(asdict(decision) if decision else {"escalated": True}, indent=2))
        elif args.cmd == "observe":
            if args.kai_data:
                value, source = outcome_from_kai_data(args.kai_data, args.metric_id)
            else:
                _require(args.observed is not None and bool(args.source), "--observed and --source are required without --kai-data")
                value, source = args.observed, args.source
            observe(Outcome(decision_id=args.decision_id, observed=value, source=source, verifier=args.verifier, label=args.label))
            print(grade(load().decisions[args.decision_id].prediction, value))
        elif args.cmd == "learn":
            result = learn(min_n=args.min_n, min_delta=args.min_delta, p_threshold=args.p_threshold, target_accuracy=args.target_accuracy)
            if args.apply and not result["stalled"]:
                result["written"] = write_lessons(result)
            print(json.dumps(result, indent=2))
        elif args.cmd == "models":
            state = load()
            print(json.dumps({
                "default": canonical_model(DEFAULT_MODEL),
                "models": MODELS,
                "accuracy": {k: {"n": len(v), "accuracy": round(sum(v) / len(v), 4), "floor": state.gates.get(k, GATE_FLOOR)}
                             for k, v in sorted(state.accuracy().items())},
                "retired": sorted(state.retired_questions),
            }, indent=2))
        else:
            state = load()
            print(json.dumps({
                "decisions": len(state.decisions),
                "escalations": state.escalations,
                "awaiting_outcome": sorted(set(state.decisions) - set(state.outcomes)),
                "graded": len(state.outcomes),
                "gates": state.gates,
                "retired_questions": sorted(state.retired_questions),
                "active_lessons": [asdict(l) for l in state.active_lessons()],
            }, indent=2))
    except DecisionLogError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
