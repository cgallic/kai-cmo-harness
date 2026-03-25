"""
Cron-like task scheduler for the autonomous agent.

Supports standard cron expressions: minute hour day month weekday
Examples:
  - "0 8 * * *"    = 8:00 AM daily
  - "0 8 * * 1-5"  = 8:00 AM weekdays
  - "0 */2 * * *"  = Every 2 hours
  - "30 9 * * 0"   = 9:30 AM Sundays
"""

import re
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from zoneinfo import ZoneInfo

from .config import agent_config
from .models import ScheduledTask, agent_db


class CronParser:
    """Parser for cron expressions."""

    FIELD_NAMES = ["minute", "hour", "day", "month", "weekday"]
    FIELD_RANGES = [
        (0, 59),   # minute
        (0, 23),   # hour
        (1, 31),   # day
        (1, 12),   # month
        (0, 6),    # weekday (0 = Sunday)
    ]

    @classmethod
    def parse(cls, expression: str) -> List[set]:
        """
        Parse a cron expression into field value sets.

        Returns list of 5 sets: [minutes, hours, days, months, weekdays]
        """
        parts = expression.strip().split()
        if len(parts) != 5:
            raise ValueError(f"Invalid cron expression: {expression}")

        return [
            cls._parse_field(parts[i], cls.FIELD_RANGES[i])
            for i in range(5)
        ]

    @classmethod
    def _parse_field(cls, field: str, value_range: Tuple[int, int]) -> set:
        """Parse a single cron field into a set of valid values."""
        min_val, max_val = value_range
        values = set()

        for part in field.split(","):
            # Handle step values (*/2, 1-10/2)
            step = 1
            if "/" in part:
                part, step_str = part.split("/")
                step = int(step_str)

            if part == "*":
                # All values
                values.update(range(min_val, max_val + 1, step))
            elif "-" in part:
                # Range (e.g., 1-5)
                start, end = part.split("-")
                values.update(range(int(start), int(end) + 1, step))
            else:
                # Single value
                values.add(int(part))

        # Validate values
        for v in values:
            if not (min_val <= v <= max_val):
                raise ValueError(f"Value {v} out of range {min_val}-{max_val}")

        return values


