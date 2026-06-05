"""SQLite-backed dedupe store keyed by (state, entity_id).

Persists across runs so the same business isn't mailed twice. Records the
priority and pull_date for later cohort analysis.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

SCHEMA = """
CREATE TABLE IF NOT EXISTS seen (
    state      TEXT NOT NULL,
    entity_id  TEXT NOT NULL,
    name       TEXT,
    priority   TEXT,
    place_id   TEXT,
    pull_date  TEXT NOT NULL,
    PRIMARY KEY (state, entity_id)
);
CREATE INDEX IF NOT EXISTS seen_pull_date ON seen (pull_date);
"""


class DedupeStore:
    def __init__(self, path: Path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path))
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def has_seen(self, state: str, entity_id: str) -> bool:
        cur = self.conn.execute(
            "SELECT 1 FROM seen WHERE state=? AND entity_id=?", (state, entity_id)
        )
        return cur.fetchone() is not None

    def record(
        self,
        state: str,
        entity_id: str,
        name: str,
        priority: str,
        place_id: Optional[str],
        pull_date: str,
    ) -> None:
        self.conn.execute(
            "INSERT OR IGNORE INTO seen "
            "(state, entity_id, name, priority, place_id, pull_date) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (state, entity_id, name, priority, place_id, pull_date),
        )

    def commit(self) -> None:
        self.conn.commit()

    def close(self) -> None:
        self.conn.commit()
        self.conn.close()
