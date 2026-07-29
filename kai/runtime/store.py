"""Stdlib-only persistence for runtime runs, artifacts, and state."""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from scripts.harness_config import get_config

from .loader import load_workspace_profile
from .models import (
    KaiArtifactRecord,
    KaiRunRecord,
    KaiRunRequest,
    KaiRuntimeState,
)
from .commercial import (
    COMMERCIAL_HANDOFF_SCHEMA,
    WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
    CommercialHandoff,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _dump_value(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()
    return value


def _json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=_dump_value)


def _json_load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload: Any) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(_json_dump(payload), encoding="utf-8")
    tmp_path.replace(path)


def _extract_dict(value: Any) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return dict(value)
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump") and callable(value.model_dump):
        return value.model_dump()
    raise TypeError(f"Unsupported object type: {type(value)!r}")


class RuntimeStore:
    """File-backed store for runtime runs, artifacts, and derived state."""

    def __init__(self, base_dir: Optional[Path] = None):
        cfg = get_config()
        if base_dir is None:
            base_dir = Path(os.environ.get("KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")))

        self.base_dir = base_dir
        self.runs_dir = _ensure_dir(self.base_dir / "runs")
        self.artifacts_dir = _ensure_dir(self.base_dir / "artifacts")
        self.commercial_dir = _ensure_dir(self.base_dir / "commercial")
        self.commercial_handoffs_dir = _ensure_dir(self.commercial_dir / "handoffs")
        self.commercial_events_file = self.commercial_dir / "events.jsonl"
        self.state_file = self.base_dir / "state.json"
        self._lock = threading.RLock()

    @classmethod
    def default(cls) -> "RuntimeStore":
        return cls()

    def start_run(
        self,
        run: KaiRunRequest | dict,
        *,
        parent_run_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> dict:
        """Create and persist a run record."""
        request = self._coerce_run_request(run)
        workspace = load_workspace_profile()
        brand = workspace.get_brand(request.brand_id)
        module_set = request.module_set or (brand.module_ids if brand else [])
        run_id = run_id or self._new_id("run")

        ancestors = self._lineage_for_parent(parent_run_id)
        record = {
            "run_id": run_id,
            "intent": request.intent,
            "workflow": request.workflow,
            "brand_id": request.brand_id,
            "surface": request.surface,
            "module_set": module_set,
            "status": "running",
            "parent_run_id": parent_run_id,
            "ancestor_run_ids": ancestors,
            "inputs": request.inputs,
            "outputs": {},
            "metadata": {
                **request.metadata,
                "workspace_id": workspace.workspace_id,
                "brand_name": brand.name if brand else request.brand_id,
            },
            "artifact_ids": [],
            "started_at": _utc_now(),
            "updated_at": _utc_now(),
            "completed_at": None,
        }

        with self._lock:
            self._write_run_record(record)
            self._refresh_state_locked()
        return record

    def start_commercial_run(
        self,
        run: KaiRunRequest | dict,
        *,
        parent_run_id: Optional[str] = None,
        run_id: Optional[str] = None,
    ) -> dict:
        """Start the website-to-checkout run in the canonical runtime store."""
        request = self._coerce_run_request(run)
        if request.workflow != WEBSITE_TO_CHECKOUT_WORKFLOW_ID:
            raise ValueError(
                "start_commercial_run requires workflow "
                f"'{WEBSITE_TO_CHECKOUT_WORKFLOW_ID}'"
            )
        record = self.start_run(
            request,
            parent_run_id=parent_run_id,
            run_id=run_id,
        )
        with self._lock:
            record = self._require_run(record["run_id"])
            record.setdefault("metadata", {})["commercial_schema"] = COMMERCIAL_HANDOFF_SCHEMA
            record["metadata"]["commercial_state"] = "running"
            record["metadata"]["commercial_handoff_ids"] = []
            self._write_run_record(record)
            self._append_commercial_event_locked(
                record["run_id"],
                "run.started",
                "agent.commercial.orchestrator",
                {"workflow": WEBSITE_TO_CHECKOUT_WORKFLOW_ID},
            )
            return record

    def append_commercial_handoff(
        self,
        handoff: CommercialHandoff | dict,
    ) -> dict:
        """Persist one typed agent-to-agent handoff and its provenance event."""
        envelope = self._coerce_commercial_handoff(handoff)
        errors = envelope.validate()
        if errors:
            raise ValueError("Invalid commercial handoff: " + "; ".join(errors))

        with self._lock:
            run = self._require_run(envelope.run_id)
            if run.get("workflow") != WEBSITE_TO_CHECKOUT_WORKFLOW_ID:
                raise ValueError("commercial handoff run is not website-to-checkout")
            path = self.commercial_handoffs_dir / f"{envelope.work_id}.json"
            previous = _json_load(path) if path.exists() else None
            if previous:
                immutable_fields = (
                    "run_id",
                    "work_id",
                    "source_ref",
                    "producer_agent_id",
                    "consumer_agent_id",
                    "artifact_uri",
                    "artifact_sha256",
                    "expires_at",
                )
                for field_name in immutable_fields:
                    if previous.get(field_name) != getattr(envelope, field_name):
                        raise ValueError(f"commercial handoff field is immutable: {field_name}")
                self._assert_commercial_transition(previous["status"], envelope.status)

            persisted = envelope.model_dump()
            persisted["updated_at"] = _utc_now()
            if not previous:
                persisted["created_at"] = persisted["updated_at"]
            else:
                persisted["created_at"] = previous.get("created_at", persisted["updated_at"])
            _write_json_atomic(path, persisted)

            handoff_ids = run.setdefault("metadata", {}).setdefault("commercial_handoff_ids", [])
            if envelope.work_id not in handoff_ids:
                handoff_ids.append(envelope.work_id)
            run["metadata"]["commercial_state"] = self._commercial_run_state(run["run_id"])
            run["updated_at"] = persisted["updated_at"]
            self._write_run_record(run)
            self._append_commercial_event_locked(
                envelope.run_id,
                f"handoff.{envelope.status}",
                envelope.producer_agent_id,
                {
                    "work_id": envelope.work_id,
                    "consumer_agent_id": envelope.consumer_agent_id,
                    "artifact_uri": envelope.artifact_uri,
                    "artifact_sha256": envelope.artifact_sha256,
                    "approval_state": envelope.approval_state,
                },
            )
            return persisted

    def claim_commercial_handoff(self, work_id: str, consumer_agent_id: str) -> dict:
        """Claim a ready handoff for its named consumer agent."""
        with self._lock:
            handoff = self._require_commercial_handoff(work_id)
            if handoff["consumer_agent_id"] != consumer_agent_id:
                raise PermissionError("handoff consumer does not match claimant")
            if handoff["status"] != "ready":
                raise ValueError(f"handoff is not ready: {handoff['status']}")
            if handoff["approval_state"] in {"pending", "declined"}:
                raise PermissionError("handoff is not approved for execution")
            handoff["status"] = "claimed"
            return self._write_commercial_transition_locked(handoff, consumer_agent_id)

    def complete_commercial_handoff(
        self,
        work_id: str,
        consumer_agent_id: str,
        *,
        result: Optional[dict] = None,
    ) -> dict:
        """Complete a claimed handoff without changing its immutable artifact binding."""
        with self._lock:
            handoff = self._require_commercial_handoff(work_id)
            if handoff["consumer_agent_id"] != consumer_agent_id:
                raise PermissionError("handoff consumer does not match completer")
            if handoff["status"] != "claimed":
                raise ValueError(f"handoff is not claimed: {handoff['status']}")
            handoff["status"] = "completed"
            if result:
                handoff.setdefault("metadata", {})["consumer_result"] = dict(result)
            return self._write_commercial_transition_locked(handoff, consumer_agent_id)

    def set_commercial_approval(
        self,
        work_id: str,
        approval_state: str,
        *,
        approval_ref: Optional[str] = None,
        approved_by: Optional[str] = None,
    ) -> dict:
        """Bind an OLA decision to the exact handoff before an effect can run."""
        if approval_state not in {"not_required", "pending", "approved", "declined"}:
            raise ValueError(f"invalid approval state: {approval_state}")
        if approval_state == "approved" and not approval_ref:
            raise ValueError("approved commercial handoff requires approval_ref")
        with self._lock:
            handoff = self._require_commercial_handoff(work_id)
            handoff["approval_state"] = approval_state
            handoff.setdefault("metadata", {})["approval_ref"] = approval_ref
            handoff["metadata"]["approved_by"] = approved_by
            return self._write_commercial_transition_locked(
                handoff,
                "agent.ola.projector",
                event_type="approval." + approval_state,
            )

    def list_commercial_handoffs(
        self,
        *,
        run_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 200,
    ) -> List[dict]:
        """List durable handoffs, newest transitions first."""
        handoffs = []
        for path in self.commercial_handoffs_dir.glob("*.json"):
            item = _json_load(path)
            if run_id and item.get("run_id") != run_id:
                continue
            if status and item.get("status") != status:
                continue
            handoffs.append(item)
        handoffs.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return handoffs[:limit]

    def get_commercial_handoff(self, work_id: str) -> dict:
        """Return one durable commercial handoff by work ID."""
        with self._lock:
            return dict(self._require_commercial_handoff(work_id))

    def get_commercial_bundle(self, run_id: str) -> Optional[dict]:
        """Return a run, all handoffs, and append-only provenance events."""
        run = self.get_run(run_id)
        if not run:
            return None
        events = []
        if self.commercial_events_file.exists():
            for line in self.commercial_events_file.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                event = json.loads(line)
                if event.get("run_id") == run_id:
                    events.append(event)
        return {
            "schema": COMMERCIAL_HANDOFF_SCHEMA,
            "run": run,
            "handoffs": self.list_commercial_handoffs(run_id=run_id),
            "events": events,
        }

    def update_run(self, run_id: str, **changes) -> dict:
        """Patch a run record and persist the change."""
        with self._lock:
            record = self.get_run(run_id)
            if not record:
                raise KeyError(f"Run not found: {run_id}")
            record.update(changes)
            record["updated_at"] = _utc_now()
            self._write_run_record(record)
            self._refresh_state_locked()
            return record

    def complete_run(
        self,
        run_id: str,
        *,
        status: str = "completed",
        outputs: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ) -> dict:
        """Mark a run as complete and persist outputs."""
        with self._lock:
            record = self.get_run(run_id)
            if not record:
                raise KeyError(f"Run not found: {run_id}")
            record["status"] = status
            if outputs is not None:
                record["outputs"] = _extract_dict(outputs)
            if metadata:
                record["metadata"].update(metadata)
            record["updated_at"] = _utc_now()
            record["completed_at"] = _utc_now()
            self._write_run_record(record)
            self._refresh_state_locked()
            return record

    # ------------------------------------------------------------------
    # Approval lifecycle mutations
    # ------------------------------------------------------------------

    _APPROVAL_ACTIONABLE = {"draft", "held", "running", "completed"}

    def approve_run(self, run_id: str, *, note: Optional[str] = None) -> dict:
        """Mark a run as approved and trigger memory writeback."""
        with self._lock:
            record = self._require_run(run_id)
            self._assert_actionable(record, "approve")
            record["status"] = "approved"
            record["updated_at"] = _utc_now()
            record["completed_at"] = record.get("completed_at") or _utc_now()
            approval_history = record.get("metadata", {}).get("approval_history", [])
            approval_history.append({
                "action": "approved",
                "at": _utc_now(),
                "note": note,
            })
            record.setdefault("metadata", {})["approval_history"] = approval_history
            self._write_run_record(record)
            self._refresh_state_locked()

        self._run_memory_writeback(run_id)
        return record

    def hold_run(self, run_id: str, *, note: Optional[str] = None) -> dict:
        """Place a run on hold pending human review."""
        with self._lock:
            record = self._require_run(run_id)
            self._assert_actionable(record, "hold")
            record["status"] = "held"
            record["updated_at"] = _utc_now()
            approval_history = record.get("metadata", {}).get("approval_history", [])
            approval_history.append({
                "action": "held",
                "at": _utc_now(),
                "note": note,
            })
            record.setdefault("metadata", {})["approval_history"] = approval_history
            self._write_run_record(record)
            self._refresh_state_locked()
            return record

    def request_revision(self, run_id: str, note: str) -> dict:
        """Request a revision, moving the run back to draft."""
        with self._lock:
            record = self._require_run(run_id)
            self._assert_actionable(record, "request_revision")
            record["status"] = "draft"
            record["updated_at"] = _utc_now()
            record["completed_at"] = None
            approval_history = record.get("metadata", {}).get("approval_history", [])
            approval_history.append({
                "action": "revision_requested",
                "at": _utc_now(),
                "note": note,
            })
            record.setdefault("metadata", {})["approval_history"] = approval_history
            self._write_run_record(record)
            self._refresh_state_locked()
            return record

    def reject_run(self, run_id: str, *, note: Optional[str] = None) -> dict:
        """Reject a run permanently."""
        with self._lock:
            record = self._require_run(run_id)
            self._assert_actionable(record, "reject")
            record["status"] = "failed"
            record["updated_at"] = _utc_now()
            record["completed_at"] = record.get("completed_at") or _utc_now()
            approval_history = record.get("metadata", {}).get("approval_history", [])
            approval_history.append({
                "action": "rejected",
                "at": _utc_now(),
                "note": note,
            })
            record.setdefault("metadata", {})["approval_history"] = approval_history
            record.setdefault("outputs", {})["rejection_note"] = note
            self._write_run_record(record)
            self._refresh_state_locked()
            return record

    def resume_run(
        self,
        run_id: str,
        *,
        inputs_override: Optional[dict] = None,
    ) -> dict:
        """Create a new child run linked to a prior run for revision continuation."""
        parent = self._require_run(run_id)
        if parent["status"] not in ("draft", "held", "failed"):
            raise ValueError(
                f"Cannot resume run in status '{parent['status']}' — "
                "only draft, held, or failed runs can be resumed"
            )
        child_request = KaiRunRequest(
            intent=f"Revision of {parent['intent']}",
            workflow=parent["workflow"],
            brand_id=parent["brand_id"],
            surface=parent.get("surface", "local"),
            module_set=list(parent.get("module_set", [])),
            inputs={**parent.get("inputs", {}), **(inputs_override or {})},
            metadata={
                **parent.get("metadata", {}),
                "resumed_from": run_id,
            },
        )
        return self.start_run(child_request, parent_run_id=run_id)

    def _require_run(self, run_id: str) -> dict:
        record = self.get_run(run_id)
        if not record:
            raise KeyError(f"Run not found: {run_id}")
        return record

    def _assert_actionable(self, record: dict, action: str) -> None:
        if record["status"] not in self._APPROVAL_ACTIONABLE:
            raise ValueError(
                f"Cannot {action} run in status '{record['status']}' — "
                f"must be one of {sorted(self._APPROVAL_ACTIONABLE)}"
            )

    def _run_memory_writeback(self, run_id: str) -> None:
        """Trigger memory writeback after approval (best-effort)."""
        try:
            from .memory import write_back_memory
            write_back_memory(run_id, self)
        except Exception:
            pass

    def record_artifact(
        self,
        artifact: KaiArtifactRecord | dict,
        *,
        run_id: Optional[str] = None,
        parent_artifact_id: Optional[str] = None,
        artifact_id: Optional[str] = None,
    ) -> dict:
        """Persist an artifact and link it to a run if provided."""
        record = self._coerce_artifact(artifact)
        artifact_id = artifact_id or record.get("artifact_id") or self._new_id("art")
        source_run = run_id or record.get("source_run")
        if source_run:
            run_record = self.get_run(source_run)
            if not run_record:
                raise KeyError(f"Run not found: {source_run}")
            lineage = self.get_run_lineage(source_run)
            module_set = record.get("module_set") or run_record.get("module_set", [])
            brand_id = record.get("brand_id") or run_record["brand_id"]
            workflow = record.get("workflow") or run_record["workflow"]
        else:
            lineage = []
            module_set = record.get("module_set", [])
            brand_id = record["brand_id"]
            workflow = record["workflow"]

        now = _utc_now()
        persisted = {
            "artifact_id": artifact_id,
            "artifact_type": record["artifact_type"],
            "brand_id": brand_id,
            "workflow": workflow,
            "module_set": module_set,
            "source_run": source_run,
            "parent_artifact_id": parent_artifact_id or record.get("parent_artifact_id"),
            "lineage_run_ids": lineage,
            "created_at": record.get("created_at") or now,
            "updated_at": now,
            "data": record.get("data", {}),
        }

        with self._lock:
            _write_json_atomic(self.artifacts_dir / f"{artifact_id}.json", persisted)
            if source_run:
                run_record = self.get_run(source_run)
                if run_record:
                    artifact_ids = run_record.get("artifact_ids", [])
                    if artifact_id not in artifact_ids:
                        artifact_ids.append(artifact_id)
                        run_record["artifact_ids"] = artifact_ids
                        run_record["updated_at"] = now
                        self._write_run_record(run_record)
            self._refresh_state_locked()
        return persisted

    def get_run(self, run_id: str) -> Optional[dict]:
        """Load a run record by ID."""
        path = self.runs_dir / f"{run_id}.json"
        if not path.exists():
            return None
        return _json_load(path)

    def get_artifact(self, artifact_id: str) -> Optional[dict]:
        """Load an artifact record by ID."""
        path = self.artifacts_dir / f"{artifact_id}.json"
        if not path.exists():
            return None
        return _json_load(path)

    def list_runs(
        self,
        *,
        brand_id: Optional[str] = None,
        workflow: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """List persisted run records."""
        records = []
        for path in self.runs_dir.glob("*.json"):
            record = _json_load(path)
            if brand_id and record.get("brand_id") != brand_id:
                continue
            if workflow and record.get("workflow") != workflow:
                continue
            if status and record.get("status") != status:
                continue
            records.append(record)
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return records[:limit]

    def get_run_artifacts(self, run_id: str) -> List[dict]:
        """Return artifacts recorded for a run in creation order."""
        artifacts = self.list_artifacts(run_id=run_id, limit=1000)
        return sorted(artifacts, key=lambda item: item.get("created_at", ""))

    def list_approvals(
        self,
        *,
        brand_id: Optional[str] = None,
        workflow: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """List runs that reached an approval or hold decision."""
        approval_statuses = {"approved", "held"}
        records = []
        for record in self.list_runs(brand_id=brand_id, workflow=workflow, status=status, limit=10_000):
            if record.get("status") not in approval_statuses:
                continue
            records.append(record)
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return records[:limit]

    def get_run_bundle(self, run_id: str) -> Optional[dict]:
        """Return a run with its lineage, artifacts, and approval context."""
        run = self.get_run(run_id)
        if not run:
            return None

        artifacts = self.get_run_artifacts(run_id)
        lineage = []
        for lineage_run_id in self.get_run_lineage(run_id):
            lineage_run = self.get_run(lineage_run_id)
            if not lineage_run:
                continue
            lineage.append(
                {
                    "run": lineage_run,
                    "artifacts": self.get_run_artifacts(lineage_run_id),
                }
            )

        gate_artifact = next(
            (
                artifact
                for artifact in reversed(artifacts)
                if artifact.get("artifact_type") == "gate_proposal"
            ),
            None,
        )
        approved_artifact = next(
            (
                artifact
                for artifact in reversed(artifacts)
                if artifact.get("artifact_type") == "approved_asset"
            ),
            None,
        )
        approval = {
            "status": run.get("status"),
            "policy": run.get("metadata", {}).get("approval_policy"),
            "proposal_id": run.get("outputs", {}).get("proposal_id"),
            "gate_report": (
                run.get("outputs", {}).get("gate_report")
                or (gate_artifact or {}).get("data", {}).get("gate_report")
            ),
            "gate_artifact_id": (gate_artifact or {}).get("artifact_id"),
            "approved_artifact_id": (approved_artifact or {}).get("artifact_id"),
            "finalized_at": run.get("completed_at"),
        }

        memory_updates = self._collect_memory_updates(run_id, run, artifacts)

        return {
            "run": run,
            "lineage": lineage,
            "artifacts": artifacts,
            "approval": approval,
            "observability": self._build_observability_snapshot(),
            "memory_updates": memory_updates,
        }

    def list_artifacts(
        self,
        *,
        brand_id: Optional[str] = None,
        workflow: Optional[str] = None,
        artifact_type: Optional[str] = None,
        run_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[dict]:
        """List persisted artifact records."""
        records = []
        for path in self.artifacts_dir.glob("*.json"):
            record = _json_load(path)
            if brand_id and record.get("brand_id") != brand_id:
                continue
            if workflow and record.get("workflow") != workflow:
                continue
            if artifact_type and record.get("artifact_type") != artifact_type:
                continue
            if run_id and record.get("source_run") != run_id:
                continue
            records.append(record)
        records.sort(key=lambda item: item.get("updated_at", ""), reverse=True)
        return records[:limit]

    def get_run_lineage(self, run_id: str) -> List[str]:
        """Return the ancestor chain ending with the requested run."""
        lineage = []
        current = self.get_run(run_id)
        while current:
            lineage.append(current["run_id"])
            parent_id = current.get("parent_run_id")
            if not parent_id:
                break
            current = self.get_run(parent_id)
        return list(reversed(lineage))

    def get_state(self) -> Optional[dict]:
        """Load the latest workspace state snapshot."""
        if not self.state_file.exists():
            return None
        return _json_load(self.state_file)

    def snapshot_state(self) -> dict:
        """Force a state recomputation and persist it."""
        with self._lock:
            return self._refresh_state_locked()

    def _refresh_state_locked(self) -> dict:
        workspace = load_workspace_profile()
        runs = [self.get_run(path.stem) for path in self.runs_dir.glob("*.json")]
        runs = [record for record in runs if record]
        artifacts = [self.get_artifact(path.stem) for path in self.artifacts_dir.glob("*.json")]
        artifacts = [record for record in artifacts if record]

        latest_run_ids_by_brand: Dict[str, str] = {}
        latest_run_ids_by_brand_workflow: Dict[str, str] = {}
        latest_artifact_ids_by_brand: Dict[str, str] = {}
        latest_artifact_ids_by_brand_workflow: Dict[str, str] = {}

        def _sort_key(record: dict) -> str:
            return record.get("updated_at") or record.get("created_at") or ""

        for record in sorted(runs, key=_sort_key, reverse=True):
            brand_id = record["brand_id"]
            workflow_key = f"{brand_id}:{record['workflow']}"
            latest_run_ids_by_brand.setdefault(brand_id, record["run_id"])
            latest_run_ids_by_brand_workflow.setdefault(workflow_key, record["run_id"])

        active_run_ids = [
            record["run_id"]
            for record in runs
            if record.get("status") in {"running", "draft", "held"}
        ]

        for record in sorted(artifacts, key=_sort_key, reverse=True):
            brand_id = record["brand_id"]
            workflow_key = f"{brand_id}:{record['workflow']}"
            latest_artifact_ids_by_brand.setdefault(brand_id, record["artifact_id"])
            latest_artifact_ids_by_brand_workflow.setdefault(workflow_key, record["artifact_id"])

        approval_run_ids = [
            record["run_id"]
            for record in runs
            if record.get("status") in {"approved", "held"}
        ]
        approval_counts_by_status: Dict[str, int] = {}
        latest_approval_run_ids_by_brand: Dict[str, str] = {}
        latest_approval_run_ids_by_brand_workflow: Dict[str, str] = {}
        for record in sorted(
            (record for record in runs if record.get("status") in {"approved", "held"}),
            key=_sort_key,
            reverse=True,
        ):
            approval_status = record.get("status", "unknown")
            approval_counts_by_status[approval_status] = approval_counts_by_status.get(approval_status, 0) + 1
            brand_id = record["brand_id"]
            workflow_key = f"{brand_id}:{record['workflow']}"
            latest_approval_run_ids_by_brand.setdefault(brand_id, record["run_id"])
            latest_approval_run_ids_by_brand_workflow.setdefault(workflow_key, record["run_id"])

        run_counts_by_status: Dict[str, int] = {}
        for record in runs:
            run_status = record.get("status", "unknown")
            run_counts_by_status[run_status] = run_counts_by_status.get(run_status, 0) + 1

        artifact_counts_by_type: Dict[str, int] = {}
        for record in artifacts:
            artifact_type = record.get("artifact_type", "unknown")
            artifact_counts_by_type[artifact_type] = artifact_counts_by_type.get(artifact_type, 0) + 1

        observability = {
            "run_count": len(runs),
            "artifact_count": len(artifacts),
            "run_counts_by_status": run_counts_by_status,
            "artifact_counts_by_type": artifact_counts_by_type,
            "active_run_count": len(active_run_ids),
        }

        approvals = {
            "approval_run_ids": approval_run_ids,
            "approval_counts_by_status": approval_counts_by_status,
            "latest_approval_run_ids_by_brand": latest_approval_run_ids_by_brand,
            "latest_approval_run_ids_by_brand_workflow": latest_approval_run_ids_by_brand_workflow,
        }

        state = KaiRuntimeState(
            workspace_id=workspace.workspace_id,
            updated_at=_utc_now(),
            latest_run_ids_by_brand=latest_run_ids_by_brand,
            latest_run_ids_by_brand_workflow=latest_run_ids_by_brand_workflow,
            latest_artifact_ids_by_brand=latest_artifact_ids_by_brand,
            latest_artifact_ids_by_brand_workflow=latest_artifact_ids_by_brand_workflow,
            active_run_ids=active_run_ids,
        ).model_dump()
        state["approvals"] = approvals
        state["observability"] = observability
        _write_json_atomic(self.state_file, state)
        return state

    def _collect_memory_updates(
        self, run_id: str, run: dict, artifacts: List[dict]
    ) -> List[dict]:
        """Collect memory-update records produced by the run."""
        updates: List[dict] = []
        for artifact in artifacts:
            if artifact.get("artifact_type") == "learned_pattern":
                updates.append({
                    "source_run": run_id,
                    "type": "learned_pattern",
                    "brand_id": run.get("brand_id"),
                    "workflow": run.get("workflow"),
                    "data": artifact.get("data", {}),
                    "recorded_at": artifact.get("created_at"),
                })
        run_memory = run.get("outputs", {}).get("memory_updates")
        if isinstance(run_memory, list):
            for entry in run_memory:
                updates.append({
                    "source_run": run_id,
                    "type": entry.get("type", "run_output"),
                    "brand_id": run.get("brand_id"),
                    "workflow": run.get("workflow"),
                    "data": entry.get("data", entry),
                    "recorded_at": run.get("completed_at") or run.get("updated_at"),
                })
        return updates

    def _build_observability_snapshot(self) -> dict:
        """Build a lightweight observability snapshot for the control plane."""
        state = self.get_state() or self.snapshot_state()
        return {
            "workspace_id": state.get("workspace_id"),
            "updated_at": state.get("updated_at"),
            "observability": state.get("observability", {}),
            "approvals": state.get("approvals", {}),
        }

    def _coerce_commercial_handoff(self, handoff: CommercialHandoff | dict) -> CommercialHandoff:
        if isinstance(handoff, CommercialHandoff):
            return handoff
        if not isinstance(handoff, dict):
            raise TypeError(f"Unsupported commercial handoff type: {type(handoff)!r}")
        payload = dict(handoff)
        payload.pop("schema", None)
        return CommercialHandoff(**payload)

    def _require_commercial_handoff(self, work_id: str) -> dict:
        path = self.commercial_handoffs_dir / f"{work_id}.json"
        if not path.exists():
            raise KeyError(f"Commercial handoff not found: {work_id}")
        return _json_load(path)

    def _assert_commercial_transition(self, previous: str, current: str) -> None:
        allowed = {
            "ready": {"ready", "claimed", "blocked", "failed"},
            "claimed": {"claimed", "completed", "blocked", "failed"},
            "completed": {"completed"},
            "blocked": {"blocked", "ready", "failed"},
            "failed": {"failed"},
        }
        if current not in allowed.get(previous, set()):
            raise ValueError(f"invalid commercial handoff transition: {previous} -> {current}")

    def _write_commercial_transition_locked(
        self,
        handoff: dict,
        actor_agent_id: str,
        *,
        event_type: Optional[str] = None,
    ) -> dict:
        path = self.commercial_handoffs_dir / f"{handoff['work_id']}.json"
        previous = _json_load(path) if path.exists() else None
        if previous:
            self._assert_commercial_transition(previous["status"], handoff["status"])
            handoff["created_at"] = previous.get("created_at", _utc_now())
        handoff["updated_at"] = _utc_now()
        _write_json_atomic(path, handoff)
        run = self._require_run(handoff["run_id"])
        run.setdefault("metadata", {})["commercial_state"] = self._commercial_run_state(run["run_id"])
        run["updated_at"] = handoff["updated_at"]
        self._write_run_record(run)
        self._append_commercial_event_locked(
            handoff["run_id"],
            event_type or f"handoff.{handoff['status']}",
            actor_agent_id,
            {
                "work_id": handoff["work_id"],
                "consumer_agent_id": handoff["consumer_agent_id"],
                "approval_state": handoff["approval_state"],
            },
        )
        return handoff

    def _commercial_run_state(self, run_id: str) -> str:
        handoffs = self.list_commercial_handoffs(run_id=run_id, limit=10_000)
        if any(item.get("status") in {"blocked", "failed"} for item in handoffs):
            return "blocked"
        if handoffs and all(item.get("status") == "completed" for item in handoffs):
            return "completed"
        return "running"

    def _append_commercial_event_locked(
        self,
        run_id: str,
        event_type: str,
        actor_agent_id: str,
        data: dict,
    ) -> dict:
        event = {
            "event_id": self._new_id("evt"),
            "schema": COMMERCIAL_HANDOFF_SCHEMA,
            "run_id": run_id,
            "event_type": event_type,
            "actor_agent_id": actor_agent_id,
            "at": _utc_now(),
            "data": dict(data),
        }
        with self.commercial_events_file.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(event, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        return event

    def _write_run_record(self, record: dict) -> None:
        _write_json_atomic(self.runs_dir / f"{record['run_id']}.json", record)

    def _coerce_run_request(self, run: KaiRunRequest | dict) -> KaiRunRequest:
        if isinstance(run, KaiRunRequest):
            return run
        if not isinstance(run, dict):
            raise TypeError(f"Unsupported run type: {type(run)!r}")
        allowed = {
            "intent": run.get("intent", ""),
            "workflow": run.get("workflow", ""),
            "brand_id": run.get("brand_id", ""),
            "surface": run.get("surface", "local"),
            "module_set": list(run.get("module_set", [])),
            "inputs": dict(run.get("inputs", {})),
            "metadata": dict(run.get("metadata", {})),
        }
        return KaiRunRequest(**allowed)

    def _coerce_artifact(self, artifact: KaiArtifactRecord | dict) -> dict:
        if isinstance(artifact, KaiArtifactRecord):
            return artifact.model_dump()
        if not isinstance(artifact, dict):
            raise TypeError(f"Unsupported artifact type: {type(artifact)!r}")
        payload = dict(artifact)
        if not payload.get("artifact_type"):
            raise ValueError("artifact_type is required")
        if not payload.get("brand_id"):
            raise ValueError("brand_id is required")
        if not payload.get("workflow"):
            raise ValueError("workflow is required")
        payload.setdefault("module_set", [])
        payload.setdefault("data", {})
        return payload

    def _new_id(self, prefix: str) -> str:
        return f"{prefix}_{uuid.uuid4().hex[:12]}"

    def _lineage_for_parent(self, parent_run_id: Optional[str]) -> List[str]:
        if not parent_run_id:
            return []
        parent = self.get_run(parent_run_id)
        if not parent:
            raise KeyError(f"Parent run not found: {parent_run_id}")
        lineage = list(parent.get("ancestor_run_ids", []))
        lineage.append(parent_run_id)
        return lineage


_DEFAULT_RUNTIME_STORE: Optional[RuntimeStore] = None


def get_default_runtime_store() -> RuntimeStore:
    """Lazily construct the process-wide default runtime store."""
    global _DEFAULT_RUNTIME_STORE
    if _DEFAULT_RUNTIME_STORE is None:
        _DEFAULT_RUNTIME_STORE = RuntimeStore.default()
    return _DEFAULT_RUNTIME_STORE
