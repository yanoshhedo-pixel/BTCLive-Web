"""
OKX WebSocket connector.
"""
import json
import asyncio
import websockets
from loguru import logger
from .base import BaseConnector


class OKXConnector(BaseConnector):
    """OKX WebSocket connector for BTC-USDT-SWAP perpetual."""
    
    def __init__(self, symbol: str = "BTC-USDT-SWAP"):
        super().__init__(symbol)
        self.ws_url = "wss://ws.okx.com:8443/ws/v5/public"
    
    async def connect(self):
        """Establish WebSocket connection."""
        logger.info(f"Connecting to OKX for {self.symbol}")
        
        self.ws = await websockets.connect(self.ws_url)
        logger.info("OKX WebSocket connected")
        
        # Subscribe to orderbook and trades
        await self._subscribe()
        
        # Start listening
        await self._listen()
    
    async def _subscribe(self):
        """Subscribe to orderbook and trades streams."""
        # Subscribe to orderbook (depth 400)
        orderbook_sub = {
            "op": "subscribe",
            "args": [{
                "channel": "books",
                "instId": self.symbol
            }]
        }
        await self.ws.send(json.dumps(orderbook_sub))
        
        # Subscribe to trades
        trades_sub = {
            "op": "subscribe",
            "args": [{
                "channel": "trades",
                "instId": self.symbol
            }]
        }
        await self.ws.send(json.dumps(trades_sub))
        
        logger.info(f"Subscribed to OKX streams for {self.symbol}")
    
    async def _listen(self):
        """Listen to WebSocket messages."""
        try:
            async for message in self.ws:
                await self._handle_message(message)
        except Exception as e:
            logger.error(f"OKX stream error: {e}")
            self.running = False
    
    async def _handle_message(self, message: str):
        """
        Handle incoming WebSocket message.
        OKX sends messages in format:
        {
            "arg": {
                "channel": "books" or "trades",
                "instId": "BTC-USDT-SWAP"
            },
            "data": [...]
        }
        """
        try:
            data = json.loads(message)
            
            # Handle subscription confirmation
            if data.get("event") == "subscribe":
                logger.info(f"OKX subscription confirmed: {data.get('arg')}")
                return
            
            arg = data.get("arg", {})
            channel = arg.get("channel", "")
            
            # Handle orderbook updates
            if channel == "books":
                await self._handle_orderbook(data)
            
            # Handle trades
            elif channel == "trades":
                await self._handle_trades(data)
                
        except Exception as e:
            logger.error(f"Error handling OKX message: {e}")
    
    async def _handle_orderbook(self, data: dict):
        """
        Handle orderbook update.
        Format: {
            "arg": {"channel": "books", "instId": "BTC-USDT-SWAP"},
            "action": "snapshot" or "update",
            "data": [{
                "asks": [[price, size, liquidated_orders, num_orders], ...],
                "bids": [[price, size, liquidated_orders, num_orders], ...],
                "ts": timestamp,
                "checksum": int
            }]
        }
        """
        try:
            orderbook_list = data.get("data", [])
            for orderbook in orderbook_list:
                normalized = {
                    "exchange": "okx",
                    "symbol": self.symbol,
                    "timestamp": int(orderbook.get("ts")),
                    "bids": [[float(p), float(q)] for p, q, *_ in orderbook.get("bids", [])],
                    "asks": [[float(p), float(q)] for p, q, *_ in orderbook.get("asks", [])]
                }
                await self._emit_orderbook(normalized)
        except Exception as e:
            logger.error(f"Error handling OKX orderbook: {e}")
    
    async def _handle_trades(self, data: dict):
        """
        Handle trades update.
        Format: {
            "arg": {"channel": "trades", "instId": "BTC-USDT-SWAP"},
            "data": [{
                "instId": "BTC-USDT-SWAP",
                "tradeId": "123456",
                "px": price,
                "sz": size,
                "side": "buy" or "sell",
                "ts": timestamp
            }]
        }
        """
        try:
            trades = data.get("data", [])
            for trade in trades:
                normalized = {
                    "exchange": "okx",
                    "symbol": self.symbol,
                    "timestamp": int(trade.get("ts")),
                    "price": float(trade.get("px")),
                    "quantity": float(trade.get("sz")),
                    "side": trade.get("side", "").lower()
                }
                await self._emit_trades(normalized)
        except Exception as e:
            logger.error(f"Error handling OKX trades: {e}")
    
    async def disconnect(self):
        """Close WebSocket connection."""
        self.running = False
        if self.ws:
            await self.ws.close()
        logger.info("OKX connector disconnected")
