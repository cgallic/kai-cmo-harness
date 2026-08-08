---
title: "Long-Horizon Operating Contract"
type: doctrine
created: 2026-07-28
updated: 2026-07-28
status: canonical
---

# Long-Horizon Operating Contract

> How Kai runs work that outlives a single context window, a single session, or the operator's attention.
>
> Completion standard: `docs/system/eco-completion-standard.md` · Floors: `harness/eco-floors.yaml` · Entry point: `/kai-goal`

A short session ends when the operator reads the answer. A long-horizon run ends when a gate says the floor was met. Everything in this document exists to make the second kind of ending trustworthy.

---

## 1. Give the agent a goal, not a procedure

The models Kai runs on pursue objectives across many steps: they interpret a goal, form a plan, pick tools, observe results, recover from failures, and continue until a stopping condition looks satisfied. Anthropic's current guidance is explicit that the latest models perform best when given **the complete task specification up front and left to run**, and that they handle multi-step reasoning internally rather than needing the steps enumerated.

That changes what a good instruction looks like.

| Skill-oriented (old) | Goal-oriented (current) |
|---|---|
| "Phase 1: ask 7 discovery questions. Phase 2: load these 5 files. Phase 3: fill this table." | "Objective: a stage-appropriate 90-day marketing plan the founder can start on Monday. Done when: E3/C3/O1 — human-approved document, non-producer review, and every P0 recommendation names the metric it targets." |
| Prescribes the path | Declares the destination, the floor, and the constraints |
| Breaks when reality differs from the script | Adapts, because the agent owns the route |
| Completion = last phase executed | Completion = gate verdict |

**Write objectives, constraints, and success criteria. Let the agent choose the route.**

A Kai objective has five parts and nothing else is mandatory:

```yaml
objective:      What result must exist in the world when this is finished.
done_when:      The ECO floor (E/C/O) plus the specific evidence that proves it.
constraints:    Budget, brand, legal, policy, channels that are off limits, spend ceiling.
context:        Where to find the brand, the data, and the prior art.
escalate_when:  The conditions where the agent must stop and ask instead of deciding.
```

Everything else — which framework to load, which skill to route through, what order to work in — is the agent's call. The Framework Map in `AGENTS.md` is a lookup table it consults, not a script it executes.

### What still belongs in a skill

Goal-orientation does not delete procedure. It relocates it. Procedure belongs in a skill when it encodes knowledge the agent cannot derive:

- Platform-specific rules and policy references.
- Provenance requirements (which collector to run, what to declare).
- The house frameworks and their load-when triggers.
- Format contracts: word counts, structure, thresholds.

Procedure does **not** belong in a skill when it is a generic work sequence the model already knows: "first research, then outline, then draft, then review." Deleting that kind of scaffolding makes the skill shorter and the output better.

### Do not tell the agent to double-check itself

Current guidance is that explicit self-verification instructions ("verify your work," "use a subagent to double-check") cause **over-verification** on the latest models and should be removed. ECO is compatible with this precisely because its verification is out of band: the actor is told *what floor it must clear*, never told *to grade itself*. The grading happens in `scripts/quality_gates/eco_gate.py`, which the actor does not control.

Same principle for subagents: delegate only for large, genuinely independent, parallelizable tracks. Never spawn a subagent to check the parent's work — that is not independence, it is the same substrate with a different name, and the ECO honest-quorum rule discards it.

---

## 2. The stopping condition is a verdict, not a feeling

A long-horizon run must never stop because the agent judges itself finished. It stops when one of these is true:

| Stop reason | What gets written |
|---|---|
| Gate returns SHIPPED or CLOSED at the declared floor | ECO record with a `computed` block |
| An external condition blocks progress | Failure record, `condition: blocked`, with `next_check_at` |
| The attempt ended below the floor | Failure record, `condition: failed_attempt`, naming the axis |
| Evidence cannot support the claim yet | Failure record, `condition: unproven` |
| An `escalate_when` condition fired | Operator question, run paused, state saved |

There is no sixth reason. "I think this is good enough" is not a stopping condition, and neither is "the last phase of the skill finished."

**Zero output is a result to explain, not a healthy heartbeat.** The audit that produced ECO found 4,777 of 4,801 heartbeats reporting alive while producing no artifacts. A scheduled Kai task that produces nothing must write a failure record saying why. A green tick with an empty output directory is a bug.

---

## 3. State that survives a context window

Long runs lose their context. Design for that from the first turn, not when the window fills.

Kai keeps three kinds of state, each in the format that suits it:

```text
workspace/runs/<run-id>/
├── objective.yaml     # immutable: the goal, floor, constraints, escalations
├── state.json         # structured: work items, ECO grades, evidence locators
├── progress.md        # freeform: what happened, what's next, open hypotheses
└── output/            # the actual artifacts
```

- **`objective.yaml` is written once and never edited by the agent.** If the objective changes, that is a new run. An agent that can rewrite its own goal has no goal.
- **`state.json` is structured** because the agent needs to reason over it: which items are open, what each one's floor is, which evidence exists. Structured formats help the model understand schema requirements.
- **`progress.md` is prose** because progress notes, hypotheses, and confidence levels do not fit a schema.
- **Git is the checkpoint layer.** Commit after each work item reaches a verdict. Git gives a log of what was done and restorable checkpoints, and the latest models are notably good at reconstructing state from a repository.

