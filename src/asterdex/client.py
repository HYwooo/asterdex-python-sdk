"""Aster DEX统一客户端入口

提供V1和V3客户端的创建接口。

默认使用V3 API (推荐)。V1 API需要通过 enable_v1=True 显式启用，
且会输出警告提示V1未经测试。
"""

import os
import warnings
from typing import Any, Optional

from .constants import DEFAULT_NETWORK, Network
from .logging_config import get_logger

logger = get_logger(__name__)

V1_WARNING = """
⚠️  [V1 API 警告] V1 API (HMAC认证) 未经过完整测试，可能存在兼容性问题。
    建议使用 V3 API (EIP712签名) 以获得更好的安全性和完整支持。
    如需启用V1 API，请设置 enable_v1=True 或环境变量 ASTERDEX_ENABLE_V1=true
"""


class Client:
    """Aster DEX统一客户端

    支持V1 (HMAC) 和 V3 (EIP712) 两种API版本。
    默认使用V3 (推荐)，V1需要显式启用。

    Usage:
        # V3 API (推荐)
        from asterdex import Client, Network
        client = Client.v3(user="0x...", signer="0x...", private_key="0x...")

        # V1 API (需要显式启用)
        client = Client.v1(api_key="...", secret_key="...", enable_v1=True)

        # 使用客户端
        orderbook = await client.get_order_book("BTCUSDT")
        await client.close()
    """

    @staticmethod
    def v1(
        api_key: str,
        secret_key: str,
        network: Network = DEFAULT_NETWORK,
        enable_v1: bool = False,
    ) -> "V1ClientWrapper":
        """创建V1 API客户端 (需要显式启用)

        Args:
            api_key: API密钥
            secret_key: 密钥
            network: 网络环境 (默认testnet)
            enable_v1: 显式启用V1 API (默认False)

        Returns:
            V1客户端实例

        Raises:
            ValueError: 如果未启用V1 API
        """
        env_enable = os.getenv("ASTERDEX_ENABLE_V1", "false").lower() == "true"

        if not enable_v1 and not env_enable:
            raise ValueError(
                "V1 API 默认禁用。请使用V3 API (推荐) 或显式启用V1:\n"
                "  client = Client.v1(..., enable_v1=True)\n"
                "或设置环境变量:\n"
                "  ASTERDEX_ENABLE_V1=true"
            )

        if not enable_v1 and (env_enable or os.getenv("ASTERDEX_ENABLE_V1")):
            warnings.warn(V1_WARNING, DeprecationWarning, stacklevel=2)
            logger.warning("V1 API 已启用 - 未经完整测试")

        from .api.v1.client import V1Client

        client = V1Client(api_key=api_key, secret_key=secret_key, network=network)
        logger.info(f"V1客户端已创建, network={network.value}")
        return V1ClientWrapper(client)

    @staticmethod
    def v3(
        user: str,
        signer: str,
        private_key: str,
        network: Network = DEFAULT_NETWORK,
    ) -> "V3ClientWrapper":
        """创建V3 API客户端

        Args:
            user: 主账户钱包地址
            signer: API钱包地址
            private_key: 私钥
            network: 网络环境 (默认testnet)

        Returns:
            V3客户端实例
        """
        from .api.v3.client import V3Client

        client = V3Client(user=user, signer=signer, private_key=private_key, network=network)
        logger.info(f"V3客户端已创建, network={network.value}")
        return V3ClientWrapper(client)

    @classmethod
    def create(
        cls,
        api_version: str,
        **kwargs: Any,
    ) -> Any:
        """创建客户端 (通用接口)

        Args:
            api_version: API版本 ("v1" 或 "v3")
            **kwargs: 传递给对应客户端的参数

        Returns:
            客户端实例

        Raises:
            ValueError: 不支持的API版本
        """
        if api_version.lower() == "v1":
            return cls.v1(**kwargs)
        elif api_version.lower() == "v3":
            return cls.v3(**kwargs)
        else:
            raise ValueError(f"不支持的API版本: {api_version}, 支持: v1, v3")


