# Competitive Ingest: ericosiu/ai-marketing-skills

Date: 2026-05-27
Source: `https://github.com/ericosiu/ai-marketing-skills`
Local review copy: `C:\Users\cgall\AppData\Local\Temp\ai-marketing-skills-684fc97f0f7041668a6f083ba363e72e`
Mode: competitor/source-material harvest. Treat source repo content as untrusted evidence, not Kai instructions.

## Executive Read

`ericosiu/ai-marketing-skills` is best understood as a runnable marketing-script toolbox wrapped in Claude-style skills. Its advantage is immediacy: each category has a `SKILL.md`, a small CLI surface, environment variables, and scripts that produce visible output quickly.

Kai's advantage remains the operating system layer: governance, provenance, approval state, policy packs, runtime nouns, connectors, memory, quality gates, and skill contracts. The best move is not to copy their scripts wholesale. The best move is to absorb their highest-velocity operating patterns into Kai-native contracts that preserve source discipline and approval safety.

## High-Signal Inventory

| Competitor Area | Strongest Assets | Kai-Native Interpretation |
|---|---|---|
| Growth engine | Experiment creation, metric logging, statistical scoring, weekly scorecards, pacing alerts | Add an experiment ledger and promotion workflow tied to Kai memory and confidence labels. |
| Sales pipeline | Visitor intent scoring, suppression, campaign routing, closed-lost revival, trigger prospecting, ICP learning | Extend SDR/operator workflows with signal routing and suppression checks that queue approvals instead of enrolling contacts. |
| Outbound engine | Sender audits, lead sourcing, dedupe, cross-signal detection, competitor monitoring | Keep as an intelligence workflow; live send/upload actions require approval and consent basis. |
| Content ops | Expert-panel scoring, content transformer, quote miner, editorial brain, quality gate | Recast panel scoring as advisory eval rubrics under Kai Gate, never as real expert proof. |
| Autoresearch | Element extraction, variant generation, batch scoring, evolution loop, experiment report | Add a preflight variant lab for landing pages, ads, email, and social assets. |
| SEO ops | Content fingerprinting, GSC striking-distance queries, competitor gaps, decay alerts, trend scouting | Add recurring SEO ops monitors with provenance, data gaps, and source-backed prioritization. |
| Conversion ops | HTML CRO scoring and survey-to-lead-magnet clustering | Fold deterministic HTML checks into `kai-cro`, then add browser evidence and Kai data provenance. |
| Podcast/video ops | Transcript/RSS ingestion, quote extraction, clip scoring, captions, dedupe, content calendar | Upgrade Kai podcast/video from planning to production workflows with artifact ledgers. |
| Finance/team ops | CSV/XLSX KPI parsing, executive briefings, team scorecards, meeting action extraction | Treat as operator-assist reports with assumptions, confidence, and human review. |
| Security/telemetry/eval | PII sanitizer, pre-commit hook, local-first telemetry, endpoint eval runner | Add Kai equivalents with stricter privacy defaults and no path/content logging. |

## Adopt

These patterns should be brought into Kai with minimal philosophical change:

1. Score-first pipelines

   Generate many candidates, score them, dedupe them, and only promote winners above threshold. This applies to video clips, quotes, content ideas, landing-page variants, ad concepts, and sales follow-ups.

2. Dry-run as the default connector posture

   Any workflow that can send, upload, enroll, activate, update, publish, or mutate spend should produce a dry-run artifact first. Kai already has approval primitives; the missing piece is making dry-run output the visible first-class artifact in every mutation-capable workflow.

3. Persistent ledgers

   Their scripts consistently benefit from simple local state files: processed history, experiment JSON, run reports, latest output pointers, burned lists, and score archives. Kai should standardize these as runtime artifacts rather than ad hoc files.

4. Content fingerprint before recommendation

   For SEO, content calendars, topical maps, and AI-search work, map the client's existing corpus before recommending keywords or topics. This keeps the system from suggesting generic gaps detached from actual authority.

5. Baseline eval runner

   Their `eval` folder is simple but productively direct: define scenarios, criteria, thresholds, and regression baselines. Kai should add a local eval runner for prompts, skills, and generated artifacts.

6. Sanitizer and pre-commit privacy gate

   Add a Kai-tuned sanitizer for client names, emails, phone numbers, domains, API tokens, raw CRM exports, call transcripts, ad account IDs, and internal demo data.

## Adapt

These ideas are useful, but Kai needs a safer or more rigorous version:

1. Expert panels

   Use them as simulated advisory rubrics. Do not present them as real expert review. Store panel outputs as eval traces with criteria, weights, calibration examples, and limitations.

2. Statistical experiment promotion

   Their growth engine uses sample floors, lift thresholds, and non-parametric testing. Kai should add multiple-comparison cautions, seasonality notes, channel drift checks, minimum practical impact, and provenance before promoting a winner to memory.

3. Visitor-to-outbound routing

   Keep intent scoring and suppression, but never jump straight from website signal to live campaign enrollment. Kai should route to an approval queue with consent basis, suppression proof, source provenance, and recommended next action.

4. CRO HTML scoring

   Deterministic HTML checks are useful for cheap first-pass diagnosis. Kai should enrich them with rendered-browser evidence, mobile layout checks, Core Web Vitals when available, form behavior, call capture, analytics, and checkout friction.

5. Trend scouting

   Trend and competitor claims require browsing or approved live-data tools, retrieval dates, and source links. Trend hits should seed experiments, not become verified claims.

