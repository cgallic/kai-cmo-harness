# Task 013: Define audit data models

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 3. Audit and Diagnosis
**Priority:** P1
**Depends on:** 001
**Estimated complexity:** Large

## Context

The audit system is Kai's diagnostic engine — it examines a business's marketing posture and produces structured findings that downstream systems (proposal generation, action planning, operator review) consume. The existing `kai/runtime/audit.py` has a prototype with FindingSeverity, FindingPriority, and AuditCategory enums, plus basic finding/result structures. The canonical audit models at `kai/models/audit.py` need to be more comprehensive, archetype-aware, and designed for multi-engine composition (multiple audit engines contribute findings to a single AuditResult).

The key design principle is that audit findings are structured data, not prose. Every finding has an ID, category, severity, evidence, recommendation, and estimated impact. Downstream systems should never need to re-parse prose to understand what was found.

## Scope

Build `kai/models/audit.py` with comprehensive audit data models that all audit engines (Tasks 014-021) will use as their output format.

## Detailed Requirements

### File: `kai/models/audit.py`

Use the same Pydantic/fallback import pattern as `gateway/models.py`.

**Enum: `FindingSeverity`**
- `CRITICAL` — actively losing revenue or trust right now; blocks meaningful operation
- `HIGH` — significant opportunity loss; major gap in marketing posture
- `MEDIUM` — notable optimization opportunity; moderate impact
- `LOW` — minor polish item; nice-to-have improvement
- `INFO` — observation or context; no action required

**Enum: `FindingPriority`**
- `P0` — fix this week (maps from CRITICAL)
- `P1` — fix this month (maps from HIGH)
- `P2` — fix this quarter (maps from MEDIUM)
- `P3` — backlog (maps from LOW/INFO)

**Enum: `FindingSource`**
- `STATIC` — determined from profile data alone (no live data needed)
- `CONNECTED` — determined from connected integration data (analytics, reviews, etc.)
- `INFERRED` — inferred from indirect signals (not directly observed)
- `MISSING_DATA` — the audit could not assess this area due to missing data

**Enum: `EffortLevel`**
- `QUICK_WIN` — can be done in under 1 hour
- `MODERATE` — requires 1-8 hours of work
- `SIGNIFICANT` — requires a week or more
- `ONGOING` — requires continuous effort (not a one-time fix)

**Enum: `ImpactLevel`**
- `HIGH` — expected to meaningfully move primary KPIs
- `MEDIUM` — expected to improve secondary KPIs or user experience
- `LOW` — marginal improvement expected

**Model: `Evidence`**
- `evidence_type: str` — one of: "text", "url", "screenshot", "metric", "comparison", "checklist_item", "missing_data"
- `value: str` — the evidence content (text, URL, metric value, etc.)
- `context: Optional[str]` — additional context explaining why this evidence matters
- `source_label: Optional[str]` — where this evidence came from (e.g., "Google Business Profile", "Website homepage")

**Model: `AuditFinding`**
- `id: str` — unique finding identifier (generate with uuid4 or sequential like "F001")
- `category: str` — audit category this finding belongs to (e.g., "website_conversion", "local_seo")
- `subcategory: Optional[str]` — more specific classification within the category
- `severity: str` — FindingSeverity value
- `priority: str` — FindingPriority value (auto-computed from severity by default, can be overridden)
- `title: str` — one-line summary of the finding (max 100 chars)
- `description: str` — detailed explanation of what was found and why it matters
- `evidence: List[Evidence]` — supporting evidence for this finding
- `recommendation: str` — specific, actionable recommendation to address this finding
- `estimated_impact: str` — ImpactLevel value
- `effort: str` — EffortLevel value
- `source: str` — FindingSource value
- `business_stage_relevance: List[str]` — which business stages this finding is most relevant for
- `archetype_relevance: List[str]` — which archetypes this finding is most relevant for
- `related_findings: List[str]` — IDs of other findings that are related
- `tags: List[str]` — freeform tags for filtering and grouping
- `kaicalls_relevant: bool = False` — whether this finding relates to phone lead capture (flags for KaiCalls recommendation)
- `metadata: Dict[str, Any]` — catch-all for finding-specific data

**Model: `CategoryScorecard`**
- `category: str` — audit category ID
- `category_display_name: str` — human-readable category name
- `score: float` — 0-100 score for this category
- `max_score: float = 100.0` — maximum possible score
- `weight: float = 1.0` — weighting factor for overall score calculation
- `findings_count: int` — total findings in this category
- `critical_count: int` — CRITICAL findings
- `high_count: int` — HIGH findings
- `medium_count: int` — MEDIUM findings
- `low_count: int` — LOW findings
- `info_count: int` — INFO findings
- `missing_data_count: int` — MISSING_DATA findings
- `top_recommendations: List[str]` — top 3 recommendations for this category
- `quick_wins: List[str]` — quick win IDs in this category

**Model: `MissingDataFlag`**
- `field_path: str` — what data is missing (dot-notation path)
- `impact_description: str` — what the audit can't assess without this data
- `affected_categories: List[str]` — which audit categories are impacted
- `how_to_provide: str` — instructions for the operator to provide this data

