"""Memory writeback for approved runs.

After a run is approved, structured learnings are extracted and persisted
into the runtime memory directory so they compound across sessions.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from .store import RuntimeStore


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def write_back_memory(run_id: str, store: "RuntimeStore") -> List[dict]:
    """Extract and persist memory updates from an approved run.

    Returns the list of memory entries that were written.
    """
    run = store.get_run(run_id)
    if not run:
        return []
    if run.get("status") != "approved":
        return []

    artifacts = store.get_run_artifacts(run_id)
    entries = _extract_memory_entries(run_id, run, artifacts)
    if not entries:
        return []

    memory_dir = store.base_dir / "memory"
    memory_dir.mkdir(parents=True, exist_ok=True)

    persisted: List[dict] = []
    for entry in entries:
        entry_id = entry.get("entry_id", f"mem_{run_id}_{len(persisted)}")
        entry["entry_id"] = entry_id
        entry["persisted_at"] = _utc_now()
        path = memory_dir / f"{entry_id}.json"
        path.write_text(json.dumps(entry, indent=2, sort_keys=True), encoding="utf-8")
        persisted.append(entry)

    return persisted


def _extract_memory_entries(
    run_id: str, run: dict, artifacts: List[dict]
) -> List[dict]:
    """Build memory entries from run outputs and learned_pattern artifacts."""
    entries: List[dict] = []
    brand_id = run.get("brand_id", "")
    workflow = run.get("workflow", "")

    # 1. Learned-pattern artifacts become memory entries directly
    for artifact in artifacts:
        if artifact.get("artifact_type") == "learned_pattern":
            entries.append({
                "source_run": run_id,
                "category": "learned_pattern",
                "brand_id": brand_id,
                "workflow": workflow,
                "data": artifact.get("data", {}),
                "artifact_id": artifact.get("artifact_id"),
            })

    # 2. Explicit memory_updates in run outputs
    run_memory = run.get("outputs", {}).get("memory_updates")
    if isinstance(run_memory, list):
        for item in run_memory:
            entries.append({
                "source_run": run_id,
                "category": item.get("category", item.get("type", "run_output")),
                "brand_id": brand_id,
                "workflow": workflow,
                "data": item.get("data", item),
            })

    # 3. Extract implicit learnings from gate reports
    gate_report = run.get("outputs", {}).get("gate_report")
    if isinstance(gate_report, dict):
        winning = _extract_winning_patterns(gate_report)
        if winning:
            entries.append({
                "source_run": run_id,
                "category": "gate_outcome",
                "brand_id": brand_id,
                "workflow": workflow,
                "data": winning,
            })

    return entries


def _extract_winning_patterns(gate_report: dict) -> Optional[dict]:
    """Pull reusable patterns from a passing gate report."""
    score = gate_report.get("score") or gate_report.get("four_us_score")
    grade = gate_report.get("grade")
    if score is None:
        return None
    return {
        "four_us_score": score,
        "grade": grade,
        "violations_resolved": gate_report.get("violations_resolved", []),
        "strengths": gate_report.get("strengths", []),
    }
