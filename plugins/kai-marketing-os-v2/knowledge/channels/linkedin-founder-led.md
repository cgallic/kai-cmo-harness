# LinkedIn Organic (Founder-Led B2B)

> **Use when:** Building B2B pipeline through personal profiles (founder + team), company pages, and feed-native organic posting. This is the full organic motion — feed posts, the algorithm, founder-led growth, comments-as-distribution, DMs, and turning attention into demos. For long-form articles only, use `channels/linkedin-articles.md`.

---

## Why This Channel for 0→$5M ARR

LinkedIn organic is one of the highest-ROI distribution channels for B2B from **$0 to roughly $5M ARR**. The reason is structural: your buyers scroll the feed daily, the cost is time not spend, and a founder voice converts attention into trust faster than any ad. Founder-led distribution compounds — every post grows the audience that sees the next.

Treat this as the **organic complement to outbound and paid**. Pair it with `channels/ai-outbound.md` for the DM/email motion, `playbooks/b2b-distribution-playbook.md` for cross-channel sequencing, and `playbooks/growth-distribution-engine.md` for the wider engine.

**Scope split (read this first):**

| You want | Go to |
|----------|-------|
| Feed posts, founder brand, comments, DMs, pipeline | **This file** |
| Long-form articles (1,200-2,000 words, Google-indexed) | `channels/linkedin-articles.md` |
| The real feed ranking architecture (research) | `frameworks/aeo-ai-search/linkedin-ai-systems-deep-dive.md` |
| Pre-publish QA against AI-slop suppression | `checklists/linkedin-ai-content-detection-and-feed-checklist.md` |
| X/Twitter (different platform, similar reply motion) | `channels/x-twitter.md` |

---

## The 2026 Feed Algorithm

Do not write for a mythical 150B-parameter ranker. The production feed is a **retrieval-then-ranking cascade**, per `frameworks/aeo-ai-search/linkedin-ai-systems-deep-dive.md`:

1. **L0 candidate generation** — a fine-tuned LLaMA-3 3B dual encoder retrieves candidate posts by semantic fit.
2. **L1 light ranking** — fast gradient-boosted calibration trims the set.
3. **L2 rich ranking** — Feed-SR, a compact decoder-only sequential recommender, scores for predicted dwell and meaningful interaction.
4. **Re-ranking** — LiGR setwise attention, LiFT fairness, then policy/business filtering.

The research packet's high-confidence correction: LinkedIn **evaluated the monolithic LLM ranker (360Brew) and rejected it for feed ranking** because numeric features lost precision when verbalized and network signals degraded as text. Write for **retrieval + semantic relevance + dwell**, not for first-hour likes.

### What the feed rewards

| Signal | Why it matters | What to do |
|--------|----------------|------------|
| **Semantic relevance** | Content routes by topic fit, not just who follows you | Anchor each post to one clear topic/entity cluster |
| **Dwell time** | Feed-SR optimizes time-spent | Write posts worth reading top to bottom; one idea, real specifics |
| **Saves** | Research cites saves as a **stronger reach signal than likes** | Add one save-worthy artifact: checklist, table, exact steps |
| **Meaningful comments** | Multi-sentence replies > "great post" | Ask a real question; reply to every early comment |
| **Delayed engagement** | 24-72h interaction is valued, not just golden-hour | Post evergreen angles, not only hot takes |
| **"Knowledge / advice" classification** | LinkedIn explicitly surfaces helpful expertise | Teach a repeatable thing; show the mechanism |

### What throttles reach

| Suppressor | Severity | Fix |
|------------|----------|-----|
| **Outbound links in post body** | High — directional reach drop often cited at **25-50%** | Put the link in the **first comment**; tell readers "link in comments" |
| **Engagement-bait** ("comment YES for the PDF") | High | Ask a genuine question instead; let saves do the work |
| **AI-slop phrasing / uniform structure** | High — distribution suppression more common than removal | Vary sentence rhythm; show human judgment early |
| **Pod / engagement-ring velocity patterns** | High — detectable, can throttle the account | Earn comments organically (see Comments section) |
| **High impressions, low dwell** (attention-bait video) | Medium | Make the first 3 seconds and first 2 lines deliver |
| **Broad thought-leadership with no proof** | Medium | Name a number, a system, a date, a workflow |

> **Anti-AI-slop note:** LinkedIn suppresses *generic* AI content, not AI assistance. Run every draft through `checklists/linkedin-ai-content-detection-and-feed-checklist.md`. Show what changed your mind, name the false narrative, give a decision rule.

