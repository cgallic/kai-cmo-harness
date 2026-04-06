# Build Overview

**Date:** 2026-04-02  
**Purpose:** Summarize the major work completed in this build cycle and show how the repo moved toward a marketing operating system.

---

## Summary

This build cycle moved the repo from a loose harness with strong ingredients into a more explicit marketing operating-system shape.

The major progress areas were:

1. establish a canonical runtime layer
2. unify local and remote execution around run / artifact / state contracts
3. add approval and action-control infrastructure
4. add connected-marketing-ops planning
5. shift from runtime-only thinking toward application-first flows
6. build the first real application slice for `local-service`
7. calibrate that slice against a real client example: Andon Window Cleaning

The system is not complete yet, but it now has a much clearer product shape and a real application path from business profile to audit to proposals to action handoff.

---

## 1. Runtime Foundation

The repo now has an explicit runtime layer under `kai/runtime/`.

### Added

- `kai/runtime/models.py`
- `kai/runtime/loader.py`
- `kai/runtime/store.py`
- `kai/runtime/modules/*.yaml`

### What this introduced

- `KaiWorkspaceProfile`
- `KaiBrandProfile`
- `KaiModuleManifest`
- `KaiRunRequest`
- runtime-backed brand and module loading
- canonical run persistence
- canonical artifact persistence
- derived runtime state snapshots

### Why it mattered

This established a shared contract for local and remote execution instead of letting every surface invent its own state model.

---

## 2. Runtime-Backed Engine and Gateway

The existing content engine and gateway were refactored to use the runtime layer more directly.

### Key updates

- `scripts/content/engine.py`
- `scripts/content/_writer.py`
- `scripts/content/content_log.py`
- `gateway/config.py`
- `gateway/main.py`
- `gateway/jobs.py`
- `gateway/models.py`
- `gateway/routers/generate.py`
- `gateway/routers/jobs.py`
- `gateway/routers/runtime.py`

### What changed

- content generation now records canonical runtime runs and artifacts
- gateway config can resolve brands from runtime workspace data
- remote jobs carry canonical run metadata
- runtime endpoints expose workspace, brands, modules, runs, artifacts, lineage, approvals, and observability state
- job views now read runtime-owned meaning more directly instead of only SQLite queue state

### Result

The repo moved closer to:

- one run model
- one artifact model
- one state model

rather than separate local, remote, and queue-only interpretations.

---

## 3. Approval, Action, and Policy Control

The control plane for safe execution became much more real.

### Added or expanded

- `kai/runtime/actions.py`
- `kai/runtime/integrations.py`
- `kai/runtime/policy.py`
- `kai/runtime/memory.py`
- approval mutations in `kai/runtime/store.py`
- `gateway/routers/actions.py`
- approval mutation routes in `gateway/routers/runtime.py`

### What this added

- action proposal persistence
- action lifecycle management
- approval / rejection / hold flows
- execution-state tracking
- immutable action log
- risk tiering and policy gating
- integration registry and kill switches
- memory writeback skeleton

### Why it mattered

This is the substrate required for connected background marketing operations to work safely.

---

## 4. Product and Architecture Reframing

The repo documentation was rewritten to stop presenting the project as a generic CMO harness.

### Updated

- `README.md`
- `CLAUDE.md`
- `docs/ARCHITECTURE.md`
- `harness/ARCHITECTURE.md`
- `config.yaml`
- `config.example.yaml`

### Product direction now reflected in the repo

- Kai as a marketing-native Claude Code-style clone
- dual surface: local + remote
- marketing as the core product, not an example use case
- runtime primitives in service of a marketing operating system

---

## 5. Planning and Product Specs

Several planning docs were added to keep the build aligned and prevent drift.

### Added

- `docs/superpowers/specs/2026-04-02-phase-2a-runtime-approval-plan.md`
- `docs/superpowers/specs/2026-04-02-connected-marketing-ops-plan.md`
- `docs/superpowers/specs/2026-04-02-local-service-subagent-orchestration-plan.md`
- `docs/superpowers/specs/2026-04-02-complete-system-task-map.md`

### What these docs do

