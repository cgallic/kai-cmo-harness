"""Social scheduling, queue, and approval management for Kai Marketing OS.

Provides the operational control plane for social publishing:

- **PostQueue** manages when posts go out, enforces frequency limits, detects
  conflicts and content similarity, and surfaces a calendar view.
- **ApprovalQueue** routes posts through operator review before publishing,
  with optional auto-approval for low-risk content.
- **SchedulingRules** and ``DEFAULT_SCHEDULING_RULES`` encode per-platform
  best-practice posting windows and rate caps.

Thread safety: all mutating operations on ``PostQueue`` are protected by an
``RLock``.  ``ApprovalQueue`` is likewise internally synchronized.
"""

from __future__ import annotations

import copy
import logging
import re
import threading
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Pydantic import with fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]

logger = logging.getLogger(__name__)

# ============================================================================
# Helpers
# ============================================================================


def generate_queue_id() -> str:
    """Return a unique queue-post ID with ``qp_`` prefix."""
    return f"qp_{uuid.uuid4().hex[:12]}"


def generate_approval_id() -> str:
    """Return a unique approval-request ID with ``apr_`` prefix."""
    return f"apr_{uuid.uuid4().hex[:12]}"


def parse_iso_timestamp(ts: str) -> datetime:
    """Parse an ISO-8601 timestamp string into a *datetime* object.

    Falls back to a manual parse for the common ``YYYY-MM-DDTHH:MM:SS``
    formats when ``fromisoformat`` is unavailable or rejects the string.
    """
    try:
        return datetime.fromisoformat(ts)
    except (ValueError, AttributeError):
        # Strip trailing 'Z' and retry
        cleaned = ts.replace("Z", "+00:00")
        return datetime.fromisoformat(cleaned)


def is_within_posting_hours(timestamp: str, rules: SchedulingRules) -> bool:
    """Return *True* if *timestamp* falls within allowed posting hours.

    Checks both ``no_post_hours`` and ``no_post_days`` from *rules*.
    """
    dt = parse_iso_timestamp(timestamp)

    # Check day of week
    day_name = dt.strftime("%A").lower()
    if day_name in [d.lower() for d in rules.no_post_days]:
        return False

    # Check hour
    if dt.hour in rules.no_post_hours:
        return False

    # Check holiday list
    if rules.respect_holidays:
        date_str = dt.strftime("%Y-%m-%d")
        if date_str in rules.holiday_list:
            return False

    return True


def count_posts_on_date(
    queue: Dict[str, "QueuedPost"], platform: str, date: str
) -> int:
    """Count posts scheduled/published for *platform* on *date* (``YYYY-MM-DD``)."""
    count = 0
    for post in queue.values():
        if post.platform != platform:
            continue
        if post.status in ("cancelled", "rejected", "failed", "draft"):
            continue
        if post.scheduled_time is not None:
            try:
                post_date = parse_iso_timestamp(post.scheduled_time).strftime("%Y-%m-%d")
                if post_date == date:
                    count += 1
            except (ValueError, TypeError):
                continue
        elif post.published_at is not None:
            try:
                post_date = parse_iso_timestamp(post.published_at).strftime("%Y-%m-%d")
                if post_date == date:
                    count += 1
            except (ValueError, TypeError):
                continue
    return count


# ============================================================================
# Enums
# ============================================================================


class PostStatus(str, Enum):
    """Lifecycle states for a queued social post."""

    draft = "draft"
    pending_approval = "pending_approval"
    approved = "approved"
    scheduled = "scheduled"
    publishing = "publishing"
    published = "published"
    failed = "failed"
    cancelled = "cancelled"
    rejected = "rejected"


# ============================================================================
# Data Models
# ============================================================================


class QueuedPost(BaseModel):
    """A social media post managed by the scheduling queue."""

    id: str = Field(default_factory=generate_queue_id, description="Unique queue ID (qp_<hex>)")
    platform: str = Field(..., description="Target platform (instagram, facebook, linkedin, tiktok, x_twitter, youtube)")
    content_type: Optional[str] = Field(None, description="SocialContentType value from Task 040, if applicable")
    content_text: str = Field(..., description="Full caption / post text")
    media_refs: List[str] = Field(default_factory=list, description="Media URLs or asset IDs")
    media_type: Optional[str] = Field(None, description="image, video, carousel, reel, story, short")
    hashtags: List[str] = Field(default_factory=list, description="Hashtags to include")
    location_tag: Optional[str] = Field(None, description="Geo-tag identifier")
    link_url: Optional[str] = Field(None, description="URL to include if platform supports it")
    scheduled_time: Optional[str] = Field(None, description="ISO timestamp for when to publish")
    status: str = Field("draft", description="PostStatus value")
    priority: int = Field(100, description="Queue priority (lower = higher priority)")
    created_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp when created",
    )
    updated_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of last update",
    )
    approved_at: Optional[str] = Field(None, description="ISO timestamp when approved")
    approved_by: Optional[str] = Field(None, description="Who approved (operator ID or 'auto')")
    published_at: Optional[str] = Field(None, description="ISO timestamp when actually published")
    published_url: Optional[str] = Field(None, description="URL of the live post")
    error_message: Optional[str] = Field(None, description="Error details if failed")
    retry_count: int = Field(0, description="How many times publication has been attempted")
    max_retries: int = Field(3, description="Maximum retry attempts")
    source_action_id: Optional[str] = Field(None, description="Link to ProposedAction if from proposal system")
    tags: List[str] = Field(default_factory=list, description="Freeform tags for filtering")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary metadata")


