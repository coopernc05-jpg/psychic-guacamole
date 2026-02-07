"""Polymarket API client for market data retrieval.

This module integrates with two Polymarket APIs:
1. Gamma API (https://gamma-api.polymarket.com) - For discovering markets and metadata
2. CLOB API (https://clob.polymarket.com) - For real-time prices and order books

The Gamma API provides market listings, while CLOB API provides trading data.
Authentication is optional for read-only endpoints.
"""

import asyncio
from datetime import datetime
from typing import List, Optional, Dict, Any
from loguru import logger
import aiohttp

from ..config import Config
from .market_data import Market, MarketStatus, OrderBook


class PolymarketAPIClient:
    """Client for interacting with Polymarket API."""
    
    def __init__(self, config: Config):
        """Initialize the API client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        # Use CLOB API as base_url (from config)
        self.clob_url = config.polymarket_api_url
        # Gamma API for market discovery
        self.gamma_url = "https://gamma-api.polymarket.com"
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = config.polymarket_api_key
        self.secret = config.polymarket_secret
        # Rate limiting
        self._last_request_time = 0
        self._min_request_interval = 0.1  # 100ms between requests
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.connect()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def connect(self):
        """Establish connection to the API."""
        if self.session is None:
            timeout = aiohttp.ClientTimeout(total=self.config.api_timeout)
            self.session = aiohttp.ClientSession(timeout=timeout)
            logger.info("Connected to Polymarket API")
    
    async def close(self):
        """Close the API connection."""
        if self.session:
            await self.session.close()
            self.session = None
            logger.info("Closed Polymarket API connection")
    
    async def _rate_limit(self):
        """Implement rate limiting to avoid overwhelming the API."""
        current_time = asyncio.get_event_loop().time()
        time_since_last = current_time - self._last_request_time
        if time_since_last < self._min_request_interval:
            await asyncio.sleep(self._min_request_interval - time_since_last)
        self._last_request_time = asyncio.get_event_loop().time()
    
    async def _request(
        self, 
        method: str, 
        url: str,
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = 0,
        use_auth: bool = False
    ) -> Dict[str, Any]:
        """Make an API request with retry logic.
        
        Args:
            method: HTTP method
            url: Full URL to request
            params: Query parameters
            data: Request body data
            retry_count: Current retry attempt
            use_auth: Whether to include API key authentication
            
        Returns:
            API response as dictionary
        """
        if self.session is None:
            await self.connect()
        
        # Rate limiting
        await self._rate_limit()
        
        headers = {}
        if use_auth and self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            async with self.session.request(
                method, url, params=params, json=data, headers=headers
            ) as response:
                response.raise_for_status()
                return await response.json()
        
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
            if retry_count < self.config.api_retry_attempts:
                wait_time = 2 ** retry_count  # Exponential backoff
                logger.warning(
                    f"API request failed (attempt {retry_count + 1}): {e}. "
                    f"Retrying in {wait_time}s..."
                )
                await asyncio.sleep(wait_time)
                return await self._request(method, url, params, data, retry_count + 1, use_auth)
            else:
                logger.error(f"API request failed after {retry_count + 1} attempts: {e}")
                raise
    
    async def get_markets(
        self, 
        category: Optional[str] = None,
        limit: int = 100,
        active: bool = True
    ) -> List[Market]:
        """Fetch active markets from Polymarket using Gamma API.
        
        The Gamma API is used for market discovery. We then enrich the data
        with real-time prices from the CLOB API for each market's tokens.
        
        Args:
            category: Filter by category (optional)
            limit: Maximum number of markets to fetch
            active: Only fetch active markets (default: True)
            
        Returns:
            List of Market objects with real-time pricing data
        """
        params = {"limit": limit}
        if active:
            params["active"] = "true"
        
        try:
            logger.info(f"Fetching markets from Gamma API (limit={limit}, active={active})")
            
            # Fetch markets from Gamma API
            url = f"{self.gamma_url}/markets"
            response = await self._request("GET", url, params=params)
            
            # Response can be a list or a dict with a data/markets field
            markets_data = response if isinstance(response, list) else response.get("data", response.get("markets", []))
            
            logger.info(f"Received {len(markets_data)} markets from Gamma API")
            
            markets = []
            for market_data in markets_data[:limit]:  # Ensure we don't exceed limit
                try:
                    market = await self._parse_market_with_prices(market_data)
                    if market:
                        markets.append(market)
                except Exception as e:
                    logger.warning(f"Failed to parse market {market_data.get('id', 'unknown')}: {e}")
                    continue
            
            logger.info(f"Successfully parsed {len(markets)} markets with price data")
            
            # Log sample market data for debugging
            if markets:
                sample = markets[0]
                logger.debug(f"Sample market: {sample.question[:50]}... | "
                           f"YES: {sample.yes_price:.3f} | NO: {sample.no_price:.3f}")
            
            return markets
        
        except Exception as e:
            logger.error(f"Error fetching markets: {e}", exc_info=True)
            return []
    
    async def get_market(self, market_id: str) -> Optional[Market]:
        """Fetch a specific market by ID from Gamma API.
        
        Args:
            market_id: Market identifier
            
        Returns:
            Market object or None if not found
        """
        try:
            url = f"{self.gamma_url}/markets/{market_id}"
            response = await self._request("GET", url)
            return await self._parse_market_with_prices(response)
        
        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None
    
    async def get_token_price(self, token_id: str, side: str = "BUY") -> Optional[float]:
        """Get current price for a token from CLOB API.
        
        Args:
            token_id: Token identifier (from market's clobTokenIds)
            side: BUY or SELL
            
        Returns:
            Current price or None if unavailable
        """
        try:
            url = f"{self.clob_url}/price"
            params = {"token_id": token_id, "side": side}
            response = await self._request("GET", url, params=params)
            
            # Response format: {"price": "0.52"} or similar
            price_str = response.get("price", response.get("mid", "0"))
            return float(price_str) if price_str else None
        
        except Exception as e:
            logger.debug(f"Error fetching price for token {token_id}: {e}")
            return None
    
    async def get_order_book(self, token_id: str) -> Optional[OrderBook]:
        """Fetch order book for a token from CLOB API.
        
        Args:
            token_id: Token identifier
            
        Returns:
            OrderBook object or None if not found
        """
        try:
            url = f"{self.clob_url}/book"
            params = {"token_id": token_id}
            response = await self._request("GET", url, params=params)
            
            # Parse bids and asks
            bids = []
            for bid in response.get("bids", []):
                price = float(bid.get("price", 0))
                size = float(bid.get("size", 0))
                if price > 0 and size > 0:
                    bids.append((price, size))
            
            asks = []
            for ask in response.get("asks", []):
                price = float(ask.get("price", 0))
                size = float(ask.get("size", 0))
                if price > 0 and size > 0:
                    asks.append((price, size))
            
            return OrderBook(
                market_id=token_id,
                outcome="",  # Will be set by caller
                bids=bids,
                asks=asks,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            logger.debug(f"Error fetching order book for token {token_id}: {e}")
            return None
    
    async def _parse_market_with_prices(self, data: Dict[str, Any]) -> Optional[Market]:
        """Parse market data from Gamma API and enrich with CLOB API prices.
        
        Args:
            data: Raw market data from Gamma API
            
        Returns:
            Market object with real-time prices or None if parsing fails
        """
        try:
            # Extract basic market information from Gamma API response
            condition_id = data.get("conditionId", data.get("condition_id", data.get("id", "")))
            question = data.get("question", data.get("title", "Unknown Market"))
            description = data.get("description", "")
            
            # Get category/tags
            category = data.get("category", "")
            if not category:
                tags = data.get("tags", [])
                category = tags[0] if tags else "other"
            
            # Get market status
            is_closed = data.get("closed", False)
            is_resolved = data.get("resolved", False)
            accepting_orders = data.get("accepting_orders", data.get("active", True))
            
            if is_resolved:
                status = MarketStatus.RESOLVED
            elif is_closed or not accepting_orders:
                status = MarketStatus.CLOSED
            else:
                status = MarketStatus.ACTIVE
            
            # Skip inactive markets
            if status != MarketStatus.ACTIVE:
                return None
            
            # Get end date
            end_date_str = data.get("endDate", data.get("end_date", data.get("endTime", "")))
            try:
                end_date = datetime.fromisoformat(end_date_str.replace('Z', '+00:00'))
            except:
                end_date = datetime.now()
            
            # Get volume and liquidity
            volume_24h = float(data.get("volume24hr", data.get("volume", data.get("volumeUsd", 0))))
            liquidity = float(data.get("liquidity", data.get("liquidityUsd", 0)))
            
            # Get token IDs for price lookup
            token_ids = data.get("clobTokenIds", data.get("tokens", []))
            
            # Initialize prices
            yes_price = 0.5
            no_price = 0.5
            yes_bid = 0.48
            yes_ask = 0.52
            no_bid = 0.48
            no_ask = 0.52
            
            # Try to get real-time prices from CLOB API if we have token IDs
            prices_from_clob = False
            if token_ids and len(token_ids) >= 2:
                # First token is typically YES, second is NO
                yes_token_id = token_ids[0]
                no_token_id = token_ids[1]
                
                try:
                    # Get order books for both outcomes
                    yes_book = await self.get_order_book(yes_token_id)
                    no_book = await self.get_order_book(no_token_id)
                    
                    if yes_book and yes_book.best_bid and yes_book.best_ask:
                        yes_bid = yes_book.best_bid[0]
                        yes_ask = yes_book.best_ask[0]
                        yes_price = (yes_bid + yes_ask) / 2
                        prices_from_clob = True
                    
                    if no_book and no_book.best_bid and no_book.best_ask:
                        no_bid = no_book.best_bid[0]
                        no_ask = no_book.best_ask[0]
                        no_price = (no_bid + no_ask) / 2
                        prices_from_clob = True
                
                except Exception as e:
                    logger.debug(f"Could not fetch CLOB prices for {condition_id}: {e}")
            
            # Fall back to Gamma API prices if CLOB prices unavailable
            if not prices_from_clob:
                outcome_prices = data.get("outcomePrices", data.get("prices", []))
                if outcome_prices and len(outcome_prices) >= 2:
                    yes_price = float(outcome_prices[0]) if outcome_prices[0] else 0.5
                    no_price = float(outcome_prices[1]) if outcome_prices[1] else 0.5
                    # Estimate bid/ask spread
                    spread = 0.04
                    yes_bid = max(0.01, yes_price - spread / 2)
                    yes_ask = min(0.99, yes_price + spread / 2)
                    no_bid = max(0.01, no_price - spread / 2)
                    no_ask = min(0.99, no_price + spread / 2)
            
            # Create Market object
            return Market(
                market_id=condition_id,
                question=question,
                description=description,
                category=category,
                end_date=end_date,
                status=status,
                yes_price=yes_price,
                no_price=no_price,
                yes_bid=yes_bid,
                yes_ask=yes_ask,
                no_bid=no_bid,
                no_ask=no_ask,
                volume_24h=volume_24h,
                liquidity=liquidity,
                metadata={
                    "token_ids": token_ids,
                    "raw_data": data
                }
            )
        
        except Exception as e:
            logger.error(f"Error parsing market data: {e}", exc_info=True)
            logger.debug(f"Market data: {data}")
            return None
    
    async def get_gas_price(self) -> float:
        """Get current Polygon gas price in gwei.
        
        Returns:
            Current gas price in gwei
        """
        try:
            # This would connect to Polygon network to get real gas prices
            # For now, return a mock value
            return 30.0
        except Exception as e:
            logger.error(f"Error fetching gas price: {e}")
            return 50.0  # Default fallback
