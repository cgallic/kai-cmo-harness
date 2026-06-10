#!/usr/bin/env python3
"""
Gate run logger — persistent JSONL record of every quality-gate run.

Every gate script appends one line per run to data/learning/gate_runs.jsonl.
This is the raw substrate the learning loop mines for repeated failure
signatures (scripts/self_improvement/lesson_capture.py mine).

Design constraints:
  - Never crash the gate. Logging failures are swallowed.
  - No new dependencies. Stdlib only.
  - Opt out with KAI_GATE_LOG=0; redirect with KAI_GATE_LOG_DIR.
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _log_path() -> Path:
    base = os.environ.get("KAI_GATE_LOG_DIR")
    if base:
        return Path(base) / "gate_runs.jsonl"
    return REPO_ROOT / "data" / "learning" / "gate_runs.jsonl"


def log_gate_result(
    gate: str,
    passed: bool,
    source: str | None = None,
    failures: list[str] | None = None,
    warnings: list[str] | None = None,
    stats: dict | None = None,
) -> None:
    """Append one gate run to the learning log. Never raises.

    failures should be short, stable signatures (rule messages or words),
    so the miner can group recurring failures across runs.
    """
    if os.environ.get("KAI_GATE_LOG", "1") == "0":
        return
    try:
        record = {
            "ts": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "gate": gate,
            "passed": passed,
            "source": source or "inline-text",
            "failures": failures or [],
        }
        if warnings:
            record["warnings"] = warnings
        if stats:
            record["stats"] = stats
        path = _log_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass
