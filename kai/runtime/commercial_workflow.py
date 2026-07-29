"""Executable orchestration for the agentic website-to-checkout workflow.

The workflow is a durable handoff graph, not a script that pretends to be a
fleet. Each turn is owned by a named commercial agent and must return a
content-addressed artifact before the next agent can claim the work. Provider
effects are represented as pending OLA-bound handoffs; this module never
silently performs them.
"""

from __future__ import annotations

import inspect
import hashlib
import json
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, Iterable, Mapping, Optional, Protocol

from .commercial import COMMERCIAL_HANDOFF_SCHEMA, WEBSITE_TO_CHECKOUT_WORKFLOW_ID, CommercialHandoff
from .models import KaiRunRequest
from .store import RuntimeStore


class CommercialAgentExecutor(Protocol):
    """The real agent-runtime boundary used for one named agent turn."""

    def __call__(self, *, agent_id: str, run: Mapping[str, Any], handoff: Mapping[str, Any]) -> Any:
        """Invoke the agent and return an artifact receipt."""


class ClaudeCommercialAgentExecutor:
    """Adapter from the commercial graph to the existing Claude agent task.

    This deliberately uses the agent task runtime, not a content-generation
    script. The returned Claude result is persisted as a normal Kai artifact;
    a downstream agent receives only its URI and hash through the handoff.
    """

    def __init__(self, store: RuntimeStore):
        self.store = store

    async def __call__(self, *, agent_id: str, run: Mapping[str, Any], handoff: Mapping[str, Any]) -> dict:
        from agent.models import ScheduledTask, ScheduledTaskConfig
        from agent.tasks import get_task_handler

        task = ScheduledTask(
            id=f"commercial:{run['run_id']}:{handoff['work_id']}",
            name=f"Commercial agent turn: {agent_id}",
            cron_expression="",
            task_type="claude_agent",
            client=run.get("brand_id"),
            config=ScheduledTaskConfig(
                requires_approval=handoff.get("approval_state") == "approved",
                extra={
                    "brand_id": run.get("brand_id"),
                    "task_type_override": agent_id,
                    "risk_tier": "high" if handoff.get("approval_state") == "approved" else "medium",
                    "input": {
                        "commercial_agent_id": agent_id,
                        "workflow": WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
                        "run": dict(run),
                        "handoff": dict(handoff),
                        "instructions": (
                            "Act as the named commercial agent. Work only from the supplied handoff. "
                            "Return the artifact receipt required by the commercial workflow. "
                            "Do not execute provider effects unless the handoff approval is approved."
                        ),
                    },
                },
            ),
        )
        handler = get_task_handler("claude_agent")
        if handler is None:
            raise RuntimeError("Claude agent task handler is not registered")
        result = await handler.execute(task)
        if not result or not result.get("success"):
            raise RuntimeError(f"commercial agent {agent_id} failed: {result or 'no result'}")

        payload = {
            "agent_id": agent_id,
            "run_id": run["run_id"],
            "work_id": handoff["work_id"],
            "result": result,
        }
        canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
        digest = hashlib.sha256(canonical).hexdigest()
        artifact = self.store.record_artifact(
            {
                "artifact_type": "draft",
                "brand_id": run["brand_id"],
                "workflow": WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
                "source_run": run["run_id"],
                "data": payload,
            },
            run_id=run["run_id"],
            artifact_id=f"commercial-{handoff['work_id']}",
        )
        return {
            "artifact_uri": f"artifact://runtime/{artifact['artifact_id']}.json",
            "artifact_sha256": digest,
            "metadata": {
                "session_id": result.get("session_id"),
                "cost_usd": result.get("cost_usd"),
                "num_turns": result.get("num_turns"),
                "runtime_artifact_id": artifact["artifact_id"],
            },
        }


@dataclass(frozen=True)
class AgentArtifact:
    """Minimum receipt an agent must return to hand off work."""

    artifact_uri: str
    artifact_sha256: str
    metadata: Dict[str, Any]

    @classmethod
    def from_result(cls, result: Mapping[str, Any]) -> "AgentArtifact":
        missing = [key for key in ("artifact_uri", "artifact_sha256") if not result.get(key)]
        if missing:
            raise ValueError("agent result is missing " + ", ".join(missing))
        return cls(
            artifact_uri=str(result["artifact_uri"]),
            artifact_sha256=str(result["artifact_sha256"]),
            metadata=dict(result.get("metadata") or {}),
        )


# The graph is intentionally explicit. Fan-out is represented by multiple
# edges, while effect edges are held by OLA until an exact approval arrives.
AGENT_EDGES: Dict[str, tuple[str, ...]] = {
    "agent.voice.sales_intake": ("agent.commercial.orchestrator",),
    "agent.commercial.orchestrator": ("agent.offer.strategist",),
    "agent.offer.strategist": (
        "agent.website.architect",
        "agent.proposal",
        "agent.checkout",
    ),
    "agent.website.architect": (
        "agent.website.content",
        "agent.website.component",
        "agent.website.page",
    ),
    "agent.website.content": ("agent.website.qa",),
    "agent.website.component": ("agent.website.qa",),
    "agent.website.page": ("agent.website.qa",),
    "agent.website.qa": ("agent.cloudflare.publisher",),
    "agent.checkout": ("agent.ola.projector",),
    "agent.cloudflare.publisher": ("agent.ola.projector",),
    "agent.proposal": ("agent.ola.projector",),
    "agent.ola.projector": ("agent.effect.executor",),
    "agent.effect.executor": (
        "agent.booking",
        "agent.delivery.call",
        "agent.delivery.message",
    ),
    "agent.booking": ("agent.verifier",),
    "agent.delivery.call": ("agent.verifier",),
    "agent.delivery.message": ("agent.verifier",),
    "agent.verifier": ("agent.eco.reconciler",),
    "agent.eco.reconciler": (),
}

