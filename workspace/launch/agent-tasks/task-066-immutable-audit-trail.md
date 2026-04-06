# Task 066: Build immutable audit trail

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 11. Approval, Compliance, and Policy Control
**Priority:** P2
**Depends on:** 064
**Estimated complexity:** Medium

## Context

An autonomous marketing system must maintain a complete, immutable record of everything it does. This is essential for regulatory compliance (proving what was approved and by whom), operator trust (seeing exactly what the system did and when), debugging (understanding why something happened), and learning (connecting actions to outcomes). The audit trail is append-only — entries can never be modified or deleted after creation. This ensures the integrity of the record even if something goes wrong. Every other system in Kai writes to this trail: approvals, executions, content publishing, budget spending, profile changes, kill switch activations, and operator overrides.

## Scope

Create `kai/compliance/audit_trail.py` containing the AuditEntry model, the AuditTrail append-only log manager, query interface, and compliance report generation.

## Detailed Requirements

### File: `kai/compliance/audit_trail.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`. For file I/O, follow the patterns in `kai/runtime/actions.py` (atomic writes, JSON helpers, thread safety).

**Enum: AuditActor**
- `system` — automated system action
- `operator` — human operator action
- `agent` — AI agent decision
- `scheduler` — scheduled/cron action
- `compliance_engine` — compliance check result
- `watcher` — background watcher finding

**Enum: AuditActionType**
- `finding_generated` — audit finding created
- `action_proposed` — marketing action proposed
- `action_approved` — action approved by operator or auto-approved
- `action_rejected` — action rejected by operator
- `action_revised` — action revised after rejection
- `action_executed` — action executed/deployed
- `action_failed` — action execution failed
- `action_rolled_back` — action was rolled back
- `content_created` — content asset created
- `content_published` — content published to a channel
- `content_unpublished` — content removed from a channel
- `budget_spent` — ad spend or budget allocation
- `profile_updated` — business profile changed
- `workspace_updated` — workspace state changed
- `compliance_check` — compliance check performed
- `compliance_violation` — compliance violation detected
- `kill_switch_activated` — kill switch triggered
- `kill_switch_deactivated` — kill switch lifted
- `operator_override` — operator overrode a system decision
- `watcher_finding` — background watcher produced a finding
- `memory_updated` — learning/memory entry written
- `escalation` — action or decision escalated to higher authority

**Model: AuditEntry**
- `id: str` — format `audit_{uuid_hex[:12]}`
- `timestamp: str` — ISO timestamp (UTC)
- `actor: str` — AuditActor enum value
- `actor_id: Optional[str]` — specific identifier (operator name, agent id, watcher name)
- `action_type: str` — AuditActionType enum value
- `action_id: Optional[str]` — reference to the ProposedAction, finding, or other object
- `business_id: str` — which business this relates to
- `description: str` — human-readable description of what happened
- `before_state: Optional[Dict[str, Any]]` — state before the action (for profile/workspace updates)
- `after_state: Optional[Dict[str, Any]]` — state after the action
- `approval_status: Optional[str]` — "auto_approved", "operator_approved", "operator_rejected", None
- `spend_amount: Optional[float]` — if this involved budget spend
- `channel: Optional[str]` — which marketing channel
- `risk_tier: Optional[str]` — risk tier of the action
- `compliance_status: Optional[str]` — "pass", "fail", "warning" if compliance was checked
- `metadata: Dict[str, Any]` — additional context
- `parent_entry_id: Optional[str]` — for linking related audit entries (e.g., approval links to proposal)
- `checksum: Optional[str]` — SHA-256 hash of the entry content for integrity verification

**Class: AuditTrail**
- `__init__(self, base_dir: str)` — base directory for audit files (typically `workspace/`)
- `_lock: threading.Lock` — for thread-safe appends
- `append(self, entry: AuditEntry) -> str`:
  - Generate checksum of entry content (SHA-256 of JSON-serialized entry excluding checksum field)
  - Set entry.checksum
  - Determine file path: `{base_dir}/{business_id}/audit/{YYYY-MM}.jsonl`
  - Append the JSON-serialized entry as a single line to the JSONL file
  - Create directories if they don't exist
  - Use file locking to prevent concurrent write corruption
  - Return the entry id
  - CRITICAL: This method must be append-only. It must NEVER modify or overwrite existing lines.
- `_compute_checksum(self, entry: AuditEntry) -> str`:
  - Serialize entry to JSON (excluding checksum field)
  - Return SHA-256 hex digest
