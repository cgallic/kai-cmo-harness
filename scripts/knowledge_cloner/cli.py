"""
Knowledge Cloner — CLI interface.

Usage:
    python -m scripts.knowledge_cloner <command> [options]
"""

import argparse
import asyncio
import sys
from pathlib import Path

from .config import BASE_DATA_DIR, PHASE_MODELS, DEFAULT_MAX_REQUESTS, DEFAULT_MAX_COST
from .types import ExpertConfig
from .utils import (
    load_progress, save_progress, generate_source_map, slugify, log,
    CostTracker, RateLimiter,
)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

async def cmd_init(args):
    """Initialize a new expert knowledge extraction project."""
    slug = slugify(args.name)
    expert_dir = BASE_DATA_DIR / slug

    if expert_dir.exists() and (expert_dir / "progress.json").exists():
        existing = load_progress(expert_dir)
        log(f"Expert '{existing.name}' already exists at {expert_dir}")
        return

    # Create directory structure
    for subdir in [
        "raw/transcripts", "raw/articles", "raw/audio", "raw/repos",
        "extractions", "distilled", "synthesis", "output",
    ]:
        (expert_dir / subdir).mkdir(parents=True, exist_ok=True)

    config = ExpertConfig(
        name=args.name,
        slug=slug,
        domain=getattr(args, "domain", ""),
    )
    save_progress(expert_dir, config)
    generate_source_map(expert_dir, config)

    log(f"Initialized expert: {args.name}")
    log(f"  Slug: {slug}")
    log(f"  Domain: {config.domain}")
    log(f"  Directory: {expert_dir}")
    log(f"  Source map: {expert_dir / 'source-map.md'}")


async def cmd_list(args):
    """List all expert extraction projects."""
    if not BASE_DATA_DIR.exists():
        log("No experts found. Run 'init' first.")
        return

    experts = []
    for d in sorted(BASE_DATA_DIR.iterdir()):
        if d.is_dir():
            config = load_progress(d)
            if config:
                experts.append(config)

    if not experts:
        log("No experts found. Run 'init' first.")
        return

    print(f"\n{'Slug':<25} {'Name':<30} {'Domain':<20} {'Sources':<10} {'Phases'}")
    print("-" * 100)
    for e in experts:
        phases = ", ".join(e.phases_completed) if e.phases_completed else "none"
        print(f"{e.slug:<25} {e.name:<30} {e.domain:<20} {len(e.sources):<10} {phases}")
    print()


async def cmd_status(args):
    """Show pipeline status for an expert."""
    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug

    print(f"\n=== {config.name} ===")
    print(f"Domain: {config.domain}")
    print(f"Created: {config.created}")
    print(f"Sources: {len(config.sources)}")

    # Source status breakdown
    statuses = {}
    for s in config.sources:
        statuses[s.status] = statuses.get(s.status, 0) + 1
    if statuses:
        print("\nSource Status:")
        for status, count in sorted(statuses.items()):
            print(f"  {status}: {count}")

    # Phase completion
    print(f"\nPhases completed: {', '.join(config.phases_completed) or 'none'}")

    # Check what files exist
    print("\nOutput files:")
    for subdir in ["distilled", "synthesis", "output"]:
        path = expert_dir / subdir
        if path.exists():
            files = list(path.glob("*.md"))
            if files:
                print(f"  {subdir}/: {len(files)} files")
    print()


async def cmd_sources(args):
    """Show source inventory for an expert."""
    config = _load_expert(args.expert)
    if not config:
        return

    if not config.sources:
        log("No sources yet. Use 'discover' to add sources.")
        return

    print(f"\n=== Sources: {config.name} ({len(config.sources)} total) ===\n")
    print(f"{'#':<4} {'Type':<10} {'Status':<12} {'Priority':<8} {'Title'}")
    print("-" * 80)
    for i, src in enumerate(config.sources, 1):
        title = (src.title or src.url)[:45]
        # Sanitize for Windows console encoding
        title = title.encode("ascii", errors="replace").decode("ascii")
        print(f"{i:<4} {src.source_type:<10} {src.status:<12} {src.priority:<8} {title}")
    print()


