# Frontend Design Methodology

> **Use when:** Designing or refining user-facing web apps, product dashboards, AI workspaces, Remotion slide scenes, landing-page interfaces, or any frontend artifact that needs dense, responsive, accessible, and visually coherent UI.

## Purpose

Frontend design in Kai should turn intent into an interface people can operate without explanation. The goal is more than decoration. The goal is a surface where hierarchy, interaction, state, and motion reduce correction cost.

This methodology consolidates the design rules from:

- `knowledge/design/b2b-saas-design.md`
- `knowledge/design/b2c-fintech-design.md`
- `harness/skills/kai-taste/SKILL.md`
- `harness/skills/kai-taste/references/pillar-rubrics.md`

Use the domain playbooks for specialized taste. Use this file as the default frontend methodology and as the citation target for video, app, and manifest workflows.

---

## Operating Principles

### 1. Function Sets The Taste Contract

Define the interface's job before choosing a visual style.

- Identify the primary user action for each screen.
- Decide which zones must be deterministic: navigation, forms, data, controls, warnings, legal copy.
- Decide where expression is allowed: empty states, success states, onboarding, scene transitions, product storytelling.
- Convert adjectives into constraints: row height, type scale, spacing scale, contrast target, animation timing, breakpoint behavior.
- Protect affordances. Buttons must look like buttons, links must look like links, and destructive actions must be visibly distinct.

### 2. Density Serves Workflow

High-density UI is good when users are comparing, scanning, triaging, or repeating actions. Low-density UI is good when users are learning, deciding, or recovering from an error.

Use this density split:

| Surface | Density Rule |
|---|---|
| Work views | High information per pixel, tight controls, compact tables, persistent filters |
| Decision views | Moderate density, clear comparison structure, visible tradeoffs |
| Transitional views | Lower density, stronger personality, clear next action |
| High-risk flows | Add selective friction through review, swipe, confirmation, or undo |

Do not make users manage the interface more than the task. Progressive disclosure is the default: common actions stay visible; advanced controls appear in context.

### 3. Cohesion Beats Novelty

Visual cohesion means the interface has one perceptual grammar across all states.

- Use a shared token set for color, type, spacing, radius, shadows, borders, motion, and focus rings.
- Render repeated patterns through components rather than one-off styling.
- Keep content and controls visually separate.
- Make generated or dynamic content look native to the surrounding UI.
- Let semantic structure drive styling: titles, metadata, body copy, actions, warnings, and evidence should have stable visual roles.

Novelty belongs only where it clarifies, rewards effort, or strengthens brand memory. Novelty that hides meaning is a defect.

---

## UI Density Rules

### Layout

- Put the primary action in the dominant scan path.
- Keep toolbars stable in height and location across states.
- Use compact spacing for repeated controls, tables, queues, and editor surfaces.
- Avoid nested cards. Use cards for repeated items, modals, and framed tools only.
- Prefer full-width bands, sidebars, panels, grids, and tables for product work.
- Do not use marketing-style hero layouts for operational tools unless the first screen is truly a landing page.

### Tables And Lists

- Provide a density toggle when users may work in both review and execution modes.
- Use 48px rows for compact work queues and 56-64px rows when rows include secondary metadata.
- Keep primary identifiers visible through sticky columns, pinned summaries, or card headers.
- On mobile, collapse wide tables into cards or folding rows instead of shrinking text below readable sizes.
- Keep bulk actions, filters, and selection state visible after scroll.

### Controls

- Use icons for common tool actions, with accessible labels or tooltips.
- Use segmented controls for mode changes.
- Use toggles or checkboxes for binary settings.
- Use sliders, steppers, or numeric inputs for quantities.
- Use menus for option sets.
- Keep destructive actions separated from high-frequency actions.

---

## Interaction States

Every interactive component must define and test these states:

- Default
- Hover
- Focus-visible
- Active or pressed
- Selected
- Disabled
- Loading
- Empty
- Error
- Success
- Pending or optimistic

### State Behavior

- Acknowledge direct manipulation within 100ms.
- Use optimistic UI for low-risk reversible actions.
- Use skeleton screens for data loading. Avoid generic spinners when layout is knowable.
- Provide undo or retry for background failures.
- Do not block repetitive workflows with animations, modals, or confirmations unless the action is high-risk.
- Keep pending state local to the affected object when possible.
- Preserve object permanence. Cards, rows, and panels should morph, expand, or move rather than disappear without context.

### Motion Timing

| Motion Type | Target |
|---|---:|
| Tap feedback, toggles, small controls | 120-160ms |
| Local panel, row, or tooltip transitions | 180-240ms |
| Major view transitions | 280-400ms |
| High-attention success or celebration | Under 900ms unless user can skip |

Dropped frames are bugs. Motion should support continuity, not hide latency.

---

## Visual Cohesion Rules

### Typography

