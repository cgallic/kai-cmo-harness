# Kai Harness — Marketing Config

Read this file first. Load nothing else until you know what task you're doing.
Then use the map below to load ONLY what you need.

---

## Non-Negotiables (always active, no exceptions)

- **Voice:** SOUL.md — banned words list is active. Tier 1 = hard block.
- **Four U's:** every piece must score 12+/16 before publishing
- **Algorithmic Authorship:** conditions after main clause, verbs first, sentences <20 words, bold answers not queries
- **No AI slop:** never use "In conclusion", "It's important to note", "In today's rapidly evolving", "leverage", "utilize"

---

## Research Phase (always before writing)

Run FIRST. Do not skip. Do not write until brief is complete.

```bash
# Owned site data (GSC + GA4)
cmo gsc opportunities --site=<site>
cmo gsc queries --site=<site> --limit=20
cmo ga4 pages --site=<site> --days=30

# Competitor + SERP data (DataForSEO)
cmo dataforseo serp --keyword="<target keyword>"
cmo dataforseo competitors --site=<site>
```

Use GSC for gaps in your own rankings. Use DataForSEO to see who ranks for the target keyword and what they're doing. Both inform the brief.

Match persona from `knowledge/personas/`. Pick closest archetype.

Output: structured brief using schema at `harness/brief-schema.md`.
Save brief to `/tmp/harness_brief.json` before proceeding to write.

---

## Framework Map (load by task, not all at once)

| Task | Load these files |
|------|-----------------|
| Blog post | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md` + `knowledge/checklists/content-checklist.md` |
| LinkedIn article | `skills/linkedin-writing/SKILL.md` |
| Email — lifecycle | `knowledge/channels/email-lifecycle.md` + `knowledge/checklists/email-checklist.md` |
| Email — cold outreach | `knowledge/channels/email-lifecycle.md` + `harness/references/cold-email-rules.md` |
| TikTok script | `knowledge/channels/tiktok-algorithm.md` + `memory/tiktok-ai-script-red-flags.md` |
| SEO content | `skills/seo-content/SKILL.md` + `knowledge/frameworks/aeo-ai-search/` + `cmo dataforseo serp` (competitor SERP snapshot) |
| Meta ads (FB/IG) | `knowledge/channels/meta-advertising.md` + `knowledge/frameworks/meta-advertising/` + `knowledge/checklists/meta-ads-checklist.md` |
| Google ads | `knowledge/channels/paid-acquisition.md` + `harness/references/google-ads-rules.md` |
| Press release | `knowledge/channels/press-releases.md` + `knowledge/checklists/pr-checklist.md` |
| Paid acquisition strategy | `knowledge/channels/paid-acquisition.md` + `knowledge/playbooks/2026-marketing-playbook.md` |

---

## Skill Contracts

Every format has a contract in `harness/skill-contracts/`:

| Contract | Format | Min Four U's | SEO Lint |
|----------|--------|-------------|---------|
| `blog-post.yaml` | Blog | 12/16 | ✅ required |
| `linkedin-article.yaml` | LinkedIn | 12/16 | ❌ skipped |
| `email-lifecycle.yaml` | Nurture email | 10/16 | ❌ skipped |
| `cold-email.yaml` | Cold outreach (3-touch) | 10/16 | ❌ skipped |
| `meta-ads.yaml` | Facebook + Instagram ads | 10/16 | ❌ skipped |
| `google-ads.yaml` | Google RSA + PMax + Display | 10/16 | ❌ skipped |
| `blog-post.yaml` | SEO content | 12/16 | ✅ required |

---

## Quality Gate (always after writing, always before approval)

All three must pass. Do not self-grade.

```bash
cd /opt/cmo-analytics && source venv/bin/activate
python3 scripts/four_us_score.py --text "<draft>"
python3 scripts/banned_word_check.py --text "<draft>"
python3 scripts/seo_lint.py --text "<draft>" --keyword "<kw>"
```

- Four U's total < 12 → **hard block, rewrite**
- Any single U < 2 → **hard block, rewrite**
- Tier 1 banned word hit → **hard block, rewrite**
- SEO lint errors → **fix before approval**

Max 2 auto-retry cycles. After 2 failures: surface to human with failure report.

---

## Approval Flow

After gate passes:
1. Post draft + score card to Discord (channel by product — see AGENTS.md)
2. Wait for ✅ reaction from Connor
3. On ✅: publish + log
4. On ❌: revise and re-gate

---

## After Publishing (log immediately)

```bash
python3 /opt/cmo-analytics/scripts/content_log.py \
  --url "<url>" \
  --keyword "<kw>" \
  --platform "<platform>" \
  --site "<site>" \
  --format "<format>"
```

30-day performance check fires automatically via cron.

---

## Products + Site Keys

| Product | Site key | Discord channel |
|---------|----------|----------------|
| KaiCalls | kaicalls | #writer (1473311759896019199) |
| BuildWithKai | buildwithkai | #bwk (1469307544454566020) |
| ABP | abp | #awesomebackyard (1469310748290191441) |
| MeetKai / general | meetkai | #meet-kai (1471889734841270332) |
| ConnorGallic.com | connorgallic | #meet-kai |
| VocalScribe | vocalscribe | #vocal-scribe (1469310699158110363) |

---

## Self-Improvement (runs automatically)

- Weekly Monday: `python3 /opt/cmo-analytics/scripts/pattern_extract.py --site all`
- 30-day check: `python3 /opt/cmo-analytics/scripts/performance_check.py --days 30`
- Patterns append to `knowledge/playbooks/what-works.md` automatically
- Harness defaults update when patterns reach statistical significance (n≥5 with consistent delta)
