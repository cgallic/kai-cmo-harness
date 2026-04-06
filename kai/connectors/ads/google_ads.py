"""Google Ads connector — campaign management, keyword targeting, and
performance reporting via the Google Ads API.

Implements the ``AdPlatformConnector`` interface using GAQL (Google Ads
Query Language) for data retrieval and the Google Ads mutate services
for campaign, ad-group, and ad creation.  All monetary values are
handled in micros internally (1 USD = 1,000,000 micros).
"""

from __future__ import annotations

import logging
import re
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

# Google Ads API version
API_VERSION = "v17"

# ---------------------------------------------------------------------------
# Status / strategy mapping tables
# ---------------------------------------------------------------------------

_CAMPAIGN_STATUS_MAP: Dict[str, str] = {
    "ENABLED": "enabled",
    "PAUSED": "paused",
    "REMOVED": "removed",
}

_BIDDING_STRATEGY_MAP: Dict[str, str] = {
    "MANUAL_CPC": "manual_cpc",
    "MAXIMIZE_CONVERSIONS": "maximize_conversions",
    "TARGET_CPA": "target_cpa",
    "TARGET_ROAS": "target_roas",
    "MAXIMIZE_CLICKS": "maximize_clicks",
    "MAXIMIZE_CONVERSION_VALUE": "target_roas",
    "TARGET_SPEND": "maximize_clicks",
    "MANUAL_CPV": "manual_cpc",
    "MANUAL_CPM": "manual_cpc",
}

_AD_GROUP_STATUS_MAP: Dict[str, str] = {
    "ENABLED": "enabled",
    "PAUSED": "paused",
    "REMOVED": "removed",
}

_AD_STATUS_MAP: Dict[str, str] = {
    "ENABLED": "active",
    "PAUSED": "paused",
    "REMOVED": "removed",
    "DISAPPROVED": "disapproved",
    "UNDER_REVIEW": "under_review",
}

# Headline: max 30 chars, Description: max 90 chars
_RSA_HEADLINE_MAX = 30
_RSA_HEADLINE_SLOTS = 15
_RSA_DESCRIPTION_MAX = 90
_RSA_DESCRIPTION_SLOTS = 4

# Customer ID format: XXX-XXX-XXXX
_CUSTOMER_ID_RE = re.compile(r"^\d{3}-\d{3}-\d{4}$")


