"""Tests for Workstream E — the closed goal loop.

Covers:
- goals CLI round-trip (kai-harness goals add|list|update)
- pace helpers in kai/runtime/goals.py
- CMOReviewTask: KPI refresh from the content log (data gaps never zeroed),
  graph creation only for behind-pace goals without active graphs,
  needs_replan re-decomposition with failure context, snapshot writing,
  and graceful no-LLM degradation
- scheduler seeding of the Weekly CMO Review task
- agent loop: needs_replan preserved by _update_graph_status_if_done
"""

from __future__ import annotations

import asyncio
import json
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

import agent.models
from agent.models import AgentDatabase
from agent.scheduler import Scheduler
from agent.tasks import get_task_handler
from agent.tasks.cmo_review import CMOReviewTask, LLM_KEY_ENV_VARS
from kai.runtime.goals import (
    GoalRegistry,
    compute_goal_pace,
    is_goal_achieved,
    parse_goal_datetime,
)
from kai.runtime.models import KaiGoal, TaskGraph, TaskNode


def _utc(offset_days: float = 0) -> datetime:
    return datetime.now(timezone.utc) + timedelta(days=offset_days)


def _make_goal(
    registry: GoalRegistry,
    *,
    brand_id: str = "brandx",
    kpi: str = "organic_clicks",
    target: float = 100.0,
    current: float = 10.0,
    deadline: str | None = None,
    metadata: dict | None = None,
) -> KaiGoal:
    return registry.create_goal(
        brand_id=brand_id,
        name=f"{kpi} goal",
        kpi_name=kpi,
        target_value=target,
        current_value=current,
        target_direction="increase",
        deadline=deadline if deadline is not None else _utc(-1).isoformat(),
        metadata=metadata or {"baseline_value": current},
    )


def _make_graph(db: AgentDatabase, goal_id: str, status: str, graph_id: str,
                nodes: dict | None = None, edges: list | None = None) -> TaskGraph:
    graph = TaskGraph(
        graph_id=graph_id,
        goal_id=goal_id,
        brand_id="brandx",
        status=status,  # type: ignore[arg-type]
        nodes=nodes or {
            "n1": TaskNode(node_id="n1", task_type="seo_optimization", status="pending"),
        },
        edges=edges or [],
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat(),
    )
    db.create_task_graph(graph)
    return graph


MOCK_DECOMPOSE_RESPONSE = """
{
  "nodes": [
    {"node_id": "step_1", "task_type": "content_pipeline", "inputs": {"k": "v"}}
  ],
  "edges": []
}
"""


@pytest.fixture
def review_env(tmp_path, monkeypatch):
    """Isolated GoalRegistry (via env), agent db, notifications, content log."""
    runtime_dir = tmp_path / "runtime"
    monkeypatch.setenv("KAI_RUNTIME_DIR", str(runtime_dir))

    db = AgentDatabase(db_path=tmp_path / "agent.db")
    monkeypatch.setattr(agent.models, "agent_db", db)

    # Deterministic LLM availability: one key set by default.
    for var in LLM_KEY_ENV_VARS:
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    # No content log unless a test provides one.
    monkeypatch.setattr(CMOReviewTask, "_load_content_log", lambda self: [])

    notifications: list[str] = []

    async def capture_notification(self, message, task=None):
        notifications.append(message)

    monkeypatch.setattr(CMOReviewTask, "send_notification", capture_notification)

    registry = GoalRegistry(base_dir=runtime_dir)
    return {
        "registry": registry,
        "db": db,
        "runtime_dir": runtime_dir,
        "notifications": notifications,
    }


def _mock_llm(monkeypatch, response: str = MOCK_DECOMPOSE_RESPONSE):
    from agent.decomposer import llm_router

    captured: list[str] = []

    async def mock_complete(prompt, **kwargs):
        captured.append(prompt)
        return response

    monkeypatch.setattr(llm_router, "complete", mock_complete)
    return captured


# ---------------------------------------------------------------------------
# Pace helpers
# ---------------------------------------------------------------------------