**Model: `AuditResult`**
- `audit_id: str` — unique audit identifier
- `business_id: str` — BusinessProfile.id
- `audit_type: str` — e.g., "full_marketing_audit", "website_conversion_audit", "local_seo_audit"
- `archetype: Optional[str]` — archetype used for this audit
- `overlays_applied: List[str]` — overlays applied during this audit
- `timestamp: str` — ISO timestamp of when the audit was run
- `findings: List[AuditFinding]` — all findings from all engines
- `category_scores: Dict[str, CategoryScorecard]` — scorecards per category
- `overall_health_score: float` — 0-100 weighted composite score
- `missing_data_flags: List[MissingDataFlag]` — what the audit couldn't assess
- `executive_summary: str` — 3-5 sentence summary of the audit results
- `top_priorities: List[str]` — ordered list of top 5 finding IDs to address first
- `quick_wins: List[str]` — finding IDs that are quick wins (high impact, low effort)
- `total_findings: int` — count of all findings
- `critical_count: int` — total CRITICAL findings across all categories
- `high_count: int` — total HIGH findings
- `engines_run: List[str]` — which audit engines contributed to this result
- `metadata: Dict[str, Any]` — catch-all

**Utility Functions:**

1. **`create_finding(category: str, severity: str, title: str, description: str, recommendation: str, **kwargs) -> AuditFinding`**
   - Factory function for creating findings with auto-generated ID and auto-mapped priority
   - Priority mapping: CRITICAL->P0, HIGH->P1, MEDIUM->P2, LOW->P3, INFO->P3
   - Accepts all other AuditFinding fields as kwargs
   - Generates UUID-based ID if not provided

2. **`create_missing_data_finding(category: str, field_path: str, impact_description: str, how_to_provide: str) -> AuditFinding`**
   - Specialized factory for missing-data findings
   - Sets source = "MISSING_DATA", severity = "INFO" (or "WARNING" if the missing data is critical)
   - Sets evidence to a single Evidence object of type "missing_data"

3. **`compute_category_scorecard(category: str, findings: List[AuditFinding], display_name: str, weight: float = 1.0) -> CategoryScorecard`**
   - Given all findings for a category, compute the scorecard
   - Score = 100 - (critical * 25 + high * 15 + medium * 8 + low * 3)
   - Clamp to 0-100
   - Count findings by severity
   - Extract top 3 recommendations from highest-severity findings
   - Extract quick_win IDs (findings where effort = QUICK_WIN and impact = HIGH or MEDIUM)

4. **`compute_overall_score(scorecards: Dict[str, CategoryScorecard]) -> float`**
   - Weighted average of all category scores
   - Use each scorecard's weight field
   - Return 0-100

5. **`compile_audit_result(business_id: str, audit_type: str, engine_findings: Dict[str, List[AuditFinding]], archetype: Optional[str] = None, overlays: Optional[List[str]] = None) -> AuditResult`**
   - Main assembly function: takes findings from multiple engines (keyed by engine name)
   - Computes category scorecards for each unique category across all findings
   - Computes overall health score
   - Extracts missing data flags from MISSING_DATA findings
   - Generates executive_summary based on scores and critical findings
   - Identifies top_priorities (highest severity, highest impact findings)
   - Identifies quick_wins
   - Returns complete AuditResult

6. **`severity_to_priority(severity: str) -> str`**
   - Map severity to default priority
   - CRITICAL -> P0, HIGH -> P1, MEDIUM -> P2, LOW -> P3, INFO -> P3

7. **`format_finding_summary(finding: AuditFinding) -> str`**
   - One-line formatted string: "[SEVERITY] [CATEGORY] — TITLE (EFFORT, IMPACT)"
   - For display in CLI or reports

### Update `kai/models/__init__.py`
- Add imports for all audit models
- Extend `__all__`

## Output Files

- `kai/models/audit.py`
- `kai/models/__init__.py` (update)

## Acceptance Criteria

- [ ] `audit.py` contains all 5 enums (FindingSeverity, FindingPriority, FindingSource, EffortLevel, ImpactLevel)
- [ ] `audit.py` contains all 5 data models (Evidence, AuditFinding, CategoryScorecard, MissingDataFlag, AuditResult)
- [ ] All 7 utility functions are implemented
- [ ] `AuditFinding` has all listed fields including `kaicalls_relevant` flag
- [ ] `AuditResult` has `missing_data_flags` for the "unknowns preserved" philosophy
- [ ] `create_finding()` auto-generates ID and auto-maps severity to priority
- [ ] `create_missing_data_finding()` creates properly typed missing-data findings
- [ ] `compute_category_scorecard()` implements the scoring formula: 100 - (critical*25 + high*15 + medium*8 + low*3)
- [ ] `compile_audit_result()` takes multi-engine findings and assembles a complete result
- [ ] `format_finding_summary()` produces clean one-line output
- [ ] Uses Pydantic/fallback import pattern from `gateway/models.py`
- [ ] `kai/models/__init__.py` updated with new exports

## Reference Materials

- `kai/runtime/audit.py` — existing audit prototype (preserve compatibility concepts)
- `kai/models/business_profile.py` (Task 001) — the profile being audited
- `gateway/models.py` — Pydantic import fallback pattern
- `CLAUDE.md` — quality gate philosophy
- `knowledge/checklists/cro-audit-checklist.md` — example of audit checklist structure
