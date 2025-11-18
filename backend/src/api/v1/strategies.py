from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List, Optional, Dict
from datetime import datetime

from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.user import User
from ...models.trading import Strategy

router = APIRouter()


class StrategyCreate(BaseModel):
    name: str
    description: Optional[str] = None
    strategy_type: str  # ai, technical, hybrid
    parameters: Dict = {}


class StrategyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters: Optional[Dict] = None


class StrategyResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    strategy_type: str
    parameters: Dict
    is_active: bool
    is_public: bool
    sharpe_ratio: Optional[float]
    max_drawdown: Optional[float]
    win_rate: Optional[float]
    created_at: datetime

    class Config:
        from_attributes = True


@router.post("/", response_model=StrategyResponse, status_code=status.HTTP_201_CREATED)
async def create_strategy(
    strategy_data: StrategyCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new trading strategy"""
    strategy = Strategy(
        owner_id=current_user.id,
        name=strategy_data.name,
        description=strategy_data.description,
        strategy_type=strategy_data.strategy_type,
        parameters=strategy_data.parameters,
    )

    db.add(strategy)
    await db.commit()
    await db.refresh(strategy)

    return strategy


@router.get("/", response_model=List[StrategyResponse])
async def list_strategies(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all strategies for current user"""
    result = await db.execute(
        select(Strategy).where(Strategy.owner_id == current_user.id)
    )
    strategies = result.scalars().all()
    return strategies


@router.get("/public", response_model=List[StrategyResponse])
async def list_public_strategies(db: AsyncSession = Depends(get_db)):
    """List all public strategies"""
    result = await db.execute(select(Strategy).where(Strategy.is_public == True))
    strategies = result.scalars().all()
    return strategies


@router.get("/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific strategy"""
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id, Strategy.owner_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
        )

    return strategy


@router.patch("/{strategy_id}", response_model=StrategyResponse)
async def update_strategy(
    strategy_id: int,
    strategy_update: StrategyUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a strategy"""
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id, Strategy.owner_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
        )

    # Update fields
    update_data = strategy_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(strategy, field, value)

    await db.commit()
    await db.refresh(strategy)

    return strategy


@router.delete("/{strategy_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_strategy(
    strategy_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a strategy"""
    result = await db.execute(
        select(Strategy).where(
            Strategy.id == strategy_id, Strategy.owner_id == current_user.id
        )
    )
    strategy = result.scalar_one_or_none()

    if not strategy:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Strategy not found"
        )

    await db.delete(strategy)
    await db.commit()
