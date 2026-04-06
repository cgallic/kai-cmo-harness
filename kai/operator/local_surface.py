"""Local operator surface for the Kai Marketing OS.

This module provides the command-line / Claude Code interaction layer.
Operators invoke ``/kai <command>`` and receive formatted plain-text
output.  Every command returns a :class:`CommandResult` containing the
formatted output, structured data for programmatic consumption, any
errors, and suggested next steps for workflow continuity.

Parsing
-------
``parse_command`` turns a raw input string into a ``(command, args)``
tuple.  ``dispatch_command`` routes the command to the appropriate
method on :class:`LocalOperatorSurface`.

Data access
-----------
All data is read from the workspace directory via lazy helpers that
tolerate missing backing stores (the system is being built
incrementally).  Missing subsystems return sensible empty defaults
rather than crashing.
"""

from __future__ import annotations

import json
import os
import re
import shlex
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from kai.operator.formatters import (
    format_action_detail,
    format_audit_summary,
    format_memory_summary,
    format_profile_summary,
    format_proposal_table,
    format_status_dashboard,
    format_watcher_findings,
    truncate,
)


# ============================================================================
# CommandResult
# ============================================================================


class CommandResult:
    """Structured result returned by every operator command.

    Attributes
    ----------
    success : bool
        Whether the command completed without errors.
    command : str
        The command that was run (e.g. ``"audit"``).
    output : str
        Formatted text output for terminal display.
    data : dict or None
        Structured data for programmatic consumption.
    errors : list of str
        Any errors encountered during execution.
    next_steps : list of str
        Suggested next commands for workflow continuity.
    """

    def __init__(
        self,
        success: bool,
        command: str,
        output: str = "",
        data: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        next_steps: Optional[List[str]] = None,
    ) -> None:
        self.success = success
        self.command = command
        self.output = output
        self.data = data
        self.errors = errors or []
        self.next_steps = next_steps or []

    def __repr__(self) -> str:
        status = "OK" if self.success else "FAIL"
        return f"<CommandResult [{status}] command={self.command!r}>"


# ============================================================================
# Lazy data-access helpers
# ============================================================================


def _load_json_file(path: str) -> Optional[Dict[str, Any]]:
    """Load a JSON file, returning ``None`` on any failure."""
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return None


def _list_json_dir(dirpath: str) -> List[Dict[str, Any]]:
    """Read every ``*.json`` file in *dirpath* and return a list of dicts."""
    results: List[Dict[str, Any]] = []
    if not os.path.isdir(dirpath):
        return results
    for name in sorted(os.listdir(dirpath)):
        if name.endswith(".json"):
            data = _load_json_file(os.path.join(dirpath, name))
            if data is not None:
                results.append(data)
    return results


def _try_audit_engine(business_id: str, scope: str, workspace_dir: str) -> Optional[Dict[str, Any]]:
    """Attempt to run the audit engine and return a result dict.

    Falls back to loading the latest cached audit from the workspace if
    the engine is not yet importable.
    """
    # Try the canonical audit engine first.
    try:
        from kai.models.audit import compile_audit_result  # noqa: F811
        # The audit engine needs a business profile and engine findings.
        # If those subsystems are not available yet, fall through.
    except ImportError:
        pass

    # Fallback: look for a cached audit result on disk.
    audit_dir = os.path.join(workspace_dir, "audits", business_id)
    if os.path.isdir(audit_dir):
        files = sorted(
            [f for f in os.listdir(audit_dir) if f.endswith(".json")],
            reverse=True,
        )
        for fname in files:
            data = _load_json_file(os.path.join(audit_dir, fname))
            if data is not None:
                if scope != "full" and data.get("audit_type", "") != scope:
                    continue
                return data
    return None


def _try_load_proposals(business_id: str, workspace_dir: str) -> List[Dict[str, Any]]:
    """Load proposals from the workspace proposal store."""
    proposals_dir = os.path.join(workspace_dir, "proposals", business_id)
    return _list_json_dir(proposals_dir)


