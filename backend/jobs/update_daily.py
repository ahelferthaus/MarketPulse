"""Daily update job for Westwood MarketPulse.

Orchestrates the full scoring pipeline for each configured market:
1. Fetch data from available providers
2. Calculate all indicator components
3. Calculate all four scores (Classic, Narrative, Positioning, Composite)
4. Generate explanation text
5. Save results to DuckDB

For the initial implementation, this uses MockProvider data. Real provider
integration is left as TODO items for subsequent layers.
"""

from __future__ import annotations

import asyncio
import logging
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from backend.config import settings
from backend.domain.article import Article
from backend.domain.indicator import IndicatorResult
from backend.domain.market import DEFAULT_MARKETS, MarketConfig
from backend.domain.score import (
    DataQualityReport,
    MarketPulseScore,
    Regime,
    ScoreDriver,
)
from backend.domain.sentiment import NarrativeSnapshot
from backend.storage.duckdb_store import DuckDBStore

logger = logging.getLogger(__name__)


# ── Mock Provider (temporary — will be replaced by real providers) ──────


class MockProvider:
    """Mock data provider for development and testing.

    Generates realistic-looking random data so the pipeline can run
    without any external API keys or network access.

    TODO: Replace with real provider integration (Layer 2).
    """

    def __init__(self, seed: int = 42) -> None:
        self.rng = random.Random(seed)
        self.name = "mock"
        self.tier = "public"

    async def get_price_history(self, ticker: str, days: int) -> dict:
        """Generate mock price history."""
        return {
            "ticker": ticker,
            "days": days,
            "prices": [100.0 + self.rng.gauss(0, 5) for _ in range(min(days, 30))],
        }

    async def get_current_quote(self, ticker: str) -> dict:
        """Generate mock current quote."""
        return {
            "ticker": ticker,
            "price": 100.0 + self.rng.gauss(0, 10),
            "change_pct": self.rng.gauss(0, 2),
        }

    async def get_breadth_data(self, market_id: str) -> dict:
        """Generate mock market breadth data."""
        return {
            "market_id": market_id,
            "advancing_pct": 50.0 + self.rng.gauss(0, 15),
            "above_ma200_pct": 50.0 + self.rng.gauss(0, 20),
        }

    async def get_options_data(self, ticker: str) -> dict:
        """Generate mock options data."""
        put_call = 0.7 + self.rng.gauss(0, 0.2)
        return {
            "ticker": ticker,
            "put_call_ratio": max(0.3, min(2.0, put_call)),
        }

    async def get_credit_spreads(self, series_id: str) -> dict:
        """Generate mock credit spread data."""
        return {
            "series_id": series_id,
            "spread_bps": 400.0 + self.rng.gauss(0, 100),
        }

    async def get_safe_haven_assets(self) -> dict:
        """Generate mock safe haven returns."""
        return {
            "TLT": self.rng.gauss(0, 1),
            "GLD": self.rng.gauss(0, 1),
            "UUP": self.rng.gauss(0, 0.5),
        }

    async def get_news_articles(self, query: str, limit: int) -> List[Article]:
        """Generate mock news articles."""
        templates = [
            ("Markets Rally on Strong Earnings Reports", 65.0),
            ("Fed Signals Potential Rate Pause", 55.0),
            ("Investors Brace for Volatility Ahead", 40.0),
            ("Tech Stocks Lead Broad Market Gains", 70.0),
            ("Economic Data Shows Mixed Signals", 50.0),
            ("Credit Markets Show Signs of Stress", 35.0),
            ("Consumer Confidence Hits New High", 72.0),
            ("Global Trade Tensions Escalate", 38.0),
            ("Analysts Upgrade Sector Outlooks", 62.0),
            ("Market Breadth Improves Across Sectors", 58.0),
        ]
        articles = []
        for i, (title, sentiment) in enumerate(templates[:limit]):
            articles.append(
                Article(
                    timestamp=datetime.now(timezone.utc),
                    source="mock_news",
                    title=title,
                    url=f"https://example.com/article/{i}",
                    content=f"Mock article content for: {title}",
                    sentiment_score=min(100.0, max(0.0, sentiment + self.rng.gauss(0, 10))),
                    panic_score=min(100.0, max(0.0, 50.0 - sentiment * 0.5 + self.rng.gauss(0, 10))),
                    caution_score=min(100.0, max(0.0, 50.0 + self.rng.gauss(0, 15))),
                    uncertainty_score=min(100.0, max(0.0, 50.0 + self.rng.gauss(0, 10))),
                    optimism_score=min(100.0, max(0.0, sentiment + self.rng.gauss(0, 10))),
                    complacency_score=min(100.0, max(0.0, 30.0 + self.rng.gauss(0, 15))),
                    euphoria_score=min(100.0, max(0.0, max(0, sentiment - 70) * 2 + self.rng.gauss(0, 5))),
                    topics=["mock"],
                    market_relevance=0.8,
                )
            )
        return articles

    async def get_social_posts(self, query: str, limit: int) -> list:
        """Generate mock social posts."""
        return []

    async def get_flows_data(self, ticker: str) -> dict:
        """Generate mock ETF flow data."""
        return {"ticker": ticker, "net_flow_mln": self.rng.gauss(0, 500)}

    async def get_source_status(self) -> dict:
        """Return mock source status."""
        return {
            "provider": self.name,
            "available": True,
            "last_successful_fetch": datetime.now(timezone.utc),
            "error_count_24h": 0,
            "avg_response_ms": 50,
            "data_freshness_minutes": 5,
            "tier": self.tier,
        }


