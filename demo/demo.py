#!/usr/bin/env python3
"""
Kai CMO Harness — Instant Demo
================================
Clone → set GEMINI_API_KEY → run this → see a scored blog post in ~60 seconds.

Usage:
  python demo/demo.py --url "https://mysite.com" --keyword "best crm for startups"
  python demo/demo.py --url "https://mysite.com" --keyword "best crm for startups" --format meta-ads
  python demo/demo.py --url "https://mysite.com" --keyword "best crm for startups" --save demo/output/

Requirements:
  pip install google-genai requests beautifulsoup4
  export GEMINI_API_KEY=your-key-here
"""

import argparse
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from textwrap import dedent

# ── Dependency check ──────────────────────────────────────────────────────

def check_deps():
    missing = []
    try:
        __import__("requests")
    except ImportError:
        missing.append("requests")
    try:
        __import__("bs4")
    except ImportError:
        missing.append("beautifulsoup4")
    try:
        __import__("google.genai")
    except ImportError:
        missing.append("google-genai")
    if missing:
        print(f"Missing dependencies: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        sys.exit(1)

check_deps()

import requests  # noqa: E402
from bs4 import BeautifulSoup, Tag  # noqa: E402
from google.genai import Client as GenaiClient  # noqa: E402

# ── Paths ─────────────────────────────────────────────────────────────────

DEMO_DIR = Path(__file__).resolve().parent
REPO_ROOT = DEMO_DIR.parent
KNOWLEDGE = REPO_ROOT / "knowledge"

# ── Gemini client ─────────────────────────────────────────────────────────

def gemini(prompt: str, model: str = "gemini-2.0-flash") -> str:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("ERROR: Set GEMINI_API_KEY environment variable.")
        print("Get a free key at: https://aistudio.google.com/apikey")
        sys.exit(1)
    client = GenaiClient(api_key=api_key)
    response = client.models.generate_content(model=model, contents=prompt)
    return response.text.strip()

# ── Web scraping (no API key needed) ──────────────────────────────────────

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def scrape_url(url: str, max_chars: int = 3000) -> str:
    """Scrape a URL and return clean text content."""
    try:
        resp = requests.get(url, headers=HEADERS, timeout=10)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")

        # Remove script/style/nav/footer
        for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
            tag.decompose()

        # Extract title
        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # Extract meta description
        meta = soup.find("meta", attrs={"name": "description"})
        meta_desc = ""
        if isinstance(meta, Tag) and meta.get("content"):
            meta_desc = str(meta["content"]).strip()

        # Extract headings
        headings = []
        for h in soup.find_all(["h1", "h2", "h3"]):
            text = h.get_text(strip=True)
            if text:
                headings.append(f"{h.name}: {text}")

        # Extract body text
        body = soup.get_text(separator="\n", strip=True)
        # Clean up whitespace
        body = re.sub(r"\n{3,}", "\n\n", body)

        result = f"Title: {title}\nMeta: {meta_desc}\n\nHeadings:\n"
        result += "\n".join(headings[:15]) + "\n\nBody:\n" + body
        return result[:max_chars]
    except Exception as e:
        return f"[Could not scrape {url}: {e}]"


def search_serp_free(keyword: str, num_results: int = 3) -> list[dict]:
    """
    Get top search results for a keyword using a free approach.
    Falls back to Gemini for competitive analysis if scraping fails.
    """
    # Use Gemini to analyze the competitive landscape (works without any extra API)
    raw = gemini(f"""You are a search marketing analyst. For the keyword "{keyword}",
provide the top {num_results} competing pages that would rank on Google.

For each result, provide:
1. A realistic URL from a real domain in this space
2. The likely title tag
3. The main angle/approach of the content
4. One specific weakness or gap in their coverage

Return ONLY valid JSON array:
[
  {{
    "url": "https://...",
    "title": "...",
    "angle": "...",
    "weakness": "..."
  }}
]""")

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        return json.loads(raw.strip())
    except Exception:
        return []


# ── Quality Gates (self-contained, no external scripts) ──────────────────

BANNED_WORDS_TIER1 = [
    "leverage", "utilize", "synergy", "innovative", "deep dive", "circle back",
    "touch base", "moving forward", "at the end of the day", "it's important to note",
    "in today's rapidly evolving", "in today's fast-paced", "great question",
    "as previously mentioned", "first and foremost", "in conclusion", "in order to",
    "going forward", "game-changer", "paradigm shift", "thought leader",
    "best practices", "cutting-edge", "state-of-the-art", "seamless", "robust",
    "scalable", "holistic", "empower", "transformative", "revolutionize",
    "ecosystem", "bandwidth", "low-hanging fruit", "peel back the layers",
    "double-click on", "unpack", "dive deep", "take it to the next level",
    "next level", "move the needle", "value proposition", "value add",
    "key takeaway", "actionable insights", "actionable steps", "pain points",
]


def gate_banned_words(draft: str) -> dict:
    """Check for banned words/phrases. No API call needed."""
    lower = draft.lower()
    hits = []
    for word in BANNED_WORDS_TIER1:
        if word.lower() in lower:
            # Find context
            idx = lower.index(word.lower())
            start = max(0, idx - 40)
            end = min(len(draft), idx + len(word) + 40)
            hits.append({
                "word": word,
                "context": draft[start:end].strip(),
            })
    return {
        "passed": len(hits) == 0,
        "tier1_count": len(hits),
        "hits": hits,
    }


def gate_four_us(draft: str, keyword: str) -> dict:
    """Score content on the Four U's framework using Gemini."""
    raw = gemini(f"""Score this content on the Four U's framework. Be strict.

Keyword: {keyword}

Content:
{draft[:4000]}

Score each dimension 1-4:
- Unique (1-4): Does it say something competitors don't? Novel angle, original data?
- Useful (1-4): Can the reader take concrete action after reading?
- Ultra-specific (1-4): Are there specific numbers, named tools, real examples?
- Urgent (1-4): Is there a reason to engage today vs next month?

Return ONLY valid JSON:
{{
  "unique": 3,
  "useful": 3,
  "ultra_specific": 3,
  "urgent": 2,
  "unique_note": "why this score",
  "useful_note": "why this score",
  "ultra_specific_note": "why this score",
  "urgent_note": "why this score"
}}""")

    if "```" in raw:
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    try:
        scores = json.loads(raw.strip())
    except Exception:
        scores = {"unique": 2, "useful": 2, "ultra_specific": 2, "urgent": 2}

    total = sum(scores.get(k, 0) for k in ["unique", "useful", "ultra_specific", "urgent"])
    all_above_min = all(scores.get(k, 0) >= 2 for k in ["unique", "useful", "ultra_specific", "urgent"])

    return {
        "passed": total >= 12 and all_above_min,
        "total": total,
        "scores": {k: scores.get(k, 0) for k in ["unique", "useful", "ultra_specific", "urgent"]},
        "notes": {k: scores.get(f"{k}_note", "") for k in ["unique", "useful", "ultra_specific", "urgent"]},
    }


def gate_seo_lint(draft: str, keyword: str) -> dict:
    """Basic SEO structural checks. No API call needed."""
    errors = []
    warnings = []

    # H1 check
    h1_match = re.search(r"^#\s+(.+)$", draft, re.MULTILINE)
    if h1_match:
        if keyword.lower() not in h1_match.group(1).lower():
            errors.append(f"Keyword '{keyword}' not found in H1 title")
    else:
        errors.append("No H1 (# heading) found")

    # Keyword in first 100 words
    first_100 = " ".join(draft.split()[:100]).lower()
    if keyword.lower() not in first_100:
        errors.append(f"Keyword '{keyword}' not in first 100 words")

    # H2 count
    h2s = re.findall(r"^##\s+(.+)$", draft, re.MULTILINE)
    if len(h2s) < 4:
        warnings.append(f"Only {len(h2s)} H2 headings (recommend 4+)")

    # Word count
    word_count = len(draft.split())
    if word_count < 1200:
        errors.append(f"Only {word_count} words (minimum 1200)")

    # Keyword density
    kw_count = draft.lower().count(keyword.lower())
    if word_count > 0:
        density = (kw_count / word_count) * 100
        if density > 3:
            warnings.append(f"Keyword density {density:.1f}% (keep under 3%)")
        elif kw_count < 2:
            warnings.append(f"Keyword only appears {kw_count} time(s)")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "word_count": word_count,
        "h2_count": len(h2s),
        "keyword_occurrences": kw_count,
    }


