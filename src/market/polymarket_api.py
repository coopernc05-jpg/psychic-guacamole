"""Polymarket API client for market data retrieval."""

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
        self.base_url = config.polymarket_api_url
        self.session: Optional[aiohttp.ClientSession] = None
        self.api_key = config.polymarket_api_key
        self.secret = config.polymarket_secret
    
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
    
    async def _request(
        self, 
        method: str, 
        endpoint: str, 
        params: Optional[Dict] = None,
        data: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """Make an API request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            data: Request body data
            retry_count: Current retry attempt
            
        Returns:
            API response as dictionary
        """
        if self.session is None:
            await self.connect()
        
        url = f"{self.base_url}{endpoint}"
        headers = {}
        
        if self.api_key:
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
                return await self._request(method, endpoint, params, data, retry_count + 1)
            else:
                logger.error(f"API request failed after {retry_count + 1} attempts: {e}")
                raise
    
    async def get_markets(
        self, 
        category: Optional[str] = None,
        limit: int = 100
    ) -> List[Market]:
        """Fetch active markets from Polymarket.
        
        Args:
            category: Filter by category (optional)
            limit: Maximum number of markets to fetch
            
        Returns:
            List of Market objects
        """
        params = {"limit": limit}
        if category:
            params["category"] = category
        
        try:
            # Note: This is a mock implementation as actual Polymarket API structure may vary
            # In production, this would use the real API endpoints
            response = await self._request("GET", "/markets", params=params)
            
            markets = []
            for market_data in response.get("markets", []):
                market = self._parse_market(market_data)
                if market:
                    markets.append(market)
            
            logger.info(f"Fetched {len(markets)} markets")
            return markets
        
        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []
    
    async def get_market(self, market_id: str) -> Optional[Market]:
        """Fetch a specific market by ID.
        
        Args:
            market_id: Market identifier
            
        Returns:
            Market object or None if not found
        """
        try:
            response = await self._request("GET", f"/markets/{market_id}")
            return self._parse_market(response)
        
        except Exception as e:
            logger.error(f"Error fetching market {market_id}: {e}")
            return None
    
    async def get_order_book(self, market_id: str, outcome: str) -> Optional[OrderBook]:
        """Fetch order book for a market outcome.
        
        Args:
            market_id: Market identifier
            outcome: Outcome (YES or NO)
            
        Returns:
            OrderBook object or None if not found
        """
        try:
            response = await self._request(
                "GET", 
                f"/markets/{market_id}/order-book",
                params={"outcome": outcome}
            )
            
            bids = [(float(b["price"]), float(b["size"])) for b in response.get("bids", [])]
            asks = [(float(a["price"]), float(a["size"])) for a in response.get("asks", [])]
            
            return OrderBook(
                market_id=market_id,
                outcome=outcome,
                bids=bids,
                asks=asks,
                timestamp=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Error fetching order book for {market_id}: {e}")
            return None
    
    def _parse_market(self, data: Dict[str, Any]) -> Optional[Market]:
        """Parse market data from API response.
        
        Args:
            data: Raw market data from API
            
        Returns:
            Market object or None if parsing fails
        """
        try:
            # Mock implementation - adjust based on actual API response structure
            return Market(
                market_id=data.get("id", ""),
                question=data.get("question", ""),
                description=data.get("description", ""),
                category=data.get("category", "unknown"),
                end_date=datetime.fromisoformat(data.get("end_date", datetime.now().isoformat())),
                status=MarketStatus(data.get("status", "active")),
                yes_price=float(data.get("yes_price", 0.5)),
                no_price=float(data.get("no_price", 0.5)),
                yes_bid=float(data.get("yes_bid", 0.48)),
                yes_ask=float(data.get("yes_ask", 0.52)),
                no_bid=float(data.get("no_bid", 0.48)),
                no_ask=float(data.get("no_ask", 0.52)),
                volume_24h=float(data.get("volume_24h", 0)),
                liquidity=float(data.get("liquidity", 0)),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Error parsing market data: {e}")
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
