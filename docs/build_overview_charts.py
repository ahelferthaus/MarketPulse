# -*- coding: utf-8 -*-
"""Charts for the MarketPulse overview document (docs/assets/)."""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from backend.storage.duckdb_store import DuckDBStore

OUT = Path(__file__).parent / "assets"
OUT.mkdir(exist_ok=True)

INK = "#16233A"; BLUE = "#3B82D6"; PAPER = "#FFFFFF"; HAIR = "#E2E6EC"
SLATE = "#5C6B80"; GOLD = "#C8A951"; NAVY = "#0B2240"
ZONES = [(0, 24, "#B3382E", "MP-1 Panic"), (24, 44, "#C4791F", "MP-2 Defensive"),
         (44, 55, "#8B93A1", "MP-3 Neutral"), (55, 75, "#6F9A3D", "MP-4 Risk-On"),
         (75, 100, "#1F7A4D", "MP-5 Euphoria")]

# (date, label, row) — row staggers the annotation line to avoid collisions
EPISODES = [
    ("2008-10-10", "Global financial crisis", 0),
    ("2011-08-08", "US downgrade", 0),
    ("2018-12-24", "Q4 2018", 0),
    ("2020-03-20", "COVID", 1),
    ("2022-06-16", "2022 bear", 0),
    ("2025-04-15", "Spring 2025", 1),
]


def load() -> pd.DataFrame:
    store = DuckDBStore(read_only=True)
    rows = store.query(
        "SELECT timestamp, composite_score FROM scores "
        "WHERE market_id='sp500' ORDER BY timestamp ASC")
    df = pd.DataFrame(rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df.set_index("timestamp")


def chart_history(df: pd.DataFrame) -> None:
    fig, ax = plt.subplots(figsize=(11.4, 4.6), dpi=180)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    for lo, hi, c, _ in ZONES:
        ax.axhspan(lo, hi, color=c, alpha=0.07, lw=0)
    smoothed = df["composite_score"].rolling(5, min_periods=1).mean()
    ax.plot(df.index, smoothed, color=INK, lw=1.0)
    for date, label, row in EPISODES:
        d = pd.Timestamp(date)
        if d < df.index.min() or d > df.index.max():
            continue
        win = df.loc[d - pd.Timedelta(days=40): d + pd.Timedelta(days=40), "composite_score"]
        if win.empty:
            continue
        dmin = win.idxmin()
        ax.annotate(label, xy=(dmin, win.min()), xytext=(dmin, -13.5 - row * 6.5),
                    ha="center", fontsize=7.2, color=SLATE,
                    arrowprops=dict(arrowstyle="-", color=SLATE, lw=0.7, alpha=0.6),
                    annotation_clip=False)
    ax.set_ylim(0, 100); ax.set_yticks([0, 24, 44, 55, 75, 100])
    ax.set_xlim(df.index.min(), df.index.max())
    ax.xaxis.set_major_locator(mdates.YearLocator(2))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    for s in ["top", "right"]: ax.spines[s].set_visible(False)
    for s in ["left", "bottom"]: ax.spines[s].set_color(HAIR)
    ax.tick_params(colors=SLATE, labelsize=8.5)
    handles = [plt.Rectangle((0, 0), 1, 1, fc=c, alpha=0.45) for _, _, c, _ in ZONES]
    ax.legend(handles, [z[3] for z in ZONES], loc="lower right", frameon=False,
              fontsize=7.6, ncol=5, bbox_to_anchor=(1.0, 1.01))
    fig.tight_layout()
    fig.savefig(OUT / "history_23y.png", facecolor=PAPER, bbox_inches="tight")
    print("wrote history_23y.png")


def chart_zone_frequency(df: pd.DataFrame) -> None:
    freq = []
    for lo, hi, c, label in ZONES:
        share = ((df["composite_score"] > lo) & (df["composite_score"] <= hi)).mean() * 100
        freq.append((label, share, c))
    fig, ax = plt.subplots(figsize=(6.4, 2.9), dpi=180)
    fig.patch.set_facecolor(PAPER); ax.set_facecolor(PAPER)
    ys = range(len(freq))
    ax.barh(list(ys), [f[1] for f in freq], color=[f[2] for f in freq],
            height=0.62, alpha=0.85)
    for y, (label, share, _) in zip(ys, freq):
        ax.text(share + 0.8, y, f"{share:.0f}%", va="center", fontsize=9,
                color=INK, fontfamily="monospace")
    ax.set_yticks(list(ys)); ax.set_yticklabels([f[0] for f in freq], fontsize=8.6, color=INK)
    ax.invert_yaxis()
    ax.set_xlim(0, max(f[1] for f in freq) + 8)
    ax.set_xticks([])
    for s in ax.spines.values(): s.set_visible(False)
    fig.tight_layout()
    fig.savefig(OUT / "zone_frequency.png", facecolor=PAPER, bbox_inches="tight")
    print("wrote zone_frequency.png")


if __name__ == "__main__":
    d = load()
    print(f"{len(d)} days  {d.index.min().date()} -> {d.index.max().date()}")
    chart_history(d)
    chart_zone_frequency(d)
