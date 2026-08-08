#!/usr/bin/env python3
"""
Agent-Readiness Linter — Kai Harness Quality Gate

Audits a live URL against the agent-readiness checklist. Catches the top P0
regressions before agents see them.

Checks:
  1. /robots.txt exists + does not block core AI search/discovery bots
  2. Training bot decisions are explicit where possible
  3. /llms.txt exists + valid format (P1, not a Google Search requirement)
  4. Main page renders meaningful content without JavaScript
  5. Capability signaling: plain-text product description above the fold
  6. Organization JSON-LD schema present on homepage
  7. Semantic HTML and accessible interactive controls are present
  8. Critical facts are not likely trapped only in images or PDFs

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

DISCOVERY_SEARCH_TOKENS = [
    "Googlebot",
    "bingbot",
    "OAI-SearchBot",
    "Claude-SearchBot",
    "PerplexityBot",
]

USER_TRIGGERED_TOKENS = [
    "ChatGPT-User",
    "Claude-User",
    "Perplexity-User",
]

TRAINING_DECISION_TOKENS = [
    "GPTBot",
    "ClaudeBot",
    "Google-Extended",
    "CCBot",
    "Bytespider",
    "Meta-ExternalAgent",
    "Applebot-Extended",
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


def parse_robot_groups(body: str) -> list[dict]:
    groups: list[dict] = []
    agents: list[str] = []
    rules: list[tuple[str, str]] = []
    saw_rules = False

    def flush() -> None:
        nonlocal agents, rules, saw_rules
        if agents or rules:
            groups.append({"agents": [a.lower() for a in agents], "rules": rules[:]})
        agents = []
        rules = []
        saw_rules = False

    for raw_line in body.splitlines():
        line = raw_line.split("#", 1)[0].strip()
        if not line:
            flush()
            continue

        if ":" not in line:
            continue

        key, value = [part.strip() for part in line.split(":", 1)]
        key = key.lower()

        if key == "user-agent":
            if saw_rules and agents:
                flush()
            agents.append(value)
            continue

        if key in {"allow", "disallow"} and agents:
            saw_rules = True
            rules.append((key, value))

    flush()
    return groups


def token_has_explicit_group(groups: list[dict], token: str) -> bool:
    wanted = token.lower()
    return any(wanted in group["agents"] for group in groups)


def token_is_fully_blocked(groups: list[dict], token: str) -> bool:
    wanted = token.lower()
    exact_groups = [group for group in groups if wanted in group["agents"]]
    relevant_groups = exact_groups or [group for group in groups if "*" in group["agents"]]

    for group in relevant_groups:
        blocks_root = any(directive == "disallow" and value.strip() == "/" for directive, value in group["rules"])
        allows_root = any(directive == "allow" and value.strip() == "/" for directive, value in group["rules"])
        if blocks_root and not allows_root:
            return True
    return False


def check_robots_txt_body(status: int, body: str) -> dict:
    result = {"id": "robots_txt", "priority": "P0", "pass": False, "details": []}

    if status != 200:
        result["details"].append(f"/robots.txt returned {status}")
        return result

    groups = parse_robot_groups(body)
    blocked_discovery = [t for t in DISCOVERY_SEARCH_TOKENS if token_is_fully_blocked(groups, t)]
    blocked_user_fetchers = [t for t in USER_TRIGGERED_TOKENS if token_is_fully_blocked(groups, t)]

    if blocked_discovery:
        result["details"].append(f"search/discovery bots blocked at root: {', '.join(blocked_discovery)}")
    else:
        result["pass"] = True
        result["details"].append(f"search/discovery bots not root-blocked: {', '.join(DISCOVERY_SEARCH_TOKENS)}")

    if blocked_user_fetchers:
        result["details"].append(f"user-triggered fetchers root-blocked: {', '.join(blocked_user_fetchers)}")

    return result


def check_robots_txt(base: str) -> tuple[dict, int, str]:
    status, body, _ = fetch(urljoin(base, "/robots.txt"))
    return check_robots_txt_body(status, body), status, body


def check_training_bot_decisions(status: int, body: str) -> dict:
    result = {"id": "training_bot_decisions", "priority": "P1", "pass": False, "details": []}
    if status != 200:
        result["details"].append("skipped because /robots.txt could not be fetched")
        return result

    groups = parse_robot_groups(body)
    missing = [t for t in TRAINING_DECISION_TOKENS if not token_has_explicit_group(groups, t)]
    present = [t for t in TRAINING_DECISION_TOKENS if token_has_explicit_group(groups, t)]

    if present:
        result["details"].append(f"explicit training bot decisions: {', '.join(present)}")
    if missing:
        result["details"].append(f"missing explicit training bot decisions: {', '.join(missing)}")

    result["pass"] = not missing
    return result


def check_llms_txt(base: str) -> dict:
    status, body, _ = fetch(urljoin(base, "/llms.txt"))
    result = {"id": "llms_txt", "priority": "P1", "pass": False, "details": []}

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


def strip_tags(fragment: str) -> str:
    text = re.sub(r"<script[\s\S]*?</script>", " ", fragment, flags=re.IGNORECASE)
    text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    return re.sub(r"\s+", " ", text).strip()


def attr_value(attrs: str, name: str) -> str:
    match = re.search(rf'{name}\s*=\s*["\']([^"\']+)["\']', attrs, re.IGNORECASE)
    return match.group(1).strip() if match else ""


def check_semantic_structure(body: str) -> dict:
    result = {"id": "semantic_structure", "priority": "P1", "pass": False, "details": []}

    h1_count = len(re.findall(r"<h1\b", body, flags=re.IGNORECASE))
    h2_count = len(re.findall(r"<h2\b", body, flags=re.IGNORECASE))
    has_main = bool(re.search(r"<main\b|role\s*=\s*['\"]main['\"]", body, flags=re.IGNORECASE))
    has_nav = bool(re.search(r"<nav\b|role\s*=\s*['\"]navigation['\"]", body, flags=re.IGNORECASE))

    if h1_count != 1:
        result["details"].append(f"expected 1 H1, found {h1_count}")
    else:
        result["details"].append("found exactly one H1")

    if h2_count < 1:
        result["details"].append("no H2 sections found")
    else:
        result["details"].append(f"found {h2_count} H2 section(s)")

    if not has_main:
        result["details"].append("missing <main> or role=\"main\" landmark")
    if not has_nav:
        result["details"].append("missing <nav> or navigation landmark")

    result["pass"] = h1_count == 1 and h2_count >= 1 and has_main
    return result


def check_interactive_accessibility(body: str) -> dict:
    result = {"id": "interactive_accessibility", "priority": "P1", "pass": False, "details": []}

    missing_buttons = 0
    for attrs, inner in re.findall(r"<button\b([^>]*)>([\s\S]*?)</button>", body, flags=re.IGNORECASE):
        name = strip_tags(inner) or attr_value(attrs, "aria-label") or attr_value(attrs, "title")
        if not name:
            missing_buttons += 1

    missing_links = 0
    for attrs, inner in re.findall(r"<a\b([^>]*)>([\s\S]*?)</a>", body, flags=re.IGNORECASE):
        href = attr_value(attrs, "href")
        if href.startswith("#") or href.lower().startswith("javascript:"):
            continue
        name = strip_tags(inner) or attr_value(attrs, "aria-label") or attr_value(attrs, "title") or attr_value(inner, "alt")
        if not name:
            missing_links += 1

    labels_for = set(re.findall(r"<label\b[^>]*for\s*=\s*['\"]([^'\"]+)['\"]", body, flags=re.IGNORECASE))
    missing_inputs = 0
    for attrs in re.findall(r"<input\b([^>]*)>", body, flags=re.IGNORECASE):
        input_type = (attr_value(attrs, "type") or "text").lower()
        if input_type in {"hidden", "submit", "button", "reset", "image"}:
            continue
        input_id = attr_value(attrs, "id")
        has_name = attr_value(attrs, "aria-label") or attr_value(attrs, "aria-labelledby") or attr_value(attrs, "placeholder")
        if not has_name and (not input_id or input_id not in labels_for):
            missing_inputs += 1

    if missing_buttons:
        result["details"].append(f"{missing_buttons} button(s) lack accessible names")
    if missing_links:
        result["details"].append(f"{missing_links} link(s) lack accessible names")
    if missing_inputs:
        result["details"].append(f"{missing_inputs} input(s) lack labels or aria labels")
    if not (missing_buttons or missing_links or missing_inputs):
        result["details"].append("interactive controls found have basic accessible names")

    result["pass"] = missing_buttons == 0 and missing_inputs == 0 and missing_links <= 2
    return result


def check_critical_content_formats(body: str, visible_text: str) -> dict:
    result = {"id": "critical_content_formats", "priority": "P1", "pass": False, "details": []}

    word_count = len(visible_text.split())
    images = re.findall(r"<img\b([^>]*)>", body, flags=re.IGNORECASE)
    pdf_links = re.findall(r"href\s*=\s*['\"][^'\"]+\.pdf(?:[?#][^'\"]*)?['\"]", body, flags=re.IGNORECASE)
    missing_alt = sum(1 for attrs in images if "alt=" not in attrs.lower())

    media_only_risk = word_count < 150 and (len(images) >= 3 or pdf_links)
    alt_risk = bool(images) and missing_alt / max(len(images), 1) > 0.5

    if media_only_risk:
        result["details"].append(
            f"only {word_count} visible words with {len(images)} image(s) and {len(pdf_links)} PDF link(s); critical facts may be media-only"
        )
    if alt_risk:
        result["details"].append(f"{missing_alt}/{len(images)} image(s) are missing alt attributes")
    if not media_only_risk and not alt_risk:
        result["details"].append("no obvious image/PDF-only critical-content risk detected")

    result["pass"] = not media_only_risk and not alt_risk
    return result


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
    robots_check, robots_status, robots_body = check_robots_txt(base)
    checks.append(robots_check)
    checks.append(check_training_bot_decisions(robots_status, robots_body))
    checks.append(check_llms_txt(base))

    no_js, visible_text = check_no_js_gating(base)
    checks.append(no_js)
    checks.append(check_capability_signaling(visible_text))

    homepage_status, homepage_body, _ = fetch(base)
    if homepage_status == 200:
        checks.append(check_semantic_structure(homepage_body))
        checks.append(check_interactive_accessibility(homepage_body))
        checks.append(check_critical_content_formats(homepage_body, visible_text))
    else:
        checks.extend(
            [
                {
                    "id": "semantic_structure",
                    "priority": "P1",
                    "pass": False,
                    "details": [f"homepage returned {homepage_status}; semantic checks skipped"],
                },
                {
                    "id": "interactive_accessibility",
                    "priority": "P1",
                    "pass": False,
                    "details": [f"homepage returned {homepage_status}; accessibility checks skipped"],
                },
                {
                    "id": "critical_content_formats",
                    "priority": "P1",
                    "pass": False,
                    "details": [f"homepage returned {homepage_status}; media/content checks skipped"],
                },
            ]
        )

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
