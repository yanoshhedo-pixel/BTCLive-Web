"""
Configuration settings for BTC Live scalping alerts backend.
"""
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = True
    
    # Database settings
    DATABASE_URL: str = "sqlite+aiosqlite:///./btclive.db"
    
    # Signal thresholds
    MODE: str = "more_action"  # "more_action" or "conservative"
    
    # Reversal signal thresholds
    REVERSAL_MIN_SWEEP_SIZE: float = 50000  # USD
    REVERSAL_MIN_REJECTION_SPEED: float = 0.8  # seconds
    REVERSAL_MIN_SCORE: float = 0.6
    
    # Continuation signal thresholds
    CONTINUATION_MIN_ABSORPTION: float = 100000  # USD
    CONTINUATION_MIN_BREAK_STRENGTH: float = 0.7
    CONTINUATION_MIN_SCORE: float = 0.65
    
    # VWAP snapback thresholds
    VWAP_SNAPBACK_MIN_DEVIATION: float = 0.002  # 0.2%
    VWAP_SNAPBACK_MIN_SCORE: float = 0.55
    
    # Alert settings
    ALERT_COOLDOWN_SECONDS: int = 30
    MAX_ALERTS_PER_MINUTE: int = 10
    
    # Order book settings
    ORDERBOOK_DEPTH: int = 20
    ORDERBOOK_UPDATE_THROTTLE_MS: int = 100
    
    # Exchange WebSocket URLs
    BINANCE_WS_URL: str = "wss://fstream.binance.com/ws/btcusdt@depth20@100ms"
    BINANCE_TRADES_URL: str = "wss://fstream.binance.com/ws/btcusdt@aggTrade"
    
    BYBIT_WS_URL: str = "wss://stream.bybit.com/v5/public/linear"
    
    OKX_WS_URL: str = "wss://ws.okx.com:8443/ws/v5/public"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
