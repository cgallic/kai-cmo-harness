"""Regression tests for cross-agent seams around harness_cli/harness_discord.

1. The Discord handler shells out to scripts/harness_cli.py BY PATH
   (get_harness_script()), from an arbitrary cwd. harness_cli must therefore
   bootstrap sys.path for direct invocation — without it every `!harness run`
   died at import time with ModuleNotFoundError: No module named 'scripts'.

2. Discord report/status formatters read the canonical content log, whose
   performance_30d field drifted (dict | legacy str | None). They must never
   crash on a legacy string grade.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
HARNESS_CLI = REPO_ROOT / "scripts" / "harness_cli.py"


class TestHarnessCliDirectInvocation:
    def test_direct_path_invocation_from_foreign_cwd(self, tmp_path):
        """python3 <abs path>/scripts/harness_cli.py --help must work from any
        cwd — this is exactly how harness_discord.run_harness and the
        `!harness run` background command invoke it."""
        result = subprocess.run(
            [sys.executable, str(HARNESS_CLI), "--help"],
            cwd=tmp_path,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr
        assert "No module named 'scripts'" not in result.stderr

    def test_module_form_still_works(self):
        """kai-start SKILL.md documents `python -m scripts.harness_cli` —
        the direct-path bootstrap must not break the module form."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.harness_cli", "--help"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=60,
        )
        assert result.returncode == 0, result.stderr


class TestDiscordFormattersTolerateLegacyGrades:
    def _log_with_string_grade(self, tmp_path):
        log_file = tmp_path / "content_log.json"
        log_file.write_text(json.dumps([
            {
                "id": "kaicalls-legacy-1",
                "url": "https://kaicalls.com/blog/a",
                "keyword": "answering service",
                "title": "Legacy string winner",
                "site": "kaicalls",
                "format": "blog",
                "performance_30d": "winner",  # legacy string form
                "status": "published",
            },
            {
                "id": "kaicalls-unmeasured-2",
                "url": "https://kaicalls.com/blog/b",
                "keyword": "after hours calls",
                "title": "Not yet measured",
                "site": "kaicalls",
                "format": "blog",
                "performance_30d": None,
                "status": "published",
            },
        ]))
        return log_file

    def test_format_report_handles_string_and_none_grades(self, tmp_path, monkeypatch):
        import scripts.content.harness_discord as hd

        monkeypatch.setattr(hd, "CONTENT_LOG", str(self._log_with_string_grade(tmp_path)))
        report = hd.format_report(site="kaicalls")
        assert "WINNER" in report
        assert "PENDING" in report

    def test_is_winner_tolerates_string_grade(self):
        """pattern_extract.is_winner aborts the whole weekly winner loop on
        the first AttributeError — a legacy str grade must just be non-win."""
        grades_mod = __import__(
            "scripts.self_improvement.grades", fromlist=["get_grade"]
        )
        # is_winner lives in pattern_extract, which imports google.genai at
        # module level (unavailable in some CI environments) — exercise the
        # shared helper it now routes through, plus the module when possible.
        assert grades_mod.get_grade({"performance_30d": "winner"}) == "winner"
        assert grades_mod.get_grade({"performance_30d": "loser"}) == "underperformer"
        try:
            from scripts.self_improvement.pattern_extract import is_winner
        except ImportError:
            return  # google.genai missing here; covered by helper assertions
        assert is_winner({"platform": "web", "performance_30d": "winner"}) is False
        assert is_winner({"platform": "web", "performance_30d": None}) is False
