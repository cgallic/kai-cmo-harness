"""Thin adapter from the ad-library scripts to the harness Jev client.

The call, the model pins, the retries and the confidence gate all live in
``scripts/autonomy/decision_log.py`` (``ask_jev``, ``Question``, ``JevAnswer``,
``GATE_FLOOR``). This module only converts the ad scripts' question dicts into
``Question`` objects and turns raw answers into gated labels, so there is one
Jev client in the harness, not two.

Questions ask about visible features, never judgments, and every count, date
and score is computed in code. ``backend="mock"`` is offline and deterministic.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.autonomy.decision_log import (  # noqa: E402
    DEFAULT_MODEL,
    GATE_FLOOR,
    DecisionLogError,
    JevAnswer,
    Question,
    ask_jev,
)

UNSURE = "unsure"


def to_questions(questions: dict[str, dict[str, Any]]) -> list[Question]:
    return [Question.from_dict(qid, spec) for qid, spec in questions.items()]


def ask(state: str, questions: dict[str, dict[str, Any]], *, backend: str = "jev", model: str = "") -> dict[str, Any]:
    """One System One call carrying every question. Returns the raw response (``answers``, ``usage``)."""
    return ask_jev(state, to_questions(questions), model=model or DEFAULT_MODEL, backend=backend)


def gate(question_id: str, spec: dict[str, Any], raw: Any, floor: float = GATE_FLOOR) -> str:
    """Gated label for one answer: the answer when it clears the harness gate, else ``unsure``.

    Choice: confidence >= floor and the leader >= MARGIN_MIN ahead. Yes/no: p >= 0.70
    is yes, p <= 0.30 is no (at the default floor). A malformed answer is ``unsure``.
    """
    question = Question.from_dict(question_id, spec)
    try:
        answer = JevAnswer.parse(question, raw)
    except DecisionLogError:
        # Some score answers arrive without a distribution; keep them only when confident.
        if question.type == "score" and isinstance(raw, dict) and raw.get("score") is not None:
            try:
                if float(raw.get("confidence") or 0) >= floor:
                    return str(int(round(float(raw["score"]))))
            except (TypeError, ValueError):
                return UNSURE
        return UNSURE
    return answer.answer if answer.passes(floor) else UNSURE


def gate_all(questions: dict[str, dict[str, Any]], answers: dict[str, Any] | None) -> dict[str, str]:
    """Gated labels for every question that came back with an answer."""
    answers = answers or {}
    return {qid: gate(qid, spec, answers[qid]) for qid, spec in questions.items() if qid in answers}


def usage_cost(rows: list[dict[str, Any]], key: str = "jev_usage") -> float | None:
    """Sum of the provider-reported ``usage.cost`` (OpenRouter returns it per call); None if absent."""
    costs = [(r.get(key) or {}).get("cost") for r in rows]
    costs = [float(c) for c in costs if c is not None]
    return round(sum(costs), 6) if costs else None
