# Kai CMO Harness — Open-Source Launch Plan

**Model:** Gstack-style — free tool that spreads through community, soft CTA for services
**Launch type:** Open-source repo launch (free tool, drive installs + GitHub stars)
**Launch date:** April 9, 2026 (T-0)
**Domain:** meetkai.xyz
**Repo:** github.com/cgallic/kai-cmo-harness
**Existing audience:** KaiCalls, BuildWithKai, Awesome Backyard Parties users
**Version:** 1.0.0 (bump from 0.2.0 for launch)
**Monetization:** No pricing page. Soft "Need help? We'll run it for you" CTA. Let demand define the offer.

---

## Phase Timeline

| Phase | Dates | Focus |
|-------|-------|-------|
| **Phase 1: Fix the product** | Mar 26 – Apr 1 | Install, onboarding, landing page — make it work for a stranger |
| **Phase 2: Pre-launch tease** | Apr 2 – Apr 6 | Social hints, email teaser, blog post draft |
| **Phase 3: Launch day** | Apr 9 | Announcement blast — email, social, LinkedIn, blog, GitHub |
| **Phase 4: Post-launch** | Apr 10 – Apr 23 | Nurture, tutorials, community engagement |

---

## Phase 1: Fix the Product (Mar 26 – Apr 1)

The product works but a stranger can't use it. Fix three things:

### 1.1 Simplify Install
**Current problem:** One-liner git clones to /tmp, copies skills, requires understanding Claude Code's skill system.
**Fix:**
- Create a proper install script that detects OS and shell
- Add a `npx kai-install` or `brew install` path if feasible
- Fallback: keep the one-liner but make it idiot-proof with error messages
- Add a verification step: "Kai installed! Type /kai to see your commands"

### 1.2 Build Onboarding Flow
**Current problem:** After install, user sees 31 commands and freezes.
**Fix:**
- Create a `/kai-start` or `/kai-setup` command that runs on first use
- Walks through: "What's your product? What stage are you at? What do you need first?"
- Auto-generates MARKETING.md
- Suggests the ONE command to run next based on their answers
- Print a "Your first 3 commands" cheat sheet

### 1.3 Rewrite Landing Page (meetkai.xyz)
**Current problem:** meetkai.xyz shows paid $299-$999 tiers — doesn't match the free OSS + paid KaiCalls model.
**Fix — meetkai.xyz becomes the Kai ecosystem hub:**

**Section 1 — Hero:**
- "Meet Kai. AI tools for founders who build alone."
- Subtitle: "Marketing that writes itself. A phone that answers itself. All from one team."

**Section 2 — Kai CMO (the free hook):**
- "Your marketing team in a terminal. Free and open-source."
- Install one-liner front and center
- 30-second demo GIF showing /kai in action
- 3 use cases: email system, ad campaign, content calendar
- CTA: "Install now" (GitHub)

**Section 3 — KaiCalls (the trojan):**
- "Your phone, but with a person."
- Kai answers your calls 24/7, takes messages, books appointments
- Social proof: "4,300+ calls handled"
- CTA: "Get your AI secretary" (links to KaiCalls signup)

**Section 4 — Social proof:**
- "Powers 5 live products"
- Logos/names of products using Kai

**Section 5 — Soft services CTA:**
- "Need help? We'll run it for you."
- No pricing. Just a contact form or Calendly link.
- Let demand define the offer.

**Footer:** GitHub link, social links, "Built by Connor Gallic"

---

## Phase 2: Pre-Launch Tease (Apr 2 – Apr 6)

### 2.1 Teaser Social Posts (3-5 posts)
- "We've been running our marketing from a terminal for 6 months. Next week we're open-sourcing the whole thing."
- Show snippets of /kai commands doing real work
- Tease the number: "31 marketing commands. 153 knowledge files. 0 dashboards."

### 2.2 Teaser Email to Existing List
- Subject: "We're open-sourcing our marketing engine"
- Body: What Kai is, why we built it, what's coming, how to get early access
- CTA: Star the repo / join waitlist

### 2.3 Blog Post Draft
- Title: "We Replaced Our Marketing Team With 31 Terminal Commands"
- Story: Why we built Kai, what it does, results so far, why we're open-sourcing it
- Publish on launch day, draft during pre-launch

---

## Phase 3: Launch Day — April 9 (T-0)

### 3.1 Announcement Email
- To: Full existing audience
- Subject: "Kai is live. Your marketing team in a terminal."
- Body: What it is, install command, 3 commands to try first, link to blog post
- CTA: Install now + star on GitHub

### 3.2 Blog Post Publish
- Publish the announcement blog post
- Cross-post to dev.to, Hashnode, Medium

### 3.3 LinkedIn Article
- Adapted from blog post for LinkedIn audience
- More business-focused angle: "Why I gave away our $50K marketing system"

### 3.4 Social Blitz (5-8 posts across platforms)
- Launch announcement thread (X/Twitter)
- LinkedIn post
- Product Hunt launch (if applicable)
- Hacker News "Show HN" post
- Reddit posts (r/ChatGPT, r/ClaudeAI, r/marketing, r/SaaS)

