# Task 010: Build overlay system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 2. Archetypes and Module System
**Priority:** P2
**Depends on:** 006, 007, 008, 009
**Estimated complexity:** Large

## Context

Archetypes define the base marketing playbook for a business type (local-service, ecommerce, etc.), but many businesses have industry-specific constraints that overlay on top. A healthcare business that is also local-service needs HIPAA considerations layered on. A creator who also sells products needs audience-first metrics layered on ecommerce defaults. Overlays are modifiers that add restrictions, adjust priorities, and introduce industry-specific requirements without replacing the base archetype. The overlay system lets the same archetype serve dozens of industry verticals.

## Scope

Build `kai/archetypes/overlays/` with four industry overlays (healthcare, creator, franchise, saas) plus an `overlay_registry.py` that provides the `apply_overlay()` function for merging overlays onto archetypes.

## Detailed Requirements

### File: `kai/archetypes/overlays/__init__.py`
- Package init importing all overlays and the registry
- `__all__` listing

### File: `kai/archetypes/overlays/overlay_registry.py`

**Data Model: `OverlayDefinition`** (dataclass)
- `id: str` — unique overlay identifier, e.g., "healthcare"
- `name: str` — display name, e.g., "Healthcare / Medical"
- `description: str` — what this overlay does
- `compatible_archetypes: List[str]` — which archetypes this overlay can be applied to (empty list = all)
- `additional_audit_categories: List[str]` — audit categories added by this overlay
- `additional_kpis: Dict[str, "KPIDefinition"]` — extra KPIs
- `additional_compliance: List[str]` — extra compliance sensitivities
- `restricted_actions: List[str]` — actions from the base archetype that are restricted or require extra review
- `restricted_claims: List[str]` — marketing claims that are restricted
- `required_disclaimers: List[str]` — disclaimers that must appear in marketing materials
- `modified_priorities: Dict[str, str]` — adjustments to priority_defaults (key = action_family_id, value = new priority)
- `additional_creative_rules: List[str]` — extra rules for creative production
- `metadata: Dict[str, Any]` — overlay-specific extra data

**Function: `apply_overlay(archetype: ArchetypeDefinition, overlay: OverlayDefinition) -> ArchetypeDefinition`**
- Create a new ArchetypeDefinition (do NOT mutate the input)
- Merge logic:
  - `audit_categories`: append overlay's additional categories (deduplicate)
  - `kpi_schema`: add overlay's additional KPIs (overlay KPIs override if same id)
  - `compliance_sensitivities`: append overlay's additional compliance items
  - `archetype_specific_rules`: append overlay's required_disclaimers and additional_creative_rules
  - `action_families`: for each restricted_action, find the matching action family and add a `_requires_compliance_review` flag (or add a note to the description)
  - `priority_defaults`: apply modified_priorities adjustments
  - Mark the resulting archetype with `applied_overlays: List[str]` tracking which overlays have been applied
- Handle incompatible overlays: if the overlay's compatible_archetypes list is non-empty and doesn't include the archetype's id, raise a ValueError with a clear message

**Function: `apply_overlays(archetype: ArchetypeDefinition, overlays: List[OverlayDefinition]) -> ArchetypeDefinition`**
- Apply multiple overlays in sequence
- Order matters — later overlays can further restrict

**Constant: `OVERLAY_REGISTRY: Dict[str, OverlayDefinition]`**
- Dict mapping overlay id -> OverlayDefinition for lookup

**Function: `get_overlay(overlay_id: str) -> Optional[OverlayDefinition]`**
- Lookup an overlay by id from the registry

**Function: `list_overlays() -> List[str]`**
- Return all registered overlay ids

### File: `kai/archetypes/overlays/healthcare.py`

**Constant: `HEALTHCARE_OVERLAY`** — an OverlayDefinition.

- `id`: "healthcare"
- `name`: "Healthcare / Medical"
- `compatible_archetypes`: ["local-service", "professional-services", "multi-location"]
- `additional_audit_categories`: ["hipaa_compliance", "medical_claim_verification", "patient_review_management"]
- `additional_kpis`:
  - `patient_acquisition_cost`: dollars, lower_is_better, primary
  - `patient_satisfaction_score`: 1-10, higher_is_better, secondary
  - `appointment_show_rate`: percentage, higher_is_better, secondary
