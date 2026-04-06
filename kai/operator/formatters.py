"""Plain-text formatters for the Kai local operator surface.

Every function in this module accepts structured data (dicts / lists) and
returns a human-readable string suitable for terminal output.  No ANSI
colour codes or external dependencies -- just alignment, borders, and
indentation.
"""

from __future__ import annotations

from typing import Any, Dict, List


# ============================================================================
# Helpers
# ============================================================================


def truncate(text: str, max_length: int) -> str:
    """Truncate *text* to *max_length* characters, appending ``...`` if cut.

    Returns the original string unchanged when it fits within the limit.
    A *max_length* of 3 or less returns the raw slice (no room for the
    ellipsis to be meaningful).
    """
    if len(text) <= max_length:
        return text
    if max_length <= 3:
        return text[:max_length]
    return text[: max_length - 3] + "..."


def align_table(headers: List[str], rows: List[List[str]], padding: int = 2) -> str:
    """Build an aligned plain-text table from *headers* and *rows*.

    Column widths are auto-detected from the widest cell in each column
    (including the header).  *padding* controls the minimum whitespace
    between columns.

    Returns a multi-line string with a header row, a separator row of
    dashes, and the data rows.
    """
    if not headers:
        return ""

    num_cols = len(headers)

    # Normalise rows: ensure every row has exactly num_cols cells.
    normalised_rows: List[List[str]] = []
    for row in rows:
        padded = list(row) + [""] * max(0, num_cols - len(row))
        normalised_rows.append(padded[:num_cols])

    # Compute column widths.
    col_widths = [len(h) for h in headers]
    for row in normalised_rows:
        for i, cell in enumerate(row):
            col_widths[i] = max(col_widths[i], len(cell))

    pad = " " * padding

    def _format_row(cells: List[str]) -> str:
        parts = [cell.ljust(col_widths[i]) for i, cell in enumerate(cells)]
        return pad.join(parts)

    lines: List[str] = []
    lines.append(_format_row(headers))
    lines.append(pad.join("-" * w for w in col_widths))
    for row in normalised_rows:
        lines.append(_format_row(row))

    return "\n".join(lines)


# ============================================================================
# Audit
# ============================================================================


def _score_bar(score: float, width: int = 20) -> str:
    """Return a simple ASCII bar representing *score* out of 100.

    Example for score=65, width=20::

        [=============       ] 65.0
    """
    filled = int(round(score / 100.0 * width))
    bar = "=" * filled + " " * (width - filled)
    return f"[{bar}] {score}"


def format_audit_summary(audit_result: Dict[str, Any]) -> str:
    """Format an audit result dictionary for terminal display.

    Sections:
    - Overall score with bar
    - Per-category scores with bars
    - Finding counts by severity
    - Top critical findings
    """
    lines: List[str] = []
    overall = audit_result.get("overall_health_score", 0.0)

    lines.append("=" * 60)
    lines.append("  MARKETING AUDIT SUMMARY")
    lines.append("=" * 60)
    lines.append("")
    lines.append(f"  Overall Health Score:  {_score_bar(overall)}")
    lines.append("")

    # Category scores
    category_scores = audit_result.get("category_scores", {})
    if category_scores:
        lines.append("  Category Scores")
        lines.append("  " + "-" * 56)
        for cat_id, scorecard in category_scores.items():
            if isinstance(scorecard, dict):
                name = scorecard.get("category_display_name", cat_id)
                score = scorecard.get("score", 0.0)
            else:
                name = getattr(scorecard, "category_display_name", cat_id)
                score = getattr(scorecard, "score", 0.0)
            lines.append(f"  {name:<30s}  {_score_bar(score)}")
        lines.append("")

    # Finding counts
    finding_counts: Dict[str, int] = {}
    severity_keys = ["critical", "high", "medium", "low", "info"]
    for key in severity_keys:
        count = audit_result.get(f"{key}_count", 0)
        if count:
            finding_counts[key] = count
    total = audit_result.get("total_findings", sum(finding_counts.values()))

    lines.append(f"  Total Findings: {total}")
    for sev in severity_keys:
        cnt = finding_counts.get(sev, 0)
        if cnt:
            label = sev.upper()
            lines.append(f"    {label:<12s} {cnt}")
    lines.append("")

    # Top findings
    top_findings = audit_result.get("findings", [])[:5]
    if top_findings:
        lines.append("  Top Findings")
        lines.append("  " + "-" * 56)
        for finding in top_findings:
            if isinstance(finding, dict):
                sev = finding.get("severity", "").upper()
                title = finding.get("title", "")
                rec = finding.get("recommendation", "")
            else:
                sev = getattr(finding, "severity", "").upper()
                title = getattr(finding, "title", "")
                rec = getattr(finding, "recommendation", "")
            lines.append(f"  [{sev}] {title}")
            if rec:
                lines.append(f"         -> {truncate(rec, 70)}")
        lines.append("")

    # Executive summary
    summary = audit_result.get("executive_summary", "")
    if summary:
        lines.append("  Summary")
        lines.append("  " + "-" * 56)
        # Word-wrap at ~70 chars
        words = summary.split()
        line = "  "
        for word in words:
            if len(line) + len(word) + 1 > 72:
                lines.append(line)
                line = "  " + word
            else:
                line = line + " " + word if line.strip() else "  " + word
        if line.strip():
            lines.append(line)
        lines.append("")

    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================================
