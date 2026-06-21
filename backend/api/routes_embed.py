"""Embed widget endpoints — HTML and JSON widgets for external embedding."""

import logging
from datetime import datetime, timezone
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/embed", tags=["embed"])

# Widget size configurations
WIDGET_SIZES = {
    "small": {"width": "300px", "height": "180px", "font_size": "14px"},
    "medium": {"width": "500px", "height": "280px", "font_size": "16px"},
    "full": {"width": "100%", "height": "400px", "font_size": "18px"},
}

# Color schemes
THEMES = {
    "light": {
        "bg": "#ffffff",
        "text": "#1a1a2e",
        "accent": "#3b82f6",
        "border": "#e5e7eb",
        "card_bg": "#f9fafb",
        "positive": "#10b981",
        "negative": "#ef4444",
        "neutral": "#f59e0b",
    },
    "dark": {
        "bg": "#1a1a2e",
        "text": "#e5e7eb",
        "accent": "#60a5fa",
        "border": "#374151",
        "card_bg": "#252543",
        "positive": "#34d399",
        "negative": "#f87171",
        "neutral": "#fbbf24",
    },
}


def _get_score_data(market: str) -> Dict[str, Any]:
    """Get current score data for a market."""
    try:
        from backend.main import store

        result = store.query(
            """
            SELECT composite_score, regime, confidence, classic_score,
                   narrative_score, positioning_score
            FROM scores
            WHERE market_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
            """,
            params=[market],
        )

        if result and len(result) > 0:
            row = result[0]
            return {
                "composite_score": row.get("composite_score", 50.0),
                "regime": row.get("regime", "mp3_neutral"),
                "regime_label": _regime_to_label(row.get("regime", "mp3_neutral")),
                "confidence": row.get("confidence", 50.0),
                "classic_score": row.get("classic_score", 50.0),
                "narrative_score": row.get("narrative_score", 50.0),
                "positioning_score": row.get("positioning_score", 50.0),
            }
    except ImportError:
        pass
    except Exception as exc:
        logger.warning("Error fetching score data: %s", exc)

    # Fallback demo data
    return {
        "composite_score": 58.5,
        "regime": "mp4_risk_on",
        "regime_label": "Risk-On",
        "confidence": 82.0,
        "classic_score": 62.0,
        "narrative_score": 55.0,
        "positioning_score": 58.0,
    }


def _regime_to_label(regime: str) -> str:
    """Convert regime code to human-readable label."""
    labels = {
        "mp1_capitulation": "Capitulation",
        "mp2_defensive": "Defensive",
        "mp3_neutral": "Neutral",
        "mp4_risk_on": "Risk-On",
        "mp5_euphoria": "Euphoria",
    }
    return labels.get(regime, "Unknown")


def _regime_color(regime: str, theme: str) -> str:
    """Get color for a regime."""
    regime_colors = {
        "mp1_capitulation": THEMES[theme]["negative"],
        "mp2_defensive": "#f97316",  # orange
        "mp3_neutral": THEMES[theme]["neutral"],
        "mp4_risk_on": THEMES[theme]["positive"],
        "mp5_euphoria": "#a855f7",  # purple
    }
    return regime_colors.get(regime, THEMES[theme]["neutral"])


def _render_score_bar(score: float, theme: str) -> str:
    """Render an SVG score bar (0-100 gauge)."""
    colors = THEMES[theme]
    # Determine color based on score
    if score < 20:
        bar_color = colors["negative"]
    elif score < 40:
        bar_color = "#f97316"
    elif score < 60:
        bar_color = colors["neutral"]
    elif score < 80:
        bar_color = colors["positive"]
    else:
        bar_color = "#a855f7"

    bar_width = max(0, min(100, score))

    return f"""
    <div style="width: 100%; height: 8px; background: {colors['border']}; border-radius: 4px; overflow: hidden; margin: 8px 0;">
        <div style="width: {bar_width}%; height: 100%; background: {bar_color}; border-radius: 4px; transition: width 0.5s ease;"></div>
    </div>
    """


