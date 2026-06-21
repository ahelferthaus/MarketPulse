"""RSS news feed provider for financial headlines.

Reads syndicated RSS/Atom feeds from major financial publishers and
parses entries into :class:`Article` objects.

Default feeds
-------------
* Yahoo Finance News
* MarketWatch
* Seeking Alpha
* Reuters

Features
--------
* HTML cleaning from descriptions
* Deduplication by title similarity (Jaccard on word sets)
* Source attribution
* Graceful degradation when ``feedparser`` is unavailable
"""

from __future__ import annotations

import hashlib
import html
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

# ── feedparser is optional ──────────────────────────────────────────

try:
    import feedparser

    _HAS_FEEDPARSER = True
except ImportError:  # pragma: no cover
    feedparser = None  # type: ignore[assignment]
    _HAS_FEEDPARSER = False

# ── Default feed list ───────────────────────────────────────────────

_DEFAULT_FEEDS: List[Dict[str, str]] = [
    {
        "name": "Yahoo Finance",
        "url": "https://finance.yahoo.com/news/rssindex",
    },
    {
        "name": "MarketWatch",
        "url": "https://www.marketwatch.com/rss/topstories",
    },
    {
        "name": "Seeking Alpha",
        "url": "https://seekingalpha.com/feed.xml",
    },
    {
        "name": "Reuters",
        "url": "https://www.reutersagency.com/feed/?taxonomy=markets&post_type=reuters-best",
    },
]


