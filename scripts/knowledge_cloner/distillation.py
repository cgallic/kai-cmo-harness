"""
Knowledge Cloner — Phase 3: Distillation.

Concatenates all extraction files and runs 5 separate LLM calls
(one per category) to produce clean, structured documents.
"""

import time
from pathlib import Path

from .types import ExpertConfig
from .config import PHASE_MODELS
from .utils import (
    CostTracker, RateLimiter, log, read_file, write_file,
    call_llm, confirm_action, estimate_phase_cost,
)
from .prompts import (
    DISTILL_FRAMEWORKS_PROMPT,
    DISTILL_TACTICS_PROMPT,
    DISTILL_EDGES_PROMPT,
    DISTILL_PRINCIPLES_PROMPT,
    DISTILL_ANTIPATTERNS_PROMPT,
)


DISTILL_CATEGORIES = [
    ("frameworks", DISTILL_FRAMEWORKS_PROMPT),
    ("tactics", DISTILL_TACTICS_PROMPT),
    ("edges", DISTILL_EDGES_PROMPT),
    ("principles", DISTILL_PRINCIPLES_PROMPT),
    ("anti-patterns", DISTILL_ANTIPATTERNS_PROMPT),
]


async def distill_extractions(
    config: ExpertConfig,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
    model: str = "",
    dry_run: bool = False,
) -> ExpertConfig:
    """Distill all extraction files into 5 structured documents."""
    model = model or PHASE_MODELS["distillation"]

    # Gather all extraction files
    extractions_dir = expert_dir / "extractions"
    if not extractions_dir.exists():
        log("No extractions directory found. Run 'extract' first.")
        return config

    extraction_files = sorted(extractions_dir.glob("*_extract.md"))
    if not extraction_files:
        log("No extraction files found. Run 'extract' first.")
        return config

    # Concatenate all extractions
    all_content = []
    for ef in extraction_files:
        content = read_file(ef)
        if content:
            all_content.append(f"--- SOURCE: {ef.stem} ---\n{content}\n")

    combined = "\n".join(all_content)
    log(f"Distilling {len(extraction_files)} extractions ({len(combined)} chars)")

    est = estimate_phase_cost("distillation", model, len(DISTILL_CATEGORIES))
    msg = f"Will run {len(DISTILL_CATEGORIES)} distillation passes via {model}. Est. cost: ${est.estimated_cost:.2f}"

    if dry_run:
        log(f"[DRY RUN] {msg}")
        for cat, _ in DISTILL_CATEGORIES:
            log(f"  Would distill: {config.slug}-{cat}.md")
        return config

    if not confirm_action(msg):
        log("Distillation cancelled.")
        return config

    distilled_dir = expert_dir / "distilled"
    distilled_dir.mkdir(parents=True, exist_ok=True)

    for category, prompt_template in DISTILL_CATEGORIES:
        log(f"  Distilling: {category}...")

        prompt = prompt_template.format(
            expert_name=config.name,
            content=combined,
        )

        try:
            tracker.check_or_abort()
            await limiter.wait()

            text, in_tok, out_tok = await call_llm(prompt, model=model, max_tokens=8192)

            tracker.record(model, in_tok, out_tok)

            if text:
                output_path = distilled_dir / f"{config.slug}-{category}.md"
                header = (
                    f"---\n"
                    f"expert: {config.name}\n"
                    f"category: {category}\n"
                    f"sources: {len(extraction_files)}\n"
                    f"distilled: {time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"model: {model}\n"
                    f"---\n\n"
                )
                write_file(output_path, header + text)
                log(f"    Saved {output_path.name} ({in_tok} in / {out_tok} out)")
            else:
                log(f"    Empty response for {category}")

        except RuntimeError as e:
            log(f"    Limit reached: {e}")
            break
        except Exception as e:
            log(f"    ERROR: {e}")

    if "distillation" not in config.phases_completed:
        config.phases_completed.append("distillation")

    return config
