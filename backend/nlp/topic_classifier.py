"""
Topic Classifier
Classifies financial text into topics using keyword matching.

Topics: macro, fed, earnings, inflation, credit, geopolitics, ai_tech,
        consumer, banking_stress, recession, liquidity, valuation
"""

import logging
import re
from typing import Dict, List, Set

logger = logging.getLogger(__name__)


class TopicClassifier:
    """Rule-based topic classification for financial text."""

    # Topic keyword mappings
    TOPIC_KEYWORDS: Dict[str, List[str]] = {
        "macro": [
            "gdp", "gross domestic product", "economic growth", "recession",
            "expansion", "contraction", "business cycle", "leading indicators",
            "pmi", "ism", "economic data", "macroeconomic",
        ],
        "fed": [
            "federal reserve", "fed", "fomc", "interest rate", "rate cut",
            "rate hike", "monetary policy", "jerome powell", "pivot",
            "tightening", "easing", "hawkish", "dovish", "pause",
            "dot plot", "forward guidance", "balance sheet",
        ],
        "earnings": [
            "earnings", "revenue", "profit", "eps", "beat", "miss",
            "guidance", "quarterly results", "income statement", "bottom line",
            "top line", "operating margin", "net income", "forecast",
            "earnings season", "conference call", "outlook",
        ],
        "inflation": [
            "inflation", "cpi", "consumer price index", "ppi", "producer price",
            "deflation", "disinflation", "stagflation", "hyperinflation",
            "core inflation", "headline inflation", "price level",
            "wage growth", "cost of living", "purchasing power",
        ],
        "credit": [
            "credit spread", "high yield", "investment grade", "junk bond",
            "default rate", "credit risk", "corporate bond", "treasury yield",
            "yield curve", "inversion", "credit default swap", "cds",
            "bond market", "fixed income", "debt issuance",
        ],
        "geopolitics": [
            "war", "conflict", "sanctions", "trade war", "tariff",
            "election", "political", "geopolitical", "diplomatic",
            "tension", "regime change", "policy uncertainty", "brexit",
            "china-us", "middle east", "ukraine", "taiwan",
        ],
        "ai_tech": [
            "artificial intelligence", "ai", "machine learning", "chatgpt",
            "large language model", "llm", "semiconductor", "chip",
            "nvidia", "tech stock", "technology sector", "innovation",
            "disruption", "cloud computing", "saas", "data center",
            "automation", "robotics", "deep learning",
        ],
        "consumer": [
            "consumer spending", "retail sales", "consumer confidence",
            "housing market", "mortgage", "auto sales", "personal income",
            "savings rate", "discretionary", "consumer staples",
            "unemployment", "job market", "labor market", "wages",
            "shopping", "demand",
        ],
        "banking_stress": [
            "bank failure", "bank run", "deposit outflow", "svb",
            "credit suisse", "regional bank", "banking crisis",
            "liquidity crisis", "capital ratio", "stress test",
            "fdic", "bailout", "systemic risk", "financial stability",
            "leverage", "counterparty",
        ],
        "recession": [
            "recession", "hard landing", "soft landing", "no landing",
            "yield curve inversion", "sahm rule", "leading economic index",
            "negative gdp", "contraction", " downturn", "slowdown",
            "stagflation", "depression",
        ],
        "liquidity": [
            "liquidity", "market depth", "trading volume", "bid-ask spread",
            "repo market", "interbank", "funding stress", "dollar shortage",
            "quantitative tightening", "qt", "balance sheet runoff",
            "money supply", "m2", "cash", "dry powder",
        ],
        "valuation": [
            "valuation", "pe ratio", "price to earnings", "price to sales",
            "market cap", "enterprise value", "overvalued", "undervalued",
            "expensive", "cheap", "forward multiple", "trailing pe",
            "shiller pe", " cape ", "equity risk premium", "erp",
            "mean reversion", "historical average",
        ],
    }

    def __init__(self):
        """Initialize the topic classifier with compiled keyword patterns."""
        self._compiled: Dict[str, re.Pattern] = {}
        self._compile_patterns()
        logger.info("TopicClassifier initialized with %d topics", len(self.TOPIC_KEYWORDS))

    def _compile_patterns(self) -> None:
        """Compile regex patterns for efficient matching."""
        for topic, keywords in self.TOPIC_KEYWORDS.items():
            # Create a pattern that matches any of the keywords as whole words
            escaped = [re.escape(kw) for kw in keywords]
            pattern = r"(?:" + "|".join(escaped) + r")"
            self._compiled[topic] = re.compile(pattern, re.IGNORECASE)

    def classify(self, text: str) -> List[str]:
        """Return list of topic labels for the text.

        Args:
            text: Input text to classify.

        Returns:
            List of topic strings that match the text.
        """
        if not text or not text.strip():
            return []

        matched_topics: List[str] = []
        text_lower = text.lower()

        for topic, pattern in self._compiled.items():
            if pattern.search(text_lower):
                matched_topics.append(topic)

        return matched_topics

    def classify_with_scores(self, text: str) -> Dict[str, int]:
        """Return topic labels with match counts.

        Args:
            text: Input text to classify.

        Returns:
            Dict mapping topic names to keyword match counts.
        """
        if not text or not text.strip():
            return {}

        scores: Dict[str, int] = {}
        text_lower = text.lower()

        for topic, pattern in self._compiled.items():
            matches = len(pattern.findall(text_lower))
            if matches > 0:
                scores[topic] = matches

        return scores

    def get_primary_topic(self, text: str) -> str:
        """Return the single most relevant topic.

        Args:
            text: Input text to classify.

        Returns:
            The topic with the most keyword matches, or "general" if none match.
        """
        scores = self.classify_with_scores(text)
        if not scores:
            return "general"
        return max(scores, key=scores.get)

    def classify_batch(self, texts: List[str]) -> List[List[str]]:
        """Classify a batch of texts.

        Args:
            texts: List of input texts.

        Returns:
            List of topic label lists, one per input text.
        """
        return [self.classify(text) for text in texts]
