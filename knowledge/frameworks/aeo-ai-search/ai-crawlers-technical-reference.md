# AI Crawlers Technical Reference

## Purpose

This reference explains crawler behavior, `robots.txt` controls, `llms.txt`, and provider differences for AI search and retrieval systems. It is source-conscious by design: official platform documentation is separated from proposed conventions and practical inference.

Use this file when auditing AI-search readiness, crawler access, WAF rules, or content controls for Google, Bing, OpenAI, Anthropic, and Perplexity.

## Evidence Labels

| Label | Meaning |
| --- | --- |
| Official | Published by the platform or standards author |
| Proposed convention | Public proposal without universal standards status |
| Operational inference | Practical interpretation from official docs, logs, or tests |
| Vendor claim | Published by a tool vendor or third party |
| Unknown | Not confirmed in official public docs |

Do not mix these labels. For example, `llms.txt` is a proposed convention; OpenAI's crawler tokens are official OpenAI controls.

## Core Distinctions

| Category | What it does | Typical control | Examples |
| --- | --- | --- | --- |
| Traditional search crawler | Crawls and indexes pages for search results | `robots.txt`, meta robots, canonical tags, sitemap, Search Console/Bing Webmaster Tools | `Googlebot`, `bingbot` |
| AI search crawler | Crawls or indexes pages for AI search answers and citations | Provider-specific `robots.txt` token and IP verification | `OAI-SearchBot`, `Claude-SearchBot`, `PerplexityBot` |
| User-triggered fetcher | Fetches a page because a user asked an AI product to access it | May use a user-agent token; `robots.txt` treatment varies by provider | `ChatGPT-User`, `Claude-User`, `Perplexity-User` |
| Model-training crawler | Collects public web content that may train foundation models | Provider-specific `robots.txt` token | `GPTBot`, `ClaudeBot`, `Google-Extended` control token |
| Enterprise or product fetcher | Fetches content for a customer workflow, app, ad review, or enterprise search | Product-specific docs and authentication/WAF rules | `Google-CloudVertexBot`, `OAI-AdsBot` |
| Cooperative agent map | Gives agents a curated map of useful content | `/llms.txt` if the agent chooses to read it | `llms.txt` proposal |

The mistake to avoid: treating all AI traffic as one crawler. Search visibility, user retrieval, model training, ad review, and enterprise fetches have different controls.

## Provider Matrix

### OpenAI

Evidence label: **Official** from OpenAI crawler documentation.

| Token | User agent string or fragment | Purpose | Control note |
| --- | --- | --- | --- |
| `OAI-SearchBot` | `compatible; OAI-SearchBot/1.3; +https://openai.com/searchbot` | Search inclusion for ChatGPT search features | Allow for ChatGPT Search visibility; OpenAI says opted-out sites will not be shown in ChatGPT search answers except limited navigational links |
| `GPTBot` | `compatible; GPTBot/1.3; +https://openai.com/gptbot` | Crawls content that may be used to train OpenAI foundation models | Disallow to signal content should not be used for training |
| `ChatGPT-User` | `compatible; ChatGPT-User/1.0; +https://openai.com/bot` | User-initiated page visits from ChatGPT or Custom GPTs | OpenAI says it is not automatic web crawling and robots.txt rules may not apply because actions are user initiated |
| `OAI-AdsBot` | `compatible; OAI-AdsBot/1.0; +https://openai.com/adsbot` | Visits ad landing pages submitted to ChatGPT ads for safety/relevance review | Not used to train foundation models according to OpenAI |

Operational notes:

- OpenAI states `OAI-SearchBot` and `GPTBot` settings are independent.
- OpenAI publishes IP lists for `OAI-SearchBot`, `GPTBot`, and `ChatGPT-User`.
- OpenAI says search crawler changes may take about 24 hours to reflect.

### Google

Evidence label: **Official** from Google Search Central and Google crawler documentation.

