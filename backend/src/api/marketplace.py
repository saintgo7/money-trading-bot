"""
Strategy Marketplace API Routes
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime

from ..core.database import get_db
from ..core.auth import get_current_user
from ..models.user import User
from ..models.subscription import StrategyMarketplace, StrategyPurchase, StrategyReview
from ..services.marketplace_service import MarketplaceService, STRATEGY_CATEGORIES

router = APIRouter(prefix="/api/v1/marketplace", tags=["marketplace"])


# Schemas

class PublishStrategyRequest(BaseModel):
    name: str = Field(..., min_length=3, max_length=100)
    description: str = Field(..., min_length=10)
    strategy_config: dict
    category: str
    price: float = Field(0.0, ge=0)
    tags: Optional[List[str]] = []
    performance_metrics: Optional[dict] = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    description: str
    author_id: int
    category: str
    price: float
    currency: str
    downloads: int
    rating: float
    review_count: int
    published: bool
    featured: bool
    verified: bool
    created_at: datetime
    tags: List[str]

    # Optional performance metrics
    backtested_return: Optional[float]
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: Optional[float]

    class Config:
        from_attributes = True


class StrategyDetailResponse(StrategyResponse):
    strategy_config: dict


class PurchaseResponse(BaseModel):
    id: int
    strategy_id: int
    price_paid: float
    currency: str
    purchased_at: datetime

    class Config:
        from_attributes = True


class AddReviewRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5)
    title: Optional[str] = Field(None, max_length=100)
    comment: Optional[str] = Field(None, max_length=1000)


class ReviewResponse(BaseModel):
    id: int
    strategy_id: int
    user_id: int
    rating: int
    title: Optional[str]
    comment: Optional[str]
    helpful_count: int
    created_at: datetime

    class Config:
        from_attributes = True


class MarketplaceStatsResponse(BaseModel):
    total_strategies: int
    total_downloads: int
    average_rating: float
    total_revenue: float
    categories: dict


# Routes

@router.post("/publish", response_model=StrategyResponse)
async def publish_strategy(
    request: PublishStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Publish strategy to marketplace"""

    # Validate category
    if request.category not in STRATEGY_CATEGORIES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid category. Must be one of: {', '.join(STRATEGY_CATEGORIES)}"
        )

    marketplace_service = MarketplaceService(db)
    strategy = await marketplace_service.publish_strategy(
        user=current_user,
        name=request.name,
        description=request.description,
        strategy_config=request.strategy_config,
        category=request.category,
        price=request.price,
        tags=request.tags,
        performance_metrics=request.performance_metrics
    )

    if not strategy:
        raise HTTPException(status_code=500, detail="Failed to publish strategy")

    return strategy


