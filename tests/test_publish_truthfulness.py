"""Publish truthfulness + idempotency tests.

Covers the fix for the fabricated-URL bug: the engine used to log
`https://<site>.com/<keyword-slug>` on approval WITHOUT publishing, which
scheduled 30-day checks against URLs that never existed and poisoned the
GSC learning loop (performance_check.py filters by logged url).

Invariants enforced here:
  - No fabricated URLs: publishing disabled/unconfigured -> url=None,
    status "approved_unpublished".
  - No 30-day pending check without a REAL url.
  - mark_published() backfills the real URL and schedules the check.
  - log_entry dedupes on (site, content_hash); engine re-runs skip publish
    when the same hash already shipped for that site.
  - WordPress publisher updates an existing slug instead of duplicating.
  - Calendar path is configurable (KAI_CONTENT_CALENDAR_PATH), not hardcoded.
"""

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

import scripts.content.content_log as cl
from scripts.content.content_log import (
    compute_content_hash,
    find_entry_by_hash,
    load_log,
    log_entry,
    mark_published,
)


BODY = "Rodriguez Air missed 19 calls a week between 6pm and 8am. Each cost $410."


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
    # Publishing OFF unless a test opts in.
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
# content_log: truthfulness
# ---------------------------------------------------------------------------


class TestLogEntryTruthfulness:
    def test_unpublished_entry_has_no_url_and_no_check(self, sandbox):
        entry = log_entry(
            url=None,
            keyword="ai receptionist",
            site="kaicalls",
            format="blog",
            content_hash=compute_content_hash(BODY),
            log_file=sandbox["log_file"],
        )
        assert entry["url"] is None
        assert entry["status"] == "approved_unpublished"
        assert _checks(sandbox) == []
        # Calendar tracks live content only — no line for unpublished pieces.
        assert not sandbox["calendar"].exists()

    def test_published_entry_schedules_check_and_calendar(self, sandbox):
        entry = log_entry(
            url="https://kaicalls.com/blog/real-post",
            keyword="ai receptionist",
            site="kaicalls",
            format="blog",
            content_hash=compute_content_hash(BODY),
            log_file=sandbox["log_file"],
        )
        assert entry["status"] == "published"
        checks = _checks(sandbox)
        assert len(checks) == 1
        check = json.loads(checks[0].read_text())
        assert check["url"] == "https://kaicalls.com/blog/real-post"
        assert "kaicalls.com" in sandbox["calendar"].read_text()

    def test_schedule_check_refuses_urlless_entry(self, sandbox):
        assert cl.schedule_30day_check({"id": "x", "url": None}) is None
        assert _checks(sandbox) == []

    def test_legacy_entries_without_status_or_hash_tolerated(self, sandbox):
        legacy = {
            "id": "kaicalls-20250101-000000",
            "url": "https://kaicalls.com/old-post",
            "keyword": "old keyword",
            "site": "kaicalls",
            "format": "blog",
            "published_at": "2025-01-01T00:00:00+00:00",
            "performance_30d": None,
        }
        Path(sandbox["log_file"]).write_text(json.dumps([legacy]))
        # New entries do not dedupe against legacy entries (no content_hash)…
        entry = log_entry(
            url=None,
            keyword="old keyword",
            site="kaicalls",
            format="blog",
            content_hash=compute_content_hash(BODY),
            log_file=sandbox["log_file"],
        )
        entries = load_log(sandbox["log_file"])
        assert len(entries) == 2
        assert entry["status"] == "approved_unpublished"
        # …and hash lookup never matches a legacy entry.
        assert find_entry_by_hash("kaicalls", "", log_file=sandbox["log_file"]) is None


