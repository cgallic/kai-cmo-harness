"""
Kai Calls autonomous agent tasks.

Manages the Kai Calls business — processes inbound calls, enriches leads,
handles follow-up emails, reports on ops, tracks onboarding and tasks.
"""

from .call_processor import CallProcessorTask
from .followup_manager import FollowUpManagerTask
from .business_ops import BusinessOpsTask
from .onboarding_tracker import OnboardingTrackerTask
from .task_board import TaskBoardTask

__all__ = [
    "CallProcessorTask",
    "FollowUpManagerTask",
    "BusinessOpsTask",
    "OnboardingTrackerTask",
    "TaskBoardTask",
]
