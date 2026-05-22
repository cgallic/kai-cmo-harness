"""Discover Facebook page IDs for brands by keyword-searching the Ad Library.

Searches for brand-specific terms, extracts page_ids from results, ranks by
frequency. Helps when the public FB page ID doesn't match the ad-running entity.

Usage:
    python scripts/ads/meta_ad_library_discover.py --queries-file queries.tsv --out-dir d/

queries.tsv format (tab-separated, multiple queries per brand):
    KiwiCo	KiwiCo Crate
    KiwiCo	KiwiCo Tinker
    KiwiCo	KiwiCo subscription
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for envfile in (".env.local", ".env"):
    p = REPO_ROOT / envfile
    if p.exists():
        for line in p.read_text().splitlines():
            if line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

KEY = os.environ.get("RAPIDAPI_KEY")
HOST = os.environ.get("RAPIDAPI_FB_HOST", "facebook-scraper-api4.p.rapidapi.com")
if not KEY:
    print("ERROR: RAPIDAPI_KEY required", flush=True)
    sys.exit(1)


def search_keyword(query: str, country: str = "US"):
    url = (
        f"https://{HOST}/fetch_search_ads_pages"
        f"?query={urllib.parse.quote(query)}&country={country}&activeStatus=ACTIVE"
    )
    req = urllib.request.Request(
        url,
        headers={
            "x-rapidapi-host": HOST,
            "x-rapidapi-key": KEY,
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
    except Exception as e:
        print(f"    ERR ({query}): {e}", flush=True)
        return []
    ads = payload.get("data", {}).get("ads", [])
    flat = []
    for group in ads:
        items = group if isinstance(group, list) else [group]
        for ad in items:
            snap = ad.get("snapshot", {}) or {}
            flat.append({
                "page_id": snap.get("page_id"),
                "page_name": snap.get("page_name"),
            })
    return flat


def discover(brand_queries: dict[str, list[str]]):
    results = {}
    for brand, queries in brand_queries.items():
        ranks = Counter()
        names = defaultdict(set)
        for q in queries:
            hits = search_keyword(q)
            for h in hits:
                if h["page_id"]:
                    ranks[h["page_id"]] += 1
                    if h["page_name"]:
                        names[h["page_id"]].add(h["page_name"])
            time.sleep(0.5)
        ranked = sorted(ranks.items(), key=lambda x: -x[1])
        results[brand] = [
            {"page_id": pid, "name": sorted(names[pid])[:3], "hits": count}
            for pid, count in ranked
        ]
        print(f"  {brand}: top candidates -> " + ", ".join(
            f"{pid}({count}, {sorted(names[pid])[:1]})" for pid, count in ranked[:3]
        ) or "  (no hits)", flush=True)
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--queries-file", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    brand_queries = defaultdict(list)
    for line in Path(args.queries_file).read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) >= 2:
            brand_queries[parts[0].strip()].append(parts[1].strip())

    results = discover(brand_queries)
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / "_discovered_page_ids.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved -> {out_path}", flush=True)


if __name__ == "__main__":
    main()
