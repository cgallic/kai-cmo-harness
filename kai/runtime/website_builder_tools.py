"""Governed tool boundary for the real Website Builder code generator.

The commercial agents own the decisions and handoffs. This module is only the
tool adapter they call: it invokes the existing Website Builder orchestrator,
captures the provider-like process receipt, and hashes the files that changed.
It does not synthesize a fake run or pretend that a deployment happened.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from .commercial import COMMERCIAL_HANDOFF_SCHEMA, CommercialHandoff
from .store import RuntimeStore


WEBSITE_BUILDER_TOOL_ID = "website_builder.codegen"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _snapshot_files(project_dir: Path, roots: Iterable[str]) -> Dict[str, str]:
    snapshot: Dict[str, str] = {}
    for root in roots:
        root_path = (project_dir / root).resolve()
        if not root_path.exists():
            continue
        if not root_path.is_dir():
            snapshot[str(root_path.relative_to(project_dir))] = _sha256_file(root_path)
            continue
        for path in root_path.rglob("*"):
            if not path.is_file():
                continue
            if any(part in {"node_modules", ".git", ".next"} for part in path.parts):
                continue
            relative = str(path.relative_to(project_dir))
            snapshot[relative] = _sha256_file(path)
    return snapshot


def _tree_sha256(snapshot: Mapping[str, str]) -> str:
    canonical = "\n".join(
        f"{relative}\t{digest}" for relative, digest in sorted(snapshot.items())
    ).encode()
    return _sha256_bytes(canonical)


@dataclass(frozen=True)
class WebsiteBuilderToolResult:
    """Receipt for one real Website Builder tool invocation."""

    run_id: str
    work_id: str
    agent_id: str
    tool_id: str
    project_dir: str
    command: List[str]
    started_at: str
    finished_at: str
    return_code: int
    ok: bool
    spec_sha256: str
    stdout_sha256: str
    stderr_sha256: str
    output_tree_sha256: str
    changed_files: Dict[str, Dict[str, Optional[str]]]
    receipt_uri: str
    receipt_sha256: str

    def model_dump(self) -> Dict[str, Any]:
        return {
            "schema": COMMERCIAL_HANDOFF_SCHEMA,
            **self.__dict__,
        }


def execute_codegen(
    *,
    store: RuntimeStore,
    run_id: str,
    work_id: str,
    agent_id: str,
    project_dir: str | Path,
    specs: Sequence[Mapping[str, Any]],
    output_roots: Sequence[str],
    build: bool = True,
    timeout_seconds: int = 900,
) -> WebsiteBuilderToolResult:
    """Invoke ``Website_Builder/orchestrate.js`` and persist a real receipt.

    ``output_roots`` is required so the caller states which generated surface
    it is delegating to the tool. The receipt records before/after hashes for
    that surface; an agent cannot claim a build artifact from stdout alone.
    """
    if not specs:
        raise ValueError("specs must contain at least one Website Builder spec")
    if not output_roots:
        raise ValueError("output_roots must identify the generated surface")
    project = Path(project_dir).resolve()
    orchestrator = project / "orchestrate.js"
    if not orchestrator.is_file():
        raise FileNotFoundError(f"Website Builder orchestrator not found: {orchestrator}")
    if not run_id or not work_id or not agent_id:
        raise ValueError("run_id, work_id, and agent_id are required")

    spec_bytes = json.dumps(list(specs), sort_keys=True, separators=(",", ":")).encode()
    before = _snapshot_files(project, output_roots)
    started_at = _utc_now()
    env = os.environ.copy()
    if not build:
        env["BUILDERX_SKIP_BUILD"] = "1"
    command = ["node", "orchestrate.js", "--stdin"]
    try:
        completed = subprocess.run(
            command,
            cwd=project,
            input=json.dumps(list(specs)),
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
            check=False,
            env=env,
        )
        return_code = completed.returncode
        stdout = completed.stdout or ""
        stderr = completed.stderr or ""
    except subprocess.TimeoutExpired as error:
        return_code = 124
        stdout = (error.stdout or "") if isinstance(error.stdout, str) else ""
        stderr = ((error.stderr or "") if isinstance(error.stderr, str) else "") + "\nprocess timeout"

    finished_at = _utc_now()
    after = _snapshot_files(project, output_roots)
    changed_files: Dict[str, Dict[str, Optional[str]]] = {}
    for relative in sorted(set(before) | set(after)):
        if before.get(relative) == after.get(relative):
            continue
        changed_files[relative] = {
            "before_sha256": before.get(relative),
            "after_sha256": after.get(relative),
        }

    receipt_payload = {
        "schema": COMMERCIAL_HANDOFF_SCHEMA,
        "run_id": run_id,
        "work_id": work_id,
        "agent_id": agent_id,
        "tool_id": WEBSITE_BUILDER_TOOL_ID,
        "project_dir": str(project),
        "command": command,
        "started_at": started_at,
        "finished_at": finished_at,
        "return_code": return_code,
        "ok": return_code == 0,
        "spec_sha256": _sha256_bytes(spec_bytes),
        "stdout_sha256": _sha256_bytes(stdout.encode()),
        "stderr_sha256": _sha256_bytes(stderr.encode()),
        "output_tree_sha256": _tree_sha256(after),
        "changed_files": changed_files,
        "stdout_tail": stdout[-4000:],
        "stderr_tail": stderr[-4000:],
    }
    receipt_dir = store.commercial_dir / "tool_receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipt_path = receipt_dir / f"{work_id}.json"
    receipt_bytes = json.dumps(receipt_payload, indent=2, sort_keys=True).encode()
    temp_path = receipt_path.with_suffix(".json.tmp")
    temp_path.write_bytes(receipt_bytes)
    temp_path.replace(receipt_path)
    receipt_sha256 = _sha256_file(receipt_path)

    return WebsiteBuilderToolResult(
        run_id=run_id,
        work_id=work_id,
        agent_id=agent_id,
        tool_id=WEBSITE_BUILDER_TOOL_ID,
        project_dir=str(project),
        command=command,
        started_at=started_at,
        finished_at=finished_at,
        return_code=return_code,
        ok=return_code == 0,
        spec_sha256=receipt_payload["spec_sha256"],
        stdout_sha256=receipt_payload["stdout_sha256"],
        stderr_sha256=receipt_payload["stderr_sha256"],
        output_tree_sha256=receipt_payload["output_tree_sha256"],
        changed_files=changed_files,
        receipt_uri=f"artifact://commercial/tool-receipts/{work_id}.json",
        receipt_sha256=receipt_sha256,
    )


def result_to_handoff(
    result: WebsiteBuilderToolResult,
    *,
    source_ref: str,
    consumer_agent_id: str,
    expires_at: str,
) -> CommercialHandoff:
    """Turn a successful tool receipt into the next agent's handoff."""
    if not result.ok:
        raise ValueError("failed Website Builder tool result cannot become a ready handoff")
    return CommercialHandoff(
        run_id=result.run_id,
        work_id=result.work_id,
        source_ref=source_ref,
        producer_agent_id=result.agent_id,
        consumer_agent_id=consumer_agent_id,
        artifact_uri=result.receipt_uri,
        artifact_sha256=result.receipt_sha256,
        status="ready",
        approval_state="not_required",
        expires_at=expires_at,
        metadata={
            "tool_id": result.tool_id,
            "changed_file_count": len(result.changed_files),
            "spec_sha256": result.spec_sha256,
            "output_tree_sha256": result.output_tree_sha256,
        },
    )
