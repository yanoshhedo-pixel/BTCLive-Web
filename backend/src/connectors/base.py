"""
Base connector class for exchange WebSocket connections.
"""
from abc import ABC, abstractmethod
from typing import Callable, Optional, Dict, Any
import asyncio
import json
from loguru import logger


class BaseConnector(ABC):
    """Base class for exchange WebSocket connectors."""
    
    def __init__(self, symbol: str = "BTCUSDT"):
        self.symbol = symbol
        self.ws = None
        self.running = False
        self.callbacks: Dict[str, list] = {
            "orderbook": [],
            "trades": []
        }
    
    def on_orderbook(self, callback: Callable):
        """Register callback for order book updates."""
        self.callbacks["orderbook"].append(callback)
    
    def on_trades(self, callback: Callable):
        """Register callback for trade updates."""
        self.callbacks["trades"].append(callback)
    
    async def _emit_orderbook(self, data: Dict[str, Any]):
        """Emit order book update to all registered callbacks."""
        for callback in self.callbacks["orderbook"]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in orderbook callback: {e}")
    
    async def _emit_trades(self, data: Dict[str, Any]):
        """Emit trade update to all registered callbacks."""
        for callback in self.callbacks["trades"]:
            try:
                await callback(data)
            except Exception as e:
                logger.error(f"Error in trades callback: {e}")
    
    @abstractmethod
    async def connect(self):
        """Establish WebSocket connection."""
        pass
    
    @abstractmethod
    async def disconnect(self):
        """Close WebSocket connection."""
        pass
    
    @abstractmethod
    async def _handle_message(self, message: str):
        """Handle incoming WebSocket message."""
        pass
    
    async def run(self):
        """Main loop for WebSocket connection."""
        self.running = True
        while self.running:
            try:
                await self.connect()
            except Exception as e:
                logger.error(f"Connection error: {e}")
                await asyncio.sleep(5)  # Reconnect delay
