# MeetKai Long-Running CMO Harness — Coordinator Blackboard

Last updated: 2026-07-31  
Coordinator: Codex  
Repository: `E:\Dev2\kai-cmo-harness-work`  
Production app: `https://app.meetkai.xyz`  

## Objective

Finish the MeetKai dashboard as a durable, self-service marketing CMO for long-running operation: authenticated brand workspaces can create, approve, schedule, publish, reconcile, and inspect social marketing actions, while the agent control plane safely claims approved work, records lineage, heartbeats, and exposes provider-backed outcomes.

Completion means the system is implemented, deployed, migration-applied, credentialed, exercised through the real execution path, independently read back from Outstand, and reconciled in the dashboard. A local build, HTTP 200, queued action, or successful transport call alone is not completion proof.

## Scope lock

`Objective=finish the existing MeetKai dashboard and long-running CMO harness; target=E:\Dev2\kai-cmo-harness-work and its existing app-meetkai deployment; non-goals=do not create a replacement dashboard, new provider surface, parallel repository, or mock social network; proof=production deployment plus Supabase migration/read-back, agent execution evidence, Outstand provider receipt/read-back, and customer-visible reconciliation.`

The existing harness, gateway, Supabase schema, Vercel project, Outstand connector, and agent worker are authoritative. Preserve unrelated dirty files and do not claim a feature is live until the provider and database state independently confirm it.

## Acceptance gates

All gates must be green for “complete.”

1. **Source and safety:** intended changes are isolated; tests/build pass; action claims are atomic and idempotent; tenant/brand authorization and RLS remain enforced.
2. **Durable execution:** an approved social post creates a durable action, carries post/action lineage, is claimed exactly once by the long-running worker, and transitions through executing, succeeded/failed, and verified states.
3. **Provider proof:** Outstand credentials are present in the production/runtime secret stores; the real API accepts a publish or schedule request; the returned provider post/account receipt is read back with `get_post` or the documented equivalent.
4. **Reconciliation:** provider status, URL/ID, error, timestamps, and action outcome are persisted to the MeetKai social tables and visible through the authenticated dashboard status surface. Retries are bounded and idempotent.
5. **Operations:** heartbeat/status/lineage are live; scheduled reconciliation is configured; failures are observable; restart/retry behavior is documented and tested.
6. **Deployment and database:** migrations 006, 007, and 008 are applied to the linked production Supabase project and independently listed/read back; the correct Vercel project is deployed with the production alias.
7. **End-to-end evidence:** one real or explicitly authorized test post has a complete evidence chain: dashboard approval → action ID → worker execution → Outstand receipt/read-back → Supabase receipt → dashboard status.

## Workstreams

### A. Control plane and worker reliability

- Maintain atomic ready-action claiming and idempotent executing transitions.
- Keep the `execute_approved_actions` task registered and failure-safe.
- Preserve runtime heartbeat, status, and action-task lineage endpoints.
- Verify restart, duplicate-claim, failure, and retry behavior against the durable store.

Owner: harness/agent runtime.  
Exit evidence: targeted tests, worker logs, action record, lineage record, and heartbeat read-back.

### B. Social publishing execution bridge

- Connect the existing social post approval/schedule routes to the existing gateway/action executor.
- Bind every social post to a durable action ID and brand ID.
- Dispatch `publish_social_post` or `schedule_social_post` through the existing Outstand connector; do not bypass policy or create a second executor.
- Update post and receipt states transactionally where possible; make repeated execution safe.

Owner: `app-meetkai/app/api/social`, gateway action routes, harness executor.  
Exit evidence: route tests, action ID stored in lineage, worker execution, and receipt state transition.

### C. Outstand provider adapter and verification

- Keep API base and endpoint behavior aligned with the current Outstand API: `/v1/social-accounts`, `/posts/`, `containers`, `accounts`, and `scheduledAt`.
- Validate account/platform mapping and media URL handling.
- After creation, read the provider object back and persist provider ID, URL, status, response, and timestamps.
- Treat missing credentials, provider rejection, rate limits, and partial account outcomes as explicit failed/blocked states.

Owner: `kai/connectors/social/outstand.py` and connector factory.  
Exit evidence: adapter tests plus a real Outstand request and independent read-back.

### D. Dashboard and customer self-service surface

- Expose social draft creation, media, approval, scheduling, publishing state, provider receipt, and failure/retry status in the authenticated brand workspace.
- Make status readable without exposing internal planning labels or raw agent internals to customers.
- Show actionable recovery for failed or credential-blocked publishing.

