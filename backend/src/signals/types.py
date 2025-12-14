"""
Signal types and data structures.
"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class SetupType(str, Enum):
    """Types of trading setups."""
    REVERSAL = "Reversal"  # Sweep & Rejection
    CONTINUATION = "Continuation"  # Absorption & Break
    SNAPBACK = "Snapback"  # VWAP Snapback


class SignalStatus(str, Enum):
    """Signal status tracking."""
    ACTIVE = "active"
    HIT_TARGET = "hit_target"
    INVALIDATED = "invalidated"
    EXPIRED = "expired"


@dataclass
class Signal:
    """Trading signal data structure."""
    
    # Basic info
    exchange: str
    setup_type: SetupType
    timestamp: int
    
    # Scoring
    score: float  # 0.0 to 1.0
    
    # Price levels
    price: float
    entry_level: Optional[float] = None
    invalidation_level: Optional[float] = None
    target_level: Optional[float] = None
    
    # Market conditions
    spread: float = 0.0
    spread_bps: float = 0.0
    slippage_estimate: float = 0.0
    
    # Signal characteristics
    ttl_seconds: int = 120  # Time-to-live
    mode: str = "more_action"
    
    # Additional context
    details: Optional[dict] = None
    
    # Status tracking
    status: SignalStatus = SignalStatus.ACTIVE
    
    def to_dict(self) -> dict:
        """Convert signal to dictionary for API response."""
        return {
            "exchange": self.exchange,
            "setup_type": self.setup_type.value,
            "timestamp": self.timestamp,
            "score": round(self.score, 3),
            "price": self.price,
            "entry_level": self.entry_level,
            "invalidation_level": self.invalidation_level,
            "target_level": self.target_level,
            "spread": round(self.spread, 2),
            "spread_bps": round(self.spread_bps, 2),
            "slippage_estimate": round(self.slippage_estimate, 2),
            "ttl_seconds": self.ttl_seconds,
            "mode": self.mode,
            "details": self.details,
            "status": self.status.value
        }
