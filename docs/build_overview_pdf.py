# -*- coding: utf-8 -*-
"""Build the MarketPulse overview document (docs/MarketPulse_Overview.pdf).

An 8-page explanatory brief for the marketing conversation: what MarketPulse
is, how it reads, the 23-year record, how it compares to CNN's Fear & Greed
Index, the engineering and compliance posture, and the go-to-market options.

Run:  python docs/build_overview_pdf.py
(Charts first: python docs/build_overview_charts.py — needs the API stopped.)
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

HERE = Path(__file__).parent
ASSETS = HERE / "assets"

NAVY = "#0B2240"; NAVY950 = "#081A33"; INK = "#16233A"; GOLD = "#C8A951"
SLATE = "#5C6B80"; HAIR = "#E2E6EC"; PAPER = "#F5F6F8"
ZONES = [
    ("MP-1", "0–24", "Panic", "Extreme risk-off; forced selling, stress in credit and volatility.", "#B3382E"),
    ("MP-2", "24–44", "Defensive", "Risk-off posture; havens bid, breadth and momentum deteriorating.", "#C4791F"),
    ("MP-3", "44–55", "Neutral", "Balanced conditions; no dominant emotional signature.", "#8B93A1"),
    ("MP-4", "55–75", "Risk-On", "Appetite for risk; momentum positive, spreads contained.", "#6F9A3D"),
    ("MP-5", "75–100", "Euphoria", "Extreme risk-on; complacency elevated — extremes cut both ways.", "#1F7A4D"),
]

TODAY = "July 12, 2026"


def img(name: str) -> str:
    return (ASSETS / name).as_uri()


CSS = f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ font-family: "Segoe UI", Arial, sans-serif; color: {INK}; }}
.page {{ width: 816px; height: 1056px; page-break-after: always; position: relative;
         overflow: hidden; background: white; padding: 56px 64px 64px 64px; }}
h1, h2, h3, .serif {{ font-family: Georgia, "Times New Roman", serif; font-weight: 400; color: {NAVY}; }}
.eyebrow {{ color: {GOLD}; font-size: 10.5px; letter-spacing: 2.4px; font-weight: 700;
            text-transform: uppercase; margin-bottom: 4px; }}
.ptitle {{ font-size: 26px; margin-bottom: 4px; }}
.rule {{ height: 3px; background: linear-gradient(90deg, {GOLD}, {GOLD} 90px, {HAIR} 90px);
         margin: 10px 0 16px 0; border-radius: 2px; }}
p {{ font-size: 12.5px; line-height: 1.55; margin-bottom: 10px; }}
p.lead {{ font-size: 14px; line-height: 1.55; }}
ul {{ list-style: none; margin: 2px 0 10px 0; }}
li {{ font-size: 12.3px; line-height: 1.5; margin-bottom: 7px; padding-left: 15px; position: relative; }}
li:before {{ content: "\\25AA"; color: {GOLD}; position: absolute; left: 0; }}
.foot {{ position: absolute; bottom: 0; left: 0; right: 0; height: 30px; background: {NAVY};
         color: #cfe0f4; font-size: 9.5px; display: flex; align-items: center;
         padding: 0 64px; letter-spacing: 0.8px; }}
.foot b {{ color: {GOLD}; }} .foot .sp {{ flex: 1; }}
img.chart {{ width: 100%; border: 1px solid {HAIR}; border-radius: 6px; }}
.cap {{ font-size: 10px; color: {SLATE}; font-style: italic; margin: 5px 0 14px 0; }}
table {{ border-collapse: collapse; width: 100%; margin: 6px 0 14px 0; }}
th {{ text-align: left; font-size: 10px; text-transform: uppercase; letter-spacing: 1.2px;
      color: {SLATE}; padding: 6px 10px 6px 0; border-bottom: 1.5px solid {GOLD}; }}
td {{ font-size: 11.8px; line-height: 1.45; padding: 7px 10px 7px 0; border-bottom: 1px solid {HAIR};
      vertical-align: top; }}
.zonechip {{ display: inline-block; padding: 2px 9px; border-radius: 10px; color: white;
             font-size: 10.5px; font-weight: 700; }}
.statrow {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 12px 0 16px 0; }}
.statrow div {{ background: {PAPER}; border: 1px solid {HAIR}; border-top: 3px solid {GOLD};
                border-radius: 6px; padding: 9px 11px; font-size: 10px; color: {SLATE}; line-height: 1.3; }}
.statrow span {{ display: block; font-family: Georgia, serif; font-size: 21px; color: {NAVY}; margin-bottom: 2px; }}
.cover {{ background: linear-gradient(165deg, {NAVY} 0%, {NAVY950} 75%);
          display: flex; flex-direction: column; justify-content: center; align-items: center;
          text-align: center; color: white; }}
.cover .mast {{ color: {GOLD}; font-size: 12px; letter-spacing: 5px; font-weight: 700; margin-bottom: 18px; }}
.cover h1 {{ color: white; font-size: 52px; margin-bottom: 10px; }}
.cover .sub {{ font-family: Georgia, serif; font-style: italic; color: {GOLD}; font-size: 19px; margin-bottom: 30px; }}
.cover .desc {{ color: rgba(255,255,255,0.75); font-size: 14px; max-width: 480px; line-height: 1.6; }}
.cover .meta {{ position: absolute; bottom: 44px; font-size: 10.5px; letter-spacing: 2px; color: rgba(255,255,255,0.45); }}
.tag {{ display: inline-block; background: #f3e8d2; color: #7a5c14; border: 1px solid {GOLD};
        font-size: 9.5px; font-weight: 700; letter-spacing: 1.2px; padding: 3px 10px;
        border-radius: 4px; margin-bottom: 12px; }}
.half {{ display: grid; grid-template-columns: 1fr 1fr; gap: 22px; }}
"""


