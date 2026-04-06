# Agent Task Manifest — Complete System Build

**Generated:** 2026-04-02  
**Source:** `docs/superpowers/specs/2026-04-02-complete-system-task-map.md`  
**Purpose:** Each file below is a self-contained agent task brief. Loop agents overnight to execute sequentially or in dependency-safe parallel batches.

---

## How to Use

1. Pick a task file from the list below
2. Feed it to an agent as the full prompt
3. The agent reads the brief, reads referenced files, and produces the output
4. Mark status as `done` when complete

**Dependency rule:** Tasks with `depends_on` should not start until their dependencies are marked done. Tasks with no dependencies can run in any order.

---

## Task Index

### Workstream 1: Workspace and Business Understanding

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 001 | `task-001-business-profile-schema.md` | Define canonical BusinessProfile schema | — | Large |
| 002 | `task-002-profile-loaders.md` | Build profile loaders (onboarding, brand config, overrides) | 001 | Medium |
| 003 | `task-003-normalization-layer.md` | Build normalization layer (channels, locations, metadata) | 001 | Medium |
| 004 | `task-004-profile-validation.md` | Build profile validation and unknowns-preserved behavior | 001 | Medium |
| 005 | `task-005-workspace-state-model.md` | Build connected workspace state model | 001 | Medium |

### Workstream 2: Archetypes and Module System

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 006 | `task-006-local-service-archetype.md` | Define local-service archetype (full spec) | 001 | Large |
| 007 | `task-007-ecommerce-archetype.md` | Define ecommerce archetype (full spec) | 001 | Large |
| 008 | `task-008-professional-services-archetype.md` | Define professional-services archetype (full spec) | 001 | Large |
| 009 | `task-009-multi-location-archetype.md` | Define multi-location archetype (full spec) | 001 | Large |
| 010 | `task-010-overlay-system.md` | Build overlay system (healthcare, creator, franchise, SaaS) | 006, 007, 008, 009 | Large |
| 011 | `task-011-module-activation-logic.md` | Build module activation logic from business profile | 001, 010 | Medium |
| 012 | `task-012-archetype-fixtures.md` | Build per-archetype fixtures and golden examples | 006, 007, 008, 009 | Medium |

### Workstream 3: Audit and Diagnosis

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 013 | `task-013-audit-data-models.md` | Define audit data models (AuditFinding, AuditResult, scorecards) | 001 | Large |
| 014 | `task-014-website-conversion-audit.md` | Build website conversion audit engine | 013 | Medium |
| 015 | `task-015-trust-proof-audit.md` | Build trust and proof audit engine | 013 | Medium |
| 016 | `task-016-local-seo-audit.md` | Build local SEO and visibility audit engine | 013 | Medium |
| 017 | `task-017-review-reputation-audit.md` | Build review and reputation audit engine | 013 | Medium |
| 018 | `task-018-lifecycle-followup-audit.md` | Build lifecycle and follow-up audit engine | 013 | Medium |
| 019 | `task-019-creative-readiness-audit.md` | Build creative and asset readiness audit | 013 | Medium |
| 020 | `task-020-paid-media-readiness-audit.md` | Build paid media readiness audit | 013 | Medium |
| 021 | `task-021-crm-data-hygiene-audit.md` | Build CRM and data hygiene audit | 013 | Medium |

### Workstream 4: Proposal and Planning

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 022 | `022-proposed-action-schema.md` | Define ProposedAction schema and generation rules | 013 | Large |
| 023 | `023-finding-to-action-mapping.md` | Build finding-to-action mapping engine | 022 | Large |
| 024 | `024-proposal-bundling.md` | Build proposal bundling (7-day, 30-day, campaign, monthly) | 022 | Medium |
| 025 | `025-proposal-ranking.md` | Build proposal ranking, dedup, and dependency tracking | 022 | Medium |
| 026 | `026-capacity-aware-pruning.md` | Build capacity-aware pruning and action mode selection | 022, 005 | Medium |

