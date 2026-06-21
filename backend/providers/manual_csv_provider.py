"""Manual CSV/JSON import provider.

Reads time-series data from local CSV or JSON files stored in
``/data/sample_sources/``.  Useful for:

* Importing Westwood internal datasets
* One-off research data (e.g. proprietary sentiment indices)
* Back-filling historical series not available from public APIs
* Testing and calibration

Expected file formats
---------------------
**CSV**::

    date,value
    2024-01-15,42.5
    2024-01-16,43.1

**JSON**::

    [
      {"date": "2024-01-15", "value": 42.5},
      {"date": "2024-01-16", "value": 43.1}
    ]

The ``date`` column is parsed flexibly; ``value`` must be numeric.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)

_DEFAULT_DATA_DIR = Path("/data/sample_sources")


class ManualCSVProvider(BaseProvider):
    """Local-file data provider for CSV/JSON time-series imports.

    Scans a directory for ``.csv`` and ``.json`` files, parses each
    into a :class:`pd.DataFrame`, and exposes them by filename stem.
    """

    name: str = "manual_csv"
    tier: str = "public"

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or _DEFAULT_DATA_DIR
        self._cache: Dict[str, pd.DataFrame] = {}
        self._last_fetch: Optional[datetime] = None
        self._error_count: int = 0
        self._load_all()

    # ── internal helpers ──────────────────────────────────────────────

    def _load_all(self) -> None:
        """Eagerly load all supported files in the data directory."""
        if not self.data_dir.exists():
            logger.debug("ManualCSVProvider data directory does not exist: %s", self.data_dir)
            return

        for path in self.data_dir.iterdir():
            if path.suffix.lower() == ".csv":
                self._load_csv(path)
            elif path.suffix.lower() == ".json":
                self._load_json(path)

    def _load_csv(self, path: Path) -> None:
        try:
            df = pd.read_csv(path, parse_dates=["date"])
            key = path.stem
            self._cache[key] = df
            self._last_fetch = datetime.now(timezone.utc)
            logger.debug("Loaded CSV '%s' with %d rows", key, len(df))
        except Exception as exc:
            self._error_count += 1
            logger.warning("Failed to load CSV %s: %s", path, exc)

    def _load_json(self, path: Path) -> None:
        try:
            with open(path, "r", encoding="utf-8") as fh:
                records = json.load(fh)
            if isinstance(records, list):
                df = pd.DataFrame(records)
                if "date" in df.columns:
                    df["date"] = pd.to_datetime(df["date"])
                key = path.stem
                self._cache[key] = df
                self._last_fetch = datetime.now(timezone.utc)
                logger.debug("Loaded JSON '%s' with %d rows", key, len(df))
        except Exception as exc:
            self._error_count += 1
            logger.warning("Failed to load JSON %s: %s", path, exc)

    def _resolve_file(self, series_id: str) -> Optional[pd.DataFrame]:
        """Look up a cached DataFrame by series_id or file stem."""
        # Direct cache hit
        if series_id in self._cache:
            return self._cache[series_id]

        # Try file stem match
        for key, df in self._cache.items():
            if key.lower() == series_id.lower():
                return df

        # Try loading on-demand if file exists
        for ext in (".csv", ".json"):
            path = self.data_dir / f"{series_id}{ext}"
            if path.exists():
                if ext == ".csv":
                    self._load_csv(path)
                else:
                    self._load_json(path)
                return self._cache.get(series_id)

        return None

    # ── BaseProvider implementation ───────────────────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """Return cached CSV/JSON data if it matches the ticker name."""
        df = self._resolve_file(ticker)
        if df is None:
            return None
        # Ensure expected columns
        if "date" not in df.columns:
            return None
        if "close" not in df.columns and "value" in df.columns:
            df = df.rename(columns={"value": "close"})
        if "close" not in df.columns:
            return None
        # Fill missing OHLCV columns with close
        for col in ("open", "high", "low"):
            if col not in df.columns:
                df[col] = df["close"]
        if "volume" not in df.columns:
            df["volume"] = 0
        # Trim to requested days
        df = df.sort_values("date").tail(days)
        return df[["date", "open", "high", "low", "close", "volume"]].copy()

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Return the latest value from cached data as a quote."""
        df = self._resolve_file(ticker)
        if df is None or df.empty:
            return None
        latest = df.iloc[-1]
        return {
            "price": float(latest.get("close", latest.get("value", 0))),
            "change": 0.0,
            "change_percent": 0.0,
            "volume": 0,
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        return None

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        return None

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Return cached spread data if available."""
        df = self._resolve_file(series_id)
        if df is None or df.empty:
            return None
        latest = df.iloc[-1]
        return {
            "hy_spread": float(latest.get("value", latest.get("hy_spread", 0))),
            "ig_spread": float(latest.get("ig_spread", 0)),
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        return []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        return []

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        df = self._resolve_file(ticker)
        if df is None or df.empty:
            return None
        latest = df.iloc[-1]
        return {
            "inflow": float(latest.get("inflow", 0)),
            "outflow": float(latest.get("outflow", 0)),
            "net_flow": float(latest.get("net_flow", 0)),
            "aum": float(latest.get("aum", 0)),
            "timestamp": datetime.now(timezone.utc),
        }

    async def get_source_status(self) -> SourceStatus:
        file_count = len(self._cache)
        age_minutes = None
        if self._last_fetch:
            age = datetime.now(timezone.utc) - self._last_fetch
            age_minutes = int(age.total_seconds() / 60)
        return SourceStatus(
            provider=self.name,
            available=file_count > 0,
            last_successful_fetch=self._last_fetch,
            error_count_24h=self._error_count,
            data_freshness_minutes=age_minutes,
            tier=self.tier,
        )
