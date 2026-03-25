import pytest
from pydantic import ValidationError
from asterdex.models.base import OrderBook, Trade, Ticker24h, Balance, Position, Order
from asterdex.models.ws import WSBookTicker, WSKline


class TestOrderBook:
    def test_orderbook_creation(self):
        ob = OrderBook(
            last_update_id=1, bids=[["100", "1"], ["99", "2"]], asks=[["101", "1"], ["102", "2"]]
        )
        assert ob.last_update_id == 1
        assert len(ob.bids) == 2

    def test_best_bid(self):
        ob = OrderBook(last_update_id=1, bids=[["100", "1"], ["99", "2"]], asks=[["101", "1"]])
        assert ob.best_bid == ("100", "1")

    def test_best_ask(self):
        ob = OrderBook(last_update_id=1, bids=[["100", "1"]], asks=[["101", "1"], ["102", "2"]])
        assert ob.best_ask == ("101", "1")

    def test_empty_orderbook(self):
        ob = OrderBook(last_update_id=0, bids=[], asks=[])
        assert ob.best_bid is None
        assert ob.best_ask is None


class TestTrade:
    def test_trade_creation(self):
        trade = Trade(
            id=123,
            price="50000",
            qty="0.5",
            quote_qty="25000",
            time=1234567890,
            is_buyer_maker=True,
        )
        assert trade.price_float == 50000.0
        assert trade.qty_float == 0.5

    def test_trade_float_conversion(self):
        trade = Trade(
            id=1, price="123.45", qty="0.001", quote_qty="0.12345", time=1, is_buyer_maker=False
        )
        assert trade.price_float == 123.45
        assert trade.qty_float == 0.001


class TestBalance:
    def test_balance_creation(self):
        bal = Balance(asset="BTC", free="1.0", locked="0.5")
        assert bal.free_float == 1.0
        assert bal.locked_float == 0.5

    def test_balance_total(self):
        bal = Balance(asset="BTC", free="1.0", locked="0.5")
        assert bal.total_float == 1.5


class TestPosition:
    def test_position_creation(self):
        pos = Position(
            symbol="BTCUSDT",
            position_side="LONG",
            position_amount="1.0",
            entry_price="45000",
            mark_price="50000",
            leverage="10",
            unrealized_pnl="5000",
            margin="1000",
        )
        assert pos.symbol == "BTCUSDT"
        assert pos.leverage == "10"


class TestOrder:
    def test_order_creation(self):
        order = Order(
            order_id=123456,
            symbol="BTCUSDT",
            side="BUY",
            type="LIMIT",
            price="50000",
            orig_qty="0.1",
            executed_qty="0.05",
            avg_price="50000",
            status="PARTIALLY_FILLED",
            time_in_force="GTC",
            order_type="LIMIT",
            reduce_only=False,
            close_position=False,
            time=1234567890,
            update_time=1234567890,
        )
        assert order.order_id == 123456
        assert order.price_float == 50000.0


class TestWSModels:
    def test_ws_book_ticker(self):
        ticker = WSBookTicker(
            update_id=1,
            event_time=1234567890,
            transaction_time=1234567890,
            symbol="BTCUSDT",
            bid_price="50000",
            bid_qty="1",
            ask_price="50001",
            ask_qty="0.5",
        )
        assert ticker.bid_price == "50000"
        assert ticker.symbol == "BTCUSDT"
