"""AutoReason orchestrator for the homepage CRO tournament.

Same shape as scripts/ads/autoreason/loop.py — 5-role tournament, k=2
convergence, randomized P/Q/R judge labels — but the unit under test is a
HomepageZones bundle and the validators look at the four homepage zones
instead of an AdCopy.
"""

from __future__ import annotations

import random
from typing import Any

from . import roles
from .knowledge import validate_banned_phrases, validate_brand_lock
from .trace import (
    HomepageZones,
    Pass,
    aggregate_borda,
    pick_winner,
)

K_CONSECUTIVE = 2
MAX_PASSES = 5
JUDGE_PANEL_SIZE = 3
MAX_REAUTHOR_ATTEMPTS = 2


def _validate(zones: HomepageZones) -> list[str]:
    reasons: list[str] = []
    bl = validate_brand_lock(zones)
    if bl:
        reasons.append(f"brand-lock drift: {', '.join(bl)}")
    bp = validate_banned_phrases(zones)
    if bp:
        reasons.append(f"Tier 1 banned phrases: {', '.join(bp)}")
    return reasons


def _safe_author_b(incumbent: HomepageZones, critique: dict,
                   context: dict) -> tuple[HomepageZones, list[str]]:
    notes: list[str] = []
    last: HomepageZones | None = None
    for attempt in range(MAX_REAUTHOR_ATTEMPTS + 1):
        b = roles.author_b(incumbent, critique, context)
        v = _validate(b)
        if not v:
            return b, notes
        notes.append(f"Author B attempt {attempt + 1} rejected: {'; '.join(v)}")
        last = b
    assert last is not None
    return last, notes


def _safe_synthesize(a: HomepageZones, b: HomepageZones, label_x_is: str,
                     context: dict) -> tuple[HomepageZones, list[str]]:
    notes: list[str] = []
    last: HomepageZones | None = None
    for attempt in range(MAX_REAUTHOR_ATTEMPTS + 1):
        ab = roles.synthesizer(a, b, label_x_is, context)
        v = _validate(ab)
        if not v:
            return ab, notes
        notes.append(f"Synthesizer attempt {attempt + 1} rejected: {'; '.join(v)}")
        last = ab
    assert last is not None
    return last, notes


def _shuffle_labels(rng: random.Random) -> dict[str, str]:
    roles_list = ["A", "AB", "B"]
    rng.shuffle(roles_list)
    return dict(zip(["P", "Q", "R"], roles_list))


def run_loop(
    incumbent: HomepageZones,
    context: dict,
    *,
    max_passes: int = MAX_PASSES,
    rng_seed: int | None = None,
    on_pass_end: Any = None,
) -> tuple[HomepageZones, list[Pass], str]:
    rng = random.Random(rng_seed)
    passes: list[Pass] = []
    consecutive_a_wins = 0
    current_a = incumbent

    for pass_index in range(1, max_passes + 1):
        critique = roles.critic(current_a, context)
        revision_b, b_notes = _safe_author_b(current_a, critique, context)

        x_is = rng.choice(["A", "B"])
        synthesis_ab, ab_notes = _safe_synthesize(current_a, revision_b, x_is, context)

        label_map = _shuffle_labels(rng)
        role_to_zones = {"A": current_a, "AB": synthesis_ab, "B": revision_b}
        candidates_pqr = {label: role_to_zones[role] for label, role in label_map.items()}

        votes = [
            roles.judge(candidates_pqr, context, judge_index=i + 1)
            for i in range(JUDGE_PANEL_SIZE)
        ]

        borda = aggregate_borda(votes, label_map)
        winner_role = pick_winner(borda, incumbent_label="A")

        p = Pass(
            pass_index=pass_index,
            incumbent=current_a,
            critique=critique,
            revision_b=revision_b,
            synthesis_ab=synthesis_ab,
            label_map=label_map,
            judge_votes=votes,
            borda_by_role=borda,
            winner_role=winner_role,
            auto_reject_notes=b_notes + ab_notes,
        )
        passes.append(p)
        if on_pass_end is not None:
            on_pass_end(p)

        if winner_role == "A":
            consecutive_a_wins += 1
        else:
            consecutive_a_wins = 0
            current_a = synthesis_ab if winner_role == "AB" else revision_b

        if consecutive_a_wins >= K_CONSECUTIVE:
            return (
                current_a,
                passes,
                f"converged: incumbent won {K_CONSECUTIVE} consecutive passes",
            )

    return current_a, passes, f"hit max_passes={max_passes} cap without k=2 convergence"
