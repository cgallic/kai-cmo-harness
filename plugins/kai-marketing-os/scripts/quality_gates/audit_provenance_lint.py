#!/usr/bin/env python3
"""
Audit Provenance Linter - Kai Harness Quality Gate

Checks audit markdown/HTML for risky numeric claims that lack nearby source
markers. Also enforces required data-source files for audit directories.

Usage:
  python scripts/quality_gates/audit_provenance_lint.py workspace/marketing-audit --audit-dir
  python scripts/quality_gates/audit_provenance_lint.py report.md deck.html
  python scripts/quality_gates/audit_provenance_lint.py report.md --json

Exit codes:
  0 pass
  1 provenance issues found
  2 input error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


AUDIT_EXTENSIONS = {".md", ".markdown", ".html", ".htm"}

REQUIRED_AUDIT_FILES = {
    "_data-sources.md",
    "_data-gaps.md",
}

RISKY_METRIC_PATTERN = re.compile(
    r"\b("
    r"review(?:s)?|rating|rank(?:s|ing)?|position|keyword(?:s)?|traffic|clicks?|ctr|"
    r"conversion(?:s| rate)?|leads?|calls?|missed calls?|"
    r"domain rating|dr|backlinks?|referring domains?|organic keywords?|"
    r"pagespeed|core web vitals|cwv|lcp|inp|cls|fid|"
    r"gbp|google business profile|local pack|google maps|map pack|"
    r"ai overview(?:s)?|aio|schema|indexed pages?"
    r")\b",
    re.IGNORECASE,
)

RISKY_NUMBER_PATTERN = re.compile(
    r"(?:"
    r"#\s*\d+\b|"
    r"\btop\s+\d+\b|"
    r"\b\d+(?:[,.]\d+)?\s?(?:%|x|ms|s|sec|seconds|pages?|reviews?|stars?|keywords?|links?|calls?|leads?|domains?)\b|"
    r"\b(?:review count|rating|rank|position|traffic|clicks|ctr|conversion|calls|leads|domain rating|dr|backlinks|referring domains|organic keywords|lcp|inp|cls|fid)\b.{0,24}\b\d+(?:[,.]\d+)?\b"
    r")",
    re.IGNORECASE,
)

SOURCE_MARKER_PATTERN = re.compile(
    r"("
    r"\bsource(?:s)?\s*:|"
    r"\bretrieved(?: at| on)?\s*:|"
    r"\bobserved(?: at| on)?\s*:|"
    r"\bchecked(?: at| on)?\s*:|"
    r"\bevidence\s*:|"
    r"\bartifact\s*:|"
    r"\bsource_tier\s*:|"
    r"\bsource_url\s*:|"
    r"data-source\s*=|"
    r"href\s*=|"
    r"https?://|"
    r"\[source[^\]]*\]"
    r")",
    re.IGNORECASE,
)

FORBIDDEN_UNVERIFIED_PATTERNS = [
    re.compile(r"\beducated guess\b", re.IGNORECASE),
    re.compile(r"\bbest guess\b", re.IGNORECASE),
    re.compile(r"\b(?:i|we|claude)\s+guessed\b", re.IGNORECASE),
    re.compile(r"\bprobably ranks?\b", re.IGNORECASE),
    re.compile(r"\blikely ranks?\b", re.IGNORECASE),
    re.compile(r"\bappears to rank\b", re.IGNORECASE),
    re.compile(r"\bno actual (?:hrefs|ahrefs|gsc|ga4|gbp|pagespeed|data)\b", re.IGNORECASE),
]


@dataclass
class Issue:
    file: str
    line: int
    code: str
    message: str
    text: str

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "code": self.code,
            "message": self.message,
            "text": self.text,
        }


def iter_audit_files(paths: Iterable[Path], audit_dir: bool) -> tuple[list[Path], list[Issue]]:
    files: list[Path] = []
    issues: list[Issue] = []

    for path in paths:
        if not path.exists():
            issues.append(Issue(str(path), 0, "INPUT_MISSING", "Path does not exist.", ""))
            continue

        if path.is_dir():
            if audit_dir:
                present = {p.name for p in path.iterdir() if p.is_file()}
                for required in sorted(REQUIRED_AUDIT_FILES - present):
                    issues.append(
                        Issue(
                            str(path / required),
                            0,
                            "MISSING_AUDIT_FILE",
                            f"Audit directory must include {required}.",
                            "",
                        )
                    )
            files.extend(
                p
                for p in path.rglob("*")
                if p.is_file()
                and p.suffix.lower() in AUDIT_EXTENSIONS
                and ".git" not in p.parts
                and "__pycache__" not in p.parts
            )
        elif path.suffix.lower() in AUDIT_EXTENSIONS:
            files.append(path)

    return sorted(set(files)), issues


def has_source_marker(lines: list[str], index: int) -> bool:
    start = max(0, index - 2)
    end = min(len(lines), index + 2)
    context = "\n".join(lines[start:end])
    return bool(SOURCE_MARKER_PATTERN.search(context))


def is_policy_language(line: str) -> bool:
    lowered = line.lower()
    return (
        "not acceptable" in lowered
        or "do not" in lowered
        or "never " in lowered
        or "failure this prevents" in lowered
    )


def lint_text(path: Path, text: str) -> list[Issue]:
    issues: list[Issue] = []
    lines = text.splitlines()
    in_fence = False

    for i, line in enumerate(lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        if not stripped:
            continue

        for pattern in FORBIDDEN_UNVERIFIED_PATTERNS:
            if pattern.search(stripped) and not is_policy_language(stripped):
                issues.append(
                    Issue(
                        str(path),
                        i + 1,
                        "UNVERIFIED_LANGUAGE",
                        "Client-facing audits cannot include guessed or unverifiable claim language.",
                        stripped,
                    )
                )
                break

        if (
            RISKY_METRIC_PATTERN.search(stripped)
            and RISKY_NUMBER_PATTERN.search(stripped)
            and not has_source_marker(lines, i)
        ):
            issues.append(
                Issue(
                    str(path),
                    i + 1,
                    "UNSOURCED_NUMERIC_CLAIM",
                    "Risky audit metric has a number but no nearby source marker.",
                    stripped,
                )
            )

    return issues


def format_text(issues: list[Issue]) -> str:
    if not issues:
        return "Audit Provenance Gate: PASS\n"

    out = ["Audit Provenance Gate: FAIL", "-" * 60]
    for issue in issues:
        location = issue.file
        if issue.line:
            location = f"{location}:{issue.line}"
        out.append(f"[{issue.code}] {location}")
        out.append(f"  {issue.message}")
        if issue.text:
            out.append(f"  {issue.text}")
    out.append("")
    out.append("Fix by adding source, retrieved date, and artifact details, or move the claim to _data-gaps.md.")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit provenance quality gate")
    parser.add_argument("paths", nargs="+", help="Audit files or directories to check")
    parser.add_argument("--audit-dir", action="store_true", help="Require _data-sources.md and _data-gaps.md in directories")
    parser.add_argument("--json", action="store_true", help="Output JSON")
    args = parser.parse_args()

    files, issues = iter_audit_files([Path(p) for p in args.paths], args.audit_dir)

    if not files and not issues:
        issues.append(Issue("", 0, "NO_INPUT_FILES", "No markdown or HTML files found to lint.", ""))

    for file_path in files:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            issues.append(Issue(str(file_path), 0, "READ_ERROR", str(exc), ""))
            continue
        issues.extend(lint_text(file_path, text))

    if args.json:
        print(json.dumps({"passed": not issues, "issues": [i.to_dict() for i in issues]}, indent=2))
    else:
        print(format_text(issues))

    if any(i.code in {"INPUT_MISSING", "NO_INPUT_FILES", "READ_ERROR"} for i in issues):
        return 2
    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
