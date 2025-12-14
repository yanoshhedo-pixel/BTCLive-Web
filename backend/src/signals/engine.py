"""
Signal generation engine for Reversal, Continuation, and Snapback setups.
"""
from typing import Optional, Dict
import time
from loguru import logger
from ..config import settings
from ..features import OrderBook, TapeAnalyzer
from .types import Signal, SetupType, SignalStatus


class SignalEngine:
    """Main signal generation engine."""
    
    def __init__(self, exchange: str):
        self.exchange = exchange
        self.orderbook: Optional[OrderBook] = None
        self.tape: Optional[TapeAnalyzer] = None
        
        # Last signal timestamps for cooldown
        self.last_signal_time: Dict[str, float] = {}
    
    def set_orderbook(self, orderbook: OrderBook):
        """Set order book reference."""
        self.orderbook = orderbook
    
    def set_tape(self, tape: TapeAnalyzer):
        """Set tape analyzer reference."""
        self.tape = tape
    
    def check_cooldown(self, setup_type: SetupType) -> bool:
        """
        Check if cooldown period has passed for this setup type.
        
        Returns:
            True if signal can be generated, False if in cooldown
        """
        last_time = self.last_signal_time.get(setup_type.value, 0)
        current_time = time.time()
        
        if current_time - last_time < settings.ALERT_COOLDOWN_SECONDS:
            return False
        
        return True
    
    def update_cooldown(self, setup_type: SetupType):
        """Update last signal time for cooldown."""
        self.last_signal_time[setup_type.value] = time.time()
    
    def detect_reversal(self) -> Optional[Signal]:
        """
        Detect Sweep & Rejection (Reversal) setup.
        
        Logic:
        1. Detect large sweep (liquidity grab)
        2. Check for immediate rejection (price moving opposite direction)
        3. Score based on sweep size, rejection speed, order book support
        """
        if not self.orderbook or not self.tape:
            return None
        
        if not self.check_cooldown(SetupType.REVERSAL):
            return None
        
        # Detect sweep
        sweep = self.tape.detect_sweep(
            threshold_usd=settings.REVERSAL_MIN_SWEEP_SIZE,
            seconds=5
        )
        
        if not sweep:
            return None
        
        # Check for rejection
        aggression = self.tape.get_aggression_score(seconds=3)
        momentum = self.tape.get_price_momentum(seconds=5)
        
        # If sweep was buy, we want to see sell aggression (rejection)
        # If sweep was sell, we want to see buy aggression (rejection)
        is_rejection = False
        rejection_strength = 0.0
        
        if sweep["side"] == "buy" and aggression["sell_aggression"] > 0.6:
            is_rejection = True
            rejection_strength = aggression["sell_aggression"]
        elif sweep["side"] == "sell" and aggression["buy_aggression"] > 0.6:
            is_rejection = True
            rejection_strength = aggression["buy_aggression"]
        
        if not is_rejection:
            return None
        
        # Calculate score
        score = self._calculate_reversal_score(sweep, rejection_strength)
        
        if score < settings.REVERSAL_MIN_SCORE:
            return None
        
        # Generate signal
        current_price = self.orderbook.get_mid_price()
        spread = self.orderbook.get_spread()
        spread_bps = self.orderbook.get_spread_bps()
        
        # Set levels based on sweep direction
        if sweep["side"] == "buy":
            # Sweep up, expecting rejection down
            entry_level = current_price
            invalidation_level = sweep["price"] * 1.002  # 0.2% above sweep
            target_level = current_price * 0.998  # 0.2% below current
        else:
            # Sweep down, expecting rejection up
            entry_level = current_price
            invalidation_level = sweep["price"] * 0.998  # 0.2% below sweep
            target_level = current_price * 1.002  # 0.2% above current
        
        slippage = self.orderbook.estimate_slippage("buy", 10000)  # Estimate for $10k
        
        signal = Signal(
            exchange=self.exchange,
            setup_type=SetupType.REVERSAL,
            timestamp=int(time.time() * 1000),
            score=score,
            price=current_price,
            entry_level=entry_level,
            invalidation_level=invalidation_level,
            target_level=target_level,
            spread=spread,
            spread_bps=spread_bps,
            slippage_estimate=slippage,
            ttl_seconds=60,
            mode=settings.MODE,
            details={
                "sweep_side": sweep["side"],
                "sweep_volume": sweep["volume"],
                "rejection_strength": rejection_strength,
                "momentum": momentum
            }
        )
        
        self.update_cooldown(SetupType.REVERSAL)
        logger.info(f"Generated REVERSAL signal: {signal.to_dict()}")
        
        return signal
    
    def _calculate_reversal_score(self, sweep: dict, rejection_strength: float) -> float:
        """Calculate reversal signal score."""
        # Base score from rejection strength
        score = rejection_strength * 0.5
        
        # Add points for sweep size
        sweep_size_normalized = min(sweep["volume"] / 200000, 1.0)  # Normalize to 200k
        score += sweep_size_normalized * 0.3
        
        # Add points for order book support
        if self.orderbook:
            imbalance = abs(self.orderbook.get_imbalance(levels=5))
            score += imbalance * 0.2
        
        return min(score, 1.0)
    
    def detect_continuation(self) -> Optional[Signal]:
        """
        Detect Absorption & Break (Continuation) setup.
        
        Logic:
        1. Detect heavy absorption (large volume at level without price movement)
        2. Check for breakout (price breaking through absorbed level)
        3. Score based on absorption size, breakout strength, order book support
        """
        if not self.orderbook or not self.tape:
            return None
        
        if not self.check_cooldown(SetupType.CONTINUATION):
            return None
        
        # Detect strong directional flow
        aggression = self.tape.get_aggression_score(seconds=10)
        volume_data = self.tape.get_volume_by_side(seconds=30)
        
        # Need strong one-sided aggression
        if abs(aggression["net_aggression"]) < 0.4:
            return None
        
        # Check if volume meets threshold
        if volume_data["total_volume"] < settings.CONTINUATION_MIN_ABSORPTION:
            return None
        
        # Check for breakout momentum
        momentum = self.tape.get_price_momentum(seconds=10)
        
        if abs(momentum) < 0.1:  # Need at least 0.1% movement
            return None
        
        # Calculate score
        score = self._calculate_continuation_score(aggression, volume_data, momentum)
        
        if score < settings.CONTINUATION_MIN_SCORE:
            return None
        
        # Generate signal
        current_price = self.orderbook.get_mid_price()
        spread = self.orderbook.get_spread()
        spread_bps = self.orderbook.get_spread_bps()
        
        # Set levels based on direction
        if aggression["net_aggression"] > 0:
            # Bullish continuation
            entry_level = current_price
            invalidation_level = current_price * 0.997  # 0.3% stop
            target_level = current_price * 1.003  # 0.3% target
            slippage = self.orderbook.estimate_slippage("buy", 10000)
        else:
            # Bearish continuation
            entry_level = current_price
            invalidation_level = current_price * 1.003  # 0.3% stop
            target_level = current_price * 0.997  # 0.3% target
            slippage = self.orderbook.estimate_slippage("sell", 10000)
        
        signal = Signal(
            exchange=self.exchange,
            setup_type=SetupType.CONTINUATION,
            timestamp=int(time.time() * 1000),
            score=score,
            price=current_price,
            entry_level=entry_level,
            invalidation_level=invalidation_level,
            target_level=target_level,
            spread=spread,
            spread_bps=spread_bps,
            slippage_estimate=slippage,
            ttl_seconds=90,
            mode=settings.MODE,
            details={
                "direction": "bullish" if aggression["net_aggression"] > 0 else "bearish",
                "net_aggression": aggression["net_aggression"],
                "volume": volume_data["total_volume"],
                "momentum": momentum
            }
        )
        
        self.update_cooldown(SetupType.CONTINUATION)
        logger.info(f"Generated CONTINUATION signal: {signal.to_dict()}")
        
        return signal
    
    def _calculate_continuation_score(self, aggression: dict, volume_data: dict, momentum: float) -> float:
        """Calculate continuation signal score."""
        # Base score from aggression
        score = abs(aggression["net_aggression"]) * 0.4
        
        # Add points for volume
        volume_normalized = min(volume_data["total_volume"] / 500000, 1.0)
        score += volume_normalized * 0.3
        
        # Add points for momentum
        momentum_normalized = min(abs(momentum) / 0.5, 1.0)  # Normalize to 0.5%
        score += momentum_normalized * 0.3
        
        return min(score, 1.0)
    
    def detect_snapback(self) -> Optional[Signal]:
        """
        Detect VWAP Snapback (Mean Reversion) setup.
        
        Logic:
        1. Calculate VWAP
        2. Check for significant deviation from VWAP
        3. Look for signs of reversion
        4. Score based on deviation size and reversion signals
        """
        if not self.orderbook or not self.tape:
            return None
        
        if not self.check_cooldown(SetupType.SNAPBACK):
            return None
        
        # Calculate VWAP
        vwap = self.tape.calculate_vwap(seconds=300)
        
        if vwap == 0:
            return None
        
        # Check deviation from VWAP
        current_price = self.orderbook.get_mid_price()
        deviation = (current_price - vwap) / vwap
        
        if abs(deviation) < settings.VWAP_SNAPBACK_MIN_DEVIATION:
            return None
        
        # Check for reversion signals
        aggression = self.tape.get_aggression_score(seconds=5)
        
        # If price above VWAP, look for sell pressure
        # If price below VWAP, look for buy pressure
        is_reverting = False
        reversion_strength = 0.0
        
        if deviation > 0 and aggression["sell_aggression"] > 0.55:
            is_reverting = True
            reversion_strength = aggression["sell_aggression"]
        elif deviation < 0 and aggression["buy_aggression"] > 0.55:
            is_reverting = True
            reversion_strength = aggression["buy_aggression"]
        
        if not is_reverting:
            return None
        
        # Calculate score
        score = self._calculate_snapback_score(deviation, reversion_strength)
        
        if score < settings.VWAP_SNAPBACK_MIN_SCORE:
            return None
        
        # Generate signal
        spread = self.orderbook.get_spread()
        spread_bps = self.orderbook.get_spread_bps()
        
        # Set levels
        if deviation > 0:
            # Price above VWAP, expect move down
            entry_level = current_price
            invalidation_level = current_price * 1.002
            target_level = vwap
            slippage = self.orderbook.estimate_slippage("sell", 10000)
        else:
            # Price below VWAP, expect move up
            entry_level = current_price
            invalidation_level = current_price * 0.998
            target_level = vwap
            slippage = self.orderbook.estimate_slippage("buy", 10000)
        
        signal = Signal(
            exchange=self.exchange,
            setup_type=SetupType.SNAPBACK,
            timestamp=int(time.time() * 1000),
            score=score,
            price=current_price,
            entry_level=entry_level,
            invalidation_level=invalidation_level,
            target_level=target_level,
            spread=spread,
            spread_bps=spread_bps,
            slippage_estimate=slippage,
            ttl_seconds=45,
            mode=settings.MODE,
            details={
                "vwap": vwap,
                "deviation": deviation,
                "deviation_pct": deviation * 100,
                "reversion_strength": reversion_strength
            }
        )
        
        self.update_cooldown(SetupType.SNAPBACK)
        logger.info(f"Generated SNAPBACK signal: {signal.to_dict()}")
        
        return signal
    
    def _calculate_snapback_score(self, deviation: float, reversion_strength: float) -> float:
        """Calculate snapback signal score."""
        # Base score from reversion strength
        score = reversion_strength * 0.5
        
        # Add points for deviation size
        deviation_normalized = min(abs(deviation) / 0.01, 1.0)  # Normalize to 1%
        score += deviation_normalized * 0.5
        
        return min(score, 1.0)
    
    def scan_all_setups(self) -> list[Signal]:
        """
        Scan for all setup types and return any valid signals.
        
        Returns:
            List of detected signals
        """
        signals = []
        
        # Try each setup type
        reversal = self.detect_reversal()
        if reversal:
            signals.append(reversal)
        
        continuation = self.detect_continuation()
        if continuation:
            signals.append(continuation)
        
        snapback = self.detect_snapback()
        if snapback:
            signals.append(snapback)
        
        return signals