# ── Indicator calculators (stubs — full implementation in Layer 3) ─────


def calculate_momentum(provider: MockProvider, market: MarketConfig) -> IndicatorResult:
    """Calculate market momentum indicator.

    TODO: Replace with real momentum calculator using actual price history.
    """
    score = 50.0 + random.gauss(0, 15)
    return IndicatorResult(
        name="momentum",
        raw_value=score,
        normalized_score=min(100.0, max(0.0, score)),
        weight=1.0 / 7.0,
        direction="bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        description=f"Market momentum is {'above' if score > 50 else 'below'} average",
        data_source="mock",
        confidence=80.0,
        inverted=False,
    )


def calculate_price_strength(provider: MockProvider, market: MarketConfig) -> IndicatorResult:
    """Calculate price strength indicator.

    TODO: Replace with real price strength calculator.
    """
    score = 50.0 + random.gauss(0, 15)
    return IndicatorResult(
        name="price_strength",
        raw_value=score,
        normalized_score=min(100.0, max(0.0, score)),
        weight=1.0 / 7.0,
        direction="bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        description=f"Price strength is {'strong' if score > 55 else 'weak' if score < 45 else 'neutral'}",
        data_source="mock",
        confidence=80.0,
        inverted=False,
    )


def calculate_breadth(provider: MockProvider, market: MarketConfig) -> IndicatorResult:
    """Calculate market breadth indicator.

    TODO: Replace with real breadth calculator.
    """
    score = 50.0 + random.gauss(0, 15)
    return IndicatorResult(
        name="breadth",
        raw_value=score,
        normalized_score=min(100.0, max(0.0, score)),
        weight=1.0 / 7.0,
        direction="bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        description=f"Market breadth is {'broad' if score > 55 else 'narrow' if score < 45 else 'neutral'}",
        data_source="mock",
        confidence=75.0,
        inverted=False,
    )


def calculate_put_call(provider: MockProvider, market: MarketConfig) -> IndicatorResult:
    """Calculate put/call ratio indicator.

    TODO: Replace with real put/call calculator using CBOE data.
    """
    score = 50.0 + random.gauss(0, 15)
    return IndicatorResult(
        name="put_call",
        raw_value=score,
        normalized_score=min(100.0, max(0.0, score)),
        weight=1.0 / 7.0,
        direction="bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        description=f"Put/call ratio indicates {'fear' if score < 45 else 'complacency' if score > 55 else 'balance'}",
        data_source="mock",
        confidence=85.0,
        inverted=True,
    )


def calculate_credit_spreads(provider: MockProvider, market: MarketConfig) -> IndicatorResult:
    """Calculate credit spread indicator.

    TODO: Replace with real credit spread calculator using FRED data.
    """
    score = 50.0 + random.gauss(0, 15)
    return IndicatorResult(
        name="credit_spreads",
        raw_value=score,
        normalized_score=min(100.0, max(0.0, score)),
        weight=1.0 / 7.0,
        direction="bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        description=f"Credit spreads are {'tight' if score > 55 else 'wide' if score < 45 else 'average'}",
        data_source="mock",
        confidence=80.0,
        inverted=True,
    )


