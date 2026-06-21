"""Mock data provider — generates realistic synthetic market data.

This provider is **guaranteed to work with zero external dependencies**
and zero API keys.  It is intended for:

* Local development & demo mode
* CI / automated test pipelines
* Fallback when all real providers fail
* Front-end prototyping before API credentials are configured

The synthetic data follows realistic statistical properties:

* Equity prices: geometric Brownian motion with ~16 % annualised vol
  and a slight positive drift.
* VIX: mean-reverting Ornstein-Uhlenbeck process centred around 18-20.
* Credit spreads: HY ~350-500 bp, IG ~100-150 bp.
* Put/call ratio: uniformly distributed in [0.7, 1.2].
* News: 20 hand-curried financial headlines with varied sentiment.
"""

from __future__ import annotations

import hashlib
import logging
import random
import string
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)

# ── Realistic headline bank ──────────────────────────────────────────

_HEADLINES: List[Dict[str, Any]] = [
    {"title": "S&P 500 Hits New All-Time High as Tech Rally Accelerates",
     "sentiment": 0.75, "topics": ["macro", "ai_tech"], "source": "Yahoo Finance"},
    {"title": "Federal Reserve Signals Potential Rate Cuts in Coming Months",
     "sentiment": 0.60, "topics": ["fed", "macro"], "source": "Reuters"},
    {"title": "Inflation Data Comes in Cooler Than Expected, Bonds Rally",
     "sentiment": 0.65, "topics": ["inflation", "macro"], "source": "MarketWatch"},
    {"title": "Tech Giants Report Strong Earnings, Cloud Revenue Surges",
     "sentiment": 0.80, "topics": ["earnings", "ai_tech"], "source": "Seeking Alpha"},
    {"title": "Geopolitical Tensions Rise in Middle East, Oil Prices Spike",
     "sentiment": -0.55, "topics": ["geopolitics"], "source": "Reuters"},
    {"title": "Credit Markets Show Signs of Stress as HY Spreads Widen",
     "sentiment": -0.45, "topics": ["credit"], "source": "MarketWatch"},
    {"title": "Consumer Spending Remains Resilient Despite Economic Headwinds",
     "sentiment": 0.30, "topics": ["consumer", "macro"], "source": "Yahoo Finance"},
    {"title": "Banking Sector Under Pressure After Regional Bank Earnings Miss",
     "sentiment": -0.50, "topics": ["banking_stress", "earnings"], "source": "Reuters"},
    {"title": "AI Stocks Lead Market Gains as Enterprise Adoption Accelerates",
     "sentiment": 0.85, "topics": ["ai_tech"], "source": "Seeking Alpha"},
    {"title": "Treasury Yields Fall on Safe-Haven Buying Amid Market Volatility",
     "sentiment": -0.20, "topics": ["macro", "liquidity"], "source": "MarketWatch"},
    {"title": "European Markets Rally on ECB Stimulus Hopes",
     "sentiment": 0.55, "topics": ["macro"], "source": "Reuters"},
    {"title": "Hedge Funds Trim Equity Exposure as Risk Appetite Wanes",
     "sentiment": -0.40, "topics": ["positioning", "flows"], "source": "Yahoo Finance"},
    {"title": "Retail Investors Pour Money Into Magnificent Seven Stocks",
     "sentiment": 0.70, "topics": ["retail", "ai_tech"], "source": "Seeking Alpha"},
    {"title": "Recession Fears Resurface as Manufacturing Data Weakens",
     "sentiment": -0.65, "topics": ["recession", "macro"], "source": "MarketWatch"},
    {"title": "IPO Market Shows Signs of Life With Multiple Tech Listings",
     "sentiment": 0.50, "topics": ["valuation", "ai_tech"], "source": "Yahoo Finance"},
    {"title": "Dollar Index Rises to Multi-Month High on Rate Differential",
     "sentiment": 0.10, "topics": ["macro", "fed"], "source": "Reuters"},
    {"title": "Corporate Buybacks Hit Record Levels in Q3",
     "sentiment": 0.45, "topics": ["flows", "earnings"], "source": "Seeking Alpha"},
    {"title": "Market Volatility Index Jumps on Options Expiration",
     "sentiment": -0.30, "topics": ["volatility"], "source": "MarketWatch"},
    {"title": "Analysts Warn of Overvaluation in Mega-Cap Tech Sector",
     "sentiment": -0.35, "topics": ["valuation", "ai_tech"], "source": "Yahoo Finance"},
    {"title": "Commodity Prices Rally on Supply Concerns and China Demand",
     "sentiment": 0.40, "topics": ["commodities", "macro"], "source": "Reuters"},
]

