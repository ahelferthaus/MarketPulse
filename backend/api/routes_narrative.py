"""Narrative endpoints — sentiment breakdown, top phrases, and scored articles."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/narrative", tags=["narrative"])

# Demo narrative data
DEMO_SENTIMENT_DIMENSIONS = {
    "panic": 12.5,
    "caution": 28.0,
    "uncertainty": 35.5,
    "optimism": 62.0,
    "complacency": 18.0,
    "euphoria": 8.5,
}

DEMO_TOP_PHRASES = [
    {"phrase": "rate cuts", "count": 45, "sentiment": "positive", "topics": ["fed"]},
    {"phrase": "earnings beat", "count": 38, "sentiment": "positive", "topics": ["earnings"]},
    {"phrase": "AI growth", "count": 32, "sentiment": "positive", "topics": ["ai_tech"]},
    {"phrase": "credit spreads", "count": 28, "sentiment": "negative", "topics": ["credit"]},
    {"phrase": "geopolitical risk", "count": 25, "sentiment": "negative", "topics": ["geopolitics"]},
    {"phrase": "consumer spending", "count": 22, "sentiment": "positive", "topics": ["consumer"]},
    {"phrase": "inflation cooling", "count": 20, "sentiment": "positive", "topics": ["inflation"]},
    {"phrase": "banking stress", "count": 15, "sentiment": "negative", "topics": ["banking_stress"]},
    {"phrase": "market breadth", "count": 12, "sentiment": "neutral", "topics": ["macro"]},
    {"phrase": "liquidity concerns", "count": 10, "sentiment": "negative", "topics": ["liquidity"]},
]

DEMO_ARTICLES = [
    {
        "id": 1,
        "title": "Fed Signals Potential Rate Cuts as Inflation Cools",
        "source": "Reuters",
        "url": "https://reuters.com/article/1",
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
        "sentiment_score": 68.5,
        "topics": ["fed", "inflation"],
        "panic_score": 5.0,
        "caution_score": 15.0,
        "uncertainty_score": 20.0,
        "optimism_score": 72.0,
        "complacency_score": 10.0,
        "euphoria_score": 5.0,
    },
    {
        "id": 2,
        "title": "Tech Stocks Rally on Strong Earnings Reports",
        "source": "Bloomberg",
        "url": "https://bloomberg.com/article/2",
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=3)).isoformat(),
        "sentiment_score": 75.0,
        "topics": ["earnings", "ai_tech"],
        "panic_score": 0.0,
        "caution_score": 5.0,
        "uncertainty_score": 10.0,
        "optimism_score": 80.0,
        "complacency_score": 20.0,
        "euphoria_score": 15.0,
    },
    {
        "id": 3,
        "title": "Credit Spreads Widen Amid Banking Concerns",
        "source": "FT",
        "url": "https://ft.com/article/3",
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
        "sentiment_score": 35.0,
        "topics": ["credit", "banking_stress"],
        "panic_score": 25.0,
        "caution_score": 55.0,
        "uncertainty_score": 40.0,
        "optimism_score": 20.0,
        "complacency_score": 5.0,
        "euphoria_score": 0.0,
    },
    {
        "id": 4,
        "title": "Investors Hedge Positions as Volatility Rises",
        "source": "WSJ",
        "url": "https://wsj.com/article/4",
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat(),
        "sentiment_score": 42.0,
        "topics": ["macro", "volatility"],
        "panic_score": 10.0,
        "caution_score": 45.0,
        "uncertainty_score": 50.0,
        "optimism_score": 30.0,
        "complacency_score": 8.0,
        "euphoria_score": 2.0,
    },
    {
        "id": 5,
        "title": "AI Boom Drives Semiconductor Stocks to New Highs",
        "source": "CNBC",
        "url": "https://cnbc.com/article/5",
        "published_at": (datetime.now(timezone.utc) - timedelta(hours=6)).isoformat(),
        "sentiment_score": 78.0,
        "topics": ["ai_tech", "earnings"],
        "panic_score": 0.0,
        "caution_score": 5.0,
        "uncertainty_score": 8.0,
        "optimism_score": 75.0,
        "complacency_score": 25.0,
        "euphoria_score": 20.0,
    },
]


def _compute_narrative_score(dimensions: Dict[str, float]) -> float:
    """Compute overall narrative score from dimension scores.

    Panic/caution/uncertainty pull score down.
    Optimism pulls score up.
    Complacency/euphoria are cautionary but still push up.
    """
    return max(
        0.0,
        min(
            100.0,
            50.0
            + (dimensions["optimism"] + dimensions["euphoria"] * 0.5) * 0.4
            - (dimensions["panic"] + dimensions["caution"] * 0.5 + dimensions["uncertainty"] * 0.25)
            * 0.4,
        ),
    )


@router.get("/sentiment")
async def get_narrative_sentiment(
    market: str = Query(default="sp500", description="Market ID"),
) -> Dict[str, Any]:
    """Get current narrative sentiment breakdown.

    Returns the 6-dimension sentiment breakdown (panic, caution, uncertainty,
    optimism, complacency, euphoria) and the overall narrative score.
    """
    logger.info("GET /narrative/sentiment?market=%s", market)

    try:
        from backend.main import store

        result = store.query(
            """
            SELECT *
            FROM narrative_snapshots
            WHERE market_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            params=[market],
        )

        if result and len(result) > 0:
            row = result[0]
            dimensions = {
                "panic": row.get("panic_score", 0.0),
                "caution": row.get("caution_score", 0.0),
                "uncertainty": row.get("uncertainty_score", 0.0),
                "optimism": row.get("optimism_score", 0.0),
                "complacency": row.get("complacency_score", 0.0),
                "euphoria": row.get("euphoria_score", 0.0),
            }

            narrative_score = _compute_narrative_score(dimensions)

            return {
                "timestamp": row.get("timestamp", datetime.now(timezone.utc)),
                "market_id": market,
                "narrative_score": round(narrative_score, 1),
                "dimensions": {k: round(v, 1) for k, v in dimensions.items()},
                "article_count": row.get("article_count", 0),
                "dominant_sentiment": max(dimensions, key=dimensions.get),
            }

    except ImportError:
        logger.debug("Store not available, returning demo sentiment")
    except Exception as exc:
        logger.warning("Error reading narrative sentiment: %s", exc)

    # Return demo data
    narrative_score = _compute_narrative_score(DEMO_SENTIMENT_DIMENSIONS)
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market,
        "narrative_score": round(narrative_score, 1),
        "dimensions": {k: round(v, 1) for k, v in DEMO_SENTIMENT_DIMENSIONS.items()},
        "article_count": 145,
        "dominant_sentiment": max(DEMO_SENTIMENT_DIMENSIONS, key=DEMO_SENTIMENT_DIMENSIONS.get),
        "note": "Demo data",
    }


