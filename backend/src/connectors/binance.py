"""
Binance Futures WebSocket connector.
"""
import json
import asyncio
import websockets
from loguru import logger
from .base import BaseConnector


class BinanceConnector(BaseConnector):
    """Binance Futures WebSocket connector for BTCUSDT perpetual."""
    
    def __init__(self, symbol: str = "btcusdt"):
        super().__init__(symbol)
        self.depth_url = f"wss://fstream.binance.com/ws/{symbol}@depth20@100ms"
        self.trades_url = f"wss://fstream.binance.com/ws/{symbol}@aggTrade"
        self.depth_ws = None
        self.trades_ws = None
    
    async def connect(self):
        """Establish WebSocket connections for depth and trades."""
        logger.info(f"Connecting to Binance for {self.symbol}")
        
        # Connect to depth stream
        self.depth_ws = await websockets.connect(self.depth_url)
        logger.info("Binance depth stream connected")
        
        # Connect to trades stream
        self.trades_ws = await websockets.connect(self.trades_url)
        logger.info("Binance trades stream connected")
        
        # Start listening tasks
        await asyncio.gather(
            self._listen_depth(),
            self._listen_trades()
        )
    
    async def _listen_depth(self):
        """Listen to depth stream."""
        try:
            async for message in self.depth_ws:
                await self._handle_depth_message(message)
        except Exception as e:
            logger.error(f"Binance depth stream error: {e}")
            self.running = False
    
    async def _listen_trades(self):
        """Listen to trades stream."""
        try:
            async for message in self.trades_ws:
                await self._handle_trades_message(message)
        except Exception as e:
            logger.error(f"Binance trades stream error: {e}")
            self.running = False
    
    async def _handle_depth_message(self, message: str):
        """
        Handle depth update message.
        Format: {
            "e": "depthUpdate",
            "E": timestamp,
            "T": transaction_time,
            "s": "BTCUSDT",
            "U": first_update_id,
            "u": last_update_id,
            "b": [[price, qty], ...],  # bids
            "a": [[price, qty], ...]   # asks
        }
        """
        try:
            data = json.loads(message)
            if data.get("e") == "depthUpdate":
                normalized = {
                    "exchange": "binance",
                    "symbol": self.symbol,
                    "timestamp": data.get("E"),
                    "bids": [[float(p), float(q)] for p, q in data.get("b", [])],
                    "asks": [[float(p), float(q)] for p, q in data.get("a", [])]
                }
                await self._emit_orderbook(normalized)
        except Exception as e:
            logger.error(f"Error handling Binance depth message: {e}")
    
    async def _handle_trades_message(self, message: str):
        """
        Handle trades message.
        Format: {
            "e": "aggTrade",
            "E": event_time,
            "s": "BTCUSDT",
            "a": agg_trade_id,
            "p": price,
            "q": quantity,
            "f": first_trade_id,
            "l": last_trade_id,
            "T": trade_time,
            "m": is_buyer_maker
        }
        """
        try:
            data = json.loads(message)
            if data.get("e") == "aggTrade":
                normalized = {
                    "exchange": "binance",
                    "symbol": self.symbol,
                    "timestamp": data.get("T"),
                    "price": float(data.get("p")),
                    "quantity": float(data.get("q")),
                    "side": "sell" if data.get("m") else "buy"  # m=true means buyer is maker (sell)
                }
                await self._emit_trades(normalized)
        except Exception as e:
            logger.error(f"Error handling Binance trades message: {e}")
    
    async def _handle_message(self, message: str):
        """Handle incoming message (not used in this implementation)."""
        pass
    
    async def disconnect(self):
        """Close WebSocket connections."""
        self.running = False
        if self.depth_ws:
            await self.depth_ws.close()
        if self.trades_ws:
            await self.trades_ws.close()
        logger.info("Binance connector disconnected")
