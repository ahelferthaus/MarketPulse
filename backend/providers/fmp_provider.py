"""Financial Modeling Prep (FMP) provider.

FMP offers a comprehensive financial data API covering:

* Historical and real-time stock prices
* Financial statements
* News articles
* ETF holdings and fund flows (premium endpoints)

This provider implements the full :class:`BaseProvider` interface.
When ``FMP_API_KEY`` is set, live data is fetched from the FMP API.
When no key is available, all methods return ``None`` so the
:class:`ProviderChain` falls back to other providers.

API documentation: https://site.financialmodelingprep.com/developer/docs
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
import requests
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)

_FMP_BASE = "https://financialmodelingprep.com/api/v3"


class FMPProvider(BaseProvider):
    """Financial Modeling Prep data provider.

    Implements live data fetching when ``FMP_API_KEY`` is configured,
    with graceful degradation to ``None`` when the key is missing.
    """

    name: str = "fmp"
    tier: str = "premium"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("FMP_API_KEY", "")
        self._has_key = bool(self.api_key)
        self._last_fetch: Optional[datetime] = None
        self._error_count: int = 0
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Westwood-MarketPulse/1.0",
        })

        if not self._has_key:
            logger.info(
                "FMP_API_KEY not set — FMPProvider will return None for all calls"
            )

    # ── internal helpers ──────────────────────────────────────────────

    def _build_url(self, endpoint: str, extra_params: Optional[Dict[str, str]] = None) -> str:
        params = {"apikey": self.api_key}
        if extra_params:
            params.update(extra_params)
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        return f"{_FMP_BASE}/{endpoint}?{qs}"

    @retry(
        retry=retry_if_exception_type((requests.RequestException,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=False,
    )
    def _get(self, endpoint: str, extra_params: Optional[Dict[str, str]] = None) -> Optional[Any]:
        """Authenticated GET to FMP API."""
        if not self._has_key:
            return None
        url = self._build_url(endpoint, extra_params)
        resp = self._session.get(url, timeout=20)
        resp.raise_for_status()
        self._last_fetch = datetime.now(timezone.utc)
        return resp.json()

    # ── BaseProvider implementation ───────────────────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """Fetch historical daily prices from FMP.

        Endpoint: ``historical-price-everything/{symbol}``
        """
        try:
            data = self._get(
                f"historical-price-everything/{ticker}",
                {"timeseries": str(days)},
            )
            if data is None or not isinstance(data, dict):
                return None

            hist = data.get("historical", [])
            if not hist:
                return None

            df = pd.DataFrame(hist)
            df = df.rename(columns={
                "date": "date",
                "open": "open",
                "high": "high",
                "low": "low",
                "close": "close",
                "volume": "volume",
            })
            df["date"] = pd.to_datetime(df["date"])
            df = df.sort_values("date").reset_index(drop=True)
            return df[["date", "open", "high", "low", "close", "volume"]]
        except Exception as exc:
            self._error_count += 1
            logger.warning("FMPProvider.get_price_history(%s) failed: %s", ticker, exc)
            return None

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch real-time quote from FMP.

        Endpoint: ``quote/{symbol}``

        Sample response::

            [
              {
                "symbol": "AAPL",
                "price": 189.52,
                "change": 1.23,
                "changesPercentage": 0.65,
                "volume": 54200000
              }
            ]
        """
        try:
            data = self._get(f"quote/{ticker}")
            if not data or not isinstance(data, list):
                return None

            q = data[0]
            return {
                "price": float(q.get("price", 0)),
                "change": float(q.get("change", 0)),
                "change_percent": float(q.get("changesPercentage", 0)),
                "volume": int(q.get("volume", 0)),
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as exc:
            self._error_count += 1
            logger.warning("FMPProvider.get_current_quote(%s) failed: %s", ticker, exc)
            return None

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Market breadth is a premium FMP endpoint — not implemented."""
        return None

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Options data stub — FMP offers options chain data on premium plans.

        Would call: ``historical/options/{symbol}`` or ``options/{symbol}``
        """
        logger.debug("FMPProvider.get_options_data is a stub")
        return None

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Credit spreads are not available via FMP — return None."""
        return None

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Fetch TLT, GLD, UUP quotes individually."""
        try:
            results: Dict[str, Any] = {}
            for sym in ("TLT", "GLD", "UUP"):
                data = self._get(f"quote/{sym}")
                if data and isinstance(data, list) and len(data) > 0:
                    q = data[0]
                    results[sym] = {
                        "price": float(q.get("price", 0)),
                        "return_1d": round(float(q.get("changesPercentage", 0)) / 100, 4),
                        "return_1w": None,
                    }
            if not results:
                return None
            results["timestamp"] = datetime.now(timezone.utc)
            return results
        except Exception as exc:
            self._error_count += 1
            logger.warning("FMPProvider.get_safe_haven_assets failed: %s", exc)
            return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """Fetch financial news from FMP.

        Endpoint: ``fmp/articles`` or ``stock_news``

        Sample response element::

            {
              "title": "Apple Reports Record Q4 Earnings",
              "date": "2024-01-15T14:30:00.000Z",
              "link": "https://...",
              "site": "Yahoo Finance",
              "text": "Apple Inc. reported..."
            }
        """
        if not self._has_key:
            return []

        try:
            data = self._get("stock_news", {"limit": str(limit), "query": query})
            if not data or not isinstance(data, list):
                return []

            articles: List[Article] = []
            for item in data[:limit]:
                pub_str = item.get("publishedDate", item.get("date", ""))
                try:
                    pub_time = datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except (ValueError, TypeError):
                    pub_time = datetime.now(timezone.utc)

                article_id = item.get("symbol", "") + "_" + str(hash(item.get("title", "")))
                articles.append(Article(
                    id=article_id[:32],
                    timestamp=pub_time,
                    source=item.get("site", "FMP"),
                    title=item.get("title", ""),
                    url=item.get("url", item.get("link", "")),
                    description=item.get("text", "")[:500],
                    sentiment_score=None,
                    topics=[],
                    market_relevance=0.5,
                ))
            return articles
        except Exception as exc:
            self._error_count += 1
            logger.warning("FMPProvider.get_news_articles failed: %s", exc)
            return []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """Social posts are not available via FMP — return empty list."""
        return []

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """Fund flows stub — FMP premium endpoint.

        Would call: ``etf-holder/{symbol}`` or ``institutional-ownership/...``
        to derive AUM and flow estimates.
        """
        logger.debug("FMPProvider.get_flows_data is a stub — requires premium plan")
        return None

    async def get_source_status(self) -> SourceStatus:
        age_minutes = None
        if self._last_fetch:
            age = datetime.now(timezone.utc) - self._last_fetch
            age_minutes = int(age.total_seconds() / 60)
        return SourceStatus(
            provider=self.name,
            available=self._has_key and self._last_fetch is not None,
            last_successful_fetch=self._last_fetch,
            error_count_24h=self._error_count,
            data_freshness_minutes=age_minutes,
            tier=self.tier,
        )
