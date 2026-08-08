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
    "scripts/capability_manifest.py",
    "scripts/intel/brand_pulse.py",
    "scripts/reddit_monitor/intelligence/__init__.py",
    "scripts/reddit_monitor/intelligence/cli.py",
    "scripts/reddit_monitor/intelligence/dashboard.py",
    "scripts/reddit_monitor/intelligence/pipeline.py",
    "scripts/reddit_monitor/intelligence/profiles.py",
    "scripts/reddit_monitor/intelligence/sources.py",
    "scripts/reddit_monitor/intelligence/profiles/example.json",
    "scripts/reddit_monitor/intelligence/profile.schema.json",
    "scripts/reddit_monitor/intelligence/opportunity.schema.json",
    "memory/MEMORY.md",
    "memory/lessons.md",
    "memory/edge-cases.md",
    "memory/what-doesnt-work.md",
    "evals/golden/manifest.json",
    "docs/system/governance-and-quality.md",
    "docs/system/capability-manifest.json",
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
    "scripts/capability_manifest.py",
    "scripts/harness_config.py",
    "scripts/reddit_monitor/intelligence/cli.py",
    "scripts/reddit_monitor/intelligence/dashboard.py",
    "scripts/reddit_monitor/intelligence/pipeline.py",
    "scripts/reddit_monitor/intelligence/profiles.py",
    "scripts/reddit_monitor/intelligence/sources.py",
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


def check_capability_manifest(report: Report) -> None:
    """Fail when the generated inventory or its bounded doc blocks drift."""
    try:
        manifest_path = REPO_ROOT / "scripts" / "capability_manifest.py"
        spec = importlib.util.spec_from_file_location("_doctor_capability_manifest", manifest_path)
        if spec is None or spec.loader is None:
            raise ImportError(f"cannot load {manifest_path}")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        errors = module.check_manifest(REPO_ROOT)
    except Exception as exc:
        report.fail(f"capability manifest check crashed: {exc}")
        return
    if errors:
        for error in errors:
            report.fail(f"capability manifest: {error}")
        return
    report.ok("capability manifest and generated inventory docs current")


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


# Cowork plugin package limits (docs/cowork/guide/plugins).
COWORK_MAX_FILES = 5000
COWORK_MAX_BYTES = 200 * 1024 * 1024


def check_eco(report: Report) -> None:
    """The ECO gate must load its floors and refuse a self-issued verdict.

    Doctor itself is stdlib-only, so the semantic half of this check runs only
    when PyYAML is available (it is an optional dep).  `tests/test_eco.py`
    enforces the same invariants where dependencies are installed.
    """
    floors_path = REPO_ROOT / "harness" / "eco-floors.yaml"
    if not floors_path.exists():
        report.fail("harness/eco-floors.yaml is missing — no work type has a declared floor")
        return

    if importlib.util.find_spec("yaml") is None:
        report.warn("pyyaml not installed — ECO floor/verdict checks skipped (tests/test_eco.py covers them)")
        return

    if str(REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(REPO_ROOT))
    try:
        from scripts.quality_gates.eco_core import EcoFloors, grade
    except Exception as exc:  # pragma: no cover - import failure is the finding
        report.fail(f"ECO core failed to import: {exc}")
        return

    try:
        floors = EcoFloors.load()
    except Exception as exc:
        report.fail(f"harness/eco-floors.yaml failed to load: {exc}")
        return

    if not floors.work_types or not floors.evidence_kinds:
        report.fail("harness/eco-floors.yaml declares no work types or evidence kinds")
        return

    # The load-bearing invariant: evidence verified by the actor is discarded.
    result = grade(
        [{"kind": "provider_receipt", "locator": "x", "verifier": "actor", "observed_at": "2026-01-01T00:00:00Z"}],
        work_type=floors.work_type("blog-post"),
        claimed_by="actor",
        floors=floors,
    )
    if result.grade["E"] != 0:
        report.fail("ECO honest-quorum rule is not enforced — actor-verified evidence was accepted")
        return

    report.ok(
        f"ECO gate live ({len(floors.work_types)} work types, "
        f"{len(floors.evidence_kinds)} evidence kinds, self-verdict refused)"
    )


# A v2 skill states an objective and a floor. A numbered phase list means the
# procedural scaffolding survived the rewrite, which is the thing v2 removes.
_PHASE_RE = re.compile(r"^#{1,4}\s+(phase|step)\s*\d", re.IGNORECASE | re.MULTILINE)
V2_REQUIRED_SECTIONS = ("## Objective", "## Done when", "## Constraints", "## Context", "## Escalate when")


