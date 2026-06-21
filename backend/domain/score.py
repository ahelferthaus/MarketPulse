"""
Domain models for MarketPulse scores, regimes, drivers, and data quality.

These Pydantic models define the core data structures used throughout
the scoring engine. They are imported by all scoring modules.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class Regime(str, Enum):
    """Five-zone regime classification for MarketPulse scores.

    Empirically-derived asymmetric ranges based on historical frequency
    analysis of market conditions:
    - MP-1 (Capitulation): 0-24   (~8% historical frequency)
    - MP-2 (Defensive): 25-44    (~23% historical frequency)
    - MP-3 (Neutral): 45-55      (~38% historical frequency)
    - MP-4 (Risk-On): 56-75      (~24% historical frequency)
    - MP-5 (Euphoria): 76-100    (~7% historical frequency)

    The MP-3 band is intentionally narrow (10 points) reflecting the
    rarity of true balance in market psychology.
    """
    MP1_CAPITULATION = "mp1_capitulation"   # 0-24
    MP2_DEFENSIVE = "mp2_defensive"         # 25-44
    MP3_NEUTRAL = "mp3_neutral"             # 45-55
    MP4_RISK_ON = "mp4_risk_on"             # 56-75
    MP5_EUPHORIA = "mp5_euphoria"           # 76-100

    @classmethod
    def from_score(cls, score: float) -> "Regime":
        """Map a 0-100 score to the appropriate regime zone.

        Uses empirically-derived asymmetric ranges based on historical
        frequency analysis. Extremes are rarer than neutral conditions.

        Args:
            score: Numeric score from 0 to 100.

        Returns:
            Regime enum member corresponding to the score range.
        """
        if score <= 24:
            return cls.MP1_CAPITULATION
        elif score <= 44:
            return cls.MP2_DEFENSIVE
        elif score <= 55:
            return cls.MP3_NEUTRAL
        elif score <= 75:
            return cls.MP4_RISK_ON
        else:
            return cls.MP5_EUPHORIA


class ScoreDriver(BaseModel):
    """A single component's contribution to the overall score."""
    component: str = Field(..., description="Component name, e.g. 'momentum', 'put_call'")
    contribution: float = Field(..., ge=-20, le=20, description="Impact on composite (-20 to +20)")
    direction: str = Field(..., description="'bullish', 'bearish', or 'neutral'")
    description: str = Field(..., description="Plain English explanation of this driver's impact")


class DataQualityReport(BaseModel):
    """Report on data quality and confidence for a MarketPulse reading."""
    overall_confidence: float = Field(..., ge=0, le=100, description="Overall confidence 0-100")
    sources_used: int = Field(0, description="Number of data sources successfully used")
    sources_available: int = Field(0, description="Total number of data sources available")
    missing_components: List[str] = Field(default_factory=list)
    substituted_components: List[str] = Field(default_factory=list)
    stale_data_warnings: List[str] = Field(default_factory=list)
    data_freshness_minutes: int = Field(0, description="Age of freshest data in minutes")

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict for JSON responses."""
        return {
            "overall_confidence": self.overall_confidence,
            "sources_used": self.sources_used,
            "sources_available": self.sources_available,
            "missing_components": self.missing_components,
            "substituted_components": self.substituted_components,
            "stale_data_warnings": self.stale_data_warnings,
            "data_freshness_minutes": self.data_freshness_minutes,
        }


class MarketPulseScore(BaseModel):
    """Complete MarketPulse score snapshot for a market at a point in time."""
    timestamp: datetime
    market_id: str = Field(..., description="e.g. 'sp500', 'nasdaq100'")
    classic_score: float = Field(0.0, ge=0, le=100)
    narrative_score: float = Field(0.0, ge=0, le=100)
    positioning_score: float = Field(0.0, ge=0, le=100)
    composite_score: float = Field(0.0, ge=0, le=100)
    regime: Regime = Regime.MP3_NEUTRAL
    regime_label: str = "Neutral"
    direction: str = "stable"  # "rising", "falling", "stable"
    confidence: float = Field(100.0, ge=0, le=100)
    explanation: str = ""
    what_changed: Optional[str] = None
    drivers: List[ScoreDriver] = Field(default_factory=list)
    data_quality: DataQualityReport = Field(default_factory=lambda: DataQualityReport(overall_confidence=100.0))

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to plain dict for JSON responses."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "market_id": self.market_id,
            "classic_score": round(self.classic_score, 1),
            "narrative_score": round(self.narrative_score, 1),
            "positioning_score": round(self.positioning_score, 1),
            "composite_score": round(self.composite_score, 1),
            "regime": self.regime.value,
            "regime_label": self.regime_label,
            "direction": self.direction,
            "confidence": round(self.confidence, 1),
            "explanation": self.explanation,
            "what_changed": self.what_changed,
            "drivers": [d.model_dump() for d in self.drivers],
            "data_quality": self.data_quality.to_dict(),
        }


class SourceStatus(BaseModel):
    """Status of a single data provider."""
    provider: str
    available: bool = False
    last_successful_fetch: Optional[datetime] = None
    error_count_24h: int = 0
    avg_response_ms: Optional[int] = None
    data_freshness_minutes: Optional[int] = None
    tier: str = "public"  # "public", "premium", "professional"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "available": self.available,
            "last_successful_fetch": self.last_successful_fetch.isoformat() if self.last_successful_fetch else None,
            "error_count_24h": self.error_count_24h,
            "avg_response_ms": self.avg_response_ms,
            "data_freshness_minutes": self.data_freshness_minutes,
            "tier": self.tier,
        }
