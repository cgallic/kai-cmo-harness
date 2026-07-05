"""Self-improvement loop task handlers.

Wraps the scripts in ``scripts/self_improvement/`` so the agent scheduler
runs the documented loop (docs/OPENCLAW_SETUP.md section 3) without external
cron:

- ``performance_check_30d``  — daily 02:00: 30-day GSC/GA4 pull, winner/loser
  grading, pending-check reconciliation (memory/edge-cases.md EC-12)
- ``pattern_extract_weekly`` — Mon 14:00: winner pattern mining + weekly
  aggregation into ``what-works.md`` / ``weekly-patterns.md``
- ``harness_defaults_update`` — Mon 14:30: statistically-significant defaults
  written via the EC-11 safe-write path (safe_write.py validates + backs up)

All handlers degrade gracefully: missing credentials (Google/Gemini) or a
missing optional dependency is a DATA GAP reported in the result dict —
never an exception that puts the scheduler into a crash/retry loop, and
never a reason to grade content against empty analytics (memory/lessons.md
2026-06-09: missing connectors are data gaps, never zeros).

These handlers only read analytics and update local knowledge/policy files
through their guarded write paths. They never publish or mutate a live
channel.
"""

from __future__ import annotations

import asyncio
import importlib
import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..models import ScheduledTask
from .base import BaseTask

logger = logging.getLogger(__name__)

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PATTERN_EXTRACT_TIMEOUT = 120  # seconds per winner subprocess


def _import_module(dotted: str) -> Tuple[Optional[Any], Optional[str]]:
    """Import a self-improvement module, returning (module, error).

    Import failures (e.g. ``google-genai`` not installed for
    pattern_extract.py) are returned as strings, not raised — the caller
    reports them as a data gap instead of crash-looping the scheduler.
    """
    try:
        return importlib.import_module(dotted), None
    except Exception as e:  # ImportError or import-time config side effects
        logger.warning("Could not import %s: %s", dotted, e)
        return None, str(e)


class PerformanceCheck30dTask(BaseTask):
    """Daily 30-day performance check (performance_check.py main flow)."""

    @property
    def task_type(self) -> str:
        return "performance_check_30d"

    @property
    def description(self) -> str:
        return "Run due 30-day GSC/GA4 performance checks and grade content"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._run)

    def _run(self) -> Dict[str, Any]:
        mod, err = _import_module("scripts.self_improvement.performance_check")
        if mod is None:
            return {
                "success": False,
                "error": f"performance_check unavailable: {err}",
                "summary": "30-day check skipped — performance_check.py could not be loaded",
            }

        # Self-heal the schedule first (EC-12): pending_checks/<id>.json is the
        # only schedule record, so rebuild missing files from the content log.
        try:
            reconciled = mod.reconcile_pending_checks()
        except Exception as e:
            logger.exception("pending-check reconciliation failed")
            return {"success": False, "error": f"reconciliation failed: {e}"}

        try:
            checks = mod.get_pending_checks()
        except Exception as e:
            logger.exception("could not read pending checks")
            return {
                "success": False,
                "error": f"could not read pending checks: {e}",
                "reconciled": reconciled,
            }

        if not checks:
            return {
                "success": True,
                "summary": f"No 30-day checks due ({reconciled} pending check(s) reconciled)",
                "checked": 0,
                "winners": 0,
                "reconciled": reconciled,
            }

        # Credentials gate: without GSC/GA4 access every check would read as
        # zero data and grade "underperformer". Missing data is a data gap —
        # defer the checks instead of mis-grading them.
        creds_path = os.environ.get("GOOGLE_CREDENTIALS_PATH", "")
        if not creds_path or not os.path.exists(creds_path):
            msg = (
                f"GOOGLE_CREDENTIALS_PATH not configured — deferred "
                f"{len(checks)} due 30-day check(s) rather than grading against "
                f"empty analytics (data gap, not a zero)"
            )
            logger.warning(msg)
            return {
                "success": False,
                "error": msg,
                "summary": msg,
                "data_gap": True,
                "deferred": len(checks),
                "reconciled": reconciled,
            }

        results: List[Dict[str, Any]] = []
        errors: List[str] = []
        for check_file, check in checks:
            try:
                results.append(mod.run_check(check_file, check))
            except Exception as e:
                logger.exception("30-day check failed for %s", check.get("id"))
                errors.append(f"{check.get('id', '?')}: {e}")

        winners = [r for r in results if r.get("evaluation", {}).get("is_winner")]

        # Winners feed pattern extraction (same as performance_check.py main()).
        # Subprocess keeps the optional google-genai dependency out of the
        # agent process; a failure here is logged, never fatal.
        for winner in winners:
            url = winner.get("url", "")
            try:
                proc = subprocess.run(
                    [sys.executable, "-m", "scripts.self_improvement.pattern_extract",
                     "--url", url],
                    cwd=str(_REPO_ROOT),
                    capture_output=True,
                    text=True,
                    timeout=PATTERN_EXTRACT_TIMEOUT,
                )
                if proc.returncode != 0:
                    errors.append(
                        f"pattern_extract {url}: exit {proc.returncode} "
                        f"{(proc.stderr or '')[:200]}"
                    )
            except Exception as e:
                logger.warning("Pattern extraction failed for %s: %s", url, e)
                errors.append(f"pattern_extract {url}: {e}")

        return {
            "success": not errors,
            "summary": (
                f"{len(results)}/{len(checks)} 30-day check(s) run, "
                f"{len(winners)} winner(s), {reconciled} reconciled"
            ),
            "checked": len(results),
            "winners": len(winners),
            "reconciled": reconciled,
            "errors": errors,
        }


