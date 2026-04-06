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

from .models import SerializableModel

logger = logging.getLogger(__name__)


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
    ) -> Dict[str, Any]:
        """Create the minimal brand record to start onboarding."""
        return {
            "brand_id": brand_id,
            "name": name,
            "archetype": archetype,
            "url": url,
            "onboarding_stage": "profile",
            "connections_pending": [],
            "connections_complete": [],
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
