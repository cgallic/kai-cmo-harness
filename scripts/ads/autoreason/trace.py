"""Per-pass trace records and Discord formatter for the AutoReason loop."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class AdCopy:
    headline: str
    primary_text: str
    description: str
    cta: str
    link: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JudgeVote:
    judge_index: int
    ranking: list[str]
    scores: dict[str, int]
    reasoning: dict[str, str]


@dataclass
class Pass:
    """One iteration of the 5-role tournament."""

    pass_index: int  # 1-based
    incumbent: AdCopy
    critique: dict
    revision_b: AdCopy
    synthesis_ab: AdCopy
    label_map: dict[str, str]  # e.g. {"P": "AB", "Q": "A", "R": "B"}
    judge_votes: list[JudgeVote] = field(default_factory=list)
    borda_by_role: dict[str, int] = field(default_factory=dict)  # A/AB/B → total points
    winner_role: str = ""  # 'A' | 'AB' | 'B'
    auto_reject_notes: list[str] = field(default_factory=list)


def aggregate_borda(votes: list[JudgeVote], label_map: dict[str, str]) -> dict[str, int]:
    """Sum judge scores by underlying role (A/AB/B), unmasking the randomized labels."""
    totals: dict[str, int] = {"A": 0, "AB": 0, "B": 0}
    for v in votes:
        for label, points in v.scores.items():
            role = label_map[label]
            totals[role] += points
    return totals


def pick_winner(borda: dict[str, int], incumbent_label: str = "A") -> str:
    """Highest Borda total. Conservative tiebreak: incumbent (A) wins ties."""
    max_score = max(borda.values())
    leaders = [r for r, s in borda.items() if s == max_score]
    if incumbent_label in leaders:
        return incumbent_label
    return leaders[0]


def format_discord_trace(passes: list[Pass], ad_set_name: str, winner: AdCopy,
                         converged_reason: str) -> str:
    """Render the full pass-by-pass trace as a Discord-friendly message."""
    lines: list[str] = []
    lines.append(f"**AutoReason loop — {ad_set_name}**")
    lines.append(f"Passes: {len(passes)}  •  {converged_reason}")
    lines.append("")

    for p in passes:
        lines.append(f"__Pass {p.pass_index}__")
        if p.auto_reject_notes:
            for note in p.auto_reject_notes:
                lines.append(f"  ⚠ {note}")
        lines.append(f"  **A (incumbent)**  `{p.incumbent.headline}` — {p.incumbent.primary_text[:80]}")
        lines.append(f"  **B (revision)**   `{p.revision_b.headline}` — {p.revision_b.primary_text[:80]}")
        lines.append(f"  **AB (synthesis)** `{p.synthesis_ab.headline}` — {p.synthesis_ab.primary_text[:80]}")

        # Judge votes — show one-line summary per judge
        for v in p.judge_votes:
            unmasked = {p.label_map[label]: pts for label, pts in v.scores.items()}
            order = sorted(unmasked.items(), key=lambda kv: -kv[1])
            line = "  ".join(f"{role}={pts}" for role, pts in order)
            lines.append(f"  Judge {v.judge_index}: {line}")

        # Borda totals
        borda_str = "  ".join(f"{r}={s}" for r, s in sorted(p.borda_by_role.items(), key=lambda kv: -kv[1]))
        lines.append(f"  **Borda:** {borda_str}  →  winner: **{p.winner_role}**")
        lines.append("")

    lines.append("__Final winner__")
    lines.append(f"```")
    lines.append(f"Headline:     {winner.headline}")
    lines.append(f"Primary text: {winner.primary_text}")
    lines.append(f"Description:  {winner.description}")
    lines.append(f"CTA:          {winner.cta}")
    lines.append(f"```")
    lines.append("")
    lines.append("React ✅ to wire this into `ad_loop.py` step 3 / ❌ to reject.")
    return "\n".join(lines)


def trace_to_json(passes: list[Pass]) -> str:
    """Full JSON dump for offline inspection."""
    return json.dumps([asdict(p) for p in passes], indent=2, default=str)
