# Voice Gate

A reusable line-editor pass. Works on any client that has a written voice guide. Complements the rule-based `/content-gate` in the Kai CMO harness.

## What it solves

The rule-based `/content-gate` scores banned words, SEO structure, and Four U's. It cannot see subjective voice issues — sing-songy cadence, signature-move overuse, meta-commentary that breaks flow, receipt gaps, voice drift from the client's actual language patterns. Those are line-editor-class problems.

Voice Gate closes that gap. It reads the client's voice guide as an authoritative rubric and scores the draft against it, returning a structured markdown editorial report with severity, category, location, verbatim quote, and rule cited for every issue.

## Required inputs

- **Draft** (required) — any markdown file.
- **Voice guide** (required) — a `*-writing-guide.md` that lists DOs/DON'Ts, forbidden vocab, signature-move caps, and structural patterns. Canonical shape: `clients/<client>/outputs/personas/<writer>-writing-guide.md`.
- **Persona file** (optional) — biographical context. Helps the judge calibrate but is not required.

## Output

A single markdown report saved next to the draft as `<draft-stem>.VOICE-GATE.md`. Sections:

- **Header** — verdict (PASS / HOLD / FAIL), word count, overall diagnosis.
- **Summary table** — every issue in one row with severity, category, location, one-liner.
- **Detailed issues** — each issue with verbatim quote, voice-guide rule cited, diagnosis, recommended direction.
- **What's working** — ≥3 specific passages that earn their place.
- **Systemic patterns** — 2–4 rewrite prompts for the next draft.
- **Signature-move count check** — table of capped moves with occurrence counts.

Canonical example: `voice-gate/examples/example-blog-voice-gate-report.md`.

## How to invoke

Run inside Claude Code:

```
/voice-gate <draft-path>
/voice-gate <draft-path> --voice-guide <path> --persona <path> --max-issues 25
```

Claude Code's OAuth session executes the judge prompt inline — no external API, no Python, no env vars, no wrapper script. See `voice-gate/SKILL.md` for the full contract.

## Client usage pattern

Each client points at their own voice guide. The judge prompt is client-agnostic — it reads the voice guide as the rubric at runtime. No code changes are needed to onboard a new client.

To onboard:

1. Create `clients/<client>/outputs/personas/<writer>-writing-guide.md` with DOs/DON'Ts, forbidden vocab, signature-move caps, and structural patterns. Use `clients/GrowthModeOn/outputs/personas/lexie-smith-writing-guide.md` as the structural template.
2. (Optional) Create `clients/<client>/outputs/personas/<writer>-persona.md` for biographical context.
3. Run `/voice-gate <draft-path>`. The skill auto-discovers the voice guide by walking up from the draft to the nearest `outputs/personas/` directory.

One judge prompt serves all clients.

## Pipeline position

```
draft agent  →  /content-gate (rule-based)  →  /voice-gate (LLM-as-judge)  →  human review  →  publish
```

Run `/content-gate` first — it is cheap and catches mechanical rule violations. Run `/voice-gate` second — it scores the subjective dimension. Human review remains the final filter. Voice Gate is not a publish-without-human step.

## What Voice Gate does NOT do

- **Rewrites.** Fixes are direction only. The human editor owns the revision.
- **Fact-checking.** Claims-vs.-reality is out of scope. Fact verification is a separate pass.
- **Embedding-based voice similarity.** That's Option C in the research doc (voice-centroid against a corpus). Deferred until Voice Gate's misses justify building it.
- **Mechanical rule scoring.** That's `/content-gate`'s job — run that first.
- **Approvals or publishing.** The report is a briefing for the human editor, not a publish signal.