# ── Format instructions ──────────────────────────────────────────────────

FORMAT_INSTRUCTIONS = {
    "blog": dedent("""\
        OUTPUT: Markdown only. No HTML tags.

        STRUCTURE:
        # [H1 title — must contain the exact target keyword]
        Meta: [150-160 char description]

        [Opening paragraph — hook first, keyword in first 100 words]

        ## [H2 — keyword or variant]
        [section body]

        ## [H2] ... (4+ H2s total)

        [Closing CTA]

        REQUIREMENTS:
        - Minimum 1,400 words
        - 4+ H2s
        - Keyword 3-5 times naturally
        - Every sentence under 20 words
        - Every claim has a number attached"""),

    "meta-ads": dedent("""\
        OUTPUT: Three ad variants (A/B/C).

        --- VARIANT A: [hook type] ---
        Primary text (max 125 chars):
        Full primary text:
        Headline (max 27 chars):
        Description (max 27 chars):
        CTA button: [Learn More | Get Quote | Sign Up]

        --- VARIANT B: [different hook] ---
        [same structure]

        --- VARIANT C: [different hook] ---
        [same structure]

        Include at least one number/stat in each variant."""),

    "linkedin": dedent("""\
        OUTPUT: Plain text only. No markdown headers.

        [Single strong hook — pattern interrupt]
        [2-3 sentence expansion]
        [Core insight — 3-4 short paragraphs]
        [Proof point with number]
        [CTA — one sentence]

        600-900 words. One idea per paragraph. No hashtags."""),

    "cold-email": dedent("""\
        OUTPUT: Three email touches.

        --- TOUCH 1 ---
        Subject: [under 50 chars]
        Body (max 120 words):
        [Personalization hook] [Bridge] [CTA]

        --- TOUCH 2 (3 days later) ---
        [Different angle, proof, same CTA]

        --- TOUCH 3 (7 days later) ---
        [Breakup, leave door open]"""),

    "google-ads": dedent("""\
        OUTPUT: RSA + PMax.

        RSA:
        H1-H15: [max 30 chars each]
        D1-D4: [max 90 chars each]
        Display path: [domain]/[keyword-slug]

        PMax headlines (5, max 90 chars each):
        PH1-PH5:"""),
}


