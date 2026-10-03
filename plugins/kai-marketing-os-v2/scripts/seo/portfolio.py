#!/usr/bin/env python3
"""Portfolio triage: which properties earn more work, and which get none.

Across a portfolio, search clicks concentrate in a few established properties.
New properties without history rarely catch up. This tool makes that explicit
before anyone plans content: each property is labeled

  invest    the smallest set of properties carrying ``--invest-share`` of
            non-brand clicks (and at least ``--invest-min`` clicks a month).
            Refresh queues and new pages go here first.
  maintain  real but minor traffic (at least ``--maintain-min`` clicks a month).
            Fix what is broken; no new content programs.
  freeze    below that. No new pages, no new sibling sites, until an invest
            property's refresh queue is worked through.

Input CSV columns (header names matched loosely):
  site, clicks, impressions, [brand_clicks], [conversions], [days]
``days`` is the window length for that row (default ``--days``); clicks are
normalized to a 30-day month.

    python -m scripts.seo.portfolio --data portfolio.csv --out workspace/seo-refresh
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def _f(v: Any) -> float:
    try:
        return float(str(v).replace(",", "").strip() or 0)
    except ValueError:
        return 0.0


def load_portfolio(path: str, default_days: int = 30) -> List[Dict[str, Any]]:
    out = []
    with open(path, newline="", encoding="utf-8-sig") as fh:
        for raw in csv.DictReader(fh):
            r = {k.strip().lower().replace(" ", "_"): v for k, v in raw.items() if k}
            site = (r.get("site") or r.get("property") or r.get("domain") or "").strip()
            if not site:
                continue
            days = _f(r.get("days")) or default_days
            scale = 30.0 / days
            clicks = _f(r.get("clicks")) * scale
            brand = _f(r.get("brand_clicks") or r.get("branded_clicks")) * scale
            out.append({
                "site": site,
                "clicks_per_month": round(clicks, 1),
                "non_brand_clicks_per_month": round(max(0.0, clicks - brand), 1),
                "impressions_per_month": round(_f(r.get("impressions")) * scale, 1),
                "conversions_per_month": (round(_f(r["conversions"]) * scale, 1)
                                          if r.get("conversions") not in (None, "") else None),
            })
    return out


def triage(props: List[Dict[str, Any]], invest_share: float = 0.8, invest_min: float = 30,
           maintain_min: float = 10) -> Dict[str, Any]:
    ranked = sorted(props, key=lambda p: -p["non_brand_clicks_per_month"])
    total = sum(p["non_brand_clicks_per_month"] for p in ranked) or 1.0
    running = 0.0
    for p in ranked:
        nb = p["non_brand_clicks_per_month"]
        share_before = running / total
        running += nb
        p["share"] = round(nb / total, 3)
        if share_before < invest_share and nb >= invest_min:
            p["tier"] = "invest"
        elif p["clicks_per_month"] >= maintain_min:
            p["tier"] = "maintain"
        else:
            p["tier"] = "freeze"
        imps = p["impressions_per_month"]
        p["ctr"] = round(p["clicks_per_month"] / imps, 4) if imps else None
    counts = {t: sum(1 for p in ranked if p["tier"] == t) for t in ("invest", "maintain", "freeze")}
    invest_clicks = sum(p["non_brand_clicks_per_month"] for p in ranked if p["tier"] == "invest")
    return {
        "schema": "kai.seo.portfolio.v1",
        "params": {"invest_share": invest_share, "invest_min": invest_min, "maintain_min": maintain_min},
        "counts": counts,
        "invest_share_of_non_brand": round(invest_clicks / total, 3) if ranked else 0,
        "properties": ranked,
        "policy": [
            "Work the refresh queue on invest properties before any new page or new property.",
            "Freeze tier gets no new content until it shows clicks from fixes on existing pages.",
            "No conversions recorded means the property's revenue is unknown; instrument before scaling it.",
        ],
    }


def render_markdown(result: Dict[str, Any]) -> str:
    c = result["counts"]
    lines = [
        "# Portfolio triage", "",
        f"{c['invest']} invest · {c['maintain']} maintain · {c['freeze']} freeze. "
        f"Invest properties carry {result['invest_share_of_non_brand']:.0%} of non-brand clicks.", "",
        "| Site | Tier | Non-brand clicks/mo | Clicks/mo | Impressions/mo | CTR | Conversions/mo |",
        "|------|------|---:|---:|---:|---:|---:|",
    ]
    for p in result["properties"]:
        ctr = f"{p['ctr']:.1%}" if p["ctr"] is not None else "n/a"
        conv = p["conversions_per_month"] if p["conversions_per_month"] is not None else "not tracked"
        lines.append(f"| {p['site']} | {p['tier']} | {p['non_brand_clicks_per_month']:.0f} | "
                     f"{p['clicks_per_month']:.0f} | {p['impressions_per_month']:.0f} | {ctr} | {conv} |")
    lines += ["", "## Policy", ""] + [f"- {x}" for x in result["policy"]] + [""]
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--data", required=True)
    ap.add_argument("--days", type=int, default=30, help="Window length when the CSV has no days column")
    ap.add_argument("--invest-share", type=float, default=0.8)
    ap.add_argument("--invest-min", type=float, default=30)
    ap.add_argument("--maintain-min", type=float, default=10)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    result = triage(load_portfolio(args.data, args.days), args.invest_share, args.invest_min, args.maintain_min)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "portfolio.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
    (out / "portfolio.md").write_text(render_markdown(result), encoding="utf-8")
    c = result["counts"]
    print(f"invest {c['invest']} · maintain {c['maintain']} · freeze {c['freeze']} -> {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
