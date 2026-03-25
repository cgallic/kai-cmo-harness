"""
Knowledge Cloner — Phase 6: Quality Gates.

Evaluates the extraction against 5 quality checklists using Claude Sonnet.
"""

import time
from pathlib import Path

from .types import ExpertConfig
from .config import PHASE_MODELS
from .utils import (
    CostTracker, RateLimiter, log, read_file, write_file,
    call_llm, confirm_action, estimate_phase_cost,
)
from .prompts import QUALITY_GATE_PROMPT


async def run_quality_gates(
    config: ExpertConfig,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
    model: str = "",
    dry_run: bool = False,
) -> ExpertConfig:
    """Run quality gate evaluation on the full extraction."""
    model = model or PHASE_MODELS["quality"]

    # Gather all outputs
    source_map = read_file(expert_dir / "source-map.md")
    if not source_map:
        log("No source-map.md found.")
        return config

    # Distilled docs
    distilled = _gather_dir(expert_dir / "distilled")
    if not distilled:
        log("No distilled docs found. Run 'distill' first.")
        return config

    # Synthesis docs
    synthesis = _gather_dir(expert_dir / "synthesis")

    # Operational docs
    operational = _gather_dir(expert_dir / "output")

    est = estimate_phase_cost("quality", model, 1)
    msg = f"Will run quality evaluation via {model}. Est. cost: ${est.estimated_cost:.2f}"

    if dry_run:
        log(f"[DRY RUN] {msg}")
        log(f"  Would evaluate: source-map, {_count_files(expert_dir)} total files")
        return config

    if not confirm_action(msg):
        log("Quality check cancelled.")
        return config

    log("  Running quality gate evaluation...")

    prompt = QUALITY_GATE_PROMPT.format(
        expert_name=config.name,
        source_map=source_map,
        distilled=distilled,
        synthesis=synthesis or "(Synthesis not yet completed)",
        operational=operational or "(Operationalization not yet completed)",
    )

    try:
        tracker.check_or_abort()
        await limiter.wait()

        text, in_tok, out_tok = await call_llm(prompt, model=model, max_tokens=8192)

        tracker.record(model, in_tok, out_tok)

        if text:
            output_path = expert_dir / "output" / "quality-report.md"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            header = (
                f"---\n"
                f"expert: {config.name}\n"
                f"evaluated: {time.strftime('%Y-%m-%d %H:%M')}\n"
                f"model: {model}\n"
                f"---\n\n"
            )
            write_file(output_path, header + text)
            log(f"    Saved quality-report.md ({in_tok} in / {out_tok} out)")

            # Also print a summary
            print(f"\n{'='*60}")
            # Extract just the overall score line
            for line in text.split("\n"):
                if "Overall Score" in line or "Gate" in line and ("PASS" in line or "FAIL" in line):
                    print(f"  {line.strip()}")
            print(f"{'='*60}\n")
        else:
            log("    Empty response from quality evaluation")

    except Exception as e:
        log(f"    ERROR: {e}")

    if "quality" not in config.phases_completed:
        config.phases_completed.append("quality")

    return config


def _gather_dir(dir_path: Path) -> str:
    """Gather all markdown files from a directory into a single string."""
    if not dir_path.exists():
        return ""

    parts = []
    for md_file in sorted(dir_path.glob("*.md")):
        content = read_file(md_file)
        if content:
            parts.append(f"--- {md_file.name} ---\n{content}\n")

    return "\n".join(parts)


def _count_files(expert_dir: Path) -> int:
    """Count total output files."""
    count = 0
    for subdir in ["distilled", "synthesis", "output"]:
        path = expert_dir / subdir
        if path.exists():
            count += len(list(path.glob("*.md")))
    return count