def foot(n: int, section: str) -> str:
    return (f'<div class="foot"><b>MarketPulse</b>&nbsp;·&nbsp;{section}'
            f'<span class="sp"></span>Westwood · Internal draft · {TODAY}'
            f'<span class="sp"></span>Page {n}</div>')


def zone_rows() -> str:
    return "".join(
        f'<tr><td><span class="zonechip" style="background:{c}">{z}</span></td>'
        f'<td style="font-family:Consolas,monospace">{rng}</td><td><b>{label}</b></td><td>{desc}</td></tr>'
        for z, rng, label, desc, c in ZONES)


PAGES: list[str] = []

# ── 1 · Cover ────────────────────────────────────────────────────────────
PAGES.append(f"""
<div class="page cover">
  <div class="mast">WESTWOOD</div>
  <h1>MarketPulse</h1>
  <div class="sub">The Westwood market barometer</div>
  <div class="desc">One daily 0&ndash;100 reading of market psychology &mdash; measured,
  not guessed &mdash; built on twenty-three years of point-in-time data and the
  research discipline of an investment firm.</div>
  <div class="meta">EXPLANATORY BRIEF · PREPARED FOR MARKETING REVIEW · {TODAY.upper()} · DRAFT — NOT FOR DISTRIBUTION</div>
</div>""")

