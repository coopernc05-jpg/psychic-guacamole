"""
Polymarket WebSocket Client
Handles real-time connections to Polymarket and price feed monitoring
"""
import asyncio
import json
import logging
from typing import Dict, List, Callable, Optional
import websockets
from datetime import datetime

logger = logging.getLogger(__name__)


class PolymarketWSClient:
    """WebSocket client for Polymarket real-time data"""
    
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.websocket = None
        self.subscribed_markets: Dict[str, dict] = {}
        self.price_callbacks: List[Callable] = []
        self.is_connected = False
        
    async def connect(self):
        """Establish WebSocket connection"""
        try:
            self.websocket = await websockets.connect(self.ws_url)
            self.is_connected = True
            logger.info(f"Connected to Polymarket WebSocket: {self.ws_url}")
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise
    
    async def subscribe_to_market(self, market_id: str):
        """Subscribe to price updates for a specific market"""
        if not self.is_connected:
            raise ConnectionError("WebSocket not connected")
        
        subscribe_message = {
            "type": "subscribe",
            "market": market_id
        }
        
        try:
            await self.websocket.send(json.dumps(subscribe_message))
            logger.info(f"Subscribed to market: {market_id}")
        except Exception as e:
            logger.error(f"Failed to subscribe to market {market_id}: {e}")
    
    async def subscribe_to_markets(self, market_ids: List[str]):
        """Subscribe to multiple markets"""
        for market_id in market_ids:
            await self.subscribe_to_market(market_id)
    
    def add_price_callback(self, callback: Callable):
        """Add a callback function to be called when prices are updated"""
        self.price_callbacks.append(callback)
    
    async def listen(self):
        """Listen for incoming messages and process price updates"""
        if not self.is_connected:
            raise ConnectionError("WebSocket not connected")
        
        try:
            async for message in self.websocket:
                await self._process_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket connection closed")
            self.is_connected = False
        except Exception as e:
            logger.error(f"Error in listen loop: {e}")
            raise
    
    async def _process_message(self, message: str):
        """Process incoming WebSocket message"""
        try:
            data = json.loads(message)
            
            if data.get("type") == "price_update":
                market_id = data.get("market_id")
                price_data = {
                    "market_id": market_id,
                    "yes_price": float(data.get("yes_price", 0)),
                    "no_price": float(data.get("no_price", 0)),
                    "yes_bid": float(data.get("yes_bid", 0)),
                    "yes_ask": float(data.get("yes_ask", 0)),
                    "no_bid": float(data.get("no_bid", 0)),
                    "no_ask": float(data.get("no_ask", 0)),
                    "timestamp": datetime.now().isoformat(),
                    "event_name": data.get("event_name", ""),
                    "outcome": data.get("outcome", "")
                }
                
                # Update internal market data
                self.subscribed_markets[market_id] = price_data
                
                # Call all registered callbacks
                for callback in self.price_callbacks:
                    await callback(price_data)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode message: {e}")
        except Exception as e:
            logger.error(f"Error processing message: {e}")
    
    async def close(self):
        """Close WebSocket connection"""
        if self.websocket:
            await self.websocket.close()
            self.is_connected = False
            logger.info("WebSocket connection closed")
    
    def get_market_data(self, market_id: str) -> Optional[dict]:
        """Get current cached data for a market"""
        return self.subscribed_markets.get(market_id)
    
    def get_all_markets(self) -> Dict[str, dict]:
        """Get all cached market data"""
        return self.subscribed_markets.copy()
