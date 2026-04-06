# Task 048: Build creative variant workflow and inventory tracking

> **SAFETY:** Do NOT run tests, execute scripts, start servers, or run any commands that could crash the system. This is a DESIGN AND WRITE task only. Read files, write files, create schemas — but do not execute anything.

**Workstream:** 8. Paid Media Operations
**Priority:** P2
**Depends on:** 046, 029
**Estimated complexity:** Medium

## Context

Ad creative is not a one-shot effort — it degrades over time as audiences see the same message repeatedly, and the only way to maintain performance is continuous testing of variants. This module manages the lifecycle of ad creative variants: generating them from a base creative, tracking which variant is winning, determining statistical significance, promoting winners, and flagging stale creatives that need refreshing. It sits between the creative generation system (Task 029) and the ad platform connectors (Task 044), ensuring the paid media system always has fresh, tested creative options.

## Scope

Create `kai/paid_media/variants.py` containing the CreativeVariant model, VariantWorkflow manager, CreativeInventory tracker, freshness scoring, and winner promotion logic.

## Detailed Requirements

### File: `kai/paid_media/variants.py`

Use the same Pydantic import fallback pattern from `gateway/models.py`.

**Enum: VariantStatus (str, Enum)**
- `draft` — variant created but not yet deployed
- `testing` — actively being tested (live in rotation)
- `winning` — declared winner based on statistical test
- `losing` — declared loser based on statistical test
- `inconclusive` — test didn't reach significance
- `retired` — removed from rotation
- `promoted` — winning variant promoted to replace the original

**Enum: VariantTestElement (str, Enum)**
- `headline` — testing different headlines
- `description` — testing different descriptions
- `image` — testing different images
- `video` — testing different videos
- `cta` — testing different calls-to-action
- `landing_page` — testing different landing pages
- `audience` — testing different audience segments
- `format` — testing different ad formats (image vs video vs carousel)

**Model: CreativeVariant**
- `id: str` — format `cv_{uuid_hex[:12]}`
- `base_creative_id: str` — ID of the original/parent ad creative
- `campaign_id: str`
- `ad_group_id: str`
- `platform: str`
- `variant_type: str` — VariantTestElement value
- `variant_label: str` — human-readable label (e.g., "Headline Test: Question Hook", "CTA: Book Now vs Get Quote")
- `variant_content: Dict[str, Any]` — the actual changed content, default empty dict. Structure depends on variant_type:
  - headline: {"headlines": ["new headline 1", "new headline 2"]}
  - description: {"descriptions": ["new description"]}
  - image: {"media_urls": ["new_image_url"]}
  - cta: {"cta": "new cta text"}
  - landing_page: {"landing_url": "new url"}
- `status: str` — VariantStatus value, default "draft"
- `platform_ad_id: Optional[str]` — platform-assigned ad ID once deployed
- `test_start_date: Optional[str]` — ISO date when testing began
- `test_end_date: Optional[str]` — ISO date when test was concluded
- `performance: Dict[str, float]` — latest performance metrics: impressions, clicks, ctr, conversions, cpa, roas, default empty dict
- `sample_size: int = 0` — total impressions or clicks (depending on test metric)
- `confidence_level: float = 0.0` — statistical confidence (0-1), 0.95 = 95% confidence
- `lift_vs_control: Optional[float]` — percentage lift vs control (e.g., 0.15 = 15% better)
- `is_control: bool = False` — whether this is the control (original) variant
- `created_at: Optional[str]`
- `updated_at: Optional[str]`
- `metadata: Dict[str, Any]` — default empty dict

