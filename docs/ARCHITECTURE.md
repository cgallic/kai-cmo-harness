# Kai Runtime Architecture

Kai is a **marketing operating system built on Claude Code**. It adds marketing-specific data models, audit engines, proposal systems, compliance checking, and approval workflows to Claude Code's existing operator experience.

> **Status note (April 2026):** For the full implementation-grounded assessment, see `docs/superpowers/specs/2026-04-03-system-current-state-report.md`.

## Product shape

Kai has two product surfaces:

1. **Local surface** [BUILT]
   Claude Code skills load marketing knowledge and framework instructions. The kai/ runtime provides business profiling, audits, proposals, approvals, and compliance checking.

2. **Remote surface** [PARTIAL]
   FastAPI gateway with SQLite job queue. Remote execution, action lifecycle, and scheduled tasks now exist in the codebase, but connector coverage and client onboarding are still incomplete.

Both surfaces resolve through the same canonical run contract and workspace model.

## Layer model

```
┌──────────────────────────────────────────────────────────────┐
│                   KAI MARKETING OS  [BUILT]                  │
│   audits • proposals • compliance • approvals • quality gates│
│   archetypes/modules • business profiling                    │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                    KAI DATA LAYER  [BUILT]                   │
│   runtime models • persistence • state • memory writeback    │
│   local runs • artifact tracking • action lifecycle          │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                CLAUDE CODE PRIMITIVES  [EXTERNAL]            │
│   skills • subagents • hooks • memory • MCP • plugins       │
└──────────────────────────────┬───────────────────────────────┘
                               │
┌──────────────────────────────▼───────────────────────────────┐
│                  IMPLEMENTATION LAYER  [MIXED]               │
│   scripts/content/engine.py  [BUILT]                         │
│   scripts/quality/*          [BUILT]                         │
│   gateway/*                  [PARTIAL]                       │
│   agent/*                    [PARTIAL]                       │
│   knowledge/*                [BUILT]                         │
│   kai/connectors/*           [PARTIAL — mixed real/stubbed]  │
│   kai/execution/*            [BUILT]                         │
└──────────────────────────────────────────────────────────────┘
```

**Key distinction:** Claude Code primitives (skills, subagents, hooks, memory, MCP, plugins) are features of Claude Code, not of the kai/ codebase. Kai leverages them but does not implement its own versions.

## Canonical runtime contracts

The new source of truth lives in `kai/runtime/`.

### Workspace profile
`KaiWorkspaceProfile` defines:
- workspace identity
- primary user type
- surfaces (`local`, `remote`)
- enabled plugins
- brands loaded into the workspace

### Brand profile
`KaiBrandProfile` defines:
- business identity
- archetype and overlay modules
- active channels
- proof points
- persona defaults
- GSC/GA/metadata bindings

### Module manifest
`KaiModuleManifest` defines:
- trigger keywords
- prompt hints
- required memory fields
- default workflows
- checklist pack
- KPI schema
- default subagents
- remote automation pack

### Run contract
`KaiRunRequest` is the common contract for local and remote execution:
- `intent`
- `workflow`
- `brand_id`
- `surface`
- `module_set`
- `inputs`
- `metadata`

## Archetype modules

The first runtime-level modules shipped in this repo are:

- `local-service`
- `ecommerce`
- `professional-services`
- `multi-location`
- `software` (fallback baseline for SaaS/digital products already in the repo)

These manifests live in `kai/runtime/modules/`.

The module system is opinionated by default:
- one primary archetype
- zero or more overlays
- prompt and workflow changes come from the active module set

## Execution flow

### Local [BUILT — content pipeline working]

1. User invokes a Kai skill (Claude Code skill system)
2. Skill loads knowledge files + framework instructions
3. `scripts/content/engine.py` runs with brief context, framework context, proof points
4. Quality gate evaluates output (Four U’s, banned words, SEO lint)
5. Approval policy decides `approved`, `held`, or `failed`
6. Artifact is logged and linked back to the run

### Programmatic audit flow [BUILT — tested end-to-end]

1. Load BusinessProfile (from config or intake)
2. Archetype detection + overlay inference
3. Run 8 audit engines → scored findings
4. Build proposals from findings (5-factor ranking, dedup, dependency resolution)
5. Bundle into time-phased plan (7-day, 30-day, campaign packs)
6. Route through approval workflow (risk-based auto-approval for low-risk)
7. Track action lifecycle (propose → approve → execute → complete)

### Remote [PARTIAL — first closed loop exists, connector coverage incomplete]

1. Gateway receives a request (FastAPI + SQLite job queue)
2. Gateway can resolve workspace + brand model from `kai.runtime`
3. Approved actions can now flow through execution infrastructure and scheduled tasks exist
4. **Gap:** Pipedream-backed account connection, channel coverage, and business onboarding are not yet complete

## Current code mapping

### Runtime layer [BUILT]
- `kai/runtime/models.py` — 5 canonical dataclasses
- `kai/runtime/store.py` — atomic persistence with lineage tracking
- `kai/runtime/loader.py` — workspace + brand loading
- `kai/runtime/actions.py` — action lifecycle state machine
- `kai/runtime/policy.py` — risk classification + banned words
- `kai/runtime/integrations.py` — channel connector registry
- `kai/runtime/memory.py` — memory layout + retrieval
- `kai/runtime/audit.py` — audit finding models + scoring
- `kai/runtime/application_flow.py` — profile → audit → proposal → bundle
- `kai/runtime/business_profile.py` — business profile + normalization
- `kai/runtime/modules/*.yaml` — 5 archetype manifests

