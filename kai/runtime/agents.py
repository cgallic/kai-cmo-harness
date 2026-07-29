"""Agent registry — local runtime identity and scope controls for Kai agents."""

from __future__ import annotations

import json
import os
import threading
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from scripts.harness_config import get_config

from .models import KaiAgentProfile
from .commercial import commercial_agent_profiles


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


def _parse_iso8601(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _is_scope_allowed(scope: List[str], target: Optional[str]) -> bool:
    if target is None:
        return True
    if not scope:
        return False
    if "*" in scope:
        return True
    return target in scope


class AgentRegistry:
    """File-backed registry of Kai agent profiles."""

    def __init__(self, base_dir: Optional[Path] = None):
        cfg = get_config()
        if base_dir is None:
            base_dir = Path(os.environ.get("KAI_RUNTIME_DIR", str(cfg.data_dir / "runtime")))

        self.base_dir = base_dir
        self.agents_dir = _ensure_dir(self.base_dir / "agents")
        self._lock = threading.RLock()

    @classmethod
    def default(cls) -> "AgentRegistry":
        return cls()

    def create(self, profile: KaiAgentProfile | dict) -> dict:
        """Create and persist an agent profile."""
        record = self._coerce_profile(profile)
        agent_id = record.get("agent_id") or _new_id("agent")
        now = _utc_now()

        record["agent_id"] = agent_id
        record["status"] = record.get("status") or "active"
        record["created_at"] = record.get("created_at") or now
        record.setdefault("metadata", {})

        with self._lock:
            _write_json_atomic(self.agents_dir / f"{agent_id}.json", record)
        return record

    def update(self, agent_id: str, **changes: Any) -> dict:
        """Patch fields on an existing agent profile."""
        with self._lock:
            record = self._require(agent_id)
            record.update(changes)
            record.setdefault("metadata", {})
            _write_json_atomic(self.agents_dir / f"{agent_id}.json", record)
            return record

    def get(self, agent_id: str) -> Optional[dict]:
        """Load a single profile by agent ID."""
        path = self.agents_dir / f"{agent_id}.json"
        if not path.exists():
            return None
        return _json_load(path)

    def list(
        self,
        *,
        workspace_id: Optional[str] = None,
        owner: Optional[str] = None,
        status: Optional[str] = None,
        limit: int = 100,
    ) -> List[dict]:
        """List agent profiles with optional filters."""
        records: List[dict] = []
        for path in self.agents_dir.glob("*.json"):
            record = _json_load(path)
            if workspace_id and record.get("workspace_id") != workspace_id:
                continue
            if owner and record.get("owner") != owner:
                continue
            if status and record.get("status") != status:
                continue
            records.append(record)
        records.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        return records[:limit]

    def revoke(self, agent_id: str, *, reason: Optional[str] = None) -> dict:
        """Revoke an agent profile immediately."""
        with self._lock:
            record = self._require(agent_id)
            record["status"] = "revoked"
            record["revoked_at"] = _utc_now()
            if reason:
                record.setdefault("metadata", {})["revocation_reason"] = reason
            _write_json_atomic(self.agents_dir / f"{agent_id}.json", record)
            return record

    def check_scope(
        self,
        agent_id: str,
        *,
        workspace_id: Optional[str] = None,
        brand_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        tool_id: Optional[str] = None,
        at_time: Optional[str] = None,
    ) -> dict:
        """Validate status, expiry, and scope access for a requested action."""
        record = self.get(agent_id)
        if not record:
            return {"allowed": False, "reason": f"Agent not found: {agent_id}", "agent_id": agent_id}

        now = _parse_iso8601(at_time) if at_time else datetime.now(timezone.utc)
        if now is None:
            now = datetime.now(timezone.utc)

        if record.get("status") == "revoked":
            return {"allowed": False, "reason": "Agent is revoked", "agent_id": agent_id}

        if record.get("status") not in ("active",):
            return {
                "allowed": False,
                "reason": f"Agent status '{record.get('status')}' is not active",
                "agent_id": agent_id,
            }

        expires_at = _parse_iso8601(record.get("expires_at"))
        if expires_at and expires_at <= now:
            return {"allowed": False, "reason": "Agent profile is expired", "agent_id": agent_id}

        if workspace_id and record.get("workspace_id") != workspace_id:
            return {
                "allowed": False,
                "reason": f"Workspace scope denied: {workspace_id}",
                "agent_id": agent_id,
            }

        if not _is_scope_allowed(record.get("brand_scope") or [], brand_id):
            return {"allowed": False, "reason": f"Brand scope denied: {brand_id}", "agent_id": agent_id}

        if not _is_scope_allowed(record.get("workflow_scope") or [], workflow_id):
            return {"allowed": False, "reason": f"Workflow scope denied: {workflow_id}", "agent_id": agent_id}

        if not _is_scope_allowed(record.get("tool_scope") or [], tool_id):
            return {"allowed": False, "reason": f"Tool scope denied: {tool_id}", "agent_id": agent_id}

        return {"allowed": True, "reason": "ok", "agent_id": agent_id}

    def _require(self, agent_id: str) -> dict:
        record = self.get(agent_id)
        if not record:
            raise KeyError(f"Agent not found: {agent_id}")
        return record

    def _coerce_profile(self, profile: KaiAgentProfile | dict) -> dict:
        if isinstance(profile, KaiAgentProfile):
            return asdict(profile)
        if isinstance(profile, dict):
            result = dict(profile)
            result.setdefault("agent_id", "")
            result.setdefault("name", "")
            result.setdefault("owner", "")
            result.setdefault("purpose", "")
            result.setdefault("workspace_id", "kai-marketing-os")
            result.setdefault("brand_scope", [])
            result.setdefault("workflow_scope", [])
            result.setdefault("tool_scope", [])
            result.setdefault("model", "")
            result.setdefault("assurance_level", "standard")
            result.setdefault("status", "active")
            result.setdefault("created_at", "")
            result.setdefault("expires_at", None)
            result.setdefault("revoked_at", None)
            result.setdefault("metadata", {})
            return result
        raise TypeError(f"Unsupported profile type: {type(profile)!r}")


def default_agent_profiles(workspace_id: str = "kai-marketing-os") -> List[KaiAgentProfile]:
    """Return starter local profiles for common Kai agent roles."""
    return [
        KaiAgentProfile(
            agent_id="agent_kai_operator",
            name="Kai Operator",
            owner="workspace-owner",
            purpose="Runs local-first orchestration and approval-safe workflow execution.",
            workspace_id=workspace_id,
            brand_scope=["*"],
            workflow_scope=["*"],
            tool_scope=["*"],
            model="gpt-5.5",
            assurance_level="high",
            status="active",
        ),
        KaiAgentProfile(
            agent_id="agent_content_worker",
            name="Kai Content Worker",
            owner="workspace-owner",
            purpose="Generates and gates marketing content under approved workflow scopes.",
            workspace_id=workspace_id,
            brand_scope=["*"],
            workflow_scope=["content-gate", "kai-seo-audit", "kai-launch"],
            tool_scope=["content_writer", "quality_gates"],
            model="gpt-5.4",
            assurance_level="standard",
            status="active",
        ),
        KaiAgentProfile(
            agent_id="agent_connector_watcher",
            name="Kai Connector Watcher",
            owner="workspace-owner",
            purpose="Performs connector-health and read-only observability checks.",
            workspace_id=workspace_id,
            brand_scope=["*"],
            workflow_scope=["connector-health-check"],
            tool_scope=["connector_health_read"],
            model="gpt-5.4-mini",
            assurance_level="standard",
            status="active",
        ),
    ] + commercial_agent_profiles(workspace_id)


_DEFAULT_AGENT_REGISTRY: Optional[AgentRegistry] = None


def get_default_agent_registry() -> AgentRegistry:
    """Lazily construct the process-wide default agent registry."""
    global _DEFAULT_AGENT_REGISTRY
    if _DEFAULT_AGENT_REGISTRY is None:
        _DEFAULT_AGENT_REGISTRY = AgentRegistry.default()
    return _DEFAULT_AGENT_REGISTRY
