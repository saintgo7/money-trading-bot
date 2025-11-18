"""
Payment Service - Stripe Integration
"""

import stripe
from typing import Dict, Optional, List
from decimal import Decimal
from datetime import datetime, timedelta
import logging
from sqlalchemy.orm import Session

from ..models.subscription import (
    Subscription, Payment, SubscriptionPlan, SubscriptionTier,
    PaymentStatus, PaymentProvider
)
from ..models.user import User
from ..core.config import settings

logger = logging.getLogger(__name__)

# Initialize Stripe
stripe.api_key = settings.STRIPE_SECRET_KEY


class StripePaymentService:
    """Stripe payment integration"""

    def __init__(self, db: Session):
        self.db = db

    async def create_customer(self, user: User) -> Optional[str]:
        """
        Create Stripe customer for user

        Args:
            user: User model

        Returns:
            Stripe customer ID
        """
        try:
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name or user.username,
                metadata={'user_id': user.id}
            )

            logger.info(f"Created Stripe customer: {customer.id} for user {user.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {e}")
            return None

    async def create_subscription(
        self,
        user: User,
        tier: SubscriptionTier,
        billing_cycle: str = "monthly",
        payment_method_id: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create subscription for user

        Args:
            user: User model
            tier: Subscription tier
            billing_cycle: 'monthly' or 'yearly'
            payment_method_id: Stripe payment method ID

        Returns:
            Subscription details
        """
        try:
            # Get plan
            plan = self.db.query(SubscriptionPlan).filter(
                SubscriptionPlan.tier == tier
            ).first()

            if not plan:
                logger.error(f"Plan not found for tier: {tier}")
                return None

            # Get price ID
            price_id = (plan.stripe_price_id_monthly if billing_cycle == "monthly"
                       else plan.stripe_price_id_yearly)

            if not price_id:
                logger.error(f"Stripe price ID not found for {tier}/{billing_cycle}")
                return None

            # Get or create Stripe customer
            subscription_obj = self.db.query(Subscription).filter(
                Subscription.user_id == user.id
            ).first()

            if subscription_obj and subscription_obj.stripe_customer_id:
                customer_id = subscription_obj.stripe_customer_id
            else:
                customer_id = await self.create_customer(user)
                if not customer_id:
                    return None

            # Attach payment method if provided
            if payment_method_id:
                stripe.PaymentMethod.attach(
                    payment_method_id,
                    customer=customer_id
                )
                stripe.Customer.modify(
                    customer_id,
                    invoice_settings={'default_payment_method': payment_method_id}
                )

            # Create subscription
            stripe_subscription = stripe.Subscription.create(
                customer=customer_id,
                items=[{'price': price_id}],
                trial_period_days=14 if tier != SubscriptionTier.FREE else 0,
                metadata={
                    'user_id': user.id,
                    'tier': tier.value
                }
            )

            # Save to database
            if not subscription_obj:
                subscription_obj = Subscription(
                    user_id=user.id,
                    tier=tier,
                    stripe_customer_id=customer_id
                )
                self.db.add(subscription_obj)

            subscription_obj.stripe_subscription_id = stripe_subscription.id
            subscription_obj.tier = tier
            subscription_obj.status = stripe_subscription.status
            subscription_obj.price = plan.price_monthly if billing_cycle == "monthly" else plan.price_yearly
            subscription_obj.billing_cycle = billing_cycle
            subscription_obj.start_date = datetime.fromtimestamp(stripe_subscription.current_period_start)
            subscription_obj.end_date = datetime.fromtimestamp(stripe_subscription.current_period_end)

            if stripe_subscription.trial_end:
                subscription_obj.trial_end_date = datetime.fromtimestamp(stripe_subscription.trial_end)

            self.db.commit()

            logger.info(f"Created subscription for user {user.id}: {tier.value}/{billing_cycle}")

            return {
                'subscription_id': subscription_obj.id,
                'stripe_subscription_id': stripe_subscription.id,
                'tier': tier.value,
                'status': stripe_subscription.status,
                'price': subscription_obj.price,
                'billing_cycle': billing_cycle,
                'trial_end': subscription_obj.trial_end_date
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating subscription: {e}")
            self.db.rollback()
            return None

    async def cancel_subscription(self, user: User, immediate: bool = False) -> bool:
        """
        Cancel subscription

        Args:
            user: User model
            immediate: Cancel immediately or at period end

        Returns:
            Success status
        """
        try:
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user.id
            ).first()

            if not subscription or not subscription.stripe_subscription_id:
                logger.warning(f"No active subscription found for user {user.id}")
                return False

            # Cancel on Stripe
            if immediate:
                stripe.Subscription.delete(subscription.stripe_subscription_id)
                subscription.status = "cancelled"
            else:
                stripe.Subscription.modify(
                    subscription.stripe_subscription_id,
                    cancel_at_period_end=True
                )
                subscription.auto_renew = False

            subscription.cancelled_at = datetime.utcnow()
            self.db.commit()

            logger.info(f"Cancelled subscription for user {user.id}")
            return True

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error cancelling subscription: {e}")
            return False

    async def create_payment_intent(
        self,
        user: User,
        amount: Decimal,
        currency: str = "usd",
        description: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Create payment intent for one-time payment

        Args:
            user: User model
            amount: Amount in currency units
            currency: Currency code
            description: Payment description

        Returns:
            Payment intent details
        """
        try:
            # Get or create customer
            subscription = self.db.query(Subscription).filter(
                Subscription.user_id == user.id
            ).first()

            customer_id = None
            if subscription and subscription.stripe_customer_id:
                customer_id = subscription.stripe_customer_id
            else:
                customer_id = await self.create_customer(user)

            # Create payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency,
                customer=customer_id,
                description=description,
                metadata={'user_id': user.id}
            )

            # Create payment record
            payment = Payment(
                user_id=user.id,
                amount=float(amount),
                currency=currency.upper(),
                status=PaymentStatus.PENDING,
                provider=PaymentProvider.STRIPE,
                stripe_payment_intent_id=intent.id,
                description=description
            )
            self.db.add(payment)
            self.db.commit()

            logger.info(f"Created payment intent for user {user.id}: {amount} {currency}")

            return {
                'payment_id': payment.id,
                'client_secret': intent.client_secret,
                'amount': amount,
                'currency': currency
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment intent: {e}")
            return None

    async def handle_webhook(self, payload: bytes, signature: str) -> bool:
        """
        Handle Stripe webhook events

        Args:
            payload: Webhook payload
            signature: Webhook signature

        Returns:
            Success status
        """
        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )

            event_type = event['type']
            data = event['data']['object']

            logger.info(f"Received Stripe webhook: {event_type}")

            # Handle different event types
            if event_type == 'payment_intent.succeeded':
                await self._handle_payment_success(data)

            elif event_type == 'payment_intent.payment_failed':
                await self._handle_payment_failed(data)

            elif event_type == 'customer.subscription.created':
                await self._handle_subscription_created(data)

            elif event_type == 'customer.subscription.updated':
                await self._handle_subscription_updated(data)

            elif event_type == 'customer.subscription.deleted':
                await self._handle_subscription_deleted(data)

            elif event_type == 'invoice.payment_succeeded':
                await self._handle_invoice_paid(data)

            elif event_type == 'invoice.payment_failed':
                await self._handle_invoice_failed(data)

            return True

        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {e}")
            return False
        except Exception as e:
            logger.error(f"Error handling webhook: {e}")
            return False

    async def _handle_payment_success(self, data: Dict):
        """Handle successful payment"""
        payment_intent_id = data['id']

        payment = self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

        if payment:
            payment.status = PaymentStatus.COMPLETED
            payment.transaction_id = data.get('charges', {}).get('data', [{}])[0].get('id')
            payment.receipt_url = data.get('charges', {}).get('data', [{}])[0].get('receipt_url')
            self.db.commit()

            logger.info(f"Payment succeeded: {payment.id}")

    async def _handle_payment_failed(self, data: Dict):
        """Handle failed payment"""
        payment_intent_id = data['id']

        payment = self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

        if payment:
            payment.status = PaymentStatus.FAILED
            self.db.commit()

            logger.warning(f"Payment failed: {payment.id}")

    async def _handle_subscription_created(self, data: Dict):
        """Handle subscription created"""
        user_id = data['metadata'].get('user_id')
        if not user_id:
            return

        logger.info(f"Subscription created for user {user_id}")

    async def _handle_subscription_updated(self, data: Dict):
        """Handle subscription updated"""
        subscription_id = data['id']

        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if subscription:
            subscription.status = data['status']
            subscription.end_date = datetime.fromtimestamp(data['current_period_end'])
            self.db.commit()

            logger.info(f"Subscription updated: {subscription.id}")

    async def _handle_subscription_deleted(self, data: Dict):
        """Handle subscription deleted"""
        subscription_id = data['id']

        subscription = self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == subscription_id
        ).first()

        if subscription:
            subscription.status = "cancelled"
            subscription.end_date = datetime.utcnow()
            self.db.commit()

            logger.info(f"Subscription deleted: {subscription.id}")

    async def _handle_invoice_paid(self, data: Dict):
        """Handle invoice paid"""
        subscription_id = data.get('subscription')

        if subscription_id:
            subscription = self.db.query(Subscription).filter(
                Subscription.stripe_subscription_id == subscription_id
            ).first()

            if subscription:
                # Create payment record
                payment = Payment(
                    user_id=subscription.user_id,
                    subscription_id=subscription.id,
                    amount=data['amount_paid'] / 100,
                    currency=data['currency'].upper(),
                    status=PaymentStatus.COMPLETED,
                    provider=PaymentProvider.STRIPE,
                    transaction_id=data['charge'],
                    description=f"Subscription payment - {subscription.tier.value}",
                    receipt_url=data.get('hosted_invoice_url')
                )
                self.db.add(payment)
                self.db.commit()

                logger.info(f"Invoice paid for subscription {subscription.id}")

    async def _handle_invoice_failed(self, data: Dict):
        """Handle invoice payment failed"""
        subscription_id = data.get('subscription')

        if subscription_id:
            logger.warning(f"Invoice payment failed for subscription {subscription_id}")

    async def get_usage_based_billing(self, user: User) -> Dict:
        """
        Calculate usage-based billing for user

        Args:
            user: User model

        Returns:
            Usage and cost details
        """
        # Get current subscription
        subscription = self.db.query(Subscription).filter(
            Subscription.user_id == user.id
        ).first()

        if not subscription:
            return {'usage': {}, 'cost': 0.0}

        # Get plan limits
        plan = self.db.query(SubscriptionPlan).filter(
            SubscriptionPlan.tier == subscription.tier
        ).first()

        if not plan:
            return {'usage': {}, 'cost': 0.0}

        # Get current period usage
        from ..models.subscription import UsageMetrics

        usage = self.db.query(UsageMetrics).filter(
            UsageMetrics.user_id == user.id,
            UsageMetrics.period_start >= subscription.start_date
        ).first()

        if not usage:
            return {
                'usage': {
                    'api_requests': 0,
                    'active_bots': 0,
                    'total_trades': 0
                },
                'limits': {
                    'max_bots': plan.max_bots,
                    'api_rate_limit': plan.api_rate_limit
                },
                'cost': 0.0
            }

        # Calculate overages
        overage_cost = 0.0

        # Example: charge $0.01 per 1000 API requests over limit
        api_overage = max(0, usage.api_requests - (plan.api_rate_limit * 43200))  # 30 days
        overage_cost += (api_overage / 1000) * 0.01

        return {
            'usage': {
                'api_requests': usage.api_requests,
                'active_bots': usage.active_bots,
                'total_trades': usage.total_trades
            },
            'limits': {
                'max_bots': plan.max_bots,
                'api_rate_limit': plan.api_rate_limit
            },
            'overage_cost': overage_cost,
            'total_cost': subscription.price + overage_cost
        }


