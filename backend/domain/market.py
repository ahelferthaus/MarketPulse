"""Market configuration models for Westwood MarketPulse.

Defines market configurations, safe haven allocation rules, component availability
flags, and the default market universe (S&P 500, Nasdaq-100, Russell 2000, Dow).
"""

from __future__ import annotations

from typing import Dict, List

from pydantic import BaseModel, ConfigDict, Field


class SafeHavenConfig(BaseModel):
    """Safe haven asset allocation for a given market.

    Maps ticker symbols to their relative weights in the safe haven basket.
    Used by the Safe Haven Demand component of MarketPulse Classic.

    Attributes:
        assets: Dictionary mapping ticker symbol to weight (must sum to ~1.0).
        invert: If True, higher safe haven returns → lower score (fear signal).
    """

    model_config = ConfigDict(frozen=True)

    assets: Dict[str, float] = Field(
        default_factory=lambda: {"TLT": 0.4, "GLD": 0.4, "UUP": 0.2},
        description="Safe haven asset weights (must sum to ~1.0)",
    )
    invert: bool = Field(
        default=True,
        description="If True, higher safe haven returns indicate fear",
    )


class ComponentAvailability(BaseModel):
    """Component availability flags for a market.

    Indicates which indicator components are available for a given market.
    Used to adjust confidence scoring when components are missing.

    Attributes:
        momentum: Market momentum component (benchmark vs moving average).
        price_strength: New highs / (highs + lows) or proxy.
        breadth: Advancing/declining volume or percentage above MA.
        put_call: Put/call ratio from options data.
        credit_spreads: High-yield / investment-grade spread.
        volatility: VIX or equivalent volatility index.
        safe_haven: Safe haven demand (equity vs TLT/GLD/DXY basket).
        etf_flows: ETF flow data.
        fund_flows: Mutual fund flow data.
        futures_positioning: CFTC futures positioning data.
        prediction_markets: Prediction market data.
        options_skew: Options skew data.
        margin_debt: Margin debt statistics.
    """

    model_config = ConfigDict(frozen=True)

    momentum: bool = True
    price_strength: bool = True
    breadth: bool = True
    put_call: bool = True
    credit_spreads: bool = True
    volatility: bool = True
    safe_haven: bool = True
    etf_flows: bool = False
    fund_flows: bool = False
    futures_positioning: bool = False
    prediction_markets: bool = False
    options_skew: bool = False
    margin_debt: bool = False


class MarketConfig(BaseModel):
    """Configuration for a tracked market.

    Defines all market-specific parameters: benchmark tickers, ETF proxies,
    volatility references, credit spread series, safe haven basket composition,
    market-specific calibration bounds, and which components are available.

    Attributes:
        market_id: Short unique identifier (e.g., 'sp500').
        name: Human-readable market name (e.g., 'S&P 500').
        benchmark_ticker: Primary benchmark index ticker (e.g., '^GSPC').
        etf_proxy: Liquid ETF proxy for the benchmark (e.g., 'SPY').
        volatility_proxy: Volatility index ticker (e.g., '^VIX').
        options_proxy: Underlying ticker for options data (e.g., 'SPY').
        breadth_universe: List of constituent/proxy tickers for breadth calc.
        credit_spread_proxy: FRED series ID for credit spread data.
        safe_haven_assets: SafeHavenConfig for this market.
        normalization_window_days: Lookback window for rolling percentile.
        component_config: Which components are available for this market.
        confidence_penalties: Penalty factor per substituted/missing component.
        momentum_bounds: +/- percentage deviation bounds for normalization.
        volatility_regime: Volatility regime classification for calibration.
    """

    model_config = ConfigDict(frozen=True)

    market_id: str = Field(..., description="Short unique identifier, e.g. 'sp500'")
    name: str = Field(..., description="Human-readable market name, e.g. 'S&P 500'")
    benchmark_ticker: str = Field(..., description="Primary benchmark index ticker")
    etf_proxy: str = Field(..., description="Liquid ETF proxy for the benchmark")
    volatility_proxy: str = Field(..., description="Volatility index ticker")
    options_proxy: str = Field(..., description="Underlying ticker for options data")
    breadth_universe: List[str] = Field(
        ...,
        description="Constituent or proxy tickers for breadth calculation",
    )
    credit_spread_proxy: str = Field(
        ...,
        description="FRED series ID for credit spread data",
    )
    safe_haven_assets: SafeHavenConfig = Field(
        default_factory=SafeHavenConfig,
        description="Safe haven basket composition",
    )
    normalization_window_days: int = Field(
        default=1260,
        description="Lookback window for rolling percentile normalization (5 years)",
    )
    component_config: ComponentAvailability = Field(
        default_factory=ComponentAvailability,
        description="Which indicator components are available",
    )
    confidence_penalties: Dict[str, float] = Field(
        default_factory=dict,
        description="Penalty per substituted/missing component",
    )
    momentum_bounds: float = Field(
        default=0.15,
        description="Momentum normalization +/- bounds (e.g. 0.15 = ±15%%)",
    )
    volatility_regime: str = Field(
        default="standard",
        description="Volatility regime: standard | high_vol | emerging",
    )


