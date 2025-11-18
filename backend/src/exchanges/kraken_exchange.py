"""
Kraken Exchange Connector
Supports Kraken Spot Trading API
"""

import ccxt
from decimal import Decimal
from typing import Dict, List, Optional
import logging
from datetime import datetime

from .base import BaseExchange, OrderSide, OrderType

logger = logging.getLogger(__name__)


class KrakenExchange(BaseExchange):
    """
    Kraken exchange implementation using CCXT

    Supports:
    - Spot trading
    - Market, limit, and advanced orders
    - Real-time price data
    - Account balances
    - Order management
    - Margin trading (optional)
    """

    def __init__(
        self,
        api_key: str,
        api_secret: str,
        testnet: bool = False
    ):
        """
        Initialize Kraken exchange

        Args:
            api_key: Kraken API key
            api_secret: Kraken API secret (base64 encoded)
            testnet: Use testnet (not available for Kraken)
        """
        super().__init__(api_key, api_secret)

        self.testnet = testnet

        # Initialize CCXT exchange
        self.exchange = ccxt.kraken({
            'apiKey': api_key,
            'secret': api_secret,
            'enableRateLimit': True,
            'rateLimit': 3000,  # Kraken has strict rate limits
        })

        if testnet:
            logger.warning("Kraken does not have a public testnet")

        self.exchange_name = "Kraken"

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
                    # Kraken uses X prefix for some currencies
                    clean_currency = currency.replace('X', '').replace('Z', '')
                    balances[clean_currency] = Decimal(str(amount))

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
            # Normalize symbol for Kraken
            kraken_symbol = self._normalize_symbol(symbol)
            ticker = await self.exchange.fetch_ticker(kraken_symbol)

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

    def _normalize_symbol(self, symbol: str) -> str:
        """
        Normalize symbol for Kraken API

        Kraken uses different symbol formats (e.g., XBT for BTC)
        """
        # CCXT handles most normalization, but we can add custom logic
        symbol = symbol.replace('BTC', 'XBT')  # Kraken uses XBT for Bitcoin
        return symbol

    async def place_order(
        self,
        symbol: str,
        side: OrderSide,
        order_type: OrderType,
        quantity: Decimal,
        price: Optional[Decimal] = None,
        leverage: Optional[int] = None
    ) -> Dict:
        """
        Place an order

        Args:
            symbol: Trading pair (e.g., 'BTC/USD')
            side: BUY or SELL
            order_type: MARKET or LIMIT
            quantity: Order quantity (in base currency)
            price: Limit price (required for LIMIT orders)
            leverage: Optional leverage (for margin trading)

        Returns:
            Order information
        """
        try:
            # Validate
            if order_type == OrderType.LIMIT and price is None:
                raise ValueError("Price required for limit orders")

            # Normalize symbol
            kraken_symbol = self._normalize_symbol(symbol)

            # Prepare params
            params = {}
            if leverage:
                params['leverage'] = leverage

            # Place order
            if order_type == OrderType.MARKET:
                order = await self.exchange.create_market_order(
                    kraken_symbol,
                    side.value.lower(),
                    float(quantity),
                    params=params
                )
            else:  # LIMIT
                order = await self.exchange.create_limit_order(
                    kraken_symbol,
                    side.value.lower(),
                    float(quantity),
                    float(price),
                    params=params
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
            kraken_symbol = self._normalize_symbol(symbol)
            await self.exchange.cancel_order(order_id, kraken_symbol)
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
            kraken_symbol = self._normalize_symbol(symbol)
            order = await self.exchange.fetch_order(order_id, kraken_symbol)

            return {
                'order_id': order['id'],
                'symbol': symbol,
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
            kraken_symbol = self._normalize_symbol(symbol) if symbol else None
            orders = await self.exchange.fetch_open_orders(kraken_symbol)

            return [
                {
                    'order_id': order['id'],
                    'symbol': order['symbol'].replace('XBT', 'BTC'),
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
            kraken_symbol = self._normalize_symbol(symbol)
            orderbook = await self.exchange.fetch_order_book(kraken_symbol, limit)

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
            kraken_symbol = self._normalize_symbol(symbol)
            ohlcv = await self.exchange.fetch_ohlcv(kraken_symbol, timeframe, limit=limit)

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
            # Kraken fees are tiered based on 30-day volume:
            # Volume < $50K: 0.26% maker, 0.26% taker
            # Volume $50K-$100K: 0.24% maker, 0.26% taker
            # Higher volumes get better rates

            fees = await self.exchange.fetch_trading_fees()

            if symbol:
                kraken_symbol = self._normalize_symbol(symbol)
                if kraken_symbol in fees:
                    return {
                        'symbol': symbol,
                        'maker': Decimal(str(fees[kraken_symbol]['maker'])),
                        'taker': Decimal(str(fees[kraken_symbol]['taker']))
                    }

            # Return default fees (lowest tier)
            return {
                'maker': Decimal('0.0026'),  # 0.26%
                'taker': Decimal('0.0026')   # 0.26%
            }

        except Exception as e:
            logger.warning(f"Error fetching fees: {e}. Using defaults.")
            return {
                'maker': Decimal('0.0026'),
                'taker': Decimal('0.0026')
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
                    'symbol': market['symbol'].replace('XBT', 'BTC'),
                    'base': market['base'].replace('XBT', 'BTC'),
                    'quote': market['quote'],
                    'active': market['active'],
                    'type': market.get('type', 'spot'),
                    'min_amount': Decimal(str(market['limits']['amount']['min'])) if market['limits']['amount']['min'] else None,
                    'max_amount': Decimal(str(market['limits']['amount']['max'])) if market['limits']['amount']['max'] else None,
                    'min_price': Decimal(str(market['limits']['price']['min'])) if market['limits']['price']['min'] else None,
                    'max_price': Decimal(str(market['limits']['price']['max'])) if market['limits']['price']['max'] else None
                }
                for market in markets
                if market['active']
            ]

        except Exception as e:
            logger.error(f"Error fetching markets: {e}")
            return []

    async def get_deposit_address(self, currency: str, network: Optional[str] = None) -> Optional[Dict]:
        """
        Get deposit address for a currency

        Args:
            currency: Currency code (e.g., 'BTC', 'ETH')
            network: Optional network specification

        Returns:
            Deposit address information
        """
        try:
            # Kraken uses different currency codes
            kraken_currency = 'XBT' if currency == 'BTC' else currency

            params = {}
            if network:
                params['network'] = network

            address_info = await self.exchange.fetch_deposit_address(kraken_currency, params)

            return {
                'currency': currency,
                'address': address_info['address'],
                'tag': address_info.get('tag'),
                'network': network
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
            network: Optional network

        Returns:
            Withdrawal information
        """
        try:
            # Kraken uses different currency codes
            kraken_currency = 'XBT' if currency == 'BTC' else currency

            params = {}
            if tag:
                params['tag'] = tag
            if network:
                params['network'] = network

            withdrawal = await self.exchange.withdraw(
                kraken_currency,
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

    async def get_account_ledger(
        self,
        currency: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get account ledger (transaction history)

        Args:
            currency: Optional currency filter
            limit: Number of entries to fetch

        Returns:
            List of ledger entries
        """
        try:
            params = {}
            if currency:
                kraken_currency = 'XBT' if currency == 'BTC' else currency
                params['asset'] = kraken_currency

            ledger = await self.exchange.fetch_ledger(code=currency, limit=limit, params=params)

            return [
                {
                    'id': entry['id'],
                    'currency': entry['currency'].replace('XBT', 'BTC') if entry['currency'] else None,
                    'type': entry['type'],
                    'amount': Decimal(str(entry['amount'])),
                    'fee': Decimal(str(entry['fee'])) if entry.get('fee') else Decimal('0'),
                    'balance': Decimal(str(entry['after'])) if entry.get('after') else None,
                    'timestamp': entry['timestamp']
                }
                for entry in ledger
            ]

        except Exception as e:
            logger.error(f"Error fetching ledger: {e}")
            return []

    async def get_trades_history(
        self,
        symbol: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict]:
        """
        Get trade history

        Args:
            symbol: Optional symbol filter
            limit: Number of trades to fetch

        Returns:
            List of trades
        """
        try:
            kraken_symbol = self._normalize_symbol(symbol) if symbol else None
            trades = await self.exchange.fetch_my_trades(symbol=kraken_symbol, limit=limit)

            return [
                {
                    'trade_id': trade['id'],
                    'order_id': trade['order'],
                    'symbol': trade['symbol'].replace('XBT', 'BTC'),
                    'side': trade['side'].upper(),
                    'price': Decimal(str(trade['price'])),
                    'quantity': Decimal(str(trade['amount'])),
                    'fee': Decimal(str(trade['fee']['cost'])) if trade.get('fee') else Decimal('0'),
                    'fee_currency': trade['fee']['currency'] if trade.get('fee') else None,
                    'timestamp': trade['timestamp']
                }
                for trade in trades
            ]

        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            return []

    def get_supported_symbols(self) -> List[str]:
        """
        Get commonly supported trading pairs on Kraken

        Returns:
            List of popular symbols
        """
        return [
            'BTC/USD', 'ETH/USD', 'LTC/USD', 'BCH/USD', 'XRP/USD',
            'ADA/USD', 'DOT/USD', 'LINK/USD', 'XLM/USD', 'UNI/USD',
            'ATOM/USD', 'ALGO/USD', 'MATIC/USD', 'AVAX/USD', 'SOL/USD',
            'BTC/EUR', 'ETH/EUR', 'BTC/USDT', 'ETH/USDT', 'BTC/GBP',
            'ETH/BTC', 'ADA/ETH', 'DOT/ETH'
        ]

    async def get_server_time(self) -> int:
        """
        Get Kraken server time

        Returns:
            Server timestamp in milliseconds
        """
        try:
            time_data = await self.exchange.fetch_time()
            return time_data

        except Exception as e:
            logger.error(f"Error fetching server time: {e}")
            return int(datetime.now().timestamp() * 1000)
