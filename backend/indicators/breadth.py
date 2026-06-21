"""Price breadth indicator — advancing vs declining issues."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class BreadthIndicator:
    """Calculates market breadth as percent of issues above moving average."""

    def __init__(self):
        self.name = "breadth"
        self.description = "Percentage of stocks above 50-day moving average"
        self.window_days = 50

    async def calculate(
        self,
        breadth_data: Optional[object] = None,
    ) -> IndicatorResult:
        """Calculate breadth from advancing/declining data."""
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="percent",
            available=False,
            direction="neutral",
            description="Breadth data not yet available",
            data_source="breadth_provider",
            invert=False,
        )

    def calculate_sync(
        self,
        advancing: List[float],
        declining: List[float],
    ) -> Optional[float]:
        """Synchronous calculation from advancing/declining counts.

        Returns 0-100 score based on recent breadth trend.
        """
        if not advancing or not declining or len(advancing) != len(declining):
            return None

        recent_adv = sum(advancing[-20:])
        recent_dec = sum(declining[-20:])
        total = recent_adv + recent_dec

        if total == 0:
            return 50.0

        ratio = recent_adv / total
        return max(0.0, min(100.0, ratio * 100))
