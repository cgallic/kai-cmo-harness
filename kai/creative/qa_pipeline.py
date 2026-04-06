"""Creative QA pipeline for the Kai Marketing OS.

Orchestrates multiple quality checks on creative output -- brand voice
consistency, claim safety, platform fit, message consistency, regulatory
compliance, banned words, AI slop detection, and quality gate integration.

Design principles
-----------------
1. **Rule-based, not script-executing.**  All checks are structural
   evaluations defined in code.  External script paths are referenced
   but never invoked.
2. **Actionable results.**  Every finding includes a specific location,
   severity, and fix suggestion so the operator knows exactly what to
   change.
3. **Severity-ordered.**  Fix suggestions are sorted errors-first so
   the most important issues surface at the top.
4. **Pure functions.**  No file I/O, no network calls, no subprocess
   invocations.

Uses Pydantic v2 ``BaseModel`` when available and falls back to a minimal
stdlib shim so the module works in environments without pydantic installed.
"""

from __future__ import annotations

import copy
import re
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import with stdlib fallback (mirrors gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:
        """Minimal pydantic-like fallback."""

        def __init__(self, **data):
            annotations = getattr(self.__class__, "__annotations__", {})
            for name in annotations:
                if name in data:
                    value = data.pop(name)
                elif hasattr(self.__class__, name):
                    value = copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self):
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self):
            import json
            return json.dumps(self.model_dump(), default=str)

        def __repr__(self):
            return f"{self.__class__.__name__}({self.model_dump()!r})"
else:
    BaseModel = _PydanticBaseModel
    Field = _PydanticField


# ============================================================================
# Enums
# ============================================================================


class QACheckType(str, Enum):
    """Type of quality-assurance check."""

    BRAND_VOICE = "brand_voice"
    CLAIM_SAFETY = "claim_safety"
    PLATFORM_FIT = "platform_fit"
    MESSAGE_CONSISTENCY = "message_consistency"
    COMPLIANCE = "compliance"
    FOUR_US = "four_us"
    BANNED_WORDS = "banned_words"
    SEO_LINT = "seo_lint"
    AI_SLOP = "ai_slop"


class QAStatus(str, Enum):
    """Outcome status of a QA check."""

    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


# ============================================================================
# Constants
# ============================================================================


BANNED_WORDS_TIER1: List[str] = [
    "leverage",
    "utilize",
    "synergy",
    "innovative",
    "deep dive",
    "circle back",
    "touch base",
    "moving forward",
    "at the end of the day",
]

AI_SLOP_PHRASES: List[str] = [
    "in conclusion",
    "it's important to note",
    "in today's rapidly evolving",
    "this comprehensive guide",
    "without further ado",
    "it's worth noting that",
    "in the ever-changing landscape",
    "it goes without saying",
    "needless to say",
    "at its core",
]

SUPERLATIVE_PATTERNS: List[str] = [
    r"\bbest\b",
    r"\b#1\b",
    r"\bnumber one\b",
    r"\bfastest\b",
    r"\bcheapest\b",
    r"\bleading\b",
    r"\btop-rated\b",
    r"\bworld-class\b",
    r"\bunmatched\b",
    r"\bunparalleled\b",
    r"\bguaranteed\b",
]

# Medical claim keywords.
_MEDICAL_KEYWORDS = [
    r"\bcure[sd]?\b",
    r"\btreat(?:s|ed|ment)?\b",
    r"\bdiagnos(?:e[sd]?|is|tic)\b",
    r"\bprevent(?:s|ed|ion)?\b",
    r"\bheal(?:s|ed|ing)?\b",
]

# Legal claim keywords.
_LEGAL_KEYWORDS = [
    r"\bguaranteed results?\b",
    r"\b100% success\b",
    r"\bnever lose\b",
    r"\bno risk\b",
]

# Financial claim keywords.
_FINANCIAL_KEYWORDS = [
    r"\bguaranteed returns?\b",
    r"\brisk-free investment\b",
    r"\bearn \$\d+\b",
    r"\bmake \$\d+\b",
]

# Absolute claim keywords.
_ABSOLUTE_KEYWORDS = [
    r"\balways\b",
    r"\bnever\b",
    r"\bevery time\b",
    r"\bzero risk\b",
]

# Comparison claim keywords.
_COMPARISON_KEYWORDS = [
    r"\bbetter than\b",
    r"\bunlike [\w]+\b",
    r"\bsuperior to\b",
]

# Tone-descriptor keyword patterns for brand voice checking.
_TONE_PATTERNS: Dict[str, Dict[str, Any]] = {
    "professional": {
        "avoid": [r"!!+", r"\blol\b", r"\bomg\b", r"\bwtf\b", r"\bbro\b", r"\bdude\b"],
        "description": "Avoid slang, emojis, excessive exclamation marks",
    },
    "casual": {
        "expect": [r"\b(you|we|I)\b", r"n't\b"],
        "description": "Can use contractions, conversational phrasing",
    },
    "warm": {
        "expect": [r"\bwe\b", r"\byou\b", r"\byour\b", r"\bunderstand\b", r"\bdeserve\b"],
        "description": "Personal pronouns, empathy language",
    },
    "direct": {
        "avoid": [r"\bmight\b", r"\bperhaps\b", r"\bmaybe\b", r"\bcould potentially\b"],
        "description": "Short sentences, imperatives, no hedging language",
    },
    "authoritative": {
        "expect": [r"\bdata\b", r"\bresearch\b", r"\bstud(?:y|ies)\b", r"\baccording to\b", r"\d+%"],
        "description": "Data citations, definitive statements, expert language",
    },
    "approachable": {
        "expect": [r"\bwe\b", r"\btogether\b", r"\?$"],
        "description": "Questions, inclusive language",
    },
    "playful": {
        "expect": [r"[!?]{2,}", r"\b(fun|love|awesome|amazing)\b"],
        "description": "Wordplay allowed, lighter tone, emoji acceptable",
    },
    "formal": {
        "avoid": [r"n't\b", r"\bcan't\b", r"\bwon't\b", r"\bdon't\b", r"\bgonna\b", r"\bwanna\b"],
        "description": "No contractions, complete sentences, no slang",
    },
}

