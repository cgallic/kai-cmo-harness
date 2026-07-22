"""Website health, local visibility, and page performance watchers.

Task 068 — Monitors the fundamental health of a business's web presence
and local search visibility, catching issues before they become
revenue-losing problems.

Watchers
--------
- **WebsiteHealthWatcher** (daily) — uptime, SSL, forms, tracking, phone.
- **LocalVisibilityWatcher** (weekly) — GBP status, NAP, rankings.
- **PagePerformanceWatcher** (weekly) — Core Web Vitals, mobile, 404s.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .framework import (
    FindingUrgency,
    Watcher,
    WatcherConfig,
    WatcherFinding,
    WatcherScheduleType,
    create_watcher_finding,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Live HTTP layer (stdlib only, per framework design principle #1)
# ---------------------------------------------------------------------------

_HTTP_TIMEOUT = 10.0
_MAX_HTML_BYTES = 500_000
_USER_AGENT = "KaiWatcher/1.0 (+https://github.com/cgallic/kai-cmo-harness)"


def _http_status(url: str, method: str = "HEAD") -> tuple[Optional[int], Optional[float]]:
    """Return ``(status_code, response_time_ms)`` for *url*.

    Falls back to GET when the server rejects HEAD with 405. Returns
    ``(None, None)`` when the host cannot be reached at all.
    """
    import socket
    import time
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, method=method, headers={"User-Agent": _USER_AGENT})
    start = time.monotonic()
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            return resp.status, (time.monotonic() - start) * 1000.0
    except urllib.error.HTTPError as exc:
        if exc.code == 405 and method == "HEAD":
            return _http_status(url, method="GET")
        return exc.code, (time.monotonic() - start) * 1000.0
    except (urllib.error.URLError, socket.timeout, OSError, ValueError) as exc:
        logger.debug("watcher fetch failed for %s: %s", url, exc)
        return None, None


def _fetch_html(url: str) -> Optional[str]:
    """GET *url* and return up to ``_MAX_HTML_BYTES`` of decoded HTML, or None."""
    import socket
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": _USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=_HTTP_TIMEOUT) as resp:
            return resp.read(_MAX_HTML_BYTES).decode("utf-8", errors="ignore")
    except (urllib.error.URLError, socket.timeout, OSError, ValueError) as exc:
        logger.debug("watcher HTML fetch failed for %s: %s", url, exc)
        return None


def _cert_expiry(domain: str) -> tuple[Optional[str], Optional[int]]:
    """Return ``(not_after_iso, days_remaining)`` for the TLS cert of *domain*.

    An expired certificate fails the default verification handshake, so that
    specific failure is reported as ``(None, 0)`` — expired now — rather than
    swallowed as unreachable.
    """
    import socket
    import ssl

    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, 443), timeout=_HTTP_TIMEOUT) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as tls:
                cert = tls.getpeercert()
        not_after = cert.get("notAfter") if cert else None
        if not not_after:
            return None, None
        expires = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(
            tzinfo=timezone.utc
        )
        return expires.date().isoformat(), (expires - datetime.now(timezone.utc)).days
    except ssl.SSLCertVerificationError as exc:
        if "expired" in str(exc).lower():
            return None, 0
        logger.debug("watcher cert verification failed for %s: %s", domain, exc)
        return None, None
    except (ssl.SSLError, socket.timeout, OSError, ValueError) as exc:
        logger.debug("watcher cert check failed for %s: %s", domain, exc)
        return None, None


_PHONE_STRIP = str.maketrans("", "", "()-. +")


def _normalize_phone(raw: str) -> str:
    """Reduce a phone string to its trailing 10 digits for comparison."""
    digits = "".join(ch for ch in raw.translate(_PHONE_STRIP) if ch.isdigit())
    return digits[-10:]


_TRACKING_PATTERNS = {
    "GA4": ("gtag(", "gtag/js", "google-analytics.com", "G-"),
    "GTM": ("googletagmanager.com", "gtm.js", "GTM-"),
    "other analytics": (
        "plausible.io", "fathom", "posthog", "matomo", "segment.com",
        "heap.io", "mixpanel", "umami", "fbevents.js", "clarity.ms",
    ),
}


# ============================================================================
# WebsiteHealthWatcher
# ============================================================================


class WebsiteHealthWatcher(Watcher):
    """Monitors website uptime, SSL, forms, tracking, and key page availability.

    Runs daily at 06:00 UTC. Relevant for every business archetype because
    every business with a website needs these checks.
    """

    name = "website_health"
    description = (
        "Monitors website uptime, SSL, forms, tracking, and key page availability"
    )
    schedule_type = WatcherScheduleType.DAILY.value
    archetype_relevance: List[str] = []  # All archetypes

    # Default set of key pages every business website should have
    DEFAULT_KEY_PAGES = ["/", "/about", "/contact", "/services", "/reviews"]

    # Pages whose downtime is more severe
    HIGH_PRIORITY_PAGES = {"/", "/contact"}

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Run all website health checks and collect findings.

        Parameters
        ----------
        business_profile:
            Business profile with at minimum ``id``, ``website_url``,
            ``phone``, and optionally ``key_pages``.
        workspace_state:
            Current workspace state providing integration data.
        """
        findings: List[WatcherFinding] = []
        business_id = self._get_business_id(business_profile)
        url = self._get_field(business_profile, "website_url", "")
        phone = self._get_field(business_profile, "phone", "")
        key_pages = self._get_field(
            business_profile, "key_pages", self.DEFAULT_KEY_PAGES
        )

        if not url:
            return findings

        # Fresh HTML cache per run so checks share one fetch per page
        self._html_cache: Dict[str, Optional[str]] = {}

        # --- Individual checks ---
        finding = self._check_site_uptime(url, business_id)
        if finding is not None:
            findings.append(finding)

        findings.extend(self._check_key_pages(url, key_pages, business_id))

        finding = self._check_ssl_certificate(url, business_id)
        if finding is not None:
            findings.append(finding)

        finding = self._check_forms_working(url, business_id)
        if finding is not None:
            findings.append(finding)

        if phone:
            finding = self._check_phone_number(url, phone, business_id)
            if finding is not None:
                findings.append(finding)

        finding = self._check_tracking_scripts(url, business_id)
        if finding is not None:
            findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_site_uptime(
        self,
        url: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check website uptime via HTTP HEAD request.

        Performs an HTTP HEAD request (GET fallback on 405) against *url* and
        evaluates the status code and response time.  A non-200 response or an
        unreachable host produces a critical finding requiring immediate
        operator attention.
        """
        status_code, response_time_ms = _http_status(url)

        if status_code is None:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Website is unreachable",
                description=(
                    f"The main website at {url} did not respond within "
                    f"{int(_HTTP_TIMEOUT)}s. Visitors cannot access the site, "
                    "which means zero lead capture until this is resolved."
                ),
                suppression_key=f"site_down_{_domain(url)}",
                urgency=FindingUrgency.IMMEDIATE.value,
                severity="critical",
                category="website_health",
                evidence={"url": url, "status_code": None, "response_time_ms": None},
                proposed_action={
                    "action_type": "alert_operator",
                    "description": "Alert the operator immediately — the website is unreachable.",
                    "auto_eligible": False,
                },
            )

        if status_code != 200:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Website is down or returning errors",
                description=(
                    f"The main website at {url} returned HTTP {status_code}. "
                    "Visitors cannot access the site, which means zero lead "
                    "capture until this is resolved."
                ),
                suppression_key=f"site_down_{_domain(url)}",
                urgency=FindingUrgency.IMMEDIATE.value,
                severity="critical",
                category="website_health",
                evidence={
                    "url": url,
                    "status_code": status_code,
                    "response_time_ms": response_time_ms,
                },
                proposed_action={
                    "action_type": "alert_operator",
                    "description": "Alert the operator immediately — the website is unreachable.",
                    "auto_eligible": False,
                },
            )
        return None

    def _check_key_pages(
        self,
        url: str,
        key_pages: List[str],
        business_id: str,
    ) -> List[WatcherFinding]:
        """Check each key page for non-200 responses.

        Issues an HTTP HEAD request (GET fallback on 405) against each path
        appended to *url* and flags any page returning a definite non-200
        status.  Pages that time out are skipped rather than flagged, to avoid
        false alarms from transient network conditions.  Homepage and /contact
        are rated severity "high"; others "medium".
        """
        findings: List[WatcherFinding] = []
        base = url.rstrip("/")
        page_statuses: Dict[str, int] = {}
        for page in key_pages:
            status, _rt = _http_status(f"{base}{page}")
            if status is not None:
                page_statuses[page] = status

        for page, status in page_statuses.items():
            if status != 200:
                severity = (
                    "high"
                    if page in self.HIGH_PRIORITY_PAGES
                    else "medium"
                )
                findings.append(
                    create_watcher_finding(
                        watcher_name=self.name,
                        business_id=business_id,
                        title=f"Key page '{page}' returning HTTP {status}",
                        description=(
                            f"The page {url}{page} returned HTTP {status}. "
                            "Visitors hitting this page will see an error."
                        ),
                        suppression_key=f"key_page_{_domain(url)}_{page}",
                        urgency=FindingUrgency.SOON.value,
                        severity=severity,
                        category="website_health",
                        evidence={
                            "url": f"{url}{page}",
                            "status_code": status,
                            "page_path": page,
                        },
                    )
                )
        return findings

    def _check_ssl_certificate(
        self,
        url: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check SSL certificate expiration date.

        Opens a TLS connection, extracts the ``notAfter`` field from the
        certificate, and compares it against the current date.  Thresholds:
        <= 0 days (expired, critical/immediate), <= 7 days (critical/immediate),
        <= 30 days (warning/soon).  Skipped for non-HTTPS sites.
        """
        import urllib.parse

        domain = _domain(url)
        if not url.lower().startswith("https://"):
            return None
        host = urllib.parse.urlparse(url).hostname or ""
        if not host:
            return None
        expiry_date, days_remaining = _cert_expiry(host)

        if days_remaining is not None:
            if days_remaining <= 0:
                severity = "critical"
                urgency = FindingUrgency.IMMEDIATE.value
                title = f"SSL certificate for {host} has expired"
                desc = (
                    f"The SSL certificate expired {abs(days_remaining)} days ago. "
                    "Browsers will show a security warning and most visitors will leave."
                )
            elif days_remaining <= 7:
                severity = "critical"
                urgency = FindingUrgency.IMMEDIATE.value
                title = f"SSL certificate for {host} expires in {days_remaining} days"
                desc = (
                    "The certificate is about to expire. Renew immediately to "
                    "avoid browser security warnings."
                )
            elif days_remaining <= 30:
                severity = "warning"
                urgency = FindingUrgency.SOON.value
                title = f"SSL certificate for {host} expires in {days_remaining} days"
                desc = (
                    "The certificate will expire within the next month. "
                    "Schedule a renewal to avoid disruption."
                )
            else:
                return None

            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=title,
                description=desc,
                suppression_key=f"ssl_expiring_{domain}",
                urgency=urgency,
                severity=severity,
                category="website_health",
                evidence={
                    "domain": host,
                    "expiry_date": expiry_date,
                    "days_remaining": days_remaining,
                },
            )
        return None

    def _check_forms_working(
        self,
        url: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check that form submission endpoints are reachable.

        Discovers ``<form>`` elements on the homepage, extracts their
        ``action`` URL, and issues a lightweight HEAD request to verify the
        endpoint exists.  Only definite failures (404/410/5xx) are flagged —
        endpoints that reject HEAD (405) are considered reachable.  A broken
        form means leads are silently lost.
        """
        import re
        import urllib.parse

        domain = _domain(url)
        form_url: Optional[str] = None
        endpoint: Optional[str] = None
        status_code: Optional[int] = None

        html = self._page_html(url)
        if html:
            match = re.search(r"<form[^>]+action=[\"']([^\"']+)[\"']", html, re.IGNORECASE)
            if match:
                action = match.group(1).strip()
                if action and not action.lower().startswith(("javascript:", "mailto:", "#")):
                    form_url = url
                    endpoint = urllib.parse.urljoin(url, action)
                    status_code, _rt = _http_status(endpoint)

        if status_code is not None and (status_code in (404, 410) or status_code >= 500):
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Contact form endpoint is unreachable",
                description=(
                    f"The form at {form_url} submits to {endpoint} which returned "
                    f"HTTP {status_code}. Leads submitted through this form are "
                    "being silently lost."
                ),
                suppression_key=f"form_broken_{domain}",
                urgency=FindingUrgency.IMMEDIATE.value,
                severity="critical",
                category="website_health",
                evidence={
                    "form_url": form_url,
                    "endpoint": endpoint,
                    "status_code": status_code,
                },
                proposed_action={
                    "action_type": "fix_form",
                    "description": (
                        "Verify the form handler URL is correct and the "
                        "server-side endpoint is operational."
                    ),
                    "auto_eligible": True,
                },
            )
        return None

    def _check_phone_number(
        self,
        url: str,
        expected_phone: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Compare the phone number on key pages to the expected number.

        Scrapes the homepage and contact page for the expected phone number
        (digit-normalized comparison) and for ``tel:`` links carrying a
        different number.  A missing or mismatched phone number is a direct
        lead-loss issue.  Pages that cannot be fetched are not flagged.
        """
        import re

        domain = _domain(url)
        found_phone: Optional[str] = None
        pages_checked: List[str] = ["/", "/contact"]

        expected_digits = _normalize_phone(expected_phone)
        base = url.rstrip("/")
        fetched_any = False
        tel_numbers: List[str] = []
        for page in pages_checked:
            html = self._page_html(f"{base}{page}" if page != "/" else url)
            if html is None:
                continue
            fetched_any = True
            page_digits = "".join(ch for ch in html if ch.isdigit())
            if expected_digits and expected_digits in page_digits:
                return None  # expected number is present — nothing to flag
            tel_numbers.extend(re.findall(r"href=[\"']tel:([^\"']+)[\"']", html, re.IGNORECASE))

        if not fetched_any or not expected_digits:
            return None  # cannot verify — do not raise a false alarm
        if tel_numbers:
            found_phone = tel_numbers[0].strip()

        if found_phone is None:
            # Phone number not found on any page
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Phone number missing from homepage",
                description=(
                    f"Expected phone number {expected_phone} was not found on "
                    f"any of the checked pages ({', '.join(pages_checked)}). "
                    "Visitors who prefer to call cannot reach the business."
                ),
                suppression_key=f"phone_missing_{domain}",
                urgency=FindingUrgency.SOON.value,
                severity="high",
                category="website_health",
                evidence={
                    "expected_phone": expected_phone,
                    "found_phone": None,
                    "pages_checked": pages_checked,
                },
            )
        elif found_phone != expected_phone:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Phone number on website does not match expected number",
                description=(
                    f"Found '{found_phone}' on the website but expected "
                    f"'{expected_phone}'. Calls may be routed to the wrong "
                    "destination."
                ),
                suppression_key=f"phone_mismatch_{domain}",
                urgency=FindingUrgency.IMMEDIATE.value,
                severity="critical",
                category="website_health",
                evidence={
                    "expected_phone": expected_phone,
                    "found_phone": found_phone,
                    "pages_checked": pages_checked,
                },
            )
        return None

    def _check_tracking_scripts(
        self,
        url: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check for the presence of GA4, GTM, or other tracking scripts.

        Fetches the homepage HTML and searches for known tracking script
        patterns (``gtag``, ``gtm.js``, GA4 measurement IDs, common
        third-party analytics).  Flags only when no known analytics tool is
        detected at all — missing analytics means the business is flying
        blind.  An unfetchable homepage is not flagged.
        """
        domain = _domain(url)
        scripts_expected = ["GA4", "GTM"]
        scripts_found: List[str] = []
        scripts_missing: List[str] = []

        html = self._page_html(url)
        if html is None:
            return None  # cannot verify — uptime check covers unreachable sites
        for label, needles in _TRACKING_PATTERNS.items():
            if any(needle in html for needle in needles):
                scripts_found.append(label)
        if not scripts_found:
            scripts_missing = scripts_expected

        if scripts_missing:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Google Analytics tracking not detected",
                description=(
                    f"Expected tracking scripts ({', '.join(scripts_expected)}) "
                    f"were not found on {url}. Without analytics the business "
                    "cannot measure traffic, conversions, or campaign performance."
                ),
                suppression_key=f"tracking_missing_{domain}",
                urgency=FindingUrgency.SOON.value,
                severity="high",
                category="website_health",
                evidence={
                    "scripts_expected": scripts_expected,
                    "scripts_found": scripts_found,
                    "scripts_missing": scripts_missing,
                },
            )
        return None

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.DAILY.value,
            schedule_time="06:00",
            archetype_relevance=[],
            max_findings_per_run=20,
            suppression_window_days=1,
        )

    # -- Helpers -----------------------------------------------------------

    def _page_html(self, page_url: str) -> Optional[str]:
        """Fetch *page_url* HTML once per run, caching the result (or None)."""
        cache = getattr(self, "_html_cache", None)
        if cache is None:
            cache = {}
            self._html_cache = cache
        if page_url not in cache:
            cache[page_url] = _fetch_html(page_url)
        return cache[page_url]

    @staticmethod
    def _get_business_id(profile: Any) -> str:
        if hasattr(profile, "id"):
            return str(profile.id)
        if isinstance(profile, dict):
            return str(profile.get("id", "unknown"))
        return "unknown"

    @staticmethod
    def _get_field(profile: Any, field: str, default: Any = None) -> Any:
        if hasattr(profile, field):
            return getattr(profile, field)
        if isinstance(profile, dict):
            return profile.get(field, default)
        return default


# ============================================================================
# LocalVisibilityWatcher
# ============================================================================


class LocalVisibilityWatcher(Watcher):
    """Monitors Google Business Profile health, NAP consistency, and local search visibility.

    Runs weekly on Mondays at 06:00 UTC.  Only relevant for ``local_service``
    and ``multi_location`` archetypes — businesses whose revenue depends on
    appearing in local search results.
    """

    name = "local_visibility"
    description = (
        "Monitors Google Business Profile health, NAP consistency, "
        "and local search visibility"
    )
    schedule_type = WatcherScheduleType.WEEKLY.value
    archetype_relevance = ["local_service", "multi_location"]

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Run all local visibility checks.

        Parameters
        ----------
        business_profile:
            Business profile containing GBP details, NAP data, and target
            service areas.
        workspace_state:
            Current workspace state with GSC/GBP connector data.
        """
        findings: List[WatcherFinding] = []
        business_id = self._get_business_id(business_profile)

        finding = self._check_gbp_status(business_profile, business_id)
        if finding is not None:
            findings.append(finding)

        finding = self._check_nap_consistency(business_profile, business_id)
        if finding is not None:
            findings.append(finding)

        finding = self._check_competitor_activity(business_profile, business_id)
        if finding is not None:
            findings.append(finding)

        finding = self._check_local_ranking(business_profile, business_id)
        if finding is not None:
            findings.append(finding)

        finding = self._check_service_area_coverage(business_profile, business_id)
        if finding is not None:
            findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_gbp_status(
        self,
        business_profile: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check Google Business Profile listing status.

        In production this would query the GBP API (via
        ``kai.connectors.analytics.gbp``) to verify the listing is active,
        verified, and not suspended.  A suspended listing means the business
        is invisible on Google Maps and the local pack.
        """
        # --- Stub: retrieve GBP status from connector ---
        gbp_status: Optional[str] = None  # "active", "suspended", "not_verified"
        listing_url: Optional[str] = None
        last_verified: Optional[str] = None

        if gbp_status == "suspended":
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Google Business Profile is suspended",
                description=(
                    "The GBP listing has been suspended. The business is "
                    "completely invisible on Google Maps and the local 3-pack. "
                    "Appeal immediately through the GBP dashboard."
                ),
                suppression_key=f"gbp_suspended_{business_id}",
                urgency=FindingUrgency.IMMEDIATE.value,
                severity="critical",
                category="local_visibility",
                evidence={
                    "gbp_status": gbp_status,
                    "listing_url": listing_url,
                    "last_verified": last_verified,
                },
            )
        elif gbp_status == "not_verified":
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title="Google Business Profile is not verified",
                description=(
                    "The GBP listing exists but has not been verified. Unverified "
                    "listings appear less frequently in search results and cannot "
                    "respond to reviews."
                ),
                suppression_key=f"gbp_not_verified_{business_id}",
                urgency=FindingUrgency.SOON.value,
                severity="high",
                category="local_visibility",
                evidence={
                    "gbp_status": gbp_status,
                    "listing_url": listing_url,
                    "last_verified": last_verified,
                },
            )
        return None

    def _check_nap_consistency(
        self,
        business_profile: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check Name, Address, Phone consistency across citation sources.

        In production this would query major citation/aggregator sources
        (Yelp, Apple Maps, Bing Places, Yellow Pages, BBB, industry-specific
        directories) and compare the NAP data against the canonical values in
        *business_profile*.
        """
        # --- Stub: compare NAP across citation sources ---
        inconsistent_sources: List[str] = []
        correct_nap: Optional[Dict[str, str]] = None
        found_variations: List[Dict[str, str]] = []

        if inconsistent_sources:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=(
                    f"NAP inconsistencies found on {len(inconsistent_sources)} "
                    "citation sources"
                ),
                description=(
                    "Name, Address, or Phone information differs across "
                    f"citation sources: {', '.join(inconsistent_sources)}. "
                    "Inconsistent NAP signals hurt local search rankings."
                ),
                suppression_key=f"nap_inconsistent_{business_id}",
                urgency=FindingUrgency.SCHEDULED.value,
                severity="medium",
                category="local_visibility",
                evidence={
                    "inconsistent_sources": inconsistent_sources,
                    "correct_nap": correct_nap,
                    "found_variations": found_variations,
                },
                proposed_action={
                    "action_type": "nap_correction",
                    "description": (
                        "Submit NAP corrections to each inconsistent source."
                    ),
                    "auto_eligible": False,
                },
            )
        return None

    def _check_competitor_activity(
        self,
        business_profile: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check for new competitor GBP listings in the service area.

        In production this would query Google Maps or a local search API for
        new GBP listings in the business's primary category within a defined
        radius.
        """
        # --- Stub: scan for new competitor listings ---
        new_competitor_name: Optional[str] = None
        location: Optional[str] = None
        distance_miles: Optional[float] = None
        category: Optional[str] = None

        if new_competitor_name is not None:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=f"New competitor detected: {new_competitor_name}",
                description=(
                    f"A new business '{new_competitor_name}' in category "
                    f"'{category}' appeared {distance_miles} miles away at "
                    f"{location}."
                ),
                suppression_key=f"new_competitor_{business_id}_{new_competitor_name}",
                urgency=FindingUrgency.INFORMATIONAL.value,
                severity="low",
                category="local_visibility",
                evidence={
                    "new_competitor_name": new_competitor_name,
                    "location": location,
                    "distance_miles": distance_miles,
                    "category": category,
                },
            )
        return None

    def _check_local_ranking(
        self,
        business_profile: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check local search ranking positions from Google Search Console.

        In production this would query GSC (via ``kai.connectors.analytics.gsc``)
        for branded and service-area queries, comparing the current average
        position to the previous period.
        """
        # --- Stub: pull ranking data from GSC connector ---
        queries_dropped: List[str] = []
        average_position_change: Optional[float] = None
        affected_pages: List[str] = []

        if queries_dropped:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=(
                    f"Local ranking drops detected on {len(queries_dropped)} queries"
                ),
                description=(
                    "Average position dropped by "
                    f"{abs(average_position_change or 0):.1f} positions on "
                    f"queries: {', '.join(queries_dropped[:5])}. "
                    "This may reduce impressions and calls from local search."
                ),
                suppression_key=f"ranking_drop_{business_id}",
                urgency=FindingUrgency.SOON.value,
                severity="medium",
                category="local_visibility",
                evidence={
                    "queries_dropped": queries_dropped,
                    "average_position_change": average_position_change,
                    "affected_pages": affected_pages,
                },
            )
        return None

    def _check_service_area_coverage(
        self,
        business_profile: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check appearance in search results for target service areas.

        In production this would query GSC or a SERP API for each target
        service area keyword (e.g., "plumber in [city]") and determine
        whether the business appears.
        """
        # --- Stub: check coverage per target area ---
        target_areas: List[str] = []
        areas_covered: List[str] = []
        areas_missing: List[str] = []

        if areas_missing:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=(
                    f"No search coverage in {len(areas_missing)} target service areas"
                ),
                description=(
                    f"The business does not appear in search results for: "
                    f"{', '.join(areas_missing[:5])}. Creating dedicated service "
                    "area pages can close these gaps."
                ),
                suppression_key=f"area_gap_{business_id}",
                urgency=FindingUrgency.SCHEDULED.value,
                severity="medium",
                category="local_visibility",
                evidence={
                    "target_areas": target_areas,
                    "areas_covered": areas_covered,
                    "areas_missing": areas_missing,
                },
                proposed_action={
                    "action_type": "create_service_area_pages",
                    "description": (
                        "Create service area pages for each missing area to "
                        "capture local search traffic."
                    ),
                    "auto_eligible": True,
                },
            )
        return None

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.WEEKLY.value,
            schedule_time="monday_06:00",
            archetype_relevance=list(self.archetype_relevance),
            max_findings_per_run=15,
            suppression_window_days=14,
        )

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _get_business_id(profile: Any) -> str:
        if hasattr(profile, "id"):
            return str(profile.id)
        if isinstance(profile, dict):
            return str(profile.get("id", "unknown"))
        return "unknown"


# ============================================================================
# PagePerformanceWatcher
# ============================================================================


class PagePerformanceWatcher(Watcher):
    """Monitors Core Web Vitals, mobile usability, and page errors.

    Runs weekly on Tuesdays at 06:00 UTC.  Relevant for all archetypes.
    CWV changes slowly, so the suppression window is 30 days.
    """

    name = "page_performance"
    description = (
        "Monitors Core Web Vitals, mobile usability, and page errors"
    )
    schedule_type = WatcherScheduleType.WEEKLY.value
    archetype_relevance: List[str] = []  # All archetypes

    # Core Web Vitals thresholds (Google "needs improvement" boundary)
    CWV_THRESHOLDS = {
        "LCP": {"value": 2.5, "unit": "s"},
        "INP": {"value": 200, "unit": "ms"},
        "CLS": {"value": 0.1, "unit": ""},
    }

    def check(
        self,
        business_profile: Any,
        workspace_state: Any,
    ) -> List[WatcherFinding]:
        """Run all page performance checks.

        Parameters
        ----------
        business_profile:
            Business profile with ``id`` and ``website_url``.
        workspace_state:
            Current workspace state with GSC/CrUX data.
        """
        findings: List[WatcherFinding] = []
        business_id = self._get_business_id(business_profile)
        url = self._get_field(business_profile, "website_url", "")

        if not url:
            return findings

        findings.extend(self._check_core_web_vitals(url, business_id))

        finding = self._check_mobile_usability(url, business_id)
        if finding is not None:
            findings.append(finding)

        finding = self._check_404_errors(business_profile, business_id)
        if finding is not None:
            findings.append(finding)

        return findings

    # -- Private checks ----------------------------------------------------

    def _check_core_web_vitals(
        self,
        url: str,
        business_id: str,
    ) -> List[WatcherFinding]:
        """Check LCP, INP, and CLS via CrUX API or PageSpeed Insights.

        In production this would call the Chrome UX Report API or the
        PageSpeed Insights API to get field data for the origin.  A finding
        is generated per metric that exceeds Google's "needs improvement"
        threshold.
        """
        findings: List[WatcherFinding] = []
        domain = _domain(url)

        # --- Stub: retrieve CWV data from CrUX/PSI connector ---
        # metrics: Dict[str, Dict] = {"LCP": {"value": 3.1, "percentile": "p75"}, ...}
        metrics: Dict[str, Dict[str, Any]] = {}

        metric_titles = {
            "LCP": "Largest Contentful Paint exceeds threshold",
            "INP": "Interaction to Next Paint exceeds threshold",
            "CLS": "Cumulative Layout Shift exceeds threshold",
        }

        for metric_name, data in metrics.items():
            threshold_info = self.CWV_THRESHOLDS.get(metric_name)
            if threshold_info is None:
                continue

            current_value = data.get("value")
            if current_value is None:
                continue

            if current_value > threshold_info["value"]:
                findings.append(
                    create_watcher_finding(
                        watcher_name=self.name,
                        business_id=business_id,
                        title=metric_titles.get(
                            metric_name,
                            f"{metric_name} exceeds threshold",
                        ),
                        description=(
                            f"{metric_name} is {current_value}"
                            f"{threshold_info['unit']} (threshold: "
                            f"{threshold_info['value']}"
                            f"{threshold_info['unit']}). This affects "
                            "search ranking and user experience."
                        ),
                        suppression_key=f"cwv_{metric_name}_{domain}",
                        urgency=FindingUrgency.SCHEDULED.value,
                        severity="medium",
                        category="page_performance",
                        evidence={
                            "metric_name": metric_name,
                            "current_value": current_value,
                            "threshold": threshold_info["value"],
                            "percentile": data.get("percentile", "p75"),
                            "page_url": url,
                        },
                    )
                )
        return findings

    def _check_mobile_usability(
        self,
        url: str,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check for mobile usability issues via Search Console API.

        In production this would call the GSC Mobile Usability report
        endpoint to list issues like viewport not set, text too small,
        clickable elements too close, or content wider than screen.
        """
        domain = _domain(url)
        # --- Stub: retrieve mobile usability issues from GSC ---
        issues_found: List[str] = []
        pages_affected: int = 0
        issue_types: List[str] = []

        if issues_found:
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=f"Mobile usability issues detected ({len(issues_found)} issues)",
                description=(
                    f"{len(issues_found)} mobile usability issues affecting "
                    f"{pages_affected} pages. Issues: {', '.join(issue_types[:3])}. "
                    "Mobile-friendliness is a ranking factor and most local "
                    "searches happen on phones."
                ),
                suppression_key=f"mobile_usability_{domain}",
                urgency=FindingUrgency.SCHEDULED.value,
                severity="medium",
                category="page_performance",
                evidence={
                    "issues_found": issues_found,
                    "pages_affected": pages_affected,
                    "issue_types": issue_types,
                },
            )
        return None

    def _check_404_errors(
        self,
        business_profile: Any,
        business_id: str,
    ) -> Optional[WatcherFinding]:
        """Check Google Search Console for pages returning 404 errors.

        In production this would query the GSC Coverage report for pages
        with ``Excluded - Not found (404)`` status, focusing on pages that
        previously received traffic.
        """
        url = self._get_field(business_profile, "website_url", "")
        domain = _domain(url)
        # --- Stub: retrieve 404 data from GSC connector ---
        new_404_urls: List[str] = []
        total_404_count: int = 0
        high_traffic_404s: List[str] = []

        if new_404_urls:
            severity = "high" if high_traffic_404s else "medium"
            return create_watcher_finding(
                watcher_name=self.name,
                business_id=business_id,
                title=f"{len(new_404_urls)} new 404 errors detected",
                description=(
                    f"{len(new_404_urls)} pages are now returning 404 errors "
                    f"(total 404s: {total_404_count}). "
                    + (
                        f"High-traffic pages affected: {', '.join(high_traffic_404s[:3])}."
                        if high_traffic_404s
                        else "No high-traffic pages affected yet."
                    )
                ),
                suppression_key=f"404_errors_{domain}",
                urgency=FindingUrgency.SOON.value,
                severity=severity,
                category="page_performance",
                evidence={
                    "new_404_urls": new_404_urls,
                    "total_404_count": total_404_count,
                    "high_traffic_404s": high_traffic_404s,
                },
                proposed_action={
                    "action_type": "setup_redirects",
                    "description": (
                        "Set up 301 redirects for important pages to preserve "
                        "link equity and user experience."
                    ),
                    "auto_eligible": False,
                },
            )
        return None

    def get_default_config(self) -> WatcherConfig:
        return WatcherConfig(
            watcher_name=self.name,
            enabled=True,
            schedule_type=WatcherScheduleType.WEEKLY.value,
            schedule_time="tuesday_06:00",
            archetype_relevance=[],
            max_findings_per_run=10,
            suppression_window_days=30,
        )

    # -- Helpers -----------------------------------------------------------

    @staticmethod
    def _get_business_id(profile: Any) -> str:
        if hasattr(profile, "id"):
            return str(profile.id)
        if isinstance(profile, dict):
            return str(profile.get("id", "unknown"))
        return "unknown"

    @staticmethod
    def _get_field(profile: Any, field: str, default: Any = None) -> Any:
        if hasattr(profile, field):
            return getattr(profile, field)
        if isinstance(profile, dict):
            return profile.get(field, default)
        return default


# ============================================================================
# Helpers
# ============================================================================


def _domain(url: str) -> str:
    """Extract a domain-like key from a URL for use in suppression keys."""
    cleaned = url.replace("https://", "").replace("http://", "")
    return cleaned.split("/")[0].replace(".", "_")
