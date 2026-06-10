# What Doesn't Work

Anti-pattern log — the failure-side complement to `knowledge/playbooks/what-works.md`. Published losers, rejected drafts, and approaches that measured badly land here so they aren't retried.

## Format

```
- [YYYY-MM-DD] <format>/<persona>: **<anti-pattern>** — <diagnosis>. Evidence: <30d numbers, gate history, or human verdict>
```

Rules:
- Only add entries with evidence: a 30-day "loser" grade, a human rejection with a stated reason, or 2+ gate failures with the same diagnosis.
- Generalize the anti-pattern, keep the evidence specific.
- During `/kai-retro`, pull new losers from `content_log.json` (`performance_30d.grade == "loser"`) and add a diagnosis for each.
- An anti-pattern confirmed 3+ times should graduate: add a contract constraint, checklist line, or lint rule, then mark it `(promoted)` here.

## Structural anti-patterns (seeded from harness doctrine)

- [2026-06-09] all/all: **Full rewrite on gate failure** — rewriting the whole draft when one dimension fails usually lowers the dimensions that passed. Fix only the named failure. Evidence: retry-policy doctrine, `harness/ARCHITECTURE.md` revision loop design.
- [2026-06-09] all/all: **Binary-contrast hooks ("It's not X, it's Y")** — read as LinkedIn slop, pass subjective scoring, get flagged by humans. Evidence: voice-pattern regex list exists because these recurred (`harness/skills/kai-gate/SKILL.md` step 3).
- [2026-06-09] seo/all: **Reusing study percentages as promises** — "30-50% AI visibility lift" framing triggered overclaim errors and client pushback. Evidence: dedicated regex in `scripts/quality_gates/seo_lint.py`.

## Measured losers

(none yet — populated by `/kai-retro` from 30-day checks)
