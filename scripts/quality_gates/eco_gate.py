#!/usr/bin/env python3
"""ECO gate — the only thing allowed to issue a completion verdict.

Doctrine: docs/system/eco-completion-standard.md
Floors:   harness/eco-floors.yaml

    The actor may submit evidence. The actor may not issue its own verdict.

Subcommands
-----------
  floors                     Show the declared floor for every work type
  claim                      Submit evidence for a work item (no verdict)
  verify                     Compute grades and issue SHIPPED / CLOSED / OPEN
  status                     Show one record
  debt                       List SHIPPED items with unpaid outcome obligations
  fail                       Write the mandatory failure record
  register                   Open an outcome ticket for shipped work (idempotent per subject)
  unregistered               List published content / executed actions with no ticket
  ledger                     Outcome verdict ledger: tally, misses, method (--format md|json)

Exit codes
----------
  0  verdict met the declared floor (SHIPPED or CLOSED), or the query succeeded
  1  the work item is still open — floor not met
  2  the submission violated the ECO contract (bad input, self-verdict)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:  # full repo, or plugin install with `scripts` on the path
    from scripts.quality_gates.eco_core import (
        VERDICT_CLOSED,
        VERDICT_SHIPPED,
        EcoError,
        EcoFloors,
        EcoRecordStore,
    )
    from scripts.quality_gates.eco_ledger import build_ledger, render_json, render_markdown
except ModuleNotFoundError as exc:
    if exc.name == "yaml":
        print(
            "\n  The ECO gate needs PyYAML to read harness/eco-floors.yaml.\n"
            "  Install it with: pip install pyyaml\n",
            file=sys.stderr,
        )
        sys.exit(2)
    # Run directly from inside scripts/quality_gates/ — `scripts` is not a package here.
    sys.path.insert(0, str(Path(__file__).absolute().parent))
    from eco_core import (  # type: ignore[no-redef]
        VERDICT_CLOSED,
        VERDICT_SHIPPED,
        EcoError,
        EcoFloors,
        EcoRecordStore,
    )
    from eco_ledger import build_ledger, render_json, render_markdown  # type: ignore[no-redef]


def _load_json_arg(value):
    """Inline JSON or a path to a JSON file; None when absent."""
    if not value:
        return None
    path = Path(value)
    payload = json.loads(path.read_text(encoding="utf-8")) if path.exists() else json.loads(value)
    if not isinstance(payload, dict):
        raise EcoError("receipt and baseline must be JSON objects")
    return payload


def _load_evidence(args) -> list:
    if args.evidence_file:
        path = Path(args.evidence_file)
        if not path.exists():
            raise EcoError(f"evidence file not found: {path}")
        payload = json.loads(path.read_text(encoding="utf-8"))
    elif args.evidence:
        payload = json.loads(args.evidence)
    else:
        return []
    if isinstance(payload, dict):
        if "computed" in payload:
            raise EcoError(
                "evidence payload contains a `computed` block — the actor may submit "
                "evidence, not a verdict. Rejected."
            )
        payload = payload.get("evidence", [])
    if not isinstance(payload, list):
        raise EcoError("evidence must be a JSON list of evidence objects")
    return payload


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _render_verdict(record: dict) -> str:
    computed = record.get("computed") or {}
    g = computed.get("grade") or {}
    floor = record.get("floor_required") or {}
    lines = [
        "",
        f"  {record.get('subject_id')} · {record.get('step_id')}  [{record.get('work_type')}]",
        f"  record   {record.get('record_id')}",
        f"  claimed  {record.get('claimed_by')}",
        f"  verified {computed.get('verdict_by')}",
        "",
        f"  floor    E{floor.get('E')}/C{floor.get('C')}/O{floor.get('O')}",
        f"  observed E{g.get('E')}/C{g.get('C')}/O{g.get('O')}",
        "",
        f"  VERDICT  {computed.get('verdict')}" + ("  (terminal)" if computed.get("terminal") else ""),
    ]
    if computed.get("unmet"):
        lines.append(f"  unmet    {', '.join(computed['unmet'])}")
    if computed.get("outcome_due_at") and computed.get("verdict") == VERDICT_SHIPPED:
        lines.append(f"  outcome due {computed['outcome_due_at']}")
        lines.append("  SHIPPED carries a debt. It is not CLOSED until that read happens.")
    for violation in computed.get("violations") or []:
        lines.append(f"  VIOLATION {violation}")
    for entry in computed.get("rejected_evidence") or []:
        lines.append(f"  rejected  {entry.get('kind')}: {entry.get('reason')}")
    lines.append("")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Subcommands
# ---------------------------------------------------------------------------


def cmd_floors(args) -> int:
    floors = EcoFloors.load(args.floors)
    if args.json:
        print(json.dumps({name: wt.floor for name, wt in floors.work_types.items()}, indent=2))
        return 0
    print(f"\nECO floors ({floors.schema_version})\n")
    print(f"  {'work type':<22} {'floor':<12} external  attribution")
    print(f"  {'-' * 22} {'-' * 12} --------  -----------")
    for name, wt in sorted(floors.work_types.items()):
        floor = f"E{wt.floor['E']}/C{wt.floor['C']}/O{wt.floor['O']}"
        print(f"  {name:<22} {floor:<12} {str(wt.external_effect):<9} {wt.attribution_required}")
    print()
    return 0


def cmd_claim(args) -> int:
    store = EcoRecordStore(floors=EcoFloors.load(args.floors))
    record = store.claim(
        subject_id=args.subject,
        step_id=args.step,
        work_type=args.work_type,
        claimed_by=args.actor,
        evidence=_load_evidence(args),
        record_id=args.record,
    )
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print(f"\n  claimed  {record['record_id']}  ({len(record['evidence'])} evidence entries)")
        print(f"  floor    E{record['floor_required']['E']}/C{record['floor_required']['C']}/O{record['floor_required']['O']}")
        print("  No verdict issued. Run `eco_gate verify` with a verifier that is not the actor.\n")
    return 0


def cmd_verify(args) -> int:
    store = EcoRecordStore(floors=EcoFloors.load(args.floors))
    record = store.verify(args.record, verifier=args.verifier)
    if args.json:
        print(json.dumps(record, indent=2))
    else:
        print(_render_verdict(record))
    verdict = (record.get("computed") or {}).get("verdict")
    return 0 if verdict in (VERDICT_SHIPPED, VERDICT_CLOSED) else 1


def cmd_status(args) -> int:
    store = EcoRecordStore(floors=EcoFloors.load(args.floors))
    record = store.get(args.record)
    if args.json:
        print(json.dumps(record, indent=2))
        return 0
    if not record.get("computed"):
        print(f"\n  {record['record_id']}: evidence submitted, no verdict yet.\n")
        return 1
    print(_render_verdict(record))
    return 0 if (record["computed"]).get("verdict") in (VERDICT_SHIPPED, VERDICT_CLOSED) else 1


def cmd_debt(args) -> int:
    store = EcoRecordStore(floors=EcoFloors.load(args.floors))
    debt = store.outcome_debt()
    if args.json:
        print(json.dumps(debt, indent=2))
        return 0
    if not debt:
        print("\n  No open outcome obligations.\n")
        return 0
    print("\n  Outcome debt — SHIPPED, not CLOSED\n")
    for item in debt:
        flag = "OVERDUE" if item["overdue"] else "due"
        print(f"  [{flag:>7}] {item['outcome_due_at']}  {item['subject_id']} · {item['step_id']}")
        print(f"            needs {', '.join(item['unmet'] or [])}  ({item['work_type']})")
    print()
    return 0


def cmd_fail(args) -> int:
    store = EcoRecordStore(floors=EcoFloors.load(args.floors))
    work = store.floors.work_type(args.work_type)
    payload = store.record_failure(
        subject_id=args.subject,
        step_id=args.step,
        actor=args.actor,
        condition=args.condition,
        failed_axis=list(args.axis),
        required_floor=dict(work.floor),
        observed_grade={
            "E": args.observed_e,
            "C": args.observed_c,
            "O": args.observed_o,
        },
        next_action=args.next_action,
        owner=args.owner,
        verdict_by=args.verifier,
        authoritative_error=args.error or "",
        retryability=args.retryability,
        next_check_at=args.next_check_at,
    )
    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(f"\n  failure recorded  {payload['attempt_id']}")
        print(f"  condition {payload['condition']}  axis {'/'.join(payload['failed_axis'])}")
        print(f"  next      {payload['next_action']}  (owner: {payload['owner']})\n")
    return 0


def cmd_register(args) -> int:
    store = EcoRecordStore(floors=EcoFloors.load(args.floors))
    record = store.register_shipped(
        subject_id=args.subject,
        work_type=args.work_type,
        claimed_by=args.actor,
        receipt=_load_json_arg(args.receipt),
        baseline=_load_json_arg(args.baseline),
        brand_id=args.brand,
        shipped_at=args.shipped_at,
        threshold=args.threshold,
        owner=args.owner,
    )
    ticket = record["ticket"]
    if args.json:
        print(json.dumps(record, indent=2))
        return 0
    print(f"\n  ticket   {record['record_id']}  ({record['subject_id']}, {record['work_type']})")
    print(f"  shipped  {ticket['shipped_at']}")
    if ticket.get("unmeasurable_reason"):
        print(f"  UNMEASURABLE  {ticket['unmeasurable_reason']}")
    else:
        print(f"  measures {ticket['metric']} from {ticket['source']} over {ticket['window_days']}-day windows")
    print("  No verdict issued. kai-measure reads it once the window closes.\n")
    return 0


def _unregistered(store: EcoRecordStore) -> list:
    """Published content-log entries and executed actions with no outcome ticket."""
    ticketed = {r.get("subject_id") for r in store.list_records() if r.get("ticket")}
    found = []
    try:  # full repo only — plugin installs have no content log
        from scripts.harness_config import get_config  # type: ignore

        log_path = Path(get_config().content_log)
    except Exception:
        log_path = None
    if log_path and log_path.exists():
        try:
            entries = json.loads(log_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            entries = []
        for entry in entries if isinstance(entries, list) else []:
            if not isinstance(entry, dict) or not entry.get("url"):
                continue
            if entry.get("status") not in (None, "published"):
                continue
            subject = f"content:{entry.get('id')}"
            if subject not in ticketed:
                found.append({"subject_id": subject, "shipped_at": entry.get("published_at"),
                              "what": entry.get("url")})
    actions_dir = store.base_dir.parent / "actions"
    for path in sorted(actions_dir.glob("*.json")) if actions_dir.is_dir() else []:
        try:
            action = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        summary = action.get("result_summary") or {}
        if action.get("execution_state") != "completed" or summary.get("dry_run", True):
            continue
        subject = f"action:{action.get('action_id')}"
        if subject not in ticketed:
            found.append({"subject_id": subject, "shipped_at": action.get("executed_at"),
                          "what": f"{action.get('channel')}/{action.get('action_type')}"})
    return found


def cmd_unregistered(args) -> int:
    store = EcoRecordStore(floors=EcoFloors.load(args.floors))
    found = _unregistered(store)
    if args.json:
        print(json.dumps(found, indent=2))
        return 0
    if not found:
        print("\n  Every discoverable shipped change has an outcome ticket.\n")
        return 0
    print(f"\n  {len(found)} shipped change(s) with no outcome ticket\n")
    for item in found:
        print(f"  {item['shipped_at'] or '?':<32} {item['subject_id']}  {item['what']}")
    print("\n  Register each with `eco_gate register` (with its pre-ship baseline, if one exists).\n")
    return 0


def cmd_ledger(args) -> int:
    floors = EcoFloors.load(args.floors)
    store = EcoRecordStore(floors=floors)
    try:
        ledger = build_ledger(store.list_records(), brand=args.brand, since=args.since, floors=floors)
    except ValueError as exc:
        raise EcoError(str(exc))
    print(render_json(ledger) if args.json or args.format == "json" else render_markdown(ledger))
    return 0


# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="eco_gate",
        description="ECO completion gate — computes SHIPPED/CLOSED from independent evidence.",
    )
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--floors", help="Path to eco-floors.yaml (defaults to harness/eco-floors.yaml)")
    common.add_argument("--json", action="store_true", help="Machine-readable output")

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("floors", help="Show declared floors", parents=[common]).set_defaults(func=cmd_floors)

    claim = sub.add_parser("claim", help="Submit evidence (never issues a verdict)", parents=[common])
    claim.add_argument("--subject", required=True, help="Work item id")
    claim.add_argument("--step", required=True, help="Step id, e.g. social.linkedin.publish")
    claim.add_argument("--work-type", required=True, help="Work type from eco-floors.yaml")
    claim.add_argument("--actor", required=True, help="Producer identity")
    claim.add_argument("--record", help="Existing record id to append to")
    claim.add_argument("--evidence", help="Inline JSON list of evidence objects")
    claim.add_argument("--evidence-file", help="Path to a JSON file of evidence objects")
    claim.set_defaults(func=cmd_claim)

    verify = sub.add_parser("verify", help="Compute grades and issue the verdict", parents=[common])
    verify.add_argument("--record", required=True)
    verify.add_argument("--verifier", required=True, help="Verifier identity — must not be the actor")
    verify.set_defaults(func=cmd_verify)

    status = sub.add_parser("status", help="Show one record", parents=[common])
    status.add_argument("--record", required=True)
    status.set_defaults(func=cmd_status)

    sub.add_parser("debt", help="List unpaid outcome obligations", parents=[common]).set_defaults(func=cmd_debt)

    fail = sub.add_parser("fail", help="Write the mandatory failure record", parents=[common])
    fail.add_argument("--subject", required=True)
    fail.add_argument("--step", required=True)
    fail.add_argument("--work-type", required=True)
    fail.add_argument("--actor", required=True)
    fail.add_argument("--verifier", required=True)
    fail.add_argument("--condition", required=True, choices=["unproven", "blocked", "failed_attempt"])
    fail.add_argument("--axis", required=True, nargs="+", choices=["E", "C", "O"])
    fail.add_argument("--observed-e", type=int, default=0)
    fail.add_argument("--observed-c", type=int, default=0)
    fail.add_argument("--observed-o", type=int, default=0)
    fail.add_argument("--next-action", required=True, help="Specific action or external condition")
    fail.add_argument("--owner", required=True)
    fail.add_argument("--error", help="Exact provider or gate output")
    fail.add_argument("--retryability", default="retryable", choices=["retryable", "waiting", "abandoned"])
    fail.add_argument("--next-check-at", help="ISO-8601 timestamp")
    fail.set_defaults(func=cmd_fail)

    register = sub.add_parser("register", help="Open an outcome ticket for shipped work", parents=[common])
    register.add_argument("--subject", required=True, help="Work item id, e.g. content:<id> or action:<id>")
    register.add_argument("--work-type", required=True)
    register.add_argument("--actor", required=True, help="Identity that shipped the work")
    register.add_argument("--brand", help="Brand / business id")
    register.add_argument("--shipped-at", help="ISO-8601 ship time (defaults to now)")
    register.add_argument("--receipt", help="Provider receipt: inline JSON or a file path")
    register.add_argument("--baseline", help="Pre-ship baseline {metric, source, value, captured_at|window_end, ...}")
    register.add_argument("--threshold", type=float, help="Predeclared target value (else baseline x min_lift)")
    register.add_argument("--owner", help="Measurement owner")
    register.set_defaults(func=cmd_register)

    sub.add_parser(
        "unregistered", help="Shipped changes with no outcome ticket", parents=[common]
    ).set_defaults(func=cmd_unregistered)

    ledger = sub.add_parser("ledger", help="Outcome verdict ledger", parents=[common])
    ledger.add_argument("--format", choices=["md", "json"], default="md")
    ledger.add_argument("--brand", help="Only tickets for this brand id")
    ledger.add_argument("--since", help="Only tickets shipped on/after this ISO date")
    ledger.set_defaults(func=cmd_ledger)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        return args.func(args)
    except EcoError as exc:
        print(f"\n  ECO contract violation: {exc}\n", file=sys.stderr)
        return 2
    except json.JSONDecodeError as exc:
        print(f"\n  Invalid JSON: {exc}\n", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
