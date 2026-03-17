"""
Outcome Engine — Collapses 28 content decisions to 3 inputs: format, site, keyword.

This is the core orchestrator. It chains:
  persona_resolver -> brief_generator -> _writer -> quality gate -> approval_policy -> content_log

Usage:
  result = await generate("blog", "kaicalls", "AI receptionists")
  # result.status in {"approved", "held", "failed", "draft", "error"}
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path

from scripts.harness_config import get_config
from scripts.content.persona_resolver import resolve_persona
from scripts.content.approval_policy import resolve_policy, apply_approval
from scripts.content import brief_generator
from scripts.content._writer import (
    FORMAT_INSTRUCTIONS,
    FORMAT_TO_POLICY,
    SHORT_FORM,
    assemble_write_prompt,
    write_content,
    assemble_revision_prompt,
    revise_content,
)

log = logging.getLogger("outcome-engine")

# ── Framework map — which knowledge files to load per format ─────────────
FRAMEWORK_MAP = {
    "blog":            ["knowledge/frameworks/content-copywriting/algorithmic-authorship.md"],
    "linkedin":        ["knowledge/channels/linkedin-articles.md"],
    "email-lifecycle": ["knowledge/channels/email-lifecycle.md"],
    "cold-email":      ["knowledge/channels/email-lifecycle.md",
                        "harness/references/cold-email-rules.md"],
    "tiktok":          ["knowledge/channels/tiktok-algorithm.md"],
    "meta-ads":        ["knowledge/channels/meta-advertising.md"],
    "google-ads":      ["knowledge/channels/paid-acquisition.md",
                        "harness/references/google-ads-rules.md"],
    "press":           ["knowledge/channels/press-releases.md"],
    "seo":             ["knowledge/frameworks/content-copywriting/algorithmic-authorship.md",
                        "knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md"],
}

VALID_FORMATS = set(FRAMEWORK_MAP.keys())


@dataclass
class GenerateResult:
    """Result of a content generation run."""
    content: str
    brief: dict
    gate_report: dict | None
    status: str  # "approved" | "held" | "failed" | "draft" | "error"
    proposal_id: str
    metadata: dict = field(default_factory=dict)


def _make_gemini_fn():
    """Create a Gemini callable. No module-level Gemini import."""
    cfg = get_config()

    def call(prompt: str) -> str:
        from google import genai as google_genai
        client = google_genai.Client(
            api_key=cfg.gemini_api_key,
            http_options={"timeout": cfg.api_timeout * 1000},
        )
        response = client.models.generate_content(
            model=cfg.gemini_model, contents=prompt
        )
        return response.text.strip()

    return call


def _load_framework_texts(fmt: str, repo_root: Path, workspace: Path) -> str:
    """Load and concatenate framework files for a format."""
    rel_paths = FRAMEWORK_MAP.get(fmt, [])
    texts = []
    for rel in rel_paths:
        # Try workspace first (deployed), then repo root (dev)
        for base in [workspace, repo_root]:
            candidate = base / rel
            if candidate.exists():
                texts.append(candidate.read_text()[:1500])
                break
    return "\n\n---\n\n".join(texts)


def _load_patterns(repo_root: Path, workspace: Path) -> str:
    """Load winning patterns from what-works.md."""
    for base in [workspace, repo_root]:
        ww = base / "knowledge" / "playbooks" / "what-works.md"
        if ww.exists():
            return ww.read_text()[-2000:]
    return ""


def _load_skill_contract(fmt: str, workspace: Path) -> dict:
    """Load skill contract YAML for a format."""
    import yaml

    slug = {
        "blog": "blog-post",
        "seo": "blog-post",
        "linkedin": "linkedin-article",
        "email-lifecycle": "email-lifecycle",
        "cold-email": "cold-email",
        "meta-ads": "meta-ads",
        "google-ads": "google-ads",
    }.get(fmt, fmt)
    path = workspace / "harness" / "skill-contracts" / f"{slug}.yaml"
    if path.exists():
        try:
            return yaml.safe_load(path.read_text()) or {}
        except Exception:
            pass
    return {}


def _load_site_facts(site: str, repo_root: Path) -> str:
    """Load site proof points from config.yaml."""
    import yaml

    config_path = repo_root / "config.yaml"
    if config_path.exists():
        try:
            cfg = yaml.safe_load(config_path.read_text()) or {}
            for p in cfg.get("products", []):
                if p.get("id") == site and p.get("proof_points"):
                    return p["proof_points"]
        except Exception:
            pass
    return ""


def _load_marketing_md(workspace: Path) -> tuple[str, str]:
    """Load non-negotiables and learned defaults from MARKETING.md.

    Returns (non_negotiables, learned_defaults).
    """
    import re

    mmd_path = workspace / "MARKETING.md"
    if not mmd_path.exists():
        return "", ""
    text = mmd_path.read_text()

    non_neg = ""
    m = re.search(r"## Non-Negotiables.*?\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if m:
        non_neg = m.group(1).strip()

    learned = ""
    m = re.search(r"## Learned Defaults.*?\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
    if m:
        learned = m.group(1).strip()

    return non_neg, learned


async def generate(
    format: str,
    site: str,
    keyword: str,
    *,
    persona: str | None = None,
    angle: str | None = None,
    secondary_keywords: list[str] | None = None,
    word_count: int | None = None,
    hook_options: list[str] | None = None,
    dry_run: bool = False,
    skip_gates: bool = False,
) -> GenerateResult:
    """Generate content from 3 inputs: format, site, keyword.

    This is the main entry point for the Outcome Engine.

    Args:
        format: Content format (blog, linkedin, meta-ads, etc.)
        site: Site key (kaicalls, buildwithkai, etc.)
        keyword: Target keyword.
        persona: Override persona selection.
        angle: Override angle/thesis.
        secondary_keywords: Override secondary keywords.
        word_count: Override word count target.
        hook_options: Override hook options.
        dry_run: If True, generate brief only (no content/gates).
        skip_gates: If True, skip quality gates.

    Returns:
        GenerateResult with content, brief, gate report, and status.
    """
    proposal_id = str(uuid.uuid4())[:8]
    cfg = get_config()

    # 1. Validate inputs
    if format not in VALID_FORMATS:
        return GenerateResult(
            content="", brief={}, gate_report=None,
            status="error", proposal_id=proposal_id,
            metadata={"error": f"Invalid format '{format}'. Valid: {sorted(VALID_FORMATS)}"},
        )

    valid_sites = list(cfg.site_persona_defaults.keys())
    if site not in valid_sites:
        return GenerateResult(
            content="", brief={}, gate_report=None,
            status="error", proposal_id=proposal_id,
            metadata={"error": f"Invalid site '{site}'. Valid: {valid_sites}"},
        )

    # 2. Create Gemini callable
    gemini_fn = _make_gemini_fn()

    # 3. Load all context
    repo_root = cfg.repo_root
    workspace = cfg.workspace_dir
    framework_texts = _load_framework_texts(format, repo_root, workspace)
    patterns = _load_patterns(repo_root, workspace)
    contract = _load_skill_contract(format, workspace)
    site_facts = _load_site_facts(site, repo_root)
    non_negotiables, learned_defaults = _load_marketing_md(workspace)

    # 4. Generate brief
    log.info("Generating brief: %s / %s / %s", format, site, keyword)
    brief = await brief_generator.generate_brief(
        format=format,
        site=site,
        keyword=keyword,
        persona=persona,
        angle=angle,
        secondary_keywords=secondary_keywords,
        word_count=word_count,
        hook_options=hook_options,
        gemini_fn=gemini_fn,
    )

    # 5. Dry run exit
    if dry_run:
        return GenerateResult(
            content="", brief=brief, gate_report=None,
            status="draft", proposal_id=proposal_id,
            metadata={"dry_run": True},
        )

    # 6. Assemble prompt and generate content
    log.info("Writing content for: %s", keyword)
    prompt = assemble_write_prompt(
        brief=brief,
        framework_texts=framework_texts,
        patterns=patterns,
        contract=contract,
        site_facts=site_facts,
        learned_defaults=learned_defaults,
        non_negotiables=non_negotiables,
    )
    draft = write_content(prompt, gemini_fn)

    # 7. Skip gates if requested
    if skip_gates:
        return GenerateResult(
            content=draft, brief=brief, gate_report=None,
            status="draft", proposal_id=proposal_id,
            metadata={"gates_skipped": True},
        )

    # 8. Run quality gate with retry loop
    policy_name = FORMAT_TO_POLICY.get(format, "default")
    gate_report = None
    max_retries = 2

    for attempt in range(1, max_retries + 2):
        log.info("Gate attempt %d/%d for: %s", attempt, max_retries + 1, keyword)

        from scripts.quality import gate as quality_gate
        proposal = await quality_gate.propose(
            content=draft,
            file_path="<engine-draft>",
            policy_name=policy_name,
        )

        gate_report = {
            "proposal_id": proposal.get("proposal_id", proposal_id),
            "score": proposal.get("score"),
            "grade": proposal.get("grade"),
            "status": proposal.get("status"),
            "violations": proposal.get("top_fixes", []),
            "violation_count": proposal.get("violation_count", 0),
            "policy": policy_name,
            "attempt": attempt,
        }
        proposal_id = gate_report["proposal_id"]

        gate_status = proposal.get("status", "rejected")

        if gate_status in ("approved", "pending"):
            break
        elif attempt <= max_retries:
            # Revise and retry
            log.info("Gate rejected (score %s). Revising...", proposal.get("score"))
            rev_prompt = assemble_revision_prompt(draft, gate_report, keyword)
            if rev_prompt != draft:
                draft = revise_content(rev_prompt, gemini_fn)
        # else: final attempt failed, fall through

    # 9. Apply approval policy
    gate_status = gate_report.get("status", "rejected") if gate_report else "rejected"
    policy = resolve_policy(format, site)
    final_status = apply_approval(gate_status, policy)

    # 10. Log if approved
    if final_status == "approved":
        try:
            from scripts.content.content_log import log_entry
            log_entry(
                url=f"https://{site}.com/{keyword.replace(' ', '-').lower()}",
                keyword=keyword,
                site=site,
                format=format,
                title=brief.get("angle", keyword),
                brief=brief,
                four_us=gate_report.get("score", 0) if gate_report else 0,
            )
        except Exception as e:
            log.warning("Failed to log content entry: %s", e)

    return GenerateResult(
        content=draft,
        brief=brief,
        gate_report=gate_report,
        status=final_status,
        proposal_id=proposal_id,
        metadata={
            "format": format,
            "site": site,
            "keyword": keyword,
            "persona": brief.get("persona"),
            "approval_policy": policy,
            "word_count": len(draft.split()),
        },
    )
