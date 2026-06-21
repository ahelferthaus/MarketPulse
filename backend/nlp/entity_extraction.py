"""Entity extraction — stub for future NER implementation."""

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class EntityExtractor:
    """Named entity extractor for financial text.

    Currently returns an empty list. Future implementation will use
    spaCy or a fine-tuned financial NER model to extract:
    - Companies/organizations
    - People (executives, Fed officials)
    - Financial instruments
    - Dates and monetary values
    - Locations/markets
    """

    def __init__(self):
        """Initialize the entity extractor."""
        self._spacy_available = self._check_spacy()
        if self._spacy_available:
            logger.info("spaCy available for entity extraction")
        else:
            logger.info("Entity extraction running in stub mode (spaCy not installed)")

    def _check_spacy(self) -> bool:
        """Check if spaCy is available."""
        try:
            import spacy  # noqa: F401
            return True
        except ImportError:
            return False

    def extract(self, text: str) -> List[Dict]:
        """Extract named entities from text.

        Args:
            text: Input text to extract entities from.

        Returns:
            List of entity dicts with keys: text, label, start, end.
            Currently returns an empty list.
        """
        if not text or not self._spacy_available:
            return []

        # Future implementation:
        # import spacy
        # nlp = spacy.load("en_core_web_sm")
        # doc = nlp(text)
        # return [
        #     {"text": ent.text, "label": ent.label_, "start": ent.start_char, "end": ent.end_char}
        #     for ent in doc.ents
        # ]

        return []

    def extract_companies(self, text: str) -> List[str]:
        """Extract company/organization names from text.

        Args:
            text: Input text.

        Returns:
            List of company names. Currently returns an empty list.
        """
        return []

    def extract_people(self, text: str) -> List[str]:
        """Extract person names from text.

        Args:
            text: Input text.

        Returns:
            List of person names. Currently returns an empty list.
        """
        return []

    def extract_tickers(self, text: str) -> List[str]:
        """Extract stock ticker symbols from text using regex.

        Args:
            text: Input text.

        Returns:
            List of uppercase ticker symbols.
        """
        import re

        if not text:
            return []

        # Match common ticker patterns: $AAPL, (NYSE: X), or standalone uppercase 1-5 chars
        patterns = [
            r"\$([A-Z]{1,5})",  # $AAPL
            r"\b(NYSE|NASDAQ|AMEX):\s*([A-Z]{1,5})\b",  # NYSE: AAPL
            r"\b([A-Z]{2,5})\b(?=\s+(?:stock|shares|equity|etf|index))",  # AAPL stock
        ]

        tickers: set = set()
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                if match.lastindex and match.group(match.lastindex):
                    tickers.add(match.group(match.lastindex))
                else:
                    tickers.add(match.group(1))

        return sorted(tickers)
