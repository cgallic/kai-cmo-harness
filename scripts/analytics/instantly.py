"""
Instantly.ai Analytics - Campaign management and cold email metrics.

Uses Instantly API V2 with Bearer token auth.

Usage:
    from scripts.analytics.instantly import InstantlyAnalytics

    instantly = InstantlyAnalytics()
    campaigns = instantly.get_campaigns()
    stats = instantly.get_campaign_stats(campaign_id)
"""

import os
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

# Try to load dotenv
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


BASE_URL = "https://api.instantly.ai/api/v2"


@dataclass
class InstantlyCampaign:
    """Instantly campaign data."""
    id: str
    name: str
    status: str  # v2 returns string status
    created_at: str

    @property
    def status_label(self) -> str:
        """Human-readable status."""
        return self.status or "unknown"


@dataclass
class InstantlyCampaignStats:
    """Campaign analytics summary."""
    campaign_id: str
    campaign_name: str
    emails_sent: int
    emails_opened: int
    emails_replied: int
    emails_bounced: int
    new_leads: int

    @property
    def open_rate(self) -> float:
        if self.emails_sent == 0:
            return 0.0
        return round(self.emails_opened / self.emails_sent * 100, 1)

    @property
    def reply_rate(self) -> float:
        if self.emails_sent == 0:
            return 0.0
        return round(self.emails_replied / self.emails_sent * 100, 1)

    @property
    def bounce_rate(self) -> float:
        if self.emails_sent == 0:
            return 0.0
        return round(self.emails_bounced / self.emails_sent * 100, 1)


