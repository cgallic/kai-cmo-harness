"""Per-pass trace records for the homepage AutoReason CRO loop.

Same tournament mechanics as scripts/ads/autoreason/trace.py, but the unit
under test is a set of *homepage zones* (hero headline, sub-hero, primary
CTA, feature framing) rather than a single Meta ad.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class HomepageZones:
    """The mutable language surfaces on the KaiCalls homepage that the
    tournament rewrites. The page has more sections than this — we test the
    high-leverage ones first."""

    hero_headline: str            # e.g. "Your Digital Secretary"
    sub_hero: str                 # 1–2 sentence body under the headline
    primary_cta: str              # e.g. "Get Your Secretary"
    feature_frame: str            # the framing line for the "What Kai Does" section

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class JudgeVote:
    judge_index: int
    ranking: list[str]
    scores: dict[str, int]
    axis_scores: dict[str, dict[str, int]]  # candidate → {axis: 1..5}
    reasoning: dict[str, str]


@dataclass
class Pass:
    """One iteration of the 5-role tournament."""

    pass_index: int
    incumbent: HomepageZones
    critique: dict
    revision_b: HomepageZones
    synthesis_ab: HomepageZones
    label_map: dict[str, str]
    judge_votes: list[JudgeVote] = field(default_factory=list)
    borda_by_role: dict[str, int] = field(default_factory=dict)
    winner_role: str = ""
    auto_reject_notes: list[str] = field(default_factory=list)


def aggregate_borda(votes: list[JudgeVote], label_map: dict[str, str]) -> dict[str, int]:
    totals: dict[str, int] = {"A": 0, "AB": 0, "B": 0}
    for v in votes:
        for label, points in v.scores.items():
            role = label_map[label]
            totals[role] += points
    return totals


def pick_winner(borda: dict[str, int], incumbent_label: str = "A") -> str:
    max_score = max(borda.values())
    leaders = [r for r, s in borda.items() if s == max_score]
    if incumbent_label in leaders:
        return incumbent_label
    return leaders[0]


def format_report(passes: list[Pass], winner: HomepageZones,
                  converged_reason: str, source_label: str) -> str:
    """Markdown report — wiki-page-ready (no Discord-specific size limits)."""
    lines: list[str] = []
    lines.append(f"# KaiCalls homepage — AutoReason CRO tournament")
    lines.append(f"")
    lines.append(f"- Source: {source_label}")
    lines.append(f"- Passes: {len(passes)}")
    lines.append(f"- Convergence: {converged_reason}")
    lines.append(f"")

    for p in passes:
        lines.append(f"## Pass {p.pass_index}")
        if p.auto_reject_notes:
            for note in p.auto_reject_notes:
                lines.append(f"- ⚠ {note}")
            lines.append("")
        lines.append(f"**A (incumbent)**")
        lines.append(f"- Hero: `{p.incumbent.hero_headline}`")
        lines.append(f"- Sub: {p.incumbent.sub_hero}")
        lines.append(f"- CTA: `{p.incumbent.primary_cta}`")
        lines.append(f"- Feature frame: {p.incumbent.feature_frame}")
        lines.append("")
        lines.append(f"**B (adversarial revision)**")
        lines.append(f"- Hero: `{p.revision_b.hero_headline}`")
        lines.append(f"- Sub: {p.revision_b.sub_hero}")
        lines.append(f"- CTA: `{p.revision_b.primary_cta}`")
        lines.append(f"- Feature frame: {p.revision_b.feature_frame}")
        lines.append("")
        lines.append(f"**AB (synthesis)**")
        lines.append(f"- Hero: `{p.synthesis_ab.hero_headline}`")
        lines.append(f"- Sub: {p.synthesis_ab.sub_hero}")
        lines.append(f"- CTA: `{p.synthesis_ab.primary_cta}`")
        lines.append(f"- Feature frame: {p.synthesis_ab.feature_frame}")
        lines.append("")
        for v in p.judge_votes:
            unmasked = {p.label_map[label]: pts for label, pts in v.scores.items()}
            order = sorted(unmasked.items(), key=lambda kv: -kv[1])
            line = "  ".join(f"{role}={pts}" for role, pts in order)
            lines.append(f"- Judge {v.judge_index}: {line}")
            # Axis breakdown — one line per candidate
            for label, axes in v.axis_scores.items():
                role = p.label_map.get(label, label)
                axis_summary = " ".join(f"{k[:3]}={vv}" for k, vv in axes.items())
                lines.append(f"  - {role} ({label}): {axis_summary}")
        borda_str = "  ".join(f"{r}={s}" for r, s in sorted(p.borda_by_role.items(), key=lambda kv: -kv[1]))
        lines.append(f"- **Borda:** {borda_str} → winner: **{p.winner_role}**")
        lines.append("")

    lines.append("## Final winner")
    lines.append("")
    lines.append("```")
    lines.append(f"Hero headline:  {winner.hero_headline}")
    lines.append(f"Sub-hero:       {winner.sub_hero}")
    lines.append(f"Primary CTA:    {winner.primary_cta}")
    lines.append(f"Feature frame:  {winner.feature_frame}")
    lines.append("```")
    return "\n".join(lines)


def trace_to_json(passes: list[Pass]) -> str:
    return json.dumps([asdict(p) for p in passes], indent=2, default=str)