class GoogleAdsConnector(AdPlatformConnector):
    """Google Ads connector using GAQL queries and mutate services.

    Supports Search, Display, Video, Performance Max, and Shopping
    campaign types.  Keywords, negative keywords, and search-terms
    reports are available through additional helper methods.
    """

    # ------------------------------------------------------------------
    # Platform identity
    # ------------------------------------------------------------------

    @property
    def platform_name(self) -> str:
        return "google_ads"

    # ------------------------------------------------------------------
    # Connection lifecycle
    # ------------------------------------------------------------------

    def connect(self) -> bool:
        """Validate credentials and test the connection.

        Requires ``access_token`` and ``account_id`` (format: XXX-XXX-XXXX).
        If ``manager_account_id`` is set it will be used as the
        ``login-customer-id`` header.
        """
        if not self.config.access_token:
            logger.error("Google Ads connect failed: access_token is required")
            return False

        if not self.config.account_id:
            logger.error("Google Ads connect failed: account_id is required")
            return False

        # Validate customer ID format
        if not _CUSTOMER_ID_RE.match(self.config.account_id):
            logger.warning(
                "Google Ads account_id '%s' does not match expected format XXX-XXX-XXXX",
                self.config.account_id,
            )

        if self._is_sandbox():
            logger.info("Google Ads connector connected in sandbox mode")
            self._connected = True
            return True

        try:
            # Test connection by fetching account info
            query = self._build_gaql(
                select=["customer.id", "customer.descriptive_name"],
                from_resource="customer",
                limit=1,
            )
            self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": query},
                headers=self._build_headers(),
            )
            self._connected = True
            logger.info("Google Ads connector connected for account %s", self.config.account_id)
            return True
        except Exception as exc:
            logger.error("Google Ads connect failed: %s", exc)
            self._connected = False
            return False

    def refresh_auth(self) -> bool:
        """Refresh the OAuth access token using the refresh token."""
        if not self.config.refresh_token:
            logger.error("Cannot refresh auth: no refresh_token configured")
            return False

        if self._is_sandbox():
            logger.info("Sandbox mode: simulated token refresh")
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
            self.config.access_token = result.get("access_token", self.config.access_token)
            self.config.token_expiry = datetime.now(timezone.utc).isoformat()
            logger.info("Google Ads token refreshed successfully")
            return True
        except Exception as exc:
            logger.error("Google Ads token refresh failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Campaign management
    # ------------------------------------------------------------------

    def get_campaigns(self, status_filter: Optional[str] = None) -> List[CampaignSummary]:
        """Fetch all campaigns via GAQL, optionally filtered by status."""
        if not self._check_rate_limit():
            return []

        where = "campaign.status != 'REMOVED'"
        if status_filter:
            gaql_status = status_filter.upper()
            where = f"campaign.status = '{gaql_status}'"

        query = self._build_gaql(
            select=[
                "campaign.id",
                "campaign.name",
                "campaign.status",
                "campaign.advertising_channel_type",
                "campaign_budget.amount_micros",
                "campaign.bidding_strategy_type",
                "campaign.start_date",
                "campaign.end_date",
            ],
            from_resource="campaign",
            where=where,
        )

        if self._is_sandbox():
            self._record_request()
            return [
                CampaignSummary(
                    id="sandbox-campaign-1",
                    name="[Sandbox] Example Search Campaign",
                    platform=self.platform_name,
                    status="enabled",
                    objective="traffic",
                    budget_daily=50.0,
                    bid_strategy="maximize_clicks",
                    start_date="2026-01-01",
                    ad_group_count=2,
                    ad_count=4,
                ),
                CampaignSummary(
                    id="sandbox-campaign-2",
                    name="[Sandbox] Example Display Campaign",
                    platform=self.platform_name,
                    status="paused",
                    objective="awareness",
                    budget_daily=25.0,
                    bid_strategy="target_cpa",
                    start_date="2026-02-15",
                    ad_group_count=1,
                    ad_count=2,
                ),
            ]

        try:
            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": query},
                headers=self._build_headers(),
            )
            return self._parse_campaigns(response)
        except Exception as exc:
            logger.error("Failed to fetch Google Ads campaigns: %s", exc)
            return []

    def get_campaign(self, campaign_id: str) -> CampaignSummary:
        """Fetch a single campaign by ID."""
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")

        query = self._build_gaql(
            select=[
                "campaign.id",
                "campaign.name",
                "campaign.status",
                "campaign.advertising_channel_type",
                "campaign_budget.amount_micros",
                "campaign.bidding_strategy_type",
                "campaign.start_date",
                "campaign.end_date",
            ],
            from_resource="campaign",
            where=f"campaign.id = {campaign_id}",
        )

        if self._is_sandbox():
            self._record_request()
            return CampaignSummary(
                id=campaign_id,
                name=f"[Sandbox] Campaign {campaign_id}",
                platform=self.platform_name,
                status="enabled",
                objective="traffic",
                budget_daily=50.0,
                bid_strategy="maximize_clicks",
                ad_group_count=2,
                ad_count=4,
            )

        try:
            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": query},
                headers=self._build_headers(),
            )
            campaigns = self._parse_campaigns(response)
            if not campaigns:
                raise ValueError(f"Campaign {campaign_id} not found")
            return campaigns[0]
        except Exception as exc:
            logger.error("Failed to fetch Google Ads campaign %s: %s", campaign_id, exc)
            raise

    def create_campaign(self, config: Dict[str, Any]) -> CampaignSummary:
        """Create a new Google Ads campaign.

        Required ``config`` keys:
        - ``name``: Campaign name
        - ``budget_daily``: Daily budget in USD
        - ``bidding_strategy``: One of MANUAL_CPC, MAXIMIZE_CONVERSIONS,
          TARGET_CPA, TARGET_ROAS, MAXIMIZE_CLICKS
        - ``campaign_type``: SEARCH, DISPLAY, VIDEO, PERFORMANCE_MAX, SHOPPING

        Optional: ``keyword_targeting``, ``location_targeting``,
        ``language_targeting``.
        """
        # Gate check
        safety = self._check_mutating_allowed("create_campaign")

        # Validate required keys
        required_keys = ["name", "budget_daily", "bidding_strategy", "campaign_type"]
        missing = [k for k in required_keys if k not in config]
        if missing:
            raise ValueError(f"Missing required config keys: {missing}")

        budget_daily_usd = float(config["budget_daily"])
        budget_micros = self._to_micros(budget_daily_usd)

        preview = CampaignSummary(
            id="pending",
            name=config["name"],
            platform=self.platform_name,
            status="draft",
            objective=config.get("objective"),
            budget_daily=budget_daily_usd,
            bid_strategy=_BIDDING_STRATEGY_MAP.get(
                config["bidding_strategy"].upper(),
                config["bidding_strategy"].lower(),
            ),
            start_date=config.get("start_date"),
            end_date=config.get("end_date"),
        )

        # Sandbox or dry-run — return preview
        if self._is_sandbox() or self._is_dry_run():
            preview.id = "preview-campaign-new"
            logger.info(
                "Preview: create_campaign '%s' with $%.2f/day budget",
                config["name"],
                budget_daily_usd,
            )
            return preview

        # Spend safety block
        if not safety.is_safe:
            raise RuntimeError(
                f"Spend safety check failed: {safety.blocks}"
            )

        try:
            self._record_request()

            # Step 1: Create campaign budget
            budget_response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/campaignBudgets:mutate",
                json={
                    "operations": [{
                        "create": {
                            "name": f"{config['name']} Budget",
                            "amount_micros": budget_micros,
                            "delivery_method": "STANDARD",
                        }
                    }]
                },
                headers=self._build_headers(),
            )
            budget_resource = budget_response.get("results", [{}])[0].get("resourceName", "")

            # Step 2: Create campaign
            campaign_config: Dict[str, Any] = {
                "name": config["name"],
                "advertising_channel_type": config["campaign_type"].upper(),
                "status": "PAUSED",  # New campaigns start paused for safety
                "campaign_budget": budget_resource,
                "bidding_strategy_type": config["bidding_strategy"].upper(),
            }

            if config.get("start_date"):
                campaign_config["start_date"] = config["start_date"]
            if config.get("end_date"):
                campaign_config["end_date"] = config["end_date"]

            # Targeting
            if config.get("location_targeting"):
                campaign_config["geo_target_type_setting"] = {
                    "positive_geo_target_type": "PRESENCE_OR_INTEREST",
                }
            if config.get("language_targeting"):
                campaign_config["language_setting"] = {
                    "target_languages": config["language_targeting"],
                }

            self._record_request()
            campaign_response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/campaigns:mutate",
                json={"operations": [{"create": campaign_config}]},
                headers=self._build_headers(),
            )
            campaign_resource = campaign_response.get("results", [{}])[0].get("resourceName", "")
            campaign_id = campaign_resource.rsplit("/", 1)[-1] if campaign_resource else "unknown"

            preview.id = campaign_id
            preview.status = "paused"  # new campaigns start paused
            logger.info("Created Google Ads campaign %s: '%s'", campaign_id, config["name"])
            return preview

        except Exception as exc:
            logger.error("Failed to create Google Ads campaign: %s", exc)
            raise

    def update_campaign(self, campaign_id: str, changes: Dict[str, Any]) -> CampaignSummary:
        """Update a campaign's settings.

        Supported ``changes`` keys: ``name``, ``status``, ``budget_daily``,
        ``bidding_strategy``, ``targeting``.
        """
        safety = self._check_mutating_allowed("update_campaign")

        # If budget is changing, run an explicit spend safety check
        if "budget_daily" in changes:
            budget_safety = self._spend_safety_check(
                "update_campaign_budget",
                requested_amount=float(changes["budget_daily"]),
            )
            if not budget_safety.is_safe:
                raise RuntimeError(
                    f"Spend safety check failed for budget change: {budget_safety.blocks}"
                )

        if self._is_sandbox() or self._is_dry_run():
            logger.info("Preview: update_campaign %s with changes %s", campaign_id, list(changes.keys()))
            return CampaignSummary(
                id=campaign_id,
                name=changes.get("name", f"[Preview] Campaign {campaign_id}"),
                platform=self.platform_name,
                status=changes.get("status", "enabled"),
                budget_daily=changes.get("budget_daily"),
                bid_strategy=changes.get("bidding_strategy"),
            )

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            operations: List[Dict[str, Any]] = []
            update_mask_fields: List[str] = []

            campaign_update: Dict[str, Any] = {
                "resource_name": f"customers/{self._clean_customer_id()}/campaigns/{campaign_id}",
            }

            if "name" in changes:
                campaign_update["name"] = changes["name"]
                update_mask_fields.append("name")

            if "status" in changes:
                campaign_update["status"] = changes["status"].upper()
                update_mask_fields.append("status")

            if "bidding_strategy" in changes:
                campaign_update["bidding_strategy_type"] = changes["bidding_strategy"].upper()
                update_mask_fields.append("bidding_strategy_type")

            if update_mask_fields:
                operations.append({
                    "update": campaign_update,
                    "update_mask": {"paths": update_mask_fields},
                })

            if operations:
                self._record_request()
                self._api_call(
                    "POST",
                    f"https://googleads.googleapis.com/{API_VERSION}/"
                    f"customers/{self._clean_customer_id()}/campaigns:mutate",
                    json={"operations": operations},
                    headers=self._build_headers(),
                )

            # Handle budget updates separately via CampaignBudgetService
            if "budget_daily" in changes:
                budget_micros = self._to_micros(float(changes["budget_daily"]))
                self._record_request()
                self._api_call(
                    "POST",
                    f"https://googleads.googleapis.com/{API_VERSION}/"
                    f"customers/{self._clean_customer_id()}/campaignBudgets:mutate",
                    json={
                        "operations": [{
                            "update": {
                                "resource_name": (
                                    f"customers/{self._clean_customer_id()}/"
                                    f"campaignBudgets/{campaign_id}"
                                ),
                                "amount_micros": budget_micros,
                            },
                            "update_mask": {"paths": ["amount_micros"]},
                        }]
                    },
                    headers=self._build_headers(),
                )

            logger.info("Updated Google Ads campaign %s", campaign_id)
            return self.get_campaign(campaign_id)

        except Exception as exc:
            logger.error("Failed to update Google Ads campaign %s: %s", campaign_id, exc)
            raise

    def pause_campaign(self, campaign_id: str) -> CampaignSummary:
        """Pause a running campaign."""
        return self.update_campaign(campaign_id, {"status": "paused"})

    def enable_campaign(self, campaign_id: str) -> CampaignSummary:
        """Re-enable a paused campaign."""
        return self.update_campaign(campaign_id, {"status": "enabled"})

    # ------------------------------------------------------------------
    # Ad groups
    # ------------------------------------------------------------------

    def get_ad_groups(self, campaign_id: str) -> List[AdGroupSummary]:
        """Fetch ad groups for a campaign via GAQL."""
        if not self._check_rate_limit():
            return []

        query = self._build_gaql(
            select=[
                "ad_group.id",
                "ad_group.name",
                "ad_group.status",
                "ad_group.cpc_bid_micros",
            ],
            from_resource="ad_group",
            where=f"ad_group.campaign = 'customers/{self._clean_customer_id()}/campaigns/{campaign_id}'",
        )

        if self._is_sandbox():
            self._record_request()
            return [
                AdGroupSummary(
                    id="sandbox-adgroup-1",
                    campaign_id=campaign_id,
                    name="[Sandbox] Ad Group 1",
                    status="enabled",
                    bid_amount=1.50,
                    ad_count=2,
                    targeting_summary="Keywords: marketing automation, email marketing",
                ),
            ]

        try:
            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": query},
                headers=self._build_headers(),
            )
            return self._parse_ad_groups(response, campaign_id)
        except Exception as exc:
            logger.error("Failed to fetch ad groups for campaign %s: %s", campaign_id, exc)
            return []

    def create_ad_group(self, campaign_id: str, config: Dict[str, Any]) -> AdGroupSummary:
        """Create a new ad group within a campaign.

        Required ``config`` keys: ``name``.
        Optional: ``bid_amount``, ``status``.
        """
        safety = self._check_mutating_allowed("create_ad_group")

        if "name" not in config:
            raise ValueError("Ad group config must include 'name'")

        bid_amount = config.get("bid_amount")
        bid_micros = self._to_micros(bid_amount) if bid_amount else None

        if self._is_sandbox() or self._is_dry_run():
            logger.info("Preview: create_ad_group '%s' in campaign %s", config["name"], campaign_id)
            return AdGroupSummary(
                id="preview-adgroup-new",
                campaign_id=campaign_id,
                name=config["name"],
                status="paused",
                bid_amount=bid_amount,
                targeting_summary=config.get("targeting_summary"),
            )

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            ad_group_config: Dict[str, Any] = {
                "name": config["name"],
                "campaign": f"customers/{self._clean_customer_id()}/campaigns/{campaign_id}",
                "status": config.get("status", "PAUSED").upper(),
                "type": config.get("type", "SEARCH_STANDARD"),
            }

            if bid_micros is not None:
                ad_group_config["cpc_bid_micros"] = bid_micros

            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/adGroups:mutate",
                json={"operations": [{"create": ad_group_config}]},
                headers=self._build_headers(),
            )
            resource_name = response.get("results", [{}])[0].get("resourceName", "")
            ad_group_id = resource_name.rsplit("/", 1)[-1] if resource_name else "unknown"

            logger.info("Created ad group %s in campaign %s", ad_group_id, campaign_id)
            return AdGroupSummary(
                id=ad_group_id,
                campaign_id=campaign_id,
                name=config["name"],
                status="paused",
                bid_amount=bid_amount,
                targeting_summary=config.get("targeting_summary"),
            )

        except Exception as exc:
            logger.error("Failed to create ad group in campaign %s: %s", campaign_id, exc)
            raise

    # ------------------------------------------------------------------
    # Ads / creatives
    # ------------------------------------------------------------------

    def create_ad(self, ad_group_id: str, creative: Dict[str, Any]) -> AdCreativeSummary:
        """Create an ad creative within an ad group.

        Supports:
        - **Responsive Search Ads**: up to 15 headlines (30 chars each),
          up to 4 descriptions (90 chars each), final URLs, path fields.
        - **Responsive Display Ads**: headlines, descriptions, marketing
          images, logos, business name.

        Validates headline/description lengths before submission.
        """
        safety = self._check_mutating_allowed("create_ad")

        ad_format = creative.get("format", "search_responsive")
        headlines = creative.get("headlines", [])
        descriptions = creative.get("descriptions", [])
        campaign_id = creative.get("campaign_id", "")

        # Validate RSA constraints
        if ad_format == "search_responsive":
            if len(headlines) > _RSA_HEADLINE_SLOTS:
                raise ValueError(
                    f"RSA supports max {_RSA_HEADLINE_SLOTS} headlines, got {len(headlines)}"
                )
            if len(descriptions) > _RSA_DESCRIPTION_SLOTS:
                raise ValueError(
                    f"RSA supports max {_RSA_DESCRIPTION_SLOTS} descriptions, got {len(descriptions)}"
                )
            for i, h in enumerate(headlines):
                if len(h) > _RSA_HEADLINE_MAX:
                    raise ValueError(
                        f"Headline {i + 1} exceeds {_RSA_HEADLINE_MAX} chars: "
                        f"'{h}' ({len(h)} chars)"
                    )
            for i, d in enumerate(descriptions):
                if len(d) > _RSA_DESCRIPTION_MAX:
                    raise ValueError(
                        f"Description {i + 1} exceeds {_RSA_DESCRIPTION_MAX} chars: "
                        f"'{d}' ({len(d)} chars)"
                    )

        preview = AdCreativeSummary(
            id="pending",
            ad_group_id=ad_group_id,
            campaign_id=campaign_id,
            format=ad_format,
            headlines=headlines,
            descriptions=descriptions,
            media_urls=creative.get("media_urls", []),
            landing_url=creative.get("landing_url") or creative.get("final_url"),
            cta=creative.get("cta"),
            status="under_review",
        )

        if self._is_sandbox() or self._is_dry_run():
            preview.id = "preview-ad-new"
            logger.info(
                "Preview: create_ad (%s) in ad group %s with %d headlines",
                ad_format,
                ad_group_id,
                len(headlines),
            )
            return preview

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            if ad_format == "search_responsive":
                ad_config = {
                    "ad": {
                        "responsive_search_ad": {
                            "headlines": [
                                {"text": h, "pinned_field": None} for h in headlines
                            ],
                            "descriptions": [
                                {"text": d, "pinned_field": None} for d in descriptions
                            ],
                        },
                        "final_urls": [creative.get("landing_url", creative.get("final_url", ""))],
                        "path1": creative.get("path1", ""),
                        "path2": creative.get("path2", ""),
                    },
                    "status": "PAUSED",
                    "ad_group": (
                        f"customers/{self._clean_customer_id()}/adGroups/{ad_group_id}"
                    ),
                }
            elif ad_format == "display_responsive":
                ad_config = {
                    "ad": {
                        "responsive_display_ad": {
                            "headlines": [{"text": h} for h in headlines],
                            "descriptions": [{"text": d} for d in descriptions],
                            "marketing_images": [
                                {"asset": url} for url in creative.get("media_urls", [])
                            ],
                            "logo_images": [
                                {"asset": url} for url in creative.get("logo_urls", [])
                            ],
                            "business_name": creative.get("business_name", ""),
                        },
                        "final_urls": [creative.get("landing_url", creative.get("final_url", ""))],
                    },
                    "status": "PAUSED",
                    "ad_group": (
                        f"customers/{self._clean_customer_id()}/adGroups/{ad_group_id}"
                    ),
                }
            else:
                raise ValueError(f"Unsupported Google Ads format: {ad_format}")

            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/adGroupAds:mutate",
                json={"operations": [{"create": ad_config}]},
                headers=self._build_headers(),
            )
            resource_name = response.get("results", [{}])[0].get("resourceName", "")
            ad_id = resource_name.rsplit("/", 1)[-1] if resource_name else "unknown"

            preview.id = ad_id
            logger.info("Created ad %s in ad group %s", ad_id, ad_group_id)
            return preview

        except Exception as exc:
            logger.error("Failed to create ad in ad group %s: %s", ad_group_id, exc)
            raise

    # ------------------------------------------------------------------
    # Metrics & reporting
    # ------------------------------------------------------------------

    def get_metrics(self, entity_id: str, entity_type: str, date_range: str) -> AdMetrics:
        """Fetch performance metrics via GAQL.

        ``date_range`` format: ``"2026-03-01:2026-03-31"``.
        ``entity_type``: ``"campaign"``, ``"ad_group"``, or ``"ad"``.
        """
        if not self._check_rate_limit():
            raise RuntimeError("Rate limit exceeded")

        # Parse date range
        start_date, end_date = self._parse_date_range(date_range)

        # Build select fields based on entity type
        entity_field_map: Dict[str, str] = {
            "campaign": "campaign.id",
            "ad_group": "ad_group.id",
            "ad": "ad_group_ad.ad.id",
        }

        id_field = entity_field_map.get(entity_type)
        if not id_field:
            raise ValueError(f"Unsupported entity_type: {entity_type}")

        from_resource_map: Dict[str, str] = {
            "campaign": "campaign",
            "ad_group": "ad_group",
            "ad": "ad_group_ad",
        }
        from_resource = from_resource_map[entity_type]

        where_field_map: Dict[str, str] = {
            "campaign": "campaign.id",
            "ad_group": "ad_group.id",
            "ad": "ad_group_ad.ad.id",
        }

        query = self._build_gaql(
            select=[
                id_field,
                "metrics.impressions",
                "metrics.clicks",
                "metrics.cost_micros",
                "metrics.conversions",
                "metrics.conversions_value",
                "metrics.average_cpc",
                "metrics.ctr",
                "metrics.search_impression_share",
            ],
            from_resource=from_resource,
            where=(
                f"{where_field_map[entity_type]} = {entity_id} AND "
                f"segments.date BETWEEN '{start_date}' AND '{end_date}'"
            ),
        )

        if self._is_sandbox():
            self._record_request()
            return AdMetrics(
                entity_id=entity_id,
                entity_type=entity_type,
                date_range=date_range,
                impressions=12500,
                clicks=375,
                ctr=3.0,
                conversions=22.0,
                conversion_rate=5.87,
                cost=562.50,
                cpc=1.50,
                cpa=25.57,
                roas=4.2,
                quality_score=7.0,
                impression_share=0.65,
            )

        try:
            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": query},
                headers=self._build_headers(),
            )
            return self._parse_metrics(response, entity_id, entity_type, date_range)
        except Exception as exc:
            logger.error("Failed to fetch metrics for %s %s: %s", entity_type, entity_id, exc)
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
                daily_budget_total=150.0,
                daily_spend_today=87.50,
                monthly_spend=1875.0,
                monthly_budget_cap=self.config.max_monthly_spend_usd,
                budget_utilization_pct=62.5 if self.config.max_monthly_spend_usd else 0.0,
                projected_monthly_spend=2625.0,
                is_over_pace=False,
                alert_triggered=False,
                campaigns_active=3,
                campaigns_paused=1,
            )

        try:
            # Fetch all active campaign budgets and today's spend
            budget_query = self._build_gaql(
                select=[
                    "campaign.id",
                    "campaign.status",
                    "campaign_budget.amount_micros",
                    "metrics.cost_micros",
                ],
                from_resource="campaign",
                where="campaign.status = 'ENABLED' AND segments.date = '2026-01-01'",
            )

            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": budget_query},
                headers=self._build_headers(),
            )
            return self._parse_budget_status(response)
        except Exception as exc:
            logger.error("Failed to fetch budget status: %s", exc)
            raise

    # ------------------------------------------------------------------
    # Keyword management (additional methods)
    # ------------------------------------------------------------------

    def get_keywords(self, ad_group_id: str) -> List[Dict[str, Any]]:
        """Fetch keywords for an ad group with match type, status, quality score."""
        if not self._check_rate_limit():
            return []

        query = self._build_gaql(
            select=[
                "ad_group_criterion.criterion_id",
                "ad_group_criterion.keyword.text",
                "ad_group_criterion.keyword.match_type",
                "ad_group_criterion.status",
                "ad_group_criterion.quality_info.quality_score",
            ],
            from_resource="ad_group_criterion",
            where=(
                f"ad_group.id = {ad_group_id} AND "
                "ad_group_criterion.type = 'KEYWORD'"
            ),
        )

        if self._is_sandbox():
            self._record_request()
            return [
                {
                    "id": "kw-1",
                    "keyword_text": "marketing automation software",
                    "match_type": "PHRASE",
                    "status": "enabled",
                    "quality_score": 7,
                },
                {
                    "id": "kw-2",
                    "keyword_text": "email marketing platform",
                    "match_type": "BROAD",
                    "status": "enabled",
                    "quality_score": 6,
                },
            ]

        try:
            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": query},
                headers=self._build_headers(),
            )
            return self._parse_keywords(response)
        except Exception as exc:
            logger.error("Failed to fetch keywords for ad group %s: %s", ad_group_id, exc)
            return []

    def add_keywords(
        self,
        ad_group_id: str,
        keywords: List[Dict[str, str]],
    ) -> List[Dict[str, Any]]:
        """Add keywords to an ad group.

        Each item in ``keywords``: ``{"keyword_text": "...", "match_type": "BROAD|PHRASE|EXACT"}``.
        """
        safety = self._check_mutating_allowed("add_keywords")

        if self._is_sandbox() or self._is_dry_run():
            logger.info("Preview: add %d keywords to ad group %s", len(keywords), ad_group_id)
            return [
                {
                    "id": f"preview-kw-{i}",
                    "keyword_text": kw["keyword_text"],
                    "match_type": kw.get("match_type", "BROAD"),
                    "status": "enabled",
                    "_preview": True,
                }
                for i, kw in enumerate(keywords)
            ]

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            operations = []
            for kw in keywords:
                operations.append({
                    "create": {
                        "ad_group": f"customers/{self._clean_customer_id()}/adGroups/{ad_group_id}",
                        "keyword": {
                            "text": kw["keyword_text"],
                            "match_type": kw.get("match_type", "BROAD").upper(),
                        },
                        "status": "ENABLED",
                    }
                })

            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/adGroupCriteria:mutate",
                json={"operations": operations},
                headers=self._build_headers(),
            )

            results = []
            for i, result in enumerate(response.get("results", [])):
                results.append({
                    "id": result.get("resourceName", "").rsplit("/", 1)[-1],
                    "keyword_text": keywords[i]["keyword_text"],
                    "match_type": keywords[i].get("match_type", "BROAD"),
                    "status": "enabled",
                })
            logger.info("Added %d keywords to ad group %s", len(results), ad_group_id)
            return results
        except Exception as exc:
            logger.error("Failed to add keywords to ad group %s: %s", ad_group_id, exc)
            raise

    def add_negative_keywords(
        self,
        campaign_id: str,
        keywords: List[str],
    ) -> List[Dict[str, Any]]:
        """Add campaign-level negative keywords."""
        safety = self._check_mutating_allowed("add_negative_keywords")

        if self._is_sandbox() or self._is_dry_run():
            logger.info(
                "Preview: add %d negative keywords to campaign %s",
                len(keywords),
                campaign_id,
            )
            return [
                {
                    "id": f"preview-neg-kw-{i}",
                    "keyword_text": kw,
                    "match_type": "EXACT",
                    "negative": True,
                    "_preview": True,
                }
                for i, kw in enumerate(keywords)
            ]

        if not safety.is_safe:
            raise RuntimeError(f"Spend safety check failed: {safety.blocks}")

        try:
            operations = []
            for kw in keywords:
                operations.append({
                    "create": {
                        "campaign": (
                            f"customers/{self._clean_customer_id()}/campaigns/{campaign_id}"
                        ),
                        "keyword": {
                            "text": kw,
                            "match_type": "EXACT",
                        },
                        "negative": True,
                    }
                })

            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/campaignCriteria:mutate",
                json={"operations": operations},
                headers=self._build_headers(),
            )

            results = []
            for i, result in enumerate(response.get("results", [])):
                results.append({
                    "id": result.get("resourceName", "").rsplit("/", 1)[-1],
                    "keyword_text": keywords[i],
                    "match_type": "EXACT",
                    "negative": True,
                })
            logger.info("Added %d negative keywords to campaign %s", len(results), campaign_id)
            return results
        except Exception as exc:
            logger.error(
                "Failed to add negative keywords to campaign %s: %s",
                campaign_id,
                exc,
            )
            raise

    def get_search_terms_report(
        self,
        campaign_id: str,
        date_range: str,
    ) -> List[Dict[str, Any]]:
        """Fetch the search terms report for a campaign."""
        if not self._check_rate_limit():
            return []

        start_date, end_date = self._parse_date_range(date_range)

        query = self._build_gaql(
            select=[
                "search_term_view.search_term",
                "segments.keyword.info.text",
                "segments.keyword.info.match_type",
                "metrics.impressions",
                "metrics.clicks",
                "metrics.cost_micros",
                "metrics.conversions",
                "metrics.ctr",
            ],
            from_resource="search_term_view",
            where=(
                f"campaign.id = {campaign_id} AND "
                f"segments.date BETWEEN '{start_date}' AND '{end_date}'"
            ),
            order_by="metrics.impressions DESC",
            limit=100,
        )

        if self._is_sandbox():
            self._record_request()
            return [
                {
                    "search_term": "best marketing automation tools",
                    "keyword": "marketing automation",
                    "match_type": "BROAD",
                    "impressions": 450,
                    "clicks": 32,
                    "cost": 48.00,
                    "conversions": 3,
                    "ctr": 7.11,
                },
                {
                    "search_term": "email marketing software comparison",
                    "keyword": "email marketing software",
                    "match_type": "PHRASE",
                    "impressions": 320,
                    "clicks": 28,
                    "cost": 35.00,
                    "conversions": 2,
                    "ctr": 8.75,
                },
            ]

        try:
            self._record_request()
            response = self._api_call(
                "POST",
                f"https://googleads.googleapis.com/{API_VERSION}/"
                f"customers/{self._clean_customer_id()}/googleAds:searchStream",
                json={"query": query},
                headers=self._build_headers(),
            )
            return self._parse_search_terms(response)
        except Exception as exc:
            logger.error(
                "Failed to fetch search terms report for campaign %s: %s",
                campaign_id,
                exc,
            )
            return []

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _convert_micros(self, micros: int) -> float:
        """Convert micros to dollars (1 USD = 1,000,000 micros)."""
        return micros / 1_000_000

    def _to_micros(self, dollars: float) -> int:
        """Convert dollars to micros."""
        return int(dollars * 1_000_000)

    def _build_gaql(
        self,
        select: List[str],
        from_resource: str,
        where: Optional[str] = None,
        order_by: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> str:
        """Build a GAQL (Google Ads Query Language) query string."""
        query = f"SELECT {', '.join(select)} FROM {from_resource}"
        if where:
            query += f" WHERE {where}"
        if order_by:
            query += f" ORDER BY {order_by}"
        if limit is not None:
            query += f" LIMIT {limit}"
        return query

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for Google Ads API calls."""
        headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.config.access_token or ''}",
            "developer-token": self.config.api_key or "",
            "Content-Type": "application/json",
        }
        if self.config.manager_account_id:
            headers["login-customer-id"] = self.config.manager_account_id.replace("-", "")
        return headers

    def _clean_customer_id(self) -> str:
        """Return account_id with dashes removed (Google API format)."""
        return self.config.account_id.replace("-", "")

    def _parse_date_range(self, date_range: str) -> tuple:
        """Parse ``'2026-03-01:2026-03-31'`` into ``('2026-03-01', '2026-03-31')``."""
        parts = date_range.split(":")
        if len(parts) != 2:
            raise ValueError(
                f"Invalid date_range format '{date_range}'. Expected 'YYYY-MM-DD:YYYY-MM-DD'"
            )
        return parts[0].strip(), parts[1].strip()

    def _parse_campaigns(self, response: Dict[str, Any]) -> List[CampaignSummary]:
        """Parse GAQL campaign response into CampaignSummary list."""
        campaigns: List[CampaignSummary] = []
        for batch in response.get("results", []):
            row = batch if isinstance(batch, dict) else {}
            campaign_data = row.get("campaign", {})
            budget_data = row.get("campaignBudget", {})

            status_raw = campaign_data.get("status", "UNKNOWN")
            bid_raw = campaign_data.get("biddingStrategyType", "UNKNOWN")

            budget_micros = budget_data.get("amountMicros", 0)
            budget_daily = self._convert_micros(int(budget_micros)) if budget_micros else None

            campaigns.append(CampaignSummary(
                id=str(campaign_data.get("id", "")),
                name=campaign_data.get("name", ""),
                platform=self.platform_name,
                status=_CAMPAIGN_STATUS_MAP.get(status_raw, status_raw.lower()),
                budget_daily=budget_daily,
                bid_strategy=_BIDDING_STRATEGY_MAP.get(bid_raw, bid_raw.lower()),
                start_date=campaign_data.get("startDate"),
                end_date=campaign_data.get("endDate"),
            ))
        return campaigns

    def _parse_ad_groups(
        self,
        response: Dict[str, Any],
        campaign_id: str,
    ) -> List[AdGroupSummary]:
        """Parse GAQL ad group response into AdGroupSummary list."""
        groups: List[AdGroupSummary] = []
        for batch in response.get("results", []):
            row = batch if isinstance(batch, dict) else {}
            ag_data = row.get("adGroup", {})
            status_raw = ag_data.get("status", "UNKNOWN")
            bid_micros = ag_data.get("cpcBidMicros")
            bid_amount = self._convert_micros(int(bid_micros)) if bid_micros else None

            groups.append(AdGroupSummary(
                id=str(ag_data.get("id", "")),
                campaign_id=campaign_id,
                name=ag_data.get("name", ""),
                status=_AD_GROUP_STATUS_MAP.get(status_raw, status_raw.lower()),
                bid_amount=bid_amount,
            ))
        return groups

    def _parse_metrics(
        self,
        response: Dict[str, Any],
        entity_id: str,
        entity_type: str,
        date_range: str,
    ) -> AdMetrics:
        """Parse GAQL metrics response into an AdMetrics object."""
        totals: Dict[str, float] = {
            "impressions": 0,
            "clicks": 0,
            "cost_micros": 0,
            "conversions": 0.0,
            "conversions_value": 0.0,
        }
        impression_share: Optional[float] = None

        for batch in response.get("results", []):
            row = batch if isinstance(batch, dict) else {}
            metrics = row.get("metrics", {})
            totals["impressions"] += int(metrics.get("impressions", 0))
            totals["clicks"] += int(metrics.get("clicks", 0))
            totals["cost_micros"] += int(metrics.get("costMicros", 0))
            totals["conversions"] += float(metrics.get("conversions", 0))
            totals["conversions_value"] += float(metrics.get("conversionsValue", 0))
            if "searchImpressionShare" in metrics:
                impression_share = float(metrics["searchImpressionShare"])

        cost = self._convert_micros(int(totals["cost_micros"]))
        clicks = int(totals["clicks"])
        impressions = int(totals["impressions"])
        conversions = totals["conversions"]

        return AdMetrics(
            entity_id=entity_id,
            entity_type=entity_type,
            date_range=date_range,
            impressions=impressions,
            clicks=clicks,
            ctr=(clicks / impressions * 100) if impressions > 0 else 0.0,
            conversions=conversions,
            conversion_rate=(conversions / clicks * 100) if clicks > 0 else 0.0,
            cost=cost,
            cpc=(cost / clicks) if clicks > 0 else 0.0,
            cpa=(cost / conversions) if conversions > 0 else 0.0,
            roas=(totals["conversions_value"] / cost) if cost > 0 else 0.0,
            impression_share=impression_share,
        )

    def _parse_budget_status(self, response: Dict[str, Any]) -> BudgetStatus:
        """Parse campaign budget/spend data into a BudgetStatus."""
        daily_budget_total = 0.0
        daily_spend_today = 0.0
        active_count = 0
        paused_count = 0

        for batch in response.get("results", []):
            row = batch if isinstance(batch, dict) else {}
            campaign = row.get("campaign", {})
            budget = row.get("campaignBudget", {})
            metrics = row.get("metrics", {})

            status = campaign.get("status", "")
            if status == "ENABLED":
                active_count += 1
            elif status == "PAUSED":
                paused_count += 1

            budget_micros = int(budget.get("amountMicros", 0))
            daily_budget_total += self._convert_micros(budget_micros)

            cost_micros = int(metrics.get("costMicros", 0))
            daily_spend_today += self._convert_micros(cost_micros)

        # Rough monthly projection
        projected_monthly = daily_spend_today * 30.4
        monthly_cap = self.config.max_monthly_spend_usd

        utilization_pct = 0.0
        is_over_pace = False
        alert_triggered = False

        if monthly_cap and monthly_cap > 0:
            # Use a running estimate for monthly_spend (daily * days elapsed)
            utilization_pct = (projected_monthly / monthly_cap) * 100
            is_over_pace = projected_monthly > monthly_cap
            alert_triggered = utilization_pct >= self.config.spend_alert_threshold_pct

        return BudgetStatus(
            account_id=self.config.account_id,
            platform=self.platform_name,
            daily_budget_total=daily_budget_total,
            daily_spend_today=daily_spend_today,
            monthly_spend=daily_spend_today,  # approximation from today's data
            monthly_budget_cap=monthly_cap,
            budget_utilization_pct=utilization_pct,
            projected_monthly_spend=projected_monthly,
            is_over_pace=is_over_pace,
            alert_triggered=alert_triggered,
            campaigns_active=active_count,
            campaigns_paused=paused_count,
        )

    def _parse_keywords(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse GAQL keyword criterion response."""
        keywords: List[Dict[str, Any]] = []
        for batch in response.get("results", []):
            row = batch if isinstance(batch, dict) else {}
            criterion = row.get("adGroupCriterion", {})
            kw = criterion.get("keyword", {})
            quality = criterion.get("qualityInfo", {})

            keywords.append({
                "id": str(criterion.get("criterionId", "")),
                "keyword_text": kw.get("text", ""),
                "match_type": kw.get("matchType", "BROAD"),
                "status": _AD_GROUP_STATUS_MAP.get(
                    criterion.get("status", "UNKNOWN"),
                    criterion.get("status", "unknown").lower(),
                ),
                "quality_score": quality.get("qualityScore"),
            })
        return keywords

    def _parse_search_terms(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse GAQL search terms report response."""
        terms: List[Dict[str, Any]] = []
        for batch in response.get("results", []):
            row = batch if isinstance(batch, dict) else {}
            stv = row.get("searchTermView", {})
            segments = row.get("segments", {})
            kw_info = segments.get("keyword", {}).get("info", {})
            metrics = row.get("metrics", {})

            cost_micros = int(metrics.get("costMicros", 0))

            terms.append({
                "search_term": stv.get("searchTerm", ""),
                "keyword": kw_info.get("text", ""),
                "match_type": kw_info.get("matchType", ""),
                "impressions": int(metrics.get("impressions", 0)),
                "clicks": int(metrics.get("clicks", 0)),
                "cost": self._convert_micros(cost_micros),
                "conversions": float(metrics.get("conversions", 0)),
                "ctr": float(metrics.get("ctr", 0)) * 100,
            })
        return terms
