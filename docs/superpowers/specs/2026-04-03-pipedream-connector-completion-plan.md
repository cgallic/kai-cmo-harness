# Pipedream Connector Completion Plan

## Goal

Finish the external connection layer so Kai can reliably onboard real businesses, connect their systems through Pipedream, execute approved actions, and verify that the full loop works in production.

This phase is not about adding more theory.
It is about finishing connector wiring, account connection flows, execution coverage, and verification.

## Why this is the next phase

Kai now has:

- business understanding
- audits and proposals
- approval and policy control
- action lifecycle tracking
- initial execution plumbing
- a first closed loop through analytics anomaly detection and WordPress execution

What is still missing is connector completeness:

- Pipedream-backed connected account flows
- provider/account mapping for real businesses
- full channel coverage across the highest-value marketing surfaces
- end-to-end execution verification for KaiCalls, Starrs Party, and new clients

The objective is to make the system operable for:

- KaiCalls
- Starrs Party
- incoming client onboarding

## Success definition

This phase is done when all of the following are true:

1. a business can connect its real accounts through Pipedream
2. Kai can persist those connections in `IntegrationRegistry`
3. Kai can verify the connection, scopes, and capabilities
4. Kai can read useful channel state back into audits, proposals, and watchers
5. Kai can route approved typed actions through a Pipedream-backed executor
6. Kai records execution results, failures, diffs, and memory updates
7. KaiCalls and Starrs Party can run through the same connection model as new clients

## Non-drift rules

Reject work if it:

- adds more planning without wiring a real connector path
- bypasses `ActionStore`, `PolicyEngine`, or kill switches
- hardcodes one client into provider logic
- lets provider-specific code leak into audit or proposal logic
- adds channel breadth without account verification and execution proof

Prefer work that:

- makes connection and execution repeatable across businesses
- improves connection health and debuggability
- increases real channel coverage through one consistent action model
- turns manual setup into reusable onboarding steps

## Core workstreams

## 1. Pipedream account model

Extend Kai’s integration records so they can represent Pipedream-managed accounts cleanly.

Required fields:

- `integration_id`
- `brand_id`
- `channel`
- `provider`
- `status`
- `connected_account_id`
- `external_user_id`
- `scopes`
- `capabilities`
- `config`
- `metadata`
- `kill_switch`
- `last_verified_at`
- `last_sync_at`
- `last_error`

Tasks:

1. Extend `IntegrationRegistry` for Pipedream identity and health fields.
2. Add a normalized connection status model:
   - `pending_auth`
   - `connected`
   - `degraded`
   - `disconnected`
   - `error`
3. Add capability normalization so Kai knows what each connected account can actually do.
4. Add scope visibility so operator surfaces can show what is connected vs missing.

Definition of done:

- every integration record can represent a real Pipedream connected account
- health and scope state are visible without digging through provider payloads

## 2. Pipedream adapter package

Create a Kai-owned adapter layer for all Pipedream interaction.

Recommended package:

- `gateway/adapters/pipedream/base.py`
- `gateway/adapters/pipedream/accounts.py`
- `gateway/adapters/pipedream/executor.py`
- `gateway/adapters/pipedream/state_sync.py`
- `gateway/adapters/pipedream/providers/*`

Tasks:

1. Add shared Pipedream client configuration and error handling.
2. Add connected-account lookup and validation helpers.
3. Add execution dispatch that translates typed Kai actions into provider calls.
4. Add read-model sync helpers that normalize provider data back into Kai state.
5. Add provider-specific translation modules only where necessary.

Definition of done:

- all Pipedream calls go through one adapter package
- no application logic calls Pipedream directly

## 3. Connection flows

Finish the actual connection lifecycle for businesses.

Tasks:

1. Create brand-scoped connection flow for each supported channel.
2. Map Pipedream connected accounts to Kai brands and channels.
3. Add connection verification after account connect.
4. Add reconnect flow for expired or degraded accounts.
5. Add disconnect flow that preserves history but disables execution.
6. Add per-channel kill switch compatibility.

Definition of done:

- a business can connect, reconnect, and disconnect accounts without manual JSON edits

## 4. Channel state sync

Kai cannot operate external systems safely if it cannot read them first.

Tasks:

1. Add state sync for analytics connectors.
2. Add state sync for website/CMS connectors.
3. Add state sync for social connectors.
4. Add state sync for email/CRM connectors.
5. Persist normalized state snapshots back into Kai artifacts or integration metadata.
6. Add stale-sync detection and warning status.

