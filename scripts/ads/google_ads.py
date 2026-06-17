#!/usr/bin/env python3
"""
Kai CMO Harness — Google Ads Integration
==========================================
Read campaign performance, keyword data, and search terms from Google Ads API.

Usage:
  python scripts/ads/google_ads.py campaigns                  # Campaign performance
  python scripts/ads/google_ads.py keywords --campaign 123     # Keyword performance
  python scripts/ads/google_ads.py search-terms --campaign 123 # Search terms report
  python scripts/ads/google_ads.py create-rsa --campaign 123 --keyword "ai crm" # Create RSA
  python scripts/ads/google_ads.py summary                     # Account summary

Environment:
  GOOGLE_ADS_DEVELOPER_TOKEN=your-dev-token
  GOOGLE_ADS_CLIENT_ID=your-client-id
  GOOGLE_ADS_CLIENT_SECRET=your-client-secret
  GOOGLE_ADS_REFRESH_TOKEN=your-refresh-token
  GOOGLE_ADS_CUSTOMER_ID=123-456-7890

Setup: https://developers.google.com/google-ads/api/docs/get-started/introduction
"""

import argparse
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def _get_client():
    """Initialize Google Ads API client."""
    try:
        from google.ads.googleads.client import GoogleAdsClient
    except ImportError:
        print("Install: pip install google-ads")
        sys.exit(1)

    credentials = {
        "developer_token": os.environ.get("GOOGLE_ADS_DEVELOPER_TOKEN", ""),
        "client_id": os.environ.get("GOOGLE_ADS_CLIENT_ID", ""),
        "client_secret": os.environ.get("GOOGLE_ADS_CLIENT_SECRET", ""),
        "refresh_token": os.environ.get("GOOGLE_ADS_REFRESH_TOKEN", ""),
        "use_proto_plus": True,
    }

    missing = [k for k, v in credentials.items() if not v and k != "use_proto_plus"]
    if missing:
        print(f"Missing env vars: {', '.join('GOOGLE_ADS_' + k.upper() for k in missing)}")
        sys.exit(1)

    return GoogleAdsClient.load_from_dict(credentials)


def _get_customer_id() -> str:
    cid = os.environ.get("GOOGLE_ADS_CUSTOMER_ID", "").replace("-", "")
    if not cid:
        print("Missing GOOGLE_ADS_CUSTOMER_ID")
        sys.exit(1)
    return cid


def get_campaigns(days: int = 30) -> list[dict]:
    """Get campaign performance data."""
    client = _get_client()
    customer_id = _get_customer_id()
    ga_service = client.get_service("GoogleAdsService")

    query = f"""
        SELECT
            campaign.id,
            campaign.name,
            campaign.status,
            campaign.advertising_channel_type,
            campaign_budget.amount_micros,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.conversions_value,
            metrics.average_cpc,
            metrics.ctr
        FROM campaign
        WHERE segments.date DURING LAST_{days}_DAYS
            AND campaign.status != 'REMOVED'
        ORDER BY metrics.cost_micros DESC
    """

    results = []
    response = ga_service.search(customer_id=customer_id, query=query)
    for row in response:
        cost = row.metrics.cost_micros / 1_000_000
        conversions = row.metrics.conversions
        roas = (row.metrics.conversions_value / cost) if cost > 0 else 0
        cpl = (cost / conversions) if conversions > 0 else 0

        results.append({
            "id": row.campaign.id,
            "name": row.campaign.name,
            "status": row.campaign.status.name,
            "type": row.campaign.advertising_channel_type.name,
            "budget_daily": row.campaign_budget.amount_micros / 1_000_000,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": round(cost, 2),
            "conversions": round(conversions, 1),
            "roas": round(roas, 2),
            "cpl": round(cpl, 2),
            "avg_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
            "ctr": round(row.metrics.ctr * 100, 2),
        })

    return results