@router.get("/top-phrases")
async def get_top_phrases(
    market: str = Query(default="sp500", description="Market ID"),
    limit: int = Query(default=10, ge=1, le=50, description="Number of phrases to return"),
) -> Dict[str, Any]:
    """Get top phrases driving narrative score.

    Returns the most frequently mentioned phrases with their sentiment
    classification and associated topics.
    """
    logger.info("GET /narrative/top-phrases?market=%s&limit=%d", market, limit)

    # Top phrases are typically computed from article analysis
    # For now, return demo data
    phrases = DEMO_TOP_PHRASES[:limit]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market,
        "phrases": phrases,
        "total_phrases": len(phrases),
    }


@router.get("/articles")
async def get_recent_articles(
    market: str = Query(default="sp500", description="Market ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Number of articles to return"),
    topic: Optional[str] = Query(default=None, description="Filter by topic"),
) -> Dict[str, Any]:
    """Get recent scored articles.

    Returns the most recently ingested and scored articles with their
    sentiment scores and topic classifications.
    """
    logger.info(
        "GET /narrative/articles?market=%s&limit=%d&topic=%s", market, limit, topic
    )

    try:
        from backend.main import store

        if topic:
            result = store.query(
                """
                SELECT id, timestamp, source, title, url,
                       sentiment_score, topics, panic_score, caution_score,
                       uncertainty_score, optimism_score, complacency_score, euphoria_score
                FROM articles
                WHERE market_relevance > 0.5
                AND array_contains(topics, ?)
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params=[topic, limit],
            )
        else:
            result = store.query(
                """
                SELECT id, timestamp, source, title, url,
                       sentiment_score, topics, panic_score, caution_score,
                       uncertainty_score, optimism_score, complacency_score, euphoria_score
                FROM articles
                WHERE market_relevance > 0.5
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                params=[limit],
            )

        if result and len(result) > 0:
            articles = []
            for row in result:
                articles.append(
                    {
                        "id": row.get("id"),
                        "title": row.get("title", ""),
                        "source": row.get("source", ""),
                        "url": row.get("url", ""),
                        "published_at": row.get("timestamp"),
                        "sentiment_score": row.get("sentiment_score", 50.0),
                        "topics": row.get("topics", []),
                        "dimensions": {
                            "panic": row.get("panic_score", 0.0),
                            "caution": row.get("caution_score", 0.0),
                            "uncertainty": row.get("uncertainty_score", 0.0),
                            "optimism": row.get("optimism_score", 0.0),
                            "complacency": row.get("complacency_score", 0.0),
                            "euphoria": row.get("euphoria_score", 0.0),
                        },
                    }
                )

            return {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "market_id": market,
                "articles": articles,
                "total": len(articles),
                "topic_filter": topic,
            }

    except ImportError:
        logger.debug("Store not available, returning demo articles")
    except Exception as exc:
        logger.warning("Error reading articles: %s", exc)

    # Filter demo articles by topic if requested
    articles = DEMO_ARTICLES
    if topic:
        articles = [
            a for a in articles if topic in a.get("topics", [])
        ]

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market,
        "articles": articles[:limit],
        "total": len(articles[:limit]),
        "topic_filter": topic,
        "note": "Demo data",
    }
