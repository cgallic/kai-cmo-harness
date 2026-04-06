"""Meta (Facebook/Instagram) Ads connector — campaign management, audience
targeting, and performance reporting via the Meta Marketing API.

Implements the ``AdPlatformConnector`` interface with Meta-specific
features including Special Ad Categories enforcement, Custom/Lookalike
audiences, and pixel event monitoring.
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

# Meta Marketing API version
API_VERSION = "v19.0"
BASE_URL = f"https://graph.facebook.com/{API_VERSION}"

# ---------------------------------------------------------------------------
# Status / objective mapping tables
# ---------------------------------------------------------------------------

_CAMPAIGN_STATUS_MAP: Dict[str, str] = {
    "ACTIVE": "enabled",
    "PAUSED": "paused",
    "DELETED": "removed",
    "ARCHIVED": "ended",
}

_OBJECTIVE_MAP: Dict[str, str] = {
    "OUTCOME_AWARENESS": "awareness",
    "OUTCOME_TRAFFIC": "traffic",
    "OUTCOME_ENGAGEMENT": "traffic",
    "OUTCOME_LEADS": "leads",
    "OUTCOME_SALES": "sales",
    "OUTCOME_APP_PROMOTION": "app_installs",
}

_BID_STRATEGY_MAP: Dict[str, str] = {
    "LOWEST_COST_WITHOUT_CAP": "lowest_cost",
    "LOWEST_COST_WITH_BID_CAP": "manual_cpc",
    "COST_CAP": "target_cpa",
    "MINIMUM_ROAS": "target_roas",
}

_AD_SET_STATUS_MAP: Dict[str, str] = {
    "ACTIVE": "enabled",
    "PAUSED": "paused",
    "DELETED": "removed",
    "ARCHIVED": "ended",
}

# Industries that trigger Special Ad Categories
_SPECIAL_AD_CATEGORY_INDUSTRIES: Dict[str, str] = {
    "real_estate": "HOUSING",
    "property_management": "HOUSING",
    "mortgage": "HOUSING",
    "housing": "HOUSING",
    "apartments": "HOUSING",
    "home_rental": "HOUSING",
    "staffing": "EMPLOYMENT",
    "recruiting": "EMPLOYMENT",
    "employment": "EMPLOYMENT",
    "job_board": "EMPLOYMENT",
    "hr": "EMPLOYMENT",
    "human_resources": "EMPLOYMENT",
    "lending": "CREDIT",
    "financial_services": "CREDIT",
    "credit": "CREDIT",
    "banking": "CREDIT",
    "insurance": "CREDIT",
    "loan": "CREDIT",
    "credit_card": "CREDIT",
}


class MetaAdsConnector(AdPlatformConnector):
    """Meta (Facebook/Instagram) Ads connector using the Marketing API.

    Supports campaign, ad-set, and ad management with enforcement of
    Special Ad Categories for housing, employment, and credit industries.
    Includes Custom Audience, Lookalike Audience, and Pixel management.
    """

    # ------------------------------------------------------------------
    # Platform identity
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "meta_ads"

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials and test connection.

        Requires ``access_token`` and ``account_id`` (format: act_XXXXXXXXX).
        """
        if not self.config.access_token:
            logger.error("Meta Ads connect failed: access_token is required")
            return False

        if not self.config.account_id:
            logger.error("Meta Ads connect failed: account_id is required")
            return False

        if not self.config.account_id.startswith("act_"):
            logger.warning(
                "Meta Ads account_id '%s' does not start with 'act_'. "
                "Expected format: act_XXXXXXXXX",
                self.config.account_id,
            )

        if self._is_sandbox():
            logger.info("Meta Ads connector connected in sandbox mode")
            self._connected = True
            return True

        try:
            self._record_request()
            self._api_call(
                "GET",
                f"{BASE_URL}/{self.config.account_id}"
                f"?fields=name,account_id,account_status,currency,timezone_name",
                headers=self._build_headers(),
            )
            self._connected = True
            logger.info(
                "Meta Ads connector connected for account %s",
                self.config.account_id,
            )
            return True
        except Exception as exc:
            logger.error("Meta Ads connect failed: %s", exc)
            self._connected = False
            return False

    def refresh_auth(self) -> bool:
        """Refresh the long-lived access token.

        Meta uses long-lived tokens exchanged via the OAuth endpoint.
        """
        if not self.config.access_token:
            logger.error("Cannot refresh auth: no access_token configured")
            return False

        if self._is_sandbox():
            logger.info("Sandbox mode: simulated Meta token refresh")
            self.config.token_expiry = datetime.now(timezone.utc).isoformat()
            return True

        try:
            self._record_request()
            result = self._api_call(
                "GET",
                f"{BASE_URL}/oauth/access_token"
                f"?grant_type=fb_exchange_token"
                f"&client_id={self.config.api_key or ''}"
                f"&client_secret={self.config.api_secret or ''}"
                f"&fb_exchange_token={self.config.access_token}",
                headers=self._build_headers(),
            )
            self.config.access_token = result.get("access_token", self.config.access_token)
            self.config.token_expiry = datetime.now(timezone.utc).isoformat()
            logger.info("Meta Ads token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("Meta Ads token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Campaign management
    # ------------------------------------------------------------------

    def get_campaigns(self, status_filter: Optional[str] = None) -> List[CampaignSummary]:
        """Fetch all campaigns from the ad account."""
        if not self._check_rate_limit():
            return []

        fields = (
            "id,name,status,objective,daily_budget,lifetime_budget,"
            "start_time,stop_time,bid_strategy,special_ad_categories"
        )
        url = f"{BASE_URL}/{self.config.account_id}/campaigns?fields={fields}"

        if status_filter:
            effective_filter = [
                k for k, v in _CAMPAIGN_STATUS_MAP.items()
                if v == status_filter.lower()
            ]
            if effective_filter:
                url += f"&effective_status=['{effective_filter[0]}']"

        if self._is_sandbox():
            self._record_request()
            return [
                CampaignSummary(
                    id="sandbox-meta-campaign-1",
                    name="[Sandbox] Lead Gen Campaign",
                    platform=self.platform_name,
                    status="enabled",
                    objective="leads",
                    budget_daily=75.0,
                    bid_strategy="lowest_cost",
                    start_date="2026-01-15",
                    ad_group_count=3,
                    ad_count=6,
                ),
                CampaignSummary(
                    id="sandbox-meta-campaign-2",
                    name="[Sandbox] Brand Awareness Campaign",
                    platform=self.platform_name,
                    status="paused",
                    objective="awareness",
                    budget_lifetime=2000.0,
                    budget_remaining=850.0,
                    bid_strategy="lowest_cost",
                    start_date="2026-02-01",
                    end_date="2026-04-30",
                    ad_group_count=2,
                    ad_count=4,
                ),
            ]

        try:
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            return self._parse_campaigns(response)
        except Exception as exc:
            logger.error("Failed to fetch Meta Ads campaigns: %s", exc)
            return []

    def get_campaign(self, campaign_id: str) -> CampaignSummary:
        """Fetch a single campaign by ID."""
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")

        fields = (
            "id,name,status,objective,daily_budget,lifetime_budget,"
            "start_time,stop_time,bid_strategy,special_ad_categories"
        )
        url = f"{BASE_URL}/{campaign_id}?fields={fields}"

        if self._is_sandbox():
            self._record_request()
            return CampaignSummary(
                id=campaign_id,
                name=f"[Sandbox] Campaign {campaign_id}",
                platform=self.platform_name,
                status="enabled",
                objective="leads",
                budget_daily=75.0,
                bid_strategy="lowest_cost",
            )

        try:
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            campaigns = self._parse_campaigns({"data": [response]})
            if not campaigns:
                raise ValueError(f"Campaign {campaign_id} not found")
            return campaigns[0]
        except Exception as exc:
            logger.error("Failed to fetch Meta Ads campaign %s: %s", campaign_id, exc)
            raise

    def create_campaign(self, config: Dict[str, Any]) -> CampaignSummary:
        """Create a new Meta Ads campaign.

        Required ``config`` keys:
        - ``name``: Campaign name
        - ``objective``: OUTCOME_AWARENESS, OUTCOME_TRAFFIC, OUTCOME_LEADS,
          OUTCOME_SALES, OUTCOME_APP_PROMOTION
        - ``status``: PAUSED recommended for new campaigns

        Optional:
        - ``special_ad_categories``: list of HOUSING, EMPLOYMENT, CREDIT
        - ``budget_daily`` or ``budget_lifetime``
        - ``business_industry``: auto-detects Special Ad Category

        **Special Ad Categories** are critical: if the business operates in
        housing, employment, or credit, the campaign MUST declare this.
        """
        safety = self._check_mutating_allowed("create_campaign")

        if "name" not in config or "objective" not in config:
            raise ValueError("Campaign config must include 'name' and 'objective'")

        # Auto-detect Special Ad Category if industry is provided
        detected_category = self.check_special_ad_category(
            config.get("business_industry"),
        )
        special_categories = config.get("special_ad_categories", [])
        if detected_category and detected_category not in special_categories:
            logger.warning(
                "Industry '%s' requires Special Ad Category '%s'. "
                "Adding it automatically.",
                config.get("business_industry"),
                detected_category,
            )
            special_categories.append(detected_category)

        objective_raw = config["objective"].upper()
        objective = _OBJECTIVE_MAP.get(objective_raw, objective_raw.lower())

        budget_daily = config.get("budget_daily")
        budget_lifetime = config.get("budget_lifetime")

        preview = CampaignSummary(
            id="pending",
            name=config["name"],
            platform=self.platform_name,
            status="draft",
            objective=objective,
            budget_daily=float(budget_daily) if budget_daily else None,
            budget_lifetime=float(budget_lifetime) if budget_lifetime else None,
            bid_strategy=config.get("bid_strategy", "lowest_cost"),
            start_date=config.get("start_time"),
            end_date=config.get("stop_time"),
        )

        if self._is_sandbox() or self._is_dry_run():
            preview.id = "preview-meta-campaign-new"
            if special_categories:
                logger.info(
                    "Preview: create_campaign '%s' with Special Ad Categories: %s",
                    config["name"],
                    special_categories,
                )
            else:
                logger.info("Preview: create_campaign '%s'", config["name"])
            return preview

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            campaign_data: Dict[str, Any] = {
                "name": config["name"],
                "objective": objective_raw,
                "status": config.get("status", "PAUSED"),
                "special_ad_categories": special_categories or ["NONE"],
            }

            if budget_daily:
                # Meta API expects budget in cents
                campaign_data["daily_budget"] = int(float(budget_daily) * 100)
            if budget_lifetime:
                campaign_data["lifetime_budget"] = int(float(budget_lifetime) * 100)

            if config.get("bid_strategy"):
                campaign_data["bid_strategy"] = config["bid_strategy"].upper()

            if config.get("start_time"):
                campaign_data["start_time"] = config["start_time"]
            if config.get("stop_time"):
                campaign_data["stop_time"] = config["stop_time"]

            self._record_request()
            response = self._api_call(
                "POST",
                f"{BASE_URL}/{self.config.account_id}/campaigns",
                json=campaign_data,
                headers=self._build_headers(),
            )

            campaign_id = response.get("id", "unknown")
            preview.id = campaign_id
            preview.status = _CAMPAIGN_STATUS_MAP.get(
                config.get("status", "PAUSED"),
                "paused",
            )
            logger.info("Created Meta Ads campaign %s: '%s'", campaign_id, config["name"])
            return preview

        except Exception as exc:
            logger.error("Failed to create Meta Ads campaign: %s", exc)
            raise

    def update_campaign(self, campaign_id: str, changes: Dict[str, Any]) -> CampaignSummary:
        """Update a campaign's settings."""
        safety = self._check_mutating_allowed("update_campaign")

        if "budget_daily" in changes or "budget_lifetime" in changes:
            amount = changes.get("budget_daily") or changes.get("budget_lifetime", 0)
            budget_safety = self._spend_safety_check(
                "update_campaign_budget",
                requested_amount=float(amount),
            )
            if not budget_safety.is_safe:
                raise RuntimeError(
                    f"Spend safety check failed for budget change: {budget_safety.blocks}"
                )

        if self._is_sandbox() or self._is_dry_run():
            logger.info(
                "Preview: update_campaign %s with changes %s",
                campaign_id,
                list(changes.keys()),
            )
            return CampaignSummary(
                id=campaign_id,
                name=changes.get("name", f"[Preview] Campaign {campaign_id}"),
                platform=self.platform_name,
                status=changes.get("status", "enabled"),
                budget_daily=changes.get("budget_daily"),
                budget_lifetime=changes.get("budget_lifetime"),
                bid_strategy=changes.get("bid_strategy"),
            )

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            update_data: Dict[str, Any] = {}

            if "name" in changes:
                update_data["name"] = changes["name"]
            if "status" in changes:
                update_data["status"] = changes["status"].upper()
            if "budget_daily" in changes:
                update_data["daily_budget"] = int(float(changes["budget_daily"]) * 100)
            if "budget_lifetime" in changes:
                update_data["lifetime_budget"] = int(float(changes["budget_lifetime"]) * 100)
            if "bid_strategy" in changes:
                update_data["bid_strategy"] = changes["bid_strategy"].upper()

            self._record_request()
            self._api_call(
                "POST",
                f"{BASE_URL}/{campaign_id}",
                json=update_data,
                headers=self._build_headers(),
            )

            logger.info("Updated Meta Ads campaign %s", campaign_id)
            return self.get_campaign(campaign_id)

        except Exception as exc:
            logger.error("Failed to update Meta Ads campaign %s: %s", campaign_id, exc)
            raise

    def pause_campaign(self, campaign_id: str) -> CampaignSummary:
        """Pause a running campaign."""
        return self.update_campaign(campaign_id, {"status": "paused"})

    def enable_campaign(self, campaign_id: str) -> CampaignSummary:
        """Re-enable a paused campaign."""
        return self.update_campaign(campaign_id, {"status": "active"})

    # ------------------------------------------------------------------
    # Ad sets (Meta's term for ad groups)
    # ------------------------------------------------------------------

    def get_ad_groups(self, campaign_id: str) -> List[AdGroupSummary]:
        """Fetch ad sets for a campaign (Meta calls ad groups 'ad sets')."""
        if not self._check_rate_limit():
            return []

        fields = (
            "id,name,status,daily_budget,targeting,"
            "optimization_goal,billing_event"
        )
        url = f"{BASE_URL}/{campaign_id}/adsets?fields={fields}"

        if self._is_sandbox():
            self._record_request()
            return [
                AdGroupSummary(
                    id="sandbox-adset-1",
                    campaign_id=campaign_id,
                    name="[Sandbox] Ad Set — US 25-54",
                    status="enabled",
                    bid_amount=None,
                    ad_count=3,
                    targeting_summary=(
                        "US, ages 25-54, interests: digital marketing, "
                        "small business, entrepreneurship"
                    ),
                ),
                AdGroupSummary(
                    id="sandbox-adset-2",
                    campaign_id=campaign_id,
                    name="[Sandbox] Ad Set — Lookalike 1%",
                    status="enabled",
                    bid_amount=None,
                    ad_count=2,
                    targeting_summary="US, 1% Lookalike of top customers",
                ),
            ]

        try:
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            return self._parse_ad_sets(response, campaign_id)
        except Exception as exc:
            logger.error(
                "Failed to fetch ad sets for campaign %s: %s",
                campaign_id,
                exc,
            )
            return []

    def create_ad_group(self, campaign_id: str, config: Dict[str, Any]) -> AdGroupSummary:
        """Create a new ad set within a campaign.

        Required ``config`` keys: ``name``, ``targeting``,
        ``optimization_goal``, ``billing_event``.
        Optional: ``daily_budget``, ``lifetime_budget``, ``bid_amount``,
        ``start_time``, ``end_time``.
        """
        safety = self._check_mutating_allowed("create_ad_set")

        required = ["name", "targeting", "optimization_goal", "billing_event"]
        missing = [k for k in required if k not in config]
        if missing:
            raise ValueError(f"Missing required ad set config keys: {missing}")

        if self._is_sandbox() or self._is_dry_run():
            logger.info(
                "Preview: create_ad_set '%s' in campaign %s",
                config["name"],
                campaign_id,
            )
            return AdGroupSummary(
                id="preview-adset-new",
                campaign_id=campaign_id,
                name=config["name"],
                status="paused",
                bid_amount=config.get("bid_amount"),
                targeting_summary=self._summarize_targeting(config.get("targeting", {})),
            )

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            adset_data: Dict[str, Any] = {
                "name": config["name"],
                "campaign_id": campaign_id,
                "status": config.get("status", "PAUSED"),
                "targeting": config["targeting"],
                "optimization_goal": config["optimization_goal"],
                "billing_event": config["billing_event"],
            }

            if config.get("daily_budget"):
                adset_data["daily_budget"] = int(float(config["daily_budget"]) * 100)
            if config.get("lifetime_budget"):
                adset_data["lifetime_budget"] = int(float(config["lifetime_budget"]) * 100)
            if config.get("bid_amount"):
                adset_data["bid_amount"] = int(float(config["bid_amount"]) * 100)
            if config.get("start_time"):
                adset_data["start_time"] = config["start_time"]
            if config.get("end_time"):
                adset_data["end_time"] = config["end_time"]

            self._record_request()
            response = self._api_call(
                "POST",
                f"{BASE_URL}/{self.config.account_id}/adsets",
                json=adset_data,
                headers=self._build_headers(),
            )

            adset_id = response.get("id", "unknown")
            logger.info("Created ad set %s in campaign %s", adset_id, campaign_id)

            return AdGroupSummary(
                id=adset_id,
                campaign_id=campaign_id,
                name=config["name"],
                status="paused",
                bid_amount=config.get("bid_amount"),
                targeting_summary=self._summarize_targeting(config.get("targeting", {})),
            )
        except Exception as exc:
            logger.error(
                "Failed to create ad set in campaign %s: %s",
                campaign_id,
                exc,
            )
            raise

    # ------------------------------------------------------------------
    # Ads / creatives
    # ------------------------------------------------------------------

    def create_ad(self, ad_group_id: str, creative: Dict[str, Any]) -> AdCreativeSummary:
        """Create a Meta ad with creative.

        Supports formats: single_image, single_video, carousel, collection.

        Steps:
        1. Create ad creative via ``/{account_id}/adcreatives``
        2. Create ad in the ad set via ``/{ad_set_id}/ads``
        3. Attach tracking specs for pixel/conversion tracking
        """
        safety = self._check_mutating_allowed("create_ad")

        ad_format = creative.get("format", "single_image")
        headlines = creative.get("headlines", [])
        descriptions = creative.get("descriptions", [])
        campaign_id = creative.get("campaign_id", "")

        preview = AdCreativeSummary(
            id="pending",
            ad_group_id=ad_group_id,
            campaign_id=campaign_id,
            format=ad_format,
            headlines=headlines,
            descriptions=descriptions,
            media_urls=creative.get("media_urls", []),
            landing_url=creative.get("landing_url"),
            cta=creative.get("cta", "LEARN_MORE"),
            status="under_review",
        )

        if self._is_sandbox() or self._is_dry_run():
            preview.id = "preview-meta-ad-new"
            logger.info(
                "Preview: create_ad (%s) in ad set %s with %d headlines",
                ad_format,
                ad_group_id,
                len(headlines),
            )
            return preview

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            # Step 1: Create ad creative
            creative_data: Dict[str, Any] = {
                "name": creative.get("creative_name", f"Creative for {ad_group_id}"),
            }

            if ad_format in ("single_image", "single_video"):
                creative_data["object_story_spec"] = {
                    "page_id": creative.get("page_id", ""),
                    "link_data": {
                        "message": descriptions[0] if descriptions else "",
                        "link": creative.get("landing_url", ""),
                        "name": headlines[0] if headlines else "",
                        "description": descriptions[1] if len(descriptions) > 1 else "",
                        "call_to_action": {
                            "type": creative.get("cta", "LEARN_MORE"),
                        },
                    },
                }
                if ad_format == "single_image" and creative.get("media_urls"):
                    creative_data["object_story_spec"]["link_data"]["image_hash"] = (
                        creative.get("image_hash", "")
                    )
                elif ad_format == "single_video" and creative.get("media_urls"):
                    creative_data["object_story_spec"]["video_data"] = {
                        "video_id": creative.get("video_id", ""),
                        "message": descriptions[0] if descriptions else "",
                        "title": headlines[0] if headlines else "",
                        "call_to_action": {
                            "type": creative.get("cta", "LEARN_MORE"),
                            "value": {"link": creative.get("landing_url", "")},
                        },
                    }
                    # Remove link_data when using video_data
                    creative_data["object_story_spec"].pop("link_data", None)

            elif ad_format == "carousel":
                child_attachments = []
                media_urls = creative.get("media_urls", [])
                for i, url in enumerate(media_urls):
                    child = {
                        "link": creative.get("landing_url", ""),
                        "name": headlines[i] if i < len(headlines) else "",
                        "description": descriptions[i] if i < len(descriptions) else "",
                        "image_hash": creative.get("image_hashes", [None])[i] if creative.get("image_hashes") else "",
                        "call_to_action": {
                            "type": creative.get("cta", "LEARN_MORE"),
                        },
                    }
                    child_attachments.append(child)

                creative_data["object_story_spec"] = {
                    "page_id": creative.get("page_id", ""),
                    "link_data": {
                        "message": creative.get("primary_text", ""),
                        "link": creative.get("landing_url", ""),
                        "child_attachments": child_attachments,
                    },
                }

            elif ad_format == "collection":
                creative_data["asset_feed_spec"] = {
                    "bodies": [{"text": d} for d in descriptions],
                    "titles": [{"text": h} for h in headlines],
                    "link_urls": [{"website_url": creative.get("landing_url", "")}],
                    "images": [
                        {"hash": h}
                        for h in creative.get("image_hashes", [])
                    ],
                    "call_to_action_types": [creative.get("cta", "LEARN_MORE")],
                }
            else:
                raise ValueError(f"Unsupported Meta ad format: {ad_format}")

            self._record_request()
            creative_response = self._api_call(
                "POST",
                f"{BASE_URL}/{self.config.account_id}/adcreatives",
                json=creative_data,
                headers=self._build_headers(),
            )
            creative_id = creative_response.get("id", "unknown")

            # Step 2: Create the ad in the ad set
            ad_data: Dict[str, Any] = {
                "name": creative.get("ad_name", f"Ad for {ad_group_id}"),
                "adset_id": ad_group_id,
                "creative": {"creative_id": creative_id},
                "status": "PAUSED",
            }

            # Step 3: Add tracking specs if pixel is configured
            if creative.get("pixel_id"):
                ad_data["tracking_specs"] = [
                    {
                        "action.type": ["offsite_conversion"],
                        "fb_pixel": [creative["pixel_id"]],
                    }
                ]

            self._record_request()
            ad_response = self._api_call(
                "POST",
                f"{BASE_URL}/{self.config.account_id}/ads",
                json=ad_data,
                headers=self._build_headers(),
            )

            ad_id = ad_response.get("id", "unknown")
            preview.id = ad_id
            logger.info(
                "Created Meta ad %s (creative %s) in ad set %s",
                ad_id,
                creative_id,
                ad_group_id,
            )
            return preview

        except Exception as exc:
            logger.error("Failed to create Meta ad in ad set %s: %s", ad_group_id, exc)
            raise

    # ------------------------------------------------------------------
    # Metrics & reporting
    # ------------------------------------------------------------------

    def get_metrics(self, entity_id: str, entity_type: str, date_range: str) -> AdMetrics:
        """Fetch performance insights via the Meta Marketing API.

        Supports breakdowns by age, gender, placement, device_platform.
        ``date_range`` format: ``"2026-03-01:2026-03-31"``.
        """
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")

        start_date, end_date = self._parse_date_range(date_range)

        fields = (
            "impressions,clicks,ctr,actions,cost_per_action_type,"
            "spend,frequency"
        )
        url = (
            f"{BASE_URL}/{entity_id}/insights?"
            f"fields={fields}"
            f"&time_range={{'since':'{start_date}','until':'{end_date}'}}"
        )

        if self._is_sandbox():
            self._record_request()
            return AdMetrics(
                entity_id=entity_id,
                entity_type=entity_type,
                date_range=date_range,
                impressions=45000,
                clicks=1350,
                ctr=3.0,
                conversions=67.0,
                conversion_rate=4.96,
                cost=1012.50,
                cpc=0.75,
                cpa=15.11,
                roas=3.8,
                frequency=2.3,
                relevance_score=7.5,
            )

        try:
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            return self._parse_insights(response, entity_id, entity_type, date_range)
        except Exception as exc:
            logger.error(
                "Failed to fetch metrics for %s %s: %s",
                entity_type,
                entity_id,
                exc,
            )
            raise

    def get_budget_status(self) -> BudgetStatus:
        """Get account-wide budget and spend status."""
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")

        if self._is_sandbox():
            self._record_request()
            return BudgetStatus(
                account_id=self.config.account_id,
                platform=self.platform_name,
                daily_budget_total=200.0,
                daily_spend_today=142.30,
                monthly_spend=2850.0,
                monthly_budget_cap=self.config.max_monthly_spend_usd,
                budget_utilization_pct=71.25 if self.config.max_monthly_spend_usd else 0.0,
                projected_monthly_spend=4325.92,
                is_over_pace=False,
                alert_triggered=False,
                campaigns_active=4,
                campaigns_paused=2,
            )

        try:
            # Fetch active campaigns with budgets
            fields = "id,status,daily_budget,lifetime_budget"
            url = (
                f"{BASE_URL}/{self.config.account_id}/campaigns?"
                f"fields={fields}&effective_status=['ACTIVE','PAUSED']"
            )
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())

            # Fetch today's spend
            insights_url = (
                f"{BASE_URL}/{self.config.account_id}/insights?"
                f"fields=spend&date_preset=today"
            )
            self._record_request()
            insights = self._api_call("GET", insights_url, headers=self._build_headers())

            return self._parse_budget_status(response, insights)
        except Exception as exc:
            logger.error("Failed to fetch Meta Ads budget status: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Audience management (additional methods)
    # ------------------------------------------------------------------

    def get_custom_audiences(self) -> List[Dict[str, Any]]:
        """Fetch custom audiences for the ad account."""
        if not self._check_rate_limit():
            return []

        url = (
            f"{BASE_URL}/{self.config.account_id}/customaudiences"
            f"?fields=id,name,subtype,approximate_count,data_source,"
            f"delivery_status,operation_status"
        )

        if self._is_sandbox():
            self._record_request()
            return [
                {
                    "id": "sandbox-audience-1",
                    "name": "[Sandbox] Website Visitors — Last 30 Days",
                    "subtype": "WEBSITE",
                    "approximate_count": 12500,
                    "delivery_status": "ready",
                },
                {
                    "id": "sandbox-audience-2",
                    "name": "[Sandbox] Customer Email List",
                    "subtype": "CUSTOM",
                    "approximate_count": 5000,
                    "delivery_status": "ready",
                },
            ]

        try:
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            return response.get("data", [])
        except Exception as exc:
            logger.error("Failed to fetch custom audiences: %s", exc)
            return []

    def create_custom_audience(
        self,
        name: str,
        audience_type: str,
        config: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Create a custom audience.

        ``audience_type``: ``"customer_list"``, ``"website_traffic"``,
        ``"lookalike"``.
        """
        safety = self._check_mutating_allowed("create_custom_audience")

        if self._is_sandbox() or self._is_dry_run():
            logger.info("Preview: create_custom_audience '%s' (%s)", name, audience_type)
            return {
                "id": "preview-audience-new",
                "name": name,
                "subtype": audience_type.upper(),
                "_preview": True,
            }

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            audience_data: Dict[str, Any] = {
                "name": name,
                "subtype": audience_type.upper(),
            }

            if audience_type == "customer_list":
                audience_data["customer_file_source"] = config.get("source", "USER_PROVIDED_ONLY")
            elif audience_type == "website_traffic":
                audience_data["rule"] = config.get("rule", {})
                audience_data["retention_days"] = config.get("retention_days", 30)
                audience_data["prefill"] = config.get("prefill", True)
            elif audience_type == "lookalike":
                return self.create_lookalike_audience(
                    source_audience_id=config["source_audience_id"],
                    country=config.get("country", "US"),
                    ratio=config.get("ratio", 0.01),
                )

            self._record_request()
            response = self._api_call(
                "POST",
                f"{BASE_URL}/{self.config.account_id}/customaudiences",
                json=audience_data,
                headers=self._build_headers(),
            )
            logger.info("Created custom audience '%s' (%s)", name, audience_type)
            return response
        except Exception as exc:
            logger.error("Failed to create custom audience '%s': %s", name, exc)
            raise

    def create_lookalike_audience(
        self,
        source_audience_id: str,
        country: str,
        ratio: float = 0.01,
    ) -> Dict[str, Any]:
        """Create a lookalike audience from a source custom audience.

        ``ratio``: 0.01 = 1% lookalike (most similar), up to 0.10 = 10%.
        """
        safety = self._check_mutating_allowed("create_lookalike_audience")

        if self._is_sandbox() or self._is_dry_run():
            pct = int(ratio * 100)
            logger.info(
                "Preview: create_lookalike_audience from %s, %s, %d%%",
                source_audience_id,
                country,
                pct,
            )
            return {
                "id": "preview-lookalike-new",
                "name": f"Lookalike ({pct}%) — {country}",
                "source_audience_id": source_audience_id,
                "country": country,
                "ratio": ratio,
                "_preview": True,
            }

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            pct = int(ratio * 100)
            lookalike_data: Dict[str, Any] = {
                "name": f"Lookalike ({pct}%) — {country} — from {source_audience_id}",
                "subtype": "LOOKALIKE",
                "origin_audience_id": source_audience_id,
                "lookalike_spec": {
                    "type": "similarity",
                    "country": country,
                    "ratio": ratio,
                },
            }

            self._record_request()
            response = self._api_call(
                "POST",
                f"{BASE_URL}/{self.config.account_id}/customaudiences",
                json=lookalike_data,
                headers=self._build_headers(),
            )
            logger.info(
                "Created lookalike audience from %s (%d%%, %s)",
                source_audience_id,
                pct,
                country,
            )
            return response
        except Exception as exc:
            logger.error(
                "Failed to create lookalike audience from %s: %s",
                source_audience_id,
                exc,
            )
            raise

    def get_pixel_events(self) -> List[Dict[str, Any]]:
        """Check pixel status and recent events for the ad account."""
        if not self._check_rate_limit():
            return []

        url = (
            f"{BASE_URL}/{self.config.account_id}/adspixels"
            f"?fields=id,name,last_fired_time,is_created_by_business,"
            f"creation_time"
        )

        if self._is_sandbox():
            self._record_request()
            return [
                {
                    "id": "sandbox-pixel-1",
                    "name": "[Sandbox] Website Pixel",
                    "last_fired_time": "2026-04-01T18:30:00+0000",
                    "is_active": True,
                    "recent_events": [
                        {"event_name": "PageView", "count_last_7d": 4500},
                        {"event_name": "Lead", "count_last_7d": 125},
                        {"event_name": "Purchase", "count_last_7d": 45},
                    ],
                }
            ]

        try:
            self._record_request()
            response = self._api_call("GET", url, headers=self._build_headers())
            return response.get("data", [])
        except Exception as exc:
            logger.error("Failed to fetch pixel events: %s", exc)
            return []

    def check_special_ad_category(
        self,
        business_industry: Optional[str],
    ) -> Optional[str]:
        """Determine if a Special Ad Category is required based on industry.

        Returns the category string (``"HOUSING"``, ``"EMPLOYMENT"``,
        ``"CREDIT"``) or ``None`` if no special category applies.

        **This is critical for Meta Ads compliance.** Campaigns in
        housing, employment, or credit MUST declare the appropriate
        Special Ad Category or risk account suspension.
        """
        if not business_industry:
            return None

        normalized = business_industry.lower().strip().replace(" ", "_")

        # Direct match
        if normalized in _SPECIAL_AD_CATEGORY_INDUSTRIES:
            category = _SPECIAL_AD_CATEGORY_INDUSTRIES[normalized]
            logger.info(
                "Industry '%s' requires Special Ad Category: %s",
                business_industry,
                category,
            )
            return category

        # Partial match — check if any keyword is in the industry string
        for keyword, category in _SPECIAL_AD_CATEGORY_INDUSTRIES.items():
            if keyword in normalized:
                logger.info(
                    "Industry '%s' matches keyword '%s' — requires Special Ad Category: %s",
                    business_industry,
                    keyword,
                    category,
                )
                return category

        return None

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for Meta Marketing API calls."""
        return {
            "Authorization": f"Bearer {self.config.access_token or ''}",
            "Content-Type": "application/json",
        }

    def _parse_date_range(self, date_range: str) -> tuple:
        """Parse ``'2026-03-01:2026-03-31'`` into ``('2026-03-01', '2026-03-31')``."""
        parts = date_range.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid date_range format '{date_range}'. "
                "Expected 'YYYY-MM-DD:YYYY-MM-DD'"
            )
        return parts[0].strip(), parts[1].strip()

    def _parse_campaigns(self, response: Dict[str, Any]) -> List[CampaignSummary]:
        """Parse Meta campaign list response."""
        campaigns: List[CampaignSummary] = []
        for item in response.get("data", []):
            status_raw = item.get("status", "UNKNOWN")
            objective_raw = item.get("objective", "")

            # Meta API returns budgets in cents
            daily_budget_cents = item.get("daily_budget")
            daily_budget = float(daily_budget_cents) / 100 if daily_budget_cents else None

            lifetime_budget_cents = item.get("lifetime_budget")
            lifetime_budget = float(lifetime_budget_cents) / 100 if lifetime_budget_cents else None

            bid_raw = item.get("bid_strategy", "")

            campaigns.append(CampaignSummary(
                id=str(item.get("id", "")),
                name=item.get("name", ""),
                platform=self.platform_name,
                status=_CAMPAIGN_STATUS_MAP.get(status_raw, status_raw.lower()),
                objective=_OBJECTIVE_MAP.get(objective_raw, objective_raw.lower()),
                budget_daily=daily_budget,
                budget_lifetime=lifetime_budget,
                bid_strategy=_BID_STRATEGY_MAP.get(bid_raw, bid_raw.lower()) if bid_raw else None,
                start_date=item.get("start_time"),
                end_date=item.get("stop_time"),
            ))
        return campaigns

    def _parse_ad_sets(
        self,
        response: Dict[str, Any],
        campaign_id: str,
    ) -> List[AdGroupSummary]:
        """Parse Meta ad set list response."""
        groups: List[AdGroupSummary] = []
        for item in response.get("data", []):
            status_raw = item.get("status", "UNKNOWN")
            targeting = item.get("targeting", {})

            daily_budget_cents = item.get("daily_budget")
            bid_amount = float(daily_budget_cents) / 100 if daily_budget_cents else None

            groups.append(AdGroupSummary(
                id=str(item.get("id", "")),
                campaign_id=campaign_id,
                name=item.get("name", ""),
                status=_AD_SET_STATUS_MAP.get(status_raw, status_raw.lower()),
                bid_amount=bid_amount,
                targeting_summary=self._summarize_targeting(targeting),
            ))
        return groups

    def _parse_insights(
        self,
        response: Dict[str, Any],
        entity_id: str,
        entity_type: str,
        date_range: str,
    ) -> AdMetrics:
        """Parse Meta Insights API response."""
        data = response.get("data", [{}])
        row = data[0] if data else {}

        impressions = int(row.get("impressions", 0))
        clicks = int(row.get("clicks", 0))
        spend = float(row.get("spend", 0))
        ctr = float(row.get("ctr", 0))
        frequency = float(row.get("frequency", 0))

        # Parse conversions from the actions array
        conversions = 0.0
        actions = row.get("actions", [])
        for action in actions:
            action_type = action.get("action_type", "")
            if action_type in (
                "offsite_conversion.fb_pixel_lead",
                "offsite_conversion.fb_pixel_purchase",
                "lead",
                "purchase",
                "complete_registration",
            ):
                conversions += float(action.get("value", 0))

        return AdMetrics(
            entity_id=entity_id,
            entity_type=entity_type,
            date_range=date_range,
            impressions=impressions,
            clicks=clicks,
            ctr=ctr,
            conversions=conversions,
            conversion_rate=(conversions / clicks * 100) if clicks > 0 else 0.0,
            cost=spend,
            cpc=(spend / clicks) if clicks > 0 else 0.0,
            cpa=(spend / conversions) if conversions > 0 else 0.0,
            roas=0.0,  # ROAS requires revenue data not in standard insights
            frequency=frequency,
        )

    def _parse_budget_status(
        self,
        campaigns_response: Dict[str, Any],
        insights_response: Dict[str, Any],
    ) -> BudgetStatus:
        """Parse campaign budgets and today's spend into BudgetStatus."""
        daily_budget_total = 0.0
        active_count = 0
        paused_count = 0

        for item in campaigns_response.get("data", []):
            status = item.get("status", "")
            if status == "ACTIVE":
                active_count += 1
            elif status == "PAUSED":
                paused_count += 1

            daily_cents = item.get("daily_budget")
            if daily_cents:
                daily_budget_total += float(daily_cents) / 100

        # Today's spend
        insights_data = insights_response.get("data", [{}])
        today_row = insights_data[0] if insights_data else {}
        daily_spend = float(today_row.get("spend", 0))

        projected_monthly = daily_spend * 30.4
        monthly_cap = self.config.max_monthly_spend_usd

        utilization_pct = 0.0
        is_over_pace = False
        alert_triggered = False

        if monthly_cap and monthly_cap > 0:
            utilization_pct = (projected_monthly / monthly_cap) * 100
            is_over_pace = projected_monthly > monthly_cap
            alert_triggered = utilization_pct >= self.config.spend_alert_threshold_pct

        return BudgetStatus(
            account_id=self.config.account_id,
            platform=self.platform_name,
            daily_budget_total=daily_budget_total,
            daily_spend_today=daily_spend,
            monthly_spend=daily_spend,  # approximation
            monthly_budget_cap=monthly_cap,
            budget_utilization_pct=utilization_pct,
            projected_monthly_spend=projected_monthly,
            is_over_pace=is_over_pace,
            alert_triggered=alert_triggered,
            campaigns_active=active_count,
            campaigns_paused=paused_count,
        )

    def _summarize_targeting(self, targeting: Dict[str, Any]) -> str:
        """Convert a Meta targeting spec into a human-readable summary."""
        parts: List[str] = []

        # Geo targeting
        geo = targeting.get("geo_locations", {})
        countries = geo.get("countries", [])
        cities = geo.get("cities", [])
        if countries:
            parts.append(f"Countries: {', '.join(countries)}")
        if cities:
            city_names = [c.get("name", c.get("key", "")) for c in cities]
            parts.append(f"Cities: {', '.join(city_names)}")

        # Age / gender
        age_min = targeting.get("age_min")
        age_max = targeting.get("age_max")
        if age_min or age_max:
            parts.append(f"Ages {age_min or '?'}-{age_max or '?'}")

        genders = targeting.get("genders", [])
        gender_map = {1: "Male", 2: "Female"}
        if genders:
            parts.append(
                f"Gender: {', '.join(gender_map.get(g, str(g)) for g in genders)}"
            )

        # Interests
        interests = targeting.get("flexible_spec", [])
        if interests:
            interest_names = []
            for spec in interests:
                for item in spec.get("interests", []):
                    interest_names.append(item.get("name", ""))
            if interest_names:
                parts.append(f"Interests: {', '.join(interest_names[:5])}")

        # Custom audiences
        custom_audiences = targeting.get("custom_audiences", [])
        if custom_audiences:
            parts.append(f"Custom Audiences: {len(custom_audiences)}")

        return "; ".join(parts) if parts else "No targeting specified"
