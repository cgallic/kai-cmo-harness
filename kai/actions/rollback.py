"""Rollback support and page health monitoring for the Kai action system.

Provides change tracking with before/after snapshots, one-click rollback
of any website mutation, and structural health checks that verify page
integrity after modifications.

Models:
    ChangeRecord -- tracks a single page mutation with before/after state
    PageHealthCheck -- structured result of health verification checks

Functions:
    create_snapshot -- capture full page state from a CMS connector
    record_change -- create a ChangeRecord dict from mutation data
    rollback_change -- restore a page to its pre-change state
    can_rollback -- check whether a rollback is still possible
    define_health_checks -- build check definitions for a page
    run_health_checks -- evaluate all checks against page content
    get_page_history -- filter and sort change records for a page
    compare_snapshots -- diff two page snapshots
"""

from __future__ import annotations

import hashlib
import json
import re
import uuid
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from .website import parse_page_sections


# ---------------------------------------------------------------------------
# Pydantic fallback (same pattern as gateway/models.py)
# ---------------------------------------------------------------------------

try:
    from pydantic import BaseModel as _PydanticBase, Field as _PydanticField

    BaseModel = _PydanticBase
    Field = _PydanticField
except ImportError:  # pragma: no cover
    import copy as _copy

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
                    value = _copy.deepcopy(getattr(self.__class__, name))
                    if value is Ellipsis:
                        raise TypeError(f"Missing required field: {name}")
                else:
                    raise TypeError(f"Missing required field: {name}")
                setattr(self, name, value)
            for key, value in data.items():
                setattr(self, key, value)

        def model_dump(self) -> Dict[str, Any]:
            return {k: v for k, v in self.__dict__.items() if not k.startswith("_")}

        def __repr__(self) -> str:
            return f"{self.__class__.__name__}({self.model_dump()!r})"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _utc_now() -> str:
    """Return the current UTC time as an ISO-8601 string."""
    return datetime.now(timezone.utc).isoformat()


def _generate_id(prefix: str) -> str:
    """Generate a unique identifier with the given prefix."""
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def _content_hash(content: str) -> str:
    """Compute a SHA-256 hash of the given content."""
    return hashlib.sha256(content.encode("utf-8", errors="replace")).hexdigest()


def _strip_html_tags(html: str) -> str:
    """Remove HTML tags and return plain text."""
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _count_words(text: str) -> int:
    """Count words in a string after stripping HTML."""
    plain = _strip_html_tags(text)
    if not plain:
        return 0
    return len(plain.split())


# ---------------------------------------------------------------------------
# ChangeRecord model
# ---------------------------------------------------------------------------

class ChangeRecord(BaseModel):
    """Tracks a single page mutation with before/after state snapshots."""

    id: str = Field(default_factory=lambda: _generate_id("chg"))
    action_id: str = ""
    action_type: str = ""
    page_id: str = ""
    page_url: Optional[str] = None
    page_title: Optional[str] = None
    before_state: Dict[str, Any] = Field(default_factory=dict)
    after_state: Dict[str, Any] = Field(default_factory=dict)
    change_summary: str = ""
    timestamp: str = Field(default_factory=_utc_now)
    operator: Optional[str] = None
    rollback_available: bool = True
    rollback_performed: bool = False
    rollback_timestamp: Optional[str] = None
    rollback_result: Optional[Dict[str, Any]] = None
    health_check_result: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# PageHealthCheck model
# ---------------------------------------------------------------------------

class PageHealthCheck(BaseModel):
    """Structured result of health verification checks on a page."""

    id: str = Field(default_factory=lambda: _generate_id("phc"))
    page_id: str = ""
    page_url: Optional[str] = None
    check_results: List[Dict[str, Any]] = Field(default_factory=list)
    overall_healthy: bool = True
    critical_failures: int = 0
    warnings: int = 0
    timestamp: str = Field(default_factory=_utc_now)
    metadata: Dict[str, Any] = Field(default_factory=dict)


# ---------------------------------------------------------------------------
# Snapshot functions
# ---------------------------------------------------------------------------

def create_snapshot(connector: Any, page_id: str) -> Dict[str, Any]:
    """Capture the full state of a page via its CMS connector.

    Calls ``connector.get_page(page_id)`` and ``connector.get_metadata(page_id)``
    to assemble a complete snapshot including parsed sections and a content hash.

    Parameters
    ----------
    connector:
        A CMS connector instance with ``get_page`` and ``get_metadata`` methods.
    page_id:
        The identifier of the page to snapshot.

    Returns
    -------
    dict
        Snapshot dict with keys: ``content_html``, ``metadata``, ``sections``,
        ``snapshot_hash``.  On error, returns an error snapshot with
        ``error`` key and empty fields.
    """
    try:
        page_data = connector.get_page(page_id)
    except Exception as exc:
        return {
            "content_html": "",
            "metadata": {},
            "sections": [],
            "snapshot_hash": "",
            "error": f"Failed to get page: {exc}",
        }

    content_html = ""
    if isinstance(page_data, dict):
        content_html = page_data.get("content", page_data.get("html", ""))
    elif isinstance(page_data, str):
        content_html = page_data

    try:
        metadata = connector.get_metadata(page_id)
    except Exception:
        metadata = {}
    if not isinstance(metadata, dict):
        metadata = {}

    try:
        sections = parse_page_sections(content_html) if content_html else []
    except Exception:
        sections = []

    snapshot_hash = _content_hash(content_html) if content_html else ""

    return {
        "content_html": content_html,
        "metadata": metadata,
        "sections": sections,
        "snapshot_hash": snapshot_hash,
    }


