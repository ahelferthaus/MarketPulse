"""
Confidence Scoring

Calculates overall data quality confidence (0-100) for a MarketPulse reading.

The confidence score reflects the reliability of the underlying data.
Higher confidence means more components had fresh, high-quality data.
Lower confidence indicates missing data, stale feeds, or source issues.

Penalty structure:
- Missing component:           -10 each
- Substituted/stub data:       -5 each
- Component substitution:      varies by component (see SUBSTITUTION_PENALTIES)
- Stale data (> 4 hours):      -15
- Stale data (> 24 hours):     -25
- Source down:                 -20
- Low article count:           -10
- Low provider availability:   proportional penalty

Component substitution penalties (research-derived):
- Put/Call Ratio substitutions:  -15%
- Junk Bond Spread substitutions: -10%
- Safe Haven Demand substitutions: -20%
- VIX substitutions:             -25%

Confidence bands:
    90-100: Excellent  — All primary sources live, fresh data
    70-89:  Good       — Minor gaps or slight staleness
    50-69:  Fair       — Some components missing or stale
    30-49:  Poor       — Significant data gaps
    0-29:   Minimal    — Mostly stubs or stale data
"""
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

from backend.domain.score import DataQualityReport, Regime, SourceStatus
from backend.domain.indicator import IndicatorResult

logger = logging.getLogger(__name__)


