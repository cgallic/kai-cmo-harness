"""Matomo pull for /kai-local-audit — connected analytics, cleaned of noise.

    python -m scripts.local_audit.matomo --config cfg.json --out <audit-dir>

Needs an owner-provided read token. Set it in the environment under the name
given by ``matomo.token_env`` in the config (default ``MATOMO_TOKEN``); the
token is never written to disk or logged. Config block::

    "matomo": {"base_url": "https://analytics.example.com/index.php",
               "id_site": 1, "date_range": "2026-08-19,2026-09-17",
               "token_env": "MATOMO_TOKEN"}

A dashboard's headline visit count is rarely what a client thinks it is. This
splits visits into real ones, storefront-pixel traffic recorded under sandbox
URLs, automation, and hits from developer machines or staging hosts, then
records each bucket as its own metric so the report can say which number is
the customer number.
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from scripts.local_audit import analysis as A
from scripts.local_audit import dataset_io as D

LOCAL_HOST_MARKERS = ("127.0.0.1", "localhost", "0.0.0.0", "::1")
AUTOMATION_BROWSERS = {"Headless Chrome", "Claude", "PhantomJS", "Chrome Headless"}


class MatomoError(RuntimeError):
    pass


def api(cfg: dict[str, Any], method: str, **params: Any) -> Any:
    token = os.getenv(cfg.get("token_env") or "MATOMO_TOKEN", "")
    if not token:
        raise MatomoError(f"{cfg.get('token_env') or 'MATOMO_TOKEN'} is not set")
    payload = {"module": "API", "method": method, "format": "JSON", "token_auth": token, "idSite": cfg["id_site"], **params}
    req = urllib.request.Request(cfg["base_url"], data=urllib.parse.urlencode(payload).encode(), headers={"User-Agent": "kai-local-audit/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read())


def classify(visit: dict[str, Any], site_host: str) -> str:
    urls = [(a.get("url") or "") for a in visit.get("actionDetails") or []]
    if any(m in u for u in urls for m in LOCAL_HOST_MARKERS):
        return "developer machine"
    if (visit.get("browserName") or "") in AUTOMATION_BROWSERS:
        return "automation and bots"
    if any("web-pixel" in u or "/sandbox/modern" in u for u in urls):
        return "storefront pixel"
    hosts = {urllib.parse.urlparse(u).hostname or "" for u in urls if u}
    if hosts and site_host and not any(h == site_host or h.endswith("." + site_host) for h in hosts):
        return "other host (staging or origin IP)"
    return "real visit"


def summarize(visits: list[dict[str, Any]], site_host: str) -> dict[str, Any]:
    buckets = collections.Counter(classify(v, site_host) for v in visits)
    real = [v for v in visits if classify(v, site_host) == "real visit"]
    actions = [a for v in real for a in v.get("actionDetails") or []]
    single = sum(1 for v in real if len([a for a in v.get("actionDetails") or [] if a.get("type") == "action"]) <= 1)
    other_hosts = collections.Counter(
        urllib.parse.urlparse(a.get("url") or "").hostname or ""
        for v in visits if classify(v, site_host) == "other host (staging or origin IP)"
        for a in v.get("actionDetails") or []
    )
    return {
        "buckets": dict(buckets),
        "real_visits": len(real),
        "real_single_page_visits": single,
        "real_sources": collections.Counter((v.get("referrerName") or v.get("referrerTypeName") or "Direct") for v in real).most_common(15),
        "real_devices": collections.Counter(v.get("deviceType") for v in real).most_common(),
        "real_os": collections.Counter(f"{v.get('operatingSystemName')} {v.get('operatingSystemVersion')}".strip() for v in real).most_common(15),
        "real_browsers": collections.Counter(v.get("browserName") for v in real).most_common(10),
        "real_pages": collections.Counter((a.get("url") or "").split("?")[0] for a in actions if a.get("type") == "action").most_common(15),
        "real_outlinks": collections.Counter(a.get("url") for a in actions if a.get("type") == "outlink").most_common(10),
        "unexpected_hosts": other_hosts.most_common(10),
    }


def run(cfg: dict[str, Any], out: Path) -> dict[str, Any]:
    m = cfg["matomo"]
    site_host = urllib.parse.urlparse("https://" + cfg["domain"]).hostname or cfg["domain"]
    site_host = site_host[4:] if site_host.startswith("www.") else site_host
    date = m.get("date_range") or "last30"
    D.ARTIFACT_ROOT = out
    dataset = D.load_or_create(out, mode=cfg["mode"], url="https://" + cfg["domain"], name=cfg["business"])

    summary = api(m, "VisitsSummary.get", period="range", date=date)
    goals = api(m, "Goals.getGoals", period="range", date=date)
    visits = api(m, "Live.getLastVisitsDetails", period="range", date=date, filter_limit=1000)
    stats = summarize(visits, site_host)
    art = D.write_json(out / "raw" / "matomo_live.json", visits)
    D.write_json(out / "raw" / "matomo_summary.json", {"summary": summary, "goals": goals})

    src = D.replace_source(dataset, D.api_source(
        "matomo", f"Matomo Reporting API (site {m['id_site']}, {date})",
        "Sessions, sources, pages, devices and analytics hygiene",
        m["base_url"], art))
    D.metric(dataset, src, "matomo_visits_tracked", "Visits in the Matomo dashboard", summary.get("nb_visits"), "visits", f"range {date}")
    D.metric(dataset, src, "matomo_visits_real", "Visits that are real people on the site", stats["real_visits"], "visits", "excludes storefront pixel, automation, developer machines and other hosts")
    for bucket, count in stats["buckets"].items():
        if bucket != "real visit":
            D.metric(dataset, src, f"matomo_noise::{A.slug(bucket)}", f"Non-customer visits: {bucket}", count, "visits")
    D.metric(dataset, src, "matomo_goals_configured", "Goals configured in Matomo", len(goals) if isinstance(goals, (list, dict)) else 0, "goals")
    D.metric(dataset, src, "matomo_real_single_page_visits", "Real visits that saw one page", stats["real_single_page_visits"], "visits", f"of {stats['real_visits']}")
    if stats["unexpected_hosts"]:
        D.metric(dataset, src, "matomo_unexpected_hosts", "Hosts reporting into this site that are not the live site", len(stats["unexpected_hosts"]), "hosts", ", ".join(h for h, _ in stats["unexpected_hosts"])[:200])
        D.gap(dataset, "Clean analytics baseline", "Session, source and conversion baselines",
              "Report the cleaned real-visit count and name the noise", "Fix tracking, then re-baseline", "Tracker gating and Matomo site settings")
    if not goals:
        D.gap(dataset, "Matomo goals", "Conversion counts for orders, calls and store clicks",
              "Report outbound clicks instead of conversions", "Configure goals, then measure", "Matomo goal configuration")
    D.write_json(out / "local-audit" / "matomo.json", {"range": date, "dashboard_summary": summary, **stats})
    dataset.write(out)
    return stats


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    if not cfg.get("matomo"):
        print("no 'matomo' block in config — skipping"); return 0
    stats = run(cfg, Path(args.out))
    print("matomo:", stats["buckets"], "| real", stats["real_visits"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
