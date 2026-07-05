"""Weekly CMO review — closes the goal loop: plan -> act -> measure -> replan.

Scheduled Monday 07:00 (agent/scheduler.py create_default_tasks). Each run:

1. Loads all active goals from the GoalRegistry (kai/runtime/goals.py).
2. Refreshes each goal's ``current_value`` where it is derivable from the
   content log (``data/content_log.json``) using the dict-tolerant grade
   helpers (``scripts/self_improvement/grades.py``). A KPI with no measured
   data is a DATA GAP — the stored value is left untouched, never zeroed
   (memory/lessons.md 2026-06-09: missing connectors are data gaps).
3. Computes pace vs deadline via ``compute_goal_pace``.
4. For each behind-pace goal with NO active task graph, decomposes the goal
   via GoalDecomposer and persists the graph (``agent_db.create_task_graph``)
   so the existing agent loop executes it. Graphs the loop flagged
   ``needs_replan`` count as inactive: the remaining work is re-decomposed
   with the failure context injected into the decomposer prompt (via goal
   metadata, which the decomposer already serializes), and the exhausted
   graph is marked ``replanned``.
5. Writes a review snapshot to ``<runtime>/goals/reviews/<date>.json``.
6. Notifies via the shared BaseTask notification helper.

Approval doctrine: this task reads local state and writes goal files and
snapshots only. Any execution it triggers flows through the existing
orchestrator, whose actions pass ActionStore approval + mandate validation
(kai/execution/executor.py). Nothing here publishes or mutates a live channel.

No LLM key configured? Decomposition is skipped as a data gap; measurement,
pace, snapshot, and notification still run — never an exception that puts
the scheduler into a crash/retry loop.
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
import sys
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..models import ScheduledTask
from .base import BaseTask

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# Any of these makes agent.llm.router usable (see router PROVIDER_KEY_ENV).
LLM_KEY_ENV_VARS = (
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
)

# Graph statuses that mean "the goal already has a plan in flight".
ACTIVE_GRAPH_STATUSES = ("pending", "running")

# KPI aliases the review can derive from the content log. Anything else is
# left to connectors/manual updates (kai-harness goals update --current).
_PUBLISHED_KPIS = {"content_published", "published_count", "published_pieces", "posts_published"}
_WINNER_KPIS = {"content_winners", "winner_count", "winners", "winners_30d"}
_CLICK_KPIS = {"organic_clicks", "gsc_clicks", "clicks", "clicks_30d"}
_IMPRESSION_KPIS = {"organic_impressions", "gsc_impressions", "impressions", "impressions_30d"}


class CMOReviewTask(BaseTask):
    """Weekly goal review: measure KPIs, check pace, (re)plan behind goals."""

    @property
    def task_type(self) -> str:
        return "cmo_review"

    @property
    def description(self) -> str:
        return "Weekly CMO review — refresh goal KPIs, check pace, decompose behind-pace goals"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            from kai.runtime.goals import GoalRegistry, compute_goal_pace
        except Exception as e:
            logger.exception("goal registry unavailable")
            return {"success": False, "error": f"goal registry unavailable: {e}"}

        try:
            registry = GoalRegistry()
            goals = [g for g in registry.list_goals() if g.status == "active"]
        except Exception as e:
            logger.exception("could not load goals")
            return {"success": False, "error": f"could not load goals: {e}"}

        entries = self._load_content_log()
        db = self._db()
        graph_index = self._graph_index(db)
        llm_available = self._llm_available()

        goal_rows: List[Dict[str, Any]] = []
        deltas: List[Dict[str, Any]] = []
        decisions: List[Dict[str, Any]] = []
        graphs_created: List[str] = []
        behind_count = 0

        for goal in goals:
            previous_value = goal.current_value
            derived = self._derive_kpi_value(goal, entries)
            refreshed = derived is not None and float(derived) != previous_value
            if refreshed:
                if goal.metadata is None:
                    goal.metadata = {}
                # Keep the original baseline so pace math stays anchored.
                goal.metadata.setdefault("baseline_value", previous_value)
                goal.current_value = float(derived)
                try:
                    registry.save_goal(goal)
                except Exception:
                    logger.warning("could not persist refreshed goal %s", goal.goal_id, exc_info=True)
                deltas.append({
                    "goal_id": goal.goal_id,
                    "kpi_name": goal.kpi_name,
                    "previous_value": previous_value,
                    "current_value": goal.current_value,
                    "source": "content_log",
                })

            pace = compute_goal_pace(goal)
            slot = graph_index.get(goal.goal_id, {"active": [], "needs_replan": []})
            goal_rows.append({
                "goal_id": goal.goal_id,
                "brand_id": goal.brand_id,
                "name": goal.name,
                "kpi_name": goal.kpi_name,
                "target_value": goal.target_value,
                "current_value": goal.current_value,
                "previous_value": previous_value,
                "target_direction": goal.target_direction,
                "deadline": goal.deadline,
                "refreshed": refreshed,
                "pace": pace,
                "active_graphs": slot["active"],
                "needs_replan_graphs": slot["needs_replan"],
            })

            if not pace["behind_pace"]:
                decisions.append({
                    "goal_id": goal.goal_id,
                    "decision": "achieved" if pace["achieved"] else "on_pace",
                })
                continue

            behind_count += 1
            if slot["active"]:
                decisions.append({
                    "goal_id": goal.goal_id,
                    "decision": "active_graph_exists",
                    "graph_ids": list(slot["active"]),
                })
                continue

            replan_context = None
            if slot["needs_replan"]:
                replan_context = self._failure_context(db, slot["needs_replan"][-1])

            if not llm_available:
                decisions.append({
                    "goal_id": goal.goal_id,
                    "decision": "decomposition_skipped_no_llm",
                    "data_gap": True,
                })
                continue

            graph_id, error = await self._decompose_and_persist(db, goal, replan_context)
            if graph_id:
                graphs_created.append(graph_id)
                # Retire the exhausted graph(s) so next week's review doesn't
                # re-inject the same failure context against the new plan.
                for old_id in slot["needs_replan"]:
                    try:
                        db.update_task_graph_status(old_id, "replanned")
                    except Exception:
                        logger.warning("could not mark graph %s replanned", old_id, exc_info=True)
                decisions.append({
                    "goal_id": goal.goal_id,
                    "decision": "replanned" if replan_context else "decomposed",
                    "graph_id": graph_id,
                    "replanned_graphs": list(slot["needs_replan"]),
                })
            else:
                decisions.append({
                    "goal_id": goal.goal_id,
                    "decision": "decomposition_failed",
                    "error": error,
                })

        snapshot_payload = {
            "task": "cmo_review",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "llm_available": llm_available,
            "goals": goal_rows,
            "deltas": deltas,
            "decisions": decisions,
            "graphs_created": graphs_created,
        }
        snapshot_path = self._write_snapshot(registry, snapshot_payload)

        summary = (
            f"CMO review: {len(goals)} active goal(s), {len(deltas)} KPI value(s) "
            f"refreshed, {behind_count} behind pace, {len(graphs_created)} task "
            f"graph(s) created (execution stays behind ActionStore approval)"
        )
        if behind_count and not llm_available:
            summary += " — decomposition skipped: no LLM key configured (data gap)"

        try:
            await self.send_notification(summary, task=task)
        except Exception:
            logger.warning("cmo_review notification failed", exc_info=True)

        return {
            "success": True,
            "summary": summary,
            "goals_reviewed": len(goals),
            "values_refreshed": len(deltas),
            "behind_pace": behind_count,
            "graphs_created": graphs_created,
            "decisions": decisions,
            "snapshot": str(snapshot_path) if snapshot_path else None,
            "llm_available": llm_available,
        }

    # ── Collaborators (small methods so tests can monkeypatch cleanly) ──────

    def _db(self):
        """Return the agent database at call time (test fixtures patch it)."""
        from .. import models as agent_models
        return agent_models.agent_db

    @staticmethod
    def _llm_available() -> bool:
        return any(os.getenv(var, "").strip() for var in LLM_KEY_ENV_VARS)

    def _load_content_log(self) -> List[Dict[str, Any]]:
        """Read the content log, returning [] on any problem (data gap)."""
        try:
            from scripts.harness_config import get_config
            path = Path(get_config().content_log)
        except Exception:
            logger.warning("harness config unavailable — no content log", exc_info=True)
            return []
        try:
            if not path.exists():
                return []
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except Exception:
            logger.warning("could not read content log %s", path, exc_info=True)
            return []

    def _derive_kpi_value(self, goal, entries: List[Dict[str, Any]]) -> Optional[float]:
        """Derive a goal's current KPI value from content-log entries.

        Returns None when the KPI is not derivable OR when there is no
        measured data for it — a data gap is never reported as zero.
        """
        try:
            from scripts.self_improvement.grades import get_grade, get_published_at
        except Exception:
            logger.warning("grades helpers unavailable", exc_info=True)
            return None

        kpi = (goal.kpi_name or "").strip().lower()
        site = (goal.metadata or {}).get("site") or goal.brand_id
        scoped = [
            e for e in entries
            if isinstance(e, dict) and (site in (None, "", "all") or e.get("site") == site)
        ]

        if kpi in _PUBLISHED_KPIS:
            if not scoped:
                return None  # no log entries for this site at all — data gap
            return float(sum(
                1 for e in scoped if e.get("url") and get_published_at(e)
            ))

        if kpi in _WINNER_KPIS:
            graded = [e for e in scoped if get_grade(e)]
            if not graded:
                return None  # nothing measured yet — data gap, not zero
            return float(sum(1 for e in graded if get_grade(e) == "winner"))

        if kpi in _CLICK_KPIS or kpi in _IMPRESSION_KPIS:
            field = "clicks" if kpi in _CLICK_KPIS else "impressions"
            values: List[float] = []
            for e in scoped:
                perf = e.get("performance_30d")
                if not isinstance(perf, dict):
                    continue
                gsc = perf.get("gsc")
                if isinstance(gsc, dict) and gsc.get(field) is not None:
                    try:
                        values.append(float(gsc[field]))
                    except (TypeError, ValueError):
                        continue
            if not values:
                return None  # no GSC-measured entries — data gap
            return float(sum(values))

        return None  # KPI not derivable from the content log

    def _graph_index(self, db) -> Dict[str, Dict[str, List[str]]]:
        """Index task graphs by goal_id into active / needs_replan buckets."""
        index: Dict[str, Dict[str, List[str]]] = {}
        try:
            with db.connect() as conn:
                conn.row_factory = sqlite3.Row
                rows = conn.execute(
                    "SELECT graph_id, goal_id, status FROM task_graphs "
                    "WHERE goal_id IS NOT NULL ORDER BY created_at ASC"
                ).fetchall()
        except Exception:
            logger.warning("could not index task graphs", exc_info=True)
            return index
        for row in rows:
            slot = index.setdefault(row["goal_id"], {"active": [], "needs_replan": []})
            if row["status"] in ACTIVE_GRAPH_STATUSES:
                slot["active"].append(row["graph_id"])
            elif row["status"] == "needs_replan":
                slot["needs_replan"].append(row["graph_id"])
        return index

    def _failure_context(self, db, graph_id: str) -> Optional[Dict[str, Any]]:
        """Summarize a needs_replan graph for the decomposer prompt."""
        try:
            graph = db.get_task_graph(graph_id)
        except Exception:
            logger.warning("could not load graph %s for replan context", graph_id, exc_info=True)
            return None
        if not graph:
            return None
        failed = [
            {"node_id": n.node_id, "task_type": n.task_type, "error": n.error}
            for n in graph.nodes.values() if n.status == "failed"
        ]
        completed = [
            {"node_id": n.node_id, "task_type": n.task_type}
            for n in graph.nodes.values() if n.status == "completed"
        ]
        remaining = [
            {"node_id": n.node_id, "task_type": n.task_type, "status": n.status}
            for n in graph.nodes.values() if n.status in ("pending", "skipped")
        ]
        return {
            "previous_graph_id": graph_id,
            "failed_nodes": failed,
            "completed_nodes": completed,
            "remaining_nodes": remaining,
            "instruction": (
                "This is a REPLAN after a failed task graph. Plan only the "
                "remaining work: do not repeat completed nodes, and design "
                "around the listed failures instead of retrying them verbatim."
            ),
        }

    async def _decompose_and_persist(
        self, db, goal, replan_context: Optional[Dict[str, Any]]
    ) -> Tuple[Optional[str], Optional[str]]:
        """Decompose a goal into a TaskGraph and persist it. Never raises."""
        try:
            from ..decomposer import GoalDecomposer
        except Exception as e:
            logger.warning("GoalDecomposer unavailable: %s", e)
            return None, f"decomposer unavailable: {e}"

        prompt_goal = goal
        if replan_context:
            # The decomposer serializes goal.metadata into its prompt, so the
            # failure context rides along without touching decomposer code.
            metadata = dict(goal.metadata or {})
            metadata["replan_context"] = replan_context
            prompt_goal = replace(goal, metadata=metadata)

        try:
            graph = await GoalDecomposer().decompose(prompt_goal)
        except Exception as e:
            logger.warning("goal decomposition failed for %s: %s", goal.goal_id, e)
            return None, str(e)

        try:
            db.create_task_graph(graph)
        except Exception as e:
            logger.exception("could not persist task graph for %s", goal.goal_id)
            return None, f"could not persist graph: {e}"
        return graph.graph_id, None

    def _write_snapshot(self, registry, payload: Dict[str, Any]) -> Optional[Path]:
        """Write the review snapshot atomically; return its path or None."""
        try:
            reviews_dir = registry.goals_dir / "reviews"
            reviews_dir.mkdir(parents=True, exist_ok=True)
            date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
            path = reviews_dir / f"{date_str}.json"
            tmp = path.with_suffix(".tmp")
            tmp.write_text(
                json.dumps(payload, indent=2, sort_keys=True, default=str),
                encoding="utf-8",
            )
            tmp.replace(path)
            return path
        except Exception:
            logger.warning("could not write review snapshot", exc_info=True)
            return None
