#!/usr/bin/env python3
"""Approval queue — the one canonical hold for risky autonomous actions.

When the decision router (``scripts/autonomy/decisions.py``) routes a finding to
``stage_for_approval``, the action does not happen yet. It lands here: an
append-only queue of items waiting on a human. Outbound email, client-facing
claims, live publishing, paid media, account/credential changes, and deploys all
pass through this gate before they touch the outside world.

Design
------
The queue is an **append-only event log** (``data/autonomy/approval_queue.jsonl``)
folded into current state on read. Every state change — queued, validated,
resolved — is its own line, so the file doubles as an audit trail of who
approved what and when. Nothing is mutated in place.

Two deliberate differences from the ledger
(``scripts/autonomy/ledger.py``):
  - **enqueue raises on persistence failure.** A staged risky action that is
    silently dropped is a safety regression, so we surface the error to the
    caller instead of swallowing it. The ledger swallows because a missing log
    line is harmless; a missing approval item is not.
  - **there is no disable switch.** ``KAI_AUTONOMY_LEDGER=0`` turns off logging;
    there is no equivalent here, because disabling the queue would let risky
    actions through unreviewed. The location can still be redirected with
    ``KAI_AUTONOMY_DIR`` (shared with the ledger).

Schema (one event per line)::

  event           "queued" | "validated" | "resolved"
  item_id         stable id (action_kind + UTC timestamp + short uuid)
  at              ISO-8601 UTC of the event

A ``queued`` event additionally carries the item fields::

  workflow        dotted automation name that staged the action
  action_kind     what the action would do (e.g. "send_email", "paid_spend")
  action_class    routed class (always "stage_for_approval" via the router)
  risk_level      none|low|medium|high|critical
  payload         dict describing the concrete action to perform on approval
  source_refs     list of source ids / urls justifying the action
  decision_reason why the router staged it
  validation      {"status": "unvalidated"|"passed"|"failed", "notes": str}
  dedupe_key      idempotency key; a pending item with the same key blocks re-queue

A ``validated`` event carries ``status`` + ``notes``; a ``resolved`` event
carries ``status`` ("approved"|"rejected"), ``resolved_by``, ``resolution_note``.
"""

from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

from scripts.autonomy.decisions import RISK_LEVELS  # noqa: E402  (shared vocabulary)

VALIDATION_STATES: tuple[str, ...] = ("unvalidated", "passed", "failed")
RESOLUTION_STATES: tuple[str, ...] = ("approved", "rejected")
PENDING = "pending"


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def queue_path() -> Path:
    """Return the active queue path, honoring ``KAI_AUTONOMY_DIR``."""
    base = os.environ.get("KAI_AUTONOMY_DIR")
    if base:
        return Path(base) / "approval_queue.jsonl"
    return REPO_ROOT / "data" / "autonomy" / "approval_queue.jsonl"


def new_item_id(action_kind: str) -> str:
    """Build a sortable, unique id from the action kind and current time."""
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    short = uuid.uuid4().hex[:8]
    leaf = (action_kind or "action").rsplit(".", 1)[-1] or "action"
    return f"{leaf}-{stamp}-{short}"


@dataclass
class ApprovalItem:
    """One risky action waiting on a human decision."""

    workflow: str
    action_kind: str
    item_id: str = ""
    action_class: str = "stage_for_approval"
    risk_level: str = "high"
    payload: dict[str, Any] = field(default_factory=dict)
    source_refs: list[Any] = field(default_factory=list)
    decision_reason: str = ""
    validation: dict[str, Any] = field(default_factory=lambda: {"status": "unvalidated", "notes": ""})
    dedupe_key: str = ""
    created_at: str = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.item_id:
            self.item_id = new_item_id(self.action_kind)
        if self.risk_level not in RISK_LEVELS:
            self.risk_level = "high"
        if self.validation.get("status") not in VALIDATION_STATES:
            self.validation = {"status": "unvalidated", "notes": str(self.validation.get("notes", ""))}
        if not self.dedupe_key:
            self.dedupe_key = self._default_dedupe_key()

    def _default_dedupe_key(self) -> str:
        """Derive a stable key so monthly re-runs don't re-queue the same action."""
        ref = ""
        if self.source_refs:
            ref = str(self.source_refs[0])
        return f"{self.workflow}|{self.action_kind}|{ref}".lower()

    def queued_event(self) -> dict[str, Any]:
        return {
            "event": "queued",
            "item_id": self.item_id,
            "at": self.created_at,
            "workflow": self.workflow,
            "action_kind": self.action_kind,
            "action_class": self.action_class,
            "risk_level": self.risk_level,
            "payload": self.payload,
            "source_refs": self.source_refs,
            "decision_reason": self.decision_reason,
            "validation": self.validation,
            "dedupe_key": self.dedupe_key,
        }


