from pathlib import Path

from scripts.quality_gates.mutation_risk_lint import lint_file


def test_mutation_risk_flags_live_send_without_approval(tmp_path: Path) -> None:
    artifact = tmp_path / "sequence.md"
    artifact.write_text("Send the email sequence to the imported lead list tomorrow.\n")

    issues = lint_file(artifact)

    assert len(issues) == 1
    assert "approval" in issues[0].message.lower()


def test_mutation_risk_allows_dry_run_proposal(tmp_path: Path) -> None:
    artifact = tmp_path / "sequence.md"
    artifact.write_text(
        "Dry-run only. Approval required before launch.\n"
        "Send the email sequence after the lifecycle owner approves it.\n"
    )

    issues = lint_file(artifact)

    assert issues == []