### Marketing OS layer [BUILT]
- `kai/audits/` — 8 audit engines (12,688 lines)
- `kai/proposals/` — ranking, bundling, dedup, pruning (~2,300 lines)
- `kai/compliance/` — 100+ rules, 13 check methods, 5 policy packs
- `kai/archetypes/` — 4 archetypes + 4 overlays + activation logic
- `kai/models/` — domain models (BusinessProfile, AuditFinding, Proposal, etc.)
- `kai/flows/` — onboarding, approval, audit review, execution, learning review
- `kai/memory/` — JSONL writeback + retrieval + anti-patterns
- `kai/watchers/` — 5+ concrete watchers (logic real, data feeds not connected)

### Content pipeline [BUILT]
- `scripts/content/engine.py` — outcome engine (persona → brief → LLM → gate → approval)
- `scripts/content/_writer.py` — LLM writing with format instructions
- `scripts/content/brief_generator.py` — structured brief creation
- `scripts/quality/*` — quality gate scripts

### Connectors [PARTIAL — business logic only]
- `kai/connectors/ads/` — Google Ads, Meta Ads, LSA (request construction, no HTTP)
- `kai/connectors/analytics/` — GA4, GSC, GBP (stubs returning `[]`)
- `kai/connectors/cms/` — WordPress, Shopify, Webflow (logic real, HTTP stub)
- `kai/connectors/lifecycle/` — Mailchimp, SendGrid, Loops (logic real, HTTP stub)
- `kai/connectors/social/` — Facebook, Instagram, TikTok, LinkedIn, YouTube (mostly stubs)

### Real API clients [BUILT — in scripts/, not routed through connectors]
- `scripts/analytics/google_analytics.py` — real GA4 API via BetaAnalyticsDataClient
- `scripts/ads/meta_ads_create.py` — real Meta Graph API via requests
- `scripts/ads/facebook_ads.py` — real Facebook API via requests
- `scripts/analytics/supabase_analytics.py` — real Supabase client

### Remote surface [PARTIAL]
- `gateway/main.py` — FastAPI app with 11+ routers
- `gateway/jobs.py` — SQLite job queue with ThreadPoolExecutor
- `gateway/routers/runtime.py` — runtime state API endpoints

### Execution layer [BUILT]
- `kai/execution/credentials.py` — credential resolution
- `kai/execution/connector_factory.py` — provider/channel instantiation
- `kai/execution/executor.py` — approved-action execution bridge
- `kai/execution/result.py` — normalized execution result
- `kai/execution/anomaly_proposals.py` — analytics anomaly proposal creation

### Background automation [PARTIAL]
- `agent/scheduler.py` — scheduled task registration
- `agent/tasks/execute_approved.py` — approved action execution task
- `agent/tasks/connector_health.py` — integration health check task
- `agent/tasks/daily_analytics.py` — connector-first analytics task with fallback

## Design rules

- The repo should prefer **Claude Code-like primitives** over custom orchestration whenever possible.
- Marketing-specific logic stays custom only when it is the moat:
  - module activation
  - quality/policy scoring
  - approvals
  - learning loop
  - connector normalization
- Markdown files like `MARKETING.md` remain useful exports, but they are not the primary runtime contract.
- New remote capabilities should attach to the runtime workspace/brand model rather than inventing parallel client schemas.
- External systems should follow the **brain / nervous system / arms** model documented in:
  - `docs/superpowers/specs/2026-04-03-brain-arms-architecture-principle.md`
  - Kai is the decision brain
  - policy, approvals, and action contracts are the nervous system
  - websites, socials, ads, email, analytics, and call systems are execution arms
  - arms should observe, execute approved actions, and report results back; they should not invent strategy

## Near-term migration path

1. Continue routing content generation and remote reads through `kai.runtime`
2. Move more gateway and agent code off legacy client config assumptions
3. Attach artifacts and approvals to canonical runtime records
4. Promote hooks, memory, and subagent definitions into first-class runtime assets

## Current implementation plan

The active next step is documented in:

- `docs/superpowers/specs/2026-04-02-phase-2a-runtime-approval-plan.md`
- `docs/superpowers/specs/2026-04-02-connected-marketing-ops-plan.md`
- `docs/superpowers/specs/2026-04-02-complete-system-task-map.md`
- `docs/superpowers/specs/2026-04-03-kai-pipedream-connect-architecture.md`
- `docs/superpowers/specs/2026-04-03-pipedream-connector-completion-plan.md`

That phase exists to prevent architectural drift while the repo is being productized into a marketing-native Claude Code-style clone. Its focus is narrow on purpose:

- make runtime state canonical
- make approval lifecycle explicit
- standardize one canonical bundle shape
- add structured memory writeback after approved runs

The application-level companion plan defines what that infrastructure is for:

- connected website, social, ad, email, and analytics operations
- proposal and approval flows for real channel actions
- compliant background execution
- archetype-aware operating loops

The current connector-platform decision is:

- use **Pipedream Connect** as the external connector and managed-auth substrate
- keep Kai as the source of truth for proposals, policy, approvals, artifacts, and memory
- isolate provider execution behind Kai-owned adapter layers

The complete-system task map expands that into the full implementation backlog:

- workspace and business understanding
- audits, proposals, and review bundles
- creative and asset generation
- website, social, paid, lifecycle, analytics, and reputation operations
- approvals, watchers, learning loops, and operator surfaces
