# T04 Connector Health Gate — Execution Gate Slice

## Selected task
- ID: T04
- Name: Connector Health Gate
- Slice: Runtime connector-health decision API + pre-dispatch executor enforcement + fixture tests + usage docs

## Existing code inspected
- `docs/plans/2026-05-15-agentic-marketing-control-plane-prd.md`
- `workspace/agentic-control-plane-build/queue.json`
- `docs/ARCHITECTURE.md`
- `docs/superpowers/specs/2026-04-03-system-current-state-report.md`
- `kai/runtime/connector_health.py`
- `kai/runtime/integrations.py`
- `kai/execution/executor.py`
- `kai/runtime/policy.py`
- `tests/test_executor.py`

## Files changed
- `kai/runtime/connector_health.py`
  - Added health-gate state model (`missing`, `unverified`, `healthy`, `degraded`, `stale`, `error`).
  - Added `evaluate_connector_health_gate(...)` with risk-tier-aware allow/block semantics.
  - Added required-scope checks and stale-health detection.
- `kai/execution/executor.py`
  - Enforced connector health gate before connector dispatch.
  - Added risk-tier + required-scope inference for gate decisions.
  - Added blocked execution logging entries for gate failures.
- `tests/test_executor.py`
  - Updated integration guard expectations for connector health gate behavior.
  - Added degraded connector tests for high-risk block and low-risk warning path.
  - Updated fixture integration helper to include verified health timestamps.
- `tests/test_connector_health_gate.py`
  - Added fixture tests for missing, degraded (warn/block by risk), healthy, and stale states.
- `kai/runtime/__init__.py`
  - Exported connector-health gate helpers in runtime public surface.
- `docs/CONNECTOR_HEALTH_GATE.md`
  - Added Python and CLI-style usage documentation.

## Verification
- Command:
  - `python -m pytest tests/test_connector_health_gate.py tests/test_executor.py`
- Result:
  - `20 passed`

## Queue changes
- Updated `workspace/agentic-control-plane-build/queue.json`:
  - `T04` status: `ready` -> `ready_for_review`
- Dependency promotions:
  - None (T04 not marked `done`, so dependent tasks remain unchanged).

## Blockers
- None for this slice.

## Next recommended task
- Continue T04 with a second bounded slice:
  - apply the same gate semantics to scheduled connector checks (`agent/tasks/connector_health.py`) and expose state-based blocking/warning telemetry through connection health endpoints.
