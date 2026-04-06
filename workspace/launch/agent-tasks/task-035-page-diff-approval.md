# Task 035: Build page diff preview and approval workflow

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 6. Website Operations
**Priority:** P2
**Depends on:** 034
**Estimated complexity:** Medium

## Context

No website change should go live without the operator seeing exactly what will change and explicitly approving it (or the system auto-approving based on pre-configured risk tolerance). The diff preview and approval workflow sits between the action system and actual execution. When an action is proposed, it generates a visual diff showing before and after states. The approval system then decides whether the change can be auto-approved or needs human review, routes it accordingly, and tracks the approval through its full lifecycle.

This is the safety net that prevents Kai from making unwanted changes to live websites. It must be conservative by default (require human approval for anything visible) while allowing operators to speed up workflows by enabling auto-approval for low-risk changes.

## Scope

Build `kai/actions/approval.py` containing the DiffPreview and ApprovalRequest models, the approval workflow logic, auto-approve rule evaluation, and the revision workflow for rejected changes.

## Detailed Requirements

### File: `kai/actions/approval.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: ApprovalStatus**
- `pending` — awaiting review
- `approved` — operator approved
- `auto_approved` — system auto-approved based on rules
- `rejected` — operator rejected
- `revision_requested` — operator wants changes before approving
- `expired` — approval request timed out without a decision

**Model: DiffPreview**
- `id: str` — unique identifier, format `diff_{uuid_hex[:12]}`
- `action_id: str` — links to the website action
- `page_id: str` — which page is being changed
- `page_url: Optional[str]` — live URL of the page
- `page_title: Optional[str]` — title of the page being changed
- `before_content: str` — content before the change
- `after_content: str` — content after the change
- `diff_html: str` — HTML-formatted diff with additions highlighted in green and removals in red
- `diff_text: str` — plain text diff (unified diff format)
- `change_summary: str` — human-readable summary of what changed, e.g., "Updated hero headline from 'Welcome' to 'Get Your Free Quote in 60 Seconds'"
- `change_type: str` — "copy_update", "section_addition", "section_removal", "section_reorder", "metadata_update", "tracking_update", "cta_update"
- `lines_added: int` — number of lines added
- `lines_removed: int` — number of lines removed
- `lines_modified: int` — number of lines modified
- `risk_assessment: Dict[str, Any]` — structured risk assessment:
  ```python
  {
      "risk_tier": str,           # "auto", "low", "medium", "high", "critical"
      "risk_factors": List[str],  # specific risk factors identified
      "is_homepage": bool,        # homepage changes are higher risk
      "is_public_facing": bool,   # visible to end users
      "affects_seo": bool,        # changes meta tags, headings, schema
      "affects_tracking": bool,   # changes analytics/tracking code
      "affects_conversion": bool, # changes CTAs, forms, phone numbers
      "word_count_change": int,   # positive = added words, negative = removed
  }
  ```
- `created_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Model: ApprovalRequest**
- `id: str` — unique identifier, format `apr_{uuid_hex[:12]}`
- `action_id: str` — links to the website action
- `diff_preview_id: str` — links to the DiffPreview
- `diff_preview: Optional[Dict[str, Any]]` — the DiffPreview dict (embedded for convenience)
- `risk_tier: str` — from the diff's risk_assessment
- `auto_approve_eligible: bool` — whether this change qualifies for auto-approval
- `auto_approve_reason: Optional[str]` — if auto-approvable, why
- `status: str` — ApprovalStatus value, default "pending"
- `operator_notes: Optional[str]` — notes from the operator (on approval or rejection)
- `revision_instructions: Optional[str]` — if status is "revision_requested", what to change
- `approved_by: Optional[str]` — who approved (or "system" for auto-approval)
- `decided_at: Optional[str]` — ISO timestamp of the decision
- `expires_at: Optional[str]` — ISO timestamp after which this request expires
- `created_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Function: `generate_diff_preview(action: Dict[str, Any], before_content: str, after_content: str, page_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`**
- Generate a DiffPreview dict from action data and before/after content
- Use Python's `difflib` to generate:
  - `diff_text`: unified diff format
  - `diff_html`: wrap additions in `<ins>` tags, deletions in `<del>` tags (use `difflib.HtmlDiff` or custom markup)
- Count lines added, removed, modified
- Generate change_summary from action metadata (action type, target, reason)
- Assess risk:
  - Check if page_id indicates homepage (slug "/", "home", "index")
  - Check if changes affect `<head>` (SEO impact)
  - Check if changes affect forms, phone numbers, CTAs (conversion impact)
  - Check if changes add/remove tracking code (analytics impact)
  - Assign risk_tier based on combined factors
- Return DiffPreview dict

**Function: `assess_risk(diff_preview: Dict[str, Any], page_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]`**
- Evaluate the risk of a proposed change:
  - `is_homepage`: True if page slug is "/", "home", "index", or page is marked as front page
  - `is_public_facing`: True unless change_type is "tracking_update" or "metadata_update" only
  - `affects_seo`: True if changes touch `<title>`, `<meta>`, `<h1>`, `<h2>`, schema markup, or canonical URL
  - `affects_tracking`: True if changes touch `<script>` tags, data-layer, or tracking pixels
  - `affects_conversion`: True if changes touch `<form>`, `<a>` with CTA classes, phone numbers, or pricing
  - `word_count_change`: count words in after vs before content
  - `risk_tier` assignment:
    - "auto" if not public-facing AND not conversion-affecting (e.g., internal metadata only)
    - "low" if small change (< 50 words changed), not homepage, not conversion-affecting
    - "medium" if medium change (50-200 words) or affects SEO but not homepage
    - "high" if homepage change, large change (> 200 words), or affects conversion elements
    - "critical" if homepage hero/CTA change, or change affects multiple conversion elements
  - `risk_factors`: list of specific concerns, e.g., ["Homepage change", "CTA text modified", "Phone number changed"]
