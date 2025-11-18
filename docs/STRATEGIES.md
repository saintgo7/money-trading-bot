# Trading Strategies Guide

## Overview

The Money Trading Bot platform supports multiple trading strategies that can be customized and combined for optimal performance.

## Strategy Types

### 1. AI-Based Strategy

Uses deep learning models (LSTM/Transformer) to predict price movements.

**How it works:**
1. Collects historical OHLCV data
2. Calculates technical indicators
3. Feeds data into neural network
4. Generates buy/sell/hold signal with confidence score

**Models:**
- **LSTM** (Long Short-Term Memory): Good for short to medium-term patterns
- **Transformer**: Better for long-term dependencies

**Configuration:**
```python
{
  "strategy_type": "ai",
  "parameters": {
    "model_type": "lstm",  # or "transformer"
    "sequence_length": 60,
    "confidence_threshold": 0.6
  }
}
```

### 2. Technical Analysis Strategy

Uses traditional technical indicators to generate signals.

**Indicators Used:**
- **RSI** (Relative Strength Index): Overbought/oversold conditions
- **MACD** (Moving Average Convergence Divergence): Trend direction
- **Bollinger Bands**: Price volatility
- **Moving Averages**: Trend confirmation
- **Stochastic Oscillator**: Momentum
- **ADX** (Average Directional Index): Trend strength

**Signal Generation:**
```python
# Buy signals:
- RSI < 30 (oversold)
- MACD crosses above signal line
- Price touches lower Bollinger Band
- EMA(12) crosses above EMA(26)

# Sell signals:
- RSI > 70 (overbought)
- MACD crosses below signal line
- Price touches upper Bollinger Band
- EMA(12) crosses below EMA(26)

# Decision: If ≥60% indicators agree → execute trade
```

### 3. Hybrid Strategy

Combines AI predictions with technical analysis.

**How it works:**
1. Get AI prediction (60% weight)
2. Get technical analysis signal (40% weight)
3. If both agree → High confidence trade
4. If they conflict → Prefer signal with higher confidence

**Configuration:**
```python
{
  "strategy_type": "hybrid",
  "parameters": {
    "ai_weight": 0.6,
    "technical_weight": 0.4,
    "min_confidence": 0.7
  }
}
```

## Risk Management

All strategies include risk management:

### Position Sizing
```python
position_size = capital * max_position_size_pct
quantity = position_size / current_price
```

### Stop Loss
Automatically closes position if loss exceeds threshold:
```python
stop_loss_price = entry_price * (1 - stop_loss_percentage / 100)
```

### Take Profit
Automatically closes position when profit target reached:
```python
take_profit_price = entry_price * (1 + take_profit_percentage / 100)
```

### Daily Loss Limit
Stops trading if daily loss exceeds maximum:
```python
if total_daily_loss > max_daily_loss:
    stop_all_trading()
```

## Creating Custom Strategies

### Step 1: Define Strategy Class

```python
# backend/src/strategies/my_strategy.py

from .trading_engine import TradingEngine
import pandas as pd

class MyCustomStrategy(TradingEngine):
    async def _custom_signal(self, df: pd.DataFrame) -> dict:
        """
        Generate custom trading signal

        Args:
            df: DataFrame with OHLCV and indicator data

        Returns:
            {
                "signal": "buy" | "sell" | "hold",
                "confidence": 0.0 to 1.0,
                "reasoning": "explanation"
            }
        """
        latest = df.iloc[-1]

        # Your custom logic here
        if latest['rsi'] < 20 and latest['macd'] > latest['macd_signal']:
            return {
                "signal": "buy",
                "confidence": 0.8,
                "reasoning": "Strong oversold with positive MACD"
            }

        return {
            "signal": "hold",
            "confidence": 0.5,
            "reasoning": "No clear signal"
        }
```

### Step 2: Register Strategy

```python
# backend/src/strategies/__init__.py

from .my_strategy import MyCustomStrategy

__all__ = [..., "MyCustomStrategy"]
```

### Step 3: Use Strategy

```python
from src.strategies.my_strategy import MyCustomStrategy

engine = MyCustomStrategy(
    exchange=exchange,
    symbol="BTC/USDT",
    initial_capital=10000
)
```

## Backtesting Strategies

Test your strategy on historical data:

