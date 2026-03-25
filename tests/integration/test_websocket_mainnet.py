"""WebSocket集成测试 - Mainnet生产环境"""

import pytest
import asyncio
from asterdex import WebSocketClient, Network


TEST_SYMBOL = "BTCUSDT"


class TestWebSocketMainnet:
    """WebSocket Mainnet集成测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_connect_disconnect(self):
        """测试WebSocket连接和断开"""
        ws = WebSocketClient(network=Network.MAINNET)

        try:
            await ws.connect()
            assert ws.is_connected is True
            print(f"✅ Connected to {ws.ws_url}")
        finally:
            await ws.disconnect()
            assert ws.is_connected is False
            print("✅ Disconnected")

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_book_ticker(self):
        """测试接收订单簿数据"""
        ws = WebSocketClient(network=Network.MAINNET)
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
            print(f"✅ bookTicker: {len(received_data)} messages, last: {ticker.get('s', 'N/A')}")
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_kline(self):
        """测试接收K线数据"""
        ws = WebSocketClient(network=Network.MAINNET)
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
            print(f"✅ kline: {len(received_data)} messages")
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_ticker(self):
        """测试接收24小时行情"""
        ws = WebSocketClient(network=Network.MAINNET)
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
            print(f"✅ ticker: {len(received_data)} messages, last: {ticker.get('s', 'N/A')}")
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_trade(self):
        """测试接收成交数据"""
        ws = WebSocketClient(network=Network.MAINNET)
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
            print(f"✅ trade: {len(received_data)} messages")
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_mark_price(self):
        """测试接收标记价格"""
        ws = WebSocketClient(network=Network.MAINNET)
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
            print(
                f"✅ markPrice: {len(received_data)} messages, last: {mark_price.get('s', 'N/A')}"
            )
        finally:
            await ws.disconnect()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_websocket_multiple_streams(self):
        """测试多stream订阅"""
        ws = WebSocketClient(network=Network.MAINNET)
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
            print(
                f"✅ multiple streams: ticker={len(ticker_received)}, kline={len(kline_received)}"
            )
        finally:
            await ws.disconnect()


class TestRESTMainnet:
    """REST API Mainnet集成测试"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_ping(self):
        """测试连接"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.ping()
            print(f"✅ Ping: {result}")
            assert result == {} or "code" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_time(self):
        """测试时间"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.get_time()
            print(f"✅ Server time: {result.get('serverTime')}")
            assert "serverTime" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_order_book(self):
        """测试订单簿"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.get_order_book(TEST_SYMBOL)
            print(
                f"✅ Order book: {len(result.get('bids', []))} bids, {len(result.get('asks', []))} asks"
            )
            assert "bids" in result and "asks" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_klines(self):
        """测试K线"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.get_klines(TEST_SYMBOL, "1m", limit=5)
            print(f"✅ Klines: {len(result)} candles")
            assert len(result) > 0
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_ticker_24h(self):
        """测试24小时行情"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.get_ticker_24h(TEST_SYMBOL)
            print(f"✅ Ticker: {result.get('symbol')}, price: {result.get('lastPrice')}")
            assert "symbol" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_mark_price(self):
        """测试标记价格"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.get_mark_price(TEST_SYMBOL)
            print(f"✅ Mark price: {result.get('symbol')}, price: {result.get('markPrice')}")
            assert "markPrice" in result
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_balance(self):
        """测试余额查询"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.get_balance()
            print(f"✅ Balance: {len(result)} assets")
            assert len(result) > 0
        finally:
            await client.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_get_positions(self):
        """测试持仓查询"""
        from asterdex import Client

        client = Client.v3(
            user="0xC8C4581b24eDFa7d66Ae33D00616ffecC9d2AC7F",
            signer="0x5C1757c09F16bC4b429D5CcaE68154A771a469f6",
            private_key="0x12cd6a1206441eaf5afd823596a9a2b88407ed1667960650ef4897d8769480de",
            network=Network.MAINNET,
        )
        try:
            result = await client.get_position()
            print(f"✅ Positions: {len(result)} positions")
        finally:
            await client.close()
