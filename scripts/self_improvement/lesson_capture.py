#!/usr/bin/env python3
"""
Lesson capture — the failure-side learning loop.

Three commands:

  add    Append a generalized trigger→advice lesson to memory/lessons.md
         (dedupes against existing advice text).

  mine   Read data/learning/gate_runs.jsonl, group repeated failure
         signatures across runs, and surface candidates that have fired
         at least --min-count times. --write appends them to
         memory/lessons.md as (candidate) entries.

  losers Read the content log and list published pieces graded "loser"
         that are not yet diagnosed in memory/what-doesnt-work.md.

Usage:
  python scripts/self_improvement/lesson_capture.py add \
      --trigger "writing Meta carousel ads" \
      --advice "use instagram_user_id, not instagram_actor_id" \
      --source "Meta API run 2026-06-09"
  python scripts/self_improvement/lesson_capture.py mine
  python scripts/self_improvement/lesson_capture.py mine --min-count 3 --write
  python scripts/self_improvement/lesson_capture.py losers

No dependencies beyond the stdlib. Never requires credentials.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import defaultdict
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
LESSONS_PATH = REPO_ROOT / "memory" / "lessons.md"
ANTIPATTERNS_PATH = REPO_ROOT / "memory" / "what-doesnt-work.md"
LEARNED_HEADER = "## Learned lessons"


def _gate_log_path() -> Path:
    base = os.environ.get("KAI_GATE_LOG_DIR")
    if base:
        return Path(base) / "gate_runs.jsonl"
    return REPO_ROOT / "data" / "learning" / "gate_runs.jsonl"


def _content_log_path() -> Path:
    override = os.environ.get("KAI_CONTENT_LOG")
    if override:
        return Path(override)
    return REPO_ROOT / "data" / "content_log.json"


def normalize_signature(sig: str) -> str:
    """Collapse run-specific detail so the same failure groups across runs."""
    sig = re.sub(r'"[^"]*"', '"<x>"', sig)        # quoted keywords/titles
    sig = re.sub(r"\b\d+(\.\d+)?\b", "<n>", sig)  # counts, scores, lengths
    return sig.strip()


def format_lesson(trigger: str, advice: str, source: str, status: str = "active") -> str:
    today = date.today().isoformat()
    trigger = trigger.strip().rstrip(".")
    if not trigger.lower().startswith("when"):
        trigger = f"When {trigger}"
    advice = advice.strip().rstrip(".")
    return (
        f"- [{today}] ({status}) **{trigger}** → {advice}. "
        f"Source: {source}. Enforced: none"
    )


def append_lessons(lines: list[str]) -> list[str]:
    """Append lesson lines under the Learned lessons header, deduped.

    Returns the lines actually written.
    """
    text = LESSONS_PATH.read_text(encoding="utf-8")
    existing_advice = {
        normalize_signature(line.split("→", 1)[1]) if "→" in line else line
        for line in text.splitlines()
        if line.startswith("- [")
    }
    new_lines = []
    for line in lines:
        key = normalize_signature(line.split("→", 1)[1]) if "→" in line else line
        if key in existing_advice:
            continue
        existing_advice.add(key)
        new_lines.append(line)
    if not new_lines:
        return []
    if LEARNED_HEADER in text:
        head, tail = text.split(LEARNED_HEADER, 1)
        text = head + LEARNED_HEADER + tail.rstrip() + "\n" + "\n".join(new_lines) + "\n"
    else:
        text = text.rstrip() + f"\n\n{LEARNED_HEADER}\n\n" + "\n".join(new_lines) + "\n"
    LESSONS_PATH.write_text(text, encoding="utf-8")
    return new_lines


def cmd_add(args: argparse.Namespace) -> int:
    line = format_lesson(args.trigger, args.advice, args.source or "manual", args.status)
    written = append_lessons([line])
    if written:
        print(f"Added to {LESSONS_PATH.relative_to(REPO_ROOT)}:")
        print(written[0])
    else:
        print("Skipped: an equivalent lesson already exists.")
    return 0


def mine_gate_log(min_count: int) -> list[dict]:
    """Group failure signatures across gate runs; return recurring ones."""
    path = _gate_log_path()
    if not path.exists():
        return []
    groups: dict[tuple[str, str], dict] = defaultdict(
        lambda: {"count": 0, "sources": set(), "example": ""}
    )
    with open(path, encoding="utf-8") as f:
        for raw in f:
            raw = raw.strip()
            if not raw:
                continue
            try:
                rec = json.loads(raw)
            except json.JSONDecodeError:
                continue
            for failure in rec.get("failures", []):
                key = (rec.get("gate", "unknown"), normalize_signature(failure))
                g = groups[key]
                g["count"] += 1
                g["sources"].add(rec.get("source", "?"))
                g["example"] = failure
    candidates = [
        {
            "gate": gate,
            "signature": sig,
            "count": g["count"],
            "distinct_sources": len(g["sources"]),
            "example": g["example"],
        }
        for (gate, sig), g in groups.items()
        if g["count"] >= min_count
    ]
    candidates.sort(key=lambda c: -c["count"])
    return candidates


def cmd_mine(args: argparse.Namespace) -> int:
    candidates = mine_gate_log(args.min_count)
    if not candidates:
        log = _gate_log_path()
        if not log.exists():
            print(f"No gate log yet at {log}. Run the quality gates first.")
        else:
            print(f"No failure signature has recurred {args.min_count}+ times. Nothing to learn yet.")
        return 0

    print(f"Recurring gate failures (≥{args.min_count} occurrences):\n")
    lesson_lines = []
    for c in candidates:
        print(
            f"  {c['count']}× [{c['gate']}] {c['signature']}"
            f"  ({c['distinct_sources']} piece{'s' if c['distinct_sources'] != 1 else ''})"
        )
        lesson_lines.append(
            format_lesson(
                trigger=f"content runs the {c['gate']} gate",
                advice=(
                    f"recurring failure ({c['count']}×): {c['example']} — "
                    f"fix the cause upstream in the brief or contract, "
                    f"or promote a check for it"
                ),
                source=f"mined from gate_runs.jsonl, {c['distinct_sources']} pieces",
                status="candidate",
            )
        )

    if args.write:
        written = append_lessons(lesson_lines)
        print(
            f"\nWrote {len(written)} candidate lesson(s) to "
            f"{LESSONS_PATH.relative_to(REPO_ROOT)} "
            f"({len(lesson_lines) - len(written)} already present)."
        )
        if written:
            print("Review them in /kai-retro: promote, keep, or retire.")
    else:
        print("\nRun with --write to append these as candidate lessons.")
    return 0


def cmd_losers(args: argparse.Namespace) -> int:
    path = _content_log_path()
    if not path.exists():
        print(
            f"No content log found at {path} "
            "(set KAI_CONTENT_LOG to override). Nothing to analyze."
        )
        return 0
    try:
        entries = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        print(f"Could not parse {path}.")
        return 1
    if isinstance(entries, dict):
        entries = entries.get("entries", [])

    diagnosed = ""
    if ANTIPATTERNS_PATH.exists():
        diagnosed = ANTIPATTERNS_PATH.read_text(encoding="utf-8")

    losers = [
        e
        for e in entries
        if isinstance(e, dict)
        and (e.get("performance_30d") or {}).get("grade") == "loser"
        and str(e.get("id", "")) not in diagnosed
    ]
    if not losers:
        print("No undiagnosed losers in the content log.")
        return 0

    print(f"{len(losers)} published piece(s) graded 'loser' with no diagnosis yet:\n")
    for e in losers:
        perf = e.get("performance_30d", {})
        print(
            f"  id={e.get('id')} format={e.get('format')} keyword={e.get('keyword')!r} "
            f"published={e.get('publish_date')} perf={json.dumps(perf.get('gsc', {}))}"
        )
    print(
        f"\nDiagnose each and add an entry to {ANTIPATTERNS_PATH.relative_to(REPO_ROOT)} "
        "under 'Measured losers' (include the id so it isn't re-flagged)."
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Kai failure-side learning loop")
    sub = parser.add_subparsers(dest="command", required=True)

    p_add = sub.add_parser("add", help="Append a lesson to memory/lessons.md")
    p_add.add_argument("--trigger", required=True, help="When does this apply (generalized)")
    p_add.add_argument("--advice", required=True, help="What to do (generalized)")
    p_add.add_argument("--source", help="Where this lesson came from")
    p_add.add_argument("--status", default="active", choices=["active", "candidate"])
    p_add.set_defaults(func=cmd_add)

    p_mine = sub.add_parser("mine", help="Surface recurring gate failures as candidate lessons")
    p_mine.add_argument("--min-count", type=int, default=2, help="Minimum occurrences (default 2)")
    p_mine.add_argument("--write", action="store_true", help="Append candidates to lessons.md")
    p_mine.set_defaults(func=cmd_mine)

    p_losers = sub.add_parser("losers", help="List undiagnosed losers from the content log")
    p_losers.set_defaults(func=cmd_losers)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
