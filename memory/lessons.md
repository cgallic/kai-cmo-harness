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

- [2026-06-09] (active) **When writing for any channel** → binary clichés ("It's not X, it's Y") slip past subjective scoring; run the voice-pattern regexes in `harness/skills/kai-gate/SKILL.md` step 3. Source: kai-gate doctrine. Enforced: kai-gate skill (manual)
- [2026-06-09] (active) **When citing AI-search studies** → never reuse study percentages (30-50%, 115%) as client promises; report sampled visibility with volatility caveats. Source: seo_lint overclaim history. Enforced: scripts/quality_gates/seo_lint.py

## Learned lessons

- [2026-06-09] (active) **When a gate fails twice on one piece for the same dimension** → stop rewriting whole drafts; fix only the named failing dimension, then escalate to a human with the diagnosis if the third run fails. Source: pipeline retry policy. Enforced: none (prose only — promotion candidate)
- [2026-06-09] (promoted) **When a draft contains template placeholders** → natural-language placeholders ("insert your", "your business name here", "TBD") must block publish, not just `[company]`-style brackets. Source: engine.py gap audit. Enforced: scripts/content/placeholders.py (promoted 2026-06-10, EC-06)
- [2026-06-09] (active) **When GSC/GA4 credentials are missing** → brief generation and performance checks fail quietly with an error dict; run `python scripts/doctor.py` first and treat missing connectors as data gaps, never as zeros. Source: performance_check.py audit. Enforced: scripts/doctor.py (preflight warning)
- [2026-06-09] (active) **When building Meta ad creatives** → use instagram_user_id, never instagram_actor_id (wrong field is accepted, ad silently fails). Source: memory/edge-cases.md EC-01. Enforced: none
- [2026-07-12] (active) **When editing a public site with multiple repos or domain aliases** → match the live response to its deployed artifact before choosing the edit target; a linked hosting project is not proof of production authority. Source: operator correction during MeetKai homepage work. Enforced: none
- [2026-10-03] (active) **When a plan proposes a new site, satellite network, or new content program** → run `python -m scripts.seo.portfolio` first; across 62 properties, 4 established ones carried 93% of ~640 search clicks/mo and 52 earned under 2. Work the refresh queue on `invest` properties before building anything new. Source: Kai CMO evidence file + Search Console pull, 2026-10-02. Enforced: /kai-page-refresh skill + page-refresh ECO work type
- [2026-10-03] (active) **When reporting search wins** → split brand from non-brand before any claim and say when no conversions are tracked; a property whose growth is mostly its own brand name, or whose clicks map to no conversion, has not shown marketing ROI. Source: KaiCalls growth was mostly branded; 4 money sites record zero conversions. Enforced: scripts/seo/striking_distance.py (brand split), refresh_tracker grades non-brand only
