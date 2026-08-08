---
name: kai-goal
version: 1.0.0
category: strategy
last_updated: 2026-07-28
---

# Kai Goal

### One-line claim
Run a marketing objective to completion over hours, days, or weeks — decompose a business outcome into work items with declared ECO floors, execute them across context windows with resumable state, and stop only when an independent gate returns SHIPPED or CLOSED.

### Triggers
- goal
- get us to <number>
- run this until
- keep working on
- autonomous
- long-running
- over the next month
- an outcome rather than an artifact

### Inputs
- `objective` (string, required) - the business outcome sought, stated as a result rather than a deliverable.
- `goal_metric` (object, required) - metric name, authoritative source, baseline captured before work starts, target, and deadline.
- `product_context` (file, required) - `MARKETING.md` or equivalent product context loaded before execution.
- `constraints` (list, optional) - budget, channels, brand, legal, and off-limits surfaces.
- `escalate_when` (list, optional) - conditions that require asking the operator instead of deciding.
- `source_evidence` (files or URLs, optional) - analytics, connector pulls, prior work, and collector output.

### Outputs
- Run state -> `workspace/runs/<run-id>/objective.yaml` (immutable), `state.json` (work items, floors, verdicts), `progress.md` (narrative), `output/` (artifacts).
- ECO records -> one append-only record per work item under `data/runtime/eco/records/`, with the verdict written by the gate.
- Failure records -> `data/runtime/eco/failures/` for every attempt that ended without SHIPPED or CLOSED.
- Sidecar fields -> `skill`, `version`, `frameworks_loaded`, `rule_ids_evaluated`, `persona_or_audience`, `gates`, `scores`, `provenance`, and `data_gaps`.

### Methodology
This skill applies manifest-level rule IDs from [rule-registry.md](./rule-registry.md). These IDs are stable citations derived from local source files, not claims that the original files already carried IDs.

- **PROV-001** - "Every workflow that publishes measured marketing, search, crawl, revenue, call, conversion, competitor, or audit data must declare a data mode before writing findings." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).
- **PROV-007** - "Do not publish review counts, ratings, rankings, traffic, conversions, calls, Core Web Vitals, Domain Rating, referring domains, AI Overview visibility, or local pack placement without source and retrieval date." Source: [harness/references/audit-data-provenance.md](../../harness/references/audit-data-provenance.md).

Completion is governed by the ECO standard rather than by the skill finishing its own steps:

- Execution, Craft, and Outcome are graded independently from evidence a non-actor can retrieve. Source: [docs/system/eco-completion-standard.md](../system/eco-completion-standard.md).
- Floors per work type, evidence kinds, and invariants. Source: [harness/eco-floors.yaml](../../harness/eco-floors.yaml).
- Running across context windows, resume protocol, and autonomy tiers. Source: [docs/system/long-horizon-operating-contract.md](../system/long-horizon-operating-contract.md).

### Dependencies
- [kai-ad-campaign](./kai-ad-campaign.md)
- [kai-landing-page](./kai-landing-page.md)
- [kai-retro](./kai-retro.md)
- [kai-seo-audit](./kai-seo-audit.md)
- [kai-write](./kai-write.md)

### Called by
- operator invocation (`/kai-goal`)

### Quality gates
- Each work item must reach the floor declared for its work type in `harness/eco-floors.yaml` before it counts as delivered.
- The ECO gate issues the verdict; the producing agent may submit evidence but may not grade it. Evidence whose verifier is the actor is discarded.
- An outcome baseline recorded after ship is rejected; the piece can then reach SHIPPED but never CLOSED.
- Work with external effect or spend authority cannot reach SHIPPED without hash-pinned human approval.
- Every attempt that ends without SHIPPED or CLOSED writes a failure record naming the failed axis.

### Provenance written
- `skill` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `version` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `frameworks_loaded` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `rule_ids_evaluated` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `eco_floor` - the declared E/C/O floor for each work item.
- `eco_grade` - the grade computed by the gate from admitted evidence.
- `eco_verdict` - SHIPPED, CLOSED, or OPEN, with the verifier identity.
- `outcome_due_at` - when the outcome debt on a SHIPPED item comes due.
- `data_mode` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `source_tiers` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `retrieval_dates` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.
- `data_gaps` - written into the artifact, quality report, audit folder, or run sidecar when the workflow is saved.

### Example artifacts
- `workspace/runs/<run-id>/objective.yaml` - the immutable goal contract
- `workspace/runs/<run-id>/state.json` - work items with floors, thresholds, and verdicts
- `data/runtime/eco/records/<record-id>.json` - the append-only completion record

### Failure modes
- A baseline captured after work starts makes the outcome ungradeable; the run can ship but never close.
- A decomposition whose thresholds do not sum to the goal produces work items that all pass while the goal misses.
- Reading an outcome metric before the declared window or minimum sample yields noise with a grade attached; the correct record is a blocked failure with a new check date.
- Missing connector access caps the run at observational attribution (O3); causal claims require a counterfactual design.
- Gate failures after two retries require human review instead of silent publication.