def calculate_volatility(provider: MockProvider, market: MarketConfig) -> IndicatorResult:
    """Calculate volatility indicator.

    TODO: Replace with real volatility calculator using VIX data.
    """
    score = 50.0 + random.gauss(0, 15)
    return IndicatorResult(
        name="volatility",
        raw_value=score,
        normalized_score=min(100.0, max(0.0, score)),
        weight=1.0 / 7.0,
        direction="bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        description=f"Volatility is {'elevated' if score < 45 else 'subdued' if score > 55 else 'normal'}",
        data_source="mock",
        confidence=90.0,
        inverted=True,
    )


def calculate_safe_haven(provider: MockProvider, market: MarketConfig) -> IndicatorResult:
    """Calculate safe haven demand indicator.

    TODO: Replace with real safe haven calculator.
    """
    score = 50.0 + random.gauss(0, 15)
    return IndicatorResult(
        name="safe_haven",
        raw_value=score,
        normalized_score=min(100.0, max(0.0, score)),
        weight=1.0 / 7.0,
        direction="bullish" if score > 55 else "bearish" if score < 45 else "neutral",
        description=f"Safe haven demand is {'high' if score < 45 else 'low' if score > 55 else 'neutral'}",
        data_source="mock",
        confidence=75.0,
        inverted=True,
    )


# ── Scoring engines (stubs — full implementation in Layer 4) ───────────


def calculate_classic_score(components: List[IndicatorResult]) -> float:
    """Calculate MarketPulse Classic score from components.

    Classic is the simple average of all 7 normalized component scores.

    TODO: Add confidence weighting when components are missing.
    """
    if not components:
        return 50.0
    valid_scores = [c.normalized_score for c in components if c.confidence > 0]
    if not valid_scores:
        return 50.0
    return sum(valid_scores) / len(valid_scores)


def calculate_narrative_score(articles: List[Article]) -> float:
    """Calculate MarketPulse Narrative score from articles.

    Maps the emotion profile to a 0-100 score.
    Panic/caution/uncertainty pull lower; optimism pulls higher;
    complacency/euphoria indicate elevated risk (moderate score).

    TODO: Full NLP pipeline with FinBERT and topic classification.
    """
    if not articles:
        return 50.0

    avg_sentiment = sum(a.sentiment_score for a in articles) / len(articles)
    avg_panic = sum(a.panic_score for a in articles) / len(articles)
    avg_euphoria = sum(a.euphoria_score for a in articles) / len(articles)

    # Blend sentiment with fear/greed adjustments
    score = avg_sentiment
    if avg_panic > 60:
        score -= (avg_panic - 60) * 0.5
    if avg_euphoria > 60:
        score -= (avg_euphoria - 60) * 0.3

    return min(100.0, max(0.0, score))


def calculate_positioning_score(provider: MockProvider, market: MarketConfig) -> float:
    """Calculate MarketPulse Positioning score.

    Combines options, volatility, credit spreads, and flow data.

    TODO: Full positioning calculator with real flow data.
    """
    # Stub: random positioning score
    score = 50.0 + random.gauss(0, 12)
    return min(100.0, max(0.0, score))


def calculate_composite(
    classic: float,
    narrative: float,
    positioning: float,
) -> float:
    """Calculate composite score as weighted average.

    Uses weights from settings (default: 40% classic, 30% narrative, 30% positioning).
    """
    weights = settings.composite_weights
    total_weight = sum(weights.values())
    if total_weight == 0:
        return 50.0

    composite = (
        classic * weights["classic"]
        + narrative * weights["narrative"]
        + positioning * weights["positioning"]
    ) / total_weight

    return min(100.0, max(0.0, composite))


