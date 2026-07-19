"""Expert-drift monitor: registry from doc sources, feed parse, drift diff."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.intel.expert_drift import (  # noqa: E402
    build_registry,
    check_drift,
    discover_feeds,
    extract_source_domains,
    parse_feed,
    write_report,
)

DOC = """# Test Expert: Knowledge Distillation

**Created:** July 2026

Body text with a stray link https://en.wikipedia.org/wiki/Ignored that is NOT in Sources.

## Sources

- https://example.com/post/one — first
- https://example.com/post/two — second
- https://blog.other.io/essay — third
- https://en.wikipedia.org/wiki/Something — infrastructure, skipped
- https://www.google.com/search?q=x — skipped
"""

RSS = """<?xml version="1.0"?>
<rss version="2.0"><channel><title>t</title>
<item><title>Post A</title><link>https://example.com/a</link><guid>id-a</guid><pubDate>Wed, 01 Jul 2026 00:00:00 GMT</pubDate></item>
<item><title>Post B</title><link>https://example.com/b</link><guid>id-b</guid></item>
</channel></rss>"""

ATOM = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom"><title>t</title>
<entry><title>Atom A</title><id>atom-a</id><link href="https://x.io/a"/><updated>2026-07-01</updated></entry>
</feed>"""


def test_extract_source_domains_ranks_and_skips():
    domains = extract_source_domains(DOC)
    assert domains[0] == "example.com"  # cited twice, ranked first
    assert "blog.other.io" in domains
    assert "en.wikipedia.org" not in domains
    assert all("google" not in d for d in domains)


def test_extract_ignores_links_outside_sources_section():
    assert extract_source_domains("no sources section https://example.com/x") == []


def test_build_registry_preserves_verified_feeds(tmp_path):
    (tmp_path / "test-expert-knowledge.md").write_text(DOC)
    existing = {"test-expert": {"feeds": ["https://example.com/feed"]}}
    registry = build_registry(tmp_path, existing)
    assert registry["test-expert"]["doc"] == "knowledge/people/test-expert-knowledge.md"
    assert registry["test-expert"]["feeds"] == ["https://example.com/feed"]
    assert registry["test-expert"]["domains"][0] == "example.com"


def test_parse_feed_rss_and_atom_and_junk():
    rss_items = parse_feed(RSS)
    assert [i["id"] for i in rss_items] == ["id-a", "id-b"]
    assert rss_items[0]["title"] == "Post A"
    atom_items = parse_feed(ATOM)
    assert atom_items[0]["id"] == "atom-a"
    assert atom_items[0]["link"] == "https://x.io/a"
    assert parse_feed("<html>not a feed</html>") == []
    assert parse_feed("total junk {") == []


def test_discover_keeps_only_verified_feeds():
    registry = {"e": {"doc": "d", "domains": ["good.com", "dead.com"], "feeds": []}}

    def fetch(url, timeout=15):
        return RSS if url == "https://good.com/feed" else None

    out = discover_feeds(registry, fetch=fetch)
    assert out["e"]["feeds"] == ["https://good.com/feed"]


def test_check_drift_seeds_silently_then_reports_new_items():
    registry = {"e": {"doc": "knowledge/people/e-knowledge.md", "domains": [], "feeds": ["https://f/feed"]}}
    feed_v1 = RSS
    feed_v2 = RSS.replace(
        "</channel></rss>",
        '<item><title>Post C</title><link>https://example.com/c</link><guid>id-c</guid></item></channel></rss>',
    )

    # First sighting: state seeded, nothing reported (backfill is not drift).
    new1, state = check_drift(registry, {}, fetch=lambda u, timeout=15: feed_v1)
    assert new1 == {}
    assert set(state["https://f/feed"]["seen_ids"]) == {"id-a", "id-b"}

    # Unchanged feed: still quiet.
    new2, state = check_drift(registry, state, fetch=lambda u, timeout=15: feed_v1)
    assert new2 == {}

    # New item appears: reported once, then absorbed into state.
    new3, state = check_drift(registry, state, fetch=lambda u, timeout=15: feed_v2)
    assert [i["id"] for i in new3["e"]] == ["id-c"]
    assert "id-c" in state["https://f/feed"]["seen_ids"]
    new4, _ = check_drift(registry, state, fetch=lambda u, timeout=15: feed_v2)
    assert new4 == {}


def test_check_drift_survives_dead_feed():
    registry = {"e": {"doc": "d", "domains": [], "feeds": ["https://dead/feed"]}}
    new, state = check_drift(registry, {}, fetch=lambda u, timeout=15: None)
    assert new == {}
    assert state == {}  # dead feed leaves no state


def test_write_report(tmp_path):
    report_file = tmp_path / "report.md"
    registry = {"e": {"doc": "knowledge/people/e-knowledge.md"}}
    new = {"e": [{"id": "id-c", "title": "Post C", "link": "https://example.com/c", "published": "", "feed": "f"}]}
    text = write_report(new, registry, report_file)
    assert "Post C" in text
    assert "knowledge/people/e-knowledge.md" in text
    assert report_file.exists()
    empty = write_report({}, registry, report_file)
    assert "quiet" in empty
