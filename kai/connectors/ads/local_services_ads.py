"""Google Local Services Ads connector — lead management, budget control,
review monitoring, and profile management via the Local Services API.

Local Services Ads (LSA) differ from traditional Google Ads campaigns:
there is no campaign/ad-group/ad hierarchy.  Instead, Google manages a
single LSA profile per business with a weekly budget, job-type
selection, and service-area targeting.  Leads arrive as phone calls,
messages, or bookings.

Abstract methods that do not apply to LSA raise
``NotImplementedError`` with a clear explanation.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .base import (
    AdConnectorConfig,
    AdCreativeSummary,
    AdGroupSummary,
    AdMetrics,
    AdPlatformConnector,
    BudgetStatus,
    CampaignSummary,
)

logger = logging.getLogger(__name__)

_NOT_APPLICABLE_MSG = (
    "Local Services Ads does not support direct campaign/ad creation. "
    "Use get_leads() and update_budget() instead."
)


class LocalServicesAdsConnector(AdPlatformConnector):
    """Google Local Services Ads connector.

    LSA operates on a pay-per-lead model with a weekly budget.  This
    connector provides lead retrieval, budget management, review
    monitoring, and profile management.  Traditional campaign/ad-group/ad
    operations raise ``NotImplementedError`` because they are not
    applicable to the LSA model.
    """

    # ------------------------------------------------------------------
    # Platform identity
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "local_services_ads"

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials and test the connection."""
        if not self.config.access_token:
            logger.error("LSA connect failed: access_token is required")
            return False

        if not self.config.account_id:
            logger.error("LSA connect failed: account_id is required")
            return False

        if self._is_sandbox():
            logger.info("LSA connector connected in sandbox mode")
            self._connected = True
            return True

        try:
            self._record_request()
            self._api_call(
                "GET",
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}",
                headers=self._build_headers(),
            )
            self._connected = True
            logger.info(
                "LSA connector connected for account %s",
                self.config.account_id,
            )
            return True
        except Exception as exc:
            logger.error("LSA connect failed: %s", exc)
            self._connected = False
            return False

    def refresh_auth(self) -> bool:
        """Refresh the OAuth access token."""
        if not self.config.refresh_token:
            logger.error("Cannot refresh auth: no refresh_token configured")
            return False

        if self._is_sandbox():
            logger.info("Sandbox mode: simulated LSA token refresh")
            self.config.token_expiry = datetime.now(timezone.utc).isoformat()
            return True

        try:
            result = self._api_call(
                "POST",
                "https://oauth2.googleapis.com/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": self.config.refresh_token,
                    "client_id": self.config.api_key or "",
                    "client_secret": self.config.api_secret or "",
                },
            )
            self.config.access_token = result.get(
                "access_token", self.config.access_token,
            )
            self.config.token_expiry = datetime.now(timezone.utc).isoformat()
            logger.info("LSA token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("LSA token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Campaign management (LSA-adapted)
    # ------------------------------------------------------------------

    def get_campaigns(self, status_filter: Optional[str] = None) -> List[CampaignSummary]:
        """Return a single CampaignSummary representing the LSA profile.

        LSA does not have traditional campaigns.  The profile itself is
        treated as the single "campaign" with its weekly budget, enabled
        job types, and service areas.
        """
        if not self._check_rate_limit():
            return []

        if self._is_sandbox():
            self._record_request()
            return [
                CampaignSummary(
                    id=f"lsa-profile-{self.config.account_id}",
                    name="[Sandbox] Local Services Ads Profile",
                    platform=self.platform_name,
                    status="enabled",
                    objective="leads",
                    budget_daily=None,
                    budget_lifetime=None,
                    spend_today=45.00,
                    spend_total=1250.00,
                    bid_strategy="pay_per_lead",
                    ad_group_count=0,
                    ad_count=0,
                ),
            ]

        try:
            profile = self.get_profile()
            self._record_request()

            status = "enabled"
            if status_filter and status_filter != status:
                return []

            return [
                CampaignSummary(
                    id=f"lsa-profile-{self.config.account_id}",
                    name=profile.get("business_name", "Local Services Profile"),
                    platform=self.platform_name,
                    status=status,
                    objective="leads",
                    bid_strategy="pay_per_lead",
                ),
            ]
        except Exception as exc:
            logger.error("Failed to fetch LSA profile as campaign: %s", exc)
            return []

    def get_campaign(self, campaign_id: str) -> CampaignSummary:
        """Return the LSA profile as a single campaign."""
        campaigns = self.get_campaigns()
        if campaigns:
            return campaigns[0]
        raise ValueError(f"LSA profile not found for account {self.config.account_id}")

    def create_campaign(self, config: Dict[str, Any]) -> CampaignSummary:
        """Not applicable for Local Services Ads."""
        raise NotImplementedError(_NOT_APPLICABLE_MSG)

    def update_campaign(self, campaign_id: str, changes: Dict[str, Any]) -> CampaignSummary:
        """Update LSA profile settings.

        Supported changes: ``weekly_budget``, ``service_areas``,
        ``job_types``.  For budget changes, delegates to
        ``update_budget()``.
        """
        if "weekly_budget" in changes:
            self.update_budget(float(changes["weekly_budget"]))

        if "service_areas" in changes:
            self.update_service_areas(changes["service_areas"])

        return self.get_campaign(campaign_id)

    def pause_campaign(self, campaign_id: str) -> CampaignSummary:
        """Not directly supported — LSA profiles cannot be paused via API.

        Setting the weekly budget to 0 effectively pauses the profile.
        """
        logger.warning(
            "LSA profiles cannot be paused directly. "
            "Setting weekly budget to $0 instead."
        )
        self.update_budget(0.0)
        return self.get_campaign(campaign_id)

    def enable_campaign(self, campaign_id: str) -> CampaignSummary:
        """Not directly supported — restore budget to re-enable.

        Raises ``NotImplementedError`` because the previous budget is
        unknown.  Use ``update_budget()`` with the desired amount.
        """
        raise NotImplementedError(
            "Cannot auto-enable LSA profile without knowing the target "
            "weekly budget. Use update_budget(amount) instead."
        )

    # ------------------------------------------------------------------
    # Ad groups and ads (not applicable)
    # ------------------------------------------------------------------

    def get_ad_groups(self, campaign_id: str) -> List[AdGroupSummary]:
        """Not applicable for Local Services Ads."""
        raise NotImplementedError(_NOT_APPLICABLE_MSG)

    def create_ad_group(self, campaign_id: str, config: Dict[str, Any]) -> AdGroupSummary:
        """Not applicable for Local Services Ads."""
        raise NotImplementedError(_NOT_APPLICABLE_MSG)

    def create_ad(self, ad_group_id: str, creative: Dict[str, Any]) -> AdCreativeSummary:
        """Not applicable for Local Services Ads."""
        raise NotImplementedError(_NOT_APPLICABLE_MSG)

    # ------------------------------------------------------------------
    # Leads
    # ------------------------------------------------------------------

    def get_leads(
        self,
        date_range: Optional[str] = None,
        lead_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch leads (phone calls, messages, bookings) from LSA.

        Each lead includes:
        - ``id``: Lead ID
        - ``lead_type``: PHONE_CALL, MESSAGE, or BOOKING
        - ``customer_phone``: Customer phone number
        - ``customer_name``: Customer name
        - ``creation_time``: ISO timestamp
        - ``service_category``: Requested service category
        - ``charged``: Whether Google charged for this lead
        - ``charge_amount``: Amount charged (USD)

        Filtering by ``date_range`` (``"YYYY-MM-DD:YYYY-MM-DD"``) and
        ``lead_type`` (``"PHONE_CALL"``, ``"MESSAGE"``, ``"BOOKING"``)
        is supported.
        """
        if not self._check_rate_limit():
            return []

        if self._is_sandbox():
            self._record_request()
            sandbox_leads = [
                {
                    "id": "sandbox-lead-1",
                    "lead_type": "PHONE_CALL",
                    "customer_phone": "+1-555-0101",
                    "customer_name": "Jane Smith",
                    "creation_time": "2026-04-01T14:30:00Z",
                    "service_category": "plumbing",
                    "charged": True,
                    "charge_amount": 35.00,
                },
                {
                    "id": "sandbox-lead-2",
                    "lead_type": "MESSAGE",
                    "customer_phone": "+1-555-0102",
                    "customer_name": "John Doe",
                    "creation_time": "2026-04-01T16:45:00Z",
                    "service_category": "hvac",
                    "charged": True,
                    "charge_amount": 45.00,
                },
                {
                    "id": "sandbox-lead-3",
                    "lead_type": "BOOKING",
                    "customer_phone": "+1-555-0103",
                    "customer_name": "Sarah Johnson",
                    "creation_time": "2026-04-02T09:15:00Z",
                    "service_category": "plumbing",
                    "charged": False,
                    "charge_amount": 0.00,
                },
            ]

            # Apply filters
            if lead_type:
                sandbox_leads = [
                    l for l in sandbox_leads
                    if l["lead_type"] == lead_type.upper()
                ]

            return sandbox_leads

        try:
            url = (
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}/leads"
            )

            params: Dict[str, str] = {}
            if date_range:
                start, end = date_range.split(":")
                params["start_date"] = start.strip()
                params["end_date"] = end.strip()
            if lead_type:
                params["lead_type"] = lead_type.upper()

            self._record_request()
            response = self._api_call(
                "GET",
                url,
                params=params,
                headers=self._build_headers(),
            )
            return self._parse_leads(response)
        except Exception as exc:
            logger.error("Failed to fetch LSA leads: %s", exc)
            return []

    # ------------------------------------------------------------------
    # Budget management
    # ------------------------------------------------------------------

    def update_budget(self, weekly_budget: float) -> Dict[str, Any]:
        """Update the weekly budget cap for the LSA profile.

        Runs spend safety check before applying changes.
        """
        safety = self._check_mutating_allowed("update_budget")

        # Convert weekly to daily for spend safety check
        daily_equivalent = weekly_budget / 7.0
        budget_safety = self._spend_safety_check(
            "update_lsa_weekly_budget",
            requested_amount=daily_equivalent,
        )

        if self._is_sandbox() or self._is_dry_run():
            logger.info(
                "Preview: update LSA weekly budget to $%.2f",
                weekly_budget,
            )
            return {
                "account_id": self.config.account_id,
                "weekly_budget": weekly_budget,
                "daily_equivalent": daily_equivalent,
                "spend_safety": budget_safety.model_dump() if hasattr(budget_safety, "model_dump") else {},
                "_preview": True,
            }

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")
        if not budget_safety.is_safe:
            raise RuntimeError(
                f"Budget safety check failed: {budget_safety.blocks}"
            )

        try:
            self._record_request()
            response = self._api_call(
                "PATCH",
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}",
                json={"weeklyBudget": {"amount": weekly_budget, "currency": self.config.currency}},
                headers=self._build_headers(),
            )
            logger.info(
                "Updated LSA weekly budget to $%.2f for account %s",
                weekly_budget,
                self.config.account_id,
            )
            return {
                "account_id": self.config.account_id,
                "weekly_budget": weekly_budget,
                "response": response,
            }
        except Exception as exc:
            logger.error("Failed to update LSA budget: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Reviews
    # ------------------------------------------------------------------

    def get_reviews(self) -> List[Dict[str, Any]]:
        """Fetch Google Guaranteed reviews for the LSA profile.

        Each review includes: ``reviewer_name``, ``rating``, ``comment``,
        ``response``, ``created_at``.
        """
        if not self._check_rate_limit():
            return []

        if self._is_sandbox():
            self._record_request()
            return [
                {
                    "id": "sandbox-review-1",
                    "reviewer_name": "Alice W.",
                    "rating": 5,
                    "comment": "Excellent service! Fixed the leak in under an hour.",
                    "response": "Thank you Alice! We appreciate your business.",
                    "created_at": "2026-03-28T10:00:00Z",
                },
                {
                    "id": "sandbox-review-2",
                    "reviewer_name": "Bob M.",
                    "rating": 4,
                    "comment": "Good work, arrived on time. Slightly pricey.",
                    "response": None,
                    "created_at": "2026-03-25T14:30:00Z",
                },
                {
                    "id": "sandbox-review-3",
                    "reviewer_name": "Carol T.",
                    "rating": 5,
                    "comment": "Very professional and clean work.",
                    "response": None,
                    "created_at": "2026-03-20T09:15:00Z",
                },
            ]

        try:
            url = (
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}/reviews"
            )
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            return self._parse_reviews(response)
        except Exception as exc:
            logger.error("Failed to fetch LSA reviews: %s", exc)
            return []

    def respond_to_review(
        self,
        review_id: str,
        response_text: str,
    ) -> Dict[str, Any]:
        """Submit a response to a review."""
        safety = self._check_mutating_allowed("respond_to_review")

        if self._is_sandbox() or self._is_dry_run():
            logger.info(
                "Preview: respond to review %s with: '%s'",
                review_id,
                response_text[:50],
            )
            return {
                "review_id": review_id,
                "response_text": response_text,
                "_preview": True,
            }

        if not safety.is_safe:
            raise RuntimeError(f"Safety check failed: {safety.blocks}")

        try:
            self._record_request()
            result = self._api_call(
                "POST",
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}/reviews/{review_id}/reply",
                json={"comment": response_text},
                headers=self._build_headers(),
            )
            logger.info("Responded to LSA review %s", review_id)
            return {
                "review_id": review_id,
                "response_text": response_text,
                "result": result,
            }
        except Exception as exc:
            logger.error("Failed to respond to review %s: %s", review_id, exc)
            raise

    # ------------------------------------------------------------------
    # Profile management
    # ------------------------------------------------------------------

    def get_profile(self) -> Dict[str, Any]:
        """Fetch the business profile for the LSA account.

        Returns: categories, service areas, hours, license info,
        insurance info, background check status.
        """
        if not self._check_rate_limit():
            return {}

        if self._is_sandbox():
            self._record_request()
            return {
                "account_id": self.config.account_id,
                "business_name": "[Sandbox] ABC Plumbing & HVAC",
                "categories": ["plumbing", "hvac", "water_heater"],
                "service_areas": [
                    {"type": "city", "name": "Austin, TX"},
                    {"type": "zip", "code": "78701"},
                    {"type": "zip", "code": "78702"},
                ],
                "hours": {
                    "monday": "08:00-18:00",
                    "tuesday": "08:00-18:00",
                    "wednesday": "08:00-18:00",
                    "thursday": "08:00-18:00",
                    "friday": "08:00-18:00",
                    "saturday": "09:00-14:00",
                    "sunday": "closed",
                },
                "license_verified": True,
                "insurance_verified": True,
                "background_check_status": "passed",
                "google_guaranteed": True,
                "weekly_budget": 500.00,
                "job_types_enabled": ["plumbing_repair", "drain_cleaning", "hvac_repair"],
            }

        try:
            self._record_request()
            response = self._api_call(
                "GET",
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}",
                headers=self._build_headers(),
            )
            return response
        except Exception as exc:
            logger.error("Failed to fetch LSA profile: %s", exc)
            return {}

    def update_service_areas(
        self,
        areas: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Update service area targeting.

        Each area dict: ``{"type": "zip"|"city"|"radius", ...}``

        - ``zip``: ``{"type": "zip", "code": "78701"}``
        - ``city``: ``{"type": "city", "name": "Austin, TX"}``
        - ``radius``: ``{"type": "radius", "center_zip": "78701", "radius_miles": 25}``
        """
        safety = self._check_mutating_allowed("update_service_areas")

        if self._is_sandbox() or self._is_dry_run():
            logger.info(
                "Preview: update LSA service areas to %d area(s)",
                len(areas),
            )
            return {
                "account_id": self.config.account_id,
                "service_areas": areas,
                "_preview": True,
            }

        if not safety.is_safe:
            raise RuntimeError(f"Safety check failed: {safety.blocks}")

        try:
            self._record_request()
            response = self._api_call(
                "PATCH",
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}",
                json={"serviceAreas": areas},
                headers=self._build_headers(),
            )
            logger.info(
                "Updated LSA service areas for account %s (%d areas)",
                self.config.account_id,
                len(areas),
            )
            return {
                "account_id": self.config.account_id,
                "service_areas": areas,
                "response": response,
            }
        except Exception as exc:
            logger.error("Failed to update LSA service areas: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Metrics
    # ------------------------------------------------------------------

    def get_metrics(self, entity_id: str, entity_type: str, date_range: str) -> AdMetrics:
        """Fetch LSA performance metrics.

        LSA metrics: leads_total (as impressions proxy), leads_charged
        (as clicks proxy), leads_disputed, cost_total, cost_per_lead,
        impression_estimate.
        """
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")

        if self._is_sandbox():
            self._record_request()
            return AdMetrics(
                entity_id=entity_id,
                entity_type=entity_type,
                date_range=date_range,
                impressions=850,  # impression estimate
                clicks=42,  # leads_charged
                ctr=4.94,
                conversions=42.0,  # leads are conversions in LSA
                conversion_rate=100.0,  # every charged lead is a conversion
                cost=1470.00,
                cpc=35.00,  # cost per lead
                cpa=35.00,  # same as CPL for LSA
                roas=0.0,  # not applicable for LSA
                frequency=0.0,
            )

        try:
            start, end = date_range.split(":")
            url = (
                f"https://localservices.googleapis.com/v1/"
                f"accounts/{self.config.account_id}/reports"
                f"?start_date={start.strip()}&end_date={end.strip()}"
            )
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            return self._parse_lsa_metrics(response, entity_id, entity_type, date_range)
        except Exception as exc:
            logger.error("Failed to fetch LSA metrics: %s", exc)
            raise

    def get_budget_status(self) -> BudgetStatus:
        """Get LSA budget and spend status."""
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")

        if self._is_sandbox():
            self._record_request()
            return BudgetStatus(
                account_id=self.config.account_id,
                platform=self.platform_name,
                daily_budget_total=71.43,  # 500/7 weekly budget as daily
                daily_spend_today=45.00,
                monthly_spend=1250.00,
                monthly_budget_cap=self.config.max_monthly_spend_usd,
                budget_utilization_pct=62.5 if self.config.max_monthly_spend_usd else 0.0,
                projected_monthly_spend=1368.00,
                is_over_pace=False,
                alert_triggered=False,
                campaigns_active=1,
                campaigns_paused=0,
            )

        try:
            profile = self.get_profile()
            weekly_budget = profile.get("weekly_budget", 0)
            daily_equivalent = weekly_budget / 7.0

            # Fetch recent spend data
            leads = self.get_leads()
            total_charged = sum(
                l.get("charge_amount", 0)
                for l in leads
                if l.get("charged")
            )

            projected_monthly = daily_equivalent * 30.4
            monthly_cap = self.config.max_monthly_spend_usd

            utilization_pct = 0.0
            is_over_pace = False
            alert_triggered = False

            if monthly_cap and monthly_cap > 0:
                utilization_pct = (total_charged / monthly_cap) * 100
                is_over_pace = projected_monthly > monthly_cap
                alert_triggered = utilization_pct >= self.config.spend_alert_threshold_pct

            return BudgetStatus(
                account_id=self.config.account_id,
                platform=self.platform_name,
                daily_budget_total=daily_equivalent,
                daily_spend_today=total_charged,
                monthly_spend=total_charged,
                monthly_budget_cap=monthly_cap,
                budget_utilization_pct=utilization_pct,
                projected_monthly_spend=projected_monthly,
                is_over_pace=is_over_pace,
                alert_triggered=alert_triggered,
                campaigns_active=1,
                campaigns_paused=0,
            )
        except Exception as exc:
            logger.error("Failed to fetch LSA budget status: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for Local Services API calls."""
        return {
            "Authorization": f"Bearer {self.config.access_token or ''}",
            "Content-Type": "application/json",
        }

    def _parse_leads(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse LSA leads response."""
        leads: List[Dict[str, Any]] = []
        for item in response.get("leads", []):
            leads.append({
                "id": item.get("leadId", ""),
                "lead_type": item.get("leadType", "UNKNOWN"),
                "customer_phone": item.get("customerPhoneNumber", ""),
                "customer_name": item.get("customerName", ""),
                "creation_time": item.get("creationTime", ""),
                "service_category": item.get("serviceCategory", ""),
                "charged": item.get("chargeStatus") == "CHARGED",
                "charge_amount": float(item.get("chargeAmount", {}).get("amount", 0)),
            })
        return leads

    def _parse_reviews(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse LSA reviews response."""
        reviews: List[Dict[str, Any]] = []
        for item in response.get("reviews", []):
            reviews.append({
                "id": item.get("reviewId", ""),
                "reviewer_name": item.get("reviewerName", ""),
                "rating": int(item.get("starRating", 0)),
                "comment": item.get("comment", ""),
                "response": item.get("reviewReply", {}).get("comment"),
                "created_at": item.get("createTime", ""),
            })
        return reviews

    def _parse_lsa_metrics(
        self,
        response: Dict[str, Any],
        entity_id: str,
        entity_type: str,
        date_range: str,
    ) -> AdMetrics:
        """Parse LSA reporting response into AdMetrics."""
        report = response.get("report", {})

        leads_total = int(report.get("leadsTotal", 0))
        leads_charged = int(report.get("leadsCharged", 0))
        cost_total = float(report.get("costTotal", {}).get("amount", 0))
        impression_estimate = int(report.get("impressionEstimate", 0))

        cpl = (cost_total / leads_charged) if leads_charged > 0 else 0.0

        return AdMetrics(
            entity_id=entity_id,
            entity_type=entity_type,
            date_range=date_range,
            impressions=impression_estimate,
            clicks=leads_charged,  # charged leads as "clicks"
            ctr=(leads_charged / impression_estimate * 100) if impression_estimate > 0 else 0.0,
            conversions=float(leads_charged),
            conversion_rate=100.0,  # every charged lead is a conversion
            cost=cost_total,
            cpc=cpl,
            cpa=cpl,
            roas=0.0,  # not applicable for LSA
            frequency=0.0,
        )
