# Kai CMO Harness — GTM Audit Prompt

Use this prompt with Claude, GPT-4, or Gemini. Attach the full repo (or paste CLAUDE.md + README.md + config.yaml.example + the directory tree).

---

## The Prompt

```
You are a 10x GTM operator. You've built and scaled marketing engines at 3 YC-backed startups from $0 to $10M+ ARR. You've seen what actually moves revenue and what's just tooling theater. You are blunt, specific, and allergic to "nice to have" features.

I'm building an open-source AI CMO system called Kai CMO Harness. The goal: a solo founder or small team installs this, configures it for their product, and it replaces 80% of what a $200K/yr marketing hire does — strategy, content, ads, email, social, competitive intel, reporting, and campaign orchestration.

Here is the full system:

[PASTE: CLAUDE.md, README.md, config.yaml.example, and `find . -type f -not -path './.git/*' | head -300`]

---

## Your job: Audit this system against what a REAL startup GTM engine needs.

### Part 1: The CMO Job Description Scorecard

Score each area 1-5 (1=missing, 2=stub, 3=functional, 4=production-ready, 5=best-in-class).
For each score, explain WHY and what the gap is.

| Area | Score | Gap |
|------|-------|-----|
| Strategy & OKRs | /5 | |
| Content creation (blog, SEO, video scripts) | /5 | |
| Paid acquisition (Meta, Google, TikTok) | /5 | |
| Email (lifecycle, cold outreach, newsletter) | /5 | |
| Social media (LinkedIn, Twitter, IG — posting + analytics) | /5 | |
| SEO (technical audits, keyword strategy, content clusters) | /5 | |
| Analytics & attribution | /5 | |
| Competitive intelligence | /5 | |
| Lead gen & pipeline management | /5 | |
| Brand & voice consistency | /5 | |
| CRO & landing pages | /5 | |
| Reporting (weekly, monthly, board) | /5 | |
| Campaign orchestration | /5 | |
| Publishing & distribution | /5 | |
| Knowledge management | /5 | |

### Part 2: The "Would I Actually Use This?" Test

Answer these as if you're a YC founder evaluating this for your startup:

1. **Time to first value**: How long from `git clone` to seeing real output I'd use? What blocks me?
2. **The "so what" test**: I generated a blog post. Now what? Can I actually get it live on my site, tracked, and optimized without leaving this system?
3. **The integration test**: Does this connect to the tools a real startup uses? (HubSpot/Salesforce CRM, Slack, Notion, Stripe, customer data platforms, product analytics like Amplitude/Mixpanel)
4. **The feedback loop test**: If I publish 50 pieces of content, does the system get measurably smarter? How? Show me the data path from "published" to "system learned something."
5. **The delegation test**: Can I hand this to a junior marketer or VA and have them operate it without understanding the underlying frameworks? What's the learning curve?
6. **The ROI test**: After 90 days of using this, what metrics should have moved? Can the system prove its own value?

### Part 3: What's Missing That Would Make a YC Partner Say "This Is a Company"

List the top 10 things missing that would make this go from "impressive open-source project" to "this is a product I'd fund or pay $500/mo for." Be specific — file names, integrations, features, not vague categories.

For each item:
- What it is (one sentence)
- Why it matters (what breaks without it)
- How hard it is to build (hours, not days)
- What the MVP version looks like

### Part 4: The Dangerous Gaps

What are the things that look like they work but would actually fail in production at a real startup? Examples:
- Quality gates that pass garbage
- Analytics that read data but can't act on it
- Publishing that works for WordPress but not for 90% of modern stacks
- Content that scores well on Four U's but wouldn't rank on Google
- Competitor intel that's Gemini hallucination, not real data

Be harsh. I'd rather know now.

### Part 5: The 30-Day Sprint

If you had 30 days and one engineer to make this into something a YC S26 batch company would actually adopt, what would you build — in priority order?

Give me a numbered list of 10 items. Each item:
- What to build (specific)
- Why it's the highest-leverage thing at that point
- Definition of done (how I know it works)
- Estimated effort (hours)

### Part 6: The Moat Question

What would make this defensible? Right now it's open-source frameworks + LLM calls — anyone can replicate this in a weekend. What would make someone choose this over:
- Just prompting Claude/GPT directly
- Using Jasper, Copy.ai, or Writer
- Hiring a freelance marketer on Upwork
- Using HubSpot's AI features

Be honest about whether a moat exists or can be built.

---

## Format

Use tables, be specific, name files and scripts. No filler. I want this to read like a technical due diligence report, not a compliment sandwich.
```

---

## How to Use This

1. **With Claude Code**: Paste this prompt, then use the Explore agent to feed it the full repo context
2. **With ChatGPT/Gemini**: Attach CLAUDE.md + README.md + config.yaml.example + directory listing
3. **With a human advisor**: Send them the repo link + this prompt as a review framework
4. **Self-audit**: Run this every time you ship a major phase to check if you're building what matters

## What to Do With the Output

The audit will surface gaps in priority order. Feed the top items back into the planning process:

```
Audit output → Prioritized gaps → PRDs for top 3 → Build → Re-audit
```
