"""NLP-based narrative sentiment indicator."""
from typing import Optional, List, Dict
from backend.domain.indicator import IndicatorResult


class NarrativeSentimentIndicator:
    """Calculates narrative sentiment across 6 emotional dimensions.

    Dimensions (bearish → bullish):
    - Panic, Caution, Uncertainty (lower score)
    - Optimism, Complacency, Euphoria (raise score)
    """

    # Dimension weights for composite mapping
    DIMENSION_WEIGHTS = {
        "panic": -1.0,
        "caution": -0.5,
        "uncertainty": -0.3,
        "optimism": 0.8,
        "complacency": 0.5,
        "euphoria": 1.0,
    }

    def __init__(self):
        self.name = "narrative_sentiment"
        self.description = "NLP sentiment across 6 emotional dimensions"

    async def calculate(
        self,
        articles: Optional[List[Dict]] = None,
        nlp_pipeline: Optional[object] = None,
    ) -> IndicatorResult:
        """Calculate narrative sentiment from news articles.

        Args:
            articles: List of article dicts with 'text', 'title', etc.
            nlp_pipeline: NLP processing pipeline

        Returns:
            IndicatorResult with 0-100 sentiment score
        """
        return IndicatorResult(
            name=self.name,
            score=None,
            raw_value=None,
            raw_unit="composite",
            available=False,
            direction="neutral",
            description="Narrative sentiment data not yet available",
            data_source="RSS/news_providers",
            invert=False,
        )

    def calculate_sync(
        self,
        dimension_scores: Dict[str, float],
    ) -> Optional[float]:
        """Synchronous calculation from dimension scores.

        Args:
            dimension_scores: Dict mapping dimension name to 0-100 score
                (0 = absent, 100 = extreme presence)

        Returns:
            0-100 composite sentiment score
        """
        if not dimension_scores:
            return None

        # Calculate weighted sum
        weighted_sum = 0.0
        total_weight = 0.0

        for dim, weight in self.DIMENSION_WEIGHTS.items():
            if dim in dimension_scores:
                score = dimension_scores[dim] / 100.0  # Normalize to 0-1
                # Negative weights: high score → subtract
                # Positive weights: high score → add
                if weight < 0:
                    weighted_sum += weight * score
                else:
                    weighted_sum += weight * score
                total_weight += abs(weight)

        if total_weight == 0:
            return 50.0

        # Normalize to 0-100
        # Max possible negative: -1.8 → 0, max positive: +2.3 → 100
        normalized = (weighted_sum + 1.8) / (2.3 + 1.8) * 100
        return max(0.0, min(100.0, normalized))
