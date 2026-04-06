"""Onboarding flow -- walks a new business from zero to first actions.

Eight-step guided workflow:

1. Collect business information (name, URL, services, phone, hours)
2. Build a structured BusinessProfile
3. Determine the business archetype (auto-detect with operator override)
4. Activate archetype-specific modules and watchers
5. Run the initial audit
6. Generate first proposals from audit findings
7. Present the review bundle to the operator
8. Operator approves initial actions

Each step declares an input schema, validation logic, and output
structure.  The entire flow state is a plain dataclass that can be
serialized to disk and resumed later.
"""

from __future__ import annotations

import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


# ---------------------------------------------------------------------------
# Step model
# ---------------------------------------------------------------------------

@dataclass
class OnboardingStep:
    """A single step in the onboarding flow."""

    step_number: int = 0
    title: str = ""
    description: str = ""
    status: str = "pending"       # pending | in_progress | completed | skipped
    required: bool = True
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None

    def model_dump(self) -> Dict[str, Any]:
        return asdict(self)


# ---------------------------------------------------------------------------
# State model
# ---------------------------------------------------------------------------

@dataclass
class OnboardingState:
    """Serializable snapshot of the entire onboarding flow."""

    business_id: str = ""
    started_at: str = ""
    current_step: int = 1
    steps: List[OnboardingStep] = field(default_factory=list)
    business_profile: Optional[Dict[str, Any]] = None
    archetype: Optional[str] = None
    initial_audit: Optional[Dict[str, Any]] = None
    initial_proposals: Optional[Dict[str, Any]] = None
    completed_at: Optional[str] = None

    def model_dump(self) -> Dict[str, Any]:
        data = asdict(self)
        return data


# ---------------------------------------------------------------------------
# Archetype detection heuristics
# ---------------------------------------------------------------------------

_ARCHETYPE_KEYWORDS: Dict[str, List[str]] = {
    "local_service": [
        "plumbing", "hvac", "cleaning", "landscaping", "roofing",
        "painting", "electrical", "handyman", "pest control", "locksmith",
        "window cleaning", "pressure washing", "carpet cleaning", "junk removal",
        "garage door", "appliance repair", "tree service", "pool service",
        "moving", "flooring", "fencing", "gutter",
    ],
    "healthcare": [
        "dentist", "dental", "chiropractic", "medical", "clinic", "therapy",
        "veterinary", "optometry", "dermatology", "orthodontics", "mental health",
        "physical therapy", "pharmacy", "urgent care", "wellness",
    ],
    "professional_services": [
        "law", "legal", "attorney", "accounting", "cpa", "consulting",
        "financial", "advisory", "architecture", "engineering firm",
        "insurance", "real estate", "mortgage", "tax",
    ],
    "restaurant": [
        "restaurant", "cafe", "bar", "catering", "bakery", "pizza",
        "food truck", "diner", "bistro", "grill", "sushi", "brewery",
    ],
    "ecommerce": [
        "shop", "store", "ecommerce", "e-commerce", "retail", "boutique",
        "marketplace", "products", "merchandise", "catalog",
    ],
    "saas": [
        "software", "saas", "platform", "app", "api", "cloud",
        "dashboard", "tool", "analytics", "automation",
    ],
    "creator": [
        "creator", "influencer", "coach", "consultant", "personal brand",
        "course", "membership", "podcast", "youtube", "content creator",
    ],
}


def _detect_archetype(profile_data: Dict[str, Any]) -> str:
    """Auto-detect archetype from business profile data.

    Scans the business name, description, services, and URL for keyword
    matches.  Returns the archetype with the most hits, defaulting to
    ``local_service`` if nothing matches.
    """
    text_parts: List[str] = []
    for key in ("name", "description", "primary_offer", "url", "tagline"):
        val = profile_data.get(key)
        if val and isinstance(val, str):
            text_parts.append(val.lower())

    services = profile_data.get("services")
    if isinstance(services, list):
        text_parts.extend(s.lower() if isinstance(s, str) else "" for s in services)
    elif isinstance(services, str):
        text_parts.append(services.lower())

    combined = " ".join(text_parts)

    scores: Dict[str, int] = {}
    for archetype, keywords in _ARCHETYPE_KEYWORDS.items():
        score = sum(1 for kw in keywords if kw in combined)
        if score > 0:
            scores[archetype] = score

    if not scores:
        return "local_service"

    return max(scores, key=scores.get)  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Archetype -> module activation map