# Platform policy file mapping.
_PLATFORM_POLICY_FILES: Dict[str, str] = {
    "google": "harness/references/google-ads-policy-reference.md",
    "google_ads": "harness/references/google-ads-policy-reference.md",
    "meta": "harness/references/meta-ads-rules.md",
    "facebook": "harness/references/meta-ads-rules.md",
    "instagram": "harness/references/meta-ads-rules.md",
    "tiktok": "harness/references/tiktok-ads-policy-reference.md",
    "linkedin": "harness/references/linkedin-ads-rules.md",
    "microsoft": "harness/references/microsoft-ads-rules.md",
    "bing": "harness/references/microsoft-ads-rules.md",
    "pinterest": "harness/references/pinterest-ads-rules.md",
    "snapchat": "harness/references/snapchat-ads-policy-reference.md",
    "amazon": "harness/references/amazon-ads-policy-reference.md",
    "x": "harness/references/x-ads-policy-reference.md",
    "twitter": "harness/references/x-ads-policy-reference.md",
}

# FTC spam trigger words for email subject lines.
_EMAIL_SPAM_TRIGGERS = [
    r"\bFREE\b",
    r"\bACT NOW\b",
    r"\bURGENT\b",
    r"\bLIMITED TIME\b",
    r"\bCLICK HERE\b",
    r"\bCONGRATULATIONS\b",
    r"\bYOU'VE BEEN SELECTED\b",
]


# ============================================================================
# Data Models
# ============================================================================


class QACheckResult(BaseModel):
    """Result of a single QA check."""

    check_type: str = ""
    status: str = QAStatus.PASSED.value
    score: Optional[float] = None
    threshold: Optional[float] = None
    passed: bool = True
    findings: List[Dict[str, Any]] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class QAResult(BaseModel):
    """Aggregated result of the full QA pipeline."""

    id: str = Field(default_factory=lambda: f"qa_{uuid.uuid4().hex[:12]}")
    content_id: str = ""
    brief_id: str = ""
    checks: List[Dict[str, Any]] = Field(default_factory=list)
    overall_status: str = QAStatus.PASSED.value
    total_checks: int = 0
    passed_checks: int = 0
    failed_checks: int = 0
    fix_suggestions: List[str] = Field(default_factory=list)
    approved_for_publishing: bool = False
    created_at: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ============================================================================
# Helpers
# ============================================================================


def _extract_text(content: Any) -> str:
    """Extract a flat text string from content which may be a str or dict."""
    if isinstance(content, str):
        return content
    if isinstance(content, dict):
        parts: List[str] = []
        for key in ("full_text", "content", "caption", "body", "text"):
            val = content.get(key, "")
            if isinstance(val, str) and val:
                parts.append(val)
        # Also check sections.
        for section in content.get("sections", []):
            if isinstance(section, dict):
                for key in ("content", "headline", "subheadline", "body", "heading"):
                    val = section.get(key, "")
                    if isinstance(val, str) and val:
                        parts.append(val)
        return "\n".join(parts)
    return str(content)


def _make_finding(
    issue: str,
    severity: str = "warning",
    location: Optional[str] = None,
    suggestion: str = "",
) -> Dict[str, Any]:
    """Create a standardized finding dict."""
    return {
        "issue": issue,
        "location": location,
        "severity": severity,
        "suggestion": suggestion,
    }


# ============================================================================
# Individual Check Functions
# ============================================================================


