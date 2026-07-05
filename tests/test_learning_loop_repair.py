"""Learning-loop repair tests: grade vocabulary + schema drift.

The 30-day grader (performance_check.py) writes performance_30d as a dict
{"gsc": ..., "ga4": ..., "grade": "winner|average|underperformer", ...},
but several readers historically compared it as a string, filtered on a
"loser" grade that was never produced, or read a publish_date field the
content log never writes. These tests pin the repaired behavior:

- get_grade() tolerates performance_30d as dict, legacy string, legacy
  "loser" alias, or None/missing.
- get_published_at() falls back to the legacy publish_date field.
- `lesson_capture.py losers` surfaces entries graded "underperformer".
- get_pending_checks()/reconcile_pending_checks() skip url-less entries
  (approved_unpublished), keeping EC-12 reconciliation otherwise intact.
- performance_dashboard / report_cli / tracker_cli count dict-shaped grades.
"""

import argparse
import json
import sys
from pathlib import Path

import pytest

from scripts.self_improvement.grades import (
    GRADE_AVERAGE,
    GRADE_UNDERPERFORMER,
    GRADE_WINNER,
    get_grade,
    get_published_at,
)


# ---------------------------------------------------------------------------
# get_grade / get_published_at
# ---------------------------------------------------------------------------


class TestGetGrade:
    def test_dict_schema(self):
        entry = {"performance_30d": {"gsc": {}, "ga4": {}, "grade": "winner",
                                     "checked_at": "2026-07-01T00:00:00+00:00"}}
        assert get_grade(entry) == GRADE_WINNER

    def test_legacy_string_schema(self):
        assert get_grade({"performance_30d": "average"}) == GRADE_AVERAGE

    def test_none_and_missing(self):
        assert get_grade({"performance_30d": None}) is None
        assert get_grade({}) is None

    def test_legacy_loser_alias_normalized(self):
        assert get_grade({"performance_30d": {"grade": "loser"}}) == GRADE_UNDERPERFORMER
        assert get_grade({"performance_30d": "loser"}) == GRADE_UNDERPERFORMER

    def test_dict_without_grade(self):
        assert get_grade({"performance_30d": {"gsc": {"clicks": 5}}}) is None

    def test_non_dict_entry(self):
        assert get_grade(None) is None
        assert get_grade("winner") is None

    def test_case_and_whitespace_normalized(self):
        assert get_grade({"performance_30d": {"grade": " Winner "}}) == GRADE_WINNER

    def test_non_string_grade_ignored(self):
        assert get_grade({"performance_30d": {"grade": 3}}) is None


class TestGetPublishedAt:
    def test_published_at_preferred(self):
        entry = {"published_at": "2026-06-01T00:00:00+00:00",
                 "publish_date": "2020-01-01"}
        assert get_published_at(entry) == "2026-06-01T00:00:00+00:00"

    def test_falls_back_to_legacy_publish_date(self):
        assert get_published_at({"publish_date": "2026-05-05"}) == "2026-05-05"

    def test_missing_returns_none(self):
        assert get_published_at({}) is None
        assert get_published_at(None) is None


# ---------------------------------------------------------------------------
# lesson_capture losers — must surface "underperformer", the grade the
# checker actually writes (never "loser")
# ---------------------------------------------------------------------------