class TestMarkPublished:
    def test_backfills_url_and_schedules_check(self, sandbox):
        entry = log_entry(
            url=None,
            keyword="ai receptionist",
            site="kaicalls",
            format="blog",
            content_hash=compute_content_hash(BODY),
            log_file=sandbox["log_file"],
        )
        assert _checks(sandbox) == []

        updated = mark_published(
            entry["id"],
            "https://kaicalls.com/blog/shipped",
            log_file=sandbox["log_file"],
        )
        assert updated["status"] == "published"
        assert updated["url"] == "https://kaicalls.com/blog/shipped"

        persisted = load_log(sandbox["log_file"])[0]
        assert persisted["url"] == "https://kaicalls.com/blog/shipped"
        checks = _checks(sandbox)
        assert len(checks) == 1
        check = json.loads(checks[0].read_text())
        assert check["url"] == "https://kaicalls.com/blog/shipped"
        assert "shipped" in sandbox["calendar"].read_text()

    def test_check_due_thirty_days_after_published_at(self, sandbox):
        entry = log_entry(
            url=None,
            keyword="k",
            site="kaicalls",
            format="blog",
            content_hash=compute_content_hash(BODY),
            log_file=sandbox["log_file"],
        )
        published_at = "2026-06-01T12:00:00+00:00"
        mark_published(
            entry["id"],
            "https://kaicalls.com/blog/x",
            published_at=published_at,
            log_file=sandbox["log_file"],
        )
        check = json.loads(_checks(sandbox)[0].read_text())
        due = datetime.fromisoformat(check["check_due"])
        assert due == datetime.fromisoformat(published_at) + timedelta(days=30)

    def test_unknown_id_or_empty_url_returns_none(self, sandbox):
        assert mark_published("nope", "https://x.com/y", log_file=sandbox["log_file"]) is None
        assert mark_published("nope", "", log_file=sandbox["log_file"]) is None


# ---------------------------------------------------------------------------
# content_log: idempotency
# ---------------------------------------------------------------------------


class TestContentHashDedup:
    def test_same_site_and_hash_updates_in_place(self, sandbox):
        content_hash = compute_content_hash(BODY)
        first = log_entry(
            url=None, keyword="k", site="kaicalls", format="blog",
            content_hash=content_hash, log_file=sandbox["log_file"],
        )
        second = log_entry(
            url=None, keyword="k", site="kaicalls", format="blog",
            notes="second run", content_hash=content_hash,
            log_file=sandbox["log_file"],
        )
        entries = load_log(sandbox["log_file"])
        assert len(entries) == 1
        assert second["id"] == first["id"]
        assert entries[0]["notes"] == "second run"
        assert "updated_at" in entries[0]

    def test_different_site_same_hash_appends(self, sandbox):
        content_hash = compute_content_hash(BODY)
        log_entry(url=None, keyword="k", site="kaicalls", format="blog",
                  content_hash=content_hash, log_file=sandbox["log_file"])
        log_entry(url=None, keyword="k", site="buildwithkai", format="blog",
                  content_hash=content_hash, log_file=sandbox["log_file"])
        assert len(load_log(sandbox["log_file"])) == 2

    def test_dedup_never_downgrades_published_entry(self, sandbox):
        content_hash = compute_content_hash(BODY)
        log_entry(
            url="https://kaicalls.com/blog/live", keyword="k", site="kaicalls",
            format="blog", content_hash=content_hash, log_file=sandbox["log_file"],
        )
        # Re-run without a URL must not clobber the real one.
        log_entry(
            url=None, keyword="k", site="kaicalls", format="blog",
            content_hash=content_hash, log_file=sandbox["log_file"],
        )
        entry = load_log(sandbox["log_file"])[0]
        assert entry["url"] == "https://kaicalls.com/blog/live"
        assert entry["status"] == "published"
        assert len(_checks(sandbox)) == 1  # not rescheduled

    def test_dedup_update_with_url_publishes_and_schedules(self, sandbox):
        content_hash = compute_content_hash(BODY)
        log_entry(url=None, keyword="k", site="kaicalls", format="blog",
                  content_hash=content_hash, log_file=sandbox["log_file"])
        assert _checks(sandbox) == []
        log_entry(
            url="https://kaicalls.com/blog/now-live", keyword="k",
            site="kaicalls", format="blog", content_hash=content_hash,
            log_file=sandbox["log_file"],
        )
        entries = load_log(sandbox["log_file"])
        assert len(entries) == 1
        assert entries[0]["status"] == "published"
        assert len(_checks(sandbox)) == 1

    def test_republish_rerun_never_restamps_published_at(self, sandbox):
        """An engine re-run (already_published -> log_entry(url=prior_url))
        must not reset published_at: re-stamping re-counts the piece as new
        and shifts the 30-day measurement window (EC-12 reconciliation
        rebuilds check_due from published_at)."""
        content_hash = compute_content_hash(BODY)
        log_entry(
            url="https://kaicalls.com/blog/live", keyword="k", site="kaicalls",
            format="blog", content_hash=content_hash, log_file=sandbox["log_file"],
        )
        # Age the entry so a re-stamp would be visible.
        entries = load_log(sandbox["log_file"])
        entries[0]["published_at"] = "2026-01-01T00:00:00+00:00"
        cl.save_log(entries, sandbox["log_file"])

        log_entry(
            url="https://kaicalls.com/blog/live", keyword="k", site="kaicalls",
            format="blog", notes="re-run", content_hash=content_hash,
            log_file=sandbox["log_file"],
        )
        entries = load_log(sandbox["log_file"])
        assert len(entries) == 1
        assert entries[0]["published_at"] == "2026-01-01T00:00:00+00:00"
        assert entries[0]["status"] == "published"
        assert entries[0]["notes"] == "re-run"  # metadata still updates
        assert len(_checks(sandbox)) == 1  # not rescheduled
        # Calendar not double-appended either.
        calendar_text = sandbox["calendar"].read_text()
        assert calendar_text.count("https://kaicalls.com/blog/live") == 1


