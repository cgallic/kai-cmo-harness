"""Concrete website action classes for the Kai action system.

Each class inherits from :class:`Action` and implements the four-phase
lifecycle (validate, preview, execute, verify) for a specific type of
website mutation.

Action classes:
    - UpdatePageCopy — replace text content in a page section
    - UpdatePageSection — replace full HTML of a page section
    - UpdateCTA — change CTA text and/or URL on a page
    - UpdateMetadata — change title, description, schema markup
    - FixTracking — inject or fix analytics/tracking code
    - RefreshApprovedSection — replace section with an approved creative block
    - RestructurePage — reorder sections without changing content
    - AddSection — insert a new section at a specified position

Helper functions:
    - generate_diff — structured diff between two content strings
    - parse_page_sections — parse HTML into logical sections
    - validate_html_safety — check HTML for script injection and unsafe elements
"""

from __future__ import annotations

import difflib
import re
import uuid
from typing import Any, Dict, List, Optional

from .base import Action, ActionLifecycleState, ActionResult


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------


def generate_diff(before: str, after: str) -> Dict[str, Any]:
    """Generate a structured diff between two content strings.

    Uses Python's ``difflib`` to produce a unified-diff style comparison,
    then summarises the changes as add/remove/modify operations.

    Parameters
    ----------
    before : str
        Original content.
    after : str
        New content.

    Returns
    -------
    dict
        ``{"before": str, "after": str, "changes": [...], "summary": str}``
        Each change: ``{"type": "add"|"remove"|"modify", "line": int, "content": str}``
    """
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)

    changes: List[Dict[str, Any]] = []
    added = 0
    removed = 0
    modified = 0

    diff = difflib.unified_diff(before_lines, after_lines, lineterm="")
    line_number = 0

    for entry in diff:
        # Skip diff header lines
        if entry.startswith("---") or entry.startswith("+++"):
            continue
        if entry.startswith("@@"):
            # Parse the hunk header to get the starting line number
            match = re.match(r"^@@ -(\d+)", entry)
            if match:
                line_number = int(match.group(1))
            continue

        content = entry[1:]  # Strip the +/- prefix
        if entry.startswith("+"):
            changes.append({"type": "add", "line": line_number, "content": content})
            added += 1
        elif entry.startswith("-"):
            changes.append({"type": "remove", "line": line_number, "content": content})
            removed += 1
            line_number += 1
        else:
            line_number += 1

    # Count modifications as pairs of adjacent remove+add on the same line
    # For the summary, keep the raw add/remove counts
    parts: List[str] = []
    if removed:
        parts.append(f"removed {removed} line{'s' if removed != 1 else ''}")
    if added:
        parts.append(f"added {added} line{'s' if added != 1 else ''}")

    summary = ", ".join(parts) if parts else "no changes detected"

    return {
        "before": before,
        "after": after,
        "changes": changes,
        "summary": summary,
    }


def parse_page_sections(html: str) -> List[Dict[str, Any]]:
    """Parse HTML content into logical sections.

    Detects boundaries from ``<section>``, ``<nav>``, ``<footer>``,
    ``<aside>`` tags, ``<div>`` elements with class/id indicators, and
    ``<h2>``/``<h3>`` headings.

    Parameters
    ----------
    html : str
        Raw HTML content.

    Returns
    -------
    list of dict
        Each section: ``{"section_id", "section_type", "content",
        "start_line", "end_line"}``.
    """
    sections: List[Dict[str, Any]] = []
    lines = html.splitlines()

    # Patterns for section boundaries
    section_patterns = [
        (r"<section[^>]*>", "section_open"),
        (r"</section>", "section_close"),
        (r"<nav[^>]*>", "nav_open"),
        (r"</nav>", "nav_close"),
        (r"<footer[^>]*>", "footer_open"),
        (r"</footer>", "footer_close"),
        (r"<aside[^>]*>", "aside_open"),
        (r"</aside>", "aside_close"),
        (r"<header[^>]*>", "header_open"),
        (r"</header>", "header_close"),
    ]

    # Build a list of boundary events
    events: List[Dict[str, Any]] = []
    for line_idx, line in enumerate(lines):
        for pattern, event_type in section_patterns:
            for match in re.finditer(pattern, line, re.IGNORECASE):
                events.append({
                    "line": line_idx + 1,
                    "type": event_type,
                    "tag_content": line.strip(),
                })

    # If no semantic elements found, try to split on major div boundaries
    if not events:
        for line_idx, line in enumerate(lines):
            # Match divs with id or class attributes
            div_match = re.search(
                r'<div[^>]*(?:id|class)\s*=\s*["\']([^"\']*)["\']',
                line,
                re.IGNORECASE,
            )
            if div_match:
                events.append({
                    "line": line_idx + 1,
                    "type": "div_open",
                    "tag_content": line.strip(),
                    "identifier": div_match.group(1),
                })

    # If still nothing, look for heading-based boundaries
    if not events:
        for line_idx, line in enumerate(lines):
            heading_match = re.search(r"<h[1-3][^>]*>", line, re.IGNORECASE)
            if heading_match:
                events.append({
                    "line": line_idx + 1,
                    "type": "heading",
                    "tag_content": line.strip(),
                })

    # Convert events into sections using a stack-based approach
    stack: List[Dict[str, Any]] = []
    section_counter = 0

    for event in events:
        etype = event["type"]

        if etype.endswith("_open"):
            stack.append(event)

        elif etype.endswith("_close") and stack:
            open_event = stack.pop()
            section_counter += 1
            tag_base = etype.replace("_close", "")
            start = open_event["line"]
            end = event["line"]

            # Determine section type
            section_type = _infer_section_type(
                tag_base, open_event.get("tag_content", ""), start == 1
            )

            # Extract the id from the opening tag if present
            id_match = re.search(
                r'id\s*=\s*["\']([^"\']*)["\']',
                open_event.get("tag_content", ""),
                re.IGNORECASE,
            )
            section_id = (
                id_match.group(1) if id_match else f"{section_type}_{section_counter}"
            )

            content_lines = lines[start - 1 : end]
            sections.append({
                "section_id": section_id,
                "section_type": section_type,
                "content": "\n".join(content_lines),
                "start_line": start,
                "end_line": end,
            })

        elif etype in ("div_open", "heading"):
            # For flat markers, each starts a new section ending at the next marker
            section_counter += 1
            start = event["line"]

            # Find end: next event's line - 1, or end of file
            idx = events.index(event)
            if idx + 1 < len(events):
                end = events[idx + 1]["line"] - 1
            else:
                end = len(lines)

            identifier = event.get("identifier", "")
            section_type = _infer_type_from_identifier(identifier, event.get("tag_content", ""))
            section_id = identifier if identifier else f"{section_type}_{section_counter}"

            content_lines = lines[start - 1 : end]
            sections.append({
                "section_id": section_id,
                "section_type": section_type,
                "content": "\n".join(content_lines),
                "start_line": start,
                "end_line": end,
            })

    # Fallback: if no sections were parsed, treat entire HTML as one section
    if not sections and html.strip():
        is_hero = bool(re.search(r"<h1[^>]*>", html, re.IGNORECASE))
        sections.append({
            "section_id": "main_1",
            "section_type": "hero" if is_hero else "content",
            "content": html,
            "start_line": 1,
            "end_line": len(lines),
        })

    return sections


