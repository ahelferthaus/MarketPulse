"""Backtest endpoints — historical regime analysis and forward returns."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Query

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/backtest", tags=["backtest"])

# Demo backtest data — forward returns by regime
REGIME_BACKTEST_DATA = {
    "mp1_capitulation": {
        "regime_label": "Capitulation",
        "score_range": "0-20",
        "periods_analyzed": 12,
        "avg_days_in_regime": 45,
        "forward_returns": {
            "1m": {"mean": -2.35, "median": -1.80, "win_rate": 0.25, "samples": 12},
            "3m": {"mean": 1.20, "median": 0.85, "win_rate": 0.50, "samples": 12},
            "6m": {"mean": 4.80, "median": 3.50, "win_rate": 0.67, "samples": 11},
            "12m": {"mean": 12.35, "median": 10.20, "win_rate": 0.75, "samples": 10},
        },
        "notes": "Contrarian entry point. Best 12-month forward returns of any regime.",
    },
    "mp2_defensive": {
        "regime_label": "Defensive",
        "score_range": "20-40",
        "periods_analyzed": 28,
        "avg_days_in_regime": 62,
        "forward_returns": {
            "1m": {"mean": -1.25, "median": -0.80, "win_rate": 0.36, "samples": 28},
            "3m": {"mean": -0.45, "median": -0.20, "win_rate": 0.43, "samples": 28},
            "6m": {"mean": 2.30, "median": 1.50, "win_rate": 0.57, "samples": 26},
            "12m": {"mean": 6.78, "median": 5.40, "win_rate": 0.65, "samples": 24},
        },
        "notes": "Risk-off positioning. Mixed short-term, positive medium-term.",
    },
    "mp3_neutral": {
        "regime_label": "Neutral",
        "score_range": "40-60",
        "periods_analyzed": 45,
        "avg_days_in_regime": 38,
        "forward_returns": {
            "1m": {"mean": 0.85, "median": 0.60, "win_rate": 0.58, "samples": 45},
            "3m": {"mean": 3.12, "median": 2.80, "win_rate": 0.64, "samples": 44},
            "6m": {"mean": 5.67, "median": 4.90, "win_rate": 0.68, "samples": 42},
            "12m": {"mean": 8.45, "median": 7.30, "win_rate": 0.71, "samples": 38},
        },
        "notes": "Balanced conditions. Positive expected returns across all horizons.",
    },
    "mp4_risk_on": {
        "regime_label": "Risk-On",
        "score_range": "60-80",
        "periods_analyzed": 38,
        "avg_days_in_regime": 52,
        "forward_returns": {
            "1m": {"mean": 1.45, "median": 1.20, "win_rate": 0.63, "samples": 38},
            "3m": {"mean": 3.85, "median": 3.40, "win_rate": 0.68, "samples": 36},
            "6m": {"mean": 5.20, "median": 4.60, "win_rate": 0.66, "samples": 34},
            "12m": {"mean": 6.30, "median": 5.80, "win_rate": 0.62, "samples": 30},
        },
        "notes": "Momentum regime. Good short-term, diminishing at 12 months.",
    },
    "mp5_euphoria": {
        "regime_label": "Euphoria",
        "score_range": "80-100",
        "periods_analyzed": 8,
        "avg_days_in_regime": 35,
        "forward_returns": {
            "1m": {"mean": 0.95, "median": 0.70, "win_rate": 0.50, "samples": 8},
            "3m": {"mean": -0.80, "median": -1.20, "win_rate": 0.38, "samples": 8},
            "6m": {"mean": -3.50, "median": -4.10, "win_rate": 0.25, "samples": 7},
            "12m": {"mean": -2.10, "median": -3.40, "win_rate": 0.33, "samples": 6},
        },
        "notes": "Danger zone. Negative expected returns beyond 1 month. Consider hedging.",
    },
}


@router.get("/regimes")
async def get_regime_backtest(
    market: str = Query(default="sp500", description="Market ID"),
) -> Dict[str, Any]:
    """Get forward returns by regime.

    Returns historical forward returns for each MarketPulse regime.
    This is the key backtest endpoint that shows how markets typically
    perform after each regime classification.
    """
    logger.info("GET /backtest/regimes?market=%s", market)

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
            # Aggregate by regime
            from collections import defaultdict

            regime_stats: Dict[str, Dict] = defaultdict(
                lambda: {
                    "periods": 0,
                    "returns_1m": [],
                    "returns_3m": [],
                    "returns_6m": [],
                    "returns_12m": [],
                }
            )

            for row in result:
                regime = row.get("regime", "")
                if not regime:
                    continue
                regime_stats[regime]["periods"] += 1
                if row.get("avg_forward_1m") is not None:
                    regime_stats[regime]["returns_1m"].append(row["avg_forward_1m"])
                if row.get("avg_forward_3m") is not None:
                    regime_stats[regime]["returns_3m"].append(row["avg_forward_3m"])
                if row.get("avg_forward_6m") is not None:
                    regime_stats[regime]["returns_6m"].append(row["avg_forward_6m"])
                if row.get("avg_forward_12m") is not None:
                    regime_stats[regime]["returns_12m"].append(row["avg_forward_12m"])

            # Compute averages
            import statistics

            regimes = []
            for regime_key, stats in sorted(regime_stats.items()):
                def _avg(vals):
                    return statistics.mean(vals) if vals else None

                regimes.append(
                    {
                        "regime": regime_key,
                        "regime_label": _regime_to_label(regime_key),
                        "periods_analyzed": stats["periods"],
                        "forward_returns": {
                            "1m": {"mean": _avg(stats["returns_1m"]), "samples": len(stats["returns_1m"])},
                            "3m": {"mean": _avg(stats["returns_3m"]), "samples": len(stats["returns_3m"])},
                            "6m": {"mean": _avg(stats["returns_6m"]), "samples": len(stats["returns_6m"])},
                            "12m": {"mean": _avg(stats["returns_12m"]), "samples": len(stats["returns_12m"])},
                        },
                    }
                )

            return {
                "market_id": market,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "regimes": regimes,
                "total_periods": len(result),
            }

    except ImportError:
        logger.debug("Store not available, returning demo backtest data")
    except Exception as exc:
        logger.warning("Error reading backtest data: %s", exc)

    # Return demo backtest data
    return {
        "market_id": market,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "regimes": list(REGIME_BACKTEST_DATA.values()),
        "total_periods": sum(r["periods_analyzed"] for r in REGIME_BACKTEST_DATA.values()),
        "methodology": (
            "Forward returns computed from first day of regime classification. "
            "Returns are price-only, not total return. Past performance does not "
            "guarantee future results."
        ),
        "disclaimer": (
            "This backtest is for research purposes only. It does not constitute "
            "investment advice. MarketPulse scores are classifications, not predictions."
        ),
        "note": "Demo data",
    }


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
