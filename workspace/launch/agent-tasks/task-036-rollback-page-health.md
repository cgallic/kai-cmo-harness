# Task 036: Build rollback support and page health monitoring

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 6. Website Operations
**Priority:** P2
**Depends on:** 034
**Estimated complexity:** Medium

## Context

When Kai makes changes to a live website, things can go wrong — a CTA update might break a form, a content change might introduce a typo, or an SEO fix might accidentally remove schema markup. The rollback system ensures every change can be undone by snapshotting the page state before any modification and providing a one-click restore function. The page health monitoring system defines structured checks to verify that a page is healthy after changes — key elements are present, links are not broken, and the page structure is intact.

Together, these systems create a safety net that makes automated website changes reversible and verifiable.

## Scope

Build `kai/actions/rollback.py` containing the ChangeRecord model, snapshot/rollback functions, the PageHealthCheck model, and health verification logic. All checks are structural definitions — they describe what to verify, not how to browse or load pages.

## Detailed Requirements

### File: `kai/actions/rollback.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Model: ChangeRecord**
- `id: str` — unique identifier, format `chg_{uuid_hex[:12]}`
- `action_id: str` — links to the Action that made this change
- `action_type: str` — type of action (from website action class name)
- `page_id: str` — which page was changed
- `page_url: Optional[str]` — live URL of the page
- `page_title: Optional[str]` — title of the page
- `before_state: Dict[str, Any]` — complete page state before the change:
  ```python
  {
      "content_html": str,        # full HTML content
      "metadata": Dict[str, Any], # title, meta description, schema, etc.
      "sections": List[Dict],     # parsed sections
      "snapshot_hash": str,       # hash of content for quick comparison
  }
  ```
- `after_state: Dict[str, Any]` — complete page state after the change (same structure)
- `change_summary: str` — human-readable description of what changed
- `timestamp: str` — ISO timestamp of when the change was made
- `operator: Optional[str]` — who approved this change (or "system" for auto-approved)
- `rollback_available: bool` — whether rollback is possible, default True
- `rollback_performed: bool` — whether this change has been rolled back, default False
- `rollback_timestamp: Optional[str]` — when rollback was performed
- `rollback_result: Optional[Dict[str, Any]]` — result of rollback operation
- `health_check_result: Optional[Dict[str, Any]]` — result of post-change health check
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Function: `create_snapshot(connector: Any, page_id: str) -> Dict[str, Any]`**
- Use the CMS connector to get the full page state
- Call `connector.get_page(page_id)` to get content
- Call `connector.get_metadata(page_id)` to get metadata
- Parse content into sections using `parse_page_sections` from `kai/actions/website.py`
- Compute a hash of the content for quick comparison
- Return a snapshot dict matching the `before_state` structure
- Handle connector errors gracefully — if page doesn't exist, return error snapshot

**Function: `record_change(action_id: str, action_type: str, page_id: str, before_snapshot: Dict[str, Any], after_snapshot: Dict[str, Any], change_summary: str, operator: Optional[str] = None) -> Dict[str, Any]`**
- Create a ChangeRecord dict from the provided data
- Generate unique ID
- Set timestamp to current UTC time
- Set rollback_available based on whether before_state has valid content
- Return ChangeRecord dict

