# Complete System Task Map

**Date:** 2026-04-02  
**Status:** Master build map  
**Goal:** Define all major work needed to turn this harness into a complete marketing operating system that can operate for any business across the core channels.

---

## What "Complete System" Means

The system is complete when an operator can:

1. onboard any real business into a connected workspace
2. understand that business in a structured way
3. run audits and diagnose the highest-leverage opportunities
4. generate small compounding actions and campaigns across channels
5. create the necessary creative and messaging assets
6. hold, approve, revise, and execute actions safely
7. run low-risk operations in the background
8. measure outcomes and write learnings back into memory
9. repeat that loop continuously

This is not just a runtime. This is:

- business understanding
- decisioning
- creative production
- compliant execution
- measurement
- learning

---

## Build Principles

- The product is application-first, not runtime-first.
- Use runtime primitives where they help, but do not confuse primitives with the product.
- Prefer compounding small actions over giant one-shot campaign plans.
- Every channel should support the same operating loop:
  - observe
  - diagnose
  - propose
  - create
  - gate
  - execute
  - verify
  - learn
- "Any business" does not mean generic mush. It means:
  - one shared system
  - one common contract layer
  - archetype-specific overlays and channel defaults

---

## System Workstreams

The full system breaks into 14 workstreams.

1. Workspace and business understanding
2. Archetypes and module system
3. Audit and diagnosis
4. Proposal and planning
5. Creative and asset generation
6. Website operations
7. Social operations
8. Paid media operations
9. Lifecycle / CRM / follow-up operations
10. Analytics, attribution, and monitoring
11. Approval, compliance, and policy control
12. Background automation and watcher loops
13. Memory and learning loop
14. Operator surfaces, packaging, and delivery

---

## 1. Workspace and Business Understanding

### Goal

Represent any business in a way the system can reason about and operate on.

### Tasks

- Define canonical `BusinessProfile` fields for:
  - identity
  - offers
  - pricing
  - geography
  - personas / ICP
  - trust signals
  - goals / KPIs
  - channel presence
  - constraints
  - budget and risk
- Build profile loaders from:
  - onboarding notes
  - runtime brand config
  - operator overrides
  - future forms / UI onboarding
- Build normalization for:
  - channels
  - state/location names
  - business metadata
  - offer naming
- Build profile validation rules
- Build "unknowns preserved" behavior so missing facts are not hallucinated
- Build per-business fixtures and calibration examples
- Build connected workspace state:
  - connected integrations
  - permissions
  - budget constraints
  - approval defaults
  - channel enablement

### Subtasks

- add industry and business-model fields
- add stage fields: startup / early PMF / scaling / mature
- add buyer and sales-cycle complexity fields
- add service-area and multi-location structure
- add brand-voice and compliance notes
- add operator-capacity constraints

---

## 2. Archetypes and Module System

### Goal

Make the system useful across business types without flattening everything into a generic workflow.

### Tasks

- Ship first-class archetypes:
  - local-service
  - ecommerce
  - professional-services
  - multi-location
- Build overlay support for:
  - healthcare / regulated
  - creator / personal brand
  - franchise / location fleet
  - SaaS / software
- Define per-archetype:
  - audit categories
  - priority defaults
  - KPI schema
  - channel mix
  - action families
  - compliance sensitivities
  - creative formats
- Build module activation logic from business profile
- Build per-archetype fixtures and golden examples

### Subtasks

- define minimum viable channel set per archetype
- define budget heuristics per archetype and stage
- define recurring automation packs per archetype
- define review / referral / local visibility logic for local-service
- define PDP / offer / retention logic for ecommerce
- define authority / proof / nurture logic for professional-services
- define location consistency / GBP fleet logic for multi-location

---

## 3. Audit and Diagnosis

### Goal

Turn business context and live channel state into structured findings and priorities.

### Tasks

- Build audit engines per archetype
- Standardize:
  - `AuditFinding`
  - `AuditResult`
  - category scorecards
  - evidence structures
  - severity and priority rules
- Add static audits:
  - based on business profile and onboarding data
- Add connected audits:
  - based on live channel and analytics data
- Add business-stage-aware scoring
- Add "missing data" findings without breaking the flow
- Add "why this matters" reasoning for operators

### Subtasks

- website conversion audit
- trust / proof audit
- local SEO / visibility audit
- review / reputation audit
- lifecycle / follow-up audit
- creative / asset readiness audit
- paid-media readiness audit
- CRM / data hygiene audit

---

## 4. Proposal and Planning

### Goal

Convert findings into a prioritized action system instead of vague recommendations.

### Tasks

- Standardize `ProposedAction`
- Build proposal generation rules from findings
- Map findings to:
  - website actions
  - social actions
  - paid media actions
  - lifecycle actions
  - analytics fixes
  - reputation actions
- Add:
  - reason
  - business impact
  - expected outcome
  - risk tier
  - approval requirement
  - suggested payload
  - source finding linkage
- Add proposal bundling:
  - 7-day actions
  - 30-day plan
  - campaign pack
  - monthly operating plan

