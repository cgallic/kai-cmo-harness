# Task 074: Build memory layer schemas

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 13. Memory and Learning Loop
**Priority:** P2
**Depends on:** 073, 001
**Estimated complexity:** Medium

## Context

The memory writeback system (Task 073) produces Learning objects — but these raw learnings need to be organized into structured memory layers that downstream systems can query efficiently. Each memory layer represents a different domain of knowledge about the business: confirmed facts, brand preferences, proof assets, channel performance, offer insights, and audience behavior. These schemas define what each layer stores, how it is structured in YAML files on disk, and when learnings become stale and need re-validation. The retrieval system (Task 075) reads from these layers.

## Scope

Create `kai/memory/schemas.py` containing six structured memory layer schemas, their storage format definitions, and staleness rules.

## Detailed Requirements

### File: `kai/memory/schemas.py`

Use the dataclass + `SerializableModel` pattern from `kai/runtime/models.py`.

**Enum: MemoryStatus**
- `active` — currently valid and used for decision-making
- `stale` — past its freshness date, needs re-validation
- `archived` — superseded by newer information, kept for history
- `pending` — awaiting operator confirmation

**Model: MemoryMetadata**
- `created_at: str` — ISO timestamp when first stored
- `updated_at: str` — ISO timestamp of last update
- `source_learning_ids: List[str]` — which Learning objects contributed to this memory
- `confidence: str` — highest confidence level from contributing learnings
- `confirmation_count: int` — how many times this has been confirmed (more = stronger)
- `last_confirmed_at: Optional[str]` — when last explicitly confirmed
- `status: str` — MemoryStatus enum value
- `staleness_days: int` — how many days before this needs re-validation
- `notes: Optional[str]` — operator notes

**Model: BusinessFactEntry**
- `fact_id: str` — format `fact_{uuid_hex[:8]}`
- `category: str` — "hours", "services", "pricing", "staff", "locations", "contact", "equipment", "certifications", "insurance", "other"
- `key: str` — machine-readable key (e.g., "business_hours_monday")
- `value: Any` — the fact value
- `previous_value: Optional[Any]` — what it was before (for change tracking)
- `change_date: Optional[str]` — when this fact changed
- `source: str` — "operator_update", "website_scan", "gbp_sync", "auto_detected"
- `metadata: MemoryMetadata`

**Model: BusinessFactMemory**
- `business_id: str`
- `facts: List[BusinessFactEntry]`
- `last_full_sync: Optional[str]` — when all facts were last verified in bulk
- Staleness rule: 90 days for general facts, 30 days for hours/pricing, 180 days for certifications
- `get_fact(self, key: str) -> Optional[BusinessFactEntry]` — lookup by key
- `get_facts_by_category(self, category: str) -> List[BusinessFactEntry]`
- `get_stale_facts(self) -> List[BusinessFactEntry]` — return facts past their staleness date
- Storage format: `workspace/{business_id}/memory/business_facts.yaml`

**Model: BrandConstraintEntry**
- `constraint_id: str` — format `bc_{uuid_hex[:8]}`
- `constraint_type: str` — "tone_preference", "style_preference", "cta_preference", "image_preference", "topic_preference", "formatting_preference", "channel_preference"
- `description: str` — human-readable description (e.g., "Prefers formal tone in all email communications")
- `rule: str` — machine-readable rule (e.g., "tone=formal for content_type=email")
- `positive: bool` — True if this is something the business DOES want, False if something to AVOID
- `strength: int` — 1-5, how strongly this preference was expressed (5 = explicit operator instruction, 1 = inferred from single data point)
- `source_events: List[str]` — "approval", "rejection", "explicit_instruction"
- `examples: List[Dict[str, str]]` — {good: str, bad: str} example pairs
- `metadata: MemoryMetadata`

**Model: BrandConstraintMemory**
- `business_id: str`
- `constraints: List[BrandConstraintEntry]`
- Staleness rule: 180 days (brand preferences are relatively stable)
- `get_constraints_for_content_type(self, content_type: str) -> List[BrandConstraintEntry]`
- `get_positive_preferences(self) -> List[BrandConstraintEntry]`
- `get_negative_constraints(self) -> List[BrandConstraintEntry]`
- Storage format: `workspace/{business_id}/memory/brand_constraints.yaml`

**Model: ProofAssetEntry**
- `asset_id: str` — format `proof_{uuid_hex[:8]}`
- `asset_type: str` — "testimonial", "case_study", "before_after", "certification", "award", "media_mention", "statistic", "review_highlight"
- `content: str` — the actual proof content (quote, stat, description)
- `source: str` — where this came from (customer name, review platform, certification body)
- `date_collected: str` — when this proof was collected
- `performance_data: Dict[str, Any]` — how this proof performs: {times_used, engagement_rate, conversion_lift, best_placement}
- `approved_for: List[str]` — content types this can be used in
- `consent_status: str` — "full_consent", "verbal_consent", "no_consent_needed", "pending"
- `metadata: MemoryMetadata`

**Model: ProofAssetMemory**
- `business_id: str`
- `assets: List[ProofAssetEntry]`
- Staleness rule: 365 days for testimonials, 180 days for statistics, never for certifications/awards
- `get_best_performing(self, limit: int = 5) -> List[ProofAssetEntry]` — sorted by engagement/conversion performance
- `get_by_type(self, asset_type: str) -> List[ProofAssetEntry]`
- `get_approved_for_content_type(self, content_type: str) -> List[ProofAssetEntry]`
- Storage format: `workspace/{business_id}/memory/proof_assets.yaml`

