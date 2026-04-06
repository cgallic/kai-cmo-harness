# Task 022: Define ProposedAction schema and generation rules

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 4. Proposal and Planning
**Priority:** P1
**Depends on:** 013
**Estimated complexity:** Large

## Context

Once the audit engine (Task 013) produces a list of AuditFinding objects, the system needs a way to translate those findings into concrete, executable marketing actions. The ProposedAction schema is the bridge between "here is a problem we found" and "here is exactly what we will do about it." Every downstream system — bundling, ranking, creative generation, execution, approval — consumes ProposedAction objects. This is the central currency of the entire proposal layer and must be comprehensive enough to represent any marketing action the system might take while remaining structured enough for automated processing.

The ProposalBundle groups related actions into coherent plans that operators can review and approve as a unit rather than dealing with dozens of individual actions.

## Scope

Create `kai/models/proposal.py` containing the ProposedAction and ProposalBundle Pydantic models, the ActionType enum, the RiskTier enum, the ApprovalRequirement enum, and all supporting types. Also define the generation rules as pure functions that map AuditFinding attributes to ProposedAction field values (risk tier assignment, approval requirement derivation, priority scoring).

## Detailed Requirements

### File: `kai/models/proposal.py`

Use the same Pydantic import fallback pattern from `gateway/models.py` (try pydantic, fall back to minimal BaseModel shim). Follow the same structural conventions as `kai/runtime/audit.py` — enums as `str, Enum` subclasses, dataclass-like models with sensible defaults.

**Enum: ActionType**
- Values (each is a string enum member):
  - `website_update` — modify existing website content, layout, or elements
  - `social_post` — create and publish social media content
  - `ad_campaign` — create, modify, or launch a paid advertising campaign
  - `email_sequence` — create or modify an automated email sequence
  - `review_request` — initiate a review solicitation campaign
  - `gbp_update` — update Google Business Profile listing
  - `seo_fix` — technical or on-page SEO correction
  - `analytics_fix` — fix or set up tracking, attribution, or analytics
  - `content_creation` — create a new content asset (blog, case study, video script, etc.)
  - `follow_up_sequence` — create or modify a lead follow-up workflow
  - `reputation_action` — respond to reviews, manage reputation signals
  - `kaicalls_setup` — set up or configure KaiCalls AI receptionist for phone lead capture

**Enum: RiskTier**
- `auto` — no spend, no public-facing change (e.g., internal analytics fix, tracking setup)
- `low` — small copy update, internal change, metadata update (e.g., update meta description, fix broken link)
- `medium` — new content publishing, small spend (e.g., publish blog post, launch $10/day ad test)
- `high` — campaign launch, significant spend (e.g., launch full ad campaign, major website restructure)
- `critical` — brand-level changes, large spend (e.g., rebrand elements, $1000+ campaign launch, homepage redesign)

**Enum: ApprovalRequirement**
- `auto_approve` — system can execute without human review
- `operator_review` — operator should review but can batch-approve
- `operator_approval` — operator must explicitly approve this specific action

