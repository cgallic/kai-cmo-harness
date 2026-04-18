#!/usr/bin/env python3
"""
Agent-Readiness Linter — Kai Harness Quality Gate

Audits a live URL against the agent-readiness checklist. Catches the top P0
regressions before agents see them.

Checks:
  1. /robots.txt exists + has explicit rules for the big-6 AI bot tokens
  2. /llms.txt exists + valid format (H1 + blockquote + H2 sections)
  3. Main page renders meaningful content without JavaScript
  4. Capability signaling: plain-text product description above the fold
  5. Organization JSON-LD schema present on homepage

Usage:
  python3 agent_readiness_lint.py https://example.com
  python3 agent_readiness_lint.py https://example.com --json
  python3 agent_readiness_lint.py https://example.com --strict   # fail on any P0 or P1 miss

Exit codes:
  0  pass
  1  partial (P0 ok, some P1 missing)
  2  fail (P0 missing)
  3  network / fetch error

Reference: knowledge/checklists/agent-readiness-checklist.md
"""

import argparse
import json
import re
import sys
import urllib.request
import urllib.error
from urllib.parse import urljoin, urlparse

USER_AGENT = "kai-agent-readiness-lint/1.0 (+https://github.com/cgallic/kai-cmo-harness)"

BIG_SIX_AI_TOKENS = [
    "GPTBot",
    "ChatGPT-User",
    "ClaudeBot",
    "Claude-User",
    "PerplexityBot",
    "Google-Extended",
]

CAPABILITY_SIGNALS = [
    ("what_it_does", r"\b(platform|tool|service|api|app|software|solution|system)\b"),
    ("who_for", r"\b(for\s+(?:developers|teams|businesses|marketers|agencies|lawyers|startups|enterprises|creators|companies))\b"),
    ("api_surface", r"\b(api|sdk|integration|webhook|mcp)\b"),
    ("pricing_signal", r"\b(free|pricing|plans?|\$\d+|per\s+month|subscription|trial)\b"),
]


def fetch(url: str, timeout: int = 15) -> tuple[int, str, dict]:
    """Return (status, body, headers). Never raises — surfaces errors as status -1."""
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", errors="replace")
            return resp.status, body, dict(resp.headers)
    except urllib.error.HTTPError as e:
        return e.code, "", {}
    except Exception:
        return -1, "", {}


def check_robots_txt(base: str) -> dict:
    status, body, _ = fetch(urljoin(base, "/robots.txt"))
    result = {"id": "robots_txt", "priority": "P0", "pass": False, "details": []}

    if status != 200:
        result["details"].append(f"/robots.txt returned {status}")
        return result

    missing = [t for t in BIG_SIX_AI_TOKENS if not re.search(rf"(?im)^\s*User-agent:\s*{re.escape(t)}\b", body)]
    if missing:
        result["details"].append(f"missing explicit User-agent rules for: {', '.join(missing)}")
    else:
        result["pass"] = True
        result["details"].append("all big-6 AI bot tokens have explicit rules")

    if re.search(r"(?im)^\s*User-agent:\s*\*\s*$.*?^\s*Disallow:\s*/\s*$", body, re.MULTILINE | re.DOTALL):
        result["pass"] = False
        result["details"].append("WARNING: `User-agent: *` blocks entire site — this hides you from everyone")

    return result


def check_llms_txt(base: str) -> dict:
    status, body, _ = fetch(urljoin(base, "/llms.txt"))
    result = {"id": "llms_txt", "priority": "P0", "pass": False, "details": []}

    if status != 200:
        result["details"].append(f"/llms.txt returned {status}")
        return result

    lines = [ln for ln in body.splitlines() if ln.strip()]
    if not lines:
        result["details"].append("/llms.txt is empty")
        return result

    has_h1 = lines[0].startswith("# ")
    has_blockquote = any(ln.lstrip().startswith(">") for ln in lines[:6])
    has_h2 = any(ln.startswith("## ") for ln in lines)
    size_kb = len(body.encode("utf-8")) / 1024

    if not has_h1:
        result["details"].append("missing required H1 on first non-blank line")
    if not has_blockquote:
        result["details"].append("missing required blockquote summary near top")
    if not has_h2:
        result["details"].append("no H2 sections — agents need grouped link lists")
    if size_kb > 8:
        result["details"].append(f"file is {size_kb:.1f} KB (target < 8 KB for single-fetch efficiency)")

    if has_h1 and has_blockquote and has_h2:
        result["pass"] = True
        result["details"].insert(0, f"valid llms.txt ({size_kb:.1f} KB)")

    return result


