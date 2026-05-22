import pytest
import json
from pathlib import Path
from datetime import datetime, timezone

from kai.runtime.models import KaiGoal
from kai.analytics.attribution import ActionOutcomeLinkage, ObservedChange
from kai.analytics.rewards import (
    compute_reward_score,
    log_action_rewards,
    load_rewards_log,
    get_average_rewards_by_action_type,
)
from agent.decomposer import GoalDecomposer
from agent.decomposer import llm_router


def test_compute_reward_score():
    # Improved direction
    change_imp = ObservedChange(
        metric_name="conversion_rate",
        before_value=1.0,
        after_value=1.1,
        absolute_change=0.1,
        percent_change=10.0,
        direction="improved",
        is_significant=True,
    )
    score = compute_reward_score(change_imp, 0.8)
    assert score == 8.0  # +10.0 * 0.8

    # Declined direction
    change_dec = ObservedChange(
        metric_name="cpa",
        before_value=10.0,
        after_value=12.0,
        absolute_change=2.0,
        percent_change=20.0,
        direction="declined",
        is_significant=True,
    )
    score = compute_reward_score(change_dec, 0.5)
    assert score == -10.0  # -20.0 * 0.5

    # Unchanged direction
    change_unc = ObservedChange(
        metric_name="ctr",
        before_value=0.05,
        after_value=0.051,
        absolute_change=0.001,
        percent_change=2.0,
        direction="unchanged",
        is_significant=False,
    )
    score = compute_reward_score(change_unc, 0.9)
    assert score == 0.0


def test_log_action_rewards_and_averages(tmp_path):
    log_file = tmp_path / "rewards_log.json"

    # Create dummy outcome linkages
    linkage1 = ActionOutcomeLinkage(
        action_id="act_1",
        action_type="seo_optimization",
        confidence_score=0.8,
        observed_changes=[
            ObservedChange(
                metric_name="visibility",
                percent_change=10.0,
                direction="improved",
            ),
            ObservedChange(
                metric_name="bounce_rate",
                percent_change=5.0,
                direction="declined",
            ),
        ],
        created_at="2026-05-22T02:00:00Z",
    )

    linkage2 = ActionOutcomeLinkage(
        action_id="act_2",
        action_type="seo_optimization",
        confidence_score=0.9,
        observed_changes=[
            ObservedChange(
                metric_name="visibility",
                percent_change=20.0,
                direction="improved",
            )
        ],
        created_at="2026-05-22T02:01:00Z",
    )

    linkage3 = ActionOutcomeLinkage(
        action_id="act_3",
        action_type="ad_management",
        confidence_score=0.6,
        observed_changes=[
            ObservedChange(
                metric_name="visibility",
                percent_change=15.0,
                direction="declined",
            )
        ],
        created_at="2026-05-22T02:02:00Z",
    )

    # Log them
    log_action_rewards(linkage1, log_file)
    log_action_rewards(linkage2, log_file)
    log_action_rewards(linkage3, log_file)

    # Load and verify
    raw_logs = load_rewards_log(log_file)
    assert len(raw_logs) == 4  # 2 from linkage1 + 1 from linkage2 + 1 from linkage3

    # Verify scores
    # visibility: act_1: 10 * 0.8 = 8.0, act_2: 20 * 0.9 = 18.0. Avg = 13.0
    # bounce_rate: act_1: -5 * 0.8 = -4.0. Avg = -4.0
    # visibility (ad_management): act_3: -15 * 0.6 = -9.0. Avg = -9.0
    averages = get_average_rewards_by_action_type(log_file)

    assert averages["seo_optimization"]["visibility"] == 13.0
    assert averages["seo_optimization"]["bounce_rate"] == -4.0
    assert averages["ad_management"]["visibility"] == -9.0


@pytest.mark.asyncio
async def test_decomposer_ingests_rewards_context(tmp_path, monkeypatch):
    log_file = tmp_path / "rewards_log.json"

    # Seed rewards log with performance history
    linkage = ActionOutcomeLinkage(
        action_id="act_1",
        action_type="seo_optimization",
        confidence_score=0.8,
        observed_changes=[
            ObservedChange(
                metric_name="visibility",
                percent_change=15.0,
                direction="improved",
            )
        ],
    )
    log_action_rewards(linkage, log_file)

    # Setup mock LLM router complete
    captured_prompts = []

    async def mock_complete(prompt, **kwargs):
        captured_prompts.append(prompt)
        return """
        {
          "nodes": [
            {
              "node_id": "seo_step",
              "task_type": "seo_optimization",
              "inputs": {}
            }
          ],
          "edges": []
        }
        """

    monkeypatch.setattr(llm_router, "complete", mock_complete)

    goal = KaiGoal(
        goal_id="goal_rl",
        brand_id="brand_rl",
        name="RL Goal Decompose Test",
        kpi_name="visibility",
        target_value=100.0,
        current_value=50.0,
        target_direction="increase",
    )

    decomposer = GoalDecomposer()
    await decomposer.decompose(goal, rewards_filepath=str(log_file))

    # Assertions
    assert len(captured_prompts) == 1
    prompt_text = captured_prompts[0]

    # Verify that the formatted rewards context was injected
    assert "Historical Performance Context" in prompt_text
    assert "Action Type 'seo_optimization'" in prompt_text
    assert "KPI 'visibility': average reward = +12.0000" in prompt_text
    assert "Prioritize action types with positive average rewards" in prompt_text