@router.get("/marketpulse", response_class=HTMLResponse)
async def get_embed_widget(
    market: str = Query(default="sp500", description="Market ID"),
    size: str = Query(default="medium", description="Widget size: small | medium | full"),
    theme: str = Query(default="light", description="Theme: light | dark"),
) -> str:
    """Return HTML embed widget.

    Returns a self-contained HTML widget that can be embedded in any webpage
    via an iframe. The widget displays the current MarketPulse composite score,
    regime, and sub-indexes.
    """
    logger.info("GET /embed/marketpulse?market=%s&size=%s&theme=%s", market, size, theme)

    if size not in WIDGET_SIZES:
        size = "medium"
    if theme not in THEMES:
        theme = "light"

    size_config = WIDGET_SIZES[size]
    colors = THEMES[theme]
    data = _get_score_data(market)

    regime_color = _regime_color(data["regime"], theme)

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MarketPulse Widget</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: {colors['bg']};
            color: {colors['text']};
            width: {size_config['width']};
            min-height: {size_config['height']};
            padding: 16px;
        }}
        .widget {{
            border: 1px solid {colors['border']};
            border-radius: 12px;
            padding: 16px;
            background: {colors['card_bg']};
        }}
        .header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }}
        .market-name {{
            font-size: {size_config['font_size']};
            font-weight: 600;
        }}
        .timestamp {{
            font-size: 11px;
            opacity: 0.6;
        }}
        .score-display {{
            text-align: center;
            margin: 16px 0;
        }}
        .score-value {{
            font-size: 48px;
            font-weight: 700;
            color: {regime_color};
            line-height: 1;
        }}
        .score-label {{
            font-size: 14px;
            margin-top: 4px;
            opacity: 0.8;
        }}
        .regime-badge {{
            display: inline-block;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            color: white;
            background: {regime_color};
            margin-top: 8px;
        }}
        .sub-indexes {{
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 8px;
            margin-top: 12px;
        }}
        .sub-index {{
            text-align: center;
            padding: 8px;
            border-radius: 8px;
            background: {colors['bg']};
            border: 1px solid {colors['border']};
        }}
        .sub-index-value {{
            font-size: 20px;
            font-weight: 600;
        }}
        .sub-index-label {{
            font-size: 10px;
            opacity: 0.7;
            text-transform: uppercase;
            margin-top: 2px;
        }}
        .confidence {{
            text-align: center;
            font-size: 11px;
            opacity: 0.6;
            margin-top: 8px;
        }}
        .footer {{
            text-align: center;
            font-size: 10px;
            opacity: 0.4;
            margin-top: 8px;
        }}
        .footer a {{
            color: {colors['accent']};
            text-decoration: none;
        }}
    </style>
</head>
<body>
    <div class="widget">
        <div class="header">
            <span class="market-name">{market.upper()}</span>
            <span class="timestamp">{datetime.now(timezone.utc).strftime('%H:%M UTC')}</span>
        </div>
        <div class="score-display">
            <div class="score-value">{data['composite_score']:.0f}</div>
            <div class="score-label">MarketPulse Score</div>
            <div class="regime-badge">{data['regime_label']}</div>
        </div>
        {_render_score_bar(data['composite_score'], theme)}
        <div class="sub-indexes">
            <div class="sub-index">
                <div class="sub-index-value">{data['classic_score']:.0f}</div>
                <div class="sub-index-label">Classic</div>
            </div>
            <div class="sub-index">
                <div class="sub-index-value">{data['narrative_score']:.0f}</div>
                <div class="sub-index-label">Narrative</div>
            </div>
            <div class="sub-index">
                <div class="sub-index-value">{data['positioning_score']:.0f}</div>
                <div class="sub-index-label">Positioning</div>
            </div>
        </div>
        <div class="confidence">Confidence: {data['confidence']:.0f}%</div>
        <div class="footer">Powered by <a href="/" target="_blank">Westwood MarketPulse</a></div>
    </div>
</body>
</html>"""

    return html_content


@router.get("/marketpulse.json")
async def get_embed_json(
    market: str = Query(default="sp500", description="Market ID"),
) -> Dict[str, Any]:
    """Return JSON for custom widget rendering.

    Returns structured data that can be used to render a custom widget.
    Use this endpoint if you want to build your own widget UI.
    """
    logger.info("GET /embed/marketpulse.json?market=%s", market)

    data = _get_score_data(market)

    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "market": market,
        "widget": {
            "composite_score": round(data["composite_score"], 1),
            "regime": data["regime"],
            "regime_label": data["regime_label"],
            "regime_color": _regime_color(data["regime"], "light"),
            "confidence": round(data["confidence"], 1),
            "sub_indexes": {
                "classic": round(data["classic_score"], 1),
                "narrative": round(data["narrative_score"], 1),
                "positioning": round(data["positioning_score"], 1),
            },
        },
        "embed": {
            "html_url": f"/api/v1/embed/marketpulse?market={market}&size=medium&theme=light",
            "recommended_height": {"small": 200, "medium": 300, "full": 420},
        },
    }
