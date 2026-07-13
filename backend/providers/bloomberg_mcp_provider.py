"""Bloomberg provider via the Westwood Bloomberg MCP server.

Talks to the firm's local Bloomberg MCP HTTP service (FastAPI, default
``http://localhost:8100``; Swagger at ``/docs``), which fronts a live
Bloomberg Terminal session:

* ``GET  /status``      -> ``{"connected": true, "terminal_available": true}``
* ``POST /historical``  -> ``{tickers, fields, start_date, end_date, periodicity}``
                           -> ``{"data": {ticker: [{"date": ..., FIELD: val}, ...]}}``
* ``POST /reference``   -> ``{tickers, fields}`` -> ``{"data": {ticker: {FIELD: val}}}``

Tickers use full Bloomberg form (``"SPX Index"``, ``"TLT US Equity"``).

Cost discipline: this provider is the *professional* tier for small live
pulls (a handful of tickers, PX_LAST, a few sessions). Deep history stays
on the free public tier (yfinance / FRED) by design — see
``backend/jobs/compute_scores.py``.

Implemented: price history, current quote, source status.
Not served by the MCP service (returns None, chain falls through):
breadth, options, credit spreads, safe-haven basket, news, social, flows.

Configuration: ``BLOOMBERG_MCP_URL`` env var (default ``http://localhost:8100``).
No credentials are stored — the MCP server uses the logged-in Terminal's
own entitlements.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

import httpx
import pandas as pd

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)

DEFAULT_URL = "http://localhost:8100"

# yfinance-style symbols -> Bloomberg form, so the provider is a drop-in
# member of the chain when callers use public-tier symbols.
SYMBOL_MAP: Dict[str, str] = {
    "^GSPC": "SPX Index",
    "^SPX": "SPX Index",
    "^NDX": "NDX Index",
    "^RUT": "RTY Index",
    "^DJI": "INDU Index",
    "^VIX": "VIX Index",
    "SPY": "SPY US Equity",
    "TLT": "TLT US Equity",
    "GLD": "GLD US Equity",
    "UUP": "UUP US Equity",
}


def to_bbg(ticker: str) -> str:
    """Map a public-tier symbol to Bloomberg form (pass through if already)."""
    if ticker in SYMBOL_MAP:
        return SYMBOL_MAP[ticker]
    if ticker.endswith(("Index", "Equity", "Curncy", "Comdty", "Govt")):
        return ticker
    return f"{ticker} US Equity"


class BloombergMCPProvider(BaseProvider):
    """Live Bloomberg data through the local Westwood MCP HTTP server."""

    name: str = "bloomberg_mcp"
    tier: str = "professional"

    def __init__(self, base_url: Optional[str] = None, timeout: float = 30.0) -> None:
        self.base_url = (base_url or os.environ.get("BLOOMBERG_MCP_URL", DEFAULT_URL)).rstrip("/")
        self.timeout = timeout
        logger.info("BloombergMCPProvider -> %s", self.base_url)

    # ── HTTP helpers ─────────────────────────────────────────────────

    async def _get(self, path: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.get(f"{self.base_url}{path}")
                r.raise_for_status()
                return r.json()
        except Exception as exc:
            logger.debug("Bloomberg MCP GET %s failed: %s", path, exc)
            return None

    async def _post(self, path: str, payload: dict) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                r = await client.post(f"{self.base_url}{path}", json=payload)
                r.raise_for_status()
                return r.json()
        except Exception as exc:
            logger.debug("Bloomberg MCP POST %s failed: %s", path, exc)
            return None

    # ── Market data ──────────────────────────────────────────────────

    async def get_price_history_range(
        self,
        ticker: str,
        start_yyyymmdd: str,
        end_yyyymmdd: str,
        field: str = "PX_LAST",
    ) -> Optional[pd.DataFrame]:
        """Daily *field* history between two dates (Bloomberg BDH-style)."""
        bbg = to_bbg(ticker)
        body = {
            "tickers": [bbg],
            "fields": [field],
            "start_date": start_yyyymmdd,
            "end_date": end_yyyymmdd,
            "periodicity": "DAILY",
        }
        res = await self._post("/historical", body)
        rows = (res or {}).get("data", {}).get(bbg, [])
        if not rows:
            return None
        df = pd.DataFrame(rows)
        if "date" not in df.columns or field not in df.columns:
            return None
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()
        close = pd.to_numeric(df[field], errors="coerce").dropna()
        out = pd.DataFrame({
            "open": close, "high": close, "low": close,
            "close": close, "volume": 0,
        })
        return out if not out.empty else None

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        end = datetime.now()
        start = end - timedelta(days=int(days * 1.6) + 5)
        return await self.get_price_history_range(
            ticker, start.strftime("%Y%m%d"), end.strftime("%Y%m%d"))

    async def get_current_quote(self, ticker: str) -> Optional[Dict[str, Any]]:
        bbg = to_bbg(ticker)
        res = await self._post("/reference", {
            "tickers": [bbg],
            "fields": ["PX_LAST", "CHG_NET_1D", "CHG_PCT_1D"],
        })
        data = (res or {}).get("data", {}).get(bbg, {})
        px = data.get("PX_LAST")
        if px is None:
            return None
        return {
            "price": float(px),
            "change": float(data.get("CHG_NET_1D") or 0.0),
            "change_percent": float(data.get("CHG_PCT_1D") or 0.0),
            "volume": 0,
            "timestamp": datetime.now(timezone.utc),
        }

    # ── Not served by the MCP service — chain falls through ─────────

    async def get_breadth_data(self, market_id: str) -> Optional[Dict[str, Any]]:
        return None

    async def get_options_data(self, ticker: str) -> Optional[Dict[str, Any]]:
        return None

    async def get_credit_spreads(self) -> Optional[Dict[str, Any]]:
        return None

    async def get_safe_haven_assets(self) -> Optional[Dict[str, Any]]:
        return None

    async def get_news_articles(self, limit: int = 50) -> List[Article]:
        return []

    async def get_social_posts(self, limit: int = 50) -> List[SocialPost]:
        return []

    async def get_flows_data(self, market_id: str) -> Optional[Dict[str, Any]]:
        return None

    # ── Health ───────────────────────────────────────────────────────

    async def get_source_status(self) -> SourceStatus:
        res = await self._get("/status")
        ok = bool(res and res.get("connected") and res.get("terminal_available"))
        return SourceStatus(
            provider=self.name,
            available=ok,
            last_successful_fetch=datetime.now(timezone.utc) if ok else None,
            tier=self.tier,
        )
