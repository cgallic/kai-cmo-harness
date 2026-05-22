"""Reward efficacy scoring loop for Kai Marketing OS.

This module maps action outcomes to numeric reward values and logs
them to a localized storage (rewards_log.json) to close the learning loop.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from kai.analytics.attribution import ActionOutcomeLinkage, ObservedChange
from kai.runtime.models import SerializableModel


@dataclass
class ActionReward(SerializableModel):
    """Represents a computed reward for a single KPI of an action.

    Attributes:
        action_id: The ID of the action.
        action_type: The type of the action.
        metric_name: The name of the KPI metric.
        percent_change: The percentage change of the metric.
        direction: The direction of change ('improved', 'declined', 'unchanged').
        confidence_score: The attribution confidence score (0.0 to 1.0).
        reward_score: The computed reward score.
        timestamp: ISO format timestamp when this reward was computed.
    """

    action_id: str
    action_type: str
    metric_name: str
    percent_change: float
    direction: str
    confidence_score: float
    reward_score: float
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


def compute_reward_score(observed_change: ObservedChange, confidence_score: float) -> float:
    """Compute reward score using: Reward = ObservedChange_percent * AttributionConfidence.

    Sign is positive for 'improved', negative for 'declined', and zero for 'unchanged'.
    """
    if observed_change.direction == "improved":
        sign = 1.0
    elif observed_change.direction == "declined":
        sign = -1.0
    else:
        sign = 0.0
    return round(sign * abs(observed_change.percent_change) * confidence_score, 4)


def get_rewards_log_path() -> Path:
    """Return the configured path to rewards_log.json."""
    try:
        from scripts.harness_config import get_config
        return get_config().data_dir / "rewards_log.json"
    except ImportError:
        # Fallback to repo root data directory
        return Path("data/rewards_log.json")


def log_action_rewards(linkage: ActionOutcomeLinkage, filepath: Optional[str | Path] = None) -> List[ActionReward]:
    """Calculate and log rewards for each observed change in the ActionOutcomeLinkage."""
    if filepath is None:
        path = get_rewards_log_path()
    else:
        path = Path(filepath)

    # Ensure parent directories exist
    path.parent.mkdir(parents=True, exist_ok=True)

    rewards: List[ActionReward] = []
    timestamp = linkage.created_at or datetime.now(timezone.utc).isoformat()

    for change in linkage.observed_changes:
        reward_val = compute_reward_score(change, linkage.confidence_score)
        reward_record = ActionReward(
            action_id=linkage.action_id,
            action_type=linkage.action_type,
            metric_name=change.metric_name,
            percent_change=change.percent_change,
            direction=change.direction,
            confidence_score=linkage.confidence_score,
            reward_score=reward_val,
            timestamp=timestamp,
        )
        rewards.append(reward_record)

    if not rewards:
        return []

    # Read existing rewards log
    existing_data: List[Dict[str, Any]] = []
    if path.exists() and path.stat().st_size > 0:
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing_data = json.load(f)
        except Exception:
            existing_data = []

    # Append new records
    for r in rewards:
        existing_data.append(r.model_dump())

    # Write back
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing_data, f, indent=2, ensure_ascii=False)

    return rewards


def load_rewards_log(filepath: Optional[str | Path] = None) -> List[Dict[str, Any]]:
    """Load the full rewards log file as list of raw dicts."""
    if filepath is None:
        path = get_rewards_log_path()
    else:
        path = Path(filepath)

    if not path.exists() or path.stat().st_size == 0:
        return []

    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def get_average_rewards_by_action_type(filepath: Optional[str | Path] = None) -> Dict[str, Dict[str, float]]:
    """Compute average reward scores grouped by action_type and metric_name.

    Returns a structure:
    {
        "seo_optimization": {
            "visibility": 12.5,
            "bounce_rate": -3.2
        },
        ...
    }
    """
    records = load_rewards_log(filepath)
    totals: Dict[str, Dict[str, List[float]]] = {}

    for r in records:
        a_type = r.get("action_type")
        metric = r.get("metric_name")
        score = r.get("reward_score")
        if not a_type or not metric or score is None:
            continue
        if a_type not in totals:
            totals[a_type] = {}
        if metric not in totals[a_type]:
            totals[a_type][metric] = []
        totals[a_type][metric].append(float(score))

    averages: Dict[str, Dict[str, float]] = {}
    for a_type, metrics in totals.items():
        averages[a_type] = {}
        for metric, scores in metrics.items():
            if scores:
                averages[a_type][metric] = round(sum(scores) / len(scores), 4)

    return averages