### Resume protocol

When a run resumes in a fresh context window, start prescriptively rather than compacting:

```text
1. pwd — you may only read and write inside this run directory and the project.
2. Read objective.yaml. It is the goal. You did not write it and may not change it.
3. Read state.json and progress.md.
4. Run: python -m scripts.quality_gates.eco_gate debt
5. Pick up the highest-priority open work item. Do not restart completed items.
```

Fresh context beats compaction for this shape of work: the filesystem already holds the state, and a clean window reads it without carrying forward drift.

### Do not stop early to save tokens

The harness compacts context automatically. Wrapping up prematurely because the budget looks tight produces half-finished work that reports as complete — exactly the failure ECO exists to catch. The correct behavior near a context limit is to **save state and continue**, not to summarize and stop.

---

## 4. Autonomy scales with reversibility, not with confidence

The control on an autonomous run should scale with **capability × autonomy × consequence**. In marketing terms, that maps to a simple gradient:

| Tier | Examples | Authority |
|---|---|---|
| **Free** | Writing drafts, running gates, reading connectors, local file edits, research | Proceed. These are reversible and internal. |
| **Approve** | Publishing to a CMS or social account, sending email, creating or editing ads, changing budgets, mutating a client's site | Human approval on the exact bytes (E3) before execution. No exceptions. |
| **Escalate** | Spend above the mandate ceiling, regulated claims, anything in a Special Ad Category, a policy question with no clear answer, contradictory instructions | Stop and ask. Save state first. |

The approval tier is not advisory. `harness/eco-floors.yaml` encodes it as an invariant: work with `external_effect` or `spend_authority` cannot reach SHIPPED without hash-pinned approval evidence, no matter what other evidence exists.

Two standing prohibitions for autonomous runs:

- **Never use a destructive shortcut to clear an obstacle.** Do not bypass a gate, disable a check, delete unfamiliar files, or force-push to get unblocked. An obstacle is a failure record, not a reason to lower the bar.
- **Never optimize the measurement instead of the objective.** If the easiest route to a passing grade is to weaken the check, that is the moment to escalate. This is the specific failure mode that grows with model capability, and it is why the actor does not hold the verdict.

---

## 5. Running in the background

Kai's background surface is the agent loop (`agent/loop.py`) and its scheduled tasks (`agent/tasks/`). The contract for anything running there:

**Every scheduled task declares a work type and a floor.** A task that cannot name its ECO floor is not ready to run unattended.

**Every tick has one of three outcomes**, and all three are recorded:

1. Work advanced → artifacts written, evidence appended to the ECO record.
2. Nothing to do → recorded as such, with the query that returned empty.
3. Something blocked → failure record with `next_check_at`.

**The weekly `cmo_review` is the goal layer's heartbeat.** It refreshes goal progress from graded 30-day results, computes pace against deadlines, decomposes behind-pace goals into task graphs, and flags failed graphs `needs_replan`. Under ECO it gains one more job: **pay down outcome debt.** Anything SHIPPED whose outcome window has closed gets its O3 read, or a failure record explaining why the read could not happen.

```bash
python -m scripts.quality_gates.eco_gate debt      # what is SHIPPED but not CLOSED
```

**Notifications follow the verdict, not the activity.** The operator hears about SHIPPED, CLOSED, blocked, and escalations. They do not hear about every tick. A run that has been quietly failing for a week is a reporting bug, not a quiet week.

---

## 6. What a good long-horizon Kai run looks like

```text
Operator:  /kai-goal "Get us to 40 qualified demo requests a month from organic
            search by end of Q4. Budget: content only, no paid. Don't touch the
            pricing page."

Run start: objective.yaml written — floor per work item from eco-floors.yaml,
           escalate_when: spend requested, pricing/legal copy, claims about
           customer outcomes without a source.

Window 1:  Diagnose. GSC + analytics pull, topical map, gap analysis.
           → 9 work items in state.json, each with a declared floor and an O1
             baseline captured before anything is written.
           → git commit, progress.md updated.

Window 2+: Execute item by item. Each piece: draft → C2 gates → C3 review →
           E3 approval (operator) → publish → E5 public read-back → eco_gate
           verify → SHIPPED with a 30-day debt.
           A publish that 500s becomes a failure record, not a retry loop.

Weeks 4-8: cmo_review pays debt. O3 reads from GSC at each window.
           Items that cleared threshold → CLOSED, fed to what-works.md.
           Items that missed → CLOSED at O3 with the miss recorded, diagnosed
           into what-doesnt-work.md via /kai-retro.

Goal:      CLOSED when the goal metric hits 40 with the observation coming from
           GSC, not from the agent's summary of its own work.
```

The run is not finished when nine articles exist. It is finished when the number moved and something other than the writer says so.

---

Related: `docs/system/eco-completion-standard.md` · `docs/system/execution-lifecycle.md` · `docs/system/governance-and-quality.md` · `docs/system/learning-loop.md` · `harness/references/eco-marketing-floors.md`
