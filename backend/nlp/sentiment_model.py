"""
Sentiment Model
Primary: Rule-based keyword matching with financial lexicon
Optional: FinBERT if transformers package is available

Lexicon structure:
- panic_words: ['crash', 'meltdown', 'collapse', 'crisis', 'plunge', 'free fall']
- caution_words: ['hedge', 'defensive', 'wary', 'cautious', 'protective', 'uncertain']
- uncertainty_words: ['mixed', 'unclear', 'wait and see', 'ambiguous', 'conflicting']
- optimism_words: ['growth', 'recovery', 'bullish', 'rally', 'expansion', 'upside']
- complacency_words: ['goldilocks', 'calm', 'stable', 'no worries', 'melt up']
- euphoria_words: ['bubble', 'to the moon', 'can\'t lose', 'unstoppable', 'euphoria']

Scoring per article:
- Count word occurrences in each category
- Normalize by article length
- Apply weights
- Return 6 dimension scores (0-100 each)
"""

import logging
import re
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# Stub Article class for type hints when domain model not available
class _ArticleStub:
    """Minimal article stub for standalone NLP pipeline usage."""
    def __init__(self, title: str = "", content: str = "", **kwargs):
        self.title = title
        self.content = content
        self.panic_score: float = 0.0
        self.caution_score: float = 0.0
        self.uncertainty_score: float = 0.0
        self.optimism_score: float = 0.0
        self.complacency_score: float = 0.0
        self.euphoria_score: float = 0.0
        self.sentiment_score: float = 50.0


try:
    from backend.domain.article import Article
except ImportError:
    Article = _ArticleStub  # type: ignore[misc,assignment]


