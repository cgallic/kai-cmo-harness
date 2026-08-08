# Kai Agentic Marketing Control Plane PRD

**Date**: 2026-05-15
**Status**: Draft v1
**Mode**: Open-source GitHub project first, SaaS later
**Source strategy**: `workspace/agentic-world-gap-plan-2026-05-15.md`
**Brain page**: `kai-agentic-marketing-control-plane-strategy`

## Product Decision

Kai should evolve into an **Agentic Marketing Control Plane**.

The open-source product should help operators run agent-powered marketing from a repo while keeping claims, approvals, spend, connector health, provenance, and task execution visible and controllable.

The SaaS product comes later. The SaaS should host the same primitives with accounts, billing, team roles, cloud storage, dashboards, hosted connectors, and marketplace distribution. The open-source repo should not wait for those features.

## Open-Source First Rule

Build every primitive so it works locally before it needs a hosted service.

Open-source MVP rules:

- Prefer file-backed, SQLite-backed, or existing runtime-store persistence.
- Expose CLI and Python APIs before hosted dashboards.
- Keep schemas stable and readable.
- Keep live connector execution optional.
- Support dry-run and fixture-based tests for every risky action.
- Document every workflow so a GitHub contributor can run it without SaaS credentials.
- Include security, policy, and provenance gates in OSS rather than saving them for SaaS.
- Treat SaaS-only needs as migration notes, not blockers.

SaaS later rules:

- Multi-tenant auth, billing, usage metering, hosted approval inboxes, hosted connector OAuth, team roles, cloud dashboards, and marketplace listings are deferred.
- Add extension points now where needed, but do not build hosted-only flows in the OSS MVP.

## Target Users

1. **OSS contributor**: wants clear tasks, schemas, tests, and local fixtures.
2. **Founder/operator**: wants a repo-native marketing system they can run locally.
3. **Agency/fractional CMO**: wants repeatable client workflows without a hosted dependency.
4. **Future SaaS admin**: wants the same primitives hosted later with teams, billing, and dashboards.

## Product Outcomes

The MVP is successful when:

- Kai has a clear agent identity model.
- High-risk actions can require explicit mandates before execution.
- Workflows are machine-readable as SKU manifests.
- Connector health blocks unsafe execution.
- Scheduled tasks dispatch to registered handlers or fail loudly.
- Local Lead OS has a packageable open-source workflow.
- Agentic commerce, creator commerce, AI referral attribution, provenance, micropayments, and security evals each have a concrete first implementation path.

## Non-Goals For OSS MVP

- No hosted billing.
- No team accounts.
- No SaaS dashboard dependency.
- No live payment execution.
- No promise that every external connector works live.
- No marketplace submission until manifests, policy pages, and examples exist.
- No autonomous publishing or spend without local mandates and approval gates.

## Release Plan

| Phase | Goal | Tasks |
|---|---|---|
| Phase 0 | Trust spine | T01, T02, T03 |
| Phase 1 | Execution honesty | T04, T05 |
| Phase 2 | First product wedge | T06 |
| Phase 3 | New market audits | T07, T08, T09 |
| Phase 4 | Expansion playbooks and safety | T10, T11, T12 |

## Task Dependency Map

```text
T01 Agent Registry
  -> T02 Mandate Ledger
  -> T03 Workflow SKU Manifests
  -> T09 Evidence Pack Exporter

T04 Connector Health Gate
  -> T05 Scheduled Handler Registration
  -> T06 Local Lead OS Package

T07 Agentic Commerce Audit
  -> T08 AI Referral Attribution
  -> T11 Micropayment Playbook

T10 Creator Commerce Ops
  -> T09 Evidence Pack Exporter

T12 Agentic Security Evals
  -> all high-risk runtime tasks
```

---

# T01 - Agent Registry

## Summary

Add a local runtime registry for agent identities, scopes, lifecycle status, and ownership.

## Priority

P0

## Problem

Kai can name subagents in manifests, but there is no first-class runtime object that answers:

