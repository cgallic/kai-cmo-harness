# Kai + Pipedream Connect Architecture

## Decision

Kai should use **Pipedream Connect** as the primary external connector and managed-auth substrate.

This is a connector-layer decision, not a product-brain decision.

Kai remains the marketing brain.
Pipedream Connect becomes the account connection and execution substrate for external systems where it reduces app-approval and auth burden.

## Why this decision

The main external-systems bottleneck is not user willingness to connect accounts.

The real bottleneck is:

- having to create and maintain app credentials across many providers
- waiting on provider app approvals and sensitive-scope reviews
- re-solving OAuth, token refresh, and connected-account lifecycle for every channel

Pipedream Connect is the best fit for Kai because it is optimized for:

- embedded integrations
- connected accounts
- managed auth
- broad connector coverage
- reducing the need for Kai to own provider app setup everywhere

## Architectural principle

Kai follows the **brain / nervous system / arms** model:

- the **brain** decides
- the **nervous system** governs
- the **arms** execute

Pipedream belongs to the **arms** layer.

It must not become:

- the source of strategy
- the source of approvals
- the source of memory
- the source of business understanding

Kai must stay in control of:

- business profile
- audits
- findings
- proposals
- policy and compliance
- approval workflow
- artifact lineage
- memory and learning

## Ownership split

### Kai owns

- workspace and brand model
- business understanding
- archetype and module selection
- audit and diagnosis
- proposal generation
- typed marketing action contracts
- policy and risk gating
- approval and hold logic
- action history and lineage
- memory writeback
- operator-facing review and control surfaces

### Pipedream Connect owns

- connected account onboarding
- managed auth
- provider token lifecycle
- account/session connection state
- connector execution substrate
- provider-facing auth complexity for supported integrations

## System shape

```text
BusinessProfile / Audit / Proposal Engine
                |
                v
         Kai Typed Actions
                |
                v
      PolicyEngine / Approvals / Kill Switches
                |
                v
        Channel Executor Abstraction
                |
                v
        Pipedream Connect Adapters
                |
                v
     External systems: website, social, ads, email, analytics, CRM
                |
                v
         Result / Diff / Outcome / Errors
                |
                v
      Kai Artifacts / Memory / Learning Loop
```

## Integration contract

Every external integration should be represented in Kai as a brand-scoped integration record.

The record should include:

- `integration_id`
- `brand_id`
- `channel`
- `provider`
- `status`
- `connected_account_id`
- `external_user_id`
- `capabilities`
- `scopes`
- `kill_switch`
- `config`
- `metadata`

`IntegrationRegistry` should become the canonical Kai-side index of connected systems, while the underlying auth and account state lives in Pipedream.

## Action contract

Kai should continue to emit typed actions like:

- `website/update_page_copy`
- `website/update_cta`
- `social/schedule_social_post`
- `paid_media/create_ad_creative`
- `paid_media/adjust_budget`
- `email/launch_email_sequence`
- `analytics/fix_tracking`

No application logic should call Pipedream directly.

The only valid path is:

1. Kai proposes a typed action
2. Kai evaluates policy and risk
3. Kai decides approval or auto-run
4. Kai executor chooses the right integration
5. Pipedream-backed adapter executes
6. Result returns to Kai
7. Kai records artifact, action status, and memory updates

## Adapter model

Pipedream should sit behind a Kai-owned adapter layer.

Recommended file layout:

- `gateway/adapters/pipedream/base.py`
- `gateway/adapters/pipedream/accounts.py`
- `gateway/adapters/pipedream/executor.py`
- `gateway/adapters/pipedream/state_sync.py`
- `gateway/adapters/pipedream/providers/`

Recommended responsibilities:

### `base.py`

- shared client setup
- request/response normalization
- error mapping
- retry-safe wrappers

### `accounts.py`

- connected account lookup
- external user mapping
- connection validation
- capability and scope discovery

### `executor.py`

- dispatch typed Kai actions to provider-specific execution handlers
- enforce capability checks before provider calls
- return normalized execution results

### `state_sync.py`

- pull read models and state snapshots back into Kai
- normalize analytics, content, campaign, and page state

### `providers/*`

- provider-specific translation only
- no business logic
- no approval logic
- no memory logic

## Required execution rules

Pipedream-backed execution must still obey Kai policy.

That means:

- every mutation goes through `PolicyEngine`
- every high-risk action requires explicit approval
- every integration respects the channel kill switch
- budget changes remain constrained by Kai rules
- regulated claims remain blocked or escalated by Kai rules
- execution results must be recorded in Kai, not only in Pipedream

## Read vs write strategy

Adopt Pipedream in this order:

### Phase 1: read-first

Start with read-heavy and low-risk flows:

- analytics reads
- account health checks
- connected account validation
- state snapshots

### Phase 2: low-risk writes

Then move to safe mutation families:

- approved content scheduling
- low-risk website updates
- approved email sends

### Phase 3: higher-risk channel ops

Then add:

- paid-media adjustments
- campaign launches
- more invasive site changes

## Recommended first channels

Use Pipedream first where the auth and provider coverage accelerate the product most:

1. analytics
2. CRM / email
3. social publishing
4. website / CMS

Paid media should come after the approval and execution loop is proven.

## Operator workflow

The operator should never feel like they are “using Pipedream.”

The operator workflow remains:

1. connect account
2. run review flow
3. inspect findings and proposed actions
4. approve or revise
5. Kai executes
6. Kai reports outcome

Pipedream is infrastructure behind the operator experience.

## Anti-drift rules

Reject any design where:

- Pipedream becomes the source of proposal generation
- Pipedream bypasses Kai approval and policy
- Kai stores only opaque external action IDs and loses semantic lineage
- channel-specific code forks its own approval model
- external provider actions are triggered directly from app logic

Prefer designs where:

- Kai remains the source of truth for action meaning
- Pipedream is interchangeable connector infrastructure
- execution results map back into Kai artifacts and memory
- provider logic is isolated behind adapters

## Initial implementation plan

### Step 1

Extend `IntegrationRegistry` to support Pipedream-specific identity:

- `connected_account_id`
- `external_user_id`
- `scopes`
- `provider_metadata`

### Step 2

Create the Pipedream adapter package under `gateway/adapters/pipedream/`.

### Step 3

Implement one read flow:

- connected account lookup
- state sync for one analytics or account-health surface

### Step 4

Implement one write flow:

- take one approved typed Kai action
- route through executor
- execute through Pipedream-backed adapter
- persist outcome to Kai action history

### Step 5

Connect the result back into:

- action execution state
- artifact bundle
- memory writeback

## Definition of done

This architecture is working when:

1. a business can connect an external account through Pipedream
2. Kai can register that connection in `IntegrationRegistry`
3. Kai can generate a typed action against that channel
4. Kai can approve or hold that action
5. a Pipedream-backed adapter can execute it
6. Kai records the result and learns from it

At that point, Pipedream is functioning as the arm substrate while Kai remains the marketing brain.
