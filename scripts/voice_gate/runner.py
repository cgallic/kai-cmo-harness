#!/usr/bin/env python3
"""
voice_gate.runner — LLM-as-judge voice-consistency check.

Given a draft and a voice guide, dispatches a single Claude call that
produces a structured markdown editorial report (severity table + detailed
issues + what's working + systemic patterns). Complements the rule-based
content-gate (which scores structural rules); this gate covers the
subjective voice dimension.

The judge prompt is versioned at harness/voice-gate/judge-prompt.md and renders
three placeholders: {{voice_guide}}, {{persona}} (optional),
{{draft}}. See harness/voice-gate/README.md.

CLI surface:
    python -m scripts.voice_gate.runner <draft-path> \\
        [--voice-guide <path>] \\
        [--persona <path>] \\
        [--output <path>] \\
        [--model <model>] \\
        [--max-issues <n>]

Returns non-zero exit code on FAIL verdict, zero on PASS/HOLD. Writes the
report to <draft-stem>.VOICE-GATE.md alongside the draft (or --output).
Logs the run summary to ~/.kai-marketing/gates/<date>-<slug>-voice.json.

Reads ANTHROPIC_API_KEY from env. Errors clearly if missing.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
KAI_DIR = Path.home() / ".kai-marketing"
GATES_DIR = KAI_DIR / "gates"

MODEL_ALIASES = {
    "haiku": "claude-haiku-4-5",
    "sonnet": "claude-sonnet-4-5",
    "opus": "claude-opus-4-5",
    "claude-sonnet-4-6": "claude-sonnet-4-5",
    "claude-opus-4-7": "claude-opus-4-5",
}

DEFAULT_MODEL = "claude-sonnet-4-5"
DEFAULT_MAX_ISSUES = 30
MAX_TOKENS = 8192

JUDGE_PROMPT_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "harness"
    / "voice-gate"
    / "judge-prompt.md"
)


# ─── Utilities ──────────────────────────────────────────────────────────────


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _resolve_voice_guide(draft_path: Path, explicit: Optional[str]) -> Path:
    """Find the voice guide. Explicit arg wins; otherwise search conventional
    client paths relative to the draft."""
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.exists():
            raise FileNotFoundError(f"Voice guide not found: {p}")
        return p

    # Conventional path: clients/<client>/outputs/personas/*-writing-guide.md
    # The draft usually lives at clients/<client>/outputs/<content-type>/<file>.md
    # So walk up from draft looking for a personas/ sibling.
    cur = draft_path.parent
    for _ in range(6):
        candidate_dir = cur / "personas"
        if candidate_dir.is_dir():
            matches = sorted(candidate_dir.glob("*-writing-guide.md"))
            if matches:
                return matches[0].resolve()
        # also try sibling 'outputs/personas'
        outputs_personas = cur / "outputs" / "personas"
        if outputs_personas.is_dir():
            matches = sorted(outputs_personas.glob("*-writing-guide.md"))
            if matches:
                return matches[0].resolve()
        if cur.parent == cur:
            break
        cur = cur.parent

    raise FileNotFoundError(
        "No voice guide found. Pass --voice-guide <path> explicitly. "
        "Convention: clients/<client>/outputs/personas/*-writing-guide.md"
    )


def _render_prompt(template: str, voice_guide: str, persona: str, draft: str, max_issues: int) -> str:
    return (
        template.replace("{{voice_guide}}", voice_guide)
        .replace("{{persona}}", persona or "(no persona file provided)")
        .replace("{{draft}}", draft)
        .replace("{{max_issues}}", str(max_issues))
    )


def _resolve_model(name: str) -> str:
    return MODEL_ALIASES.get(name, name)


# ─── Anthropic call ─────────────────────────────────────────────────────────


def _call_claude(prompt: str, model: str, api_key: str, timeout: int = 300) -> dict:
    body = {
        "model": model,
        "max_tokens": MAX_TOKENS,
        "messages": [{"role": "user", "content": prompt}],
    }
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    data = json.dumps(body).encode("utf-8")
    req = urllib.request.Request(ANTHROPIC_URL, data=data, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic API error {e.code}: {err_body}") from None
    except urllib.error.URLError as e:
        raise RuntimeError(f"Anthropic API unreachable: {e.reason}") from None


def _extract_text(resp: dict) -> str:
    parts = []
    for block in resp.get("content", []) or []:
        if block.get("type") == "text":
            parts.append(block.get("text", ""))
    return "\n".join(parts).strip()


# ─── Report parsing ─────────────────────────────────────────────────────────


def _parse_verdict(report: str) -> str:
    m = re.search(r"\*\*Verdict:\*\*\s*(PASS|HOLD|FAIL)", report)
    if m:
        return m.group(1).upper()
    return "HOLD"  # safe default


def _parse_severity(report: str) -> dict:
    m = re.search(
        r"\*\*Severity breakdown:\*\*\s*High\s+(\d+),\s*Medium\s+(\d+),\s*Low\s+(\d+)",
        report,
    )
    if m:
        return {"high": int(m.group(1)), "medium": int(m.group(2)), "low": int(m.group(3))}
    return {"high": 0, "medium": 0, "low": 0}


def _parse_total(report: str) -> int:
    m = re.search(r"\*\*Total issues:\*\*\s*(\d+)", report)
    return int(m.group(1)) if m else 0


def _token_counts(resp: dict) -> dict:
    usage = resp.get("usage", {}) or {}
    return {
        "input_tokens": usage.get("input_tokens", 0),
        "output_tokens": usage.get("output_tokens", 0),
    }


# ─── Gate log ───────────────────────────────────────────────────────────────


def _log_gate_run(draft_path: Path, report_path: Path, verdict: str,
                  severity: dict, total: int, tokens: dict, model: str) -> Path:
    GATES_DIR.mkdir(parents=True, exist_ok=True)
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = draft_path.stem
    out = GATES_DIR / f"{date}-{slug}-voice.json"
    payload = {
        "draft": str(draft_path),
        "voice_gate_report": str(report_path),
        "verdict": verdict,
        "severity": severity,
        "total_issues": total,
        "model": model,
        "tokens": tokens,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "gate": "voice-gate",
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out


# ─── Main ───────────────────────────────────────────────────────────────────


def run(draft: str, voice_guide: Optional[str], persona: Optional[str],
        output: Optional[str], model: str, max_issues: int,
        quiet: bool = False) -> int:
    draft_path = Path(draft).expanduser().resolve()
    if not draft_path.exists():
        print(f"ERROR: Draft not found: {draft_path}", file=sys.stderr)
        return 2

    voice_guide_path = _resolve_voice_guide(draft_path, voice_guide)

    persona_text = ""
    if persona:
        persona_path = Path(persona).expanduser().resolve()
        if not persona_path.exists():
            print(f"ERROR: Persona file not found: {persona_path}", file=sys.stderr)
            return 2
        persona_text = _read(persona_path)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not api_key:
        print(
            "ERROR: ANTHROPIC_API_KEY is not set. Export it or add to .env.",
            file=sys.stderr,
        )
        return 2

    if not JUDGE_PROMPT_PATH.exists():
        print(f"ERROR: Judge prompt not found at {JUDGE_PROMPT_PATH}", file=sys.stderr)
        return 2

    template = _read(JUDGE_PROMPT_PATH)
    draft_text = _read(draft_path)
    voice_guide_text = _read(voice_guide_path)

    resolved_model = _resolve_model(model)
    prompt = _render_prompt(template, voice_guide_text, persona_text, draft_text, max_issues)

    if not quiet:
        print(
            f"[voice-gate] model={resolved_model} draft={draft_path.name} "
            f"guide={voice_guide_path.name} max_issues={max_issues}",
            file=sys.stderr,
        )

    resp = _call_claude(prompt, resolved_model, api_key)
    report = _extract_text(resp)
    if not report:
        print("ERROR: Empty response from Claude.", file=sys.stderr)
        return 3

    # Ensure report starts with expected heading; if not, add a minimal frame
    if not report.startswith("# Voice Gate Report"):
        report = f"# Voice Gate Report — {draft_path.name}\n\n" + report

    out_path = Path(output).expanduser().resolve() if output else (
        draft_path.with_suffix("") .parent / (draft_path.stem + ".VOICE-GATE.md")
    )
    out_path.write_text(report, encoding="utf-8")

    verdict = _parse_verdict(report)
    severity = _parse_severity(report)
    total = _parse_total(report)
    tokens = _token_counts(resp)

    log_path = _log_gate_run(
        draft_path, out_path, verdict, severity, total, tokens, resolved_model
    )

    if not quiet:
        print(
            f"[voice-gate] verdict={verdict} total={total} "
            f"High={severity['high']} Medium={severity['medium']} Low={severity['low']} "
            f"tokens_in={tokens['input_tokens']} tokens_out={tokens['output_tokens']}",
            file=sys.stderr,
        )
        print(f"[voice-gate] report: {out_path}", file=sys.stderr)
        print(f"[voice-gate] log:    {log_path}", file=sys.stderr)

    # Print summary JSON on stdout for pipeline consumption
    print(
        json.dumps(
            {
                "verdict": verdict,
                "total_issues": total,
                "severity": severity,
                "report_path": str(out_path),
                "log_path": str(log_path),
                "tokens": tokens,
                "model": resolved_model,
            },
            indent=2,
        )
    )

    # Exit code policy: FAIL = 1, PASS/HOLD = 0. Caller decides on HOLD.
    return 1 if verdict == "FAIL" else 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="voice-gate", description=__doc__)
    ap.add_argument("draft", help="Path to the markdown draft to review.")
    ap.add_argument(
        "--voice-guide",
        default=None,
        help="Path to the voice guide. Auto-detected from conventional client paths if omitted.",
    )
    ap.add_argument("--persona", default=None, help="Optional persona file for biographical context.")
    ap.add_argument("--output", default=None, help="Output path. Defaults to <draft-stem>.VOICE-GATE.md")
    ap.add_argument(
        "--model",
        default=DEFAULT_MODEL,
        help=f"Model or alias (haiku/sonnet/opus). Default: {DEFAULT_MODEL}",
    )
    ap.add_argument(
        "--max-issues",
        type=int,
        default=DEFAULT_MAX_ISSUES,
        help=f"Cap on issues in the report. Default: {DEFAULT_MAX_ISSUES}",
    )
    ap.add_argument("--quiet", action="store_true", help="Suppress stderr progress output.")
    args = ap.parse_args(argv)

    try:
        return run(
            draft=args.draft,
            voice_guide=args.voice_guide,
            persona=args.persona,
            output=args.output,
            model=args.model,
            max_issues=args.max_issues,
            quiet=args.quiet,
        )
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 2
    except RuntimeError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    sys.exit(main())