- `_get_file_path(self, business_id: str, date: str) -> Path`:
  - Parse date to get year-month
  - Return Path to the JSONL file
- `query(self, business_id: str, start_date: Optional[str] = None, end_date: Optional[str] = None, actor: Optional[str] = None, action_type: Optional[str] = None, action_id: Optional[str] = None, channel: Optional[str] = None, limit: int = 100, offset: int = 0) -> List[AuditEntry]`:
  - Read the relevant JSONL files for the date range
  - Apply filters
  - Return matching entries with pagination (limit/offset)
  - Sort by timestamp descending (most recent first)
- `query_by_action(self, action_id: str, business_id: str) -> List[AuditEntry]`:
  - Convenience method: find all audit entries related to a specific action_id
  - Searches across all available JSONL files for the business
  - Returns entries sorted by timestamp ascending (chronological)
- `get_action_timeline(self, action_id: str, business_id: str) -> List[Dict[str, Any]]`:
  - Return a clean timeline of an action's lifecycle
  - Each entry: {timestamp, event_type, description, actor}
  - Ordered chronologically
- `verify_integrity(self, business_id: str, month: str) -> Dict[str, Any]`:
  - Read all entries in a JSONL file
  - Recompute checksums and verify they match stored checksums
  - Return: {total_entries, verified_ok, verification_failures (list of entry ids with mismatched checksums)}
- `generate_compliance_report(self, business_id: str, start_date: str, end_date: str) -> Dict[str, Any]`:
  - Query all entries in the date range
  - Compile a report with:
    - `total_actions`: count of all actions proposed
    - `approved_actions`: count of approved actions
    - `rejected_actions`: count of rejected actions
    - `auto_approved_actions`: count of auto-approved actions
    - `compliance_checks`: count of compliance checks performed
    - `compliance_violations`: list of all violations with details
    - `kill_switch_activations`: list of all kill switch events
    - `operator_overrides`: list of all operator overrides
    - `total_spend`: sum of all spend_amount entries
    - `spend_by_channel`: dict of channel -> total spend
    - `regulated_actions`: list of actions in regulated categories (healthcare, financial, legal) with their approval chain
  - Return the report as a dict

**Function: create_audit_entry(actor: str, action_type: str, business_id: str, description: str, **kwargs) -> AuditEntry**
- Convenience function for creating entries with proper id and timestamp
- Accept optional keyword arguments for all optional AuditEntry fields
- Generate id and timestamp automatically
- Return the AuditEntry (caller must still call trail.append())

**Function: log_approval(trail: AuditTrail, action_id: str, business_id: str, approved_by: str, route: str, risk_tier: str, spend: Optional[float] = None) -> str**
- Convenience function: create and append an approval audit entry
- Return the entry id

**Function: log_execution(trail: AuditTrail, action_id: str, business_id: str, channel: str, description: str, success: bool) -> str**
- Convenience function: create and append an execution audit entry
- Use action_type "action_executed" if success, "action_failed" if not
- Return the entry id

**Function: log_compliance_violation(trail: AuditTrail, action_id: str, business_id: str, violation_description: str, rule_id: str, severity: str) -> str**
- Convenience function: create and append a compliance violation entry
- Return the entry id

## Output Files

- `kai/compliance/audit_trail.py`

## Acceptance Criteria

- File parses as valid Python
- `AuditTrail.append()` is truly append-only — it opens the file in append mode ("a"), never write mode ("w")
- Checksum computation is deterministic (sorted JSON keys, consistent serialization)
- `verify_integrity()` correctly detects tampered entries
- `query()` correctly applies all filter parameters and respects pagination
- JSONL files are organized by business_id and year-month
- Thread safety is implemented with `threading.Lock` on append operations
- `generate_compliance_report()` produces a comprehensive report with all specified sections
- Convenience functions (log_approval, log_execution, log_compliance_violation) correctly populate all fields
- AuditActionType enum covers all action types listed in the requirements
- File I/O follows the patterns from `kai/runtime/actions.py` (atomic helpers, path management)
- No external dependencies beyond stdlib (hashlib for SHA-256, json, threading, pathlib)

## Reference Materials

- `kai/runtime/actions.py` — file I/O patterns, atomic writes, thread safety, JSON helpers
- `kai/runtime/store.py` — file storage conventions and directory structure
- `kai/compliance/approval_routing.py` (Task 064) — RoutingDecision, what gets logged
- `kai/compliance/revision.py` (Task 065) — Rejection, KillSwitchActivation events to log
- `kai/runtime/models.py` — SerializableModel pattern
