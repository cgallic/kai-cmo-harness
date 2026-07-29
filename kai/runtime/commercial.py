"""Contracts for the agentic website-to-checkout workflow.

This module defines identities and handoff validation only. Provider effects
remain outside the contract and must be executed through the governed effect
path after approval.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional

from .models import KaiAgentProfile


WEBSITE_TO_CHECKOUT_WORKFLOW_ID = "website-to-checkout"
COMMERCIAL_HANDOFF_SCHEMA = "kai.commercial.handoff.v1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")

COMMERCIAL_AGENT_IDS = (
    "agent.voice.sales_intake",
    "agent.commercial.orchestrator",
    "agent.offer.strategist",
    "agent.website.architect",
    "agent.website.content",
    "agent.website.component",
    "agent.website.page",
    "agent.website.qa",
    "agent.cloudflare.publisher",
    "agent.checkout",
    "agent.checkout.release",
    "agent.booking",
    "agent.proposal",
    "agent.ola.projector",
    "agent.effect.executor",
    "agent.delivery.call",
    "agent.delivery.message",
    "agent.verifier",
    "agent.eco.reconciler",
)

COMMERCIAL_TOOL_IDS = (
    "kaicalls.voice_call",
    "brain.source_event",
    "website_builder.gen_content",
    "website_builder.gen_component",
    "website_builder.gen_page",
    "website_builder.qa",
    "cloudflare.deploy",
    "stripe.test_checkout",
    "stripe.activate_checkout",
    "calendar.booking",
    "proposal.render",
    "ola.authorize",
    "action_gateway.claim",
    "gmail.send_exact",
    "kaicalls.outbound_call",
    "provider.readback",
    "eco.reconcile",
)


@dataclass(frozen=True)
class CommercialHandoff:
    """Durable identity envelope passed between commercial agents."""

    run_id: str
    work_id: str
    source_ref: str
    producer_agent_id: str
    consumer_agent_id: str
    artifact_uri: str
    artifact_sha256: str
    status: Literal["ready", "claimed", "completed", "blocked", "failed"]
    approval_state: Literal["not_required", "pending", "approved", "declined"]
    expires_at: str
    parent_work_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def validate(self) -> List[str]:
        """Return contract violations without performing any provider effect."""
        errors: List[str] = []
        required = {
            "run_id": self.run_id,
            "work_id": self.work_id,
            "source_ref": self.source_ref,
            "producer_agent_id": self.producer_agent_id,
            "consumer_agent_id": self.consumer_agent_id,
            "artifact_uri": self.artifact_uri,
            "artifact_sha256": self.artifact_sha256,
            "expires_at": self.expires_at,
        }
        errors.extend(f"{name} is required" for name, value in required.items() if not value)
        if self.producer_agent_id == self.consumer_agent_id:
            errors.append("producer_agent_id and consumer_agent_id must differ")
        if self.producer_agent_id not in COMMERCIAL_AGENT_IDS:
            errors.append(f"unknown producer agent: {self.producer_agent_id}")
        if self.consumer_agent_id not in COMMERCIAL_AGENT_IDS:
            errors.append(f"unknown consumer agent: {self.consumer_agent_id}")
        if not _SHA256_RE.fullmatch(self.artifact_sha256):
            errors.append("artifact_sha256 must be lowercase SHA-256")
        try:
            datetime.fromisoformat(self.expires_at.replace("Z", "+00:00"))
        except ValueError:
            errors.append("expires_at must be ISO-8601")
        return errors

    def model_dump(self) -> Dict[str, Any]:
        return {
            "schema": COMMERCIAL_HANDOFF_SCHEMA,
            "run_id": self.run_id,
            "work_id": self.work_id,
            "parent_work_id": self.parent_work_id,
            "source_ref": self.source_ref,
            "producer_agent_id": self.producer_agent_id,
            "consumer_agent_id": self.consumer_agent_id,
            "artifact_uri": self.artifact_uri,
            "artifact_sha256": self.artifact_sha256,
            "status": self.status,
            "approval_state": self.approval_state,
            "expires_at": self.expires_at,
            "metadata": self.metadata,
        }


def commercial_agent_profiles(workspace_id: str) -> List[KaiAgentProfile]:
    """Return scoped first-class agents for the website-to-checkout workflow."""
    common = {
        "workspace_id": workspace_id,
        "brand_scope": ["*"],
        "workflow_scope": [WEBSITE_TO_CHECKOUT_WORKFLOW_ID],
        "status": "active",
        "assurance_level": "high",
    }
    definitions = [
        ("agent.voice.sales_intake", "Sales Intake Agent", "Turns a KaiCalls interaction into a sourced sales request.", ["kaicalls.voice_call", "brain.source_event"], "gpt-5.4"),
        ("agent.commercial.orchestrator", "Commercial Orchestrator", "Decomposes and routes one bounded website-to-checkout run.", ["agent_rpc", "workflow_ledger"], "gpt-5.5"),
        ("agent.offer.strategist", "Offer Strategist", "Produces the exact offer, price, terms, and claims boundary.", ["offer_policy", "source_retrieval"], "gpt-5.4"),
        ("agent.website.architect", "Website Architect", "Creates the Website Builder vision, specification, and plan artifacts.", ["website_builder.specify", "website_builder.plan"], "gpt-5.4"),
        ("agent.website.content", "Website Content Agent", "Creates sourced site content through the content-generation tool.", ["website_builder.gen_content"], "gpt-5.4"),
        ("agent.website.component", "Website Component Agent", "Creates UI components through the component-generation tool.", ["website_builder.gen_component"], "gpt-5.4"),
        ("agent.website.page", "Website Page Agent", "Assembles pages through the page-generation tool.", ["website_builder.gen_page"], "gpt-5.4"),
        ("agent.website.qa", "Website QA Agent", "Checks the generated build and checkout path independently.", ["website_builder.qa", "browser.read"], "gpt-5.4"),
        ("agent.cloudflare.publisher", "Cloudflare Publisher", "Deploys only the approved website artifact to the bound target.", ["cloudflare.deploy"], "gpt-5.4"),
        ("agent.checkout", "Checkout Agent", "Prepares a checkout object bound to the offer and run.", ["stripe.test_checkout"], "gpt-5.4"),
        ("agent.checkout.release", "Checkout Release Agent", "Activates or sends only the approved checkout object.", ["stripe.activate_checkout"], "gpt-5.4"),
        ("agent.booking", "Booking Agent", "Prepares the exact customer call booking.", ["calendar.booking"], "gpt-5.4"),
        ("agent.proposal", "Proposal Agent", "Assembles the customer proposal from verified artifacts.", ["proposal.render"], "gpt-5.4"),
        ("agent.ola.projector", "OLA Projector", "Presents the exact commercial packet for human approval.", ["ola.authorize"], "gpt-5.4"),
        ("agent.effect.executor", "Effect Executor", "Claims and executes one approved bounded effect.", ["action_gateway.claim"], "gpt-5.4"),
        ("agent.delivery.call", "Call Delivery Agent", "Places the approved outbound KaiCalls call.", ["kaicalls.outbound_call"], "gpt-5.4"),
        ("agent.delivery.message", "Message Delivery Agent", "Sends the exact approved proposal bytes.", ["gmail.send_exact"], "gpt-5.4"),
        ("agent.verifier", "Commercial Verifier", "Reads Cloudflare, Stripe, Calendar, call, and message state independently.", ["provider.readback"], "gpt-5.4"),
        ("agent.eco.reconciler", "ECO Reconciler", "Joins receipts and verification into the final company state.", ["eco.reconcile"], "gpt-5.4"),
    ]
    return [
        KaiAgentProfile(
            agent_id=agent_id,
            name=name,
            owner="workspace-owner",
            purpose=purpose,
            tool_scope=tools,
            model=model,
            **common,
        )
        for agent_id, name, purpose, tools, model in definitions
    ]
