"""混合客户端 (Hybrid Client)

自动在WebSocket和REST API之间切换:
- 优先使用WebSocket获取实时数据
- WebSocket失败时自动降级到REST轮询
- 支持自适应轮询间隔 (1s → 5s, 无上限)
"""

import asyncio
from typing import Any, Callable, Optional

from .api.v3.client import V3Client
from .constants import (
    DEFAULT_NETWORK,
    REST_POLLING_INITIAL_INTERVAL,
    REST_POLLING_MAX_INTERVAL,
    REST_POLLING_NO_LIMIT,
    REST_POLLING_STEP,
    Network,
)
from .exceptions import WSFallbackError
from .logging_config import get_logger
from .websocket.client import WebSocketClient

logger = get_logger(__name__)


class HybridClient:
    """混合客户端

    自动在WebSocket和REST API之间切换:
    - 优先使用WebSocket获取实时数据
    - WebSocket失败时自动降级到REST轮询
    - 支持自适应轮询间隔

    Usage:
        from asterdex import HybridClient, Network

        # 需要认证的客户端
        client = HybridClient(
            user="0x...",
            signer="0x...",
            private_key="0x...",
            network=Network.TESTNET
        )

        # 只需要市场数据
        market_client = HybridClient(network=Network.TESTNET)

        @client.on_book_ticker("BTCUSDT")
        async def on_ticker(ticker):
            print(f"买一: {ticker.bid_price}, 卖一: {ticker.ask_price}")

        await client.connect()
        await asyncio.sleep(60)
        await client.disconnect()
    """

    def __init__(
        self,
        user: Optional[str] = None,
        signer: Optional[str] = None,
        private_key: Optional[str] = None,
        network: Network = DEFAULT_NETWORK,
        poll_interval: float = REST_POLLING_INITIAL_INTERVAL,
        max_poll_interval: float = REST_POLLING_MAX_INTERVAL,
        poll_step: float = REST_POLLING_STEP,
        no_limit: bool = REST_POLLING_NO_LIMIT,
    ):
        self.network = network
        self._user = user
        self._signer = signer
        self._private_key = private_key

        self._ws_client = WebSocketClient(network=network)
        self._rest_client: Optional[V3Client] = None

        self._poll_interval = poll_interval
        self._max_poll_interval = max_poll_interval
        self._poll_step = poll_step
        self._no_limit = no_limit
        self._current_poll_interval = poll_interval

        self._running = False
        self._fallback_mode = False
        self._poll_task: Optional[asyncio.Task] = None

        self._callbacks: dict[str, list[Callable]] = {}

    async def _ensure_rest_client(self) -> V3Client:
        """确保REST客户端已初始化"""
        if self._rest_client is None:
            has_auth = all([self._user, self._signer, self._private_key])
            self._rest_client = V3Client(
                user=self._user if has_auth else None,
                signer=self._signer if has_auth else None,
                private_key=self._private_key if has_auth else None,
                network=self.network,
            )
        return self._rest_client

    async def connect(self) -> None:
        """建立连接

        优先尝试WebSocket，失败时自动降级到REST轮询。
        """
        self._running = True

        try:
            await self._ws_client.connect()

            # 订阅已注册的 streams
            for stream in self._callbacks.keys():
                await self._ws_client.subscribe(stream)

            logger.info("[Hybrid] WebSocket connected, exiting fallback mode")
            self._fallback_mode = False
            self._current_poll_interval = self._poll_interval
            return
        except Exception as ws_error:
            logger.warning(f"[Hybrid] WebSocket connection failed: {ws_error}")
            await self._start_fallback()
            return

    async def _start_fallback(self) -> None:
        """启动REST轮询降级模式"""
        logger.warning(
            f"[Hybrid] Starting REST fallback mode with poll interval={self._poll_interval}s"
        )
        self._fallback_mode = True

        try:
            await self._ensure_rest_client()
        except Exception as e:
            logger.error(f"[Hybrid] Failed to initialize REST client: {e}")
            raise WSFallbackError(f"Cannot initialize REST client: {e}") from e

        self._poll_task = asyncio.create_task(self._poll_loop())

    async def _poll_loop(self) -> None:
        """REST轮询循环"""
        logger.info("[Hybrid] Starting REST polling loop")

        while self._running and self._fallback_mode:
            try:
                await self._poll_once()
            except Exception as e:
                logger.error(f"[Hybrid] Poll error: {type(e).__name__}: {e}")

            self._adjust_poll_interval()
            await asyncio.sleep(self._current_poll_interval)

    async def _poll_once(self) -> None:
        """执行一次轮询"""
        rest = await self._ensure_rest_client()

        for stream, callbacks in self._callbacks.items():
            if not callbacks:
                continue

            if "@bookTicker" in stream:
                symbol = stream.split("@")[0].upper()
                try:
                    data = await rest.get_order_book(symbol)
                    for cb in callbacks:
                        await cb(data)
                except Exception as e:
                    logger.warning(f"[Hybrid] Poll failed for {stream}: {e}")
            elif "@ticker" in stream:
                symbol = stream.split("@")[0].upper()
                try:
                    data = await rest.get_ticker_24h(symbol)
                    for cb in callbacks:
                        await cb(data)
                except Exception as e:
                    logger.warning(f"[Hybrid] Poll failed for {stream}: {e}")
            elif "@kline_" in stream:
                parts = stream.split("@kline_")
                symbol = parts[0].upper()
                interval = parts[1] if len(parts) > 1 else "1m"
                try:
                    data = await rest.get_klines(symbol, interval, limit=1)
                    for cb in callbacks:
                        await cb(data[-1] if data else {})
                except Exception as e:
                    logger.warning(f"[Hybrid] Poll failed for {stream}: {e}")
            elif "@aggTrade" in stream:
                symbol = stream.split("@")[0].upper()
                try:
                    data = await rest.get_trades(symbol, limit=1)
                    for cb in callbacks:
                        await cb(data[0] if data else {})
                except Exception as e:
                    logger.warning(f"[Hybrid] Poll failed for {stream}: {e}")
            elif "@markPrice" in stream:
                symbol = stream.split("@")[0].upper()
                try:
                    data = await rest.get_mark_price(symbol)
                    for cb in callbacks:
                        await cb(data)
                except Exception as e:
                    logger.warning(f"[Hybrid] Poll failed for {stream}: {e}")

    def _adjust_poll_interval(self) -> None:
        """调整轮询间隔

        每次增加poll_step，上限为max_poll_interval (如果no_limit=False)
        """
        if self._no_limit:
            self._current_poll_interval += self._poll_step
            logger.warning(
                f"[Hybrid] Poll interval increased to {self._current_poll_interval:.1f}s (no limit)"
            )
        else:
            if self._current_poll_interval < self._max_poll_interval:
                old_interval = self._current_poll_interval
                self._current_poll_interval = min(
                    self._current_poll_interval + self._poll_step,
                    self._max_poll_interval,
                )
                if old_interval != self._current_poll_interval:
                    logger.warning(
                        f"[Hybrid] Poll interval adjusted: {old_interval:.1f}s -> {self._current_poll_interval:.1f}s"
                    )

    async def disconnect(self) -> None:
        """断开连接"""
        self._running = False

        if self._poll_task:
            self._poll_task.cancel()
            try:
                await self._poll_task
            except asyncio.CancelledError:
                pass
            self._poll_task = None

        await self._ws_client.disconnect()

        if self._rest_client:
            await self._rest_client.close()
            self._rest_client = None

        logger.info("[Hybrid] Disconnected")

    def on(self, stream: str) -> Callable:
        """注册回调装饰器"""

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            self._ws_client.on(stream)(func)
            return func

        return decorator

    def on_book_ticker(self, symbol: str) -> Callable:
        """订阅订单簿更新"""
        stream = f"{symbol.lower()}@bookTicker"

        # 注册到 WebSocket 客户端
        self._ws_client.on_book_ticker(symbol)

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            # 同时注册到 WebSocket 客户端以便在正常模式下接收数据
            self._ws_client.on(stream)(func)
            return func

        return decorator

    def on_kline(self, symbol: str, interval: str = "1m") -> Callable:
        """订阅K线数据"""
        stream = f"{symbol.lower()}@kline_{interval}"

        self._ws_client.on_kline(symbol, interval)

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            self._ws_client.on(stream)(func)
            return func

        return decorator

    def on_ticker(self, symbol: str) -> Callable:
        """订阅24小时行情"""
        stream = f"{symbol.lower()}@ticker"

        self._ws_client.on_ticker(symbol)

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            self._ws_client.on(stream)(func)
            return func

        return decorator

    def on_trade(self, symbol: str) -> Callable:
        """订阅成交数据"""
        stream = f"{symbol.lower()}@aggTrade"

        self._ws_client.on_trade(symbol)

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            self._ws_client.on(stream)(func)
            return func

        return decorator

    def on_mark_price(self, symbol: str) -> Callable:
        """订阅标记价格"""
        stream = f"{symbol.lower()}@markPrice"

        self._ws_client.on_mark_price(symbol)

        def decorator(func: Callable) -> Callable:
            self._callbacks.setdefault(stream, []).append(func)
            self._ws_client.on(stream)(func)
            return func

        return decorator

    def on_error(self, func: Callable) -> Callable:
        """注册错误回调"""
        self._ws_client.on_error(func)
        return func

    @property
    def is_connected(self) -> bool:
        return self._ws_client.is_connected or self._fallback_mode

    @property
    def is_fallback_mode(self) -> bool:
        return self._fallback_mode
