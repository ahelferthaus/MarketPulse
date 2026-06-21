# Westwood MarketPulse — Methodology

## Overview
MarketPulse produces four daily 0-100 indices that measure market psychology from different angles. All scores are normalized to a 0-100 scale where:

**Empirically-Derived Five-Zone Framework (asymmetric frequency-based ranges):**

| Zone | Score Range | Label | Historical Frequency |
|------|-------------|-------|---------------------|
| MP-1 | 0-24 | Capitulation | ~8% |
| MP-2 | 25-44 | Defensive | ~23% |
| MP-3 | 45-55 | Neutral | ~38% |
| MP-4 | 56-75 | Risk-On | ~24% |
| MP-5 | 76-100 | Euphoria | ~7% |

The MP-3 band is intentionally narrow (10 points) reflecting the rarity of true balance in market psychology. These ranges are empirically derived from historical frequency analysis — market conditions spend far more time near neutral or in moderate risk-on/risk-off states than in extremes.

## MarketPulse Classic

Classic is a market-data-driven index inspired by the traditional fear/greed concept but implemented independently. It uses 7 components, each normalized to 0-100 and averaged.

### Component 1: Market Momentum (Weight: 1/7)
**What it measures**: Whether the market is trending above or below its medium-term moving average.
**Calculation**:
```
raw = (current_price / 125_day_sma - 1) * 100   # percent deviation
score = percentile_rank(raw, lookback=252d)      # 0-100
```
**Interpretation**: 100 = price far above 125d MA (strong momentum). 0 = price far below (weak momentum).
**Sources**: S&P 500 price data (yfinance, FMP, Bloomberg)

### Component 2: Stock Price Strength (Weight: 1/7)
**What it measures**: The ratio of stocks making new highs vs new lows.
**Calculation**:
```
if new_highs + new_lows > 0:
    raw = new_highs / (new_highs + new_lows) * 100
else:
    raw = 50  # neutral when no activity
score = percentile_rank(raw, lookback=252d)
```
**Fallback**: If new highs/lows unavailable, use % of stocks above 50-day MA as proxy.
**Interpretation**: 100 = many stocks making new highs (broad strength). 0 = many new lows (broad weakness).

### Component 3: Stock Price Breadth (Weight: 1/7)
**What it measures**: Whether advancing volume is dominating declining volume.
**Calculation**:
```
if advancing_volume + declining_volume > 0:
    raw = advancing_volume / (advancing_volume + declining_volume) * 100
else:
    raw = 50
score = percentile_rank(raw, lookback=252d)
```
**Fallback**: If breadth data unavailable, use % of stocks above 200-day MA.
**Interpretation**: 100 = strong breadth (volume flowing to gainers). 0 = weak breadth.

### Component 4: Put/Call Ratio (Weight: 1/7)
**What it measures**: Options market positioning. High put/call = defensive positioning.
**Calculation**:
```
raw = total_put_volume / total_call_volume   # CBOE total put/call
score = 100 - percentile_rank(raw, lookback=252d)   # INVERTED
```
**Interpretation**: 100 = very low put/call (complacent/call-heavy). 0 = very high put/call (fear/hedging).
**Note**: This component is inverted because high put/call indicates fear (low score).

### Component 5: Credit Spreads (Weight: 1/7)
**What it measures**: The premium investors demand for risky corporate bonds.
**Calculation**:
```
raw = high_yield_option_adjusted_spread   # from FRED (BAMLH0A0HYM2)
score = 100 - percentile_rank(raw, lookback=252d)   # INVERTED
```
**Interpretation**: 100 = tight spreads (risk appetite). 0 = wide spreads (risk aversion).

### Component 6: Volatility (Weight: 1/7)
**What it measures**: Market volatility as measured by VIX.
**Calculation**:
```
raw = VIX_level
score = 100 - percentile_rank(raw, lookback=252d)   # INVERTED
```
**Interpretation**: 100 = very low VIX (complacency). 0 = very high VIX (fear).

