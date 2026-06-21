# Bloomberg MCP & Daily Export Plan

## Bloomberg Data Licensing Constraint

**Critical**: Bloomberg data is licensed per-terminal and cannot be served publicly. The public MarketPulse website must NEVER receive raw Bloomberg data.

## Architecture: Internal Processing → Public Export

```
┌─────────────────┐     ┌──────────────────────┐     ┌─────────────────────┐
│  Bloomberg      │────▶│  Internal MarketPulse │────▶│  Sanitized Export   │
│  Terminal + MCP │     │  (Python backend)      │     │  (JSON/CSV)         │
│                 │     │  - Raw data            │     │  - Scores only      │
│                 │     │  - Full components     │     │  - No raw prices    │
│                 │     │  - Professional calc   │     │  - No Bloomberg IDs │
│                 │     │  - Internal DuckDB     │     │  - Labels + ranges  │
└─────────────────┘     └──────────────────────┘     └─────────────────────┘
                                                               │
                                                               ▼
                                                        ┌──────────────┐
                                                        │  Public Site │
                                                        │  (React app)  │
                                                        └──────────────┘
```

## Bloomberg MCP Provider

### What is MCP?
Model Context Protocol (MCP) is a protocol for connecting AI assistants to data sources. Bloomberg MCP allows Claude Code (and similar tools) to query Bloomberg data through the terminal.

### Implementation

The `BloombergMCPProvider` in `/backend/providers/bloomberg_mcp_provider.py`:

```python
class BloombergMCPProvider(BaseProvider):
    """
    Bloomberg Terminal data provider via MCP.
    
    This provider requires:
    1. A Bloomberg Terminal subscription
    2. Bloomberg MCP installed and running
    3. Access to the MCP server from the machine running MarketPulse
    
    It is designed for internal/Westwood use only.
    """
    name = "bloomberg_mcp"
    tier = "professional"
    
    def __init__(self, mcp_server_path: Optional[str] = None):
        self.mcp_path = mcp_server_path or os.getenv("BLOOMBERG_MCP_PATH")
        # ... connection logic
```

### MCP Connection
```python
async def _mcp_query(self, command: str, securities: List[str], fields: List[str]) -> dict:
    """Send a query to Bloomberg MCP and return parsed results."""
    # Implementation depends on MCP SDK version
    # This is a stub for the interface contract
    pass
```

### Data Available via Bloomberg MCP
- Real-time and historical prices for any security
- Options data (implied vol, skew, put/call ratios)
- Credit spreads (corporate bond spreads by rating)
- Fund flows (mutual fund, ETF flows)
- Futures positioning (COT data)
- Economic data releases
- News (Bloomberg News, not for redistribution)

## Daily Export Workflow

### Step 1: Internal Calculation (on Bloomberg-connected machine)
```bash
# Run at market close (4:35 PM ET)
python -m backend.jobs.update_daily --market sp500 --mode professional
```

This:
1. Fetches all data via Bloomberg MCP
2. Calculates all scores and components
3. Stores in local DuckDB
4. Generates explanation text

### Step 2: Sanitized Export Generation
```bash
# Generate public-safe export
python -m backend.jobs.generate_static_exports --market sp500
```

This creates `/data/static_site_payloads/latest_marketpulse.json`:

```json
{
  "generated_at": "2026-01-15T21:35:00Z",
  "export_version": "1.0",
  "license_notice": "Derived scores only. No raw market data included.",
  "marketpulse": {
    "market": "sp500",
    "timestamp": "2026-01-15T21:35:00Z",
    "composite": {
      "score": 67,
      "regime": "mp4_risk_on",
      "label": "Risk-On",
      "direction": "rising",
      "change_1d": 3,
      "change_1w": -5
    },
    "classic": {
      "score": 72,
      "regime": "mp4_risk_on",
      "change_1d": 3,
      "change_1w": -5,
      "components": [
        {"name": "momentum", "score": 78, "weight": 0.143, "contribution": 11.1},
        {"name": "breadth", "score": 65, "weight": 0.143, "contribution": 9.3},
        {"name": "put_call", "score": 82, "weight": 0.143, "contribution": 11.7},
        {"name": "credit_spreads", "score": 70, "weight": 0.143, "contribution": 10.0},
        {"name": "volatility", "score": 68, "weight": 0.143, "contribution": 9.7},
        {"name": "safe_haven", "score": 71, "weight": 0.143, "contribution": 10.1},
        {"name": "price_strength", "score": 69, "weight": 0.143, "contribution": 9.9}
      ]
    },
    "narrative": {
      "score": 58,
      "regime": "mp3_neutral",
      "change_1d": -2,
      "change_1w": 8,
      "dimensions": {
        "panic": 15,
        "caution": 35,
        "uncertainty": 45,
        "optimism": 55,
        "complacency": 30,
        "euphoria": 10
      },
      "article_count": 47,
      "top_phrases": ["Fed policy", "earnings growth", "inflation data"]
    },
    "positioning": {
      "score": 71,
      "regime": "mp4_risk_on",
      "change_1d": 1,
      "change_1w": -3,
      "components": [
        {"name": "put_call_all", "score": 82, "available": true},
        {"name": "vix_level", "score": 68, "available": true},
        {"name": "credit_spreads", "score": 70, "available": true},
        {"name": "equity_bond_relative", "score": 75, "available": true},
        {"name": "safe_haven_flows", "score": 60, "available": true},
        {"name": "etf_flows", "score": null, "available": false},
        {"name": "futures_positioning", "score": null, "available": false}
      ]
    },
    "confidence": 92,
    "explanation": "Markets are risk-on...",
    "data_quality": {
      "sources_used": 6,
      "sources_available": 6,
      "missing_components": [],
      "substituted_components": [],
      "data_freshness_minutes": 35
    }
  }
}
```

**Key**: This file contains ONLY derived scores. No raw prices, no ticker-level data, no Bloomberg identifiers.

### Step 3: Transfer to Public Site

**Option A: Manual upload**
```bash
scp data/static_site_payloads/latest_marketpulse.json webserver:/var/www/marketpulse/data/
```

**Option B: CI/CD pipeline**
```yaml
# .github/workflows/daily-export.yml
# Runs on self-hosted runner with Bloomberg access
# Generates export, commits to data branch
# Public site pulls from data branch
```

**Option C: API push**
```python
# Push to CDN or cloud storage
# Cloudflare R2, S3, etc.
```

### Public Site Consumption
```javascript
// React frontend loads the static export
const response = await fetch('/data/latest_marketpulse.json');
const data = await response.json();
// Render scores, charts, explanations from sanitized data
```

## Morningstar MCP (Future)

Similar pattern for Morningstar data:
- Internal processing with Morningstar MCP
- Same sanitized export workflow
- Different data strengths (fund flows, analyst data)

## Implementation Checklist

- [x] Provider interface defined
- [x] BloombergMCPProvider stub created
- [ ] Bloomberg MCP SDK integration (needs Bloomberg terminal)
- [x] Daily export format defined
- [x] Export generation job stub created
- [ ] Self-hosted CI/CD runner for daily export
- [ ] Public site static data endpoint
- [ ] Data freshness monitoring
- [ ] Export validation (ensure no raw data leaks)
