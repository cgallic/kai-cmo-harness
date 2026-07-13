# YouTube Channel Guide

> **Use when:** Building a YouTube presence, creating video content for SEO, or running YouTube ads.
>
> **Distribution hub:** `playbooks/growth-distribution-engine.md` — where YouTube fits in channel selection and the B2B/B2C build order.

Primary references:
- YouTube Community Guidelines: https://support.google.com/youtube/answer/9288567?hl=en
- Recommendations on YouTube: https://www.youtube.com/howyoutubeworks/recommendations/
- YouTube recommendation system help: https://support.google.com/youtube/answer/16533387?hl=en
- Search & discovery tips: https://support.google.com/youtube/answer/11914225?hl=en
- YouTube organic rules: `harness/references/youtube-organic-posting-rules.md`
- Social automation rules: `harness/references/social-automation-rules.md`

---

## Why YouTube in 2026

- **2nd largest search engine** — 3B+ searches/month
- **Evergreen content** — videos rank for years (unlike social posts)
- **Google integration** — YouTube videos appear in Google search, AI Overviews
- **Highest trust** — video builds more trust than text or images
- **Monetization** — ads revenue, lead gen, product sales all work

---

## Channel Strategy

### Content Pillars for Business YouTube

| Pillar | % of Content | Examples | Goal |
|--------|-------------|---------|------|
| **How-To / Tutorial** | 40% | "How to set up AI receptionist" | Search traffic, authority |
| **Industry Insights** | 25% | "Why law firms are switching to AI" | Thought leadership |
| **Customer Stories** | 15% | "How Acme Law saves 12 hours/week" | Trust, conversion |
| **Product Updates** | 10% | "New feature: call routing" | Existing users, retention |
| **Behind the Scenes** | 10% | "How we built our AI" | Brand, personality |

### Posting Cadence

| Stage | Frequency | Focus |
|-------|-----------|-------|
| Launch (month 1-3) | 1x/week minimum | Consistency over quality |
| Growth (month 3-12) | 2x/week | Quality + consistency |
| Scale (year 2+) | 3-5x/week (mix of long + Shorts) | Volume + quality |

---

## Video Production

### Title Formula

```
[Keyword phrase] + [Hook/benefit] + [Year if relevant]

GOOD:
  "AI Receptionists: How Law Firms Save 12 Hours/Week (2026)"
  "I Tested 5 Answering Services — Here's the Best One"
  "Stop Losing Clients to Voicemail (Do This Instead)"

BAD:
  "Our Amazing New Product!"
  "KaiCalls Overview"
  "Weekly Update #47"
```

### Thumbnail Rules

1. **Face with emotion** — surprise, excitement, concern (not neutral)
2. **3 elements max** — face + text + one visual element
3. **Bold, high-contrast text** — 4-6 words max, readable at 120x68px
4. **Bright colors** — stand out in a feed of muted thumbnails
5. **No clickbait** — the thumbnail should honestly represent the content
6. **A/B test** — YouTube supports native thumbnail testing

### Script Structure

```
[0-30s]  COLD OPEN
         Start with the payoff or a hook — NOT "Hey guys, welcome to my channel"
         Example: "This one change saved our client $4,000/month on missed calls"

[30s-2m] SETUP
         Context: who this is for, what you'll cover, why it matters
         Promise: "By the end of this video, you'll know exactly how to..."
         Keep it tight — viewers are deciding whether to stay

[2m-end] CONTENT (broken into chapters)
         Chapter 1: First key point
           - Claim → Evidence → Example → Transition
         Chapter 2: Second key point
           - Same structure
         Chapter 3+: Additional points

         Re-hook every 3-4 minutes:
           "Now here's where it gets interesting..."
           "But there's a catch that most people miss..."

[Last 2m] OUTRO
          One-sentence summary
          Single CTA: "Subscribe" or "Watch this next video"
          End screen: 2 video cards + subscribe button
```

### Retention Optimization

| Tactic | Impact | Implementation |
|--------|--------|---------------|
| Pattern interrupts | +15-25% retention | B-roll, graphics, camera angle changes every 30-60s |
| Open loops | +10-20% retention | "I'll reveal the results in a minute, but first..." |
| Chapters/timestamps | +engagement | Add to description, improves search + retention |
| Progress indicators | +retention | "Point 3 of 5" — viewers know how far along they are |
| Curiosity gaps | +click-through | Tease upcoming content in the middle of the video |

---

## YouTube SEO

Use official YouTube help pages for policy or ranking claims. The factor ordering below is an operating heuristic, not a published weight table. YouTube's current recommendation and search/discovery docs emphasize audience fit, viewer satisfaction, content performance, topic interest, competition, and seasonality over any single CTR hack. Sources: https://support.google.com/youtube/answer/16533387?hl=en and https://support.google.com/youtube/answer/11914225?co=YOUTUBE._YTVideoType%3Dvideo&hl=en (accessed 2026-07-13).

### Ranking Factors (by importance)

