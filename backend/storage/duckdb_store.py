"""DuckDB analytical store for Westwood MarketPulse.

Provides persistent storage for scores, component scores, narrative snapshots,
articles, provider status logs, and regime periods. Uses DuckDB for efficient
analytical queries and time-series operations.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Generator, List, Optional

import duckdb

from backend.config import settings
from backend.domain.article import Article
from backend.domain.indicator import IndicatorResult
from backend.domain.regime import RegimePeriod
from backend.domain.score import MarketPulseScore
from backend.domain.sentiment import NarrativeSnapshot

logger = logging.getLogger(__name__)

# SQL DDL for all tables
_INIT_SQL = """
-- Core scores table
CREATE TABLE IF NOT EXISTS scores (
    timestamp TIMESTAMP,
    market_id VARCHAR,
    classic_score DOUBLE,
    narrative_score DOUBLE,
    positioning_score DOUBLE,
    composite_score DOUBLE,
    regime VARCHAR,
    confidence DOUBLE,
    explanation VARCHAR,
    PRIMARY KEY (timestamp, market_id)
);

-- Component scores (one row per component per timestamp)
CREATE TABLE IF NOT EXISTS component_scores (
    timestamp TIMESTAMP,
    market_id VARCHAR,
    component_name VARCHAR,
    raw_value DOUBLE,
    normalized_score DOUBLE,
    weight DOUBLE,
    direction VARCHAR,
    data_source VARCHAR,
    confidence DOUBLE,
    PRIMARY KEY (timestamp, market_id, component_name)
);

-- Narrative sentiment snapshots
CREATE TABLE IF NOT EXISTS narrative_snapshots (
    timestamp TIMESTAMP,
    market_id VARCHAR,
    panic_score DOUBLE,
    caution_score DOUBLE,
    uncertainty_score DOUBLE,
    optimism_score DOUBLE,
    complacency_score DOUBLE,
    euphoria_score DOUBLE,
    article_count INTEGER,
    top_phrases VARCHAR[],
    PRIMARY KEY (timestamp, market_id)
);

-- Scored articles
CREATE SEQUENCE IF NOT EXISTS article_seq START 1;
CREATE TABLE IF NOT EXISTS articles (
    id BIGINT PRIMARY KEY DEFAULT nextval('article_seq'),
    timestamp TIMESTAMP,
    source VARCHAR,
    title VARCHAR,
    url VARCHAR,
    content VARCHAR,
    sentiment_score DOUBLE,
    panic_score DOUBLE DEFAULT 50.0,
    caution_score DOUBLE DEFAULT 50.0,
    uncertainty_score DOUBLE DEFAULT 50.0,
    optimism_score DOUBLE DEFAULT 50.0,
    complacency_score DOUBLE DEFAULT 50.0,
    euphoria_score DOUBLE DEFAULT 50.0,
    topics VARCHAR[],
    market_relevance DOUBLE DEFAULT 1.0
);

-- Provider status log
CREATE TABLE IF NOT EXISTS provider_status_log (
    timestamp TIMESTAMP,
    provider VARCHAR,
    available BOOLEAN,
    response_ms INTEGER,
    error_message VARCHAR
);

