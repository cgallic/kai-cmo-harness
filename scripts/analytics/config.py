"""
Analytics System Configuration

All credentials are loaded from environment variables.
See scripts/.env.example for required variables.
"""

import os
import json
from dataclasses import dataclass
from pathlib import Path


def load_dotenv():
    """Load .env file from scripts directory"""
    env_paths = [
        Path(__file__).parent.parent / ".env",  # scripts/.env
        Path(__file__).parent / ".env",  # scripts/analytics/.env
        Path.home() / ".cmo-agent.env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip().strip('"\''))
            break


# Load environment on import
load_dotenv()


@dataclass
class Config:
    """Central configuration for analytics system

    All values loaded from environment variables.
    Set these in scripts/.env or export them in your shell.
    """

    # Supabase - loaded from env
    supabase_url: str = ""
    supabase_key: str = ""
    default_business_id: str = ""

    # Google Analytics
    ga_property_id: str = ""
    ga_credentials_path: str = ""

    # Google Search Console
    gsc_site_url: str = ""
    gsc_credentials_path: str = ""

    # Defaults
    default_date_range: int = 30  # days
    default_limit: int = 50

    @classmethod
    def from_env(cls) -> "Config":
        """Load config from environment variables"""
        # Look for credentials in repo first, then fallback to home directory
        repo_creds = Path(__file__).parent / "credentials" / "google-analytics-credentials.json"
        home_creds = Path.home() / ".claude" / "google-analytics-credentials.json"

        if repo_creds.exists():
            default_creds = str(repo_creds)
        elif home_creds.exists():
            default_creds = str(home_creds)
        else:
            default_creds = str(repo_creds)  # Will fail with clear error

        creds_path = os.getenv("GOOGLE_CREDENTIALS_PATH", default_creds)
        return cls(
            supabase_url=os.getenv("SUPABASE_URL", ""),
            supabase_key=os.getenv("SUPABASE_SERVICE_KEY", ""),
            default_business_id=os.getenv("DEFAULT_BUSINESS_ID", ""),
            ga_property_id=os.getenv("GA_PROPERTY_ID", ""),
            ga_credentials_path=os.getenv("GA_CREDENTIALS_PATH", creds_path),
            gsc_site_url=os.getenv("GSC_SITE_URL", ""),
            gsc_credentials_path=os.getenv("GSC_CREDENTIALS_PATH", creds_path),
        )

    def is_configured(self) -> bool:
        """Check if required credentials are set"""
        return bool(self.supabase_url and self.supabase_key)


# Global config instance
config = Config.from_env()
