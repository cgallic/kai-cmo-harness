"""
Content Quality Scorer — Terminal output formatter.
"""

from scripts.quality.types import QualityReport, Category


# ANSI color codes
class _C:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[91m"
    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    BLUE = "\033[94m"
    MAGENTA = "\033[95m"
    CYAN = "\033[96m"


def _grade_color(grade: str) -> str:
    return {
        "A": _C.GREEN,
        "B": _C.BLUE,
        "C": _C.YELLOW,
        "D": _C.MAGENTA,
        "F": _C.RED,
    }.get(grade, _C.RESET)


def _severity_label(passed: bool) -> str:
    if passed:
        return f"{_C.GREEN}  PASS{_C.RESET}"
    return f"{_C.YELLOW}  WARN{_C.RESET}"


def format_terminal(report: QualityReport) -> str:
    """Format a QualityReport for terminal output with colors."""
    lines = []
    w = 64  # Width

    # Header
    lines.append(f"{_C.BOLD}{'=' * w}{_C.RESET}")
    lines.append(f"{_C.BOLD}Content Quality Report: {report.file_path}{_C.RESET}")
    lines.append(f"{_C.BOLD}{'=' * w}{_C.RESET}")

    # Overall score
    grade = report.overall_grade
    color = _grade_color(grade)
    lines.append(
        f"{_C.BOLD}Overall Score: {color}{report.overall_score:.0f}/100 ({grade}){_C.RESET}"
    )

    # Metadata
    meta = report.metadata
    meta_parts = []
    if "word_count" in meta:
        meta_parts.append(f"Word Count: {meta['word_count']:,}")
    if "sentence_count" in meta:
        meta_parts.append(f"Sentences: {meta['sentence_count']}")
    if "reading_level" in meta:
        meta_parts.append(f"Reading Level: {meta['reading_level']}")
    if meta_parts:
        lines.append(f"{_C.DIM}{' | '.join(meta_parts)}{_C.RESET}")

    # Categories
    for cat_score in report.categories:
        lines.append(f"\n{_C.DIM}{'-' * w}{_C.RESET}")
        cat_name = cat_score.category.value.upper()
        cat_grade = _grade_color(cat_score.grade)
        lines.append(
            f"{_C.BOLD}{cat_name:<48}{cat_grade}Score: {cat_score.score:.0f}/100{_C.RESET}"
        )
        lines.append(f"{_C.DIM}{'-' * w}{_C.RESET}")

        # GEO signals get special formatting
        if cat_score.category == Category.GEO_SIGNALS:
            for rule in cat_score.rules:
                meta = rule.metadata
                count = meta.get("count", 0)
                target = meta.get("target", 0)
                status = f"{_C.GREEN}PASS{_C.RESET}" if count >= target else f"{_C.YELLOW}LOW {_C.RESET}"
                lines.append(f"  {status}  {rule.rule_name}: {count} (target: {target}+)")
            continue

        # Four U's get special formatting
        if cat_score.category == Category.FOUR_US:
            for rule in cat_score.rules:
                meta = rule.metadata
                if meta.get("skipped"):
                    lines.append(f"  {_C.DIM}SKIP  {meta.get('reason', 'LLM unavailable')}{_C.RESET}")
                    continue
                for dim in ["unique", "useful", "ultra_specific", "urgent"]:
                    dim_data = meta.get(dim, {})
                    score = dim_data.get("score", 0)
                    evidence = dim_data.get("evidence", "")
                    display = dim.replace("_", "-").title()
                    bar = f"{'#' * score}{'.' * (4 - score)}"
                    lines.append(f"  {display:<16} {score}/4  [{bar}]  {_C.DIM}{evidence[:60]}{_C.RESET}")
                total = meta.get("total", 0)
                lines.append(f"  {_C.BOLD}Total: {total}/16{_C.RESET}")
            continue

        # Standard rule display
        for rule in cat_score.rules:
            label = _severity_label(rule.passed)
            status_line = f"{label}  {rule.rule_id}  {rule.rule_name}"
            if rule.passed:
                # Add metadata highlights for passing rules
                if "avg_sentence_length" in rule.metadata:
                    status_line += f" (avg {rule.metadata['avg_sentence_length']} words)"
                elif "active_pct" in rule.metadata:
                    status_line += f" ({rule.metadata['active_pct']}% active)"
                elif "grade_level" in rule.metadata:
                    status_line += f" (grade {rule.metadata['grade_level']})"
                lines.append(status_line)
            else:
                count = len(rule.violations)
                lines.append(f"{status_line} ({count} violation{'s' if count != 1 else ''})")
                # Show first 3 violations
                for v in rule.violations[:3]:
                    line_ref = f"L{v.line}" if v.line > 0 else ""
                    lines.append(f"        {_C.DIM}{line_ref}: {v.text}{_C.RESET}")
                    lines.append(f"        {_C.CYAN}FIX: {v.fix}{_C.RESET}")
                if count > 3:
                    lines.append(f"        {_C.DIM}... and {count - 3} more{_C.RESET}")

    # Top fixes
    fixes = report.top_fixes
    if fixes:
        lines.append(f"\n{_C.BOLD}{'=' * w}{_C.RESET}")
        lines.append(f"{_C.BOLD}TOP {len(fixes)} FIXES (highest impact){_C.RESET}")
        lines.append(f"{_C.BOLD}{'=' * w}{_C.RESET}")
        for i, fix in enumerate(fixes, 1):
            v = fix["first_violation"]
            impact = fix["impact"]
            line_ref = f"[L{v['line']}] " if v.get("line", 0) > 0 else ""
            lines.append(f"{i}. {line_ref}{fix['suggestion']} (+{impact:.0f} pts)")

    lines.append("")
    return "\n".join(lines)