**Model: VariantTest**
- `id: str` — format `vt_{uuid_hex[:12]}`
- `base_creative_id: str`
- `campaign_id: str`
- `platform: str`
- `test_element: str` — VariantTestElement value
- `hypothesis: str` — what we're testing and why (e.g., "Question-based headlines will generate higher CTR than statement headlines")
- `variants: List[str]` — list of CreativeVariant IDs in this test (including control)
- `control_variant_id: str` — which variant is the control
- `primary_metric: str` — the metric being optimized: "ctr", "conversion_rate", "cpa", "roas"
- `minimum_sample_size: int = 1000` — minimum impressions per variant before evaluation
- `significance_threshold: float = 0.95` — required confidence to declare a winner
- `status: str` — "running", "completed", "cancelled", default "running"
- `winner_id: Optional[str]` — ID of the winning variant (if test completed)
- `result_summary: Optional[str]` — human-readable summary of test results
- `started_at: Optional[str]`
- `completed_at: Optional[str]`
- `metadata: Dict[str, Any]` — default empty dict

**Model: CreativeInventoryItem**
- `id: str` — format `ci_{uuid_hex[:12]}`
- `platform: str`
- `campaign_id: Optional[str]` — campaign this creative is used in
- `ad_group_id: Optional[str]`
- `format: str` — ad format
- `headlines: List[str]` — default empty list
- `descriptions: List[str]` — default empty list
- `media_refs: List[str]` — default empty list
- `landing_url: Optional[str]`
- `cta: Optional[str]`
- `status: str` — "active", "paused", "retired", "disapproved", default "active"
- `created_at: Optional[str]`
- `first_served_at: Optional[str]` — when the creative first received impressions
- `days_active: int = 0` — how many days this creative has been running
- `freshness_score: float = 1.0` — 1.0 = fresh, degrades over time (see scoring formula)
- `performance_trend: str` — "improving", "stable", "declining", "no_data", default "no_data"
- `last_performance_check: Optional[str]`
- `needs_refresh: bool = False` — flagged when freshness_score drops below threshold
- `variant_count: int = 0` — how many variants have been tested against this creative
- `last_variant_test: Optional[str]` — date of last variant test
- `metadata: Dict[str, Any]` — default empty dict

**Class: VariantWorkflow**

Manages the lifecycle of creative variant testing.

Methods:
- `__init__(self, significance_threshold: float = 0.95, min_sample_size: int = 1000)` — set testing parameters
- `generate_variants(self, base_creative: Dict[str, Any], test_element: str, count: int = 3) -> List[CreativeVariant]`:
  - Given a base creative and which element to test, generate variant specs.
  - For `headline`: generate `count` alternative headline sets based on different angles:
    - Question-based: turn the value prop into a question
    - Number-based: lead with a number/statistic
    - Fear-based: address a pain point or risk
    - Benefit-led: lead with the primary benefit
    - Social-proof: lead with a testimonial or result
  - For `description`: vary the description using different frameworks (benefit-first, problem-first, social-proof-first)
  - For `cta`: generate alternative CTAs (e.g., "Book Now", "Get Quote", "Call Today", "See Pricing", "Learn More")
  - For `image`: create variant specs describing what different images should show (the actual image generation is handled by Task 029)
  - One variant is always marked as `is_control=True`
  - Return list of CreativeVariant objects with status "draft"

- `create_test(self, base_creative_id: str, variants: List[CreativeVariant], primary_metric: str = "ctr", hypothesis: Optional[str] = None) -> VariantTest`:
  - Create a VariantTest from the base creative and generated variants
  - Auto-generate hypothesis if not provided based on test_element and variant contents
  - Return VariantTest with status "running"

- `evaluate_test(self, test: VariantTest, variant_performance: Dict[str, Dict[str, float]]) -> VariantTest`:
  - Given performance data for each variant, determine if there's a winner.
  - `variant_performance` maps variant_id -> {"impressions": x, "clicks": x, "conversions": x, "ctr": x, "cpa": x, "roas": x}
  - Check if minimum_sample_size is met for all variants.
  - If not enough data: set test status to "running" (still), return
  - If enough data: run simplified statistical significance check:
    - For CTR: use normal approximation to compare proportions. Calculate z-score = (p1 - p2) / sqrt(p_combined * (1 - p_combined) * (1/n1 + 1/n2)). If z-score > 1.96 (for 95% confidence), declare significance.
    - For CPA/ROAS: compare means with simple threshold (>20% difference with sufficient sample)
  - Set winner_id, result_summary, confidence levels on each variant
  - Set losing variants to "losing" status
  - Return updated VariantTest

