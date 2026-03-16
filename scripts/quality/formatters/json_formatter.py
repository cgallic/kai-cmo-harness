"""
Content Quality Scorer — JSON output formatter.
"""

import json

from scripts.quality.types import QualityReport


def format_json(report: QualityReport, indent: int = 2) -> str:
    """Format a QualityReport as JSON."""
    return json.dumps(report.to_dict(), indent=indent, ensure_ascii=False)
