"""CLI for the homepage AutoReason CRO loop.

Usage:
    python -m scripts.cro.autoreason_homepage.run --use-fixture --dry-run
    python -m scripts.cro.autoreason_homepage.run                            # live
    python -m scripts.cro.autoreason_homepage.run --wiki-out /path/to/page.md
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(REPO_ROOT / ".env")

from . import knowledge  # noqa: E402
from .loop import run_loop  # noqa: E402
from .trace import format_report, trace_to_json  # noqa: E402


WIKI_DIR = Path("/home/connor/brain/wiki/topics")


def _wiki_frontmatter(slug: str, source_label: str) -> str:
    today = date.today().isoformat()
    return (
        "---\n"
        f"title: KaiCalls homepage — AutoReason CRO tournament\n"
        "type: topic\n"
        f"slug: {slug}\n"
        "status: active\n"
        "confidence: medium\n"
        f"created: {today}\n"
        f"updated: {today}\n"
        'related: ["kaicalls", "kaicalls-intelligent-business-number-prd", "autoreason"]\n'
        "source_events: []\n"
        f"# tournament source: {source_label}\n"
        "---\n\n"
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AutoReason CRO loop — KaiCalls homepage zone tournament"
    )
    parser.add_argument("--use-fixture", action="store_true",
                        help="Use the slop fixture instead of the live homepage zones.")
    parser.add_argument("--max-passes", type=int, default=5,
                        help="Hard cap on tournament passes (paper avg 3.9).")
    parser.add_argument("--rng-seed", type=int, default=None,
                        help="Optional RNG seed for label-shuffling reproducibility.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Don't write to wiki — print the report to stdout instead.")
    parser.add_argument("--json-out", default=None,
                        help="Optional path to write the full per-pass trace JSON.")
    parser.add_argument("--wiki-out", default=None,
                        help="Override the default wiki output path "
                             "(default: wiki/topics/kaicalls-homepage-cro-<date>.md).")
    args = parser.parse_args()

    bundle = knowledge.fixture_bundle() if args.use_fixture else knowledge.live_bundle()

    print(f"\nAutoReason CRO loop — {bundle['source_label']}")
    print(f"  Incumbent hero:  {bundle['incumbent'].hero_headline}")
    print(f"  Incumbent CTA:   {bundle['incumbent'].primary_cta}")
    print()

    def _on_pass(p):
        print(f"  pass {p.pass_index}: borda={p.borda_by_role}  winner={p.winner_role}")

    winner, passes, reason = run_loop(
        incumbent=bundle["incumbent"],
        context=bundle["context"],
        max_passes=args.max_passes,
        rng_seed=args.rng_seed,
        on_pass_end=_on_pass,
    )

    print(f"\n{reason}")
    print("\nFinal winner:")
    print(json.dumps(winner.to_dict(), indent=2))

    report = format_report(
        passes=passes,
        winner=winner,
        converged_reason=reason,
        source_label=bundle["source_label"],
    )

    if args.json_out:
        Path(args.json_out).write_text(trace_to_json(passes))
        print(f"\nFull trace JSON: {args.json_out}")

    if args.dry_run:
        print("\n[DRY RUN — report that WOULD write to wiki]:\n")
        print(report)
        return 0

    today = date.today().isoformat()
    slug_stem = f"kaicalls-homepage-cro-autoreason-{today}"
    if args.wiki_out:
        out_path = Path(args.wiki_out)
    else:
        out_path = WIKI_DIR / f"{slug_stem}.md"

    fm = _wiki_frontmatter(slug_stem, bundle["source_label"])
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(fm + report + "\n")
    print(f"\n  ✓ Report written to {out_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
