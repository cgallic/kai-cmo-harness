from __future__ import annotations

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.intel.brand_pulse import (
    BrandPulseQuery,
    build_query_plan,
    normalize_search_items,
    run_brand_pulse,
)


def test_build_query_plan_includes_social_review_and_competitor_fallbacks():
    plan = build_query_plan(
        "KaiCalls",
        ["Smith.ai"],
        category="AI receptionist",
        domain="https://kaicalls.com",
    )
    queries = [item.query for item in plan]

    assert any("site:x.com" in query and "KaiCalls" in query for query in queries)
    assert any("site:linkedin.com/posts" in query for query in queries)
    assert any("site:reddit.com" in query and "KaiCalls" in query for query in queries)
    assert any("site:g2.com" in query for query in queries)
    assert any('site:kaicalls.com "KaiCalls"' in query for query in queries)
    assert any('"KaiCalls" vs "Smith.ai"' in query for query in queries)


def test_normalize_search_items_adds_citation_and_objection_tags():
    query = BrandPulseQuery(
        platform="reviews",
        intent="reviews",
        entity="KaiCalls",
        query='"KaiCalls" review',
    )
    raw = {
        "organic_results": [
            {
                "position": 1,
                "title": "KaiCalls pricing review",
                "link": "https://example.com/kaicalls-review",
                "snippet": "KaiCalls is expensive, but support is fast.",
                "displayed_link": "example.com",
            }
        ]
    }

    items = normalize_search_items(query, raw, "raw/reviews.json")

    assert len(items) == 1
    assert items[0].citation_id.startswith("reviews-")
    assert items[0].source_url == "https://example.com/kaicalls-review"
    assert items[0].sentiment == "mixed"
    assert "pricing" in items[0].objection_tags
    assert "support" in items[0].objection_tags


def test_run_brand_pulse_skip_fetch_writes_packets_and_data_gaps(tmp_path, monkeypatch):
    monkeypatch.delenv("SERPAPI_API_KEY", raising=False)
    out_dir = tmp_path / "brand-pulse"
    db_path = tmp_path / "brand-pulse.db"

    dataset = run_brand_pulse(
        "KaiCalls",
        competitors=["Smith.ai"],
        category="AI receptionist",
        domain="https://kaicalls.com",
        out_dir=out_dir,
        db_path=db_path,
        skip_fetch=True,
    )

    assert dataset["brand"] == "KaiCalls"
    assert dataset["evidence"] == []
    assert dataset["data_gaps"]
    assert (out_dir / "brand-pulse-data.json").exists()
    assert (out_dir / "_brand-pulse.md").exists()
    assert (out_dir / "_data-gaps.md").exists()
    assert (out_dir / "raw" / "query-plan.json").exists()
    assert (out_dir / "platforms" / "reddit.md").exists()
    assert db_path.exists()
