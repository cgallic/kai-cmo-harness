# Task 045: Build paid media action system

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 8. Paid Media Operations
**Priority:** P1
**Depends on:** 044
**Estimated complexity:** Large

## Context

With ad platform connectors in place (Task 044), the system needs structured action types that represent every paid media operation the system might take. These actions follow the same validate-preview-execute-verify lifecycle as the base action system, but with paid-media-specific concerns: spend safety, platform compliance, creative validation, and budget impact assessment. This is the "what can we do with ads" layer — it defines the verbs of paid media management. Tasks 046-049 consume these action types to build campaign schemas, budget controls, variant workflows, and monitoring.

## Scope

Create `kai/actions/paid_media.py` containing all paid media action type classes, their validation logic, preview rendering, and execution stubs. Also create the `kai/actions/` package init.

## Detailed Requirements

### File: `kai/actions/__init__.py`

- Module docstring: "Marketing action types — structured operations that validate, preview, and execute changes across marketing channels."
- Import and re-export all action classes from paid_media.py
- `__all__` listing

### File: `kai/actions/paid_media.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: PaidMediaActionType (str, Enum)**
- `create_ad_creative`
- `adjust_bidding`
- `adjust_budget`
- `pause_campaign`
- `enable_campaign`
- `launch_campaign`
- `publish_approved_variant`
- `update_targeting`
- `add_negative_keywords`
- `create_ad_group`
- `retire_creative`

**Enum: ActionLifecycleState (str, Enum)**
- `pending_validation` — action created but not yet validated
- `validated` — passed all validation checks
- `validation_failed` — failed validation, cannot proceed
- `previewing` — generating preview
- `previewed` — preview generated, awaiting approval
- `approved` — approved for execution
- `executing` — currently executing
- `executed` — successfully executed
- `execution_failed` — execution attempt failed
- `verifying` — post-execution verification in progress
- `verified` — execution verified successful
- `verification_failed` — execution succeeded but verification found issues
- `rolled_back` — action was rolled back after execution

**Model: ValidationResult**
- `is_valid: bool`
- `errors: List[str]` — hard failures that prevent execution, default empty list
- `warnings: List[str]` — soft warnings that don't block but should be noted, default empty list
- `compliance_notes: List[str]` — platform policy compliance notes, default empty list

**Model: ActionPreview**
- `action_type: str` — PaidMediaActionType value
- `summary: str` — human-readable 1-2 sentence summary of what will happen
- `details: Dict[str, Any]` — structured details of the changes, default empty dict
- `spend_impact: Optional[str]` — human-readable spend impact (e.g., "Will add $50/day to total spend")
- `spend_amount: Optional[float]` — numeric spend impact in USD
- `risk_level: str` — "low", "medium", "high"
- `reversible: bool` — whether this action can be undone
- `estimated_time: Optional[str]` — how long until changes take effect (e.g., "Immediate", "24-48 hours for review")
- `requires_platform_review: bool = False` — whether the platform needs to review (e.g., new ad creatives)

**Model: ExecutionResult**
- `success: bool`
- `action_type: str`
- `platform: str`
- `entity_id: Optional[str]` — ID of the created/modified entity
- `entity_type: Optional[str]` — "campaign", "ad_group", "ad", "keyword"
- `changes_made: Dict[str, Any]` — what was actually changed, default empty dict
- `error_message: Optional[str]`
- `executed_at: str` — ISO timestamp
- `rollback_data: Optional[Dict[str, Any]]` — data needed to undo this action

**Model: VerificationResult**
- `verified: bool`
- `checks_performed: List[str]` — what was verified, default empty list
- `issues_found: List[str]` — any issues detected post-execution, default empty list
- `verified_at: str` — ISO timestamp

**Abstract class: PaidMediaAction(ABC)**

Base class for all paid media actions. Follows validate() -> preview() -> execute() -> verify() lifecycle.

