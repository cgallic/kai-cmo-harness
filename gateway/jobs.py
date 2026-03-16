"""
SQLite-backed job queue with ThreadPoolExecutor for async jobs.
"""

import asyncio
import sqlite3
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .models import JobStatus, JobInfo


class JobQueue:
    """SQLite-backed job queue for async operations."""

    def __init__(self, db_path: Optional[Path] = None, max_workers: int = 4):
        """
        Initialize the job queue.

        Args:
            db_path: Path to SQLite database. Defaults to gateway/jobs.db
            max_workers: Maximum concurrent workers for job execution
        """
        if db_path is None:
            db_path = Path(__file__).parent / "jobs.db"

        self.db_path = db_path
        self.max_workers = max_workers
        self._executor = ThreadPoolExecutor(max_workers=max_workers)
        self._lock = threading.Lock()

        # Initialize database
        self._init_db()

    def _init_db(self):
        """Create the jobs table if it doesn't exist."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
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
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_status ON jobs(status)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_jobs_created ON jobs(created_at)
            """)
            conn.commit()

    def _serialize_json(self, data: Any) -> str:
        """Serialize data to JSON string."""
        import json
        return json.dumps(data) if data else None

    def _deserialize_json(self, data: str) -> Any:
        """Deserialize JSON string to data."""
        import json
        return json.loads(data) if data else None

    def create_job(
        self,
        command: str,
        client: Optional[str] = None,
        options: Optional[Dict] = None
    ) -> str:
        """
        Create a new job in pending state.

        Returns:
            Job ID
        """
        job_id = str(uuid.uuid4())[:8]
        created_at = datetime.utcnow().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO jobs (job_id, command, client, options, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (job_id, command, client, self._serialize_json(options), "pending", created_at)
            )
            conn.commit()

        return job_id

    def get_job(self, job_id: str) -> Optional[JobInfo]:
        """Get job information by ID."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(
                "SELECT * FROM jobs WHERE job_id = ?",
                (job_id,)
            )
            row = cursor.fetchone()

        if not row:
            return None

        return JobInfo(
            job_id=row["job_id"],
            command=row["command"],
            client=row["client"],
            status=JobStatus(row["status"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
            completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
            result=self._deserialize_json(row["result"]),
            error=row["error"]
        )

    def list_jobs(
        self,
        status: Optional[JobStatus] = None,
        limit: int = 50
    ) -> List[JobInfo]:
        """List jobs, optionally filtered by status."""
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row

            if status:
                cursor = conn.execute(
                    "SELECT * FROM jobs WHERE status = ? ORDER BY created_at DESC LIMIT ?",
                    (status.value, limit)
                )
            else:
                cursor = conn.execute(
                    "SELECT * FROM jobs ORDER BY created_at DESC LIMIT ?",
                    (limit,)
                )

            rows = cursor.fetchall()

        return [
            JobInfo(
                job_id=row["job_id"],
                command=row["command"],
                client=row["client"],
                status=JobStatus(row["status"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                started_at=datetime.fromisoformat(row["started_at"]) if row["started_at"] else None,
                completed_at=datetime.fromisoformat(row["completed_at"]) if row["completed_at"] else None,
                result=self._deserialize_json(row["result"]),
                error=row["error"]
            )
            for row in rows
        ]

    def update_job(
        self,
        job_id: str,
        status: Optional[JobStatus] = None,
        started_at: Optional[datetime] = None,
        completed_at: Optional[datetime] = None,
        result: Optional[Dict] = None,
        error: Optional[str] = None
    ):
        """Update job fields."""
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

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                f"UPDATE jobs SET {', '.join(updates)} WHERE job_id = ?",
                values
            )
            conn.commit()

    def submit_job(
        self,
        job_id: str,
        func: Callable,
        *args,
        **kwargs
    ):
        """
        Submit a job for execution in the thread pool.

        The function will be called with the given args/kwargs.
        Result or error will be stored in the job record.
        """
        def run_job():
            # Mark as running
            self.update_job(
                job_id,
                status=JobStatus.RUNNING,
                started_at=datetime.utcnow()
            )

            try:
                # Run the function
                result = func(*args, **kwargs)

                # Handle async functions
                if asyncio.iscoroutine(result):
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    try:
                        result = loop.run_until_complete(result)
                    finally:
                        loop.close()

                # Mark as completed
                self.update_job(
                    job_id,
                    status=JobStatus.COMPLETED,
                    completed_at=datetime.utcnow(),
                    result=result if isinstance(result, dict) else {"result": result}
                )

            except Exception as e:
                # Mark as failed
                self.update_job(
                    job_id,
                    status=JobStatus.FAILED,
                    completed_at=datetime.utcnow(),
                    error=str(e)
                )

        self._executor.submit(run_job)

    def cleanup_old_jobs(self, days: int = 7):
        """Remove jobs older than N days."""
        from datetime import timedelta
        cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                "DELETE FROM jobs WHERE created_at < ?",
                (cutoff,)
            )
            conn.commit()

    def shutdown(self):
        """Shutdown the executor."""
        self._executor.shutdown(wait=True)


# Global job queue instance
job_queue = JobQueue()
