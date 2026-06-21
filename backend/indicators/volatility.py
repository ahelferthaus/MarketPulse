"""Volatility/VIX indicator — inverted (high VIX = fear = low score)."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class VolatilityIndicator:
    """Calculates VIX-based score (inverted — high VIX is bearish)."""

    def __init__(self):
        self.name = "volatility"
        self.description = "VIX level (inverted)"
        self.normal_window = 252

    async def calculate(
        self,
        vix_history: Optional[object] = None,
    ) -> IndicatorResult:
        """Calculate volatility score from VIX data."""
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="index",
            available=False,
            direction="neutral",
            description="VIX data not yet available",
            data_source="yfinance",
            invert=True,
        )

    def calculate_sync(self, vix_series: List[float]) -> Optional[float]:
        """Synchronous calculation from VIX series.

        High VIX = fear = low score (inverted).

        Args:
            vix_series: List of VIX values, oldest first

        Returns:
            0-100 score where 0 = extreme fear, 100 = extreme complacency
        """
        if not vix_series or len(vix_series) < 20:
            return None

        current = vix_series[-1]
        history = vix_series[:-1]

        if not history:
            return 50.0

        # Inverted percentile — high VIX = low score
        above = sum(1 for x in history if x > current)
        percentile = (above / len(history)) * 100
        return max(0.0, min(100.0, percentile))
