"""
Facebook/Meta Ads API Module
Pull spend, impressions, clicks, and performance data directly from Meta Marketing API

Setup:
1. Create a Meta Business account and Ad Account
2. Go to developers.facebook.com and create an app
3. Get a long-lived access token (System User recommended for production)
4. Set environment variables:
   - META_ACCESS_TOKEN: Your access token
   - META_AD_ACCOUNT_ID: Your ad account ID (format: act_XXXXXXXXX)
"""

import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any


class FacebookAdsConfig:
    """Configuration for Facebook Ads API"""

    def __init__(self):
        self.access_token = os.getenv("META_ACCESS_TOKEN")
        self.ad_account_id = os.getenv("META_AD_ACCOUNT_ID")
        self.api_version = os.getenv("META_API_VERSION", "v18.0")

    @property
    def is_configured(self) -> bool:
        return bool(self.access_token and self.ad_account_id)


fb_ads_config = FacebookAdsConfig()


class FacebookAds:
    """Facebook/Meta Marketing API client"""

    BASE_URL = "https://graph.facebook.com"

    def __init__(
        self,
        access_token: str = None,
        ad_account_id: str = None,
        api_version: str = None,
    ):
        self.access_token = access_token or fb_ads_config.access_token
        self.ad_account_id = ad_account_id or fb_ads_config.ad_account_id
        self.api_version = api_version or fb_ads_config.api_version

        if not self.access_token:
            raise ValueError(
                "META_ACCESS_TOKEN not set. "
                "Get one from developers.facebook.com"
            )
        if not self.ad_account_id:
            raise ValueError(
                "META_AD_ACCOUNT_ID not set. "
                "Format: act_XXXXXXXXX"
            )

    def _make_request(self, endpoint: str, params: Dict = None) -> Dict:
        """Make API request to Meta Graph API"""
        import requests

        url = f"{self.BASE_URL}/{self.api_version}/{endpoint}"
        params = params or {}
        params["access_token"] = self.access_token

        response = requests.get(url, params=params)

        if response.status_code != 200:
            error_data = response.json().get("error", {})
            raise Exception(
                f"Meta API Error: {error_data.get('message', response.text)}"
            )

        return response.json()

    def _get_date_range(self, days: int = 30) -> Dict:
        """Get date range for API requests"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return {
            "since": start_date.strftime("%Y-%m-%d"),
            "until": end_date.strftime("%Y-%m-%d"),
        }

    # ============ ACCOUNT LEVEL ============

    def get_account_info(self) -> Dict:
        """Get ad account information"""
        return self._make_request(
            self.ad_account_id,
            params={
                "fields": "name,account_id,account_status,currency,timezone_name,spend_cap,amount_spent"
            },
        )

    def get_account_insights(
        self,
        days: int = 30,
        date_preset: str = None,
    ) -> Dict:
        """Get account-level insights (total spend, impressions, etc.)"""
        params = {
            "fields": ",".join([
                "spend",
                "impressions",
                "clicks",
                "reach",
                "cpm",
                "cpc",
                "ctr",
                "frequency",
                "actions",
                "cost_per_action_type",
                "conversions",
                "cost_per_conversion",
            ]),
            "level": "account",
        }

        if date_preset:
            params["date_preset"] = date_preset
        else:
            date_range = self._get_date_range(days)
            params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        response = self._make_request(f"{self.ad_account_id}/insights", params)
        data = response.get("data", [{}])[0]

        return self._format_insights(data)

    def _format_insights(self, data: Dict) -> Dict:
        """Format raw insights data into readable metrics"""
        if not data:
            return {"error": "No data available"}

        spend = float(data.get("spend", 0))
        impressions = int(data.get("impressions", 0))
        clicks = int(data.get("clicks", 0))
        reach = int(data.get("reach", 0))

        # Extract action data
        actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}
        cost_per_action = {
            a["action_type"]: float(a["value"])
            for a in data.get("cost_per_action_type", [])
        }

        return {
            "spend": f"${spend:.2f}",
            "spend_raw": spend,
            "impressions": impressions,
            "clicks": clicks,
            "reach": reach,
            "cpm": f"${float(data.get('cpm', 0)):.2f}",
            "cpc": f"${float(data.get('cpc', 0)):.2f}",
            "ctr": f"{float(data.get('ctr', 0)):.2f}%",
            "frequency": f"{float(data.get('frequency', 0)):.2f}",
            "actions": {
                "link_clicks": actions.get("link_click", 0),
                "landing_page_views": actions.get("landing_page_view", 0),
                "leads": actions.get("lead", 0),
                "purchases": actions.get("purchase", 0),
                "page_engagement": actions.get("page_engagement", 0),
                "post_engagement": actions.get("post_engagement", 0),
                "video_views": actions.get("video_view", 0),
            },
            "cost_per_action": {
                "cost_per_click": f"${cost_per_action.get('link_click', 0):.2f}",
                "cost_per_lead": f"${cost_per_action.get('lead', 0):.2f}",
                "cost_per_landing_page_view": f"${cost_per_action.get('landing_page_view', 0):.2f}",
            },
        }

    # ============ CAMPAIGN LEVEL ============

    def get_campaigns(self, status: str = None) -> List[Dict]:
        """Get all campaigns"""
        params = {
            "fields": "id,name,status,objective,daily_budget,lifetime_budget,budget_remaining,created_time,start_time,stop_time"
        }
        if status:
            params["filtering"] = f'[{{"field":"effective_status","operator":"IN","value":["{status}"]}}]'

        response = self._make_request(f"{self.ad_account_id}/campaigns", params)
        return response.get("data", [])

    def get_campaign_insights(
        self,
        campaign_id: str = None,
        days: int = 30,
    ) -> List[Dict]:
        """Get insights for all campaigns or a specific campaign"""
        params = {
            "fields": ",".join([
                "campaign_id",
                "campaign_name",
                "spend",
                "impressions",
                "clicks",
                "reach",
                "cpm",
                "cpc",
                "ctr",
                "frequency",
                "actions",
                "cost_per_action_type",
            ]),
            "level": "campaign",
        }

        date_range = self._get_date_range(days)
        params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        endpoint = f"{campaign_id}/insights" if campaign_id else f"{self.ad_account_id}/insights"
        response = self._make_request(endpoint, params)

        return [self._format_campaign_insights(d) for d in response.get("data", [])]

    def _format_campaign_insights(self, data: Dict) -> Dict:
        """Format campaign-level insights"""
        actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}
        cost_per_action = {
            a["action_type"]: float(a["value"])
            for a in data.get("cost_per_action_type", [])
        }

        spend = float(data.get("spend", 0))
        leads = actions.get("lead", 0)
        clicks = int(data.get("clicks", 0))

        return {
            "campaign_id": data.get("campaign_id"),
            "campaign_name": data.get("campaign_name"),
            "spend": f"${spend:.2f}",
            "spend_raw": spend,
            "impressions": int(data.get("impressions", 0)),
            "clicks": clicks,
            "reach": int(data.get("reach", 0)),
            "cpm": f"${float(data.get('cpm', 0)):.2f}",
            "cpc": f"${float(data.get('cpc', 0)):.2f}",
            "ctr": f"{float(data.get('ctr', 0)):.2f}%",
            "frequency": f"{float(data.get('frequency', 0)):.2f}",
            "leads": leads,
            "cost_per_lead": f"${cost_per_action.get('lead', 0):.2f}" if leads > 0 else "N/A",
            "link_clicks": actions.get("link_click", 0),
            "landing_page_views": actions.get("landing_page_view", 0),
        }

    # ============ AD SET LEVEL ============

    def get_adsets(self, campaign_id: str = None) -> List[Dict]:
        """Get ad sets"""
        params = {
            "fields": "id,name,status,campaign_id,daily_budget,lifetime_budget,targeting,optimization_goal,billing_event"
        }

        endpoint = (
            f"{campaign_id}/adsets" if campaign_id else f"{self.ad_account_id}/adsets"
        )
        response = self._make_request(endpoint, params)
        return response.get("data", [])

    def get_adset_insights(self, days: int = 30) -> List[Dict]:
        """Get insights at ad set level"""
        params = {
            "fields": ",".join([
                "adset_id",
                "adset_name",
                "campaign_name",
                "spend",
                "impressions",
                "clicks",
                "reach",
                "cpm",
                "cpc",
                "ctr",
                "actions",
                "cost_per_action_type",
            ]),
            "level": "adset",
        }

        date_range = self._get_date_range(days)
        params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        response = self._make_request(f"{self.ad_account_id}/insights", params)

        results = []
        for data in response.get("data", []):
            actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}
            cost_per_action = {
                a["action_type"]: float(a["value"])
                for a in data.get("cost_per_action_type", [])
            }

            spend = float(data.get("spend", 0))
            leads = actions.get("lead", 0)

            results.append({
                "adset_id": data.get("adset_id"),
                "adset_name": data.get("adset_name"),
                "campaign_name": data.get("campaign_name"),
                "spend": f"${spend:.2f}",
                "spend_raw": spend,
                "impressions": int(data.get("impressions", 0)),
                "clicks": int(data.get("clicks", 0)),
                "reach": int(data.get("reach", 0)),
                "cpm": f"${float(data.get('cpm', 0)):.2f}",
                "cpc": f"${float(data.get('cpc', 0)):.2f}",
                "ctr": f"{float(data.get('ctr', 0)):.2f}%",
                "leads": leads,
                "cost_per_lead": f"${cost_per_action.get('lead', 0):.2f}" if leads > 0 else "N/A",
            })

        return results

    # ============ AD LEVEL ============

    def get_ads(self, adset_id: str = None) -> List[Dict]:
        """Get ads"""
        params = {
            "fields": "id,name,status,adset_id,campaign_id,creative,effective_status"
        }

        endpoint = f"{adset_id}/ads" if adset_id else f"{self.ad_account_id}/ads"
        response = self._make_request(endpoint, params)
        return response.get("data", [])

    def get_ad_insights(self, days: int = 30) -> List[Dict]:
        """Get insights at ad (creative) level"""
        params = {
            "fields": ",".join([
                "ad_id",
                "ad_name",
                "adset_name",
                "campaign_name",
                "spend",
                "impressions",
                "clicks",
                "reach",
                "cpm",
                "cpc",
                "ctr",
                "actions",
                "cost_per_action_type",
            ]),
            "level": "ad",
        }

        date_range = self._get_date_range(days)
        params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        response = self._make_request(f"{self.ad_account_id}/insights", params)

        results = []
        for data in response.get("data", []):
            actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}
            cost_per_action = {
                a["action_type"]: float(a["value"])
                for a in data.get("cost_per_action_type", [])
            }

            spend = float(data.get("spend", 0))
            leads = actions.get("lead", 0)

            results.append({
                "ad_id": data.get("ad_id"),
                "ad_name": data.get("ad_name"),
                "adset_name": data.get("adset_name"),
                "campaign_name": data.get("campaign_name"),
                "spend": f"${spend:.2f}",
                "spend_raw": spend,
                "impressions": int(data.get("impressions", 0)),
                "clicks": int(data.get("clicks", 0)),
                "reach": int(data.get("reach", 0)),
                "cpm": f"${float(data.get('cpm', 0)):.2f}",
                "cpc": f"${float(data.get('cpc', 0)):.2f}",
                "ctr": f"{float(data.get('ctr', 0)):.2f}%",
                "leads": leads,
                "cost_per_lead": f"${cost_per_action.get('lead', 0):.2f}" if leads > 0 else "N/A",
                "link_clicks": actions.get("link_click", 0),
                "video_views": actions.get("video_view", 0),
                "landing_page_views": actions.get("landing_page_view", 0),
            })

        return results

    # ============ DAILY BREAKDOWN ============

    def get_daily_spend(self, days: int = 30) -> List[Dict]:
        """Get daily spend breakdown"""
        params = {
            "fields": "spend,impressions,clicks,reach,cpm,cpc,ctr,actions",
            "level": "account",
            "time_increment": 1,  # Daily breakdown
        }

        date_range = self._get_date_range(days)
        params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        response = self._make_request(f"{self.ad_account_id}/insights", params)

        results = []
        for data in response.get("data", []):
            actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}

            results.append({
                "date": data.get("date_start"),
                "spend": f"${float(data.get('spend', 0)):.2f}",
                "spend_raw": float(data.get("spend", 0)),
                "impressions": int(data.get("impressions", 0)),
                "clicks": int(data.get("clicks", 0)),
                "reach": int(data.get("reach", 0)),
                "cpm": f"${float(data.get('cpm', 0)):.2f}",
                "cpc": f"${float(data.get('cpc', 0)):.2f}",
                "ctr": f"{float(data.get('ctr', 0)):.2f}%",
                "leads": actions.get("lead", 0),
                "link_clicks": actions.get("link_click", 0),
            })

        return sorted(results, key=lambda x: x["date"])

    # ============ DEMOGRAPHIC BREAKDOWN ============

    def get_age_gender_breakdown(self, days: int = 30) -> List[Dict]:
        """Get performance by age and gender"""
        params = {
            "fields": "spend,impressions,clicks,reach,actions",
            "breakdowns": "age,gender",
        }

        date_range = self._get_date_range(days)
        params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        response = self._make_request(f"{self.ad_account_id}/insights", params)

        results = []
        for data in response.get("data", []):
            actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}
            spend = float(data.get("spend", 0))
            clicks = int(data.get("clicks", 0))
            leads = actions.get("lead", 0)

            results.append({
                "age": data.get("age"),
                "gender": data.get("gender"),
                "spend": f"${spend:.2f}",
                "spend_raw": spend,
                "impressions": int(data.get("impressions", 0)),
                "clicks": clicks,
                "reach": int(data.get("reach", 0)),
                "leads": leads,
                "cost_per_lead": f"${spend / leads:.2f}" if leads > 0 else "N/A",
            })

        return results

    def get_placement_breakdown(self, days: int = 30) -> List[Dict]:
        """Get performance by placement (Feed, Stories, Reels, etc.)"""
        params = {
            "fields": "spend,impressions,clicks,reach,actions",
            "breakdowns": "publisher_platform,platform_position",
        }

        date_range = self._get_date_range(days)
        params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        response = self._make_request(f"{self.ad_account_id}/insights", params)

        results = []
        for data in response.get("data", []):
            actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}
            spend = float(data.get("spend", 0))
            clicks = int(data.get("clicks", 0))
            leads = actions.get("lead", 0)

            results.append({
                "platform": data.get("publisher_platform"),
                "position": data.get("platform_position"),
                "spend": f"${spend:.2f}",
                "spend_raw": spend,
                "impressions": int(data.get("impressions", 0)),
                "clicks": clicks,
                "reach": int(data.get("reach", 0)),
                "leads": leads,
                "cpc": f"${spend / clicks:.2f}" if clicks > 0 else "N/A",
            })

        return results

    def get_device_breakdown(self, days: int = 30) -> List[Dict]:
        """Get performance by device"""
        params = {
            "fields": "spend,impressions,clicks,reach,actions",
            "breakdowns": "device_platform",
        }

        date_range = self._get_date_range(days)
        params["time_range"] = f'{{"since":"{date_range["since"]}","until":"{date_range["until"]}"}}'

        response = self._make_request(f"{self.ad_account_id}/insights", params)

        results = []
        for data in response.get("data", []):
            actions = {a["action_type"]: int(a["value"]) for a in data.get("actions", [])}
            spend = float(data.get("spend", 0))
            clicks = int(data.get("clicks", 0))
            leads = actions.get("lead", 0)

            results.append({
                "device": data.get("device_platform"),
                "spend": f"${spend:.2f}",
                "spend_raw": spend,
                "impressions": int(data.get("impressions", 0)),
                "clicks": clicks,
                "reach": int(data.get("reach", 0)),
                "leads": leads,
                "cpc": f"${spend / clicks:.2f}" if clicks > 0 else "N/A",
            })

        return results

    # ============ COMPREHENSIVE REPORTS ============

    def get_full_ads_report(self, days: int = 30) -> Dict:
        """Generate comprehensive Facebook Ads report"""
        return {
            "period_days": days,
            "generated_at": datetime.now().isoformat(),
            "account": self.get_account_info(),
            "summary": self.get_account_insights(days=days),
            "campaigns": self.get_campaign_insights(days=days),
            "adsets": self.get_adset_insights(days=days),
            "ads": self.get_ad_insights(days=days),
            "daily_trend": self.get_daily_spend(days=days),
            "demographics": {
                "age_gender": self.get_age_gender_breakdown(days=days),
                "device": self.get_device_breakdown(days=days),
                "placement": self.get_placement_breakdown(days=days),
            },
        }

    def get_quick_stats(self, days: int = 7) -> Dict:
        """Quick stats for daily check-in"""
        insights = self.get_account_insights(days=days)
        daily = self.get_daily_spend(days=days)

        # Calculate today vs yesterday
        today_spend = daily[-1]["spend_raw"] if daily else 0
        yesterday_spend = daily[-2]["spend_raw"] if len(daily) > 1 else 0
        spend_change = ((today_spend - yesterday_spend) / yesterday_spend * 100) if yesterday_spend > 0 else 0

        return {
            "period": f"Last {days} days",
            "total_spend": insights.get("spend", "$0"),
            "impressions": insights.get("impressions", 0),
            "clicks": insights.get("clicks", 0),
            "cpm": insights.get("cpm", "$0"),
            "cpc": insights.get("cpc", "$0"),
            "ctr": insights.get("ctr", "0%"),
            "leads": insights.get("actions", {}).get("leads", 0),
            "cost_per_lead": insights.get("cost_per_action", {}).get("cost_per_lead", "N/A"),
            "today_vs_yesterday": {
                "today_spend": f"${today_spend:.2f}",
                "yesterday_spend": f"${yesterday_spend:.2f}",
                "change": f"{spend_change:+.1f}%",
            },
        }

    def generate_report_text(self, days: int = 7) -> str:
        """Generate formatted text report"""
        stats = self.get_quick_stats(days)
        campaigns = self.get_campaign_insights(days=days)

        report = f"""
