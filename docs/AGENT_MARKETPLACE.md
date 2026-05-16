# Agent Marketplace Workflow SKUs

Kai exposes machine-readable workflow manifests from `harness/workflow-skus/` so humans and agents can inspect what a workflow does before execution.

## Manifest contract

Each workflow SKU is a YAML file with these required fields:

- `id`
- `name`
- `description`
- `stage`
- `inputs`
- `outputs`
- `artifacts`
- `risk_tier` (`low`, `medium`, `high`)
- `required_scopes`
- `quality_gates`
- `approval_rule`
- `estimated_runtime`
- `oss_price_band`
- `saas_later`
- `docs`

## Current OSS SKUs

- `agent-ready-audit`
- `local-lead-os`
- `agentic-commerce-readiness`
- `creator-commerce-ops`
- `content-gate`

## Runtime API

Use `kai.runtime.workflow_skus`:

- `load_workflow_skus()` to load all manifests
- `get_workflow_sku(workflow_id)` to load one manifest
- `validate_workflow_sku_payload(payload)` to validate a candidate manifest

Example:

```python
from kai.runtime.workflow_skus import load_workflow_skus

skus = load_workflow_skus()
print(sorted(skus.keys()))
```

## Validation behavior

- Missing required fields raise `WorkflowSKUValidationError`.
- Unknown `risk_tier` values raise `WorkflowSKUValidationError`.
- `inputs` must be a list of objects containing `name`.
- List fields must contain non-empty strings.

## How to add a new SKU

1. Add `harness/workflow-skus/<workflow-id>.yaml`.
2. Populate all required fields.
3. Keep `required_scopes`, `quality_gates`, and `approval_rule` conservative.
4. Add docs references in `docs`.
5. Run:

```bash
pytest tests/test_workflow_skus.py
```
