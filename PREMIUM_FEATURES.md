# Premium Features Guide

Complete guide to subscription management, payments, and strategy marketplace

---

## Table of Contents

1. [Subscription System](#subscription-system)
2. [Payment Integration](#payment-integration)
3. [Strategy Marketplace](#strategy-marketplace)
4. [Usage Tracking](#usage-tracking)
5. [API Documentation](#api-documentation)

---

## Subscription System

### Subscription Tiers

| Tier | Price (Monthly) | Price (Yearly) | Max Bots | Max Strategies | Max Exchanges | API Rate Limit |
|------|-----------------|----------------|----------|----------------|---------------|----------------|
| **Free** | $0 | $0 | 1 | 3 | 1 | 100/min |
| **Basic** | $29 | $290 (save $58) | 5 | 10 | 3 | 500/min |
| **Pro** | $99 | $990 (save $198) | 20 | 50 | 10 | 2,000/min |
| **Enterprise** | $499 | $4,990 (save $998) | 100 | 200 | 50 | 10,000/min |

### Features by Tier

#### Free Tier
- ✅ Basic trading bots
- ✅ Standard indicators
- ✅ 1 exchange connection
- ✅ Community support
- ❌ AI models
- ❌ Strategy marketplace
- ❌ Advanced analytics

#### Basic Tier ($29/month)
- ✅ Everything in Free
- ✅ Advanced AI models (LSTM, Transformer)
- ✅ Up to 5 bots
- ✅ 3 exchange connections
- ✅ Email support
- ✅ Strategy marketplace access
- ✅ Basic analytics
- ❌ Reinforcement learning
- ❌ Ensemble models
- ❌ API access

#### Pro Tier ($99/month)
- ✅ Everything in Basic
- ✅ Reinforcement learning (DQN, PPO)
- ✅ Ensemble models
- ✅ Up to 20 bots
- ✅ 10 exchange connections
- ✅ Priority support
- ✅ Custom strategies
- ✅ Advanced analytics
- ✅ Full API access
- ✅ Backtest reports
- ❌ White-label
- ❌ Team collaboration

#### Enterprise Tier ($499/month)
- ✅ Everything in Pro
- ✅ Unlimited bots
- ✅ All exchanges
- ✅ Dedicated support
- ✅ Custom development
- ✅ White-label option
- ✅ Team collaboration
- ✅ Advanced security
- ✅ SLA guarantee (99.9% uptime)
- ✅ Custom integrations

### Subscription Management

#### Create Subscription

```bash
POST /api/v1/subscriptions/subscribe
Content-Type: application/json
Authorization: Bearer <token>

{
  "tier": "pro",
  "billing_cycle": "monthly",
  "payment_method_id": "pm_1234567890"
}
```

**Response:**
```json
{
  "id": 1,
  "tier": "pro",
  "status": "active",
  "price": 99.0,
  "currency": "USD",
  "billing_cycle": "monthly",
  "start_date": "2025-01-18T00:00:00Z",
  "end_date": "2025-02-18T00:00:00Z",
  "trial_end_date": "2025-02-01T00:00:00Z",
  "auto_renew": true
}
```

#### View Current Subscription

```bash
GET /api/v1/subscriptions/current
Authorization: Bearer <token>
```

#### Cancel Subscription

```bash
POST /api/v1/subscriptions/cancel?immediate=false
Authorization: Bearer <token>
```

- `immediate=false`: Cancel at period end (default)
- `immediate=true`: Cancel immediately

#### Upgrade/Downgrade

```bash
POST /api/v1/subscriptions/upgrade
Content-Type: application/json
Authorization: Bearer <token>

{
  "new_tier": "enterprise"
}
```

---

## Payment Integration

### Supported Payment Methods

1. **Stripe** (Primary)
   - Credit/Debit Cards
   - Apple Pay
   - Google Pay
   - SEPA Direct Debit (Europe)
   - iDEAL (Netherlands)

2. **PayPal** (Coming Soon)
   - PayPal Balance
   - Bank Account
   - Credit/Debit Cards

3. **Cryptocurrency** (Future)
   - Bitcoin (BTC)
   - Ethereum (ETH)
   - USDT/USDC

### Stripe Integration

#### Setup

1. **Get Stripe Keys:**
```bash
# .env file
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
```

2. **Initialize Stripe in Frontend:**
```typescript
import { loadStripe } from '@stripe/stripe-js';

const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY);
```

3. **Create Payment Intent:**
```bash
POST /api/v1/subscriptions/payment-intent
Authorization: Bearer <token>

{
  "amount": 99.00,
  "currency": "usd",
  "description": "Pro Subscription"
}
```

#### Webhook Events

Configure webhook endpoint in Stripe Dashboard:
```
https://yourdomain.com/api/v1/subscriptions/webhook
```

**Handled Events:**
- `payment_intent.succeeded`
- `payment_intent.payment_failed`
- `customer.subscription.created`
- `customer.subscription.updated`
- `customer.subscription.deleted`
- `invoice.payment_succeeded`
- `invoice.payment_failed`

### Payment History

```bash
GET /api/v1/subscriptions/payments?limit=20&offset=0
Authorization: Bearer <token>
```

**Response:**
```json
[
  {
    "id": 1,
    "amount": 99.0,
    "currency": "USD",
    "status": "completed",
    "provider": "stripe",
    "description": "Pro Subscription - January 2025",
    "receipt_url": "https://pay.stripe.com/receipts/...",
    "created_at": "2025-01-18T00:00:00Z"
  }
]
```

---

## Strategy Marketplace

Buy, sell, and discover trading strategies created by the community.

### Publishing Strategies

#### Create Strategy Listing

```bash
POST /api/v1/marketplace/publish
Authorization: Bearer <token>

{
  "name": "Advanced BTC Momentum Strategy",
  "description": "High-frequency momentum trading strategy optimized for Bitcoin...",
  "strategy_config": {
    "type": "momentum",
    "parameters": {
      "lookback_period": 20,
      "rsi_threshold": 70,
      "take_profit": 0.02,
      "stop_loss": 0.01
    }
  },
  "category": "momentum",
  "price": 49.99,
  "tags": ["bitcoin", "momentum", "high-frequency"],
  "performance_metrics": {
    "total_return": 0.45,
    "sharpe_ratio": 2.3,
    "max_drawdown": -0.12,
    "win_rate": 0.62
  }
}
```

**Response:**
```json
{
  "id": 1,
  "name": "Advanced BTC Momentum Strategy",
  "author_id": 123,
  "price": 49.99,
  "downloads": 0,
  "rating": 0.0,
  "published": false,
  "verified": false,
  "created_at": "2025-01-18T00:00:00Z"
}
```

**Note:** Strategies require admin approval before becoming visible in marketplace.

### Discovering Strategies

#### Search Strategies

```bash
GET /api/v1/marketplace/search?query=bitcoin&category=momentum&sort_by=rating&limit=20
```

**Filters:**
- `query`: Search in name/description
- `category`: Filter by category
- `tags`: Filter by tags (array)
- `min_rating`: Minimum rating (0-5)
- `max_price`: Maximum price
- `sort_by`: downloads, rating, price, created_at
- `limit`: Results per page (1-100)
- `offset`: Pagination offset

#### Get Featured Strategies

```bash
GET /api/v1/marketplace/featured?limit=10
```

#### Get Trending Strategies

```bash
GET /api/v1/marketplace/trending?days=7&limit=10
```

### Purchasing Strategies

```bash
POST /api/v1/marketplace/strategies/{strategy_id}/purchase
Authorization: Bearer <token>

{
  "payment_method_id": "pm_1234567890"  // Optional for free strategies
}
```

### Reviews and Ratings

#### Add Review

```bash
POST /api/v1/marketplace/strategies/{strategy_id}/review
Authorization: Bearer <token>

{
  "rating": 5,
  "title": "Excellent strategy!",
  "comment": "Made 45% return in 3 months. Highly recommend!"
}
```

#### View Reviews

```bash
GET /api/v1/marketplace/strategies/{strategy_id}/reviews?limit=20&offset=0
```

### Strategy Categories

- `trend_following` - Follow market trends
- `mean_reversion` - Buy low, sell high
- `momentum` - Ride the momentum
- `arbitrage` - Cross-exchange arbitrage
- `market_making` - Provide liquidity
- `scalping` - Quick small profits
- `swing_trading` - Hold positions days-weeks
- `ai_ml` - AI/ML based strategies
- `technical_analysis` - Technical indicators
- `fundamental_analysis` - Based on fundamentals
- `other` - Other strategies

### Marketplace Statistics

```bash
GET /api/v1/marketplace/stats
```

**Response:**
```json
{
  "total_strategies": 1247,
  "total_downloads": 8934,
  "average_rating": 4.2,
  "total_revenue": 125670.50,
  "categories": {
    "momentum": 234,
    "mean_reversion": 189,
    "ai_ml": 156,
    "trend_following": 143
  }
}
```

### Earnings as Strategy Author

```bash
GET /api/v1/marketplace/earnings
Authorization: Bearer <token>
```

**Response:**
```json
{
  "total_earnings": 2450.00,
  "total_downloads": 87,
  "strategy_count": 5
}
```

**Revenue Share:**
- Platform: 20%
- Author: 80%

Example: If strategy sells for $49.99:
- Author receives: $39.99
- Platform: $10.00

---

## Usage Tracking

Monitor your usage to stay within tier limits.

### View Current Usage

```bash
GET /api/v1/subscriptions/usage
Authorization: Bearer <token>
```

**Response:**
```json
{
  "usage": {
    "api_requests": 2847,
    "active_bots": 8,
    "total_trades": 134
  },
  "limits": {
    "max_bots": 20,
    "api_rate_limit": 2000
  },
  "overage_cost": 0.00,
  "total_cost": 99.00
}
```

### Usage-Based Billing

If you exceed tier limits, overage charges may apply:

| Resource | Overage Rate |
|----------|--------------|
| API Requests | $0.01 per 1,000 requests over limit |
| Additional Bots | $5/month per bot over limit |
| Storage | $0.10/GB/month over 10GB |

---

## API Documentation

### Authentication

All API calls require JWT authentication:

```bash
Authorization: Bearer <your_jwt_token>
```

### Rate Limits

Rate limits depend on subscription tier:

| Tier | Rate Limit |
|------|------------|
| Free | 100 requests/minute |
| Basic | 500 requests/minute |
| Pro | 2,000 requests/minute |
| Enterprise | 10,000 requests/minute |

**Rate Limit Headers:**
```
X-RateLimit-Limit: 2000
X-RateLimit-Remaining: 1847
X-RateLimit-Reset: 1642512000
```

### Error Responses

#### Insufficient Permissions
```json
{
  "detail": "Upgrade to Pro tier to access this feature",
  "required_tier": "pro",
  "current_tier": "basic",
  "upgrade_url": "/subscriptions/plans/pro"
}
```

#### Rate Limit Exceeded
```json
{
  "detail": "Rate limit exceeded",
  "limit": 500,
  "retry_after": 42
}
```

#### Bot Limit Reached
```json
{
  "detail": "Bot limit reached",
  "current": 5,
  "limit": 5,
  "tier": "basic",
  "upgrade_message": "Upgrade to Pro for up to 20 bots"
}
```

---

## Integration Examples

### Frontend - Subscribe to Pro Tier

```typescript
import { useState } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import { CardElement, useStripe, useElements } from '@stripe/react-stripe-js';

export function SubscriptionForm() {
  const stripe = useStripe();
  const elements = useElements();
  const [loading, setLoading] = useState(false);

  const handleSubscribe = async (tier: string, billingCycle: string) => {
    setLoading(true);

    try {
      // Create payment method
      const { paymentMethod } = await stripe.createPaymentMethod({
        type: 'card',
        card: elements.getElement(CardElement),
      });

      // Subscribe
      const response = await fetch('/api/v1/subscriptions/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          tier,
          billing_cycle: billingCycle,
          payment_method_id: paymentMethod.id
        })
      });

      const subscription = await response.json();
      console.log('Subscribed:', subscription);

      // Redirect to success page
      window.location.href = '/dashboard?subscribed=true';

    } catch (error) {
      console.error('Subscription error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <form onSubmit={(e) => {
      e.preventDefault();
      handleSubscribe('pro', 'monthly');
    }}>
      <CardElement />
      <button disabled={loading}>
        {loading ? 'Processing...' : 'Subscribe to Pro'}
      </button>
    </form>
  );
}
```

### Backend - Check User Tier

```python
from fastapi import Depends, HTTPException
from ..models.subscription import Subscription, SubscriptionTier

async def require_tier(
    required_tier: SubscriptionTier,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Dependency to enforce tier requirements"""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    ).first()

    if not subscription:
        raise HTTPException(
            status_code=403,
            detail=f"Upgrade to {required_tier.value} tier required"
        )

    tier_order = {
        SubscriptionTier.FREE: 0,
        SubscriptionTier.BASIC: 1,
        SubscriptionTier.PRO: 2,
        SubscriptionTier.ENTERPRISE: 3
    }

    if tier_order[subscription.tier] < tier_order[required_tier]:
        raise HTTPException(
            status_code=403,
            detail=f"Upgrade to {required_tier.value} tier required"
        )

# Usage
@router.post("/advanced-feature")
async def advanced_feature(
    _: None = Depends(lambda: require_tier(SubscriptionTier.PRO))
):
    # Only Pro and Enterprise users can access
    return {"message": "Advanced feature"}
```

---

## Stripe Testing

### Test Credit Cards

| Card Number | Brand | Result |
|-------------|-------|--------|
| 4242 4242 4242 4242 | Visa | Success |
| 4000 0025 0000 3155 | Visa | Requires authentication |
| 4000 0000 0000 9995 | Visa | Declined |
| 5555 5555 5555 4444 | Mastercard | Success |

**Expiration:** Any future date
**CVC:** Any 3 digits
**ZIP:** Any 5 digits

### Webhook Testing

```bash
# Install Stripe CLI
stripe login

# Forward webhooks to local
stripe listen --forward-to localhost:8000/api/v1/subscriptions/webhook

# Trigger test events
stripe trigger payment_intent.succeeded
stripe trigger customer.subscription.created
```

---

## Support

### Getting Help

- **Free Tier:** Community forum
- **Basic Tier:** Email support (48h response)
- **Pro Tier:** Priority email (24h response)
- **Enterprise Tier:** Dedicated support (4h response) + Slack channel

### Contact

- Email: support@trading-bot.com
- Discord: https://discord.gg/trading-bot
- Documentation: https://docs.trading-bot.com

---

## Roadmap

### Q1 2025
- ✅ Stripe integration
- ✅ Basic subscription tiers
- ✅ Strategy marketplace
- ⏳ PayPal integration

### Q2 2025
- ⏳ Cryptocurrency payments
- ⏳ Team collaboration features
- ⏳ Advanced analytics dashboard
- ⏳ Mobile app (React Native)

### Q3 2025
- ⏳ White-label solution
- ⏳ API marketplace
- ⏳ Strategy backtesting service
- ⏳ Social trading features

---

**Last Updated:** January 18, 2025
