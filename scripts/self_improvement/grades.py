"""Shared grade/schema helpers for the learning loop.

``performance_30d`` has drifted across writers over time:

  - dict ``{"gsc": ..., "ga4": ..., "grade": ..., "checked_at": ...}``
    (current schema, written by performance_check.py)
  - bare string grade (legacy readers/writers stored just the grade)
  - ``None`` / missing (not yet measured)

The grade vocabulary is ``winner | average | underperformer`` — the bottom
grade is "underperformer" everywhere. Some legacy entries used "loser";
normalize it here so readers never have to know it existed.

Publish timestamps drifted the same way: the content log writes
``published_at``, but some legacy entries carry ``publish_date``.

Every reader of the content log should go through these helpers instead of
poking at the raw fields.
"""

from __future__ import annotations

GRADE_WINNER = "winner"
GRADE_AVERAGE = "average"
GRADE_UNDERPERFORMER = "underperformer"

_LEGACY_GRADE_ALIASES = {"loser": GRADE_UNDERPERFORMER}


def get_grade(entry) -> str | None:
    """Return the 30-day grade for a content-log entry, or None if ungraded.

    Tolerates ``performance_30d`` as a dict (current schema), a bare string
    (legacy), or None/missing. Normalizes the legacy "loser" grade to
    "underperformer".
    """
    if not isinstance(entry, dict):
        return None
    perf = entry.get("performance_30d")
    if isinstance(perf, dict):
        grade = perf.get("grade")
    elif isinstance(perf, str):
        grade = perf
    else:
        return None
    if not grade or not isinstance(grade, str):
        return None
    grade = grade.strip().lower()
    return _LEGACY_GRADE_ALIASES.get(grade, grade)


def get_published_at(entry) -> str | None:
    """Return the publish timestamp for a content-log entry, or None.

    Prefers ``published_at`` (current field) with fallback to the legacy
    ``publish_date`` field.
    """
    if not isinstance(entry, dict):
        return None
    return entry.get("published_at") or entry.get("publish_date") or None
