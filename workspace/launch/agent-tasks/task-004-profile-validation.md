# Task 004: Build profile validation

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 1. Workspace and Business Understanding
**Priority:** P2
**Depends on:** 001
**Estimated complexity:** Medium

## Context

A BusinessProfile can be partially filled — operators may not have every data point at onboarding time. The validation layer's job is to assess what we know, what we don't know, and whether we have enough to proceed with specific operations. Critically, validation must never hallucinate or fill in missing data. The system must know what it doesn't know, and communicate that clearly to downstream consumers (audits, proposals, archetypes). This is the "unknowns preserved" philosophy.

## Scope

Build `kai/validation/profile_validator.py` and `kai/validation/__init__.py` that validate a BusinessProfile against archetype-specific requirements and return structured validation results with severity levels.

## Detailed Requirements

### File: `kai/validation/__init__.py`
- Package init with imports and `__all__`

### File: `kai/validation/profile_validator.py`

**Data Models (use same Pydantic/fallback pattern as gateway/models.py):**

`FieldValidationStatus` — Enum with values:
- `PRESENT` — field has a value
- `MISSING` — field is None/empty and is needed
- `INVALID` — field has a value but it fails validation rules
- `INFERRED` — field was inferred from other data (flagged, not treated as ground truth)
- `UNKNOWN` — field's status cannot be determined

`ValidationSeverity` — Enum with values:
- `CRITICAL` — blocks operation; the system cannot meaningfully proceed without this
- `WARNING` — degrades quality of output; system can proceed but results will be weaker
- `INFO` — nice to have; improves output but not essential

`FieldValidation` — Model with fields:
- `field_path: str` — dot-notation path, e.g., "identity.business_name"
- `status: FieldValidationStatus`
- `severity: ValidationSeverity`
- `message: str` — human-readable explanation
- `value_summary: Optional[str]` — brief summary of the current value (for PRESENT/INVALID)

`ValidationResult` — Model with fields:
- `profile_id: str`
- `archetype: Optional[str]` — which archetype rules were applied
- `timestamp: str` — ISO timestamp of validation
- `is_sufficient: bool` — whether the profile has enough data for basic operation
- `total_fields_checked: int`
- `present_count: int`
- `missing_count: int`
- `invalid_count: int`
- `critical_issues: List[FieldValidation]` — CRITICAL severity items
- `warnings: List[FieldValidation]` — WARNING severity items
- `info_items: List[FieldValidation]` — INFO severity items
- `all_validations: List[FieldValidation]` — complete list
- `completeness_score: float` — 0.0 to 1.0, percentage of fields that are present
- `readiness_summary: str` — one-sentence human-readable summary

**Core Functions:**

1. **`validate_profile(profile: "BusinessProfile", archetype: Optional[str] = None) -> ValidationResult`**
   - Main entry point
   - If archetype is None, use profile.classification.archetype (if set), otherwise validate against universal requirements only
   - Check every field in the profile for presence/validity
   - Apply archetype-specific rules on top of universal rules
   - Compute completeness_score as (present_count / total_fields_checked)
   - Set is_sufficient = True only if zero CRITICAL issues
   - Generate readiness_summary based on results

2. **`_validate_universal(profile) -> List[FieldValidation]`**
   - Universal fields required for ANY business:
     - CRITICAL: identity.business_name (must be non-empty string)
     - CRITICAL: classification.industry OR classification.vertical (at least one)
     - WARNING: identity.website_url (needed for most operations)
     - WARNING: identity.phone OR identity.email (at least one contact method)
     - WARNING: at least one item in offers list
     - WARNING: at least one item in personas list
     - INFO: identity.tagline
     - INFO: identity.elevator_pitch
     - INFO: brand_voice.tone_descriptors (non-empty list)
     - INFO: goals.primary_goals (non-empty list)
     - INFO: budget.monthly_marketing_budget (set)

3. **`_validate_local_service(profile) -> List[FieldValidation]`**
   - Archetype = "local-service" specific requirements:
     - CRITICAL: geography.service_areas is non-empty OR geography.locations is non-empty
     - CRITICAL: identity.phone (local service businesses MUST have a phone number)
     - WARNING: geography.locations has at least one location with address
     - WARNING: at least one location has gbp_url set
     - WARNING: trust.years_in_business is set
     - WARNING: trust.licenses is non-empty (many local services require licensing)
     - INFO: trust.insurance_details is set
     - INFO: geography.is_mobile is explicitly set (not just default)
     - INFO: at least one offer has price_range set

