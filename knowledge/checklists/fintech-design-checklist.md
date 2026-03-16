# B2C Fintech Design Checklist

> **Use when:** Designing or reviewing consumer financial apps, payment flows, neobank interfaces, or any B2C product where money movement needs to feel premium.

---

## Pre-Design: Strategic Foundation

- [ ] Product positioned as lifestyle accessory (not utility)
- [ ] Target "streetwear" demographic defined
- [ ] Competitive audit completed (Cash App, Monzo, Revolut)
- [ ] Physical card strategy defined (material, personalization)
- [ ] Sonic brand brief created
- [ ] Haptic vocabulary documented

---

## Chapter 1: Vibe & Culture

### Typography
- [ ] Custom or extended typeface selected (not system fonts)
- [ ] Key numerals at 40-120pt ("financial brutalism")
- [ ] Font feels "editorial" not "administrative"
- [ ] Dollar signs stylized (superscript, custom treatment)

### Color & Mode
- [ ] Dark mode is default (OLED optimized)
- [ ] Palette includes "acid" colors (neon green, electric purple)
- [ ] No "Trust Blue" (navy, forest green)
- [ ] High contrast validated for WCAG

### Visual Language
- [ ] 3D/surreal imagery (not stock photos)
- [ ] Fluid abstractions (liquid metal, gravity-defying objects)
- [ ] Assets animate and breathe
- [ ] No "Corporate Memphis" illustrations

### Voice & Tone
- [ ] "Big Sister" persona (ally, peer, accountable)
- [ ] Error messages are conversational
- [ ] Plain English for complex terms (APR explained as actual cost)
- [ ] Emojis as functional UI elements where appropriate
- [ ] Copy feels like group chat, not legal disclaimer

### Social Integration
- [ ] Transaction feed feels like social feed
- [ ] Emojis/notes in transactions displayed prominently
- [ ] "The Crew" (frequent contacts) highlighted
- [ ] Content/culture tab exists beyond pure utility

---

## Chapter 2: Invisible Utility

### Performance
- [ ] Optimistic UI for all send/transfer actions
- [ ] Skeleton screens (never spinners)
- [ ] Shimmer animation left-to-right
- [ ] <200ms perceived latency for core actions

### Grid & Layout
- [ ] Swiss-style mathematical grid applied
- [ ] Generous whitespace/blackspace
- [ ] Eye guided to primary action (Pay button, balance)
- [ ] No layout shift on data load

### Failure Handling
- [ ] Non-intrusive toast for errors (not modal)
- [ ] "Undo" pattern for failed transactions
- [ ] Atomic error handling (fix without navigating away)
- [ ] Graceful rollback animations

### Predictions & Context
- [ ] GPS-based suggestions implemented
- [ ] Time-based suggestions (rent on 1st, split bill Friday night)
- [ ] Frequent payees prioritized
- [ ] "Next Best Action" surfaced

### Security UX
- [ ] FaceID/biometrics in background
- [ ] PIN only for high-value transactions (>$500)
- [ ] "Positive friction" for risky actions
- [ ] No unnecessary authentication interrupts

### Notifications
- [ ] Action buttons in notification (approve, pay)
- [ ] Can complete tasks without full app launch
- [ ] Request notifications show amount and requester

---

## Chapter 3: Game Feel

### Haptics
- [ ] Custom haptic for payment success (heavy impact + decay)
- [ ] Selection haptic for amount input (ratchet/dial feel)
- [ ] Haptic intensity scales with transaction amount
- [ ] Scroll has subtle selection feedback

### Sound
- [ ] Payment success sound designed (major-key, upward resolve)
- [ ] Sound in lower-mid frequency range ("expensive")
- [ ] UI sounds consistent across all touchpoints
- [ ] Sound works with haptic timing

### Motion
- [ ] Spring physics (not linear easing)
- [ ] Parameters: Mass 1.0, Stiffness 170, Damping 15
- [ ] Rubber band effect on scroll edges
- [ ] Shared Element Transitions (no teleporting)
- [ ] 60fps validated (dropped frames = bugs)

### Celebration
- [ ] Variable rewards for positive actions
- [ ] Full-screen animation for payments
- [ ] Rolling number animation on balance changes
- [ ] Confetti/particle effects for milestones

---

## Payment Flow Specific

### Input Screen
- [ ] Amount fills majority of viewport
- [ ] Custom keypad (not system)
- [ ] Numbers animate in (spring overshoot)
- [ ] Haptic + sound per keypress
- [ ] Auto-focus on input field

### Recipient Selection
- [ ] Avatar-first display (not text list)
- [ ] Frequent contacts elevated
- [ ] One-tap selection for predicted recipient
- [ ] Morph transition to confirmation

### Confirmation
- [ ] **Swipe gesture** (not tap button)
- [ ] Pill/slider appearance (unlock metaphor)
- [ ] Drag has "weight" (slingshot resistance)
- [ ] Haptic crescendo during drag
- [ ] Screen stretch/distortion effect

### Success State
- [ ] Optimistic (instant, no spinner)
- [ ] Full-screen animation (coins, splash, confetti)
- [ ] Ka-ching sound + success haptic
- [ ] Balance decrements with rolling animation
- [ ] Auto-return to home/feed

### Social Loop
- [ ] Transaction appears in feed immediately
- [ ] Note/emoji displayed prominently
- [ ] "Split" action available on feed item
- [ ] Reaction animations for friend responses

---

## Physical Card

- [ ] Premium material (metal, unique plastic)
- [ ] Distinguishing feature (glow, holographic, weight)
- [ ] Personalization option (colors, patterns, engraving)
- [ ] Unboxing experience designed
- [ ] Card feels like "membership" not "access"

---

## Performance Benchmarks

| Metric | Target | Method |
|--------|--------|--------|
| Perceived latency | <200ms | Optimistic UI |
| Animation framerate | 60fps | Profiler validation |
| Skeleton duration | <500ms | Backend optimization |
| Haptic latency | <50ms | System API |
| Sound latency | <100ms | Pre-loaded audio |

---

## Anti-Patterns (Avoid These)

- [ ] **No spinners** - Use skeleton screens
- [ ] **No "Are you sure?" modals** - Use swipe gesture
- [ ] **No Trust Blue** - Use cultural/acid colors
- [ ] **No stock photos** - Use 3D/surreal imagery
- [ ] **No legal-speak** - Use conversational tone
- [ ] **No silent success** - Always celebrate with sound+haptic
- [ ] **No linear animations** - Use spring physics
- [ ] **No system keyboards for amounts** - Custom keypad

---

## Testing Protocol

### User Testing
- [ ] "Vibe check" - Does it feel cool or corporate?
- [ ] Payment flow timed (<10 seconds total)
- [ ] Emotional response to success state measured
- [ ] Sound tested in noisy/quiet environments

### Technical Testing
- [ ] 60fps across all animations
- [ ] Haptic patterns on multiple device models
- [ ] Optimistic UI rollback tested
- [ ] Skeleton screens on slow network

### A/B Candidates
- [ ] Swipe vs tap confirmation
- [ ] Haptic intensity levels
- [ ] Success animation variations
- [ ] Sound on/off impact on completion
