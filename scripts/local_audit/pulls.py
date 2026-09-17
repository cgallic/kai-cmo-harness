"""DataForSEO pulls for /kai-local-audit.

    python -m scripts.local_audit.pulls balance
    python -m scripts.local_audit.pulls <command> --config cfg.json --out workspace/local-audit/<slug>

Commands: volumes, discover, serp, maps, listings, reviews (--collect), backlinks,
ai, lighthouse, crawl (--collect), all. Each writes raw artifacts to ``<out>/raw``,
a readable summary to ``<out>/local-audit/<command>.json``, and registers sources
and metrics in ``<out>/audit-data.json`` (read by the provenance lint).
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from scripts.local_audit import analysis as A
from scripts.local_audit import dataset_io as D
from scripts.local_audit.dfs import Client, DataForSEOError, first_result, has_credentials, task_ok, tasks

MAX_CATEGORIES_PER_REQUEST = 8  # larger lists return 40501 "Invalid Field: 'categories'"


def load_config(path: str) -> dict[str, Any]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    for key in ("business", "domain", "mode"):
        if not cfg.get(key):
            raise SystemExit(f"config missing '{key}'")
    cfg.setdefault("points", {})
    return cfg


def _parallel(fn, jobs, workers=8):
    with ThreadPoolExecutor(workers) as ex:
        return list(ex.map(fn, jobs))


class Run:
    def __init__(self, cfg: dict[str, Any], out: Path):
        self.cfg = cfg
        self.out = out
        self.client = Client(out / "raw")
        D.ARTIFACT_ROOT = out
        self.dataset = D.load_or_create(out, mode=cfg["mode"], url="https://" + cfg["domain"], name=cfg["business"])

    def rel(self, path: str) -> str:
        try:
            return Path(path).resolve().relative_to(self.out.resolve()).as_posix()
        except ValueError:
            return path

    def summary(self, name: str, payload: Any) -> str:
        return D.write_json(self.out / "local-audit" / f"{name}.json", payload)

    def save(self) -> None:
        self.dataset.write(self.out)


# --------------------------------------------------------------------------- volumes
def cmd_volumes(run: Run) -> None:
    rows = []
    for block in run.cfg.get("volumes", []):
        resp, art = run.client.call("keywords_data/google_ads/search_volume/live", [{"location_code": block["location_code"], "keywords": block["keywords"]}])
        art = run.rel(art)
        src = D.replace_source(run.dataset, D.api_source(f"dfs_volumes_{block['location_code']}", f"DataForSEO Google Ads search volume (location {block['location_code']})", "Monthly search volume and 12-month seasonality", "https://api.dataforseo.com/v3/keywords_data/google_ads/search_volume/live", art))
        for t in tasks(resp):
            for r in (t.get("result") or []) if task_ok(t) else []:
                monthly = sorted((m["year"], m["month"], m["search_volume"]) for m in (r.get("monthly_searches") or []))
                rows.append({"location_code": block["location_code"], "keyword": r["keyword"], "volume": r.get("search_volume"), "cpc": r.get("cpc"), "competition": r.get("competition"), "monthly": monthly})
                if r.get("search_volume") is not None:
                    D.metric(run.dataset, src, f"volume::{block['location_code']}::{A.slug(r['keyword'])}", f"Monthly searches: {r['keyword']} ({block['location_code']})", r["search_volume"], "searches/month", "Google Ads groups close variants under one figure")
    run.summary("volumes", rows)


def cmd_discover(run: Run) -> None:
    d = run.cfg.get("discover") or {}
    loc = d.get("location_code")
    if not loc:
        return
    ideas: dict[str, dict[str, Any]] = {}
    arts = []
    for seeds in d.get("seed_batches", []):
        resp, art = run.client.call("keywords_data/google_ads/keywords_for_keywords/live", [{"location_code": loc, "keywords": seeds[:20], "sort_by": "search_volume"}])
        arts.append(art)
        for t in tasks(resp):
            for r in t.get("result") or []:
                ideas.setdefault(r["keyword"], {"keyword": r["keyword"], "volume": r.get("search_volume"), "cpc": r.get("cpc")})
    for site in d.get("sites", []):
        resp, art = run.client.call("keywords_data/google_ads/keywords_for_site/live", [{"location_code": loc, "target": site, "target_type": "site", "sort_by": "search_volume"}])
        arts.append(art)
        for t in tasks(resp):
            for r in t.get("result") or []:
                ideas.setdefault(r["keyword"], {"keyword": r["keyword"], "volume": r.get("search_volume"), "cpc": r.get("cpc"), "site": site})
    buckets: dict[str, list] = {name: [] for name in d.get("intents", {})}
    for idea in sorted(ideas.values(), key=lambda x: -(x["volume"] or 0)):
        for name, pattern in d.get("intents", {}).items():
            if re.search(pattern, idea["keyword"], re.IGNORECASE):
                buckets[name].append(idea)
                break
    run.summary("discover", {"location_code": loc, "idea_count": len(ideas), "artifacts": arts, "buckets": buckets})


# --------------------------------------------------------------------------- serp
def cmd_serp(run: Run) -> None:
    cfg, pts = run.cfg, run.cfg["points"]
    jobs = [(k, p) for k in cfg.get("keywords", []) for p in k.get("points", list(pts))]

    def one(job):
        k, p = job
        resp, art = run.client.call("serp/google/organic/live/advanced", [{"keyword": k["keyword"], "location_coordinate": pts[p] + ",5000", "language_code": k.get("lang", "en"), "device": "mobile", "os": "android", "depth": 30}])
        t = (tasks(resp) or [{}])[0]
        items = first_result(t).get("items") or [] if task_ok(t) else []
        return {
            "keyword": k["keyword"], "lang": k.get("lang", "en"), "group": k.get("group", "all"), "volume": k.get("volume"), "point": p, "artifact": art, "ok": task_ok(t),
            "organic": [(i["rank_group"], i.get("domain")) for i in items if i.get("type") == "organic"][:30],
            "local_pack": [i.get("title") for i in items if i.get("type") == "local_pack"],
            "paa": [e.get("title") for i in items if i.get("type") == "people_also_ask" for e in (i.get("items") or []) if e.get("title")],
            "paid": [i.get("domain") for i in items if i.get("type") == "paid"],
            "features": sorted({i.get("type") for i in items if i.get("type")}),
        }

    obs = _parallel(one, jobs, 12)
    src = D.replace_source(run.dataset, D.api_source("dfs_serp_located", "DataForSEO Google organic SERP (mobile, location_coordinate)", "Located rankings, local packs, People Also Ask, paid ads", "https://api.dataforseo.com/v3/serp/google/organic/live/advanced", ""))
    brand = cfg["domain"]
    for o in obs:
        if not o["ok"]:
            D.gap(run.dataset, f"SERP task: {o['keyword']} @ {o['point']}", "Ranking for this keyword/location", "Do not claim a position", "Re-run the pull")
            continue
        rank = A.brand_rank(o["organic"], brand)
        D.metric(run.dataset, src, f"serp_rank::{A.slug(o['keyword'])}::{A.slug(o['point'])}", f"{brand} position for '{o['keyword']}' from {o['point']} (top 30)", rank if rank else "not in top 30", "position")
    sov = A.share_of_clicks(o for o in obs if o["ok"])
    for group, shares in sov.items():
        D.metric(run.dataset, src, f"share_of_clicks::{A.slug(group)}::{A.slug(brand)}", f"Estimated click share for {brand} — {group}", shares.get(A.normalize_domain(brand), 0.0), "percent", "Modeled: volume × positional CTR (28% #1 … 2.5% #10)")
    packs = A.local_pack_counts(o for o in obs if o["ok"])
    D.metric(run.dataset, src, "serp_paid_ads_total", "Paid ads seen across located SERPs", sum(len(o["paid"]) for o in obs), "ads")
    D.metric(run.dataset, src, "serp_observations", "Located SERP observations", len(obs), "serps")
    run.summary("serp", {"observations": obs, "share_of_clicks": sov, "local_pack_counts": packs.most_common(30), "paa": Counter(q for o in obs for q in o["paa"]).most_common(50), "features": Counter(f for o in obs for f in o["features"]).most_common()})


# --------------------------------------------------------------------------- maps
def cmd_maps(run: Run) -> None:
    cfg, pts = run.cfg, run.cfg["points"]
    brand_re = re.compile(cfg.get("brand_pattern", re.escape(cfg["business"])), re.IGNORECASE)
    jobs = [(q, p) for q in cfg.get("maps_queries", []) for p in q.get("points", list(pts))]

    def one(job):
        q, p = job
        resp, art = run.client.call("serp/google/maps/live/advanced", [{"keyword": q["keyword"], "location_coordinate": pts[p] + ",14z", "language_code": q.get("lang", "en"), "depth": 20}])
        t = (tasks(resp) or [{}])[0]
        items = first_result(t).get("items") or [] if task_ok(t) else []
        rows = [{"rank": i.get("rank_group"), "title": i.get("title"), "category": i.get("category"), "rating": (i.get("rating") or {}).get("value"), "votes": (i.get("rating") or {}).get("votes_count"), "cid": i.get("cid")} for i in items]
        return {"keyword": q["keyword"], "point": p, "artifact": art, "items": rows, "brand_rank": next((r["rank"] for r in rows if brand_re.search(r["title"] or "")), None)}

    obs = _parallel(one, jobs, 12)
    src = D.replace_source(run.dataset, D.api_source("dfs_maps_grid", "DataForSEO Google Maps SERP grid", "Map visibility across nearby towns", "https://api.dataforseo.com/v3/serp/google/maps/live/advanced", ""))
    D.metric(run.dataset, src, "maps_brand_appearances", f"Maps searches where {cfg['business']} appears (top 20)", sum(1 for o in obs if o["brand_rank"]), "searches", f"of {len(obs)} searches")
    top3 = Counter(r["title"] for o in obs for r in o["items"][:3])
    run.summary("maps", {"observations": obs, "top3_counts": top3.most_common(30)})


# --------------------------------------------------------------------------- listings
def cmd_listings(run: Run) -> None:
    cfg = run.cfg
    lcfg = cfg.get("listings") or {}
    out: dict[str, Any] = {"name_matches": [], "category_counts": [], "category_listings": {}}
    src = D.replace_source(run.dataset, D.api_source("dfs_business_listings", "DataForSEO Business Listings (Google business data)", "Listing existence, category gap, market size, prospects", "https://api.dataforseo.com/v3/business_data/business_listings/search/live", ""))
    area = lcfg.get("name_search_area")
    if area:
        matches = {}
        for pattern in lcfg.get("name_patterns", []):  # the `like` filter is case-sensitive
            resp, _ = run.client.call("business_data/business_listings/search/live", [{"location_coordinate": area, "filters": [["title", "like", pattern]], "limit": 100}])
            for t in tasks(resp):
                for i in first_result(t).get("items") or []:
                    matches[i.get("cid") or i["title"]] = {"title": i["title"], "category": i.get("category"), "address": i.get("address"), "cid": i.get("cid")}
        out["name_matches"] = list(matches.values())
        brand_re = re.compile(cfg.get("brand_pattern", re.escape(cfg["business"])), re.IGNORECASE)
        found = [m["title"] for m in matches.values() if brand_re.search(m["title"] or "")]
        D.metric(run.dataset, src, "listing_found", f"Google business listing for {cfg['business']}", "found" if found else "not found", "listing",
                 ("matched: " + "; ".join(found[:5])) if found else "no title matched brand_pattern — brand_pattern must match only this business")
    center = lcfg.get("market_area")
    if center:
        resp, _ = run.client.call("business_data/business_listings/categories_aggregation/live", [{"location_coordinate": center, "limit": 1000}])
        counts = [(i["categories"][0], i["aggregation"]["count"]) for t in tasks(resp) for i in (first_result(t).get("items") or []) if i.get("categories")]
        out["category_counts"] = sorted(counts, key=lambda x: -x[1])
    for group, cats in (lcfg.get("category_groups") or {}).items():
        items: dict[str, dict] = {}
        for start in range(0, len(cats), MAX_CATEGORIES_PER_REQUEST):
            chunk = cats[start:start + MAX_CATEGORIES_PER_REQUEST]
            resp, _ = run.client.call("business_data/business_listings/search/live", [{"location_coordinate": center, "categories": chunk, "order_by": ["rating.votes_count,desc"], "limit": 200}])
            for t in tasks(resp):
                if not task_ok(t):
                    D.gap(run.dataset, f"Listings categories {chunk}", "Market size for this group", "Omit this group", "Fix category ids via categories_aggregation")
                    continue
                for i in first_result(t).get("items") or []:
                    items[i.get("cid") or i["title"]] = {"title": i["title"], "category": i.get("category"), "city": (i.get("address_info") or {}).get("city"), "rating": (i.get("rating") or {}).get("value"), "votes": (i.get("rating") or {}).get("votes_count"), "domain": i.get("domain"), "claimed": i.get("is_claimed"), "cid": i.get("cid"), "maps_url": f"https://maps.google.com/?cid={i.get('cid')}"}
        out["category_listings"][group] = sorted(items.values(), key=lambda x: -(x["votes"] or 0))
        D.metric(run.dataset, src, f"listings_count::{A.slug(group)}", f"Listings within market area: {group}", len(items), "businesses")
    run.summary("listings", out)


# --------------------------------------------------------------------------- reviews
def cmd_reviews(run: Run, collect: bool) -> None:
    targets = run.cfg.get("review_targets", [])
    ids_path = run.out / "local-audit" / "review_task_ids.json"
    if not collect:
        payload = [{"cid": t["cid"], "location_code": t.get("location_code", 2840), "language_code": t.get("lang", "en"), "depth": t.get("depth", 300), "sort_by": "newest", "tag": t["name"]} for t in targets]
        resp, _ = run.client.call("business_data/google/reviews/task_post", payload, cache=False)
        ids = {t["data"]["tag"]: t["id"] for t in tasks(resp) if task_ok(t)}
        D.write_json(ids_path, ids)
        print(f"posted {len(ids)} review tasks; run again with --collect in a few minutes")
        return
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    patterns = run.cfg.get("review_patterns", {})
    src = D.replace_source(run.dataset, D.api_source("dfs_google_reviews", "DataForSEO Google Reviews", "Review text mining: brand mentions, product mentions, owner replies", "https://api.dataforseo.com/v3/business_data/google/reviews/task_get", ""))
    out = {}
    for name, task_id in ids.items():
        resp, _ = run.client.call(f"business_data/google/reviews/task_get/{task_id}", None, cache=False)
        t = (tasks(resp) or [{}])[0]
        if not task_ok(t) or t.get("status_code") != 20000:
            D.gap(run.dataset, f"Google reviews: {name}", "Review mining for this business", "Omit quotes and counts", "Re-collect later")
            continue
        r = first_result(t)
        revs = [{"text": x.get("review_text") or "", "rating": (x.get("rating") or {}).get("value"), "date": (x.get("timestamp") or "")[:10], "owner_reply": bool(x.get("owner_answer"))} for x in r.get("items") or []]
        with_text = [x for x in revs if x["text"]]
        hits = {k: [x for x in with_text if re.search(p, x["text"], re.IGNORECASE)] for k, p in patterns.items()}
        out[name] = {"rating": (r.get("rating") or {}).get("value"), "reviews_count": r.get("reviews_count"), "pulled": len(revs), "with_text": len(with_text), "owner_reply_rate": round(100 * sum(x["owner_reply"] for x in revs) / max(1, len(revs))), "hits": hits}
        D.metric(run.dataset, src, f"reviews_owner_reply_rate::{A.slug(name)}", f"Owner reply rate: {name}", out[name]["owner_reply_rate"], "percent", f"{len(revs)} newest reviews")
        for k, v in hits.items():
            D.metric(run.dataset, src, f"reviews_mentions::{A.slug(name)}::{A.slug(k)}", f"Reviews mentioning {k}: {name}", len(v), "reviews", f"of {len(with_text)} with text")
    run.summary("reviews", out)


# --------------------------------------------------------------------------- backlinks
def cmd_backlinks(run: Run) -> None:
    b = run.cfg.get("backlinks") or {}
    src = D.replace_source(run.dataset, D.api_source("dfs_backlinks", "DataForSEO Backlinks", "Referring domains, spam score, local media link targets", "https://api.dataforseo.com/v3/backlinks/summary/live", ""))
    out: dict[str, Any] = {"summary": {}, "brand_referring_domains": [], "media_targets": []}
    for dom in [run.cfg["domain"]] + b.get("compare_domains", []):
        resp, _ = run.client.call("backlinks/summary/live", [{"target": dom, "include_subdomains": True}])
        t = (tasks(resp) or [{}])[0]
        if not task_ok(t):
            continue
        r = first_result(t)
        out["summary"][dom] = {k: r.get(k) for k in ("rank", "backlinks", "referring_domains", "backlinks_spam_score")}
        D.metric(run.dataset, src, f"referring_domains::{A.slug(dom)}", f"Referring domains: {dom}", r.get("referring_domains"), "domains")
    resp, _ = run.client.call("backlinks/referring_domains/live", [{"target": run.cfg["domain"], "include_subdomains": True, "limit": 200, "order_by": ["rank,desc"]}])
    out["brand_referring_domains"] = [(i["domain"], i.get("rank"), (i.get("first_seen") or "")[:10]) for t in tasks(resp) for i in (first_result(t).get("items") or [])]
    media_re = re.compile(b.get("media_pattern", r"$^"), re.IGNORECASE)
    agg: dict[str, set] = {}
    for dom in b.get("category_leaders", []):
        resp, _ = run.client.call("backlinks/referring_domains/live", [{"target": dom, "include_subdomains": True, "limit": 1000, "order_by": ["rank,desc"]}])
        for t in tasks(resp):
            for i in first_result(t).get("items") or []:
                if media_re.search(i["domain"]):
                    agg.setdefault(i["domain"], set()).add(dom)
    out["media_targets"] = sorted(((d, sorted(v)) for d, v in agg.items()), key=lambda x: -len(x[1]))
    run.summary("backlinks", out)


# --------------------------------------------------------------------------- ai
def cmd_ai(run: Run) -> None:
    a = run.cfg.get("ai") or {}
    brands = a.get("brand_patterns", {run.cfg["business"]: run.cfg.get("brand_pattern", re.escape(run.cfg["business"]))})
    jobs = [(e, p) for e in a.get("engines", []) for p in a.get("prompts", [])]

    def one(job):
        e, prompt = job
        body = {"user_prompt": prompt, "model_name": e["model"], "web_search": True}
        if e["engine"] == "chat_gpt" and a.get("country_iso"):
            body["web_search_country_iso_code"] = a["country_iso"]
        resp, art = run.client.call(f"ai_optimization/{e['engine']}/llm_responses/live", [body])
        t = (tasks(resp) or [{}])[0]
        if not task_ok(t):
            return {"engine": e["engine"], "prompt": prompt, "ok": False}
        r = first_result(t)
        text = " ".join(s.get("text", "") for it in (r.get("items") or []) for s in (it.get("sections") or [it]) if isinstance(s, dict))
        urls = [x.get("url") for it in (r.get("items") or []) for s in (it.get("sections") or []) for x in (s.get("annotations") or []) if x.get("url")]
        return {"engine": e["engine"], "model": e["model"], "prompt": prompt, "ok": True, "mentions": A.brand_mentions(text, brands), "sources": urls[:20], "text": text[:4000], "artifact": art}

    obs = _parallel(one, jobs, 8)
    src = D.replace_source(run.dataset, D.api_source("dfs_ai_optimization", "DataForSEO AI Optimization (LLM responses, web search on)", "Whether AI assistants name the business", "https://api.dataforseo.com/v3/ai_optimization/", ""))
    brand = run.cfg["business"]
    for e in a.get("engines", []):
        rows = [o for o in obs if o["engine"] == e["engine"] and o.get("ok")]
        D.metric(run.dataset, src, f"ai_mentions::{e['engine']}::{A.slug(a.get('label', 'default'))}", f"{e['engine']} answers naming {brand} ({a.get('label', 'default')})", sum(1 for o in rows if o["mentions"].get(brand)), "answers", f"of {len(rows)} prompts")
    domains = Counter(re.sub(r"^https?://(www\.)?", "", u).split("/")[0] for o in obs if o.get("ok") for u in o["sources"])
    run.summary(f"ai_{A.slug(a.get('label', 'default'))}", {"observations": obs, "cited_domains": domains.most_common(30)})


# --------------------------------------------------------------------------- lighthouse / crawl
def cmd_lighthouse(run: Run) -> None:
    src = D.replace_source(run.dataset, D.api_source("dfs_lighthouse", "DataForSEO Lighthouse (mobile)", "Performance, accessibility, SEO scores and failing audits", "https://api.dataforseo.com/v3/on_page/lighthouse/live/json", ""))
    out = {}
    for url in run.cfg.get("lighthouse_urls", []):
        resp, _ = run.client.call("on_page/lighthouse/live/json", [{"url": url, "for_mobile": True, "categories": ["performance", "seo", "accessibility", "best_practices"]}])
        t = (tasks(resp) or [{}])[0]
        if not task_ok(t):
            D.gap(run.dataset, f"Lighthouse: {url}", "Speed and accessibility scores", "Omit scores", "Re-run")
            continue
        r = first_result(t)
        audits = r.get("audits") or {}
        cats = {k: round((v.get("score") or 0) * 100) for k, v in (r.get("categories") or {}).items()}
        failing = [{"id": k, "title": v.get("title"), "display": v.get("displayValue")} for k, v in audits.items() if v.get("score") is not None and v.get("score") < 0.9 and v.get("scoreDisplayMode") not in ("notApplicable", "manual", "informative")]
        out[url] = {"categories": cats, "lcp": (audits.get("largest-contentful-paint") or {}).get("displayValue"), "total_byte_weight": (audits.get("total-byte-weight") or {}).get("displayValue"), "failing": failing}
        for k, v in cats.items():
            D.metric(run.dataset, src, f"lighthouse::{A.slug(url)}::{k}", f"Lighthouse {k}: {url}", v, "score")
    run.summary("lighthouse", out)


def cmd_crawl(run: Run, collect: bool) -> None:
    ids_path = run.out / "local-audit" / "crawl_task_ids.json"
    if not collect:
        ids = {}
        for target in run.cfg.get("crawl_targets", []):
            resp, _ = run.client.call("on_page/task_post", [{"target": target, "max_crawl_pages": 200, "load_resources": True, "enable_javascript": True, "enable_browser_rendering": True, "validate_micromarkup": True, "browser_preset": "mobile"}], cache=False)
            ids.update({target: t["id"] for t in tasks(resp) if task_ok(t)})
        D.write_json(ids_path, ids)
        print(f"posted {len(ids)} crawl tasks; run again with --collect when finished")
        return
    ids = json.loads(ids_path.read_text(encoding="utf-8"))
    src = D.replace_source(run.dataset, D.api_source("dfs_on_page_crawl", "DataForSEO On-Page crawl (mobile, JS rendering)", "Indexable pages, titles, descriptions, headings, resources, broken links", "https://api.dataforseo.com/v3/on_page/", ""))
    out = {}
    for target, task_id in ids.items():
        s, _ = run.client.call(f"on_page/summary/{task_id}", None, cache=False)
        summary = first_result((tasks(s) or [{}])[0])
        if (summary.get("crawl_progress") or "") != "finished":
            print(f"{target}: crawl not finished")
            continue
        pages, _ = run.client.call("on_page/pages", [{"id": task_id, "limit": 200}], cache=False)
        resources, _ = run.client.call("on_page/resources", [{"id": task_id, "limit": 100, "order_by": ["size,desc"]}], cache=False)
        page_rows = [{"url": p["url"], "status": p.get("status_code"), "title": (p.get("meta") or {}).get("title"), "description": (p.get("meta") or {}).get("description"), "h1": ((p.get("meta") or {}).get("htags") or {}).get("h1"), "checks": [k for k, v in (p.get("checks") or {}).items() if v]} for p in first_result((tasks(pages) or [{}])[0]).get("items") or []]
        res_rows = [{"url": r["url"], "type": r.get("resource_type"), "size_kb": round((r.get("size") or 0) / 1024)} for r in first_result((tasks(resources) or [{}])[0]).get("items") or []]
        pm = summary.get("page_metrics") or {}
        out[target] = {"pages": page_rows, "resources": res_rows, "page_metrics": pm, "domain_checks": (summary.get("domain_info") or {}).get("checks")}
        D.metric(run.dataset, src, f"crawl_pages::{A.slug(target)}", f"Pages crawled: {target}", len(page_rows), "pages")
        D.metric(run.dataset, src, f"crawl_broken_links::{A.slug(target)}", f"Broken links: {target}", pm.get("broken_links", 0), "links")
    run.summary("crawl", out)


COMMANDS = ["volumes", "discover", "serp", "maps", "listings", "reviews", "backlinks", "ai", "lighthouse", "crawl"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["balance", "all"] + COMMANDS)
    parser.add_argument("--config")
    parser.add_argument("--out")
    parser.add_argument("--collect", action="store_true", help="collect async reviews/crawl tasks posted earlier")
    args = parser.parse_args(argv)
    if not has_credentials():
        print("DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD not set — record a data gap and continue with public checks", file=sys.stderr)
        return 2
    if args.command == "balance":
        resp, _ = Client(Path(args.out or ".") / "raw", use_cache=False).call("appendix/user_data", None, cache=False)
        print("balance", first_result((tasks(resp) or [{}])[0]).get("money", {}).get("balance"))
        return 0
    if not args.config or not args.out:
        parser.error("--config and --out are required")
    run = Run(load_config(args.config), Path(args.out))
    todo = COMMANDS if args.command == "all" else [args.command]
    for name in todo:
        started = time.time()
        try:
            if name in ("reviews", "crawl"):
                globals()[f"cmd_{name}"](run, args.collect)
            else:
                globals()[f"cmd_{name}"](run)
        except DataForSEOError as exc:
            D.gap(run.dataset, f"DataForSEO {name}", f"All {name} metrics", "Do not publish these metrics", "Fix credentials or request and re-run", str(exc))
        print(f"{name}: done in {time.time() - started:.0f}s")
    run.save()
    print(f"api cost this run: ${run.client.cost:.3f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
