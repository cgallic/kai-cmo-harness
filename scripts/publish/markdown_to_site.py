#!/usr/bin/env python3
"""
Kai CMO Harness — Static Site Publisher
=========================================
Write markdown files with frontmatter for Hugo, Jekyll, Astro, or any static site generator.

Usage:
  python scripts/publish/markdown_to_site.py --draft draft.md --output-dir ./content/blog/ --generator hugo
  python scripts/publish/markdown_to_site.py --draft draft.md --output-dir ./_posts/ --generator jekyll
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path


FRONTMATTER_TEMPLATES = {
    "hugo": """\
---
title: "{title}"
date: {date}
draft: {draft}
description: "{description}"
slug: "{slug}"
categories: {categories}
tags: {tags}
---
""",
    "jekyll": """\
---
layout: post
title: "{title}"
date: {date}
description: "{description}"
categories: {categories_str}
tags: {tags_str}
---
""",
    "astro": """\
---
title: "{title}"
pubDate: {date}
description: "{description}"
slug: "{slug}"
tags: {tags}
draft: {draft}
---
""",
    "11ty": """\
---
title: "{title}"
date: {date}
description: "{description}"
tags: {tags}
---
""",
}


def publish(
    title: str = "",
    body: str = "",
    status: str = "draft",
    slug: str = "",
    meta_description: str = "",
    categories: list[str] | None = None,
    tags: list[str] | None = None,
    output_dir: str = "./content/blog",
    generator: str = "hugo",
    **_kwargs,
) -> dict:
    """Write markdown file with frontmatter for static site generators."""
    if not title:
        # Extract from H1
        h1 = re.search(r"^#\s+(.+)$", body, re.MULTILINE)
        title = h1.group(1).strip() if h1 else "Untitled"

    if not slug:
        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

    date = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S+00:00")
    is_draft = status != "publish"
    cats = categories or []
    tag_list = tags or []

    # Strip H1 from body (title is in frontmatter)
    body_clean = re.sub(r"^#\s+.+\n*", "", body, count=1).strip()
    # Strip Meta: line
    body_clean = re.sub(r"^Meta:\s*.+\n*", "", body_clean, count=1).strip()

    template = FRONTMATTER_TEMPLATES.get(generator, FRONTMATTER_TEMPLATES["hugo"])
    frontmatter = template.format(
        title=title.replace('"', '\\"'),
        date=date,
        draft=str(is_draft).lower(),
        description=(meta_description or "").replace('"', '\\"'),
        slug=slug,
        categories=json.dumps(cats),
        tags=json.dumps(tag_list),
        categories_str=" ".join(cats),
        tags_str=" ".join(tag_list),
    )

    content = frontmatter + "\n" + body_clean

    # Determine filename
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    if generator == "jekyll":
        date_prefix = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filename = f"{date_prefix}-{slug}.md"
    else:
        filename = f"{slug}.md"

    out_path = out_dir / filename
    out_path.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "platform": "markdown",
        "id": slug,
        "url": str(out_path),
        "status": "draft" if is_draft else "published",
        "message": f"Written to {out_path}",
    }


def main():
    parser = argparse.ArgumentParser(description="Write markdown with frontmatter for static sites")
    parser.add_argument("--draft", required=True, help="Path to markdown draft")
    parser.add_argument("--output-dir", default="./content/blog", help="Output directory")
    parser.add_argument("--generator", default="hugo", choices=list(FRONTMATTER_TEMPLATES.keys()))
    parser.add_argument("--status", default="draft", choices=["draft", "publish"])
    parser.add_argument("--categories", nargs="*")
    parser.add_argument("--tags", nargs="*")
    parser.add_argument("--slug", help="URL slug")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    content = Path(args.draft).read_text()
    h1 = re.search(r"^#\s+(.+)$", content, re.MULTILINE)
    title = h1.group(1).strip() if h1 else "Untitled"

    meta_match = re.search(r"^Meta:\s*(.+)$", content, re.MULTILINE)
    meta_desc = meta_match.group(1).strip() if meta_match else ""

    result = publish(
        title=title, body=content, status=args.status,
        slug=args.slug, meta_description=meta_desc,
        categories=args.categories, tags=args.tags,
        output_dir=args.output_dir, generator=args.generator,
    )

    if args.json:
        print(json.dumps(result, indent=2))
    else:
        print(result["message"])


if __name__ == "__main__":
    main()
