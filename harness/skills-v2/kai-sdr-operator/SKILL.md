---
name: kai-sdr-operator
description: >
  Build a plug-in-ready SDR operator package for sales development and outbound pipeline work:
  ICP definition, compliant lead-source plan, enrichment/research workflow, account scoring,
  outbound assets, CRM handoff, reply triage, meeting prep, approval gates, and loop memory. Use when "SDR",
  "sales development", "outbound SDR", "operator room", "lead gen pipeline",
  "prospecting pipeline", "ICP targeting", "Apify", "RapidAPI", "Clay", "Apollo",
  "agentic SDR workflow", "sales operating loop", "sales dashboard handoff", or any request
  to package outbound sales workflows that can later connect to data tools, CRMs, or operator surfaces.
---

# kai-sdr-operator — SDR Package Builder

> **Kai root note:** `knowledge/`, `harness/`, and `scripts/` paths in this skill live in the Kai install, not the user's project. Resolve them against the first ancestor directory of this SKILL.md that contains a `knowledge/` folder (the Kai plugin root, `~/.claude/kai`, or the kai-cmo-harness repo). `MARKETING.md`, `memory/`, and any output files live in the current project. If a referenced `scripts/` command is not available in this install, say so, skip it, and continue with the file-based guidance — never fabricate its output.

## Objective

A reusable SDR operating package on disk that a human or a future agent can pick up and run: lawful lead sources with their terms recorded, an ICP scorecard, an account scoring model, enrichment and research workflows, connector contracts, an approval queue, outreach handoff briefs, reply and meeting loops, CRM handoff records, and a memory ledger that learns from outcomes. Every worker's input and output is explicit enough that a sub-agent, MCP connector, or dashboard can call it.

This skill is the orchestrator, not the copywriter. `/kai-cold-outreach` writes the email touches once lead-source, suppression, sender, and claim-evidence gates are clear. `/kai-sdr-reply-triage` handles replies. `/kai-sales-meeting-prep` handles booked calls. `/kai-data-dashboard` runs only when the user explicitly asks for a dashboard surface.

## Done when

Work type `strategy-plan` — floor **E3/C3/O1** (`harness/eco-floors.yaml`). The package is a plan; nothing in it fires a live action on its own.

- **E3** — a named human approved the exact package, including `_lead-source-plan.md` and `approval-plan.md`. Approval of the package is not approval of any run it describes.
- **C3** — `banned_word_check` passes on every customer-facing markdown file; `four_us_score` clears **10/16** on outreach copy and **12/16** on strategic package docs (`sequence-brief.md`, `_brief.md`); `sdr-package.yaml`, `cold-email.yaml`, `sdr-reply-triage.yaml`, and `sales-meeting-prep.yaml` checks are satisfied; and a named non-producer read the package end to end.
- **O1** — the package names the first live action it will spawn, its metric, baseline, threshold, and owner. A package that never reaches a test cohort is not CLOSED.

Every quantitative or client-facing claim resolves to a source with a retrieval date, or sits in `_data-gaps.md`. No live action was taken without recorded approval.

## Constraints

