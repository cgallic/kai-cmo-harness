"""
Keyword Opportunity Scorer — Score keywords by growth potential.

Combines position, impressions, CTR gap, and competition signals
into a single opportunity score (0-100).

Usage:
    score = score_keyword(position=8, impressions=1240, ctr=1.8, clicks=22)
    # score = 92 (position 8 with high impressions = striking distance)
"""


def score_keyword(
    position: float,
    impressions: int,
    ctr: float = 0.0,
    clicks: int = 0,
    has_content: bool = False,
) -> int:
    """
    Score a keyword's opportunity from 0-100.

    Factors:
    - Position gap: keywords at 5-20 have the most upside (striking distance)
    - Impression volume: more impressions = bigger opportunity
    - CTR gap: current CTR vs expected CTR for position = room for improvement
    - Existing content: lower score if we already target this keyword
    """
    # Position score (0-40): closer to page 1 = higher
    if position <= 3:
        pos_score = 10  # Already ranking well, limited upside
    elif position <= 10:
        pos_score = 35 - (position - 3) * 2  # Page 1 but room to improve
    elif position <= 20:
        pos_score = 40 - (position - 10)  # Striking distance — highest opportunity
    elif position <= 50:
        pos_score = 30 - (position - 20) * 0.5
    else:
        pos_score = max(5, 20 - (position - 50) * 0.3)

    # Impression score (0-30): more impressions = bigger prize
    if impressions >= 5000:
        imp_score = 30
    elif impressions >= 1000:
        imp_score = 20 + (impressions - 1000) / 400
    elif impressions >= 100:
        imp_score = 10 + (impressions - 100) / 90
    else:
        imp_score = max(2, impressions / 10)

    # CTR gap score (0-20): low CTR at good position = improvement opportunity
    expected_ctr = _expected_ctr_for_position(position)
    ctr_gap = max(0, expected_ctr - ctr)
    ctr_score = min(20, ctr_gap * 5)

    # Penalty for existing content (-15 if we already have a page targeting this)
    content_penalty = -15 if has_content else 0

    total = pos_score + imp_score + ctr_score + content_penalty
    return max(0, min(100, int(total)))


def _expected_ctr_for_position(position: float) -> float:
    """Expected CTR for a given search position (2026 benchmarks)."""
    # Based on aggregated CTR curves
    ctr_curve = {
        1: 28.5, 2: 15.7, 3: 11.0, 4: 8.0, 5: 6.3,
        6: 4.8, 7: 3.5, 8: 2.8, 9: 2.4, 10: 2.0,
        15: 1.0, 20: 0.5, 30: 0.3, 50: 0.1,
    }
    # Interpolate
    prev_pos, prev_ctr = 1, 28.5
    for pos, ctr in sorted(ctr_curve.items()):
        if position <= pos:
            # Linear interpolation
            ratio = (position - prev_pos) / (pos - prev_pos) if pos != prev_pos else 0
            return prev_ctr + ratio * (ctr - prev_ctr)
        prev_pos, prev_ctr = pos, ctr
    return 0.05


def rank_keywords(keywords: list[dict]) -> list[dict]:
    """
    Rank a list of keyword dicts by opportunity score.
    Each dict should have: query, position, impressions, ctr, clicks.
    Returns sorted list with 'opportunity_score' added.
    """
    for kw in keywords:
        kw["opportunity_score"] = score_keyword(
            position=kw.get("position", 100),
            impressions=kw.get("impressions", 0),
            ctr=kw.get("ctr", 0),
            clicks=kw.get("clicks", 0),
            has_content=kw.get("has_content", False),
        )
    return sorted(keywords, key=lambda k: k["opportunity_score"], reverse=True)
