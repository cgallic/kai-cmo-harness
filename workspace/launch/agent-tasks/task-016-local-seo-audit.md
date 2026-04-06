# Task 016: Build local SEO and visibility audit engine

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P1
**Depends on:** 013
**Estimated complexity:** Medium

## Context

Local SEO determines whether a business shows up when nearby customers search for their services. For local-service and multi-location businesses, this is often the single most important marketing channel — Google Maps and local search results drive the majority of new customer discovery. This audit engine examines GBP completeness, NAP consistency, local schema markup readiness, service area page strategy, citation health, and local keyword targeting. For multi-location businesses, it scores each location independently and identifies fleet-level issues.

## Scope

Build `kai/audits/local_seo.py` with a local SEO audit engine that examines BusinessProfile geography, channel, and content data to produce structured AuditFindings.

## Detailed Requirements

### File: `kai/audits/local_seo.py`

**Function: `audit_local_seo(profile: "BusinessProfile", connected_data: Optional[Dict[str, Any]] = None) -> List[AuditFinding]`**

Main entry point. Returns List[AuditFinding]. Primarily relevant for local-service and multi-location archetypes, but generates advisory findings for any business with a physical presence.

**Check 1: GBP Existence and Completeness**
- Check profile.channels for a "gbp" entry
- If no GBP channel found:
  - Local-service/multi-location archetype -> CRITICAL: "No Google Business Profile detected — GBP is the #1 local discovery channel"
  - Other archetypes with physical locations -> HIGH: "Business has physical locations but no Google Business Profile"
- If GBP exists but is_active is False -> HIGH: "Google Business Profile exists but is inactive — an inactive GBP loses ranking signals"
- If GBP exists and is active -> check for completeness indicators in notes/metadata
- Recommendation: "Claim, verify, and fully complete your Google Business Profile. Include: business description, all services, photos, hours, and service area."

**Check 2: GBP Categories**
- If connected_data has GBP category info: check that primary category matches the business's main service
- If not available: generate advisory MISSING_DATA finding
- Recommendation: "Set your primary GBP category to your most important service. Add secondary categories for all other services offered."

**Check 3: NAP Consistency**
- NAP = Name, Address, Phone — must be identical across all online listings
- Check that profile has a consistent name, address, and phone:
  - If identity.business_name is set AND geography.locations has at least one location with address AND identity.phone is set -> check that these can form a consistent NAP
  - If phone differs between identity.phone and location.phone -> WARNING: "Inconsistent phone numbers between business profile and location — NAP inconsistency hurts local rankings"
- If business_name contains variations (DBA vs legal name) -> WARNING: "Business uses multiple names — ensure consistent name across all directories"
- For multi-location: each location should have its own consistent NAP
  - Check each location for completeness (address, phone)
  - If any location is missing address or phone -> HIGH: "Location '{name}' is missing {field} — incomplete location data breaks NAP consistency"

**Check 4: Local Schema Markup Readiness**
- Cannot verify schema markup from profile alone — generate advisory finding
- Recommendation: "Implement LocalBusiness schema markup on every location page. Include: name, address, phone, hours, geo coordinates, service area, and aggregate rating."
- For multi-location: "Each location page should have its own LocalBusiness schema with unique address and phone"
- Severity: MEDIUM (advisory)

**Check 5: Service Area Pages**
- If archetype is local-service:
  - Check profile.geography.service_areas
  - If service_areas is empty -> HIGH: "No service areas defined — service area pages are the foundation of local SEO"
  - If service_areas has 1-2 items -> MEDIUM: "Only {n} service area(s) defined — expand to cover all primary markets with dedicated pages"
  - If service_areas has 3+ items -> INFO: "Service areas defined for {n} markets — ensure each has a dedicated, unique content page"
- For multi-location: each location should effectively have its own service area content
  - If locations exist but service_areas is empty -> HIGH: "Locations exist but no service area strategy defined"

