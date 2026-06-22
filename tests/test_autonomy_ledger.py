"""Tests for the Kai autonomy control layer (issue #27).

Covers the append-only ledger schema, the policy decision router, and the
impact classifier that backs the social platform monitor's impact cards.
"""

from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.autonomy.decisions import ACTION_CLASSES, RISK_LEVELS, route_decision
from scripts.autonomy.impact import build_impact_card, classify_source_status
from scripts.autonomy.ledger import (
    LEDGER_FIELDS,
    LedgerRecord,
    mine_repeated_lessons,
    new_run_id,
    read_records,
    record_run,
)


class TestLedgerSchema(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(os.environ.get("PYTEST_TMP", "/tmp")) / f"kai-ledger-{os.getpid()}"
        self.ledger = self._tmp / "ledger.jsonl"
        self._tmp.mkdir(parents=True, exist_ok=True)
        if self.ledger.exists():
            self.ledger.unlink()

    def tearDown(self) -> None:
        if self.ledger.exists():
            self.ledger.unlink()

    def test_run_id_is_unique_and_namespaced(self) -> None:
        a = new_run_id("scripts.social.platform_change_monitor")
        b = new_run_id("scripts.social.platform_change_monitor")
        self.assertTrue(a.startswith("platform_change_monitor-"))
        self.assertNotEqual(a, b)

    def test_record_carries_every_field_in_order(self) -> None:
        rec = LedgerRecord(workflow="demo.workflow").finish()
        payload = rec.to_record()
        self.assertEqual(tuple(payload.keys()), LEDGER_FIELDS)
        for field_name in LEDGER_FIELDS:
            self.assertIn(field_name, payload)

    def test_finish_derives_risk_and_human_from_findings(self) -> None:
        rec = LedgerRecord(
            workflow="demo.workflow",
            findings=[
                {"risk_level": "low", "decision": "auto_fix"},
                {"risk_level": "high", "decision": "stage_for_approval"},
            ],
        ).finish()
        self.assertEqual(rec.risk_level, "high")
        self.assertTrue(rec.requires_human)

    def test_finish_no_findings_is_clean(self) -> None:
        rec = LedgerRecord(workflow="demo.workflow").finish()
        self.assertEqual(rec.risk_level, "none")
        self.assertFalse(rec.requires_human)

    def test_record_run_appends_jsonl(self) -> None:
        rec = LedgerRecord(workflow="demo.workflow", actions_taken=["did a thing"])
        written = record_run(rec, path=self.ledger)
        self.assertIsNotNone(written)
        self.assertTrue(self.ledger.exists())
        lines = self.ledger.read_text().strip().splitlines()
        self.assertEqual(len(lines), 1)
        parsed = json.loads(lines[0])
        self.assertEqual(parsed["workflow"], "demo.workflow")
        self.assertEqual(parsed["actions_taken"], ["did a thing"])

    def test_record_run_respects_opt_out(self) -> None:
        os.environ["KAI_AUTONOMY_LEDGER"] = "0"
        try:
            written = record_run(LedgerRecord(workflow="demo.workflow"), path=self.ledger)
        finally:
            del os.environ["KAI_AUTONOMY_LEDGER"]
        self.assertIsNone(written)
        self.assertFalse(self.ledger.exists())

    def test_record_run_never_raises(self) -> None:
        # A directory path that cannot be written should be swallowed.
        bad = Path("/proc/should-not-be-writable/ledger.jsonl")
        self.assertIsNone(record_run(LedgerRecord(workflow="demo"), path=bad))

    def test_mine_repeated_lessons(self) -> None:
        for _ in range(3):
            record_run(
                LedgerRecord(workflow="demo.workflow", lessons=["source unreachable"]),
                path=self.ledger,
            )
        record_run(LedgerRecord(workflow="demo.workflow", lessons=["one-off"]), path=self.ledger)
        records = read_records(self.ledger)
        self.assertEqual(len(records), 4)
        mined = mine_repeated_lessons(records, min_count=2)
        self.assertEqual(len(mined), 1)
        self.assertEqual(mined[0]["lesson"], "source unreachable")
        self.assertEqual(mined[0]["count"], 3)


class TestDecisionRouter(unittest.TestCase):
    def test_action_classes_are_known(self) -> None:
        self.assertEqual(
            ACTION_CLASSES,
            ("auto_fix", "auto_pr", "stage_for_approval", "escalate", "block"),
        )

    def test_guardrail_blocks_win(self) -> None:
        res = route_decision({"summary": "buy followers to inflate engagement", "risk_level": "low"})
        self.assertEqual(res.action_class, "block")
        self.assertEqual(res.risk_level, "critical")
        self.assertTrue(res.requires_human)

    def test_outbound_email_stages_for_approval(self) -> None:
        res = route_decision({"action_kind": "send_email", "change_type": "content"})
        self.assertEqual(res.action_class, "stage_for_approval")
        self.assertTrue(res.requires_human)

    def test_paid_spend_stages_for_approval(self) -> None:
        res = route_decision({"action_kind": "paid_spend"})
        self.assertEqual(res.action_class, "stage_for_approval")

    def test_unresolved_source_escalates(self) -> None:
        res = route_decision({"source_status": "unresolved", "change_type": "dead_link"})
        self.assertEqual(res.action_class, "escalate")
        self.assertTrue(res.requires_human)

    def test_safe_docs_change_auto_fixes(self) -> None:
        res = route_decision({"change_type": "snapshot", "risk_level": "low"})
        self.assertEqual(res.action_class, "auto_fix")
        self.assertFalse(res.requires_human)

    def test_code_change_routes_to_pr(self) -> None:
        res = route_decision({"change_type": "code", "risk_level": "medium"})
        self.assertEqual(res.action_class, "auto_pr")

    def test_risk_levels_ordered(self) -> None:
        self.assertEqual(RISK_LEVELS, ("none", "low", "medium", "high", "critical"))


class TestImpactClassifier(unittest.TestCase):
    def test_classify_unresolved(self) -> None:
        result = {"monitor_status": "error", "ok": False, "previous_error": True}
        self.assertEqual(classify_source_status(result), "unresolved")

    def test_classify_replaced(self) -> None:
        result = {"monitor_status": "error", "ok": False, "replacement_url": "https://x/new"}
        self.assertEqual(classify_source_status(result), "replaced")

    def test_classify_fixed(self) -> None:
        result = {"monitor_status": "unchanged", "ok": True, "previous_error": True}
        self.assertEqual(classify_source_status(result), "fixed")

    def test_classify_ok(self) -> None:
        result = {"monitor_status": "unchanged", "ok": True, "previous_error": False}
        self.assertEqual(classify_source_status(result), "ok")

    def test_changed_policy_card_has_practical_impact(self) -> None:
        card = build_impact_card(
            {
                "id": "x_rules",
                "platform": "x",
                "category": "policy",
                "title": "X Rules",
                "url": "https://help.x.com/rules",
                "owner_file": "knowledge/channels/twitter-x.md",
                "monitor_status": "changed",
                "previous_hash": "a" * 64,
                "content_hash": "b" * 64,
                "ok": True,
            }
        )
        # Practical impact, not just a hash.
        self.assertIn("hash changed", card["what_changed"].lower())
        self.assertEqual(card["impact_area"], "allowed content")
        self.assertNotEqual(card["why_it_matters"], "No operational impact this run")
        self.assertEqual(card["change_type"], "docs")
        self.assertEqual(card["decision"], "auto_fix")
        self.assertIn("twitter-x.md", card["next_step"])

    def test_error_card_routes_to_escalate(self) -> None:
        card = build_impact_card(
            {
                "id": "tt_changelog",
                "platform": "tiktok",
                "category": "changelog",
                "title": "TikTok API Changelog",
                "url": "https://developers.tiktok.com/changelog",
                "monitor_status": "error",
                "ok": False,
                "status_code": 404,
                "previous_error": False,
            }
        )
        self.assertEqual(card["source_status"], "unresolved")
        self.assertEqual(card["decision"], "escalate")
        self.assertEqual(card["impact_area"], "scheduling/rate limits")
        self.assertTrue(card["requires_human"])

    def test_ai_policy_card_flags_disclosure_gate(self) -> None:
        card = build_impact_card(
            {
                "id": "tt_ai",
                "platform": "tiktok",
                "category": "ai_policy",
                "title": "TikTok AI Disclosure",
                "url": "https://tiktok.com/ai",
                "monitor_status": "changed",
                "previous_hash": "c" * 64,
                "content_hash": "d" * 64,
                "ok": True,
            }
        )
        self.assertEqual(card["impact_area"], "AI/synthetic media labels")
        self.assertIn("disclosure", card["why_it_matters"].lower())


if __name__ == "__main__":
    unittest.main()
