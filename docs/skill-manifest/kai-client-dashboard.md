---
name: kai-client-dashboard
version: 1.0.0
category: production
last_updated: 2026-07-27
---

# Kai Client Dashboard

### One-line claim
Build a white-labeled, client-facing intelligence dashboard — brand auto-extraction, a three-tier build, an onboarding feature wizard, a 10-page inventory, and the retention plays that make it sticky.

### Triggers
- client dashboard
- client intelligence dashboard
- white label dashboard
- client portal
- branded dashboard for my client
- agency dashboard
- build my client a dashboard
- give the client a live view instead of a report

### Inputs
- `client_name` (string, required) - business name as it should appear on the dashboard.
- `client_url` (string, required) - the client's website, used for brand auto-extraction in Phase 0.
- `tier` (string, optional) - `basic`, `standard`, or `advanced`. Defaults to `standard`.
- `connected_sources` (object, optional) - GA4 property ID, GSC site URL, CRM/lifecycle provider and credentials, ad platform access, competitor list.
- `feature_selections` (object, optional) - yes/no answers to the Phase 2 wizard (retargeting, visitor ID, competitor benchmarks, brand assets, press releases, video library, AI/LLM rankings, social, deliverables, roadmap, multi-location, agent registry).
- `public_access_decision` (string, optional) - `public`, `split_access`, or `obscured_gated`. Required before any page ships live.

### Outputs
- Artifact -> `<dashboard-project>/` - the client-facing dashboard itself (static shell via `scripts/build_dashboard.py` or a full app in the operator's own stack).
- Artifact -> Brand Assets page - extracted or supplied logo, colors, fonts.
- Artifact -> Deliverables page - active/in-progress/available service checklist.
- Artifact -> Agent Registry page - real scheduled automation for this client.
- Data contract -> handed off from/to `/kai-data-dashboard` once sources are connected.
- Quality report -> provenance coverage, public-access decision, data gaps, pitfall check.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md).

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-003** - "Use `onboarding_connected` only after the client has signed and granted access to connected sources such as GSC, GA4, GBP, ad accounts, CRM, call tracking, analytics exports, or owner data." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-008** - "Missing credentials or unavailable sources must produce `_data-gaps.md` entries. Do not replace missing sources with estimates or placeholder metrics." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **AEO-005** - "Design passages to be retrievable: use self-contained section-answer pairs, descriptive headings, tables, definitions, examples, and visible HTML." Source: [knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md](../../knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md).
- **TASTE-005** - "For Visual Cohesion, require component grammar, semantic structure before styling, protected affordances, consistent tokens, and generated output that fits the surrounding UI." Source: [harness/skills/kai-taste/SKILL.md](../../harness/skills/kai-taste/SKILL.md).

### Dependencies
- [kai-data-dashboard](./kai-data-dashboard.md)
- [kai-brand-pulse](./kai-brand-pulse.md)
- [kai-competitors](./kai-competitors.md)
- [kai-surround-sound](./kai-surround-sound.md)
- [kai-social](./kai-social.md)
- [kai-gate](./kai-gate.md)

### Called by
- No committed caller found. Standalone onboarding-triggered build.

### Quality gates
- Every metric has a source and a sync/retrieval timestamp, or is explicitly `internal_demo`-labeled.
- No score or dollar figure (Health Grade, ROI/Value Delivered) ships without a stated formula and a source per input.
- The public-access decision is explicit and covers every page, not just the Overview.
- Deliverables and Agent Registry pages reflect real, current work.
- Any SMS or prerecorded-voice engagement automation has a logged consent and opt-out path (`harness/skills/kai-sdr-operator/references/compliance-matrix.md`).
- `python scripts/quality_gates/audit_provenance_lint.py <folder> --audit-dir` passes.

### Provenance written
- `skill`
- `version`
- `client_id`
- `tier`
- `feature_selections`
- `data_mode`
- `public_access_decision`
- `data_gaps`
- `quality_gate_scores`

### Example artifacts
- No committed example artifact found.

### Failure modes
- No bundled reference client codebase to copy from — the full-app path requires the operator's own stack; only the static fast path (`scripts/build_dashboard.py`) works out of the box.
- Credentials for tools this harness has no connector for (visitor identification, some retargeting platforms) become data gaps, not estimates.
- A public-access decision made once at launch can go stale as new PII-bearing pages (Leads, Sales Intelligence) are added later.
- Retention plays (Health Grade, ROI summary) are provenance-gated and may ship without a number if the underlying formula or source is missing.

### Competitive claim
This skill differs from generic client-dashboard playbooks by refusing to fabricate the two things they most often fake: a finished-looking reference codebase that does not exist in this repo, and filler metrics for panels with no real source behind them.
