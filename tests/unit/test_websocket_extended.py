"""扩展的WebSocket单元测试"""

import pytest
import asyncio
import json
from unittest.mock import AsyncMock, patch, MagicMock
from asterdex import WebSocketClient, Network
from asterdex.exceptions import (
    WebSocketError,
    WSConnectionError,
    WSTimeoutError,
    WSReconnectError,
)


class TestWebSocketExtended:
    """扩展WebSocket测试"""

    def test_client_init_default_values(self):
        ws = WebSocketClient()
        assert ws.ping_interval == 60
        assert ws._running is False
        assert ws._reconnect_attempts == 0
        assert ws._max_reconnect == 20
        assert ws._subscriptions == {}
        assert ws._callbacks == {}
        assert ws._message_id == 0

    def test_client_init_custom_values(self):
        ws = WebSocketClient(
            network=Network.MAINNET,
            ping_interval=30,
        )
        assert ws.ping_interval == 30
        assert ws.ws_url == Network.MAINNET.ws_url

    def test_connect_already_connected(self):
        ws = WebSocketClient()
        ws._running = True
        ws._ws = MagicMock()

        assert ws.is_connected is True

    @pytest.mark.asyncio
    async def test_connect_timeout(self):
        ws = WebSocketClient()

        with patch("asterdex.websocket.client.websockets.connect") as mock_connect:
            mock_connect.side_effect = asyncio.TimeoutError()

            with pytest.raises(WSTimeoutError):
                await ws.connect()

    @pytest.mark.asyncio
    async def test_disconnect(self):
        ws = WebSocketClient()
        mock_ws = AsyncMock()
        ws._ws = mock_ws
        ws._running = True

        await ws.disconnect()

        assert ws._running is False
        assert ws._ws is None
        mock_ws.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_disconnect_no_ws(self):
        ws = WebSocketClient()
        ws._running = True

        await ws.disconnect()

        assert ws._running is False

    @pytest.mark.asyncio
    async def test_handle_message_valid_json(self):
        ws = WebSocketClient()

        @ws.on("btcusdt@bookTicker")
        async def handler(data):
            pass

        message = json.dumps(
            {
                "stream": "btcusdt@bookTicker",
                "data": {"s": "BTCUSDT", "b": "50000.00", "a": "50001.00"},
            }
        )

        await ws._handle_message(message)

    @pytest.mark.asyncio
    async def test_handle_message_invalid_json(self):
        ws = WebSocketClient()

        message = "invalid json {"

        await ws._handle_message(message)

    @pytest.mark.asyncio
    async def test_handle_message_subscription_confirm(self):
        ws = WebSocketClient()

        message = json.dumps({"result": None, "id": 1})

        await ws._handle_message(message)

    @pytest.mark.asyncio
    async def test_handle_message_no_stream(self):
        ws = WebSocketClient()

        message = json.dumps({"data": {"s": "BTCUSDT"}})

        await ws._handle_message(message)

    @pytest.mark.asyncio
    async def test_handle_message_callback_error(self):
        ws = WebSocketClient()

        @ws.on("btcusdt@bookTicker")
        async def handler(data):
            raise ValueError("test error")

        message = json.dumps({"stream": "btcusdt@bookTicker", "data": {"s": "BTCUSDT"}})

        await ws._handle_message(message)

    @pytest.mark.asyncio
    async def test_subscribe_success(self):
        ws = WebSocketClient()
        mock_ws = AsyncMock()
        ws._ws = mock_ws
        ws._running = True

        result = await ws.subscribe("btcusdt@bookTicker")

        assert result is True
        mock_ws.send.assert_called_once()

        sent_data = json.loads(mock_ws.send.call_args[0][0])
        assert sent_data["method"] == "SUBSCRIBE"
        assert "btcusdt@bookTicker" in sent_data["params"]

    @pytest.mark.asyncio
    async def test_unsubscribe_success(self):
        ws = WebSocketClient()
        mock_ws = AsyncMock()
        ws._ws = mock_ws
        ws._running = True
        ws._subscriptions = {"btcusdt@bookTicker": {"btcusdt@bookTicker"}}

        result = await ws.unsubscribe("btcusdt@bookTicker")

        assert result is True
        mock_ws.send.assert_called_once()

    @pytest.mark.asyncio
    async def test_resubscribe(self):
        ws = WebSocketClient()
        ws._subscriptions = {"test@stream": {"test@stream"}}

        with patch.object(ws, "subscribe", new_callable=AsyncMock) as mock_sub:
            await ws._resubscribe({"test@stream"})
            mock_sub.assert_called_once_with("test@stream")

    @pytest.mark.asyncio
    async def test_handle_disconnect_not_running(self):
        ws = WebSocketClient()
        ws._running = False

        await ws._handle_disconnect()

    @pytest.mark.asyncio
    async def test_handle_disconnect_with_reconnect(self):
        ws = WebSocketClient()
        ws._running = True
        ws._reconnect_attempts = 0

        with (
            patch.object(ws, "connect", new_callable=AsyncMock),
            patch.object(ws, "subscribe", new_callable=AsyncMock),
        ):
            await ws._handle_disconnect()

    @pytest.mark.asyncio
    async def test_handle_disconnect_max_attempts(self):
        ws = WebSocketClient()
        ws._running = True
        ws._reconnect_attempts = 10
        ws._max_reconnect = 10

        error_callback = AsyncMock()
        ws._callbacks["__error__"] = [error_callback]

        await ws._handle_disconnect()

        assert ws._running is False


class TestWebSocketClientProperties:
    """WebSocket客户端属性测试"""

    def test_is_connected_when_running(self):
        ws = WebSocketClient()
        ws._running = True
        ws._ws = MagicMock()

        assert ws.is_connected is True

    def test_is_connected_when_not_running(self):
        ws = WebSocketClient()
        ws._running = False

        assert ws.is_connected is False

    def test_is_connected_no_ws(self):
        ws = WebSocketClient()
        ws._running = True
        ws._ws = None

        assert ws.is_connected is False


class TestWebSocketCallbacks:
    """WebSocket回调测试"""

    def test_multiple_callbacks_same_stream(self):
        ws = WebSocketClient()

        @ws.on("test@stream")
        async def handler1(data):
            pass

        @ws.on("test@stream")
        async def handler2(data):
            pass

        assert len(ws._callbacks["test@stream"]) == 2

    def test_callback_decorator_returns_function(self):
        ws = WebSocketClient()

        @ws.on("test@stream")
        async def handler(data):
            pass

        assert callable(handler)


class TestWebSocketNetwork:
    """WebSocket网络配置测试"""

    def test_testnet_url(self):
        ws = WebSocketClient(network=Network.TESTNET)
        assert "testnet" in ws.ws_url

    def test_mainnet_url(self):
        ws = WebSocketClient(network=Network.MAINNET)
        assert "testnet" not in ws.ws_url.lower()

    def test_default_network(self):
        from asterdex.constants import DEFAULT_NETWORK

        ws = WebSocketClient(network=DEFAULT_NETWORK)
        assert ws.ws_url == DEFAULT_NETWORK.ws_url