================================================================================
                    FACEBOOK ADS REPORT - Last {days} Days
                    Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
================================================================================

ACCOUNT SUMMARY
---------------
  Total Spend:      {stats['total_spend']}
  Impressions:      {stats['impressions']:,}
  Clicks:           {stats['clicks']:,}
  CTR:              {stats['ctr']}
  CPM:              {stats['cpm']}
  CPC:              {stats['cpc']}
  Leads:            {stats['leads']}
  Cost/Lead:        {stats['cost_per_lead']}

TODAY VS YESTERDAY
------------------
  Today:            {stats['today_vs_yesterday']['today_spend']}
  Yesterday:        {stats['today_vs_yesterday']['yesterday_spend']}
  Change:           {stats['today_vs_yesterday']['change']}

CAMPAIGNS
---------"""

        for c in campaigns[:10]:
            report += f"""
  {c['campaign_name'][:40]:<40}
    Spend: {c['spend']:>10} | Clicks: {c['clicks']:>6} | CTR: {c['ctr']:>6} | Leads: {c['leads']:>4} | CPL: {c['cost_per_lead']:>8}"""

        report += """

================================================================================
"""
        return report


def test_connection():
    """Test Facebook Ads API connection"""
    try:
        fb = FacebookAds()
        account = fb.get_account_info()
        print(f"Connected to: {account.get('name')}")
        print(f"Account ID: {account.get('account_id')}")
        print(f"Currency: {account.get('currency')}")
        return True
    except Exception as e:
        print(f"Connection failed: {e}")
        return False


if __name__ == "__main__":
    test_connection()
