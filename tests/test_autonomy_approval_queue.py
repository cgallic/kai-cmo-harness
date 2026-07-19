"""Tests for the autonomy approval queue (issue #27 item 4).

Covers the append-only event log, fold-to-state reads, dedupe on enqueue,
validation, approve/reject resolution, and the bridge from router findings.
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from scripts.autonomy.approval_queue import (
    ApprovalItem,
    approve,
    enqueue,
    get_item,
    list_pending,
    read_events,
    read_items,
    record_validation,
    reject,
    resolve,
    stage_finding,
    stage_findings,
)


class _QueueCase(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = Path(os.environ.get("PYTEST_TMP", "/tmp")) / f"kai-queue-{os.getpid()}"
        self.queue = self._tmp / "approval_queue.jsonl"
        self._tmp.mkdir(parents=True, exist_ok=True)
        if self.queue.exists():
            self.queue.unlink()

    def tearDown(self) -> None:
        if self.queue.exists():
            self.queue.unlink()

    def _item(self, **over) -> ApprovalItem:
        base = dict(
            workflow="demo.workflow",
            action_kind="send_email",
            risk_level="high",
            payload={"to": "lead@example.com"},
            source_refs=["https://example.com/x"],
            decision_reason="action 'send_email' touches a live/client surface",
        )
        base.update(over)
        return ApprovalItem(**base)


class TestEnqueue(_QueueCase):
    def test_item_gets_id_and_default_dedupe_key(self) -> None:
        item = self._item()
        self.assertTrue(item.item_id.startswith("send_email-"))
        self.assertEqual(item.dedupe_key, "demo.workflow|send_email|https://example.com/x")

    def test_invalid_risk_defaults_high(self) -> None:
        self.assertEqual(self._item(risk_level="bogus").risk_level, "high")

    def test_enqueue_appends_and_reads_back(self) -> None:
        item = self._item()
        event = enqueue(item, path=self.queue)
        self.assertIsNotNone(event)
        items = read_items(self.queue)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0]["status"], "pending")
        self.assertEqual(items[0]["action_kind"], "send_email")
        self.assertEqual(items[0]["validation"]["status"], "unvalidated")

    def test_enqueue_dedupes_pending_same_key(self) -> None:
        self.assertIsNotNone(enqueue(self._item(dedupe_key="k1"), path=self.queue))
        self.assertIsNone(enqueue(self._item(dedupe_key="k1"), path=self.queue))
        self.assertEqual(len(list_pending(self.queue)), 1)

    def test_resolved_item_does_not_block_requeue(self) -> None:
        first = self._item(dedupe_key="k2")
        enqueue(first, path=self.queue)
        reject(first.item_id, "operator", path=self.queue)
        # Same key may be queued again once the prior one is resolved.
        self.assertIsNotNone(enqueue(self._item(dedupe_key="k2"), path=self.queue))
        self.assertEqual(len(list_pending(self.queue)), 1)

    def test_enqueue_raises_on_bad_path(self) -> None:
        bad = Path("/proc/should-not-be-writable/approval_queue.jsonl")
        with self.assertRaises(OSError):
            enqueue(self._item(), path=bad)


class TestResolution(_QueueCase):
    def test_approve_records_who_and_when(self) -> None:
        item = self._item()
        enqueue(item, path=self.queue)
        approve(item.item_id, "connor", "looks good", path=self.queue)
        resolved = get_item(item.item_id, self.queue)
        self.assertEqual(resolved["status"], "approved")
        self.assertEqual(resolved["resolved_by"], "connor")
        self.assertEqual(resolved["resolution_note"], "looks good")
        self.assertTrue(resolved["resolved_at"])
        self.assertEqual(list_pending(self.queue), [])

    def test_reject_sets_status(self) -> None:
        item = self._item()
        enqueue(item, path=self.queue)
        reject(item.item_id, "connor", path=self.queue)
        self.assertEqual(get_item(item.item_id, self.queue)["status"], "rejected")

    def test_double_resolution_raises(self) -> None:
        item = self._item()
        enqueue(item, path=self.queue)
        approve(item.item_id, "connor", path=self.queue)
        with self.assertRaises(ValueError):
            resolve(item.item_id, "rejected", "someone", path=self.queue)

    def test_resolve_unknown_item_raises(self) -> None:
        with self.assertRaises(ValueError):
            approve("does-not-exist", "connor", path=self.queue)

    def test_invalid_resolution_status_raises(self) -> None:
        item = self._item()
        enqueue(item, path=self.queue)
        with self.assertRaises(ValueError):
            resolve(item.item_id, "maybe", "connor", path=self.queue)

    def test_append_only_keeps_queued_line(self) -> None:
        item = self._item()
        enqueue(item, path=self.queue)
        approve(item.item_id, "connor", path=self.queue)
        events = read_events(self.queue)
        self.assertEqual([e["event"] for e in events], ["queued", "resolved"])


class TestValidation(_QueueCase):
    def test_record_validation_updates_state(self) -> None:
        item = self._item()
        enqueue(item, path=self.queue)
        record_validation(item.item_id, "passed", "gates clean", path=self.queue)
        val = get_item(item.item_id, self.queue)["validation"]
        self.assertEqual(val["status"], "passed")
        self.assertEqual(val["notes"], "gates clean")

    def test_invalid_validation_status_raises(self) -> None:
        item = self._item()
        enqueue(item, path=self.queue)
        with self.assertRaises(ValueError):
            record_validation(item.item_id, "great", path=self.queue)

    def test_validate_unknown_item_raises(self) -> None:
        with self.assertRaises(ValueError):
            record_validation("nope", "passed", path=self.queue)


class TestFindingBridge(_QueueCase):
    def test_stage_finding_only_for_approval_decisions(self) -> None:
        approval = {
            "decision": "stage_for_approval",
            "action_kind": "paid_spend",
            "risk_level": "high",
            "decision_reason": "paid run",
            "source_url": "https://ads.example.com",
            "id": "ad_1",
        }
        other = {"decision": "auto_fix", "action_kind": "review", "id": "doc_1"}
        self.assertIsNotNone(stage_finding(approval, "demo.workflow", path=self.queue))
        self.assertIsNone(stage_finding(other, "demo.workflow", path=self.queue))
        pending = list_pending(self.queue)
        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0]["action_kind"], "paid_spend")
        self.assertIn("https://ads.example.com", pending[0]["source_refs"])

    def test_stage_findings_filters_and_returns_written(self) -> None:
        findings = [
            {"decision": "stage_for_approval", "action_kind": "send_email", "id": "a", "source_url": "u1"},
            {"decision": "escalate", "action_kind": "review", "id": "b"},
            {"decision": "stage_for_approval", "action_kind": "publish", "id": "c", "source_url": "u2"},
        ]
        staged = stage_findings(findings, "demo.workflow", path=self.queue)
        self.assertEqual(len(staged), 2)
        self.assertEqual(len(list_pending(self.queue)), 2)


if __name__ == "__main__":
    unittest.main()
