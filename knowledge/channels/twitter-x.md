# X (Twitter) Organic Strategy and Posting Rules

> **Use when**: Writing X posts, planning threads, building reply strategy, deciding cadence, reviewing automation, or preparing an organic post that may later be promoted.

Last updated: 2026-07-13

Primary references:
- X For You recommendations: https://help.x.com/en/resources/recommender-systems/for-you-home-timeline-recommendations
- X conversation recommendations: https://help.x.com/en/resources/recommender-systems/conversations-recommendations
- X search recommendations: https://help.x.com/en/resources/recommender-systems/search-recommendations
- X organic guidance: https://business.x.com/en/basics/organic-b%65st-practices
- X automation rules: https://help.x.com/en/rules-and-policies/x-automation
- X authenticity policy: https://help.x.com/en/rules-and-policies/authenticity
- X developer policy: https://docs.x.com/developer-terms/policy
- X Ads policies: https://business.x.com/en/help/ads-policies
- X algorithm repository: https://github.com/xai-org/x-algorithm
- X Community Notes: https://help.x.com/en/using-x/community-notes
- X Articles: https://help.x.com/en/using-x/articles
- X Spaces: https://help.x.com/en/using-x/spaces
- X Premium and checkmark features: https://help.x.com/en/managing-your-account/about-x-bluecheck

---

## Core Read

X distribution is personalized recommendation, not a single posting hack. The feed pulls candidate posts from in-network and out-of-network sources, predicts positive and negative viewer actions, filters unsafe or low-quality content, then mixes the timeline.

Use X as a conversation and authority channel. The default strategy is:

**short text + useful replies first, threads second, native media for proof, links last.**

Do not treat exact public "algorithm weights" as doctrine. Use them as test ideas only when the source is not official or current.

The `xai-org/x-algorithm` repo was updated on May 15, 2026 with an end-to-end retrieval-to-ranking pipeline, Grok-based content understanding, ad blending modules, query hydrators, candidate hydrators, and additional candidate sources. Treat the repo as high-signal architecture evidence, not a guarantee of current production weights.

---

## Ranking Signals

High-confidence signal families from X's recommendation docs:

- **Viewer relevance**: followed accounts, followed Topics, liked posts, network likes, similar-interest behavior, language, and location fit.
- **Engagement prediction**: likes, replies, reposts, quotes, clicks, profile clicks, video views, photo expands, shares, follows, active minutes, and dwell.
- **Negative feedback**: not interested, block, mute, report, spam reports, policy labels, abusive replies, low-quality determinations, and muted keywords.
- **Conversation quality**: reply relevance, whether the viewer follows the replying account, whether the original author replied, and account reputation signals.
- **Media interaction**: watched media, media details, video retention, photo clicks, and media popularity.
- **Freshness and diversity**: old posts, repeated authors, duplicate posts, duplicate conversation branches, deleted content, blocked accounts, and muted accounts are filtered or reduced.
- **Author diversity**: repeated author exposure can be attenuated, so many similar posts in a short window can compete with each other.
- **Content understanding**: X's public algorithm materials describe classifiers and embedders for spam, post category, policy, media, language, quote expansion, and brand-safety signals.
- **Search-specific ranking**: X's search recommendations doc separates Top, Latest, People, Media, and Lists. Top search weighs engagement, health, and relevance, while Latest is reverse-chronological with visibility filtering.
- **Search-specific enforcement**: X's July 2026 search rules page says duplicate or near-duplicate posts, automated posts/replies, keyword-triggered bot messages, aggressive follow churn, and similar posts across multiple accounts can be filtered out of search even when followers can still see the post. Source: https://help.x.com/en/resources/recommender-systems/search-recommendations and https://help.x.com/en/rules-and-policies/x-search-policies (accessed 2026-07-13 in browser).

Practical implications:

1. Write posts that deserve replies, not passive likes.
2. Build network overlap before expecting out-of-network reach.
3. Use native media when it proves the point.
4. Avoid duplicate or substantially similar posts.
5. Treat blocks, mutes, reports, and spam flags as reach killers.
6. Treat links as conversion steps after native value has earned attention.
7. Do not spray many similar posts in a narrow window; diversity and dedup filters can make them fight each other.
8. Write with entity clarity if search matters. X search is not only chronological; healthy engagement and relevance affect Top results.

---

## Account Capabilities

Do not assume every X account can use every format.

| Capability | Requires | Harness implication |
|---|---|---|
| Standard post | X account | Default to 280 characters unless the brief says the account has Premium long-post access |
| Longer post | X Premium feature | Use only for memos, teardowns, checklists, or founder POV that needs depth |
| Articles | Premium, Premium+, Premium Business, or Premium Organizations | Use for native long-form category POV; post a short native hook that points to the Article |
| Reply prioritization | Premium tier, larger at higher tiers | Useful for reply-led growth, but not a substitute for relevance or specificity |
| Creator monetization | Premium or organization subscription plus eligibility requirements | Do not optimize brand accounts for payout unless monetization is an explicit goal |
| X Ads | Verified advertiser-eligible account | Check `x-ads-policy-reference.md` before promoting an organic post |