def _infer_section_type(tag_base: str, tag_content: str, is_first: bool) -> str:
    """Infer section type from the HTML tag and its attributes."""
    tag_lower = tag_base.lower()
    content_lower = tag_content.lower()

    if tag_lower == "nav":
        return "nav"
    if tag_lower == "footer":
        return "footer"
    if tag_lower == "aside":
        return "sidebar"
    if tag_lower == "header":
        return "header"

    # For <section> tags, inspect class/id for hints
    if "hero" in content_lower:
        return "hero"
    if "testimonial" in content_lower:
        return "testimonials"
    if "cta" in content_lower:
        return "cta_block"
    if "faq" in content_lower:
        return "faq"
    if "trust" in content_lower or "logo" in content_lower:
        return "trust_signals"
    if "contact" in content_lower or "form" in content_lower:
        return "contact_form"

    # Check for h1 to identify hero
    if re.search(r"<h1[^>]*>", tag_content, re.IGNORECASE) or is_first:
        return "hero"

    return "content"


def _infer_type_from_identifier(identifier: str, tag_content: str) -> str:
    """Infer section type from a class/id string."""
    combined = (identifier + " " + tag_content).lower()

    type_map = {
        "hero": "hero",
        "nav": "nav",
        "footer": "footer",
        "sidebar": "sidebar",
        "aside": "sidebar",
        "testimonial": "testimonials",
        "cta": "cta_block",
        "faq": "faq",
        "trust": "trust_signals",
        "contact": "contact_form",
        "form": "contact_form",
        "header": "header",
    }

    for keyword, section_type in type_map.items():
        if keyword in combined:
            return section_type

    return "content"


def validate_html_safety(html: str, *, allow_tracking_scripts: bool = False) -> Dict[str, Any]:
    """Check HTML content for unsafe elements before injection.

    Parameters
    ----------
    html : str
        HTML content to validate.
    allow_tracking_scripts : bool
        When True, ``<script>`` tags containing known tracking IDs
        (GA4, GTM, Meta Pixel) are allowed. Default False.

    Returns
    -------
    dict
        ``{"safe": bool, "warnings": list[str]}``
    """
    warnings: List[str] = []

    # Check for <script> tags
    script_matches = re.findall(r"<script[^>]*>.*?</script>", html, re.IGNORECASE | re.DOTALL)
    if not script_matches:
        # Also catch self-closing or unclosed script tags
        script_matches = re.findall(r"<script[^>]*>", html, re.IGNORECASE)

    if script_matches:
        if allow_tracking_scripts:
            # Allow known tracking patterns
            tracking_patterns = [
                r"googletagmanager\.com",
                r"gtag\(",
                r"G-[A-Z0-9]+",
                r"GTM-[A-Z0-9]+",
                r"fbq\(",
                r"connect\.facebook\.net",
                r"hotjar\.com",
            ]
            for script in script_matches:
                is_tracking = any(
                    re.search(pat, script, re.IGNORECASE) for pat in tracking_patterns
                )
                if not is_tracking:
                    warnings.append(
                        f"Non-tracking <script> tag detected: {script[:100]}..."
                    )
        else:
            warnings.append(
                f"Found {len(script_matches)} <script> tag(s). "
                "Scripts are not allowed unless explicitly expected for tracking."
            )

    # Check for <iframe> tags
    iframe_matches = re.findall(r"<iframe[^>]*>", html, re.IGNORECASE)
    if iframe_matches:
        warnings.append(
            f"Found {len(iframe_matches)} <iframe> tag(s). "
            "Iframes are not allowed unless explicitly expected."
        )

    # Check for inline event handlers
    event_handlers = re.findall(
        r'\bon(?:click|load|error|mouseover|mouseout|focus|blur|submit|change|keyup|keydown'
        r'|keypress|dblclick|contextmenu|mouseenter|mouseleave|input|reset)\s*=',
        html,
        re.IGNORECASE,
    )
    if event_handlers:
        warnings.append(
            f"Found {len(event_handlers)} inline event handler(s) "
            f"(e.g., onclick, onload). Inline handlers are not allowed."
        )

    # Check for javascript: protocol in href/src attributes
    js_protocol = re.findall(
        r'(?:href|src|action)\s*=\s*["\']javascript:',
        html,
        re.IGNORECASE,
    )
    if js_protocol:
        warnings.append(
            f"Found {len(js_protocol)} javascript: protocol URI(s). Not allowed."
        )

    # Check for data: URIs (potential XSS vector)
    data_uri = re.findall(
        r'(?:href|src)\s*=\s*["\']data:(?!image/)',
        html,
        re.IGNORECASE,
    )
    if data_uri:
        warnings.append(
            f"Found {len(data_uri)} non-image data: URI(s). Potentially unsafe."
        )

    # Check for external resource loading from unknown domains
    external_resources = re.findall(
        r'(?:src|href)\s*=\s*["\']https?://([^/"\']+)',
        html,
        re.IGNORECASE,
    )
    known_safe_domains = {
        "fonts.googleapis.com",
        "fonts.gstatic.com",
        "cdn.jsdelivr.net",
        "cdnjs.cloudflare.com",
        "unpkg.com",
        "www.googletagmanager.com",
        "www.google-analytics.com",
        "connect.facebook.net",
        "www.facebook.com",
        "static.hotjar.com",
        "snap.licdn.com",
        "platform.twitter.com",
    }
    unknown_domains = [
        d for d in external_resources if d.lower() not in known_safe_domains
    ]
    if unknown_domains:
        unique_unknown = sorted(set(unknown_domains))
        warnings.append(
            f"External resources loaded from unknown domain(s): "
            f"{', '.join(unique_unknown[:5])}"
            f"{' (and more)' if len(unique_unknown) > 5 else ''}. "
            "Verify these are trusted."
        )

    return {
        "safe": len(warnings) == 0,
        "warnings": warnings,
    }


# ---------------------------------------------------------------------------
# Concrete Action Classes
# ---------------------------------------------------------------------------

# Valid CTA locations shared across classes
_VALID_CTA_LOCATIONS = frozenset({
    "header", "hero", "body", "footer", "sticky_bar", "popup",
})

# Valid tracking types
_VALID_TRACKING_TYPES = frozenset({
    "ga4", "gtm", "meta_pixel", "google_ads_conversion",
    "call_tracking", "hotjar", "custom",
})

# Required config keys per tracking type
_TRACKING_REQUIRED_KEYS: Dict[str, List[str]] = {
    "ga4": ["measurement_id"],
    "gtm": ["container_id"],
    "meta_pixel": ["pixel_id"],
    "google_ads_conversion": ["conversion_id", "conversion_label"],
    "call_tracking": ["provider", "tracking_number"],
    "hotjar": ["site_id"],
    "custom": ["snippet"],
}

# Valid section types for AddSection
_VALID_SECTION_TYPES = frozenset({
    "hero", "testimonials", "cta_block", "faq", "trust_signals",
    "service_description", "contact_form", "custom",
})


