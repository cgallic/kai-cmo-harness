"""
Tasks adapter.

Wraps task extraction and management scripts.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure scripts path is available
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class TasksAdapter:
    """Adapter for task-related operations."""

    def run_extract(
        self,
        text: str,
        client: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract tasks from text."""
        try:
            # Try to use the task extractor if available
            from scripts.task_extractor import TaskExtractor

            extractor = TaskExtractor()
            tasks = extractor.extract(text)

            return {
                "input_length": len(text),
                "tasks_extracted": len(tasks),
                "tasks": tasks,
            }
        except ImportError:
            # Fallback: simple extraction based on common patterns
            tasks = self._simple_extract(text)
            return {
                "input_length": len(text),
                "tasks_extracted": len(tasks),
                "tasks": tasks,
                "note": "Using fallback extraction (task_extractor not available)",
            }

    def _simple_extract(self, text: str) -> List[Dict[str, Any]]:
        """Simple task extraction fallback."""
        tasks = []
        lines = text.split("\n")

        task_indicators = [
            "- [ ]", "- []", "[ ]", "[]",  # Markdown checkboxes
            "TODO:", "FIXME:", "TODO", "FIXME",  # Code comments
            "• ", "* ", "- ",  # Bullet points
        ]

        for i, line in enumerate(lines):
            line = line.strip()
            if not line:
                continue

            for indicator in task_indicators:
                if line.startswith(indicator):
                    task_text = line[len(indicator):].strip()
                    if task_text:
                        tasks.append({
                            "id": i,
                            "text": task_text,
                            "source": "line",
                            "indicator": indicator.strip(),
                        })
                    break

        return tasks

    def deduplicate(self, tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Deduplicate a list of tasks."""
        try:
            from scripts.task_deduplicator import TaskDeduplicator

            deduplicator = TaskDeduplicator()
            unique_tasks = deduplicator.deduplicate(tasks)

            return {
                "input_count": len(tasks),
                "output_count": len(unique_tasks),
                "removed": len(tasks) - len(unique_tasks),
                "tasks": unique_tasks,
            }
        except ImportError:
            # Fallback: simple text-based deduplication
            seen = set()
            unique = []

            for task in tasks:
                # Normalize task text for comparison
                text = task.get("text", str(task)).lower().strip()
                if text not in seen:
                    seen.add(text)
                    unique.append(task)

            return {
                "input_count": len(tasks),
                "output_count": len(unique),
                "removed": len(tasks) - len(unique),
                "tasks": unique,
                "note": "Using fallback deduplication (task_deduplicator not available)",
            }
