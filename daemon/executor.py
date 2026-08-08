"""Task executor using Claude Agent SDK.

Spawns Claude Code via the official SDK, streams messages to Supabase
for real-time dashboard visibility, and handles completion/failure.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

from .config import DaemonConfig
from .models import AgentTask, MessageType, TaskResult, TaskStatus
from . import injector

logger = logging.getLogger(__name__)

# Permission mode per risk tier
PERMISSION_MODES = {
    "low": "acceptEdits",
    "medium": "acceptEdits",
    "high": "dontAsk",
}

# Tool sets per task type
TOOL_SETS: dict[str, list[str]] = {
    "audit": ["Read", "Glob", "Grep", "WebFetch", "WebSearch", "Bash"],
    "content": ["Read", "Edit", "Write", "Glob", "Grep", "WebFetch", "WebSearch"],
    "seo": ["Read", "Glob", "Grep", "WebFetch", "WebSearch", "Bash"],
    "ads": ["Read", "Glob", "Grep", "WebFetch"],
    "email": ["Read", "Edit", "Write", "Glob", "Grep", "WebFetch"],
    "social": ["Read", "Edit", "Write", "Glob", "Grep", "WebFetch"],
    "analytics": ["Read", "Glob", "Grep", "Bash"],
    "competitors": ["Read", "Glob", "Grep", "WebFetch", "WebSearch"],
    "landing_page": ["Read", "Edit", "Write", "Glob", "Grep", "WebFetch"],
    "brand": ["Read", "Glob", "Grep", "WebFetch", "WebSearch"],
    "outreach": ["Read", "Edit", "Write", "Glob", "Grep", "WebFetch"],
    "launch": ["Read", "Edit", "Write", "Glob", "Grep", "WebFetch", "WebSearch"],
}

DEFAULT_TOOLS = ["Read", "Glob", "Grep", "WebFetch"]

# Fallback when risk_tier is missing or unrecognised. Must stay the least
# capable entry in PERMISSION_MODES.
LEAST_PERMISSIVE_MODE = "acceptEdits"

# The only variables the agent subprocess is allowed to see. Everything else --
# every API key, every service-role credential -- is withheld. Add to this list
# deliberately, and never add a secret that the agent could exfiltrate by
# printing it.
SUBPROCESS_ENV_ALLOWLIST = (
    "PATH",
    "HOME",
    "USER",
    "LOGNAME",
    "SHELL",
    "LANG",
    "LC_ALL",
    "TZ",
    "TMPDIR",
    "TEMP",
    "TMP",
    "SYSTEMROOT",
    "COMSPEC",
    "PATHEXT",
    "NUMBER_OF_PROCESSORS",
    "PROCESSOR_ARCHITECTURE",
    # Claude Code needs its own credential to run at all.
    "ANTHROPIC_API_KEY",
    "CLAUDE_CODE_OAUTH_TOKEN",
)


def _subprocess_env() -> dict[str, str]:
    """Build the minimal environment for the agent subprocess."""
    return {
        name: os.environ[name]
        for name in SUBPROCESS_ENV_ALLOWLIST
        if name in os.environ
    }


async def execute_task(
    task: AgentTask,
    config: DaemonConfig,
    supabase_client,
) -> TaskResult:
    """Execute a task using the Claude Agent SDK.

    Args:
        task: The claimed task to execute
        config: Daemon configuration
        supabase_client: Supabase client (service_role) for streaming messages

    Returns:
        TaskResult with status, output, session_id, cost
    """
    try:
        from claude_agent_sdk import query, ClaudeAgentOptions
        from claude_agent_sdk.types import (
            AssistantMessage,
            ResultMessage,
            SystemMessage,
        )
    except ImportError:
        logger.error("claude-agent-sdk not installed. Run: pip install claude-agent-sdk")
        return TaskResult(
            status=TaskStatus.FAILED,
            error="claude-agent-sdk not installed",
        )

    # 1. Prepare isolated workdir with skills + knowledge
    workdir = injector.prepare_workdir(task, config)
    logger.info("Workdir prepared: %s", workdir)

    # 2. Build prompt
    prompt = _build_prompt(task)

    # 3. Determine permissions and tools
    #
    # Both of these are selected by columns on agent_runs, which are written by
    # callers rather than by this process. Unknown values must therefore fail
    # toward *less* capability, not more. DEFAULT_TOOLS already does the right
    # thing (no Bash); risk_tier did not -- an unrecognised value fell through
    # to "dontAsk", the most permissive mode of the three, so a typo or a
    # hostile row bought more permission than "high" was ever meant to grant.
    tools = TOOL_SETS.get(task.task_type, DEFAULT_TOOLS)
    if task.task_type not in TOOL_SETS:
        logger.warning(
            "Unknown task_type %r for run %s; using restricted default tool set",
            task.task_type, task.id,
        )

    perm_mode = PERMISSION_MODES.get(task.risk_tier)
    if perm_mode is None:
        perm_mode = LEAST_PERMISSIVE_MODE
        logger.warning(
            "Unknown risk_tier %r for run %s; using least permissive mode %r",
            task.risk_tier, task.id, perm_mode,
        )

    # 4. Build SDK options
    options = ClaudeAgentOptions(
        allowed_tools=tools,
        permission_mode=perm_mode,
        max_turns=config.max_turns_per_task,
        max_budget_usd=config.max_budget_per_task,
        cwd=str(workdir),
        model=config.claude_model,
        persist_session=True,
        # Without this the subprocess inherits the daemon's entire environment,
        # which holds SUPABASE_SERVICE_ROLE_KEY (RLS-bypassing), ANTHROPIC_API_KEY,
        # META_ACCESS_TOKEN and every other product credential. Several task types
        # grant Bash, and the task's `input` is attacker-influenced text that lands
        # in the prompt -- so `env` printed one variable away from a full breach.
        env=_subprocess_env(),
    )

    # Resume prior session if this is a continuation
    if task.prior_session_id:
        options.resume = task.prior_session_id

    # 5. Execute via SDK — stream messages to Supabase
    seq = 0
    session_id = None
    final_result = None
    total_cost = 0.0
    num_turns = 0
    messages_batch: List[Dict[str, Any]] = []

    try:
        async for message in query(prompt=prompt, options=options):

            if isinstance(message, SystemMessage):
                if hasattr(message, "subtype") and message.subtype == "init":
                    session_id = message.data.get("session_id") if hasattr(message, "data") else None

            elif isinstance(message, AssistantMessage):
                for block in message.content:
                    msg_type, content, metadata = _parse_content_block(block)
                    if msg_type:
                        messages_batch.append({
                            "run_id": task.id,
                            "brand_id": task.brand_id,
                            "seq": seq,
                            "msg_type": msg_type,
                            "content": content,
                            "metadata": metadata,
                        })
                        seq += 1

                # Flush batch every 10 messages
                if len(messages_batch) >= 10:
                    await _flush_messages(supabase_client, messages_batch)

            elif isinstance(message, ResultMessage):
                session_id = getattr(message, "session_id", session_id)
                total_cost = getattr(message, "total_cost_usd", 0.0)
                num_turns = getattr(message, "num_turns", 0)
                final_result = getattr(message, "result", "")
                stop_reason = getattr(message, "stop_reason", "success")

                # Flush remaining messages
                if messages_batch:
                    await _flush_messages(supabase_client, messages_batch)

                if stop_reason == "success":
                    return TaskResult(
                        status=TaskStatus.COMPLETED,
                        output={"result": final_result, "cost_usd": total_cost},
                        session_id=session_id,
                        work_dir=str(workdir),
                        cost_usd=total_cost,
                        num_turns=num_turns,
                    )
                else:
                    return TaskResult(
                        status=TaskStatus.FAILED,
                        output={"partial_result": final_result, "cost_usd": total_cost},
                        error=f"Stop reason: {stop_reason}",
                        session_id=session_id,
                        work_dir=str(workdir),
                        cost_usd=total_cost,
                        num_turns=num_turns,
                    )

    except Exception as e:
        logger.exception("Task execution failed: %s", task.id)
        if messages_batch:
            try:
                await _flush_messages(supabase_client, messages_batch)
            except Exception:
                pass
        return TaskResult(
            status=TaskStatus.FAILED,
            error=str(e),
            session_id=session_id,
            work_dir=str(workdir),
            cost_usd=total_cost,
        )

    # Fallback — shouldn't reach here normally
    return TaskResult(
        status=TaskStatus.FAILED,
        error="Execution ended without ResultMessage",
        session_id=session_id,
        work_dir=str(workdir),
    )


def _build_prompt(task: AgentTask) -> str:
    """Build the prompt sent to Claude Code."""
    input_json = json.dumps(task.input or {}, indent=2)

    prompt = f"""You are executing an autonomous marketing task.