OLA_REQUIRED_CONSUMERS = frozenset(
    {
        "agent.cloudflare.publisher",
        "agent.checkout",
        "agent.delivery.call",
        "agent.delivery.message",
        "agent.effect.executor",
    }
)


def _expires(hours: int = 24) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def _work_id(agent_id: str) -> str:
    return f"work-{agent_id.rsplit('.', 1)[-1]}-{uuid.uuid4().hex[:12]}"


class CommercialWorkflow:
    """Coordinates actual agent turns against the durable runtime store."""

    def __init__(self, store: RuntimeStore, executor: CommercialAgentExecutor):
        self.store = store
        self.executor = executor

    def start_from_voice(self, request: Mapping[str, Any]) -> dict:
        """Create a run from a real voice receipt and enqueue the first agent turn."""
        required = ("brand_id", "source_ref", "source_artifact_uri", "source_artifact_sha256")
        missing = [key for key in required if not request.get(key)]
        if missing:
            raise ValueError("voice trigger is missing " + ", ".join(missing))

        run = self.store.start_commercial_run(
            KaiRunRequest(
                intent=str(request.get("intent") or "Turn a qualified voice request into a checkout"),
                workflow=WEBSITE_TO_CHECKOUT_WORKFLOW_ID,
                brand_id=str(request["brand_id"]),
                surface=str(request.get("surface") or "remote"),
                inputs={
                    "source_ref": str(request["source_ref"]),
                    "source_artifact_uri": str(request["source_artifact_uri"]),
                    "source_artifact_sha256": str(request["source_artifact_sha256"]),
                },
                metadata={"trigger": "voice", "schema": COMMERCIAL_HANDOFF_SCHEMA},
            )
        )
        handoff = CommercialHandoff(
            run_id=run["run_id"],
            work_id=_work_id("agent.voice.sales_intake"),
            source_ref=str(request["source_ref"]),
            producer_agent_id="agent.voice.sales_intake",
            consumer_agent_id="agent.commercial.orchestrator",
            artifact_uri=str(request["source_artifact_uri"]),
            artifact_sha256=str(request["source_artifact_sha256"]),
            status="ready",
            approval_state="not_required",
            expires_at=_expires(),
            metadata={"trigger": "voice", "call_id": request.get("call_id")},
        )
        return self.store.append_commercial_handoff(handoff)

    async def advance(self, work_id: str) -> dict:
        """Run one real agent turn and enqueue its next bounded handoffs."""
        source = self.store.get_commercial_handoff(work_id)
        if source["consumer_agent_id"] in OLA_REQUIRED_CONSUMERS and source["approval_state"] != "approved":
            return {"status": "awaiting_ola", "work_id": work_id, "handoff": source}

        claimed = self.store.claim_commercial_handoff(work_id, source["consumer_agent_id"])
        run = self.store.get_run(claimed["run_id"])
        if not run:
            raise KeyError(f"Run not found: {claimed['run_id']}")
        result = self.executor(
            agent_id=claimed["consumer_agent_id"],
            run=run,
            handoff=claimed,
        )
        if inspect.isawaitable(result):
            result = await result
        artifact = AgentArtifact.from_result(result)
        self.store.complete_commercial_handoff(
            work_id,
            claimed["consumer_agent_id"],
            result={"agent_id": claimed["consumer_agent_id"], **artifact.metadata},
        )

        next_handoffs = []
        for consumer in AGENT_EDGES.get(claimed["consumer_agent_id"], ()):
            next_handoff = CommercialHandoff(
                run_id=claimed["run_id"],
                work_id=_work_id(consumer),
                parent_work_id=work_id,
                source_ref=claimed["artifact_uri"],
                producer_agent_id=claimed["consumer_agent_id"],
                consumer_agent_id=consumer,
                artifact_uri=artifact.artifact_uri,
                artifact_sha256=artifact.artifact_sha256,
                status="ready",
                approval_state="pending" if consumer in OLA_REQUIRED_CONSUMERS else "not_required",
                expires_at=_expires(),
                metadata={"parent_work_id": work_id, "agent_result": artifact.metadata},
            )
            next_handoffs.append(self.store.append_commercial_handoff(next_handoff))
        return {
            "status": "advanced",
            "run_id": claimed["run_id"],
            "completed_work_id": work_id,
            "next_handoffs": next_handoffs,
        }


async def website_to_checkout(
    request: Mapping[str, Any],
    *,
    store: Optional[RuntimeStore] = None,
    executor: Optional[CommercialAgentExecutor] = None,
) -> dict:
    """Workflow handler used by the registry and remote trigger surfaces.

    A missing executor is a configuration error, never an invitation to
    generate a fake trace. The real deployment supplies an agent-runtime
    executor backed by the configured Claude/Kai agent service.
    """
    if executor is None:
        raise RuntimeError("website-to-checkout requires a configured agent executor")
    workflow = CommercialWorkflow(store or RuntimeStore.default(), executor)
    first = workflow.start_from_voice(request)
    return {"status": "started", "run_id": first["run_id"], "first_handoff": first}


__all__ = [
    "AGENT_EDGES",
    "OLA_REQUIRED_CONSUMERS",
    "AgentArtifact",
    "CommercialAgentExecutor",
    "ClaudeCommercialAgentExecutor",
    "CommercialWorkflow",
    "website_to_checkout",
]