- `promote_winner(self, test: VariantTest) -> Dict[str, Any]`:
  - Generate instructions for promoting the winning variant:
    - Which creative elements to update
    - What the new values should be
    - Which ad to pause (control/losers)
    - Return: `{"action": "promote", "winner_id": str, "updates": dict, "pause_ids": list, "summary": str}`
  - Does NOT execute the promotion — returns the instructions for the action system to execute.

- `suggest_next_test(self, inventory_item: CreativeInventoryItem, past_tests: List[VariantTest]) -> Optional[Dict[str, Any]]`:
  - Given a creative's test history, suggest what to test next.
  - Rule: test one element at a time.
  - Priority order: headline > CTA > description > image > landing_page
  - Skip elements that were tested in the last 30 days.
  - Return: `{"test_element": str, "reason": str, "priority": str}` or None if all elements recently tested.

**Class: CreativeInventory**

Tracks all ad creatives with freshness scoring.

Methods:
- `__init__(self, freshness_threshold: float = 0.3, max_days_without_refresh: int = 30)` — set thresholds
- `add_creative(self, creative: Dict[str, Any]) -> CreativeInventoryItem`:
  - Create a CreativeInventoryItem from a creative dict
  - Set created_at, freshness_score = 1.0, status = "active"

- `update_performance(self, item_id: str, performance: Dict[str, float]) -> CreativeInventoryItem`:
  - Update the performance data for an inventory item
  - Determine performance_trend based on recent data:
    - Compare last 7 days vs previous 7 days
    - If CTR improved >10%: "improving"
    - If CTR declined >10%: "declining"
    - Otherwise: "stable"
  - Return updated item

- `calculate_freshness(self, item: CreativeInventoryItem) -> float`:
  - Freshness formula: `max(0.0, 1.0 - (days_active / max_days_without_refresh) * degradation_factor)`
  - `degradation_factor`: 1.0 for declining performance, 0.7 for stable, 0.4 for improving
  - A creative that's improving degrades much slower than one that's declining
  - Clamp to 0.0-1.0 range
  - Set needs_refresh = True if freshness < freshness_threshold

- `get_stale_creatives(self) -> List[CreativeInventoryItem]`:
  - Return all items where needs_refresh is True or days_active > max_days_without_refresh
  - Sort by freshness_score ascending (most stale first)

- `get_inventory_summary(self, platform: Optional[str] = None) -> Dict[str, Any]`:
  - Return summary: `{"total": int, "active": int, "stale": int, "average_freshness": float, "by_platform": dict, "by_format": dict, "needs_attention": list}`
  - Optionally filter by platform

- `retire_creative(self, item_id: str, reason: str = "Stale") -> CreativeInventoryItem`:
  - Set status to "retired", record reason in metadata

**Helper functions (module-level):**

- `generate_variant_id() -> str` — return `cv_{uuid.uuid4().hex[:12]}`
- `generate_test_id() -> str` — return `vt_{uuid.uuid4().hex[:12]}`
- `generate_inventory_id() -> str` — return `ci_{uuid.uuid4().hex[:12]}`
- `calculate_z_score(p1: float, n1: int, p2: float, n2: int) -> float` — calculate z-score for two-proportion z-test. Handle edge cases (n1=0, n2=0, p1=p2). Formula: `(p1 - p2) / sqrt(p_combined * (1 - p_combined) * (1/n1 + 1/n2))` where `p_combined = (p1*n1 + p2*n2) / (n1 + n2)`
- `is_significant(z_score: float, threshold: float = 0.95) -> bool` — return True if z-score indicates significance at the given threshold (z > 1.96 for 0.95, z > 2.576 for 0.99)
- `calculate_lift(control_rate: float, variant_rate: float) -> float` — return `(variant_rate - control_rate) / control_rate` if control_rate > 0, else 0.0
- `days_since(date_str: str) -> int` — calculate days between date_str and now

