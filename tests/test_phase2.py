import pytest
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from kai.runtime.models import KaiGoal, TaskGraph, TaskNode
from agent.models import AgentDatabase, ScheduledTask, ScheduledTaskConfig, agent_db
import agent.models
import agent.state
import agent.loop
import agent.scheduler
from agent.state import state_manager
from agent.tasks import register_task, BaseTask
from agent.decomposer import GoalDecomposer, has_cycle
from agent.loop import AgentLoop


# =============================================================================
# Custom Dummy Tasks for Testing Execution Flow
# =============================================================================

class DummyTestTask(BaseTask):
    @property
    def task_type(self) -> str:
        return "dummy_test_task"

    async def execute(self, task: ScheduledTask, **kwargs) -> Dict[str, Any]:
        return {"success": True, "summary": "Dummy task completed successfully", "data": {"val": 42}}


class FailingTestTask(BaseTask):
    @property
    def task_type(self) -> str:
        return "failing_test_task"

    async def execute(self, task: ScheduledTask, **kwargs) -> Dict[str, Any]:
        return {"success": False, "error": "Intentionally failed"}


# Register the test tasks
register_task("dummy_test_task", DummyTestTask)
register_task("failing_test_task", FailingTestTask)


# =============================================================================
# Pytest Fixtures
# =============================================================================

@pytest.fixture(autouse=True)
def use_test_db(tmp_path: Path, monkeypatch):
    """Dynamically redirects the database in all modules to a temp SQLite database."""
    test_db_path = tmp_path / "test_agent.db"
    test_db = AgentDatabase(db_path=test_db_path)

    # Monkeypatch singleton in all relevant modules
    monkeypatch.setattr(agent.models, "agent_db", test_db)
    monkeypatch.setattr(agent.state, "agent_db", test_db)
    monkeypatch.setattr(agent.loop, "agent_db", test_db)
    monkeypatch.setattr(agent.scheduler, "agent_db", test_db)
    monkeypatch.setattr(agent.state.state_manager, "db", test_db)

    # Clear any running tasks
    state_manager.clear_running_tasks()

    yield test_db


# =============================================================================
# Tests
# =============================================================================

def test_wal_mode_active(use_test_db):
    """Verify that SQLite connection is configured with WAL journal mode."""
    with use_test_db.connect() as conn:
        res = conn.execute("PRAGMA journal_mode;").fetchone()
        assert res[0].lower() == "wal"


def test_task_graph_crud(use_test_db):
    """Test CRUD operations on TaskGraph and TaskNode schemas."""
    graph_id = "test_graph_123"
    nodes = {
        "node_1": TaskNode(node_id="node_1", task_type="dummy_test_task", status="pending"),
        "node_2": TaskNode(node_id="node_2", task_type="dummy_test_task", status="pending")
    }
    edges = [["node_1", "node_2"]]

    graph = TaskGraph(
        graph_id=graph_id,
        goal_id="goal_abc",
        brand_id="brand_xyz",
        status="pending",
        nodes=nodes,
        edges=edges,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )

    # Create
    use_test_db.create_task_graph(graph)

    # Read
    retrieved = use_test_db.get_task_graph(graph_id)
    assert retrieved is not None
    assert retrieved.graph_id == graph_id
    assert retrieved.goal_id == "goal_abc"
    assert retrieved.brand_id == "brand_xyz"
    assert retrieved.status == "pending"
    assert len(retrieved.nodes) == 2
    assert retrieved.edges == [["node_1", "node_2"]]

    # List active
    active = use_test_db.list_active_task_graphs()
    assert len(active) == 1
    assert active[0].graph_id == graph_id

    # Update graph status
    use_test_db.update_task_graph_status(graph_id, "running")
    assert use_test_db.get_task_graph(graph_id).status == "running"

    # Update node status
    use_test_db.update_task_node(graph_id, "node_1", status="completed", outputs={"done": True})
    nodes_retrieved = use_test_db.get_task_nodes(graph_id)
    assert nodes_retrieved["node_1"].status == "completed"
    assert nodes_retrieved["node_1"].outputs == {"done": True}


def test_cycle_detection():
    """Verify that cycle-detection correctly determines if a graph is a valid DAG."""
    # Linear graph (DAG)
    assert not has_cycle(["A", "B", "C"], [["A", "B"], ["B", "C"]])

    # Branching graph (DAG)
    assert not has_cycle(["A", "B", "C", "D"], [["A", "B"], ["A", "C"], ["B", "D"], ["C", "D"]])

    # Simple Cycle
    assert has_cycle(["A", "B"], [["A", "B"], ["B", "A"]])

    # Self Loop
    assert has_cycle(["A"], [["A", "A"]])

    # Multi-node Cycle
    assert has_cycle(["A", "B", "C"], [["A", "B"], ["B", "C"], ["C", "A"]])


