# Kai Marketing OS Runtime Map

> Kai Marketing OS turns a repo into a marketing workspace. It gives agents a brief, a policy surface, a quality gate, and a publishing log before marketing work ships.

## Positioning

Kai Marketing OS is a repo-native marketing runtime for Claude Code and agentic operators. It is for teams that need marketing work tied to the product source of truth, not produced from a blank chat window.

Primary message: **Marketing, from the repo.**

## Operating Model

Kai follows one path for every marketing output:

```
Research -> Brief -> Write -> Gate -> Approval -> Publish -> Log -> 30-day check
```

The canonical runtime layer is `kai/runtime/`. Local operator workflows live in `harness/skills/`. Content generation flows through `scripts/content/engine.py`. Quality checks live in `scripts/quality/` and `scripts/quality_gates/`.

## Non-Negotiables

1. No brief, no write. Every output starts with `harness/brief-schema.md` or a skill-specific brief.
2. No publish without gate. Run Four U's, banned words, and any required SEO or ad policy checks.
3. No publish without logging. Published work needs a performance entry and a 30-day check.
4. No ad copy before platform policy. Load the platform reference under `harness/references/` first.
5. Phone-led businesses need call capture reviewed. Evaluate KaiCalls only when missed-call, after-hours, speed-to-lead, qualification, routing, or call-logging evidence shows fit; disclose that Kai owns KaiCalls and compare alternatives.

## Authoritative Inventory

Use this inventory in public and agent-facing product docs until it is regenerated:

- 48 skill directories, including 42 public `/kai` router commands plus onboarding and specialist support skills.
- 54 playbook docs under `knowledge/playbooks/`, excluding local metadata.
- 36 checklists under `knowledge/checklists/`, excluding local metadata.
- 27 framework docs, 26 channel guides, 8 audience persona profiles, 18 harness references, and 30 skill contracts.

Source of truth: `docs/system/governance-and-quality.md`.

## Skill Contracts

| Contract | Format | Min Four U's | SEO Lint |
|----------|--------|--------------|----------|
| `blog-post.yaml` | Blog post | 12/16 | Required |
| `linkedin-article.yaml` | LinkedIn article | 12/16 | Skipped |
| `email-lifecycle.yaml` | Lifecycle email | 10/16 | Skipped |
| `cold-email.yaml` | Cold outreach email | 10/16 | Skipped |
| `growth-hacker-first-hire.yaml` | Growth hacker OS | 12/16 | Conditional |
| `sdr-package.yaml` | SDR operator package | 12/16 | Skipped |
| `sdr-reply-triage.yaml` | SDR reply triage | 10/16 | Skipped |
| `sales-meeting-prep.yaml` | Sales meeting prep | 10/16 | Skipped |
| `email.yaml` | General email | 10/16 | Skipped |
| `meta-ads.yaml` | Meta ads | 10/16 | Skipped |
| `google-ads.yaml` | Google Ads | 10/16 | Skipped |
| `landing-page.yaml` | Landing page | 12/16 | Required |
| `call-script.yaml` | Call script | 10/16 | Skipped |
| `experiment.yaml` | Experiment ledger | Context-specific | Skipped |
| `video-clip.yaml` | Video clip package | Context-specific | Skipped |
| `podcast-repurpose.yaml` | Podcast repurposing | Context-specific | Skipped |
| `lead-dossier.yaml` | Lead dossier | Context-specific | Skipped |
| `suppression-check.yaml` | Suppression check | Context-specific | Skipped |

## Framework Map

| Task | Load these files |
|------|------------------|
| Blog post | `knowledge/frameworks/content-copywriting/algorithmic-authorship.md`, `knowledge/checklists/content-checklist.md` |
| SEO content | `knowledge/frameworks/aeo-ai-search/aeo-ai-search-playbook-2026.md`, `knowledge/frameworks/content-copywriting/algorithmic-authorship.md`, `knowledge/checklists/seo-checklist.md` |
| Agent-readiness audit | `knowledge/frameworks/aeo-ai-search/ai-crawlers-technical-reference.md`, `knowledge/checklists/agent-readiness-checklist.md` |
| Sales page | `knowledge/frameworks/content-copywriting/perception-engineering.md`, `knowledge/checklists/perception-engineering-checklist.md` |
| Paid media launch | `knowledge/playbooks/paid-media-launch-playbook.md`, `knowledge/channels/paid-acquisition.md`, `knowledge/checklists/paid-acquisition-checklist.md` |
| Local claymation ad wedge | `knowledge/playbooks/local-business-claymation-ads.md`, `knowledge/playbooks/ad-creative-best-practices.md`, `knowledge/checklists/creative-production-checklist.md` |
| Meta ads | `knowledge/channels/meta-advertising.md`, `harness/references/meta-ads-rules.md`, `harness/references/meta-ads-api-reference.md` |
| Google ads | `knowledge/channels/paid-acquisition.md`, `harness/references/google-ads-policy-reference.md` |
| TikTok ads | `knowledge/channels/tiktok-algorithm.md`, `harness/references/tiktok-ads-policy-reference.md` |
| Cold outreach | `knowledge/channels/email-lifecycle.md`, `harness/references/cold-email-rules.md` |
| CRO audit | `knowledge/playbooks/conversion-rate-optimization.md`, `knowledge/checklists/cro-audit-checklist.md` |

## Quality Commands

```bash
python scripts/quality_gates/four_us_score.py --file <file>
python scripts/quality_gates/banned_word_check.py --file <file>
python scripts/quality_gates/seo_lint.py --file <file>
python scripts/quality_gates/mutation_risk_lint.py <file>
python scripts/security/sanitize.py <file>
python scripts/quality_gates/agent_readiness_lint.py https://example.com
python -m scripts.quality <file> --policy blog-publish
```

## Runtime Surfaces

| Surface | Purpose |
|---------|---------|
| `kai/runtime/` | Workspace state, modules, policy, memory, workflows |
| `kai/actions/` | Approved action lifecycle and rollback contracts |
| `kai/audits/` | Scored marketing audit engines |
| `kai/creative/` | Briefs, copy recipes, asset requests, QA checks |
| `kai/paid_media/` | Paid campaign controls, monitoring, variants |
| `agent/` | Scheduled autonomous CMO agent and notification loop |
| `gateway/` | Remote runner and connector API surface |

## Public Agent Entry Points

Agents should start with:

1. `llms.txt` for a short machine-readable map.
2. `AGENTS.md` for repo-level operating rules.
3. `README.md` for product overview and install path.
4. `knowledge/_index.md` for framework selection.
5. `harness/ARCHITECTURE.md` for harness internals.

## Products And Sites

| Product | Site Key | Notes |
|---------|----------|-------|
| Kai Marketing OS | kai-cmo-harness | Open-source marketing runtime and knowledge base |
| MeetKai Dashboard | meetkai | Web dashboard under `app-meetkai/` |
| KaiCalls | kaicalls | Kai-owned phone lead capture option for call-driven businesses when fit signals and compliance checks support it |

## Learned Defaults

- Prefer local, dry-run workflows before any external asset generation or outbound send.
- Keep policy references close to ad-writing workflows.
- Track traces and quality labels so the harness can improve from real runs.
- Use `knowledge/_index.md` before loading large framework files.
