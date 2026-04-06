# Task 041: Build social scheduling, queue, and approval management

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 7. Social Operations
**Priority:** P2
**Depends on:** 039
**Estimated complexity:** Medium

## Context

With social connectors in place (Task 039), the system needs a scheduling and queue layer that manages when posts go out, enforces frequency limits, and routes posts through approval before publishing. This is the operational control plane for social publishing — it prevents posting too frequently, handles scheduling conflicts, manages operator review workflows, and provides a calendar view of planned content. Tasks 042 (caption engine) and 043 (proof-of-life) both depend on this scheduler to actually queue and publish content.

## Scope

Create `kai/social/scheduler.py` containing the PostQueue, SchedulingRules, ApprovalQueue, and all supporting models and management functions for social content scheduling.

## Detailed Requirements

### File: `kai/social/scheduler.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: PostStatus (str, Enum)**
- `draft` — created but not ready for review
- `pending_approval` — submitted for operator review
- `approved` — approved by operator, ready to schedule
- `scheduled` — confirmed scheduled for a specific time
- `publishing` — currently being published (in-flight)
- `published` — successfully published to platform
- `failed` — publication failed (see error details)
- `cancelled` — cancelled before publishing
- `rejected` — rejected by operator during approval

**Model: QueuedPost**
- `id: str` — unique queue ID, format `qp_{uuid_hex[:12]}`
- `platform: str` — target platform (instagram, facebook, linkedin, tiktok, x_twitter, youtube)
- `content_type: Optional[str]` — SocialContentType value from Task 040, if applicable
- `content_text: str` — the full caption/post text
- `media_refs: List[str]` — list of media URLs or asset IDs, default empty list
- `media_type: Optional[str]` — "image", "video", "carousel", "reel", "story", "short"
- `hashtags: List[str]` — hashtags to include, default empty list
- `location_tag: Optional[str]` — geo-tag identifier
- `link_url: Optional[str]` — URL to include if platform supports it
- `scheduled_time: Optional[str]` — ISO timestamp for when to publish
- `status: str` — PostStatus value, default "draft"
- `priority: int` — queue priority (lower = higher priority), default 100
- `created_at: str` — ISO timestamp
- `updated_at: str` — ISO timestamp
- `approved_at: Optional[str]` — ISO timestamp when approved
- `approved_by: Optional[str]` — who approved (operator ID or "auto")
- `published_at: Optional[str]` — ISO timestamp when actually published
- `published_url: Optional[str]` — URL of the live post
- `error_message: Optional[str]` — error details if failed
- `retry_count: int = 0` — how many times publication has been attempted
- `max_retries: int = 3` — maximum retry attempts
- `source_action_id: Optional[str]` — link to ProposedAction if this post came from the proposal system
- `tags: List[str]` — freeform tags for filtering, default empty list
- `metadata: Dict[str, Any]` — default empty dict

**Model: SchedulingRules**
- `platform: str` — which platform these rules apply to
- `optimal_posting_times: List[Dict[str, Any]]` — list of {day_of_week: str, hours: List[int]} representing best times to post. Example: [{"day": "monday", "hours": [9, 12, 17]}, {"day": "tuesday", "hours": [9, 12, 17]}]
- `max_posts_per_day: int` — hard cap on posts per day for this platform
- `recommended_posts_per_day: float` — ideal posting frequency
- `min_gap_minutes: int` — minimum minutes between posts on same platform, default 120 (2 hours)
- `no_post_days: List[str]` — days of the week to never post (e.g., ["sunday"] for B2B LinkedIn), default empty list
- `no_post_hours: List[int]` — hours of the day (0-23) to never post (e.g., [0, 1, 2, 3, 4, 5] for overnight), default empty list
- `timezone: str` — IANA timezone string, default "America/New_York"
- `respect_holidays: bool = True` — skip posting on major holidays
- `holiday_list: List[str]` — list of holiday dates in YYYY-MM-DD format, default empty list (populated by system)

**Pre-built DEFAULT_SCHEDULING_RULES dict: `DEFAULT_SCHEDULING_RULES: Dict[str, SchedulingRules]`**

Define sensible defaults for each platform:

1. **Instagram**: optimal times Mon-Fri at 9am, 12pm, 5pm; max 3/day, recommended 1/day; min gap 180 min; no_post_hours 0-6
2. **Facebook**: optimal times Mon-Fri at 9am, 1pm; max 2/day, recommended 1/day; min gap 240 min; no_post_hours 0-6
3. **LinkedIn**: optimal times Mon-Fri at 8am, 12pm; max 2/day, recommended 1/day; min gap 360 min; no_post_days ["saturday", "sunday"]; no_post_hours 0-6, 20-23
4. **TikTok**: optimal times daily at 10am, 2pm, 7pm; max 3/day, recommended 1/day; min gap 120 min; no_post_hours 0-7
5. **X/Twitter**: optimal times Mon-Fri at 9am, 12pm, 5pm; max 5/day, recommended 2/day; min gap 60 min; no_post_hours 0-6
6. **YouTube**: optimal times Tue/Thu/Sat at 2pm; max 2/day (Shorts), recommended 0.3/day (long-form) or 1/day (Shorts); min gap 240 min; no_post_hours 0-8

**Model: ApprovalRequest**
- `id: str` — format `apr_{uuid_hex[:12]}`
- `post_id: str` — ID of the QueuedPost needing approval
- `requested_at: str` — ISO timestamp
- `requested_by: str` — who/what triggered the approval request (e.g., "system", "scheduler", operator ID)
- `reason: str` — why approval is needed (e.g., "New content type", "First post on platform", "Contains offer/promotion")
- `status: str` — "pending", "approved", "rejected", default "pending"
- `reviewed_at: Optional[str]`
- `reviewed_by: Optional[str]`
- `review_notes: Optional[str]` — operator's notes on the approval/rejection
- `auto_approve_eligible: bool = False` — whether this post could be auto-approved based on rules

**Model: CalendarEntry**
- `date: str` — YYYY-MM-DD
- `time: str` — HH:MM (24hr)
- `platform: str`
- `post_id: str`
- `content_preview: str` — first 100 characters of content text
- `content_type: Optional[str]`
- `status: str`
- `media_count: int`

**Model: ContentSimilarityCheck**
- `post_a_id: str`
- `post_b_id: str`
- `similarity_score: float` — 0.0 to 1.0
- `similarity_type: str` — "exact_duplicate", "near_duplicate", "similar_topic", "different"
- `time_gap_hours: float` — hours between the two posts' scheduled times

**Class: PostQueue**

Manages the queue of posts across all platforms.

Methods:
- `__init__(self, rules: Optional[Dict[str, SchedulingRules]] = None)` — initialize with scheduling rules (default to DEFAULT_SCHEDULING_RULES)
- `add_post(self, post: QueuedPost) -> QueuedPost` — add a post to the queue. Validate against scheduling rules. Return the post with assigned `id` and `created_at`.
- `remove_post(self, post_id: str) -> bool` — remove a post from the queue. Only allowed if status is "draft", "pending_approval", "approved", or "scheduled". Return True if removed.
- `update_post(self, post_id: str, updates: Dict[str, Any]) -> QueuedPost` — update fields on a queued post. Only allowed if status is "draft" or "pending_approval" (content editable) or "approved"/"scheduled" (only schedule changes).
- `reschedule_post(self, post_id: str, new_time: str) -> QueuedPost` — change scheduled time. Validate against scheduling rules. Return updated post.
- `reorder_queue(self, platform: str, post_ids: List[str]) -> List[QueuedPost]` — reorder posts for a platform by setting priority based on position in the list.
- `get_queue(self, platform: Optional[str] = None, status: Optional[str] = None, date_from: Optional[str] = None, date_to: Optional[str] = None) -> List[QueuedPost]` — fetch queue with optional filters. Return sorted by scheduled_time.
- `get_next_post(self, platform: str) -> Optional[QueuedPost]` — return the next post that should be published for a platform (status "scheduled" with earliest scheduled_time in the past or now).
- `bulk_approve(self, post_ids: List[str], approved_by: str = "operator") -> List[QueuedPost]` — approve multiple posts at once. Update status to "approved", set approved_at and approved_by.
- `submit_for_approval(self, post_id: str, reason: str = "Standard review") -> ApprovalRequest` — change post status to "pending_approval" and create an ApprovalRequest.
- `get_calendar_view(self, start_date: str, end_date: str, platform: Optional[str] = None) -> List[CalendarEntry]` — return a list of CalendarEntry objects for the date range, optionally filtered by platform.
- `check_conflicts(self, post: QueuedPost) -> List[str]` — check for scheduling conflicts: (a) another post on same platform within min_gap_minutes, (b) max_posts_per_day exceeded, (c) posting during no_post_hours, (d) posting on no_post_days. Return list of conflict description strings.
- `check_similarity(self, post: QueuedPost, threshold: float = 0.7) -> List[ContentSimilarityCheck]` — check if a post's content is too similar to other recent/scheduled posts. Use simple word overlap as a similarity heuristic: `len(words_a & words_b) / max(len(words_a), len(words_b))`. Return list of ContentSimilarityCheck objects where similarity_score > threshold.
- `suggest_optimal_time(self, platform: str, preferred_date: str) -> str` — given a platform and date, suggest the best available time slot based on scheduling rules and existing queue. Return ISO timestamp.