def _append_event(event: dict[str, Any], path: Path) -> dict[str, Any]:
    """Append one event line. Raises on failure (callers depend on durability)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def read_events(path: Path | None = None) -> list[dict[str, Any]]:
    """Read every raw event. Skips malformed lines rather than raising."""
    target = path or queue_path()
    if not target.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in target.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def _fold(events: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Fold the event log into current item state, keyed by item_id."""
    items: dict[str, dict[str, Any]] = {}
    for ev in events:
        kind = ev.get("event")
        item_id = ev.get("item_id")
        if not item_id:
            continue
        if kind == "queued":
            if item_id in items:
                continue  # first queue wins; ignore accidental duplicates
            items[item_id] = {
                "item_id": item_id,
                "created_at": ev.get("at", ""),
                "workflow": ev.get("workflow", ""),
                "action_kind": ev.get("action_kind", ""),
                "action_class": ev.get("action_class", "stage_for_approval"),
                "risk_level": ev.get("risk_level", "high"),
                "payload": ev.get("payload", {}),
                "source_refs": ev.get("source_refs", []),
                "decision_reason": ev.get("decision_reason", ""),
                "validation": ev.get("validation", {"status": "unvalidated", "notes": ""}),
                "dedupe_key": ev.get("dedupe_key", ""),
                "status": PENDING,
                "resolved_at": "",
                "resolved_by": "",
                "resolution_note": "",
            }
        elif kind == "validated":
            item = items.get(item_id)
            if item is not None:
                item["validation"] = {
                    "status": ev.get("status", "unvalidated"),
                    "notes": ev.get("notes", ""),
                }
        elif kind == "resolved":
            item = items.get(item_id)
            if item is not None:
                item["status"] = ev.get("status", item["status"])
                item["resolved_at"] = ev.get("at", "")
                item["resolved_by"] = ev.get("resolved_by", "")
                item["resolution_note"] = ev.get("resolution_note", "")
    return items


def read_items(path: Path | None = None, *, status: str | None = None) -> list[dict[str, Any]]:
    """Return folded items, oldest first, optionally filtered by status."""
    items = list(_fold(read_events(path)).values())
    if status is not None:
        items = [i for i in items if i["status"] == status]
    items.sort(key=lambda i: (i.get("created_at", ""), i.get("item_id", "")))
    return items


def get_item(item_id: str, path: Path | None = None) -> dict[str, Any] | None:
    """Return one folded item by id, or ``None`` if it was never queued."""
    return _fold(read_events(path)).get(item_id)


def list_pending(path: Path | None = None) -> list[dict[str, Any]]:
    """Return every item still waiting on a human, oldest first."""
    return read_items(path, status=PENDING)


def enqueue(item: ApprovalItem, path: Path | None = None) -> dict[str, Any] | None:
    """Append a queued event for ``item``. Returns the event, or ``None`` if a
    pending item with the same ``dedupe_key`` already exists.

    Raises on persistence failure — a dropped approval item is unsafe, so the
    error reaches the caller rather than being swallowed (see module docstring).
    """
    target = path or queue_path()
    if item.dedupe_key:
        for existing in _fold(read_events(target)).values():
            if existing["status"] == PENDING and existing.get("dedupe_key") == item.dedupe_key:
                return None
    return _append_event(item.queued_event(), target)


