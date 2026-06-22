"""Kai autonomy control layer.

The control layer is the part of Kai that decides what a finding means, what
action is allowed, what must be verified, and what needs human approval. It sits
between raw automations (monitors, patchers, publishers) and the systems they
touch.

Modules:
  - ``ledger``    append-only, machine-readable record of every automation run
  - ``decisions`` maps findings to a permitted action class (the policy router)
  - ``impact``    turns raw change signals into practical impact cards

See GitHub issue #27 for the full design and the broader roadmap.
"""

from scripts.autonomy.decisions import (
    ACTION_CLASSES,
    RISK_LEVELS,
    DecisionResult,
    route_decision,
)
from scripts.autonomy.ledger import (
    LedgerRecord,
    mine_repeated_lessons,
    new_run_id,
    read_records,
    record_run,
)

__all__ = [
    "ACTION_CLASSES",
    "RISK_LEVELS",
    "DecisionResult",
    "route_decision",
    "LedgerRecord",
    "mine_repeated_lessons",
    "new_run_id",
    "read_records",
    "record_run",
]
