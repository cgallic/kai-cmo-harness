# Task 077: Build local operator surfaces

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 14. Operator Surfaces, Packaging, and Delivery
**Priority:** P1
**Depends on:** 013, 022
**Estimated complexity:** Large

## Context

The local operator surface is how a human interacts with Kai from the command line or Claude Code environment. It translates system capabilities (audits, proposals, approvals, status) into typed commands that operators can invoke. This is the primary user interface for the MVP — before dashboards or web UIs exist, the operator interacts with Kai through skill commands. The command system maps to the existing `harness/skills/` pattern, making each command a first-class skill invocation. The output formatters ensure that audit results, proposals, and status information are displayed in a readable, actionable format.

## Scope

Create `kai/operator/local_surface.py` containing the command parser and dispatcher for all `/kai` commands, and `kai/operator/formatters.py` for pretty-printing output to the terminal.

## Detailed Requirements

### File: `kai/operator/__init__.py`
- Module docstring explaining operator surface layers
- Export key classes

### File: `kai/operator/local_surface.py`

**Model: CommandResult**
- `success: bool`
- `command: str` — the command that was run
- `output: str` — formatted output string
- `data: Optional[Dict[str, Any]]` — structured data (for programmatic consumption)
- `errors: List[str]` — any errors encountered
- `next_steps: List[str]` — suggested next commands

**Class: LocalOperatorSurface**
- `__init__(self, business_id: str, workspace_dir: str)` — initialize with a business context
- `_business_id: str`
- `_workspace_dir: str`

**Command methods** (each returns a CommandResult):

- `cmd_audit(self, args: Dict[str, Any]) -> CommandResult`:
  - Run full audit for current business
  - Args: `scope` (optional: "full", "website", "seo", "social", "ads", "lifecycle" — default "full")
  - Load business profile, run audit engine, compile results
  - Format output using `formatters.py`
  - Output: audit summary with category scores, finding counts by severity, top 5 critical findings
  - Next steps: ["kai proposals" to see resulting proposals]

- `cmd_proposals(self, args: Dict[str, Any]) -> CommandResult`:
  - Show current proposal queue
  - Args: `filter` (optional: "pending", "approved", "rejected", "all" — default "pending"), `channel` (optional), `limit` (optional, default 20)
  - Format: table with columns [ID, Title, Channel, Risk, Priority, Status]
  - Show total count and summary stats
  - Next steps: ["kai approve <id>" or "kai reject <id> <reason>"]

- `cmd_approve(self, args: Dict[str, Any]) -> CommandResult`:
  - Approve a proposed action
  - Args: `action_id` (required), `notes` (optional)
  - Validate action exists and is in pending state
  - Route through approval system
  - Output: confirmation with action details and execution timeline
  - Next steps: ["kai execute <id>" or "kai status"]

- `cmd_reject(self, args: Dict[str, Any]) -> CommandResult`:
  - Reject a proposed action with feedback
  - Args: `action_id` (required), `reason` (required), `category` (optional: RejectionCategory)
  - Create Rejection record
  - Trigger revision workflow if applicable
  - Output: confirmation with rejection details
  - Next steps: ["kai proposals" to see updated queue]

- `cmd_execute(self, args: Dict[str, Any]) -> CommandResult`:
  - Execute an approved action
  - Args: `action_id` (required), `dry_run` (optional, default False)
  - Validate action is in approved state
  - If dry_run: show what would happen without executing
  - Output: execution status or dry-run preview
  - Next steps: ["kai status" to monitor]

- `cmd_status(self, args: Dict[str, Any]) -> CommandResult`:
  - Show system status dashboard
  - Output sections:
    - System health: active/paused/maintenance
    - Pending actions: count by risk tier
    - Active campaigns: list with key metrics
    - Recent changes: last 5 actions taken
    - Active watchers: count of enabled watchers and last run times
    - Alerts: any critical watcher findings
  - Next steps: contextual based on status

- `cmd_history(self, args: Dict[str, Any]) -> CommandResult`:
  - Show action history
  - Args: `days` (optional, default 30), `channel` (optional), `action_type` (optional), `limit` (optional, default 50)
  - Format: table with columns [Date, Action, Channel, Status, Outcome]
  - Next steps: ["kai status" for current state]

- `cmd_watchers(self, args: Dict[str, Any]) -> CommandResult`:
  - Show active watchers and recent findings
  - Args: `watcher` (optional: specific watcher name), `findings_only` (optional, default False)
  - Output: list of watchers with status, last run, finding count
  - If findings_only: show only recent findings sorted by severity
  - Next steps: contextual based on findings

