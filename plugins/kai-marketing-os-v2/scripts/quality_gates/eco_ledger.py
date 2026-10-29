"""ECO outcome ledger — every shipped change and how it turned out, misses included.

Doctrine: "Outcome verdicts" in ``docs/system/eco-completion-standard.md``
CLI:      ``python -m scripts.quality_gates.eco_gate ledger --format md|json``

The ledger reads ``computed.outcome.verdict`` on each ticketed ECO record. It
never infers a verdict from CLOSED: a record can be CLOSED on a didn't-work
read, because CLOSED means measured, not won.

Like ``eco_core``, this module imports only the stdlib and PyYAML (through
``eco_core``) so it ships inside the Kai plugin.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

try:
    from scripts.quality_gates.eco_core import (
        OUTCOME_DIDNT_WORK,
        OUTCOME_INCONCLUSIVE,
        OUTCOME_PARTIAL,
        OUTCOME_VERDICTS,
        OUTCOME_WORKED,
        EcoFloors,
        _parse_ts,
        ticket_measurable,
    )
except ModuleNotFoundError as exc:
    if exc.name == "yaml":
        raise
    sys.path.insert(0, str(Path(__file__).absolute().parent))
    from eco_core import (  # type: ignore[no-redef]
        OUTCOME_DIDNT_WORK,
        OUTCOME_INCONCLUSIVE,
        OUTCOME_PARTIAL,
        OUTCOME_VERDICTS,
        OUTCOME_WORKED,
        EcoFloors,
        _parse_ts,
        ticket_measurable,
    )

PENDING = "pending"
UNMEASURABLE = "unmeasurable"
STATUSES = OUTCOME_VERDICTS + (PENDING, UNMEASURABLE)

_LABELS = {
    OUTCOME_WORKED: "worked",
    OUTCOME_PARTIAL: "partial",
    OUTCOME_DIDNT_WORK: "didn't work",
    OUTCOME_INCONCLUSIVE: "inconclusive",
    PENDING: "pending",
    UNMEASURABLE: "unmeasurable",
}


def _row(record: Dict[str, Any]) -> Dict[str, Any]:
    ticket = record.get("ticket") or {}
    computed = record.get("computed") or {}
    outcome = computed.get("outcome") or {}
    reads = len(ticket.get("reads") or [])
    if not ticket_measurable(ticket):
        status, reason = UNMEASURABLE, ticket.get("unmeasurable_reason") or "no pre-ship baseline"
    elif outcome.get("final") and outcome.get("reads") == reads:
        status, reason = outcome.get("verdict"), outcome.get("reason")
    else:
        status = PENDING
        reason = outcome.get("reason") if outcome else f"{reads} of {ticket.get('max_reads')} read(s) taken"
    return {
        "record_id": record.get("record_id"),
        "subject_id": record.get("subject_id"),
        "work_type": record.get("work_type"),
        "brand_id": ticket.get("brand_id"),
        "shipped_at": ticket.get("shipped_at"),
        "status": status,
        "reason": reason,
        "metric": ticket.get("metric"),
        "source": ticket.get("source"),
        "baseline": outcome.get("baseline"),
        "observed": outcome.get("observed"),
        "threshold": outcome.get("threshold"),
        "lift": outcome.get("lift"),
        "reads": reads,
        "window_days": ticket.get("window_days"),
        "verdict_by": outcome.get("verdict_by"),
        "next_check_at": outcome.get("next_check_at"),
        "eco_verdict": computed.get("verdict"),
    }


def build_ledger(
    records: Iterable[Dict[str, Any]],
    *,
    brand: Optional[str] = None,
    since: Optional[str] = None,
    floors: Optional[EcoFloors] = None,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Tally ticketed records into a ledger. ``since`` filters on ship date."""
    since_dt = _parse_ts(since) if since else None
    if since and since_dt is None:
        raise ValueError(f"--since must be an ISO date, got {since!r}")
    rows = []
    for record in records:
        if not record.get("ticket"):
            continue
        row = _row(record)
        if brand and row["brand_id"] != brand:
            continue
        shipped = _parse_ts(row["shipped_at"])
        if since_dt and (shipped is None or shipped < since_dt):
            continue
        rows.append(row)
    rows.sort(key=lambda r: r["shipped_at"] or "")

    tally = {status: 0 for status in STATUSES}
    by_work_type: Dict[str, Dict[str, int]] = {}
    for row in rows:
        tally[row["status"]] = tally.get(row["status"], 0) + 1
        bucket = by_work_type.setdefault(row["work_type"], {status: 0 for status in STATUSES})
        bucket[row["status"]] = bucket.get(row["status"], 0) + 1
    decided = tally[OUTCOME_WORKED] + tally[OUTCOME_PARTIAL] + tally[OUTCOME_DIDNT_WORK]

    return {
        "schema_version": "kai.eco-ledger.v1",
        "generated_at": (now or datetime.now(timezone.utc)).isoformat(),
        "filters": {"brand": brand, "since": since},
        "tickets": len(rows),
        "tally": tally,
        "win_rate": round(tally[OUTCOME_WORKED] / decided, 3) if decided else None,
        "by_work_type": by_work_type,
        "misses": [r for r in rows if r["status"] in (OUTCOME_PARTIAL, OUTCOME_DIDNT_WORK)],
        "inconclusive": [r for r in rows if r["status"] == OUTCOME_INCONCLUSIVE],
        "unmeasurable": [r for r in rows if r["status"] == UNMEASURABLE],
        "rows": rows,
        "method": _method(floors),
    }


