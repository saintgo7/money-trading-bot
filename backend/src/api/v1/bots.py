from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from decimal import Decimal
from typing import List, Optional
from datetime import datetime

from ...core.database import get_db
from ...core.security import get_current_active_user
from ...models.user import User
from ...models.trading import TradingBot, BotStatus, Order, Trade
from ...tasks.trading_tasks import run_trading_bot

router = APIRouter()


class BotCreate(BaseModel):
    name: str
    description: Optional[str] = None
    exchange: str
    trading_pair: str
    initial_capital: Decimal
    max_position_size: Decimal = Decimal("10.0")
    stop_loss_percentage: Decimal = Decimal("5.0")
    take_profit_percentage: Decimal = Decimal("10.0")
    strategy_id: Optional[int] = None


class BotUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    max_position_size: Optional[Decimal] = None
    stop_loss_percentage: Optional[Decimal] = None
    take_profit_percentage: Optional[Decimal] = None


class BotResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    exchange: str
    trading_pair: str
    status: BotStatus
    initial_capital: Decimal
    current_capital: Decimal
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: Decimal
    total_profit_loss: Decimal
    created_at: datetime
    started_at: Optional[datetime]

    class Config:
        from_attributes = True


class OrderResponse(BaseModel):
    id: int
    symbol: str
    side: str
    order_type: str
    quantity: Decimal
    price: Optional[Decimal]
    status: str
    filled_quantity: Decimal
    created_at: datetime

    class Config:
        from_attributes = True


class TradeResponse(BaseModel):
    id: int
    symbol: str
    entry_price: Decimal
    exit_price: Optional[Decimal]
    quantity: Decimal = None
    profit_loss: Optional[Decimal]
    profit_loss_percentage: Optional[Decimal]
    is_open: bool
    entry_time: datetime
    exit_time: Optional[datetime]

    class Config:
        from_attributes = True


@router.post("/", response_model=BotResponse, status_code=status.HTTP_201_CREATED)
async def create_bot(
    bot_data: BotCreate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a new trading bot"""
    bot = TradingBot(
        owner_id=current_user.id,
        name=bot_data.name,
        description=bot_data.description,
        exchange=bot_data.exchange,
        trading_pair=bot_data.trading_pair,
        initial_capital=bot_data.initial_capital,
        current_capital=bot_data.initial_capital,
        max_position_size=bot_data.max_position_size,
        stop_loss_percentage=bot_data.stop_loss_percentage,
        take_profit_percentage=bot_data.take_profit_percentage,
        strategy_id=bot_data.strategy_id,
        status=BotStatus.STOPPED,
    )

    db.add(bot)
    await db.commit()
    await db.refresh(bot)

    return bot


@router.get("/", response_model=List[BotResponse])
async def list_bots(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """List all bots for current user"""
    result = await db.execute(
        select(TradingBot).where(TradingBot.owner_id == current_user.id)
    )
    bots = result.scalars().all()
    return bots


@router.get("/{bot_id}", response_model=BotResponse)
async def get_bot(
    bot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a specific bot"""
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    return bot


@router.patch("/{bot_id}", response_model=BotResponse)
async def update_bot(
    bot_id: int,
    bot_update: BotUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Update a bot"""
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    # Update fields
    update_data = bot_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(bot, field, value)

    await db.commit()
    await db.refresh(bot)

    return bot


@router.delete("/{bot_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_bot(
    bot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Delete a bot"""
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    if bot.status == BotStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete a running bot. Stop it first.",
        )

    await db.delete(bot)
    await db.commit()


@router.post("/{bot_id}/start", response_model=BotResponse)
async def start_bot(
    bot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Start a bot"""
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    if bot.status == BotStatus.RUNNING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Bot is already running"
        )

    bot.status = BotStatus.RUNNING
    bot.started_at = datetime.utcnow()
    await db.commit()
    await db.refresh(bot)

    # Schedule bot to run
    run_trading_bot.delay(bot_id)

    return bot


@router.post("/{bot_id}/stop", response_model=BotResponse)
async def stop_bot(
    bot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Stop a bot"""
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    bot.status = BotStatus.STOPPED
    bot.stopped_at = datetime.utcnow()
    await db.commit()
    await db.refresh(bot)

    return bot


@router.get("/{bot_id}/orders", response_model=List[OrderResponse])
async def get_bot_orders(
    bot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all orders for a bot"""
    # Verify bot ownership
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    # Fetch orders
    result = await db.execute(select(Order).where(Order.bot_id == bot_id))
    orders = result.scalars().all()

    return orders


@router.get("/{bot_id}/trades", response_model=List[TradeResponse])
async def get_bot_trades(
    bot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all trades for a bot"""
    # Verify bot ownership
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    # Fetch trades
    result = await db.execute(select(Trade).where(Trade.bot_id == bot_id))
    trades = result.scalars().all()

    # Add quantity to response
    for trade in trades:
        trade.quantity = trade.entry_quantity

    return trades


@router.get("/{bot_id}/performance")
async def get_bot_performance(
    bot_id: int,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    """Get bot performance metrics"""
    result = await db.execute(
        select(TradingBot).where(
            TradingBot.id == bot_id, TradingBot.owner_id == current_user.id
        )
    )
    bot = result.scalar_one_or_none()

    if not bot:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Bot not found")

    roi = (
        ((bot.current_capital - bot.initial_capital) / bot.initial_capital * 100)
        if bot.initial_capital > 0
        else 0
    )

    return {
        "total_trades": bot.total_trades,
        "winning_trades": bot.winning_trades,
        "losing_trades": bot.losing_trades,
        "win_rate": float(bot.win_rate),
        "total_pnl": float(bot.total_profit_loss),
        "current_capital": float(bot.current_capital),
        "initial_capital": float(bot.initial_capital),
        "roi": float(roi),
    }