### The golden hour

The **first 60-90 minutes** still shape distribution — early dwell and meaningful comments tell the ranker the post is worth expanding. Post when your audience is active, then stay in the comments for an hour. Do not chase the golden hour with pods; chase it with a strong hook and fast, real replies.

---

## Founder-Led vs Company Page

Personal profiles outperform company pages on reach by a wide margin — directional **5-10x more reach per follower** is the common benchmark. People follow people. The feed routes founder posts through human-to-human semantic relevance; pages read as broadcast.

| Dimension | Personal Profile (founder/team) | Company Page |
|-----------|--------------------------------|--------------|
| **Organic reach** | High (5-10x page, directional) | Low without spend |
| **Trust** | High — a face and a voice | Medium — institutional |
| **Best use** | Pipeline, expert authority, recruiting | Proof, social proof hub, ad landing, employer brand |
| **Comments** | People reply to people | People rarely reply to logos |

**The distribution-node model.** Make the founder the primary distribution node for the first $1-2M ARR. The founder's profile *is* the channel. The company page becomes the credibility backstop: case studies, product news, careers, a place ad clicks land. Do not invert this — a polished page with no founder voice is a channel that does not exist.

### Team-of-creators model

Past ~$1M ARR, distribution should not depend on one person. Build a **team of creators**: the **founder** (vision, contrarian takes, build-in-public), **execs/leaders** (domain depth — sales lead on sales), and **ICs/CSMs** (tactical wins, customer love).

**Amplification done right:** notify the team on publish, ask for *real* comments that add a point, let people reshare with their own framing. Do **not** mandate identical likes within 5 minutes — that is a pod pattern the system detects. Five authentic comments beat fifty coordinated likes.

---

## Content Formats

| Format | What it does best | Reach pattern | Effort |
|--------|-------------------|---------------|--------|
| **Text post** | Insight, story, hot take, build-in-public | High, fast | Low |
| **Document / carousel (PDF)** | Save-heavy teaching; frameworks, teardowns | High dwell + saves | Medium |
| **Native video** | Face-to-camera trust, demos, talks | High if early dwell holds | High |
| **Poll** | Cheap reach + audience research | High impressions, low depth | Low |
| **Image post** | Data viz, screenshots, quote cards | Medium-high | Low-Med |
| **Long-form article** | Evergreen, Google-indexed authority | Slow, durable | High — see `channels/linkedin-articles.md` |

### Format by goal

| Goal | Use | Why |
|------|-----|-----|
| Fast reach + audience growth | Text post / poll | Lowest friction, feed-native |
| Saves + bookmarkable authority | Document carousel | Save signal compounds reach |
| Trust + face recognition | Native video | Humans buy from humans |
| Pipeline / demo intent | Text post → comment link → DM | Keeps reach on-platform |
| Durable SEO + deep proof | Article (separate file) | Indexed, lives on profile |

**Carousel rules:** 8-12 slides, one idea per slide, big legible type, a cover slide that works as a standalone hook, a final slide with a soft CTA. Carousels are the single most save-efficient format on LinkedIn.

**Native video rules:** hook in the first 3 seconds, add captions (most watch muted), keep it 30-90 seconds for feed, upload natively — never link to YouTube in the body.

---

## Hook + Post Structure

The feed shows only the **first 2 lines (~200-210 characters)** before "see more." Those two lines decide whether anyone reads the rest, and the click-to-expand is an early dwell signal. Win the first two lines or nothing else matters.

### Structure rules

1. **Open with the hook** — no warm-up, no "I've been thinking about...".
2. **Break a line after the hook** — whitespace pulls the eye down past "see more".
3. **One idea per post** — single takeaway; split anything bigger into a series.
4. **Short lines** — 1-2 sentences per paragraph; mobile reads vertically.
5. **Land the payoff** — give the actual answer, do not tease it for the comments.
6. **Vary rhythm** — avoid uniform paragraph lengths; that reads as AI-slop.
7. **End with a real question** — invite a meaningful comment, not "thoughts?".

### Hook templates