**Model: ProposedAction**
- `id: str` — unique identifier, format `act_{uuid_hex[:12]}` (generate via helper function)
- `source_finding_id: str` — links back to the AuditFinding that generated this action
- `action_type: str` — ActionType enum value
- `channel: str` — target channel: "website", "social", "paid_media", "email", "sms", "phone", "gbp", "analytics", "offline"
- `title: str` — short operator-readable title, e.g., "Add phone number to homepage hero"
- `description: str` — 2-3 sentence explanation of what this action entails
- `reason: str` — why this action matters for the business (connects back to the finding)
- `business_impact: str` — narrative description of expected business impact, e.g., "Adding a prominent phone number typically increases call volume by 20-40% for local service businesses"
- `expected_outcome: str` — measurable expected outcome, e.g., "Increase monthly phone inquiries from 12 to 18-22"
- `risk_tier: str` — RiskTier enum value, default "low"
- `approval_requirement: str` — ApprovalRequirement enum value, default "operator_review"
- `suggested_payload: Dict[str, Any]` — the actual content, configuration, or parameters needed for execution. Structure varies by action_type. Default empty dict.
- `estimated_effort: Optional[str]` — human-readable effort estimate, e.g., "30 minutes", "2 hours", "1 day"
- `estimated_effort_hours: Optional[float]` — numeric effort in hours for capacity math
- `estimated_cost: Optional[float]` — estimated USD cost (ad spend, tool subscription, etc.), default 0.0
- `priority_score: float` — computed priority score (0-100), default 50.0
- `archetype_relevance: List[str]` — which archetypes this action is especially relevant for, default empty list
- `tags: List[str]` — freeform tags for filtering and grouping, default empty list
- `depends_on: List[str]` — list of other ProposedAction IDs that must complete first, default empty list
- `status: str` — one of: "proposed", "approved", "rejected", "in_progress", "completed", "cancelled", default "proposed"
- `created_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all for extra data, default empty dict

**Model: ProposalBundle**
- `id: str` — unique identifier, format `bnd_{uuid_hex[:12]}`
- `business_id: str` — links to the BusinessProfile this bundle is for
- `bundle_type: str` — one of: "7_day", "30_day", "campaign", "monthly_operating"
- `bundle_name: str` — human-readable name, e.g., "Week 1 Quick Wins" or "Review Generation Campaign"
- `actions: List[ProposedAction]` — the actions in this bundle, default empty list
- `total_estimated_cost: float` — sum of all action estimated_cost values, default 0.0
- `total_estimated_effort_hours: float` — sum of all action estimated_effort_hours values, default 0.0
- `executive_summary: str` — 3-5 sentence summary of what this bundle accomplishes and why
- `expected_outcomes: List[str]` — list of measurable expected outcomes, default empty list
- `weekly_milestones: Dict[str, List[str]]` — week number to list of milestone descriptions (for 30-day bundles), default empty dict
- `created_at: Optional[str]` — ISO timestamp
- `metadata: Dict[str, Any]` — catch-all, default empty dict

**Generation rule functions (pure functions, no side effects):**

1. `assign_risk_tier(action_type: str, estimated_cost: float, channel: str, is_public_facing: bool) -> str`
   - If estimated_cost == 0 and not is_public_facing: return "auto"
   - If estimated_cost == 0 and is_public_facing and action_type in [seo_fix, analytics_fix]: return "low"
   - If estimated_cost > 0 and estimated_cost <= 50: return "medium"
   - If estimated_cost > 50 and estimated_cost <= 500: return "high"
   - If estimated_cost > 500: return "critical"
   - If action_type == "ad_campaign" and estimated_cost > 100: return "high"
   - If action_type in [website_update] and channel == "website": check if it's a homepage change (high) vs. inner page (medium vs. low)
   - Default: "low"
   - Include logic comments explaining the reasoning

2. `derive_approval_requirement(risk_tier: str, auto_execution_enabled: bool) -> str`
   - If risk_tier == "auto" and auto_execution_enabled: return "auto_approve"
   - If risk_tier == "low" and auto_execution_enabled: return "auto_approve"
   - If risk_tier == "low" and not auto_execution_enabled: return "operator_review"
   - If risk_tier == "medium": return "operator_review"
   - If risk_tier in ["high", "critical"]: return "operator_approval"
   - Default: "operator_review"

3. `compute_priority_score(severity: str, finding_priority: str, estimated_effort_hours: float, estimated_cost: float, archetype_match: bool) -> float`
   - Base score from severity: critical=90, high=70, medium=50, low=30
   - Priority boost: P0=+10, P1=+5, P2=0, P3=-5
   - Effort penalty: if effort > 8 hours, -10; if effort > 4 hours, -5; if effort <= 1 hour, +10
   - Cost penalty: if cost > 500, -10; if cost > 100, -5; if cost == 0, +5
   - Archetype match bonus: +5 if archetype_match is True
   - Clamp result to 0-100
   - Return float

4. `generate_action_id() -> str`
   - Return `act_{uuid.uuid4().hex[:12]}`

5. `generate_bundle_id() -> str`
   - Return `bnd_{uuid.uuid4().hex[:12]}`

### File: `kai/models/__init__.py` (update if exists, create if not)

- Add imports for all new model classes and enums from `proposal.py`
- Add them to `__all__`

## Output Files

- `kai/models/proposal.py`
- `kai/models/__init__.py` (create or update)

## Acceptance Criteria

- [ ] `kai/models/proposal.py` exists and contains ActionType, RiskTier, ApprovalRequirement enums
- [ ] ProposedAction model has all 20+ fields listed above with correct types and defaults
- [ ] ProposalBundle model has all 12 fields listed above with correct types and defaults
- [ ] All 5 generation rule functions exist with correct signatures and logic
- [ ] Risk tier assignment covers all specified cases with comments explaining reasoning
- [ ] Approval requirement derivation handles auto_execution_enabled flag
- [ ] Priority score computation handles all 5 factors with correct weights and clamping
- [ ] ID generators produce correctly formatted IDs with `act_` and `bnd_` prefixes
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] All list fields use `Field(default_factory=list)`, all dict fields use `Field(default_factory=dict)`
- [ ] `kai/models/__init__.py` exports all new classes and enums
- [ ] ProposedAction can be instantiated with just `source_finding_id`, `action_type`, `title`, and `description` (everything else has defaults)
- [ ] No imports from `kai/runtime/` — this is standalone in `kai/models/`

## Reference Materials

- `kai/runtime/audit.py` — AuditFinding and AuditResult schemas that this consumes (lines 88-159)
- `kai/runtime/actions.py` — existing ActionProposal dataclass in the runtime layer (for compatibility awareness)
- `gateway/models.py` — Pydantic import fallback pattern to replicate
- `kai/models/business_profile.py` (created by Task 001) — BusinessProfile schema for business_id references
- `CLAUDE.md` — full project context and quality gate rules
