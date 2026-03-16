# Kai CMO Harness

An autonomous marketing intelligence system. Works two ways:

1. **Claude Code path** — Drop `CLAUDE.md` + `knowledge/` into any project. Instant marketing brain with quality gates. No server needed.
2. **OpenClaw path** — Full autonomous CMO with Discord integration, heartbeat protocol, domain agents, scheduled tasks, and self-improvement loop. Needs a VPS.

## What's Inside

- **100+ marketing frameworks** — AEO/AI search, content copywriting, Meta advertising, perception engineering, SEO, email, TikTok, paid acquisition
- **Ad network policy library** — Actual TOS, prohibited/restricted content, and compliance rules for 9 platforms (Google, Meta, TikTok, LinkedIn, Microsoft/Bing, Pinterest, Snapchat, Amazon, X/Twitter) plus cross-platform FTC/GDPR/CAN-SPAM/COPPA compliance
- **Quality gate pipeline** — Four U's scoring (12+/16 to publish), banned word detection, SEO linting, platform policy compliance checks with auto-retry
- **8 audience personas** — With pain points, hooks, and voice profiles
- **Content pipeline** — Research → Brief → Write → Gate → Approve → Publish → 30-day performance check
- **Self-improvement loop** — Extracts winning patterns from published content and updates the harness defaults
- **Analytics engine** — GA4, GSC, Stripe, Supabase, Meta Ads, Instantly — all via CLI
- **Domain agents** — Product, finance, infrastructure, research — each monitors its scope and reports to Discord
- **Heartbeat protocol** — Parallel fan-out to all agents, yield, route alerts

## Quick Start

### Path A: Claude Code (5 minutes)

```bash
git clone https://github.com/cgallic/kai-cmo-harness.git
cp kai-cmo-harness/CLAUDE.md ./your-project/
cp -r kai-cmo-harness/knowledge ./your-project/
cp -r kai-cmo-harness/harness ./your-project/
cp -r kai-cmo-harness/scripts/quality_gates ./your-project/scripts/
```

Start Claude Code in your project. It now has marketing intelligence.

### Path B: Full Autonomous CMO (30 minutes)

```bash
git clone https://github.com/cgallic/kai-cmo-harness.git
cd kai-cmo-harness
bash setup.sh
```

The setup wizard walks you through configuration, credential setup, and deployment.

## Repository Structure

```
kai-cmo-harness/
├── CLAUDE.md                    # Standalone Claude Code entry point
├── config.yaml.example          # Central config template
├── setup.sh                     # Interactive setup wizard
├── render_templates.py          # Jinja2 renderer for workspace files
│
├── knowledge/                   # 100+ marketing frameworks (ships as-is)
│   ├── frameworks/              # Core frameworks (AEO, copywriting, Meta ads)
│   ├── channels/                # Channel guides (blog, email, TikTok, etc.)
│   ├── checklists/              # Validation checklists
│   ├── personas/                # 8 audience personas
│   ├── playbooks/               # Strategic playbooks
│   └── design/                  # UI/UX design patterns
│
├── harness/                     # Pipeline config + quality gates
│   ├── brief-schema.md          # Content brief format
│   ├── skill-contracts/         # Format-specific YAML contracts
│   └── references/              # Ad network policies & compliance (12 files, 7,600+ lines)
│       ├── google-ads-policy-reference.md   # Google Ads TOS/policies
│       ├── meta-ads-rules.md                # Meta/FB/IG TOS/policies
│       ├── tiktok-ads-policy-reference.md   # TikTok TOS/policies
│       ├── linkedin-ads-rules.md            # LinkedIn Ads policies
│       ├── microsoft-ads-rules.md           # Microsoft/Bing Ads policies
│       ├── pinterest-ads-rules.md           # Pinterest Ads policies
│       ├── snapchat-ads-policy-reference.md # Snapchat Ads policies
│       ├── amazon-ads-policy-reference.md   # Amazon Ads policies
│       ├── x-ads-policy-reference.md        # X/Twitter Ads policies
│       ├── advertising-compliance.md        # FTC/GDPR/CAN-SPAM/COPPA/CCPA
│       ├── google-ads-rules.md              # Google Ads copy constraints
│       └── cold-email-rules.md              # CAN-SPAM, deliverability
│
├── workspace/                   # OpenClaw workspace templates
│   ├── MARKETING.md             # Operating config (parsed by harness)
│   ├── SOUL.md                  # Voice profile + banned words
│   ├── HEARTBEAT.md             # Agent heartbeat protocol
│   ├── AGENTS.md                # Agent hierarchy + data tools
│   ├── TOOLS.md                 # Tool configuration
│   └── agents/                  # Domain agent templates (.j2)
│
├── scripts/                     # Python pipeline + analytics
│   ├── harness_cli.py           # Main CLI (brief → write → gate → approve)
│   ├── quality_gates/           # four_us_score, banned_word_check, seo_lint
│   ├── self_improvement/        # Pattern extraction + harness updates
│   ├── content/                 # Content generation helpers
│   ├── leads/                   # Lead pipeline + conversion
│   ├── ads/                     # Ad management (Meta, Google)
│   └── analytics/               # GA4, GSC, Stripe, Supabase, Meta Ads
│
├── agent/                       # Autonomous loop (optional)
│   ├── loop.py, scheduler.py    # Task scheduling + execution
│   ├── channels/                # Discord, WhatsApp integrations
│   └── tasks/                   # Generic + example product handlers
│
├── gateway/                     # FastAPI webhook gateway (optional)
│
├── deploy/                      # VPS deployment templates
│   ├── cloud-config.yaml.j2    # Cloud-init template
│   ├── cmo-agent.service        # systemd service
│   └── deploy.sh                # Git pull → restart → health check
│
├── examples/                    # Config examples by business type
│   ├── config.yaml.saas
│   ├── config.yaml.ecommerce
│   └── config.yaml.agency
│
└── docs/                        # Documentation
    ├── QUICK_START.md
    ├── CONFIGURATION.md
    ├── ADDING_PRODUCTS.md
    ├── ANALYTICS_SETUP.md
    └── ARCHITECTURE.md
```

