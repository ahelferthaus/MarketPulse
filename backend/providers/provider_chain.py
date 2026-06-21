"""Provider chain manager — prioritized fallback across data providers.

The :class:`ProviderChain` is the **single integration point** between
the scoring engine and the provider layer.  It maintains a sorted list
of providers (professional → premium → public) and attempts each data
fetch in priority order until one succeeds.

Usage::

    from backend.providers import (
        ProviderChain, BloombergMCPProvider, YFinanceProvider,
        FREDProvider, MockProvider,
    )

    chain = ProviderChain([
        BloombergMCPProvider(),
        YFinanceProvider(),
        FREDProvider(),
        MockProvider(),
    ])

    # Scoring engine calls the chain, not individual providers
    price_hist = await chain.get_price_history("SPY", days=252)
    spreads = await chain.get_credit_spreads()
    articles = await chain.get_news_articles("stock market", limit=20)

Design principles
-----------------
* **Never propagate exceptions** — a failing provider is skipped;
  the chain returns ``None`` only when *all* providers fail.
* **Tier-based priority** — professional providers are tried first,
  then premium, then public.  Within a tier, order is preserved.
* **Observable** — every attempt, success, and failure is logged.
* **Status aggregation** — health of all providers is exposed for
  the ``/api/v1/sources/status`` endpoint.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import pandas as pd

from backend.domain.article import Article, SocialPost
from backend.domain.source import SourceStatus
from backend.providers.base import BaseProvider

logger = logging.getLogger(__name__)

_TIER_PRIORITY = {
    "professional": 0,
    "premium": 1,
    "public": 2,
}


class ProviderChain:
    """Manages a prioritized fallback chain of :class:`BaseProvider` instances.

    The chain is sorted by provider tier at construction time:
    ``professional`` (highest priority) → ``premium`` → ``public``.
    Within the same tier, the insertion order is preserved.

    Every data-fetch method iterates through providers in priority order,
    returning the first non-null / non-empty result.  If all providers
    fail, ``None`` or an empty collection is returned.
    """

    def __init__(self, providers: List[BaseProvider]) -> None:
        """Create a new provider chain.

        Args:
            providers: Unordered (or partially ordered) list of provider
                instances.  The constructor re-sorts by tier priority.
        """
        self.providers = sorted(
            providers,
            key=lambda p: _TIER_PRIORITY.get(p.tier, 99),
        )
        logger.info(
            "ProviderChain initialised with %d providers: %s",
            len(self.providers),
            ", ".join(f"{p.name}({p.tier})" for p in self.providers),
        )

    # ── Generic fallback helper ───────────────────────────────────────

    async def _try_providers(
        self,
        method_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        """Try *method_name* on each provider in priority order.

        Returns the first truthy result, or ``None`` if all fail.
        """
        for provider in self.providers:
            try:
                method = getattr(provider, method_name)
                result = await method(*args, **kwargs)

                # DataFrame-specific emptiness check
                if isinstance(result, pd.DataFrame):
                    if result is not None and not result.empty:
                        logger.debug(
                            "ProviderChain.%s — %s succeeded (%d rows)",
                            method_name, provider.name, len(result),
                        )
                        return result
                elif isinstance(result, list):
                    if result:
                        logger.debug(
                            "ProviderChain.%s — %s succeeded (%d items)",
                            method_name, provider.name, len(result),
                        )
                        return result
                elif result is not None:
                    logger.debug(
                        "ProviderChain.%s — %s succeeded",
                        method_name, provider.name,
                    )
                    return result

            except Exception as exc:
                logger.warning(
                    "ProviderChain.%s — %s raised %s: %s",
                    method_name, provider.name, type(exc).__name__, exc,
                )

        logger.warning(
            "ProviderChain.%s — all %d providers failed",
            method_name, len(self.providers),
        )
        return None

    # ── Market data ───────────────────────────────────────────────────

    async def get_price_history(
        self,
        ticker: str,
        days: int = 252,
    ) -> Optional[pd.DataFrame]:
        """Fetch price history from the first successful provider.

        Args:
            ticker: Security ticker symbol.
            days: Number of trading days to retrieve.

        Returns:
            OHLCV DataFrame or ``None`` when no provider succeeds.
        """
        return await self._try_providers("get_price_history", ticker, days=days)

    async def get_current_quote(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch the current quote from the first successful provider."""
        return await self._try_providers("get_current_quote", ticker)

    async def get_breadth_data(
        self,
        market_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch market breadth data from the first successful provider."""
        return await self._try_providers("get_breadth_data", market_id)

    # ── Options & volatility ──────────────────────────────────────────

    async def get_options_data(
        self,
        ticker: str,
    ) -> Optional[Dict[str, Any]]:
        """Fetch options-market indicators from the first successful provider."""
        return await self._try_providers("get_options_data", ticker)

    # ── Credit & macro ────────────────────────────────────────────────

    async def get_credit_spreads(
        self,
        series_id: str = "BAMLH0A0HYM2",
    ) -> Optional[Dict[str, Any]]:
        """Fetch credit spreads from the first successful provider."""
        return await self._try_providers("get_credit_spreads", series_id)

    async def get_safe_haven_assets(
        self,
    ) -> Optional[Dict[str, Any]]:
        """Fetch safe-haven asset prices from the first successful provider."""
        return await self._try_providers("get_safe_haven_assets")

    # ── News & social ─────────────────────────────────────────────────

    async def get_news_articles(
        self,
        query: str = "stock market",
        limit: int = 20,
    ) -> List[Article]:
        """Fetch news articles from the first successful provider.

        Returns an empty list if no provider succeeds.
        """
        result = await self._try_providers("get_news_articles", query, limit=limit)
        return result if result is not None else []

    async def get_social_posts(
        self,
        query: str = "stock market",
        limit: int = 50,
    ) -> List[SocialPost]:
        """Fetch social-media posts from the first successful provider.

        Returns an empty list if no provider succeeds.
        """
        result = await self._try_providers("get_social_posts", query, limit=limit)
        return result if result is not None else []

    # ── Flows & positioning ───────────────────────────────────────────

    async def get_flows_data(
        self,
        ticker: str = "SPY",
    ) -> Optional[Dict[str, Any]]:
        """Fetch fund-flow data from the first successful provider."""
        return await self._try_providers("get_flows_data", ticker)

    # ── Diagnostics ───────────────────────────────────────────────────

    async def get_source_status(self) -> List[SourceStatus]:
        """Aggregate health status from **all** providers.

        Unlike data-fetch methods, this queries every provider (not just
        the first successful one) so the admin UI can display a complete
        source-status table.

        Returns:
            List of :class:`SourceStatus` objects, one per provider.
        """
        statuses: List[SourceStatus] = []
        for provider in self.providers:
            try:
                status = await provider.get_source_status()
                statuses.append(status)
            except Exception as exc:
                logger.warning(
                    "get_source_status failed for %s: %s", provider.name, exc
                )
                statuses.append(
                    SourceStatus(
                        provider=provider.name,
                        available=False,
                        error_count_24h=1,
                        tier=provider.tier,
                    )
                )
        return statuses

    def provider_names(self) -> List[str]:
        """Return the ordered list of provider names in the chain."""
        return [p.name for p in self.providers]

    def __repr__(self) -> str:
        names = ", ".join(f"{p.name}({p.tier})" for p in self.providers)
        return f"ProviderChain([{names}])"