# ── 2 · What it is ───────────────────────────────────────────────────────
PAGES.append(f"""
<div class="page">
  <div class="eyebrow">The product</div>
  <div class="ptitle serif">One number for market psychology</div>
  <div class="rule"></div>
  <p class="lead">MarketPulse distills the market's emotional state into a single daily
  score from 0 (extreme risk-off) to 100 (extreme risk-on), presented on a five-zone
  barometer. It answers the question every client asks first &mdash; <i>"how nervous is the
  market right now?"</i> &mdash; with a measured, repeatable, explainable reading.</p>
  <div class="statrow">
    <div><span>0&ndash;100</span>daily composite score, five named zones</div>
    <div><span>4</span>markets scored independently: S&amp;P 500, Nasdaq 100, Russell 2000, Dow</div>
    <div><span>23 yrs</span>of point-in-time history, 2003 to today</div>
    <div><span>3</span>lenses: market data, news narrative, positioning</div>
  </div>
  <p>The score is built from three families of evidence, echoing how an investment
  committee actually reads sentiment:</p>
  <ul>
    <li><b>Classic</b> &mdash; what the market is doing: price momentum, volatility, credit
    spreads, breadth. The hard data of risk appetite.</li>
    <li><b>Narrative</b> &mdash; what the market is saying: sentiment scored from financial
    news text. This lens accrues live and is clearly labeled while its history builds.</li>
    <li><b>Positioning</b> &mdash; where money is leaning: options activity, volatility term
    structure, and safe-haven flows.</li>
  </ul>
  <p>Every reading ships with its regime label, direction, a <b>data-confidence score</b>,
  an honest as-of timestamp, and a plain-English explanation of what moved. The product
  is deliberately transparent: a public methodology page documents every component.</p>
  <p><b>Why the vocabulary matters.</b> MarketPulse deliberately avoids the "fear and
  greed" framing of the well-known CNN index. The zones speak the language of
  institutional risk &mdash; <i>Panic, Defensive, Neutral, Risk-On, Euphoria</i> &mdash;
  which is more precise, more professional, and ownable as Westwood intellectual
  property.</p>
  {foot(2, "The product")}
</div>""")

# ── 3 · The five zones ───────────────────────────────────────────────────
PAGES.append(f"""
<div class="page">
  <div class="eyebrow">How it reads</div>
  <div class="ptitle serif">Five zones, drawn from evidence</div>
  <div class="rule"></div>
  <p class="lead">Zone boundaries are not arbitrary quintiles &mdash; they are asymmetric
  bands derived from the historical distribution of market conditions, so each zone
  means something about frequency as well as level.</p>
  <table>
    <tr><th style="width:70px">Zone</th><th style="width:70px">Range</th><th style="width:110px">Label</th><th>Reading</th></tr>
    {zone_rows()}
  </table>
  <img class="chart" src="{img('zone_frequency.png')}" style="width:62%">
  <div class="cap">Realized share of trading days per zone, S&amp;P 500, 2003&ndash;2026 — the
  neutral middle dominates; the extremes are rare by construction.</div>
  <p>Nine components feed the composite. Four are live today with twenty-three years of
  point-in-time history &mdash; <b>momentum</b> (price vs. 125-day average),
  <b>volatility</b> (VIX percentile), <b>credit spreads</b> (high-yield OAS), and
  <b>safe-haven demand</b> (equities vs. Treasuries). The remaining components &mdash;
  put/call ratios, breadth, new highs/lows, flows, and news narrative &mdash; are staged
  on the roadmap, each added with the same no-look-ahead discipline.</p>
  <p>At extremes the barometer is a <b>contrarian instrument</b>: the research literature
  and our own backtest agree that deep Panic readings have historically preceded
  above-average forward returns, while Euphoria compresses them. That framing &mdash;
  discipline against the crowd &mdash; is the Westwood voice.</p>
  {foot(3, "How it reads")}
</div>""")

# ── 4 · 23 years ─────────────────────────────────────────────────────────
PAGES.append(f"""
<div class="page">
  <div class="eyebrow">The record</div>
  <div class="ptitle serif">Twenty-three years of the barometer</div>
  <div class="rule"></div>
  <p class="lead">MarketPulse is not a black box launched yesterday. The engine was walked
  forward through every trading day since 2003 &mdash; each day scored using only the
  data available on that day &mdash; producing a genuine point-in-time record across
  every modern market regime.</p>
  <img class="chart" src="{img('history_23y.png')}">
  <div class="cap">S&amp;P 500 MarketPulse composite, 2003&ndash;2026 (5-day average), with the
  five zones shaded. Every major stress episode registers as a plunge into Panic; every
  extended bull phase presses into Euphoria.</div>
  <ul>
    <li>The global financial crisis, the 2011 downgrade, the Q4 2018 selloff, COVID,
    the 2022 bear market, and the spring 2025 stress all print as deep Panic
    readings &mdash; the instrument sees what investors felt.</li>
    <li>History is reconstructed from the four live components (momentum, volatility,
    credit, safe haven); the narrative lens accrues from launch forward and is excluded
    from the historical composite &mdash; stated plainly wherever the history is shown.</li>
    <li>The same walk-forward engine refreshes the site daily, so the public record and
    the research record can never diverge.</li>
  </ul>
  {foot(4, "The record")}
</div>""")