# Proposals
# ============================================================================


def format_proposal_table(proposals: List[Dict[str, Any]]) -> str:
    """Format a list of proposals as an aligned text table.

    Columns: ID (truncated to 16), Title (max 50), Channel, Risk Tier,
    Priority, Status.
    """
    headers = ["ID", "Title", "Channel", "Risk", "Priority", "Status"]
    rows: List[List[str]] = []
    for p in proposals:
        rows.append([
            truncate(str(p.get("id", "")), 16),
            truncate(str(p.get("title", "")), 50),
            str(p.get("channel", "")),
            str(p.get("risk_tier", "")),
            str(p.get("priority_score", p.get("priority", ""))),
            str(p.get("status", "")),
        ])

    header_line = f"Proposals ({len(proposals)} shown)"
    separator = "-" * len(header_line)
    table = align_table(headers, rows)
    return f"{header_line}\n{separator}\n{table}"


# ============================================================================
# Action detail
# ============================================================================


def format_action_detail(action: Dict[str, Any]) -> str:
    """Format a single action's full details for terminal display."""
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append(f"  Action: {action.get('id', 'N/A')}")
    lines.append("=" * 60)

    field_order = [
        ("title", "Title"),
        ("action_type", "Type"),
        ("channel", "Channel"),
        ("status", "Status"),
        ("risk_tier", "Risk Tier"),
        ("approval_requirement", "Approval"),
        ("description", "Description"),
        ("reason", "Reason"),
        ("business_impact", "Impact"),
        ("expected_outcome", "Expected Outcome"),
        ("estimated_effort", "Effort"),
        ("estimated_cost", "Est. Cost"),
        ("priority_score", "Priority Score"),
        ("created_at", "Created"),
    ]

    for key, label in field_order:
        value = action.get(key)
        if value is not None and value != "" and value != []:
            display = str(value)
            if key == "estimated_cost" and isinstance(value, (int, float)):
                display = f"${value:,.2f}"
            lines.append(f"  {label:<20s} {display}")

    # Content preview
    payload = action.get("suggested_payload", {})
    if isinstance(payload, dict):
        preview_text = payload.get("preview", payload.get("content", ""))
        if preview_text:
            lines.append("")
            lines.append("  Content Preview")
            lines.append("  " + "-" * 40)
            preview_str = str(preview_text)
            for pline in preview_str.split("\n")[:10]:
                lines.append(f"  {pline}")
            if len(preview_str.split("\n")) > 10:
                lines.append("  ... (truncated)")

    # Dependencies
    deps = action.get("depends_on", [])
    if deps:
        lines.append("")
        lines.append(f"  Depends On: {', '.join(deps)}")

    # Tags
    tags = action.get("tags", [])
    if tags:
        lines.append(f"  Tags: {', '.join(tags)}")

    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================================
# Status dashboard
# ============================================================================


def format_status_dashboard(status: Dict[str, Any]) -> str:
    """Format system status as a multi-section dashboard."""
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("  KAI SYSTEM STATUS")
    lines.append("=" * 60)

    # System health
    system_status = status.get("system_status", "unknown")
    lines.append("")
    lines.append(f"  System Health:  {system_status.upper()}")

    # Pending actions
    pending = status.get("pending_actions", {})
    if pending:
        lines.append("")
        lines.append("  Pending Actions by Risk Tier")
        lines.append("  " + "-" * 40)
        for tier, count in pending.items():
            lines.append(f"    {tier:<12s} {count}")

    # Active campaigns
    campaigns = status.get("active_campaigns", [])
    if campaigns:
        lines.append("")
        lines.append("  Active Campaigns")
        lines.append("  " + "-" * 40)
        for camp in campaigns[:10]:
            name = camp.get("name", "Unnamed")
            channel = camp.get("channel", "")
            camp_status = camp.get("status", "")
            lines.append(f"    {name}  [{channel}]  {camp_status}")

    # Recent actions
    recent = status.get("recent_actions", [])
    if recent:
        lines.append("")
        lines.append("  Recent Actions")
        lines.append("  " + "-" * 40)
        for act in recent[:5]:
            ts = act.get("timestamp", act.get("created_at", ""))
            title = truncate(act.get("title", ""), 40)
            act_status = act.get("status", "")
            lines.append(f"    {ts}  {title}  [{act_status}]")

    # Watchers
    watcher_count = status.get("active_watchers", 0)
    watcher_findings = status.get("watcher_findings_today", 0)
    lines.append("")
    lines.append(f"  Active Watchers: {watcher_count}   Findings Today: {watcher_findings}")

    # Alerts
    alerts = status.get("critical_alerts", [])
    if alerts:
        lines.append("")
        lines.append("  CRITICAL ALERTS")
        lines.append("  " + "-" * 40)
        for alert in alerts:
            title = alert.get("title", "")
            lines.append(f"    [!] {title}")

    # Kill switches
    kill_switches = status.get("kill_switches_active", [])
    if kill_switches:
        lines.append("")
        lines.append("  KILL SWITCHES ACTIVE")
        lines.append("  " + "-" * 40)
        for ks in kill_switches:
            channel = ks.get("channel", "")
            reason = ks.get("reason", "")
            lines.append(f"    {channel}: {reason}")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================================
