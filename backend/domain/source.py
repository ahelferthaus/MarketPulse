"""Source status domain model."""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class ProviderTier(str, Enum):
    """Data provider access tier."""
    PUBLIC = "public"
    PREMIUM = "premium"
    PROFESSIONAL = "professional"


class SourceStatus(BaseModel):
    """Health and availability status for a single data provider.

    Attributes:
        provider: Human-readable provider name (e.g. "yahoo_finance").
        available: Whether the provider returned usable data on the last attempt.
        last_successful_fetch: UTC timestamp of the last successful data retrieval.
        error_count_24h: Number of failed calls in the last 24 hours.
        avg_response_ms: Average response latency over the last 24 hours.
        data_freshness_minutes: Age of the most recent data point in minutes.
        tier: Provider tier — "public", "premium", or "professional".
    """

    provider: str
    available: bool = False
    last_successful_fetch: Optional[datetime] = None
    error_count_24h: int = 0
    avg_response_ms: Optional[int] = None
    data_freshness_minutes: Optional[int] = None
    tier: str = "public"
