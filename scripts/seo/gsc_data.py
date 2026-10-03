#!/usr/bin/env python3
"""Search Console query x page data: load an export, or pull one from the API.

Search Console is often reachable only from the owner's machine. So every
downstream tool reads a plain file, and ``pull`` writes that file wherever the
credentials live. The file carries its own window and source so a later reader
(the refresh tracker, an audit) never has to guess what period it covers.

    python -m scripts.seo.gsc_data pull --site sc-domain:example.com \
        --start 2026-07-01 --end 2026-09-30 --out data/seo/example-q3.json

Accepted inputs for ``load_rows``:
  - JSON written by ``pull``: {"meta": {...}, "rows": [{query, page, ...}]}
  - Raw API JSON: {"rows": [{"keys": [query, page], clicks, ...}]}
  - CSV with query/page/clicks/impressions/ctr/position columns
    (header names are matched loosely: "Top queries", "Landing page", "URL", ...)
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

_ALIASES = {
    "query": {"query", "queries", "top queries", "search query", "keyword"},
    "page": {"page", "pages", "top pages", "landing page", "url", "address"},
    "clicks": {"clicks", "url clicks"},
    "impressions": {"impressions"},
    "ctr": {"ctr", "url ctr"},
    "position": {"position", "average position", "avg position", "avg. position"},
}


def _canon(header: str) -> Optional[str]:
    h = header.strip().lower().replace("_", " ")
    for key, names in _ALIASES.items():
        if h in names:
            return key
    return None


def _num(value: Any) -> float:
    if value is None or value == "":
        return 0.0
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip().replace(",", "")
    pct = text.endswith("%")
    text = text.rstrip("%")
    try:
        n = float(text)
    except ValueError:
        return 0.0
    return n / 100.0 if pct else n


def normalize_row(raw: Dict[str, Any], dimensions: Tuple[str, ...] = ("query", "page")) -> Optional[Dict[str, Any]]:
    """Return {query, page, clicks, impressions, ctr, position} or None if unusable."""
    row: Dict[str, Any] = {}
    if "keys" in raw and isinstance(raw["keys"], list):
        for dim, val in zip(dimensions, raw["keys"]):
            row[dim] = val
        for k in ("clicks", "impressions", "ctr", "position"):
            row[k] = raw.get(k)
    else:
        for k, v in raw.items():
            c = _canon(str(k))
            if c and c not in row:
                row[c] = v
    if not row.get("page") or row.get("query") in (None, ""):
        return None
    impressions = _num(row.get("impressions"))
    clicks = _num(row.get("clicks"))
    ctr_raw = row.get("ctr")
    if ctr_raw in (None, ""):
        ctr = clicks / impressions if impressions else 0.0
    else:
        ctr = _num(ctr_raw)
        # A CSV that wrote CTR as "3.2" (percent without the sign).
        if ctr > 1:
            ctr = ctr / 100.0
    return {
        "query": str(row["query"]).strip(),
        "page": str(row["page"]).strip(),
        "clicks": clicks,
        "impressions": impressions,
        "ctr": ctr,
        "position": _num(row.get("position")),
    }


def load_rows(path: str | Path) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """Load query x page rows and whatever metadata the file carries."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Search Console export not found: {p}")
    meta: Dict[str, Any] = {"source_file": str(p)}
    rows: List[Dict[str, Any]] = []
    if p.suffix.lower() == ".json":
        payload = json.loads(p.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            meta.update(payload.get("meta") or {})
            raw_rows = payload.get("rows") or []
            dims = tuple(payload.get("dimensions") or meta.get("dimensions") or ("query", "page"))
        else:
            raw_rows, dims = payload, ("query", "page")
        for raw in raw_rows:
            r = normalize_row(raw, dims)
            if r:
                rows.append(r)
    else:
        with p.open(newline="", encoding="utf-8-sig") as fh:
            for raw in csv.DictReader(fh):
                r = normalize_row(raw)
                if r:
                    rows.append(r)
    meta.setdefault("source", "google_search_console")
    return rows, meta


def is_brand(query: str, brand_terms: List[str]) -> bool:
    q = " ".join(query.lower().split())
    q_nospace = q.replace(" ", "")
    for term in brand_terms:
        t = " ".join(term.lower().split())
        if t and (t in q or t.replace(" ", "") in q_nospace):
            return True
    return False


def parse_brand_terms(value: Optional[str]) -> List[str]:
    return [t.strip() for t in (value or "").split(",") if t.strip()]


def pull(site: str, start: str, end: str, credentials: Optional[str] = None,
         row_limit: int = 25000, max_rows: int = 200000) -> Dict[str, Any]:
    """Pull every query x page row for the window via the Search Console API."""
    try:
        from scripts.analytics.search_console import SearchConsole
    except ImportError:
        sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
        try:
            from scripts.analytics.search_console import SearchConsole
        except ImportError as exc:
            raise SystemExit(
                "  The API pull needs the full kai-cmo-harness checkout (scripts/analytics). "
                "Export query x page data from Search Console as CSV instead, or run the pull there."
            ) from exc

    service = SearchConsole(site_url=site, credentials_path=credentials)._get_service()
    rows: List[Dict[str, Any]] = []
    start_row = 0
    while start_row < max_rows:
        resp = service.searchanalytics().query(
            siteUrl=site,
            body={
                "startDate": start,
                "endDate": end,
                "dimensions": ["query", "page"],
                "rowLimit": row_limit,
                "startRow": start_row,
                "dataState": "final",
            },
        ).execute()
        batch = resp.get("rows", [])
        for raw in batch:
            r = normalize_row(raw)
            if r:
                rows.append(r)
        if len(batch) < row_limit:
            break
        start_row += row_limit
    return {
        "meta": {
            "site": site,
            "start": start,
            "end": end,
            "dimensions": ["query", "page"],
            "source": "google_search_console",
            "retrieved_at": date.today().isoformat(),
        },
        "rows": rows,
    }


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("pull", help="Pull query x page rows from the Search Console API to a JSON file")
    p.add_argument("--site", required=True, help="Property, e.g. sc-domain:example.com or https://example.com/")
    p.add_argument("--start", help="YYYY-MM-DD (default: 90 days before --end)")
    p.add_argument("--end", help="YYYY-MM-DD (default: 3 days ago; GSC data lags)")
    p.add_argument("--credentials", help="Service account JSON (default: GOOGLE_CREDENTIALS_PATH)")
    p.add_argument("--out", required=True)
    args = ap.parse_args(argv)

    end = args.end or (date.today() - timedelta(days=3)).isoformat()
    start = args.start or (date.fromisoformat(end) - timedelta(days=89)).isoformat()
    payload = pull(args.site, start, end, args.credentials)
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=1), encoding="utf-8")
    print(f"Wrote {len(payload['rows'])} rows ({start} to {end}) to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
