"""FastAPI routes for Westwood MarketPulse."""

from backend.api import (
    routes_admin,
    routes_backtest,
    routes_components,
    routes_embed,
    routes_history,
    routes_markets,
    routes_narrative,
    routes_scores,
    routes_sources,
)

__all__ = [
    "routes_scores",
    "routes_markets",
    "routes_components",
    "routes_history",
    "routes_embed",
    "routes_sources",
    "routes_narrative",
    "routes_backtest",
    "routes_admin",
]