# ---------------------------------------------------------------------------
# engine: publish decision (no fabricated URLs, gated by config)
# ---------------------------------------------------------------------------


class TestEnginePublishDecision:
    def _write_publishing_config(self, tmp_path, monkeypatch, enabled=True, sites=None):
        cfg = tmp_path / "config.yaml"
        lines = ["publishing:", f"  enabled: {'true' if enabled else 'false'}"]
        if sites:
            lines.append("  sites:")
            for site, platform in sites.items():
                lines.append(f"    {site}:")
                lines.append(f"      platform: {platform}")
        cfg.write_text("\n".join(lines) + "\n")
        monkeypatch.setenv("CMO_CONFIG_PATH", str(cfg))

    def test_disabled_by_default_no_fabricated_url(self, sandbox, monkeypatch, tmp_path):
        from scripts.content.engine import _publish_if_configured

        called = []
        monkeypatch.setattr("scripts.publish.publish", lambda *a, **k: called.append(1))
        info = _publish_if_configured(
            site="kaicalls", title="T", body=BODY,
            content_hash=compute_content_hash(BODY), keyword="ai receptionist",
            log_file=sandbox["log_file"],
        )
        assert info["published"] is False
        assert info["url"] is None
        assert info["skipped"] == "publishing_disabled"
        assert called == []

    def test_enabled_but_site_unconfigured(self, sandbox, monkeypatch, tmp_path):
        from scripts.content.engine import _publish_if_configured

        monkeypatch.setenv("KAI_PUBLISH_ENABLED", "1")
        info = _publish_if_configured(
            site="kaicalls", title="T", body=BODY,
            content_hash=compute_content_hash(BODY), keyword="k",
            log_file=sandbox["log_file"],
        )
        assert info["published"] is False
        assert info["url"] is None
        assert info["skipped"] == "site_not_configured"

    def test_env_override_wins_over_config(self, sandbox, monkeypatch, tmp_path):
        from scripts.harness_config import publishing_enabled

        self._write_publishing_config(tmp_path, monkeypatch, enabled=True)
        monkeypatch.setenv("KAI_PUBLISH_ENABLED", "0")
        assert publishing_enabled() is False
        monkeypatch.setenv("KAI_PUBLISH_ENABLED", "1")
        assert publishing_enabled() is True

    def test_configured_publish_logs_real_url(self, sandbox, monkeypatch, tmp_path):
        from scripts.content.engine import _publish_if_configured

        self._write_publishing_config(
            tmp_path, monkeypatch, enabled=True, sites={"kaicalls": "wordpress"}
        )
        captured = {}

        def fake_publish(platform, **kwargs):
            captured["platform"] = platform
            captured.update(kwargs)
            return {"success": True, "url": "https://kaicalls.com/?p=99", "id": 99}

        monkeypatch.setattr("scripts.publish.publish", fake_publish)
        info = _publish_if_configured(
            site="kaicalls", title="T", body=BODY,
            content_hash=compute_content_hash(BODY), keyword="AI Receptionist!",
            log_file=sandbox["log_file"],
        )
        assert info["published"] is True
        assert info["url"] == "https://kaicalls.com/?p=99"  # REAL url from publisher
        assert captured["platform"] == "wordpress"
        assert captured["slug"] == "ai-receptionist"
        assert captured["status"] == "draft"  # safe default: never auto-live

    def test_publish_failure_yields_unpublished(self, sandbox, monkeypatch, tmp_path):
        from scripts.content.engine import _publish_if_configured

        self._write_publishing_config(
            tmp_path, monkeypatch, enabled=True, sites={"kaicalls": "wordpress"}
        )
        monkeypatch.setattr(
            "scripts.publish.publish",
            lambda platform, **k: {"success": False, "message": "boom"},
        )
        info = _publish_if_configured(
            site="kaicalls", title="T", body=BODY,
            content_hash=compute_content_hash(BODY), keyword="k",
            log_file=sandbox["log_file"],
        )
        assert info["published"] is False
        assert info["url"] is None
        assert info["skipped"] == "publish_failed"

    def test_rerun_with_same_hash_skips_publish(self, sandbox, monkeypatch, tmp_path):
        from scripts.content.engine import _publish_if_configured

        self._write_publishing_config(
            tmp_path, monkeypatch, enabled=True, sites={"kaicalls": "wordpress"}
        )
        content_hash = compute_content_hash(BODY)
        calls = []

        def fake_publish(platform, **kwargs):
            calls.append(platform)
            return {"success": True, "url": "https://kaicalls.com/?p=7", "id": 7}

        monkeypatch.setattr("scripts.publish.publish", fake_publish)

        first = _publish_if_configured(
            site="kaicalls", title="T", body=BODY, content_hash=content_hash,
            keyword="k", log_file=sandbox["log_file"],
        )
        # Engine logs the entry after publishing — simulate that.
        log_entry(
            url=first["url"], keyword="k", site="kaicalls", format="blog",
            content_hash=content_hash, status="published",
            log_file=sandbox["log_file"],
        )

        second = _publish_if_configured(
            site="kaicalls", title="T", body=BODY, content_hash=content_hash,
            keyword="k", log_file=sandbox["log_file"],
        )
        assert calls == ["wordpress"]  # publisher hit exactly once
        assert second["published"] is True
        assert second["skipped"] == "already_published"
        assert second["url"] == "https://kaicalls.com/?p=7"

    def test_slugify(self):
        from scripts.content.engine import _slugify

        assert _slugify("AI Receptionist for Law Firms") == "ai-receptionist-for-law-firms"
        assert _slugify("  weird -- punctuation!! ") == "weird-punctuation"


