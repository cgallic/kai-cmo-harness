"""ECO completion standard — deterministic grading, verdicts, and records.

Doctrine: ``docs/system/eco-completion-standard.md``
Floors:   ``harness/eco-floors.yaml``
CLI:      ``python -m scripts.quality_gates.eco_gate``

The single control this module exists to enforce:

    The actor may submit evidence. The actor may not issue its own verdict.

``EcoRecordStore.claim()`` accepts evidence from a producer and refuses anything
that looks like a self-issued verdict.  ``EcoRecordStore.verify()`` is the only
path that writes the ``computed`` block, and it discards evidence whose verifier
is the actor for every kind that requires independence.

This module deliberately imports nothing from the rest of the repo — only the
stdlib and PyYAML.  It ships inside the Kai plugin, where `kai/` and
`scripts/harness_config.py` are not present, and the gate must still run.
``kai.runtime.eco`` re-exports it for callers inside the full repo.
"""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import yaml


AXES = ("E", "C", "O")

VERDICT_OPEN = "OPEN"
VERDICT_SHIPPED = "SHIPPED"
VERDICT_CLOSED = "CLOSED"

FAILURE_CONDITIONS = ("unproven", "blocked", "failed_attempt")

_FLOORS_RELATIVE = Path("harness") / "eco-floors.yaml"


def _find_install_root() -> Path:
    """Locate the Kai install root from either layout.

    Walks up from this file looking for ``harness/eco-floors.yaml``.  That
    resolves in the repo (``<repo>/scripts/quality_gates/``) and in a plugin
    install (``<plugin>/scripts/quality_gates/``) alike.  Symlinks are walked
    unresolved first so a plugin that symlinks ``scripts/`` back to a checkout
    still finds the plugin's own floors.
    """
    here = Path(__file__).absolute()
    for candidate in (here, here.resolve()):
        for parent in candidate.parents:
            if (parent / _FLOORS_RELATIVE).exists():
                return parent
    return here.resolve().parents[2]


INSTALL_ROOT = _find_install_root()
DEFAULT_FLOORS_PATH = INSTALL_ROOT / _FLOORS_RELATIVE


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _utc_now_iso() -> str:
    return _utc_now().isoformat()


def _parse_ts(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _write_json_atomic(path: Path, payload: Any) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True, default=str), encoding="utf-8")
    tmp_path.replace(path)


class EcoError(ValueError):
    """Raised when a submission violates the ECO contract."""


def _default_runtime_dir() -> Path:
    """Where ECO records live.

    ``KAI_RUNTIME_DIR`` wins.  Inside the full repo the harness config owns the
    data directory; in a plugin-only install that module is absent, so fall back
    to ``<install root>/data/runtime``.
    """
    override = os.environ.get("KAI_RUNTIME_DIR")
    if override:
        return Path(override)
    try:
        from scripts.harness_config import get_config  # type: ignore

        return Path(get_config().data_dir) / "runtime"
    except Exception:
        return INSTALL_ROOT / "data" / "runtime"


# ---------------------------------------------------------------------------
# Floor registry
# ---------------------------------------------------------------------------


@dataclass
class EvidenceKind:
    """One rung of one axis ladder."""

    name: str
    axis: str
    grade: int
    independence_required: bool = False
    requires_fields: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class WorkType:
    """The declared completion floor for a class of marketing work."""

    name: str
    floor: Dict[str, int]
    external_effect: bool = False
    spend_authority: bool = False
    client_facing: bool = False
    composite: bool = False
    shipped_is_terminal: bool = False
    attribution_required: bool = False
    outcome_window_days: int = 30
    craft_gates: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


