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

  "current_rank": "position for target keyword, or not ranking",
  "monthly_impressions": 0,
  "current_ctr": 0.0,
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

---

## Brief Validation

Before write agent starts, validate:
- All required fields present and non-empty
- `hook_options` has exactly 3 variants
- `competitor_weakness` is specific (≥20 words), not generic
- `angle` is differentiated from `target_keyword` (not just a restatement)
- `proof_available` references actual data or a named example
