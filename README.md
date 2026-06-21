# Westwood MarketPulse

A finance-media-grade market sentiment and risk appetite platform. MarketPulse produces four daily 0-100 indices — Classic, Narrative, Positioning & Flows, and Composite — that explain market psychology from different angles.

![MarketPulse Concept](docs/assets/concept.png)

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 20+
- Git

### Install & Run Backend

```bash
# Clone and enter repository
cd MarketPulse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
cd frontend && npm install

# Run backend
python -m backend.main
```

The API will be available at `http://localhost:8000` with auto-generated docs at `/docs`.

### Install & Run Frontend

```bash
# In a new terminal
cd frontend

# Run development server
npm run dev
```

The frontend will be available at `http://localhost:3000`.

### Run in Mock Mode (No API Keys Required)

```bash
# Backend runs with mock data by default
python -m backend.main

# Or explicitly
MARKETPULSE_MODE=public python -m backend.main
```

## Docker Deployment

Build and run the full stack with Docker Compose:

```bash
# Build and run full stack
docker-compose up --build
```

Services:
- **Backend API**: `http://localhost:8000`
- **Frontend**: `http://localhost:3000`
- **API Docs**: `http://localhost:8000/docs`

Run services individually:

```bash
docker-compose up backend
docker-compose up frontend
```

## Running Tests

```bash
# Run all tests
pytest backend/tests/ -v

# With coverage
pytest backend/tests/ --cov=backend --cov-report=html
```

Tests cover domain models, data providers (using MockProvider with no external dependencies), indicator calculations, scoring engines, NLP sentiment analysis, and API endpoints.

## API Documentation

When the backend is running, interactive API docs are available at:

- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Key Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /health` | Health check |
| `GET /api/v1/scores/current` | Current scores for a market |
| `GET /api/v1/scores/composite` | Lightweight composite score only |
| `GET /api/v1/markets/` | Available markets |
| `GET /api/v1/components/current` | Component breakdown |
| `GET /api/v1/history/scores` | Historical scores |
| `GET /api/v1/narrative/sentiment` | Narrative sentiment details |
| `GET /api/v1/sources/status` | Provider status |
| `POST /api/v1/admin/refresh` | Trigger manual refresh |
| `GET /api/v1/embed/marketpulse` | Embeddable HTML widget |

## Project Structure

```
MarketPulse/
├── Dockerfile                  # Backend Docker image
├── docker-compose.yml          # Full stack orchestration
├── pytest.ini                  # pytest configuration
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── backend/                    # Python FastAPI backend
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── domain/                 # Pydantic data models
│   │   ├── score.py            # Regime, Score, DataQualityReport
│   │   ├── market.py           # MarketConfig, DEFAULT_MARKETS
│   │   ├── indicator.py        # IndicatorResult
│   │   ├── article.py          # Article, SocialPost
│   │   ├── source.py           # SourceStatus
│   │   ├── sentiment.py        # NarrativeSnapshot
│   │   └── regime.py           # RegimePeriod
│   ├── providers/              # Data source providers
│   │   ├── base.py             # BaseProvider abstract class
│   │   ├── mock_provider.py    # Synthetic data (no API keys)
│   │   ├── provider_chain.py   # Prioritized fallback chain
│   │   ├── yfinance_provider.py
│   │   ├── fred_provider.py
│   │   ├── cboe_provider.py
│   │   ├── rss_news_provider.py
│   │   ├── fmp_provider.py
│   │   ├── bloomberg_mcp_provider.py
│   │   ├── daily_export_provider.py
│   │   ├── manual_csv_provider.py
│   │   ├── x_provider.py
│   │   ├── reddit_provider.py
│   │   └── stocktwits_provider.py
│   ├── indicators/             # Component calculators
│   │   ├── normalizer.py       # Rolling percentile, z-score, min-max
│   │   ├── momentum.py         # Price vs 125-day MA
│   │   ├── put_call.py         # Put/call ratio (inverted)
│   │   ├── breadth.py          # Advancing/declining
│   │   ├── volatility.py       # VIX normalization
│   │   ├── credit_spreads.py   # HY/IG spread scoring
│   │   ├── safe_haven.py       # TLT/GLD/UUP demand
│   │   ├── highs_lows.py       # New highs/lows ratio
│   │   ├── flows_positioning.py
│   │   └── narrative_sentiment.py
│   ├── scoring/                # Index scoring engines
│   │   ├── marketpulse_classic.py
│   │   ├── marketpulse_narrative.py
│   │   ├── marketpulse_positioning.py
│   │   ├── marketpulse_composite.py
│   │   ├── confidence.py       # ConfidenceScorer
│   │   ├── explanation.py      # Explanation generation
│   │   └── backtest.py         # Regime backtesting
│   ├── nlp/                    # Text sentiment pipeline
│   │   ├── sentiment_model.py  # Rule-based + optional FinBERT
│   │   ├── topic_classifier.py
│   │   ├── entity_extraction.py
│   │   ├── text_ingestion.py
│   │   └── summarizer.py
│   ├── storage/                # DuckDB, cache, exports
│   │   ├── duckdb_store.py
│   │   ├── cache.py
│   │   └── exports.py
│   ├── api/                    # FastAPI route handlers
│   │   ├── routes_scores.py
│   │   ├── routes_markets.py
│   │   ├── routes_components.py
│   │   ├── routes_history.py
│   │   ├── routes_narrative.py
│   │   ├── routes_sources.py
│   │   ├── routes_embed.py
│   │   ├── routes_backtest.py
│   │   └── routes_admin.py
│   ├── jobs/                   # Scheduled tasks
│   │   ├── update_daily.py
│   │   └── generate_static_exports.py
│   └── tests/                  # pytest test suite
│       ├── __init__.py
│       ├── test_domain.py      # Domain model tests
│       ├── test_providers.py   # MockProvider tests
│       ├── test_indicators.py  # Indicator calculation tests
│       ├── test_scoring.py     # Scoring engine tests
│       ├── test_nlp.py         # Sentiment analysis tests
│       └── test_api.py         # FastAPI endpoint tests
├── frontend/                   # React + Vite frontend
│   ├── Dockerfile              # Frontend Docker image
│   ├── nginx.conf              # Nginx SPA configuration
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── src/
├── data/                       # Data storage (gitignored)
│   ├── cache/
│   ├── exports/
│   └── static_site_payloads/
└── docs/                       # Documentation
    ├── PRODUCT_VISION.md
    ├── ARCHITECTURE.md
    ├── METHODOLOGY.md
    ├── DATA_SOURCE_STRATEGY.md
    ├── BLOOMBERG_MCP_AND_DAILY_EXPORT_PLAN.md
    ├── WEBSITE_EMBED_PLAN.md
    ├── ROADMAP.md
    └── COMPLIANCE_AND_DISCLOSURES.md
