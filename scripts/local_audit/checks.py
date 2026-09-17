"""Direct public checks for /kai-local-audit (no paid API).

    python -m scripts.local_audit.checks access  --config cfg.json --out <audit-dir>
    python -m scripts.local_audit.checks assets  --config cfg.json --out <audit-dir>
    python -m scripts.local_audit.checks dns     --config cfg.json --out <audit-dir>
    python -m scripts.local_audit.checks shopify --config cfg.json --out <audit-dir>
    python -m scripts.local_audit.checks all     --config cfg.json --out <audit-dir>

Shipping quotes need a cart session and are taken in a browser — see
harness/references/local-audit-playbook.md ("Shopify shipping quotes").
"""

from __future__ import annotations

import argparse
import json
import re
import urllib.error
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

from scripts.local_audit import analysis as A
from scripts.local_audit import dataset_io as D

# Real-world browsers that still reach small-business sites. Frameworks with
# "modern browser only" defaults (Rails 8 ``allow_browser versions: :modern``)
# answer the older ones with HTTP 406 while crawlers and link previews get 200.
USER_AGENTS = {
    "iOS 15.8 Safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 15_8 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.6.6 Mobile/15E148 Safari/604.1",
    "iOS 16.7 Safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "iOS 17.1 Safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_1_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1.2 Mobile/15E148 Safari/604.1",
    "iOS 18.6 Safari": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.6 Mobile/15E148 Safari/604.1",
    "iPadOS 16 Safari": "Mozilla/5.0 (iPad; CPU OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1",
    "Instagram in-app iOS 16.7": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20H350 Instagram 385.0.0.21.83 (iPhone10,6; iOS 16_7_10; en_US; en; scale=3.00; 1125x2436; 740817574)",
    "Facebook in-app iOS 16.7": "Mozilla/5.0 (iPhone; CPU iPhone OS 16_7_10 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/20H350 [FBAN/FBIOS;FBAV/512.0.0.44.109;FBDV/iPhone10,6;FBMD/iPhone;FBSN/iOS;FBSV/16.7.10;FBSS/3;FBID/phone;FBLC/en_US;FBOP/5]",
    "Instagram in-app iOS 18.5": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/22F76 Instagram 385.0.0.21.83 (iPhone15,3; iOS 18_5; en_US; en; scale=3.00; 1290x2796; 740817574; IABMV/1)",
    "Android Chrome 119": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Mobile Safari/537.36",
    "Android Chrome 139": "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36",
    "Samsung Internet 23": "Mozilla/5.0 (Linux; Android 13; SM-A536U) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/23.0 Chrome/115.0.0.0 Mobile Safari/537.36",
    "Samsung Internet 28": "Mozilla/5.0 (Linux; Android 14; SM-S921B) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/28.0 Chrome/130.0.0.0 Mobile Safari/537.36",
    "macOS Safari 16.6": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Safari/605.1.15",
    "Firefox 115 ESR": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "Chrome 109 (Windows 7)": "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36",
    "Googlebot smartphone": "Mozilla/5.0 (Linux; Android 6.0.1; Nexus 5X Build/MMB29P) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.7258.94 Mobile Safari/537.36 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)",
    "facebookexternalhit": "facebookexternalhit/1.1 (+http://www.facebook.com/externalhit_uatext.php)",
}
BROWSER_UA = USER_AGENTS["Android Chrome 139"]


