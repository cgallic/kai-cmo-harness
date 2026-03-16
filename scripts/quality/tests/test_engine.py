"""Tests for the quality engine."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from scripts.quality.engine import QualityEngine


FIXTURES = Path(__file__).parent / "fixtures"


async def test_score_perfect():
    engine = QualityEngine(use_llm=False)
    report = await engine.score(str(FIXTURES / "perfect.md"))
    print(f"  perfect.md: {report.overall_score:.0f}/100 ({report.overall_grade})")
    assert report.overall_score >= 60, f"Expected 60+, got {report.overall_score}"
    assert report.overall_grade in ("A", "B", "C")


async def test_score_terrible():
    engine = QualityEngine(use_llm=False)
    report = await engine.score(str(FIXTURES / "terrible.md"))
    print(f"  terrible.md: {report.overall_score:.0f}/100 ({report.overall_grade})")
    assert report.overall_score < 75, f"Expected <75, got {report.overall_score}"


async def test_score_needs_work():
    engine = QualityEngine(use_llm=False)
    report = await engine.score(str(FIXTURES / "needs-work.md"))
    print(f"  needs-work.md: {report.overall_score:.0f}/100 ({report.overall_grade})")
    # Should be between terrible and perfect
    assert 30 < report.overall_score < 90


async def test_perfect_beats_terrible():
    engine = QualityEngine(use_llm=False)
    perfect = await engine.score(str(FIXTURES / "perfect.md"))
    terrible = await engine.score(str(FIXTURES / "terrible.md"))
    assert perfect.overall_score > terrible.overall_score, (
        f"perfect ({perfect.overall_score}) should beat terrible ({terrible.overall_score})"
    )


async def test_rule_set_filter():
    engine = QualityEngine(rule_sets=["aa"], use_llm=False)
    report = await engine.score(str(FIXTURES / "perfect.md"))
    # Should only have AA category
    categories = [c.category.value for c in report.categories]
    assert "Algorithmic Authorship" in categories
    assert "GEO/AEO Signals" not in categories


async def test_report_metadata():
    engine = QualityEngine(use_llm=False)
    report = await engine.score(str(FIXTURES / "perfect.md"))
    assert report.metadata["word_count"] > 0
    assert report.metadata["sentence_count"] > 0
    assert report.file_path.endswith("perfect.md")


async def test_report_to_dict():
    engine = QualityEngine(use_llm=False)
    report = await engine.score(str(FIXTURES / "perfect.md"))
    d = report.to_dict()
    assert "overall_score" in d
    assert "overall_grade" in d
    assert "categories" in d
    assert "top_fixes" in d
    assert "metadata" in d


async def run_all():
    print("Engine tests:")
    await test_score_perfect()
    await test_score_terrible()
    await test_score_needs_work()
    await test_perfect_beats_terrible()
    await test_rule_set_filter()
    await test_report_metadata()
    await test_report_to_dict()
    print("All engine tests passed!")


if __name__ == "__main__":
    asyncio.run(run_all())
