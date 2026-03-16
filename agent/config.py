"""
Agent configuration - environment variables and defaults.
"""

import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# Load environment from scripts/.env and root .env
_env_path = Path(__file__).parent.parent / "scripts" / ".env"
load_dotenv(_env_path)
_root_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env)


class AgentConfig:
    """Configuration manager for the autonomous agent."""

    def __init__(self):
        self._db_path: Optional[Path] = None

    # -------------------------------------------------------------------------
    # Database
    # -------------------------------------------------------------------------
    @property
    def db_path(self) -> Path:
        """Get the path to the agent SQLite database."""
        if self._db_path is None:
            self._db_path = Path(__file__).parent / "agent.db"
        return self._db_path

    # -------------------------------------------------------------------------
    # Twilio WhatsApp
    # -------------------------------------------------------------------------
    @property
    def twilio_account_sid(self) -> str:
        return os.getenv("TWILIO_ACCOUNT_SID", "")

    @property
    def twilio_auth_token(self) -> str:
        return os.getenv("TWILIO_AUTH_TOKEN", "")

    @property
    def twilio_whatsapp_number(self) -> str:
        """Twilio WhatsApp sandbox or business number."""
        return os.getenv("TWILIO_WHATSAPP_NUMBER", "+14155238886")

    @property
    def agent_owner_phone(self) -> str:
        """Owner's WhatsApp number for notifications."""
        return os.getenv("AGENT_OWNER_PHONE", "")

    # -------------------------------------------------------------------------
    # LLM Models
    # -------------------------------------------------------------------------
    @property
    def anthropic_api_key(self) -> str:
        return os.getenv("ANTHROPIC_API_KEY", "")

    @property
    def default_model(self) -> str:
        """Default model for routine tasks (cost-optimized)."""
        return os.getenv("AGENT_DEFAULT_MODEL", "claude-3-5-haiku-20241022")

    @property
    def opus_model(self) -> str:
        """Opus model for complex reasoning tasks."""
        return os.getenv("AGENT_OPUS_MODEL", "claude-opus-4-5-20251101")

    @property
    def haiku_model(self) -> str:
        """Haiku model for simple/fast tasks."""
        return os.getenv("AGENT_HAIKU_MODEL", "claude-3-5-haiku-20241022")

    # -------------------------------------------------------------------------
    # Agent Behavior
    # -------------------------------------------------------------------------
    @property
    def polling_interval(self) -> int:
        """Seconds between scheduler checks."""
        return int(os.getenv("AGENT_POLLING_INTERVAL", "60"))

    @property
    def max_concurrent_tasks(self) -> int:
        """Maximum tasks to run in parallel."""
        return int(os.getenv("AGENT_MAX_CONCURRENT_TASKS", "3"))

    @property
    def task_timeout(self) -> int:
        """Default task timeout in seconds."""
        return int(os.getenv("AGENT_TASK_TIMEOUT", "300"))

    @property
    def retry_attempts(self) -> int:
        """Number of retry attempts for failed tasks."""
        return int(os.getenv("AGENT_RETRY_ATTEMPTS", "3"))

    @property
    def retry_delay(self) -> int:
        """Delay between retries in seconds."""
        return int(os.getenv("AGENT_RETRY_DELAY", "60"))

    # -------------------------------------------------------------------------
    # Notifications
    # -------------------------------------------------------------------------
    @property
    def notify_on_failure(self) -> bool:
        """Send WhatsApp notification on task failure."""
        return os.getenv("AGENT_NOTIFY_ON_FAILURE", "true").lower() == "true"

    @property
    def notify_on_approval(self) -> bool:
        """Send WhatsApp notification when approval is needed."""
        return os.getenv("AGENT_NOTIFY_ON_APPROVAL", "true").lower() == "true"

    @property
    def daily_summary_enabled(self) -> bool:
        """Send daily summary to owner."""
        return os.getenv("AGENT_DAILY_SUMMARY", "true").lower() == "true"

    # -------------------------------------------------------------------------
    # Discord
    # -------------------------------------------------------------------------
    @property
    def discord_bot_token(self) -> str:
        return os.getenv("DISCORD_BOT_TOKEN", "")

    @property
    def discord_channel_id(self) -> str:
        """Default Discord channel for notifications."""
        return os.getenv("DISCORD_CHANNEL_ID", "")

    # -------------------------------------------------------------------------
    # Feature Flags
    # -------------------------------------------------------------------------
    @property
    def whatsapp_enabled(self) -> bool:
        """Enable WhatsApp channel."""
        return os.getenv("AGENT_WHATSAPP_ENABLED", "true").lower() == "true"

    @property
    def discord_enabled(self) -> bool:
        """Enable Discord channel."""
        return os.getenv("AGENT_DISCORD_ENABLED", "true").lower() == "true"

    @property
    def scheduler_enabled(self) -> bool:
        """Enable scheduled task execution."""
        return os.getenv("AGENT_SCHEDULER_ENABLED", "true").lower() == "true"


# Global config instance
agent_config = AgentConfig()
