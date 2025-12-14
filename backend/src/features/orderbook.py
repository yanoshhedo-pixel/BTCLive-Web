"""
Order book maintenance and feature extraction.
"""
from typing import Dict, List, Tuple
import numpy as np
from collections import deque
from loguru import logger


class OrderBook:
    """Maintain and analyze order book state."""
    
    def __init__(self, exchange: str, symbol: str, max_depth: int = 20):
        self.exchange = exchange
        self.symbol = symbol
        self.max_depth = max_depth
        
        # Order book state
        self.bids: Dict[float, float] = {}  # price -> quantity
        self.asks: Dict[float, float] = {}  # price -> quantity
        
        # Last update timestamp
        self.last_update = 0
        
        # Historical snapshots for analysis
        self.history = deque(maxlen=100)
    
    def update(self, bids: List[List[float]], asks: List[List[float]], timestamp: int):
        """
        Update order book with new data.
        
        Args:
            bids: List of [price, quantity] for bids
            asks: List of [price, quantity] for asks
            timestamp: Update timestamp in milliseconds
        """
        # Update bids
        for price, qty in bids:
            if qty == 0:
                self.bids.pop(price, None)
            else:
                self.bids[price] = qty
        
        # Update asks
        for price, qty in asks:
            if qty == 0:
                self.asks.pop(price, None)
            else:
                self.asks[price] = qty
        
        self.last_update = timestamp
        
        # Save snapshot for historical analysis
        self._save_snapshot()
    
    def _save_snapshot(self):
        """Save current order book snapshot."""
        snapshot = {
            "timestamp": self.last_update,
            "bids": sorted(self.bids.items(), reverse=True)[:self.max_depth],
            "asks": sorted(self.asks.items())[:self.max_depth],
            "spread": self.get_spread(),
            "mid_price": self.get_mid_price()
        }
        self.history.append(snapshot)
    
    def get_best_bid(self) -> Tuple[float, float]:
        """Get best bid price and quantity."""
        if not self.bids:
            return 0.0, 0.0
        best_price = max(self.bids.keys())
        return best_price, self.bids[best_price]
    
    def get_best_ask(self) -> Tuple[float, float]:
        """Get best ask price and quantity."""
        if not self.asks:
            return 0.0, 0.0
        best_price = min(self.asks.keys())
        return best_price, self.asks[best_price]
    
    def get_mid_price(self) -> float:
        """Get mid price."""
        best_bid, _ = self.get_best_bid()
        best_ask, _ = self.get_best_ask()
        if best_bid == 0 or best_ask == 0:
            return 0.0
        return (best_bid + best_ask) / 2
    
    def get_spread(self) -> float:
        """Get spread in dollars."""
        best_bid, _ = self.get_best_bid()
        best_ask, _ = self.get_best_ask()
        return best_ask - best_bid
    
    def get_spread_bps(self) -> float:
        """Get spread in basis points."""
        spread = self.get_spread()
        mid = self.get_mid_price()
        if mid == 0:
            return 0.0
        return (spread / mid) * 10000
    
    def get_depth_liquidity(self, side: str, levels: int = 10) -> float:
        """
        Calculate total liquidity at specified depth.
        
        Args:
            side: "bid" or "ask"
            levels: Number of levels to include
        
        Returns:
            Total USD value of liquidity
        """
        if side == "bid":
            sorted_levels = sorted(self.bids.items(), reverse=True)[:levels]
        else:
            sorted_levels = sorted(self.asks.items())[:levels]
        
        return sum(price * qty for price, qty in sorted_levels)
    
    def get_imbalance(self, levels: int = 5) -> float:
        """
        Calculate order book imbalance.
        
        Args:
            levels: Number of levels to include
        
        Returns:
            Imbalance ratio between -1 (all asks) and 1 (all bids)
        """
        bid_liq = self.get_depth_liquidity("bid", levels)
        ask_liq = self.get_depth_liquidity("ask", levels)
        
        total = bid_liq + ask_liq
        if total == 0:
            return 0.0
        
        return (bid_liq - ask_liq) / total
    
    def detect_liquidity_shelf(self, side: str, threshold_multiplier: float = 3.0) -> Tuple[float, float]:
        """
        Detect significant liquidity concentration (shelf).
        
        Args:
            side: "bid" or "ask"
            threshold_multiplier: Multiplier above average to be considered a shelf
        
        Returns:
            Tuple of (price, quantity) for the largest shelf, or (0, 0) if none found
        """
        if side == "bid":
            levels = sorted(self.bids.items(), reverse=True)[:20]
        else:
            levels = sorted(self.asks.items())[:20]
        
        if not levels:
            return 0.0, 0.0
        
        quantities = [qty for _, qty in levels]
        avg_qty = np.mean(quantities)
        threshold = avg_qty * threshold_multiplier
        
        # Find largest shelf
        shelves = [(price, qty) for price, qty in levels if qty > threshold]
        if not shelves:
            return 0.0, 0.0
        
        return max(shelves, key=lambda x: x[1])
    
    def estimate_slippage(self, side: str, size_usd: float) -> float:
        """
        Estimate slippage for a market order of given size.
        
        Args:
            side: "buy" or "sell"
            size_usd: Order size in USD
        
        Returns:
            Estimated slippage in basis points
        """
        if side == "buy":
            levels = sorted(self.asks.items())
        else:
            levels = sorted(self.bids.items(), reverse=True)
        
        if not levels:
            return 999.9  # Large value to indicate no liquidity
        
        start_price = levels[0][0]
        remaining = size_usd
        total_cost = 0.0
        
        for price, qty in levels:
            level_value = price * qty
            if level_value >= remaining:
                total_cost += remaining
                break
            else:
                total_cost += level_value
                remaining -= level_value
        
        if remaining > 0:
            return 999.9  # Not enough liquidity
        
        avg_price = total_cost / size_usd
        slippage_bps = abs((avg_price - start_price) / start_price) * 10000
        
        return slippage_bps
