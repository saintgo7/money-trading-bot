"""
Optimization utilities for the trading bot platform
"""
import functools
import time
from typing import Callable, Any
import redis.asyncio as redis
import pickle
from loguru import logger

from ..core.config import settings


class CacheManager:
    """Redis cache manager for optimization"""

    def __init__(self):
        self.redis_client = None

    async def connect(self):
        """Connect to Redis"""
        if not self.redis_client:
            self.redis_client = await redis.from_url(settings.REDIS_URL)

    async def disconnect(self):
        """Disconnect from Redis"""
        if self.redis_client:
            await self.redis_client.close()

    async def get(self, key: str) -> Any:
        """Get value from cache"""
        if not self.redis_client:
            await self.connect()

        value = await self.redis_client.get(key)
        if value:
            return pickle.loads(value)
        return None

    async def set(self, key: str, value: Any, expire: int = 300):
        """Set value in cache with expiration"""
        if not self.redis_client:
            await self.connect()

        await self.redis_client.set(key, pickle.dumps(value), ex=expire)

    async def delete(self, key: str):
        """Delete key from cache"""
        if not self.redis_client:
            await self.connect()

        await self.redis_client.delete(key)

    async def clear_pattern(self, pattern: str):
        """Clear all keys matching pattern"""
        if not self.redis_client:
            await self.connect()

        keys = await self.redis_client.keys(pattern)
        if keys:
            await self.redis_client.delete(*keys)


# Global cache manager
cache_manager = CacheManager()


def async_cache(expire: int = 300, key_prefix: str = ""):
    """
    Decorator for caching async function results

    Args:
        expire: Cache expiration in seconds
        key_prefix: Prefix for cache key
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{str(args)}:{str(kwargs)}"

            # Try to get from cache
            cached_value = await cache_manager.get(cache_key)
            if cached_value is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_value

            # Execute function
            result = await func(*args, **kwargs)

            # Store in cache
            await cache_manager.set(cache_key, result, expire)
            logger.debug(f"Cached result for {cache_key}")

            return result

        return wrapper
    return decorator


def timing_decorator(func: Callable):
    """Decorator to measure function execution time"""
    @functools.wraps(func)
    async def async_wrapper(*args, **kwargs):
        start_time = time.time()
        result = await func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.info(f"{func.__name__} took {elapsed_time:.4f}s")
        return result

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        logger.info(f"{func.__name__} took {elapsed_time:.4f}s")
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


class QueryOptimizer:
    """Database query optimization utilities"""

    @staticmethod
    def batch_queries(queries, batch_size=100):
        """Batch multiple queries together"""
        for i in range(0, len(queries), batch_size):
            yield queries[i:i + batch_size]

    @staticmethod
    async def prefetch_related(session, model, relationship, ids):
        """Prefetch related objects to avoid N+1 queries"""
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        result = await session.execute(
            select(model)
            .where(model.id.in_(ids))
            .options(selectinload(relationship))
        )
        return result.scalars().all()


class ConnectionPool:
    """Manage connection pooling for better performance"""

    def __init__(self, min_size=5, max_size=20):
        self.min_size = min_size
        self.max_size = max_size
        self.pool = []

    async def get_connection(self):
        """Get a connection from pool"""
        # Implementation would depend on the specific database
        pass

    async def return_connection(self, conn):
        """Return connection to pool"""
        pass


import asyncio


def rate_limit(calls_per_second: int = 10):
    """
    Rate limiting decorator

    Args:
        calls_per_second: Maximum number of calls per second
    """
    min_interval = 1.0 / calls_per_second
    last_called = [0.0]

    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed

            if left_to_wait > 0:
                await asyncio.sleep(left_to_wait)

            last_called[0] = time.time()
            return await func(*args, **kwargs)

        return wrapper
    return decorator


class DataFrameOptimizer:
    """Optimize pandas DataFrame operations"""

    @staticmethod
    def reduce_memory_usage(df):
        """Reduce DataFrame memory usage by downcasting types"""
        import pandas as pd
        import numpy as np

        start_mem = df.memory_usage().sum() / 1024**2
        logger.info(f"Memory usage: {start_mem:.2f} MB")

        for col in df.columns:
            col_type = df[col].dtype

            if col_type != object:
                c_min = df[col].min()
                c_max = df[col].max()

                if str(col_type)[:3] == "int":
                    if c_min > np.iinfo(np.int8).min and c_max < np.iinfo(np.int8).max:
                        df[col] = df[col].astype(np.int8)
                    elif c_min > np.iinfo(np.int16).min and c_max < np.iinfo(np.int16).max:
                        df[col] = df[col].astype(np.int16)
                    elif c_min > np.iinfo(np.int32).min and c_max < np.iinfo(np.int32).max:
                        df[col] = df[col].astype(np.int32)
                else:
                    if (
                        c_min > np.finfo(np.float16).min
                        and c_max < np.finfo(np.float16).max
                    ):
                        df[col] = df[col].astype(np.float32)

        end_mem = df.memory_usage().sum() / 1024**2
        logger.info(f"Memory usage after optimization: {end_mem:.2f} MB")
        logger.info(f"Decreased by {100 * (start_mem - end_mem) / start_mem:.1f}%")

        return df


class ModelOptimizer:
    """Optimize AI model inference"""

    @staticmethod
    def quantize_model(model):
        """Quantize model for faster inference"""
        import torch

        # Dynamic quantization
        quantized_model = torch.quantization.quantize_dynamic(
            model, {torch.nn.Linear}, dtype=torch.qint8
        )
        return quantized_model

    @staticmethod
    def enable_amp():
        """Enable Automatic Mixed Precision for faster training"""
        import torch

        scaler = torch.cuda.amp.GradScaler()
        return scaler