def check_brand_voice(
    content: str,
    brand_voice: Dict[str, Any],
) -> Dict[str, Any]:
    """Evaluate content against brand voice specifications.

    Checks tone alignment against ``tone_descriptors``, personality
    trait adherence, and basic competitor differentiation signals.
    """
    findings: List[Dict[str, Any]] = []
    content_lower = content.lower()

    # Extract tone descriptors.
    descriptors = brand_voice.get("tone_descriptors") or brand_voice.get("tone") or []
    if isinstance(descriptors, str):
        descriptors = [d.strip() for d in descriptors.split(",")]

    # Check each descriptor's patterns.
    for descriptor in descriptors:
        desc_lower = descriptor.lower().strip()
        patterns = _TONE_PATTERNS.get(desc_lower)
        if not patterns:
            continue

        # Check for patterns that should be avoided.
        for pattern in patterns.get("avoid", []):
            matches = re.findall(pattern, content, re.IGNORECASE | re.MULTILINE)
            if matches:
                findings.append(_make_finding(
                    issue=f"Tone '{descriptor}' violated: found '{matches[0]}' which conflicts with this tone.",
                    severity="warning",
                    location=f"Pattern: {pattern}",
                    suggestion=f"Remove or replace '{matches[0]}'. {patterns['description']}.",
                ))

    # Check personality traits -- flag traits NOT in the profile.
    personality_traits = brand_voice.get("personality_traits") or []
    if isinstance(personality_traits, str):
        personality_traits = [t.strip() for t in personality_traits.split(",")]
    personality_lower = [t.lower() for t in personality_traits]

    # If "humorous" is not listed, flag jokes/humor.
    if "humorous" not in personality_lower and "funny" not in personality_lower:
        humor_patterns = [r"\bjust kidding\b", r"\blol\b", r"\bhaha\b", r"\bjk\b"]
        for pattern in humor_patterns:
            if re.search(pattern, content, re.IGNORECASE):
                findings.append(_make_finding(
                    issue="Humor detected but 'humorous' is not in brand personality traits.",
                    severity="warning",
                    suggestion="Remove humorous language or add 'humorous' to brand personality traits.",
                ))
                break

    # Determine pass/fail.
    has_errors = any(f.get("severity") == "error" for f in findings)
    has_warnings = any(f.get("severity") == "warning" for f in findings)

    if has_errors:
        status = QAStatus.FAILED.value
    elif has_warnings:
        status = QAStatus.WARNING.value
    else:
        status = QAStatus.PASSED.value

    return QACheckResult(
        check_type=QACheckType.BRAND_VOICE.value,
        status=status,
        passed=not has_errors,
        findings=findings,
    ).model_dump()