### Subtasks

- proposal deduping
- proposal ranking beyond severity
- dependency tracking between actions
- opportunity cost / capacity-aware pruning
- "small compounding action" mode vs "campaign burst" mode

---

## 5. Creative and Asset Generation

### Goal

Produce the creative and copy assets required to execute proposals and campaigns.

### Tasks

- Build a creative brief system from proposals
- Build copy generation for:
  - web sections
  - landing pages
  - ads
  - social posts
  - email sequences
  - scripts / call prompts
- Build creative asset support for:
  - static image concepts
  - before/after layouts
  - testimonial graphics
  - local offer graphics
  - ad creative variants
  - short video / reel briefs
- Build content inventory awareness:
  - existing photos
  - testimonials
  - logos
  - brand assets
  - approved messaging blocks
- Build creative QA:
  - brand voice
  - claim safety
  - platform fit
  - offer/message consistency

### Subtasks

- creative request schema
- asset storage and references
- approved message block library
- reusable offer and CTA library
- variant generation rules
- cross-channel adaptation logic

---

## 6. Website Operations

### Goal

Operate websites as a live conversion surface, not just a content output.

### Tasks

- Connect CMS/platforms:
  - WordPress
  - Webflow
  - Shopify
  - custom/static sites where feasible
- Support website actions:
  - `update_page_copy`
  - `update_page_section`
  - `update_cta`
  - `update_metadata`
  - `fix_tracking`
  - `refresh_approved_section`
  - `restructure_page`
- Build page diff previews
- Build page-level approval workflow
- Build rollback support where possible
- Build page health and conversion monitoring
- Build local-service page types:
  - homepage
  - service pages
  - service-area pages
  - quote/contact pages

### Subtasks

- page schema and section targeting
- CTA placement logic
- trust-block generation
- schema markup and local markup support
- on-page SEO updates
- form and call CTA validation

---

## 7. Social Operations

### Goal

Run social as a proof, distribution, and demand-support channel.

### Tasks

- Connect:
  - Facebook
  - Instagram
  - LinkedIn
  - TikTok
  - YouTube Shorts where relevant
- Support social actions:
  - `schedule_social_post`
  - `publish_social_post`
  - `publish_approved_variant`
  - repurposing tasks
- Build social content types:
  - proof posts
  - before/after
  - local tips
  - offer posts
  - testimonial posts
  - behind-the-scenes
- Build scheduling logic
- Build asset adaptation logic
- Build frequency caps and compliance checks
- Build proof-of-life automation for low-volume brands

### Subtasks

- channel-specific format rules
- caption generation
- hashtag / geo tag support
- post queue management
- approval queue for posts
- suppression of low-value filler content

---

## 8. Paid Media Operations

### Goal

Operate bounded, measurable acquisition loops rather than ad-hoc campaign creation.

### Tasks

- Connect:
  - Google Ads
  - Meta Ads
  - Local Services Ads where relevant
  - future optional channels
- Support paid-media actions:
  - `create_ad_creative`
  - `adjust_bidding`
  - `adjust_budget`
  - `pause_campaign`
  - `launch_campaign`
  - `publish_approved_variant`
- Build readiness checks before launch
- Build budget and risk controls
- Build creative variant workflows
- Build landing-page / ad-message alignment checks
- Build fatigue and underperformance detection

### Subtasks

- campaign schema
- ad group / audience schema
- negative keyword and exclusions support
- creative inventory tracking
- spend anomaly detection
- bounded test budget logic
- geo and service-area targeting helpers

---

## 9. Lifecycle / CRM / Follow-Up Operations

### Goal

Turn customers and leads into repeat business, reviews, referrals, and higher LTV.

### Tasks

- Connect:
  - email providers
  - SMS / texting providers where relevant
  - CRM / spreadsheets / lightweight contact stores
- Support lifecycle actions:
  - `launch_email_sequence`
  - `update_nurture_copy`
  - reminder sequences
  - review request sequences
  - referral asks
  - repeat service reactivation
- Build contact and segment models
- Build sequence templates by archetype
- Build follow-up timing rules
- Build deliverability and opt-out controls

### Subtasks

- post-job review sequence
- quarterly repeat reminder
- dormant lead follow-up
- quote follow-up
- referral engine
- maintenance / reorder / reorder-likely cadence

---

## 10. Analytics, Attribution, and Monitoring

### Goal

Measure what happened so the system can choose better next actions.

### Tasks

- Connect:
  - GA4
  - GSC
  - ad platform metrics
  - CRM / lead sources
  - call tracking
  - GBP metrics where available
- Build KPI models per archetype
- Build attribution snapshots
- Build anomaly detection
- Build action-to-outcome linkage
- Build scorecards for:
  - visibility
  - lead flow
  - conversion
  - repeat business
  - spend efficiency

### Subtasks

- metric normalization
- per-channel rollups
- action lineage to results
- dashboard summary objects
- confidence scoring for observed changes

---

## 11. Approval, Compliance, and Policy Control

### Goal

Ensure the system can act safely and compliantly across channels.

