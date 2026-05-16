# T04 Connector Health Gate — Risk Matrix Adjustments

## Selected task
- ID: T04
- Name: Connector Health Gate
- Queue status set this run: `ready_for_review`

## Existing code inspected
- `AGENTS.md`
- `docs/plans/2026-05-15-agentic-marketing-control-plane-prd.md` (T04 section)
- `workspace/agentic-world-gap-plan-2026-05-15.md`
- `workspace/agentic-control-plane-build/queue.json`
- `docs/ARCHITECTURE.md`
- `docs/superpowers/specs/2026-04-03-system-current-state-report.md`
- `kai/runtime/connector_health.py`
- `kai/execution/executor.py`
- `agent/tasks/connector_health.py`
- `gateway/routers/connections.py`
- `tests/test_connector_health_gate.py`
- `tests/test_executor.py`

## Files changed
- `kai/runtime/connector_health.py`
  - Updated connector health gate decision matrix:
    - `degraded`: block for `medium/high`, warn for `low`.
    - `stale`: block for `high`, warn for `low/medium`.
    - `unverified`: block for `high`, warn for `low/medium`.
  - Treated `kill_switch` as `error` state (always blocking) in integration state assessment.
  - Updated warning wording to include risk tier.
- `tests/test_connector_health_gate.py`
  - Added stale medium-risk warning coverage.
  - Added unverified high-risk blocking coverage.

## Verification
- Command run:
  - `python -m pytest tests/test_connector_health_gate.py tests/test_executor.py`
- Result:
  - `22 passed`

## Queue changes
- Updated `workspace/agentic-control-plane-build/queue.json`:
  - `T04` status: `ready_for_review` (from `ready`)
- No dependent task promotions were applied in this run because `T04` is not marked `done`.

## Blockers
- None for this bounded slice.
- Remaining completion decision for T04 depends on reviewer acceptance of the final risk-tier policy behavior and whether additional CLI/API docs are required beyond existing tests/docstrings.

## Next recommended task
- Primary: finalize T04 review and, if accepted, mark `T04` as `done`.
- Next build task after T04 completion: `T05 Scheduled Handler Registration`.
