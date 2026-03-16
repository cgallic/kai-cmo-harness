"""
DataForSEO module — competitor SERP + keyword research
Usage:
  cmo dataforseo serp --keyword="AI call answering" [--depth=10]
  cmo dataforseo domain --domain=claireai.com [--limit=20]
  cmo dataforseo keywords --seed="law firm answering service" [--limit=20]
  cmo dataforseo competitors --site=kaicalls [--limit=5]
"""

import argparse
import json
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv("/opt/cmo-analytics/.env")

LOGIN = os.getenv("DATAFORSEO_LOGIN", "connor@kaicalls.com")
PASSWORD = os.getenv("DATAFORSEO_PASSWORD", "")
BASE_URL = "https://api.dataforseo.com/v3"

COMPETITOR_MAP = {
    "kaicalls": ["claireai.com", "smith.ai", "callpod.io", "ruby.com", "answerfirst.com"],
    "abp":      ["partysource.com", "rentmyequipment.com", "liveevents.com"],
    "bwk":      ["buildai.space", "durable.co", "10web.io"],
}

SITE_MAP = {
    "kaicalls":    "kaicalls.com",
    "abp":         "awesomebackyardparties.com",
    "bwk":         "buildwithkai.com",
    "vocalscribe": "vocalscribe.xyz",
    "meetkai":     "meetkai.xyz",
}


def auth():
    return (LOGIN, PASSWORD)


def post(endpoint, payload):
    r = requests.post(f"{BASE_URL}{endpoint}", json=payload, auth=auth(), timeout=30)
    r.raise_for_status()
    return r.json()


def cmd_serp(args):
    """Live SERP results for a keyword."""
    depth = int(args.depth) if hasattr(args, "depth") and args.depth else 10
    data = post("/serp/google/organic/live/advanced", [{
        "keyword": args.keyword,
        "location_code": 2840,
        "language_code": "en",
        "device": "desktop",
        "depth": depth,
    }])
    results = data["tasks"][0]["result"][0]["items"]
    cost = data["cost"]
    print(f"Keyword: {args.keyword}  |  Cost: ${cost:.4f}\n")
    print(f"{'#':<4} {'Domain':<30} {'Title':<55} {'URL'}")
    print("-" * 120)
    rank = 1
    for item in results:
        if item.get("type") != "organic":
            continue
        domain = item.get("domain", "")
        title = (item.get("title") or "")[:53]
        url = item.get("url", "")[:60]
        print(f"{rank:<4} {domain:<30} {title:<55} {url}")
        rank += 1


def cmd_domain(args):
    """Domain overview — ranked keywords + visibility."""
    limit = int(args.limit) if hasattr(args, "limit") and args.limit else 20
    data = post("/dataforseo_labs/google/domain_rank_overview/live", [{
        "target": args.domain,
        "location_code": 2840,
        "language_code": "en",
    }])
    result = data["tasks"][0]["result"][0]["items"][0]
    metrics = result.get("metrics", {}).get("organic", {})
    cost = data["cost"]
    print(f"Domain: {args.domain}  |  Cost: ${cost:.4f}\n")
    print(f"  ETV (est. traffic/mo):  {metrics.get('etv', 0):,.0f}")
    print(f"  Keywords ranked:        {metrics.get('count', 0):,}")
    print(f"  Avg position:           {metrics.get('pos', 0):.1f}")
    print(f"  SERP features:          {metrics.get('pos_1', 0)} top-1  |  {metrics.get('pos_2_3', 0)} top-3  |  {metrics.get('pos_4_10', 0)} top-10")

    # Top keywords
    kw_data = post("/dataforseo_labs/google/ranked_keywords/live", [{
        "target": args.domain,
        "location_code": 2840,
        "language_code": "en",
        "limit": limit,
        "order_by": ["keyword_data.keyword_info.search_volume,desc"],
    }])
    items = kw_data["tasks"][0]["result"][0].get("items", [])
    if items:
        print(f"\nTop {limit} keywords by search volume:\n")
        print(f"{'Keyword':<45} {'Vol':>8} {'Pos':>5} {'URL'}")
        print("-" * 90)
        for item in items:
            kw = item["keyword_data"]["keyword"][:43]
            vol = item["keyword_data"]["keyword_info"].get("search_volume", 0) or 0
            pos = item["ranked_serp_element"]["serp_item"].get("rank_absolute", 0)
            url = (item["ranked_serp_element"]["serp_item"].get("url") or "")[:35]
            print(f"{kw:<45} {vol:>8,} {pos:>5} {url}")