Premium can change account capabilities, reply placement, and long-form access. It does not erase negative feedback, policy risk, weak hooks, or poor audience fit.

---

## Operating Cadence

Set cadence by channel priority.

| Priority | Posting cadence | Reply cadence | Use when |
|---|---:|---:|---|
| Core X channel | 3-5 original posts per day | 10-20 useful replies per day | Founder-led, media-led, B2B authority, creator, active category |
| Secondary X channel | 1-2 posts per day | 5-10 useful replies per day | SaaS, local services, service firms, support plus category POV |
| Maintenance | 10-15 total posts per week | 3-5 replies per weekday | Lean team, reputation proof, event/commentary support |

Post timing test windows:

- Start with Tuesday-Thursday, 9-11 AM in the audience's local time.
- Test a second window Monday-Friday, 12-6 PM for B2B and live discussion.
- Replace benchmark timing with account analytics after 30 days.

Volume alone is not a strategy. If impressions fall while cadence rises, reduce repetition and raise post specificity.

---

## Weekly Format Mix

Use this as the default harness mix:

| Format | Share | Job |
|---|---:|---|
| Short text insight | 35% | One observation, one implication, one useful takeaway |
| Replies | 20% | Distribution, research, and relationship-building |
| Quote reposts | 15% | Add analysis, contradiction, example, or data |
| Threads | 10% | Frameworks, audits, teardowns, lessons, stories |
| Media posts | 10% | Screenshots, charts, 15-second clips, process proof |
| Polls | 5% | Research, segmentation, language mining, objection mining |
| Product or CTA posts | 5% | Offers, demos, lead magnets, announcements |

Product-heavy accounts should keep promotional posts under 20% unless the account is explicitly support, status, or launch-only.

---

## Patterns

### Observation Post

```text
Most [audience] think [common belief].

The real problem is [specific mechanism].

Do [action] before [expensive mistake].
```

### Local-Service Post

```text
A [city/service] lead does not need more choices.

They need:
- response in under [time]
- clear next step
- proof you handle [specific job]
- no phone tag

The business that answers first usually wins.
```

### B2B Authority Post

```text
We reviewed [number/source] [asset type].

Pattern:
[specific finding]

Why it matters:
[commercial implication]

What to change:
[action]
```

### Quote Repost

```text
This is true, but incomplete.

The missing variable is [variable].

Example: [specific example]

That is why [practical takeaway].
```

### Thread Hook

```text
I reviewed [number] [industry] sites/accounts/calls.

The winners did not have better branding.

They had better [specific operational behavior].

Here are the [number] patterns:
```

### Poll

```text
What is costing you more leads right now?

- Missed calls
- Slow follow-up
- Weak offer
- No proof
```

---

## Reply Strategy

Replies are first-class content.

Use replies to:

- Add a specific example under a relevant post.
- Correct an incomplete claim without sounding performative.
- Add a useful number, source, or operating detail.
- Ask a sharper follow-up question.
- Build familiarity with niche creators, local accounts, reporters, partners, customers, and category peers.

Do not post empty replies like "great post." Do not use automated keyword-search replies. Reply within the first hour to comments on owned posts when possible.

---

## Threads

Use threads only when the idea needs sequence or depth:

- teardown
- audit
- before/after
- lessons learned
- framework
- event recap
- market memo

Thread rules:

1. Make the first post stand alone.
2. Put one idea in each post.
3. Use specific examples in at least half the posts.
4. Use native screenshots or charts when they prove the claim.
5. Put external links at the end or in a reply when reach matters.
6. Avoid threads where every post depends on the previous post to make sense.

---

## Articles and Long-Form Posts

Use native long-form only when the reader benefits from depth:

- founder memo
- market thesis
- audit teardown
- original research
- policy or category explainer
- checklist or playbook

Long-form rules:

1. Start with a post-length hook before the long body.
2. Put the core claim in the first two lines.
3. Break the piece into scannable sections.
4. Include concrete examples, screenshots, or source references.
5. Use a short follow-up post or thread to distribute the long-form piece.
6. Avoid turning a weak short post into a long post. Length does not create authority.

---

## Media

Use media when it proves the claim:

- screenshots of workflows, search results, dashboards, calls, or reviews
- annotated charts
- short clips around 15 seconds
- before/after process evidence
- captions for sound-off video
- 9:16 vertical video when the asset may later be promoted or used in the immersive video surface

Keep images low-text and readable on mobile. Avoid decorative images that do not add evidence.

Video defaults:

- Put motion or the strongest proof in the first 3 seconds.
- Keep most organic/paid candidates around 15 seconds.
- Use captions when there is spoken-word audio.
- Prefer 9:16 for vertical video candidates.
- Keep logo/product presence visible but not obnoxious.

---

## Spaces and Live Formats

