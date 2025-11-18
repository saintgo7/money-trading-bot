import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from loguru import logger

from ..exchanges.base import BaseExchange
from ..strategies.trading_engine import TradingEngine
from ..strategies.indicators import TechnicalIndicators


class BacktestEngine:
    """
    Backtesting engine for testing trading strategies on historical data
    """

    def __init__(
        self,
        strategy_type: str = "technical",
        initial_capital: Decimal = Decimal("10000"),
        commission: Decimal = Decimal("0.001"),  # 0.1% commission
    ):
        self.strategy_type = strategy_type
        self.initial_capital = initial_capital
        self.current_capital = initial_capital
        self.commission = commission

        # Trading stats
        self.trades: List[Dict] = []
        self.equity_curve: List[Dict] = []
        self.positions: List[Dict] = []

        # Performance metrics
        self.total_trades = 0
        self.winning_trades = 0
        self.losing_trades = 0
        self.total_pnl = Decimal("0")
        self.max_drawdown = Decimal("0")
        self.sharpe_ratio = 0.0

    def run_backtest(
        self,
        historical_data: pd.DataFrame,
        symbol: str,
        strategy_params: Optional[Dict] = None,
    ) -> Dict:
        """
        Run backtest on historical data

        Args:
            historical_data: DataFrame with OHLCV data
            symbol: Trading pair symbol
            strategy_params: Optional strategy parameters

        Returns:
            Backtest results dictionary
        """
        logger.info(f"Starting backtest for {symbol}")
        logger.info(f"Data period: {historical_data.index[0]} to {historical_data.index[-1]}")
        logger.info(f"Total bars: {len(historical_data)}")

        # Calculate technical indicators
        df = TechnicalIndicators.calculate_all_indicators(historical_data)

        # Initialize variables
        position = None
        entry_price = Decimal("0")
        entry_time = None

        # Iterate through data
        for i in range(60, len(df)):  # Start at 60 to have enough data for indicators
            current_bar = df.iloc[i]
            window_data = df.iloc[i - 60 : i]

            # Generate signal
            signal = self._generate_signal(window_data)

            # Execute trades
            if signal["signal"] == "buy" and position is None:
                # Open long position
                entry_price = Decimal(str(current_bar["close"]))
                entry_time = current_bar.name
                position = {
                    "type": "long",
                    "entry_price": entry_price,
                    "entry_time": entry_time,
                    "quantity": self.current_capital * Decimal("0.95") / entry_price,
                }

                # Deduct commission
                commission_cost = position["quantity"] * entry_price * self.commission
                self.current_capital -= commission_cost

                logger.debug(f"BUY at {entry_price} on {entry_time}")

            elif signal["signal"] == "sell" and position is not None:
                # Close position
                exit_price = Decimal(str(current_bar["close"]))
                exit_time = current_bar.name

                # Calculate P&L
                pnl = (exit_price - position["entry_price"]) * position["quantity"]
                commission_cost = position["quantity"] * exit_price * self.commission
                net_pnl = pnl - commission_cost

                self.current_capital += position["quantity"] * exit_price - commission_cost
                self.total_pnl += net_pnl

                # Record trade
                trade = {
                    "entry_time": position["entry_time"],
                    "exit_time": exit_time,
                    "entry_price": position["entry_price"],
                    "exit_price": exit_price,
                    "quantity": position["quantity"],
                    "pnl": net_pnl,
                    "pnl_percentage": (net_pnl / (position["entry_price"] * position["quantity"]))
                    * 100,
                }
                self.trades.append(trade)

                # Update stats
                self.total_trades += 1
                if net_pnl > 0:
                    self.winning_trades += 1
                else:
                    self.losing_trades += 1

                logger.debug(f"SELL at {exit_price} on {exit_time}, P&L: {net_pnl}")

                position = None

            # Record equity
            current_equity = self.current_capital
            if position is not None:
                current_equity += position["quantity"] * Decimal(str(current_bar["close"]))

            self.equity_curve.append(
                {
                    "time": current_bar.name,
                    "equity": float(current_equity),
                    "capital": float(self.current_capital),
                }
            )

        # Close any open position at the end
        if position is not None:
            exit_price = Decimal(str(df.iloc[-1]["close"]))
            pnl = (exit_price - position["entry_price"]) * position["quantity"]
            commission_cost = position["quantity"] * exit_price * self.commission
            net_pnl = pnl - commission_cost
            self.current_capital += position["quantity"] * exit_price - commission_cost
            self.total_pnl += net_pnl
            self.total_trades += 1
            if net_pnl > 0:
                self.winning_trades += 1
            else:
                self.losing_trades += 1

        # Calculate performance metrics
        self._calculate_metrics()

        results = self.get_results()
        logger.info(f"Backtest completed: {results}")

        return results

    def _generate_signal(self, df: pd.DataFrame) -> Dict:
        """Generate trading signal based on strategy"""
        if self.strategy_type == "technical":
            return self._technical_signal(df)
        elif self.strategy_type == "ai":
            # For backtesting, we'll use technical signals
            # In real implementation, you'd use a trained AI model
            return self._technical_signal(df)
        else:
            return {"signal": "hold", "confidence": 0.5}

    def _technical_signal(self, df: pd.DataFrame) -> Dict:
        """Generate technical analysis signal"""
        latest = df.iloc[-1]
        prev = df.iloc[-2]

        buy_signals = 0
        sell_signals = 0
        total_signals = 0

        # RSI
        if "rsi" in latest:
            total_signals += 1
            if latest["rsi"] < 30:
                buy_signals += 1
            elif latest["rsi"] > 70:
                sell_signals += 1

        # MACD
        if "macd" in latest and "macd_signal" in latest:
            total_signals += 1
            if latest["macd"] > latest["macd_signal"] and prev["macd"] <= prev["macd_signal"]:
                buy_signals += 1
            elif latest["macd"] < latest["macd_signal"] and prev["macd"] >= prev["macd_signal"]:
                sell_signals += 1

        # EMA crossover
        if "ema_12" in latest and "ema_26" in latest:
            total_signals += 1
            if latest["ema_12"] > latest["ema_26"] and prev["ema_12"] <= prev["ema_26"]:
                buy_signals += 1
            elif latest["ema_12"] < latest["ema_26"] and prev["ema_12"] >= prev["ema_26"]:
                sell_signals += 1

        # Determine signal
        if buy_signals > sell_signals and buy_signals >= total_signals * 0.6:
            return {"signal": "buy", "confidence": buy_signals / total_signals}
        elif sell_signals > buy_signals and sell_signals >= total_signals * 0.6:
            return {"signal": "sell", "confidence": sell_signals / total_signals}
        else:
            return {"signal": "hold", "confidence": 0.5}

    def _calculate_metrics(self):
        """Calculate performance metrics"""
        if len(self.equity_curve) == 0:
            return

        # Calculate max drawdown
        equity = [e["equity"] for e in self.equity_curve]
        peak = equity[0]
        max_dd = 0

        for value in equity:
            if value > peak:
                peak = value
            dd = (peak - value) / peak * 100
            if dd > max_dd:
                max_dd = dd

        self.max_drawdown = Decimal(str(max_dd))

        # Calculate Sharpe ratio
        returns = pd.Series([e["equity"] for e in self.equity_curve]).pct_change().dropna()
        if len(returns) > 0 and returns.std() > 0:
            self.sharpe_ratio = (returns.mean() / returns.std()) * np.sqrt(252)  # Annualized
        else:
            self.sharpe_ratio = 0.0

    def get_results(self) -> Dict:
        """Get backtest results"""
        win_rate = (
            (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0
        )

        roi = (
            ((self.current_capital - self.initial_capital) / self.initial_capital * 100)
            if self.initial_capital > 0
            else 0
        )

        avg_win = (
            sum(t["pnl"] for t in self.trades if t["pnl"] > 0) / self.winning_trades
            if self.winning_trades > 0
            else 0
        )

        avg_loss = (
            sum(t["pnl"] for t in self.trades if t["pnl"] < 0) / self.losing_trades
            if self.losing_trades > 0
            else 0
        )

        profit_factor = abs(avg_win * self.winning_trades / (avg_loss * self.losing_trades)) if self.losing_trades > 0 and avg_loss != 0 else 0

        return {
            "initial_capital": float(self.initial_capital),
            "final_capital": float(self.current_capital),
            "total_pnl": float(self.total_pnl),
            "roi": float(roi),
            "total_trades": self.total_trades,
            "winning_trades": self.winning_trades,
            "losing_trades": self.losing_trades,
            "win_rate": float(win_rate),
            "max_drawdown": float(self.max_drawdown),
            "sharpe_ratio": float(self.sharpe_ratio),
            "avg_win": float(avg_win),
            "avg_loss": float(avg_loss),
            "profit_factor": float(profit_factor),
            "equity_curve": self.equity_curve,
            "trades": [
                {
                    "entry_time": str(t["entry_time"]),
                    "exit_time": str(t["exit_time"]),
                    "entry_price": float(t["entry_price"]),
                    "exit_price": float(t["exit_price"]),
                    "quantity": float(t["quantity"]),
                    "pnl": float(t["pnl"]),
                    "pnl_percentage": float(t["pnl_percentage"]),
                }
                for t in self.trades
            ],
        }
