"""Score endpoints — current and composite scores."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/scores", tags=["scores"])


def _get_store():
    """Dependency to get the DuckDB store from app state."""
    from fastapi import Request

    def _dependency(request: Request):
        store = getattr(request.app.state, "store", None)
        if store is None:
            raise HTTPException(status_code=503, detail="Storage not initialized")
        return store

    return _dependency


def _get_cache():
    """Dependency to get the cache from app state."""
    from fastapi import Request

    def _dependency(request: Request):
        cache = getattr(request.app.state, "cache", None)
        if cache is None:
            raise HTTPException(status_code=503, detail="Cache not initialized")
        return cache

    return _dependency


@router.get("/current")
async def get_current_score(
    market: str = Query(default="sp500", description="Market ID (e.g., sp500, nasdaq100)"),
) -> Dict[str, Any]:
    """Get current MarketPulse scores for a market.

    Returns the full score object including classic, narrative, positioning,
    composite scores, regime, direction, confidence, and explanation.
    """
    logger.info("GET /scores/current?market=%s", market)

    # Attempt to read from DuckDB cache
    try:
        from backend.main import cache, store

        # Check cache first
        cache_key = f"scores:current:{market}"
        cached = cache.get(cache_key)
        if cached:
            logger.debug("Cache hit for %s", cache_key)
            return cached

        # Query DuckDB for latest score
        result = store.query(
            """
            SELECT * FROM scores
            WHERE market_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            params=[market],
        )

        if result and len(result) > 0:
            row = result[0]
            response = {
                "timestamp": row.get("timestamp", datetime.now(timezone.utc)),
                "market_id": market,
                "classic_score": row.get("classic_score", 50.0),
                "narrative_score": row.get("narrative_score", 50.0),
                "positioning_score": row.get("positioning_score", 50.0),
                "composite_score": row.get("composite_score", 50.0),
                "regime": row.get("regime", "mp3_neutral"),
                "regime_label": _regime_to_label(row.get("regime", "mp3_neutral")),
                "direction": row.get("direction", "stable"),
                "confidence": row.get("confidence", 50.0),
                "explanation": row.get(
                    "explanation", f"MarketPulse score for {market}."
                ),
            }
            cache.set(cache_key, response, ttl=300)
            return response

    except ImportError:
        logger.debug("Store/cache not available, returning demo response")
    except Exception as exc:
        logger.warning("Error reading from store: %s", exc)

    # Return a demo response when no data exists
    return _demo_score_response(market)


@router.get("/composite")
async def get_composite_score(
    market: str = Query(default="sp500", description="Market ID"),
) -> Dict[str, Any]:
    """Get lightweight composite score only.

    Returns just the composite score, regime, and label — optimized
    for widgets and embeds that don't need full component breakdown.
    """
    logger.info("GET /scores/composite?market=%s", market)

    try:
        from backend.main import cache, store

        cache_key = f"scores:composite:{market}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        result = store.query(
            """
            SELECT timestamp, composite_score, regime, confidence
            FROM scores
            WHERE market_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            params=[market],
        )

        if result and len(result) > 0:
            row = result[0]
            regime = row.get("regime", "mp3_neutral")
            response = {
                "timestamp": row.get("timestamp", datetime.now(timezone.utc)),
                "market_id": market,
                "composite_score": row.get("composite_score", 50.0),
                "regime": regime,
                "regime_label": _regime_to_label(regime),
                "confidence": row.get("confidence", 50.0),
            }
            cache.set(cache_key, response, ttl=300)
            return response

    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error reading composite score: %s", exc)

    # Demo response
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market,
        "composite_score": 58.5,
        "regime": "mp4_risk_on",
        "regime_label": "Risk-On",
        "confidence": 82.0,
    }


def _regime_to_label(regime: Optional[str]) -> str:
    """Convert regime code to human-readable label."""
    labels = {
        "mp1_capitulation": "Capitulation",
        "mp2_defensive": "Defensive",
        "mp3_neutral": "Neutral",
        "mp4_risk_on": "Risk-On",
        "mp5_euphoria": "Euphoria",
    }
    return labels.get(regime or "", "Unknown")


def _demo_score_response(market: str) -> Dict[str, Any]:
    """Generate a demo score response when no data exists."""
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market,
        "classic_score": 62.0,
        "narrative_score": 55.0,
        "positioning_score": 58.0,
        "composite_score": 58.5,
        "regime": "mp4_risk_on",
        "regime_label": "Risk-On",
        "direction": "stable",
        "confidence": 82.0,
        "explanation": (
            f"Markets are in a risk-on posture with composite score of 58.5. "
            f"Classic indicators show moderate bullishness while narrative "
            f"sentiment remains balanced. Overall confidence is good at 82%."
        ),
        "what_changed": None,
        "drivers": [
            {
                "component": "momentum",
                "contribution": 8.5,
                "direction": "bullish",
                "description": "Strong momentum above 125-day moving average",
            },
            {
                "component": "credit_spreads",
                "contribution": -3.2,
                "direction": "bearish",
                "description": "Credit spreads slightly wider than average",
            },
        ],
        "data_quality": {
            "overall_confidence": 82.0,
            "sources_used": 5,
            "sources_available": 7,
            "missing_components": ["etf_flows", "futures_positioning"],
            "substituted_components": [],
            "stale_data_warnings": [],
            "data_freshness_minutes": 12,
        },
    }
