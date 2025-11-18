from abc import ABC, abstractmethod
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from enum import Enum


class OrderSide(str, Enum):
    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    MARKET = "market"
    LIMIT = "limit"
    STOP_LOSS = "stop_loss"
    TAKE_PROFIT = "take_profit"


class OrderStatus(str, Enum):
    PENDING = "pending"
    OPEN = "open"
    FILLED = "filled"
    PARTIALLY_FILLED = "partially_filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


class BaseExchange(ABC):
    """Base exchange abstract class for all trading platforms"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet
        self.exchange_name = self.__class__.__name__

    @abstractmethod
    async def connect(self) -> bool:
        """Initialize connection to exchange"""
        pass

    @abstractmethod
    async def disconnect(self) -> bool:
        """Close connection to exchange"""
        pass

    @abstractmethod
    async def get_balance(self) -> Dict[str, Decimal]:
        """
        Get account balance

        Returns:
            Dict with currency as key and balance as value
            Example: {"BTC": Decimal("0.5"), "USDT": Decimal("10000")}
        """
        pass

    @abstractmethod
    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> Dict:
        """
        Place an order

        Args:
            symbol: Trading pair (e.g., "BTC/USDT")
            side: Buy or Sell
            order_type: Market, Limit, Stop Loss, etc.
            quantity: Order quantity
            price: Limit price (required for limit orders)
            stop_price: Stop price (required for stop orders)

        Returns:
            Order details including order_id, status, filled quantity, etc.
        """
        pass

    @abstractmethod
    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order"""
        pass

    @abstractmethod
    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get status of a specific order"""
        pass

    @abstractmethod
    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        pass

    @abstractmethod
    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker information

        Returns:
            Dict with current price, 24h high/low, volume, etc.
        """
        pass

    @abstractmethod
    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str,
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict]:
        """
        Get OHLCV (candlestick) data

        Args:
            symbol: Trading pair
            timeframe: Candle interval (1m, 5m, 15m, 1h, 4h, 1d, etc.)
            limit: Number of candles to fetch
            since: Start time

        Returns:
            List of candles with timestamp, open, high, low, close, volume
        """
        pass

    @abstractmethod
    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book (market depth)

        Returns:
            Dict with bids and asks
        """
        pass

    @abstractmethod
    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades from the market"""
        pass

    async def get_trading_fees(self, symbol: str) -> Dict[str, Decimal]:
        """
        Get trading fees for a symbol

        Returns:
            Dict with maker and taker fees
        """
        return {"maker": Decimal("0.001"), "taker": Decimal("0.001")}

    def validate_symbol(self, symbol: str) -> bool:
        """Validate trading pair symbol format"""
        return "/" in symbol

    def format_price(self, price: Decimal, precision: int = 8) -> Decimal:
        """Format price to exchange precision"""
        return Decimal(str(round(float(price), precision)))

    def format_quantity(self, quantity: Decimal, precision: int = 8) -> Decimal:
        """Format quantity to exchange precision"""
        return Decimal(str(round(float(quantity), precision)))
