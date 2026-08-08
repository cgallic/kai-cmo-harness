# The Refiner Layer: 10-Step Protocol

The Refiner Layer sits between raw model output and the user-facing artifact. It converts stochastic generation into deterministic, authored behavior. This is where taste becomes repeatable.

The model is not the product. The model is a probabilistic component inside a deterministic refinement system. The Refiner is what makes output feel inevitable rather than generated.

---

## Step 1: Define the Taste Contract as Constraints, Not Adjectives

Translate "brand voice" and "quality" into testable constraints:
- Reading level (e.g., Flesch-Kincaid 8th grade)
- Verbosity ceiling (max tokens/words per section)
- Required sections and structure (headings, summary, steps, caveats, citations)
- Prohibited moves (never hide uncertainty, never use banned phrases, never omit sources)
- Formatting grammar (markdown conventions, component types allowed)
- Interaction rules (when to ask questions vs proceed, when to show alternatives)

**Why:** Adjectives like "clean" and "professional" are not enforceable. Constraints are. A taste contract is a design system expressed as rules.

**Bad signal:** The contract says "make it good" or "be creative" — these are not constraints, they are wishes.

---

## Step 2: Separate Divergence from Convergence

Make the pipeline explicitly two-phase:

**Divergent phase (exploration):**
- Multiple candidates allowed
- Higher entropy/temperature
- Broader sampling strategies (nucleus/top-p)
- Goal: surface range of possibilities

**Convergent phase (refinement):**
- Low variance, strong constraints
- Schema-bound outputs
- Deterministic formatting
- Goal: lock down the final artifact

Never mix these phases. Exploring while refining creates volatility. Refining while exploring kills creativity.

**Why:** Iterative self-feedback with phase separation improves preference outcomes vs one-shot generation. The system needs room to explore before it commits.

**Bad signal:** The system generates a single candidate and immediately renders it as final output. Or: the system keeps generating alternatives after the user has committed to a direction.

---

## Step 3: Generate a Structured Intent Representation

Before drafting any prose or UI, derive a structured intent object:

```
{
  goal: "what the user is trying to accomplish",
  constraints: ["hard limits from the taste contract"],
  audience: "who will consume this output",
  deliverable_type: "answer | plan | code | document | UI component",
  risk_level: "low | medium | high (determines verification depth)",
  uncertainty_zones: ["areas where the model is not confident"]
}
```

This intent object becomes the stable substrate of the artifact. In a Canvas/Artifact model, it persists across turns. In Chat, it would otherwise be buried in conversation history.

**Why:** Without structured intent, the model guesses what the user wants from ambiguous natural language. Structured intent is a compact control vector that reduces downstream entropy.

**Bad signal:** The system jumps straight to prose without establishing what it's building, for whom, or under what constraints.

---

## Step 4: Draft into Intermediate Representation, Not Final UI

Have the model produce an IR — not polished prose or rendered UI:

```
IR = {
  sections: [
    { type: "summary", claims: [...], confidence: 0.9 },
    { type: "steps", items: [...], dependencies: [...] },
    { type: "caveats", items: [...], severity: [...] },
    { type: "citations", sources: [...], verified: true/false }
  ],
  ui_components: ["code_block", "table", "callout"],
  uncertainty_map: { section_id: confidence_score }
}
```

The IR separates content from presentation. It can be projected into Chat, Canvas, or any other surface.

**Why:** Drafting directly into final UI couples content to presentation. When you need to change the rendering (different device, different context), you lose the semantic structure. IR makes the system surface-agnostic.

**Bad signal:** The model outputs a wall of markdown that is simultaneously the content and the UI. Changing the format requires regenerating everything.

---

## Step 5: Run a Critic Pass with Explicit Rubrics

Use a second model call (or the same model in critic mode) to grade the IR against:

- **Correctness:** Are claims supported? Are there contradictions?
- **Constraint compliance:** Does the output meet the taste contract from Step 1?
- **Tone violations:** Does it match the target voice? Any banned words or AI slop?
- **Formatting violations:** Does the structure match the required schema?
- **Affordance hazards:** Are calls-to-action ambiguous? Can users tell what's clickable?
- **Uncertainty gaps:** Are low-confidence claims marked? Or smoothed over?

The critic catches errors before the user pays the correction cost.

**Why:** The system corrects itself before the user has to. This is "support efficient correction" applied internally. Every error the critic catches is one less edit the user makes.

**Bad signal:** No self-review. The first draft goes directly to the user. Or: the critic exists but uses vague rubrics ("is this good?") instead of testable criteria.

---

## Step 6: Refine via Diffs, Not Rewrites

Output a patch/diff against the IR, not a complete rewrite:

```diff
- section.summary.claims[2]: "Revenue grew 40%"
+ section.summary.claims[2]: "Revenue grew 40% (source: Q3 earnings report, p.12)"
```

