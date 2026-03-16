"""
BuildWithKai autonomous agent tasks.

Monitors the BuildWithKai SaaS platform — tracks product generations,
user activation funnels, revenue, and content quality.
"""

from .generation_monitor import GenerationMonitorTask
from .user_activation import UserActivationTask
from .revenue_monitor import RevenueMonitorTask
from .business_ops import BWKBusinessOpsTask
from .quality_auditor import QualityAuditorTask

__all__ = [
    "GenerationMonitorTask",
    "UserActivationTask",
    "RevenueMonitorTask",
    "BWKBusinessOpsTask",
    "QualityAuditorTask",
]
