#!/usr/bin/env python3
"""
SEO Linter — Kai Harness Quality Gate

Structural analysis of content for SEO compliance.
Does not require API calls — pure text analysis.

Usage:
  python3 seo_lint.py --text "content" --keyword "target keyword"
  python3 seo_lint.py --file draft.md --keyword "target keyword"
  python3 seo_lint.py --file draft.md --keyword "target keyword" --json
"""

import argparse
import json
import re
import sys


def extract_sections(text: str) -> dict:
    """Parse markdown structure from content."""
    lines = text.strip().split("\n")

    title = None
    h1 = None
    h2s = []
    meta_desc = None
    paragraphs = []
    current_para = []

    for line in lines:
        stripped = line.strip()

        # Detect meta description comment
        if stripped.lower().startswith("meta:") or stripped.lower().startswith("meta description:"):
            meta_desc = re.sub(r"(?i)meta(?:\s+description)?:\s*", "", stripped).strip()
            continue

        if stripped.startswith("# ") and not h1:
            h1 = stripped[2:].strip()
            if not title:
                title = h1
        elif stripped.startswith("## "):
            h2s.append(stripped[3:].strip())
        elif stripped.startswith("### "):
            pass  # H3s noted but not primary check
        elif stripped:
            current_para.append(stripped)
        else:
            if current_para:
                paragraphs.append(" ".join(current_para))
                current_para = []

    if current_para:
        paragraphs.append(" ".join(current_para))

    return {
        "title": title,
        "h1": h1,
        "h2s": h2s,
        "meta_desc": meta_desc,
        "paragraphs": paragraphs,
    }


def count_words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def avg_sentence_length(text: str) -> float:
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0
    return sum(count_words(s) for s in sentences) / len(sentences)


def keyword_in_text(text: str, keyword: str) -> bool:
    return keyword.lower() in text.lower()


