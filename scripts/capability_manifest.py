#!/usr/bin/env python3
"""Generate and verify Kai's repository capability inventory.

The filesystem and the /kai router tables are the sources of truth.  The
checked-in JSON manifest and bounded documentation blocks are derived views.
No wall-clock value is emitted, so identical trees produce identical output.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[1]
ARTIFACT_PATH = Path("docs/system/capability-manifest.json")
ROUTER_PATH = Path("harness/skills/kai/SKILL.md")

BLOCK_START = "<!-- capability-counts:start -->"
BLOCK_END = "<!-- capability-counts:end -->"

_FRONTMATTER_RE = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
_ROUTER_ROW_RE = re.compile(
    r"^\|\s*`/(?P<name>kai-[a-z0-9-]+)`\s*\|\s*(?P<description>.*?)\s*\|\s*$"
)
_HEADING_RE = re.compile(r"^##\s+(?P<name>[A-Z][A-Z ]+?)(?:\s+\(.*\))?\s*$")


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = _FRONTMATTER_RE.match(text)
    if not match:
        return {}
    values: dict[str, str] = {}
    for line in match.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator and key.strip() in {"name", "description"}:
            values[key.strip()] = value.strip().strip('"').strip("'")
    return values


# Router table headings that hold public /kai commands. "pursue" is the
# goal-oriented surface (/kai-goal): it runs an objective to a verdict rather
# than producing a single asset.
ROUTER_CATEGORIES = {"pursue", "produce", "audit", "plan", "analyze", "learn"}


def parse_router_commands(router_path: Path) -> list[dict[str, str]]:
    """Parse public commands only from categorized router table rows."""
    commands: list[dict[str, str]] = []
    seen: set[str] = set()
    category: str | None = None
    for line in router_path.read_text(encoding="utf-8").splitlines():
        heading = _HEADING_RE.match(line)
        if heading:
            candidate = heading.group("name").strip().lower().replace(" ", "-")
            category = candidate if candidate in ROUTER_CATEGORIES else None
            continue
        row = _ROUTER_ROW_RE.match(line)
        if not row or category is None:
            continue
        name = row.group("name")
        if name in seen:
            continue
        seen.add(name)
        commands.append(
            {
                "name": name,
                "category": category,
                "description": row.group("description").strip(),
            }
        )
    return commands


def _markdown_count(path: Path, *, recursive: bool = False) -> int:
    iterator = path.rglob("*.md") if recursive else path.glob("*.md")
    return sum(1 for item in iterator if item.is_file() and item.name not in {"AGENTS.md", "CLAUDE.md"})


def discover_inventory(root: Path = REPO_ROOT) -> dict[str, Any]:
    """Return the deterministic capability manifest derived from ``root``."""
    root = root.resolve()
    skills_root = root / "harness" / "skills"
    router_commands = parse_router_commands(root / ROUTER_PATH)
    router_by_name = {command["name"]: command for command in router_commands}

    skill_dirs = sorted(path for path in skills_root.iterdir() if path.is_dir())
    canonical_dirs = sorted(
        path for path in skill_dirs if path.name.startswith("kai-") and (path / "SKILL.md").is_file()
    )
    manifest_pages = {
        path.stem: path
        for path in (root / "docs" / "skill-manifest").glob("kai-*.md")
        if path.is_file()
    }

    skills: list[dict[str, Any]] = []
    for directory in canonical_dirs:
        skill_path = directory / "SKILL.md"
        metadata = _frontmatter(skill_path) if skill_path.exists() else {}
        command = router_by_name.get(directory.name)
        doc_path = manifest_pages.get(directory.name)
        skills.append(
            {
                "name": directory.name,
                "description": metadata.get("description", ""),
                "source": _relative(skill_path, root),
                "public_router_command": command is not None,
                "router_category": command["category"] if command else None,
                "manifest_doc": _relative(doc_path, root) if doc_path else None,
            }
        )

    canonical_names = {skill["name"] for skill in skills}
    unresolved_commands = sorted(set(router_by_name) - canonical_names)
    undocumented_skills = sorted(canonical_names - set(manifest_pages))
    orphan_manifest_pages = sorted(set(manifest_pages) - canonical_names)
    named_personas = [
        path
        for path in (root / "knowledge" / "personas").glob("*.md")
        if path.is_file() and not path.name.startswith("_") and path.name not in {"AGENTS.md", "CLAUDE.md"}
    ]

    counts = {
        "skill_directories": len(skill_dirs),
        "canonical_kai_skills": len(skills),
        "public_router_commands": len(router_commands),
        "public_manifest_pages": len(manifest_pages),
        "undocumented_canonical_skills": len(undocumented_skills),
        "playbook_docs": _markdown_count(root / "knowledge" / "playbooks"),
        "checklists": _markdown_count(root / "knowledge" / "checklists"),
        "framework_docs": _markdown_count(root / "knowledge" / "frameworks", recursive=True),
        "channel_guides": _markdown_count(root / "knowledge" / "channels"),
        "audience_persona_profiles": len(named_personas),
        "harness_references": sum(1 for path in (root / "harness" / "references").iterdir() if path.is_file()),
        "skill_contracts": sum(1 for path in (root / "harness" / "skill-contracts").glob("*.yaml") if path.is_file()),
    }

    return {
        "schema_version": 1,
        "sources": {
            "skills": "harness/skills/*/SKILL.md",
            "public_router_commands": ROUTER_PATH.as_posix(),
            "public_manifest_pages": "docs/skill-manifest/kai-*.md",
            "knowledge": "repository filesystem counts using counting_rules",
        },
        "counting_rules": {
            "skill_directories": "Immediate directories under harness/skills.",
            "canonical_kai_skills": "Immediate kai-* directories under harness/skills with their SKILL.md as source.",
            "public_router_commands": "Unique /kai-* rows in the PURSUE, PRODUCE, AUDIT, PLAN, ANALYZE, and LEARN tables.",
            "public_manifest_pages": "kai-*.md files under docs/skill-manifest.",
            "knowledge_markdown": "Markdown files under the named surface; recursive only for frameworks; AGENTS.md and CLAUDE.md excluded.",
            "audience_persona_profiles": "Non-underscore Markdown files under knowledge/personas; AGENTS.md and CLAUDE.md excluded.",
            "harness_references": "Immediate files under harness/references.",
            "skill_contracts": "Immediate *.yaml files under harness/skill-contracts.",
        },
        "counts": counts,
        "coverage": {
            "undocumented_canonical_skills": undocumented_skills,
            "orphan_manifest_pages": orphan_manifest_pages,
            "unresolved_router_commands": unresolved_commands,
        },
        "router_commands": router_commands,
        "skills": skills,
    }


def render_json(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, indent=2, ensure_ascii=False) + "\n"


def render_markdown(manifest: dict[str, Any]) -> str:
    counts = manifest["counts"]
    rows = ["| Surface | Count |", "|---|---:|"]
    labels = {
        "skill_directories": "Skill directories",
        "canonical_kai_skills": "Canonical `kai-*` skills",
        "public_router_commands": "Public `/kai` router commands",
        "public_manifest_pages": "Public skill manifest pages",
        "undocumented_canonical_skills": "Canonical skills missing manifest pages",
        "playbook_docs": "Playbook docs",
        "checklists": "Checklists",
        "framework_docs": "Framework docs",
        "channel_guides": "Channel guides",
        "audience_persona_profiles": "Audience persona profiles",
        "harness_references": "Harness references",
        "skill_contracts": "Skill contracts",
    }
    for key, label in labels.items():
        rows.append(f"| {label} | {counts[key]} |")
    return "\n".join(rows)


def generated_doc_blocks(manifest: dict[str, Any]) -> dict[Path, str]:
    counts = manifest["counts"]
    agent_summary = (
        f"Inventory reachable from here: {counts['skill_directories']} skill directories, "
        f"{counts['canonical_kai_skills']} canonical `kai-*` skills, "
        f"{counts['public_router_commands']} public `/kai` router commands, "
        f"{counts['playbook_docs']} playbook docs, {counts['checklists']} checklists, "
        f"{counts['framework_docs']} framework docs, {counts['channel_guides']} channel guides, "
        f"{counts['audience_persona_profiles']} audience persona profiles, "
        f"{counts['harness_references']} harness references, and {counts['skill_contracts']} skill contracts."
    )
    governance = (
        "Generated from `docs/system/capability-manifest.json`. Regenerate with "
        "`python -m scripts.capability_manifest generate`; verify with "
        "`python -m scripts.capability_manifest check`.\n\n"
        + render_markdown(manifest)
    )
    return {
        Path("AGENTS.md"): f"{BLOCK_START}\n{agent_summary}\n{BLOCK_END}",
        Path("docs/system/governance-and-quality.md"): f"{BLOCK_START}\n{governance}\n{BLOCK_END}",
    }


def _replace_block(text: str, replacement: str, path: Path) -> str:
    pattern = re.compile(re.escape(BLOCK_START) + r".*?" + re.escape(BLOCK_END), re.DOTALL)
    matches = list(pattern.finditer(text))
    if len(matches) != 1:
        raise ValueError(f"{path.as_posix()}: expected exactly one generated capability-count block, found {len(matches)}")
    return pattern.sub(replacement, text, count=1)


def _atomic_write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8")
    temporary.replace(path)


def generate(root: Path = REPO_ROOT) -> dict[str, Any]:
    manifest = discover_inventory(root)
    _atomic_write(root / ARTIFACT_PATH, render_json(manifest))
    for relative_path, block in generated_doc_blocks(manifest).items():
        path = root / relative_path
        updated = _replace_block(path.read_text(encoding="utf-8"), block, relative_path)
        _atomic_write(path, updated)
    return manifest


def check_manifest(root: Path = REPO_ROOT) -> list[str]:
    root = root.resolve()
    expected = discover_inventory(root)
    errors: list[str] = []
    for name in expected["coverage"]["unresolved_router_commands"]:
        errors.append(f"public router command has no canonical skill implementation: {name}")
    for name in expected["coverage"]["orphan_manifest_pages"]:
        errors.append(f"public manifest page has no canonical skill implementation: {name}")
    artifact = root / ARTIFACT_PATH
    if not artifact.exists():
        errors.append(f"missing generated artifact: {ARTIFACT_PATH.as_posix()}")
    elif artifact.read_text(encoding="utf-8") != render_json(expected):
        try:
            actual_manifest = json.loads(artifact.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            actual_manifest = {}
        actual_counts = actual_manifest.get("counts", {})
        for key, expected_value in expected["counts"].items():
            actual_value = actual_counts.get(key)
            if actual_value != expected_value:
                errors.append(
                    f"capability count drift: {key} is {actual_value!r} in the artifact, "
                    f"but live discovery is {expected_value!r}"
                )
        actual_coverage = actual_manifest.get("coverage", {})
        for key, expected_value in expected["coverage"].items():
            actual_value = actual_coverage.get(key)
            if actual_value != expected_value:
                errors.append(
                    f"capability coverage drift: {key} is {actual_value!r} in the artifact, "
                    f"but live discovery is {expected_value!r}"
                )
        errors.append(
            f"{ARTIFACT_PATH.as_posix()} is stale; run `python -m scripts.capability_manifest generate`"
        )

    for relative_path, block in generated_doc_blocks(expected).items():
        path = root / relative_path
        if not path.exists():
            errors.append(f"missing generated-count document: {relative_path.as_posix()}")
            continue
        try:
            actual = path.read_text(encoding="utf-8")
            expected_text = _replace_block(actual, block, relative_path)
        except ValueError as exc:
            errors.append(str(exc))
            continue
        if actual != expected_text:
            errors.append(
                f"{relative_path.as_posix()} capability-count block is stale; "
                "run `python -m scripts.capability_manifest generate`"
            )
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate or verify Kai's capability manifest")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("generate", help="Regenerate the JSON artifact and bounded documentation blocks")
    subparsers.add_parser("check", help="Fail when the artifact or documentation blocks drift")
    show = subparsers.add_parser("show", help="Print the live derived inventory without writing files")
    show.add_argument("--format", choices=("json", "markdown"), default="json")
    args = parser.parse_args(argv)

    if args.command == "generate":
        manifest = generate()
        print(f"Generated {ARTIFACT_PATH.as_posix()} ({manifest['counts']['canonical_kai_skills']} canonical skills)")
        return 0
    if args.command == "check":
        errors = check_manifest()
        if errors:
            for error in errors:
                print(f"FAIL {error}", file=sys.stderr)
            return 1
        print("Capability manifest and generated documentation blocks are current.")
        return 0

    manifest = discover_inventory()
    print(render_json(manifest) if args.format == "json" else render_markdown(manifest))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
