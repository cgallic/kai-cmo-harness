"""Tests for the structured editorial calendar store + hourly executor task.

Covers:
- calendar CRUD (add/list/mark) and validation
- due-item selection with timezone-safe comparisons
- editorial_calendar_tick handler with generation mocked (drafts only —
  the handler never publishes and never sets status "published")
"""

from __future__ import annotations

import asyncio
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.campaigns import calendar as cal
from agent.models import ScheduledTask, ScheduledTaskConfig


@pytest.fixture(autouse=True)
def calendar_dir(tmp_path, monkeypatch):
    """Redirect the calendar store to a temp dir for every test."""
    monkeypatch.setenv("KAI_CALENDAR_DIR", str(tmp_path / "calendar"))
    yield tmp_path / "calendar"


def _make_task(extra=None, client=None) -> ScheduledTask:
    return ScheduledTask(
        id="tick1",
        name="Editorial Calendar Tick",
        cron_expression="0 * * * *",
        task_type="editorial_calendar_tick",
        client=client,
        config=ScheduledTaskConfig(extra=extra or {}),
    )


# ---------------------------------------------------------------------------
# Store CRUD
# ---------------------------------------------------------------------------


class TestCalendarCrud:
    def test_add_and_list(self, calendar_dir):
        item = cal.add_item(
            site="kaicalls",
            title="AI receptionist ROI math",
            publish_at="2026-07-10T14:00:00Z",
            format="blog",
            keyword="ai receptionist roi",
            persona="Admin Martyr",
            campaign_id="q3-launch",
            notes="from Q3 plan",
        )
        assert item["id"].startswith("cal-")
        assert item["status"] == "planned"
        assert item["publish_at"] == "2026-07-10T14:00:00+00:00"
        assert item["campaign_id"] == "q3-launch"

        items = cal.list_items()
        assert len(items) == 1
        assert items[0]["title"] == "AI receptionist ROI math"

        # File is JSONL under the overridden dir
        store = calendar_dir / "editorial.jsonl"
        assert store.exists()
        lines = [l for l in store.read_text().splitlines() if l.strip()]
        assert len(lines) == 1
        assert json.loads(lines[0])["site"] == "kaicalls"

    def test_list_filters(self):
        cal.add_item(site="kaicalls", title="A", publish_at="2026-07-01T00:00:00Z")
        cal.add_item(site="buildwithkai", title="B", publish_at="2026-07-02T00:00:00Z")
        b = cal.list_items(site="buildwithkai")
        assert [i["title"] for i in b] == ["B"]
        assert cal.list_items(status="ready") == []

    def test_list_sorted_by_publish_at(self):
        cal.add_item(site="s", title="later", publish_at="2026-07-20T00:00:00Z")
        cal.add_item(site="s", title="sooner", publish_at="2026-07-01T00:00:00Z")
        assert [i["title"] for i in cal.list_items()] == ["sooner", "later"]

    def test_mark_status(self):
        item = cal.add_item(site="s", title="t", publish_at="2026-07-01T00:00:00Z")
        updated = cal.mark_status(item["id"], "skipped", notes="dropped from plan")
        assert updated["status"] == "skipped"
        assert updated["notes"] == "dropped from plan"
        # Persisted
        assert cal.get_item(item["id"])["status"] == "skipped"

    def test_mark_unknown_id_returns_none(self):
        assert cal.mark_status("cal-nope", "ready") is None

    def test_mark_invalid_status_raises(self):
        item = cal.add_item(site="s", title="t", publish_at="2026-07-01T00:00:00Z")
        with pytest.raises(ValueError):
            cal.mark_status(item["id"], "live")  # not a valid status

    def test_add_invalid_inputs(self):
        with pytest.raises(ValueError):
            cal.add_item(site="", title="t", publish_at="2026-07-01T00:00:00Z")
        with pytest.raises(ValueError):
            cal.add_item(site="s", title="", publish_at="2026-07-01T00:00:00Z")
        with pytest.raises(ValueError):
            cal.add_item(site="s", title="t", publish_at="not-a-date")
        with pytest.raises(ValueError):
            cal.add_item(site="s", title="t", publish_at="2026-07-01T00:00:00Z",
                         status="live")

    def test_corrupt_line_skipped(self, calendar_dir):
        cal.add_item(site="s", title="good", publish_at="2026-07-01T00:00:00Z")
        store = calendar_dir / "editorial.jsonl"
        with open(store, "a") as f:
            f.write("{not json\n")
        items = cal.list_items()
        assert len(items) == 1
        assert items[0]["title"] == "good"


