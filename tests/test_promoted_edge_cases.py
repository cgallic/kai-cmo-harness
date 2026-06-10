"""Tests for edge cases promoted from memory/edge-cases.md into code.

Each test class names the registry entry it enforces. If one of these fails,
either the enforcement regressed or the edge case changed — update both the
code and the registry entry together.
"""

import json
from pathlib import Path

import pytest

from scripts.content.placeholders import find_placeholders
from scripts.self_improvement.safe_write import guarded_write_text, safe_write_yaml


class TestEC06PlaceholderDetection:
    """EC-06: placeholder detection must catch natural language, not just brackets."""

    def test_bracketed_placeholder_caught(self):
        assert "[company name]" in find_placeholders("Call [company name] today.")

    def test_markdown_link_not_flagged(self):
        assert find_placeholders("Read [our pricing page](/pricing) for details.") == []

    def test_insert_your_phrase_caught(self):
        hits = find_placeholders("To get started, insert your company name in the header.")
        assert any("insert your company" in h.lower() for h in hits)

    def test_your_x_here_caught(self):
        hits = find_placeholders("Welcome to Your Business Name Here, the best in town.")
        assert hits

    def test_tbd_and_lorem_caught(self):
        assert find_placeholders("Pricing: TBD")
        assert find_placeholders("Lorem ipsum dolor sit amet.")

    def test_curly_template_caught(self):
        assert find_placeholders("Hi {company_name}, welcome aboard.")
        assert find_placeholders("Hi {{ first name }}, welcome.")

    def test_angle_bracket_placeholder_caught(self):
        assert find_placeholders("Contact <your company> for a quote.")

    def test_clean_copy_passes(self):
        clean = (
            "Rodriguez Air missed 19 calls a week between 6pm and 8am. "
            "Each missed emergency call in Mesa averages $410 in lost revenue. "
            "[See the full case study](/case-studies/rodriguez-air) for the 60-day numbers."
        )
        assert find_placeholders(clean) == []

    def test_html_tags_not_flagged(self):
        assert find_placeholders("<strong>Bold claim</strong> with a <title> tag.") == []


class TestEC11SafeDefaultsRewrite:
    """EC-11: automated rewrites of MARKETING.md / policy YAML must validate, not clobber."""

    def test_yaml_write_round_trips(self, tmp_path):
        target = tmp_path / "policy.yaml"
        ok, _ = safe_write_yaml(target, {"auto_approve_above": 85, "reject_below": 60})
        assert ok
        import yaml

        assert yaml.safe_load(target.read_text())["auto_approve_above"] == 85

    def test_yaml_write_backs_up_existing(self, tmp_path):
        target = tmp_path / "policy.yaml"
        target.write_text("auto_approve_above: 85\n")
        ok, _ = safe_write_yaml(target, {"auto_approve_above": 90})
        assert ok
        assert (tmp_path / "policy.yaml.bak").read_text() == "auto_approve_above: 85\n"

    def test_unserializable_data_refused_and_original_intact(self, tmp_path):
        target = tmp_path / "policy.yaml"
        original = "auto_approve_above: 85\n"
        target.write_text(original)
        ok, msg = safe_write_yaml(target, {"bad": object()})
        assert not ok
        assert "refused" in msg
        assert target.read_text() == original

    def test_text_rewrite_normal_case(self, tmp_path):
        target = tmp_path / "MARKETING.md"
        target.write_text("# Marketing Config\n\nsites: kaicalls\n")
        ok, _ = guarded_write_text(target, "# Marketing Config\n\nsites: kaicalls\n\n## Learned Defaults\n- x\n")
        assert ok
        assert "Learned Defaults" in target.read_text()

    def test_text_rewrite_refuses_truncation(self, tmp_path):
        target = tmp_path / "MARKETING.md"
        original = "# Marketing Config\n" + "site config line\n" * 100
        target.write_text(original)
        ok, msg = guarded_write_text(target, "# Marketing Config\noops")
        assert not ok
        assert "shrank" in msg
        assert target.read_text() == original

    def test_text_rewrite_refuses_lost_heading(self, tmp_path):
        target = tmp_path / "MARKETING.md"
        target.write_text("# Marketing Config\nbody\n")
        ok, msg = guarded_write_text(target, "totally unrelated content that is long enough\n")
        assert not ok
        assert "heading" in msg

    def test_text_rewrite_refuses_empty(self, tmp_path):
        target = tmp_path / "MARKETING.md"
        target.write_text("# Marketing Config\nbody\n")
        ok, _ = guarded_write_text(target, "   \n")
        assert not ok
        assert "Marketing Config" in target.read_text()


class TestEC12PendingCheckReconciliation:
    """EC-12: lost pending-check files must be rebuilt from the content log."""

    @pytest.fixture
    def perf(self, tmp_path, monkeypatch):
        from scripts.self_improvement import performance_check as pc

        content_log = tmp_path / "content_log.json"
        checks_dir = tmp_path / "pending_checks"
        monkeypatch.setattr(pc, "CONTENT_LOG", str(content_log))
        monkeypatch.setattr(pc, "PENDING_CHECKS_DIR", str(checks_dir))
        return pc, content_log, checks_dir

    def _entry(self, entry_id="abc123", **overrides):
        entry = {
            "id": entry_id,
            "url": "https://example.com/post",
            "keyword": "ai receptionist",
            "site": "kaicalls",
            "published_at": "2026-05-20T12:00:00+00:00",
        }
        entry.update(overrides)
        return entry

    def test_missing_check_file_recreated(self, perf):
        pc, content_log, checks_dir = perf
        content_log.write_text(json.dumps([self._entry()]))
        assert pc.reconcile_pending_checks() == 1
        check = json.loads((checks_dir / "abc123.json").read_text())
        assert check["status"] == "pending"
        assert check["reconciled"] is True
        assert check["check_due"].startswith("2026-06-19")  # published + 30 days

    def test_measured_entry_skipped(self, perf):
        pc, content_log, checks_dir = perf
        content_log.write_text(json.dumps([self._entry(performance_30d={"grade": "winner"})]))
        assert pc.reconcile_pending_checks() == 0
        assert not (checks_dir / "abc123.json").exists()

    def test_existing_check_file_untouched(self, perf):
        pc, content_log, checks_dir = perf
        content_log.write_text(json.dumps([self._entry()]))
        checks_dir.mkdir()
        (checks_dir / "abc123.json").write_text('{"status": "done"}')
        assert pc.reconcile_pending_checks() == 0
        assert json.loads((checks_dir / "abc123.json").read_text()) == {"status": "done"}

    def test_uncheckable_entry_skipped(self, perf):
        pc, content_log, checks_dir = perf
        content_log.write_text(json.dumps([self._entry(url=None)]))
        assert pc.reconcile_pending_checks() == 0

    def test_dry_run_writes_nothing(self, perf):
        pc, content_log, checks_dir = perf
        content_log.write_text(json.dumps([self._entry()]))
        assert pc.reconcile_pending_checks(dry_run=True) == 1
        assert not (checks_dir / "abc123.json").exists()
