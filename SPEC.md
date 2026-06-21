# Westwood MarketPulse — Technical Specification

## 1. Overview

Westwood MarketPulse is a modular, finance-media-grade market sentiment and risk appetite platform. It produces four daily 0-100 indices (Classic, Narrative, Positioning & Flows, Composite) that explain market psychology from different angles, served via a FastAPI backend and a React/Next.js frontend.

## 2. Architecture

### 2.1 High-Level Diagram
```
┌─────────────────────────────────────────────────────────────────────────┐
│                           FRONTEND LAYER                                 │
│  React/Next.js + Tailwind + shadcn/ui + Recharts                        │
│  Pages: Landing | Methodology | Markets | Embed | Admin                  │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP/JSON
┌─────────────────────────────────────────────────────────────────────────┐
│                              API LAYER                                   │
│  FastAPI — RESTful JSON API                                              │
│  /api/v1/scores/*    → Current & historical scores                       │
│  /api/v1/markets/*   → Market universe & configuration                   │
│  /api/v1/components/*→ Component breakdown & contributions               │
│  /api/v1/history/*   → Time-series history                               │
│  /api/v1/embed/*     → Embeddable widget endpoints                       │
│  /api/v1/sources/*   → Source status & quality                           │
│  /api/v1/admin/*     → Internal research & diagnostics                   │
│  /api/v1/narrative/* → Text sentiment & top phrases                      │
│  /api/v1/backtest/*  → Historical regime analysis                        │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                            SCORING LAYER                                 │
│  marketpulse_classic.py      ── Market-data-driven index                 │
│  marketpulse_narrative.py    ── NLP/news/social sentiment index          │
│  marketpulse_positioning.py  ── Trading-market & positioning index       │
│  marketpulse_composite.py    ── Blended headline index                   │
│  confidence.py               ── Source quality & data confidence         │
│  normalizer.py               ── Rolling percentile / min-max / z-score   │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          INDICATOR LAYER                                 │
│  momentum.py, highs_lows.py, breadth.py, put_call.py                     │
│  volatility.py, credit_spreads.py, safe_haven.py                         │
│  flows_positioning.py, narrative_sentiment.py                            │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          PROVIDER LAYER                                  │
│  yfinance, FRED, FMP, CBOE, RSS News, Manual CSV, Daily Export         │
│  (Bloomberg MCP, Morningstar MCP, X/Reddit/StockTwits — stubs)         │
└─────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                          STORAGE LAYER                                   │
│  DuckDB ── Analytical store (scores, components, history)                │
│  SQLite ── Cache layer (API responses, raw data cache)                   │
│  JSON   ── Static exports for public website                             │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Data Flow
1. **Ingest**: Providers fetch raw market data, news, social feeds
2. **Cache**: Raw data cached in SQLite with TTL
3. **Calculate**: Indicators transform raw → component scores (0-100)
4. **Normalize**: Normalizer handles rolling percentile, min-max, z-score
5. **Score**: Scoring engine assembles components into 4 indices
6. **Store**: DuckDB persists all scores, components, raw values with timestamps
7. **Serve**: FastAPI serves JSON; static exports for public consumption
8. **Display**: React frontend renders gauges, charts, cards, explanations

## 3. Domain Models (Pydantic)

### 3.1 Score & Regime
```python
class MarketPulseScore(BaseModel):
    timestamp: datetime
    market_id: str                          # "sp500", "nasdaq100", etc.
    classic_score: float                    # 0-100
    narrative_score: float                  # 0-100
    positioning_score: float                # 0-100
    composite_score: float                  # 0-100
    regime: Regime                          # MP-1 through MP-5
    regime_label: str                       # "Capitulation", "Defensive", etc.
    direction: str                          # "rising", "falling", "stable"
    confidence: float                       # 0-100
    explanation: str                        # One-sentence plain English
    what_changed: Optional[str]             # "What changed today"
    drivers: List[ScoreDriver]              # Top contributors
    data_quality: DataQualityReport

class Regime(str, Enum):
    MP1_CAPITULATION = "mp1_capitulation"   # 0-20
    MP2_DEFENSIVE = "mp2_defensive"         # 20-40
    MP3_NEUTRAL = "mp3_neutral"             # 40-60
    MP4_RISK_ON = "mp4_risk_on"             # 60-80
    MP5_EUPHORIA = "mp5_euphoria"           # 80-100

