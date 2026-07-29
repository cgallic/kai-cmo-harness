"""Cloudflare Pages deployment tool boundary for approved website artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from .store import RuntimeStore


CLOUDFLARE_TOOL_ID = "cloudflare.deploy"
_PROJECT_NAME = re.compile(r"^[a-z0-9][a-z0-9-]{1,62}$")


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _tree_sha256(directory: Path) -> str:
    entries: list[str] = []
    for path in sorted(directory.rglob("*")):
        if not path.is_file() or any(part in {".git", ".next", "node_modules"} for part in path.parts):
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        entries.append(f"{path.relative_to(directory)}\t{digest}")
    return hashlib.sha256("\n".join(entries).encode()).hexdigest()


@dataclass(frozen=True)
class CloudflareDeploymentReceipt:
    run_id: str
    work_id: str
    project_name: str
    output_dir: str
    artifact_tree_sha256: str
    command: List[str]
    return_code: int
    ok: bool
    started_at: str
    finished_at: str
    deployment_url: Optional[str]
    provider_output_sha256: str
    readback: Optional[dict]
    receipt_uri: str
    receipt_sha256: str

    def model_dump(self) -> Dict[str, Any]:
        return {"schema": "kai.cloudflare.deployment-receipt.v1", **self.__dict__}


def deploy_pages(
    *,
    store: RuntimeStore,
    run_id: str,
    work_id: str,
    project_name: str,
    output_dir: str | Path,
    approved_artifact_tree_sha256: str,
    account_id: Optional[str] = None,
    branch: Optional[str] = None,
    timeout_seconds: int = 900,
) -> CloudflareDeploymentReceipt:
    """Deploy one exact output tree and read the deployment list back.

    The caller must supply the tree digest bound into the approved handoff.
    Credentials remain in Wrangler's environment; they are never persisted in
    the receipt. This function performs a real Pages direct upload when called.
    """
    if not _PROJECT_NAME.fullmatch(project_name):
        raise ValueError("project_name must be a lowercase Cloudflare Pages name")
    output = Path(output_dir).resolve()
    if not output.is_dir():
        raise FileNotFoundError(f"Cloudflare Pages output directory not found: {output}")
    current_digest = _tree_sha256(output)
    if current_digest != approved_artifact_tree_sha256:
        raise ValueError("Cloudflare artifact tree changed after OLA approval")
    account = account_id or os.environ.get("CLOUDFLARE_ACCOUNT_ID")
    if not account:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID is required for Pages deployment")

    command = ["npx", "wrangler", "pages", "deploy", str(output), "--project-name", project_name]
    if branch:
        command.extend(["--branch", branch])
    command.extend(["--commit-hash", approved_artifact_tree_sha256, "--commit-message", f"Kai commercial run {run_id}/{work_id}"])
    started_at = _utc_now()
    completed = subprocess.run(
        command,
        cwd=output,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
        env={**os.environ, "CLOUDFLARE_ACCOUNT_ID": account},
    )
    provider_output = (completed.stdout or "") + "\n" + (completed.stderr or "")
    readback = None
    if completed.returncode == 0:
        readback_result = subprocess.run(
            ["npx", "wrangler", "pages", "deployment", "list", "--project-name", project_name, "--json"],
            cwd=output,
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            check=False,
            env={**os.environ, "CLOUDFLARE_ACCOUNT_ID": account},
        )
        if readback_result.returncode == 0:
            try:
                readback = json.loads(readback_result.stdout)
            except json.JSONDecodeError:
                readback = {"raw_sha256": hashlib.sha256(readback_result.stdout.encode()).hexdigest()}
        provider_output += "\n" + (readback_result.stdout or "") + "\n" + (readback_result.stderr or "")

    finished_at = _utc_now()
    deployment_url = None
    for token in provider_output.split():
        if token.startswith("https://") and ".pages.dev" in token:
            deployment_url = token.rstrip(".,)")
            break

    receipt_payload = {
        "schema": "kai.cloudflare.deployment-receipt.v1",
        "run_id": run_id,
        "work_id": work_id,
        "project_name": project_name,
        "output_dir": str(output),
        "artifact_tree_sha256": current_digest,
        "command": command,
        "return_code": completed.returncode,
        "ok": completed.returncode == 0 and readback is not None,
        "started_at": started_at,
        "finished_at": finished_at,
        "deployment_url": deployment_url,
        "provider_output_sha256": hashlib.sha256(provider_output.encode()).hexdigest(),
        "readback": readback,
    }
    receipt_dir = store.commercial_dir / "provider_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"{work_id}.cloudflare.json"
    receipt_bytes = json.dumps(receipt_payload, indent=2, sort_keys=True).encode()
    temp_path = receipt_path.with_suffix(".json.tmp")
    temp_path.write_bytes(receipt_bytes)
    temp_path.replace(receipt_path)
    receipt_sha256 = hashlib.sha256(receipt_path.read_bytes()).hexdigest()
    return CloudflareDeploymentReceipt(
        run_id=run_id,
        work_id=work_id,
        project_name=project_name,
        output_dir=str(output),
        artifact_tree_sha256=current_digest,
        command=command,
        return_code=completed.returncode,
        ok=receipt_payload["ok"],
        started_at=started_at,
        finished_at=finished_at,
        deployment_url=deployment_url,
        provider_output_sha256=receipt_payload["provider_output_sha256"],
        readback=readback,
        receipt_uri=f"artifact://commercial/provider-receipts/{work_id}.cloudflare.json",
        receipt_sha256=receipt_sha256,
    )
