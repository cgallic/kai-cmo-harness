"""
Knowledge Cloner — Phase 5: Operationalization.

Generates templates, decision trees, checklists, and AI prompts
from distilled knowledge using Gemini Flash.
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
    OPERATIONALIZE_QUICK_REFERENCE_PROMPT,
    OPERATIONALIZE_DECISION_TREES_PROMPT,
    OPERATIONALIZE_CHECKLISTS_PROMPT,
    OPERATIONALIZE_AI_PROMPTS_PROMPT,
)


OPERATIONAL_OUTPUTS = [
    ("quick-reference", OPERATIONALIZE_QUICK_REFERENCE_PROMPT),
    ("decision-trees", OPERATIONALIZE_DECISION_TREES_PROMPT),
    ("checklists", OPERATIONALIZE_CHECKLISTS_PROMPT),
    ("ai-prompts", OPERATIONALIZE_AI_PROMPTS_PROMPT),
]


async def run_operationalization(
    config: ExpertConfig,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
    model: str = "",
    dry_run: bool = False,
) -> ExpertConfig:
    """Generate operational outputs from distilled knowledge."""
    model = model or PHASE_MODELS["operationalization"]

    # Gather distilled docs
    distilled_dir = expert_dir / "distilled"
    if not distilled_dir.exists():
        log("No distilled directory found. Run 'distill' first.")
        return config

    distilled_files = sorted(distilled_dir.glob("*.md"))
    if not distilled_files:
        log("No distilled files found. Run 'distill' first.")
        return config

    all_distilled = []
    for df in distilled_files:
        content = read_file(df)
        if content:
            all_distilled.append(f"--- {df.stem} ---\n{content}\n")
    combined = "\n".join(all_distilled)

    est = estimate_phase_cost("operationalization", model, len(OPERATIONAL_OUTPUTS))
    msg = f"Will generate {len(OPERATIONAL_OUTPUTS)} operational docs via {model}. Est. cost: ${est.estimated_cost:.2f}"

    if dry_run:
        log(f"[DRY RUN] {msg}")
        for name, _ in OPERATIONAL_OUTPUTS:
            log(f"  Would produce: {name}.md")
        return config

    if not confirm_action(msg):
        log("Operationalization cancelled.")
        return config

    output_dir = expert_dir / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    for output_name, prompt_template in OPERATIONAL_OUTPUTS:
        log(f"  Generating: {output_name}...")

        prompt = prompt_template.format(
            expert_name=config.name,
            domain=config.domain,
            content=combined,
        )

        try:
            tracker.check_or_abort()
            await limiter.wait()

            text, in_tok, out_tok = await call_llm(prompt, model=model, max_tokens=8192)

            tracker.record(model, in_tok, out_tok)

            if text:
                output_path = output_dir / f"{output_name}.md"
                header = (
                    f"---\n"
                    f"expert: {config.name}\n"
                    f"output: {output_name}\n"
                    f"generated: {time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"model: {model}\n"
                    f"---\n\n"
                )
                write_file(output_path, header + text)
                log(f"    Saved {output_path.name} ({in_tok} in / {out_tok} out)")
            else:
                log(f"    Empty response for {output_name}")

        except RuntimeError as e:
            log(f"    Limit reached: {e}")
            break
        except Exception as e:
            log(f"    ERROR: {e}")

    if "operationalization" not in config.phases_completed:
        config.phases_completed.append("operationalization")

    return config