# ---------------------------------------------------------------------------
# Reader compatibility: reconcile must never rebuild checks for url-less entries
# ---------------------------------------------------------------------------


class TestReaderCompatibility:
    def test_reconcile_skips_approved_unpublished_entries(self, sandbox, monkeypatch):
        import scripts.self_improvement.performance_check as pc

        checks_dir = sandbox["data_dir"] / "pending_checks"
        entries = [
            {
                "id": "kaicalls-20260701-000000",
                "url": None,
                "status": "approved_unpublished",
                "keyword": "k",
                "site": "kaicalls",
                "format": "blog",
                "published_at": "2026-07-01T00:00:00+00:00",
                "performance_30d": None,
                "content_hash": compute_content_hash(BODY),
            },
            {
                "id": "kaicalls-20260702-000000",
                "url": "https://kaicalls.com/blog/live",
                "keyword": "k2",
                "site": "kaicalls",
                "published_at": "2026-07-02T00:00:00+00:00",
                "performance_30d": None,
            },
        ]
        Path(sandbox["log_file"]).write_text(json.dumps(entries))
        monkeypatch.setattr(pc, "CONTENT_LOG", sandbox["log_file"])
        monkeypatch.setattr(pc, "PENDING_CHECKS_DIR", str(checks_dir))

        recreated = pc.reconcile_pending_checks()
        assert recreated == 1  # only the entry with a REAL url
        files = sorted(checks_dir.glob("*.json"))
        assert [f.stem for f in files] == ["kaicalls-20260702-000000"]


