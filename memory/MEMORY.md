# Kai Memory Index

Load this file at the start of every session. It is the index for everything Kai has learned — read the topic files below on demand, not all at once.

**Hard cap: this file stays under 200 lines.** When it grows past that, move detail into topic files and keep one-line pointers here. History lives in git, not in this file.

## Topic files

| File | What's in it | Read when |
|------|--------------|-----------|
| `memory/lessons.md` | Dated trigger→advice lessons from corrections, gate failures, and surprises | Before writing content, before any task you've done before |
| `memory/edge-cases.md` | Known edge cases and gotchas in the harness and platform APIs, with enforcement status | Before touching ads APIs, the gate scripts, the self-improvement loop, or connectors |
| `memory/what-doesnt-work.md` | Anti-patterns: published losers and rejected approaches, with the diagnosis | Before picking a hook, angle, or format |
| `knowledge/playbooks/what-works.md` | Auto-extracted winning patterns from 30-day performance checks | Before picking a hook, angle, or format |

## Write triggers

Append a lesson to `memory/lessons.md` (one line, dated, generalized) when any of these happen:

1. You make the same mistake a second time.
2. A human corrects you, and the correction would apply to future work.
3. A quality gate fails twice for the same reason on one piece.
4. A platform, API, or tool behaves differently than its docs or the harness references say.
5. A claim you almost shipped turned out to be wrong or unsourceable.

Generalize at write time: "Meta carousel ads need X" — not "the Acme campaign needed X."

## Graduation ladder

A lesson that keeps mattering must move into a more enforced, more compressed form. Never let the same lesson sit as prose forever:

```
lessons.md entry  →  CLAUDE.md rule or checklist line  →  lint rule / contract check + golden case
```

When you promote a lesson into a gate script or banned-word list, you MUST add a golden corpus case (`evals/golden/`) proving the new check, then run `python scripts/quality_gates/golden_check.py`. Mark the lesson `promoted` in `lessons.md` — do not delete it.

## Mining

Gate scripts append every run to `data/learning/gate_runs.jsonl`. Surface repeated failure signatures as candidate lessons:

```bash
python scripts/self_improvement/lesson_capture.py mine          # show candidates
python scripts/self_improvement/lesson_capture.py mine --write  # append candidates to lessons.md
```

Run `/kai-retro` monthly (or after any heavy content sprint) to triage candidates: promote, keep, or retire.

## Current standing lessons (index)

- Platform/API gotchas are catalogued in `memory/edge-cases.md` — 18 entries. EC-06 (NL placeholders), EC-11 (defaults rewrite validation), and EC-12 (pending-check reconciliation) were promoted to code on 2026-06-10 (`tests/test_promoted_edge_cases.py`); the rest with `enforcement: none` are graduation candidates.
- No published losers analyzed yet — `what-doesnt-work.md` is seeded with structural anti-patterns only.
