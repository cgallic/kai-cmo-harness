# TikTok Algorithm Deep Dive

> **Use when:** Optimizing content strategy for TikTok FYP distribution, understanding engagement weighting, or debugging poor video performance.
>
> **Distribution hub:** `playbooks/growth-distribution-engine.md` + `playbooks/b2c-distribution-playbook.md` — where organic TikTok fits the creative-volume flywheel. Feed it with `channels/ai-ugc.md`.

## Quick Reference

Official TikTok help should anchor any policy-sensitive claim. TikTok's July 2026 recommendation article says each surface has its own recommendation system, and that user interactions, content information, and user/device information are weighted differently by surface. For most users, interactions are generally weighted more heavily on For You, Following, Friends, LIVE, and notifications, while Search weighs content-match information more heavily. The numeric thresholds and proxy weights below are benchmark heuristics, not official TikTok doctrine. Source: https://support.tiktok.com/en/using-tiktok/exploring-videos/how-tiktok-recommends-content (accessed 2026-07-13).

- **First 60 minutes** are critical - content half-life is under 1 hour
- **3-second retention** benchmark: many operators treat 65%+ as a useful threshold, but TikTok does not publish this number as an official requirement
- Signal hierarchy benchmark: Rewatch > Completion > Share > Comment > Like is a working heuristic, not a published official weighting
- **Share signal** is the key to breaking out of personalized feed into viral distribution
- Avoid: Watermarks, excessive hashtags (>5), low technical quality

---

## The Algorithm's Core Objective

TikTok's recommendation system maximizes **user watch time and session duration**. Unlike legacy platforms built on social graphs (who you follow), TikTok operates on an **interest graph** (what you engage with). This means:

- Content relevance > Creator popularity
- Zero-follower accounts can go viral
- Every video is independently evaluated
- Distribution is earned through performance, not existing audience

---

## Signal Hierarchy (Engagement Weighting)

The "5-point system" is creator lore, but the **relative hierarchy** has 90%+ analytical confidence:

### Tier 1: Retention Metrics (Highest Weight)

| Signal | Proxy Weight | Why It Matters |
|--------|--------------|----------------|
| **Rewatch/Replay** | ~5 | Definitive proof of content value. Provides 2x completion data. |
| **Watch to Completion** | ~4 | Primary quality signal. 70%+ completion rate triggers distribution expansion. |

These are **passive behavioral signals** - the algorithm trusts what users DO over what they CLICK.

### Tier 2: Distribution Metrics (High Weight)

| Signal | Proxy Weight | Why It Matters |
|--------|--------------|----------------|
| **Share/Send** | ~3 | Highest external validation. Signals content can succeed beyond personalized feed. |
| **Save** | ~3 | Indicates long-term reference value. |

**The Share is the viral unlock.** It's the algorithm's confirmation that content can transcend niche interests and succeed with unconnected users.

### Tier 3: Affirmation Metrics (Lower Weight)

| Signal | Proxy Weight | Why It Matters |
|--------|--------------|----------------|
| **Comment** | ~2 | Provides NLP data for categorization. Higher friction than Like. |
| **Like** | ~1 | Lowest-friction affirmation. Easily saturated. Necessary but insufficient. |

### Negative Signals (Very High Weight)

Negative feedback carries **exponentially higher weight** than low-value positive signals:

- "Not Interested" click
- Skip within first second
- Scroll-away before 3 seconds
- Report/Block

One "Not Interested" likely outweighs multiple Likes in algorithmic impact.

---

## The 3-Second Rule: Sub-Second Decision Matrix

The first 3 seconds determine whether your video gets distributed or dies. Videos achieving 65%+ 3-second retention get **4-7x more impressions**.

### Phase I: Scroll-Stop (0.0 - 0.7 seconds)

**Goal:** Trigger the Orienting Response - stop the muscle-memory scroll

**Tactics:**
- Immediate visual pattern interrupt
- Quick cuts or unexpected movement
- Visual incongruity
- Must work on MUTE (many users watch without sound)

**Failure indicator:** Drop-off at 0.5s = visual interrupt failed

### Phase II: Cognitive Commitment (0.7 - 2.0 seconds)

**Goal:** Deliver clear value proposition - answer "Is this relevant to me?"

