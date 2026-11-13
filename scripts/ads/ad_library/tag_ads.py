#!/usr/bin/env python3
"""Tag collected ads with Jev (visible features only) and compute days_running.

One Jev call per ad, through the harness Jev client (``scripts/autonomy/decision_log.py``
via ``jev.py``). The state is the ad's own text fields plus page name, CTA and format.
days_running, body length and first-line length are computed in code.
Choice questions with no "none" option are paired with a companion yes/no
("does any listed option fit?"): Jev's choice always returns one of the options,
so when the companion gates to "no" the label becomes "other".

Usage:
  OPENROUTER_API_KEY=... python -m scripts.ads.ad_library.tag_ads --in ads.jsonl --out tagged.jsonl \
      --category "youth baseball or softball players, parents or coaches"
  python -m scripts.ads.ad_library.tag_ads --mock --in ads.jsonl --out tagged.jsonl
  python -m scripts.ads.ad_library.tag_ads --model laya/english --in ads.jsonl --out tagged.jsonl

Model: jev-1.14 unless --model or JEV_MODEL is set (pinned versions only).
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import sys
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.ads.ad_library import jev  # noqa: E402

CHOICES = {
    "hook_type": {
        "type": "choice",
        "instructions": "How does the first sentence of the ad open?",
        "criteria": {
            "question": "It asks the reader a question",
            "bold_claim_number": "It makes a bold claim that contains a number, percentage or amount",
            "pain_callout": "It names a problem, frustration or pain the reader has",
            "us_vs_them": "It contrasts the product with another product, the old way, or what others do",
            "testimonial_quote": "It quotes a customer or reviewer",
            "offer_first": "It leads with a discount, price, free trial or other offer",
            "curiosity": "It teases something without saying what it is",
            "news": "It announces something new, a launch, or an event",
        },
    },
    "offer_type": {
        "type": "choice",
        "instructions": "What offer does the ad make?",
        "criteria": {
            "discount_pct": "A percentage or amount off",
            "free_trial": "A free trial, free month, or free plan",
            "free_shipping": "Free shipping or delivery",
            "bundle": "A bundle, gift, or extra item included",
            "guarantee": "A money-back or satisfaction guarantee",
            "lead_magnet": "A free guide, quiz, checklist, webinar, or download",
            "no_offer": "No offer is made",
        },
    },
    "angle": {
        "type": "choice",
        "instructions": "Which approach does the ad text mainly use?",
        "criteria": {
            "problem_solution": "States a problem, then presents the product as the fix",
            "transformation": "Describes a before and after change in the reader's life",
            "social_proof": "Points to how many people use or rate the product",
            "authority": "Cites experts, credentials, awards or official approval",
            "comparison": "Compares the product with alternatives",
            "founder_story": "Tells the story of the founder or why the company was started",
            "ugc_style": "Written as a first-person customer talking casually about their experience",
        },
    },
    "proof_type": {
        "type": "choice",
        "instructions": "What evidence does the ad text show?",
        "criteria": {
            "review": "A customer review, rating, or star count",
            "number_stat": "A statistic such as a user count, saving amount, or percentage result",
            "before_after": "A before and after comparison",
            "expert": "A named expert, doctor, or professional",
            "press": "A media outlet, publication, or award",
            "none": "No evidence is shown",
        },
    },
}
# Companion yes/no for choice questions that have no "none"-style option.
COMPANIONS = {
    "hook_type_fits": {"type": "noul", "for": "hook_type",
                       "instructions": "Does the first sentence of the ad open in one of these ways: a question, a "
                                       "claim with a number, naming a pain, a contrast with others, a customer "
                                       "quote, an offer, a tease, or an announcement?"},
    "offer_type_fits": {"type": "noul", "for": "offer_type",
                        "instructions": "Does the ad make an offer that is a discount, free trial, free shipping, "
                                        "bundle, guarantee, or free download, or clearly make no offer at all?"},
    "angle_fits": {"type": "noul", "for": "angle",
                   "instructions": "Does the ad use one of these approaches: problem then fix, before and after, "
                                   "user counts or ratings, experts or awards, comparison with alternatives, "
                                   "founder story, or a casual first-person customer voice?"},
}
NOULS = {
    "price_shown": {"type": "noul", "instructions": "Does the ad text show a price or a currency amount?"},
    "number_in_first_line": {"type": "noul",
                             "instructions": "Does the first sentence contain a number, a currency amount, or a percentage?"},
    "names_competitor_or_old_way": {"type": "noul",
                                    "instructions": "Does the ad name a competing product or brand, or describe the "
                                                    "old way of doing something that the product replaces?"},
    "urgency_deadline": {"type": "noul",
                         "instructions": "Does the ad state a deadline, an end date, limited stock, or words like "
                                         "'today only' or 'ends soon'?"},
    "addresses_reader_as_you_in_first_line": {"type": "noul",
                                              "instructions": "Does the first sentence address the reader as 'you' "
                                                              "or 'your' (or the same word in another language)?"},
}
QUESTIONS = {**CHOICES,
             **{k: {"type": "noul", "instructions": v["instructions"]} for k, v in COMPANIONS.items()},
             **NOULS}
LABEL_KEYS = list(CHOICES) + list(NOULS)  # what the survival report counts
CATEGORY_KEY = "in_category"


def category_question(category: str) -> dict:
    """Keyword search bleeds (novels, politics, marketplaces that mention the keyword once).
    Relevance is a judgment, so Jev answers it; the report drops ads answered "no"."""
    return {CATEGORY_KEY: {"type": "noul",
                           "instructions": f"Is this ad selling a product, service or program for {category}? "
                                           "Answer no if the keyword only appears in passing, in a story, "
                                           "or in a list of unrelated categories."}}


def days_running(row: dict, today: date | None = None) -> int | None:
    """(end_date, or today if still running) minus start_date, in days."""
    start = row.get("start_date")
    if not start:
        return None
    end = row.get("end_date")
    if row.get("is_active") or not end:
        end_d = today or date.today()
    else:
        end_d = date.fromisoformat(end[:10])
    return max(0, (end_d - date.fromisoformat(start[:10])).days)


def first_line(text: str) -> str:
    text = (text or "").strip()
    for sep in ("\n", ". ", "! ", "? "):
        i = text.find(sep)
        if i > 0:
            text = text[: i + 1]
    return text.strip()


def state_for(row: dict) -> str:
    parts = [f"Advertiser: {row.get('page_name') or 'unknown'}"]
    if row.get("display_format"):
        parts.append(f"Format: {row['display_format']}")
    if row.get("cta"):
        parts.append(f"Button: {row['cta']}")
    if row.get("title"):
        parts.append(f"Headline: {row['title']}")
    if row.get("body"):
        parts.append(f"Ad text:\n{row['body']}")
    if row.get("link_description"):
        parts.append(f"Link description: {row['link_description']}")
    if not (row.get("body") or row.get("title") or row.get("link_description")):
        return ""
    return "\n".join(parts)[:4000]


def apply_labels(raw: dict, questions: dict | None = None) -> dict:
    """Gated labels; a choice whose companion gates to "no listed option fits" becomes 'other'."""
    questions = questions or QUESTIONS
    raw = raw or {}
    labels = {q: jev.gate(q, questions[q], a) for q, a in raw.items() if q in questions and q not in COMPANIONS}
    for cq, spec in COMPANIONS.items():
        if cq in raw and spec["for"] in labels and jev.gate(cq, questions.get(cq, spec), raw[cq]) == "no":
            labels[spec["for"]] = "other"
    return labels


def tag_rows(rows, mock=False, workers=8, model="", today=None, answer_fn=None, category: str = ""):
    """Tag every row. ``answer_fn(state, questions) -> response`` replaces the Jev call (tests)."""
    if (model or "").startswith("laya"):
        workers = 1  # one local model; threads only contend for the CPU
    questions = {**QUESTIONS, **(category_question(category) if category else {})}
    backend = "mock" if mock else "jev"

    def work(row):
        state = state_for(row)
        if not state:
            return row, None, "empty"
        try:
            resp = answer_fn(state, questions) if answer_fn else jev.ask(state, questions, backend=backend, model=model)
        except Exception as e:  # one bad ad must not sink the batch; it is reported per row
            return row, None, str(e)[:200]
        return row, resp, None

    out = []
    with cf.ThreadPoolExecutor(max_workers=max(1, workers)) as pool:
        for row, resp, err in pool.map(work, rows):
            rec = dict(row)
            rec["days_running"] = days_running(row, today)
            rec["body_chars"] = len(row.get("body") or "")
            rec["first_line_chars"] = len(first_line(row.get("body") or ""))
            rec["jev_error"] = err
            rec["jev_model"] = (resp or {}).get("model")
            rec["jev_raw"] = (resp or {}).get("answers")
            rec["jev_usage"] = (resp or {}).get("usage")
            rec["labels"] = apply_labels(rec["jev_raw"], questions)
            out.append(rec)
    return out


usage_cost = jev.usage_cost


def read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(l) for l in f if l.strip()]


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--mock", action="store_true", help="offline deterministic answers; no API calls")
    ap.add_argument("--model", default="", help="pinned System One model, e.g. jev-1.14, jev-1.13, laya/english")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--category", default="",
                    help="e.g. 'youth baseball or softball players, parents or coaches'; adds an in_category "
                         "yes/no that survival_report uses to drop keyword-search bleed")
    args = ap.parse_args(argv)

    has_key = os.environ.get("OPENROUTER_API_KEY") or os.environ.get("TYPESAFE_API_KEY")
    if not args.mock and not args.model.startswith("laya") and not has_key:
        sys.exit("set OPENROUTER_API_KEY (or TYPESAFE_API_KEY with JEV_URL), or pass --mock / --model laya/<name>")

    rows, seen = [], set()
    for r in read_jsonl(args.inp):
        if r.get("ad_id") in seen:
            continue
        seen.add(r.get("ad_id"))
        rows.append(r)
    if args.limit:
        rows = rows[: args.limit]
    tagged = tag_rows(rows, args.mock, args.workers, args.model, category=args.category)
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    with open(args.out, "w", encoding="utf-8") as f:
        for r in tagged:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    tokens = sum((r.get("jev_usage") or {}).get("input_tokens", 0) or 0 for r in tagged)
    errs = sum(bool(r["jev_error"]) for r in tagged)
    charged = usage_cost(tagged)
    cost = (f"${charged:.4f} charged (sum of usage.cost)" if charged is not None
            else f"~${tokens / 1e6 * 0.042:.4f} estimated at the vendor's $0.042/M input tokens")
    print(f"tagged {len(tagged)} ads ({errs} errors/empty, {tokens:,} input tokens, {cost}) -> {args.out}")


if __name__ == "__main__":
    main()
