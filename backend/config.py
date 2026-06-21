"""Central configuration for Westwood MarketPulse.

Loads settings from environment variables (via .env file) and provides
type-safe access to all application configuration. Uses Pydantic Settings
for validation and defaults.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional

from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env file if present (non-fatal if missing)
load_dotenv()


class Settings(BaseSettings):
    """Application settings for Westwood MarketPulse.

    All values can be overridden via environment variables or a .env file.
    Boolean flags accept 'true', '1', 'yes' (case-insensitive) as True.

    Attributes:
        marketpulse_mode: Operating mode — public, premium, or professional.
        enabled_providers: Comma-separated list of active data providers.
        log_level: Python logging level (DEBUG, INFO, WARNING, ERROR).

        data_dir: Root directory for all data files.
        duckdb_path: Path to the DuckDB analytical database.
        cache_path: Path to the SQLite cache database.
        exports_dir: Directory for exported data files.
        static_payloads_dir: Directory for static site JSON payloads.

        fmp_api_key: Financial Modeling Prep API key (premium).
        fred_api_key: FRED (Federal Reserve Economic Data) API key.
        newsapi_key: NewsAPI.org API key.
        bloomberg_mcp_path: Path to Bloomberg MCP bridge executable.
        morningstar_mcp_path: Path to Morningstar MCP bridge executable.

        daily_update_time: UTC time for the daily update job (HH:MM).
        intraday_refresh_minutes: Minutes between intraday data refreshes.
        cache_ttl_minutes: Default cache time-to-live in minutes.

        enable_narrative: Enable narrative sentiment scoring.
        enable_positioning: Enable positioning & flows scoring.
        enable_nlp_llm: Enable LLM-based NLP summarization.
        enable_backtest: Enable backtesting endpoints.
        enable_admin_endpoints: Enable admin API endpoints.

        normalization_method: Rolling percentile, min-max, or z-score.
        rolling_window_days: Days of history for rolling normalizations.
        classic_weight: Weight of Classic index in composite.
        narrative_weight: Weight of Narrative index in composite.
        positioning_weight: Weight of Positioning index in composite.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Mode ──────────────────────────────────────────────────────────────
    marketpulse_mode: str = Field(
        default="public",
        description="Operating mode: public | premium | professional",
    )
    enabled_providers: str = Field(
        default="yfinance,fred,cboe,rss,mock",
        description="Comma-separated list of active providers",
    )
    log_level: str = Field(
        default="INFO",
        description="Python logging level",
    )

    # ── Paths ─────────────────────────────────────────────────────────────
    data_dir: str = Field(
        default="./data",
        description="Root directory for all data files",
    )
    duckdb_path: str = Field(
        default="./data/marketpulse.duckdb",
        description="Path to DuckDB analytical database",
    )
    cache_path: str = Field(
        default="./data/cache.sqlite",
        description="Path to SQLite cache database",
    )
    exports_dir: str = Field(
        default="./data/exports",
        description="Directory for exported data files",
    )
    static_payloads_dir: str = Field(
        default="./data/static_site_payloads",
        description="Directory for static site JSON payloads",
    )

    # ── API Keys ──────────────────────────────────────────────────────────
    fmp_api_key: Optional[str] = Field(
        default=None,
        description="Financial Modeling Prep API key",
    )
    fred_api_key: Optional[str] = Field(
        default=None,
        description="FRED (Federal Reserve) API key",
    )
    newsapi_key: Optional[str] = Field(
        default=None,
        description="NewsAPI.org API key",
    )
    bloomberg_mcp_path: Optional[str] = Field(
        default=None,
        description="Path to Bloomberg MCP bridge",
    )
    morningstar_mcp_path: Optional[str] = Field(
        default=None,
        description="Path to Morningstar MCP bridge",
    )

    # ── Schedule ──────────────────────────────────────────────────────────
    daily_update_time: str = Field(
        default="16:30",
        description="UTC time for daily update job (HH:MM)",
    )
    intraday_refresh_minutes: int = Field(
        default=15,
        ge=1,
        description="Minutes between intraday refreshes",
    )
    cache_ttl_minutes: int = Field(
        default=5,
        ge=1,
        description="Default cache TTL in minutes",
    )

    # ── Features ──────────────────────────────────────────────────────────
    enable_narrative: bool = Field(
        default=True,
        description="Enable narrative sentiment scoring",
    )
    enable_positioning: bool = Field(
        default=True,
        description="Enable positioning & flows scoring",
    )
    enable_nlp_llm: bool = Field(
        default=False,
        description="Enable LLM-based NLP summarization",
    )
    enable_backtest: bool = Field(
        default=True,
        description="Enable backtesting endpoints",
    )
    enable_admin_endpoints: bool = Field(
        default=True,
        description="Enable admin API endpoints",
    )

    # ── Scoring ───────────────────────────────────────────────────────────
    normalization_method: str = Field(
        default="rolling_percentile",
        description="Normalization: rolling_percentile | min_max | z_score",
    )
    rolling_window_days: int = Field(
        default=1260,
        ge=30,
        description="Days of history for rolling normalizations (1260 = 5 years)",
    )
    classic_weight: float = Field(
        default=0.40,
        ge=0.0,
        le=1.0,
        description="Weight of Classic index in composite",
    )
    narrative_weight: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Weight of Narrative index in composite",
    )
    positioning_weight: float = Field(
        default=0.30,
        ge=0.0,
        le=1.0,
        description="Weight of Positioning index in composite",
    )

    # ── Derived properties ────────────────────────────────────────────────

    @property
    def enabled_providers_list(self) -> List[str]:
        """Return enabled_providers as a list of trimmed strings."""
        return [p.strip() for p in self.enabled_providers.split(",") if p.strip()]

    @property
    def composite_weights(self) -> dict[str, float]:
        """Return the three composite index weights as a dictionary."""
        return {
            "classic": self.classic_weight,
            "narrative": self.narrative_weight,
            "positioning": self.positioning_weight,
        }

    @property
    def is_public_mode(self) -> bool:
        """True when running in public (free data only) mode."""
        return self.marketpulse_mode == "public"

    @property
    def is_premium_mode(self) -> bool:
        """True when running in premium (paid APIs) mode."""
        return self.marketpulse_mode in ("premium", "professional")

    @property
    def is_professional_mode(self) -> bool:
        """True when running in professional (institutional) mode."""
        return self.marketpulse_mode == "professional"

    def ensure_directories(self) -> None:
        """Create all configured data directories if they do not exist."""
        for path_attr in (
            "data_dir",
            "exports_dir",
            "static_payloads_dir",
        ):
            path = Path(getattr(self, path_attr))
            path.mkdir(parents=True, exist_ok=True)


# Global settings singleton
settings = Settings()