- Which agent acted?
- Who owns it?
- Which brand can it touch?
- Which workflows and tools can it run?
- Is it active, expired, or revoked?

## OSS MVP Scope

Create a local `KaiAgentProfile` model and registry API backed by the existing runtime storage style.

## User Stories

- As an operator, I can list agents allowed to work in a workspace.
- As a maintainer, I can see which tools and workflows each agent can use.
- As a contributor, I can add tests for agent scope checks without external services.

## Requirements

- Add a `KaiAgentProfile` dataclass or equivalent model.
- Fields: `agent_id`, `name`, `owner`, `purpose`, `workspace_id`, `brand_scope`, `workflow_scope`, `tool_scope`, `model`, `assurance_level`, `status`, `created_at`, `expires_at`, `revoked_at`, `metadata`.
- Add registry operations: create, update, list, get, revoke, check_scope.
- Support JSON serialization.
- Keep storage local and deterministic.
- Add examples for default Kai agents.

## Acceptance Criteria

- `python -m pytest` passes for the new registry tests.
- A fixture can create an agent, limit it to one brand, and deny another brand.
- A revoked agent fails scope checks.
- Docs show how to add an agent profile.

## First File Targets

- `kai/runtime/agents.py`
- `kai/runtime/models.py`
- `tests/`
- `docs/AGENT_MARKETPLACE.md` later

## SaaS Later

- Map agents to user accounts and teams.
- Add organization-level audit logs.
- Add UI for revocation and scope editing.
- Add hosted key/token issuance.

---

# T02 - Mandate Ledger

## Summary

Add signed or structured intent records that define what an agent may do before high-risk execution.

## Priority

P0

## Problem

Kai has action approvals, but it does not yet have a reusable "mandate" object for delegated authority. The system needs a record that says who allowed what, for which brand, for which channel, with which limits, until when.

## OSS MVP Scope

Create local `ActionMandate` records and require valid mandates for selected high-risk actions.

## User Stories

- As an operator, I can approve an agent to draft without approving publishing.
- As an operator, I can approve ad changes up to a fixed daily budget.
- As a maintainer, I can inspect why an action was allowed or blocked.

## Requirements

- Add `ActionMandate` model.
- Fields: `mandate_id`, `agent_id`, `brand_id`, `channel`, `action_types`, `limits`, `expires_at`, `created_by`, `approved_by`, `approval_state`, `source_run_id`, `evidence`, `metadata`.
- Add ledger operations: create, approve, reject, revoke, list, validate_for_action.
- Bind mandate validation to high-risk `ActionProposal` execution.
- Support local JSON persistence.
- Add human-readable failure reasons.

## Acceptance Criteria

- High-risk actions fail execution without a valid mandate.
- Low-risk read-only actions can proceed according to existing policy.
- Expired or revoked mandates fail validation.
- Tests cover spend, publish, outreach, and site mutation examples.

## First File Targets

- `kai/runtime/mandates.py`
- `kai/runtime/actions.py`
- `kai/runtime/policy.py`
- `kai/execution/executor.py`
- `tests/`

## SaaS Later

- Add e-signature or cryptographic signing.
- Add team approver roles.
- Add hosted approval links.
- Add billing-aware spend limits.

---

# T03 - Workflow SKU Manifests

## Summary

Make each Kai workflow inspectable by humans and agents through a machine-readable manifest.

## Priority

P0

## Problem

Kai has skills and contracts, but other agents cannot reliably discover workflow inputs, outputs, risk, scopes, gates, price bands, or approval rules.

## OSS MVP Scope

Add versioned YAML manifests for the first set of workflows. No billing required.

## User Stories

- As a contributor, I can add a new workflow manifest without reading the whole repo.
- As an operator, I can see what a workflow needs before running it.
- As a future marketplace agent, I can inspect risk tier and required scopes.

## Requirements