# ---------------------------------------------------------------------------
# Change recording
# ---------------------------------------------------------------------------

def record_change(
    action_id: str,
    action_type: str,
    page_id: str,
    before_snapshot: Dict[str, Any],
    after_snapshot: Dict[str, Any],
    change_summary: str,
    operator: Optional[str] = None,
) -> Dict[str, Any]:
    """Create a ChangeRecord dict from the provided mutation data.

    Parameters
    ----------
    action_id:
        The unique identifier of the Action that made this change.
    action_type:
        Class name of the action (e.g. ``UpdatePageCopy``).
    page_id:
        Identifier of the page that was changed.
    before_snapshot:
        Full page state captured before the change.
    after_snapshot:
        Full page state captured after the change.
    change_summary:
        Human-readable description of the change.
    operator:
        Who approved this change, or ``None`` for system-auto.

    Returns
    -------
    dict
        A complete ChangeRecord serialised as a dict.
    """
    # Determine whether rollback is feasible
    before_content = before_snapshot.get("content_html", "")
    rollback_available = bool(before_content and before_content.strip())

    record = ChangeRecord(
        id=_generate_id("chg"),
        action_id=action_id,
        action_type=action_type,
        page_id=page_id,
        page_url=before_snapshot.get("metadata", {}).get("url")
            or after_snapshot.get("metadata", {}).get("url"),
        page_title=before_snapshot.get("metadata", {}).get("title")
            or after_snapshot.get("metadata", {}).get("title"),
        before_state=before_snapshot,
        after_state=after_snapshot,
        change_summary=change_summary,
        timestamp=_utc_now(),
        operator=operator or "system",
        rollback_available=rollback_available,
        rollback_performed=False,
        rollback_timestamp=None,
        rollback_result=None,
        health_check_result=None,
        metadata={},
    )

    if hasattr(record, "model_dump"):
        return record.model_dump()
    return record.__dict__.copy()


# ---------------------------------------------------------------------------
# Rollback
# ---------------------------------------------------------------------------

def can_rollback(
    change_record: Dict[str, Any],
    max_age_days: int = 30,
) -> Dict[str, Any]:
    """Check whether a rollback is possible for the given change record.

    Parameters
    ----------
    change_record:
        Serialised ChangeRecord dict.
    max_age_days:
        Maximum age in days before a rollback expires. Defaults to 30.

    Returns
    -------
    dict
        ``{"can_rollback": bool, "reason": str}``
    """
    if not change_record.get("rollback_available", False):
        return {"can_rollback": False, "reason": "Rollback is not available for this change (no valid before state)."}

    if change_record.get("rollback_performed", False):
        return {"can_rollback": False, "reason": "This change has already been rolled back."}

    before_state = change_record.get("before_state", {})
    before_content = before_state.get("content_html", "")
    if not before_content or not before_content.strip():
        return {"can_rollback": False, "reason": "Before state has no valid content to restore."}

    # Check age
    timestamp_str = change_record.get("timestamp", "")
    if timestamp_str:
        try:
            change_time = datetime.fromisoformat(timestamp_str)
            if change_time.tzinfo is None:
                change_time = change_time.replace(tzinfo=timezone.utc)
            age = datetime.now(timezone.utc) - change_time
            if age > timedelta(days=max_age_days):
                return {
                    "can_rollback": False,
                    "reason": f"Change is {age.days} days old, exceeding the {max_age_days}-day rollback window.",
                }
        except (ValueError, TypeError):
            # If we cannot parse the timestamp, allow rollback but warn
            pass

    return {"can_rollback": True, "reason": "Rollback is available."}


