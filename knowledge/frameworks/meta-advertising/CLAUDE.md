# Meta Advertising Frameworks

Deep technical documentation of Meta's ad delivery stack: Andromeda, GEM, Lattice, and the Breakdown Effect.

## Files

| File | Use When |
|------|----------|
| `meta-andromeda-deep-dive.md` | Understanding retrieval system, HSNN architecture, creative signals |
| `meta-gem-deep-dive.md` | Understanding generative ads model, InterFormer, knowledge transfer |
| `meta-lattice-deep-dive.md` | Understanding prediction/ranking, MDMO learning, Zipper/Filter |
| `meta-breakdown-effect-deep-dive.md` | Understanding budget allocation, inflection points, scalability |

## Quick Reference

### Meta Ad Delivery Pipeline

```
ANDROMEDA (Retrieval)
    ↓ Filters millions → thousands
LATTICE (Ranking)
    ↓ Predicts performance
GEM (Optimization)
    ↓ Central brain feeding both
AUCTION
    ↓ Final ad selection
```

### Key Metrics

| System | Key Finding |
|--------|-------------|
| **Andromeda** | 10,000x model capacity, creative = targeting signal |
| **GEM** | +5% IG / +3% FB conversions, auto-deployed Q2 2025 |
| **Lattice** | 10% revenue gain, consolidates hundreds of models |
| **Breakdown Effect** | Low CPA often = small scalability ceiling |

### The Breakdown Effect

When the algorithm gives more budget to ads with higher CPAs:
- It's finding the optimal **blended** result
- Low-CPA ads often have **limited scale**
- Evaluate at **ad set level**, not individual ads
- Trust the algorithm's meritocratic distribution

## Related Files

- `channels/meta-advertising.md` - Complete Meta ads guide (main reference)
- `checklists/meta-advertising-checklist.md` - Launch & optimization checklist