class V1ClientWrapper:
    """V1客户端包装器"""

    def __init__(self, client: Any):
        self._client = client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    async def close(self) -> None:
        await self._client.close()

    @property
    def market(self) -> Any:
        return MarketEndpoints(self._client)

    @property
    def order(self) -> Any:
        return OrderEndpoints(self._client)

    @property
    def account(self) -> Any:
        return AccountEndpoints(self._client)


class V3ClientWrapper:
    """V3客户端包装器"""

    def __init__(self, client: Any):
        self._client = client

    def __getattr__(self, name: str) -> Any:
        return getattr(self._client, name)

    async def close(self) -> None:
        await self._client.close()

    @property
    def market(self) -> Any:
        return MarketEndpoints(self._client)

    @property
    def order(self) -> Any:
        return OrderEndpoints(self._client)

    @property
    def account(self) -> Any:
        return AccountEndpointsV3(self._client)


class MarketEndpoints:
    """市场数据端点"""

    def __init__(self, client: Any):
        self._client = client

    async def ping(self) -> dict[str, Any]:
        return await self._client.ping()

    async def get_time(self) -> dict[str, Any]:
        return await self._client.get_time()

    async def get_exchange_info(self) -> dict[str, Any]:
        return await self._client.get_exchange_info()

    async def get_order_book(self, symbol: str, limit: int = 500) -> dict[str, Any]:
        return await self._client.get_order_book(symbol, limit)

    async def get_trades(self, symbol: str, limit: int = 500) -> dict[str, Any]:
        return await self._client.get_trades(symbol, limit)

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> dict[str, Any]:
        return await self._client.get_klines(symbol, interval, limit, start_time, end_time)

    async def get_ticker_24h(self, symbol: Optional[str] = None) -> dict[str, Any]:
        return await self._client.get_ticker_24h(symbol)

    async def get_mark_price(self, symbol: Optional[str] = None) -> dict[str, Any]:
        return await self._client.get_mark_price(symbol)


class OrderEndpoints:
    """订单端点"""

    def __init__(self, client: Any):
        self._client = client

    async def create(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: str = "GTC",
        position_side: Optional[str] = None,
        reduce_only: bool = False,
        close_position: bool = False,
        stop_price: Optional[str] = None,
    ) -> dict[str, Any]:
        return await self._client.create_order(
            symbol,
            side,
            type,
            quantity,
            price,
            time_in_force,
            reduce_only=reduce_only,
            close_position=close_position,
            stop_price=stop_price,
            position_side=position_side,
        )

    async def cancel(self, symbol: str, order_id: int) -> dict[str, Any]:
        return await self._client.cancel_order(symbol, order_id)

    async def get(self, symbol: str, order_id: int) -> dict[str, Any]:
        return await self._client.get_order(symbol, order_id)

    async def get_open_orders(self, symbol: Optional[str] = None) -> dict[str, Any]:
        return await self._client.get_open_orders(symbol)

    async def get_all_orders(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        return await self._client.get_all_orders(symbol, start_time, end_time, limit)


class AccountEndpoints:
    """账户端点 (V1)"""

    def __init__(self, client: Any):
        self._client = client

    async def get_balance(self) -> dict[str, Any]:
        return await self._client.get_balance()

    async def get_position(self, symbol: Optional[str] = None) -> dict[str, Any]:
        return await self._client.get_position(symbol)

    async def set_leverage(self, symbol: str, leverage: int) -> dict[str, Any]:
        return await self._client.set_leverage(symbol, leverage)

    async def set_margin_type(self, symbol: str, margin_type: str) -> dict[str, Any]:
        return await self._client.set_margin_type(symbol, margin_type)


class AccountEndpointsV3:
    """账户端点 (V3)"""

    def __init__(self, client: Any):
        self._client = client

    async def get_balance(self) -> dict[str, Any]:
        return await self._client.get_balance()

    async def get_position(self, symbol: Optional[str] = None) -> dict[str, Any]:
        return await self._client.get_position(symbol)

    async def get_account_info(self) -> dict[str, Any]:
        return await self._client.get_account_info()

    async def set_leverage(self, symbol: str, leverage: int) -> dict[str, Any]:
        return await self._client.set_leverage(symbol, leverage)

    async def set_margin_type(self, symbol: str, margin_type: str) -> dict[str, Any]:
        return await self._client.set_margin_type(symbol, margin_type)
