"""
MarketPulse Indicator Calculators

All indicator modules for computing normalized 0-100 component scores:
    - MomentumIndicator: Benchmark vs 125-day moving average
    - HighsLowsIndicator: New highs vs new lows ratio
    - BreadthIndicator: Advancing/declining volume ratio
    - PutCallIndicator: CBOE put/call ratio (inverted)
    - VolatilityIndicator: VIX level (inverted)
    - CreditSpreadsIndicator: High-yield credit spreads (inverted)
    - SafeHavenIndicator: Equity vs safe-haven basket returns
    - FlowsPositioningIndicator: Composite positioning & flows
    - NarrativeSentimentIndicator: 6-dimension NLP sentiment aggregation

Also exports:
    - Normalizer: Rolling percentile, min-max, z-score normalization
    - IndicatorResult: Dataclass for all indicator outputs
    - Article: Dataclass for scored news articles
"""

# Domain
from backend.domain.indicator import IndicatorResult

# Normalization
from backend.indicators.normalizer import Normalizer

# Individual indicators
from backend.indicators.momentum import MomentumIndicator
from backend.indicators.highs_lows import HighsLowsIndicator
from backend.indicators.breadth import BreadthIndicator
from backend.indicators.put_call import PutCallIndicator
from backend.indicators.volatility import VolatilityIndicator
from backend.indicators.credit_spreads import CreditSpreadsIndicator
from backend.indicators.safe_haven import SafeHavenIndicator
from backend.indicators.flows_positioning import FlowsPositioningIndicator
from backend.indicators.narrative_sentiment import NarrativeSentimentIndicator
from backend.domain.article import Article

__all__ = [
    # Domain
    "IndicatorResult",
    # Normalization
    "Normalizer",
    # Classic indicators
    "MomentumIndicator",
    "HighsLowsIndicator",
    "BreadthIndicator",
    "PutCallIndicator",
    "VolatilityIndicator",
    "CreditSpreadsIndicator",
    "SafeHavenIndicator",
    # Composite / Narrative
    "FlowsPositioningIndicator",
    "NarrativeSentimentIndicator",
    "Article",
]