def generate_explanation(
    composite: float,
    regime: Regime,
    drivers: List[ScoreDriver],
) -> str:
    """Generate a one-sentence plain-English explanation.

    Args:
        composite: Composite score (0-100).
        regime: Current regime classification.
        drivers: Top score drivers.

    Returns:
        One-sentence explanation string.
    """
    regime_phrases = {
        Regime.MP1_CAPITULATION: "Markets are in extreme risk-off, with widespread fear and defensive positioning.",
        Regime.MP2_DEFENSIVE: "Markets are defensive, with cautious sentiment and protective flows.",
        Regime.MP3_NEUTRAL: "Markets are balanced, with mixed signals and no strong directional bias.",
        Regime.MP4_RISK_ON: "Markets are risk-on, supported by positive momentum and constructive positioning.",
        Regime.MP5_EUPHORIA: "Markets are euphoric, with elevated sentiment and aggressive positioning.",
    }

    base = regime_phrases.get(regime, "Markets show mixed signals.")

    if drivers:
        top_driver = max(drivers, key=lambda d: abs(d.contribution))
        driver_text = f" Key driver: {top_driver.component} ({top_driver.direction})."
        base += driver_text

    return base


def build_drivers(components: List[IndicatorResult]) -> List[ScoreDriver]:
    """Build ScoreDriver list from component results.

    Each component's contribution is derived from its deviation from neutral (50).
    """
    drivers = []
    for comp in components:
        deviation = comp.normalized_score - 50.0
        contribution = deviation / 2.5  # Scale to roughly -20 to +20
        direction = (
            "bullish"
            if (not comp.inverted and deviation > 5)
            or (comp.inverted and deviation < -5)
            else "bearish"
            if (not comp.inverted and deviation < -5)
            or (comp.inverted and deviation > 5)
            else "neutral"
        )
        drivers.append(
            ScoreDriver(
                component=comp.name,
                contribution=round(contribution, 1),
                direction=direction,
                description=comp.description,
            )
        )
    # Sort by absolute contribution descending
    drivers.sort(key=lambda d: abs(d.contribution), reverse=True)
    return drivers


# ── Main update orchestrator ────────────────────────────────────────────


