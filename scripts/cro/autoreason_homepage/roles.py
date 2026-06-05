"""Five fresh-agent roles for the homepage AutoReason CRO loop.

Mirrors scripts/ads/autoreason/roles.py but every role takes / returns
HomepageZones (4 zones) instead of AdCopy (ad fields), and the LLM sees the
PRD-derived context bundle instead of Meta perf data.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests

from .trace import HomepageZones, JudgeVote

PROMPTS_DIR = Path(__file__).parent / "prompts"

MODEL = "anthropic/claude-3.5-haiku"
AUTHOR_TEMP = 0.8
JUDGE_TEMP = 0.3
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _call(system: str, user: str, temperature: float, max_tokens: int = 1500) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not in env")
    r = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-Title": "kai-cmo-harness/cro-autoreason-homepage",
        },
        json={
            "model": MODEL,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        },
        timeout=120,
    )
    if r.status_code >= 300:
        raise RuntimeError(f"OpenRouter {r.status_code}: {r.text[:300]}")
    body = r.json()
    return body["choices"][0]["message"]["content"]


_FENCE_RE = re.compile(r"```(?:json)?\s*(\{.*?\})\s*```", re.DOTALL)


def _balanced_object(text: str) -> str | None:
    start = text.find("{")
    if start < 0:
        return None
    depth = 0
    in_str = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_str:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == '"':
                in_str = False
        else:
            if ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    return text[start : i + 1]
    return None


def _parse_json(text: str) -> dict:
    import json_repair
    m = _FENCE_RE.search(text)
    candidate = m.group(1) if m else (_balanced_object(text) or text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        repaired = json_repair.loads(candidate)
        if not isinstance(repaired, dict):
            raise ValueError(f"json_repair did not yield an object: {repaired!r}")
        return repaired


def _call_json(system: str, user: str, temperature: float, max_tokens: int = 1500) -> dict:
    text = _call(system, user, temperature, max_tokens)
    try:
        return _parse_json(text)
    except (ValueError, json.JSONDecodeError):
        retry_user = (
            user
            + "\n\nYour previous response was not valid JSON. Re-emit ONLY the "
              "JSON object, no prose, no code fences."
        )
        text = _call(system, retry_user, temperature, max_tokens)
        return _parse_json(text)


# ---------------------------------------------------------------------------
# Role: Critic
# ---------------------------------------------------------------------------

def critic(incumbent: HomepageZones, context: dict) -> dict:
    user = (
        "## Incumbent homepage zones\n"
        f"```json\n{json.dumps(incumbent.to_dict(), indent=2)}\n```\n\n"
        "## PRD-derived context\n"
        f"```json\n{json.dumps(context, indent=2)}\n```\n\n"
        "Produce your critique JSON."
    )
    return _call_json(_load_prompt("critic"), user, AUTHOR_TEMP)


# ---------------------------------------------------------------------------
# Role: Author B
# ---------------------------------------------------------------------------

def author_b(incumbent: HomepageZones, critique: dict, context: dict) -> HomepageZones:
    user = (
        "## Incumbent (A)\n"
        f"```json\n{json.dumps(incumbent.to_dict(), indent=2)}\n```\n\n"
        "## Critique\n"
        f"```json\n{json.dumps(critique, indent=2)}\n```\n\n"
        "## Positioning context\n"
        f"```json\n{json.dumps(context, indent=2)}\n```\n\n"
        "Write your adversarial revision (B) JSON."
    )
    data = _call_json(_load_prompt("author"), user, AUTHOR_TEMP)
    return HomepageZones(
        hero_headline=data["hero_headline"],
        sub_hero=data["sub_hero"],
        primary_cta=data["primary_cta"],
        feature_frame=data["feature_frame"],
    )


# ---------------------------------------------------------------------------
# Role: Synthesizer
# ---------------------------------------------------------------------------

def synthesizer(a: HomepageZones, b: HomepageZones, label_x_is: str,
                context: dict) -> HomepageZones:
    if label_x_is == "A":
        x_payload, y_payload = a, b
    else:
        x_payload, y_payload = b, a
    user = (
        "## Candidate X\n"
        f"```json\n{json.dumps(x_payload.to_dict(), indent=2)}\n```\n\n"
        "## Candidate Y\n"
        f"```json\n{json.dumps(y_payload.to_dict(), indent=2)}\n```\n\n"
        "## Positioning context\n"
        f"```json\n{json.dumps(context, indent=2)}\n```\n\n"
        "Produce the synthesized homepage JSON."
    )
    data = _call_json(_load_prompt("synthesizer"), user, AUTHOR_TEMP)
    return HomepageZones(
        hero_headline=data["hero_headline"],
        sub_hero=data["sub_hero"],
        primary_cta=data["primary_cta"],
        feature_frame=data["feature_frame"],
    )


# ---------------------------------------------------------------------------
# Role: Judge
# ---------------------------------------------------------------------------

def judge(candidates_pqr: dict[str, HomepageZones], context: dict,
          judge_index: int) -> JudgeVote:
    pqr_payload = {label: zones.to_dict() for label, zones in candidates_pqr.items()}
    user = (
        "## Candidates (judge blind)\n"
        f"```json\n{json.dumps(pqr_payload, indent=2)}\n```\n\n"
        "## Positioning context\n"
        f"```json\n{json.dumps(context, indent=2)}\n```\n\n"
        "Produce your ranking JSON. Borda: 3=first, 2=second, 1=third. "
        "Score every candidate 1–5 on every axis."
    )
    data = _call_json(_load_prompt("judge"), user, JUDGE_TEMP)
    return JudgeVote(
        judge_index=judge_index,
        ranking=data["ranking"],
        scores={k: int(v) for k, v in data["scores"].items()},
        axis_scores={
            k: {ax: int(s) for ax, s in axes.items()}
            for k, axes in data.get("axis_scores", {}).items()
        },
        reasoning=data.get("reasoning", {}),
    )
