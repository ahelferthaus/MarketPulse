"""
NLP Query Parser for MarketPulse

Enables natural language queries like:
- "How nervous am I today?"
- "How excited about upside opportunities?"
- "Is the market fearful enough to buy?"
- "What's the sentiment vs last week?"

Pipeline:
1. Intent classification (descriptive/diagnostic/comparative/predictive)
2. Sentiment keyword extraction with orientation scores
3. Temporal resolution
4. Thematic focus
5. Comparative structure detection

Produces structured ParsedQuery objects consumed by the scoring engine
and explanation generators.
"""

import re
from typing import Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field


class ParsedQuery(BaseModel):
    """Structured representation of a natural language query.

    Attributes:
        intent: Query intent — descriptive | diagnostic | comparative | predictive.
        sentiment_orientation: Net sentiment orientation in [-1.0, +1.0],
            derived from extracted sentiment keywords.
        temporal_scope: Time period referenced — today | yesterday |
            last_week | last_month | forward.
        is_comparative: True if the query contains a comparison (e.g., "vs").
        comparison_period: The period being compared against, if any.
        thematic_focus: Thematic subject of the query (e.g., "upside",
            "safe havens", "volatility").
        market_id: Target market identifier (default: "sp500").
        raw_query: Original raw query string.
    """

    intent: str = Field(
        default="descriptive",
        description="descriptive | diagnostic | comparative | predictive",
    )
    sentiment_orientation: float = Field(
        default=0.0,
        ge=-1.0,
        le=1.0,
        description="Net sentiment orientation from extracted keywords",
    )
    temporal_scope: str = Field(
        default="today",
        description="today | yesterday | last_week | last_month | forward",
    )
    is_comparative: bool = Field(default=False)
    comparison_period: Optional[str] = Field(default=None)
    thematic_focus: Optional[str] = Field(default=None)
    market_id: str = Field(default="sp500")
    raw_query: str = Field(default="")