async def cmd_discover(args):
    """Discover sources for an expert."""
    from .discovery import discover_youtube, add_source, add_podcast_feed

    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug

    if hasattr(args, "youtube") and args.youtube:
        log(f"Discovering YouTube channel: {args.youtube}")
        config = await discover_youtube(config, args.youtube, limit=getattr(args, "limit", 0))

    if hasattr(args, "podcast_rss") and args.podcast_rss:
        log(f"Discovering podcast feed: {args.podcast_rss}")
        config = await add_podcast_feed(config, args.podcast_rss)

    if hasattr(args, "github_repo") and args.github_repo:
        from .discovery import discover_github_repo
        log(f"Adding GitHub repo: {args.github_repo}")
        config = await discover_github_repo(config, args.github_repo, priority=getattr(args, "priority", "HIGH"))

    if hasattr(args, "url") and args.url:
        source_type = getattr(args, "type", "article")
        log(f"Adding {source_type} source: {args.url}")
        config = add_source(config, args.url, source_type, priority=getattr(args, "priority", "MEDIUM"))

    if hasattr(args, "file") and args.file:
        from .discovery import import_local_file
        source_type = getattr(args, "type", "file")
        log(f"Importing local file: {args.file}")
        config = import_local_file(config, args.file, source_type, expert_dir)

    save_progress(expert_dir, config)
    generate_source_map(expert_dir, config)
    log(f"Sources: {len(config.sources)} total")


async def cmd_transcribe(args):
    """Transcribe sources for an expert."""
    from .transcription import transcribe_sources

    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug
    limit = getattr(args, "limit", 0)
    source_type = getattr(args, "type", None)
    dry_run = getattr(args, "dry_run", False)
    max_requests = getattr(args, "max_requests", DEFAULT_MAX_REQUESTS)
    max_cost = getattr(args, "max_cost", DEFAULT_MAX_COST)

    tracker = CostTracker(max_requests, max_cost)
    limiter = RateLimiter()

    config = await transcribe_sources(
        config, expert_dir, tracker, limiter,
        limit=limit, source_type_filter=source_type, dry_run=dry_run,
    )

    save_progress(expert_dir, config)
    generate_source_map(expert_dir, config)
    log(f"Transcription complete. {tracker.summary()}")


async def cmd_extract(args):
    """Run knowledge extraction on transcribed sources."""
    from .extraction import extract_sources

    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug
    limit = getattr(args, "limit", 0)
    dry_run = getattr(args, "dry_run", False)
    model = getattr(args, "model", None) or PHASE_MODELS["extraction"]
    max_requests = getattr(args, "max_requests", DEFAULT_MAX_REQUESTS)
    max_cost = getattr(args, "max_cost", DEFAULT_MAX_COST)

    tracker = CostTracker(max_requests, max_cost)
    limiter = RateLimiter()

    config = await extract_sources(
        config, expert_dir, tracker, limiter,
        limit=limit, model=model, dry_run=dry_run,
    )

    save_progress(expert_dir, config)
    generate_source_map(expert_dir, config)
    log(f"Extraction complete. {tracker.summary()}")


async def cmd_distill(args):
    """Distill extractions into structured documents."""
    from .distillation import distill_extractions

    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug
    dry_run = getattr(args, "dry_run", False)
    model = getattr(args, "model", None) or PHASE_MODELS["distillation"]
    max_requests = getattr(args, "max_requests", DEFAULT_MAX_REQUESTS)
    max_cost = getattr(args, "max_cost", DEFAULT_MAX_COST)

    tracker = CostTracker(max_requests, max_cost)
    limiter = RateLimiter()

    config = await distill_extractions(
        config, expert_dir, tracker, limiter,
        model=model, dry_run=dry_run,
    )

    save_progress(expert_dir, config)
    log(f"Distillation complete. {tracker.summary()}")


async def cmd_synthesize(args):
    """Run cross-source synthesis (Claude Sonnet)."""
    from .synthesis import run_synthesis

    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug
    dry_run = getattr(args, "dry_run", False)
    model = getattr(args, "model", None) or PHASE_MODELS["synthesis"]
    max_requests = getattr(args, "max_requests", DEFAULT_MAX_REQUESTS)
    max_cost = getattr(args, "max_cost", DEFAULT_MAX_COST)

    tracker = CostTracker(max_requests, max_cost)
    limiter = RateLimiter()

    config = await run_synthesis(
        config, expert_dir, tracker, limiter,
        model=model, dry_run=dry_run,
    )

    save_progress(expert_dir, config)
    log(f"Synthesis complete. {tracker.summary()}")


