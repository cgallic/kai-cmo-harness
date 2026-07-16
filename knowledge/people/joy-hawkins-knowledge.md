# Joy Hawkins: Knowledge Distillation

**Created:** July 2026
**Sources:** Sterling Sky published case studies and ranking experiments (2021-2026), her spam-fighting guide, Whitespark ranking-factor writeups crediting her tests, LocalU interview, Sterling Sky bio pages. All quantitative claims cite the specific study.

---

## Table of Contents

1. [Background](#background)
2. [Core Philosophy & Mental Models](#core-philosophy--mental-models)
3. [Framework: Single-Variable GBP Testing](#framework-single-variable-gbp-testing)
4. [Framework: The Local Pack Ranking Factor Hierarchy](#framework-the-local-pack-ranking-factor-hierarchy)
5. [Framework: The Review Engine](#framework-the-review-engine)
6. [Framework: The Spam-Fighting SOP](#framework-the-spam-fighting-sop)
7. [Framework: Service-Area Business (SAB) Nuances](#framework-service-area-business-sab-nuances)
8. [Framework: The 2026 Local Visibility Shift](#framework-the-2026-local-visibility-shift)
9. [Tactical Playbooks](#tactical-playbooks)
10. [Notable Quotes](#notable-quotes)
11. [Anti-Patterns / What She Argues Against](#anti-patterns--what-she-argues-against)
12. [How This Maps Into Kai](#how-this-maps-into-kai)
13. [Sources](#sources)

---

## Background

Joy Hawkins is the owner of **Sterling Sky** (local SEO agency, Uxbridge, Ontario + a US entity), the **Local Search Forum** (bought from her mentor Linda Buquet), and **LocalU** (conference/education series where she is also faculty). She has worked in local SEO since **2006**, self-taught, starting at a Toronto company selling AdWords when Google Places launched, then ~8 years at Imprezzio Marketing (from 2009) troubleshooting the hardest ranking cases at an agency serving ~1,300 SEO/SEM clients (LocalU interview) before founding Sterling Sky. Credentials that matter for weighting her claims:

- **Google Business Profile Product Expert** (volunteer on Google's own forum) and former Google MapMaker Regional Lead (USA) — she sees Google's moderation behavior from the inside.
- Search Engine Land columnist; speaker at MozCon, Pubcon, SearchLove, brightonSEO, State of Search, SMX, Whitespark Local Search Summit.
- BS in Communications (Advertising), Liberty University, summa cum laude.

Her distinctive position in the industry: she is the person who **runs controlled experiments on Google Business Profiles and publishes the results**, including the ones that kill popular tactics. Sterling Sky's client base skews toward phone-led local service businesses: law firms, dentists, garage door companies, home services.

---

## Core Philosophy & Mental Models

### 1. Watch what Google does, not what Google says
Her closing line on the 2025 "near me" study: "SEO isn't magic. It's about the process, testing, and a lot of paying attention to what Google does (not just what they say)." Google's official guidance and Google's algorithm routinely disagree (e.g., Google tells service-area businesses to hide their address; her tests show hiding it tanks pack rankings). When guidance and observed behavior conflict, behavior wins — but she still flags the compliance risk of acting on it.

### 2. Test one variable on listings nobody is touching
Her experiments isolate a single change on GBP listings with **no other active SEO work** (no content, links, or review campaigns running), so movement can be attributed. The salad bar restaurant had no website and no brand mentions anywhere online — a perfect isolation chamber.

### 3. The 48-hour signal window
Fields that actually matter to the local algorithm (categories, business name, website link) "generally result in an increase in ranking within 48 hours" of changing them (geotagging study, Sterling Sky). Corollary decision rule: if you change a GBP field and see nothing move for weeks, it is probably not a ranking factor — stop investing there.

### 4. Correlation traps: always diagnose the confound
In her own Google Posts test, one listing's ranking "drop" turned out to be Google filtering it against a same-address sibling listing, and another's fluctuation was a job pack entering and leaving the SERP. She treats every ranking change as guilty of confounding until proven otherwise. Rank trackers report symptoms, not causes.

### 5. Diminishing returns govern most local tactics
Reviews boost rankings up to ~10, then plateau. Spam fighting works until the spammer rebrands legally. Photos help in visual industries, not in garage door repair. The question is never "does X work?" but "where does X stop working?"

### 6. It's all relative to competitors
Her answer to "how many reviews do I need per month": "it depends and it's all relative. You really need to look at your competitors" (review recency study). Benchmarks are market-local, not global.

### 7. Puzzles over processes
"You definitely have to be good at solving puzzles and be one of those people that is never content with your current processes... I'm always looking for things that everyone else missed" (LocalU interview). Her troubleshooting method is diagnostic, not checklist-first.

---

## Framework: Single-Variable GBP Testing

Her repeatable experiment design, reverse-engineered from published studies:

1. **Pick dormant listings.** No active SEO efforts, small markets, low noise. (Posts test: 3 listings; geotag test: 5 listings; review-threshold test: 3 businesses in different regions with identical review counts.)
2. **Establish a baseline** with a geo-grid / rank tracker (she uses Places Scout; also cites Local Falcon grids) across a wide keyword set — the Posts test tracked **441 keywords per location** for 9 weeks.
3. **Change exactly one field.** Add the keyword, the service, the photos, the hours — nothing else.
4. **Watch the 48-hour window** for real factors; run multi-week observation for slow factors.
5. **Reverse the change** (A-B-A design). The salad bar test added "Salad Bar" to a restaurant's GBP name, removed it, then re-added it: rankings jumped dramatically within hours, fell back when the keyword was removed, and jumped again when re-added.
6. **Audit every anomaly for confounds** (listing filters, SERP feature changes, job packs) before attributing.
7. **Repeat across clients** before claiming a conclusion ("we have repeated this test many, many times with our clients").
8. **Publish, including null results.** Null results (posts, geotags) are treated as equally valuable output.

Decision rule embedded here: a case study is a *pattern claim*, not proof — "individual examples may not serve as definitive proof of how Google's algorithm operates, collectively, they provide valuable insights" (review recency study).

---

## Framework: The Local Pack Ranking Factor Hierarchy

What actually moves local pack rankings, per Sterling Sky's tests and the 8,186-business "near me" study (Nov 2025, with Places Scout: 5 home-service queries across 100 large + 50 mid + 50 small US cities, top-10 pack results):

### Tier 1 — proven, fast-acting levers
- **Keywords in the GBP business name.** The strongest controllable signal she has documented. Salad bar test: dramatic pack-ranking jump within hours of adding the keyword. When Google stripped keywords from a drug rehab's stuffed name, it fell from position 1 to 7 in two days. Multiple keywords **side-by-side** in the name compound the effect. Caveat: adding descriptors violates Google's guidelines and risks suspension — the compliant route is an actual legal rebrand/DBA.
- **Primary category (and category changes).** Moves rankings within ~48 hours (cited as a known-mover control in her geotag study).
- **Predefined services.** Her discovery (credited by Darren Shaw at Whitespark, who replicated it Oct 2024): checking Google's *predefined* service options — not free-text custom services — lifted an untouched electrical contractor from position 41+ into positions 4-10 on many terms within ~3 days, strongest on long-tail queries.
- **Openness / business hours.** New factor she documented after the **November 2023 core update**: listings sink or vanish from the pack when the business is marked closed and recover when open. Verified via ranking reports run two hours apart (closed vs open — e.g., a lawyer, a psychiatrist on weekends, restaurants); confirmed by a reader in Japan. 24-hour businesses gain at night. Per Whitespark's 2025 factor writeup, rankings even begin to degrade in the final hour a business is open. Implication: hours are now a strategic field, not an administrative one — but only list 24/7 if you genuinely answer.

### Tier 2 — proven, gradual levers
- **Review velocity and recency** (see The Review Engine below).
- **Visible address / map pin.** Negative correlation between "is service area business" (hidden address) and near-me pack rankings; replicated on two client locations (see SAB Nuances).
- **Review text.** Reviews with substantive text outrank star-only ratings in impact; Google appears to mine review content for relevance.
- **Landing page content.** Slight positive correlation between count of substantive (non-stop) words on the GBP-linked landing page and pack rank. Meaningful words, not word count.
- **Linking the GBP to the right page.** Inner/location page vs homepage was her long-standing "one move" answer for pack ranking, alongside a few backlinks (LocalU interview; the website field is also on her 48-hour movers list).

### Tier 3 — conditional or conversion-only
- **Photos.** Help engagement and rank in visual industries (restaurants, salons); no measurable ranking effect for e.g. garage door companies.
- **Review count past ~10.** Threshold effect at 10, then plateau (see Review Engine).
- **Google Posts.** Zero ranking effect; useful for conversions only.

She is explicit that proximity remains the dominant uncontrollable factor and that no single lever wins alone: "There is no one magic ranking factor. But there are some strong patterns, especially when you stack them together" (near-me study).

---

## Framework: The Review Engine

Sterling Sky's review doctrine, from the review-count case study (updated April 2025) and the review-recency case study (July 2025):

1. **The Magic 10 threshold.** Going from 9 → 10 reviews produced a measurable Maps ranking bump across three separate same-industry businesses in different regions (2025 retest of an earlier Sterling Sky finding). Going 10 → 11 produced no comparable bump. Earlier test: an insurance practitioner listing rose when reviews went 3 → 16, with no further gain 16 → 31. Independent corroboration she cites: Joel Headley (PatientPop saw appointment-lead lift above ten reviews) and Mike Blumenthal (LocalU).
2. **Velocity over volume.** Reviews received *this month* matter more than lifetime total (near-me study). A dental client pulling 60+ reviews/month dominated the pack; after they stopped for **18 days**, rankings "fell off a cliff," while competitors getting 15-45/month held steady.
3. **Recency is a diagnostic.** When a client's rankings sank post-Vicinity update, the root cause was that incoming reviews had flat-lined after the owner stopped a staff incentive program; restarting it recovered rankings. Another client filtered out of historic keywords had gone 3+ years without a new review.
4. **Cadence is competitor-relative.** Use Pleper's Chrome extension on a Maps search to see average/top/bottom review counts for the pack you're fighting for; match or beat the winners' cadence. Weekly in competitive markets, monthly may suffice in small ones. The one absolute: never let reviews stop.
5. **Text beats stars.** Encourage detailed written reviews; 1-star ratings without text don't even display in the Google Maps app, so don't panic over them.
6. **Incentivize staff, never customers.** Her compliant mechanism: customers who name a staff member in a review put that employee into a weekly cash-draw lottery ($5-$50). Incentivizing *reviewers* violates Google policy; incentivizing your *team's ask* does not (verify industry-specific regulations first).
7. **More reviews still pay after the rank plateau** — through click-through rate and conversion, not position. A personal-injury attorney "killing it with reviews" still ranked poorly: reviews are one input, not the algorithm.

---

## Framework: The Spam-Fighting SOP

From her long-running "Ultimate Guide to Fighting Spam on Google Maps" (maintained since 2016; 2025 edition). She also presented "The State of Spam Fighting" after analyzing 5,306 listings in 16 industries (LocalU, April 2022).

### The four spam types to target
1. Keyword stuffing in business names
2. Businesses ineligible for Maps (no real presence/eligibility)
3. Duplicate listings for the same business
4. Listings at locations where the business doesn't physically exist (fake/virtual offices, lead-gen fronts — she flags personal injury law as a hotbed of lead-gen listing spam)

### Research before reporting (evidence stack)
- **Name:** Does it match the signage in Street View? The Secretary of State business registry? The state bar (lawyers) or NPI registry (medical)? Their own website's About page?
- **Phone test:** Call (from an anonymized line). Spammers answer generically ("Hello, locksmith"); real businesses answer with their name.
- **Address:** Street View confirmation; search the address (UPS Store or mail service = ineligible); zoom the map for co-located listings; drive-by photos as proof.
- **Networks:** Same address/phone across many listings = spam network (can be thousands of listings). Check shared IPs and reviewer profiles — a "customer" reviewing two garage-door companies in two states is a marketing company.

### Reporting mechanics and decision rules
- **Suggest an Edit** (Google Maps) for simple cases; it builds your editor trust profile, but edits to obvious spam are frequently denied — check your contributions tab because denials generate no email.
- **Business Redressal Complaint Form** for strong cases; turnaround ~2 weeks at time of writing. Evidence rules: government sources, the real business's website, your own photos, and zoomed Street View links only — **never cite third-party sites** (Facebook/Yelp) as proof.
- **Expect regression.** Verified listings get incorrectly reinstated "all the time"; owners re-add stuffed keywords the next day. Log every case ID, re-report, and document the revert count — repeat offenses build the case for a soft suspension (Google has also issued hard penalties for repeat keyword stuffers).
- **Track everything in a spreadsheet.** Organization is the highest-return spam-fighting skill.

### Strategic caveats (the part most spam guides skip)
- Spam fighting is **not a long-term strategy**: the need fades unless you keep entering new markets, and legal rebranding has made keyword-rich names increasingly untouchable.
- **Check the filter first:** sometimes the spam listing is *filtering* your competitor's real listing; removing it can promote the competitor, not you.
- Report competitors who stuff names — it's a rigged ranking benefit, and removals demonstrably drop them (position 1 → 7 in two days in her rehab example) — but expect to file multiple reports.

---

## Framework: Service-Area Business (SAB) Nuances

- **Hiding your address hurts pack rankings**, despite Google's guidance that SABs should hide it. The near-me study found "is service area business" negatively correlated with ranking; on a real home-service client, hiding the address made rankings free-fall and restoring it a month later brought them back — replicated on a second location. Her rule: "Have a real office with a real address" if you want to compete on near-me queries.
- Whitespark's 2025 factor roundup (Miriam Ellis) reports the emerging theory that hiding the address may revert the ranking radius or attach a random map pin.
- **Same-address listings filter each other.** Two listings verified at one address (even with different sites/phones) compete for one slot; Google shows one and hides the other. Diagnose "ranking drops" for possible filtering before blaming your changes (Google Posts study).
- **Multi-location expansion is a visibility hedge** — one of her top 2026 recommendations, since each additional legitimate location is another chance to appear as pack real estate shrinks.
- SAB-heavy categories (locksmiths, garage door, addiction treatment, personal injury) are the highest-spam battlegrounds; budget spam-fighting time there.

---

## Framework: The 2026 Local Visibility Shift

Her "State of Local SEO in 2026" thesis (June 2026): rankings can hold steady while *outcomes* decline, because Google is restructuring the SERP itself.

**The evidence she published:**
- **Clicks-to-call from GBPs are falling.** Jepto data compiled at her request across 179 profiles / 34 US law firms shows a 2-year decline in profile calls — specific to mobile (call buttons), not desktop website clicks.
- **AI-powered local packs** (mobile, US): appearing on ~7% of tracked keywords; show only 1-2 businesses instead of 3; have **no call buttons**; and feature different businesses than the 3-pack. Places Scout analysis: AI packs surfaced 5,943 unique businesses vs 18,330 in traditional packs (~32%); in 88% of 322 markets, AI packs showed fewer unique businesses.
- **Call buttons replaced by images** in several industries (tracked with Jepto since the dentist rollout, with sizable call-click declines).
- **Pay-to-play acceleration:** local pack ads on mobile grew from ~1% of her tracked reports (early 2025) to ~22% (Dec 2025); LSAs from ~11% to ~31% of tracked queries.
- **ChatGPT is not the traffic thief (yet):** for a large multi-location client, ChatGPT referrals grew from 0.1% to 2% of Google's traffic year-over-year — still only 22% of what Bing sends. Google's own AI Overviews are what crushed blog/article traffic.

**Her prescriptions for 2026:**
1. Write content competitors haven't written (information gain), not clones of what already ranks.
2. Open more locations to offset shrinking per-listing visibility.
3. Run Google Ads (all formats) — ads are inheriting the call buttons and placement organic is losing, and ad ROI improved for her clients.
4. Move expertise content to YouTube/Reddit — slow, but durable as AI eats informational search.
5. Track AI referral traffic now (she points to Seer's tracking template), before it matters.

**Penalty-era recovery (Aug 2025 spam update case study, Feb 2026):** she diagnosed a client's organic collapse to 5-year-old exact-match-anchor comment/PBN links being devalued (referring domains up while traffic down = devaluation signature; the linking sites were tanking too). Her recovery play is the **Avalanche technique** (credited to Kyle Roof): abandon the lost head terms, win the keywords already in positions 3-10 — the "SEO goldmine," since position 2 → 1 substantially lifts CTR — and rebuild credibility upward. "When you build your house on sand, you have to expect that one day it will come crashing down."

---

## Tactical Playbooks

### GBP optimization order of operations (synthesized from her tests)
1. Verify the **primary category** is the best-fit, highest-volume option; audit competitors' categories.
2. Add **every applicable predefined service** Google suggests (not just custom text services).
3. Set **hours accurately and as generously as honestly possible**; consider genuine 24/7 answering (pairs with call-handling — Google's LSA AI now transcribes and evaluates how calls are answered, per Whitespark 2025).
4. Show the **address** if you have any legitimate office; get the map pin right.
5. Link the profile to the **best-matching inner page**, with substantive descriptive content on it; use UTM codes so GBP traffic is separable in analytics.
6. Ignore posts/geotags as ranking work; use posts for offers and conversion messaging only (average post CTR she measured: ~0.5%).

### Review program setup
Get to 10 reviews fast → build a staff-side incentive for the *ask* → target competitor-matching monthly velocity (Pleper benchmark) → prompt for written detail → respond to reviews → never stop. Treat any 3-week gap as an incident.

### Local ranking-drop diagnosis checklist (her repeated diagnostic moves)
1. Did the business's **hours** change, or is the report running while they're closed? Re-run the grid during open hours.
2. Did **review velocity** flat-line? (GMB Everywhere review audit; check for stopped internal programs.)
3. Is the listing being **filtered** by a same-address/same-category sibling?
4. Did a **SERP feature** (job pack, AI pack, ads) displace the pack rather than the ranking falling?
5. Did a competitor **rebrand or stuff keywords** into their name?
6. Was the address recently **hidden**, or the map pin moved?
7. On the organic side: check for **devalued spam links** (traffic down while referring domains up; anchors match the losing keywords).

### Spam-fighting cadence
Monthly sweep of your money categories in target cities → evidence workbook per offender → Suggest an Edit for simple cases, Redressal Form with government-source evidence for hard ones → recheck in 2 weeks → re-report reverts with revert history documented.

---

## Notable Quotes

- "SEO isn't magic. It's about the process, testing, and a lot of paying attention to what Google does (not just what they say)." — near-me study, Nov 2025
- "It's not the total reviews. It's the recent ones." — near-me study, Nov 2025
- "I think there is a lot of value in Google posts, they just aren't a ranking factor." — comment on her Posts study, July 2021
- "Fixing business names is important because the business name is a ranking factor so those who are breaking the guidelines are reaping a benefit that those who are following the rules cannot have." — spam guide comments, June 2016
- "When you build your house on sand, you have to expect that one day it will come crashing down." — on black-hat link building, Aug 2025 spam update case study
- "You definitely have to be good at solving puzzles and be one of those people that is never content with your current processes." — LocalU interview
- "If you spend time geotagging photos as a part of your local SEO strategy, I would advise spending that time elsewhere." — geotagging study

---

## Anti-Patterns / What She Argues Against

1. **Geotagging photos for rank.** Tested on 5 GBP listings + 3 websites: zero movement in pack, organic, or image traffic. Google strips the EXIF data on upload anyway (Joel Headley concurring).
2. **Google Posts as a ranking tactic.** 9 weeks, 3 listings, 441 tracked keywords per location: no ranking effect. Conversion tool only.
3. **Chasing total review count.** Plateau after ~10 reviews; a stagnant pile of reviews loses to a competitor's steady drip.
4. **Stuffing keywords into the GBP name.** It works — which is exactly why it's a suspension risk and a spam-report magnet. The compliant version is a real rebrand; otherwise, report competitors doing it rather than copying them.
5. **Hiding the address because Google said so** (for SABs) — repeatedly measured ranking damage.
6. **Exact-match-anchor comment links and PBNs.** Fast results, delayed detonation; devaluation showed up years later in the Aug 2025 spam update.
7. **Copying whatever the top-ranked competitor does.** "Competitor analysis should inform your strategy, not your tactics — never replicate manipulative methods just because competitors use them" (Aug 2025 case study). Also her 2026 content advice: write what competitors haven't written.
8. **Trusting rank trackers at face value.** SERP-feature churn and listing filters masquerade as ranking changes.
9. **One-report spam fighting.** Single reports get denied or reverted; persistence with documented evidence is the method.
10. **Assuming ChatGPT is why your traffic fell.** Her client data points at Google's own AI surfaces and SERP redesign, not ChatGPT (2% of Google's referral volume as of 2026).

---

## How This Maps Into Kai

| Kai surface | How to apply this doc |
|---|---|
| `knowledge/playbooks/local-seo-gbp-optimization.md` | Primary companion. Use the Ranking Factor Hierarchy and GBP order-of-operations as the prioritization spine; the Review Engine thresholds (10-review threshold, 18-day velocity rule, competitor-relative cadence) as concrete targets. |
| `/kai-seo-audit` (harness/skills/kai-seo-audit) | Load for any local/GBP audit. Add her diagnosis checklist (hours/openness, review velocity flat-line, listing filter, SERP-feature displacement, competitor name-stuffing, hidden address, devalued links) to the audit runbook. All quantitative claims in client-facing audits must still pass the Kai Data Provenance Rule — cite collector data, not this doc, for the client's own numbers. |
| `/kai-audit`, CRO audits | Openness finding: recommend accurate/extended hours and call answering; pairs with the KaiCalls fit rule for phone-led businesses (missed calls now interact with LSA call-quality evaluation and shrinking call buttons). Disclose KaiCalls ownership per house rules. |
| `/kai-competitors` | Spam-Fighting SOP for competitor teardown in local verticals: detect name-stuffing, fake locations, review networks; decide report-vs-ignore using her filter caveat. |
| `/kai-surround-sound`, AEO work | Her 2026 shift data (AI local packs, pay-to-play, YouTube/Reddit expertise) supports diversification recommendations; treat her stats as dated snapshots (2025-2026) and re-verify before publishing them. |
| Content pipeline | Her "write what competitors haven't written" doctrine reinforces the Information Gain principle in `knowledge/frameworks/aeo-ai-search/`. |

**Freshness warning:** local algorithm behavior changes fast (openness became a factor overnight in Nov 2023). Treat every ranking-factor claim here as dated to its cited study; re-verify against sterlingsky.ca and localsearchforum.com before making client-facing claims.

---

## Sources

1. https://www.sterlingsky.ca/what-gets-you-ranking-for-near-me-2025/ — 8,186-business near-me study (Nov 2025)
2. https://www.sterlingsky.ca/ultimate-guide-fighting-spam-google-maps/ — spam-fighting guide (2016, updated Aug 2025)
3. https://www.sterlingsky.ca/the-state-of-local-seo-in-2026/ — State of Local SEO 2026 (June 2026)
4. https://www.sterlingsky.ca/do-google-posts-impact-ranking/ — Google Posts test (July 2021)
5. https://www.sterlingsky.ca/geotagging-photos-impact-ranking/ — geotagging test (updated Jan 2024)
6. https://www.sterlingsky.ca/google-added-a-new-ranking-factor/ — business hours / openness factor (Dec 2023)
7. https://www.sterlingsky.ca/keyword-stuffing-gmb-name/ — keywords-in-name / salad bar test (updated Aug 2023)
8. https://www.sterlingsky.ca/number-of-reviews-impact-ranking/ — review count threshold case study (updated April 2025)
9. https://www.sterlingsky.ca/google-review-recency-ranking/ — review recency case study (updated July 2025)
10. https://www.sterlingsky.ca/august-2025-spam-algorithm-update/ — Aug 2025 spam update / Avalanche recovery case study (Feb 2026)
11. https://www.sterlingsky.ca/about-us/joy-hawkins/ — bio and credentials
12. https://whitespark.ca/blog/7-local-search-ranking-factors-that-may-challenge-your-current-thinking/ — Miriam Ellis, Whitespark (Dec 2025), on openness/SAB/name factors
13. https://whitespark.ca/blog/how-to-easily-boost-local-rankings-with-googles-predefined-services/ — Darren Shaw, Whitespark (Oct 2024), predefined services replication crediting Hawkins
14. https://localu.org/localu-interview-series-joy-hawkins/ — LocalU interview (Imprezzio-era, republished May 2024)
