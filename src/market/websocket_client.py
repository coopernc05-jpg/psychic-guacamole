"""WebSocket client for real-time Polymarket data."""

import asyncio
import json
from typing import Callable, Optional, Set
from datetime import datetime
from loguru import logger
import websockets
from websockets.exceptions import WebSocketException

from ..config import Config
from .market_data import Market


class WebSocketClient:
    """WebSocket client for real-time market updates."""
    
    def __init__(self, config: Config):
        """Initialize WebSocket client.
        
        Args:
            config: Configuration object
        """
        self.config = config
        self.ws_url = config.polymarket_ws_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.subscribed_markets: Set[str] = set()
        self.callbacks: list[Callable] = []
        self.is_running = False
        self._reconnect_delay = 1
        self._max_reconnect_delay = 60
    
    async def connect(self):
        """Connect to WebSocket server."""
        try:
            self.websocket = await websockets.connect(
                self.ws_url,
                ping_interval=20,
                ping_timeout=10
            )
            self.is_running = True
            self._reconnect_delay = 1
            logger.info("Connected to Polymarket WebSocket")
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            raise
    
    async def disconnect(self):
        """Disconnect from WebSocket server."""
        self.is_running = False
        if self.websocket:
            await self.websocket.close()
            self.websocket = None
            logger.info("Disconnected from Polymarket WebSocket")
    
    async def subscribe_market(self, market_id: str):
        """Subscribe to market updates.
        
        Args:
            market_id: Market identifier to subscribe to
        """
        if not self.websocket:
            raise RuntimeError("WebSocket not connected")
        
        subscribe_msg = {
            "type": "subscribe",
            "channel": "market",
            "market_id": market_id
        }
        
        await self.websocket.send(json.dumps(subscribe_msg))
        self.subscribed_markets.add(market_id)
        logger.debug(f"Subscribed to market: {market_id}")
    
    async def unsubscribe_market(self, market_id: str):
        """Unsubscribe from market updates.
        
        Args:
            market_id: Market identifier to unsubscribe from
        """
        if not self.websocket:
            return
        
        unsubscribe_msg = {
            "type": "unsubscribe",
            "channel": "market",
            "market_id": market_id
        }
        
        await self.websocket.send(json.dumps(unsubscribe_msg))
        self.subscribed_markets.discard(market_id)
        logger.debug(f"Unsubscribed from market: {market_id}")
    
    def register_callback(self, callback: Callable):
        """Register a callback for market updates.
        
        Args:
            callback: Async function to call on market updates
        """
        self.callbacks.append(callback)
    
    async def listen(self):
        """Listen for WebSocket messages and process them."""
        while self.is_running:
            try:
                if not self.websocket:
                    await self.connect()
                
                async for message in self.websocket:
                    try:
                        data = json.loads(message)
                        await self._handle_message(data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse WebSocket message: {e}")
                    except Exception as e:
                        logger.error(f"Error handling WebSocket message: {e}")
            
            except WebSocketException as e:
                logger.warning(f"WebSocket connection lost: {e}")
                if self.is_running:
                    await self._reconnect()
            
            except Exception as e:
                logger.error(f"Unexpected error in WebSocket listener: {e}")
                if self.is_running:
                    await self._reconnect()
    
    async def _reconnect(self):
        """Attempt to reconnect to WebSocket."""
        await asyncio.sleep(self._reconnect_delay)
        self._reconnect_delay = min(self._reconnect_delay * 2, self._max_reconnect_delay)
        
        logger.info(f"Attempting to reconnect to WebSocket...")
        try:
            await self.connect()
            
            # Re-subscribe to all markets
            for market_id in list(self.subscribed_markets):
                await self.subscribe_market(market_id)
            
            logger.info("Reconnected and re-subscribed to markets")
        except Exception as e:
            logger.error(f"Reconnection failed: {e}")
    
    async def _handle_message(self, data: dict):
        """Handle incoming WebSocket message.
        
        Args:
            data: Parsed message data
        """
        message_type = data.get("type")
        
        if message_type == "market_update":
            # Process market update and notify callbacks
            market_id = data.get("market_id")
            update = {
                "market_id": market_id,
                "yes_price": data.get("yes_price"),
                "no_price": data.get("no_price"),
                "yes_bid": data.get("yes_bid"),
                "yes_ask": data.get("yes_ask"),
                "no_bid": data.get("no_bid"),
                "no_ask": data.get("no_ask"),
                "timestamp": datetime.now()
            }
            
            # Notify all registered callbacks
            for callback in self.callbacks:
                try:
                    await callback(update)
                except Exception as e:
                    logger.error(f"Error in callback: {e}")
        
        elif message_type == "trade":
            # Handle trade execution notification
            logger.debug(f"Trade notification: {data}")
        
        elif message_type == "error":
            logger.error(f"WebSocket error: {data.get('message')}")
        
        else:
            logger.debug(f"Unknown message type: {message_type}")