# ---------------------------------------------------------------------------
# Due-item selection (timezone-safe)
# ---------------------------------------------------------------------------


class TestDueItems:
    def test_due_selection(self):
        now = datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc)
        past = cal.add_item(site="s", title="past", publish_at="2026-07-05T11:00:00Z")
        cal.add_item(site="s", title="future", publish_at="2026-07-05T13:00:00Z")
        due = cal.due_items(now=now)
        assert [i["id"] for i in due] == [past["id"]]

    def test_naive_publish_at_treated_as_utc(self):
        # Naive timestamp — must be interpreted as UTC, not local time.
        cal.add_item(site="s", title="naive", publish_at="2026-07-05T11:30:00")
        assert cal.due_items(now=datetime(2026, 7, 5, 11, 0, tzinfo=timezone.utc)) == []
        due = cal.due_items(now=datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc))
        assert len(due) == 1

    def test_offset_publish_at_normalized(self):
        # 14:00 at UTC+2 == 12:00 UTC
        cal.add_item(site="s", title="offset", publish_at="2026-07-05T14:00:00+02:00")
        assert cal.due_items(now=datetime(2026, 7, 5, 11, 59, tzinfo=timezone.utc)) == []
        assert len(cal.due_items(now=datetime(2026, 7, 5, 12, 0, tzinfo=timezone.utc))) == 1

    def test_naive_now_treated_as_utc(self):
        cal.add_item(site="s", title="x", publish_at="2026-07-05T11:00:00Z")
        due = cal.due_items(now=datetime(2026, 7, 5, 12, 0))  # naive now
        assert len(due) == 1

    def test_only_planned_items_are_due(self):
        item = cal.add_item(site="s", title="x", publish_at="2026-07-01T00:00:00Z")
        cal.mark_status(item["id"], "ready")
        assert cal.due_items(now=datetime(2026, 7, 5, tzinfo=timezone.utc)) == []

    def test_due_sorted_oldest_first(self):
        cal.add_item(site="s", title="newer", publish_at="2026-07-04T00:00:00Z")
        cal.add_item(site="s", title="older", publish_at="2026-07-01T00:00:00Z")
        due = cal.due_items(now=datetime(2026, 7, 5, tzinfo=timezone.utc))
        assert [i["title"] for i in due] == ["older", "newer"]


# ---------------------------------------------------------------------------
# Stale "generating" sweep (crash recovery)
# ---------------------------------------------------------------------------


def _rewrite_item(calendar_dir, item_id, **fields):
    """Rewrite one stored record directly (simulate legacy/aged records)."""
    store = calendar_dir / "editorial.jsonl"
    lines = []
    for line in store.read_text().splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        if rec.get("id") == item_id:
            for key, value in fields.items():
                if value is None:
                    rec.pop(key, None)
                else:
                    rec[key] = value
        lines.append(json.dumps(rec))
    store.write_text("\n".join(lines) + "\n")


