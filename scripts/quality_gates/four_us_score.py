#!/usr/bin/env python3
"""
Four U's Scorer — Kai Harness Quality Gate

Scores content on:
  Unique (1-4): Does it say something competitors don't?
  Useful (1-4): Does it solve a concrete problem?
  Ultra-specific (1-4): Numbers, names, timeframes, outcomes?
  Urgent (1-4): Reason to read now vs later?

Minimum passing score: 12/16
Any single U < 2 = hard fail regardless of total

The judge is pluggable. Gemini is used when GEMINI_API_KEY is set, but any agent
(Claude, Codex, a human reviewer) can score instead: emit the rubric with
--prompt-only, then hand the resulting JSON back via --scores. Thresholds,
report formatting and gate logging are identical either way, so a result is
comparable no matter who judged it.

Usage:
  python3 four_us_score.py --text "content here"
  python3 four_us_score.py --file draft.md
  python3 four_us_score.py --file draft.md --json

  # agent-scored, no API key required
  python3 four_us_score.py --file draft.md --prompt-only
  python3 four_us_score.py --file draft.md --scores '{"unique":3,"useful":4,"ultra_specific":3,"urgent":2}'
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Windows consoles default to cp1252 and cannot encode the report's ✅ / █ glyphs,
# which made every gate run crash with UnicodeEncodeError instead of reporting.
for _stream in (sys.stdout, sys.stderr):
    _reconfigure = getattr(_stream, "reconfigure", None)
    if _reconfigure is not None:
        try:
            _reconfigure(encoding="utf-8")
        except ValueError:
            pass

sys.path.insert(0, str(Path(__file__).resolve().parent))
from gate_logger import log_gate_result

MIN_TOTAL = 12
MIN_SINGLE = 2
DIMENSIONS = ("unique", "useful", "ultra_specific", "urgent")

SCORING_PROMPT = """You are a ruthless content quality scorer using the Four U's framework.

Score the following content. Be harsh and specific. A score of 4 is rare and must be truly exceptional.

UNIQUE (1-4):
4 = Genuinely novel angle no competitor has — specific mechanism, counterintuitive data, original research
3 = Fresh perspective on familiar topic — some originality in framing or examples
2 = Standard take with minor original elements — competent but forgettable
1 = Generic — could have been written by anyone with a Google search

USEFUL (1-4):
4 = Solves a specific, painful problem completely — reader can act immediately
3 = Helpful with minor gaps — mostly actionable
2 = Partially useful — more inspirational than practical
1 = Mostly theoretical — no clear next step for reader

ULTRA-SPECIFIC (1-4):
4 = Specific numbers, percentages, timeframes, named examples, outcomes throughout
3 = Some specifics but could go deeper — 2-3 concrete data points
2 = Vague claims with few anchors — "many businesses", "often", "significant"
1 = Pure generalities — not a single number or named example

URGENT (1-4):
4 = Clear reason to read/act NOW — trend with deadline, cost of delay quantified, seasonal window
3 = Moderately timely — relevant to current conditions but not time-sensitive
2 = Could read this any time — no urgency signal
1 = Evergreen with no hook to read today

Content to score:
---
{content}
---

Return ONLY valid JSON, no explanation outside the JSON:
{{
  "unique": <1-4>,
  "useful": <1-4>,
  "ultra_specific": <1-4>,
  "urgent": <1-4>,
  "notes": {{
    "unique": "specific critique and suggestion",
    "useful": "specific critique and suggestion",
    "ultra_specific": "specific critique and suggestion",
    "urgent": "specific critique and suggestion"
  }}
}}"""


def parse_agent_scores(raw: str) -> dict:
    """Validate scores produced by an agent judge instead of the Gemini call."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        scores = json.loads(raw.strip())
    except json.JSONDecodeError as exc:
        print(f"ERROR: --scores is not valid JSON: {exc}", file=sys.stderr)
        sys.exit(2)
    if not isinstance(scores, dict):
        print("ERROR: --scores must be a JSON object", file=sys.stderr)
        sys.exit(2)

    missing = [d for d in DIMENSIONS if d not in scores]
    if missing:
        print(f"ERROR: --scores is missing dimension(s): {', '.join(missing)}", file=sys.stderr)
        sys.exit(2)
    for dimension in DIMENSIONS:
        try:
            scores[dimension] = int(scores[dimension])
        except (TypeError, ValueError):
            print(f"ERROR: --scores '{dimension}' must be an integer 1-4", file=sys.stderr)
            sys.exit(2)
        if not MIN_SINGLE - 1 <= scores[dimension] <= 4:
            print(
                f"ERROR: --scores '{dimension}' is {scores[dimension]}; must be 1-4",
                file=sys.stderr,
            )
            sys.exit(2)
    if not isinstance(scores.get("notes"), dict):
        scores["notes"] = {}
    return scores