Diffs are explainable, controllable, and auditable. Rewrites are volatile — the user can't tell what changed or why.

**Why:** Full rewrites destroy user trust because the output shifts unpredictably. Diffs let users accept/reject individual changes, preserving agency. This also reduces outcome volatility (a key failure metric).

**Bad signal:** Every refinement regenerates the entire output. The user notices wording changed in sections they already approved.

---

## Step 7: Anchor Truth with Tools, Then Re-Render

When factuality matters, route to tools — don't let the model guess:

- **Retrieval:** Search knowledge base, documentation, or web for source material
- **Calculation:** Use a calculator for numeric claims
- **Database:** Query live data instead of recalling training data
- **Verification:** Cross-check claims against authoritative sources

After tool results return, regenerate only the dependent sections of the IR.

**Why:** Tool calls are determinism anchors. They convert "the model thinks X" into "the system verified X." This is the boundary where taste enforces "don't guess when you can check."

**Bad signal:** The model states facts with high confidence but never verifies them. Or: tool results are available but the model ignores them in favor of its own generation.

---

## Step 8: Compile to UI Using Component Grammar

Render the IR through a constrained set of components, not raw text:

| IR Type | Component | Rules |
|---------|-----------|-------|
| Summary | `<Summary>` | Max 3 sentences, bold key claim |
| Steps | `<StepList>` | Numbered, verb-first, one action per step |
| Warning | `<Callout type="warning">` | Yellow/orange, icon, never hidden |
| Code | `<CodeBlock lang="x">` | Syntax highlighted, copy button |
| Citation | `<Citation>` | Inline link + footnote, verified badge if checked |
| Table | `<DataTable>` | Sortable headers, aligned numbers |
| Uncertainty | `<ConfidenceBand>` | Visual encoding: blur, opacity, or explicit range |

Every component inherits design tokens (typography, spacing, color) from the product's design system.

**Why:** Raw LLM output should never directly become UI. Compiling through a component grammar ensures visual cohesion, affordance protection, and consistent behavior across all outputs. This is where Pillar 3 (Visual Cohesion) becomes mechanically enforced.

**Bad signal:** Generated content renders as unstyled markdown. Or: every output looks slightly different because there's no component grammar governing rendering.

---

## Step 9: Guarantee Correction Affordances at the Surface

Expose correction as primary interaction, not a fallback:

- **Edit-in-place:** Click any section to modify directly
- **Scoped refinement:** "Refine this section" without regenerating everything
- **Accept/reject diffs:** Per-change approval, not all-or-nothing
- **Dismiss:** Clear way to suppress unwanted AI interventions
- **Undo:** Reversible at every step
- **Fork:** Branch from any point to explore alternatives without losing current state

Correction affordances are not optional features. They are the primary interaction surface for uncertain systems.

**Why:** AI will be wrong. The product must make correction cheap, not treat it as user failure. "Support efficient correction" is a first-class design requirement, not a nice-to-have.

**Bad signal:** The only way to change output is to re-prompt from scratch. Or: the "edit" button exists but regenerates the entire artifact.

---

## Step 10: Instrument Taste as Feedback Loops

Log everything needed to close the loop:

| Signal | What It Measures | How to Use It |
|--------|-----------------|---------------|
| Time-to-first-value | How quickly users reach useful output | Optimize onboarding and first-run experience |
| Edit operations per session | Correction density | Identify sections that consistently need cleanup |
| Regeneration count | Output quality misses | Find patterns in what triggers regeneration |
| Diff rejection rate | Refinement quality | If users reject diffs, the critic pass is miscalibrated |
| Dismissal events | Relevance and intrusion | If users dismiss > 30% of suggestions, reduce proactivity |
| Abandonment after render | Output fails to meet intent | Investigate what was shown vs what was expected |
| Session graph structure | Workflow efficiency | Loops = thrashing; short paths = good taste |

Feed these signals back into:
- Critic rubric calibration (Step 5)
- Taste contract updates (Step 1)
- Component grammar refinement (Step 8)
- RLDF training data (preference pairs from edit traces)

**Why:** Taste is not a one-time decision. It's a closed-loop system. Without instrumentation, you're flying blind — guessing what users want instead of measuring it.

**Bad signal:** No telemetry. The team debates taste in design reviews based on personal preference instead of behavioral data.

---

## What the Refiner Buys You

1. **The model is not the product.** The model is a probabilistic component inside a deterministic system. Brand and experience stability come from the Refiner, not from hoping the model behaves consistently.

2. **No retraining required for taste changes.** Constraints, critique rubrics, component grammar, and rendering rules do most of the visible work. Updating taste = updating the Refiner config, not fine-tuning a foundation model.

3. **Chat-to-Canvas becomes an architecture shift.** The artifact (IR + rendered components) is the primary state. Conversation becomes one control surface among many. The Refiner makes this possible by maintaining structured state that survives across interaction modes.
