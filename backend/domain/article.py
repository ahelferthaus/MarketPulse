"""Article and social post domain models."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class Article(BaseModel):
    """A financial news article parsed from RSS or an API.

    Attributes:
        id: Unique identifier (hash or UUID).
        timestamp: Publication time in UTC.
        source: Publisher name (e.g. "Yahoo Finance", "Reuters").
        title: Article headline.
        url: Direct link to the article.
        description: Short summary or excerpt.
        sentiment_score: Normalized sentiment (-1 bearish to +1 bullish).
        topics: Classified topics (e.g. ["macro", "fed", "inflation"]).
        market_relevance: 0-1 score indicating relevance to market sentiment.
    """

    id: str
    timestamp: datetime
    source: str
    title: str
    url: str
    description: str = ""
    sentiment_score: Optional[float] = None
    topics: List[str] = Field(default_factory=list)
    market_relevance: float = 0.5

    # NLP sentiment dimension scores (0-100 each)
    panic_score: float = 0.0
    caution_score: float = 0.0
    uncertainty_score: float = 0.0
    optimism_score: float = 0.0
    complacency_score: float = 0.0
    euphoria_score: float = 0.0


class SocialPost(BaseModel):
    """A social media post relevant to market sentiment.

    Attributes:
        id: Unique identifier for the post.
        timestamp: Post creation time in UTC.
        platform: Source platform (e.g. "twitter", "reddit", "stocktwits").
        author: Username or display name.
        content: Raw post text.
        sentiment_score: Normalized sentiment (-1 to +1).
        engagement_score: Likes, retweets, comments aggregate.
        topics: Extracted topics.
        market_relevance: 0-1 relevance score.
    """

    id: str
    timestamp: datetime
    platform: str
    author: str
    content: str
    sentiment_score: Optional[float] = None
    engagement_score: float = 0.0
    topics: List[str] = Field(default_factory=list)
    market_relevance: float = 0.5

    # NLP sentiment dimension scores (0-100 each)
    panic_score: float = 0.0
    caution_score: float = 0.0
    uncertainty_score: float = 0.0
    optimism_score: float = 0.0
    complacency_score: float = 0.0
    euphoria_score: float = 0.0
