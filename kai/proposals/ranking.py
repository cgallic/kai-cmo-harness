"""Proposal ranking, deduplication, and dependency resolution.

This module takes a raw list of ProposedAction dicts (as produced by the
action mapper) and returns a clean, ranked, deduped, dependency-ordered
list ready for bundling and capacity pruning.

Pipeline: ``rank_actions`` --> ``deduplicate_actions`` --> ``resolve_dependencies``

The main entry point is ``process_actions``, which chains all three steps.

Design principles
-----------------
1. **Multi-factor ranking.**  Five weighted factors produce a single
   composite score for deterministic ordering.
2. **Conservative dedup.**  Only merges actions that are clearly
   redundant -- exact type+channel+target match, high title similarity,
   or heavy payload overlap.
3. **Dependency-safe ordering.**  Topological sort ensures actions
   execute in a valid order.  Cycles are broken by removing the
   lowest-priority edge.
4. **Pure functions.**  No file I/O, no network, no state mutation.
"""

from __future__ import annotations

import copy
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# Constants
# ============================================================================

# Ranking weight factors (sum to 1.0)
WEIGHT_SEVERITY = 0.30
WEIGHT_IMPACT = 0.25
WEIGHT_EFFORT_INVERSE = 0.20
WEIGHT_STAGE_FIT = 0.15
WEIGHT_BUDGET_FIT = 0.10

# Severity scores (0-100)
SEVERITY_SCORES: Dict[str, float] = {
    "critical": 100.0,
    "high": 75.0,
    "medium": 50.0,
    "low": 25.0,
    "info": 10.0,
}

# Impact scores by action type (0-100).  Higher means more direct
# revenue impact.
IMPACT_SCORES: Dict[str, float] = {
    "ad_campaign": 85.0,
    "email_sequence": 80.0,
    "follow_up_sequence": 75.0,
    "kaicalls_setup": 75.0,
    "review_request": 70.0,
    "content_creation": 65.0,
    "website_update": 60.0,
    "social_post": 55.0,
    "gbp_update": 55.0,
    "reputation_action": 50.0,
    "seo_fix": 50.0,
    "analytics_fix": 40.0,
}

# Business stage fit multipliers.  Each action type gets a 0-1 multiplier
# reflecting how appropriate it is for the business's current stage.
STAGE_FIT: Dict[str, Dict[str, float]] = {
    "pre-launch": {
        "website_update": 1.0,
        "content_creation": 0.8,
        "seo_fix": 0.5,
        "ad_campaign": 0.3,
        "email_sequence": 0.6,
        "review_request": 0.2,
        "social_post": 0.7,
        "analytics_fix": 0.9,
        "gbp_update": 0.4,
        "kaicalls_setup": 0.7,
        "follow_up_sequence": 0.5,
        "reputation_action": 0.2,
    },
    "early-pmf": {
        "website_update": 0.9,
        "content_creation": 0.8,
        "seo_fix": 0.7,
        "ad_campaign": 0.5,
        "email_sequence": 0.7,
        "review_request": 0.8,
        "social_post": 0.6,
        "analytics_fix": 0.8,
        "gbp_update": 0.9,
        "kaicalls_setup": 0.9,
        "follow_up_sequence": 0.7,
        "reputation_action": 0.7,
    },
    "growth": {
        "website_update": 0.7,
        "content_creation": 0.8,
        "seo_fix": 0.8,
        "ad_campaign": 0.9,
        "email_sequence": 0.9,
        "review_request": 0.7,
        "social_post": 0.7,
        "analytics_fix": 0.6,
        "gbp_update": 0.7,
        "kaicalls_setup": 0.8,
        "follow_up_sequence": 0.8,
        "reputation_action": 0.6,
    },
    "scale": {
        "website_update": 0.5,
        "content_creation": 0.7,
        "seo_fix": 0.6,
        "ad_campaign": 1.0,
        "email_sequence": 0.9,
        "review_request": 0.5,
        "social_post": 0.8,
        "analytics_fix": 0.5,
        "gbp_update": 0.5,
        "kaicalls_setup": 0.6,
        "follow_up_sequence": 0.7,
        "reputation_action": 0.4,
    },
    "mature": {
        "website_update": 0.4,
        "content_creation": 0.6,
        "seo_fix": 0.5,
        "ad_campaign": 0.8,
        "email_sequence": 0.8,
        "review_request": 0.4,
        "social_post": 0.7,
        "analytics_fix": 0.4,
        "gbp_update": 0.4,
        "kaicalls_setup": 0.5,
        "follow_up_sequence": 0.6,
        "reputation_action": 0.3,
    },
}