1. **Click-through rate (CTR)** — title + thumbnail determine this
2. **Watch time** — total minutes watched (not just views)
3. **Retention** — % of video watched (high retention = promoted more)
4. **Engagement** — likes, comments, shares, saves
5. **Keywords** — title, description, spoken words, captions; tags have a minor role, mainly for misspellings
6. **Freshness** — new videos get a promotion boost for 48-72 hours

YouTube's official search/discovery guidance also calls out **topic interest**, **competition**, and **seasonality** as external reach factors. Compare against audience context before concluding a format or thumbnail failed.

### SEO Checklist

- [ ] Primary keyword in title (front-loaded)
- [ ] Keyword in first 2 lines of description
- [ ] Description 200+ words with natural keyword usage
- [ ] Tags used only for misspellings, alternate names, or disambiguation
- [ ] Chapters with timestamps in description
- [ ] Cards linking to related videos
- [ ] End screen with 2 video suggestions + subscribe
- [ ] Custom thumbnail (never use auto-generated)
- [ ] Closed captions reviewed for accuracy (YouTube auto-captions help SEO)

---

## YouTube Shorts

### When to Use Shorts vs Long-Form

| Shorts (< 60s) | Long-Form (5-20 min) |
|----------------|---------------------|
| Subscriber growth | Watch time + authority |
| Clips from long-form | Original in-depth content |
| Trending topics | Evergreen SEO content |
| Repurposed TikToks/Reels | Product tutorials |
| Quick tips | Case studies |

### Shorts Best Practices
- First 1-2 seconds = hook (same as TikTok/Reels)
- Vertical 9:16 format
- Loop-friendly endings (last frame connects to first)
- Text overlays for sound-off viewing
- Hashtag #Shorts in title or description
- Post 3-5 Shorts per week alongside 1-2 long-form videos

---

## Policy and Upload Checks

Before publishing or scheduling YouTube content:

- Load `harness/references/youtube-organic-posting-rules.md`.
- Check Community Guidelines, spam/fake engagement, external links, and advertiser-friendly guidance.
- Set paid promotion, made-for-kids, age restriction, AI/altered content, license, captions, and remix fields intentionally.
- If using the API, set the altered/synthetic-media and brand-partner fields intentionally and track quota by method. YouTube's July 2026 revision history adds `brandPartner` for creator-initiated paid partnerships and splits `videos.insert`, `search.list`, and `videos.batchGetStats` into distinct quota buckets. Source: https://developers.google.com/youtube/v3/revision_history (accessed 2026-07-13).
- Do not use artificial views, engagement incentives, repetitive AI batches, or scraped reposting.
- Mark analytics trend breaks when Shorts view counting or API metric definitions change.

---

## YouTube Ads

### Ad Formats

| Format | Length | Skippable? | Best For |
|--------|--------|-----------|----------|
| Skippable In-Stream | 12s-3min+ | After 5s | Awareness, consideration |
| Non-Skippable In-Stream | 15-20s | No | High-impact messaging |
| Bumper Ads | 6s max | No | Brand recall |
| Discovery Ads | N/A | Click to play | Search-based targeting |
| Shorts Ads | 10-60s | Varies | Mobile-first audiences |

### YouTube Ad Script (Skippable In-Stream)

```
[0-5s]  HOOK — must earn the non-skip in 5 seconds
        "If you're a lawyer losing clients to voicemail, watch this."
        (Address viewer directly, name their pain)

[5-15s] PROBLEM + AGITATE
        "The average law firm misses 40% of calls. That's $200K in lost revenue."

[15-25s] SOLUTION
         "KaiCalls AI answers every call in 0.4 seconds, 24/7."
         (Show product in action — screen recording or demo)

[25-30s] PROOF
         "500+ law firms. 99.7% answer rate. 12 hours saved per week."

[30s]    CTA
         "Start your free trial. Link below."
         (Companion banner shows throughout)
```

---

## Analytics & Growth Metrics

### Key Metrics to Track

| Metric | Where to Find | Good | Excellent |
|--------|--------------|------|-----------|
| CTR (impressions → clicks) | YouTube Studio > Reach | 4-6% | 8%+ |
| Average view duration | Studio > Engagement | 40-50% of video length | 60%+ |
| Subscriber conversion rate | Studio > Build audience | 1-3% of viewers | 5%+ |
| Watch time (hours) | Studio > Overview | Growing MoM | — |
| RPM (revenue per mille) | Studio > Revenue | $3-8 | $10+ |

### Growth Milestones

| Milestone | Typical Timeline | Significance |
|-----------|-----------------|-------------|
| 100 subscribers | Month 1-2 | Community tab unlocked |
| 500 subscribers | Month 2-4 | Decent momentum |
| 1,000 subscribers | Month 3-6 | Monetization eligible (+ 4,000 watch hours) |
| 10,000 subscribers | Month 6-18 | YouTube promotes you more aggressively |
| 100,000 subscribers | Year 1-3+ | Silver Play Button, significant authority |