- **Approval before anything live.** Billable API or connector runs, imports, exports, enrichment credit spend, email sends, DMs, calls, SMS, calendar actions, and CRM mutations all require explicit human approval first. A signal alone never triggers a live action.
- **Adapters are not permission slips.** Apify, RapidAPI, Clay, Apollo, and CRM exports are tools; check current vendor docs and account terms before running one. Never bypass logins, CAPTCHAs, robots restrictions, paywalls, platform rate limits, or social-network terms.
- **Prohibited sources:** personal email scrapes, consumer lists, sensitive personal attributes, bought accounts.
- **`_lead-source-plan.md` precedes any list building** and must carry: approved source inventory with owner, access method, terms notes, and data fields; disallowed sources and why; suppression source and opt-out sync path; consent or lawful-interest basis by region; data minimization (only fields needed for fit, relevance, routing, compliance); connector notes.
- **Suppression runs before scoring promotion.** Suppression covers prior opt-out, existing-customer conflict, active opportunity owner, disallowed source, sensitive-data risk, bad domain, region restriction, missing lawful basis. Only `suppression_status=clear` rows may reach `approved_for_copy`; `needs_review`, `conflict`, and `blocked` rows go to the approval queue with row ID, requested live action, reason, evidence, approver, decision, timestamp, and next state.
- **Block outright:** accounts with missing source, missing suppression check, sensitive personal data, prior opt-out, disallowed source, or an unsupported claim dependency.
- **No invented numbers.** Reply rates, meeting rates, benchmarks, TAM, revenue, and conversion figures come from real data or user-provided targets, or they are data gaps.
- **No raw rows to the copy step.** A row reaches `/kai-cold-outreach` only with source, suppression, relevance, and sender fields filled.
- **Specialists inherit the same limits.** Neither `/kai-sdr-reply-triage` nor `/kai-sales-meeting-prep` may mutate live CRM, sequencer, calendar, SMS, phone, or email systems without approval; both write back into this package folder and update the memory ledger.
- **`local_phone_led` mode triggers KaiCalls fit review** — disclose the ownership relationship, compare alternatives, and do not lead with it when phone demand is low or the workflow is self-serve by design.

**Account scoring model (0–100):**

| Component | Points | Basis |
|---|---|---|
| Fit | 40 | Industry, size, geography, budget, use-case match |
| Timing | 20 | Hiring, funding, expansion, new regulation, new location, tech migration, active demand |
| Pain evidence | 20 | Public proof, owned data, CRM notes, reviews, job posts, pages, user research |
| Reachability | 10 | Valid business contact path, routing clarity |
| Compliance confidence | 10 | Lawful source, suppression clear, no sensitive-data concern |

**Lead ledger columns** (`lead-ledger-template.csv`, minimum):

```text
account_id,company,website,industry,geo,company_size,source_name,source_url,source_retrieved_at,fit_score,intent_signal,trigger_event,problem_evidence,contact_name,contact_role,contact_channel,personalization_note,personalization_source,confidence,suppression_status,consent_basis,next_action,owner,status
```

`confidence`: `high`, `medium`, `hypothesis`, `blocked`. `status`: `sourced`, `enriched`, `approved_for_copy`, `queued`, `sent`, `replied`, `meeting_booked`, `disqualified`, `suppressed`, `blocked`.

## Context

Seven things must be known before the package can be built — read them from `MARKETING.md` first and ask only for what is missing: the offer and desired conversion (meeting, demo, audit, quote, trial, call); ICP filters (industry, geography, size, tech stack, budget, trigger events); available lead sources; outreach channels; sender stack (domain, ESP, CRM, sequencer, calendar, suppression list); volume target and human review capacity; and whether the category is regulated or sensitive (healthcare, finance, legal, minors, employment, housing, credit, political, consumer data). If `MARKETING.md` does not exist, run `/kai-start` or infer a temporary brief from trusted project files and mark unknowns `[TODO]`.

| Need | Load |
|---|---|
| Package schema, required files, gate thresholds | `harness/skill-contracts/sdr-package.yaml` |
| Outreach copy contract | `harness/skill-contracts/cold-email.yaml` |
| Opt-out, sender identity, consent, list law | `harness/references/cold-email-rules.md` |
| Demand mechanics and channel fit | `knowledge/playbooks/demand-generation.md` |
| Named accounts or enterprise targets | `knowledge/playbooks/account-based-marketing.md` |
| Deliverability and sender setup | `knowledge/channels/email-lifecycle.md` |
| Row, account, contact, and event schema | `references/sdr-data-model.md` |
| Connector wiring and action contracts | `references/connector-recipes.md` + `references/connector-action-contracts.md` |
| Vertical-specific ICP and trigger packs | `references/vertical-packs.md` |
| What needs human sign-off and when | `references/human-approval-gates.md` |
| Loop mechanics, states, transitions | `references/operating-loop.md` + `references/loop-events-and-transitions.md` |
| Region and category compliance matrix | `references/compliance-matrix.md` |
| Run ledger and observability fields | `references/observability-and-run-ledger.md` |
| Package evaluation criteria | `references/evaluation-harness.md` |
| Outside research on agentic SDR loops | `references/external-loop-research.md` |