class TestLessonCaptureLosers:
    @pytest.fixture
    def lc(self, tmp_path, monkeypatch):
        from scripts.self_improvement import lesson_capture as mod

        content_log = tmp_path / "content_log.json"
        antipatterns = tmp_path / "what-doesnt-work.md"
        monkeypatch.setenv("KAI_CONTENT_LOG", str(content_log))
        monkeypatch.setattr(mod, "ANTIPATTERNS_PATH", antipatterns)
        return mod, content_log, antipatterns

    def _entry(self, entry_id, grade, **overrides):
        entry = {
            "id": entry_id,
            "format": "blog",
            "keyword": "ai receptionist",
            "published_at": "2026-06-01T00:00:00+00:00",
            "performance_30d": {"gsc": {"clicks": 1}, "ga4": {}, "grade": grade,
                                "checked_at": "2026-07-01T00:00:00+00:00"},
        }
        entry.update(overrides)
        return entry

    def _run(self, mod, capsys):
        rc = mod.cmd_losers(argparse.Namespace())
        out = capsys.readouterr().out
        return rc, out

    def test_underperformer_entries_surface(self, lc, capsys):
        mod, content_log, _ = lc
        content_log.write_text(json.dumps([
            self._entry("under-1", "underperformer"),
            self._entry("win-1", "winner"),
            self._entry("avg-1", "average"),
        ]))
        rc, out = self._run(mod, capsys)
        assert rc == 0
        assert "1 published piece(s) graded 'underperformer'" in out
        assert "under-1" in out
        assert "win-1" not in out
        assert "avg-1" not in out

    def test_legacy_loser_grades_still_surface(self, lc, capsys):
        mod, content_log, _ = lc
        content_log.write_text(json.dumps([
            self._entry("legacy-dict", "loser"),
            {"id": "legacy-str", "format": "blog", "keyword": "k",
             "published_at": "2026-06-01T00:00:00+00:00",
             "performance_30d": "loser"},
        ]))
        _, out = self._run(mod, capsys)
        assert "legacy-dict" in out
        assert "legacy-str" in out

    def test_diagnosed_entries_excluded(self, lc, capsys):
        mod, content_log, antipatterns = lc
        content_log.write_text(json.dumps([
            self._entry("under-1", "underperformer"),
            self._entry("under-2", "underperformer"),
        ]))
        antipatterns.write_text("## Measured losers\n- [2026-07-01] blog/all: under-1 diagnosed\n")
        _, out = self._run(mod, capsys)
        assert "under-1" not in out
        assert "under-2" in out

    def test_published_at_printed_with_publish_date_fallback(self, lc, capsys):
        mod, content_log, _ = lc
        current = self._entry("under-1", "underperformer")
        legacy = self._entry("under-2", "underperformer")
        del legacy["published_at"]
        legacy["publish_date"] = "2026-04-04"
        content_log.write_text(json.dumps([current, legacy]))
        _, out = self._run(mod, capsys)
        assert "published=2026-06-01T00:00:00+00:00" in out
        assert "published=2026-04-04" in out
        assert "published=None" not in out

    def test_no_underperformers_message(self, lc, capsys):
        mod, content_log, _ = lc
        content_log.write_text(json.dumps([self._entry("win-1", "winner")]))
        rc, out = self._run(mod, capsys)
        assert rc == 0
        assert "No undiagnosed underperformers" in out


# ---------------------------------------------------------------------------
# performance_check — url-less entries must never be scheduled or pulled
# ---------------------------------------------------------------------------


class TestPendingChecksSkipNullUrl:
    @pytest.fixture
    def perf(self, tmp_path, monkeypatch):
        from scripts.self_improvement import performance_check as pc

        content_log = tmp_path / "content_log.json"
        checks_dir = tmp_path / "pending_checks"
        checks_dir.mkdir()
        monkeypatch.setattr(pc, "CONTENT_LOG", str(content_log))
        monkeypatch.setattr(pc, "PENDING_CHECKS_DIR", str(checks_dir))
        return pc, content_log, checks_dir

    @staticmethod
    def _check(checks_dir, name, **fields):
        data = {
            "id": name,
            "url": f"https://example.com/{name}",
            "keyword": "k",
            "site": "kaicalls",
            "check_due": "2020-01-01T00:00:00+00:00",  # long past due
            "status": "pending",
        }
        data.update(fields)
        (checks_dir / f"{name}.json").write_text(json.dumps(data))

    def test_get_pending_checks_skips_null_or_missing_url(self, perf):
        pc, _, checks_dir = perf
        self._check(checks_dir, "live")
        self._check(checks_dir, "null-url", url=None)
        no_url = {"id": "no-url-key", "keyword": "k", "site": "kaicalls",
                  "check_due": "2020-01-01T00:00:00+00:00", "status": "pending"}
        (checks_dir / "no-url-key.json").write_text(json.dumps(no_url))

        due = pc.get_pending_checks()
        assert [c["id"] for _, c in due] == ["live"]

    def test_get_pending_checks_still_honors_status_and_due(self, perf):
        pc, _, checks_dir = perf
        self._check(checks_dir, "done", status="done")
        self._check(checks_dir, "future", check_due="2999-01-01T00:00:00+00:00")
        self._check(checks_dir, "due")
        due = pc.get_pending_checks()
        assert [c["id"] for _, c in due] == ["due"]

    def test_reconcile_skips_approved_unpublished_null_url(self, perf):
        pc, content_log, checks_dir = perf
        entries = [
            {
                "id": "unpublished-1",
                "url": None,
                "status": "approved_unpublished",
                "keyword": "k",
                "site": "kaicalls",
                "published_at": "2026-06-01T00:00:00+00:00",
                "performance_30d": None,
            },
            {
                "id": "live-1",
                "url": "https://example.com/live",
                "keyword": "k",
                "site": "kaicalls",
                "published_at": "2026-06-01T00:00:00+00:00",
            },
        ]
        content_log.write_text(json.dumps(entries))
        assert pc.reconcile_pending_checks() == 1
        assert sorted(f.stem for f in checks_dir.glob("*.json")) == ["live-1"]


