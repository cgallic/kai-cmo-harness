"""AutoReason orchestrator — runs the 5-role tournament until k=2 convergence.

Pure module: takes (incumbent, knowledge_bundle) and returns
(winner, passes, converged_reason). Has no Discord, no Meta uploads, no side
effects beyond LLM calls.
"""

from __future__ import annotations

import random
from typing import Any

from . import roles
from .knowledge import validate_banned_phrases, validate_brand_lock
from .trace import (
    AdCopy,
    Pass,
    aggregate_borda,
    pick_winner,
)

K_CONSECUTIVE = 2     # paper-validated convergence threshold
MAX_PASSES = 5        # hard cap (paper avg was 3.9)
JUDGE_PANEL_SIZE = 3
MAX_REAUTHOR_ATTEMPTS = 2  # if B violates brand lock or banned words


def _validate(ad: AdCopy) -> list[str]:
    """Return human-readable rejection reasons (empty if clean)."""
    reasons: list[str] = []
    bl = validate_brand_lock(ad)
    if bl:
        reasons.append(f"brand-lock drift: {', '.join(bl)}")
    bp = validate_banned_phrases(ad)
    if bp:
        reasons.append(f"Tier 1 banned phrases: {', '.join(bp)}")
    return reasons


def _safe_author_b(incumbent: AdCopy, critique: dict) -> tuple[AdCopy, list[str]]:
    """Run author_b. If output violates lock/banned, re-author up to MAX_REAUTHOR
    times. If still bad, return the last attempt + the rejection notes — the
    judges will see it but the brand-lock prompt instructs them to last-place it."""
    notes: list[str] = []
    last: AdCopy | None = None
    for attempt in range(MAX_REAUTHOR_ATTEMPTS + 1):
        b = roles.author_b(incumbent, critique)
        v = _validate(b)
        if not v:
            return b, notes
        notes.append(f"Author B attempt {attempt + 1} rejected: {'; '.join(v)}")
        last = b
    assert last is not None
    return last, notes


def _safe_synthesize(a: AdCopy, b: AdCopy, label_x_is: str) -> tuple[AdCopy, list[str]]:
    notes: list[str] = []
    last: AdCopy | None = None
    for attempt in range(MAX_REAUTHOR_ATTEMPTS + 1):
        ab = roles.synthesizer(a, b, label_x_is)
        v = _validate(ab)
        if not v:
            return ab, notes
        notes.append(f"Synthesizer attempt {attempt + 1} rejected: {'; '.join(v)}")
        last = ab
    assert last is not None
    return last, notes


def _shuffle_labels(rng: random.Random) -> dict[str, str]:
    """Map randomized P/Q/R judge labels to underlying roles A/AB/B."""
    roles_list = ["A", "AB", "B"]
    rng.shuffle(roles_list)
    return dict(zip(["P", "Q", "R"], roles_list))


def run_loop(
    incumbent: AdCopy,
    perf: dict,
    top_ads: list[dict],
    bottom_ads: list[dict],
    *,
    max_passes: int = MAX_PASSES,
    rng_seed: int | None = None,
    on_pass_end: Any = None,  # optional callback(pass_obj) for streaming logs
) -> tuple[AdCopy, list[Pass], str]:
    """Run the AutoReason tournament. Returns (winner, passes, converged_reason)."""
    rng = random.Random(rng_seed)
    passes: list[Pass] = []
    consecutive_a_wins = 0
    current_a = incumbent

    for pass_index in range(1, max_passes + 1):
        critique = roles.critic(current_a, perf, top_ads, bottom_ads)

        revision_b, b_notes = _safe_author_b(current_a, critique)

        # Synthesizer sees A and B under randomized X/Y labels
        x_is = rng.choice(["A", "B"])
        synthesis_ab, ab_notes = _safe_synthesize(current_a, revision_b, x_is)

        # Build randomized P/Q/R panel for judges
        label_map = _shuffle_labels(rng)
        role_to_ad = {"A": current_a, "AB": synthesis_ab, "B": revision_b}
        candidates_pqr = {label: role_to_ad[role] for label, role in label_map.items()}

        # Three judges, fresh agents
        votes = [
            roles.judge(candidates_pqr, perf, top_ads, judge_index=i + 1)
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

        # Convergence check
        if winner_role == "A":
            consecutive_a_wins += 1
        else:
            consecutive_a_wins = 0
            current_a = synthesis_ab if winner_role == "AB" else revision_b

        if consecutive_a_wins >= K_CONSECUTIVE:
            return current_a, passes, f"converged: incumbent won {K_CONSECUTIVE} consecutive passes"

    return current_a, passes, f"hit max_passes={max_passes} cap without k=2 convergence"