def record_validation(
    item_id: str,
    status: str,
    notes: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    """Record a validation outcome for a queued item.

    ``status`` must be one of ``VALIDATION_STATES``. Raises if the item is
    unknown.
    """
    if status not in VALIDATION_STATES:
        raise ValueError(f"validation status must be one of {VALIDATION_STATES}, got {status!r}")
    target = path or queue_path()
    if get_item(item_id, target) is None:
        raise ValueError(f"unknown approval item: {item_id}")
    return _append_event(
        {"event": "validated", "item_id": item_id, "at": _utc_now(), "status": status, "notes": notes},
        target,
    )


def resolve(
    item_id: str,
    status: str,
    resolved_by: str,
    resolution_note: str = "",
    path: Path | None = None,
) -> dict[str, Any]:
    """Approve or reject a pending item. Append-only; the queued line stays.

    ``status`` must be ``approved`` or ``rejected``. Raises if the item is
    unknown or already resolved (re-resolving would muddy the audit trail).
    """
    if status not in RESOLUTION_STATES:
        raise ValueError(f"resolution status must be one of {RESOLUTION_STATES}, got {status!r}")
    target = path or queue_path()
    item = get_item(item_id, target)
    if item is None:
        raise ValueError(f"unknown approval item: {item_id}")
    if item["status"] != PENDING:
        raise ValueError(f"item {item_id} already resolved as {item['status']!r}")
    return _append_event(
        {
            "event": "resolved",
            "item_id": item_id,
            "at": _utc_now(),
            "status": status,
            "resolved_by": resolved_by,
            "resolution_note": resolution_note,
        },
        target,
    )


def approve(item_id: str, resolved_by: str, resolution_note: str = "", path: Path | None = None) -> dict[str, Any]:
    """Convenience wrapper: resolve ``item_id`` as approved."""
    return resolve(item_id, "approved", resolved_by, resolution_note, path)


def reject(item_id: str, resolved_by: str, resolution_note: str = "", path: Path | None = None) -> dict[str, Any]:
    """Convenience wrapper: resolve ``item_id`` as rejected."""
    return resolve(item_id, "rejected", resolved_by, resolution_note, path)


def stage_finding(
    finding: dict[str, Any],
    workflow: str,
    *,
    payload: dict[str, Any] | None = None,
    source_refs: list[Any] | None = None,
    dedupe_key: str = "",
    path: Path | None = None,
) -> dict[str, Any] | None:
    """Enqueue a finding **only if** the router staged it for approval.

    Returns the queued event, or ``None`` when the finding's ``decision`` is not
    ``stage_for_approval`` or a matching pending item already exists. This is the
    intended bridge from ``route_decision`` output to the queue.
    """
    if finding.get("decision") != "stage_for_approval":
        return None
    refs = source_refs if source_refs is not None else _finding_source_refs(finding)
    item = ApprovalItem(
        workflow=workflow,
        action_kind=(finding.get("action_kind") or "review").strip().lower(),
        action_class="stage_for_approval",
        risk_level=finding.get("risk_level", "high"),
        payload=payload if payload is not None else _finding_payload(finding),
        source_refs=refs,
        decision_reason=finding.get("decision_reason", ""),
        dedupe_key=dedupe_key,
    )
    return enqueue(item, path)


def stage_findings(
    findings: list[dict[str, Any]],
    workflow: str,
    *,
    path: Path | None = None,
) -> list[dict[str, Any]]:
    """Enqueue every finding routed to ``stage_for_approval``. Returns the events
    actually written (deduped/non-staged findings are skipped)."""
    staged: list[dict[str, Any]] = []
    for finding in findings:
        event = stage_finding(finding, workflow, path=path)
        if event is not None:
            staged.append(event)
    return staged


def _finding_source_refs(finding: dict[str, Any]) -> list[Any]:
    refs = [finding.get("source_url"), finding.get("id")]
    return [r for r in refs if r]


def _finding_payload(finding: dict[str, Any]) -> dict[str, Any]:
    return {
        "title": finding.get("title"),
        "action_taken": finding.get("action_taken"),
        "next_step": finding.get("next_step"),
        "what_changed": finding.get("what_changed"),
    }
