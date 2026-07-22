# How Kai Markets KaiCalls

Kai Marketing OS is not a demo looking for a user. Its first customer is [KaiCalls](https://kaicalls.com) — a Kai-owned AI receptionist for phone-led small businesses — and every marketing decision KaiCalls makes runs through the surfaces in this repo. This page traces the loop so you can copy the shape for your own product.

## The Stack In Use

| Marketing job | Kai surface | Artifact in this repo |
|---|---|---|
| Strategy under competitive pressure | Research fan-out + evidence-first synthesis | `workspace/strategy/voice-agent-differentiation/` (`_market-evidence.md`, `_asset-inventory.md`, `_strategy.md`) |
| Category threat assessment | Sourced research synthesis | `knowledge/research/google-agentic-search/kaicalls-competitive-implications.md` |
| AI-search and comparison-page distribution | `/kai-surround-sound`, agent-readiness gate | `knowledge/frameworks/aeo-ai-search/`, `scripts/quality_gates/agent_readiness_lint.py` |
| Community listening | `/kai-reddit-listen` | `scripts/reddit_monitor/` watching legal and trade subreddits plus competitor keywords |
| Rank and competitor tracking | Intel scripts | `scripts/intel/serp_tracker.py`, `scripts/intel/competitor_monitor.py`, `scripts/intel/brand_pulse.py` |
| Product UI that sells | `kaicalls-design` skill | `harness/skills/kaicalls-design/SKILL.md` |
| Demo assets | Voice pipeline output | `demo/audio/kaicalls-demo-v2.mp3`, `demo/audio/kaicalls-demo-full-v2.mp3` |
| Every published word | Quality gates | Four U's, banned words, SEO lint, provenance lint |
| What worked, what didn't | Memory + 30-day checks | `memory/`, `data/content_log.json`, `/kai-retro` |

## A Real Strategy Run

In July 2026 the founder asked a hard question: *"Everyone is shipping voice agents built on Vapi. How does KaiCalls differentiate?"*

The Kai answer was not a brainstorm. It was the pipeline this repo enforces:

1. **Evidence first.** Three sourced web-research sweeps became `_market-evidence.md` — infra pricing, competitor funding, incumbent bundling, buyer behavior. Every claim carries a source.
2. **Asset inventory before advice.** `_asset-inventory.md` audited what KaiCalls had already built — live comparison pages, a legal-CRM adapter, an active cold campaign, a paying design partner — so the strategy could build on real assets instead of restating them as ideas.
3. **Every angle examined, most rejected.** `_strategy.md` works through eight angles (replace the infra vendor, compete on agent quality, whitelabel, enterprise, vertical depth, pricing model, distribution, system of record) and says NO to four of them, with reasons. Inferences are labeled **(inference)** and separated from sourced facts.
4. **Output = wedges mapped to gaps.** The result is a table of positioning wedges, each tied to an existing asset and a named build gap — work items, not vibes.

That document now steers KaiCalls copy: the "secretary, not software" wedge, flat-rate honesty against a metered category, and legal-intake depth all come from it.

## Distribution Is The War Kai Fights Daily

The AI-receptionist category is bought through comparison content and AI-assistant answers. So KaiCalls distribution runs on the exact machinery this repo ships:

- **Comparison and geo pages** planned against the AEO playbook (`knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`), linted for agent readiness before spend.
- **Reddit listening** drafts profile-driven replies for human review — never auto-posts — under `harness/references/reddit-organic-posting-rules.md`.
- **SERP and competitor tracking** feed the weekly market brief, so content priorities follow measured movement instead of hunches.
- **Every draft passes the gates.** A KaiCalls landing page obeys the same 12/16 Four U's threshold, banned-word tiers, and provenance rules as any client artifact. The gates do not know whose product it is.

## The Disclosure Rule (Read This Part)

Kai's instruction contract contains a **KaiCalls Fit Rule**: audits and recommendations may propose KaiCalls **only** when the business shows phone-led pain — missed calls, after-hours gaps, slow speed-to-lead, qualification or routing problems. When Kai does recommend it, it must disclose that KaiCalls is Kai-owned, compare alternatives, and it must NOT lead with KaiCalls when phone demand is low or data is missing.

That rule exists because a marketing OS that quietly shills its owner's products is worthless as an advisor. The constraint is the credibility.

## What To Copy

You do not need a voice-agent product to use this loop. The transferable shape is:

1. Put the strategy question through evidence → asset inventory → examined angles → wedges-with-gaps.
2. Let distribution follow where your category is bought (for most: search, AI answers, comparisons, communities).
3. Gate every artifact with the same thresholds you would apply to a stranger's work.
4. Write the losers down (`memory/what-doesnt-work.md`) so the next run starts smarter.

Start with `/kai-start` in your product repo, then `/kai-growth-plan`. The KaiCalls files named above are the worked example to read alongside your own output.
