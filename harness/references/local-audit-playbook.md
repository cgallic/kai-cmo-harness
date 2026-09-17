# Local Audit Playbook — located data, direct checks, and the three deliverables

> **Use when:** auditing a third-party local business (café, roaster, shop, restaurant, hotel, clinic, home service) for a prospect or new client, especially from a Google Maps / `share.google` / website link. Loaded by `/kai-local-audit`. Provenance rules still come from `harness/references/audit-data-provenance.md`.

## Quick Reference

- **Measure from where the customer stands.** Rankings, map packs and AI answers change by town, device and language. Pull them with coordinates, mobile, in every language the market searches in. A desktop browser check from another country is not evidence.
- **The two most common false findings** in the reference run came from eyeballing: a browser-observed rank of #4–5 that the located SERP API put outside the top 30, and a local Lighthouse score of 39 that DataForSEO's Lighthouse scored 88. Publish only API-pulled or directly observed numbers.
- **Test the site the way phones reach it.** Real user agents (old iPhones, Instagram/Facebook in-app browsers, Samsung Internet) can get HTTP 406 from "modern browsers only" framework defaults while Googlebot and link previews get 200.
- **Price offers on measured costs.** Take live shipping quotes before designing bundles; the efficient unit often falls out of the carrier's box tiers.
- **Every finding becomes three things:** a priced offer (if it's a revenue lever), an exact change (file / setting / DNS record / copy block), and a dated week in the plan with a "done when".
- **Rankings move day to day.** Re-pulling one keyword the next morning moved the business from outside the top 30 to #17. Date every ranking claim and prefer counts across many located observations over single positions.

---

## 1. Identify the business before planning

Resolve the link and read the business's own site. Restate the business model in one sentence before choosing modules — the reference request said "cafe/restaurant", the business was a micro-roaster with no storefront selling wholesale, via a local order form and via Shopify. That changes the audit from menu/reservations/dine-in reviews to catalog/ordering/partner venues. List every sales channel and every contact point; phone and email are often only on Facebook.

## 2. Located data (DataForSEO)

Collector: `python -m scripts.local_audit.pulls <command> --config <cfg.json> --out workspace/local-audit/<slug>`. Config template: `examples/local-audit-config.example.json`. Credentials: `DATAFORSEO_LOGIN` / `DATAFORSEO_PASSWORD`. Responses are cached per request in `<out>/raw/`, so re-runs are free and the cache is the evidence archive. A full run (two markets, crawl, reviews, AI) cost about $8 in September 2026.

| Command | Endpoint(s) | What it answers | Gotchas |
|---|---|---|---|
| `volumes` | `keywords_data/google_ads/search_volume/live` | Monthly volume and 12-month seasonality in the home market and the buyer market (tourists, diaspora, online) | Google groups close variants under one number — never sum variants. Small numbers are bucketed (10, 20, 30…). |
| `discover` | `keywords_for_keywords/live`, `keywords_for_site/live` | The local keyword universe | ~15k noisy ideas; bucket by intent regex, dedupe equal-volume variants, drop hotels/chains. |
| `serp` | `serp/google/organic/live/advanced`, `location_coordinate "lat,lng,5000"`, mobile, depth 30 | Brand position per keyword per town, local-pack owners, People Also Ask, paid ads | Share of estimated clicks = volume × positional CTR (28/15/11/8/7/5/4/3/3/2.5%) — label it modeled. PAA questions are a ready FAQ plan. Zero paid ads = uncontested Google Ads. |
| `maps` | `serp/google/maps/live/advanced`, `"lat,lng,14z"` | Map visibility across 7–10 nearby towns | Record #1 per cell and whether the relevant Google category (e.g. Coffee roasters) appears at all — an empty category slot is the opportunity. |
| `listings` | `business_data/business_listings/search/live`, `categories_aggregation/live` | Does the business have a Google listing? Market size by category, prospect list with `https://maps.google.com/?cid=<cid>` | The `like` title filter is case-sensitive — search several casings. More than ~8 categories in one request returns `40501 Invalid Field: 'categories'`; take valid ids from `categories_aggregation`. `brand_pattern` must match only this business (a loose pattern matched monuments and bars sharing the name). |
| `reviews` / `reviews --collect` | `business_data/google/reviews/task_post` → `task_get` | Customer proof at partner venues, complaints at competitors, owner reply rates | Async. Partner reviews that name the audited brand are the strongest proof in the report; competitor complaints ("expensive and not specialty") are ready-made wholesale pitches. |
| `backlinks` | `backlinks/summary`, `referring_domains` | Real vs spam referring domains; local press targets | Separate editorial links by eye. For press targets, pull referring domains of 10–15 category leaders and filter to local, travel and trade media (`media_pattern`). Also fetch partner sites and search for the brand name. |
| `ai` | `ai_optimization/{chat_gpt,perplexity,gemini,claude}/llm_responses/live`, `web_search: true` | Which businesses assistants name for the market's real questions | List models first (`.../llm_responses/models`). Run prompts in every market language — the reference business was named in 12/24 English answers and 4/24 Spanish ones. **Verify every business the assistants recommend**: the top "Rincon wholesale roaster" in two assistants was a California company with the town's name in its brand. |
| `lighthouse` | `on_page/lighthouse/live/json` | Cited speed/accessibility/SEO scores and failing audits | Prefer this to PageSpeed Insights (quota) and to local Lighthouse runs (unstable). Report failing audit items, not only scores. |
| `crawl` / `crawl --collect` | `on_page/task_post` → `summary`, `pages`, `resources`, `links` | Indexable pages, duplicate titles, missing descriptions/H1/alt, heavy resources, broken links | Mobile preset with JS rendering. A one-page site plus an order form crawls as 2 pages — that is the finding. |

Labs datasets (`dataforseo_labs/*`) cover few countries; for small markets use them only for the US buyer market and label the database.

## 3. Direct checks

`python -m scripts.local_audit.checks all --config <cfg.json> --out <audit-dir>` runs:

- **access** — HTTP status for 17 real user agents. Frameworks shipping a "modern browsers only" default (Rails 8 `allow_browser versions: :modern`) answer iOS ≤17.1, iPadOS 16, macOS Safari 16, Chrome ≤119, Samsung Internet 23 and in-app browsers on iOS 16 with 406. Fix is usually one line.
- **assets** — sizes of every referenced asset (HEAD) and frame/duration parse of large WebP files. A 31 MB "image" was an 87-frame, 7-second phone video saved as animated WebP.
- **dns** — MX, SPF, DKIM (common selectors), DMARC via DNS-over-HTTPS. Missing SPF/DKIM on the address that answers order requests is a sales problem.
- **shopify** — `products.json` (empty descriptions, placeholder vendor "My Store", variant availability) and policy URL status.

Browser work (use a real browser session; read-only on any logged-in social account):

- **Mobile screenshots** at 390×844 with a current iOS user agent; probe `document.documentElement.scrollWidth > clientWidth` and list elements whose right edge exceeds the viewport. Compress screenshots to WebP ≤ 45 KB for the report.
- **Shopify shipping quotes** from a throwaway cart, then empty it and confirm `item_count` 0:

  ```js
  await fetch('/cart/clear.js', {method: 'POST'});
  await fetch('/cart/add.js', {method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({items: [{id: VARIANT_ID, quantity: 2}]})});
  const q = 'shipping_address[country]=US&shipping_address[province]=PR&shipping_address[zip]=00677';
  await fetch('/cart/prepare_shipping_rates.json?' + q, {method: 'POST'});
  // poll GET /cart/async_shipping_rates.json?<q> until 200 with a non-null body, then POST /cart/clear.js
  ```

  Quote 1, 2, 3–6 units, each add-on, local ZIPs and a far ZIP. The reference store charged the same for one or two bags and jumped a tier when a $5 sticker pack was added.
- **Instagram** — profile `og:description` gives followers and posts; post dates decode from shortcodes (`scripts.local_audit.analysis.instagram_post_date`); per-post likes come from each post's `og:description`. Pull partner accounts too: borrowed reach often exceeds the client's own by 100×.
- **Facebook About** for phone/email; **Meta Ad Library** exact-phrase search for any ads ever; **Yelp / TripAdvisor** presence; the brand-name knowledge panel (name collisions with unrelated businesses are common).
- **Competitor claims** — fetch rivals' own pages before repeating a positioning claim ("first and only roaster" vs a rival site saying it roasts in-house; a brand named after the town but produced elsewhere).

## 3b. Connected analytics, when the owner shares a token

`python -m scripts.local_audit.matomo --config <cfg.json> --out <audit-dir>` reads a Matomo instance (config block `matomo`, token from the env var named in `token_env`) and, crucially, **splits the dashboard number into real visits, storefront-pixel traffic recorded under sandbox URLs, automation, developer machines and other hosts**. In the reference run the dashboard showed 139 visits for 30 days; 72 were real people, 44 were the Shopify pixel writing `/web-pixels@…/sandbox/modern/...` paths, 11 were bots and audits, 9 were `http://127.0.0.1:<port>/` test runs, and 4 came from a staging host and the origin server's bare IP. Report the cleaned number and name the noise; a client comparing months on the raw dashboard is comparing test runs.

Analytics also answers questions the rest of the audit cannot: which sources actually deliver (AI assistants already appear as referrers), how many people reach the store, and whether conversions are measured at all (no goals configured means no conversion exists to report). It cannot measure people the site turns away — a browser blocked at the door never loads the tracker — so it never disproves the access test. Metrics from it are `connected` tier, so the audit mode for that section is `onboarding_connected` even when the rest stays `sales_external`.

Unexpected hosts in the analytics are a finding in themselves: the reference run surfaced the origin server answering on its bare IP over plain HTTP, serving the whole site and its order form outside the CDN, with no `noindex`.

## 4. Deliverables

One owner-facing page (and, where the market is bilingual, a translated sibling). Order:

1. **Start here · this week** — 3–5 actions with the exact URL, number, setting or line of code.
2. **Headline findings** ordered by revenue impact, then a 0–5 scorecard.
3. **Evidence sections** — demand, located rankings, map grid, listings/category gap, backlinks and press targets, AI assistants, website deep dive (access, weight, mobile walkthrough with screenshots, crawl table, copy review table, forms, email DNS), store (shipping quotes, catalog issues), reviews, social reach, pricing and landed cost per unit, competitors, wholesale market with a prospect table.
4. **Offers** — build with `/kai-offer-builder` doctrine: entry, core, signature (wholesale/B2B), flagship subscription, seasonal offers placed on the seasonality pull, education/add-ons. Every price is a proposal to check against costs; never publish margins that weren't provided.
5. **Changes** — grouped by owner: code (file + exact edit), copy (both languages), commerce admin (menu path → field → value), Google Business Profile fields and description, DNS records, social bio/pins and partner-ask messages.
6. **12-week plan** — starts the next Monday; owner and developer columns; "done when" per week; retail peaks and tourist seasons placed from the seasonality data; a targets table (today → target) that names the same pulls and a dated re-run.
7. **Phone and follow-up** — apply the KaiCalls Fit Rule; say plainly when it is not the first fix.

## 5. Localized rerun

When the user asks to rerun "for local <market>": switch `location_code` to the market, re-run `discover`, then `serp` with 40–50 intent-bucketed keywords × 3–6 towns in the local language(s), `maps` in the local language across ~10 towns, `ai` with local-language prompts and `country_iso`, and `backlinks` press targets from local category leaders. Add a section after the headlines with share of clicks by intent, the map grid, the AI table, press targets and PAA questions, then patch the plan rows and targets it changes.

## 6. Bilingual version

Split the finished HTML at section comment markers into chunks of ≤ 25 KB with the CSS removed. Translate chunks in parallel with one shared brief: preserve every tag, attribute and element order; translate only visible text plus `alt`, `title`, `aria-label` and meta description; never translate code, URLs, brand names or search queries shown as data; keep numbers; translate month names and chart initials; keep deliverable copy that is already labeled for the other language; use a regional glossary. Reassemble and compare tag signatures (ignoring `alt`/`title`/`aria-label`/`content`) — the only difference should be `lang`. Publish at `<page>/es/` (or the language code) with image paths adjusted and a language toggle on both pages.

## 7. Verify before handoff

- `python scripts/quality_gates/audit_provenance_lint.py workspace/local-audit/<slug> --audit-dir`
- `python scripts/quality_gates/banned_word_check.py <report>`
- Rendered page at 390 px and 1280 px: no horizontal overflow outside table wrappers, every image loaded (scroll slowly — lazy images report false negatives), no duplicate ids, no dead in-page anchors.
- Private pages carry `noindex,nofollow,noarchive`.