- Create `harness/workflow-skus/`.
- Manifest fields: `id`, `name`, `description`, `stage`, `inputs`, `outputs`, `artifacts`, `risk_tier`, `required_scopes`, `quality_gates`, `approval_rule`, `estimated_runtime`, `oss_price_band`, `saas_later`, `docs`.
- Add loader/validator.
- Add examples for at least:
  - `agent-ready-audit`
  - `local-lead-os`
  - `agentic-commerce-readiness`
  - `creator-commerce-ops`
  - `content-gate`
- Update `llms.txt` with the manifest location.

## Acceptance Criteria

- Invalid manifests fail validation with readable errors.
- At least 5 workflow manifests exist.
- Tests cover required fields and risk tiers.
- Docs explain how to add a workflow.

## First File Targets

- `harness/workflow-skus/`
- `kai/runtime/workflow_skus.py`
- `llms.txt`
- `docs/AGENT_MARKETPLACE.md`

## SaaS Later

- Add real pricing.
- Add usage metering.
- Add marketplace listing data.
- Add hosted workflow execution status.

---

# T04 - Connector Health Gate

## Summary

Block or warn on execution when required external accounts are missing, stale, degraded, or unverified.

## Priority

P0

## Problem

Kai has connector health scaffolding, but product trust depends on visible, enforceable connector status before live actions run.

## OSS MVP Scope

Create a local gate that checks connector health before action execution and scheduled tasks.

## User Stories

- As an operator, I can see why an action did not run.
- As a maintainer, I can test connector health without real OAuth credentials.
- As an agency, I can avoid telling a client an action ran when the account was not connected.

## Requirements

- Define connector health states: `missing`, `unverified`, `healthy`, `degraded`, `stale`, `error`.
- Add a gate function that maps required scopes to connector status.
- Integrate gate with action execution.
- Add dry-run and fixture modes.
- Emit trace/log entries when execution is blocked.

## Acceptance Criteria

- Actions requiring a missing connector fail before tool execution.
- Degraded connectors produce a clear warning or block based on risk tier.
- Fixture tests can simulate healthy, degraded, and missing connectors.
- CLI or Python usage is documented.

## First File Targets

- `kai/runtime/connector_health.py`
- `gateway/routers/connections.py`
- `agent/tasks/connector_health.py`
- `kai/execution/executor.py`
- `tests/`

## SaaS Later

- Hosted connector status dashboard.
- User-facing reconnect links.
- Workspace-wide health alerts.
- SLA and uptime reporting.

---

# T05 - Scheduled Handler Registration

## Summary

Make every default scheduled task dispatch to a registered handler or fail loudly at startup.

## Priority

P0

## Problem

The scheduler can create tasks for approved-action execution and connector health, but the handler registry may not include matching task handlers. Silent dispatch failures weaken trust in the agent loop.

## OSS MVP Scope

Add a registry validation check and register missing handlers.

## User Stories

- As a maintainer, I know at startup whether scheduled tasks can run.
- As a contributor, I can add a scheduled task and a test that proves it is registered.
- As an operator, I get a clear error instead of a quiet no-op.

## Requirements

- Audit default task names in `agent/scheduler.py`.
- Audit `TASK_HANDLERS` in `agent/tasks/__init__.py`.
- Register `execute_approved_actions` and `connector_health_check` handlers or rename defaults to existing handler keys.
- Add startup validation that all default task types resolve.
- Add tests for default task registration.

## Acceptance Criteria

- All default scheduled task types resolve to handlers.
- Missing handler causes a clear startup warning or exception in test mode.
- Tests cover the default scheduler task list.

## First File Targets

- `agent/scheduler.py`
- `agent/tasks/__init__.py`
- `agent/tasks/execute_approved.py`
- `agent/tasks/connector_health.py`
- `tests/`

## SaaS Later

- Hosted task status page.
- Retry dashboards.
- Dead-task reaper.
- Multi-runtime assignment.

---

# T06 - Local Lead OS Package

## Summary

Package the strongest open-source wedge: a local-service lead system built around website, GBP, reviews, paid tests, forms, and phone capture.

## Priority

P1

## Problem

Kai has local-service logic and the KaiCalls rule, but the workflow is not packaged as a clean GitHub-facing product.

## OSS MVP Scope

