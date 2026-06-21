"""Component endpoints — current breakdown and historical component data."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/components", tags=["components"])

# Demo component data for when no store is available
DEMO_COMPONENTS = [
    {
        "name": "momentum",
        "raw_value": 2.35,
        "normalized_score": 72.5,
        "weight": 0.143,
        "direction": "bullish",
        "description": "Price vs 125-day moving average",
        "data_source": "yfinance",
    },
    {
        "name": "price_strength",
        "raw_value": 0.65,
        "normalized_score": 65.0,
        "weight": 0.143,
        "direction": "bullish",
        "description": "New highs vs new lows ratio",
        "data_source": "yfinance",
    },
    {
        "name": "breadth",
        "raw_value": 1.85,
        "normalized_score": 62.5,
        "weight": 0.143,
        "direction": "bullish",
        "description": "Advancing vs declining volume",
        "data_source": "yfinance",
    },
    {
        "name": "put_call",
        "raw_value": 0.85,
        "normalized_score": 55.0,
        "weight": 0.143,
        "direction": "neutral",
        "description": "CBOE put/call ratio",
        "data_source": "CBOE",
    },
    {
        "name": "credit_spreads",
        "raw_value": 3.45,
        "normalized_score": 45.0,
        "weight": 0.143,
        "direction": "bearish",
        "description": "High yield OAS spread",
        "data_source": "FRED",
    },
    {
        "name": "volatility",
        "raw_value": 18.5,
        "normalized_score": 48.0,
        "weight": 0.143,
        "direction": "neutral",
        "description": "VIX level",
        "data_source": "yfinance",
    },
    {
        "name": "safe_haven",
        "raw_value": -0.25,
        "normalized_score": 58.0,
        "weight": 0.143,
        "direction": "bullish",
        "description": "Equity vs safe haven relative returns",
        "data_source": "yfinance",
    },
]


@router.get("/current")
async def get_current_components(
    market: str = Query(default="sp500", description="Market ID"),
) -> Dict[str, Any]:
    """Get current component breakdown.

    Returns all component scores with their normalized values,
    weights, directions, and descriptions.
    """
    logger.info("GET /components/current?market=%s", market)

    try:
        from backend.main import cache, store

        cache_key = f"components:current:{market}"
        cached = cache.get(cache_key)
        if cached:
            return cached

        result = store.query(
            """
            SELECT *
            FROM component_scores
            WHERE market_id = ?
            AND timestamp = (
                SELECT MAX(timestamp) FROM component_scores WHERE market_id = ?
            )
            ORDER BY component_name
            """,
            params=[market, market],
        )

        if result and len(result) > 0:
            components = []
            for row in result:
                components.append(
                    {
                        "name": row.get("component_name", ""),
                        "raw_value": row.get("raw_value", 0.0),
                        "normalized_score": row.get("normalized_score", 50.0),
                        "weight": row.get("weight", 0.143),
                        "data_source": row.get("data_source", ""),
                    }
                )

            response = {
                "timestamp": result[0].get("timestamp", datetime.now(timezone.utc)),
                "market_id": market,
                "components": components,
                "component_count": len(components),
            }
            cache.set(cache_key, response, ttl=300)
            return response

    except ImportError:
        logger.debug("Store not available, returning demo components")
    except Exception as exc:
        logger.warning("Error reading components: %s", exc)

    # Return demo data
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "market_id": market,
        "components": DEMO_COMPONENTS,
        "component_count": len(DEMO_COMPONENTS),
        "note": "Demo data — no live store connected",
    }


@router.get("/history")
async def get_component_history(
    market: str = Query(default="sp500", description="Market ID"),
    component: Optional[str] = Query(default=None, description="Filter by component name"),
    days: int = Query(default=90, ge=1, le=365, description="Number of days of history"),
) -> Dict[str, Any]:
    """Get component time series history.

    Returns historical component scores over the specified period.
    Optionally filter to a single component.
    """
    logger.info("GET /components/history?market=%s&component=%s&days=%d", market, component, days)

    try:
        from backend.main import store

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        if component:
            result = store.query(
                """
                SELECT timestamp, component_name, raw_value, normalized_score, weight
                FROM component_scores
                WHERE market_id = ? AND component_name = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                """,
                params=[market, component, cutoff],
            )
        else:
            result = store.query(
                """
                SELECT timestamp, component_name, raw_value, normalized_score, weight
                FROM component_scores
                WHERE market_id = ? AND timestamp >= ?
                ORDER BY timestamp DESC
                """,
                params=[market, cutoff],
            )

        if result and len(result) > 0:
            # Group by component if no single component filter
            if component:
                series = [
                    {
                        "timestamp": row.get("timestamp"),
                        "normalized_score": row.get("normalized_score", 50.0),
                        "raw_value": row.get("raw_value", 0.0),
                    }
                    for row in result
                ]
                return {
                    "market_id": market,
                    "component": component,
                    "days": days,
                    "series": series,
                    "data_points": len(series),
                }
            else:
                # Group by component name
                from collections import defaultdict

                by_component: Dict[str, List[Dict]] = defaultdict(list)
                for row in result:
                    by_component[row.get("component_name", "")].append(
                        {
                            "timestamp": row.get("timestamp"),
                            "normalized_score": row.get("normalized_score", 50.0),
                            "raw_value": row.get("raw_value", 0.0),
                        }
                    )

                return {
                    "market_id": market,
                    "days": days,
                    "components": dict(by_component),
                    "data_points": len(result),
                }

    except ImportError:
        logger.debug("Store not available, returning demo history")
    except Exception as exc:
        logger.warning("Error reading component history: %s", exc)

    # Return demo time series
    return _demo_component_history(market, component, days)


def _demo_component_history(
    market: str, component: Optional[str], days: int
) -> Dict[str, Any]:
    """Generate demo component history."""
    import random

    random.seed(42)
    now = datetime.now(timezone.utc)
    dates = [(now - timedelta(days=i)).isoformat() for i in range(days)]

    if component:
        series = [
            {
                "timestamp": d,
                "normalized_score": 50.0 + random.gauss(0, 10),
                "raw_value": random.gauss(1.0, 0.3),
            }
            for d in dates
        ]
        return {
            "market_id": market,
            "component": component,
            "days": days,
            "series": series,
            "data_points": len(series),
            "note": "Demo data",
        }

    # All components
    from collections import defaultdict

    by_component: Dict[str, List[Dict]] = defaultdict(list)
    for comp in DEMO_COMPONENTS:
        name = comp["name"]
        by_component[name] = [
            {
                "timestamp": d,
                "normalized_score": min(100, max(0, comp["normalized_score"] + random.gauss(0, 5))),
                "raw_value": comp["raw_value"] + random.gauss(0, 0.2),
            }
            for d in dates
        ]

    return {
        "market_id": market,
        "days": days,
        "components": dict(by_component),
        "data_points": days * len(DEMO_COMPONENTS),
        "note": "Demo data",
    }