def _method(floors: Optional[EcoFloors]) -> Dict[str, Any]:
    windows = {}
    if floors is not None:
        windows = {
            name: wt.verdict_window_days
            for name, wt in sorted(floors.work_types.items())
            if wt.verdict_window_days
        }
    return {
        "counted": (
            "Every shipped change registered as an ECO outcome ticket — content publishes, "
            "executed actions, and manual `eco_gate register` calls — inside the filters."
        ),
        "not_counted": (
            "Work never registered as a ticket (`eco_gate unregistered` lists what is cheaply "
            "discoverable), dry runs, drafts, and approvals that never shipped. Unmeasurable "
            "tickets are listed with their reason, never scored."
        ),
        "comparison": (
            "Equal-length windows before and after ship, read from the same source at the same "
            "scope. Read k uses k x the verdict window; an inconclusive read is re-run until "
            "max_reads, then it is final inconclusive."
        ),
        "windows_days": windows,
        "verdicts": {
            OUTCOME_WORKED: "cleared the threshold predeclared at registration",
            OUTCOME_PARTIAL: "moved the right way, missed the threshold",
            OUTCOME_DIDNT_WORK: "flat or moved the wrong way",
            OUTCOME_INCONCLUSIVE: "data gap or sample below the minimum — never read as zero",
        },
        "verifier": (
            "Reads are taken and verdicts issued by `kai-measure:<source>`, never by the actor "
            "that shipped the work; each row names its verdict_by."
        ),
        "attribution": (
            "A verdict is a before/after comparison, not causal attribution. Seasonality and "
            "concurrent changes are not controlled."
        ),
        "audit": (
            "Not third-party audited. Computed from the ECO records in this workspace; anyone "
            "holding them can recompute it."
        ),
        "disclosure": (
            "Results come from the businesses whose data was read. Where the operator owns the "
            "business measured, the result is self-reported, not independent evidence."
        ),
    }


def render_json(ledger: Dict[str, Any]) -> str:
    return json.dumps(ledger, indent=2, sort_keys=True, default=str)


def _fmt(value: Any) -> str:
    if value is None:
        return "—"
    if isinstance(value, float):
        return f"{value:g}"
    return str(value)


def _lift(value: Any) -> str:
    return "—" if value is None else f"{value * 100:+.1f}%"


def render_markdown(ledger: Dict[str, Any]) -> str:
    tally = ledger["tally"]
    filters = ", ".join(f"{k}={v}" for k, v in ledger["filters"].items() if v) or "none"
    lines = [
        "# ECO outcome ledger",
        "",
        f"Generated {ledger['generated_at']} · filters: {filters} · {ledger['tickets']} ticket(s)",
        "",
        "| Verdict | Count |",
        "|---|---:|",
    ]
    for status in STATUSES:
        lines.append(f"| {_LABELS[status]} | {tally.get(status, 0)} |")
    rate = ledger["win_rate"]
    lines += ["", f"Win rate (worked / decided): {'—' if rate is None else f'{rate * 100:.0f}%'}", ""]

    if ledger["by_work_type"]:
        lines += ["## By work type", "", "| Work type | " + " | ".join(_LABELS[s] for s in STATUSES) + " |",
                  "|---|" + "---:|" * len(STATUSES)]
        for name, counts in sorted(ledger["by_work_type"].items()):
            lines.append(f"| {name} | " + " | ".join(str(counts.get(s, 0)) for s in STATUSES) + " |")
        lines.append("")

    def table(title: str, rows: List[Dict[str, Any]]) -> None:
        lines.extend([f"## {title}", ""])
        if not rows:
            lines.extend(["None.", ""])
            return
        lines.append("| Shipped | Subject | Work type | Verdict | Metric | Before | After | Lift | Reason |")
        lines.append("|---|---|---|---|---|---:|---:|---:|---|")
        for r in rows:
            lines.append(
                f"| {(r['shipped_at'] or '')[:10]} | {r['subject_id']} | {r['work_type']} | "
                f"{_LABELS.get(r['status'], r['status'])} | {_fmt(r['metric'])} | {_fmt(r['baseline'])} | "
                f"{_fmt(r['observed'])} | {_lift(r['lift'])} | {_fmt(r['reason'])} |"
            )
        lines.append("")

    table("Misses (partial and didn't work)", ledger["misses"])
    table("Inconclusive", ledger["inconclusive"])
    table("Unmeasurable", ledger["unmeasurable"])
    table("All tickets", ledger["rows"])

    method = ledger["method"]
    lines += ["## Method", ""]
    for key in ("counted", "not_counted", "comparison", "verifier", "attribution", "audit", "disclosure"):
        lines.append(f"- **{key.replace('_', ' ').capitalize()}.** {method[key]}")
    if method["windows_days"]:
        windows = ", ".join(f"{k} {v}d" for k, v in method["windows_days"].items())
        lines.append(f"- **Verdict windows.** {windows}")
    lines.append("- **Verdicts.** " + "; ".join(f"{_LABELS[k]}: {v}" for k, v in method["verdicts"].items()))
    lines.append("")
    return "\n".join(lines)


__all__ = ["build_ledger", "render_json", "render_markdown", "PENDING", "UNMEASURABLE", "STATUSES"]
