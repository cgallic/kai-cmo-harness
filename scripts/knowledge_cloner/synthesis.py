"""
Knowledge Cloner — Phase 4: Synthesis.

Cross-source analysis using Claude Sonnet (quality matters here).
Produces: novelty pass, hidden curriculum, gap analysis, real thesis.
"""

import time
from pathlib import Path

from .types import ExpertConfig
from .config import PHASE_MODELS, BASE_DATA_DIR
from .utils import (
    CostTracker, RateLimiter, log, read_file, write_file,
    call_llm, confirm_action, estimate_phase_cost,
)
from .prompts import (
    SYNTHESIS_NOVELTY_PROMPT,
    SYNTHESIS_HIDDEN_CURRICULUM_PROMPT,
    SYNTHESIS_GAP_ANALYSIS_PROMPT,
    SYNTHESIS_REAL_THESIS_PROMPT,
)


SYNTHESIS_PASSES = [
    ("novelty-pass", SYNTHESIS_NOVELTY_PROMPT, True),    # needs existing_kb
    ("hidden-curriculum", SYNTHESIS_HIDDEN_CURRICULUM_PROMPT, False),
    ("gap-analysis", SYNTHESIS_GAP_ANALYSIS_PROMPT, False),
    ("real-thesis", SYNTHESIS_REAL_THESIS_PROMPT, False),
]


async def run_synthesis(
    config: ExpertConfig,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
    model: str = "",
    dry_run: bool = False,
) -> ExpertConfig:
    """Run cross-source synthesis passes."""
    model = model or PHASE_MODELS["synthesis"]

    # Gather distilled docs
    distilled_dir = expert_dir / "distilled"
    if not distilled_dir.exists():
        log("No distilled directory found. Run 'distill' first.")
        return config

    distilled_files = sorted(distilled_dir.glob("*.md"))
    if not distilled_files:
        log("No distilled files found. Run 'distill' first.")
        return config

    # Combine distilled content
    all_distilled = []
    for df in distilled_files:
        content = read_file(df)
        if content:
            all_distilled.append(f"--- {df.stem} ---\n{content}\n")
    combined = "\n".join(all_distilled)

    # Try to load existing KB for novelty comparison
    existing_kb = _load_existing_kb()

    est = estimate_phase_cost("synthesis", model, len(SYNTHESIS_PASSES))
    msg = f"Will run {len(SYNTHESIS_PASSES)} synthesis passes via {model}. Est. cost: ${est.estimated_cost:.2f}"

    if dry_run:
        log(f"[DRY RUN] {msg}")
        for name, _, _ in SYNTHESIS_PASSES:
            log(f"  Would produce: {name}.md")
        return config

    if not confirm_action(msg):
        log("Synthesis cancelled.")
        return config

    synthesis_dir = expert_dir / "synthesis"
    synthesis_dir.mkdir(parents=True, exist_ok=True)

    for pass_name, prompt_template, needs_kb in SYNTHESIS_PASSES:
        log(f"  Synthesis: {pass_name}...")

        kwargs = {
            "expert_name": config.name,
            "content": combined,
            "domain": config.domain,
        }
        if needs_kb:
            kwargs["existing_kb"] = existing_kb or "(No existing KB loaded)"

        prompt = prompt_template.format(**kwargs)

        try:
            tracker.check_or_abort()
            await limiter.wait()

            text, in_tok, out_tok = await call_llm(prompt, model=model, max_tokens=8192)

            tracker.record(model, in_tok, out_tok)

            if text:
                output_path = synthesis_dir / f"{pass_name}.md"
                header = (
                    f"---\n"
                    f"expert: {config.name}\n"
                    f"pass: {pass_name}\n"
                    f"synthesized: {time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"model: {model}\n"
                    f"---\n\n"
                )
                write_file(output_path, header + text)
                log(f"    Saved {output_path.name} ({in_tok} in / {out_tok} out)")
            else:
                log(f"    Empty response for {pass_name}")

        except RuntimeError as e:
            log(f"    Limit reached: {e}")
            break
        except Exception as e:
            log(f"    ERROR: {e}")

    if "synthesis" not in config.phases_completed:
        config.phases_completed.append("synthesis")

    return config


def _load_existing_kb() -> str:
    """Try to load existing KB frameworks for novelty comparison."""
    kb_root = BASE_DATA_DIR.parent.parent  # CMO_Agent_System root
    frameworks_dir = kb_root / "frameworks"

    if not frameworks_dir.exists():
        return ""

    snippets = []
    for md_file in sorted(frameworks_dir.rglob("*.md"))[:20]:  # Cap at 20 files
        content = read_file(md_file)
        if content:
            # Take just the first 500 chars as a summary
            snippets.append(f"### {md_file.relative_to(kb_root)}\n{content[:500]}...\n")

    return "\n".join(snippets) if snippets else ""
