# Theoretical Foundations of Design Taste

This document distills the theoretical grounding from the full 40,000-word research corpus. Read this when you want to understand *why* the framework works, not just *how* to apply it.

---

## Information Theory Foundation

Taste is a high-dimensional entropy-reduction engine.

**Shannon Entropy:** `H(X) = -SUM p(x_i) * log(p(x_i))`
- Model output begins as a high-entropy state — stochastic tokens with low predictable structure
- Taste reduces entropy by imposing semantic constraints on the output space
- The goal is not minimum entropy (that's sterile determinism) but *controlled* entropy: high where creativity matters, low where reliability matters

**Semantic Density:** `rho = E[task_utility] / (tokens * pixels * time)`
- Not brevity — maximizing mutual information between what is shown and the user's next correct action
- High semantic density = high information value per unit of cognitive cost
- Low semantic density = syntactic noise that burns working memory to decode

**Birkhoff's Aesthetic Measure:** `M = O / C` (Order / Complexity)
- Complexity = preliminary attention effort required to perceive
- Order = formal associations (symmetry, repetition, harmony) that reward attention
- High-taste design maximizes M: delivering order that rewards the attention investment

**Surprisal:** `I(x) = log(1/p(x))`
- Unexpected symbols trigger mismatch detection in the hippocampus
- High surprisal in the wrong context = confusion and cognitive overload
- High surprisal in the right context = insight and delight (the "Aha!" moment)

---

## Cognitive Load Theory

Taste is the discipline of minimizing extraneous load while preserving germane load.

**Three types of cognitive load:**

| Type | Definition | Taste Implication |
|------|-----------|-------------------|
| **Intrinsic** | Difficulty inherent to the task itself | Cannot be reduced by design — accept it |
| **Extraneous** | Difficulty imposed by bad presentation | The primary target of taste optimization. Layout noise, redundant verbosity, ambiguity, inconsistent affordances |
| **Germane** | Effort that builds useful mental models | Must be preserved. Selective friction and the IKEA effect generate germane load |

**Key principle:** When intrinsic load is high (complex task), extraneous load must be near zero, or the user's working memory overflows. This is why complex AI tools need *more* taste discipline, not less.

**Working memory constraint:** ~3-5 chunks under typical conditions. Any interface that depends on recall rather than recognition burns scarce capacity. This is why:
- Chat (recall-dependent) is worse than Canvas (recognition-based) for complex tasks
- Persistent spatial layouts beat scrolling conversation history
- Component grammar beats raw text — visual patterns are recognized, not decoded

---

## Neuroscience of Insight and Temporal Pacing

The "Aha!" moment has a specific neural signature that taste must support.

**Insight sequence:** Preparation -> Incubation -> Illumination -> Verification

**Neural signature of illumination:**
- Gamma-wave bursts (~40 Hz) in the right anterior superior temporal gyrus
- Dopamine release in the reward system (nucleus accumbens)
- Hippocampus acts as mismatch detector — fires when input diverges from expectation
- Ventral occipitotemporal cortex processes visual pattern recognition

**Temporal pacing thresholds:**

| Latency | Cognitive Effect | Design Implication |
|---------|-----------------|-------------------|
| < 0.1s | Direct causality — system registered intent | Immediate visual acknowledgment (loading state, cursor change) |
| 0.5-1.5s | Thought continuity preserved | Show provisional structure: skeleton, partial plan, outline |
| 1.5-2.0s | Perceived "thoughtfulness" — optimal for complex creative tasks | Prevent oracle feeling; position system as collaborative partner |
| > 10s | Attention disengages; user starts managing waiting | Must expose progress, allow partial action, or lose the user |

**The oracle failure mode:** Delivering polished output too fast forecloses thinking. Users over-trust because surface coherence bleeds into perceived correctness (halo effect). The system should pace delivery to support — not replace — the user's cognitive process.

---

## Locus of Control and the IKEA Effect

Automation increases capability but can reduce perceived agency. Taste must optimize the user's control experience.

**IKEA effect:** People value outcomes more when they invest labor in creating them.
- **Fragile:** Disappears if the task is too difficult (abandoned) or if the creation is disassembled shortly after
- **Mechanism:** Effort Heuristic — users judge value by metabolic energy invested
- **Implication:** Total friction removal kills ownership. Selective friction preserves it.

**Selective friction mechanisms:**
1. **Constraint-first shaping:** Force 1-3 invariants (goal, audience, risk tolerance) before generation — converts vague intent into a compact control vector
2. **Editable scaffolds:** Present outputs as manipulable structures (cards, nodes, parameters) rather than monolithic prose — labor becomes selection and adjustment
3. **Commit gates:** Require confirmation only at irreversible or high-impact transitions

**Sense of Agency (SoA):** The belief that one is the cause of an action.
- High SoA: stable activity in anterior prefrontal cortex
- Disrupted SoA: stress markers increase (amylase activity), cognitive dissonance
- AI products disrupt SoA when outcomes feel externally authored despite user initiation

**Self-Determination Theory:** Undermining autonomy and competence reduces intrinsic motivation and persistence. A "tasteful" system must optimize the user's control experience as a closed-loop variable.

---

## Chat to Canvas: The Skeuomorphism Parallel

The transition from Chat to Canvas mirrors the skeuomorphism-to-flat-design shift.

| Era | Transitional Metaphor | Native Idiom | Problem Solved |
|-----|----------------------|-------------|----------------|
| Mobile UI (2007-2013) | Skeuomorphism (leather, glass textures) | Flat Design (minimalism, content-first) | Digital literacy bootstrapping |
| Generative AI (2022-present) | Chat (linear conversation) | Canvas (spatial workspaces, persistent artifacts) | Managing multi-dimensional state in 1D stream |

**Why Chat is skeuomorphic:**
- Conversation is a familiar metaphor that onboards quickly
- But it forces 1D serialization of multi-dimensional problems
- Every return to context becomes a search problem (recall, not recognition)
- Working memory constraints make this expensive

**Why Canvas is the native idiom:**
- Object permanence: state persists and is visible
- Direct manipulation: reversible actions, spatial organization
- Distributed cognition: externalization reduces working memory tax
- Spatial memory: distinct positions reduce comparison errors and facilitate retrieval

**The historical lesson:** Metaphors help early adoption, then become friction when precision and throughput dominate. Taste must remain subordinate to function.

---

## Confidence-Aware UI

When the system cannot express uncertainty, "taste" degrades into a surface-level style that amplifies automation bias.

**The Uncanny Valley of Agency:** A system appears highly agentic but proves inscrutably unreliable. The mismatch produces overtrust, brittle reliance, and eventual betrayal. Users don't just lose confidence — they lose it catastrophically.

**Uncertainty visual conventions:**

| Convention | Visual Metaphor | Mental Model |
|-----------|----------------|-------------|
| **Blur** | Visual resolution | Certainty = precision; uncertainty = lack of resolve |
| **Transparency** | Physical solidity | Certainty = solid object; uncertainty = absence |
| **Strikethrough** | Editorial notation | Uncertainty = rejection of the claim |
| **Static/Noise** | Signal interference | Uncertainty = interference in the signal |
| **Fill/Volume** | Liquid capacity | Uncertainty = substance that fills a container |

**Protocol for confidence-aware design:**
1. Calibrate internal confidence (temperature scaling to align predicted with empirical correctness)
2. Represent uncertainty as decision-relevant information (not all uncertainty, just what changes action selection)
3. Use abstention and ranges when stakes justify it (conformal prediction for coverage guarantees)
4. Expose provenance and limits (sources, reasoning, not just conclusions)
5. Never smooth uncertainty language — "this is likely correct based on X" beats "this is correct"

**The test:** If users accept outputs because they *sound* right rather than because they verified, the system has Trust Distortion — the most dangerous failure mode.

---

## RLDF: Reinforcement Learning from Design Feedback

RLDF adapts RLHF to optimize for design-quality objectives rather than general helpfulness.

**Feedback signals (not just thumbs-up/down):**
- Edit traces — what users change (behavioral preference labels)
- Latency-to-correction — how quickly users fix errors (urgency signal)
- Abandonment after render — output failed to meet intent (hard negative)
- Diff acceptance rate — which refinements users keep vs reject

**Style weight hierarchy:**
1. **Base weights:** General competence
2. **Brand adapter:** Cross-product invariants (brevity norms, epistemic humility, structural grammar)
3. **Product-mode adapters:** Domain constraints, UI projection rules (chat vs canvas)
4. **User delta:** Small, bounded personalization vectors

**Process Reward Models (PRMs):** Evaluate intermediate generation steps, not just final output. This identifies exactly where taste breaks down — which step in the pipeline produced the error.

**Governance constraint:** RLDF metrics must be paired with counter-metrics. Optimizing refinement velocity without a correction density guard invites degenerate strategies (forcing acceptance, hiding edit affordances). Goodhart's Law applies: once proxies become targets, systems learn to game them.
