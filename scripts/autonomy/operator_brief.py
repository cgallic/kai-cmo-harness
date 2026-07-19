#!/usr/bin/env python3
"""Weekly operator brief — a decision, not a dump.

The ledger and approval queue accumulate raw runs. An operator does not want raw
runs; they want the few things that need a human this week. This module reads the
autonomy ledger (``scripts/autonomy/ledger.py``) and the approval queue
(``scripts/autonomy/approval_queue.py``) and renders a short, decision-oriented
brief:

  - biggest risks            high/critical findings across runs
  - approvals needed         pending items in the approval queue
  - actions taken            what automations actually did
  - failed automations       runs that recorded blockers
  - stale docs / broken      unresolved sources and stale owner docs
  - suggested upgrades       lessons that recurred enough to promote

Everything is derived; nothing new is asserted. Quantitative lines come straight
from the ledger/queue, so the brief never invents numbers (Kai Data Provenance
Rule). Stdlib only; no network.

Usage:
  python -m scripts.autonomy.operator_brief
  python -m scripts.autonomy.operator_brief --since 7
  python -m scripts.autonomy.operator_brief --out reports/operator-brief.md
"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]

from scripts.autonomy.approval_queue import list_pending, read_items
from scripts.autonomy.decisions import RISK_LEVELS
from scripts.autonomy.ledger import mine_repeated_lessons, read_records

_HIGH_RISK = {"high", "critical"}


def _parse_dt(value: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value)
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


def _within_window(records: list[dict[str, Any]], since_days: int | None) -> list[dict[str, Any]]:
    """Keep records started within ``since_days``. Undated records are kept."""
    if not since_days:
        return records
    cutoff = datetime.now(timezone.utc) - timedelta(days=since_days)
    kept = []
    for rec in records:
        started = _parse_dt(rec.get("started_at", ""))
        if started is None or started >= cutoff:
            kept.append(rec)
    return kept


def brief_data(
    *,
    records: list[dict[str, Any]] | None = None,
    pending: list[dict[str, Any]] | None = None,
    since_days: int | None = 7,
    ledger_path: Path | None = None,
    queue_path: Path | None = None,
) -> dict[str, Any]:
    """Assemble the structured brief data from the ledger and approval queue.

    Inputs can be injected (tests) or read from disk. Returns a dict with one key
    per brief section plus a ``summary`` rollup.
    """
    if records is None:
        records = read_records(ledger_path)
    records = _within_window(records, since_days)
    if pending is None:
        pending = list_pending(queue_path)

    biggest_risks: list[dict[str, Any]] = []
    actions_taken: list[dict[str, Any]] = []
    failed: list[dict[str, Any]] = []
    stale_sources: list[dict[str, Any]] = []

    for rec in records:
        run_id = rec.get("run_id", "")
        workflow = rec.get("workflow", "")
        for finding in rec.get("findings", []) or []:
            if finding.get("risk_level") in _HIGH_RISK or finding.get("decision") in {"escalate", "block"}:
                biggest_risks.append(
                    {
                        "run_id": run_id,
                        "workflow": workflow,
                        "title": finding.get("title") or finding.get("id") or "(untitled finding)",
                        "risk_level": finding.get("risk_level", "low"),
                        "decision": finding.get("decision", ""),
                        "why_it_matters": finding.get("why_it_matters", ""),
                        "source_url": finding.get("source_url", ""),
                    }
                )
            if finding.get("source_status") == "unresolved":
                stale_sources.append(
                    {
                        "run_id": run_id,
                        "workflow": workflow,
                        "title": finding.get("title") or finding.get("id") or "(unknown source)",
                        "source_url": finding.get("source_url", ""),
                        "next_step": finding.get("next_step", ""),
                    }
                )
        for action in rec.get("actions_taken", []) or []:
            actions_taken.append({"run_id": run_id, "workflow": workflow, "action": action})
        if rec.get("blockers"):
            failed.append(
                {
                    "run_id": run_id,
                    "workflow": workflow,
                    "blockers": list(rec.get("blockers", [])),
                }
            )

    biggest_risks.sort(key=lambda r: -_risk_rank(r["risk_level"]))
    pending_sorted = sorted(pending, key=lambda i: -_risk_rank(i.get("risk_level", "low")))
    upgrades = mine_repeated_lessons(records, min_count=2)

    summary = {
        "runs_considered": len(records),
        "biggest_risks": len(biggest_risks),
        "approvals_needed": len(pending_sorted),
        "failed_automations": len(failed),
        "stale_or_broken_sources": len(stale_sources),
        "promotion_candidates": len(upgrades),
        "since_days": since_days,
    }
    return {
        "summary": summary,
        "biggest_risks": biggest_risks,
        "approvals_needed": pending_sorted,
        "actions_taken": actions_taken,
        "failed_automations": failed,
        "stale_or_broken_sources": stale_sources,
        "suggested_upgrades": upgrades,
    }


def _risk_rank(level: str) -> int:
    return RISK_LEVELS.index(level) if level in RISK_LEVELS else 1


def render_brief(data: dict[str, Any]) -> str:
    """Render the structured brief data as operator-facing markdown."""
    summary = data["summary"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    window = f"last {summary['since_days']} days" if summary.get("since_days") else "all time"

    lines: list[str] = [
        "# Kai Operator Brief",
        "",
        f"Generated: {now} · Window: {window}",
        "",
        "## At a glance",
        "",
        f"- Runs considered: {summary['runs_considered']}",
        f"- Biggest risks: {summary['biggest_risks']}",
        f"- Approvals needed: {summary['approvals_needed']}",
        f"- Failed automations: {summary['failed_automations']}",
        f"- Stale/broken sources: {summary['stale_or_broken_sources']}",
        f"- Promotion candidates: {summary['promotion_candidates']}",
        "",
    ]

    lines.append("## Approvals needed")
    lines.append("")
    if data["approvals_needed"]:
        for item in data["approvals_needed"]:
            val = item.get("validation", {}) or {}
            lines.append(
                f"- `{item.get('risk_level', 'low')}` **{item.get('action_kind', 'action')}** "
                f"({item.get('workflow', '')}) — {item.get('decision_reason', '')}"
            )
            lines.append(
                f"  - id: `{item.get('item_id', '')}` · validation: {val.get('status', 'unvalidated')}"
            )
            if item.get("source_refs"):
                lines.append(f"  - sources: {', '.join(str(s) for s in item['source_refs'])}")
    else:
        lines.append("- None waiting.")
    lines.append("")

    lines.append("## Biggest risks")
    lines.append("")
    if data["biggest_risks"]:
        for risk in data["biggest_risks"]:
            lines.append(
                f"- `{risk['risk_level']}` **{risk['title']}** ({risk['workflow']}) "
                f"→ `{risk['decision']}`"
            )
            if risk.get("why_it_matters"):
                lines.append(f"  - {risk['why_it_matters']}")
            if risk.get("source_url"):
                lines.append(f"  - source: {risk['source_url']}")
    else:
        lines.append("- No high/critical findings this window.")
    lines.append("")

    lines.append("## Failed automations")
    lines.append("")
    if data["failed_automations"]:
        for fail in data["failed_automations"]:
            lines.append(f"- **{fail['workflow']}** (`{fail['run_id']}`)")
            for blocker in fail["blockers"]:
                lines.append(f"  - {blocker}")
    else:
        lines.append("- None.")
    lines.append("")

    lines.append("## Stale docs / broken sources")
    lines.append("")
    if data["stale_or_broken_sources"]:
        for src in data["stale_or_broken_sources"]:
            lines.append(f"- **{src['title']}** ({src['workflow']}) — {src.get('source_url', '')}")
            if src.get("next_step"):
                lines.append(f"  - next: {src['next_step']}")
    else:
        lines.append("- None flagged.")
    lines.append("")

    lines.append("## Suggested upgrades (recurring lessons)")
    lines.append("")
    if data["suggested_upgrades"]:
        for up in data["suggested_upgrades"]:
            workflows = ", ".join(up.get("workflows", []))
            lines.append(f"- {up['count']}× **{up['lesson']}** (workflows: {workflows})")
        lines.append("")
        lines.append(
            "Promotion ladder: ledger → `memory/lessons.md` → checklist/doctrine → gate/eval → golden test."
        )
    else:
        lines.append("- No lesson has recurred enough to promote yet.")
    lines.append("")

    lines.append("## Actions taken")
    lines.append("")
    if data["actions_taken"]:
        for act in data["actions_taken"]:
            lines.append(f"- [{act['workflow']}] {act['action']}")
    else:
        lines.append("- No actions recorded this window.")
    lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def build_brief(
    *,
    since_days: int | None = 7,
    ledger_path: Path | None = None,
    queue_path: Path | None = None,
) -> str:
    """Read the ledger + queue and return the rendered markdown brief."""
    data = brief_data(since_days=since_days, ledger_path=ledger_path, queue_path=queue_path)
    return render_brief(data)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate the Kai operator brief from the autonomy ledger")
    parser.add_argument("--since", type=int, default=7, help="Only consider runs from the last N days (0 = all)")
    parser.add_argument("--out", help="Write the brief to this path instead of stdout")
    args = parser.parse_args(argv)

    since = args.since if args.since and args.since > 0 else None
    brief = build_brief(since_days=since)

    if args.out:
        out = Path(args.out)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(brief, encoding="utf-8")
        print(f"Wrote operator brief to {out}")
    else:
        print(brief)
    return 0


if __name__ == "__main__":
    sys.exit(main())
