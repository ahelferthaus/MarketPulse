"""
Westwood MarketPulse — FastAPI Application

Main entry point for the MarketPulse API server.
Provides RESTful endpoints for market sentiment scores,
component breakdowns, narrative analysis, and embeddable widgets.
"""

import logging
import sys
from contextlib import asynccontextmanager
from pathlib import Path

# Ensure backend package is importable
BACKEND_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = BACKEND_DIR.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Global store instances
store = None
cache = None


def _create_fallback_store():
    """Create a minimal in-memory fallback store when DuckDB is unavailable."""
    class FallbackStore:
        """Minimal fallback that logs queries but returns no data."""

        def __init__(self, path=None):
            self.path = path or ":memory:"
            logger.info("Using fallback in-memory store")

        def init_database(self):
            """No-op for fallback store."""
            pass

        def query(self, sql, params=None):
            """Log query and return empty result."""
            logger.debug("FallbackStore query (no data): %s", sql[:100])
            return []

        def execute(self, sql, params=None):
            """Log execute."""
            logger.debug("FallbackStore execute: %s", sql[:100])

        def close(self):
            """No-op close."""
            pass

    return FallbackStore


def _create_fallback_cache():
    """Create a minimal in-memory fallback cache."""
    class FallbackCache:
        """Simple dict-based cache with TTL support."""

        def __init__(self, path=None):
            self._data = {}
            self._expiry = {}
            import time
            self._time = time
            logger.info("Using fallback in-memory cache")

        def get(self, key):
            """Get cached value if not expired."""
            if key in self._data:
                if self._time.time() < self._expiry.get(key, 0):
                    return self._data[key]
                else:
                    self.delete(key)
            return None

        def set(self, key, value, ttl=300):
            """Set cached value with TTL in seconds."""
            self._data[key] = value
            self._expiry[key] = self._time.time() + ttl

        def delete(self, key):
            """Delete cached value."""
            self._data.pop(key, None)
            self._expiry.pop(key, None)

        def clear(self):
            """Clear all cached values."""
            self._data.clear()
            self._expiry.clear()

    return FallbackCache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager.

    Initializes storage connections on startup and
    cleans up resources on shutdown.
    """
    global store, cache

    logger.info("MarketPulse API starting up...")

    # Initialize store
    try:
        from backend.storage.duckdb_store import DuckDBStore

        # None -> DuckDBStore falls back to settings.duckdb_path, keeping the
        # API and the batch jobs (compute_scores etc.) on the SAME database.
        # (A hardcoded ".data/..." here once split them into two silos.)
        store = DuckDBStore(getattr(app.state, "duckdb_path", None))
        store.init_database()
        logger.info("DuckDB store initialized")
    except ImportError:
        logger.warning("DuckDBStore not available, using fallback store")
        FallbackStore = _create_fallback_store()
        store = FallbackStore()
    except Exception as exc:
        logger.error("Failed to initialize DuckDB store: %s", exc)
        FallbackStore = _create_fallback_store()
        store = FallbackStore()

    # Initialize cache
    try:
        from backend.storage.cache import Cache

        # None -> Cache falls back to settings.cache_path (same silo rule
        # as the store above).
        cache = Cache(getattr(app.state, "cache_path", None))
        logger.info("Cache initialized")
    except ImportError:
        logger.warning("Cache not available, using fallback cache")
        FallbackCache = _create_fallback_cache()
        cache = FallbackCache()
    except Exception as exc:
        logger.error("Failed to initialize cache: %s", exc)
        FallbackCache = _create_fallback_cache()
        cache = FallbackCache()

    # Initialize NLP pipeline
    try:
        from backend.nlp import SentimentModel, TopicClassifier

        sentiment_model = SentimentModel()
        topic_classifier = TopicClassifier()
        app.state.sentiment_model = sentiment_model
        app.state.topic_classifier = topic_classifier
        logger.info(
            "NLP pipeline initialized (FinBERT: %s)",
            sentiment_model.finbert_available,
        )
    except ImportError:
        logger.warning("NLP pipeline not available")
    except Exception as exc:
        logger.warning("NLP pipeline initialization failed: %s", exc)

    # Store references in app state for route access
    app.state.store = store
    app.state.cache = cache

    logger.info("MarketPulse API ready")
    yield

    # Shutdown
    logger.info("MarketPulse API shutting down...")
    if store:
        try:
            store.close()
        except Exception as exc:
            logger.warning("Error closing store: %s", exc)
    logger.info("MarketPulse API shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="Westwood MarketPulse API",
    description=(
        "Market sentiment and risk appetite platform. "
        "Provides daily 0-100 indices for market psychology across "
        "Classic, Narrative, Positioning & Flows, and Composite dimensions."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # TODO: Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and include all routers
try:
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

    app.include_router(routes_scores.router)
    app.include_router(routes_markets.router)
    app.include_router(routes_components.router)
    app.include_router(routes_history.router)
    app.include_router(routes_embed.router)
    app.include_router(routes_sources.router)
    app.include_router(routes_narrative.router)
    app.include_router(routes_backtest.router)
    app.include_router(routes_admin.router)

    logger.info("All API routers registered")
except ImportError as exc:
    logger.warning("Some routers could not be imported: %s", exc)


@app.get("/health", tags=["health"])
async def health_check() -> dict:
    """Health check endpoint.

    Returns service status and basic diagnostics.
    """
    global store, cache

    checks = {}

    # Check store
    if store is not None:
        try:
            store.query("SELECT 1")
            checks["store"] = "connected"
        except Exception:
            checks["store"] = "degraded"
    else:
        checks["store"] = "not_initialized"

    # Check cache
    if cache is not None:
        checks["cache"] = "connected"
    else:
        checks["cache"] = "not_initialized"

    all_healthy = all(v == "connected" for v in checks.values())

    return {
        "status": "healthy" if all_healthy else "degraded",
        "version": "1.0.0",
        "checks": checks,
    }


@app.get("/", tags=["root"])
async def root() -> dict:
    """Root endpoint.

    Returns API metadata and documentation links.
    """
    return {
        "name": "Westwood MarketPulse API",
        "version": "1.0.0",
        "description": "Market sentiment and risk appetite platform",
        "docs": "/docs",
        "redoc": "/redoc",
        "health": "/health",
        "endpoints": {
            "scores": "/api/v1/scores",
            "markets": "/api/v1/markets",
            "components": "/api/v1/components",
            "history": "/api/v1/history",
            "narrative": "/api/v1/narrative",
            "sources": "/api/v1/sources",
            "embed": "/api/v1/embed",
            "backtest": "/api/v1/backtest",
            "admin": "/api/v1/admin",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
