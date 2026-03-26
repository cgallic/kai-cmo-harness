# KaiCalls Full Color Token Reference

Complete reference of all CSS custom properties and Tailwind classes.

## Table of Contents
1. [Background Colors](#background-colors)
2. [Brand Colors](#brand-colors)
3. [Text Colors](#text-colors)
4. [Status Colors](#status-colors)
5. [Badge Colors](#badge-colors)
6. [Table Colors](#table-colors)
7. [Shadow & Elevation](#shadow--elevation)
8. [Transitions](#transitions)
9. [Z-Index Scale](#z-index-scale)

## Background Colors

| Token | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| `--background` | #12121A | `bg-background` | Main page background |
| `--card` | #181B23 | `bg-card` | Card surfaces |
| `--secondary` | #23263B | `bg-secondary` | Secondary surfaces, inputs |
| `--muted` | #23263B | `bg-muted` | Muted backgrounds |
| `--surface-primary` | #181B23 | `bg-surface-primary` | Primary surfaces |
| `--surface-secondary` | #23263B | `bg-surface-secondary` | Secondary surfaces |
| `--surface-elevated` | #2A2D3E | `bg-surface-elevated` | Elevated elements |
| `--surface-overlay` | rgba(0,0,0,0.8) | `bg-surface-overlay` | Modal overlays |
| `--kai-bg-main` | #12121A | `bg-kai-bg-main` | Main background |
| `--kai-bg-card` | #181B23 | `bg-kai-bg-card` | Card background |
| `--kai-bg-card-dark` | #23263B | `bg-kai-bg-card-dark` | Darker card variant |
| `--kai-bg-card-hover` | #21223A | `bg-kai-bg-card-hover` | Card hover state |
| `--modal-bg` | #181B23 | custom | Modal background |
| `--popover` | #181B23 | `bg-popover` | Popover background |
| `--sidebar` | #181B23 | `bg-sidebar` | Sidebar background |

## Brand Colors

| Token | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| `--primary` | #5C8CFF | `bg-primary`, `text-primary` | Primary actions |
| `--kai-blue` | #5C8CFF | `text-kai-blue`, `bg-kai-blue` | Brand blue |
| `--accent` | #C68BF8 | `bg-accent`, `text-accent` | Accent elements |
| `--kai-purple` | #C68BF8 | `text-kai-purple`, `bg-kai-purple` | Brand purple |
| `--kai-btn-primary` | #3575F6 | `bg-kai-btn-primary` | Primary button |
| `--kai-indigo` | #9AA7FF | custom | Indigo accent |
| `--ring` | #5C8CFF | `ring-ring` | Focus rings |

## Text Colors

| Token | Hex | Tailwind | Usage |
|-------|-----|----------|-------|
| `--foreground` | #F7F7FA | `text-foreground` | Primary text |
| `--kai-text-primary` | #F7F7FA | `text-kai-text-primary` | Primary text |
| `--muted-foreground` | #A7A9BE | `text-muted-foreground` | Secondary text |
| `--kai-text-muted` | #A7A9BE | `text-kai-text-muted` | Muted text |
| `--kai-text-placeholder` | #6B6D76 | custom | Placeholder text |
| `--kai-text-table-heading` | #B0B2C3 | custom | Table headers |
| `--card-foreground` | #F7F7FA | `text-card-foreground` | Card text |
| `--primary-foreground` | #FFFFFF | `text-primary-foreground` | Text on primary |
| `--secondary-foreground` | #FFFFFF | `text-secondary-foreground` | Text on secondary |
| `--accent-foreground` | #FFFFFF | `text-accent-foreground` | Text on accent |
| `--destructive-foreground` | #FFFFFF | `text-destructive-foreground` | Text on destructive |

## Status Colors

| Status | Background | Text | Usage |
|--------|------------|------|-------|
| Success | `--kai-success-bg` #1F3D2B | `--kai-success-text` #34D399 | Positive states |
| Error | `--kai-error-bg` #391919 | `--kai-error-text` #FF4B4B | Error states |
| Warning | `--kai-warning-bg` #3A2911 | `--kai-warning-text` #FFC04B | Warning states |
| Info | `--kai-info-bg` #1A1D28 | `--kai-info-text` #5C8CFF | Info states |
| Destructive | - | `--destructive` #FF4B4B | Destructive actions |

### Status Badge Classes

```css
.status-success { background: var(--kai-success-bg); color: var(--kai-success-text); }
.status-error { background: var(--kai-error-bg); color: var(--kai-error-text); }
.status-warning { background: var(--kai-warning-bg); color: var(--kai-warning-text); }
.status-info { background: var(--kai-info-bg); color: var(--kai-info-text); }
```

## Badge Colors

### Temperature Badges (Lead Scoring)

| Temperature | Background | Text | Class |
|-------------|------------|------|-------|
| Hot | #FF4B4B33 | #FF6B6B | `.badge-hot` |
| Warm | #FFC04B33 | #FFD76B | `.badge-warm` |
| Cold | #4B7BFF33 | #6B93FF | `.badge-cold` |

### Intent/Action Badges

| Type | Background | Text | Class |
|------|------------|------|-------|
| Intent | #24294B | #80B8FF | `.badge-intent` |
| Action | #321C5F | #B39DFF | `.badge-action` |

### Special Badges

| Type | Background | Text | Class |
|------|------------|------|-------|
| AI Handled | rgba(92,140,255,0.3) | #90B8FF | `.ai-handled-badge` |
| Low Score | #FF784433 | #FF9D6B | `.low-score-badge` |

## Table Colors

| Token | Hex | Usage |
|-------|-----|-------|
| `--kai-table-border` | rgba(255,255,255,0.1) | Table borders |
| `--kai-hover-row` | #21223A | Row hover |
| `--kai-selected-row` | #1A1D28 | Selected row |
| `--kai-slate` | #23263B | Table header bg |

### Table Classes

```css
.table-row { background: var(--card); }
.table-row:hover { background: var(--kai-hover-row); }
.table-row-selected { background: var(--kai-selected-row); border-left: 3px solid var(--kai-blue); }
```

## Border Colors

| Token | Value | Tailwind | Usage |
|-------|-------|----------|-------|
| `--border` | rgba(255,255,255,0.07) | `border-border` | Standard borders |
| `--modal-border` | rgba(255,255,255,0.1) | custom | Modal borders |
| `--kai-table-border` | rgba(255,255,255,0.1) | `border-kai-table-border` | Table borders |
| `--sidebar-border` | rgba(255,255,255,0.07) | `border-sidebar-border` | Sidebar borders |

## Shadow & Elevation

| Token | Value | Tailwind |
|-------|-------|----------|
| `--shadow-sm` | 0 1px 2px rgba(0,0,0,0.3) | `shadow-elevation-sm` |
| `--shadow-md` | 0 4px 6px rgba(0,0,0,0.3) | `shadow-elevation-md` |
| `--shadow-lg` | 0 10px 15px rgba(0,0,0,0.3) | `shadow-elevation-lg` |
| `--shadow-xl` | 0 20px 25px rgba(0,0,0,0.3) | `shadow-elevation-xl` |

## Transitions

| Token | Value | Tailwind |
|-------|-------|----------|
| `--transition-fast` | 150ms | `duration-fast` |
| `--transition-normal` | 200ms | `duration-normal` |
| `--transition-slow` | 300ms | `duration-slow` |

## Z-Index Scale

| Token | Value | Tailwind |
|-------|-------|----------|
| `--z-dropdown` | 50 | `z-dropdown` |
| `--z-modal` | 100 | `z-modal` |
| `--z-toast` | 150 | `z-toast` |

## Chart Colors

For data visualization, use these semantic chart colors:

| Token | Hex | Usage |
|-------|-----|-------|
| `--chart-1` | #5C8CFF | Primary data series |
| `--chart-2` | #C68BF8 | Secondary data series |
| `--chart-3` | #34D399 | Positive/success data |
| `--chart-4` | #FFC04B | Warning/attention data |
| `--chart-5` | #FF4B4B | Negative/error data |

## Gradient Utilities

### Brand Gradient

```css
.bg-gradient-kai {
  background: linear-gradient(90deg, var(--kai-blue) 0%, var(--kai-purple) 100%);
}

.text-gradient-kai {
  background: linear-gradient(90deg, var(--kai-blue) 0%, var(--kai-purple) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}
```

### Heat Bar Gradients (Lead Temperature)

```css
.heat-bar-hot {
  background: linear-gradient(180deg, #FF3333 0%, #FF6600 50%, #FFAA00 100%);
  box-shadow: 0 0 16px rgba(255, 75, 75, 0.6);
}

.heat-bar-warm {
  background: linear-gradient(180deg, #FFCC00 0%, #FF9900 50%, #FF6600 100%);
  box-shadow: 0 0 10px rgba(255, 192, 75, 0.4);
}

.heat-bar-cold {
  background: linear-gradient(180deg, #6B7280 0%, #4B5563 100%);
  opacity: 0.6;
}
```
