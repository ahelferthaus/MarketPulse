"""FRED (Federal Reserve Economic Data) provider.

Fetches macro-economic and credit-market time series from the St. Louis
Fed's FRED API.  Key series:

* ``BAMLH0A0HYM2`` — ICE BofA US High Yield Option-Adjusted Spread
* ``BAMLC0A0CM``  — ICE BofA US Corporate Option-Adjusted Spread (IG)
* ``DGS10``       — 10-Year Treasury Constant Maturity Rate
* ``DGS2``        — 2-Year Treasury Constant Maturity Rate

API key is **optional** — many FRED series are available without one,
though rate limits are stricter.

Data source: https://fred.stlouisfed.org/
"""

from __future__ import annotations

import logging
import os
import xml.etree.ElementTree as ET
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

# FRED API endpoints
_FRED_BASE = "https://api.stlouisfed.org/fred"
_FRED_OBSERVATIONS = f"{_FRED_BASE}/series/observations"

# Default series
_SERIES_HY = "BAMLH0A0HYM2"  # High Yield OAS
_SERIES_IG = "BAMLC0A0CM"  # Investment Grade OAS
_SERIES_10Y = "DGS10"  # 10Y Treasury
_SERIES_2Y = "DGS2"  # 2Y Treasury


class FREDProvider(BaseProvider):
    """Federal Reserve Economic Data (FRED) provider.

    Handles XML/JSON parsing, optional API-key injection, and graceful
    degradation when FRED is unreachable or a series has no recent data.
    """

    name: str = "fred"
    tier: str = "public"

    def __init__(self, api_key: Optional[str] = None) -> None:
        self.api_key = api_key or os.environ.get("FRED_API_KEY", "")
        self._last_fetch: Optional[datetime] = None
        self._error_count: int = 0
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Westwood-MarketPulse/1.0 (research@westwood.com)",
        })

    # ── internal helpers ──────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type((requests.RequestException,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=False,
    )
    def _fetch_series(
        self,
        series_id: str,
        limit: int = 10,
        file_type: str = "json",
    ) -> Optional[Dict[str, Any]]:
        """Low-level FRED API call."""
        params: Dict[str, Any] = {
            "series_id": series_id,
            "sort_order": "desc",
            "limit": limit,
            "file_type": file_type,
        }
        if self.api_key:
            params["api_key"] = self.api_key

        try:
            resp = self._session.get(_FRED_OBSERVATIONS, params=params, timeout=30)
            resp.raise_for_status()
            self._last_fetch = datetime.now(timezone.utc)

            if file_type == "json":
                data = resp.json()
                return data
            else:
                return {"xml": resp.text}
        except requests.HTTPError as exc:
            if exc.response is not None and exc.response.status_code == 429:
                logger.warning("FRED rate limit hit for series %s", series_id)
            else:
                logger.warning("FRED HTTP error for %s: %s", series_id, exc)
            self._error_count += 1
            raise
        except Exception as exc:
            self._error_count += 1
            logger.warning("FRED fetch error for %s: %s", series_id, exc)
            raise

    def _parse_json_observations(
        self, data: Dict[str, Any]
    ) -> Optional[pd.DataFrame]:
        """Parse FRED JSON observation response into a DataFrame."""
        obs = data.get("observations", [])
        if not obs:
            return None
        rows = []
        for o in obs:
            val = o.get("value")
            if val is None or val == ".":
                continue
            try:
                rows.append({
                    "date": pd.Timestamp(o["date"]),
                    "value": float(val),
                })
            except (ValueError, TypeError):
                continue
        if not rows:
            return None
        return pd.DataFrame(rows)

    def _latest_value(self, series_id: str) -> Optional[float]:
        """Fetch the most recent non-null observation for a series."""
        try:
            raw = self._fetch_series(series_id, limit=10, file_type="json")
            if raw is None:
                return None
            df = self._parse_json_observations(raw)
            if df is None or df.empty:
                return None
            return float(df.iloc[0]["value"])
        except Exception as exc:
            logger.debug("FREDProvider._latest_value(%s) failed: %s", series_id, exc)
            return None

    # ── BaseProvider implementation ───────────────────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """FRED does not provide equity price history — return None."""
        return None

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """FRED does not provide equity quotes — return None."""
        return None

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """FRED does not provide market breadth — return None."""
        return None

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """FRED does not provide options data — return None."""
        return None

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Fetch the latest HY and IG credit spreads from FRED.

        Even if the caller requests a specific *series_id*, we always
        fetch both HY and IG for completeness.
        """
        try:
            hy_val = self._latest_value(_SERIES_HY)
            ig_val = self._latest_value(_SERIES_IG)

            if hy_val is None and ig_val is None:
                return None

            return {
                "hy_spread": hy_val,
                "ig_spread": ig_val,
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as exc:
            self._error_count += 1
            logger.warning("FREDProvider.get_credit_spreads failed: %s", exc)
            return None

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Fetch latest 10Y and 2Y Treasury yields."""
        try:
            y10 = self._latest_value(_SERIES_10Y)
            y2 = self._latest_value(_SERIES_2Y)

            if y10 is None and y2 is None:
                return None

            return {
                "DGS10": y10,
                "DGS2": y2,
                "yield_curve_spread": round(y10 - y2, 4) if y10 and y2 else None,
                "timestamp": datetime.now(timezone.utc),
            }
        except Exception as exc:
            self._error_count += 1
            logger.warning("FREDProvider.get_safe_haven_assets failed: %s", exc)
            return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """FRED does not provide news — return empty list."""
        return []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """FRED does not provide social data — return empty list."""
        return []

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """FRED does not provide fund-flow data — return None."""
        return None

    async def get_source_status(self) -> SourceStatus:
        """Report availability based on last successful fetch."""
        age_minutes = None
        if self._last_fetch:
            age = datetime.now(timezone.utc) - self._last_fetch
            age_minutes = int(age.total_seconds() / 60)
        return SourceStatus(
            provider=self.name,
            available=self._last_fetch is not None,
            last_successful_fetch=self._last_fetch,
            error_count_24h=self._error_count,
            data_freshness_minutes=age_minutes,
            tier=self.tier,
        )
