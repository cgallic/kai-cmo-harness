# T09 Evidence Pack Exporter — Core OSS Slice

## Selected task
- ID: T09
- Name: Evidence Pack Exporter
- Queue status set this run: `ready_for_review`

## Existing code inspected
- `AGENTS.md`
- `docs/plans/2026-05-15-agentic-marketing-control-plane-prd.md` (T09 section)
- `workspace/agentic-world-gap-plan-2026-05-15.md`
- `workspace/agentic-control-plane-build/queue.json`
- `docs/ARCHITECTURE.md`
- `docs/superpowers/specs/2026-04-03-system-current-state-report.md`
- `kai/runtime/store.py`
- `kai/runtime/actions.py`
- `agent/traces/models.py`
- `tests/test_runtime_loader.py`
- `tests/test_actions_integrations.py`

## Files changed
- `kai/provenance/__init__.py`
  - Added provenance package exports for evidence-pack functionality.
- `kai/provenance/evidence_pack.py`
  - Added local `EvidencePackExporter` with run/action export methods.
  - Added deterministic JSON + Markdown evidence pack writing to local filesystem.
  - Added run-pack assembly with required proof fields: run metadata, artifact IDs, artifact links, sources, data gaps, claim cards, quality gates, policy results, mandate IDs, approval state, connector health, action result, rollback reference.
  - Added action-pack assembly for single `ActionProposal` records with mandate/data-gap checks.
- `tests/test_evidence_pack_exporter.py`
  - Added fixture test for run-based export covering artifact links, data gaps, mandate IDs, sources, and action result.
  - Added fixture test for action-based export covering missing-evidence and missing-mandate data-gap behavior.
- `workspace/agentic-control-plane-build/queue.json`
  - Updated `T09` status to `ready_for_review`.

## Verification
- Command run:
  - `python -m pytest tests/test_evidence_pack_exporter.py tests/test_runtime_loader.py tests/test_actions_integrations.py`
- Result:
  - `31 passed`
- Additional focused re-run:
  - `python -m pytest tests/test_evidence_pack_exporter.py`
  - `2 passed`

## Queue changes
- Updated `workspace/agentic-control-plane-build/queue.json`:
  - `T09` status: `ready` -> `ready_for_review`
- Dependency promotions:
  - None (task not marked `done` in this bounded slice).

## Blockers
- No functional blocker for this slice.
- Remaining completion opportunity before `done`: add a small CLI entrypoint for evidence-pack export and optional trace span attachment fields for richer proof context.

## Next recommended task
- T09 follow-up slice: add CLI wrapper (`scripts/quality` or runtime script) and optional trace linkage, then mark T09 `done`.
