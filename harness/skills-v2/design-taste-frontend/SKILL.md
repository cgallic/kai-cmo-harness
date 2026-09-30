---
name: design-taste-frontend
description: Anti-slop frontend skill for landing pages, portfolios, and redesigns. The agent reads the brief, infers the right design direction, and ships interfaces that do not look templated. Real design systems when applicable, audit-first on redesigns, strict pre-flight check.
---

# design-taste-frontend (v2, goal-oriented)

Third-party skill (Leonxlnx/taste-skill, MIT; see `UPSTREAM.md` and `LICENSE`). The complete, unmodified rule set is `references/taste-rules.md` in this folder. This file states the goal and the binding constraints; every rule in the reference still applies.

## Objective

Ship a landing page, portfolio or redesign that does not read as templated or AI-generated, built for the audience the brief implies, using the brand material that already exists.

## Done when

- A one-line design read (page kind, audience, vibe, design-system or aesthetic family) and the three dials (`DESIGN_VARIANCE`, `MOTION_INTENSITY`, `VISUAL_DENSITY`) are stated before any code, with reasons.
- For a redesign, the audit in section 11 of `references/taste-rules.md` is written before any change: brand tokens, IA, content blocks, patterns to keep and retire, and the current dial reading.
- The page is rendered and screenshotted at mobile and desktop widths, in light and dark mode, and every box in the Final Pre-Flight Check (section 14) is honestly ticked. A failed box means the work is not done.

## Constraints

- Zero em dashes or en dashes anywhere visible, including alt text and button labels.
- One theme per page, one accent colour, and one documented corner-radius system.
- Hero: headline of at most 2 lines on desktop, subtext of at most 20 words, CTA visible without scrolling, no more than 4 text elements, and top padding of 96px at most.
- Eyebrow labels: at most one per three sections. No split headers, no three consecutive image-and-text splits, no layout family used twice, and no duplicate CTA intent.
- Real images, from an image tool, supplied assets, then seeded placeholders. No div-built fake screenshots, no hand-drawn decorative SVG, and no pills or captions over photos.
- No invented precise numbers, fake testimonials or placeholder brands. Copy is re-read and every broken or cute-but-wrong line is rewritten.
- WCAG AA contrast on every button, form field, label and helper text. Honour `prefers-reduced-motion` above motion level 3. Use no `window` scroll listeners.
- Official packages when the brief maps to a real design system (section 2), and one system per project.
- Redesigns never silently change URLs, primary nav labels, form field names, the logo or legal copy.

## Context

- Full rules, dial tables, bans, block-library schema and install commands: `references/taste-rules.md`.
- Out of scope: dashboards, data tables, multi-step forms, code editors and native apps (section 13). Say so, and apply only the marketing-page parts.

## Escalate when

- The design read genuinely diverges (for example, Linear-clean versus experimental). Ask exactly one question.
- Redesign mode is unclear between preserve and overhaul. Ask once.
- No image source is available. List the exact placements and sizes that need images instead of shipping a text-only page.