class SentimentModel:
    """Rule-based financial sentiment analyzer."""

    # Dimension weights for overall sentiment calculation
    DIMENSION_WEIGHTS = {
        "panic": 1.0,
        "caution": 0.5,
        "uncertainty": 0.3,
        "optimism": 1.0,
        "complacency": 0.4,
        "euphoria": 0.5,
    }

    def __init__(self):
        self._load_lexicon()
        self.finbert_available = self._check_finbert()
        if self.finbert_available:
            logger.info("FinBERT transformers available — neural blending enabled")
        else:
            logger.info("Running in rule-based mode (transformers not installed)")

    def _load_lexicon(self) -> None:
        """Load financial sentiment lexicon."""
        self.lexicon: Dict[str, List[str]] = {
            "panic": [
                "crash", "meltdown", "collapse", "crisis", "plunge", "free fall",
                "nosedive", "tailspin", "bloodbath", "massacre", "devastation",
                "panic selling", "sell-off", "rout", "tumble", "dive", "plummet",
                "implosion", "wipeout", "carnage", "mayhem",
            ],
            "caution": [
                "hedge", "defensive", "wary", "cautious", "protective", "uncertain",
                "risk-off", "flight to safety", "de-risking", "underweight",
                "reduce exposure", "take profits", "wait", "pause", "concern",
                "warning", "risk averse", "conservative", "tread carefully",
                "headwinds", "challenging",
            ],
            "uncertainty": [
                "mixed", "unclear", "wait and see", "ambiguous", "conflicting",
                "volatile", "unpredictable", "in flux", "crosscurrents",
                "uncertainty", "unknown", "up in the air", "debated",
                "uncertain outlook", "cloudy", "murky", "jury is out",
                "tug of war", "divided",
            ],
            "optimism": [
                "growth", "recovery", "bullish", "rally", "expansion", "upside",
                "breakout", "momentum", "strong", "robust", "outperform",
                "upgrade", "beat expectations", "tailwind", "bright spot",
                "positive", "optimistic", "green shoots", "renaissance",
                "rebound", "surge", "soar", "rally", "upswing",
            ],
            "complacency": [
                "goldilocks", "calm", "stable", "no worries", "melt up",
                "easy", "smooth sailing", "risk-on", "complacent",
                "benign", "tranquil", "placid", "too quiet", "sleepy",
                "undisturbed", "carefree", "relaxed", "lulled",
            ],
            "euphoria": [
                "bubble", "to the moon", "can't lose", "unstoppable", "euphoria",
                "mania", "frenzy", "irrational exuberance", "parabolic",
                "tulip", "rocket", "skyrocket", "exponential", "insane",
                "crazy gains", "everyone's buying", "fomo", "feeding frenzy",
                "melt-up", "disconnected from fundamentals",
            ],
        }

    def _check_finbert(self) -> bool:
        """Check if transformers/FinBERT is available."""
        try:
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def _finbert_score(self, text: str) -> Dict[str, float]:
        """Get neural sentiment scores from FinBERT.

        Returns a neutral mapping if FinBERT fails or is not fully loaded.
        """
        try:
            from transformers import pipeline  # type: ignore[import-untyped]

            if not hasattr(self, "_finbert_pipe"):
                self._finbert_pipe = pipeline(
                    "sentiment-analysis",
                    model="yiyanghkust/finbert-tone",
                    tokenizer="yiyanghkust/finbert-tone",
                )

            # FinBERT returns label + score; map to our dimensions
            result = self._finbert_pipe(text[:512])  # Truncate to model max length
            label = result[0]["label"].lower()
            confidence = result[0]["score"]

            # Map FinBERT labels to our 6 dimensions
            neural: Dict[str, float] = {
                "panic": 0.0,
                "caution": 0.0,
                "uncertainty": 0.0,
                "optimism": 0.0,
                "complacency": 0.0,
                "euphoria": 0.0,
            }

            if label == "negative":
                neural["panic"] = confidence * 70
                neural["caution"] = confidence * 50
            elif label == "neutral":
                neural["uncertainty"] = confidence * 60
            elif label == "positive":
                neural["optimism"] = confidence * 70
                if confidence > 0.9:
                    neural["euphoria"] = confidence * 40

            return neural
        except Exception as exc:
            logger.warning("FinBERT scoring failed: %s", exc)
            return {dim: 50.0 for dim in self.lexicon}

    def analyze(self, text: str) -> Dict[str, float]:
        """
        Analyze text sentiment across 6 dimensions.

        Returns dict: {panic, caution, uncertainty, optimism, complacency, euphoria}
        Each value is 0-100.
        """
        if not text or not text.strip():
            return {dim: 0.0 for dim in self.lexicon}

        text_lower = text.lower()
        scores: Dict[str, float] = {}

        for dimension, words in self.lexicon.items():
            count = sum(1 for word in words if word in text_lower)
            # Normalize: cap at 100, scale by expected density
            # Using max(len(words) * 0.3, 1) as denominator means
            # ~30% of lexicon words must match to hit 100
            scores[dimension] = min(100.0, count * 100.0 / max(len(words) * 0.3, 1.0))

        # If FinBERT available, blend with neural score
        if self.finbert_available:
            try:
                neural = self._finbert_score(text)
                for key in scores:
                    scores[key] = 0.7 * scores[key] + 0.3 * neural.get(key, 50.0)
            except Exception as exc:
                logger.warning("Neural blending failed, using rule-based only: %s", exc)

        return scores

    def analyze_batch(self, texts: List[str]) -> List[Dict[str, float]]:
        """Analyze sentiment for a batch of texts."""
        return [self.analyze(text) for text in texts]

    def analyze_article(self, article: Article) -> Article:
        """Score an article and return updated article with sentiment fields."""
        text = f"{article.title} {getattr(article, 'content', '') or ''}"
        scores = self.analyze(text)

        article.panic_score = scores["panic"]
        article.caution_score = scores["caution"]
        article.uncertainty_score = scores["uncertainty"]
        article.optimism_score = scores["optimism"]
        article.complacency_score = scores["complacency"]
        article.euphoria_score = scores["euphoria"]

        # Overall: weighted toward positive/negative extremes
        article.sentiment_score = 50.0 + (
            scores["optimism"]
            + scores["euphoria"] * 0.5
            - scores["panic"]
            - scores["caution"] * 0.5
        ) * 0.3
        article.sentiment_score = max(0.0, min(100.0, article.sentiment_score))

        return article