### 3.5 GitHub Repo Polish
- Updated README (already solid — minor tweaks for launch)
- Add CONTRIBUTING.md
- Create GitHub Discussions or Discord for community
- Pin issues for "good first contribution"

---

## Phase 4: Post-Launch (Apr 10 – Apr 23)

### 4.1 Follow-Up Email Sequence (2-3 emails)
- Day 2: "3 things to try with Kai this week"
- Day 5: "How [product] uses Kai to write all their emails"
- Day 10: "What people are building with Kai" (early user stories)

### 4.2 Tutorial Content
- "How to write a complete email system in 5 minutes with /kai-email-system"
- "Audit your marketing in 60 seconds with /kai-audit"
- Short video walkthroughs

### 4.3 Community Engagement
- Respond to GitHub issues within 24h
- Share user wins on social
- Collect testimonials and case studies

---

## Asset Checklist

| # | Asset | Channel | Phase | Status |
|---|-------|---------|-------|--------|
| 1 | Install script overhaul | Repo | Phase 1 | Needed |
| 2 | Onboarding flow (/kai-start) | Repo | Phase 1 | Needed |
| 3 | Landing page rewrite | meetkai.xyz | Phase 1 | Needed |
| 4 | Demo GIF/video | Landing page | Phase 1 | Needed |
| 5 | Teaser social posts (3-5) | X, LinkedIn | Phase 2 | Needed |
| 6 | Teaser email | Loops | Phase 2 | Needed |
| 7 | Announcement blog post | Blog | Phase 2-3 | Needed |
| 8 | Announcement email | Loops | Phase 3 | Needed |
| 9 | LinkedIn article | LinkedIn | Phase 3 | Needed |
| 10 | Launch day social posts (5-8) | X, LinkedIn, Reddit, HN | Phase 3 | Needed |
| 11 | GitHub repo polish | GitHub | Phase 3 | Needed |
| 12 | Follow-up email sequence (2-3) | Loops | Phase 4 | Needed |
| 13 | Tutorial blog posts (2) | Blog | Phase 4 | Needed |

### Removed (not needed for open-source launch)
- ~~Meta ads~~ — no ad budget needed, organic push
- ~~Google ads~~ — same
- ~~Press release~~ — overkill for dev tool launch
- ~~Retargeting~~ — no paid funnel

---

## Messaging Guide (Draft)

### The Kai Ecosystem (Gstack-style positioning)

**meetkai.xyz** is the hub for Kai — a suite of AI tools for founders who build alone.

| Product | What it is | Price | Role in ecosystem |
|---------|-----------|-------|-------------------|
| **Kai CMO** | 31 marketing slash commands for Claude Code | Free / open-source | The hook — gets people in the door |
| **KaiCalls** | AI phone agent / digital secretary | Paid SaaS | The trojan — revenue driver |
| **Future tools** | TBD | TBD | Expand the suite |

### Trojan Horse Flow
```
Founder discovers Kai CMO (free) →
  Uses it for marketing (builds trust) →
    Sees KaiCalls on meetkai.xyz →
      "Wait, they have an AI that answers my phone?" →
        Pays for KaiCalls
```

### Core Value Prop (Kai CMO — the launch product)
"31 marketing commands for Claude Code. Type a slash command, get finished marketing."

### One-liner
"Your marketing team in a terminal."

### KaiCalls Cross-sell (soft, not hard)
On meetkai.xyz: "Need more than marketing? Meet Kai — your AI secretary who answers your phone 24/7."
No pricing page for services. Just: "Need help? Talk to us."

### Key Proof Points
- 153 knowledge files (frameworks, checklists, personas, channel guides)
- Quality gates on every piece of content (Four U's, banned words, SEO lint)
- Powers marketing for 5 live products
- Free and open-source (MIT)
- Same team behind KaiCalls (4,900+ leads captured, 4,300+ calls handled)

### Target Audience (for launch)
- Solo founders who do their own marketing
- Developers who hate marketing but know they need it
- Claude Code power users looking for useful skills
- Small teams without a marketing hire
- **Secondary:** Founders who also need phone/receptionist (KaiCalls funnel)

### Tone
Direct. No jargon. Show, don't tell. "Here's what it does" > "Revolutionizing marketing with AI."
Same energy as Gstack — builder tool, not enterprise software.

---

## Success Metrics

| Metric | Target (30 days) |
|--------|-----------------|
| GitHub stars | 500+ |
| Installs (clone/download) | 200+ |
| Email signups | 100+ |
| Blog post views | 2,000+ |
| Social impressions | 10,000+ |
| KaiCalls page clicks (from meetkai.xyz) | 50+ |
| KaiCalls trial signups (trojan conversion) | 10+ |

---

## Approval Gate

**Do not produce any assets until this timeline is approved.**

Questions for approval:
1. Does the phase timeline work with your schedule?
2. Is "free and open-source" the right positioning, or should we keep a paid tier?
3. Any channels to add or remove?
4. Is April 9 realistic for T-0?
