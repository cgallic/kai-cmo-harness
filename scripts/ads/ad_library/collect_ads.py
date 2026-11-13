#!/usr/bin/env python3
"""Collect Meta Ad Library ads into normalized JSONL rows.

Sources (pick one):
  --from-apify FILE          JSON/JSONL export of curious_coder/facebook-ads-library-scraper
  --from-scrapecreators FILE JSON/JSONL from ScrapeCreators' Facebook Ad Library endpoint
  --meta-api                 Graph API ads_archive (META_ACCESS_TOKEN). Commercial ads are
                             only returned when delivered to the EU, so --countries defaults
                             to EU countries.
  --apify-run                run the Apify actor (APIFY_TOKEN). Needs --max-usd (per-run ceiling,
                             passed to Apify as maxTotalChargeUsd) and fits under the monthly cap
                             in scripts/ads/ad_library/budget.py (fail-closed).

Every row has: ad_id, page_id, page_name, start_date, end_date (null while active),
is_active, body, title, link_description, cta, link_url, display_format, platforms,
snapshot_url, source, raw.

Read-only: every source is a public ad archive. Nothing touches an ad account.

Usage:
  python -m scripts.ads.ad_library.collect_ads --from-apify export.json --out ads.jsonl
  python -m scripts.ads.ad_library.collect_ads --apify-run --search-terms "baseball training" \
      --countries US --max 500 --max-usd 0.50 --require "baseball|softball" --out ads.jsonl
  python -m scripts.ads.ad_library.collect_ads --meta-api --search-terms "personal finance app" \
      --countries DE,FR,IE,NL --max 50 --out ads.jsonl

The access token never appears in output, logs or error messages (see _redact).
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

GRAPH_VERSION = os.environ.get("META_GRAPH_VERSION", "v21.0")
GRAPH_URL = f"https://graph.facebook.com/{GRAPH_VERSION}/ads_archive"
META_FIELDS = [
    "ad_creation_time", "ad_delivery_start_time", "ad_delivery_stop_time", "ad_creative_bodies",
    "ad_creative_link_titles", "ad_creative_link_descriptions", "ad_creative_link_captions",
    "page_id", "page_name", "publisher_platforms", "ad_snapshot_url",
]
EU_COUNTRIES = ["AT", "BE", "BG", "HR", "CY", "CZ", "DK", "EE", "FI", "FR", "DE", "GR", "HU", "IE",
                "IT", "LV", "LT", "LU", "MT", "NL", "PL", "PT", "RO", "SK", "SI", "ES", "SE"]
APIFY_ACTOR = "curious_coder/facebook-ads-library-scraper"
FORMATS = {"video": "video", "image": "image", "carousel": "carousel", "dco": "dco",
           "dpa": "carousel", "multi_images": "carousel", "multi_videos": "carousel"}


def _redact(text: str, *secrets: str) -> str:
    text = str(text)
    for s in secrets:
        if s:
            text = text.replace(s, "[redacted]")
            text = text.replace(urllib.parse.quote(s, safe=""), "[redacted]")
    return text


def _get(d: dict, *keys, default=None):
    """First present, non-empty value among key variants (dotted paths allowed)."""
    for k in keys:
        cur = d
        for part in k.split("."):
            if isinstance(cur, dict) and part in cur:
                cur = cur[part]
            else:
                cur = None
                break
        if cur not in (None, "", [], {}):
            return cur
    return default


def to_date(v) -> str | None:
    """ISO date from a Unix timestamp (s or ms), ISO string or YYYY-MM-DD. 0/empty -> None."""
    if v in (None, "", 0, "0"):
        return None
    if isinstance(v, (int, float)) or (isinstance(v, str) and v.strip().isdigit()):
        ts = float(v)
        if ts <= 0:
            return None
        if ts > 1e11:  # milliseconds
            ts /= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc).date().isoformat()
    s = str(v).strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S.%f%z", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d",
                "%b %d, %Y", "%d %b %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(s.replace("Z", "+0000"), fmt).date().isoformat()
        except ValueError:
            continue
    return s[:10] if len(s) >= 10 and s[4] == "-" else None


def _text(v) -> str:
    if isinstance(v, dict):
        v = v.get("text") or (v.get("markup") or {}).get("__html") or ""
    if isinstance(v, list):
        v = "\n".join(_text(x) for x in v if x)
    return str(v or "").strip()


def _as_list(v) -> list:
    if v in (None, ""):
        return []
    if isinstance(v, str):
        return [p.strip() for p in v.split(",") if p.strip()]
    return list(v)


_TEMPLATE = re.compile(r"\{\{[^}]*\}\}|\[[A-Za-z]+\d*\]")


def _real(v) -> str:
    """Text with catalog-template placeholders ({{product.name}}, [categoryOne1]) treated as missing."""
    t = _text(v)
    return "" if _TEMPLATE.search(t) else t


def _first_real(*vals) -> str:
    for v in vals:
        t = _real(v)
        if t:
            return t
    return ""


def normalize_library_record(rec: dict, source: str = "apify") -> dict:
    """Apify curious_coder / ScrapeCreators record -> normalized row (tolerant of key variants).

    Catalog (DPA) ads carry an unrendered template ({{product.name}}) in the top-level snapshot;
    the real copy is on the cards, so placeholder text is skipped in favour of the first real value.
    """
    snap = rec.get("snapshot") or {}
    cards = [c for c in (snap.get("cards") or []) if isinstance(c, dict)]
    card0 = cards[0] if cards else {}
    body = _first_real(_get(snap, "body"), *[c.get("body") for c in cards],
                       _get(rec, "body", "ad_copy", "text", "adText", "ad_creative_bodies"))
    fmt = str(_get(snap, "display_format") or _get(rec, "display_format", "displayFormat", "format",
                                                    default="") or "").lower()
    if not fmt:
        fmt = "video" if snap.get("videos") else ("carousel" if len(cards) > 1 else
                                                  ("image" if snap.get("images") else ""))
    start = to_date(_get(rec, "start_date_string", "start_date", "startDate", "start_date_formatted",
                         "ad_delivery_start_time"))
    end = to_date(_get(rec, "end_date_string", "end_date", "endDate", "end_date_formatted",
                       "ad_delivery_stop_time"))
    active = _get(rec, "is_active", "isActive")
    if active is None:
        active = end is None
    active = bool(active)
    if active:
        end = None  # a scraped end_date on an active ad is the scrape day, not a stop
    ad_id = _get(rec, "ad_archive_id", "adArchiveID", "adArchiveId", "ad_id", "id")
    return {
        "ad_id": str(ad_id) if ad_id is not None else None,
        "page_id": str(_get(rec, "page_id", "pageID", "pageId", "snapshot.page_id", default="") or "") or None,
        "page_name": _get(rec, "page_name", "pageName", "advertiser", "advertiser_name", "snapshot.page_name"),
        "start_date": start,
        "end_date": end,
        "is_active": active,
        "body": body,
        "title": _first_real(_get(snap, "title"), *[c.get("title") for c in cards],
                             _get(rec, "title", "ad_creative_link_titles")),
        "link_description": _first_real(_get(snap, "link_description"), *[c.get("link_description") for c in cards],
                                        _get(rec, "link_description", "ad_creative_link_descriptions")),
        "categories": [str(c).upper() for c in _as_list(_get(rec, "categories"))],
        "cta": _text(_get(snap, "cta_text") or _get(card0, "cta_text") or _get(rec, "cta", "call_to_action",
                                                                               "cta_text")) or None,
        "link_url": _get(snap, "link_url") or _get(card0, "link_url") or _get(rec, "link_url", "linkUrl"),
        "display_format": FORMATS.get(fmt, fmt or None),
        "platforms": [str(p).lower() for p in _as_list(_get(rec, "publisher_platform", "publisher_platforms",
                                                             "publisherPlatform", "platforms"))],
        "snapshot_url": _get(rec, "ad_library_url", "url", "snapshot_url", "ad_snapshot_url")
                        or (f"https://www.facebook.com/ads/library/?id={ad_id}" if ad_id else None),
        "source": source,
        "raw": rec,
    }


def normalize_graph_record(rec: dict) -> dict:
    """Graph API ads_archive record -> normalized row. The API has no CTA or format field."""
    stop = to_date(rec.get("ad_delivery_stop_time"))
    first = lambda k: (rec.get(k) or [None])[0]
    return {
        "ad_id": str(rec.get("id")) if rec.get("id") else None,
        "page_id": rec.get("page_id"),
        "page_name": rec.get("page_name"),
        "start_date": to_date(rec.get("ad_delivery_start_time") or rec.get("ad_creation_time")),
        "end_date": stop,
        "is_active": stop is None,
        "body": (first("ad_creative_bodies") or "").strip(),
        "title": (first("ad_creative_link_titles") or "").strip(),
        "link_description": (first("ad_creative_link_descriptions") or "").strip(),
        "cta": None,
        "link_url": first("ad_creative_link_captions"),
        "display_format": None,
        "platforms": [p.lower() for p in rec.get("publisher_platforms") or []],
        # ad_snapshot_url embeds the access token, so it is never stored; link the public library page.
        "snapshot_url": f"https://www.facebook.com/ads/library/?id={rec['id']}" if rec.get("id") else None,
        "source": "meta_api",
        "raw": {k: v for k, v in rec.items() if k != "ad_snapshot_url"},
    }


def load_records(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        txt = f.read().strip()
    if not txt:
        return []
    if txt[0] == "[":
        data = json.loads(txt)
    elif txt[0] == "{" and "\n" not in txt:
        data = json.loads(txt)
    else:
        try:
            data = json.loads(txt)
        except json.JSONDecodeError:
            data = [json.loads(l) for l in txt.splitlines() if l.strip()]
    if isinstance(data, dict):  # {"results": [...]} / {"searchResults": [...]} / {"data": [...]}
        data = _get(data, "results", "searchResults", "ads", "data", "items", default=[data])
    out = []
    for r in data:
        # Some exports group variants: {"collation_id":..., "ads":[...]} / searchResults pages.
        if isinstance(r, dict) and isinstance(r.get("ads"), list) and not r.get("snapshot"):
            out.extend(r["ads"])
        else:
            out.append(r)
    return out


class MetaApiError(RuntimeError):
    pass


def fetch_meta_api(token: str, search_terms: str, countries: list[str], active_status: str = "ALL",
                   max_ads: int = 100, ad_type: str = "ALL", page_size: int = 50) -> list[dict]:
    params = {
        "search_terms": search_terms,
        "ad_reached_countries": json.dumps(countries),
        "ad_active_status": active_status,
        "ad_type": ad_type,
        "fields": ",".join(META_FIELDS),
        "limit": str(min(page_size, max_ads)),
        "access_token": token,
    }
    url = GRAPH_URL + "?" + urllib.parse.urlencode(params)
    out: list[dict] = []
    while url and len(out) < max_ads:
        try:
            with urllib.request.urlopen(url, timeout=60) as resp:
                payload = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode()).get("error", {})
            except Exception:
                err = {}
            msg = (f"ads_archive HTTP {e.code}: code={err.get('code')} subcode={err.get('error_subcode')} "
                   f"type={err.get('type')} message={err.get('message')}")
            raise MetaApiError(_redact(msg, token)) from None
        except urllib.error.URLError as e:
            raise MetaApiError(_redact(f"ads_archive network error: {e.reason}", token)) from None
        out.extend(payload.get("data") or [])
        url = (payload.get("paging") or {}).get("next")  # contains the token; never printed
    return out[:max_ads]


def ad_library_url(search_terms: str, country: str) -> str:
    q = urllib.parse.urlencode({"active_status": "all", "ad_type": "all", "country": country,
                                "q": search_terms, "search_type": "keyword_unordered", "media_type": "all"})
    return "https://www.facebook.com/ads/library/?" + q


def _apify_json(url: str, token: str, data: bytes | None = None, timeout: int = 60):
    req = urllib.request.Request(url, data=data, headers={"Authorization": f"Bearer {token}",
                                                          "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        raise RuntimeError(_redact(f"apify HTTP {e.code}: {e.read()[:300]!r}", token)) from None


def run_apify(token: str, search_terms: str, countries: list[str], max_ads: int, max_usd: float,
              budget=None, poll_seconds: int = 10, max_wait: int = 1800) -> list[dict]:
    """Start the actor, wait for it, and settle the reservation with what Apify charged.

    The run-sync endpoint gives up after 300 s, which a few hundred ads can exceed, so the run
    is started asynchronously and polled. The reservation is the smaller of the list-price
    estimate and ``max_usd``, and it is passed to Apify as ``maxTotalChargeUsd``, so Apify itself
    stops charging there: the cap is a hard ceiling, not an estimate.
    """
    import time

    from scripts.ads.ad_library.budget import ApifyBudget, estimate_usd

    budget = budget or ApifyBudget()
    cap = round(min(estimate_usd(APIFY_ACTOR, max_ads) + 0.01, max_usd), 4)  # + actor-start events
    if cap <= 0:
        raise ValueError("--max-usd must be greater than 0")
    actor = APIFY_ACTOR.replace("/", "~")
    body = json.dumps({"urls": [{"url": ad_library_url(search_terms, c)} for c in countries],
                       "count": max_ads, "scrapeAdDetails": False}).encode()
    base = "https://api.apify.com/v2"
    with budget.reserve(APIFY_ACTOR, est_usd=cap, note=f"ad_library:{search_terms[:40]}") as res:
        run = _apify_json(f"{base}/acts/{actor}/runs?maxTotalChargeUsd={cap}", token, data=body)["data"]
        waited = 0
        while run.get("status") in ("READY", "RUNNING") and waited < max_wait:
            time.sleep(poll_seconds)
            waited += poll_seconds
            run = _apify_json(f"{base}/actor-runs/{run['id']}", token)["data"]
        if run.get("status") in ("READY", "RUNNING"):
            _apify_json(f"{base}/actor-runs/{run['id']}/abort", token, data=b"")
            run = _apify_json(f"{base}/actor-runs/{run['id']}", token)["data"]
        items = _apify_json(f"{base}/datasets/{run['defaultDatasetId']}/items?format=json&clean=true",
                            token, timeout=300)
        actual = run.get("usageTotalUsd")
        res.settle(float(actual) if actual is not None else cap)
        n = len(items) if isinstance(items, list) else 0
        print(f"apify run {run.get('status')}: {n} items, charged ${float(actual or 0):.4f} "
              f"(ceiling ${cap:.4f})", file=sys.stderr)
    return items[:max_ads] if isinstance(items, list) else []


def ad_text(row: dict) -> str:
    """Every visible text field, including all carousel/catalog cards, for relevance matching."""
    snap = (row.get("raw") or {}).get("snapshot") or {}
    parts = [row.get(k) or "" for k in ("page_name", "title", "body", "link_description")]
    for c in snap.get("cards") or []:
        if isinstance(c, dict):
            parts += [_real(c.get(k)) for k in ("title", "body", "link_description")]
    return " ".join(parts)


def filter_rows(rows, require: str = "", keep_political: bool = False):
    """Drop political/issue ads (their run length tracks an election, not a sale) and, with
    --require, ads whose text never matches the category regex (keyword-search bleed)."""
    rx = re.compile(require, re.I) if require else None
    kept, dropped = [], {"political": 0, "off_category": 0}
    for r in rows:
        if not keep_political and "POLITICAL" in (r.get("categories") or []):
            dropped["political"] += 1
        elif rx and not rx.search(ad_text(r)):
            dropped["off_category"] += 1
        else:
            kept.append(r)
    return kept, dropped


def write_jsonl(rows, path):
    os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    src = ap.add_mutually_exclusive_group(required=True)
    src.add_argument("--from-apify", metavar="FILE")
    src.add_argument("--from-scrapecreators", metavar="FILE")
    src.add_argument("--meta-api", action="store_true")
    src.add_argument("--apify-run", action="store_true")
    ap.add_argument("--search-terms", default="")
    ap.add_argument("--countries", default=",".join(EU_COUNTRIES),
                    help="comma list; default EU (ads_archive only returns commercial ads delivered to the EU)")
    ap.add_argument("--active-status", default="ALL", choices=["ALL", "ACTIVE", "INACTIVE"])
    ap.add_argument("--max", type=int, default=200)
    ap.add_argument("--max-usd", type=float, default=None,
                    help="--apify-run only, required: hard dollar ceiling for this run (Apify maxTotalChargeUsd)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--require", default="",
                    help="regex an ad's text (any field or card) must match to be kept, e.g. 'baseball|softball'")
    ap.add_argument("--keep-political", action="store_true",
                    help="keep political/issue ads (dropped by default)")
    args = ap.parse_args(argv)
    countries = [c.strip().upper() for c in args.countries.split(",") if c.strip()]

    if args.from_apify:
        rows = [normalize_library_record(r, "apify") for r in load_records(args.from_apify)]
    elif args.from_scrapecreators:
        rows = [normalize_library_record(r, "scrapecreators") for r in load_records(args.from_scrapecreators)]
    elif args.meta_api:
        token = os.environ.get("META_ACCESS_TOKEN") or ""
        if not token:
            sys.exit("META_ACCESS_TOKEN is not set")
        if not args.search_terms:
            sys.exit("--meta-api needs --search-terms")
        try:
            recs = fetch_meta_api(token, args.search_terms, countries, args.active_status, args.max)
        except MetaApiError as e:
            sys.exit(str(e))
        rows = [normalize_graph_record(r) for r in recs]
    else:
        token = os.environ.get("APIFY_TOKEN") or ""
        if not token:
            sys.exit("APIFY_TOKEN is not set; --apify-run needs it (or export from Apify and use --from-apify)")
        if not args.search_terms:
            sys.exit("--apify-run needs --search-terms")
        if not args.max_usd or args.max_usd <= 0:
            sys.exit("--apify-run needs --max-usd (the per-run spend ceiling); list price is about $0.75 per 1,000 ads")
        from scripts.ads.ad_library.budget import BudgetExceeded, BudgetUnavailable

        try:
            items = run_apify(token, args.search_terms, countries if len(countries) == 1 else ["ALL"], args.max,
                              args.max_usd)
        except (BudgetExceeded, BudgetUnavailable) as e:
            sys.exit(f"refused: {e}")
        rows = [normalize_library_record(r, "apify") for r in items]

    rows = [r for r in rows if r.get("ad_id")]
    seen, uniq = set(), []
    for r in rows:
        if r["ad_id"] not in seen:
            seen.add(r["ad_id"])
            uniq.append(r)
    rows, dropped = filter_rows(uniq, args.require, args.keep_political)
    write_jsonl(rows, args.out)
    active = sum(r["is_active"] for r in rows)
    print(f"collected {len(rows)} ads ({active} active; dropped {dropped['political']} political, "
          f"{dropped['off_category']} off-category) -> {args.out}")


if __name__ == "__main__":
    main()
