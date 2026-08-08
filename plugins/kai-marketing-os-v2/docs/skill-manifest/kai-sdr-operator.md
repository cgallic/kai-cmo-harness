---
name: kai-sdr-operator
version: 1.0.0
category: lifecycle
last_updated: 2026-05-27
---

# Kai SDR Operator

### One-line claim
Build a plug-in-ready SDR operator package for outbound sales development: ICP definition, compliant lead-source plan, enrichment and research workflow, account scoring, outbound assets, CRM handoff, reply triage, meeting prep, approval gates, and learning memory.

### Triggers
- SDR
- sales development
- outbound SDR
- operator room
- lead gen pipeline
- prospecting pipeline
- ICP targeting
- Apify or RapidAPI prospecting
- agentic SDR workflow
- sales dashboard handoff
- sales operating loop

### Inputs
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `package_mode` (string, optional) - `pipeline_prototype`, `b2b_sdr_engine`, `abm_sdr_engine`, or `local_phone_led`.
- `offer` (string, required) - meeting, demo, audit, quote, trial, call, or other conversion event.
- `icp_filters` (object, required) - industry, geography, company size, budget, tech stack, trigger events, and disqualifiers.
- `lead_sources` (array, required) - approved CRM exports, vendor tools, public directories, owned data, or user-provided files.
- `sender_identity` (object, required) - sender, company, reply path, domain, and physical address when email is used.
- `suppression_list_id` (string, required) - opt-out, bounced, do-not-contact, and suppression source.
- `source_evidence` (files or URLs, optional) - proof points, public pages, CRM notes, exports, screenshots, or connector docs.

### Outputs
- Artifact -> `workspace/sdr-operator/<package-slug>/` with package brief, lead-source plan, ICP scorecard, scoring model, research workflows, connector plan, approval plan, loop state model, memory ledger, ledger template, sequence brief, CRM handoff, reply triage, meeting prep, data handoff, `sdr-package.json`, data sources, data gaps, evaluation report, and quality report.
- Quality report -> pass/fail status for SDR package checks, cold email readiness, source gaps, blockers, and approval status.
- Sidecar fields -> `skill`, `version`, `package_mode`, `source_files_loaded`, `lead_sources`, `source_tiers`, `data_gaps`, `approval_status`, `quality_gate_scores`, and `dashboard_handoff_id`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md).

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **POL-002** - "All advertising claims must be truthful, non-misleading, and evidence-based before the ad runs." Source: [harness/references/advertising-compliance.md](../../harness/references/advertising-compliance.md).
- **POL-006** - "No paid-media write action should auto-execute. Human approval is required for creating, publishing, pausing, activating, bid changes, budget changes, targeting changes, asset uploads, and keyword mutations." Source: [harness/references/ad-write-guardrails.md](../../harness/references/ad-write-guardrails.md).
- **VG-007** - "Format-specific quality gates from the relevant skill contract must be applied after Four U's, banned-word, AI-slop, and voice-pattern checks." Source: [harness/skills/kai-write/SKILL.md](../../harness/skills/kai-write/SKILL.md).
- **VG-008** - "When a piece fails quality gates, fix the specific issues and re-score. Stop after two retry cycles and surface remaining failures." Source: [harness/skills/kai-write/SKILL.md](../../harness/skills/kai-write/SKILL.md).

### Dependencies
- [kai-cold-outreach](./kai-cold-outreach.md)
- [kai-abm](./kai-abm.md)
- [kai-sdr-reply-triage](./kai-sdr-reply-triage.md)
- [kai-sales-meeting-prep](./kai-sales-meeting-prep.md)
- [kai-gate](./kai-gate.md)

### Called by
- [kai-growth-plan](./kai-growth-plan.md)
- [kai-abm](./kai-abm.md)

### Quality gates
- `harness/skill-contracts/sdr-package.yaml` checks pass or blockers are listed.
- Lead sources are named, approved, and separated from blocked sources.
- Suppression, sender identity, claim evidence, and consent or lawful-interest notes are present.
- Connector plan, approval plan, loop state model, and memory ledger are present.
- Four U's score meets threshold: 12/16 for strategic package docs and 10/16 for outreach assets.
- Banned-word, AI-slop, and voice-pattern checks pass with zero hard-blocking hits.
- No live connector, CRM, sequencer, email, DM, call, SMS, or paid action runs without approval.

### Provenance written
- `skill`
- `version`
- `package_mode`
- `source_files_loaded`
- `lead_sources`
- `source_tiers`
- `retrieval_dates`
- `data_gaps`
- `approval_status`
- `quality_gate_scores`
- `loop_state_id`
- `memory_ledger_id`
- `reply_triage_id`
- `meeting_prep_id`

### Example artifacts
- No committed example artifact found.

### Failure modes
- Missing product context causes the package to infer ICP or offer details too broadly.
- Unclear connector terms or source rights block live list building.
- Missing suppression list blocks outreach approval.
- Unsupported quantitative claims are removed or held for review.
- Human approval is required before any live system mutation.

### Competitive claim
This skill differs from generic SDR prompting by treating outbound as an operating loop: source policy, fit scoring, suppression, proof, copy, approval, reply routing, meeting prep, CRM handoff, and memory are all defined before live outreach begins.
