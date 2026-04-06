# Connected Marketing Ops Plan

**Date:** 2026-04-02  
**Status:** Active plan  
**Goal:** Re-center Kai on the actual application: operating connected marketing channels in the background, safely and compliantly.

---

## Product Goal

Kai should not stop at generating plans, briefs, or drafts.

Kai should become a **connected marketing operating system** that can:

- observe live business and channel state
- propose changes across websites, socials, ads, email, and CRM
- enforce policy and compliance before execution
- run approved low-risk work in the background
- hold medium and high-risk work for approval
- track outcomes and compound learnings

This is the application layer the runtime is supposed to serve.

---

## Problem

Right now the repo is strongest at:

- promptable workflows
- content generation
- quality scoring
- remote job scaffolding
- knowledge and archetype logic

But a real marketing operating system has to close the loop:

- from recommendation to action
- from action to compliant execution
- from execution to observed performance
- from performance to future decisions

Without that, Kai remains a capable planning and generation tool instead of an operating system.

---

## Product Thesis

The next major application step is:

**Connected workspace -> continuous observation -> proposed actions -> policy gating -> execution -> monitoring -> learning**

That loop should work across:

- websites
- socials
- ad platforms
- email/CRM
- analytics and search data

---

## Core Application Surfaces

### 1. Connected Workspace

Each business needs a real operating context, not just a config entry.

The connected workspace should include:

- brand identity
- offers and proof points
- ICP/personas
- active channels
- connected tools and credentials
- risk policy defaults
- approval defaults
- budget and spend constraints
- compliance constraints
- publishing permissions

### 2. Operator Command Center

The operator should be able to do a small set of powerful things:

- connect or inspect channel integrations
- review proposals waiting for approval
- approve, reject, revise, or auto-authorize classes of actions
- see what changed across channels
- see what background automations executed
- see performance deltas and recommended next actions

### 3. Channel Ops Layer

Kai should treat channel operations as first-class product capabilities:

- website ops
- social ops
- paid media ops
- lifecycle ops
- analytics ops

Each channel should support:

- observe
- propose
- gate
- execute
- verify

---

## Canonical Action Model

Every background mutation should be represented as a typed action.

Examples:

- `update_page_copy`
- `update_page_section`
- `publish_blog_post`
- `publish_social_post`
- `schedule_social_post`
- `create_ad_creative`
- `pause_ad`
- `adjust_budget`
- `launch_email_sequence`
- `update_cta`
- `fix_tracking`

Each action should include:

- `action_id`
- `brand_id`
- `channel`
- `action_type`
- `intent`
- `proposed_changes`
- `source_run_id`
- `risk_tier`
- `policy_result`
- `approval_state`
- `execution_state`
- `rollback_reference`
- `result_summary`

This should become the application-level contract for channel execution.

---

## Compliance and Safety Model

Kai should not mutate live surfaces based only on “the model thought it was a good idea.”

Every action should pass through channel-specific policy.

### Policy dimensions

- brand voice and business constraints
- channel/platform policy
- legal and regulated-claims rules
- budget limits
- account-scoped permissions
- content risk
- landing-page risk
- spend-change risk
- frequency and rate limits

### Risk tiers

#### Tier 1: Low risk

Safe to auto-execute when explicitly enabled.

Examples:

- schedule already-approved social content
- publish low-risk variants from approved inventory
- fix known metadata or broken internal links
- refresh non-claim website sections with approved messaging blocks

#### Tier 2: Medium risk

Hold for approval by default.

Examples:

- update visible landing page copy
- launch new ad creative
- change bidding strategy within bounded constraints
- update nurture copy

#### Tier 3: High risk

Require explicit approval every time.

Examples:

- increase spend beyond threshold
- pause major campaigns
- change pricing or offer language
- edit regulated claims
- push structural website changes

### Mandatory controls

- immutable action log
- proposal preview before execution
- diff view for website changes
- budget and spend guardrails
- scoped credentials
- kill switch per channel
- rollback where the integration allows it
- policy trace attached to each action

---

## Background Automation Model

Kai should run persistent background watchers that observe business state and generate actions.

### Watcher categories

#### Website watchers

- broken pages or forms
- stale pages
- low-conversion pages
- tracking drift
- ranking drops tied to key pages

