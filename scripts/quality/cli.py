"""
Content Quality Scorer — CLI interface.

Usage:
    python -m scripts.quality score path/to/content.md
    python -m scripts.quality score path/to/content.md --rules aa,geo
    python -m scripts.quality score path/to/content.md --no-llm
    python -m scripts.quality score path/to/content.md --format json
    python -m scripts.quality score path/to/content.md -o report.md
    python -m scripts.quality score path/to/content.md --min-score 70
    python -m scripts.quality batch path/to/dir/ --recursive
    python -m scripts.quality gate path/to/content.md --policy blog-publish
    python -m scripts.quality gate --list
    python -m scripts.quality gate --approve gp-abc12345
    python -m scripts.quality rules
    python -m scripts.quality explain AA-01
"""

import argparse
import asyncio
import sys
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(
        description="Content Quality Scorer — ESLint for marketing copy",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m scripts.quality score article.md              Score a file
  python -m scripts.quality score article.md --no-llm     Skip LLM rules
  python -m scripts.quality score article.md --format json JSON output
  python -m scripts.quality batch docs/ --recursive        Score all .md files
  python -m scripts.quality gate article.md --policy blog  Score + gate decision
  python -m scripts.quality gate --list                    Pending proposals
  python -m scripts.quality gate --approve gp-abc12345     Approve a proposal
  python -m scripts.quality rules                          List all rules
  python -m scripts.quality explain AA-01                  Explain a rule
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # score command
    score_parser = subparsers.add_parser("score", help="Score a single file")
    score_parser.add_argument("file", help="Path to markdown file")
    score_parser.add_argument(
        "--rules", type=str, default=None,
        help="Comma-separated rule sets: aa,geo,structure,four_us"
    )
    score_parser.add_argument(
        "--no-llm", action="store_true",
        help="Skip LLM-based rules (Four U's)"
    )
    score_parser.add_argument(
        "--format", choices=["terminal", "json", "markdown"], default="terminal",
        help="Output format (default: terminal)"
    )
    score_parser.add_argument(
        "-o", "--output", type=str, default=None,
        help="Save report to file"
    )
    score_parser.add_argument(
        "--min-score", type=int, default=None,
        help="CI gate: exit code 1 if score below this threshold"
    )
    score_parser.add_argument(
        "--model", type=str, default=None,
        help="LLM model for Four U's scoring (default: qwen-plus)"
    )

    # batch command
    batch_parser = subparsers.add_parser("batch", help="Score all .md files in a directory")
    batch_parser.add_argument("directory", help="Path to directory")
    batch_parser.add_argument(
        "--recursive", "-r", action="store_true",
        help="Search subdirectories"
    )
    batch_parser.add_argument(
        "--no-llm", action="store_true",
        help="Skip LLM-based rules"
    )
    batch_parser.add_argument(
        "--format", choices=["terminal", "json"], default="terminal",
        help="Output format"
    )
    batch_parser.add_argument(
        "--min-score", type=int, default=None,
        help="CI gate: exit code 1 if any file below threshold"
    )

    # gate command
    gate_parser = subparsers.add_parser("gate", help="Score + gate decision (approve/hold/reject)")
    gate_parser.add_argument("file", nargs="?", default=None, help="Path to markdown file")
    gate_parser.add_argument(
        "--policy", type=str, default="default",
        help="Policy name (default, blog-publish, linkedin-article, cold-email)"
    )
    gate_parser.add_argument(
        "--no-llm", action="store_true",
        help="Skip LLM-based rules"
    )
    gate_parser.add_argument(
        "--list", action="store_true", dest="list_pending",
        help="List pending proposals"
    )
    gate_parser.add_argument(
        "--history", action="store_true",
        help="Show recent proposal history"
    )
    gate_parser.add_argument(
        "--approve", type=str, default=None, metavar="ID",
        help="Approve a pending proposal"
    )
    gate_parser.add_argument(
        "--reject", type=str, default=None, metavar="ID",
        help="Reject a pending proposal"
    )
    gate_parser.add_argument(
        "--reason", type=str, default="",
        help="Reason for rejection (used with --reject)"
    )

    # rules command
    subparsers.add_parser("rules", help="List all available rules")

    # explain command
    explain_parser = subparsers.add_parser("explain", help="Explain a specific rule")
    explain_parser.add_argument("rule_id", help="Rule ID (e.g., AA-01, GEO-01, CS-01)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "score": cmd_score,
        "batch": cmd_batch,
        "gate": cmd_gate,
        "rules": cmd_rules,
        "explain": cmd_explain,
    }

    if args.command in commands:
        exit_code = asyncio.run(commands[args.command](args))
        if exit_code:
            sys.exit(exit_code)


async def cmd_score(args) -> int:
    """Score a single file."""
    from scripts.quality.engine import QualityEngine
    from scripts.quality.formatters.terminal import format_terminal
    from scripts.quality.formatters.json_formatter import format_json
    from scripts.quality.formatters.markdown_formatter import format_markdown

    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    rule_sets = args.rules.split(",") if args.rules else None
    engine = QualityEngine(
        rule_sets=rule_sets,
        llm_model=args.model,
        use_llm=not args.no_llm,
    )

    report = await engine.score(str(path))

    # Format output
    formatters = {
        "terminal": format_terminal,
        "json": format_json,
        "markdown": format_markdown,
    }
    output = formatters[args.format](report)

    # Write to file or stdout
    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
        print(f"Report saved to {args.output}")
    else:
        print(output)

    # CI gate
    if args.min_score is not None and report.overall_score < args.min_score:
        print(
            f"\nCI GATE FAILED: Score {report.overall_score:.0f} < minimum {args.min_score}",
            file=sys.stderr,
        )
        return 1

    return 0


async def cmd_batch(args) -> int:
    """Score all .md files in a directory."""
    from scripts.quality.engine import QualityEngine
    from scripts.quality.formatters.terminal import format_terminal
    from scripts.quality.formatters.json_formatter import format_json

    directory = Path(args.directory)
    if not directory.is_dir():
        print(f"Error: Not a directory: {directory}", file=sys.stderr)
        return 1

    pattern = "**/*.md" if args.recursive else "*.md"
    files = sorted(directory.glob(pattern))

    if not files:
        print(f"No .md files found in {directory}")
        return 0

    engine = QualityEngine(use_llm=not args.no_llm)

    print(f"Scoring {len(files)} files...\n")

    results = []
    any_failed = False

    for path in files:
        try:
            report = await engine.score(str(path))
            results.append(report)

            grade_color = {
                "A": "\033[92m", "B": "\033[94m", "C": "\033[93m",
                "D": "\033[95m", "F": "\033[91m",
            }.get(report.overall_grade, "")
            reset = "\033[0m"
            print(
                f"  {grade_color}{report.overall_score:5.0f}{reset}  "
                f"{report.overall_grade}  {path}"
            )

            if args.min_score and report.overall_score < args.min_score:
                any_failed = True

        except Exception as e:
            print(f"  ERROR  {path}: {e}", file=sys.stderr)

    # Summary
    if results:
        avg = sum(r.overall_score for r in results) / len(results)
        best = max(results, key=lambda r: r.overall_score)
        worst = min(results, key=lambda r: r.overall_score)
        print(f"\n{'=' * 60}")
        print(f"Files scored: {len(results)}")
        print(f"Average score: {avg:.0f}/100")
        print(f"Best:  {best.overall_score:.0f} — {best.file_path}")
        print(f"Worst: {worst.overall_score:.0f} — {worst.file_path}")

    if args.min_score and any_failed:
        print(f"\nCI GATE FAILED: Some files scored below {args.min_score}", file=sys.stderr)
        return 1

    return 0


async def cmd_gate(args) -> int:
    """Score + gate decision, or manage proposals."""
    from scripts.quality.gate import propose, approve, reject, list_proposals
    import time

    # Approve a proposal
    if args.approve:
        result = approve(args.approve)
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1
        print(f"Approved: {result['proposal_id']}")
        return 0

    # Reject a proposal
    if args.reject:
        result = reject(args.reject, reason=args.reason)
        if "error" in result:
            print(f"Error: {result['error']}", file=sys.stderr)
            return 1
        print(f"Rejected: {result['proposal_id']}" + (f" ({args.reason})" if args.reason else ""))
        return 0

    # List proposals
    if args.list_pending or args.history:
        status = "all" if args.history else "pending"
        proposals = list_proposals(status=status)
        if not proposals:
            print("No proposals found.")
            return 0

        print(f"\n{'=' * 72}")
        label = "Recent History" if args.history else "Pending Proposals"
        print(f"  {label} ({len(proposals)} total)")
        print(f"{'=' * 72}\n")

        status_colors = {
            "approved": "\033[92m",
            "pending": "\033[93m",
            "rejected": "\033[91m",
        }
        reset = "\033[0m"

        for p in proposals:
            color = status_colors.get(p["status"], "")
            age = time.time() - p["created_at"]
            if age < 3600:
                age_str = f"{age / 60:.0f}m ago"
            elif age < 86400:
                age_str = f"{age / 3600:.0f}h ago"
            else:
                age_str = f"{age / 86400:.0f}d ago"

            print(
                f"  {p['id']}  {color}{p['status']:<10}{reset}  "
                f"{p['score']:5.0f} ({p['grade']})  "
                f"{p['policy']:<16}  {age_str:<8}  {p['file_path']}"
            )
            if p.get("decision_reason"):
                print(f"             {reset}\033[2m{p['decision_reason']}\033[0m")

        print()
        return 0

    # Score + propose
    if not args.file:
        print("Error: provide a file to gate, or use --list/--approve/--reject", file=sys.stderr)
        return 1

    path = Path(args.file)
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        return 1

    content = path.read_text(encoding="utf-8")
    result = await propose(
        content=content,
        file_path=str(path),
        policy_name=args.policy,
        engine_kwargs={"use_llm": not args.no_llm},
    )

    # Display result
    status_colors = {
        "approved": "\033[92m",
        "pending": "\033[93m",
        "rejected": "\033[91m",
    }
    reset = "\033[0m"
    color = status_colors.get(result["status"], "")

    print(f"\n{'=' * 60}")
    print(f"  Gate Decision: {color}{result['status'].upper()}{reset}")
    print(f"  Score: {result['score']:.0f}/100 ({result['grade']})")
    print(f"  Policy: {result['policy']}")
    print(f"  Reason: {result['reason']}")
    print(f"  Proposal: {result['proposal_id']}")
    print(f"  Violations: {result['violation_count']}")
    print(f"{'=' * 60}")

    if result["status"] == "pending":
        print(f"\n  To approve:  python -m scripts.quality gate --approve {result['proposal_id']}")
        print(f"  To reject:   python -m scripts.quality gate --reject {result['proposal_id']} --reason \"...\"")

    if result["top_fixes"]:
        print(f"\n  Top fixes:")
        for i, fix in enumerate(result["top_fixes"][:3], 1):
            print(f"    {i}. {fix['suggestion']} (+{fix['impact']:.0f} pts)")

    print()

    if result["status"] == "rejected":
        return 1
    return 0


async def cmd_rules(args) -> int:
    """List all available rules."""
    from scripts.quality.rules import get_all_rules

    # Import rule modules to trigger registration
    _import_rules()

    rules = get_all_rules()
    current_cat = None

    print(f"\n{'=' * 70}")
    print(f"Content Quality Scorer — All Rules ({len(rules)} total)")
    print(f"{'=' * 70}\n")

    for rule_cls in sorted(rules, key=lambda r: (r.CATEGORY.value, r.RULE_ID)):
        if rule_cls.CATEGORY != current_cat:
            current_cat = rule_cls.CATEGORY
            print(f"\n  {current_cat.value.upper()}")
            print(f"  {'-' * 40}")

        llm = " [LLM]" if hasattr(rule_cls, '_requires_llm') and rule_cls._requires_llm else ""
        print(f"  {rule_cls.RULE_ID:<8} {rule_cls.RULE_NAME:<35} {rule_cls.SEVERITY.value}{llm}")

    print()
    return 0


async def cmd_explain(args) -> int:
    """Explain a specific rule with examples."""
    from scripts.quality.rules import get_rule_by_id

    # Import rule modules to trigger registration
    _import_rules()

    rule_cls = get_rule_by_id(args.rule_id.upper())
    if not rule_cls:
        print(f"Error: Unknown rule ID: {args.rule_id}", file=sys.stderr)
        print("Run 'python -m scripts.quality rules' to see all available rules.")
        return 1

    print(f"\n{'=' * 60}")
    print(f"Rule: {rule_cls.RULE_ID} — {rule_cls.RULE_NAME}")
    print(f"{'=' * 60}")
    print(f"Category:    {rule_cls.CATEGORY.value}")
    print(f"Severity:    {rule_cls.SEVERITY.value}")
    print(f"Description: {rule_cls.DESCRIPTION}")

    if hasattr(rule_cls, '_requires_llm') and rule_cls._requires_llm:
        print(f"Requires:    LLM (OPENROUTER_API_KEY)")

    # Show the docstring if it has more detail
    if rule_cls.__doc__:
        print(f"\n{rule_cls.__doc__.strip()}")

    print()
    return 0


def _import_rules():
    """Import all rule modules to trigger @register decorators."""
    import scripts.quality.rules.algorithmic_authorship  # noqa
    import scripts.quality.rules.geo_signals  # noqa
    import scripts.quality.rules.content_structure  # noqa
    import scripts.quality.rules.four_us  # noqa


if __name__ == "__main__":
    main()
