# Westwood MarketPulse — Roadmap

## Phase 1: MVP (Current Sprint)
**Goal**: Working local application with mock/public data

### Backend
- [x] Domain models (Pydantic)
- [x] Provider abstraction + mock provider
- [x] yfinance provider
- [x] FRED provider
- [x] All indicator calculators
- [x] All 4 scoring engines
- [x] NLP pipeline (rule-based)
- [x] DuckDB storage
- [x] SQLite cache
- [x] FastAPI routes
- [x] Daily update job
- [x] Static export generation
- [x] Confidence scoring
- [x] Plain-English explanation engine

### Frontend
- [x] Next.js project setup
- [x] Landing page with hero score
- [x] Sub-index cards
- [x] Stacked chart visualization
- [x] Component breakdown
- [x] Methodology page
- [x] Admin page
- [x] Embed widget demo

### Infrastructure
- [x] Tests (pytest)
- [x] Docker support
- [x] README with setup instructions
- [x] All documentation

## Phase 2: Data Quality & Premium APIs
**Goal**: Higher data quality, more reliable scores

### Data Integrations
- [ ] FMP provider (full implementation)
- [ ] CBOE web scraping for put/call
- [ ] Better RSS/news ingestion
- [ ] NewsAPI integration
- [ ] Historical data backfill (2+ years)

### Frontend
- [ ] Multi-market comparison page
- [ ] Historical backtest visualization
- [ ] Interactive component explorer
- [ ] Mobile app-like responsive design

### Backend
- [ ] Backtest engine with forward returns
- [ ] Regime transition analysis
- [ ] Score prediction (simple trend)
- [ ] Alert system (score threshold notifications)

## Phase 3: Professional Data
**Goal**: Bloomberg integration for internal Westwood use

### Data Integrations
- [ ] Bloomberg MCP provider
- [ ] Daily export workflow
- [ ] Manual CSV/JSON import
- [ ] Morningstar MCP provider
- [ ] Internal Westwood data feed

### Features
- [ ] Multi-user support (internal)
- [ ] Custom watchlists
- [ ] Sector-level MarketPulse
- [ ] Custom alert rules
- [ ] API key management

## Phase 4: Advanced Features
**Goal**: Differentiated, production-grade platform

### NLP & Narrative
- [ ] FinBERT sentiment model
- [ ] X/Twitter API integration
- [ ] Reddit API integration
- [ ] LLM-powered summarization
- [ ] Topic trend analysis
- [ ] Narrative shift detection

### Positioning
- [ ] ETF flow data (live)
- [ ] Fund flow data
- [ ] CFTC futures positioning
- [ ] Options skew analysis
- [ ] Margin debt tracking
- [ ] Prediction market data (Kalshi, Polymarket)

### Frontend
- [ ] Embeddable widget (public launch)
- [ ] Email digest generation
- [ ] PDF report generation
- [ ] Mobile app (React Native)
- [ ] Real-time WebSocket updates

## Phase 5: Scale & Ecosystem
**Goal**: Industry-recognized sentiment platform

### Expansion
- [ ] International markets (MSCI EAFE, EM)
- [ ] Sector-specific indices
- [ ] Commodity MarketPulse
- [ ] Crypto MarketPulse
- [ ] Custom index builder

### Distribution
- [ ] MarketWatch/Bloomberg distribution partnership
- [ ] Advisor platform integration
- [ ] White-label options
- [ ] API marketplace listing

## Timeline

| Phase | Target | Key Deliverable |
|-------|--------|-----------------|
| MVP | Month 1 | Working local app |
| Phase 2 | Month 2-3 | Public website live |
| Phase 3 | Month 4-6 | Bloomberg integration |
| Phase 4 | Month 6-12 | Full feature set |
| Phase 5 | Year 2+ | Scale and distribution |
