"""Yahoo Finance provider — real-time and historical market data.

Uses the ``yfinance`` library to fetch:

* Price history (OHLCV) for any ticker
* Current quotes
* VIX data via ``^VIX``
* Safe-haven asset prices (TLT, GLD, UUP)

Failure handling
----------------
All methods return ``None`` on failure so the :class:`ProviderChain` can
fall back to the next provider.  Transient errors (rate limits, network
blips) are retried with :mod:`tenacity`.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd
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

# ── yfinance is an optional dependency ───────────────────────────────

try:
    import yfinance as yf

    _HAS_YFINANCE = True
except ImportError:  # pragma: no cover
    yf = None  # type: ignore[assignment]
    _HAS_YFINANCE = False


class YFinanceProvider(BaseProvider):
    """Yahoo Finance data provider.

    Wraps the ``yfinance`` library with async-compatible execution,
    retry logic, and graceful degradation.
    """

    name: str = "yahoo_finance"
    tier: str = "public"

    # Cache the last successful fetch time per ticker for status reporting
    _last_fetch: Dict[str, datetime] = {}
    _error_count: int = 0

    def __init__(self) -> None:
        if not _HAS_YFINANCE:
            logger.warning(
                "yfinance is not installed — YFinanceProvider will be unavailable"
            )

    # ── internal helpers ──────────────────────────────────────────────

    @staticmethod
    def _sync_download(ticker: str, period: str, interval: str) -> pd.DataFrame:
        """Synchronous yfinance call (executed in thread pool)."""
        if yf is None:
            raise RuntimeError("yfinance not installed")
        t = yf.Ticker(ticker)
        df = t.history(period=period, interval=interval, auto_adjust=True)
        if df.empty:
            raise ValueError(f"No data returned for {ticker}")
        return df

    @retry(
        retry=retry_if_exception_type((RuntimeError, ValueError, Exception)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=False,
    )
    def _download_with_retry(
        self, ticker: str, period: str, interval: str
    ) -> Optional[pd.DataFrame]:
        try:
            df = self._sync_download(ticker, period, interval)
            self._last_fetch[ticker] = datetime.now(timezone.utc)
            return df
        except Exception as exc:
            self._error_count += 1
            logger.warning("yfinance download failed for %s: %s", ticker, exc)
            raise

    def _normalize_ohlcv(self, raw: pd.DataFrame) -> pd.DataFrame:
        """Normalize yfinance column names to the BaseProvider contract."""
        raw = raw.reset_index()
        col_map = {
            "Date": "date",
            "Datetime": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
        raw = raw.rename(columns={k: v for k, v in col_map.items() if k in raw.columns})
        # Select only expected columns
        expected = ["date", "open", "high", "low", "close", "volume"]
        available = [c for c in expected if c in raw.columns]
        return raw[available].copy()

    # ── BaseProvider implementation ───────────────────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """Fetch daily OHLCV from Yahoo Finance.

        Args:
            ticker: Yahoo Finance ticker (e.g. ``"SPY"``, ``"^VIX"``).
            days: Number of calendar days to request.

        Returns:
            Normalized DataFrame or ``None``.
        """
        if not _HAS_YFINANCE:
            return None

        try:
            # yfinance period strings
            period = f"{max(days, 5)}d" if days <= 730 else "max"
            raw = self._download_with_retry(ticker, period=period, interval="1d")
            if raw is None:
                return None
            df = self._normalize_ohlcv(raw)
            # Trim to requested trading-day count (approximate)
            if len(df) > days:
                df = df.iloc[-days:]
            logger.debug("YFinanceProvider fetched %d rows for %s", len(df), ticker)
            return df
        except Exception as exc:
            logger.warning("YFinanceProvider.get_price_history(%s) failed: %s", ticker, exc)
            return None

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch the most recent quote via yfinance fast_info."""
        if not _HAS_YFINANCE:
            return None

        try:
            import asyncio

            loop = asyncio.get_event_loop()
            t = yf.Ticker(ticker)
            info = await loop.run_in_executor(None, lambda: t.fast_info)
            if info is None:
                return None

            last_price = getattr(info, "last_price", None)
            prev_close = getattr(info, "previous_close", None)
            if last_price is None or prev_close is None:
                return None

            change = last_price - prev_close
            change_pct = (change / prev_close) * 100 if prev_close else 0.0

            self._last_fetch[ticker] = datetime.now(timezone.utc)
            return {
                "price": round(float(last_price), 4),
                "change": round(float(change), 4),
                "change_percent": round(float(change_pct), 4),
                "volume": int(getattr(info, "last_volume", 0)),
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as exc:
            self._error_count += 1
            logger.warning("YFinanceProvider.get_current_quote(%s) failed: %s", ticker, exc)
            return None

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Breadth data is not available via yfinance for free — return None."""
        logger.debug("YFinanceProvider does not support breadth_data")
        return None

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Options data is limited via yfinance — return None for now."""
        logger.debug("YFinanceProvider does not support options_data")
        return None

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Credit spreads are not available via yfinance — return None."""
        return None

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Fetch TLT, GLD, UUP quotes concurrently."""
        if not _HAS_YFINANCE:
            return None

        import asyncio

        tickers = ["TLT", "GLD", "UUP"]
        try:
            results: Dict[str, Any] = {}
            loop = asyncio.get_event_loop()

            for sym in tickers:
                try:
                    t = yf.Ticker(sym)
                    info = await loop.run_in_executor(None, lambda _t=t: _t.fast_info)
                    price = getattr(info, "last_price", None)
                    prev = getattr(info, "previous_close", None)
                    if price and prev:
                        results[sym] = {
                            "price": round(float(price), 2),
                            "return_1d": round((float(price) - float(prev)) / float(prev), 4),
                            "return_1w": None,  # would need history
                        }
                        self._last_fetch[sym] = datetime.now(timezone.utc)
                except Exception as sub_exc:
                    logger.debug("Safe-haven fetch failed for %s: %s", sym, sub_exc)

            if not results:
                return None

            results["timestamp"] = datetime.now(timezone.utc)
            return results
        except Exception as exc:
            self._error_count += 1
            logger.warning("YFinanceProvider.get_safe_haven_assets failed: %s", exc)
            return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """News is not reliably available via yfinance — return empty list."""
        return []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """Social posts are not available via yfinance — return empty list."""
        return []

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """Fund flows are not available via yfinance — return None."""
        return None

    async def get_source_status(self) -> SourceStatus:
        """Report availability based on whether yfinance is installed."""
        available = _HAS_YFINANCE and bool(self._last_fetch)
        last_fetch = max(self._last_fetch.values()) if self._last_fetch else None
        age_minutes = None
        if last_fetch:
            age = datetime.now(timezone.utc) - last_fetch
            age_minutes = int(age.total_seconds() / 60)
        return SourceStatus(
            provider=self.name,
            available=available,
            last_successful_fetch=last_fetch,
            error_count_24h=self._error_count,
            data_freshness_minutes=age_minutes,
            tier=self.tier,
        )