class EcoFloors:
    """Parsed ``harness/eco-floors.yaml``."""

    def __init__(self, payload: Dict[str, Any]):
        self.raw = payload or {}
        self.schema_version = self.raw.get("schema_version", "kai.eco-floors.v1")
        defaults = self.raw.get("defaults") or {}
        self._default_floor = {"E": 2, "C": 2, "O": 0, **(defaults.get("floor") or {})}
        self._default_window = int(defaults.get("outcome_window_days", 30))
        self._default_gates = list(defaults.get("craft_gates") or [])

        self.evidence_kinds: Dict[str, EvidenceKind] = {}
        for name, spec in (self.raw.get("evidence_kinds") or {}).items():
            spec = spec or {}
            axis = str(spec.get("axis", "")).upper()
            if axis not in AXES:
                raise EcoError(f"evidence kind {name!r} declares unknown axis {axis!r}")
            self.evidence_kinds[name] = EvidenceKind(
                name=name,
                axis=axis,
                grade=int(spec.get("grade", 0)),
                independence_required=bool(spec.get("independence_required", False)),
                requires_fields=list(spec.get("requires_fields") or []),
                description=str(spec.get("description", "")),
            )

        self.work_types: Dict[str, WorkType] = {}
        aliases: Dict[str, str] = {}
        for name, spec in (self.raw.get("work_types") or {}).items():
            spec = spec or {}
            outcome = spec.get("outcome") or {}
            work = WorkType(
                name=name,
                floor={**self._default_floor, **(spec.get("floor") or {})},
                external_effect=bool(spec.get("external_effect", False)),
                spend_authority=bool(spec.get("spend_authority", False)),
                client_facing=bool(spec.get("client_facing", False)),
                composite=bool(spec.get("composite", False)),
                shipped_is_terminal=bool(spec.get("shipped_is_terminal", False)),
                attribution_required=bool(spec.get("attribution_required", False)),
                outcome_window_days=int(outcome.get("window_days", self._default_window)),
                craft_gates=list(spec.get("craft_gates") or self._default_gates),
                raw=spec,
            )
            self.work_types[name] = work
            for alias in spec.get("also_covers") or []:
                aliases[str(alias)] = name
        self._aliases = aliases

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "EcoFloors":
        path = Path(path or os.environ.get("KAI_ECO_FLOORS", DEFAULT_FLOORS_PATH))
        if not path.exists():
            raise EcoError(f"ECO floor registry not found at {path}")
        return cls(yaml.safe_load(path.read_text(encoding="utf-8")) or {})

    def work_type(self, name: str) -> WorkType:
        key = (name or "").strip()
        if key in self.work_types:
            return self.work_types[key]
        if key in self._aliases:
            return self.work_types[self._aliases[key]]
        known = ", ".join(sorted(set(list(self.work_types) + list(self._aliases))))
        raise EcoError(f"unknown work type {name!r}. Known: {known}")

    def kind(self, name: str) -> EvidenceKind:
        if name not in self.evidence_kinds:
            raise EcoError(f"unknown evidence kind {name!r}")
        return self.evidence_kinds[name]


# ---------------------------------------------------------------------------
# Grading
# ---------------------------------------------------------------------------


@dataclass
class GradeResult:
    """What the verifier computed, and why."""

    grade: Dict[str, int]
    accepted: List[Dict[str, Any]]
    rejected: List[Dict[str, Any]]
    violations: List[str]
    unmet: List[str]
    verdict: str
    terminal: bool
    outcome_due_at: Optional[str] = None

    def as_dict(self) -> Dict[str, Any]:
        return {
            "grade": self.grade,
            "verdict": self.verdict,
            "terminal": self.terminal,
            "unmet": self.unmet,
            "violations": self.violations,
            "rejected_evidence": self.rejected,
            "outcome_due_at": self.outcome_due_at,
        }


def _reject(entry: Dict[str, Any], reason: str) -> Dict[str, Any]:
    return {"kind": entry.get("kind"), "locator": entry.get("locator"), "reason": reason}


