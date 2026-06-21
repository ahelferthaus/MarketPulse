"""Price strength indicator — new highs vs new lows ratio."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class HighsLowsIndicator:
    """Calculates price strength as new highs / (new highs + new lows)."""

    def __init__(self):
        self.name = "price_strength"
        self.description = "New highs relative to new highs plus new lows"
        self.window_days = 52

    async def calculate(
        self,
        breadth_data: Optional[object] = None,
    ) -> IndicatorResult:
        """Calculate price strength from market breadth data."""
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="ratio",
            available=False,
            direction="neutral",
            description="Price strength data not yet available",
            data_source="breadth_provider",
            invert=False,
        )

    def calculate_sync(
        self,
        new_highs: List[float],
        new_lows: List[float],
    ) -> Optional[float]:
        """Synchronous calculation from highs/lows series.

        Args:
            new_highs: Count of new highs per period
            new_lows: Count of new lows per period

        Returns:
            0-100 score where 100 = all highs, 0 = all lows
        """
        if not new_highs or not new_lows or len(new_highs) != len(new_lows):
            return None

        totals = [h + l for h, l in zip(new_highs, new_lows) if h + l > 0]
        if not totals:
            return 50.0

        recent_highs = sum(new_highs[-self.window_days:])
        recent_lows = sum(new_lows[-self.window_days:])
        recent_total = recent_highs + recent_lows

        if recent_total == 0:
            return 50.0

        ratio = recent_highs / recent_total
        return max(0.0, min(100.0, ratio * 100))
