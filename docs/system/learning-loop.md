# The Kai Learning Loop

How the harness captures edge cases, learns from failures and wins, and hardens itself over time — without a database, using files and git.

This doc is doctrine. The operating surface is `memory/MEMORY.md` (always loaded), the `/kai-retro` skill (the triage cycle), and `scripts/self_improvement/lesson_capture.py` (the mechanism).

## Design principles

These come from the systems that demonstrably work — Claude Code's two-tier memory, the devin.cursorrules Lessons pattern, Voyager's executable skill library, Reflexion's retry-with-diagnosis, and eval-driven gate development:

1. **Two tiers, two write paths.** Humans write doctrine (CLAUDE.md, checklists, contracts). The agent writes learnings (`memory/*.md`, `data/learning/*.jsonl`). Both are plain text a human can audit, edit, and revert via git.
2. **Volatile capture, curated promotion.** Capture is cheap and allowed to be noisy (JSONL gate logs, `candidate` lessons). Promotion is deliberate: a reviewed edit, visible in a diff. Memories that survive contact with reality get promoted; the rest get retired.
3. **The stored artifact should be executable.** A lesson that can be a regex, a threshold, or a checklist line must become one. Prose advice decays; lint rules don't. The gate scripts *are* the skill library.
4. **Gates are oracles, so gates get regression tests.** Every gate change must keep `evals/golden/` passing and should add a case. Otherwise "learning" can silently break the thing that enforces quality.
5. **Bounded growth.** `memory/MEMORY.md` stays under 200 lines. Lessons are one-liners, generalized at write time so near-duplicates merge. Old entries are marked `retired`, never deleted — git holds history, context windows don't have to.

## The full loop

```
                    ┌────────────────────────────────────────────┐
                    │                 CAPTURE                    │
                    │                                            │
 gate runs ───────► data/learning/gate_runs.jsonl  (automatic)   │
 corrections ─────► memory/lessons.md              (write trigger)│
 30-day losers ───► memory/what-doesnt-work.md     (/kai-retro)  │
 30-day winners ──► knowledge/playbooks/what-works.md (cron)     │
 platform surprises► memory/edge-cases.md          (write trigger)│
                    └───────────────┬────────────────────────────┘
                                    │  /kai-retro (monthly or post-sprint)
                    ┌───────────────▼────────────────────────────┐
                    │                 TRIAGE                     │
                    │  lesson_capture.py mine  → candidates      │
                    │  lesson_capture.py losers → diagnoses      │
                    │  promote / keep / merge / retire           │
                    └───────────────┬────────────────────────────┘
                                    │  graduation ladder
                    ┌───────────────▼────────────────────────────┐
                    │                 HARDEN                     │
                    │  lint rule / contract check  (preferred)   │
                    │  checklist line                            │
                    │  CLAUDE.md / framework rule  (last resort) │
                    │  + golden corpus case        (mandatory)   │
                    └───────────────┬────────────────────────────┘
                                    │
                    ┌───────────────▼────────────────────────────┐
                    │                 PROVE                      │
                    │  golden_check.py — gate verdicts unchanged │
                    │  scripts/doctor.py — harness self-intact   │
                    │  CI runs both on every push                │
                    └────────────────────────────────────────────┘
```

## Capture: what writes where

| Signal | Destination | Writer | Trigger |
|--------|-------------|--------|---------|
| Every gate run (pass or fail, with failure signatures) | `data/learning/gate_runs.jsonl` | `gate_logger.py`, wired into the gate CLIs | automatic |
| Correction received, repeated mistake, platform surprise | `memory/lessons.md` | the agent, via `lesson_capture.py add` or direct edit | the five write triggers in `memory/MEMORY.md` |
| Harness/API sharp edges with enforcement status | `memory/edge-cases.md` | the agent during retro or incident | new gotcha discovered |
| Published pieces graded `loser` at 30 days | `memory/what-doesnt-work.md` | the agent during `/kai-retro` | `lesson_capture.py losers` surfaces them |
| Published pieces graded `winner` at 30 days | `knowledge/playbooks/what-works.md` | `pattern_extract.py` (cron) | existing pipeline |

The JSONL log is machine-local (gitignored under `data/`). The markdown memory is git-backed and travels with the repo — clone the repo, inherit the lessons.

### Lesson schema

One line, trigger→advice, generalized:

```
- [YYYY-MM-DD] (status) **When <trigger>** → <advice>. Source: <origin>. Enforced: <path or none>
```

`Enforced:` is the load-bearing field. Every `none` is a standing question: why isn't this a check yet?

### Retry-with-diagnosis

When a gate fails during the content pipeline, the revision prompt must name the specific failing dimension or rule ("failed Four U's on Urgent: no time-bound reason"), not "improve the draft." If the **same diagnosis appears twice on one piece**, that's write-trigger #3: log it as a lesson before escalating to a human. The 2-retry cap is unchanged.

## Triage: /kai-retro

Monthly, or after any sprint with 5+ gated pieces. The skill (`harness/skills/kai-retro/SKILL.md`) does five things: mine, diagnose losers, triage every lesson, graduate promotions, refresh the index. Verdicts are promote / keep / merge / retire — never silent deletion.

## Harden: the graduation ladder

```
lessons.md entry → CLAUDE.md rule or checklist line → lint rule / contract check + golden case
```

Each step is fewer tokens and more enforcement. The end state of a good lesson is that nobody needs to remember it.

A promotion into any gate script (`banned_word_check.py` tiers, `seo_lint.py` patterns, contract `deterministic_checks`) **must** ship with a golden case in `evals/golden/manifest.json`. Run `python scripts/quality_gates/golden_check.py` before committing. Promotions that introduce a new hard block need human approval — they change publishing behavior.

## Prove: self-validation

Two commands keep the harness honest for anyone who clones it:

```bash
python scripts/doctor.py                       # preflight: referenced files, gates, deps, creds
python scripts/quality_gates/golden_check.py   # gate verdicts unchanged
```

CI (`.github/workflows/quality-gates.yml`) runs both on every push and PR. If CLAUDE.md references a file that doesn't exist, or a gate edit flips a known verdict, the build fails.

## Growth control

- `memory/MEMORY.md` ≤ 200 lines (hard cap; detail goes to topic files).
- Lessons are single lines; anything longer belongs in `edge-cases.md` or a framework doc.
- `lesson_capture.py` dedupes at write time using normalized advice text.
- Retired and promoted entries stay in place as one-liners; full history is git's job.
- The retro merges near-duplicates into the more general lesson.

## What this loop does NOT do

- It does not auto-apply gate changes. Promotion is always a reviewed edit.
- It does not learn from unverified vibes. Lessons need a source: a log line, a human correction, a measured outcome.
- It does not replace the winner-side loop (`performance_check.py` → `pattern_extract.py` → `harness_defaults_update.py`). It adds the failure side that loop never had.