# ---------------------------------------------------------------------------
# WordPress publisher idempotency (mocked HTTP)
# ---------------------------------------------------------------------------


class _Resp:
    def __init__(self, json_data, status=200):
        self._json = json_data
        self.status_code = status
        self.ok = status < 400

    def json(self):
        return self._json

    def raise_for_status(self):
        pass


class TestWordPressIdempotency:
    @pytest.fixture(autouse=True)
    def wp_env(self, monkeypatch):
        monkeypatch.setenv("WP_URL", "https://test.example.com")
        monkeypatch.setenv("WP_USERNAME", "admin")
        monkeypatch.setenv("WP_APP_PASSWORD", "app-pass")

    def test_existing_slug_updates_instead_of_creating(self, monkeypatch):
        import scripts.publish.wordpress as wp

        posted = {}

        def fake_get(url, **kwargs):
            assert url.endswith("/wp-json/wp/v2/posts")
            assert kwargs["params"] == {"slug": "my-post", "status": "any"}
            return _Resp([{"id": 42, "link": "https://test.example.com/my-post/"}])

        def fake_post(url, **kwargs):
            posted["url"] = url
            return _Resp(
                {"id": 42, "link": "https://test.example.com/my-post/", "status": "draft"}
            )

        monkeypatch.setattr(wp.requests, "get", fake_get)
        monkeypatch.setattr(wp.requests, "post", fake_post)

        result = wp.publish(title="T", body="plain body", slug="my-post")
        assert result["success"] is True
        assert result["updated"] is True
        assert posted["url"].endswith("/wp-json/wp/v2/posts/42")  # update, not create
        assert result["url"] == "https://test.example.com/my-post/"

    def test_no_existing_slug_creates_new_post(self, monkeypatch):
        import scripts.publish.wordpress as wp

        posted = {}
        monkeypatch.setattr(wp.requests, "get", lambda url, **k: _Resp([]))

        def fake_post(url, **kwargs):
            posted["url"] = url
            return _Resp(
                {"id": 7, "link": "https://test.example.com/new-post/", "status": "draft"}
            )

        monkeypatch.setattr(wp.requests, "post", fake_post)
        result = wp.publish(title="T", body="plain body", slug="new-post")
        assert result["success"] is True
        assert result["updated"] is False
        assert posted["url"].endswith("/wp-json/wp/v2/posts")

    def test_update_omits_status_so_existing_post_is_never_demoted(self, monkeypatch):
        """Slug-idempotent updates must not send the engine's default
        status=draft to an existing post — WP preserves current status when
        the field is absent."""
        import scripts.publish.wordpress as wp

        posted = {}

        def fake_get(url, **kwargs):
            return _Resp([{"id": 42, "status": "draft",
                           "link": "https://test.example.com/my-post/"}])

        def fake_post(url, **kwargs):
            posted["url"] = url
            posted["json"] = kwargs["json"]
            return _Resp(
                {"id": 42, "link": "https://test.example.com/my-post/", "status": "draft"}
            )

        monkeypatch.setattr(wp.requests, "get", fake_get)
        monkeypatch.setattr(wp.requests, "post", fake_post)

        result = wp.publish(title="T", body="plain body", slug="my-post", status="draft")
        assert result["success"] is True
        assert result["updated"] is True
        assert posted["url"].endswith("/wp-json/wp/v2/posts/42")
        assert "status" not in posted["json"]  # existing status preserved

    def test_live_post_is_never_demoted_or_overwritten(self, monkeypatch):
        """A human published this post in WP admin. A draft-status re-run
        must leave it untouched (no unpublish, no content overwrite) — that
        would be a live-channel mutation without approval."""
        import scripts.publish.wordpress as wp

        def fake_get(url, **kwargs):
            return _Resp([{"id": 42, "status": "publish",
                           "link": "https://test.example.com/my-post/"}])

        def fail_post(url, **kwargs):  # pragma: no cover - must never run
            raise AssertionError("live post must not be mutated")

        monkeypatch.setattr(wp.requests, "get", fake_get)
        monkeypatch.setattr(wp.requests, "post", fail_post)

        result = wp.publish(title="T", body="regenerated body", slug="my-post", status="draft")
        assert result["success"] is True
        assert result["updated"] is False
        assert result["skipped"] == "existing_live_post"
        assert result["status"] == "publish"
        assert result["url"] == "https://test.example.com/my-post/"

    def test_explicit_publish_can_update_live_post(self, monkeypatch):
        """status=publish is an explicit human ask (CLI --publish) — that IS
        the approval, so the update proceeds and keeps status=publish."""
        import scripts.publish.wordpress as wp

        posted = {}

        def fake_get(url, **kwargs):
            return _Resp([{"id": 42, "status": "publish",
                           "link": "https://test.example.com/my-post/"}])

        def fake_post(url, **kwargs):
            posted["url"] = url
            posted["json"] = kwargs["json"]
            return _Resp(
                {"id": 42, "link": "https://test.example.com/my-post/", "status": "publish"}
            )

        monkeypatch.setattr(wp.requests, "get", fake_get)
        monkeypatch.setattr(wp.requests, "post", fake_post)

        result = wp.publish(title="T", body="refreshed body", slug="my-post", status="publish")
        assert result["success"] is True
        assert result["updated"] is True
        assert posted["url"].endswith("/wp-json/wp/v2/posts/42")
        assert posted["json"]["status"] == "publish"

    def test_lookup_failure_falls_back_to_create(self, monkeypatch):
        import scripts.publish.wordpress as wp

        def broken_get(url, **kwargs):
            raise RuntimeError("network down")

        posted = {}

        def fake_post(url, **kwargs):
            posted["url"] = url
            return _Resp({"id": 8, "link": "https://test.example.com/p/", "status": "draft"})

        monkeypatch.setattr(wp.requests, "get", broken_get)
        monkeypatch.setattr(wp.requests, "post", fake_post)
        result = wp.publish(title="T", body="plain body", slug="p")
        assert result["success"] is True
        assert posted["url"].endswith("/wp-json/wp/v2/posts")


