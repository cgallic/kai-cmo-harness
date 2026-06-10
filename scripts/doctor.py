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
    "harness/skills/kai-gate/SKILL.md",
    "harness/skills/kai-write/SKILL.md",
    "harness/skills/kai-retro/SKILL.md",
    "scripts/quality_gates/four_us_score.py",
    "scripts/quality_gates/banned_word_check.py",
    "scripts/quality_gates/seo_lint.py",
    "scripts/quality_gates/agent_readiness_lint.py",
    "scripts/quality_gates/audit_provenance_lint.py",
    "scripts/quality_gates/golden_check.py",
    "scripts/quality_gates/llm_judge.py",
    "scripts/llm_client.py",
    "scripts/self_improvement/lesson_capture.py",
    "scripts/content/engine.py",
    "scripts/audit/collect.py",
    "memory/MEMORY.md",
    "memory/lessons.md",
    "memory/edge-cases.md",
    "memory/what-doesnt-work.md",
    "evals/golden/manifest.json",
    "docs/system/governance-and-quality.md",
    "docs/system/learning-loop.md",
    "docs/OPENCLAW_SETUP.md",
]

# Scripts that must at least compile on a fresh clone (no credentials needed).
COMPILE_PATHS = [
    "scripts/quality_gates/banned_word_check.py",
    "scripts/quality_gates/seo_lint.py",
    "scripts/quality_gates/gate_logger.py",
    "scripts/quality_gates/golden_check.py",
    "scripts/quality_gates/llm_judge.py",
    "scripts/quality_gates/four_us_score.py",
    "scripts/llm_client.py",
    "scripts/self_improvement/lesson_capture.py",
    "scripts/doctor.py",
]

# (module, what it unlocks). All LLM tasks (judge, writer, extraction,
# scoring) run on ANY one provider via scripts/llm_client.py.
OPTIONAL_DEPS = [
    ("google.genai", "Gemini provider for all LLM tasks + audio/video transcription (knowledge_cloner)"),
    ("anthropic", "Anthropic provider for all LLM tasks + OpenClaw agent"),
    ("openai", "OpenAI provider for all LLM tasks"),
    ("dotenv", ".env loading for all scripts"),
    ("yaml", "skill contracts, quality policies, defaults updater"),
    ("fastapi", "gateway remote runner (gateway/main.py)"),
    ("pytest", "test suite (tests/)"),
]

# (env var, what it unlocks). LLM tasks need ANY ONE of the three LLM keys
# (pin with KAI_LLM_PROVIDER / KAI_LLM_MODEL).
OPTIONAL_ENV = [
    ("GEMINI_API_KEY", "all LLM tasks via Gemini + knowledge-cloner transcription"),
    ("ANTHROPIC_API_KEY", "all LLM tasks via Claude + OpenClaw agent mode"),
    ("OPENAI_API_KEY", "all LLM tasks via OpenAI"),
    ("GOOGLE_CREDENTIALS_PATH", "GSC/GA4 briefs + 30-day performance checks"),
    ("DISCORD_BOT_TOKEN", "Discord approvals + notifications"),
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


def check_judge_provider(report: Report) -> None:
    """Report which LLM provider all LLM tasks will use, if any."""
    client_path = REPO_ROOT / "scripts" / "llm_client.py"
    spec = importlib.util.spec_from_file_location("_doctor_llm_client", client_path)
    mod = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(mod)
        provider, model = mod.resolve_provider()
        report.ok(f"LLM provider (judge/writer/extraction): {provider} ({model})")
    except FileNotFoundError:
        report.fail("scripts/llm_client.py missing")
    except Exception as exc:
        report.warn(f"LLM tasks disabled — {exc}")


def check_optional(report: Report) -> None:
    for module, unlocks in OPTIONAL_DEPS:
        if importlib.util.find_spec(module.split(".")[0]) is None:
            report.warn(f"python package {module!r} not installed — disables: {unlocks}")
        else:
            report.ok(f"{module} available ({unlocks})")
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
    check_compiles(report)
    check_golden_corpus(report)
    if not args.ci:
        check_learning_layer(report)
        check_judge_provider(report)
        check_optional(report)

    print("\nKai Harness Doctor")
    print("─" * 40)
    for msg in report.passes:
        print(f"  ✓ {msg}")
    if report.warnings:
        print(f"\n  Warnings (degraded features, not blockers):")
        for msg in report.warnings:
            print(f"  ⚠ {msg}")
    if report.failures:
        print(f"\n  FAILURES (the harness will not behave as documented):")
        for msg in report.failures:
            print(f"  ✗ {msg}")
        print("\n❌ Doctor found hard failures. Fix these before relying on the harness.")
        return 1

    print(f"\n✅ Harness intact. {len(report.warnings)} optional feature(s) unconfigured." if report.warnings
          else "\n✅ Harness fully configured.")
    if not args.ci:
        print("   Next: open Claude Code here and run /kai-start, or /kai-gate on any draft.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