- `additional_compliance`:
  - "HIPAA requires that no patient information (including testimonials) be shared without written consent"
  - "Medical claims must be evidence-based — no unproven treatment efficacy claims"
  - "Before/after photos require explicit patient consent and may not be used on certain platforms"
  - "Advertising cannot guarantee specific medical outcomes"
  - "Prescription medication advertising has FDA requirements"
  - "Telehealth advertising must comply with state licensing requirements"
  - "Patient testimonials may need disclaimer: 'Individual results may vary'"
- `restricted_actions`: ["before_after_posts", "testimonial_cards"]
- `restricted_claims`: ["cure", "guaranteed results", "painless", "risk-free treatment", "best doctor/practice"]
- `required_disclaimers`: ["Individual results may vary", "Consult your healthcare provider"]
- `additional_creative_rules`:
  - "No before/after images without written patient consent on file"
  - "No stock photos representing specific medical procedures"
  - "All practitioner credentials must be current and verifiable"
  - "Meta Ads: healthcare falls under Special Ad Categories on some platforms"

### File: `kai/archetypes/overlays/creator.py`

**Constant: `CREATOR_OVERLAY`** — an OverlayDefinition.

- `id`: "creator"
- `name`: "Creator / Personal Brand"
- `compatible_archetypes`: [] (all archetypes)
- `additional_audit_categories`: ["audience_engagement", "content_consistency", "monetization_diversification"]
- `additional_kpis`:
  - `audience_growth_rate`: percentage/month, higher_is_better, primary
  - `engagement_rate`: percentage, higher_is_better, primary
  - `content_consistency_score`: 0-100, higher_is_better, secondary
  - `revenue_per_follower`: dollars, higher_is_better, tertiary
  - `sponsorship_rate`: dollars per post/video, higher_is_better, tertiary
- `additional_compliance`:
  - "FTC requires clear disclosure of sponsored content and affiliate relationships"
  - "Platform-specific sponsorship disclosure rules (Instagram #ad, YouTube paid promotion checkbox)"
  - "Earnings claims in monetization courses must be substantiated"
- `restricted_actions`: []
- `restricted_claims`: ["guaranteed income", "easy money", "passive income without effort"]
- `required_disclaimers`: ["Paid partnership" (for sponsored), "Affiliate link" (for affiliate)]
- `modified_priorities`: content creation moves to P1, audience engagement moves to P1
- `additional_creative_rules`:
  - "Personal brand content should be authentic — scripted content should still feel genuine"
  - "Algorithm optimization is important but not at the cost of brand authenticity"
  - "Cross-platform repurposing should adapt format, not just repost identically"

### File: `kai/archetypes/overlays/franchise.py`

**Constant: `FRANCHISE_OVERLAY`** — an OverlayDefinition.

- `id`: "franchise"
- `name`: "Franchise"
- `compatible_archetypes`: ["local-service", "multi-location", "ecommerce"]
- `additional_audit_categories`: ["brand_compliance", "corporate_alignment", "co_op_utilization"]
- `additional_kpis`:
  - `brand_compliance_score`: 0-100, higher_is_better, primary
  - `co_op_fund_utilization`: percentage, higher_is_better, secondary
- `additional_compliance`:
  - "All marketing materials must comply with franchisor brand guidelines"
  - "Co-op advertising funds have specific usage rules and approval requirements"
  - "Franchisee cannot make brand-level claims without corporate approval"
  - "Territory advertising must respect agreed-upon geographic boundaries"
  - "Pricing and promotion changes may require franchisor approval"
  - "Use of franchisor trademarks is governed by franchise agreement"
- `restricted_actions`: ["brand_messaging_changes", "pricing_changes", "new_offer_creation"]
- `restricted_claims`: ["franchise-wide claims without corporate approval"]
- `required_disclaimers`: ["Independently owned and operated" (if required by franchise agreement)]
- `modified_priorities`: brand_consistency moves to P1
- `additional_creative_rules`:
  - "All creative must use approved brand assets (logos, colors, fonts)"
  - "Local customization is limited to approved template fields"
  - "Corporate must approve any creative that deviates from templates"

