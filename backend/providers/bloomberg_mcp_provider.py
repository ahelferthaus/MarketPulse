"""Bloomberg MCP (Model Context Protocol) provider — **stub**.

This module defines the full :class:`BaseProvider` interface for a
future Bloomberg Terminal integration via the Model Context Protocol
(MCP).  All methods currently return ``None`` with an informative log
message.

Planned capabilities
--------------------
Once connected to a Bloomberg Terminal via MCP, this provider will
expose:

* **Real-time pricing** — BDP (Bloomberg Data Point) overrides for
  equities, indices, futures, and options.
* **Historical data** — BDH (Bloomberg Data History) time-series
  retrieval with custom fields.
* **Credit spreads** — ``YAS_CID_SPREAD``, ``YAS_ASW_SPREAD`` for
  corporate bonds.
* **Fund flows** — EPFR-tracked ETF and mutual fund flow data.
* **News sentiment** — Bloomberg NLP-scored news archive.
* **Options analytics** — VOL_SURFACE, DELTA_SKEW, and implied-vol
  term structure.

Connection instructions
-----------------------
1. Install the Bloomberg MCP server::

       pip install bloomberg-mcp

2. Set environment variables::

       export BLOOMBERG_MCP_HOST=localhost
       export BLOOMBERG_MCP_PORT=50051
       export BLOOMBERG_AUTH_TOKEN=<your-token>

3. Launch the MCP server (requires active Bloomberg Terminal session)::

       bloomberg-mcp-server --config mcp_config.yaml

4. Update this provider to connect via gRPC instead of returning stubs.

Security notes
--------------
* Never commit ``BLOOMBERG_AUTH_TOKEN`` to version control.
* Use a secrets manager (AWS Secrets Manager, Vault, etc.) in production.
* All Bloomberg data is subject to terminal license agreements.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)


class BloombergMCPProvider(BaseProvider):
    """Bloomberg Terminal provider via Model Context Protocol (MCP).

    **Status:** Stub — not yet connected to a live Bloomberg Terminal.

    All methods log a diagnostic message and return ``None`` (or an
    empty collection) so the :class:`ProviderChain` seamlessly falls
    back to the next provider in the priority list.
    """

    name: str = "bloomberg_mcp"
    tier: str = "professional"

    def __init__(self) -> None:
        logger.info(
            "BloombergMCPProvider initialised — Bloomberg MCP not connected (stub mode)"
        )

    # ── internal helper ───────────────────────────────────────────────

    def _log_stub(self, method: str) -> None:
        logger.debug("Bloomberg MCP not connected — %s returning stub (None)", method)

    # ── BaseProvider implementation (all stubs) ───────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """Would fetch BDH (Bloomberg Data History) time-series.

        Stub: returns ``None``.
        """
        self._log_stub("get_price_history")
        return None

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Would fetch BDP (Bloomberg Data Point) real-time fields.

        Fields: ``PX_LAST``, ``PX_CHG_NET_1D``, ``PX_VOLUME``.

        Stub: returns ``None``.
        """
        self._log_stub("get_current_quote")
        return None

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Would fetch advance/decline statistics from Bloomberg.

        Stub: returns ``None``.
        """
        self._log_stub("get_breadth_data")
        return None

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Would fetch options analytics: put/call volume, open interest.

        Bloomberg fields: ``OPT_PUT_CALL_VOLUME_RATIO``, ``OPT_PX``.

        Stub: returns ``None``.
        """
        self._log_stub("get_options_data")
        return None

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Would fetch OAS spreads from Bloomberg's fixed-income analytics.

        Stub: returns ``None``.
        """
        self._log_stub("get_credit_spreads")
        return None

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Would fetch TLT, GLD, DXY via Bloomberg real-time feeds.

        Stub: returns ``None``.
        """
        self._log_stub("get_safe_haven_assets")
        return None

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """Would search Bloomberg News with NLP sentiment scoring.

        Stub: returns empty list.
        """
        self._log_stub("get_news_articles")
        return []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """Bloomberg does not provide social-media data directly.

        Stub: returns empty list.
        """
        self._log_stub("get_social_posts")
        return []

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """Would fetch EPFR-tracked fund flows via Bloomberg.

        Stub: returns ``None``.
        """
        self._log_stub("get_flows_data")
        return None

    async def get_source_status(self) -> SourceStatus:
        """Report as unavailable — Bloomberg MCP is not connected."""
        return SourceStatus(
            provider=self.name,
            available=False,
            last_successful_fetch=None,
            error_count_24h=0,
            avg_response_ms=None,
            data_freshness_minutes=None,
            tier=self.tier,
        )
