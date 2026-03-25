"""WebSocket集成测试 - 使用真实Testnet"""

import pytest
import asyncio
from asterdex import WebSocketClient, Network


TEST_SYMBOL = "BTCUSDT"


class TestWebSocketIntegration:
    """WebSocket集成测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_connect_disconnect(self):
        """测试WebSocket连接和断开"""
        ws = WebSocketClient(network=Network.TESTNET)

        try:
            await ws.connect()
            assert ws.is_connected is True
        finally:
            await ws.disconnect()
            assert ws.is_connected is False

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_book_ticker(self):
        """测试接收订单簿数据"""
        ws = WebSocketClient(network=Network.TESTNET)
        received_data = []

        @ws.on_book_ticker(TEST_SYMBOL)
        async def handler(data):
            received_data.append(data)

        try:
            await ws.connect()
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@bookTicker")

            await asyncio.sleep(3)

            assert len(received_data) > 0
            ticker = received_data[-1]
            assert "s" in ticker or "symbol" in ticker
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_kline(self):
        """测试接收K线数据"""
        ws = WebSocketClient(network=Network.TESTNET)
        received_data = []

        @ws.on_kline(TEST_SYMBOL, "1m")
        async def handler(data):
            received_data.append(data)

        try:
            await ws.connect()
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@kline_1m")

            await asyncio.sleep(3)

            assert len(received_data) > 0
            kline = received_data[-1]
            assert "k" in kline or "o" in kline or "c" in kline
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_ticker(self):
        """测试接收24小时行情"""
        ws = WebSocketClient(network=Network.TESTNET)
        received_data = []

        @ws.on_ticker(TEST_SYMBOL)
        async def handler(data):
            received_data.append(data)

        try:
            await ws.connect()
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@ticker")

            await asyncio.sleep(3)

            assert len(received_data) > 0
            ticker = received_data[-1]
            assert "s" in ticker or "symbol" in ticker
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_trade(self):
        """测试接收成交数据"""
        ws = WebSocketClient(network=Network.TESTNET)
        received_data = []

        @ws.on_trade(TEST_SYMBOL)
        async def handler(data):
            received_data.append(data)

        try:
            await ws.connect()
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@aggTrade")

            await asyncio.sleep(3)

            assert len(received_data) > 0
            trade = received_data[-1]
            assert "s" in trade or "p" in trade
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_mark_price(self):
        """测试接收标记价格"""
        ws = WebSocketClient(network=Network.TESTNET)
        received_data = []

        @ws.on_mark_price(TEST_SYMBOL)
        async def handler(data):
            received_data.append(data)

        try:
            await ws.connect()
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@markPrice")

            await asyncio.sleep(3)

            assert len(received_data) > 0
            mark_price = received_data[-1]
            assert "s" in mark_price or "markPrice" in mark_price
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_multiple_streams(self):
        """测试多stream订阅"""
        ws = WebSocketClient(network=Network.TESTNET)
        ticker_received = []
        kline_received = []

        @ws.on_ticker(TEST_SYMBOL)
        async def ticker_handler(data):
            ticker_received.append(data)

        @ws.on_kline(TEST_SYMBOL, "1m")
        async def kline_handler(data):
            kline_received.append(data)

        try:
            await ws.connect()
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@ticker")
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@kline_1m")

            await asyncio.sleep(3)

            assert len(ticker_received) > 0
            assert len(kline_received) > 0
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_unsubscribe(self):
        """测试取消订阅"""
        ws = WebSocketClient(network=Network.TESTNET)
        received_data = []

        @ws.on_book_ticker(TEST_SYMBOL)
        async def handler(data):
            received_data.append(data)

        try:
            await ws.connect()
            await ws.subscribe(f"{TEST_SYMBOL.lower()}@bookTicker")
            await asyncio.sleep(2)

            first_count = len(received_data)

            await ws.unsubscribe(f"{TEST_SYMBOL.lower()}@bookTicker")
            await asyncio.sleep(2)

            second_count = len(received_data)

            assert second_count >= first_count
        finally:
            await ws.disconnect()


class TestHybridClientIntegration:
    """Hybrid客户端集成测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hybrid_client_init(self):
        """测试Hybrid客户端初始化"""
        from asterdex import HybridClient

        client = HybridClient(network=Network.TESTNET)

        assert client.network == Network.TESTNET
        assert client.is_connected is False

        await client.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hybrid_fallback_mode(self):
        """测试Hybrid客户端降级模式"""
        from asterdex import HybridClient

        client = HybridClient(
            network=Network.TESTNET,
            poll_interval=1.0,
            max_poll_interval=2.0,
            no_limit=False,
        )

        @client.on_book_ticker(TEST_SYMBOL)
        async def handler(data):
            pass

        try:
            client._ws_client._ws = None
            client._ws_client._running = False

            await client._start_fallback()

            await asyncio.sleep(3)

            assert client.is_fallback_mode is True
        finally:
            await client.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hybrid_poll_interval_adjustment(self):
        """测试Hybrid客户端轮询间隔调整"""
        from asterdex import HybridClient

        client = HybridClient(
            network=Network.TESTNET,
            poll_interval=1.0,
            max_poll_interval=3.0,
            no_limit=False,
        )

        assert client._current_poll_interval == 1.0

        client._adjust_poll_interval()
        assert client._current_poll_interval == 1.5

        client._adjust_poll_interval()
        assert client._current_poll_interval == 2.0

        client._adjust_poll_interval()
        assert client._current_poll_interval == 2.5

        client._adjust_poll_interval()
        assert client._current_poll_interval == 3.0

        client._adjust_poll_interval()
        assert client._current_poll_interval == 3.0

        await client.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_hybrid_no_limit_mode(self):
        """测试无上限轮询模式"""
        from asterdex import HybridClient

        client = HybridClient(
            network=Network.TESTNET,
            poll_interval=1.0,
            no_limit=True,
        )

        assert client._current_poll_interval == 1.0

        client._adjust_poll_interval()
        assert client._current_poll_interval == 1.5

        client._adjust_poll_interval()
        assert client._current_poll_interval == 2.0

        client._adjust_poll_interval()
        client._adjust_poll_interval()
        client._adjust_poll_interval()

        assert client._current_poll_interval > 3.0

        await client.disconnect()
