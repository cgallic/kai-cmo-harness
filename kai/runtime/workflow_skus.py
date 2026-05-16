"""Workflow SKU manifest loading and validation for Kai runtime."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


_DEFAULT_SKU_DIR = (
    Path(__file__).resolve().parents[2] / "harness" / "workflow-skus"
)
_VALID_RISK_TIERS = {"low", "medium", "high"}
_REQUIRED_FIELDS = (
    "id",
    "name",
    "description",
    "stage",
    "inputs",
    "outputs",
    "artifacts",
    "risk_tier",
    "required_scopes",
    "quality_gates",
    "approval_rule",
    "estimated_runtime",
    "oss_price_band",
    "saas_later",
    "docs",
)


class WorkflowSKUValidationError(ValueError):
    """Raised when a workflow SKU manifest fails validation."""


@dataclass
class WorkflowSKUManifest:
    """Machine-readable workflow SKU used for registry and marketplace docs."""

    id: str
    name: str
    description: str
    stage: str
    inputs: List[Dict[str, Any]] = field(default_factory=list)
    outputs: List[str] = field(default_factory=list)
    artifacts: List[str] = field(default_factory=list)
    risk_tier: str = "medium"
    required_scopes: List[str] = field(default_factory=list)
    quality_gates: List[str] = field(default_factory=list)
    approval_rule: str = ""
    estimated_runtime: str = ""
    oss_price_band: str = ""
    saas_later: List[str] = field(default_factory=list)
    docs: List[str] = field(default_factory=list)

    def model_dump(self) -> Dict[str, Any]:
        """Return JSON-serializable manifest dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "stage": self.stage,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "artifacts": self.artifacts,
            "risk_tier": self.risk_tier,
            "required_scopes": self.required_scopes,
            "quality_gates": self.quality_gates,
            "approval_rule": self.approval_rule,
            "estimated_runtime": self.estimated_runtime,
            "oss_price_band": self.oss_price_band,
            "saas_later": self.saas_later,
            "docs": self.docs,
        }


def _coerce_string_list(value: Any, field_name: str, source: Path) -> List[str]:
    if not isinstance(value, list):
        raise WorkflowSKUValidationError(
            f"{source}: field '{field_name}' must be a list."
        )
    output: List[str] = []
    for item in value:
        if not isinstance(item, str) or not item.strip():
            raise WorkflowSKUValidationError(
                f"{source}: field '{field_name}' must contain non-empty strings."
            )
        output.append(item.strip())
    return output


def _coerce_inputs(value: Any, source: Path) -> List[Dict[str, Any]]:
    if not isinstance(value, list):
        raise WorkflowSKUValidationError(f"{source}: field 'inputs' must be a list.")
    inputs: List[Dict[str, Any]] = []
    for idx, item in enumerate(value):
        if not isinstance(item, dict):
            raise WorkflowSKUValidationError(
                f"{source}: inputs[{idx}] must be an object."
            )
        if not item.get("name"):
            raise WorkflowSKUValidationError(
                f"{source}: inputs[{idx}] must include a non-empty 'name'."
            )
        inputs.append(item)
    return inputs


def _validate_required_fields(payload: Dict[str, Any], source: Path) -> None:
    missing = [field for field in _REQUIRED_FIELDS if field not in payload]
    if missing:
        raise WorkflowSKUValidationError(
            f"{source}: missing required fields: {', '.join(missing)}"
        )


def validate_workflow_sku_payload(
    payload: Dict[str, Any],
    source: str = "<memory>",
) -> WorkflowSKUManifest:
    """Validate and normalize one workflow SKU payload."""
    source_path = Path(source)
    _validate_required_fields(payload, source_path)

    risk_tier = str(payload["risk_tier"]).strip().lower()
    if risk_tier not in _VALID_RISK_TIERS:
        raise WorkflowSKUValidationError(
            f"{source_path}: invalid risk_tier '{payload['risk_tier']}'. "
            f"Expected one of: {', '.join(sorted(_VALID_RISK_TIERS))}."
        )

    return WorkflowSKUManifest(
        id=str(payload["id"]).strip(),
        name=str(payload["name"]).strip(),
        description=str(payload["description"]).strip(),
        stage=str(payload["stage"]).strip(),
        inputs=_coerce_inputs(payload["inputs"], source_path),
        outputs=_coerce_string_list(payload["outputs"], "outputs", source_path),
        artifacts=_coerce_string_list(payload["artifacts"], "artifacts", source_path),
        risk_tier=risk_tier,
        required_scopes=_coerce_string_list(
            payload["required_scopes"], "required_scopes", source_path
        ),
        quality_gates=_coerce_string_list(
            payload["quality_gates"], "quality_gates", source_path
        ),
        approval_rule=str(payload["approval_rule"]).strip(),
        estimated_runtime=str(payload["estimated_runtime"]).strip(),
        oss_price_band=str(payload["oss_price_band"]).strip(),
        saas_later=_coerce_string_list(payload["saas_later"], "saas_later", source_path),
        docs=_coerce_string_list(payload["docs"], "docs", source_path),
    )


def load_workflow_skus(
    manifest_dir: Optional[Path] = None,
) -> Dict[str, WorkflowSKUManifest]:
    """Load and validate all workflow SKU manifests from disk."""
    target_dir = (manifest_dir or _DEFAULT_SKU_DIR).resolve()
    manifests: Dict[str, WorkflowSKUManifest] = {}
    if not target_dir.exists():
        return manifests

    for path in sorted(target_dir.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if not isinstance(raw, dict):
            raise WorkflowSKUValidationError(f"{path}: manifest root must be an object.")
        manifest = validate_workflow_sku_payload(raw, source=str(path))
        if manifest.id in manifests:
            raise WorkflowSKUValidationError(
                f"{path}: duplicate workflow id '{manifest.id}'."
            )
        manifests[manifest.id] = manifest
    return manifests


def get_workflow_sku(
    workflow_id: str,
    manifest_dir: Optional[Path] = None,
) -> Optional[WorkflowSKUManifest]:
    """Get a single workflow SKU manifest by id."""
    return load_workflow_skus(manifest_dir=manifest_dir).get(workflow_id)
