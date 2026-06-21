# Westwood MarketPulse — Frontend Design

## Overview
A finance-media-grade market sentiment dashboard with a MarketWatch/Barron's-quality aesthetic. Clean, authoritative, data-rich but instantly understandable. The design prioritizes clarity, trust, and visual hierarchy.

## Tech Stack
- React 19 + TypeScript + Vite
- Tailwind CSS v3.4.19
- shadcn/ui components
- Recharts for data visualization
- React Router (BrowserRouter)

## Color Palette

### Primary
| Token | Hex | Usage |
|-------|-----|-------|
| `--navy` | `#0A1628` | Primary dark backgrounds, header |
| `--navy-light` | `#1A2B45` | Card backgrounds in dark mode |
| `--slate` | `#64748B` | Secondary text, borders |
| `--white` | `#FFFFFF` | Primary text on dark, backgrounds |

### Regime Colors (Five-Zone Framework)
| Zone | Hex | Tailwind | Usage |
|------|-----|----------|-------|
| MP-1 Capitulation | `#DC2626` | `red-600` | Extreme risk-off |
| MP-2 Defensive | `#F97316` | `orange-500` | Risk-off |
| MP-3 Neutral | `#6B7280` | `gray-500` | Balanced |
| MP-4 Risk-On | `#22C55E` | `green-500` | Risk-on |
| MP-5 Euphoria | `#10B981` | `emerald-500` | Extreme risk-on |

### Accent
| Token | Hex | Usage |
|-------|-----|-------|
| `--blue` | `#2563EB` | Links, active states, primary buttons |
| `--blue-light` | `#3B82F6` | Hover states |
| `--amber` | `#F59E0B` | Warnings, medium confidence |
| `--gold` | `#D4AF37` | Premium features, Westwood branding |

### Background Modes
**Light (default)**:
- Page: `#F8FAFC` (slate-50)
- Card: `#FFFFFF`
- Border: `#E2E8F0`

**Dark**:
- Page: `#0A1628`
- Card: `#1A2B45`
- Border: `#334155`

## Typography

| Element | Font | Weight | Size | Line Height |
|---------|------|--------|------|-------------|
| Brand | Inter | 700 | 24px | 1.2 |
| H1 (Hero Score) | Inter | 800 | 96px | 1.0 |
| H2 (Section) | Inter | 600 | 32px | 1.2 |
| H3 (Card Title) | Inter | 600 | 18px | 1.3 |
| Body | Inter | 400 | 14px | 1.5 |
| Caption | Inter | 400 | 12px | 1.4 |
| Mono (data) | JetBrains Mono | 400 | 13px | 1.4 |

## Spacing
- Page padding: `px-4 md:px-8 lg:px-12`
- Card padding: `p-6`
- Card gap: `gap-6`
- Section gap: `py-12`
- Border radius: `rounded-xl` (12px) for cards, `rounded-full` for badges

## Layout

### Navigation (sticky top-0 z-50)
- Height: 64px
- Background: `--navy` with 95% opacity + backdrop blur
- Left: "WESTWOOD" + "MarketPulse" brand
- Center: Nav links (Dashboard, Methodology, Markets, Admin)
- Right: Theme toggle + "Embed" button

### Footer
- Background: `--navy`
- Height: auto, min 160px
- Three columns: About, Resources, Legal
- Disclaimer text at bottom

## Component Design

### PulseGauge (Hero Score Display)
- Large circular gauge showing composite score (0-100)
- Color-coded fill based on regime
- Center: large score number + regime label
- Bottom: 1-day and 1-week change arrows
- Animation: smooth fill transition on load

### PulseCard (Sub-index Card)
- White card with subtle shadow
- Header: index name (Classic, Narrative, Positioning) + info icon
- Large score number with regime color
- Sparkline mini-chart (last 30 days)
- Change indicators: 1d, 1w, 1m
- Confidence badge

### StackedPulseChart (Main Visualization)
- 4 synchronized area charts sharing x-axis (date)
- Panels: S&P 500, Classic, Narrative, Positioning
- Background zone shading for MP-1 through MP-5
- Tooltip on hover: score, regime, contributors
- Height: 600px total (150px per panel)
- Brush/zoom capability

### RegimeBadge
- Small pill badge with regime color
- Text: "Risk-On", "Neutral", etc.
- Optional: direction arrow

### SourceQualityBadge
- Small badge showing confidence level
- Colors: green (90-100), blue (70-89), yellow (50-69), orange (30-49), red (0-29)
- Text: "High Confidence", "Good", "Moderate", "Low", "Very Low"

### ComponentBreakdown
- Horizontal bar chart showing component contributions
- Each bar segment colored by direction (green=bullish, red=bearish)
- Tooltip with raw value and description
- Sortable by contribution or name

### ExplanationBox
- Light gray background card
- Icon + header: "What Changed Today" or "Why It Matters"
- 2-3 sentences of plain English
- Updated timestamp

## Page Designs

### Home (Landing Page)
- **Hero Section**: Full-width navy background
  - Large PulseGauge (centered)
  - Regime label below
  - One-sentence explanation
  - "Last updated" timestamp
- **Three Cards Row**: Classic, Narrative, Positioning cards
- **Stacked Chart**: Full-width StackedPulseChart
- **Explanation Boxes**: "What Changed" + "Why It Matters" side by side
- **Component Breakdown**: Full-width table
- **Bottom CTA**: Methodology link + embed button

### Methodology Page
- Hero: "How MarketPulse Works"
- Section: The Four Indices (4 cards with descriptions)
- Section: Five-Zone Framework (visual diagram)
- Section: Component Details (expandable accordion)
- Section: Data Sources (table with tiers)
- Section: FAQ

### Markets Page
- Market selector tabs (S&P 500, Nasdaq, Russell, Dow)
- Score cards for selected market
- Multi-market comparison chart
- Component comparison table

### Admin Page (Internal)
- Source status dashboard (grid of provider cards)
- Latest update time
- Raw component values table
- Manual refresh button
- Export generation button
- Diagnostics log

### Embed Demo Page
- Live embed widget preview
- Size selector (small, medium, full)
- Theme selector (light, dark)
- Copy code button

### Backtest Page
- Regime history chart
- Forward returns table by regime
- Caveats and disclaimers

## Animation
- Page load: fade-in with stagger (0.1s delay per section)
- Score changes: smooth number transition (0.5s)
- Gauge fill: animated on mount (1s ease-out)
- Cards: subtle hover lift (translateY -2px, shadow increase)
- Chart tooltips: instant on hover

## Responsive Breakpoints
| Breakpoint | Layout Changes |
|-----------|----------------|
| < 640px (sm) | Single column, stacked cards, simplified gauge |
| 640-1024px (md) | Two columns for cards, full chart |
| > 1024px (lg) | Full layout, side-by-side explanations |
| > 1280px (xl) | Max-width container centered |

## Mock Data
Since the frontend will use mock data by default (connecting to backend API optionally):
- Composite score: 67 (Risk-On)
- Classic: 72, Narrative: 58, Positioning: 71
- 90 days of daily history for all indices
- 7 components with realistic values
- 5 source statuses (3 available, 2 stubs)
- 10 scored articles

## Files to Generate
No external media files needed — all visuals are charts, gauges, and data displays rendered in code.

## Dependencies (beyond template)
- `recharts` — Charting library
- `lucide-react` — Icons (already in template)
- `date-fns` — Date formatting
- `react-router-dom` — Client-side routing