# ---------------------------------------------------------------------------
# EC-15 — baseline-relative grading (absolute behavior preserved bit-for-bit
# when no baseline exists; relative context added when one does)
# ---------------------------------------------------------------------------


class TestBaselineRelativeGrading:
    @pytest.fixture
    def pc(self):
        from scripts.self_improvement import performance_check as pc

        return pc

    def test_absolute_grading_unchanged_without_baseline(self, pc):
        """No baseline -> result is EXACTLY the historical dict (same keys,
        same values) for winner / average / underperformer inputs."""
        cases = [
            (  # winner
                {"position": pc.WIN_POSITION, "ctr": pc.WIN_CTR, "impressions": 500,
                 "clicks": 25},
                {"avg_session_duration": pc.WIN_TIME_ON_PAGE},
                {"is_winner": True, "is_underperformer": False, "grade": "winner"},
            ),
            (  # average
                {"position": 12, "ctr": 0.03, "impressions": 50, "clicks": 2},
                {"avg_session_duration": 10},
                {"is_winner": False, "is_underperformer": False, "grade": "average"},
            ),
            (  # underperformer: no position at all
                {"position": None, "ctr": 0, "impressions": 0, "clicks": 0},
                {},
                {"is_winner": False, "is_underperformer": True,
                 "grade": "underperformer"},
            ),
            (  # underperformer: position > 20
                {"position": 25, "ctr": 0.015, "impressions": 200, "clicks": 3},
                {},
                {"is_winner": False, "is_underperformer": True,
                 "grade": "underperformer"},
            ),
        ]
        for gsc, ga4, expected in cases:
            assert pc.evaluate_performance({"url": "u", "keyword": "k"}, gsc, ga4) == expected

    def test_relative_context_added_with_baseline(self, pc):
        baseline = {"gsc": {"clicks": 30, "impressions": 1000, "window_days": 28},
                    "captured_at": "2026-06-05T00:00:00+00:00"}
        gsc = {"position": 12, "ctr": 0.03, "impressions": 100, "clicks": 3}
        result = pc.evaluate_performance(
            {"url": "u", "keyword": "k"}, gsc, {"avg_session_duration": 10},
            baseline=baseline,
        )
        rel = result["baseline_relative"]
        assert rel["site_clicks_at_publish"] == 30
        assert rel["click_share"] == 0.1
        assert rel["impression_share"] == 0.1
        assert rel["baseline_captured_at"] == "2026-06-05T00:00:00+00:00"
        assert result["grade"] == "average"  # absolute grade unchanged here

    def test_underperformer_softened_when_page_carries_site_share(self, pc):
        """Position 25 is an absolute underperformer, but the page holds 10%
        of site clicks — the trough is site-wide (EC-15), so grade average."""
        baseline = {"gsc": {"clicks": 30, "impressions": 1000, "window_days": 28},
                    "captured_at": "2026-06-05T00:00:00+00:00"}
        gsc = {"position": 25, "ctr": 0.015, "impressions": 200, "clicks": 3}
        result = pc.evaluate_performance(
            {"url": "u", "keyword": "k"}, gsc, {}, baseline=baseline
        )
        assert result["grade"] == "average"
        assert result["is_underperformer"] is False
        assert result["regraded_by_baseline"] is True

    def test_underperformer_kept_when_share_below_threshold(self, pc):
        baseline = {"gsc": {"clicks": 1000, "impressions": 50000, "window_days": 28},
                    "captured_at": "2026-06-05T00:00:00+00:00"}
        gsc = {"position": 25, "ctr": 0.015, "impressions": 200, "clicks": 3}
        result = pc.evaluate_performance(
            {"url": "u", "keyword": "k"}, gsc, {}, baseline=baseline
        )
        assert result["grade"] == "underperformer"
        assert result["baseline_relative"]["click_share"] == 0.003
        assert "regraded_by_baseline" not in result

    def test_unavailable_baseline_treated_as_absent(self, pc):
        baseline = {"status": "unavailable", "reason": "No GSC credentials",
                    "captured_at": "2026-06-05T00:00:00+00:00"}
        gsc = {"position": 25, "ctr": 0.015, "impressions": 200, "clicks": 3}
        result = pc.evaluate_performance(
            {"url": "u", "keyword": "k"}, gsc, {}, baseline=baseline
        )
        # A data gap never becomes numbers: exact absolute behavior.
        assert result == {"is_winner": False, "is_underperformer": True,
                          "grade": "underperformer"}

    def test_zero_site_clicks_yields_null_share_and_no_regrade(self, pc):
        baseline = {"gsc": {"clicks": 0, "impressions": 0, "window_days": 28},
                    "captured_at": "2026-06-05T00:00:00+00:00"}
        gsc = {"position": None, "ctr": 0, "impressions": 0, "clicks": 0}
        result = pc.evaluate_performance(
            {"url": "u", "keyword": "k"}, gsc, {}, baseline=baseline
        )
        assert result["baseline_relative"]["click_share"] is None
        assert result["grade"] == "underperformer"


