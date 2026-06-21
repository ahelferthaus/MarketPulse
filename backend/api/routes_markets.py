"""Market endpoints — list markets and get market configuration."""

import logging
from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException, Path

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/markets", tags=["markets"])

# Default market configurations (embedded for standalone operation)
DEFAULT_MARKETS: Dict[str, Dict[str, Any]] = {
    "sp500": {
        "market_id": "sp500",
        "name": "S&P 500",
        "benchmark_ticker": "^GSPC",
        "etf_proxy": "SPY",
        "volatility_proxy": "^VIX",
        "options_proxy": "SPY",
        "credit_spread_proxy": "BAMLH0A0HYM2",
        "normalization_window_days": 252,
        "component_availability": {
            "momentum": True,
            "price_strength": True,
            "breadth": True,
            "put_call": True,
            "credit_spreads": True,
            "volatility": True,
            "safe_haven": True,
            "etf_flows": False,
            "fund_flows": False,
            "futures_positioning": False,
            "prediction_markets": False,
            "options_skew": False,
            "margin_debt": False,
        },
    },
    "nasdaq100": {
        "market_id": "nasdaq100",
        "name": "Nasdaq 100",
        "benchmark_ticker": "^NDX",
        "etf_proxy": "QQQ",
        "volatility_proxy": "^VXN",
        "options_proxy": "QQQ",
        "credit_spread_proxy": "BAMLH0A0HYM2",
        "normalization_window_days": 252,
        "component_availability": {
            "momentum": True,
            "price_strength": True,
            "breadth": True,
            "put_call": True,
            "credit_spreads": True,
            "volatility": True,
            "safe_haven": True,
            "etf_flows": False,
            "fund_flows": False,
            "futures_positioning": False,
            "prediction_markets": False,
            "options_skew": False,
            "margin_debt": False,
        },
    },
    "russell2000": {
        "market_id": "russell2000",
        "name": "Russell 2000",
        "benchmark_ticker": "^RUT",
        "etf_proxy": "IWM",
        "volatility_proxy": "^RVX",
        "options_proxy": "IWM",
        "credit_spread_proxy": "BAMLH0A0HYM2",
        "normalization_window_days": 252,
        "component_availability": {
            "momentum": True,
            "price_strength": True,
            "breadth": True,
            "put_call": True,
            "credit_spreads": True,
            "volatility": True,
            "safe_haven": True,
            "etf_flows": False,
            "fund_flows": False,
            "futures_positioning": False,
            "prediction_markets": False,
            "options_skew": False,
            "margin_debt": False,
        },
    },
    "dow": {
        "market_id": "dow",
        "name": "Dow Jones Industrial Average",
        "benchmark_ticker": "^DJI",
        "etf_proxy": "DIA",
        "volatility_proxy": "^VIX",
        "options_proxy": "DIA",
        "credit_spread_proxy": "BAMLH0A0HYM2",
        "normalization_window_days": 252,
        "component_availability": {
            "momentum": True,
            "price_strength": True,
            "breadth": False,
            "put_call": True,
            "credit_spreads": True,
            "volatility": True,
            "safe_haven": True,
            "etf_flows": False,
            "fund_flows": False,
            "futures_positioning": False,
            "prediction_markets": False,
            "options_skew": False,
            "margin_debt": False,
        },
    },
}


@router.get("/")
async def list_markets() -> Dict[str, Any]:
    """List all available markets.

    Returns a list of all markets with their basic configuration.
    """
    logger.info("GET /markets/")

    markets = []
    for market_data in DEFAULT_MARKETS.values():
        # Return summary info only
        markets.append(
            {
                "market_id": market_data["market_id"],
                "name": market_data["name"],
                "benchmark_ticker": market_data["benchmark_ticker"],
                "etf_proxy": market_data["etf_proxy"],
                "normalization_window_days": market_data["normalization_window_days"],
            }
        )

    return {"markets": markets, "count": len(markets)}


@router.get("/{market_id}/config")
async def get_market_config(
    market_id: str = Path(..., description="Market ID (e.g., sp500, nasdaq100)"),
) -> Dict[str, Any]:
    """Get configuration for a specific market.

    Returns the full market configuration including component availability,
    ticker mappings, and normalization settings.
    """
    logger.info("GET /markets/%s/config", market_id)

    if market_id not in DEFAULT_MARKETS:
        raise HTTPException(
            status_code=404,
            detail=f"Market '{market_id}' not found. Available markets: {list(DEFAULT_MARKETS.keys())}",
        )

    config = DEFAULT_MARKETS[market_id]

    # Calculate available component count
    available = sum(
        1 for v in config["component_availability"].values() if v
    )
    total = len(config["component_availability"])

    return {
        **config,
        "component_summary": {
            "available": available,
            "total": total,
            "missing": [
                k for k, v in config["component_availability"].items() if not v
            ],
        },
    }
