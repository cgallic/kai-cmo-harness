"""
LLM integration for the autonomous agent.

Provides model routing and prompt management.
"""

from .router import LLMRouter, llm_router
from .prompts import TaskPrompts

__all__ = ["LLMRouter", "llm_router", "TaskPrompts"]
