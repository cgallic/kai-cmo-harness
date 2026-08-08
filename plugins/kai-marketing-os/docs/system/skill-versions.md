---
title: "Skill Versions — v1 (procedural) and v2 (goal-oriented)"
type: doctrine
created: 2026-07-28
updated: 2026-07-28
status: canonical
---

# Skill Versions

Kai ships every skill in two forms. Both are supported. They differ in **how much of the route they prescribe**, because that is what different models need.

| | **v1 — procedural** | **v2 — goal-oriented** |
|---|---|---|
| Location | `harness/skills/` | `harness/skills-v2/` |
| Plugin | `kai` | `kai-v2` |
| Shape | Phases, numbered steps, explicit question lists, output templates | Objective, done-when, constraints, context, escalate-when |
| Assumes | The model needs the route laid out | The model can plan the route from the destination |
| Best for | Smaller and older models, tightly repeatable output, high-compliance work where deviation is the risk | Current frontier models, work where the situation varies and the route should adapt |

**Neither is deprecated.** v1 is not a legacy shim, and v2 is not a beta. A team running Haiku-class models, or one that needs byte-identical output shape every run, is correctly served by v1.

---

## Why two versions instead of one

Anthropic's current guidance is that the latest models perform best when given the complete task specification up front and left to run, and that they handle multi-step reasoning internally rather than needing steps enumerated. The same guidance warns that legacy harness scaffolding and explicit self-verification instructions actively degrade output on these models — they cause over-verification and over-procedure.

That guidance does not generalize downward. A smaller model given only an objective will often skip the provenance step, miss the policy reference, or produce a shape the downstream gate rejects. For that model, the phase list is doing real work.

A single merged file cannot serve both. If the scaffolding stays in the document, a capable model still reads it and is still pulled toward it — which is the exact failure the v2 rewrite exists to remove. **Keeping the versions physically separate is the point, not an accident of packaging.**

---

## What stays identical across versions

These are not style choices, so they do not change with the version:

- **Frontmatter `name` and `description`.** Routing and trigger matching must behave identically. A user typing the same thing reaches the same skill in either plugin.
- **The knowledge base.** `knowledge/`, `harness/references/`, `harness/skill-contracts/`, and `harness/eco-floors.yaml` are shared by symlink. There is one copy of the frameworks.
- **The quality gates.** Four U's, banned words, SEO lint, provenance lint, policy compliance.
- **The governance rules.** Instruction contract, Data Provenance Rule, KaiCalls Fit Rule, approval doctrine, ECO floors.
- **Output locations.** Both versions write to the same `workspace/` paths, so downstream tooling does not branch on version.

**A v2 skill is never more permissive than its v1 counterpart.** Removing procedure never means removing a constraint. If v1 requires the collector before writing a number, v2 requires it too — stated as a constraint rather than as a step.

---

## What v2 removes

Only knowledge the model can derive:

- Generic work sequences: "first research, then outline, then draft, then review."
- Phase numbering that exists to order work the model would order correctly anyway.
- Fixed interview scripts ("ask these seven questions") where the real requirement is "know these seven things before you can proceed."
- Output templates that restate structure already defined in the skill contract.
- Self-verification instructions ("double-check your work," "verify before returning"). ECO's checking is out of band, in a gate the actor does not control.
- Instructions to spawn a subagent to review the skill's own output.

## What v2 keeps

Everything the model cannot derive from the objective:

- Which framework files to load, and their paths.
- Platform policy references and the rule that they load *before* writing.
- Provenance requirements: which collector, which mode, what a data gap is.
- Format contracts: word counts, structure, thresholds, gate minimums.
- House frameworks and their load-when triggers.
- Approval requirements and the ECO floor.
- Where output goes.

---

## The v2 skill shape

```markdown
---
name: kai-<skill>            # identical to v1
description: <identical to v1 — routing must not change>
---

# /kai-<skill> — <the outcome, not the activity>

> **Kai root note:** <identical to v1>

## Objective
What must exist in the world when this is finished. One paragraph. States a
result, not an activity.

## Done when
The ECO floor for this work type, plus the specific evidence that proves it.
Cites harness/eco-floors.yaml.

## Constraints
Policy, provenance, legal, brand, approval, spend. Everything that bounds the
route without prescribing it. This section is never shorter than v1's
equivalent rules.

## Context
Where the knowledge lives: framework paths, the skill contract, the checklist,
the relevant channel guide, prior art. A lookup table, not a reading order.

## Escalate when
The conditions that require asking instead of deciding.
```

Sections may carry skill-specific additions — a scoring rubric, a decision table, a policy matrix — when they encode real knowledge. They may not carry a phase list.

---

## Choosing a version

**Install `kai-v2`** when running Claude Opus 5, Sonnet 5, or a comparable current frontier model, and the work benefits from adapting to what the situation turns out to be.

**Install `kai`** when running smaller or older models, when output shape must be identical run to run, or when an operator wants to read exactly what the agent will do before it does it.

Both plugins can be installed together. Claude Code namespaces them — `/kai:kai-write` and `/kai-v2:kai-write` — so there is no trigger collision.

---

## Keeping them in sync

`scripts/doctor.py` enforces parity:

- Every v1 `kai-*` skill has a v2 counterpart.
- Frontmatter `name` and `description` match exactly between versions.
- No v2 skill reintroduces a phase list.

A new skill is added to both. A change to a shared rule — a policy reference, a gate threshold, a provenance requirement — lands in both. Only the route differs.

Related: `docs/system/eco-completion-standard.md` · `docs/system/long-horizon-operating-contract.md` · `AGENTS.md` ("Goals over procedures")