**Tactics:**
- Explicit verbal statement or bold claim
- Proof-first hook (show result before method)
- Compelling question
- Clear topic signal

**Failure indicator:** Drop-off at 1.5s = value proposition unclear

### Phase III: Sustained Interest (2.0 - 3.0 seconds)

**Goal:** Create curiosity gap and transition to main content

**Tactics:**
- Introduce structure ("Here are the 3 ways...")
- Tease what's coming
- Start delivering on the promise

**Failure indicator:** Drop-off at 2.5s = failed to create commitment

---

## Time-Decay Model: The First Hour Imperative

TikTok's distribution priority follows **aggressive exponential decay**:

$$N(t) = N_0 \cdot e^{-\lambda t}$$

Where λ is VERY high - content half-life is under 60 minutes.

### Critical Distribution Windows

| Window | What Happens | Success Threshold |
|--------|--------------|-------------------|
| **0-60 min** | Initial test audience (~300 users) | 70%+ completion, 15%+ engagement rate |
| **1-4 hours** | First expansion wave (if passed) | Maintained engagement velocity |
| **4-24 hours** | Broader distribution or death | High EV must offset decaying time factor |
| **24+ hours** | Relevance-only ranking | Only exceptional content survives |

### Pre-Peak Posting Strategy

Post **15-30 minutes BEFORE** your audience's peak activity time:
- Video completes initial test as audience density peaks
- Maximizes engagement velocity during freshness window
- Converts freshness bonus into distribution expansion

---

## FYP Distribution Mechanics

### The Test Pool Mechanism

1. **Initial seed:** Video shown to ~300 random users
2. **Performance evaluation:** Algorithm measures completion, engagement, shares
3. **Gate decision:** Pass = expand to larger pool. Fail = distribution halted.
4. **Expansion tiers:** 300 → 1,000 → 10,000 → 100,000+ (each requires threshold performance)

### The Share as Distribution Accelerator

When test pool generates **unusually high share rate**, the algorithm:
- Interprets this as "external market potential"
- Skips intermediate test pools
- Commits immediately to mass distribution
- This is the empirical "2-3x multiplier" creators observe

**Why shares matter so much:** A share is user endorsement that content will succeed with algorithmically unknown recipients. It bridges interest vectors and enables cross-niche virality.

---

## Suppression Triggers (FYP Ineligibility)

These factors cause algorithmic demotion or distribution restriction:

### Confirmed Triggers

| Trigger | Severity | Why |
|---------|----------|-----|
| **Watermarks from other platforms** | High | Violates content sharing guidelines |
| **Excessive hashtags (>5)** | Medium | Signals spam behavior |
| **Low technical quality** | Medium | Poor completion rates |
| **Misleading captions/CTAs** | High | Policy violation |
| **Unlabeled AI-generated content** | Medium | Authenticity violation |
| **Duplicate content** | High | Spam signal |
| **Sensitive content flags** | Variable | Multimodal AI detection |

### Multimodal Content Filtering

ByteDance's filtering system (Patent US20170289624A1) analyzes:
- **Visual:** Image/video content
- **Audio:** Speech and sounds
- **Text:** Captions and overlays

All three modalities are fused for a combined confidence score. High scores trigger automatic review or FYP ineligibility.

---

## Optimization Strategies

### Retention Optimization (Tier 1 Focus)

1. **Hook in first 0.7 seconds** - visual interrupt that works on mute
2. **Deliver value proposition by 2 seconds**
3. **Create seamless loops** - shorter videos more likely to rewatch
4. **Use pattern interrupts throughout** - re-earn attention every 3-7 seconds
5. **Front-load the payoff** - proof before process

### Distribution Optimization (Tier 2 Focus)

1. **Create share-worthy content:**
   - Highly relatable humor
   - Actionable advice
   - Emotional resonance
   - Niche utility

2. **Subtle CTAs for high-value actions:**
   - "Save this for later"
   - "Send this to someone who..."
   - NOT "Like and follow"

### Technical Quality Requirements

- **Lighting:** Subject well-lit, no shadows/grain
- **Audio:** Clear and crisp (use lavalier mic)
- **Resolution:** HD minimum
- **Safe zones:** Text not over UI elements

---

