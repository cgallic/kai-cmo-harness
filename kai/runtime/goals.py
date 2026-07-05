"""Thread-safe file-backed persistence for brand goals and KPI targets."""

from __future__ import annotations

import json
import os
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.harness_config import get_config
from .models import KaiGoal


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


class GoalRegistry:
    """Thread-safe file-backed registry for tracking brand goals and targets."""

    def __init__(self, base_dir: Optional[Path] = None):
        cfg = get_config()
        if base_dir is None:
            base_dir = Path(os.environ.get("KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")))
        self.base_dir = base_dir
        self.goals_dir = _ensure_dir(self.base_dir / "goals")
        self._lock = threading.RLock()

    @classmethod
    def default(cls) -> GoalRegistry:
        return cls()

    def create_goal(
        self,
        brand_id: str,
        name: str,
        kpi_name: str,
        target_value: float,
        current_value: float,
        target_direction: str,  # "increase" | "decrease"
        goal_id: Optional[str] = None,
        deadline: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> KaiGoal:
        """Create and persist a new goal."""
        with self._lock:
            g_id = goal_id or f"goal_{uuid.uuid4().hex[:8]}"
            now = _utc_now()
            
            goal = KaiGoal(
                goal_id=g_id,
                brand_id=brand_id,
                name=name,
                kpi_name=kpi_name,
                target_value=float(target_value),
                current_value=float(current_value),
                target_direction=target_direction,  # type: ignore
                status="active",
                deadline=deadline,
                created_at=now,
                updated_at=now,
                metadata=metadata or {},
            )
            self.save_goal(goal)
            return goal

    def get_goal(self, goal_id: str) -> Optional[KaiGoal]:
        """Retrieve a goal by ID."""
        goal_file = self.goals_dir / f"{goal_id}.json"
        with self._lock:
            if not goal_file.is_file():
                return None
            try:
                data = json.loads(goal_file.read_text(encoding="utf-8"))
                return KaiGoal(
                    goal_id=data["goal_id"],
                    brand_id=data["brand_id"],
                    name=data["name"],
                    kpi_name=data["kpi_name"],
                    target_value=data["target_value"],
                    current_value=data["current_value"],
                    target_direction=data["target_direction"],
                    status=data.get("status", "active"),
                    deadline=data.get("deadline", ""),
                    created_at=data.get("created_at", ""),
                    updated_at=data.get("updated_at", ""),
                    metadata=data.get("metadata", {}),
                )
            except Exception:
                return None

    def save_goal(self, goal: KaiGoal) -> None:
        """Persist or update a goal."""
        goal.updated_at = _utc_now()
        goal_file = self.goals_dir / f"{goal.goal_id}.json"
        
        # Build payload
        payload = goal.model_dump()
        
        with self._lock:
            tmp_path = goal_file.with_suffix(".tmp")
            tmp_path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")
            tmp_path.replace(goal_file)

    def list_goals(self, brand_id: Optional[str] = None) -> List[KaiGoal]:
        """List all goals, optionally filtered by brand_id."""
        goals = []
        with self._lock:
            for filepath in self.goals_dir.glob("*.json"):
                goal_id = filepath.stem
                goal = self.get_goal(goal_id)
                if goal:
                    if brand_id is None or goal.brand_id == brand_id:
                        goals.append(goal)
        return goals

    def delete_goal(self, goal_id: str) -> bool:
        """Delete a goal from the registry."""
        goal_file = self.goals_dir / f"{goal_id}.json"
        with self._lock:
            if goal_file.is_file():
                goal_file.unlink()
                return True
            return False


_global_registry_lock = threading.Lock()
_global_registry: Optional[GoalRegistry] = None


def get_default_goal_registry() -> GoalRegistry:
    """Thread-safe singleton helper for the default goal store."""
    global _global_registry
    with _global_registry_lock:
        if _global_registry is None:
            _global_registry = GoalRegistry.default()
        return _global_registry


# ── Pace helpers (pure functions — no I/O) ──────────────────────────────────
# Used by the goals CLI (scripts/harness_cli.py) and the weekly CMO review
# (agent/tasks/cmo_review.py) to decide whether a goal is behind pace.

# A goal is "on pace" while its progress fraction is within this slack of the
# elapsed-time fraction. Keeps the review from replanning on tiny wobbles.
PACE_TOLERANCE = 0.05


def parse_goal_datetime(value: Any) -> Optional[datetime]:
    """Parse a goal timestamp/deadline into an aware UTC datetime, or None.

    Tolerates ISO-8601 strings (date-only like ``2026-12-31`` included, with
    or without a trailing ``Z``), datetime objects, and blank/garbage values.
    Naive datetimes are treated as UTC.
    """
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value or not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def is_goal_achieved(goal: KaiGoal) -> bool:
    """Return True when current_value has met the target in the goal's direction."""
    if goal.target_direction == "decrease":
        return goal.current_value <= goal.target_value
    return goal.current_value >= goal.target_value


def compute_goal_pace(goal: KaiGoal, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Compute pace-vs-deadline for a goal.

    Returns a dict with:
      - ``achieved``          — target already met (direction-aware)
      - ``overdue``           — deadline passed without achieving
      - ``time_fraction``     — elapsed/(created→deadline), clamped 0..1, or
                                None when the deadline is missing/unparsable
      - ``progress_fraction`` — (current-baseline)/(target-baseline) clamped
                                0..1, or None when no baseline is derivable
      - ``expected_value``    — linear on-pace value for today, or None
      - ``behind_pace``       — True when progress trails elapsed time by more
                                than PACE_TOLERANCE

    Baseline comes from ``goal.metadata["baseline_value"]`` (the goals CLI and
    CMO review both record it); "increase" goals fall back to a 0.0 baseline.
    When pace cannot be measured (no deadline, or a "decrease" goal with no
    baseline), an unachieved active goal is treated as behind pace so the goal
    loop keeps pursuing it — downstream plans still flow through ActionStore
    approval, so this never mutates a live channel by itself.
    """
    if now is None:
        now = datetime.now(timezone.utc)
    elif now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)

    achieved = is_goal_achieved(goal)
    deadline = parse_goal_datetime(goal.deadline)
    created = parse_goal_datetime(goal.created_at)
    overdue = bool(deadline is not None and now >= deadline and not achieved)

    time_fraction: Optional[float] = None
    if deadline is not None:
        if created is not None and deadline > created:
            span_s = (deadline - created).total_seconds()
            elapsed_s = (now - created).total_seconds()
            time_fraction = min(max(elapsed_s / span_s, 0.0), 1.0)
        elif now >= deadline:
            time_fraction = 1.0

    baseline: Optional[float] = None
    raw_baseline = (goal.metadata or {}).get("baseline_value")
    if raw_baseline is not None:
        try:
            baseline = float(raw_baseline)
        except (TypeError, ValueError):
            baseline = None
    if baseline is None and goal.target_direction == "increase":
        baseline = 0.0

    progress_fraction: Optional[float] = None
    expected_value: Optional[float] = None
    if baseline is not None:
        span = goal.target_value - baseline
        if abs(span) > 1e-12:
            progress_fraction = min(max((goal.current_value - baseline) / span, 0.0), 1.0)
            if time_fraction is not None:
                expected_value = baseline + span * time_fraction

    if achieved:
        behind_pace = False
    elif overdue:
        behind_pace = True
    elif time_fraction is not None and progress_fraction is not None:
        behind_pace = (progress_fraction + PACE_TOLERANCE) < time_fraction
    else:
        # Pace unmeasurable (no deadline / no baseline): an active, unmet goal
        # still needs pursuit — conservative for the goal, safe for channels.
        behind_pace = True

    return {
        "achieved": achieved,
        "overdue": overdue,
        "time_fraction": time_fraction,
        "progress_fraction": progress_fraction,
        "expected_value": expected_value,
        "behind_pace": behind_pace,
    }
