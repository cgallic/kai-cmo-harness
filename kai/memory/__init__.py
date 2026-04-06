"""Memory and learning loop for the Kai Marketing OS.

This module implements the write path of Kai's persistent learning system.
Every time an action is approved, rejected, executed, measured, or receives
operator feedback, the writeback system captures structured learnings and
persists them to disk.  Over time these learnings accumulate into a rich
understanding of what works for a specific business -- which headlines
convert, which offers resonate, which channels deliver ROI, and which
creative styles the operator prefers.

The write path lives in :mod:`kai.memory.writeback`; the retrieval/read
path lives in :mod:`kai.memory.retrieval`.

Submodules
----------
writeback
    The :class:`MemoryWriteback` engine, :class:`Learning` and
    :class:`WritebackEvent` models, and all eight trigger handlers that
    extract structured learnings from marketing events.

retrieval
    The :class:`MemoryRetriever` engine, :class:`RetrievalContext`,
    :class:`RetrievedMemory`, and :class:`MemoryBrief` models.  Five
    context-specific retrieval methods surface relevant learnings for
    the proposal engine, creative engine, approval router, watcher
    system, and audit subsystem.

anti_patterns
    The :class:`AntiPatternMemory` and :class:`AntiPatternMatcher` for
    tracking what does NOT work, plus :class:`ArchetypeDefaultImprovement`
    for aggregating cross-business learnings into archetype default
    improvement suggestions.

Quick start (write path)::

    from kai.memory import (
        MemoryWriteback,
        Learning,
        WritebackEvent,
        LearningCategory,
        LearningConfidence,
        WritebackTrigger,
    )

    wb = MemoryWriteback(memory_dir="workspace/biz_123/memory")
    event = WritebackEvent(
        trigger=WritebackTrigger.ACTION_APPROVED.value,
        action_id="act_a1b2c3d4e5f6",
        business_id="biz_123",
        event_data={"action_type": "email_sequence", "title": "Welcome drip"},
        timestamp="2026-04-02T12:00:00+00:00",
    )
    learnings = wb.process_event(event)

Quick start (read path)::

    from kai.memory import MemoryRetriever, RetrievalContext

    retriever = MemoryRetriever(base_dir="workspace")
    brief = retriever.retrieve_for_creative(
        business_id="biz_123",
        content_type="blog_post",
        channel="organic_search",
        audience="small_business_owners",
    )
    print(brief.key_constraints)
    print(brief.winning_patterns)

Quick start (anti-patterns)::

    from kai.memory import (
        AntiPatternMemory,
        AntiPatternMatcher,
        load_anti_pattern_memory,
        save_anti_pattern_memory,
    )

    memory = load_anti_pattern_memory("biz_123", "workspace")
    matcher = AntiPatternMatcher(memory)

    # Check a proposal against known failures
    matches = matcher.check_proposal(
        action_type="social_post",
        channel="instagram",
        content_type="carousel",
        content_features={"tone": "aggressive", "cta_type": "discount"},
    )

    # Record a new failure
    entry = matcher.record_anti_pattern(
        action_id="act_abc123",
        business_id="biz_123",
        anti_pattern_type="rejected_content",
        action_type="social_post",
        channel="instagram",
        content_type="carousel",
        failure_reason="operator_rejected",
        specific_feedback="Too aggressive, prefer value framing",
    )
    save_anti_pattern_memory(memory, "workspace")
"""

from kai.memory.anti_patterns import (
    AntiPatternEntry,
    AntiPatternMatcher,
    AntiPatternMemory,
    AntiPatternType,
    ArchetypeAggregate,
    ArchetypeDefaultImprovement,
    DefaultImprovementSuggestion,
    load_anti_pattern_memory,
    save_anti_pattern_memory,
)
from kai.memory.retrieval import (
    MemoryBrief,
    MemoryRetriever,
    RetrievalContext,
    RetrievedMemory,
)
from kai.memory.writeback import (
    Learning,
    LearningCategory,
    LearningConfidence,
    MemoryWriteback,
    WritebackEvent,
    WritebackTrigger,
)

__all__ = [
    # Anti-patterns
    "AntiPatternEntry",
    "AntiPatternMatcher",
    "AntiPatternMemory",
    "AntiPatternType",
    "ArchetypeAggregate",
    "ArchetypeDefaultImprovement",
    "DefaultImprovementSuggestion",
    "load_anti_pattern_memory",
    "save_anti_pattern_memory",
    # Retrieval (read path)
    "MemoryBrief",
    "MemoryRetriever",
    "RetrievalContext",
    "RetrievedMemory",
    # Writeback (write path)
    "Learning",
    "LearningCategory",
    "LearningConfidence",
    "MemoryWriteback",
    "WritebackEvent",
    "WritebackTrigger",
]