def score_content(content: str) -> dict:
    try:
        from google import genai as google_genai
    except ImportError:
        print(
            "ERROR: the 'google-genai' package is required for Four U's scoring "
            "(pip install google-genai). The offline gates (banned_word_check.py, "
            "seo_lint.py) run without it.",
            file=sys.stderr,
        )
        sys.exit(2)
    try:
        from dotenv import load_dotenv
        load_dotenv("/opt/cmo-analytics/.env")
        load_dotenv()
    except ImportError:
        pass
    if not os.environ.get("GEMINI_API_KEY"):
        print(
            "ERROR: GEMINI_API_KEY is not set. Set it in the environment or .env. "
            "Run 'python scripts/doctor.py' to see everything else this affects.",
            file=sys.stderr,
        )
        sys.exit(2)
    client = google_genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=SCORING_PROMPT.format(content=content[:8000]),
    )

    if not response.text:
        print("ERROR: the model returned an empty response", file=sys.stderr)
        sys.exit(2)
    raw = response.text.strip()
    # Strip markdown if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


def format_report(scores: dict, as_json: bool = False) -> str:
    total = scores["unique"] + scores["useful"] + scores["ultra_specific"] + scores["urgent"]
    passed = total >= MIN_TOTAL and all(
        scores[k] >= MIN_SINGLE for k in ["unique", "useful", "ultra_specific", "urgent"]
    )

    if as_json:
        return json.dumps(
            {
                "scores": {
                    "unique": scores["unique"],
                    "useful": scores["useful"],
                    "ultra_specific": scores["ultra_specific"],
                    "urgent": scores["urgent"],
                    "total": total,
                },
                "passed": passed,
                "notes": scores.get("notes", {}),
            },
            indent=2,
        )

    lines = []
    status = "✅ GATE PASS" if passed else "❌ GATE FAIL"
    lines.append(f"\n{status}: Four U's Score {total}/16")
    lines.append("─" * 40)

    labels = {
        "unique": "Unique",
        "useful": "Useful",
        "ultra_specific": "Ultra-Specific",
        "urgent": "Urgent",
    }

    for key, label in labels.items():
        score = scores[key]
        bar = "█" * score + "░" * (4 - score)
        fail_flag = " ← FAIL (must be ≥2)" if score < MIN_SINGLE else ""
        lines.append(f"  {label:<16} {bar} {score}/4{fail_flag}")
        note = scores.get("notes", {}).get(key, "")
        if note:
            lines.append(f"    └ {note}")

    lines.append("─" * 40)

    if not passed:
        lines.append("  REWRITE REQUIRED before publishing.")
        fails = []
        if total < MIN_TOTAL:
            fails.append(f"  Total {total}/16 is below minimum {MIN_TOTAL}/16")
        for key, label in labels.items():
            if scores[key] < MIN_SINGLE:
                fails.append(f"  {label} ({scores[key]}/4) is below minimum {MIN_SINGLE}/4")
        lines.extend(fails)
    else:
        lines.append("  Content meets quality threshold. Proceed to publish gate.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Four U's Quality Gate Scorer")
    parser.add_argument("--text", help="Content text to score")
    parser.add_argument("--file", help="Path to content file")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument(
        "--prompt-only",
        action="store_true",
        help="Print the scoring rubric for an agent judge and exit; no API call",
    )
    parser.add_argument(
        "--scores",
        help='Scores from an agent judge, e.g. \'{"unique":3,"useful":4,'
        '"ultra_specific":3,"urgent":2}\'. Skips the Gemini call entirely.',
    )
    args = parser.parse_args()

    if not args.text and not args.file:
        parser.error("Provide --text or --file")

    if args.file:
        with open(args.file, encoding="utf-8") as f:
            content = f.read()
    else:
        content = args.text

    if not content.strip():
        print("ERROR: Empty content", file=sys.stderr)
        sys.exit(1)

    if args.prompt_only:
        print(SCORING_PROMPT.format(content=content[:8000]))
        sys.exit(0)

    scores = parse_agent_scores(args.scores) if args.scores else score_content(content)
    report = format_report(scores, as_json=args.json)
    print(report)

    total = scores["unique"] + scores["useful"] + scores["ultra_specific"] + scores["urgent"]
    passed = total >= MIN_TOTAL and all(
        scores[k] >= MIN_SINGLE for k in ["unique", "useful", "ultra_specific", "urgent"]
    )
    failures = []
    if total < MIN_TOTAL:
        failures.append(f"total_below_minimum:{total}/16")
    for k in ["unique", "useful", "ultra_specific", "urgent"]:
        if scores[k] < MIN_SINGLE:
            failures.append(f"dimension_below_minimum:{k}:{scores[k]}/4")
    log_gate_result(
        gate="four_us_score",
        passed=passed,
        source=args.file,
        failures=failures,
        stats={
            "total": total,
            "judge": "agent" if args.scores else "gemini",
            **{k: scores[k] for k in DIMENSIONS},
        },
    )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
