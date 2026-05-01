"""SQLite-backed job queue with canonical run and artifact tracking."""

import asyncio
import gc
import json
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from kai.runtime import get_default_runtime_store

from .models import ArtifactType, JobInfo, JobStatus, RunSurface


class JobQueue:
    """SQLite-backed job queue for async operations."""

    def __init__(self, db_path: Optional[Path] = None, max_workers: int = 4):
        """Initialize the job queue."""
        if db_path is None:
            db_path = Path(__file__).parent / "jobs.db"

        self.db_path = db_path
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self):
        """Create the jobs, runs, and artifacts tables if they don't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS jobs (
                    job_id TEXT PRIMARY KEY,
                    command TEXT NOT NULL,
                    client TEXT,
                    options TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    result TEXT,
                    error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    run_id TEXT PRIMARY KEY,
                    job_id TEXT UNIQUE NOT NULL,
                    intent TEXT NOT NULL,
                    workflow TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    surface TEXT NOT NULL DEFAULT 'remote',
                    module_set TEXT,
                    inputs TEXT,
                    metadata TEXT,
                    status TEXT NOT NULL DEFAULT 'pending',
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    result TEXT,
                    error TEXT
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS artifacts (
                    artifact_id TEXT PRIMARY KEY,
                    run_id TEXT NOT NULL,
                    job_id TEXT,
                    artifact_type TEXT NOT NULL,
                    brand_id TEXT NOT NULL,
                    workflow TEXT NOT NULL,
                    module_set TEXT,
                    payload TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (run_id) REFERENCES runs(run_id)
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_status ON runs(status)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_job ON runs(job_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_artifacts_run ON artifacts(run_id)")
            conn.commit()

    def _serialize_json(self, data: Any) -> Optional[str]:
        """Serialize data to JSON string."""
        if data is None:
            return None
        return json.dumps(data)

    def _deserialize_json(self, data: Optional[str]) -> Any:
        """Deserialize JSON string to data."""
        if not data:
            return None
        return json.loads(data)

    def create_job(
        self,
        command: str,
        client: Optional[str] = None,
        options: Optional[Dict] = None,
        run_request: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Create a new job in pending state and seed the canonical run record."""
        job_id = str(uuid.uuid4())[:8]
        created_at = datetime.utcnow().isoformat()
        options = options or {}
        run_request = run_request or {}

        workflow = run_request.get("workflow") or command
        brand_id = run_request.get("brand_id") or client or ""
        surface = run_request.get("surface") or RunSurface.REMOTE.value
        surface = surface.value if isinstance(surface, RunSurface) else surface
        module_set = run_request.get("module_set") or []
        inputs = run_request.get("inputs") or options
        metadata = run_request.get("metadata") or {}
        intent = run_request.get("intent") or f"{workflow} for {brand_id or client or 'unknown'}"

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO jobs (job_id, command, client, options, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, command, client, self._serialize_json(options), JobStatus.PENDING.value, created_at),
            )
            conn.execute(
                """
                INSERT INTO runs (
                    run_id, job_id, intent, workflow, brand_id, surface,
                    module_set, inputs, metadata, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job_id,
                    job_id,
                    intent,
                    workflow,
                    brand_id,
                    surface,
                    self._serialize_json(module_set),
                    self._serialize_json(inputs),
                    self._serialize_json(metadata),
                    JobStatus.PENDING.value,
                    created_at,
                ),
            )
            conn.commit()

        return job_id

    def _fetch_run_row(self, job_id: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM runs WHERE job_id = ? OR run_id = ?",
                (job_id, job_id),
            ).fetchone()
        return dict(row) if row else None

    def _load_artifact_ids(self, run_id: str) -> List[str]:
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(
                "SELECT artifact_id FROM artifacts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            ).fetchall()
            artifact_ids = [row["artifact_id"] for row in rows]
        return artifact_ids

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information by ID, joined with canonical run state."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,),
            ).fetchone()
        row = dict(row) if row else None

        if not row:
            return None

        run = self._fetch_run_row(job_id)
        runtime_run = None
        runtime_artifact_ids: List[str] = []
        lineage_run_ids: List[str] = []
        if run:
            runtime_store = get_default_runtime_store()
            runtime_run = runtime_store.get_run(run["run_id"])
            if runtime_run:
                runtime_artifact_ids = list(runtime_run.get("artifact_ids", []))
                lineage_run_ids = runtime_store.get_run_lineage(run["run_id"])

        artifact_ids = runtime_artifact_ids or (self._load_artifact_ids(run["run_id"]) if run else [])
        surface_value = (
            (runtime_run or {}).get("surface")
            or (run["surface"] if run and run["surface"] else None)
        )
        queue_result = self._deserialize_json(row["result"])
        run_outputs = dict((runtime_run or {}).get("outputs", {}))
        runtime_metadata = dict((runtime_run or {}).get("metadata", {}))
        merged_metadata = self._deserialize_json(run["metadata"]) if run and run["metadata"] else {}
        merged_metadata = {**merged_metadata, **runtime_metadata}
        merged_result = (
            {
                **queue_result,
                "canonical_outputs": run_outputs,
            }
            if isinstance(queue_result, dict) and run_outputs
            else queue_result or run_outputs
        )
        approval_state = None
        if runtime_run:
            approval_state = runtime_run.get("outputs", {}).get("status") or runtime_run.get("status")

        return JobInfo(
            job_id=row["job_id"],
            run_id=run["run_id"] if run else row["job_id"],
            status=JobStatus(row["status"]),
            run_status=(runtime_run or {}).get("status") if runtime_run else (run["status"] if run else None),
            approval_state=approval_state,
            command=row["command"],
            client=row["client"],
            workflow=(runtime_run or {}).get("workflow") or (run["workflow"] if run else row["command"]),
            brand_id=(runtime_run or {}).get("brand_id") or (run["brand_id"] if run else row["client"]),
            surface=RunSurface(surface_value) if surface_value else None,
            module_set=(runtime_run or {}).get("module_set")
            or (self._deserialize_json(run["module_set"]) if run and run["module_set"] else []),
            inputs=(runtime_run or {}).get("inputs")
            or (self._deserialize_json(run["inputs"]) if run and run["inputs"] else self._deserialize_json(row["options"]) or {}),
            metadata=merged_metadata,
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            result=merged_result or (
                self._deserialize_json(run["result"])
                if run and run["result"]
                else None
            ),
            run_outputs=run_outputs,
            runtime_metadata=runtime_metadata,
            error=(runtime_run or {}).get("outputs", {}).get("error") or row["error"],
            lineage_run_ids=lineage_run_ids,
            artifact_ids=artifact_ids,
        )

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> List[JobInfo]:
        """List jobs, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            if status:
                rows = conn.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        rows = [dict(row) for row in rows]

        return [self.get_job(row["job_id"]) or self._row_to_jobinfo(row) for row in rows]

    def list_runs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50,
    ) -> List[JobInfo]:
        """List canonical runs using the same compatibility shape."""
        return self.list_jobs(status=status, limit=limit)

    def _row_to_jobinfo(self, row) -> JobInfo:
        """Fallback conversion for rows when the joined lookup is unavailable."""
        return JobInfo(
            job_id=row["job_id"],
            status=JobStatus(row["status"]),
            command=row["command"],
            client=row["client"],
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            result=self._deserialize_json(row["result"]),
            error=row["error"],
        )

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None,
    ):
        """Update job fields and mirror the state into the canonical run row."""
        updates = []
        values = []

        if status:
            updates.append("status = ?")
            values.append(status.value)
        if started_at:
            updates.append("started_at = ?")
            values.append(started_at.isoformat())
        if completed_at:
            updates.append("completed_at = ?")
            values.append(completed_at.isoformat())
        if result is not None:
            updates.append("result = ?")
            values.append(self._serialize_json(result))
        if error is not None:
            updates.append("error = ?")
            values.append(error)

        if not updates:
            return

        values.append(job_id)

        run_updates = []
        run_values = []
        if status:
            run_updates.append("status = ?")
            run_values.append(status.value)
        if started_at:
            run_updates.append("started_at = ?")
            run_values.append(started_at.isoformat())
        if completed_at:
            run_updates.append("completed_at = ?")
            run_values.append(completed_at.isoformat())
        if result is not None:
            run_updates.append("result = ?")
            run_values.append(self._serialize_json(result))
        if error is not None:
            run_updates.append("error = ?")
            run_values.append(error)

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?",
                values,
            )
            if run_updates:
                conn.execute(
                    f"UPDATE runs SET {', '.join(run_updates)} WHERE job_id = ? OR run_id = ?",
                    run_values + [job_id, job_id],
                )
            conn.commit()

    def submit_job(
        self,
        job_id: str,
        func: Callable,
        *args,
        **kwargs,
    ):
        """Submit a job for execution in the thread pool."""

        def run_job():
            self.update_job(
                job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.utcnow(),
            )

            try:
                result = func(*args, **kwargs)

                if asyncio.iscoroutine(result):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(result)
                    finally:
                        loop.close()

                normalized_result = result if isinstance(result, dict) else {"result": result}
                self.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    completed_at=datetime.utcnow(),
                    result=normalized_result,
                )
            except Exception as exc:
                self.update_job(
                    job_id,
                    status=JobStatus.FAILED,
                    completed_at=datetime.utcnow(),
                    error=str(exc),
                )

        self._executor.submit(run_job)

    def record_artifact(
        self,
        run_id: str,
        artifact_type: Any,
        brand_id: str,
        workflow: str,
        payload: Dict[str, Any],
        *,
        job_id: Optional[str] = None,
        module_set: Optional[List[str]] = None,
    ) -> str:
        """Persist a canonical artifact record."""
        artifact_id = str(uuid.uuid4())[:8]
        created_at = datetime.utcnow().isoformat()
        if isinstance(artifact_type, ArtifactType):
            artifact_type = artifact_type.value

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO artifacts (
                    artifact_id, run_id, job_id, artifact_type,
                    brand_id, workflow, module_set, payload, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    artifact_id,
                    run_id,
                    job_id,
                    artifact_type,
                    brand_id,
                    workflow,
                    self._serialize_json(module_set or []),
                    self._serialize_json(payload) or "{}",
                    created_at,
                ),
            )
            conn.commit()

        return artifact_id

    def list_artifacts(
        self,
        run_id: Optional[str] = None,
        job_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List persisted artifacts."""
        query = "SELECT * FROM artifacts"
        params: tuple[Any, ...] = ()
        if run_id:
            query += " WHERE run_id = ?"
            params = (run_id,)
        elif job_id:
            query += " WHERE job_id = ?"
            params = (job_id,)
        query += " ORDER BY created_at ASC"

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute(query, params).fetchall()
        rows = [dict(row) for row in rows]

        artifacts = []
        for row in rows:
            artifacts.append(
                {
                    "artifact_id": row["artifact_id"],
                    "run_id": row["run_id"],
                    "job_id": row["job_id"],
                    "artifact_type": row["artifact_type"],
                    "brand_id": row["brand_id"],
                    "workflow": row["workflow"],
                    "module_set": self._deserialize_json(row["module_set"]) or [],
                    "payload": self._deserialize_json(row["payload"]) or {},
                    "created_at": row["created_at"],
                }
            )
        return artifacts

    def cleanup_old_jobs(self, days: int = 7):
        """Remove jobs older than N days."""
        from datetime import timedelta

        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM jobs WHERE created_at < ?", (cutoff,))
            conn.execute("DELETE FROM runs WHERE created_at < ?", (cutoff,))
            conn.execute("DELETE FROM artifacts WHERE created_at < ?", (cutoff,))
            conn.commit()

    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=True, cancel_futures=True)
        gc.collect()


job_queue = JobQueue()
