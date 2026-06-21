"""Regime history models for Westwood MarketPulse.

Defines regime periods with forward return statistics used for backtesting
and regime-based performance analysis.
"""

from __future__ import annotations

from datetime import date
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class RegimePeriod(BaseModel):
    """A contiguous regime period for a market with forward returns.

    Used to track historical regime transitions and compute average
    forward returns for backtesting and regime analysis.

    Attributes:
        market_id: Market identifier (e.g., 'sp500').
        regime: Regime code (e.g., 'mp1_capitulation').
        start_date: First day of the regime period.
        end_date: Last day of the regime period (None if ongoing).
        avg_forward_1m: Average 1-month forward return (%).
        avg_forward_3m: Average 3-month forward return (%).
        avg_forward_6m: Average 6-month forward return (%).
        avg_forward_12m: Average 12-month forward return (%).
    """

    model_config = ConfigDict(frozen=False)

    market_id: str = Field(..., description="Market identifier, e.g. 'sp500'")
    regime: str = Field(..., description="Regime code, e.g. 'mp1_capitulation'")
    start_date: date = Field(..., description="First day of the regime period")
    end_date: Optional[date] = Field(
        default=None,
        description="Last day of the regime period (None if ongoing)",
    )
    avg_forward_1m: Optional[float] = Field(
        default=None,
        description="Average 1-month forward return (%)",
    )
    avg_forward_3m: Optional[float] = Field(
        default=None,
        description="Average 3-month forward return (%)",
    )
    avg_forward_6m: Optional[float] = Field(
        default=None,
        description="Average 6-month forward return (%)",
    )
    avg_forward_12m: Optional[float] = Field(
        default=None,
        description="Average 12-month forward return (%)",
    )