async def cmd_operationalize(args):
    """Generate operational outputs (templates, checklists, prompts)."""
    from .operationalization import run_operationalization

    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug
    dry_run = getattr(args, "dry_run", False)
    model = getattr(args, "model", None) or PHASE_MODELS["operationalization"]
    max_requests = getattr(args, "max_requests", DEFAULT_MAX_REQUESTS)
    max_cost = getattr(args, "max_cost", DEFAULT_MAX_COST)

    tracker = CostTracker(max_requests, max_cost)
    limiter = RateLimiter()

    config = await run_operationalization(
        config, expert_dir, tracker, limiter,
        model=model, dry_run=dry_run,
    )

    save_progress(expert_dir, config)
    log(f"Operationalization complete. {tracker.summary()}")


async def cmd_quality(args):
    """Run quality gate evaluation."""
    from .quality import run_quality_gates

    config = _load_expert(args.expert)
    if not config:
        return

    expert_dir = BASE_DATA_DIR / config.slug
    dry_run = getattr(args, "dry_run", False)
    model = getattr(args, "model", None) or PHASE_MODELS["quality"]
    max_requests = getattr(args, "max_requests", DEFAULT_MAX_REQUESTS)
    max_cost = getattr(args, "max_cost", DEFAULT_MAX_COST)

    tracker = CostTracker(max_requests, max_cost)
    limiter = RateLimiter()

    config = await run_quality_gates(
        config, expert_dir, tracker, limiter,
        model=model, dry_run=dry_run,
    )

    save_progress(expert_dir, config)
    log(f"Quality gates complete. {tracker.summary()}")