# Watcher findings
# ============================================================================


_SEVERITY_ICONS = {
    "critical": "[!]",
    "high": "[*]",
    "medium": "[-]",
    "low": "[ ]",
    "info": "[ ]",
}

_SEVERITY_ORDER = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}


def format_watcher_findings(findings: List[Dict[str, Any]]) -> str:
    """Format watcher findings sorted by severity."""
    sorted_findings = sorted(
        findings,
        key=lambda f: _SEVERITY_ORDER.get(
            f.get("severity", "info"), 99
        ),
    )

    lines: List[str] = []
    lines.append(f"Watcher Findings ({len(findings)} total)")
    lines.append("-" * 50)

    if not sorted_findings:
        lines.append("  No findings.")
        return "\n".join(lines)

    for finding in sorted_findings:
        severity = finding.get("severity", "info")
        icon = _SEVERITY_ICONS.get(severity, "[ ]")
        title = finding.get("title", "Untitled")
        watcher = finding.get("watcher", "")
        desc = finding.get("description", "")

        header = f"  {icon} {title}"
        if watcher:
            header += f"  (via {watcher})"
        lines.append(header)
        if desc:
            lines.append(f"       {truncate(desc, 70)}")

    return "\n".join(lines)


# ============================================================================
# Memory summary
# ============================================================================


def format_memory_summary(memories: Dict[str, Any]) -> str:
    """Format memory / learning summary by category."""
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("  MEMORY & LEARNINGS")
    lines.append("=" * 60)

    if not memories:
        lines.append("  No stored learnings.")
        lines.append("=" * 60)
        return "\n".join(lines)

    for category, entries in memories.items():
        if isinstance(entries, list):
            count = len(entries)
        elif isinstance(entries, dict):
            count = entries.get("count", len(entries))
        else:
            count = 1

        lines.append("")
        display_name = category.replace("_", " ").title()
        lines.append(f"  {display_name} ({count} entries)")
        lines.append("  " + "-" * 40)

        if isinstance(entries, list):
            for entry in entries[:5]:
                if isinstance(entry, dict):
                    key = entry.get("key", entry.get("title", ""))
                    value = entry.get("value", entry.get("summary", ""))
                    confirmed = entry.get("confirmed", True)
                    status_tag = "" if confirmed else " [PENDING]"
                    lines.append(f"    {key}: {truncate(str(value), 50)}{status_tag}")
                else:
                    lines.append(f"    {truncate(str(entry), 60)}")
            if isinstance(entries, list) and len(entries) > 5:
                lines.append(f"    ... and {len(entries) - 5} more")
        elif isinstance(entries, dict):
            highlights = entries.get("highlights", [])
            for h in highlights[:5]:
                lines.append(f"    {truncate(str(h), 60)}")
            pending = entries.get("pending_count", 0)
            if pending:
                lines.append(f"    ({pending} pending confirmation)")

    lines.append("")
    lines.append("=" * 60)
    return "\n".join(lines)


# ============================================================================
# Profile summary
# ============================================================================


def format_profile_summary(profile: Dict[str, Any]) -> str:
    """Format a business profile for display."""
    lines: List[str] = []
    lines.append("=" * 60)
    lines.append("  BUSINESS PROFILE")
    lines.append("=" * 60)

    field_map = [
        ("business_id", "Business ID"),
        ("name", "Name"),
        ("archetype", "Archetype"),
        ("url", "Website"),
        ("service_area", "Service Area"),
        ("description", "Description"),
    ]

    for key, label in field_map:
        value = profile.get(key)
        if value:
            lines.append(f"  {label:<20s} {value}")

    # Active channels
    channels = profile.get("active_channels", [])
    if channels:
        lines.append(f"  {'Active Channels':<20s} {', '.join(channels)}")

    # Primary offers
    offers = profile.get("primary_offers", profile.get("offers", []))
    if offers:
        lines.append("")
        lines.append("  Primary Offers")
        lines.append("  " + "-" * 40)
        for offer in offers[:10]:
            if isinstance(offer, dict):
                lines.append(f"    {offer.get('name', str(offer))}")
            else:
                lines.append(f"    {offer}")

    lines.append("=" * 60)
    return "\n".join(lines)
