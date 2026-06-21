"""
Backtesting Engine

Analyzes historical performance of MarketPulse regimes.

Computes:
- Regime history and transitions
- Average forward returns (1m, 3m, 6m, 12m) by regime
- Regime persistence statistics (how long regimes last)
- Transition probability matrix
- Caveats and limitations

CRITICAL: This engine prevents look-ahead bias. At each point in time,
only data available up to that point is used. No future information
is incorporated into regime classification or return calculations.

Methodology:
1. Walk forward through historical scores chronologically
2. At each point, record the regime (using only past data)
3. Calculate forward returns from that point (future is only used
   for returns, not for regime classification)
4. Aggregate returns by regime
"""
import logging
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

from backend.domain.score import MarketPulseScore, Regime
from backend.scoring.confidence import ConfidenceScorer

logger = logging.getLogger(__name__)


class BacktestEngine:
    """Analyzes historical regime performance.

    The backtest engine computes forward returns by regime to validate
    that the MarketPulse framework has predictive value. It strictly
    prevents look-ahead bias by using only historically available data.

    Usage:
        engine = BacktestEngine()
        results = engine.analyze_regime_returns(scores, price_history)
        transitions = engine.get_regime_transitions(scores)
    """

    # Forward return horizons in trading days
    HORIZONS: Dict[str, int] = {
        "1m": 21,
        "3m": 63,
        "6m": 126,
        "12m": 252,
    }

    def __init__(self):
        self.confidence_scorer = ConfidenceScorer()

    # ------------------------------------------------------------------
    # Regime returns analysis
    # ------------------------------------------------------------------

    def analyze_regime_returns(
        self,
        scores: List[MarketPulseScore],
        price_history: pd.DataFrame,
    ) -> Dict[str, Any]:
        """Calculate average forward returns by regime.

        For each regime entry point:
        1. Record the regime at that point (using only past data)
        2. Calculate 1m, 3m, 6m, 12m forward returns
        3. Average across all occurrences of each regime

        IMPORTANT: No look-ahead bias. Regime classification uses only
        data available at each point. Forward returns use future prices
        (which is the definition of forward returns) but the regime
        itself is not influenced by future data.

        Args:
            scores: Chronologically ordered list of MarketPulseScore
            price_history: DataFrame with 'close' price column and DatetimeIndex

        Returns:
            Dict with:
                - regime_returns: Dict mapping regime -> horizon -> avg return
                - regime_counts: Number of occurrences per regime
                - regime_persistence: Average days spent in each regime
                - total_observations: Total number of score points
                - caveats: List of methodology caveats
        """
        if not scores:
            return self._empty_result("No scores provided")

        if price_history.empty or "close" not in price_history.columns:
            return self._empty_result("Invalid price history")

        # Ensure scores are sorted chronologically
        sorted_scores = sorted(scores, key=lambda s: s.timestamp)

        # Ensure price history has DatetimeIndex
        if not isinstance(price_history.index, pd.DatetimeIndex):
            price_history = price_history.copy()
            price_history.index = pd.to_datetime(price_history.index)

        # Match scores to price data
        matched = self._match_scores_to_prices(sorted_scores, price_history)

        if not matched:
            return self._empty_result("Could not match scores to price data")

        # Calculate forward returns for each matched point
        returns_data: Dict[str, List[Dict]] = {r.value: [] for r in Regime}

        for score, price_idx in matched:
            regime = score.regime.value
            forward_returns = self._calculate_forward_returns(
                price_history, price_idx
            )

            returns_data[regime].append({
                "date": score.timestamp.isoformat(),
                "score": score.composite_score,
                "returns": forward_returns,
            })

        # Aggregate results
        regime_returns = self._aggregate_by_regime(returns_data)
        regime_counts = {r: len(data) for r, data in returns_data.items()}
        persistence = self._calculate_persistence(sorted_scores)

        return {
            "regime_returns": regime_returns,
            "regime_counts": regime_counts,
            "regime_persistence": persistence,
            "total_observations": len(matched),
            "horizons": list(self.HORIZONS.keys()),
            "caveats": self._get_caveats(),
        }

    # ------------------------------------------------------------------
    # Regime transitions
    # ------------------------------------------------------------------

    def get_regime_transitions(
        self,
        scores: List[MarketPulseScore],
    ) -> List[Dict]:
        """Identify regime changes and their frequency.

        Analyzes the sequence of regimes to find:
        - All regime transitions (from -> to)
        - Transition frequencies
        - Average time spent in each regime before transitioning

        Args:
            scores: Chronologically ordered list of MarketPulseScore

        Returns:
            List of transition dicts with from_regime, to_regime,
            count, and avg_days_before_transition
        """
        if not scores:
            return []

        sorted_scores = sorted(scores, key=lambda s: s.timestamp)

        # Track transitions
        transitions: Dict[Tuple[str, str], List[int]] = {}
        current_regime = sorted_scores[0].regime.value
        regime_start_idx = 0

        for i, score in enumerate(sorted_scores[1:], 1):
            new_regime = score.regime.value
            if new_regime != current_regime:
                # Record transition
                key = (current_regime, new_regime)
                days_in_regime = i - regime_start_idx

                if key not in transitions:
                    transitions[key] = []
                transitions[key].append(days_in_regime)

                current_regime = new_regime
                regime_start_idx = i

        # Build result
        result = []
        for (from_regime, to_regime), durations in sorted(transitions.items()):
            result.append({
                "from_regime": from_regime,
                "to_regime": to_regime,
                "count": len(durations),
                "avg_days_in_regime": round(sum(durations) / len(durations), 1),
                "min_days": min(durations),
                "max_days": max(durations),
            })

        return result

    def get_transition_matrix(
        self,
        scores: List[MarketPulseScore],
    ) -> pd.DataFrame:
        """Build regime transition probability matrix.

        Returns a DataFrame where cell (i, j) is the probability
        of transitioning from regime i to regime j.

        Args:
            scores: Chronologically ordered list of MarketPulseScore

        Returns:
            DataFrame with regimes as both index and columns
        """
        transitions = self.get_regime_transitions(scores)

        regimes = [r.value for r in Regime]
        matrix = pd.DataFrame(0.0, index=regimes, columns=regimes)

        # Count transitions
        from_counts: Dict[str, int] = {r: 0 for r in regimes}
        for t in transitions:
            matrix.loc[t["from_regime"], t["to_regime"]] = t["count"]
            from_counts[t["from_regime"]] += t["count"]

        # Normalize to probabilities
        for from_regime in regimes:
            total = from_counts[from_regime]
            if total > 0:
                matrix.loc[from_regime] = matrix.loc[from_regime] / total

        return matrix

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _match_scores_to_prices(
        self,
        scores: List[MarketPulseScore],
        price_history: pd.DataFrame,
    ) -> List[Tuple[MarketPulseScore, int]]:
        """Match each score to the closest price data point.

        Returns list of (score, price_index) tuples where price_index
        is the position in price_history closest to the score timestamp.

        Only matches scores that have sufficient future data for
        all forward return horizons.
        """
        matched = []
        max_horizon = max(self.HORIZONS.values())

        for score in scores:
            # Find closest price date
            score_ts = pd.Timestamp(score.timestamp)
            idx = price_history.index.get_indexer([score_ts], method="nearest")[0]

            if idx < 0 or idx >= len(price_history):
                continue

            # Check if enough future data exists
            if idx + max_horizon >= len(price_history):
                continue  # Not enough future data

            matched.append((score, idx))

        return matched

    def _calculate_forward_returns(
        self,
        price_history: pd.DataFrame,
        start_idx: int,
    ) -> Dict[str, Optional[float]]:
        """Calculate forward returns from a starting index.

        Uses only price data from start_idx onward. No look-ahead.

        Args:
            price_history: Price DataFrame with 'close' column
            start_idx: Starting index in the price history

        Returns:
            Dict mapping horizon label to return (or None if unavailable)
        """
        start_price = price_history["close"].iloc[start_idx]
        returns: Dict[str, Optional[float]] = {}

        if start_price <= 0:
            return {h: None for h in self.HORIZONS}

        for label, days in self.HORIZONS.items():
            end_idx = start_idx + days
            if end_idx >= len(price_history):
                returns[label] = None
                continue

            end_price = price_history["close"].iloc[end_idx]
            ret = (end_price - start_price) / start_price
            returns[label] = round(ret * 100, 2)  # Convert to percentage

        return returns

    def _aggregate_by_regime(
        self,
        returns_data: Dict[str, List[Dict]],
    ) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Aggregate forward returns by regime.

        For each regime and each horizon, compute:
        - mean return
        - median return
        - std deviation
        - win rate (% positive)
        - count
        """
        result: Dict[str, Dict[str, Dict[str, float]]] = {}

        for regime, entries in returns_data.items():
            result[regime] = {}

            for horizon in self.HORIZONS:
                returns = [
                    e["returns"][horizon]
                    for e in entries
                    if e["returns"].get(horizon) is not None
                ]

                if not returns:
                    result[regime][horizon] = {
                        "mean": None,
                        "median": None,
                        "std": None,
                        "win_rate": None,
                        "count": 0,
                    }
                    continue

                arr = np.array(returns)
                positive = sum(1 for r in returns if r > 0)

                result[regime][horizon] = {
                    "mean": round(float(np.mean(arr)), 2),
                    "median": round(float(np.median(arr)), 2),
                    "std": round(float(np.std(arr)), 2),
                    "win_rate": round(positive / len(returns) * 100, 1),
                    "count": len(returns),
                }

        return result

    def _calculate_persistence(
        self,
        scores: List[MarketPulseScore],
    ) -> Dict[str, float]:
        """Calculate average regime persistence in days.

        Measures how long the index typically stays in each regime
        before transitioning.
        """
        if not scores:
            return {}

        regime_durations: Dict[str, List[int]] = {}
        current_regime = scores[0].regime.value
        current_start = 0

        for i, score in enumerate(scores[1:], 1):
            if score.regime.value != current_regime:
                duration = i - current_start
                if current_regime not in regime_durations:
                    regime_durations[current_regime] = []
                regime_durations[current_regime].append(duration)
                current_regime = score.regime.value
                current_start = i

        # Handle final regime
        duration = len(scores) - current_start
        if current_regime not in regime_durations:
            regime_durations[current_regime] = []
        regime_durations[current_regime].append(duration)

        # Calculate averages
        persistence = {}
        for regime, durations in regime_durations.items():
            persistence[regime] = round(sum(durations) / len(durations), 1)

        return persistence

    def _empty_result(self, reason: str) -> Dict[str, Any]:
        """Return empty result with reason."""
        return {
            "regime_returns": {},
            "regime_counts": {},
            "regime_persistence": {},
            "total_observations": 0,
            "horizons": list(self.HORIZONS.keys()),
            "caveats": [reason] + self._get_caveats(),
        }

    def _get_caveats(self) -> List[str]:
        """Return list of methodology caveats and limitations.

        These are important disclaimers about the backtest methodology
        that should always accompany results.
        """
        return [
            "Past performance does not guarantee future results.",
            "Forward returns use point-in-time price data — no lookahead bias in regime classification.",
            "Transaction costs, slippage, and taxes are not included.",
            "Regime classifications may change retroactively as normalization windows shift.",
            "Limited historical data may reduce statistical significance for some regimes.",
            "The five-zone framework is heuristic, not derived from statistical optimization.",
            "Survivorship bias may affect long-horizon returns if constituents changed.",
            "Results assume immediate execution at observed prices — not realistic for large positions.",
        ]

    # ------------------------------------------------------------------
    # Summary report
    # ------------------------------------------------------------------

    def generate_summary_report(
        self,
        scores: List[MarketPulseScore],
        price_history: pd.DataFrame,
    ) -> str:
        """Generate a human-readable backtest summary.

        Args:
            scores: Historical scores
            price_history: Price history DataFrame

        Returns:
            Formatted text report
        """
        results = self.analyze_regime_returns(scores, price_history)
        transitions = self.get_regime_transitions(scores)

        lines = [
            "=" * 60,
            "MARKETPULSE REGIME BACKTEST REPORT",
            "=" * 60,
            "",
            f"Total observations: {results['total_observations']}",
            f"Forward horizons: {', '.join(results['horizons'])}",
            "",
            "-" * 40,
            "FORWARD RETURNS BY REGIME",
            "-" * 40,
        ]

        regime_labels = {
            "mp1_capitulation": "MP-1 Capitulation",
            "mp2_defensive": "MP-2 Defensive",
            "mp3_neutral": "MP-3 Neutral",
            "mp4_risk_on": "MP-4 Risk-On",
            "mp5_euphoria": "MP-5 Euphoria",
        }

        for regime in [r.value for r in Regime]:
            label = regime_labels.get(regime, regime)
            count = results["regime_counts"].get(regime, 0)
            lines.append(f"\n{label} (n={count}):")

            if regime not in results["regime_returns"]:
                lines.append("  No data")
                continue

            for horizon in results["horizons"]:
                data = results["regime_returns"][regime].get(horizon, {})
                if data.get("mean") is None:
                    lines.append(f"  {horizon}: insufficient data")
                    continue

                mean = data["mean"]
                win = data["win_rate"]
                count_h = data["count"]
                sign = "+" if mean >= 0 else ""
                lines.append(
                    f"  {horizon:>3}: {sign}{mean:>6.2f}%  (win: {win:.0f}%, n={count_h})"
                )

        if transitions:
            lines.extend([
                "",
                "-" * 40,
                "REGIME TRANSITIONS",
                "-" * 40,
            ])
            for t in transitions:
                from_label = regime_labels.get(t["from_regime"], t["from_regime"])
                to_label = regime_labels.get(t["to_regime"], t["to_regime"])
                lines.append(
                    f"  {from_label} -> {to_label}: "
                    f"{t['count']}x (avg {t['avg_days_in_regime']:.0f}d)"
                )

        lines.extend([
            "",
            "-" * 40,
            "CAVEATS",
            "-" * 40,
        ])
        for caveat in results["caveats"]:
            lines.append(f"  * {caveat}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)
