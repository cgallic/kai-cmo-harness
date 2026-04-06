"""Gateway configuration for the Kai runtime remote surface."""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    def load_dotenv(*args, **kwargs):
        return False
from kai.runtime import load_workspace_profile

# Load environment from scripts/.env
_env_path = Path(__file__).parent.parent / "scripts" / ".env"
load_dotenv(_env_path)

# Also try root .env
_root_env = Path(__file__).parent.parent / ".env"
load_dotenv(_root_env)


class GatewayConfig:
    """Configuration manager for the Kai remote runner."""

    def __init__(self):
        self._clients_config: Optional[Dict] = None
        self._workspace_profile = None
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
        """Load and cache legacy clients_config.json if present."""
        if self._clients_config is None:
            if self._config_path.exists():
                with open(self._config_path) as f:
                    self._clients_config = json.load(f)
            else:
                self._clients_config = {}
        return self._clients_config

    @property
    def workspace_profile(self):
        """Load and cache the canonical runtime workspace profile."""
        if self._workspace_profile is None:
            self._workspace_profile = load_workspace_profile()
        return self._workspace_profile

    def get_all_clients(self) -> List[Dict[str, Any]]:
        """Get all brands from runtime profile, falling back to legacy config."""
        if self.workspace_profile.brands:
            return [
                {
                    "id": brand.id,
                    "category": "brand",
                    "name": brand.name,
                    "description": brand.description,
                    "url": brand.url,
                    "ga_property": brand.ga_property,
                    "gsc_site": brand.gsc_site,
                    "primary_archetype": brand.primary_archetype,
                    "module_ids": brand.module_ids,
                    "active_channels": brand.active_channels,
                    **brand.metadata,
                }
                for brand in self.workspace_profile.brands
            ]

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
        """Get a specific brand/client by ID."""
        brand = self.workspace_profile.get_brand(client_id)
        if brand:
            return {
                "id": brand.id,
                "category": "brand",
                "name": brand.name,
                "description": brand.description,
                "url": brand.url,
                "ga_property": brand.ga_property,
                "gsc_site": brand.gsc_site,
                "primary_archetype": brand.primary_archetype,
                "module_ids": brand.module_ids,
                "active_channels": brand.active_channels,
                **brand.metadata,
            }

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