def rollback_change(
    change_record: Dict[str, Any],
    connector: Any,
) -> Dict[str, Any]:
    """Restore the page to its state before the recorded change.

    Steps:
        1. Verify rollback is possible via :func:`can_rollback`.
        2. Capture the current page state as an intermediate snapshot.
        3. Restore the before_state content and metadata via the connector.
        4. Verify the restoration by capturing another snapshot and comparing.
        5. Update and return the change record with rollback details.

    Parameters
    ----------
    change_record:
        Serialised ChangeRecord dict to roll back.
    connector:
        CMS connector instance.

    Returns
    -------
    dict
        Updated ChangeRecord dict with ``rollback_performed``,
        ``rollback_timestamp``, and ``rollback_result`` populated.
    """
    check = can_rollback(change_record)
    if not check["can_rollback"]:
        change_record["rollback_result"] = {
            "success": False,
            "restored_content_match": False,
            "restored_metadata_match": False,
            "warnings": [check["reason"]],
            "intermediate_state": {},
        }
        return change_record

    page_id = change_record.get("page_id", "")
    before_state = change_record.get("before_state", {})
    warnings: List[str] = []

    # Step 2 -- capture intermediate state (current page before we overwrite)
    intermediate_state: Dict[str, Any] = {}
    try:
        intermediate_state = create_snapshot(connector, page_id)
    except Exception as exc:
        warnings.append(f"Could not capture intermediate snapshot: {exc}")

    # Step 3 -- restore content
    before_content = before_state.get("content_html", "")
    try:
        # Attempt section-level restore first, then fall back to full page
        sections = before_state.get("sections", [])
        if sections:
            for section in sections:
                section_id = section.get("section_id", "")
                section_content = section.get("content", "")
                if section_id and section_content:
                    connector.update_page_section(
                        page_id, section_id, section_content,
                        content_type="html",
                    )
        else:
            # Fall back to updating the full page as a single section
            connector.update_page_section(
                page_id, "main", before_content,
                content_type="html",
            )
    except Exception as exc:
        warnings.append(f"Error restoring content: {exc}")

    # Step 3b -- restore metadata
    before_metadata = before_state.get("metadata", {})
    if before_metadata:
        try:
            connector.update_metadata(page_id, before_metadata)
        except Exception as exc:
            warnings.append(f"Error restoring metadata: {exc}")

    # Step 4 -- verify restoration
    restored_content_match = False
    restored_metadata_match = False
    try:
        verify_snapshot = create_snapshot(connector, page_id)
        before_hash = before_state.get("snapshot_hash", "")
        verify_hash = verify_snapshot.get("snapshot_hash", "")
        restored_content_match = bool(before_hash and before_hash == verify_hash)

        # Compare metadata keys
        verify_meta = verify_snapshot.get("metadata", {})
        if before_metadata and verify_meta:
            meta_keys_match = all(
                verify_meta.get(k) == v
                for k, v in before_metadata.items()
                if k not in ("last_modified", "updated_at", "modified_date")
            )
            restored_metadata_match = meta_keys_match
        elif not before_metadata:
            restored_metadata_match = True
    except Exception as exc:
        warnings.append(f"Error verifying restoration: {exc}")

    if not restored_content_match:
        warnings.append("Restored content hash does not match before_state hash. Manual verification recommended.")

    # Step 5 -- update change record
    rollback_result = {
        "success": True,
        "restored_content_match": restored_content_match,
        "restored_metadata_match": restored_metadata_match,
        "warnings": warnings,
        "intermediate_state": intermediate_state,
    }

    change_record["rollback_performed"] = True
    change_record["rollback_timestamp"] = _utc_now()
    change_record["rollback_result"] = rollback_result

    return change_record


# ---------------------------------------------------------------------------
# Page history and snapshot comparison
# ---------------------------------------------------------------------------