class ScoreDriver(BaseModel):
    component: str                          # e.g. "momentum", "put_call"
    contribution: float                     # -20 to +20 (impact on composite)
    direction: str                          # "bullish", "bearish", "neutral"
    description: str                        # Plain English explanation

class DataQualityReport(BaseModel):
    overall_confidence: float               # 0-100
    sources_used: int
    sources_available: int
    missing_components: List[str]
    substituted_components: List[str]
    stale_data_warnings: List[str]
    data_freshness_minutes: int
```

### 3.2 Market Configuration
```python
class MarketConfig(BaseModel):
    market_id: str                          # "sp500"
    name: str                               # "S&P 500"
    benchmark_ticker: str                   # "^GSPC"
    etf_proxy: str                          # "SPY"
    volatility_proxy: str                   # "^VIX"
    options_proxy: str                      # "SPY"
    breadth_universe: List[str]             # S&P 500 constituents (or proxy)
    credit_spread_proxy: str                # "BAMLH0A0HYM2"
    safe_haven_comparison: SafeHavenConfig
    normalization_window_days: int          # 252 default
    component_config: ComponentAvailability
    confidence_penalties: Dict[str, float]  # Penalty per substitution

class ComponentAvailability(BaseModel):
    momentum: bool = True
    price_strength: bool = True
    breadth: bool = True
    put_call: bool = True
    credit_spreads: bool = True
    volatility: bool = True
    safe_haven: bool = True
    etf_flows: bool = False               # stub
    fund_flows: bool = False              # stub
    futures_positioning: bool = False     # stub
    prediction_markets: bool = False      # stub
    options_skew: bool = False            # stub
    margin_debt: bool = False             # stub
```

### 3.3 Provider Interface
```python
class BaseProvider(ABC):
    name: str
    tier: Literal["public", "premium", "professional"]
    
    @abstractmethod async def get_price_history(self, ticker: str, days: int) -> pd.DataFrame
    @abstractmethod async def get_current_quote(self, ticker: str) -> dict
    @abstractmethod async def get_breadth_data(self, market_id: str) -> dict
    @abstractmethod async def get_options_data(self, ticker: str) -> dict
    @abstractmethod async def get_credit_spreads(self, series_id: str) -> dict
    @abstractmethod async def get_safe_haven_assets(self) -> dict
    @abstractmethod async def get_news_articles(self, query: str, limit: int) -> List[Article]
    @abstractmethod async def get_social_posts(self, query: str, limit: int) -> List[SocialPost]
    @abstractmethod async def get_flows_data(self, ticker: str) -> dict
    @abstractmethod async def get_source_status(self) -> SourceStatus

class SourceStatus(BaseModel):
    provider: str
    available: bool
    last_successful_fetch: Optional[datetime]
    error_count_24h: int
    avg_response_ms: Optional[int]
    data_freshness_minutes: Optional[int]
    tier: str