class Scheduler:
    """Manages scheduled task execution."""

    def __init__(self, timezone: str = "America/New_York"):
        self.timezone = ZoneInfo(timezone)
        self.db = agent_db

    def get_next_run_time(
        self,
        cron_expression: str,
        after: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate the next run time for a cron expression.

        Args:
            cron_expression: Standard cron expression (5 fields)
            after: Start searching from this time (defaults to now)

        Returns:
            Next datetime when the cron should run (in UTC)
        """
        fields = CronParser.parse(cron_expression)
        minutes, hours, days, months, weekdays = fields

        # Start from the given time or now (in the configured timezone)
        if after is None:
            after = datetime.now(self.timezone)
        elif after.tzinfo is None:
            after = after.replace(tzinfo=self.timezone)

        # Start checking from the next minute
        current = after.replace(second=0, microsecond=0) + timedelta(minutes=1)

        # Search up to 1 year ahead
        max_iterations = 366 * 24 * 60  # 1 year in minutes
        for _ in range(max_iterations):
            if (
                current.minute in minutes and
                current.hour in hours and
                current.day in days and
                current.month in months and
                current.weekday() in self._convert_weekday(weekdays)
            ):
                # Convert to UTC for storage
                return current.astimezone(ZoneInfo("UTC")).replace(tzinfo=None)

            current += timedelta(minutes=1)

        raise ValueError(f"Could not find next run time for: {cron_expression}")

    def _convert_weekday(self, cron_weekdays: set) -> set:
        """
        Convert cron weekdays (0=Sunday) to Python weekdays (0=Monday).
        """
        # Cron: 0=Sun, 1=Mon, ..., 6=Sat
        # Python: 0=Mon, 1=Tue, ..., 6=Sun
        python_weekdays = set()
        for cron_day in cron_weekdays:
            if cron_day == 0:
                python_weekdays.add(6)  # Sunday
            else:
                python_weekdays.add(cron_day - 1)
        return python_weekdays

    def get_due_tasks(self) -> List[ScheduledTask]:
        """
        Get all tasks that are due to run now.

        Returns tasks where next_run_at <= now and enabled = True.
        """
        now = datetime.utcnow()
        tasks = self.db.list_scheduled_tasks(enabled_only=True)

        due_tasks = []
        for task in tasks:
            if task.next_run_at is None:
                # Task has never run - calculate initial next_run_at
                next_run = self.get_next_run_time(task.cron_expression)
                self.db.update_scheduled_task(task.id, next_run_at=next_run)
                task.next_run_at = next_run

            if task.next_run_at <= now:
                due_tasks.append(task)

        return due_tasks

    def mark_task_started(self, task: ScheduledTask):
        """
        Mark a task as having started execution.

        Updates last_run_at to now and calculates new next_run_at.
        """
        now = datetime.utcnow()
        next_run = self.get_next_run_time(task.cron_expression, after=now)

        self.db.update_scheduled_task(
            task.id,
            last_run_at=now,
            next_run_at=next_run
        )

    def create_default_tasks(self):
        """
        Create the default scheduled tasks if they don't exist.

        Default schedule:
        - daily_analytics: 8:00 AM
        - content_generation: 10:00 AM
        - lead_scrape: 6:00 AM
        - warmup_check: 7:00 AM
        - ad_performance: 12:00 PM
        - seo_opportunities: 2:00 PM
        - weekly_report: Sunday 9:00 AM
        """
        from uuid import uuid4

        default_tasks = [
            {
                "name": "Daily Analytics Briefing",
                "cron_expression": "0 8 * * *",  # 8 AM daily
                "task_type": "daily_analytics",
                "config": {"model": "haiku", "notify_on_complete": True}
            },
            {
                "name": "Content Generation",
                "cron_expression": "0 10 * * *",  # 10 AM daily
                "task_type": "content_pipeline",
                "config": {"model": "haiku"}
            },
            {
                "name": "Lead Scraping",
                "cron_expression": "0 6 * * *",  # 6 AM daily
                "task_type": "lead_outreach",
                "config": {"model": "haiku"}
            },
            {
                "name": "Email Warmup Check",
                "cron_expression": "0 7 * * *",  # 7 AM daily
                "task_type": "warmup_check",
                "config": {"model": "haiku"}
            },
            {
                "name": "Ad Performance Check",
                "cron_expression": "0 12 * * *",  # 12 PM daily
                "task_type": "ad_management",
                "config": {"model": "haiku"}
            },
            {
                "name": "SEO Opportunities",
                "cron_expression": "0 14 * * *",  # 2 PM daily
                "task_type": "seo_optimization",
                "config": {"model": "haiku"}
            },
            {
                "name": "Weekly Strategy Report",
                "cron_expression": "0 9 * * 0",  # 9 AM Sundays
                "task_type": "weekly_report",
                "config": {"model": "opus", "notify_on_complete": True}
            },
            # Kai Calls tasks
            {
                "name": "KaiCalls Call Processor",
                "cron_expression": "*/5 * * * *",  # Every 5 minutes
                "task_type": "kai_call_processor",
                "client": "kai-calls",
                "config": {"notify_on_complete": False}
            },
            {
                "name": "KaiCalls Follow-Up Monitor",
                "cron_expression": "*/10 * * * *",  # Every 10 minutes
                "task_type": "kai_followup",
                "client": "kai-calls",
                "config": {"notify_on_complete": False}
            },
            {
                "name": "KaiCalls Daily Report",
                "cron_expression": "0 8 * * *",  # 8 AM daily
                "task_type": "kai_business_ops",
                "client": "kai-calls",
                "config": {"notify_on_complete": True}
            },
            {
                "name": "KaiCalls Weekly Report",
                "cron_expression": "0 9 * * 0",  # 9 AM Sundays
                "task_type": "kai_business_ops",
                "client": "kai-calls",
                "config": {"notify_on_complete": True, "extra": {"weekly": True}}
            },
            {
                "name": "KaiCalls Onboarding Tracker",
                "cron_expression": "0 */6 * * *",  # Every 6 hours
                "task_type": "kai_onboarding",
                "client": "kai-calls",
                "config": {}
            },
            {
                "name": "KaiCalls Task Board Reminder",
                "cron_expression": "0 9 * * *",  # 9 AM daily
                "task_type": "kai_task_board",
                "client": "kai-calls",
                "config": {"notify_on_complete": False}
            },
            # BuildWithKai tasks
            {
                "name": "BWK Generation Monitor",
                "cron_expression": "*/10 * * * *",  # Every 10 minutes
                "task_type": "bwk_generation_monitor",
                "client": "buildwithkai",
                "config": {"notify_on_complete": False}
            },
            {
                "name": "BWK User Activation",
                "cron_expression": "0 */6 * * *",  # Every 6 hours
                "task_type": "bwk_user_activation",
                "client": "buildwithkai",
                "config": {}
            },
            {
                "name": "BWK Revenue Monitor",
                "cron_expression": "0 7 * * *",  # 7 AM daily
                "task_type": "bwk_revenue_monitor",
                "client": "buildwithkai",
                "config": {"notify_on_complete": True}
            },
            {
                "name": "BWK Daily Report",
                "cron_expression": "0 8 * * *",  # 8 AM daily
                "task_type": "bwk_business_ops",
                "client": "buildwithkai",
                "config": {"notify_on_complete": True}
            },
            {
                "name": "BWK Weekly Report",
                "cron_expression": "0 9 * * 0",  # 9 AM Sundays
                "task_type": "bwk_business_ops",
                "client": "buildwithkai",
                "config": {"notify_on_complete": True, "extra": {"weekly": True}}
            },
            {
                "name": "BWK Quality Auditor",
                "cron_expression": "0 */12 * * *",  # Every 12 hours
                "task_type": "bwk_quality_auditor",
                "client": "buildwithkai",
                "config": {}
            },
            # Amazing Backyard Parties tasks
            {
                "name": "ABP Lead Processor",
                "cron_expression": "*/15 * * * *",  # Every 15 minutes
                "task_type": "abp_lead_processor",
                "client": "abp",
                "config": {"notify_on_complete": False}
            },
            {
                "name": "ABP Vendor Health",
                "cron_expression": "0 */6 * * *",  # Every 6 hours
                "task_type": "abp_vendor_health",
                "client": "abp",
                "config": {}
            },
            {
                "name": "ABP Daily Report",
                "cron_expression": "0 8 * * *",  # 8 AM daily
                "task_type": "abp_business_ops",
                "client": "abp",
                "config": {"notify_on_complete": True}
            },
            {
                "name": "ABP SEO Monitor",
                "cron_expression": "0 6 * * *",  # 6 AM daily
                "task_type": "abp_seo_monitor",
                "client": "abp",
                "config": {"notify_on_complete": True}
            },
            # Social data staleness monitoring
            {
                "name": "Social Data Staleness Check",
                "cron_expression": "0 9 * * 1",  # 9 AM Mondays
                "task_type": "social_staleness_check",
                "config": {"notify_on_complete": True}
            },
            {
                "name": "Social Data Critical Alert",
                "cron_expression": "0 8 * * *",  # 8 AM daily
                "task_type": "social_staleness_check",
                "config": {"notify_on_complete": False, "extra": {"critical_only": True}}
            },
        ]

        existing_tasks = {t.name for t in self.db.list_scheduled_tasks(enabled_only=False)}

        for task_def in default_tasks:
            if task_def["name"] not in existing_tasks:
                from .models import ScheduledTask, ScheduledTaskConfig

                task = ScheduledTask(
                    id=str(uuid4())[:8],
                    name=task_def["name"],
                    cron_expression=task_def["cron_expression"],
                    task_type=task_def["task_type"],
                    client=task_def.get("client"),
                    config=ScheduledTaskConfig(**task_def["config"])
                )
                task.next_run_at = self.get_next_run_time(task.cron_expression)
                self.db.create_scheduled_task(task)
                print(f"Created default task: {task.name}")

    def list_upcoming_tasks(self, limit: int = 10) -> List[Tuple[ScheduledTask, str]]:
        """
        List upcoming scheduled tasks with human-readable next run times.

        Returns list of (task, time_until_run) tuples.
        """
        tasks = self.db.list_scheduled_tasks(enabled_only=True)
        now = datetime.utcnow()

        results = []
        for task in tasks[:limit]:
            if task.next_run_at:
                delta = task.next_run_at - now
                if delta.total_seconds() < 0:
                    time_str = "overdue"
                elif delta.total_seconds() < 3600:
                    time_str = f"in {int(delta.total_seconds() / 60)} minutes"
                elif delta.total_seconds() < 86400:
                    time_str = f"in {int(delta.total_seconds() / 3600)} hours"
                else:
                    time_str = f"in {int(delta.total_seconds() / 86400)} days"
                results.append((task, time_str))

        return results


# Global scheduler instance
scheduler = Scheduler()