class SchedulingRules(BaseModel):
    """Per-platform scheduling constraints and optimal posting windows."""

    platform: str = Field(..., description="Which platform these rules apply to")
    optimal_posting_times: List[Dict[str, Any]] = Field(
        default_factory=list,
        description='List of {day: str, hours: List[int]} for best posting times',
    )
    max_posts_per_day: int = Field(..., description="Hard cap on posts per day")
    recommended_posts_per_day: float = Field(..., description="Ideal posting frequency")
    min_gap_minutes: int = Field(120, description="Minimum minutes between posts on same platform")
    no_post_days: List[str] = Field(default_factory=list, description="Days to never post (e.g., 'sunday')")
    no_post_hours: List[int] = Field(default_factory=list, description="Hours (0-23) to never post")
    timezone: str = Field("America/New_York", description="IANA timezone string")
    respect_holidays: bool = Field(True, description="Skip posting on major holidays")
    holiday_list: List[str] = Field(
        default_factory=list,
        description="Holiday dates in YYYY-MM-DD format",
    )


class ApprovalRequest(BaseModel):
    """A request to review a queued post before publishing."""

    id: str = Field(default_factory=generate_approval_id, description="Unique approval request ID (apr_<hex>)")
    post_id: str = Field(..., description="ID of the QueuedPost needing approval")
    requested_at: str = Field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(),
        description="ISO timestamp of request creation",
    )
    requested_by: str = Field(..., description="Who/what triggered the request (e.g., 'system', 'scheduler')")
    reason: str = Field(..., description="Why approval is needed")
    status: str = Field("pending", description="pending, approved, or rejected")
    reviewed_at: Optional[str] = Field(None, description="ISO timestamp when reviewed")
    reviewed_by: Optional[str] = Field(None, description="Who reviewed the request")
    review_notes: Optional[str] = Field(None, description="Operator notes on approval/rejection")
    auto_approve_eligible: bool = Field(False, description="Whether this post could be auto-approved")


class CalendarEntry(BaseModel):
    """A single entry in the social content calendar view."""

    date: str = Field(..., description="YYYY-MM-DD")
    time: str = Field(..., description="HH:MM (24hr)")
    platform: str = Field(..., description="Platform name")
    post_id: str = Field(..., description="QueuedPost ID")
    content_preview: str = Field(..., description="First 100 characters of content text")
    content_type: Optional[str] = Field(None, description="Content type if set")
    status: str = Field(..., description="Current post status")
    media_count: int = Field(0, description="Number of media attachments")


class ContentSimilarityCheck(BaseModel):
    """Result of comparing two posts for content similarity."""

    post_a_id: str = Field(..., description="First post ID")
    post_b_id: str = Field(..., description="Second post ID")
    similarity_score: float = Field(..., description="0.0 to 1.0 similarity score")
    similarity_type: str = Field(
        ...,
        description="exact_duplicate, near_duplicate, similar_topic, or different",
    )
    time_gap_hours: float = Field(..., description="Hours between the two posts' scheduled times")


# ============================================================================
# Default Scheduling Rules
# ============================================================================

_WEEKDAYS = ["monday", "tuesday", "wednesday", "thursday", "friday"]
_ALL_DAYS = _WEEKDAYS + ["saturday", "sunday"]


def _make_optimal_times(days: List[str], hours: List[int]) -> List[Dict[str, Any]]:
    """Build an ``optimal_posting_times`` list from days and hours."""
    return [{"day": d, "hours": list(hours)} for d in days]