class UpdatePageCopy(Action):
    """Replace text content in a specific page section.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    section_id : str
        Section within the page to update.
    new_copy : str
        New text content for the section.
    reason : str
        Why this change is being made.
    connector : object or None
        CMS connector instance.
    """

    def __init__(
        self,
        page_id: str,
        section_id: str,
        new_copy: str,
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_upc_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.section_id = section_id
        self.new_copy = new_copy

    def validate(self) -> ActionResult:
        # Check required params
        if not self.page_id:
            return self._fail_result("page_id is required.")
        if not self.section_id:
            return self._fail_result("section_id is required.")
        if not self.new_copy:
            return self._fail_result("new_copy cannot be empty.")

        # Check connector and page existence
        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
            except Exception as exc:
                return self._fail_result(f"Page '{self.page_id}' not found: {exc}")

            # Check section exists
            sections = page.get("sections", [])
            section_ids = [s.get("section_id", s.get("id", "")) for s in sections]
            if self.section_id not in section_ids:
                return self._fail_result(
                    f"Section '{self.section_id}' not found on page '{self.page_id}'. "
                    f"Available sections: {section_ids}"
                )

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed.")

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        before_content = ""
        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
                sections = page.get("sections", [])
                for section in sections:
                    sid = section.get("section_id", section.get("id", ""))
                    if sid == self.section_id:
                        before_content = section.get("content", "")
                        break
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "section_id": self.section_id,
                    "content": before_content,
                    "content_type": "text",
                }
            except Exception:
                pass

        diff = generate_diff(before_content, self.new_copy)
        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"Preview generated: {diff['summary']}",
            before_state=self._before_snapshot,
            metadata={"diff": diff},
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        # Capture before-state if not already captured
        if self._before_snapshot is None:
            try:
                page = self.connector.get_page(self.page_id)
                for section in page.get("sections", []):
                    sid = section.get("section_id", section.get("id", ""))
                    if sid == self.section_id:
                        self._before_snapshot = {
                            "page_id": self.page_id,
                            "section_id": self.section_id,
                            "content": section.get("content", ""),
                            "content_type": "text",
                        }
                        break
            except Exception:
                pass

        try:
            result = self.connector.update_page_section(
                self.page_id, self.section_id, self.new_copy, content_type="text"
            )
            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"Section '{self.section_id}' on page '{self.page_id}' updated.",
                before_state=self._before_snapshot,
                after_state={
                    "page_id": self.page_id,
                    "section_id": self.section_id,
                    "content": self.new_copy,
                },
                metadata={"connector_result": result},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        try:
            page = self.connector.get_page(self.page_id)
            for section in page.get("sections", []):
                sid = section.get("section_id", section.get("id", ""))
                if sid == self.section_id:
                    current = section.get("content", "")
                    if current.strip() == self.new_copy.strip():
                        return self._success_result(
                            "Verification passed: section content matches expected copy."
                        )
                    else:
                        return self._fail_result(
                            "Verification failed: section content does not match.",
                            errors=[
                                f"Expected: {self.new_copy[:100]}...",
                                f"Found: {current[:100]}...",
                            ],
                        )
            return self._fail_result(
                f"Verification failed: section '{self.section_id}' not found."
            )
        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "section_id": self.section_id,
            "new_copy": self.new_copy,
        })
        return base


class UpdatePageSection(Action):
    """Replace full HTML content of a page section.

    Similar to UpdatePageCopy but handles raw HTML replacement.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    section_id : str
        Section within the page to update.
    new_html : str
        New HTML content for the section.
    reason : str
        Why this change is being made.
    """

    def __init__(
        self,
        page_id: str,
        section_id: str,
        new_html: str,
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_ups_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.section_id = section_id
        self.new_html = new_html

    def validate(self) -> ActionResult:
        if not self.page_id:
            return self._fail_result("page_id is required.")
        if not self.section_id:
            return self._fail_result("section_id is required.")
        if not self.new_html or not self.new_html.strip():
            return self._fail_result("new_html cannot be empty.")

        # Safety check on the new HTML
        safety = validate_html_safety(self.new_html)
        warnings: List[str] = []
        if not safety["safe"]:
            warnings = safety["warnings"]

        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
            except Exception as exc:
                return self._fail_result(f"Page '{self.page_id}' not found: {exc}")

            sections = page.get("sections", [])
            section_ids = [s.get("section_id", s.get("id", "")) for s in sections]
            if self.section_id not in section_ids:
                return self._fail_result(
                    f"Section '{self.section_id}' not found on page '{self.page_id}'. "
                    f"Available sections: {section_ids}"
                )

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed.", warnings=warnings)

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        before_html = ""
        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
                for section in page.get("sections", []):
                    sid = section.get("section_id", section.get("id", ""))
                    if sid == self.section_id:
                        before_html = section.get("content", "")
                        break
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "section_id": self.section_id,
                    "content": before_html,
                    "content_type": "html",
                }
            except Exception:
                pass

        diff = generate_diff(before_html, self.new_html)
        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"Preview generated: {diff['summary']}",
            before_state=self._before_snapshot,
            metadata={"diff": diff},
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        if self._before_snapshot is None:
            try:
                page = self.connector.get_page(self.page_id)
                for section in page.get("sections", []):
                    sid = section.get("section_id", section.get("id", ""))
                    if sid == self.section_id:
                        self._before_snapshot = {
                            "page_id": self.page_id,
                            "section_id": self.section_id,
                            "content": section.get("content", ""),
                            "content_type": "html",
                        }
                        break
            except Exception:
                pass

        try:
            result = self.connector.update_page_section(
                self.page_id, self.section_id, self.new_html, content_type="html"
            )
            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"Section '{self.section_id}' HTML updated on page '{self.page_id}'.",
                before_state=self._before_snapshot,
                after_state={
                    "page_id": self.page_id,
                    "section_id": self.section_id,
                    "content": self.new_html,
                },
                metadata={"connector_result": result},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        try:
            page = self.connector.get_page(self.page_id)
            for section in page.get("sections", []):
                sid = section.get("section_id", section.get("id", ""))
                if sid == self.section_id:
                    current = section.get("content", "")
                    if current.strip() == self.new_html.strip():
                        return self._success_result(
                            "Verification passed: section HTML matches."
                        )
                    else:
                        return self._fail_result(
                            "Verification failed: section HTML does not match.",
                            errors=[
                                f"Expected length: {len(self.new_html)}",
                                f"Found length: {len(current)}",
                            ],
                        )
            return self._fail_result(
                f"Verification failed: section '{self.section_id}' not found."
            )
        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "section_id": self.section_id,
            "new_html_length": len(self.new_html),
        })
        return base


