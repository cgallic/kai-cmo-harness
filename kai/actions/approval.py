"""Page diff preview and approval workflow for website actions.

Generates visual diffs between before/after content, assesses risk, and
manages the approval lifecycle.  Every website mutation flows through this
module before reaching execution:

    generate_diff_preview  ->  create_approval_request  ->  approve / reject / request_revision

Auto-approval is available for low-risk changes when the operator opts in,
but defaults to off (conservative).  All functions are pure -- no external I/O.
"""

from __future__ import annotations

import copy
import difflib
import enum
import re
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Pydantic import -- same fallback pattern as gateway/models.py
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBaseModel, Field as _PydanticField
except ImportError:  # pragma: no cover - fallback for minimal runtimes
    _PydanticBaseModel = None

    def Field(default=None, *, default_factory=None, **kwargs):  # type: ignore[misc]
        if default_factory is not None:
            return default_factory()
        return default

    class BaseModel:  # type: ignore[no-redef]
        """Minimal pydantic-like fallback."""

        def __init__(self, **data: Any) -> None:
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

        def model_dump(self) -> Dict[str, Any]:
            return {
                key: value
                for key, value in self.__dict__.items()
                if not key.startswith("_")
            }

        def model_dump_json(self) -> str:
            import json

            return json.dumps(self.model_dump(), default=str)

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"

