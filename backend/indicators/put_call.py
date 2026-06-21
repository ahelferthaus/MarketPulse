"""Put/call ratio indicator — inverted (high put/call = bearish = low score)."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class PutCallIndicator:
    """Calculates put/call ratio score (inverted — high P/C is bearish)."""

    def __init__(self):
        self.name = "put_call"
        self.description = "CBOE total put/call ratio (inverted)"
        self.normal_window = 252

    async def calculate(
        self,
        options_data: Optional[object] = None,
    ) -> IndicatorResult:
        """Calculate put/call score from options data."""
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="ratio",
            available=False,
            direction="neutral",
            description="Put/call ratio data not yet available",
            data_source="CBOE",
            invert=True,
        )

    def calculate_sync(self, put_call_series: List[float]) -> Optional[float]:
        """Synchronous calculation from put/call ratio series.

        High put/call ratio = fear = low score (inverted).

        Args:
            put_call_series: List of put/call ratios, oldest first

        Returns:
            0-100 score where 0 = extreme fear, 100 = extreme complacency
        """
        if not put_call_series or len(put_call_series) < 20:
            return None

        current = put_call_series[-1]
        history = put_call_series[:-1]

        if not history:
            return 50.0

        # Percentile (inverted — high P/C = low percentile = low score)
        above = sum(1 for x in history if x > current)
        percentile = (above / len(history)) * 100
        return max(0.0, min(100.0, percentile))
