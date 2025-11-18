from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import ccxt.async_support as ccxt
from loguru import logger

from .base import BaseExchange, OrderSide, OrderType, OrderStatus


class BinanceExchange(BaseExchange):
    """Binance exchange implementation"""

    def __init__(self, api_key: str, api_secret: str, testnet: bool = False):
        super().__init__(api_key, api_secret, testnet)
        self.exchange = None
        self._setup_exchange()

    def _setup_exchange(self):
        """Initialize Binance exchange client"""
        options = {
            "apiKey": self.api_key,
            "secret": self.api_secret,
            "enableRateLimit": True,
            "options": {
                "defaultType": "future" if self.testnet else "spot",
            },
        }

        if self.testnet:
            self.exchange = ccxt.binance({
                **options,
                "urls": {
                    "api": {
                        "public": "https://testnet.binance.vision/api/v3",
                        "private": "https://testnet.binance.vision/api/v3",
                    }
                },
            })
        else:
            self.exchange = ccxt.binance(options)

    async def connect(self) -> bool:
        """Test connection to Binance"""
        try:
            await self.exchange.load_markets()
            logger.info(f"Connected to Binance (testnet={self.testnet})")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Binance: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close Binance connection"""
        try:
            await self.exchange.close()
            logger.info("Disconnected from Binance")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Binance: {e}")
            return False

    async def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        try:
            balance = await self.exchange.fetch_balance()
            return {
                currency: Decimal(str(amount["free"]))
                for currency, amount in balance["total"].items()
                if amount["free"] > 0
            }
        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        stop_price: Optional[Decimal] = None,
    ) -> Dict:
        """Place an order on Binance"""
        try:
            params = {}

            # Convert enum to string
            side_str = side.value
            type_str = order_type.value

            # Handle different order types
            if order_type == OrderType.MARKET:
                order = await self.exchange.create_market_order(
                    symbol, side_str, float(quantity)
                )
            elif order_type == OrderType.LIMIT:
                if price is None:
                    raise ValueError("Price required for limit orders")
                order = await self.exchange.create_limit_order(
                    symbol, side_str, float(quantity), float(price)
                )
            elif order_type == OrderType.STOP_LOSS:
                if stop_price is None:
                    raise ValueError("Stop price required for stop loss orders")
                params["stopPrice"] = float(stop_price)
                order = await self.exchange.create_order(
                    symbol, "STOP_LOSS_LIMIT", side_str, float(quantity), float(price), params
                )
            elif order_type == OrderType.TAKE_PROFIT:
                if stop_price is None:
                    raise ValueError("Stop price required for take profit orders")
                params["stopPrice"] = float(stop_price)
                order = await self.exchange.create_order(
                    symbol, "TAKE_PROFIT_LIMIT", side_str, float(quantity), float(price), params
                )

            logger.info(f"Order placed: {order}")
            return {
                "order_id": order["id"],
                "symbol": order["symbol"],
                "side": order["side"],
                "type": order["type"],
                "quantity": Decimal(str(order["amount"])),
                "price": Decimal(str(order.get("price", 0))),
                "status": self._map_order_status(order["status"]),
                "filled": Decimal(str(order.get("filled", 0))),
                "remaining": Decimal(str(order.get("remaining", 0))),
                "timestamp": datetime.fromtimestamp(order["timestamp"] / 1000),
            }
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order"""
        try:
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get order status"""
        try:
            order = await self.exchange.fetch_order(order_id, symbol)
            return {
                "order_id": order["id"],
                "status": self._map_order_status(order["status"]),
                "filled": Decimal(str(order.get("filled", 0))),
                "remaining": Decimal(str(order.get("remaining", 0))),
            }
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            raise

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            orders = await self.exchange.fetch_open_orders(symbol)
            return [
                {
                    "order_id": order["id"],
                    "symbol": order["symbol"],
                    "side": order["side"],
                    "type": order["type"],
                    "quantity": Decimal(str(order["amount"])),
                    "price": Decimal(str(order.get("price", 0))),
                    "filled": Decimal(str(order.get("filled", 0))),
                    "remaining": Decimal(str(order.get("remaining", 0))),
                    "timestamp": datetime.fromtimestamp(order["timestamp"] / 1000),
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker"""
        try:
            ticker = await self.exchange.fetch_ticker(symbol)
            return {
                "symbol": ticker["symbol"],
                "last": Decimal(str(ticker["last"])),
                "bid": Decimal(str(ticker["bid"])),
                "ask": Decimal(str(ticker["ask"])),
                "high": Decimal(str(ticker["high"])),
                "low": Decimal(str(ticker["low"])),
                "volume": Decimal(str(ticker["baseVolume"])),
                "timestamp": datetime.fromtimestamp(ticker["timestamp"] / 1000),
            }
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            raise

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1m",
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get OHLCV candlestick data"""
        try:
            since_ms = int(since.timestamp() * 1000) if since else None
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, since_ms, limit)

            return [
                {
                    "timestamp": datetime.fromtimestamp(candle[0] / 1000),
                    "open": Decimal(str(candle[1])),
                    "high": Decimal(str(candle[2])),
                    "low": Decimal(str(candle[3])),
                    "close": Decimal(str(candle[4])),
                    "volume": Decimal(str(candle[5])),
                }
                for candle in ohlcv
            ]
        except Exception as e:
            logger.error(f"Error fetching OHLCV: {e}")
            raise

    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book"""
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit)
            return {
                "bids": [
                    {"price": Decimal(str(bid[0])), "quantity": Decimal(str(bid[1]))}
                    for bid in orderbook["bids"]
                ],
                "asks": [
                    {"price": Decimal(str(ask[0])), "quantity": Decimal(str(ask[1]))}
                    for ask in orderbook["asks"]
                ],
                "timestamp": datetime.fromtimestamp(orderbook["timestamp"] / 1000),
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook: {e}")
            raise

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades"""
        try:
            trades = await self.exchange.fetch_trades(symbol, limit=limit)
            return [
                {
                    "id": trade["id"],
                    "price": Decimal(str(trade["price"])),
                    "quantity": Decimal(str(trade["amount"])),
                    "side": trade["side"],
                    "timestamp": datetime.fromtimestamp(trade["timestamp"] / 1000),
                }
                for trade in trades
            ]
        except Exception as e:
            logger.error(f"Error fetching recent trades: {e}")
            raise

    async def get_trading_fees(self, symbol: str) -> Dict[str, Decimal]:
        """Get trading fees"""
        try:
            fees = await self.exchange.fetch_trading_fees()
            if symbol in fees:
                return {
                    "maker": Decimal(str(fees[symbol]["maker"])),
                    "taker": Decimal(str(fees[symbol]["taker"])),
                }
            return {"maker": Decimal("0.001"), "taker": Decimal("0.001")}
        except Exception as e:
            logger.error(f"Error fetching trading fees: {e}")
            return {"maker": Decimal("0.001"), "taker": Decimal("0.001")}

    def _map_order_status(self, status: str) -> OrderStatus:
        """Map exchange order status to internal status"""
        status_map = {
            "open": OrderStatus.OPEN,
            "closed": OrderStatus.FILLED,
            "canceled": OrderStatus.CANCELLED,
            "cancelled": OrderStatus.CANCELLED,
            "rejected": OrderStatus.REJECTED,
        }
        return status_map.get(status.lower(), OrderStatus.PENDING)