class TestPaceHelpers:
    def test_parse_goal_datetime_tolerant(self):
        assert parse_goal_datetime("") is None
        assert parse_goal_datetime(None) is None
        assert parse_goal_datetime("not-a-date") is None
        dt = parse_goal_datetime("2026-12-31")
        assert dt is not None and dt.tzinfo is not None
        dt_z = parse_goal_datetime("2026-12-31T10:00:00Z")
        assert dt_z is not None and dt_z.utcoffset().total_seconds() == 0

    def test_achieved_direction_aware(self):
        inc = KaiGoal("g1", "b", "n", "k", 100.0, 100.0, "increase")
        dec = KaiGoal("g2", "b", "n", "k", 10.0, 9.0, "decrease")
        assert is_goal_achieved(inc) is True
        assert is_goal_achieved(dec) is True
        assert is_goal_achieved(KaiGoal("g3", "b", "n", "k", 100.0, 99.0, "increase")) is False

    def test_achieved_goal_never_behind(self):
        goal = KaiGoal("g", "b", "n", "k", 100.0, 150.0, "increase",
                       deadline=_utc(-10).isoformat())
        pace = compute_goal_pace(goal)
        assert pace["achieved"] is True
        assert pace["behind_pace"] is False

    def test_overdue_unachieved_is_behind(self):
        goal = KaiGoal("g", "b", "n", "k", 100.0, 10.0, "increase",
                       deadline=_utc(-1).isoformat(),
                       created_at=_utc(-30).isoformat())
        pace = compute_goal_pace(goal)
        assert pace["overdue"] is True
        assert pace["behind_pace"] is True

    def test_early_goal_on_pace(self):
        goal = KaiGoal("g", "b", "n", "k", 100.0, 5.0, "increase",
                       deadline=_utc(365).isoformat(),
                       created_at=_utc(0).isoformat())
        pace = compute_goal_pace(goal)
        assert pace["behind_pace"] is False
        assert pace["time_fraction"] is not None and pace["time_fraction"] < 0.05

    def test_mid_deadline_lagging_is_behind(self):
        goal = KaiGoal("g", "b", "n", "k", 100.0, 10.0, "increase",
                       deadline=_utc(10).isoformat(),
                       created_at=_utc(-90).isoformat(),
                       metadata={"baseline_value": 0.0})
        pace = compute_goal_pace(goal)
        assert pace["time_fraction"] > 0.8
        assert pace["progress_fraction"] == pytest.approx(0.1)
        assert pace["behind_pace"] is True
        assert pace["expected_value"] > 80.0

    def test_no_deadline_unachieved_is_behind(self):
        goal = KaiGoal("g", "b", "n", "k", 100.0, 10.0, "increase", deadline="")
        assert compute_goal_pace(goal)["behind_pace"] is True


# ---------------------------------------------------------------------------
# Goals CLI round-trip
# ---------------------------------------------------------------------------


