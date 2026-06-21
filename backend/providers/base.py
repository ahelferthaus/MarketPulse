"""Abstract base provider defining the Westwood MarketPulse provider interface.

All data providers — public, premium, and professional — must implement
:class:`BaseProvider`.  The :class:`ProviderChain` consumes this interface
and handles prioritized fallback across multiple providers.

Design principles
-----------------
* **Never raise on failure** — every coroutine must return ``None`` (or an
  empty collection) when data cannot be fetched.
* **Return typed structures** — use ``pd.DataFrame``, ``dict``, and Pydantic
  models so the indicator layer can rely on consistent shapes.
* **Implement :meth:`get_source_status`** — the admin UI and confidence
  engine depend on accurate provider health metadata.
"""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Abstract base class for all MarketPulse data providers.

    Attributes:
        name: Unique short identifier used in logs and the status endpoint.
        tier: Provider quality tier. One of ``"public"``, ``"premium"``,
            or ``"professional"``.  Lower numeric values = higher priority
            in the default :class:`ProviderChain` sort order.
    """

    name: str = "base"
    tier: str = "public"  # public | premium | professional

    # ------------------------------------------------------------------
    # Market data
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """Return daily OHLCV price history for *ticker*.

        The returned DataFrame must contain the following columns:
        ``date`` (datetime), ``open``, ``high``, ``low``, ``close``,
        ``volume`` (all float except volume which may be int).

        Args:
            ticker: Security ticker symbol (e.g. ``"SPY"``, ``"^VIX"``).
            days: Number of trading days to retrieve (default ~1 year).

        Returns:
            A DataFrame or ``None`` when data is unavailable.
        """
        ...

    @abstractmethod
    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the most recent quote for *ticker*.

        Expected return shape::

            {
                "price": float,
                "change": float,
                "change_percent": float,
                "volume": int,
                "timestamp": datetime,
            }

        Args:
            ticker: Security ticker symbol.

        Returns:
            Quote dict or ``None`` on failure.
        """
        ...

    @abstractmethod
    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Return market breadth indicators.

        Expected return shape::

            {
                "advancing": int,
                "declining": int,
                "advancing_volume": float,
                "declining_volume": float,
                "new_highs": int,
                "new_lows": int,
                "percent_above_ma_50": float,
                "percent_above_ma_200": float,
            }

        Args:
            market_id: Market identifier (e.g. ``"sp500"``, ``"nasdaq100"``).

        Returns:
            Breadth dict or ``None`` when data cannot be sourced.
        """
        ...

    # ------------------------------------------------------------------
    # Options & volatility
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Return options-market indicators for *ticker*.

        Expected return shape::

            {
                "put_volume": int,
                "call_volume": int,
                "put_call_ratio": float,
                "put_open_interest": int,
                "call_open_interest": int,
            }

        Args:
            ticker: Underlying ticker (usually the ETF proxy, e.g. ``"SPY"``).

        Returns:
            Options dict or ``None`` on failure.
        """
        ...

    # ------------------------------------------------------------------
    # Credit & macro
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Return credit spread observations.

        Expected return shape::

            {
                "hy_spread": float,   # High-yield OAS in basis points
                "ig_spread": float,   # Investment-grade OAS in basis points
                "timestamp": datetime,
            }

        Args:
            series_id: Primary FRED series to fetch.  Defaults to the
                Bank of America US High Yield OAS series.

        Returns:
            Spread dict or ``None``.
        """
        ...

    @abstractmethod
    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Return safe-haven asset prices and recent returns.

        Assets tracked: 20+ Year Treasury (``TLT``), Gold (``GLD``),
        and US Dollar Index (``UUP``).

        Expected return shape::

            {
                "TLT": {"price": float, "return_1d": float, "return_1w": float},
                "GLD": {"price": float, "return_1d": float, "return_1w": float},
                "UUP": {"price": float, "return_1d": float, "return_1w": float},
                "timestamp": datetime,
            }

        Returns:
            Safe-haven dict or ``None``.
        """
        ...

    # ------------------------------------------------------------------
    # News & social
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """Fetch financial news articles matching *query*.

        Args:
            query: Free-text search query or topic filter.
            limit: Maximum number of articles to return.

        Returns:
            List of :class:`Article` objects (may be empty).
        """
        ...

    @abstractmethod
    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """Fetch social-media posts matching *query*.

        Args:
            query: Free-text search query or hashtag.
            limit: Maximum number of posts to return.

        Returns:
            List of :class:`SocialPost` objects (may be empty).
        """
        ...

    # ------------------------------------------------------------------
    # Flows & positioning (stubs for future expansion)
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """Return fund-flow / positioning data for *ticker*.

        Expected return shape (stubs for now)::

            {
                "inflow": float,
                "outflow": float,
                "net_flow": float,
                "aum": float,
                "timestamp": datetime,
            }

        Args:
            ticker: ETF or fund ticker to query.

        Returns:
            Flows dict or ``None``.
        """
        ...

    # ------------------------------------------------------------------
    # Diagnostics
    # ------------------------------------------------------------------

    @abstractmethod
    async def get_source_status(self) -> SourceStatus:
        """Return the current health status of this provider.

        The status object is consumed by the ``/api/v1/sources/status``
        endpoint and the confidence engine when deciding whether to
        trust data from this provider.

        Returns:
            A fully-populated :class:`SourceStatus` instance.
        """
        ...
