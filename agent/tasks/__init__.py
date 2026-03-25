"""
Task handlers for the autonomous agent.

Each task type has a handler class that implements the execute() method.

Generic task handlers are included by default. Product-specific handlers
can be registered dynamically via register_task() or by adding them to
config.yaml.

See examples_kai_calls/, examples_buildwithkai/, examples_abp/ for
product-specific handler examples.
"""

from typing import Optional

from .base import BaseTask
from .daily_analytics import DailyAnalyticsTask
from .content_pipeline import ContentPipelineTask
from .lead_outreach import LeadOutreachTask
from .ad_management import AdManagementTask
from .seo_optimization import SEOOptimizationTask
from .weekly_report import WeeklyReportTask
from .creative_assets import CreativeAssetsTask
from .social_staleness import SocialStalenessTask

# Task type to handler mapping (generic handlers only)
TASK_HANDLERS: dict[str, type[BaseTask]] = {
    "daily_analytics": DailyAnalyticsTask,
    "content_pipeline": ContentPipelineTask,
    "lead_outreach": LeadOutreachTask,
    "ad_management": AdManagementTask,
    "seo_optimization": SEOOptimizationTask,
    "weekly_report": WeeklyReportTask,
    "warmup_check": LeadOutreachTask,
    "creative_assets": CreativeAssetsTask,
    "og_image": CreativeAssetsTask,
    "social_staleness_check": SocialStalenessTask,
}


def register_task(task_type: str, handler_class: type[BaseTask]) -> None:
    """
    Register a custom task handler.

    Use this to add product-specific task handlers at runtime:

        from agent.tasks import register_task
        from my_product.tasks import MyProductOpsTask
        register_task("myproduct_ops", MyProductOpsTask)
    """
    TASK_HANDLERS[task_type] = handler_class


def get_task_handler(task_type: str) -> Optional[BaseTask]:
    """
    Get a task handler instance for the given task type.

    Args:
        task_type: The type of task

    Returns:
        Task handler instance or None if unknown type
    """
    handler_class = TASK_HANDLERS.get(task_type)
    if handler_class:
        return handler_class()
    return None


__all__ = [
    "BaseTask",
    "DailyAnalyticsTask",
    "ContentPipelineTask",
    "LeadOutreachTask",
    "AdManagementTask",
    "SEOOptimizationTask",
    "WeeklyReportTask",
    "CreativeAssetsTask",
    "SocialStalenessTask",
    "register_task",
    "get_task_handler",
]
