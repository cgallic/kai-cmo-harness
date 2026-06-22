#!/usr/bin/env python3
"""Autonomy ledger — append-only, machine-readable record of every run.

Each automation run writes one typed JSON line to ``data/autonomy/ledger.jsonl``.
The ledger is the source of truth for mining repeated failures, successes, and
stale guidance, and for promoting recurring lessons into checklists, gates, and
evals.

Design constraints (mirror ``scripts/quality_gates/gate_logger.py``):
  - Never crash the caller. Logging failures are swallowed.
  - Stdlib only; no new dependencies.
  - Opt out with ``KAI_AUTONOMY_LEDGER=0``; redirect with ``KAI_AUTONOMY_DIR``.

Schema (one object per line):
  run_id          stable id for the run (workflow + UTC timestamp + short uuid)
  workflow        dotted automation name, e.g. "scripts.social.platform_change_monitor"
  started_at      ISO-8601 UTC
  finished_at     ISO-8601 UTC
  inputs          dict of run inputs (filters, flags)
  sources_checked list of source ids / urls inspected
  findings        list of finding dicts (each carries risk_level + decision)
  actions_taken   list of strings describing what the run actually did
  files_changed   list of repo-relative paths written
  validation      dict describing how the run was verified
  risk_level      highest risk across findings ("none"|"low"|"medium"|"high"|"critical")
  requires_human  bool — true if any finding routed to approval/escalate/block
  blockers        list of strings preventing completion
  lessons         list of short, stable lesson signatures for mining
  followups       list of recommended next steps (gate/registry/doc updates)
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

# Ordered low -> high so callers can compare and roll up.
from scripts.autonomy.decisions import RISK_LEVELS  # noqa: E402  (intentional: shared vocabulary)

# Fields a ledger record always carries, in stable order, for readers/tests.
LEDGER_FIELDS: tuple[str, ...] = (
    "run_id",
    "workflow",
    "started_at",
    "finished_at",
    "inputs",
    "sources_checked",
    "findings",
    "actions_taken",
    "files_changed",
    "validation",
    "risk_level",
    "requires_human",
    "blockers",
    "lessons",
    "followups",
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def ledger_path() -> Path:
    """Return the active ledger path, honoring ``KAI_AUTONOMY_DIR``."""
    base = os.environ.get("KAI_AUTONOMY_DIR")
    if base:
        return Path(base) / "ledger.jsonl"
    return REPO_ROOT / "data" / "autonomy" / "ledger.jsonl"


def new_run_id(workflow: str) -> str:
    """Build a sortable, unique run id from the workflow name and current time."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = uuid.uuid4().hex[:8]
    leaf = workflow.rsplit(".", 1)[-1]
    return f"{leaf}-{stamp}-{short}"


def _rollup_risk(findings: list[dict[str, Any]]) -> str:
    """Return the highest risk level present across findings."""
    highest = "none"
    for finding in findings:
        level = finding.get("risk_level", "none")
        if level not in RISK_LEVELS:
            level = "none"
        if RISK_LEVELS.index(level) > RISK_LEVELS.index(highest):
            highest = level
    return highest


def _needs_human(findings: list[dict[str, Any]]) -> bool:
    """True if any finding routed to an action class that requires a person."""
    human_classes = {"stage_for_approval", "escalate", "block"}
    return any(f.get("decision") in human_classes for f in findings)


@dataclass
class LedgerRecord:
    """One automation run. Use :meth:`finish` then :func:`record_run`."""

    workflow: str
    run_id: str = ""
    started_at: str = field(default_factory=_utc_now)
    finished_at: str = ""
    inputs: dict[str, Any] = field(default_factory=dict)
    sources_checked: list[Any] = field(default_factory=list)
    findings: list[dict[str, Any]] = field(default_factory=list)
    actions_taken: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    validation: dict[str, Any] = field(default_factory=dict)
    risk_level: str = "none"
    requires_human: bool = False
    blockers: list[str] = field(default_factory=list)
    lessons: list[str] = field(default_factory=list)
    followups: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.run_id:
            self.run_id = new_run_id(self.workflow)

    def finish(self) -> "LedgerRecord":
        """Stamp completion time and derive ``risk_level`` / ``requires_human``.

        Both derived fields are recomputed from ``findings`` so callers cannot
        forget to set them; an explicit non-default value is preserved only when
        it is stricter than the derived one.
        """
        if not self.finished_at:
            self.finished_at = _utc_now()
        derived_risk = _rollup_risk(self.findings)
        if RISK_LEVELS.index(derived_risk) >= RISK_LEVELS.index(self.risk_level):
            self.risk_level = derived_risk
        self.requires_human = self.requires_human or _needs_human(self.findings)
        return self

    def to_record(self) -> dict[str, Any]:
        data = asdict(self)
        # Emit in stable field order for deterministic, diff-friendly lines.
        return {key: data[key] for key in LEDGER_FIELDS}


def record_run(record: LedgerRecord, path: Path | None = None) -> dict[str, Any] | None:
    """Append a finished run to the ledger. Never raises.

    Returns the written record (useful for tests), or ``None`` when logging is
    disabled or fails.
    """
    if os.environ.get("KAI_AUTONOMY_LEDGER", "1") == "0":
        return None
    try:
        record.finish()
        payload = record.to_record()
        target = path or ledger_path()
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
        return payload
    except Exception:
        return None


def read_records(path: Path | None = None) -> list[dict[str, Any]]:
    """Read every ledger record. Skips malformed lines rather than raising."""
    target = path or ledger_path()
    if not target.exists():
        return []
    records: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def mine_repeated_lessons(
    records: list[dict[str, Any]] | None = None,
    *,
    min_count: int = 2,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Group lesson signatures that recur across runs.

    Returns a list of ``{"lesson", "count", "run_ids", "workflows"}`` sorted by
    descending count. Lessons seen at least ``min_count`` times are candidates
    for promotion (memory -> checklist -> gate/eval), per the issue's promotion
    ladder.
    """
    if records is None:
        records = read_records(path)
    counts: dict[str, dict[str, Any]] = {}
    for rec in records:
        run_id = rec.get("run_id", "")
        workflow = rec.get("workflow", "")
        for lesson in rec.get("lessons", []) or []:
            bucket = counts.setdefault(
                lesson, {"lesson": lesson, "count": 0, "run_ids": [], "workflows": set()}
            )
            bucket["count"] += 1
            bucket["run_ids"].append(run_id)
            bucket["workflows"].add(workflow)
    mined = [
        {
            "lesson": b["lesson"],
            "count": b["count"],
            "run_ids": b["run_ids"],
            "workflows": sorted(b["workflows"]),
        }
        for b in counts.values()
        if b["count"] >= min_count
    ]
    mined.sort(key=lambda b: (-b["count"], b["lesson"]))
    return mined
