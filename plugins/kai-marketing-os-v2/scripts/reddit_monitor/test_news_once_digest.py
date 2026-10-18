import types
import reddit_digest as digest
import news_once


def test_second_agent_news_digest_skipped(monkeypatch, tmp_path):
    rows, sends = [], []
    outreach = types.SimpleNamespace(history=lambda *a, **k: rows,
                                    record=lambda contact, **k: rows.append(k))
    monkeypatch.setattr(news_once, "_outreach", lambda: outreach)
    monkeypatch.setattr(news_once, "_ledger_state", lambda *args: (set(), set()))
    monkeypatch.setattr(news_once, "_attempt_event", lambda *args: None)
    monkeypatch.setattr(digest, "post_to_discord", lambda hook, content: sends.append(content) or True)
    bucket = [{"url": "https://www.reddit.com/r/smallbusiness/comments/real-source"}]
    kwargs = dict(db_path=tmp_path / "events.db")
    first = digest.notify_digest_once("unused", bucket, "http://agent/review", "2026-10-02", agent="scout", **kwargs)
    second = digest.notify_digest_once("unused", bucket, "http://agent/review", "2026-10-02", agent="ember", **kwargs)
    assert first["sent"]
    assert second["skipped"]
    assert len(sends) == len(rows) == 1
    assert rows[0]["message_id"] == bucket[0]["url"]


def test_digest_failed_delivery_not_logged(monkeypatch, tmp_path):
    rows = []
    outreach = types.SimpleNamespace(history=lambda *a, **k: rows,
                                    record=lambda contact, **k: rows.append(k))
    monkeypatch.setattr(news_once, "_outreach", lambda: outreach)
    monkeypatch.setattr(news_once, "_ledger_state", lambda *args: (set(), set()))
    monkeypatch.setattr(news_once, "_attempt_event", lambda *args: None)
    monkeypatch.setattr(digest, "post_to_discord", lambda *a: False)
    result = digest.notify_digest_once("unused", [{"url": "https://example.com/source"}], "http://agent/review", "2026-10-02", db_path=tmp_path / "events.db")
    assert not result["sent"]
    assert not rows
