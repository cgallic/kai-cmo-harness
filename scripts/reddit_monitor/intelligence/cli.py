from __future__ import annotations

import argparse
import json
from pathlib import Path

from .pipeline import run_pipeline
from .profiles import load_profile
from .sources import collect_reddit_rss


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Read-only Reddit intelligence pipeline")
    parser.add_argument("--profile", required=True, help="Path to a JSON profile")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--input", help="JSON array or JSONL export from an approved read-only source")
    source.add_argument("--collect", action="store_true", help="Collect the profile's approved public Reddit RSS sources")
    parser.add_argument("--output-dir", required=True)
    parser.add_argument("--activate-sheets", action="store_true")
    parser.add_argument("--activate-email", action="store_true")
    args = parser.parse_args(argv)
    profile = load_profile(args.profile)
    if args.collect:
        items = collect_reddit_rss(profile)
    else:
        input_path = Path(args.input)
        if input_path.suffix.casefold() == ".jsonl":
            items = [json.loads(line) for line in input_path.read_text(encoding="utf-8").splitlines() if line.strip()]
        else:
            items = json.loads(input_path.read_text(encoding="utf-8"))
    result = run_pipeline(items, profile, args.output_dir,
                          activate_sheets=args.activate_sheets, activate_email=args.activate_email)
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