# ---------------------------------------------------------------------------
# Calendar path de-hardcoding
# ---------------------------------------------------------------------------


class TestCalendarPath:
    def test_env_override(self, sandbox):
        # sandbox sets KAI_CONTENT_CALENDAR_PATH — a published entry lands there.
        log_entry(
            url="https://kaicalls.com/blog/a", keyword="k", site="kaicalls",
            format="blog", content_hash=compute_content_hash(BODY),
            log_file=sandbox["log_file"],
        )
        assert sandbox["calendar"].exists()
        assert "/opt/meetkai-data" not in str(sandbox["calendar"])

    def test_default_lands_under_data_dir(self, tmp_path, monkeypatch):
        from scripts.harness_config import get_config, get_content_calendar_path

        monkeypatch.delenv("KAI_CONTENT_CALENDAR_PATH", raising=False)
        path = get_content_calendar_path()
        assert path == get_config().data_dir / "content-calendar.md"

    def test_calendar_write_failure_never_crashes(self, sandbox, monkeypatch):
        monkeypatch.setenv(
            "KAI_CONTENT_CALENDAR_PATH", "/proc/definitely/not/writable/cal.md"
        )
        entry = log_entry(
            url="https://kaicalls.com/blog/b", keyword="k", site="kaicalls",
            format="blog", content_hash=compute_content_hash(BODY),
            log_file=sandbox["log_file"],
        )
        assert entry["status"] == "published"  # publish survives calendar failure