def http(url: str, *, method: str = "GET", ua: str = BROWSER_UA, headers: dict | None = None, limit: int | None = None) -> tuple[int, dict, bytes]:
    req = urllib.request.Request(url, method=method, headers={"User-Agent": ua, **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            body = resp.read(limit) if limit else resp.read()
            return resp.status, dict(resp.headers), body
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers or {}), b""
    except Exception:
        return 0, {}, b""


class _Assets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.urls: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag in ("img", "script", "source", "video") and a.get("src"):
            self.urls.append(a["src"])
        if tag == "link" and a.get("href") and (a.get("rel") or "") in ("stylesheet", "preload", "icon"):
            self.urls.append(a["href"])


def cmd_access(run: dict[str, Any]) -> dict[str, Any]:
    rows = {}
    for page in run["cfg"].get("access_urls") or ["https://" + run["cfg"]["domain"] + "/"]:
        rows[page] = {name: http(page, ua=ua, limit=4096)[0] for name, ua in USER_AGENTS.items()}
    art = D.write_json(run["out"] / "raw" / "access_user_agents.json", rows)
    src = D.replace_source(run["dataset"], D.observed_source("access_user_agents", "HTTP status by real browser user agent", "Which browsers can open the site", next(iter(rows)), art))
    for page, statuses in rows.items():
        blocked = [n for n, s in statuses.items() if s >= 400 or s == 0]
        D.metric(run["dataset"], src, f"access_blocked::{A.slug(page)}", f"Browsers refused: {page}", len(blocked), "browsers", ", ".join(blocked) or "none")
    return rows


def cmd_assets(run: dict[str, Any]) -> dict[str, Any]:
    out = {}
    for page in run["cfg"].get("asset_pages") or ["https://" + run["cfg"]["domain"] + "/"]:
        status, _, html = http(page)
        parser = _Assets()
        parser.feed(html.decode("utf-8", "ignore"))
        assets = []
        for rel in dict.fromkeys(parser.urls):
            url = urllib.parse.urljoin(page, rel)
            _, headers, _ = http(url, method="HEAD")
            size = int(headers.get("Content-Length") or headers.get("content-length") or 0)
            row = {"url": url, "bytes": size, "type": headers.get("Content-Type") or headers.get("content-type")}
            if size > 1_000_000 and url.lower().split("?")[0].endswith(".webp"):
                try:
                    row["webp"] = A.webp_animation(http(url)[2])
                except ValueError:
                    pass
            assets.append(row)
        assets.sort(key=lambda r: -r["bytes"])
        out[page] = {"status": status, "html_bytes": len(html), "assets": assets, "total_bytes": len(html) + sum(r["bytes"] for r in assets)}
    art = D.write_json(run["out"] / "raw" / "assets.json", out)
    src = D.replace_source(run["dataset"], D.observed_source("page_assets", "Page asset sizes (HEAD requests) and WebP frame parse", "Page weight and oversized or animated assets", next(iter(out)), art))
    for page, v in out.items():
        D.metric(run["dataset"], src, f"page_weight::{A.slug(page)}", f"Page weight (HTML + referenced assets): {page}", round(v["total_bytes"] / 1_048_576, 2), "MB")
        if v["assets"]:
            D.metric(run["dataset"], src, f"largest_asset::{A.slug(page)}", f"Largest asset: {v['assets'][0]['url']}", round(v["assets"][0]["bytes"] / 1_048_576, 2), "MB")
    return out


def _doh(name: str, rtype: str) -> list[str]:
    _, _, body = http(f"https://cloudflare-dns.com/dns-query?name={urllib.parse.quote(name)}&type={rtype}", headers={"accept": "application/dns-json"})
    try:
        return [a["data"] for a in json.loads(body).get("Answer", [])]
    except Exception:
        return []


def cmd_dns(run: dict[str, Any]) -> dict[str, Any]:
    root = run["cfg"].get("email_domain") or run["cfg"]["domain"].removeprefix("www.")
    selectors = run["cfg"].get("dkim_selectors", ["google", "selector1", "selector2", "default", "k1"])
    records = {"mx": _doh(root, "MX"), "txt": _doh(root, "TXT"), "dmarc": _doh("_dmarc." + root, "TXT"), "dkim": {s: _doh(f"{s}._domainkey.{root}", "TXT") for s in selectors}}
    status = A.email_auth_status(records["txt"], records["dmarc"], [t for v in records["dkim"].values() for t in v])
    art = D.write_json(run["out"] / "raw" / "email_dns.json", {"records": records, "status": status})
    src = D.replace_source(run["dataset"], D.observed_source("email_dns", "DNS over HTTPS (Cloudflare) — MX, SPF, DKIM, DMARC", "Email deliverability of the order/reply address", f"https://cloudflare-dns.com/dns-query?name={root}", art))
    for k, v in status.items():
        D.metric(run["dataset"], src, f"email_{k}", f"{k.upper()} for {root}", v, "record", "DKIM checked only for the listed selectors" if k == "dkim" else "")
    return {"records": records, "status": status}


def cmd_shopify(run: dict[str, Any]) -> dict[str, Any]:
    shop = run["cfg"].get("shopify_domain")
    if not shop:
        return {}
    base = "https://" + shop
    _, _, body = http(base + "/products.json?limit=250")
    try:
        products = json.loads(body).get("products", [])
    except Exception:
        products = []
    policies = {p: http(f"{base}/policies/{p}", limit=2048)[0] for p in ("shipping-policy", "refund-policy", "privacy-policy", "terms-of-service")}
    rows = [{"handle": p["handle"], "title": p["title"], "vendor": p.get("vendor"), "empty_description": not re.sub(r"<[^>]+>|\s", "", p.get("body_html") or ""), "images": len(p.get("images") or []), "variants": [{"id": v["id"], "title": v["title"], "price": v["price"], "available": v.get("available")} for v in p.get("variants", [])]} for p in products]
    out = {"products": rows, "policies": policies}
    art = D.write_json(run["out"] / "raw" / "shopify_storefront.json", out)
    src = D.replace_source(run["dataset"], D.observed_source("shopify_storefront", "Shopify storefront products.json and policy URLs", "Catalog, descriptions, vendor field, published policies", base + "/products.json", art))
    D.metric(run["dataset"], src, "shopify_products", "Products in store", len(rows), "products")
    D.metric(run["dataset"], src, "shopify_empty_descriptions", "Products with empty descriptions", sum(r["empty_description"] for r in rows), "products")
    D.metric(run["dataset"], src, "shopify_placeholder_vendor", "Products with vendor 'My Store'", sum(1 for r in rows if (r["vendor"] or "").strip().lower() == "my store"), "products")
    for p, s in policies.items():
        D.metric(run["dataset"], src, f"shopify_policy::{p}", f"Policy page status: {p}", s, "http_status")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("command", choices=["access", "assets", "dns", "shopify", "all"])
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True)
    args = parser.parse_args(argv)
    cfg = json.loads(Path(args.config).read_text(encoding="utf-8"))
    out = Path(args.out)
    dataset = D.load_or_create(out, mode=cfg["mode"], url="https://" + cfg["domain"], name=cfg["business"])
    run = {"cfg": cfg, "out": out, "dataset": dataset}
    D.ARTIFACT_ROOT = out
    names = ["access", "assets", "dns", "shopify"] if args.command == "all" else [args.command]
    results = {n: globals()[f"cmd_{n}"](run) for n in names}
    D.write_json(out / "local-audit" / f"checks_{args.command}.json", results)
    dataset.write(out)
    print("checks:", ", ".join(names))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
