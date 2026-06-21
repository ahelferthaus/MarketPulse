"""Market momentum indicator — price vs 125-day moving average."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class MomentumIndicator:
    """Calculates market momentum as rolling percentile of price vs 125d MA."""

    def __init__(self):
        self.name = "momentum"
        self.description = "Price relative to 125-day moving average"
        self.window_days = 125

    async def calculate(
        self,
        price_history: Optional[object] = None,
        history_days: int = 252,
    ) -> IndicatorResult:
        """Calculate momentum score from price history.

        Args:
            price_history: DataFrame with 'close' column or None
            history_days: Lookback window for normalization

        Returns:
            IndicatorResult with normalized 0-100 score
        """
        # Implementation will compute: current_price / MA125 -> rolling percentile
        # For now, return unavailable stub
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="ratio",
            available=False,
            direction="neutral",
            description="Momentum data not yet available",
            data_source="yfinance",
            invert=False,
        )

    def calculate_sync(self, price_series: List[float]) -> Optional[float]:
        """Synchronous calculation from a price series (for backtesting).

        Args:
            price_series: List of closing prices, oldest first

        Returns:
            Normalized 0-100 score or None if insufficient data
        """
        if len(price_series) < self.window_days + 10:
            return None

        # Compute 125-day MA and ratio
        ma125 = sum(price_series[-self.window_days:]) / self.window_days
        current_price = price_series[-1]
        ratio = current_price / ma125 if ma125 > 0 else 1.0

        # Compute rolling percentile of this ratio over history
        lookback = price_series[:-1]
        ratios = []
        for i in range(self.window_days, len(lookback)):
            window = lookback[i - self.window_days:i]
            ma = sum(window) / len(window)
            if ma > 0:
                ratios.append(lookback[i] / ma)

        if not ratios:
            return 50.0

        # Percentile of current ratio
        below = sum(1 for r in ratios if r < ratio)
        percentile = (below / len(ratios)) * 100
        return max(0.0, min(100.0, percentile))
