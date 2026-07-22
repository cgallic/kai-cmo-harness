"""One-command durable agency setup for Kai Company Autopilot.

This module wraps :class:`kai.packaging.setup.SetupWizard` instead of creating
another onboarding schema.  The setup receipt proves that the durable context
was written and read back; it deliberately does not claim that connectors or
external effects have been verified.
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from .setup import SetupResult, SetupWizard


class AgencySetupError(ValueError):
    """Raised when a one-command setup payload is incomplete or invalid."""


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True),
        encoding="utf-8",
    )
    temporary.replace(path)


def _validated_answers(wizard: SetupWizard, answers: Dict[str, Any]) -> Dict[str, Any]:
    normalized: Dict[str, Any] = dict(answers)
    errors = []
    for index, section in enumerate(wizard.get_sections()):
        processed = wizard.process_section(index, normalized)
        errors.extend(processed.pop("_errors", []))
        normalized.update(processed)

    if errors:
        raise AgencySetupError("; ".join(errors))
    return normalized


def run_agency_setup(
    workspace_dir: str | Path,
    answers: Dict[str, Any],
) -> Dict[str, Any]:
    """Create durable agency context and return a read-back-bound receipt.

    The command writes the existing canonical setup artifacts, reads them back,
    binds their SHA-256 hashes into ``setup_receipt.json``, and returns both the
    canonical :class:`SetupResult` and the receipt.  This is idempotent for the
    same agency id; a rerun replaces the same generated context files.
    """

    workspace = Path(workspace_dir).resolve()
    wizard = SetupWizard(str(workspace))
    normalized = _validated_answers(wizard, answers)
    result: SetupResult = wizard.complete_setup(normalized)
    brand_id = result.business_profile.get("brand_id", "default")

    artifact_paths = {
        "config": workspace / "config.yaml",
        "business_profile": workspace / brand_id / "config" / "business_profile.json",
        "workspace_state": workspace / brand_id / "workspace_state.json",
    }
    missing = [name for name, path in artifact_paths.items() if not path.is_file()]
    if missing:
        raise RuntimeError(f"Setup did not persist required artifacts: {', '.join(missing)}")

    profile_readback = json.loads(
        artifact_paths["business_profile"].read_text(encoding="utf-8")
    )
    state_readback = json.loads(
        artifact_paths["workspace_state"].read_text(encoding="utf-8")
    )
    if profile_readback.get("brand_id") != brand_id:
        raise RuntimeError("Business profile read-back did not match the setup brand")
    if state_readback.get("brand_id") != brand_id:
        raise RuntimeError("Workspace state read-back did not match the setup brand")

    receipt = {
        "schema_version": 1,
        "status": "durable_context_written",
        "brand_id": brand_id,
        "workspace": str(workspace),
        "created_at": _utc_now(),
        "proof_boundary": (
            "This receipt proves local durable-context write and read-back only; "
            "connector, provider, and external-effect verification remain separate gates."
        ),
        "artifacts": {
            name: {
                "path": str(path),
                "sha256": _sha256(path),
                "bytes": path.stat().st_size,
            }
            for name, path in artifact_paths.items()
        },
    }
    receipt_path = workspace / brand_id / "setup_receipt.json"
    _write_json_atomic(receipt_path, receipt)

    receipt_readback = json.loads(receipt_path.read_text(encoding="utf-8"))
    if receipt_readback.get("brand_id") != brand_id:
        raise RuntimeError("Setup receipt read-back did not match the setup brand")

    return {
        "result": result.model_dump(),
        "receipt": receipt_readback,
        "receipt_path": str(receipt_path),
    }


__all__ = ["AgencySetupError", "run_agency_setup"]
