"""Safe haven demand indicator — equity vs safe haven relative performance."""
from typing import Optional, List
from backend.domain.indicator import IndicatorResult


class SafeHavenIndicator:
    """Calculates safe haven demand (inverted — strong safe havens = fear = low score).

    Measures relative performance of equities vs safe haven basket
    (TLT treasuries, GLD gold, DXY dollar index).
    """

    def __init__(self):
        self.name = "safe_haven"
        self.description = "Equity vs safe haven relative return (inverted)"
        self.lookback_days = 20

    async def calculate(
        self,
        equity_returns: Optional[List[float]] = None,
        safe_haven_returns: Optional[List[float]] = None,
    ) -> IndicatorResult:
        """Calculate safe haven demand score."""
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="percent",
            available=False,
            direction="neutral",
            description="Safe haven demand data not yet available",
            data_source="yfinance",
            invert=True,
        )

    def calculate_sync(
        self,
        equity_prices: List[float],
        safe_haven_prices: List[float],
    ) -> Optional[float]:
        """Synchronous calculation from equity and safe haven price series.

        Args:
            equity_prices: Equity index prices, oldest first
            safe_haven_prices: Safe haven basket prices, oldest first

        Returns:
            0-100 score where 0 = flight to safety, 100 = risk seeking
        """
        if len(equity_prices) < self.lookback_days + 1 or len(safe_haven_prices) < self.lookback_days + 1:
            return None

        # Calculate returns over lookback period
        equity_ret = (equity_prices[-1] - equity_prices[-self.lookback_days - 1]) / equity_prices[-self.lookback_days - 1]
        haven_ret = (safe_haven_prices[-1] - safe_haven_prices[-self.lookback_days - 1]) / safe_haven_prices[-self.lookback_days - 1]

        # Relative performance: positive = equities outperforming = risk-on
        relative = equity_ret - haven_ret

        # Map to 0-100 (typical range: -0.15 to +0.15)
        score = (relative + 0.15) / 0.30 * 100
        return max(0.0, min(100.0, score))