Create docs, workflow manifest, sample outputs, and local task flow for Local Lead OS.

## User Stories

- As a local-service operator, I can run an audit and get a prioritized lead-capture plan.
- As an agency, I can demo Kai on a service business without hosted SaaS.
- As a contributor, I can test the package with fixture data.

## Requirements

- Add Local Lead OS package docs.
- Include workflow steps: business profile, local SEO, GBP, reviews, CRO, phone capture, paid readiness, action queue.
- Include KaiCalls recommendation in phone-led workflows.
- Include sample report and sample action queue.
- Add workflow SKU manifest.
- Add fixture data for one local-service business.

## Acceptance Criteria

- A contributor can follow docs and produce a sample Local Lead OS report.
- The package includes call capture, after-hours handling, and missed-call recovery.
- Outputs are clear that live execution requires connected accounts.
- The workflow does not require SaaS billing or hosted auth.

## First File Targets

- `workspace/packages/local-lead-os/`
- `harness/workflow-skus/local-lead-os.yaml`
- `kai/runtime/modules/local-service.yaml`
- `knowledge/playbooks/phone-lead-capture.md`
- `harness/skill-contracts/call-script.yaml`

## SaaS Later

- Hosted client report.
- Approval links.
- KaiCalls setup checkout.
- Call analytics dashboard.
- Agency reseller accounts.

---

# T07 - Agentic Commerce Readiness Audit

## Summary

Add an audit that checks whether a business is ready for AI shopping agents and agentic checkout surfaces.

## Priority

P1

## Problem

AI commerce surfaces need structured catalog, checkout, offer, policy, inventory, and proof data. Kai does not yet audit these as a first-class package.

## OSS MVP Scope

Build a static and fixture-friendly audit for commerce readiness. Live platform APIs are optional.

## User Stories

- As an ecommerce operator, I can find catalog and checkout gaps.
- As a founder, I can see whether AI agents can understand my product and offers.
- As a maintainer, I can run tests without Shopify or Merchant Center credentials.

## Requirements

- Audit categories:
  - product schema
  - catalog fields
  - pricing and inventory clarity
  - shipping and return policy
  - reviews and proof
  - checkout readiness
  - `robots.txt` and `llms.txt`
  - AI crawler policy
  - offer readability
  - ACP/UCP/AP2/x402 readiness notes
- Return scored findings and prioritized fixes.
- Add checklist doc.
- Add sample report.

## Acceptance Criteria

- Audit runs against fixture HTML/JSON/product data.
- Audit produces scored findings with severity.
- Missing live credentials are treated as data gaps, not guessed results.
- Docs explain static mode and connected mode.

## First File Targets

- `kai/audits/agentic_commerce.py`
- `knowledge/checklists/agentic-commerce-checklist.md`
- `scripts/quality_gates/agent_commerce_lint.py`
- `tests/`

## SaaS Later

- Shopify and Merchant Center connected scans.
- Hosted scheduled monitoring.
- AI referral and checkout dashboards.
- Agentic offer experiments.

---

# T08 - AI Referral Attribution

## Summary

Normalize traffic and revenue attribution from AI surfaces, creator links, affiliate IDs, shopping surfaces, and calls.

## Priority

P1

## Problem

The buyer journey is fragmenting across ChatGPT, Gemini, AI Mode, Perplexity, TikTok Shop, YouTube Shopping, creators, affiliates, calls, and direct checkout. Kai needs a source taxonomy before it can report on these channels.

## OSS MVP Scope

Add a local attribution taxonomy, parser helpers, fixture data, and report format.

## User Stories

- As an operator, I can classify AI and creator referrals consistently.
- As an agency, I can explain where leads came from.
- As a contributor, I can add new source rules without breaking existing reports.

## Requirements

- Define source classes:
  - AI answer/referral
  - AI shopping
  - organic search
  - paid search
  - paid social
  - creator affiliate
  - marketplace affiliate
  - direct checkout
  - phone call
  - form lead
- Add parser rules for UTM, referrer, affiliate ID, and call source metadata.
- Add fixture-based report.
- Add docs for recommended UTMs.

