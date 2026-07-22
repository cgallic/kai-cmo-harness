"""Tests for live watcher wiring: HTTP feeds, notification dispatch, and the
agent-loop bridge (watchers_tick) — plus proposal-path memory retrieval.

The HTTP layer itself is monkeypatched: these tests verify the wiring from
fetched data to findings, not the network.
"""

from kai.watchers import (
    NotificationPreference,
    NotificationSystem,
    create_default_registry,
)
from kai.watchers import website_visibility as wv
from kai.watchers.framework import create_watcher_finding


def _profile(**over):
    base = {
        "id": "biz1",
        "website_url": "https://example.com",
        "phone": "(555) 123-4567",
        "key_pages": ["/"],
    }
    base.update(over)
    return base


def _quiet_http(monkeypatch, status=200, html=None, cert=(None, None)):
    monkeypatch.setattr(wv, "_http_status", lambda url, method="HEAD": (status, 50.0))
    monkeypatch.setattr(wv, "_fetch_html", lambda url: html)
    monkeypatch.setattr(wv, "_cert_expiry", lambda domain: cert)


# ── Live feed → finding wiring ──────────────────────────────────────────────


def test_uptime_finding_on_non_200(monkeypatch):
    _quiet_http(monkeypatch, status=503)
    findings = wv.WebsiteHealthWatcher().check(_profile(), {})
    assert any("down or returning errors" in f.title for f in findings)


def test_uptime_finding_on_unreachable(monkeypatch):
    monkeypatch.setattr(wv, "_http_status", lambda url, method="HEAD": (None, None))
    monkeypatch.setattr(wv, "_fetch_html", lambda url: None)
    monkeypatch.setattr(wv, "_cert_expiry", lambda domain: (None, None))
    findings = wv.WebsiteHealthWatcher().check(_profile(), {})
    assert any("unreachable" in f.title for f in findings)


def test_healthy_site_produces_no_findings(monkeypatch):
    html = "<html><script>gtag('config','G-ABC123');</script>tel 555.123.4567</html>"
    _quiet_http(monkeypatch, status=200, html=html, cert=("2099-01-01", 3650))
    findings = wv.WebsiteHealthWatcher().check(_profile(), {})
    assert findings == []


def test_ssl_expiring_soon_is_critical(monkeypatch):
    _quiet_http(monkeypatch, status=200, cert=("2026-07-27", 5))
    findings = wv.WebsiteHealthWatcher().check(_profile(phone=""), {})
    ssl = [f for f in findings if "SSL certificate" in f.title]
    assert ssl and ssl[0].severity == "critical"
    assert "expires in 5 days" in ssl[0].title


def test_missing_tracking_flagged(monkeypatch):
    _quiet_http(monkeypatch, status=200, html="<html>no analytics here</html>")
    findings = wv.WebsiteHealthWatcher().check(_profile(phone=""), {})
    assert any("tracking not detected" in f.title for f in findings)


def test_phone_mismatch_flagged(monkeypatch):
    html = '<a href="tel:+15559999999">Call us</a>'
    _quiet_http(monkeypatch, status=200, html=html)
    findings = wv.WebsiteHealthWatcher().check(_profile(), {})
    mismatch = [f for f in findings if "does not match" in f.title]
    assert mismatch and mismatch[0].severity == "critical"


def test_unfetchable_pages_do_not_false_alarm(monkeypatch):
    # Site up, but HTML fetches fail: phone/tracking/forms checks must stay quiet
    _quiet_http(monkeypatch, status=200, html=None, cert=("2099-01-01", 3650))
    findings = wv.WebsiteHealthWatcher().check(_profile(), {})
    assert findings == []


# ── Notification dispatch ───────────────────────────────────────────────────


def _finding(urgency="immediate", severity="critical"):
    return create_watcher_finding(
        watcher_name="website_health",
        business_id="biz1",
        title="Website is unreachable",
        description="No response in 10s.",
        suppression_key="site_down_example_com",
        urgency=urgency,
        severity=severity,
        category="website_health",
        evidence={},
    )


def test_dispatch_finding_immediate_sends():
    sent = []
    route = NotificationSystem().dispatch_finding(
        _finding(), NotificationPreference(business_id="biz1"), sent.append
    )
    assert route == "immediate"
    assert sent and "[CRITICAL]" in sent[0] and "unreachable" in sent[0]


def test_dispatch_finding_informational_queues_no_send():
    sent = []
    system = NotificationSystem()
    route = system.dispatch_finding(
        _finding(urgency="informational", severity="low"),
        NotificationPreference(business_id="biz1"),
        sent.append,
    )
    assert route == "weekly_digest"
    assert sent == []


def test_dispatch_finding_survives_send_failure():
    def boom(_msg):
        raise RuntimeError("channel down")

    route = NotificationSystem().dispatch_finding(
        _finding(), NotificationPreference(business_id="biz1"), boom
    )
    assert route == "immediate"  # delivery failure never breaks the run


# ── Registry factory + agent bridge registration ────────────────────────────


def test_create_default_registry_covers_archetypes():
    registry = create_default_registry()
    local = {w.name for w in registry.get_watchers_for_archetype("local_service")}
    assert "website_health" in local
    assert "speed_to_lead" in local
    ecom = {w.name for w in registry.get_watchers_for_archetype("ecommerce")}
    assert "website_health" in ecom


def test_watchers_tick_registered_in_task_handlers():
    from agent.tasks import TASK_HANDLERS

    assert TASK_HANDLERS["watchers_tick"].__name__ == "WatchersTickTask"


# ── Proposal-path memory retrieval ──────────────────────────────────────────


def test_action_from_finding_attaches_prior_learnings(tmp_path):
    import json

    from kai.runtime.local_service import action_from_finding

    memory_dir = tmp_path / "memory"
    memory_dir.mkdir()
    (memory_dir / "entry1.json").write_text(
        json.dumps(
            {
                "brand_id": "b1",
                "retrieval_tags": ["website"],
                "note": "homepage rewrite lifted conversions",
            }
        )
    )

    action = action_from_finding(
        {"title": "Website down", "category": "website_health"},
        brand_id="b1",
        base_dir=tmp_path,
    )
    learnings = action["proposed_changes"]["prior_learnings"]
    assert len(learnings) == 1
    assert learnings[0]["note"] == "homepage rewrite lifted conversions"


def test_action_from_finding_without_base_dir_is_unchanged():
    from kai.runtime.local_service import action_from_finding

    action = action_from_finding({"title": "Website down"}, brand_id="b1")
    assert action["proposed_changes"]["prior_learnings"] == []
