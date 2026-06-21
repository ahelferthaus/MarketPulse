"""
Indicator result model used by all indicator calculators and scoring engines.
"""
from datetime import datetime
from typing import Optional, Dict, Any

from pydantic import BaseModel, Field


class IndicatorResult(BaseModel):
    """Result from a single indicator calculation.

    Each indicator (momentum, put/call, etc.) produces an IndicatorResult
    that is consumed by the scoring engines. The scoring engine combines
    multiple IndicatorResults into a composite score.
    """
    name: str = Field(..., description="Indicator/component name")
    score: Optional[float] = Field(None, ge=0, le=100, description="Normalized score 0-100, or None if unavailable")
    raw_value: Optional[float] = Field(None, description="Raw unnormalized value")
    raw_unit: str = Field("", description="Unit of raw value, e.g. 'ratio', 'index', 'bps'")
    weight: float = Field(1.0, description="Intended weight in composite (before redistribution)")
    available: bool = Field(True, description="Whether data was available for this indicator")
    direction: str = Field("neutral", description="'bullish', 'bearish', or 'neutral'")
    description: str = Field("", description="Human-readable description of this reading")
    data_source: str = Field("", description="Source provider name")
    timestamp: Optional[datetime] = None
    invert: bool = Field(False, description="Whether this indicator is inverted (higher raw = lower score)")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict."""
        return {
            "name": self.name,
            "score": round(self.score, 2) if self.score is not None else None,
            "raw_value": self.raw_value,
            "raw_unit": self.raw_unit,
            "weight": self.weight,
            "available": self.available,
            "direction": self.direction,
            "description": self.description,
            "data_source": self.data_source,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "invert": self.invert,
        }

    @property
    def effective_score(self) -> Optional[float]:
        """Return the effective score for composite calculation.

        For inverted indicators, score is already normalized so that
        higher raw values map to lower scores (bearish). The score
        field should already reflect this inversion.
        """
        return self.score if self.available else None