- `__init__(self, platform: str, **kwargs)` — store platform, set `_state: ActionLifecycleState = "pending_validation"`, `_validation: Optional[ValidationResult] = None`, `_preview: Optional[ActionPreview] = None`, `_result: Optional[ExecutionResult] = None`, `_verification: Optional[VerificationResult] = None`
- `action_type: str` — abstract property returning PaidMediaActionType value
- `validate(self) -> ValidationResult` — run all validation checks. Set _state and _validation. Calls abstract `_validate_impl()`.
- `preview(self) -> ActionPreview` — generate preview. Must be validated first. Set _state and _preview. Calls abstract `_preview_impl()`.
- `execute(self, connector: Any, confirm: bool = False) -> ExecutionResult` — execute the action via the connector. Must be validated and previewed. If `confirm` is False, return preview instead. Calls abstract `_execute_impl()`.
- `verify(self, connector: Any) -> VerificationResult` — verify the action was executed correctly. Calls abstract `_verify_impl()`.
- `rollback(self, connector: Any) -> ExecutionResult` — roll back the action if possible. Calls abstract `_rollback_impl()`.
- `get_state(self) -> ActionLifecycleState` — return current state
- `to_dict(self) -> Dict[str, Any]` — serialize the action and its state to a dict

Abstract methods (to be implemented by each concrete action):
- `_validate_impl(self) -> ValidationResult`
- `_preview_impl(self) -> ActionPreview`
- `_execute_impl(self, connector: Any) -> ExecutionResult`
- `_verify_impl(self, connector: Any) -> VerificationResult`
- `_rollback_impl(self, connector: Any) -> ExecutionResult`

**Class: CreateAdCreative(PaidMediaAction)**

- `__init__(self, platform: str, format: str, headlines: List[str], descriptions: List[str], media_urls: Optional[List[str]] = None, cta: Optional[str] = None, landing_url: str = "", ad_group_id: Optional[str] = None, compliance_check_passed: bool = False)`
- `action_type` returns `"create_ad_creative"`
- `_validate_impl()`:
  - Check headlines are not empty
  - Check descriptions are not empty
  - Check landing_url is not empty
  - Platform-specific validation:
    - Google Ads: headlines max 30 chars each, descriptions max 90 chars, need 3-15 headlines and 2-4 descriptions for responsive search
    - Meta: primary text max 125 chars recommended, headline max 40 chars recommended
  - Check compliance_check_passed — warn if False
  - Check for banned words in headlines and descriptions (from CLAUDE.md banned list)