## Quality Gates

Every piece of content passes three gates before publishing:

| Gate | Tool | Threshold |
|------|------|-----------|
| **Four U's** | `scripts/quality_gates/four_us_score.py` | 12+/16 (10+ for ads/email) |
| **Banned Words** | `scripts/quality_gates/banned_word_check.py` | Tier 1 = instant reject |
| **SEO Lint** | `scripts/quality_gates/seo_lint.py` | 0 errors (long-form only) |

Content that fails gets 2 automatic revision attempts. After that, it's escalated to a human.

## Content Formats

| Format | Framework | Quality Gate |
|--------|-----------|-------------|
| Blog post | Algorithmic Authorship | Four U's 12+ / SEO lint |
| LinkedIn article | LinkedIn writing guide | Four U's 12+ |
| Cold email (3-touch) | Cold email rules | Four U's 10+ |
| Meta ads (FB/IG) | Meta advertising + Meta TOS | Four U's 10+ / Policy check |
| Google ads (RSA + PMax) | Google Ads rules + Google TOS | Four U's 10+ / Policy check |
| TikTok ads/scripts | TikTok algorithm + TikTok TOS | Four U's 10+ / Policy check |
| LinkedIn ads | LinkedIn Ads policies | Four U's 10+ / Policy check |
| Microsoft/Bing ads | Microsoft Ads policies | Four U's 10+ / Policy check |
| Pinterest ads | Pinterest Ads policies | Four U's 10+ / Policy check |
| Snapchat ads | Snapchat Ads policies | Four U's 10+ / Policy check |
| Amazon ads | Amazon Ads policies | Four U's 10+ / Policy check |
| X/Twitter ads | X Ads policies | Four U's 10+ / Policy check |
| Email lifecycle | Email lifecycle | Four U's 10+ |
| Press release | Press release guide | Four U's 12+ |
| SEO content | AEO + Algorithmic Authorship | Four U's 12+ / SEO lint |

## Ad Network Policy Library

Every ad platform has rules about what you can and can't say. The harness includes actual TOS-derived policy docs so content gets checked **before** it hits the ad review queue.

| Platform | Lines | Covers |
|----------|------:|--------|
| Google Ads | 991 | Prohibited/restricted content, healthcare certs, crypto rules, disapproval prevention |
| Meta (FB/IG) | 931 | 22 prohibited categories, Special Ad Categories, personal attributes ban, MARS enforcement |
| TikTok | 1,020 | Shop seller policies, Spark Ads, AI content disclosure, political ad ban |
| X/Twitter | 621 | Verification tiers, political certification by country, cannabis/crypto |
| Amazon | 579 | 18-month claim evidence, DSP policies, Brand Store requirements |
| Snapchat | 512 | AR lens/filter rules, young audience protections, EU political ad ban |
| Pinterest | 490 | Weight loss ad ban (first platform), body image rules, GLP-1 exception |
| LinkedIn | 465 | Professional context, B2B claim substantiation, Account Quality Score |
| Microsoft/Bing | 431 | Country-specific gambling bans, clinical trials ban, editorial rules |
| **Cross-platform** | **1,500** | **FTC, GDPR, CAN-SPAM, COPPA, CCPA, FINRA, FDA, AI ad rules** |

## Knowledge Base Highlights

- **Algorithmic Authorship** — 31 rules for ranking in Google passage indexing and AI Overviews
- **Perception Engineering** — 3-layer persuasion framework (Perception → Context → Permission)
- **AEO Research** — Patent analysis (Information Gain US12013887B2), Perplexity reverse-engineering, Entity SEO
- **GEO Citation Science** — Statistics +37%, Quotes +40%, Citations +115% visibility in AI search
- **Meta Advertising** — Andromeda retrieval, GEM generative ads, Lattice prediction, Breakdown Effect

## Self-Improvement

The harness learns from its own output:

1. **30-day performance check** — Measures published content against GSC/GA4 data
2. **Pattern extraction** — Identifies what works (hooks, formats, word counts, topics)
3. **Harness defaults update** — Writes winning patterns back into MARKETING.md
4. **Next run** — Harness reads updated defaults and applies them to new content

## License

MIT
