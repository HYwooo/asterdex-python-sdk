"""WebSocket客户端

支持自动重连、心跳、stream订阅、REST Fallback等功能。
"""

import asyncio
import json
from typing import Callable, Optional, Union

import aiohttp
import websockets
from websockets import WebSocketClientProtocol
from websockets.exceptions import (
    ConnectionClosed,
    InvalidURI,
)

from ..constants import (
    DEFAULT_NETWORK,
    WS_MAX_RECONNECT_ATTEMPTS,
    WS_PING_INTERVAL,
    WS_RECONNECT_BASE_DELAY,
    WS_RECONNECT_MAX_DELAY,
    Network,
    ProductType,
)
from ..exceptions import (
    ValidationError,
    WebSocketError,
    WSConnectionError,
    WSReconnectError,
    WSTimeoutError,
)
from ..logging_config import get_logger

logger = get_logger(__name__)


class WebSocketClient:
    """WebSocket客户端

    支持:
    - 自动重连
    - 心跳保活
    - Stream订阅/取消
    - 回调事件处理
    - Futures/Spot产品类型
    - Combined Stream格式

    Usage:
        from asterdex import WebSocketClient, Network, ProductType

        # Futures (默认)
        ws = WebSocketClient(network=Network.TESTNET)

        # Spot
        ws = WebSocketClient(network=Network.MAINNET, product=ProductType.SPOT)

        @ws.on_book_ticker("BTCUSDT")
        async def on_ticker(ticker):
            print(f"买一: {ticker.bid_price}, 卖一: {ticker.ask_price}")

        await ws.connect()
        await asyncio.sleep(60)
        await ws.disconnect()
    """

    def __init__(
        self,
        network: Network = DEFAULT_NETWORK,
        product: ProductType = ProductType.FUTURES,
        ping_interval: int = WS_PING_INTERVAL,
        use_combined: bool = True,
        proxy: Optional[str] = None,
    ):
        self.network = network
        self.product = product
        self.base_url = network.get_ws_url(product)
        self.use_combined = use_combined
        self.ping_interval = ping_interval
        self.ws_url = self.base_url
        self._proxy = self._validate_proxy(proxy)
        self._ws: Optional[WebSocketClientProtocol] = None
        self._ws_session: Optional[aiohttp.ClientSession] = None
        self._using_aiohttp_ws = False
        self._running = False
        self._reconnect_attempts = 0
        self._max_reconnect = WS_MAX_RECONNECT_ATTEMPTS
        self._subscriptions: dict[str, set[str]] = {}
        self._callbacks: dict[str, list[Callable]] = {}
        self._message_id = 0
        self._lock = asyncio.Lock()

    def _validate_proxy(self, proxy: Optional[str]) -> Optional[str]:
        """验证代理URL格式"""
        if proxy is None:
            return None

        proxy_lower = proxy.lower()
        if proxy_lower.startswith(("http://", "https://")):
            return proxy
        else:
            raise ValidationError(
                f"不支持的代理类型: {proxy}. 支持的类型: http://, https://",
                field="proxy",
            )

    async def _create_proxy_session(self) -> aiohttp.ClientSession:
        """创建带代理的aiohttp会话"""
        if self._ws_session is None or self._ws_session.closed:
            if self._proxy:
                self._ws_session = aiohttp.ClientSession(proxy=self._proxy)
            else:
                self._ws_session = aiohttp.ClientSession()
        return self._ws_session

    async def connect(self, streams: Optional[list[str]] = None) -> None:
        """建立WebSocket连接

        Args:
            streams: 可选的初始订阅stream列表

        Raises:
            WSConnectionError: 连接失败
        """
        if self._running and self._ws:
            logger.debug("WebSocket already connected")
            return

        try:
            if self.use_combined:
                self.ws_url = f"{self.base_url}/stream"
            else:
                self.ws_url = f"{self.base_url}/ws"

            logger.info(
                f"[WS] Connecting to {self.ws_url} (product={self.product.value}, proxy={self._proxy})"
            )

            if self._proxy:
                session = await self._create_proxy_session()
                ws = await session.ws_connect(self.ws_url)
                self._ws = ws
                self._using_aiohttp_ws = True
            else:
                self._ws = await websockets.connect(
                    self.ws_url,
                    ping_interval=self.ping_interval,
                    ping_timeout=30,
                )
                self._using_aiohttp_ws = False

            self._running = True
            self._reconnect_attempts = 0
            logger.info(f"[WS] Connected to {self.ws_url}")

            asyncio.create_task(self._receive_loop())

            if streams:
                for stream in streams:
                    await self.subscribe(stream)

        except InvalidURI as e:
            logger.error(f"[WS] Invalid WebSocket URI: {self.ws_url}")
            raise WSConnectionError(f"Invalid URI: {e}") from e
        except ConnectionClosed as e:
            logger.warning(f"[WS] Connection closed during connect: {e}")
            raise WSConnectionError(f"Connection failed: {e}") from e
        except asyncio.TimeoutError as e:
            logger.error(f"[WS] Connection timeout: {self.ws_url}")
            raise WSTimeoutError(f"Connection timeout: {e}") from e
        except Exception as e:
            logger.error(f"[WS] Connection failed: {type(e).__name__}: {e}")
            raise WSConnectionError(f"Connection failed: {e}") from e

    async def disconnect(self) -> None:
        """断开WebSocket连接"""
        self._running = False
        if self._ws:
            await self._ws.close()
            self._ws = None
        if self._ws_session and not self._ws_session.closed:
            await self._ws_session.close()
            self._ws_session = None
        logger.info("WebSocket已断开")

    async def _receive_loop(self) -> None:
        """接收消息循环

        处理所有接收到的消息，包括异常处理和日志记录。
        """
        try:
            async for message in self._ws:  # type: ignore
                if not self._running:
                    logger.debug("[WS] Receive loop stopped (not running)")
                    break
                if self._using_aiohttp_ws:
                    from aiohttp import WSMsgType

                    if message.type in (WSMsgType.TEXT, WSMsgType.BINARY):
                        msg_data = message.data
                    else:
                        continue
                else:
                    msg_data = message
                await self._handle_message(msg_data)
        except ConnectionClosed as e:
            logger.warning(f"[WS] Connection closed: code={e.code}, reason={e.reason}")
            await self._handle_disconnect()
        except asyncio.CancelledError:
            logger.info("[WS] Receive loop cancelled")
            self._running = False
        except Exception as e:
            logger.error(f"[WS] Receive error: {type(e).__name__}: {e}")
            await self._handle_disconnect()

    async def _handle_message(self, message: Union[str, bytes]) -> None:
        """处理接收到的消息

        包含完整的异常处理，确保不会因为单条消息问题导致整个连接崩溃。
        """
        try:
            if isinstance(message, bytes):
                message = message.decode("utf-8")

            logger.debug(f"[WS] Raw message: {message[:200]}")

            data = json.loads(message)

            if isinstance(data, dict):
                result = data.get("result")
                if result is None and "id" in data:
                    logger.debug(f"[WS] Subscription confirmed, id={data.get('id')}")
                    return

                stream = data.get("stream", "")
                payload = data.get("data", data)

                if not stream:
                    stream = payload.get("s", "").lower() if isinstance(payload, dict) else ""

                if not stream:
                    logger.debug(f"[WS] No stream in message: {message[:100]}")
                    return

                callback_data = payload
                if "@kline_" in stream:
                    callback_data = (
                        payload.get("k", payload) if isinstance(payload, dict) else payload
                    )

                if stream in self._callbacks:
                    for callback in self._callbacks[stream]:
                        try:
                            if asyncio.iscoroutinefunction(callback):
                                await callback(callback_data)
                            else:
                                callback(callback_data)
                        except Exception as e:
                            logger.error(
                                f"[WS] Callback error for {stream}: {type(e).__name__}: {e}"
                            )

        except json.JSONDecodeError as e:
            logger.warning(f"[WS] JSON parse failed: {e}, message: {message[:100]}")
        except KeyError as e:
            logger.debug(f"[WS] Missing key in message: {e}")
        except Exception as e:
            logger.error(f"[WS] Message handling error: {type(e).__name__}: {e}")

    async def _handle_disconnect(self) -> None:
        """处理连接断开

        快速重连逻辑:
        - 线性退避: 100ms, 200ms, 300ms... 最大2s
        - 最大重连次数: 20次
        - 重连成功后自动重新订阅
        """
        if not self._running:
            logger.debug("[WS] Ignoring disconnect (not running)")
            return

        self._running = False

        if self._reconnect_attempts < self._max_reconnect:
            delay = min(
                WS_RECONNECT_BASE_DELAY + (self._reconnect_attempts * 0.1), WS_RECONNECT_MAX_DELAY
            )
            logger.warning(
                f"[WS] Disconnected, reconnecting in {delay * 1000:.0f}ms "
                f"({self._reconnect_attempts + 1}/{self._max_reconnect})"
            )

            await asyncio.sleep(delay)
            self._reconnect_attempts += 1

            try:
                logger.info(f"[WS] Reconnect attempt {self._reconnect_attempts}...")
                await self.connect()

                # 重新订阅之前的streams
                if self._subscriptions:
                    logger.info(f"[WS] Resubscribing to {len(self._subscriptions)} streams...")
                    for streams in self._subscriptions.values():
                        for stream in streams:
                            try:
                                await self.subscribe(stream)
                            except Exception as e:
                                logger.error(f"[WS] Resubscribe failed for {stream}: {e}")

                logger.info("[WS] Reconnected successfully")

            except WSConnectionError as e:
                logger.error(f"[WS] Reconnect failed: {e}")
                await self._handle_disconnect()  # 递归尝试下一次
            except Exception as e:
                logger.error(f"[WS] Unexpected reconnect error: {type(e).__name__}: {e}")
                await self._handle_disconnect()
        else:
            logger.error(
                f"[WS] Max reconnection attempts ({self._max_reconnect}) reached. "
                "Stopping reconnection. Please manually reconnect."
            )
            self._running = False

            # 通知错误回调
            if self._callbacks.get("__error__"):
                error = WSReconnectError(
                    f"Max reconnection attempts reached ({self._max_reconnect})"
                )
                for cb in self._callbacks["__error__"]:
                    try:
                        await cb(error)
                    except Exception as e:
                        logger.error(f"[WS] Error callback failed: {e}")

    async def _resubscribe(self, streams: set[str]) -> None:
        """重新订阅streams"""
        for stream in streams:
            await self.subscribe(stream)

    async def _ws_send(self, data: str) -> None:
        """发送WebSocket消息（兼容websockets和aiohttp）"""
        if self._using_aiohttp_ws:
            await self._ws.send_str(data)
        else:
            await self._ws.send(data)

    async def subscribe(self, stream: str) -> bool:
        """订阅stream

        Args:
            stream: stream名称，例如 "btcusdt@bookTicker"

        Returns:
            是否成功订阅
        """
        if not self._ws or not self._running:
            logger.warning(f"[WS] Cannot subscribe: not connected (stream={stream})")
            return False

        try:
            self._message_id += 1
            msg = {
                "method": "SUBSCRIBE",
                "params": [stream],
                "id": self._message_id,
            }

            await self._ws_send(json.dumps(msg))
            logger.info(f"[WS] Subscribed to {stream}")

            self._subscriptions.setdefault(stream, set()).add(stream)
            return True

        except ConnectionClosed as e:
            logger.error(f"[WS] Subscribe failed (connection closed): {e}")
            raise WebSocketError("Subscribe failed: connection closed") from e
        except Exception as e:
            logger.error(f"[WS] Subscribe failed: {type(e).__name__}: {e}")
            raise WebSocketError(f"Subscribe failed: {e}") from e

    async def subscribe_batch(self, streams: list[str]) -> bool:
        """批量订阅多个stream

        Args:
            streams: stream名称列表，例如 ["btcusdt@ticker", "ethusdt@ticker"]

        Returns:
            是否成功订阅
        """
        if not self._ws or not self._running:
            logger.warning(f"[WS] Cannot subscribe batch: not connected")
            return False

        try:
            self._message_id += 1
            msg = {
                "method": "SUBSCRIBE",
                "params": streams,
                "id": self._message_id,
            }

            await self._ws_send(json.dumps(msg))
            logger.info(f"[WS] Batch subscribed to {len(streams)} streams")

            for stream in streams:
                self._subscriptions.setdefault(stream, set()).add(stream)
            return True

        except ConnectionClosed as e:
            logger.error(f"[WS] Batch subscribe failed (connection closed): {e}")
            raise WebSocketError("Batch subscribe failed: connection closed") from e
        except Exception as e:
            logger.error(f"[WS] Batch subscribe failed: {type(e).__name__}: {e}")
            raise WebSocketError(f"Batch subscribe failed: {e}") from e

    async def unsubscribe(self, stream: str) -> bool:
        """取消订阅stream

        Returns:
            是否成功取消订阅
        """
        if not self._ws or not self._running:
            logger.warning(f"[WS] Cannot unsubscribe: not connected (stream={stream})")
            return False

        try:
            self._message_id += 1
            msg = {
                "method": "UNSUBSCRIBE",
                "params": [stream],
                "id": self._message_id,
            }

            await self._ws_send(json.dumps(msg))
            logger.info(f"[WS] Unsubscribed from {stream}")

            if stream in self._subscriptions:
                self._subscriptions[stream].discard(stream)
            return True

        except Exception as e:
            logger.error(f"[WS] Unsubscribe failed: {type(e).__name__}: {e}")
            return False

    def on(self, stream: str) -> Callable:
        """注册回调装饰器

        Usage:
            @ws.on("btcusdt@bookTicker")
            async def handle(data):
                print(data)
        """

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            return func

        return decorator

    def on_book_ticker(self, symbol: str) -> Callable:
        """订阅订单簿更新

        Args:
            symbol: 交易对，例如 "BTCUSDT"
        """
        stream = f"{symbol.lower()}@bookTicker"

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            return func

        return decorator

    def on_kline(self, symbol: str, interval: str = "1m") -> Callable:
        """订阅K线数据

        Args:
            symbol: 交易对
            interval: K线间隔
        """
        stream = f"{symbol.lower()}@kline_{interval}"

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            return func

        return decorator

    def on_ticker(self, symbol: str) -> Callable:
        """订阅24小时行情"""
        stream = f"{symbol.lower()}@ticker"

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            return func

        return decorator

    def on_trade(self, symbol: str) -> Callable:
        """订阅成交数据"""
        stream = f"{symbol.lower()}@aggTrade"

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            return func

        return decorator

    def on_mark_price(self, symbol: str) -> Callable:
        """订阅标记价格"""
        stream = f"{symbol.lower()}@markPrice"

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            return func

        return decorator

    def on_error(self, func: Callable) -> Callable:
        """注册错误回调"""
        self._callbacks.setdefault("__error__", []).append(func)
        return func

    @property
    def is_connected(self) -> bool:
        return self._running and self._ws is not None
