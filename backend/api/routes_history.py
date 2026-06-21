"""History endpoints — score history and regime transitions."""

import logging
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/history", tags=["history"])


@router.get("/scores")
async def get_score_history(
    market: str = Query(default="sp500", description="Market ID"),
    days: int = Query(default=365, ge=1, le=730, description="Number of days of history"),
) -> Dict[str, Any]:
    """Get historical scores.

    Returns time series of all four scores (classic, narrative, positioning, composite)
    over the specified period.
    """
    logger.info("GET /history/scores?market=%s&days=%d", market, days)

    try:
        from backend.main import store

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)

        result = store.query(
            """
            SELECT timestamp, classic_score, narrative_score,
                   positioning_score, composite_score, regime, confidence
            FROM scores
            WHERE market_id = ? AND timestamp >= ?
            ORDER BY timestamp DESC
            """,
            params=[market, cutoff],
        )

        if result and len(result) > 0:
            series = [
                {
                    "timestamp": row.get("timestamp"),
                    "classic_score": row.get("classic_score", 50.0),
                    "narrative_score": row.get("narrative_score", 50.0),
                    "positioning_score": row.get("positioning_score", 50.0),
                    "composite_score": row.get("composite_score", 50.0),
                    "regime": row.get("regime", "mp3_neutral"),
                    "confidence": row.get("confidence", 50.0),
                }
                for row in result
            ]

            return {
                "market_id": market,
                "days": days,
                "series": series,
                "data_points": len(series),
            }

    except ImportError:
        logger.debug("Store not available, returning demo history")
    except Exception as exc:
        logger.warning("Error reading score history: %s", exc)

    # Return demo data
    return _demo_score_history(market, days)


@router.get("/regimes")
async def get_regime_history(
    market: str = Query(default="sp500", description="Market ID"),
) -> Dict[str, Any]:
    """Get regime history with transitions.

    Returns the history of regime changes including start/end dates
    and average forward returns for each regime period.
    """
    logger.info("GET /history/regimes?market=%s", market)

    try:
        from backend.main import store

        result = store.query(
            """
            SELECT regime, start_date, end_date,
                   avg_forward_1m, avg_forward_3m, avg_forward_6m, avg_forward_12m
            FROM regime_periods
            WHERE market_id = ?
            ORDER BY start_date DESC
            """,
            params=[market],
        )

        if result and len(result) > 0:
            regimes = [
                {
                    "regime": row.get("regime", ""),
                    "regime_label": _regime_to_label(row.get("regime", "")),
                    "start_date": row.get("start_date"),
                    "end_date": row.get("end_date"),
                    "forward_returns": {
                        "1m": row.get("avg_forward_1m"),
                        "3m": row.get("avg_forward_3m"),
                        "6m": row.get("avg_forward_6m"),
                        "12m": row.get("avg_forward_12m"),
                    },
                }
                for row in result
            ]

            return {
                "market_id": market,
                "regimes": regimes,
                "regime_count": len(regimes),
            }

    except ImportError:
        logger.debug("Store not available, returning demo regimes")
    except Exception as exc:
        logger.warning("Error reading regime history: %s", exc)

    # Return demo regime history
    return _demo_regime_history(market)


def _regime_to_label(regime: str) -> str:
    """Convert regime code to human-readable label."""
    labels = {
        "mp1_capitulation": "Capitulation",
        "mp2_defensive": "Defensive",
        "mp3_neutral": "Neutral",
        "mp4_risk_on": "Risk-On",
        "mp5_euphoria": "Euphoria",
    }
    return labels.get(regime, "Unknown")


def _demo_score_history(market: str, days: int) -> Dict[str, Any]:
    """Generate demo score history."""
    import random

    random.seed(42)
    now = datetime.now(timezone.utc)

    series = []
    base_classic = 55.0
    base_narrative = 52.0
    base_positioning = 58.0

    for i in range(days):
        date = now - timedelta(days=i)
        # Random walk with mean reversion
        base_classic = max(20, min(90, base_classic + random.gauss(0, 3)))
        base_narrative = max(20, min(90, base_narrative + random.gauss(0, 2.5)))
        base_positioning = max(20, min(90, base_positioning + random.gauss(0, 2)))

        composite = (base_classic * 0.4 + base_narrative * 0.3 + base_positioning * 0.3)

        # Determine regime
        if composite < 20:
            regime = "mp1_capitulation"
        elif composite < 40:
            regime = "mp2_defensive"
        elif composite < 60:
            regime = "mp3_neutral"
        elif composite < 80:
            regime = "mp4_risk_on"
        else:
            regime = "mp5_euphoria"

        series.append(
            {
                "timestamp": date.isoformat(),
                "classic_score": round(base_classic, 2),
                "narrative_score": round(base_narrative, 2),
                "positioning_score": round(base_positioning, 2),
                "composite_score": round(composite, 2),
                "regime": regime,
                "confidence": round(70 + random.gauss(0, 10), 2),
            }
        )

    return {
        "market_id": market,
        "days": days,
        "series": series,
        "data_points": len(series),
        "note": "Demo data",
    }


def _demo_regime_history(market: str) -> Dict[str, Any]:
    """Generate demo regime history."""
    now = datetime.now(timezone.utc)

    regimes = [
        {
            "regime": "mp4_risk_on",
            "regime_label": "Risk-On",
            "start_date": (now - timedelta(days=45)).strftime("%Y-%m-%d"),
            "end_date": None,  # Current regime
            "forward_returns": {
                "1m": 2.35,
                "3m": None,
                "6m": None,
                "12m": None,
            },
        },
        {
            "regime": "mp3_neutral",
            "regime_label": "Neutral",
            "start_date": (now - timedelta(days=120)).strftime("%Y-%m-%d"),
            "end_date": (now - timedelta(days=45)).strftime("%Y-%m-%d"),
            "forward_returns": {
                "1m": 0.85,
                "3m": 3.12,
                "6m": 5.67,
                "12m": 8.45,
            },
        },
        {
            "regime": "mp2_defensive",
            "regime_label": "Defensive",
            "start_date": (now - timedelta(days=200)).strftime("%Y-%m-%d"),
            "end_date": (now - timedelta(days=120)).strftime("%Y-%m-%d"),
            "forward_returns": {
                "1m": -1.25,
                "3m": -0.45,
                "6m": 2.30,
                "12m": 6.78,
            },
        },
        {
            "regime": "mp1_capitulation",
            "regime_label": "Capitulation",
            "start_date": (now - timedelta(days=250)).strftime("%Y-%m-%d"),
            "end_date": (now - timedelta(days=200)).strftime("%Y-%m-%d"),
            "forward_returns": {
                "1m": -3.50,
                "3m": 1.20,
                "6m": 4.80,
                "12m": 12.35,
            },
        },
    ]

    return {
        "market_id": market,
        "regimes": regimes,
        "regime_count": len(regimes),
        "note": "Demo data",
    }
