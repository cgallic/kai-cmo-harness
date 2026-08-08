#!/usr/bin/env python3
"""Materialize plugin payloads from their canonical source directories.

The plugin directories under ``plugins/`` used to be git symlinks pointing up
into the repo root (``plugins/kai-marketing-os/skills -> ../../harness/skills``).
That breaks in two ways:

1. On a Windows checkout without ``core.symlinks=true``, git writes the link
   target as a small text file. The plugin then installs with zero skills.
2. Claude Code skips symlinks whose target escapes the marketplace when it
   copies a plugin into ``~/.claude/plugins/cache/``.

So the payloads are committed as real files. Git stores blobs by content hash,
so the duplicated bytes cost effectively nothing in the object database -- but
the working tree can now drift. This script is the reconciler.

Usage::

    python scripts/sync_plugin_assets.py            # copy canonical -> plugins
    python scripts/sync_plugin_assets.py --check    # exit 1 if they differ

``--check`` runs in CI so a change to ``harness/skills/`` that never made it
into ``plugins/`` fails the build instead of shipping a stale plugin.
"""

from __future__ import annotations

import argparse
import filecmp
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Top-level entries inside a canonical directory that must never reach a plugin
# payload, keyed by canonical source. ``docs/superpowers/`` is internal build
# plans and specs -- it names infrastructure hosts and project refs, nothing in
# harness/ or knowledge/ references it, and customers have no use for it.
PAYLOAD_EXCLUDES: dict[str, set[str]] = {
    "docs": {"superpowers"},
}

# (destination inside the repo, canonical source) -- both repo-relative.
ASSET_MAP: list[tuple[str, str]] = [
    # v1 plugin
    ("plugins/kai-marketing-os/skills", "harness/skills"),
    ("plugins/kai-marketing-os/knowledge", "knowledge"),
    ("plugins/kai-marketing-os/docs", "docs"),
    ("plugins/kai-marketing-os/scripts/quality_gates", "scripts/quality_gates"),
    ("plugins/kai-marketing-os/scripts/reddit_monitor", "scripts/reddit_monitor"),
    ("plugins/kai-marketing-os/harness/references", "harness/references"),
    ("plugins/kai-marketing-os/harness/skill-contracts", "harness/skill-contracts"),
    ("plugins/kai-marketing-os/harness/brief-schema.md", "harness/brief-schema.md"),
    ("plugins/kai-marketing-os/harness/eco-floors.yaml", "harness/eco-floors.yaml"),
    # v2 plugin -- same payload except the skills tree, and it borrows v1's agents
    ("plugins/kai-marketing-os-v2/skills", "harness/skills-v2"),
    ("plugins/kai-marketing-os-v2/agents", "plugins/kai-marketing-os/agents"),
    ("plugins/kai-marketing-os-v2/knowledge", "knowledge"),
    ("plugins/kai-marketing-os-v2/docs", "docs"),
    ("plugins/kai-marketing-os-v2/scripts/quality_gates", "scripts/quality_gates"),
    ("plugins/kai-marketing-os-v2/scripts/reddit_monitor", "scripts/reddit_monitor"),
    ("plugins/kai-marketing-os-v2/harness/references", "harness/references"),
    ("plugins/kai-marketing-os-v2/harness/skill-contracts", "harness/skill-contracts"),
    ("plugins/kai-marketing-os-v2/harness/brief-schema.md", "harness/brief-schema.md"),
    ("plugins/kai-marketing-os-v2/harness/eco-floors.yaml", "harness/eco-floors.yaml"),
]

# Never copy these into a plugin payload.
IGNORE = shutil.ignore_patterns(
    "__pycache__", "*.pyc", ".DS_Store", ".git", "*.egg-info",
)


def _diff_tree(src: Path, dst: Path, excludes: set[str]) -> list[str]:
    """Return human-readable differences between two directory trees."""
    problems: list[str] = []
    ignore = [".git", "__pycache__", *excludes]

    def walk(cmp_result: filecmp.dircmp, prefix: str) -> None:
        for name in cmp_result.left_only:
            problems.append(f"missing from plugin: {prefix}{name}")
        for name in cmp_result.right_only:
            problems.append(f"stale in plugin (not in canonical): {prefix}{name}")
        for name in cmp_result.diff_files:
            problems.append(f"content differs: {prefix}{name}")
        for name, sub in cmp_result.subdirs.items():
            walk(sub, f"{prefix}{name}/")

    # Excludes only apply at the top level of the copied tree.
    top = filecmp.dircmp(src, dst, ignore=ignore)
    for name in top.left_only:
        problems.append(f"missing from plugin: {name}")
    for name in top.right_only:
        problems.append(f"stale in plugin (not in canonical): {name}")
    for name in top.diff_files:
        problems.append(f"content differs: {name}")
    for name, sub in top.subdirs.items():
        walk(sub, f"{name}/")
    return problems


def check() -> int:
    problems: list[str] = []
    for dest_rel, src_rel in ASSET_MAP:
        dest, src = REPO_ROOT / dest_rel, REPO_ROOT / src_rel
        if not src.exists():
            problems.append(f"{src_rel}: canonical source is missing")
            continue
        if not dest.exists():
            problems.append(f"{dest_rel}: not materialized (run sync_plugin_assets.py)")
            continue
        if dest.is_symlink():
            problems.append(f"{dest_rel}: is a symlink; plugin payloads must be real files")
            continue
        if src.is_file():
            if not filecmp.cmp(src, dest, shallow=False):
                problems.append(f"{dest_rel}: differs from {src_rel}")
        else:
            excludes = PAYLOAD_EXCLUDES.get(src_rel, set())
            problems.extend(
                f"{dest_rel}: {p}" for p in _diff_tree(src, dest, excludes)
            )

    if problems:
        print("Plugin assets are out of sync with their canonical sources:\n")
        for problem in problems:
            print(f"  - {problem}")
        print("\nRun: python scripts/sync_plugin_assets.py")
        return 1

    print(f"Plugin assets in sync ({len(ASSET_MAP)} entries).")
    return 0


def sync() -> int:
    for dest_rel, src_rel in ASSET_MAP:
        dest, src = REPO_ROOT / dest_rel, REPO_ROOT / src_rel
        if not src.exists():
            print(f"  SKIP {dest_rel} (canonical source {src_rel} is missing)")
            continue

        # A leftover symlink -- or the text file Windows git leaves in its place --
        # has to go before we can write real content.
        if dest.is_symlink() or dest.is_file():
            dest.unlink()
        elif dest.is_dir():
            shutil.rmtree(dest)

        dest.parent.mkdir(parents=True, exist_ok=True)
        if src.is_file():
            shutil.copy2(src, dest)
            print(f"  {dest_rel} <- {src_rel}")
        else:
            excludes = PAYLOAD_EXCLUDES.get(src_rel, set())
            shutil.copytree(
                src,
                dest,
                ignore=lambda d, names: set(IGNORE(d, names))
                | (excludes if Path(d) == src else set()),
            )
            note = f"  (excluding {', '.join(sorted(excludes))})" if excludes else ""
            print(f"  {dest_rel} <- {src_rel}{note}")

    print(f"\nSynced {len(ASSET_MAP)} plugin asset entries.")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Materialize plugin payloads from their canonical source directories."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify plugin payloads match canonical sources; exit 1 on drift",
    )
    args = parser.parse_args()
    return check() if args.check else sync()


if __name__ == "__main__":
    sys.exit(main())
