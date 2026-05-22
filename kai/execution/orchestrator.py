"""
Orchestrator - runs individual TaskNodes by mapping them to ScheduledTasks and invoking handlers.
"""

from typing import Any, Dict, Optional
from datetime import datetime

from kai.runtime.models import TaskNode
from agent.models import ScheduledTask, ScheduledTaskConfig
from agent.tasks import get_task_handler

class TaskOrchestrator:
    """Executes a TaskNode by translating it into a ScheduledTask and dispatching to task handlers."""

    async def execute_node(self, graph_id: str, node: TaskNode, brand_id: str) -> Dict[str, Any]:
        """
        Execute a single TaskNode.
        
        Args:
            graph_id: The ID of the parent TaskGraph.
            node: The TaskNode to execute.
            brand_id: The ID of the target brand/client.
            
        Returns:
            A dictionary with execution outcome metadata:
            - success: bool
            - summary: str
            - data: dict
        """
        # Map TaskNode to ScheduledTask
        task_id = f"node:{graph_id}:{node.node_id}"
        name = f"Graph Node {node.node_id} ({node.task_type})"
        
        config = ScheduledTaskConfig(
            extra=node.inputs or {}
        )
        
        scheduled_task = ScheduledTask(
            id=task_id,
            name=name,
            cron_expression="",  # Non-scheduled one-off execution
            task_type=node.task_type,
            client=brand_id,
            config=config,
            enabled=True,
            created_at=datetime.utcnow()
        )
        
        # Dispatch to the task handler
        handler = get_task_handler(node.task_type)
        if handler is None:
            raise ValueError(f"Unknown task type handler: {node.task_type}")
            
        result = await handler.execute(scheduled_task)
        if result is None:
            result = {
                "success": True,
                "summary": "Task completed with no output returned.",
                "data": {}
            }
        return result
