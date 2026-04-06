# Task 034: Build website action system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 6. Website Operations
**Priority:** P1
**Depends on:** 033
**Estimated complexity:** Large

## Context

ProposedActions of type "website_update" and "seo_fix" describe what should change on a website — but they need to be translated into concrete, executable operations that interact with the CMS connector layer. The website action system defines specific action types as classes with a standard lifecycle: validate (check that the target exists and the action is safe), preview (generate a diff showing what would change), execute (apply the change via CMS connector), and verify (confirm the change took effect). This four-phase lifecycle ensures no change happens without being validated and previewable first.

Each action type inherits from a base Action class and implements its own validation, preview, and execution logic.

## Scope

Build `kai/actions/base.py` with the abstract Action class, and `kai/actions/website.py` with all concrete website action types. Also create `kai/actions/__init__.py`.

## Detailed Requirements

### File: `kai/actions/__init__.py`
- Package init that imports and re-exports the base class and all website action classes
- Include `__all__` listing

### File: `kai/actions/base.py`

**Enum: ActionLifecycleState**
- `created` — action instantiated but not validated
- `validated` — validation passed, ready for preview
- `previewed` — preview generated, ready for approval
- `approved` — approved for execution
- `executing` — execution in progress
- `completed` — execution completed successfully
- `failed` — execution failed
- `rolled_back` — action was rolled back after execution
- `cancelled` — action was cancelled before execution