@pytest.mark.asyncio
async def test_goal_decomposer(monkeypatch):
    """Test GoalDecomposer parses LLM outputs and validates them into a TaskGraph."""
    async def mock_complete(prompt, **kwargs):
        # Return mock JSON with markdown wrappers to verify cleaning behavior
        return """
        ```json
        {
          "nodes": [
            {
              "node_id": "step_1",
              "task_type": "dummy_test_task",
              "inputs": {"p1": "v1"}
            },
            {
              "node_id": "step_2",
              "task_type": "dummy_test_task",
              "inputs": {"p2": "v2"}
            }
          ],
          "edges": [
            ["step_1", "step_2"]
          ]
        }
        ```
        """

    from agent.decomposer import llm_router
    monkeypatch.setattr(llm_router, "complete", mock_complete)

    goal = KaiGoal(
        goal_id="goal_test",
        brand_id="brand_test",
        name="Test Goal Decomposition",
        kpi_name="some_kpi",
        target_value=100.0,
        current_value=50.0,
        target_direction="increase"
    )

    decomposer = GoalDecomposer()
    graph = await decomposer.decompose(goal)

    assert graph.goal_id == "goal_test"
    assert graph.brand_id == "brand_test"
    assert graph.status == "pending"
    assert len(graph.nodes) == 2
    assert "step_1" in graph.nodes
    assert "step_2" in graph.nodes
    assert graph.nodes["step_1"].inputs == {"p1": "v1"}
    assert graph.edges == [["step_1", "step_2"]]


@pytest.mark.asyncio
async def test_successful_graph_execution(use_test_db):
    """Verify concurrent loop execution updates statuses correctly for a successful DAG."""
    graph_id = "success_graph"
    nodes = {
        "node_a": TaskNode(node_id="node_a", task_type="dummy_test_task", status="pending"),
        "node_b": TaskNode(node_id="node_b", task_type="dummy_test_task", status="pending")
    }
    edges = [["node_a", "node_b"]]

    graph = TaskGraph(
        graph_id=graph_id,
        goal_id="goal_s",
        brand_id="brand_s",
        status="pending",
        nodes=nodes,
        edges=edges,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    use_test_db.create_task_graph(graph)

    loop_engine = AgentLoop()

    # Step 1: Run tick. Only node_a should start executing since node_b has a dependency on node_a
    await loop_engine._tick()

    # Check database status
    retrieved = use_test_db.get_task_graph(graph_id)
    assert retrieved.status == "running"
    assert retrieved.nodes["node_a"].status == "running"
    assert retrieved.nodes["node_b"].status == "pending"

    # Verify task registered in state_manager
    assert f"graph:{graph_id}:node_a" in state_manager.get_running_tasks()

    # Wait for node_a to complete
    for _ in range(20):
        await asyncio.sleep(0.1)
        nodes_status = use_test_db.get_task_nodes(graph_id)
        if nodes_status["node_a"].status == "completed":
            break
    else:
        pytest.fail("node_a failed to complete execution in time")

    # Step 2: Run tick again. Since node_a is completed, node_b is ready and should start
    await loop_engine._tick()

    retrieved = use_test_db.get_task_graph(graph_id)
    assert retrieved.status == "running"
    assert retrieved.nodes["node_a"].status == "completed"
    assert retrieved.nodes["node_b"].status == "running"

    # Wait for node_b to complete
    for _ in range(20):
        await asyncio.sleep(0.1)
        nodes_status = use_test_db.get_task_nodes(graph_id)
        if nodes_status["node_b"].status == "completed":
            break
    else:
        pytest.fail("node_b failed to complete execution in time")

    # Let the loop finalize graph status (occurs inside the task completion callback/finally block)
    # We sleep briefly to let the task's finally block run and update graph status
    await asyncio.sleep(0.1)

    retrieved = use_test_db.get_task_graph(graph_id)
    assert retrieved.status == "completed"
    assert retrieved.nodes["node_b"].outputs["data"] == {"val": 42}


@pytest.mark.asyncio
async def test_failed_graph_execution_skips_descendants(use_test_db):
    """Verify that if a node fails, all downstream nodes are recursively marked as skipped."""
    graph_id = "failure_graph"
    nodes = {
        "node_parent": TaskNode(node_id="node_parent", task_type="failing_test_task", status="pending"),
        "node_child": TaskNode(node_id="node_child", task_type="dummy_test_task", status="pending"),
        "node_grandchild": TaskNode(node_id="node_grandchild", task_type="dummy_test_task", status="pending")
    }
    edges = [["node_parent", "node_child"], ["node_child", "node_grandchild"]]

    graph = TaskGraph(
        graph_id=graph_id,
        goal_id="goal_f",
        brand_id="brand_f",
        status="pending",
        nodes=nodes,
        edges=edges,
        created_at=datetime.utcnow().isoformat(),
        updated_at=datetime.utcnow().isoformat()
    )
    use_test_db.create_task_graph(graph)

    loop_engine = AgentLoop()

    # Step 1: Run tick. Start execution of node_parent
    await loop_engine._tick()

    # Wait for node_parent to fail
    for _ in range(20):
        await asyncio.sleep(0.1)
        nodes_status = use_test_db.get_task_nodes(graph_id)
        if nodes_status["node_parent"].status == "failed":
            break
    else:
        pytest.fail("node_parent did not fail as expected")

    # Sleep briefly to let the database updates and descendant skipping finish
    await asyncio.sleep(0.1)

    # Verify that the parent is failed, child and grandchild are skipped, and
    # the graph is flagged needs_replan (replan-instead-of-dead-end: the
    # weekly CMO review re-decomposes remaining work instead of abandoning it)
    retrieved = use_test_db.get_task_graph(graph_id)
    assert retrieved.status == "needs_replan"
    assert retrieved.nodes["node_parent"].status == "failed"
    assert retrieved.nodes["node_child"].status == "skipped"
    assert retrieved.nodes["node_grandchild"].status == "skipped"

    # needs_replan graphs must drop out of the active set — execution stops.
    assert all(g.graph_id != graph_id for g in use_test_db.list_active_task_graphs())
