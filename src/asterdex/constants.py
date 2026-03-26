"""Aster DEX常量定义

定义网络环境、日志级别、API端点等全局常量。
"""

import os
from enum import Enum

__version__ = "0.1.0"


class ProductType(str, Enum):
    """产品类型枚举"""

    FUTURES = "futures"
    SPOT = "spot"


class Network(str, Enum):
    """网络环境枚举"""

    TESTNET = "testnet"
    MAINNET = "mainnet"

    def __init__(self, value: str):
        super().__init__()

    def get_rest_url(self, product: ProductType = ProductType.FUTURES) -> str:
        """获取REST API基础URL"""
        base_urls = {
            ProductType.FUTURES: {
                Network.TESTNET: "https://fapi.asterdex-testnet.com",
                Network.MAINNET: "https://fapi.asterdex.com",
            },
            ProductType.SPOT: {
                Network.TESTNET: "https://sapi.asterdex-testnet.com",
                Network.MAINNET: "https://sapi.asterdex.com",
            },
        }
        return base_urls[product][self]

    def get_ws_url(self, product: ProductType = ProductType.FUTURES) -> str:
        """获取WebSocket URL"""
        ws_urls = {
            ProductType.FUTURES: {
                Network.TESTNET: "wss://fstream.asterdex-testnet.com",
                Network.MAINNET: "wss://fstream.asterdex.com",
            },
            ProductType.SPOT: {
                Network.TESTNET: "wss://sstream.asterdex-testnet.com",
                Network.MAINNET: "wss://sstream.asterdex.com",
            },
        }
        return ws_urls[product][self]

    @property
    def rest_url(self) -> str:
        """获取Futures REST API基础URL (兼容旧版)"""
        return self.get_rest_url(ProductType.FUTURES)

    @property
    def ws_url(self) -> str:
        """获取Futures WebSocket URL (兼容旧版)"""
        return self.get_ws_url(ProductType.FUTURES)

    @property
    def chain_id(self) -> int:
        """获取链ID"""
        if self == Network.TESTNET:
            return 1666  # Aster Chain Testnet
        return 1666  # Aster Chain Mainnet (同testnet)


class LogLevel(str, Enum):
    """日志级别枚举"""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"

    @property
    def level(self) -> int:
        """转换为logging模块的级别"""
        from logging import DEBUG, ERROR, INFO, WARNING

        return {
            LogLevel.DEBUG: DEBUG,
            LogLevel.INFO: INFO,
            LogLevel.WARNING: WARNING,
            LogLevel.ERROR: ERROR,
        }[self]


# 默认网络配置 (优先使用环境变量)
DEFAULT_NETWORK: Network = Network(os.getenv("ASTERDEX_NETWORK", "testnet").lower())

# 默认日志级别
DEFAULT_LOG_LEVEL: LogLevel = LogLevel(os.getenv("ASTERDEX_LOG_LEVEL", "INFO").upper())

# 超时配置
DEFAULT_TIMEOUT: int = int(os.getenv("ASTERDEX_TIMEOUT", "30"))
DEFAULT_MAX_RETRIES: int = int(os.getenv("ASTERDEX_MAX_RETRIES", "3"))

# API配置
V3_API_VERSION = "v3"

# WebSocket配置
WS_PING_INTERVAL = 60  # 秒
WS_PING_TIMEOUT = 30  # 秒
WS_MAX_RECONNECT_ATTEMPTS = 20  # 增加重连次数
WS_RECONNECT_BASE_DELAY = 0.1  # 100ms 初始延迟
WS_RECONNECT_MAX_DELAY = 2.0  # 最大2秒
WS_MESSAGE_QUEUE_SIZE = 1000

# REST轮询配置 (WebSocket失败时的降级方案)
REST_POLLING_INITIAL_INTERVAL = 1.0  # 秒
REST_POLLING_MAX_INTERVAL = 5.0  # 秒
REST_POLLING_STEP = 0.5  # 每次增加的步长
REST_POLLING_NO_LIMIT = False  # 是否无上限增加间隔