```python
from src.strategies.trading_engine import TradingEngine
import pandas as pd

# Load historical data
df = pd.read_csv('historical_data.csv')

# Initialize strategy
engine = TradingEngine(
    exchange=mock_exchange,
    symbol="BTC/USDT",
    initial_capital=10000
)

# Run backtest
results = []
for i in range(60, len(df)):
    window = df.iloc[i-60:i]
    signal = await engine.generate_signal(window)
    # Execute virtual trade
    results.append(signal)

# Analyze results
print(f"Final Capital: {engine.current_capital}")
print(f"Win Rate: {engine.win_rate}%")
print(f"Total Trades: {engine.total_trades}")
```

## Strategy Performance Metrics

### Win Rate
```python
win_rate = (winning_trades / total_trades) * 100
```

### ROI (Return on Investment)
```python
roi = ((current_capital - initial_capital) / initial_capital) * 100
```

### Sharpe Ratio
Measures risk-adjusted returns:
```python
sharpe_ratio = (mean_returns - risk_free_rate) / std_returns
```

### Maximum Drawdown
Largest peak-to-trough decline:
```python
max_drawdown = max(peak - trough for peak, trough in drawdowns)
```

### Profit Factor
```python
profit_factor = total_profits / abs(total_losses)
```

## Best Practices

### 1. Diversification
- Trade multiple pairs
- Use different strategies
- Don't put all capital in one bot

### 2. Risk Management
- Never risk more than 2% per trade
- Always use stop-loss
- Set realistic profit targets

### 3. Testing
- Backtest on at least 6 months of data
- Paper trade before real money
- Monitor performance regularly

### 4. Parameter Optimization
- Don't overfit to historical data
- Test across different market conditions
- Use walk-forward optimization

### 5. Market Awareness
- Be aware of major news events
- Adjust strategy for different market phases
- Monitor correlation with market indices

## Example Strategies

### Mean Reversion
```python
def mean_reversion_signal(df):
    latest = df.iloc[-1]
    sma_50 = latest['sma_50']
    current_price = latest['close']

    # Buy when price is 5% below mean
    if current_price < sma_50 * 0.95:
        return {"signal": "buy", "confidence": 0.7}

    # Sell when price is 5% above mean
    if current_price > sma_50 * 1.05:
        return {"signal": "sell", "confidence": 0.7}

    return {"signal": "hold", "confidence": 0.5}
```

### Trend Following
```python
def trend_following_signal(df):
    latest = df.iloc[-1]

    # Check if in uptrend
    if (latest['ema_12'] > latest['ema_26'] and
        latest['adx'] > 25 and
        latest['close'] > latest['sma_50']):
        return {"signal": "buy", "confidence": 0.8}

    # Check if in downtrend
    if (latest['ema_12'] < latest['ema_26'] and
        latest['adx'] > 25 and
        latest['close'] < latest['sma_50']):
        return {"signal": "sell", "confidence": 0.8}

    return {"signal": "hold", "confidence": 0.5}
```

### Breakout Strategy
```python
def breakout_signal(df):
    latest = df.iloc[-1]
    prev = df.iloc[-2]

    # Buy on breakout above resistance
    if (latest['close'] > latest['bb_upper'] and
        prev['close'] <= prev['bb_upper'] and
        latest['volume'] > df['volume'].mean() * 1.5):
        return {"signal": "buy", "confidence": 0.75}

    # Sell on breakdown below support
    if (latest['close'] < latest['bb_lower'] and
        prev['close'] >= prev['bb_lower'] and
        latest['volume'] > df['volume'].mean() * 1.5):
        return {"signal": "sell", "confidence": 0.75}

    return {"signal": "hold", "confidence": 0.5}
```

## Troubleshooting

### Strategy Not Generating Signals
- Check if there's enough historical data
- Verify indicators are calculated correctly
- Review confidence threshold

### Too Many False Signals
- Increase confidence threshold
- Add more confirmation indicators
- Adjust indicator parameters

### Poor Performance
- Backtest on different time periods
- Check if strategy fits market conditions
- Review risk management parameters

## Resources

- [Technical Analysis Library](https://technical-analysis-library-in-python.readthedocs.io/)
- [PyTorch Documentation](https://pytorch.org/docs/stable/index.html)
- [Trading Strategy Examples](https://www.investopedia.com/trading-strategies-4689645)
