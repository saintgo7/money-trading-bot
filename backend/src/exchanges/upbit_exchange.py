from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import pyupbit
import asyncio
from loguru import logger

from .base import BaseExchange, OrderSide, OrderType, OrderStatus


class UpbitExchange(BaseExchange):
    """Upbit (Korean cryptocurrency exchange) implementation"""

    def __init__(self, access_key: str, secret_key: str, testnet: bool = False):
        super().__init__(access_key, secret_key, testnet)
        self.upbit = None
        self._setup_exchange()

    def _setup_exchange(self):
        """Initialize Upbit exchange client"""
        self.upbit = pyupbit.Upbit(self.api_key, self.api_secret)

    async def connect(self) -> bool:
        """Test connection to Upbit"""
        try:
            # Run synchronous pyupbit call in executor
            loop = asyncio.get_event_loop()
            balance = await loop.run_in_executor(None, self.upbit.get_balances)
            if balance is not None:
                logger.info("Connected to Upbit")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to connect to Upbit: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close Upbit connection"""
        try:
            logger.info("Disconnected from Upbit")
            return True
        except Exception as e:
            logger.error(f"Error disconnecting from Upbit: {e}")
            return False

    async def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        try:
            loop = asyncio.get_event_loop()
            balances = await loop.run_in_executor(None, self.upbit.get_balances)

            if balances is None:
                return {}

            return {
                balance["currency"]: Decimal(str(balance["balance"]))
                for balance in balances
                if float(balance["balance"]) > 0
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
        """Place an order on Upbit"""
        try:
            loop = asyncio.get_event_loop()

            # Convert symbol format (BTC/KRW -> KRW-BTC)
            upbit_symbol = self._convert_symbol_to_upbit(symbol)

            if side == OrderSide.BUY:
                if order_type == OrderType.MARKET:
                    # Market buy with KRW amount
                    order = await loop.run_in_executor(
                        None,
                        lambda: self.upbit.buy_market_order(upbit_symbol, float(quantity)),
                    )
                else:
                    # Limit buy
                    order = await loop.run_in_executor(
                        None,
                        lambda: self.upbit.buy_limit_order(
                            upbit_symbol, float(price), float(quantity)
                        ),
                    )
            else:  # SELL
                if order_type == OrderType.MARKET:
                    order = await loop.run_in_executor(
                        None,
                        lambda: self.upbit.sell_market_order(upbit_symbol, float(quantity)),
                    )
                else:
                    order = await loop.run_in_executor(
                        None,
                        lambda: self.upbit.sell_limit_order(
                            upbit_symbol, float(price), float(quantity)
                        ),
                    )

            if order is None:
                raise Exception("Failed to place order")

            logger.info(f"Order placed on Upbit: {order}")
            return {
                "order_id": order["uuid"],
                "symbol": symbol,
                "side": side.value,
                "type": order_type.value,
                "quantity": Decimal(str(order.get("volume", quantity))),
                "price": Decimal(str(order.get("price", price or 0))),
                "status": self._map_order_status(order["state"]),
                "filled": Decimal("0"),
                "remaining": Decimal(str(order.get("remaining_volume", quantity))),
                "timestamp": datetime.fromisoformat(order["created_at"].replace("Z", "+00:00")),
            }
        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order"""
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.upbit.cancel_order(order_id))
            if result:
                logger.info(f"Order cancelled: {order_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get order status"""
        try:
            loop = asyncio.get_event_loop()
            order = await loop.run_in_executor(None, lambda: self.upbit.get_order(order_id))

            if order is None:
                raise Exception(f"Order not found: {order_id}")

            return {
                "order_id": order["uuid"],
                "status": self._map_order_status(order["state"]),
                "filled": Decimal(str(order.get("executed_volume", 0))),
                "remaining": Decimal(str(order.get("remaining_volume", 0))),
            }
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            raise

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        try:
            loop = asyncio.get_event_loop()

            if symbol:
                upbit_symbol = self._convert_symbol_to_upbit(symbol)
                orders = await loop.run_in_executor(
                    None, lambda: self.upbit.get_order(upbit_symbol)
                )
            else:
                orders = await loop.run_in_executor(None, self.upbit.get_order)

            if orders is None:
                return []

            # Ensure orders is a list
            if not isinstance(orders, list):
                orders = [orders]

            return [
                {
                    "order_id": order["uuid"],
                    "symbol": self._convert_symbol_from_upbit(order["market"]),
                    "side": order["side"],
                    "type": order["ord_type"],
                    "quantity": Decimal(str(order["volume"])),
                    "price": Decimal(str(order.get("price", 0))),
                    "filled": Decimal(str(order.get("executed_volume", 0))),
                    "remaining": Decimal(str(order.get("remaining_volume", 0))),
                    "timestamp": datetime.fromisoformat(
                        order["created_at"].replace("Z", "+00:00")
                    ),
                }
                for order in orders
            ]
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker"""
        try:
            upbit_symbol = self._convert_symbol_to_upbit(symbol)
            loop = asyncio.get_event_loop()
            ticker = await loop.run_in_executor(None, lambda: pyupbit.get_ticker(upbit_symbol))

            if ticker is None:
                raise Exception(f"Failed to fetch ticker for {symbol}")

            return {
                "symbol": symbol,
                "last": Decimal(str(ticker)),
                "bid": Decimal(str(ticker)),  # Upbit doesn't provide bid/ask in simple ticker
                "ask": Decimal(str(ticker)),
                "high": Decimal(str(ticker)),
                "low": Decimal(str(ticker)),
                "volume": Decimal("0"),
                "timestamp": datetime.now(),
            }
        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            raise

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "1",
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get OHLCV candlestick data"""
        try:
            upbit_symbol = self._convert_symbol_to_upbit(symbol)

            # Map timeframe to Upbit format
            interval_map = {
                "1m": "1",
                "3m": "3",
                "5m": "5",
                "15m": "15",
                "30m": "30",
                "1h": "60",
                "4h": "240",
                "1d": "day",
                "1w": "week",
            }
            upbit_interval = interval_map.get(timeframe, "1")

            loop = asyncio.get_event_loop()
            df = await loop.run_in_executor(
                None, lambda: pyupbit.get_ohlcv(upbit_symbol, interval=upbit_interval, count=limit)
            )

            if df is None or df.empty:
                return []

            return [
                {
                    "timestamp": row.name.to_pydatetime(),
                    "open": Decimal(str(row["open"])),
                    "high": Decimal(str(row["high"])),
                    "low": Decimal(str(row["low"])),
                    "close": Decimal(str(row["close"])),
                    "volume": Decimal(str(row["volume"])),
                }
                for _, row in df.iterrows()
            ]
        except Exception as e:
            logger.error(f"Error fetching OHLCV: {e}")
            raise

    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book"""
        try:
            upbit_symbol = self._convert_symbol_to_upbit(symbol)
            loop = asyncio.get_event_loop()
            orderbook = await loop.run_in_executor(
                None, lambda: pyupbit.get_orderbook(upbit_symbol)
            )

            if orderbook is None:
                raise Exception(f"Failed to fetch orderbook for {symbol}")

            orderbook = orderbook[0]  # get_orderbook returns a list

            return {
                "bids": [
                    {"price": Decimal(str(bid["price"])), "quantity": Decimal(str(bid["size"]))}
                    for bid in orderbook["orderbook_units"]
                ][:limit],
                "asks": [
                    {"price": Decimal(str(ask["price"])), "quantity": Decimal(str(ask["size"]))}
                    for ask in orderbook["orderbook_units"]
                ][:limit],
                "timestamp": datetime.fromtimestamp(orderbook["timestamp"] / 1000),
            }
        except Exception as e:
            logger.error(f"Error fetching orderbook: {e}")
            raise

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades - Not directly supported by pyupbit"""
        logger.warning("get_recent_trades not fully supported by Upbit API")
        return []

    def _convert_symbol_to_upbit(self, symbol: str) -> str:
        """Convert symbol from standard format (BTC/KRW) to Upbit format (KRW-BTC)"""
        if "/" in symbol:
            base, quote = symbol.split("/")
            return f"{quote}-{base}"
        return symbol

    def _convert_symbol_from_upbit(self, upbit_symbol: str) -> str:
        """Convert symbol from Upbit format (KRW-BTC) to standard format (BTC/KRW)"""
        if "-" in upbit_symbol:
            quote, base = upbit_symbol.split("-")
            return f"{base}/{quote}"
        return upbit_symbol

    def _map_order_status(self, status: str) -> OrderStatus:
        """Map Upbit order status to internal status"""
        status_map = {
            "wait": OrderStatus.OPEN,
            "done": OrderStatus.FILLED,
            "cancel": OrderStatus.CANCELLED,
        }
        return status_map.get(status.lower(), OrderStatus.PENDING)
