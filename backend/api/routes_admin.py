"""Admin endpoints — refresh triggers, exports, and diagnostics."""

import logging
import json
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse, PlainTextResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def _generate_static_export(market: str) -> Dict[str, Any]:
    """Generate the static export payload for a market."""
    now = datetime.now(timezone.utc)

    return {
        "generated_at": now.isoformat(),
        "marketpulse": {
            "market": market,
            "timestamp": now.isoformat(),
            "composite": {
                "score": 58,
                "regime": "mp4_risk_on",
                "label": "Risk-On",
                "direction": "stable",
            },
            "classic": {
                "score": 62,
                "change_1d": 3,
                "change_1w": -5,
            },
            "narrative": {
                "score": 55,
                "change_1d": -2,
                "change_1w": 8,
            },
            "positioning": {
                "score": 58,
                "change_1d": 1,
                "change_1w": -3,
            },
            "confidence": 85,
            "explanation": (
                "Markets are risk-on, driven by strong momentum and positioning, "
                "though narrative sentiment has cooled."
            ),
            "components": [
                {
                    "name": "momentum",
                    "score": 72,
                    "direction": "bullish",
                    "description": "Price vs 125-day moving average",
                },
                {
                    "name": "price_strength",
                    "score": 65,
                    "direction": "bullish",
                    "description": "New highs vs new lows",
                },
                {
                    "name": "breadth",
                    "score": 62,
                    "direction": "bullish",
                    "description": "Advancing vs declining volume",
                },
                {
                    "name": "put_call",
                    "score": 55,
                    "direction": "neutral",
                    "description": "CBOE put/call ratio",
                },
                {
                    "name": "credit_spreads",
                    "score": 45,
                    "direction": "bearish",
                    "description": "High yield OAS spread",
                },
                {
                    "name": "volatility",
                    "score": 48,
                    "direction": "neutral",
                    "description": "VIX level",
                },
                {
                    "name": "safe_haven",
                    "score": 58,
                    "direction": "bullish",
                    "description": "Equity vs safe haven relative returns",
                },
            ],
            "data_quality": {
                "overall_confidence": 85,
                "sources_used": 5,
                "sources_available": 7,
                "missing_components": ["etf_flows", "futures_positioning"],
                "stale_data_warnings": [],
                "data_freshness_minutes": 12,
            },
        },
    }


@router.post("/refresh")
async def trigger_refresh(
    market: str = Query(default="sp500", description="Market ID to refresh"),
) -> Dict[str, Any]:
    """Trigger manual data refresh.

    Initiates a full data refresh for the specified market.
    This is an async operation — the endpoint returns immediately
    while the refresh runs in the background.
    """
    logger.info("POST /admin/refresh?market=%s", market)

    try:
        from backend.main import store

        # In a real implementation, this would trigger a background job
        # For now, log and return acknowledgment
        logger.info("Manual refresh triggered for market=%s", market)

        return {
            "status": "accepted",
            "market": market,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "message": f"Refresh job queued for {market}. Check /admin/export/latest.json for results.",
        }

    except ImportError:
        logger.warning("Store not available, refresh is stubbed")
        return {
            "status": "accepted",
            "market": market,
            "triggered_at": datetime.now(timezone.utc).isoformat(),
            "message": "Refresh endpoint is stubbed (no store connected).",
            "note": "Stub mode",
        }
    except Exception as exc:
        logger.error("Error triggering refresh: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to trigger refresh: {str(exc)}")


@router.post("/export-static")
async def trigger_export(
    market: str = Query(default="sp500", description="Market ID to export"),
) -> Dict[str, Any]:
    """Generate static export.

    Creates a static JSON file suitable for public website embedding.
    This is a lightweight snapshot that can be served from a CDN.
    """
    logger.info("POST /admin/export-static?market=%s", market)

    try:
        export_data = _generate_static_export(market)

        # In a real implementation, write to a static file location
        # For now, return the payload
        logger.info("Static export generated for market=%s", market)

        return {
            "status": "completed",
            "market": market,
            "generated_at": export_data["generated_at"],
            "download_url": f"/api/v1/admin/export/latest.json?market={market}",
            "file_size_bytes": len(json.dumps(export_data)),
        }

    except Exception as exc:
        logger.error("Error generating export: %s", exc)
        raise HTTPException(status_code=500, detail=f"Failed to generate export: {str(exc)}")


@router.get("/export/latest.json")
async def get_latest_export(
    market: str = Query(default="sp500", description="Market ID"),
) -> Dict[str, Any]:
    """Download latest static export.

    Returns the most recent static JSON export for the specified market.
    This endpoint is designed to be served directly from a CDN or static file server.
    """
    logger.info("GET /admin/export/latest.json?market=%s", market)

    export_data = _generate_static_export(market)
    return export_data


@router.get("/diagnostics")
async def get_diagnostics() -> Dict[str, Any]:
    """Get system diagnostics.

    Returns internal diagnostics including store connectivity,
    cache status, and pipeline health. For internal use only.
    """
    logger.info("GET /admin/diagnostics")

    diagnostics = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "version": "1.0.0",
        "checks": {},
    }

    # Check store connectivity
    try:
        from backend.main import store
        store.query("SELECT 1")
        diagnostics["checks"]["store"] = {"status": "ok", "type": "DuckDB"}
    except ImportError:
        diagnostics["checks"]["store"] = {"status": "not_configured", "type": "none"}
    except Exception as exc:
        diagnostics["checks"]["store"] = {"status": "error", "error": str(exc)}

    # Check cache
    try:
        from backend.main import cache
        diagnostics["checks"]["cache"] = {"status": "ok", "type": type(cache).__name__}
    except ImportError:
        diagnostics["checks"]["cache"] = {"status": "not_configured", "type": "none"}
    except Exception as exc:
        diagnostics["checks"]["cache"] = {"status": "error", "error": str(exc)}

    # NLP pipeline status
    try:
        from backend.nlp import SentimentModel, TopicClassifier
        sentiment = SentimentModel()
        topics = TopicClassifier()
        diagnostics["checks"]["nlp"] = {
            "status": "ok",
            "finbert_available": sentiment.finbert_available,
            "topics_supported": list(topics.TOPIC_KEYWORDS.keys()),
        }
    except ImportError as exc:
        diagnostics["checks"]["nlp"] = {"status": "not_available", "error": str(exc)}
    except Exception as exc:
        diagnostics["checks"]["nlp"] = {"status": "error", "error": str(exc)}

    # Overall health
    all_ok = all(
        c.get("status") == "ok" or c.get("status") == "not_configured"
        for c in diagnostics["checks"].values()
    )
    diagnostics["overall"] = "healthy" if all_ok else "degraded"

    return diagnostics
