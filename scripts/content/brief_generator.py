"""
Brief Generator — Auto-generates 18-field content briefs from (format, site, keyword).

Gathers GSC data, persona pain points, site facts, and skill contract constraints,
then uses a single LLM call to fill creative fields (angle, hooks, competitor weakness).
"""

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from scripts.harness_config import get_config
from scripts.content.persona_resolver import resolve_persona


def _run_cmo(args: list[str]) -> str:
    """Call cmo_wrapper.py for GSC/analytics data."""
    cfg = get_config()
    scripts_dir = cfg.scripts_dir
    try:
        result = subprocess.run(
            ["python3", str(scripts_dir / "cmo_wrapper.py")] + args,
            capture_output=True, text=True, timeout=30,
        )
        return result.stdout.strip()
    except Exception:
        return ""


def _load_persona_text(persona: str) -> str:
    """Load persona markdown for context."""
    cfg = get_config()
    knowledge = cfg.knowledge_dir
    # Try slug form: "Competent Cog" -> "competent-cog"
    slug = persona.lower().replace(" ", "-")
    for candidate in [
        knowledge / "personas" / f"{slug}.md",
        knowledge / "personas" / f"{persona}.md",
    ]:
        if candidate.exists():
            return candidate.read_text()[:1500]
    return ""


def _load_skill_contract(fmt: str, workspace: Path) -> dict:
    """Load the skill contract YAML for a format."""
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
    contract_path = workspace / "harness" / "skill-contracts" / f"{slug}.yaml"
    if contract_path.exists():
        try:
            return yaml.safe_load(contract_path.read_text()) or {}
        except Exception:
            pass
    return {}


def _parse_json_response(raw: str) -> dict:
    """Parse JSON from LLM response with fallback chain."""
    # Direct parse
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        pass

    # Strip markdown fences
    if "```" in raw:
        inner = raw.split("```")[1]
        if inner.startswith("json"):
            inner = inner[4:]
        try:
            return json.loads(inner.strip())
        except json.JSONDecodeError:
            pass

    # Regex extract first JSON object
    m = re.search(r"\{[\s\S]*\}", raw)
    if m:
        try:
            return json.loads(m.group())
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not parse JSON from LLM response: {raw[:200]}")


async def generate_brief(
    format: str,
    site: str,
    keyword: str,
    persona: str | None = None,
    angle: str | None = None,
    secondary_keywords: list[str] | None = None,
    word_count: int | None = None,
    hook_options: list[str] | None = None,
    gemini_fn=None,
) -> dict:
    """Generate a full 18-field content brief from minimal inputs.

    Args:
        format: Content format (blog, meta-ads, etc.)
        site: Site key (kaicalls, buildwithkai, etc.)
        keyword: Target keyword.
        persona: Override persona (optional).
        angle: Override angle (optional).
        secondary_keywords: Override secondary keywords (optional).
        word_count: Override word count (optional).
        hook_options: Override hooks (optional).
        gemini_fn: Callable(prompt) -> str for LLM calls.

    Returns:
        Dict with 18 brief fields + metadata.data_sources.
    """
    cfg = get_config()

    # Step 1: Resolve persona
    resolved_persona = resolve_persona(site, keyword, persona)
    persona_text = _load_persona_text(resolved_persona)

    # Step 2: Gather API data
    gsc_opps = _run_cmo(["gsc", "opportunities", f"--site={site}"])
    gsc_queries = _run_cmo(["gsc", "queries", f"--site={site}", "--limit=20"])

    # Step 3: Lookup data
    contract = _load_skill_contract(format, cfg.workspace_dir)
    wc_range = contract.get("word_count", "1400")
    default_wc = int(str(wc_range).split("-")[0]) if "-" in str(wc_range) else int(wc_range)
    target_wc = word_count or default_wc

    # Load content log for internal links
    internal_links = []
    content_log_path = cfg.content_log
    if content_log_path.exists():
        try:
            log_data = json.loads(content_log_path.read_text())
            site_entries = [e for e in log_data if e.get("site") == site and e.get("url")]
            internal_links = [e["url"] for e in site_entries[-5:]]
        except Exception:
            pass

    # Site facts from config
    config_path = cfg.repo_root / "config.yaml"
    site_facts = ""
    if config_path.exists():
        import yaml
        try:
            raw_cfg = yaml.safe_load(config_path.read_text()) or {}
            for p in raw_cfg.get("products", []):
                if p.get("id") == site and p.get("proof_points"):
                    site_facts = p["proof_points"]
        except Exception:
            pass

    # Step 4: LLM call for creative fields
    data_sources = {
        "persona": "config" if not persona else "override",
        "gsc_data": "api" if gsc_opps or gsc_queries else "none",
        "word_count": "override" if word_count else "contract",
        "internal_links": "content_log" if internal_links else "none",
    }

    if gemini_fn and not (angle and hook_options and secondary_keywords):
        creative_prompt = f"""Generate creative fields for a content brief.

Site: {site}
Keyword: {keyword}
Format: {format}
Persona: {resolved_persona}

GSC opportunities:
{gsc_opps[:3000] or "No GSC data"}

GSC top queries:
{gsc_queries[:2000] or "No GSC data"}

Persona pain points:
{persona_text or "Infer from context"}

Return ONLY valid JSON:
{{
  "angle": "differentiated frame — not just the keyword restated",
  "hook_options": [
    "Hook 1 — specific, counter-intuitive or data-driven",
    "Hook 2 — pain/fear angle",
    "Hook 3 — curiosity gap"
  ],
  "competitor_weakness": "specific gap we can exploit in 20+ words",
  "secondary_keywords": ["kw2", "kw3", "kw4"],
  "audience_pain": "single biggest frustration of this persona with this topic",
  "current_rank": "not ranking OR position N",
  "monthly_impressions": 0,
  "current_ctr": 0.0,
  "competitor_url": "https://...",
  "proof_available": "specific data point or stat we can use"
}}"""
        raw = gemini_fn(creative_prompt)
        creative = _parse_json_response(raw)
        data_sources["creative_fields"] = "llm"
    else:
        creative = {}
        data_sources["creative_fields"] = "override"

    # Step 5: Assemble 18-field brief
    brief = {
        "target_site": site,
        "target_keyword": keyword,
        "secondary_keywords": secondary_keywords or creative.get("secondary_keywords", []),
        "format": format,
        "persona": resolved_persona,
        "current_rank": creative.get("current_rank", "unknown"),
        "monthly_impressions": creative.get("monthly_impressions", 0),
        "current_ctr": creative.get("current_ctr", 0.0),
        "competitor_url": creative.get("competitor_url", ""),
        "competitor_weakness": angle if angle else creative.get("competitor_weakness", ""),
        "angle": angle or creative.get("angle", keyword),
        "hook_options": hook_options or creative.get("hook_options", [keyword]),
        "audience_pain": creative.get("audience_pain", ""),
        "proof_available": site_facts or creative.get("proof_available", ""),
        "cta": creative.get("cta", f"Learn more at {site}"),
        "word_count_target": target_wc,
        "publish_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "internal_links": internal_links,
    }

    # Step 6: Attach metadata
    brief["metadata"] = {"data_sources": data_sources}

    return brief
