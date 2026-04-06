# Local-Service Application Orchestration Plan

**Date:** 2026-04-02  
**Status:** Active execution plan  
**Goal:** Coordinate the next application-first implementation pass across the available subagents without drifting back into platform-heavy work.

---

## Objective

Build the first real application slice for Kai:

**business profile -> local-service audit -> prioritized findings -> typed action proposals -> operator review bundle**

This work should sit above the connected execution and compliance layer that is already being built elsewhere.

---

## Product Focus

The product is not "better runtime infrastructure."

The product is:

- understanding a business
- diagnosing its marketing situation
- deciding what should happen next
- handing off structured actions to the connected execution layer

The current slice is intentionally narrow:

- one archetype: `local-service`
- one end-to-end application path
- one clean handoff into the action system

---

## Orchestrator Responsibilities

The orchestrator owns:

- canonical application contracts
- anti-drift checks
- file and interface review
- integration of the agent outputs
- final validation
- handoff into the connected execution/action system

The orchestrator should not spend most of its time implementing platform plumbing unless directly needed to unblock the application flow.

---

## Canonical Contracts To Lock

These are the contracts the orchestrator will enforce across all subagent work:

- `BusinessProfile`
- `AuditFinding`
- `AuditResult`
- `ProposedAction`
- `ReviewBundle`

Expected shape progression:

1. `BusinessProfile` describes the business and marketing context.
2. `AuditResult` captures scores, findings, and evidence.
3. `ProposedAction` converts findings into typed website/social/ad actions.
4. `ReviewBundle` groups the profile, audit, and proposals into one operator-facing package.

---

## Work Split

## Subagent 1: Maxwell

Primary ownership:

- business profile model
- connected workspace application model
- local-service fixtures and defaults
- profile parsing and normalization
- profile tests

Output should include:

- structured business profile schema
- loader/serializer path
- local-service example profile
- tests for profile normalization and archetype defaults

## Subagent 2: Heisenberg

Primary ownership:

- local-service audit engine
- finding schema
- scoring and prioritization
- evidence capture
- audit tests

Output should include:

- local-service audit result schema
- scored findings across the agreed categories
- priority ranking logic
- tests for findings and scoring

## Orchestrator

Primary ownership:

- proposal contract
- review bundle contract
- integration of profile + audit outputs
- handoff contract to `ActionStore`
- final end-to-end assembly and validation

---

## Local-Service Audit Categories

The first archetype should score and diagnose:

- offer clarity
- trust and proof
- conversion path
- local SEO / local intent coverage
- speed-to-lead
- reviews and reputation
- channel presence
- follow-up gaps

These categories are the minimum useful local-service operating view.

---

## Proposed Action Families

The orchestrator layer will convert audit findings into:

- website actions
- social actions
- ad actions

Each proposed action should carry:

- `action_type`
- `channel`
- `title`
- `reason`
- `business_impact`
- `expected_outcome`
- `risk_tier`
- `approval_required`
- `suggested_payload`
- `source_finding_ids`

The connected action system can then evaluate, hold, approve, or execute those actions.

---

## File Ownership Boundaries

Maxwell should primarily touch:

- new application profile modules
- application fixtures
- tests for business profile handling

Heisenberg should primarily touch:

- new application audit modules
- scoring/prioritization logic
- tests for audit behavior

The orchestrator should primarily touch:

- proposal generation modules
- review bundle modules
- integration glue
- shared contract files where needed

Avoid overlapping write sets unless integration requires it.

---

## Non-Drift Rules

Reject work that mainly:

- improves runtime internals without unblocking the app flow
- expands connector plumbing
- adds generic abstractions without business/application value
- broadens archetypes before `local-service` works end to end

Prefer work that:

- improves business understanding
- sharpens archetype-specific judgment
- creates cleaner action proposals
- helps the operator decide what to do next

---

## Definition of Done

This coordinated slice is complete when:

1. A local-service business can be loaded into a canonical profile.
2. Kai can audit that business using structured findings and scores.
3. Findings can be turned into typed website/social/ad actions.
4. The operator can inspect a single review bundle.
5. That bundle can hand off to the connected action/execution layer without inventing a new contract.

---

## Execution Order

1. Maxwell ships `BusinessProfile` and local-service fixtures.
2. Heisenberg ships `AuditResult` and scoring against that profile.
3. Orchestrator locks `ProposedAction` and `ReviewBundle`.
4. Orchestrator integrates the full path:
   - profile
   - audit
   - findings
   - action proposals
   - review bundle
5. Final validation confirms clean handoff to the connected ops/action layer.

---

## Notes

This plan is intentionally biased toward the application.

The runtime, approval, and action-control foundation now exists well enough to support this work. The next value comes from making Kai understand and operate a real business archetype, not from continuing to optimize infrastructure in isolation.
