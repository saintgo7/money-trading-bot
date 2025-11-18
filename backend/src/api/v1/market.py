from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from pydantic import BaseModel
from decimal import Decimal
from datetime import datetime

from ...exchanges.binance_exchange import BinanceExchange
from ...exchanges.upbit_exchange import UpbitExchange
from ...core.config import settings

router = APIRouter()


class TickerResponse(BaseModel):
    symbol: str
    last: Decimal
    bid: Decimal
    ask: Decimal
    high: Decimal
    low: Decimal
    volume: Decimal
    timestamp: datetime


class CandleResponse(BaseModel):
    timestamp: datetime
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal


class OrderBookLevel(BaseModel):
    price: Decimal
    quantity: Decimal


class OrderBookResponse(BaseModel):
    bids: List[OrderBookLevel]
    asks: List[OrderBookLevel]
    timestamp: datetime


def get_exchange(exchange_name: str):
    """Get exchange instance"""
    if exchange_name.lower() == "binance":
        return BinanceExchange(
            api_key=settings.BINANCE_API_KEY,
            api_secret=settings.BINANCE_API_SECRET,
            testnet=settings.BINANCE_TESTNET,
        )
    elif exchange_name.lower() == "upbit":
        return UpbitExchange(
            access_key=settings.UPBIT_ACCESS_KEY,
            secret_key=settings.UPBIT_SECRET_KEY,
            testnet=False,
        )
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported exchange: {exchange_name}")


@router.get("/ticker/{exchange}/{symbol}", response_model=TickerResponse)
async def get_ticker(exchange: str, symbol: str):
    """Get current ticker for a symbol"""
    try:
        ex = get_exchange(exchange)
        await ex.connect()
        ticker = await ex.get_ticker(symbol)
        await ex.disconnect()
        return ticker
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/candles/{exchange}/{symbol}", response_model=List[CandleResponse])
async def get_candles(
    exchange: str,
    symbol: str,
    timeframe: str = Query("1h", description="Timeframe (1m, 5m, 15m, 1h, 4h, 1d)"),
    limit: int = Query(100, ge=1, le=1000, description="Number of candles"),
):
    """Get OHLCV candlestick data"""
    try:
        ex = get_exchange(exchange)
        await ex.connect()
        candles = await ex.get_ohlcv(symbol=symbol, timeframe=timeframe, limit=limit)
        await ex.disconnect()
        return candles
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/orderbook/{exchange}/{symbol}", response_model=OrderBookResponse)
async def get_orderbook(
    exchange: str,
    symbol: str,
    limit: int = Query(20, ge=1, le=100, description="Depth limit"),
):
    """Get order book (market depth)"""
    try:
        ex = get_exchange(exchange)
        await ex.connect()
        orderbook = await ex.get_orderbook(symbol=symbol, limit=limit)
        await ex.disconnect()
        return orderbook
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/exchanges")
async def list_exchanges():
    """List supported exchanges"""
    return {
        "exchanges": [
            {
                "name": "binance",
                "display_name": "Binance",
                "supported": True,
                "testnet": settings.BINANCE_TESTNET,
            },
            {
                "name": "upbit",
                "display_name": "Upbit",
                "supported": True,
                "testnet": False,
            },
        ]
    }


@router.get("/trading-pairs/{exchange}")
async def get_trading_pairs(exchange: str):
    """Get available trading pairs for an exchange"""
    try:
        ex = get_exchange(exchange)
        await ex.connect()

        # For Binance, we can get markets
        if hasattr(ex, "exchange") and hasattr(ex.exchange, "load_markets"):
            markets = await ex.exchange.load_markets()
            pairs = list(markets.keys())[:100]  # Limit to first 100
        else:
            # Default popular pairs for Upbit
            pairs = ["BTC/KRW", "ETH/KRW", "XRP/KRW", "ADA/KRW", "DOGE/KRW"]

        await ex.disconnect()
        return {"exchange": exchange, "pairs": pairs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
