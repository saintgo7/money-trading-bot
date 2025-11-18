from celery import shared_task
from loguru import logger
from decimal import Decimal
from datetime import datetime
import asyncio
from sqlalchemy import select

from .celery_app import celery_app
from ..core.database import AsyncSessionLocal
from ..models.trading import TradingBot, BotStatus, Order, MarketData
from ..exchanges.binance_exchange import BinanceExchange
from ..exchanges.upbit_exchange import UpbitExchange
from ..strategies.trading_engine import TradingEngine
from ..core.config import settings


def get_exchange(exchange_name: str, testnet: bool = False):
    """Get exchange instance"""
    if exchange_name.lower() == "binance":
        return BinanceExchange(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            testnet=testnet,
        )
    elif exchange_name.lower() == "upbit":
        return UpbitExchange(
            access_key=settings.UPBIT_ACCESS_KEY,
            secret_key=settings.UPBIT_SECRET_KEY,
            testnet=testnet,
        )
    else:
        raise ValueError(f"Unsupported exchange: {exchange_name}")


@celery_app.task(name="src.tasks.trading_tasks.run_trading_bot")
def run_trading_bot(bot_id: int):
    """Run a single trading bot cycle"""
    asyncio.run(_run_trading_bot_async(bot_id))


async def _run_trading_bot_async(bot_id: int):
    """Async implementation of run_trading_bot"""
    async with AsyncSessionLocal() as db:
        try:
            # Fetch bot from database
            result = await db.execute(select(TradingBot).where(TradingBot.id == bot_id))
            bot = result.scalar_one_or_none()

            if not bot:
                logger.error(f"Bot {bot_id} not found")
                return

            if bot.status != BotStatus.RUNNING:
                logger.info(f"Bot {bot_id} is not running, skipping")
                return

            logger.info(f"Running bot {bot.name} (ID: {bot_id})")

            # Get exchange instance
            exchange = get_exchange(bot.exchange, testnet=True)
            await exchange.connect()

            # Create trading engine
            engine = TradingEngine(
                exchange=exchange,
                symbol=bot.trading_pair,
                strategy_type=bot.strategy.strategy_type if bot.strategy else "technical",
                initial_capital=bot.initial_capital,
            )

            # Restore bot state
            engine.current_capital = bot.current_capital
            engine.total_trades = bot.total_trades
            engine.winning_trades = bot.winning_trades
            engine.losing_trades = bot.losing_trades

            # Run trading cycle
            await engine.run_trading_cycle()

            # Update bot in database
            bot.current_capital = engine.current_capital
            bot.total_trades = engine.total_trades
            bot.winning_trades = engine.winning_trades
            bot.losing_trades = engine.losing_trades
            bot.total_profit_loss = engine.total_pnl
            bot.win_rate = (
                Decimal(str(engine.winning_trades / engine.total_trades * 100))
                if engine.total_trades > 0
                else Decimal("0")
            )
            bot.updated_at = datetime.utcnow()

            await db.commit()

            await exchange.disconnect()

            logger.info(f"Bot {bot.name} cycle completed successfully")

        except Exception as e:
            logger.error(f"Error running bot {bot_id}: {e}")
            await db.rollback()

            # Update bot status to error
            try:
                result = await db.execute(select(TradingBot).where(TradingBot.id == bot_id))
                bot = result.scalar_one_or_none()
                if bot:
                    bot.status = BotStatus.ERROR
                    await db.commit()
            except:
                pass


@celery_app.task(name="src.tasks.trading_tasks.run_all_active_bots")
def run_all_active_bots():
    """Run all active trading bots"""
    asyncio.run(_run_all_active_bots_async())


