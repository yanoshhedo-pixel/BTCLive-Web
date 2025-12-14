"""
Trade flow analysis and tape reading features.
"""
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass
import time
from loguru import logger


@dataclass
class Trade:
    """Trade data structure."""
    timestamp: int
    price: float
    quantity: float
    side: str  # "buy" or "sell"
    exchange: str


class TapeAnalyzer:
    """Analyze trade flow and tape for aggressive activity."""
    
    def __init__(self, exchange: str, symbol: str, window_seconds: int = 60):
        self.exchange = exchange
        self.symbol = symbol
        self.window_seconds = window_seconds
        
        # Trade history
        self.trades: deque[Trade] = deque(maxlen=1000)
        
        # VWAP calculation
        self.vwap_cache = None
        self.vwap_cache_time = 0
    
    def add_trade(self, timestamp: int, price: float, quantity: float, side: str):
        """Add a trade to the tape."""
        trade = Trade(
            timestamp=timestamp,
            price=price,
            quantity=quantity,
            side=side,
            exchange=self.exchange
        )
        self.trades.append(trade)
    
    def _get_recent_trades(self, seconds: int = None) -> List[Trade]:
        """Get trades within specified time window."""
        if seconds is None:
            seconds = self.window_seconds
        
        if not self.trades:
            return []
        
        cutoff = self.trades[-1].timestamp - (seconds * 1000)
        return [t for t in self.trades if t.timestamp >= cutoff]
    
    def get_aggression_score(self, seconds: int = 10) -> Dict[str, float]:
        """
        Calculate aggression scores for buy and sell sides.
        
        Args:
            seconds: Time window for analysis
        
        Returns:
            Dict with buy_aggression, sell_aggression, net_aggression
        """
        recent = self._get_recent_trades(seconds)
        
        if not recent:
            return {
                "buy_aggression": 0.0,
                "sell_aggression": 0.0,
                "net_aggression": 0.0
            }
        
        buy_volume = sum(t.quantity * t.price for t in recent if t.side == "buy")
        sell_volume = sum(t.quantity * t.price for t in recent if t.side == "sell")
        total_volume = buy_volume + sell_volume
        
        if total_volume == 0:
            return {
                "buy_aggression": 0.0,
                "sell_aggression": 0.0,
                "net_aggression": 0.0
            }
        
        buy_aggr = buy_volume / total_volume
        sell_aggr = sell_volume / total_volume
        net_aggr = (buy_volume - sell_volume) / total_volume
        
        return {
            "buy_aggression": buy_aggr,
            "sell_aggression": sell_aggr,
            "net_aggression": net_aggr
        }
    
    def get_volume_by_side(self, seconds: int = 60) -> Dict[str, float]:
        """
        Get volume breakdown by side.
        
        Returns:
            Dict with buy_volume, sell_volume in USD
        """
        recent = self._get_recent_trades(seconds)
        
        buy_volume = sum(t.quantity * t.price for t in recent if t.side == "buy")
        sell_volume = sum(t.quantity * t.price for t in recent if t.side == "sell")
        
        return {
            "buy_volume": buy_volume,
            "sell_volume": sell_volume,
            "total_volume": buy_volume + sell_volume
        }
    
    def calculate_vwap(self, seconds: int = 300) -> float:
        """
        Calculate Volume Weighted Average Price.
        
        Args:
            seconds: Time window for VWAP calculation
        
        Returns:
            VWAP price
        """
        # Use cache if recent enough
        current_time = time.time()
        if self.vwap_cache and (current_time - self.vwap_cache_time) < 1.0:
            return self.vwap_cache
        
        recent = self._get_recent_trades(seconds)
        
        if not recent:
            return 0.0
        
        total_value = sum(t.price * t.quantity for t in recent)
        total_volume = sum(t.quantity for t in recent)
        
        if total_volume == 0:
            return 0.0
        
        vwap = total_value / total_volume
        
        # Update cache
        self.vwap_cache = vwap
        self.vwap_cache_time = current_time
        
        return vwap
    
    def detect_sweep(self, threshold_usd: float = 50000, seconds: int = 5) -> Optional[Dict]:
        """
        Detect large aggressive orders (sweeps).
        
        Args:
            threshold_usd: Minimum size to be considered a sweep
            seconds: Time window to analyze
        
        Returns:
            Dict with sweep details or None
        """
        recent = self._get_recent_trades(seconds)
        
        if not recent:
            return None
        
        # Group by side
        buy_volume = sum(t.quantity * t.price for t in recent if t.side == "buy")
        sell_volume = sum(t.quantity * t.price for t in recent if t.side == "sell")
        
        if buy_volume > threshold_usd:
            return {
                "side": "buy",
                "volume": buy_volume,
                "timestamp": recent[-1].timestamp,
                "price": recent[-1].price
            }
        elif sell_volume > threshold_usd:
            return {
                "side": "sell",
                "volume": sell_volume,
                "timestamp": recent[-1].timestamp,
                "price": recent[-1].price
            }
        
        return None
    
    def get_trade_velocity(self, seconds: int = 10) -> float:
        """
        Calculate trade velocity (trades per second).
        
        Args:
            seconds: Time window
        
        Returns:
            Trades per second
        """
        recent = self._get_recent_trades(seconds)
        return len(recent) / seconds if seconds > 0 else 0.0
    
    def get_price_momentum(self, seconds: int = 30) -> float:
        """
        Calculate price momentum (% change).
        
        Args:
            seconds: Time window
        
        Returns:
            Price change in percentage
        """
        recent = self._get_recent_trades(seconds)
        
        if len(recent) < 2:
            return 0.0
        
        start_price = recent[0].price
        end_price = recent[-1].price
        
        return ((end_price - start_price) / start_price) * 100 if start_price > 0 else 0.0
