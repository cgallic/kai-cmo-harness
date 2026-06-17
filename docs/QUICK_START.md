# Quick Start

Kai Marketing OS gives Claude Code a marketing operating surface inside any product repo. Start with local, dry-run work. Add credentials only when you want approved connector actions.

## Path A: Use The Skills In Claude Code

### 1. Install

```bash
curl -fsSL https://raw.githubusercontent.com/cgallic/kai-cmo-harness/main/install.sh | bash
```

Manual install:

```bash
git clone https://github.com/cgallic/kai-cmo-harness.git /tmp/kai-install
cp -r /tmp/kai-install/harness/skills/kai* ~/.claude/skills/
rm -rf /tmp/kai-install
```

### 2. Open A Product Repo

```bash
cd your-product
claude
```

Run:

```text
/kai-start
```

Kai reads repo files, creates or refreshes `MARKETING.md`, and recommends the first workflow.

### 3. Try One Useful Command

```text
/kai-growth-plan
```

Good first commands:

| Need | Command | Output |
|---|---|---|
| Choose the next marketing move | `/kai-growth-plan` | Stage, channels, constraints, and next actions |
| Write a page | `/kai-landing-page` | Page copy, proof table, CRO hypotheses, approval notes |
| Plan content | `/kai-content-calendar` | Topics, keywords, personas, priorities, kill list |
| Check a funnel | `/kai-cro` | Findings, evidence, gaps, tests |
| Repurpose an asset | `/kai-repurpose` | Quotes, posts, clips, email angles, source map |
| Run quality checks | `/kai-gate` | Four U's, banned words, policy, provenance, risk notes |

## Path B: Copy Kai Into A Client Repo

Use this path when you want the repo itself to carry the marketing system.

```text
your-project/
├── AGENTS.md
├── knowledge/
├── harness/
└── scripts/
```

Copy:

```bash
cp -r kai-cmo-harness/AGENTS.md your-project/
cp -r kai-cmo-harness/knowledge your-project/
cp -r kai-cmo-harness/harness your-project/
mkdir -p your-project/scripts
cp -r kai-cmo-harness/scripts/quality_gates your-project/scripts/
cp -r kai-cmo-harness/scripts/security your-project/scripts/
```

Claude Code will read `AGENTS.md` and use Kai's framework map, contracts, references, and gates.

## What You Get

| Surface | Count | Examples |
|---|---:|---|
| Skill directories | 48 | `/kai`, `/kai-growth-plan`, `/kai-growth-hacker`, `/kai-landing-page`, `/kai-gate` |
| Canonical `kai-*` docs | 45 | API-style skill docs with triggers, inputs, outputs, gates |
| Public router commands | 42 | The commands shown by `/kai` |
| Playbooks | 54 | CRO, experiments, growth hacker OS, pricing, SEO ops, content repurposing |
| Checklists | 36 | Content, ads, growth hacker OS, launch, privacy, mutation risk |
| Frameworks | 27 | Algorithmic Authorship, AEO/GEO, perception engineering |
| Channel guides | 26 | SEO, LinkedIn, email, Meta, TikTok, YouTube, X, podcast |
| Skill contracts | 30 | Blog, ads, cold email, growth hacker OS, experiments, clips, lead dossiers |

## Local Gates

Run these before sharing publishable work:

```bash
python scripts/quality_gates/banned_word_check.py --file draft.md
python scripts/quality_gates/four_us_score.py --file draft.md
python scripts/quality_gates/seo_lint.py --file draft.md
python scripts/quality_gates/mutation_risk_lint.py draft.md
python scripts/security/sanitize.py draft.md
```

Use audit provenance for reports, decks, SEO audits, CRO audits, and other client-facing findings:

```bash
python scripts/quality_gates/audit_provenance_lint.py workspace/audit-folder --audit-dir
```

## Approval Rule

Kai can draft, score, plan, audit, and prepare dry-run artifacts locally. It should not send, upload, enroll, publish, change spend, update CRM records, or mutate a live channel without explicit approval and a saved dry-run artifact.

## Next Pages

- [README](../README.md): product overview and command map.
- [System guide](system/README.md): architecture and runtime docs.
- [Public skill manifest](skill-manifest/README.md): API-style reference for the canonical skills.
- [Governance and quality](system/governance-and-quality.md): instruction contract, source rules, policy gates, and approval doctrine.