def _try_load_action(action_id: str, workspace_dir: str) -> Optional[Dict[str, Any]]:
    """Load a single action/proposal by scanning subdirectories."""
    proposals_root = os.path.join(workspace_dir, "proposals")
    if not os.path.isdir(proposals_root):
        return None
    for biz_dir in os.listdir(proposals_root):
        biz_path = os.path.join(proposals_root, biz_dir)
        if not os.path.isdir(biz_path):
            continue
        for fname in os.listdir(biz_path):
            if not fname.endswith(".json"):
                continue
            data = _load_json_file(os.path.join(biz_path, fname))
            if data is not None and data.get("id") == action_id:
                return data
    return None


def _try_save_action(action: Dict[str, Any], workspace_dir: str) -> None:
    """Persist a modified action back to the proposals directory."""
    biz_id = action.get("business_id", "unknown")
    proposals_dir = os.path.join(workspace_dir, "proposals", biz_id)
    os.makedirs(proposals_dir, exist_ok=True)
    fname = f"{action.get('id', 'unknown')}.json"
    with open(os.path.join(proposals_dir, fname), "w", encoding="utf-8") as fh:
        json.dump(action, fh, indent=2, default=str)


def _try_load_history(
    business_id: str,
    workspace_dir: str,
    days: int = 30,
    channel: Optional[str] = None,
    action_type: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """Load action history from the workspace."""
    history_dir = os.path.join(workspace_dir, "history", business_id)
    entries = _list_json_dir(history_dir)
    # Filter by channel
    if channel:
        entries = [e for e in entries if e.get("channel") == channel]
    # Filter by action_type
    if action_type:
        entries = [e for e in entries if e.get("action_type") == action_type]
    # Sort by date descending
    entries.sort(key=lambda e: e.get("timestamp", e.get("created_at", "")), reverse=True)
    return entries[:limit]


def _try_load_watchers(business_id: str, workspace_dir: str) -> Dict[str, Any]:
    """Load watcher state from the workspace."""
    watchers_file = os.path.join(workspace_dir, "watchers", business_id, "state.json")
    return _load_json_file(watchers_file) or {"watchers": [], "findings": []}


def _try_load_memory(business_id: str, workspace_dir: str, layer: str = "all") -> Dict[str, Any]:
    """Load memory / learnings from the workspace."""
    memory_dir = os.path.join(workspace_dir, "memory", business_id)
    if not os.path.isdir(memory_dir):
        return {}

    all_layers = ["brand", "channel", "proof", "offers", "audience"]
    layers_to_load = all_layers if layer == "all" else [layer]
    result: Dict[str, Any] = {}
    for lyr in layers_to_load:
        lyr_file = os.path.join(memory_dir, f"{lyr}.json")
        data = _load_json_file(lyr_file)
        if data is not None:
            result[lyr] = data
    return result


def _try_load_profile(business_id: str, workspace_dir: str) -> Optional[Dict[str, Any]]:
    """Load business profile from the workspace."""
    profile_path = os.path.join(workspace_dir, "profiles", f"{business_id}.json")
    data = _load_json_file(profile_path)
    if data is not None:
        return data
    # Try alternate location
    alt_path = os.path.join(workspace_dir, "profiles", business_id, "profile.json")
    return _load_json_file(alt_path)


def _try_save_profile(profile: Dict[str, Any], workspace_dir: str) -> None:
    """Persist a modified profile."""
    biz_id = profile.get("business_id", "unknown")
    profiles_dir = os.path.join(workspace_dir, "profiles")
    os.makedirs(profiles_dir, exist_ok=True)
    with open(os.path.join(profiles_dir, f"{biz_id}.json"), "w", encoding="utf-8") as fh:
        json.dump(profile, fh, indent=2, default=str)


# ============================================================================
# LocalOperatorSurface
# ============================================================================


# Fields that may NOT be edited via the profile command.
_PROFILE_READONLY_FIELDS = frozenset({"business_id", "id", "archetype", "created_at"})

# Allowed audit scopes.
_VALID_AUDIT_SCOPES = frozenset({"full", "website", "seo", "social", "ads", "lifecycle"})

# Allowed proposal filter values.
_VALID_PROPOSAL_FILTERS = frozenset({"pending", "approved", "rejected", "all"})


class LocalOperatorSurface:
    """Command-line operator surface for the Kai marketing runtime.

    Parameters
    ----------
    business_id : str
        The canonical business/brand identifier.
    workspace_dir : str
        Path to the Kai workspace directory on disk.
    """

    def __init__(self, business_id: str, workspace_dir: str) -> None:
        self._business_id = business_id
        self._workspace_dir = workspace_dir

    # ------------------------------------------------------------------ audit

    def cmd_audit(self, args: Dict[str, Any]) -> CommandResult:
        """Run (or retrieve) a marketing audit for the current business.

        Args (in *args* dict):
            scope -- "full", "website", "seo", "social", "ads", or
                     "lifecycle".  Defaults to "full".
        """
        scope = args.get("scope", "full")
        if scope not in _VALID_AUDIT_SCOPES:
            return CommandResult(
                success=False,
                command="audit",
                errors=[f"Invalid scope '{scope}'. Choose from: {', '.join(sorted(_VALID_AUDIT_SCOPES))}"],
                next_steps=["kai audit --scope full"],
            )

        audit_data = _try_audit_engine(self._business_id, scope, self._workspace_dir)
        if audit_data is None:
            return CommandResult(
                success=False,
                command="audit",
                output="No audit results found. Run a full audit first or check the workspace directory.",
                errors=["Audit data not available"],
                next_steps=["kai audit --scope full"],
            )

        output = format_audit_summary(audit_data)
        return CommandResult(
            success=True,
            command="audit",
            output=output,
            data=audit_data,
            next_steps=["kai proposals  -- see resulting proposals"],
        )

    # -------------------------------------------------------------- proposals

    def cmd_proposals(self, args: Dict[str, Any]) -> CommandResult:
        """Show the current proposal queue.

        Args (in *args* dict):
            filter  -- "pending", "approved", "rejected", "all".  Default "pending".
            channel -- optional channel filter.
            limit   -- max results (default 20).
        """
        status_filter = args.get("filter", "pending")
        if status_filter not in _VALID_PROPOSAL_FILTERS:
            return CommandResult(
                success=False,
                command="proposals",
                errors=[f"Invalid filter '{status_filter}'. Choose from: {', '.join(sorted(_VALID_PROPOSAL_FILTERS))}"],
                next_steps=["kai proposals --filter pending"],
            )

        channel = args.get("channel")
        limit = int(args.get("limit", 20))

        proposals = _try_load_proposals(self._business_id, self._workspace_dir)

        # Apply filters
        if status_filter != "all":
            proposals = [p for p in proposals if p.get("status") == status_filter]
        if channel:
            proposals = [p for p in proposals if p.get("channel") == channel]
        proposals = proposals[:limit]

        # Stats
        all_proposals = _try_load_proposals(self._business_id, self._workspace_dir)
        pending_count = sum(1 for p in all_proposals if p.get("status") == "proposed" or p.get("status") == "pending")
        approved_count = sum(1 for p in all_proposals if p.get("status") == "approved")
        rejected_count = sum(1 for p in all_proposals if p.get("status") == "rejected")

        output_lines = [
            format_proposal_table(proposals),
            "",
            f"Total: {len(all_proposals)}  |  Pending: {pending_count}  |  Approved: {approved_count}  |  Rejected: {rejected_count}",
        ]

        return CommandResult(
            success=True,
            command="proposals",
            output="\n".join(output_lines),
            data={
                "proposals": proposals,
                "total": len(all_proposals),
                "pending": pending_count,
                "approved": approved_count,
                "rejected": rejected_count,
            },
            next_steps=[
                "kai approve <id>   -- approve a proposal",
                "kai reject <id> <reason>  -- reject a proposal",
            ],
        )

    # --------------------------------------------------------------- approve

    def cmd_approve(self, args: Dict[str, Any]) -> CommandResult:
        """Approve a proposed action.

        Args (in *args* dict):
            action_id -- required.
            notes     -- optional approval notes.
        """
        action_id = args.get("action_id")
        if not action_id:
            return CommandResult(
                success=False,
                command="approve",
                errors=["Missing required argument: action_id"],
                next_steps=["kai approve <action_id>"],
            )

        action = _try_load_action(action_id, self._workspace_dir)
        if action is None:
            return CommandResult(
                success=False,
                command="approve",
                errors=[f"Action '{action_id}' not found"],
                next_steps=["kai proposals  -- list available proposals"],
            )

        current_status = action.get("status", "")
        if current_status not in ("proposed", "pending"):
            return CommandResult(
                success=False,
                command="approve",
                errors=[f"Action '{action_id}' is in '{current_status}' state, not pending"],
                next_steps=["kai proposals  -- list pending proposals"],
            )

        # Perform approval
        action["status"] = "approved"
        action["approved_at"] = datetime.now(timezone.utc).isoformat()
        notes = args.get("notes", "")
        if notes:
            action["approval_notes"] = notes
        _try_save_action(action, self._workspace_dir)

        title = action.get("title", action_id)
        output = (
            f"Approved: {title}\n"
            f"  Action ID:  {action_id}\n"
            f"  Risk Tier:  {action.get('risk_tier', 'N/A')}\n"
            f"  Channel:    {action.get('channel', 'N/A')}\n"
            f"  Status:     approved\n"
        )
        if notes:
            output += f"  Notes:      {notes}\n"

        return CommandResult(
            success=True,
            command="approve",
            output=output,
            data=action,
            next_steps=[
                f"kai execute {action_id}  -- execute this action",
                "kai status  -- check system status",
            ],
        )

    # ---------------------------------------------------------------- reject

    def cmd_reject(self, args: Dict[str, Any]) -> CommandResult:
        """Reject a proposed action with feedback.

        Args (in *args* dict):
            action_id -- required.
            reason    -- required rejection reason.
            category  -- optional RejectionCategory.
        """
        action_id = args.get("action_id")
        reason = args.get("reason", "")

        if not action_id:
            return CommandResult(
                success=False,
                command="reject",
                errors=["Missing required argument: action_id"],
                next_steps=["kai reject <action_id> <reason>"],
            )
        if not reason:
            return CommandResult(
                success=False,
                command="reject",
                errors=["Missing required argument: reason"],
                next_steps=[f'kai reject {action_id} "reason for rejection"'],
            )

        action = _try_load_action(action_id, self._workspace_dir)
        if action is None:
            return CommandResult(
                success=False,
                command="reject",
                errors=[f"Action '{action_id}' not found"],
                next_steps=["kai proposals  -- list available proposals"],
            )

        current_status = action.get("status", "")
        if current_status not in ("proposed", "pending"):
            return CommandResult(
                success=False,
                command="reject",
                errors=[f"Action '{action_id}' is in '{current_status}' state, not pending"],
                next_steps=["kai proposals  -- list pending proposals"],
            )

        # Perform rejection
        action["status"] = "rejected"
        action["rejected_at"] = datetime.now(timezone.utc).isoformat()
        action["rejection_reason"] = reason
        category = args.get("category")
        if category:
            action["rejection_category"] = category
        _try_save_action(action, self._workspace_dir)

        title = action.get("title", action_id)
        output = (
            f"Rejected: {title}\n"
            f"  Action ID:  {action_id}\n"
            f"  Reason:     {reason}\n"
        )
        if category:
            output += f"  Category:   {category}\n"

        return CommandResult(
            success=True,
            command="reject",
            output=output,
            data=action,
            next_steps=["kai proposals  -- see updated queue"],
        )

    # --------------------------------------------------------------- execute

    def cmd_execute(self, args: Dict[str, Any]) -> CommandResult:
        """Execute an approved action.

        Args (in *args* dict):
            action_id -- required.
            dry_run   -- optional bool, default False.
        """
        action_id = args.get("action_id")
        dry_run = args.get("dry_run", False)
        if isinstance(dry_run, str):
            dry_run = dry_run.lower() in ("true", "1", "yes")

        if not action_id:
            return CommandResult(
                success=False,
                command="execute",
                errors=["Missing required argument: action_id"],
                next_steps=["kai execute <action_id>"],
            )

        action = _try_load_action(action_id, self._workspace_dir)
        if action is None:
            return CommandResult(
                success=False,
                command="execute",
                errors=[f"Action '{action_id}' not found"],
                next_steps=["kai proposals  -- list available proposals"],
            )

        if action.get("status") != "approved":
            return CommandResult(
                success=False,
                command="execute",
                errors=[f"Action '{action_id}' is not approved (status: {action.get('status', 'unknown')})"],
                next_steps=[f"kai approve {action_id}  -- approve first"],
            )

        title = action.get("title", action_id)
        action_type = action.get("action_type", "unknown")
        channel = action.get("channel", "unknown")

        if dry_run:
            output = (
                f"DRY RUN: {title}\n"
                f"  Action ID:    {action_id}\n"
                f"  Type:         {action_type}\n"
                f"  Channel:      {channel}\n"
                f"  Risk Tier:    {action.get('risk_tier', 'N/A')}\n"
                f"  Est. Cost:    ${action.get('estimated_cost', 0):,.2f}\n"
                f"  Description:  {truncate(action.get('description', ''), 60)}\n"
                f"\n"
                f"  No changes were made.  Remove --dry_run to execute.\n"
            )
            return CommandResult(
                success=True,
                command="execute",
                output=output,
                data={"dry_run": True, "action": action},
                next_steps=[f"kai execute {action_id}  -- execute for real"],
            )

        # Mark as in-progress
        action["status"] = "in_progress"
        action["executed_at"] = datetime.now(timezone.utc).isoformat()
        _try_save_action(action, self._workspace_dir)

        output = (
            f"Executing: {title}\n"
            f"  Action ID:    {action_id}\n"
            f"  Type:         {action_type}\n"
            f"  Channel:      {channel}\n"
            f"  Status:       in_progress\n"
        )

        return CommandResult(
            success=True,
            command="execute",
            output=output,
            data=action,
            next_steps=["kai status  -- monitor execution"],
        )

    # ---------------------------------------------------------------- status

    def cmd_status(self, args: Dict[str, Any]) -> CommandResult:
        """Show the system status dashboard."""
        # Gather data from multiple sources
        proposals = _try_load_proposals(self._business_id, self._workspace_dir)
        watcher_state = _try_load_watchers(self._business_id, self._workspace_dir)
        history = _try_load_history(self._business_id, self._workspace_dir, days=7, limit=5)

        # Pending actions by risk tier
        pending = [p for p in proposals if p.get("status") in ("proposed", "pending")]
        pending_by_tier: Dict[str, int] = {}
        for p in pending:
            tier = p.get("risk_tier", "unknown")
            pending_by_tier[tier] = pending_by_tier.get(tier, 0) + 1

        # Active campaigns (in_progress actions)
        active_campaigns = [
            {
                "name": p.get("title", "Unnamed"),
                "channel": p.get("channel", ""),
                "status": p.get("status", ""),
            }
            for p in proposals
            if p.get("status") == "in_progress"
        ]

        # Recent changes
        recent_actions = [
            {
                "timestamp": h.get("timestamp", h.get("created_at", "")),
                "title": h.get("title", ""),
                "status": h.get("status", ""),
            }
            for h in history[:5]
        ]

        # Watchers
        watchers_list = watcher_state.get("watchers", [])
        findings_list = watcher_state.get("findings", [])
        enabled_watchers = sum(1 for w in watchers_list if w.get("enabled", True))
        critical_alerts = [
            f for f in findings_list
            if f.get("severity") in ("critical", "high") and f.get("urgency", "") == "immediate"
        ]

        status_data: Dict[str, Any] = {
            "system_status": "active",
            "pending_actions": pending_by_tier,
            "active_campaigns": active_campaigns,
            "recent_actions": recent_actions,
            "active_watchers": enabled_watchers,
            "watcher_findings_today": len(findings_list),
            "critical_alerts": critical_alerts,
            "kill_switches_active": [],
        }

        output = format_status_dashboard(status_data)

        # Build contextual next steps
        next_steps: List[str] = []
        if pending:
            next_steps.append(f"kai proposals  -- {len(pending)} pending actions need review")
        if critical_alerts:
            next_steps.append("kai watchers --findings_only  -- review critical findings")
        if not next_steps:
            next_steps.append("kai audit  -- run a fresh audit")

        return CommandResult(
            success=True,
            command="status",
            output=output,
            data=status_data,
            next_steps=next_steps,
        )

    # --------------------------------------------------------------- history

    def cmd_history(self, args: Dict[str, Any]) -> CommandResult:
        """Show action history.

        Args (in *args* dict):
            days        -- number of days to look back (default 30).
            channel     -- optional channel filter.
            action_type -- optional type filter.
            limit       -- max results (default 50).
        """
        days = int(args.get("days", 30))
        channel = args.get("channel")
        action_type = args.get("action_type")
        limit = int(args.get("limit", 50))

        entries = _try_load_history(
            self._business_id,
            self._workspace_dir,
            days=days,
            channel=channel,
            action_type=action_type,
            limit=limit,
        )

        headers = ["Date", "Action", "Channel", "Status", "Outcome"]
        rows = [
            [
                str(e.get("timestamp", e.get("created_at", "")))[:10],
                truncate(str(e.get("title", e.get("action_type", ""))), 35),
                str(e.get("channel", "")),
                str(e.get("status", "")),
                truncate(str(e.get("outcome", "")), 25),
            ]
            for e in entries
        ]

        from kai.operator.formatters import align_table
        table = align_table(headers, rows)
        output = f"Action History (last {days} days, {len(entries)} entries)\n{'-' * 50}\n{table}"

        return CommandResult(
            success=True,
            command="history",
            output=output,
            data={"entries": entries, "count": len(entries)},
            next_steps=["kai status  -- current system state"],
        )

    # -------------------------------------------------------------- watchers

    def cmd_watchers(self, args: Dict[str, Any]) -> CommandResult:
        """Show active watchers and recent findings.

        Args (in *args* dict):
            watcher       -- optional specific watcher name to filter.
            findings_only -- optional bool, show only findings.
        """
        watcher_name = args.get("watcher")
        findings_only = args.get("findings_only", False)
        if isinstance(findings_only, str):
            findings_only = findings_only.lower() in ("true", "1", "yes")

        watcher_state = _try_load_watchers(self._business_id, self._workspace_dir)
        watchers_list = watcher_state.get("watchers", [])
        findings_list = watcher_state.get("findings", [])

        # Filter by specific watcher
        if watcher_name:
            watchers_list = [w for w in watchers_list if w.get("name") == watcher_name]
            findings_list = [f for f in findings_list if f.get("watcher") == watcher_name]

        if findings_only:
            output = format_watcher_findings(findings_list)
            next_steps: List[str] = []
            critical = [f for f in findings_list if f.get("severity") in ("critical", "high")]
            if critical:
                next_steps.append("kai proposals  -- check proposals generated from findings")
            else:
                next_steps.append("kai status  -- system overview")
            return CommandResult(
                success=True,
                command="watchers",
                output=output,
                data={"findings": findings_list},
                next_steps=next_steps,
            )

        # Full watcher listing
        lines: List[str] = []
        lines.append(f"Watchers ({len(watchers_list)} total)")
        lines.append("-" * 50)
        for w in watchers_list:
            name = w.get("name", "unnamed")
            enabled = w.get("enabled", True)
            last_run = w.get("last_run", "never")
            finding_count = sum(1 for f in findings_list if f.get("watcher") == name)
            status_tag = "enabled" if enabled else "disabled"
            lines.append(f"  {name:<25s}  [{status_tag}]  last_run: {last_run}  findings: {finding_count}")

        lines.append("")
        lines.append(format_watcher_findings(findings_list))

        next_steps_watchers: List[str] = ["kai watchers --findings_only  -- see only findings"]
        if findings_list:
            next_steps_watchers.append("kai proposals  -- see proposals from watcher findings")

        return CommandResult(
            success=True,
            command="watchers",
            output="\n".join(lines),
            data={"watchers": watchers_list, "findings": findings_list},
            next_steps=next_steps_watchers,
        )

    # ---------------------------------------------------------------- memory

    def cmd_memory(self, args: Dict[str, Any]) -> CommandResult:
        """Show key learnings and brand preferences.

        Args (in *args* dict):
            layer -- "brand", "channel", "proof", "offers", "audience",
                     or "all" (default "all").
        """
        layer = args.get("layer", "all")
        valid_layers = {"brand", "channel", "proof", "offers", "audience", "all"}
        if layer not in valid_layers:
            return CommandResult(
                success=False,
                command="memory",
                errors=[f"Invalid layer '{layer}'. Choose from: {', '.join(sorted(valid_layers))}"],
                next_steps=["kai memory --layer all"],
            )

        memories = _try_load_memory(self._business_id, self._workspace_dir, layer=layer)
        output = format_memory_summary(memories)

        return CommandResult(
            success=True,
            command="memory",
            output=output,
            data=memories,
            next_steps=["kai memory confirm <id>  -- confirm pending learnings"],
        )

    # --------------------------------------------------------------- profile

    def cmd_profile(self, args: Dict[str, Any]) -> CommandResult:
        """Show or edit the business profile.

        Args (in *args* dict):
            edit  -- bool, if True show editable fields or apply an edit.
            field -- specific field to show or edit.
            value -- new value for the field (requires field and edit=True).
        """
        edit = args.get("edit", False)
        if isinstance(edit, str):
            edit = edit.lower() in ("true", "1", "yes")
        field_name = args.get("field")
        new_value = args.get("value")

        profile = _try_load_profile(self._business_id, self._workspace_dir)
        if profile is None:
            return CommandResult(
                success=False,
                command="profile",
                output="No business profile found.",
                errors=[f"Profile for '{self._business_id}' not found in workspace"],
                next_steps=["Set up a business profile first."],
            )

        # Edit mode: update a specific field
        if edit and field_name and new_value is not None:
            if field_name in _PROFILE_READONLY_FIELDS:
                return CommandResult(
                    success=False,
                    command="profile",
                    errors=[f"Field '{field_name}' is read-only and cannot be edited"],
                    next_steps=["kai profile  -- view current profile"],
                )
            if field_name not in profile:
                return CommandResult(
                    success=False,
                    command="profile",
                    errors=[f"Field '{field_name}' does not exist in the profile"],
                    next_steps=["kai profile  -- view current profile with field names"],
                )
            old_value = profile[field_name]
            profile[field_name] = new_value
            _try_save_profile(profile, self._workspace_dir)

            output = (
                f"Updated profile field '{field_name}':\n"
                f"  Old: {old_value}\n"
                f"  New: {new_value}\n"
            )
            return CommandResult(
                success=True,
                command="profile",
                output=output,
                data=profile,
                next_steps=["kai profile  -- view updated profile"],
            )

        # Edit mode: show editable fields
        if edit:
            editable = [
                k for k in sorted(profile.keys())
                if k not in _PROFILE_READONLY_FIELDS
            ]
            lines = ["Editable fields:"]
            for k in editable:
                lines.append(f"  {k}: {truncate(str(profile[k]), 50)}")
            lines.append("")
            lines.append("To edit:  kai profile --edit --field <name> --value <new_value>")
            return CommandResult(
                success=True,
                command="profile",
                output="\n".join(lines),
                data={"editable_fields": editable, "profile": profile},
                next_steps=["kai profile --edit --field name --value 'New Name'"],
            )

        # View mode: show specific field
        if field_name:
            value = profile.get(field_name)
            if value is None:
                return CommandResult(
                    success=False,
                    command="profile",
                    errors=[f"Field '{field_name}' not found in profile"],
                    next_steps=["kai profile  -- view all fields"],
                )
            return CommandResult(
                success=True,
                command="profile",
                output=f"{field_name}: {value}",
                data={"field": field_name, "value": value},
                next_steps=["kai profile  -- view full profile"],
            )

        # Default: show full profile summary
        output = format_profile_summary(profile)
        return CommandResult(
            success=True,
            command="profile",
            output=output,
            data=profile,
            next_steps=["kai profile --edit  -- see editable fields"],
        )


# ============================================================================
# Command parsing
# ============================================================================


def parse_command(input_str: str) -> Tuple[str, Dict[str, Any]]:
    """Parse a raw input string into a command name and arguments dict.

    Supported formats::

        kai audit                                -> ("audit", {})
        kai audit --scope website                -> ("audit", {"scope": "website"})
        kai approve act_abc123                   -> ("approve", {"action_id": "act_abc123"})
        kai reject act_abc123 "too aggressive"   -> ("reject", {"action_id": "act_abc123", "reason": "too aggressive"})
        kai proposals --filter pending --channel email -> ("proposals", {"filter": "pending", "channel": "email"})

    The leading ``kai`` token is stripped if present.

    Parameters
    ----------
    input_str : str
        The raw user input.

    Returns
    -------
    tuple of (str, dict)
        ``(command_name, args_dict)``.
    """
    stripped = input_str.strip()
    if not stripped:
        return ("", {})

    # Use shlex for proper quoted-string handling.
    try:
        tokens = shlex.split(stripped)
    except ValueError:
        # Fallback to naive split if quotes are malformed.
        tokens = stripped.split()

    if not tokens:
        return ("", {})

    # Strip leading "kai" or "/kai"
    if tokens[0].lower() in ("kai", "/kai"):
        tokens = tokens[1:]

    if not tokens:
        return ("", {})

    command = tokens[0].lower()
    rest = tokens[1:]

    # Commands that take a positional action_id as their first argument.
    _action_id_commands = {"approve", "reject", "execute"}

    args: Dict[str, Any] = {}

    i = 0
    positional_index = 0
    while i < len(rest):
        token = rest[i]
        if token.startswith("--"):
            key = token.lstrip("-").replace("-", "_")
            # Check if next token is a value (not another flag).
            if i + 1 < len(rest) and not rest[i + 1].startswith("--"):
                args[key] = rest[i + 1]
                i += 2
            else:
                # Boolean flag
                args[key] = True
                i += 1
        else:
            # Positional argument
            if command in _action_id_commands:
                if positional_index == 0:
                    args["action_id"] = token
                elif positional_index == 1 and command == "reject":
                    args["reason"] = token
                else:
                    args.setdefault("extra", []).append(token)
            else:
                args.setdefault("extra", []).append(token)
            positional_index += 1
            i += 1

    # For reject, collect remaining positional args as part of reason.
    if command == "reject" and "extra" in args:
        existing_reason = args.get("reason", "")
        extra_parts = args.pop("extra")
        if existing_reason:
            args["reason"] = existing_reason + " " + " ".join(extra_parts)
        else:
            args["reason"] = " ".join(extra_parts)

    return (command, args)


# ============================================================================
# Command dispatch
# ============================================================================


# Map of command names to method names on LocalOperatorSurface.
_COMMAND_MAP: Dict[str, str] = {
    "audit": "cmd_audit",
    "proposals": "cmd_proposals",
    "approve": "cmd_approve",
    "reject": "cmd_reject",
    "execute": "cmd_execute",
    "status": "cmd_status",
    "history": "cmd_history",
    "watchers": "cmd_watchers",
    "memory": "cmd_memory",
    "profile": "cmd_profile",
}


def dispatch_command(
    surface: LocalOperatorSurface,
    command: str,
    args: Dict[str, Any],
) -> CommandResult:
    """Route a command string to the appropriate method on *surface*.

    Returns an error ``CommandResult`` for unknown commands, listing the
    available commands.

    Parameters
    ----------
    surface : LocalOperatorSurface
        The surface instance to dispatch against.
    command : str
        The command name (e.g. ``"audit"``).
    args : dict
        Parsed arguments for the command.

    Returns
    -------
    CommandResult
    """
    method_name = _COMMAND_MAP.get(command)
    if method_name is None:
        available = ", ".join(sorted(_COMMAND_MAP.keys()))
        return CommandResult(
            success=False,
            command=command or "(empty)",
            errors=[f"Unknown command: '{command}'"],
            next_steps=[f"Available commands: {available}"],
        )

    method = getattr(surface, method_name)
    return method(args)
