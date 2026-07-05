"""Client onboarding flow — reusable across all business types.

Guides a new business through: create brand → fill profile → choose archetype
→ connect systems → verify capabilities → run first audit → generate first
action queue.

Also provides connection readiness checklists for specific clients.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .business_profile import deep_merge_profile, save_profile_overlay
from .models import SerializableModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Durable-fact extraction — onboarding answers → profile overlay updates
# ---------------------------------------------------------------------------

# Raw BusinessProfile sections that may be passed through whole.
_PROFILE_SECTION_KEYS = {
    "identity", "offers", "geography", "personas", "trust",
    "goals", "channels", "constraints", "metadata",
}

# Flat answer keys (kai/packaging/setup.py conventions) → (section, field).
_FLAT_ANSWER_MAP = {
    "business_name": ("identity", "name"),
    "name": ("identity", "name"),
    "website_url": ("identity", "url"),
    "url": ("identity", "url"),
    "business_description": ("identity", "description"),
    "tagline": ("identity", "tagline"),
    "year_founded": ("identity", "year_founded"),
    "employee_count_range": ("identity", "employee_count_range"),
    "primary_service": ("offers", "primary_offer"),
    "primary_offer": ("offers", "primary_offer"),
    "pricing_model": ("offers", "pricing_model"),
    "average_deal_value": ("offers", "average_deal_value"),
    "phone_number": ("channels", "phone_number"),
    "primary_lead_source": ("channels", "primary_lead_source"),
    "primary_kpi": ("goals", "primary_kpi"),
    "monthly_budget_range": ("goals", "monthly_budget_range"),
    "budget_ceiling": ("constraints", "budget_ceiling"),
    "icp_description": ("personas", "icp_description"),
    "years_in_business": ("trust", "years_in_business"),
    "review_count": ("trust", "review_count"),
    "review_average": ("trust", "review_average"),
}

# Flat geography answers land under geography.primary_location.
_GEO_PRIMARY_MAP = {
    "primary_city": "city",
    "state_province": "state",
    "service_radius_miles": "radius_miles",
}

# Session-scoped keys that never belong in the durable overlay.
_TRANSIENT_ANSWER_KEYS = {
    "brand_id", "onboarding_stage", "connections_pending",
    "connections_complete", "known_client", "connected", "updated_at",
}


def _normalize_archetype_id(value: Any) -> str:
    """Normalize archetype ids ('local_service' → 'local-service')."""
    return str(value).strip().lower().replace("_", "-")


def extract_profile_facts(answers: Dict[str, Any]) -> Dict[str, Any]:
    """Map onboarding answers to a raw BusinessProfile overlay update.

    Accepts both flat answer keys (business_name, primary_city, ...) and
    whole profile sections (identity, offers, ...). Unknown scalar answers
    are preserved under metadata so durable facts never evaporate; keys
    starting with '_' and session-transient keys are dropped.
    """
    updates: Dict[str, Any] = {}
    metadata: Dict[str, Any] = {}

    for key, value in (answers or {}).items():
        if key.startswith("_") or key in _TRANSIENT_ANSWER_KEYS:
            continue
        if value is None or (isinstance(value, str) and not value.strip()):
            continue

        if key == "archetype":
            updates["archetype"] = _normalize_archetype_id(value)
        elif key == "archetype_overlays" and isinstance(value, list):
            updates["archetype_overlays"] = list(value)
        elif key in _PROFILE_SECTION_KEYS and isinstance(value, dict):
            updates[key] = deep_merge_profile(updates.get(key) or {}, value)
        elif key in _FLAT_ANSWER_MAP:
            section, field_name = _FLAT_ANSWER_MAP[key]
            updates.setdefault(section, {})[field_name] = value
        elif key in _GEO_PRIMARY_MAP:
            geo = updates.setdefault("geography", {})
            geo.setdefault("primary_location", {})[_GEO_PRIMARY_MAP[key]] = value
        elif key == "service_list":
            primary = str((answers or {}).get("primary_service", "")).strip().lower()
            items = [s.strip() for s in str(value).split(",") if s.strip()]
            if items:
                updates.setdefault("offers", {})["offer_list"] = [
                    {"name": item, "is_primary": item.lower() == primary}
                    for item in items
                ]
        elif isinstance(value, (str, int, float, bool)):
            metadata[key] = value

    if metadata:
        updates["metadata"] = deep_merge_profile(updates.get("metadata") or {}, metadata)

    return updates


# ---------------------------------------------------------------------------
# Connection checklist items
# ---------------------------------------------------------------------------


@dataclass
class ConnectionRequirement(SerializableModel):
    """A single system that a business needs connected."""

    channel: str  # website, analytics, social, email, paid_media
    provider: str  # wordpress, ga4, facebook, mailchimp, etc.
    priority: str = "required"  # required, recommended, optional
    reason: str = ""
    scopes_needed: List[str] = field(default_factory=list)
    notes: str = ""


# ---------------------------------------------------------------------------
# Pre-built checklists for known clients
# ---------------------------------------------------------------------------

KAICALLS_CHECKLIST: List[ConnectionRequirement] = [
    ConnectionRequirement(
        channel="website",
        provider="github",
        priority="required",
        reason="Next.js repo — PRs for landing page copy, CRO changes, new pages",
        scopes_needed=["read", "write"],
        notes="KaiCalls runs Next.js on Vercel. Website changes go through GitHub PRs, not a CMS API.",
    ),
    ConnectionRequirement(
        channel="website",
        provider="vercel",
        priority="recommended",
        reason="Deploy status, preview URLs, environment management",
        scopes_needed=["read"],
    ),
    ConnectionRequirement(
        channel="analytics",
        provider="ga4",
        priority="required",
        reason="Traffic monitoring, conversion tracking, anomaly detection",
        scopes_needed=["read"],
    ),
    ConnectionRequirement(
        channel="analytics",
        provider="gsc",
        priority="required",
        reason="Search performance monitoring, keyword tracking",
        scopes_needed=["read"],
    ),
    ConnectionRequirement(
        channel="social",
        provider="linkedin",
        priority="recommended",
        reason="B2B thought leadership, company updates",
        scopes_needed=["read", "write"],
    ),
    ConnectionRequirement(
        channel="email",
        provider="loops",
        priority="recommended",
        reason="Transactional emails, lifecycle nurture sequences",
        scopes_needed=["read", "write", "send"],
    ),
    ConnectionRequirement(
        channel="paid_media",
        provider="google_ads",
        priority="optional",
        reason="Paid search campaigns for AI receptionist keywords",
        scopes_needed=["read", "write", "budget"],
    ),
]

STARRS_PARTY_CHECKLIST: List[ConnectionRequirement] = [
    ConnectionRequirement(
        channel="website",
        provider="wordpress",
        priority="required",
        reason="Service pages, booking flow, seasonal content",
        scopes_needed=["read", "write"],
    ),
    ConnectionRequirement(
        channel="analytics",
        provider="ga4",
        priority="required",
        reason="Traffic and booking conversion tracking",
        scopes_needed=["read"],
    ),
    ConnectionRequirement(
        channel="analytics",
        provider="gbp",
        priority="required",
        reason="Google Business Profile — local visibility, reviews, posts",
        scopes_needed=["read", "write"],
    ),
    ConnectionRequirement(
        channel="social",
        provider="facebook",
        priority="required",
        reason="Event promotion, community engagement, local reach",
        scopes_needed=["read", "write", "schedule"],
    ),
    ConnectionRequirement(
        channel="social",
        provider="instagram",
        priority="required",
        reason="Visual content, event showcase, stories",
        scopes_needed=["read", "write"],
    ),
    ConnectionRequirement(
        channel="email",
        provider="mailchimp",
        priority="recommended",
        reason="Event announcements, seasonal campaigns, customer retention",
        scopes_needed=["read", "write", "send"],
    ),
    ConnectionRequirement(
        channel="paid_media",
        provider="meta_ads",
        priority="optional",
        reason="Local event promotion, retargeting",
        scopes_needed=["read", "write", "budget"],
    ),
]

CLIENT_CHECKLISTS: Dict[str, List[ConnectionRequirement]] = {
    "kaicalls": KAICALLS_CHECKLIST,
    "starrs_party": STARRS_PARTY_CHECKLIST,
}


# ---------------------------------------------------------------------------
# Onboarding flow
# ---------------------------------------------------------------------------


class OnboardingFlow:
    """Orchestrates the full onboarding sequence for a new client.

    Steps:
    1. Create brand in RuntimeStore
    2. Fill business profile
    3. Choose archetype
    4. Generate connection checklist
    5. Connect systems (via ConnectionManager)
    6. Verify capabilities
    7. Run first audit
    8. Generate first action queue
    """

    def __init__(
        self,
        connection_manager=None,
        registry=None,
    ):
        self._connection_manager = connection_manager
        self._registry = registry

    @property
    def connections(self):
        if self._connection_manager is None:
            from .connections import ConnectionManager
            self._connection_manager = ConnectionManager(registry=self._registry)
        return self._connection_manager

    # ------------------------------------------------------------------
    # Step 1-3: Brand creation (delegates to existing models)
    # ------------------------------------------------------------------

    def create_brand_stub(
        self,
        *,
        brand_id: str,
        name: str,
        archetype: str = "local_service",
        url: Optional[str] = None,
        persist_profile: bool = True,
    ) -> Dict[str, Any]:
        """Create the minimal brand record to start onboarding.

        By default the durable identity facts (name, url, archetype) are
        persisted to the brand's profile overlay so they survive the
        session instead of evaporating with the process.
        """
        stub = {
            "brand_id": brand_id,
            "name": name,
            "archetype": archetype,
            "url": url,
            "onboarding_stage": "profile",
            "connections_pending": [],
            "connections_complete": [],
        }
        if persist_profile:
            identity: Dict[str, Any] = {"name": name}
            if url:
                identity["url"] = url
            save_profile_overlay(brand_id, {
                "archetype": _normalize_archetype_id(archetype),
                "identity": identity,
            })
        return stub

    # ------------------------------------------------------------------
    # Step 2: Persist profile answers (durable business facts)
    # ------------------------------------------------------------------

    def record_profile_answers(
        self,
        brand_id: str,
        answers: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Persist durable business facts from onboarding answers.

        Answers are mapped to the raw BusinessProfile schema via
        ``extract_profile_facts`` and deep-merged into the brand's
        profile overlay (data/runtime/profile/<brand>.json), so
        subsequent ``build_business_profile`` calls — in this session
        and future ones — reflect them.
        """
        updates = extract_profile_facts(answers)
        if not updates:
            return {
                "brand_id": brand_id,
                "persisted": False,
                "updates": {},
            }
        record = save_profile_overlay(brand_id, updates)
        return {
            "brand_id": brand_id,
            "persisted": True,
            "updates": updates,
            "updated_at": record.get("updated_at"),
        }

    # ------------------------------------------------------------------
    # Step 4: Generate connection checklist
    # ------------------------------------------------------------------

    def get_connection_checklist(
        self,
        brand_id: str,
        *,
        archetype: str = "local_service",
        known_client: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Generate a connection checklist for a brand.

        If ``known_client`` matches a pre-built checklist (kaicalls,
        starrs_party), use that.  Otherwise generate a default checklist
        based on archetype.
        """
        if known_client and known_client in CLIENT_CHECKLISTS:
            items = CLIENT_CHECKLISTS[known_client]
        else:
            items = self._default_checklist(archetype)

        return [
            {
                "channel": item.channel,
                "provider": item.provider,
                "priority": item.priority,
                "reason": item.reason,
                "scopes_needed": item.scopes_needed,
                "notes": item.notes,
                "connected": False,
            }
            for item in items
        ]

    # ------------------------------------------------------------------
    # Step 5: Connect systems
    # ------------------------------------------------------------------

    def initiate_connections(
        self,
        brand_id: str,
        checklist: List[Dict[str, Any]],
        *,
        allowed_origins: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """Initiate connections for all required items in a checklist.

        Returns a list of connection initiation results with connect tokens.
        """
        results = []
        for item in checklist:
            if item.get("connected"):
                continue
            if item.get("priority") == "optional":
                continue
            result = self.connections.initiate_connection(
                brand_id=brand_id,
                channel=item["channel"],
                provider=item["provider"],
                allowed_origins=allowed_origins,
            )
            results.append(result)
        return results

    # ------------------------------------------------------------------
    # Step 6: Verify capabilities
    # ------------------------------------------------------------------

    def verify_readiness(self, brand_id: str) -> Dict[str, Any]:
        """Check that all required connections are healthy."""
        status = self.connections.get_connection_status(brand_id)
        integrations = status.get("integrations", [])

        connected = [i for i in integrations if i.get("status") == "connected"]
        pending = [i for i in integrations if i.get("status") == "pending_auth"]
        errored = [i for i in integrations if i.get("status") in ("error", "degraded")]

        ready = len(errored) == 0 and len(pending) == 0 and len(connected) > 0

        return {
            "brand_id": brand_id,
            "ready": ready,
            "connected_count": len(connected),
            "pending_count": len(pending),
            "errored_count": len(errored),
            "connected_channels": list({i.get("channel") for i in connected}),
            "missing_channels": status.get("scopes", {}).get("missing", []),
        }

    # ------------------------------------------------------------------
    # Step 7-8: First audit and action queue (delegates to application_flow)
    # ------------------------------------------------------------------

    def run_first_audit(self, brand_id: str, business_profile: Any) -> Dict[str, Any]:
        """Run the initial marketing audit for a newly onboarded brand.

        Delegates to the existing audit system. Returns audit results.
        """
        try:
            from .audit import LocalServiceAuditor
            auditor = LocalServiceAuditor()
            result = auditor.audit(business_profile)
            return {
                "brand_id": brand_id,
                "audit_complete": True,
                "finding_count": len(result.findings) if hasattr(result, "findings") else 0,
                "result": result,
            }
        except Exception as exc:
            logger.warning("First audit failed for brand=%s: %s", brand_id, exc)
            return {
                "brand_id": brand_id,
                "audit_complete": False,
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Full onboarding status
    # ------------------------------------------------------------------

    def get_onboarding_status(self, brand_id: str) -> Dict[str, Any]:
        """Return the current onboarding progress for a brand."""
        readiness = self.verify_readiness(brand_id)
        return {
            "brand_id": brand_id,
            "steps": {
                "brand_created": True,
                "profile_complete": False,  # caller checks this
                "archetype_chosen": False,  # caller checks this
                "connections_initiated": readiness["connected_count"] + readiness["pending_count"] > 0,
                "connections_verified": readiness["ready"],
                "first_audit_complete": False,  # caller checks this
                "action_queue_generated": False,  # caller checks this
            },
            "readiness": readiness,
        }

    # ------------------------------------------------------------------
    # Default checklist by archetype
    # ------------------------------------------------------------------

    @staticmethod
    def _default_checklist(archetype: str) -> List[ConnectionRequirement]:
        """Generate a default connection checklist based on business archetype."""
        base = [
            ConnectionRequirement(
                channel="website",
                provider="wordpress",
                priority="required",
                reason="Website management and content updates",
            ),
            ConnectionRequirement(
                channel="analytics",
                provider="ga4",
                priority="required",
                reason="Traffic and conversion tracking",
            ),
        ]

        if archetype == "local_service":
            base.extend([
                ConnectionRequirement(
                    channel="analytics",
                    provider="gbp",
                    priority="required",
                    reason="Local visibility, reviews, Google Maps presence",
                ),
                ConnectionRequirement(
                    channel="social",
                    provider="facebook",
                    priority="recommended",
                    reason="Local community engagement",
                ),
            ])
        elif archetype == "saas":
            base.extend([
                ConnectionRequirement(
                    channel="email",
                    provider="loops",
                    priority="required",
                    reason="Lifecycle emails, onboarding sequences",
                ),
                ConnectionRequirement(
                    channel="social",
                    provider="linkedin",
                    priority="recommended",
                    reason="B2B thought leadership",
                ),
            ])
        elif archetype == "ecommerce":
            base.extend([
                ConnectionRequirement(
                    channel="social",
                    provider="instagram",
                    priority="required",
                    reason="Product showcase, visual marketing",
                ),
                ConnectionRequirement(
                    channel="email",
                    provider="mailchimp",
                    priority="required",
                    reason="Abandoned cart, promotions, lifecycle",
                ),
                ConnectionRequirement(
                    channel="paid_media",
                    provider="meta_ads",
                    priority="recommended",
                    reason="Product retargeting, lookalike audiences",
                ),
            ])

        return base
