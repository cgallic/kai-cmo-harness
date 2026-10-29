"""ECO outcome ledger — tally, misses, filters, method block, and the CLI.

Doctrine under test: "Outcome verdicts" in docs/system/eco-completion-standard.md
"""

from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path

import pytest

from kai.runtime.eco import EcoFloors, EcoRecordStore, build_ledger, render_json, render_markdown
from scripts.quality_gates import eco_gate

MEASURE = "kai-measure:gsc"


@pytest.fixture(scope="module")
def floors() -> EcoFloors:
    return EcoFloors.load()


@pytest.fixture
def store(tmp_path: Path, floors: EcoFloors) -> EcoRecordStore:
    return EcoRecordStore(base_dir=tmp_path / "eco", floors=floors)


def ticket(store, subject, *, brand="kaicalls", shipped="2026-10-01T12:00:00+00:00", baseline=True,
           work_type="blog-post", read=None):
    record = store.register_shipped(
        subject_id=subject, work_type=work_type, claimed_by="content_log", brand_id=brand, shipped_at=shipped,
        receipt={"url": f"https://kaicalls.com/{subject}"},
        baseline={"metric": "clicks", "source": "google_search_console", "value": 400,
                  "window_end": (date.fromisoformat(shipped[:10]) - timedelta(days=1)).isoformat()}
        if baseline else None,
    )
    if read:
        store.record_read(record["record_id"], verifier=MEASURE, pre={"value": read[0]}, post={"value": read[1]})
        store.verify(record["record_id"], verifier=MEASURE)
    return record


@pytest.fixture
def populated(store):
    ticket(store, "content:won", read=(400, 500))
    ticket(store, "content:partial", read=(400, 420))
    ticket(store, "content:flop", read=(400, 300))
    ticket(store, "content:waiting")
    ticket(store, "content:nobase", baseline=False)
    ticket(store, "content:other-brand", brand="acme", read=(400, 500))
    ticket(store, "content:old", shipped="2026-08-01T12:00:00+00:00", read=(400, 500))
    store.claim(subject_id="no-ticket", step_id="s", work_type="internal-research", claimed_by="a")
    return store


def test_tally_counts_each_verdict_and_skips_unticketed(populated, floors):
    ledger = build_ledger(populated.list_records(), floors=floors)
    assert ledger["tickets"] == 7
    tally = ledger["tally"]
    assert (tally["worked"], tally["partial"], tally["didnt_work"]) == (3, 1, 1)
    assert tally["pending"] == 1 and tally["unmeasurable"] == 1 and tally["inconclusive"] == 0
    assert ledger["win_rate"] == 0.6
    assert ledger["by_work_type"]["blog-post"]["worked"] == 3


def test_misses_are_listed_not_dropped(populated, floors):
    misses = {r["subject_id"]: r for r in build_ledger(populated.list_records(), floors=floors)["misses"]}
    assert set(misses) == {"content:partial", "content:flop"}
    assert misses["content:flop"]["lift"] == -0.25
    assert misses["content:flop"]["verdict_by"] == MEASURE


def test_unmeasurable_lists_its_reason(populated, floors):
    rows = build_ledger(populated.list_records(), floors=floors)["unmeasurable"]
    assert [r["subject_id"] for r in rows] == ["content:nobase"]
    assert rows[0]["reason"] == "no pre-ship baseline captured"


def test_verdict_comes_from_the_verdict_field_not_closed(populated, floors):
    """A didn't-work ticket on a CLOSED record is still a miss."""
    record = next(r for r in populated.list_records() if r["subject_id"] == "content:flop")
    record["computed"]["verdict"] = "CLOSED"
    rows = build_ledger([record], floors=floors)["rows"]
    assert rows[0]["status"] == "didnt_work"


def test_brand_and_since_filters(populated, floors):
    assert build_ledger(populated.list_records(), brand="acme", floors=floors)["tickets"] == 1
    assert build_ledger(populated.list_records(), since="2026-09-01", floors=floors)["tickets"] == 6
    with pytest.raises(ValueError):
        build_ledger(populated.list_records(), since="last tuesday")


def test_method_block_states_what_is_and_is_not_counted(populated, floors):
    method = build_ledger(populated.list_records(), floors=floors)["method"]
    for key in ("counted", "not_counted", "verifier", "audit", "disclosure", "attribution"):
        assert method[key]
    assert "Not third-party audited" in method["audit"]
    assert method["windows_days"]["paid-ad-campaign"] == 3
    assert method["windows_days"]["blog-post"] == 7


def test_renderers(populated, floors):
    ledger = build_ledger(populated.list_records(), floors=floors)
    md = render_markdown(ledger)
    assert "## Misses (partial and didn't work)" in md and "content:flop" in md and "## Method" in md
    assert json.loads(render_json(ledger))["tally"]["worked"] == 3


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


@pytest.fixture
def cli_env(tmp_path, monkeypatch):
    monkeypatch.setenv("KAI_RUNTIME_DIR", str(tmp_path / "runtime"))
    return tmp_path


def test_cli_register_is_idempotent_and_ledger_reads_it(cli_env, capsys):
    args = ["register", "--subject", "content:x", "--work-type", "blog-post", "--actor", "me",
            "--shipped-at", "2026-10-01T12:00:00Z",
            "--baseline", json.dumps({"metric": "clicks", "value": 10, "window_end": "2026-09-30"})]
    assert eco_gate.main(args) == 0
    assert eco_gate.main(args) == 0
    capsys.readouterr()
    assert eco_gate.main(["ledger", "--format", "json"]) == 0
    ledger = json.loads(capsys.readouterr().out)
    assert ledger["tickets"] == 1 and ledger["tally"]["pending"] == 1


def test_cli_register_rejects_a_smuggled_verdict(cli_env):
    assert eco_gate.main(["register", "--subject", "s", "--work-type", "blog-post", "--actor", "me",
                          "--receipt", json.dumps({"computed": {"verdict": "worked"}})]) == 2


def test_cli_unregistered_finds_executed_actions_without_tickets(cli_env, capsys):
    actions = cli_env / "runtime" / "actions"
    actions.mkdir(parents=True)
    (actions / "a1.json").write_text(json.dumps({
        "action_id": "a1", "execution_state": "completed", "channel": "social", "action_type": "publish_social_post",
        "result_summary": {"dry_run": False}, "executed_at": "2026-10-01T00:00:00Z"}))
    (actions / "a2.json").write_text(json.dumps({
        "action_id": "a2", "execution_state": "completed", "result_summary": {"dry_run": True}}))
    assert eco_gate.main(["unregistered", "--json"]) == 0
    found = json.loads(capsys.readouterr().out)
    assert [f["subject_id"] for f in found if f["subject_id"].startswith("action:")] == ["action:a1"]
