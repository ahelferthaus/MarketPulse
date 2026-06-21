# Website Embed Plan

## Overview
MarketPulse provides an embeddable widget that can be included on third-party websites (Westwood's site, advisor websites, etc.) without requiring API keys or backend integration.

## Embed Types

### Type 1: Small Card (Minimal)
**Dimensions**: 300x200px (responsive)
**Content**:
- Composite score (large number)
- Regime label (colored badge)
- One-sentence explanation
- "Powered by Westwood MarketPulse" link
- Updated timestamp

**Use case**: Sidebar widget, small embeds, email-compatible preview

### Type 2: Medium Card (Standard)
**Dimensions**: 600x400px (responsive)
**Content**:
- Composite score with gauge visualization
- Three sub-index mini-bars (Classic, Narrative, Positioning)
- Regime label + direction arrow
- One-sentence explanation
- "What changed today" snippet
- Source quality badge
- Methodology link

**Use case**: Blog posts, article insets, dashboard widgets

### Type 3: Full Article (Interactive)
**Dimensions**: 100%x800px (responsive, full-width)
**Content**:
- Large headline score with animated gauge
- Three full sub-index cards with scores and changes
- Stacked chart (mini version)
- Component breakdown table
- "Why it matters" explanation
- Source quality section
- Full methodology link

**Use case**: Dedicated MarketPulse page sections, featured articles

## Embed API Endpoints

### HTML Widget Endpoint
```
GET /api/v1/embed/marketpulse?market=sp500&size=medium&theme=light
```

Returns an HTML snippet with inline styles:
```html
<div class="wmp-embed wmp-embed-medium" data-market="sp500">
  <style>/* inline styles */</style>
  <div class="wmp-score">67</div>
  <div class="wmp-regime wmp-regime-mp4">Risk-On</div>
  <!-- ... -->
  <script>
    // Optional: auto-refresh every 5 minutes
    setInterval(() => refreshWidget('.wmp-embed'), 300000);
  </script>
</div>
```

### JSON Widget Endpoint
```
GET /api/v1/embed/marketpulse.json?market=sp500
```

Returns JSON for custom rendering:
```json
{
  "widget_type": "marketpulse",
  "market": "sp500",
  "timestamp": "2026-01-15T21:35:00Z",
  "composite_score": 67,
  "regime": "mp4_risk_on",
  "regime_label": "Risk-On",
  "explanation": "Markets are risk-on...",
  "classic": {"score": 72, "change_1d": 3},
  "narrative": {"score": 58, "change_1d": -2},
  "positioning": {"score": 71, "change_1d": 1},
  "confidence": 92,
  "source_quality": "high"
}
```

## Integration Methods

### Method 1: Iframe Embed (Recommended)
```html
<iframe 
  src="https://marketpulse.westwood.com/embed?market=sp500&size=medium&theme=light"
  width="600" 
  height="400"
  frameborder="0"
  title="Westwood MarketPulse"
></iframe>
```

**Pros**: Secure, isolated, no CSS conflicts
**Cons**: Less flexible styling

### Method 2: JavaScript Embed
```html
<div id="marketpulse-widget"></div>
<script 
  src="https://marketpulse.westwood.com/embed.js" 
  data-market="sp500"
  data-size="medium"
  data-theme="light"
  data-target="marketpulse-widget"
></script>
```

**Pros**: Flexible, can access parent page context
**Cons**: Potential CSS conflicts, requires JavaScript

### Method 3: Static JSON + Custom Rendering
```javascript
fetch('https://marketpulse.westwood.com/api/v1/embed/marketpulse.json?market=sp500')
  .then(r => r.json())
  .then(data => renderCustomWidget(data));
```

**Pros**: Full control over rendering
**Cons**: Requires custom implementation

## Embed Configuration Parameters

| Parameter | Options | Default | Description |
|-----------|---------|---------|-------------|
| `market` | sp500, nasdaq100, russell2000, dow | sp500 | Market to display |
| `size` | small, medium, full | medium | Widget size |
| `theme` | light, dark, auto | light | Color theme |
| `show_chart` | true, false | false | Include mini chart |
| `show_methodology` | true, false | true | Show methodology link |
| `refresh` | number (minutes) | 5 | Auto-refresh interval |
| `branding` | full, minimal, none | full | Westwood branding level |

## CORS and Security

### CORS Policy
```python
# FastAPI CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Embeds are public
    allow_methods=["GET"],
    allow_headers=["*"],
    max_age=3600,
)
```

### Rate Limiting
- Embeds: 100 requests/hour per IP
- JSON widget: 60 requests/hour per IP
- Use CDN caching for static embed responses

### Content Security
- All embed HTML is sanitized
- No JavaScript execution in iframe embeds
- CSS is inline and scoped to widget class

## Performance Targets

| Metric | Target |
|--------|--------|
| Time to First Byte | < 200ms |
| Widget render time | < 500ms |
| JSON response size | < 5KB |
| HTML response size | < 30KB |
| CDN cache hit rate | > 95% |

## Implementation Status

- [x] Embed API endpoints defined
- [x] Widget size variants designed
- [x] JSON widget format specified
- [ ] Iframe embed page created
- [ ] JavaScript embed script created
- [ ] Embed styling (light/dark themes)
- [ ] Rate limiting implemented
- [ ] CDN configuration
- [ ] Embed usage analytics
