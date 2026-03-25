"""
A/B Test CLI — Create tests, record results, analyze significance.

Usage:
    python ab_cli.py create "headline-test" --variants "pain-hook,data-hook,social-hook"
    python ab_cli.py record ab-1234abcd --variant pain-hook --impressions 1000 --clicks 45 --conversions 8
    python ab_cli.py analyze ab-1234abcd
    python ab_cli.py list
    python ab_cli.py list --status running
"""

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))


def main():
    parser = argparse.ArgumentParser(description="A/B Test Tracker")
    subparsers = parser.add_subparsers(dest="command")

    # create
    create_p = subparsers.add_parser("create", help="Create a new A/B test")
    create_p.add_argument("name", help="Test name")
    create_p.add_argument("--variants", "-v", required=True, help="Comma-separated variant names")
    create_p.add_argument("--metric", "-m", default="cvr", choices=["ctr", "cvr", "roas", "cpa"], help="Primary metric")

    # record
    record_p = subparsers.add_parser("record", help="Record results for a variant")
    record_p.add_argument("test_id", help="Test ID (ab-xxxxxxxx)")
    record_p.add_argument("--variant", required=True, help="Variant name")
    record_p.add_argument("--impressions", type=int, default=0)
    record_p.add_argument("--clicks", type=int, default=0)
    record_p.add_argument("--conversions", type=int, default=0)
    record_p.add_argument("--revenue", type=float, default=0.0)
    record_p.add_argument("--spend", type=float, default=0.0)
    record_p.add_argument("--source", default="manual", help="Data source (manual, meta, google, etc.)")

    # analyze
    analyze_p = subparsers.add_parser("analyze", help="Analyze a test for significance")
    analyze_p.add_argument("test_id", help="Test ID")
    analyze_p.add_argument("--format", choices=["text", "json"], default="text")

    # list
    list_p = subparsers.add_parser("list", help="List all tests")
    list_p.add_argument("--status", help="Filter by status")
    list_p.add_argument("--format", choices=["text", "json"], default="text")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    from scripts.content.ab_tracker import ABTracker

    tracker = ABTracker()

    if args.command == "create":
        variants = [v.strip() for v in args.variants.split(",")]
        test_id = tracker.create_test(args.name, variants, metric=args.metric)
        print(json.dumps({"test_id": test_id, "name": args.name, "variants": variants, "metric": args.metric}))

    elif args.command == "record":
        tracker.record_result(
            test_id=args.test_id,
            variant=args.variant,
            impressions=args.impressions,
            clicks=args.clicks,
            conversions=args.conversions,
            revenue=args.revenue,
            spend=args.spend,
            source=args.source,
        )
        print(json.dumps({"status": "recorded", "test_id": args.test_id, "variant": args.variant}))

    elif args.command == "analyze":
        report = tracker.analyze(args.test_id)
        if args.format == "json":
            print(json.dumps({
                "test_id": report.test_id,
                "name": report.test_name,
                "metric": report.metric,
                "status": report.status,
                "winner": report.winner,
                "confidence": report.confidence,
                "significant": report.significant,
                "sample_needed": report.sample_needed,
                "recommendation": report.recommendation,
                "variants": [
                    {"variant": v.variant, "impressions": v.impressions, "clicks": v.clicks,
                     "conversions": v.conversions, "ctr": v.ctr, "cvr": v.cvr}
                    for v in report.variants
                ],
            }, indent=2))
        else:
            print(tracker.format_report(report))

    elif args.command == "list":
        tests = tracker.list_tests(status=args.status)
        if args.format == "json":
            print(json.dumps(tests, indent=2, default=str))
        else:
            if not tests:
                print("No A/B tests found.")
            else:
                print(f"{'Test ID':<16} {'Name':<25} {'Status':<15} {'Winner':<15} {'Confidence':>10}")
                print("-" * 85)
                for t in tests:
                    print(f"{t['test_id']:<16} {t['name']:<25} {t['status']:<15} {t.get('winner') or '-':<15} {t.get('confidence', 0):>9.1%}")


if __name__ == "__main__":
    main()