- Return risk assessment dict

**Function: `evaluate_auto_approval(approval_request: Dict[str, Any], auto_approve_settings: Dict[str, Any]) -> Dict[str, Any]`**
- Determine if an approval request can be auto-approved
- `auto_approve_settings` structure:
  ```python
  {
      "enabled": bool,              # master switch for auto-approval
      "max_risk_tier": str,         # highest risk tier to auto-approve ("auto", "low", "medium")
      "allowed_change_types": List[str],  # change types that can be auto-approved
      "require_preview": bool,      # whether preview must be generated before auto-approval
      "max_word_count_change": int, # maximum word count change for auto-approval
      "blocked_pages": List[str],   # page IDs/slugs that can never be auto-approved
  }
  ```
- Auto-approval rules:
  1. `enabled` must be True
  2. `risk_tier` must be <= `max_risk_tier` (auto < low < medium < high < critical)
  3. `change_type` must be in `allowed_change_types`
  4. Page must not be in `blocked_pages`
  5. `word_count_change` (absolute) must be <= `max_word_count_change`
- If all rules pass: set `auto_approve_eligible` to True, set `auto_approve_reason` explaining which rules were satisfied
- If any rule fails: set `auto_approve_eligible` to False, set `auto_approve_reason` explaining which rule blocked it
- Return updated approval_request dict

**Function: `create_approval_request(action: Dict[str, Any], diff_preview: Dict[str, Any], auto_approve_settings: Optional[Dict[str, Any]] = None, expiry_hours: int = 72) -> Dict[str, Any]`**
- Create an ApprovalRequest from an action and its diff preview
- If auto_approve_settings provided, evaluate auto-approval eligibility
- If auto-approvable, set status to "auto_approved" and approved_by to "system"
- If not, set status to "pending" and calculate expires_at
- Return ApprovalRequest dict

**Function: `approve_request(request: Dict[str, Any], approved_by: str, notes: Optional[str] = None) -> Dict[str, Any]`**
- Set status to "approved"
- Set approved_by, operator_notes, decided_at
- Return updated request dict
- Raise error if request is not in "pending" status

**Function: `reject_request(request: Dict[str, Any], rejected_by: str, notes: str) -> Dict[str, Any]`**
- Set status to "rejected"
- Set approved_by (rejected_by), operator_notes, decided_at
- Notes are required for rejection (must explain why)
- Return updated request dict

**Function: `request_revision(request: Dict[str, Any], revision_instructions: str) -> Dict[str, Any]`**
- Set status to "revision_requested"
- Set revision_instructions
- Return updated request dict

**Function: `process_revision(request: Dict[str, Any], revised_action: Dict[str, Any], revised_before: str, revised_after: str) -> Dict[str, Any]`**
- After a revision, generate a new diff preview and create a new approval request
- Link the new request to the original via metadata
- Return new ApprovalRequest dict

**Function: `get_pending_approvals(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]`**
- Filter and return only requests with status "pending"
- Sort by risk_tier (highest risk first) then by created_at (oldest first)
- Return filtered list

**Function: `check_expired(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]`**
- Check each request's expires_at against current time
- Mark expired requests with status "expired"
- Return list of newly expired requests

**Default auto-approve settings:**
```python
DEFAULT_AUTO_APPROVE_SETTINGS = {
    "enabled": False,  # Conservative default: require human approval
    "max_risk_tier": "low",
    "allowed_change_types": ["metadata_update", "tracking_update"],
    "require_preview": True,
    "max_word_count_change": 50,
    "blocked_pages": [],  # No specific pages blocked by default
}
```

## Output Files

- `kai/actions/approval.py`

## Acceptance Criteria

- [ ] `approval.py` contains ApprovalStatus enum with all 6 status values
- [ ] DiffPreview model has all specified fields including structured risk_assessment
- [ ] ApprovalRequest model has all specified fields with correct defaults
- [ ] generate_diff_preview produces both HTML and text diffs using difflib
- [ ] assess_risk correctly identifies homepage, SEO, tracking, and conversion impacts
- [ ] Risk tier assignment follows the specified rules (auto/low/medium/high/critical)
- [ ] evaluate_auto_approval checks all 5 rules and explains pass/fail reasons
- [ ] create_approval_request auto-approves eligible changes and sets expiry for others
- [ ] approve_request, reject_request, request_revision enforce correct state transitions
- [ ] process_revision creates a new diff preview and approval request linked to the original
- [ ] get_pending_approvals sorts by risk tier (highest first) then age (oldest first)
- [ ] check_expired marks timed-out requests as expired
- [ ] DEFAULT_AUTO_APPROVE_SETTINGS is conservative (disabled by default)
- [ ] Rejection requires notes (cannot reject without explanation)
- [ ] All functions are pure — no external I/O

## Reference Materials

- `kai/actions/base.py` (created by Task 034) — Action class with validate/preview/execute/verify lifecycle
- `kai/actions/website.py` (created by Task 034) — website action types that produce diffs
- `kai/models/proposal.py` (created by Task 022) — ProposedAction with risk_tier and approval_requirement
- Python `difflib` module — for diff generation (unified_diff, HtmlDiff)
- `gateway/models.py` — Pydantic import fallback pattern