# ── 5 · vs CNN ───────────────────────────────────────────────────────────
PAGES.append(f"""
<div class="page">
  <div class="eyebrow">The benchmark comparison</div>
  <div class="ptitle serif">Same animal, better instrument</div>
  <div class="rule"></div>
  <p class="lead">CNN's Fear &amp; Greed Index is the category's household name. Over the
  three years of its published history we can compare against, MarketPulse tracks it
  closely &mdash; and differs exactly where a firm-built instrument should.</p>
  <img class="chart" src="{img('vs_cnn.png')}">
  <div class="cap">MarketPulse point-in-time reconstruction (navy) vs. the published CNN
  Fear &amp; Greed history (blue), July 2023 &ndash; July 2026. Level correlation 0.78;
  agreement on risk-on vs. risk-off 74% of days.</div>
  <table>
    <tr><th style="width:180px"></th><th>MarketPulse</th><th>CNN Fear &amp; Greed</th></tr>
    <tr><td><b>Vocabulary</b></td><td>Institutional risk language (Panic &rarr; Euphoria), ownable IP</td><td>"Fear / Greed" consumer framing</td></tr>
    <tr><td><b>Markets</b></td><td>Four indices scored independently</td><td>S&amp;P 500 only</td></tr>
    <tr><td><b>Credit input</b></td><td>True high-yield OAS spreads</td><td>Junk-bond demand proxy</td></tr>
    <tr><td><b>Transparency</b></td><td>Public methodology page, per-component breakdown, confidence score on every reading</td><td>Component list, limited detail</td></tr>
    <tr><td><b>Narrative</b></td><td>Dedicated news-sentiment lens (accruing live)</td><td>None</td></tr>
    <tr><td><b>Honesty layer</b></td><td>As-of stamps, data-source status, reconstruction clearly labeled</td><td>&mdash;</td></tr>
  </table>
  <p>The +7.6-point average gap vs. CNN reflects composition: two of CNN's most
  fear-sensitive inputs (put/call and breadth) are still on our roadmap. Adding them is
  a calibration choice &mdash; we can converge toward the benchmark or deliberately keep
  a differentiated read.</p>
  {foot(5, "The comparison")}
</div>""")

# ── 6 · Engineering & data ───────────────────────────────────────────────
PAGES.append(f"""
<div class="page">
  <div class="eyebrow">Under the hood</div>
  <div class="ptitle serif">Built like research, run like software</div>
  <div class="rule"></div>
  <ul>
    <li><b>Point-in-time discipline.</b> Every historical value uses only data available on
    that date; rolling windows are strictly trailing. The backtest engine that validates
    regimes enforces the same rule &mdash; no look-ahead, anywhere.</li>
    <li><b>Tiered data sourcing.</b> Public tier (exchange data, FRED credit spreads) powers
    the deep history at zero data cost; the <b>professional tier &mdash; Westwood's
    Bloomberg infrastructure &mdash; verifies the most recent sessions</b> whenever a
    Terminal is present. Raw licensed data never leaves the building: only derived
    0&ndash;100 scores are published.</li>
    <li><b>Honest by construction.</b> The public page shows when data is a static snapshot
    vs. live, the exact as-of time, how many sources are reporting, and a confidence
    score computed from data quality &mdash; not marketing copy.</li>
    <li><b>Modern, owned stack.</b> Python analytics engine and API, analytical database,
    React front end; deploys as a static site (near-zero hosting cost) or a live API.
    Fully Westwood-built and Westwood-owned.</li>
    <li><b>Embeddable.</b> A widget endpoint already exists &mdash; the barometer can sit on
    westwood.com, in a partner's page, or inside advisor collateral with one line of
    HTML.</li>
    <li><b>Daily automation.</b> Scores recompute and republish automatically after each
    US close; the historical record and the live site can never drift apart.</li>
  </ul>
  <div class="eyebrow" style="margin-top:16px">Compliance posture</div>
  <div class="ptitle serif" style="font-size:19px">Educational by design</div>
  <div class="rule"></div>
  <ul>
    <li>MarketPulse is an educational market-sentiment indicator &mdash; explicitly not
    investment advice, not a trading signal, and labeled as such on every surface.</li>
    <li>No performance promotion, no product recommendations, no client data &mdash; the
    cleanest possible footprint under the SEC Marketing Rule, pending formal review.</li>
    <li>Sources are public or properly licensed; published values are derived scores,
    never redistributed raw data.</li>
  </ul>
  {foot(6, "Engineering & compliance")}
</div>""")

