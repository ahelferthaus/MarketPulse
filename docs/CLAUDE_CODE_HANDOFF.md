# Claude Code Handoff

## Context
You are continuing development on Westwood MarketPulse, a market sentiment and risk appetite platform. The MVP has been built with a modular Python backend (FastAPI, DuckDB) and a React/Next.js frontend.

## What Has Been Built

### Backend
- **Domain models**: Pydantic v2 models for all data contracts
- **Provider layer**: Base provider interface, mock, yfinance, FRED, CBOE, RSS, FMP (stub), Bloomberg MCP (stub), manual CSV, daily export
- **Indicators**: All 9 component calculators (momentum, highs/lows, breadth, put/call, volatility, credit spreads, safe haven, flows/positioning, narrative sentiment)
- **Scoring**: Classic, Narrative, Positioning, Composite indices + confidence scoring
- **NLP**: Rule-based sentiment model, text ingestion, topic classifier, entity extractor, summarizer (stub)
- **Storage**: DuckDB analytical store, SQLite cache, static export generator
- **API**: Full FastAPI with all routes, CORS, health checks
- **Jobs**: Daily update, intraday refresh, static export generation
- **Tests**: pytest suite with mock data

### Frontend
- **Next.js app** with Tailwind CSS and shadcn/ui
- **Landing page**: Hero score, sub-index cards, stacked chart, explanations
- **Methodology page**: Interactive component explorer
- **Admin page**: Source status, diagnostics, manual refresh
- **Embed demo page**: Widget demonstration

### Documentation
All docs in `/docs/`: Product Vision, Architecture, Methodology, Data Source Strategy, Bloomberg MCP Plan, Embed Plan, Roadmap, Compliance.

## Your Next Tasks

### Priority 1: Data Integration Quality
1. **Improve yfinance integration**: Add better error handling, retry logic, rate limit management
2. **Complete FRED provider**: Ensure all credit spread series work, add fallback series
3. **Complete CBOE provider**: Implement web scraping for put/call ratios with proper error handling
4. **Add FMP provider**: Implement the premium provider if FMP_API_KEY is available
5. **Test all provider combinations**: Ensure graceful degradation when providers fail

### Priority 2: NLP & Narrative
1. **Enhance RSS ingestion**: Add more financial news sources, better deduplication
2. **Improve rule-based sentiment**: Expand financial lexicon, add negation handling
3. **Add FinBERT option**: Install transformers, use FinBERT when available, fall back to rules
4. **Implement article storage**: Store scored articles in DuckDB for historical analysis
5. **Add narrative shift detection**: Identify significant day-over-day narrative changes

### Priority 3: Bloomberg MCP Integration
1. **Study Bloomberg MCP SDK**: Understand the MCP protocol and Bloomberg's implementation
2. **Implement BloombergMCPProvider**: Connect to Bloomberg Terminal via MCP
3. **Test with real terminal**: Validate data retrieval for all security types
4. **Build daily export workflow**: Run on licensed machine, generate sanitized JSON
5. **Document the workflow**: Ensure any Westwood team member can run the export

### Priority 4: Frontend Polish
1. **Add more interactive charts**: D3.js or Recharts for component contribution, regime history
2. **Improve responsive design**: Mobile-first refinements
3. **Add backtest visualization**: Historical regime analysis page with forward returns
4. **Implement embed widget**: Iframe and JavaScript embed options
5. **Add dark mode**: Theme switching support

### Priority 5: Production Readiness
1. **Add comprehensive error handling**: Every edge case covered
2. **Add structured logging**: JSON logs, correlation IDs, performance metrics
3. **Add monitoring**: Health checks, metrics endpoints, alert thresholds
4. **Add rate limiting**: API throttling, embed widget limits
5. **Security audit**: Input validation, CORS policy, no credential exposure
6. **Performance optimization**: Database indexing, query optimization, caching

### Priority 6: Testing
1. **Add integration tests**: End-to-end score calculation with real (but cached) data
2. **Add property-based tests**: Hypothesis for score normalization
3. **Add load tests**: API performance under concurrent requests
4. **Add frontend tests**: Component tests with React Testing Library
5. **Ensure no look-ahead bias**: Validate all historical calculations

## Architecture Reminders

### Provider Chain
Providers are tried in priority order: professional → premium → public → mock. Always fall back, never fail.

### Data Sanitization
Raw Bloomberg data NEVER goes to the public site. Only derived scores in sanitized JSON exports.

### Confidence Scoring
Every score has a confidence value (0-100) based on data quality. Always display confidence to users.

### Look-Ahead Bias
Historical calculations must use only data available at that point in time. Rolling windows must be strictly historical.

## Running the Project

```bash
# Backend
cd /path/to/MarketPulse
source venv/bin/activate
python -m backend.main

# Frontend (new terminal)
cd /path/to/MarketPulse/frontend
npm run dev

# Tests
pytest backend/tests/ -v

# Daily update
python -m backend.jobs.update_daily --market sp500

# Generate export
python -m backend.jobs.generate_static_exports
```

## Files to Read First
1. `SPEC.md` — Technical specification
2. `docs/ARCHITECTURE.md` — Architecture overview
3. `docs/METHODOLOGY.md` — Scoring methodology
4. `backend/domain/` — Data models
5. `backend/providers/base.py` — Provider interface
6. `backend/scoring/` — Scoring engines

## Rules
- Do NOT commit API keys or credentials
- Do NOT expose raw Bloomberg data in public responses
- Keep public/exported data sanitized and license-compliant
- Add tests for every new feature
- Maintain the provider abstraction — never hardcode data sources in scoring logic
- Update documentation when changing behavior