class QueryParser:
    """Parses natural language queries into structured sentiment queries.

    Implements a rule-based NLP pipeline for intent classification,
    sentiment keyword extraction, temporal resolution, and thematic
    focus detection. No external LLM dependencies — fully deterministic.

    Example::

        parser = QueryParser()
        result = parser.parse("How nervous am I today vs last week?")
        print(result.sentiment_orientation)  # -0.65 (nervous)
        print(result.is_comparative)         # True ("vs" detected)
        print(result.temporal_scope)         # "today"
        print(result.comparison_period)      # "last_week"
    """

    # --- Sentiment keyword lexicon with orientation scores (-1.0 to +1.0) ---
    SENTIMENT_KEYWORDS: Dict[str, float] = {
        # Fear-intense (-0.9 to -1.0)
        "terrified": -0.95,
        "panic": -0.95,
        "crash": -0.95,
        "collapse": -0.95,
        "meltdown": -0.95,
        "bloodbath": -0.95,
        "capitulation": -0.90,
        # Fear-moderate (-0.5 to -0.8)
        "nervous": -0.65,
        "worried": -0.60,
        "concerned": -0.55,
        "cautious": -0.50,
        "defensive": -0.55,
        "fearful": -0.70,
        "scared": -0.75,
        # Neutral-anxiety (-0.2 to +0.2)
        "uncertain": 0.0,
        "mixed": 0.0,
        "confused": 0.0,
        "waiting": -0.1,
        # Greed-moderate (+0.5 to +0.8)
        "optimistic": 0.65,
        "hopeful": 0.60,
        "constructive": 0.55,
        "positive": 0.55,
        "confident": 0.70,
        "bullish": 0.75,
        "excited": 0.70,
        # Greed-intense (+0.9 to +1.0)
        "euphoric": 0.95,
        "ecstatic": 0.95,
        "bubble": 0.90,
        "mania": 0.95,
        "unstoppable": 0.90,
        "euphoria": 0.95,
        "greedy": 0.85,
    }

    # --- Intent classification patterns ---
    INTENT_PATTERNS: Dict[str, List[str]] = {
        "comparative": [
            r"\bvs\b",
            r"\bversus\b",
            r"\bcompared?\s+to\b",
            r"\bcompared?\s+with\b",
            r"\bbetter\s+than\b",
            r"\bworse\s+than\b",
            r"\bdifference\b",
        ],
        "predictive": [
            r"\bwill\b",
            r"\bgonna\b",
            r"\bgoing\s+to\b",
            r"\bpredict\b",
            r"\bforecast\b",
            r"\bexpect\b",
            r"\boutlook\b",
            r"\bforward\b",
            r"\bfuture\b",
            r"\bnext\s+(week|month|year|quarter)\b",
        ],
        "diagnostic": [
            r"\bwhy\b",
            r"\bhow\s+come\b",
            r"\bwhat\s+is\s+driving\b",
            r"\bwhat\s+caused\b",
            r"\breason\b",
            r"\bexplain\b",
        ],
        "descriptive": [
            r"\bhow\s+is\b",
            r"\bwhat\s+is\b",
            r"\bwhat.s\s+the\b",
            r"\btell\s+me\b",
            r"\bdescribe\b",
        ],
    }

    # --- Temporal resolution patterns ---
    TEMPORAL_PATTERNS: Dict[str, List[str]] = {
        "today": [
            r"\btoday\b",
            r"\bnow\b",
            r"\bcurrent\b",
            r"\bat\s+the\s+moment\b",
        ],
        "yesterday": [
            r"\byesterday\b",
            r"\blast\s+session\b",
            r"\bprevious\s+day\b",
        ],
        "last_week": [
            r"\blast\s+week\b",
            r"\bprevious\s+week\b",
            r"\bweek\s+ago\b",
        ],
        "last_month": [
            r"\blast\s+month\b",
            r"\bprevious\s+month\b",
            r"\bmonth\s+ago\b",
        ],
        "forward": [
            r"\bnext\s+week\b",
            r"\bnext\s+month\b",
            r"\bnext\s+year\b",
            r"\bcoming\b",
            r"\bahead\b",
            r"\bforward\b",
            r"\bfuture\b",
            r"\boutlook\b",
        ],
    }

    # --- Thematic focus patterns ---
    THEME_PATTERNS: Dict[str, List[str]] = {
        "upside": [
            r"\bupside\b",
            r"\bopportunit",
            r"\brally\b",
            r"\b rally",
            r"\bbull\b",
            r"\bgains?\b",
            r"\brally\b",
            r"\bbreakout\b",
        ],
        "downside": [
            r"\bdownside\b",
            r"\brisk\b",
            r"\bdrawdown\b",
            r"\bcorrection\b",
            r"\bdecline\b",
            r"\bfall\b",
            r"\bcrash\b",
        ],
        "safe_havens": [
            r"\bsafe\s+haven",
            r"\btreasur",
            r"\bgold\b",
            r"\bdollar\b",
            r"\bbond\b",
        ],
        "volatility": [
            r"\bvolatil",
            r"\bVIX\b",
            r"\bchoppy\b",
            r"\buncertain",
        ],
        "credit": [
            r"\bcredit\b",
            r"\bspread\b",
            r"\bjunk\b",
            r"\bhigh.yield\b",
            r"\bhy\b",
        ],
        "momentum": [
            r"\bmomentum\b",
            r"\btrend\b",
            r"\bmoving\s+average\b",
            r"\bma\b",
        ],
    }

    # --- Market identification patterns ---
    MARKET_PATTERNS: Dict[str, List[str]] = {
        "sp500": [
            r"\bsp500\b",
            r"\bs.p\s*500\b",
            r"\bs&p\s*500\b",
            r"\bspx\b",
            r"\bspy\b",
        ],
        "nasdaq100": [
            r"\bnasdaq\b",
            r"\bndx\b",
            r"\bqqq\b",
            r"\btech\b",
        ],
        "russell2000": [
            r"\brussell\b",
            r"\brut\b",
            r"\biwm\b",
            r"\bsmall.cap\b",
        ],
        "dow": [
            r"\bdow\b",
            r"\bdjia\b",
            r"\bdia\b",
            r"\bindustrial\b",
        ],
    }

    def parse(self, query: str, market_id: str = "sp500") -> ParsedQuery:
        """Parse a natural language query into a structured ParsedQuery.

        Executes the full NLP pipeline: intent classification, sentiment
        keyword extraction, temporal resolution, thematic focus detection,
        and market identification.

        Args:
            query: The raw natural language query string.
            market_id: Default market to use if none detected in query.

        Returns:
            ParsedQuery with all structured fields populated.
        """
        if not query or not query.strip():
            return ParsedQuery(
                intent="descriptive",
                sentiment_orientation=0.0,
                temporal_scope="today",
                market_id=market_id,
                raw_query=query,
            )

        raw_lower = query.lower()

        # Step 1: Intent classification
        intent = self._classify_intent(raw_lower)

        # Step 2: Sentiment keyword extraction
        sentiment_orientation = self._extract_sentiment(raw_lower)

        # Step 3: Temporal resolution
        temporal_scope = self._resolve_temporal(raw_lower)

        # Step 4: Comparative structure detection
        is_comparative, comparison_period = self._detect_comparison(
            raw_lower, temporal_scope
        )

        # Step 5: Thematic focus
        thematic_focus = self._detect_thematic_focus(raw_lower)

        # Step 6: Market identification
        detected_market = self._detect_market(raw_lower)
        if detected_market:
            market_id = detected_market

        return ParsedQuery(
            intent=intent,
            sentiment_orientation=sentiment_orientation,
            temporal_scope=temporal_scope,
            is_comparative=is_comparative,
            comparison_period=comparison_period,
            thematic_focus=thematic_focus,
            market_id=market_id,
            raw_query=query,
        )

    # ------------------------------------------------------------------
    # Pipeline steps (internal)
    # ------------------------------------------------------------------

    def _classify_intent(self, query_lower: str) -> str:
        """Classify query intent using pattern matching.

        Priority order: comparative > predictive > diagnostic > descriptive.
        Comparative is checked first because it can co-occur with others.
        """
        for intent, patterns in self.INTENT_PATTERNS.items():
            if any(re.search(p, query_lower) for p in patterns):
                return intent
        return "descriptive"

    def _extract_sentiment(self, query_lower: str) -> float:
        """Extract sentiment keywords and compute net orientation.

        Computes the average of all matched keyword scores. Returns 0.0
        if no sentiment keywords are found.
        """
        scores: List[float] = []
        for keyword, score in self.SENTIMENT_KEYWORDS.items():
            if keyword in query_lower:
                scores.append(score)

        if not scores:
            return 0.0

        return sum(scores) / len(scores)

    def _resolve_temporal(self, query_lower: str) -> str:
        """Resolve temporal scope from query text.

        Defaults to "today" if no temporal marker is found.
        """
        for scope, patterns in self.TEMPORAL_PATTERNS.items():
            if any(re.search(p, query_lower) for p in patterns):
                return scope
        return "today"

    def _detect_comparison(
        self, query_lower: str, temporal_scope: str
    ) -> Tuple[bool, Optional[str]]:
        """Detect comparative structure and comparison period.

        Returns a tuple of (is_comparative, comparison_period). The
        comparison period is inferred from temporal patterns found in
        the query, excluding the primary temporal_scope.
        """
        is_comparative = any(
            re.search(p, query_lower)
            for p in self.INTENT_PATTERNS["comparative"]
        )

        if not is_comparative:
            return False, None

        # Find all temporal markers; use the non-primary one as comparison
        all_temporals: List[str] = []
        for scope, patterns in self.TEMPORAL_PATTERNS.items():
            if scope != temporal_scope and any(
                re.search(p, query_lower) for p in patterns
            ):
                all_temporals.append(scope)

        comparison_period = all_temporals[0] if all_temporals else None
        return True, comparison_period

    def _detect_thematic_focus(self, query_lower: str) -> Optional[str]:
        """Detect the thematic focus of the query.

        Returns the first matched theme or None if no theme is detected.
        """
        for theme, patterns in self.THEME_PATTERNS.items():
            if any(re.search(p, query_lower) for p in patterns):
                return theme
        return None

    def _detect_market(self, query_lower: str) -> Optional[str]:
        """Detect market reference in the query.

        Returns the first matched market_id or None if no market is
        explicitly referenced.
        """
        for market, patterns in self.MARKET_PATTERNS.items():
            if any(re.search(p, query_lower) for p in patterns):
                return market
        return None

    def get_dominant_sentiment_label(self, orientation: float) -> str:
        """Map a sentiment orientation score to a human-readable label.

        Args:
            orientation: Sentiment orientation in [-1.0, +1.0].

        Returns:
            Human-readable sentiment label (e.g., "Fearful", "Neutral").
        """
        if orientation <= -0.9:
            return "Extreme Fear"
        elif orientation <= -0.6:
            return "Fearful"
        elif orientation <= -0.3:
            return "Cautious"
        elif orientation < 0.4:
            return "Neutral"
        elif orientation < 0.7:
            return "Constructive"
        elif orientation < 0.9:
            return "Optimistic"
        else:
            return "Euphoric"