-- Regime history for backtesting
CREATE TABLE IF NOT EXISTS regime_periods (
    market_id VARCHAR,
    regime VARCHAR,
    start_date DATE,
    end_date DATE,
    avg_forward_1m DOUBLE,
    avg_forward_3m DOUBLE,
    avg_forward_6m DOUBLE,
    avg_forward_12m DOUBLE
);
"""


class DuckDBStore:
    """DuckDB analytical store for all MarketPulse data.

    Manages the DuckDB database connection and provides CRUD operations
    for scores, component scores, narrative snapshots, articles, provider
    status logs, and regime periods.

    Args:
        db_path: Path to the DuckDB database file. Defaults to settings.duckdb_path.
    """

    def __init__(self, db_path: Optional[str] = None, read_only: bool = False) -> None:
        self.db_path: str = db_path or settings.duckdb_path
        self.read_only: bool = read_only
        self._conn: Optional[duckdb.DuckDBPyConnection] = None

    # ── Connection management ─────────────────────────────────────────────

    def _connect(self) -> duckdb.DuckDBPyConnection:
        """Establish a connection to the DuckDB database.

        read_only=True lets a second process (e.g. the payload generator)
        read while the API server holds the write lock.
        """
        if self._conn is None:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
            self._conn = duckdb.connect(self.db_path, read_only=self.read_only)
            logger.debug("DuckDB connection opened: %s (ro=%s)", self.db_path, self.read_only)
        return self._conn

    def close(self) -> None:
        """Close the DuckDB connection."""
        if self._conn:
            self._conn.close()
            self._conn = None
            logger.debug("DuckDB connection closed")

    @contextmanager
    def _cursor(self) -> Generator[duckdb.DuckDBPyConnection, None, None]:
        """Context manager for DuckDB cursor operations."""
        conn = self._connect()
        try:
            yield conn
        except Exception:
            conn.rollback()
            raise

    def query(self, sql: str, params: Optional[list] = None) -> list:
        """Run a read query and return rows as dicts (column-name keyed).

        The API route handlers use this generic accessor for ad-hoc reads
        (latest component scores, provider status) and consume rows via
        ``row.get(...)`` — so rows must be dicts, not tuples.
        """
        with self._cursor() as conn:
            cur = conn.execute(sql, params or [])
            columns = [d[0] for d in cur.description] if cur.description else []
            return [dict(zip(columns, row)) for row in cur.fetchall()]

    # ── Database initialization ───────────────────────────────────────────

    def init_database(self) -> None:
        """Create all tables and sequences if they do not exist."""
        with self._cursor() as conn:
            for statement in _INIT_SQL.strip().split(";"):
                stmt = statement.strip()
                if stmt:
                    conn.execute(stmt)
        logger.info("DuckDB database initialized: %s", self.db_path)

    # ── Scores ────────────────────────────────────────────────────────────

    def save_score(self, score: MarketPulseScore) -> None:
        """Save a complete MarketPulseScore snapshot.

        Args:
            score: The score snapshot to persist.
        """
        with self._cursor() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO scores (
                    timestamp, market_id, classic_score, narrative_score,
                    positioning_score, composite_score, regime, confidence,
                    explanation
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    score.timestamp,
                    score.market_id,
                    score.classic_score,
                    score.narrative_score,
                    score.positioning_score,
                    score.composite_score,
                    score.regime.value,
                    score.confidence,
                    score.explanation,
                ),
            )
        logger.debug(
            "Score saved: %s @ %s (composite=%.1f)",
            score.market_id,
            score.timestamp.isoformat(),
            score.composite_score,
        )

    def get_latest_score(self, market_id: str) -> Optional[MarketPulseScore]:
        """Retrieve the most recent score for a market.

        Args:
            market_id: Market identifier (e.g., 'sp500').

        Returns:
            The most recent MarketPulseScore, or None if no scores exist.
        """
        with self._cursor() as conn:
            row = conn.execute(
                """
                SELECT * FROM scores
                WHERE market_id = ?
                ORDER BY timestamp DESC
                LIMIT 1
                """,
                (market_id,),
            ).fetchone()

        if row is None:
            return None

        return self._row_to_score(row)

    def get_score_history(
        self,
        market_id: str,
        days: int = 30,
    ) -> List[MarketPulseScore]:
        """Retrieve score history for a market over the given lookback period.

        Args:
            market_id: Market identifier (e.g., 'sp500').
            days: Number of days of history to retrieve.

        Returns:
            List of MarketPulseScore objects, ordered by timestamp ascending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with self._cursor() as conn:
            rows = conn.execute(
                """
                SELECT * FROM scores
                WHERE market_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                """,
                (market_id, cutoff),
            ).fetchall()

        return [self._row_to_score(row) for row in rows]

    # ── Component scores ──────────────────────────────────────────────────

    def save_component_scores(
        self,
        timestamp: datetime,
        market_id: str,
        components: List[IndicatorResult],
    ) -> None:
        """Save component scores for a given timestamp and market.

        Args:
            timestamp: Score timestamp.
            market_id: Market identifier.
            components: List of IndicatorResult objects to persist.
        """
        with self._cursor() as conn:
            for comp in components:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO component_scores (
                        timestamp, market_id, component_name, raw_value,
                        normalized_score, weight, direction, data_source, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        timestamp,
                        market_id,
                        comp.name,
                        comp.raw_value,
                        comp.normalized_score,
                        comp.weight,
                        comp.direction,
                        comp.data_source,
                        comp.confidence,
                    ),
                )
        logger.debug(
            "Saved %d component scores for %s @ %s",
            len(components),
            market_id,
            timestamp.isoformat(),
        )

    def get_component_history(
        self,
        market_id: str,
        component: str,
        days: int = 90,
    ) -> List[dict]:
        """Retrieve historical values for a single component.

        Args:
            market_id: Market identifier.
            component: Component name (e.g., 'momentum').
            days: Number of days of history to retrieve.

        Returns:
            List of dicts with keys: timestamp, raw_value, normalized_score,
            weight, direction, data_source, confidence.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with self._cursor() as conn:
            rows = conn.execute(
                """
                SELECT
                    timestamp,
                    raw_value,
                    normalized_score,
                    weight,
                    direction,
                    data_source,
                    confidence
                FROM component_scores
                WHERE market_id = ? AND component_name = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                """,
                (market_id, component, cutoff),
            ).fetchall()

        return [
            {
                "timestamp": row[0],
                "raw_value": row[1],
                "normalized_score": row[2],
                "weight": row[3],
                "direction": row[4],
                "data_source": row[5],
                "confidence": row[6],
            }
            for row in rows
        ]

    def get_all_components_at_time(
        self,
        market_id: str,
        timestamp: Optional[datetime] = None,
    ) -> List[dict]:
        """Retrieve all component scores for a market at a specific time.

        Args:
            market_id: Market identifier.
            timestamp: Specific timestamp. Uses latest if None.

        Returns:
            List of component score dicts.
        """
        with self._cursor() as conn:
            if timestamp:
                rows = conn.execute(
                    """
                    SELECT
                        component_name,
                        raw_value,
                        normalized_score,
                        weight,
                        direction,
                        data_source,
                        confidence
                    FROM component_scores
                    WHERE market_id = ? AND timestamp = ?
                    ORDER BY component_name
                    """,
                    (market_id, timestamp),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT
                        component_name,
                        raw_value,
                        normalized_score,
                        weight,
                        direction,
                        data_source,
                        confidence
                    FROM component_scores
                    WHERE market_id = ?
                        AND timestamp = (
                            SELECT MAX(timestamp) FROM component_scores
                            WHERE market_id = ?
                        )
                    ORDER BY component_name
                    """,
                    (market_id, market_id),
                ).fetchall()

        return [
            {
                "component_name": row[0],
                "raw_value": row[1],
                "normalized_score": row[2],
                "weight": row[3],
                "direction": row[4],
                "data_source": row[5],
                "confidence": row[6],
            }
            for row in rows
        ]

    # ── Narrative snapshots ───────────────────────────────────────────────

    def save_narrative_snapshot(self, snapshot: NarrativeSnapshot) -> None:
        """Save a narrative sentiment snapshot.

        Args:
            snapshot: The NarrativeSnapshot to persist.
        """
        with self._cursor() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO narrative_snapshots (
                    timestamp, market_id, panic_score, caution_score,
                    uncertainty_score, optimism_score, complacency_score,
                    euphoria_score, article_count, top_phrases
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    snapshot.timestamp,
                    snapshot.market_id,
                    snapshot.panic_score,
                    snapshot.caution_score,
                    snapshot.uncertainty_score,
                    snapshot.optimism_score,
                    snapshot.complacency_score,
                    snapshot.euphoria_score,
                    snapshot.article_count,
                    snapshot.top_phrases,
                ),
            )
        logger.debug(
            "Narrative snapshot saved: %s @ %s",
            snapshot.market_id,
            snapshot.timestamp.isoformat(),
        )

    def get_narrative_history(
        self,
        market_id: str,
        days: int = 30,
    ) -> List[dict]:
        """Retrieve narrative snapshot history for a market.

        Args:
            market_id: Market identifier.
            days: Number of days of history.

        Returns:
            List of narrative snapshot dicts, ordered by timestamp ascending.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        with self._cursor() as conn:
            rows = conn.execute(
                """
                SELECT
                    timestamp,
                    panic_score,
                    caution_score,
                    uncertainty_score,
                    optimism_score,
                    complacency_score,
                    euphoria_score,
                    article_count,
                    top_phrases
                FROM narrative_snapshots
                WHERE market_id = ? AND timestamp >= ?
                ORDER BY timestamp ASC
                """,
                (market_id, cutoff),
            ).fetchall()

        return [
            {
                "timestamp": row[0],
                "panic_score": row[1],
                "caution_score": row[2],
                "uncertainty_score": row[3],
                "optimism_score": row[4],
                "complacency_score": row[5],
                "euphoria_score": row[6],
                "article_count": row[7],
                "top_phrases": row[8],
            }
            for row in rows
        ]

    # ── Articles ──────────────────────────────────────────────────────────

    def save_articles(self, articles: List[Article]) -> None:
        """Save scored articles to the database.

        Args:
            articles: List of Article objects to persist.
        """
        with self._cursor() as conn:
            for article in articles:
                conn.execute(
                    """
                    INSERT INTO articles (
                        timestamp, source, title, url, content,
                        sentiment_score, panic_score, caution_score,
                        uncertainty_score, optimism_score, complacency_score,
                        euphoria_score, topics, market_relevance
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        article.timestamp,
                        article.source,
                        article.title,
                        article.url,
                        article.content,
                        article.sentiment_score,
                        article.panic_score,
                        article.caution_score,
                        article.uncertainty_score,
                        article.optimism_score,
                        article.complacency_score,
                        article.euphoria_score,
                        article.topics,
                        article.market_relevance,
                    ),
                )
        logger.debug("Saved %d articles", len(articles))

    def get_articles(
        self,
        market_id: Optional[str] = None,
        limit: int = 50,
    ) -> List[Article]:
        """Retrieve recent scored articles.

        Args:
            market_id: Optional market filter (filters by source containing market_id).
            limit: Maximum number of articles to return.

        Returns:
            List of Article objects, ordered by timestamp descending.
        """
        with self._cursor() as conn:
            if market_id:
                rows = conn.execute(
                    """
                    SELECT
                        id, timestamp, source, title, url, content,
                        sentiment_score, panic_score, caution_score,
                        uncertainty_score, optimism_score, complacency_score,
                        euphoria_score, topics, market_relevance
                    FROM articles
                    WHERE source LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (f"%{market_id}%", limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT
                        id, timestamp, source, title, url, content,
                        sentiment_score, panic_score, caution_score,
                        uncertainty_score, optimism_score, complacency_score,
                        euphoria_score, topics, market_relevance
                    FROM articles
                    ORDER BY timestamp DESC
                    LIMIT ?
                    """,
                    (limit,),
                ).fetchall()

        return [
            Article(
                id=row[0],
                timestamp=row[1],
                source=row[2],
                title=row[3],
                url=row[4],
                content=row[5],
                sentiment_score=row[6],
                panic_score=row[7] if row[7] is not None else 50.0,
                caution_score=row[8] if row[8] is not None else 50.0,
                uncertainty_score=row[9] if row[9] is not None else 50.0,
                optimism_score=row[10] if row[10] is not None else 50.0,
                complacency_score=row[11] if row[11] is not None else 50.0,
                euphoria_score=row[12] if row[12] is not None else 50.0,
                topics=row[13] if row[13] else [],
                market_relevance=row[14] if row[14] is not None else 1.0,
            )
            for row in rows
        ]

    # ── Provider status log ───────────────────────────────────────────────

    def log_provider_status(
        self,
        provider: str,
        available: bool,
        response_ms: Optional[int] = None,
        error_message: Optional[str] = None,
    ) -> None:
        """Log a provider status event.

        Args:
            provider: Provider name.
            available: Whether the provider is operational.
            response_ms: Response time in milliseconds.
            error_message: Error message if the provider failed.
        """
        with self._cursor() as conn:
            conn.execute(
                """
                INSERT INTO provider_status_log (
                    timestamp, provider, available, response_ms, error_message
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    datetime.now(timezone.utc),
                    provider,
                    available,
                    response_ms,
                    error_message,
                ),
            )

    def get_provider_status_history(
        self,
        provider: Optional[str] = None,
        hours: int = 24,
    ) -> List[dict]:
        """Retrieve provider status history.

        Args:
            provider: Optional provider name filter.
            hours: Number of hours of history.

        Returns:
            List of status log dicts.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        with self._cursor() as conn:
            if provider:
                rows = conn.execute(
                    """
                    SELECT timestamp, provider, available, response_ms, error_message
                    FROM provider_status_log
                    WHERE provider = ? AND timestamp >= ?
                    ORDER BY timestamp DESC
                    """,
                    (provider, cutoff),
                ).fetchall()
            else:
                rows = conn.execute(
                    """
                    SELECT timestamp, provider, available, response_ms, error_message
                    FROM provider_status_log
                    WHERE timestamp >= ?
                    ORDER BY timestamp DESC
                    """,
                    (cutoff,),
                ).fetchall()

        return [
            {
                "timestamp": row[0],
                "provider": row[1],
                "available": row[2],
                "response_ms": row[3],
                "error_message": row[4],
            }
            for row in rows
        ]

    # ── Regime periods ────────────────────────────────────────────────────

    def save_regime_period(self, period: RegimePeriod) -> None:
        """Save a regime period.

        Args:
            period: The RegimePeriod to persist.
        """
        with self._cursor() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO regime_periods (
                    market_id, regime, start_date, end_date,
                    avg_forward_1m, avg_forward_3m, avg_forward_6m, avg_forward_12m
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    period.market_id,
                    period.regime,
                    period.start_date,
                    period.end_date,
                    period.avg_forward_1m,
                    period.avg_forward_3m,
                    period.avg_forward_6m,
                    period.avg_forward_12m,
                ),
            )

    def get_regime_periods(
        self,
        market_id: str,
    ) -> List[RegimePeriod]:
        """Retrieve all regime periods for a market.

        Args:
            market_id: Market identifier.

        Returns:
            List of RegimePeriod objects, ordered by start_date descending.
        """
        with self._cursor() as conn:
            rows = conn.execute(
                """
                SELECT
                    market_id, regime, start_date, end_date,
                    avg_forward_1m, avg_forward_3m, avg_forward_6m, avg_forward_12m
                FROM regime_periods
                WHERE market_id = ?
                ORDER BY start_date DESC
                """,
                (market_id,),
            ).fetchall()

        return [
            RegimePeriod(
                market_id=row[0],
                regime=row[1],
                start_date=row[2],
                end_date=row[3],
                avg_forward_1m=row[4],
                avg_forward_3m=row[5],
                avg_forward_6m=row[6],
                avg_forward_12m=row[7],
            )
            for row in rows
        ]

    # ── Internal helpers ──────────────────────────────────────────────────

    def _row_to_score(self, row) -> MarketPulseScore:
        """Convert a DuckDB row tuple to a MarketPulseScore.

        Note: drivers and data_quality are not stored in the scores table
        and are returned with sensible defaults. Use get_all_components_at_time
        to reconstruct full driver information.

        Args:
            row: DuckDB row tuple from the scores table.

        Returns:
            A MarketPulseScore with default drivers/data_quality.
        """
        from backend.domain.score import (
            DataQualityReport,
            Regime,
            ScoreDriver,
        )

        return MarketPulseScore(
            timestamp=row[0],
            market_id=row[1],
            classic_score=row[2],
            narrative_score=row[3],
            positioning_score=row[4],
            composite_score=row[5],
            regime=Regime(row[6]),
            regime_label=Regime(row[6]).label,
            direction="stable",
            confidence=row[7] if row[7] is not None else 50.0,
            explanation=row[8] if row[8] else "",
            what_changed=None,
            drivers=[],
            data_quality=DataQualityReport(
                overall_confidence=50.0,
                sources_used=0,
                sources_available=0,
                missing_components=[],
                substituted_components=[],
                stale_data_warnings=[],
                data_freshness_minutes=0,
            ),
        )

    # ── Context manager ───────────────────────────────────────────────────

    def __enter__(self) -> DuckDBStore:
        return self

    def __exit__(self, *args) -> None:
        self.close()