**VARIANT_GENERATION_STRATEGIES dict:**

Define strategies for generating variants by test element:
```
VARIANT_GENERATION_STRATEGIES = {
    "headline": {
        "angles": ["question", "number_stat", "fear_pain", "benefit_led", "social_proof"],
        "templates": {
            "question": "What if {benefit}?",
            "number_stat": "{number} {audience} trust {brand} for {service}",
            "fear_pain": "Stop {pain_point} — {solution}",
            "benefit_led": "Get {benefit} in {timeframe}",
            "social_proof": "Join {number}+ {audience} who {outcome}"
        }
    },
    "cta": {
        "options_by_objective": {
            "leads": ["Get Free Quote", "Book Now", "Call Today", "Schedule Service", "Get Estimate"],
            "sales": ["Buy Now", "Shop Now", "Order Today", "Get Started", "Claim Offer"],
            "traffic": ["Learn More", "See Details", "Explore", "Read More", "Discover How"],
            "awareness": ["Learn More", "Watch Now", "See How", "Discover", "Explore"]
        }
    },
    "description": {
        "frameworks": ["benefit_first", "problem_first", "social_proof_first", "urgency_first"],
        "templates": {
            "benefit_first": "{benefit}. {how_it_works}. {cta}.",
            "problem_first": "Tired of {problem}? {solution}. {cta}.",
            "social_proof_first": "{number}+ {audience} chose us. {benefit}. {cta}.",
            "urgency_first": "Limited time: {offer}. {benefit}. {cta}."
        }
    }
}
```

## Output Files

- `kai/paid_media/variants.py`
- `kai/paid_media/__init__.py` (update to include variants exports)

## Acceptance Criteria

- [ ] `VariantStatus` enum has all 7 statuses
- [ ] `VariantTestElement` enum has all 8 test elements
- [ ] `CreativeVariant` model has all 19 fields with correct types and defaults
- [ ] `VariantTest` model has all 16 fields
- [ ] `CreativeInventoryItem` model has all 18 fields including freshness tracking
- [ ] `VariantWorkflow.generate_variants()` produces different variant types for headline/description/cta/image
- [ ] `VariantWorkflow.evaluate_test()` implements z-score statistical significance check
- [ ] `VariantWorkflow.evaluate_test()` handles insufficient sample size (returns "running")
- [ ] `VariantWorkflow.promote_winner()` returns actionable promotion instructions without executing
- [ ] `VariantWorkflow.suggest_next_test()` respects the 30-day cooldown and priority order
- [ ] `CreativeInventory.calculate_freshness()` uses degradation factor based on performance trend
- [ ] `CreativeInventory.get_stale_creatives()` returns items sorted by staleness
- [ ] `calculate_z_score()` handles edge cases (zero sample sizes, equal proportions)
- [ ] `is_significant()` correctly maps confidence threshold to z-score critical value
- [ ] `VARIANT_GENERATION_STRATEGIES` dict has templates for headline, cta, and description
- [ ] All 7 helper functions exist with correct signatures
- [ ] Pydantic import fallback pattern matches `gateway/models.py`
- [ ] No banned words from CLAUDE.md in string constants or templates

## Reference Materials

- `kai/models/paid_media.py` (created by Task 046) — Ad, AdPerformance models for compatibility
- `kai/connectors/ads/base.py` (created by Task 044) — AdCreativeSummary for connector output mapping
- `gateway/models.py` — Pydantic import fallback pattern (lines 1-30)
- `knowledge/playbooks/ad-creative-best-practices.md` — creative testing best practices
- `knowledge/playbooks/ad-campaign-management.md` — campaign optimization guidance
- `CLAUDE.md` — full project context, banned word list
