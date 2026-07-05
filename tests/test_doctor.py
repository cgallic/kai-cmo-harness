"""Tests for scripts/doctor.py — the trust anchor.

Doctor promises "referenced files exist, gates run, golden corpus passes".
These tests pin the referenced-files half: the instruction chain
(CLAUDE.md/AGENTS.md load-on-demand pointers, workspace core files, the
memory layer, and every path named in the AGENTS.md Framework Map and the
.claude/rules docs) must exist on the current tree, and doctor must FLAG a
missing referenced file rather than silently passing.
"""

from pathlib import Path

from scripts import doctor
from scripts.doctor import (
    INSTRUCTION_CHAIN_PATHS,
    REFERENCED_DOCS,
    Report,
    check_instruction_chain,
    check_required_paths,
    extract_repo_paths,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


# ── extract_repo_paths ──────────────────────────────────────────────────────


def test_extract_repo_paths_finds_inline_code_paths():
    md = "Load `knowledge/_index.md` and `harness/brief-schema.md` first."
    assert extract_repo_paths(md) == [
        "harness/brief-schema.md",
        "knowledge/_index.md",
    ]


def test_extract_repo_paths_strips_fenced_code_blocks():
    md = (
        "Real: `memory/lessons.md`\n"
        "```bash\n"
        "cat fenced/not-a-real-path.md\n"
        "`fenced/inline.md`\n"
        "```\n"
    )
    assert extract_repo_paths(md) == ["memory/lessons.md"]


def test_extract_repo_paths_skips_globs_ellipses_data_and_absolute():
    md = (
        "See `harness/references/*-organic-posting-rules.md` and "
        "`.../aeo-ai-search-playbook-2026.md` and "
        "`data/learning/gate_runs.jsonl` and `/tmp/draft.md` and `/kai`."
    )
    assert extract_repo_paths(md) == []


def test_extract_repo_paths_takes_script_path_from_python_commands():
    md = (
        "Run: `python scripts/quality_gates/four_us_score.py <file>` then "
        "`python -m scripts.audit.collect --url <url>` (module form skipped)."
    )
    assert extract_repo_paths(md) == ["scripts/quality_gates/four_us_score.py"]


# ── current tree passes ─────────────────────────────────────────────────────


def test_instruction_chain_passes_on_current_tree():
    report = Report()
    check_instruction_chain(report)
    assert report.failures == [], "\n".join(report.failures)
    assert any("instruction chain intact" in msg for msg in report.passes)


def test_required_paths_pass_on_current_tree():
    report = Report()
    check_required_paths(report)
    assert report.failures == [], "\n".join(report.failures)


def test_rules_files_exist_and_are_in_instruction_chain():
    for rel in (
        ".claude/rules/architecture-and-memory.md",
        ".claude/rules/scripts-and-tools.md",
    ):
        assert (REPO_ROOT / rel).exists(), f"{rel} missing"
        assert rel in INSTRUCTION_CHAIN_PATHS
        assert rel in REFERENCED_DOCS


# ── doctor flags missing referenced files ───────────────────────────────────


def _minimal_tree(root: Path) -> None:
    """Build a tree containing every instruction-chain core file."""
    for rel in INSTRUCTION_CHAIN_PATHS:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("# stub\n", encoding="utf-8")


def test_instruction_chain_flags_missing_core_file(tmp_path):
    _minimal_tree(tmp_path)
    (tmp_path / ".claude/rules/scripts-and-tools.md").unlink()

    report = Report()
    check_instruction_chain(report, root=tmp_path)

    assert any(
        "instruction chain broken" in msg and ".claude/rules/scripts-and-tools.md" in msg
        for msg in report.failures
    ), report.failures


def test_instruction_chain_flags_missing_framework_map_path(tmp_path):
    _minimal_tree(tmp_path)
    (tmp_path / "AGENTS.md").write_text(
        "# AGENTS.md\n\n"
        "| Task | Framework |\n|---|---|\n"
        "| Blog | `knowledge/frameworks/does-not-exist.md` |\n",
        encoding="utf-8",
    )

    report = Report()
    check_instruction_chain(report, root=tmp_path)

    assert any(
        "knowledge/frameworks/does-not-exist.md" in msg for msg in report.failures
    ), report.failures


def test_instruction_chain_clean_on_minimal_tree(tmp_path):
    _minimal_tree(tmp_path)
    report = Report()
    check_instruction_chain(report, root=tmp_path)
    assert report.failures == [], report.failures


def test_doctor_main_registers_instruction_chain_check():
    # main() must actually run the new check — guard against it being wired
    # up in tests but dropped from the entry point.
    import inspect

    assert "check_instruction_chain(report)" in inspect.getsource(doctor.main)