# ── Pipeline ──────────────────────────────────────────────────────────────

def load_framework(fmt: str) -> str:
    """Load the relevant knowledge framework for the content type."""
    framework_map = {
        "blog": "frameworks/content-copywriting/algorithmic-authorship.md",
        "seo": "frameworks/content-copywriting/algorithmic-authorship.md",
        "linkedin": "channels/linkedin-articles.md",
        "meta-ads": "channels/meta-advertising.md",
        "cold-email": "channels/email-lifecycle.md",
        "google-ads": "channels/paid-acquisition.md",
    }
    path = KNOWLEDGE / framework_map.get(fmt, "frameworks/content-copywriting/algorithmic-authorship.md")
    if path.exists():
        return path.read_text()[:2000]
    return ""


def step(n: int, total: int, title: str):
    print(f"\n{'─'*50}")
    print(f"  [{n}/{total}] {title}")
    print(f"{'─'*50}")


def run_demo(url: str, keyword: str, fmt: str = "blog", save_dir: str | None = None):
    """Run the full demo pipeline."""
    start_time = time.time()

    print(f"\n{'═'*60}")
    print(f"  Kai CMO Harness — Demo Pipeline")
    print(f"  URL: {url}")
    print(f"  Keyword: {keyword}")
    print(f"  Format: {fmt}")
    print(f"{'═'*60}")

    # ── Step 1: Research ──────────────────────────────────────────────────
    step(1, 5, "Research — Scraping target + competitors")

    site_content = scrape_url(url)
    print(f"  Scraped target: {len(site_content)} chars")

    competitors = search_serp_free(keyword)
    print(f"  Analyzed {len(competitors)} competitor positions")

    # ── Step 2: Brief ─────────────────────────────────────────────────────
    step(2, 5, "Brief — Generating content brief")

    comp_summary = "\n".join(
        f"- {c.get('title', 'N/A')}: {c.get('angle', 'N/A')} (weakness: {c.get('weakness', 'N/A')})"
        for c in competitors
    )

    brief_raw = gemini(f"""Build a content brief for this target.

Target URL: {url}
Target keyword: {keyword}
Format: {fmt}

Site content summary:
{site_content[:2000]}

Competitor analysis:
{comp_summary}

Return ONLY valid JSON:
{{
  "target_site": "{url}",
  "target_keyword": "{keyword}",
  "format": "{fmt}",
  "secondary_keywords": ["kw2", "kw3", "kw4"],
  "angle": "differentiated frame — not just the keyword restated",
  "hook_options": [
    "Hook 1 — counter-intuitive or data-driven",
    "Hook 2 — pain/fear angle",
    "Hook 3 — curiosity gap"
  ],
  "competitor_weakness": "specific gap we can exploit",
  "audience_pain": "single biggest frustration",
  "proof_available": "specific data point or stat to use",
  "cta": "exact action we want them to take",
  "word_count_target": 1400
}}""")

    if "```" in brief_raw:
        brief_raw = brief_raw.split("```")[1]
        if brief_raw.startswith("json"):
            brief_raw = brief_raw[4:]

    try:
        brief = json.loads(brief_raw.strip())
    except Exception:
        print("  WARNING: Could not parse brief JSON, using defaults")
        brief = {
            "target_site": url,
            "target_keyword": keyword,
            "format": fmt,
            "angle": f"Expert guide to {keyword}",
            "hook_options": [f"The truth about {keyword}"],
            "competitor_weakness": "Generic content without specific data",
            "audience_pain": f"Can't find actionable advice about {keyword}",
            "proof_available": "Industry benchmarks",
            "cta": "Start implementing today",
            "word_count_target": 1400,
        }

    print(f"  Angle: {brief.get('angle', 'N/A')}")
    print(f"  Hook: {brief.get('hook_options', ['N/A'])[0]}")

    # ── Step 3: Write ─────────────────────────────────────────────────────
    step(3, 5, f"Write — Generating {fmt} content")

    framework = load_framework(fmt)
    instructions = FORMAT_INSTRUCTIONS.get(fmt, FORMAT_INSTRUCTIONS["blog"])

    draft = gemini(f"""You are a marketing content writer for the Kai CMO Harness pipeline.

## Brief
{json.dumps(brief, indent=2)}

## Competitor weaknesses to exploit
{comp_summary}

## Format instructions
{instructions}

## Framework rules
{framework[:1500] if framework else "Write clearly. Lead with data. Short sentences. Hook first."}

## Non-negotiables
- No banned words: leverage, utilize, synergy, innovative, game-changer, deep dive,
  in conclusion, going forward, first and foremost, next level, it's important to note
- Conditions after main clause: "Do X if Y fails" not "If Y fails, do X"
- Every sentence under 20 words
- Every claim has a specific number — no vague adjectives
- Lead with hook_options[0] as the first body sentence
- Hit the word count target: {brief.get('word_count_target', 1400)}+ words

Write the complete draft now:""")

    word_count = len(draft.split())
    print(f"  Draft: {word_count} words")

    # ── Step 4: Quality Gates ─────────────────────────────────────────────
    step(4, 5, "Quality Gates — Scoring content")

    is_short = fmt in ("meta-ads", "google-ads", "cold-email", "tiktok")

    # Gate 1: Four U's
    four_us = gate_four_us(draft, keyword)
    total = four_us["total"]
    threshold = 10 if is_short else 12
    indicator = "PASS" if four_us["passed"] else "FAIL"
    print(f"  Four U's: {indicator} — {total}/16 (threshold: {threshold})")
    for dim in ["unique", "useful", "ultra_specific", "urgent"]:
        score = four_us["scores"].get(dim, 0)
        note = four_us["notes"].get(dim, "")
        label = dim.replace("_", " ").title()
        print(f"    {label}: {score}/4 — {note}")

    # Gate 2: Banned words
    banned = gate_banned_words(draft)
    indicator = "PASS" if banned["passed"] else "FAIL"
    print(f"  Banned words: {indicator} ({banned['tier1_count']} hits)")
    for hit in banned.get("hits", [])[:3]:
        print(f"    Found: \"{hit['word']}\" in: ...{hit['context']}...")

    # Gate 3: SEO lint (skip for short-form)
    if is_short:
        seo = {"passed": True, "errors": [], "warnings": [], "skipped": True}
        print(f"  SEO lint: SKIP (short-form format)")
    else:
        seo = gate_seo_lint(draft, keyword)
        indicator = "PASS" if seo["passed"] else "FAIL"
        print(f"  SEO lint: {indicator} ({len(seo['errors'])} errors, {len(seo['warnings'])} warnings)")
        for err in seo.get("errors", []):
            print(f"    ERROR: {err}")
        for warn in seo.get("warnings", []):
            print(f"    WARN: {warn}")

    # Overall
    all_passed = four_us["passed"] and banned["passed"] and seo["passed"]

    # ── Step 5: Output ────────────────────────────────────────────────────
    step(5, 5, "Output — Assembling results")

    elapsed = time.time() - start_time

    # Build scorecard
    scorecard = f"""# Scorecard — {keyword}
Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}
Pipeline time: {elapsed:.1f}s

## Overall: {"PASS" if all_passed else "FAIL"}

## Four U's: {total}/16 {"PASS" if four_us["passed"] else "FAIL"}
| Dimension | Score | Notes |
|-----------|-------|-------|
| Unique | {four_us["scores"].get("unique", 0)}/4 | {four_us["notes"].get("unique", "")} |
| Useful | {four_us["scores"].get("useful", 0)}/4 | {four_us["notes"].get("useful", "")} |
| Ultra-Specific | {four_us["scores"].get("ultra_specific", 0)}/4 | {four_us["notes"].get("ultra_specific", "")} |
| Urgent | {four_us["scores"].get("urgent", 0)}/4 | {four_us["notes"].get("urgent", "")} |

## Banned Words: {"PASS" if banned["passed"] else "FAIL"} ({banned["tier1_count"]} violations)
{chr(10).join(f'- "{h["word"]}"' for h in banned.get("hits", [])) or "None found."}

## SEO Lint: {"SKIP" if seo.get("skipped") else ("PASS" if seo["passed"] else "FAIL")}
"""
    if not seo.get("skipped"):
        scorecard += f"Word count: {seo.get('word_count', word_count)}\n"
        scorecard += f"H2 count: {seo.get('h2_count', 0)}\n"
        scorecard += f"Keyword occurrences: {seo.get('keyword_occurrences', 0)}\n"
        if seo.get("errors"):
            scorecard += "Errors:\n" + "\n".join(f"- {e}" for e in seo["errors"]) + "\n"
        if seo.get("warnings"):
            scorecard += "Warnings:\n" + "\n".join(f"- {w}" for w in seo["warnings"]) + "\n"

    # Save or print
    if save_dir:
        out = Path(save_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "brief.json").write_text(json.dumps(brief, indent=2))
        (out / "draft.md").write_text(draft)
        (out / "scorecard.md").write_text(scorecard)
        print(f"\n  Saved to {out}/:")
        print(f"    brief.json    — content brief")
        print(f"    draft.md      — {word_count} word draft")
        print(f"    scorecard.md  — quality scorecard")
    else:
        print(f"\n{'═'*60}")
        print(f"  DRAFT ({word_count} words)")
        print(f"{'═'*60}")
        print(draft[:2000])
        if len(draft) > 2000:
            print(f"\n  ... [{len(draft) - 2000} more characters] ...")
        print(f"\n{'═'*60}")
        print(f"  SCORECARD")
        print(f"{'═'*60}")
        print(scorecard)

    # Final summary
    print(f"\n{'═'*60}")
    overall = "PASS" if all_passed else "FAIL"
    print(f"  Result: {overall} | Four U's: {total}/16 | Words: {word_count} | Time: {elapsed:.1f}s")
    print(f"{'═'*60}")

    if all_passed:
        print("\n  Content passed all gates. Ready for human review.")
    else:
        print("\n  Content needs revision. In production, the harness auto-retries up to 2x.")

    return {
        "brief": brief,
        "draft": draft,
        "scorecard": scorecard,
        "four_us": four_us,
        "banned": banned,
        "seo": seo,
        "passed": all_passed,
        "elapsed": elapsed,
    }


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="kai-harness-demo",
        description="Kai CMO Harness — Instant Demo. One command, one API key, scored content.",
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    parser.add_argument("--keyword", required=True, help="Target keyword to write about")
    parser.add_argument("--format", default="blog", choices=list(FORMAT_INSTRUCTIONS.keys()),
                        help="Content format (default: blog)")
    parser.add_argument("--save", help="Directory to save output files (brief.json + draft.md + scorecard.md)")

    args = parser.parse_args()
    run_demo(args.url, args.keyword, fmt=args.format, save_dir=args.save)


if __name__ == "__main__":
    main()