class TestResetStaleGenerating:
    def test_stale_item_recovered_and_due_again(self):
        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        cal.mark_status(item["id"], "generating")

        later = datetime.now(timezone.utc) + timedelta(hours=7)
        reset = cal.reset_stale_generating(max_age_hours=6, now=later)

        assert [i["id"] for i in reset] == [item["id"]]
        stored = cal.get_item(item["id"])
        assert stored["status"] == "planned"
        assert "auto-reset" in stored["notes"]
        # Recovered items are due again on the next tick
        assert any(i["id"] == item["id"] for i in cal.due_items(now=later))

    def test_fresh_generating_item_not_touched(self):
        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        cal.mark_status(item["id"], "generating")

        soon = datetime.now(timezone.utc) + timedelta(hours=1)
        assert cal.reset_stale_generating(max_age_hours=6, now=soon) == []
        assert cal.get_item(item["id"])["status"] == "generating"

    def test_note_appended_not_overwritten(self):
        item = cal.add_item(
            site="s", title="t", publish_at="2020-01-01T00:00:00Z", notes="from plan"
        )
        cal.mark_status(item["id"], "generating")

        later = datetime.now(timezone.utc) + timedelta(hours=7)
        cal.reset_stale_generating(max_age_hours=6, now=later)

        notes = cal.get_item(item["id"])["notes"]
        assert notes.startswith("from plan; ")
        assert "auto-reset" in notes

    def test_missing_timestamps_treated_as_stale(self, calendar_dir):
        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        cal.mark_status(item["id"], "generating")
        # Legacy record without updated_at/created_at can never age out —
        # the sweep must still recover it.
        _rewrite_item(calendar_dir, item["id"], updated_at=None, created_at=None)

        reset = cal.reset_stale_generating(max_age_hours=6)
        assert [i["id"] for i in reset] == [item["id"]]
        assert cal.get_item(item["id"])["status"] == "planned"

    def test_other_statuses_never_swept(self):
        planned = cal.add_item(site="s", title="p", publish_at="2020-01-01T00:00:00Z")
        ready = cal.add_item(site="s", title="r", publish_at="2020-01-02T00:00:00Z")
        cal.mark_status(ready["id"], "ready")

        later = datetime.now(timezone.utc) + timedelta(days=30)
        assert cal.reset_stale_generating(max_age_hours=6, now=later) == []
        assert cal.get_item(planned["id"])["status"] == "planned"
        assert cal.get_item(ready["id"])["status"] == "ready"

    def test_mark_status_stamps_updated_at(self):
        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        before = item["updated_at"]
        updated = cal.mark_status(item["id"], "generating")
        assert updated["updated_at"] >= before


# ---------------------------------------------------------------------------
# editorial_calendar_tick handler
# ---------------------------------------------------------------------------


