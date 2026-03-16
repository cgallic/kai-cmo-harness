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

Usage:
  python3 four_us_score.py --text "content here"
  python3 four_us_score.py --file draft.md
  python3 four_us_score.py --file draft.md --json
"""

import argparse
import json
import os
import sys

from google import genai as google_genai
import os

MIN_TOTAL = 12
MIN_SINGLE = 2

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


def score_content(content: str) -> dict:
    from dotenv import load_dotenv
    load_dotenv("/opt/cmo-analytics/.env")
    client = google_genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    response = client.models.generate_content(
        model="gemini-2.0-flash",
        contents=SCORING_PROMPT.format(content=content[:8000]),
    )

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
    args = parser.parse_args()

    if not args.text and not args.file:
        parser.error("Provide --text or --file")

    if args.file:
        with open(args.file) as f:
            content = f.read()
    else:
        content = args.text

    if not content.strip():
        print("ERROR: Empty content", file=sys.stderr)
        sys.exit(1)

    scores = score_content(content)
    report = format_report(scores, as_json=args.json)
    print(report)

    total = scores["unique"] + scores["useful"] + scores["ultra_specific"] + scores["urgent"]
    passed = total >= MIN_TOTAL and all(
        scores[k] >= MIN_SINGLE for k in ["unique", "useful", "ultra_specific", "urgent"]
    )
    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
