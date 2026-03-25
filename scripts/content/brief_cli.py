"""
Brief Generator CLI — Thin wrapper for skill invocation.

Usage:
    python brief_cli.py --format blog --site kaicalls --keyword "AI receptionists"
    python brief_cli.py --format blog --site kaicalls --keyword "AI" --output json
"""

import argparse
import json
import sys
from pathlib import Path

# Add project root to path
_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Generate a content brief")
    parser.add_argument("--format", "-f", required=True, help="Content format (blog, seo, meta-ads, etc.)")
    parser.add_argument("--site", "-s", required=True, help="Site key (e.g., kaicalls)")
    parser.add_argument("--keyword", "-k", required=True, help="Target keyword")
    parser.add_argument("--output", "-o", choices=["json", "text"], default="json", help="Output format")
    args = parser.parse_args()

    try:
        import asyncio
        from scripts.content.brief_generator import generate_brief
    except ImportError as e:
        print(json.dumps({"error": f"Import failed: {e}. Run: pip install -r scripts/requirements.txt"}))
        sys.exit(1)

    try:
        brief = asyncio.run(generate_brief(args.format, args.site, args.keyword))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

    if args.output == "json":
        print(json.dumps(brief, indent=2, default=str))
    else:
        for key, val in brief.items():
            print(f"{key}: {val}")


if __name__ == "__main__":
    main()
