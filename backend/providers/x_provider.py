"""X (formerly Twitter) provider — **stub**.

Full :class:`BaseProvider` interface implementation.  All methods
return ``None`` or empty collections so the :class:`ProviderChain`
seamlessly falls back to other providers.

Planned capabilities
--------------------
Once the X API v2 integration is implemented, this provider will:

* Search recent tweets by keyword/hashtag (e.g. ``$SPY``, ``#stockmarket``)
* Fetch tweet engagement metrics (likes, retweets, replies)
* Extract sentiment via the NLP pipeline
* Track trending financial hashtags

API requirements
----------------
* **X API v2 Basic or Pro plan** — the free tier is too limited for
  reliable market sentiment tracking.
* **Bearer token** — required for all API v2 endpoints.
* **Rate limits** (Basic plan):

  * Search recent: 450 requests / 15 min
  * Tweet lookup: 300 requests / 15 min
  * User timeline: 1500 requests / 15 min

Setup
-----
1. Create an X developer account at https://developer.twitter.com/
2. Create a project and app, generate a Bearer Token
3. Set environment variable::

       export X_BEARER_TOKEN=<your-token>

4. Install ``tweepy``::

       pip install tweepy>=4.14

5. Update this provider to use the live API.

Sample API response format
--------------------------
Search recent tweets (simplified)::

    {
      "data": [
        {
          "id": "1234567890",
          "text": "Bulls are in control today $SPY 🚀",
          "created_at": "2026-01-15T14:30:00Z",
          "public_metrics": {
            "retweet_count": 12,
            "reply_count": 5,
            "like_count": 45,
            "quote_count": 2
          },
          "author_id": "987654321"
        }
      ],
      "meta": {
        "result_count": 1,
        "next_token": "b26v89c19zqg8o3"
      }
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


class XProvider(BaseProvider):
    """X (Twitter) social media data provider — stub implementation.

    **Status:** Not connected.  All methods return empty results so the
    provider chain continues to the next candidate.

    To activate:

    1. Obtain X API v2 Bearer Token
    2. ``pip install tweepy>=4.14``
    3. Override methods to call ``tweepy.Client``
    """

    name: str = "x_twitter"
    tier: str = "premium"

    def __init__(self) -> None:
        logger.info(
            "XProvider initialised — X API not connected (stub mode)"
        )

    def _log_stub(self, method: str) -> None:
        logger.debug("X API not connected — %s returning stub", method)

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
        """Would search X for financial tweets and map to Article objects.

        Stub: returns empty list.
        """
        self._log_stub("get_news_articles")
        return []

    async def get_social_posts(
        self, query: str = "stock market", limit: int = 50
    ) -> List[SocialPost]:
        """Would fetch tweets matching *query* and return as SocialPost objects.

        Stub: returns empty list.

        Sample live implementation::

            client = tweepy.Client(bearer_token=self.bearer_token)
            tweets = client.search_recent_tweets(
                query=query, max_results=min(limit, 100),
                tweet_fields=["created_at", "public_metrics", "author_id"]
            )
            return [
                SocialPost(
                    id=t.id,
                    timestamp=t.created_at,
                    platform="twitter",
                    author=t.author_id,
                    content=t.text,
                    engagement_score=sum(t.public_metrics.values()),
                )
                for t in (tweets.data or [])
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
