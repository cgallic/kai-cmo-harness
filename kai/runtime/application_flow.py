"""Application-layer orchestration for the first local-service flow.

Bridges:
BusinessProfile -> audit input -> AuditResult -> ProposedAction -> ReviewBundle
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .actions import ActionStore
from .audit import AuditCategory, AuditFinding, AuditResult, LocalServiceAuditor
from .business_profile import BusinessProfile
from .models import SerializableModel
from .policy import PolicyEngine


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _split_budget_range(value: Optional[str]) -> Optional[int]:
    """Extract the upper monthly budget bound if present."""
    if not value:
        return None
    digits = []
    current = ""
    for char in value:
        if char.isdigit():
            current += char
        elif current:
            digits.append(int(current))
            current = ""
    if current:
        digits.append(int(current))
    if not digits:
        return None
    return max(digits)


def _active_channel_names(profile: BusinessProfile) -> set[str]:
    return {
        channel.channel
        for channel in profile.channels.channels
        if channel.status == "active"
    }


def _has_channel(profile: BusinessProfile, channel_name: str, *, statuses: tuple[str, ...] = ("active",)) -> bool:
    return any(
        channel.channel == channel_name and channel.status in statuses
        for channel in profile.channels.channels
    )


def _find_channel(profile: BusinessProfile, channel_name: str):
    for channel in profile.channels.channels:
        if channel.channel == channel_name:
            return channel
    return None


def _has_kai_calls_coverage(profile: BusinessProfile) -> bool:
    if any("kaicalls" in item.lower() for item in profile.constraints.non_negotiables):
        return True
    calls_channel = _find_channel(profile, "calls")
    if calls_channel and calls_channel.notes:
        return "kaicalls" in calls_channel.notes.lower()
    return bool(profile.metadata.get("after_hours_coverage"))


def _has_review_goal(profile: BusinessProfile) -> bool:
    return any(
        "review" in (goal.metric or "").lower() or "review" in goal.goal.lower()
        for goal in profile.goals.goals
    )


def _has_referral_goal(profile: BusinessProfile) -> bool:
    return any(
        "referral" in (goal.metric or "").lower() or "referral" in goal.goal.lower()
        for goal in profile.goals.goals
    )


def _check(
    check_id: str,
    label: str,
    passed: bool,
    *,
    summary: str,
    evidence: Optional[Dict[str, Any]] = None,
    weight: float = 1.0,
    severity: Optional[str] = None,
    priority: Optional[str] = None,
    recommended_direction: Optional[str] = None,
    affected_channel: Optional[str] = None,
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "id": check_id,
        "label": label,
        "passed": passed,
        "summary": summary,
        "evidence": evidence or {},
        "weight": weight,
    }
    if severity:
        payload["severity"] = severity
    if priority:
        payload["priority"] = priority
    if recommended_direction:
        payload["recommended_direction"] = recommended_direction
    if affected_channel:
        payload["affected_channel"] = affected_channel
    return payload


def build_local_service_audit_input(profile: BusinessProfile) -> Dict[str, List[Dict[str, Any]]]:
    """Translate a BusinessProfile into the check lists expected by LocalServiceAuditor."""
    budget_ceiling = _split_budget_range(profile.constraints.budget_ceiling)
    active_channels = _active_channel_names(profile)
    social_channels = {"paid-social", "social", "facebook", "instagram", "linkedin", "tiktok", "youtube"}
    active_social_channels = active_channels & social_channels
    phone_visible = profile.metadata.get("website_phone_in_header") or any(
        "phone number must be prominently displayed" in item.lower()
        for item in profile.constraints.non_negotiables
    )
    review_process = bool(profile.metadata.get("review_request_process")) or _has_review_goal(profile)
    follow_up_sequence = bool(profile.metadata.get("follow_up_sequence_active"))
    website_url = profile.identity.url or _find_channel(profile, "website").url if _find_channel(profile, "website") else profile.identity.url

    return {
        AuditCategory.OFFER_CLARITY.value: [
            _check(
                "offer_primary",
                "Primary offer is clearly defined",
                bool(profile.offers.primary_offer),
                summary="The business needs a clearly stated primary service or offer.",
                evidence={"primary_offer": profile.offers.primary_offer},
                severity="high",
                recommended_direction="Clarify the primary service offer in the hero and service pages",
                affected_channel="website",
            ),
            _check(
                "offer_depth",
                "Offer catalog covers core services",
                len(profile.offers.offer_list) >= 2,
                summary="Local-service businesses need enough service detail to match multiple search intents.",
                evidence={"offer_count": len(profile.offers.offer_list)},
                recommended_direction="Expand service-page coverage for the core job types you want to win",
                affected_channel="website",
            ),
            _check(
                "offer_messaging",
                "Tagline or business description explains the promise",
                bool(profile.identity.tagline or profile.identity.description),
                summary="Visitors should immediately understand what the company does and why it is different.",
                evidence={
                    "tagline_present": bool(profile.identity.tagline),
                    "description_present": bool(profile.identity.description),
                },
                recommended_direction="Tighten the headline and supporting copy around the core promise",
                affected_channel="website",
            ),
            _check(
                "pricing_signal",
                "Pricing model or deal value signal is available",
                bool(profile.offers.pricing_model or profile.offers.average_deal_value),
                summary="Even when exact pricing is variable, the business should signal how buying works.",
                evidence={
                    "pricing_model": profile.offers.pricing_model,
                    "average_deal_value": profile.offers.average_deal_value,
                },
                recommended_direction="Add pricing context, financing, or quote expectations to reduce uncertainty",
                affected_channel="website",
            ),
        ],
        AuditCategory.TRUST_AND_PROOF.value: [
            _check(
                "trust_signal_count",
                "Trust signals are visible and numerous",
                len(profile.trust.signals) >= 3,
                summary="Local-service buyers need visible proof before calling.",
                evidence={"trust_signal_count": len(profile.trust.signals)},
                severity="high",
                recommended_direction="Add testimonials, certifications, guarantees, and awards to key pages",
                affected_channel="website",
            ),
            _check(
                "review_volume",
                "Review volume is competitive",
                (profile.trust.review_count or 0) >= 50,
                summary="A thin review profile makes the business harder to trust against local competitors.",
                evidence={"review_count": profile.trust.review_count},
                recommended_direction="Increase review acquisition velocity and showcase the best reviews prominently",
                affected_channel="website",
            ),
            _check(
                "review_rating",
                "Average review rating is healthy",
                (profile.trust.review_average or 0) >= 4.5,
                summary="Low review averages create immediate trust friction.",
                evidence={"review_average": profile.trust.review_average},
                recommended_direction="Address service quality issues and rebalance the review profile with fresh wins",
                affected_channel="website",
            ),
            _check(
                "certs_guarantees",
                "Certifications or guarantees are present",
                bool(profile.trust.certifications or profile.trust.guarantees),
                summary="Local-service sites should reduce risk with credentials and guarantees.",
                evidence={
                    "certification_count": len(profile.trust.certifications),
                    "guarantee_count": len(profile.trust.guarantees),
                },
                recommended_direction="Add certifications, licensing, and service guarantees near CTAs",
                affected_channel="website",
            ),
        ],
        AuditCategory.CONVERSION_PATH.value: [
            _check(
                "website_url",
                "Website has a live primary destination",
                bool(website_url),
                summary="The business needs a canonical destination for conversion-focused updates.",
                evidence={"url": website_url},
                severity="critical",
                recommended_direction="Establish and optimize a single primary website destination",
                affected_channel="website",
            ),
            _check(
                "phone_number",
                "Primary phone number is available",
                bool(profile.channels.phone_number),
                summary="Phone is the main conversion path for most local-service businesses.",
                evidence={"phone_number": profile.channels.phone_number},
                severity="critical",
                recommended_direction="Add a clearly visible tracked phone number across the site",
                affected_channel="website",
            ),
            _check(
                "calls_channel",
                "Calls channel is active",
                _has_channel(profile, "calls"),
                summary="The business should treat inbound calls as an operating channel, not an afterthought.",
                evidence={"calls_active": _has_channel(profile, "calls")},
                severity="critical",
                recommended_direction="Make calls the primary CTA across hero, service pages, and local pages",
                affected_channel="website",
            ),
            _check(
                "phone_visibility",
                "Phone CTA is expected to be prominent",
                bool(phone_visible),
                summary="Local-service buyers should not have to hunt for the number or CTA.",
                evidence={"phone_visible": bool(phone_visible)},
                recommended_direction="Move the primary call CTA above the fold and repeat it throughout the page",
                affected_channel="website",
            ),
        ],
        AuditCategory.LOCAL_SEO.value: [
            _check(
                "gbp_active",
                "Google Business Profile is active",
                _has_channel(profile, "gbp"),
                summary="GBP is foundational for map-pack visibility and local credibility.",
                evidence={"gbp_active": _has_channel(profile, "gbp")},
                recommended_direction="Claim, optimize, and maintain the Google Business Profile",
                affected_channel="website",
            ),
            _check(
                "local_seo_active",
                "Local SEO channel is active",
                _has_channel(profile, "local-seo"),
                summary="The business should actively target local intent terms, not rely on brand alone.",
                evidence={"local_seo_active": _has_channel(profile, "local-seo")},
                recommended_direction="Build location and service-area page coverage around real local queries",
                affected_channel="website",
            ),
            _check(
                "location_defined",
                "Primary location is defined",
                bool(profile.geography.primary_location and profile.geography.primary_location.city and profile.geography.primary_location.state),
                summary="Local search performance depends on a clear primary city and state footprint.",
                evidence={
                    "city": profile.geography.primary_location.city if profile.geography.primary_location else None,
                    "state": profile.geography.primary_location.state if profile.geography.primary_location else None,
                },
                recommended_direction="Clarify the core market and align pages, GBP, and citations to it",
                affected_channel="website",
            ),
            _check(
                "service_areas",
                "Service areas are documented",
                len(profile.geography.service_areas) >= 1,
                summary="Service-area businesses need explicit coverage signals for nearby markets.",
                evidence={"service_area_count": len(profile.geography.service_areas)},
                recommended_direction="Create service-area and city-specific landing-page coverage",
                affected_channel="website",
            ),
            _check(
                "google_reviews_platform",
                "Google is part of the review footprint",
                any(platform.lower() == "google" for platform in profile.trust.review_platforms),
                summary="Google reviews strongly influence local visibility and buyer trust.",
                evidence={"review_platforms": profile.trust.review_platforms},
                recommended_direction="Drive more Google review acquisition and showcase Google proof on-page",
                affected_channel="website",
            ),
        ],
        AuditCategory.SPEED_TO_LEAD.value: [
            _check(
                "calls_primary_source",
                "Calls are acknowledged as the primary lead source",
                profile.channels.primary_lead_source == "calls",
                summary="The business should align its operating model around the fastest lead path.",
                evidence={"primary_lead_source": profile.channels.primary_lead_source},
                severity="critical",
                recommended_direction="Re-center acquisition and conversion around the inbound call path",
                affected_channel="website",
            ),
            _check(
                "call_tracking",
                "Call tracking is enabled",
                profile.channels.uses_call_tracking,
                summary="Without call tracking, the business cannot reliably measure speed-to-lead or channel ROI.",
                evidence={"uses_call_tracking": profile.channels.uses_call_tracking},
                severity="high",
                recommended_direction="Enable call tracking to attribute and improve inbound lead handling",
                affected_channel="website",
            ),
            _check(
                "missed_call_coverage",
                "Missed-call or after-hours coverage exists",
                _has_kai_calls_coverage(profile),
                summary="Local-service buyers often call first. Missed calls are missed revenue.",
                evidence={"kaicalls_or_after_hours": _has_kai_calls_coverage(profile)},
                severity="critical",
                recommended_direction="Implement KaiCalls or another after-hours coverage layer for missed calls",
                affected_channel="website",
            ),
            _check(
                "lead_response_sla",
                "Lead response SLA is defined",
                bool(profile.metadata.get("lead_response_minutes")),
                summary="If response speed is not defined, it usually is not managed.",
                evidence={"lead_response_minutes": profile.metadata.get("lead_response_minutes")},
                severity="high",
                recommended_direction="Set and enforce a response-time SLA for inbound leads",
                affected_channel="website",
            ),
        ],
        AuditCategory.REVIEWS_REPUTATION.value: [
            _check(
                "reviews_channel",
                "Reviews channel is active",
                _has_channel(profile, "reviews"),
                summary="The business should treat reviews as an active operating channel.",
                evidence={"reviews_active": _has_channel(profile, "reviews")},
                severity="high",
                recommended_direction="Operationalize review requests after every completed job",
                affected_channel="social",
            ),
            _check(
                "review_count_healthy",
                "Review count is healthy for a local-service brand",
                (profile.trust.review_count or 0) >= 100,
                summary="A small review footprint weakens both trust and local visibility.",
                evidence={"review_count": profile.trust.review_count},
                recommended_direction="Run a review-generation campaign tied to completed jobs",
                affected_channel="social",
            ),
            _check(
                "review_average_healthy",
                "Review average is strong",
                (profile.trust.review_average or 0) >= 4.7,
                summary="Strong averages help the business convert uncertain buyers faster.",
                evidence={"review_average": profile.trust.review_average},
                recommended_direction="Fix service delivery issues and amplify the strongest customer outcomes",
                affected_channel="social",
            ),
            _check(
                "review_process",
                "Review request process exists",
                bool(review_process),
                summary="Review growth should be process-driven, not accidental.",
                evidence={"review_process": bool(review_process)},
                recommended_direction="Create a post-job review request sequence and social proof loop",
                affected_channel="social",
            ),
        ],
        AuditCategory.CHANNEL_PRESENCE.value: [
            _check(
                "active_channel_count",
                "Core acquisition channels are active",
                len(active_channels) >= 4,
                summary="The business should not rely on a single fragile channel.",
                evidence={"active_channels": sorted(active_channels)},
                recommended_direction="Expand presence across the core local-service acquisition channels",
                affected_channel="social",
            ),
            _check(
                "social_presence",
                "At least one social channel is active",
                bool(active_social_channels),
                summary="Even low-volume local brands benefit from basic proof-of-life social presence.",
                evidence={"active_social_channels": sorted(active_social_channels)},
                recommended_direction="Stand up a lightweight social proof cadence on one or two channels",
                affected_channel="social",
            ),
            _check(
                "paid_search_presence",
                "Paid search is active or planned",
                _has_channel(profile, "paid-search", statuses=("active", "planned")),
                summary="Paid search gives local-service brands controllable demand capture.",
                evidence={
                    "paid_search_status": _find_channel(profile, "paid-search").status
                    if _find_channel(profile, "paid-search")
                    else None
                },
                recommended_direction="Add or improve paid-search coverage for high-intent service terms",
                affected_channel="paid_media",
            ),
            _check(
                "budget_supports_ads",
                "Budget can support paid demand capture",
                (budget_ceiling or 0) >= 1000 or bool(profile.goals.monthly_budget_range),
                summary="Paid acquisition needs a clear budget envelope before it can operate responsibly.",
                evidence={"budget_ceiling": profile.constraints.budget_ceiling, "monthly_budget_range": profile.goals.monthly_budget_range},
                recommended_direction="Set a bounded paid-media budget and creative testing cadence",
                affected_channel="paid_media",
            ),
        ],
        AuditCategory.FOLLOW_UP_GAPS.value: [
            _check(
                "email_channel",
                "Email or lifecycle channel exists",
                _has_channel(profile, "email", statuses=("active", "planned")),
                summary="Follow-up requires an owned re-engagement channel.",
                evidence={
                    "email_status": _find_channel(profile, "email").status
                    if _find_channel(profile, "email")
                    else None
                },
                recommended_direction="Set up a lightweight lifecycle channel for post-job follow-up",
                affected_channel="email",
            ),
            _check(
                "follow_up_sequence",
                "Post-job follow-up sequence is active",
                bool(follow_up_sequence),
                summary="Without a repeatable sequence, referral and review opportunities are left on the table.",
                evidence={"follow_up_sequence_active": bool(follow_up_sequence)},
                recommended_direction="Launch a post-job follow-up sequence for reviews, referrals, and maintenance offers",
                affected_channel="email",
            ),
            _check(
                "referral_channel",
                "Referral motion is active",
                _has_channel(profile, "referrals") and _has_referral_goal(profile),
                summary="Referrals should be an intentional motion, not just a hope.",
                evidence={
                    "referrals_active": _has_channel(profile, "referrals"),
                    "referral_goal": _has_referral_goal(profile),
                },
                recommended_direction="Create a formal referral ask after successful jobs",
                affected_channel="email",
            ),
            _check(
                "upsell_motion",
                "There is a clear upsell or nurture motion",
                bool(profile.offers.upsells),
                summary="Local-service businesses should turn one-time jobs into higher-LTV relationships.",
                evidence={"upsell_count": len(profile.offers.upsells)},
                recommended_direction="Build follow-up offers around maintenance, upgrades, or accessory services",
                affected_channel="email",
            ),
        ],
    }


@dataclass
class ProposedAction(SerializableModel):
    """Application-level action proposal before persistence to ActionStore."""

    proposal_id: str = ""
    brand_id: str = ""
    channel: str = ""
    action_type: str = ""
    title: str = ""
    reason: str = ""
    business_impact: str = ""
    expected_outcome: str = ""
    risk_tier: str = ""
    approval_required: bool = True
    suggested_payload: Dict[str, Any] = field(default_factory=dict)
    source_finding_ids: List[str] = field(default_factory=list)
    source_audit_id: Optional[str] = None
    source_run_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.proposal_id:
            self.proposal_id = _new_id("prop")


@dataclass
class ReviewBundle(SerializableModel):
    """Operator-facing review bundle for one business diagnostic pass."""

    bundle_id: str = ""
    brand_id: str = ""
    archetype: str = "local-service"
    generated_at: str = field(default_factory=_utc_now)
    business_profile_summary: Dict[str, Any] = field(default_factory=dict)
    audit_summary: Dict[str, Any] = field(default_factory=dict)
    audit_result: Dict[str, Any] = field(default_factory=dict)
    proposed_actions: List[Dict[str, Any]] = field(default_factory=list)
    persisted_action_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.bundle_id:
            self.bundle_id = _new_id("bundle")


def run_local_service_audit(profile: BusinessProfile) -> AuditResult:
    """Run the local-service audit directly from a BusinessProfile."""
    audit_input = build_local_service_audit_input(profile)
    auditor = LocalServiceAuditor()
    return auditor.audit(audit_input, brand_id=profile.brand_id)


def _proposal_recipe_for_finding(profile: BusinessProfile, finding: AuditFinding) -> tuple[str, str, Dict[str, Any], str]:
    """Map a finding to a concrete channel/action/payload family."""
    if finding.category == AuditCategory.OFFER_CLARITY.value:
        return (
            "website",
            "update_page_copy",
            {
                "page": "/",
                "section": "hero",
                "focus": "primary_offer",
                "service_area": profile.geography.primary_location.city if profile.geography.primary_location else None,
            },
            "Sharper messaging should increase qualified calls and quote requests.",
        )
    if finding.category == AuditCategory.TRUST_AND_PROOF.value:
        return (
            "website",
            "update_page_section",
            {
                "page": "/",
                "section": "trust_block",
                "assets": [signal.value for signal in profile.trust.signals[:5]],
            },
            "More proof near conversion points should improve trust and call conversion.",
        )
    if finding.category == AuditCategory.CONVERSION_PATH.value:
        if "primary destination" in finding.title.lower():
            return (
                "website",
                "update_page_copy",
                {
                    "page": "/",
                    "section": "homepage_foundation",
                    "focus": "launch_core_offer_and_local_service_message",
                },
                "A basic but credible homepage should give the business a conversion destination instead of losing demand entirely.",
            )
        return (
            "website",
            "update_cta",
            {
                "page": "/",
                "cta_type": "call_now",
                "phone_number": profile.channels.phone_number,
            },
            "A stronger call-first CTA should shorten the path from visit to lead.",
        )
    if finding.category == AuditCategory.LOCAL_SEO.value:
        return (
            "website",
            "update_page_section",
            {
                "page": "/service-areas",
                "section": "local_coverage",
                "locations": [
                    {"city": area.city, "state": area.state}
                    for area in profile.geography.service_areas
                ],
            },
            "Better local coverage pages should improve local-intent rankings and map-pack relevance.",
        )
    if finding.category == AuditCategory.SPEED_TO_LEAD.value:
        return (
            "website",
            "update_cta",
            {
                "page": "/",
                "cta_type": "call_or_text",
                "message": "same_day_response",
            },
            "Reducing response friction should recover more urgent inbound leads.",
        )
    if finding.category == AuditCategory.REVIEWS_REPUTATION.value:
        return (
            "social",
            "schedule_social_post",
            {
                "campaign": "social_proof",
                "theme": "customer_outcomes_and_reviews",
                "review_platform": "Google",
            },
            "A visible proof cadence should improve trust and create more review momentum.",
        )
    if finding.category == AuditCategory.CHANNEL_PRESENCE.value:
        if finding.affected_channel == "paid_media":
            return (
                "paid_media",
                "create_ad_creative",
                {
                    "campaign_theme": "local_service_emergency_intent",
                    "offer": profile.offers.primary_offer,
                    "service_area": profile.geography.primary_location.city if profile.geography.primary_location else None,
                },
                "Adding controlled paid demand capture should create a second high-intent acquisition path.",
            )
        return (
            "social",
            "schedule_social_post",
            {
                "campaign": "proof_of_presence",
                "theme": "local_tips_and_service_proof",
                "cadence": "weekly",
            },
            "A lightweight social cadence should make the brand feel active and credible.",
        )
    return (
        "email",
        "launch_email_sequence",
        {
            "sequence_type": "post_job_follow_up",
            "goals": ["review_request", "referral_ask", "upsell_offer"],
        },
        "Consistent follow-up should improve repeat business, reviews, and referrals.",
    )


def build_proposed_actions(
    profile: BusinessProfile,
    audit_result: AuditResult,
    *,
    source_run_id: Optional[str] = None,
    limit: int = 8,
    policy_engine: Optional[PolicyEngine] = None,
) -> List[ProposedAction]:
    """Convert prioritized findings into typed application-level action proposals."""
    engine = policy_engine or PolicyEngine()
    proposals: List[ProposedAction] = []
    selected_findings: List[AuditFinding] = []
    seen_categories: set[str] = set()

    # First pass: guarantee cross-category coverage so the plan is not eight copies of the same website fix.
    for finding in audit_result.prioritized_findings:
        if finding.category in seen_categories:
            continue
        selected_findings.append(finding)
        seen_categories.add(finding.category)
        if len(selected_findings) >= limit:
            break

    # Second pass: fill remaining slots by priority order.
    if len(selected_findings) < limit:
        selected_ids = {finding.finding_id for finding in selected_findings}
        for finding in audit_result.prioritized_findings:
            if finding.finding_id in selected_ids:
                continue
            selected_findings.append(finding)
            if len(selected_findings) >= limit:
                break

    for finding in selected_findings:
        channel, action_type, payload, expected_outcome = _proposal_recipe_for_finding(profile, finding)
        action_seed = {
            "brand_id": profile.brand_id,
            "channel": channel,
            "action_type": action_type,
            "intent": finding.title,
            "proposed_changes": payload,
            "source_run_id": source_run_id,
        }
        policy_result = engine.evaluate(action_seed)
        proposals.append(
            ProposedAction(
                brand_id=profile.brand_id,
                channel=channel,
                action_type=action_type,
                title=finding.title,
                reason=finding.summary,
                business_impact=(
                    "High near-term impact on lead generation and conversion."
                    if finding.priority in {"P0", "P1"}
                    else "Moderate impact on pipeline quality and conversion efficiency."
                ),
                expected_outcome=expected_outcome,
                risk_tier=policy_result["risk_tier"],
                approval_required=policy_result.get("requires_approval", True),
                suggested_payload=payload,
                source_finding_ids=[finding.finding_id],
                source_audit_id=audit_result.audit_id,
                source_run_id=source_run_id,
                metadata={
                    "finding_category": finding.category,
                    "finding_priority": finding.priority,
                    "finding_severity": finding.severity,
                    "affected_channel": finding.affected_channel,
                    "recommended_direction": finding.recommended_direction,
                    "policy_result": policy_result,
                },
            )
        )
    return proposals


def persist_proposed_actions(
    proposals: List[ProposedAction],
    *,
    action_store: Optional[ActionStore] = None,
) -> List[dict]:
    """Persist application proposals into the runtime ActionStore."""
    store = action_store or ActionStore.default()
    records: List[dict] = []
    for proposal in proposals:
        action_dict = {
            "brand_id": proposal.brand_id,
            "channel": proposal.channel,
            "action_type": proposal.action_type,
            "intent": proposal.title,
            "proposed_changes": proposal.suggested_payload,
            "source_run_id": proposal.source_run_id,
            "risk_tier": proposal.risk_tier or "medium",
            "policy_result": proposal.metadata.get("policy_result", {"passed": True, "checks": [], "violations": []}),
            "metadata": {
                "proposal_id": proposal.proposal_id,
                "reason": proposal.reason,
                "business_impact": proposal.business_impact,
                "expected_outcome": proposal.expected_outcome,
                "source_finding_ids": proposal.source_finding_ids,
                "source_audit_id": proposal.source_audit_id,
            },
        }
        records.append(store.propose_action(action_dict))
    return records


def build_business_profile_summary(profile: BusinessProfile) -> Dict[str, Any]:
    """Build a compact operator summary from the full BusinessProfile."""
    active_channels = sorted(_active_channel_names(profile))
    return {
        "brand_id": profile.brand_id,
        "name": profile.identity.name,
        "archetype": profile.archetype,
        "primary_offer": profile.offers.primary_offer,
        "service_area": {
            "primary_city": profile.geography.primary_location.city if profile.geography.primary_location else None,
            "primary_state": profile.geography.primary_location.state if profile.geography.primary_location else None,
            "service_area_count": len(profile.geography.service_areas),
        },
        "primary_persona": profile.personas.primary.persona_id if profile.personas.primary else None,
        "trust": {
            "review_count": profile.trust.review_count,
            "review_average": profile.trust.review_average,
            "signal_count": len(profile.trust.signals),
        },
        "active_channels": active_channels,
        "primary_kpi": profile.goals.primary_kpi,
        "budget_ceiling": profile.constraints.budget_ceiling,
        "non_negotiables": profile.constraints.non_negotiables,
    }


def build_audit_summary(audit_result: AuditResult) -> Dict[str, Any]:
    """Build a compact scorecard summary from the full AuditResult."""
    return {
        "audit_id": audit_result.audit_id,
        "overall_score": audit_result.overall_score,
        "overall_grade": audit_result.overall_grade,
        "total_findings": audit_result.total_findings,
        "critical_findings": len(audit_result.critical_findings),
        "top_categories": [
            {
                "category": category.category,
                "display_name": category.display_name,
                "score": category.score,
                "grade": category.grade,
                "finding_count": category.finding_count,
            }
            for category in audit_result.categories
        ],
    }


def build_review_bundle(
    profile: BusinessProfile,
    audit_result: AuditResult,
    proposed_actions: List[ProposedAction],
    *,
    persisted_actions: Optional[List[dict]] = None,
    source_run_id: Optional[str] = None,
) -> ReviewBundle:
    """Assemble the operator-facing review bundle."""
    persisted_actions = persisted_actions or []
    action_counts_by_channel: Dict[str, int] = {}
    for action in proposed_actions:
        action_counts_by_channel[action.channel] = action_counts_by_channel.get(action.channel, 0) + 1

    return ReviewBundle(
        brand_id=profile.brand_id,
        archetype=profile.archetype,
        business_profile_summary=build_business_profile_summary(profile),
        audit_summary=build_audit_summary(audit_result),
        audit_result=audit_result.model_dump(),
        proposed_actions=[proposal.model_dump() for proposal in proposed_actions],
        persisted_action_ids=[record["action_id"] for record in persisted_actions],
        metadata={
            "source_run_id": source_run_id,
            "proposal_count": len(proposed_actions),
            "action_counts_by_channel": action_counts_by_channel,
            "approval_required_count": sum(1 for proposal in proposed_actions if proposal.approval_required),
        },
    )


def run_local_service_review_flow(
    profile: BusinessProfile,
    *,
    source_run_id: Optional[str] = None,
    persist_actions: bool = False,
    action_store: Optional[ActionStore] = None,
    policy_engine: Optional[PolicyEngine] = None,
) -> ReviewBundle:
    """Run the full application flow for the first local-service slice."""
    audit_result = run_local_service_audit(profile)
    proposed_actions = build_proposed_actions(
        profile,
        audit_result,
        source_run_id=source_run_id,
        policy_engine=policy_engine,
    )
    persisted_actions = persist_proposed_actions(
        proposed_actions,
        action_store=action_store,
    ) if persist_actions else []
    return build_review_bundle(
        profile,
        audit_result,
        proposed_actions,
        persisted_actions=persisted_actions,
        source_run_id=source_run_id,
    )
