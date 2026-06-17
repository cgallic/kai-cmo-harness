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
| LinkedIn organic post | `knowledge/channels/linkedin-organic.md` |
| Twitter/X post | `knowledge/channels/twitter-x.md` |
| Instagram content | `knowledge/channels/instagram.md` |
| Email — lifecycle | `knowledge/channels/email-lifecycle.md` + `knowledge/checklists/email-checklist.md` |
| Email — cold outreach | `knowledge/channels/email-lifecycle.md` + `harness/references/cold-email-rules.md` |
| TikTok script | `knowledge/channels/tiktok-algorithm.md` + `memory/tiktok-ai-script-red-flags.md` |
| SEO content | `skills/seo-content/SKILL.md` + `knowledge/frameworks/aeo-ai-search/` + `cmo dataforseo serp` (competitor SERP snapshot) |
| Meta ads (FB/IG) | `knowledge/channels/meta-advertising.md` + `knowledge/frameworks/meta-advertising/` + `knowledge/checklists/meta-ads-checklist.md` |
| Google ads | `knowledge/channels/paid-acquisition.md` + `harness/references/google-ads-rules.md` + `knowledge/frameworks/google-ads/` |
| Google ads (deep) | `knowledge/frameworks/google-ads/google-ads-auction-deep-dive.md` + `google-ads-pmax-deep-dive.md` + `google-ads-rsa-deep-dive.md` |
| Press release | `knowledge/channels/press-releases.md` + `knowledge/checklists/pr-checklist.md` |
| Landing page / CRO | `knowledge/frameworks/cro-landing-pages.md` + `knowledge/frameworks/content-copywriting/perception-engineering.md` |
| Paid acquisition strategy | `knowledge/channels/paid-acquisition.md` + `knowledge/playbooks/2026-marketing-playbook.md` |
| Competitor analysis | `knowledge/playbooks/competitive-intelligence.md` + `knowledge/frameworks/competitor-content-analysis.md` |
| Campaign planning | `knowledge/playbooks/campaign-orchestration.md` + `knowledge/frameworks/cro-landing-pages.md` |

---

## Skill Contracts

Every format has a contract in `harness/skill-contracts/`:

| Contract | Format | Min Four U's | SEO Lint |
|----------|--------|-------------|---------|
| `blog-post.yaml` | Blog | 12/16 | ✅ required |
| `linkedin-article.yaml` | LinkedIn | 12/16 | ❌ skipped |
| `social-post.yaml` | LinkedIn/Twitter/IG posts | 10/16 | ❌ skipped |
| `email-lifecycle.yaml` | Nurture email | 10/16 | ❌ skipped |
| `cold-email.yaml` | Cold outreach (3-touch) | 10/16 | ❌ skipped |
| `meta-ads.yaml` | Facebook + Instagram ads | 10/16 | ❌ skipped |
| `google-ads.yaml` | Google RSA + PMax + Display | 10/16 | ❌ skipped |
| `landing-page.yaml` | Landing/sales pages | 12/16 | ✅ required |
| `campaign.yaml` | Multi-channel campaigns | 12/16 | per asset |
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

## Publishing (content goes live, not just to /tmp/)

After approval, publish directly to CMS or social:

```bash
# CMS publishing (via harness CLI)
kai-harness run --task blog --site kaicalls --keyword "..." --publish wordpress
kai-harness run --task blog --site kaicalls --keyword "..." --publish ghost
kai-harness run --task blog --site kaicalls --keyword "..." --publish markdown

# Standalone publishing
python3 scripts/publish/wordpress.py --draft /tmp/harness_draft.md --status draft
python3 scripts/publish/ghost.py --draft /tmp/harness_draft.md --status draft
python3 scripts/publish/webflow.py --draft /tmp/harness_draft.md --status draft
python3 scripts/publish/markdown_to_site.py --draft /tmp/harness_draft.md --output-dir ./content/blog/ --generator hugo
```

### Social Posting

```bash
python3 scripts/social/linkedin.py --content "Your post text"
python3 scripts/social/twitter.py --content "Your tweet"
python3 scripts/social/buffer.py --content "Scheduled post" --platforms linkedin twitter
```

Credentials in `.env`: `WP_URL`, `WP_USERNAME`, `WP_APP_PASSWORD`, `GHOST_URL`, `GHOST_ADMIN_KEY`, `LINKEDIN_ACCESS_TOKEN`, `TWITTER_API_KEY`, etc.

---

## Competitive Intelligence

Run regularly. intel data feeds into briefs and market briefs.