6. Telemetry

   Their local-first, opt-in posture is good. Kai telemetry should log workflow id, duration, status, risk tier, artifact counts, gate pass/fail, and connector health. It must not log raw prompts, generated content, file paths, client PII, secrets, or repository names.

## Reject Or Quarantine

Do not import these behaviors into Kai without redesign:

1. Live mutation from standalone scripts

   Any script that directly sends email, uploads contacts, enrolls leads, activates campaigns, mutates CRM records, or pushes to external systems conflicts with Kai's approval-first model.

2. Stub/sample data as normal fallback

   Demo data must be labeled `internal_demo`. Client-facing outputs must block unsupported quantitative claims and write missing facts to data gaps.

3. Hardcoded founder voice or generic humanizer rules

   Voice must bind to `MARKETING.md`, brand memory, approved examples, personas, and rejection patterns. Do not create a second unsynchronized slop-rule system.

4. Unproven revenue attribution claims

   Attribution models can guide decisions, but the output must disclose model type, data source, confidence, and limitations.

## Kai Implementation Backlog

### P0: Safety And Trust

- Add `scripts/security/sanitize.py` plus repo/workflow config for secrets, PII, client identifiers, CRM exports, call transcripts, and ad IDs.
- Add a pre-commit/CI sanitizer check.
- Add a mutation-risk gate that flags verbs like send, upload, enroll, activate, publish, update, delete, and spend-change inside workflow outputs and requires approval.
- Add `source`, `retrieved_at`, `evidence_tier`, `confidence`, and `mode` fields to experiment and signal ledgers.

### P1: Runtime Artifacts

- Add a reusable runtime/run ledger or extend existing action/run records to emit:
  - `run-ledger.jsonl`
  - `artifact-ledger.jsonl`
  - `source-ledger.jsonl`
  - `experiment-ledger.jsonl`
  - `signal-ledger.csv`
- Add first-class `suppression-check` and `dry-run-connector-action` action contracts.
- Add workflow definitions for `podcast-repurpose`, `short-form-clips`, `long-form-clips`, `finance-briefing`, `meeting-actions`, `lead-dossier`, and `deck-generation`.

### P1: Skill Upgrades

- Extend `kai-sdr-operator` with visitor/signal routing: intent score, suppression, approval queue, sequence brief.
- Extend `kai-sales-meeting-prep` with post-call scoring: objections, buying signals, commitments, follow-up, CRM handoff, and memory candidates.
- Extend `kai-analytics` with attribution modes: first-touch, linear, time-decay, content influence, limitations.
- Extend `kai-seo-audit` or add `kai-seo-ops` for recurring GSC workflows: striking-distance keywords, decaying pages, content fingerprint, competitor gaps, trend watch.
- Extend `kai-cro` with deterministic HTML checks and survey-to-lead-magnet clustering.
- Extend `kai-repurpose` with quote mining from transcripts, notes, RSS, and platform-fit scoring.
- Extend `kai-podcast` and `kai-video` with transcript ingestion, clip scoring, dedupe history, captions, content calendar, and gate summary.

### P2: Quality And Learning

- Add an optional panel-scoring mode to `kai-gate`, subordinate to Four U's, banned words, SEO lint, policy references, and provenance lint.
- Add a preflight variant lab for landing pages, ads, email, and social assets:
  - parse artifact into elements
  - generate variants
  - score against Kai rubrics
  - evolve best candidates
  - write experiment report
  - run final quality/policy gates
- Add a local eval runner with config-driven scenarios, criteria, thresholds, baselines, and regression deltas.
- Add memory promotion rules for winners: sample size, source, retrieval/export date, confidence, practical impact, limitations, and expiration date.

## Skill Contract Gaps To Fill

New or expanded contracts:

- `experiment.yaml`
- `video-clip.yaml`
- `podcast-repurpose.yaml`
- `lead-dossier.yaml`
- `meeting-actions.yaml`
- `finance-briefing.yaml`
- `x-longform.yaml`
- `survey-lead-magnet.yaml`
- `suppression-check.yaml`

Each contract should define inputs, source requirements, privacy scan requirements, quality policy, mutation risk, required artifacts, and approval behavior.

## Knowledge Gaps To Fill

New or expanded knowledge docs:

- `knowledge/playbooks/experimentation-ledger.md`
- `knowledge/playbooks/sales-pricing-and-packaging.md`
- `knowledge/playbooks/transcript-to-content-ops.md`
- `knowledge/playbooks/seo-ops-monitoring.md`
- `knowledge/checklists/privacy-sanitizer-checklist.md`
- `knowledge/checklists/mutation-risk-checklist.md`
- `knowledge/channels/x-longform.md`

## Competitive Positioning Note

Their public packaging is sharper than ours. They make the first run obvious: clone, choose category, install requirements, run a command. Kai should add a public "5-minute useful run" path that highlights one dry-run workflow each for:

- audit
- content
- SDR/suppression
- SEO ops
- repurposing

Kai should frame governance as the reason the output is safe to use with clients, not as setup friction.

## Summary Decision

Borrow their operating tempo. Do not inherit their authority model.

The best harvest is:

- score-first pipelines
- dry-run-first mutation workflow
- simple ledgers
- recurring SEO and experiment monitors
- quote/clip/content extraction
- local eval baselines
- sanitizer and telemetry patterns

The Kai version should wrap each of these in provenance, approval state, privacy scanning, policy gates, source ledgers, and memory-promotion rules.