async def _run_all_active_bots_async():
    """Async implementation of run_all_active_bots"""
    async with AsyncSessionLocal() as db:
        try:
            # Fetch all running bots
            result = await db.execute(
                select(TradingBot).where(
                    TradingBot.status == BotStatus.RUNNING, TradingBot.is_active == True
                )
            )
            bots = result.scalars().all()

            logger.info(f"Found {len(bots)} active bots to run")

            # Run each bot
            for bot in bots:
                try:
                    run_trading_bot.delay(bot.id)
                except Exception as e:
                    logger.error(f"Error scheduling bot {bot.id}: {e}")

        except Exception as e:
            logger.error(f"Error fetching active bots: {e}")


@celery_app.task(name="src.tasks.trading_tasks.update_market_data")
def update_market_data():
    """Update market data for all trading pairs"""
    asyncio.run(_update_market_data_async())


async def _update_market_data_async():
    """Async implementation of update_market_data"""
    async with AsyncSessionLocal() as db:
        try:
            # Get unique trading pairs from active bots
            result = await db.execute(
                select(TradingBot.trading_pair, TradingBot.exchange)
                .where(TradingBot.is_active == True)
                .distinct()
            )
            pairs = result.all()

            logger.info(f"Updating market data for {len(pairs)} trading pairs")

            for pair, exchange_name in pairs:
                try:
                    # Get exchange
                    exchange = get_exchange(exchange_name, testnet=True)
                    await exchange.connect()

                    # Fetch OHLCV data
                    ohlcv = await exchange.get_ohlcv(symbol=pair, timeframe="1h", limit=1)

                    if ohlcv:
                        candle = ohlcv[0]

                        # Save to database
                        market_data = MarketData(
                            symbol=pair,
                            exchange=exchange_name,
                            timeframe="1h",
                            timestamp=candle["timestamp"],
                            open=candle["open"],
                            high=candle["high"],
                            low=candle["low"],
                            close=candle["close"],
                            volume=candle["volume"],
                        )

                        db.add(market_data)
                        await db.commit()

                    await exchange.disconnect()

                except Exception as e:
                    logger.error(f"Error updating market data for {pair}: {e}")

        except Exception as e:
            logger.error(f"Error in update_market_data: {e}")


@celery_app.task(name="src.tasks.trading_tasks.check_bot_health")
def check_bot_health():
    """Check health of all running bots"""
    asyncio.run(_check_bot_health_async())


async def _check_bot_health_async():
    """Async implementation of check_bot_health"""
    async with AsyncSessionLocal() as db:
        try:
            # Fetch all running bots
            result = await db.execute(
                select(TradingBot).where(TradingBot.status == BotStatus.RUNNING)
            )
            bots = result.scalars().all()

            logger.info(f"Checking health of {len(bots)} bots")

            for bot in bots:
                try:
                    # Check if bot has exceeded max daily loss
                    if bot.max_daily_loss and bot.total_profit_loss < -bot.max_daily_loss:
                        logger.warning(
                            f"Bot {bot.name} exceeded max daily loss, stopping"
                        )
                        bot.status = BotStatus.STOPPED
                        bot.stopped_at = datetime.utcnow()

                    # Check if bot capital is too low
                    min_capital = bot.initial_capital * Decimal("0.5")  # 50% of initial
                    if bot.current_capital < min_capital:
                        logger.warning(
                            f"Bot {bot.name} capital too low ({bot.current_capital}), stopping"
                        )
                        bot.status = BotStatus.STOPPED
                        bot.stopped_at = datetime.utcnow()

                    await db.commit()

                except Exception as e:
                    logger.error(f"Error checking health of bot {bot.id}: {e}")

        except Exception as e:
            logger.error(f"Error in check_bot_health: {e}")


@celery_app.task(name="src.tasks.trading_tasks.backtest_strategy")
def backtest_strategy(strategy_id: int, symbol: str, start_date: str, end_date: str):
    """Run backtesting for a strategy"""
    # TODO: Implement backtesting logic
    logger.info(f"Backtesting strategy {strategy_id} for {symbol}")
    return {"status": "completed", "strategy_id": strategy_id}
