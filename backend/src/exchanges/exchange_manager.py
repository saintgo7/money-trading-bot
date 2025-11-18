"""
Exchange Manager
Centralized management for multiple exchange connections
"""

from typing import Dict, List, Optional, Type
from enum import Enum
import logging

from .base import BaseExchange
from .binance_exchange import BinanceExchange
from .upbit_exchange import UpbitExchange
from .coinbase_exchange import CoinbaseExchange
from .kraken_exchange import KrakenExchange
from .kis_exchange import KISExchange

logger = logging.getLogger(__name__)


class ExchangeType(Enum):
    """Supported exchange types"""
    BINANCE = "binance"
    UPBIT = "upbit"
    COINBASE = "coinbase"
    KRAKEN = "kraken"
    KIS = "kis"  # Korea Investment & Securities


class ExchangeManager:
    """
    Manage multiple exchange connections

    Features:
    - Initialize and manage multiple exchange connections
    - Route orders to appropriate exchanges
    - Aggregate market data across exchanges
    - Handle exchange-specific configurations
    """

    EXCHANGE_CLASSES: Dict[ExchangeType, Type[BaseExchange]] = {
        ExchangeType.BINANCE: BinanceExchange,
        ExchangeType.UPBIT: UpbitExchange,
        ExchangeType.COINBASE: CoinbaseExchange,
        ExchangeType.KRAKEN: KrakenExchange,
        ExchangeType.KIS: KISExchange,
    }

    def __init__(self):
        self.exchanges: Dict[str, BaseExchange] = {}
        self.exchange_configs: Dict[str, Dict] = {}

    async def add_exchange(
        self,
        name: str,
        exchange_type: ExchangeType,
        credentials: Dict,
        testnet: bool = False
    ) -> bool:
        """
        Add and connect to an exchange

        Args:
            name: Unique name for this exchange connection
            exchange_type: Type of exchange
            credentials: API credentials
            testnet: Use testnet/sandbox

        Returns:
            True if successfully connected
        """
        try:
            # Get exchange class
            exchange_class = self.EXCHANGE_CLASSES.get(exchange_type)
            if not exchange_class:
                logger.error(f"Unknown exchange type: {exchange_type}")
                return False

            # Initialize exchange
            if exchange_type == ExchangeType.BINANCE:
                exchange = exchange_class(
                    api_key=credentials['api_key'],
                    api_secret=credentials['api_secret'],
                    testnet=testnet
                )
            elif exchange_type == ExchangeType.UPBIT:
                exchange = exchange_class(
                    access_key=credentials['access_key'],
                    secret_key=credentials['secret_key']
                )
            elif exchange_type == ExchangeType.COINBASE:
                exchange = exchange_class(
                    api_key=credentials['api_key'],
                    api_secret=credentials['api_secret'],
                    passphrase=credentials.get('passphrase', ''),
                    testnet=testnet
                )
            elif exchange_type == ExchangeType.KRAKEN:
                exchange = exchange_class(
                    api_key=credentials['api_key'],
                    api_secret=credentials['api_secret'],
                    testnet=testnet
                )
            elif exchange_type == ExchangeType.KIS:
                exchange = exchange_class(
                    app_key=credentials['app_key'],
                    app_secret=credentials['app_secret'],
                    testnet=testnet
                )
            else:
                logger.error(f"Exchange type {exchange_type} not implemented")
                return False

            # Connect
            connected = await exchange.connect()
            if connected:
                self.exchanges[name] = exchange
                self.exchange_configs[name] = {
                    'type': exchange_type,
                    'testnet': testnet
                }
                logger.info(f"Added exchange: {name} ({exchange_type.value})")
                return True
            else:
                logger.error(f"Failed to connect to {name}")
                return False

        except Exception as e:
            logger.error(f"Error adding exchange {name}: {e}")
            return False

    async def remove_exchange(self, name: str) -> bool:
        """
        Remove and disconnect exchange

        Args:
            name: Exchange name

        Returns:
            True if successfully removed
        """
        if name in self.exchanges:
            try:
                await self.exchanges[name].disconnect()
                del self.exchanges[name]
                del self.exchange_configs[name]
                logger.info(f"Removed exchange: {name}")
                return True
            except Exception as e:
                logger.error(f"Error removing exchange {name}: {e}")
                return False
        return False

    def get_exchange(self, name: str) -> Optional[BaseExchange]:
        """Get exchange by name"""
        return self.exchanges.get(name)

    def list_exchanges(self) -> List[str]:
        """List all connected exchanges"""
        return list(self.exchanges.keys())

    async def get_all_balances(self) -> Dict[str, Dict]:
        """
        Get balances from all exchanges

        Returns:
            Dict of {exchange_name: {currency: balance}}
        """
        all_balances = {}

        for name, exchange in self.exchanges.items():
            try:
                balances = await exchange.get_balance()
                all_balances[name] = balances
            except Exception as e:
                logger.error(f"Error fetching balance from {name}: {e}")
                all_balances[name] = {}

        return all_balances

    async def get_best_price(
        self,
        symbol: str,
        exchanges: Optional[List[str]] = None
    ) -> Dict:
        """
        Get best bid/ask prices across exchanges

        Args:
            symbol: Trading pair
            exchanges: Optional list of exchange names to check

        Returns:
            Dict with best prices and sources
        """
        if exchanges is None:
            exchanges = list(self.exchanges.keys())

        best_bid = None
        best_bid_exchange = None
        best_ask = None
        best_ask_exchange = None

        for name in exchanges:
            if name not in self.exchanges:
                continue

            try:
                ticker = await self.exchanges[name].get_ticker(symbol)

                if ticker['bid'] and (best_bid is None or ticker['bid'] > best_bid):
                    best_bid = ticker['bid']
                    best_bid_exchange = name

                if ticker['ask'] and (best_ask is None or ticker['ask'] < best_ask):
                    best_ask = ticker['ask']
                    best_ask_exchange = name

            except Exception as e:
                logger.warning(f"Error fetching ticker from {name}: {e}")

        return {
            'symbol': symbol,
            'best_bid': best_bid,
            'best_bid_exchange': best_bid_exchange,
            'best_ask': best_ask,
            'best_ask_exchange': best_ask_exchange,
            'spread': (best_ask - best_bid) if (best_bid and best_ask) else None
        }

    async def check_arbitrage_opportunity(
        self,
        symbol: str,
        min_profit_pct: float = 0.5
    ) -> Optional[Dict]:
        """
        Check for arbitrage opportunities

        Args:
            symbol: Trading pair
            min_profit_pct: Minimum profit percentage required

        Returns:
            Arbitrage opportunity details or None
        """
        prices = await self.get_best_price(symbol)

        if not (prices['best_bid'] and prices['best_ask']):
            return None

        # Calculate potential profit
        buy_price = prices['best_ask']
        sell_price = prices['best_bid']

        # Need to buy low on one exchange and sell high on another
        # Best case: buy at best_ask on one exchange, sell at best_bid on another
        # But we need to check if best_ask exchange != best_bid exchange

        if prices['best_ask_exchange'] == prices['best_bid_exchange']:
            return None  # Same exchange, no arbitrage

        profit_pct = ((sell_price - buy_price) / buy_price) * 100

        if profit_pct >= min_profit_pct:
            return {
                'symbol': symbol,
                'buy_exchange': prices['best_ask_exchange'],
                'buy_price': buy_price,
                'sell_exchange': prices['best_bid_exchange'],
                'sell_price': sell_price,
                'profit_pct': profit_pct,
                'spread': prices['spread']
            }

        return None

    async def get_exchange_status(self) -> Dict:
        """
        Get status of all exchanges

        Returns:
            Status information for each exchange
        """
        status = {}

        for name, exchange in self.exchanges.items():
            try:
                # Try to get balance as health check
                await exchange.get_balance()
                connected = True
                error = None
            except Exception as e:
                connected = False
                error = str(e)

            status[name] = {
                'type': self.exchange_configs[name]['type'].value,
                'connected': connected,
                'testnet': self.exchange_configs[name]['testnet'],
                'error': error
            }

        return status

    async def execute_smart_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        prefer_best_price: bool = True
    ) -> Dict:
        """
        Execute order on exchange with best price

        Args:
            symbol: Trading pair
            side: 'buy' or 'sell'
            quantity: Order quantity
            prefer_best_price: Route to exchange with best price

        Returns:
            Order execution details
        """
        from .base import OrderSide, OrderType
        from decimal import Decimal

        order_side = OrderSide.BUY if side.lower() == 'buy' else OrderSide.SELL

        if prefer_best_price:
            # Find exchange with best price
            prices = await self.get_best_price(symbol)

            if side.lower() == 'buy':
                # Buy at lowest ask
                target_exchange = prices['best_ask_exchange']
            else:
                # Sell at highest bid
                target_exchange = prices['best_bid_exchange']

            if target_exchange and target_exchange in self.exchanges:
                exchange = self.exchanges[target_exchange]

                # Place market order
                order = await exchange.place_order(
                    symbol=symbol,
                    side=order_side,
                    order_type=OrderType.MARKET,
                    quantity=Decimal(str(quantity))
                )

                return {
                    'exchange': target_exchange,
                    'order': order,
                    'strategy': 'best_price'
                }

        # Fallback: use first available exchange
        if self.exchanges:
            first_exchange_name = list(self.exchanges.keys())[0]
            exchange = self.exchanges[first_exchange_name]

            order = await exchange.place_order(
                symbol=symbol,
                side=order_side,
                order_type=OrderType.MARKET,
                quantity=Decimal(str(quantity))
            )

            return {
                'exchange': first_exchange_name,
                'order': order,
                'strategy': 'default'
            }

        raise ValueError("No exchanges available")

    async def disconnect_all(self):
        """Disconnect from all exchanges"""
        for name in list(self.exchanges.keys()):
            await self.remove_exchange(name)

        logger.info("Disconnected from all exchanges")