**Model: ChannelLearningEntry**
- `learning_id: str` — format `chl_{uuid_hex[:8]}`
- `channel: str` — "google_ads", "meta_ads", "email", "social_facebook", "social_instagram", "social_linkedin", "social_tiktok", "organic_search", "gbp"
- `insight_type: str` — "best_posting_time", "best_ad_format", "best_audience_segment", "best_creative_type", "best_subject_line_pattern", "optimal_frequency", "optimal_budget", "platform_algorithm_note"
- `insight: str` — the actual insight (e.g., "Tuesday 10am posts get 2.3x engagement")
- `data_points: int` — how many data points support this insight
- `effect_size: Optional[float]` — quantified impact (e.g., 2.3 for 2.3x improvement)
- `time_period: str` — period the data covers (e.g., "2025-10 to 2026-03")
- `metadata: MemoryMetadata`

**Model: ChannelLearningMemory**
- `business_id: str`
- `learnings: List[ChannelLearningEntry]`
- Staleness rule: 90 days (channel algorithms and performance change frequently)
- `get_learnings_for_channel(self, channel: str) -> List[ChannelLearningEntry]`
- `get_learnings_by_type(self, insight_type: str) -> List[ChannelLearningEntry]`
- `get_strongest_insights(self, min_data_points: int = 5) -> List[ChannelLearningEntry]` — only return insights with sufficient data
- Storage format: `workspace/{business_id}/memory/channel_learnings.yaml`

**Model: OfferLearningEntry**
- `learning_id: str` — format `ofl_{uuid_hex[:8]}`
- `offer_type: str` — "discount", "bundle", "free_consultation", "guarantee", "urgency", "seasonal", "loyalty", "referral", "financing"
- `offer_description: str` — what the offer was
- `channel: str` — where it was used
- `conversion_rate: Optional[float]` — conversion rate achieved
- `revenue_impact: Optional[float]` — revenue generated
- `cost: Optional[float]` — cost of the offer (discounts, etc.)
- `net_impact: Optional[float]` — revenue_impact - cost
- `time_period: str` — when this offer ran
- `seasonal_relevance: Optional[str]` — "spring", "summer", "fall", "winter", "holiday", "back_to_school", etc.
- `audience_segment: Optional[str]` — which audience this worked for
- `metadata: MemoryMetadata`

**Model: OfferLearningMemory**
- `business_id: str`
- `learnings: List[OfferLearningEntry]`
- Staleness rule: 180 days for general, refresh before each seasonal period
- `get_best_offers(self, limit: int = 5) -> List[OfferLearningEntry]` — by net_impact
- `get_seasonal_offers(self, season: str) -> List[OfferLearningEntry]`
- `get_offers_for_channel(self, channel: str) -> List[OfferLearningEntry]`
- Storage format: `workspace/{business_id}/memory/offer_learnings.yaml`

**Model: AudienceLearningEntry**
- `learning_id: str` — format `aud_{uuid_hex[:8]}`
- `audience_type: str` — "demographic", "behavioral", "psychographic", "persona_match"
- `segment_description: str` — description of the audience segment
- `insight: str` — what was learned about this segment
- `response_to_message_type: Optional[str]` — which message type they respond to best
- `preferred_channel: Optional[str]` — which channel they engage on most
- `conversion_rate: Optional[float]`
- `ltv_estimate: Optional[float]`
- `data_points: int`
- `metadata: MemoryMetadata`

**Model: AudienceLearningMemory**
- `business_id: str`
- `learnings: List[AudienceLearningEntry]`
- Staleness rule: 120 days
- `get_learnings_by_type(self, audience_type: str) -> List[AudienceLearningEntry]`
- `get_highest_value_segments(self, limit: int = 5) -> List[AudienceLearningEntry]`
- Storage format: `workspace/{business_id}/memory/audience_learnings.yaml`

**Function: load_memory_layer(business_id: str, layer_name: str, base_dir: str) -> Any**
- Load a memory layer from disk (YAML file)
- Layer names: "business_facts", "brand_constraints", "proof_assets", "channel_learnings", "offer_learnings", "audience_learnings"
- Return the appropriate memory model, or an empty instance if file doesn't exist
- Handle malformed YAML gracefully (return empty instance + log warning)

**Function: save_memory_layer(memory_layer: Any, base_dir: str)**
- Save a memory layer to its YAML file on disk
- Use atomic write pattern
- Create directories if they don't exist

**Function: get_all_stale_entries(business_id: str, base_dir: str) -> Dict[str, List]**
- Check all memory layers for stale entries
- Return dict of {layer_name: [stale_entries]}
- Used by watchers or periodic review to surface items needing re-validation

## Output Files

- `kai/memory/schemas.py`

## Acceptance Criteria

- File parses as valid Python
- All six memory layer models are complete with query methods
- Each memory layer has an explicit staleness rule with appropriate duration
- MemoryMetadata tracks creation, update, confirmation count, and status
- BusinessFactMemory has category-specific staleness rules (30 days for pricing, 90 for general)
- BrandConstraintMemory distinguishes positive preferences from negative constraints
- ProofAssetMemory tracks consent status and performance data
- ChannelLearningMemory filters by minimum data points for "strong" insights
- Load/save functions handle missing files and malformed data gracefully
- YAML is the storage format (import yaml with try/except fallback to json)
- All storage paths follow the `workspace/{business_id}/memory/` convention
- `get_all_stale_entries` checks all layers and returns a comprehensive stale list

## Reference Materials

- `kai/memory/writeback.py` (Task 073) — Learning model, LearningCategory
- `kai/runtime/business_profile.py` — BusinessProfile (for business facts context)
- `kai/runtime/models.py` — SerializableModel pattern
- `kai/runtime/actions.py` — file I/O patterns, atomic writes
- `kai/runtime/store.py` — workspace storage directory conventions