# 限流配置
RATE_LIMIT_WEIGHT_HEADER = "X-MBX-USED-WEIGHT"
RATE_LIMIT_ORDER_HEADER = "X-MBX-ORDER-COUNT"

# 默认限速配置 (当无法从exchangeInfo获取时使用)
DEFAULT_RATE_LIMIT_RAW_REQUEST = 6000
DEFAULT_RATE_LIMIT_REQUEST_WEIGHT = 6000
DEFAULT_RATE_LIMIT_ORDER = 300
DEFAULT_RATE_LIMIT_INTERVAL = "MINUTE"


# 限速器类型枚举
class RateLimitType(str, Enum):
    RAW_REQUEST = "RAW_REQUEST"
    REQUEST_WEIGHT = "REQUEST_WEIGHT"
    ORDER = "ORDER"


class RateLimitInterval(str, Enum):
    SECOND = "SECOND"
    MINUTE = "MINUTE"
    HOUR = "HOUR"
    DAY = "DAY"


# 优先级订单类型 (不受限速影响，优先处理)
PRIORITY_ORDER_TYPES = ["CLOSE_POSITION", "REDUCE_ONLY"]

# 缓存配置
CACHE_EXCHANGE_INFO_SECONDS = 60  # 1分钟

# K线间隔
KLINE_INTERVALS = [
    "1m",
    "3m",
    "5m",
    "15m",
    "30m",
    "1h",
    "2h",
    "4h",
    "6h",
    "8h",
    "12h",
    "1d",
    "3d",
    "1w",
    "1M",
]

# 订单方向
ORDER_SIDE_BUY = "BUY"
ORDER_SIDE_SELL = "SELL"

# 订单类型
ORDER_TYPE_LIMIT = "LIMIT"
ORDER_TYPE_MARKET = "MARKET"
ORDER_TYPE_STOP = "STOP"
ORDER_TYPE_STOP_MARKET = "STOP_MARKET"
ORDER_TYPE_TAKE_PROFIT = "TAKE_PROFIT"
ORDER_TYPE_TAKE_PROFIT_MARKET = "TAKE_PROFIT_MARKET"
ORDER_TYPE_TRAILING_STOP_MARKET = "TRAILING_STOP_MARKET"

# 有效委托类型
TIME_IN_FORCE_GTC = "GTC"  # Good Till Cancel
TIME_IN_FORCE_IOC = "IOC"  # Immediate or Cancel
TIME_IN_FORCE_FOK = "FOK"  # Fill or Kill
TIME_IN_FORCE_GTX = "GTX"  # Good Till Crossing (Post Only)
TIME_IN_FORCE_HIDDEN = "HIDDEN"

# 持仓方向
POSITION_SIDE_BOTH = "BOTH"
POSITION_SIDE_LONG = "LONG"
POSITION_SIDE_SHORT = "SHORT"

# 保证金模式
MARGIN_TYPE_ISOLATED = "ISOLATED"
MARGIN_TYPE_CROSSED = "CROSSED"

# 响应类型
ORDER_RESP_TYPE_ACK = "ACK"
ORDER_RESP_TYPE_RESULT = "RESULT"

# 合约状态
CONTRACT_STATUS_PENDING_TRADING = "PENDING_TRADING"
CONTRACT_STATUS_TRADING = "TRADING"
CONTRACT_STATUS_PRE_SETTLE = "PRE_SETTLE"
CONTRACT_STATUS_SETTLING = "SETTLING"
CONTRACT_STATUS_CLOSE = "CLOSE"

# 订单状态
ORDER_STATUS_NEW = "NEW"
ORDER_STATUS_PARTIALLY_FILLED = "PARTIALLY_FILLED"
ORDER_STATUS_FILLED = "FILLED"
ORDER_STATUS_CANCELED = "CANCELED"
ORDER_STATUS_REJECTED = "REJECTED"
ORDER_STATUS_EXPIRED = "EXPIRED"
