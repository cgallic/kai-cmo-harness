"""Canonical runtime models for the Kai Claude Code-style clone."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Literal, Optional


class SerializableModel:
    """Small stdlib-only serialization helper."""

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class KaiModuleManifest(SerializableModel):
    """Opinionated module manifest for a business archetype."""

    id: str
    name: str
    description: str
    trigger_keywords: List[str] = field(default_factory=list)
    prompt_hints: List[str] = field(default_factory=list)
    required_memory_fields: List[str] = field(default_factory=list)
    default_workflows: List[str] = field(default_factory=list)
    checklist_paths: List[str] = field(default_factory=list)
    default_kpis: List[str] = field(default_factory=list)
    subagents: List[str] = field(default_factory=list)
    remote_automations: List[str] = field(default_factory=list)


@dataclass
class KaiAgentProfile(SerializableModel):
    """Canonical agent identity and scope record for runtime actions."""

    agent_id: str = ""
    name: str = ""
    owner: str = ""
    purpose: str = ""
    workspace_id: str = "kai-marketing-os"
    brand_scope: List[str] = field(default_factory=list)
    workflow_scope: List[str] = field(default_factory=list)
    tool_scope: List[str] = field(default_factory=list)
    model: str = ""
    assurance_level: str = "standard"
    status: Literal["active", "inactive", "expired", "revoked"] = "active"
    created_at: str = ""
    expires_at: Optional[str] = None
    revoked_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ActionMandate(SerializableModel):
    """Structured authority record for high-risk runtime actions."""

    mandate_id: str = ""
    agent_id: str = ""
    brand_id: str = ""
    channel: str = ""
    action_types: List[str] = field(default_factory=list)
    limits: Dict[str, Any] = field(default_factory=dict)
    expires_at: Optional[str] = None
    created_by: str = ""
    approved_by: str = ""
    approval_state: Literal["pending", "approved", "rejected", "revoked"] = "pending"
    source_run_id: Optional[str] = None
    evidence: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    updated_at: str = ""
    revoked_at: Optional[str] = None


@dataclass
class KaiBrandProfile(SerializableModel):
    """A brand/workspace target that runs inside the Kai runtime."""

    id: str
    name: str
    description: str = ""
    url: Optional[str] = None
    primary_archetype: Optional[str] = None
    archetype_overlays: List[str] = field(default_factory=list)
    module_ids: List[str] = field(default_factory=list)
    active_channels: List[str] = field(default_factory=list)
    proof_points: List[str] = field(default_factory=list)
    persona_defaults: Dict[str, str] = field(default_factory=dict)
    ga_property: Optional[str] = None
    gsc_site: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KaiWorkspaceProfile(SerializableModel):
    """Canonical workspace profile for local and remote execution."""

    workspace_id: str = "kai-marketing-os"
    name: str = "Kai Marketing OS"
    description: str = "Marketing-native Claude Code-style runtime"
    primary_user: str = "operator_saas"
    product_mode: str = "clone"
    surfaces: List[str] = field(default_factory=lambda: ["local", "remote"])
    brands: List[KaiBrandProfile] = field(default_factory=list)
    enabled_plugins: List[str] = field(default_factory=lambda: ["kai-marketing"])
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get_brand(self, brand_id: str) -> Optional[KaiBrandProfile]:
        """Find a brand by id."""
        for brand in self.brands:
            if brand.id == brand_id:
                return brand
        return None


@dataclass
class KaiRunRequest(SerializableModel):
    """Canonical run contract shared by local and remote surfaces."""

    intent: str
    workflow: str
    brand_id: str
    surface: Literal["local", "remote"] = "local"
    module_set: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KaiRunRecord(SerializableModel):
    """Persisted run record with lineage and lifecycle state."""

    run_id: str
    intent: str
    workflow: str
    brand_id: str
    surface: Literal["local", "remote"] = "local"
    module_set: List[str] = field(default_factory=list)
    status: Literal["running", "draft", "held", "approved", "completed", "failed"] = "running"
    parent_run_id: Optional[str] = None
    ancestor_run_ids: List[str] = field(default_factory=list)
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    artifact_ids: List[str] = field(default_factory=list)
    started_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None


@dataclass
class KaiArtifactRecord(SerializableModel):
    """Canonical artifact contract."""

    artifact_id: str
    artifact_type: Literal[
        "brief",
        "draft",
        "audit_findings",
        "campaign_plan",
        "gate_proposal",
        "approved_asset",
        "published_asset",
        "performance_snapshot",
        "learned_pattern",
    ]
    brand_id: str
    workflow: str
    module_set: List[str] = field(default_factory=list)
    source_run: Optional[str] = None
    parent_artifact_id: Optional[str] = None
    lineage_run_ids: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KaiRuntimeState(SerializableModel):
    """Mutable workspace state snapshot derived from runs and artifacts."""

    workspace_id: str
    updated_at: str
    latest_run_ids_by_brand: Dict[str, str] = field(default_factory=dict)
    latest_run_ids_by_brand_workflow: Dict[str, str] = field(default_factory=dict)
    latest_artifact_ids_by_brand: Dict[str, str] = field(default_factory=dict)
    latest_artifact_ids_by_brand_workflow: Dict[str, str] = field(default_factory=dict)
    active_run_ids: List[str] = field(default_factory=list)


@dataclass
class KaiGoal(SerializableModel):
    """Canonical model for tracking brand goals and targets."""

    goal_id: str
    brand_id: str
    name: str
    kpi_name: str
    target_value: float
    current_value: float
    target_direction: Literal["increase", "decrease"]
    status: Literal["active", "achieved", "failed"] = "active"
    deadline: str = ""
    created_at: str = ""
    updated_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TaskNode(SerializableModel):
    """Individual execution node within a TaskGraph."""

    node_id: str
    task_type: str
    status: Literal["pending", "running", "completed", "failed", "skipped"] = "pending"
    inputs: Dict[str, Any] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


@dataclass
class TaskGraph(SerializableModel):
    """Directed Acyclic Graph representing a workflow execution roadmap."""

    graph_id: str
    goal_id: Optional[str]
    brand_id: str
    # needs_replan: a node failed and the weekly CMO review should
    # re-decompose the remaining work; replanned: a successor graph exists.
    status: Literal[
        "pending", "running", "completed", "failed", "needs_replan", "replanned"
    ] = "pending"
    nodes: Dict[str, TaskNode] = field(default_factory=dict)
    edges: List[List[str]] = field(default_factory=list)  # List of [from_node, to_node]
    created_at: str = ""
    updated_at: str = ""

