# Westwood MarketPulse — Architecture

## Design Philosophy
MarketPulse uses a **layered, modular architecture** that separates data acquisition, calculation, storage, and presentation. Each layer depends only on the layer below it, never above. This enables:
- Swapping data sources without changing scoring logic
- Adding new markets by configuration
- Running in mock mode without any API keys
- Graduating from public → premium → professional data sources

## Layer Stack

```
┌─────────────────────────────────────┐
│  LAYER 6: Presentation (React)      │  ← Frontend only talks to API
├─────────────────────────────────────┤
│  LAYER 5: API (FastAPI)             │  ← HTTP/JSON interface
├─────────────────────────────────────┤
│  LAYER 4: Jobs (Scheduled tasks)    │  ← Daily update, export generation
├─────────────────────────────────────┤
│  LAYER 3: Scoring Engine            │  ← Classic, Narrative, Positioning, Composite
├─────────────────────────────────────┤
│  LAYER 2: Indicators                │  ← Raw → normalized component scores
├─────────────────────────────────────┤
│  LAYER 1: Providers                 │  ← Data source abstraction
├─────────────────────────────────────┤
│  LAYER 0: Storage + Domain          │  ← DuckDB, SQLite cache, Pydantic models
└─────────────────────────────────────┘
```

## Layer Details

### Layer 0: Storage + Domain
- **Domain models**: Pydantic v2 models for all data contracts (`/backend/domain/`)
- **DuckDB store**: Analytical database for scores, components, history (`/backend/storage/duckdb_store.py`)
- **Cache**: SQLite-based TTL cache for raw API responses (`/backend/storage/cache.py`)
- **Exports**: Static JSON/CSV generation for public consumption (`/backend/storage/exports.py`)

### Layer 1: Providers
All providers implement `BaseProvider` (abstract class in `/backend/providers/base.py`).

**Provider chain of responsibility**: When calculating a component, the scoring engine asks providers in priority order (professional → premium → public → mock). The first provider that returns valid data wins.

**Provider list**:
| Provider | Tier | Key Data | Requirements |
|----------|------|----------|-------------|
| `MockProvider` | public | All data types | None — always works |
| `YFinanceProvider` | public | Prices, VIX, safe-haven assets | None |
| `FREDProvider` | public | Credit spreads, macro data | None |
| `CBOEProvider` | public | Put/call ratios, options data | None |
| `RSSNewsProvider` | public | News headlines | RSS URLs configured |
| `FMPProvider` | premium | Prices, fundamentals, news | FMP_API_KEY |
| `ManualCSVProvider` | professional | Any data via CSV upload | CSV files in `/data/sample_sources/` |
| `DailyExportProvider` | professional | Sanitized daily payload | `/data/static_site_payloads/latest_marketpulse.json` |
| `BloombergMCPProvider` | professional | Full professional data | Bloomberg terminal + MCP (stub) |

### Layer 2: Indicators
Each indicator calculator takes raw provider data and returns a normalized 0-100 score.

| Calculator | File | Inputs | Output |
|-----------|------|--------|--------|
| Momentum | `momentum.py` | Price history (125d) | 0-100 momentum score |
| Highs/Lows | `highs_lows.py` | Constituent prices, highs/lows | 0-100 strength score |
| Breadth | `breadth.py` | Advancing/declining volume or % above MA | 0-100 breadth score |
| Put/Call | `put_call.py` | Options volume/open interest | 0-100 (inverted) |
| Volatility | `volatility.py` | VIX history | 0-100 (inverted) |
| Credit Spreads | `credit_spreads.py` | HY/IG spreads | 0-100 (inverted) |
| Safe Haven | `safe_haven.py` | Equity vs TLT/GLD/DXY returns | 0-100 (inverted) |
| Flows/Positioning | `flows_positioning.py` | ETF flows, fund flows, futures | 0-100 score |
| Narrative Sentiment | `narrative_sentiment.py` | Scored articles, social posts | 0-100 narrative score |

### Layer 3: Scoring Engine
Four index calculators + confidence scoring:

**`marketpulse_classic.py`**: Average of 7 component scores (momentum, strength, breadth, put/call, credit, volatility, safe haven). Each component weighted equally by default (configurable). Missing components reduce confidence but don't break the index.

**`marketpulse_narrative.py`**: Aggregates NLP sentiment across panic, caution, uncertainty, optimism, complacency, euphoria dimensions. Maps emotional profile to 0-100 using a configurable scoring matrix.

**`marketpulse_positioning.py`**: Scores available positioning signals (put/call, VIX, credit spreads, equity/bond relative, safe haven flows). Stubs for ETF flows, futures positioning, options skew, margin debt. Weights dynamically adjusted based on available components.

**`marketpulse_composite.py`**: Weighted average of Classic/Narrative/Positioning with configurable weights. Confidence-adjusted: if one index has low confidence, its weight is reduced proportionally.

**`confidence.py`**: Calculates overall confidence based on:
- Source availability ratio (available / total expected)
- Data freshness (staleness penalties)
- Component substitution penalties
- Historical consistency checks