```

## The Four Indices

| Index | What It Measures | Data Sources |
|-------|-----------------|--------------|
| **Classic** | Market-data-driven sentiment | Prices, VIX, credit spreads, put/call, breadth, momentum |
| **Narrative** | News & text sentiment | RSS feeds, news headlines, financial text |
| **Positioning** | Trading & investor positioning | Put/call, VIX term structure, spreads, safe-haven flows |
| **Composite** | Blended headline score | Weighted combination of the three above |

## Five-Zone Framework

| Zone | Score | Label |
|------|-------|-------|
| MP-1 | 0-20 | Capitulation / Risk-Off Extreme |
| MP-2 | 20-40 | Defensive / Risk-On |
| MP-3 | 40-60 | Neutral / Balanced |
| MP-4 | 60-80 | Risk-On |
| MP-5 | 80-100 | Euphoria / Risk-On Extreme |

## Data Sources

### Public/Free (Default)
- **yfinance**: Stock prices, VIX, safe-haven assets
- **FRED**: Credit spreads, Treasury yields, macro data
- **CBOE**: Put/call ratios, volatility data
- **RSS Feeds**: News headlines from Yahoo Finance, MarketWatch, etc.
- **Mock Provider**: Synthetic realistic data when real data unavailable

### Premium (Requires API Keys)
- **FMP**: More reliable prices, fundamentals, news
- **NewsAPI**: Broader news coverage
- **Social APIs**: X/Twitter, Reddit (stubs ready)

### Professional (Internal Westwood Only)
- **Bloomberg MCP**: Full institutional data
- **Morningstar MCP**: Fund flows, analyst data
- **Manual CSV/JSON**: Import any data source

## Documentation

- [Product Vision](docs/PRODUCT_VISION.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Methodology](docs/METHODOLOGY.md)
- [Data Source Strategy](docs/DATA_SOURCE_STRATEGY.md)
- [Bloomberg MCP & Export Plan](docs/BLOOMBERG_MCP_AND_DAILY_EXPORT_PLAN.md)
- [Website Embed Plan](docs/WEBSITE_EMBED_PLAN.md)
- [Roadmap](docs/ROADMAP.md)
- [Compliance & Disclosures](docs/COMPLIANCE_AND_DISCLOSURES.md)

## Disclaimer

MarketPulse is an educational market-sentiment tool, not investment advice. It is not a trading signal. Data may be delayed or derived from public/proxy sources. See [COMPLIANCE_AND_DISCLOSURES.md](docs/COMPLIANCE_AND_DISCLOSURES.md) for full details.