**Model: ActionResult**
- `success: bool`
- `action_id: str`
- `state: str` — ActionLifecycleState value
- `message: str` — human-readable result message
- `before_state: Optional[Dict[str, Any]]` — state before execution (for rollback)
- `after_state: Optional[Dict[str, Any]]` — state after execution
- `errors: List[str]` — error messages if failed, default empty list
- `warnings: List[str]` — warning messages, default empty list
- `timestamp: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Abstract class: Action**
- `__init__(self, action_id: str, source_proposal_id: str, reason: str, connector: Optional[Any] = None)`
  - `action_id` — unique identifier
  - `source_proposal_id` — links back to ProposedAction
  - `reason` — why this action is being taken (from ProposedAction.reason)
  - `connector` — CMS connector instance (passed at execution time, not required at creation)
  - `state` — ActionLifecycleState, starts as "created"
  - `created_at` — ISO timestamp of creation
  - `_before_snapshot` — stored before-state for rollback
  - `_preview_result` — stored preview result

Abstract methods:

1. `validate(self) -> ActionResult`
   - Check that all required parameters are present and valid
   - Check that the target (page, section, etc.) exists via connector
   - Check that the action is safe (no destructive changes without explicit intent)
   - Update state to "validated" if passed
   - Return ActionResult with success=True/False

2. `preview(self) -> ActionResult`
   - Generate a diff or description of what would change
   - Take a before_snapshot if connector is available
   - Update state to "previewed" if successful
   - Return ActionResult with before_state and a preview in metadata

3. `execute(self) -> ActionResult`
   - Apply the change via CMS connector
   - Must be in "approved" state to execute (raise error otherwise)
   - Store before_state for rollback
   - Update state to "completed" or "failed"
   - Return ActionResult with before_state and after_state

4. `verify(self) -> ActionResult`
   - After execution, verify the change was applied correctly
   - Read the target back via connector and compare with expected state
   - Return ActionResult indicating verification success/failure

Non-abstract methods:

5. `approve(self) -> None`
   - Set state to "approved" (can only be called when state is "previewed")
   - Raises error if state is not "previewed"

6. `cancel(self) -> None`
   - Set state to "cancelled" (can be called in any state before "executing")

7. `rollback(self) -> ActionResult`
   - Restore before_state via connector
   - Can only be called when state is "completed"
   - Update state to "rolled_back"
   - Return ActionResult

8. `to_dict(self) -> Dict[str, Any]`
   - Serialize the action to a dict for storage/logging

### File: `kai/actions/website.py`

All website actions inherit from Action. Each defines its own parameters, validation, preview, and execution logic.

**Class: UpdatePageCopy(Action)**
- Constructor params: `page_id: str, section_id: str, new_copy: str, reason: str`
- `validate()`: check page_id exists via connector.get_page(), check section_id exists in page sections
- `preview()`: get current section content, generate diff with new_copy
- `execute()`: call connector.update_page_section(page_id, section_id, new_copy)
- `verify()`: re-read page, confirm section content matches new_copy

**Class: UpdatePageSection(Action)**
- Constructor params: `page_id: str, section_id: str, new_html: str, reason: str`
- Similar to UpdatePageCopy but for full HTML section replacement
- `validate()`: check page_id and section_id exist, validate new_html is not empty
- `preview()`: diff of old HTML vs new HTML
- `execute()`: call connector.update_page_section(page_id, section_id, new_html, content_type="html")
- `verify()`: re-read and confirm

**Class: UpdateCTA(Action)**
- Constructor params: `page_id: str, cta_location: str, new_cta_text: str, new_cta_url: Optional[str], reason: str`
- `cta_location`: "header", "hero", "body", "footer", "sticky_bar", "popup"
- `validate()`: check page exists, check CTA location is valid
- `preview()`: show old CTA text/URL vs new
- `execute()`: locate CTA element in page content, update text and URL
- `verify()`: confirm CTA text and URL are updated

**Class: UpdateMetadata(Action)**
- Constructor params: `page_id: str, title: Optional[str], description: Optional[str], schema_markup: Optional[Dict], reason: str`
- `validate()`: check page exists, validate title length (< 60 chars), description length (< 160 chars)
- `preview()`: show old metadata vs new metadata
- `execute()`: call connector.update_metadata(page_id, meta_dict)
- `verify()`: re-read metadata and confirm updates

**Class: FixTracking(Action)**
- Constructor params: `page_id: str, tracking_type: str, tracking_config: Dict[str, Any], reason: str`
- `tracking_type`: "ga4", "gtm", "meta_pixel", "google_ads_conversion", "call_tracking", "hotjar", "custom"
- `tracking_config`: varies by type, e.g., `{"measurement_id": "G-XXXXX"}` for GA4
- `validate()`: check page exists, validate tracking_config has required fields for the type
- `preview()`: show what tracking code/snippet will be added
- `execute()`: inject tracking snippet into page head or body
- `verify()`: check that tracking code is present in page source

**Class: RefreshApprovedSection(Action)**
- Constructor params: `page_id: str, section_id: str, approved_block_id: str, reason: str`
- Uses an ApprovedMessageBlock from the creative library to replace a section
- `validate()`: check page and section exist, check approved_block_id is valid
- `preview()`: show current section vs approved block content
- `execute()`: replace section content with approved block content
- `verify()`: confirm section matches approved block

**Class: RestructurePage(Action)**
- Constructor params: `page_id: str, new_section_order: List[str], reason: str`
- Reorder the sections on a page without changing their content
- `validate()`: check page exists, check all section IDs in new_section_order exist on the page
- `preview()`: show current order vs new order
- `execute()`: reorder sections in page content
- `verify()`: confirm section order matches new_section_order

**Class: AddSection(Action)**
- Constructor params: `page_id: str, position: str, section_type: str, content: str, reason: str`
- `position`: "before:{section_id}", "after:{section_id}", "top", "bottom"
- `section_type`: "hero", "testimonials", "cta_block", "faq", "trust_signals", "service_description", "contact_form", "custom"
- `validate()`: check page exists, check position reference is valid, validate content is not empty
- `preview()`: show where the new section will be inserted and its content
- `execute()`: insert section content at specified position
- `verify()`: confirm new section exists at the expected position

**Helper functions:**

`generate_diff(before: str, after: str) -> Dict[str, Any]`
- Generate a structured diff between two content strings
- Output: `{"before": str, "after": str, "changes": [{"type": "add|remove|modify", "line": int, "content": str}], "summary": str}`
- Use Python's `difflib` module for diff generation
- `summary`: "Changed 3 lines, added 5 lines, removed 2 lines"

`parse_page_sections(html: str) -> List[Dict[str, Any]]`
- Parse HTML content into logical sections
- Look for: `<section>` tags, `<div>` with class/id indicators, `<h2>`/`<h3>` headings as section boundaries
- Each section: `{"section_id": str, "section_type": str, "content": str, "start_line": int, "end_line": int}`
- Section type inference: "hero" (first section with h1), "nav" (nav elements), "footer" (footer element), "sidebar" (aside elements), "content" (default)

`validate_html_safety(html: str) -> Dict[str, Any]`
- Check that HTML content is safe to inject:
  - No `<script>` tags (unless explicitly expected for tracking)
  - No `<iframe>` tags (unless explicitly expected)
  - No `onclick` or other inline event handlers
  - No external resource loading from unknown domains
- Return: `{"safe": bool, "warnings": List[str]}`

## Output Files

- `kai/actions/__init__.py`
- `kai/actions/base.py`
- `kai/actions/website.py`

## Acceptance Criteria

- [ ] `base.py` contains ActionLifecycleState enum, ActionResult model, and abstract Action class
- [ ] Action class has all 8 methods (4 abstract + 4 concrete) with correct state transitions
- [ ] `website.py` contains all 8 concrete action classes (UpdatePageCopy, UpdatePageSection, UpdateCTA, UpdateMetadata, FixTracking, RefreshApprovedSection, RestructurePage, AddSection)
- [ ] Each action class accepts specific constructor params matching its purpose
- [ ] Each action's validate() checks for required parameters and target existence
- [ ] Each action's preview() generates a meaningful diff or comparison
- [ ] Each action's execute() calls the appropriate CMS connector method
- [ ] Each action's verify() reads back and confirms the change
- [ ] State transitions are enforced (cannot execute without approval, cannot rollback without completion)
- [ ] generate_diff uses difflib for structured diff generation
- [ ] parse_page_sections handles common HTML structures
- [ ] validate_html_safety catches script injection and unsafe elements
- [ ] rollback() restores before_state via connector
- [ ] approve() and cancel() enforce valid state transitions
- [ ] `kai/actions/__init__.py` exports all classes via `__all__`

## Reference Materials

- `kai/connectors/cms/base.py` (created by Task 033) — CMSConnector interface that actions call
- `kai/models/proposal.py` (created by Task 022) — ProposedAction schema with suggested_payload
- `kai/runtime/actions.py` — existing ActionProposal in the runtime (for compatibility awareness)
- `kai/creative/libraries.py` (created by Task 032) — ApprovedMessageBlock for RefreshApprovedSection
- Python `difflib` module — for diff generation