def get_keywords(campaign_id: str | None = None, days: int = 30) -> list[dict]:
    """Get keyword performance data."""
    client = _get_client()
    customer_id = _get_customer_id()
    ga_service = client.get_service("GoogleAdsService")

    campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

    query = f"""
        SELECT
            ad_group.name,
            ad_group_criterion.keyword.text,
            ad_group_criterion.keyword.match_type,
            ad_group_criterion.quality_info.quality_score,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.average_cpc,
            metrics.ctr
        FROM keyword_view
        WHERE segments.date DURING LAST_{days}_DAYS
            {campaign_filter}
        ORDER BY metrics.impressions DESC
        LIMIT 100
    """

    results = []
    response = ga_service.search(customer_id=customer_id, query=query)
    for row in response:
        results.append({
            "ad_group": row.ad_group.name,
            "keyword": row.ad_group_criterion.keyword.text,
            "match_type": row.ad_group_criterion.keyword.match_type.name,
            "quality_score": row.ad_group_criterion.quality_info.quality_score,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": round(row.metrics.cost_micros / 1_000_000, 2),
            "conversions": round(row.metrics.conversions, 1),
            "avg_cpc": round(row.metrics.average_cpc / 1_000_000, 2),
            "ctr": round(row.metrics.ctr * 100, 2),
        })

    return results


def get_search_terms(campaign_id: str | None = None, days: int = 30) -> list[dict]:
    """Get search terms report — find new opportunities and negatives."""
    client = _get_client()
    customer_id = _get_customer_id()
    ga_service = client.get_service("GoogleAdsService")

    campaign_filter = f"AND campaign.id = {campaign_id}" if campaign_id else ""

    query = f"""
        SELECT
            search_term_view.search_term,
            search_term_view.status,
            campaign.name,
            metrics.impressions,
            metrics.clicks,
            metrics.cost_micros,
            metrics.conversions,
            metrics.ctr
        FROM search_term_view
        WHERE segments.date DURING LAST_{days}_DAYS
            {campaign_filter}
        ORDER BY metrics.impressions DESC
        LIMIT 200
    """

    results = []
    response = ga_service.search(customer_id=customer_id, query=query)
    for row in response:
        cost = row.metrics.cost_micros / 1_000_000
        results.append({
            "search_term": row.search_term_view.search_term,
            "status": row.search_term_view.status.name,
            "campaign": row.campaign.name,
            "impressions": row.metrics.impressions,
            "clicks": row.metrics.clicks,
            "cost": round(cost, 2),
            "conversions": round(row.metrics.conversions, 1),
            "ctr": round(row.metrics.ctr * 100, 2),
        })

    return results


def create_rsa(campaign_id: str, ad_group_id: str, headlines: list[str],
               descriptions: list[str], final_url: str) -> dict:
    """Create a Responsive Search Ad."""
    client = _get_client()
    customer_id = _get_customer_id()

    ad_group_ad_service = client.get_service("AdGroupAdService")
    ad_group_ad_operation = client.get_type("AdGroupAdOperation")

    ad_group_ad = ad_group_ad_operation.create
    ad_group_ad.ad_group = client.get_service("AdGroupService").ad_group_path(customer_id, ad_group_id)
    ad_group_ad.status = client.enums.AdGroupAdStatusEnum.PAUSED

    ad = ad_group_ad.ad
    ad.final_urls.append(final_url)

    for i, headline in enumerate(headlines[:15]):
        headline_asset = client.get_type("AdTextAsset")
        headline_asset.text = headline[:30]  # Enforce 30 char limit
        ad.responsive_search_ad.headlines.append(headline_asset)

    for desc in descriptions[:4]:
        desc_asset = client.get_type("AdTextAsset")
        desc_asset.text = desc[:90]  # Enforce 90 char limit
        ad.responsive_search_ad.descriptions.append(desc_asset)

    try:
        response = ad_group_ad_service.mutate_ad_group_ads(
            customer_id=customer_id,
            operations=[ad_group_ad_operation],
        )
        return {
            "success": True,
            "resource_name": response.results[0].resource_name,
            "message": "RSA created (paused). Review and enable in Google Ads.",
        }
    except Exception as e:
        return {"success": False, "message": str(e)}


