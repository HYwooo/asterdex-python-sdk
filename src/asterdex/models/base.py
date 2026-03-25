"""基础模型定义"""

from typing import Any, Generic, Optional, TypeVar

from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel):
    """API响应基类"""

    model_config = ConfigDict(str_strip_whitespace=True)


class ListResponse(BaseModel, Generic[T]):
    """列表响应基类"""

    items: list[T]


class TimestampMixin(BaseModel):
    """时间戳混入类"""

    time: Optional[int] = None
    event_time: Optional[int] = None


class OrderBookEntry(BaseModel):
    """订单簿条目"""

    price: str
    qty: str

    @property
    def price_float(self) -> float:
        return float(self.price)

    @property
    def qty_float(self) -> float:
        return float(self.qty)


class OrderBook(BaseModel):
    """订单簿"""

    last_update_id: int
    bids: list[list[str]]
    asks: list[list[str]]

    @property
    def best_bid(self) -> Optional[tuple[str, str]]:
        if self.bids:
            return (self.bids[0][0], self.bids[0][1])
        return None

    @property
    def best_ask(self) -> Optional[tuple[str, str]]:
        if self.asks:
            return (self.asks[0][0], self.asks[0][1])
        return None


class Trade(BaseModel):
    """成交记录"""

    id: int
    price: str
    qty: str
    quote_qty: str
    time: int
    is_buyer_maker: bool

    @property
    def price_float(self) -> float:
        return float(self.price)

    @property
    def qty_float(self) -> float:
        return float(self.qty)


class Ticker24h(BaseModel):
    """24小时行情"""

    symbol: str
    price_change: str
    price_change_percent: str
    weighted_avg_price: str
    prev_close_price: str
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


class MarkPrice(BaseModel):
    """标记价格"""

    symbol: str
    mark_price: str
    index_price: str
    estimated_settle_price: str
    last_funding_rate: str
    next_funding_time: int
    interest_rate: str
    time: int


class Kline(BaseModel):
    """K线数据"""

    open_time: int
    open: str
    high: str
    low: str
    close: str
    volume: str
    close_time: int
    quote_volume: str
    trade_count: int
    taker_buy_base_volume: str
    taker_buy_quote_volume: str


class ExchangeSymbol(BaseModel):
    """交易对信息"""

    symbol: str
    pair: str
    contract_type: str
    delivery_date: int
    onboard_date: int
    status: str
    maint_margin_percent: str
    required_margin_percent: str
    base_asset: str
    quote_asset: str
    margin_asset: str
    price_precision: int
    quantity_precision: int
    base_asset_precision: int
    quote_precision: int
    underlying_type: str
    underlying_sub_type: list[str]
    settle_plan: int
    trigger_protect: str
    filters: list[dict[str, Any]]
    order_types: list[str]
    time_in_force: list[str]
    liquidation_fee: str
    market_take_bound: str


class ExchangeInfo(BaseModel):
    """交易所信息"""

    exchange_filters: list[Any]
    rate_limits: list[dict[str, Any]]
    server_time: int
    assets: list[dict[str, Any]]
    symbols: list[ExchangeSymbol]
    timezone: str


class Balance(BaseModel):
    """账户余额"""

    asset: str
    free: str
    locked: str

    @property
    def free_float(self) -> float:
        return float(self.free)

    @property
    def locked_float(self) -> float:
        return float(self.locked)

    @property
    def total_float(self) -> float:
        return self.free_float + self.locked_float


class Position(BaseModel):
    """持仓信息"""

    symbol: str
    position_side: str
    position_amount: str
    entry_price: str
    mark_price: str
    leverage: str
    unrealized_pnl: str
    margin: str
    liquidation_price: Optional[str] = None
    margin_type: Optional[str] = None


class Order(BaseModel):
    """订单信息"""

    order_id: int
    symbol: str
    side: str
    type: str
    position_side: Optional[str] = None
    price: str
    orig_qty: str
    executed_qty: str
    avg_price: str
    status: str
    time_in_force: str
    order_type: str
    reduce_only: bool
    close_position: bool
    time: int
    update_time: int

    @property
    def price_float(self) -> float:
        return float(self.price)

    @property
    def orig_qty_float(self) -> float:
        return float(self.orig_qty)

    @property
    def executed_qty_float(self) -> float:
        return float(self.executed_qty)


class OrderRequest(BaseModel):
    """订单请求"""

    symbol: str
    side: str
    type: str
    quantity: str
    price: Optional[str] = None
    time_in_force: Optional[str] = "GTC"
    position_side: Optional[str] = None
    reduce_only: Optional[bool] = None
    new_order_resp_type: Optional[str] = None
    stop_price: Optional[str] = None
    activation_price: Optional[str] = None
    callback_rate: Optional[str] = None


class AccountInfo(BaseModel):
    """账户信息"""

    total_wallet_balance: str
    total_unrealized_pnl: str
    total_margin_balance: str
    available_balance: str
    positions: list[Position]
    balances: list[Balance]


class FundingRate(BaseModel):
    """资金费率"""

    symbol: str
    funding_rate: str
    funding_time: int
