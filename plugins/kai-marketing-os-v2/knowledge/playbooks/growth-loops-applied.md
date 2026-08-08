# Growth Loops — Applied Playbook

> **Use when:** Designing growth mechanics for a product or service. Not "how do we market" but "how does usage itself create more usage." Combines the Loop Mechanics framework with real-world implementation patterns.
>
> **Read first:** `frameworks/content-copywriting/loop-mechanics.md` for the meta-framework (12 loop types, 7 thinking personas, diagnostic questions).

Sources: [Reforge — Growth Loops are the New Funnels](https://www.reforge.com/blog/growth-loops), [FourWeekMBA — Growth Flywheel Atlas](https://fourweekmba.com/growth-flywheel-atlas/), [Thoughtlytics — Growth Loops Guide](https://www.thoughtlytics.com/newsletter/growth-loops), [PLG Playbook 2026](https://www.news.aakashg.com/p/plg-in-2026)

---

## Why Loops Beat Funnels

Funnels are linear: Awareness → Interest → Desire → Action. Each stage loses people. Nothing feeds back.

Loops are circular: Output of one cycle becomes input of the next. Each cycle makes the next cycle stronger.

```
FUNNEL (linear, leaky):
  1000 visitors → 100 signups → 10 customers → done.
  Next month: start from scratch.

LOOP (circular, compounding):
  100 signups → 30 activate → 10 share artifact →
  artifact reaches 500 people → 50 new signups →
  20 activate → 8 share → ...
  Each cycle compounds.
```

**The core insight from Reforge:** The fastest-growing products are better represented as a system of loops, not funnels. Growth loops are closed systems where the output of one process generates input that can be reinvested.

---

## The 6 Growth Loop Archetypes

### 1. Viral / User-Generated Content Loop

**How it works:** Users create artifacts that are visible to non-users → non-users discover the product through the artifact → some become users → create more artifacts.

**Canonical examples:**
- **Loom:** Record video → share link → viewer sees "made with Loom" → signs up → records their own video
- **Canva:** Create design → share/download → "Made with Canva" watermark → viewer creates their own
- **Notion:** Create template → share publicly → template user discovers Notion → creates their own templates

**Blueprint:**
```
USER creates [ARTIFACT]
  → ARTIFACT shared/published to [CHANNEL]
  → NON-USER discovers artifact
  → NON-USER has [AHA MOMENT] ("I could make one too")
  → NON-USER signs up → becomes USER
  → Repeat
```

**The key diagnostic question:** What artifact does your user create that naturally travels outside your product?

**Implementation checklist:**
- [ ] Users create something shareable as part of normal use (not as a favor)
- [ ] Shared artifact carries product branding or attribution
- [ ] Viewing the artifact doesn't require an account
- [ ] Viewer can clearly see how to create their own
- [ ] One-click path from viewer to creator

### 2. Invitation / Network Loop

**How it works:** Product is more valuable with more people → users invite others to increase their own value → invitees find value → invite more.

**Canonical examples:**
- **Slack Connect:** Invite external contacts to shared channels → they discover Slack → their company adopts it
- **Dropbox:** Refer a friend → both get more storage → friend refers their friends
- **Figma:** Share design file → collaborator joins → collaborator brings it to their team

**Blueprint:**
```
USER gets value from product
  → Value increases with [MORE PARTICIPANTS]
  → USER invites [CONTACT] (selfish motive: better experience)
  → CONTACT joins → gets value → invites their own contacts
  → Network density increases → value increases for everyone
  → Repeat
```

**The key diagnostic question:** Does the product get better when another person joins? (Not "would you recommend us" — does the product itself improve?)

**Implementation checklist:**
- [ ] Clear reason why inviting helps the inviter (not just the invitee)
- [ ] Invitation is embedded in natural workflow (not a separate "invite" page)
- [ ] Invitee gets immediate value (no empty experience)
- [ ] Network effects kick in at a reachable threshold (not "works great with 1000 users")

### 3. Content / SEO Loop

**How it works:** Content ranks in search → attracts visitors → some become users → user data/behavior creates more content → more content ranks.

**Canonical examples:**
- **HubSpot:** Blog content ranks → visitors read → some become leads → leads create data that informs more content → more content ranks
- **Zapier:** Integration pages rank for "[App A] + [App B]" → users find Zapier → use it → Zapier creates pages for new integrations → more pages rank
- **Pinterest:** Users pin images → pins become SEO-optimized pages → Google indexes → searchers discover Pinterest → pin more images

**Blueprint:**
```
Create [CONTENT] targeting [KEYWORD]
  → Content ranks in search / AI search
  → SEARCHER discovers content → visits
  → Some become USERS → generate [DATA/BEHAVIOR]
  → Data informs BETTER/MORE content
  → More content ranks → more searchers
  → Repeat
```

**The key diagnostic question:** Does user activity create indexable content that attracts more users?

**Implementation checklist:**
- [ ] Each user action creates or improves a page that can rank
- [ ] Pages target real search queries (not just internal navigation)
- [ ] Content quality stays high even at scale (no thin/duplicate content)
- [ ] Feedback loop: performance data from published content improves next batch

### 4. Paid + Monetization Loop

**How it works:** Revenue from customers funds acquisition → better acquisition brings more customers → more customers generate more revenue → revenue funds more acquisition.

**Blueprint:**
```
CUSTOMER pays $X
  → $Y reinvested in paid acquisition
  → Acquisition brings MORE customers
  → More customers generate MORE revenue
  → More revenue funds BETTER acquisition
  → Repeat (if LTV > CAC with margin)
```

**The key diagnostic question:** Is LTV/CAC > 3x? Does each dollar of acquisition spend generate enough revenue to fund the next dollar of acquisition with profit?

**Critical metric:** Payback period. If it takes 12 months to recoup CAC, you need 12 months of capital to fund the loop. If payback is 30 days, the loop is nearly self-funding.

### 5. Sales-Assisted / PLG Hybrid Loop

**How it works:** Users adopt free product → product signals "this account is ready for sales" → sales team converts → enterprise deal funds more free product development → attracts more free users.

**Canonical examples:**
- **Slack:** Free teams grow → usage signals trigger sales outreach → enterprise deal → Slack invests in free product → more free teams
- **Zoom:** Free meetings → PQL (product-qualified lead) signals → sales team closes enterprise → revenue funds better free product

**Blueprint:**
```
FREE USER uses product
  → Product tracks [PQL SIGNALS] (team size, usage frequency, feature hits)
  → PQL triggers SALES outreach
  → Sales converts to PAID
  → Revenue funds BETTER FREE product
  → Better free product attracts MORE free users
  → Repeat
```

### 6. Community / Knowledge Loop

**How it works:** Community creates knowledge → knowledge attracts new members → new members create more knowledge → community becomes the authority source.

**Canonical examples:**
- **Stack Overflow:** Users ask questions → experts answer → answers rank in Google → searchers find SO → join → ask/answer more
- **Reddit:** Users post content → content surfaces via algorithm → attracts new users → more content → more surfacing

---

## How to Design Your Growth Loop

### Step 1: Map Your Current Loop (or Lack Thereof)

Answer honestly:
1. How do new users find you today? (Not "how do we want them to")
2. What do users create/do that could be visible to non-users?
3. Is there a natural invitation moment? When?
4. What percentage of new signups come from existing user activity?

If the answer to #4 is <10%, you don't have a loop yet. You have acquisition.

### Step 2: Choose Your Loop Type

| Your Situation | Best Loop Type |
|---------------|---------------|
| Users create visible artifacts | Viral / UGC Loop |
| Product better with more people | Invitation / Network Loop |
| Strong SEO potential + user data | Content / SEO Loop |
| Clear LTV > 3x CAC | Paid + Monetization Loop |
| Free product + enterprise upsell | Sales-Assisted / PLG Hybrid |
| Expert community in your niche | Community / Knowledge Loop |

### Step 3: Find the Transmission Trigger

The exact moment a user wants to share. Be brutally specific:
- NOT "after they use the product"
- YES "after they see their first quality score and it's higher than expected"
- YES "after they generate their first content brief and realize it's better than what their agency sends"

### Step 4: Design the Portable Artifact

What travels? It must be:
- **Instantly legible** — a stranger understands the value in 2 seconds
- **Self-contained** — doesn't require product access to appreciate
- **Branded** — carries product attribution naturally
- **Actionable** — viewer knows how to create their own

### Step 5: Make Sharing Selfish

The sharer must benefit. Options:
- They look smart/early/capable by sharing
- They get more value (more storage, more credits, better features)
- Their result improves with more participants
- They gain status in a community

### Step 6: Minimize Friction at Every Handoff

Audit every step from "user has urge to share" to "new user activates":
- How many clicks from share-moment to share-action?
- Does the recipient need to create an account to see the value?
- Is the landing experience instant value or "sign up to see"?
- Does the format work on mobile? (Most first-touches are mobile)

---

## Measuring Loop Health

### The K-Factor

```
K = invitations_per_user × conversion_rate_per_invitation

K > 1: Viral growth (exponential)
K = 0.5-1: Viral assist (amplifies other channels)
K < 0.5: Not viral (loop exists but doesn't drive meaningful growth alone)
```

Most products live at K = 0.3-0.7. That's fine — it means your loop amplifies your other channels by 30-70%, which is enormous.

### Loop Cycle Time

How long from "user signs up" to "user's activity brings another signup"? Shorter = faster compounding.

| Cycle Time | Compounding Speed | Example |
|-----------|-------------------|---------|
| Minutes | Explosive | TikTok (watch → create → share) |
| Hours | Fast | Loom (record → send → viewer signs up) |
| Days | Moderate | Dropbox (invite → friend joins → invites more) |
| Weeks | Slow | Slack (team adopts → invites external contacts) |
| Months | Very slow | HubSpot (content ranks → traffic → leads) |

### Loop Metrics Dashboard

| Metric | What It Measures | Target |
|--------|-----------------|--------|
| Viral coefficient (K) | Invitations × conversion | > 0.5 |
| Loop cycle time | Time from signup to referral | Decreasing |
| Artifact creation rate | % of users who create shareable output | > 20% |
| Share rate | % of creators who share | > 10% |
| Conversion from share | % of share recipients who sign up | > 5% |
| Activation rate | % of new signups who reach value | > 40% |
| Time to value | Minutes from signup to "aha" | < 5 min |

---

## False Loop Detection

### Signs You Don't Have a Real Loop

1. **"We'll encourage sharing"** — If the loop depends on asking users to share, it's marketing, not a loop
2. **"Users love us"** — NPS doesn't cause growth. Mechanism causes growth.
3. **"We'll add a referral program"** — Referral programs amplify existing loops, they don't create them
4. **"Our content will go viral"** — Content virality is unpredictable. Content SEO loops are reliable.
5. **"Network effects"** — Most products that claim network effects just mean "more users." Real network effects mean each user increases value for all others.

### The Test

Remove all paid acquisition and marketing for 30 days. If growth drops to near-zero, you don't have a loop. You have an acquisition engine. That's not bad — but call it what it is.