class TestRunCheckBaselineWiring:
    @pytest.fixture
    def perf(self, tmp_path, monkeypatch):
        from scripts.self_improvement import performance_check as pc

        content_log = tmp_path / "content_log.json"
        checks_dir = tmp_path / "pending_checks"
        checks_dir.mkdir()
        monkeypatch.setattr(pc, "CONTENT_LOG", str(content_log))
        monkeypatch.setattr(pc, "PENDING_CHECKS_DIR", str(checks_dir))
        monkeypatch.setattr(pc, "post_to_discord", lambda *a, **k: None)
        monkeypatch.setattr(pc, "retro_score_content", lambda *a, **k: None)
        monkeypatch.setattr(
            pc, "pull_gsc_data",
            lambda url, keyword, site: {"position": 25, "ctr": 0.015,
                                        "impressions": 200, "clicks": 3},
        )
        monkeypatch.setattr(pc, "pull_ga4_data", lambda url, site: {"sessions": 4})
        return pc, content_log, checks_dir

    def _seed(self, pc, content_log, checks_dir, baseline=None):
        entry = {
            "id": "kaicalls-20260601-000000",
            "url": "https://kaicalls.com/blog/x",
            "keyword": "k",
            "site": "kaicalls",
            "published_at": "2026-06-01T00:00:00+00:00",
            "performance_30d": None,
        }
        if baseline is not None:
            entry["baseline"] = baseline
        content_log.write_text(json.dumps([entry]))
        check = {
            "id": entry["id"], "url": entry["url"], "keyword": "k",
            "site": "kaicalls", "published_at": entry["published_at"],
            "check_due": "2026-07-01T00:00:00+00:00", "status": "pending",
        }
        check_file = checks_dir / f"{entry['id']}.json"
        check_file.write_text(json.dumps(check))
        return check_file, check

    def test_performance_30d_schema_unchanged_without_baseline(self, perf):
        """All existing entries have no baseline — their written record must
        be identical to today's shape (no new keys, absolute grade)."""
        pc, content_log, checks_dir = perf
        check_file, check = self._seed(pc, content_log, checks_dir)
        pc.run_check(check_file, check, dry_run=False)
        entry = json.loads(content_log.read_text())[0]
        perf30 = entry["performance_30d"]
        assert set(perf30.keys()) == {"gsc", "ga4", "grade", "checked_at"}
        assert perf30["grade"] == "underperformer"
        assert perf30["gsc"] == {"position": 25, "ctr": 0.015,
                                 "impressions": 200, "clicks": 3}

    def test_performance_30d_carries_baseline_relative(self, perf):
        pc, content_log, checks_dir = perf
        baseline = {"gsc": {"clicks": 30, "impressions": 1000, "window_days": 28},
                    "captured_at": "2026-06-01T00:00:00+00:00"}
        check_file, check = self._seed(pc, content_log, checks_dir, baseline=baseline)
        pc.run_check(check_file, check, dry_run=False)
        entry = json.loads(content_log.read_text())[0]
        perf30 = entry["performance_30d"]
        assert perf30["baseline_relative"]["click_share"] == 0.1
        assert perf30["baseline_relative"]["site_clicks_at_publish"] == 30
        # 10% of site clicks vetoes the absolute "underperformer" verdict.
        assert perf30["grade"] == "average"


# ---------------------------------------------------------------------------
# performance_dashboard — dict-shaped grades + published_at
# ---------------------------------------------------------------------------