### Workstream 5: Creative and Asset Generation

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 027 | `027-creative-brief-system.md` | Build creative brief system from proposals | 022 | Medium |
| 028 | `028-copy-generation-engine.md` | Build copy generation engine (web, landing, ads, social, email, scripts) | 027 | Large |
| 029 | `029-creative-asset-support.md` | Build creative asset support (images, layouts, graphics, video briefs) | 027 | Large |
| 030 | `030-content-inventory.md` | Build content inventory and asset awareness system | 001 | Medium |
| 031 | `031-creative-qa-pipeline.md` | Build creative QA pipeline (brand voice, claim safety, platform fit) | 028 | Medium |
| 032 | `032-reusable-libraries.md` | Build reusable libraries (CTAs, offers, approved message blocks) | 001 | Medium |

### Workstream 6: Website Operations

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 033 | `033-cms-connector-layer.md` | Build CMS connector layer (WordPress, Webflow, Shopify) | — | Large |
| 034 | `034-website-action-system.md` | Build website action system (update_page_copy, update_cta, etc.) | 033 | Large |
| 035 | `035-page-diff-approval.md` | Build page diff preview and approval workflow | 034 | Medium |
| 036 | `036-rollback-page-health.md` | Build rollback support and page health monitoring | 034 | Medium |
| 037 | `037-local-service-page-types.md` | Build local-service page type builders | 034, 006 | Large |
| 038 | `038-onpage-seo-schema.md` | Build on-page SEO, schema markup, and trust-block generation | 034 | Medium |

### Workstream 7: Social Operations

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 039 | `039-social-platform-connectors.md` | Build social platform connectors (FB, IG, LinkedIn, TikTok, YT) | — | Large |
| 040 | `040-social-content-types.md` | Build social content type system and format rules | 039 | Medium |
| 041 | `041-social-scheduling-queue.md` | Build social scheduling, queue, and approval management | 039 | Medium |
| 042 | `042-caption-hashtag-generation.md` | Build caption, hashtag, and geo-tag generation | 040 | Small |
| 043 | `043-proof-of-life-automation.md` | Build proof-of-life automation and filler suppression | 040, 041 | Medium |

### Workstream 8: Paid Media Operations

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 044 | `044-ad-platform-connectors.md` | Build ad platform connectors (Google Ads, Meta Ads, LSA) | — | Large |
| 045 | `045-paid-media-action-system.md` | Build paid media action system (create, adjust, pause, launch) | 044 | Large |
| 046 | `046-campaign-adgroup-schema.md` | Build campaign and ad group schema | 044 | Medium |
| 047 | `047-budget-risk-controls.md` | Build budget and risk controls with readiness checks | 046 | Medium |
| 048 | `048-creative-variant-workflow.md` | Build creative variant workflow and inventory tracking | 046, 029 | Medium |
| 049 | `049-fatigue-spend-anomaly.md` | Build fatigue detection and spend anomaly monitoring | 046 | Medium |

### Workstream 9: Lifecycle / CRM / Follow-Up

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 050 | `050-crm-email-sms-connectors.md` | Build email/SMS/CRM connector layer | — | Large |
| 051 | `051-lifecycle-action-system.md` | Build lifecycle action system (sequences, reminders, reviews, referrals) | 050 | Large |
| 052 | `052-contact-segment-models.md` | Build contact and segment models | 050, 001 | Medium |
| 053 | `053-sequence-templates-archetype.md` | Build sequence templates by archetype | 051, 006, 007, 008, 009 | Large |
| 054 | `054-followup-timing-deliverability.md` | Build follow-up timing rules and deliverability controls | 051 | Medium |
| 055 | `055-specific-sequence-builders.md` | Build specific sequences (post-job, dormant, quote, referral, reorder) | 051 | Large |

### Workstream 10: Analytics, Attribution, Monitoring

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 056 | `056-analytics-connector-layer.md` | Build analytics connectors (GA4, GSC, ad platforms, call tracking, GBP) | — | Large |
| 057 | `057-kpi-models-archetype.md` | Build KPI models per archetype | 056, 006, 007, 008, 009 | Medium |
| 058 | `058-attribution-outcome-linkage.md` | Build attribution snapshots and action-to-outcome linkage | 056, 022 | Large |
| 059 | `059-anomaly-detection.md` | Build anomaly detection and confidence scoring | 056 | Medium |
| 060 | `060-scorecards-dashboards.md` | Build scorecards and dashboard summary objects | 057 | Medium |

