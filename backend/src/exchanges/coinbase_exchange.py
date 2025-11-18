"""
Coinbase Exchange Connector
Supports Coinbase Pro (Advanced Trade) API
"""

import ccxt
from decimal import Decimal
from typing import Dict, List, Optional
import logging
from datetime import datetime

from .base import BaseExchange, OrderSide, OrderType

logger = logging.getLogger(__name__)


class CoinbaseExchange(BaseExchange):
    """
    Coinbase exchange implementation using CCXT

    Supports:
    - Spot trading
    - Market and limit orders
    - Real-time price data
    - Account balances
    - Order management
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        passphrase: str = "",
        testnet: bool = False
    ):
        """
        Initialize Coinbase exchange

        Args:
            api_key: Coinbase API key
            api_secret: Coinbase API secret
            passphrase: Coinbase API passphrase (required for Coinbase Pro)
            testnet: Use testnet (sandbox) environment
        """
        super().__init__(api_key, api_secret)

        self.passphrase = passphrase
        self.testnet = testnet

        # Initialize CCXT exchange
        self.exchange = ccxt.coinbase({
            'apiKey': api_key,
            'secret': api_secret,
            'password': passphrase,  # Coinbase requires passphrase
            'enableRateLimit': True,
        })

        if testnet:
            # Coinbase sandbox
            self.exchange.set_sandbox_mode(True)
            logger.info("Coinbase testnet mode enabled")

        self.exchange_name = "Coinbase"

    async def connect(self) -> bool:
        """Connect and verify credentials"""
        try:
            # Test connection by fetching balance
            await self.get_balance()
            self.connected = True
            logger.info(f"Connected to {self.exchange_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to {self.exchange_name}: {e}")
            self.connected = False
            return False

    async def disconnect(self):
        """Disconnect from exchange"""
        await self.exchange.close()
        self.connected = False
        logger.info(f"Disconnected from {self.exchange_name}")

    async def get_balance(self) -> Dict[str, Decimal]:
        """
        Get account balance

        Returns:
            Dictionary of {currency: available_balance}
        """
        try:
            balance = await self.exchange.fetch_balance()

            # Extract available balances
            balances = {}
            for currency, amount in balance['free'].items():
                if amount > 0:
                    balances[currency] = Decimal(str(amount))

            logger.debug(f"Fetched balances: {balances}")
            return balances

        except Exception as e:
            logger.error(f"Error fetching balance: {e}")
            raise

    async def get_ticker(self, symbol: str) -> Dict:
        """
        Get current ticker data

        Args:
            symbol: Trading pair (e.g., 'BTC/USD', 'ETH/USD')

        Returns:
            Ticker data dictionary
        """
        try:
            ticker = await self.exchange.fetch_ticker(symbol)

            return {
                'symbol': symbol,
                'bid': Decimal(str(ticker['bid'])) if ticker['bid'] else None,
                'ask': Decimal(str(ticker['ask'])) if ticker['ask'] else None,
                'last': Decimal(str(ticker['last'])),
                'volume': Decimal(str(ticker['baseVolume'])),
                'timestamp': ticker['timestamp']
            }

        except Exception as e:
            logger.error(f"Error fetching ticker for {symbol}: {e}")
            raise

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None
    ) -> Dict:
        """
        Place an order

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            side: BUY or SELL
            order_type: MARKET or LIMIT
            quantity: Order quantity (in base currency)
            price: Limit price (required for LIMIT orders)

        Returns:
            Order information
        """
        try:
            # Validate
            if order_type == OrderType.LIMIT and price is None:
                raise ValueError("Price required for limit orders")

            # Place order
            if order_type == OrderType.MARKET:
                order = await self.exchange.create_market_order(
                    symbol,
                    side.value.lower(),
                    float(quantity)
                )
            else:  # LIMIT
                order = await self.exchange.create_limit_order(
                    symbol,
                    side.value.lower(),
                    float(quantity),
                    float(price)
                )

            logger.info(f"Order placed: {order['id']} - {side.value} {quantity} {symbol}")

            return {
                'order_id': order['id'],
                'symbol': symbol,
                'side': side.value,
                'type': order_type.value,
                'quantity': Decimal(str(order['amount'])),
                'price': Decimal(str(order['price'])) if order['price'] else None,
                'status': order['status'],
                'timestamp': order['timestamp']
            }

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """
        Cancel an order

        Args:
            order_id: Order ID to cancel
            symbol: Trading pair

        Returns:
            True if successful
        """
        try:
            await self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {order_id}")
            return True

        except Exception as e:
            logger.error(f"Error cancelling order {order_id}: {e}")
            return False

    async def get_order(self, order_id: str, symbol: str) -> Optional[Dict]:
        """
        Get order status

        Args:
            order_id: Order ID
            symbol: Trading pair

        Returns:
            Order information or None
        """
        try:
            order = await self.exchange.fetch_order(order_id, symbol)

            return {
                'order_id': order['id'],
                'symbol': order['symbol'],
                'side': order['side'].upper(),
                'type': order['type'].upper(),
                'quantity': Decimal(str(order['amount'])),
                'filled': Decimal(str(order['filled'])),
                'remaining': Decimal(str(order['remaining'])),
                'price': Decimal(str(order['price'])) if order['price'] else None,
                'average': Decimal(str(order['average'])) if order['average'] else None,
                'status': order['status'],
                'timestamp': order['timestamp']
            }

        except Exception as e:
            logger.error(f"Error fetching order {order_id}: {e}")
            return None

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """
        Get all open orders

        Args:
            symbol: Optional trading pair filter

        Returns:
            List of open orders
        """
        try:
            orders = await self.exchange.fetch_open_orders(symbol)

            return [
                {
                    'order_id': order['id'],
                    'symbol': order['symbol'],
                    'side': order['side'].upper(),
                    'type': order['type'].upper(),
                    'quantity': Decimal(str(order['amount'])),
                    'filled': Decimal(str(order['filled'])),
                    'price': Decimal(str(order['price'])) if order['price'] else None,
                    'status': order['status'],
                    'timestamp': order['timestamp']
                }
                for order in orders
            ]

        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []

    async def get_order_book(self, symbol: str, limit: int = 20) -> Dict:
        """
        Get order book

        Args:
            symbol: Trading pair
            limit: Depth limit

        Returns:
            Order book with bids and asks
        """
        try:
            orderbook = await self.exchange.fetch_order_book(symbol, limit)

            return {
                'symbol': symbol,
                'bids': [
                    {'price': Decimal(str(bid[0])), 'quantity': Decimal(str(bid[1]))}
                    for bid in orderbook['bids'][:limit]
                ],
                'asks': [
                    {'price': Decimal(str(ask[0])), 'quantity': Decimal(str(ask[1]))}
                    for ask in orderbook['asks'][:limit]
                ],
                'timestamp': orderbook['timestamp']
            }

        except Exception as e:
            logger.error(f"Error fetching order book for {symbol}: {e}")
            raise

    async def get_historical_data(
        self,
        symbol: str,
        timeframe: str = '1h',
        limit: int = 100
    ) -> List[Dict]:
        """
        Get historical OHLCV data

        Args:
            symbol: Trading pair
            timeframe: Candle timeframe (1m, 5m, 15m, 1h, 4h, 1d)
            limit: Number of candles

        Returns:
            List of OHLCV candles
        """
        try:
            ohlcv = await self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            return [
                {
                    'timestamp': candle[0],
                    'open': Decimal(str(candle[1])),
                    'high': Decimal(str(candle[2])),
                    'low': Decimal(str(candle[3])),
                    'close': Decimal(str(candle[4])),
                    'volume': Decimal(str(candle[5]))
                }
                for candle in ohlcv
            ]

        except Exception as e:
            logger.error(f"Error fetching historical data for {symbol}: {e}")
            raise

    async def get_trading_fees(self, symbol: Optional[str] = None) -> Dict:
        """
        Get trading fees

        Args:
            symbol: Optional trading pair

        Returns:
            Fee information
        """
        try:
            # Coinbase fees are typically:
            # - Maker: 0.4% - 0.5%
            # - Taker: 0.6%
            # Actual fees depend on 30-day volume

            fees = await self.exchange.fetch_trading_fees()

            if symbol and symbol in fees:
                return {
                    'symbol': symbol,
                    'maker': Decimal(str(fees[symbol]['maker'])),
                    'taker': Decimal(str(fees[symbol]['taker']))
                }

            # Return default fees
            return {
                'maker': Decimal('0.005'),  # 0.5%
                'taker': Decimal('0.006')   # 0.6%
            }

        except Exception as e:
            logger.warning(f"Error fetching fees: {e}. Using defaults.")
            return {
                'maker': Decimal('0.005'),
                'taker': Decimal('0.006')
            }

    async def get_markets(self) -> List[Dict]:
        """
        Get available trading markets

        Returns:
            List of market information
        """
        try:
            markets = await self.exchange.fetch_markets()

            return [
                {
                    'symbol': market['symbol'],
                    'base': market['base'],
                    'quote': market['quote'],
                    'active': market['active'],
                    'type': market.get('type', 'spot'),
                    'min_amount': Decimal(str(market['limits']['amount']['min'])) if market['limits']['amount']['min'] else None,
                    'max_amount': Decimal(str(market['limits']['amount']['max'])) if market['limits']['amount']['max'] else None,
                    'min_price': Decimal(str(market['limits']['price']['min'])) if market['limits']['price']['min'] else None,
                    'max_price': Decimal(str(market['limits']['price']['max'])) if market['limits']['price']['max'] else None
                }
                for market in markets
                if market['active'] and market.get('spot', True)
            ]

        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    async def get_deposit_address(self, currency: str) -> Optional[Dict]:
        """
        Get deposit address for a currency

        Args:
            currency: Currency code (e.g., 'BTC', 'ETH')

        Returns:
            Deposit address information
        """
        try:
            address_info = await self.exchange.fetch_deposit_address(currency)

            return {
                'currency': currency,
                'address': address_info['address'],
                'tag': address_info.get('tag'),
                'network': address_info.get('network')
            }

        except Exception as e:
            logger.error(f"Error fetching deposit address for {currency}: {e}")
            return None

    async def withdraw(
        self,
        currency: str,
        amount: Decimal,
        address: str,
        tag: Optional[str] = None,
        network: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Withdraw funds

        Args:
            currency: Currency to withdraw
            amount: Amount to withdraw
            address: Destination address
            tag: Optional address tag/memo
            network: Optional network (e.g., 'ERC20', 'TRC20')

        Returns:
            Withdrawal information
        """
        try:
            params = {}
            if tag:
                params['tag'] = tag
            if network:
                params['network'] = network

            withdrawal = await self.exchange.withdraw(
                currency,
                float(amount),
                address,
                params=params
            )

            logger.info(f"Withdrawal initiated: {withdrawal['id']}")

            return {
                'withdrawal_id': withdrawal['id'],
                'currency': currency,
                'amount': Decimal(str(withdrawal['amount'])),
                'address': address,
                'status': withdrawal.get('status', 'pending'),
                'timestamp': withdrawal.get('timestamp')
            }

        except Exception as e:
            logger.error(f"Error withdrawing {currency}: {e}")
            return None

    def get_supported_symbols(self) -> List[str]:
        """
        Get commonly supported trading pairs on Coinbase

        Returns:
            List of popular symbols
        """
        return [
            'BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD', 'XRP/USD',
            'ADA/USD', 'DOT/USD', 'LINK/USD', 'XLM/USD', 'UNI/USD',
            'ATOM/USD', 'ALGO/USD', 'MATIC/USD', 'AVAX/USD', 'SOL/USD',
            'BTC/USDT', 'ETH/USDT', 'BTC/EUR', 'ETH/EUR'
        ]