Definition of done:

- Kai can show the latest known state for each connected channel
- stale or broken integrations are visible and actionable

## 5. Execution coverage

Finish routing real approved actions through Pipedream-backed execution.

Priority order:

1. website / CMS
2. analytics read and anomaly follow-up
3. social publishing or scheduling
4. email / lifecycle
5. paid media

Tasks:

1. Define the first set of supported typed actions per channel.
2. Map each supported action to a Pipedream-backed provider execution path.
3. Normalize execution results into a shared `ExecutionResult`.
4. Capture before/after diffs where possible.
5. Store rollback references where possible.
6. Mark execution state consistently:
   - `pending`
   - `executing`
   - `completed`
   - `failed`
   - `rolled_back`

Definition of done:

- an approved action can execute against a real connected account and update Kai state accordingly

## 6. Health, observability, and debugging

Finish the operational safety layer around connectors.

Tasks:

1. Build connector health verification for all active integrations.
2. Add clear failure classification:
   - auth failure
   - scope failure
   - provider validation failure
   - rate limit
   - transient upstream error
   - unsupported action
3. Add operator-readable execution logs.
4. Add per-integration error history.
5. Add channel and brand-level health summaries.

Definition of done:

- connector failures are diagnosable without reading stack traces

## 7. Client migration and onboarding

This work must be validated against real businesses, not only fixtures.

Priority businesses:

1. KaiCalls
2. Starrs Party
3. new incoming client onboarding flow

Tasks:

1. Create connection readiness checklist for KaiCalls.
2. Create connection readiness checklist for Starrs Party.
3. Identify which systems each business needs connected first.
4. Create reusable onboarding flow for new clients:
   - create brand
   - fill business profile
   - choose archetype
   - connect systems
   - verify capabilities
   - run first audit
   - generate first action queue
5. Validate that one new client can follow the same path with no custom engineering.

Definition of done:

- KaiCalls and Starrs Party are migrated into the same connector model as new clients

## 8. End-to-end verification

Do not consider connectors complete until the live loop is verified for real businesses.

Per-business test flow:

1. connect account(s)
2. verify connection health
3. sync channel state
4. run audit / watcher / proposal generation
5. approve one low or medium risk action
6. execute through Pipedream-backed adapter
7. verify result in external system
8. confirm Kai recorded artifacts, logs, and memory updates

Required proof categories:

- one analytics read path
- one website mutation path
- one social or email execution path
- one anomaly or watcher-generated proposal path

Definition of done:

- at least one business completes every proof category successfully

## Recommended implementation order

1. finish Pipedream account model in `IntegrationRegistry`
2. build Pipedream adapter package
3. finish connection + verification flows
4. finish analytics and website sync/execution
5. finish social or email execution
6. add health/debugging surface
7. migrate KaiCalls
8. migrate Starrs Party
9. onboard one new client end to end

## Immediate task list

### Connector foundation

1. Patch `IntegrationRegistry` for Pipedream account fields and health state.
2. Add `gateway/adapters/pipedream/` package.
3. Implement connected-account lookup and validation.
4. Implement normalized capability and scope extraction.

### Execution

5. Route all approved website actions through Pipedream-backed execution.
6. Route analytics reads and anomaly proposals through Pipedream-backed sync.
7. Add one social or email execution path behind the same action system.

### Reliability

8. Add integration health status, last sync, and last error tracking.
9. Add connector error normalization and operator-readable logs.
10. Add reconnect and disconnect flows.

### Client readiness

11. Prepare KaiCalls connection inventory.
12. Prepare Starrs Party connection inventory.
13. Create reusable new-client connection checklist.
14. Verify the same connection flow works across all three business types.

## What not to do next

Do not prioritize:

- more archetypes
- broader creative systems
- UI polish before connector completion
- more connector theory docs
- exotic channels before core channels work

Right now the bottleneck is:

- connect the real systems
- route approved actions through them
- verify the results

## Deliverable at the end of this phase

At the end of this phase, Kai should be able to act as the central marketing brain for multiple businesses while Pipedream handles the external account layer.

That means:

- businesses can connect real systems
- Kai can reason over those systems
- Kai can propose actions against them
- Kai can safely execute approved work
- Kai can verify what happened
- Kai can operate KaiCalls, Starrs Party, and new clients on the same connector foundation
