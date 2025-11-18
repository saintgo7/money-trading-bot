from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import jwt
import requests
from loguru import logger

from .base import BaseExchange, OrderSide, OrderType, OrderStatus


class KISExchange(BaseExchange):
    """
    Korea Investment & Securities (KIS) exchange implementation
    한국투자증권 API 구현
    """

    def __init__(self, app_key: str, app_secret: str, account_number: str, testnet: bool = False):
        super().__init__(app_key, app_secret, testnet)
        self.account_number = account_number
        self.access_token = None
        self.base_url = (
            "https://openapivts.koreainvestment.com:29443"
            if testnet
            else "https://openapi.koreainvestment.com:9443"
        )

    async def connect(self) -> bool:
        """Get access token from KIS API"""
        try:
            url = f"{self.base_url}/oauth2/tokenP"
            headers = {"content-type": "application/json"}
            body = {
                "grant_type": "client_credentials",
                "appkey": self.api_key,
                "appsecret": self.api_secret,
            }

            response = requests.post(url, headers=headers, json=body)
            if response.status_code == 200:
                self.access_token = response.json()["access_token"]
                logger.info(f"Connected to KIS (testnet={self.testnet})")
                return True
            else:
                logger.error(f"Failed to connect to KIS: {response.text}")
                return False
        except Exception as e:
            logger.error(f"Error connecting to KIS: {e}")
            return False

    async def disconnect(self) -> bool:
        """Close KIS connection"""
        self.access_token = None
        logger.info("Disconnected from KIS")
        return True

    def _get_headers(self) -> Dict:
        """Get request headers with auth token"""
        return {
            "content-type": "application/json; charset=utf-8",
            "authorization": f"Bearer {self.access_token}",
            "appkey": self.api_key,
            "appsecret": self.api_secret,
        }

    async def get_balance(self) -> Dict[str, Decimal]:
        """Get account balance"""
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/inquire-balance"
            headers = self._get_headers()
            headers["tr_id"] = "TTTC8434R" if self.testnet else "CTTC8434R"

            params = {
                "CANO": self.account_number[:8],
                "ACNT_PRDT_CD": self.account_number[8:],
                "AFHR_FLPR_YN": "N",
                "OFL_YN": "",
                "INQR_DVSN": "02",
                "UNPR_DVSN": "01",
                "FUND_STTL_ICLD_YN": "N",
                "FNCG_AMT_AUTO_RDPT_YN": "N",
                "PRCS_DVSN": "01",
                "CTX_AREA_FK100": "",
                "CTX_AREA_NK100": "",
            }

            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if data["rt_cd"] == "0":
                # Parse balance
                balance = {}
                for item in data["output1"]:
                    if float(item["hldg_qty"]) > 0:
                        balance[item["pdno"]] = Decimal(item["hldg_qty"])

                # Add cash balance
                cash = Decimal(data["output2"][0]["dnca_tot_amt"])
                balance["KRW"] = cash

                return balance
            else:
                raise Exception(f"Failed to get balance: {data['msg1']}")

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
        """Place an order on KIS"""
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-cash"
            headers = self._get_headers()

            # Set transaction ID based on order type
            if side == OrderSide.BUY:
                headers["tr_id"] = "TTTC0802U" if self.testnet else "CTTC0802U"
            else:
                headers["tr_id"] = "TTTC0801U" if self.testnet else "CTTC0801U"

            body = {
                "CANO": self.account_number[:8],
                "ACNT_PRDT_CD": self.account_number[8:],
                "PDNO": symbol,
                "ORD_DVSN": "00" if order_type == OrderType.MARKET else "01",
                "ORD_QTY": str(int(quantity)),
                "ORD_UNPR": str(int(price)) if price else "0",
            }

            response = requests.post(url, headers=headers, json=body)
            data = response.json()

            if data["rt_cd"] == "0":
                logger.info(f"Order placed on KIS: {data}")
                return {
                    "order_id": data["output"]["ORD_NO"],
                    "symbol": symbol,
                    "side": side.value,
                    "type": order_type.value,
                    "quantity": quantity,
                    "price": price or Decimal("0"),
                    "status": OrderStatus.PENDING,
                    "filled": Decimal("0"),
                    "remaining": quantity,
                    "timestamp": datetime.now(),
                }
            else:
                raise Exception(f"Failed to place order: {data['msg1']}")

        except Exception as e:
            logger.error(f"Error placing order: {e}")
            raise

    async def cancel_order(self, order_id: str, symbol: str) -> bool:
        """Cancel an open order"""
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/trading/order-rvsecncl"
            headers = self._get_headers()
            headers["tr_id"] = "TTTC0803U" if self.testnet else "CTTC0803U"

            body = {
                "CANO": self.account_number[:8],
                "ACNT_PRDT_CD": self.account_number[8:],
                "KRX_FWDG_ORD_ORGNO": "",
                "ORGN_ODNO": order_id,
                "ORD_DVSN": "00",
                "RVSE_CNCL_DVSN_CD": "02",
                "ORD_QTY": "0",
                "ORD_UNPR": "0",
                "QTY_ALL_ORD_YN": "Y",
            }

            response = requests.post(url, headers=headers, json=body)
            data = response.json()

            if data["rt_cd"] == "0":
                logger.info(f"Order cancelled: {order_id}")
                return True
            else:
                logger.error(f"Failed to cancel order: {data['msg1']}")
                return False

        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False

    async def get_order_status(self, order_id: str, symbol: str) -> Dict:
        """Get order status - KIS doesn't provide simple order status API"""
        logger.warning("KIS get_order_status not fully implemented")
        return {
            "order_id": order_id,
            "status": OrderStatus.OPEN,
            "filled": Decimal("0"),
            "remaining": Decimal("0"),
        }

    async def get_open_orders(self, symbol: Optional[str] = None) -> List[Dict]:
        """Get all open orders"""
        logger.warning("KIS get_open_orders not fully implemented")
        return []

    async def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker"""
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-price"
            headers = self._get_headers()
            headers["tr_id"] = "FHKST01010100"

            params = {"FID_COND_MRKT_DIV_CODE": "J", "FID_INPUT_ISCD": symbol}

            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if data["rt_cd"] == "0":
                output = data["output"]
                return {
                    "symbol": symbol,
                    "last": Decimal(output["stck_prpr"]),
                    "bid": Decimal(output["stck_bidp"]),
                    "ask": Decimal(output["stck_askp"]),
                    "high": Decimal(output["stck_hgpr"]),
                    "low": Decimal(output["stck_lwpr"]),
                    "volume": Decimal(output["acml_vol"]),
                    "timestamp": datetime.now(),
                }
            else:
                raise Exception(f"Failed to get ticker: {data['msg1']}")

        except Exception as e:
            logger.error(f"Error fetching ticker: {e}")
            raise

    async def get_ohlcv(
        self,
        symbol: str,
        timeframe: str = "D",
        limit: int = 100,
        since: Optional[datetime] = None,
    ) -> List[Dict]:
        """Get OHLCV candlestick data"""
        try:
            url = f"{self.base_url}/uapi/domestic-stock/v1/quotations/inquire-daily-price"
            headers = self._get_headers()
            headers["tr_id"] = "FHKST01010400"

            params = {
                "FID_COND_MRKT_DIV_CODE": "J",
                "FID_INPUT_ISCD": symbol,
                "FID_PERIOD_DIV_CODE": "D",
                "FID_ORG_ADJ_PRC": "0",
            }

            response = requests.get(url, headers=headers, params=params)
            data = response.json()

            if data["rt_cd"] == "0":
                candles = []
                for item in data["output"][:limit]:
                    candles.append({
                        "timestamp": datetime.strptime(item["stck_bsop_date"], "%Y%m%d"),
                        "open": Decimal(item["stck_oprc"]),
                        "high": Decimal(item["stck_hgpr"]),
                        "low": Decimal(item["stck_lwpr"]),
                        "close": Decimal(item["stck_clpr"]),
                        "volume": Decimal(item["acml_vol"]),
                    })
                return candles
            else:
                raise Exception(f"Failed to get OHLCV: {data['msg1']}")

        except Exception as e:
            logger.error(f"Error fetching OHLCV: {e}")
            raise

    async def get_orderbook(self, symbol: str, limit: int = 20) -> Dict:
        """Get order book"""
        logger.warning("KIS get_orderbook not implemented")
        return {"bids": [], "asks": [], "timestamp": datetime.now()}

    async def get_recent_trades(self, symbol: str, limit: int = 100) -> List[Dict]:
        """Get recent trades"""
        logger.warning("KIS get_recent_trades not implemented")
        return []
