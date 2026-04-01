"""V3 API客户端"""

from typing import TYPE_CHECKING, Any, Optional

from ...constants import DEFAULT_NETWORK, V3_API_VERSION, Network
from ...exceptions import AuthenticationError
from ...logging_config import get_logger
from ...utils.json import dumps
from ..base import BaseAPIClient

if TYPE_CHECKING:
    from .auth import EIP712Signer

logger = get_logger(__name__)


class V3Client(BaseAPIClient):
    """V3 API客户端"""

    signer: "Optional[EIP712Signer]" = None

    def __init__(
        self,
        user: Optional[str] = None,
        signer: Optional[str] = None,
        private_key: Optional[str] = None,
        network: Network = DEFAULT_NETWORK,
        proxy: Optional[str] = None,
    ):
        super().__init__(network, proxy=proxy)
        self.api_version = V3_API_VERSION
        self._has_auth = all([user, signer, private_key])

        if self._has_auth:
            from .auth import EIP712Signer

            assert user is not None and signer is not None and private_key is not None
            self.signer = EIP712Signer(user, signer, private_key)
        else:
            self.signer = None

    def _require_auth(self) -> "EIP712Signer":
        """要求认证，未认证时抛出异常，返回签名器供后续使用"""
        if not self._has_auth or self.signer is None:
            raise AuthenticationError(
                message="Authentication required for signed operations",
                code=401,
            )
        return self.signer

    async def noop(self, nonce: int) -> dict[str, Any]:
        """Noop操作取消pending交易

        Args:
            nonce: 要取消的nonce值
        """
        signer = self._require_auth()
        params, _ = signer.sign({"nonce": str(nonce)})
        headers = signer.get_headers()
        return await self.post(f"/fapi/{self.api_version}/noop", data=params, headers=headers)

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
        """获取订单簿"""
        return await self.get(
            f"/fapi/{self.api_version}/depth",
            params={"symbol": symbol, "limit": limit},
        )

    async def get_trades(self, symbol: str, limit: int = 500) -> dict[str, Any]:
        """获取最近成交"""
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
        """获取K线数据"""
        params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self.get(f"/fapi/{self.api_version}/klines", params=params)

    async def get_ticker_24h(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """获取24小时行情"""
        params = {"symbol": symbol} if symbol else {}
        return await self.get(f"/fapi/{self.api_version}/ticker/24hr", params=params)

    async def get_mark_price(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """获取标记价格"""
        params = {"symbol": symbol} if symbol else {}
        return await self.get(f"/fapi/{self.api_version}/premiumIndex", params=params)

    async def get_funding_rate(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """获取资金费率"""
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
        time_in_force: Optional[str] = None,
        reduce_only: bool = False,
        close_position: bool = False,
        stop_price: Optional[str] = None,
        position_side: Optional[str] = None,
    ) -> dict[str, Any]:
        """创建订单

        Args:
            symbol: 交易对
            side: 买卖方向 BUY/SELL
            type: 订单类型 LIMIT/MARKET/STOP/TAKE_PROFIT/STOP_MARKET/TAKE_PROFIT_MARKET
            quantity: 数量
            price: 价格 (LIMIT订单需要)
            time_in_force: 有效时间 GTC/IOC/FOK (LIMIT订单需要)
            reduce_only: 仅减仓 (最高优先级，不受 rate limit 影响)
            close_position: 全平仓 (最高优先级，不受 rate limit 影响)
            stop_price: 触发价格 (STOP/TAKE_PROFIT 订单需要)
            position_side: 持仓方向 LONG/SHORT/BOTH
        """
        order_type_upper = type.upper()
        params: dict[str, Any] = {
            "symbol": symbol,
            "side": side,
            "type": order_type_upper,
            "quantity": quantity,
        }

        if price:
            params["price"] = price

        if order_type_upper == "LIMIT" and time_in_force:
            params["timeInForce"] = time_in_force
        elif order_type_upper == "LIMIT" and not time_in_force:
            params["timeInForce"] = "GTC"

        if reduce_only:
            params["reduceOnly"] = "true"

        if close_position:
            params["closePosition"] = "true"

        if stop_price:
            params["stopPrice"] = stop_price

        if position_side:
            params["positionSide"] = position_side

        signer = self._require_auth()
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/order",
            data=signed_params,
            headers=headers,
        )

    async def batch_orders(self, orders: list[dict[str, Any]]) -> dict[str, Any]:
        """批量下单

        Args:
            orders: 订单列表，每项包含symbol, side, type, quantity, price, timeInForce
        """
        signer = self._require_auth()

        params, _ = signer.sign({"batchOrders": dumps(orders)})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/batchOrders",
            data=params,
            headers=headers,
        )

    async def cancel_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        """取消订单"""
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol, "orderId": str(order_id)})
        headers = signer.get_headers()
        return await self.delete(f"/fapi/{self.api_version}/order", params=params, headers=headers)

    async def get_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        """查询订单"""
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol, "orderId": str(order_id)})
        headers = signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/order", params=params, headers=headers)

    async def get_open_orders(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """查询当前挂单"""
        signer = self._require_auth()
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/openOrders",
            params=signed_params,
            headers=headers,
        )

    async def get_balance(self) -> dict[str, Any]:
        """查询账户余额"""
        signer = self._require_auth()
        params, _ = signer.sign({})
        headers = signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/balance", params=params, headers=headers)

    async def get_position(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """查询持仓"""
        signer = self._require_auth()
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/positionRisk",
            params=signed_params,
            headers=headers,
        )

    async def get_account_info(self) -> dict[str, Any]:
        """获取账户信息 (V3)"""
        signer = self._require_auth()
        params, _ = signer.sign({})
        headers = signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/account", params=params, headers=headers)

    async def set_leverage(self, symbol: str, leverage: int) -> dict[str, Any]:
        """调整杠杆"""
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol, "leverage": str(leverage)})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/leverage",
            data=params,
            headers=headers,
        )

    async def set_margin_type(self, symbol: str, margin_type: str) -> dict[str, Any]:
        """调整保证金模式"""
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol, "marginType": margin_type})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/marginType",
            data=params,
            headers=headers,
        )

    async def get_all_orders(
        self,
        symbol: str,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """查询所有订单"""
        signer = self._require_auth()
        params: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/allOrders", params=signed_params, headers=headers
        )

    async def get_user_trades(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 500,
    ) -> dict[str, Any]:
        """查询账户交易历史"""
        signer = self._require_auth()
        params: dict[str, Any] = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/userTrades", params=signed_params, headers=headers
        )

    async def get_commission_rate(self, symbol: str) -> dict[str, Any]:
        """查询手续费率"""
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol})
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/commissionRate", params=params, headers=headers
        )

    async def cancel_all_open_orders(self, symbol: str) -> dict[str, Any]:
        """取消所有挂单"""
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol})
        headers = signer.get_headers()
        return await self.delete(
            f"/fapi/{self.api_version}/allOpenOrders", params=params, headers=headers
        )

    async def cancel_multiple_orders(self, symbol: str, order_ids: list[int]) -> dict[str, Any]:
        """批量取消订单"""
        signer = self._require_auth()

        order_id_list = [str(oid) for oid in order_ids]
        params, _ = signer.sign({"symbol": symbol, "orderIdList": dumps(order_id_list)})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/batchCancel", data=params, headers=headers
        )

    async def get_income_history(
        self,
        symbol: Optional[str] = None,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        """查询收益历史"""
        signer = self._require_auth()
        params: dict[str, Any] = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/income", params=signed_params, headers=headers
        )

    async def get_leverage_bracket(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """查询杠杆分级"""
        signer = self._require_auth()
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/leverageBracket", params=signed_params, headers=headers
        )

    async def change_position_mode(self, hedge_mode: bool) -> dict[str, Any]:
        """切换持仓模式

        Args:
            hedge_mode: True为对冲模式, False为单向模式
        """
        signer = self._require_auth()
        params, _ = signer.sign({"positionSide": "HEDGE" if hedge_mode else "ONEWAY"})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/positionSide", data=params, headers=headers
        )

    async def get_position_mode(self) -> dict[str, Any]:
        """获取当前持仓模式"""
        signer = self._require_auth()
        params, _ = signer.sign({})
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/positionSide", params=params, headers=headers
        )

    async def transfer_spot_futures(self, asset: str, amount: str, type: int) -> dict[str, Any]:
        """现货与合约转账

        Args:
            asset: 资产符号
            amount: 数量
            type: 1: 现货->合约, 2: 合约->现货
        """
        signer = self._require_auth()
        params, _ = signer.sign({"asset": asset, "amount": amount, "type": str(type)})
        headers = signer.get_headers()
        return await self.post(f"/fapi/{self.api_version}/transfer", data=params, headers=headers)

    async def get_ticker_price(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """获取价格 ticker

        GET /fapi/v3/ticker/price

        Args:
            symbol: 交易对 (可选，不传则返回所有)
        """
        params = {"symbol": symbol} if symbol else {}
        return await self.get(f"/fapi/{self.api_version}/ticker/price", params=params)

    async def get_book_ticker(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """获取订单簿 ticker

        GET /fapi/v3/ticker/bookTicker

        Args:
            symbol: 交易对 (可选，不传则返回所有)
        """
        params = {"symbol": symbol} if symbol else {}
        return await self.get(f"/fapi/{self.api_version}/ticker/bookTicker", params=params)

    async def get_historical_trades(
        self,
        symbol: str,
        limit: int = 500,
        from_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取历史成交 (需要MARKET_DATA Key)

        GET /fapi/v3/historicalTrades

        Args:
            symbol: 交易对
            limit: 返回数量，默认500，最大1000
            from_id: 起始交易ID
        """
        params: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if from_id:
            params["fromId"] = from_id
        return await self.get(f"/fapi/{self.api_version}/historicalTrades", params=params)

    async def get_agg_trades(
        self,
        symbol: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
        from_id: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取聚合交易

        GET /fapi/v3/aggTrades

        Args:
            symbol: 交易对
            limit: 返回数量
            start_time: 起始时间
            end_time: 结束时间
            from_id: 起始聚合交易ID
        """
        params: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        if from_id:
            params["fromId"] = from_id
        return await self.get(f"/fapi/{self.api_version}/aggTrades", params=params)

    async def get_index_price_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取指数价格K线

        GET /fapi/v3/indexPriceKlines

        Args:
            symbol: 交易对
            interval: K线间隔 (1m, 5m, 15m, 1h, 4h, 1d等)
            limit: 返回数量
            start_time: 起始时间
            end_time: 结束时间
        """
        params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self.get(f"/fapi/{self.api_version}/indexPriceKlines", params=params)

    async def get_mark_price_klines(
        self,
        symbol: str,
        interval: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取标记价格K线

        GET /fapi/v3/markPriceKlines

        Args:
            symbol: 交易对
            interval: K线间隔
            limit: 返回数量
            start_time: 起始时间
            end_time: 结束时间
        """
        params: dict[str, Any] = {"symbol": symbol, "interval": interval, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        return await self.get(f"/fapi/{self.api_version}/markPriceKlines", params=params)

    async def get_single_open_order(self, symbol: str, order_id: int) -> dict[str, Any]:
        """查询单笔挂单

        GET /fapi/v3/openOrder

        Args:
            symbol: 交易对
            order_id: 订单ID
        """
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol, "orderId": str(order_id)})
        headers = signer.get_headers()
        return await self.get(f"/fapi/{self.api_version}/openOrder", params=params, headers=headers)

    async def modify_isolated_margin(
        self,
        symbol: str,
        amount: str,
        type: int,
    ) -> dict[str, Any]:
        """调整逐仓保证金

        POST /fapi/v3/positionMargin

        Args:
            symbol: 交易对
            amount: 调整数量 (正数增加, 负数减少)
            type: 1: 增加保证金, 2: 减少保证金
        """
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol, "amount": amount, "type": str(type)})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/positionMargin", data=params, headers=headers
        )

    async def get_position_margin_history(
        self,
        symbol: str,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取逐仓保证金变动历史

        GET /fapi/v3/positionMargin/history

        Args:
            symbol: 交易对
            limit: 返回数量
            start_time: 起始时间
            end_time: 结束时间
        """
        signer = self._require_auth()
        params: dict[str, Any] = {"symbol": symbol, "limit": limit}
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/positionMargin/history",
            params=signed_params,
            headers=headers,
        )

    async def get_adl_quantile(self, symbol: Optional[str] = None) -> dict[str, Any]:
        """获取ADL分位估算

        GET /fapi/v3/adlQuantile

        Args:
            symbol: 交易对 (可选)
        """
        signer = self._require_auth()
        params: dict[str, Any] = {}
        if symbol:
            params["symbol"] = symbol
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/adlQuantile", params=signed_params, headers=headers
        )

    async def get_force_orders(
        self,
        symbol: Optional[str] = None,
        limit: int = 500,
        start_time: Optional[int] = None,
        end_time: Optional[int] = None,
    ) -> dict[str, Any]:
        """获取强平订单

        GET /fapi/v3/forceOrders

        Args:
            symbol: 交易对 (可选)
            limit: 返回数量
            start_time: 起始时间
            end_time: 结束时间
        """
        signer = self._require_auth()
        params: dict[str, Any] = {"limit": limit}
        if symbol:
            params["symbol"] = symbol
        if start_time:
            params["startTime"] = start_time
        if end_time:
            params["endTime"] = end_time
        signed_params, _ = signer.sign(params)
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/forceOrders", params=signed_params, headers=headers
        )

    async def get_index_references(self, symbol: str) -> dict[str, Any]:
        """获取指数参考

        GET /fapi/v3/indexreferences

        Args:
            symbol: 交易对
        """
        return await self.get(
            f"/fapi/{self.api_version}/indexreferences", params={"symbol": symbol}
        )

    async def get_multi_assets_margin(self) -> dict[str, Any]:
        """查询多资产保证金模式

        GET /fapi/v3/multiAssetsMargin
        """
        signer = self._require_auth()
        params, _ = signer.sign({})
        headers = signer.get_headers()
        return await self.get(
            f"/fapi/{self.api_version}/multiAssetsMargin", params=params, headers=headers
        )

    async def set_multi_assets_margin(self, multi_assets_margin: bool) -> dict[str, Any]:
        """设置多资产保证金模式

        POST /fapi/v3/multiAssetsMargin

        Args:
            multi_assets_margin: True开启, False关闭
        """
        signer = self._require_auth()
        params, _ = signer.sign({"multiAssetsMargin": "true" if multi_assets_margin else "false"})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/multiAssetsMargin", data=params, headers=headers
        )

    async def countdown_cancel_all(
        self,
        symbol: str,
        countdown_time: int,
    ) -> dict[str, Any]:
        """设置自动取消所有挂单定时器

        POST /fapi/v3/countdownCancelAll

        Args:
            symbol: 交易对
            countdown_time: 倒计时时间(毫秒), 0表示取消
        """
        signer = self._require_auth()
        params, _ = signer.sign({"symbol": symbol, "countdownTime": str(countdown_time)})
        headers = signer.get_headers()
        return await self.post(
            f"/fapi/{self.api_version}/countdownCancelAll", data=params, headers=headers
        )

    async def start_user_stream(self) -> dict[str, Any]:
        """开启用户数据流 (WebSocket)

        POST /fapi/v3/listenKey
        """
        signer = self._require_auth()
        params, _ = signer.sign({})
        headers = signer.get_headers()
        return await self.post(f"/fapi/{self.api_version}/listenKey", data=params, headers=headers)

    async def keepalive_user_stream(self, listen_key: str) -> dict[str, Any]:
        """续期用户数据流

        PUT /fapi/v3/listenKey

        Args:
            listen_key: listenKey值
        """
        signer = self._require_auth()
        params, _ = signer.sign({"listenKey": listen_key})
        headers = signer.get_headers()
        return await self.put(f"/fapi/{self.api_version}/listenKey", data=params, headers=headers)

    async def close_user_stream(self, listen_key: str) -> dict[str, Any]:
        """关闭用户数据流

        DELETE /fapi/v3/listenKey

        Args:
            listen_key: listenKey值
        """
        signer = self._require_auth()
        params, _ = signer.sign({"listenKey": listen_key})
        headers = signer.get_headers()
        return await self.delete(
            f"/fapi/{self.api_version}/listenKey", params=params, headers=headers
        )