class RSSNewsProvider(BaseProvider):
    """RSS-based financial news provider.

    Aggregates headlines from multiple RSS feeds, cleans HTML content,
    deduplicates by title similarity, and returns structured
    :class:`Article` objects.
    """

    name: str = "rss_news"
    tier: str = "public"

    def __init__(
        self,
        feeds: Optional[List[Dict[str, str]]] = None,
        dedup_threshold: float = 0.85,
    ) -> None:
        self.feeds = feeds or _DEFAULT_FEEDS
        self.dedup_threshold = dedup_threshold
        self._last_fetch: Optional[datetime] = None
        self._error_count: int = 0
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": "Westwood-MarketPulse/1.0 (research@westwood.com)",
        })

    # ── internal helpers ──────────────────────────────────────────────

    @staticmethod
    def _clean_html(text: str) -> str:
        """Remove HTML tags and unescape entities."""
        if not text:
            return ""
        text = re.sub(r"<[^>]+>", " ", text)
        text = html.unescape(text)
        text = re.sub(r"\s+", " ", text).strip()
        return text

    @staticmethod
    def _parse_published(entry: Any) -> Optional[datetime]:
        """Extract datetime from feed entry."""
        # feedparser provides published_parsed or updated_parsed as time tuples
        tt = getattr(entry, "published_parsed", None) or getattr(entry, "updated_parsed", None)
        if tt:
            try:
                return datetime(*tt[:6], tzinfo=timezone.utc)
            except (ValueError, TypeError):
                pass

        # Fallback: parse string
        pub_str = getattr(entry, "published", "") or getattr(entry, "updated", "")
        if pub_str:
            for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
                try:
                    return datetime.strptime(pub_str, fmt)
                except ValueError:
                    continue
        return None

    @staticmethod
    def _title_similarity(a: str, b: str) -> float:
        """Jaccard similarity on word sets."""
        words_a = set(RSSNewsProvider._tokenize(a))
        words_b = set(RSSNewsProvider._tokenize(b))
        if not words_a or not words_b:
            return 0.0
        intersection = words_a & words_b
        union = words_a | words_b
        return len(intersection) / len(union)

    @staticmethod
    def _tokenize(title: str) -> List[str]:
        """Lowercase alphanumeric tokens."""
        return re.findall(r"[a-z0-9]+", title.lower())

    @retry(
        retry=retry_if_exception_type((requests.RequestException,)),
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=1, min=1, max=5),
        reraise=False,
    )
    def _fetch_feed(self, url: str) -> Optional[Any]:
        """Download and parse a single RSS feed."""
        if feedparser is None:
            return None
        try:
            resp = self._session.get(url, timeout=15)
            resp.raise_for_status()
            parsed = feedparser.parse(resp.content)
            if parsed.bozo and hasattr(parsed, "bozo_exception"):
                logger.debug("Feed %s parse warning: %s", url, parsed.bozo_exception)
            return parsed
        except Exception as exc:
            logger.debug("Feed fetch failed for %s: %s", url, exc)
            raise

    def _entries_to_articles(
        self,
        parsed: Any,
        source_name: str,
        query_lower: str,
    ) -> List[Article]:
        """Convert parsed feed entries to Article objects."""
        articles: List[Article] = []
        entries = getattr(parsed, "entries", [])
        for entry in entries:
            title = self._clean_html(getattr(entry, "title", ""))
            if not title:
                continue

            # Query filter
            if query_lower and query_lower not in title.lower():
                continue

            link = getattr(entry, "link", "")
            description = self._clean_html(getattr(entry, "summary", ""))
            pub_time = self._parse_published(entry) or datetime.now(timezone.utc)

            # Stable ID from content hash
            article_id = hashlib.sha256(f"{title}{link}".encode()).hexdigest()[:16]

            articles.append(Article(
                id=article_id,
                timestamp=pub_time,
                source=source_name,
                title=title,
                url=link,
                description=description,
                sentiment_score=None,
                topics=[],
                market_relevance=0.5,
            ))
        return articles

    def _deduplicate(self, articles: List[Article]) -> List[Article]:
        """Remove near-duplicate articles by title similarity."""
        unique: List[Article] = []
        for art in articles:
            is_dup = False
            for existing in unique:
                sim = self._title_similarity(art.title, existing.title)
                if sim >= self.dedup_threshold:
                    is_dup = True
                    break
            if not is_dup:
                unique.append(art)
        return unique

    # ── BaseProvider implementation ───────────────────────────────────

    async def get_price_history(
        self, ticker: str, days: int = 252
    ) -> Optional[Any]:
        return None

    async def get_current_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        return None

    async def get_breadth_data(self, market_id: str) -> Optional[Dict[str, Any]]:
        return None

    async def get_options_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        return None

    async def get_credit_spreads(
        self, series_id: str = "BAMLH0A0HYM2"
    ) -> Optional[Dict[str, Any]]:
        return None

    async def get_safe_haven_assets(self) -> Optional[Dict[str, Any]]:
        return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """Fetch, parse, and deduplicate RSS headlines.

        Args:
            query: Case-insensitive substring filter on article titles.
            limit: Maximum articles to return across all feeds.

        Returns:
            Deduplicated list of :class:`Article` objects (may be empty).
        """
        if not _HAS_FEEDPARSER:
            logger.debug("feedparser not installed — RSSNewsProvider returning empty")
            return []

        all_articles: List[Article] = []
        query_lower = query.lower()

        for feed_cfg in self.feeds:
            try:
                parsed = self._fetch_feed(feed_cfg["url"])
                if parsed is None:
                    continue
                articles = self._entries_to_articles(
                    parsed, feed_cfg["name"], query_lower
                )
                all_articles.extend(articles)
                self._last_fetch = datetime.now(timezone.utc)
            except Exception as exc:
                self._error_count += 1
                logger.warning(
                    "RSSNewsProvider failed for %s: %s", feed_cfg["name"], exc
                )

        # Sort by recency
        all_articles.sort(key=lambda a: a.timestamp, reverse=True)
        # Deduplicate
        deduped = self._deduplicate(all_articles)
        return deduped[:limit]

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """RSS feeds do not provide social posts — return empty list."""
        return []

    async def get_flows_data(self, ticker: str = "SPY") -> Optional[Dict[str, Any]]:
        return None

    async def get_source_status(self) -> SourceStatus:
        age_minutes = None
        if self._last_fetch:
            age = datetime.now(timezone.utc) - self._last_fetch
            age_minutes = int(age.total_seconds() / 60)
        return SourceStatus(
            provider=self.name,
            available=_HAS_FEEDPARSER,
            last_successful_fetch=self._last_fetch,
            error_count_24h=self._error_count,
            data_freshness_minutes=age_minutes,
            tier=self.tier,
        )