_SOCIAL_POSTS: List[Dict[str, Any]] = [
    {"author": "TraderTom", "content": "SPY breaking above resistance, bulls in control 🚀", "sentiment": 0.8, "platform": "stocktwits", "engagement": 245},
    {"author": "BearHunter", "content": "VIX spiking — time to hedge long positions", "sentiment": -0.6, "platform": "stocktwits", "engagement": 189},
    {"author": "FedWatcher", "content": "Powell's speech was more dovish than expected. Rate cuts coming.", "sentiment": 0.5, "platform": "reddit", "engagement": 1203},
    {"author": "ValueInvestor", "content": "These valuations don't make sense. TTM P/E at 25+ is unsustainable.", "sentiment": -0.4, "platform": "reddit", "engagement": 567},
    {"author": "CryptoKing", "content": "BTC correlation with SPY is breaking down. Interesting divergence.", "sentiment": 0.2, "platform": "reddit", "engagement": 892},
    {"author": "OptionFlow", "content": "Massive call buying detected on AAPL ahead of earnings", "sentiment": 0.7, "platform": "stocktwits", "engagement": 445},
    {"author": "MacroMacro", "content": "Yield curve uninversion — watch the 2s10s closely", "sentiment": -0.3, "platform": "reddit", "engagement": 334},
    {"author": "DividendDad", "content": "Loading up on utilities and REITs for defensive positioning", "sentiment": -0.2, "platform": "stocktwits", "engagement": 156},
    {"author": "GrowthHunter", "content": "NVDA guidance was insane. AI boom is just getting started.", "sentiment": 0.9, "platform": "stocktwits", "engagement": 678},
    {"author": "RiskManager", "content": "Trimming risk exposure. HY spreads widening is a warning sign.", "sentiment": -0.5, "platform": "reddit", "engagement": 223},
]


