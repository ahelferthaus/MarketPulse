"""
Westwood MarketPulse — Scoring Engine

This package implements the complete scoring layer for MarketPulse:

- MarketPulseClassic: Market-data-driven sentiment (7 components)
- MarketPulseNarrative: NLP/news sentiment (6 dimensions)
- MarketPulsePositioning: Trading & positioning flows (10 components)
- MarketPulseComposite: Blended headline index with confidence weighting
- ConfidenceScorer: Data quality and confidence calculation
- ExplanationEngine: Plain-English explanation generation
- BacktestEngine: Historical regime performance analysis

Usage:
    from backend.scoring import (
        MarketPulseClassic,
        MarketPulseNarrative,
        MarketPulsePositioning,
        MarketPulseComposite,
        ConfidenceScorer,
        ExplanationEngine,
        BacktestEngine,
    )
"""
from backend.scoring.marketpulse_classic import MarketPulseClassic
from backend.scoring.marketpulse_narrative import MarketPulseNarrative
from backend.scoring.marketpulse_positioning import MarketPulsePositioning
from backend.scoring.marketpulse_composite import MarketPulseComposite
from backend.scoring.confidence import ConfidenceScorer
from backend.scoring.explanation import ExplanationEngine
from backend.scoring.backtest import BacktestEngine

__all__ = [
    "MarketPulseClassic",
    "MarketPulseNarrative",
    "MarketPulsePositioning",
    "MarketPulseComposite",
    "ConfidenceScorer",
    "ExplanationEngine",
    "BacktestEngine",
]