```
[CONTRARIAN]
Most B2B founders post on LinkedIn wrong.

They optimize for likes. The algorithm rewards dwell and saves.

[DATA / RESULT]
We tested 40 LinkedIn hooks over 90 days.

The top 5 had one thing in common — and it wasn't the topic.

[STORY / VULNERABILITY]
I posted every weekday for 6 months and got 200 followers.

Then I changed one thing and added 4,000 in 60 days.

[BUILD IN PUBLIC]
We're at $1.2M ARR with zero paid ads.

Here's the exact LinkedIn motion that got us there:

[PROBLEM → PROMISE]
Your demo pipeline is dry because your posts ask for nothing — or ask for everything.

Here's the in-between that actually books calls:

[NAMED-MECHANISM (anti-slop, retrieval-friendly)]
LinkedIn rejected its own 150B model for feed ranking.

What it uses instead — Feed-SR — changes how you should write every post:
```

### Post skeleton

```
[Hook line 1 — claim / stat / tension]
[Hook line 2 — the stakes or the promise]
        ← line break, before "see more"
[Context: 1-2 short lines on why this matters now]

[The idea, delivered. The actual answer, bolded once.]

[Proof: a number, an example, a named tool/system, a workflow]

[Decision rule: "Do X if Y." — what the reader does next]

[One real question to the reader]

(link, if any, goes in the FIRST COMMENT)
```

---

## Content Pillars + Weekly Cadence

Pick **3-4 pillars** and rotate them. Pillars keep you on-topic for semantic retrieval and keep the feed from typecasting you as one-note.

| Pillar | Purpose | Example angle |
|--------|---------|---------------|
| **Expertise / how-to** | Authority + saves | "The 5-step pipeline review we run every Friday" |
| **Contrarian / POV** | Reach + memorability | "Cold outreach isn't dead — your targeting is" |
| **Build-in-public / metrics** | Trust + relatability | "Why we killed a feature at $900K ARR" |
| **Customer / proof** | Bottom-funnel trust | "How a 12-person team cut response time 60%" |
| **Personal / behind-the-scenes** | Humanize the node | A hard week, a hire, a lesson |

### Founder weekly calendar (4-5 posts/week)

| Day | Pillar | Format |
|-----|--------|--------|
| Mon | Expertise / how-to | Text or carousel |
| Tue | Contrarian / POV | Text |
| Wed | Build-in-public / metrics | Text or image (data) |
| Thu | Customer / proof | Text or video |
| Fri | Personal / lighter | Text or video |
| Sat/Sun | Optional | Reshare a winner with new framing |

**Daily, non-negotiable:** 10-20 meaningful comments on others' posts (see next section). Commenting is not optional polish — it is half the growth engine.

### Posting time — the honest caveat

Common guidance: **Tuesday-Thursday, 8-10 AM in your audience's main timezone**. That is a starting point, not a law.

**Consistency beats timing.** Posting 5 days a week at a "wrong" time outperforms posting twice a month at the "perfect" time. The algorithm rewards a steady supply of dwell. Find your real best window from your own analytics after 20-30 posts, then hold it.

---

## Comments as Distribution

Strategic commenting is the fastest way to grow from zero. Your comment on a 50,000-follower account gets seen by **their** audience — borrowed reach, no ad spend.

### The reply-to-grow motion

1. **Pick 15-25 target accounts** — bigger creators and prospects in your niche.
2. **Turn on notifications** for them; comment within the first **15-30 minutes** of their post.
3. **Add a real point** — a counter-angle, a number, a specific example, a relevant story.
4. **Comment 10-20 times daily.** Their readers click your profile → you grow.
5. **Reply to replies** on your own posts fast; threaded conversation deepens dwell.

### Meaningful-comment standard

```
WEAK (ignored, sometimes flagged as spam):
"Great post! 🔥 So true."

STRONG (earns profile clicks):
"This matches what we saw — but the saves signal mattered more than
comment volume for us. We doubled reach by switching from polls to
carousels, same posting cadence. Did topic consistency move your
retrieval, or was it pure dwell?"
```

### Why automated pods and engagement rings are risky

Pods (coordinated like/comment groups) and auto-engagement bots create **velocity patterns the cascade detects** — synchronized timing, the same accounts on every post, comment depth that doesn't match reach. Per the research, the system can **suppress distribution or restrict the account**, and recovery is slow and opaque.

Do **not** join automated pods/rings, run auto-comment or auto-like bots, or buy comments, likes, or followers. Earn comments by writing posts worth replying to and commenting generously yourself. That signal is indistinguishable from "good content" because it *is* good content — a reach decision and a ToS decision (see Compliance).

---

## Profile as Landing Page

A strong post sends a stranger to your profile, which must convert them in 5 seconds. Treat it as a **landing page**, not a résumé.

