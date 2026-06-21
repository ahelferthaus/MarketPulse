"""
MarketPulse Composite Index

Blended headline index combining Classic, Narrative, and Positioning.

Default weights:
    Classic:     40%
    Narrative:   30%
    Positioning: 30%

Confidence-adjusted weighting:
    When an index has low confidence, its weight is reduced proportionally
    and redistributed to higher-confidence indices.

    Formula:
        adjusted_weight_i = (base_weight_i * confidence_i) / sum(base_weight_j * confidence_j)
        composite = sum(score_i * adjusted_weight_i)

This ensures that indices with poor data quality don't disproportionately
influence the headline score.
"""
import logging
from typing import Dict, Tuple

from backend.domain.score import DataQualityReport

logger = logging.getLogger(__name__)


class MarketPulseComposite:
    """Calculates the composite headline score.

    The Composite is the primary MarketPulse output — a single 0-100
    score that blends market data (Classic), media sentiment (Narrative),
    and positioning flows (Positioning) into one headline reading.

    Score interpretation (same 5-zone framework):
        0-20: Capitulation
        20-40: Defensive
        40-60: Neutral
        60-80: Risk-On
        80-100: Euphoria
    """

    def __init__(
        self,
        classic_weight: float = 0.40,
        narrative_weight: float = 0.30,
        positioning_weight: float = 0.30,
    ):
        """Initialize composite with base weights.

        Args:
            classic_weight: Weight for Classic index (default 0.40)
            narrative_weight: Weight for Narrative index (default 0.30)
            positioning_weight: Weight for Positioning index (default 0.30)

        Raises:
            ValueError: If weights don't sum to 1.0
        """
        weight_sum = classic_weight + narrative_weight + positioning_weight
        if abs(weight_sum - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {weight_sum}")

        self.weights: Dict[str, float] = {
            "classic": classic_weight,
            "narrative": narrative_weight,
            "positioning": positioning_weight,
        }

    # ------------------------------------------------------------------
    # Public API (synchronous — pure math)
    # ------------------------------------------------------------------

    def calculate(
        self,
        classic_score: float,
        narrative_score: float,
        positioning_score: float,
        classic_confidence: float = 100.0,
        narrative_confidence: float = 100.0,
        positioning_confidence: float = 100.0,
    ) -> Tuple[float, DataQualityReport]:
        """Calculate composite with confidence-adjusted weighting.

        Algorithm:
        1. Multiply each base weight by its confidence level
        2. Normalize adjusted weights to sum to 1.0
        3. Composite = weighted sum of scores

        This reduces the influence of low-confidence indices and
        increases the weight of high-confidence ones.

        Args:
            classic_score: Classic index score (0-100)
            narrative_score: Narrative index score (0-100)
            positioning_score: Positioning index score (0-100)
            classic_confidence: Classic data confidence (0-100)
            narrative_confidence: Narrative data confidence (0-100)
            positioning_confidence: Positioning data confidence (0-100)

        Returns:
            Tuple of (composite_score, data_quality_report)
        """
        # Clamp inputs
        classic_score = max(0.0, min(100.0, classic_score))
        narrative_score = max(0.0, min(100.0, narrative_score))
        positioning_score = max(0.0, min(100.0, positioning_score))
        classic_confidence = max(0.0, min(100.0, classic_confidence))
        narrative_confidence = max(0.0, min(100.0, narrative_confidence))
        positioning_confidence = max(0.0, min(100.0, positioning_confidence))

        # Step 1: Calculate confidence-adjusted weights
        adjusted_weights = self._adjust_weights_for_confidence({
            "classic": classic_confidence,
            "narrative": narrative_confidence,
            "positioning": positioning_confidence,
        })

        # Step 2: Compute weighted composite
        composite = (
            classic_score * adjusted_weights["classic"] +
            narrative_score * adjusted_weights["narrative"] +
            positioning_score * adjusted_weights["positioning"]
        )

        composite = max(0.0, min(100.0, composite))

        # Step 3: Build quality report
        overall_confidence = (
            classic_confidence * self.weights["classic"] +
            narrative_confidence * self.weights["narrative"] +
            positioning_confidence * self.weights["positioning"]
        )

        missing_indices = []
        if classic_confidence < 10:
            missing_indices.append("classic")
        if narrative_confidence < 10:
            missing_indices.append("narrative")
        if positioning_confidence < 10:
            missing_indices.append("positioning")

        quality = DataQualityReport(
            overall_confidence=overall_confidence,
            sources_used=3 - len(missing_indices),
            sources_available=3,
            missing_components=missing_indices,
            substituted_components=[],
            stale_data_warnings=[],
            data_freshness_minutes=0,
        )

        logger.info(
            "Composite score: %.2f (classic=%.1f@%s, narrative=%.1f@%s, positioning=%.1f@%s, "
            "weights=[%.2f, %.2f, %.2f])",
            composite,
            classic_score, f"{classic_confidence:.0f}%",
            narrative_score, f"{narrative_confidence:.0f}%",
            positioning_score, f"{positioning_confidence:.0f}%",
            adjusted_weights["classic"],
            adjusted_weights["narrative"],
            adjusted_weights["positioning"],
        )

        return composite, quality

    def calculate_from_indices(
        self,
        classic_result: Tuple[float, list, DataQualityReport],
        narrative_result: Tuple[float, list, DataQualityReport],
        positioning_result: Tuple[float, list, DataQualityReport],
    ) -> Tuple[float, DataQualityReport]:
        """Calculate composite from full index results.

        Convenience method that extracts scores and confidence from
        the full result tuples returned by each index calculator.

        Args:
            classic_result: (score, components, quality) from Classic
            narrative_result: (score, components, quality) from Narrative
            positioning_result: (score, components, quality) from Positioning

        Returns:
            Tuple of (composite_score, data_quality_report)
        """
        classic_score, _, classic_quality = classic_result
        narrative_score, _, narrative_quality = narrative_result
        positioning_score, _, positioning_quality = positioning_result

        return self.calculate(
            classic_score=classic_score,
            narrative_score=narrative_score,
            positioning_score=positioning_score,
            classic_confidence=classic_quality.overall_confidence,
            narrative_confidence=narrative_quality.overall_confidence,
            positioning_confidence=positioning_quality.overall_confidence,
        )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _adjust_weights_for_confidence(
        self,
        confidences: Dict[str, float],
    ) -> Dict[str, float]:
        """Adjust base weights by confidence levels.

        Formula:
            adjusted_i = base_weight_i * confidence_i / sum(base_weight_j * confidence_j)

        Args:
            confidences: Dict mapping index name to confidence (0-100)

        Returns:
            Dict mapping index name to adjusted weight (sums to 1.0)
        """
        raw_adjusted: Dict[str, float] = {}
        for name, base_weight in self.weights.items():
            confidence = confidences.get(name, 0.0)
            # Normalize confidence to 0-1
            raw_adjusted[name] = base_weight * (confidence / 100.0)

        total = sum(raw_adjusted.values())

        if total == 0:
            # All confidences are zero — fall back to equal weights
            n = len(self.weights)
            return {name: 1.0 / n for name in self.weights}

        # Normalize to sum to 1.0
        return {name: w / total for name, w in raw_adjusted.items()}

    @staticmethod
    def get_regime(score: float) -> str:
        """Map composite score to regime label."""
        if score <= 20:
            return "Capitulation"
        elif score <= 40:
            return "Defensive"
        elif score <= 60:
            return "Neutral"
        elif score <= 80:
            return "Risk-On"
        else:
            return "Euphoria"
