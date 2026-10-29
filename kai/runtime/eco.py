"""ECO completion standard — runtime re-export.

The implementation lives in ``scripts/quality_gates/eco_core.py`` because it
must run inside the Kai plugin, where the ``kai`` package is not installed.
This module is the import path for callers inside the full repo.

Doctrine: ``docs/system/eco-completion-standard.md``
Floors:   ``harness/eco-floors.yaml``
CLI:      ``python -m scripts.quality_gates.eco_gate``

    The actor may submit evidence. The actor may not issue its own verdict.
"""

from __future__ import annotations

from scripts.quality_gates.eco_core import (  # noqa: F401
    AXES,
    DEFAULT_FLOORS_PATH,
    FAILURE_CONDITIONS,
    INSTALL_ROOT,
    OUTCOME_DIDNT_WORK,
    OUTCOME_INCONCLUSIVE,
    OUTCOME_PARTIAL,
    OUTCOME_VERDICTS,
    OUTCOME_WORKED,
    VERDICT_CLOSED,
    VERDICT_OPEN,
    VERDICT_SHIPPED,
    EcoError,
    EcoFloors,
    EcoRecordStore,
    EvidenceKind,
    GradeResult,
    WorkType,
    grade,
    outcome_verdict,
    ticket_measurable,
    ticket_threshold,
)
from scripts.quality_gates.eco_ledger import build_ledger, render_json, render_markdown  # noqa: F401

__all__ = [
    "AXES",
    "DEFAULT_FLOORS_PATH",
    "FAILURE_CONDITIONS",
    "INSTALL_ROOT",
    "OUTCOME_DIDNT_WORK",
    "OUTCOME_INCONCLUSIVE",
    "OUTCOME_PARTIAL",
    "OUTCOME_VERDICTS",
    "OUTCOME_WORKED",
    "VERDICT_CLOSED",
    "VERDICT_OPEN",
    "VERDICT_SHIPPED",
    "EcoError",
    "EcoFloors",
    "EcoRecordStore",
    "EvidenceKind",
    "GradeResult",
    "WorkType",
    "build_ledger",
    "grade",
    "outcome_verdict",
    "render_json",
    "render_markdown",
    "ticket_measurable",
    "ticket_threshold",
]
