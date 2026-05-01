"""Integration registry — tracks connected channel integrations per brand."""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from scripts.harness_config import get_config

from .models import SerializableModel


# ---------------------------------------------------------------------------
# Helpers (mirrors store.py conventions)
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def _json_dump(payload: Any) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, default=str)


def _json_load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json_atomic(path: Path, payload: Any) -> None:
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    tmp_path.write_text(_json_dump(payload), encoding="utf-8")
    tmp_path.replace(path)


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Dataclass
# ---------------------------------------------------------------------------


INTEGRATION_STATUSES = ("pending_auth", "connected", "degraded", "disconnected", "error")
CAPABILITY_STATES = (
    "connected",
    "configured",
    "read_sync_ok",
    "write_supported",
    "verified",
    "degraded",
)


def derive_capability_state(record: dict) -> Dict[str, bool]:
    """Return provider capability health flags for dashboard clients."""

    capabilities = set(record.get("capabilities") or [])
    status = record.get("status")
    kill_switch = bool(record.get("kill_switch", False))
    last_sync_at = record.get("last_sync_at")
    last_verified_at = record.get("last_verified_at")
    last_error = record.get("last_error")

    return {
        "connected": status in ("connected", "degraded"),
        "configured": bool(record.get("config") or record.get("connected_account_id")),
        "read_sync_ok": bool(last_sync_at) and status in ("connected", "degraded"),
        "write_supported": bool(capabilities.intersection({"write", "publish", "schedule", "budget"})) and not kill_switch,
        "verified": bool(last_verified_at or last_sync_at) and status == "connected" and not kill_switch,
        "degraded": status in ("degraded", "error") or bool(last_error) or kill_switch,
    }


def is_operational(record: dict) -> bool:
    """Return True only when a provider has proven read or verify health."""

    state = derive_capability_state(record)
    return state["connected"] and state["configured"] and (state["read_sync_ok"] or state["verified"])


@dataclass
class IntegrationEntry(SerializableModel):
    """A connected channel integration for a brand."""

    integration_id: str = ""
    brand_id: str = ""
    channel: str = ""  # website, social, paid_media, email, analytics
    provider: str = ""  # wordpress, shopify, meta, google_ads, mailchimp, ga4, gsc, etc.
    status: Literal[
        "pending_auth", "connected", "degraded", "disconnected", "error"
    ] = "pending_auth"
    credentials_ref: Optional[str] = None  # pointer, NOT the credentials
    config: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)  # read, write, schedule, budget
    kill_switch: bool = False  # True = all mutations blocked
    metadata: Dict[str, Any] = field(default_factory=dict)
    connected_at: Optional[str] = None
    updated_at: str = ""

    # --- Pipedream identity ---
    connected_account_id: Optional[str] = None  # Pipedream connected account ID
    external_user_id: Optional[str] = None  # user ID in the external provider

    # --- Scopes & capabilities ---
    scopes: List[str] = field(default_factory=list)  # OAuth scopes granted

    # --- Health tracking ---
    last_verified_at: Optional[str] = None
    last_sync_at: Optional[str] = None
    last_error: Optional[str] = None


# ---------------------------------------------------------------------------
# IntegrationRegistry
# ---------------------------------------------------------------------------


