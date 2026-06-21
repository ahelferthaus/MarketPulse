"""CBOE (Chicago Board Options Exchange) data provider.

Fetches options-market statistics, primarily:

* **Total put/call ratio** — the aggregate ratio of put volume to call
  volume across all CBOE-listed options.

Data sources
------------
The CBOE publishes daily market statistics at:
https://www.cboe.com/us/options/market_statistics/daily/

This provider attempts to scrape the public page and falls back to a
hardcoded recent baseline if the site is unavailable or the layout
changes.

"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

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

_CBOE_DAILY_URL = "https://www.cboe.com/us/options/market_statistics/daily/"
_CBOE_PC_JSON = "https://cdn.cboe.com/api/global/us_pref/daily_put_call.json"

# Fallback baseline — recent historical average
_FALLBACK_PUT_CALL_RATIO = 0.85


class CBOEProvider(BaseProvider):
    """CBOE options and volatility statistics provider.

    Public-tier provider that scrapes CBOE's published daily statistics.
    If scraping fails, returns a cached fallback value so the indicator
    layer can still compute a score (with reduced confidence).
    """

    name: str = "cboe"
    tier: str = "public"

    def __init__(self) -> None:
        self._last_fetch: Optional[datetime] = None
        self._error_count: int = 0
        self._cached_ratio: Optional[float] = None
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Westwood-MarketPulse/1.0 (research@westwood.com)",
            "Accept": "application/json, text/html",
        })

    # ── internal helpers ──────────────────────────────────────────────

    @retry(
        retry=retry_if_exception_type((requests.RequestException,)),
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=False,
    )
    def _fetch_json_ratio(self) -> Optional[float]:
        """Try the CBOE JSON endpoint first (undocumented but stable)."""
        resp = self._session.get(_CBOE_PC_JSON, timeout=20)
        resp.raise_for_status()
        data = resp.json()

        # The JSON is a list of daily records
        if isinstance(data, list) and len(data) > 0:
            latest = data[-1]
            ratio = latest.get("put_call_ratio") or latest.get("P/C Ratio")
            if ratio is not None:
                return float(ratio)

        # Try alternate key names
        if isinstance(data, dict):
            for key in ("put_call_ratio", "P/C Ratio", "total_put_call_ratio"):
                if key in data:
                    return float(data[key])

        return None

    @retry(
        retry=retry_if_exception_type((requests.RequestException,)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        reraise=False,
    )
    def _fetch_html_ratio(self) -> Optional[float]:
        """Fallback: scrape the CBOE daily statistics HTML page."""
        resp = self._session.get(_CBOE_DAILY_URL, timeout=20)
        resp.raise_for_status()
        text = resp.text

        # Look for put/call ratio in the page
        patterns = [
            r'Put/Call\s*Ratio[^\d]*(\d+\.\d+)',
            r'P/C\s*Ratio[^\d]*(\d+\.\d+)',
            r'put.call.ratio[^\d]*(\d+\.\d+)',
            r'total[^\d]*(\d+\.\d+)[^\d]*put[^\d]*call',
        ]
        for pat in patterns:
            match = re.search(pat, text, re.IGNORECASE)
            if match:
                return float(match.group(1))

        return None

    def _get_put_call_ratio(self) -> Optional[float]:
        """Best-effort fetch with fallback chain."""
        try:
            ratio = self._fetch_json_ratio()
            if ratio is not None:
                self._cached_ratio = ratio
                self._last_fetch = datetime.now(timezone.utc)
                return ratio
        except Exception as exc:
            logger.debug("CBOE JSON endpoint failed: %s", exc)

        try:
            ratio = self._fetch_html_ratio()
            if ratio is not None:
                self._cached_ratio = ratio
                self._last_fetch = datetime.now(timezone.utc)
                return ratio
        except Exception as exc:
            logger.debug("CBOE HTML scrape failed: %s", exc)

        # Final fallback
        self._error_count += 1
        if self._cached_ratio is not None:
            logger.info("CBOE using cached put/call ratio: %.3f", self._cached_ratio)
            return self._cached_ratio

        logger.info("CBOE using hardcoded baseline ratio: %.3f", _FALLBACK_PUT_CALL_RATIO)
        return _FALLBACK_PUT_CALL_RATIO

    # ── BaseProvider implementation ───────────────────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """CBOE does not provide equity price history — return None."""
        return None

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """CBOE does not provide equity quotes — return None."""
        return None

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """CBOE does not provide market breadth — return None."""
        return None

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the CBOE total put/call ratio.

        The return shape follows the BaseProvider contract::

            {
                "put_volume": int,      # estimated from ratio
                "call_volume": int,
                "put_call_ratio": float,
                "put_open_interest": int,   # stub
                "call_open_interest": int,  # stub
            }
        """
        try:
            ratio = self._get_put_call_ratio()
            if ratio is None:
                return None

            # Estimate volumes based on typical CBOE daily totals
            estimated_call_volume = 12_000_000
            estimated_put_volume = int(estimated_call_volume * ratio)

            return {
                "put_volume": estimated_put_volume,
                "call_volume": estimated_call_volume,
                "put_call_ratio": round(ratio, 4),
                "put_open_interest": estimated_put_volume * 10,
                "call_open_interest": estimated_call_volume * 10,
            }
        except Exception as exc:
            self._error_count += 1
            logger.warning("CBOEProvider.get_options_data failed: %s", exc)
            return None

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """CBOE does not provide credit spreads — return None."""
        return None

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """CBOE does not provide safe-haven prices — return None."""
        return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """CBOE does not provide news — return empty list."""
        return []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """CBOE does not provide social data — return empty list."""
        return []

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """CBOE does not provide fund-flow data — return None."""
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