async def init_subscription_plans(db: Session):
    """Initialize default subscription plans"""

    plans = [
        {
            'tier': SubscriptionTier.FREE,
            'name': 'Free',
            'description': 'Get started with basic features',
            'price_monthly': 0.0,
            'price_yearly': 0.0,
            'max_bots': 1,
            'max_strategies': 3,
            'max_exchanges': 1,
            'api_rate_limit': 100,  # per minute
            'features': [
                'Basic trading bots',
                'Standard indicators',
                '1 exchange connection',
                'Community support'
            ]
        },
        {
            'tier': SubscriptionTier.BASIC,
            'name': 'Basic',
            'description': 'For individual traders',
            'price_monthly': 29.0,
            'price_yearly': 290.0,  # 2 months free
            'max_bots': 5,
            'max_strategies': 10,
            'max_exchanges': 3,
            'api_rate_limit': 500,
            'features': [
                'Everything in Free',
                'Advanced AI models',
                'Up to 5 bots',
                '3 exchange connections',
                'Email support',
                'Strategy marketplace access'
            ]
        },
        {
            'tier': SubscriptionTier.PRO,
            'name': 'Pro',
            'description': 'For professional traders',
            'price_monthly': 99.0,
            'price_yearly': 990.0,
            'max_bots': 20,
            'max_strategies': 50,
            'max_exchanges': 10,
            'api_rate_limit': 2000,
            'features': [
                'Everything in Basic',
                'Reinforcement learning',
                'Ensemble models',
                'Up to 20 bots',
                '10 exchange connections',
                'Priority support',
                'Custom strategies',
                'Advanced analytics',
                'API access'
            ]
        },
        {
            'tier': SubscriptionTier.ENTERPRISE,
            'name': 'Enterprise',
            'description': 'For institutions and teams',
            'price_monthly': 499.0,
            'price_yearly': 4990.0,
            'max_bots': 100,
            'max_strategies': 200,
            'max_exchanges': 50,
            'api_rate_limit': 10000,
            'features': [
                'Everything in Pro',
                'Unlimited bots',
                'All exchanges',
                'Dedicated support',
                'Custom development',
                'White-label option',
                'Team collaboration',
                'Advanced security',
                'SLA guarantee'
            ]
        }
    ]

    for plan_data in plans:
        existing = db.query(SubscriptionPlan).filter(
            SubscriptionPlan.tier == plan_data['tier']
        ).first()

        if not existing:
            plan = SubscriptionPlan(**plan_data)
            db.add(plan)

    db.commit()
    logger.info("Subscription plans initialized")