async def update_market(
    market: MarketConfig,
    store: DuckDBStore,
    provider: MockProvider,
) -> Optional[MarketPulseScore]:
    """Run the full scoring pipeline for a single market.

    Args:
        market: Market configuration.
        store: DuckDB store for persistence.
        provider: Data provider (MockProvider for now).

    Returns:
        The computed MarketPulseScore, or None if the update failed.
    """
    logger.info("Starting update for market: %s", market.market_id)
    now = datetime.now(timezone.utc)

    try:
        # ── Step 1: Fetch data ──────────────────────────────────────────
        # TODO: Replace with real provider calls (Layer 2)
        # ── Step 1: Fetch data ──────────────────────────────────────────
        # TODO: Replace with real provider calls (Layer 2)
        # Fetch independent data sources concurrently
        quote_task = provider.get_current_quote(market.etf_proxy)
        breadth_task = provider.get_breadth_data(market.market_id)
        options_task = provider.get_options_data(market.options_proxy)
        credit_task = provider.get_credit_spreads(market.credit_spread_proxy)
        safe_haven_task = provider.get_safe_haven_assets()

        await asyncio.gather(
            quote_task,
            breadth_task,
            options_task,
            credit_task,
            safe_haven_task,
        )

        # Fetch articles separately (result needed for narrative scoring)
        articles = await provider.get_news_articles(market.market_id, limit=10)

        # TODO: Fetch real social posts when API keys available
        social_posts: list = []

        # ── Step 2: Calculate Classic components ────────────────────────
        # TODO: Replace with real indicator calculators (Layer 3)
        components = [
            calculate_momentum(provider, market),
            calculate_price_strength(provider, market),
            calculate_breadth(provider, market),
            calculate_put_call(provider, market),
            calculate_credit_spreads(provider, market),
            calculate_volatility(provider, market),
            calculate_safe_haven(provider, market),
        ]

        # ── Step 3: Calculate all four scores ───────────────────────────
        # TODO: Replace with real scoring engines (Layer 4)
        classic_score = calculate_classic_score(components)

        narrative_score = calculate_narrative_score(articles)
        narrative_score = calculate_narrative_score(articles)

        positioning_score = calculate_positioning_score(provider, market)

        composite_score = calculate_composite(
            classic_score, narrative_score, positioning_score
        )

        regime = Regime.from_score(composite_score)
        drivers = build_drivers(components)
        explanation = generate_explanation(composite_score, regime, drivers)

        # ── Step 4: Build data quality report ───────────────────────────
        data_quality = DataQualityReport(
            overall_confidence=75.0,
            sources_used=1,
            sources_available=6,
            missing_components=[],
            substituted_components=["all"],
            stale_data_warnings=["Using mock data — not real market data"],
            data_freshness_minutes=5,
        )

        # ── Step 5: Build final score ───────────────────────────────────
        score = MarketPulseScore(
            timestamp=now,
            market_id=market.market_id,
            classic_score=round(classic_score, 1),
            narrative_score=round(narrative_score, 1),
            positioning_score=round(positioning_score, 1),
            composite_score=round(composite_score, 1),
            regime=regime,
            regime_label=regime.label,
            direction="stable",
            confidence=data_quality.overall_confidence,
            explanation=explanation,
            what_changed=None,
            drivers=drivers,
            data_quality=data_quality,
        )

        # ── Step 6: Save to DuckDB ──────────────────────────────────────
        store.save_score(score)
        store.save_component_scores(now, market.market_id, components)

        # Save narrative snapshot
        if articles:
            narrative_snapshot = NarrativeSnapshot(
                timestamp=now,
                market_id=market.market_id,
                panic_score=sum(a.panic_score for a in articles) / len(articles),
                caution_score=sum(a.caution_score for a in articles) / len(articles),
                uncertainty_score=sum(a.uncertainty_score for a in articles) / len(articles),
                optimism_score=sum(a.optimism_score for a in articles) / len(articles),
                complacency_score=sum(a.complacency_score for a in articles) / len(articles),
                euphoria_score=sum(a.euphoria_score for a in articles) / len(articles),
                article_count=len(articles),
                top_phrases=["mock"],
                overall_narrative_score=narrative_score,
            )
            store.save_narrative_snapshot(narrative_snapshot)

        # Save articles
        store.save_articles(articles)

        logger.info(
            "Update complete for %s: composite=%.1f regime=%s",
            market.market_id,
            score.composite_score,
            score.regime.value,
        )
        return score

    except Exception as exc:
        logger.error(
            "Update failed for market %s: %s",
            market.market_id,
            exc,
            exc_info=True,
        )
        # Log provider failure
        store.log_provider_status(
            provider="mock",
            available=False,
            error_message=str(exc),
        )
        return None


async def run_daily_update(store: Optional[DuckDBStore] = None) -> Dict[str, Any]:
    """Run the daily update for all configured markets.

    Args:
        store: Optional DuckDBStore instance. Creates one if not provided.

    Returns:
        Dict with update results: {'success': [...], 'failed': [...], 'scores': {...}}
    """
    if store is None:
        store = DuckDBStore()

    store.init_database()
    provider = MockProvider()

    results: Dict[str, Any] = {
        "success": [],
        "failed": [],
        "scores": {},
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    logger.info("=== Daily Update Started ===")

    for market_id, market_config in DEFAULT_MARKETS.items():
        score = await update_market(market_config, store, provider)
        if score:
            results["success"].append(market_id)
            results["scores"][market_id] = {
                "composite": score.composite_score,
                "classic": score.classic_score,
                "narrative": score.narrative_score,
                "positioning": score.positioning_score,
                "regime": score.regime.value,
                "confidence": score.confidence,
            }
        else:
            results["failed"].append(market_id)

    logger.info(
        "=== Daily Update Complete: %d succeeded, %d failed ===",
        len(results["success"]),
        len(results["failed"]),
    )

    return results


# ── CLI entry point ─────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    logging.basicConfig(
        level=getattr(logging, settings.log_level),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    store = DuckDBStore()
    results = asyncio.run(run_daily_update(store))

    print(f"\nUpdate Results ({results['timestamp']}):")
    print(f"  Success: {', '.join(results['success']) or 'None'}")
    print(f"  Failed:  {', '.join(results['failed']) or 'None'}")
    print(f"\nScores:")
    for market_id, score_data in results["scores"].items():
        print(
            f"  {market_id}: composite={score_data['composite']:.1f} "
            f"regime={score_data['regime']}"
        )

    store.close()
