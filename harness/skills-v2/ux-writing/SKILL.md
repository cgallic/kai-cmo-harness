---
name: ux-writing
description: Create user-centered, accessible interface copy (microcopy) for digital products including buttons, labels, error messages, notifications, forms, onboarding, empty states, success messages, and help text. Use when writing or editing any text that appears in apps, websites, or software interfaces, designing conversational flows, establishing voice and tone guidelines, auditing product content for consistency and usability, reviewing UI strings, or improving existing interface copy. Applies UX writing best practices based on four quality standards — purposeful, concise, conversational, and clear. Includes accessibility guidelines, research-backed benchmarks (sentence length, comprehension rates, reading levels), expanded error patterns, tone adaptation frameworks, and comprehensive reference materials.
---

# ux-writing (v2, goal-oriented)

Third-party skill (content-designer/ux-writing-skill, MIT; see `UPSTREAM.md` and `LICENSE`). The complete, unmodified rule set is `references/ux-writing-rules.md` in this folder. This file states the goal and the binding constraints; every rule in the reference still applies. Paths that the rules mention (`references/`, `templates/`, `examples/`, `docs/`) are relative to this skill folder.

## Objective

Ship interface copy (buttons, labels, errors, notifications, forms, onboarding, empty states, success messages, help text) that is purposeful, concise, conversational and clear, matches the product's voice, and works for every user, including screen-reader users.

## Done when

- The context is written down before drafting: the user goal, the business goal, technical constraints (character limits, components) and the user's likely emotional state and stakes.
- Every string follows its pattern from the rules: buttons as `[Verb] [object]`, errors as `[What failed]. [Why]. [What to do].`, success as `[Action] [result]`, empty states as explanation plus a CTA.
- Each string has gone through the four editing phases (purposeful, concise, conversational, clear) and meets the length benchmarks: buttons 2-4 words (6 max), titles 40 characters max, errors 12-18 words including the fix, instructions 20 words max.
- For an audit or edit, each change is shown before and after, with the rule it applies. `references/content-usability-checklist.md` is run on the final set.

## Constraints

- Sentence case. Second person. Active voice by default. Consistent terminology across the whole flow.
- No generic labels ("OK", "Submit", "Click here"), no blame words ("invalid", "illegal"), no bare error codes, and no dead ends: every error names a recovery step.
- Plain language at a 7th-8th grade reading level for a general audience (9th-10th for professional tools). Define a technical term the first time it appears.
- Accessible by default: descriptive link and button text, visible labels (never placeholder-only), and meaning never carried by colour alone. See `references/accessibility-guidelines.md`.
- Tone shifts with context and stakes; voice does not. High-stakes confirmations state the consequence plainly and make backing out easy.
- Keep existing brand voice rules when the product has them. Use `references/voice-chart-template.md` only when none exist.

## Context

- Full patterns, tone tables, benchmarks and editing process: `references/ux-writing-rules.md`.
- Extended patterns: `references/patterns-detailed.md`. Before/after examples: `examples/real-world-improvements.md`. Fillable templates: `templates/`. Figma MCP workflow: `docs/figma-integration.md`.
- Out of scope: long-form marketing content (blog posts, ads, emails). Route those to `/kai-write` and the content frameworks.

## Escalate when

- The product has no voice guidance and the tone choice would change meaning (for example, playful versus formal for a financial product). Ask once.
- A string cannot meet its length limit without dropping required legal or safety information. Keep the information and flag the limit.