class UpdateCTA(Action):
    """Update a call-to-action element on a page.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    cta_location : str
        One of: ``"header"``, ``"hero"``, ``"body"``, ``"footer"``,
        ``"sticky_bar"``, ``"popup"``.
    new_cta_text : str
        New CTA button/link text.
    new_cta_url : str or None
        New CTA destination URL. If None, URL is not changed.
    reason : str
        Why this change is being made.
    """

    def __init__(
        self,
        page_id: str,
        cta_location: str,
        new_cta_text: str,
        new_cta_url: Optional[str],
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_cta_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.cta_location = cta_location
        self.new_cta_text = new_cta_text
        self.new_cta_url = new_cta_url

    def validate(self) -> ActionResult:
        if not self.page_id:
            return self._fail_result("page_id is required.")
        if not self.new_cta_text:
            return self._fail_result("new_cta_text is required.")
        if self.cta_location not in _VALID_CTA_LOCATIONS:
            return self._fail_result(
                f"Invalid cta_location '{self.cta_location}'. "
                f"Valid locations: {sorted(_VALID_CTA_LOCATIONS)}"
            )

        if self.connector is not None:
            try:
                self.connector.get_page(self.page_id)
            except Exception as exc:
                return self._fail_result(f"Page '{self.page_id}' not found: {exc}")

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed.")

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        old_cta: Dict[str, Any] = {"text": "", "url": ""}
        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
                old_cta = self._find_cta_in_page(page)
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "cta_location": self.cta_location,
                    "cta_text": old_cta.get("text", ""),
                    "cta_url": old_cta.get("url", ""),
                }
            except Exception:
                pass

        new_cta = {
            "text": self.new_cta_text,
            "url": self.new_cta_url or old_cta.get("url", ""),
        }

        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"CTA preview: '{old_cta.get('text', '(unknown)')}' -> '{self.new_cta_text}'",
            before_state=self._before_snapshot,
            metadata={
                "old_cta": old_cta,
                "new_cta": new_cta,
            },
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        if self._before_snapshot is None:
            try:
                page = self.connector.get_page(self.page_id)
                old_cta = self._find_cta_in_page(page)
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "cta_location": self.cta_location,
                    "cta_text": old_cta.get("text", ""),
                    "cta_url": old_cta.get("url", ""),
                }
            except Exception:
                pass

        try:
            # Find the section that contains the CTA and update it
            page = self.connector.get_page(self.page_id)
            cta_section = self._find_cta_section(page)

            if cta_section is None:
                self.state = ActionLifecycleState.failed
                return self._fail_result(
                    f"No CTA found at location '{self.cta_location}' on page '{self.page_id}'."
                )

            section_id = cta_section.get("section_id", cta_section.get("id", ""))
            old_content = cta_section.get("content", "")

            # Update CTA text and URL in the section content
            new_content = self._replace_cta_in_content(old_content)

            result = self.connector.update_page_section(
                self.page_id, section_id, new_content, content_type="html"
            )

            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"CTA at '{self.cta_location}' updated on page '{self.page_id}'.",
                before_state=self._before_snapshot,
                after_state={
                    "page_id": self.page_id,
                    "cta_location": self.cta_location,
                    "cta_text": self.new_cta_text,
                    "cta_url": self.new_cta_url,
                },
                metadata={"connector_result": result},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        try:
            page = self.connector.get_page(self.page_id)
            content_html = page.get("content_html", "")

            # Check if the new CTA text appears in the page
            if self.new_cta_text in content_html:
                url_ok = True
                if self.new_cta_url and self.new_cta_url not in content_html:
                    url_ok = False

                if url_ok:
                    return self._success_result(
                        "Verification passed: CTA text and URL confirmed."
                    )
                else:
                    return self._fail_result(
                        "Verification partial: CTA text found but URL not confirmed.",
                        errors=[f"Expected URL '{self.new_cta_url}' not found in page."],
                    )
            else:
                return self._fail_result(
                    f"Verification failed: CTA text '{self.new_cta_text}' not found."
                )
        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def _find_cta_in_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """Extract current CTA info from a page at the target location."""
        sections = page.get("sections", [])
        for section in sections:
            section_type = section.get("section_type", "")
            sid = section.get("section_id", section.get("id", "")).lower()
            combined = f"{section_type} {sid}"

            if self.cta_location in combined or self._location_matches_section(section):
                content = section.get("content", "")
                # Extract first <a> tag with button-like class
                a_match = re.search(
                    r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>(.*?)</a>',
                    content,
                    re.IGNORECASE | re.DOTALL,
                )
                if a_match:
                    # Strip HTML tags from the link text
                    text = re.sub(r"<[^>]+>", "", a_match.group(2)).strip()
                    return {"text": text, "url": a_match.group(1)}

                # Try <button> tags
                btn_match = re.search(
                    r"<button[^>]*>(.*?)</button>",
                    content,
                    re.IGNORECASE | re.DOTALL,
                )
                if btn_match:
                    text = re.sub(r"<[^>]+>", "", btn_match.group(1)).strip()
                    return {"text": text, "url": ""}

        return {"text": "", "url": ""}

    def _find_cta_section(self, page: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find the section containing the CTA at the target location."""
        sections = page.get("sections", [])
        for section in sections:
            if self._location_matches_section(section):
                return section
        # Fallback: look for any section with a CTA-like element
        for section in sections:
            content = section.get("content", "")
            if re.search(r'<a[^>]*class=["\'][^"\']*btn|button', content, re.IGNORECASE):
                return section
        return None

    def _location_matches_section(self, section: Dict[str, Any]) -> bool:
        """Check if a section matches the target CTA location."""
        section_type = section.get("section_type", "").lower()
        sid = section.get("section_id", section.get("id", "")).lower()
        combined = f"{section_type} {sid}"

        location_map = {
            "header": ["header", "nav"],
            "hero": ["hero"],
            "body": ["content", "body", "main"],
            "footer": ["footer"],
            "sticky_bar": ["sticky", "bar", "fixed"],
            "popup": ["popup", "modal", "overlay"],
        }

        keywords = location_map.get(self.cta_location, [self.cta_location])
        return any(kw in combined for kw in keywords)

    def _replace_cta_in_content(self, content: str) -> str:
        """Replace CTA text and URL in section HTML content."""
        # Replace <a> tag content
        def replace_link(match: re.Match) -> str:
            full = match.group(0)
            url = self.new_cta_url if self.new_cta_url else match.group(1)
            # Reconstruct the link with new text and URL
            tag_start = full[: full.index("href=")]
            tag_rest = full[full.index(">") + 1 :]
            closing = tag_rest[tag_rest.rindex("</a>") :]
            return f'{tag_start}href="{url}">{self.new_cta_text}{closing}'

        updated = re.sub(
            r'<a[^>]*href=["\']([^"\']*)["\'][^>]*>.*?</a>',
            replace_link,
            content,
            count=1,
            flags=re.IGNORECASE | re.DOTALL,
        )

        # If no <a> tag was replaced, try <button>
        if updated == content:
            updated = re.sub(
                r"(<button[^>]*>).*?(</button>)",
                rf"\g<1>{self.new_cta_text}\g<2>",
                content,
                count=1,
                flags=re.IGNORECASE | re.DOTALL,
            )

        return updated

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "cta_location": self.cta_location,
            "new_cta_text": self.new_cta_text,
            "new_cta_url": self.new_cta_url,
        })
        return base


class UpdateMetadata(Action):
    """Update SEO metadata (title, description, schema markup) for a page.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    title : str or None
        New title tag (must be < 60 chars if provided).
    description : str or None
        New meta description (must be < 160 chars if provided).
    schema_markup : dict or None
        New JSON-LD schema markup to set.
    reason : str
        Why this change is being made.
    """

    def __init__(
        self,
        page_id: str,
        title: Optional[str],
        description: Optional[str],
        schema_markup: Optional[Dict[str, Any]],
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_meta_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.title = title
        self.description = description
        self.schema_markup = schema_markup

    def validate(self) -> ActionResult:
        if not self.page_id:
            return self._fail_result("page_id is required.")

        # Must update at least one field
        if self.title is None and self.description is None and self.schema_markup is None:
            return self._fail_result(
                "At least one of title, description, or schema_markup must be provided."
            )

        warnings: List[str] = []

        # Validate title length
        if self.title is not None:
            if len(self.title) >= 60:
                return self._fail_result(
                    f"Title is {len(self.title)} characters. Must be under 60."
                )
            if len(self.title) < 10:
                warnings.append(
                    f"Title is only {len(self.title)} characters. "
                    "Consider making it more descriptive (30-60 chars ideal)."
                )

        # Validate description length
        if self.description is not None:
            if len(self.description) >= 160:
                return self._fail_result(
                    f"Description is {len(self.description)} characters. Must be under 160."
                )
            if len(self.description) < 50:
                warnings.append(
                    f"Description is only {len(self.description)} characters. "
                    "Consider making it more descriptive (120-155 chars ideal)."
                )

        if self.connector is not None:
            try:
                self.connector.get_page(self.page_id)
            except Exception as exc:
                return self._fail_result(f"Page '{self.page_id}' not found: {exc}")

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed.", warnings=warnings)

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        old_meta: Dict[str, Any] = {}
        if self.connector is not None:
            try:
                old_meta = self.connector.get_metadata(self.page_id)
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "metadata": old_meta,
                }
            except Exception:
                pass

        new_meta = self._build_meta_dict()
        changes: Dict[str, Dict[str, Any]] = {}
        for key, new_val in new_meta.items():
            old_val = old_meta.get(key)
            if old_val != new_val:
                changes[key] = {"before": old_val, "after": new_val}

        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"Metadata preview: {len(changes)} field(s) will change.",
            before_state=self._before_snapshot,
            metadata={"changes": changes, "new_meta": new_meta},
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        if self._before_snapshot is None:
            try:
                old_meta = self.connector.get_metadata(self.page_id)
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "metadata": old_meta,
                }
            except Exception:
                pass

        meta_dict = self._build_meta_dict()

        try:
            result = self.connector.update_metadata(self.page_id, meta_dict)
            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"Metadata updated on page '{self.page_id}'.",
                before_state=self._before_snapshot,
                after_state={"page_id": self.page_id, "metadata": meta_dict},
                metadata={"connector_result": result},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        try:
            current_meta = self.connector.get_metadata(self.page_id)
            mismatches: List[str] = []

            if self.title is not None:
                current_title = current_meta.get("title", "")
                if current_title != self.title:
                    mismatches.append(
                        f"Title: expected '{self.title}', found '{current_title}'"
                    )

            if self.description is not None:
                current_desc = current_meta.get("meta_description", "")
                if current_desc != self.description:
                    mismatches.append(
                        f"Description: expected '{self.description}', "
                        f"found '{current_desc}'"
                    )

            if self.schema_markup is not None:
                current_schema = current_meta.get("schema_markup", [])
                # Simple presence check
                if not current_schema:
                    mismatches.append("Schema markup: expected markup not found.")

            if mismatches:
                return self._fail_result(
                    "Verification failed: metadata mismatches detected.",
                    errors=mismatches,
                )

            return self._success_result("Verification passed: metadata matches.")

        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def _build_meta_dict(self) -> Dict[str, Any]:
        """Build the metadata update dict from provided fields."""
        meta: Dict[str, Any] = {}
        if self.title is not None:
            meta["title"] = self.title
        if self.description is not None:
            meta["meta_description"] = self.description
        if self.schema_markup is not None:
            meta["schema_markup"] = self.schema_markup
        return meta

    def _apply_rollback(self, before_snapshot: Dict[str, Any]) -> None:
        """Restore metadata from the before-snapshot."""
        if "metadata" in before_snapshot:
            self.connector.update_metadata(
                before_snapshot["page_id"],
                before_snapshot["metadata"],
            )

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "title": self.title,
            "description": self.description,
            "has_schema_markup": self.schema_markup is not None,
        })
        return base


class FixTracking(Action):
    """Inject or fix analytics/tracking code on a page.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    tracking_type : str
        One of: ``"ga4"``, ``"gtm"``, ``"meta_pixel"``,
        ``"google_ads_conversion"``, ``"call_tracking"``, ``"hotjar"``,
        ``"custom"``.
    tracking_config : dict
        Type-specific configuration. See ``_TRACKING_REQUIRED_KEYS`` for
        required fields per type.
    reason : str
        Why this change is being made.
    """

    def __init__(
        self,
        page_id: str,
        tracking_type: str,
        tracking_config: Dict[str, Any],
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_trk_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.tracking_type = tracking_type
        self.tracking_config = tracking_config

    def validate(self) -> ActionResult:
        if not self.page_id:
            return self._fail_result("page_id is required.")
        if self.tracking_type not in _VALID_TRACKING_TYPES:
            return self._fail_result(
                f"Invalid tracking_type '{self.tracking_type}'. "
                f"Valid types: {sorted(_VALID_TRACKING_TYPES)}"
            )

        # Validate required config keys
        required = _TRACKING_REQUIRED_KEYS.get(self.tracking_type, [])
        missing = [k for k in required if k not in self.tracking_config]
        if missing:
            return self._fail_result(
                f"Missing required config key(s) for '{self.tracking_type}': "
                f"{missing}"
            )

        if self.connector is not None:
            try:
                self.connector.get_page(self.page_id)
            except Exception as exc:
                return self._fail_result(f"Page '{self.page_id}' not found: {exc}")

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed.")

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        snippet = self._generate_tracking_snippet()

        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "content_html": page.get("content_html", ""),
                }
            except Exception:
                pass

        # Validate the snippet safety
        safety = validate_html_safety(snippet, allow_tracking_scripts=True)

        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"Tracking snippet preview for '{self.tracking_type}'.",
            before_state=self._before_snapshot,
            metadata={
                "tracking_type": self.tracking_type,
                "snippet": snippet,
                "snippet_length": len(snippet),
                "safety_check": safety,
            },
            warnings=safety.get("warnings", []),
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        snippet = self._generate_tracking_snippet()

        if self._before_snapshot is None:
            try:
                page = self.connector.get_page(self.page_id)
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "content_html": page.get("content_html", ""),
                }
            except Exception:
                pass

        try:
            # Get current page content and inject tracking snippet
            page = self.connector.get_page(self.page_id)
            current_html = page.get("content_html", "")

            # Inject into <head> if available, otherwise prepend
            injection_point = self.tracking_config.get("injection_point", "head")
            if injection_point == "head":
                if "</head>" in current_html:
                    updated_html = current_html.replace(
                        "</head>", f"{snippet}\n</head>"
                    )
                else:
                    updated_html = snippet + "\n" + current_html
            else:
                if "</body>" in current_html:
                    updated_html = current_html.replace(
                        "</body>", f"{snippet}\n</body>"
                    )
                else:
                    updated_html = current_html + "\n" + snippet

            # Use the page's first section or a synthetic one for the update
            sections = page.get("sections", [])
            if sections:
                # Update the first section that contains <head> or <body>
                target_section = sections[0]
                section_id = target_section.get(
                    "section_id", target_section.get("id", "main")
                )
            else:
                section_id = "head"

            result = self.connector.update_page_section(
                self.page_id, section_id, updated_html, content_type="html"
            )

            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"Tracking '{self.tracking_type}' injected on page '{self.page_id}'.",
                before_state=self._before_snapshot,
                after_state={
                    "page_id": self.page_id,
                    "tracking_type": self.tracking_type,
                    "snippet_injected": True,
                },
                metadata={"connector_result": result, "snippet": snippet},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        try:
            page = self.connector.get_page(self.page_id)
            content = page.get("content_html", "")

            # Check for the tracking identifier in the page source
            identifier = self._get_tracking_identifier()
            if identifier and identifier in content:
                return self._success_result(
                    f"Verification passed: '{self.tracking_type}' tracking "
                    f"code found (identifier: {identifier})."
                )
            else:
                return self._fail_result(
                    f"Verification failed: tracking identifier '{identifier}' "
                    f"not found in page source."
                )
        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def _generate_tracking_snippet(self) -> str:
        """Generate the tracking code snippet for the configured type."""
        generators = {
            "ga4": self._ga4_snippet,
            "gtm": self._gtm_snippet,
            "meta_pixel": self._meta_pixel_snippet,
            "google_ads_conversion": self._google_ads_snippet,
            "call_tracking": self._call_tracking_snippet,
            "hotjar": self._hotjar_snippet,
            "custom": self._custom_snippet,
        }
        generator = generators.get(self.tracking_type, self._custom_snippet)
        return generator()

    def _ga4_snippet(self) -> str:
        mid = self.tracking_config["measurement_id"]
        return (
            f'<!-- Google Analytics (GA4) -->\n'
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={mid}"></script>\n'
            f'<script>\n'
            f'  window.dataLayer = window.dataLayer || [];\n'
            f'  function gtag(){{dataLayer.push(arguments);}}\n'
            f"  gtag('js', new Date());\n"
            f"  gtag('config', '{mid}');\n"
            f'</script>'
        )

    def _gtm_snippet(self) -> str:
        cid = self.tracking_config["container_id"]
        return (
            f'<!-- Google Tag Manager -->\n'
            f'<script>(function(w,d,s,l,i){{w[l]=w[l]||[];w[l].push({{\'gtm.start\':\n'
            f"new Date().getTime(),event:'gtm.js'}});var f=d.getElementsByTagName(s)[0],\n"
            f"j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=\n"
            f"'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);\n"
            f"}})(window,document,'script','dataLayer','{cid}');</script>\n"
            f'<!-- End Google Tag Manager -->'
        )

    def _meta_pixel_snippet(self) -> str:
        pid = self.tracking_config["pixel_id"]
        return (
            f'<!-- Meta Pixel Code -->\n'
            f'<script>\n'
            f"!function(f,b,e,v,n,t,s)\n"
            f"{{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?\n"
            f"n.callMethod.apply(n,arguments):n.queue.push(arguments)}};\n"
            f"if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';\n"
            f"n.queue=[];t=b.createElement(e);t.async=!0;\n"
            f"t.src=v;s=b.getElementsByTagName(e)[0];\n"
            f"s.parentNode.insertBefore(t,s)}}(window, document,'script',\n"
            f"'https://connect.facebook.net/en_US/fbevents.js');\n"
            f"fbq('init', '{pid}');\n"
            f"fbq('track', 'PageView');\n"
            f'</script>\n'
            f'<noscript><img height="1" width="1" style="display:none"\n'
            f'src="https://www.facebook.com/tr?id={pid}&ev=PageView&noscript=1"\n'
            f'/></noscript>\n'
            f'<!-- End Meta Pixel Code -->'
        )

    def _google_ads_snippet(self) -> str:
        cid = self.tracking_config["conversion_id"]
        label = self.tracking_config["conversion_label"]
        return (
            f'<!-- Google Ads Conversion Tracking -->\n'
            f'<script async src="https://www.googletagmanager.com/gtag/js?id={cid}"></script>\n'
            f'<script>\n'
            f'  window.dataLayer = window.dataLayer || [];\n'
            f'  function gtag(){{dataLayer.push(arguments);}}\n'
            f"  gtag('js', new Date());\n"
            f"  gtag('config', '{cid}');\n"
            f"  gtag('event', 'conversion', {{'send_to': '{cid}/{label}'}});\n"
            f'</script>'
        )

    def _call_tracking_snippet(self) -> str:
        provider = self.tracking_config["provider"]
        number = self.tracking_config["tracking_number"]
        script_url = self.tracking_config.get("script_url", "")
        if script_url:
            return (
                f'<!-- {provider} Call Tracking -->\n'
                f'<script async src="{script_url}"></script>\n'
                f'<!-- Tracking number: {number} -->'
            )
        return (
            f'<!-- {provider} Call Tracking -->\n'
            f'<!-- Tracking number: {number} -->\n'
            f'<a href="tel:{number}" class="call-tracking">{number}</a>'
        )

    def _hotjar_snippet(self) -> str:
        site_id = self.tracking_config["site_id"]
        return (
            f'<!-- Hotjar Tracking Code -->\n'
            f'<script>\n'
            f"  (function(h,o,t,j,a,r){{\n"
            f"    h.hj=h.hj||function(){{(h.hj.q=h.hj.q||[]).push(arguments)}};\n"
            f"    h._hjSettings={{hjid:{site_id},hjsv:6}};\n"
            f"    a=o.getElementsByTagName('head')[0];\n"
            f"    r=o.createElement('script');r.async=1;\n"
            f"    r.src=t+h._hjSettings.hjid+j+h._hjSettings.hjsv;\n"
            f"    a.appendChild(r);\n"
            f"  }})(window,document,'https://static.hotjar.com/c/hotjar-','.js?sv=');\n"
            f'</script>'
        )

    def _custom_snippet(self) -> str:
        return self.tracking_config.get("snippet", "<!-- custom tracking -->")

    def _get_tracking_identifier(self) -> str:
        """Return the key identifier string to look for during verification."""
        identifiers = {
            "ga4": self.tracking_config.get("measurement_id", ""),
            "gtm": self.tracking_config.get("container_id", ""),
            "meta_pixel": self.tracking_config.get("pixel_id", ""),
            "google_ads_conversion": self.tracking_config.get("conversion_id", ""),
            "call_tracking": self.tracking_config.get("tracking_number", ""),
            "hotjar": str(self.tracking_config.get("site_id", "")),
            "custom": self.tracking_config.get("verification_string", "custom tracking"),
        }
        return identifiers.get(self.tracking_type, "")

    def _apply_rollback(self, before_snapshot: Dict[str, Any]) -> None:
        """Restore the page content to remove injected tracking."""
        if "content_html" in before_snapshot:
            page = self.connector.get_page(before_snapshot["page_id"])
            sections = page.get("sections", [])
            if sections:
                section_id = sections[0].get(
                    "section_id", sections[0].get("id", "main")
                )
                self.connector.update_page_section(
                    before_snapshot["page_id"],
                    section_id,
                    before_snapshot["content_html"],
                    content_type="html",
                )

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "tracking_type": self.tracking_type,
            "tracking_config": {
                k: v for k, v in self.tracking_config.items() if k != "snippet"
            },
        })
        return base


class RefreshApprovedSection(Action):
    """Replace a page section with content from an approved creative block.

    Uses an ApprovedMessageBlock from the creative library to replace a
    section, ensuring only pre-approved content goes live.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    section_id : str
        Section to replace.
    approved_block_id : str
        Identifier of the approved creative block to use.
    reason : str
        Why this change is being made.
    """

    def __init__(
        self,
        page_id: str,
        section_id: str,
        approved_block_id: str,
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
        creative_library: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_ref_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.section_id = section_id
        self.approved_block_id = approved_block_id
        self.creative_library = creative_library
        self._approved_content: Optional[str] = None

    def validate(self) -> ActionResult:
        if not self.page_id:
            return self._fail_result("page_id is required.")
        if not self.section_id:
            return self._fail_result("section_id is required.")
        if not self.approved_block_id:
            return self._fail_result("approved_block_id is required.")

        # Validate approved block exists
        if self.creative_library is not None:
            block = self._get_approved_block()
            if block is None:
                return self._fail_result(
                    f"Approved block '{self.approved_block_id}' not found "
                    "in creative library."
                )
            # Check that the block is actually approved
            status = block.get("status", "")
            if status not in ("approved", "active"):
                return self._fail_result(
                    f"Block '{self.approved_block_id}' has status '{status}'. "
                    "Only approved or active blocks can be used."
                )
            self._approved_content = block.get("content", block.get("html", ""))

        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
            except Exception as exc:
                return self._fail_result(f"Page '{self.page_id}' not found: {exc}")

            sections = page.get("sections", [])
            section_ids = [s.get("section_id", s.get("id", "")) for s in sections]
            if self.section_id not in section_ids:
                return self._fail_result(
                    f"Section '{self.section_id}' not found on page '{self.page_id}'."
                )

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed.")

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        current_content = ""
        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
                for section in page.get("sections", []):
                    sid = section.get("section_id", section.get("id", ""))
                    if sid == self.section_id:
                        current_content = section.get("content", "")
                        break
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "section_id": self.section_id,
                    "content": current_content,
                    "content_type": "html",
                }
            except Exception:
                pass

        approved_content = self._approved_content or "(approved block content)"
        diff = generate_diff(current_content, approved_content)

        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"Preview: replacing section with approved block '{self.approved_block_id}'. "
            f"{diff['summary']}",
            before_state=self._before_snapshot,
            metadata={
                "diff": diff,
                "approved_block_id": self.approved_block_id,
            },
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        # Resolve approved content if not already
        if self._approved_content is None and self.creative_library is not None:
            block = self._get_approved_block()
            if block:
                self._approved_content = block.get("content", block.get("html", ""))

        if not self._approved_content:
            self.state = ActionLifecycleState.failed
            return self._fail_result(
                "Cannot execute: approved block content could not be resolved."
            )

        if self._before_snapshot is None:
            try:
                page = self.connector.get_page(self.page_id)
                for section in page.get("sections", []):
                    sid = section.get("section_id", section.get("id", ""))
                    if sid == self.section_id:
                        self._before_snapshot = {
                            "page_id": self.page_id,
                            "section_id": self.section_id,
                            "content": section.get("content", ""),
                            "content_type": "html",
                        }
                        break
            except Exception:
                pass

        try:
            result = self.connector.update_page_section(
                self.page_id,
                self.section_id,
                self._approved_content,
                content_type="html",
            )
            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"Section '{self.section_id}' refreshed with approved block "
                f"'{self.approved_block_id}'.",
                before_state=self._before_snapshot,
                after_state={
                    "page_id": self.page_id,
                    "section_id": self.section_id,
                    "approved_block_id": self.approved_block_id,
                },
                metadata={"connector_result": result},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        if not self._approved_content:
            return self._fail_result(
                "Cannot verify: approved content not available for comparison."
            )

        try:
            page = self.connector.get_page(self.page_id)
            for section in page.get("sections", []):
                sid = section.get("section_id", section.get("id", ""))
                if sid == self.section_id:
                    current = section.get("content", "")
                    if current.strip() == self._approved_content.strip():
                        return self._success_result(
                            "Verification passed: section matches approved block."
                        )
                    else:
                        return self._fail_result(
                            "Verification failed: section content does not match "
                            "approved block."
                        )
            return self._fail_result(
                f"Verification failed: section '{self.section_id}' not found."
            )
        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def _get_approved_block(self) -> Optional[Dict[str, Any]]:
        """Retrieve the approved block from the creative library."""
        if self.creative_library is None:
            return None

        # Try common creative library interfaces
        if hasattr(self.creative_library, "get_block"):
            return self.creative_library.get_block(self.approved_block_id)
        if hasattr(self.creative_library, "get"):
            return self.creative_library.get(self.approved_block_id)
        if isinstance(self.creative_library, dict):
            return self.creative_library.get(self.approved_block_id)

        return None

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "section_id": self.section_id,
            "approved_block_id": self.approved_block_id,
        })
        return base


class RestructurePage(Action):
    """Reorder sections on a page without changing their content.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    new_section_order : list of str
        Ordered list of section IDs defining the new arrangement.
    reason : str
        Why this change is being made.
    """

    def __init__(
        self,
        page_id: str,
        new_section_order: List[str],
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_reo_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.new_section_order = new_section_order

    def validate(self) -> ActionResult:
        if not self.page_id:
            return self._fail_result("page_id is required.")
        if not self.new_section_order:
            return self._fail_result("new_section_order cannot be empty.")

        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
            except Exception as exc:
                return self._fail_result(f"Page '{self.page_id}' not found: {exc}")

            sections = page.get("sections", [])
            existing_ids = {
                s.get("section_id", s.get("id", "")) for s in sections
            }
            requested_ids = set(self.new_section_order)

            # All requested IDs must exist
            missing = requested_ids - existing_ids
            if missing:
                return self._fail_result(
                    f"Section(s) not found on page: {sorted(missing)}"
                )

            # Warn if some existing sections are not in the new order
            omitted = existing_ids - requested_ids
            warnings = []
            if omitted:
                warnings.append(
                    f"Section(s) {sorted(omitted)} exist on the page but are "
                    "not in new_section_order. They will retain their "
                    "current position."
                )

            self.state = ActionLifecycleState.validated
            return self._success_result("Validation passed.", warnings=warnings)

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed (connector not available for full check).")

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        current_order: List[str] = []
        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
                sections = page.get("sections", [])
                current_order = [
                    s.get("section_id", s.get("id", "")) for s in sections
                ]
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "section_order": current_order,
                    "sections": sections,
                }
            except Exception:
                pass

        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"Section reorder preview: {len(self.new_section_order)} sections.",
            before_state=self._before_snapshot,
            metadata={
                "current_order": current_order,
                "new_order": self.new_section_order,
            },
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        try:
            page = self.connector.get_page(self.page_id)
            sections = page.get("sections", [])
            current_order = [
                s.get("section_id", s.get("id", "")) for s in sections
            ]

            if self._before_snapshot is None:
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "section_order": current_order,
                    "sections": sections,
                }

            # Build section lookup
            section_map = {
                s.get("section_id", s.get("id", "")): s for s in sections
            }

            # Assemble new content by concatenating sections in new order
            reordered_parts: List[str] = []
            for sid in self.new_section_order:
                section = section_map.get(sid)
                if section:
                    reordered_parts.append(section.get("content", ""))

            # Append any sections not in the new order
            for sid in current_order:
                if sid not in self.new_section_order and sid in section_map:
                    reordered_parts.append(section_map[sid].get("content", ""))

            new_content = "\n".join(reordered_parts)

            # Update the entire page content
            # Use the first section as the target for the combined update
            first_section_id = sections[0].get(
                "section_id", sections[0].get("id", "main")
            ) if sections else "main"

            result = self.connector.update_page_section(
                self.page_id, first_section_id, new_content, content_type="html"
            )

            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"Page '{self.page_id}' restructured with new section order.",
                before_state=self._before_snapshot,
                after_state={
                    "page_id": self.page_id,
                    "section_order": self.new_section_order,
                },
                metadata={"connector_result": result},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        try:
            page = self.connector.get_page(self.page_id)
            sections = page.get("sections", [])
            current_order = [
                s.get("section_id", s.get("id", "")) for s in sections
            ]

            # Check that the requested sections appear in the right order
            # (additional sections may exist between/after)
            order_idx = 0
            for sid in current_order:
                if order_idx < len(self.new_section_order):
                    if sid == self.new_section_order[order_idx]:
                        order_idx += 1

            if order_idx == len(self.new_section_order):
                return self._success_result(
                    "Verification passed: section order matches."
                )
            else:
                return self._fail_result(
                    "Verification failed: section order does not match.",
                    errors=[
                        f"Expected order: {self.new_section_order}",
                        f"Current order: {current_order}",
                    ],
                )
        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def _apply_rollback(self, before_snapshot: Dict[str, Any]) -> None:
        """Restore the original section order."""
        if "sections" in before_snapshot:
            original_content = "\n".join(
                s.get("content", "") for s in before_snapshot["sections"]
            )
            page = self.connector.get_page(before_snapshot["page_id"])
            sections = page.get("sections", [])
            first_sid = (
                sections[0].get("section_id", sections[0].get("id", "main"))
                if sections
                else "main"
            )
            self.connector.update_page_section(
                before_snapshot["page_id"],
                first_sid,
                original_content,
                content_type="html",
            )

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "new_section_order": self.new_section_order,
        })
        return base


class AddSection(Action):
    """Insert a new section at a specified position on a page.

    Parameters
    ----------
    page_id : str
        Target page identifier.
    position : str
        Where to insert: ``"before:{section_id}"``,
        ``"after:{section_id}"``, ``"top"``, or ``"bottom"``.
    section_type : str
        Type of section: ``"hero"``, ``"testimonials"``, ``"cta_block"``,
        ``"faq"``, ``"trust_signals"``, ``"service_description"``,
        ``"contact_form"``, ``"custom"``.
    content : str
        HTML content for the new section.
    reason : str
        Why this change is being made.
    """

    def __init__(
        self,
        page_id: str,
        position: str,
        section_type: str,
        content: str,
        reason: str,
        *,
        action_id: str = "",
        source_proposal_id: str = "",
        connector: Optional[Any] = None,
    ) -> None:
        if not action_id:
            action_id = f"act_add_{uuid.uuid4().hex[:12]}"
        super().__init__(action_id, source_proposal_id, reason, connector)
        self.page_id = page_id
        self.position = position
        self.section_type = section_type
        self.content = content
        self._new_section_id = f"{section_type}_{uuid.uuid4().hex[:8]}"

    def validate(self) -> ActionResult:
        if not self.page_id:
            return self._fail_result("page_id is required.")
        if not self.content or not self.content.strip():
            return self._fail_result("content cannot be empty.")

        # Validate section_type
        if self.section_type not in _VALID_SECTION_TYPES:
            return self._fail_result(
                f"Invalid section_type '{self.section_type}'. "
                f"Valid types: {sorted(_VALID_SECTION_TYPES)}"
            )

        # Validate position format
        valid_positions = {"top", "bottom"}
        if self.position not in valid_positions:
            if ":" not in self.position:
                return self._fail_result(
                    f"Invalid position '{self.position}'. "
                    "Use 'top', 'bottom', 'before:{{section_id}}', "
                    "or 'after:{{section_id}}'."
                )
            prefix, ref_id = self.position.split(":", 1)
            if prefix not in ("before", "after"):
                return self._fail_result(
                    f"Invalid position prefix '{prefix}'. Use 'before' or 'after'."
                )
            if not ref_id:
                return self._fail_result(
                    "Position reference section_id cannot be empty."
                )

            # Check that the reference section exists
            if self.connector is not None:
                try:
                    page = self.connector.get_page(self.page_id)
                    sections = page.get("sections", [])
                    section_ids = [
                        s.get("section_id", s.get("id", "")) for s in sections
                    ]
                    if ref_id not in section_ids:
                        return self._fail_result(
                            f"Reference section '{ref_id}' not found on page. "
                            f"Available sections: {section_ids}"
                        )
                except Exception as exc:
                    return self._fail_result(
                        f"Page '{self.page_id}' not found: {exc}"
                    )
        else:
            if self.connector is not None:
                try:
                    self.connector.get_page(self.page_id)
                except Exception as exc:
                    return self._fail_result(
                        f"Page '{self.page_id}' not found: {exc}"
                    )

        # Safety check on the new content
        safety = validate_html_safety(self.content)
        warnings = safety.get("warnings", [])

        self.state = ActionLifecycleState.validated
        return self._success_result("Validation passed.", warnings=warnings)

    def preview(self) -> ActionResult:
        self._require_state(ActionLifecycleState.validated, "preview")

        current_sections: List[str] = []
        if self.connector is not None:
            try:
                page = self.connector.get_page(self.page_id)
                sections = page.get("sections", [])
                current_sections = [
                    s.get("section_id", s.get("id", "")) for s in sections
                ]
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "sections": sections,
                    "section_order": current_sections,
                }
            except Exception:
                pass

        # Compute where the new section will appear
        insert_description = self._describe_insertion(current_sections)

        self.state = ActionLifecycleState.previewed
        result = self._success_result(
            f"New '{self.section_type}' section will be inserted {insert_description}.",
            before_state=self._before_snapshot,
            metadata={
                "new_section_id": self._new_section_id,
                "section_type": self.section_type,
                "position": self.position,
                "insert_description": insert_description,
                "content_preview": self.content[:500],
                "current_sections": current_sections,
            },
        )
        self._preview_result = result
        return result

    def execute(self) -> ActionResult:
        self._require_state(ActionLifecycleState.approved, "execute")
        self._require_connector("execute")

        self.state = ActionLifecycleState.executing

        try:
            page = self.connector.get_page(self.page_id)
            sections = page.get("sections", [])

            if self._before_snapshot is None:
                self._before_snapshot = {
                    "page_id": self.page_id,
                    "sections": sections,
                    "section_order": [
                        s.get("section_id", s.get("id", "")) for s in sections
                    ],
                }

            # Build the new section HTML with wrapping
            wrapped_content = (
                f'<section id="{self._new_section_id}" '
                f'class="kai-section kai-{self.section_type}" '
                f'data-section-type="{self.section_type}">\n'
                f"{self.content}\n"
                f"</section>"
            )

            # Determine insertion point and assemble new page content
            section_contents = [s.get("content", "") for s in sections]
            section_ids = [
                s.get("section_id", s.get("id", "")) for s in sections
            ]

            new_parts: List[str] = []
            inserted = False

            if self.position == "top":
                new_parts.append(wrapped_content)
                new_parts.extend(section_contents)
                inserted = True
            elif self.position == "bottom":
                new_parts.extend(section_contents)
                new_parts.append(wrapped_content)
                inserted = True
            else:
                prefix, ref_id = self.position.split(":", 1)
                for i, sid in enumerate(section_ids):
                    if prefix == "before" and sid == ref_id:
                        new_parts.append(wrapped_content)
                        inserted = True
                    new_parts.append(section_contents[i])
                    if prefix == "after" and sid == ref_id:
                        new_parts.append(wrapped_content)
                        inserted = True

            if not inserted:
                # Fallback: append to bottom
                new_parts = list(section_contents)
                new_parts.append(wrapped_content)

            combined_content = "\n".join(new_parts)

            # Update via the first section
            first_sid = section_ids[0] if section_ids else "main"
            result = self.connector.update_page_section(
                self.page_id, first_sid, combined_content, content_type="html"
            )

            self.state = ActionLifecycleState.completed
            return self._success_result(
                f"New '{self.section_type}' section added to page '{self.page_id}'.",
                before_state=self._before_snapshot,
                after_state={
                    "page_id": self.page_id,
                    "new_section_id": self._new_section_id,
                    "section_type": self.section_type,
                    "position": self.position,
                },
                metadata={"connector_result": result},
            )
        except Exception as exc:
            self.state = ActionLifecycleState.failed
            return self._fail_result(f"Execution failed: {exc}", errors=[str(exc)])

    def verify(self) -> ActionResult:
        self._require_connector("verify")
        try:
            page = self.connector.get_page(self.page_id)
            content_html = page.get("content_html", "")

            # Check if our section ID appears in the page
            if self._new_section_id in content_html:
                return self._success_result(
                    f"Verification passed: section '{self._new_section_id}' found."
                )

            # Also check for the content itself
            content_sample = self.content[:100].strip()
            if content_sample and content_sample in content_html:
                return self._success_result(
                    "Verification passed: section content found on page."
                )

            return self._fail_result(
                f"Verification failed: section '{self._new_section_id}' "
                "not found on page."
            )
        except Exception as exc:
            return self._fail_result(f"Verification error: {exc}")

    def _describe_insertion(self, current_sections: List[str]) -> str:
        """Generate a human-readable description of where the section goes."""
        if self.position == "top":
            return "at the top of the page"
        if self.position == "bottom":
            return "at the bottom of the page"

        prefix, ref_id = self.position.split(":", 1)
        return f"{prefix} section '{ref_id}'"

    def _apply_rollback(self, before_snapshot: Dict[str, Any]) -> None:
        """Remove the added section by restoring original page content."""
        if "sections" in before_snapshot:
            original_content = "\n".join(
                s.get("content", "") for s in before_snapshot["sections"]
            )
            page = self.connector.get_page(before_snapshot["page_id"])
            sections = page.get("sections", [])
            first_sid = (
                sections[0].get("section_id", sections[0].get("id", "main"))
                if sections
                else "main"
            )
            self.connector.update_page_section(
                before_snapshot["page_id"],
                first_sid,
                original_content,
                content_type="html",
            )

    def to_dict(self) -> Dict[str, Any]:
        base = super().to_dict()
        base.update({
            "page_id": self.page_id,
            "position": self.position,
            "section_type": self.section_type,
            "new_section_id": self._new_section_id,
            "content_length": len(self.content),
        })
        return base
