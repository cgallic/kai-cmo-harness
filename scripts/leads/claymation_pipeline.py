#!/usr/bin/env python3
"""Dry-run local business claymation ad pipeline.

Usage:
  python scripts/leads/claymation_pipeline.py --input leads.csv --output workspace/claymation/dry-run.json --dry-run
  python scripts/leads/claymation_pipeline.py --input leads.json --top 25
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from kai.creative.claymation_pipeline import ClaymationLead, run_dry_run


def read_leads(path: Path) -> List[ClaymationLead]:
    """Read leads from CSV or JSON."""
    if not path.exists():
        raise FileNotFoundError(f"input file not found: {path}")

    if path.suffix.lower() == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = data.get("leads") or data.get("items") or []
        return [ClaymationLead.from_mapping(item) for item in data]

    with path.open("r", newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle)
        return [ClaymationLead.from_mapping(row) for row in reader]


def sample_leads() -> List[ClaymationLead]:
    """Return a safe sample when no input file is provided."""
    return [
        ClaymationLead(
            name="Sample Fitness Studio",
            category="gym",
            city="Austin",
            state="TX",
            rating=4.8,
            reviews=132,
            social_links={"instagram": "https://instagram.com/sample"},
            ad_observations=[
                "No video creative",
                "Generic stock visuals",
                "Weak CTA",
                "No local specificity",
            ],
        )
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the Kai local claymation ad pipeline in dry-run mode.")
    parser.add_argument("--input", type=Path, help="CSV or JSON leads file.")
    parser.add_argument("--output", type=Path, default=Path("workspace/claymation/dry-run.json"))
    parser.add_argument("--top", type=int, default=0, help="Keep only the top N scored leads.")
    parser.add_argument("--sample-url", help="Optional sample video or storyboard URL to include in pitches.")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Always dry-run; kept for explicit CLI use.")
    args = parser.parse_args()

    leads = read_leads(args.input) if args.input else sample_leads()
    result = run_dry_run(leads, sample_url=args.sample_url)

    if args.top and args.top > 0:
        result["items"] = sorted(
            result["items"],
            key=lambda item: item["score"]["score"],
            reverse=True,
        )[:args.top]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(f"Wrote dry-run package for {len(result['items'])} lead(s): {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