### Component 7: Safe Haven Demand (Weight: 1/7)
**What it measures**: Whether investors are fleeing to safe assets.
**Calculation**:
```
equity_return = SPY_20d_return
safe_return = weighted_basket_return(TLT=0.4, GLD=0.4, DXY=0.2, 20d)
raw = equity_return - safe_return   # positive = stocks outperforming safe havens
score = percentile_rank(raw, lookback=252d)
```
**Interpretation**: 100 = stocks strongly outperforming safe havens (risk-on). 0 = safe havens outperforming (risk-off).

### Classic Score Assembly
```
classic_score = weighted_average(components, weights=[1/7]*7)
```
If a component is missing, its weight is redistributed proportionally to available components. Confidence is reduced.

## MarketPulse Narrative

Narrative measures the emotional tone of financial markets through text analysis of news headlines, financial blogs, and social media. It uses 6 sentiment dimensions.

### Sentiment Dimensions

| Dimension | What It Detects | Score Impact |
|-----------|----------------|--------------|
| Panic | Crash, meltdown, crisis, collapse language | Lowers score significantly |
| Caution | Hedging, defensive, wary, uncertain language | Lowers score moderately |
| Uncertainty | Mixed signals, "wait and see", ambiguity | Lowers score slightly |
| Optimism | Growth, recovery, positive outlook language | Raises score moderately |
| Complacency | Low volatility, "goldilocks", risk-ignoring | Raises score slightly (warning) |
| Euphoria | Bubble, rocket, "can't lose", extreme bullish | Raises score significantly (warning) |

### Scoring Algorithm

**Step 1: Text ingestion**
- Collect articles from configured RSS feeds
- Apply quality filters (min length, deduplication, financial relevance)

**Step 2: Sentiment scoring (per article)**
- Rule-based keyword matching with financial sentiment lexicon
- Optional FinBERT for nuanced sentiment
- Classify into 6 dimensions (0-100 each)
- Assign topic tags

**Step 3: Aggregation**
```
for each dimension:
    dimension_score = average(top_n_most_relevant_articles)
    
# Map to 0-100 narrative score
narrative_score = f(panic, caution, uncertainty, optimism, complacency, euphoria)
```

The mapping function weights panic/caution/uncertainty more heavily at the low end and euphoria/complacency at the high end:
```
base = (optimism * 0.3 + euphoria * 0.1 + complacency * 0.1) 
       - (panic * 0.25 + caution * 0.15 + uncertainty * 0.1)
narrative_score = clamp(50 + base * 0.5, 0, 100)
```

**Step 4: Tracking**
- Track volume of stories (higher volume = more conviction)
- Track intensity (extreme language = higher intensity)
- Show top phrases driving the score

## MarketPulse Positioning & Flows

Positioning measures how investors are actually positioned through trading data, fund flows, and cross-asset behavior.

### Available Components (Tier 1 — Live)
| Component | Source | Calculation |
|-----------|--------|-------------|
| Put/Call (all) | CBOE | Same as Classic, but weighted more heavily |
| VIX Level | CBOE/yfinance | Same as Classic |
| VIX Term Structure | CBOE futures | Stub — needs futures data |
| Credit Spreads (HY, IG) | FRED | Same as Classic |
| Equity/Bond Relative | yfinance | SPY return minus TLT return, percentile rank |
| Safe Haven Flows | yfinance | Equity vs TLT/GLD/DXY composite |

### Stub Components (Tier 2 — Placeholder)
| Component | Source | Status |
|-----------|--------|--------|
| ETF Flows | ETF.com, FMP, Bloomberg | Needs premium API |
| Fund Flows | ICI, EPFR, Bloomberg | Needs premium/institutional |
| Futures Positioning | CFTC COT reports | Needs CFTC data feed |
| Options Skew | CBOE, ORATS | Needs options data API |
| Margin Debt | FINRA | Monthly, delayed |

### Positioning Score Assembly
```
available_weight = sum(weights_for_available_components)
positioning_score = weighted_average(available_components) * (100 / available_weight)
confidence = available_weight  # as percentage of ideal total
```

## MarketPulse Composite

The Composite is the headline index that blends the three sub-indices.

### Default Weights
| Index | Weight | Rationale |
|-------|--------|-----------|
| Classic | 40% | Most data-rich, most reliable |
| Narrative | 30% | Captures sentiment not in price data |
| Positioning | 30% | Captures actual investor behavior |

