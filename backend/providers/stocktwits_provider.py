"""StockTwits provider — **stub**.

Full :class:`BaseProvider` interface implementation.  All methods
return ``None`` or empty collections so the :class:`ProviderChain`
seamlessly falls back to other providers.

Planned capabilities
--------------------
Once connected, this provider will:

* Fetch trending symbols and watchlist counts
* Stream public messages for tracked tickers
* Extract bullish/bearish sentiment from message tags
* Track message volume as a sentiment indicator

API requirements
----------------
* **StockTwits API v2** — requires developer registration.
* **Access token** — OAuth2 bearer token for API access.
* **Rate limits** — 200 requests/hour for standard developer tier.

Setup
-----
1. Register for a developer account at https://api.stocktwits.com/developers
2. Create an app and obtain an access token
3. Set environment variable::

       export STOCKTWITS_ACCESS_TOKEN=<your-token>

4. Install ``requests`` (already a project dependency).

5. Update this provider to call the StockTwits REST API.

API endpoints (planned)
-----------------------
* ``GET /api/2/trending/symbols.json`` — trending symbols
* ``GET /api/2/streams/symbol/{id}.json`` — messages for a symbol
* ``GET /api/2/symbols/{id}/sentiment.json`` — bullish/bearish breakdown

Sample API response format
--------------------------
Symbol stream (simplified)::

    {
      "response": {"status": 200},
      "symbol": {"symbol": "AAPL", "title": "Apple Inc."},
      "messages": [
        {
          "id": 123456789,
          "body": "$AAPL looking strong into earnings",
          "created_at": "2026-01-15T14:30:00Z",
          "user": {"username": "TechBull", "followers": 1523},
          "entities": {"sentiment": {"basic": "Bullish"}},
          "likes": {"total": 23}
        }
      ]
    }

Sentiment endpoint::

    {
      "response": {"status": 200},
      "symbol": {"symbol": "AAPL"},
      "bullish": 65,
      "bearish": 35
    }
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)

_STOCKTWITS_API_BASE = "https://api.stocktwits.com/api/2"


class StockTwitsProvider(BaseProvider):
    """StockTwits social sentiment provider — stub implementation.

    **Status:** Not connected.  All methods return empty results so the
    provider chain continues to the next candidate.

    To activate:

    1. Register for StockTwits developer account
    2. Obtain access token
    3. Override methods to call StockTwits REST API
    """

    name: str = "stocktwits"
    tier: str = "public"

    def __init__(self) -> None:
        logger.info(
            "StockTwitsProvider initialised — StockTwits API not connected (stub mode)"
        )

    def _log_stub(self, method: str) -> None:
        logger.debug("StockTwits API not connected — %s returning stub", method)

    # ── BaseProvider implementation (all stubs) ───────────────────────

    async def get_price_history(
        self, ticker: str, days: int = 252
    ) -> Optional[pd.DataFrame]:
        self._log_stub("get_price_history")
        return None

    async def get_current_quote(
        self, ticker: str
    ) -> Optional[Dict[str, Any]]:
        self._log_stub("get_current_quote")
        return None

    async def get_breadth_data(
        self, market_id: str
    ) -> Optional[Dict[str, Any]]:
        self._log_stub("get_breadth_data")
        return None

    async def get_options_data(
        self, ticker: str
    ) -> Optional[Dict[str, Any]]:
        self._log_stub("get_options_data")
        return None

    async def get_credit_spreads(
        self, series_id: str = "BAMLH0A0HYM2"
    ) -> Optional[Dict[str, Any]]:
        self._log_stub("get_credit_spreads")
        return None

    async def get_safe_haven_assets(self) -> Optional[Dict[str, Any]]:
        self._log_stub("get_safe_haven_assets")
        return None

    async def get_news_articles(
        self, query: str = "stock market", limit: int = 20
    ) -> List[Article]:
        self._log_stub("get_news_articles")
        return []

    async def get_social_posts(
        self, query: str = "stock market", limit: int = 50
    ) -> List[SocialPost]:
        """Would fetch StockTwits messages for a symbol.

        Stub: returns empty list.

        Sample live implementation::

            url = f"{_STOCKTWITS_API_BASE}/streams/symbol/{query}.json"
            headers = {"Authorization": f"Bearer {self.access_token}"}
            resp = requests.get(url, headers=headers, timeout=10)
            data = resp.json()
            messages = data.get("messages", [])
            return [
                SocialPost(
                    id=str(m["id"]),
                    timestamp=datetime.fromisoformat(m["created_at"].replace("Z", "+00:00")),
                    platform="stocktwits",
                    author=m["user"]["username"],
                    content=m["body"],
                    sentiment_score=1.0 if m.get("entities", {})
                        .get("sentiment", {}).get("basic") == "Bullish" else -1.0,
                    engagement_score=m.get("likes", {}).get("total", 0),
                )
                for m in messages
            ]
        """
        self._log_stub("get_social_posts")
        return []

    async def get_flows_data(
        self, ticker: str = "SPY"
    ) -> Optional[Dict[str, Any]]:
        self._log_stub("get_flows_data")
        return None

    async def get_source_status(self) -> SourceStatus:
        return SourceStatus(
            provider=self.name,
            available=False,
            last_successful_fetch=None,
            error_count_24h=0,
            data_freshness_minutes=None,
            tier=self.tier,
        )
