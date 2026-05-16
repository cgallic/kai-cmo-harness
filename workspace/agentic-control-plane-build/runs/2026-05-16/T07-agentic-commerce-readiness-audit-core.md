# T07 Agentic Commerce Readiness Audit — Core OSS Slice

## Selected task
- ID: T07
- Name: Agentic Commerce Readiness Audit
- Queue status set this run: `ready_for_review`

## Existing code inspected
- `AGENTS.md`
- `docs/plans/2026-05-15-agentic-marketing-control-plane-prd.md` (T07 section)
- `workspace/agentic-world-gap-plan-2026-05-15.md`
- `workspace/agentic-control-plane-build/queue.json`
- `docs/ARCHITECTURE.md`
- `docs/superpowers/specs/2026-04-03-system-current-state-report.md`
- `kai/models/audit.py`
- `kai/audits/__init__.py`
- `kai/audits/offer_architecture.py`
- `scripts/quality_gates/agent_readiness_lint.py`
- `tests/test_offer_architecture_audit.py`

## Files changed
- `kai/audits/agentic_commerce.py`
  - Added fixture-friendly `audit_agentic_commerce_readiness(...)` audit engine.
  - Added category checks for: product schema, catalog fields, pricing/inventory clarity, shipping/returns policy, reviews/proof, checkout readiness, robots/llms, AI crawler policy, offer readability, and ACP/UCP/AP2/x402 readiness notes.
  - Added explicit missing-data handling for absent fixtures and unavailable live credentials (`connected_sources.credentials_available`) to prevent guessed claims.
  - Added `score_agentic_commerce_readiness(...)` and `summarize_agentic_commerce_findings(...)` helpers.
- `kai/audits/__init__.py`
  - Exported the new agentic-commerce audit helpers and updated audit inventory docs.
- `scripts/quality_gates/agent_commerce_lint.py`
  - Added local JSON quality-gate CLI for agentic-commerce fixtures with PASS/PARTIAL/FAIL verdicts.
  - Added JSON output mode for fixture-test workflows.
- `knowledge/checklists/agentic-commerce-checklist.md`
  - Added OSS checklist covering static-mode and connected-mode execution guidance.
- `tests/test_agentic_commerce_audit.py`
  - Added focused fixture tests for healthy baseline, missing critical inputs, and credential-unavailable data-gap behavior.

## Verification
- Command run:
  - `python -m pytest tests/test_agentic_commerce_audit.py tests/test_offer_architecture_audit.py`
- Result:
  - `8 passed`
- Additional validation:
  - `python scripts/quality_gates/agent_commerce_lint.py <temp-fixture>.json --json` (PASS output confirmed)

## Queue changes
- Updated `workspace/agentic-control-plane-build/queue.json`:
  - `T07` status: `ready` -> `ready_for_review`
- Dependency promotions:
  - None in this slice (`T07` not marked `done` yet).

## Blockers
- No code blockers.
- Remaining completion work for full T07 acceptance (outside this bounded slice): sample report artifact + expanded docs for static-vs-connected run examples.

## Next recommended task
- Finish T07 with a docs/report slice (sample fixture report + static/connected mode walkthrough), then mark `T07` `done` and promote `T08`/`T11` to `ready`.