```bash
# Monitor competitors (RSS + sitemap diffing)
kai-harness intel --check

# Show new competitor pages since last scan
kai-harness intel --diff

# Content gap analysis (they rank, you don't)
kai-harness intel --gaps --site kaicalls

# AI-synthesized weekly market brief
kai-harness intel --brief

# SERP tracking (daily keyword positions)
python3 scripts/intel/serp_tracker.py --track
python3 scripts/intel/serp_tracker.py --alerts
```

Competitors configured in `config.yaml` under `competitors:`.

---

## Campaign Management

For coordinated multi-channel campaigns (not individual content pieces):

```bash
# Generate all campaign assets
kai-harness campaign --goal "product launch" --product kaicalls --keyword "ai receptionist" --type launch --save campaigns/q1/

# Track campaign performance
python3 scripts/campaigns/campaign_tracker.py --create "Q1 Launch" --dir campaigns/q1/
python3 scripts/campaigns/campaign_tracker.py --update "Q1 Launch" --channel email --metric opens --value 2450
python3 scripts/campaigns/campaign_tracker.py --report "Q1 Launch"
```

Campaign types: launch, promotion, webinar, seasonal, awareness.
Assets generated: landing page, 5-email sequence, social variants, ad variants, content calendar.

---

## Reporting

```bash
# Weekly marketing report (traffic, SEO, content, competitive, recommendations)
kai-harness weekly-report --save reports/weekly.md

# CEO deck (5 slides, Marp-compatible)
python3 scripts/reporting/ceo_deck.py --save reports/deck.md

# HTML dashboard (open in browser, no server needed)
kai-harness dashboard
```

---

## Google Ads (API integration)

```bash
# Campaign performance
python3 scripts/ads/google_ads.py campaigns
python3 scripts/ads/google_ads.py keywords --campaign 123
python3 scripts/ads/google_ads.py search-terms --campaign 123
python3 scripts/ads/google_ads.py summary

# AI-powered optimization
python3 scripts/ads/google_ads_optimize.py --analyze       # Full analysis
python3 scripts/ads/google_ads_optimize.py --negatives      # Negative keyword suggestions
python3 scripts/ads/google_ads_optimize.py --budget          # Budget reallocation
python3 scripts/ads/google_ads_optimize.py --opportunities   # New keyword opportunities
```

Credentials in `.env`: `GOOGLE_ADS_DEVELOPER_TOKEN`, `GOOGLE_ADS_CLIENT_ID`, `GOOGLE_ADS_CLIENT_SECRET`, `GOOGLE_ADS_REFRESH_TOKEN`, `GOOGLE_ADS_CUSTOMER_ID`.

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

## Knowledge Cloner (expert knowledge extraction pipeline)

Extract expert knowledge from YouTube channels, podcasts, articles, and GitHub repos into structured, actionable knowledge bases.

```bash
# Initialize an expert
python -m scripts.knowledge_cloner init "Expert Name" --domain "Marketing"

# Discover sources
python -m scripts.knowledge_cloner discover expert-name --youtube https://www.youtube.com/@Channel/videos --limit 20

# Run full pipeline (discover → transcribe → extract → distill → synthesize → operationalize → quality)
python -m scripts.knowledge_cloner pipeline expert-name --max-cost 10.00

# Individual phases
python -m scripts.knowledge_cloner transcribe expert-name
python -m scripts.knowledge_cloner extract expert-name
python -m scripts.knowledge_cloner distill expert-name
python -m scripts.knowledge_cloner synthesize expert-name
python -m scripts.knowledge_cloner operationalize expert-name
python -m scripts.knowledge_cloner quality expert-name

# Check progress and costs
python -m scripts.knowledge_cloner status expert-name
python -m scripts.knowledge_cloner cost expert-name
```

**Output**: 5 distilled docs (frameworks, tactics, edges, principles, anti-patterns) + 4 operational outputs (quick reference, decision trees, checklists, AI prompts) + quality report.

**Cost**: ~$3.50 for 40 sources via OpenRouter (qwen-plus/qwen-max).

See `scripts/knowledge_cloner/README.md` for full documentation.

---

## Self-Improvement (runs automatically)

- Weekly Monday: `python3 /opt/cmo-analytics/scripts/pattern_extract.py --site all`
- 30-day check: `python3 /opt/cmo-analytics/scripts/performance_check.py --days 30`
- Patterns append to `knowledge/playbooks/what-works.md` automatically
- Harness defaults update when patterns reach statistical significance (n≥5 with consistent delta)