def _frontmatter_block(text: str) -> str | None:
    """Return the raw YAML frontmatter, or None when the file has none."""
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    return text[: end + 4] if end != -1 else None


def check_skill_versions(report: Report) -> None:
    """v1 and v2 must stay in lockstep on routing, and v2 must stay goal-shaped."""
    v1_root = REPO_ROOT / "harness" / "skills"
    v2_root = REPO_ROOT / "harness" / "skills-v2"
    if not v2_root.exists():
        report.fail("harness/skills-v2 is missing — the v2 skill set is not installed")
        return

    v1 = {p.name for p in v1_root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}
    v2 = {p.name for p in v2_root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}

    missing = sorted(v1 - v2)
    orphans = sorted(v2 - v1)
    if missing:
        report.fail(f"{len(missing)} skill(s) have no v2 counterpart: {', '.join(missing[:6])}")
    if orphans:
        report.fail(f"{len(orphans)} v2 skill(s) have no v1 counterpart: {', '.join(orphans[:6])}")
    if missing or orphans:
        return

    drift: list[str] = []
    shape: list[str] = []
    for name in sorted(v1):
        v1_text = (v1_root / name / "SKILL.md").read_text(encoding="utf-8")
        v2_text = (v2_root / name / "SKILL.md").read_text(encoding="utf-8")

        # Routing must be identical, or the same request reaches different skills.
        if _frontmatter_block(v1_text) != _frontmatter_block(v2_text):
            drift.append(name)

        # The router is an index, and kai-goal was authored goal-native.
        if name in {"kai", "kai-goal"}:
            continue
        if _PHASE_RE.search(v2_text):
            shape.append(f"{name} (phase list)")
        else:
            absent = [s for s in V2_REQUIRED_SECTIONS if s not in v2_text]
            if absent:
                shape.append(f"{name} (missing {absent[0]})")

    for name in drift[:6]:
        report.fail(f"v1/v2 frontmatter drift in {name} — routing would differ between plugins")
    for item in shape[:6]:
        report.fail(f"v2 skill is not goal-shaped: {item}")
    if drift or shape:
        return

    report.ok(f"skill versions in parity ({len(v1)} skills, v1 procedural + v2 goal-oriented)")


def check_plugin_package(report: Report) -> None:
    """Both plugin packages must be self-contained and inside Cowork's limits."""
    for package in ("kai-marketing-os", "kai-marketing-os-v2"):
        _check_one_plugin(report, package)


def _check_one_plugin(report: Report, package: str) -> None:
    plugin_root = REPO_ROOT / "plugins" / package
    if not plugin_root.exists():
        report.fail(f"plugins/{package} is missing — nothing to install in Cowork")
        return

    manifest = plugin_root / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        report.fail(f"plugins/{package}/.claude-plugin/plugin.json is missing")
        return

    # followlinks: the plugin symlinks knowledge/, skills/, and gates back into
    # the repo, and Cowork installs the materialized tree — so measure what the
    # user actually receives, not the symlinks.
    broken = []
    file_count = 0
    total_bytes = 0
    for dirpath, _dirnames, filenames in os.walk(plugin_root, followlinks=True):
        for name in filenames:
            path = Path(dirpath) / name
            if path.is_symlink() and not path.exists():
                broken.append(str(path.relative_to(REPO_ROOT)))
                continue
            file_count += 1
            try:
                total_bytes += path.stat().st_size
            except OSError:
                pass

    if broken:
        for path in broken:
            report.fail(f"{package} symlink does not resolve: {path}")
        return

    for required in (
        "skills",
        "knowledge",
        "harness/eco-floors.yaml",
        "scripts/quality_gates",
        "scripts/reddit_monitor",
        "agents",
    ):
        if not (plugin_root / required).exists():
            report.fail(f"{package} is missing {required} — install would be incomplete")
            return

    if file_count > COWORK_MAX_FILES:
        report.fail(f"{package} has {file_count} files, over Cowork's {COWORK_MAX_FILES} limit")
        return
    if total_bytes > COWORK_MAX_BYTES:
        report.fail(f"{package} is {total_bytes / 1e6:.0f} MB, over Cowork's 200 MB limit")
        return

    agents = len(list((plugin_root / "agents").glob("*.md")))
    report.ok(
        f"{package} installable ({file_count} files, {total_bytes / 1e6:.1f} MB, "
        f"{agents} agents — within Cowork limits)"
    )


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
    check_capability_manifest(report)
    check_golden_corpus(report)
    check_eco(report)
    check_skill_versions(report)
    check_plugin_package(report)
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
