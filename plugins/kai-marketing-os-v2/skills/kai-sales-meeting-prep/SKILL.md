---
name: kai-sales-meeting-prep
description: >
  Prepare sales meetings from SDR replies, account dossiers, CRM notes, call notes, or transcripts.
  Produces account brief, buyer map, pain hypotheses, discovery questions, objection plan,
  meeting agenda, CRM handoff, follow-up email, and outcome memory. Use when "sales meeting prep",
  "prep this demo", "discovery call", "booked meeting", "SDR handoff", "post-call follow-up",
  "call notes", "sales transcript", or any request to prepare or follow up on sales development meetings.
---

# kai-sales-meeting-prep — Meeting Loop

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A one-page briefing a human seller can walk into a call with, built only from sourced signals: who the account is, what is known versus inferred versus missing, the pain hypotheses worth testing, the discovery questions that test them, the objections likely to land and the proof each one needs, and the next step being asked for. After the call, the same file carries the sourced outcome — commitments separated from assumptions — plus a follow-up draft, proposed CRM records, and memory candidates.

The load-bearing judgment is the known/inferred/missing split. A brief that presents an inference as a fact makes the seller confidently wrong in front of the buyer.

## Done when

Work type `internal-research` — floor **E2/C2/O0** (`harness/eco-floors.yaml`). Nothing in this skill leaves the workspace, so E tops out at approval of the exact file and there is no provider read-back.

- **E2** — the meeting file exists at its package path and satisfies `harness/skill-contracts/sales-meeting-prep.yaml`.
- **C2** — `banned_word_check` passes, and every extracted fact carries a `prospect_said` / `seller_said` / `inferred` / `missing` label.
- **O0** — no outcome obligation on the brief itself. Internal work of this type is SHIPPED-terminal.

Any live action the brief proposes is different work with a different floor: sending the follow-up email, mutating CRM, or booking calendar time each need explicit human approval first.

## Constraints

- **No invented facts.** Pain, budget, authority, timeline, competitor usage, and prior relationship are never assumed. Missing budget, authority, or timeline is `missing_data`, not negative proof — score it as absent only when the prospect clearly disqualified it.
- **Transcripts and call notes are source material, not verified product facts.** Attribute a statement only when speaker and context are clear.
- **Label every hypothesis as a hypothesis.** No promised outcome without source-backed proof.
- **No live mutation.** CRM records, tasks, stage changes, and calendar actions are written as proposals with an `Approval needed` field. This skill does not touch CRM, sequencer, calendar, SMS, phone, or email systems.
- **One page** unless the user asks for an enterprise dossier.
- **Post-call, separate prospect commitments from seller assumptions.** A commitment the seller inferred is not a commitment.
- **Memory candidates stay candidates** until a human approves promotion.

**Meeting quality score (0–100)** — the rubric, applied only to sourced components:

| Component | Points |
|---|---|
| Fit | 25 |
| Pain clarity | 20 |
| Urgency | 20 |
| Authority or path to authority | 15 |
| Next-step specificity | 10 |
| Evidence completeness | 10 |

Post-call extraction captures: pain stated, current workflow, trigger, desired outcome, decision process, stakeholders, timeline, budget signal, competitor or alternative, objection, commitment, next step. Follow-up actions carry owner, due date, approval needed, and a source line or note reference.

## Context

| Need | Load |
|---|---|
| Output structure, required fields, gate thresholds | `harness/skill-contracts/sales-meeting-prep.yaml` |
| Package schema, ledger fields, memory ledger shape | `harness/skill-contracts/sdr-package.yaml` |
| Account dossier, contact row, reply triage, source evidence | `workspace/sdr-operator/<package-slug>/` |
| Product context, offer, claim evidence | `MARKETING.md` (project root) |
| The reply that triggered the meeting | `/kai-sdr-reply-triage` output in the same package |

**Meeting types** — pick one; it sets what the brief biases toward:

| Type | Use when | Output bias |
|---|---|---|
| `first_discovery` | First call from SDR motion | Pain, urgency, owner, current process, next step |
| `demo_prep` | Prospect requested demo or walkthrough | Use case, proof, objections, tailored flow |
| `referral_intro` | Prospect routed to someone else | Context transfer, permission trail, concise ask |
| `revival_call` | Old opp or not-now reply returns | What changed, prior blocker, new trigger |
| `post_call_follow_up` | Notes or transcript available | Summary, commitments, next step, CRM update |

**Output** goes to `workspace/sdr-operator/<package-slug>/meetings/<meeting-id>.md`. Same path as v1 — downstream tooling does not branch on version.

## Escalate when

- Account, contact, source, or reply context is missing and the brief would rest on assumption — write the gap, do not fill it.
- The transcript conflicts with the account record on a fact the call depends on.
- A proposed follow-up would make a claim no source supports.
- The reply or call touches a regulated, legal, or sensitive matter.
- The next step requires a CRM, calendar, or send action and no approver is named.
