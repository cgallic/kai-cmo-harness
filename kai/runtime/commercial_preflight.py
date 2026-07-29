"""Fail-closed pre-call readiness checks for website-to-checkout."""
from __future__ import annotations

from typing import Any, Mapping

from .commercial import COMMERCIAL_AGENT_IDS, COMMERCIAL_TOOL_IDS
from .commercial_packet import build_commercial_packet
from .commercial_workflow import AGENT_EDGES


REQUIRED_PHASES = (
    "voice",
    "orchestrator",
    "offer",
    "website",
    "website_qa",
    "proposal",
    "checkout_held",
    "booking_held",
    "ola_pending",
)


def preflight(*, profiles: Mapping[str, Mapping[str, Any]], packet: Mapping[str, Any]) -> dict[str, Any]:
    """Validate all pre-call contracts without contacting providers."""
    missing_agents = [agent_id for agent_id in COMMERCIAL_AGENT_IDS if agent_id not in profiles]
    missing_edges = [agent_id for agent_id in ("agent.website.qa", "agent.proposal", "agent.checkout", "agent.booking") if agent_id not in AGENT_EDGES]
    errors = []
    if missing_agents:
        errors.append(f"missing agent profiles: {', '.join(missing_agents)}")
    if missing_edges:
        errors.append(f"missing graph edges: {', '.join(missing_edges)}")
    if packet.get("approval_state") != "pending":
        errors.append("packet must remain approval-pending before the call")
    if packet.get("checkout", {}).get("livemode") is not False:
        errors.append("checkout must be Stripe test mode")
    if packet.get("checkout", {}).get("state") != "held":
        errors.append("checkout must be held")
    if packet.get("booking", {}).get("state") != "held":
        errors.append("booking must be held")
    return {"ready": not errors, "phases": list(REQUIRED_PHASES), "errors": errors}


__all__ = ["preflight", "REQUIRED_PHASES"]
