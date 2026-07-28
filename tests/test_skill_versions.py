"""v1 (procedural) and v2 (goal-oriented) skill sets must stay in lockstep.

Doctrine under test: docs/system/skill-versions.md
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
V1_ROOT = REPO_ROOT / "harness" / "skills"
V2_ROOT = REPO_ROOT / "harness" / "skills-v2"

# The router is an index, and kai-goal was authored goal-native from the start.
SHAPE_EXEMPT = {"kai", "kai-goal"}

REQUIRED_SECTIONS = ("## Objective", "## Done when", "## Constraints", "## Context", "## Escalate when")
PHASE_RE = re.compile(r"^#{1,4}\s+(phase|step)\s*\d", re.IGNORECASE | re.MULTILINE)

# Rules that must survive the rewrite wherever v1 stated them. v2 may restate
# them as constraints, but may not drop them — v2 is never more permissive.
BINDING_TOKENS = {
    "audit-data-provenance.md",
    "advertising-compliance.md",
    "creator-disclosure.md",
    "cold-email-rules.md",
    "social-automation-rules.md",
}


def _skill_dirs(root: Path) -> set[str]:
    if not root.is_dir():
        return set()
    return {p.name for p in root.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()}


def _frontmatter(text: str) -> str | None:
    if not text.startswith("---"):
        return None
    end = text.find("\n---", 3)
    return text[: end + 4] if end != -1 else None


def _read(root: Path, name: str) -> str:
    return (root / name / "SKILL.md").read_text(encoding="utf-8")


V1_SKILLS = sorted(_skill_dirs(V1_ROOT))


def test_v2_skill_set_exists():
    assert V2_ROOT.is_dir(), "harness/skills-v2 is missing"
    assert _skill_dirs(V2_ROOT), "harness/skills-v2 contains no skills"


def test_every_v1_skill_has_a_v2_counterpart():
    missing = sorted(_skill_dirs(V1_ROOT) - _skill_dirs(V2_ROOT))
    assert not missing, f"skills with no v2 counterpart: {missing}"


def test_no_orphan_v2_skills():
    orphans = sorted(_skill_dirs(V2_ROOT) - _skill_dirs(V1_ROOT))
    assert not orphans, f"v2 skills with no v1 counterpart: {orphans}"


@pytest.mark.parametrize("name", V1_SKILLS)
def test_frontmatter_is_identical(name: str):
    """Routing must not change between plugins — same request, same skill."""
    assert _frontmatter(_read(V1_ROOT, name)) == _frontmatter(_read(V2_ROOT, name)), (
        f"{name}: v1/v2 frontmatter differs, so the two plugins would route differently"
    )


@pytest.mark.parametrize("name", [n for n in V1_SKILLS if n not in SHAPE_EXEMPT])
def test_v2_is_goal_shaped(name: str):
    text = _read(V2_ROOT, name)
    assert not PHASE_RE.search(text), f"{name}: v2 still carries a phase/step list"
    missing = [s for s in REQUIRED_SECTIONS if s not in text]
    assert not missing, f"{name}: v2 is missing {missing}"


@pytest.mark.parametrize("name", [n for n in V1_SKILLS if n not in SHAPE_EXEMPT])
def test_v2_keeps_binding_references(name: str):
    """Removing procedure never means removing a constraint."""
    v1_text = _read(V1_ROOT, name)
    v2_text = _read(V2_ROOT, name)
    dropped = [t for t in BINDING_TOKENS if t in v1_text and t not in v2_text]
    assert not dropped, f"{name}: v2 dropped binding reference(s) present in v1: {dropped}"


@pytest.mark.parametrize("name", [n for n in V1_SKILLS if n not in SHAPE_EXEMPT])
def test_v2_is_shorter_than_v1(name: str):
    """v2 removes derivable scaffolding; a longer v2 means it was not removed."""
    v1_lines = len(_read(V1_ROOT, name).splitlines())
    v2_lines = len(_read(V2_ROOT, name).splitlines())
    assert v2_lines < v1_lines, f"{name}: v2 ({v2_lines} lines) is not shorter than v1 ({v1_lines})"


def test_v2_plugin_package_is_wired():
    plugin = REPO_ROOT / "plugins" / "kai-marketing-os-v2"
    assert (plugin / ".claude-plugin" / "plugin.json").is_file()
    for required in ("skills", "knowledge", "agents", "harness/eco-floors.yaml", "scripts/quality_gates"):
        assert (plugin / required).exists(), f"v2 plugin is missing {required}"
    assert (plugin / "skills").resolve() == V2_ROOT.resolve(), "v2 plugin does not point at harness/skills-v2"