# ── Default market configurations ───────────────────────────────────────────

DEFAULT_MARKETS: Dict[str, MarketConfig] = {
    "sp500": MarketConfig(
        market_id="sp500",
        name="S&P 500",
        benchmark_ticker="^GSPC",
        etf_proxy="SPY",
        volatility_proxy="^VIX",
        options_proxy="SPY",
        breadth_universe=["SPY", "IVV", "VOO", "XLK", "XLF", "XLV", "XLE"],
        credit_spread_proxy="BAMLH0A0HYM2",
        safe_haven_assets=SafeHavenConfig(
            assets={"TLT": 0.4, "GLD": 0.4, "UUP": 0.2},
            invert=True,
        ),
        normalization_window_days=1260,
        component_config=ComponentAvailability(
            momentum=True,
            price_strength=True,
            breadth=True,
            put_call=True,
            credit_spreads=True,
            volatility=True,
            safe_haven=True,
            etf_flows=False,
            fund_flows=False,
            futures_positioning=False,
            prediction_markets=False,
            options_skew=False,
            margin_debt=False,
        ),
        momentum_bounds=0.15,
        volatility_regime="standard",
    ),
    "nasdaq100": MarketConfig(
        market_id="nasdaq100",
        name="Nasdaq-100",
        benchmark_ticker="^NDX",
        etf_proxy="QQQ",
        volatility_proxy="^VXN",
        options_proxy="QQQ",
        breadth_universe=["QQQ", "IXIC", "AAPL", "MSFT", "GOOGL", "AMZN", "META"],
        credit_spread_proxy="BAMLH0A0HYM2",
        safe_haven_assets=SafeHavenConfig(
            assets={"TLT": 0.4, "GLD": 0.4, "UUP": 0.2},
            invert=True,
        ),
        normalization_window_days=1260,
        component_config=ComponentAvailability(
            momentum=True,
            price_strength=True,
            breadth=True,
            put_call=True,
            credit_spreads=True,
            volatility=True,
            safe_haven=True,
            etf_flows=False,
            fund_flows=False,
            futures_positioning=False,
            prediction_markets=False,
            options_skew=False,
            margin_debt=False,
        ),
        momentum_bounds=0.20,
        volatility_regime="high_vol",
    ),
    "russell2000": MarketConfig(
        market_id="russell2000",
        name="Russell 2000",
        benchmark_ticker="^RUT",
        etf_proxy="IWM",
        volatility_proxy="^RVX",
        options_proxy="IWM",
        breadth_universe=["IWM", "IWN", "IWO", "VTWO"],
        credit_spread_proxy="BAMLH0A0HYM2",
        safe_haven_assets=SafeHavenConfig(
            assets={"TLT": 0.4, "GLD": 0.4, "UUP": 0.2},
            invert=True,
        ),
        normalization_window_days=1260,
        component_config=ComponentAvailability(
            momentum=True,
            price_strength=True,
            breadth=True,
            put_call=True,
            credit_spreads=True,
            volatility=True,
            safe_haven=True,
            etf_flows=False,
            fund_flows=False,
            futures_positioning=False,
            prediction_markets=False,
            options_skew=False,
            margin_debt=False,
        ),
        momentum_bounds=0.18,
        volatility_regime="high_vol",
    ),
    "dow": MarketConfig(
        market_id="dow",
        name="Dow Jones Industrial Average",
        benchmark_ticker="^DJI",
        etf_proxy="DIA",
        volatility_proxy="^VIX",
        options_proxy="DIA",
        breadth_universe=["DIA", "SPY", "IVV", "XLK", "XLF", "XLV"],
        credit_spread_proxy="BAMLH0A0HYM2",
        safe_haven_assets=SafeHavenConfig(
            assets={"TLT": 0.4, "GLD": 0.4, "UUP": 0.2},
            invert=True,
        ),
        normalization_window_days=1260,
        component_config=ComponentAvailability(
            momentum=True,
            price_strength=True,
            breadth=True,
            put_call=True,
            credit_spreads=True,
            volatility=True,
            safe_haven=True,
            etf_flows=False,
            fund_flows=False,
            futures_positioning=False,
            prediction_markets=False,
            options_skew=False,
            margin_debt=False,
        ),
        momentum_bounds=0.15,
        volatility_regime="standard",
    ),
}
