#!/usr/bin/env python3
"""
Kai privacy sanitizer.

Scans files for common secrets, PII, client identifiers, and marketing-system
IDs. By default it reports findings only. Use --sanitize to replace findings
in place with stable placeholders.

Exit codes:
  0 clean
  1 findings detected
  2 input/config error
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_EXTENSIONS = {
    ".csv",
    ".env",
    ".html",
    ".htm",
    ".json",
    ".md",
    ".py",
    ".txt",
    ".yaml",
    ".yml",
}

DEFAULT_SKIP_PARTS = {
    ".git",
    ".pytest_cache",
    ".venv",
    "__pycache__",
    "node_modules",
}

PATTERNS: list[tuple[str, str, str]] = [
    (
        "URL_CREDENTIALS",
        "[URL_CREDENTIALS]",
        r"https?://[^/\s:@]+:[^/\s:@]+@[^/\s]+",
    ),
    (
        "OPENAI_API_KEY",
        "[API_KEY]",
        r"\bsk-[A-Za-z0-9_-]{20,}\b",
    ),
    (
        "GITHUB_TOKEN",
        "[API_KEY]",
        r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
    ),
    (
        "BEARER_TOKEN",
        "[API_KEY]",
        r"\bBearer\s+[A-Za-z0-9._~+/=-]{20,}\b",
    ),
    (
        "SECRET_ASSIGNMENT",
        "[SECRET_ASSIGNMENT]",
        r"(?i)\b(?:api[_-]?key|secret|token|password|private[_-]?key)\s*[=:]\s*['\"]?[A-Za-z0-9._~+/=-]{12,}['\"]?",
    ),
    (
        "EMAIL",
        "[EMAIL]",
        r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b",
    ),
    (
        "PHONE",
        "[PHONE]",
        r"(?<!\d)(?:\+?1[\s.-]?)?(?:\([2-9]\d{2}\)|[2-9]\d{2})[\s.-]?\d{3}[\s.-]?\d{4}(?!\d)",
    ),
    (
        "SSN",
        "[SSN]",
        r"\b\d{3}-\d{2}-\d{4}\b",
    ),
    (
        "IP_ADDRESS",
        "[IP_ADDRESS]",
        r"\b(?!(?:10|127|172\.(?:1[6-9]|2\d|3[0-1])|192\.168)\.)\d{1,3}(?:\.\d{1,3}){3}\b",
    ),
    (
        "AD_ACCOUNT_ID",
        "[AD_ACCOUNT_ID]",
        r"\b(?:act_)?\d{12,20}\b",
    ),
    (
        "GOOGLE_CLIENT_ID",
        "[GOOGLE_CLIENT_ID]",
        r"\b\d{12,}-[A-Za-z0-9_-]{20,}\.apps\.googleusercontent\.com\b",
    ),
]


@dataclass
class Finding:
    path: str
    line: int
    label: str
    match: str
    text: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line": self.line,
            "label": self.label,
            "match": self.match,
            "text": self.text,
        }


def load_config(path: Path | None) -> dict:
    if not path:
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise SystemExit(f"Could not read config: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise SystemExit(f"Invalid JSON config: {exc}") from exc


def compile_patterns(config: dict) -> list[tuple[str, str, re.Pattern[str]]]:
    compiled = [(label, repl, re.compile(pattern)) for label, repl, pattern in PATTERNS]

    for item in config.get("custom_patterns", []):
        if isinstance(item, str):
            compiled.append(("CUSTOM", "[CUSTOM]", re.compile(item)))
        elif isinstance(item, dict) and item.get("pattern"):
            label = str(item.get("label", "CUSTOM"))
            replacement = str(item.get("replacement", f"[{label}]"))
            compiled.append((label, replacement, re.compile(str(item["pattern"]))))

    for name in config.get("client_names", []):
        escaped = re.escape(str(name))
        compiled.append(("CLIENT_NAME", "[CLIENT_NAME]", re.compile(rf"\b{escaped}\b", re.IGNORECASE)))

    for domain in config.get("client_domains", []):
        escaped = re.escape(str(domain))
        compiled.append(("CLIENT_DOMAIN", "[CLIENT_DOMAIN]", re.compile(rf"\b{escaped}\b", re.IGNORECASE)))

    return compiled


def should_skip(path: Path, skip_parts: set[str]) -> bool:
    return any(part in skip_parts for part in path.parts)


def iter_files(paths: Iterable[Path], recursive: bool, config: dict) -> list[Path]:
    extensions = set(config.get("extensions", DEFAULT_EXTENSIONS))
    skip_parts = set(config.get("skip_parts", DEFAULT_SKIP_PARTS))
    files: list[Path] = []

    for path in paths:
        if not path.exists():
            raise SystemExit(f"Path does not exist: {path}")
        if should_skip(path, skip_parts):
            continue
        if path.is_file():
            if path.suffix.lower() in extensions:
                files.append(path)
            continue
        pattern = "**/*" if recursive else "*"
        for candidate in path.glob(pattern):
            if candidate.is_file() and candidate.suffix.lower() in extensions and not should_skip(candidate, skip_parts):
                files.append(candidate)

    return sorted(set(files))


def scan_text(path: Path, text: str, patterns: list[tuple[str, str, re.Pattern[str]]]) -> list[Finding]:
    findings: list[Finding] = []
    for line_no, line in enumerate(text.splitlines(), start=1):
        for label, _replacement, pattern in patterns:
            for match in pattern.finditer(line):
                findings.append(
                    Finding(
                        path=str(path),
                        line=line_no,
                        label=label,
                        match=match.group(0),
                        text=line.strip(),
                    )
                )
    return findings


def sanitize_text(text: str, patterns: list[tuple[str, str, re.Pattern[str]]]) -> str:
    sanitized = text
    for _label, replacement, pattern in patterns:
        sanitized = pattern.sub(replacement, sanitized)
    return sanitized


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="ignore")


def main() -> int:
    parser = argparse.ArgumentParser(description="Scan or sanitize files for Kai privacy risks.")
    parser.add_argument("paths", nargs="+", help="Files or directories to scan.")
    parser.add_argument("--recursive", action="store_true", help="Recurse into directories.")
    parser.add_argument("--sanitize", action="store_true", help="Replace findings in place.")
    parser.add_argument("--config", help="Optional JSON config with custom_patterns, client_names, client_domains.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    args = parser.parse_args()

    config = load_config(Path(args.config)) if args.config else {}
    patterns = compile_patterns(config)
    files = iter_files([Path(p) for p in args.paths], args.recursive, config)

    all_findings: list[Finding] = []
    changed: list[str] = []

    for path in files:
        original = read_text(path)
        findings = scan_text(path, original, patterns)
        all_findings.extend(findings)
        if args.sanitize and findings:
            sanitized = sanitize_text(original, patterns)
            if sanitized != original:
                path.write_text(sanitized, encoding="utf-8")
                changed.append(str(path))

    payload = {
        "passed": not all_findings,
        "files_scanned": len(files),
        "findings": [finding.to_dict() for finding in all_findings],
        "changed": changed,
    }

    if args.json:
        print(json.dumps(payload, indent=2))
    else:
        status = "PASS" if payload["passed"] else "FAIL"
        print(f"{status}: privacy sanitizer scanned {len(files)} file(s), found {len(all_findings)} issue(s).")
        for finding in all_findings[:50]:
            print(f"{finding.path}:{finding.line}: {finding.label}: {finding.text}")
        if len(all_findings) > 50:
            print(f"... {len(all_findings) - 50} more finding(s)")
        if changed:
            print(f"Sanitized {len(changed)} file(s).")

    return 1 if all_findings else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            raise SystemExit(2)
        raise
