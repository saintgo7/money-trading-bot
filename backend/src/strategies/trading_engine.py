from typing import Dict, Optional, List
from decimal import Decimal
import pandas as pd
from loguru import logger
from datetime import datetime, timedelta

from ..exchanges.base import BaseExchange, OrderSide, OrderType
from ..exchanges.binance_exchange import BinanceExchange
from ..exchanges.upbit_exchange import UpbitExchange
from .indicators import TechnicalIndicators
from .ai_model import AITradingStrategy


class TradingEngine:
    """
    Main trading engine that executes strategies and manages positions
    """

    def __init__(
        self,
        exchange: BaseExchange,
        symbol: str,
        strategy_type: str = "ai",
        initial_capital: Decimal = Decimal("10000"),
    ):
        self.exchange = exchange
        self.symbol = symbol
        self.strategy_type = strategy_type
        self.initial_capital = initial_capital
        self.current_capital = initial_capital

        # Position tracking
        self.position: Optional[Dict] = None  # Current open position
        self.position_size = Decimal("0")
        self.entry_price = Decimal("0")

        # Risk management
        self.max_position_size_pct = 0.1  # Max 10% of capital per trade
        self.stop_loss_pct = 0.05  # 5% stop loss
        self.take_profit_pct = 0.10  # 10% take profit

        # AI Strategy
        if strategy_type == "ai":
            self.ai_strategy = AITradingStrategy(model_type="lstm", sequence_length=60)
        else:
            self.ai_strategy = None

        # Performance tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = Decimal("0")

        logger.info(
            f"Trading Engine initialized for {symbol} on {exchange.exchange_name}"
        )

    async def analyze_market(self, lookback_periods: int = 200) -> pd.DataFrame:
        """
        Fetch and analyze market data

        Args:
            lookback_periods: Number of periods to fetch

        Returns:
            DataFrame with OHLCV and indicators
        """
        try:
            # Fetch OHLCV data
            ohlcv = await self.exchange.get_ohlcv(
                symbol=self.symbol, timeframe="1h", limit=lookback_periods
            )

            # Convert to DataFrame
            df = pd.DataFrame(ohlcv)

            # Calculate all technical indicators
            df = TechnicalIndicators.calculate_all_indicators(df)

            logger.info(f"Market analysis completed: {len(df)} periods analyzed")
            return df

        except Exception as e:
            logger.error(f"Error analyzing market: {e}")
            raise

    async def generate_signal(self, df: pd.DataFrame) -> Dict:
        """
        Generate trading signal based on strategy

        Args:
            df: DataFrame with market data and indicators

        Returns:
            Dict with signal, confidence, and reasoning
        """
        try:
            if self.strategy_type == "ai":
                return await self._ai_signal(df)
            elif self.strategy_type == "technical":
                return await self._technical_signal(df)
            else:
                return await self._hybrid_signal(df)

        except Exception as e:
            logger.error(f"Error generating signal: {e}")
            return {"signal": "hold", "confidence": 0.0, "reasoning": str(e)}

    async def _ai_signal(self, df: pd.DataFrame) -> Dict:
        """Generate AI-based signal"""
        if self.ai_strategy is None or self.ai_strategy.model is None:
            logger.warning("AI model not initialized, using technical analysis")
            return await self._technical_signal(df)

        prediction = self.ai_strategy.predict(df)
        return {
            "signal": prediction["signal"],
            "confidence": prediction["confidence"],
            "reasoning": f"AI prediction with {prediction['confidence']:.2%} confidence",
            "probabilities": prediction["probabilities"],
        }

    async def _technical_signal(self, df: pd.DataFrame) -> Dict:
        """Generate technical analysis-based signal"""
        if len(df) < 50:
            return {"signal": "hold", "confidence": 0.5, "reasoning": "Insufficient data"}

        latest = df.iloc[-1]
        prev = df.iloc[-2]

        buy_signals = 0
        sell_signals = 0
        total_signals = 0

        # RSI signals
        if "rsi" in latest:
            total_signals += 1
            if latest["rsi"] < 30:
                buy_signals += 1
            elif latest["rsi"] > 70:
                sell_signals += 1

        # MACD signals
        if "macd" in latest and "macd_signal" in latest:
            total_signals += 1
            if latest["macd"] > latest["macd_signal"] and prev["macd"] <= prev["macd_signal"]:
                buy_signals += 1
            elif latest["macd"] < latest["macd_signal"] and prev["macd"] >= prev["macd_signal"]:
                sell_signals += 1

        # Moving average crossover
        if "ema_12" in latest and "ema_26" in latest:
            total_signals += 1
            if latest["ema_12"] > latest["ema_26"] and prev["ema_12"] <= prev["ema_26"]:
                buy_signals += 1
            elif latest["ema_12"] < latest["ema_26"] and prev["ema_12"] >= prev["ema_26"]:
                sell_signals += 1

        # Bollinger Bands
        if "bb_upper" in latest and "bb_lower" in latest:
            total_signals += 1
            if latest["close"] < latest["bb_lower"]:
                buy_signals += 1
            elif latest["close"] > latest["bb_upper"]:
                sell_signals += 1

        # Determine signal
        if buy_signals > sell_signals and buy_signals >= total_signals * 0.6:
            signal = "buy"
            confidence = buy_signals / total_signals
        elif sell_signals > buy_signals and sell_signals >= total_signals * 0.6:
            signal = "sell"
            confidence = sell_signals / total_signals
        else:
            signal = "hold"
            confidence = 0.5

        return {
            "signal": signal,
            "confidence": confidence,
            "reasoning": f"{buy_signals} buy signals, {sell_signals} sell signals out of {total_signals}",
        }

    async def _hybrid_signal(self, df: pd.DataFrame) -> Dict:
        """Combine AI and technical signals"""
        ai_signal = await self._ai_signal(df)
        tech_signal = await self._technical_signal(df)

        # Weight: 60% AI, 40% Technical
        if ai_signal["signal"] == tech_signal["signal"]:
            # Both agree
            confidence = 0.6 * ai_signal["confidence"] + 0.4 * tech_signal["confidence"]
            return {
                "signal": ai_signal["signal"],
                "confidence": confidence,
                "reasoning": f"AI and Technical analysis agree: {ai_signal['signal']}",
            }
        else:
            # Conflict - prefer AI if high confidence
            if ai_signal["confidence"] > 0.7:
                return ai_signal
            elif tech_signal["confidence"] > 0.7:
                return tech_signal
            else:
                return {"signal": "hold", "confidence": 0.5, "reasoning": "Conflicting signals"}

    async def execute_trade(self, signal: Dict) -> Optional[Dict]:
        """
        Execute trade based on signal

        Args:
            signal: Trading signal dict

        Returns:
            Order details if trade executed, None otherwise
        """
        try:
            # Check if we should trade based on confidence
            if signal["confidence"] < 0.6:
                logger.info(f"Signal confidence too low ({signal['confidence']:.2%}), skipping trade")
                return None

            current_price = await self._get_current_price()

            if signal["signal"] == "buy" and self.position is None:
                return await self._open_long_position(current_price, signal)

            elif signal["signal"] == "sell" and self.position is not None:
                return await self._close_position(current_price, signal)

            else:
                logger.info(f"No action taken for signal: {signal['signal']}")
                return None

        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None

    async def _open_long_position(self, price: Decimal, signal: Dict) -> Dict:
        """Open a long position"""
        # Calculate position size
        position_value = self.current_capital * Decimal(str(self.max_position_size_pct))
        quantity = position_value / price

        # Place market buy order
        order = await self.exchange.place_order(
            symbol=self.symbol,
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=quantity,
        )

        # Update position
        self.position = {
            "side": "long",
            "entry_price": price,
            "quantity": quantity,
            "entry_time": datetime.now(),
            "order_id": order["order_id"],
        }

        self.entry_price = price
        self.position_size = quantity

        logger.info(f"Opened LONG position: {quantity} @ {price}")

        return order

    async def _close_position(self, price: Decimal, signal: Dict) -> Dict:
        """Close current position"""
        if self.position is None:
            logger.warning("No position to close")
            return None

        # Place market sell order
        order = await self.exchange.place_order(
            symbol=self.symbol,
            side=OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=self.position_size,
        )

        # Calculate P&L
        pnl = (price - self.entry_price) * self.position_size
        pnl_pct = ((price - self.entry_price) / self.entry_price) * 100

        # Update capital
        self.current_capital += pnl
        self.total_pnl += pnl

        # Update stats
        self.total_trades += 1
        if pnl > 0:
            self.winning_trades += 1
        else:
            self.losing_trades += 1

        logger.info(
            f"Closed position: {self.position_size} @ {price} | P&L: {pnl} ({pnl_pct:.2f}%)"
        )

        # Clear position
        self.position = None
        self.position_size = Decimal("0")
        self.entry_price = Decimal("0")

        return order

    async def check_stop_loss_take_profit(self):
        """Check and execute stop loss or take profit"""
        if self.position is None:
            return

        current_price = await self._get_current_price()
        entry_price = self.position["entry_price"]

        # Calculate price change percentage
        price_change_pct = ((current_price - entry_price) / entry_price) * 100

        # Check stop loss
        if price_change_pct <= -self.stop_loss_pct * 100:
            logger.warning(f"Stop loss triggered at {price_change_pct:.2f}%")
            await self._close_position(
                current_price, {"signal": "stop_loss", "confidence": 1.0}
            )

        # Check take profit
        elif price_change_pct >= self.take_profit_pct * 100:
            logger.info(f"Take profit triggered at {price_change_pct:.2f}%")
            await self._close_position(
                current_price, {"signal": "take_profit", "confidence": 1.0}
            )

    async def _get_current_price(self) -> Decimal:
        """Get current market price"""
        ticker = await self.exchange.get_ticker(self.symbol)
        return ticker["last"]

    def get_performance_stats(self) -> Dict:
        """Get performance statistics"""
        win_rate = (
            (self.winning_trades / self.total_trades * 100)
            if self.total_trades > 0
            else 0
        )

        roi = (
            ((self.current_capital - self.initial_capital) / self.initial_capital * 100)
            if self.initial_capital > 0
            else 0
        )

        return {
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": f"{win_rate:.2f}%",
            "total_pnl": float(self.total_pnl),
            "current_capital": float(self.current_capital),
            "initial_capital": float(self.initial_capital),
            "roi": f"{roi:.2f}%",
            "has_open_position": self.position is not None,
        }

    async def run_trading_cycle(self):
        """Run one complete trading cycle"""
        try:
            logger.info("Starting trading cycle...")

            # 1. Analyze market
            df = await self.analyze_market()

            # 2. Generate signal
            signal = await self.generate_signal(df)
            logger.info(f"Signal: {signal['signal']} (confidence: {signal['confidence']:.2%})")

            # 3. Check stop loss / take profit
            await self.check_stop_loss_take_profit()

            # 4. Execute trade if signal is strong
            if signal["signal"] != "hold":
                order = await self.execute_trade(signal)
                if order:
                    logger.info(f"Trade executed: {order}")

            # 5. Log performance
            stats = self.get_performance_stats()
            logger.info(f"Performance: {stats}")

        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
