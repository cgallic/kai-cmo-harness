"""Website action system -- executable operations against CMS connectors.

Provides the abstract :class:`Action` base class with a four-phase lifecycle
(validate -> preview -> approve -> execute -> verify), concrete website action
classes, helper utilities for diffing, HTML parsing, and safety checking, and
the diff-preview / approval workflow.

Action classes:
    UpdatePageCopy, UpdatePageSection, UpdateCTA, UpdateMetadata,
    FixTracking, RefreshApprovedSection, RestructurePage, AddSection

Approval workflow:
    ApprovalStatus, DiffPreview, ApprovalRequest,
    generate_diff_preview, assess_risk, evaluate_auto_approval,
    create_approval_request, approve_request, reject_request,
    request_revision, process_revision, get_pending_approvals, check_expired

Helpers:
    generate_diff, parse_page_sections, validate_html_safety
"""

from .approval import (
    DEFAULT_AUTO_APPROVE_SETTINGS,
    ApprovalRequest,
    ApprovalStatus,
    DiffPreview,
    approve_request,
    assess_risk,
    check_expired,
    create_approval_request,
    evaluate_auto_approval,
    generate_diff_preview,
    get_pending_approvals,
    process_revision,
    reject_request,
    request_revision,
)
from .base import Action, ActionLifecycleState, ActionResult
from .website import (
    AddSection,
    FixTracking,
    RefreshApprovedSection,
    RestructurePage,
    UpdateCTA,
    UpdateMetadata,
    UpdatePageCopy,
    UpdatePageSection,
    generate_diff,
    parse_page_sections,
    validate_html_safety,
)

__all__ = [
    # Base
    "Action",
    "ActionLifecycleState",
    "ActionResult",
    # Concrete actions
    "AddSection",
    "FixTracking",
    "RefreshApprovedSection",
    "RestructurePage",
    "UpdateCTA",
    "UpdateMetadata",
    "UpdatePageCopy",
    "UpdatePageSection",
    # Approval workflow
    "ApprovalStatus",
    "DiffPreview",
    "ApprovalRequest",
    "DEFAULT_AUTO_APPROVE_SETTINGS",
    "generate_diff_preview",
    "assess_risk",
    "evaluate_auto_approval",
    "create_approval_request",
    "approve_request",
    "reject_request",
    "request_revision",
    "process_revision",
    "get_pending_approvals",
    "check_expired",
    # Helpers
    "generate_diff",
    "parse_page_sections",
    "validate_html_safety",
]
