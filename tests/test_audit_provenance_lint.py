from pathlib import Path

from scripts.quality_gates.audit_provenance_lint import iter_audit_files, lint_text


def test_unsourced_risky_numeric_claim_fails(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("The firm has 63 reviews and ranks top 3 for injury lawyer.\n")

    issues = lint_text(report, report.read_text())

    assert any(issue.code == "UNSOURCED_NUMERIC_CLAIM" for issue in issues)


def test_sourced_risky_numeric_claim_passes(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text(
        "Source: Google Places API, retrieved 2026-05-05\n"
        "The firm has 63 reviews.\n"
    )

    issues = lint_text(report, report.read_text())

    assert issues == []


def test_guessed_language_fails(tmp_path: Path) -> None:
    report = tmp_path / "report.md"
    report.write_text("This is an educated guess from search snippets.\n")

    issues = lint_text(report, report.read_text())

    assert any(issue.code == "UNVERIFIED_LANGUAGE" for issue in issues)


def test_audit_dir_requires_sources_and_gaps(tmp_path: Path) -> None:
    (tmp_path / "_executive-summary.md").write_text("No risky claims.\n")

    files, issues = iter_audit_files([tmp_path], audit_dir=True)

    assert files == [tmp_path / "_executive-summary.md"]
    assert {issue.code for issue in issues} == {"MISSING_AUDIT_FILE"}
    assert {Path(issue.file).name for issue in issues} == {"_data-sources.md", "_data-gaps.md"}