- `_preview_impl()`:
  - Summary: "Create {format} ad creative on {platform} with {len(headlines)} headlines"
  - Details: full creative spec
  - spend_impact: None (creating creative doesn't spend money directly)
  - risk_level: "medium"
  - requires_platform_review: True (all new creatives go through platform review)
- `_execute_impl()`:
  - Call `connector.create_ad(ad_group_id, creative_dict)`
- `_verify_impl()`:
  - Fetch the created ad and verify status is not "disapproved"
- `_rollback_impl()`:
  - Pause or remove the created ad

**Class: AdjustBidding(PaidMediaAction)**

- `__init__(self, platform: str, campaign_id: str, strategy: str, target_values: Optional[Dict[str, float]] = None, reason: str = "")`
- `strategy` options: "manual_cpc", "maximize_conversions", "target_cpa", "target_roas", "maximize_clicks", "lowest_cost"
- `_validate_impl()`:
  - Check campaign_id is set
  - Check strategy is valid
  - If target_cpa/target_roas: validate target values are reasonable (CPA > 0, ROAS > 0)
  - Check reason is provided
- `_preview_impl()`:
  - Summary: "Change bidding strategy for campaign {campaign_id} to {strategy}"
  - spend_impact: describe potential spend changes (e.g., "Switching to maximize_conversions may increase or decrease spend depending on conversion volume")
  - risk_level: "medium" for strategy changes, "high" for removing caps
- `_rollback_impl()`:
  - Store original bidding strategy and revert

**Class: AdjustBudget(PaidMediaAction)**

- `__init__(self, platform: str, campaign_id: str, new_budget: float, budget_type: str = "daily", reason: str = "", safety_check: Optional[Dict[str, Any]] = None)`
- `budget_type`: "daily" or "lifetime"
- `_validate_impl()`:
  - Check new_budget > 0
  - Check campaign_id is set
  - Check reason is provided
  - Run spend safety check via connector config:
    - If new_budget > max_daily_spend_usd (from config): error "Budget exceeds daily spend cap"
    - If projected monthly (new_budget * 30.4) > max_monthly_spend_usd: error "Projected monthly spend exceeds cap"
  - Warn if budget increase is >50% over current (may indicate a mistake)
  - Warn if budget decrease is >50% (may harm campaign learning)
- `_preview_impl()`:
  - Summary: "Set {budget_type} budget for campaign {campaign_id} to ${new_budget}"
  - spend_impact: "Daily spend will change to ${new_budget}/day (${new_budget * 30.4:.0f}/month projected)"
  - risk_level: "high" if increase > 100%, "medium" if any change, "low" if decrease
- `_rollback_impl()`:
  - Store original budget and revert

**Class: PauseCampaign(PaidMediaAction)**

- `__init__(self, platform: str, campaign_id: str, reason: str = "", pause_duration: Optional[str] = None)`
- `pause_duration`: human-readable (e.g., "7 days", "indefinite"), optional
- `_validate_impl()`:
  - Check campaign_id
  - Check reason
  - Warn if pausing a campaign with active spend (there may be commitments)
- `_preview_impl()`:
  - Summary: "Pause campaign {campaign_id} on {platform}"
  - spend_impact: "Campaign spend will stop. Current daily budget was ${current_budget}."
  - risk_level: "low" (pausing is safe)
  - reversible: True
- `_rollback_impl()`:
  - Re-enable the campaign

**Class: LaunchCampaign(PaidMediaAction)**

- `__init__(self, platform: str, campaign_config: Dict[str, Any], budget: float, targeting: Dict[str, Any], creatives: List[Dict[str, Any]], landing_pages: List[str], compliance_check_passed: bool = False)`
- This is the highest-risk action — launching a new campaign that will spend money.
- `_validate_impl()`:
  - **Readiness checks** (comprehensive):
    1. campaign_config has name, objective, bid_strategy
    2. budget > 0 and within safety caps
    3. targeting is not empty
    4. targeting is not overly broad (warn if no location, age, or interest targeting)
    5. targeting is not overly narrow (warn if estimated reach < 1000)
    6. creatives list is not empty
    7. Each creative has required fields (headlines, descriptions, landing_url)
    8. landing_pages are not empty
    9. compliance_check_passed is True (error if False — "Platform compliance check must pass before launch")
    10. For Meta: check if special_ad_categories needed
  - Must pass ALL checks to validate
- `_preview_impl()`:
  - Summary: "Launch new {objective} campaign on {platform} with ${budget}/day budget"
  - Details: full campaign config, targeting summary, creative count, landing pages
  - spend_impact: "New campaign will spend up to ${budget}/day (${budget * 30.4:.0f}/month)"
  - risk_level: "high"
  - reversible: True (can pause immediately)
  - estimated_time: "24-48 hours for ad review" (Meta/Google review new creatives)
- `_execute_impl()`:
  - Create campaign, create ad groups, create ads
  - Start campaign in PAUSED state, then enable only after everything is set up correctly
- `_rollback_impl()`:
  - Pause all campaign components and optionally remove

**Class: PublishApprovedVariant(PaidMediaAction)**

- `__init__(self, platform: str, ad_group_id: str, creative_variant_id: str, replace_existing: bool = False)`
- `_validate_impl()`:
  - Check ad_group_id and creative_variant_id
  - If replace_existing: store reference to what's being replaced for rollback
- `_preview_impl()`:
  - Summary: "Publish approved creative variant to ad group {ad_group_id}"
  - risk_level: "medium" if replacing, "low" if adding

**Class: UpdateTargeting(PaidMediaAction)**

- `__init__(self, platform: str, campaign_id: str, targeting_changes: Dict[str, Any], reason: str = "")`
- `targeting_changes` structure: `{"add": {...}, "remove": {...}, "update": {...}}`
- `_validate_impl()`:
  - Check campaign_id and reason
  - Check targeting_changes is not empty
  - Warn if removing all location targeting (too broad)
  - Warn if narrowing audience significantly
- `_preview_impl()`:
  - Summary: "Update targeting for campaign {campaign_id}: {change_summary}"
  - risk_level: "medium"
- `_rollback_impl()`:
  - Store original targeting and revert

**Class: AddNegativeKeywords(PaidMediaAction)**

- `__init__(self, platform: str, campaign_id: str, keywords: List[str], reason: str = "")`
- `_validate_impl()`:
  - Check keywords list is not empty
  - Check no keyword conflicts with active positive keywords (if detectable)
  - Validate keyword formats
- `_preview_impl()`:
  - Summary: "Add {len(keywords)} negative keywords to campaign {campaign_id}"
  - Details: list of keywords being added
  - risk_level: "low" (negative keywords reduce waste)
  - reversible: True

**Helper functions (module-level):**

- `generate_action_execution_id() -> str` — return `pma_{uuid.uuid4().hex[:12]}`
- `format_spend_impact(daily_budget: float) -> str` — return formatted string: "${daily:.2f}/day (${daily * 30.4:.0f}/month projected)"
- `check_headline_length(headline: str, platform: str) -> Optional[str]` — return error string if headline exceeds platform limit, None if ok
- `check_description_length(description: str, platform: str) -> Optional[str]` — return error string if too long
- `PLATFORM_CREATIVE_LIMITS: Dict[str, Dict[str, Any]]` — dict mapping platform to creative constraints:
  - google_ads: {"headline_max": 30, "description_max": 90, "headlines_min": 3, "headlines_max": 15, "descriptions_min": 2, "descriptions_max": 4}
  - meta_ads: {"primary_text_max": 125, "headline_max": 40, "description_max": 30, "link_description_max": 30}
  - local_services_ads: {} (no direct ad creation)

## Output Files

- `kai/actions/__init__.py`
- `kai/actions/paid_media.py`

## Acceptance Criteria

- [ ] `PaidMediaActionType` enum has all 11 action types
- [ ] `ActionLifecycleState` enum has all 13 states
- [ ] `ValidationResult`, `ActionPreview`, `ExecutionResult`, `VerificationResult` models all have correct fields
- [ ] `PaidMediaAction` abstract base class has validate/preview/execute/verify/rollback lifecycle methods
- [ ] All 8 concrete action classes extend PaidMediaAction and implement all abstract methods
- [ ] `CreateAdCreative._validate_impl()` checks platform-specific headline/description limits
- [ ] `AdjustBudget._validate_impl()` runs spend safety checks against daily and monthly caps
- [ ] `LaunchCampaign._validate_impl()` runs all 10 readiness checks listed above
- [ ] `LaunchCampaign` starts campaigns in PAUSED state before enabling
- [ ] All mutating actions check `confirm` flag before executing
- [ ] All actions include rollback data in ExecutionResult
- [ ] `PLATFORM_CREATIVE_LIMITS` dict has entries for google_ads and meta_ads
- [ ] `format_spend_impact()` helper correctly calculates monthly projection
- [ ] No banned words from CLAUDE.md appear in any string constants
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] All actions store enough state for rollback in `_rollback_impl()`

## Reference Materials

- `kai/connectors/ads/base.py` (created by Task 044) — AdPlatformConnector, SpendSafetyCheck, all ad models
- `kai/models/proposal.py` (created by Task 022) — ProposedAction, ActionType, RiskTier for compatibility
- `kai/runtime/actions.py` — existing ActionProposal and ActionStore patterns (lines 50-150)
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `harness/references/google-ads-policy-reference.md` — Google Ads creative requirements
- `harness/references/meta-ads-rules.md` — Meta Ads creative requirements and Special Ad Categories
- `knowledge/playbooks/ad-campaign-management.md` — ad campaign management guidance
- `CLAUDE.md` — full project context, banned word list