def cmd_keywords(args):
    """Keyword ideas from a seed term."""
    limit = int(args.limit) if hasattr(args, "limit") and args.limit else 20
    data = post("/dataforseo_labs/google/keyword_suggestions/live", [{
        "keyword": args.seed,
        "location_code": 2840,
        "language_code": "en",
        "limit": limit,
        "order_by": ["keyword_info.search_volume,desc"],
        "filters": ["keyword_info.search_volume", ">", 50],
    }])
    items = data["tasks"][0]["result"][0].get("items") or []
    cost = data["cost"]
    print(f"Seed: {args.seed}  |  Cost: ${cost:.4f}\n")
    if not items:
        print("No keyword suggestions found. Try a broader seed term.")
        return
    print(f"{'Keyword':<50} {'Vol':>8} {'CPC':>7} {'Diff':>5}")
    print("-" * 75)
    for item in items:
        kw = item["keyword"][:48]
        info = item.get("keyword_info", {})
        vol = info.get("search_volume", 0) or 0
        cpc = info.get("cpc", 0) or 0
        diff = item.get("keyword_properties", {}).get("keyword_difficulty", 0) or 0
        print(f"{kw:<50} {vol:>8,} ${cpc:>6.2f} {diff:>5}")


def cmd_competitors(args):
    """SERP snapshot for competitor domains."""
    site_key = args.site if hasattr(args, "site") and args.site else "kaicalls"
    domains = COMPETITOR_MAP.get(site_key, [])
    limit = int(args.limit) if hasattr(args, "limit") and args.limit else 5
    domains = domains[:limit]
    if not domains:
        print(f"No competitors configured for site: {site_key}")
        return

    print(f"Competitor domain overview for: {site_key}\n")
    total_cost = 0.0
    for domain in domains:
        try:
            data = post("/dataforseo_labs/google/domain_rank_overview/live", [{
                "target": domain,
                "location_code": 2840,
                "language_code": "en",
            }])
            items = data["tasks"][0]["result"][0].get("items") or []
            if not items:
                print(f"  {domain:<35} No data in DataForSEO index")
                continue
            result = items[0]
            metrics = result.get("metrics", {}).get("organic", {})
            total_cost += data["cost"]
            etv = metrics.get("etv", 0) or 0
            count = metrics.get("count", 0) or 0
            top10 = metrics.get("pos_4_10", 0) or 0
            top3 = metrics.get("pos_2_3", 0) or 0
            pos1 = metrics.get("pos_1", 0) or 0
            print(f"  {domain:<35} ETV: {etv:>8,.0f}  KWs: {count:>6,}  Top-1: {pos1:>4}  Top-3: {top3:>4}  Top-10: {top10:>5}")
        except Exception as e:
            print(f"  {domain:<35} ERROR: {e}")
    print(f"\nTotal cost: ${total_cost:.4f}")


def main():
    parser = argparse.ArgumentParser(description="DataForSEO module")
    sub = parser.add_subparsers(dest="command")

    p_serp = sub.add_parser("serp")
    p_serp.add_argument("--keyword", required=True)
    p_serp.add_argument("--depth", default=10)

    p_domain = sub.add_parser("domain")
    p_domain.add_argument("--domain", required=True)
    p_domain.add_argument("--limit", default=20)

    p_kw = sub.add_parser("keywords")
    p_kw.add_argument("--seed", required=True)
    p_kw.add_argument("--limit", default=20)

    p_comp = sub.add_parser("competitors")
    p_comp.add_argument("--site", default="kaicalls")
    p_comp.add_argument("--limit", default=5)

    args = parser.parse_args()

    if args.command == "serp":
        cmd_serp(args)
    elif args.command == "domain":
        cmd_domain(args)
    elif args.command == "keywords":
        cmd_keywords(args)
    elif args.command == "competitors":
        cmd_competitors(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
