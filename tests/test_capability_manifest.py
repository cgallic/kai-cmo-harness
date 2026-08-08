import asyncio
import json
from pathlib import Path

from scripts import capability_manifest as manifest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _minimal_tree(root: Path) -> None:
    for relative in (
        "harness/skills",
        "harness/references",
        "harness/skill-contracts",
        "docs/skill-manifest",
        "docs/system",
        "knowledge/playbooks",
        "knowledge/checklists",
        "knowledge/frameworks",
        "knowledge/channels",
        "knowledge/personas",
    ):
        (root / relative).mkdir(parents=True, exist_ok=True)
    _write(
        root / "harness/skills/kai/SKILL.md",
        "---\nname: kai\ndescription: Router\n---\n\n"
        "Mention `/kai-not-public` outside a table.\n\n"
        "## PRODUCE (make assets)\n\n"
        "| Skill | What It Does |\n|---|---|\n"
        "| `/kai-alpha` | Alpha workflow |\n"
        "| `/kai-alpha` | Duplicate row ignored |\n",
    )
    _write(
        root / "harness/skills/kai-alpha/SKILL.md",
        "---\nname: kai-alpha\ndescription: Alpha skill\n---\n# Alpha\n",
    )
    _write(root / "docs/skill-manifest/kai-alpha.md", "# Alpha\n")
    _write(root / "AGENTS.md", f"# Agents\n\n{manifest.BLOCK_START}\nstale\n{manifest.BLOCK_END}\n")
    _write(
        root / "docs/system/governance-and-quality.md",
        f"# Governance\n\n{manifest.BLOCK_START}\nstale\n{manifest.BLOCK_END}\n",
    )


def test_current_inventory_is_derived_from_live_sources():
    inventory = manifest.discover_inventory(REPO_ROOT)
    # Re-baselined 2026-08-08: kai-gtm-pack and two skill contracts had been
    # added without updating this fixture, which left the harness self-check
    # red on main from 2026-07-31. Bump these numbers deliberately when a
    # capability is added -- an unexplained change means something drifted.
    assert inventory["counts"] == {
        "skill_directories": 57,
        "canonical_kai_skills": 55,
        "v2_goal_oriented_skills": 57,
        "public_router_commands": 50,
        "public_manifest_pages": 47,
        "undocumented_canonical_skills": 8,
        "playbook_docs": 67,
        "checklists": 37,
        "framework_docs": 38,
        "channel_guides": 31,
        "audience_persona_profiles": 8,
        "harness_references": 37,
        "skill_contracts": 36,
    }
    assert inventory["coverage"]["unresolved_router_commands"] == []
    assert inventory["coverage"]["orphan_manifest_pages"] == []


def test_current_manifest_doc_gaps_are_explicit():
    inventory = manifest.discover_inventory(REPO_ROOT)
    assert inventory["coverage"]["undocumented_canonical_skills"] == [
        "kai-brand-pulse",
        "kai-content-batching",
        "kai-funnel-audit",
        "kai-gtm-pack",
        "kai-hook-bench",
        "kai-offer-builder",
        "kai-proof-builder",
        "kai-retro",
    ]


def test_router_parser_only_counts_unique_categorized_table_rows(tmp_path):
    _minimal_tree(tmp_path)
    commands = manifest.parse_router_commands(tmp_path / manifest.ROUTER_PATH)
    assert commands == [
        {"name": "kai-alpha", "category": "produce", "description": "Alpha workflow"}
    ]


def test_generated_manifest_is_deterministic_and_detects_added_skill(tmp_path):
    _minimal_tree(tmp_path)
    first = manifest.discover_inventory(tmp_path)
    second = manifest.discover_inventory(tmp_path)
    assert manifest.render_json(first) == manifest.render_json(second)

    manifest.generate(tmp_path)
    assert manifest.check_manifest(tmp_path) == []
    artifact = json.loads((tmp_path / manifest.ARTIFACT_PATH).read_text(encoding="utf-8"))
    assert artifact["counts"]["canonical_kai_skills"] == 1

    _write(
        tmp_path / "harness/skills/kai-beta/SKILL.md",
        "---\nname: kai-beta\ndescription: Beta skill\n---\n# Beta\n",
    )
    errors = manifest.check_manifest(tmp_path)
    assert any("capability-manifest.json is stale" in error for error in errors)
    assert any("AGENTS.md capability-count block is stale" in error for error in errors)


def test_checked_in_artifact_and_generated_blocks_are_current():
    assert manifest.check_manifest(REPO_ROOT) == []


def test_checked_in_artifact_matches_live_discovery_byte_for_byte():
    expected = manifest.render_json(manifest.discover_inventory(REPO_ROOT))
    actual = (REPO_ROOT / manifest.ARTIFACT_PATH).read_text(encoding="utf-8")
    assert actual == expected


def test_runtime_capability_endpoint_uses_live_generated_inventory():
    from gateway.routers.runtime import list_capabilities

    response = asyncio.run(list_capabilities())
    assert response == manifest.discover_inventory(REPO_ROOT)
    assert response["coverage"]["unresolved_router_commands"] == []