4. **`_validate_ecommerce(profile) -> List[FieldValidation]`**
   - Archetype = "ecommerce" specific requirements:
     - CRITICAL: offers list has at least one item
     - CRITICAL: identity.website_url is set
     - WARNING: at least one offer has price_range set
     - WARNING: sales_cycle.buyer_type is set
     - WARNING: at least one channel in channels list is an ecommerce platform
     - WARNING: goals.target_kpis has at least one KPI
     - INFO: brand_voice.tone_descriptors is non-empty
     - INFO: trust.testimonials is non-empty

5. **`_validate_professional_services(profile) -> List[FieldValidation]`**
   - Archetype = "professional-services" specific:
     - CRITICAL: offers has at least one item describing a service
     - WARNING: trust.case_studies is non-empty
     - WARNING: trust.certifications is non-empty
     - WARNING: personas has at least one item with decision_makers info
     - WARNING: sales_cycle.sales_cycle_length is set
     - INFO: trust.notable_clients is non-empty
     - INFO: brand_voice.competitor_differentiation is set

6. **`_validate_multi_location(profile) -> List[FieldValidation]`**
   - Archetype = "multi-location" specific:
     - CRITICAL: geography.locations has at least 2 items
     - WARNING: every location in geography.locations has address and phone
     - WARNING: every location has gbp_url
     - WARNING: brand_voice has tone_descriptors (brand consistency needs)
     - INFO: each location has its own hours set

7. **`_check_field(profile, field_path: str, severity: ValidationSeverity, message: str) -> FieldValidation`**
   - Helper that navigates dot-notation path on the profile object
   - Returns FieldValidation with appropriate status based on whether the value is present, None, empty list, empty string, etc.
   - For list fields: empty list = MISSING
   - For string fields: None or "" = MISSING
   - For numeric fields: None = MISSING, but 0 is a valid value (PRESENT)
   - For bool fields: the field is PRESENT as long as it exists (even if False)
   - For dict fields: empty dict = MISSING

8. **`get_archetype_requirements(archetype: str) -> Dict[str, ValidationSeverity]`**
   - Return a dict mapping field paths to their severity for a given archetype
   - Useful for UIs that want to show which fields are most important to fill

### Error Handling

- If the profile object is None, return a ValidationResult with a single CRITICAL issue
- If an archetype name is not recognized, fall back to universal-only validation with an INFO note
- Navigation of nested fields should never raise — if a sub-model is None, treat all its children as MISSING

### Design Principles

- **Unknowns preserved**: Missing fields are flagged but NEVER filled with defaults, guesses, or hallucinated values
- **Severity is meaningful**: CRITICAL truly blocks meaningful operation; WARNING degrades but doesn't block; INFO is nice-to-have
- **Transparency**: every validation decision is traceable in the returned data structure
- **Archetype stacking**: archetype-specific rules ADD to universal rules, never override them

## Output Files

- `kai/validation/__init__.py`
- `kai/validation/profile_validator.py`

## Acceptance Criteria

- [ ] `profile_validator.py` contains all 8 functions/methods listed above
- [ ] All 4 archetypes have dedicated validation functions with specific field requirements
- [ ] `FieldValidationStatus` and `ValidationSeverity` enums exist with all listed values
- [ ] `ValidationResult` model includes completeness_score and readiness_summary
- [ ] `_check_field` handles dot-notation navigation through nested objects
- [ ] Empty lists, None values, and empty strings are all correctly identified as MISSING
- [ ] No hallucination or default-filling — missing data stays missing
- [ ] `validate_profile` auto-detects archetype from profile.classification.archetype when not provided
- [ ] Universal validation runs for ALL archetypes
- [ ] Every validation function has docstrings and type hints
- [ ] Uses the same Pydantic/fallback import pattern as `gateway/models.py`

## Reference Materials

- `kai/models/business_profile.py` (Task 001) — the schema being validated
- `kai/runtime/business_profile.py` — existing profile structure for compatibility reference
- `gateway/models.py` — Pydantic import fallback pattern
- `CLAUDE.md` — quality gate philosophy (pass/fail with specific failures)
