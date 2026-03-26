"""Aster DEX Python SDK

支持V3 (EIP712) API的异步交易库。
默认连接Testnet以保证安全。

快速开始:
    from asterdex import Client, Network

    # V3 API
    client = Client.v3(user="0x...", signer="0x...", private_key="0x...")

    # 使用客户端
    orderbook = await client.market.get_order_book("BTCUSDT")
    await client.close()

更多示例请参考: https://github.com/HYwooo/asterdex-python-sdk
"""

from .client import Client
from .constants import (
    DEFAULT_LOG_LEVEL,
    DEFAULT_MAX_RETRIES,
    DEFAULT_NETWORK,
    DEFAULT_TIMEOUT,
    KLINE_INTERVALS,
    MARGIN_TYPE_CROSSED,
    MARGIN_TYPE_ISOLATED,
    ORDER_SIDE_BUY,
    ORDER_SIDE_SELL,
    ORDER_TYPE_LIMIT,
    ORDER_TYPE_MARKET,
    ORDER_TYPE_STOP,
    ORDER_TYPE_STOP_MARKET,
    ORDER_TYPE_TAKE_PROFIT,
    ORDER_TYPE_TAKE_PROFIT_MARKET,
    ORDER_TYPE_TRAILING_STOP_MARKET,
    POSITION_SIDE_BOTH,
    POSITION_SIDE_LONG,
    POSITION_SIDE_SHORT,
    TIME_IN_FORCE_FOK,
    TIME_IN_FORCE_GTC,
    TIME_IN_FORCE_GTX,
    TIME_IN_FORCE_HIDDEN,
    TIME_IN_FORCE_IOC,
    LogLevel,
    Network,
    ProductType,
    __version__,
)
from .exceptions import (
    APIError,
    AsterError,
    AuthenticationError,
    NetworkError,
    OrderError,
    RateLimitError,
    SignatureError,
    StreamError,
    TimeoutError,
    ValidationError,
    WebSocketError,
)
from .hybrid_client import HybridClient
from .logging_config import get_logger, set_log_level, set_module_log_level
from .models import (
    AccountInfo,
    Balance,
    ExchangeInfo,
    FundingRate,
    Kline,
    MarkPrice,
    Order,
    OrderBook,
    Position,
    Ticker24h,
    Trade,
)
from .websocket.client import WebSocketClient

__all__ = [
    "__version__",
    "Client",
    "Network",
    "ProductType",
    "LogLevel",
    "WebSocketClient",
    "HybridClient",
    "get_logger",
    "set_log_level",
    "set_module_log_level",
    "DEFAULT_NETWORK",
    "DEFAULT_LOG_LEVEL",
    "DEFAULT_TIMEOUT",
    "DEFAULT_MAX_RETRIES",
    "KLINE_INTERVALS",
    "ORDER_SIDE_BUY",
    "ORDER_SIDE_SELL",
    "ORDER_TYPE_LIMIT",
    "ORDER_TYPE_MARKET",
    "ORDER_TYPE_STOP",
    "ORDER_TYPE_STOP_MARKET",
    "ORDER_TYPE_TAKE_PROFIT",
    "ORDER_TYPE_TAKE_PROFIT_MARKET",
    "ORDER_TYPE_TRAILING_STOP_MARKET",
    "TIME_IN_FORCE_GTC",
    "TIME_IN_FORCE_IOC",
    "TIME_IN_FORCE_FOK",
    "TIME_IN_FORCE_GTX",
    "TIME_IN_FORCE_HIDDEN",
    "POSITION_SIDE_BOTH",
    "POSITION_SIDE_LONG",
    "POSITION_SIDE_SHORT",
    "MARGIN_TYPE_ISOLATED",
    "MARGIN_TYPE_CROSSED",
    "AsterError",
    "APIError",
    "AuthenticationError",
    "NetworkError",
    "OrderError",
    "RateLimitError",
    "SignatureError",
    "StreamError",
    "TimeoutError",
    "ValidationError",
    "WebSocketError",
    "OrderBook",
    "Trade",
    "Ticker24h",
    "MarkPrice",
    "Kline",
    "ExchangeInfo",
    "Balance",
    "Position",
    "Order",
    "AccountInfo",
    "FundingRate",
]
