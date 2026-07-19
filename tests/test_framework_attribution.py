"""Framework attribution: content-log field, engine loader paths, aggregator."""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from scripts.content.content_log import log_entry  # noqa: E402
from scripts.self_improvement.framework_attribution import (  # noqa: E402
    aggregate,
    review_candidates,
)

FW_A = "knowledge/frameworks/content-copywriting/algorithmic-authorship.md"
FW_B = "knowledge/channels/email-lifecycle.md"


def _entry(frameworks=None, grade=None, fmt="blog"):
    entry = {"site": "s", "format": fmt}
    if frameworks is not None:
        entry["frameworks"] = frameworks
    if grade is not None:
        entry["performance_30d"] = {"grade": grade}
    return entry


def test_log_entry_stores_frameworks(tmp_path):
    log_file = str(tmp_path / "log.json")
    entry = log_entry(
        url=None,
        keyword="k",
        site="site-a",
        format="blog",
        content_hash="hash-1",
        frameworks=[FW_A],
        log_file=log_file,
    )
    assert entry["frameworks"] == [FW_A]
    saved = json.loads(Path(log_file).read_text())
    assert saved[0]["frameworks"] == [FW_A]


def test_log_entry_dedupe_updates_frameworks(tmp_path):
    log_file = str(tmp_path / "log.json")
    log_entry(
        url=None, keyword="k", site="site-a", format="blog",
        content_hash="hash-1", frameworks=[], log_file=log_file,
    )
    entry = log_entry(
        url=None, keyword="k", site="site-a", format="blog",
        content_hash="hash-1", frameworks=[FW_A, FW_B], log_file=log_file,
    )
    assert entry["frameworks"] == [FW_A, FW_B]
    saved = json.loads(Path(log_file).read_text())
    assert len(saved) == 1  # deduped, not appended


def test_log_entry_defaults_frameworks_to_empty_list(tmp_path):
    log_file = str(tmp_path / "log.json")
    entry = log_entry(
        url=None, keyword="k", site="site-a", format="blog",
        content_hash="hash-2", log_file=log_file,
    )
    assert entry["frameworks"] == []


def test_engine_loader_returns_loaded_paths(tmp_path):
    from scripts.content.engine import _load_framework_texts

    repo = tmp_path / "repo"
    target = repo / FW_A
    target.parent.mkdir(parents=True)
    target.write_text("# Algorithmic Authorship\nrules")
    text, paths = _load_framework_texts("blog", repo, tmp_path / "nowhere")
    assert paths == [FW_A]
    assert "Algorithmic Authorship" in text
    # Missing files load nothing and attribute nothing.
    text_none, paths_none = _load_framework_texts("blog", tmp_path / "empty", tmp_path / "empty2")
    assert paths_none == []
    assert text_none == ""


def test_aggregate_counts_and_winner_rate():
    entries = [
        _entry([FW_A], "winner"),
        _entry([FW_A], "underperformer"),
        _entry([FW_A], None),
        _entry([FW_A, FW_B], "winner"),
        _entry([FW_B], "loser"),  # legacy alias -> underperformer
    ]
    stats = aggregate(entries)
    assert stats[FW_A]["winner"] == 2
    assert stats[FW_A]["underperformer"] == 1
    assert stats[FW_A]["ungraded"] == 1
    assert stats[FW_A]["graded"] == 3
    assert stats[FW_A]["winner_rate"] == round(2 / 3, 3)
    assert stats[FW_B]["underperformer"] == 1
    assert stats[FW_B]["winner"] == 1
    assert stats[FW_B]["inferred"] == 0


def test_aggregate_infers_frameworks_for_legacy_entries():
    # No frameworks field: attributed via GENERATION_FRAMEWORK_MAP by format.
    stats = aggregate([_entry(None, "winner", fmt="blog")])
    assert stats[FW_A]["winner"] == 1
    assert stats[FW_A]["inferred"] == 1


def test_aggregate_skips_unattributable_entries():
    stats = aggregate([{"site": "s"}, "junk", None])
    assert stats == {}


def test_review_candidates_threshold():
    entries = (
        [_entry([FW_A], "underperformer")] * 3
        + [_entry([FW_B], "underperformer")]  # only 1 graded — below min
        + [_entry([FW_B], None)]
    )
    stats = aggregate(entries)
    flagged = review_candidates(stats, min_graded=3, flag_below=0.34)
    assert flagged == [FW_A]
