# B2C Fintech Design Playbook

> **Use when:** Designing consumer financial apps, payment interfaces, neobank products, or any B2C product where "money is identity."

> **See also:** `b2b-saas-design.md` for enterprise software patterns.

---

## Quick Reference

- Treat financial tools as lifestyle accessories, not utilities (the "streetwearification" of finance)
- Use massive typography (40-120pt) for key numerals - "financial brutalism"
- Optimistic UI is mandatory - show success before server confirms
- Design custom haptic vocabulary for financial events
- "Swipe to Pay" > "Tap to Confirm" (positive friction prevents accidents)

---

## Core Philosophy: The Triangulation

This playbook synthesizes three design studios:

| Studio | Philosophy | Focus |
|--------|------------|-------|
| **Family NYC** | Vibe & Culture | Streetwear aesthetics, "money is identity" |
| **Work & Co** | Invisible Utility | Zero friction, perceived immediacy |
| **Ustwo** | Game Feel | Haptics, sound, emotional mechanics |

**Metaphor Shift:**
- OLD: The Vault (static, heavy, guarded)
- NEW: The Stream (fluid, immediate, social)

---

## Chapter 1: Vibe & Culture (Family NYC)

### 1.1 The Cultural Pivot

Trust in finance was historically established through architecture: marble columns, vault-thick aesthetics. Digital fintechs attempted skeuomorphism (leather textures) then "Trust Blue" palettes.

**The Shift:** Treat financial instruments as lifestyle accessories. Money is identity.

> Just as streetwear brands (Supreme, Off-White) deconstructed luxury fashion with scarcity and community, modern fintech must deconstruct banking by injecting it with culture.

### 1.2 The "Drop" Mentality

**Physical Card as Collectible:**
- Metal cores, glow-in-the-dark plastics, holographic foils
- Personalization (doodles, stickers, laser etching)
- Co-creation deepens emotional bond
- Card signals membership in cultural tribe

**Why Cards Matter:** In rent-based economy where home ownership is elusive, small luxury goods become primary status vessels.

### 1.3 Anti-Design & Brutalism

Reject "Corporate Memphis" (flat, cheerful illustrations). The new aesthetic is raw, bold, unapologetically loud.

#### Typography as Infrastructure

| Element | Traditional | Streetwear Fintech |
|---------|-------------|-------------------|
| Font Choice | Open Sans, Roboto | CashMarket, Agrandir Wide |
| Balance Size | 12-14pt | 40-120pt |
| Feel | Administrative | Editorial |

**Financial Brutalism:** Key numerals dominate the viewport. If a user sends $50, the numbers should fill the screen, celebrating the action.

#### Visual Language

| Element | Traditional | Streetwear |
|---------|-------------|------------|
| Imagery | Stock photos of families | 3D surrealism, liquid metal, gravity-defying objects |
| Palette | Navy Blue, Forest Green | Acid Green, Neon Purple, Stark Black |
| Mode | Light default | Dark default (OLED optimized, club culture) |

### 1.4 Voice & Tone: The "Big Sister" Persona

**Not:** Distant Banker (formal, legalistic, passive)
**Yes:** Big Sister (on your side, speaks your language, holds you accountable)

