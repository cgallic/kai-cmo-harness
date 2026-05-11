from __future__ import annotations

from typing import Any

from kai.connectors.ads.base import (
    AdConnectorConfig,
    AdCreativeSummary,
    AdGroupSummary,
    AdMetrics,
    AdPlatformConnector,
    BudgetStatus,
    CampaignSummary,
)


class _FailingBudgetConnector(AdPlatformConnector):
    @property
    def platform_name(self) -> str:
        return "test_ads"

    def connect(self) -> bool:
        self._connected = True
        return True

    def refresh_auth(self) -> bool:
        return True

    def get_campaigns(self, status_filter: str | None = None) -> list[CampaignSummary]:
        return []

    def get_campaign(self, campaign_id: str) -> CampaignSummary:
        return CampaignSummary(id=campaign_id)

    def create_campaign(self, config: dict[str, Any]) -> CampaignSummary:
        return CampaignSummary()

    def update_campaign(self, campaign_id: str, changes: dict[str, Any]) -> CampaignSummary:
        return CampaignSummary(id=campaign_id)

    def pause_campaign(self, campaign_id: str) -> CampaignSummary:
        return CampaignSummary(id=campaign_id, status="paused")

    def enable_campaign(self, campaign_id: str) -> CampaignSummary:
        return CampaignSummary(id=campaign_id, status="enabled")

    def get_ad_groups(self, campaign_id: str) -> list[AdGroupSummary]:
        return []

    def create_ad_group(self, campaign_id: str, config: dict[str, Any]) -> AdGroupSummary:
        return AdGroupSummary(campaign_id=campaign_id)

    def create_ad(self, ad_group_id: str, creative: dict[str, Any]) -> AdCreativeSummary:
        return AdCreativeSummary(ad_group_id=ad_group_id)

    def get_metrics(self, entity_id: str, entity_type: str, date_range: str) -> AdMetrics:
        return AdMetrics(entity_id=entity_id, entity_type=entity_type, date_range=date_range)

    def get_budget_status(self) -> BudgetStatus:
        raise RuntimeError("read-side unavailable")


class _BudgetConnector(_FailingBudgetConnector):
    def get_budget_status(self) -> BudgetStatus:
        return BudgetStatus(
            account_id=self.config.account_id,
            platform=self.platform_name,
            daily_budget_total=125.0,
            monthly_budget_cap=5000.0,
        )


def test_spend_safety_fails_closed_when_before_state_cannot_be_fetched():
    connector = _FailingBudgetConnector(
        AdConnectorConfig(
            platform="test_ads",
            account_id="acct_1",
            sandbox_mode=False,
            dry_run=False,
            max_daily_spend_usd=200.0,
        )
    )
    connector.connect()

    result = connector._spend_safety_check("adjust_budget", requested_amount=25.0)

    assert result.is_safe is False
    assert "Unable to fetch current budget status" in result.blocks[0]


def test_spend_safety_uses_live_daily_budget_total():
    connector = _BudgetConnector(
        AdConnectorConfig(
            platform="test_ads",
            account_id="acct_1",
            sandbox_mode=False,
            dry_run=False,
            max_daily_spend_usd=200.0,
        )
    )
    connector.connect()

    result = connector._spend_safety_check("adjust_budget", requested_amount=25.0)

    assert result.current_daily_total == 125.0
    assert result.new_daily_total_if_approved == 150.0
    assert result.is_safe is True
