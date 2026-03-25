"""WebSocket消息模型"""

from typing import Any, Optional

from pydantic import BaseModel


class WSAggTrade(BaseModel):
    """聚合交易WebSocket消息"""

    event_type: str
    event_time: int
    symbol: str
    agg_trade_id: int
    price: str
    qty: str
    first_trade_id: int
    last_trade_id: int
    trade_time: int
    is_buyer_maker: bool


class WSKline(BaseModel):
    """K线WebSocket消息"""

    event_type: str
    event_time: int
    symbol: str
    kline: dict[str, Any]


class WSTicker(BaseModel):
    """行情WebSocket消息"""

    event_type: str
    event_time: int
    symbol: str
    price_change: str
    price_change_percent: str
    weighted_avg_price: str
    last_price: str
    last_qty: str
    open_price: str
    high_price: str
    low_price: str
    volume: str
    quote_volume: str
    open_time: int
    close_time: int
    first_id: int
    last_id: int
    count: int


class WSBookTicker(BaseModel):
    """订单簿最佳价格WebSocket消息"""

    update_id: int
    event_time: int
    transaction_time: int
    symbol: str
    bid_price: str
    bid_qty: str
    ask_price: str
    ask_qty: str


class WSMiniTicker(BaseModel):
    """迷你行情WebSocket消息"""

    event_type: str
    event_time: int
    symbol: str
    close_price: str
    open_price: str
    high_price: str
    low_price: str
    volume: str
    quote_volume: str


class WSMarkPrice(BaseModel):
    """标记价格WebSocket消息"""

    event_type: str
    event_time: int
    symbol: str
    mark_price: str
    index_price: str
    estimated_settle_price: str
    funding_rate: str
    next_funding_time: int


class WSLiquidation(BaseModel):
    """强平订单WebSocket消息"""

    event_type: str
    event_time: int
    order: dict[str, Any]


class WSOrderUpdate(BaseModel):
    """订单更新WebSocket消息"""

    event_type: str
    event_time: int
    transaction_time: int
    order: dict[str, Any]


class WSBalanceUpdate(BaseModel):
    """余额更新WebSocket消息"""

    event_type: str
    event_time: int
    balances: dict[str, Any]


class WSMarginCall(BaseModel):
    """追加保证金通知"""

    event_type: str
    event_time: int
    positions: list[dict[str, Any]]


class WSMessage(BaseModel):
    """通用WebSocket消息"""

    stream: Optional[str] = None
    data: Optional[dict[str, Any]] = None


class WSSubscribeRequest(BaseModel):
    """订阅请求"""

    method: str = "SUBSCRIBE"
    params: list[str]
    id: int


class WSUnsubscribeRequest(BaseModel):
    """取消订阅请求"""

    method: str = "UNSUBSCRIBE"
    params: list[str]
    id: int


class WSListSubscriptionsRequest(BaseModel):
    """列出订阅请求"""

    method: str = "LIST_SUBSCRIPTIONS"
    id: int


class WSResponse(BaseModel):
    """WebSocket响应"""

    result: Optional[Any] = None
    id: int
    code: Optional[int] = None
    msg: Optional[str] = None
