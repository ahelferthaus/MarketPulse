"""Generate static JSON payloads consumed by the frontend2 React app.

The React app (frontend2) reads pre-generated JSON from `<base>/data/*.json`
when no live backend URL is configured. This job produces those files by
calling the same API endpoint handlers the live backend serves, so the static
payloads and the live responses share one shape — switching the frontend to a
hosted backend later is just setting VITE_API_BASE_URL.

The endpoint handlers degrade gracefully to demo data when no DuckDB store is
connected, so this runs standalone with no database or network access.

Usage:
    python -m backend.jobs.generate_frontend_payloads
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from pathlib import Path
from typing import Any, Dict

from backend.api import (
    routes_backtest,
    routes_components,
    routes_history,
    routes_scores,
    routes_sources,
)

logger = logging.getLogger(__name__)

# Markets to export. Mirrors DEFAULT_MARKETS in routes_markets.
MARKETS = ["sp500", "nasdaq100", "russell2000", "dow"]

# Output directory: frontend2/public/data is copied verbatim into the build
# output (dist/data) and served at <base>/data/ on GitHub Pages.
OUTPUT_DIR = (
    Path(__file__).resolve().parents[2] / "frontend2" / "public" / "data"
)


def _connect_store() -> None:
    """Wire the route handlers to the real store/cache.

    The handlers read ``backend.main.store``/``cache`` module globals, which
    are normally assigned during FastAPI startup. When this job runs
    standalone we assign them here so the payloads carry the real computed
    scores (run ``backend.jobs.compute_scores`` first). If anything fails,
    the handlers keep their graceful demo fallback.
    """
    import backend.main as main_module

    try:
        from backend.storage.duckdb_store import DuckDBStore
        from backend.storage.cache import Cache

        try:
            store = DuckDBStore()
            store.init_database()
        except Exception:
            # the API server holds the write lock — read alongside it
            store = DuckDBStore(read_only=True)
            store.query("SELECT 1")
        main_module.store = store
        main_module.cache = Cache()
        logger.info("Payload generator connected to store: %s (ro=%s)",
                    store.db_path, store.read_only)
    except Exception as exc:  # pragma: no cover — CI without optional deps
        logger.warning("No store available (%s) — payloads will use fallbacks", exc)


async def _build_payloads() -> Dict[str, Any]:
    """Call each endpoint handler and return a {filename: payload} mapping."""
    _connect_store()
    payloads: Dict[str, Any] = {}

    # Per-market payloads.
    for market in MARKETS:
        payloads[f"scores-current-{market}"] = await routes_scores.get_current_score(
            market=market
        )
        # sp500 ships the full 23-year point-in-time reconstruction (the
        # homepage barometer history); other markets ship one year to keep
        # the static bundle and the daily payload-refresh commits small.
        payloads[f"history-scores-{market}"] = await routes_history.get_score_history(
            market=market, days=9000 if market == "sp500" else 365
        )
        payloads[
            f"components-current-{market}"
        ] = await routes_components.get_current_components(market=market)
        payloads[
            f"backtest-regimes-{market}"
        ] = await routes_backtest.get_regime_backtest(market=market)

    # Global payloads.
    payloads["sources-status"] = await routes_sources.get_all_source_status()

    return payloads


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    payloads = asyncio.run(_build_payloads())

    for name, payload in payloads.items():
        fpath = OUTPUT_DIR / f"{name}.json"
        with open(fpath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, default=str)
        logger.info("Wrote %s", fpath.relative_to(OUTPUT_DIR.parents[2]))

    logger.info("Generated %d payload(s) in %s", len(payloads), OUTPUT_DIR)
    return 0


if __name__ == "__main__":
    sys.exit(main())
