# Phase 2A — Runtime and Approval Canonicalization

**Date:** 2026-04-02  
**Status:** Active plan  
**Goal:** Keep Kai aligned with the original product direction while hardening the next implementation step.

---

## Original Goal

Kai should become a **marketing-native Claude Code-style operating system**, not:

- a generic agent harness
- a pile of marketing scripts with a thin wrapper
- a generic Claude clone with marketing as an example use case

The product target remains:

- a productized Claude Code-style clone
- with marketing as the native runtime domain
- with shared local and remote execution
- with official primitive-style concepts at the center:
  - skills
  - subagents
  - hooks
  - memory
  - MCP
  - plugins
  - remote/background tasks

This phase exists to make that architecture harder to drift away from.

---

## Why This Phase Exists

The repo now has a real runtime layer, canonical workspace model, module manifests, runtime persistence, and runtime-backed remote reads. That is the right direction.

The remaining weakness is that the system can still drift into split-brain behavior:

- queue state vs runtime state
- local workflows vs remote workflows
- generated outputs vs approved outputs
- config/doc context vs managed memory

If we expand workflows or archetypes before fixing that seam, Kai will drift back toward a generic harness with marketing features attached.

---

## Phase Objective

Make **runtime state, artifact lineage, and approval lifecycle canonical**.

At the end of this phase:

- the runtime is the source of truth for run meaning
- the queue is only transport and execution metadata
- approvals are explicit operating actions, not passive derived states
- major workflows return one canonical bundle shape
- approved runs can write back into runtime-managed memory

---

## Non-Drift Rules

Before merging work in this phase, ask:

1. Does this make the runtime contract more central or less central?
2. Does this reduce duplicate state or execution paths?
3. Does this make marketing workflows feel more native rather than more generic?
4. Does this improve local and remote parity?
5. Does this strengthen approval, lineage, observability, or memory?
6. Would this make sense if Kai were a real shipped product rather than a repo experiment?

If the answer is "no" to most of those questions, the change is probably drift.

---

## Scope

### 1. Approval lifecycle

Implement approval as first-class runtime behavior, not just a value attached to artifacts.

Required operations:

- `approve_run(run_id)`
- `hold_run(run_id)`
- `request_revision(run_id, note)`
- `reject_run(run_id, note)`
- `resume_run(run_id, inputs_override=None)`

Required effects:

- runtime run status updates
- approval artifact updates
- revision lineage preserved
- resumable follow-up runs linked to prior runs

### 2. Runtime-first job reads

Refactor remote job reads so they treat runtime state as canonical.

The queue should own:

- dispatch state
- started/completed/failed execution metadata
- retries
- worker errors

The runtime should own:

- run status
- workflow outputs
- approval state
- lineage
- artifact IDs
- artifact payloads
- observability state

Expected result:

- `/jobs/*` becomes a compatibility and transport surface
- `/runtime/*` becomes the canonical product surface

### 3. Canonical run bundle

Define one normalized bundle serializer for all important workflows.

Bundle shape:

- `run`
- `lineage`
- `artifacts`
- `approval`
- `observability`
- `memory_updates`

This bundle should be returned or referenced by:

- runtime bundle endpoints
- job detail endpoints
- future local skill wrappers

### 4. Memory writeback skeleton

After approved runs, write structured updates into runtime-managed memory.

Initial scope:

- approved voice/style constraints
- offer and proof-point updates
- winning angles or hooks
- workflow defaults
- channel-level learnings

This phase does not require a full learning engine. It only requires the contract and first writeback path.

---

## Explicitly Out of Scope

Do not expand surface area while this phase is underway.

Out of scope:

- new archetypes
- new channels
- major dashboard work
- broad docs rewrites
- connector expansion unless required by approval or memory flow
- large agent rewrites
- more workflow variety before the canonical contract is firm

---

## Acceptance Criteria

This phase is complete when all of the following are true:

1. A remote generation run can be created, held, revised, approved, and inspected through one canonical bundle.
2. A job and a runtime run cannot disagree on the meaning of status.
3. Approval state is explicit and queryable, not inferred from scattered artifact payloads.
4. Approved runs can write structured updates into runtime-managed memory.
5. A second major workflow can be onboarded without inventing a new state model.

---

## Recommended Implementation Order

1. Add approval mutation methods to the runtime store or runtime service layer.
2. Add runtime approval mutation endpoints.
3. Refactor job detail and status routes to runtime-first reads.
4. Introduce a shared canonical bundle serializer.
5. Add memory writeback skeleton for approved runs.
6. Port one additional workflow through the same contract to verify generality.

---

## Expected Deliverables

Code deliverables:

- runtime approval mutation methods
- approval endpoints
- canonical bundle serializer
- runtime-first job read logic
- memory writeback primitives
- one additional workflow ported through the bundle contract

Validation deliverables:

- focused tests for approval transitions
- focused tests for canonical bundle shape
- focused tests for runtime-first job reads
- focused tests for memory writeback on approval

---

## What Success Looks Like

After this phase, Kai should feel less like:

- a queue wrapped around a set of scripts

and more like:

- a real marketing operating system with a canonical runtime
- a system where local and remote runs share the same shape
- a system where approvals are operating actions
- a system where accepted work compounds into memory

That is the next step that keeps the repo moving toward the original product goal instead of drifting away from it.