@router.get("/search", response_model=List[StrategyResponse])
async def search_strategies(
    query: Optional[str] = Query(None, description="Search query"),
    category: Optional[str] = Query(None, description="Filter by category"),
    tags: Optional[List[str]] = Query(None, description="Filter by tags"),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    max_price: Optional[float] = Query(None, ge=0),
    sort_by: str = Query("downloads", description="Sort by: downloads, rating, price, created_at"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Search marketplace strategies"""
    marketplace_service = MarketplaceService(db)
    strategies = await marketplace_service.search_strategies(
        query=query,
        category=category,
        tags=tags,
        min_rating=min_rating,
        max_price=max_price,
        sort_by=sort_by,
        limit=limit,
        offset=offset
    )

    return strategies


@router.get("/categories", response_model=List[str])
async def get_categories():
    """Get all available strategy categories"""
    return STRATEGY_CATEGORIES


@router.get("/featured", response_model=List[StrategyResponse])
async def get_featured_strategies(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get featured strategies"""
    marketplace_service = MarketplaceService(db)
    strategies = await marketplace_service.get_featured_strategies(limit=limit)

    return strategies


@router.get("/trending", response_model=List[StrategyResponse])
async def get_trending_strategies(
    days: int = Query(7, ge=1, le=30),
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """Get trending strategies"""
    marketplace_service = MarketplaceService(db)
    strategies = await marketplace_service.get_trending_strategies(days=days, limit=limit)

    return strategies


@router.get("/strategies/{strategy_id}", response_model=StrategyDetailResponse)
async def get_strategy(
    strategy_id: int,
    db: Session = Depends(get_db)
):
    """Get strategy details"""
    marketplace_service = MarketplaceService(db)
    strategy = await marketplace_service.get_strategy(strategy_id)

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    return strategy


@router.post("/strategies/{strategy_id}/purchase", response_model=PurchaseResponse)
async def purchase_strategy(
    strategy_id: int,
    payment_method_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Purchase strategy from marketplace"""
    marketplace_service = MarketplaceService(db)
    purchase = await marketplace_service.purchase_strategy(
        user=current_user,
        strategy_id=strategy_id,
        payment_method_id=payment_method_id
    )

    if not purchase:
        raise HTTPException(status_code=500, detail="Failed to purchase strategy")

    return purchase


@router.get("/purchases", response_model=List[PurchaseResponse])
async def get_my_purchases(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's purchased strategies"""
    marketplace_service = MarketplaceService(db)
    purchases = await marketplace_service.get_user_purchases(current_user)

    return purchases


@router.get("/my-strategies", response_model=List[StrategyResponse])
async def get_my_published_strategies(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get strategies published by current user"""
    marketplace_service = MarketplaceService(db)
    strategies = await marketplace_service.get_user_published_strategies(current_user)

    return strategies


@router.post("/strategies/{strategy_id}/review", response_model=ReviewResponse)
async def add_review(
    strategy_id: int,
    request: AddReviewRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Add review for strategy"""
    marketplace_service = MarketplaceService(db)
    review = await marketplace_service.add_review(
        user=current_user,
        strategy_id=strategy_id,
        rating=request.rating,
        title=request.title,
        comment=request.comment
    )

    if not review:
        raise HTTPException(status_code=500, detail="Failed to add review")

    return review


@router.get("/strategies/{strategy_id}/reviews", response_model=List[ReviewResponse])
async def get_strategy_reviews(
    strategy_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Get reviews for strategy"""
    marketplace_service = MarketplaceService(db)
    reviews = await marketplace_service.get_strategy_reviews(
        strategy_id=strategy_id,
        limit=limit,
        offset=offset
    )

    return reviews


@router.get("/stats", response_model=MarketplaceStatsResponse)
async def get_marketplace_stats(
    db: Session = Depends(get_db)
):
    """Get marketplace statistics"""
    marketplace_service = MarketplaceService(db)
    stats = await marketplace_service.get_marketplace_stats()

    return stats


# Admin routes

@router.post("/admin/strategies/{strategy_id}/approve")
async def approve_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Approve strategy for publication (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    marketplace_service = MarketplaceService(db)
    success = await marketplace_service.approve_strategy(strategy_id, current_user)

    if not success:
        raise HTTPException(status_code=500, detail="Failed to approve strategy")

    return {"message": "Strategy approved"}


@router.post("/admin/strategies/{strategy_id}/reject")
async def reject_strategy(
    strategy_id: int,
    reason: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Reject strategy (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    marketplace_service = MarketplaceService(db)
    success = await marketplace_service.reject_strategy(
        strategy_id,
        current_user,
        reason
    )

    if not success:
        raise HTTPException(status_code=500, detail="Failed to reject strategy")

    return {"message": "Strategy rejected"}


@router.patch("/admin/strategies/{strategy_id}/feature")
async def feature_strategy(
    strategy_id: int,
    featured: bool = True,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark strategy as featured (admin only)"""
    if not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Admin access required")

    strategy = db.query(StrategyMarketplace).filter(
        StrategyMarketplace.id == strategy_id
    ).first()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    strategy.featured = featured
    db.commit()

    return {"message": f"Strategy {'featured' if featured else 'unfeatured'}"}


@router.delete("/strategies/{strategy_id}")
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete own strategy"""
    strategy = db.query(StrategyMarketplace).filter(
        StrategyMarketplace.id == strategy_id
    ).first()

    if not strategy:
        raise HTTPException(status_code=404, detail="Strategy not found")

    if strategy.author_id != current_user.id and not current_user.is_superuser:
        raise HTTPException(status_code=403, detail="Not authorized")

    db.delete(strategy)
    db.commit()

    return {"message": "Strategy deleted"}


@router.get("/earnings", response_model=dict)
async def get_my_earnings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get earnings from published strategies"""
    from sqlalchemy import func

    # Get total earnings from strategy sales
    total_earnings = db.query(
        func.sum(StrategyPurchase.price_paid)
    ).join(
        StrategyMarketplace,
        StrategyPurchase.strategy_id == StrategyMarketplace.id
    ).filter(
        StrategyMarketplace.author_id == current_user.id
    ).scalar()

    # Get total downloads
    total_downloads = db.query(
        func.sum(StrategyMarketplace.downloads)
    ).filter(
        StrategyMarketplace.author_id == current_user.id
    ).scalar()

    # Get strategy count
    strategy_count = db.query(
        func.count(StrategyMarketplace.id)
    ).filter(
        StrategyMarketplace.author_id == current_user.id
    ).scalar()

    return {
        'total_earnings': float(total_earnings) if total_earnings else 0.0,
        'total_downloads': int(total_downloads) if total_downloads else 0,
        'strategy_count': strategy_count or 0
    }
