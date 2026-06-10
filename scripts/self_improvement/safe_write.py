#!/usr/bin/env python3
"""
Safe-write helpers for files the harness rewrites automatically.

Promoted from memory/edge-cases.md EC-11: harness_defaults_update.py rewrote
MARKETING.md and policy YAML with only a .bak backup and no validation — one
bad rewrite breaks every later run. These helpers make automated rewrites
atomic, validated, and refusable.

Stdlib only; YAML validation requires PyYAML (callers already gate on it).
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


def atomic_write_text(path: str | Path, content: str) -> None:
    """Write via a temp file + os.replace so a crash never leaves a partial file."""
    path = Path(path)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    os.replace(tmp, path)


def safe_write_yaml(path: str | Path, data: dict, backup: bool = True) -> tuple[bool, str]:
    """Validate-then-write a YAML file. Returns (ok, message).

    The dumped text is round-tripped through yaml.safe_load before anything
    touches disk; if it doesn't parse back to the same top-level structure,
    the original file is left untouched.
    """
    import yaml

    path = Path(path)
    try:
        dumped = yaml.dump(data, default_flow_style=False, sort_keys=False)
        reloaded = yaml.safe_load(dumped)
    except yaml.YAMLError as exc:
        return False, f"refused write to {path.name}: output is not valid YAML ({exc})"
    if not isinstance(reloaded, type(data)) or reloaded is None:
        return False, f"refused write to {path.name}: YAML round-trip changed structure"

    if backup and path.exists():
        shutil.copy2(path, str(path) + ".bak")
    atomic_write_text(path, dumped)
    return True, f"wrote {path.name}"


def guarded_write_text(
    path: str | Path,
    new_content: str,
    backup: bool = True,
    min_ratio: float = 0.3,
) -> tuple[bool, str]:
    """Rewrite a text file, refusing suspicious truncation. Returns (ok, message).

    Refuses when the new content is empty, lost the file's first heading, or
    shrank below min_ratio of the original — the failure modes of a regex
    rewrite gone wrong.
    """
    path = Path(path)
    if not new_content.strip():
        return False, f"refused write to {path.name}: new content is empty"

    if path.exists():
        original = path.read_text(encoding="utf-8")
        first_line = next((ln for ln in original.splitlines() if ln.strip()), "")
        if first_line and first_line not in new_content:
            return False, (
                f"refused write to {path.name}: first heading "
                f"{first_line[:60]!r} missing from rewritten content"
            )
        if len(original) > 500 and len(new_content) < len(original) * min_ratio:
            return False, (
                f"refused write to {path.name}: content shrank from "
                f"{len(original)} to {len(new_content)} chars (>{1 - min_ratio:.0%} loss)"
            )
        if backup:
            shutil.copy2(path, str(path) + ".bak")

    atomic_write_text(path, new_content)
    return True, f"wrote {path.name}"
