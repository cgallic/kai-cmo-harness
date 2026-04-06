"""Canonical model package for the Kai Marketing OS.

This package contains the authoritative Pydantic data models consumed by
every downstream system -- audits, proposals, action plans, archetype
activation, and workspace state.

All model classes are re-exported here so callers can write::

    from kai.models import BusinessProfile, BusinessIdentity, Offer
    from kai.models import Campaign, AdGroup, Ad, BudgetGuard
    from kai.models import WorkspaceState, Integration, BudgetConstraint
    from kai.models import AuditResult, AuditFinding, create_finding
"""

from .business_profile import (
    BaseModel,
    BrandVoice,
    BudgetAndRisk,
    BusinessClassification,
    BusinessConstraints,
    BusinessGeography,
    BusinessIdentity,
    BusinessProfile,
    BuyerSalesCycle,
    ChannelPresence,
    GoalsAndKPIs,
    Location,
    Offer,
    OperatorCapacity,
    PersonaProfile,
    TrustProfile,
    TrustSignal,
)

from .paid_media import (
    # Enums
    AdFormat,
    AdStatus,
    BidStrategy,
    CampaignObjective,
    CampaignStatus,
    # Models
    Ad,
    AdGroup,
    AdPerformance,
    BudgetGuard,
    Campaign,
    ExclusionList,
    NegativeKeywordList,
    Targeting,
    # Constants
    STANDARD_NEGATIVE_KEYWORDS,
    # ID generators
    generate_ad_group_id,
    generate_ad_id,
    generate_budget_guard_id,
    generate_campaign_id,
    generate_exclusion_id,
    generate_nkl_id,
    # Metric calculators
    calculate_conversion_rate,
    calculate_cpa,
    calculate_ctr,
    calculate_roas,
    # Targeting helper
    summarize_targeting,
)

from .audit import (
    # Enums
    FindingSeverity,
    FindingPriority,
    FindingSource,
    EffortLevel,
    ImpactLevel,
    # Data models
    Evidence,
    AuditFinding,
    CategoryScorecard,
    MissingDataFlag,
    AuditResult,
    # Utility functions
    severity_to_priority,
    create_finding,
    create_missing_data_finding,
    compute_category_scorecard,
    compute_overall_score,
    compile_audit_result,
    format_finding_summary,
)

from .proposal import (
    # Enums
    ActionType,
    RiskTier,
    ApprovalRequirement,
    # Data models
    ProposedAction,
    ProposalBundle,
    # ID generators
    generate_action_id,
    generate_bundle_id,
    # Generation rule functions
    assign_risk_tier,
    derive_approval_requirement,
    compute_priority_score,
)

from .workspace_state import (
    # Sub-models
    ApprovalDefaults,
    BudgetConstraint,
    ChannelEnablement,
    Integration,
    OperatorPreferences,
    # Top-level state
    WorkspaceState,
    # Persistence functions
    load_workspace_state,
    save_workspace_state,
    update_integration_status,
    # Utility functions
    check_budget_available,
    get_available_capabilities,
    get_connected_platforms,
    requires_approval,
)

__all__ = [
    # Pydantic base (or stdlib fallback)
    "BaseModel",
    # ---------------------------------------------------------------
    # BusinessProfile models (Task 001)
    # ---------------------------------------------------------------
    # Identity & classification
    "BusinessIdentity",
    "BusinessClassification",
    # Offers
    "Offer",
    # Geography
    "Location",
    "BusinessGeography",
    # Personas
    "PersonaProfile",
    # Trust
    "TrustSignal",
    "TrustProfile",
    # Goals
    "GoalsAndKPIs",
    # Channels
    "ChannelPresence",
    # Constraints
    "BusinessConstraints",
    # Budget
    "BudgetAndRisk",
    # Sales cycle
    "BuyerSalesCycle",
    # Brand voice
    "BrandVoice",
    # Operator
    "OperatorCapacity",
    # Top-level profile
    "BusinessProfile",
    # ---------------------------------------------------------------
    # Paid media models
    # ---------------------------------------------------------------
    # --- Paid media enums ---
    "CampaignObjective",
    "CampaignStatus",
    "BidStrategy",
    "AdFormat",
    "AdStatus",
    # --- Paid media models ---
    "Targeting",
    "NegativeKeywordList",
    "ExclusionList",
    "Ad",
    "AdGroup",
    "AdPerformance",
    "Campaign",
    "BudgetGuard",
    # --- Paid media constants ---
    "STANDARD_NEGATIVE_KEYWORDS",
    # --- Paid media ID generators ---
    "generate_campaign_id",
    "generate_ad_group_id",
    "generate_ad_id",
    "generate_nkl_id",
    "generate_exclusion_id",
    "generate_budget_guard_id",
    # --- Paid media metric calculators ---
    "calculate_ctr",
    "calculate_cpa",
    "calculate_roas",
    "calculate_conversion_rate",
    # --- Paid media helpers ---
    "summarize_targeting",
    # ---------------------------------------------------------------
    # Audit models (Task 013)
    # ---------------------------------------------------------------
    # --- Audit enums ---
    "FindingSeverity",
    "FindingPriority",
    "FindingSource",
    "EffortLevel",
    "ImpactLevel",
    # --- Audit data models ---
    "Evidence",
    "AuditFinding",
    "CategoryScorecard",
    "MissingDataFlag",
    "AuditResult",
    # --- Audit utility functions ---
    "severity_to_priority",
    "create_finding",
    "create_missing_data_finding",
    "compute_category_scorecard",
    "compute_overall_score",
    "compile_audit_result",
    "format_finding_summary",
    # ---------------------------------------------------------------
    # Proposal models (Task 022)
    # ---------------------------------------------------------------
    # --- Proposal enums ---
    "ActionType",
    "RiskTier",
    "ApprovalRequirement",
    # --- Proposal data models ---
    "ProposedAction",
    "ProposalBundle",
    # --- Proposal ID generators ---
    "generate_action_id",
    "generate_bundle_id",
    # --- Proposal generation rule functions ---
    "assign_risk_tier",
    "derive_approval_requirement",
    "compute_priority_score",
    # ---------------------------------------------------------------
    # WorkspaceState models (Task 005)
    # ---------------------------------------------------------------
    # Sub-models
    "Integration",
    "BudgetConstraint",
    "ApprovalDefaults",
    "ChannelEnablement",
    "OperatorPreferences",
    # Top-level state
    "WorkspaceState",
    # Persistence functions
    "save_workspace_state",
    "load_workspace_state",
    "update_integration_status",
    # Utility functions
    "check_budget_available",
    "requires_approval",
    "get_connected_platforms",
    "get_available_capabilities",
]