- Use one type system with clear roles for display, heading, body, label, numeric, and code text.
- Match type scale to container scale. Compact panels need compact headings.
- Keep letter spacing at `0` unless a brand typeface requires otherwise.
- Do not scale type directly with viewport width.
- Make numeric values easy to compare through tabular numbers or stable alignment.

### Color And Contrast

- Define semantic colors for background, surface, border, text, muted text, accent, success, warning, error, and focus.
- Do not build a one-hue interface unless the brand explicitly requires it.
- Use contrast to show hierarchy before using saturation.
- Reserve high-saturation color for action, alert, or brand moments.
- Validate text and essential icons against WCAG contrast targets.

### Shape, Border, Shadow

- Keep radius consistent. Product UI cards should usually stay at 8px radius or less unless the design system says otherwise.
- Use borders for structure and shadows for elevation.
- Do not use shadows as random decoration.
- Keep elevation consistent: popovers, menus, modals, side panels, and cards should have distinct depth rules.

### Media And Scenes

For Remotion slides, product videos, and visual demos:

- Make the product, feature, or object legible in the first frame of the scene.
- Use real screenshots, recordings, or generated bitmap assets when the viewer needs to understand the thing itself.
- Keep captions, numbers, and UI labels inside safe margins.
- Limit simultaneous motion. One dominant motion path per scene is usually enough.
- Validate readable text at the final export size and in the editor.

---

## Responsive Constraints

Responsive design is not shrinking a desktop screen. It is preserving task structure across viewport sizes.

### Required Breakpoints

Check at minimum:

- 375px mobile
- 768px tablet
- 1024px small desktop
- 1440px desktop

### Rules

- Define stable dimensions for boards, grids, toolbars, counters, tiles, and fixed-format scenes.
- Use `minmax()`, `clamp()` for spacing or containers, aspect ratios, and max-widths to prevent layout drift.
- Keep critical controls reachable on mobile without horizontal page scroll.
- Move dense comparison into cards, accordions, tabs, or horizontal object-level scroll on small screens.
- Never let button text, labels, badges, or long words overflow their containers.
- Keep sticky headers, bottom bars, and side panels from covering content.
- Test empty, short, typical, long, and error content in each responsive layout.

---

## Accessibility Rules

Accessibility is part of frontend quality, not a compliance pass at the end.

- Use semantic HTML before ARIA.
- Provide keyboard access for every interactive control.
- Make focus-visible states obvious and consistent.
- Ensure reading order matches visual order.
- Pair icons with labels, `aria-label`, or tooltips where meaning is not universal.
- Respect reduced-motion preferences.
- Do not encode status by color alone.
- Keep touch targets at least 44px where touch is expected.
- Confirm contrast for text, icons that communicate state, and focus indicators.
- Write error messages that identify the field, the issue, and the recovery action.

---

## Verification Protocol

Run this before shipping a frontend artifact, scene, or manifest-cited design output.

### 1. One-Second Test

Show the screen for one second. A new viewer should identify:

- What this screen is
- What changed
- What the primary action is

If not, reduce visual competition or strengthen hierarchy.

### 2. State Matrix

Exercise every state for primary components:

- Loading with slow network or delayed data
- Empty data
- Long content
- Validation error
- Permission error
- Success
- Optimistic update failure
- Disabled action with reason

### 3. Responsive Pass

Capture or inspect mobile, tablet, and desktop. Check:

- No overlap
- No clipped labels
- No hidden primary action
- No unintended horizontal page scroll
- Stable toolbar and navigation positions
- Product screenshots or videos remain legible

### 4. Accessibility Pass

Verify:

- Keyboard-only operation
- Visible focus order
- Contrast
- Labels for controls
- Reduced-motion behavior
- Screen-reader-friendly semantics for forms, dialogs, menus, and tables

### 5. Performance And Motion Pass

Check:

- Interaction response within 100ms for local feedback
- Smooth animation at target device class
- Skeleton or local pending state for delayed data
- No animation blocks repeated work
- Media assets load at the required resolution without blur or layout shift

### 6. Taste Score

For AI or generated interfaces, score against the `kai-taste` pillars:

| Pillar | Minimum Useful Target |
|---|---:|
| Deterministic-Stochastic Balance | 7/10 |
| Interaction Density | 7/10 |
| Visual Cohesion | 7/10 |

If a score is below 7, fix the highest-friction finding before adding polish.

---

## Handoff Checklist

- [ ] Primary action is visible and unambiguous.
- [ ] UI density matches the workflow.
- [ ] All core components have complete interaction states.
- [ ] Dynamic content renders through a consistent component grammar.
- [ ] Responsive layouts pass mobile, tablet, and desktop checks.
- [ ] Accessibility basics pass for keyboard, focus, labels, contrast, and reduced motion.
- [ ] Loading, empty, error, success, and optimistic states are implemented.
- [ ] Motion is smooth, purposeful, and non-blocking.
- [ ] Screenshots, recordings, or rendered scenes are verified at final size.
- [ ] Design choices are traceable to a taste contract or domain playbook.