#### Social watchers

- posting gaps
- campaign cadence misses
- creative fatigue
- engagement drop-offs
- missing repurposing opportunities

#### Paid media watchers

- CPA drift
- CTR drop
- creative fatigue
- audience saturation
- spend anomalies
- landing page mismatch

#### Lifecycle watchers

- lead follow-up gaps
- abandoned flows
- underperforming nurture sequences
- missing segmentation opportunities

#### Analytics watchers

- traffic anomalies
- conversion shifts
- source/medium deterioration
- local SEO declines
- call volume or lead quality shifts

### Watcher output

A watcher should not directly “do things” by default.

A watcher should emit:

- finding
- recommendation
- proposed action bundle
- risk tier
- policy result
- auto-execute eligibility

---

## First Connected Channels

Do not attempt every integration at once.

The first application slice should support 3 mutation surfaces and 3 read surfaces.

### First mutation surfaces

1. Website content updates
2. Social scheduling and publishing
3. Ad creative and bounded budget adjustments

### First read surfaces

1. Analytics and search
2. Social/account state
3. Ad account performance

This is enough to prove the operating loop.

---

## Archetype Strategy

Connected channel behavior should be archetype-aware.

### Local service

Prioritize:

- service pages
- GBP/local visibility
- lead-form and call conversion
- review and reputation prompts
- local offer and location consistency

### Ecommerce

Prioritize:

- PDP and landing page updates
- creative iteration
- retention and lifecycle actions
- merchandising and offer cadence
- paid media and catalog performance

### Professional services

Prioritize:

- authority and trust pages
- case-study and proof distribution
- consult-intake conversion
- nurture sequences
- thought-leadership repurposing

### Multi-location

Prioritize:

- location page consistency
- GBP and local content fleet ops
- location-level reporting
- localized promotions and coverage checks

---

## Phase Plan

## Phase A: Connected workspace and proposal system

Build:

- connected workspace model
- integration registry
- action proposal schema
- approval queue
- operator review surface

Definition of done:

- a brand can connect channels and receive structured proposed actions with risk and policy metadata

## Phase B: Controlled execution for 3 channel types

Build:

- website update execution
- social schedule/publish execution
- ad creative and bounded budget execution

Definition of done:

- Kai can safely execute approved actions against live channel integrations with auditability

## Phase C: Watchers and compounding loop

Build:

- background watchers
- anomaly and opportunity detection
- auto-execution for approved low-risk actions
- performance-linked recommendations

Definition of done:

- Kai can continuously observe channel state, surface actions, execute safe ones, and show what happened

---

## Acceptance Criteria

This plan is succeeding when:

1. A business can connect its website, socials, ads, and analytics into one workspace.
2. Kai can propose real cross-channel actions instead of only generating content.
3. Each action includes compliance and risk metadata before execution.
4. Low-risk actions can run automatically when enabled.
5. Medium and high-risk actions wait in an approval queue.
6. Executed actions are observable, attributable, and reversible where possible.
7. Results feed back into future recommendations and defaults.

---

## Non-Drift Rules

Before building anything in this area, ask:

1. Does this help Kai operate a connected business, or is it just more infrastructure?
2. Does this move the system from outputs toward actions?
3. Does this improve compliant execution?
4. Does this improve the operator’s ability to supervise background work?
5. Does this strengthen one real business archetype end to end?

If not, it is probably not part of the next application phase.

---

## Immediate Next Build Slice

The best first application slice is:

**Local service connected ops**

Build this loop:

1. connect analytics, website, and social
2. run business audit
3. generate proposed website/social/ad actions
4. gate them by risk and policy
5. approve or auto-run low-risk changes
6. track outcomes

Why this slice:

- it matches existing repo strengths
- it aligns with current archetype work
- it is operationally concrete
- it forces the product to become an actual operator system

---

## Relationship to the Runtime Plan

The runtime plan still matters, but only as support infrastructure.

This application plan is the higher-order product direction:

- runtime exists to support connected channel operations
- approval exists to supervise real actions
- background jobs exist to operate real business systems
- memory exists to improve future actions

If a future change improves runtime quality but does not make connected marketing operations more real, it should be deprioritized.
