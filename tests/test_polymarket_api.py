"""Unit tests for Polymarket API client."""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch
from src.config import Config
from src.market.polymarket_api import PolymarketAPIClient
from src.market.market_data import MarketStatus


@pytest.fixture
def config():
    """Create a test configuration."""
    return Config(
        polymarket_api_url="https://clob.polymarket.com",
        api_timeout=10,
        api_retry_attempts=3,
        polymarket_api_key="test_key",
    )


@pytest.fixture
def api_client(config):
    """Create an API client for testing."""
    return PolymarketAPIClient(config)


@pytest.fixture
def sample_gamma_market():
    """Sample market data from Gamma API."""
    return {
        "conditionId": "0x123abc",
        "question": "Will Bitcoin reach $100k in 2026?",
        "description": "Market resolves YES if BTC reaches $100,000",
        "category": "Crypto",
        "tags": ["crypto", "bitcoin"],
        "clobTokenIds": ["token_yes_123", "token_no_456"],
        "outcomePrices": [0.62, 0.38],
        "volume24hr": "145000",
        "liquidity": "12000",
        "closed": False,
        "resolved": False,
        "accepting_orders": True,
        "endDate": "2026-12-31T23:59:59Z",
    }


@pytest.fixture
def sample_orderbook():
    """Sample order book from CLOB API."""
    return {
        "bids": [{"price": "0.61", "size": "1000"}, {"price": "0.60", "size": "2000"}],
        "asks": [{"price": "0.63", "size": "1500"}, {"price": "0.64", "size": "3000"}],
    }


@pytest.mark.asyncio
async def test_parse_market_with_prices_basic(api_client, sample_gamma_market):
    """Test parsing market data from Gamma API without CLOB prices."""
    # Mock get_order_book to return None (CLOB unavailable)
    with patch.object(
        api_client, "get_order_book", new_callable=AsyncMock
    ) as mock_book:
        mock_book.return_value = None

        market = await api_client._parse_market_with_prices(sample_gamma_market)

        assert market is not None
        assert market.market_id == "0x123abc"
        assert market.question == "Will Bitcoin reach $100k in 2026?"
        assert market.category == "Crypto"
        assert market.status == MarketStatus.ACTIVE
        assert market.yes_price == 0.62
        assert market.no_price == 0.38
        assert market.volume_24h == 145000.0
        assert market.liquidity == 12000.0
        # Check that bid/ask spreads were estimated
        assert market.yes_bid < market.yes_price < market.yes_ask
        assert market.no_bid < market.no_price < market.no_ask


@pytest.mark.asyncio
async def test_parse_market_with_orderbook(
    api_client, sample_gamma_market, sample_orderbook
):
    """Test parsing market with real-time order book prices."""
    from src.market.market_data import OrderBook

    # Create mock order books
    yes_book = OrderBook(
        market_id="token_yes_123",
        outcome="YES",
        bids=[(0.61, 1000), (0.60, 2000)],
        asks=[(0.63, 1500), (0.64, 3000)],
        timestamp=datetime.now(),
    )

    no_book = OrderBook(
        market_id="token_no_456",
        outcome="NO",
        bids=[(0.37, 1000), (0.36, 2000)],
        asks=[(0.39, 1500), (0.40, 3000)],
        timestamp=datetime.now(),
    )

    # Mock get_order_book to return order books
    with patch.object(
        api_client, "get_order_book", new_callable=AsyncMock
    ) as mock_book:
        mock_book.side_effect = [yes_book, no_book]

        market = await api_client._parse_market_with_prices(sample_gamma_market)

        assert market is not None
        # Prices should come from order books
        assert market.yes_bid == 0.61
        assert market.yes_ask == 0.63
        assert market.yes_price == 0.62  # Mid price
        assert market.no_bid == 0.37
        assert market.no_ask == 0.39
        assert market.no_price == 0.38  # Mid price


@pytest.mark.asyncio
async def test_skip_inactive_markets(api_client):
    """Test that inactive markets are skipped."""
    inactive_market = {
        "conditionId": "0x999",
        "question": "Closed market",
        "closed": True,
        "resolved": False,
        "clobTokenIds": [],
        "outcomePrices": [0.5, 0.5],
    }

    market = await api_client._parse_market_with_prices(inactive_market)
    assert market is None


@pytest.mark.asyncio
async def test_skip_resolved_markets(api_client):
    """Test that resolved markets are skipped."""
    resolved_market = {
        "conditionId": "0x888",
        "question": "Resolved market",
        "closed": True,
        "resolved": True,
        "clobTokenIds": [],
        "outcomePrices": [1.0, 0.0],
    }

    market = await api_client._parse_market_with_prices(resolved_market)
    assert market is None


@pytest.mark.asyncio
async def test_get_markets_with_mock_response(api_client):
    """Test get_markets with mocked API response."""
    mock_response = [
        {
            "conditionId": "0x111",
            "question": "Market 1",
            "clobTokenIds": [],
            "outcomePrices": [0.55, 0.45],
            "closed": False,
            "resolved": False,
        },
        {
            "conditionId": "0x222",
            "question": "Market 2",
            "clobTokenIds": [],
            "outcomePrices": [0.30, 0.70],
            "closed": False,
            "resolved": False,
        },
    ]

    with patch.object(api_client, "_request", new_callable=AsyncMock) as mock_request:
        with patch.object(
            api_client, "get_order_book", new_callable=AsyncMock
        ) as mock_book:
            mock_request.return_value = mock_response
            mock_book.return_value = None

            markets = await api_client.get_markets(limit=10)

            assert len(markets) == 2
            assert markets[0].market_id == "0x111"
            assert markets[1].market_id == "0x222"
            assert markets[0].yes_price == 0.55
            assert markets[1].yes_price == 0.30


@pytest.mark.asyncio
async def test_error_handling(api_client):
    """Test error handling when API fails."""
    with patch.object(api_client, "_request", new_callable=AsyncMock) as mock_request:
        mock_request.side_effect = Exception("Network error")

        markets = await api_client.get_markets()

        # Should return empty list on error, not raise exception
        assert markets == []


def test_rate_limiting(api_client):
    """Test that rate limiting is configured."""
    assert api_client._min_request_interval == 0.1
    assert api_client._last_request_time == 0


@pytest.mark.asyncio
async def test_api_urls(api_client):
    """Test that API URLs are correctly configured."""
    assert api_client.clob_url == "https://clob.polymarket.com"
    assert api_client.gamma_url == "https://gamma-api.polymarket.com"
