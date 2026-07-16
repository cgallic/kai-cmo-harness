# Darren Shaw: Knowledge Distillation

**Created:** July 2026
**Sources:** Whitespark blog and Local Search Ranking Factors reports (2021-2026), Near Media podcast interviews (2026), third-party LSRF summaries, Whitespark founder bio, X/Twitter commentary

---

## Table of Contents

1. [Background](#background)
2. [Core Philosophy & Mental Models](#core-philosophy--mental-models)
3. [The Local Search Ranking Factors Survey](#the-local-search-ranking-factors-survey)
4. [Proximity, Relevance, Prominence: How the Weights Moved](#proximity-relevance-prominence-how-the-weights-moved)
5. [Citation Strategy Evolution: What Stopped Mattering (and What Came Back)](#citation-strategy-evolution-what-stopped-mattering-and-what-came-back)
6. [The GBP Optimization Tier List](#the-gbp-optimization-tier-list)
7. [Review Velocity & Recency Framework](#review-velocity--recency-framework)
8. [AI Search Visibility & Brand Reverence](#ai-search-visibility--brand-reverence)
9. [Tactical Playbooks](#tactical-playbooks)
10. [Notable Quotes](#notable-quotes)
11. [Anti-Patterns / What He Argues Against](#anti-patterns--what-he-argues-against)
12. [How This Maps Into Kai](#how-this-maps-into-kai)
13. [Sources](#sources)

---

## Background

Darren Shaw started building websites in 1996 during his first year at the University of Alberta — by his own account, failing courses because he was in the computer lab writing HTML instead of attending class. He founded **Whitespark** in Edmonton in 2005 as a web design and development shop, then pivoted the company entirely to local search in 2010, launching its first SaaS product, the **Local Citation Finder**, the same year. Whitespark now serves over 100,000 businesses and agencies with citation building, review management, rank tracking, and GBP management tools (per Whitespark's founder bio page).

His signature contribution is the **Local Search Ranking Factors (LSRF) survey** — originally created by David Mihm in 2008, taken over by Shaw in 2017. It is the industry's longest-running aggregation of expert opinion on what actually moves Google local rankings. He has presented local SEO research at MozCon, LocalU, SearchLove, and dozens of podcasts for over 14 years.

What makes Shaw distinct from most local SEO commentators: he runs the survey (aggregate expert opinion), runs software on tens of thousands of listings (observational data), and repeatedly changes his public position when the evidence changes — most visibly on citations, which his own company sells.

---

## Core Philosophy & Mental Models

### 1. Aggregate expert opinion beats any single guru
"No one knows exactly how Google's algorithm works." The LSRF survey exists because the honest epistemic position in local SEO is triangulation: survey ~40-47 practitioners who run controlled tests and thousands of client campaigns, then look at where they converge and where they diverge. Shaw explicitly labels the results "opinions... not the inner workings of Google" (Near Media EP 247, March 2026). Treat all local ranking claims — including his — as hypotheses ranked by practitioner consensus.

### 2. Rankings follow *activity*, not setup
The recurring thread across his GBP, review, and photo advice: Google rewards businesses that look **alive**. One-time optimization is table stakes; sustained signals (new reviews weekly, regular photo uploads, updated hours, fresh content) are the differentiator. His review-recency thesis is the sharpest version: a stream of new reviews is partly an *engagement proxy* — evidence the business is operating and customers are interacting.

### 3. Relative value decays; jobs migrate down the stack
His model for why tactics "die": citations didn't stop working, they stopped *differentiating* once every competitor had them. A signal moves from ranking lever → table stakes → hygiene/conversion factor. Diagnose which stage a tactic is in before spending on it.

### 4. Separate ranking factors from conversion factors — then do both
Half the GBP surface (descriptions, Q&A, posts, products, appointment links) has no measured ranking impact but strong conversion impact. Shaw scores them separately and funds them separately. Never justify a conversion tactic with a ranking claim, or vice versa.

### 5. Proximity is the biggest factor you can't control — so plan around it
Since Google's "Vicinity" update (Nov-Dec 2021, the largest local algorithm change since Possum 2016 — per Sterling Sky's analysis), proximity radius tightened sharply. Shaw's response is not despair but scoping: your realistic ranking radius defines your market; win everything controllable inside it (category, name relevance, reviews, engagement), and use organic + LSAs + service pages to reach beyond it.

### 6. Watch the spam to understand the algorithm
Keyword-stuffed business names and fake-review networks work precisely because they exploit real ranking signals. Shaw studies spam as reverse-engineering: what spammers abuse tells you what Google weighs. (His ethics line: understand it, report it, don't do it — while acknowledging spam reporting succeeds only ~20% of the time.)

---

## The Local Search Ranking Factors Survey

**Mechanics (2026 edition, published November 6, 2025):** 47 top local SEO experts scored 187 factors across four result surfaces — the local pack/Maps, localized organic results, conversions, and (new in 2026) **AI search visibility**. The survey takes contributors 2+ hours; results are aggregated into ranked factor lists and category weight treemaps.

### Headline findings by surface (2026)

| Surface | #1 Factor | Notable |
|---|---|---|
| Local pack / Maps | **Primary GBP category** | Keywords in business name #3; being open at search time #5; hidden SAB address #7; review recency #11 |
| Localized organic | **Dedicated page for each product/service** | On-page relevance architecture beats domain-level authority plays |
| AI search (new) | **Presence on expert-curated "best of" lists** | Third-party review-site authority and unstructured mentions dominate; behavioral signals absent (LLMs can't see them) |
| Local Services Ads | **Budget/bidding** | Reviews #2, response speed #4; Google removed proximity from its LSA ranking documentation in May 2024 (Shaw flagged this on X) |

### Factor-level surprises Shaw highlights (2026 report + his "7 Factors" post)

- **Hours of operation is a top-5 pack factor.** Google prefers open businesses; expert observation says "rankings begin to degrade in the final hour that a business is open each day." Tactical corollary: audit competitor hours, extend yours, cover days competitors are closed.
- **GBP services went from "myth" (2023 consensus) to confirmed factor (2026)** — largely on the back of Joy Hawkins/Sterling Sky testing. The survey updates itself when tests land.
- **Behavioral signals rising:** profile dwell time, photo/video views, wayfinding actions, and whether the searcher returns to results are increasingly credited by experts — and are the signal class competitors try to game.
- **Keywords in Google reviews dropped sharply in 2023** after Sterling Sky research questioned it — an example of the survey self-correcting downward, not just up.

---

## Proximity, Relevance, Prominence: How the Weights Moved

Google's own stated triad is proximity, relevance, prominence. Shaw's survey tracks how practitioners see the *controllable* weights shifting underneath it:

- **2021 report:** GBP (then GMB) signals were the top category at roughly **36%** of local pack weight — Shaw noted their "outsized impact" via primary category and business-title keywords. Citations were in steady decline; internal linking and content silos were rising on the organic side.
- **Late 2021:** the **Vicinity update** hardened proximity — smaller radius, more zoomed-in packs, keyword-stuffed business names devalued (temporarily). Businesses that ranked 15 miles out lost that reach (Sterling Sky's characterization).
- **2023 report:** GBP signals eased slightly, on-page signals grew; "proximity of address to centroid" and "links from locally relevant domains" were among the biggest single-factor jumps; "dedicated page for each service" rose ~186% (per SearchLab's summary of the 2023 report).
- **2026 report:** third-party summaries put local pack weights at roughly **GBP ~32%, reviews ~20% (up from ~16% in 2023), on-page ~15-19%, links ~15%, behavioral ~8%, citations ~7%** (figures vary slightly between summaries; treat as approximate and check the Whitespark report directly before citing to a client). Link signals show what Shaw calls a "precipitous decline" over the survey's history.

**The synthesis Shaw teaches:** proximity is dominant and fixed; relevance (primary category, service pages, business name terms) is the highest-ROI controllable class; prominence has bifurcated — for the map pack it now means *reviews + engagement*, for AI surfaces it means *mentions + list placements*, and classic link authority matters less every year.

---

## Citation Strategy Evolution: What Stopped Mattering (and What Came Back)

Shaw is the most credible voice on citations because Whitespark sells citation building and he still publicly demoted it. The arc (from his "Do Citations Still Matter" essay and 2026 interviews):

1. **Early era (2000s-2012): citations were the golden ticket.** Most businesses hadn't claimed listings; volume citation building alone could rank you. The "build 700 citations" playbook was rational then.
2. **Decline (2014-2020): table stakes, not differentiator.** Every serious competitor had the core citations, so incremental citations stopped moving rankings. His 2020 survey showed experts cutting time on citation consistency and aggregators; one called them "almost a non-factor."
3. **His four-part caveat to "citations are dead":** (a) the decline is *relative*, not absolute; (b) clients still report gains after citation cleanup; (c) citations can take ~1.5 years to fully index, so impact is delayed and under-attributed; (d) Uberall's visibility study found wide citation distribution correlated with **89% more direct searches, 102% more driving-direction requests, 87% more website clicks** (correlational, per his citation of the study).
4. **The steady-state prescription (2021-2025):** get NAP right on the ~5 human-visible platforms (Google, Bing, Apple Maps, Facebook, Yelp), the top 30-50 general directories, and 20-30 industry/city-specific sites. Then stop. **Refuse recurring citation fees** for single-location businesses — one-time cleanup holds; ongoing subscriptions only make sense at enterprise scale.
5. **The AI-era comeback (2025-2026): "Citations are back!"** (his own tongue-in-cheek framing). LLMs assemble local recommendations from *mentions* across trusted domains — structured citations, unstructured mentions, review-site presence, and above all **"best of" lists**, the #1 AI-visibility factor in the 2026 survey. The same directory pages that stopped moving map-pack rankings now feed ChatGPT/Gemini answers.
6. **New 2026 tactic — citation description optimization:** most businesses still run a description written in 2007 across every listing. Rewrite them as clean **semantic triples** — "[Business] is [category]. [Business] does [services] in [city]" — so LLMs can parse entity, offering, and geography (Near Media EP 247).

**Decision rule:** citations are a one-time foundation for map-pack purposes, a *living surface* for AI-visibility purposes, and always a conversion/NAP-accuracy hygiene issue. Budget accordingly — never as a monthly ranking lever.

---

## The GBP Optimization Tier List

From his "How to Outrank 99% of Local Competitors" tier list (Whitespark blog). This is the operational priority order for any GBP engagement:

**S Tier — do these or nothing else matters**
- **Primary category:** pick the category matching the exact term you want to rank for ("Criminal defense attorney," not "Law firm"). Re-audit whenever Google adds categories.
- **Keywords in business name:** "the number one most impactful thing" when the query matches — but only legitimately: real DBA/legal name change, updated everywhere, before touching the GBP field. (He simultaneously calls this the most spammable factor in local search.)
- **Consistent new reviews:** 4.7+ average, growing count, and above all steady frequency.

**A Tier — high impact**
- Photos/videos on a regular upload schedule (Google's vision AI extracts relevance; uploads signal activity — "I have seen businesses improve rankings just by implementing a regular photo upload strategy").
- Additional categories (every legitimately applicable one).
- Address/proximity (mostly uncontrollable; matters for office-location decisions).
- Website URL link (connects the profile to your site's relevance data).

**B Tier — helpful**
- Services with detailed descriptions (confirmed factor per Sterling Sky testing), accurate hours (open-now beats closed), Merchant Center product feeds, applicable attributes.

**C Tier — conversion value, no ranking value**
- Google Posts ("free ad space"), products section, social links, appointment URL.

**D Tier — low value**
- Q&A (treat as an FAQ you seed yourself), description (zero ranking impact — conversion copy only), spam reporting (~20% success), messaging.

**F Tier — waste of time**
- **Geotagging images** ("one of the most widely spread myths in the SEO industry" — zero impact), service-area polygons ("all they do is draw a red outline on the map"), keywords stuffed into review responses.

---

## Review Velocity & Recency Framework

Shaw's 2025 thesis: **review recency is the most underrated local ranking factor** — ranked #20 by the 2023 survey, #11 by 2026, and in his view deserving top-5 (Whitespark blog, 2025).

**Evidence he cites:** Joy Hawkins's January 2023 case study — staff incentivized to request reviews → rankings rose; incentive stopped → reviews slowed and rankings fell; restarted → rankings recovered. Plus GatherUp's 2025 consumer survey: 98% of consumers read reviews, 45% weigh recent reviews most.

**Operational rules:**
1. **Velocity target = top competitor + 1.** If the leader gets 2 reviews/month, you need 3. Set the target from a competitor audit, not a vanity number.
2. **Cadence beats bursts.** Quarterly email blasts create visible ranking spikes that decay; asking every customer, every day, creates the sustained signal Google actually rewards. Review requests are daily local SEO work.
3. **Ask timing:** immediately after service, while the experience is fresh.
4. **Expected ratio:** asking *every* customer should yield at least **30:1 positive-to-negative**. If it doesn't, you have an operations problem, not a marketing problem.
5. **Incentivize staff, never customers.** Paying reviewers violates Google guidelines; rewarding employees for *asking* is compliant and proven.
6. **Recency beats perfection:** "getting a negative review is actually better than getting no new reviews at all" — staleness is the bigger ranking risk.
7. **Respond to reviews** — modest ranking evidence, strong conversion and (in AI search) relevance-parsing value.
8. **Diversify beyond Google** for the AI era: industry-specific review sites (Avvo, Healthgrades, Houzz, TripAdvisor, etc.) feed LLM recommendations even though they don't move the map pack (Near Media EP 247).

---

## AI Search Visibility & Brand Reverence

The 2026 survey added AI visibility as a scored surface, and Shaw's 2026 interviews (Near Media EP 247 March 2026, EP 258 May 2026) sketch the emerging playbook:

- **Different retrieval, different levers.** LLMs can't see Google's behavioral data, so the pack's rising signal class is absent. Instead they weigh mentions, list placements, review-site authority, and clean entity descriptions across the web.
- **Rank the lists, not just the pack.** #1 AI factor: expert-curated "best of {category} in {city}" lists. Getting placed on the ones that already rank is the new link building.
- **"Traditional SEO focuses on rankings and clicks. AI-driven SEO focuses on mentions and recommendations."** GBP remains foundational — Shaw calls it your "AI recommendation application," since Gemini and Google AI surfaces draw on it directly.
- **Brand reverence over keyword positions (with Mike Blumenthal, EP 258):** AI answers are non-deterministic and sentiment-aware. The strategic goal shifts to being the most *revered* brand in the local market — niche specialization ("engagement rings," not "jewelry store"), accreditations, community presence (Reddit, sponsorships, local media), and review sentiment strong enough to survive an LLM's summarization. "Traditional SEO is only table stakes."
- **Write for machine parsing:** shorter, declarative site copy ("we are X, we do Y in Z") is replacing 10,000-word service pages; fields long dismissed as cosmetic (GBP description, services text, citation descriptions) become relevance inputs for LLMs even where they never moved map rankings.

---

## Tactical Playbooks

### The local pack audit sequence (Shaw's implied order of operations)
1. Confirm primary category matches the money query; sweep additional categories quarterly.
2. Score business-name relevance vs. the top 3 competitors (note spam; report it, expect ~20% removal).
3. Review audit: count, rating, and **velocity over trailing 90 days** vs. competitors. Set the +1 velocity target.
4. Hours audit: are competitors closed when you could be open?
5. Service/product pages: one dedicated, succinct page per service (the #1 organic factor).
6. Engagement surface: photo/video upload cadence, posts as free ad slots, seeded Q&A.
7. Citations: one-time top-50 + vertical cleanup; rewrite descriptions as semantic triples.
8. AI visibility pass: which "best of" lists rank for your category+city, and are you on them? Are you present and well-reviewed on the vertical review sites LLMs cite?

### SAB (service-area business) handling
Hidden addresses ranked as the #7 pack factor in 2026 — with weird behavior: sometimes Google appears to rank you from a *previous* verified location, or drop a near-random pin (Shaw suspects bugs). His recommendation: if at all feasible, establish a real staffed office where customers can visit, and display it.

### LSA playbook
Budget/bidding first, reviews second, **speed-to-lead** fourth — and Google "uses AI to get transcripts and understand how calls were handled," so answer fast, answer professionally, and close on the phone. (Direct tie-in to phone-led lead capture: a missed or badly handled LSA call is now a ranking input, not just a lost sale.)

---

## Notable Quotes

- "No one knows exactly how Google's algorithm works." — the survey's founding premise (2023 LSRF)
- "Keywords in the business name [are] the number one most impactful thing." — GBP tier list
- "I have seen businesses improve rankings just by implementing a regular photo upload strategy." — GBP tier list
- "Getting a negative review is actually better than getting no new reviews at all." — review recency essay, 2025
- "Service areas don't impact rankings. All they do is draw a red outline on the map." — GBP tier list
- "Geotagging images [is] one of the most widely spread myths in the SEO industry." — GBP tier list
- "Citation description optimization is a hot new tactic for 2026." — Near Media EP 247
- "Traditional SEO focuses on rankings and clicks. AI-driven SEO focuses on mentions and recommendations." — 2026 commentary
- "Google has a stranglehold on this industry." — on GBP data + behavioral signals as Google's AI moat, Near Media EP 247

---

## Anti-Patterns / What He Argues Against

1. **Mass citation building and recurring citation fees.** The "700 citations" era is over; monthly citation subscriptions for a single-location business are rent extraction. One-time top-50 + verticals, then done.
2. **Geotagging image EXIF data.** Persistent myth, zero measured effect.
3. **Keyword-stuffing review responses and GBP descriptions** for rankings — no effect, looks unprofessional.
4. **Review blitzes.** A burst every 6 months produces a spike-and-decay pattern; the algorithm rewards steady cadence.
5. **Incentivizing customers for reviews** — guideline violation; incentivize your staff's *asking* behavior instead.
6. **Treating the survey as gospel.** He is explicit that LSRF is aggregated opinion; individual factors get demoted when controlled tests (often Sterling Sky's) contradict consensus.
7. **Optimizing setup once and walking away.** Static profiles decay against competitors emitting activity signals.
8. **Chasing map-pack radius you can't win.** Post-Vicinity, distant rankings are mostly gone; fighting proximity instead of scoping to it wastes budget.
9. **Assuming a "level playing field" on behavioral signals** — competitors run engagement manipulation; understand it, don't copy it.

---

## Edges & Open Questions

Signals Shaw flags as unsettled — track these rather than treating them as doctrine:

- **Hidden-address SAB behavior:** possibly a bug (previous-location fallback or random pin), not a stable penalty. Re-test before advising a client to reveal or hide an address.
- **Behavioral-signal weighting:** experts believe it is rising, but it is the hardest class to isolate in tests and the easiest to manipulate; expect survey volatility here.
- **Review keyword content:** demoted in 2023 after Sterling Sky research, noted as needing further validation — the survey may swing back if new tests contradict.
- **AI-surface volatility:** the 2026 AI-visibility factor list is a first edition; retrieval sources for ChatGPT/Gemini shift quarterly, so re-verify the "best of" list thesis each cycle.
- **Category weight percentages** differ slightly between third-party summaries of the same report; only the report itself is citable in client work.

---

## How This Maps Into Kai

| Kai surface | How to use this doc |
|---|---|
| `knowledge/playbooks/local-seo-gbp-optimization.md` | Primary companion. The GBP tier list is the priority order for any GBP engagement; the review velocity rules (+1 target, 30:1 ratio, cadence-over-bursts) are the review-program spec. |
| `/kai-seo-audit` (local mode) | Use the "local pack audit sequence" above as the local module checklist. Cite survey positions (primary category #1, name keywords #3, hours #5, review recency #11) when prioritizing recommendations — attributed to Whitespark LSRF 2026, and verify current-year numbers via the collector before putting them in client deliverables (Kai Data Provenance Rule applies). |
| `/kai-cro-audit` + KaiCalls fit checks | Shaw's LSA finding — call handling transcribed and scored by Google, speed-to-lead a top-4 LSA factor — is direct third-party support for phone-led lead-capture recommendations on local businesses. |
| `knowledge/people/joy-hawkins-knowledge.md` | Cross-reference: Shaw's survey repeatedly incorporates Hawkins/Sterling Sky test results (services factor, review keywords demotion, hours testing, review velocity case study). Load both for local SEO work. |
| AEO/AI-search workflows (`kai-surround-sound`, AEO playbook) | His AI-visibility findings (best-of lists #1, mentions over links, semantic-triple entity descriptions, review-site diversification) are the local-business instantiation of Kai's entity/citation AEO doctrine. |
| Citation/directory recommendations in any audit | Enforce his decision rule: one-time top-50 + vertical citations, no recurring fees for single locations, but treat citations as an active AI-visibility surface in 2026. |

**Freshness note:** LSRF is annual. Before citing weights or factor ranks in client work, confirm against the current report at whitespark.ca/local-search-ranking-factors — numbers in this doc reflect the 2026 edition (published November 2025) and third-party summaries of it, and category percentages vary slightly between summaries.

---

## Sources

- https://whitespark.ca/local-search-ranking-factors/ — 2026 LSRF report page (Whitespark, Nov 2025)
- https://whitespark.ca/?page_id=5641 — 2021 Local Search Ranking Factors (Whitespark)
- https://whitespark.ca/blog/7-local-search-ranking-factors-that-may-challenge-your-current-thinking/ — factor deep-cuts from the 2026 survey
- https://whitespark.ca/blog/do-citations-matter-local-seo/ — citation strategy evolution essay
- https://whitespark.ca/blog/the-most-underrated-local-ranking-factor-in-2025/ — review recency thesis
- https://whitespark.ca/blog/how-to-outrank-99-of-local-competitors-google-business-profile-tier-list/ — GBP tier list
- https://whitespark.ca/darren-shaw-whitespark-founder/ — founder bio
- https://searchlabdigital.com/blog/just-released-2026-local-search-ranking-search-factors/ — 2026 LSRF summary
- https://searchlabdigital.com/blog/2023-lsrf/ — 2023 LSRF summary
- https://www.nearmedia.co/ep-247-from-the-archives-local-search-ranking-factors-darren-shaw-on-reviews-ai-search-what-drives-local-rank/ — Near Media interview, March 2026
- https://www.nearmedia.co/ep-258-from-keyword-rankings-to-brand-reverence-the-new-local-ai-seo-blueprint-with-darren-shaw/ — Near Media interview, May 2026
- https://www.sterlingsky.ca/vicinity-algorithm-update/ — Vicinity update context (Sterling Sky)
- https://w3marketinghub.com/seo/local-seo-ranking/ — third-party 2026 weight summary
- https://blckalpaca.at/en/knowledge-base/seo-geo/local-seo/local-ranking-factors-2026-the-complete-overview — third-party 2026 weight summary
- https://x.com/DarrenShaw_/status/1793305472340291623 — Shaw on proximity removed from LSA ranking docs (May 2024)
