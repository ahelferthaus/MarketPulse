"""
MarketPulse Positioning & Flows Index

Trading-market and positioning-driven index combining live Tier 1 data
with stub placeholders for Tier 2 premium data sources.

Tier 1 components (live):
- Put/call ratio          20%  (CBOE/FMP)
- VIX level               15%  (yfinance)
- Credit spreads          15%  (FRED)
- Equity/bond relative    20%  (yfinance)
- Safe haven flows        15%  (yfinance)

Tier 2 components (stub — return None, reduce confidence):
- ETF flows               5%   (needs premium API)
- Fund flows              5%   (needs premium API)
- Futures positioning     3%   (CFTC — delayed)
- Options skew            1%   (needs options data)
- Margin debt             1%   (FINRA — delayed)

Weight redistribution: When Tier 2 components are unavailable, their
weights are redistributed proportionally among Tier 1 components.
"""
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.domain.score import DataQualityReport
from backend.domain.indicator import IndicatorResult
from backend.indicators.put_call import PutCallIndicator
from backend.indicators.volatility import VolatilityIndicator
from backend.indicators.credit_spreads import CreditSpreadsIndicator
from backend.indicators.safe_haven import SafeHavenIndicator

logger = logging.getLogger(__name__)


class MarketPulsePositioning:
    """Calculates the MarketPulse Positioning & Flows index.

    The Positioning index measures how market participants are
    positioned through options activity, volatility expectations,
    credit spreads, and flow data.

    Score interpretation:
        0-20: Extreme defensive positioning (heavy hedging)
        20-40: Defensive positioning (risk-off flows)
        40-60: Neutral positioning (balanced)
        60-80: Risk-on positioning (bullish flows)
        80-100: Aggressive risk-on (crowded long, complacent)
    """

    # Full component weights (Tier 1 + Tier 2)
    COMPONENT_WEIGHTS: Dict[str, float] = {
        "put_call": 0.20,
        "vix": 0.15,
        "credit_spreads": 0.15,
        "equity_bond_relative": 0.20,
        "safe_haven_flows": 0.15,
        "etf_flows": 0.05,
        "fund_flows": 0.05,
        "futures_positioning": 0.03,
        "options_skew": 0.01,
        "margin_debt": 0.01,
    }

    # Tier classification
    TIER_1_COMPONENTS = {"put_call", "vix", "credit_spreads", "equity_bond_relative", "safe_haven_flows"}
    TIER_2_COMPONENTS = {"etf_flows", "fund_flows", "futures_positioning", "options_skew", "margin_debt"}

    def __init__(self):
        self.put_call = PutCallIndicator()
        self.volatility = VolatilityIndicator()
        self.credit = CreditSpreadsIndicator()
        self.safe_haven = SafeHavenIndicator()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def calculate(
        self,
        provider_chain: Any,   # ProviderChain instance
        market_config: Any,    # MarketConfig instance
    ) -> Tuple[float, List[IndicatorResult], DataQualityReport]:
        """Calculate Positioning score.

        Flow:
        1. Fetch positioning data from providers
        2. Calculate all available components (Tier 1 + Tier 2)
        3. Redistribute weights for unavailable components
        4. Weighted average of available components
        5. Return score, components, quality report

        Args:
            provider_chain: ProviderChain with configured providers
            market_config: Market configuration

        Returns:
            Tuple of (composite_score, component_results, data_quality_report)
        """
        logger.info("Starting Positioning index calculation for market=%s", getattr(market_config, "market_id", "unknown"))

        # Step 1 & 2: Calculate all components
        components: List[IndicatorResult] = []

        # Tier 1: Live components
        components.append(await self._calc_put_call(provider_chain, market_config))
        components.append(await self._calc_vix(provider_chain, market_config))
        components.append(await self._calc_credit_spreads(provider_chain, market_config))
        components.append(await self._calc_equity_bond_relative(provider_chain, market_config))
        components.append(await self._calc_safe_haven_flows(provider_chain, market_config))

        # Tier 2: Stub components (attempt to fetch, but expect None)
        components.append(await self._calc_etf_flows(provider_chain, market_config))
        components.append(await self._calc_fund_flows(provider_chain, market_config))
        components.append(await self._calc_futures_positioning(provider_chain, market_config))
        components.append(await self._calc_options_skew(provider_chain, market_config))
        components.append(await self._calc_margin_debt(provider_chain, market_config))

        # Step 3 & 4: Assemble with weight redistribution
        score, quality_report = self._assemble_score(components)

        logger.info(
            "Positioning index complete: score=%.2f, tier1_available=%d/5, tier2_available=%d/5, confidence=%.1f",
            score,
            sum(1 for c in components if c.available and c.name in self.TIER_1_COMPONENTS),
            sum(1 for c in components if c.available and c.name in self.TIER_2_COMPONENTS),
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
                Expected keys: 'put_call_series', 'vix_series', 'spread_series',
                'equity_prices', 'bond_prices', 'safe_haven_prices'

        Returns:
            Same tuple as calculate() but without async/await.
        """
        components: List[IndicatorResult] = []

        # Put/call ratio
        pc = data_bundle.get("put_call_series")
        if pc and len(pc) >= 20:
            score = self.put_call.calculate_sync(pc)
            components.append(IndicatorResult(
                name="put_call", score=score, raw_value=pc[-1],
                raw_unit="ratio", available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Put/call ratio: {score:.1f}" if score else "Unavailable",
                data_source="historical", invert=True,
            ))
        else:
            components.append(self._unavailable("put_call"))

        # VIX
        vix = data_bundle.get("vix_series")
        if vix and len(vix) >= 20:
            score = self.volatility.calculate_sync(vix)
            components.append(IndicatorResult(
                name="vix", score=score, raw_value=vix[-1],
                raw_unit="index", available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"VIX: {score:.1f}" if score else "Unavailable",
                data_source="historical", invert=True,
            ))
        else:
            components.append(self._unavailable("vix"))

        # Credit spreads
        spreads = data_bundle.get("spread_series")
        if spreads and len(spreads) >= 20:
            score = self.credit.calculate_sync(spreads)
            components.append(IndicatorResult(
                name="credit_spreads", score=score, raw_value=spreads[-1],
                raw_unit="bps", available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Credit spreads: {score:.1f}" if score else "Unavailable",
                data_source="historical", invert=True,
            ))
        else:
            components.append(self._unavailable("credit_spreads"))

        # Equity/bond relative
        eq = data_bundle.get("equity_prices")
        bn = data_bundle.get("bond_prices")
        if eq and bn and len(eq) >= 21 and len(bn) >= 21:
            eq_ret = (eq[-1] - eq[-21]) / eq[-21]
            bn_ret = (bn[-1] - bn[-21]) / bn[-21]
            relative = eq_ret - bn_ret
            score = max(0.0, min(100.0, (relative + 0.15) / 0.30 * 100))
            components.append(IndicatorResult(
                name="equity_bond_relative", score=score,
                raw_value=relative, raw_unit="percent", available=True,
                direction="bullish" if score > 60 else "bearish" if score < 40 else "neutral",
                description=f"Equity/bond relative: {score:.1f}",
                data_source="historical", invert=False,
            ))
        else:
            components.append(self._unavailable("equity_bond_relative"))

        # Safe haven flows
        eq2 = data_bundle.get("equity_prices")
        sh = data_bundle.get("safe_haven_prices")
        if eq2 and sh and len(eq2) >= 21 and len(sh) >= 21:
            score = self.safe_haven.calculate_sync(eq2, sh)
            components.append(IndicatorResult(
                name="safe_haven_flows", score=score,
                raw_value=None, raw_unit="percent", available=score is not None,
                direction="bullish" if score and score > 60 else "bearish" if score and score < 40 else "neutral",
                description=f"Safe haven flows: {score:.1f}" if score else "Unavailable",
                data_source="historical", invert=True,
            ))
        else:
            components.append(self._unavailable("safe_haven_flows"))

        # Tier 2 stubs (always unavailable in sync mode)
        for name in self.TIER_2_COMPONENTS:
            components.append(self._stub_unavailable(name))

        score, quality_report = self._assemble_score(components)
        return score, components, quality_report

    # ------------------------------------------------------------------
    # Component calculators
    # ------------------------------------------------------------------

    async def _calc_put_call(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 1: Put/call ratio (inverted)."""
        try:
            ticker = getattr(market_config, "options_proxy", "SPY")
            options = await provider_chain.get_options_data(ticker)
            return await self.put_call.calculate(options_data=options)
        except Exception as e:
            logger.debug("Put/call unavailable: %s", e)
            return self._unavailable("put_call")

    async def _calc_vix(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 1: VIX level (inverted)."""
        try:
            vix_ticker = getattr(market_config, "volatility_proxy", "^VIX")
            df = await provider_chain.get_price_history(vix_ticker, days=252)
            return await self.volatility.calculate(vix_history=df)
        except Exception as e:
            logger.debug("VIX unavailable: %s", e)
            return self._unavailable("vix")

    async def _calc_credit_spreads(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 1: Credit spreads (inverted)."""
        try:
            series_id = getattr(market_config, "credit_spread_proxy", "BAMLH0A0HYM2")
            credit = await provider_chain.get_credit_spreads(series_id)
            return await self.credit.calculate(credit_data=credit)
        except Exception as e:
            logger.debug("Credit spreads unavailable: %s", e)
            return self._unavailable("credit_spreads")

    async def _calc_equity_bond_relative(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 1: Equity vs bond relative performance."""
        try:
            benchmark = getattr(market_config, "benchmark_ticker", "^GSPC")
            equity_df = await provider_chain.get_price_history(benchmark, days=30)
            bond_df = await provider_chain.get_price_history("TLT", days=30)

            # Calculate 20-day returns
            eq_prices = list(equity_df["close"]) if hasattr(equity_df, "__getitem__") else equity_df
            bond_prices = list(bond_df["close"]) if hasattr(bond_df, "__getitem__") else bond_df

            if len(eq_prices) >= 21 and len(bond_prices) >= 21:
                eq_ret = (eq_prices[-1] - eq_prices[-21]) / eq_prices[-21]
                bn_ret = (bond_prices[-1] - bond_prices[-21]) / bond_prices[-21]
                relative = eq_ret - bn_ret
                score = max(0.0, min(100.0, (relative + 0.15) / 0.30 * 100))
                return IndicatorResult(
                    name="equity_bond_relative", score=score,
                    raw_value=relative, raw_unit="percent", available=True,
                    direction="bullish" if score > 60 else "bearish" if score < 40 else "neutral",
                    description=f"Equity/bond relative return: {score:.1f}",
                    data_source="yfinance", invert=False,
                )
        except Exception as e:
            logger.debug("Equity/bond relative unavailable: %s", e)
        return self._unavailable("equity_bond_relative")

    async def _calc_safe_haven_flows(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 1: Safe haven demand flows (inverted)."""
        try:
            benchmark = getattr(market_config, "benchmark_ticker", "^GSPC")
            equity_df = await provider_chain.get_price_history(benchmark, days=30)
            haven_df = await provider_chain.get_safe_haven_assets()
            return await self.safe_haven.calculate(
                equity_returns=list(equity_df["close"]) if hasattr(equity_df, "__getitem__") else equity_df,
                safe_haven_returns=haven_df,
            )
        except Exception as e:
            logger.debug("Safe haven flows unavailable: %s", e)
            return self._unavailable("safe_haven_flows")

    # Tier 2 stubs
    async def _calc_etf_flows(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 2: ETF flows (stub)."""
        return self._stub_unavailable("etf_flows")

    async def _calc_fund_flows(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 2: Fund flows (stub)."""
        return self._stub_unavailable("fund_flows")

    async def _calc_futures_positioning(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 2: Futures positioning CFTC (stub)."""
        return self._stub_unavailable("futures_positioning")

    async def _calc_options_skew(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 2: Options skew (stub)."""
        return self._stub_unavailable("options_skew")

    async def _calc_margin_debt(self, provider_chain: Any, market_config: Any) -> IndicatorResult:
        """Tier 2: Margin debt FINRA (stub)."""
        return self._stub_unavailable("margin_debt")

    # ------------------------------------------------------------------
    # Assembly
    # ------------------------------------------------------------------

    def _assemble_score(
        self,
        components: List[IndicatorResult],
    ) -> Tuple[float, DataQualityReport]:
        """Assemble final score with weight redistribution.

        Algorithm:
        1. Separate available and unavailable components
        2. Sum weights of available components
        3. Redistribute: effective_weight = original / available_sum
        4. Score = sum(score * effective_weight)
        5. Confidence adjusted for Tier 2 stubs
        """
        available = [c for c in components if c.available and c.score is not None]
        unavailable = [c.name for c in components if not c.available or c.score is None]
        tier2_unavailable = [c for c in unavailable if c in self.TIER_2_COMPONENTS]
        tier1_unavailable = [c for c in unavailable if c in self.TIER_1_COMPONENTS]

        if not available:
            return 50.0, DataQualityReport(
                overall_confidence=0.0,
                sources_used=0, sources_available=10,
                missing_components=unavailable,
                substituted_components=[],
                stale_data_warnings=["No positioning data available"],
                data_freshness_minutes=9999,
            )

        # Sum original weights of available
        available_weight_sum = sum(self.COMPONENT_WEIGHTS.get(c.name, 0.0) for c in available)

        if available_weight_sum == 0:
            return 50.0, DataQualityReport(
                overall_confidence=0.0,
                sources_used=0, sources_available=10,
                missing_components=unavailable,
                substituted_components=[],
                stale_data_warnings=["Weight sum is zero"],
                data_freshness_minutes=9999,
            )

        # Calculate effective weights and composite
        score = 0.0
        for comp in available:
            original_weight = self.COMPONENT_WEIGHTS.get(comp.name, 0.0)
            effective_weight = original_weight / available_weight_sum
            score += comp.score * effective_weight  # type: ignore[operator]

        score = max(0.0, min(100.0, score))

        # Confidence: penalize Tier 1 missing more heavily than Tier 2
        confidence = 100.0
        confidence -= len(tier1_unavailable) * 15.0
        confidence -= len(tier2_unavailable) * 3.0  # Minor penalty for Tier 2 stubs
        confidence = max(0.0, confidence)

        warnings = []
        if tier2_unavailable:
            warnings.append(f"{len(tier2_unavailable)} Tier 2 components using stubs")
        if tier1_unavailable:
            warnings.append(f"{len(tier1_unavailable)} Tier 1 components unavailable")

        quality = DataQualityReport(
            overall_confidence=confidence,
            sources_used=len(available),
            sources_available=10,
            missing_components=unavailable,
            substituted_components=list(self.TIER_2_COMPONENTS) if tier2_unavailable else [],
            stale_data_warnings=warnings,
            data_freshness_minutes=0,
        )

        return score, quality

    def _unavailable(self, name: str) -> IndicatorResult:
        """Create an unavailable Tier 1 indicator result."""
        return IndicatorResult(
            name=name, score=None, raw_value=None,
            available=False, direction="neutral",
            description=f"{name}: data unavailable",
            data_source="none",
        )

    def _stub_unavailable(self, name: str) -> IndicatorResult:
        """Create a Tier 2 stub indicator result."""
        return IndicatorResult(
            name=name, score=None, raw_value=None,
            available=False, direction="neutral",
            description=f"{name}: Tier 2 stub (premium data required)",
            data_source="stub",
        )
