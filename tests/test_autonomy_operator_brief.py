"""Tests for the weekly operator brief (issue #27 item 8).

Covers section assembly from injected ledger records + queue items, the time
window filter, risk sorting, recurring-lesson upgrades, and markdown rendering.
"""

from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.autonomy.operator_brief import brief_data, render_brief


def _iso(days_ago: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days_ago)).isoformat(timespec="seconds")


def _record(**over) -> dict:
    base = dict(
        run_id="run-1",
        workflow="demo.workflow",
        started_at=_iso(1),
        findings=[],
        actions_taken=[],
        blockers=[],
        lessons=[],
    )
    base.update(over)
    return base


def _pending(**over) -> dict:
    base = dict(
        item_id="send_email-x",
        workflow="demo.workflow",
        action_kind="send_email",
        risk_level="high",
        decision_reason="touches a live surface",
        source_refs=["https://example.com"],
        validation={"status": "unvalidated", "notes": ""},
        status="pending",
    )
    base.update(over)
    return base


class TestBriefData(unittest.TestCase):
    def test_sections_assembled(self) -> None:
        records = [
            _record(
                findings=[
                    {"title": "X policy changed", "risk_level": "high", "decision": "auto_pr",
                     "why_it_matters": "allowed content shifted"},
                    {"title": "dead source", "risk_level": "medium", "decision": "escalate",
                     "source_status": "unresolved", "next_step": "find replacement"},
                ],
                actions_taken=["Updated snapshot"],
                blockers=["source unreachable"],
                lessons=["source unreachable; needs replacement"],
            ),
            _record(
                run_id="run-2",
                lessons=["source unreachable; needs replacement"],
            ),
        ]
        data = brief_data(records=records, pending=[_pending()], since_days=7)
        s = data["summary"]
        self.assertEqual(s["approvals_needed"], 1)
        self.assertEqual(s["failed_automations"], 1)
        self.assertEqual(s["stale_or_broken_sources"], 1)
        # high finding + escalate finding both count as biggest risks
        self.assertEqual(s["biggest_risks"], 2)
        # lesson recurred twice across runs -> one promotion candidate
        self.assertEqual(s["promotion_candidates"], 1)
        self.assertEqual(data["actions_taken"][0]["action"], "Updated snapshot")

    def test_window_filters_old_runs(self) -> None:
        records = [_record(started_at=_iso(1)), _record(run_id="old", started_at=_iso(40))]
        data = brief_data(records=records, pending=[], since_days=7)
        self.assertEqual(data["summary"]["runs_considered"], 1)

    def test_window_zero_keeps_all(self) -> None:
        records = [_record(started_at=_iso(1)), _record(run_id="old", started_at=_iso(40))]
        data = brief_data(records=records, pending=[], since_days=None)
        self.assertEqual(data["summary"]["runs_considered"], 2)

    def test_biggest_risks_sorted_desc(self) -> None:
        records = [
            _record(findings=[
                {"title": "med", "risk_level": "medium", "decision": "auto_pr"},
                {"title": "crit", "risk_level": "critical", "decision": "block"},
            ])
        ]
        data = brief_data(records=records, pending=[], since_days=7)
        self.assertEqual(data["biggest_risks"][0]["risk_level"], "critical")

    def test_low_risk_findings_excluded_from_risks(self) -> None:
        records = [_record(findings=[{"title": "minor", "risk_level": "low", "decision": "auto_fix"}])]
        data = brief_data(records=records, pending=[], since_days=7)
        self.assertEqual(data["summary"]["biggest_risks"], 0)


class TestRender(unittest.TestCase):
    def test_render_has_all_headers(self) -> None:
        data = brief_data(records=[_record()], pending=[], since_days=7)
        md = render_brief(data)
        for header in [
            "# Kai Operator Brief",
            "## Approvals needed",
            "## Biggest risks",
            "## Failed automations",
            "## Stale docs / broken sources",
            "## Suggested upgrades",
            "## Actions taken",
        ]:
            self.assertIn(header, md)

    def test_render_empty_states(self) -> None:
        md = render_brief(brief_data(records=[], pending=[], since_days=7))
        self.assertIn("None waiting.", md)
        self.assertIn("No high/critical findings", md)

    def test_render_lists_pending_approval(self) -> None:
        md = render_brief(brief_data(records=[], pending=[_pending()], since_days=7))
        self.assertIn("send_email", md)
        self.assertIn("send_email-x", md)


if __name__ == "__main__":
    unittest.main()