```

## 4. Component Breakdown

### 4.1 MarketPulse Classic (7 components)
| # | Component | Raw Source | Normalization | Invert |
|---|-----------|-----------|---------------|--------|
| 1 | Market Momentum | Benchmark vs 125d MA | Rolling percentile | No |
| 2 | Price Strength | New highs / (highs+lows) or proxy | Rolling percentile | No |
| 3 | Price Breadth | Advancing/declining volume or % above MA | Rolling percentile | No |
| 4 | Put/Call Ratio | CBOE total put/call | Rolling percentile | Yes |
| 5 | Credit Spreads | HY-OAS or BBB spread | Rolling percentile | Yes |
| 6 | Volatility | VIX level | Rolling percentile | Yes |
| 7 | Safe Haven Demand | Equity vs TLT/GLD/DXY basket return | Rolling percentile | Yes |

**Scoring**: Average of 7 normalized components, each 0-100. Apply confidence weighting if components missing.

### 4.2 MarketPulse Narrative (6 dimensions)
| Dimension | Description | Scoring |
|-----------|-------------|---------|
| Panic | Extreme negative emotion, crash language | 0 = no panic, 100 = extreme panic |
| Caution | Defensive, hedging, protective language | 0 = no caution, 100 = high caution |
| Uncertainty | Mixed signals, "wait and see", ambiguity | 0 = certain, 100 = highly uncertain |
| Optimism | Positive outlook, growth language | 0 = no optimism, 100 = strong optimism |
| Complacency | Low volatility expectations, risk-ignoring | 0 = vigilant, 100 = complacent |
| Euphoria | Extreme bullishness, bubble language | 0 = no euphoria, 100 = extreme euphoria |

**Scoring**: Map emotion profile to 0-100. Panic/caution/uncertainty → lower scores. Optimism → mid-high. Complacency/euphoria → high risk.

### 4.3 MarketPulse Positioning & Flows (8+ components)
| # | Component | Status |
|---|-----------|--------|
| 1 | Put/Call Ratio (all) | Live (CBOE/FMP) |
| 2 | VIX Level | Live (yfinance) |
| 3 | VIX Term Structure | Stub (needs futures data) |
| 4 | Credit Spreads (HY, IG) | Live (FRED) |
| 5 | ETF Flows | Stub (needs premium API) |
| 6 | Equity/Bond Relative Return | Live (yfinance) |
| 7 | Dollar/Gold/Treasury Flow | Live (yfinance) |
| 8 | Fund Flows | Stub |
| 9 | Futures Positioning (CFTC) | Stub |
| 10 | Options Skew | Stub |
| 11 | Margin Debt | Stub |

### 4.4 Composite
Weighted average of Classic, Narrative, Positioning with configurable weights (default: 40/30/30). Confidence-adjusted.

## 5. Five-Zone Framework
| Zone | Score | Label | Public Language |
|------|-------|-------|-----------------|
| MP-1 | 0-20 | Capitulation / Risk-Off Extreme | "Markets are in extreme risk-off" |
| MP-2 | 20-40 | Defensive / Risk-Off | "Markets are defensive" |
| MP-3 | 40-60 | Neutral / Balanced | "Markets are balanced" |
| MP-4 | 60-80 | Risk-On | "Markets are risk-on" |
| MP-5 | 80-100 | Euphoria / Risk-On Extreme | "Markets are euphoric" |

## 6. NLP Pipeline

### 6.1 Text Ingestion
- RSS feeds (configurable list of financial news sources)
- Mock news dataset (for demo without API keys)
- Stub interfaces for: X/Twitter, Reddit, StockTwits, blogs

### 6.2 Processing Pipeline
```
Raw Text → Clean/Normalize → Tokenize → Entity Extract → Topic Classify → Sentiment Score → Aggregate
```

### 6.3 Sentiment Model
- **Primary**: Rule-based keyword matching with financial lexicon (no ML dependencies required)
- **Optional**: FinBERT/transformers if `transformers` package installed
- **LLM Summarization**: On-demand only, not required for daily score

### 6.4 Topic Classification
Topics: macro, fed, earnings, inflation, credit, geopolitics, ai_tech, consumer, banking_stress, recession, liquidity, valuation

## 7. API Endpoints

```
GET  /api/v1/scores/current?market=sp500              → Current MarketPulseScore
GET  /api/v1/scores/composite?market=sp500             → Composite score only (lightweight)
GET  /api/v1/markets/                                   → List available markets
GET  /api/v1/markets/{market_id}/config                 → Market configuration
GET  /api/v1/components/current?market=sp500            → Component breakdown
GET  /api/v1/components/history?market=sp500&days=90    → Component time series
GET  /api/v1/history/scores?market=sp500&days=365       → Score history
GET  /api/v1/history/regimes?market=sp500               → Regime history
GET  /api/v1/narrative/sentiment?market=sp500           → Current narrative sentiment
GET  /api/v1/narrative/top-phrases?market=sp500         → Top phrases driving score
GET  /api/v1/narrative/articles?market=sp500            → Recent scored articles
GET  /api/v1/sources/status                             → All provider statuses
GET  /api/v1/sources/status/{provider}                  → Single provider status
POST /api/v1/admin/refresh                              → Trigger manual refresh
POST /api/v1/admin/export-static                        → Generate static JSON payload
GET  /api/v1/admin/export/latest.json                   → Download latest static export
GET  /api/v1/backtest/regimes?market=sp500              → Forward returns by regime
GET  /api/v1/embed/marketpulse?market=sp500&size=full   → Embeddable HTML widget
GET  /api/v1/embed/marketpulse.json?market=sp500        → Embeddable JSON widget
GET  /health                                            → Health check
GET  /docs                                              → Auto-generated API docs
```

## 8. Static Export Format

```json
{
  "generated_at": "2026-01-15T16:30:00Z",
  "marketpulse": {
    "market": "sp500",
    "timestamp": "2026-01-15T16:30:00Z",
    "composite": {"score": 67, "regime": "mp4_risk_on", "label": "Risk-On", "direction": "rising"},
    "classic": {"score": 72, "change_1d": 3, "change_1w": -5},
    "narrative": {"score": 58, "change_1d": -2, "change_1w": 8},
    "positioning": {"score": 71, "change_1d": 1, "change_1w": -3},
    "confidence": 85,
    "explanation": "Markets are risk-on, driven by strong momentum and positioning, though narrative sentiment has cooled.",
    "components": [...],
    "data_quality": {...}
  }
}
```

## 9. Frontend Pages

| Page | Route | Description |
|------|-------|-------------|
| Landing | `/` | Headline score, regime, 3 sub-index cards, stacked chart, explanation boxes |
| Methodology | `/methodology` | How scores are calculated, component details, zone framework |
| Markets | `/markets` | Multi-market comparison, detailed charts |
| Embed Demo | `/embed-demo` | Demonstration of embeddable widget |
| Admin | `/admin` | Source status, raw components, diagnostics, export controls |
| Backtest | `/backtest` | Historical regime analysis, forward returns |

## 10. Database Schema (DuckDB)

```sql
-- Core scores table
CREATE TABLE scores (
    timestamp TIMESTAMP,
    market_id VARCHAR,
    classic_score DOUBLE,
    narrative_score DOUBLE,
    positioning_score DOUBLE,
    composite_score DOUBLE,
    regime VARCHAR,
    confidence DOUBLE,
    explanation VARCHAR,
    PRIMARY KEY (timestamp, market_id)
);

