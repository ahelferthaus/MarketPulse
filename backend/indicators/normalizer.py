"""
Normalization methods for raw indicator values to 0-100 scores.

Implements three normalization strategies:
- rolling_percentile: Percentile rank within a rolling window (default)
- min_max: Min-max scaling over a rolling window
- z_score: Z-score normalization, approximately scaled to 0-100

All methods strictly use historical data only (no look-ahead bias).
Uses a 5-year (1260 trading days) rolling window by default for
statistical stability balanced with responsiveness to regime changes.
"""
import math
from typing import Dict, Literal, Optional

import numpy as np
import pandas as pd


# Market-specific calibration bounds for momentum normalization.
# Keys are market_id values (e.g., "sp500", "nasdaq100").
# Values are the ±percentage bounds used for momentum normalization.
MARKET_MOMENTUM_BOUNDS: Dict[str, float] = {
    "sp500": 0.15,       # ±15% — standard large-cap
    "nasdaq100": 0.20,   # ±20% — higher inherent volatility
    "russell2000": 0.18, # ±18% — liquidity filtering
    "dow": 0.15,         # ±15% — blue-chip stability
    "msci_em": 0.25,     # ±25% — emerging markets currency adjustment
}


class Normalizer:
    """Converts raw indicator values to normalized 0-100 scores.

    Uses a 5-year (1260 trading days) rolling window by default to balance
    statistical stability with responsiveness to regime changes. Supports
    market-specific calibration bounds for momentum and other indicators.
    """

    # Default rolling window: 5 years of trading days
    DEFAULT_WINDOW: int = 1260

    def rolling_percentile(
        self,
        current_value: float,
        history: pd.Series,
        window: int = 1260,
        invert: bool = False,
    ) -> float:
        """
        Calculate percentile rank of current value within rolling window.

        Formula:
            percentile = (# of historical values < current) / total * 100
            if invert: score = 100 - percentile
            else:      score = percentile

        Args:
            current_value: The raw value to normalize.
            history: Series of past raw values (strictly before current).
            window: Lookback window size (default 1260 trading days ~ 5 years).
            invert: If True, flip so high raw values → low scores (for fear
                indicators like put/call ratio, VIX, credit spreads).

        Returns:
            Normalized score in [0, 100].

        Edge cases:
            - Empty history → returns 50.0 (neutral)
            - All identical values → returns 50.0
            - NaN in history → dropped before calculation
            - NaN current_value → returns NaN
        """
        if math.isnan(current_value):
            return float("nan")

        # Use only the most recent `window` observations, drop NaNs
        hist = history.dropna().tail(window)

        if hist.empty:
            return 50.0

        # Count how many historical values are strictly less than current
        below = (hist < current_value).sum()
        equal = (hist == current_value).sum()
        n = len(hist)

        if n == 0:
            return 50.0

        # Use midpoint method for percentile (below + 0.5 * equal) / n * 100
        if equal > 0 and n > 1:
            percentile = (below + 0.5 * equal) / n * 100.0
        else:
            percentile = below / n * 100.0

        # Clamp to [0, 100]
        percentile = max(0.0, min(100.0, percentile))

        if invert:
            return 100.0 - percentile
        return percentile

    def min_max_normalize(
        self,
        current_value: float,
        history: pd.Series,
        window: int = 1260,
        invert: bool = False,
    ) -> float:
        """
        Min-max normalization over a rolling window.

        Formula:
            score = (current - min(history)) / (max(history) - min(history)) * 100
            if invert: score = 100 - score

        Args:
            current_value: The raw value to normalize.
            history: Series of past raw values.
            window: Lookback window size.
            invert: If True, flip the score.

        Returns:
            Normalized score in [0, 100].

        Edge cases:
            - Empty history or all same → returns 50.0
            - NaN current_value → returns NaN
        """
        if math.isnan(current_value):
            return float("nan")

        hist = history.dropna().tail(window)

        if hist.empty:
            return 50.0

        hist_min = hist.min()
        hist_max = hist.max()

        if hist_max == hist_min:
            return 50.0

        score = (current_value - hist_min) / (hist_max - hist_min) * 100.0
        score = max(0.0, min(100.0, score))

        if invert:
            return 100.0 - score
        return score

    def z_score_normalize(
        self,
        current_value: float,
        history: pd.Series,
        window: int = 1260,
        invert: bool = False,
    ) -> float:
        """
        Z-score normalization, scaled to approximately 0-100 range.

        Formula:
            z = (current - mean(history)) / std(history)
            score = 50 + z * 25   # maps z=-2 → 0, z=0 → 50, z=+2 → 100
            if invert: score = 100 - score

        Args:
            current_value: The raw value to normalize.
            history: Series of past raw values.
            window: Lookback window size.
            invert: If True, flip the score.

        Returns:
            Normalized score (may slightly exceed [0, 100] for extreme z,
            clamped to [0, 100]).

        Edge cases:
            - Empty history or std=0 → returns 50.0
            - NaN current_value → returns NaN
        """
        if math.isnan(current_value):
            return float("nan")

        hist = history.dropna().tail(window)

        if hist.empty or hist.std() == 0 or len(hist) < 2:
            return 50.0

        mean = hist.mean()
        std = hist.std()

        z = (current_value - mean) / std
        score = 50.0 + z * 25.0

        # Clamp to valid range
        score = max(0.0, min(100.0, score))

        if invert:
            return 100.0 - score
        return score

    def normalize(
        self,
        current_value: float,
        history: pd.Series,
        method: Literal["rolling_percentile", "min_max", "z_score"] = "rolling_percentile",
        window: int = 1260,
        invert: bool = False,
    ) -> float:
        """
        Dispatch to the appropriate normalization method.

        Args:
            current_value: The raw value to normalize.
            history: Series of past raw values (strictly historical).
            method: Normalization strategy to use.
            window: Lookback window size.
            invert: If True, flip so high raw → low score.

        Returns:
            Normalized score in [0, 100] (or NaN if input is NaN).
        """
        if method == "rolling_percentile":
            return self.rolling_percentile(current_value, history, window, invert)
        elif method == "min_max":
            return self.min_max_normalize(current_value, history, window, invert)
        elif method == "z_score":
            return self.z_score_normalize(current_value, history, window, invert)
        else:
            raise ValueError(f"Unknown normalization method: {method}")

    def rolling_percentile_market_calibrated(
        self,
        current_value: float,
        history: pd.Series,
        market_id: str,
        invert: bool = False,
    ) -> float:
        """Calculate percentile rank with market-specific calibration bounds.

        Uses market-specific momentum bounds to calibrate the normalization
        window and sensitivity. Falls back to default bounds if the market
        is not explicitly configured.

        Args:
            current_value: The raw value to normalize.
            history: Series of past raw values (strictly historical).
            market_id: Market identifier (e.g., 'sp500', 'nasdaq100').
            invert: If True, flip so high raw → low score.

        Returns:
            Normalized score in [0, 100].
        """
        bounds = MARKET_MOMENTUM_BOUNDS.get(market_id, 0.15)
        # Adjust effective window based on market volatility regime:
        # higher-volatility markets benefit from slightly longer windows
        # for statistical stability.
        if bounds >= 0.20:
            effective_window = int(self.DEFAULT_WINDOW * 1.1)
        else:
            effective_window = self.DEFAULT_WINDOW

        return self.rolling_percentile(
            current_value, history, window=effective_window, invert=invert
        )
