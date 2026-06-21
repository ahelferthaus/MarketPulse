import pytest
from datetime import datetime, timezone

from backend.nlp.sentiment_model import SentimentModel
from backend.nlp.query_parser import QueryParser, ParsedQuery
from backend.domain.article import Article


def test_sentiment_panic():
    model = SentimentModel()
    scores = model.analyze("CRASH! The market is collapsing! Total meltdown!")
    assert scores["panic"] > scores["optimism"]
    assert scores["panic"] > 20


def test_sentiment_optimism():
    model = SentimentModel()
    scores = model.analyze("Strong growth and rally! Bullish expansion!")
    assert scores["optimism"] > scores["panic"]


def test_sentiment_empty_text():
    model = SentimentModel()
    scores = model.analyze("")
    for val in scores.values():
        assert val == 0.0


def test_sentiment_neutral():
    model = SentimentModel()
    scores = model.analyze("The market is open today. Trading continues.")
    # Neutral text should have low scores across dimensions
    assert scores["panic"] < 50
    assert scores["optimism"] < 50


def test_analyze_article():
    model = SentimentModel()
    article = Article(
        id="test-1",
        timestamp=datetime.now(timezone.utc),
        source="test",
        title="Market crashes",
        url="https://example.com/test",
        description="",
        sentiment_score=50.0,
    )
    result = model.analyze_article(article)
    # Should update sentiment scores
    assert result.panic_score > 0
    assert result.sentiment_score != 50.0


def test_analyze_article_optimistic():
    model = SentimentModel()
    article = Article(
        id="test-2",
        timestamp=datetime.now(timezone.utc),
        source="test",
        title="Strong growth and rally ahead",
        url="https://example.com/test2",
        description="",
        sentiment_score=50.0,
    )
    result = model.analyze_article(article)
    assert result.optimism_score > 0


def test_analyze_batch():
    model = SentimentModel()
    texts = [
        "Market crashing! Sell everything!",
        "Bullish growth ahead!",
        "Mixed signals today.",
    ]
    results = model.analyze_batch(texts)
    assert len(results) == 3
    assert results[0]["panic"] > results[0]["optimism"]
    assert results[1]["optimism"] > results[1]["panic"]


def test_lexicon_loaded():
    model = SentimentModel()
    assert "panic" in model.lexicon
    assert "optimism" in model.lexicon
    assert "caution" in model.lexicon
    assert "euphoria" in model.lexicon
    assert "complacency" in model.lexicon
    assert "uncertainty" in model.lexicon
    assert len(model.lexicon["panic"]) > 10


def test_finbert_check():
    model = SentimentModel()
    # Should run without error, either True or False depending on install
    assert isinstance(model.finbert_available, bool)


# ──────────────────────────────────────────────────────────────────
# QueryParser Tests
# ──────────────────────────────────────────────────────────────────


def test_query_parser_basic():
    parser = QueryParser()
    result = parser.parse("How is the market today?")
    assert isinstance(result, ParsedQuery)
    assert result.intent == "descriptive"
    assert result.temporal_scope == "today"
    assert result.market_id == "sp500"
    assert not result.is_comparative


def test_query_parser_nervous():
    parser = QueryParser()
    result = parser.parse("How nervous am I today?")
    assert result.sentiment_orientation == pytest.approx(-0.65)
    assert result.intent == "descriptive"
    assert result.temporal_scope == "today"
    assert parser.get_dominant_sentiment_label(result.sentiment_orientation) == "Fearful"


def test_query_parser_excited_upside():
    parser = QueryParser()
    result = parser.parse("How excited about upside opportunities?")
    assert result.sentiment_orientation == pytest.approx(0.70)
    assert result.thematic_focus == "upside"
    assert parser.get_dominant_sentiment_label(result.sentiment_orientation) == "Optimistic"


def test_query_parser_comparative():
    parser = QueryParser()
    result = parser.parse("How nervous am I today vs last week?")
    assert result.is_comparative is True
    assert result.temporal_scope == "today"
    assert result.comparison_period == "last_week"
    assert result.sentiment_orientation == pytest.approx(-0.65)


def test_query_parser_predictive():
    parser = QueryParser()
    result = parser.parse("What will the market do next week?")
    assert result.intent == "predictive"
    assert result.temporal_scope == "forward"


def test_query_parser_diagnostic():
    parser = QueryParser()
    result = parser.parse("Why is the market crashing?")
    assert result.intent == "diagnostic"
    assert result.sentiment_orientation == pytest.approx(-0.95)


def test_query_parser_empty():
    parser = QueryParser()
    result = parser.parse("")
    assert result.intent == "descriptive"
    assert result.sentiment_orientation == 0.0
    assert result.temporal_scope == "today"


def test_query_parser_market_detection():
    parser = QueryParser()
    result = parser.parse("How is the nasdaq doing today?")
    assert result.market_id == "nasdaq100"

    result = parser.parse("What's the Russell 2000 outlook?")
    assert result.market_id == "russell2000"

    result = parser.parse("How is the Dow Jones today?")
    assert result.market_id == "dow"


def test_query_parser_thematic_focus():
    parser = QueryParser()
    result = parser.parse("What's happening with safe havens?")
    assert result.thematic_focus == "safe_havens"

    result = parser.parse("How is volatility looking?")
    assert result.thematic_focus == "volatility"

    result = parser.parse("Tell me about credit spreads")
    assert result.thematic_focus == "credit"


def test_query_parser_intense_fear():
    parser = QueryParser()
    result = parser.parse("Terrified about a total meltdown!")
    assert result.sentiment_orientation == pytest.approx(-0.95)
    assert parser.get_dominant_sentiment_label(result.sentiment_orientation) == "Extreme Fear"


def test_query_parser_intense_greed():
    parser = QueryParser()
    result = parser.parse("Ecstatic about this bubble mania!")
    # ecstatic(+0.95) + bubble(+0.90) + mania(+0.95) averaged = +0.933
    assert result.sentiment_orientation == pytest.approx(0.933, abs=0.01)
    assert parser.get_dominant_sentiment_label(result.sentiment_orientation) == "Euphoric"


def test_query_parser_forward_looking():
    parser = QueryParser()
    result = parser.parse("What upside opportunities are ahead?")
    assert result.temporal_scope == "forward"
    assert result.thematic_focus == "upside"
    # No sentiment keywords in this query → neutral orientation
    assert result.sentiment_orientation == 0.0


def test_query_parser_comparative_versus():
    parser = QueryParser()
    result = parser.parse("Is the market better than last month?")
    assert result.is_comparative is True
    # "last_month" is both the temporal_scope and implied comparison period
    assert result.temporal_scope == "last_month"


def test_query_parser_sentiment_labels():
    parser = QueryParser()
    assert parser.get_dominant_sentiment_label(-0.95) == "Extreme Fear"
    assert parser.get_dominant_sentiment_label(-0.65) == "Fearful"
    assert parser.get_dominant_sentiment_label(-0.40) == "Cautious"
    assert parser.get_dominant_sentiment_label(0.0) == "Neutral"
    assert parser.get_dominant_sentiment_label(0.30) == "Neutral"
    assert parser.get_dominant_sentiment_label(0.40) == "Constructive"
    assert parser.get_dominant_sentiment_label(0.55) == "Constructive"
    assert parser.get_dominant_sentiment_label(0.75) == "Optimistic"
    assert parser.get_dominant_sentiment_label(0.95) == "Euphoric"
