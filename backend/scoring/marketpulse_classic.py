"""
MarketPulse Classic Index

Market-data-driven sentiment index using 7 components:
1. Market momentum (price vs 125d MA)
2. Price strength (new highs/lows)
3. Price breadth (advancing/declining)
4. Put/call ratio (inverted)
5. Credit spreads (inverted)
6. Volatility/VIX (inverted)
7. Safe haven demand (equity vs safe havens)

Assembly: Equal-weighted average of available components.
Missing components: Weight redistributed proportionally.

Each component produces a 0-100 score via rolling percentile normalization.
Inverted components (put/call, credit spreads, volatility, safe haven) are
already flipped so that extreme readings map to the appropriate end of
the 0-100 scale.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.score import DataQualityReport, Regime
from backend.domain.indicator import IndicatorResult
from backend.indicators.momentum import MomentumIndicator
from backend.indicators.highs_lows import HighsLowsIndicator
from backend.indicators.breadth import BreadthIndicator
from backend.indicators.put_call import PutCallIndicator
from backend.indicators.volatility import VolatilityIndicator
from backend.indicators.credit_spreads import CreditSpreadsIndicator
from backend.indicators.safe_haven import SafeHavenIndicator

logger = logging.getLogger(__name__)


class MarketPulseClassic:
    """Calculates the MarketPulse Classic index from market data.

    The Classic index is a pure market-data-driven sentiment gauge.
    It combines 7 normalized indicators into an equal-weighted composite.
    Missing components have their weights redistributed proportionally
    among available components.

    Score interpretation:
        0-20: Capitulation (extreme fear)
        20-40: Defensive (risk-off)
        40-60: Neutral (balanced)
        60-80: Risk-on (bullish)
        80-100: Euphoria (extreme greed)
    """

    # Equal weights for 7 components
    COMPONENT_WEIGHTS: Dict[str, float] = {
        "momentum": 1.0 / 7.0,
        "price_strength": 1.0 / 7.0,
        "breadth": 1.0 / 7.0,
        "put_call": 1.0 / 7.0,
        "credit_spreads": 1.0 / 7.0,
        "volatility": 1.0 / 7.0,
        "safe_haven": 1.0 / 7.0,
    }

    # Map component names to their indicator classes
    COMPONENT_MAP: Dict[str, str] = {
        "momentum": "momentum",
        "price_strength": "highs_lows",
        "breadth": "breadth",
        "put_call": "put_call",
        "credit_spreads": "credit",
        "volatility": "volatility",
        "safe_haven": "safe_haven",
    }

    def __init__(self):
        self.momentum = MomentumIndicator()
        self.highs_lows = HighsLowsIndicator()
        self.breadth = BreadthIndicator()
        self.put_call = PutCallIndicator()
        self.volatility = VolatilityIndicator()
        self.credit = CreditSpreadsIndicator()
        self.safe_haven = SafeHavenIndicator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def calculate(
        self,
        provider_chain: Any,  # ProviderChain instance
        market_config: Any,   # MarketConfig instance
        history_days: int = 252,
    ) -> Tuple[float, List[IndicatorResult], DataQualityReport]:
        """Calculate Classic score from provider data.

        Flow:
        1. Fetch all required data from providers
        2. Calculate each component indicator
        3. Equal-weight average (redistribute for missing)
        4. Return score, components, and quality report

        Args:
            provider_chain: ProviderChain with configured providers
            market_config: Market configuration (tickers, proxies, etc.)
            history_days: Lookback window for normalization

        Returns:
            Tuple of (composite_score, component_results, data_quality_report)
        """
        logger.info("Starting Classic index calculation for market=%s", getattr(market_config, "market_id", "unknown"))

        # Step 1: Calculate all 7 components
        components: List[IndicatorResult] = []

        # 1. Market momentum
        momentum_result = await self._calc_momentum(provider_chain, market_config, history_days)
        components.append(momentum_result)

        # 2. Price strength (new highs/lows)
        strength_result = await self._calc_price_strength(provider_chain, market_config, history_days)
        components.append(strength_result)

        # 3. Price breadth (advancing/declining)
        breadth_result = await self._calc_breadth(provider_chain, market_config, history_days)
        components.append(breadth_result)

        # 4. Put/call ratio (inverted)
        pc_result = await self._calc_put_call(provider_chain, market_config, history_days)
        components.append(pc_result)

        # 5. Credit spreads (inverted)
        credit_result = await self._calc_credit_spreads(provider_chain, market_config, history_days)
        components.append(credit_result)

        # 6. Volatility/VIX (inverted)
        vol_result = await self._calc_volatility(provider_chain, market_config, history_days)
        components.append(vol_result)

        # 7. Safe haven demand (inverted)
        safe_result = await self._calc_safe_haven(provider_chain, market_config, history_days)
        components.append(safe_result)

        # Step 2: Assemble with weight redistribution
        score, quality_report = self._assemble_score(components)

        logger.info(
            "Classic index complete: score=%.2f, components_available=%d/%d, confidence=%.1f",
            score,
            sum(1 for c in components if c.available),
            len(components),
            quality_report.overall_confidence,
        )

        return score, components, quality_report

    def calculate_sync(
        self,
        data_bundle: Dict[str, Any],
    ) -> Tuple[float, List[IndicatorResult], DataQualityReport]:
        """Synchronous calculation for backtesting and testing.

        Args:
            data_bundle: Dict with pre-fetched data series keyed by component name.
                Expected keys: 'prices', 'new_highs', 'new_lows', 'advancing',
                'declining', 'put_call_series', 'vix_series', 'spread_series',
                'equity_prices', 'safe_haven_prices'

        Returns:
            Same tuple as calculate() but without async/await.
        """
        components: List[IndicatorResult] = []

        # 1. Momentum
        prices = data_bundle.get("prices")
        if prices and len(prices) >= 135:
            score = self.momentum.calculate_sync(prices)
            components.append(IndicatorResult(
                name="momentum",
                score=score,
                raw_value=prices[-1] / (sum(prices[-125:]) / 125) if len(prices) >= 125 else None,
                raw_unit="ratio",
                available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Price vs 125d MA: {score:.1f}" if score else "Momentum unavailable",
                data_source="historical",
                invert=False,
            ))
        else:
            components.append(self._unavailable("momentum"))

        # 2. Price strength
        nh = data_bundle.get("new_highs")
        nl = data_bundle.get("new_lows")
        if nh and nl:
            score = self.highs_lows.calculate_sync(nh, nl)
            components.append(IndicatorResult(
                name="price_strength",
                score=score,
                raw_value=None,
                raw_unit="ratio",
                available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"New highs/lows strength: {score:.1f}" if score else "Strength unavailable",
                data_source="historical",
                invert=False,
            ))
        else:
            components.append(self._unavailable("price_strength"))

        # 3. Breadth
        adv = data_bundle.get("advancing")
        dec = data_bundle.get("declining")
        if adv and dec:
            score = self.breadth.calculate_sync(adv, dec)
            components.append(IndicatorResult(
                name="breadth",
                score=score,
                raw_value=None,
                raw_unit="percent",
                available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Market breadth: {score:.1f}" if score else "Breadth unavailable",
                data_source="historical",
                invert=False,
            ))
        else:
            components.append(self._unavailable("breadth"))

        # 4. Put/call
        pc = data_bundle.get("put_call_series")
        if pc and len(pc) >= 20:
            score = self.put_call.calculate_sync(pc)
            components.append(IndicatorResult(
                name="put_call",
                score=score,
                raw_value=pc[-1],
                raw_unit="ratio",
                available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Put/call ratio (inverted): {score:.1f}" if score else "P/C unavailable",
                data_source="historical",
                invert=True,
            ))
        else:
            components.append(self._unavailable("put_call"))

        # 5. Credit spreads
        spreads = data_bundle.get("spread_series")
        if spreads and len(spreads) >= 20:
            score = self.credit.calculate_sync(spreads)
            components.append(IndicatorResult(
                name="credit_spreads",
                score=score,
                raw_value=spreads[-1],
                raw_unit="bps",
                available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Credit spreads (inverted): {score:.1f}" if score else "Credit unavailable",
                data_source="historical",
                invert=True,
            ))
        else:
            components.append(self._unavailable("credit_spreads"))

        # 6. Volatility
        vix = data_bundle.get("vix_series")
        if vix and len(vix) >= 20:
            score = self.volatility.calculate_sync(vix)
            components.append(IndicatorResult(
                name="volatility",
                score=score,
                raw_value=vix[-1],
                raw_unit="index",
                available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"VIX (inverted): {score:.1f}" if score else "VIX unavailable",
                data_source="historical",
                invert=True,
            ))
        else:
            components.append(self._unavailable("volatility"))

        # 7. Safe haven
        eq = data_bundle.get("equity_prices")
        sh = data_bundle.get("safe_haven_prices")
        if eq and sh and len(eq) >= 21 and len(sh) >= 21:
            score = self.safe_haven.calculate_sync(eq, sh)
            components.append(IndicatorResult(
                name="safe_haven",
                score=score,
                raw_value=None,
                raw_unit="percent",
                available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Safe haven demand (inverted): {score:.1f}" if score else "Safe haven unavailable",
                data_source="historical",
                invert=True,
            ))
        else:
            components.append(self._unavailable("safe_haven"))

        score, quality_report = self._assemble_score(components)
        return score, components, quality_report

    # ------------------------------------------------------------------
    # Component calculators (async — call providers)
    # ------------------------------------------------------------------

    async def _calc_momentum(
        self,
        provider_chain: Any,
        market_config: Any,
        history_days: int,
    ) -> IndicatorResult:
        """Calculate momentum: price vs 125d MA rolling percentile."""
        try:
            ticker = getattr(market_config, "benchmark_ticker", "^GSPC")
            df = await provider_chain.get_price_history(ticker, days=history_days)
            result = await self.momentum.calculate(price_history=df, history_days=history_days)
            return result
        except Exception as e:
            logger.warning("Momentum calculation failed: %s", e)
            return self._unavailable("momentum")

    async def _calc_price_strength(
        self,
        provider_chain: Any,
        market_config: Any,
        history_days: int,
    ) -> IndicatorResult:
        """Calculate price strength: new highs / (highs + lows)."""
        try:
            market_id = getattr(market_config, "market_id", "sp500")
            breadth = await provider_chain.get_breadth_data(market_id)
            result = await self.highs_lows.calculate(breadth_data=breadth)
            return result
        except Exception as e:
            logger.warning("Price strength calculation failed: %s", e)
            return self._unavailable("price_strength")

    async def _calc_breadth(
        self,
        provider_chain: Any,
        market_config: Any,
        history_days: int,
    ) -> IndicatorResult:
        """Calculate breadth: advancing / (advancing + declining)."""
        try:
            market_id = getattr(market_config, "market_id", "sp500")
            breadth = await provider_chain.get_breadth_data(market_id)
            result = await self.breadth.calculate(breadth_data=breadth)
            return result
        except Exception as e:
            logger.warning("Breadth calculation failed: %s", e)
            return self._unavailable("breadth")

    async def _calc_put_call(
        self,
        provider_chain: Any,
        market_config: Any,
        history_days: int,
    ) -> IndicatorResult:
        """Calculate put/call ratio (inverted)."""
        try:
            ticker = getattr(market_config, "options_proxy", "SPY")
            options = await provider_chain.get_options_data(ticker)
            result = await self.put_call.calculate(options_data=options)
            return result
        except Exception as e:
            logger.warning("Put/call calculation failed: %s", e)
            return self._unavailable("put_call")

    async def _calc_credit_spreads(
        self,
        provider_chain: Any,
        market_config: Any,
        history_days: int,
    ) -> IndicatorResult:
        """Calculate credit spreads (inverted)."""
        try:
            series_id = getattr(market_config, "credit_spread_proxy", "BAMLH0A0HYM2")
            credit = await provider_chain.get_credit_spreads(series_id)
            result = await self.credit.calculate(credit_data=credit)
            return result
        except Exception as e:
            logger.warning("Credit spread calculation failed: %s", e)
            return self._unavailable("credit_spreads")

    async def _calc_volatility(
        self,
        provider_chain: Any,
        market_config: Any,
        history_days: int,
    ) -> IndicatorResult:
        """Calculate VIX score (inverted)."""
        try:
            vix_ticker = getattr(market_config, "volatility_proxy", "^VIX")
            df = await provider_chain.get_price_history(vix_ticker, days=history_days)
            result = await self.volatility.calculate(vix_history=df)
            return result
        except Exception as e:
            logger.warning("Volatility calculation failed: %s", e)
            return self._unavailable("volatility")

    async def _calc_safe_haven(
        self,
        provider_chain: Any,
        market_config: Any,
        history_days: int,
    ) -> IndicatorResult:
        """Calculate safe haven demand (inverted)."""
        try:
            haven_assets = await provider_chain.get_safe_haven_assets()
            result = await self.safe_haven.calculate(
                equity_returns=None,
                safe_haven_returns=haven_assets,
            )
            return result
        except Exception as e:
            logger.warning("Safe haven calculation failed: %s", e)
            return self._unavailable("safe_haven")

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------

    def _assemble_score(
        self,
        components: List[IndicatorResult],
    ) -> Tuple[float, DataQualityReport]:
        """Assemble final score from components with weight redistribution.

        Algorithm:
        1. Identify available components (score is not None)
        2. Sum their original weights
        3. Redistribute: each available component's effective weight =
           original_weight / sum_of_available_weights
        4. Score = sum(effective_score * effective_weight)
        5. Confidence penalized for each missing component
        """
        available = [c for c in components if c.available and c.score is not None]
        missing = [c.name for c in components if not c.available or c.score is None]

        if not available:
            # No data at all — return neutral with zero confidence
            return 50.0, DataQualityReport(
                overall_confidence=0.0,
                sources_used=0,
                sources_available=7,
                missing_components=[c.name for c in components],
                substituted_components=[],
                stale_data_warnings=["No data available for any component"],
                data_freshness_minutes=9999,
            )

        # Sum original weights of available components
        available_weight_sum = sum(self.COMPONENT_WEIGHTS.get(c.name, 0.0) for c in available)

        if available_weight_sum == 0:
            return 50.0, DataQualityReport(
                overall_confidence=0.0,
                sources_used=0,
                sources_available=7,
                missing_components=missing,
                substituted_components=[],
                stale_data_warnings=["Weight sum is zero"],
                data_freshness_minutes=9999,
            )

        # Calculate effective weights and composite score
        score = 0.0
        for comp in available:
            original_weight = self.COMPONENT_WEIGHTS.get(comp.name, 0.0)
            effective_weight = original_weight / available_weight_sum
            score += comp.score * effective_weight  # type: ignore[operator]

        # Clamp to valid range
        score = max(0.0, min(100.0, score))

        # Build quality report
        confidence = self._calc_confidence(available, missing)
        quality = DataQualityReport(
            overall_confidence=confidence,
            sources_used=len(available),
            sources_available=7,
            missing_components=missing,
            substituted_components=[],
            stale_data_warnings=[],
            data_freshness_minutes=0,  # Would be set from actual provider timestamps
        )

        return score, quality

    def _calc_confidence(
        self,
        available: List[IndicatorResult],
        missing: List[str],
    ) -> float:
        """Calculate confidence based on component availability.

        Start at 100, apply penalties:
        - Missing component: -10 each (max -70)
        - Clamp at 0
        """
        confidence = 100.0
        confidence -= len(missing) * 10.0
        return max(0.0, confidence)

    def _unavailable(self, name: str) -> IndicatorResult:
        """Create an unavailable indicator result."""
        return IndicatorResult(
            name=name,
            score=None,
            raw_value=None,
            available=False,
            direction="neutral",
            description=f"{name}: data unavailable",
            data_source="none",
        )

    @staticmethod
    def get_regime(score: float) -> Tuple[Regime, str]:
        """Map a 0-100 score to regime enum and label."""
        if score <= 20:
            return Regime.MP1_CAPITULATION, "Capitulation"
        elif score <= 40:
            return Regime.MP2_DEFENSIVE, "Defensive"
        elif score <= 60:
            return Regime.MP3_NEUTRAL, "Neutral"
        elif score <= 80:
            return Regime.MP4_RISK_ON, "Risk-On"
        else:
            return Regime.MP5_EUPHORIA, "Euphoria"