def check_no_js_gating(base: str) -> tuple[dict, str]:
    status, body, _ = fetch(base)
    result = {"id": "no_js_gating", "priority": "P0", "pass": False, "details": []}

    if status != 200:
        result["details"].append(f"homepage returned {status}")
        return result, ""

    # Strip script/style blocks and all HTML tags
    text = re.sub(r"<script[\s\S]*?</script>", " ", body, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    words = len(text.split())

    if words < 50:
        result["details"].append(f"only {words} words of text render without JS — content likely JS-gated")
    else:
        result["pass"] = True
        result["details"].append(f"{words} words of text render without JS")

    return result, text


def check_capability_signaling(text: str) -> dict:
    result = {"id": "capability_signaling", "priority": "P1", "pass": False, "details": []}

    lowered = text.lower()[:4000]  # above-the-fold proxy
    hits = []
    misses = []
    for name, pattern in CAPABILITY_SIGNALS:
        if re.search(pattern, lowered, re.IGNORECASE):
            hits.append(name)
        else:
            misses.append(name)

    if misses:
        result["details"].append(f"missing plain-text signals: {', '.join(misses)}")
    if hits:
        result["details"].append(f"found signals: {', '.join(hits)}")

    result["pass"] = len(hits) >= 3
    return result


def check_organization_schema(base: str) -> dict:
    status, body, _ = fetch(base)
    result = {"id": "organization_schema", "priority": "P1", "pass": False, "details": []}

    if status != 200:
        result["details"].append(f"homepage returned {status}")
        return result

    jsonld_blocks = re.findall(
        r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        body,
        re.IGNORECASE | re.DOTALL,
    )

    if not jsonld_blocks:
        result["details"].append("no JSON-LD blocks found")
        return result

    found_types = set()
    for block in jsonld_blocks:
        try:
            data = json.loads(block.strip())
        except json.JSONDecodeError:
            continue
        items = data if isinstance(data, list) else [data]
        for item in items:
            if isinstance(item, dict):
                t = item.get("@type")
                if isinstance(t, list):
                    found_types.update(t)
                elif t:
                    found_types.add(t)

    wanted = {"Organization", "WebSite", "SoftwareApplication", "Product"}
    overlap = found_types & wanted
    if overlap:
        result["pass"] = True
        result["details"].append(f"found schema types: {', '.join(sorted(overlap))}")
    else:
        result["details"].append(f"no Organization/WebSite/SoftwareApplication schema (found: {sorted(found_types) or 'none parseable'})")

    return result


def score(checks: list[dict]) -> tuple[str, dict]:
    p0 = [c for c in checks if c["priority"] == "P0"]
    p1 = [c for c in checks if c["priority"] == "P1"]

    p0_pass = sum(1 for c in p0 if c["pass"])
    p1_pass = sum(1 for c in p1 if c["pass"])

    summary = {
        "p0": f"{p0_pass}/{len(p0)}",
        "p1": f"{p1_pass}/{len(p1)}",
    }

    if p0_pass < len(p0):
        return "FAIL", summary
    if p1_pass >= len(p1) * 0.8:
        return "PASS", summary
    return "PARTIAL", summary


def format_text(url: str, checks: list[dict], verdict: str, summary: dict) -> str:
    lines = [f"\nAgent-Readiness Audit — {url}", "=" * 60]
    for c in checks:
        mark = "[PASS]" if c["pass"] else "[FAIL]"
        lines.append(f"{mark} {c['priority']}  {c['id']}")
        for d in c["details"]:
            lines.append(f"         - {d}")
    lines.append("-" * 60)
    lines.append(f"P0: {summary['p0']}   P1: {summary['p1']}   Verdict: {verdict}")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    p = argparse.ArgumentParser(description="Agent-readiness linter for Kai CMO harness")
    p.add_argument("url", help="Base URL to audit (e.g., https://example.com)")
    p.add_argument("--json", action="store_true", help="Output JSON")
    p.add_argument("--strict", action="store_true", help="Fail (exit 1) on any P1 miss, not just P0")
    args = p.parse_args()

    parsed = urlparse(args.url)
    if not parsed.scheme or not parsed.netloc:
        print(f"error: invalid URL: {args.url}", file=sys.stderr)
        return 3
    base = f"{parsed.scheme}://{parsed.netloc}"

    checks = []
    checks.append(check_robots_txt(base))
    checks.append(check_llms_txt(base))

    no_js, visible_text = check_no_js_gating(base)
    checks.append(no_js)
    checks.append(check_capability_signaling(visible_text))
    checks.append(check_organization_schema(base))

    verdict, summary = score(checks)

    if args.json:
        print(json.dumps({"url": base, "verdict": verdict, "summary": summary, "checks": checks}, indent=2))
    else:
        print(format_text(base, checks, verdict, summary))

    if verdict == "FAIL":
        return 2
    if verdict == "PARTIAL":
        return 1 if args.strict else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