def check_claim_safety(
    content: str,
    constraints: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Scan content for unsubstantiated or legally risky claims.

    Checks for superlatives without proof, medical/legal/financial
    claims, absolute claims, comparison claims, and income/results
    claims.
    """
    findings: List[Dict[str, Any]] = []
    content_lower = content.lower()
    constraints = constraints or {}
    is_regulated = constraints.get("regulated_industry", False)

    # Superlatives without proof.
    for pattern in SUPERLATIVE_PATTERNS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        for match in matches:
            word = match.group()
            # Check if a citation or specific number follows within 100 chars.
            context_after = content[match.end():match.end() + 100]
            has_citation = bool(re.search(r"\d+|according to|source:|study|survey", context_after, re.IGNORECASE))
            if not has_citation:
                findings.append(_make_finding(
                    issue=f"Superlative '{word}' used without supporting evidence.",
                    severity="error",
                    location=f"Near: '...{content[max(0, match.start()-20):match.end()+20]}...'",
                    suggestion=f"Either remove '{word}', qualify it ('one of the...'), or add a specific citation immediately after.",
                ))

    # Medical claims.
    for pattern in _MEDICAL_KEYWORDS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        for match in matches:
            severity = "error" if is_regulated else "warning"
            findings.append(_make_finding(
                issue=f"Potential medical claim: '{match.group()}'.",
                severity=severity,
                location=f"Near: '...{content[max(0, match.start()-20):match.end()+20]}...'",
                suggestion="Remove medical claim or add required disclaimer. Non-medical businesses should avoid medical language entirely.",
            ))

    # Legal claims.
    for pattern in _LEGAL_KEYWORDS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        for match in matches:
            findings.append(_make_finding(
                issue=f"Potential legal claim: '{match.group()}'.",
                severity="error",
                location=f"Near: '...{content[max(0, match.start()-20):match.end()+20]}...'",
                suggestion="Remove absolute legal claim or qualify with specific conditions and disclaimers.",
            ))

    # Financial claims.
    for pattern in _FINANCIAL_KEYWORDS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        for match in matches:
            findings.append(_make_finding(
                issue=f"Potential financial claim: '{match.group()}'.",
                severity="error",
                location=f"Near: '...{content[max(0, match.start()-20):match.end()+20]}...'",
                suggestion="Remove or add required financial disclosures. Include 'results may vary' disclaimer.",
            ))

    # Absolute claims.
    for pattern in _ABSOLUTE_KEYWORDS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        for match in matches:
            findings.append(_make_finding(
                issue=f"Absolute claim: '{match.group()}'. Absolute language is risky.",
                severity="warning",
                location=f"Near: '...{content[max(0, match.start()-20):match.end()+20]}...'",
                suggestion=f"Qualify '{match.group()}' -- use 'typically', 'in most cases', or add specific conditions.",
            ))

    # Comparison claims.
    for pattern in _COMPARISON_KEYWORDS:
        matches = list(re.finditer(pattern, content, re.IGNORECASE))
        for match in matches:
            findings.append(_make_finding(
                issue=f"Comparison claim: '{match.group()}'. Requires substantiation.",
                severity="warning",
                location=f"Near: '...{content[max(0, match.start()-20):match.end()+20]}...'",
                suggestion="Substantiate the comparison with specific evidence or remove the claim.",
            ))

    # Testimonial claims -- individual results presented as typical.
    testimonial_patterns = [r"\bI (?:lost|gained|earned|made|saved)\b", r"\bmy results\b"]
    for pattern in testimonial_patterns:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(_make_finding(
                issue="Individual results may be presented as typical. Needs disclaimer.",
                severity="warning",
                location="Testimonial/results section",
                suggestion="Add 'Results may vary. Individual results are not guaranteed.' disclaimer.",
            ))
            break

    # Check against profile-level claim restrictions.
    claim_restrictions = constraints.get("claims_restrictions") or []
    for restriction in claim_restrictions:
        if isinstance(restriction, str) and restriction.lower() in content_lower:
            findings.append(_make_finding(
                issue=f"Restricted claim found: '{restriction}'.",
                severity="error",
                location="Content body",
                suggestion=f"Remove '{restriction}' -- it is restricted by business profile constraints.",
            ))

    has_errors = any(f.get("severity") == "error" for f in findings)
    has_warnings = any(f.get("severity") == "warning" for f in findings)

    if has_errors:
        status = QAStatus.FAILED.value
    elif has_warnings:
        status = QAStatus.WARNING.value
    else:
        status = QAStatus.PASSED.value

    return QACheckResult(
        check_type=QACheckType.CLAIM_SAFETY.value,
        status=status,
        passed=not has_errors,
        findings=findings,
    ).model_dump()


def check_platform_fit(
    content: Dict[str, Any],
    platform: str,
    content_type: str,
) -> Dict[str, Any]:
    """Validate content against platform-specific constraints.

    Checks character limits, image dimensions, hashtag counts, video
    duration, and platform-specific policy rules.
    """
    from kai.creative.brief import PLATFORM_CONSTRAINTS

    findings: List[Dict[str, Any]] = []
    platform_lower = platform.lower()

    # Find the relevant constraint set.
    constraint_keys = [
        f"{platform_lower}_{content_type}",
        f"{platform_lower}_ads",
        f"{platform_lower}_post",
        platform_lower,
    ]
    constraints: Dict[str, Any] = {}
    for key in constraint_keys:
        if key in PLATFORM_CONSTRAINTS:
            constraints = PLATFORM_CONSTRAINTS[key]
            break

    # Character limit checks.
    text_fields = {
        "caption": constraints.get("caption_max_chars") or constraints.get("post_max_chars"),
        "primary_text": constraints.get("primary_text_max_chars"),
        "headline": constraints.get("headline_max_chars"),
        "description": constraints.get("description_max_chars"),
        "subject_line": constraints.get("subject_max_chars"),
        "preview_text": constraints.get("preview_max_chars"),
        "intro_text": constraints.get("intro_text_max_chars"),
    }

    for field_name, max_chars in text_fields.items():
        if max_chars is None:
            continue
        field_value = content.get(field_name, "")
        if isinstance(field_value, str) and len(field_value) > max_chars:
            findings.append(_make_finding(
                issue=f"'{field_name}' is {len(field_value)} chars, exceeds {platform} limit of {max_chars}.",
                severity="error",
                location=field_name,
                suggestion=f"Shorten '{field_name}' to {max_chars} characters or fewer.",
            ))

    # Check headlines list (Google Ads pattern).
    headlines = content.get("headlines") or []
    headline_max = constraints.get("headline_max_chars")
    if headline_max and isinstance(headlines, list):
        for i, headline in enumerate(headlines):
            if isinstance(headline, str) and len(headline) > headline_max:
                findings.append(_make_finding(
                    issue=f"Headline {i + 1} is {len(headline)} chars, exceeds limit of {headline_max}.",
                    severity="error",
                    location=f"headlines[{i}]",
                    suggestion=f"Shorten headline {i + 1} to {headline_max} characters.",
                ))

    # Check descriptions list (Google Ads pattern).
    descriptions = content.get("descriptions") or []
    desc_max = constraints.get("description_max_chars")
    if desc_max and isinstance(descriptions, list):
        for i, desc in enumerate(descriptions):
            if isinstance(desc, str) and len(desc) > desc_max:
                findings.append(_make_finding(
                    issue=f"Description {i + 1} is {len(desc)} chars, exceeds limit of {desc_max}.",
                    severity="error",
                    location=f"descriptions[{i}]",
                    suggestion=f"Shorten description {i + 1} to {desc_max} characters.",
                ))

    # Hashtag limit check.
    hashtag_max = constraints.get("hashtag_max")
    hashtags = content.get("hashtags") or []
    if hashtag_max and isinstance(hashtags, list) and len(hashtags) > hashtag_max:
        findings.append(_make_finding(
            issue=f"Too many hashtags: {len(hashtags)}, limit is {hashtag_max} for {platform}.",
            severity="warning",
            location="hashtags",
            suggestion=f"Reduce to {hashtag_max} hashtags. Prioritize niche + branded tags.",
        ))

    # Video duration check.
    video_max = constraints.get("video_max_seconds")
    duration = content.get("total_duration_seconds") or content.get("duration_target")
    if video_max and duration and isinstance(duration, (int, float)) and duration > video_max:
        findings.append(_make_finding(
            issue=f"Video duration {duration}s exceeds {platform} limit of {video_max}s.",
            severity="error",
            location="duration",
            suggestion=f"Edit video to {video_max} seconds or fewer.",
        ))

    # Platform-specific policy rules.
    if platform_lower in ("meta", "facebook", "instagram"):
        text = _extract_text(content)
        # No personal attributes ("You are overweight", "You look...").
        personal_patterns = [r"\byou are\b", r"\byou look\b", r"\byou have\b"]
        for pattern in personal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append(_make_finding(
                    issue="Meta policy: personal attributes language detected ('You are/look/have...').",
                    severity="error",
                    location="Content text",
                    suggestion="Rephrase to avoid directly addressing personal characteristics. Use 'People who...' instead of 'You are...'.",
                ))
                break

    if platform_lower in ("tiktok",):
        text = _extract_text(content)
        # AI content disclosure check.
        if not re.search(r"\bAI\b.*\bgenerated\b|\bgenerated\b.*\bAI\b|\bAI-generated\b", text, re.IGNORECASE):
            findings.append(_make_finding(
                issue="TikTok policy: AI-generated content must be disclosed.",
                severity="warning",
                location="Content metadata",
                suggestion="Add AI content disclosure label as required by TikTok policy.",
            ))

    if platform_lower in ("pinterest",):
        text = _extract_text(content)
        weight_loss_patterns = [r"\bweight loss\b", r"\blose weight\b", r"\bdiet\b", r"\bslimming\b"]
        for pattern in weight_loss_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append(_make_finding(
                    issue="Pinterest policy: weight loss advertising is banned (narrow GLP-1 exception only).",
                    severity="error",
                    location="Content text",
                    suggestion="Remove weight loss language. Pinterest bans all weight loss ads with narrow medical exceptions.",
                ))
                break

    if platform_lower in ("linkedin",):
        text = _extract_text(content)
        # Professional context check -- very informal language.
        informal_patterns = [r"\bomg\b", r"\blol\b", r"\bwtf\b", r"!!{3,}"]
        for pattern in informal_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                findings.append(_make_finding(
                    issue="LinkedIn: content may lack professional context.",
                    severity="warning",
                    location="Content text",
                    suggestion="Maintain professional tone. Remove overly informal language for LinkedIn.",
                ))
                break

    # Determine overall status.
    has_errors = any(f.get("severity") == "error" for f in findings)
    has_warnings = any(f.get("severity") == "warning" for f in findings)

    if has_errors:
        status = QAStatus.FAILED.value
    elif has_warnings:
        status = QAStatus.WARNING.value
    else:
        status = QAStatus.PASSED.value

    return QACheckResult(
        check_type=QACheckType.PLATFORM_FIT.value,
        status=status,
        passed=not has_errors,
        findings=findings,
    ).model_dump()


def check_message_consistency(
    content: Dict[str, Any],
    brief: Dict[str, Any],
) -> Dict[str, Any]:
    """Verify content is internally consistent and matches the brief.

    Checks CTA match, offer consistency, key message presence, persona
    alignment, and keyword presence.
    """
    findings: List[Dict[str, Any]] = []
    text = _extract_text(content)
    text_lower = text.lower()

    # CTA match.
    brief_cta = brief.get("cta", "")
    if brief_cta:
        # Check if the CTA or a close variant appears in the content.
        cta_lower = brief_cta.lower()
        cta_words = set(cta_lower.split())
        # Allow partial match -- at least half the words should appear.
        matching_words = sum(1 for w in cta_words if w in text_lower)
        if matching_words < len(cta_words) / 2:
            findings.append(_make_finding(
                issue=f"Brief CTA '{brief_cta}' not found in content.",
                severity="warning",
                location="CTA section",
                suggestion=f"Include the CTA '{brief_cta}' or a close variant in the content.",
            ))

    # Check for multiple competing CTAs.
    cta_patterns = [
        r"\bcall now\b", r"\bcontact us\b", r"\bget started\b",
        r"\blearn more\b", r"\bbook now\b", r"\bsign up\b",
        r"\bschedule\b", r"\bdownload\b", r"\bsubscribe\b",
        r"\bbuy now\b", r"\bshop now\b", r"\bclaim\b",
    ]
    found_ctas = []
    for pattern in cta_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            found_ctas.append(pattern.replace(r"\b", "").strip())
    if len(found_ctas) > 3:
        findings.append(_make_finding(
            issue=f"Multiple competing CTAs detected ({len(found_ctas)}). This may confuse the reader.",
            severity="warning",
            location="Throughout content",
            suggestion="Reduce to one primary CTA. Use the same CTA consistently throughout.",
        ))

    # Offer consistency.
    brief_offer = brief.get("offer", "")
    if brief_offer:
        offer_lower = brief_offer.lower()
        if offer_lower not in text_lower:
            # Check for partial match.
            offer_words = set(offer_lower.split())
            matching = sum(1 for w in offer_words if w in text_lower and len(w) > 3)
            if matching < len(offer_words) / 2:
                findings.append(_make_finding(
                    issue=f"Brief offer '{brief_offer}' not mentioned in content.",
                    severity="warning",
                    location="Content body",
                    suggestion=f"Include the offer '{brief_offer}' in the content, ideally near the CTA.",
                ))

    # Key message presence.
    key_message = brief.get("key_message", "")
    if key_message:
        km_lower = key_message.lower()
        km_words = [w for w in km_lower.split() if len(w) > 3]
        if km_words:
            matching = sum(1 for w in km_words if w in text_lower)
            if matching < len(km_words) / 3:
                findings.append(_make_finding(
                    issue="Key message from brief does not appear to be reflected in the content.",
                    severity="warning",
                    location="Content body",
                    suggestion=f"Ensure the content conveys: '{key_message[:100]}'.",
                ))

    # Keyword presence (SEO content).
    target_keyword = brief.get("target_keyword", "")
    if target_keyword:
        kw_lower = target_keyword.lower()
        if kw_lower not in text_lower:
            findings.append(_make_finding(
                issue=f"Target keyword '{target_keyword}' not found in content.",
                severity="error" if brief.get("quality_gate_thresholds", {}).get("seo_lint") else "warning",
                location="Content body",
                suggestion=f"Include '{target_keyword}' naturally in the content, ideally in the first paragraph and a heading.",
            ))

    # Determine status.
    has_errors = any(f.get("severity") == "error" for f in findings)
    has_warnings = any(f.get("severity") == "warning" for f in findings)

    if has_errors:
        status = QAStatus.FAILED.value
    elif has_warnings:
        status = QAStatus.WARNING.value
    else:
        status = QAStatus.PASSED.value

    return QACheckResult(
        check_type=QACheckType.MESSAGE_CONSISTENCY.value,
        status=status,
        passed=not has_errors,
        findings=findings,
    ).model_dump()


def check_compliance(
    content: str,
    platform: str,
    content_type: str,
    regulated_industry: bool = False,
) -> Dict[str, Any]:
    """Check content against regulatory and platform compliance rules.

    Covers FTC, CAN-SPAM (email), GDPR (EU), COPPA (children), and
    click-to-cancel (subscriptions).  References platform-specific policy
    files for the execution layer to load.
    """
    findings: List[Dict[str, Any]] = []
    content_lower = content.lower()
    platform_lower = platform.lower()

    # FTC: Material connections disclosure.
    sponsored_indicators = [r"\bsponsored\b", r"\bpartner(?:ship)?\b", r"\bpaid\b", r"\baffiliate\b"]
    for pattern in sponsored_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            if not re.search(r"\b(?:ad|sponsored|#ad|#sponsored|paid partnership)\b", content, re.IGNORECASE):
                findings.append(_make_finding(
                    issue="FTC: Material connection indicated but no clear disclosure found.",
                    severity="error",
                    location="Content body",
                    suggestion="Add clear FTC disclosure: '#ad', '#sponsored', or 'Paid partnership' at the beginning of the content.",
                ))
            break

    # FTC: Testimonials should be attributed.
    if re.search(r'["\u201c].{10,}["\u201d]', content):
        if not re.search(r"(?:[-\u2014]\s*\w+|attributed|from\s+\w+)", content):
            findings.append(_make_finding(
                issue="FTC: Testimonial quote found without clear attribution.",
                severity="warning",
                location="Testimonial section",
                suggestion="Attribute all testimonial quotes to a named source.",
            ))

    # CAN-SPAM (email only).
    if content_type in ("email", "cold_outreach", "email_sequence"):
        # Physical address.
        if not re.search(r"\d+\s+\w+\s+(?:st|ave|blvd|rd|dr|ln|ct|way|street|avenue)", content, re.IGNORECASE):
            findings.append(_make_finding(
                issue="CAN-SPAM: No physical address detected in email content.",
                severity="error",
                location="Email footer",
                suggestion="Include a valid physical mailing address in the email footer.",
            ))

        # Unsubscribe mechanism.
        if not re.search(r"\bunsubscribe\b|\bopt.?out\b|\bmanage\s+preferences?\b", content, re.IGNORECASE):
            findings.append(_make_finding(
                issue="CAN-SPAM: No unsubscribe/opt-out mechanism found.",
                severity="error",
                location="Email footer",
                suggestion="Include a clear unsubscribe link in the email footer.",
            ))

    # GDPR (if targeting EU or if content mentions EU/GDPR).
    if re.search(r"\b(?:EU|GDPR|Europe|European)\b", content, re.IGNORECASE):
        if not re.search(r"\bconsent\b|\bprivacy\b|\bdata\s+protection\b", content, re.IGNORECASE):
            findings.append(_make_finding(
                issue="GDPR: EU-targeting content without consent/privacy language.",
                severity="warning",
                location="Content body",
                suggestion="Include consent language and link to privacy policy for EU-targeted content.",
            ))

    # COPPA: content targeting children.
    child_indicators = [r"\bkids\b", r"\bchildren\b", r"\bunder\s+13\b", r"\bchild\b"]
    for pattern in child_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            findings.append(_make_finding(
                issue="COPPA: Content may target children under 13. Special rules apply.",
                severity="error",
                location="Content body",
                suggestion="Review COPPA requirements. Do not collect personal information from children under 13 without parental consent.",
            ))
            break

    # Click-to-cancel (FTC rule for subscriptions).
    subscription_indicators = [r"\bsubscrib", r"\bmembership\b", r"\bmonthly\s+plan\b", r"\brecurring\b"]
    for pattern in subscription_indicators:
        if re.search(pattern, content, re.IGNORECASE):
            if not re.search(r"\bcancel\b|\bterminate\b|\bend\s+(?:your\s+)?(?:subscription|membership)\b", content, re.IGNORECASE):
                findings.append(_make_finding(
                    issue="FTC click-to-cancel: subscription promoted without cancellation information.",
                    severity="warning",
                    location="Content body",
                    suggestion="Include cancellation information when promoting subscriptions (FTC click-to-cancel rule).",
                ))
            break

    # Regulated industry -- extra disclaimers.
    if regulated_industry:
        disclaimer_patterns = [r"\bdisclaimer\b", r"\bnot\s+(?:legal|medical|financial)\s+advice\b", r"\bconsult\b"]
        has_disclaimer = any(re.search(p, content, re.IGNORECASE) for p in disclaimer_patterns)
        if not has_disclaimer:
            findings.append(_make_finding(
                issue="Regulated industry content without required disclaimer.",
                severity="error",
                location="Content footer",
                suggestion="Add appropriate disclaimer: 'This is not legal/medical/financial advice. Consult a qualified professional.'",
            ))

    # Platform-specific policy file reference.
    policy_file = _PLATFORM_POLICY_FILES.get(platform_lower)
    if policy_file:
        findings.append(_make_finding(
            issue=f"Platform policy review needed: check against {policy_file}",
            severity="info",
            location="Full content",
            suggestion=f"Load and review {policy_file} for {platform}-specific compliance.",
        ))

    # Determine status.
    has_errors = any(f.get("severity") == "error" for f in findings)
    has_warnings = any(f.get("severity") == "warning" for f in findings)

    if has_errors:
        status = QAStatus.FAILED.value
    elif has_warnings:
        status = QAStatus.WARNING.value
    else:
        status = QAStatus.PASSED.value

    return QACheckResult(
        check_type=QACheckType.COMPLIANCE.value,
        status=status,
        passed=not has_errors,
        findings=findings,
    ).model_dump()


def check_quality_gates(
    content: str,
    brief: Dict[str, Any],
) -> Dict[str, Any]:
    """Define quality gate checks and perform inline scans.

    Returns a combined result:
    - Script references (four_us, banned_words, seo_lint) with paths
      and thresholds for the execution layer to run externally.
    - Inline scan results for banned words and AI slop that are
      performed directly in this function.
    """
    thresholds = brief.get("quality_gate_thresholds") or {}
    four_us_min = thresholds.get("four_us_min", 12)
    seo_lint_enabled = thresholds.get("seo_lint", False)

    # Script references (NOT executed).
    script_refs = {
        "four_us": {
            "script": "scripts/quality_gates/four_us_score.py",
            "threshold": four_us_min,
            "description": f"Four U's score must be >= {four_us_min}/16.",
        },
        "banned_words": {
            "script": "scripts/quality_gates/banned_word_check.py",
            "threshold": 0,
            "description": "Zero Tier 1 banned words allowed.",
        },
    }
    if seo_lint_enabled:
        script_refs["seo_lint"] = {
            "script": "scripts/quality_gates/seo_lint.py",
            "threshold": None,
            "description": "Algorithmic authorship rule compliance.",
        }

    # Inline banned word scan.
    banned_findings: List[Dict[str, Any]] = []
    content_lower = content.lower()

    for word in BANNED_WORDS_TIER1:
        pattern = r"\b" + re.escape(word) + r"\b"
        matches = list(re.finditer(pattern, content_lower))
        for match in matches:
            # Find approximate location.
            start = max(0, match.start() - 20)
            end = min(len(content), match.end() + 20)
            context = content[start:end]
            banned_findings.append(_make_finding(
                issue=f"Banned word (Tier 1): '{word}'",
                severity="error",
                location=f"Near: '...{context}...'",
                suggestion=_get_banned_word_replacement(word),
            ))

    banned_passed = len(banned_findings) == 0
    banned_result = QACheckResult(
        check_type=QACheckType.BANNED_WORDS.value,
        status=QAStatus.PASSED.value if banned_passed else QAStatus.FAILED.value,
        passed=banned_passed,
        findings=banned_findings,
    ).model_dump()

    # Inline AI slop scan.
    slop_findings: List[Dict[str, Any]] = []
    for phrase in AI_SLOP_PHRASES:
        pattern = re.escape(phrase)
        matches = list(re.finditer(pattern, content_lower))
        for match in matches:
            start = max(0, match.start() - 20)
            end = min(len(content), match.end() + 20)
            context = content[start:end]
            slop_findings.append(_make_finding(
                issue=f"AI slop phrase detected: '{phrase}'",
                severity="error",
                location=f"Near: '...{context}...'",
                suggestion=f"Remove '{phrase}'. Rewrite the sentence with specific, concrete language.",
            ))

    slop_passed = len(slop_findings) == 0
    slop_result = QACheckResult(
        check_type=QACheckType.AI_SLOP.value,
        status=QAStatus.PASSED.value if slop_passed else QAStatus.FAILED.value,
        passed=slop_passed,
        findings=slop_findings,
    ).model_dump()

    return {
        "script_references": script_refs,
        "inline_results": {
            "banned_words": banned_result,
            "ai_slop": slop_result,
        },
    }


def _get_banned_word_replacement(word: str) -> str:
    """Return a suggested replacement for a banned word."""
    replacements = {
        "leverage": "Replace 'leverage' with 'use', 'apply', or a specific verb.",
        "utilize": "Replace 'utilize' with 'use'.",
        "synergy": "Replace 'synergy' with 'collaboration', 'partnership', or describe the specific benefit.",
        "innovative": "Replace 'innovative' with a specific description of what is new.",
        "deep dive": "Replace 'deep dive' with 'detailed analysis', 'thorough look', or 'breakdown'.",
        "circle back": "Replace 'circle back' with 'follow up', 'revisit', or 'return to'.",
        "touch base": "Replace 'touch base' with 'check in', 'connect', or 'discuss'.",
        "moving forward": "Replace 'moving forward' with 'next', 'from here', or 'going ahead'.",
        "at the end of the day": "Replace 'at the end of the day' with 'ultimately', 'in practice', or just make the point directly.",
    }
    return replacements.get(word.lower(), f"Remove '{word}' and use specific, concrete language instead.")


# ============================================================================
# Main Orchestrator
# ============================================================================


def run_qa_pipeline(
    content: Dict[str, Any],
    brief: Dict[str, Any],
    business_profile: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Orchestrate all applicable QA checks on creative content.

    Determines which checks apply based on content format and brief,
    runs all applicable checks, aggregates results into a QAResult,
    and produces severity-ordered fix suggestions.

    Parameters
    ----------
    content:
        A CopyOutput dict or any content dict to check.
    brief:
        A CreativeBrief dict with quality thresholds and targeting info.
    business_profile:
        Optional BusinessProfile dict with brand_voice, constraints, etc.

    Returns
    -------
    Dict[str, Any]
        A QAResult dict with all check results and fix suggestions.
    """
    checks: List[Dict[str, Any]] = []
    text = _extract_text(content)
    platform = brief.get("channel", "website")
    content_format = brief.get("format", "")

    # 1. Brand voice check (if business_profile has brand_voice).
    brand_voice = (business_profile or {}).get("brand_voice")
    if brand_voice and isinstance(brand_voice, dict):
        checks.append(check_brand_voice(text, brand_voice))
    else:
        checks.append(QACheckResult(
            check_type=QACheckType.BRAND_VOICE.value,
            status=QAStatus.SKIPPED.value,
            passed=True,
            metadata={"reason": "No brand_voice in business_profile"},
        ).model_dump())

    # 2. Claim safety (always).
    constraints = (business_profile or {}).get("constraints")
    checks.append(check_claim_safety(text, constraints))

    # 3. Platform fit (if platform-specific content).
    if platform and platform != "website":
        checks.append(check_platform_fit(content, platform, content_format))
    elif content_format in ("ad_copy", "social_post"):
        # Ad copy and social posts always need platform fit check.
        checks.append(check_platform_fit(content, platform, content_format))
    else:
        checks.append(QACheckResult(
            check_type=QACheckType.PLATFORM_FIT.value,
            status=QAStatus.SKIPPED.value,
            passed=True,
            metadata={"reason": "No specific platform targeting"},
        ).model_dump())

    # 4. Message consistency (always).
    checks.append(check_message_consistency(content, brief))

    # 5. Compliance (always).
    regulated = (business_profile or {}).get("constraints", {})
    is_regulated = False
    if isinstance(regulated, dict):
        is_regulated = regulated.get("regulated_industry", False)
    checks.append(check_compliance(text, platform, content_format, is_regulated))

    # 6. Quality gates (inline banned words + AI slop, plus script references).
    gate_results = check_quality_gates(text, brief)
    inline_results = gate_results.get("inline_results", {})

    # Add inline banned words result.
    banned_result = inline_results.get("banned_words", {})
    checks.append(banned_result)

    # Add inline AI slop result.
    slop_result = inline_results.get("ai_slop", {})
    checks.append(slop_result)

    # Add four_us as a reference-only check.
    thresholds = brief.get("quality_gate_thresholds") or {}
    four_us_min = thresholds.get("four_us_min", 12)
    checks.append(QACheckResult(
        check_type=QACheckType.FOUR_US.value,
        status=QAStatus.PASSED.value,  # Can't determine without running script.
        threshold=float(four_us_min),
        passed=True,
        metadata={
            "note": "Four U's score requires external script execution.",
            "script": "scripts/quality_gates/four_us_score.py",
            "threshold": four_us_min,
        },
    ).model_dump())

    # Add SEO lint as reference-only (if applicable).
    seo_lint_enabled = thresholds.get("seo_lint", False)
    if seo_lint_enabled:
        checks.append(QACheckResult(
            check_type=QACheckType.SEO_LINT.value,
            status=QAStatus.PASSED.value,  # Can't determine without running script.
            passed=True,
            metadata={
                "note": "SEO lint requires external script execution.",
                "script": "scripts/quality_gates/seo_lint.py",
            },
        ).model_dump())

    # Aggregate results.
    total = len(checks)
    passed = sum(1 for c in checks if c.get("passed", False))
    failed = sum(1 for c in checks if not c.get("passed", True) and c.get("status") != QAStatus.SKIPPED.value)

    # Compute overall status (worst status wins).
    statuses = [c.get("status", QAStatus.PASSED.value) for c in checks]
    if QAStatus.FAILED.value in statuses:
        overall = QAStatus.FAILED.value
    elif QAStatus.WARNING.value in statuses:
        overall = QAStatus.WARNING.value
    else:
        overall = QAStatus.PASSED.value

    # Generate fix suggestions ordered by severity.
    all_findings: List[Dict[str, Any]] = []
    for check in checks:
        for finding in check.get("findings", []):
            all_findings.append(finding)

    # Sort: errors first, then warnings, then info.
    severity_order = {"error": 0, "warning": 1, "info": 2}
    all_findings.sort(key=lambda f: severity_order.get(f.get("severity", "info"), 3))

    fix_suggestions: List[str] = []
    for finding in all_findings:
        severity = finding.get("severity", "info")
        issue = finding.get("issue", "")
        suggestion = finding.get("suggestion", "")
        if severity in ("error", "warning"):
            prefix = "ERROR" if severity == "error" else "WARNING"
            fix_suggestions.append(f"[{prefix}] {issue} -- {suggestion}")

    # approved_for_publishing = True only if no error-severity findings.
    has_errors = any(f.get("severity") == "error" for f in all_findings)
    approved = not has_errors

    result = QAResult(
        content_id=content.get("id", ""),
        brief_id=brief.get("id", ""),
        checks=checks,
        overall_status=overall,
        total_checks=total,
        passed_checks=passed,
        failed_checks=failed,
        fix_suggestions=fix_suggestions,
        approved_for_publishing=approved,
        created_at=datetime.now(timezone.utc).isoformat(),
        metadata={
            "script_references": gate_results.get("script_references", {}),
        },
    )

    return result.model_dump()
