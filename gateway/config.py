"""
Gateway configuration - loads clients_config.json and environment variables.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv

# Load environment from scripts/.env
_env_path = Path(__file__).parent.parent / "scripts" / ".env"
load_dotenv(_env_path)

# Also try root .env
_root_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env)


class GatewayConfig:
    """Configuration manager for the gateway."""

    def __init__(self):
        self._clients_config: Optional[Dict] = None
        self._config_path = Path(__file__).parent.parent / "clients" / "clients_config.json"

    @property
    def api_key(self) -> str:
        """Get the API key for authentication."""
        return os.getenv("CMO_GATEWAY_API_KEY", "")

    @property
    def host(self) -> str:
        """Get the host to bind to."""
        return os.getenv("CMO_GATEWAY_HOST", "0.0.0.0")

    @property
    def port(self) -> int:
        """Get the port to bind to."""
        return int(os.getenv("CMO_GATEWAY_PORT", "8088"))

    @property
    def debug(self) -> bool:
        """Check if debug mode is enabled."""
        return os.getenv("CMO_GATEWAY_DEBUG", "false").lower() == "true"

    @property
    def clients_config(self) -> Dict:
        """Load and cache clients_config.json."""
        if self._clients_config is None:
            if self._config_path.exists():
                with open(self._config_path) as f:
                    self._clients_config = json.load(f)
            else:
                self._clients_config = {}
        return self._clients_config

    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get all clients from config with their category."""
        clients = []
        config = self.clients_config

        for category in ["products", "clients", "leadgen", "personal", "internal"]:
            category_items = config.get(category, {})
            for client_id, client_data in category_items.items():
                clients.append({
                    "id": client_id,
                    "category": category,
                    **client_data
                })

        return clients

    def get_client(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific client by ID."""
        config = self.clients_config

        for category in ["products", "clients", "leadgen", "personal", "internal"]:
            category_items = config.get(category, {})
            if client_id in category_items:
                return {
                    "id": client_id,
                    "category": category,
                    **category_items[client_id]
                }

        return None

    def get_ga_property(self, client_id: str) -> Optional[str]:
        """Get Google Analytics property ID for a client."""
        client = self.get_client(client_id)
        return client.get("ga_property") if client else None

    def get_gsc_site(self, client_id: str) -> Optional[str]:
        """Get Google Search Console site URL for a client."""
        client = self.get_client(client_id)
        return client.get("gsc_site") if client else None

    def get_supabase_config(self, client_id: str) -> Optional[Dict]:
        """Get Supabase configuration for a client."""
        client = self.get_client(client_id)
        return client.get("supabase") if client else None


# Global config instance
config = GatewayConfig()
