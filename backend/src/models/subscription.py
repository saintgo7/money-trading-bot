"""
Subscription and Payment Models
"""

from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, Enum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from ..core.database import Base


class SubscriptionTier(enum.Enum):
    """Subscription tier levels"""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentStatus(enum.Enum):
    """Payment status"""
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class PaymentProvider(enum.Enum):
    """Payment provider"""
    STRIPE = "stripe"
    PAYPAL = "paypal"
    CRYPTO = "crypto"


class Subscription(Base):
    """User subscription model"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Subscription details
    tier = Column(Enum(SubscriptionTier), nullable=False, default=SubscriptionTier.FREE)
    status = Column(String, nullable=False, default="active")  # active, cancelled, expired

    # Billing
    price = Column(Float, default=0.0)
    currency = Column(String, default="USD")
    billing_cycle = Column(String, default="monthly")  # monthly, yearly

    # Dates
    start_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    end_date = Column(DateTime)
    trial_end_date = Column(DateTime)
    cancelled_at = Column(DateTime)

    # External IDs
    stripe_subscription_id = Column(String, unique=True, index=True)
    stripe_customer_id = Column(String, index=True)

    # Auto-renewal
    auto_renew = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="subscription")
    payments = relationship("Payment", back_populates="subscription", cascade="all, delete-orphan")


class Payment(Base):
    """Payment transaction model"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id", ondelete="SET NULL"))

    # Payment details
    amount = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    status = Column(Enum(PaymentStatus), nullable=False, default=PaymentStatus.PENDING)
    provider = Column(Enum(PaymentProvider), nullable=False)

    # External IDs
    transaction_id = Column(String, unique=True, index=True)
    stripe_payment_intent_id = Column(String, unique=True, index=True)
    paypal_transaction_id = Column(String, unique=True, index=True)

    # Details
    description = Column(String)
    receipt_url = Column(String)

    # Refund info
    refunded = Column(Boolean, default=False)
    refund_amount = Column(Float, default=0.0)
    refunded_at = Column(DateTime)

    # Metadata
    metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="payments")
    subscription = relationship("Subscription", back_populates="payments")


class SubscriptionPlan(Base):
    """Available subscription plans"""
    __tablename__ = "subscription_plans"

    id = Column(Integer, primary_key=True, index=True)

    # Plan details
    tier = Column(Enum(SubscriptionTier), unique=True, nullable=False)
    name = Column(String, nullable=False)
    description = Column(String)

    # Pricing
    price_monthly = Column(Float, nullable=False)
    price_yearly = Column(Float, nullable=False)
    currency = Column(String, default="USD")

    # Limits
    max_bots = Column(Integer, nullable=False)
    max_strategies = Column(Integer, nullable=False)
    max_exchanges = Column(Integer, nullable=False)
    api_rate_limit = Column(Integer, nullable=False)  # requests per minute

    # Features (JSON array of feature names)
    features = Column(JSON, nullable=False, default=[])

    # Stripe IDs
    stripe_price_id_monthly = Column(String)
    stripe_price_id_yearly = Column(String)
    stripe_product_id = Column(String)

    # Status
    active = Column(Boolean, default=True)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class StrategyMarketplace(Base):
    """Published strategies in marketplace"""
    __tablename__ = "strategy_marketplace"

    id = Column(Integer, primary_key=True, index=True)

    # Strategy info
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=False)
    author_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Strategy configuration
    strategy_config = Column(JSON, nullable=False)
    category = Column(String, index=True)  # trend_following, mean_reversion, etc.
    tags = Column(JSON, default=[])

    # Pricing
    price = Column(Float, default=0.0)  # 0 = free
    currency = Column(String, default="USD")

    # Performance metrics
    backtested_return = Column(Float)
    sharpe_ratio = Column(Float)
    max_drawdown = Column(Float)
    win_rate = Column(Float)

    # Stats
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    review_count = Column(Integer, default=0)

    # Status
    published = Column(Boolean, default=False)
    featured = Column(Boolean, default=False)
    verified = Column(Boolean, default=False)  # Admin verified

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="published_strategies")
    purchases = relationship("StrategyPurchase", back_populates="strategy", cascade="all, delete-orphan")
    reviews = relationship("StrategyReview", back_populates="strategy", cascade="all, delete-orphan")


class StrategyPurchase(Base):
    """Strategy purchase records"""
    __tablename__ = "strategy_purchases"

    id = Column(Integer, primary_key=True, index=True)

    strategy_id = Column(Integer, ForeignKey("strategy_marketplace.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Purchase details
    price_paid = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    payment_id = Column(Integer, ForeignKey("payments.id"))

    # Status
    active = Column(Boolean, default=True)

    # Metadata
    purchased_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    strategy = relationship("StrategyMarketplace", back_populates="purchases")
    user = relationship("User", back_populates="strategy_purchases")
    payment = relationship("Payment")


class StrategyReview(Base):
    """Strategy reviews and ratings"""
    __tablename__ = "strategy_reviews"

    id = Column(Integer, primary_key=True, index=True)

    strategy_id = Column(Integer, ForeignKey("strategy_marketplace.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Review
    rating = Column(Integer, nullable=False)  # 1-5
    title = Column(String)
    comment = Column(String)

    # Stats
    helpful_count = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    strategy = relationship("StrategyMarketplace", back_populates="reviews")
    user = relationship("User")


class UsageMetrics(Base):
    """Track user usage for billing and limits"""
    __tablename__ = "usage_metrics"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Period
    period_start = Column(DateTime, nullable=False)
    period_end = Column(DateTime, nullable=False)

    # Usage
    api_requests = Column(Integer, default=0)
    active_bots = Column(Integer, default=0)
    total_trades = Column(Integer, default=0)
    strategy_runs = Column(Integer, default=0)

    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User")