| Element | Do this | Anti-pattern |
|---------|---------|--------------|
| **Headline** | Outcome you deliver + who for: "I help B2B founders turn LinkedIn into pipeline" | "CEO @ Company" |
| **Banner** | One-line value prop + proof + soft CTA | Stock skyline image |
| **Profile photo** | Clear face, eye contact, simple background | Logo or group photo |
| **About** | Hook → who you help → how → proof → CTA, in first-person | Third-person corporate bio |
| **Featured section** | Best post, lead magnet, booking link, case study | Empty, or one stale link |
| **Experience** | Phrased as outcomes, keyword-rich for search | Job-description copy |
| **CTA** | One clear next step — book a call or grab the resource | Five competing links |

**Lead capture:** put a **booking link or lead magnet** in Featured and in the banner. Keep links *out of post bodies* (reach throttle) and *in the profile/first comment* instead. The profile is where the link lives without a reach penalty.

---

## DMs + Social Selling

DMs convert organic attention into conversations — when done as outreach, not as ambush. The dominant anti-pattern is the **pitch-slap**: connect, then immediately sell. It kills trust and trains people to ignore you.


### The right sequence

```
1. CONNECT  — personalized note referencing their work or a shared context
              (or connect off the back of a real comment exchange)
2. VALUE    — engage with their content; share a resource with no ask
3. SIGNAL   — they engage back / view your profile / reply to a post
4. SOFT CTA — only now: "Curious how you're handling X — worth a quick chat?"
```

### Comment-to-DM play

The warmest DM follows a real interaction. When someone leaves a meaningful comment, reply publicly, then DM: *"Loved your point on X — we just shipped something on that, happy to share the teardown if useful."* No pitch. Value first.

### DM template (warm, post-engagement)

```
Hey [Name] — your comment on [topic] was sharp, especially the bit
about [specific].

We put together a [1-page teardown / checklist] on exactly that.
Want me to send it over? No pitch, genuinely useful for [their goal].
```

### Newsletter on LinkedIn

A LinkedIn **newsletter** notifies all subscribers on publish — a recurring reach spike and a list you own on-platform. Use it for your deepest pillar content (often cross-posted from articles — see `channels/linkedin-articles.md`). Subscribers become a warm DM and demo audience over time.

### The content → DM → call funnel

```
POST (feed reach)
  → PROFILE VISIT (profile-as-landing-page converts)
    → CONNECT / FOLLOW
      → MEANINGFUL COMMENT or DM (value-first)
        → SOFT CTA
          → CALL / DEMO
```

For the systematized outbound version of this funnel, see `channels/ai-outbound.md`.

---

## Turning Organic into Pipeline

Attention is not pipeline until you track and route it. Build the path from post to demo deliberately.

### Attribution path

```
Post → Profile visit → Featured link / booking link → Site → Demo booked
```

| Signal | Where to find it | Play |
|--------|------------------|------|
| **Who viewed your profile** | LinkedIn "Who viewed" (richer with Premium/Sales Nav) | DM warm viewers with value, not a pitch |
| **Post engagers** | Post analytics → reactions/comments list | Note ICP-fit names; engage their content next |
| **Comment intent** | High-signal comments asking "how?" | Comment-to-DM play |
| **Booking-link source** | UTM on the link in Featured/comments | Attribute demos back to LinkedIn organic |

### Tracking that actually works

- **UTM every link** in Featured, first comments, and the newsletter (`utm_source=linkedin&utm_medium=organic`).
- **Tag inbound demos** with "heard via LinkedIn" — self-reported attribution catches what UTMs miss.
- **Retarget LinkedIn engagers** with LinkedIn Ads engagement/video-view audiences to close the organic-to-paid loop.
- **Watch leading indicators** monthly: profile views, ICP-fit followers, save rate, comment quality — not vanity likes.

### Directional benchmarks

Treat these as benchmark ranges, not guarantees. Numbers vary by niche, account size, and offer — use your own 30-day baseline as truth.

| Metric | Reasonable range | Strong |
|--------|------------------|--------|
| Post impressions vs followers | 2-5x followers | 10x+ |
| Engagement rate | 2-5% | 8%+ |
| Save rate (carousels) | 1-3% of impressions | 5%+ |
| Profile-visit rate | 1-3% of impressions | 5%+ |
| Follower growth (consistent founder) | 5-15%/month early | 20%+ |

---

## Compliance + Risk

LinkedIn organic is high-trust, which means fake signals do disproportionate damage. Keep it clean.

