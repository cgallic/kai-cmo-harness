#!/usr/bin/env python3
"""Score ad briefs against the patterns that survived in the Ad Library.

Each brief (JSONL: id, hook, body, format, offer) is shown to Jev as an ad draft.
Jev answers yes/no questions about visible features, one per surviving pattern
("does the first sentence ask the reader a question?"), plus brand-fit questions
when --brand FILE is given. Jev never scores the brief; the 0-100 score is
computed here:

  pattern part (70, or 100 without --brand): for every pattern question, the
    brief earns (lift - 1) of the value it matches, scaled between the worst and
    the best possible brief under these patterns.
  brand part (30): brand_fit score 0-3 -> up to 20, speaks to the brand's
    audience -> 10; a brief that uses something the brand says to avoid gets 0, and so
    does one where Jev is unsure (fail closed; the reason says to check it by hand).

Unsure answers count as "does not use". Format is matched in code.

Usage:
  OPENROUTER_API_KEY=... python -m scripts.ads.ad_library.score_briefs --briefs briefs.jsonl \
      --patterns patterns.json --brand brand.txt --out ranked.jsonl --report ranked.md
  python -m scripts.ads.ad_library.score_briefs --mock ...
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ads.ad_library import jev  # noqa: E402
from scripts.ads.ad_library.tag_ads import CHOICES, NOULS, read_jsonl, usage_cost  # noqa: E402

BRAND_QUESTIONS = {
    "brand_fit": {
        "type": "score",
        "instructions": "Using the brand notes above the ad draft, how closely do the draft's words, tone and claims "
                        "match what the notes ask for?",
        "criteria": ["Contradicts the notes", "Unrelated to the notes", "Partly matches the notes",
                     "Matches the notes closely"],
    },
    "brand_audience": {"type": "noul",
                       "instructions": "Does the ad draft speak to the audience that the brand notes describe?"},
    "brand_avoid": {"type": "noul",
                    "instructions": "Does the ad draft use a word, claim, or topic that the brand notes say to avoid?"},
}


def select_patterns(patterns: dict, include_untrusted: bool = False) -> list[dict]:
    return [p for p in patterns.get("patterns", [])
            if p.get("lift") is not None and p["value"] != "other" and (p["trusted"] or include_untrusted)]


def pattern_questions(pats: list[dict]) -> tuple[dict, dict]:
    """Jev questions for the patterns, and pattern -> (question id, expected answer)."""
    qs, how = {}, {}
    for p in pats:
        q, v = p["question"], p["value"]
        if p["source"] == "code":
            how[(q, v)] = ("code", v)
        elif q in NOULS:
            qid = f"p_{q}"
            qs[qid] = NOULS[q]
            how[(q, v)] = (qid, v)
        elif q in CHOICES and v in CHOICES[q]["criteria"]:
            qid = f"p_{q}__{v}"
            qs[qid] = {"type": "noul",
                       "instructions": f"{CHOICES[q]['instructions']} Is this true of the ad: "
                                       f"{CHOICES[q]['criteria'][v]}?"}
            how[(q, v)] = (qid, "yes")
    return qs, how


def state_for(brief: dict, brand: str = "") -> str:
    parts = []
    if brand:
        parts.append(f"Brand notes:\n{brand.strip()[:2000]}\n\n---\nAd draft:")
    if brief.get("format"):
        parts.append(f"Format: {brief['format']}")
    if brief.get("offer"):
        parts.append(f"Offer: {brief['offer']}")
    text = "\n".join(x for x in (brief.get("hook") or "", brief.get("body") or "") if x)
    parts.append(f"Ad text:\n{text}")
    return "\n".join(parts)[:6000]


def score_brief(brief: dict, labels: dict, pats: list[dict], how: dict, use_brand: bool) -> tuple[float, list[str]]:
    by_q = defaultdict(list)
    for p in pats:
        by_q[p["question"]].append(p)
    best = worst = got = 0.0
    reasons = []
    for q, ps in by_q.items():
        lifts = [p["lift"] - 1 for p in ps]
        best += max(0.0, max(lifts))
        worst += min(0.0, min(lifts))
        matched = []
        for p in ps:
            qid, want = how.get((q, p["value"]), (None, None))
            if qid == "code":
                hit = str(brief.get("format") or "").strip().lower() == str(want).lower()
            else:
                hit = qid is not None and labels.get(qid) == want
            if hit:
                matched.append(p)
        if matched:
            m = max(matched, key=lambda p: p["lift"])
            got += m["lift"] - 1
            verb = "uses" if m["lift"] >= 1 else "uses weak pattern"
            reasons.append(f"{verb} {q}={m['value']} ({m['lift']:.2f}x, {m['n']} ads)")
    pattern_max = 70.0 if use_brand else 100.0
    pattern_pts = pattern_max * (got - worst) / (best - worst) if best > worst else pattern_max / 2
    total = pattern_pts
    if use_brand:
        avoid = labels.get("brand_avoid")
        if avoid == "yes":
            reasons.append("brand: uses something the brand notes say to avoid (brand points 0)")
        elif avoid != "no":
            # Fail closed: a brand-safety gate that can't tell is not a pass.
            reasons.append("brand: unclear whether it uses something to avoid; check by hand (brand points 0)")
        else:
            fit = labels.get("brand_fit")
            fit_n = int(fit) if fit not in (None, "unsure") else 0
            total += 20.0 * fit_n / 3
            reasons.append(f"brand fit {fit if fit else 'n/a'}/3")
            if labels.get("brand_audience") == "yes":
                total += 10.0
                reasons.append("speaks to the brand's audience")
    if not any(r.startswith("uses ") for r in reasons):
        reasons.insert(0, "uses none of the surviving patterns")
    return round(max(0.0, min(100.0, total)), 1), reasons


def score_briefs(briefs, patterns, brand="", mock=False, workers=8, model="", include_untrusted=False,
                 answer_fn=None):
    """Rank briefs. ``answer_fn(state, questions) -> response`` replaces the Jev call (tests)."""
    pats = select_patterns(patterns, include_untrusted)
    qs, how = pattern_questions(pats)
    if brand:
        qs.update(BRAND_QUESTIONS)
    if (model or "").startswith("laya"):
        workers = 1
    backend = "mock" if mock else "jev"

    def work(b):
        if not qs:
            return b, {}, None
        st = state_for(b, brand)
        try:
            resp = answer_fn(st, qs) if answer_fn else jev.ask(st, qs, backend=backend, model=model)
        except Exception as e:  # reported per brief; the brief scores 0
            return b, None, str(e)[:200]
        return b, resp, None

    out = []
    with cf.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for b, resp, err in pool.map(work, briefs):
            rec = dict(b)
            rec["jev_error"] = err
            rec["jev_usage"] = (resp or {}).get("usage")
            rec["labels"] = jev.gate_all(qs, (resp or {}).get("answers"))
            if err:
                rec["score"], rec["reasons"] = 0.0, [f"error: {err}"]
            else:
                rec["score"], rec["reasons"] = score_brief(b, rec["labels"], pats, how, bool(brand))
            out.append(rec)
    out.sort(key=lambda r: -r["score"])
    for i, r in enumerate(out, 1):
        r["rank"] = i
    return out, pats


def report(ranked, pats) -> str:
    lines = ["# Brief ranking", "",
             f"{len(ranked)} briefs scored against {len(pats)} survival patterns. "
             "Scores are computed from pattern lifts and gated Jev answers; Jev never scores the brief.", "",
             "| Rank | Score | Brief | Hook | Reasons |", "|---:|---:|---|---|---|"]
    for r in ranked:
        hook = (r.get("hook") or "").replace("|", "/")[:80]
        lines.append(f"| {r['rank']} | {r['score']:.0f} | {r.get('id')} | {hook} | {'; '.join(r['reasons'])} |")
    return "\n".join(lines) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--briefs", required=True)
    ap.add_argument("--patterns", required=True)
    ap.add_argument("--brand", help="text file of brand notes: voice, audience, words/claims to avoid")
    ap.add_argument("--out", required=True)
    ap.add_argument("--report", required=True)
    ap.add_argument("--mock", action="store_true", help="offline deterministic answers; no API calls")
    ap.add_argument("--model", default="", help="pinned System One model, e.g. jev-1.14, jev-1.13, laya/english")
    ap.add_argument("--include-untrusted", action="store_true",
                    help="also use cells under the min-n / min-advertisers threshold (small samples only)")
    ap.add_argument("--workers", type=int, default=8)
    args = ap.parse_args(argv)

    has_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
    if not args.mock and not args.model.startswith("laya") and not has_key:
        sys.exit("set OPENROUTER_API_KEY (or TYPESAFE_API_KEY with JEV_URL), or pass --mock / --model laya/<name>")
    with open(args.patterns, encoding="utf-8") as f:
        patterns = json.load(f)
    brand = open(args.brand, encoding="utf-8").read() if args.brand else ""
    ranked, pats = score_briefs(read_jsonl(args.briefs), patterns, brand, args.mock, args.workers,
                                args.model, args.include_untrusted)
    for path in (args.out, args.report):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in ranked:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    with open(args.report, "w", encoding="utf-8") as f:
        f.write(report(ranked, pats))
    if not pats:
        print("warning: no trusted patterns; scores are neutral. Use --include-untrusted for small samples.")
    charged = usage_cost(ranked)
    cost = f", ${charged:.4f} charged" if charged is not None else ""
    print(f"ranked {len(ranked)} briefs with {len(pats)} patterns{cost} -> {args.out}, {args.report}")


if __name__ == "__main__":
    main()