(`references/` paths are relative to this skill directory in the Kai install.)

**Package modes** — pick one from the request or product context; default `pipeline_prototype` for a showcase or proof-of-work asset:

| Mode | Best fit | Output bias |
|---|---|---|
| `pipeline_prototype` | Interview demo, founder experiment, first outbound system | Small sample list, visible workflow, dashboard-ready schema |
| `b2b_sdr_engine` | SaaS, agency, service firm, consulting offer | ICP scorecard, lead sources, email/LinkedIn/call handoff |
| `abm_sdr_engine` | Named accounts or enterprise targets | Account dossiers, buying committee, 1:1 research tasks |
| `local_phone_led` | Local services, legal, home services, clinics | Call capture, speed-to-lead, KaiCalls fit review |
| `recruiting_sdr_engine` | Staffing, recruiting, talent marketplace | Candidate/client split, employment-policy caution, role-fit evidence |
| `partner_sdr_engine` | Co-marketing, channels, affiliates, agencies | Partner-fit matrix, mutual value, low-volume relationship motion |
| `sdr_migration_audit` | Existing SDR team moving work into Claude/Kai loops | Workflow map, automation readiness, cost model, approval plan |

**Workers in the loop** — each is a callable unit with explicit inputs and outputs: Source Scout, ICP Scorer, Contact Mapper, Personalization Researcher, Outreach Producer (hands approved rows to `/kai-cold-outreach`), Test Cohort Runner, Compliance Reviewer, Reply Router (`/kai-sdr-reply-triage`), Meeting Prepper (`/kai-sales-meeting-prep`), CRM Handoff Writer, Daily Briefing Writer, Outcome Learner.

**Output** goes to `workspace/sdr-operator/<package-slug>/`. Same path as v1. Required files:

```text
_brief.md  _lead-source-plan.md  _icp-scorecard.md  _account-scoring-model.md
_research-workflows.md  connector-plan.md  connector-action-contracts.md
approval-plan.md  approval-queue-template.csv  loop-state-model.md
loop-events-and-transitions.md  compliance-matrix.md  run-ledger-template.json
memory-ledger.md  daily-briefing-template.md  test-cohort-plan.md
lead-ledger-template.csv  account-dossier-template.md  sequence-brief.md
reply-triage.md  meeting-prep.md  follow-up-workflows.md  crm-handoff.md
data-handoff.md  sales-role-handoff.md  sdr-package.json
_data-sources.md  _data-gaps.md  _quality-report.md  _evaluation-report.md
```

`loop-state-model.md`, `memory-ledger.md`, and `sdr-package.json` carry what makes the motion repeatable: package mode, retrieval dates, data mode, counts by ledger status, source inventory and gaps, account/contact state transitions, approval state for every live action, reply categories and objections and referrals and booked meetings, source/trigger/message/meeting quality memory, quality gates, blockers, next actions.

The closing summary names the package path, the mode, what was produced, blocked sources and missing data, and which of `/kai-cold-outreach`, `/kai-sdr-reply-triage`, or `/kai-sales-meeting-prep` runs next.

## Escalate when

- The category is regulated or sensitive — healthcare, finance, legal, minors, employment, housing, credit, political, or consumer data.
- A lead source's terms are unclear, or the only available source is disallowed.
- Lawful basis or consent for a region cannot be established.
- The user asks to run a connector, spend enrichment credits, import or export contacts, send, call, or mutate CRM — that is an approval request, not a decision.
- Sender stack, suppression list, or domain reputation is unknown and volume targets are non-trivial.
- The offer depends on a claim with no evidence behind it.
- Requested volume exceeds the human review capacity the user stated.
