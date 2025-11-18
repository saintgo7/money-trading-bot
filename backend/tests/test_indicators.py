import pytest
import numpy as np
import pandas as pd
from src.strategies.indicators import TechnicalIndicators


def test_sma():
    """Test Simple Moving Average calculation."""
    data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    sma = TechnicalIndicators.sma(data, period=3)

    assert not sma.isna().all()
    assert sma.iloc[-1] == 9.0  # Average of 8, 9, 10


def test_ema():
    """Test Exponential Moving Average calculation."""
    data = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
    ema = TechnicalIndicators.ema(data, period=3)

    assert not ema.isna().all()
    assert ema.iloc[-1] > 0


def test_rsi():
    """Test RSI calculation."""
    # Create sample data with uptrend
    data = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20] * 3)
    rsi = TechnicalIndicators.rsi(data, period=14)

    assert not rsi.isna().all()
    # RSI should be high for uptrend
    assert rsi.iloc[-1] > 50


def test_macd():
    """Test MACD calculation."""
    data = pd.Series(np.random.randn(100).cumsum() + 100)
    macd, signal, hist = TechnicalIndicators.macd(data)

    assert not macd.isna().all()
    assert not signal.isna().all()
    assert not hist.isna().all()


def test_bollinger_bands():
    """Test Bollinger Bands calculation."""
    data = pd.Series(np.random.randn(100).cumsum() + 100)
    upper, middle, lower = TechnicalIndicators.bollinger_bands(data, period=20)

    assert not upper.isna().all()
    assert not middle.isna().all()
    assert not lower.isna().all()
    # Upper should be greater than lower
    assert upper.iloc[-1] > lower.iloc[-1]


def test_calculate_all_indicators():
    """Test calculating all indicators at once."""
    # Create sample OHLCV data
    df = pd.DataFrame({
        'open': np.random.randn(100).cumsum() + 100,
        'high': np.random.randn(100).cumsum() + 102,
        'low': np.random.randn(100).cumsum() + 98,
        'close': np.random.randn(100).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 100),
    })

    result = TechnicalIndicators.calculate_all_indicators(df)

    # Check that indicators were added
    assert 'sma_20' in result.columns
    assert 'rsi' in result.columns
    assert 'macd' in result.columns
    assert 'bb_upper' in result.columns
    assert result.shape[0] == df.shape[0]
