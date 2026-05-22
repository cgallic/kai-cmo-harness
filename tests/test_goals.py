import pytest
from pathlib import Path
from kai.runtime import (
    KaiGoal,
    GoalRegistry,
    get_default_goal_registry,
)
from agent.tasks.weekly_report import WeeklyReportTask


def test_goal_creation_and_persistence(tmp_path: Path):
    registry = GoalRegistry(base_dir=tmp_path)
    goal = registry.create_goal(
        brand_id="test_brand",
        name="Increase Leads",
        kpi_name="total_leads",
        target_value=100.0,
        current_value=45.0,
        target_direction="increase",
        deadline="2026-06-01",
    )
    
    assert goal.goal_id.startswith("goal_")
    assert goal.brand_id == "test_brand"
    assert goal.name == "Increase Leads"
    assert goal.kpi_name == "total_leads"
    assert goal.target_value == 100.0
    assert goal.current_value == 45.0
    assert goal.target_direction == "increase"
    assert goal.status == "active"
    assert goal.deadline == "2026-06-01"
    
    # Retrieve from registry
    retrieved = registry.get_goal(goal.goal_id)
    assert retrieved is not None
    assert retrieved.goal_id == goal.goal_id
    assert retrieved.name == "Increase Leads"
    assert retrieved.target_value == 100.0


def test_list_and_delete_goals(tmp_path: Path):
    registry = GoalRegistry(base_dir=tmp_path)
    goal1 = registry.create_goal("brand_a", "Goal 1", "kpi_a", 10.0, 5.0, "increase")
    goal2 = registry.create_goal("brand_a", "Goal 2", "kpi_b", 20.0, 15.0, "increase")
    goal3 = registry.create_goal("brand_b", "Goal 3", "kpi_c", 30.0, 25.0, "increase")
    
    # List all
    all_goals = registry.list_goals()
    assert len(all_goals) == 3
    
    # List by brand
    brand_a_goals = registry.list_goals(brand_id="brand_a")
    assert len(brand_a_goals) == 2
    assert {g.goal_id for g in brand_a_goals} == {goal1.goal_id, goal2.goal_id}
    
    # Delete
    deleted = registry.delete_goal(goal1.goal_id)
    assert deleted is True
    assert registry.get_goal(goal1.goal_id) is None
    assert len(registry.list_goals()) == 2


def test_global_singleton():
    reg1 = get_default_goal_registry()
    reg2 = get_default_goal_registry()
    assert reg1 is reg2


@pytest.mark.asyncio
async def test_weekly_report_integration(tmp_path: Path, monkeypatch):
    registry = GoalRegistry(base_dir=tmp_path)
    # Monkeypatch get_default_goal_registry to return our temporary test registry
    monkeypatch.setattr("kai.runtime.get_default_goal_registry", lambda: registry)
    
    goal = registry.create_goal(
        brand_id="my_client",
        name="Signups",
        kpi_name="signup_count",
        target_value=500.0,
        current_value=320.0,
        target_direction="increase",
    )
    
    task = WeeklyReportTask()
    client = {"id": "my_client", "name": "My Client"}
    
    goals_str = await task._collect_goals_data(client)
    assert "Signups" in goals_str
    assert "signup_count" in goals_str
    assert "320.0 / 500.0" in goals_str