Task Type: {task.task_type}
Skill: {task.skill or 'auto-select based on task type'}

Read context/task.md for full details. Your input parameters:

```json
{input_json}
```

Execute this task completely. Write all deliverables to ../output/.
Apply quality gates to any content you produce.
"""
    return prompt


def _parse_content_block(block) -> tuple[Optional[str], str, Dict[str, Any]]:
    """Parse a content block from AssistantMessage into (msg_type, content, metadata)."""
    block_type = getattr(block, "type", None)

    if block_type == "text" or hasattr(block, "text"):
        text = getattr(block, "text", str(block))
        return MessageType.TEXT, text, {}

    elif block_type == "tool_use" or hasattr(block, "name"):
        name = getattr(block, "name", "unknown")
        inp = getattr(block, "input", {})
        return MessageType.TOOL_USE, name, {"input": _truncate(inp, 8192)}

    elif block_type == "thinking" or hasattr(block, "thinking"):
        thinking = getattr(block, "thinking", str(block))
        return MessageType.THINKING, thinking[:2000], {}

    return None, "", {}


async def _flush_messages(supabase_client, batch: List[Dict[str, Any]]):
    """Write message batch directly to Supabase (bypasses gateway for speed)."""
    if not batch:
        return
    try:
        supabase_client.table("agent_messages").insert(list(batch)).execute()
    except Exception as e:
        logger.warning("Failed to flush %d messages: %s", len(batch), e)
    batch.clear()


def _truncate(data: Any, max_len: int) -> Any:
    """Truncate data to prevent oversized DB writes."""
    s = json.dumps(data) if isinstance(data, dict) else str(data)
    if len(s) > max_len:
        return {"_truncated": True, "preview": s[:max_len]}
    return data
