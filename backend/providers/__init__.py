"""Provider layer for Westwood MarketPulse.

This package exposes all data providers and the provider chain manager.
Providers are organized by tier: public (free), premium (paid), and
professional (institutional).

Usage:
    from backend.providers import ProviderChain, MockProvider, YFinanceProvider
    from backend.providers.base import BaseProvider

    chain = ProviderChain([
        BloombergMCPProvider(),
        YFinanceProvider(),
        MockProvider(),
    ])
    quotes = await chain.get_current_quote("SPY")
"""

from backend.providers.base import BaseProvider
from backend.providers.provider_chain import ProviderChain
from backend.providers.mock_provider import MockProvider
from backend.providers.yfinance_provider import YFinanceProvider
from backend.providers.fred_provider import FREDProvider
from backend.providers.cboe_provider import CBOEProvider
from backend.providers.rss_news_provider import RSSNewsProvider
from backend.providers.fmp_provider import FMPProvider
from backend.providers.bloomberg_mcp_provider import BloombergMCPProvider
from backend.providers.manual_csv_provider import ManualCSVProvider
from backend.providers.daily_export_provider import DailyExportProvider
from backend.providers.x_provider import XProvider
from backend.providers.reddit_provider import RedditProvider
from backend.providers.stocktwits_provider import StockTwitsProvider

__all__ = [
    "BaseProvider",
    "ProviderChain",
    "MockProvider",
    "YFinanceProvider",
    "FREDProvider",
    "CBOEProvider",
    "RSSNewsProvider",
    "FMPProvider",
    "BloombergMCPProvider",
    "ManualCSVProvider",
    "DailyExportProvider",
    "XProvider",
    "RedditProvider",
    "StockTwitsProvider",
]