Use Spaces when live conversation is the asset:

- founder AMA
- customer/community Q&A
- partner panel
- event commentary
- launch room
- local issue or breaking-news discussion
- post-webinar discussion

Spaces rules:

1. Schedule the Space and post the card in advance.
2. Name the Space with the audience and outcome, not a vague topic.
3. Use 2-4 prepared prompts to avoid dead air.
4. Record when reuse matters, and tell speakers/listeners that it is recorded.
5. Clip or summarize the best moments into follow-up posts.
6. Use Spaces as a relationship and authority surface, not a cold conversion surface.

---

## Links

Link posts can work, but link-only posts are weak default X content. They pull the user away from the conversation and often earn less engagement.

Default rules:

1. Put the value in the native post first.
2. Use a summary, screenshot, chart, or thread before the link.
3. Put the link in the final thread post, a self-reply, or the profile when reach matters.
4. Track link posts separately from native posts in analytics.

Confidence: medium. X does not publish a stable "link penalty" rule, but publisher analysis and platform behavior support treating links as a distribution risk.

---

## Community Notes, Labels, and Trust

Community Notes can appear when contributors from different points of view rate a note as helpful. X says Community Notes do not themselves enforce rules, represent X's viewpoint, or trigger removals, labels, or reduced distribution.

That does not mean notes are harmless for marketing. A note can damage trust, lower conversion, and create reputational drag.

Rules:

1. Source claims before posting, especially numbers, comparisons, regulated claims, and breaking-news commentary.
2. If a post receives a Community Note, review the claim and source chain before amplifying it further.
3. Do not delete-and-repost the same claim without fixing the underlying issue.
4. Civic Integrity labels are different from Community Notes. X says civic labels can restrict visibility, remove posts from timelines, limit engagements, and downrank replies.

---

## Hashtags

X's business guidance says to avoid hashtags in post copy. The harness default is **zero hashtags** for X.

Use 1-2 hashtags only when:

- the hashtag is the official event or conference tag
- the hashtag is required for a contest or campaign
- the hashtag is how the audience searches the topic

Never overload posts with hashtags.

---

## B2B Use Cases

Best fit:

- founder point of view
- category education
- teardown threads
- analyst-style commentary
- live industry or event commentary
- partner/customer amplification
- recruiting and credibility building

For B2B tech, make replies part of the calendar. Public expertise under relevant conversations often beats another brand announcement.

---

## Local-Service Use Cases

Best fit:

- service-area alerts
- "what we fixed today" posts
- review and objection mining
- local event commentary
- fast-response proof
- before/after process stories
- customer support and public FAQ

X is usually not the primary acquisition channel for most local services unless the audience is civic, media, tech, real estate, hospitality, government-adjacent, crisis-driven, or availability-driven. Use it as reputation, responsiveness, and community proof, then measure assisted leads.

---

## Automation and Compliance Rules

Load `harness/references/x-organic-posting-rules.md` before scheduling, automating, or preparing posts that may be promoted.

Hard stops:

- no automated posting, replying, DMing, following, unfollowing, deleting, or hashtagging without express consent
- no duplicate or substantially similar posts across one or many accounts
- no automated trend-jacking
- no unsolicited bulk automated replies, mentions, or DMs
- no keyword-search auto-reply campaigns without opt-in
- no automated likes or automated hiding replies
- no impersonation, confusing affiliation, misleading links, phishing, scams, or deceptive redirects
- no unlabeled sensitive media
- no unsupported claims with numbers, outcomes, savings, earnings, health benefits, rankings, or timelines

Route to human/platform/legal review:

- AI-powered automated reply bots
- brand auto-response campaigns
- paid promotion candidates
- contests, incentives, affiliate, or creator posts
- political, civic, financial, crypto, health, gambling, alcohol, tobacco, cannabis, weight-loss, adult, or sensitive-event content

---

## Metrics

Track X content by format:

- impressions
- replies
- reposts
- quote reposts
- likes
- profile clicks
- follows
- link clicks
- video retention
- completion rate
- Article clicks or reads where available
- Space attendance, replay listens, clips, and follow-up post engagement
- blocks, mutes, reports, and negative replies when visible

Review after 30 days. Promote patterns that create conversation quality, profile clicks, and assisted leads. Kill patterns that create impressions without useful downstream behavior.

Testing loop:

1. Tag each post with `format`, `angle`, `audience`, `asset_type`, `link_strategy`, and `cta_type`.
2. Compare posts within the same format before declaring a winner.
3. Separate link posts from native posts.
4. Separate replies from original posts.
5. Track negative feedback as a quality signal, not only a moderation issue.

---

## Anti-Patterns

- external link as the whole post
- overloaded hashtag blocks
- posting only announcements
- reposting without commentary
- generic motivational filler
- engagement bait CTAs like "agree?"
- all-caps copy
- repeated posts with small wording changes
- AI-polished but unspecific voice
- product pitches above 20% of the calendar
- exact algorithm-weight claims treated as fact