# ── 7 · Go to market ─────────────────────────────────────────────────────
PAGES.append(f"""
<div class="page">
  <div class="tag">DRAFT CONCEPTS — FOR MARKETING DISCUSSION</div>
  <div class="eyebrow">Why this matters commercially</div>
  <div class="ptitle serif">Three ways MarketPulse earns its keep</div>
  <div class="rule"></div>
  <p class="lead">Sentiment indices are traffic machines: CNN's index is one of the most
  visited pages in financial media because it answers a universal question in one glance,
  every day. Westwood can own that daily habit &mdash; in our own voice.</p>
  <table>
    <tr><th style="width:150px">Path</th><th>Shape</th><th style="width:230px">What it earns</th></tr>
    <tr><td><b>1 · westwood.com</b></td>
        <td>A public MarketPulse page and homepage widget, refreshed daily after the close.
        Evergreen, self-updating content with genuine daily-return-visit mechanics.</td>
        <td>Organic traffic, brand association with disciplined risk measurement, a reason
        to visit Westwood daily.</td></tr>
    <tr><td><b>2 · Media partnership</b></td>
        <td>Offer a financial news outlet (e.g. MarketWatch) a differentiated sentiment
        indicator &mdash; multi-market, credit-aware, confidence-scored &mdash; branded
        <i>"MarketPulse, provided by Westwood."</i> The embed widget makes integration
        one line of code.</td>
        <td>Daily brand impressions at media scale; the byline CNN gets today, with a
        better instrument.</td></tr>
    <tr><td><b>3 · Advisor &amp; client collateral</b></td>
        <td>The barometer as a standing exhibit in decks, commentaries, and the WAL-E
        weekly brief &mdash; one image that frames every market conversation.</td>
        <td>A house sentiment framework, used consistently across every client
        touchpoint.</td></tr>
  </table>
  <div class="eyebrow" style="margin-top:8px">Suggested next steps</div>
  <ul>
    <li>Marketing review of naming, framing, and this document.</li>
    <li>Compliance review of the public site and disclosures (educational positioning).</li>
    <li>Add put/call and breadth components to tighten the benchmark comparison.</li>
    <li>Decide the flagship surface (westwood.com page vs. partnership pitch) and
    sequence accordingly.</li>
  </ul>
  {foot(7, "Go to market")}
</div>""")

# ── 8 · Back ─────────────────────────────────────────────────────────────
PAGES.append(f"""
<div class="page cover">
  <div class="mast">WESTWOOD</div>
  <div class="sub" style="font-size:24px; max-width: 560px; line-height:1.5">The market,
  measured &mdash; one number, five zones, twenty-three years of discipline.</div>
  <div class="meta">MARKETPULSE · WESTWOOD MULTI-ASSET · {TODAY.upper()}</div>
</div>""")


def build() -> Path:
    html = f"""<!doctype html><html><head><meta charset="utf-8">
    <style>{CSS}</style></head><body>{''.join(PAGES)}</body></html>"""
    out_html = HERE / "overview.html"
    out_html.write_text(html, encoding="utf-8")

    from playwright.sync_api import sync_playwright
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_page()
        pg.goto(out_html.as_uri())
        pg.wait_for_timeout(2500)
        out_pdf = HERE / "MarketPulse_Overview.pdf"
        pg.pdf(path=str(out_pdf), width="8.5in", height="11in",
               print_background=True, prefer_css_page_size=False)
        b.close()
    print("Wrote:", out_pdf)
    return out_pdf


if __name__ == "__main__":
    build()
