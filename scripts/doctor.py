#!/usr/bin/env python3
"""
Kai Harness Doctor — preflight self-check for a fresh clone.

Run this first. It verifies the harness's own promises:
  - every file CLAUDE.md tells Claude to load actually exists
  - the deterministic quality gates compile and their golden corpus passes
  - the memory/learning layer is present and writable
  - optional dependencies and credentials are reported with exactly what
    each one unlocks (missing ones are warnings, not failures)

Usage:
  python scripts/doctor.py          # full report
  python scripts/doctor.py --ci     # hard checks only; exit 1 on failure

Stdlib only. Never requires credentials or network.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import py_compile
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# Files CLAUDE.md and the skill docs instruct Claude to load. If one of these
# is missing, the harness silently degrades — that is a hard failure.
REQUIRED_PATHS = [
    "CLAUDE.md",
    "knowledge/_index.md",
    "knowledge/_quick-reference.md",
    "knowledge/frameworks/content-copywriting/algorithmic-authorship.md",
    "knowledge/frameworks/content-copywriting/perception-engineering.md",
    "knowledge/frameworks/content-copywriting/four-us-framework.md",
    "knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md",
    "knowledge/checklists/content-checklist.md",
    "knowledge/checklists/seo-checklist.md",
    "knowledge/checklists/agent-readiness-checklist.md",
    "knowledge/personas/_persona-index.md",
    "knowledge/playbooks/what-works.md",
    "harness/brief-schema.md",
    "harness/ARCHITECTURE.md",
    "harness/skill-contracts/blog-post.yaml",
    "harness/skill-contracts/cold-email.yaml",
    "harness/skill-contracts/meta-ads.yaml",
    "harness/references/audit-data-provenance.md",
    "harness/references/meta-ads-rules.md",
    "harness/references/google-ads-policy-reference.md",
    "harness/references/advertising-compliance.md",
    "harness/skills/kai/SKILL.md",
    "harness/skills/kai-brand-pulse/SKILL.md",
    "harness/skills/kai-gate/SKILL.md",
    "harness/skills/kai-write/SKILL.md",
    "harness/skills/kai-retro/SKILL.md",
    "harness/workflow-skus/brand-pulse.yaml",
    "scripts/quality_gates/four_us_score.py",
    "scripts/quality_gates/banned_word_check.py",
    "scripts/quality_gates/seo_lint.py",
    "scripts/quality_gates/agent_readiness_lint.py",
    "scripts/quality_gates/audit_provenance_lint.py",
    "scripts/quality_gates/golden_check.py",
    "scripts/self_improvement/lesson_capture.py",
    "scripts/content/engine.py",
    "scripts/audit/collect.py",
    "scripts/intel/brand_pulse.py",
    "memory/MEMORY.md",
    "memory/lessons.md",
    "memory/edge-cases.md",
    "memory/what-doesnt-work.md",
    "evals/golden/manifest.json",
    "docs/system/governance-and-quality.md",
    "docs/system/learning-loop.md",
    "docs/OPENCLAW_SETUP.md",
]

# The instruction chain: files that CLAUDE.md/AGENTS.md tell every agent to
# read (load-on-demand pointers, workspace core files, the memory layer).
# If one of these is missing, agents get instructed to load files that do not
# exist — which silently happened when .claude/rules/ was dropped in the
# 2026-06-18 slimming. To update: when AGENTS.md or CLAUDE.md gains a new
# pointer target (a "read this file" instruction outside the Framework Map),
# add it here.
INSTRUCTION_CHAIN_PATHS = [
    "AGENTS.md",
    "CLAUDE.md",
    ".claude/rules/architecture-and-memory.md",
    ".claude/rules/scripts-and-tools.md",
    "memory/MEMORY.md",
    "memory/lessons.md",
    "memory/edge-cases.md",
    "memory/what-doesnt-work.md",
    "workspace/AGENTS.md",
    "workspace/HEARTBEAT.md",
    "workspace/IDENTITY.md",
    "workspace/MARKETING.md",
    "workspace/SOUL.md",
    "workspace/TOOLS.md",
    "workspace/USER.md",
]

# Markdown docs whose inline `path` references (Framework Map table, skill
# contracts, checklists, rules files) are parsed and existence-checked by
# check_instruction_chain(). Paths under data/ are runtime artifacts and are
# skipped; so are globs, ellipses, and command arguments.
REFERENCED_DOCS = [
    "AGENTS.md",
    ".claude/rules/architecture-and-memory.md",
    ".claude/rules/scripts-and-tools.md",
]

# Scripts that must at least compile on a fresh clone (no credentials needed).
COMPILE_PATHS = [
    "scripts/quality_gates/banned_word_check.py",
    "scripts/quality_gates/seo_lint.py",
    "scripts/quality_gates/gate_logger.py",
    "scripts/quality_gates/golden_check.py",
    "scripts/self_improvement/lesson_capture.py",
    "scripts/intel/brand_pulse.py",
    "scripts/doctor.py",
]

# (module, what it unlocks)
OPTIONAL_DEPS = [
    ("google.genai", "Four U's scoring + content writing (Gemini)"),
    ("openai", "agent loop LLM router + OpenRouter-compatible SDK callers"),
    ("dotenv", ".env loading for all scripts"),
    ("yaml", "skill contracts, quality policies, defaults updater"),
    ("fastapi", "gateway remote runner (gateway/main.py)"),
    ("pytest", "test suite (tests/)"),
]

# (env var, what it unlocks)
OPTIONAL_ENV = [
    ("GEMINI_API_KEY", "Four U's gate + draft writing"),
    ("GOOGLE_CREDENTIALS_PATH", "GSC/GA4 briefs + 30-day performance checks"),
    ("DISCORD_BOT_TOKEN", "Discord approvals + notifications"),
]
AGENT_PROVIDER_ENV = [
    "OPENROUTER_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "ANTHROPIC_API_KEY",
]


class Report:
    def __init__(self) -> None:
        self.failures: list[str] = []
        self.warnings: list[str] = []
        self.passes: list[str] = []

    def ok(self, msg: str) -> None:
        self.passes.append(msg)

    def warn(self, msg: str) -> None:
        self.warnings.append(msg)

    def fail(self, msg: str) -> None:
        self.failures.append(msg)


def check_python(report: Report) -> None:
    if sys.version_info < (3, 10):
        report.fail(f"Python {sys.version.split()[0]} — the harness needs 3.10+")
    else:
        report.ok(f"Python {sys.version.split()[0]}")


def check_required_paths(report: Report) -> None:
    missing = [p for p in REQUIRED_PATHS if not (REPO_ROOT / p).exists()]
    if missing:
        for p in missing:
            report.fail(f"missing referenced file: {p}")
    report.ok(f"{len(REQUIRED_PATHS) - len(missing)}/{len(REQUIRED_PATHS)} referenced files present")


_PATH_TOKEN_RE = re.compile(r"[A-Za-z0-9_.\-/]+/?")


def extract_repo_paths(markdown_text: str) -> list[str]:
    """Extract repo-relative file/dir paths from inline-code spans in markdown.

    Rules (kept deliberately conservative to avoid false failures):
      - fenced code blocks are stripped (inline backticks only)
      - a token counts as a path when it contains "/" and is made purely of
        path characters (no spaces, globs, angle brackets, or "..." ellipses)
      - `python <script>.py ...` command tokens contribute their script path
      - absolute paths and data/ runtime artifacts are skipped
    """
    lines: list[str] = []
    in_fence = False
    for line in markdown_text.splitlines():
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if not in_fence:
            lines.append(line)

    paths: set[str] = set()
    for line in lines:
        for token in re.findall(r"`([^`\n]+)`", line):
            token = token.strip()
            candidate = ""
            if token.startswith(("python ", "python3 ")):
                words = token.split()
                if len(words) > 1 and words[1].endswith(".py"):
                    candidate = words[1]
            elif " " not in token and _PATH_TOKEN_RE.fullmatch(token):
                candidate = token
            if not candidate or "/" not in candidate:
                continue
            if ".." in candidate or "*" in candidate:
                continue
            if candidate.startswith(("/", "data/")):
                continue
            paths.add(candidate)
    return sorted(paths)


def check_instruction_chain(report: Report, root: Path = REPO_ROOT) -> None:
    """Verify every file the instruction chain tells agents to load exists.

    Covers the CLAUDE.md/AGENTS.md load-on-demand pointers (.claude/rules/*),
    the workspace core files, the memory layer, and every path referenced in
    the AGENTS.md Framework Map + the .claude/rules docs themselves.
    """
    missing_chain = [p for p in INSTRUCTION_CHAIN_PATHS if not (root / p).exists()]
    for p in missing_chain:
        report.fail(f"instruction chain broken: {p} is referenced by CLAUDE.md/AGENTS.md but missing")

    checked = 0
    for doc in REFERENCED_DOCS:
        doc_path = root / doc
        if not doc_path.exists():
            continue  # already failed above (or not part of this tree)
        try:
            text = doc_path.read_text(encoding="utf-8")
        except OSError as exc:
            report.fail(f"cannot read {doc}: {exc}")
            continue
        for rel in extract_repo_paths(text):
            checked += 1
            if not (root / rel).exists():
                report.fail(f"{doc} references missing path: {rel}")
    report.ok(
        f"instruction chain intact ({len(INSTRUCTION_CHAIN_PATHS) - len(missing_chain)}"
        f"/{len(INSTRUCTION_CHAIN_PATHS)} core files, {checked} doc-referenced paths checked)"
    )


def check_compiles(report: Report) -> None:
    for rel in COMPILE_PATHS:
        path = REPO_ROOT / rel
        if not path.exists():
            continue  # already reported by check_required_paths
        try:
            py_compile.compile(str(path), doraise=True)
        except py_compile.PyCompileError as exc:
            report.fail(f"{rel} does not compile: {exc.msg}")
    report.ok("deterministic gate scripts compile")


def check_golden_corpus(report: Report) -> None:
    runner = REPO_ROOT / "scripts" / "quality_gates" / "golden_check.py"
    if not runner.exists():
        report.fail("golden corpus runner missing (scripts/quality_gates/golden_check.py)")
        return
    spec = importlib.util.spec_from_file_location("_doctor_golden", runner)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        ok, results = mod.run_golden()
    except Exception as exc:
        report.fail(f"golden corpus runner crashed: {exc}")
        return
    if ok:
        report.ok(f"golden corpus intact ({len(results)} cases)")
    else:
        for r in results:
            if not r["ok"]:
                report.fail(f"golden case {r['id']}: {r['detail']}")


def check_learning_layer(report: Report) -> None:
    learn_dir = REPO_ROOT / "data" / "learning"
    try:
        learn_dir.mkdir(parents=True, exist_ok=True)
        probe = learn_dir / ".doctor-probe"
        probe.write_text("ok", encoding="utf-8")
        probe.unlink()
        report.ok("data/learning/ writable (gate runs will be logged)")
    except OSError as exc:
        report.warn(f"data/learning/ not writable ({exc}) — gate logging disabled, mining won't work")


def check_optional(report: Report) -> None:
    for module, unlocks in OPTIONAL_DEPS:
        if importlib.util.find_spec(module.split(".")[0]) is None:
            report.warn(f"python package {module!r} not installed — disables: {unlocks}")
        else:
            report.ok(f"{module} available ({unlocks})")
    configured_agent_keys = [var for var in AGENT_PROVIDER_ENV if os.environ.get(var)]
    if configured_agent_keys:
        report.ok(
            "agent LLM provider key set ("
            + ", ".join(configured_agent_keys)
            + ")"
        )
    else:
        report.warn(
            "no agent LLM provider key set — disables: OpenClaw autonomous agent mode "
            f"(set one of {', '.join(AGENT_PROVIDER_ENV)})"
        )
    for var, unlocks in OPTIONAL_ENV:
        if os.environ.get(var):
            report.ok(f"{var} set ({unlocks})")
        else:
            report.warn(f"{var} not set — disables: {unlocks}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Kai harness preflight self-check")
    parser.add_argument(
        "--ci",
        action="store_true",
        help="Hard checks only (paths, compiles, golden corpus); skip dependency/credential report",
    )
    args = parser.parse_args()

    report = Report()
    check_python(report)
    check_required_paths(report)
    check_instruction_chain(report)
    check_compiles(report)
    check_golden_corpus(report)
    if not args.ci:
        check_learning_layer(report)
        check_optional(report)

    print("\nKai Harness Doctor")
    print("-" * 40)
    for msg in report.passes:
        print(f"  OK {msg}")
    if report.warnings:
        print(f"\n  Warnings (degraded features, not blockers):")
        for msg in report.warnings:
            print(f"  WARN {msg}")
    if report.failures:
        print(f"\n  FAILURES (the harness will not behave as documented):")
        for msg in report.failures:
            print(f"  FAIL {msg}")
        print("\nDoctor found hard failures. Fix these before relying on the harness.")
        return 1

    print(f"\nHarness intact. {len(report.warnings)} optional feature(s) unconfigured." if report.warnings
          else "\nHarness fully configured.")
    if not args.ci:
        print("   Next: open Claude Code here and run /kai-start, or /kai-gate on any draft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