DEFAULT_SCHEDULING_RULES: Dict[str, SchedulingRules] = {
    # ------------------------------------------------------------------
    # Instagram
    # ------------------------------------------------------------------
    "instagram": SchedulingRules(
        platform="instagram",
        optimal_posting_times=_make_optimal_times(_WEEKDAYS, [9, 12, 17]),
        max_posts_per_day=3,
        recommended_posts_per_day=1.0,
        min_gap_minutes=180,
        no_post_days=[],
        no_post_hours=[0, 1, 2, 3, 4, 5, 6],
        timezone="America/New_York",
    ),
    # ------------------------------------------------------------------
    # Facebook
    # ------------------------------------------------------------------
    "facebook": SchedulingRules(
        platform="facebook",
        optimal_posting_times=_make_optimal_times(_WEEKDAYS, [9, 13]),
        max_posts_per_day=2,
        recommended_posts_per_day=1.0,
        min_gap_minutes=240,
        no_post_days=[],
        no_post_hours=[0, 1, 2, 3, 4, 5, 6],
        timezone="America/New_York",
    ),
    # ------------------------------------------------------------------
    # LinkedIn
    # ------------------------------------------------------------------
    "linkedin": SchedulingRules(
        platform="linkedin",
        optimal_posting_times=_make_optimal_times(_WEEKDAYS, [8, 12]),
        max_posts_per_day=2,
        recommended_posts_per_day=1.0,
        min_gap_minutes=360,
        no_post_days=["saturday", "sunday"],
        no_post_hours=[0, 1, 2, 3, 4, 5, 6, 20, 21, 22, 23],
        timezone="America/New_York",
    ),
    # ------------------------------------------------------------------
    # TikTok
    # ------------------------------------------------------------------
    "tiktok": SchedulingRules(
        platform="tiktok",
        optimal_posting_times=_make_optimal_times(_ALL_DAYS, [10, 14, 19]),
        max_posts_per_day=3,
        recommended_posts_per_day=1.0,
        min_gap_minutes=120,
        no_post_days=[],
        no_post_hours=[0, 1, 2, 3, 4, 5, 6, 7],
        timezone="America/New_York",
    ),
    # ------------------------------------------------------------------
    # X / Twitter
    # ------------------------------------------------------------------
    "x_twitter": SchedulingRules(
        platform="x_twitter",
        optimal_posting_times=_make_optimal_times(_WEEKDAYS, [9, 12, 17]),
        max_posts_per_day=5,
        recommended_posts_per_day=2.0,
        min_gap_minutes=60,
        no_post_days=[],
        no_post_hours=[0, 1, 2, 3, 4, 5, 6],
        timezone="America/New_York",
    ),
    # ------------------------------------------------------------------
    # YouTube
    # ------------------------------------------------------------------
    "youtube": SchedulingRules(
        platform="youtube",
        optimal_posting_times=_make_optimal_times(["tuesday", "thursday", "saturday"], [14]),
        max_posts_per_day=2,
        recommended_posts_per_day=0.3,
        min_gap_minutes=240,
        no_post_days=[],
        no_post_hours=[0, 1, 2, 3, 4, 5, 6, 7, 8],
        timezone="America/New_York",
    ),
}


# ============================================================================
# PostQueue
# ============================================================================


