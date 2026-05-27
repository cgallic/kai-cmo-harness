#!/usr/bin/env python3
"""
Mutation-risk linter for Kai artifacts.

Flags output that appears to send, upload, enroll, activate, publish, or change
spend without nearby approval/dry-run language.

Exit codes:
  0 pass
  1 mutation risk issues found
  2 input error
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


TEXT_EXTENSIONS = {".md", ".markdown", ".txt", ".html", ".htm", ".json", ".yaml", ".yml"}

MUTATION_PATTERNS = [
    re.compile(r"\b(?:send|sent|sending)\s+(?:the\s+)?(?:email|sequence|campaign|message|sms|dm)s?\b", re.IGNORECASE),
    re.compile(r"\b(?:upload|import|push|sync)\s+(?:contacts?|leads?|audiences?|records?)\b", re.IGNORECASE),
    re.compile(
        r"\b(?:enroll|add)\s+(?:contacts?|leads?|prospects?|records?|people|users?|visitors?|audience)\b.+\b(?:campaign|sequence|workflow|automation)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:activate|pause|resume|launch)\s+(?:the\s+)?(?:campaign|ad\s*set|ad|sequence|automation)\b", re.IGNORECASE),
    re.compile(r"\b(?:publish|post|schedule)\s+(?:the\s+)?(?:page|post|article|ad|campaign|email|video)\b", re.IGNORECASE),
    re.compile(r"\b(?:increase|decrease|change|set)\s+(?:daily\s+)?(?:budget|spend|bid)\b", re.IGNORECASE),
    re.compile(r"\b(?:delete|remove|update|modify)\s+(?:the\s+)?(?:crm|contact|lead|campaign|ad|record|audience)\b", re.IGNORECASE),
]

SAFE_CONTEXT_PATTERN = re.compile(
    r"\b("
    r"approval required|pending approval|approved by|approved links|human approval|"
    r"with approval|without approval|approval-ready|"
    r"dry[- ]run|preview only|do not execute|not yet sent|not live|"
    r"proposal only|requires review|approval_state|approver|"
    r"hold for review|queue for approval"
    r")\b",
    re.IGNORECASE,
)


@dataclass
class Issue:
    file: str
    line: int
    text: str
    message: str

    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "line": self.line,
            "text": self.text,
            "message": self.message,
        }


def iter_files(paths: Iterable[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            raise SystemExit(f"Path does not exist: {path}")
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            files.append(path)
        elif path.is_dir():
            files.extend(
                candidate
                for candidate in path.rglob("*")
                if candidate.is_file()
                and candidate.suffix.lower() in TEXT_EXTENSIONS
                and ".git" not in candidate.parts
                and "__pycache__" not in candidate.parts
            )
    return sorted(set(files))


def has_safe_context(lines: list[str], index: int) -> bool:
    start = max(0, index - 3)
    end = min(len(lines), index + 4)
    context = "\n".join(lines[start:end])
    return bool(SAFE_CONTEXT_PATTERN.search(context))


def lint_file(path: Path) -> list[Issue]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    issues: list[Issue] = []

    for index, line in enumerate(lines):
        if not any(pattern.search(line) for pattern in MUTATION_PATTERNS):
            continue
        if has_safe_context(lines, index):
            continue
        issues.append(
            Issue(
                file=str(path),
                line=index + 1,
                text=line.strip(),
                message="Live-channel or connector mutation appears without nearby approval or dry-run language.",
            )
        )

    return issues


def main() -> int:
    parser = argparse.ArgumentParser(description="Lint Kai artifacts for unapproved mutation risk.")
    parser.add_argument("paths", nargs="+", help="Files or directories to lint.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    files = iter_files([Path(p) for p in args.paths])
    issues: list[Issue] = []
    for path in files:
        issues.extend(lint_file(path))

    payload = {
        "passed": not issues,
        "files_scanned": len(files),
        "issues": [issue.to_dict() for issue in issues],
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        status = "PASS" if payload["passed"] else "FAIL"
        print(f"{status}: mutation-risk lint scanned {len(files)} file(s), found {len(issues)} issue(s).")
        for issue in issues[:50]:
            print(f"{issue.file}:{issue.line}: {issue.message} {issue.text}")
        if len(issues) > 50:
            print(f"... {len(issues) - 50} more issue(s)")

    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