| Token | User agent string or fragment | Purpose | Control note |
| --- | --- | --- | --- |
| `Googlebot` | Googlebot user agents vary by device and Chromium version | Google Search crawling and indexing | Do not block if Google Search, AI Overviews, or AI Mode visibility matters |
| `Google-Extended` | No separate HTTP user-agent string | Control token for whether content Google crawls may be used for future Gemini model training and grounding in Gemini/Vertex contexts | Must be set in `robots.txt`; it does not affect Google Search inclusion or ranking |
| `GoogleOther` | `compatible; GoogleOther` | Generic crawler for various Google product teams and R&D | Blocking may affect unspecified non-Search fetches; evaluate by risk |
| `Google-CloudVertexBot` | `Google-CloudVertexBot` | Crawls requested by site owners for Vertex AI Agents | Does not affect Google Search or other products |

Google generative AI Search notes:

- Google says generative AI features on Search are rooted in core Search ranking and quality systems.
- Google describes AI Search grounding as retrieval from Google's Search index.
- Google says site owners do not need special AI files, AI-only markup, or Markdown versions for Google generative AI Search.
- Operational inference: Google Search eligibility still depends on standard crawlability, indexability, snippets, helpful content, structured data where relevant, and policy compliance.

### Anthropic

Evidence label: **Official** from Anthropic crawler documentation.

| Token | Purpose | Control note |
| --- | --- | --- |
| `ClaudeBot` | Collects web content that could contribute to future model training | Disallow to signal future materials should be excluded from Anthropic model training datasets |
| `Claude-User` | Retrieves content at a Claude user's direction | Disabling can reduce visibility for user-directed web search |
| `Claude-SearchBot` | Navigates the web to improve search result relevance and accuracy | Disabling can reduce Claude search visibility and accuracy |

Operational notes:

- Anthropic says its bots honor standard `robots.txt` directives.
- Anthropic says its bots respect anti-circumvention technologies.
- Anthropic supports the non-standard `Crawl-delay` extension where appropriate.
- Anthropic recommends `robots.txt` controls over IP-only blocking because blocking IPs can prevent the crawler from reading the policy file.

### Perplexity

Evidence label: **Official** from Perplexity crawler documentation.

| Token | User agent string or fragment | Purpose | Control note |
| --- | --- | --- | --- |
| `PerplexityBot` | `compatible; PerplexityBot/1.0; +https://perplexity.ai/perplexitybot` | Surfaces and links websites in Perplexity search results | Perplexity recommends allowing it and permitting published IP ranges for search visibility |
| `Perplexity-User` | `compatible; Perplexity-User/1.0; +https://perplexity.ai/perplexity-user` | Fetches pages in response to user requests | Perplexity says it is not used for foundation-model training and generally ignores robots.txt because the fetch is user requested |

Operational notes:

- Perplexity says each crawler setting works independently.
- Perplexity says changes may take up to 24 hours.
- Perplexity publishes IP range JSON endpoints and recommends combining user-agent matching with IP verification in WAF rules.
- Perplexity's own docs publish an `llms.txt` documentation index, which is evidence of adoption by that docs stack, not proof of universal support.

### Microsoft Bing / Copilot

Evidence label: **Official** for Bing crawler strings and Bing AI-powered preview controls; **Operational inference** for Copilot dependence on Bing indexing where no separate public Copilot crawler token is documented here.

| Token | User agent string or fragment | Purpose | Control note |
| --- | --- | --- | --- |
| `bingbot` | `compatible; bingbot/2.0; +http://www.bing.com/bingbot.htm` with evergreen Chromium/Edge versions | Bing Search crawling and rendering | Keep accessible if Bing Search or Copilot visibility matters |

Operational notes:

- Bing moved bingbot to evergreen user-agent strings with current rendering versions.
- Bing supports standard robots controls and Bing Webmaster Tools testing.
- Bing says `data-nosnippet` can keep selected page sections out of Bing Search snippets and AI-generated answers while leaving the content discoverable and available for ranking.
- Operational inference: because Bing positions these controls across Bing Search and Copilot experiences, Bing crawl/index access is the primary public control surface for Bing/Copilot visibility unless Microsoft publishes a separate AI crawler token.

## llms.txt

Evidence label: **Proposed convention** from Jeremy Howard's `llms.txt` proposal.

`llms.txt` is a proposed Markdown file at `/llms.txt` that gives LLMs and agents a concise map of important site resources at inference time.

It is not:

- A replacement for `robots.txt`
- A replacement for `sitemap.xml`
- A universal AI crawler standard
- A Google Search or Google AI Overview requirement
- A permission system for model training

It can be useful for:

- Developer documentation
- API references
- Product docs
- Support libraries
- Internal assistants
- AI browsers or agents that choose to read it
- Public source maps for important canonical pages

### Proposed Format

According to the proposal, a conforming file uses Markdown in this order:

1. H1 with the project or site name. This is the only required section.
2. Blockquote summary with key information about the site.
3. Optional paragraphs or lists, but no headings, with extra context.
4. Optional H2 sections containing file lists.
5. File lists use Markdown links with optional descriptions.
6. A section named `## Optional` marks resources that can be skipped when shorter context is needed.

Example:

```markdown
# Example Product
> Example Product helps service businesses route phone leads and qualify callers.

Important notes:
- Public docs are canonical at https://example.com/docs/
- Pricing changes should be checked on the pricing page.

## Documentation
- [Overview](https://example.com/docs/overview.md): Product concepts and setup flow
- [API Reference](https://example.com/docs/api.md): Endpoint and authentication details

## Optional
- [Changelog](https://example.com/changelog.md): Release history
```

### Kai Default

Publish `llms.txt` when it helps agents find clean, canonical, high-value content. Do not score it as a P0 blocker for Google Search visibility. Score it as an agent ergonomics improvement.

## Robots.txt Strategy

Evidence label: **Operational inference** built from official provider controls.

The safest default is not "allow all" or "block all." Decide separately for:

- Search visibility
- User-triggered retrieval
- Model training
- Ad review or enterprise fetches
- Server load and WAF trust

### Example: Allow Search, Decide Separately on Training

This is a template, not a universal recommendation. Legal, client, and content-risk review may change it.

```robots.txt
User-agent: *
Allow: /

# OpenAI search visibility
User-agent: OAI-SearchBot
Allow: /

# Optional: OpenAI model-training opt-out
User-agent: GPTBot
Disallow: /

# Anthropic search and user-directed retrieval
User-agent: Claude-SearchBot
Allow: /
User-agent: Claude-User
Allow: /

# Optional: Anthropic model-training opt-out
User-agent: ClaudeBot
Disallow: /

# Perplexity search and user fetches
User-agent: PerplexityBot
Allow: /
User-agent: Perplexity-User
Allow: /

# Google Search and AI Search features depend on Google Search indexing
User-agent: Googlebot
Allow: /

# Optional: Google Gemini/Vertex training and grounding control token.
# This is not a separate HTTP user agent and does not affect Google Search ranking.
User-agent: Google-Extended
Disallow: /

# Bing Search and Copilot-related visibility
User-agent: bingbot
Allow: /
```

### Important Caveats

- `robots.txt` can prevent crawling, but it does not always remove already indexed URLs.
- User-triggered fetchers may treat robots differently by provider.
- WAF rules can silently block allowed bots.
- User-agent strings can be spoofed. Verify with official IP lists or DNS guidance where available.
- Search engines cache robots rules. Changes may not apply instantly.
- Separate subdomains need their own `robots.txt` files.

## WAF and Log Verification

Use server logs and WAF logs to confirm actual behavior.

Minimum checks:

- Confirm relevant bots receive 200 responses for `robots.txt`.
- Confirm important canonical URLs are not returning 403, 401, 429, 5xx, or JS-only empty shells.
- Verify IP ranges for OpenAI and Perplexity using their published JSON endpoints.
- Verify Googlebot and bingbot with official verification methods, not user-agent strings alone.
- Check whether edge rules block headless browsers, data center IPs, or uncommon user agents.
- Separate production rate limiting from crawler policy.
- Track last seen date, response code, path, user agent, and verification method.

## Source Control Matrix

| Goal | Primary controls | Notes |
| --- | --- | --- |
| Appear in Google AI Search features | Google Search crawl/index eligibility, snippets, content quality | `llms.txt` is not required by Google |
| Appear in ChatGPT Search | Allow `OAI-SearchBot`; verify IP/WAF access | `GPTBot` is training-related, not search inclusion |
| Support ChatGPT user actions | Avoid blocking `ChatGPT-User` at WAF when appropriate | OpenAI says robots may not apply |
| Appear in Claude search | Allow `Claude-SearchBot` | Separate from `ClaudeBot` |
| Support Claude user retrieval | Allow `Claude-User` where appropriate | Separate from training |
| Appear in Perplexity results | Allow `PerplexityBot`; allow published IPs | Separate from `Perplexity-User` |
| Support Perplexity user fetches | Avoid WAF blocking `Perplexity-User` where appropriate | Perplexity says it generally ignores robots |
| Appear in Bing/Copilot experiences | Allow `bingbot`; maintain Bing indexability | Use Bing Webmaster Tools and preview controls |
| Opt out of selected model training | Disallow provider training/control tokens | This may not affect already collected data |
| Help cooperative agents navigate docs | Publish `/llms.txt` and Markdown mirrors where useful | Proposed convention, not access control |

## Audit Checklist

- [ ] Identify the business goal: search visibility, training opt-out, retrieval access, load control, or all of these.
- [ ] Review `robots.txt` for each subdomain.
- [ ] Confirm Googlebot and bingbot are not blocked when Search visibility matters.
- [ ] Confirm `OAI-SearchBot`, `Claude-SearchBot`, and `PerplexityBot` rules match the desired AI-search posture.
- [ ] Treat `GPTBot`, `ClaudeBot`, and `Google-Extended` as separate model-training or control decisions.
- [ ] Review user-triggered fetchers separately: `ChatGPT-User`, `Claude-User`, `Perplexity-User`.
- [ ] Check WAF, CDN, bot protection, and rate limits.
- [ ] Verify official bot IPs or DNS where available.
- [ ] Confirm canonical pages render useful HTML without requiring user interaction.
- [ ] Check sitemap, canonical tags, structured data, snippets, and `data-nosnippet` where relevant.
- [ ] Publish `llms.txt` only when it points to accurate, canonical resources.
- [ ] Record evidence labels and data gaps in the audit.

## Primary Sources

- OpenAI crawlers: https://developers.openai.com/api/docs/bots
- Google generative AI Search guidance: https://developers.google.com/search/docs/fundamentals/ai-optimization-guide
- Google common crawlers and `Google-Extended`: https://developers.google.com/crawling/docs/crawlers-fetchers/google-common-crawlers
- Anthropic crawler controls: https://support.claude.com/en/articles/8896518-does-anthropic-crawl-data-from-the-web-and-how-can-site-owners-block-the-crawler
- Perplexity crawlers: https://docs.perplexity.ai/docs/resources/perplexity-crawlers
- Bing evergreen bingbot user agents: https://blogs.bing.com/webmaster/april-2022/Announcing-user-agent-change-for-Bing-crawler-bingbot/
- Bing `data-nosnippet` for search and AI-generated answers: https://blogs.bing.com/webmaster/October-2025/Bing-Introduces-Support-for-the-data-nosnippet-HTML-Attribute
- `llms.txt` proposal: https://llmstxt.org/