### Confidence Adjustment
```
# Adjust weights based on confidence
adjusted_classic = classic_score * classic_confidence
adjusted_narrative = narrative_score * narrative_confidence
adjusted_positioning = positioning_score * positioning_confidence

composite = (adjusted_classic + adjusted_narrative + adjusted_positioning) / 
            (classic_confidence + narrative_confidence + positioning_confidence)
```

## Normalization Methods

MarketPulse supports three normalization methods:

### Rolling Percentile (Default)
```
score = percentile_rank(current_value, rolling_window_values) * 100
```
- Uses **1260-day (5-year) rolling window** — balances statistical stability with responsiveness to regime changes
- Adapts to changing market regimes
- No look-ahead bias if window is strictly historical
- Market-specific calibration bounds for momentum normalization:
  | Market | Momentum Bounds | Notes |
  |--------|----------------|-------|
  | S&P 500 | ±15% | Standard large-cap |
  | Nasdaq 100 | ±20% | Higher inherent volatility |
  | Russell 2000 | ±18% | Liquidity filtering |
  | Dow Jones | ±15% | Blue-chip stability |
  | MSCI EM | ±25% | Currency adjustment |

### Min-Max
```
score = (current - min) / (max - min) * 100
```
- Uses rolling min/max over lookback period
- Sensitive to outliers
- Good for bounded metrics

### Z-Score
```
score = 50 + (current - mean) / std * 25   # scaled to 0-100 approximately
```
- Normalizes by standard deviation
- Can exceed 0-100 range (clamped)
- Good for normally distributed data

## Confidence Scoring

Confidence (0-100) reflects data quality:

### Factors
| Factor | Penalty | Description |
|--------|---------|-------------|
| Missing component | -10 each | Expected component unavailable |
| Substituted data | -5 each | Using proxy instead of primary source |
| Stale data (>4h) | -15 | Intraday data older than 4 hours |
| Stale data (>24h) | -25 | Daily data older than 24 hours |
| Source down | -20 | Primary provider unavailable, using fallback |
| Low article count | -10 | <10 articles for narrative |

### Component Substitution Hierarchy
When primary components are unavailable, specific substitution chains are applied with associated confidence penalties:

| Unavailable Component | Substitution Chain | Confidence Penalty |
|----------------------|-------------------|-------------------|
| Put/Call Ratio | ETF options → Index futures options → Implied vol surface | -15% |
| Junk Bond Spread | Broad HY index → IG spread → Sovereign spread | -10% |
| Safe Haven Demand | USD Treasury proxy → Currency movement → Omitted (6-comp) | -20% |
| VIX | Regional vol index → Historical realized vol → Omitted (6-comp) | -25% |

### Confidence Levels
| Range | Label | Display |
|-------|-------|---------|
| 90-100 | High | Green badge |
| 70-89 | Good | Blue badge |
| 50-69 | Moderate | Yellow badge |
| 30-49 | Low | Orange badge |
| 0-29 | Very Low | Red badge |

## Look-Ahead Bias Prevention

All historical backtests use **point-in-time data only**:
- Rolling windows use only data available as of the calculation date
- Percentile ranks are computed from historical distributions, not including future data
- News sentiment uses only articles published before the calculation timestamp
- This prevents overfitting and gives realistic historical performance estimates

## Daily Update Schedule

| Time (ET) | Action |
|-----------|--------|
| 04:00 | Pre-market: Refresh overnight data, update narrative with Asian/European session news |
| 09:35 | Market open: Initial intraday refresh |
| 10:00-15:30 | Every 15-30 min: Intraday price refresh |
| 16:35 | Market close: Full daily calculation with closing data |
| 17:00 | Generate static exports, update public site |

## Plain-English Explanation Engine

For every reading, the system generates:
1. **Today's bottom line**: One sentence summary (e.g., "Markets are risk-on, driven by strong momentum and positioning.")
2. **What changed**: Day-over-day comparison (e.g., "Narrative sentiment cooled 5 points after Fed comments.")
3. **What is driving the score**: Top 2-3 contributors
4. **What investors should watch**: Forward-looking cues
5. **What would move the index higher/lower**: Key data points to monitor
6. **Data confidence**: Source quality summary

These are generated algorithmically from component scores and changes, not by LLM (which would be optional on-demand).