else:
    BaseModel = _PydanticBaseModel  # type: ignore[assignment,misc]
    Field = _PydanticField  # type: ignore[assignment,misc]


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_RISK_TIER_ORDER: Dict[str, int] = {
    "auto": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

VALID_CHANGE_TYPES = frozenset({
    "copy_update",
    "section_addition",
    "section_removal",
    "section_reorder",
    "metadata_update",
    "tracking_update",
    "cta_update",
})

DEFAULT_AUTO_APPROVE_SETTINGS: Dict[str, Any] = {
    "enabled": False,  # Conservative default: require human approval
    "max_risk_tier": "low",
    "allowed_change_types": ["metadata_update", "tracking_update"],
    "require_preview": True,
    "max_word_count_change": 50,
    "blocked_pages": [],  # No specific pages blocked by default
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _new_id(prefix: str) -> str:
    """Generate a short prefixed identifier from a UUID hex."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _word_count(text: str) -> int:
    """Count whitespace-delimited words in *text*."""
    return len(text.split())


def _is_homepage_slug(page_id: str, page_info: Optional[Dict[str, Any]] = None) -> bool:
    """Return True when the page is likely the homepage."""
    slug = page_id.strip("/").lower()
    if slug in ("", "home", "index", "index.html", "index.php"):
        return True
    if page_info:
        if page_info.get("is_front_page"):
            return True
        info_slug = str(page_info.get("slug", "")).strip("/").lower()
        if info_slug in ("", "home", "index", "index.html", "index.php"):
            return True
    return False


# ---------------------------------------------------------------------------
# Detection helpers (content-level risk signals)
# ---------------------------------------------------------------------------

_SEO_PATTERNS = re.compile(
    r"<title[\s>]|<meta[\s>]|<h1[\s>]|<h2[\s>]|<link[^>]+rel=[\"']canonical|"
    r"application/ld\+json|schema\.org",
    re.IGNORECASE,
)

_TRACKING_PATTERNS = re.compile(
    r"<script[\s>]|data-layer|dataLayer|gtag\(|fbq\(|_paq\.|hotjar|"
    r"googletagmanager|analytics|pixel",
    re.IGNORECASE,
)

_CONVERSION_PATTERNS = re.compile(
    r"<form[\s>]|<button[\s>]|<a[^>]+(?:class|id)\s*=\s*[\"'][^\"']*(?:cta|btn|button)|"
    r"tel:|href=[\"']tel:|"
    r"\b\d{3}[-.\s]?\d{3}[-.\s]?\d{4}\b|"
    r"\(\d{3}\)\s?\d{3}[-.\s]?\d{4}|"
    r"\$\d+|\bpric(?:e|ing)\b",
    re.IGNORECASE,
)


def _content_has_seo_elements(content: str) -> bool:
    return bool(_SEO_PATTERNS.search(content))


def _content_has_tracking_elements(content: str) -> bool:
    return bool(_TRACKING_PATTERNS.search(content))


def _content_has_conversion_elements(content: str) -> bool:
    return bool(_CONVERSION_PATTERNS.search(content))


# ---------------------------------------------------------------------------
# Enum: ApprovalStatus
# ---------------------------------------------------------------------------


class ApprovalStatus(str, enum.Enum):
    """Lifecycle status for an approval request."""

    pending = "pending"
    approved = "approved"
    auto_approved = "auto_approved"
    rejected = "rejected"
    revision_requested = "revision_requested"
    expired = "expired"


# ---------------------------------------------------------------------------
# Model: DiffPreview
# ---------------------------------------------------------------------------


class DiffPreview(BaseModel):
    """Visual diff between the before and after state of a page change."""

    id: str = Field(default_factory=lambda: _new_id("diff"))
    action_id: str = ...  # type: ignore[assignment]
    page_id: str = ...  # type: ignore[assignment]
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    before_content: str = ...  # type: ignore[assignment]
    after_content: str = ...  # type: ignore[assignment]
    diff_html: str = ""
    diff_text: str = ""
    change_summary: str = ""
    change_type: str = "copy_update"
    lines_added: int = 0
    lines_removed: int = 0
    lines_modified: int = 0
    risk_assessment: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[str] = Field(default_factory=_utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Model: ApprovalRequest
# ---------------------------------------------------------------------------


class ApprovalRequest(BaseModel):
    """An operator-facing approval request wrapping a diff preview."""

    id: str = Field(default_factory=lambda: _new_id("apr"))
    action_id: str = ...  # type: ignore[assignment]
    diff_preview_id: str = ...  # type: ignore[assignment]
    diff_preview: Optional[Dict[str, Any]] = None
    risk_tier: str = "medium"
    auto_approve_eligible: bool = False
    auto_approve_reason: Optional[str] = None
    status: str = Field(default=ApprovalStatus.pending.value)
    operator_notes: Optional[str] = None
    revision_instructions: Optional[str] = None
    approved_by: Optional[str] = None
    decided_at: Optional[str] = None
    expires_at: Optional[str] = None
    created_at: Optional[str] = Field(default_factory=_utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Diff generation
# ---------------------------------------------------------------------------


def _generate_diff_text(before: str, after: str) -> str:
    """Return a unified-diff string from *before* to *after*."""
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    diff_lines = difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile="before",
        tofile="after",
    )
    return "".join(diff_lines)


def _generate_diff_html(before: str, after: str) -> str:
    """Return an HTML diff with ``<ins>``/``<del>`` markup.

    Compares line-by-line.  Removed lines are wrapped in ``<del>`` with a
    red background; added lines in ``<ins>`` with a green background.
    Modified lines show the old version in ``<del>`` and the new in ``<ins>``.
    Unchanged context lines are included plain.
    """
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    matcher = difflib.SequenceMatcher(None, before_lines, after_lines)

    html_parts: List[str] = [
        "<div class='diff-preview' "
        "style='font-family:monospace;font-size:13px;line-height:1.6;'>"
    ]

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for line in before_lines[i1:i2]:
                html_parts.append(
                    f"<div style='padding:2px 8px;'>{_escape_html(line)}</div>"
                )
        elif tag == "delete":
            for line in before_lines[i1:i2]:
                html_parts.append(
                    f"<del style='display:block;background:#fdd;padding:2px 8px;"
                    f"text-decoration:none;'>{_escape_html(line)}</del>"
                )
        elif tag == "insert":
            for line in after_lines[j1:j2]:
                html_parts.append(
                    f"<ins style='display:block;background:#dfd;padding:2px 8px;"
                    f"text-decoration:none;'>{_escape_html(line)}</ins>"
                )
        elif tag == "replace":
            for line in before_lines[i1:i2]:
                html_parts.append(
                    f"<del style='display:block;background:#fdd;padding:2px 8px;"
                    f"text-decoration:none;'>{_escape_html(line)}</del>"
                )
            for line in after_lines[j1:j2]:
                html_parts.append(
                    f"<ins style='display:block;background:#dfd;padding:2px 8px;"
                    f"text-decoration:none;'>{_escape_html(line)}</ins>"
                )

    html_parts.append("</div>")
    return "\n".join(html_parts)


def _escape_html(text: str) -> str:
    """Minimal HTML entity escaping for diff display."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _count_diff_lines(before: str, after: str) -> Dict[str, int]:
    """Count added, removed, and modified lines between two strings.

    "Modified" is estimated as the minimum of contiguous replace-blocks
    detected by :class:`difflib.SequenceMatcher`.
    """
    before_lines = before.splitlines()
    after_lines = after.splitlines()
    matcher = difflib.SequenceMatcher(None, before_lines, after_lines)

    added = 0
    removed = 0
    modified = 0

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "insert":
            added += j2 - j1
        elif tag == "delete":
            removed += i2 - i1
        elif tag == "replace":
            overlap = min(i2 - i1, j2 - j1)
            modified += overlap
            extra_removed = (i2 - i1) - overlap
            extra_added = (j2 - j1) - overlap
            removed += extra_removed
            added += extra_added

    return {"lines_added": added, "lines_removed": removed, "lines_modified": modified}


def _build_change_summary(
    action: Dict[str, Any],
    change_type: str,
    lines_added: int,
    lines_removed: int,
    lines_modified: int,
) -> str:
    """Produce a human-readable summary of what changed."""
    action_type = action.get("action_type", change_type)
    target = action.get("target", action.get("page_id", "page"))
    reason = action.get("reason", "")

    # Attempt to extract old/new values for concise summaries
    params = action.get("parameters", {})
    old_value = params.get("old_value") or params.get("before_value", "")
    new_value = params.get("new_value") or params.get("after_value", "")

    if old_value and new_value:
        old_short = (old_value[:60] + "...") if len(old_value) > 60 else old_value
        new_short = (new_value[:60] + "...") if len(new_value) > 60 else new_value
        return f"Updated {target}: changed from '{old_short}' to '{new_short}'"

    parts: List[str] = []
    if reason:
        parts.append(reason)
    else:
        parts.append(f"{action_type} on {target}")

    detail_bits: List[str] = []
    if lines_added:
        detail_bits.append(f"+{lines_added} lines")
    if lines_removed:
        detail_bits.append(f"-{lines_removed} lines")
    if lines_modified:
        detail_bits.append(f"~{lines_modified} modified")
    if detail_bits:
        parts.append(f"({', '.join(detail_bits)})")

    return " ".join(parts)


def _infer_change_type(action: Dict[str, Any]) -> str:
    """Infer a change_type from action metadata if not explicitly set."""
    explicit = action.get("change_type")
    if explicit and explicit in VALID_CHANGE_TYPES:
        return explicit

    action_type = action.get("action_type", "").lower()

    type_map = {
        "updatepagecopy": "copy_update",
        "updatepagesection": "copy_update",
        "updatecta": "cta_update",
        "updatemetadata": "metadata_update",
        "fixtracking": "tracking_update",
        "addsection": "section_addition",
        "restructurepage": "section_reorder",
        "refreshapprovedsection": "copy_update",
    }

    for key, value in type_map.items():
        if key in action_type:
            return value

    return "copy_update"


# ---------------------------------------------------------------------------
# Public API: risk assessment
# ---------------------------------------------------------------------------


def assess_risk(
    diff_preview: Dict[str, Any],
    page_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Evaluate the risk of a proposed change.

    Parameters
    ----------
    diff_preview : dict
        A :class:`DiffPreview`-shaped dict.
    page_info : dict, optional
        Extra page metadata (``is_front_page``, ``slug``, etc.).

    Returns
    -------
    dict
        Structured risk assessment with ``risk_tier``, ``risk_factors``, and
        per-dimension boolean flags.
    """
    before = diff_preview.get("before_content", "")
    after = diff_preview.get("after_content", "")
    change_type = diff_preview.get("change_type", "copy_update")
    page_id = diff_preview.get("page_id", "")

    # Combine before+after to detect what areas are touched
    combined_diff_content = before + "\n" + after

    is_homepage = _is_homepage_slug(page_id, page_info)

    # Public-facing: only metadata_update and tracking_update are not
    is_public_facing = change_type not in ("tracking_update", "metadata_update")

    # SEO: check if changes touch title, meta, headings, schema, canonical
    before_seo = _content_has_seo_elements(before)
    after_seo = _content_has_seo_elements(after)
    affects_seo = before_seo or after_seo

    # Tracking: check for script tags, data-layer, pixels
    before_tracking = _content_has_tracking_elements(before)
    after_tracking = _content_has_tracking_elements(after)
    affects_tracking = before_tracking or after_tracking

    # Conversion: forms, CTA links, phone numbers, pricing
    before_conversion = _content_has_conversion_elements(before)
    after_conversion = _content_has_conversion_elements(after)
    affects_conversion = before_conversion or after_conversion

    # Word count delta
    before_wc = _word_count(before)
    after_wc = _word_count(after)
    word_count_change = after_wc - before_wc
    abs_word_change = abs(word_count_change)

    # --- Risk factors ---
    risk_factors: List[str] = []

    if is_homepage:
        risk_factors.append("Homepage change")
    if affects_seo:
        risk_factors.append("SEO elements affected (title/meta/headings/schema)")
    if affects_tracking:
        risk_factors.append("Tracking/analytics code affected")
    if affects_conversion:
        risk_factors.append("Conversion elements affected (CTA/form/phone/pricing)")
    if abs_word_change > 200:
        risk_factors.append(f"Large content change ({abs_word_change} words)")
    elif abs_word_change > 50:
        risk_factors.append(f"Medium content change ({abs_word_change} words)")
    if change_type == "section_removal":
        risk_factors.append("Section removal")
    if change_type == "section_reorder":
        risk_factors.append("Section reorder")

    # --- Tier assignment ---
    # Determine whether the hero/CTA on the homepage is being changed
    is_homepage_hero_cta = is_homepage and (
        change_type == "cta_update"
        or (affects_conversion and change_type in ("copy_update", "section_addition"))
    )

    multiple_conversion_signals = sum([
        before_conversion and after_conversion,
        bool(re.search(r"tel:", combined_diff_content, re.IGNORECASE)),
        bool(re.search(r"<form", combined_diff_content, re.IGNORECASE)),
        change_type == "cta_update",
    ])

    if is_homepage_hero_cta or multiple_conversion_signals >= 2:
        risk_tier = "critical"
    elif is_homepage or abs_word_change > 200 or affects_conversion:
        risk_tier = "high"
    elif abs_word_change > 50 or (affects_seo and not is_homepage):
        risk_tier = "medium"
    elif is_public_facing and abs_word_change <= 50 and not affects_conversion:
        risk_tier = "low"
    else:
        # Not public-facing AND not conversion-affecting
        risk_tier = "auto"

    return {
        "risk_tier": risk_tier,
        "risk_factors": risk_factors,
        "is_homepage": is_homepage,
        "is_public_facing": is_public_facing,
        "affects_seo": affects_seo,
        "affects_tracking": affects_tracking,
        "affects_conversion": affects_conversion,
        "word_count_change": word_count_change,
    }


# ---------------------------------------------------------------------------
# Public API: diff preview generation
# ---------------------------------------------------------------------------


def generate_diff_preview(
    action: Dict[str, Any],
    before_content: str,
    after_content: str,
    page_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Generate a :class:`DiffPreview` dict from action data and content.

    Parameters
    ----------
    action : dict
        Action dict (must include ``action_id``, typically has ``page_id``,
        ``page_url``, ``page_title``, ``reason``, ``action_type``).
    before_content : str
        Content before the proposed change.
    after_content : str
        Content after the proposed change.
    page_info : dict, optional
        Additional page metadata.

    Returns
    -------
    dict
        A dict matching the :class:`DiffPreview` schema.
    """
    action_id = action.get("action_id", "unknown")
    page_id = action.get("page_id", action.get("target", "unknown"))
    page_url = action.get("page_url") or (page_info or {}).get("url")
    page_title = action.get("page_title") or (page_info or {}).get("title")
    change_type = _infer_change_type(action)

    # Diffs
    diff_text = _generate_diff_text(before_content, after_content)
    diff_html = _generate_diff_html(before_content, after_content)
    counts = _count_diff_lines(before_content, after_content)

    # Summary
    change_summary = _build_change_summary(
        action,
        change_type,
        counts["lines_added"],
        counts["lines_removed"],
        counts["lines_modified"],
    )

    # Construct partial preview for risk assessment input
    preview_for_risk: Dict[str, Any] = {
        "before_content": before_content,
        "after_content": after_content,
        "change_type": change_type,
        "page_id": page_id,
    }
    risk_assessment = assess_risk(preview_for_risk, page_info)

    preview = DiffPreview(
        action_id=action_id,
        page_id=page_id,
        page_url=page_url,
        page_title=page_title,
        before_content=before_content,
        after_content=after_content,
        diff_html=diff_html,
        diff_text=diff_text,
        change_summary=change_summary,
        change_type=change_type,
        lines_added=counts["lines_added"],
        lines_removed=counts["lines_removed"],
        lines_modified=counts["lines_modified"],
        risk_assessment=risk_assessment,
    )

    return preview.model_dump()


# ---------------------------------------------------------------------------
# Public API: auto-approval evaluation
# ---------------------------------------------------------------------------


def evaluate_auto_approval(
    approval_request: Dict[str, Any],
    auto_approve_settings: Dict[str, Any],
) -> Dict[str, Any]:
    """Determine whether an approval request can be auto-approved.

    Checks five rules in order.  If all pass the request is marked eligible;
    if any fail the blocking rule is recorded.

    Parameters
    ----------
    approval_request : dict
        An :class:`ApprovalRequest`-shaped dict.
    auto_approve_settings : dict
        Operator-configured auto-approval rules.

    Returns
    -------
    dict
        Updated *approval_request* dict with ``auto_approve_eligible`` and
        ``auto_approve_reason`` populated.
    """
    result = dict(approval_request)
    settings = {**DEFAULT_AUTO_APPROVE_SETTINGS, **auto_approve_settings}

    # Rule 1: master switch
    if not settings.get("enabled", False):
        result["auto_approve_eligible"] = False
        result["auto_approve_reason"] = "Auto-approval is disabled"
        return result

    # Extract fields from the embedded diff preview or the request itself
    diff_preview = result.get("diff_preview") or {}
    risk_assessment = diff_preview.get("risk_assessment", {})
    risk_tier = result.get("risk_tier", risk_assessment.get("risk_tier", "medium"))
    change_type = diff_preview.get("change_type", "copy_update")
    page_id = diff_preview.get("page_id", "")
    word_count_change = abs(risk_assessment.get("word_count_change", 0))

    # Rule 2: risk tier ceiling
    max_tier = settings.get("max_risk_tier", "low")
    if _RISK_TIER_ORDER.get(risk_tier, 99) > _RISK_TIER_ORDER.get(max_tier, 1):
        result["auto_approve_eligible"] = False
        result["auto_approve_reason"] = (
            f"Risk tier '{risk_tier}' exceeds maximum auto-approve tier '{max_tier}'"
        )
        return result

    # Rule 3: allowed change types
    allowed_types = settings.get("allowed_change_types", [])
    if change_type not in allowed_types:
        result["auto_approve_eligible"] = False
        result["auto_approve_reason"] = (
            f"Change type '{change_type}' is not in allowed types: {allowed_types}"
        )
        return result

    # Rule 4: blocked pages
    blocked_pages = settings.get("blocked_pages", [])
    if page_id in blocked_pages or page_id.strip("/").lower() in [
        p.strip("/").lower() for p in blocked_pages
    ]:
        result["auto_approve_eligible"] = False
        result["auto_approve_reason"] = (
            f"Page '{page_id}' is in the blocked pages list"
        )
        return result

    # Rule 5: word count ceiling
    max_wc = settings.get("max_word_count_change", 50)
    if word_count_change > max_wc:
        result["auto_approve_eligible"] = False
        result["auto_approve_reason"] = (
            f"Word count change ({word_count_change}) exceeds maximum ({max_wc})"
        )
        return result

    # All rules passed
    satisfied: List[str] = [
        f"risk tier '{risk_tier}' <= '{max_tier}'",
        f"change type '{change_type}' is allowed",
        "page is not blocked",
        f"word count change ({word_count_change}) <= {max_wc}",
    ]
    result["auto_approve_eligible"] = True
    result["auto_approve_reason"] = "All rules satisfied: " + "; ".join(satisfied)
    return result


# ---------------------------------------------------------------------------
# Public API: approval request lifecycle
# ---------------------------------------------------------------------------


def create_approval_request(
    action: Dict[str, Any],
    diff_preview: Dict[str, Any],
    auto_approve_settings: Optional[Dict[str, Any]] = None,
    expiry_hours: int = 72,
) -> Dict[str, Any]:
    """Create an :class:`ApprovalRequest` from an action and its diff preview.

    If *auto_approve_settings* is provided and the change qualifies, the
    request is immediately set to ``auto_approved``.  Otherwise it stays
    ``pending`` with an expiry timestamp.

    Parameters
    ----------
    action : dict
        The website action dict.
    diff_preview : dict
        A :class:`DiffPreview`-shaped dict (as returned by
        :func:`generate_diff_preview`).
    auto_approve_settings : dict, optional
        Operator auto-approval configuration.  When ``None``, uses
        :data:`DEFAULT_AUTO_APPROVE_SETTINGS`.
    expiry_hours : int
        Hours before a pending request expires.  Default 72.

    Returns
    -------
    dict
        An :class:`ApprovalRequest`-shaped dict.
    """
    now = _utc_now()
    risk_assessment = diff_preview.get("risk_assessment", {})
    risk_tier = risk_assessment.get("risk_tier", "medium")

    request = ApprovalRequest(
        action_id=action.get("action_id", "unknown"),
        diff_preview_id=diff_preview.get("id", "unknown"),
        diff_preview=diff_preview,
        risk_tier=risk_tier,
        created_at=now,
    )

    req_dict = request.model_dump()

    # Evaluate auto-approval
    effective_settings = auto_approve_settings if auto_approve_settings is not None else DEFAULT_AUTO_APPROVE_SETTINGS
    req_dict = evaluate_auto_approval(req_dict, effective_settings)

    if req_dict["auto_approve_eligible"]:
        req_dict["status"] = ApprovalStatus.auto_approved.value
        req_dict["approved_by"] = "system"
        req_dict["decided_at"] = now
    else:
        req_dict["status"] = ApprovalStatus.pending.value
        expires_at = datetime.now(timezone.utc) + timedelta(hours=expiry_hours)
        req_dict["expires_at"] = expires_at.isoformat()

    return req_dict


def approve_request(
    request: Dict[str, Any],
    approved_by: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Mark a pending approval request as approved.

    Parameters
    ----------
    request : dict
        An :class:`ApprovalRequest`-shaped dict.
    approved_by : str
        Identifier of the operator who approved.
    notes : str, optional
        Optional approval notes.

    Returns
    -------
    dict
        Updated request dict with ``status`` set to ``approved``.

    Raises
    ------
    ValueError
        If the request is not in ``pending`` status.
    """
    current_status = request.get("status", "")
    if current_status != ApprovalStatus.pending.value:
        raise ValueError(
            f"Cannot approve request in status '{current_status}'. "
            f"Request must be in 'pending' status."
        )

    result = dict(request)
    result["status"] = ApprovalStatus.approved.value
    result["approved_by"] = approved_by
    result["operator_notes"] = notes
    result["decided_at"] = _utc_now()
    return result


def reject_request(
    request: Dict[str, Any],
    rejected_by: str,
    notes: str,
) -> Dict[str, Any]:
    """Mark a pending approval request as rejected.

    Parameters
    ----------
    request : dict
        An :class:`ApprovalRequest`-shaped dict.
    rejected_by : str
        Identifier of the operator who rejected.
    notes : str
        Required explanation for the rejection.

    Returns
    -------
    dict
        Updated request dict with ``status`` set to ``rejected``.

    Raises
    ------
    ValueError
        If the request is not in ``pending`` status.
    ValueError
        If *notes* is empty.
    """
    if not notes or not notes.strip():
        raise ValueError("Rejection notes are required. Cannot reject without explanation.")

    current_status = request.get("status", "")
    if current_status != ApprovalStatus.pending.value:
        raise ValueError(
            f"Cannot reject request in status '{current_status}'. "
            f"Request must be in 'pending' status."
        )

    result = dict(request)
    result["status"] = ApprovalStatus.rejected.value
    result["approved_by"] = rejected_by
    result["operator_notes"] = notes
    result["decided_at"] = _utc_now()
    return result


def request_revision(
    request: Dict[str, Any],
    revision_instructions: str,
) -> Dict[str, Any]:
    """Mark a pending approval request as needing revision.

    Parameters
    ----------
    request : dict
        An :class:`ApprovalRequest`-shaped dict.
    revision_instructions : str
        What the operator wants changed before re-approval.

    Returns
    -------
    dict
        Updated request dict with ``status`` set to ``revision_requested``.

    Raises
    ------
    ValueError
        If the request is not in ``pending`` status.
    ValueError
        If *revision_instructions* is empty.
    """
    if not revision_instructions or not revision_instructions.strip():
        raise ValueError("Revision instructions are required.")

    current_status = request.get("status", "")
    if current_status != ApprovalStatus.pending.value:
        raise ValueError(
            f"Cannot request revision for request in status '{current_status}'. "
            f"Request must be in 'pending' status."
        )

    result = dict(request)
    result["status"] = ApprovalStatus.revision_requested.value
    result["revision_instructions"] = revision_instructions
    result["decided_at"] = _utc_now()
    return result


def process_revision(
    request: Dict[str, Any],
    revised_action: Dict[str, Any],
    revised_before: str,
    revised_after: str,
) -> Dict[str, Any]:
    """Process a revision by generating a new diff preview and approval request.

    After an operator requests changes and the system revises the action,
    this function creates a fresh :class:`DiffPreview` and a new
    :class:`ApprovalRequest` linked to the original via metadata.

    Parameters
    ----------
    request : dict
        The original :class:`ApprovalRequest`-shaped dict (should have
        ``status == 'revision_requested'``).
    revised_action : dict
        The revised action dict.
    revised_before : str
        Content before the revised change.
    revised_after : str
        Content after the revised change.

    Returns
    -------
    dict
        A new :class:`ApprovalRequest`-shaped dict linked to the original.
    """
    original_id = request.get("id", "unknown")
    page_info_from_preview = request.get("diff_preview") or {}

    # Carry forward page_info if available
    page_info: Optional[Dict[str, Any]] = None
    if page_info_from_preview.get("page_url") or page_info_from_preview.get("page_title"):
        page_info = {
            "url": page_info_from_preview.get("page_url"),
            "title": page_info_from_preview.get("page_title"),
        }

    new_diff = generate_diff_preview(
        revised_action,
        revised_before,
        revised_after,
        page_info=page_info,
    )

    # Create a new approval request (always pending for revisions -- no auto-approve)
    now = _utc_now()
    new_request = ApprovalRequest(
        action_id=revised_action.get("action_id", "unknown"),
        diff_preview_id=new_diff.get("id", "unknown"),
        diff_preview=new_diff,
        risk_tier=new_diff.get("risk_assessment", {}).get("risk_tier", "medium"),
        created_at=now,
        metadata={
            "revision_of": original_id,
            "original_revision_instructions": request.get("revision_instructions", ""),
        },
    )

    req_dict = new_request.model_dump()
    req_dict["status"] = ApprovalStatus.pending.value
    expires_at = datetime.now(timezone.utc) + timedelta(hours=72)
    req_dict["expires_at"] = expires_at.isoformat()

    return req_dict


# ---------------------------------------------------------------------------
# Public API: filtering and expiry
# ---------------------------------------------------------------------------


def get_pending_approvals(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Filter and sort pending approval requests.

    Returns only requests with ``status == 'pending'``, sorted by risk tier
    (highest risk first) then by ``created_at`` (oldest first).

    Parameters
    ----------
    requests : list of dict
        Collection of :class:`ApprovalRequest`-shaped dicts.

    Returns
    -------
    list of dict
        Filtered and sorted pending requests.
    """
    pending = [r for r in requests if r.get("status") == ApprovalStatus.pending.value]

    def sort_key(req: Dict[str, Any]) -> tuple:
        # Negate risk tier so highest risk sorts first
        tier_rank = -_RISK_TIER_ORDER.get(req.get("risk_tier", "medium"), 2)
        created = req.get("created_at", "")
        return (tier_rank, created)

    pending.sort(key=sort_key)
    return pending


def check_expired(requests: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Mark pending requests past their ``expires_at`` as expired.

    Mutates the input dicts in-place for any newly-expired requests and
    returns only those that were just marked expired.

    Parameters
    ----------
    requests : list of dict
        Collection of :class:`ApprovalRequest`-shaped dicts.

    Returns
    -------
    list of dict
        Requests that were just transitioned to ``expired`` status.
    """
    now = datetime.now(timezone.utc)
    newly_expired: List[Dict[str, Any]] = []

    for req in requests:
        if req.get("status") != ApprovalStatus.pending.value:
            continue

        expires_at_str = req.get("expires_at")
        if not expires_at_str:
            continue

        try:
            expires_at = datetime.fromisoformat(expires_at_str)
            # Ensure timezone-aware comparison
            if expires_at.tzinfo is None:
                expires_at = expires_at.replace(tzinfo=timezone.utc)
            if now >= expires_at:
                req["status"] = ApprovalStatus.expired.value
                req["decided_at"] = _utc_now()
                newly_expired.append(req)
        except (ValueError, TypeError):
            # Malformed timestamp -- skip
            continue

    return newly_expired