### Layer 4: Jobs
- **`update_daily.py`**: Run once daily. Fetches all data, calculates all scores, stores in DuckDB, generates explanations, exports static JSON.
- **`refresh_intraday.py`**: Run every 15-30 min during market hours. Refreshes price-dependent components only (momentum, volatility, safe haven).
- **`generate_static_exports.py`**: Generates sanitized JSON payload for public website consumption. Removes raw data, keeps only derived scores and labels.

### Layer 5: API (FastAPI)
RESTful JSON API with auto-generated OpenAPI docs. All endpoints under `/api/v1/`. See SPEC.md for full endpoint list.

**Key features**:
- CORS enabled for embed widget
- Response caching via middleware
- Structured logging
- Health check endpoint
- API key authentication optional (for premium endpoints)

### Layer 6: Presentation (React)
Next.js application with finance-news aesthetic. Key pages:
- **Landing**: Hero score, sub-index cards, stacked chart, explanation boxes
- **Methodology**: Interactive component explorer
- **Markets**: Multi-market comparison
- **Embed Demo**: Widget demonstration
- **Admin**: Source diagnostics, manual refresh, export
- **Backtest**: Historical regime analysis

## Data Flow: Score Calculation

```
1. Trigger: Daily job or API request
2. For each configured market:
   a. Fetch raw data from available providers (parallel where possible)
   b. Cache raw data in SQLite
   c. Calculate each indicator → normalized 0-100 component score
   d. Assemble Classic index from 7 components
   e. Ingest & score text → Narrative index
   f. Assemble Positioning index from available signals
   g. Calculate Composite from 3 indices with confidence weighting
   h. Generate plain-English explanation
   i. Store all scores, components, raw values in DuckDB
   j. Update cache for API responses
3. Generate static JSON export
```

## Data Flow: API Request

```
1. Request arrives at FastAPI
2. Check response cache (SQLite, 5-min TTL for current scores)
3. If cache miss:
   a. Read latest scores from DuckDB
   b. Assemble response with Pydantic models
   c. Cache response
   d. Return JSON
4. If cache hit: return cached JSON
```

## Configuration System

MarketPulse uses a layered config system:
1. **Default config** (Python dataclasses in `config.py`)
2. **Environment variables** (`.env` file, loaded via `python-dotenv`)
3. **Market config files** (JSON in `/data/markets/`)

Key environment variables:
```bash
# Operating mode
MARKETPULSE_MODE=public                    # public | premium | professional

# API Keys (optional — app works without them)
FMP_API_KEY=                               # Financial Modeling Prep
FRED_API_KEY=                              # St. Louis Fed (optional, many series public)
NEWSAPI_KEY=                               # NewsAPI for RSS feeds
X_API_BEARER_TOKEN=                        # X/Twitter (stub)
REDDIT_CLIENT_ID=                          # Reddit (stub)
REDDIT_CLIENT_SECRET=                      # Reddit (stub)

# Paths
DATA_DIR=./data
DUCKDB_PATH=./data/marketpulse.duckdb
CACHE_PATH=./data/cache.sqlite
EXPORTS_DIR=./data/exports

# Intervals
DAILY_UPDATE_TIME=16:30                    # ET
INTRADAY_REFRESH_MINUTES=15
CACHE_TTL_MINUTES=5

# Features
ENABLE_NARRATIVE=true
ENABLE_POSITIONING=true
ENABLE_NLP_LLM=false                       # LLM summarization (on-demand only)
ENABLE_BACKTEST=true
```

## Error Handling Strategy

### Provider failures
- Individual provider failure → log warning, try next provider in chain
- All providers fail for a component → use mock data, mark as substituted, reduce confidence
- Provider temporarily unavailable → serve cached data with stale warning

### Calculation failures
- Indicator calculation error → skip component, continue with remaining components
- All components fail → return error response with details
- Partial data → return score with reduced confidence, list missing components

### API failures
- Invalid parameters → 400 with validation detail
- Internal error → 500 with trace ID (no stack traces in production)
- Timeout → 503 with retry-after header

## Security Considerations

- **No Bloomberg data in public responses**: Static exports contain only derived scores
- **No API keys in responses**: Keys stay server-side only
- **CORS restricted**: Embed widget uses specific allowed origins
- **Rate limiting**: Applied to embed and API endpoints
- **Input validation**: All params validated via Pydantic
- **SQL injection prevention**: Parameterized queries in DuckDB layer

## Deployment Modes

### Local Development
```bash
pip install -r requirements.txt
python -m backend.main        # FastAPI dev server
npm run dev                   # Next.js dev server (separate terminal)
```

### Docker
```bash
docker-compose up             # Full stack: backend + frontend + DuckDB
```

### Production (Internal)
- Backend: Deployed on internal infrastructure with Bloomberg MCP access
- Frontend: Static site consuming `/data/static_site_payloads/latest_marketpulse.json`
- Daily export job runs on licensed Bloomberg machine, generates sanitized JSON
- Public website never touches raw Bloomberg data
