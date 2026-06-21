"""
MarketPulse Narrative Index

NLP/news/social sentiment index using 6 emotional dimensions:

Bearish dimensions (lower score):
- Panic: Extreme negative emotion, crash language
- Caution: Defensive, hedging, protective language
- Uncertainty: Mixed signals, "wait and see", ambiguity

Bullish dimensions (raise score):
- Optimism: Positive outlook, growth language
- Complacency: Low volatility expectations, risk-ignoring
- Euphoria: Extreme bullishness, bubble language

Scoring: Weighted combination of dimension scores mapped to 0-100.

The narrative index captures the emotional tone of financial media
and social discourse. It complements the data-driven Classic index
by measuring what people are saying, not just what markets are doing.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.score import DataQualityReport
from backend.domain.indicator import IndicatorResult
from backend.indicators.narrative_sentiment import NarrativeSentimentIndicator

logger = logging.getLogger(__name__)


class MarketPulseNarrative:
    """Calculates the MarketPulse Narrative index from text sentiment.

    The Narrative index measures market psychology through natural
    language processing of financial news and social content.

    Score interpretation:
        0-20: Extreme fear/panic in media
        20-40: Cautious/defensive tone
        40-60: Balanced/neutral discourse
        60-80: Optimistic sentiment
        80-100: Euphoric/bubble-like exuberance
    """

    # Dimension weights: negative = bearish, positive = bullish
    DIMENSION_WEIGHTS: Dict[str, float] = {
        "panic": -1.0,        # Extreme fear → very bearish
        "caution": -0.5,      # Defensive posture → bearish
        "uncertainty": -0.3,  # Ambiguity → slightly bearish
        "optimism": 0.8,      # Positive outlook → bullish
        "complacency": 0.5,   # Risk ignoring → bullish (but risky)
        "euphoria": 1.0,      # Extreme bullishness → very bullish
    }

    # Minimum articles for reliable scoring
    MIN_ARTICLES = 5

    def __init__(self):
        self.sentiment = NarrativeSentimentIndicator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def calculate(
        self,
        provider_chain: Any,       # ProviderChain instance
        market_config: Any,        # MarketConfig instance
        nlp_pipeline: Any = None,  # NLP processing pipeline
    ) -> Tuple[float, List[IndicatorResult], DataQualityReport]:
        """Calculate Narrative score.

        Flow:
        1. Fetch news articles from RSS/news providers
        2. Process through NLP pipeline (sentiment scoring)
        3. Aggregate sentiment across 6 dimensions
        4. Map dimension scores to 0-100 composite
        5. Return score, components, quality report

        Args:
            provider_chain: ProviderChain with news/RSS providers
            market_config: Market configuration
            nlp_pipeline: Optional NLP pipeline for text processing

        Returns:
            Tuple of (composite_score, dimension_results, data_quality_report)
        """
        logger.info("Starting Narrative index calculation for market=%s", getattr(market_config, "market_id", "unknown"))

        # Step 1: Fetch news articles
        articles: List[Dict] = []
        try:
            query = getattr(market_config, "market_id", "sp500")
            articles = await provider_chain.get_news_articles(query=query, limit=100)
        except Exception as e:
            logger.warning("Failed to fetch news articles: %s", e)

        # Step 2: Process through NLP pipeline
        dimension_scores: Dict[str, float] = {}
        if articles and nlp_pipeline:
            try:
                dimension_scores = await self._process_with_nlp(articles, nlp_pipeline)
            except Exception as e:
                logger.warning("NLP processing failed: %s", e)
        elif articles:
            # Fallback: rule-based keyword scoring
            dimension_scores = self._rule_based_scoring(articles)

        # Step 3: Build component results for each dimension
        components = self._build_dimension_results(dimension_scores, len(articles))

        # Step 4: Calculate composite score
        score = self._compute_composite(dimension_scores)

        # Step 5: Build quality report
        quality = self._build_quality_report(dimension_scores, articles)

        logger.info(
            "Narrative index complete: score=%.2f, articles=%d, dimensions_scored=%d/%d",
            score,
            len(articles),
            sum(1 for d in dimension_scores.values() if d is not None),
            6,
        )

        return score, components, quality

    def calculate_sync(
        self,
        dimension_scores: Dict[str, float],
        article_count: int = 0,
    ) -> Tuple[float, List[IndicatorResult], DataQualityReport]:
        """Synchronous calculation from pre-computed dimension scores.

        Args:
            dimension_scores: Dict mapping dimension name to 0-100 score
            article_count: Number of articles analyzed

        Returns:
            Same tuple as calculate() but without async/await.
        """
        components = self._build_dimension_results(dimension_scores, article_count)
        score = self._compute_composite(dimension_scores)
        quality = self._build_quality_report(dimension_scores, article_count=article_count)
        return score, components, quality

    # ------------------------------------------------------------------
    # NLP Processing
    # ------------------------------------------------------------------

    async def _process_with_nlp(
        self,
        articles: List[Dict],
        nlp_pipeline: Any,
    ) -> Dict[str, float]:
        """Process articles through NLP pipeline to get dimension scores.

        Args:
            articles: List of article dicts with 'title', 'text', etc.
            nlp_pipeline: NLP pipeline with analyze() method

        Returns:
            Dict mapping dimension names to 0-100 scores
        """
        all_texts = []
        for article in articles:
            text = article.get("text", "") or article.get("content", "") or article.get("title", "")
            if text:
                all_texts.append(text)

        if not all_texts:
            return {}

        # Batch process through NLP
        try:
            if hasattr(nlp_pipeline, "analyze_batch"):
                results = await nlp_pipeline.analyze_batch(all_texts)
            else:
                results = nlp_pipeline.analyze_batch(all_texts)
        except Exception:
            # Fallback to rule-based
            return self._rule_based_scoring(articles)

        # Aggregate dimension scores across all articles
        aggregated: Dict[str, List[float]] = {
            "panic": [],
            "caution": [],
            "uncertainty": [],
            "optimism": [],
            "complacency": [],
            "euphoria": [],
        }

        for result in results:
            for dim in aggregated:
                if dim in result and result[dim] is not None:
                    aggregated[dim].append(result[dim])

        # Average each dimension
        return {
            dim: (sum(scores) / len(scores)) if scores else 50.0
            for dim, scores in aggregated.items()
        }

    def _rule_based_scoring(self, articles: List[Dict]) -> Dict[str, float]:
        """Rule-based sentiment scoring using financial lexicon.

        Scans article text for keyword matches across 6 dimensions.
        No ML dependencies required.

        Args:
            articles: List of article dicts

        Returns:
            Dict mapping dimension names to 0-100 scores
        """
        # Financial sentiment lexicon
        LEXICON: Dict[str, List[str]] = {
            "panic": [
                "crash", "collapse", "meltdown", "crisis", "panic", "sell-off",
                "bloodbath", "rout", "plunge", "freefall", "armageddon",
                "devastating", "catastrophe", "disaster", "emergency",
            ],
            "caution": [
                "hedge", "defensive", "protective", "worried", "concern",
                "cautious", "wary", "risk-off", "safe haven", "uncertainty",
                "volatile", "fragile", "vulnerable", "bubble",
            ],
            "uncertainty": [
                "uncertain", "unclear", "mixed", "wait and see", "ambiguous",
                "unpredictable", "unknown", "debatable", "divided", "confusion",
                "may", "might", "could", "possibly", "perhaps",
            ],
            "optimism": [
                "growth", "recovery", "expansion", "strong", "robust",
                "bullish", "upside", "opportunity", "promising", "outperform",
                "beat expectations", "solid", "healthy", "momentum",
            ],
            "complacency": [
                "calm", "quiet", "steady", "unchanged", "flat", "stability",
                " Goldilocks", "smooth", "benign", "dovish", "accommodative",
                "easy money", "low volatility", "range-bound",
            ],
            "euphoria": [
                "euphoria", "mania", "frenzy", "boom", "to the moon",
                "unstoppable", "parabolic", "record high", "all-time",
                "exponential", "disruptive", "revolutionary", "can't lose",
                "sure thing", "no brainer",
            ],
        }

        dimension_hits: Dict[str, int] = {dim: 0 for dim in LEXICON}
        total_words = 0

        for article in articles:
            text = article.get("text", "") or article.get("content", "") or article.get("title", "")
            if not text:
                continue

            text_lower = text.lower()
            words = text_lower.split()
            total_words += len(words)

            for dim, keywords in LEXICON.items():
                for kw in keywords:
                    dimension_hits[dim] += text_lower.count(kw)

        # Normalize to 0-100 (with dampening to prevent extremes)
        # Use log scaling to avoid dominance by any single dimension
        import math

        scores: Dict[str, float] = {}
        for dim, hits in dimension_hits.items():
            if total_words > 0 and hits > 0:
                # Normalize by article count and apply log scaling
                per_article = hits / len(articles) if articles else 0
                score = min(100.0, math.log1p(per_article * 10) * 25)
                scores[dim] = score
            else:
                scores[dim] = 0.0

        return scores

    # ------------------------------------------------------------------
    # Score computation
    # ------------------------------------------------------------------

    def _compute_composite(self, dimension_scores: Dict[str, float]) -> float:
        """Map dimension scores to 0-100 composite.

        Algorithm:
        1. Each dimension contributes weighted score
        2. Negative-weight dimensions (panic, caution, uncertainty)
           subtract from the score
        3. Positive-weight dimensions (optimism, complacency, euphoria)
           add to the score
        4. Normalize to 0-100 range

        The formula ensures that high panic/caution pulls the score down
        while high optimism/euphoria pushes it up.
        """
        if not dimension_scores:
            return 50.0  # Neutral if no data

        weighted_sum = 0.0
        total_weight = 0.0

        for dim, weight in self.DIMENSION_WEIGHTS.items():
            if dim in dimension_scores:
                normalized = dimension_scores[dim] / 100.0  # 0-1
                weighted_sum += weight * normalized
                total_weight += abs(weight)

        if total_weight == 0:
            return 50.0

        # Normalize to 0-100
        # Range of weighted_sum: [-1.8, +2.3]
        # Shift by +1.8, divide by 4.1, multiply by 100
        normalized = (weighted_sum + 1.8) / 4.1 * 100
        return max(0.0, min(100.0, normalized))

    def _build_dimension_results(
        self,
        dimension_scores: Dict[str, float],
        article_count: int,
    ) -> List[IndicatorResult]:
        """Build IndicatorResult objects for each dimension."""
        components = []
        for dim, weight in self.DIMENSION_WEIGHTS.items():
            score = dimension_scores.get(dim)
            direction = "bullish" if weight > 0 else "bearish"
            available = score is not None

            if score is not None and score > 50:
                intensity = "strong" if score > 75 else "moderate"
            elif score is not None:
                intensity = "low"
            else:
                intensity = "unknown"

            components.append(IndicatorResult(
                name=dim,
                score=score,
                raw_value=score,
                raw_unit="score",
                available=available,
                direction=direction,
                description=f"{dim.capitalize()}: {intensity} ({score:.1f})" if score is not None else f"{dim}: unavailable",
                data_source="nlp",
                invert=weight < 0,
            ))

        # Add meta-component for article count
        components.append(IndicatorResult(
            name="article_count",
            score=float(min(article_count, 100)),
            raw_value=float(article_count),
            raw_unit="count",
            available=article_count >= self.MIN_ARTICLES,
            direction="neutral",
            description=f"Articles analyzed: {article_count}",
            data_source="news_providers",
            invert=False,
        ))

        return components

    def _build_quality_report(
        self,
        dimension_scores: Dict[str, float],
        articles: Optional[List[Dict]] = None,
        article_count: int = 0,
    ) -> DataQualityReport:
        """Build data quality report for narrative scoring."""
        count = len(articles) if articles else article_count
        scored_dims = sum(1 for d in dimension_scores.values() if d is not None)
        missing_dims = [d for d in self.DIMENSION_WEIGHTS if d not in dimension_scores]

        # Confidence calculation
        confidence = 100.0
        if count < self.MIN_ARTICLES:
            confidence -= (self.MIN_ARTICLES - count) * 10
            confidence = max(0.0, confidence)
        if scored_dims < 6:
            confidence -= (6 - scored_dims) * 5
        if count == 0:
            confidence = 0.0

        warnings = []
        if count < self.MIN_ARTICLES:
            warnings.append(f"Low article count: {count} (min {self.MIN_ARTICLES})")
        if scored_dims < 4:
            warnings.append(f"Only {scored_dims}/6 dimensions scored")

        return DataQualityReport(
            overall_confidence=max(0.0, confidence),
            sources_used=scored_dims,
            sources_available=6,
            missing_components=missing_dims,
            substituted_components=[],
            stale_data_warnings=warnings,
            data_freshness_minutes=60,  # Typical news refresh
        )