# ---------------------------------------------------------------------------

_ARCHETYPE_MODULES: Dict[str, List[str]] = {
    "local_service": [
        "seo_local", "gbp_optimization", "review_management",
        "lead_capture", "email_nurture", "paid_local",
    ],
    "healthcare": [
        "seo_local", "gbp_optimization", "review_management",
        "patient_education", "hipaa_compliance", "email_nurture",
    ],
    "professional_services": [
        "seo_content", "linkedin_authority", "case_study_engine",
        "email_nurture", "referral_program", "thought_leadership",
    ],
    "restaurant": [
        "seo_local", "gbp_optimization", "social_visual",
        "menu_optimization", "review_management", "event_promotion",
    ],
    "ecommerce": [
        "seo_product", "paid_shopping", "email_lifecycle",
        "social_commerce", "retargeting", "review_management",
    ],
    "saas": [
        "seo_content", "paid_acquisition", "email_lifecycle",
        "content_marketing", "product_led_growth", "trial_optimization",
    ],
    "creator": [
        "social_organic", "email_newsletter", "community_building",
        "content_repurposing", "sponsorship_management", "personal_brand",
    ],
}

_ARCHETYPE_WATCHERS: Dict[str, List[str]] = {
    "local_service": ["gbp_watcher", "review_watcher", "ranking_watcher"],
    "healthcare": ["gbp_watcher", "review_watcher", "compliance_watcher"],
    "professional_services": ["ranking_watcher", "backlink_watcher", "review_watcher"],
    "restaurant": ["gbp_watcher", "review_watcher", "social_watcher"],
    "ecommerce": ["ranking_watcher", "price_watcher", "review_watcher"],
    "saas": ["ranking_watcher", "competitor_watcher", "churn_watcher"],
    "creator": ["social_watcher", "engagement_watcher", "trend_watcher"],
}


# ---------------------------------------------------------------------------
# OnboardingFlow
# ---------------------------------------------------------------------------