def lint(text: str, keyword: str) -> dict:
    sections = extract_sections(text)
    total_words = count_words(text)
    full_text_lower = text.lower()
    kw_lower = keyword.lower()

    errors = []
    warnings = []

    # Title checks
    if not sections["title"] and not sections["h1"]:
        errors.append("No H1/title found. Add a clear H1 containing the target keyword.")
    elif sections["title"] and kw_lower not in sections["title"].lower():
        errors.append(
            f'Target keyword "{keyword}" not found in title/H1: "{sections["title"]}"'
        )
    if sections["title"]:
        tlen = len(sections["title"])
        if tlen < 40:
            warnings.append(f"Title is {tlen} chars (target 50-60). Too short — may underperform.")
        elif tlen > 65:
            warnings.append(f"Title is {tlen} chars (target 50-60). Trim to avoid truncation in SERPs.")

    # First paragraph check
    first_para = sections["paragraphs"][0] if sections["paragraphs"] else ""
    first_para_words = count_words(first_para)
    if not keyword_in_text(first_para, keyword):
        warnings.append(
            f'Keyword "{keyword}" not in first paragraph. Lead with it within 100 words.'
        )
    if first_para_words > 120:
        warnings.append(
            f"First paragraph is {first_para_words} words. Cut to under 100 — answer the query faster."
        )

    # H2 checks
    if len(sections["h2s"]) < 2:
        warnings.append(
            f"Only {len(sections['h2s'])} H2(s) found. Add subheadings every 300 words minimum."
        )
    h2_text = " ".join(sections["h2s"]).lower()
    if kw_lower not in h2_text:
        warnings.append(
            f'Keyword "{keyword}" not found in any H2. Include it or a close variant in at least one subheading.'
        )

    # Meta description
    if not sections["meta_desc"]:
        warnings.append(
            'No meta description found. Add "Meta: [description]" near the top of the draft.'
        )
    else:
        mlen = len(sections["meta_desc"])
        if mlen < 120:
            warnings.append(f"Meta description is {mlen} chars (target 150-160). Expand it.")
        elif mlen > 165:
            warnings.append(f"Meta description is {mlen} chars (target 150-160). Trim to avoid truncation.")
        if kw_lower not in sections["meta_desc"].lower():
            warnings.append(f'Keyword "{keyword}" not in meta description. Add it within first 50 chars.')

    # Internal links
    internal_links = len(re.findall(r"\[.+?\]\((?!http)", text))
    absolute_internal = len(
        re.findall(r"\[.+?\]\(https?://(?:kaicalls|buildwithkai|awesomebackyardparties|meetkai|connorgallic|vocalscribe)", text)
    )
    total_internal = internal_links + absolute_internal
    if total_internal < 2:
        warnings.append(
            f"Only {total_internal} internal link(s) found. Add at least 2 links to related content."
        )

    # Word count
    if total_words < 800:
        warnings.append(
            f"Word count is {total_words}. Under 800 is thin content — target 1200+ for blog posts."
        )
    elif total_words > 2500:
        warnings.append(
            f"Word count is {total_words}. Over 2500 may dilute focus — consider splitting."
        )

    # Sentence length
    avg_sent = avg_sentence_length(text)
    if avg_sent > 22:
        warnings.append(
            f"Average sentence length is {avg_sent:.1f} words. Target <20. Break up long sentences."
        )

    # Paragraph length check
    long_paras = [p for p in sections["paragraphs"] if count_words(p) > 80]
    if long_paras:
        warnings.append(
            f"{len(long_paras)} paragraph(s) exceed 80 words. Break them up for mobile readability."
        )

    # Keyword density (rough)
    kw_count = len(re.findall(re.escape(kw_lower), full_text_lower))
    density = kw_count / max(total_words, 1) * 100
    if density > 3.0:
        warnings.append(
            f'Keyword density is {density:.1f}% ({kw_count} uses). Over 3% reads as stuffing — aim for 1-2%.'
        )
    elif kw_count < 2:
        warnings.append(
            f'Keyword "{keyword}" appears only {kw_count} time(s). Use it naturally 3-5x.'
        )

    passed = len(errors) == 0

    return {
        "passed": passed,
        "errors": errors,
        "warnings": warnings,
        "stats": {
            "word_count": total_words,
            "h2_count": len(sections["h2s"]),
            "internal_links": total_internal,
            "avg_sentence_length": round(avg_sent, 1),
            "keyword_count": kw_count,
            "keyword_density_pct": round(density, 2),
            "title": sections["title"],
            "meta_desc": sections["meta_desc"],
        },
    }


def format_report(result: dict, as_json: bool = False) -> str:
    if as_json:
        return json.dumps(result, indent=2)

    lines = []
    error_count = len(result["errors"])
    warn_count = len(result["warnings"])

    status = "✅ GATE PASS" if result["passed"] else "❌ GATE FAIL"
    lines.append(f"\n{status}: SEO Lint — {error_count} error(s), {warn_count} warning(s)")
    lines.append("─" * 40)

    s = result["stats"]
    lines.append(
        f"  Words: {s['word_count']} | H2s: {s['h2_count']} | "
        f"Int. links: {s['internal_links']} | Avg sentence: {s['avg_sentence_length']}w | "
        f"KW density: {s['keyword_density_pct']}%"
    )

    if result["errors"]:
        lines.append("\n  ERRORS (must fix before publishing):")
        for e in result["errors"]:
            lines.append(f"  ✗ {e}")

    if result["warnings"]:
        lines.append("\n  WARNINGS (fix for best results):")
        for w in result["warnings"]:
            lines.append(f"  ⚠ {w}")

    if not result["errors"] and not result["warnings"]:
        lines.append("  Clean. All SEO checks passed.")
    elif result["passed"]:
        lines.append("\n  No hard errors. Review warnings before publishing.")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="SEO Linter Quality Gate")
    parser.add_argument("--text", help="Content text to lint")
    parser.add_argument("--file", help="Path to content file")
    parser.add_argument("--keyword", required=True, help="Target keyword")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    if not args.text and not args.file:
        parser.error("Provide --text or --file")

    if args.file:
        with open(args.file) as f:
            content = f.read()
    else:
        content = args.text

    result = lint(content, args.keyword)
    report = format_report(result, as_json=args.json)
    print(report)
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