class PatternExtractWeeklyTask(BaseTask):
    """Weekly pattern mining: process unprocessed winners + aggregate patterns."""

    @property
    def task_type(self) -> str:
        return "pattern_extract_weekly"

    @property
    def description(self) -> str:
        return "Mine winner patterns into what-works.md and run weekly aggregation"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._run)

    def _run(self) -> Dict[str, Any]:
        mod, err = _import_module("scripts.self_improvement.pattern_extract")
        if mod is None:
            # google-genai (or config) unavailable — data gap, not a crash.
            return {
                "success": False,
                "error": f"pattern_extract unavailable: {err}",
                "summary": "Weekly pattern extraction skipped — dependency/config missing (data gap)",
                "data_gap": True,
            }

        cfg = getattr(mod, "_CFG", None)
        if cfg is not None and not getattr(cfg, "gemini_api_key", ""):
            msg = "GEMINI_API_KEY not configured — weekly pattern extraction skipped (data gap)"
            logger.warning(msg)
            return {"success": False, "error": msg, "summary": msg, "data_gap": True}

        errors: List[str] = []

        # 1) Process unprocessed winners (default main() flow).
        processed = 0
        try:
            entries = mod.load_log()
            dirty = False
            for entry in entries:
                if mod.is_winner(entry) and not entry.get("patterns_extracted"):
                    analysis = mod.analyze_winner(entry)
                    mod.append_to_what_works(entry, analysis)
                    entry["patterns_extracted"] = True
                    processed += 1
                    dirty = True
            if dirty:
                import json as _json
                with open(mod.CONTENT_LOG, "w") as f:
                    _json.dump(entries, f, indent=2)
        except Exception as e:
            # EC-13: pattern_extract's circuit breaker is in-memory; once it
            # opens we get a fast RuntimeError here instead of hammering Gemini.
            logger.exception("winner pattern extraction failed")
            errors.append(f"winner extraction: {e}")

        # 2) Weekly aggregation across all sites.
        patterns_text = ""
        try:
            patterns_text = mod.run_weekly_aggregation("all")
        except Exception as e:
            logger.exception("weekly aggregation failed")
            errors.append(f"weekly aggregation: {e}")

        return {
            "success": not errors,
            "summary": (
                f"{processed} winner(s) mined; weekly aggregation: "
                f"{(patterns_text or 'skipped')[:300]}"
            ),
            "winners_processed": processed,
            "patterns": patterns_text,
            "errors": errors,
        }


class HarnessDefaultsUpdateTask(BaseTask):
    """Weekly defaults update (harness_defaults_update.py main flow)."""

    @property
    def task_type(self) -> str:
        return "harness_defaults_update"

    @property
    def description(self) -> str:
        return "Update MARKETING.md/policy defaults when patterns reach significance"

    async def execute(self, task: ScheduledTask, **kwargs) -> Optional[Dict[str, Any]]:
        return await asyncio.to_thread(self._run)

    def _run(self) -> Dict[str, Any]:
        mod, err = _import_module("scripts.self_improvement.harness_defaults_update")
        if mod is None:
            return {
                "success": False,
                "error": f"harness_defaults_update unavailable: {err}",
                "summary": "Defaults update skipped — harness_defaults_update.py could not be loaded",
            }

        try:
            entries = mod.load_log()
            patterns = mod.analyze_patterns(entries)
        except Exception as e:
            logger.exception("pattern analysis failed")
            return {"success": False, "error": f"pattern analysis failed: {e}"}

        if patterns.get("insufficient_data"):
            n = patterns.get("n", 0)
            required = patterns.get("required", 0)
            return {
                "success": True,
                "summary": (
                    f"Insufficient data ({n}/{required} measured entries) — "
                    f"defaults unchanged (data gap, keep publishing)"
                ),
                "updated": 0,
            }

        # Writes below go through safe_write.py (EC-11): round-trip-validated
        # atomic replaces with .bak backups; aborted writes leave originals.
        try:
            updates = mod.update_marketing_md(patterns)
        except Exception as e:
            logger.exception("MARKETING.md update failed")
            return {"success": False, "error": f"MARKETING.md update failed: {e}"}

        try:
            policy_result = mod.update_policy_thresholds(patterns)
        except Exception as e:
            logger.exception("policy threshold update failed")
            return {"success": False, "error": f"policy threshold update failed: {e}"}

        policy_updates = policy_result.get("updates", [])
        drift_alerts = policy_result.get("drift_alerts", [])
        all_updates = list(updates) + list(policy_updates)

        if drift_alerts:
            try:
                mod.post_drift_alert(drift_alerts)
            except Exception:
                logger.warning("drift alert notification failed", exc_info=True)

        if all_updates:
            try:
                mod.save_defaults(patterns)
            except Exception as e:
                logger.exception("saving harness defaults failed")
                return {
                    "success": False,
                    "error": f"saving defaults failed: {e}",
                    "updates": all_updates,
                    "drift_alerts": drift_alerts,
                }
            try:
                mod.post_discord(all_updates, patterns)
            except Exception:
                logger.warning("defaults digest notification failed", exc_info=True)

        summary_bits = [f"{len(all_updates)} default(s) updated"]
        if drift_alerts:
            summary_bits.append(f"{len(drift_alerts)} drift alert(s) — policy writes halted")
        return {
            "success": True,
            "summary": "; ".join(summary_bits),
            "updated": len(all_updates),
            "updates": all_updates,
            "drift_alerts": drift_alerts,
        }
