"""Credit spreads indicator — inverted (wide spreads = fear = low score)."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class CreditSpreadsIndicator:
    """Calculates credit spread score (inverted — wide spreads are bearish)."""

    def __init__(self):
        self.name = "credit_spreads"
        self.description = "High-yield option-adjusted spread (inverted)"
        self.normal_window = 252

    async def calculate(
        self,
        credit_data: Optional[object] = None,
    ) -> IndicatorResult:
        """Calculate credit spread score from FRED/credit data."""
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="bps",
            available=False,
            direction="neutral",
            description="Credit spread data not yet available",
            data_source="FRED",
            invert=True,
        )

    def calculate_sync(self, spread_series: List[float]) -> Optional[float]:
        """Synchronous calculation from credit spread series.

        Wide spreads = fear = low score (inverted).

        Args:
            spread_series: List of OAS spreads in bps, oldest first

        Returns:
            0-100 score where 0 = extreme fear, 100 = complacency
        """
        if not spread_series or len(spread_series) < 20:
            return None

        current = spread_series[-1]
        history = spread_series[:-1]

        if not history:
            return 50.0

        # Inverted percentile — wide spreads = low score
        above = sum(1 for x in history if x > current)
        percentile = (above / len(history)) * 100
        return max(0.0, min(100.0, percentile))
