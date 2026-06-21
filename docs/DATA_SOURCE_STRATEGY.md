# Westwood MarketPulse — Data Source Strategy

## Three Operating Modes

### Mode A: Public / Free (Default)
**Goal**: Full functionality with zero API costs. Used for development, demo, and public website.

| Data Type | Source | Cost | Limitations |
|-----------|--------|------|-------------|
| Stock prices | yfinance | Free | Rate limits, delayed 15min |
| VIX | yfinance | Free | Real-time |
| Credit spreads | FRED | Free | Daily, morning update |
| Treasury yields | FRED | Free | Daily |
| Put/Call ratios | CBOE (web scrape) | Free | Daily, limited history |
| News headlines | RSS feeds (Yahoo, MarketWatch, etc.) | Free | Delayed, filtered |
| Safe haven assets | yfinance (TLT, GLD, DXY) | Free | Delayed 15min |
| Mock data | Internal generator | Free | Realistic synthetic data |

### Mode B: Premium / API
**Goal**: Higher data quality, more components, faster updates. Requires API subscriptions.

| Data Type | Source | Est. Cost | Improvement |
|-----------|--------|-----------|-------------|
| All price data | FMP (Financial Modeling Prep) | ~$20-50/mo | More reliable, more history |
| News | NewsAPI, GDELT | ~$50-100/mo | More sources, better NLP |
| Social sentiment | X API, Reddit API | Variable | Real social sentiment |
| ETF flows | FMP, ETF.com | ~$50/mo | Live flow data |
| Options data | CBOE Datashop, ORATS | ~$200+/mo | Full options analytics |
| Fund flows | ICI, EPFR | Institutional | Professional-grade |

### Mode C: Westwood / Professional
**Goal**: Institutional-grade data for internal use. Licensed data only.

| Data Type | Source | Access | Notes |
|-----------|--------|--------|-------|
| Full market data | Bloomberg Terminal | Licensed terminal | Via Bloomberg MCP or API |
| Fund flows | EPFR, Morningstar | Licensed | Weekly/monthly |
| Futures positioning | CFTC + Bloomberg | Mixed | COT reports are public |
| Proprietary signals | Westwood internal | Internal | Custom models, research |
| Analyst data | Internal research | Internal | Westwood views |

## Provider Priority Chain

For each data type, providers are tried in priority order:

```
Professional: BloombergMCPProvider → MorningstarMCPProvider → DailyExportProvider
Premium:    FMPProvider → CBOEProvider → RSSNewsProvider
Public:     YFinanceProvider → FREDProvider → RSSNewsProvider → MockProvider (fallback)
```

The system always falls back to a lower tier rather than failing. The confidence score reflects which tier ultimately provided the data.

## Data Freshness Expectations

| Data Type | Public Mode | Premium Mode | Professional Mode |
|-----------|-------------|--------------|-------------------|
| Prices | 15-min delay | Real-time | Real-time |
| VIX | 15-min delay | Real-time | Real-time |
| Credit spreads | Daily morning | Daily morning | Intraday |
| Put/call | Daily close | Intraday | Intraday |
| News | 15-60 min delay | 5-15 min delay | Real-time |
| Social | N/A (mock) | 5-15 min delay | Real-time |
| ETF flows | N/A (stub) | Daily | Real-time |

## Implementation Roadmap

### Phase 1 (MVP): Public Mode
- Implement all public providers: yfinance, FRED, CBOE, RSS
- Implement mock provider as universal fallback
- Build full scoring engine with public data
- Stub interfaces for premium/professional providers

### Phase 2: Premium Integration
- Add FMP provider (prices, news, fundamentals)
- Add NewsAPI/GDELT for better narrative coverage
- Add X/Reddit stubs with API interfaces
- Enable premium mode with API keys

### Phase 3: Professional Integration
- Implement Bloomberg MCP provider (interface + stub)
- Implement daily export workflow
- Build manual CSV/JSON import path
- Add Morningstar MCP provider stub

### Phase 4: Additional Sources
- CFTC futures positioning (public, needs parser)
- FINRA margin debt (public, monthly)
- Options skew data (CBOE)
- Prediction markets (Kalshi, Polymarket stubs)

## Adding a New Provider

To add a new data provider:

1. Create a new file in `/backend/providers/`
2. Inherit from `BaseProvider`
3. Implement all required methods (can return empty/None for unsupported data types)
4. Register in `config.py` provider chain
5. Add environment variable for API key (if needed)
6. Add tests in `/backend/tests/providers/`
7. Update this document

Example provider skeleton:
```python
class MyProvider(BaseProvider):
    name = "my_provider"
    tier = "premium"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("MY_API_KEY")
    
    async def get_source_status(self) -> SourceStatus:
        return SourceStatus(
            provider=self.name,
            available=self.api_key is not None,
            ...
        )
    
    # Implement other methods...
```

## Environment Configuration

See `.env.example` for all provider API keys and configuration options.

Key configuration:
```bash
# Provider selection
MARKETPULSE_MODE=public              # public | premium | professional
ENABLED_PROVIDERS=yfinance,fred,cboe,rss,mock

# API keys (only needed for premium/professional)
FMP_API_KEY=your_key_here
NEWSAPI_KEY=your_key_here
BLOOMBERG_MCP_PATH=/path/to/mcp
```
