"""
Text Ingestion Pipeline
Collects and preprocesses text from multiple sources:
- RSS news feeds
- Mock news dataset (for demo)
- Future: social media APIs
"""

import hashlib
import html
import logging
import re
from datetime import datetime, timezone
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Stub Article class for standalone usage
try:
    from backend.domain.article import Article
except ImportError:

    class Article:  # type: ignore[no-redef]
        """Minimal article stub."""

        def __init__(
            self,
            title: str = "",
            content: str = "",
            source: str = "",
            url: str = "",
            published_at: Optional[datetime] = None,
            **kwargs,
        ):
            self.id = kwargs.get("id", 0)
            self.title = title
            self.content = content
            self.source = source
            self.url = url
            self.published_at = published_at or datetime.now(timezone.utc)
            self.topics: List[str] = []
            self.sentiment_score: float = 50.0
            self.panic_score: float = 0.0
            self.caution_score: float = 0.0
            self.uncertainty_score: float = 0.0
            self.optimism_score: float = 0.0
            self.complacency_score: float = 0.0
            self.euphoria_score: float = 0.0
            self.market_relevance: float = 1.0


class TextIngestionPipeline:
    """Collects and preprocesses financial text."""

    # Mock headlines for demo mode
    MOCK_HEADLINES: List[Dict[str, str]] = [
        {"title": "Fed Signals Potential Rate Cuts as Inflation Cools", "source": "MockNews"},
        {"title": "Tech Stocks Rally on Strong Earnings Reports", "source": "MockNews"},
        {"title": "Credit Spreads Widen Amid Banking Concerns", "source": "MockNews"},
        {"title": "Investors Hedge Positions as Volatility Rises", "source": "MockNews"},
        {"title": "AI Boom Drives Semiconductor Stocks to New Highs", "source": "MockNews"},
        {"title": "Consumer Spending Remains Resilient Despite Headwinds", "source": "MockNews"},
        {"title": "Geopolitical Tensions Rise in Middle East", "source": "MockNews"},
        {"title": "Market Breadth Improves with Broad-Based Rally", "source": "MockNews"},
        {"title": "Treasury Yields Fall on Safe-Haven Demand", "source": "MockNews"},
        {"title": "Housing Market Shows Signs of Recovery", "source": "MockNews"},
        {"title": "Oil Prices Surge on Supply Concerns", "source": "MockNews"},
        {"title": "Dollar Strengthens Against Major Currencies", "source": "MockNews"},
        {"title": "Corporate Bond Issuance Hits Record Levels", "source": "MockNews"},
        {"title": "Retail Sales Beat Expectations in Holiday Season", "source": "MockNews"},
        {"title": "Analysts Warn of Potential Market Correction", "source": "MockNews"},
    ]

    def __init__(self, provider_chain=None):
        """Initialize the text ingestion pipeline.

        Args:
            provider_chain: Optional provider chain for fetching external data.
        """
        self.provider_chain = provider_chain
        logger.info("TextIngestionPipeline initialized")

    async def ingest(
        self,
        market_id: str = "sp500",
        limit: int = 50,
        use_mock: bool = True,
    ) -> List[Article]:
        """Ingest articles for a market.

        1. Fetch from RSS/news providers
        2. Clean and normalize text
        3. Deduplicate
        4. Filter by relevance
        5. Return list of Article objects

        Args:
            market_id: Market identifier (e.g., "sp500").
            limit: Maximum number of articles to return.
            use_mock: Whether to use mock data when no providers available.

        Returns:
            List of Article objects.
        """
        articles: List[Article] = []

        # Try to fetch from providers if available
        if self.provider_chain is not None:
            try:
                provider_articles = await self._fetch_from_providers(market_id, limit)
                articles.extend(provider_articles)
                logger.info("Fetched %d articles from providers", len(provider_articles))
            except Exception as exc:
                logger.warning("Provider fetch failed: %s", exc)

        # Fall back to mock data if no articles or explicitly requested
        if not articles and use_mock:
            mock_articles = self._generate_mock_articles(limit)
            articles.extend(mock_articles)
            logger.info("Generated %d mock articles", len(mock_articles))

        # Clean and normalize
        for article in articles:
            article.title = self._clean_text(article.title)
            if article.content:
                article.content = self._clean_text(article.content)

        # Deduplicate
        articles = self._deduplicate(articles)

        # Filter by relevance
        articles = self._filter_by_relevance(articles, market_id)

        return articles[:limit]

    async def _fetch_from_providers(self, market_id: str, limit: int) -> List[Article]:
        """Fetch articles from configured providers.

        Args:
            market_id: Market identifier.
            limit: Maximum articles to fetch.

        Returns:
            List of articles from providers.
        """
        articles: List[Article] = []

        # Attempt RSS feed fetching if feedparser is available
        try:
            rss_articles = await self._fetch_rss_feeds(market_id, limit)
            articles.extend(rss_articles)
        except Exception as exc:
            logger.debug("RSS fetch not available: %s", exc)

        return articles

    async def _fetch_rss_feeds(self, market_id: str, limit: int) -> List[Article]:
        """Fetch articles from RSS feeds.

        Args:
            market_id: Market identifier.
            limit: Maximum articles to fetch.

        Returns:
            List of articles from RSS feeds.
        """
        try:
            import feedparser  # type: ignore[import-untyped]
        except ImportError:
            logger.debug("feedparser not installed, skipping RSS feeds")
            return []

        # Default financial RSS feeds
        feeds = [
            "https://feeds.reuters.com/reuters/businessNews",
            "https://feeds.finance.yahoo.com/rss/2.0/headline?s=%5EGSPC",
        ]

        articles: List[Article] = []
        for feed_url in feeds:
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:limit]:
                    article = Article(
                        title=entry.get("title", ""),
                        content=entry.get("summary", ""),
                        source=feed.feed.get("title", "RSS"),
                        url=entry.get("link", ""),
                        published_at=datetime.now(timezone.utc),
                    )
                    articles.append(article)
            except Exception as exc:
                logger.warning("Failed to parse RSS feed %s: %s", feed_url, exc)

        return articles

    def _generate_mock_articles(self, limit: int) -> List[Article]:
        """Generate mock articles from headline templates.

        Args:
            limit: Number of articles to generate.

        Returns:
            List of mock Article objects.
        """
        articles: List[Article] = []
        now = datetime.now(timezone.utc)

        for i, headline in enumerate(self.MOCK_HEADLINES[:limit]):
            article = Article(
                id=i + 1,
                title=headline["title"],
                content=f"This is a mock article about {headline['title']}. "
                "It contains placeholder content for demonstration purposes "
                "when no live news sources are available.",
                source=headline["source"],
                url=f"https://example.com/article/{i + 1}",
                published_at=now,
            )
            articles.append(article)

        return articles

    def _clean_text(self, text: str) -> str:
        """Clean HTML, normalize whitespace, remove boilerplate.

        Args:
            text: Raw text to clean.

        Returns:
            Cleaned text string.
        """
        if not text:
            return ""

        # Unescape HTML entities
        text = html.unescape(text)

        # Remove HTML tags
        text = re.sub(r"<[^>]+>", " ", text)

        # Remove URLs
        text = re.sub(r"https?://\S+", "", text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text)

        # Remove common boilerplate phrases
        boilerplate = [
            r"Read more\s*\.\.\.?",
            r"Click here to\s*.+",
            r"Sign up for\s*.+",
            r"Follow us on\s*.+",
            r"Copyright\s*[©].*",
            r"All rights reserved\s*\.?",
        ]
        for pattern in boilerplate:
            text = re.sub(pattern, "", text, flags=re.IGNORECASE)

        return text.strip()

    def _deduplicate(self, articles: List[Article]) -> List[Article]:
        """Remove near-duplicate articles by title similarity.

        Args:
            articles: List of articles to deduplicate.

        Returns:
            Deduplicated list of articles.
        """
        if not articles:
            return []

        seen_hashes: set = set()
        unique: List[Article] = []

        for article in articles:
            # Use normalized title hash for deduplication
            normalized = re.sub(r"[^\w]", "", article.title.lower())
            title_hash = hashlib.md5(normalized.encode()).hexdigest()

            if title_hash not in seen_hashes:
                seen_hashes.add(title_hash)
                unique.append(article)

        if len(unique) < len(articles):
            logger.info(
                "Removed %d duplicate articles", len(articles) - len(unique)
            )

        return unique

    def _filter_by_relevance(
        self, articles: List[Article], market_id: str
    ) -> List[Article]:
        """Filter articles by market relevance.

        Args:
            articles: List of articles to filter.
            market_id: Target market identifier.

        Returns:
            Filtered list of articles.
        """
        if not articles or market_id == "all":
            return articles

        # Market-specific relevance keywords
        relevance_keywords: Dict[str, List[str]] = {
            "sp500": ["s&p", "sp500", "spy", "stock market", "equities", "wall street"],
            "nasdaq100": ["nasdaq", "qqq", "tech", "technology", "growth"],
            "russell2000": ["russell", "small cap", "smallcap", "iwi"],
            "dow": ["dow", "dji", "dia", "industrial"],
        }

        keywords = relevance_keywords.get(market_id, [])
        if not keywords:
            return articles

        filtered: List[Article] = []
        for article in articles:
            text = f"{article.title} {article.content or ''}".lower()
            # Article is relevant if it mentions market keywords or is general financial news
            is_relevant = any(kw in text for kw in keywords) or market_id == "sp500"
            if is_relevant:
                article.market_relevance = 1.0
                filtered.append(article)
            else:
                # Still keep but mark lower relevance
                article.market_relevance = 0.3
                filtered.append(article)

        return filtered