# Deduplication thresholds
_TITLE_SIMILARITY_THRESHOLD = 0.80
_PAYLOAD_OVERLAP_THRESHOLD = 0.70

# Implicit dependency rules: (prerequisite_type, dependent_type)
_IMPLICIT_DEPENDENCY_RULES: List[Tuple[str, str]] = [
    ("analytics_fix", "ad_campaign"),
    ("content_creation", "ad_campaign"),
    ("website_update", "email_sequence"),
    ("reputation_action", "review_request"),
    ("kaicalls_setup", "website_update"),  # KaiCalls before click-to-call
]


# ============================================================================
# Ranking
# ============================================================================


def rank_actions(
    actions: List[Dict[str, Any]],
    business_stage: str = "early-pmf",
    monthly_budget: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Compute a multi-factor composite score for each action and sort.

    Five weighted factors are combined:
    1. Severity (30%) -- from the source finding's severity level.
    2. Impact (25%) -- from the action type's revenue-impact potential.
    3. Effort inverse (20%) -- smaller effort = higher score.
    4. Stage fit (15%) -- how appropriate for the current business stage.
    5. Budget fit (10%) -- how affordable relative to monthly budget.

    Each action's ``priority_score`` is updated with the composite score,
    and the list is returned sorted by score descending.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.
    business_stage:
        One of ``"pre-launch"``, ``"early-pmf"``, ``"growth"``,
        ``"scale"``, ``"mature"``.
    monthly_budget:
        Monthly marketing budget in USD.  None means unknown (neutral
        budget factor).

    Returns
    -------
    list[dict]
        Actions sorted by composite priority score, highest first.
    """
    scored = []
    for action in actions:
        action = copy.deepcopy(action)
        metadata = action.get("metadata", {})

        # Factor 1: Severity
        severity = metadata.get("finding_severity", "medium")
        # Fallback: use existing priority_score as proxy
        severity_factor = SEVERITY_SCORES.get(severity, action.get("priority_score", 50.0))

        # Factor 2: Impact
        action_type = action.get("action_type", "")
        impact_factor = IMPACT_SCORES.get(action_type, 50.0)

        # Factor 3: Effort inverse
        effort_hours = action.get("estimated_effort_hours") or 1.0
        effort_inverse = 100.0 - min(effort_hours * 10.0, 100.0)

        # Factor 4: Stage fit
        stage_multipliers = STAGE_FIT.get(business_stage, {})
        stage_fit = stage_multipliers.get(action_type, 0.5) * 100.0

        # Factor 5: Budget fit
        estimated_cost = action.get("estimated_cost") or 0.0
        if monthly_budget is None:
            budget_fit = 50.0
        elif monthly_budget <= 0:
            # No budget -- only free actions are affordable
            budget_fit = 90.0 if estimated_cost == 0 else 10.0
        else:
            cost_pct = estimated_cost / monthly_budget
            if cost_pct <= 0.10:
                budget_fit = 90.0
            elif cost_pct <= 0.25:
                budget_fit = 70.0
            elif cost_pct <= 0.50:
                budget_fit = 40.0
            else:
                budget_fit = 10.0

        # Composite score
        composite = (
            WEIGHT_SEVERITY * severity_factor
            + WEIGHT_IMPACT * impact_factor
            + WEIGHT_EFFORT_INVERSE * effort_inverse
            + WEIGHT_STAGE_FIT * stage_fit
            + WEIGHT_BUDGET_FIT * budget_fit
        )

        # Clamp to [0, 100]
        composite = max(0.0, min(100.0, round(composite, 2)))
        action["priority_score"] = composite

        # Store factor breakdown in metadata for transparency
        action.setdefault("metadata", {})
        action["metadata"]["ranking_factors"] = {
            "severity": round(severity_factor, 2),
            "impact": round(impact_factor, 2),
            "effort_inverse": round(effort_inverse, 2),
            "stage_fit": round(stage_fit, 2),
            "budget_fit": round(budget_fit, 2),
            "composite": composite,
        }

        scored.append(action)

    scored.sort(key=lambda a: a["priority_score"], reverse=True)
    return scored


# ============================================================================
# Deduplication
# ============================================================================


def deduplicate_actions(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Detect and merge duplicate or near-duplicate actions.

    Duplicates are detected using three signals:
    1. **Exact match** -- same ``action_type`` + ``channel`` + target
       page/platform in ``suggested_payload``.
    2. **Title similarity** -- normalized titles with > 80% token overlap.
    3. **Payload overlap** -- same ``action_type`` and > 70% key overlap
       in ``suggested_payload``.

    When duplicates are found, the higher-scored action is kept, tags are
    merged (union), source finding IDs are collected, and the richer
    description is preserved.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts, ideally already ranked.

    Returns
    -------
    list[dict]
        Deduplicated list with merged metadata.
    """
    if not actions:
        return []

    # Sort by priority so we keep the highest-scored duplicate
    sorted_actions = sorted(
        actions, key=lambda a: a.get("priority_score", 0), reverse=True
    )

    kept: List[Dict[str, Any]] = []
    merged_ids: Set[str] = set()

    for action in sorted_actions:
        action_id = action.get("id", "")
        if action_id in merged_ids:
            continue

        # Check against all already-kept actions for duplicates
        is_dup = False
        for kept_action in kept:
            if _is_duplicate(action, kept_action):
                # Merge into the kept action
                _merge_actions(kept_action, action)
                merged_ids.add(action_id)
                is_dup = True
                break

        if not is_dup:
            # Deep copy to avoid mutation issues
            kept.append(copy.deepcopy(action))

    return kept


def _normalize_title(title: str) -> str:
    """Normalize a title for comparison by lowercasing and stripping specifics.

    Removes page-specific references, curly-brace placeholders, extra
    whitespace, and common filler words.
    """
    import re as _re

    normalized = title.lower()
    # Remove placeholder patterns like {page}, {topic}, etc.
    normalized = _re.sub(r"\{[^}]+\}", "", normalized)
    # Remove common page-specific phrases
    normalized = _re.sub(r"on\s+(homepage|contact|about|service\s+page)", "", normalized)
    # Collapse whitespace
    normalized = _re.sub(r"\s+", " ", normalized).strip()
    return normalized


def _title_similarity(title_a: str, title_b: str) -> float:
    """Compute token-overlap similarity between two normalized titles.

    Returns a float from 0.0 (no overlap) to 1.0 (identical tokens).
    Uses Jaccard similarity: ``|intersection| / |union|``.
    """
    norm_a = _normalize_title(title_a)
    norm_b = _normalize_title(title_b)

    words_a = set(norm_a.split())
    words_b = set(norm_b.split())

    if not words_a and not words_b:
        return 1.0
    if not words_a or not words_b:
        return 0.0

    intersection = words_a & words_b
    union = words_a | words_b
    return len(intersection) / len(union)


def _payload_key_overlap(payload_a: Dict[str, Any], payload_b: Dict[str, Any]) -> float:
    """Compute key-set overlap ratio between two payload dicts.

    Returns ``|intersection| / |union|`` of top-level keys.
    """
    keys_a = set(payload_a.keys())
    keys_b = set(payload_b.keys())

    if not keys_a and not keys_b:
        return 1.0
    if not keys_a or not keys_b:
        return 0.0

    intersection = keys_a & keys_b
    union = keys_a | keys_b
    return len(intersection) / len(union)


def _is_duplicate(action_a: Dict[str, Any], action_b: Dict[str, Any]) -> bool:
    """Determine whether two actions are duplicates using three signals."""
    type_a = action_a.get("action_type", "")
    type_b = action_b.get("action_type", "")
    channel_a = action_a.get("channel", "")
    channel_b = action_b.get("channel", "")

    # Signal 1: Exact match on type + channel + target
    if type_a == type_b and channel_a == channel_b:
        payload_a = action_a.get("suggested_payload", {})
        payload_b = action_b.get("suggested_payload", {})
        target_a = payload_a.get("page", payload_a.get("platform", ""))
        target_b = payload_b.get("page", payload_b.get("platform", ""))
        if target_a and target_b and target_a == target_b:
            return True

    # Signal 2: Title similarity above threshold
    title_a = action_a.get("title", "")
    title_b = action_b.get("title", "")
    if _title_similarity(title_a, title_b) > _TITLE_SIMILARITY_THRESHOLD:
        return True

    # Signal 3: Same type + high payload key overlap
    if type_a == type_b:
        payload_a = action_a.get("suggested_payload", {})
        payload_b = action_b.get("suggested_payload", {})
        if _payload_key_overlap(payload_a, payload_b) > _PAYLOAD_OVERLAP_THRESHOLD:
            # Also require title similarity > 50% to avoid false positives
            # on actions of the same type but different targets
            if _title_similarity(title_a, title_b) > 0.50:
                return True

    return False


def _merge_actions(primary: Dict[str, Any], secondary: Dict[str, Any]) -> None:
    """Merge *secondary* into *primary*, mutating primary in place.

    Merges tags (union), collects source finding IDs, preserves the
    longer description, and marks the action as deduplicated.
    """
    # Merge tags
    primary_tags = set(primary.get("tags", []))
    secondary_tags = set(secondary.get("tags", []))
    primary["tags"] = sorted(primary_tags | secondary_tags)

    # Collect source finding IDs
    primary.setdefault("metadata", {})
    merged_ids = primary["metadata"].get("merged_finding_ids", [])
    primary_source = primary.get("source_finding_id", "")
    secondary_source = secondary.get("source_finding_id", "")
    if primary_source and primary_source not in merged_ids:
        merged_ids.append(primary_source)
    if secondary_source and secondary_source not in merged_ids:
        merged_ids.append(secondary_source)
    primary["metadata"]["merged_finding_ids"] = merged_ids
    primary["metadata"]["deduplicated"] = True

    # Keep the longer (richer) description
    primary_desc = primary.get("description", "")
    secondary_desc = secondary.get("description", "")
    if len(secondary_desc) > len(primary_desc):
        primary["description"] = secondary_desc


# ============================================================================
# Dependency Resolution
# ============================================================================


def resolve_dependencies(actions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Order actions respecting explicit and implicit dependencies.

    Builds a dependency graph from each action's ``depends_on`` list and
    adds implicit edges based on action type relationships (e.g.,
    tracking setup before campaign launch).  Performs a topological sort
    using Kahn's algorithm.  Cycles are broken by removing the
    lowest-priority edge.

    Parameters
    ----------
    actions:
        List of ProposedAction dicts.

    Returns
    -------
    list[dict]
        Actions in dependency-valid execution order, with priority
        ordering preserved within each dependency level.
    """
    if not actions:
        return []

    # Build an index for fast lookup
    action_map: Dict[str, Dict[str, Any]] = {}
    for action in actions:
        action_id = action.get("id", "")
        if action_id:
            action_map[action_id] = action

    # Build dependency graph
    graph = _build_dependency_graph(actions, action_map)

    # Topological sort
    sorted_ids = _topological_sort(graph, action_map)

    # Reconstruct ordered list, including any actions not in the graph
    ordered: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for action_id in sorted_ids:
        if action_id in action_map and action_id not in seen:
            ordered.append(action_map[action_id])
            seen.add(action_id)

    # Append any actions that weren't in the graph (no ID, etc.)
    for action in actions:
        action_id = action.get("id", "")
        if action_id not in seen:
            ordered.append(action)
            if action_id:
                seen.add(action_id)

    return ordered


def _build_dependency_graph(
    actions: List[Dict[str, Any]],
    action_map: Dict[str, Dict[str, Any]],
) -> Dict[str, List[str]]:
    """Build an adjacency list of action dependencies.

    Combines explicit ``depends_on`` edges with implicit edges derived
    from action type relationships.

    Returns a dict mapping ``action_id`` to a list of action IDs that
    must complete before it (its prerequisites).
    """
    # Initialize empty adjacency list for all known actions
    graph: Dict[str, List[str]] = {
        action.get("id", ""): [] for action in actions if action.get("id")
    }

    # Add explicit dependencies
    for action in actions:
        action_id = action.get("id", "")
        if not action_id:
            continue
        for dep_id in action.get("depends_on", []):
            if dep_id in action_map and dep_id != action_id:
                graph[action_id].append(dep_id)

    # Add implicit dependencies based on action type rules
    # Group actions by type for efficient lookup
    actions_by_type: Dict[str, List[str]] = defaultdict(list)
    for action in actions:
        action_id = action.get("id", "")
        action_type = action.get("action_type", "")
        if action_id and action_type:
            actions_by_type[action_type].append(action_id)

    for prereq_type, dependent_type in _IMPLICIT_DEPENDENCY_RULES:
        prereq_ids = actions_by_type.get(prereq_type, [])
        dependent_ids = actions_by_type.get(dependent_type, [])

        if not prereq_ids or not dependent_ids:
            continue

        # Special case: kaicalls_setup -> website_update only for
        # click-to-call type website updates
        if prereq_type == "kaicalls_setup" and dependent_type == "website_update":
            for dep_id in dependent_ids:
                dep_action = action_map.get(dep_id, {})
                dep_tags = dep_action.get("tags", [])
                dep_title = dep_action.get("title", "").lower()
                if "click_to_call" in dep_tags or "click-to-call" in dep_title:
                    for pre_id in prereq_ids:
                        if pre_id != dep_id and pre_id not in graph.get(dep_id, []):
                            graph.setdefault(dep_id, []).append(pre_id)
            continue

        # Special case: content_creation -> ad_campaign only if the
        # ad campaign references a landing page
        if prereq_type == "content_creation" and dependent_type == "ad_campaign":
            for dep_id in dependent_ids:
                dep_action = action_map.get(dep_id, {})
                payload = dep_action.get("suggested_payload", {})
                if payload.get("landing_page"):
                    for pre_id in prereq_ids:
                        pre_action = action_map.get(pre_id, {})
                        pre_tags = pre_action.get("tags", [])
                        if ("landing_page" in pre_tags or "service_page" in pre_tags
                                or "content" in pre_tags):
                            if pre_id != dep_id and pre_id not in graph.get(dep_id, []):
                                graph.setdefault(dep_id, []).append(pre_id)
            continue

        # General case: all actions of prereq_type should come before
        # all actions of dependent_type
        for dep_id in dependent_ids:
            for pre_id in prereq_ids:
                if pre_id != dep_id and pre_id not in graph.get(dep_id, []):
                    graph.setdefault(dep_id, []).append(pre_id)

    return graph


def _topological_sort(
    graph: Dict[str, List[str]],
    action_map: Dict[str, Dict[str, Any]],
) -> List[str]:
    """Topological sort using Kahn's algorithm with priority ordering.

    Within each level (actions whose dependencies are all resolved),
    actions are ordered by ``priority_score`` descending so higher-value
    work is scheduled first within its dependency tier.

    If a cycle is detected, the lowest-priority edge is removed to break
    it, and sorting continues.

    Parameters
    ----------
    graph:
        Adjacency list mapping action_id to its prerequisite IDs.
    action_map:
        Lookup dict from action_id to action dict.

    Returns
    -------
    list[str]
        Action IDs in valid execution order.
    """
    # Compute in-degree for each node
    all_nodes: Set[str] = set(graph.keys())
    for deps in graph.values():
        for dep in deps:
            all_nodes.add(dep)

    in_degree: Dict[str, int] = {node: 0 for node in all_nodes}
    # Build a forward adjacency list (node -> list of nodes that depend on it)
    forward: Dict[str, List[str]] = defaultdict(list)
    for node, deps in graph.items():
        for dep in deps:
            forward[dep].append(node)
            in_degree[node] = in_degree.get(node, 0) + 1

    # Initialize the queue with nodes that have no prerequisites
    queue: List[str] = [
        node for node in all_nodes if in_degree.get(node, 0) == 0
    ]
    # Sort initial queue by priority descending
    queue.sort(
        key=lambda nid: action_map.get(nid, {}).get("priority_score", 0),
        reverse=True,
    )

    result: List[str] = []
    visited: Set[str] = set()

    max_iterations = len(all_nodes) * 2  # Safety bound for cycle breaking
    iteration = 0

    while queue and iteration < max_iterations:
        iteration += 1

        # Pick highest-priority node from the queue
        queue.sort(
            key=lambda nid: action_map.get(nid, {}).get("priority_score", 0),
            reverse=True,
        )
        node = queue.pop(0)

        if node in visited:
            continue
        visited.add(node)
        result.append(node)

        # Reduce in-degree for dependents
        for dependent in forward.get(node, []):
            in_degree[dependent] = in_degree.get(dependent, 1) - 1
            if in_degree[dependent] <= 0 and dependent not in visited:
                queue.append(dependent)

    # Handle cycles: any remaining unvisited nodes have unresolved dependencies
    remaining = [n for n in all_nodes if n not in visited]
    if remaining:
        # Break cycles by processing remaining nodes in priority order
        remaining.sort(
            key=lambda nid: action_map.get(nid, {}).get("priority_score", 0),
            reverse=True,
        )
        for node in remaining:
            if node not in visited:
                visited.add(node)
                result.append(node)
                # Mark the cycle break in metadata
                if node in action_map:
                    action_map[node].setdefault("metadata", {})
                    action_map[node]["metadata"]["cycle_broken"] = True

    return result


# ============================================================================
# Pipeline entry point
# ============================================================================


def process_actions(
    actions: List[Dict[str, Any]],
    business_stage: str = "early-pmf",
    monthly_budget: Optional[float] = None,
) -> List[Dict[str, Any]]:
    """Full processing pipeline: rank, deduplicate, resolve dependencies.

    This is the recommended entry point for consumers.  It chains the
    three processing steps in the correct order.

    Parameters
    ----------
    actions:
        Raw list of ProposedAction dicts from the action mapper.
    business_stage:
        Current business stage for stage-fit scoring.
    monthly_budget:
        Monthly marketing budget in USD for budget-fit scoring.

    Returns
    -------
    list[dict]
        Clean, ranked, deduped, dependency-ordered list of actions.
    """
    ranked = rank_actions(actions, business_stage=business_stage, monthly_budget=monthly_budget)
    deduped = deduplicate_actions(ranked)
    ordered = resolve_dependencies(deduped)
    return ordered
