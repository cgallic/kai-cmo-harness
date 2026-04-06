"""First-class operator flows for the Kai Marketing OS.

Flows are guided, multi-step workflows that walk operators through
complete marketing cycles.  Each flow orchestrates multiple subsystems
(audit, proposals, approval, execution, memory) into a coherent,
step-by-step experience.

Available flows
---------------

OnboardingFlow
    Walk a new business from zero to first-approved actions in 8 steps:
    collect info, build profile, detect archetype, activate modules,
    run initial audit, generate proposals, present review bundle,
    and approve first actions.

AuditReviewFlow
    Run all relevant audits, generate an executive summary, support
    drill-down into specific categories, and produce proposals from
    findings.

ApproveRejectReviseFlow
    Queue-based approval workflow with individual review, batch
    approval (low-risk only), defer, and revision triggering.

ExecutionMonitoringFlow
    Visibility into active, completed, failed, and scheduled actions.
    Retry failed actions and view upcoming execution schedules.

LearningReviewFlow
    Review recent learnings, confirm or dismiss pending observations,
    re-validate stale memories, and get learning summaries.

All flows maintain serializable state objects that can be persisted
to disk and resumed later.
"""

from kai.flows.onboarding import OnboardingFlow, OnboardingState, OnboardingStep
from kai.flows.audit_review import AuditReviewFlow, AuditReviewState
from kai.flows.approval_flow import ApproveRejectReviseFlow, ApprovalFlowState
from kai.flows.execution_monitor import ExecutionMonitoringFlow
from kai.flows.learning_review import LearningReviewFlow

__all__ = [
    "OnboardingFlow",
    "OnboardingState",
    "OnboardingStep",
    "AuditReviewFlow",
    "AuditReviewState",
    "ApproveRejectReviseFlow",
    "ApprovalFlowState",
    "ExecutionMonitoringFlow",
    "LearningReviewFlow",
]
