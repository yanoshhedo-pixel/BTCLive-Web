"""
Bybit WebSocket connector.
"""
import json
import asyncio
import websockets
from loguru import logger
from .base import BaseConnector


class BybitConnector(BaseConnector):
    """Bybit WebSocket connector for BTCUSDT perpetual."""
    
    def __init__(self, symbol: str = "BTCUSDT"):
        super().__init__(symbol)
        self.ws_url = "wss://stream.bybit.com/v5/public/linear"
    
    async def connect(self):
        """Establish WebSocket connection."""
        logger.info(f"Connecting to Bybit for {self.symbol}")
        
        self.ws = await websockets.connect(self.ws_url)
        logger.info("Bybit WebSocket connected")
        
        # Subscribe to orderbook and trades
        await self._subscribe()
        
        # Start listening
        await self._listen()
    
    async def _subscribe(self):
        """Subscribe to orderbook and trades streams."""
        # Subscribe to orderbook (depth 50)
        orderbook_sub = {
            "op": "subscribe",
            "args": [f"orderbook.50.{self.symbol}"]
        }
        await self.ws.send(json.dumps(orderbook_sub))
        
        # Subscribe to trades
        trades_sub = {
            "op": "subscribe",
            "args": [f"publicTrade.{self.symbol}"]
        }
        await self.ws.send(json.dumps(trades_sub))
        
        logger.info(f"Subscribed to Bybit streams for {self.symbol}")
    
    async def _listen(self):
        """Listen to WebSocket messages."""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except Exception as e:
            logger.error(f"Bybit stream error: {e}")
            self.running = False
    
    async def _handle_message(self, message: str):
        """
        Handle incoming WebSocket message.
        Bybit sends messages in format:
        {
            "topic": "orderbook.50.BTCUSDT",
            "type": "snapshot" or "delta",
            "ts": timestamp,
            "data": {
                "s": "BTCUSDT",
                "b": [[price, size], ...],
                "a": [[price, size], ...],
                ...
            }
        }
        """
        try:
            data = json.loads(message)
            
            # Handle ping
            if data.get("op") == "ping":
                await self.ws.send(json.dumps({"op": "pong"}))
                return
            
            topic = data.get("topic", "")
            
            # Handle orderbook updates
            if topic.startswith("orderbook"):
                await self._handle_orderbook(data)
            
            # Handle trades
            elif topic.startswith("publicTrade"):
                await self._handle_trades(data)
                
        except Exception as e:
            logger.error(f"Error handling Bybit message: {e}")
    
    async def _handle_orderbook(self, data: dict):
        """Handle orderbook update."""
        try:
            orderbook_data = data.get("data", {})
            normalized = {
                "exchange": "bybit",
                "symbol": self.symbol,
                "timestamp": data.get("ts"),
                "bids": [[float(p), float(q)] for p, q in orderbook_data.get("b", [])],
                "asks": [[float(p), float(q)] for p, q in orderbook_data.get("a", [])]
            }
            await self._emit_orderbook(normalized)
        except Exception as e:
            logger.error(f"Error handling Bybit orderbook: {e}")
    
    async def _handle_trades(self, data: dict):
        """
        Handle trades update.
        Format: {
            "topic": "publicTrade.BTCUSDT",
            "type": "snapshot",
            "ts": timestamp,
            "data": [{
                "T": timestamp,
                "s": "BTCUSDT",
                "S": "Buy" or "Sell",
                "v": volume,
                "p": price,
                ...
            }]
        }
        """
        try:
            trades = data.get("data", [])
            for trade in trades:
                normalized = {
                    "exchange": "bybit",
                    "symbol": self.symbol,
                    "timestamp": trade.get("T"),
                    "price": float(trade.get("p")),
                    "quantity": float(trade.get("v")),
                    "side": trade.get("S", "").lower()
                }
                await self._emit_trades(normalized)
        except Exception as e:
            logger.error(f"Error handling Bybit trades: {e}")
    
    async def disconnect(self):
        """Close WebSocket connection."""
        self.running = False
        if self.ws:
            await self.ws.close()
        logger.info("Bybit connector disconnected")