- `cmd_memory(self, args: Dict[str, Any]) -> CommandResult`:
  - Show key learnings and brand preferences
  - Args: `layer` (optional: "brand", "channel", "proof", "offers", "audience", "all" — default "all")
  - Output: summarized learnings by category
  - Next steps: ["kai memory confirm <id>" to confirm pending learnings]

- `cmd_profile(self, args: Dict[str, Any]) -> CommandResult`:
  - Show or edit business profile
  - Args: `edit` (optional, bool — if True, show editable fields), `field` (optional: specific field to show/edit), `value` (optional: new value for field)
  - If no args: show current profile summary
  - If edit + field + value: update the field
  - Output: profile summary or confirmation of edit

**Function: parse_command(input_str: str) -> Tuple[str, Dict[str, Any]]**
- Parse a raw input string into command name and arguments
- Handle formats:
  - `kai audit` → ("audit", {})
  - `kai audit --scope website` → ("audit", {"scope": "website"})
  - `kai approve act_abc123` → ("approve", {"action_id": "act_abc123"})
  - `kai reject act_abc123 "headline too aggressive"` → ("reject", {"action_id": "act_abc123", "reason": "headline too aggressive"})
  - `kai proposals --filter pending --channel email` → ("proposals", {"filter": "pending", "channel": "email"})
- Return (command_name, args_dict)

**Function: dispatch_command(surface: LocalOperatorSurface, command: str, args: Dict[str, Any]) -> CommandResult**
- Route command string to the appropriate method on LocalOperatorSurface
- Handle unknown commands gracefully (return error with available commands)

### File: `kai/operator/formatters.py`

**Function: format_audit_summary(audit_result: Dict[str, Any]) -> str**
- Format audit results for terminal display
- Include: overall score, per-category scores (with visual bar), finding counts by severity, top critical findings
- Use plain text formatting (no colors/ANSI — just alignment, borders, and indentation)

**Function: format_proposal_table(proposals: List[Dict[str, Any]]) -> str**
- Format proposals as an aligned text table
- Columns: ID (truncated), Title (max 50 chars), Channel, Risk Tier, Priority, Status
- Include header and separator rows

**Function: format_action_detail(action: Dict[str, Any]) -> str**
- Format a single action's full details
- Include: all fields, preview of content if available, approval status, execution timeline

**Function: format_status_dashboard(status: Dict[str, Any]) -> str**
- Format system status as a multi-section dashboard
- Sections with headers and clear separation

**Function: format_watcher_findings(findings: List[Dict[str, Any]]) -> str**
- Format watcher findings sorted by severity
- Include: severity icon (text-based: [!] critical, [*] high, [-] medium, [ ] low), title, description

**Function: format_memory_summary(memories: Dict[str, Any]) -> str**
- Format memory/learning summary by category
- Include: count per category, key highlights, pending confirmations

**Function: format_profile_summary(profile: Dict[str, Any]) -> str**
- Format business profile for display
- Key fields: name, archetype, active channels, service area, primary offers

**Helper: truncate(text: str, max_length: int) -> str**
- Truncate text to max_length, add "..." if truncated

**Helper: align_table(headers: List[str], rows: List[List[str]], padding: int = 2) -> str**
- Create an aligned text table from headers and rows
- Auto-detect column widths
- Return formatted string

## Output Files

- `kai/operator/__init__.py`
- `kai/operator/local_surface.py`
- `kai/operator/formatters.py`

## Acceptance Criteria

- All files parse as valid Python
- All 10 command methods are implemented with proper argument validation
- `parse_command` handles all documented input formats including quoted strings
- `dispatch_command` routes correctly and handles unknown commands
- Every CommandResult includes next_steps suggestions for workflow continuity
- Formatters produce readable, aligned text output without relying on ANSI color codes
- `align_table` correctly handles varying column widths
- Profile editing validates that the field exists before attempting to update
- Audit command supports scoped audits (not just full audit)
- Proposals command supports filtering by status, channel, and limit
- No external dependencies

## Reference Materials

- `kai/runtime/audit.py` — AuditFinding, AuditResult models
- `kai/runtime/actions.py` — ProposedAction models
- `kai/compliance/approval_routing.py` (Task 064) — approval flow
- `kai/compliance/revision.py` (Task 065) — rejection handling
- `kai/watchers/framework.py` (Task 067) — watcher findings
- `kai/memory/schemas.py` (Task 074) — memory layers
- `harness/skills/` — existing skill patterns to align with
- `kai/runtime/models.py` — SerializableModel pattern
