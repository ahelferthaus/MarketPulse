"""
Explanation Engine

Generates human-readable explanations for MarketPulse readings.

Produces:
- Today's bottom line (one sentence)
- What changed (day-over-day comparison)
- What's driving the score (top contributors)
- What to watch (forward-looking cues)
- Data confidence note

The ExplanationEngine uses rule-based templates to produce natural-sounding
text without requiring an LLM. This ensures deterministic, fast, and free
explanation generation for every reading.

Template system:
    Explanations are assembled from fragments based on regime, direction,
    and top drivers. Fragments are combined with transitions to create
    coherent sentences.
"""
import logging
from typing import Dict, List, Optional

from backend.domain.score import MarketPulseScore, ScoreDriver, Regime

logger = logging.getLogger(__name__)


class ExplanationEngine:
    """Generates plain-English explanations from score data.

    The explanation engine transforms structured score data into
    human-readable narratives. It uses a template-based approach
    that produces consistent, natural-sounding text.

    All text generation is deterministic and rule-based — no LLM
    calls, no API dependencies, no latency.
    """

    # Regime-specific language templates
    REGIME_LANGUAGE: Dict[str, Dict[str, str]] = {
        "mp1_capitulation": {
            "label": "in extreme risk-off",
            "tone": "risk-off",
            "descriptor": "Extreme risk-off is driving markets.",
        },
        "mp2_defensive": {
            "label": "defensive",
            "tone": "caution",
            "descriptor": "Markets are in a defensive posture.",
        },
        "mp3_neutral": {
            "label": "balanced",
            "tone": "neutral",
            "descriptor": "Markets are in a balanced state.",
        },
        "mp4_risk_on": {
            "label": "risk-on",
            "tone": "optimism",
            "descriptor": "Markets are in risk-on mode.",
        },
        "mp5_euphoria": {
            "label": "euphoric",
            "tone": "exuberance",
            "descriptor": "Markets are showing signs of euphoria.",
        },
    }

    # Driver-specific language
    DRIVER_LANGUAGE: Dict[str, Dict[str, str]] = {
        "momentum": {
            "bullish": "strong price momentum",
            "bearish": "weak price momentum",
            "neutral": "stable momentum",
        },
        "price_strength": {
            "bullish": "broad participation in new highs",
            "bearish": "weak breadth with many new lows",
            "neutral": "mixed price action",
        },
        "breadth": {
            "bullish": "broad market participation",
            "bearish": "narrow market breadth",
            "neutral": "average market breadth",
        },
        "put_call": {
            "bullish": "low put/call ratio indicating complacency",
            "bearish": "elevated put/call ratio indicating hedging",
            "neutral": "neutral options positioning",
        },
        "credit_spreads": {
            "bullish": "tight credit spreads",
            "bearish": "widening credit spreads",
            "neutral": "stable credit conditions",
        },
        "volatility": {
            "bullish": "low volatility environment",
            "bearish": "elevated volatility",
            "neutral": "moderate volatility",
        },
        "safe_haven": {
            "bullish": "weak safe-haven demand",
            "bearish": "strong safe-haven flows",
            "neutral": "balanced safe-haven flows",
        },
        "panic": {
            "bullish": "",  # Not bullish
            "bearish": "panic-level risk-off in media",
            "neutral": "",
        },
        "caution": {
            "bullish": "",
            "bearish": "cautious media tone",
            "neutral": "measured media coverage",
        },
        "uncertainty": {
            "bullish": "",
            "bearish": "high uncertainty in narratives",
            "neutral": "clear market narratives",
        },
        "optimism": {
            "bullish": "optimistic media sentiment",
            "bearish": "",
            "neutral": "",
        },
        "complacency": {
            "bullish": "complacent risk appetite",
            "bearish": "",
            "neutral": "",
        },
        "euphoria": {
            "bullish": "euphoric media coverage",
            "bearish": "",  # Actually a warning sign
            "neutral": "",
        },
    }

    # Direction transitions
    DIRECTION_PHRASES: Dict[str, Dict[str, str]] = {
        "rising": {
            "mp1_capitulation": "improving from extreme lows",
            "mp2_defensive": "climbing out of defensive territory",
            "mp3_neutral": "rising toward risk-on",
            "mp4_risk_on": "continuing to climb",
            "mp5_euphoria": "pushing deeper into euphoric territory",
        },
        "falling": {
            "mp1_capitulation": "deteriorating further",
            "mp2_defensive": "slipping into more defensive posture",
            "mp3_neutral": "slipping toward defensive",
            "mp4_risk_on": "retreating from risk-on levels",
            "mp5_euphoria": "cooling from euphoric highs",
        },
        "stable": {
            "mp1_capitulation": "holding at extreme lows",
            "mp2_defensive": "remaining defensive",
            "mp3_neutral": "holding steady",
            "mp4_risk_on": "holding risk-on levels",
            "mp5_euphoria": "holding at euphoric extremes",
        },
    }

    def __init__(self):
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate(
        self,
        current_score: MarketPulseScore,
        previous_score: Optional[MarketPulseScore],
    ) -> Dict[str, str]:
        """Generate all explanation fields.

        Args:
            current_score: Current MarketPulseScore snapshot
            previous_score: Previous day's score (for comparison)

        Returns:
            Dict with:
                - bottom_line: One-sentence summary
                - what_changed: Day-over-day comparison
                - drivers: List of top contributor descriptions
                - what_to_watch: Forward-looking cues
                - confidence_note: Data quality note
        """
        return {
            "bottom_line": self._generate_bottom_line(current_score),
            "what_changed": self._generate_what_changed(current_score, previous_score),
            "drivers": self._generate_drivers(current_score),
            "what_to_watch": self._generate_what_to_watch(current_score),
            "confidence_note": self._generate_confidence_note(current_score),
        }

    # ------------------------------------------------------------------
    # Bottom line (one-sentence summary)
    # ------------------------------------------------------------------

    def _generate_bottom_line(self, score: MarketPulseScore) -> str:
        """Generate one-sentence summary of the current reading.

        Template:
            "Markets are [regime_label], driven by [top_driver] and [second_driver]."

        Falls back to simpler templates when driver data is sparse.
        """
        regime_info = self.REGIME_LANGUAGE.get(score.regime.value, self.REGIME_LANGUAGE["mp3_neutral"])

        # Get top 2 drivers
        top_drivers = self._get_top_drivers(score.drivers, n=2)

        if not top_drivers:
            # Minimal explanation when no driver data
            return f"Markets are {regime_info['label']} with a composite score of {score.composite_score:.0f}."

        if len(top_drivers) == 1:
            driver_text = self._describe_driver(top_drivers[0])
            return f"Markets are {regime_info['label']}, driven by {driver_text}."

        # Two drivers
        driver1_text = self._describe_driver(top_drivers[0])
        driver2_text = self._describe_driver(top_drivers[1])

        # Combine with appropriate transition
        transitions = [", supported by ", ", with ", ", while ", " and "]
        transition = transitions[hash(driver1_text) % len(transitions)]

        return f"Markets are {regime_info['label']}, driven by {driver1_text}{transition}{driver2_text}."

    # ------------------------------------------------------------------
    # What changed (day-over-day)
    # ------------------------------------------------------------------

    def _generate_what_changed(
        self,
        current: MarketPulseScore,
        previous: Optional[MarketPulseScore],
    ) -> str:
        """Compare current reading to previous reading.

        Describes the direction and magnitude of change, and identifies
        which sub-indices moved the most.
        """
        if previous is None:
            return "No previous reading available for comparison."

        # Composite change
        composite_change = current.composite_score - previous.composite_score
        direction = "rose" if composite_change > 0 else "fell" if composite_change < 0 else "was unchanged"

        # Sub-index changes
        classic_change = current.classic_score - previous.classic_score
        narrative_change = current.narrative_score - previous.narrative_score
        positioning_change = current.positioning_score - previous.positioning_score

        changes = [
            ("Classic", classic_change),
            ("Narrative", narrative_change),
            ("Positioning", positioning_change),
        ]
        changes.sort(key=lambda x: abs(x[1]), reverse=True)

        # Build sentence
        parts = [f"The composite score {direction} {abs(composite_change):.1f} point{'s' if abs(composite_change) != 1 else ''} to {current.composite_score:.1f}."]

        # Mention the biggest mover
        biggest_name, biggest_change = changes[0]
        if abs(biggest_change) >= 1.0:
            biggest_direction = "gained" if biggest_change > 0 else "lost"
            parts.append(f"The {biggest_name} index led the move, {biggest_direction} {abs(biggest_change):.1f} point{'s' if abs(biggest_change) != 1 else ''}.")

        # Mention second mover if significant
        if len(changes) > 1 and abs(changes[1][1]) >= 1.0:
            name, change = changes[1]
            direction2 = "gained" if change > 0 else "lost"
            parts.append(f"The {name} index {direction2} {abs(change):.1f} point{'s' if abs(change) != 1 else ''}.")

        return " ".join(parts)

    # ------------------------------------------------------------------
    # Drivers (top contributors)
    # ------------------------------------------------------------------

    def _generate_drivers(self, score: MarketPulseScore) -> List[str]:
        """Generate descriptions of top contributing factors.

        Returns a list of plain-English strings describing what
        is driving the score, ordered by contribution magnitude.
        """
        if not score.drivers:
            # Generate generic drivers from sub-scores
            return self._generate_generic_drivers(score)

        descriptions = []
        for driver in sorted(score.drivers, key=lambda d: abs(d.contribution), reverse=True)[:4]:
            direction_word = "supporting" if driver.contribution > 0 else "weighing on"
            magnitude = "strongly" if abs(driver.contribution) > 10 else "moderately" if abs(driver.contribution) > 5 else "slightly"
            descriptions.append(f"{driver.description} is {magnitude} {direction_word} the score.")

        return descriptions if descriptions else self._generate_generic_drivers(score)

    def _generate_generic_drivers(self, score: MarketPulseScore) -> List[str]:
        """Generate driver descriptions from sub-scores when no driver data."""
        drivers = []

        if score.classic_score >= 70:
            drivers.append("Strong market data readings are supporting the score.")
        elif score.classic_score <= 30:
            drivers.append("Weak market data readings are weighing on the score.")

        if score.narrative_score >= 70:
            drivers.append("Bullish media sentiment is providing support.")
        elif score.narrative_score <= 30:
            drivers.append("Bearish media sentiment is creating headwinds.")

        if score.positioning_score >= 70:
            drivers.append("Risk-on positioning signals are contributing.")
        elif score.positioning_score <= 30:
            drivers.append("Defensive positioning is dragging the score lower.")

        if not drivers:
            drivers.append("Mixed signals across market data, narrative, and positioning.")

        return drivers

    # ------------------------------------------------------------------
    # What to watch (forward-looking cues)
    # ------------------------------------------------------------------

    def _generate_what_to_watch(self, score: MarketPulseScore) -> str:
        """Generate forward-looking guidance.

        Provides context about what could change the score and
        key levels or events to monitor.
        """
        regime_value = score.regime.value
        direction = score.direction

        cues = []

        # Regime-specific cues
        if regime_value == "mp1_capitulation":
            cues.append("Watch for signs of selling exhaustion or a volume panic.")
            cues.append("Extreme risk-off can persist — look for breadth thrusts to signal a turn.")
        elif regime_value == "mp2_defensive":
            cues.append("Monitor credit spreads and VIX for signs of stabilization.")
            cues.append("A break above 50 would signal a shift to neutral territory.")
        elif regime_value == "mp3_neutral":
            cues.append("The score could move in either direction from here.")
            cues.append("Watch for momentum breaks or narrative shifts to signal the next move.")
        elif regime_value == "mp4_risk_on":
            cues.append("Monitor for signs of overheating in breadth or sentiment.")
            cues.append("A drop below 60 would signal a retreat from risk-on.")
        elif regime_value == "mp5_euphoria":
            cues.append("Extreme readings often precede corrections — watch for divergences.")
            cues.append("Monitor put/call ratios and volatility for early warning signs.")

        # Direction cue
        if direction == "rising":
            cues.append("The rising trend suggests improving conditions if it continues.")
        elif direction == "falling":
            cues.append("The falling trend warrants caution if it accelerates.")

        # Confidence caveat
        if score.confidence < 50:
            cues.append("Low data confidence means this reading may shift significantly as more data arrives.")

        return " ".join(cues[:3])  # Limit to 3 cues

    # ------------------------------------------------------------------
    # Confidence note
    # ------------------------------------------------------------------

    def _generate_confidence_note(self, score: MarketPulseScore) -> str:
        """Generate data confidence explanation."""
        if score.confidence >= 90:
            return "High data confidence — all primary sources are live and current."
        elif score.confidence >= 70:
            return "Good data confidence — most sources are available with minor gaps."
        elif score.confidence >= 50:
            return "Moderate confidence — some components are estimated or delayed."
        elif score.confidence >= 30:
            return "Low confidence — significant data gaps, treat as preliminary."
        else:
            return "Minimal confidence — mostly stub data, reading is indicative only."

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _get_top_drivers(self, drivers: List[ScoreDriver], n: int = 2) -> List[ScoreDriver]:
        """Get top N drivers by absolute contribution."""
        if not drivers:
            return []
        sorted_drivers = sorted(drivers, key=lambda d: abs(d.contribution), reverse=True)
        return sorted_drivers[:n]

    def _describe_driver(self, driver: ScoreDriver) -> str:
        """Convert a ScoreDriver to plain English description."""
        lang = self.DRIVER_LANGUAGE.get(driver.component, {})
        direction_key = driver.direction if driver.direction in ("bullish", "bearish", "neutral") else "neutral"
        description = lang.get(direction_key, f"{driver.component} ({driver.direction})")

        if description:
            return description

        # Fallback
        return f"{driver.component} ({driver.direction})"
