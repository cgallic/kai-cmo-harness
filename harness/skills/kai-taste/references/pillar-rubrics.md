# Pillar Scoring Rubrics

Use these rubrics when scoring in Audit mode. Each pillar is scored 1-10 based on observable evidence. Score what you can see and measure, not what you assume.

---

## Pillar 1: Deterministic-Stochastic Balance

The policy governing where the system is creative vs where it must be reproducible.

| Score | Observable Criteria |
|:-----:|---------------------|
| **1-2** | No entropy management. Every output is fully stochastic — same input yields wildly different results. No structured outputs, no schema enforcement. Users cannot get reproducible results. Tool calls not used even when factual accuracy matters. "Why did it change?" is a constant user complaint. |
| **3-4** | Some determinism exists (e.g., templates or fixed formatting) but it's applied uniformly — no phase awareness. System doesn't distinguish exploration from execution. Structured outputs exist but are inconsistent. Tool calls available but underused. Users sometimes get unexpected creative flourishes in contexts that need reliability. |
| **5-6** | Entropy injection points are identified and partially managed. System uses structured outputs for some downstream actions. Multi-sample generation exists but reranking criteria are vague. Users can get reproducible results with effort (e.g., seed values, explicit parameters). Phase separation (explore vs execute) is implicit but not enforced. |
| **7-8** | Clear entropy budgeting: high variance for ideation, low variance for final outputs. Structured outputs enforced where reliability matters. Multi-sample + rerank with explicit quality criteria. Tool calls used as determinism anchors for factual claims. Users rarely encounter unwanted variance. Stochastic zones are clearly delineated from deterministic zones. |
| **9-10** | Fully phase-aware pipeline: divergent exploration followed by convergent refinement with hard constraints. Entropy budget is explicit and tunable per task type. Users experience creative freedom when they want it and rock-solid reliability when they need it. System proactively switches modes based on task context without user prompting. Tool verification is automatic for all factual claims. |

**Key evidence to look for:**
- Regenerate the same input 3 times — how much variance?
- Does the system use structured outputs for actionable content?
- Are tool calls used for verifiable claims?
- Can users toggle between exploration and execution?

---

## Pillar 2: Interaction Density

The ratio of actionable affordances to cognitive load — cost per unit of outcome.

| Score | Observable Criteria |
|:-----:|---------------------|
| **1-2** | Empty text box and nothing else. User must know exactly what to ask. No progressive disclosure, no correction affordances. Editing means re-prompting from scratch. Output is monolithic text with no interaction handles. Every iteration costs a full conversation turn. High clarification burden (5+ turns to get something usable). |
| **3-4** | Basic chat with some affordances (copy button, regenerate). Correction still expensive — mostly requires reprompting. Some structure in output (headings, code blocks) but no inline editing. Progressive disclosure absent; all options visible or all hidden. Users manage the interface more than their task. Time-to-value > 3 minutes for typical tasks. |
| **5-6** | Output has some interaction handles (edit sections, accept/reject). Progressive disclosure partially implemented — common features accessible, advanced features available. Correction pathways exist but are clunky (e.g., edit button regenerates entire section). State partially persistent across turns. Time-to-value improving but still requires iteration. |
| **7-8** | Rich affordances: inline editing, scoped refinement, diff-based review, dismiss/accept per section. Progressive disclosure well-tuned — shallow default path, deep options contextually available. Canvas/artifact surface for persistent work. Correction is cheap and precise. Users spend most time on their task, not managing the interface. Time-to-first-value under 60 seconds. |
| **9-10** | Optimal density: every affordance earns its space, none creates overload. Correction cost near-zero (edit-in-place, granular diffs, instant undo, fork/branch). Chat and Canvas work as complementary surfaces — chat for intent, canvas for manipulation. Selective friction preserves agency (IKEA effect) without wasting time. Users reach flow state. Clarification burden < 2 turns. |

**Key evidence to look for:**
- How many turns to first useful output? (Refinement Velocity)
- Can users edit output without re-prompting? (Correction cost)
- Are advanced features hidden until needed? (Progressive disclosure)
- Is work persistent across sessions? (State management)
- Does the user manage the interface or their task? (Overhead ratio)

---

## Pillar 3: Visual Cohesion

The consistency of perceptual grammar across all outputs and interface states.

| Score | Observable Criteria |
|:-----:|---------------------|
| **1-2** | Raw text dumps. No consistent typography, spacing, or hierarchy. Generated content looks foreign to the surrounding UI. No component grammar — outputs are unstyled markdown or plain text. Affordances invisible (can't tell what's clickable). Different outputs look like they came from different products. |
| **3-4** | Basic styling applied (headings, bold, code blocks) but inconsistently. Some design tokens used but not uniformly. Generated content is visually distinguishable from hand-authored content. Affordance signals weak — some buttons look like text, some links look like labels. Layout breaks at different viewport sizes. |
| **5-6** | Component grammar exists and covers most output types. Design tokens consistent within a single output but may vary across features. Affordances generally visible but some edge cases are ambiguous. Typography hierarchy adequate. Generated content mostly blends with native UI. Responsive behavior functional but imperfect. |
| **7-8** | Strong component grammar: all outputs render through defined components with consistent tokens. Typography, spacing, color temperature, and micro-animations reinforce semantic intent. Affordances protected — buttons look like buttons, interactive elements are clearly distinguishable. Generated content is visually native. Responsive at all breakpoints. |
| **9-10** | Pixel-perfect cohesion. Generated content is indistinguishable from hand-authored content within the same UI. Component grammar covers every output type including edge cases (errors, loading states, empty states, uncertainty indicators). Semantic structure drives visual rendering — changing content doesn't break layout. Micro-animations consistent with platform conventions. Confidence-aware UI: uncertainty has visual encoding (blur, opacity, ranges). |

**Key evidence to look for:**
- Place generated output next to hand-authored content — can you tell which is which?
- Are all interactive elements clearly signaled? (Affordance protection)
- Does the layout hold at mobile, tablet, and desktop? (Responsive cohesion)
- Is there a visible component grammar, or does each output render ad hoc?
- Are uncertainty and confidence visually encoded?

---

## Scoring Guidelines

- **Score what you observe**, not what documentation claims
- **Test edge cases**, not just the golden path — cohesion breaks at boundaries
- **Compare to the product's own standards**, not an abstract ideal
- **Half-points allowed** (e.g., 6.5) when evidence straddles two bands
- **Weight the composite** if one pillar is dramatically more important for the product's use case — note the weighting in the scorecard
