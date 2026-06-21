import pytest
from datetime import datetime, timezone

from backend.domain.score import Regime, MarketPulseScore, ScoreDriver, DataQualityReport
from backend.domain.market import MarketConfig, DEFAULT_MARKETS
from backend.domain.indicator import IndicatorResult


def test_regime_from_score():
    # Empirically-derived asymmetric ranges from research
    assert Regime.from_score(15) == Regime.MP1_CAPITULATION
    assert Regime.from_score(35) == Regime.MP2_DEFENSIVE
    assert Regime.from_score(50) == Regime.MP3_NEUTRAL
    assert Regime.from_score(65) == Regime.MP4_RISK_ON
    assert Regime.from_score(90) == Regime.MP5_EUPHORIA


def test_regime_boundaries():
    # MP-1 Capitulation: 0-24 (~8% frequency)
    assert Regime.from_score(0) == Regime.MP1_CAPITULATION
    assert Regime.from_score(24) == Regime.MP1_CAPITULATION
    # MP-2 Defensive: 25-44 (~23% frequency)
    assert Regime.from_score(25) == Regime.MP2_DEFENSIVE
    assert Regime.from_score(44) == Regime.MP2_DEFENSIVE
    # MP-3 Neutral: 45-55 (~38% frequency) — intentionally narrow
    assert Regime.from_score(45) == Regime.MP3_NEUTRAL
    assert Regime.from_score(55) == Regime.MP3_NEUTRAL
    # MP-4 Risk-On: 56-75 (~24% frequency)
    assert Regime.from_score(56) == Regime.MP4_RISK_ON
    assert Regime.from_score(75) == Regime.MP4_RISK_ON
    # MP-5 Euphoria: 76-100 (~7% frequency)
    assert Regime.from_score(76) == Regime.MP5_EUPHORIA
    assert Regime.from_score(100) == Regime.MP5_EUPHORIA


def test_default_markets_exist():
    assert "sp500" in DEFAULT_MARKETS
    assert "nasdaq100" in DEFAULT_MARKETS
    assert "russell2000" in DEFAULT_MARKETS
    assert "dow" in DEFAULT_MARKETS


def test_market_config_structure():
    sp500 = DEFAULT_MARKETS["sp500"]
    assert sp500.market_id == "sp500"
    assert sp500.name == "S&P 500"
    assert sp500.etf_proxy == "SPY"
    assert sp500.benchmark_ticker == "^GSPC"


def test_indicator_result_defaults():
    result = IndicatorResult(name="test", score=50.0)
    assert result.score == 50.0
    assert result.invert is False
    assert result.available is True
    assert result.weight == 1.0
    assert result.direction == "neutral"


def test_indicator_result_effective_score():
    result = IndicatorResult(name="test", score=75.0, available=True)
    assert result.effective_score == 75.0

    unavailable = IndicatorResult(name="test", score=None, available=False)
    assert unavailable.effective_score is None


def test_data_quality_report():
    report = DataQualityReport(
        overall_confidence=85.0,
        sources_used=5,
        sources_available=6,
        missing_components=["etf_flows"],
        substituted_components=[],
        stale_data_warnings=[],
        data_freshness_minutes=30,
    )
    assert report.overall_confidence == 85.0
    assert report.sources_used == 5
    assert report.sources_available == 6
    assert report.missing_components == ["etf_flows"]


def test_data_quality_report_defaults():
    report = DataQualityReport(overall_confidence=100.0)
    assert report.sources_used == 0
    assert report.sources_available == 0
    assert report.missing_components == []
    assert report.data_freshness_minutes == 0


def test_market_pulse_score_creation():
    score = MarketPulseScore(
        timestamp=datetime.now(timezone.utc),
        market_id="sp500",
        classic_score=62.0,
        narrative_score=55.0,
        positioning_score=58.0,
        composite_score=58.5,
        regime=Regime.MP4_RISK_ON,
    )
    assert score.market_id == "sp500"
    assert score.composite_score == 58.5
    assert score.regime == Regime.MP4_RISK_ON


def test_score_driver():
    driver = ScoreDriver(
        component="momentum",
        contribution=8.5,
        direction="bullish",
        description="Strong momentum above 125-day moving average",
    )
    assert driver.component == "momentum"
    assert driver.direction == "bullish"
    assert driver.contribution == 8.5
