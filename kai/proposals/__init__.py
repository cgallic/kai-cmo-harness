"""Proposal layer for the Kai Marketing OS.

This package turns audit findings into concrete, executable marketing
action plans.  The pipeline is:

    AuditFinding  -->  action_mapper  -->  ranking  -->  pruning  -->  bundler
                       (raw actions)     (scored,      (capacity-   (grouped
                                          deduped,      filtered)    into plans)
                                          ordered)

Public API
----------
- ``map_finding_to_actions`` -- convert one audit finding into proposed actions
- ``ActionMapping`` / ``MAPPING_REGISTRY`` -- the rule set that powers mapping
- ``process_actions`` -- rank, dedup, and dependency-sort a raw action list
- ``auto_bundle`` -- generate all applicable proposal bundles from an action list
- ``prune_and_shape`` -- capacity-aware filtering and scheduling
"""

from kai.proposals.action_mapper import (
    ActionMapping,
    MAPPING_REGISTRY,
    map_finding_to_actions,
    get_mappings_for_category,
    fill_template,
)
from kai.proposals.ranking import (
    rank_actions,
    deduplicate_actions,
    resolve_dependencies,
    process_actions,
)
from kai.proposals.bundler import (
    auto_bundle,
    bundle_7day_quick_wins,
    bundle_30day_plan,
    bundle_campaign_pack,
    bundle_monthly_operating_plan,
)
from kai.proposals.pruning import (
    prune_and_shape,
    prune_by_capacity,
    select_action_mode,
    boost_preferred_channels,
    shape_for_compounding,
    shape_for_burst,
    CapacityConstraints,
)

__all__ = [
    # action_mapper
    "map_finding_to_actions",
    "ActionMapping",
    "MAPPING_REGISTRY",
    "get_mappings_for_category",
    "fill_template",
    # ranking
    "rank_actions",
    "deduplicate_actions",
    "resolve_dependencies",
    "process_actions",
    # bundler
    "auto_bundle",
    "bundle_7day_quick_wins",
    "bundle_30day_plan",
    "bundle_campaign_pack",
    "bundle_monthly_operating_plan",
    # pruning
    "prune_and_shape",
    "prune_by_capacity",
    "select_action_mode",
    "boost_preferred_channels",
    "shape_for_compounding",
    "shape_for_burst",
    "CapacityConstraints",
]