| Practice | Status | Why |
|----------|--------|-----|
| **Aggressive auto-connect / auto-DM bots** | **Prohibited — ban risk** | Violates LinkedIn User Agreement; triggers restrictions and permanent bans |
| **Automated engagement pods / rings** | **Risky — suppression + ToS** | Detectable velocity patterns; reach throttling and account limits |
| **Bought followers / likes / comments** | **Prohibited** | Fake engagement, against ToS, destroys signal quality |
| **Scraping at scale** | **Prohibited** | Violates ToS; legal and account risk |
| **Manual, value-first DMs** | **Allowed** | This is the channel working as intended |
| **Light scheduling tools** | **Generally fine** | Use reputable schedulers; avoid auto-engagement features |
| **Paid creator amplification** | **Allowed with disclosure** | Disclose any paid relationship per FTC rules — see `harness/references/advertising-compliance.md` |

**Disclosure rule:** any time money changes hands for a post — paid creator, sponsored mention, affiliate — disclose it plainly. No astroturfing, no fake testimonials, no undisclosed endorsements. Authenticity *is* the moat on this channel.

---

## Cold-Start Runbook (Founder, First 30 Days)

For a founder starting from zero followers.

```
WEEK 1 — Foundation
[ ] Rewrite profile as a landing page (headline, banner, about, photo)
[ ] Add booking link + 1 lead magnet to Featured
[ ] Pick 3-4 content pillars
[ ] Build a target list of 20 accounts to comment on
[ ] Write 5 posts in advance from your real expertise

WEEK 2 — Voice + reps
[ ] Post 4-5 times (one idea each, strong 2-line hooks)
[ ] Comment meaningfully 10x/day on the target list
[ ] Reply to every comment on your posts within the first hour
[ ] Ship one document carousel for saves

WEEK 3 — Find what lands
[ ] Keep 4-5 posts/week; double down on the pillar with best dwell/saves
[ ] Start value-first DMs to people who engaged (no pitch)
[ ] Launch a LinkedIn newsletter if you have a deep pillar
[ ] Check analytics: which hook style and format won?

WEEK 4 — Tighten the funnel
[ ] Add UTMs to every profile/comment link
[ ] Run the comment-to-DM play on 5 high-intent commenters
[ ] Note any demos sourced from LinkedIn; tag attribution
[ ] Set a sustainable cadence you can hold for 6 months
```

Expect quiet early weeks. **Consistency beats timing and beats virality.** The compounding starts around the 20-30 post mark.

---

## Scale Runbook (Team Amplification)

Once the founder motion works, distribute the load.

```
[ ] Recruit 3-5 internal creators (execs, sales lead, CSMs)
[ ] Give each a pillar tied to their real expertise
[ ] Set a shared but flexible cadence (no synchronized engagement)
[ ] Create a "new post" channel so the team can add REAL comments
[ ] Cross-pollinate: founder reshares team wins, team reshares founder POV
[ ] Keep the company page as the proof/social-proof hub + ad landing
[ ] Retarget all organic engagers with LinkedIn Ads audiences
[ ] Review monthly: ICP-fit follower growth, demos sourced, save rate
[ ] Promote top-performing posts into articles + newsletter for durability
```

**Guardrail:** scale the *number of authentic voices*, never the *automation of fake engagement*. The moment amplification looks coordinated and mechanical, the cascade reads it as a pod and the whole team's reach suffers.

---

## Quick Reference

| Question | Answer |
|----------|--------|
| Personal or company page? | **Personal** for reach and pipeline; page for proof/ads |
| How many posts/week? | **4-5** for a founder, plus daily comments |
| Best format for saves? | **Document carousel** |
| Where do links go? | **First comment + profile**, never the body |
| Strongest reach signal? | **Saves + dwell + meaningful comments**, not likes |
| Best time to post? | Tue-Thu mornings, but **consistency beats timing** |
| Are pods worth it? | **No** — detectable, throttle/ban risk |
| First DM move? | **Value, never a pitch** |
| Pre-publish QA? | `checklists/linkedin-ai-content-detection-and-feed-checklist.md` |

---

## Related Files

- `channels/linkedin-articles.md` — long-form articles (separate motion)
- `channels/x-twitter.md` — parallel reply-to-grow motion on X
- `frameworks/aeo-ai-search/linkedin-ai-systems-deep-dive.md` — feed ranking research
- `checklists/linkedin-ai-content-detection-and-feed-checklist.md` — pre-publish QA
- `channels/ai-outbound.md` — systematized DM/outbound funnel
- `playbooks/b2b-distribution-playbook.md` — cross-channel sequencing
- `playbooks/growth-distribution-engine.md` — the wider distribution engine
