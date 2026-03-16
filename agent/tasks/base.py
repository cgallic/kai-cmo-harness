"""
Base task class for agent tasks.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from ..models import ScheduledTask


class BaseTask(ABC):
    """
    Abstract base class for scheduled tasks.

    Each task handler must implement:
    - execute(): Run the task and return results
    """

    @property
    @abstractmethod
    def task_type(self) -> str:
        """Return the task type identifier."""
        pass

    @property
    def description(self) -> str:
        """Return a human-readable description of the task."""
        return f"{self.task_type} task"

    @abstractmethod
    async def execute(
        self,
        task: ScheduledTask,
        **kwargs
    ) -> Optional[Dict[str, Any]]:
        """
        Execute the task.

        Args:
            task: The scheduled task definition
            **kwargs: Additional execution parameters

        Returns:
            Dict with task results including:
            - success: bool
            - summary: str (for notifications)
            - data: Any additional data
        """
        pass

    def get_client_config(self, task: ScheduledTask) -> Dict[str, Any]:
        """Get client configuration if task has a client."""
        if not task.client:
            return {}

        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent))

        from gateway.config import config
        client = config.get_client(task.client)
        return client or {}

    async def send_notification(
        self,
        message: str,
        task: Optional[ScheduledTask] = None
    ):
        """Send a notification about task progress or results."""
        from ..channels.whatsapp import whatsapp_channel
        from ..config import agent_config

        if agent_config.agent_owner_phone:
            await whatsapp_channel.send_message(
                agent_config.agent_owner_phone,
                message
            )
