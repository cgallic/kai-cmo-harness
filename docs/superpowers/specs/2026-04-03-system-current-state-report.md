# Kai Marketing OS — Current State Report

**Date:** 2026-04-03
**Version:** 1.0.0
**Purpose:** Honest, implementation-grounded assessment of where the system is today.

---

## Executive Summary

**What Kai is now:** A marketing data model and audit/proposal engine implemented in Python (~128K lines across 175 files in `kai/`), backed by a comprehensive marketing knowledge base (168 markdown files), a content pipeline that chains through LLMs with quality gates (`scripts/content/`), and a FastAPI gateway for remote execution. The system runs inside Claude Code and leverages Claude Code's skill system as its primary operator surface.

**What stage it is at:** Connector rollout and proof phase. The core data models, audit engines, proposal ranking, compliance rules, and approval workflows are implemented and tested. A Pipedream-backed execution layer now provides real HTTP transport for all supported providers — the full audit→proposal→approval→execution→verification chain is wired end-to-end. The system is blocked on live Pipedream credentials and real account connections for KaiCalls and Starrs Party to complete the first live actions.

**Strongest parts:**
- Runtime persistence layer (atomic writes, thread-safe, audit log)
- Audit engines with real scoring algorithms (8 audit categories, 40+ checks, severity-weighted scoring)
- Proposal system (5-factor weighted ranking, deduplication, dependency resolution, capacity-aware pruning)
- Compliance engine (100+ rules, 50+ regex patterns, 13 check methods)
- Policy engine (risk tier classification, banned word detection, regulated claim detection)
- Knowledge base (41 playbooks, 27 frameworks, 24 checklists, 17 channel guides, 12 ad platform policies)
- Content pipeline with quality gates (Four U's scoring, banned word check, SEO lint)
- Test coverage on core flows (239 tests across 6 files, all passing)

**Main gaps:**
- Live Pipedream credentials and real account connections not yet configured — execution layer is wired but untested against real APIs
- Creative system generates templates/briefs with `[Placeholder]` text, not actual content — it is a "recipe generator, not LLM caller"
- The 31 `/kai-*` commands listed in README are Claude Code superpowers skills, not features of the kai/ runtime itself
- Agent loop and subagent orchestration are sketched, not operational

---

## Capability Inventory

### 1. Runtime / State / Artifacts

**Status: BUILT — Production-grade**

| Component | File | Lines | Assessment |
|-----------|------|-------|------------|
| Run persistence | `kai/runtime/store.py` | 705 | Atomic JSON writes, thread-safe (RLock), lineage tracking |
| Artifact storage | `kai/runtime/store.py` | (same) | Type-enumerated artifacts linked to runs |
| State derivation | `kai/runtime/store.py` | (same) | Latest-run-by-brand-workflow queries |
| Workspace loading | `kai/runtime/loader.py` | ~150 | Config.yaml + env-based resolution |
| Canonical models | `kai/runtime/models.py` | 146 | 5 dataclasses: Workspace, Brand, RunRequest, RunRecord, ArtifactRecord |
| Module manifests | `kai/runtime/modules/*.yaml` | 5 files | local-service, ecommerce, professional-services, multi-location, software |

Evidence: Atomic `.tmp` → `.replace` write pattern. `RLock` on all mutations. Tests verify state transitions.

### 2. Business Profile / Audit / Proposal System

**Status: BUILT — Real algorithms**

#### Business Profile (`kai/runtime/business_profile.py`, `kai/models/business_profile.py`)
- 13 composable classes (identity, classification, offers, geography, personas, trust, goals, channels, constraints, budget, sales cycle, brand voice, operator)
- State normalization ("Texas" → "TX"), channel aliasing ("Google Ads" → "paid-search")
- Archetype inference from keywords
- Overlay detection (multi-location, franchise, SaaS, healthcare)

#### Audit Engines (`kai/audits/`, 12,688 lines)
- 8 engines: website conversion, trust/proof, local SEO, reviews/reputation, lifecycle followup, creative readiness, paid media readiness, CRM hygiene
- Real scoring: starts at 100, deducts by severity (CRITICAL: -25, HIGH: -15, MEDIUM: -8, LOW: -3)
- Pattern matching: 10+ regex patterns for trust assessment, 40+ specific checks per engine
- Archetype weighting: multipliers by business type (local-service gets 2.0x phone visibility weight)
- Per-location scoring for multi-location businesses

#### Proposal System (`kai/proposals/`, ~2,300 lines)
- **Ranking**: 5-factor weighted scoring (severity 0.30, impact 0.25, effort-inverse 0.20, stage-fit 0.15, budget-fit 0.10)
- **Deduplication**: 3-level (exact match, Jaccard title similarity >0.80, payload overlap >0.70)
- **Dependency resolution**: 14 implicit rules + topological sort + cycle breaking
- **Bundling**: 4 bundle types (7-day quick wins, 30-day plan, campaign packs, monthly operating plan)
- **Capacity pruning**: Monthly/daily hour caps, preferred channel boosting

### 3. Approval and Action System

**Status: BUILT — State machine enforced**

| Component | File | Assessment |
|-----------|------|------------|
| Action lifecycle | `kai/runtime/actions.py` | Full state machine: pending → approved → executing → completed. Auto-approval for low-risk. |
| Action types | `kai/actions/website.py` | 7 concrete action classes (UpdatePageCopy, etc.) with validate/preview/execute/verify phases |
| Approval flow | `kai/flows/approval_flow.py` | Queue-based review, batch approval, decision tracking, risk-tier ordering |
| Rollback | `kai/actions/rollback.py` | Before/after snapshot capture, state restoration |
| Paid media actions | `kai/actions/paid_media.py` | Ad action orchestration (370 lines) |
| Lifecycle actions | `kai/actions/lifecycle.py` | Email sequence handling |

Evidence: Tests in `test_actions_integrations.py` verify the full propose→approve→execute→complete workflow.

### 4. Policy / Compliance System

**Status: BUILT — Real rule evaluation**

#### Policy Engine (`kai/runtime/policy.py`, 528 lines)
- Risk tier classification across all channels (website, social, paid_media, email, analytics)
- 99 Tier-1 banned words with instant rejection
- Regulated-claim keyword detection (medical, financial, legal)
- Personal attribute pattern matching (Meta ads compliance)
- Budget constraint checking
- Frequency rate limiting

#### Compliance Engine (`kai/compliance/engine.py`, 1,200+ lines)
- 13 check methods via dynamic dispatch
- 50+ compiled regex patterns (superlatives, results claims, personal attributes, before/after)
- 100+ rules across 5 policy packs (website, social, paid_media, email, analytics)
- Industry-specific rules (healthcare, finance, legal, fitness)
- Violation tracking with fixability flags and fix suggestions
- Required disclosure enforcement

#### Supporting (`kai/compliance/`)
- `approval_routing.py` — approval workflow routing
- `audit_trail.py` — compliance audit trail
- `brand_constraints.py` — brand-level constraint enforcement
- `policy_packs/` — 5 packs with 24-18 rules each

### 5. Connected Ops / Integrations

**Status: BUILT — Pipedream-backed execution layer wired end-to-end**

#### Pipedream Adapter Layer (`gateway/adapters/pipedream/`, NEW)

All external system interaction now routes through Pipedream Connect, which manages OAuth credentials, account connections, and API execution without exposing secrets to Kai.

| Module | Purpose | Key Classes |
|--------|---------|-------------|
| `base.py` | SDK client wrapper, error classification, app slug mapping | `PipedreamClient`, `PipedreamError`, `PipedreamErrorKind` |
| `accounts.py` | Connected account CRUD, connect tokens, capability discovery | `PipedreamAccountManager` |
| `executor.py` | Action dispatch via `actions.run()` and `proxy.*` | `PipedreamExecutor` |
| `state_sync.py` | Channel state reads for audits/watchers | `PipedreamStateSync` |

#### Execution Routing (`kai/execution/executor.py`, UPDATED)

ActionExecutor now prefers Pipedream-backed execution when an integration has a `connected_account_id`. Falls back to direct connector dispatch for legacy integrations.

| Write Path | Pipedream Component | Verified Props |
|------------|---------------------|----------------|
| WordPress page update | `wordpress_org-update-post` | `post_id`, `content`, `title` |
| Mailchimp campaign | `mailchimp-create-campaign` | `list_id`, `subject_line`, `from_name` |
| Loops transactional | `loops_so-send-transactional-email` | `transactional_id`, `email`, `data_variables` |
| Facebook post | `facebook_pages-create-post` | `message`, `link` |
| LinkedIn post | `linkedin-create-share-update` | `text` |
| Google Ads campaign | `google_ads-update-campaign` | `campaign_id`, `status`, `budget_amount_micros` |
| Meta Ads creative | `facebook_marketing_api-create-ad` | `ad_account_id`, `name`, `creative` |
| SendGrid email | `sendgrid-send-email` | `to_email`, `from_email`, `subject`, `html_content` |

#### Connection Lifecycle (`kai/runtime/connections.py`, NEW)

Full lifecycle: initiate → confirm → verify → reconnect → disconnect. Bridges Pipedream connected accounts to IntegrationRegistry entries.

#### Health & Observability (`kai/runtime/connector_health.py`, NEW)

Error classification (auth/scope/rate-limit/transient/etc.), persistent JSONL execution logs per brand, per-integration error history, brand-level health dashboard.

#### Onboarding (`kai/runtime/onboarding.py`, NEW)

Reusable flow: create brand → fill profile → choose archetype → connect systems → verify → audit → action queue. Pre-built checklists for KaiCalls and Starrs Party. Default checklists by archetype (local_service, saas, ecommerce).

#### Gateway Router (`gateway/routers/connections.py`, NEW)

13 endpoints: `/connections/connect`, `/confirm`, `/{id}/verify`, `/{id}/reconnect`, `/{id}/disconnect`, `/status/{brand_id}`, `/verify-all/{brand_id}`, `/health/{brand_id}`, `/sync/{brand_id}`, `/onboarding/checklist`, `/onboarding/status/{brand_id}`, `/webhooks/pipedream/connect`.

#### IntegrationRegistry (`kai/runtime/integrations.py`, UPDATED)

Added: `connected_account_id`, `external_user_id`, `scopes`, `last_verified_at`, `last_sync_at`, `last_error`, `degraded` status. New methods: `mark_verified()`, `mark_degraded()`, `mark_error()`, `mark_synced()`, `get_health_summary()`, `get_scope_summary()`.

#### Legacy Connector Layer (`kai/connectors/`, unchanged)

Still has 26 `NotImplementedError` stubs. These are bypassed when integrations have a `connected_account_id` — Pipedream handles the HTTP transport.

#### Scripts Layer (`scripts/`, unchanged)

| Script | Lines | Real HTTP? |
|--------|-------|-----------|
| `scripts/analytics/google_analytics.py` | 2,026 | Yes — `BetaAnalyticsDataClient` |
| `scripts/ads/facebook_ads.py` | 631 | Yes — `requests` library |
| `scripts/ads/meta_ads_create.py` | 197 | Yes — `requests` to Graph API |
| `scripts/analytics/supabase_analytics.py` | 843 | Yes — Supabase client |
| `scripts/content/engine.py` | ~800 | Yes — LLM calls via Google Gemini |

**The gap is closing:** Pipedream adapter provides real HTTP transport for all connected accounts. The scripts layer still handles non-Pipedream integrations (Supabase, Gemini).

### 6. Creative Generation

**Status: PARTIALLY BUILT — Briefs and templates only, no content production**

| Component | File | What It Does | What It Does NOT Do |
|-----------|------|-------------|-------------------|
| Copy engine | `kai/creative/copy_engine.py` (2,000+ lines) | Generates template dicts with `[Placeholder]` text and framework instructions | Does not call an LLM or produce final prose |
| Brief system | `kai/creative/brief.py` (1,000+ lines) | Creates `CreativeBrief` metadata dicts | Does not produce content |
| QA pipeline | `kai/creative/qa_pipeline.py` (800+ lines) | Rule-based checks (brand voice, claim safety, platform fit) | Does not fix content, only flags violations |
| Asset support | `kai/creative/asset_support.py` | Generates `AssetRequest` specs (dimensions, platform, concept) | Does not produce images or assets |
| Variant engine | `kai/creative/variant_engine.py` | Variant generation framework | Template-based |
| Landing page blocks | `kai/creative/landing_page_blocks.py` | Section templates | All `[Placeholder]` text |

**Example of what copy_engine produces:**
```python
{
    "section_type": "hero",
    "headline": "[Max 10 words, action-oriented] {key_message[:80]}",
    "subheadline": "[Max 20 words, expand headline with specificity]",
    "instructions": {
        "perception_engineering": "Apply Layer 3 (Permission): CTA must feel zero-risk..."
    },
}
```

This is a brief/recipe, not content. The actual content generation happens in `scripts/content/engine.py` which calls Google Gemini.

### 7. Execution Surfaces

**Status: PARTIALLY BUILT**

#### Local Surface (`kai/operator/local_surface.py`)
- Command parser, dispatcher, formatter
- Returns structured `CommandResult` objects
- Lazy data loading from workspace
- Graceful handling of missing subsystems

#### Remote Surface (`kai/operator/remote_surface.py`, `gateway/`)
- FastAPI app with 11+ routers
- SQLite-backed job queue with ThreadPoolExecutor
- Auth via API key dependency injection
- Health check endpoint
- CORS middleware

#### Skill Surface (Claude Code skills)
- 31 `/kai-*` commands exist as Claude Code superpowers skills
- These invoke Claude Code's skill system, NOT the kai/ runtime
- The skills load knowledge base files and framework instructions for the LLM
- They do not call kai/ Python code directly

### 8. Memory / Learning

**Status: BUILT — Real persistence**

| Component | File | Assessment |
|-----------|------|------------|
| Writeback | `kai/memory/writeback.py` | JSONL append-only files per LearningCategory. Atomic writes. |
| Retrieval | `kai/memory/retrieval.py` | Query system for memory lookup |
| Schemas | `kai/memory/schemas.py` | 9 learning categories (brand_preference, creative_performance, channel_insight, audience_insight, offer_performance, compliance_constraint, operator_preference, business_fact, execution_record) |
| Anti-patterns | `kai/memory/anti_patterns.py` | Registry of known failure patterns |
| Runtime memory | `kai/runtime/memory.py` | Memory layout and retrieval interfaces |

### 9. Operator Surfaces

**Status: PARTIALLY BUILT**

| Surface | Status | Notes |
|---------|--------|-------|
| Claude Code skills | Working | 31 commands via superpowers skill system. These work by loading knowledge + framework context for the LLM. |
| Local CLI | Built | `kai/operator/local_surface.py` — command dispatch and formatting |
| Remote API | Built | FastAPI gateway with routers |
| Setup wizard | Built | `kai/packaging/setup.py` — 8-step interactive setup |
| Plugin system | Sketched | `kai/packaging/plugin.py` — defined but not operational |

---

## End-to-End Flows That Are Truly Working

Being strict: only flows that are implemented AND testable.

### Working

1. **Business Profile → Audit → Proposals → Review Bundle**
   - Tested in `test_application_flow.py` (7/7 pass)
   - `BusinessProfile` → `audit_business()` → `build_proposals()` → `ReviewBundle`
   - Real scoring, ranking, bundling in the pipeline

2. **Action Proposal → Approval → Execution Tracking**
   - Tested in `test_actions_integrations.py`
   - `ActionStore.propose_action()` → `.approve_action()` → `.mark_executing()` → `.mark_completed()`
   - State machine enforced, JSON persistence, audit log

3. **Policy/Compliance Check on Content**
   - Tested in `test_policy.py` (72/72 pass)
   - `PolicyEngine.classify_risk()`, `check_banned_words()`, `check_regulated_claims()`
   - Returns violations, warnings, required modifications

4. **Content Pipeline (via scripts/content/)**
   - `engine.py` chains: persona → brief → LLM write → quality gate → approval policy → content log
   - Quality gates: `four_us_score.py`, `banned_word_check.py`, `seo_lint.py`
   - Actually calls Google Gemini for content generation

5. **Run/Artifact Persistence**
   - `RuntimeStore` creates run records, stores artifacts, tracks lineage
   - Atomic writes, thread-safe, queryable

6. **Memory Writeback**
   - `kai/memory/writeback.py` persists learnings as JSONL
   - Categorized by 9 learning types

### Ready But Awaiting Live Credentials

1. **Audit Finding → Approved Action → Live Channel Execution (via Pipedream)**
   - Full code path wired: Audit → Proposal → Approval → ActionExecutor → PipedreamExecutor → Pipedream `actions.run()` → external system
   - Tested with mocked SDK (33 tests passing, all prop translations verified)
   - **Blocked on:** Pipedream credentials + real account connections for KaiCalls and Starrs Party

2. **Connector → Real API Call (via Pipedream)**
   - Pipedream adapter provides HTTP transport for all supported providers
   - ActionExecutor prefers Pipedream path when `connected_account_id` exists
   - **Blocked on:** Same — Pipedream credentials

### NOT Working End-to-End

1. **Skill Command → Runtime → Execution**
   - `/kai-*` skills work via Claude Code but don't invoke kai/ Python runtime
   - They load knowledge files for the LLM, not programmatic execution

2. **Remote Automation / Scheduled Jobs**
   - Gateway job queue works (SQLite, thread pool)
   - But: no scheduled jobs or background automations are configured
   - Module manifests define "remote_automation_pack" but nothing triggers them

3. **Agent Loop / Subagent Orchestration**
   - `agent/` directory has channel agents and LLM integration scaffolding
   - Not operational as an autonomous agent loop

---

## Partially Built Flows

### 1. Connected Channel Operations
**What exists:** Full Pipedream adapter package providing HTTP transport for all supported providers. Connection lifecycle (initiate/confirm/verify/reconnect/disconnect). Health dashboard with error classification. Execution logging. Onboarding checklists for KaiCalls and Starrs Party. 13 gateway endpoints for connection management.
**What's missing:** Live Pipedream credentials and real account connections. Once credentials are configured, the full audit→proposal→approval→execution→verification loop is operational.

### 2. Creative Content Production
**What exists:** Brief schema, template generators for 10+ content types, QA pipeline with rule-based checks, asset request specs.
**What's missing:** LLM integration in the creative module itself. The copy engine produces recipes, not content. Real content generation happens in `scripts/content/engine.py` but isn't routed through `kai/creative/`.

### 3. Watcher/Monitoring System
**What exists:** Watcher framework with `check()` abstract method. 5+ concrete watchers (ad spend/fatigue, lead followup, social freshness, website visibility). Real threshold logic.
**What's missing:** Data feed from connectors. Scheduling infrastructure. Notification delivery.

### 4. Learning Loop Closure
**What exists:** Memory writeback (JSONL persistence). 9 learning categories. Anti-pattern registry.
**What's missing:** Retrieval integration into content/proposal generation. Automatic feedback from execution outcomes. Pattern discovery across sessions.

### 5. Onboarding Flow
**What exists:** 8-step guided setup flow (collect info → profile → archetype → modules → audit → proposals → review → approval).
**What's missing:** Integration with operator surface. Not exposed through any command or API endpoint.

---

## Documentation Drift

### Where docs OVERSTATE the system

1. **README.md** — "Kai is a marketing-native Claude Code clone/fork"
   - Reality: Kai is a marketing data model + audit engine that runs alongside Claude Code. It does not implement its own skill system, subagent orchestration, hooks, memory, or MCP. Those are Claude Code features that Kai benefits from.

2. **README.md** — 31 commands presented as working features
   - Reality: These are Claude Code superpowers skills that load knowledge files. They work, but through Claude Code's skill system, not through kai/ runtime execution.

3. **README.md** — "a canonical runtime/workspace model" + "a gateway that exposes runtime metadata and remote execution surfaces"
   - Reality: Runtime models and gateway exist, but the gateway is mostly router scaffolding. Remote execution is defined but not operational.

4. **Build report** (overnight build) — "85/85 tasks complete"
   - Reality: 85 code files were written, not 85 features completed. Many modules are business-logic complete but integration-incomplete (connectors, creative, watchers).

5. **ARCHITECTURE.md** — "skills, subagents, hooks, memory, MCP, plugins" listed as Kai Runtime features
   - Reality: These are Claude Code primitives that Kai uses. Kai doesn't implement its own version of these.

### Where docs UNDERSTATE the system

1. **Knowledge base depth not surfaced** — 168 files including 12 ad platform policies (7,600+ lines of TOS), 8 personas, 41 playbooks. This is a genuine competitive asset that docs mention but don't emphasize enough.

2. **Audit engine sophistication** — The docs don't explain that audits use real algorithmic scoring with severity penalties, archetype weighting, and multi-location support.

3. **Proposal ranking** — 5-factor weighted scoring with dependency resolution and capacity pruning is non-trivial and not well documented.

4. **Compliance engine** — 100+ rules with regex pattern matching and dynamic dispatch. This is real IP, barely mentioned.

### What needs correction

1. README should distinguish between "works via Claude Code skills" and "works via kai/ runtime"
2. README should add implementation status markers (Built / Partial / Planned) to the command table
3. ARCHITECTURE.md should clarify that the "Runtime" layer refers to kai/ data models and persistence, not a full Claude Code-style runtime implementation
4. Build overview should note that connectors and creative are business-logic complete but integration-incomplete

---

## What Kai Can Do Now

1. Load a business profile with archetype detection and overlay inference
2. Run 8 audit categories against a business profile and produce scored findings
3. Rank audit findings into prioritized action proposals with dependency resolution
4. Bundle proposals into time-phased plans (7-day quick wins, 30-day plans, campaign packs)
5. Route proposals through risk-based approval workflows
6. Track action lifecycle (propose → approve → execute → complete) with persistence
7. Check content against 100+ compliance rules across 5 policy packs
8. Detect banned words, regulated claims, and personal attribute violations
9. Persist learnings as categorized JSONL memory files
10. Generate content via LLM with quality gates (through scripts/content/, not kai/creative/)
11. Provide 31 Claude Code skills for interactive marketing work (knowledge-driven, not runtime-driven)
12. Expose runtime state via FastAPI gateway

## What Kai Cannot Do Yet

1. Execute actions against live channels (no connector HTTP transport)
2. Generate content within the kai/ creative module (produces templates, not prose)
3. Run autonomous monitoring/watchers (framework exists, data feeds missing)
4. Close the learning loop (writeback works, retrieval not integrated)
5. Run as an autonomous agent (agent loop sketched, not operational)
6. Schedule background automations (defined in module manifests, not triggered)
7. Route skill commands through kai/ Python runtime (skills use Claude Code, not kai/)

## What Should Happen Next

**Priority 1 — Wire connectors to scripts layer**
The scripts/ layer already makes real API calls (GA4, Meta Ads, Facebook, Supabase). The kai/connectors/ layer has the business logic. Connect them so the connector interface can delegate to real HTTP clients.

**Priority 2 — Close the audit-to-execution loop**
The chain works from profile → audit → proposals → approval. Add execution dispatch so an approved action can call a connector and complete the loop.

**Priority 3 — Wire creative module to LLM**
`scripts/content/engine.py` already calls Google Gemini. Route that through `kai/creative/copy_engine.py` so the creative module produces actual content instead of templates.

**Priority 4 — Activate watchers**
Watcher logic is real (ad fatigue thresholds, spend anomaly detection). Connect to data feeds from connectors and add scheduling.

**Priority 5 — Integrate memory retrieval**
Writeback works. Add retrieval into proposal ranking and content generation so the system learns from past runs.