class TestEditorialCalendarTick:
    def _patch_pipeline(self, monkeypatch, draft=None, saved=None, calls=None):
        """Mock the ContentPipelineTask generation path."""
        from agent.tasks.content_pipeline import ContentPipelineTask
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        calls = calls if calls is not None else []

        async def fake_generate(self, client, opportunity):
            calls.append({"client": client, "opportunity": opportunity})
            return draft

        def fake_save(self, client_id, drafts):
            return saved if saved is not None else []

        monkeypatch.setattr(ContentPipelineTask, "_generate_draft", fake_generate)
        monkeypatch.setattr(ContentPipelineTask, "_save_drafts", fake_save)
        monkeypatch.setattr(
            EditorialCalendarTickTask,
            "_resolve_client",
            lambda self, task, item: {"id": item.get("site", "x"), "name": item.get("site", "x")},
        )
        return calls

    def test_no_due_items(self):
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask
        result = asyncio.run(EditorialCalendarTickTask().execute(_make_task()))
        assert result["success"] is True
        assert result["generated"] == 0

    def test_generates_draft_and_marks_ready(self, monkeypatch):
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        item = cal.add_item(
            site="kaicalls",
            title="Missed calls cost math",
            publish_at="2020-01-01T00:00:00Z",  # long due
            keyword="missed call cost",
            persona="Admin Martyr",
        )
        calls = self._patch_pipeline(
            monkeypatch,
            draft={"topic": "Missed calls cost math", "content": "...", "status": "draft"},
            saved=["/tmp/draft.md"],
        )

        result = asyncio.run(EditorialCalendarTickTask().execute(_make_task()))

        assert result["success"] is True
        assert result["generated"] == 1
        # Same generation path as content_pipeline, with calendar metadata
        opp = calls[0]["opportunity"]
        assert opp["topic"] == "Missed calls cost math"
        assert opp["keywords"] == ["missed call cost"]
        assert opp["type"] == "blog"
        assert opp["calendar_item_id"] == item["id"]

        stored = cal.get_item(item["id"])
        assert stored["status"] == "ready"
        assert "human approval" in stored["notes"]
        # Approval doctrine: the tick NEVER publishes
        assert stored["status"] != "published"
        assert "nothing published" in result["summary"]

    def test_failed_generation_reverts_to_planned(self, monkeypatch):
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        self._patch_pipeline(monkeypatch, draft={"topic": "t", "error": "LLM down"})

        result = asyncio.run(EditorialCalendarTickTask().execute(_make_task()))

        assert result["success"] is False
        assert result["generated"] == 0
        assert any("LLM down" in e for e in result["errors"])
        stored = cal.get_item(item["id"])
        assert stored["status"] == "planned"  # retried on next tick
        assert "generation failed" in stored["notes"]

    def test_exception_during_generation_is_contained(self, monkeypatch):
        from agent.tasks.content_pipeline import ContentPipelineTask
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")

        async def boom(self, client, opportunity):
            raise RuntimeError("kaput")

        monkeypatch.setattr(ContentPipelineTask, "_generate_draft", boom)
        monkeypatch.setattr(
            EditorialCalendarTickTask,
            "_resolve_client",
            lambda self, task, item: {"id": "s", "name": "s"},
        )

        result = asyncio.run(EditorialCalendarTickTask().execute(_make_task()))
        assert result["success"] is False
        assert any("kaput" in e for e in result["errors"])
        assert cal.get_item(item["id"])["status"] == "planned"

    def test_respects_max_items_per_run(self, monkeypatch):
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        ids = [
            cal.add_item(site="s", title=f"t{i}",
                         publish_at=f"2020-01-0{i+1}T00:00:00Z")["id"]
            for i in range(4)
        ]
        calls = self._patch_pipeline(
            monkeypatch,
            draft={"topic": "t", "content": "...", "status": "draft"},
            saved=["/tmp/d.md"],
        )

        result = asyncio.run(
            EditorialCalendarTickTask().execute(_make_task(extra={"max_items": 2}))
        )
        assert result["generated"] == 2
        assert len(calls) == 2
        # Oldest two were processed; the rest remain planned
        assert cal.get_item(ids[0])["status"] == "ready"
        assert cal.get_item(ids[1])["status"] == "ready"
        assert cal.get_item(ids[2])["status"] == "planned"
        assert cal.get_item(ids[3])["status"] == "planned"

    def test_tick_recovers_stale_generating_item(self, monkeypatch, calendar_dir):
        """An item orphaned in 'generating' by a crash is swept back to
        planned at the start of the tick and generated in the same run."""
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        cal.mark_status(item["id"], "generating")
        stale_stamp = (datetime.now(timezone.utc) - timedelta(hours=7)).isoformat()
        _rewrite_item(calendar_dir, item["id"], updated_at=stale_stamp)

        self._patch_pipeline(
            monkeypatch,
            draft={"topic": "t", "content": "...", "status": "draft"},
            saved=["/tmp/d.md"],
        )
        result = asyncio.run(EditorialCalendarTickTask().execute(_make_task()))

        assert result["recovered_stale"] == 1
        assert result["generated"] == 1
        assert cal.get_item(item["id"])["status"] == "ready"

    def test_tick_leaves_fresh_generating_alone(self, monkeypatch):
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        cal.mark_status(item["id"], "generating")  # updated_at = now

        self._patch_pipeline(
            monkeypatch,
            draft={"topic": "t", "content": "...", "status": "draft"},
            saved=["/tmp/d.md"],
        )
        result = asyncio.run(EditorialCalendarTickTask().execute(_make_task()))

        assert result["recovered_stale"] == 0
        assert result["generated"] == 0
        assert cal.get_item(item["id"])["status"] == "generating"

    def test_stale_threshold_configurable_via_extra(self, monkeypatch):
        from agent.tasks.editorial_calendar import EditorialCalendarTickTask

        item = cal.add_item(site="s", title="t", publish_at="2020-01-01T00:00:00Z")
        cal.mark_status(item["id"], "generating")  # fresh, but threshold is 0h

        self._patch_pipeline(
            monkeypatch,
            draft={"topic": "t", "content": "...", "status": "draft"},
            saved=["/tmp/d.md"],
        )
        result = asyncio.run(
            EditorialCalendarTickTask().execute(
                _make_task(extra={"stale_generating_hours": 0})
            )
        )

        assert result["recovered_stale"] == 1
        assert result["generated"] == 1
        assert cal.get_item(item["id"])["status"] == "ready"

    def test_handler_registered(self):
        from agent.tasks import get_task_handler
        handler = get_task_handler("editorial_calendar_tick")
        assert handler is not None
        assert handler.task_type == "editorial_calendar_tick"