Owner: `app-meetkai/app/api/social` and existing dashboard UI.  
Exit evidence: production browser/API read-back as an authenticated brand owner, including published and failed states.

### E. Durable reconciliation and operations

- Add the scheduled reconciliation path for pending/scheduled/publishing actions.
- Reconcile gateway/action state with Supabase social receipts and provider read-back.
- Add bounded retry/backoff and alertable error records.
- Ensure cron authentication and tenant scoping are enforced.

Owner: app cron routes, gateway, agent runtime.  
Exit evidence: cron invocation, reconciliation log/record, and corrected dashboard state after a controlled provider outcome.

### F. Production wiring and release

- Apply migrations 006–008 to the linked production Supabase project.
- Configure only real server-side secrets: Outstand API key/org/account configuration, gateway key, Supabase service role where required, and agent heartbeat token.
- Deploy using the existing Vercel project `app-meetkai` with root directory `app-meetkai`, then verify `https://app.meetkai.xyz`.
- Commit and push the completed implementation to `main`; retain unrelated untracked work.

Owner: coordinator with deployment authority.  
Exit evidence: migration list/read-back, Vercel deployment READY/alias, environment read-back by name, and final end-to-end packet.

## Known blockers and explicit handling

- **Production Supabase migration authority is currently unavailable.** `supabase migration list --linked` requested the database password and failed authentication. Do not claim migrations 006–008 are live until the linked database can be authenticated and migration state is read back.
- **Outstand production credentials are currently absent.** The Vercel production environment and inspected agent env files did not contain `OUTSTAND_API_KEY` or `OUTSTAND_ORG_ID`. The provider endpoint is reachable and returns 401 without a credential, proving reachability but not authorization. Do not invent or add empty secrets; credential provisioning is required for live publish proof.
- **Current uncommitted bridge is not yet shipped.** The bridge must be read, tested, integrated with the worker/reconciliation path, and committed only after the acceptance gates above are met.
- **Deployment scope must remain correct.** The correct Vercel project is `prj_WAOs1J99BOhSPUHpA4MgKiTFjrae`; the root repository project is not the MeetKai app. A READY deployment without the correct project/alias is not evidence.

When a blocker is external, continue all safe local implementation and tests, record the exact missing authority, and return to the blocked gate rather than replacing it with a scaffold.

## Evidence ledger

### Verified committed foundation

- `6aa3b51` — **Add long-running agent control plane**
  - Atomic action claiming and idempotent execution transition in `kai/runtime/actions.py`.
  - Registered `execute_approved_actions` worker task and failure handling.
  - Added migrations and types for brand-bound runtimes and action-task lineage.
  - Added heartbeat, lineage, and status API routes.
- `9aed15a` — **Add Outstand social publishing vertical slice**
  - Added Outstand connector, factory registration, and connector tests.
  - Added social publishing schema 007 and authenticated posts/approve/schedule/status routes.
  - Added social types and removed deployment-sensitive remote font imports.
  - Targeted tests, TypeScript, lint, and production build passed at the time of commit.

### Current uncommitted bridge evidence

Present in the working tree and intentionally not represented as complete:

- `app-meetkai/app/api/social/execute/route.ts` — social approval-to-action execution bridge.
- `app-meetkai/supabase/migrations/008_social_action_lineage.sql` — action lineage schema extension.
- `app-meetkai/.env.local.example` — documented Outstand and heartbeat variable names.

These files are the current implementation seam. They require review against the existing gateway contract, tests, production-safe authorization, and integration with reconciliation before staging.

### Deployment/provider checks already observed

- Correct Vercel deployment reached READY and aliased `https://app.meetkai.xyz` using the MeetKai project.
- Outstand `GET /v1/social-accounts` is reachable and returns `401 Missing or invalid Authorization header` without credentials.
- Vercel production env names currently do not include the Outstand credentials or heartbeat token.
- Linked Supabase migration read-back is not yet available because database authentication failed.

## Coordinator protocol

Every worker must return: files inspected/changed, tests run, exact output or failure, remaining gate, and whether the result is planned, built, deployed, executed, independently verified, reconciled, or blocked. The coordinator owns consolidation, avoids duplicate work, and never converts a worker conclusion into completion without independent read-back.

Next executable action: inspect and test the current social execution bridge against the existing gateway route contract, then implement the smallest missing reconciliation/read-back path while preserving this scope lock.