-- Component scores (one row per component per timestamp)
CREATE TABLE component_scores (
    timestamp TIMESTAMP,
    market_id VARCHAR,
    component_name VARCHAR,
    raw_value DOUBLE,
    normalized_score DOUBLE,
    weight DOUBLE,
    data_source VARCHAR,
    PRIMARY KEY (timestamp, market_id, component_name)
);

-- Narrative sentiment snapshots
CREATE TABLE narrative_snapshots (
    timestamp TIMESTAMP,
    market_id VARCHAR,
    panic_score DOUBLE,
    caution_score DOUBLE,
    uncertainty_score DOUBLE,
    optimism_score DOUBLE,
    complacency_score DOUBLE,
    euphoria_score DOUBLE,
    article_count INTEGER,
    top_phrases VARCHAR[],
    PRIMARY KEY (timestamp, market_id)
);

-- Scored articles
CREATE TABLE articles (
    id BIGINT PRIMARY KEY,
    timestamp TIMESTAMP,
    source VARCHAR,
    title VARCHAR,
    url VARCHAR,
    sentiment_score DOUBLE,
    topics VARCHAR[],
    market_relevance DOUBLE
);

-- Provider status log
CREATE TABLE provider_status_log (
    timestamp TIMESTAMP,
    provider VARCHAR,
    available BOOLEAN,
    response_ms INTEGER,
    error_message VARCHAR
);

-- Regime history for backtesting
CREATE TABLE regime_periods (
    market_id VARCHAR,
    regime VARCHAR,
    start_date DATE,
    end_date DATE,
    avg_forward_1m DOUBLE,
    avg_forward_3m DOUBLE,
    avg_forward_6m DOUBLE,
    avg_forward_12m DOUBLE
);
```

## 11. Implementation Order

1. **Layer 0**: Config, domain models, exceptions, logging utilities
2. **Layer 1**: Storage (DuckDB + cache), provider base + mock provider
3. **Layer 2**: Public providers (yfinance, FRED), normalizer
4. **Layer 3**: All indicator calculators
5. **Layer 4**: Scoring engines (Classic → Narrative → Positioning → Composite)
6. **Layer 5**: NLP pipeline + text ingestion
7. **Layer 6**: FastAPI routes
8. **Layer 7**: Jobs (daily update, export generation)
9. **Layer 9**: React frontend
10. **Layer 10**: Integration, tests, Docker, docs

## 12. Testing Strategy

- **Unit tests**: Each indicator, scorer, normalizer independently
- **Integration tests**: Full score calculation pipeline end-to-end
- **API tests**: FastAPI TestClient for all routes
- **Mock mode tests**: Ensure app runs with zero API keys
- **Data quality tests**: Verify no look-ahead bias in backtests
