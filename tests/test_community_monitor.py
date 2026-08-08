import json
from pathlib import Path

from scripts.community_monitor.sources import collect, file_drop


def test_indexed_sources_are_source_neutral_and_evidence_bound():
    profile = {"keywords": ["missed calls"], "sources": [
        {"id": "quora", "enabled": True, "access_mode": "indexed_public", "queries": ["q"]},
        {"id": "g2_reviews", "enabled": True, "access_mode": "indexed_public", "queries": ["g"]},
    ]}
    fetch = lambda q: [{"title": q, "original_text": "We keep having missed calls", "original_text_is_full": False, "url": f"https://example.com/{q}"}]
    rows, status = collect(profile, env={}, indexed_fetcher=fetch)
    assert {row["source"] for row in rows} == {"quora", "g2_reviews"}
    assert all(row["source_mode"] == "indexed_public" for row in rows)
    assert status["quora"]["accepted"] == 1


def test_authenticated_file_drop_keeps_full_original(tmp_path: Path):
    row = {"url": "https://linkedin.com/posts/x", "original_text": "missed calls", "original_text_is_full": True}
    (tmp_path / "in.jsonl").write_text(json.dumps(row) + "\n", encoding="utf-8")
    profile = {"keywords": ["missed calls"], "sources": [
        {"id": "linkedin_public_posts", "enabled": True, "access_mode": "authenticated_file_drop", "import_dir": str(tmp_path)}
    ]}
    rows, _ = collect(profile, env={})
    assert rows[0]["original_text"] == "missed calls"
    assert rows[0]["original_text_is_full"] is True
    assert file_drop(tmp_path) == [row]
