# Research QA

## Provenance

- Source ledger exists: yes.
- Official docs back platform/API/policy/legal/search claims: yes for all covered platforms except Grok/xAI crawler behavior.
- Retrieved date recorded: yes, 2026-06-17.
- Evidence tier recorded: yes.
- Quantitative client-facing metrics: none invented.
- Quantitative claims requiring collector output: none shipped in this research packet.

## Copyright and Transcript Safety

- No private, paywalled, login-gated, deleted, or restricted transcript/content was scraped.
- No transcript text was copied into this packet.
- New transcript rules block full transcript storage and long excerpts by default.
- Knowledge Cloner now disables unofficial transcript/subtitle/audio fallback unless `KAI_TRANSCRIPT_UNOFFICIAL_OK=1` is explicitly set for an owned/authorized workflow.
- Podcast/video contracts now require rights status, allowed source status, timestamps, and no long excerpts.

## Policy Coverage

- Paid ads covered: Google, Meta, TikTok, LinkedIn, Microsoft/Bing, Pinterest, Snapchat, Amazon, X, OpenAI Ads measurement.
- Organic social covered: X, LinkedIn, Instagram, Facebook, Threads, TikTok, YouTube, Reddit, Pinterest, Snapchat, Bluesky, Mastodon/Fediverse.
- Search/AEO covered: Google Search AI features, Bing/Copilot webmaster/API surface, ChatGPT/OpenAI crawlers, Claude/Anthropic crawlers, Perplexity crawlers.
- Search/AEO gap: Grok/xAI crawler docs not found as official public docs.
- Content/video covered: YouTube transcript/caption rules, podcast/video repurpose contracts, webinar/transcript playbook routing.
- Automation/TOS covered: social automation, X automation/API, Meta developer policies, TikTok posting/API, YouTube API, LinkedIn prohibited software/API, Pinterest developer rules, Reddit developer/public content policies, Bluesky/Mastodon API limits.

## Remaining Data Gaps

| Gap | Blocking? | Needed Access |
|---|---|---|
| Official Grok/xAI crawler or robots.txt docs | Blocks factual Grok crawler claims | Official xAI/X docs or direct support confirmation |
| Full OpenAI Ads creative/ad policy reference beyond current Ads docs | Blocks auto-approval of OpenAI ad creative | Ads Manager policy docs or official help/policy page |
| Endpoint-by-endpoint Snapchat API rate limits | Blocks high-volume automation planning | Snap developer console/API docs or partner account |
| Microsoft Ads full rate-limit crosswalk by service | Blocks exact pull scheduler math | Microsoft Advertising account/API docs by service |
| Gate engine enforcement of `require_policy_ref` metadata | Does not block docs, but weakens executable enforcement | Code patch and golden tests |
| Transcript provenance lint | Does not block docs, but weakens executable transcript safety | New linter and fixture corpus |

## QA Verdict

Pass for research packet and routing patches. Human/API access is still needed before claiming Grok crawler behavior, shipping OpenAI Ads creative without human review, or sizing high-volume API jobs for Snapchat/Microsoft beyond public docs.