class IntegrationRegistry:
    """File-backed registry for brand channel integrations.

    Each integration is stored as a JSON file under ``{base_dir}/integrations/``.
    """

    def __init__(self, base_dir: Optional[Path] = None):
        cfg = get_config()
        if base_dir is None:
            base_dir = Path(os.environ.get("KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")))

        self.base_dir = base_dir
        self.integrations_dir = _ensure_dir(self.base_dir / "integrations")
        self._lock = threading.RLock()

    @classmethod
    def default(cls) -> "IntegrationRegistry":
        return cls()

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, entry: IntegrationEntry | dict) -> dict:
        """Register a new integration."""
        record = self._coerce_entry(entry)
        integration_id = record.get("integration_id") or _new_id("int")
        now = _utc_now()

        record["integration_id"] = integration_id
        record["updated_at"] = now
        if record.get("status") == "connected" and not record.get("connected_at"):
            record["connected_at"] = now

        with self._lock:
            _write_json_atomic(
                self.integrations_dir / f"{integration_id}.json",
                record,
            )
        return record

    # ------------------------------------------------------------------
    # Updates
    # ------------------------------------------------------------------

    def update(self, integration_id: str, **changes: Any) -> dict:
        """Patch fields on an existing integration."""
        with self._lock:
            record = self._require(integration_id)
            record.update(changes)
            record["updated_at"] = _utc_now()
            # If status just became connected, set connected_at
            if changes.get("status") == "connected" and not record.get("connected_at"):
                record["connected_at"] = _utc_now()
            _write_json_atomic(
                self.integrations_dir / f"{integration_id}.json",
                record,
            )
            return record

    def disconnect(self, integration_id: str) -> dict:
        """Mark an integration as disconnected."""
        return self.update(integration_id, status="disconnected")

    # ------------------------------------------------------------------
    # Queries
    # ------------------------------------------------------------------

    def get(self, integration_id: str) -> Optional[dict]:
        """Load a single integration by ID."""
        path = self.integrations_dir / f"{integration_id}.json"
        if not path.exists():
            return None
        return _json_load(path)

    def list_for_brand(
        self,
        brand_id: str,
        channel: Optional[str] = None,
    ) -> List[dict]:
        """List all integrations for a brand, optionally filtered by channel."""
        records: List[dict] = []
        for path in self.integrations_dir.glob("*.json"):
            record = _json_load(path)
            if record.get("brand_id") != brand_id:
                continue
            if channel and record.get("channel") != channel:
                continue
            records.append(record)
        records.sort(key=lambda r: r.get("updated_at", ""), reverse=True)
        return records

    def is_channel_active(self, brand_id: str, channel: str) -> bool:
        """Return True if the brand has a connected integration on this channel
        with kill_switch disabled."""
        for path in self.integrations_dir.glob("*.json"):
            record = _json_load(path)
            if (
                record.get("brand_id") == brand_id
                and record.get("channel") == channel
                and record.get("status") == "connected"
                and not record.get("kill_switch", False)
            ):
                return True
        return False

    # ------------------------------------------------------------------
    # Health & verification
    # ------------------------------------------------------------------

    def mark_verified(self, integration_id: str) -> dict:
        """Record that a connection was just verified healthy."""
        return self.update(integration_id, status="connected", last_verified_at=_utc_now(), last_error=None)

    def mark_degraded(self, integration_id: str, reason: str) -> dict:
        """Mark a connection as degraded with a reason."""
        return self.update(integration_id, status="degraded", last_error=reason)

    def mark_error(self, integration_id: str, error: str) -> dict:
        """Mark a connection as errored."""
        return self.update(integration_id, status="error", last_error=error)

    def mark_synced(self, integration_id: str) -> dict:
        """Record that channel state was just synced."""
        return self.update(integration_id, last_sync_at=_utc_now())

    def get_health_summary(self, brand_id: str) -> Dict[str, Any]:
        """Return a per-channel health summary for a brand.

        Returns dict keyed by channel with status, provider, last_verified_at,
        last_sync_at, kill_switch, and last_error for each integration.
        """
        integrations = self.list_for_brand(brand_id)
        summary: Dict[str, Any] = {}
        for rec in integrations:
            channel = rec.get("channel", "unknown")
            entry = {
                "integration_id": rec.get("integration_id"),
                "provider": rec.get("provider"),
                "status": rec.get("status"),
                "kill_switch": rec.get("kill_switch", False),
                "capabilities": rec.get("capabilities", []),
                "capability_state": derive_capability_state(rec),
                "operational": is_operational(rec),
                "scopes": rec.get("scopes", []),
                "last_verified_at": rec.get("last_verified_at"),
                "last_sync_at": rec.get("last_sync_at"),
                "last_error": rec.get("last_error"),
            }
            summary.setdefault(channel, []).append(entry)
        return summary

    def get_scope_summary(self, brand_id: str) -> Dict[str, Any]:
        """Return what is connected vs missing for operator surfaces.

        Returns dict with 'connected' (channel→capabilities) and 'missing'
        (channels with no active integration).
        """
        all_channels = {"website", "social", "paid_media", "email", "analytics"}
        integrations = self.list_for_brand(brand_id)
        connected: Dict[str, Any] = {}
        for rec in integrations:
            if rec.get("status") in ("connected", "degraded"):
                ch = rec.get("channel", "unknown")
                connected.setdefault(ch, []).append({
                    "provider": rec.get("provider"),
                    "capabilities": rec.get("capabilities", []),
                    "scopes": rec.get("scopes", []),
                    "status": rec.get("status"),
                })
        missing = sorted(all_channels - set(connected.keys()))
        return {"connected": connected, "missing": missing}

    # ------------------------------------------------------------------
    # Kill switch
    # ------------------------------------------------------------------

    def activate_kill_switch(self, brand_id: str, channel: str) -> List[dict]:
        """Set kill_switch=True for every integration on the given brand+channel."""
        updated: List[dict] = []
        with self._lock:
            for path in self.integrations_dir.glob("*.json"):
                record = _json_load(path)
                if record.get("brand_id") != brand_id or record.get("channel") != channel:
                    continue
                record["kill_switch"] = True
                record["updated_at"] = _utc_now()
                _write_json_atomic(path, record)
                updated.append(record)
        return updated

    def deactivate_kill_switch(self, brand_id: str, channel: str) -> List[dict]:
        """Set kill_switch=False for every integration on the given brand+channel."""
        updated: List[dict] = []
        with self._lock:
            for path in self.integrations_dir.glob("*.json"):
                record = _json_load(path)
                if record.get("brand_id") != brand_id or record.get("channel") != channel:
                    continue
                record["kill_switch"] = False
                record["updated_at"] = _utc_now()
                _write_json_atomic(path, record)
                updated.append(record)
        return updated

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require(self, integration_id: str) -> dict:
        record = self.get(integration_id)
        if not record:
            raise KeyError(f"Integration not found: {integration_id}")
        return record

    def _coerce_entry(self, entry: IntegrationEntry | dict) -> dict:
        if isinstance(entry, IntegrationEntry):
            return asdict(entry)
        if isinstance(entry, dict):
            result = dict(entry)
            result.setdefault("config", {})
            result.setdefault("capabilities", [])
            result.setdefault("kill_switch", False)
            result.setdefault("metadata", {})
            result.setdefault("connected_at", None)
            result.setdefault("status", "pending_auth")
            result.setdefault("connected_account_id", None)
            result.setdefault("external_user_id", None)
            result.setdefault("scopes", [])
            result.setdefault("last_verified_at", None)
            result.setdefault("last_sync_at", None)
            result.setdefault("last_error", None)
            return result
        raise TypeError(f"Unsupported entry type: {type(entry)!r}")


# ---------------------------------------------------------------------------
# Process-wide singleton
# ---------------------------------------------------------------------------

_DEFAULT_INTEGRATION_REGISTRY: Optional[IntegrationRegistry] = None


def get_default_integration_registry() -> IntegrationRegistry:
    """Lazily construct the process-wide default integration registry."""
    global _DEFAULT_INTEGRATION_REGISTRY
    if _DEFAULT_INTEGRATION_REGISTRY is None:
        _DEFAULT_INTEGRATION_REGISTRY = IntegrationRegistry.default()
    return _DEFAULT_INTEGRATION_REGISTRY
