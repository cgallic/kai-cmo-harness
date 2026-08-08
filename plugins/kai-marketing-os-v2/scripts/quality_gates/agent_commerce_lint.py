#!/usr/bin/env python3
"""
Agentic Commerce Readiness Lint - Kai Harness Quality Gate

Runs the fixture-friendly commerce readiness audit and prints a concise
score + finding summary. Designed for local OSS workflows without live
connector credentials.

Usage:
  python scripts/quality_gates/agent_commerce_lint.py fixtures/commerce.json
  python scripts/quality_gates/agent_commerce_lint.py fixtures/commerce.json --json

Exit codes:
  0 pass (no critical findings, score >= 70)
  1 partial/fail (score < 70 or high findings present)
  2 hard fail (critical findings)
  3 input/read error
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kai.audits.agentic_commerce import (
    audit_agentic_commerce_readiness,
    summarize_agentic_commerce_findings,
)


def load_fixture(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("Fixture root must be a JSON object.")
    return data


def verdict(summary: Dict[str, Any]) -> tuple[str, int]:
    counts = summary.get("counts", {})
    critical = int(counts.get("critical", 0))
    high = int(counts.get("high", 0))
    score = float(summary.get("score", 0.0))

    if critical > 0:
        return "FAIL", 2
    if high > 0 or score < 70.0:
        return "PARTIAL", 1
    return "PASS", 0


def format_text(summary: Dict[str, Any], findings: list[dict]) -> str:
    counts = summary["counts"]
    lines = [
        "Agentic Commerce Readiness Gate",
        "=" * 60,
        f"Score: {summary['score']}",
        (
            "Counts: "
            f"critical={counts.get('critical', 0)} "
            f"high={counts.get('high', 0)} "
            f"medium={counts.get('medium', 0)} "
            f"low={counts.get('low', 0)} "
            f"missing_data={counts.get('missing_data', 0)}"
        ),
        "-" * 60,
    ]
    if not findings:
        lines.append("No findings.")
    else:
        for finding in findings:
            lines.append(
                f"[{finding['severity'].upper()}] {finding['subcategory'] or finding['category']}: {finding['title']}"
            )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Agentic commerce readiness quality gate.")
    parser.add_argument("fixture", help="Path to JSON fixture file.")
    parser.add_argument("--json", action="store_true", help="Output machine-readable JSON.")
    args = parser.parse_args()

    path = Path(args.fixture)
    if not path.exists() or not path.is_file():
        print(f"error: fixture not found: {path}", file=sys.stderr)
        return 3

    try:
        fixture = load_fixture(path)
    except Exception as exc:  # pragma: no cover - integration path
        print(f"error: failed to load fixture: {exc}", file=sys.stderr)
        return 3

    findings = audit_agentic_commerce_readiness(fixture)
    summary = summarize_agentic_commerce_findings(findings)
    state, exit_code = verdict(summary)

    finding_payload = [
        {
            "id": finding.id,
            "category": finding.category,
            "subcategory": finding.subcategory,
            "severity": finding.severity,
            "title": finding.title,
            "source": finding.source,
        }
        for finding in findings
    ]

    payload = {
        "fixture": str(path),
        "verdict": state,
        "summary": summary,
        "findings": finding_payload,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        print(format_text(summary, finding_payload))
        print(f"\nVerdict: {state}")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
