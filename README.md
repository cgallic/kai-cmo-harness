# Kai — Marketing team in your terminal

31 marketing commands for Claude Code. Write emails, run ad campaigns, plan content, audit your SEO — all by typing a slash command.

You tell it what you need. It reads your project, learns your product, and does the work.

## Install (paste this into Claude Code)

```
git clone https://github.com/cgallic/kai-cmo-harness.git /tmp/kai-install && cp -r /tmp/kai-install/harness/skills/kai* ~/.claude/skills/ && rm -rf /tmp/kai-install && echo "Installed! Type /kai to start."
```

That's it. Type `/kai` to see everything you can do.

## What can it do?

**"Write all my emails"** → `/kai-email-system`
Maps every email your product needs (welcome, onboarding, trial expiring, win-back, password reset...), writes them all, checks quality, outputs ready for Loops.

**"Create my ad campaign"** → `/kai-ad-campaign`
Plans ads across Meta, Google, LinkedIn, TikTok. Writes copy for each platform with the right character limits and policy compliance. TOF/MOF/BOF variants.

**"Plan my content for the month"** → `/kai-content-calendar`
Generates a month of blog posts and LinkedIn articles mapped to keywords, personas, and business goals.

**"Write a landing page"** → `/kai-landing-page`
Full landing page copy — hero, value props, social proof, objection handling, CTA. Uses conversion psychology frameworks.

**"What should I do for marketing?"** → `/kai-growth-plan`
Tells you exactly what to do (and what NOT to do) based on your company stage. Pre-launch, early, growth, or scale.

**"Audit my marketing"** → `/kai-audit`
Runs 24 checklists across SEO, content, email, ads, social, CRO. Gives you a health score and prioritized fix list.

**"Get us into ChatGPT answers"** → `/kai-surround-sound`
Builds a plan to get your brand mentioned when people ask AI about your category.

**"Make social posts from this blog"** → `/kai-repurpose`
Takes one piece of content and produces 15-25 posts across LinkedIn, X, Instagram, TikTok, email, and YouTube.

## How it works

First time you run any `/kai` command in a project, it:

1. **Reads your codebase** — CLAUDE.md, README, package.json, routes, schemas, whatever exists
2. **Creates MARKETING.md** — a product marketing bible with your ICP, personas, brand voice, competitive landscape
3. **Does the work** — writes the emails, ads, content, whatever you asked for

Every command after that reads MARKETING.md and skips straight to work. No setup. No answering the same questions 30 times.

## All 31 commands

### Make stuff

| Command | What you get |
|---------|-------------|
| `/kai-write` | One piece of content — blog, email, LinkedIn, ad, press release |
| `/kai-landing-page` | Complete landing page copy |
| `/kai-email-system` | Every email your product needs |
| `/kai-ad-campaign` | Full ad campaign across platforms |
| `/kai-content-calendar` | Month of planned + written content |
| `/kai-social` | Week/month of social posts for all platforms |
| `/kai-video` | Video scripts for TikTok, YouTube, Reels |
| `/kai-cold-outreach` | Cold email sequences |
| `/kai-newsletter` | Newsletter editions |
| `/kai-case-study` | Customer success stories |
| `/kai-repurpose` | 1 piece → 15-25 pieces across platforms |
| `/kai-launch` | Full product launch — emails + ads + PR + content + social |
| `/kai-retarget` | Retargeting campaign setup |
| `/kai-influencer` | Influencer marketing campaigns |
| `/kai-webinar` | Webinar/event marketing |
| `/kai-podcast` | Podcast launch or guest strategy |
| `/kai-abm` | Account-based marketing for enterprise |
| `/kai-partnership` | Co-marketing campaigns |

### Check stuff

| Command | What you get |
|---------|-------------|
| `/kai-gate` | Quality score on any content |
| `/kai-audit` | Full marketing audit with health scores |
| `/kai-seo-audit` | Technical SEO audit with fix list |
| `/kai-cro` | Conversion rate audit for any page |

### Plan stuff

| Command | What you get |
|---------|-------------|
| `/kai-brief` | Content brief before writing |
| `/kai-growth-plan` | Marketing plan for your stage |
| `/kai-brand` | Brand positioning + messaging framework |
| `/kai-budget` | Marketing budget planning |
| `/kai-retention` | Customer retention system |

### Research stuff

| Command | What you get |
|---------|-------------|
| `/kai-competitors` | Competitive teardown + sales battlecards |
| `/kai-surround-sound` | Get mentioned in AI answers |
| `/kai-analytics` | Analytics + attribution setup |

### Help

| Command | What you get |
|---------|-------------|
| `/kai` | See all commands, organized by what you need |

## Where to start

**Just launched?** → `/kai-growth-plan` first, then `/kai-email-system` + `/kai-landing-page`

**Need content?** → `/kai-content-calendar` for the plan, `/kai-write` for individual pieces

**Running ads?** → `/kai-ad-campaign` handles the copy, `/kai-cro` audits your landing page

**Want everything?** → `/kai-launch` orchestrates all of the above into one coordinated campaign

## What's behind it

153 marketing knowledge files that power the commands:

- 41 playbooks (growth loops, CRO, pricing, competitive intel, content repurposing...)
- 27 frameworks (SEO rules, persuasion psychology, copywriting formulas, AI search optimization)
- 24 checklists (technical SEO, ad launch, content quality, email, social media audit...)
- 17 channel guides (every major platform)
- 8 audience personas
- 12 ad platform policies (Google, Meta, TikTok, LinkedIn, and 6 more — 7,600+ lines of TOS so your ads don't get rejected)

Every piece of content gets quality-checked before it ships:
- **Four U's score** — is it Unique, Useful, Ultra-specific, Urgent?
- **Banned word check** — no "leverage", "synergy", or AI slop
- **Platform compliance** — character limits, policy rules, format requirements

## Requirements

- [Claude Code](https://claude.ai/download) (CLI, desktop app, or VS Code extension)
- That's it

## License

MIT — use it however you want.
