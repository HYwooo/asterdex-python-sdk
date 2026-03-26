"""Aster DEX统一客户端入口

提供V3客户端的创建接口。
"""

from typing import Any, Optional

from .constants import DEFAULT_NETWORK, Network
from .logging_config import get_logger

logger = get_logger(__name__)


class Client:
    """Aster DEX统一客户端

    仅支持V3 (EIP712) API。

    Usage:
        # V3 API
        from asterdex import Client, Network
        client = Client.v3(user="0x...", signer="0x...", private_key="0x...")

        # 使用客户端
        orderbook = await client.get_order_book("BTCUSDT")
        await client.close()
    """

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
            api_version: API版本 (仅支持 "v3")
            **kwargs: 传递给V3客户端的参数

        Returns:
            客户端实例

        Raises:
            ValueError: 不支持的API版本
        """
        if api_version.lower() == "v3":
            return cls.v3(**kwargs)
        else:
            raise ValueError(f"不支持的API版本: {api_version}, 仅支持: v3")


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
        return AccountEndpoints(self._client)


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
    """账户端点"""

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