class PostQueue:
    """Manages the queue of posts across all platforms.

    All mutating operations are protected by an ``RLock`` for thread safety.
    """

    def __init__(self, rules: Optional[Dict[str, SchedulingRules]] = None) -> None:
        self._queue: Dict[str, QueuedPost] = {}
        self._approval_requests: Dict[str, ApprovalRequest] = {}
        self._rules: Dict[str, SchedulingRules] = (
            dict(rules) if rules is not None else dict(DEFAULT_SCHEDULING_RULES)
        )
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Queue mutations
    # ------------------------------------------------------------------

    def add_post(self, post: QueuedPost) -> QueuedPost:
        """Add a post to the queue.

        Assigns ``id`` and ``created_at`` if not already set, validates
        against scheduling rules, and stores the post.
        """
        with self._lock:
            # Ensure unique ID
            if not post.id or post.id in self._queue:
                post.id = generate_queue_id()

            now = datetime.now(timezone.utc).isoformat()
            post.created_at = now
            post.updated_at = now

            # Validate against scheduling rules if a time is set
            if post.scheduled_time:
                conflicts = self.check_conflicts(post)
                if conflicts:
                    logger.warning(
                        "Post %s has scheduling conflicts: %s",
                        post.id,
                        "; ".join(conflicts),
                    )
                    # Store the conflicts as metadata but still allow the add
                    if isinstance(post.metadata, dict):
                        post.metadata["scheduling_conflicts"] = conflicts

            self._queue[post.id] = post
            logger.info("Added post %s for %s (status=%s)", post.id, post.platform, post.status)
            return post

    def remove_post(self, post_id: str) -> bool:
        """Remove a post from the queue.

        Only allowed if status is ``draft``, ``pending_approval``,
        ``approved``, or ``scheduled``.  Returns *True* if the post was
        removed, *False* otherwise.
        """
        removable_statuses = {"draft", "pending_approval", "approved", "scheduled"}
        with self._lock:
            post = self._queue.get(post_id)
            if post is None:
                logger.warning("Cannot remove post %s: not found", post_id)
                return False

            if post.status not in removable_statuses:
                logger.warning(
                    "Cannot remove post %s: status '%s' is not removable",
                    post_id,
                    post.status,
                )
                return False

            del self._queue[post_id]
            # Also clean up any associated approval requests
            to_remove = [
                aid for aid, ar in self._approval_requests.items() if ar.post_id == post_id
            ]
            for aid in to_remove:
                del self._approval_requests[aid]

            logger.info("Removed post %s from queue", post_id)
            return True

    def update_post(self, post_id: str, updates: Dict[str, Any]) -> QueuedPost:
        """Update fields on a queued post.

        Content edits (``content_text``, ``media_refs``, ``hashtags``, etc.)
        are only allowed when status is ``draft`` or ``pending_approval``.
        Schedule-only changes (``scheduled_time``, ``priority``) are also
        allowed for ``approved`` or ``scheduled`` posts.

        Raises ``ValueError`` if the post is not found or the update is
        disallowed.
        """
        content_fields = {
            "content_text", "media_refs", "media_type", "hashtags",
            "location_tag", "link_url", "content_type", "tags",
        }
        schedule_fields = {"scheduled_time", "priority"}

        with self._lock:
            post = self._queue.get(post_id)
            if post is None:
                raise ValueError(f"Post {post_id} not found in queue")

            has_content_changes = bool(set(updates.keys()) & content_fields)
            has_schedule_changes = bool(set(updates.keys()) & schedule_fields)
            other_fields = set(updates.keys()) - content_fields - schedule_fields - {"metadata"}

            # Determine what is allowed based on status
            if post.status in ("draft", "pending_approval"):
                # Everything editable
                pass
            elif post.status in ("approved", "scheduled"):
                if has_content_changes or other_fields:
                    raise ValueError(
                        f"Post {post_id} is '{post.status}': only schedule/priority "
                        f"changes are allowed. To edit content, move back to draft first."
                    )
            else:
                raise ValueError(
                    f"Post {post_id} has status '{post.status}' and cannot be updated"
                )

            for key, value in updates.items():
                if hasattr(post, key):
                    setattr(post, key, value)

            post.updated_at = datetime.now(timezone.utc).isoformat()
            self._queue[post_id] = post
            logger.info("Updated post %s: fields=%s", post_id, list(updates.keys()))
            return post

    def reschedule_post(self, post_id: str, new_time: str) -> QueuedPost:
        """Change the scheduled time for a post.

        Validates the new time against scheduling rules.  Returns the
        updated post.

        Raises ``ValueError`` if the post is not found or not in a
        reschedulable state.
        """
        reschedulable = {"draft", "pending_approval", "approved", "scheduled"}
        with self._lock:
            post = self._queue.get(post_id)
            if post is None:
                raise ValueError(f"Post {post_id} not found in queue")
            if post.status not in reschedulable:
                raise ValueError(
                    f"Post {post_id} has status '{post.status}' and cannot be rescheduled"
                )

            old_time = post.scheduled_time
            post.scheduled_time = new_time
            post.updated_at = datetime.now(timezone.utc).isoformat()

            # Validate against rules
            conflicts = self.check_conflicts(post)
            if conflicts:
                logger.warning(
                    "Rescheduled post %s to %s with conflicts: %s",
                    post_id,
                    new_time,
                    "; ".join(conflicts),
                )
                if isinstance(post.metadata, dict):
                    post.metadata["scheduling_conflicts"] = conflicts

            self._queue[post_id] = post
            logger.info(
                "Rescheduled post %s from %s to %s", post_id, old_time, new_time
            )
            return post

    def reorder_queue(self, platform: str, post_ids: List[str]) -> List[QueuedPost]:
        """Reorder posts for *platform* by setting priority from list position.

        Posts listed first get the lowest priority number (highest priority).
        Returns the reordered list of posts.

        Raises ``ValueError`` if any post_id is not found or does not belong
        to the given platform.
        """
        with self._lock:
            reordered: List[QueuedPost] = []
            for idx, pid in enumerate(post_ids):
                post = self._queue.get(pid)
                if post is None:
                    raise ValueError(f"Post {pid} not found in queue")
                if post.platform != platform:
                    raise ValueError(
                        f"Post {pid} belongs to '{post.platform}', not '{platform}'"
                    )
                post.priority = idx + 1
                post.updated_at = datetime.now(timezone.utc).isoformat()
                self._queue[pid] = post
                reordered.append(post)

            logger.info(
                "Reordered %d posts for %s", len(reordered), platform
            )
            return reordered

    # ------------------------------------------------------------------
    # Query methods
    # ------------------------------------------------------------------

    def get_queue(
        self,
        platform: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> List[QueuedPost]:
        """Fetch the queue with optional filters.

        Results are sorted by ``scheduled_time`` (posts without a scheduled
        time are placed at the end, further sorted by priority).
        """
        with self._lock:
            results: List[QueuedPost] = []
            for post in self._queue.values():
                # Platform filter
                if platform is not None and post.platform != platform:
                    continue

                # Status filter
                if status is not None and post.status != status:
                    continue

                # Date range filter (based on scheduled_time)
                if date_from is not None or date_to is not None:
                    if post.scheduled_time is None:
                        continue
                    try:
                        post_dt = parse_iso_timestamp(post.scheduled_time)
                    except (ValueError, TypeError):
                        continue

                    if date_from is not None:
                        try:
                            from_dt = parse_iso_timestamp(date_from)
                            if post_dt < from_dt:
                                continue
                        except (ValueError, TypeError):
                            pass

                    if date_to is not None:
                        try:
                            to_dt = parse_iso_timestamp(date_to)
                            if post_dt > to_dt:
                                continue
                        except (ValueError, TypeError):
                            pass

                results.append(post)

            # Sort: scheduled posts by time, then unscheduled by priority
            def _sort_key(p: QueuedPost) -> tuple:
                if p.scheduled_time is not None:
                    try:
                        dt = parse_iso_timestamp(p.scheduled_time)
                        return (0, dt.isoformat(), p.priority)
                    except (ValueError, TypeError):
                        pass
                return (1, "", p.priority)

            results.sort(key=_sort_key)
            return results

    def get_next_post(self, platform: str) -> Optional[QueuedPost]:
        """Return the next post ready to publish for *platform*.

        Finds the post with status ``scheduled`` whose ``scheduled_time``
        is at or before the current moment, ordered by earliest time first.
        Returns *None* if no such post exists.
        """
        now = datetime.now(timezone.utc)
        with self._lock:
            candidates: List[tuple] = []
            for post in self._queue.values():
                if post.platform != platform:
                    continue
                if post.status != PostStatus.scheduled.value:
                    continue
                if post.scheduled_time is None:
                    continue
                try:
                    sched_dt = parse_iso_timestamp(post.scheduled_time)
                    # If the timestamp is naive, assume UTC
                    if sched_dt.tzinfo is None:
                        sched_dt = sched_dt.replace(tzinfo=timezone.utc)
                    if sched_dt <= now:
                        candidates.append((sched_dt, post))
                except (ValueError, TypeError):
                    continue

            if not candidates:
                return None

            # Earliest first
            candidates.sort(key=lambda c: c[0])
            return candidates[0][1]

    # ------------------------------------------------------------------
    # Approval bridge
    # ------------------------------------------------------------------

    def bulk_approve(
        self, post_ids: List[str], approved_by: str = "operator"
    ) -> List[QueuedPost]:
        """Approve multiple posts at once.

        Sets status to ``approved``, records ``approved_at`` and
        ``approved_by``.  Returns the list of updated posts.
        """
        now = datetime.now(timezone.utc).isoformat()
        approved: List[QueuedPost] = []
        with self._lock:
            for pid in post_ids:
                post = self._queue.get(pid)
                if post is None:
                    logger.warning("bulk_approve: post %s not found, skipping", pid)
                    continue
                if post.status not in ("draft", "pending_approval"):
                    logger.warning(
                        "bulk_approve: post %s has status '%s', skipping", pid, post.status
                    )
                    continue

                post.status = PostStatus.approved.value
                post.approved_at = now
                post.approved_by = approved_by
                post.updated_at = now
                self._queue[pid] = post
                approved.append(post)

                # Also update any related approval requests
                for ar in self._approval_requests.values():
                    if ar.post_id == pid and ar.status == "pending":
                        ar.status = "approved"
                        ar.reviewed_at = now
                        ar.reviewed_by = approved_by

            logger.info(
                "Bulk approved %d/%d posts by %s",
                len(approved),
                len(post_ids),
                approved_by,
            )
        return approved

    def submit_for_approval(
        self, post_id: str, reason: str = "Standard review"
    ) -> ApprovalRequest:
        """Move a post to ``pending_approval`` and create an ``ApprovalRequest``.

        Raises ``ValueError`` if the post is not found.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            post = self._queue.get(post_id)
            if post is None:
                raise ValueError(f"Post {post_id} not found in queue")

            post.status = PostStatus.pending_approval.value
            post.updated_at = now
            self._queue[post_id] = post

            approval = ApprovalRequest(
                id=generate_approval_id(),
                post_id=post_id,
                requested_at=now,
                requested_by="scheduler",
                reason=reason,
                status="pending",
            )
            self._approval_requests[approval.id] = approval

            logger.info(
                "Submitted post %s for approval (request %s): %s",
                post_id,
                approval.id,
                reason,
            )
            return approval

    # ------------------------------------------------------------------
    # Calendar view
    # ------------------------------------------------------------------

    def get_calendar_view(
        self,
        start_date: str,
        end_date: str,
        platform: Optional[str] = None,
    ) -> List[CalendarEntry]:
        """Build a calendar view of scheduled posts between two dates.

        Parameters
        ----------
        start_date:
            Start of range (``YYYY-MM-DD``).
        end_date:
            End of range (``YYYY-MM-DD``).
        platform:
            Optional platform filter.

        Returns
        -------
        list[CalendarEntry]
            Sorted by date then time.
        """
        entries: List[CalendarEntry] = []
        with self._lock:
            for post in self._queue.values():
                # Platform filter
                if platform is not None and post.platform != platform:
                    continue

                # Must have a scheduled time
                if post.scheduled_time is None:
                    continue

                try:
                    dt = parse_iso_timestamp(post.scheduled_time)
                except (ValueError, TypeError):
                    continue

                post_date = dt.strftime("%Y-%m-%d")

                # Date range check
                if post_date < start_date or post_date > end_date:
                    continue

                entry = CalendarEntry(
                    date=post_date,
                    time=dt.strftime("%H:%M"),
                    platform=post.platform,
                    post_id=post.id,
                    content_preview=post.content_text[:100],
                    content_type=post.content_type,
                    status=post.status,
                    media_count=len(post.media_refs),
                )
                entries.append(entry)

        # Sort by date, then time
        entries.sort(key=lambda e: (e.date, e.time))
        return entries

    # ------------------------------------------------------------------
    # Conflict detection
    # ------------------------------------------------------------------

    def check_conflicts(self, post: QueuedPost) -> List[str]:
        """Check for scheduling conflicts with the given post.

        Detects:
        (a) Another post on the same platform within ``min_gap_minutes``.
        (b) ``max_posts_per_day`` exceeded for the platform.
        (c) Posting during ``no_post_hours``.
        (d) Posting on ``no_post_days``.

        Returns a list of human-readable conflict descriptions.  An empty
        list means no conflicts.
        """
        conflicts: List[str] = []

        if post.scheduled_time is None:
            return conflicts

        try:
            post_dt = parse_iso_timestamp(post.scheduled_time)
        except (ValueError, TypeError):
            conflicts.append(f"Invalid scheduled_time format: {post.scheduled_time}")
            return conflicts

        rules = self._rules.get(post.platform)
        if rules is None:
            # No rules defined -- no conflict checking possible
            return conflicts

        # (c) Check no_post_hours
        if post_dt.hour in rules.no_post_hours:
            conflicts.append(
                f"Scheduled at hour {post_dt.hour:02d}, which is in no_post_hours "
                f"for {post.platform}"
            )

        # (d) Check no_post_days
        day_name = post_dt.strftime("%A").lower()
        if day_name in [d.lower() for d in rules.no_post_days]:
            conflicts.append(
                f"Scheduled on {day_name}, which is in no_post_days "
                f"for {post.platform}"
            )

        # (b) Check max_posts_per_day
        post_date = post_dt.strftime("%Y-%m-%d")
        # Count existing posts on that date (exclude the post itself)
        existing_count = 0
        with self._lock:
            for other in self._queue.values():
                if other.id == post.id:
                    continue
                if other.platform != post.platform:
                    continue
                if other.status in ("cancelled", "rejected", "failed"):
                    continue
                if other.scheduled_time is None:
                    continue
                try:
                    other_dt = parse_iso_timestamp(other.scheduled_time)
                    if other_dt.strftime("%Y-%m-%d") == post_date:
                        existing_count += 1
                except (ValueError, TypeError):
                    continue

        # +1 for the new post
        if existing_count + 1 > rules.max_posts_per_day:
            conflicts.append(
                f"Would exceed max_posts_per_day ({rules.max_posts_per_day}) "
                f"for {post.platform} on {post_date} "
                f"({existing_count} existing + this post)"
            )

        # (a) Check min_gap_minutes
        with self._lock:
            for other in self._queue.values():
                if other.id == post.id:
                    continue
                if other.platform != post.platform:
                    continue
                if other.status in ("cancelled", "rejected", "failed"):
                    continue
                if other.scheduled_time is None:
                    continue
                try:
                    other_dt = parse_iso_timestamp(other.scheduled_time)
                    gap = abs((post_dt - other_dt).total_seconds()) / 60.0
                    if gap < rules.min_gap_minutes:
                        conflicts.append(
                            f"Only {gap:.0f} min from post {other.id} "
                            f"(min gap is {rules.min_gap_minutes} min for {post.platform})"
                        )
                except (ValueError, TypeError):
                    continue

        # Holiday check
        if rules.respect_holidays and post_date in rules.holiday_list:
            conflicts.append(
                f"Scheduled on holiday {post_date} for {post.platform}"
            )

        return conflicts

    # ------------------------------------------------------------------
    # Content similarity
    # ------------------------------------------------------------------

    def check_similarity(
        self, post: QueuedPost, threshold: float = 0.7
    ) -> List[ContentSimilarityCheck]:
        """Check if *post* is too similar to other queued/recent posts.

        Uses simple word overlap as a heuristic:

            similarity = len(words_a & words_b) / max(len(words_a), len(words_b))

        Returns a list of ``ContentSimilarityCheck`` objects where the
        score exceeds *threshold*.
        """
        results: List[ContentSimilarityCheck] = []
        post_words = self._extract_words(post.content_text)
        if not post_words:
            return results

        with self._lock:
            for other in self._queue.values():
                if other.id == post.id:
                    continue
                # Only compare against active posts on the same platform
                if other.platform != post.platform:
                    continue
                if other.status in ("cancelled", "rejected"):
                    continue

                other_words = self._extract_words(other.content_text)
                if not other_words:
                    continue

                overlap = len(post_words & other_words)
                max_len = max(len(post_words), len(other_words))
                score = overlap / max_len

                if score <= threshold:
                    continue

                # Classify similarity type
                if score >= 1.0:
                    sim_type = "exact_duplicate"
                elif score >= 0.9:
                    sim_type = "near_duplicate"
                elif score > threshold:
                    sim_type = "similar_topic"
                else:
                    sim_type = "different"

                # Compute time gap
                time_gap = 0.0
                if post.scheduled_time and other.scheduled_time:
                    try:
                        dt_a = parse_iso_timestamp(post.scheduled_time)
                        dt_b = parse_iso_timestamp(other.scheduled_time)
                        time_gap = abs((dt_a - dt_b).total_seconds()) / 3600.0
                    except (ValueError, TypeError):
                        pass

                check = ContentSimilarityCheck(
                    post_a_id=post.id,
                    post_b_id=other.id,
                    similarity_score=round(score, 4),
                    similarity_type=sim_type,
                    time_gap_hours=round(time_gap, 2),
                )
                results.append(check)

        # Sort by similarity descending
        results.sort(key=lambda c: c.similarity_score, reverse=True)
        return results

    @staticmethod
    def _extract_words(text: str) -> Set[str]:
        """Extract a set of lowercased alphanumeric words from *text*."""
        return set(re.findall(r"[a-z0-9]+", text.lower()))

    # ------------------------------------------------------------------
    # Optimal time suggestion
    # ------------------------------------------------------------------

    def suggest_optimal_time(self, platform: str, preferred_date: str) -> str:
        """Suggest the best available time slot for *platform* on *preferred_date*.

        Walks through the platform's ``optimal_posting_times`` for the
        day of the week, finds the first hour that does not conflict with
        existing posts or scheduling rules, and returns an ISO timestamp.

        If no optimal slot is conflict-free, falls back to the first
        allowed hour with no conflicts.

        Returns an ISO-8601 timestamp string.
        """
        rules = self._rules.get(platform)
        if rules is None:
            # No rules -- default to noon
            return f"{preferred_date}T12:00:00"

        # Parse the preferred date
        try:
            date_obj = datetime.strptime(preferred_date, "%Y-%m-%d")
        except ValueError:
            return f"{preferred_date}T12:00:00"

        day_name = date_obj.strftime("%A").lower()

        # Gather optimal hours for this day
        optimal_hours: List[int] = []
        for entry in rules.optimal_posting_times:
            if entry.get("day", "").lower() == day_name:
                optimal_hours = list(entry.get("hours", []))
                break

        # Build a set of hours already occupied by posts on this date
        occupied_hours: Set[int] = set()
        with self._lock:
            for post in self._queue.values():
                if post.platform != platform:
                    continue
                if post.status in ("cancelled", "rejected", "failed"):
                    continue
                if post.scheduled_time is None:
                    continue
                try:
                    post_dt = parse_iso_timestamp(post.scheduled_time)
                    if post_dt.strftime("%Y-%m-%d") == preferred_date:
                        # Mark the hour and hours within the min_gap as occupied
                        gap_hours = max(1, rules.min_gap_minutes // 60)
                        for h in range(
                            max(0, post_dt.hour - gap_hours),
                            min(24, post_dt.hour + gap_hours + 1),
                        ):
                            occupied_hours.add(h)
                except (ValueError, TypeError):
                    continue

        no_post_hours = set(rules.no_post_hours)

        # Try optimal hours first
        for hour in optimal_hours:
            if hour in no_post_hours:
                continue
            if hour in occupied_hours:
                continue
            return f"{preferred_date}T{hour:02d}:00:00"

        # Fallback: try every allowed hour
        for hour in range(24):
            if hour in no_post_hours:
                continue
            if hour in occupied_hours:
                continue
            return f"{preferred_date}T{hour:02d}:00:00"

        # Absolute fallback: everything is occupied -- pick first optimal hour anyway
        if optimal_hours:
            hour = optimal_hours[0]
            return f"{preferred_date}T{hour:02d}:00:00"

        return f"{preferred_date}T12:00:00"


# ============================================================================
# ApprovalQueue
# ============================================================================


class ApprovalQueue:
    """Manages the approval workflow for social posts.

    Provides pending/approved/rejected tracking, auto-approve eligibility
    checks, and batch approval support.
    """

    def __init__(self) -> None:
        self._requests: Dict[str, ApprovalRequest] = {}
        self._approved_urls: Set[str] = set()
        self._approved_templates: Set[str] = set()
        self._lock = threading.RLock()

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def get_pending(self) -> List[ApprovalRequest]:
        """Return all pending approval requests, sorted oldest-first."""
        with self._lock:
            pending = [
                ar for ar in self._requests.values() if ar.status == "pending"
            ]
        pending.sort(key=lambda ar: ar.requested_at)
        return pending

    def get_auto_approve_candidates(self) -> List[ApprovalRequest]:
        """Return pending requests where ``auto_approve_eligible`` is True."""
        with self._lock:
            return [
                ar
                for ar in self._requests.values()
                if ar.status == "pending" and ar.auto_approve_eligible
            ]

    # ------------------------------------------------------------------
    # Review actions
    # ------------------------------------------------------------------

    def approve(
        self,
        approval_id: str,
        reviewed_by: str,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        """Approve an approval request.

        Raises ``ValueError`` if the request is not found.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            ar = self._requests.get(approval_id)
            if ar is None:
                raise ValueError(f"Approval request {approval_id} not found")

            ar.status = "approved"
            ar.reviewed_at = now
            ar.reviewed_by = reviewed_by
            ar.review_notes = notes
            self._requests[approval_id] = ar

        logger.info(
            "Approved request %s by %s (post %s)", approval_id, reviewed_by, ar.post_id
        )
        return ar

    def reject(
        self,
        approval_id: str,
        reviewed_by: str,
        notes: Optional[str] = None,
    ) -> ApprovalRequest:
        """Reject an approval request.

        Raises ``ValueError`` if the request is not found.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._lock:
            ar = self._requests.get(approval_id)
            if ar is None:
                raise ValueError(f"Approval request {approval_id} not found")

            ar.status = "rejected"
            ar.reviewed_at = now
            ar.reviewed_by = reviewed_by
            ar.review_notes = notes
            self._requests[approval_id] = ar

        logger.info(
            "Rejected request %s by %s (post %s)", approval_id, reviewed_by, ar.post_id
        )
        return ar

    # ------------------------------------------------------------------
    # Auto-approve eligibility
    # ------------------------------------------------------------------

    def auto_approve_eligible(self, post: QueuedPost) -> bool:
        """Determine if *post* qualifies for automatic approval.

        A post is auto-approve eligible when ALL of the following hold:

        1. ``content_type`` is not ``"offer_post"`` (offers always require
           manual review).
        2. Any ``link_url`` on the post has been previously approved (is in
           ``_approved_urls``), or the post has no link.
        3. The post was generated from a pre-approved template (its
           ``metadata`` contains a ``template_id`` that appears in
           ``_approved_templates``), or no template tracking is in use.
        4. The post's ``metadata`` indicates it has passed quality gates
           (``metadata.get("quality_gates_passed")`` is truthy).
        """
        # Criterion 1: offers always need review
        if post.content_type == "offer_post":
            return False

        # Criterion 2: link URL must be previously approved (if present)
        if post.link_url is not None:
            with self._lock:
                if post.link_url not in self._approved_urls:
                    return False

        # Criterion 3: template must be pre-approved (if template_id present)
        template_id = (
            post.metadata.get("template_id") if isinstance(post.metadata, dict) else None
        )
        if template_id is not None:
            with self._lock:
                if template_id not in self._approved_templates:
                    return False

        # Criterion 4: quality gates must have passed
        quality_passed = (
            post.metadata.get("quality_gates_passed")
            if isinstance(post.metadata, dict)
            else False
        )
        if not quality_passed:
            return False

        return True

    # ------------------------------------------------------------------
    # Administrative helpers
    # ------------------------------------------------------------------

    def add_request(self, request: ApprovalRequest) -> ApprovalRequest:
        """Register an ``ApprovalRequest`` in this queue."""
        with self._lock:
            self._requests[request.id] = request
        return request

    def add_approved_url(self, url: str) -> None:
        """Mark a URL as previously approved for auto-approve checks."""
        with self._lock:
            self._approved_urls.add(url)

    def add_approved_template(self, template_id: str) -> None:
        """Mark a template as pre-approved for auto-approve checks."""
        with self._lock:
            self._approved_templates.add(template_id)


# ============================================================================
# Module exports
# ============================================================================

__all__ = [
    # Enums
    "PostStatus",
    # Models
    "QueuedPost",
    "SchedulingRules",
    "ApprovalRequest",
    "CalendarEntry",
    "ContentSimilarityCheck",
    # Defaults
    "DEFAULT_SCHEDULING_RULES",
    # Classes
    "PostQueue",
    "ApprovalQueue",
    # Helpers
    "generate_queue_id",
    "generate_approval_id",
    "is_within_posting_hours",
    "count_posts_on_date",
    "parse_iso_timestamp",
]
