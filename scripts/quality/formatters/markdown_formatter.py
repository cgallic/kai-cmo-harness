"""
Content Quality Scorer — Markdown report formatter.
"""

from scripts.quality.types import QualityReport, Category


def format_markdown(report: QualityReport) -> str:
    """Format a QualityReport as a markdown document."""
    lines = []

    lines.append(f"# Content Quality Report")
    lines.append(f"**File:** `{report.file_path}`")
    lines.append(f"**Score:** {report.overall_score:.0f}/100 ({report.overall_grade})")
    lines.append("")

    # Metadata
    meta = report.metadata
    lines.append("## Summary")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    if "word_count" in meta:
        lines.append(f"| Word Count | {meta['word_count']:,} |")
    if "sentence_count" in meta:
        lines.append(f"| Sentences | {meta['sentence_count']} |")
    if "reading_level" in meta:
        lines.append(f"| Reading Level | Grade {meta['reading_level']} |")
    if "paragraph_count" in meta:
        lines.append(f"| Paragraphs | {meta['paragraph_count']} |")
    lines.append("")

    # Category scores
    lines.append("## Scores by Category")
    lines.append("")
    lines.append("| Category | Score | Grade | Weight |")
    lines.append("|----------|-------|-------|--------|")
    for cat in report.categories:
        lines.append(
            f"| {cat.category.value} | {cat.score:.0f}/100 | {cat.grade} | {cat.weight:.0%} |"
        )
    lines.append("")

    # Details per category
    for cat_score in report.categories:
        lines.append(f"## {cat_score.category.value}")
        lines.append("")

        # GEO signals
        if cat_score.category == Category.GEO_SIGNALS:
            lines.append("| Signal | Count | Target | Visibility Boost |")
            lines.append("|--------|-------|--------|-----------------|")
            for rule in cat_score.rules:
                meta = rule.metadata
                count = meta.get("count", 0)
                target = meta.get("target", 0)
                status = "pass" if count >= target else "**needs work**"
                lines.append(
                    f"| {rule.rule_name} | {count} | {target}+ | {status} |"
                )
            lines.append("")
            continue

        # Four U's
        if cat_score.category == Category.FOUR_US:
            for rule in cat_score.rules:
                meta = rule.metadata
                if meta.get("skipped"):
                    lines.append(f"*Skipped: {meta.get('reason', 'LLM unavailable')}*")
                    continue
                lines.append("| Dimension | Score | Evidence |")
                lines.append("|-----------|-------|----------|")
                for dim in ["unique", "useful", "ultra_specific", "urgent"]:
                    data = meta.get(dim, {})
                    display = dim.replace("_", "-").title()
                    lines.append(
                        f"| {display} | {data.get('score', 0)}/4 | {data.get('evidence', '')[:80]} |"
                    )
                total = meta.get("total", 0)
                lines.append(f"\n**Total: {total}/16**")
            lines.append("")
            continue

        # Standard rules
        for rule in cat_score.rules:
            status = "PASS" if rule.passed else "WARN"
            lines.append(f"### {status} {rule.rule_id}: {rule.rule_name}")
            lines.append("")
            if rule.passed:
                lines.append("No violations found.")
            else:
                lines.append(f"**{len(rule.violations)} violation(s):**")
                lines.append("")
                for v in rule.violations[:5]:
                    line_ref = f"L{v.line}: " if v.line > 0 else ""
                    lines.append(f"- {line_ref}{v.text}")
                    lines.append(f"  - **Fix:** {v.fix}")
                if len(rule.violations) > 5:
                    lines.append(f"- *...and {len(rule.violations) - 5} more*")
            lines.append("")

    # Top fixes
    fixes = report.top_fixes
    if fixes:
        lines.append("## Top Fixes (Highest Impact)")
        lines.append("")
        for i, fix in enumerate(fixes, 1):
            v = fix["first_violation"]
            line_ref = f"[L{v['line']}] " if v.get("line", 0) > 0 else ""
            lines.append(f"{i}. {line_ref}{fix['suggestion']} (+{fix['impact']:.0f} pts)")
        lines.append("")

    return "\n".join(lines)