Internal state:
- `_queue: Dict[str, QueuedPost]` — post_id -> QueuedPost mapping
- `_approval_requests: Dict[str, ApprovalRequest]` — approval_id -> ApprovalRequest mapping
- `_rules: Dict[str, SchedulingRules]` — platform -> SchedulingRules mapping
- `_lock: threading.RLock` — thread safety for queue mutations

**Class: ApprovalQueue**

Manages the approval workflow for social posts.

Methods:
- `__init__(self)` — initialize internal state
- `get_pending(self) -> List[ApprovalRequest]` — return all pending approval requests, sorted by requested_at (oldest first)
- `approve(self, approval_id: str, reviewed_by: str, notes: Optional[str] = None) -> ApprovalRequest` — approve a request. Update status, reviewed_at, reviewed_by, review_notes.
- `reject(self, approval_id: str, reviewed_by: str, notes: Optional[str] = None) -> ApprovalRequest` — reject a request. Update status and related fields.
- `get_auto_approve_candidates(self) -> List[ApprovalRequest]` — return requests where auto_approve_eligible is True. These can be batch-approved without manual review.
- `auto_approve_eligible(self, post: QueuedPost) -> bool` — determine if a post qualifies for auto-approval based on rules: (a) content_type is not "offer_post" (offers always need review), (b) post does not contain URLs that haven't been approved before, (c) post has been generated from an approved template, (d) content has passed quality gates.

Internal state:
- `_requests: Dict[str, ApprovalRequest]` — approval_id -> ApprovalRequest
- `_approved_urls: Set[str]` — URLs that have been previously approved (for auto-approve checks)
- `_approved_templates: Set[str]` — template IDs that have been pre-approved

**Helper functions (module-level):**

- `generate_queue_id() -> str` — return `qp_{uuid.uuid4().hex[:12]}`
- `generate_approval_id() -> str` — return `apr_{uuid.uuid4().hex[:12]}`
- `is_within_posting_hours(timestamp: str, rules: SchedulingRules) -> bool` — check if a timestamp falls within allowed posting hours for the rules
- `count_posts_on_date(queue: Dict[str, QueuedPost], platform: str, date: str) -> int` — count how many posts are scheduled/published for a platform on a specific date
- `parse_iso_timestamp(ts: str) -> datetime` — parse ISO timestamp string (helper, using datetime.fromisoformat)

## Output Files

- `kai/social/scheduler.py`
- `kai/social/__init__.py` (update to include scheduler exports)

## Acceptance Criteria

- [ ] `PostStatus` enum has all 9 statuses listed above
- [ ] `QueuedPost` model has all 23 fields with correct types and defaults
- [ ] `SchedulingRules` model has all 11 fields with correct types and defaults
- [ ] `DEFAULT_SCHEDULING_RULES` dict has entries for all 6 platforms with sensible real-world values
- [ ] `ApprovalRequest` model has all 10 fields
- [ ] `CalendarEntry` model has all 8 fields
- [ ] `ContentSimilarityCheck` model has all 4 fields
- [ ] `PostQueue` class has all 13 methods listed above with correct signatures
- [ ] `PostQueue.check_conflicts()` catches min_gap, max_per_day, no_post_hours, and no_post_days violations
- [ ] `PostQueue.check_similarity()` implements word-overlap similarity check
- [ ] `PostQueue.suggest_optimal_time()` considers existing queue and scheduling rules
- [ ] `ApprovalQueue` class has all 6 methods listed above
- [ ] `ApprovalQueue.auto_approve_eligible()` implements the 4 criteria checks
- [ ] All 5 helper functions exist with correct signatures
- [ ] Thread safety via `_lock` on all mutating PostQueue methods
- [ ] ID generators use the `qp_` and `apr_` prefixes
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] No external dependencies beyond standard library + Pydantic

## Reference Materials

- `kai/connectors/social/base.py` (created by Task 039) — SocialPost model, connector interface
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `kai/runtime/actions.py` — ActionStore patterns for file-backed state and thread safety (lines 80-150)
- `kai/social/content_types.py` (created by Task 040) — SocialContentType and SocialPlatform enums
- `knowledge/playbooks/social-media-strategy.md` — social posting strategy guidance
- `CLAUDE.md` — full project context