class TestPerformanceDashboard:
    @pytest.fixture
    def dash(self, tmp_path, monkeypatch):
        from scripts.analytics import performance_dashboard as pd_mod

        log_path = tmp_path / "content-log.jsonl"
        monkeypatch.setattr(pd_mod, "CONTENT_LOG", log_path)
        monkeypatch.setattr(pd_mod, "QUALITY_LOG", tmp_path / "content-quality.jsonl")
        return pd_mod, log_path

    @staticmethod
    def _write_jsonl(path, entries):
        path.write_text("\n".join(json.dumps(e) for e in entries) + "\n")

    def test_weekly_summary_counts_dict_grades(self, dash):
        pd_mod, log_path = dash
        self._write_jsonl(log_path, [
            {"id": "w", "published_at": "2026-06-01T00:00:00+00:00",
             "performance_30d": {"grade": "winner", "gsc": {}}},
            {"id": "a", "published_at": "2026-06-01T00:00:00+00:00",
             "performance_30d": "average"},  # legacy string still counted
            {"id": "u", "published_at": "2026-06-01T00:00:00+00:00",
             "performance_30d": {"grade": "underperformer"}},
            {"id": "p", "published_at": "2026-06-01T00:00:00+00:00"},
        ])
        perf = pd_mod.weekly_summary()["performance"]
        assert perf["winners"] == 1
        assert perf["average"] == 1
        assert perf["underperformers"] == 1
        assert perf["pending"] == 1
        assert perf["win_rate"] == "33%"

    def test_weekly_summary_uses_published_at(self, dash):
        from datetime import datetime, timedelta, timezone

        pd_mod, log_path = dash
        recent = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        self._write_jsonl(log_path, [
            {"id": "new", "published_at": recent},
            {"id": "old", "published_at": "2020-01-01T00:00:00+00:00"},
            {"id": "legacy", "publish_date": recent},  # legacy field counts too
        ])
        summary = pd_mod.weekly_summary()
        assert summary["content_published_this_week"] == 2

    def test_trend_analysis_counts_dict_grades(self, dash):
        pd_mod, log_path = dash
        self._write_jsonl(log_path, [
            {"id": "w", "published_at": "2026-06-01T00:00:00+00:00",
             "performance_30d": {"grade": "winner"}},
            {"id": "u", "published_at": "2026-06-01T00:00:00+00:00",
             "performance_30d": {"grade": "underperformer"}},
        ])
        trends = pd_mod.trend_analysis(weeks=520)
        assert trends["total_published"] == 2
        assert trends["total_winners"] == 1
        week = trends["weekly_trend"][-1]
        assert week["graded"] == 2
        assert week["win_rate"] == "50%"


# ---------------------------------------------------------------------------
# report_cli / tracker_cli — dict-shaped grades in report buckets
# ---------------------------------------------------------------------------


class TestReportCli:
    def test_text_report_counts_dict_grades(self, monkeypatch, capsys):
        from scripts.content import report_cli as rc

        entries = [
            # No url/keyword → the CLI never attempts a live GSC/GA4 pull.
            {"id": "w1", "keyword": "", "url": "",
             "performance_30d": {"grade": "winner", "gsc": {}}},
            {"id": "u1", "keyword": "", "url": "",
             "performance_30d": "loser"},  # legacy alias → underperformer
            {"id": "p1", "keyword": "", "url": ""},
        ]
        monkeypatch.setattr(rc, "_load_content_log", lambda: entries)
        monkeypatch.setattr(sys, "argv", ["report_cli.py"])
        rc.main()
        out = capsys.readouterr().out
        assert "Winners: 1" in out
        assert "Under: 1" in out
        assert "Pending: 1" in out
        assert "[+] w1" in out
        assert "(underperformer)" in out


class TestTrackerCli:
    def test_report_counts_dict_grades(self, monkeypatch, capsys):
        from scripts.content import tracker_cli as tc

        entries = [
            {"id": "learning-loop-test-w1", "keyword": "", "url": "",
             "performance_30d": {"grade": "winner", "gsc": {}}},
            {"id": "learning-loop-test-u1", "keyword": "", "url": "",
             "performance_30d": {"grade": "underperformer"}},
            {"id": "learning-loop-test-p1", "keyword": "", "url": ""},
        ]
        monkeypatch.setattr(tc, "_load_log", lambda: entries)
        rc = tc.cmd_report(argparse.Namespace(site=None, format="text"))
        out = capsys.readouterr().out
        assert rc == 0
        assert "Winners: 1" in out
        assert "Under: 1" in out
        assert "Pending: 1" in out
