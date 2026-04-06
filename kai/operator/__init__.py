"""Kai Operator Surface Layer.

The operator surface is the interface between the Kai marketing runtime
and the humans who oversee it.  There are two surfaces:

- **LocalOperatorSurface** -- command-line / Claude Code interaction.
  Parses ``/kai`` commands, dispatches them to the runtime, and renders
  results as formatted plain-text output suitable for a terminal.

- **RemoteOperatorSurface** -- HTTP API interaction via the FastAPI
  gateway.  Returns structured JSON response models that front-end
  dashboards, mobile apps, and third-party integrations consume.

Both surfaces expose the same capabilities (audit, proposals, approve,
reject, execute, status, history, watchers, memory, profile) but differ
in their I/O format: text strings vs. JSON-serializable response models.
"""

from kai.operator.local_surface import (
    CommandResult,
    LocalOperatorSurface,
    dispatch_command,
    parse_command,
)
from kai.operator.formatters import (
    align_table,
    format_action_detail,
    format_audit_summary,
    format_memory_summary,
    format_profile_summary,
    format_proposal_table,
    format_status_dashboard,
    format_watcher_findings,
    truncate,
)

__all__ = [
    "CommandResult",
    "LocalOperatorSurface",
    "dispatch_command",
    "parse_command",
    "align_table",
    "format_action_detail",
    "format_audit_summary",
    "format_memory_summary",
    "format_profile_summary",
    "format_proposal_table",
    "format_status_dashboard",
    "format_watcher_findings",
    "truncate",
]