## A/B Testing Protocol

Since weights are dynamic and personalized, systematic testing is essential:

### Variables to Test

| Variable | How to Test |
|----------|-------------|
| **Hook (0-3s)** | Film 3-4 variations, swap and repost |
| **Video length** | Same content at 15s, 30s, 60s |
| **CTA type** | Share vs Save vs Comment prompt |
| **Posting time** | Same content at different hours |
| **Hashtag strategy** | Niche vs broad vs trending |

### Metrics to Track

- 3-second retention rate
- Exact drop-off points (TikTok Studio)
- Completion rate
- Share/Save ratio
- Time to reach view thresholds

---

## Iteration Strategy: Finding and Scaling Winners

The winning strategy is **iteration, not diversification**. Most creators fail because they post different content hoping something hits. Winners find what works and iterate relentlessly.

### The Iteration Flywheel

```
Week 1: Post 10 variations across categories (financial tips, trading, crypto, etc.)
         ↓
Week 2: Identify top performer (highest views)
         ↓
Week 3: Create 5 variations of THAT winner (same message, slight tweaks)
         ↓
Week 4: Repeat until hitting 100k views
         ↓
Then: Find next category winner, repeat process
```

### Why Iteration Beats Diversification

- **Diversification:** 10 different topics = 10 independent shots, no compounding
- **Iteration:** 10 variations of a winner = algorithm learns what works, compounds success

**Key insight:** Once a format works, iterate the idea honestly instead of inventing a new format every time.

### Screenshot Feedback Loop

Use AI to accelerate iteration:

1. **Screenshot TikTok grid** (mobile view shows thumbnails + view counts)
2. **Feed to ChatGPT/Claude:** "This is yesterday's performance. Give me 10 new posts. 50% should iterate on the winners."
3. **AI reads:** Text on thumbnails AND view counts
4. **Result:** AI learns which messaging resonates without explicit explanation

This creates a compounding learning loop - each batch is informed by previous performance.

### Duplicate-Evasion Block

Do not post the same clip across multiple accounts with speed, brightness, crop, or length tweaks to disguise duplication. Treat that as platform-integrity risk, not an optimization tactic.

Safe iteration means changing the creative idea for a real viewer reason:
- New hook or first frame
- New example or proof point
- New audience/problem framing
- New edit that changes pacing or comprehension
- New caption/disclosure because the commercial context changed

### CTA Placement Strategy

Two CTAs per video, different purposes:

| Location | CTA | Purpose |
|----------|-----|---------|
| **In video (text overlay)** | "Follow for more" | Drives follows directly |
| **In caption** | "Comment below for [X]" | Drives engagement + enables DM outreach |

**DM Funnel:** Anyone who comments can receive a DM. "Comment for X" creates permission-based lead generation even before you have 1,000 followers (when link in bio unlocks)

---

## Checklist

### Pre-Posting
- [ ] Hook works on MUTE (visual-first)
- [ ] Value proposition clear by 2 seconds
- [ ] Technical quality meets standards (lighting, audio)
- [ ] No watermarks from other platforms
- [ ] No duplicate-content evasion or cross-account manipulation
- [ ] Branded content, AI content, and commercial music rights checked
- [ ] `harness/references/tiktok-organic-posting-rules.md` loaded
- [ ] 5 or fewer specific hashtags
- [ ] Posting 15-30 min before audience peak

### Content Structure
- [ ] Pattern interrupt in first 0.7 seconds
- [ ] Clear value proposition by 2 seconds
- [ ] Curiosity gap before 3 seconds
- [ ] Visual/audio changes every 3-7 seconds (for longer content)
- [ ] Designed for looping (if short)

### Optimization
- [ ] Multiple hook variations filmed
- [ ] Share-worthy element included
- [ ] Subtle high-value CTA (save/share, not like)
- [ ] No suppression triggers present

---

## Source Research Files

Detailed research available in `archive/`:
- TikTok Engagement Algorithm Research.md
- TikTok Recommendation Weight Research.md
- TikTok's 3-Second Hook Research.md
- TikTok Algorithm_ Time-Decay Analysis.md
- TikTok Content Suppression Research.md
- ByteDance Monolith System Research.md
- ByteDance Patent Verification And Analysis.md
