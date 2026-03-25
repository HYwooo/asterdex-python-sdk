"""Spot WebSocket测试"""

import asyncio
import sys
from asterdex import WebSocketClient, Network, ProductType


async def test_spot_websocket():
    """测试Spot WebSocket"""
    print("=" * 50)
    print("Testing Spot Mainnet WebSocket")
    print("=" * 50)

    ws = WebSocketClient(
        network=Network.MAINNET,
        product=ProductType.SPOT,
        use_combined=True,
    )

    received_data = []

    @ws.on_book_ticker("BTCUSDT")
    async def on_book_ticker(data):
        print(f"bookTicker: {data}")
        received_data.append(data)

    @ws.on_ticker("BTCUSDT")
    async def on_ticker(data):
        print(f"ticker: {data.get('s')}, price: {data.get('c')}")
        received_data.append(data)

    @ws.on_kline("BTCUSDT", "1m")
    async def on_kline(data):
        print(f"kline: {data.get('s')}, close: {data.get('c')}")
        received_data.append(data)

    @ws.on_trade("BTCUSDT")
    async def on_trade(data):
        print(f"trade: {data.get('s')}, price: {data.get('p')}, qty: {data.get('q')}")
        received_data.append(data)

    try:
        print(f"Connecting to {ws.ws_url}...")
        await ws.connect()
        print(f"Connected! URL: {ws.ws_url}")

        print("Subscribing to streams...")
        await ws.subscribe("btcusdt@bookTicker")
        await ws.subscribe("btcusdt@ticker")
        await ws.subscribe("btcusdt@kline_1m")
        await ws.subscribe("btcusdt@aggTrade")

        print("Waiting for data (5s)...")
        await asyncio.sleep(5)

        print(f"\nTotal messages received: {len(received_data)}")

        if received_data:
            print("SUCCESS: WebSocket is working!")
        else:
            print("FAIL: No data received")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await ws.disconnect()
        print("Disconnected")


async def test_futures_websocket():
    """测试Futures WebSocket (使用combined stream)"""
    print("\n" + "=" * 50)
    print("Testing Futures Mainnet WebSocket (Combined)")
    print("=" * 50)

    ws = WebSocketClient(
        network=Network.MAINNET,
        product=ProductType.FUTURES,
        use_combined=True,
    )

    received_data = []

    @ws.on_book_ticker("BTCUSDT")
    async def on_book_ticker(data):
        print(f"bookTicker: {data.get('s')}, bid: {data.get('b')}, ask: {data.get('a')}")
        received_data.append(data)

    @ws.on_ticker("BTCUSDT")
    async def on_ticker(data):
        print(f"ticker: {data.get('s')}, price: {data.get('c')}")
        received_data.append(data)

    try:
        print(f"Connecting to {ws.base_url}/stream...")
        await ws.connect()
        print(f"Connected! URL: {ws.ws_url}")

        print("Subscribing to streams...")
        await ws.subscribe("btcusdt@bookTicker")
        await ws.subscribe("btcusdt@ticker")

        print("Waiting for data (5s)...")
        await asyncio.sleep(5)

        print(f"\nTotal messages received: {len(received_data)}")

        if received_data:
            print("SUCCESS: WebSocket is working!")
        else:
            print("FAIL: No data received")

    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
    finally:
        await ws.disconnect()
        print("Disconnected")


async def main():
    """运行所有测试"""
    await test_spot_websocket()
    await test_futures_websocket()


if __name__ == "__main__":
    asyncio.run(main())
