"""
Knowledge Cloner — Phase 2b: Knowledge Extraction.

Runs the master extraction prompt against each transcribed source
using Gemini Flash (or Claude Sonnet if overridden).
"""

import time
from pathlib import Path

from .types import ExpertConfig
from .config import PHASE_MODELS
from .utils import (
    CostTracker, RateLimiter, log, read_file, write_file,
    call_llm, confirm_action, estimate_phase_cost,
)
from .prompts import MASTER_EXTRACTION_PROMPT, REPO_EXTRACTION_PROMPT


async def extract_sources(
    config: ExpertConfig,
    expert_dir: Path,
    tracker: CostTracker,
    limiter: RateLimiter,
    limit: int = 0,
    model: str = "",
    dry_run: bool = False,
) -> ExpertConfig:
    """Run knowledge extraction on all transcribed sources."""
    model = model or PHASE_MODELS["extraction"]

    candidates = config.sources_with_status("transcribed")
    if limit:
        candidates = candidates[:limit]

    if not candidates:
        log("No transcribed sources to extract.")
        return config

    # Cost estimate
    est = estimate_phase_cost("extraction", model, len(candidates))
    msg = f"Will extract {len(candidates)} sources via {model}. Est. cost: ${est.estimated_cost:.2f}"

    if dry_run:
        log(f"[DRY RUN] {msg}")
        for s in candidates:
            log(f"  Would extract: {s.title or s.id}")
        return config

    if not confirm_action(msg):
        log("Extraction cancelled.")
        return config

    succeeded = 0
    failed = 0

    for i, source in enumerate(candidates, 1):
        log(f"  [{i}/{len(candidates)}] Extracting: {source.title or source.id}")

        # Read transcript
        transcript_path = expert_dir / source.transcript_path
        if not transcript_path.exists():
            log(f"    Transcript not found: {source.transcript_path}")
            source.error = "Transcript file missing"
            failed += 1
            continue

        transcript = read_file(transcript_path)
        if not transcript.strip():
            log(f"    Empty transcript. Skipping.")
            failed += 1
            continue

        # Build prompt — use repo-specific prompt for repositories
        prompt_template = REPO_EXTRACTION_PROMPT if source.source_type == "repo" else MASTER_EXTRACTION_PROMPT
        prompt = prompt_template.format(
            expert_name=config.name,
            source_type=source.source_type.upper(),
            source_url=source.url,
            source_date=source.date or "Unknown",
            content=transcript,
        )

        try:
            tracker.check_or_abort()
            await limiter.wait()

            text, in_tok, out_tok = await call_llm(prompt, model=model, max_tokens=8192)

            tracker.record(model, in_tok, out_tok)

            if text:
                # Save extraction
                extraction_path = f"extractions/{source.id}_extract.md"
                header = (
                    f"---\n"
                    f"source_id: {source.id}\n"
                    f"expert: {config.name}\n"
                    f"source_type: {source.source_type}\n"
                    f"title: {source.title}\n"
                    f"extracted: {time.strftime('%Y-%m-%d %H:%M')}\n"
                    f"model: {model}\n"
                    f"---\n\n"
                )
                write_file(expert_dir / extraction_path, header + text)

                source.status = "extracted"
                source.extraction_path = extraction_path
                succeeded += 1
                log(f"    Done ({in_tok} in / {out_tok} out tokens)")
            else:
                log(f"    Empty response from LLM")
                source.error = "Empty LLM response"
                failed += 1

        except RuntimeError as e:
            log(f"    Limit reached: {e}")
            break
        except Exception as e:
            log(f"    ERROR: {e}")
            source.error = str(e)[:200]
            failed += 1

    log(f"Extraction: {succeeded} succeeded, {failed} failed. {tracker.summary()}")

    if succeeded > 0 and "extraction" not in config.phases_completed:
        config.phases_completed.append("extraction")

    return config