**Function: `rollback_change(change_record: Dict[str, Any], connector: Any) -> Dict[str, Any]`**
- Restore the before_state of a change
- Steps:
  1. Verify rollback_available is True
  2. Verify rollback_performed is False (can't rollback twice)
  3. Take a current snapshot (in case the page was further modified since our change)
  4. Restore content: call `connector.update_page_section()` with before_state content
  5. Restore metadata: call `connector.update_metadata()` with before_state metadata
  6. Verify the restoration by taking another snapshot and comparing with before_state
  7. Update change_record: set rollback_performed=True, rollback_timestamp, rollback_result
- Return updated ChangeRecord dict with rollback result:
  ```python
  {
      "success": bool,
      "restored_content_match": bool,  # does restored content match before_state?
      "restored_metadata_match": bool, # does restored metadata match before_state?
      "warnings": List[str],           # any issues during rollback
      "intermediate_state": Dict,      # state that was overwritten by rollback (in case operator wants to go back to it)
  }
  ```

**Function: `can_rollback(change_record: Dict[str, Any]) -> Dict[str, Any]`**
- Check if a rollback is possible:
  - `rollback_available` must be True
  - `rollback_performed` must be False
  - `before_state` must have valid content
  - Change must not be too old (configurable, default 30 days)
- Return: `{"can_rollback": bool, "reason": str}`

**Model: PageHealthCheck**
- `id: str` — unique identifier, format `phc_{uuid_hex[:12]}`
- `page_id: str` — which page to check
- `page_url: Optional[str]` — live URL
- `check_results: List[Dict[str, Any]]` — individual check results, each with:
  - `check_name: str` — name of the check
  - `passed: bool`
  - `details: str` — what was checked and what was found
  - `severity: str` — "critical", "warning", "info"
- `overall_healthy: bool` — True only if no critical checks failed
- `critical_failures: int` — count of critical check failures
- `warnings: int` — count of warning-level issues
- `timestamp: str` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Function: `define_health_checks(page_content: str, page_metadata: Dict[str, Any], page_type: Optional[str] = None) -> List[Dict[str, Any]]`**
- Define the set of health checks to run on a page (returns check definitions, not results)
- Universal checks (all pages):
  1. `title_present` — page has a non-empty `<title>` tag (critical)
  2. `meta_description_present` — page has a meta description (warning)
  3. `h1_present` — page has exactly one `<h1>` tag (warning)
  4. `no_broken_images` — all `<img>` tags have non-empty `src` attributes (critical)
  5. `no_empty_links` — all `<a>` tags have non-empty `href` attributes (warning)
  6. `phone_number_present` — page contains at least one phone number pattern (warning, only for local-service pages)
  7. `cta_present` — page has at least one CTA element (button, link with CTA class, or form submit) (warning)
  8. `no_lorem_ipsum` — content does not contain "lorem ipsum" or similar placeholder text (critical)
  9. `no_console_errors_indicators` — no `<script>` tags with obvious errors (unclosed tags, syntax issues) (critical)
  10. `content_not_empty` — page body has meaningful content (> 50 words) (critical)
  11. `schema_markup_valid` — if JSON-LD schema exists, it is valid JSON (warning)
  12. `canonical_url_present` — page has a canonical URL tag (info)
- Additional checks by page_type:
  - `homepage`: check for hero section, trust signals, service overview, contact info
  - `service_page`: check for service description, CTA, pricing indicators, testimonials
  - `contact_page`: check for form, phone number, address, map embed
  - `blog_post`: check for author, date, content length (> 300 words), internal links

**Function: `run_health_checks(page_content: str, page_metadata: Dict[str, Any], page_type: Optional[str] = None) -> Dict[str, Any]`**
- Define and evaluate health checks against the page content
- For each check:
  - Parse the page content using simple string/regex operations (no external HTML parser required)
  - Evaluate the check condition
  - Record pass/fail with details
- Compute overall_healthy (no critical failures)
- Count critical_failures and warnings
- Return PageHealthCheck dict

**Specific check implementations (all using string/regex parsing):**

`_check_title_present(content: str) -> Dict[str, Any]`
- Regex search for `<title>` tag with content
- Return check result dict

`_check_meta_description(metadata: Dict[str, Any], content: str) -> Dict[str, Any]`
- Check metadata dict for description field, or regex search for `<meta name="description"` in content
- Return check result dict

`_check_h1_count(content: str) -> Dict[str, Any]`
- Count `<h1>` tags in content
- Pass if exactly 1, warn if 0 or > 1
- Return check result dict

`_check_broken_images(content: str) -> Dict[str, Any]`
- Regex find all `<img` tags, check each has a non-empty `src` attribute
- Return check result dict with count of broken images

`_check_empty_links(content: str) -> Dict[str, Any]`
- Regex find all `<a` tags, check each has a non-empty `href` (not "#" unless it's an anchor link)
- Return check result dict

`_check_phone_number(content: str) -> Dict[str, Any]`
- Regex search for phone number patterns (US format: xxx-xxx-xxxx, (xxx) xxx-xxxx, etc.)
- Return check result dict with found phone numbers

`_check_cta_present(content: str) -> Dict[str, Any]`
- Look for: `<button>` tags, `<a>` with class containing "cta", "btn", "button", or `<input type="submit">`
- Return check result dict with count of CTAs found

`_check_placeholder_content(content: str) -> Dict[str, Any]`
- Search for: "lorem ipsum", "dolor sit amet", "placeholder", "TODO", "FIXME", "[insert", "[replace"
- Return check result dict with found placeholders

`_check_content_length(content: str) -> Dict[str, Any]`
- Strip HTML tags, count words
- Critical if < 50 words (page is essentially empty)
- Warning if < 200 words (thin content)
- Return check result dict with word count

`_check_schema_markup(content: str) -> Dict[str, Any]`
- Find `<script type="application/ld+json">` blocks
- Attempt to parse as JSON (using `json.loads`)
- Return check result dict with schema types found and validation status

**Function: `get_page_history(page_id: str, change_records: List[Dict[str, Any]]) -> List[Dict[str, Any]]`**
- Filter change_records by page_id
- Sort by timestamp descending (most recent first)
- Return list of ChangeRecords for this page

**Function: `compare_snapshots(snapshot_a: Dict[str, Any], snapshot_b: Dict[str, Any]) -> Dict[str, Any]`**
- Compare two page snapshots and report differences
- Check: content_hash match, metadata changes, section count changes
- Return: `{"identical": bool, "content_changed": bool, "metadata_changed": bool, "sections_changed": bool, "details": List[str]}`

## Output Files

- `kai/actions/rollback.py`

## Acceptance Criteria

- [ ] `rollback.py` contains ChangeRecord and PageHealthCheck models with all specified fields
- [ ] create_snapshot captures full page state (content + metadata + sections + hash)
- [ ] record_change creates a complete ChangeRecord with before/after states
- [ ] rollback_change restores before_state via CMS connector with verification
- [ ] can_rollback checks all conditions including age limit
- [ ] Rollback preserves the intermediate state (what was overwritten) for recovery
- [ ] define_health_checks returns 12+ universal checks plus page-type-specific checks
- [ ] run_health_checks evaluates all checks using string/regex parsing (no external HTML parser)
- [ ] Individual check functions exist for all 10+ check types
- [ ] Phone number detection uses regex for common US formats
- [ ] Schema markup validation attempts JSON parsing
- [ ] Placeholder content detection catches lorem ipsum and common markers
- [ ] get_page_history filters and sorts change records by page
- [ ] compare_snapshots detects content, metadata, and section changes
- [ ] All functions handle edge cases (empty content, missing metadata, malformed HTML)
- [ ] No external dependencies beyond stdlib (re, json, hashlib, difflib)

## Reference Materials

- `kai/actions/base.py` (created by Task 034) — Action class with rollback() method
- `kai/actions/website.py` (created by Task 034) — website action types and parse_page_sections helper
- `kai/connectors/cms/base.py` (created by Task 033) — CMSConnector.get_page(), update_page_section()
- `gateway/models.py` — Pydantic import fallback pattern
- `knowledge/checklists/technical-seo-audit-sop.md` — SEO health check items