class OnboardingFlow:
    """Guided 8-step onboarding for a new business.

    Usage::

        flow = OnboardingFlow(workspace_dir="workspace")
        state = flow.start("Acme Plumbing")
        state = flow.advance_step(state, {
            "name": "Acme Plumbing",
            "url": "https://acmeplumbing.com",
            "services": ["drain cleaning", "pipe repair"],
            "phone": "555-123-4567",
        })
        # ... advance through remaining steps ...
    """

    def __init__(self, workspace_dir: str) -> None:
        self.workspace_dir = workspace_dir

    # -- lifecycle -------------------------------------------------------

    def start(self, business_name: str) -> OnboardingState:
        """Initialize the onboarding flow and return the initial state."""
        steps = self.get_steps()
        steps[0].status = "in_progress"

        return OnboardingState(
            business_id=_new_id("biz"),
            started_at=_utc_now(),
            current_step=1,
            steps=steps,
        )

    def get_steps(self) -> List[OnboardingStep]:
        """Return the full list of onboarding steps with input schemas."""
        return [
            OnboardingStep(
                step_number=1,
                title="Collect Business Information",
                description="Gather the basics: name, URL, services, service area, phone, and hours.",
                required=True,
                input_schema={
                    "name": {"type": "str", "required": True},
                    "url": {"type": "str", "required": False},
                    "services": {"type": "list[str]", "required": False},
                    "service_area": {"type": "str", "required": False},
                    "phone": {"type": "str", "required": False},
                    "hours": {"type": "dict", "required": False},
                },
            ),
            OnboardingStep(
                step_number=2,
                title="Build Business Profile",
                description="Create a structured BusinessProfile from the collected data.",
                required=True,
                input_schema={"confirm": {"type": "bool", "required": True}},
            ),
            OnboardingStep(
                step_number=3,
                title="Determine Archetype",
                description="Auto-detect or manually select the business archetype (local_service, healthcare, etc.).",
                required=True,
                input_schema={
                    "archetype_override": {"type": "str", "required": False},
                },
            ),
            OnboardingStep(
                step_number=4,
                title="Activate Modules",
                description="Activate archetype-specific marketing modules and configure watchers.",
                required=True,
                input_schema={
                    "additional_modules": {"type": "list[str]", "required": False},
                    "disable_modules": {"type": "list[str]", "required": False},
                },
            ),
            OnboardingStep(
                step_number=5,
                title="Run Initial Audit",
                description="Execute a full marketing audit against the business.",
                required=True,
                input_schema={
                    "audit_scope": {"type": "str", "required": False, "default": "full"},
                },
            ),
            OnboardingStep(
                step_number=6,
                title="Generate First Proposals",
                description="Generate an initial proposal bundle from audit findings.",
                required=True,
                input_schema={
                    "max_proposals": {"type": "int", "required": False, "default": 10},
                },
            ),
            OnboardingStep(
                step_number=7,
                title="Present Review Bundle",
                description="Show audit results and proposals to the operator for review.",
                required=True,
                input_schema={},
            ),
            OnboardingStep(
                step_number=8,
                title="Operator Approves Initial Actions",
                description="Operator approves the first batch of actions to kick off marketing.",
                required=True,
                input_schema={
                    "approved_action_ids": {"type": "list[str]", "required": True},
                    "rejected_action_ids": {"type": "list[str]", "required": False},
                    "notes": {"type": "str", "required": False},
                },
            ),
        ]

    # -- step advancement ------------------------------------------------

    def advance_step(self, state: OnboardingState, step_input: Dict[str, Any]) -> OnboardingState:
        """Process the input for the current step and advance.

        Validates input against the step's input_schema, runs step
        processing logic, marks the step completed, and advances the
        pointer to the next step.

        Raises ``ValueError`` if the current step's required inputs are
        missing.
        """
        if state.completed_at:
            raise ValueError("Onboarding is already complete.")

        idx = state.current_step - 1
        if idx < 0 or idx >= len(state.steps):
            raise ValueError(f"Invalid current step: {state.current_step}")

        step = state.steps[idx]

        # Validate required inputs
        for field_name, schema in step.input_schema.items():
            if schema.get("required") and field_name not in step_input:
                raise ValueError(
                    f"Step {state.current_step} ({step.title}) requires '{field_name}'"
                )

        # Dispatch to step processor
        processors = {
            1: self._process_step_1,
            2: self._process_step_2,
            3: self._process_step_3,
            4: self._process_step_4,
            5: self._process_step_5,
            6: self._process_step_6,
            7: self._process_step_7,
            8: self._process_step_8,
        }

        processor = processors.get(state.current_step)
        if processor:
            state = processor(state, step_input)

        # Mark step completed and advance
        state.steps[idx].status = "completed"
        state.steps[idx].output = step_input

        if state.current_step < len(state.steps):
            state.current_step += 1
            state.steps[state.current_step - 1].status = "in_progress"

        return state

    def skip_step(self, state: OnboardingState) -> OnboardingState:
        """Skip the current step if it is not required."""
        idx = state.current_step - 1
        if idx < 0 or idx >= len(state.steps):
            raise ValueError(f"Invalid current step: {state.current_step}")

        step = state.steps[idx]
        if step.required:
            raise ValueError(f"Step {state.current_step} ({step.title}) is required and cannot be skipped.")

        step.status = "skipped"

        if state.current_step < len(state.steps):
            state.current_step += 1
            state.steps[state.current_step - 1].status = "in_progress"

        return state

    def get_progress(self, state: OnboardingState) -> Dict[str, Any]:
        """Return a progress summary for the onboarding flow."""
        total = len(state.steps)
        completed = sum(1 for s in state.steps if s.status in ("completed", "skipped"))
        remaining = total - completed
        # Rough estimate: ~5 minutes per remaining step
        est_minutes = remaining * 5

        return {
            "current_step": state.current_step,
            "total_steps": total,
            "completed_steps": completed,
            "pct_complete": round((completed / total) * 100, 1) if total > 0 else 0.0,
            "estimated_remaining_minutes": est_minutes,
        }

    # -- step processors -------------------------------------------------

    def _process_step_1(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Collect business information."""
        name = input_data.get("name", "").strip()
        if not name:
            raise ValueError("Business name is required.")

        # Store collected data in the business_profile dict for later steps
        state.business_profile = {
            "name": name,
            "url": input_data.get("url", ""),
            "services": input_data.get("services", []),
            "service_area": input_data.get("service_area", ""),
            "phone": input_data.get("phone", ""),
            "hours": input_data.get("hours", {}),
            "collected_at": _utc_now(),
        }
        return state

    def _process_step_2(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Build the BusinessProfile from step 1 data."""
        profile = state.business_profile or {}

        # Fill defaults for missing fields
        profile.setdefault("description", "")
        profile.setdefault("tagline", "")
        profile.setdefault("primary_offer", "")
        profile.setdefault("employee_count_range", "1-5")
        profile.setdefault("pricing_model", "per-job")

        # Derive primary_offer from services if not set
        if not profile.get("primary_offer") and profile.get("services"):
            services_list = profile["services"]
            if isinstance(services_list, list) and services_list:
                profile["primary_offer"] = services_list[0]

        profile["profile_built_at"] = _utc_now()
        state.business_profile = profile
        return state

    def _process_step_3(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Determine archetype via auto-detection with optional override."""
        profile = state.business_profile or {}

        override = input_data.get("archetype_override", "").strip()
        if override:
            state.archetype = override
        else:
            state.archetype = _detect_archetype(profile)

        return state

    def _process_step_4(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Activate modules and watchers based on archetype."""
        archetype = state.archetype or "local_service"

        base_modules = list(_ARCHETYPE_MODULES.get(archetype, _ARCHETYPE_MODULES["local_service"]))
        base_watchers = list(_ARCHETYPE_WATCHERS.get(archetype, _ARCHETYPE_WATCHERS["local_service"]))

        # Apply operator customizations
        additional = input_data.get("additional_modules", [])
        disable = set(input_data.get("disable_modules", []))

        modules = [m for m in base_modules if m not in disable] + additional
        watchers = [w for w in base_watchers if w not in disable]

        profile = state.business_profile or {}
        profile["active_modules"] = modules
        profile["active_watchers"] = watchers
        profile["archetype"] = archetype
        profile["modules_activated_at"] = _utc_now()
        state.business_profile = profile

        return state

    def _process_step_5(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Run the initial audit.

        This step produces a structured audit result.  The actual audit
        engine is invoked at runtime; here we build the result structure
        that downstream steps consume.
        """
        scope = input_data.get("audit_scope", "full")
        profile = state.business_profile or {}
        archetype = state.archetype or "local_service"

        # Build audit categories based on archetype
        category_map: Dict[str, List[str]] = {
            "local_service": ["seo", "gbp", "reviews", "website", "lead_capture", "content"],
            "healthcare": ["seo", "gbp", "reviews", "website", "compliance", "patient_ed"],
            "professional_services": ["seo", "content", "linkedin", "website", "email", "referrals"],
            "restaurant": ["seo", "gbp", "social", "website", "reviews", "menu"],
            "ecommerce": ["seo", "paid", "email", "social", "website", "reviews"],
            "saas": ["seo", "content", "paid", "email", "product_led", "analytics"],
            "creator": ["social", "email", "content", "community", "branding", "monetization"],
        }

        categories = category_map.get(archetype, category_map["local_service"])
        findings: List[Dict[str, Any]] = []

        for cat in categories:
            findings.append({
                "category": cat,
                "score": 0,
                "max_score": 100,
                "findings": [],
                "critical_issues": 0,
                "quick_wins": 0,
            })

        state.initial_audit = {
            "audit_id": _new_id("audit"),
            "business_id": state.business_id,
            "scope": scope,
            "archetype": archetype,
            "overall_score": 0,
            "max_score": 100,
            "categories": findings,
            "critical_findings": [],
            "quick_wins": [],
            "audit_date": _utc_now(),
        }
        return state

    def _process_step_6(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Generate initial proposals from audit findings."""
        max_proposals = int(input_data.get("max_proposals", 10))
        audit = state.initial_audit or {}
        categories = audit.get("categories", [])

        proposals: List[Dict[str, Any]] = []
        proposal_count = 0

        for cat_data in categories:
            if proposal_count >= max_proposals:
                break
            cat = cat_data.get("category", "unknown")
            proposals.append({
                "proposal_id": _new_id("prop"),
                "category": cat,
                "title": f"Address {cat} findings",
                "description": f"Remediation actions for {cat} audit category.",
                "priority": "high" if cat_data.get("critical_issues", 0) > 0 else "medium",
                "estimated_effort_hours": 4,
                "risk_tier": "low",
                "actions": [],
            })
            proposal_count += 1

        state.initial_proposals = {
            "bundle_id": _new_id("bundle"),
            "business_id": state.business_id,
            "proposal_count": len(proposals),
            "proposals": proposals,
            "generated_at": _utc_now(),
        }
        return state

    def _process_step_7(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Compile the review bundle for operator review.

        This step does not modify state significantly -- it assembles
        audit + proposals into a review-ready format.
        """
        audit = state.initial_audit or {}
        proposals = state.initial_proposals or {}

        # Build a summary view the operator can quickly scan
        review_bundle = {
            "audit_summary": {
                "overall_score": audit.get("overall_score", 0),
                "max_score": audit.get("max_score", 100),
                "critical_findings_count": len(audit.get("critical_findings", [])),
                "quick_wins_count": len(audit.get("quick_wins", [])),
                "categories_audited": len(audit.get("categories", [])),
            },
            "top_proposals": proposals.get("proposals", [])[:5],
            "total_proposals": proposals.get("proposal_count", 0),
            "recommended_first_actions": [],
        }

        # Pick recommended first actions: quick wins and low-risk items
        for prop in proposals.get("proposals", [])[:3]:
            review_bundle["recommended_first_actions"].append({
                "proposal_id": prop.get("proposal_id", ""),
                "title": prop.get("title", ""),
                "priority": prop.get("priority", "medium"),
                "risk_tier": prop.get("risk_tier", "low"),
            })

        profile = state.business_profile or {}
        profile["review_bundle"] = review_bundle
        state.business_profile = profile

        return state

    def _process_step_8(self, state: OnboardingState, input_data: Dict[str, Any]) -> OnboardingState:
        """Process operator's approvals and mark onboarding complete."""
        approved_ids = input_data.get("approved_action_ids", [])
        rejected_ids = input_data.get("rejected_action_ids", [])
        notes = input_data.get("notes", "")

        proposals = state.initial_proposals or {}
        proposal_list = proposals.get("proposals", [])

        for prop in proposal_list:
            pid = prop.get("proposal_id", "")
            if pid in approved_ids:
                prop["approval_status"] = "approved"
            elif pid in rejected_ids:
                prop["approval_status"] = "rejected"
            else:
                prop["approval_status"] = "deferred"

        if notes:
            profile = state.business_profile or {}
            profile["onboarding_notes"] = notes
            state.business_profile = profile

        state.initial_proposals = proposals
        state.completed_at = _utc_now()

        return state
