"""Learning review flow -- review, confirm, and manage learned memories.

Provides a structured workflow for operators to:

1. View recent learnings from the memory system
2. Confirm or dismiss pending observations
3. Review and re-validate stale memories
4. Get a summary of learning health by category

Works with the memory writeback (Task 073) and memory schemas
(Task 074) to surface actionable learning insights.
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(ts: str) -> Optional[datetime]:
    try:
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _load_json_file(path: str) -> Optional[Dict[str, Any]]:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _read_jsonl(path: str) -> List[Dict[str, Any]]:
    """Read all JSON lines from a file. Returns [] if missing."""
    records: List[Dict[str, Any]] = []
    if not os.path.isfile(path):
        return records
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if line:
                    records.append(json.loads(line))
    except Exception:
        pass
    return records


# ---------------------------------------------------------------------------
# Learning categories (aligned with writeback.py LearningCategory)
# ---------------------------------------------------------------------------

_LEARNING_CATEGORIES = [
    "brand_preference",
    "creative_performance",
    "channel_insight",
    "audience_insight",
    "offer_performance",
    "compliance_constraint",
    "operator_preference",
    "business_fact",
    "execution_record",
]

# Memory layer names (aligned with schemas.py)
_MEMORY_LAYERS = [
    "business_facts",
    "brand_constraints",
    "proof_assets",
    "channel_learnings",
    "offer_learnings",
    "audience_learnings",
]


# ---------------------------------------------------------------------------
# LearningReviewFlow
# ---------------------------------------------------------------------------

class LearningReviewFlow:
    """Operator flow for reviewing and managing learned knowledge.

    Usage::

        flow = LearningReviewFlow(workspace_dir="workspace")
        overview = flow.start("biz_abc123")
        pending = flow.get_pending_confirmations("biz_abc123")
        result = flow.confirm_learning("learn_abc123", confirmed=True,
                                       notes="Verified with client")
        stale = flow.review_stale_memories("biz_abc123")
        summary = flow.get_learning_summary("biz_abc123")
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir

    # -- lifecycle -------------------------------------------------------

    def start(self, business_id: str) -> Dict[str, Any]:
        """Load recent learnings and separate by confirmation status.

        Returns
        -------
        dict with keys:
            recent_learnings, pending_confirmations, stale_memories
        """
        recent = self._load_recent_learnings(business_id, days=30)
        pending = [l for l in recent if l.get("requires_confirmation", False)
                   and l.get("confidence") != "confirmed"]
        stale = self._find_stale_memories(business_id)

        return {
            "recent_learnings": recent,
            "pending_confirmations": pending,
            "stale_memories": stale,
            "total_recent": len(recent),
            "total_pending": len(pending),
            "total_stale": len(stale),
        }

    # -- pending confirmations -------------------------------------------

    def get_pending_confirmations(self, business_id: str) -> List[Dict[str, Any]]:
        """Return learnings awaiting operator confirmation.

        Scans all learning category JSONL files for entries where
        ``requires_confirmation`` is True and confidence is not yet
        ``confirmed``.
        """
        all_learnings = self._load_all_learnings(business_id)
        pending: List[Dict[str, Any]] = []

        for learning in all_learnings:
            if learning.get("requires_confirmation") and learning.get("confidence") != "confirmed":
                pending.append({
                    "learning_id": learning.get("id", ""),
                    "category": learning.get("category", ""),
                    "title": learning.get("title", ""),
                    "finding": learning.get("finding", ""),
                    "confidence": learning.get("confidence", ""),
                    "channel": learning.get("channel"),
                    "content_type": learning.get("content_type"),
                    "created_at": learning.get("created_at", ""),
                    "evidence": learning.get("evidence", {}),
                })

        # Sort by creation date descending (newest first)
        pending.sort(key=lambda p: p.get("created_at", ""), reverse=True)
        return pending

    # -- confirm / dismiss -----------------------------------------------

    def confirm_learning(
        self,
        learning_id: str,
        confirmed: bool,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Confirm or dismiss a learning.

        If *confirmed* is True, the learning's confidence is elevated
        to ``confirmed`` and ``requires_confirmation`` is set to False.
        If False, the learning is marked as dismissed (archived).

        The updated record is persisted back to its JSONL file.
        """
        result = self._update_learning(learning_id, confirmed, notes)
        return result

    # -- stale memories --------------------------------------------------

    def review_stale_memories(self, business_id: str) -> List[Dict[str, Any]]:
        """Return memories past their staleness date for re-validation.

        Tries to load memory layer schemas (Task 074) for structured
        staleness checking.  Falls back to a simple timestamp-based
        approach if schemas are not available.
        """
        return self._find_stale_memories(business_id)

    # -- learning summary ------------------------------------------------

    def get_learning_summary(self, business_id: str) -> Dict[str, Any]:
        """Return a comprehensive learning health summary.

        Returns
        -------
        dict with keys:
            total_learnings, by_category, strongest_insights,
            newest_learnings, recommended_review_cadence
        """
        all_learnings = self._load_all_learnings(business_id)

        # Group by category
        by_category: Dict[str, int] = {}
        for learning in all_learnings:
            cat = learning.get("category", "unknown")
            by_category[cat] = by_category.get(cat, 0) + 1

        # Find strongest insights (high confidence, most evidence)
        confirmed = [
            l for l in all_learnings
            if l.get("confidence") == "confirmed"
        ]
        confirmed.sort(
            key=lambda l: len(l.get("evidence", {})),
            reverse=True,
        )
        strongest = [
            {
                "learning_id": l.get("id", ""),
                "title": l.get("title", ""),
                "category": l.get("category", ""),
                "finding": l.get("finding", ""),
            }
            for l in confirmed[:5]
        ]

        # Newest learnings
        all_sorted = sorted(
            all_learnings,
            key=lambda l: l.get("created_at", ""),
            reverse=True,
        )
        newest = [
            {
                "learning_id": l.get("id", ""),
                "title": l.get("title", ""),
                "category": l.get("category", ""),
                "created_at": l.get("created_at", ""),
                "confidence": l.get("confidence", ""),
            }
            for l in all_sorted[:10]
        ]

        # Determine recommended review cadence based on volume
        total = len(all_learnings)
        pending_count = sum(
            1 for l in all_learnings
            if l.get("requires_confirmation") and l.get("confidence") != "confirmed"
        )

        if pending_count > 20:
            cadence = "daily"
        elif pending_count > 5:
            cadence = "twice_weekly"
        elif total > 50:
            cadence = "weekly"
        else:
            cadence = "bi_weekly"

        return {
            "total_learnings": total,
            "by_category": by_category,
            "strongest_insights": strongest,
            "newest_learnings": newest,
            "pending_confirmation_count": pending_count,
            "recommended_review_cadence": cadence,
        }

    # -- private helpers -------------------------------------------------

    def _memory_dir(self, business_id: str) -> str:
        """Return the memory directory path for a business."""
        return os.path.join(self.workspace_dir, business_id, "memory")

    def _load_all_learnings(self, business_id: str) -> List[Dict[str, Any]]:
        """Load all learnings across all categories from JSONL files."""
        mem_dir = self._memory_dir(business_id)
        all_learnings: List[Dict[str, Any]] = []

        for category in _LEARNING_CATEGORIES:
            filepath = os.path.join(mem_dir, f"{category}.jsonl")
            records = _read_jsonl(filepath)
            for rec in records:
                rec.setdefault("category", category)
                all_learnings.append(rec)

        return all_learnings

    def _load_recent_learnings(
        self, business_id: str, days: int = 30,
    ) -> List[Dict[str, Any]]:
        """Load learnings created within the last *days* days."""
        all_learnings = self._load_all_learnings(business_id)
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        recent: List[Dict[str, Any]] = []
        for learning in all_learnings:
            created_at = learning.get("created_at", "")
            dt = _parse_iso(created_at)
            if dt is not None and dt >= cutoff:
                recent.append(learning)

        recent.sort(key=lambda l: l.get("created_at", ""), reverse=True)
        return recent

    def _find_stale_memories(self, business_id: str) -> List[Dict[str, Any]]:
        """Find stale memory entries across all layers.

        Attempts to use the structured memory schemas from Task 074.
        Falls back to a simple JSONL scan with default staleness of
        90 days.
        """
        stale_entries: List[Dict[str, Any]] = []

        # Try the structured schema approach first
        try:
            from kai.memory.schemas import get_all_stale_entries
            stale_by_layer = get_all_stale_entries(business_id, self.workspace_dir)
            for layer_name, entries in stale_by_layer.items():
                for entry in entries:
                    if hasattr(entry, "model_dump"):
                        entry_data = entry.model_dump()
                    elif hasattr(entry, "__dict__"):
                        entry_data = dict(vars(entry))
                    else:
                        entry_data = {"raw": str(entry)}
                    entry_data["_layer"] = layer_name
                    stale_entries.append(entry_data)
            return stale_entries
        except ImportError:
            pass

        # Fallback: scan JSONL files for old entries
        default_staleness_days = 90
        cutoff = datetime.now(timezone.utc) - timedelta(days=default_staleness_days)
        all_learnings = self._load_all_learnings(business_id)

        for learning in all_learnings:
            # Skip already-archived entries
            if learning.get("status") == "archived":
                continue
            if learning.get("confidence") == "confirmed":
                # Confirmed learnings have longer shelf life
                check_cutoff = datetime.now(timezone.utc) - timedelta(days=180)
            else:
                check_cutoff = cutoff

            created_at = learning.get("created_at", "")
            updated_at = learning.get("updated_at", created_at)
            ref_ts = updated_at or created_at

            dt = _parse_iso(ref_ts)
            if dt is not None and dt < check_cutoff:
                stale_entries.append({
                    "learning_id": learning.get("id", ""),
                    "category": learning.get("category", ""),
                    "title": learning.get("title", ""),
                    "finding": learning.get("finding", ""),
                    "confidence": learning.get("confidence", ""),
                    "last_updated": ref_ts,
                    "staleness_reason": "Exceeds staleness threshold",
                })

        return stale_entries

    def _update_learning(
        self,
        learning_id: str,
        confirmed: bool,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Find and update a learning record in its JSONL file.

        Rewrites the entire JSONL file with the updated record.  This
        is acceptable because learning files are append-heavy but
        relatively small.
        """
        # Scan all business directories in the workspace
        workspace = self.workspace_dir
        if not os.path.isdir(workspace):
            return {"success": False, "reason": "Workspace directory not found."}

        for entry in os.listdir(workspace):
            biz_path = os.path.join(workspace, entry)
            if not os.path.isdir(biz_path):
                continue

            mem_dir = os.path.join(biz_path, "memory")
            if not os.path.isdir(mem_dir):
                continue

            for category in _LEARNING_CATEGORIES:
                filepath = os.path.join(mem_dir, f"{category}.jsonl")
                if not os.path.isfile(filepath):
                    continue

                records = _read_jsonl(filepath)
                found = False

                for rec in records:
                    if rec.get("id") == learning_id:
                        found = True
                        if confirmed:
                            rec["confidence"] = "confirmed"
                            rec["requires_confirmation"] = False
                            action = "confirmed"
                        else:
                            rec["confidence"] = "dismissed"
                            rec["requires_confirmation"] = False
                            rec["status"] = "archived"
                            action = "dismissed"

                        if notes:
                            rec["operator_notes"] = notes

                        rec["updated_at"] = _utc_now()
                        break

                if found:
                    # Rewrite the JSONL file atomically
                    self._rewrite_jsonl(filepath, records)
                    return {
                        "success": True,
                        "learning_id": learning_id,
                        "action": action,
                        "notes": notes,
                        "updated_at": _utc_now(),
                    }

        return {"success": False, "reason": f"Learning {learning_id} not found."}

    @staticmethod
    def _rewrite_jsonl(filepath: str, records: List[Dict[str, Any]]) -> None:
        """Rewrite a JSONL file atomically."""
        tmp_path = filepath + ".tmp"
        try:
            with open(tmp_path, "w", encoding="utf-8") as fh:
                for rec in records:
                    fh.write(json.dumps(rec, separators=(",", ":"), sort_keys=True, default=str) + "\n")
            os.replace(tmp_path, filepath)
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