- define the next runtime-hardening step
- define the connected-ops application direction
- define subagent work split for the first application slice
- define the complete-system backlog needed to support any business across the major channels

### Why it mattered

This made the roadmap explicit:

- runtime hardening is support work
- application value is the real product center
- the system must eventually cover website, social, paid, lifecycle, analytics, approvals, creative, automation, and learning

---

## 6. First Real Application Slice

The repo now has a first application flow for `local-service`.

### Added

- `kai/runtime/business_profile.py`
- `kai/runtime/audit.py`
- `kai/runtime/application_flow.py`

### What this introduced

#### Business understanding

`BusinessProfile` and its submodels:

- identity
- offers
- geography
- personas
- trust
- goals
- channels
- constraints

#### Diagnosis

`AuditFinding`, `AuditResult`, category scorecards, and the first `local-service` audit engine.

#### Application flow

- `BusinessProfile -> audit input`
- `audit input -> AuditResult`
- `AuditResult -> ProposedAction`
- `ProposedAction -> ReviewBundle`
- optional persistence into `ActionStore`

### Why it mattered

This was the first real move from:

- "the runtime can do things"

to:

- "the product can understand a business, diagnose it, and propose real actions"

---

## 7. Subagent Coordination

The build included explicit subagent coordination and separated ownership.

### Added

- `workspace/agents/maxwell-agent.md`
- `workspace/agents/heisenberg-agent.md`

### Work split used

- Maxwell: business-profile and application-model layer
- Heisenberg: audit and diagnosis layer
- orchestrator: application integration, proposal layer, review bundle, end-to-end flow

### Why it mattered

This kept the work application-first and prevented everything from collapsing back into platform-only changes.

---

## 8. Andon Window Cleaning Calibration

A real onboarding transcript was turned into a first-class calibration asset.

### Added

- `ANDON_WINDOW_CLEANING_FIXTURE` and `load_andon_window_cleaning_fixture()` in `kai/runtime/business_profile.py`
- `docs/superpowers/specs/2026-04-02-andon-window-cleaning-review-bundle.md`

### What this did

- preserved the real onboarding facts
- preserved unknowns instead of inventing answers
- generated a real `local-service` review flow against a real small business
- produced a typed 30-day action plan tied to the action system

### Why it mattered

This gave the system a concrete early-stage local-service benchmark:

- new business
- low budget
- verified GBP
- no website
- no reviews
- no systems
- clear need for compounding small actions

That is exactly the type of business the system should eventually help well.

---

## 9. Tests and Validation

The build added and expanded focused tests.

### Test coverage added or expanded

- `tests/test_runtime_loader.py`
- `tests/test_actions_integrations.py`
- `tests/test_policy.py`
- `tests/test_business_profile.py`
- `tests/test_audit.py`
- `tests/test_application_flow.py`

### Validation performed during the build

- runtime loader and persistence tests
- action and integration tests
- policy tests
- business profile tests
- audit tests
- application flow tests
- repeated `py_compile` checks on touched Python modules

### Why it mattered

The repo now has real regression coverage for:

- runtime state
- action lifecycle
- policy gating
- business profile behavior
- audit behavior
- application flow behavior

---

## 10. Current State

The repo now has:

- a real runtime layer
- a real action / approval / policy layer
- a first connected-ops design direction
- a first application flow
- a real local-service client calibration example

But it does **not** yet have the full operator product loop exposed as a single stable surface.

### What still remains

- expose the application flow through skills and/or API routes
- connect review bundles directly to operator approval surfaces
- push selected approved actions through real execution paths
- add real watcher loops that emit proposals automatically
- expand the system beyond one archetype and one client calibration case
- deepen creative and asset generation so proposals can become execution-ready campaigns

---

## Bottom Line

The repo is no longer just:

- a content engine
- a gateway
- a knowledge base
- a few scripts with marketing logic

It now has the beginnings of a true marketing operating system:

- business understanding
- diagnosis
- proposal generation
- action control
- approval logic
- memory hooks
- connected-ops direction

The next work is to expose these capabilities as a true operator-facing system and expand the execution loop across real channels.
