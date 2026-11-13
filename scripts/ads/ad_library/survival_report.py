#!/usr/bin/env python3
"""Which visible ad features show up in long-running ads? Survival lift per gated label.

An ad that keeps running is an ad that pays: nobody keeps spending on a loser,
so advertisers stop losers and keep winners. Buckets (thresholds are flags):
  survivor  ran >= --survivor-days (still active or stopped)
  short     stopped before --short-days
  middle    everything else, including ads still active but younger than
            --survivor-days (their outcome is unknown, so they are left out)

Survivor rate = survivors / (survivors + short). Each advertiser carries equal
total weight, split across its decided ads, so one advertiser with 300 ads
cannot dominate. A label cell is trusted only with >= --min-n ads AND
>= --min-advertisers advertisers.

Ads Jev judged off-category (``in_category`` = no) are dropped before anything is counted.

Usage:
  python -m scripts.ads.ad_library.survival_report --in tagged.jsonl --report survival.md --patterns patterns.json
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ads.ad_library.tag_ads import CATEGORY_KEY, LABEL_KEYS, first_line, read_jsonl  # noqa: E402

CODE_KEYS = ["display_format"]  # labels computed in code, reported alongside Jev's


def bucket(row: dict, survivor_days: int = 60, short_days: int = 21) -> str:
    d = row.get("days_running")
    if d is None:
        return "unknown"
    if d >= survivor_days:
        return "survivor"
    if not row.get("is_active") and d < short_days:
        return "short"
    return "middle"


def advertiser(row: dict) -> str:
    return str(row.get("page_id") or row.get("page_name") or "unknown")


def weights(rows: list[dict]) -> list[float]:
    """Per-row weight: 1 / (decided ads of that advertiser)."""
    n = defaultdict(int)
    for r in rows:
        n[advertiser(r)] += 1
    return [1.0 / n[advertiser(r)] for r in rows]


def weighted_rate(rows, ws) -> float | None:
    tot = sum(ws)
    if not tot:
        return None
    return sum(w for r, w in zip(rows, ws) if r["_bucket"] == "survivor") / tot


def analyze(rows, survivor_days=60, short_days=21, min_n=10, min_advertisers=3, examples=3) -> dict:
    for r in rows:
        r["_bucket"] = bucket(r, survivor_days, short_days)
    decided = [r for r in rows if r["_bucket"] in ("survivor", "short")]
    ws = weights(decided)
    overall = weighted_rate(decided, ws)
    raw_overall = (sum(r["_bucket"] == "survivor" for r in decided) / len(decided)) if decided else None
    cells = []
    for key in LABEL_KEYS + CODE_KEYS:
        groups = defaultdict(list)
        for r, w in zip(decided, ws):
            val = r.get(key) if key in CODE_KEYS else (r.get("labels") or {}).get(key)
            if val in (None, "unsure", ""):
                continue
            groups[val].append((r, w))
        for val, items in groups.items():
            g_rows = [r for r, _ in items]
            rate = weighted_rate(g_rows, [w for _, w in items])
            advs = {advertiser(r) for r in g_rows}
            surv = [r for r in g_rows if r["_bucket"] == "survivor"]
            ex, seen = [], set()
            for r in sorted(surv, key=lambda r: -(r.get("days_running") or 0)):
                if advertiser(r) in seen:
                    continue  # one example per advertiser
                seen.add(advertiser(r))
                ex.append({"ad_id": r.get("ad_id"), "page_name": r.get("page_name"),
                           "days_running": r.get("days_running"),
                           "text": (first_line(r.get("body") or "") or r.get("title") or "")[:200]})
                if len(ex) >= examples:
                    break
            cells.append({
                "question": key, "value": val, "source": "code" if key in CODE_KEYS else "jev",
                "n": len(g_rows), "advertisers": len(advs), "survivors": len(surv),
                "survivor_rate": round(rate, 4) if rate is not None else None,
                "lift": round(rate / overall, 3) if (rate is not None and overall) else None,
                "trusted": len(g_rows) >= min_n and len(advs) >= min_advertisers,
                "examples": ex,
            })
    cells.sort(key=lambda c: (not c["trusted"], -(c["lift"] or 0), -c["n"]))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "thresholds": {"survivor_days": survivor_days, "short_days": short_days,
                       "min_n": min_n, "min_advertisers": min_advertisers},
        "counts": {b: sum(r["_bucket"] == b for r in rows) for b in ("survivor", "short", "middle", "unknown")},
        "ads": len(rows), "advertisers": len({advertiser(r) for r in rows}),
        "decided": len(decided), "decided_advertisers": len({advertiser(r) for r in decided}),
        "overall_survivor_rate": round(overall, 4) if overall is not None else None,
        "overall_survivor_rate_unweighted": round(raw_overall, 4) if raw_overall is not None else None,
        "patterns": cells,
    }


def report(res: dict) -> str:
    t = res["thresholds"]
    pct = lambda v: f"{v * 100:.0f}%" if v is not None else "n/a"
    c = res["counts"]
    lines = ["# Ad survival report", "",
             f"{res['ads']} ads from {res['advertisers']} advertisers. Survivors (ran {t['survivor_days']}+ days): "
             f"{c['survivor']}; short (stopped under {t['short_days']} days): {c['short']}; "
             f"undecided: {c['middle']}; no start date: {c['unknown']}."
             + (f" {res['dropped_off_category']} ads Jev judged off-category were left out."
                if res.get("dropped_off_category") else ""), "",
             f"Overall survivor rate, each advertiser weighted equally: {pct(res['overall_survivor_rate'])} "
             f"(unweighted {pct(res['overall_survivor_rate_unweighted'])}, over {res['decided']} decided ads "
             f"from {res['decided_advertisers']} advertisers).", "",
             f"A cell is trusted only with at least {t['min_n']} ads and {t['min_advertisers']} advertisers. "
             "Untrusted cells are hypotheses.", ""]
    top = [p for p in res["patterns"] if p["trusted"] and (p["lift"] or 0) > 1]
    lines += ["## Top surviving patterns", ""]
    if not top:
        lines += ["None met the trust threshold yet. Collect more ads or more advertisers.", ""]
    for p in top[:10]:
        lines.append(f"### {p['question']} = {p['value']}: {p['lift']:.2f}x lift "
                     f"({pct(p['survivor_rate'])}, {p['n']} ads, {p['advertisers']} advertisers)")
        for e in p["examples"]:
            lines.append(f"- {e['page_name']} ({e['days_running']} days): \"{e['text']}\"")
        lines.append("")
    lines += ["## All cells", "", "| Question | Value | Ads | Advertisers | Survivors | Survivor rate | Lift | Trusted |",
              "|---|---|---:|---:|---:|---:|---:|---|"]
    for p in sorted(res["patterns"], key=lambda p: (p["question"], -p["n"])):
        lift = f"{p['lift']:.2f}x" if p["lift"] is not None else "n/a"
        lines.append(f"| {p['question']} | {p['value']} | {p['n']} | {p['advertisers']} | {p['survivors']} | "
                     f"{pct(p['survivor_rate'])} | {lift} | {'yes' if p['trusted'] else 'no'} |")
    lines += ["", "Run length is the performance signal: advertisers keep paying for ads that work and cut "
              "the ones that don't. Active ads younger than the survivor threshold are left out because "
              "their outcome isn't known yet. Unsure Jev labels are excluded from every cell.", ""]
    return "\n".join(lines)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--patterns", required=True)
    ap.add_argument("--survivor-days", type=int, default=60)
    ap.add_argument("--short-days", type=int, default=21)
    ap.add_argument("--min-n", type=int, default=10)
    ap.add_argument("--min-advertisers", type=int, default=3)
    args = ap.parse_args(argv)
    rows = [r for r in read_jsonl(args.inp) if not r.get("jev_error")]
    off = [r for r in rows if (r.get("labels") or {}).get(CATEGORY_KEY) == "no"]
    rows = [r for r in rows if (r.get("labels") or {}).get(CATEGORY_KEY) != "no"]
    res = analyze(rows, args.survivor_days, args.short_days, args.min_n, args.min_advertisers)
    res["dropped_off_category"] = len(off)
    for path in (args.patterns, args.report):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(args.patterns, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2)
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(report(res))
    trusted = sum(p["trusted"] for p in res["patterns"])
    if off:
        print(f"dropped {len(off)} ads Jev judged off-category")
    print(f"{res['decided']} decided ads, overall survivor rate {res['overall_survivor_rate']}, "
          f"{trusted} trusted cells -> {args.report}, {args.patterns}")


if __name__ == "__main__":
    main()
