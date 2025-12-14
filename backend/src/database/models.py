"""
Database models for BTC Live alerts.
"""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Alert(Base):
    """Alert log table for storing all generated alerts."""
    
    __tablename__ = "alerts"
    
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    exchange = Column(String(50), nullable=False)  # Binance, OKX, Bybit
    setup_type = Column(String(50), nullable=False)  # Reversal, Continuation, Snapback
    score = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    entry_level = Column(Float)
    invalidation_level = Column(Float)
    target_level = Column(Float)
    spread = Column(Float)
    slippage_estimate = Column(Float)
    ttl_seconds = Column(Integer)  # Time-to-live
    mode = Column(String(20))  # more_action, conservative
    details = Column(Text)  # JSON with additional context
    outcome = Column(String(50))  # hit_target, invalidated, expired, null


class Settings(Base):
    """User-configurable settings table."""
    
    __tablename__ = "settings"
    
    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(String(500), nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