class InstantlyAnalytics:
    """
    Instantly.ai campaign analytics and management (API V2).

    Requires: INSTANTLY_API_KEY from Instantly dashboard.
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Instantly analytics.

        Args:
            api_key: Instantly API key.
                     Falls back to INSTANTLY_API_KEY env var.
        """
        self.api_key = api_key or os.getenv("INSTANTLY_API_KEY")
        if not self.api_key:
            raise ValueError(
                "Instantly API key required. "
                "Set INSTANTLY_API_KEY environment variable or pass api_key parameter."
            )

    def _request(
        self,
        endpoint: str,
        method: str = "GET",
        params: Optional[Dict] = None,
        body: Optional[Dict] = None
    ) -> Any:
        """Make a request to Instantly API V2 with Bearer auth."""
        url = f"{BASE_URL}{endpoint}"

        if params:
            query = urlencode({k: v for k, v in params.items() if v is not None})
            url = f"{url}?{query}"

        if body:
            data = json.dumps(body).encode("utf-8")
            request = Request(url, data=data, method=method)
        else:
            request = Request(url, method=method)

        request.add_header("Authorization", f"Bearer {self.api_key}")
        request.add_header("Content-Type", "application/json")
        request.add_header("User-Agent", "CMO-Analytics/1.0")

        try:
            with urlopen(request, timeout=30) as response:
                raw = response.read().decode("utf-8")
                return json.loads(raw) if raw else {}
        except HTTPError as e:
            error_body = e.read().decode("utf-8") if e.fp else ""
            try:
                error_data = json.loads(error_body)
                error_msg = error_data.get("message", error_body)
            except json.JSONDecodeError:
                error_msg = error_body
            raise Exception(f"Instantly API error {e.code}: {error_msg}")
        except URLError as e:
            raise Exception(f"Network error: {e.reason}")

    def get_campaigns(self) -> List[InstantlyCampaign]:
        """
        List all campaigns.

        Returns:
            List of InstantlyCampaign objects.
        """
        data = self._request("/campaigns", params={"limit": 100})

        items = data.get("items", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = []

        campaigns = []
        for c in items:
            campaigns.append(InstantlyCampaign(
                id=c.get("id", ""),
                name=c.get("name", "Unnamed"),
                status=str(c.get("status", "unknown")),
                created_at=c.get("timestamp_created", c.get("created_at", "")),
            ))

        return campaigns

    def get_campaign_stats(self, campaign_id: str) -> InstantlyCampaignStats:
        """
        Get analytics for a specific campaign.

        Args:
            campaign_id: Campaign UUID.

        Returns:
            InstantlyCampaignStats with open/reply/bounce metrics.
        """
        data = self._request("/campaigns/analytics", params={
            "campaign_id": campaign_id,
        })

        # V2 returns a list even for single campaign
        if isinstance(data, list) and data:
            stats = data[0]
        else:
            stats = data

        return InstantlyCampaignStats(
            campaign_id=campaign_id,
            campaign_name=stats.get("campaign_name", campaign_id),
            emails_sent=stats.get("emails_sent_count", 0),
            emails_opened=stats.get("open_count_unique", 0),
            emails_replied=stats.get("reply_count_unique", 0),
            emails_bounced=stats.get("bounced_count", 0),
            new_leads=stats.get("new_leads_contacted_count", stats.get("leads_count", 0)),
        )

    def get_all_campaign_stats(self) -> Dict[str, Any]:
        """
        Get stats for ALL campaigns (single API call).

        Returns:
            Dict with per-campaign stats and totals.
        """
        # Fetch all campaign analytics in one call (no campaign_id filter)
        data = self._request("/campaigns/analytics")
        items = data if isinstance(data, list) else []

        # Also get overview totals
        overview = self._request("/campaigns/analytics/overview")

        all_stats = []
        for s in items:
            sent = s.get("emails_sent_count", 0)
            opened = s.get("open_count_unique", 0)
            replied = s.get("reply_count_unique", 0)
            bounced = s.get("bounced_count", 0)
            all_stats.append({
                "campaign_id": s.get("campaign_id", ""),
                "name": s.get("campaign_name", ""),
                "status": {0: "draft", 1: "active", 2: "paused", 3: "completed"}.get(
                    s.get("campaign_status"), "unknown"
                ),
                "sent": sent,
                "contacted": s.get("contacted_count", 0),
                "opened": opened,
                "replied": replied,
                "bounced": bounced,
                "leads": s.get("leads_count", 0),
                "open_rate": round(opened / sent * 100, 1) if sent > 0 else 0,
                "reply_rate": round(replied / sent * 100, 1) if sent > 0 else 0,
                "bounce_rate": round(bounced / sent * 100, 1) if sent > 0 else 0,
            })

        total_sent = overview.get("emails_sent_count", 0)
        total_opened = overview.get("open_count_unique", 0)
        total_replied = overview.get("reply_count_unique", 0)
        total_bounced = overview.get("bounced_count", 0)

        return {
            "campaigns": all_stats,
            "totals": {
                "sent": total_sent,
                "contacted": overview.get("contacted_count", 0),
                "opened": total_opened,
                "replied": total_replied,
                "bounced": total_bounced,
                "open_rate": round(total_opened / total_sent * 100, 1) if total_sent > 0 else 0,
                "reply_rate": round(total_replied / total_sent * 100, 1) if total_sent > 0 else 0,
                "bounce_rate": round(total_bounced / total_sent * 100, 1) if total_sent > 0 else 0,
                "opportunities": overview.get("total_opportunities", 0),
                "meetings_booked": overview.get("total_meeting_booked", 0),
            },
            "campaign_count": len(all_stats),
        }

    def get_accounts(self) -> List[Dict[str, Any]]:
        """
        List sending accounts with warmup status.

        Returns:
            List of account dicts.
        """
        data = self._request("/accounts", params={"limit": 100})
        items = data.get("items", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = []

        return [
            {
                "email": a.get("email", ""),
                "status": a.get("status", "unknown"),
                "warmup_enabled": a.get("warmup_enabled", False),
                "warmup_status": a.get("warmup", {}).get("status", "") if isinstance(a.get("warmup"), dict) else str(a.get("warmup_status", "")),
                "daily_limit": a.get("daily_limit", 0),
            }
            for a in items
        ]

    def get_leads(self, campaign_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List leads in a campaign.

        Args:
            campaign_id: Campaign UUID.
            limit: Max leads to return.

        Returns:
            List of lead dicts.
        """
        data = self._request("/leads/list", method="POST", body={
            "campaign_id": campaign_id,
            "limit": limit,
        })
        items = data.get("items", data) if isinstance(data, dict) else data
        if not isinstance(items, list):
            items = []

        lead_status_map = {0: "new", 1: "interested", 2: "meeting_booked",
                           3: "contacted", 4: "bounced", 5: "unsubscribed",
                           6: "not_interested", 7: "wrong_person"}

        return [
            {
                "email": lead.get("email", lead.get("lead_email", "")),
                "first_name": lead.get("first_name", ""),
                "last_name": lead.get("last_name", ""),
                "company": lead.get("company_name", lead.get("company", "")),
                "status": lead_status_map.get(lead.get("status"), str(lead.get("status", ""))),
            }
            for lead in items
        ]

    def launch_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Launch a campaign.

        Args:
            campaign_id: Campaign UUID.

        Returns:
            API response dict.
        """
        return self._request(f"/campaigns/{campaign_id}/launch", method="POST")

    def pause_campaign(self, campaign_id: str) -> Dict[str, Any]:
        """
        Pause a campaign.

        Args:
            campaign_id: Campaign UUID.

        Returns:
            API response dict.
        """
        return self._request(f"/campaigns/{campaign_id}/pause", method="POST")

    def update_campaign(self, campaign_id: str, **kwargs) -> Dict[str, Any]:
        """
        Update campaign settings.

        Args:
            campaign_id: Campaign UUID.
            **kwargs: Fields to update (name, daily_limit, etc.)

        Returns:
            API response dict.
        """
        return self._request(f"/campaigns/{campaign_id}", method="PATCH", body=kwargs)


# CLI for testing
def main():
    """Test Instantly analytics."""
    import argparse

    parser = argparse.ArgumentParser(description="Instantly Analytics CLI")
    parser.add_argument("command", choices=["campaigns", "stats", "accounts", "leads"])
    parser.add_argument("--id", help="Campaign ID")
    parser.add_argument("--all", action="store_true", help="All campaigns")
    args = parser.parse_args()

    try:
        instantly = InstantlyAnalytics()
    except ValueError as e:
        print(f"Error: {e}")
        return 1

    if args.command == "campaigns":
        campaigns = instantly.get_campaigns()
        for c in campaigns:
            print(f"  [{c.status_label}] {c.name} ({c.id})")

    elif args.command == "stats":
        if args.all:
            data = instantly.get_all_campaign_stats()
            print(json.dumps(data, indent=2, default=str))
        elif args.id:
            stats = instantly.get_campaign_stats(args.id)
            print(f"  Sent: {stats.emails_sent}, Opened: {stats.emails_opened} ({stats.open_rate}%)")
            print(f"  Replied: {stats.emails_replied} ({stats.reply_rate}%), Bounced: {stats.emails_bounced} ({stats.bounce_rate}%)")
        else:
            print("Error: --id=CAMPAIGN_ID or --all required")

    elif args.command == "accounts":
        accounts = instantly.get_accounts()
        for a in accounts:
            print(f"  {a['email']}: warmup={a['warmup_enabled']} (limit: {a['daily_limit']})")

    elif args.command == "leads":
        if not args.id:
            print("Error: --id=CAMPAIGN_ID required")
            return 1
        leads = instantly.get_leads(args.id)
        for lead in leads[:20]:
            print(f"  {lead['email']} - {lead['first_name']} {lead['last_name']} ({lead['status']})")

    return 0


if __name__ == "__main__":
    exit(main())