def grade(
    evidence: Iterable[Dict[str, Any]],
    *,
    work_type: WorkType,
    claimed_by: str,
    floors: EcoFloors,
    now: Optional[datetime] = None,
) -> GradeResult:
    """Compute axis grades and a verdict from submitted evidence.

    Evidence is admitted only when its kind is known, its required fields are
    present, and — for kinds that require independence — its verifier differs
    from the claiming actor.
    """

    now = now or _utc_now()
    accepted: List[Dict[str, Any]] = []
    rejected: List[Dict[str, Any]] = []
    violations: List[str] = []
    grades = {"E": 0, "C": 0, "O": 0}

    for entry in evidence:
        if not isinstance(entry, dict):
            rejected.append({"kind": None, "locator": None, "reason": "evidence entry is not an object"})
            continue
        name = entry.get("kind")
        try:
            kind = floors.kind(str(name))
        except EcoError as exc:
            rejected.append(_reject(entry, str(exc)))
            continue

        missing = [f for f in kind.requires_fields if not entry.get(f)]
        if missing:
            rejected.append(_reject(entry, f"missing required field(s): {', '.join(missing)}"))
            continue

        if kind.independence_required:
            verifier = str(entry.get("verifier") or "").strip()
            if not verifier:
                rejected.append(_reject(entry, "no verifier named; independent evidence requires one"))
                continue
            if verifier.casefold() == str(claimed_by or "").strip().casefold():
                rejected.append(_reject(entry, "verifier is the actor — honest quorum requires a different substrate"))
                continue

        accepted.append(entry)
        grades[kind.axis] = max(grades[kind.axis], kind.grade)

    # --- invariants -------------------------------------------------------

    ship_at = _earliest_ship_timestamp(accepted, floors)

    if work_type.external_effect or work_type.spend_authority:
        if grades["E"] >= 4 and not _has_kind(accepted, "approval_review"):
            violations.append(
                "spend_and_live_channels: external or spend work reached E4+ without hash-pinned approval evidence"
            )

    baseline = _first_kind(accepted, "outcome_baseline")
    if baseline and ship_at:
        observed = _parse_ts(baseline.get("observed_at"))
        if observed and observed > ship_at:
            violations.append(
                "outcome_predeclared: outcome_baseline was recorded after ship — a baseline written after ship is not a baseline"
            )
            grades["O"] = 0

    if work_type.attribution_required and grades["O"] >= 4:
        if not _has_kind(accepted, "outcome_attribution"):
            # O4 stands, but O5 is unreachable without a counterfactual design.
            grades["O"] = min(grades["O"], 4)

    # --- verdict ----------------------------------------------------------

    floor = work_type.floor
    unmet = [f"{axis}{floor[axis]}" for axis in AXES if grades[axis] < floor.get(axis, 0)]

    outcome_due_at = _outcome_due_at(ship_at, baseline, work_type)

    if violations or grades["E"] < floor["E"] or grades["C"] < floor["C"]:
        verdict, terminal = VERDICT_OPEN, False
    elif grades["O"] < floor["O"]:
        verdict, terminal = VERDICT_SHIPPED, False
    elif work_type.shipped_is_terminal:
        verdict, terminal = VERDICT_SHIPPED, True
    else:
        verdict, terminal = VERDICT_CLOSED, True

    return GradeResult(
        grade=grades,
        accepted=accepted,
        rejected=rejected,
        violations=violations,
        unmet=unmet,
        verdict=verdict,
        terminal=terminal,
        outcome_due_at=outcome_due_at,
    )


def _has_kind(entries: Iterable[Dict[str, Any]], kind: str) -> bool:
    return any(e.get("kind") == kind for e in entries)


def _first_kind(entries: Iterable[Dict[str, Any]], kind: str) -> Optional[Dict[str, Any]]:
    for entry in entries:
        if entry.get("kind") == kind:
            return entry
    return None


def _earliest_ship_timestamp(entries: Iterable[Dict[str, Any]], floors: EcoFloors) -> Optional[datetime]:
    """The first moment the work touched its real target (E4 or above)."""
    stamps: List[datetime] = []
    for entry in entries:
        try:
            kind = floors.kind(str(entry.get("kind")))
        except EcoError:
            continue
        if kind.axis == "E" and kind.grade >= 4:
            parsed = _parse_ts(entry.get("observed_at"))
            if parsed:
                stamps.append(parsed)
    return min(stamps) if stamps else None


def _outcome_due_at(
    ship_at: Optional[datetime],
    baseline: Optional[Dict[str, Any]],
    work_type: WorkType,
) -> Optional[str]:
    if ship_at is None:
        return None
    window = work_type.outcome_window_days
    if baseline:
        declared = baseline.get("window_days") or baseline.get("window")
        try:
            window = int(str(declared).rstrip("d"))
        except (TypeError, ValueError):
            pass
    return (ship_at + timedelta(days=window)).isoformat()


