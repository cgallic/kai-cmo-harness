#!/usr/bin/env python3
"""
Banned Word Scanner — Kai Harness Quality Gate

Tiers:
  Tier 1 (HARD BLOCK): must rewrite before publishing
  Tier 2 (FLAG): suggest replacement, warn
  Tier 3 (WARN): reduce frequency

Usage:
  python3 banned_word_check.py --text "content here"
  python3 banned_word_check.py --file draft.md
  python3 banned_word_check.py --file draft.md --json
"""

import argparse
import json
import re
import sys

TIER1 = [
    "leverage",
    "utilize",
    "utilise",
    "synergy",
    "synergies",
    "innovative",
    "innovation",
    "deep dive",
    "circle back",
    "touch base",
    "moving forward",
    "at the end of the day",
    "it's important to note",
    "its important to note",
    "in today's rapidly evolving",
    "in today's fast-paced",
    "i'd be happy to help",
    "id be happy to help",
    "great question",
    "as previously mentioned",
    "first and foremost",
    "in conclusion",
    "in order to",
    "going forward",
    "game-changer",
    "game changer",
    "paradigm shift",
    "thought leader",
    "thought leadership",
    "best practices",
    "cutting-edge",
    "cutting edge",
    "state-of-the-art",
    "state of the art",
    "seamless",
    "robust",
    "scalable",
    "holistic",
    "empower",
    "empowering",
    "transformative",
    "transforming",
    "revolutionize",
    "revolutionizing",
    "ecosystem",
    "bandwidth",
    "low-hanging fruit",
    "low hanging fruit",
    "peel back the layers",
    "double-click on",
    "double click on",
    "unpack",
    "dive deep",
    "take it to the next level",
    "next level",
    "move the needle",
    "value proposition",
    "value add",
    "value-add",
    "key takeaway",
    "key takeaways",
    "actionable insights",
    "actionable steps",
    "pain points",
]

TIER2_REPLACEMENTS = {
    "impact": ["effect", "result", "outcome", "change — be specific"],
    "solution": ["answer", "fix", "tool — name what it actually does"],
    "space": ["industry", "market", "field — name it"],
    "journey": ["process", "path", "steps — be specific"],
    "stakeholders": ["clients", "team", "partners — name them"],
    "facilitate": ["help", "run", "manage"],
    "leverage": ["use", "apply", "build on"],
    "utilize": ["use"],
    "innovative": ["first", "only", "new as of [date]"],
    "seamless": ["smooth", "simple", "fast — give the number"],
}

TIER3 = [
    "very",
    "really",
    "just",
    "actually",
    "basically",
    "literally",
    "honestly",
    "frankly",
    "clearly",
    "obviously",
    "simply",
    "things",
    "stuff",
    "a lot",
    "kind of",
    "sort of",
]


def find_hits(text: str, words: list[str]) -> list[dict]:
    hits = []
    text_lower = text.lower()
    for word in words:
        pattern = re.compile(r"\b" + re.escape(word.lower()) + r"\b")
        matches = list(pattern.finditer(text_lower))
        if matches:
            hits.append(
                {
                    "word": word,
                    "count": len(matches),
                    "positions": [m.start() for m in matches],
                }
            )
    return hits


def check_content(text: str) -> dict:
    tier1_hits = find_hits(text, TIER1)
    tier2_hits = find_hits(text, list(TIER2_REPLACEMENTS.keys()))
    tier3_hits = find_hits(text, TIER3)

    # Filter tier2 to only show words not already in tier1
    tier1_words_lower = {w.lower() for w in TIER1}
    tier2_hits = [h for h in tier2_hits if h["word"].lower() not in tier1_words_lower]

    passed = len(tier1_hits) == 0

    return {
        "passed": passed,
        "tier1": tier1_hits,
        "tier2": tier2_hits,
        "tier3": tier3_hits,
    }


def get_context(text: str, position: int, window: int = 60) -> str:
    start = max(0, position - window)
    end = min(len(text), position + window)
    snippet = text[start:end].replace("\n", " ")
    return f"…{snippet}…"


def format_report(result: dict, text: str, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(result, indent=2)

    lines = []
    status = "✅ GATE PASS" if result["passed"] else "❌ GATE FAIL"
    tier1_count = sum(h["count"] for h in result["tier1"])
    tier2_count = sum(h["count"] for h in result["tier2"])
    tier3_count = sum(h["count"] for h in result["tier3"])

    lines.append(f"\n{status}: Banned Word Check")
    lines.append("─" * 40)

    if result["tier1"]:
        lines.append(f"\n  TIER 1 — HARD BLOCK ({tier1_count} hit{'s' if tier1_count != 1 else ''})")
        for hit in result["tier1"]:
            lines.append(f"  ✗ \"{hit['word']}\" × {hit['count']}")
            ctx = get_context(text, hit["positions"][0])
            lines.append(f"    Context: {ctx}")
            replacements = TIER2_REPLACEMENTS.get(hit["word"].lower())
            if replacements:
                lines.append(f"    Replace with: {' | '.join(replacements)}")

    if result["tier2"]:
        lines.append(f"\n  TIER 2 — FLAG ({tier2_count} hit{'s' if tier2_count != 1 else ''})")
        for hit in result["tier2"]:
            replacements = TIER2_REPLACEMENTS.get(hit["word"].lower(), ["[be more specific]"])
            lines.append(f"  ⚠ \"{hit['word']}\" × {hit['count']} → {' | '.join(replacements)}")

    if result["tier3"]:
        lines.append(f"\n  TIER 3 — WEAK QUALIFIERS ({tier3_count} total)")
        summary = ", ".join(f"\"{h['word']}\"×{h['count']}" for h in result["tier3"])
        lines.append(f"  ⚠ {summary}")
        lines.append("    Cut or replace with specific language.")

    if result["passed"] and not result["tier2"] and not result["tier3"]:
        lines.append("  Clean. No banned words detected.")
    elif result["passed"]:
        lines.append("\n  Tier 1 clear. Review flagged Tier 2/3 before publishing.")

    if not result["passed"]:
        lines.append("\n  REWRITE REQUIRED. Remove all Tier 1 words before proceeding.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Banned Word Quality Gate")
    parser.add_argument("--text", help="Content text to check")
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

    result = check_content(content)
    report = format_report(result, content, as_json=args.json)
    print(report)
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
