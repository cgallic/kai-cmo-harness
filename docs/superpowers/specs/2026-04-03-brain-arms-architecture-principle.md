# Brain / Arms Architecture Principle

Kai should be built as a single marketing brain with many execution arms, not as a bag of disconnected automations.

## Core model

The correct mental model is an octopus:

- the **brain** decides
- the **nervous system** governs
- the **arms** observe and act
- the **loop** closes with measurement and learning

If a connector, channel workflow, or background job starts making strategic decisions outside this loop, the system is drifting.

## 1. The brain

The brain is the central decision layer for marketing judgment.

It owns:

- business understanding
- archetype and module selection
- audits and diagnosis
- prioritization
- planning
- proposal generation
- approval intent
- memory and learning

In the current repo, this layer is primarily:

- [business_profile.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/business_profile.py)
- [audit.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/audit.py)
- [application_flow.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/application_flow.py)
- [store.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/store.py)
- [memory.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/memory.py)

The brain should decide:

- what matters
- what to do next
- what channel to use
- what risk tier applies
- whether an action should be held, approved, or blocked

The brain should not directly contain provider-specific mutation code.

## 2. The nervous system

The nervous system is the control layer between judgment and action.

It owns:

- action contracts
- policy and compliance checks
- approval state
- kill switches
- artifact lineage
- observability and audit history

In the current repo, this layer is primarily:

- [actions.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/actions.py)
- [policy.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/policy.py)
- [integrations.py](/mnt/e/Dev2/kai-cmo-harness-work/kai/runtime/integrations.py)
- [actions.py](/mnt/e/Dev2/kai-cmo-harness-work/gateway/routers/actions.py)

The nervous system exists so the arms cannot bypass:

- brand constraints
- compliance rules
- budget limits
- approval rules
- emergency kill switches

## 3. The arms

The arms are the external systems Kai uses to observe and act.

Examples:

- website and CMS
- Google Business Profile
- social channels
- paid media platforms
- email and CRM systems
- analytics systems
- call handling systems
- scheduling and ops systems

The arms should do only 3 things:

1. read state
2. apply approved actions
3. report results back

The arms should not decide strategy, priority, or policy on their own.

## 4. The closed loop

The system is only complete when it operates as a closed loop:

1. observe
2. interpret
3. prioritize
4. propose
5. approve or auto-run
6. execute
7. measure
8. learn
9. repeat

Without this loop, Kai is just a toolset.

With this loop, Kai becomes a marketing operating system.

## Connector design rule

Every external integration should be attached to the same central loop.

Each connector must answer:

1. What can I see?
2. What can I change?
3. How do I report the result back?

Each connector should be split into 4 parts:

1. integration registration
2. provider adapter
3. channel executor
4. watcher or state sync

That keeps provider logic isolated while preserving one central brain.

## Anti-drift rules

Reject work if it causes any of the following:

- a connector makes strategic decisions outside the central proposal model
- a background job mutates live systems without going through policy and approval
- provider-specific code leaks into business understanding or audit logic
- each channel invents its own state, approval, or memory model
- a channel integration becomes its own mini-product

Prefer work that:

- strengthens one proposal model for all channels
- strengthens one policy model for all mutations
- strengthens one memory model for future decisions
- keeps channel systems as interchangeable arms

## Practical implementation rule

Application logic should only emit typed actions.

Examples:

- `website/update_page_copy`
- `website/update_cta`
- `social/schedule_social_post`
- `paid_media/create_ad_creative`
- `email/launch_email_sequence`

Then:

- the nervous system decides whether the action is allowed
- the appropriate arm executes it
- the result comes back into artifacts, memory, and future planning

## What this means for the repo

When adding new external systems, do not build them as isolated automations.

Build them as arms attached to:

- one business understanding layer
- one audit and proposal layer
- one action and policy layer
- one approval model
- one measurement and memory loop

That is how Kai stays a marketing brain with many arms instead of devolving into disconnected scripts.