### Tasks

- Expand policy packs for:
  - website
  - social
  - paid media
  - email
  - analytics changes
- Build platform-specific compliance rules
- Build brand-specific constraints
- Build regulated-claims handling
- Build approval routing by risk tier
- Build revision workflows
- Build kill switches and operator overrides

### Subtasks

- legal / medical / financial claims packs
- spend cap enforcement
- frequency caps
- approval bundles
- diff + preview generation
- rollback / revert references
- immutable audit trail

---

## 12. Background Automation and Watcher Loops

### Goal

Continuously find small opportunities and problems without waiting for a human to ask.

### Tasks

- Build watcher framework
- Build watcher types for:
  - website health
  - local visibility
  - review velocity
  - social staleness
  - ad fatigue
  - spend anomalies
  - lead response gaps
  - follow-up gaps
  - content / proof freshness
- Build watcher outputs:
  - finding
  - proposal
  - urgency
  - auto-eligible flag
- Build scheduling and throttling
- Build operator notifications

### Subtasks

- daily watchers
- weekly watchers
- event-driven watchers
- archetype-specific watcher packs
- suppression / dedup logic
- recurring proposal generation

---

## 13. Memory and Learning Loop

### Goal

Compound knowledge from work that was approved and from actions that actually performed.

### Tasks

- Build structured memory writeback from:
  - approved actions
  - completed actions
  - campaign results
  - winning creative
  - winning offers
  - high-performing CTAs
- Build memory layers for:
  - business facts
  - brand constraints
  - proof assets
  - channel learnings
  - offer learnings
  - audience learnings
- Build memory update approval rules
- Build retrieval logic for future proposals and creative generation

### Subtasks

- memory schema for explicit learnings
- asset and proof references
- performance-linked learnings
- anti-pattern memory
- archetype defaults that improve over time

---

## 14. Operator Surfaces, Packaging, and Delivery

### Goal

Make the whole system operable by a human, not just programmatically present in the repo.

### Tasks

- Build local operator surfaces:
  - skills / commands
  - review-flow entry points
  - audit-flow entry points
- Build remote operator surfaces:
  - API routes
  - dashboard / overview responses
  - proposal queue
  - action history
- Build first-class flows:
  - onboarding
  - audit review
  - proposal review
  - approve / reject / revise
  - execution monitoring
  - learning review
- Package the system as a productized Claude Code-style clone / plugin bundle

### Subtasks

- one-click review bundle generation
- client / brand selection
- action queue filtering
- operator notifications
- runbook docs
- install / packaging / setup

---

## Cross-Cutting Creative Work

Creative is not a separate toy subsystem. It cuts across website, social, ads, and lifecycle.

Someone has to build:

- messaging frameworks by archetype
- offer messaging blocks
- CTA libraries
- trust / proof block templates
- before/after creative templates
- ad creative variant logic
- short-form post formats
- review/testimonial rendering patterns
- landing-page block generation
- image / visual asset request workflow
- creative approval loop
- asset inventory and reuse logic

Without this, the system will propose actions but not produce execution-ready assets.

---

## Minimum Channel Coverage for "Any Business"

To genuinely support "any business," the system must at minimum handle:

- website / landing pages
- local profile surfaces like GBP where relevant
- social publishing
- paid media
- email / lifecycle
- CRM / contact follow-up
- analytics / attribution
- reviews / reputation
- calls / speed-to-lead

Not every business uses all channels, but the system must know:

- which channels matter
- which are missing
- which should be activated next

---

## Sequencing: What To Build First

Do not try to finish everything at once.

### Phase 1: One complete archetype

Ship `local-service` end to end:

- business profile
- audit
- proposals
- review bundle
- one website execution path
- one social execution path
- one follow-up execution path
- one watcher loop
- memory writeback

### Phase 2: Make the loop real

Add:

- live integrations
- approvals from operator surface
- one real low-risk auto-execution path
- result monitoring
- action history and learning loop

### Phase 3: Port the pattern

Port the same system to:

- ecommerce
- professional-services
- multi-location

### Phase 4: Depth and scale

Add:

- richer creative system
- richer paid-media control
- richer lifecycle logic
- more watchers
- more memory and benchmarking

---

## Definition of Done

This harness becomes a complete system when:

1. A real business can be onboarded into a connected workspace.
2. The system can diagnose it and generate a review bundle.
3. The system can generate typed actions across the major channels.
4. The system can create the necessary copy and creative assets for those actions.
5. The operator can approve, reject, or revise those actions.
6. The system can execute low-risk actions and queue higher-risk ones.
7. Outcomes are measured and linked back to the originating actions.
8. Learnings persist and improve future decisions.
9. The same pattern works across multiple archetypes, not just one demo client.

---

## Immediate Meta-Task

For every new feature added to the harness, ask:

- Does this improve the operator loop?
- Does this help the system understand, propose, create, execute, or learn?
- Does this make one archetype more complete?
- Does this reduce manual stitching between subsystems?

If not, it is probably not part of the shortest path to the complete system.