### File: `kai/archetypes/overlays/saas.py`

**Constant: `SAAS_OVERLAY`** — an OverlayDefinition.

- `id`: "saas"
- `name`: "SaaS / Software"
- `compatible_archetypes`: [] (all archetypes, but primarily professional-services and ecommerce)
- `additional_audit_categories`: ["trial_funnel", "product_led_growth", "feature_announcements", "churn_prevention"]
- `additional_kpis`:
  - `trial_to_paid_rate`: percentage, higher_is_better, primary
  - `monthly_churn_rate`: percentage, lower_is_better, primary
  - `net_revenue_retention`: percentage (over 100% = expansion), higher_is_better, primary
  - `activation_rate`: percentage of signups reaching "aha moment", higher_is_better, primary
  - `feature_adoption_rate`: percentage, higher_is_better, secondary
  - `support_ticket_volume`: count, lower_is_better, tertiary
- `additional_compliance`:
  - "Free trial terms must be clearly stated — no surprise charges"
  - "Pricing page must accurately reflect current pricing (FTC click-to-cancel compliance)"
  - "Comparison claims against competitors must be factual and current"
  - "Data handling and privacy claims must comply with GDPR/CCPA"
  - "Uptime and performance claims must be verifiable"
- `restricted_actions`: []
- `restricted_claims`: ["#1 software", "guaranteed uptime" (without SLA), "competitor disparagement"]
- `required_disclaimers`: []
- `modified_priorities`: trial_funnel optimization and churn prevention move to P1
- `additional_creative_rules`:
  - "Product screenshots must reflect the current UI"
  - "Feature announcements should be timed with actual releases"
  - "Comparison charts must be kept current — outdated comparisons are worse than none"
  - "Demo videos should show real product workflows, not mockups"

### Update `kai/archetypes/__init__.py`
- Import and export all overlays and the registry

## Output Files

- `kai/archetypes/overlays/__init__.py`
- `kai/archetypes/overlays/overlay_registry.py`
- `kai/archetypes/overlays/healthcare.py`
- `kai/archetypes/overlays/creator.py`
- `kai/archetypes/overlays/franchise.py`
- `kai/archetypes/overlays/saas.py`
- `kai/archetypes/__init__.py` (update to include overlays)

## Acceptance Criteria

- [ ] `overlay_registry.py` defines OverlayDefinition model with all listed fields
- [ ] `apply_overlay()` creates a new ArchetypeDefinition without mutating the input
- [ ] `apply_overlay()` raises ValueError for incompatible archetype/overlay combinations
- [ ] `apply_overlays()` handles applying multiple overlays in sequence
- [ ] `OVERLAY_REGISTRY` dict contains all 4 overlays
- [ ] Healthcare overlay includes HIPAA compliance and before/after restrictions
- [ ] Creator overlay includes FTC sponsorship disclosure requirements
- [ ] Franchise overlay restricts brand-level changes and requires corporate approval
- [ ] SaaS overlay adds trial funnel and churn prevention KPIs
- [ ] Each overlay has `compatible_archetypes` properly set
- [ ] All overlays follow the OverlayDefinition schema exactly
- [ ] `kai/archetypes/__init__.py` updated to export overlay module

## Reference Materials

- `kai/archetypes/base.py` (Task 006) — ArchetypeDefinition and sub-models
- `kai/archetypes/local_service.py` (Task 006) — example of a full archetype
- `knowledge/checklists/healthcare-medical-checklist.md` — healthcare marketing checklist
- `knowledge/checklists/creator-personal-brand-checklist.md` — creator checklist
- `knowledge/checklists/restaurant-food-bev-checklist.md` — franchise-relevant checklist
- `knowledge/playbooks/saas-metrics-guide.md` — SaaS metrics guide
- `harness/references/advertising-compliance.md` — FTC/GDPR compliance reference
