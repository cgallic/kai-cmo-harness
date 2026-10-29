"""Outcome verdict runner — due tickets read through injected fetchers.

Missing credentials or data are inconclusive data gaps, never zeros.
"""

from __future__ import annotations

from datetime import date, datetime, timezone
from pathlib import Path

import pytest

from kai.runtime.eco import EcoFloors, EcoRecordStore
from scripts.self_improvement import outcome_measure as om

DUE = datetime(2026, 10, 20, tzinfo=timezone.utc)


@pytest.fixture
def store(tmp_path: Path) -> EcoRecordStore:
    return EcoRecordStore(base_dir=tmp_path / "eco", floors=EcoFloors.load())


def register(store, subject="content:a", work_type="blog-post", baseline=True, **receipt):
    return store.register_shipped(
        subject_id=subject, work_type=work_type, claimed_by="content_log", brand_id="kaicalls",
        shipped_at="2026-10-01T12:00:00+00:00",
        receipt={"url": "https://kaicalls.com/blog/a", "site": "kaicalls", **receipt},
        baseline={"metric": "clicks", "source": "google_search_console", "scope": "page",
                  "value": 0, "window_end": "2026-09-30"} if baseline else None,
    )


def fake(pre_value, post_value, calls=None):
    def fetch(ticket, start, end):
        if calls is not None:
            calls.append((start, end))
        return {"value": pre_value if end < date(2026, 10, 1) else post_value}
    return fetch


def test_windows_are_equal_length_and_exclude_ship_day():
    ticket = {"shipped_at": "2026-10-01T12:00:00+00:00", "window_days": 7}
    assert om.windows_for(ticket, 1) == (date(2026, 9, 24), date(2026, 9, 30), date(2026, 10, 2), date(2026, 10, 8))
    pre_start, pre_end, post_start, post_end = om.windows_for(ticket, 2)
    assert (pre_end - pre_start) == (post_end - post_start)
    assert (post_end - post_start).days + 1 == 14


def test_worked_read_is_verified_by_kai_measure(store):
    record = register(store)
    calls = []
    results = om.measure_due(store, fetchers={"gsc": fake(40, 120, calls)}, now=DUE)
    assert [r["verdict"] for r in results] == ["worked"]
    assert calls == [(date(2026, 9, 24), date(2026, 9, 30)), (date(2026, 10, 2), date(2026, 10, 8))]
    saved = store.get(record["record_id"])
    assert saved["computed"]["outcome"]["verdict_by"] == "kai-measure:gsc"
    assert saved["ticket"]["reads"][0]["verifier"] == "kai-measure:gsc"
    assert store.due_for_measurement(DUE) == []


def test_missing_fetcher_is_inconclusive_data_gap(store):
    register(store)
    results = om.measure_due(store, fetchers={}, now=DUE)
    assert results[0]["verdict"] == "inconclusive"
    assert "no fetcher" in results[0]["reason"]
    assert results[0]["final"] is False


def test_fetcher_error_or_crash_is_never_zero(store):
    record = register(store)

    def boom(ticket, start, end):
        raise RuntimeError("quota exhausted")

    om.measure_due(store, fetchers={"gsc": boom}, now=DUE)
    read = store.get(record["record_id"])["ticket"]["reads"][0]
    assert read["pre"] == {"error": "quota exhausted"}
    assert "value" not in read["post"]


def test_non_numeric_fetch_is_a_gap(store):
    register(store)
    results = om.measure_due(store, fetchers={"gsc": lambda t, s, e: {"value": None}}, now=DUE)
    assert results[0]["verdict"] == "inconclusive"


def test_default_gsc_fetcher_without_credentials_is_a_gap(store, monkeypatch):
    monkeypatch.delenv("GOOGLE_CREDENTIALS_PATH", raising=False)
    register(store)
    results = om.measure_due(store, now=DUE)
    assert results[0]["verdict"] == "inconclusive"
    assert "No GSC credentials" in results[0]["reason"]


def test_unmeasurable_tickets_are_never_read(store):
    register(store, baseline=False)
    assert om.measure_due(store, fetchers={"gsc": fake(1, 2)}, now=DUE) == []


def test_dry_run_reads_and_writes_nothing(store):
    record = register(store)
    calls = []
    results = om.measure_due(store, fetchers={"gsc": fake(1, 2, calls)}, now=DUE, dry_run=True)
    assert results[0]["dry_run"] is True and calls == []
    assert store.get(record["record_id"])["ticket"]["reads"] == []


def test_ads_fetcher_refuses_without_entity():
    assert "entity" in om.fetch_ads({"receipt": {}}, date(2026, 1, 1), date(2026, 1, 3))["error"]


def test_main_dry_run(store, monkeypatch, capsys):
    monkeypatch.setattr(om, "EcoRecordStore", lambda: store)
    assert om.main(["--dry-run"]) == 0
    assert "No outcome tickets due" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Review regressions (commit 8fa493e)
# ---------------------------------------------------------------------------


def test_windows_use_the_source_reporting_day():
    """Fix 5: shipped 03:00 UTC Oct 2 is Oct 1 in GSC's Pacific day — Oct 1 is in neither window."""
    ticket = {"shipped_at": "2026-10-02T03:00:00+00:00", "window_days": 7, "report_tz": "America/Los_Angeles"}
    assert om.windows_for(ticket, 1) == (date(2026, 9, 24), date(2026, 9, 30), date(2026, 10, 2), date(2026, 10, 8))


def test_one_failing_ticket_does_not_abort_the_run(store, monkeypatch):
    """Fix 4: an EcoError on one ticket is recorded and the run continues."""
    first = register(store, subject="content:a")
    register(store, subject="content:b")
    real_verify = store.verify

    def flaky(record_id, **kwargs):
        if record_id == first["record_id"]:
            raise om.EcoError("record corrupted")
        return real_verify(record_id, **kwargs)

    monkeypatch.setattr(store, "verify", flaky)
    results = om.measure_due(store, fetchers={"gsc": fake(40, 120)}, now=DUE)
    by_subject = {r["subject_id"]: r for r in results}
    assert by_subject["content:a"]["error"] == "record corrupted"
    assert by_subject["content:b"]["verdict"] == "worked"


def test_every_measured_source_in_floors_has_a_fetcher():
    """Fix 3: registration trusts floors' measured_sources; each must have a reader here."""
    measured = EcoFloors.load().outcome_verdicts["measured_sources"]
    assert measured and all(om.SOURCE_KEYS.get(source) in om.default_fetchers() for source in measured)