**Patterns:**
- Conversational microcopy: "That didn't work. Let's try again." (not "Error 404")
- Memetic communication: Emojis as functional UI elements
- Warm wit + radical honesty (Monzo's "straightforward kindness")
- Plain English: Explain APR in actual cost terms

### 1.5 The Feed as Home Screen

Home screen should feel less like spreadsheet, more like social feed.

- **Social Proof:** Transaction graph becomes social graph (Venmo model)
- **Content Partnerships:** "Discover" tab hosts culture (music, fashion drops, artist spotlights)
- **Pay tab:** Utility
- **Discover tab:** Culture

---

## Chapter 2: Invisible Utility (Work & Co)

### 2.1 The Philosophy of Subtraction

> The best interface is often no interface.

Every tap, every millisecond of wait time, every decision point is a tax on cognitive load. Goal: reduce tax to zero.

**The "Ghost":** Systems working in background, anticipating needs before they're articulated.

### 2.2 The Swiss Style Grid

Mathematical grids, asymmetry, obsession with readability.

**Grid as Trust Anchor:** In finance, chaos = risk. Perfect alignment communicates precision/stability. User subconsciously perceives system as secure.

**Asymmetry for Focus:** Guide eye to critical action (Pay button, balance). Generous white/black space reduces cognitive noise.

### 2.3 Optimistic UI

Show successful state *before* server confirms. Essential for "Zero Friction" feel.

**The Flow:**
```
1. User taps "Send"
2. INSTANTLY: UI animates money leaving, "Sent" animation, input clears
3. BACKGROUND: App sends API request
4. RECONCILIATION:
   - Success (99%): Nothing happens (user already saw it)
   - Failure: Graceful rollback + non-intrusive toast
```

**Implementation:** React 19 `useOptimistic` hook, SwiftUI state management

**Why:** Eliminates "spinner anxiety" - makes app feel native, responsive, alive

### 2.4 Managing Failure States

**The "Undo" Pattern:**
- No modal errors blocking user
- Non-intrusive toast: "Could not send. Tap to retry"
- Restore funds to view
- Error handling must be "atomic" - fix issue without navigating away

### 2.5 Skeleton Screens

When data must load, reject spinning wheel. Use animated placeholders mimicking content layout.

**The "Shimmer" Effect:**
- Primes brain for content layout (gray bars for text, circles for avatars)
- Animation moves left-to-right (reading direction = forward momentum)
- Reduces perceived duration vs spinners

### 2.6 Anticipatory Design

**Context-Aware Actions:**
| Context | Surfaced Action |
|---------|-----------------|
| Friday night at bar | "Split Bill" prominent |
| 1st of month | "Pay Rent" contacts surfaced |
| Near recurring payee | "Pay [Name]" suggested |

**Invisible Security:**
- FaceID in background
- PIN only for high-risk (>$500)
- "Positive Friction" makes user feel secure without slowing low-value transactions

**Atomic Notifications:**
- Request for money includes "Pay" button in notification
- Complete task without fully opening app

---

## Chapter 3: Game Feel (Ustwo)

### 3.1 Play Thinking

Distinguish between "Jobs to be Done" (utility) and **"Joy to be Had"** (emotion).

> In fintech where anxiety is default emotion, Joy is competitive advantage.

**"Juice":** Non-essential visual/audio feedback making interactions satisfying. Difference between database update and a *payment*.

### 3.2 Variable Rewards

When user saves money or gets discount:
- Confetti animation
- Haptic pulses
- Unique sound bite

Taps into dopamine loops. Makes financial responsibility feel rewarding.

### 3.3 Haptic Vocabulary

Design custom haptic patterns (AHAP) for specific financial events:

| Event | Haptic Pattern | Implementation |
|-------|----------------|----------------|
| **Large Transfer** | "Heavy" impact (thud) | `UIImpactFeedbackGenerator(style: .heavy)` |
| **Amount Selection** | "Ratchet" clicks (safe dial) | `UISelectionFeedbackGenerator` |
| **Payment Success** | Sharp tap + dissolving purr | Custom AHAP pattern |
| **Scroll** | Light selection ticks | Per-integer feedback |

**Scaling:** Haptic intensity can scale with transaction amount.

### 3.4 Sonic Branding

Sound is fastest sense - bypasses rational brain, hits emotional center.

**Design Principles:**
| Element | Spec | Reasoning |
|---------|------|-----------|
| Payment Sent | Major-key chord resolving upward | Confirms success without reading |
| UI Sounds | Lower-mid frequency range | Sound "expensive" (not tinny/cheap) |
| Error | Low-frequency thud | Conveys solidity |

**Consistency:** Same soundscape across app, push notifications, physical card tap.

> Mastercard research: distinct sonic brand increases trust 4x.

### 3.5 Physics-Based Motion

Objects carry momentum, mass, friction. UI animations must obey physics.

**Spring Animation Parameters:**
```
Mass: 1.0 (standard weight for cards)
Stiffness: 170 (snappy, not sluggish)
Damping: 15 (minimal bounce - precise, not wobbly)
```

**Rubber Band Effect:** When user pulls to refresh or reaches list end, UI stretches. Signals continuous, organic interface.

**Spatial Continuity:** Objects never teleport. Tapping a card should expand/morph into full-screen (Shared Element Transition).

---

## Chapter 4: Synthesis - "Pay a Friend" Flow

### Step 1: The Open

| Layer | Implementation |
|-------|----------------|
| **Vibe** | No splash screen - straight to utility. Deep matte black (OLED). Brand IS the interface. |
| **Utility** | Skeleton screen for 200ms balance fetch. Pay/Request buttons actionable before data loads. |
| **Feel** | Subtle "thrum" haptic on open - heartbeat signaling app is live. |

### Step 2: The Input

| Layer | Implementation |
|-------|----------------|
| **Vibe** | Custom keypad with massive rounded glyphs. "5-0" fills upper half of screen. CashMarket font. Dollar sign superscript/stylized. Looks like poster, not form. |
| **Utility** | Zero latency. Input focused by default. No decimals initially (auto-format if needed). |
| **Feel** | Numbers scale up with spring animation (overshoot and settle). Light haptic per tap. Subtle "click" sound. |

### Step 3: The Context

| Layer | Implementation |
|-------|----------------|
| **Vibe** | Recipient list shows avatars + Cashtags. "Who is this for?" search. "The Crew" (frequent contacts) have larger, glowing avatars. Mimics social media stories. |
| **Utility** | GPS-based prediction surfaces likely recipient first. One-tap selection. |
| **Feel** | Tapping recipient triggers morph transition. Avatar "flies" to top, anchoring context. Shared Element Transition. |

### Step 4: The Gesture

**Swipe to Pay** (not tap)

| Layer | Implementation |
|-------|----------------|
| **Vibe** | Pill-shaped button at bottom, glowing Acid Green. "PAY $50". Looks like unlock slider. |
| **Utility** | Swipe = positive friction. Requires intent. No "Are you sure?" modal needed - gesture IS confirmation. |
| **Feel** | Drag has "weight" (slingshot feel). Screen distorts slightly (stretch). Taptic Engine generates crescendo vibration as button moves up. |

### Step 5: The Release

| Layer | Implementation |
|-------|----------------|
| **Vibe** | Screen flashes (flashbulb). Full-screen animation (3D coins, liquid splash). Feels like loot box unlock. |
| **Utility** | Optimistic success - "Sent" state instantly. Return to home. No spinner. |
| **Feel** | "Ka-ching" major chord. Success haptic (sharp thud + fading resonance). Balance decrements with rolling number animation. |

### Step 6: The Ripple

| Layer | Implementation |
|-------|----------------|
| **Vibe** | Transaction note in large type. Emojis rendered as custom 3D assets. Looks like social post. |
| **Utility** | "Split" button next to feed item anticipates group expense. Invites next transaction. |
| **Feel** | If friend reacts later, particle explosion of hearts/emojis. Loop closed with delight. |

---

## Design Comparison Table

| Feature | Traditional Banking | Streetwear Fintech |
|---------|--------------------|--------------------|
| **Typography** | Conservative (Arial, 12pt) | Massive, Extended (CashMarket, 40pt+) |
| **Palette** | Navy Blue, Grey | Acid Green, Neon Purple, Black |
| **Imagery** | Stock families, handshakes | 3D Surrealism, abstract fluids |
| **Voice** | Formal, passive ("Transaction processed") | Conversational, active ("You paid $50") |
| **Physical Card** | Generic plastic | Metal, glow-in-dark, personalized |
| **Metaphor** | The Vault (security, static) | The Drop (hype, flow, dynamic) |
| **Feedback** | Toast notification | Full-screen celebration + haptics + sound |
| **Confirmation** | "Are you sure?" modal | Swipe gesture (positive friction) |

---

## Sensory Design Specs

| Channel | Element | Design Intent | Technical Spec |
|---------|---------|---------------|----------------|
| **Touch** | Payment Success | Confirmation, relief | `UIImpactFeedbackGenerator(style:.heavy)` + decay |
| **Touch** | Amount Selection | Precision, mechanical | `UISelectionFeedbackGenerator` per integer |
| **Sound** | Send Money | "Expensive," finality | Major triad, synth-pluck, reverb, <500ms |
| **Sight** | Card Swipe | Fluidity, momentum | Spring: Stiffness 300, Damping 20 |
| **Sight** | Screen Transition | Continuity | Shared Element Transition (Hero) |

---

## Checklist

### Vibe & Culture
- [ ] Typography massive for key numerals (40pt+)
- [ ] Custom/extended typeface selected
- [ ] Dark mode as default
- [ ] Acid/neon palette (not Trust Blue)
- [ ] 3D/surreal imagery (not stock photos)
- [ ] Conversational voice (not legalistic)
- [ ] Physical card designed as collectible

### Invisible Utility
- [ ] Optimistic UI implemented for all sends
- [ ] Skeleton screens (no spinners)
- [ ] Swiss grid system applied
- [ ] Context-aware predictions implemented
- [ ] Atomic notifications designed
- [ ] Invisible security (FaceID background)
- [ ] Positive friction for high-value actions

### Game Feel
- [ ] Custom haptic patterns per event type
- [ ] Sonic brand designed (payment sound)
- [ ] Spring physics for all animations
- [ ] Rubber band effect on scroll edges
- [ ] Shared Element Transitions
- [ ] Variable rewards for positive actions
- [ ] 60fps performance validated

### Pay Flow Specific
- [ ] Swipe-to-pay gesture (not tap)
- [ ] Full-screen success celebration
- [ ] Rolling number animation on balance
- [ ] Social feed integration
- [ ] One-tap recipient selection
- [ ] GPS-based prediction

---

## Sources

See original document in `archive/Fintech Design Playbook_ Streetwear, Utility, Game.md` for complete 49-source bibliography including:
- Family NYC case studies
- Work & Co design philosophy
- Ustwo Play Thinking methodology
- Apple Human Interface Guidelines (Haptics)
- Mastercard Sonic Branding research
