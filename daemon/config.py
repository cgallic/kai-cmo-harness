"""Daemon configuration — environment variables and defaults."""

import os
import socket
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class DaemonConfig:
    """Configuration for the MeetKai daemon process."""

    # Gateway connection
    gateway_url: str = ""
    gateway_key: str = ""

    # Supabase (direct writes for high-frequency streaming)
    supabase_url: str = ""
    supabase_service_key: str = ""  # service_role key — bypasses RLS

    # Daemon identity
    daemon_id: str = ""
    daemon_name: str = ""
    runtime_id: Optional[str] = None  # Assigned after registration

    # Polling
    poll_interval: int = 3       # seconds between task checks
    heartbeat_interval: int = 15  # seconds between heartbeats

    # Execution limits
    max_concurrent: int = 4
    agent_timeout: int = 7200     # 2 hours max per task
    max_budget_per_task: float = 5.0  # USD cost cap per task
    max_turns_per_task: int = 30

    # Paths
    workspaces_root: str = ""
    skills_path: str = ""
    knowledge_path: str = ""

    # Claude Code
    claude_model: str = "claude-sonnet-4-6"

    @classmethod
    def from_env(cls) -> "DaemonConfig":
        """Load configuration from environment variables."""
        project_root = Path(__file__).parent.parent

        return cls(
            gateway_url=os.getenv("MEETKAI_GATEWAY_URL", "http://localhost:8088"),
            gateway_key=os.getenv("CMO_GATEWAY_API_KEY", ""),
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_service_key=os.getenv("SUPABASE_SERVICE_ROLE_KEY", ""),
            daemon_id=os.getenv("MEETKAI_DAEMON_ID", socket.gethostname()),
            daemon_name=os.getenv("MEETKAI_DAEMON_NAME", f"Claude-Code-{socket.gethostname()}"),
            poll_interval=int(os.getenv("MEETKAI_POLL_INTERVAL", "3")),
            heartbeat_interval=int(os.getenv("MEETKAI_HEARTBEAT_INTERVAL", "15")),
            max_concurrent=int(os.getenv("MEETKAI_MAX_CONCURRENT", "4")),
            agent_timeout=int(os.getenv("MEETKAI_AGENT_TIMEOUT", "7200")),
            max_budget_per_task=float(os.getenv("MEETKAI_MAX_BUDGET", "5.0")),
            max_turns_per_task=int(os.getenv("MEETKAI_MAX_TURNS", "30")),
            workspaces_root=os.getenv(
                "MEETKAI_WORKSPACES_ROOT",
                str(Path.home() / "meetkai_workspaces"),
            ),
            skills_path=os.getenv(
                "MEETKAI_SKILLS_PATH",
                str(project_root / "harness" / "skills"),
            ),
            knowledge_path=os.getenv(
                "MEETKAI_KNOWLEDGE_PATH",
                str(project_root / "knowledge"),
            ),
            claude_model=os.getenv("MEETKAI_CLAUDE_MODEL", "claude-sonnet-4-6"),
        )
