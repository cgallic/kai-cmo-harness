"""Campaign identity + unified content log tests (Workstream D).

Covers:
  - campaign_id minting (cmp-YYYYMMDD-<slug>) and the planner --save flow:
    manifest.json carries the id, a campaign_tracker row is auto-created,
    and a campaign_plan artifact (the declared-but-never-used type in
    kai/runtime/models.py) is recorded in the RuntimeStore.
  - campaign_id threading: engine.generate(campaign_id=...) ->
    content_log.log_entry -> data/pending_checks/<id>.json.
  - migrate_legacy_log: ~/.kai-marketing/content-log.jsonl folded into the
    canonical data/content_log.json (publish_date -> published_at, dedupe by
    id/url, performance preserved, idempotent re-runs).
  - gateway job retention: 45-day configurable default that floors legacy
    days=7 callers so learning-loop lineage survives past the 30-day check.
"""

import asyncio
import json
import re
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.campaigns.campaign_planner as planner
import scripts.campaigns.campaign_tracker as tracker
import scripts.content.content_log as cl
from scripts.content.content_log import (
    compute_content_hash,
    load_log,
    log_entry,
    mark_published,
)
from scripts.content.migrate_legacy_log import migrate, normalize_legacy_entry

BODY = "Rodriguez Air missed 19 calls a week between 6pm and 8am. Each cost $410."

CAMPAIGN_ID_RE = re.compile(r"^cmp-\d{8}-[a-z0-9-]+$")


