"""V1 API客户端"""

from typing import Any, Optional

from ...constants import DEFAULT_NETWORK, V1_API_VERSION, Network
from ...logging_config import get_logger
from ..base import BaseAPIClient
from .auth import HMACSigner

logger = get_logger(__name__)


class V1Client(BaseAPIClient):
    """V1 API客户端"""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        network: Network = DEFAULT_NETWORK,
    ):
        super().__init__(network)
        self.api_version = V1_API_VERSION
        self.signer = HMACSigner(api_key, secret_key)

    def _signed_params(self, params: dict[str, Any]) -> dict[str, Any]:
        """添加签名参数"""
        return self.signer.sign(params)

    async def ping(self) -> dict[str, Any]:
        """测试连接"""
        return await self.get(f"/fapi/{self.api_version}/ping")

    async def get_time(self) -> dict[str, Any]:
        """获取服务器时间"""
        return await self.get(f"/fapi/{self.api_version}/time")

    async def get_exchange_info(self) -> dict[str, Any]:
        """获取交易所信息"""
        return await self.get(f"/fapi/{self.api_version}/exchangeInfo")

    async def get_order_book(self, symbol: str, limit: int = 500) -> dict[str, Any]:
        """获取订单簿

        Args:
            symbol: 交易对
            limit: 深度数量
        """
        return await self.get(
            f"/fapi/{self.api_version}/depth",
            params={"symbol": symbol, "limit": limit},
        )

    async def get_trades(self, symbol: str, limit: int = 500) -> dict[str, Any]:
        """获取最近成交

        Args:
            symbol: 交易对
            limit: 数量限制
        """
        return await self.get(
            f"/fapi/{self.api_version}/trades",
            params={"symbol": symbol, "limit": limit},
        )

    async def get_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取K线数据

        Args:
            symbol: 交易对
            interval: K线间隔
            limit: 数量限制
            start_time: 开始时间戳
            end_time: 结束时间戳
        """
        params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self.get(f"/fapi/{self.api_version}/klines", params=params)

    async def get_ticker_24h(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """获取24小时行情

        Args:
            symbol: 交易对，不传则返回所有
        """
        params = {"symbol": symbol} if symbol else {}
        return await self.get(f"/fapi/{self.api_version}/ticker/24hr", params=params)

    async def get_mark_price(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """获取标记价格

        Args:
            symbol: 交易对
        """
        params = {"symbol": symbol} if symbol else {}
        return await self.get(f"/fapi/{self.api_version}/premiumIndex", params=params)

    async def get_funding_rate(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """获取资金费率历史

        Args:
            symbol: 交易对
            start_time: 开始时间
            end_time: 结束时间
            limit: 数量限制
        """
        params: dict[str, Any] = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self.get(f"/fapi/{self.api_version}/fundingRate", params=params)

    async def create_order(
        self,
        symbol: str,
        side: str,
        type: str,
        quantity: str,
        price: Optional[str] = None,
        time_in_force: str = "GTC",
        position_side: Optional[str] = None,
        reduce_only: bool = False,
        new_order_resp_type: Optional[str] = None,
    ) -> dict[str, Any]:
        """创建订单

        Args:
            symbol: 交易对
            side: 订单方向 (BUY/SELL)
            type: 订单类型
            quantity: 数量
            price: 价格
            time_in_force: 有效时间
            position_side: 持仓方向
            reduce_only: 仅减仓
            new_order_resp_type: 响应类型
        """
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": type,
            "quantity": quantity,
            "timeInForce": time_in_force,
        }
        if price:
            params["price"] = price
        if position_side:
            params["positionSide"] = position_side
        if reduce_only:
            params["reduceOnly"] = "true"
        if new_order_resp_type:
            params["newOrderRespType"] = new_order_resp_type

        signed_params = self._signed_params(params)
        headers = self.signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/order",
            data=signed_params,
            headers=headers,
        )

    async def cancel_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        """取消订单

        Args:
            symbol: 交易对
            order_id: 订单ID
        """
        params = self._signed_params({"symbol": symbol, "orderId": order_id})
        headers = self.signer.get_headers()
        return await self.delete(f"/fapi/{self.api_version}/order", params=params, headers=headers)

    async def get_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        """查询订单

        Args:
            symbol: 交易对
            order_id: 订单ID
        """
        params = self._signed_params({"symbol": symbol, "orderId": order_id})
        headers = self.signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/order", params=params, headers=headers)

    async def get_open_orders(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """查询当前挂单

        Args:
            symbol: 交易对
        """
        params = self._signed_params({"symbol": symbol} if symbol else {})
        headers = self.signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/openOrders", params=params, headers=headers)

    async def get_all_orders(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """查询所有订单

        Args:
            symbol: 交易对
            start_time: 开始时间
            end_time: 结束时间
            limit: 数量限制
        """
        params: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        signed_params = self._signed_params(params)
        headers = self.signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/allOrders",
            params=signed_params,
            headers=headers,
        )

    async def get_balance(self) -> dict[str, Any]:
        """查询账户余额"""
        params = self._signed_params({})
        headers = self.signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/balance", params=params, headers=headers)

    async def get_position(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """查询持仓

        Args:
            symbol: 交易对
        """
        params = self._signed_params({"symbol": symbol} if symbol else {})
        headers = self.signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/positionRisk", params=params, headers=headers)

    async def set_leverage(self, symbol: str, leverage: int) -> dict[str, Any]:
        """调整杠杆

        Args:
            symbol: 交易对
            leverage: 杠杆倍数
        """
        params = self._signed_params({"symbol": symbol, "leverage": leverage})
        headers = self.signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/leverage",
            data=params,
            headers=headers,
        )

    async def set_margin_type(self, symbol: str, margin_type: str) -> dict[str, Any]:
        """调整保证金模式

        Args:
            symbol: 交易对
            margin_type: 保证金模式 (ISOLATED/CROSSED)
        """
        params = self._signed_params({"symbol": symbol, "marginType": margin_type})
        headers = self.signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/marginType",
            data=params,
            headers=headers,
        )