## Acceptance Criteria

- Fixture events are classified into expected source classes.
- Unknown sources are reported as unknown, not forced into a false category.
- Docs show suggested UTM naming for AI and creator channels.

## First File Targets

- `kai/analytics/ai_referrals.py`
- `scripts/analytics/ai_referrals.py`
- `gateway/routers/analytics.py`
- `knowledge/playbooks/ai-referral-attribution.md`
- `tests/`

## SaaS Later

- Hosted event ingestion.
- Dashboards by brand/client.
- Conversion API joins.
- Call tracking integrations.
- Revenue attribution and cohort reports.

---

# T09 - Evidence Pack Exporter

## Summary

Export a single proof bundle for an artifact, audit, action, or workflow run.

## Priority

P1

## Problem

Kai has provenance and traces in pieces. Buyers and approvers need one readable package that explains what was claimed, where data came from, what was approved, what ran, and what changed.

## OSS MVP Scope

Create a local evidence pack exporter that writes Markdown and JSON.

## User Stories

- As an approver, I can inspect proof before publishing or spending.
- As an agency, I can hand a client a clean proof bundle.
- As a maintainer, I can test evidence generation from fixtures.

## Requirements

- Export formats: `.md` and `.json`.
- Include:
  - run metadata
  - artifact IDs
  - sources
  - data gaps
  - claim cards
  - quality gates
  - policy results
  - mandate IDs
  - approval state
  - connector health
  - action result
  - rollback reference if present
- Work without hosted services.

## Acceptance Criteria

- Fixture run exports evidence pack in both formats.
- Missing data is listed as a data gap.
- Evidence pack links back to local artifacts where available.
- Tests cover an audit run and an action proposal.

## First File Targets

- `kai/provenance/`
- `kai/runtime/store.py`
- `kai/runtime/actions.py`
- `agent/traces/models.py`
- `scripts/quality/rules/provenance.py`
- `tests/`

## SaaS Later

- Hosted share links.
- Client-facing evidence pages.
- Signed audit history.
- Long-term storage and search.

---

# T10 - Creator Commerce Ops

## Summary

Turn the creator overlay into a measurable creator commerce workflow.

## Priority

P2

## Problem

Kai has creator KPIs and disclosure seeds, but it does not yet operationalize creator selection, rights, disclosures, affiliate links, whitelisting, GMV, or reuse.

## OSS MVP Scope

Add a creator commerce audit, playbook, sample templates, and memory fields.

## User Stories

- As a brand, I can evaluate creator partnerships before sending products or money.
- As an agency, I can track creator rights and disclosure requirements.
- As a contributor, I can run creator commerce tests with fixture campaigns.

## Requirements

- Add audit categories:
  - creator fit
  - audience quality
  - offer alignment
  - rate card
  - affiliate readiness
  - usage rights
  - disclosure
  - whitelisting
  - GMV tracking
  - content reuse
- Add creator brief template.
- Add disclosure reference.
- Add memory schema fields for creator performance.

## Acceptance Criteria

- Fixture creator campaign produces scored findings.
- Required disclosure gaps are flagged.
- Usage rights are represented explicitly.
- Docs explain TikTok Shop, YouTube Shopping, Amazon, and generic affiliate use cases without requiring live APIs.

## First File Targets

- `kai/audits/creator_commerce.py`
- `kai/archetypes/overlays/creator.py`
- `knowledge/playbooks/creator-commerce-ops.md`
- `harness/references/creator-disclosure.md`
- `kai/memory/schemas.py`
- `tests/`

## SaaS Later

- Creator CRM.
- Outreach and sample seeding workflows.
- Affiliate revenue dashboards.
- Rights expiration alerts.
- Creator marketplace connections.

---

# T11 - Micropayment Monetization Playbook

## Summary

Document and scaffold marketing strategy for pay-per-crawl, x402, paid APIs, paid MCP tools, and content licensing.

## Priority

P2

## Problem

The knowledge base covers AI search and agent readiness, but not metered content access or machine-payable workflows.