### Workstream 11: Approval, Compliance, Policy

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 061 | `061-policy-pack-expansion.md` | Expand policy packs (website, social, paid, email, analytics) | — | Large |
| 062 | `062-platform-compliance-engine.md` | Build platform-specific compliance rule engine | 061 | Large |
| 063 | `063-brand-constraints-regulated.md` | Build brand-specific constraints and regulated-claims handling | 061, 001 | Medium |
| 064 | `064-approval-routing.md` | Build approval routing by risk tier | 022 | Medium |
| 065 | `065-revision-kill-switches.md` | Build revision workflows and kill switches | 064 | Medium |
| 066 | `066-immutable-audit-trail.md` | Build immutable audit trail | 064 | Medium |

### Workstream 12: Background Automation

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 067 | `067-watcher-framework.md` | Build watcher framework core | 013, 022 | Large |
| 068 | `068-watchers-website-visibility.md` | Build website health and local visibility watchers | 067 | Medium |
| 069 | `069-watchers-social-freshness.md` | Build social staleness and content freshness watchers | 067 | Medium |
| 070 | `070-watchers-ad-spend.md` | Build ad fatigue and spend anomaly watchers | 067 | Medium |
| 071 | `071-watchers-lead-followup.md` | Build lead response and follow-up gap watchers | 067 | Medium |
| 072 | `072-watcher-scheduling-throttle.md` | Build watcher scheduling, throttling, and notification system | 067 | Medium |

### Workstream 13: Memory and Learning

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 073 | `073-memory-writeback.md` | Build memory writeback system from actions and results | 022 | Large |
| 074 | `074-memory-layer-schemas.md` | Build memory layer schemas (business, brand, proof, channel, offer, audience) | 073, 001 | Medium |
| 075 | `075-memory-retrieval.md` | Build memory retrieval for proposals and creative generation | 074 | Medium |
| 076 | `076-anti-pattern-learning.md` | Build anti-pattern memory and archetype default improvement | 074 | Medium |

### Workstream 14: Operator Surfaces

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 077 | `077-local-operator-surfaces.md` | Build local operator surfaces (skills, review-flow, audit-flow) | 013, 022 | Large |
| 078 | `078-remote-operator-surfaces.md` | Build remote operator surfaces (API routes, dashboard, proposal queue) | 022 | Large |
| 079 | `079-first-class-flows.md` | Build first-class flows (onboarding, audit, approve/reject/revise) | 077, 078 | Large |
| 080 | `080-execution-monitoring.md` | Build execution monitoring and action history | 078 | Medium |
| 081 | `081-packaging-install.md` | Build packaging, install, and setup system | 079 | Large |

### Cross-Cutting: Creative System

| ID | File | Title | Depends On | Complexity |
|----|------|-------|------------|------------|
| 082 | `082-messaging-frameworks-archetype.md` | Build messaging frameworks by archetype | 006, 007, 008, 009 | Large |
| 083 | `083-trust-proof-templates.md` | Build trust/proof block templates and review rendering | 001 | Medium |
| 084 | `084-ad-creative-variant-logic.md` | Build ad creative variant logic and cross-channel adaptation | 028, 029 | Large |
| 085 | `085-landing-page-blocks.md` | Build landing page block generation and visual request workflow | 028, 034 | Large |

---

## Dependency Graph — Parallel Execution Waves

### Wave 1 (No dependencies — can all run in parallel)
001, 033, 039, 044, 050, 056, 061

### Wave 2 (Depends only on Wave 1)
002, 003, 004, 005, 006, 007, 008, 009, 013, 030, 032, 034, 040, 041, 045, 046, 051, 052, 057, 059, 062, 063, 064, 083

### Wave 3 (Depends on Wave 2)
010, 012, 014, 015, 016, 017, 018, 019, 020, 021, 022, 035, 036, 037, 038, 042, 043, 047, 048, 049, 053, 054, 055, 058, 060, 065, 066, 067, 073, 077, 078, 082

### Wave 4 (Depends on Wave 3)
011, 023, 024, 025, 026, 027, 028, 029, 031, 068, 069, 070, 071, 072, 074, 079, 080, 084, 085

### Wave 5 (Depends on Wave 4)
076, 075, 081

---

## Status Tracking

Mark each task as you complete it:
- `[ ]` = pending
- `[~]` = in progress  
- `[x]` = done
- `[!]` = blocked

All 85 tasks currently: `[ ]` pending
