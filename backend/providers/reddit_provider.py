"""Reddit provider — **stub**.

Full :class:`BaseProvider` interface implementation.  All methods
return ``None`` or empty collections so the :class:`ProviderChain`
seamlessly falls back to other providers.

Planned capabilities
--------------------
Once connected, this provider will:

* Monitor subreddits: r/wallstreetbets, r/stocks, r/investing,
  r/StockMarket, r/options
* Fetch hot and new posts with engagement metrics
* Extract sentiment from post titles and comments
* Track ticker mention frequency

API requirements
----------------
* **PRAW** (Python Reddit API Wrapper) — the standard library for
  Reddit API access.
* **Reddit app credentials** — client_id, client_secret, user_agent.
* **Rate limits** — 60 requests/minute for OAuth-authenticated apps.

Setup
-----
1. Create a Reddit app at https://www.reddit.com/prefs/apps/
2. Note the client_id and client_secret
3. Set environment variables::

       export REDDIT_CLIENT_ID=<your-id>
       export REDDIT_CLIENT_SECRET=<your-secret>
       export REDDIT_USER_AGENT="Westwood-MarketPulse/1.0"

4. Install ``praw``::

       pip install praw>=7.7

5. Update this provider to use the live API.

Sample API response format
--------------------------
Subreddit hot posts (via PRAW, simplified)::

    [
      {
        "id": "abc123",
        "title": "Why I think SPY is going to 500",
        "selftext": "I've been analyzing the charts...",
        "subreddit": "wallstreetbets",
        "author": "BullTrader99",
        "created_utc": 1705328400.0,
        "score": 1250,
        "num_comments": 342,
        "upvote_ratio": 0.85,
        "url": "https://reddit.com/r/wallstreetbets/comments/abc123/..."
      }
    ]
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

# Default subreddits to monitor
_DEFAULT_SUBREDDITS = [
    "wallstreetbets",
    "stocks",
    "investing",
    "StockMarket",
    "options",
    "securityanalysis",
]


class RedditProvider(BaseProvider):
    """Reddit social media data provider — stub implementation.

    **Status:** Not connected.  All methods return empty results so the
    provider chain continues to the next candidate.

    To activate:

    1. Create Reddit app and obtain credentials
    2. ``pip install praw>=7.7``
    3. Override methods to use ``praw.Reddit``
    """

    name: str = "reddit"
    tier: str = "public"

    def __init__(self) -> None:
        logger.info(
            "RedditProvider initialised — Reddit API not connected (stub mode)"
        )

    def _log_stub(self, method: str) -> None:
        logger.debug("Reddit API not connected — %s returning stub", method)

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
        """Would fetch Reddit posts from monitored subreddits.

        Stub: returns empty list.

        Sample live implementation::

            reddit = praw.Reddit(
                client_id=self.client_id,
                client_secret=self.client_secret,
                user_agent=self.user_agent,
            )
            posts = []
            for sub_name in self.subreddits:
                subreddit = reddit.subreddit(sub_name)
                for post in subreddit.hot(limit=limit // len(self.subreddits)):
                    posts.append(SocialPost(
                        id=post.id,
                        timestamp=datetime.utcfromtimestamp(post.created_utc),
                        platform="reddit",
                        author=str(post.author),
                        content=f"{post.title}\n{post.selftext}",
                        engagement_score=post.score + post.num_comments,
                    ))
            return posts[:limit]
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
