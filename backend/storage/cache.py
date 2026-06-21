"""SQLite-based TTL cache for Westwood MarketPulse.

Provides a simple key-value cache with expiration support. Stores JSON-serialized
values in SQLite for persistence across process restarts.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import threading
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class Cache:
    """Thread-safe SQLite cache with TTL support.

    Stores JSON-serialized values keyed by string identifiers.
    Entries automatically expire based on a configurable TTL.

    Args:
        db_path: Path to the SQLite cache file. Defaults to settings.cache_path.
        default_ttl_minutes: Default TTL when not specified per key.
    """

    def __init__(
        self,
        db_path: Optional[str] = None,
        default_ttl_minutes: Optional[int] = None,
    ) -> None:
        self.db_path: str = db_path or settings.cache_path
        self.default_ttl_minutes: int = (
            default_ttl_minutes or settings.cache_ttl_minutes
        )
        self._local = threading.local()
        self._init_db()

    # ── Connection management ─────────────────────────────────────────────

    def _connection(self) -> sqlite3.Connection:
        """Get a thread-local SQLite connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._local.conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
                isolation_level=None,
            )
            self._local.conn.row_factory = sqlite3.Row
        return self._local.conn

    def _init_db(self) -> None:
        """Create the cache table if it does not exist."""
        with self._connection() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value TEXT NOT NULL,
                    expires_at TIMESTAMP NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_cache_expires
                ON cache(expires_at)
                """
            )

    # ── Public API ────────────────────────────────────────────────────────

    def set(
        self,
        key: str,
        value: Any,
        ttl_minutes: Optional[int] = None,
    ) -> None:
        """Store a value in the cache with an optional TTL.

        Args:
            key: Cache key string.
            value: Any JSON-serializable value.
            ttl_minutes: Time-to-live in minutes. Uses default if None.
        """
        ttl = ttl_minutes or self.default_ttl_minutes
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=ttl)
        serialized = json.dumps(value, default=str)

        with self._connection() as conn:
            conn.execute(
                """
                INSERT INTO cache (key, value, expires_at)
                VALUES (?, ?, ?)
                ON CONFLICT(key) DO UPDATE SET
                    value = excluded.value,
                    expires_at = excluded.expires_at
                """,
                (key, serialized, expires_at.isoformat()),
            )
        logger.debug("Cache SET key=%s ttl=%dm", key, ttl)

    def get(self, key: str) -> Optional[dict]:
        """Retrieve a value from the cache if it exists and is not expired.

        Args:
            key: Cache key string.

        Returns:
            The cached value as a dict, or None if missing/expired.
        """
        self._evict_expired()

        with self._connection() as conn:
            row = conn.execute(
                "SELECT value FROM cache WHERE key = ?",
                (key,),
            ).fetchone()

        if row is None:
            logger.debug("Cache MISS key=%s", key)
            return None

        try:
            value = json.loads(row["value"])
            logger.debug("Cache HIT key=%s", key)
            return value
        except (json.JSONDecodeError, TypeError) as exc:
            logger.warning("Cache corrupt entry for key=%s: %s", key, exc)
            self.delete(key)
            return None

    def delete(self, key: str) -> None:
        """Delete a cache entry by key.

        Args:
            key: Cache key string.
        """
        with self._connection() as conn:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
        logger.debug("Cache DELETE key=%s", key)

    def clear(self) -> None:
        """Remove all entries from the cache."""
        with self._connection() as conn:
            conn.execute("DELETE FROM cache")
        logger.info("Cache cleared")

    # ── Internal ──────────────────────────────────────────────────────────

    def _evict_expired(self) -> None:
        """Remove all expired entries (called lazily on get)."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connection() as conn:
            result = conn.execute(
                "DELETE FROM cache WHERE expires_at < ?",
                (now,),
            )
            if result.rowcount and result.rowcount > 0:
                logger.debug("Cache evicted %d expired entries", result.rowcount)

    def close(self) -> None:
        """Close the thread-local database connection."""
        if hasattr(self._local, "conn") and self._local.conn:
            self._local.conn.close()
            self._local.conn = None

    def __enter__(self) -> Cache:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()
