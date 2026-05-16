# Run Handoff — T01 Agent Registry Core

## Selected task
- `T01` — Agent Registry
- Status set to `done` in queue after implementation + tests.

## Existing code inspected
- `kai/runtime/models.py`
- `kai/runtime/store.py`
- `kai/runtime/actions.py`
- `kai/runtime/integrations.py`
- `kai/runtime/__init__.py`
- `tests/test_runtime_loader.py`
- `tests/test_actions_integrations.py`
- `docs/ARCHITECTURE.md`
- `docs/superpowers/specs/2026-04-03-system-current-state-report.md`
- `docs/plans/2026-05-15-agentic-marketing-control-plane-prd.md`
- `workspace/agentic-world-gap-plan-2026-05-15.md`

## Files changed
- `kai/runtime/models.py`
  - Added `KaiAgentProfile` dataclass with required fields:
    `agent_id`, `name`, `owner`, `purpose`, `workspace_id`, `brand_scope`, `workflow_scope`, `tool_scope`, `model`, `assurance_level`, `status`, `created_at`, `expires_at`, `revoked_at`, `metadata`.
- `kai/runtime/agents.py` (new)
  - Added file-backed `AgentRegistry` with operations:
    `create`, `update`, `list`, `get`, `revoke`, `check_scope`.
  - Added `default_agent_profiles()` example profiles.
  - Added process-wide singleton `get_default_agent_registry()`.
- `kai/runtime/__init__.py`
  - Exported `KaiAgentProfile`, `AgentRegistry`, `default_agent_profiles`, `get_default_agent_registry`.
- `tests/test_agent_registry.py` (new)
  - Added fixture-backed tests for create/get/list/update, scope allow/deny, revoked scope failure, and default profile examples.
- `docs/AGENT_REGISTRY.md` (new)
  - Added OSS usage docs showing how to add an agent profile and run scope checks.
- `workspace/agentic-control-plane-build/queue.json`
  - Updated task statuses per dependency rule.

## Verification
- Command run:
  - `pytest -q tests/test_agent_registry.py`
- Result:
  - `4 passed in 0.36s`

## Queue changes
- `T01` changed: `ready` -> `done`
- Newly promoted to `ready` because dependencies are now satisfied:
  - `T02` Mandate Ledger
  - `T03` Workflow SKU Manifests
  - `T04` Connector Health Gate
- Remaining tasks kept as-is (`pending`) because dependencies are still unmet.

## Blockers
- No code blockers for T01.

## Next recommended task
- `T02` Mandate Ledger (next P0 in dependency order and now unblocked).
