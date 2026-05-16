"""Tests for workflow SKU manifest loader and validator."""

from __future__ import annotations

import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from kai.runtime.workflow_skus import (
    WorkflowSKUValidationError,
    get_workflow_sku,
    load_workflow_skus,
    validate_workflow_sku_payload,
)


def test_load_workflow_skus_includes_required_examples():
    """OSS MVP should ship the five seed workflow SKUs."""
    skus = load_workflow_skus()
    expected = {
        "agent-ready-audit",
        "local-lead-os",
        "agentic-commerce-readiness",
        "creator-commerce-ops",
        "content-gate",
    }
    assert expected.issubset(set(skus.keys()))


def test_get_workflow_sku_returns_expected_manifest():
    """Single SKU lookup should return a validated manifest object."""
    manifest = get_workflow_sku("local-lead-os")
    assert manifest is not None
    assert manifest.risk_tier == "medium"
    assert "quality_gates" in manifest.model_dump()


def test_validate_workflow_sku_payload_rejects_missing_fields():
    """Validation should fail loudly with readable field errors."""
    payload = {
        "id": "broken-workflow",
        "name": "Broken Workflow",
    }
    try:
        validate_workflow_sku_payload(payload, source="broken.yaml")
        assert False, "Expected WorkflowSKUValidationError"
    except WorkflowSKUValidationError as exc:
        message = str(exc)
        assert "missing required fields" in message
        assert "risk_tier" in message


def test_loader_rejects_invalid_risk_tier():
    """Loader should reject manifests with invalid risk tiers."""
    with tempfile.TemporaryDirectory() as tmpdir:
        manifest_path = Path(tmpdir) / "bad.yaml"
        manifest_path.write_text(
            "\n".join(
                [
                    "id: bad-risk",
                    "name: Bad Risk",
                    "description: bad",
                    "stage: test",
                    "inputs:",
                    "  - name: target_url",
                    "    type: url",
                    "outputs: [out]",
                    "artifacts: [artifact]",
                    "risk_tier: critical",
                    "required_scopes: [scope:read]",
                    "quality_gates: [scripts/quality_gates/four_us_score.py]",
                    "approval_rule: manual",
                    "estimated_runtime: 1m",
                    "oss_price_band: free-oss",
                    "saas_later: [hosted-version]",
                    "docs: [docs/AGENT_MARKETPLACE.md]",
                ]
            ),
            encoding="utf-8",
        )

        try:
            load_workflow_skus(manifest_dir=Path(tmpdir))
            assert False, "Expected WorkflowSKUValidationError"
        except WorkflowSKUValidationError as exc:
            assert "invalid risk_tier" in str(exc)


if __name__ == "__main__":
    test_load_workflow_skus_includes_required_examples()
    test_get_workflow_sku_returns_expected_manifest()
    test_validate_workflow_sku_payload_rejects_missing_fields()
    test_loader_rejects_invalid_risk_tier()
    print("All workflow SKU tests passed!")
