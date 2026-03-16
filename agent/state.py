"""
State management for the autonomous agent.

Provides persistent state storage with type-safe access patterns.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from .models import AgentState, ConversationContext, agent_db


class StateManager:
    """
    Manages persistent agent state.

    State keys:
    - "agent_state": Global agent state (paused, stats, etc.)
    - "conversation:{phone}": Conversation context per phone number
    - "task_context:{task_id}": Task-specific context
    - "client_state:{client_id}": Per-client state
    """

    # Well-known state keys
    AGENT_STATE_KEY = "agent_state"
    CONVERSATION_PREFIX = "conversation:"
    TASK_CONTEXT_PREFIX = "task_context:"
    CLIENT_STATE_PREFIX = "client_state:"

    def __init__(self):
        self.db = agent_db

    # -------------------------------------------------------------------------
    # Global Agent State
    # -------------------------------------------------------------------------
    def get_agent_state(self) -> AgentState:
        """Get the global agent state."""
        data = self.db.get_state(self.AGENT_STATE_KEY)
        if data is None:
            return AgentState()
        return AgentState(**data)

    def set_agent_state(self, state: AgentState):
        """Set the global agent state."""
        self.db.set_state(self.AGENT_STATE_KEY, state.model_dump())

    def update_agent_state(self, **kwargs):
        """Update specific fields of the agent state."""
        state = self.get_agent_state()
        for key, value in kwargs.items():
            if hasattr(state, key):
                setattr(state, key, value)
        self.set_agent_state(state)

    def is_paused(self) -> bool:
        """Check if the agent is paused."""
        return self.get_agent_state().paused

    def pause(self):
        """Pause the agent."""
        self.update_agent_state(paused=True)

    def resume(self):
        """Resume the agent."""
        self.update_agent_state(paused=False)

    def record_activity(self):
        """Record that the agent performed an activity."""
        self.update_agent_state(last_activity=datetime.utcnow())

    def increment_stat(self, stat_name: str, amount: int = 1):
        """Increment a statistics counter."""
        state = self.get_agent_state()
        state.stats[stat_name] = state.stats.get(stat_name, 0) + amount
        self.set_agent_state(state)

    def get_stats(self) -> Dict[str, int]:
        """Get all statistics."""
        return self.get_agent_state().stats

    # -------------------------------------------------------------------------
    # Conversation Context
    # -------------------------------------------------------------------------
    def get_conversation_context(self, phone_number: str) -> ConversationContext:
        """Get conversation context for a phone number."""
        key = f"{self.CONVERSATION_PREFIX}{phone_number}"
        data = self.db.get_state(key)
        if data is None:
            return ConversationContext()
        return ConversationContext(**data)

    def set_conversation_context(self, phone_number: str, context: ConversationContext):
        """Set conversation context for a phone number."""
        key = f"{self.CONVERSATION_PREFIX}{phone_number}"
        self.db.set_state(key, context.model_dump())

    def update_conversation_context(self, phone_number: str, **kwargs):
        """Update specific fields of a conversation context."""
        context = self.get_conversation_context(phone_number)
        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)
        self.set_conversation_context(phone_number, context)

    def clear_conversation_context(self, phone_number: str):
        """Clear conversation context for a phone number."""
        key = f"{self.CONVERSATION_PREFIX}{phone_number}"
        self.db.delete_state(key)

    # -------------------------------------------------------------------------
    # Task Context
    # -------------------------------------------------------------------------
    def get_task_context(self, task_id: str) -> Dict[str, Any]:
        """Get context for a specific task."""
        key = f"{self.TASK_CONTEXT_PREFIX}{task_id}"
        return self.db.get_state(key) or {}

    def set_task_context(self, task_id: str, context: Dict[str, Any]):
        """Set context for a specific task."""
        key = f"{self.TASK_CONTEXT_PREFIX}{task_id}"
        self.db.set_state(key, context)

    def update_task_context(self, task_id: str, **kwargs):
        """Update task context fields."""
        context = self.get_task_context(task_id)
        context.update(kwargs)
        self.set_task_context(task_id, context)

    def clear_task_context(self, task_id: str):
        """Clear task context."""
        key = f"{self.TASK_CONTEXT_PREFIX}{task_id}"
        self.db.delete_state(key)

    # -------------------------------------------------------------------------
    # Client State
    # -------------------------------------------------------------------------
    def get_client_state(self, client_id: str) -> Dict[str, Any]:
        """Get state for a specific client."""
        key = f"{self.CLIENT_STATE_PREFIX}{client_id}"
        return self.db.get_state(key) or {}

    def set_client_state(self, client_id: str, state: Dict[str, Any]):
        """Set state for a specific client."""
        key = f"{self.CLIENT_STATE_PREFIX}{client_id}"
        self.db.set_state(key, state)

    def update_client_state(self, client_id: str, **kwargs):
        """Update client state fields."""
        state = self.get_client_state(client_id)
        state.update(kwargs)
        self.set_client_state(client_id, state)

    # -------------------------------------------------------------------------
    # Running Tasks Tracking
    # -------------------------------------------------------------------------
    def add_running_task(self, task_id: str):
        """Add a task to the running tasks list."""
        state = self.get_agent_state()
        if task_id not in state.current_tasks:
            state.current_tasks.append(task_id)
            self.set_agent_state(state)

    def remove_running_task(self, task_id: str):
        """Remove a task from the running tasks list."""
        state = self.get_agent_state()
        if task_id in state.current_tasks:
            state.current_tasks.remove(task_id)
            self.set_agent_state(state)

    def get_running_tasks(self) -> List[str]:
        """Get list of currently running task IDs."""
        return self.get_agent_state().current_tasks

    def clear_running_tasks(self):
        """Clear all running tasks (use on startup to clear stale state)."""
        state = self.get_agent_state()
        state.current_tasks = []
        self.set_agent_state(state)

    # -------------------------------------------------------------------------
    # Generic Key-Value Access
    # -------------------------------------------------------------------------
    def get(self, key: str, default: Any = None) -> Any:
        """Get any state value by key."""
        return self.db.get_state(key, default)

    def set(self, key: str, value: Any):
        """Set any state value."""
        self.db.set_state(key, value)

    def delete(self, key: str):
        """Delete a state key."""
        self.db.delete_state(key)


# Global state manager instance
state_manager = StateManager()
