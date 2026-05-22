"""Meta Ad Library puller via RapidAPI (facebook-scraper-api4).

Pulls competitor ad creative for swipe-file research. Different endpoint than
meta.py (which pulls own-account ads via Meta Marketing API).

Usage:
    python scripts/ads/meta_ad_library.py --page-id 345914995276546 --brand IM8 --out clients/earnyz/raw-ads/
    python scripts/ads/meta_ad_library.py --brands-file brands.tsv --out-dir clients/earnyz/raw-ads/

brands.tsv format (tab-separated):
    IM8	345914995276546
    KiwiCo	123456789012345
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
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
    print("ERROR: RAPIDAPI_KEY required in .env.local", flush=True)
    sys.exit(1)


def fetch_page(ad_page_id: str, country: str = "ALL", active_only: bool = True, max_pages: int = 5):
    all_ads = []
    cursor = ""
    pages = 0
    while pages < max_pages:
        body = {
            "query": "",
            "ad_page_id": ad_page_id,
            "country": country,
            "activeStatus": "ACTIVE" if active_only else "ALL",
            "end_cursor": cursor,
            "after_time": "",
            "before_time": "",
            "sort_data": "",
        }
        req = urllib.request.Request(
            f"https://{HOST}/fetch_search_ads_pages",
            data=json.dumps(body).encode(),
            headers={
                "Content-Type": "application/json",
                "x-rapidapi-host": HOST,
                "x-rapidapi-key": KEY,
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            payload = json.loads(resp.read().decode())
        data = payload.get("data", {})
        ads = data.get("ads", [])
        # Flatten — each entry is a list with one ad in it
        for group in ads:
            if isinstance(group, list):
                all_ads.extend(group)
            else:
                all_ads.append(group)
        info = data.get("page_info", {})
        cursor = info.get("end_cursor", "")
        if not info.get("has_next_page") or not cursor:
            break
        pages += 1
        time.sleep(0.5)
    return all_ads


def flatten(ad: dict) -> dict:
    """Reduce an ad to the fields we care about for swipe-file research."""
    snap = ad.get("snapshot", {}) or {}
    cards = snap.get("cards") or []
    first_card = cards[0] if cards else {}
    body = (snap.get("body") or {}).get("text") if isinstance(snap.get("body"), dict) else snap.get("body")
    return {
        "ad_archive_id": ad.get("ad_archive_id"),
        "page_id": snap.get("page_id"),
        "page_name": snap.get("page_name"),
        "page_profile_uri": snap.get("page_profile_uri"),
        "start_date": ad.get("start_date"),
        "end_date": ad.get("end_date"),
        "publisher_platforms": ad.get("publisher_platform"),
        "is_active": ad.get("is_active"),
        "creative_body": body or first_card.get("body"),
        "card_title": first_card.get("title"),
        "card_caption": first_card.get("caption"),
        "card_cta_text": first_card.get("cta_text") or snap.get("cta_text"),
        "card_link_url": first_card.get("link_url"),
        "card_link_description": first_card.get("link_description"),
        "card_image_url": first_card.get("original_image_url") or first_card.get("resized_image_url"),
        "card_video_hd_url": first_card.get("video_hd_url"),
        "card_video_sd_url": first_card.get("video_sd_url"),
        "card_video_preview": first_card.get("video_preview_image_url"),
        "num_cards": len(cards),
        "all_cards_summary": [
            {"title": c.get("title"), "cta": c.get("cta_text"), "body": (c.get("body") or "")[:200]}
            for c in cards
        ],
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--page-id", help="Single Facebook page ID")
    ap.add_argument("--brand", help="Brand name (for filename)")
    ap.add_argument("--brands-file", help="TSV: brand<TAB>page_id per line")
    ap.add_argument("--out-dir", required=True, help="Output directory")
    ap.add_argument("--country", default="ALL")
    ap.add_argument("--all-status", action="store_true")
    ap.add_argument("--max-pages", type=int, default=5)
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if args.page_id and args.brand:
        targets = [(args.brand, args.page_id)]
    elif args.brands_file:
        targets = []
        for line in Path(args.brands_file).read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) >= 2:
                targets.append((parts[0].strip(), parts[1].strip()))
    else:
        print("Usage: --page-id X --brand Y --out-dir d/  OR  --brands-file f.tsv --out-dir d/")
        sys.exit(2)

    summary = []
    for brand, page_id in targets:
        try:
            ads = fetch_page(page_id, country=args.country, active_only=not args.all_status, max_pages=args.max_pages)
            flat = [flatten(a) for a in ads]
        except Exception as e:
            print(f"  ERR {brand}: {e}", flush=True)
            ads, flat = [], []
        slug = brand.lower().replace(" ", "-").replace("/", "-")
        raw_path = out_dir / f"{slug}.raw.json"
        flat_path = out_dir / f"{slug}.json"
        raw_path.write_text(json.dumps(ads, indent=2, default=str))
        flat_path.write_text(json.dumps(flat, indent=2, default=str))
        # ASCII-only output for Windows console
        print(f"  {brand}: {len(ads)} ads -> {flat_path}", flush=True)
        summary.append({"brand": brand, "page_id": page_id, "ad_count": len(ads), "file": str(flat_path)})
        time.sleep(1)

    summary_path = out_dir / "_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"\nSummary -> {summary_path}", flush=True)


if __name__ == "__main__":
    main()
