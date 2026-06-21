"""Sentiment snapshot models for Westwood MarketPulse.

Defines narrative sentiment snapshots that aggregate article and social post
scores into the six emotion dimensions used by the Narrative index.
"""

from __future__ import annotations

from datetime import datetime
from typing import List

from pydantic import BaseModel, ConfigDict, Field


class NarrativeSnapshot(BaseModel):
    """Aggregated narrative sentiment snapshot for a market.

    Combines scores from all ingested articles and social posts into
    the six emotion dimensions (panic, caution, uncertainty, optimism,
    complacency, euphoria) that feed into the MarketPulse Narrative index.

    Attributes:
        timestamp: Snapshot timestamp (UTC).
        market_id: Target market identifier.
        panic_score: Panic emotion intensity (0-100).
        caution_score: Caution emotion intensity (0-100).
        uncertainty_score: Uncertainty emotion intensity (0-100).
        optimism_score: Optimism emotion intensity (0-100).
        complacency_score: Complacency emotion intensity (0-100).
        euphoria_score: Euphoria emotion intensity (0-100).
        article_count: Number of articles/posts in the aggregation window.
        top_phrases: Most frequently occurring phrases driving sentiment.
        overall_narrative_score: Aggregated narrative index value (0-100).
    """

    model_config = ConfigDict(frozen=False)

    timestamp: datetime = Field(..., description="Snapshot timestamp (UTC)")
    market_id: str = Field(..., description="Market identifier, e.g. 'sp500'")
    panic_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Panic emotion intensity (0-100)",
    )
    caution_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Caution emotion intensity (0-100)",
    )
    uncertainty_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Uncertainty emotion intensity (0-100)",
    )
    optimism_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Optimism emotion intensity (0-100)",
    )
    complacency_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Complacency emotion intensity (0-100)",
    )
    euphoria_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Euphoria emotion intensity (0-100)",
    )
    article_count: int = Field(
        ...,
        ge=0,
        description="Number of articles/posts in aggregation window",
    )
    top_phrases: List[str] = Field(
        default_factory=list,
        description="Most frequent phrases driving sentiment",
    )
    overall_narrative_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Aggregated narrative index value (0-100)",
    )
