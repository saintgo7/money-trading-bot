"""
Subscription and Payment API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models.user import User
from ..models.subscription import (
    Subscription, SubscriptionPlan, SubscriptionTier,
    Payment, UsageMetrics
)
from ..services.payment_service import StripePaymentService, init_subscription_plans

router = APIRouter(prefix="/api/v1/subscriptions", tags=["subscriptions"])


# Schemas

class SubscriptionPlanResponse(BaseModel):
    tier: str
    name: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    max_bots: int
    max_strategies: int
    max_exchanges: int
    api_rate_limit: int
    features: List[str]

    class Config:
        from_attributes = True


class CreateSubscriptionRequest(BaseModel):
    tier: str = Field(..., description="Subscription tier (basic, pro, enterprise)")
    billing_cycle: str = Field("monthly", description="monthly or yearly")
    payment_method_id: Optional[str] = Field(None, description="Stripe payment method ID")


class SubscriptionResponse(BaseModel):
    id: int
    tier: str
    status: str
    price: float
    currency: str
    billing_cycle: str
    start_date: datetime
    end_date: Optional[datetime]
    trial_end_date: Optional[datetime]
    auto_renew: bool

    class Config:
        from_attributes = True


class PaymentIntentRequest(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field("USD")
    description: Optional[str] = None


class PaymentIntentResponse(BaseModel):
    payment_id: int
    client_secret: str
    amount: float
    currency: str


class PaymentResponse(BaseModel):
    id: int
    amount: float
    currency: str
    status: str
    provider: str
    description: Optional[str]
    receipt_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class UsageResponse(BaseModel):
    usage: dict
    limits: dict
    overage_cost: float
    total_cost: float


# Routes

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def get_subscription_plans(db: Session = Depends(get_db)):
    """Get all available subscription plans"""
    plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.active == True).all()

    if not plans:
        # Initialize plans if not exists
        await init_subscription_plans(db)
        plans = db.query(SubscriptionPlan).filter(SubscriptionPlan.active == True).all()

    return plans


@router.get("/plans/{tier}", response_model=SubscriptionPlanResponse)
async def get_subscription_plan(
    tier: str,
    db: Session = Depends(get_db)
):
    """Get specific subscription plan"""
    try:
        tier_enum = SubscriptionTier(tier.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    plan = db.query(SubscriptionPlan).filter(
        SubscriptionPlan.tier == tier_enum
    ).first()

    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")

    return plan


@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    request: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create new subscription"""
    try:
        tier_enum = SubscriptionTier(request.tier.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    # Check if user already has active subscription
    existing = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status.in_(["active", "trialing"])
    ).first()

    if existing:
        raise HTTPException(status_code=400, detail="User already has active subscription")

    # Create subscription
    payment_service = StripePaymentService(db)
    result = await payment_service.create_subscription(
        user=current_user,
        tier=tier_enum,
        billing_cycle=request.billing_cycle,
        payment_method_id=request.payment_method_id
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create subscription")

    # Get created subscription
    subscription = db.query(Subscription).filter(
        Subscription.id == result['subscription_id']
    ).first()

    return subscription


@router.get("/current", response_model=Optional[SubscriptionResponse])
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's subscription"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    return subscription


@router.post("/cancel")
async def cancel_subscription(
    immediate: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Cancel subscription"""
    payment_service = StripePaymentService(db)
    success = await payment_service.cancel_subscription(current_user, immediate)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to cancel subscription")

    return {"message": "Subscription cancelled successfully"}


@router.post("/payment-intent", response_model=PaymentIntentResponse)
async def create_payment_intent(
    request: PaymentIntentRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create payment intent for one-time payment"""
    payment_service = StripePaymentService(db)
    result = await payment_service.create_payment_intent(
        user=current_user,
        amount=request.amount,
        currency=request.currency,
        description=request.description
    )

    if not result:
        raise HTTPException(status_code=500, detail="Failed to create payment intent")

    return result


@router.get("/payments", response_model=List[PaymentResponse])
async def get_payment_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get payment history"""
    payments = db.query(Payment).filter(
        Payment.user_id == current_user.id
    ).order_by(
        Payment.created_at.desc()
    ).offset(offset).limit(limit).all()

    return payments


@router.get("/usage", response_model=UsageResponse)
async def get_usage_metrics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current usage and billing"""
    payment_service = StripePaymentService(db)
    usage = await payment_service.get_usage_based_billing(current_user)

    return usage


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: Session = Depends(get_db)
):
    """Handle Stripe webhook events"""
    payload = await request.body()
    signature = request.headers.get("stripe-signature")

    if not signature:
        raise HTTPException(status_code=400, detail="Missing signature")

    payment_service = StripePaymentService(db)
    success = await payment_service.handle_webhook(payload, signature)

    if not success:
        raise HTTPException(status_code=400, detail="Webhook processing failed")

    return {"status": "success"}


@router.post("/upgrade")
async def upgrade_subscription(
    new_tier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Upgrade subscription to higher tier"""
    try:
        tier_enum = SubscriptionTier(new_tier.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    # Check if upgrade
    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.BASIC: 1,
        SubscriptionTier.PRO: 2,
        SubscriptionTier.ENTERPRISE: 3
    }

    if tier_order[tier_enum] <= tier_order[subscription.tier]:
        raise HTTPException(status_code=400, detail="Can only upgrade to higher tier")

    # TODO: Implement Stripe subscription update
    # For now, return success

    return {"message": f"Subscription upgraded to {new_tier}"}


@router.post("/downgrade")
async def downgrade_subscription(
    new_tier: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Downgrade subscription to lower tier (at period end)"""
    try:
        tier_enum = SubscriptionTier(new_tier.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid subscription tier")

    # Get current subscription
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id
    ).first()

    if not subscription:
        raise HTTPException(status_code=404, detail="No active subscription found")

    # Check if downgrade
    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.BASIC: 1,
        SubscriptionTier.PRO: 2,
        SubscriptionTier.ENTERPRISE: 3
    }

    if tier_order[tier_enum] >= tier_order[subscription.tier]:
        raise HTTPException(status_code=400, detail="Can only downgrade to lower tier")

    # TODO: Implement Stripe subscription update
    # Downgrade happens at period end

    return {"message": f"Subscription will downgrade to {new_tier} at period end"}
