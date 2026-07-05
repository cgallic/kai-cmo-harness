"""Editorial calendar executor — turns due calendar items into content drafts.

Hourly task that pulls due ``planned`` items from the structured editorial
calendar (``scripts/campaigns/calendar.py`` → ``data/calendar/editorial.jsonl``)
and runs each through the SAME generation path ContentPipelineTask uses
(``_generate_draft`` + ``_save_drafts``), advancing status
planned -> generating -> ready.

Approval doctrine: this task produces DRAFTS only. Drafts land in the client
outputs directory and flow through the normal quality-gate + human-approval
pipeline. This task NEVER publishes or mutates a live channel, and it never
sets an item's status to ``published``.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..models import ScheduledTask
from .base import BaseTask
from .content_pipeline import ContentPipelineTask

logger = logging.getLogger(__name__)

# Matches ContentPipelineTask's 3-drafts-per-run cap.
DEFAULT_MAX_ITEMS_PER_RUN = 3


class EditorialCalendarTickTask(BaseTask):
    """Hourly: generate drafts for due editorial calendar items."""

    @property
    def task_type(self) -> str:
        return "editorial_calendar_tick"

    @property
    def description(self) -> str:
        return "Generate drafts for due editorial calendar items (drafts only, never publishes)"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        try:
            from scripts.campaigns import calendar as editorial_calendar
        except Exception as e:
            logger.warning("Editorial calendar store unavailable: %s", e)
            return {"success": False, "error": f"calendar store unavailable: {e}"}

        try:
            due = editorial_calendar.due_items()
        except Exception as e:
            logger.exception("failed to read editorial calendar")
            return {"success": False, "error": f"failed to read editorial calendar: {e}"}

        if not due:
            return {
                "success": True,
                "summary": "No editorial calendar items due",
                "generated": 0,
            }

        extra = getattr(task.config, "extra", None) or {}
        try:
            max_items = int(extra.get("max_items", DEFAULT_MAX_ITEMS_PER_RUN))
        except (TypeError, ValueError):
            max_items = DEFAULT_MAX_ITEMS_PER_RUN

        pipeline = ContentPipelineTask()
        generated: List[Dict[str, Any]] = []
        failures: List[str] = []

        for item in due[:max_items]:
            item_id = item.get("id", "?")
            editorial_calendar.mark_status(item_id, "generating")
            try:
                client = self._resolve_client(task, item)
                keyword = item.get("keyword") or ""
                opportunity = {
                    "type": item.get("format") or "blog",
                    "topic": item.get("title", ""),
                    "keywords": [keyword] if keyword else [],
                    "priority": "high",
                    "persona": item.get("persona"),
                    "calendar_item_id": item_id,
                }

                # Same code path content_pipeline.py uses: draft + save only.
                draft = await pipeline._generate_draft(client, opportunity)

                if draft and "error" not in draft:
                    client_id = client.get("id") or item.get("site", "")
                    saved = pipeline._save_drafts(client_id, [draft])
                    note = (
                        f"draft saved: {saved[0]}; awaiting quality gate + human approval"
                        if saved
                        else "draft generated but not saved; awaiting quality gate + human approval"
                    )
                    editorial_calendar.mark_status(item_id, "ready", notes=note)
                    generated.append({
                        "id": item_id,
                        "title": item.get("title"),
                        "site": item.get("site"),
                        "saved_paths": saved,
                    })
                else:
                    err = (draft or {}).get("error", "generation returned no draft")
                    # Revert to planned so the next tick retries; note the failure.
                    editorial_calendar.mark_status(
                        item_id, "planned", notes=f"generation failed: {err}"
                    )
                    failures.append(f"{item_id}: {err}")
            except Exception as e:
                logger.exception("editorial calendar item %s failed", item_id)
                try:
                    editorial_calendar.mark_status(
                        item_id, "planned", notes=f"generation failed: {e}"
                    )
                except Exception:
                    pass
                failures.append(f"{item_id}: {e}")

        return {
            "success": not failures,
            "summary": (
                f"Editorial calendar: {len(generated)} draft(s) generated, "
                f"{len(failures)} failure(s), {max(len(due) - max_items, 0)} deferred "
                f"— drafts await quality gate + human approval (nothing published)"
            ),
            "generated": len(generated),
            "items": generated,
            "errors": failures,
        }

    def _resolve_client(self, task: ScheduledTask, item: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve the client/brand for an item: task.client, else item site.

        Falls back to a minimal client dict so draft generation still works
        when the site isn't a registered brand (the draft simply lacks brand
        voice/previous-content context).
        """
        client_id = task.client or item.get("site") or ""
        if client_id:
            try:
                from gateway.config import config
                client = config.get_client(client_id)
                if client:
                    return client
            except Exception:
                logger.warning("Could not load client config for %s", client_id, exc_info=True)
        return {"id": client_id or "unknown", "name": client_id or "unknown"}