class ConfidenceScorer:
    """Scores data quality confidence for a MarketPulse reading.

    This is a deterministic scoring system. Given the same inputs,
    it always produces the same confidence score. The methodology
    is fully documented and auditable.

    Usage:
        scorer = ConfidenceScorer()
        report = scorer.calculate(
            components=indicator_results,
            provider_statuses=source_statuses,
            article_count=42,
        )
        print(report.overall_confidence)  # 0-100
    """

    # Penalty values (documented and auditable)
    PENALTIES: Dict[str, float] = {
        "missing_component": 10.0,
        "substituted_data": 5.0,
        "stale_4h": 15.0,
        "stale_24h": 25.0,
        "source_down": 20.0,
        "low_article_count": 10.0,
    }

    # Thresholds
    STALE_4H_MINUTES = 240    # 4 hours
    STALE_24H_MINUTES = 1440  # 24 hours
    MIN_ARTICLES = 5

    # Component substitution penalties keyed by unavailable component.
    # Each entry maps the substitution chain to a confidence penalty
    # percentage (negative value, applied multiplicatively).
    # Research-derived values reflecting relative information loss
    # when substituting each component type.
    SUBSTITUTION_PENALTIES: Dict[str, Dict[str, float]] = {
        "put_call": {
            "etf_options": -15.0,
            "index_futures_options": -15.0,
            "implied_vol_surface": -15.0,
        },
        "junk_bond_spread": {
            "broad_hy": -10.0,
            "ig_spread": -10.0,
            "sovereign_spread": -10.0,
        },
        "safe_haven": {
            "usd_treasury_proxy": -20.0,
            "currency_movement": -20.0,
            "omitted": -20.0,
        },
        "vix": {
            "regional_vol": -25.0,
            "realized_vol": -25.0,
            "omitted": -25.0,
        },
    }

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def calculate(
        self,
        components: List[IndicatorResult],
        provider_statuses: List[SourceStatus],
        article_count: int = 0,
        is_narrative: bool = False,
    ) -> DataQualityReport:
        """Calculate confidence score and quality report.

        Algorithm:
        1. Start at 100 (perfect confidence)
        2. Apply penalties for each quality issue found
        3. Clamp at 0 (never negative)
        4. Build structured quality report

        Args:
            components: List of indicator results from scoring
            provider_statuses: List of source/provider statuses
            article_count: Number of articles (for narrative scoring)
            is_narrative: Whether this is a narrative score (affects article penalty)

        Returns:
            DataQualityReport with overall confidence and details
        """
        penalties: List[Tuple[str, float]] = []

        # Step 1: Check component availability
        missing = [c.name for c in components if not c.available]
        substituted = [c.name for c in components if c.data_source == "stub"]

        for name in missing:
            penalties.append((f"missing:{name}", self.PENALTIES["missing_component"]))

        for name in substituted:
            penalties.append((f"substituted:{name}", self.PENALTIES["substituted_data"]))

        # Step 2: Check provider health
        for status in provider_statuses:
            if not status.available:
                penalties.append((f"source_down:{status.provider}", self.PENALTIES["source_down"]))

            # Check staleness
            if status.data_freshness_minutes is not None:
                if status.data_freshness_minutes > self.STALE_24H_MINUTES:
                    penalties.append((
                        f"stale_24h:{status.provider}",
                        self.PENALTIES["stale_24h"],
                    ))
                elif status.data_freshness_minutes > self.STALE_4H_MINUTES:
                    penalties.append((
                        f"stale_4h:{status.provider}",
                        self.PENALTIES["stale_4h"],
                    ))

        # Step 3: Check article count (for narrative)
        if is_narrative and article_count < self.MIN_ARTICLES:
            penalties.append(("low_article_count", self.PENALTIES["low_article_count"]))

        # Step 4: Calculate overall confidence
        total_penalty = sum(p for _, p in penalties)
        confidence = max(0.0, 100.0 - total_penalty)

        # Step 5: Build warnings list
        warnings = []
        for reason, penalty in penalties:
            if penalty >= self.PENALTIES["stale_24h"]:
                warnings.append(f"CRITICAL: {reason} (-{penalty:.0f})")
            elif penalty >= self.PENALTIES["stale_4h"]:
                warnings.append(f"WARNING: {reason} (-{penalty:.0f})")
            else:
                warnings.append(f"{reason} (-{penalty:.0f})")

        # Step 6: Determine data freshness
        freshness = self._compute_freshness(provider_statuses)

        sources_used = sum(1 for s in provider_statuses if s.available)
        sources_available = len(provider_statuses)

        report = DataQualityReport(
            overall_confidence=confidence,
            sources_used=sources_used,
            sources_available=max(sources_available, 1),
            missing_components=missing,
            substituted_components=substituted,
            stale_data_warnings=warnings,
            data_freshness_minutes=freshness,
        )

        logger.debug(
            "Confidence: %.1f (penalties=%d, total=%.1f, sources=%d/%d)",
            confidence, len(penalties), total_penalty, sources_used, sources_available,
        )

        return report

    def calculate_simple(
        self,
        available_count: int,
        total_count: int,
        stale_sources: int = 0,
        down_sources: int = 0,
        substituted_count: int = 0,
    ) -> float:
        """Simplified confidence calculation without full provider statuses.

        Convenience method for quick confidence estimates.

        Args:
            available_count: Number of available components
            total_count: Total number of expected components
            stale_sources: Number of stale data sources
            down_sources: Number of down sources
            substituted_count: Number of substituted components

        Returns:
            Confidence score 0-100
        """
        confidence = 100.0

        # Missing component penalty
        missing = total_count - available_count
        confidence -= missing * self.PENALTIES["missing_component"]

        # Substituted data penalty
        confidence -= substituted_count * self.PENALTIES["substituted_data"]

        # Stale data penalty
        confidence -= stale_sources * self.PENALTIES["stale_4h"]

        # Source down penalty
        confidence -= down_sources * self.PENALTIES["source_down"]

        return max(0.0, confidence)

    # ------------------------------------------------------------------
    # Regime mapping
    # ------------------------------------------------------------------

    @staticmethod
    def get_regime(score: float) -> Tuple[Regime, str]:
        """Map 0-100 score to regime enum and label.

        This is the canonical five-zone framework used across all
        MarketPulse indices. Uses empirically-derived asymmetric ranges
        based on historical frequency analysis of market conditions.

        Score ranges:
        - MP-1 (Capitulation): 0-24   (~8% historical frequency)
        - MP-2 (Defensive): 25-44    (~23% historical frequency)
        - MP-3 (Neutral): 45-55      (~38% historical frequency)
        - MP-4 (Risk-On): 56-75      (~24% historical frequency)
        - MP-5 (Euphoria): 76-100    (~7% historical frequency)

        Args:
            score: 0-100 composite score

        Returns:
            Tuple of (Regime enum, human-readable label)
        """
        if score <= 24:
            return Regime.MP1_CAPITULATION, "Capitulation"
        elif score <= 44:
            return Regime.MP2_DEFENSIVE, "Defensive"
        elif score <= 55:
            return Regime.MP3_NEUTRAL, "Neutral"
        elif score <= 75:
            return Regime.MP4_RISK_ON, "Risk-On"
        else:
            return Regime.MP5_EUPHORIA, "Euphoria"

    @staticmethod
    def get_regime_from_label(label: str) -> Regime:
        """Get regime enum from string label.

        Args:
            label: One of "Capitulation", "Defensive", "Neutral", "Risk-On", "Euphoria"

        Returns:
            Regime enum value
        """
        mapping = {
            "Capitulation": Regime.MP1_CAPITULATION,
            "Defensive": Regime.MP2_DEFENSIVE,
            "Neutral": Regime.MP3_NEUTRAL,
            "Risk-On": Regime.MP4_RISK_ON,
            "Euphoria": Regime.MP5_EUPHORIA,
        }
        return mapping.get(label, Regime.MP3_NEUTRAL)

    @staticmethod
    def get_direction(current: float, previous: Optional[float]) -> str:
        """Determine score direction based on current vs previous.

        Args:
            current: Current score
            previous: Previous score (None if no history)

        Returns:
            "rising", "falling", or "stable"
        """
        if previous is None:
            return "stable"
        diff = current - previous
        if abs(diff) < 1.0:
            return "stable"
        return "rising" if diff > 0 else "falling"

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _compute_freshness(self, provider_statuses: List[SourceStatus]) -> int:
        """Compute overall data freshness in minutes.

        Returns the maximum (worst) freshness across all providers,
        representing the age of the stalest data in the calculation.
        """
        if not provider_statuses:
            return 9999

        max_freshness = 0
        for status in provider_statuses:
            if status.data_freshness_minutes is not None:
                max_freshness = max(max_freshness, status.data_freshness_minutes)

        return max_freshness if max_freshness > 0 else 9999

    def get_confidence_band(self, confidence: float) -> str:
        """Map confidence score to quality band.

        Args:
            confidence: 0-100 confidence score

        Returns:
            Quality band label
        """
        if confidence >= 90:
            return "Excellent"
        elif confidence >= 70:
            return "Good"
        elif confidence >= 50:
            return "Fair"
        elif confidence >= 30:
            return "Poor"
        else:
            return "Minimal"

    def calculate_substitution_penalty(
        self,
        component: str,
        substitution: str,
    ) -> float:
        """Calculate the confidence penalty for a component substitution.

        Looks up the penalty from SUBSTITUTION_PENALTIES based on the
        unavailable component and the substitution used.

        Args:
            component: The unavailable component name (e.g., 'put_call').
            substitution: The substitution applied (e.g., 'etf_options').

        Returns:
            Penalty value as a positive float (0 if no penalty defined).
        """
        penalties = self.SUBSTITUTION_PENALTIES.get(component, {})
        penalty = penalties.get(substitution, 0.0)
        return abs(penalty)

    def calculate_total_substitution_penalty(
        self,
        substitutions: Dict[str, str],
    ) -> float:
        """Calculate total confidence penalty from multiple substitutions.

        Args:
            substitutions: Dict mapping unavailable component names to
                the substitution applied for each.

        Returns:
            Total penalty value (capped at 100).
        """
        total = 0.0
        for component, substitution in substitutions.items():
            total += self.calculate_substitution_penalty(component, substitution)
        return min(total, 100.0)

    def explain_confidence(self, report: DataQualityReport) -> str:
        """Generate human-readable explanation of confidence score.

        Args:
            report: DataQualityReport to explain

        Returns:
            Plain-English confidence explanation
        """
        band = self.get_confidence_band(report.overall_confidence)

        parts = [f"Data confidence is {report.overall_confidence:.0f}/100 ({band})."]

        if report.missing_components:
            parts.append(f"Missing: {', '.join(report.missing_components)}.")

        if report.substituted_components:
            parts.append(f"Using stubs: {', '.join(report.substituted_components)}.")

        if report.stale_data_warnings:
            critical = [w for w in report.stale_data_warnings if w.startswith("CRITICAL")]
            if critical:
                parts.append(f"Critical issues: {len(critical)}")

        parts.append(f"Sources: {report.sources_used}/{report.sources_available} available.")

        return " ".join(parts)