# Convenience functions

def get_supported_exchanges() -> List[str]:
    """Get list of supported exchange types"""
    return [e.value for e in ExchangeType]


def get_exchange_info(exchange_type: str) -> Dict:
    """
    Get information about an exchange

    Args:
        exchange_type: Exchange type string

    Returns:
        Exchange information
    """
    exchange_info = {
        'binance': {
            'name': 'Binance',
            'description': 'Largest cryptocurrency exchange by volume',
            'features': ['spot', 'futures', 'margin', 'staking'],
            'fees': {'maker': 0.001, 'taker': 0.001},
            'supported_countries': 'Global (with restrictions)',
            'testnet': True,
            'credentials': ['api_key', 'api_secret']
        },
        'upbit': {
            'name': 'Upbit',
            'description': 'Leading South Korean cryptocurrency exchange',
            'features': ['spot'],
            'fees': {'maker': 0.0005, 'taker': 0.0005},
            'supported_countries': 'South Korea',
            'testnet': False,
            'credentials': ['access_key', 'secret_key']
        },
        'coinbase': {
            'name': 'Coinbase Pro',
            'description': 'Major US-based cryptocurrency exchange',
            'features': ['spot'],
            'fees': {'maker': 0.005, 'taker': 0.006},
            'supported_countries': 'US and many others',
            'testnet': True,
            'credentials': ['api_key', 'api_secret', 'passphrase']
        },
        'kraken': {
            'name': 'Kraken',
            'description': 'Established US-based exchange with global reach',
            'features': ['spot', 'margin', 'futures'],
            'fees': {'maker': 0.0026, 'taker': 0.0026},
            'supported_countries': 'Global (US, EU, Canada, Japan)',
            'testnet': False,
            'credentials': ['api_key', 'api_secret']
        },
        'kis': {
            'name': 'Korea Investment & Securities',
            'description': 'Korean stock and securities trading',
            'features': ['stocks'],
            'fees': {'trading': 0.0015},
            'supported_countries': 'South Korea',
            'testnet': True,
            'credentials': ['app_key', 'app_secret']
        }
    }

    return exchange_info.get(exchange_type.lower(), {})
