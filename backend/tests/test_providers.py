import pytest
import asyncio

from backend.providers.mock_provider import MockProvider
from backend.providers.provider_chain import ProviderChain


@pytest.mark.asyncio
async def test_mock_provider_status():
    provider = MockProvider()
    status = await provider.get_source_status()
    assert status.available is True
    assert status.provider == "mock"
    assert status.tier == "public"


@pytest.mark.asyncio
async def test_mock_provider_prices():
    provider = MockProvider()
    df = await provider.get_price_history("SPY", 30)
    assert df is not None
    assert len(df) == 30
    assert "close" in df.columns
    assert "open" in df.columns
    assert "high" in df.columns
    assert "low" in df.columns
    assert "volume" in df.columns


@pytest.mark.asyncio
async def test_mock_provider_current_quote():
    provider = MockProvider()
    quote = await provider.get_current_quote("SPY")
    assert quote is not None
    assert "price" in quote
    assert "change" in quote
    assert "change_percent" in quote


@pytest.mark.asyncio
async def test_mock_provider_articles():
    provider = MockProvider()
    articles = await provider.get_news_articles("market", 5)
    assert len(articles) == 5
    for article in articles:
        assert article.title
        assert article.source
        assert article.timestamp is not None


@pytest.mark.asyncio
async def test_mock_provider_social_posts():
    provider = MockProvider()
    posts = await provider.get_social_posts("market", 10)
    assert len(posts) == 10
    for post in posts:
        assert post.content
        assert post.author
        assert post.platform in ("stocktwits", "reddit")


@pytest.mark.asyncio
async def test_mock_provider_breadth_data():
    provider = MockProvider()
    data = await provider.get_breadth_data("sp500")
    assert data is not None
    assert "advancing" in data
    assert "declining" in data
    assert "new_highs" in data


@pytest.mark.asyncio
async def test_mock_provider_options_data():
    provider = MockProvider()
    data = await provider.get_options_data("SPY")
    assert data is not None
    assert "put_call_ratio" in data
    assert 0.7 <= data["put_call_ratio"] <= 1.2


@pytest.mark.asyncio
async def test_mock_provider_credit_spreads():
    provider = MockProvider()
    data = await provider.get_credit_spreads()
    assert data is not None
    assert "hy_spread" in data
    assert "ig_spread" in data


@pytest.mark.asyncio
async def test_mock_provider_safe_haven():
    provider = MockProvider()
    data = await provider.get_safe_haven_assets()
    assert data is not None
    assert "TLT" in data
    assert "GLD" in data
    assert "UUP" in data


@pytest.mark.asyncio
async def test_mock_provider_flows():
    provider = MockProvider()
    data = await provider.get_flows_data("SPY")
    assert data is not None
    assert "inflow" in data
    assert "outflow" in data
    assert "net_flow" in data


@pytest.mark.asyncio
async def test_provider_chain_price_history():
    chain = ProviderChain([MockProvider()])
    df = await chain.get_price_history("SPY", 30)
    assert df is not None
    assert len(df) == 30


@pytest.mark.asyncio
async def test_provider_chain_news_articles():
    chain = ProviderChain([MockProvider()])
    articles = await chain.get_news_articles("market", 5)
    assert len(articles) == 5


@pytest.mark.asyncio
async def test_provider_chain_source_status():
    chain = ProviderChain([MockProvider()])
    statuses = await chain.get_source_status()
    assert len(statuses) == 1
    assert statuses[0].provider == "mock"
    assert statuses[0].available is True


def test_provider_chain_priority():
    chain = ProviderChain([MockProvider()])
    assert chain.providers[0].tier == "public"
    assert chain.providers[0].name == "mock"


def test_provider_chain_repr():
    chain = ProviderChain([MockProvider()])
    assert "mock" in repr(chain)
    assert "public" in repr(chain)
