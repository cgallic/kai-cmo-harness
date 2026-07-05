"""Tests for scheduler self-containment: default self-improvement tasks
seeded into the scheduler, plus the wrapping task handlers.

Verifies:
- create_default_tasks() seeds performance_check_30d (0 2 * * *),
  pattern_extract_weekly (0 14 * * 1), harness_defaults_update (30 14 * * 1)
  and editorial_calendar_tick (hourly), and stays idempotent
- handlers are registered and degrade gracefully (missing credentials /
  dependencies are data gaps, never exceptions that crash the loop)
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.models import AgentDatabase
from agent.scheduler import Scheduler
from agent.tasks import get_task_handler
import agent.tasks.self_improvement as si


NEW_DEFAULT_TASKS = {
    "30-Day Performance Check": ("0 2 * * *", "performance_check_30d"),
    "Weekly Pattern Extraction": ("0 14 * * 1", "pattern_extract_weekly"),
    "Harness Defaults Update": ("30 14 * * 1", "harness_defaults_update"),
    "Editorial Calendar Tick": ("0 * * * *", "editorial_calendar_tick"),
}


@pytest.fixture
def scheduler(tmp_path):
    sched = Scheduler()
    sched.db = AgentDatabase(db_path=tmp_path / "sched_test.db")
    return sched


# ---------------------------------------------------------------------------
# Default task seeding
# ---------------------------------------------------------------------------


class TestDefaultTaskSeeding:
    def test_self_improvement_tasks_seeded(self, scheduler):
        scheduler.create_default_tasks()
        tasks = {t.name: t for t in scheduler.db.list_scheduled_tasks(enabled_only=False)}

        for name, (cron, task_type) in NEW_DEFAULT_TASKS.items():
            assert name in tasks, f"default task missing: {name}"
            assert tasks[name].cron_expression == cron
            assert tasks[name].task_type == task_type
            assert tasks[name].enabled is True
            assert tasks[name].next_run_at is not None

    def test_seeding_is_idempotent(self, scheduler):
        scheduler.create_default_tasks()
        first = scheduler.db.list_scheduled_tasks(enabled_only=False)
        scheduler.create_default_tasks()
        second = scheduler.db.list_scheduled_tasks(enabled_only=False)
        assert len(first) == len(second)
        # No duplicate names
        names = [t.name for t in second]
        assert len(names) == len(set(names))

    def test_every_seeded_task_type_has_new_handlers(self, scheduler):
        """The four new task types must resolve to registered handlers."""
        for _, (_, task_type) in NEW_DEFAULT_TASKS.items():
            handler = get_task_handler(task_type)
            assert handler is not None, f"no handler registered for {task_type}"
            assert handler.task_type == task_type


# ---------------------------------------------------------------------------
# performance_check_30d handler
# ---------------------------------------------------------------------------


class TestPerformanceCheck30d:
    def test_no_pending_checks(self, monkeypatch):
        import scripts.self_improvement.performance_check as pc
        monkeypatch.setattr(pc, "reconcile_pending_checks", lambda: 2)
        monkeypatch.setattr(pc, "get_pending_checks", lambda: [])

        result = asyncio.run(si.PerformanceCheck30dTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["checked"] == 0
        assert result["reconciled"] == 2
        assert "No 30-day checks due" in result["summary"]

    def test_missing_google_creds_is_data_gap_not_grading(self, monkeypatch, tmp_path):
        """Without GSC/GA4 creds, due checks are DEFERRED — never graded as
        zeros (memory/lessons.md 2026-06-09)."""
        import scripts.self_improvement.performance_check as pc
        monkeypatch.setattr(pc, "reconcile_pending_checks", lambda: 0)
        monkeypatch.setattr(
            pc, "get_pending_checks",
            lambda: [(tmp_path / "c1.json", {"id": "c1"})],
        )

        def fail_run_check(*args, **kwargs):
            raise AssertionError("run_check must not be called without credentials")

        monkeypatch.setattr(pc, "run_check", fail_run_check)
        monkeypatch.delenv("GOOGLE_CREDENTIALS_PATH", raising=False)

        result = asyncio.run(si.PerformanceCheck30dTask().execute(MagicMock()))
        assert result["success"] is False
        assert result["data_gap"] is True
        assert result["deferred"] == 1
        assert "GOOGLE_CREDENTIALS_PATH" in result["error"]

    def test_runs_due_checks_with_creds(self, monkeypatch, tmp_path):
        import scripts.self_improvement.performance_check as pc

        creds = tmp_path / "creds.json"
        creds.write_text("{}")
        monkeypatch.setenv("GOOGLE_CREDENTIALS_PATH", str(creds))

        monkeypatch.setattr(pc, "reconcile_pending_checks", lambda: 1)
        monkeypatch.setattr(
            pc, "get_pending_checks",
            lambda: [
                (tmp_path / "a.json", {"id": "a"}),
                (tmp_path / "b.json", {"id": "b"}),
            ],
        )
        run_calls = []

        def fake_run_check(check_file, check, **kwargs):
            run_calls.append(check["id"])
            return {
                "entry_id": check["id"],
                "url": f"https://x.test/{check['id']}",
                "evaluation": {"is_winner": check["id"] == "a"},
            }

        monkeypatch.setattr(pc, "run_check", fake_run_check)

        # Winner → pattern extraction via subprocess; stub it out.
        sub_calls = []

        def fake_subprocess_run(cmd, **kwargs):
            sub_calls.append(cmd)
            return SimpleNamespace(returncode=0, stdout="", stderr="")

        monkeypatch.setattr(si.subprocess, "run", fake_subprocess_run)

        result = asyncio.run(si.PerformanceCheck30dTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["checked"] == 2
        assert result["winners"] == 1
        assert run_calls == ["a", "b"]
        assert len(sub_calls) == 1
        assert "--url" in sub_calls[0]
        assert "https://x.test/a" in sub_calls[0]

    def test_exception_contained_not_raised(self, monkeypatch):
        import scripts.self_improvement.performance_check as pc
        monkeypatch.setattr(pc, "reconcile_pending_checks", lambda: 0)

        def boom():
            raise RuntimeError("db locked")

        monkeypatch.setattr(pc, "get_pending_checks", boom)
        result = asyncio.run(si.PerformanceCheck30dTask().execute(MagicMock()))
        assert result["success"] is False
        assert "db locked" in result["error"]

    def test_import_failure_is_graceful(self, monkeypatch):
        monkeypatch.setattr(si, "_import_module", lambda dotted: (None, "no module"))
        result = asyncio.run(si.PerformanceCheck30dTask().execute(MagicMock()))
        assert result["success"] is False
        assert "unavailable" in result["error"]


# ---------------------------------------------------------------------------
# pattern_extract_weekly handler
# ---------------------------------------------------------------------------


class TestPatternExtractWeekly:
    def test_import_failure_is_data_gap(self, monkeypatch):
        """google-genai missing (as in CI) must degrade, never crash."""
        monkeypatch.setattr(
            si, "_import_module", lambda dotted: (None, "cannot import genai")
        )
        result = asyncio.run(si.PatternExtractWeeklyTask().execute(MagicMock()))
        assert result["success"] is False
        assert result["data_gap"] is True
        assert "genai" in result["error"]

    def test_missing_gemini_key_is_data_gap(self, monkeypatch):
        fake_mod = SimpleNamespace(_CFG=SimpleNamespace(gemini_api_key=""))
        monkeypatch.setattr(si, "_import_module", lambda dotted: (fake_mod, None))
        result = asyncio.run(si.PatternExtractWeeklyTask().execute(MagicMock()))
        assert result["success"] is False
        assert result["data_gap"] is True
        assert "GEMINI_API_KEY" in result["error"]

    def test_runs_winner_mining_and_weekly_aggregation(self, monkeypatch, tmp_path):
        content_log = tmp_path / "content_log.json"
        appended = []

        fake_mod = SimpleNamespace(
            _CFG=SimpleNamespace(gemini_api_key="key"),
            CONTENT_LOG=str(content_log),
            load_log=lambda: [
                {"id": "w1", "url": "https://x.test/w1", "_winner": True},
                {"id": "n1", "url": "https://x.test/n1", "_winner": False},
            ],
            is_winner=lambda e: e.get("_winner", False),
            analyze_winner=lambda e: f"analysis for {e['id']}",
            append_to_what_works=lambda e, a: appended.append((e["id"], a)),
            run_weekly_aggregation=lambda site: "3 patterns surfaced",
        )
        monkeypatch.setattr(si, "_import_module", lambda dotted: (fake_mod, None))

        result = asyncio.run(si.PatternExtractWeeklyTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["winners_processed"] == 1
        assert appended == [("w1", "analysis for w1")]
        assert result["patterns"] == "3 patterns surfaced"
        assert content_log.exists()  # updated log persisted

    def test_gemini_failure_contained(self, monkeypatch):
        def raise_gemini(site):
            raise RuntimeError("Circuit breaker open")

        fake_mod = SimpleNamespace(
            _CFG=SimpleNamespace(gemini_api_key="key"),
            CONTENT_LOG="/nonexistent/content_log.json",
            load_log=lambda: [],
            is_winner=lambda e: False,
            run_weekly_aggregation=raise_gemini,
        )
        monkeypatch.setattr(si, "_import_module", lambda dotted: (fake_mod, None))

        result = asyncio.run(si.PatternExtractWeeklyTask().execute(MagicMock()))
        assert result["success"] is False
        assert any("Circuit breaker" in e for e in result["errors"])


# ---------------------------------------------------------------------------
# harness_defaults_update handler
# ---------------------------------------------------------------------------


class TestHarnessDefaultsUpdate:
    def test_insufficient_data_is_success_with_data_gap_note(self, monkeypatch):
        fake_mod = SimpleNamespace(
            load_log=lambda: [],
            analyze_patterns=lambda entries: {
                "insufficient_data": True, "n": 2, "required": 10,
            },
        )
        monkeypatch.setattr(si, "_import_module", lambda dotted: (fake_mod, None))

        result = asyncio.run(si.HarnessDefaultsUpdateTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["updated"] == 0
        assert "Insufficient data" in result["summary"]

    def test_applies_updates_through_guarded_writers(self, monkeypatch):
        saved = []
        posted = []
        patterns = {"best_publish_day": {"day": "Tuesday", "n": 12}}

        fake_mod = SimpleNamespace(
            load_log=lambda: [{"id": 1}],
            analyze_patterns=lambda entries: patterns,
            update_marketing_md=lambda p: ["- best publish day: Tuesday"],
            update_policy_thresholds=lambda p: {
                "updates": ["- policy.yaml: approve 85->80"],
                "drift_alerts": [],
            },
            save_defaults=lambda p: saved.append(p),
            post_discord=lambda updates, p: posted.append(updates),
            post_drift_alert=lambda alerts: pytest.fail("no drift expected"),
        )
        monkeypatch.setattr(si, "_import_module", lambda dotted: (fake_mod, None))

        result = asyncio.run(si.HarnessDefaultsUpdateTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["updated"] == 2
        assert saved == [patterns]
        assert len(posted) == 1

    def test_drift_alerts_halt_and_are_reported(self, monkeypatch):
        drift_posts = []
        fake_mod = SimpleNamespace(
            load_log=lambda: [{"id": 1}],
            analyze_patterns=lambda entries: {"best_publish_day": {"day": "Tue"}},
            update_marketing_md=lambda p: [],
            update_policy_thresholds=lambda p: {
                "updates": [],
                "drift_alerts": ["DRIFT: policy.yaml auto_approve_above 85->40"],
            },
            save_defaults=lambda p: pytest.fail("must not save on drift-only run"),
            post_discord=lambda updates, p: pytest.fail("no digest without updates"),
            post_drift_alert=lambda alerts: drift_posts.append(alerts),
        )
        monkeypatch.setattr(si, "_import_module", lambda dotted: (fake_mod, None))

        result = asyncio.run(si.HarnessDefaultsUpdateTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["updated"] == 0
        assert len(result["drift_alerts"]) == 1
        assert len(drift_posts) == 1

    def test_analysis_exception_contained(self, monkeypatch):
        def boom(entries):
            raise ValueError("corrupt log")

        fake_mod = SimpleNamespace(load_log=lambda: [], analyze_patterns=boom)
        monkeypatch.setattr(si, "_import_module", lambda dotted: (fake_mod, None))

        result = asyncio.run(si.HarnessDefaultsUpdateTask().execute(MagicMock()))
        assert result["success"] is False
        assert "corrupt log" in result["error"]

    def test_import_failure_is_graceful(self, monkeypatch):
        monkeypatch.setattr(si, "_import_module", lambda dotted: (None, "gone"))
        result = asyncio.run(si.HarnessDefaultsUpdateTask().execute(MagicMock()))
        assert result["success"] is False
        assert "unavailable" in result["error"]


# ---------------------------------------------------------------------------
# Real-module smoke: pattern_extract import degrades in this environment
# ---------------------------------------------------------------------------


class TestRealModuleDegradation:
    def test_pattern_extract_handler_never_raises(self):
        """Whatever this environment has installed, execute() must return a
        dict — never raise (crash-loop guard)."""
        result = asyncio.run(si.PatternExtractWeeklyTask().execute(MagicMock()))
        assert isinstance(result, dict)
        assert "success" in result
