# Content Brief Schema

Every content task requires a completed brief. No brief = no write.
Save to `/tmp/harness_brief.json` before passing to write agent.

---

## Required Fields

```json
{
  "target_site": "kaicalls | buildwithkai | abp | meetkai | connorgallic | vocalscribe",
  "target_keyword": "primary keyword exactly as it appears in title",
  "secondary_keywords": ["2-3 supporting terms"],
  "format": "blog | linkedin | email | tiktok | ad | press",
  "persona": "archetype name from knowledge/personas/",
  "persona_evidence_status": "evidence_backed | directional | hypothesis",
  "persona_evidence_sources": [
    {
      "source_type": "interview | sales_call | support_ticket | review | survey | analytics | third_party_research | hypothesis",
      "source": "URL, file path, CRM note, or research artifact",
      "retrieved_or_observed_date": "YYYY-MM-DD",
      "confidence": "high | medium | low"
    }
  ],

  "current_rank": "position for target keyword, or not ranking",
  "monthly_impressions": 0,
  "current_ctr": 0.0,
  "data_provenance_mode": "sales_external | onboarding_connected | internal_demo | not_applicable",
  "quantitative_claims": [
    {
      "claim": "exact claim that may appear in output",
      "source": "URL, file path, collector output, or internal measurement",
      "retrieved_or_observed_date": "YYYY-MM-DD",
      "evidence_tier": "official_requirement | official_best_practice | law_regulation_court_status | academic_study | vendor_platform_study | practitioner_benchmark | internal_measurement | inference_hypothesis | missing_data",
      "confidence": "high | medium | low"
    }
  ],
  "data_gaps": ["known missing data that must not be guessed"],
  "competitor_url": "top-ranking URL we're competing against",
  "competitor_weakness": "specific gap in their content — not vague",

  "angle": "specific frame — not AI for law firms, but why law firms lose 40% of leads after 5pm",
  "hook_options": [
    "Hook variant 1",
    "Hook variant 2",
    "Hook variant 3"
  ],
  "audience_pain": "the single biggest frustration of this persona",
  "proof_available": "data, stories, or examples we can use",
  "proof_inventory": [
    {
      "proof_type": "customer_quote | product_data | case_study | demo | review | benchmark | legal_requirement | platform_requirement",
      "source": "URL, file path, collector output, or note",
      "claim_allowed": "what this proof can safely support"
    }
  ],
  "cta": "what we want them to do after reading",

  "ad_concept_bench": {
    "use_when": "required for paid ad batches; omit for non-ad content",
    "personas": ["3-5 situational or psychographic personas"],
    "desires": ["3-5 customer-language desired outcomes"],
    "angles": ["4-8 story, proof, or mechanism frames"],
    "concept_math": "personas x desires x angles = total possible concepts",
    "portfolio_rule": "60% winners, 30% adjacent tests, 10% experiments",
    "selected_concepts": [
      {
        "concept_id": "PDA-persona-desire-angle-01",
        "persona": "who this ad speaks to",
        "desire": "the progress they want",
        "angle": "the story/proof/frame",
        "awareness_stage": "unaware | problem-aware | solution-aware | product-aware | most-aware",
        "format": "video | static | carousel | UGC | founder | demo",
        "hook": "first line or first 3 seconds",
        "portfolio_bucket": "winner | adjacent | experiment",
        "kill_rule": "named threshold before launch"
      }
    ]
  },

  "word_count_target": 1400,
  "publish_date": "YYYY-MM-DD",
  "internal_links": [
    "https://site.com/existing-post-1",
    "https://site.com/existing-post-2"
  ]
}
```

---

## Word Count Targets by Format

| Format | Target |
|--------|--------|
| Blog post | 1200–1800 |
| LinkedIn article | 700–1000 |
| Email | 300–500 |
| TikTok script | 150–300 (spoken words) |
| Meta ad | 50–150 |
| Press release | 400–600 |

---

## Persona Reference

Load the matching file from `knowledge/personas/` before completing the brief.
Available archetypes: check `ls knowledge/personas/` for current list.

Personas must be labeled:

- `evidence_backed`: supported by interviews, sales calls, support tickets, analytics, reviews, or credible research.
- `directional`: supported by partial evidence but still needs validation.
- `hypothesis`: useful for creative exploration only; not enough for client-facing strategy claims.

Do not present a persona pain, budget authority, buying trigger, or objection as fact unless the evidence source is listed.

---

## Outcome Declaration (ECO O1 — required before writing)

A baseline recorded after the piece ships is not a baseline, and a threshold chosen after seeing the result is not a threshold. Capture both here, before the first draft.

```yaml
outcome:
  metric: organic_clicks           # what this piece is supposed to move
  source: google_search_console    # the authoritative system, not a dashboard screenshot
  baseline: 0                      # the pre-state, measured now
  threshold: 120                   # the number that counts as success
  window_days: 30                  # when it gets read
  owner: Connor                    # who reads it
  attribution: observational       # observational | control | holdout | geo_split | switchback
```

This block becomes the `outcome_baseline` evidence entry on the piece's ECO record. Without it the work can reach SHIPPED but never CLOSED.

Floors per format: `harness/eco-floors.yaml` · Doctrine: `docs/system/eco-completion-standard.md`

---

## Brief Validation

Before write agent starts, validate:
- `outcome` block is complete (metric, source, baseline, threshold, window, owner) and recorded before drafting
- All required fields present and non-empty
- `hook_options` has exactly 3 variants
- `competitor_weakness` is specific (≥20 words), not generic
- `angle` is differentiated from `target_keyword` (not just a restatement)
- `proof_available` references actual data or a named example
- `persona_evidence_status` is present and matches the sources
- Every quantitative claim has a source, evidence tier, date, and confidence label
- Missing data is listed in `data_gaps`, not replaced with a benchmark
