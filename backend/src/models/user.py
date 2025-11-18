from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base


class User(Base):
    """User model"""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Subscription info
    subscription_tier = Column(String, default="free")  # free, basic, premium
    subscription_expires_at = Column(DateTime, nullable=True)

    # API Keys (encrypted)
    exchange_credentials = Column(JSON, default={})  # Stores encrypted API keys

    # Relationships
    bots = relationship("TradingBot", back_populates="owner", cascade="all, delete-orphan")
    strategies = relationship("Strategy", back_populates="owner", cascade="all, delete-orphan")
    subscription = relationship("Subscription", back_populates="user", uselist=False, cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")
    published_strategies = relationship("StrategyMarketplace", back_populates="author", cascade="all, delete-orphan")
    strategy_purchases = relationship("StrategyPurchase", back_populates="user", cascade="all, delete-orphan")


class ExchangeCredential(Base):
    """Store encrypted exchange API credentials"""

    __tablename__ = "exchange_credentials"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True, nullable=False)
    exchange_name = Column(String, nullable=False)  # binance, upbit, etc.
    api_key_encrypted = Column(String, nullable=False)
    api_secret_encrypted = Column(String, nullable=False)
    is_testnet = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
