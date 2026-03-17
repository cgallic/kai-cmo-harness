"""
Intent Parser — NLP convenience layer for natural-language content requests.

Parses freeform text like "write a blog about AI receptionists for kai calls"
into structured (format, site, keyword) using Gemini Flash.

All surfaces work without this — it's purely optional syntactic sugar.
"""

import json
import re
from dataclasses import dataclass, field

from scripts.content.engine import VALID_FORMATS
from scripts.harness_config import get_config


@dataclass
class ParsedIntent:
    """Result of intent parsing."""
    format: str | None = None
    site: str | None = None
    keyword: str | None = None
    confidence: float = 0.0
    missing: list[str] = field(default_factory=list)
    overrides: dict = field(default_factory=dict)


async def parse_intent(text: str, gemini_fn=None) -> ParsedIntent:
    """Parse a natural-language content request into structured fields.

    Args:
        text: Freeform request (e.g. "write a blog about AI receptionists for kai calls")
        gemini_fn: Callable(prompt) -> str. If None, creates one.

    Returns:
        ParsedIntent with extracted fields and confidence score.
    """
    cfg = get_config()
    valid_sites = list(cfg.site_persona_defaults.keys())

    if gemini_fn is None:
        from scripts.content.engine import _make_gemini_fn
        gemini_fn = _make_gemini_fn()

    prompt = f"""Extract structured content request fields from this natural language input.

Valid formats: {sorted(VALID_FORMATS)}
Valid sites: {valid_sites}

Input: "{text}"

Return ONLY valid JSON:
{{
  "format": "blog|linkedin|meta-ads|etc or null if unclear",
  "site": "site_key or null if unclear",
  "keyword": "the target keyword/topic or null if unclear",
  "confidence": 0.0 to 1.0,
  "overrides": {{}}
}}

Rules:
- "kai calls" or "kaicalls" maps to site "kaicalls"
- "build with kai" maps to "buildwithkai"
- If format is not mentioned, infer from context (default to "blog")
- keyword is the topic/subject, not the format or site name
- Set confidence based on how clear the request is"""

    raw = gemini_fn(prompt)

    # Parse response
    try:
        if "```" in raw:
            inner = raw.split("```")[1]
            if inner.startswith("json"):
                inner = inner[4:]
            data = json.loads(inner.strip())
        else:
            data = json.loads(raw.strip())
    except (json.JSONDecodeError, IndexError):
        m = re.search(r"\{[\s\S]*\}", raw)
        if m:
            try:
                data = json.loads(m.group())
            except json.JSONDecodeError:
                return ParsedIntent(missing=["format", "site", "keyword"])
        else:
            return ParsedIntent(missing=["format", "site", "keyword"])

    result = ParsedIntent(
        format=data.get("format"),
        site=data.get("site"),
        keyword=data.get("keyword"),
        confidence=float(data.get("confidence", 0.0)),
        overrides=data.get("overrides", {}),
    )

    # Determine missing fields
    if not result.format or result.format not in VALID_FORMATS:
        result.missing.append("format")
    if not result.site or result.site not in valid_sites:
        result.missing.append("site")
    if not result.keyword:
        result.missing.append("keyword")

    return result