def account_summary(days: int = 30) -> dict:
    """Get account-level summary."""
    campaigns = get_campaigns(days)
    total_spend = sum(c["cost"] for c in campaigns)
    total_conversions = sum(c["conversions"] for c in campaigns)
    total_clicks = sum(c["clicks"] for c in campaigns)
    active = [c for c in campaigns if c["status"] == "ENABLED"]

    return {
        "active_campaigns": len(active),
        "total_campaigns": len(campaigns),
        "total_spend": round(total_spend, 2),
        "total_conversions": round(total_conversions, 1),
        "total_clicks": total_clicks,
        "avg_cpl": round(total_spend / max(total_conversions, 1), 2),
        "avg_roas": round(sum(c["roas"] for c in active) / max(len(active), 1), 2),
        "top_campaigns": sorted(active, key=lambda c: c["conversions"], reverse=True)[:5],
    }


def main():
    parser = argparse.ArgumentParser(description="Google Ads integration")
    sub = parser.add_subparsers(dest="command", required=True)

    # campaigns
    c = sub.add_parser("campaigns", help="Campaign performance")
    c.add_argument("--days", type=int, default=30)
    c.add_argument("--json", action="store_true")

    # keywords
    k = sub.add_parser("keywords", help="Keyword performance")
    k.add_argument("--campaign", help="Campaign ID filter")
    k.add_argument("--days", type=int, default=30)
    k.add_argument("--json", action="store_true")

    # search-terms
    s = sub.add_parser("search-terms", help="Search terms report")
    s.add_argument("--campaign", help="Campaign ID filter")
    s.add_argument("--days", type=int, default=30)
    s.add_argument("--json", action="store_true")

    # summary
    su = sub.add_parser("summary", help="Account summary")
    su.add_argument("--days", type=int, default=30)
    su.add_argument("--json", action="store_true")

    args = parser.parse_args()

    if args.command == "campaigns":
        data = get_campaigns(args.days)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(f"\n{'Campaign':<30} {'Status':<10} {'Spend':>10} {'Conv':>7} {'ROAS':>7} {'CPC':>7} {'CTR':>6}")
            print("─" * 85)
            for c in data:
                print(f"{c['name'][:30]:<30} {c['status']:<10} ${c['cost']:>9,.2f} {c['conversions']:>7.1f} {c['roas']:>7.2f} ${c['avg_cpc']:>6.2f} {c['ctr']:>5.1f}%")

    elif args.command == "keywords":
        data = get_keywords(args.campaign, args.days)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(f"\n{'Keyword':<35} {'Match':<10} {'QS':>3} {'Clicks':>7} {'Cost':>9} {'Conv':>6} {'CTR':>6}")
            print("─" * 85)
            for k in data:
                print(f"{k['keyword'][:35]:<35} {k['match_type']:<10} {k['quality_score']:>3} {k['clicks']:>7} ${k['cost']:>8.2f} {k['conversions']:>6.1f} {k['ctr']:>5.1f}%")

    elif args.command == "search-terms":
        data = get_search_terms(args.campaign, args.days)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(f"\n{'Search Term':<40} {'Clicks':>7} {'Cost':>9} {'Conv':>6} {'CTR':>6}")
            print("─" * 75)
            for s in data:
                print(f"{s['search_term'][:40]:<40} {s['clicks']:>7} ${s['cost']:>8.2f} {s['conversions']:>6.1f} {s['ctr']:>5.1f}%")

    elif args.command == "summary":
        data = account_summary(args.days)
        if args.json:
            print(json.dumps(data, indent=2))
        else:
            print(f"\n  Google Ads — {args.days}-Day Summary")
            print(f"  {'─'*40}")
            print(f"  Active campaigns:  {data['active_campaigns']}")
            print(f"  Total spend:       ${data['total_spend']:,.2f}")
            print(f"  Total conversions: {data['total_conversions']:.1f}")
            print(f"  Total clicks:      {data['total_clicks']:,}")
            print(f"  Avg CPL:           ${data['avg_cpl']:.2f}")
            print(f"  Avg ROAS:          {data['avg_roas']:.2f}x")


if __name__ == "__main__":
    main()
