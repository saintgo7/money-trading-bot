"""
Strategy Marketplace Service
Buy, sell, and discover trading strategies
"""

from typing import Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import desc, and_
from decimal import Decimal
import logging
from datetime import datetime

from ..models.subscription import (
    StrategyMarketplace, StrategyPurchase, StrategyReview,
    Payment, PaymentStatus, PaymentProvider
)
from ..models.user import User

logger = logging.getLogger(__name__)


class MarketplaceService:
    """Strategy marketplace management"""

    def __init__(self, db: Session):
        self.db = db

    async def publish_strategy(
        self,
        user: User,
        name: str,
        description: str,
        strategy_config: Dict,
        category: str,
        price: float = 0.0,
        tags: Optional[List[str]] = None,
        performance_metrics: Optional[Dict] = None
    ) -> Optional[StrategyMarketplace]:
        """
        Publish strategy to marketplace

        Args:
            user: Strategy author
            name: Strategy name
            description: Strategy description
            strategy_config: Strategy configuration JSON
            category: Strategy category
            price: Price (0 for free)
            tags: Strategy tags
            performance_metrics: Backtest performance metrics

        Returns:
            Published strategy
        """
        try:
            # Validate strategy config
            if not self._validate_strategy_config(strategy_config):
                logger.error("Invalid strategy configuration")
                return None

            # Create marketplace entry
            strategy = StrategyMarketplace(
                name=name,
                description=description,
                author_id=user.id,
                strategy_config=strategy_config,
                category=category,
                price=price,
                tags=tags or [],
                published=False  # Requires admin approval
            )

            # Add performance metrics if provided
            if performance_metrics:
                strategy.backtested_return = performance_metrics.get('total_return')
                strategy.sharpe_ratio = performance_metrics.get('sharpe_ratio')
                strategy.max_drawdown = performance_metrics.get('max_drawdown')
                strategy.win_rate = performance_metrics.get('win_rate')

            self.db.add(strategy)
            self.db.commit()
            self.db.refresh(strategy)

            logger.info(f"Strategy published: {strategy.id} by user {user.id}")

            return strategy

        except Exception as e:
            logger.error(f"Error publishing strategy: {e}")
            self.db.rollback()
            return None

    def _validate_strategy_config(self, config: Dict) -> bool:
        """Validate strategy configuration"""
        required_fields = ['type', 'parameters']

        for field in required_fields:
            if field not in config:
                return False

        return True

    async def search_strategies(
        self,
        query: Optional[str] = None,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        min_rating: Optional[float] = None,
        max_price: Optional[float] = None,
        sort_by: str = "downloads",  # downloads, rating, price, created_at
        limit: int = 20,
        offset: int = 0
    ) -> List[StrategyMarketplace]:
        """
        Search marketplace strategies

        Args:
            query: Search query
            category: Filter by category
            tags: Filter by tags
            min_rating: Minimum rating
            max_price: Maximum price
            sort_by: Sort field
            limit: Results limit
            offset: Results offset

        Returns:
            List of strategies
        """
        try:
            # Base query - only published strategies
            query_obj = self.db.query(StrategyMarketplace).filter(
                StrategyMarketplace.published == True
            )

            # Apply filters
            if query:
                query_obj = query_obj.filter(
                    StrategyMarketplace.name.ilike(f"%{query}%") |
                    StrategyMarketplace.description.ilike(f"%{query}%")
                )

            if category:
                query_obj = query_obj.filter(StrategyMarketplace.category == category)

            if tags:
                # Filter by tags (PostgreSQL JSON operations)
                for tag in tags:
                    query_obj = query_obj.filter(
                        StrategyMarketplace.tags.contains([tag])
                    )

            if min_rating:
                query_obj = query_obj.filter(StrategyMarketplace.rating >= min_rating)

            if max_price is not None:
                query_obj = query_obj.filter(StrategyMarketplace.price <= max_price)

            # Sort
            if sort_by == "downloads":
                query_obj = query_obj.order_by(desc(StrategyMarketplace.downloads))
            elif sort_by == "rating":
                query_obj = query_obj.order_by(desc(StrategyMarketplace.rating))
            elif sort_by == "price":
                query_obj = query_obj.order_by(StrategyMarketplace.price)
            elif sort_by == "created_at":
                query_obj = query_obj.order_by(desc(StrategyMarketplace.created_at))

            # Paginate
            strategies = query_obj.offset(offset).limit(limit).all()

            return strategies

        except Exception as e:
            logger.error(f"Error searching strategies: {e}")
            return []

    async def get_strategy(self, strategy_id: int) -> Optional[StrategyMarketplace]:
        """Get strategy by ID"""
        return self.db.query(StrategyMarketplace).filter(
            StrategyMarketplace.id == strategy_id,
            StrategyMarketplace.published == True
        ).first()

    async def purchase_strategy(
        self,
        user: User,
        strategy_id: int,
        payment_method_id: Optional[str] = None
    ) -> Optional[StrategyPurchase]:
        """
        Purchase strategy from marketplace

        Args:
            user: Buyer
            strategy_id: Strategy to purchase
            payment_method_id: Payment method (for paid strategies)

        Returns:
            Purchase record
        """
        try:
            # Get strategy
            strategy = await self.get_strategy(strategy_id)

            if not strategy:
                logger.error(f"Strategy not found: {strategy_id}")
                return None

            # Check if already purchased
            existing = self.db.query(StrategyPurchase).filter(
                StrategyPurchase.user_id == user.id,
                StrategyPurchase.strategy_id == strategy_id,
                StrategyPurchase.active == True
            ).first()

            if existing:
                logger.warning(f"User {user.id} already owns strategy {strategy_id}")
                return existing

            # Handle payment for paid strategies
            payment = None
            if strategy.price > 0:
                # Create payment
                from .payment_service import StripePaymentService

                payment_service = StripePaymentService(self.db)
                payment_intent = await payment_service.create_payment_intent(
                    user=user,
                    amount=Decimal(str(strategy.price)),
                    currency="USD",
                    description=f"Purchase: {strategy.name}"
                )

                if not payment_intent:
                    logger.error("Failed to create payment intent")
                    return None

                # Get payment record
                payment = self.db.query(Payment).filter(
                    Payment.id == payment_intent['payment_id']
                ).first()

                # Note: Payment will be completed via webhook
                # For demo, we'll mark as completed
                payment.status = PaymentStatus.COMPLETED

            # Create purchase record
            purchase = StrategyPurchase(
                strategy_id=strategy_id,
                user_id=user.id,
                price_paid=strategy.price,
                payment_id=payment.id if payment else None
            )

            self.db.add(purchase)

            # Update strategy stats
            strategy.downloads += 1

            self.db.commit()
            self.db.refresh(purchase)

            logger.info(f"Strategy purchased: {strategy_id} by user {user.id}")

            return purchase

        except Exception as e:
            logger.error(f"Error purchasing strategy: {e}")
            self.db.rollback()
            return None

    async def get_user_purchases(self, user: User) -> List[StrategyPurchase]:
        """Get user's purchased strategies"""
        return self.db.query(StrategyPurchase).filter(
            StrategyPurchase.user_id == user.id,
            StrategyPurchase.active == True
        ).all()

    async def get_user_published_strategies(self, user: User) -> List[StrategyMarketplace]:
        """Get strategies published by user"""
        return self.db.query(StrategyMarketplace).filter(
            StrategyMarketplace.author_id == user.id
        ).all()

    async def add_review(
        self,
        user: User,
        strategy_id: int,
        rating: int,
        title: Optional[str] = None,
        comment: Optional[str] = None
    ) -> Optional[StrategyReview]:
        """
        Add review for strategy

        Args:
            user: Reviewer
            strategy_id: Strategy ID
            rating: Rating (1-5)
            title: Review title
            comment: Review comment

        Returns:
            Review record
        """
        try:
            # Validate rating
            if rating < 1 or rating > 5:
                logger.error("Invalid rating: must be 1-5")
                return None

            # Check if user purchased strategy
            purchase = self.db.query(StrategyPurchase).filter(
                StrategyPurchase.user_id == user.id,
                StrategyPurchase.strategy_id == strategy_id,
                StrategyPurchase.active == True
            ).first()

            if not purchase:
                logger.error("User has not purchased this strategy")
                return None

            # Check if already reviewed
            existing = self.db.query(StrategyReview).filter(
                StrategyReview.user_id == user.id,
                StrategyReview.strategy_id == strategy_id
            ).first()

            if existing:
                # Update existing review
                existing.rating = rating
                existing.title = title
                existing.comment = comment
                existing.updated_at = datetime.utcnow()
                review = existing
            else:
                # Create new review
                review = StrategyReview(
                    strategy_id=strategy_id,
                    user_id=user.id,
                    rating=rating,
                    title=title,
                    comment=comment
                )
                self.db.add(review)

            self.db.commit()

            # Update strategy rating
            await self._update_strategy_rating(strategy_id)

            logger.info(f"Review added for strategy {strategy_id} by user {user.id}")

            return review

        except Exception as e:
            logger.error(f"Error adding review: {e}")
            self.db.rollback()
            return None

    async def _update_strategy_rating(self, strategy_id: int):
        """Recalculate strategy rating"""
        from sqlalchemy import func

        result = self.db.query(
            func.avg(StrategyReview.rating),
            func.count(StrategyReview.id)
        ).filter(
            StrategyReview.strategy_id == strategy_id
        ).first()

        avg_rating, count = result

        strategy = self.db.query(StrategyMarketplace).filter(
            StrategyMarketplace.id == strategy_id
        ).first()

        if strategy:
            strategy.rating = float(avg_rating) if avg_rating else 0.0
            strategy.review_count = count or 0
            self.db.commit()

    async def get_strategy_reviews(
        self,
        strategy_id: int,
        limit: int = 20,
        offset: int = 0
    ) -> List[StrategyReview]:
        """Get reviews for strategy"""
        return self.db.query(StrategyReview).filter(
            StrategyReview.strategy_id == strategy_id
        ).order_by(
            desc(StrategyReview.created_at)
        ).offset(offset).limit(limit).all()

    async def get_featured_strategies(self, limit: int = 10) -> List[StrategyMarketplace]:
        """Get featured strategies"""
        return self.db.query(StrategyMarketplace).filter(
            StrategyMarketplace.published == True,
            StrategyMarketplace.featured == True
        ).order_by(
            desc(StrategyMarketplace.rating)
        ).limit(limit).all()

    async def get_trending_strategies(
        self,
        days: int = 7,
        limit: int = 10
    ) -> List[StrategyMarketplace]:
        """Get trending strategies (most downloads in recent days)"""
        from datetime import timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        # Get strategies with recent purchases
        recent_purchases = self.db.query(
            StrategyPurchase.strategy_id,
            func.count(StrategyPurchase.id).label('recent_downloads')
        ).filter(
            StrategyPurchase.purchased_at >= cutoff_date
        ).group_by(
            StrategyPurchase.strategy_id
        ).subquery()

        strategies = self.db.query(StrategyMarketplace).join(
            recent_purchases,
            StrategyMarketplace.id == recent_purchases.c.strategy_id
        ).filter(
            StrategyMarketplace.published == True
        ).order_by(
            desc(recent_purchases.c.recent_downloads)
        ).limit(limit).all()

        return strategies

    async def get_marketplace_stats(self) -> Dict:
        """Get marketplace statistics"""
        from sqlalchemy import func

        total_strategies = self.db.query(func.count(StrategyMarketplace.id)).filter(
            StrategyMarketplace.published == True
        ).scalar()

        total_downloads = self.db.query(func.sum(StrategyMarketplace.downloads)).filter(
            StrategyMarketplace.published == True
        ).scalar()

        avg_rating = self.db.query(func.avg(StrategyMarketplace.rating)).filter(
            StrategyMarketplace.published == True,
            StrategyMarketplace.rating > 0
        ).scalar()

        total_revenue = self.db.query(func.sum(StrategyPurchase.price_paid)).scalar()

        categories = self.db.query(
            StrategyMarketplace.category,
            func.count(StrategyMarketplace.id).label('count')
        ).filter(
            StrategyMarketplace.published == True
        ).group_by(
            StrategyMarketplace.category
        ).all()

        return {
            'total_strategies': total_strategies or 0,
            'total_downloads': int(total_downloads or 0),
            'average_rating': float(avg_rating) if avg_rating else 0.0,
            'total_revenue': float(total_revenue) if total_revenue else 0.0,
            'categories': {cat: count for cat, count in categories}
        }

    async def approve_strategy(self, strategy_id: int, admin: User) -> bool:
        """
        Approve strategy for publication (admin only)

        Args:
            strategy_id: Strategy ID
            admin: Admin user

        Returns:
            Success status
        """
        if not admin.is_superuser:
            logger.error(f"User {admin.id} is not authorized to approve strategies")
            return False

        strategy = self.db.query(StrategyMarketplace).filter(
            StrategyMarketplace.id == strategy_id
        ).first()

        if not strategy:
            return False

        strategy.published = True
        strategy.verified = True
        self.db.commit()

        logger.info(f"Strategy {strategy_id} approved by admin {admin.id}")

        return True

    async def reject_strategy(
        self,
        strategy_id: int,
        admin: User,
        reason: Optional[str] = None
    ) -> bool:
        """
        Reject strategy (admin only)

        Args:
            strategy_id: Strategy ID
            admin: Admin user
            reason: Rejection reason

        Returns:
            Success status
        """
        if not admin.is_superuser:
            logger.error(f"User {admin.id} is not authorized to reject strategies")
            return False

        strategy = self.db.query(StrategyMarketplace).filter(
            StrategyMarketplace.id == strategy_id
        ).first()

        if not strategy:
            return False

        strategy.published = False
        self.db.commit()

        # TODO: Send notification to author with reason

        logger.info(f"Strategy {strategy_id} rejected by admin {admin.id}")

        return True


# Strategy categories
STRATEGY_CATEGORIES = [
    "trend_following",
    "mean_reversion",
    "momentum",
    "arbitrage",
    "market_making",
    "scalping",
    "swing_trading",
    "ai_ml",
    "technical_analysis",
    "fundamental_analysis",
    "other"
]