# ---------------------------------------------------------------------------
# Record store
# ---------------------------------------------------------------------------


class EcoRecordStore:
    """Append-only ECO records under ``data/runtime/eco/``."""

    def __init__(self, base_dir: Optional[Path] = None, floors: Optional[EcoFloors] = None):
        if base_dir is None:
            base_dir = _default_runtime_dir() / "eco"
        self.base_dir = _ensure_dir(Path(base_dir))
        self.records_dir = _ensure_dir(self.base_dir / "records")
        self.failures_dir = _ensure_dir(self.base_dir / "failures")
        self.floors = floors or EcoFloors.load()
        self._lock = threading.RLock()

    # -- claim ------------------------------------------------------------

    def claim(
        self,
        *,
        subject_id: str,
        step_id: str,
        work_type: str,
        claimed_by: str,
        evidence: Optional[List[Dict[str, Any]]] = None,
        record_id: Optional[str] = None,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record an actor's evidence submission. Never issues a verdict."""

        if payload and "computed" in payload:
            raise EcoError(
                "actor submitted a `computed` block — the actor may submit evidence, "
                "not a verdict. Record rejected."
            )
        if not claimed_by:
            raise EcoError("claimed_by is required: unattributed evidence cannot be graded")

        work = self.floors.work_type(work_type)
        with self._lock:
            record_id = record_id or f"eco-{uuid.uuid4().hex[:12]}"
            path = self._record_path(record_id)
            if path.exists():
                record = json.loads(path.read_text(encoding="utf-8"))
            else:
                record = {
                    "schema_version": "kai.eco-record.v1",
                    "record_id": record_id,
                    "subject_id": subject_id,
                    "step_id": step_id,
                    "work_type": work.name,
                    "floor_required": dict(work.floor),
                    "claimed_by": claimed_by,
                    "claimed_at": _utc_now_iso(),
                    "evidence": [],
                }
            for entry in evidence or []:
                record["evidence"].append(self._stamp(entry))
            record["updated_at"] = _utc_now_iso()
            _write_json_atomic(path, record)
            return record

    def add_evidence(self, record_id: str, entries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Append evidence. Existing entries are never edited or removed."""
        with self._lock:
            record = self.get(record_id)
            record["evidence"].extend(self._stamp(e) for e in entries)
            record["updated_at"] = _utc_now_iso()
            _write_json_atomic(self._record_path(record_id), record)
            return record

    # -- verify -----------------------------------------------------------

    def verify(self, record_id: str, *, verifier: str, now: Optional[datetime] = None) -> Dict[str, Any]:
        """Compute grades and the verdict. The only writer of ``computed``."""

        if not verifier:
            raise EcoError("verifier identity is required")
        with self._lock:
            record = self.get(record_id)
            if verifier.strip().casefold() == str(record.get("claimed_by", "")).strip().casefold():
                raise EcoError(
                    f"verifier {verifier!r} is the claiming actor — the actor may not issue its own verdict"
                )
            work = self.floors.work_type(record.get("work_type", ""))
            result = grade(
                record.get("evidence") or [],
                work_type=work,
                claimed_by=record.get("claimed_by", ""),
                floors=self.floors,
                now=now,
            )
            record["computed"] = {
                **result.as_dict(),
                "verdict_by": verifier,
                "verdict_at": (now or _utc_now()).isoformat(),
            }
            record["updated_at"] = _utc_now_iso()
            _write_json_atomic(self._record_path(record_id), record)
            return record

    # -- failures ---------------------------------------------------------

    def record_failure(
        self,
        *,
        subject_id: str,
        step_id: str,
        actor: str,
        condition: str,
        failed_axis: List[str],
        required_floor: Dict[str, int],
        observed_grade: Dict[str, int],
        next_action: str,
        owner: str,
        verdict_by: str,
        started_at: Optional[str] = None,
        ended_at: Optional[str] = None,
        failed_predicates: Optional[List[str]] = None,
        evidence: Optional[List[str]] = None,
        authoritative_error: str = "",
        retryability: str = "retryable",
        next_check_at: Optional[str] = None,
        attempt_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write the mandatory failure record for an attempt that ended short."""

        if condition not in FAILURE_CONDITIONS:
            raise EcoError(f"condition must be one of {FAILURE_CONDITIONS}, got {condition!r}")
        bad_axes = [a for a in failed_axis if a not in AXES]
        if bad_axes:
            raise EcoError(f"failed_axis must name E, C, or O — got {bad_axes}")
        if not failed_axis:
            raise EcoError("failed_axis is required: a generic red status is not a failure record")
        if not next_action:
            raise EcoError("next_action is required: name the specific action or external condition")
        if not owner:
            raise EcoError("owner is required: an unowned failure is not tracked")

        attempt_id = attempt_id or f"attempt-{uuid.uuid4().hex[:12]}"
        payload = {
            "schema_version": "kai.eco-failure.v1",
            "attempt_id": attempt_id,
            "subject_id": subject_id,
            "step_id": step_id,
            "actor": actor,
            "started_at": started_at or _utc_now_iso(),
            "ended_at": ended_at or _utc_now_iso(),
            "condition": condition,
            "failed_axis": failed_axis,
            "required_floor": required_floor,
            "observed_grade": observed_grade,
            "failed_predicates": failed_predicates or [],
            "evidence": evidence or [],
            "authoritative_error": authoritative_error,
            "retryability": retryability,
            "next_action": next_action,
            "owner": owner,
            "next_check_at": next_check_at,
            "verdict_by": verdict_by,
        }
        with self._lock:
            _write_json_atomic(self.failures_dir / f"{attempt_id}.json", payload)
        return payload

    # -- queries ----------------------------------------------------------

    def get(self, record_id: str) -> Dict[str, Any]:
        path = self._record_path(record_id)
        if not path.exists():
            raise EcoError(f"no ECO record {record_id!r}")
        return json.loads(path.read_text(encoding="utf-8"))

    def list_records(self) -> List[Dict[str, Any]]:
        records = []
        for path in sorted(self.records_dir.glob("*.json")):
            try:
                records.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return records

    def outcome_debt(self, *, now: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """SHIPPED records still carrying an unpaid outcome obligation."""
        now = now or _utc_now()
        debt = []
        for record in self.list_records():
            computed = record.get("computed") or {}
            if computed.get("verdict") != VERDICT_SHIPPED or computed.get("terminal"):
                continue
            due = _parse_ts(computed.get("outcome_due_at"))
            debt.append(
                {
                    "record_id": record.get("record_id"),
                    "subject_id": record.get("subject_id"),
                    "step_id": record.get("step_id"),
                    "work_type": record.get("work_type"),
                    "grade": computed.get("grade"),
                    "unmet": computed.get("unmet"),
                    "outcome_due_at": computed.get("outcome_due_at"),
                    "overdue": bool(due and due <= now),
                }
            )
        return sorted(debt, key=lambda item: (not item["overdue"], item["outcome_due_at"] or ""))

    def failures(self) -> List[Dict[str, Any]]:
        out = []
        for path in sorted(self.failures_dir.glob("*.json")):
            try:
                out.append(json.loads(path.read_text(encoding="utf-8")))
            except json.JSONDecodeError:
                continue
        return out

    # -- internals --------------------------------------------------------

    def _record_path(self, record_id: str) -> Path:
        safe = "".join(ch for ch in record_id if ch.isalnum() or ch in "-_")
        if not safe:
            raise EcoError(f"invalid record id {record_id!r}")
        return self.records_dir / f"{safe}.json"

    @staticmethod
    def _stamp(entry: Dict[str, Any]) -> Dict[str, Any]:
        if not isinstance(entry, dict):
            raise EcoError("evidence entries must be objects")
        stamped = dict(entry)
        stamped.setdefault("observed_at", _utc_now_iso())
        return stamped


__all__ = [
    "AXES",
    "VERDICT_OPEN",
    "VERDICT_SHIPPED",
    "VERDICT_CLOSED",
    "EcoError",
    "EcoFloors",
    "EcoRecordStore",
    "EvidenceKind",
    "GradeResult",
    "WorkType",
    "grade",
]
