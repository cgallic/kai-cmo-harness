"""Canonical workflow registry for Kai runtime surfaces.

This module is the shared contract between local skills, the gateway, and
dashboard clients. It keeps product workflow IDs separate from the legacy
content engine formats while still giving the engine a canonical format to run.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Iterable, Optional, Tuple

from .models import SerializableModel


@dataclass(frozen=True)
class WorkflowDefinition(SerializableModel):
    """A product workflow that can be invoked from Kai surfaces."""

    workflow_id: str
    handler: str
    input_schema: str
    output_artifacts: Tuple[str, ...] = field(default_factory=tuple)
    quality_policy: str = "default"
    supported_surfaces: Tuple[str, ...] = ("local", "remote", "dashboard")
    content_format: Optional[str] = None
    aliases: Tuple[str, ...] = field(default_factory=tuple)
    local_service_asset: Optional[str] = None
    risk_tier: str = "medium"
    auto_run_allowed: bool = False


GENERATION_FRAMEWORK_MAP: Dict[str, Tuple[str, ...]] = {
    "blog": ("knowledge/frameworks/content-copywriting/algorithmic-authorship.md",),
    "linkedin": ("knowledge/channels/linkedin-articles.md",),
    "email-lifecycle": ("knowledge/channels/email-lifecycle.md",),
    "cold-email": (
        "knowledge/channels/email-lifecycle.md",
        "harness/references/cold-email-rules.md",
    ),
    "tiktok": ("knowledge/channels/tiktok-algorithm.md",),
    "meta-ads": (
        "knowledge/channels/meta-advertising.md",
        "harness/references/meta-ads-rules.md",
        "harness/references/meta-ads-api-reference.md",
    ),
    "google-ads": (
        "knowledge/channels/paid-acquisition.md",
        "harness/references/google-ads-policy-reference.md",
    ),
    "press": ("knowledge/channels/press-releases.md",),
    "seo": (
        "knowledge/frameworks/content-copywriting/algorithmic-authorship.md",
        "knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md",
    ),
    "landing-page": (
        "knowledge/frameworks/content-copywriting/perception-engineering.md",
        "knowledge/playbooks/funnel-hack-offer-architecture.md",
        "knowledge/checklists/perception-engineering-checklist.md",
    ),
    "gbp-post": (
        "knowledge/playbooks/demand-generation.md",
        "knowledge/checklists/content-checklist.md",
    ),
    "review-response": (
        "knowledge/playbooks/conversion-rate-optimization.md",
        "knowledge/checklists/content-checklist.md",
    ),
    "call-script": (
        "knowledge/playbooks/conversion-rate-optimization.md",
        "knowledge/playbooks/demand-generation.md",
    ),
    "review-request-sequence": (
        "knowledge/channels/email-lifecycle.md",
        "harness/references/advertising-compliance.md",
    ),
}


_WORKFLOWS: Tuple[WorkflowDefinition, ...] = (
    WorkflowDefinition(
        workflow_id="blog",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/blog-post.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="blog-publish",
        content_format="blog",
        aliases=("kai-write",),
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="seo",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/blog-post.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="blog-publish",
        content_format="seo",
        aliases=("seo-content",),
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="linkedin",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/linkedin-article.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="linkedin-article",
        content_format="linkedin",
        aliases=("linkedin-article",),
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="email-lifecycle",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/email-lifecycle.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="cold-email",
        content_format="email-lifecycle",
        aliases=("email", "kai-email-system"),
        local_service_asset="follow_up_email",
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="cold-email",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/cold-email.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="cold-email",
        content_format="cold-email",
        aliases=("kai-cold-outreach",),
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="meta-ads",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/meta-ads.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="meta-ad",
        content_format="meta-ads",
        aliases=("kai-ad-campaign", "facebook-ads", "instagram-ads"),
        risk_tier="high",
    ),
    WorkflowDefinition(
        workflow_id="google-ads",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/google-ads.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="google-ad",
        content_format="google-ads",
        aliases=("search-ads",),
        risk_tier="high",
    ),
    WorkflowDefinition(
        workflow_id="tiktok",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/tiktok.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="tiktok-script",
        content_format="tiktok",
        aliases=("kai-social", "tiktok-script"),
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="press",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/press-release.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="press-release",
        content_format="press",
        aliases=("press-release",),
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="landing-page",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/landing-page.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="landing-page",
        content_format="landing-page",
        aliases=("kai-landing-page", "website-section", "website-cta"),
        local_service_asset="website_conversion_asset",
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="gbp-post",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/gbp-post.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="local-service-asset",
        content_format="gbp-post",
        aliases=("google-business-profile-post", "gbp-update"),
        local_service_asset="gbp_post",
        risk_tier="low",
        auto_run_allowed=True,
    ),
    WorkflowDefinition(
        workflow_id="review-response",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/review-response.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="local-service-asset",
        content_format="review-response",
        aliases=("review-reply", "gbp-review-response"),
        local_service_asset="review_response",
        risk_tier="low",
        auto_run_allowed=True,
    ),
    WorkflowDefinition(
        workflow_id="call-script",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/call-script.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="local-service-asset",
        content_format="call-script",
        aliases=("kaicalls-script", "missed-call-script"),
        local_service_asset="call_handling_script",
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="review-request-sequence",
        handler="scripts.content.engine.generate",
        input_schema="harness/skill-contracts/review-request-sequence.yaml",
        output_artifacts=("brief", "draft", "gate_proposal", "approved_asset"),
        quality_policy="cold-email",
        content_format="review-request-sequence",
        aliases=("review-request", "review-sequence"),
        local_service_asset="review_request_sequence",
        risk_tier="medium",
    ),
    WorkflowDefinition(
        workflow_id="website-to-checkout",
        handler="kai.runtime.commercial.website_to_checkout",
        input_schema="harness/skill-contracts/website-to-checkout.yaml",
        output_artifacts=(
            "sales_request",
            "offer",
            "website_build",
            "checkout",
            "proposal",
            "booking",
            "approval_packet",
            "provider_receipts",
            "reconciliation",
        ),
        quality_policy="website-to-checkout",
        supported_surfaces=("remote", "dashboard"),
        risk_tier="high",
        auto_run_allowed=False,
    ),
)

_BY_ID: Dict[str, WorkflowDefinition] = {w.workflow_id: w for w in _WORKFLOWS}
_ALIASES: Dict[str, str] = {
    alias: workflow.workflow_id
    for workflow in _WORKFLOWS
    for alias in workflow.aliases
}


def list_workflows() -> Tuple[WorkflowDefinition, ...]:
    """Return every known workflow definition."""

    return _WORKFLOWS


def list_generation_formats() -> Tuple[str, ...]:
    """Return canonical content formats supported by the content engine."""

    return tuple(sorted(w.content_format for w in _WORKFLOWS if w.content_format))


def normalize_workflow_id(value: str) -> str:
    """Normalize aliases and legacy skill names to workflow IDs."""

    normalized = (value or "").strip().lower()
    return _ALIASES.get(normalized, normalized)


def get_workflow(value: str) -> Optional[WorkflowDefinition]:
    """Resolve a workflow ID or alias."""

    return _BY_ID.get(normalize_workflow_id(value))


def get_generation_workflow(value: str) -> Optional[WorkflowDefinition]:
    """Resolve a workflow that can run through scripts.content.engine."""

    workflow = get_workflow(value)
    if workflow and workflow.content_format:
        return workflow
    return None


def get_content_format(value: str) -> Optional[str]:
    """Return the canonical engine format for an ID or alias."""

    workflow = get_generation_workflow(value)
    return workflow.content_format if workflow else None


def get_framework_paths(value: str) -> Tuple[str, ...]:
    """Return knowledge/reference files for a generation workflow."""

    content_format = get_content_format(value) or normalize_workflow_id(value)
    return GENERATION_FRAMEWORK_MAP.get(content_format, ())


def iter_aliases() -> Iterable[tuple[str, str]]:
    """Yield alias -> workflow ID pairs for diagnostic UIs."""

    return tuple(sorted(_ALIASES.items()))
