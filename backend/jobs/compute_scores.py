# -*- coding: utf-8 -*-
"""Compute real MarketPulse scores — 20+ year backfill plus daily update.

Walks forward day by day per market using the platform's own point-in-time
calculators (no look-ahead) and writes the results to the DuckDB scores
table, which /scores/current and /history/scores serve directly. This
replaces the demo/random-walk fallbacks with a real, per-market series.

Data sources (cost-tiered):
  * Deep history — free: yfinance (index closes, VIX, TLT) + FRED (HY OAS).
  * Recent tail  — Bloomberg MCP server (http://localhost:8100) when the
    Terminal is up: a small PX_LAST pull for the last few sessions, merged
    over the free data. Falls back silently to yfinance when offline.

Components reconstructed per market: momentum, volatility, credit spreads,
safe haven. classic = mean(momentum, volatility, credit);
positioning = safe haven; composite = mean of all four.
narrative_score is stored as neutral 50 and EXCLUDED from the composite —
news sentiment cannot be reconstructed historically and accrues live only.

Usage:
  python -m backend.jobs.compute_scores            # incremental (recent tail)
  python -m backend.jobs.compute_scores --full     # full rebuild from 2003
"""
from __future__ import annotations

import argparse
import io
import logging
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.domain.score import MarketPulseScore, Regime
from backend.indicators.momentum import MomentumIndicator
from backend.indicators.volatility import VolatilityIndicator
from backend.indicators.credit_spreads import CreditSpreadsIndicator
from backend.indicators.safe_haven import SafeHavenIndicator
from backend.providers.bloomberg_mcp_provider import BloombergMCPProvider
from backend.storage.duckdb_store import DuckDBStore

logger = logging.getLogger(__name__)

WARMUP_START = "2001-06-01"   # rolling-window warmup before first score
EVAL_START = "2003-01-02"     # first scored day -> 23+ years of history

MARKETS = {
    "sp500":       {"yf": "^GSPC", "bbg": "SPX Index",  "label": "S&P 500"},
    "nasdaq100":   {"yf": "^NDX",  "bbg": "NDX Index",  "label": "Nasdaq 100"},
    "russell2000": {"yf": "^RUT",  "bbg": "RTY Index",  "label": "Russell 2000"},
    "dow":         {"yf": "^DJI",  "bbg": "INDU Index", "label": "Dow Jones"},
}
VIX_YF, VIX_BBG = "^VIX", "VIX Index"
HAVEN_YF, HAVEN_BBG = "TLT", "TLT US Equity"
FRED_HY_OAS = "BAMLH0A0HYM2"

BANDS = [(24, Regime.MP1_CAPITULATION, "Panic"),
         (44, Regime.MP2_DEFENSIVE, "Defensive"),
         (55, Regime.MP3_NEUTRAL, "Neutral"),
         (75, Regime.MP4_RISK_ON, "Risk-On"),
         (100, Regime.MP5_EUPHORIA, "Euphoria")]


def regime_for(score: float):
    for mx, reg, label in BANDS:
        if score <= mx:
            return reg, label
    return Regime.MP3_NEUTRAL, "Neutral"


def fetch_fred(series_id: str) -> pd.Series:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    with urllib.request.urlopen(url, timeout=30) as r:
        df = pd.read_csv(io.BytesIO(r.read()))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().set_index("date")["value"]


def fetch_yf() -> pd.DataFrame:
    import yfinance as yf
    tickers = [m["yf"] for m in MARKETS.values()] + [VIX_YF, HAVEN_YF]
    raw = yf.download(tickers, start=WARMUP_START, progress=False,
                      auto_adjust=True)["Close"]
    return raw.dropna(how="all").ffill()


async def merge_bloomberg_tail(prices: pd.DataFrame, days: int = 10) -> tuple[pd.DataFrame, bool]:
    """Overlay the last few sessions with Bloomberg MCP data when available.

    Deliberately tiny pull (6 tickers x ~10 days, PX_LAST daily) per the
    firm's Bloomberg-cost discipline; deep history stays on free sources.
    """
    bbg = BloombergMCPProvider()
    status = await bbg.get_source_status()
    if not status.available:
        logger.info("Bloomberg MCP not available — staying on free sources")
        return prices, False

    start = (datetime.now() - timedelta(days=days)).strftime("%Y%m%d")
    end = datetime.now().strftime("%Y%m%d")
    pairs = [(m["bbg"], m["yf"]) for m in MARKETS.values()]
    pairs += [(VIX_BBG, VIX_YF), (HAVEN_BBG, HAVEN_YF)]

    updated = 0
    for bbg_ticker, col in pairs:
        hist = await bbg.get_price_history_range(bbg_ticker, start, end)
        if hist is None or hist.empty or col not in prices.columns:
            continue
        for ts, px in hist["close"].items():
            prices.loc[pd.Timestamp(ts).normalize(), col] = float(px)
        updated += 1
    prices = prices.sort_index().ffill()
    logger.info("Bloomberg MCP overlay applied to %d of %d series", updated, len(pairs))
    return prices, updated > 0