class TestGoalsCli:
    def _run_cli(self, monkeypatch, capsys, argv: list[str]) -> str:
        import scripts.harness_cli as cli

        monkeypatch.setattr(sys, "argv", ["kai-harness"] + argv)
        cli.main()
        return capsys.readouterr().out

    def test_add_list_update_round_trip(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("KAI_RUNTIME_DIR", str(tmp_path / "runtime"))

        out = self._run_cli(monkeypatch, capsys, [
            "goals", "add",
            "--brand", "brandx",
            "--name", "Q3 organic clicks",
            "--kpi", "organic_clicks",
            "--target", "5000",
            "--current", "100",
            "--deadline", "2027-01-01",
            "--site", "brandx-site",
        ])
        m = re.search(r"Created goal (goal_\w+)", out)
        assert m, out
        goal_id = m.group(1)

        out = self._run_cli(monkeypatch, capsys, ["goals", "list", "--json"])
        goals = json.loads(out)
        assert len(goals) == 1
        assert goals[0]["goal_id"] == goal_id
        assert goals[0]["kpi_name"] == "organic_clicks"
        assert goals[0]["target_value"] == 5000.0
        assert goals[0]["current_value"] == 100.0
        assert goals[0]["metadata"]["baseline_value"] == 100.0
        assert goals[0]["metadata"]["site"] == "brandx-site"

        out = self._run_cli(monkeypatch, capsys, [
            "goals", "update", goal_id, "--current", "1200", "--status", "achieved",
        ])
        assert "Updated goal" in out

        # Achieved goals drop out of the default list, appear with --all.
        out = self._run_cli(monkeypatch, capsys, ["goals", "list", "--json"])
        assert json.loads(out) == []
        out = self._run_cli(monkeypatch, capsys, ["goals", "list", "--all", "--json"])
        goals = json.loads(out)
        assert goals[0]["current_value"] == 1200.0
        assert goals[0]["status"] == "achieved"

        # And the registry on disk agrees (round trip through GoalRegistry).
        registry = GoalRegistry(base_dir=tmp_path / "runtime")
        stored = registry.get_goal(goal_id)
        assert stored is not None
        assert stored.current_value == 1200.0
        assert stored.status == "achieved"

    def test_update_unknown_goal_exits_nonzero(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("KAI_RUNTIME_DIR", str(tmp_path / "runtime"))
        with pytest.raises(SystemExit):
            self._run_cli(monkeypatch, capsys, [
                "goals", "update", "goal_nope", "--current", "1",
            ])

    def test_human_list_flags_behind_pace(self, tmp_path, monkeypatch, capsys):
        monkeypatch.setenv("KAI_RUNTIME_DIR", str(tmp_path / "runtime"))
        self._run_cli(monkeypatch, capsys, [
            "goals", "add", "--brand", "b", "--name", "Late goal",
            "--kpi", "clicks", "--target", "100", "--current", "1",
            "--deadline", "2026-01-01",
        ])
        out = self._run_cli(monkeypatch, capsys, ["goals", "list"])
        assert "BEHIND PACE" in out
        assert "overdue" in out


# ---------------------------------------------------------------------------
# CMOReviewTask — KPI refresh
# ---------------------------------------------------------------------------


class TestKpiRefresh:
    def test_refreshes_derivable_kpi_and_records_delta(self, review_env, monkeypatch):
        registry = review_env["registry"]
        goal = _make_goal(registry, kpi="organic_clicks", current=10.0,
                          deadline=_utc(300).isoformat())

        entries = [
            {"site": "brandx", "performance_30d": {"gsc": {"clicks": 100}, "grade": "winner"}},
            {"site": "brandx", "performance_30d": {"gsc": {"clicks": 50}, "grade": "average"}},
            {"site": "other", "performance_30d": {"gsc": {"clicks": 999}, "grade": "winner"}},
            {"site": "brandx"},  # unmeasured — ignored, not zeroed
        ]
        monkeypatch.setattr(CMOReviewTask, "_load_content_log", lambda self: entries)

        result = asyncio.run(CMOReviewTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["values_refreshed"] == 1

        stored = registry.get_goal(goal.goal_id)
        assert stored.current_value == 150.0
        # Baseline stays anchored at the original value.
        assert stored.metadata["baseline_value"] == 10.0

    def test_missing_data_is_gap_not_zero(self, review_env, monkeypatch):
        registry = review_env["registry"]
        goal = _make_goal(registry, kpi="organic_clicks", current=42.0,
                          deadline=_utc(300).isoformat())
        # Entries exist but none has measured GSC data.
        entries = [{"site": "brandx"}, {"site": "brandx", "performance_30d": None}]
        monkeypatch.setattr(CMOReviewTask, "_load_content_log", lambda self: entries)

        result = asyncio.run(CMOReviewTask().execute(MagicMock()))
        assert result["values_refreshed"] == 0
        assert registry.get_goal(goal.goal_id).current_value == 42.0

    def test_derivers_tolerate_legacy_grade_shapes(self, review_env):
        handler = CMOReviewTask()
        goal = KaiGoal("g", "brandx", "n", "content_winners", 10.0, 0.0, "increase")
        entries = [
            {"site": "brandx", "performance_30d": {"grade": "winner"}},   # dict schema
            {"site": "brandx", "performance_30d": "loser"},               # legacy string
            {"site": "brandx", "performance_30d": "winner"},              # legacy string
        ]
        assert handler._derive_kpi_value(goal, entries) == 2.0

    def test_non_derivable_kpi_left_alone(self, review_env):
        handler = CMOReviewTask()
        goal = KaiGoal("g", "brandx", "n", "demo_bookings", 10.0, 3.0, "increase")
        assert handler._derive_kpi_value(goal, [{"site": "brandx", "url": "x"}]) is None


# ---------------------------------------------------------------------------
# CMOReviewTask — planning decisions
# ---------------------------------------------------------------------------


class TestReviewPlanning:
    def test_creates_graph_only_for_behind_pace_goal_without_active_graph(
        self, review_env, monkeypatch
    ):
        registry, db = review_env["registry"], review_env["db"]
        behind = _make_goal(registry, kpi="organic_clicks")              # overdue → behind
        on_pace = _make_goal(registry, kpi="content_winners",
                             deadline=_utc(365).isoformat())             # just created → on pace
        covered = _make_goal(registry, kpi="organic_impressions")        # behind but has graph
        _make_graph(db, covered.goal_id, "running", "graph_active_1")

        captured = _mock_llm(monkeypatch)

        result = asyncio.run(CMOReviewTask().execute(MagicMock()))
        assert result["success"] is True
        assert len(result["graphs_created"]) == 1
        assert len(captured) == 1  # decomposer called exactly once

        decisions = {d["goal_id"]: d for d in result["decisions"]}
        assert decisions[behind.goal_id]["decision"] == "decomposed"
        assert decisions[on_pace.goal_id]["decision"] == "on_pace"
        assert decisions[covered.goal_id]["decision"] == "active_graph_exists"

        # The new graph is persisted, pending, and bound to the behind goal —
        # the existing agent loop will pick it up from list_active_task_graphs.
        active = db.list_active_task_graphs()
        goal_ids = {g.goal_id for g in active}
        assert behind.goal_id in goal_ids
        new_graph = next(g for g in active if g.goal_id == behind.goal_id)
        assert new_graph.status == "pending"
        assert "step_1" in new_graph.nodes

    def test_needs_replan_graph_is_replanned_with_failure_context(
        self, review_env, monkeypatch
    ):
        registry, db = review_env["registry"], review_env["db"]
        goal = _make_goal(registry, kpi="organic_clicks")
        _make_graph(
            db, goal.goal_id, "needs_replan", "graph_dead_1",
            nodes={
                "audit": TaskNode(node_id="audit", task_type="seo_optimization",
                                  status="failed", error="GSC quota exceeded"),
                "write": TaskNode(node_id="write", task_type="content_pipeline",
                                  status="skipped"),
            },
            edges=[["audit", "write"]],
        )

        captured = _mock_llm(monkeypatch)

        result = asyncio.run(CMOReviewTask().execute(MagicMock()))
        assert len(result["graphs_created"]) == 1

        decision = next(d for d in result["decisions"] if d["goal_id"] == goal.goal_id)
        assert decision["decision"] == "replanned"
        assert decision["replanned_graphs"] == ["graph_dead_1"]

        # Failure context reached the decomposer prompt via goal metadata.
        prompt = captured[0]
        assert "replan_context" in prompt
        assert "GSC quota exceeded" in prompt
        assert "graph_dead_1" in prompt

        # Old graph retired; new one active.
        assert db.get_task_graph("graph_dead_1").status == "replanned"
        active = db.list_active_task_graphs()
        assert len(active) == 1 and active[0].goal_id == goal.goal_id

    def test_no_llm_key_degrades_gracefully(self, review_env, monkeypatch):
        registry = review_env["registry"]
        goal = _make_goal(registry, kpi="organic_clicks")
        for var in LLM_KEY_ENV_VARS:
            monkeypatch.delenv(var, raising=False)

        def fail_decompose(*args, **kwargs):
            raise AssertionError("decomposer must not be called without an LLM key")

        monkeypatch.setattr(CMOReviewTask, "_decompose_and_persist", fail_decompose)

        result = asyncio.run(CMOReviewTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["graphs_created"] == []
        assert result["llm_available"] is False
        decision = next(d for d in result["decisions"] if d["goal_id"] == goal.goal_id)
        assert decision["decision"] == "decomposition_skipped_no_llm"
        assert decision["data_gap"] is True
        # Snapshot + notification still happen.
        assert result["snapshot"] and Path(result["snapshot"]).exists()
        assert len(review_env["notifications"]) == 1
        assert "no LLM key" in review_env["notifications"][0]

    def test_decomposition_failure_contained(self, review_env, monkeypatch):
        registry = review_env["registry"]
        goal = _make_goal(registry, kpi="organic_clicks")

        from agent.decomposer import llm_router

        async def boom(prompt, **kwargs):
            raise RuntimeError("provider down")

        monkeypatch.setattr(llm_router, "complete", boom)

        result = asyncio.run(CMOReviewTask().execute(MagicMock()))
        assert result["success"] is True  # review completed; planning failed
        decision = next(d for d in result["decisions"] if d["goal_id"] == goal.goal_id)
        assert decision["decision"] == "decomposition_failed"
        assert "provider down" in decision["error"]

    def test_snapshot_written_with_goals_deltas_decisions(self, review_env, monkeypatch):
        registry = review_env["registry"]
        runtime_dir = review_env["runtime_dir"]
        _make_goal(registry, kpi="organic_clicks", current=10.0)
        entries = [{"site": "brandx", "performance_30d": {"gsc": {"clicks": 75}, "grade": "average"}}]
        monkeypatch.setattr(CMOReviewTask, "_load_content_log", lambda self: entries)
        _mock_llm(monkeypatch)

        result = asyncio.run(CMOReviewTask().execute(MagicMock()))

        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        snapshot_path = runtime_dir / "goals" / "reviews" / f"{date_str}.json"
        assert str(snapshot_path) == result["snapshot"]
        snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
        assert snapshot["task"] == "cmo_review"
        assert len(snapshot["goals"]) == 1
        assert snapshot["goals"][0]["current_value"] == 75.0
        assert snapshot["deltas"][0]["previous_value"] == 10.0
        assert snapshot["decisions"]
        assert snapshot["graphs_created"] == result["graphs_created"]
        # The reviews subdir must not confuse the goal registry.
        assert len(registry.list_goals()) == 1

    def test_no_active_goals_still_snapshots_and_notifies(self, review_env):
        result = asyncio.run(CMOReviewTask().execute(MagicMock()))
        assert result["success"] is True
        assert result["goals_reviewed"] == 0
        assert result["snapshot"] and Path(result["snapshot"]).exists()
        assert len(review_env["notifications"]) == 1


# ---------------------------------------------------------------------------
# Scheduler + handler registration
# ---------------------------------------------------------------------------


class TestScheduling:
    def test_default_task_seeded_monday_7am(self, tmp_path):
        sched = Scheduler()
        sched.db = AgentDatabase(db_path=tmp_path / "sched.db")
        sched.create_default_tasks()
        tasks = {t.name: t for t in sched.db.list_scheduled_tasks(enabled_only=False)}
        assert "Weekly CMO Review" in tasks
        task = tasks["Weekly CMO Review"]
        assert task.cron_expression == "0 7 * * 1"
        assert task.task_type == "cmo_review"
        assert task.enabled is True

        # Idempotent reseed.
        sched.create_default_tasks()
        names = [t.name for t in sched.db.list_scheduled_tasks(enabled_only=False)]
        assert names.count("Weekly CMO Review") == 1

    def test_handler_registered(self):
        handler = get_task_handler("cmo_review")
        assert handler is not None
        assert handler.task_type == "cmo_review"


# ---------------------------------------------------------------------------
# Agent loop — needs_replan status handling
# ---------------------------------------------------------------------------


class TestLoopReplanStatus:
    def test_update_graph_status_preserves_needs_replan(self, tmp_path, monkeypatch):
        import agent.loop as loop_mod
        from agent.loop import AgentLoop

        db = AgentDatabase(db_path=tmp_path / "loop.db")
        monkeypatch.setattr(loop_mod, "agent_db", db)

        graph = _make_graph(
            db, "goal_x", "needs_replan", "graph_nr",
            nodes={
                "a": TaskNode(node_id="a", task_type="t", status="failed", error="boom"),
                "b": TaskNode(node_id="b", task_type="t", status="skipped"),
            },
            edges=[["a", "b"]],
        )
        AgentLoop()._update_graph_status_if_done(graph.graph_id)
        assert db.get_task_graph("graph_nr").status == "needs_replan"
        # And it is not in the active set the executor polls.
        assert db.list_active_task_graphs() == []
