"""Summarizer — on-demand only, not required for daily calculation."""

import logging
from typing import List

logger = logging.getLogger(__name__)

# Stub Article class for type hints
try:
    from backend.domain.article import Article
except ImportError:

    class Article:  # type: ignore[no-redef]
        def __init__(self, title: str = "", **kwargs):
            self.title = title


class Summarizer:
    """Stub for LLM-powered summarization.

    Provides basic concatenation-based summaries. A future implementation
    may use OpenAI, Anthropic, or local LLMs for richer summarization.
    """

    def __init__(self):
        """Initialize the summarizer."""
        logger.info("Summarizer initialized (stub mode)")

    async def summarize(self, articles: List[Article]) -> str:
        """Generate summary of articles.

        Args:
            articles: List of articles to summarize.

        Returns:
            A summary string. Stub implementation returns headline concatenation.
        """
        if not articles:
            return "No articles to summarize."

        titles = [a.title for a in articles[:10]]
        return "Recent headlines: " + "; ".join(titles)

    async def summarize_by_topic(self, articles: List[Article]) -> dict:
        """Group articles by topic and summarize each group.

        Args:
            articles: List of articles with topic annotations.

        Returns:
            Dict mapping topic names to summary strings.
        """
        from collections import defaultdict

        by_topic: dict = defaultdict(list)
        for article in articles:
            topics = getattr(article, "topics", [])
            if not topics:
                by_topic["general"].append(article)
            for topic in topics:
                by_topic[topic].append(article)

        summaries = {}
        for topic, topic_articles in by_topic.items():
            titles = [a.title for a in topic_articles[:5]]
            summaries[topic] = f"{topic}: " + "; ".join(titles)

        return summaries

    async def generate_market_narrative(
        self,
        articles: List[Article],
        sentiment_scores: dict,
    ) -> str:
        """Generate a narrative description of market sentiment.

        Args:
            articles: Recent scored articles.
            sentiment_scores: Current sentiment dimension scores.

        Returns:
            A plain-English narrative summary.
        """
        # Find dominant sentiment
        dominant = max(
            [
                ("panic", sentiment_scores.get("panic", 0)),
                ("caution", sentiment_scores.get("caution", 0)),
                ("uncertainty", sentiment_scores.get("uncertainty", 0)),
                ("optimism", sentiment_scores.get("optimism", 0)),
                ("complacency", sentiment_scores.get("complacency", 0)),
                ("euphoria", sentiment_scores.get("euphoria", 0)),
            ],
            key=lambda x: x[1],
        )

        narrative = f"Market narrative is dominated by {dominant[0]} sentiment."

        if articles:
            narrative += f" Based on {len(articles)} recent articles."

        return narrative
