"""Lifecycle marketing -- sequence templates, timing rules, deliverability
controls, and sequence builders for automated email marketing."""

from kai.lifecycle.sequence_templates import (
    ALL_SEQUENCE_TEMPLATES,
    SequenceEmailTemplate,
    SequenceTemplate,
    get_required_merge_fields,
    get_template,
    get_templates_by_archetype,
    get_templates_by_category,
    validate_merge_fields,
)
from kai.lifecycle.timing import (
    BounceRecord,
    BounceType,
    DeliverabilityController,
    DeliverabilityReport,
    OptOutManager,
    OptOutRecord,
    SendTimeDecision,
    SendWindow,
    SpamComplaintRecord,
    TIMING_PRESETS,
    TimingEngine,
    TimingRules,
    WarmUpSchedule,
)
from kai.lifecycle.sequence_builders import (
    BANNED_PHRASES_IN_EMAILS,
    BuilderConfig,
    BuiltSequence,
    DormantLeadFollowUp,
    MaintenanceReorderCadence,
    PostJobReviewSequence,
    QuarterlyRepeatReminder,
    QuoteFollowUp,
    ReferralEngine,
    SequenceBuilder,
)

__all__ = [
    # sequence_templates
    "ALL_SEQUENCE_TEMPLATES",
    "SequenceEmailTemplate",
    "SequenceTemplate",
    "get_required_merge_fields",
    "get_template",
    "get_templates_by_archetype",
    "get_templates_by_category",
    "validate_merge_fields",
    # timing
    "BounceRecord",
    "BounceType",
    "DeliverabilityController",
    "DeliverabilityReport",
    "OptOutManager",
    "OptOutRecord",
    "SendTimeDecision",
    "SendWindow",
    "SpamComplaintRecord",
    "TIMING_PRESETS",
    "TimingEngine",
    "TimingRules",
    "WarmUpSchedule",
    # sequence_builders
    "BANNED_PHRASES_IN_EMAILS",
    "BuilderConfig",
    "BuiltSequence",
    "DormantLeadFollowUp",
    "MaintenanceReorderCadence",
    "PostJobReviewSequence",
    "QuarterlyRepeatReminder",
    "QuoteFollowUp",
    "ReferralEngine",
    "SequenceBuilder",
]