class MockProvider(BaseProvider):
    """Synthetic data provider with realistic market statistics.

    Every method is fully implemented and returns deterministic-yet-
    realistic data.  No network calls, no API keys, no external
    dependencies beyond NumPy / pandas.
    """

    name: str = "mock"
    tier: str = "public"

    # Deterministic seed so repeated calls in the same process produce
    # consistent results unless refreshed.
    _rng: np.random.Generator = np.random.default_rng(42)

    # ── internal helpers ──────────────────────────────────────────────

    def _trading_dates(self, days: int) -> pd.DatetimeIndex:
        """Generate approximately *days* trading dates ending today."""
        # Add ~30 % buffer for weekends/holidays
        calendar_days = int(days * 1.4)
        end = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start = end - timedelta(days=calendar_days)
        dates = pd.bdate_range(start=start, end=end)
        return dates[-days:]

    def _gbm(
        self,
        n: int,
        mu: float = 0.08,  # 8 % annual drift
        sigma: float = 0.16,  # 16 % annual vol
        s0: float = 100.0,
    ) -> np.ndarray:
        """Geometric Brownian motion price path."""
        dt = 1 / 252  # daily
        returns = self._rng.normal(
            loc=mu * dt, scale=sigma * np.sqrt(dt), size=n
        )
        log_prices = np.log(s0) + np.cumsum(returns)
        return np.exp(log_prices)

    def _ou_process(
        self,
        n: int,
        theta: float = 0.15,  # mean-reversion speed
        mu: float = 18.0,  # long-run mean
        sigma: float = 5.0,
        x0: Optional[float] = None,
    ) -> np.ndarray:
        """Ornstein-Uhlenbeck process for VIX-like mean reversion."""
        x = np.zeros(n)
        x[0] = x0 if x0 is not None else mu
        dt = 1 / 252
        for t in range(1, n):
            dx = theta * (mu - x[t - 1]) * dt + sigma * np.sqrt(dt) * self._rng.normal()
            x[t] = max(x[t - 1] + dx, 5.0)  # VIX floor ~5
        return x

    # ── BaseProvider implementation ───────────────────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """Synthetic OHLCV from a geometric Brownian motion."""
        try:
            dates = self._trading_dates(days)
            n = len(dates)

            # Use ticker as additional seed for per-ticker variation
            ticker_seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % (2**31)
            rng = np.random.default_rng(42 + ticker_seed)

            close = self._gbm(n, s0=100.0 + (ticker_seed % 400))
            # Intraday noise
            high = close * (1 + rng.uniform(0.001, 0.015, size=n))
            low = close * (1 - rng.uniform(0.001, 0.015, size=n))
            open_ = close * (1 + rng.normal(0, 0.005, size=n))
            volume = rng.integers(50_000_000, 200_000_000, size=n)

            df = pd.DataFrame({
                "date": dates,
                "open": np.round(open_, 2),
                "high": np.round(high, 2),
                "low": np.round(low, 2),
                "close": np.round(close, 2),
                "volume": volume,
            })
            logger.debug("MockProvider generated %d rows for %s", len(df), ticker)
            return df
        except Exception as exc:
            logger.warning("MockProvider.get_price_history failed: %s", exc)
            return None

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Synthetic last-sale quote."""
        try:
            ticker_seed = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % (2**31)
            rng = np.random.default_rng(42 + ticker_seed)
            base_price = 100.0 + (ticker_seed % 400)
            change = rng.normal(0, base_price * 0.008)
            return {
                "price": round(base_price, 2),
                "change": round(change, 2),
                "change_percent": round(change / base_price * 100, 2),
                "volume": int(rng.integers(50_000_000, 200_000_000)),
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as exc:
            logger.warning("MockProvider.get_current_quote failed: %s", exc)
            return None

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Synthetic market breadth."""
        try:
            rng = self._rng
            adv = int(rng.integers(250, 450))
            dec = int(rng.integers(150, 350))
            return {
                "advancing": adv,
                "declining": dec,
                "advancing_volume": float(rng.uniform(1.5e9, 3.5e9)),
                "declining_volume": float(rng.uniform(0.8e9, 2.5e9)),
                "new_highs": int(rng.integers(30, 150)),
                "new_lows": int(rng.integers(10, 80)),
                "percent_above_ma_50": float(rng.uniform(35, 75)),
                "percent_above_ma_200": float(rng.uniform(40, 85)),
            }
        except Exception as exc:
            logger.warning("MockProvider.get_breadth_data failed: %s", exc)
            return None

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Synthetic put/call and volume data."""
        try:
            rng = self._rng
            put_vol = int(rng.integers(800_000, 1_500_000))
            call_vol = int(rng.integers(1_000_000, 2_000_000))
            pcr = round(rng.uniform(0.7, 1.2), 3)
            return {
                "put_volume": put_vol,
                "call_volume": call_vol,
                "put_call_ratio": pcr,
                "put_open_interest": int(put_vol * rng.uniform(8, 15)),
                "call_open_interest": int(call_vol * rng.uniform(8, 15)),
            }
        except Exception as exc:
            logger.warning("MockProvider.get_options_data failed: %s", exc)
            return None

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Synthetic HY and IG credit spreads."""
        try:
            rng = self._rng
            return {
                "hy_spread": float(rng.uniform(350, 500)),
                "ig_spread": float(rng.uniform(100, 150)),
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as exc:
            logger.warning("MockProvider.get_credit_spreads failed: %s", exc)
            return None

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Synthetic TLT, GLD, UUP prices and returns."""
        try:
            rng = self._rng
            now = datetime.now(timezone.utc)

            def _asset(price: float) -> Dict[str, Any]:
                return {
                    "price": round(price + rng.normal(0, price * 0.005), 2),
                    "return_1d": round(rng.normal(0, 0.008), 4),
                    "return_1w": round(rng.normal(0, 0.018), 4),
                }

            return {
                "TLT": _asset(95.0),
                "GLD": _asset(185.0),
                "UUP": _asset(28.0),
                "timestamp": now,
            }
        except Exception as exc:
            logger.warning("MockProvider.get_safe_haven_assets failed: %s", exc)
            return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """Return a shuffled subset of the headline bank."""
        try:
            rng = np.random.default_rng(42)
            now = datetime.now(timezone.utc)
            shuffled = _HEADLINES.copy()
            rng.shuffle(shuffled)
            selected = shuffled[:limit]

            articles: List[Article] = []
            for i, h in enumerate(selected):
                pub_time = now - timedelta(hours=int(rng.integers(1, 72)))
                article_id = hashlib.sha256(
                    f"{h['title']}{pub_time.isoformat()}".encode()
                ).hexdigest()[:16]
                articles.append(Article(
                    id=article_id,
                    timestamp=pub_time,
                    source=h["source"],
                    title=h["title"],
                    url=f"https://example.com/article/{article_id}",
                    description=f"Detailed analysis of {h['title'].lower()}...",
                    sentiment_score=h["sentiment"],
                    topics=h["topics"],
                    market_relevance=round(rng.uniform(0.5, 1.0), 2),
                ))
            logger.debug("MockProvider generated %d articles for query '%s'", len(articles), query)
            return articles
        except Exception as exc:
            logger.warning("MockProvider.get_news_articles failed: %s", exc)
            return []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """Return synthetic social posts with cycling."""
        try:
            rng = np.random.default_rng(42)
            now = datetime.now(timezone.utc)
            posts: List[SocialPost] = []
            for i in range(limit):
                template = _SOCIAL_POSTS[i % len(_SOCIAL_POSTS)]
                post_time = now - timedelta(minutes=int(rng.integers(5, 360)))
                post_id = hashlib.sha256(
                    f"{template['author']}{i}{post_time.isoformat()}".encode()
                ).hexdigest()[:16]
                posts.append(SocialPost(
                    id=post_id,
                    timestamp=post_time,
                    platform=template["platform"],
                    author=template["author"],
                    content=template["content"],
                    sentiment_score=template["sentiment"],
                    engagement_score=float(template["engagement"]),
                    topics=[],
                    market_relevance=round(rng.uniform(0.4, 0.9), 2),
                ))
            return posts
        except Exception as exc:
            logger.warning("MockProvider.get_social_posts failed: %s", exc)
            return []

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """Synthetic fund-flow stub data."""
        try:
            rng = self._rng
            inflow = float(rng.uniform(500e6, 2_000e6))
            outflow = float(rng.uniform(200e6, 1_500e6))
            return {
                "inflow": round(inflow, 2),
                "outflow": round(outflow, 2),
                "net_flow": round(inflow - outflow, 2),
                "aum": float(rng.uniform(400e9, 600e9)),
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as exc:
            logger.warning("MockProvider.get_flows_data failed: %s", exc)
            return None

    async def get_source_status(self) -> SourceStatus:
        """Always available."""
        return SourceStatus(
            provider=self.name,
            available=True,
            last_successful_fetch=datetime.now(timezone.utc),
            error_count_24h=0,
            avg_response_ms=5,
            data_freshness_minutes=0,
            tier=self.tier,
        )
