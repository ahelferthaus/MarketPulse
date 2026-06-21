"""Static export generator job for Westwood MarketPulse.

Reads the latest scores from DuckDB, generates sanitized JSON exports
for each configured market, and saves them to the static payloads directory.

These exports are suitable for:
- Public website consumption
- Embeddable widgets
- CDN distribution
- Third-party integrations

All exports contain ONLY derived scores — no raw prices, no ticker data.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.domain.market import DEFAULT_MARKETS
from backend.storage.duckdb_store import DuckDBStore
from backend.storage.exports import ExportManager

logger = logging.getLogger(__name__)


async def generate_all_exports(
    store: Optional[DuckDBStore] = None,
    export_manager: Optional[ExportManager] = None,
) -> Dict[str, Any]:
    """Generate static exports for all configured markets.

    Args:
        store: DuckDBStore to read scores from. Creates one if None.
        export_manager: ExportManager for saving payloads. Creates one if None.

    Returns:
        Dict with export results: {'success': [...], 'failed': [...], 'files': {...}}
    """
    if store is None:
        store = DuckDBStore()
        store.init_database()

    if export_manager is None:
        export_manager = ExportManager()

    results: Dict[str, Any] = {
        "success": [],
        "failed": [],
        "files": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("=== Static Export Generation Started ===")

    for market_id in DEFAULT_MARKETS:
        try:
            # Generate export from latest database records
            payload = export_manager.generate_from_latest(market_id, store)

            # Save to disk
            filepath = export_manager.save_export(payload)

            results["success"].append(market_id)
            results["files"][market_id] = str(filepath)

            logger.info(
                "Export generated for %s: composite=%d → %s",
                market_id,
                payload["marketpulse"]["composite"]["score"],
                filepath.name if hasattr(filepath, "name") else filepath,
            )

        except Exception as exc:
            logger.error(
                "Export generation failed for %s: %s",
                market_id,
                exc,
                exc_info=True,
            )
            results["failed"].append(market_id)

    logger.info(
        "=== Export Generation Complete: %d succeeded, %d failed ===",
        len(results["success"]),
        len(results["failed"]),
    )

    return results


def generate_all_exports_sync(
    store: Optional[DuckDBStore] = None,
    export_manager: Optional[ExportManager] = None,
) -> Dict[str, Any]:
    """Synchronous wrapper for generate_all_exports.

    Args:
        store: DuckDBStore to read scores from. Creates one if None.
        export_manager: ExportManager for saving payloads. Creates one if None.

    Returns:
        Dict with export results.
    """
    return asyncio.run(generate_all_exports(store, export_manager))


# ── CLI entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    store: Optional[DuckDBStore] = None
    try:
        store = DuckDBStore()
        store.init_database()
        export_manager = ExportManager()

        results = asyncio.run(generate_all_exports(store, export_manager))

        print(f"\nExport Results ({results['timestamp']}):")
        print(f"  Success: {', '.join(results['success']) or 'None'}")
        print(f"  Failed:  {', '.join(results['failed']) or 'None'}")
        print(f"\nFiles:")
        for market_id, filepath in results["files"].items():
            print(f"  {market_id}: {filepath}")

    except Exception as exc:
        logger.error("Export generation failed: %s", exc, exc_info=True)
        sys.exit(1)
    finally:
        if store:
            store.close()