async def cmd_cost(args):
    """Show estimated remaining costs for an expert."""
    from .utils import estimate_phase_cost

    config = _load_expert(args.expert)
    if not config:
        return

    print(f"\n=== Cost Estimate: {config.name} ===\n")

    total = 0.0

    # Transcription (mostly free)
    queued = len(config.sources_with_status("queued")) + len(config.sources_with_status("discovered"))
    if queued:
        # Assume 20% need Gemini fallback
        fallback_count = max(1, queued // 5)
        est = estimate_phase_cost("extraction", "gemini-flash", fallback_count)
        est.phase = "transcription (Gemini fallback)"
        print(f"  {est}")
        total += est.estimated_cost

    # Extraction
    transcribed = len(config.sources_with_status("transcribed"))
    if transcribed:
        est = estimate_phase_cost("extraction", PHASE_MODELS["extraction"], transcribed)
        print(f"  {est}")
        total += est.estimated_cost

    # Distillation
    if "distillation" not in config.phases_completed:
        est = estimate_phase_cost("distillation", PHASE_MODELS["distillation"], 5)
        print(f"  {est}")
        total += est.estimated_cost

    # Synthesis
    if "synthesis" not in config.phases_completed:
        est = estimate_phase_cost("synthesis", PHASE_MODELS["synthesis"], 4)
        print(f"  {est}")
        total += est.estimated_cost

    # Operationalization
    if "operationalization" not in config.phases_completed:
        est = estimate_phase_cost("operationalization", PHASE_MODELS["operationalization"], 4)
        print(f"  {est}")
        total += est.estimated_cost

    # Quality
    if "quality" not in config.phases_completed:
        est = estimate_phase_cost("quality", PHASE_MODELS["quality"], 1)
        print(f"  {est}")
        total += est.estimated_cost

    print(f"\n  TOTAL ESTIMATED: ${total:.2f}")
    print()


async def cmd_pipeline(args):
    """Run full pipeline with confirmation prompts between phases."""
    config = _load_expert(args.expert)
    if not config:
        return

    phases = [
        ("transcribe", cmd_transcribe),
        ("extract", cmd_extract),
        ("distill", cmd_distill),
        ("synthesize", cmd_synthesize),
        ("operationalize", cmd_operationalize),
        ("quality", cmd_quality),
    ]

    for phase_name, phase_fn in phases:
        log(f"\n--- Phase: {phase_name} ---")

        # Reload config between phases
        config = _load_expert(args.expert)
        if phase_name in (config.phases_completed if config else []):
            log(f"  Already completed. Skipping.")
            continue

        await phase_fn(args)
        log(f"  Phase '{phase_name}' done.")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_expert(slug: str):
    expert_dir = BASE_DATA_DIR / slug
    config = load_progress(expert_dir)
    if not config:
        log(f"Expert '{slug}' not found. Run 'init' first.")
        log(f"  Looked in: {expert_dir}")
        return None
    return config


def _add_global_flags(parser):
    """Add flags common to all API-calling commands."""
    parser.add_argument("--dry-run", action="store_true", help="Show what would happen without making API calls")
    parser.add_argument("--max-requests", type=int, default=DEFAULT_MAX_REQUESTS, help=f"Max API requests (default: {DEFAULT_MAX_REQUESTS})")
    parser.add_argument("--max-cost", type=float, default=DEFAULT_MAX_COST, help=f"Max estimated spend (default: ${DEFAULT_MAX_COST:.2f})")
    parser.add_argument("--model", choices=["qwen-plus", "qwen-max", "qwen-coder", "gemini-flash", "claude-sonnet"], help="Override model for this phase")


# ---------------------------------------------------------------------------
# Argparse setup
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="knowledge-cloner",
        description="Automated expert knowledge extraction pipeline",
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # init
    p = subparsers.add_parser("init", help="Initialize new expert project")
    p.add_argument("name", help="Expert's full name")
    p.add_argument("--domain", default="", help="Expert's domain (e.g., consulting, marketing)")

    # list
    subparsers.add_parser("list", help="List all expert projects")

    # status
    p = subparsers.add_parser("status", help="Show pipeline status")
    p.add_argument("expert", help="Expert slug")

    # sources
    p = subparsers.add_parser("sources", help="Show source inventory")
    p.add_argument("expert", help="Expert slug")

    # discover
    p = subparsers.add_parser("discover", help="Discover and add sources")
    p.add_argument("expert", help="Expert slug")
    p.add_argument("--youtube", help="YouTube channel URL")
    p.add_argument("--podcast-rss", help="Podcast RSS feed URL")
    p.add_argument("--github-repo", help="GitHub repo URL or owner/repo (e.g., TIGER-AI-Lab/TheoremExplainAgent)")
    p.add_argument("--url", help="Direct URL to add as source")
    p.add_argument("--file", help="Local file path to import")
    p.add_argument("--type", default="article", help="Source type (youtube/podcast/article/xspace/book/course/thread/file/repo)")
    p.add_argument("--priority", default="MEDIUM", choices=["HIGH", "MEDIUM", "LOW"], help="Source priority")
    p.add_argument("--limit", type=int, default=0, help="Max videos to discover from channel")

    # transcribe
    p = subparsers.add_parser("transcribe", help="Transcribe sources")
    p.add_argument("expert", help="Expert slug")
    p.add_argument("--limit", type=int, default=0, help="Max sources to transcribe")
    p.add_argument("--type", help="Only transcribe this source type")
    _add_global_flags(p)

    # extract
    p = subparsers.add_parser("extract", help="Extract knowledge from transcripts")
    p.add_argument("expert", help="Expert slug")
    p.add_argument("--limit", type=int, default=0, help="Max sources to extract")
    _add_global_flags(p)

    # distill
    p = subparsers.add_parser("distill", help="Distill extractions into structured docs")
    p.add_argument("expert", help="Expert slug")
    _add_global_flags(p)

    # synthesize
    p = subparsers.add_parser("synthesize", help="Cross-source synthesis (Claude Sonnet)")
    p.add_argument("expert", help="Expert slug")
    _add_global_flags(p)

    # operationalize
    p = subparsers.add_parser("operationalize", help="Generate templates, checklists, prompts")
    p.add_argument("expert", help="Expert slug")
    _add_global_flags(p)

    # quality
    p = subparsers.add_parser("quality", help="Run quality gate evaluation")
    p.add_argument("expert", help="Expert slug")
    _add_global_flags(p)

    # cost
    p = subparsers.add_parser("cost", help="Show estimated remaining costs")
    p.add_argument("expert", help="Expert slug")

    # pipeline
    p = subparsers.add_parser("pipeline", help="Run full pipeline with confirmations")
    p.add_argument("expert", help="Expert slug")
    _add_global_flags(p)

    return parser


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = build_parser()
    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    commands = {
        "init": cmd_init,
        "list": cmd_list,
        "status": cmd_status,
        "sources": cmd_sources,
        "discover": cmd_discover,
        "transcribe": cmd_transcribe,
        "extract": cmd_extract,
        "distill": cmd_distill,
        "synthesize": cmd_synthesize,
        "operationalize": cmd_operationalize,
        "quality": cmd_quality,
        "cost": cmd_cost,
        "pipeline": cmd_pipeline,
    }

    if args.command in commands:
        asyncio.run(commands[args.command](args))
    else:
        parser.print_help()
        sys.exit(1)