def get_page_history(
    page_id: str,
    change_records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Filter and sort change records for a specific page.

    Parameters
    ----------
    page_id:
        Identifier of the page to retrieve history for.
    change_records:
        Full list of serialised ChangeRecord dicts.

    Returns
    -------
    list of dict
        Records for *page_id* sorted by timestamp descending (newest first).
    """
    filtered = [r for r in change_records if r.get("page_id") == page_id]
    filtered.sort(key=lambda r: r.get("timestamp", ""), reverse=True)
    return filtered


def compare_snapshots(
    snapshot_a: Dict[str, Any],
    snapshot_b: Dict[str, Any],
) -> Dict[str, Any]:
    """Compare two page snapshots and report differences.

    Parameters
    ----------
    snapshot_a:
        First snapshot dict (typically the earlier state).
    snapshot_b:
        Second snapshot dict (typically the later state).

    Returns
    -------
    dict
        ``{"identical": bool, "content_changed": bool, "metadata_changed": bool,
        "sections_changed": bool, "details": list[str]}``
    """
    details: List[str] = []

    hash_a = snapshot_a.get("snapshot_hash", "")
    hash_b = snapshot_b.get("snapshot_hash", "")
    content_changed = hash_a != hash_b
    if content_changed:
        details.append("Content HTML has changed (hash mismatch).")

    meta_a = snapshot_a.get("metadata", {})
    meta_b = snapshot_b.get("metadata", {})
    metadata_changed = meta_a != meta_b
    if metadata_changed:
        changed_keys = set()
        all_keys = set(meta_a.keys()) | set(meta_b.keys())
        for k in all_keys:
            if meta_a.get(k) != meta_b.get(k):
                changed_keys.add(k)
        if changed_keys:
            details.append(f"Metadata fields changed: {', '.join(sorted(changed_keys))}.")

    sections_a = snapshot_a.get("sections", [])
    sections_b = snapshot_b.get("sections", [])
    sections_changed = len(sections_a) != len(sections_b)
    if sections_changed:
        details.append(
            f"Section count changed from {len(sections_a)} to {len(sections_b)}."
        )
    elif sections_a and sections_b:
        # Compare section IDs and types
        ids_a = [s.get("section_id") for s in sections_a]
        ids_b = [s.get("section_id") for s in sections_b]
        if ids_a != ids_b:
            sections_changed = True
            details.append("Section IDs or ordering has changed.")
        else:
            for sa, sb in zip(sections_a, sections_b):
                if sa.get("content") != sb.get("content"):
                    sections_changed = True
                    details.append(
                        f"Section '{sa.get('section_id', 'unknown')}' content has changed."
                    )

    identical = not content_changed and not metadata_changed and not sections_changed

    if identical:
        details.append("Snapshots are identical.")

    return {
        "identical": identical,
        "content_changed": content_changed,
        "metadata_changed": metadata_changed,
        "sections_changed": sections_changed,
        "details": details,
    }


# ===================================================================
# Page Health Checks
# ===================================================================


# ---------------------------------------------------------------------------
# Individual check implementations
# ---------------------------------------------------------------------------

def _check_title_present(content: str) -> Dict[str, Any]:
    """Check that the page has a non-empty <title> tag."""
    match = re.search(r"<title[^>]*>\s*(.+?)\s*</title>", content, re.IGNORECASE | re.DOTALL)
    if match and match.group(1).strip():
        return {
            "check_name": "title_present",
            "passed": True,
            "details": f"Title found: '{match.group(1).strip()[:80]}'",
            "severity": "critical",
        }
    return {
        "check_name": "title_present",
        "passed": False,
        "details": "No <title> tag with content found.",
        "severity": "critical",
    }


def _check_meta_description(metadata: Dict[str, Any], content: str) -> Dict[str, Any]:
    """Check that the page has a meta description."""
    # Check metadata dict first
    desc = metadata.get("description", metadata.get("meta_description", ""))
    if desc and str(desc).strip():
        return {
            "check_name": "meta_description_present",
            "passed": True,
            "details": f"Meta description found ({len(str(desc).strip())} chars): '{str(desc).strip()[:80]}...'",
            "severity": "warning",
        }

    # Fall back to parsing the content
    match = re.search(
        r'<meta\s+[^>]*name\s*=\s*["\']description["\']\s+[^>]*content\s*=\s*["\']([^"\']+)["\']',
        content,
        re.IGNORECASE,
    )
    if not match:
        # Try reversed attribute order
        match = re.search(
            r'<meta\s+[^>]*content\s*=\s*["\']([^"\']+)["\']\s+[^>]*name\s*=\s*["\']description["\']',
            content,
            re.IGNORECASE,
        )

    if match and match.group(1).strip():
        desc_text = match.group(1).strip()
        return {
            "check_name": "meta_description_present",
            "passed": True,
            "details": f"Meta description found ({len(desc_text)} chars): '{desc_text[:80]}...'",
            "severity": "warning",
        }

    return {
        "check_name": "meta_description_present",
        "passed": False,
        "details": "No meta description found in metadata or page content.",
        "severity": "warning",
    }


def _check_h1_count(content: str) -> Dict[str, Any]:
    """Check that the page has exactly one <h1> tag."""
    h1_matches = re.findall(r"<h1[^>]*>", content, re.IGNORECASE)
    count = len(h1_matches)
    if count == 1:
        return {
            "check_name": "h1_present",
            "passed": True,
            "details": "Exactly one <h1> tag found.",
            "severity": "warning",
        }
    elif count == 0:
        return {
            "check_name": "h1_present",
            "passed": False,
            "details": "No <h1> tag found. Every page should have exactly one.",
            "severity": "warning",
        }
    else:
        return {
            "check_name": "h1_present",
            "passed": False,
            "details": f"Found {count} <h1> tags. Pages should have exactly one.",
            "severity": "warning",
        }


def _check_broken_images(content: str) -> Dict[str, Any]:
    """Check that all <img> tags have non-empty src attributes."""
    img_tags = re.findall(r"<img[^>]*>", content, re.IGNORECASE)
    if not img_tags:
        return {
            "check_name": "no_broken_images",
            "passed": True,
            "details": "No <img> tags found on the page.",
            "severity": "critical",
        }

    broken = 0
    for tag in img_tags:
        src_match = re.search(r'src\s*=\s*["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if not src_match or not src_match.group(1).strip():
            broken += 1

    if broken == 0:
        return {
            "check_name": "no_broken_images",
            "passed": True,
            "details": f"All {len(img_tags)} image(s) have valid src attributes.",
            "severity": "critical",
        }
    return {
        "check_name": "no_broken_images",
        "passed": False,
        "details": f"{broken} of {len(img_tags)} image(s) have empty or missing src attributes.",
        "severity": "critical",
    }


def _check_empty_links(content: str) -> Dict[str, Any]:
    """Check that all <a> tags have non-empty href attributes."""
    a_tags = re.findall(r"<a[^>]*>", content, re.IGNORECASE)
    if not a_tags:
        return {
            "check_name": "no_empty_links",
            "passed": True,
            "details": "No <a> tags found on the page.",
            "severity": "warning",
        }

    empty = 0
    for tag in a_tags:
        href_match = re.search(r'href\s*=\s*["\']([^"\']*)["\']', tag, re.IGNORECASE)
        if not href_match:
            empty += 1
            continue
        href_val = href_match.group(1).strip()
        # Allow "#" only if it looks like an anchor reference (e.g. "#section-id")
        if not href_val or href_val == "#":
            empty += 1

    if empty == 0:
        return {
            "check_name": "no_empty_links",
            "passed": True,
            "details": f"All {len(a_tags)} link(s) have valid href attributes.",
            "severity": "warning",
        }
    return {
        "check_name": "no_empty_links",
        "passed": False,
        "details": f"{empty} of {len(a_tags)} link(s) have empty or missing href attributes.",
        "severity": "warning",
    }


def _check_phone_number(content: str) -> Dict[str, Any]:
    """Check that the page contains at least one phone number (US formats)."""
    # Patterns: (xxx) xxx-xxxx, xxx-xxx-xxxx, xxx.xxx.xxxx, +1xxxxxxxxxx, 1-xxx-xxx-xxxx
    phone_patterns = [
        r"\(\d{3}\)\s*\d{3}[-.\s]?\d{4}",
        r"\d{3}[-.\s]\d{3}[-.\s]\d{4}",
        r"\+?1[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}",
    ]
    found_numbers: List[str] = []
    for pattern in phone_patterns:
        matches = re.findall(pattern, content)
        found_numbers.extend(matches)

    # Deduplicate
    unique_numbers = list(dict.fromkeys(found_numbers))

    if unique_numbers:
        return {
            "check_name": "phone_number_present",
            "passed": True,
            "details": f"Found {len(unique_numbers)} phone number(s): {', '.join(unique_numbers[:3])}",
            "severity": "warning",
        }
    return {
        "check_name": "phone_number_present",
        "passed": False,
        "details": "No phone number found on the page.",
        "severity": "warning",
    }


def _check_cta_present(content: str) -> Dict[str, Any]:
    """Check that the page has at least one CTA element."""
    cta_count = 0

    # <button> tags
    buttons = re.findall(r"<button[^>]*>", content, re.IGNORECASE)
    cta_count += len(buttons)

    # <a> with CTA-like classes
    cta_links = re.findall(
        r'<a[^>]*class\s*=\s*["\'][^"\']*(?:cta|btn|button)[^"\']*["\'][^>]*>',
        content,
        re.IGNORECASE,
    )
    cta_count += len(cta_links)

    # <input type="submit">
    submits = re.findall(r'<input[^>]*type\s*=\s*["\']submit["\'][^>]*>', content, re.IGNORECASE)
    cta_count += len(submits)

    if cta_count > 0:
        return {
            "check_name": "cta_present",
            "passed": True,
            "details": f"Found {cta_count} CTA element(s) (buttons, CTA links, submit inputs).",
            "severity": "warning",
        }
    return {
        "check_name": "cta_present",
        "passed": False,
        "details": "No CTA elements found (no buttons, CTA links, or submit inputs).",
        "severity": "warning",
    }


def _check_placeholder_content(content: str) -> Dict[str, Any]:
    """Check that the page does not contain placeholder text."""
    placeholder_patterns = [
        r"lorem\s+ipsum",
        r"dolor\s+sit\s+amet",
        r"\bplaceholder\b",
        r"\bTODO\b",
        r"\bFIXME\b",
        r"\[insert\b",
        r"\[replace\b",
    ]
    found: List[str] = []
    content_lower = content.lower()
    for pattern in placeholder_patterns:
        # Use case-insensitive for Latin phrases, case-sensitive for TODO/FIXME
        if pattern in (r"\bTODO\b", r"\bFIXME\b"):
            matches = re.findall(pattern, content)
        else:
            matches = re.findall(pattern, content_lower)
        if matches:
            found.extend(matches)

    if not found:
        return {
            "check_name": "no_lorem_ipsum",
            "passed": True,
            "details": "No placeholder content detected.",
            "severity": "critical",
        }
    unique = list(dict.fromkeys(found))
    return {
        "check_name": "no_lorem_ipsum",
        "passed": False,
        "details": f"Placeholder content detected: {', '.join(unique[:5])}",
        "severity": "critical",
    }


def _check_script_errors(content: str) -> Dict[str, Any]:
    """Check for obvious script-tag issues (unclosed tags, syntax markers)."""
    issues: List[str] = []

    # Find script tags
    open_scripts = re.findall(r"<script[^>]*>", content, re.IGNORECASE)
    close_scripts = re.findall(r"</script>", content, re.IGNORECASE)
    if len(open_scripts) != len(close_scripts):
        issues.append(
            f"Mismatched <script> tags: {len(open_scripts)} open vs "
            f"{len(close_scripts)} close."
        )

    # Check for common syntax-error markers inside script blocks
    script_blocks = re.findall(
        r"<script[^>]*>(.*?)</script>", content, re.IGNORECASE | re.DOTALL
    )
    for block in script_blocks:
        if "SyntaxError" in block or "Uncaught" in block or "undefined is not" in block:
            issues.append("Script block contains error text (SyntaxError/Uncaught).")
            break

    if not issues:
        return {
            "check_name": "no_console_errors_indicators",
            "passed": True,
            "details": "No obvious script errors detected.",
            "severity": "critical",
        }
    return {
        "check_name": "no_console_errors_indicators",
        "passed": False,
        "details": "; ".join(issues),
        "severity": "critical",
    }


def _check_content_length(content: str) -> Dict[str, Any]:
    """Check that the page body has meaningful content."""
    word_count = _count_words(content)

    if word_count < 50:
        return {
            "check_name": "content_not_empty",
            "passed": False,
            "details": f"Page has only {word_count} words (minimum 50 for a non-empty page).",
            "severity": "critical",
        }
    if word_count < 200:
        return {
            "check_name": "content_not_empty",
            "passed": True,
            "details": f"Page has {word_count} words. Content exists but is thin (< 200 words).",
            "severity": "warning",
        }
    return {
        "check_name": "content_not_empty",
        "passed": True,
        "details": f"Page has {word_count} words.",
        "severity": "critical",
    }


def _check_schema_markup(content: str) -> Dict[str, Any]:
    """Check that JSON-LD schema markup is present and valid."""
    ld_blocks = re.findall(
        r'<script[^>]*type\s*=\s*["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        content,
        re.IGNORECASE | re.DOTALL,
    )

    if not ld_blocks:
        return {
            "check_name": "schema_markup_valid",
            "passed": True,
            "details": "No JSON-LD schema markup found (not required but recommended).",
            "severity": "warning",
        }

    schema_types: List[str] = []
    invalid_blocks = 0
    for block in ld_blocks:
        block = block.strip()
        if not block:
            invalid_blocks += 1
            continue
        try:
            parsed = json.loads(block)
            if isinstance(parsed, dict):
                schema_type = parsed.get("@type", "Unknown")
                schema_types.append(str(schema_type))
            elif isinstance(parsed, list):
                for item in parsed:
                    if isinstance(item, dict):
                        schema_types.append(str(item.get("@type", "Unknown")))
        except (json.JSONDecodeError, ValueError):
            invalid_blocks += 1

    if invalid_blocks > 0:
        return {
            "check_name": "schema_markup_valid",
            "passed": False,
            "details": f"{invalid_blocks} of {len(ld_blocks)} JSON-LD block(s) contain invalid JSON. Types found: {', '.join(schema_types) if schema_types else 'none'}.",
            "severity": "warning",
        }

    return {
        "check_name": "schema_markup_valid",
        "passed": True,
        "details": f"Found {len(ld_blocks)} valid JSON-LD block(s). Schema types: {', '.join(schema_types)}.",
        "severity": "warning",
    }


def _check_canonical_url(content: str) -> Dict[str, Any]:
    """Check that the page has a canonical URL tag."""
    match = re.search(
        r'<link[^>]*rel\s*=\s*["\']canonical["\']\s+[^>]*href\s*=\s*["\']([^"\']+)["\']',
        content,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r'<link[^>]*href\s*=\s*["\']([^"\']+)["\']\s+[^>]*rel\s*=\s*["\']canonical["\']',
            content,
            re.IGNORECASE,
        )

    if match and match.group(1).strip():
        return {
            "check_name": "canonical_url_present",
            "passed": True,
            "details": f"Canonical URL: {match.group(1).strip()}",
            "severity": "info",
        }
    return {
        "check_name": "canonical_url_present",
        "passed": False,
        "details": "No canonical URL tag found.",
        "severity": "info",
    }


# ---------------------------------------------------------------------------
# Page-type-specific checks
# ---------------------------------------------------------------------------

def _checks_for_homepage(content: str) -> List[Dict[str, Any]]:
    """Additional health checks for a homepage."""
    results: List[Dict[str, Any]] = []

    # Hero section
    has_hero = bool(re.search(
        r'(?:<section[^>]*hero|class\s*=\s*["\'][^"\']*hero|<h1[^>]*>)',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "homepage_hero_section",
        "passed": has_hero,
        "details": "Hero section found." if has_hero else "No hero section detected (look for <h1> or hero class).",
        "severity": "warning",
    })

    # Trust signals
    has_trust = bool(re.search(
        r'(?:trust|testimonial|review|rating|certified|guarantee|years)',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "homepage_trust_signals",
        "passed": has_trust,
        "details": "Trust signals found." if has_trust else "No trust signals detected (testimonials, reviews, certifications).",
        "severity": "warning",
    })

    # Service overview
    has_services = bool(re.search(
        r'(?:service|what\s+we\s+do|our\s+work|solutions|offerings)',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "homepage_service_overview",
        "passed": has_services,
        "details": "Service overview section found." if has_services else "No service overview detected.",
        "severity": "warning",
    })

    # Contact info
    has_contact = bool(re.search(
        r'(?:contact|phone|email|call\s+us|get\s+in\s+touch|\(\d{3}\)\s*\d{3})',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "homepage_contact_info",
        "passed": has_contact,
        "details": "Contact information found." if has_contact else "No contact information detected.",
        "severity": "warning",
    })

    return results


def _checks_for_service_page(content: str) -> List[Dict[str, Any]]:
    """Additional health checks for a service page."""
    results: List[Dict[str, Any]] = []

    # Service description (substantial content)
    word_count = _count_words(content)
    has_description = word_count >= 100
    results.append({
        "check_name": "service_description",
        "passed": has_description,
        "details": f"Service description has {word_count} words." if has_description
        else f"Service description is thin ({word_count} words, need 100+).",
        "severity": "warning",
    })

    # CTA
    has_cta = bool(re.search(
        r'(?:<button|class\s*=\s*["\'][^"\']*(?:cta|btn)|type\s*=\s*["\']submit["\']|free\s+(?:quote|estimate|consultation))',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "service_cta",
        "passed": has_cta,
        "details": "CTA element found on service page." if has_cta else "No CTA found on service page.",
        "severity": "warning",
    })

    # Pricing indicators
    has_pricing = bool(re.search(
        r'(?:pric|cost|\$\d|starting\s+at|free\s+estimate|quote|affordable)',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "service_pricing_indicators",
        "passed": has_pricing,
        "details": "Pricing indicators found." if has_pricing else "No pricing indicators detected.",
        "severity": "info",
    })

    # Testimonials
    has_testimonials = bool(re.search(
        r'(?:testimonial|review|customer\s+said|client\s+feedback|"[^"]{20,}")',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "service_testimonials",
        "passed": has_testimonials,
        "details": "Testimonials or reviews found." if has_testimonials else "No testimonials detected on service page.",
        "severity": "info",
    })

    return results


def _checks_for_contact_page(content: str) -> List[Dict[str, Any]]:
    """Additional health checks for a contact page."""
    results: List[Dict[str, Any]] = []

    # Form
    has_form = bool(re.search(r"<form[^>]*>", content, re.IGNORECASE))
    results.append({
        "check_name": "contact_form",
        "passed": has_form,
        "details": "Contact form found." if has_form else "No <form> element detected on contact page.",
        "severity": "warning",
    })

    # Phone number
    phone_result = _check_phone_number(content)
    phone_result["check_name"] = "contact_phone_number"
    phone_result["severity"] = "warning"
    results.append(phone_result)

    # Address
    has_address = bool(re.search(
        r'(?:address|street|suite|ave|blvd|road|drive|city|state|zip|\d{5})',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "contact_address",
        "passed": has_address,
        "details": "Physical address indicators found." if has_address else "No address detected on contact page.",
        "severity": "warning",
    })

    # Map embed
    has_map = bool(re.search(
        r'(?:google\.com/maps|maps\.googleapis|<iframe[^>]*map|mapbox)',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "contact_map_embed",
        "passed": has_map,
        "details": "Map embed found." if has_map else "No map embed detected on contact page.",
        "severity": "info",
    })

    return results


def _checks_for_blog_post(content: str) -> List[Dict[str, Any]]:
    """Additional health checks for a blog post."""
    results: List[Dict[str, Any]] = []

    # Author
    has_author = bool(re.search(
        r'(?:author|written\s+by|posted\s+by|byline|class\s*=\s*["\'][^"\']*author)',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "blog_author",
        "passed": has_author,
        "details": "Author information found." if has_author else "No author attribution detected.",
        "severity": "warning",
    })

    # Date
    has_date = bool(re.search(
        r'(?:date|published|posted\s+on|class\s*=\s*["\'][^"\']*date|\d{4}-\d{2}-\d{2})',
        content, re.IGNORECASE,
    ))
    results.append({
        "check_name": "blog_date",
        "passed": has_date,
        "details": "Publication date found." if has_date else "No publication date detected.",
        "severity": "warning",
    })

    # Content length (blog posts should be > 300 words)
    word_count = _count_words(content)
    sufficient = word_count >= 300
    results.append({
        "check_name": "blog_content_length",
        "passed": sufficient,
        "details": f"Blog post has {word_count} words." if sufficient
        else f"Blog post has only {word_count} words (target 300+).",
        "severity": "warning",
    })

    # Internal links
    internal_link_count = len(re.findall(
        r'<a[^>]*href\s*=\s*["\'](?!/|http)([^"\']+)["\']',
        content, re.IGNORECASE,
    ))
    # Also count relative links starting with /
    internal_link_count += len(re.findall(
        r'<a[^>]*href\s*=\s*["\']\/[^"\']*["\']',
        content, re.IGNORECASE,
    ))
    has_internal = internal_link_count >= 1
    results.append({
        "check_name": "blog_internal_links",
        "passed": has_internal,
        "details": f"Found {internal_link_count} internal link(s)." if has_internal
        else "No internal links found. Blog posts should link to service pages.",
        "severity": "warning",
    })

    return results


# ---------------------------------------------------------------------------
# Main health check functions
# ---------------------------------------------------------------------------

def define_health_checks(
    page_content: str,
    page_metadata: Dict[str, Any],
    page_type: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Define the set of health checks to run on a page.

    Returns check *definitions* (not results).  Each definition describes
    what will be verified and at what severity level.

    Parameters
    ----------
    page_content:
        Raw HTML content of the page.
    page_metadata:
        Metadata dict for the page.
    page_type:
        Optional page type (``homepage``, ``service_page``, ``contact_page``,
        ``blog_post``) to include type-specific checks.

    Returns
    -------
    list of dict
        Check definitions with ``check_name``, ``description``, ``severity``.
    """
    # Universal checks
    checks: List[Dict[str, Any]] = [
        {"check_name": "title_present", "description": "Page has a non-empty <title> tag.", "severity": "critical"},
        {"check_name": "meta_description_present", "description": "Page has a meta description.", "severity": "warning"},
        {"check_name": "h1_present", "description": "Page has exactly one <h1> tag.", "severity": "warning"},
        {"check_name": "no_broken_images", "description": "All <img> tags have non-empty src attributes.", "severity": "critical"},
        {"check_name": "no_empty_links", "description": "All <a> tags have non-empty href attributes.", "severity": "warning"},
        {"check_name": "phone_number_present", "description": "Page contains at least one phone number.", "severity": "warning"},
        {"check_name": "cta_present", "description": "Page has at least one CTA element.", "severity": "warning"},
        {"check_name": "no_lorem_ipsum", "description": "Content has no placeholder text (lorem ipsum, TODO, etc.).", "severity": "critical"},
        {"check_name": "no_console_errors_indicators", "description": "No <script> tags with obvious errors.", "severity": "critical"},
        {"check_name": "content_not_empty", "description": "Page body has meaningful content (> 50 words).", "severity": "critical"},
        {"check_name": "schema_markup_valid", "description": "JSON-LD schema markup is valid JSON (if present).", "severity": "warning"},
        {"check_name": "canonical_url_present", "description": "Page has a canonical URL tag.", "severity": "info"},
    ]

    # Page-type-specific checks
    ptype = (page_type or "").lower().replace("-", "_").replace(" ", "_")

    if ptype == "homepage":
        checks.extend([
            {"check_name": "homepage_hero_section", "description": "Homepage has a hero section with <h1>.", "severity": "warning"},
            {"check_name": "homepage_trust_signals", "description": "Homepage has trust signals (testimonials, reviews).", "severity": "warning"},
            {"check_name": "homepage_service_overview", "description": "Homepage has a services/offerings section.", "severity": "warning"},
            {"check_name": "homepage_contact_info", "description": "Homepage has visible contact information.", "severity": "warning"},
        ])
    elif ptype == "service_page":
        checks.extend([
            {"check_name": "service_description", "description": "Service page has 100+ words of description.", "severity": "warning"},
            {"check_name": "service_cta", "description": "Service page has a clear CTA.", "severity": "warning"},
            {"check_name": "service_pricing_indicators", "description": "Service page has pricing or quote indicators.", "severity": "info"},
            {"check_name": "service_testimonials", "description": "Service page has testimonials or reviews.", "severity": "info"},
        ])
    elif ptype == "contact_page":
        checks.extend([
            {"check_name": "contact_form", "description": "Contact page has a form element.", "severity": "warning"},
            {"check_name": "contact_phone_number", "description": "Contact page displays a phone number.", "severity": "warning"},
            {"check_name": "contact_address", "description": "Contact page shows a physical address.", "severity": "warning"},
            {"check_name": "contact_map_embed", "description": "Contact page has an embedded map.", "severity": "info"},
        ])
    elif ptype == "blog_post":
        checks.extend([
            {"check_name": "blog_author", "description": "Blog post has author attribution.", "severity": "warning"},
            {"check_name": "blog_date", "description": "Blog post has a publication date.", "severity": "warning"},
            {"check_name": "blog_content_length", "description": "Blog post has 300+ words.", "severity": "warning"},
            {"check_name": "blog_internal_links", "description": "Blog post has internal links to service pages.", "severity": "warning"},
        ])

    return checks


def run_health_checks(
    page_content: str,
    page_metadata: Dict[str, Any],
    page_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Run all health checks against page content and return results.

    Evaluates every check defined by :func:`define_health_checks` using
    string and regex parsing (no external HTML parser required).

    Parameters
    ----------
    page_content:
        Raw HTML content of the page.
    page_metadata:
        Metadata dict for the page.
    page_type:
        Optional page type for type-specific checks.

    Returns
    -------
    dict
        A PageHealthCheck serialised as a dict.
    """
    if not page_content:
        page_content = ""
    if not page_metadata:
        page_metadata = {}

    # Run universal checks
    check_results: List[Dict[str, Any]] = [
        _check_title_present(page_content),
        _check_meta_description(page_metadata, page_content),
        _check_h1_count(page_content),
        _check_broken_images(page_content),
        _check_empty_links(page_content),
        _check_phone_number(page_content),
        _check_cta_present(page_content),
        _check_placeholder_content(page_content),
        _check_script_errors(page_content),
        _check_content_length(page_content),
        _check_schema_markup(page_content),
        _check_canonical_url(page_content),
    ]

    # Run page-type-specific checks
    ptype = (page_type or "").lower().replace("-", "_").replace(" ", "_")
    if ptype == "homepage":
        check_results.extend(_checks_for_homepage(page_content))
    elif ptype == "service_page":
        check_results.extend(_checks_for_service_page(page_content))
    elif ptype == "contact_page":
        check_results.extend(_checks_for_contact_page(page_content))
    elif ptype == "blog_post":
        check_results.extend(_checks_for_blog_post(page_content))

    # Compute summary stats
    critical_failures = sum(
        1 for r in check_results
        if not r.get("passed", True) and r.get("severity") == "critical"
    )
    warning_count = sum(
        1 for r in check_results
        if not r.get("passed", True) and r.get("severity") == "warning"
    )
    overall_healthy = critical_failures == 0

    health_check = PageHealthCheck(
        id=_generate_id("phc"),
        page_id="",
        page_url=page_metadata.get("url") or page_metadata.get("canonical_url"),
        check_results=check_results,
        overall_healthy=overall_healthy,
        critical_failures=critical_failures,
        warnings=warning_count,
        timestamp=_utc_now(),
        metadata={
            "page_type": page_type or "unknown",
            "total_checks": len(check_results),
            "passed": sum(1 for r in check_results if r.get("passed", False)),
            "failed": sum(1 for r in check_results if not r.get("passed", True)),
        },
    )

    if hasattr(health_check, "model_dump"):
        return health_check.model_dump()
    return health_check.__dict__.copy()