def compute_market(market_id: str, cfg: dict, prices: pd.DataFrame,
                   oas: pd.Series, eval_start: pd.Timestamp,
                   bbg_live: bool) -> list[MarketPulseScore]:
    momentum, volatility = MomentumIndicator(), VolatilityIndicator()
    credit, haven = CreditSpreadsIndicator(), SafeHavenIndicator()

    px = prices[cfg["yf"]].dropna()
    vix = prices[VIX_YF].dropna()
    tlt = prices[HAVEN_YF].dropna()
    oas_d = oas.reindex(px.index).ffill().dropna()

    days = px.index[px.index >= eval_start]
    out: list[MarketPulseScore] = []
    composites: list[float] = []
    for day in days:
        comps = {
            "momentum": momentum.calculate_sync(px.loc[:day].tolist()[-500:]),
            "volatility": volatility.calculate_sync(vix.loc[:day].tolist()[-252:]),
            "credit": credit.calculate_sync(oas_d.loc[:day].tolist()[-252:]),
            "safe_haven": haven.calculate_sync(px.loc[:day].tolist()[-260:],
                                               tlt.loc[:day].tolist()[-260:]),
        }
        vals = [v for v in comps.values() if v is not None]
        if len(vals) < 3:
            continue
        composite = float(np.mean(vals))
        classic_parts = [comps[k] for k in ("momentum", "volatility", "credit")
                         if comps[k] is not None]
        classic = float(np.mean(classic_parts)) if classic_parts else composite
        positioning = comps["safe_haven"] if comps["safe_haven"] is not None else composite

        composites.append(composite)
        d5 = composite - composites[-6] if len(composites) >= 6 else 0.0
        direction = "rising" if d5 > 2 else "falling" if d5 < -2 else "stable"
        regime, label = regime_for(composite)

        is_last = day == days[-1]
        explanation = ""
        if is_last:
            explanation = (
                f"{cfg['label']} composite {composite:.1f} — {label.lower()} — from momentum, "
                f"volatility, credit-spread and safe-haven reads. Narrative sentiment accrues "
                f"live and is not in this composite."
                + (" Latest sessions verified against Bloomberg." if bbg_live else "")
            )
        out.append(MarketPulseScore(
            timestamp=datetime(day.year, day.month, day.day, 21, 0, tzinfo=timezone.utc),
            market_id=market_id,
            classic_score=round(classic, 1),
            narrative_score=50.0,
            positioning_score=round(positioning, 1),
            composite_score=round(composite, 1),
            regime=regime,
            regime_label=label,
            direction=direction,
            confidence=75.0 if (is_last and bbg_live) else 70.0,
            explanation=explanation,
        ))
    return out


async def run(full: bool) -> None:
    store = DuckDBStore()
    store.init_database()

    print("downloading free history (yfinance + FRED)...")
    prices = fetch_yf()
    oas = fetch_fred(FRED_HY_OAS) * 100  # percent -> bps

    prices, bbg_live = await merge_bloomberg_tail(prices)
    print(f"bloomberg overlay: {'applied' if bbg_live else 'offline — free sources only'}")

    for market_id, cfg in MARKETS.items():
        if full:
            eval_start = pd.Timestamp(EVAL_START)
            store.query("DELETE FROM scores WHERE market_id = ?", [market_id])
        else:
            rows = store.query(
                "SELECT MAX(timestamp) AS mx FROM scores WHERE market_id = ?", [market_id])
            mx = rows[0]["mx"] if rows and rows[0].get("mx") else None
            if mx is None:
                eval_start = pd.Timestamp(EVAL_START)
            else:
                eval_start = pd.Timestamp(mx).tz_localize(None).normalize() - pd.Timedelta(days=7)
                store.query("DELETE FROM scores WHERE market_id = ? AND timestamp >= ?",
                            [market_id, eval_start.to_pydatetime()])

        scores = compute_market(market_id, cfg, prices, oas,
                                eval_start, bbg_live)
        for s in scores:
            store.save_score(s)
        if scores:
            print(f"{market_id:<13} {len(scores):>6} days  "
                  f"{scores[0].timestamp.date()} -> {scores[-1].timestamp.date()}  "
                  f"latest {scores[-1].composite_score} ({scores[-1].regime_label})")


def main() -> None:
    import asyncio
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    ap = argparse.ArgumentParser()
    ap.add_argument("--full", action="store_true", help="rebuild from 2003")
    args = ap.parse_args()
    asyncio.run(run(full=args.full))


if __name__ == "__main__":
    main()