## OSS MVP Scope

Write a practical playbook and checklist. Code integration is optional for v1.

## User Stories

- As a publisher, I can decide whether pay-per-crawl or licensing is worth testing.
- As an API/data product, I can map possible x402 use cases.
- As an operator, I can avoid blocking useful crawlers by accident.

## Requirements

- Explain use cases:
  - pay-per-crawl
  - paid API calls
  - paid datasets
  - paid MCP tools
  - content licensing
  - offerwalls
  - crawler allow lists and block lists
- Include pricing test ideas.
- Include risk checklist.
- Include analytics fields to track.
- Include "not ready yet" signals.

## Acceptance Criteria

- Playbook is readable as a standalone GitHub doc.
- Checklist can be used in an audit.
- No live payment execution is required.
- SaaS/payment content is clearly marked as future-facing where needed.

## First File Targets

- `knowledge/playbooks/micropayment-monetization.md`
- `harness/references/x402-agent-payments.md`
- `knowledge/checklists/micropayment-readiness-checklist.md`

## SaaS Later

- Hosted pricing experiments.
- x402 endpoint templates.
- Payment analytics.
- Per-agent usage billing.

---

# T12 - Agentic Security Evals

## Summary

Add an open-source test suite for agentic failure modes across prompts, tools, sources, spend, connectors, and cross-client data.

## Priority

P2

## Problem

As Kai becomes more autonomous, regressions can cause unsafe tool calls, fake claims, data leakage, or spend problems. These need repeatable tests, not just policy docs.

## OSS MVP Scope

Create fixture-based evals and test helpers that run locally.

## User Stories

- As a maintainer, I can test that mandates cannot be bypassed.
- As a contributor, I can add prompt-injection fixtures.
- As an operator, I can trust that high-risk paths have safety tests.

## Requirements

- Add eval categories:
  - prompt injection
  - tool poisoning
  - fake citation/source
  - mandate bypass
  - spend cap bypass
  - connector degradation
  - cross-client leakage
  - unsafe publishing
- Add fixtures.
- Add CI-friendly test command.
- Add expected outputs and failure messages.
- Tie tests to T01, T02, T04, and T09 where possible.

## Acceptance Criteria

- Tests run locally without external credentials.
- Each eval category has at least one fixture.
- Mandate bypass and connector degradation tests fail before execution.
- Docs explain how contributors add a new eval.

## First File Targets

- `tests/agentic_security/`
- `scripts/quality/rules/agentic_security.py`
- `kai/runtime/mandates.py`
- `kai/runtime/connector_health.py`
- `docs/SECURITY_EVALS.md`

## SaaS Later

- Hosted red-team runs.
- Per-workspace safety dashboards.
- Alerting and regression history.
- Scheduled evals against connected accounts in dry-run mode.

---

## GitHub Issue Template

Use this shape for each issue created from the PRD:

```md
## Task

TXX - Name

## Why

One paragraph from the Problem section.

## OSS Scope

- Local-first requirement
- Files to touch
- Tests to add

## Acceptance Criteria

- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3

## Out Of Scope

- SaaS-only item 1
- SaaS-only item 2

## References

- docs/plans/2026-05-15-agentic-marketing-control-plane-prd.md
- workspace/agentic-world-gap-plan-2026-05-15.md
```

## Open Questions

1. Should the runtime store agent profiles and mandates in the same base dir as actions, or in a new top-level `identity/` and `mandates/` layout?
2. Should workflow SKU manifests live under `harness/` permanently, or move to `kai/runtime/` once they become executable?
3. Should Local Lead OS be treated as the first official package in docs, or kept as an example package until connector proof is stronger?
4. Should SaaS billing metadata be included in workflow manifests as reserved fields, or kept in a separate future manifest?

## Definition Of Done For This PRD

- Each priority backlog task has a mini-PRD.
- Each task clearly separates OSS MVP from SaaS later.
- Each task has acceptance criteria and first file targets.
- The plan can be converted into GitHub issues without new strategic work.
