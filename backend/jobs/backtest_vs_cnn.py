# -*- coding: utf-8 -*-
"""Point-in-time MarketPulse reconstruction vs CNN Fear & Greed.

Reconstructs a 4-component MarketPulse composite (momentum, volatility,
credit spreads, safe haven — the components computable from free public
history) walking forward day by day with the platform's own calculators,
then compares it against CNN's published Fear & Greed history.

No look-ahead: each day's score uses only data up to that day, via the
same `calculate_sync` methods the BacktestEngine uses.

Usage:  python -m backend.jobs.backtest_vs_cnn [--cnn path/to/cnn_fg.json]
Writes: data/exports/backtest_vs_cnn.csv + .png + stats to stdout
"""
from __future__ import annotations

import argparse
import io
import json
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.indicators.momentum import MomentumIndicator
from backend.indicators.volatility import VolatilityIndicator
from backend.indicators.credit_spreads import CreditSpreadsIndicator
from backend.indicators.safe_haven import SafeHavenIndicator

OUT = Path(__file__).resolve().parents[2] / "data" / "exports"
START_WARMUP = "2021-06-01"   # rolling-window warmup before the eval window
START_EVAL = "2023-07-01"     # matches CNN history depth

# Brand tokens (frontend2/src/lib/theme.ts)
INK = "#16233A"; BLUE = "#3B82D6"; PAPER = "#FFFFFF"; HAIR = "#E2E6EC"
SLATE = "#5C6B80"; GOLD = "#C8A951"
ZONES = [(0, 24, "#B3382E"), (24, 44, "#C4791F"), (44, 55, "#8B93A1"),
         (55, 75, "#6F9A3D"), (75, 100, "#1F7A4D")]


def fetch_fred(series_id: str) -> pd.Series:
    url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
    with urllib.request.urlopen(url, timeout=30) as r:
        df = pd.read_csv(io.BytesIO(r.read()))
    df.columns = ["date", "value"]
    df["date"] = pd.to_datetime(df["date"])
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    return df.dropna().set_index("date")["value"]


def fetch_prices() -> pd.DataFrame:
    import yfinance as yf
    raw = yf.download(["^GSPC", "^VIX", "TLT"], start=START_WARMUP,
                      progress=False, auto_adjust=True)["Close"]
    return raw.dropna(how="all").ffill()


def load_cnn(path: str | None) -> pd.Series:
    if path and Path(path).exists():
        d = json.loads(Path(path).read_text())
    else:
        req = urllib.request.Request(
            "https://production.dataviz.cnn.io/index/fearandgreed/graphdata/2023-07-01",
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                     "Accept": "application/json", "Referer": "https://www.cnn.com/markets/fear-and-greed"})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.loads(r.read().decode())
    rows = d["fear_and_greed_historical"]["data"]
    s = pd.Series({pd.Timestamp(datetime.fromtimestamp(p["x"] / 1000, tz=timezone.utc).date()): p["y"]
                   for p in rows})
    return s.sort_index()


def reconstruct(prices: pd.DataFrame, hy_oas: pd.Series) -> pd.DataFrame:
    momentum = MomentumIndicator()
    volatility = VolatilityIndicator()
    credit = CreditSpreadsIndicator()
    haven = SafeHavenIndicator()

    spx = prices["^GSPC"].dropna()
    vix = prices["^VIX"].dropna()
    tlt = prices["TLT"].dropna()
    oas = hy_oas.reindex(spx.index).ffill().dropna()

    eval_days = spx.index[spx.index >= START_EVAL]
    rows = []
    for day in eval_days:
        px = spx.loc[:day].tolist()[-500:]
        vx = vix.loc[:day].tolist()[-252:]
        cs = oas.loc[:day].tolist()[-252:]
        eq = spx.loc[:day].tolist()[-260:]
        sh = tlt.loc[:day].tolist()[-260:]
        comps = {
            "momentum": momentum.calculate_sync(px),
            "volatility": volatility.calculate_sync(vx),
            "credit": credit.calculate_sync(cs),
            "safe_haven": haven.calculate_sync(eq, sh),
        }
        vals = [v for v in comps.values() if v is not None]
        if not vals:
            continue
        rows.append({"date": day, **comps, "mp_reconstructed": float(np.mean(vals))})
    return pd.DataFrame(rows).set_index("date")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--cnn", default=None, help="path to saved cnn_fg.json (else fetch)")
    args = ap.parse_args()

    print("downloading price history (yfinance)...")
    prices = fetch_prices()
    print("downloading HY OAS (FRED)...")
    hy = fetch_fred("BAMLH0A0HYM2") * 100  # percent -> bps
    print("loading CNN Fear & Greed history...")
    cnn = load_cnn(args.cnn)

    print("reconstructing MarketPulse point-in-time...")
    mp = reconstruct(prices, hy)

    df = mp.join(cnn.rename("cnn_fg"), how="inner").dropna(subset=["mp_reconstructed", "cnn_fg"])
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "backtest_vs_cnn.csv")

    lvl = df["mp_reconstructed"].corr(df["cnn_fg"])
    chg = df["mp_reconstructed"].diff(5).corr(df["cnn_fg"].diff(5))
    side = ((df["mp_reconstructed"] >= 50) == (df["cnn_fg"] >= 50)).mean()
    spread = (df["mp_reconstructed"] - df["cnn_fg"])
    print(f"\ndays compared: {len(df)}  ({df.index.min().date()} -> {df.index.max().date()})")
    print(f"correlation (levels):        {lvl:.2f}")
    print(f"correlation (5d changes):    {chg:.2f}")
    print(f"same side of 50:             {side*100:.0f}% of days")
    print(f"MP minus CNN, mean / stdev:  {spread.mean():+.1f} / {spread.std():.1f}")

    # chart
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(12.8, 5.4), dpi=170)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    for lo, hi, c in ZONES:
        ax.axhspan(lo, hi, color=c, alpha=0.06, lw=0)
    ax.plot(df.index, df["cnn_fg"], color=BLUE, lw=1.4, label="CNN Fear & Greed")
    ax.plot(df.index, df["mp_reconstructed"], color=INK, lw=2.0,
            label="MarketPulse (reconstructed, 4 components)")
    ax.set_ylim(0, 100); ax.set_yticks([0, 24, 44, 55, 75, 100])
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color(HAIR)
    ax.tick_params(colors=SLATE, labelsize=9)
    ax.set_title("MarketPulse point-in-time reconstruction vs CNN Fear & Greed",
                 loc="left", fontsize=12, color=INK, pad=14)
    ax.text(0, 1.015, f"July 2023 – July 2026 · level correlation {lvl:.2f} · "
                      f"same side of 50 on {side*100:.0f}% of days",
            transform=ax.transAxes, fontsize=9, color=SLATE)
    leg = ax.legend(loc="lower left", frameon=False, fontsize=9)
    for t in leg.get_texts(): t.set_color(INK)
    fig.tight_layout()
    fig.savefig(OUT / "backtest_vs_cnn.png", facecolor=PAPER, bbox_inches="tight")
    print("wrote:", OUT / "backtest_vs_cnn.csv", "and .png")


if __name__ == "__main__":
    main()
