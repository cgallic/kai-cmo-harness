"""Five fresh-agent roles for the AutoReason loop.

Each role is a one-shot LLM call. No shared session state. Every call loads
its own prompt from prompts/ and gets only the inputs spelled out in the
paper §A. Authors run at T=0.8, judges at T=0.3 (paper-validated defaults).

Routes through OpenRouter (OpenAI-compat) by default to keep model swaps
cheap. Falls back to native Anthropic SDK if ANTHROPIC_API_KEY is set and
USE_OPENROUTER is not.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

import requests

from .trace import AdCopy, JudgeVote

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Paper-validated sweet spot: Haiku 3.5. Routed via OpenRouter as
# `anthropic/claude-3.5-haiku`. ~10× cheaper than Sonnet, model gap to
# self-eval is the AutoReason peak per the paper.
MODEL = "anthropic/claude-3.5-haiku"

AUTHOR_TEMP = 0.8
JUDGE_TEMP = 0.3

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def _load_prompt(name: str) -> str:
    return (PROMPTS_DIR / f"{name}.md").read_text(encoding="utf-8")


def _call(system: str, user: str, temperature: float, max_tokens: int = 1024) -> str:
    key = os.environ.get("OPENROUTER_API_KEY")
    if not key:
        raise RuntimeError("OPENROUTER_API_KEY not in env")
    r = requests.post(
        OPENROUTER_URL,
        headers={
            "Authorization": f"Bearer {key}",
            "Content-Type": "application/json",
            "X-Title": "kai-cmo-harness/autoreason",
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
    """Return the first balanced {...} block, ignoring braces inside strings."""
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
    """Extract JSON from a model response. Tolerates code fences, prose, and
    common LLM mistakes (unescaped inner quotes, trailing commas) via
    json_repair."""
    import json_repair  # local import — keep module-level imports light

    m = _FENCE_RE.search(text)
    candidate = m.group(1) if m else (_balanced_object(text) or text)
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        repaired = json_repair.loads(candidate)
        if not isinstance(repaired, dict):
            raise ValueError(f"json_repair did not yield an object: {repaired!r}")
        return repaired


def _call_json(system: str, user: str, temperature: float, max_tokens: int = 1024) -> dict:
    """Call the model and parse JSON from the reply. One retry on parse failure."""
    text = _call(system, user, temperature, max_tokens)
    try:
        return _parse_json(text)
    except (ValueError, json.JSONDecodeError):
        retry_user = (
            user
            + "\n\nYour previous response was not valid JSON. Re-emit ONLY the JSON object, "
              "no prose, no code fences."
        )
        text = _call(system, retry_user, temperature, max_tokens)
        return _parse_json(text)


# ---------------------------------------------------------------------------
# Role: Critic
# ---------------------------------------------------------------------------

def critic(incumbent: AdCopy, perf: dict, top_ads: list[dict], bottom_ads: list[dict]) -> dict:
    user = (
        "## Incumbent\n"
        f"```json\n{json.dumps(incumbent.to_dict(), indent=2)}\n```\n\n"
        "## Ad set performance (last 30/90d)\n"
        f"```json\n{json.dumps(perf, indent=2)}\n```\n\n"
        "## Top 3 winning ads in this audience\n"
        f"```json\n{json.dumps(top_ads, indent=2)}\n```\n\n"
        "## Bottom 3 losing ads in this audience\n"
        f"```json\n{json.dumps(bottom_ads, indent=2)}\n```\n\n"
        "Produce your critique JSON."
    )
    return _call_json(_load_prompt("critic"), user, AUTHOR_TEMP)


# ---------------------------------------------------------------------------
# Role: Author B
# ---------------------------------------------------------------------------

def author_b(incumbent: AdCopy, critique: dict) -> AdCopy:
    user = (
        "## Incumbent (A)\n"
        f"```json\n{json.dumps(incumbent.to_dict(), indent=2)}\n```\n\n"
        "## Critique\n"
        f"```json\n{json.dumps(critique, indent=2)}\n```\n\n"
        "Write your adversarial revision (B) JSON."
    )
    data = _call_json(_load_prompt("author"), user, AUTHOR_TEMP)
    return AdCopy(
        headline=data["headline"],
        primary_text=data["primary_text"],
        description=data["description"],
        cta=data["cta"],
        link=incumbent.link,
    )


# ---------------------------------------------------------------------------
# Role: Synthesizer
# ---------------------------------------------------------------------------

def synthesizer(a: AdCopy, b: AdCopy, label_x_is: str) -> AdCopy:
    """Synthesize A and B into AB. label_x_is is 'A' or 'B' — which underlying
    candidate the X label points to. The model never sees this; we use it only
    to record the rationale unmasking."""
    if label_x_is == "A":
        x_payload, y_payload = a, b
    else:
        x_payload, y_payload = b, a
    user = (
        "## Candidate X\n"
        f"```json\n{json.dumps(x_payload.to_dict(), indent=2)}\n```\n\n"
        "## Candidate Y\n"
        f"```json\n{json.dumps(y_payload.to_dict(), indent=2)}\n```\n\n"
        "Produce the synthesized ad JSON."
    )
    data = _call_json(_load_prompt("synthesizer"), user, AUTHOR_TEMP)
    return AdCopy(
        headline=data["headline"],
        primary_text=data["primary_text"],
        description=data["description"],
        cta=data["cta"],
        link=a.link,
    )


# ---------------------------------------------------------------------------
# Role: Judge
# ---------------------------------------------------------------------------

def judge(candidates_pqr: dict[str, AdCopy], perf: dict, top_ads: list[dict],
          judge_index: int) -> JudgeVote:
    """One judge sees three labeled candidates (P/Q/R) and returns a Borda vote."""
    pqr_payload = {label: ad.to_dict() for label, ad in candidates_pqr.items()}
    user = (
        "## Candidates (judge blind)\n"
        f"```json\n{json.dumps(pqr_payload, indent=2)}\n```\n\n"
        "## Ad set performance (context)\n"
        f"```json\n{json.dumps(perf, indent=2)}\n```\n\n"
        "## Top 3 winning ads in this audience (context)\n"
        f"```json\n{json.dumps(top_ads, indent=2)}\n```\n\n"
        "Produce your ranking JSON. Borda points: 3=first, 2=second, 1=third."
    )
    data = _call_json(_load_prompt("judge"), user, JUDGE_TEMP)
    return JudgeVote(
        judge_index=judge_index,
        ranking=data["ranking"],
        scores={k: int(v) for k, v in data["scores"].items()},
        reasoning=data.get("reasoning", {}),
    )