**Check 6: Location Pages**
- For multi-location archetype:
  - Count locations in profile.geography.locations
  - Recommend one dedicated website page per location
  - If locations > 1: "Ensure {n} unique location pages exist — each with unique content, not just address swaps"
  - Severity: HIGH (location pages are essential for multi-location local SEO)
- For local-service with single location:
  - Advisory: "Create a dedicated 'About Our [City] Office' or 'Service Areas' page"
  - Severity: MEDIUM

**Check 7: Local Keyword Targeting Readiness**
- Check that profile has enough data to build local keyword targets:
  - Needs: offers (what they do) + service_areas (where they do it)
  - If both present -> INFO: "Local keyword targets can be built: [service] + [location] combinations"
  - If offers present but service_areas missing -> HIGH: "Service areas needed to build local keyword targeting"
  - If offers missing -> CRITICAL: "Offers not defined — cannot build keyword strategy without knowing what the business does"
- Example keyword patterns: "{service} in {city}", "{service} near {neighborhood}", "best {service} {city}"

**Check 8: Citation Consistency**
- If connected_data includes citation audit data: analyze
- If not: generate advisory finding
- Recommendation: "Audit citations on major directories (Google, Yelp, Bing, Apple Maps, Facebook, Yellow Pages, BBB, Nextdoor) for NAP consistency"
- Severity: MEDIUM

**Check 9: Local Link Profile Indicators**
- If connected_data includes backlink data: analyze local link signals
- If not: generate advisory finding
- Recommendation: "Build local links through: chamber of commerce membership, local sponsorships, local news coverage, partner cross-links, and community involvement"
- Severity: LOW (advisory)

**Check 10: Per-Location Scoring (multi-location only)**
- If archetype is multi-location and geography.locations has 2+ items:
  - Generate a finding for each location summarizing its local SEO readiness
  - Score each location on: has address (Y/N), has phone (Y/N), has GBP URL (Y/N), has hours (Y/N)
  - Identify the weakest location and flag it: "Location '{name}' has the weakest local SEO profile — prioritize"
  - Identify the strongest location: "Location '{name}' is the best-optimized — use as template for others"

**Scoring Function:**

**`score_local_seo(findings: List[AuditFinding]) -> float`**
- Score 0-100 using the standard formula
- For multi-location: weight per-location findings proportionally

**Helper Function:**

**`assess_location_completeness(location: Dict[str, Any]) -> Dict[str, bool]`**
- Check a single location dict for: has_address, has_phone, has_gbp, has_hours, has_name
- Return dict of booleans

## Output Files

- `kai/audits/local_seo.py`

## Acceptance Criteria

- [ ] `local_seo.py` implements `audit_local_seo()` with all 10 checks
- [ ] GBP existence check is CRITICAL for local-service and multi-location archetypes
- [ ] NAP consistency is checked across identity and location data
- [ ] Service area page recommendations are generated for local-service archetype
- [ ] Multi-location archetype gets per-location scoring (Check 10)
- [ ] Local keyword targeting readiness check validates offers + service_areas combination
- [ ] MISSING_DATA findings are generated for schema markup, citations, and link profile when not available
- [ ] `score_local_seo()` scoring function exists
- [ ] `assess_location_completeness()` helper checks all location fields
- [ ] All findings have complete fields including category = "local_seo"
- [ ] Imports from `kai.models.audit` and `kai.models.business_profile`

## Reference Materials

- `kai/models/audit.py` (Task 013) — audit data models
- `kai/models/business_profile.py` (Task 001) — geography and channel fields
- `knowledge/checklists/local-service-business-checklist.md` — local service SEO items
- `knowledge/checklists/seo-checklist.md` — SEO checklist
- `knowledge/playbooks/local-seo-gbp-optimization.md` — GBP optimization playbook
- `knowledge/playbooks/semantic-seo-methodology.md` — SEO methodology
