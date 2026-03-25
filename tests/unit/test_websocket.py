import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from asterdex import WebSocketClient, Network
from asterdex.exceptions import WebSocketError


class TestWebSocketClient:
    def test_client_initialization(self):
        ws = WebSocketClient()
        assert ws.ws_url == Network.TESTNET.ws_url

    def test_client_with_mainnet(self):
        ws = WebSocketClient(network=Network.MAINNET)
        assert ws.ws_url == Network.MAINNET.ws_url

    def test_is_connected_false_by_default(self):
        ws = WebSocketClient()
        assert ws.is_connected is False

    @pytest.mark.asyncio
    async def test_connect_sets_running(self):
        ws = WebSocketClient()
        ws._running = True
        ws._ws = MagicMock()

        assert ws.is_connected is True

    def test_on_decorator(self):
        ws = WebSocketClient()

        @ws.on("test_stream")
        async def handler(data):
            pass

        assert "test_stream" in ws._callbacks

    def test_on_book_ticker(self):
        ws = WebSocketClient()

        @ws.on_book_ticker("BTCUSDT")
        async def handler(data):
            pass

        assert "btcusdt@bookTicker" in ws._callbacks

    def test_on_kline(self):
        ws = WebSocketClient()

        @ws.on_kline("BTCUSDT", "1m")
        async def handler(data):
            pass

        assert "btcusdt@kline_1m" in ws._callbacks

    def test_on_ticker(self):
        ws = WebSocketClient()

        @ws.on_ticker("BTCUSDT")
        async def handler(data):
            pass

        assert "btcusdt@ticker" in ws._callbacks

    def test_on_trade(self):
        ws = WebSocketClient()

        @ws.on_trade("BTCUSDT")
        async def handler(data):
            pass

        assert "btcusdt@aggTrade" in ws._callbacks

    def test_on_mark_price(self):
        ws = WebSocketClient()

        @ws.on_mark_price("BTCUSDT")
        async def handler(data):
            pass

        assert "btcusdt@markPrice" in ws._callbacks

    def test_on_error(self):
        ws = WebSocketClient()

        async def error_handler(error):
            pass

        ws.on_error(error_handler)
        assert "__error__" in ws._callbacks

    @pytest.mark.asyncio
    async def test_subscribe_without_connection_raises(self):
        ws = WebSocketClient()
        with pytest.raises(WebSocketError):
            await ws.subscribe("test@stream")

    @pytest.mark.asyncio
    async def test_unsubscribe_without_connection_raises(self):
        ws = WebSocketClient()
        with pytest.raises(WebSocketError):
            await ws.unsubscribe("test@stream")
