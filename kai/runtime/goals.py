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
