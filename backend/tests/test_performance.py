"""
Performance tests for critical operations
"""
import pytest
import asyncio
import time
from httpx import AsyncClient
from decimal import Decimal
import pandas as pd
import numpy as np

from src.strategies.indicators import TechnicalIndicators
from src.strategies.ai_model import AITradingStrategy
from src.services.backtesting import BacktestEngine


@pytest.mark.asyncio
async def test_indicator_calculation_performance():
    """Test performance of indicator calculations"""
    # Generate large dataset
    data_size = 10000
    df = pd.DataFrame({
        'open': np.random.randn(data_size).cumsum() + 100,
        'high': np.random.randn(data_size).cumsum() + 102,
        'low': np.random.randn(data_size).cumsum() + 98,
        'close': np.random.randn(data_size).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, data_size),
    })

    start_time = time.time()
    result = TechnicalIndicators.calculate_all_indicators(df)
    elapsed_time = time.time() - start_time

    assert elapsed_time < 5.0, f"Indicator calculation took too long: {elapsed_time}s"
    assert len(result) == data_size
    assert 'rsi' in result.columns
    assert 'macd' in result.columns


@pytest.mark.asyncio
async def test_backtesting_performance():
    """Test backtesting engine performance"""
    # Generate historical data
    data_size = 1000
    df = pd.DataFrame({
        'open': np.random.randn(data_size).cumsum() + 100,
        'high': np.random.randn(data_size).cumsum() + 102,
        'low': np.random.randn(data_size).cumsum() + 98,
        'close': np.random.randn(data_size).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, data_size),
    })
    df.index = pd.date_range(start='2023-01-01', periods=data_size, freq='1H')

    engine = BacktestEngine(strategy_type="technical", initial_capital=Decimal("10000"))

    start_time = time.time()
    results = engine.run_backtest(df, "BTC/USDT")
    elapsed_time = time.time() - start_time

    assert elapsed_time < 10.0, f"Backtesting took too long: {elapsed_time}s"
    assert "total_trades" in results
    assert "roi" in results


@pytest.mark.asyncio
async def test_concurrent_api_requests(client: AsyncClient, test_user):
    """Test API performance under concurrent load"""
    headers = {"Authorization": f"Bearer {test_user['token']}"}

    async def make_request():
        return await client.get("/api/v1/bots/", headers=headers)

    # Make 50 concurrent requests
    start_time = time.time()
    tasks = [make_request() for _ in range(50)]
    responses = await asyncio.gather(*tasks)
    elapsed_time = time.time() - start_time

    # All requests should succeed
    assert all(r.status_code == 200 for r in responses)

    # Should complete in reasonable time
    assert elapsed_time < 5.0, f"50 concurrent requests took {elapsed_time}s"

    # Average response time
    avg_time = elapsed_time / 50
    assert avg_time < 0.2, f"Average response time: {avg_time}s"


@pytest.mark.asyncio
async def test_database_query_performance(db_session):
    """Test database query performance"""
    from src.models.trading import TradingBot
    from sqlalchemy import select

    # Create test bots
    for i in range(100):
        bot = TradingBot(
            owner_id=1,
            name=f"Test Bot {i}",
            exchange="binance",
            trading_pair="BTC/USDT",
            initial_capital=Decimal("10000"),
            current_capital=Decimal("10000"),
        )
        db_session.add(bot)
    await db_session.commit()

    # Test query performance
    start_time = time.time()
    result = await db_session.execute(select(TradingBot))
    bots = result.scalars().all()
    elapsed_time = time.time() - start_time

    assert len(bots) >= 100
    assert elapsed_time < 0.5, f"Query took too long: {elapsed_time}s"


def test_memory_usage():
    """Test memory usage of AI model"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss / 1024 / 1024  # MB

    # Create AI model
    strategy = AITradingStrategy(model_type="lstm", sequence_length=60)
    strategy.initialize_model(input_size=16)

    # Generate test data
    df = pd.DataFrame({
        'close': np.random.randn(1000).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 1000),
        'rsi': np.random.rand(1000) * 100,
        'macd': np.random.randn(1000),
        'macd_signal': np.random.randn(1000),
        'bb_upper': np.random.randn(1000).cumsum() + 105,
        'bb_middle': np.random.randn(1000).cumsum() + 100,
        'bb_lower': np.random.randn(1000).cumsum() + 95,
        'sma_20': np.random.randn(1000).cumsum() + 100,
        'sma_50': np.random.randn(1000).cumsum() + 100,
        'ema_12': np.random.randn(1000).cumsum() + 100,
        'ema_26': np.random.randn(1000).cumsum() + 100,
        'stoch_k': np.random.rand(1000) * 100,
        'stoch_d': np.random.rand(1000) * 100,
        'atr': np.random.rand(1000) * 10,
        'adx': np.random.rand(1000) * 100,
    })

    # Make predictions
    for _ in range(10):
        strategy.predict(df)

    final_memory = process.memory_info().rss / 1024 / 1024  # MB
    memory_increase = final_memory - initial_memory

    # Memory increase should be reasonable (< 500MB)
    assert memory_increase < 500, f"Memory increased by {memory_increase}MB"


@pytest.mark.asyncio
async def test_websocket_connection_performance(client: AsyncClient):
    """Test WebSocket connection performance"""
    from fastapi.testclient import TestClient
    from src.main import app

    # Use sync client for WebSocket
    with TestClient(app) as test_client:
        start_time = time.time()

        with test_client.websocket_connect("/ws/test-client") as websocket:
            # Send messages
            for i in range(100):
                websocket.send_text(f"test message {i}")
                data = websocket.receive_json()
                assert "message" in data

        elapsed_time = time.time() - start_time

        # Should handle 100 messages quickly
        assert elapsed_time < 2.0, f"WebSocket communication took {elapsed_time}s"
