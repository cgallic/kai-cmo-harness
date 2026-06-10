# Lessons

Trigger→advice pairs Kai has learned. One line each, dated, generalized beyond the incident that caused them.

## Format

```
- [YYYY-MM-DD] (status) **When <trigger>** → <advice>. Source: <where this came from>. Enforced: <gate/check path, or none>
```

Statuses: `candidate` (mined, unreviewed) · `active` (reviewed, true) · `promoted` (now enforced by a gate/checklist — entry kept for history) · `retired` (no longer true; say why).

Rules:
- Generalize at write time. Name the class of situation, not the client or campaign.
- One line per lesson. If it needs a paragraph, it belongs in `memory/edge-cases.md` or a framework doc.
- Never delete — mark `retired` with a reason. Git keeps history.
- During `/kai-retro`, any `active` lesson that has fired 3+ times must be proposed for promotion (see graduation ladder in `memory/MEMORY.md`).

## User-specified lessons

- [2026-06-10] (active) **When adding any LLM-judged gate or check** → never hard-code a single LLM vendor; route completions through `scripts/quality_gates/llm_judge.py` so the gate runs with whatever provider key the operator has (Gemini/Anthropic/OpenAI, `KAI_LLM_PROVIDER` to pin). Source: human correction on four_us_score.py. Enforced: scripts/quality_gates/llm_judge.py + tests/test_llm_judge.py

- [2026-06-09] (active) **When writing for any channel** → binary clichés ("It's not X, it's Y") slip past subjective scoring; run the voice-pattern regexes in `harness/skills/kai-gate/SKILL.md` step 3. Source: kai-gate doctrine. Enforced: kai-gate skill (manual)
- [2026-06-09] (active) **When citing AI-search studies** → never reuse study percentages (30-50%, 115%) as client promises; report sampled visibility with volatility caveats. Source: seo_lint overclaim history. Enforced: scripts/quality_gates/seo_lint.py

## Learned lessons

- [2026-06-09] (active) **When a gate fails twice on one piece for the same dimension** → stop rewriting whole drafts; fix only the named failing dimension, then escalate to a human with the diagnosis if the third run fails. Source: pipeline retry policy. Enforced: none (prose only — promotion candidate)
- [2026-06-09] (promoted) **When a draft contains template placeholders** → natural-language placeholders ("insert your", "your business name here", "TBD") must block publish, not just `[company]`-style brackets. Source: engine.py gap audit. Enforced: scripts/content/placeholders.py (promoted 2026-06-10, EC-06)
- [2026-06-09] (active) **When GSC/GA4 credentials are missing** → brief generation and performance checks fail quietly with an error dict; run `python scripts/doctor.py` first and treat missing connectors as data gaps, never as zeros. Source: performance_check.py audit. Enforced: scripts/doctor.py (preflight warning)
- [2026-06-09] (active) **When building Meta ad creatives** → use instagram_user_id, never instagram_actor_id (wrong field is accepted, ad silently fails). Source: memory/edge-cases.md EC-01. Enforced: none