@pytest.fixture()
def sandbox(tmp_path, monkeypatch):
    """Isolate content log, pending checks, and calendar under tmp_path."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    log_file = data_dir / "content_log.json"
    calendar = data_dir / "content-calendar.md"
    monkeypatch.setattr(cl._CFG, "data_dir", data_dir)
    monkeypatch.setattr(cl, "LOG_FILE", str(log_file))
    monkeypatch.setenv("KAI_CONTENT_CALENDAR_PATH", str(calendar))
    monkeypatch.delenv("KAI_PUBLISH_ENABLED", raising=False)
    monkeypatch.setenv("CMO_CONFIG_PATH", str(tmp_path / "no-such-config.yaml"))
    return {
        "data_dir": data_dir,
        "log_file": str(log_file),
        "checks_dir": data_dir / "pending_checks",
        "calendar": calendar,
    }


def _checks(sandbox) -> list[Path]:
    checks_dir = sandbox["checks_dir"]
    return sorted(checks_dir.glob("*.json")) if checks_dir.exists() else []


# ---------------------------------------------------------------------------
# campaign_id minting
# ---------------------------------------------------------------------------


class TestMintCampaignId:
    def test_format(self):
        cid = planner.mint_campaign_id("Q3 Product Launch!", "ai receptionist")
        assert CAMPAIGN_ID_RE.match(cid)
        assert cid.endswith("-q3-product-launch")

    def test_date_prefix_uses_when(self):
        when = datetime(2026, 7, 5, tzinfo=timezone.utc)
        cid = planner.mint_campaign_id("Launch", when=when)
        assert cid == "cmp-20260705-launch"

    def test_falls_back_to_keyword_then_placeholder(self):
        when = datetime(2026, 7, 5, tzinfo=timezone.utc)
        assert planner.mint_campaign_id("", "AI CRM", when=when) == "cmp-20260705-ai-crm"
        assert planner.mint_campaign_id("", "", when=when) == "cmp-20260705-campaign"


# ---------------------------------------------------------------------------
# planner --save: manifest + tracker row + campaign_plan artifact
# ---------------------------------------------------------------------------


class TestPlannerSaveFlow:
    @pytest.fixture()
    def campaign_env(self, tmp_path, monkeypatch):
        # Never hit Gemini.
        monkeypatch.setattr(planner, "_gemini", lambda prompt: "stub asset content")
        # Tracker DB isolated.
        monkeypatch.setattr(tracker, "DATA_DIR", tmp_path / "campaigns-db")
        monkeypatch.setattr(tracker, "DB_PATH", tmp_path / "campaigns-db" / "campaigns.db")
        # Runtime store isolated.
        from kai.runtime.store import RuntimeStore

        store = RuntimeStore(base_dir=tmp_path / "runtime")
        monkeypatch.setattr("kai.runtime.get_default_runtime_store", lambda: store)
        return {"tmp": tmp_path, "store": store}

    def test_save_writes_manifest_tracker_and_artifact(self, campaign_env):
        save_dir = campaign_env["tmp"] / "camp"
        planner.generate_campaign(
            goal="Q3 Launch",
            product_id="kaicalls",
            keyword="ai receptionist",
            campaign_type="launch",
            save_dir=str(save_dir),
        )

        manifest = json.loads((save_dir / "manifest.json").read_text())
        cid = manifest["campaign_id"]
        assert CAMPAIGN_ID_RE.match(cid)

        # Tracker row auto-created and joinable by campaign_id.
        row = tracker.find_campaign(cid)
        assert row is not None
        assert row["campaign_id"] == cid
        assert row["name"] == cid
        assert row["product"] == "kaicalls"
        assert row["goal"] == "Q3 Launch"

        # campaign_plan artifact recorded with the id in its data payload.
        artifacts = [
            json.loads(p.read_text())
            for p in (campaign_env["tmp"] / "runtime" / "artifacts").glob("*.json")
        ]
        plans = [a for a in artifacts if a["artifact_type"] == "campaign_plan"]
        assert len(plans) == 1
        assert plans[0]["data"]["campaign_id"] == cid
        assert plans[0]["brand_id"] == "kaicalls"
        assert plans[0]["data"]["manifest"]["goal"] == "Q3 Launch"

    def test_explicit_campaign_id_is_respected(self, campaign_env):
        save_dir = campaign_env["tmp"] / "camp2"
        planner.generate_campaign(
            goal="Q3 Launch",
            product_id="kaicalls",
            keyword="ai receptionist",
            campaign_type="awareness",
            save_dir=str(save_dir),
            campaign_id="cmp-20260701-custom",
        )
        manifest = json.loads((save_dir / "manifest.json").read_text())
        assert manifest["campaign_id"] == "cmp-20260701-custom"
        assert tracker.find_campaign("cmp-20260701-custom") is not None

    def test_no_save_still_mints_but_writes_nothing(self, campaign_env, tmp_path):
        planner.generate_campaign(
            goal="Ad-hoc",
            product_id="kaicalls",
            keyword="k",
            campaign_type="awareness",
            save_dir=None,
        )
        assert tracker.find_campaign("cmp-nonexistent") is None
        assert not (tmp_path / "runtime" / "artifacts").exists() or not list(
            (tmp_path / "runtime" / "artifacts").glob("*.json")
        )

    def test_tracker_backfills_campaign_id_on_existing_row(self, campaign_env):
        tracker.create_campaign("legacy-name")
        tracker.create_campaign("legacy-name", campaign_id="cmp-20260705-late")
        row = tracker.find_campaign("cmp-20260705-late")
        assert row is not None and row["name"] == "legacy-name"

    def test_tracker_migrates_legacy_db_schema(self, campaign_env):
        # Simulate a pre-campaign_id database.
        tracker.DATA_DIR.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(tracker.DB_PATH))
        conn.execute("DROP TABLE IF EXISTS campaigns")
        conn.execute(
            "CREATE TABLE campaigns (id INTEGER PRIMARY KEY AUTOINCREMENT, "
            "name TEXT UNIQUE NOT NULL, campaign_type TEXT, goal TEXT, product TEXT, "
            "keyword TEXT, start_date TEXT, end_date TEXT, status TEXT DEFAULT 'active', "
            "assets_dir TEXT, created_at TEXT DEFAULT (datetime('now')))"
        )
        conn.execute("INSERT INTO campaigns (name) VALUES ('old-row')")
        conn.commit()
        conn.close()

        tracker.create_campaign("new-row", campaign_id="cmp-20260705-new")
        row = tracker.find_campaign("cmp-20260705-new")
        assert row is not None
        # Old row survives the ALTER with a NULL campaign_id.
        conn = sqlite3.connect(str(tracker.DB_PATH))
        old = conn.execute(
            "SELECT campaign_id FROM campaigns WHERE name = 'old-row'"
        ).fetchone()
        conn.close()
        assert old == (None,)


# ---------------------------------------------------------------------------
# content_log threading
# ---------------------------------------------------------------------------


class TestContentLogCampaignId:
    def test_entry_and_pending_check_carry_campaign_id(self, sandbox):
        entry = log_entry(
            url="https://kaicalls.com/blog/x",
            keyword="k",
            site="kaicalls",
            format="blog",
            content_hash=compute_content_hash(BODY),
            campaign_id="cmp-20260705-q3-launch",
            log_file=sandbox["log_file"],
        )
        assert entry["campaign_id"] == "cmp-20260705-q3-launch"
        check = json.loads(_checks(sandbox)[0].read_text())
        assert check["campaign_id"] == "cmp-20260705-q3-launch"

    def test_mark_published_preserves_campaign_id_into_check(self, sandbox):
        entry = log_entry(
            url=None,
            keyword="k",
            site="kaicalls",
            format="blog",
            content_hash=compute_content_hash(BODY),
            campaign_id="cmp-20260705-q3-launch",
            log_file=sandbox["log_file"],
        )
        assert _checks(sandbox) == []
        mark_published(entry["id"], "https://kaicalls.com/blog/live", log_file=sandbox["log_file"])
        check = json.loads(_checks(sandbox)[0].read_text())
        assert check["campaign_id"] == "cmp-20260705-q3-launch"

    def test_dedup_update_attaches_campaign_id(self, sandbox):
        content_hash = compute_content_hash(BODY)
        log_entry(
            url=None, keyword="k", site="kaicalls", format="blog",
            content_hash=content_hash, log_file=sandbox["log_file"],
        )
        log_entry(
            url=None, keyword="k", site="kaicalls", format="blog",
            content_hash=content_hash, campaign_id="cmp-20260705-late-join",
            log_file=sandbox["log_file"],
        )
        entries = load_log(sandbox["log_file"])
        assert len(entries) == 1
        assert entries[0]["campaign_id"] == "cmp-20260705-late-join"

    def test_absent_campaign_id_stays_none(self, sandbox):
        entry = log_entry(
            url=None, keyword="k", site="kaicalls", format="blog",
            content_hash=compute_content_hash(BODY), log_file=sandbox["log_file"],
        )
        assert entry["campaign_id"] is None


# ---------------------------------------------------------------------------
# engine threading (mocked run — no Gemini, no publishing)
# ---------------------------------------------------------------------------


class _FakeBrand:
    id = "kaicalls"
    module_ids: list = []

    def model_dump(self):
        return {"id": "kaicalls", "module_ids": []}


class _FakeWorkspace:
    product_mode = "local"
    brands = [_FakeBrand()]

    def get_brand(self, site):
        return _FakeBrand() if site == "kaicalls" else None

    def model_dump(self):
        return {"product_mode": "local"}


class _FakeStore:
    def __init__(self):
        self.runs: dict = {}
        self.artifacts: list = []
        self.completed: list = []
        self.base_dir = Path("/nonexistent-runtime")

    def start_run(self, payload, parent_run_id=None, run_id=None):
        rid = run_id or "run-test"
        self.runs[rid] = payload
        return {"run_id": rid}

    def record_artifact(self, record, run_id=None, parent_artifact_id=None):
        rec = dict(record)
        rec["artifact_id"] = f"art-{len(self.artifacts)}"
        self.artifacts.append(rec)
        return rec

    def complete_run(self, run_id, status="completed", outputs=None, metadata=None):
        self.completed.append({"run_id": run_id, "status": status, "outputs": outputs})


class TestEngineCampaignThreading:
    @pytest.fixture()
    def engine_env(self, sandbox, monkeypatch):
        import scripts.content.engine as engine

        fake_store = _FakeStore()
        monkeypatch.setattr(engine, "load_workspace_profile", lambda: _FakeWorkspace())
        monkeypatch.setattr(engine, "get_default_runtime_store", lambda: fake_store)
        monkeypatch.setattr(engine, "load_module_manifests", lambda: {})
        monkeypatch.setattr(engine, "retrieve_memory_entries", lambda *a, **k: [])
        monkeypatch.setattr(engine, "_make_gemini_fn", lambda: (lambda prompt: "x"))
        monkeypatch.setattr(engine, "write_content", lambda prompt, fn: BODY)
        monkeypatch.setattr(engine, "resolve_policy", lambda fmt, site: {"mode": "auto"})
        monkeypatch.setattr(engine, "apply_approval", lambda status, policy: "approved")

        async def fake_brief(**kwargs):
            return {"persona": "Shock Absorber", "angle": "Missed calls cost $410"}

        monkeypatch.setattr(engine.brief_generator, "generate_brief", fake_brief)

        async def fake_propose(content, file_path, policy_name):
            return {
                "proposal_id": "prop-1",
                "score": 14,
                "grade": "A",
                "status": "approved",
                "top_fixes": [],
                "violation_count": 0,
            }

        monkeypatch.setattr("scripts.quality.gate.propose", fake_propose)
        return {"engine": engine, "store": fake_store}

    def test_campaign_id_reaches_run_log_and_metadata(self, engine_env, sandbox):
        engine = engine_env["engine"]
        result = asyncio.run(
            engine.generate(
                "blog", "kaicalls", "ai receptionist",
                campaign_id="cmp-20260705-q3-launch",
            )
        )
        assert result.status == "approved"
        assert result.metadata["campaign_id"] == "cmp-20260705-q3-launch"

        # Run inputs carry the id.
        run_payload = engine_env["store"].runs["run-test"]
        assert run_payload["inputs"]["campaign_id"] == "cmp-20260705-q3-launch"

        # Canonical log entry carries the id; publishing disabled -> no URL,
        # no fabricated pending check.
        entries = load_log(sandbox["log_file"])
        assert len(entries) == 1
        assert entries[0]["campaign_id"] == "cmp-20260705-q3-launch"
        assert entries[0]["url"] is None
        assert entries[0]["status"] == "approved_unpublished"
        assert _checks(sandbox) == []

    def test_campaign_id_defaults_to_none(self, engine_env, sandbox):
        engine = engine_env["engine"]
        result = asyncio.run(engine.generate("blog", "kaicalls", "ai receptionist"))
        assert result.metadata["campaign_id"] is None
        entries = load_log(sandbox["log_file"])
        assert entries[0]["campaign_id"] is None


# ---------------------------------------------------------------------------
# legacy log migration
# ---------------------------------------------------------------------------


LEGACY_WINNER = {
    "id": "kaicalls-blog-20260316",
    "site": "kaicalls",
    "keyword": "ai receptionists",
    "format": "blog",
    "publish_date": "2026-03-16",
    "four_us_score": 14,
    "hook_type": "data",
    "persona": "Shock Absorber",
    "draft_path": "~/.kai-marketing/drafts/2026-03-16-ai.md",
    "performance_30d": {"grade": "winner", "position": 3},
    "url": "https://kaicalls.com/blog/ai-receptionists",
}

LEGACY_DRAFT_ONLY = {
    "id": "abp-linkedin-20260401",
    "site": "abp",
    "keyword": "backyard design",
    "format": "linkedin",
    "publish_date": "2026-04-01",
    "four_us_score": 11,
    "performance_30d": None,
}


class TestLegacyLogMigration:
    def _write_legacy(self, tmp_path, entries, extra_lines=()):
        legacy = tmp_path / "content-log.jsonl"
        lines = [json.dumps(e) for e in entries]
        lines.extend(extra_lines)
        legacy.write_text("\n".join(lines) + "\n")
        return legacy

    def test_merge_maps_fields_and_grades_survive(self, sandbox, tmp_path):
        legacy = self._write_legacy(
            tmp_path,
            [LEGACY_WINNER, LEGACY_DRAFT_ONLY],
            extra_lines=["{not json", json.dumps({"keyword": "no id or url"})],
        )
        summary = migrate(legacy_path=legacy, log_file=sandbox["log_file"])
        assert summary["added"] == 2
        assert summary["skipped_invalid"] == 1

        entries = {e["id"]: e for e in load_log(sandbox["log_file"])}
        winner = entries["kaicalls-blog-20260316"]
        assert winner["published_at"] == "2026-03-16"  # publish_date mapped
        assert "publish_date" not in winner
        assert winner["performance_30d"] == {"grade": "winner", "position": 3}
        assert winner["status"] == "published"
        assert winner["hook_type"] == "data"
        assert winner["migrated_from"] == "kai-marketing-jsonl"

        draft = entries["abp-linkedin-20260401"]
        assert draft["url"] is None
        assert draft["status"] == "approved_unpublished"

    def test_idempotent_rerun_changes_nothing(self, sandbox, tmp_path):
        legacy = self._write_legacy(tmp_path, [LEGACY_WINNER, LEGACY_DRAFT_ONLY])
        migrate(legacy_path=legacy, log_file=sandbox["log_file"])
        before = Path(sandbox["log_file"]).read_text()
        summary = migrate(legacy_path=legacy, log_file=sandbox["log_file"])
        assert summary["added"] == 0
        assert summary["updated"] == 0
        assert summary["unchanged"] == 2
        assert Path(sandbox["log_file"]).read_text() == before

    def test_dedupe_by_url_and_performance_backfill(self, sandbox, tmp_path):
        # Canonical already tracks the same URL under a different id with no
        # performance data — migration must NOT duplicate, only backfill.
        canonical = [{
            "id": "kaicalls-20260316-090000",
            "url": "https://kaicalls.com/blog/ai-receptionists",
            "keyword": "ai receptionists",
            "site": "kaicalls",
            "format": "blog",
            "published_at": "2026-03-16T09:00:00+00:00",
            "performance_30d": None,
            "status": "published",
        }]
        Path(sandbox["log_file"]).write_text(json.dumps(canonical))
        legacy = self._write_legacy(tmp_path, [LEGACY_WINNER])

        summary = migrate(legacy_path=legacy, log_file=sandbox["log_file"])
        assert summary["added"] == 0
        assert summary["updated"] == 1

        entries = load_log(sandbox["log_file"])
        assert len(entries) == 1
        assert entries[0]["id"] == "kaicalls-20260316-090000"  # canonical id kept
        assert entries[0]["performance_30d"]["grade"] == "winner"
        assert entries[0]["published_at"] == "2026-03-16T09:00:00+00:00"  # not clobbered

    def test_dry_run_writes_nothing(self, sandbox, tmp_path):
        legacy = self._write_legacy(tmp_path, [LEGACY_WINNER])
        summary = migrate(legacy_path=legacy, log_file=sandbox["log_file"], dry_run=True)
        assert summary["added"] == 1
        assert not Path(sandbox["log_file"]).exists()

    def test_missing_legacy_file_is_noop(self, sandbox, tmp_path):
        summary = migrate(
            legacy_path=tmp_path / "nope.jsonl", log_file=sandbox["log_file"]
        )
        assert summary["legacy_total"] == 0
        assert summary["added"] == 0

    def test_normalize_entry_without_key_is_rejected(self):
        assert normalize_legacy_entry({"keyword": "x"}) is None

    def test_string_grades_normalized_to_dict_schema(self, sandbox, tmp_path):
        """Legacy STRING-form grades must land in the canonical log as the
        dict schema — canonical readers (pattern_extract.is_winner,
        weekly_report, ceo_deck) crash on a bare str."""
        legacy = self._write_legacy(tmp_path, [
            {**LEGACY_WINNER, "performance_30d": "winner"},
            {**LEGACY_DRAFT_ONLY, "id": "abp-str-loser",
             "url": "https://abp.com/blog/x", "performance_30d": "loser"},
        ])
        migrate(legacy_path=legacy, log_file=sandbox["log_file"])

        entries = {e["id"]: e for e in load_log(sandbox["log_file"])}
        winner = entries["kaicalls-blog-20260316"]
        assert winner["performance_30d"] == {"grade": "winner", "migrated": True}
        loser = entries["abp-str-loser"]
        # Legacy "loser" vocabulary normalizes to "underperformer".
        assert loser["performance_30d"] == {"grade": "underperformer", "migrated": True}

        # is_winner must tolerate the migrated entries without AttributeError.
        from scripts.self_improvement.grades import get_grade
        assert get_grade(winner) == "winner"
        assert get_grade(loser) == "underperformer"

    def test_rerun_heals_canonical_string_grade(self, sandbox, tmp_path):
        """A canonical log poisoned by an earlier merge (string grade) is
        healed to the dict schema when the migration re-runs."""
        canonical = [{
            "id": "kaicalls-blog-20260316",
            "url": "https://kaicalls.com/blog/ai-receptionists",
            "keyword": "ai receptionists",
            "site": "kaicalls",
            "format": "blog",
            "published_at": "2026-03-16T09:00:00+00:00",
            "performance_30d": "winner",
            "status": "published",
        }]
        Path(sandbox["log_file"]).write_text(json.dumps(canonical))
        legacy = self._write_legacy(tmp_path, [LEGACY_WINNER])

        summary = migrate(legacy_path=legacy, log_file=sandbox["log_file"])
        assert summary["added"] == 0
        assert summary["updated"] == 1
        entries = load_log(sandbox["log_file"])
        assert len(entries) == 1
        assert entries[0]["performance_30d"] == {"grade": "winner", "migrated": True}

    def test_migration_never_schedules_pending_checks(self, sandbox, tmp_path):
        legacy = self._write_legacy(tmp_path, [LEGACY_WINNER])
        migrate(legacy_path=legacy, log_file=sandbox["log_file"])
        # Checks are reconcile_pending_checks' job (EC-12), not the migration's.
        assert _checks(sandbox) == []


# ---------------------------------------------------------------------------
# gateway job retention
# ---------------------------------------------------------------------------


class TestJobRetention:
    @pytest.fixture()
    def queue(self, tmp_path, monkeypatch):
        monkeypatch.delenv("KAI_JOB_RETENTION_DAYS", raising=False)
        from gateway.jobs import JobQueue

        q = JobQueue(db_path=tmp_path / "jobs.db", max_workers=1)
        yield q
        q.shutdown()

    def _age_job(self, queue, job_id, days_old):
        stamp = (datetime.utcnow() - timedelta(days=days_old)).isoformat()
        with sqlite3.connect(queue.db_path) as conn:
            conn.execute("UPDATE jobs SET created_at = ? WHERE job_id = ?", (stamp, job_id))
            conn.execute("UPDATE runs SET created_at = ? WHERE job_id = ?", (stamp, job_id))
            conn.commit()

    def _job_ids(self, queue):
        with sqlite3.connect(queue.db_path) as conn:
            return {row[0] for row in conn.execute("SELECT job_id FROM jobs")}

    def test_default_retention_is_45_days(self, queue):
        fresh = queue.create_job("cmd", client="c")
        mid = queue.create_job("cmd", client="c")
        old = queue.create_job("cmd", client="c")
        self._age_job(queue, mid, 40)   # inside the 30-day learning window's buffer
        self._age_job(queue, old, 50)

        queue.cleanup_old_jobs()
        ids = self._job_ids(queue)
        assert fresh in ids
        assert mid in ids       # 40 days < 45 — must survive
        assert old not in ids   # 50 days > 45 — deleted
        # Run rows follow the same retention.
        with sqlite3.connect(queue.db_path) as conn:
            runs = {row[0] for row in conn.execute("SELECT job_id FROM runs")}
        assert old not in runs and mid in runs

    def test_legacy_days_7_caller_is_floored(self, queue):
        mid = queue.create_job("cmd", client="c")
        self._age_job(queue, mid, 40)
        # gateway/main.py still calls cleanup_old_jobs(days=7) — the configured
        # retention (45) is a floor, so the 40-day job must survive.
        queue.cleanup_old_jobs(days=7)
        assert mid in self._job_ids(queue)

    def test_explicit_longer_window_is_honored(self, queue):
        old = queue.create_job("cmd", client="c")
        self._age_job(queue, old, 50)
        queue.cleanup_old_jobs(days=90)
        assert old in self._job_ids(queue)

    def test_env_override_shortens_retention(self, queue, monkeypatch):
        monkeypatch.setenv("KAI_JOB_RETENTION_DAYS", "7")
        mid = queue.create_job("cmd", client="c")
        self._age_job(queue, mid, 10)
        queue.cleanup_old_jobs()
        assert mid not in self._job_ids(queue)

    def test_invalid_env_falls_back_to_default(self, monkeypatch):
        from gateway.jobs import DEFAULT_JOB_RETENTION_DAYS, get_job_retention_days

        monkeypatch.setenv("KAI_JOB_RETENTION_DAYS", "banana")
        assert get_job_retention_days() == DEFAULT_JOB_RETENTION_DAYS
        monkeypatch.setenv("KAI_JOB_RETENTION_DAYS", "-3")
        assert get_job_retention_days() == DEFAULT_JOB_RETENTION_DAYS
        monkeypatch.setenv("KAI_JOB_RETENTION_DAYS", "60")
        assert get_job_retention_days() == 60
